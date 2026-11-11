#!/usr/bin/env python3
"""校验随包 GPL / LGPL 二进制与 tools/gpl-binaries.lock.json 是否仍一致。

## 为什么要这个脚本

THIRD_PARTY_NOTICES.md 长期对 libproot.so / libprootloader.so / libprootloader32.so
写「original Standard binary exact revision remains unverified」，对 libtalloc.so 写
「exact binary revision unverified」。这等于承认没人知道这些 GPL 二进制从哪来，
而 GPL-2.0 第 3 条要求分发方能提供对应源码。

2026-11-11 做了溯源（见 gpl-binaries.lock.json 的 versionEvidence / residualGap），
本脚本把「锁文件声明的 sha256」与「磁盘上实际二进制」绑死：任何一方变了都会红。
没有这一步，溯源结论过几轮就没人记得是否还成立。

## 检查内容

1. 锁文件 schema 合法、每个条目有 license / sha256 / bytes / upstream
2. 声明的二进制确实存在于 jniLibs，且 sha256 与 bytes 与锁文件一致
3. 锁文件里没登记的 GPL 类新二进制（按文件名 proot/talloc 识别）要报出来，
   避免有人偷偷换包而不更新溯源
4. residualGap 必须存在且非空 —— 不允许把「尚未证明」的部分悄悄删掉当已解决

## 跑法

    python3 tools/check-proot-provenance.py
    python3 tools/check-proot-provenance.py --json
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / 'tools/gpl-binaries.lock.json'
JNI = ROOT / 'app/src/main/jniLibs/arm64-v8a'
REQUIRED = ('license', 'sha256', 'bytes', 'upstream', 'status', 'residualGap')
# 需要纳入溯源的原生库名特征；命中但未登记即报错。
TRACKED_HINTS = ('proot', 'talloc')


def sha256_of(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)

    problems = []
    if not LOCK.is_file():
        print('FAIL PROVENANCE_LOCK_MISSING: %s' % LOCK)
        return 1
    lock = json.loads(LOCK.read_text(encoding='utf-8'))
    if lock.get('schema') != 1:
        problems.append('PROVENANCE_SCHEMA: 期望 schema=1')
    binaries = lock.get('binaries') or {}
    if not binaries:
        problems.append('PROVENANCE_EMPTY: 锁文件没有登记任何二进制')

    facts = []
    for name, row in sorted(binaries.items()):
        missing = [key for key in REQUIRED if not row.get(key)]
        if missing:
            problems.append('PROVENANCE_FIELD_MISSING: %s 缺 %s' % (name, ','.join(missing)))
            continue
        # residualGap 为空等于宣称「已完全证明」，这需要真的做到才允许。
        if row['status'] != 'fully-reproduced' and len(str(row['residualGap']).strip()) < 10:
            problems.append('PROVENANCE_GAP_ERASED: %s status=%s 但 residualGap 被清空，'
                            '不允许把未证明的部分当作已解决' % (name, row['status']))
        if not str(row['sha256']).startswith(tuple('0123456789abcdef')) or len(row['sha256']) != 64:
            problems.append('PROVENANCE_SHA_FORMAT: %s' % name)
            continue
        path = JNI / name
        if not path.is_file():
            problems.append('PROVENANCE_BINARY_MISSING: %s 不在 %s' % (name, JNI.relative_to(ROOT)))
            continue
        actual_sha = sha256_of(path)
        actual_bytes = path.stat().st_size
        if actual_sha != row['sha256']:
            problems.append('PROVENANCE_SHA_MISMATCH: %s\n'
                            '    锁文件: %s\n'
                            '    实际  : %s' % (name, row['sha256'], actual_sha))
        if actual_bytes != row['bytes']:
            problems.append('PROVENANCE_BYTES_MISMATCH: %s 锁文件 %s / 实际 %s'
                            % (name, row['bytes'], actual_bytes))
        facts.append({'name': name, 'license': row['license'],
                      'version': (row['upstream'] or {}).get('version'),
                      'status': row['status']})

    # 未登记但看起来属于 GPL 家族的二进制
    if JNI.is_dir():
        for path in sorted(JNI.glob('*.so')):
            if path.name in binaries:
                continue
            if path.name in (lock.get('notDistributed') or {}):
                continue
            if any(hint in path.name.lower() for hint in TRACKED_HINTS):
                problems.append('PROVENANCE_UNREGISTERED: %s 命中 GPL 家族特征但未在锁文件登记'
                                % path.name)

    if args.json:
        print(json.dumps({'problems': problems, 'binaries': facts}, ensure_ascii=False, indent=2))
    elif problems:
        for problem in problems:
            print('FAIL ' + problem)
        print('\n更新办法：核对新二进制的真实来源后修改 tools/gpl-binaries.lock.json，'
              '并在 GPL-SOURCE-OFFER.md 同步披露 residualGap。不要只改 sha256 了事。')
    else:
        print('PASS GPL 二进制溯源：%d 项与锁文件一致（%s）'
              % (len(facts), ', '.join('%s=%s' % (f['name'], f['status']) for f in facts)))
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
