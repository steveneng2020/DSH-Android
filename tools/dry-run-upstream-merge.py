#!/usr/bin/env python3
"""只读合并预演：在不改动主干的前提下，估算与上游 v0.2.2 合并的真实冲突。

## 背景

2026-11-11 的 `git filter-repo` 重写全部 commit hash，导致 fork 与上游
**完全没有共同祖先**（`git merge-base` 返回空）。直接 `git merge` 会退化成
`--allow-unrelated-histories`，等于把两套无关版本硬拼。

研究发现：fork 的根提交 `1be4060f`（无父提交）在上游对应 `5cdd30c9`
（父提交 `733a54b2`，且 `5cdd30c9` 确实在上游 `v0.2.2` 历史中）。
也就是 filter-repo 只留下了「被扫描到的第一个提交」作为新根，祖先链丢了。

## 预演做法

用 `git replace --graft` 把 `1be4060f` 的父提交临时接上 `733a54b2`，
从而人为恢复祖先关系；然后在一个**临时工作树**里 merge 上游 `v0.2.2`，
统计冲突文件与类型。全部只读，`git replace` 本身可用 `--delete` 撤销。

## 用法

    python3 tools/dry-run-upstream-merge.py --prepare   # 建 replace + 临时工作树
    python3 tools/dry-run-upstream-merge.py --merge     # 在工作树里执行 merge 并统计
    python3 tools/dry-run-upstream-merge.py --cleanup   # 撤销 replace、删工作树
"""
import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKTREE = Path('/tmp/dsha-merge-dryrun')
FORK_ROOT = '1be4060f9d605b2e9b7c38861aa68c9bd0193fc8'      # filter-repo 后的根
UPSTREAM_PARENT = '733a54b2c8ba5a17b810c9a2617c902f41b2e5fb'  # 上游里对应的父提交
UPSTREAM_REF = 'refs/remotes/upstream/v0.2.2'


def run(args, cwd=ROOT, check=False):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise SystemExit('FAILED: %s\n%s%s' % (' '.join(args), result.stdout, result.stderr))
    return result


def prepare():
    # 已存在则先清
    run(['git', 'replace', '--delete', FORK_ROOT])
    status = run(['git', 'replace', '--graft', FORK_ROOT, UPSTREAM_PARENT])
    print('graft: %s' % (status.stderr.strip() or '已建立替换'))

    if WORKTREE.exists():
        run(['git', 'worktree', 'remove', '--force', str(WORKTREE)])
    # 用 detached HEAD 建工作树，避免动任何分支
    run(['git', 'worktree', 'add', '--detach', str(WORKTREE), 'HEAD'], check=True)
    print('工作树: %s（detached HEAD，不影响分支）' % WORKTREE)

    # 验证祖先关系已恢复
    base = run(['git', 'merge-base', 'HEAD', UPSTREAM_REF]).stdout.strip()
    print('merge-base: %s' % (base or '(仍为空)'))
    if not base:
        print('WARN 祖先关系未恢复，merge 会退化为 unrelated-histories')
    return 0


def merge():
    if not WORKTREE.is_dir():
        print('FAIL 工作树不存在，先跑 --prepare')
        return 1
    print('=== 在工作树里 merge %s（不提交）===' % UPSTREAM_REF)
    result = run(['git', 'merge', '--no-commit', '--no-ff', UPSTREAM_REF], cwd=WORKTREE)
    out = (result.stdout + result.stderr).strip()
    print(out[:3000])

    conflicts = run(['git', 'diff', '--name-only', '--diff-filter=U'], cwd=WORKTREE).stdout
    files = [f for f in conflicts.split('\n') if f]
    print('\n=== 冲突文件: %d ===' % len(files))

    buckets = Counter()
    for name in files:
        if name.startswith('app/src/main/java'):
            buckets['java (主代码)'] += 1
        elif name.startswith('app/src/main/res'):
            buckets['res (资源)'] += 1
        elif name.startswith('app/src/main/assets'):
            buckets['assets (插件与补丁)'] += 1
        elif name.startswith('app/build.gradle') or name.endswith('.gradle'):
            buckets['gradle 配置'] += 1
        elif name.startswith('tools/'):
            buckets['tools (脚本/门禁)'] += 1
        elif name.startswith('docs/'):
            buckets['docs'] += 1
        elif name.startswith('.github/'):
            buckets['CI'] += 1
        else:
            buckets['其他'] += 1
    for key, value in buckets.most_common():
        print('  %-22s %4d' % (key, value))

    print('\n=== 全部冲突文件（前 80）===')
    for name in files[:80]:
        print('  ' + name)
    if len(files) > 80:
        print('  ... 还有 %d' % (len(files) - 80))

    # 自动合并成功但内容可能可疑的：两边都改过的非冲突文件
    stat = run(['git', 'diff', '--cached', '--stat'], cwd=WORKTREE).stdout
    print('\n=== 合并暂存区概览（末 3 行）===')
    for line in stat.strip().split('\n')[-3:]:
        print('  ' + line)

    report = {'conflicts': files, 'buckets': dict(buckets)}
    Path('/tmp/merge-dryrun-report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('\n报告: /tmp/merge-dryrun-report.json')
    print('\n注意：这是只读预演，worktree 里的 merge 未提交；主干未受影响。')
    return 0


def cleanup():
    if WORKTREE.is_dir():
        run(['git', 'worktree', 'remove', '--force', str(WORKTREE)])
        print('已删工作树')
    run(['git', 'replace', '--delete', FORK_ROOT])
    print('已撤销 replace')
    remaining = run(['git', 'replace', '-l']).stdout.strip()
    print('剩余 replace: %s' % (remaining or '(无)'))
    base = run(['git', 'merge-base', 'HEAD', UPSTREAM_REF]).stdout.strip()
    print('merge-base 已恢复为: %s' % (base or '(空，即原始状态)'))
    return 0


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare', action='store_true')
    group.add_argument('--merge', action='store_true')
    group.add_argument('--cleanup', action='store_true')
    args = parser.parse_args()
    if args.prepare:
        return prepare()
    if args.merge:
        return merge()
    return cleanup()


if __name__ == '__main__':
    sys.exit(main())
