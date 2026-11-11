#!/usr/bin/env python3
"""把 rebuild/v0.2.2-base 的 fork 改动，逐批移植到 fork/v0.2.2 分支。

## 背景

2026-11-11 用户要求：以后上游更新要能「很方便快捷合并」。
但 rebuild/v0.2.2-base 是把 v0.2.2 文件树贴在旧 fork 历史之上，
`git merge-base` 为空 —— 下次上游发版仍会退化成 unrelated-histories 硬拼。

正确做法是从上游提交直接开分支（本脚本运行时的 fork/v0.2.2，父提交 = 5e2dca92），
再把 fork 的改动作为自己的提交叠上去。这样上游 v0.2.2 是真实祖先，
将来 `git merge upstream/v0.2.3` 只会冲突在 fork 改过的文件上。

## 本脚本做的事

从旧分支（SOURCE）按类别取文件，落到当前工作区，供分批 commit：
  identity  发行身份与版本号、10 语言 changelog
  forkjava  fork 独有 java
  forkres   fork 独有 res
  forkassets fork 独有 assets
  forktools fork 独有 tools（跳过 low 相关）
  forkmisc  文档类（GPL-SOURCE-OFFER / SECURITY / UPDATES-HOWTO 等）

用法：
    python3 tools/port-fork-changes.py identity
    python3 tools/port-fork-changes.py forkjava
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = '49ba0962'          # rebuild/v0.2.2-base 的最新提交
UPSTREAM = 'refs/remotes/upstream/v0.2.2'


def ls(rev):
    out = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', rev],
                                  cwd=ROOT, text=True)
    return {line for line in out.split('\n') if line}


def take(path):
    """从 SOURCE 取单个文件写到工作区。"""
    data = subprocess.check_output(['git', 'show', '%s:%s' % (SOURCE, path)], cwd=ROOT)
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return target


def fork_only():
    """SOURCE 相对上游多出来的文件。"""
    return sorted(ls(SOURCE) - ls(UPSTREAM))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    phase = sys.argv[1]
    files = fork_only()
    taken = 0

    if phase == 'identity':
        # 构建配置与身份：这些必须手工合并，不直接覆盖
        for path in ('ci/release-identity.fork.json', 'tools/write-fork-changelog.py',
                     'gradle.properties', 'local.properties'):
            try:
                take(path)
                taken += 1
            except subprocess.CalledProcessError:
                pass
        # app/build.gradle 需要手工合并（里面有上游的身份体系），这里不覆盖
        print('identity: 已取 %d 个；app/build.gradle 需手工合并' % taken)
        return 0

    if phase == 'forkjava':
        # 只取 app/src/main/java 下、且不属于 low 的
        targets = [f for f in files if f.startswith('app/src/main/java')]
    elif phase == 'forkres':
        targets = [f for f in files if f.startswith('app/src/main/res')]
    elif phase == 'forkassets':
        targets = [f for f in files if f.startswith('app/src/main/assets')]
    elif phase == 'forktools':
        targets = [f for f in files if f.startswith('tools/')
                   and 'low' not in Path(f).name]
    elif phase == 'forkmisc':
        targets = [f for f in files if f.split('/')[0] in
                   ('GPL-SOURCE-OFFER.md', 'SECURITY.md', 'UPDATES-HOWTO.md', 'updates.json')
                   or f.startswith('docs/')]
    else:
        print('未知阶段: %s' % phase)
        return 2

    for path in targets:
        try:
            take(path)
            taken += 1
        except subprocess.CalledProcessError:
            print('  跳过（SOURCE 中不存在）: %s' % path)

    print('%s: 已取 %d 个文件' % (phase, taken))
    return 0


if __name__ == '__main__':
    sys.exit(main())
