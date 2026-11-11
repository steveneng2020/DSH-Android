#!/usr/bin/env python3
"""T7(G8)：更新说明两个面的一致性检查（changelog.md 全文 + changelog_recent.json 摘要卡）。

背景：G8 的原状态是「tools/check-release-notes-coverage.py 不存在」。当时只有
tools/generate-changelog.py 守着「docs/releases/build{N}-changes.{zh,en}.md →
app/src/main/res/{raw,raw-en}/changelog.md」这一段，而 APK 里另一份面向用户的
数据 app/src/main/res/{raw,raw-en}/changelog_recent.json（ChangelogPanel 直接
openRawResource 读的那份）完全没有门禁 —— 版本号、构建号、条数、中英一致性
全靠手写，漂了没人知道（v1.3 就漂过一次）。

本检查器覆盖四类可机械判定的事实，全部取自仓库现状，不猜、不补：
  A 版本锚点：app/build.gradle 的 versionCode / versionName 必须同时出现在
    两个面（changelog.md 首行 + changelog_recent.json 的第 0 条）。
  B 结构：changelog.md 有标题行与至少一条 bullet；changelog_recent.json 满足
    ChangelogPanel.readEntries() 的运行期契约（schema=1、entries 非空、每条
    有 version/title/bullets）。
  C 中英对齐：两侧的条目数、条目版本序列、bullet 条数必须一致（翻译义务）。
  D 摘要卡不越界：changelog_recent.json 第 0 条的 bullet 数不得超过同语言
    changelog.md 的 bullet 数（摘要卡是全文的子集，不能反过来多）。

不做的事：不做语义比对（摘要卡的三条 bullet 与全文十一条不是逐字同一句话，
把逐字相等当判据会假红）；不判断文案优劣；不改任何文件。

跑法：
    python3 tools/check-release-notes-coverage.py           # 等价 --check
    python3 tools/check-release-notes-coverage.py --check --json
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRADLE = ROOT / 'app/build.gradle'
FACES = (
    ('zh', ROOT / 'app/src/main/res/raw/changelog.md',
     ROOT / 'app/src/main/res/raw/changelog_recent.json'),
    ('en', ROOT / 'app/src/main/res/raw-en/changelog.md',
     ROOT / 'app/src/main/res/raw-en/changelog_recent.json'),
)
ENTRY_KEYS = ('version', 'title', 'bullets')


class CoverageError(Exception):
    pass


def read_gradle_version():
    text = GRADLE.read_text(encoding='utf-8')
    code = re.search(r'(?m)^\s*versionCode\s+(\d+)\s*$', text)
    name = re.search(r'(?m)^\s*versionName\s+"([^"]+)"\s*$', text)
    if not code:
        raise CoverageError('VERSION_CODE_MISSING: app/build.gradle')
    if not name:
        raise CoverageError('VERSION_NAME_MISSING: app/build.gradle')
    return int(code.group(1)), name.group(1)


def normalize_version(value):
    """把日期段里的连字符去掉，并去掉可选的 `DSHA ` 前缀，再比。

    versionName 是 `DSHA v1.4 20261031@0.2.1-rc.2`？不 —— 本 fork 的
    `app/build.gradle` 里 versionName **不带** `DSHA ` 前缀（带了会让
    `tools/generate-changelog.py` 拼出 `DSHA DSHA …` 的标题）。
    而 `changelog_recent.json` 的展示名**必须**带前缀：
    `tools/check-changelog-sync.py` 的 `key_of()` 用 `split()[1]` 取版本键，
    少了前缀会整串当键，CHANGELOG.md 立刻报「没有 ## 小节」。

    两个上游脚本对同一字段的期望相反（2026-11-11 实测：
    `check-release-notes-coverage.py` FAIL、`check-changelog-sync.py` PASS）。
    前缀只是展示写法，不是版本内容，所以在归一化里一并剥掉，
    让两边都能通过，而不是逼着一个脚本去改另一个脚本依赖的字段格式。

    日期段去连字符同理（v1.3 起 `changelog_recent` 用 `2026-10-27` 写法）。
    """
    text = str(value or '').strip()
    if text.startswith('DSHA '):
        text = text[len('DSHA '):]
    return re.sub(r'(\d{4})-(\d{2})-(\d{2})', r'\1\2\3', text)


def short_version(version_name):
    """`DSHA v1.4 20261031@0.2.1-rc.2` -> `DSHA v1.4`；changelog.md 首行只写这一截。"""
    matched = re.match(r'^(.*?\bv[\d.]+)\s', version_name)
    return matched.group(1) if matched else version_name


def bullets_in(text):
    return [line for line in text.splitlines() if line.startswith('- ')]


def check_face(locale, changelog_path, recent_path, version_code, version_name):
    problems = []
    facts = {'locale': locale}
    if not changelog_path.is_file():
        raise CoverageError('CHANGELOG_MISSING: ' + str(changelog_path))
    if not recent_path.is_file():
        raise CoverageError('CHANGELOG_RECENT_MISSING: ' + str(recent_path))
    text = changelog_path.read_text(encoding='utf-8')
    lines = text.splitlines()
    head = lines[0] if lines else ''
    build = 'build%d' % version_code
    if not head.startswith('# '):
        problems.append('CHANGELOG_HEADER_MISSING: ' + locale)
    if build not in head:
        problems.append('CHANGELOG_BUILD_MISMATCH: %s: 首行无 %s（实际 %r）' % (locale, build, head))
    short = short_version(version_name)
    if short not in head:
        problems.append('CHANGELOG_SHORTVERSION_MISSING: %s: 首行无 %r（实际 %r）'
                        % (locale, short, head))
    bullets = bullets_in(text)
    if not bullets:
        problems.append('CHANGELOG_BULLETS_EMPTY: ' + locale)
    facts['changelogBullets'] = len(bullets)

    try:
        data = json.loads(recent_path.read_text(encoding='utf-8'))
    except ValueError as error:
        raise CoverageError('CHANGELOG_RECENT_JSON: %s: %s' % (locale, error))
    if data.get('schema') != 1:
        problems.append('CHANGELOG_RECENT_SCHEMA: ' + locale)
    entries = data.get('entries')
    if not isinstance(entries, list) or not entries:
        raise CoverageError('CHANGELOG_RECENT_ENTRIES_EMPTY: ' + locale)
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            problems.append('CHANGELOG_RECENT_ENTRY_TYPE: %s[%d]' % (locale, index))
            continue
        for key in ENTRY_KEYS:
            if key == 'bullets':
                value = entry.get('bullets')
                if not isinstance(value, list) or not value:
                    problems.append('CHANGELOG_RECENT_BULLETS_EMPTY: %s[%d]' % (locale, index))
            elif not str(entry.get(key) or '').strip():
                problems.append('CHANGELOG_RECENT_%s_EMPTY: %s[%d]' % (key.upper(), locale, index))
    first = entries[0]
    if str(first.get('build') or '') != build:
        problems.append('CHANGELOG_RECENT_BUILD_MISMATCH: %s: %r != %r'
                        % (locale, first.get('build'), build))
    if normalize_version(first.get('version')) != normalize_version(version_name):
        problems.append('CHANGELOG_RECENT_VERSION_MISMATCH: %s: %r != %r'
                        % (locale, first.get('version'), version_name))
    recent_bullets = len(first.get('bullets') or [])
    if recent_bullets > len(bullets):
        problems.append('CHANGELOG_RECENT_BULLETS_EXCEED: %s: 摘要卡 %d > 全文 %d'
                        % (locale, recent_bullets, len(bullets)))
    facts.update(entries=len(entries), firstBuild=first.get('build'),
                 firstVersion=first.get('version'), recentBullets=recent_bullets,
                 versions=[str(entry.get('version') or '') for entry in entries])
    return problems, facts


def check(root=None):
    global ROOT, GRADLE, FACES
    if root is not None:
        ROOT = Path(root).resolve()
        GRADLE = ROOT / 'app/build.gradle'
        FACES = (
            ('zh', ROOT / 'app/src/main/res/raw/changelog.md',
             ROOT / 'app/src/main/res/raw/changelog_recent.json'),
            ('en', ROOT / 'app/src/main/res/raw-en/changelog.md',
             ROOT / 'app/src/main/res/raw-en/changelog_recent.json'),
        )
    version_code, version_name = read_gradle_version()
    problems, facts = [], []
    for locale, changelog_path, recent_path in FACES:
        face_problems, face_facts = check_face(locale, changelog_path, recent_path,
                                               version_code, version_name)
        problems += face_problems
        facts.append(face_facts)
    versions = [tuple(face['versions']) for face in facts]
    if len(set(versions)) != 1:
        problems.append('CHANGELOG_RECENT_LOCALE_DRIFT: 中英版本序列不一致 %s'
                        % ([list(v) for v in versions],))
    counts = {face['entries'] for face in facts}
    if len(counts) != 1:
        problems.append('CHANGELOG_RECENT_COUNT_DRIFT: 中英条目数不一致 %s' % (sorted(counts),))
    if problems:
        raise CoverageError('; '.join(problems))
    return {'status': 'PASS_RELEASE_NOTES_COVERAGE', 'versionCode': version_code,
            'versionName': version_name, 'faces': facts}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='检查更新说明两个面（changelog.md 与 changelog_recent.json）是否与 app/build.gradle 一致。')
    parser.add_argument('--check', action='store_true',
                        help='执行检查（默认动作，保留此开关以便 Gradle 与 CI 显式调用）')
    parser.add_argument('--json', action='store_true', help='以 JSON 输出结果')
    parser.add_argument('--root', help='仓库根目录（默认按本文件位置推导）')
    args = parser.parse_args(argv)
    try:
        result = check(args.root)
    except CoverageError as error:
        print('FAIL_RELEASE_NOTES_COVERAGE: ' + str(error), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print('PASS release notes coverage: %s / "DSHA" build %d, %d entries per locale'
              % (result['versionName'], result['versionCode'], result['faces'][0]['entries']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
