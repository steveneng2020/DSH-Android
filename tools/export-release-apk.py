#!/usr/bin/env python3
"""把正式版 APK 输出到统一的构建产物目录。

## 为什么需要这个脚本

2026-11-11 用户明确要求：**以后构建的正式版 app 都要输出到**
`/storage/emulated/0/Download/Eta/DSHA开发/builds`。

在此之前产物只躺在 `app/build/outputs/apk/standard/release/`，那是个会被
`gradle clean` 清掉、也被 `.gitignore` 排除的中间目录；要交付时再手工 `cp`，
既容易忘，也容易把诊断包和正式包混在一起（历史上 `builds/` 里就有
`-PROBE1`~`-PROBE16` 这种一次性探针包）。

本脚本做的事：
1. 校验产物确实是「正式包」：包名、versionCode、签名证书、非 debuggable、
   arm64-v8a、minSdk 30 —— 任一不符就拒绝输出，避免把调试包放进 builds/。
2. 按该目录既有命名规范复制：`DSHA-<版本>-<YYYYMMDD>-<HHMM>.apk`
3. 同目录写 `.apk.sha256`（sha256sum 兼容格式）
4. 与 `updates.json` 登记的 sha256/bytes 交叉核对，不一致直接失败

## 命名规范（沿用该目录既有习惯）

    DSHA-v1.4-release-20261104-0025.apk
    DSHA-v1.4-patch-dedup-20261110-0147.apk
    DSHA-v1.4-20261111-0157.apk        ← 本脚本产出：版本 + 构建日期 + 时刻

日期时刻取 APK 自身 mtime 的北京时间，而不是"现在"——
避免事后补输出时名字与真实构建时间不符。

## 跑法

    python3 tools/export-release-apk.py                 # 输出到默认目录
    python3 tools/export-release-apk.py --out <dir>     # 指定目录
    python3 tools/export-release-apk.py --dry-run       # 只校验与打印目标名
"""
import argparse
import datetime
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APK = ROOT / 'app/build/outputs/apk/standard/release/app-standard-release.apk'
DEFAULT_OUT = Path('/storage/emulated/0/Download/Eta/DSHA开发/builds')
# 与本项目 ci/release-identity.json 一致；写死是为了让本脚本不依赖构建期产物。
EXPECTED_CERT = '814ab1037fb25c781236809c7dffff1a101385ae245b6d5b55b767e44e63622f'
EXPECTED_PACKAGE = 'dsh.android.dev'


def find_build_tools():
    sdk = Path('/opt/android-sdk/build-tools')
    if not sdk.is_dir():
        return None
    # 只认三段纯数字正式版，取版本号最大的
    # 2026-11-11 教训：本机 build-tools/37.0.0 只有 aapt2 没有 apksigner.jar，
    # 只按版本号取最大会选到 37.0.0 然后签名检查失败。改为要求两者都在。
    candidates = []
    for item in sdk.iterdir():
        match = re.fullmatch(r'(\d+)\.(\d+)\.(\d+)', item.name)
        if (match and (item / 'aapt').is_file()
                and (item / 'lib/apksigner.jar').is_file()):
            candidates.append(((int(match.group(1)), int(match.group(2)), int(match.group(3))), item))
    return max(candidates)[1] if candidates else None


def verify(apk):
    """返回 (problems, facts)。只读检查，不改任何东西。"""
    problems, facts = [], {}
    if not apk.is_file():
        return ['APK_MISSING: %s' % apk], facts

    tools = find_build_tools()
    if tools is None:
        return ['BUILD_TOOLS_MISSING: 找不到带 aapt2 的 build-tools'], facts

    # aapt2 dump badging 不输出 sdkVersion，只有 aapt 才有；这里必须用 aapt。
    badging = subprocess.run([str(tools / 'aapt'), 'dump', 'badging', str(apk)],
                             capture_output=True, text=True).stdout
    package = re.search(r"package: name='([^']+)'", badging)
    version_code = re.search(r"versionCode='(\d+)'", badging)
    version_name = re.search(r"versionName='([^']+)'", badging)
    min_sdk = re.search(r"sdkVersion:'(\d+)'", badging)
    facts['package'] = package.group(1) if package else '(未知)'
    facts['versionCode'] = int(version_code.group(1)) if version_code else 0
    facts['versionName'] = version_name.group(1) if version_name else '(未知)'
    facts['minSdk'] = int(min_sdk.group(1)) if min_sdk else 0

    if facts['package'] != EXPECTED_PACKAGE:
        problems.append('PACKAGE_MISMATCH: %s（期望 %s）' % (facts['package'], EXPECTED_PACKAGE))
    if 'application-debuggable' in badging:
        problems.append('DEBUGGABLE_APK: 正式版不得可调试')
    if facts['minSdk'] != 30:
        problems.append('MIN_SDK_UNEXPECTED: %s（standard 期望 30）' % facts['minSdk'])
    if "native-code: 'arm64-v8a'" not in badging:
        problems.append('ABI_MISMATCH: 期望仅 arm64-v8a')

    jar = tools / 'lib/apksigner.jar'
    java = shutil.which('java') or '/opt/dsha-env/jdk17/bin/java'
    if not jar.is_file():
        problems.append('APKSIGNER_MISSING: %s' % jar)
    else:
        result = subprocess.run([java, '-jar', str(jar), 'verify', '--min-sdk-version', '23',
                                 '--verbose', '--print-certs', str(apk)],
                                capture_output=True, text=True)
        blob = result.stdout + result.stderr
        digest = re.search(r'certificate SHA-256 digest:\s*([a-f0-9]{64})', blob)
        facts['cert'] = digest.group(1) if digest else '(未检出)'
        if facts['cert'] != EXPECTED_CERT:
            problems.append('CERT_MISMATCH: %s（期望 %s）' % (facts['cert'], EXPECTED_CERT))
        for scheme in ('v1', 'v2', 'v3'):
            if not re.search(r'Verified using ' + scheme + r' scheme[^:]*: true', blob):
                problems.append('SCHEME_MISSING: %s' % scheme)
    return problems, facts


