#!/usr/bin/env python3
"""核对 APK 内的更新日记与源文件是否一致。

2026-11-13 事故：改了 res/raw*/changelog_recent.json 的 build 字段后重新构建，
Gradle 增量构建复用了旧的中间产物（app/build/intermediates/packaged_res/），
APK 里仍是上一版的值。用户装包后看到 build20060457，源文件是 build20070357。

**门禁 11/11 PASS 也查不出这个** —— 门禁读磁盘源文件，不读 APK 内容。

用法：
    python3 tools/check-apk-changelog.py <apk>
    python3 tools/check-apk-changelog.py            # 默认取标准 release 产物

判据：APK 内 raw/changelog_recent 的中英两份，其 entries[0] 的
      version / build 必须与 build.gradle 的 versionCode / versionName 一致。
退出码 0 = 一致；非 0 = 不一致（禁止交付）。
"""
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_APK = ROOT / 'app/build/outputs/apk/standard/release/app-standard-release.apk'
AAPT2 = Path('/opt/android-sdk/build-tools/37.0.0/aapt2')


def build_identity():
    gradle = (ROOT / 'app/build.gradle').read_text(encoding='utf-8')
    code = re.search(r'^\s*versionCode\s+(\d+)\s*$', gradle, re.M)
    name = re.search(r'^\s*versionName\s+"([^"\r\n]+)"\s*$', gradle, re.M)
    if not code or not name:
        raise SystemExit('BUILD_IDENTITY_MISSING')
    return int(code.group(1)), name.group(1)


def apk_changelog_resources(apk):
    """返回 raw/changelog_recent 在 APK 内的实际文件名列表（AGP 会改名成 res/xx.json）。"""
    out = subprocess.run([str(AAPT2), 'dump', 'resources', str(apk)],
                         capture_output=True, text=True).stdout
    m = re.search(r'resource\s+0x[0-9a-f]+\s+raw/changelog_recent\s*\n((?:\s+\([a-zA-Z-]*\)\s+\(file\)\s+\S+\s*\n)+)', out)
    if not m:
        return []
    return re.findall(r'\(file\)\s+(\S+)', m.group(1))


def main():
    apk = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_APK
    if not apk.is_file():
        print('APK_MISSING: %s' % apk)
        return 1
    code, name = build_identity()
    want_version = 'DSHA ' + name
    want_build = 'build%d' % code

    files = apk_changelog_resources(apk)
    if not files:
        print('CHANGELOG_RESOURCE_MISSING: APK 内找不到 raw/changelog_recent')
        return 1

    problems = []
    with zipfile.ZipFile(apk) as z:
        for f in files:
            data = json.loads(z.read(f).decode('utf-8'))
            entries = data.get('entries') or []
            if not entries:
                problems.append('%s: entries 为空' % f)
                continue
            e = entries[0]
            got_version, got_build = e.get('version'), e.get('build')
            status = 'OK'
            if got_version != want_version:
                problems.append('%s: version=%r，期望 %r' % (f, got_version, want_version))
                status = 'MISMATCH'
            if got_build != want_build:
                problems.append('%s: build=%r，期望 %r' % (f, got_build, want_build))
                status = 'MISMATCH'
            print('  %-16s %-34s %-14s %s' % (f, got_version, got_build, status))

    print()
    print('期望：version=%s  build=%s' % (want_version, want_build))
    if problems:
        print()
        for p in problems:
            print('FAIL ' + p)
        print()
        print('原因通常是 Gradle 增量构建复用了旧中间产物。修法：')
        print('  rm -rf app/build/intermediates/packaged_res app/build/intermediates/merged_res')
        print('  然后重新 assembleStandardRelease')
        return 1
    print('PASS APK 内更新日记与 build.gradle 一致')
    return 0


if __name__ == '__main__':
    sys.exit(main())
