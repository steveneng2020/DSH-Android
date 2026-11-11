#!/usr/bin/env python3
"""T7(G5)：受管运行时测试夹具的只读探针。

原状态：manifest 与 app/build.gradle 里 prepare-test-runtime 出现次数均为 0，没有任何入口。
新状态：本文件 + manifest 的 runtimeFixture 声明 + gradle 的 prepareTestRuntime/verifyTestRuntimeFixture。
依据命令：python3 tools/check-test-runtime-fixture.py --check --json
复跑命令：同上；缺夹具时的聚合提示见 reports/t75/evidence/04-g5-runtime-fixture.txt。


原状态是「没有入口」：tools/host-tests.manifest.json 与 app/build.gradle 里
`prepare-test-runtime` 的出现次数都是 0，`--stage all` 有 74 条测试各自撞
`Run python tools/prepare-test-runtime.py first`，而没有任何一处告诉执行者
夹具是什么、怎么准备、缺了会影响多少条。

本脚本只读：不生成、不下载、不改任何文件。它回答三个问题：
  1 夹具指针 app/build/test-runtimes/current.json 在不在；
  2 清单里有多少条测试依赖夹具（按 runtimeFixture.requires 判，不靠字符串匹配）；
  3 缺失时，受影响的是哪些 stage、以及该跑哪条命令。

退出码：夹具就绪 → 0；缺失但不影响任何选中 stage → 0；缺失且清单里有依赖 → 1。
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'tools/host-tests.manifest.json'


def probe(root=None):
    root = Path(root or ROOT).resolve()
    manifest = root / 'tools/host-tests.manifest.json'
    data = json.loads(manifest.read_text(encoding='utf-8'))
    fixture = data.get('runtimeFixture')
    if not isinstance(fixture, dict):
        raise ValueError('TEST_MANIFEST_RUNTIME_FIXTURE_MISSING')
    needs = set(fixture.get('requires') or [])
    if not needs:
        raise ValueError('TEST_MANIFEST_RUNTIME_FIXTURE_REQUIRES_EMPTY')
    pointer = root / fixture['pointer']
    rows = [row for row in data['tests'] if set(row.get('requires') or []) & needs]
    stages = {}
    for row in rows:
        stages[row['stage']] = stages.get(row['stage'], 0) + 1
    pointer_data = None
    if pointer.is_file():
        try:
            pointer_data = json.loads(pointer.read_text(encoding='utf-8'))
        except ValueError as error:
            raise ValueError('TEST_RUNTIME_POINTER_JSON: ' + str(error))
    return {
        'status': 'PASS_TEST_RUNTIME_FIXTURE' if pointer.is_file() else 'TEST_RUNTIME_FIXTURE_MISSING',
        'pointer': fixture['pointer'],
        'producer': fixture['producer'],
        'requires': sorted(needs),
        'affected': len(rows),
        'affectedByStage': dict(sorted(stages.items())),
        'pointerPresent': pointer.is_file(),
        'dshVersion': (pointer_data or {}).get('dshVersion'),
        'archiveCurrent': (pointer_data or {}).get('archiveCurrent'),
        'prepare': 'python3 %s --offline' % fixture['producer'],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description='报告受管运行时测试夹具状态（只读）。')
    parser.add_argument('--check', action='store_true', help='执行探针（默认动作）')
    parser.add_argument('--json', action='store_true', help='以 JSON 输出')
    parser.add_argument('--root', help='仓库根目录（默认按本文件位置推导）')
    args = parser.parse_args(argv)
    try:
        result = probe(args.root)
    except Exception as error:
        print('FAIL_TEST_RUNTIME_FIXTURE: ' + str(error), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result['pointerPresent']:
        print('PASS test runtime fixture: %s (dshVersion %s, archiveCurrent %s), %d 条测试依赖'
              % (result['pointer'], result['dshVersion'], result['archiveCurrent'], result['affected']))
    else:
        print('TEST_RUNTIME_FIXTURE_MISSING: %s 不存在；%d 条测试受影响（%s）；先跑 `%s`'
              % (result['pointer'], result['affected'],
                 ', '.join('%s=%d' % item for item in result['affectedByStage'].items()),
                 result['prepare']))
    if result['pointerPresent']:
        return 0
    return 1 if result['affected'] else 0


if __name__ == '__main__':
    sys.exit(main())