def sanitize_note(note):
    """把「主要更新内容」压成可放进文件名的短标签。

    2026-11-11 用户要求：同版本反复测试导致 builds/ 里几十个包名字一样、分不清，
    要在时间后追加「-主要更新内容」；正式发布时再加 `-release`。

    文件名约束（跨平台 + shell 安全）：不允许 / \\ : * ? " < > | 与空白和控制字符，
    长度限 24 个字符。中文保留原样——本项目全部产物都在 Android/Linux 上流转，
    不要求 ASCII——但空格一律换成 `-`，否则 shell 里必须引号、也容易被门禁误判。
    """
    if not note:
        return ''
    tag = re.sub(r'[\s/\\:*?"<>|]+', '-', note.strip())
    tag = re.sub(r'-{2,}', '-', tag).strip('-')
    # 去掉首尾的点（隐藏文件 / 末尾点在某些文件系统上非法）
    tag = tag.strip('.')
    return tag[:24]


def target_name(facts, apk, note='', release=False):
    """DSHA-<版本>-<YYYYMMDD>-<HHMM>[-<主要更新内容>][-release].apk

    日期时刻取 APK 自身 mtime 的**北京时间**。

    2026-11-11 教训：容器默认时区是 UTC，用 time.localtime() 会把
    北京时间 2026-11-11 00:57 的产物命名成 `20261110-1657`，
    与 versionName 里的 20261111 自相矛盾（差一天）。
    这里显式换成 Asia/Shanghai，与项目「构建日期用北京时间」的约定一致。

    2026-11-11 追加：`-<主要更新内容>` 与 `-release` 由用户要求，
    门禁 `tools/gate.py` 的 G12 负责校验本函数的产物符合该规范。
    """
    moment = datetime.datetime.fromtimestamp(apk.stat().st_mtime,
                                            datetime.timezone(datetime.timedelta(hours=8)))
    stamp = moment.strftime('%Y%m%d-%H%M')
    # versionName 形如 `DSHA v1.4 20261111@0.2.1-rc.2`，取 `v1.4` 那段
    match = re.search(r'\bv\d+(?:\.\d+)*\b', facts['versionName'])
    short = match.group(0) if match else 'v?'
    tag = sanitize_note(note)
    parts = ['DSHA', short, stamp]
    if tag:
        parts.append(tag)
    if release:
        parts.append('release')
    return '-'.join(parts) + '.apk'


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--note', default='',
                        help='主要更新内容，追加到时间后作为文件名标签，例如「图标提示条修复」')
    parser.add_argument('--release', action='store_true',
                        help='这是要对外发布的正式版，文件名追加 -release')
    args = parser.parse_args()

    problems, facts = verify(APK)
    if problems:
        for problem in problems:
            print('FAIL ' + problem)
        print('\n拒绝输出：产物不是合格的正式包。')
        return 1

    digest = hashlib.sha256(APK.read_bytes()).hexdigest()
    size = APK.stat().st_size

    # 与 updates.json 交叉核对，防止把"仓库登记过但没这版"的包当正式版输出
    updates = json.loads((ROOT / 'updates.json').read_text(encoding='utf-8'))
    artifact = updates['releases'][0]['artifacts'][0]
    if artifact['sha256'] != digest or artifact['bytes'] != size:
        print('FAIL UPDATES_MISMATCH: updates.json 登记 %s / %s B，产物 %s / %s B'
              % (artifact['sha256'][:16], artifact['bytes'], digest[:16], size))
        print('（先让 updates.json 与本产物一致，再输出）')
        return 1

    name = target_name(facts, APK, note=args.note, release=args.release)
    target = args.out / name
    print('产物 : %s' % APK)
    print('版本 : %s  (versionCode %s)' % (facts['versionName'], facts['versionCode']))
    print('签名 : %s' % facts['cert'])
    print('大小 : {:,} B'.format(size))
    print('sha256: %s' % digest)
    print('目标 : %s' % target)

    if args.dry_run:
        print('\n--dry-run：未复制')
        return 0

    args.out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(APK, target)
    if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
        print('FAIL COPY_CORRUPTED: 复制后摘要不一致')
        return 1
    # 2026-11-11：文件名可含中文（--note 标签），这里不能再用 ascii 编码，
    # 否则 sha256 校验文件写不出去（实测 UnicodeEncodeError）。
    # sha256sum 本身按字节比对，UTF-8 文件名可被 --check 正常读取。
    target.with_suffix('.apk.sha256').write_text(
        '%s  %s\n' % (digest, target.name), encoding='utf-8')
    print('已输出：%s' % target)
    return 0


if __name__ == '__main__':
    sys.exit(main())
