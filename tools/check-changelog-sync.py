#!/usr/bin/env python3
"""仓库 CHANGELOG.md、App 内 changelog.md 与 changelog_recent.json 的更新记录一致性检查与自动对齐。

## 为什么需要这个脚本

2026-11-10 实测发现 v1.1 第 1 条两处不一致：
仓库 `CHANGELOG.md` 只写到「应用图标重做为「鲲」单剪影，去除玉璧双环与描金。」，
而 App 内 `changelog_recent.json` 多了《庄子·逍遥游》的出处。

原因是这些数据**分别手写**，且在过去三条链路各自维护：
- 仓库面：`CHANGELOG.md`（人写）
- App 全文：`docs/releases/build{code}-changes.{zh,en}.md` → `generate-changelog.py`
  → `app/src/main/res/{raw,raw-en}/changelog.md`（已由生成器守着）
- App 摘要卡：`app/src/main/res/{raw,raw-en}/changelog_recent.json`（人写）

`check-release-notes-coverage.py` 只校验 `changelog.md` 与 `changelog_recent.json`
之间的关系，**完全不看 `CHANGELOG.md`**，所以它漂了没人知道。

2026-11-10 第二版加了本脚本，但**没有接进 CI，也没提交**，等于没生效 ——
v1.1 那条在 HEAD 里仍然漂着。第三版（本版）补上这两件事：
1. `--write` 自动对齐：把 `CHANGELOG.md` 的 bullet 段改写为 App 侧内容（人不必手抄）
2. 由 `.github/workflows/ci-fast.yml` 与 `tools/verify-stability.py` 实际执行

## 对齐方向

**以 App 内为准，向仓库回写。** 理由：App 内是用户实际看到的内容，改动它的代价
（要重新打包发版）远高于改仓库 Markdown；反过来以仓库为准去改 App，会让已发布
APK 里的文案与仓库不符。

## 检查内容

对每个在 `changelog_recent.json` 里出现的版本：
1. `CHANGELOG.md` 必须有同名版本小节（`## v1.4` / `## v1` 形态）
2. 两边的 bullet 条数必须相等
3. 逐条文本必须一致（去首尾空白后精确比较）

英文面（`raw-en`）与中文 `CHANGELOG.md` 天然不同语言，只校验「版本存在 + 条数相等」，
不做逐字比对 —— 否则会把正常翻译差异报成错误（2026-11-10 实测踩过）。

## 跑法

    python3 tools/check-changelog-sync.py          # 等价 --check；CI 与 verify-stability 用这个
    python3 tools/check-changelog-sync.py --json   # 机器可读
    python3 tools/check-changelog-sync.py --write  # 自动把 CHANGELOG.md 对齐到 App 内内容
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = ROOT / 'CHANGELOG.md'
# CHANGELOG.md 是中文；只有中文面能与它逐字比对。
FACES = (
    ('zh', ROOT / 'app/src/main/res/raw/changelog_recent.json', True),
    ('en', ROOT / 'app/src/main/res/raw-en/changelog_recent.json', False),
)
UPDATES = ROOT / 'updates.json'


def read(path):
    return path.read_text(encoding='utf-8')


def changelog_versions(text):
    """把 CHANGELOG.md 切成 {版本键: [bullet, ...]}。

    版本键取自 `## v1.4` / `## v1` 这类二级标题；遇到 `## 上游历史` 等非版块即停止收集。
    """
    versions = {}
    current = None
    for line in text.splitlines():
        if line.startswith('## '):
            head = line[3:].strip()
            m = re.match(r'(v\d+(?:\.\d+)?)', head)
            current = m.group(1) if m else None
            if current:
                versions.setdefault(current, [])
            continue
        if current and line.startswith('- '):
            versions[current].append(line[2:].strip())
    return versions


def key_of(version_name):
    """'DSHA v1.4 20261110@0.2.1-rc.2' -> 'v1.4'；'DSHA v1 2026-10-25@...' -> 'v1'。"""
    parts = str(version_name).split()
    return parts[1] if len(parts) > 1 else str(version_name)


def app_versions():
    """中文面的 {版本键: [bullet, ...]} —— 对齐的唯一真源。"""
    data = json.loads(read(FACES[0][1]))
    return {key_of(e.get('version')): [str(x).strip() for x in (e.get('bullets') or [])]
            for e in (data.get('entries') or [])}


def check_updates_notes(app):
    """updates.json 的 notes 必须把本版每一条更新都带给用户。

    2026-11-10 事故：App 的更新页（UpdateUi）直接显示 updates.json 的 notes 字段，
    而 notes 当时只有一句摘要，用户点「检查更新」只能看到一行字，
    看不到 9 条实际改动 —— 表现为「更新日记没有了」。
    Release 正文与 App 内更新页是两条独立展示链，两边都得有完整清单。
    """
    problems = []
    if not UPDATES.is_file():
        return ['UPDATES_MISSING: %s' % UPDATES]
    release = (json.loads(read(UPDATES)).get('releases') or [{}])[0]
    notes = str(release.get('notes') or '')
    key = key_of(release.get('version'))
    bullets = app.get(key) or []
    if not bullets:
        return problems
    if len(notes) > 8192:
        # UpdateLocations.notes() 会在 8192 字符处截断。
        problems.append('UPDATES_NOTES_TOO_LONG: %s 的 notes 有 %d 字符，'
                        '超过 UpdateLocations 的 8192 上限，会被截断' % (key, len(notes)))
    for index, bullet in enumerate(bullets, 1):
        # 逐条比对正文，不比对前缀符号，避免因 `·` / `-` 写法差异假红。
        if bullet not in notes:
            problems.append(
                'UPDATES_NOTES_MISSING: %s 第 %d 条没写进 updates.json 的 notes\n'
                '    条目: %s\n'
                '    notes 里找不到上面这段文字' % (key, index, bullet[:100]))
    return problems


def rewrite(repo_bullets, app_bullets):
    """把 CHANGELOG.md 的 bullet 行按 App 侧内容重建，返回 (新全文, 改写条数)。"""
    text = read(CHANGELOG)
    lines = text.split('\n')
    out = []
    current = None
    replaced = {}          # 版本键 -> 新 bullet 列表
    changed = 0
    for line in lines:
        if line.startswith('## '):
            head = line[3:].strip()
            m = re.match(r'(v\d+(?:\.\d+)?)', head)
            current = m.group(1) if m else None
            out.append(line)
            continue
        if current and line.startswith('- '):
            key = current
            if key not in replaced:
                replaced[key] = list(app_bullets.get(key) or [])
                for bullet in replaced[key]:
                    out.append('- ' + bullet)
            # 原有 bullet 行一律丢弃，由上面统一重写
            if line[2:].strip() != (app_bullets.get(key) or [])[0:1] and line not in out:
                pass
            continue
        out.append(line)
    new_text = '\n'.join(out)
    if new_text != text:
        changed = sum(1 for key in replaced
                      if repo_bullets.get(key) != app_bullets.get(key))
    return new_text, changed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true', help='默认行为')
    group.add_argument('--write', action='store_true',
                       help='把 CHANGELOG.md 的 bullet 段改写为 App 内 changelog_recent.json 的内容')
    parser.add_argument('--json', action='store_true', help='输出 JSON')
    args = parser.parse_args(argv)

    if not CHANGELOG.is_file():
        print('FAIL CHANGELOG_MISSING: %s' % CHANGELOG)
        return 1
    repo = changelog_versions(read(CHANGELOG))
    app = app_versions()

    problems = []
    facts = []
    for locale, recent_path, compare_text in FACES:
        data = json.loads(read(recent_path))
        entries = data.get('entries') or []
        facts.append({'locale': locale, 'versions': len(entries)})
        for entry in entries:
            key = key_of(entry.get('version'))
            app_bullets = [str(x).strip() for x in (entry.get('bullets') or [])]
            if key not in repo:
                problems.append(
                    'CHANGELOG_SYNC_MISSING: %s: CHANGELOG.md 没有 `## %s` 小节' % (locale, key))
                continue
            repo_bullets = repo[key]
            if len(repo_bullets) != len(app_bullets):
                problems.append(
                    'CHANGELOG_SYNC_COUNT: %s: %s 仓库 %d 条 / App %d 条'
                    % (locale, key, len(repo_bullets), len(app_bullets)))
                continue
            if not compare_text:
                continue  # 英文面只校验版本与条数
            for index, (a, b) in enumerate(zip(repo_bullets, app_bullets), 1):
                if a != b:
                    problems.append(
                        'CHANGELOG_SYNC_TEXT: %s: %s 第 %d 条不一致\n'
                        '    仓库: %s\n'
                        '    App : %s' % (locale, key, index, a[:120], b[:120]))

    problems.extend(check_updates_notes(app))

    if args.write:
        new_text, changed = rewrite(repo, app)
        if not changed:
            print('PASS changelog sync: 无需对齐')
            return 0
        CHANGELOG.write_text(new_text, encoding='utf-8', newline='\n')
        print('WROTE CHANGELOG.md: 已按 App 内 changelog_recent.json 对齐 %d 个版本' % changed)
        return 0

    if args.json:
        print(json.dumps({'problems': problems, 'faces': facts}, ensure_ascii=False, indent=2))
    elif problems:
        for problem in problems:
            print('FAIL ' + problem)
        print('\n对齐办法：python3 tools/check-changelog-sync.py --write   '
              '（以 App 内为准回写 CHANGELOG.md，然后人工复核 git diff）')
    else:
        total = sum(len(v) for v in repo.values())
        print('PASS changelog sync: %d 个版本、%d 条，仓库与 App 逐条一致'
              % (len(repo), total))
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
