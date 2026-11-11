#!/usr/bin/env python3
"""T7(G10)：受管运行时输入契约的真入口，校验契约与 runtime-descriptor.json 的一致性。

原状态：`python3 tools/runtime_input_contract.py --check` 零输出 rc=0（空跑假绿）。
新状态：本文件是真校验（结构 / 实体 / 描述符 / runtimeId 四层），任何不一致 rc=1。
依据命令：python3 tools/check-runtime-input-contract.py --check --json
复跑命令：同上；反证见 reports/t75/evidence/05-g10-runtime-input-contract.txt。


## 为什么是一个新文件，而不是给 tools/runtime_input_contract.py 加 __main__

G10 的原状是 `python3 tools/runtime_input_contract.py --check` 打印零字节、rc=0
—— 空跑假绿。任务书给了两条修法（删掉 / 改成转发 prepare-runtime-descriptor.py
--check），实测**两条都被同一道硬约束挡住**：

`app/src/main/assets/dsh-runtime.inputs.json` 的 `inputs` 逐字节 pin 了
`tools/runtime_input_contract.py` 的 sha256（现值
5c0ae822c8b8049a5421cc6bfdad5cf834aa306941e573f357c725a8bc47a10c），而这个
pin 有两处活引用：
  - tools/build-dsh-runtime.py:89 —— 归档构建的 recipe
  - tools/prepare-standard-assets.py:145-152 —— 出包前校验
     metadata['inputs'] 必须等于 live recipe，否则抛错
所以改动该文件任何一个字节，都会让 122 MB 的 app/src/main/assets/dsh-runtime.bin
的 archive_sha256 失配，直接打断 `:app:assembleStandardRelease`，并且会改写
runtime-descriptor.json 的 runtimeId（t65 审计冻结的
0396a5081c9ff7e2b65778d41a8fea8d8ac8028ac9efa866a500ed195cc12f0d 会变）。

最小修法（需发布执行者，不在本任务范围）：改库 → 跑
`python3 tools/build-dsh-runtime.py` 重建 dsh-runtime.bin 与
dsh-runtime.inputs.json → 跑 `tools/prepare-runtime-descriptor.py --write`
→ 重打 standard/low 两个包 → 重做 t65 级审计。本任务不许重打包，因此不动它。

## 本文件做了什么

把「契约 + 描述符 + 实体文件」三方对齐做成真校验，任何不一致都非零退出：
  A 契约结构：managed-runtime-inputs.json 满足 runtime_input_contract.load()
  B 实体齐备：assetFiles / assetTrees / installs.asset 全部在盘且不越界
  C 描述符一致：runtime-descriptor.json 的 inputs / launcherInputs 与实体
    sha256 逐条相等，且双向无多无缺
  D 摘要可复算：用与 prepare-runtime-descriptor.py 相同的契约算法重算
    runtimeId，必须等于描述符里写的那一个（这一条才能抓「描述符是手改的」）

跑法：
    python3 tools/check-runtime-input-contract.py            # 等价 --check
    python3 tools/check-runtime-input-contract.py --check --json
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import runtime_input_contract as contract  # noqa: E402  (只当库用，不加 __main__)


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(data)
    return value.hexdigest()


def build_runtime_id(root):
    """与 tools/prepare-runtime-descriptor.py 的 build_descriptor 同一算法。"""
    root = Path(root)
    assets = root / 'app/src/main/assets'
    spec = contract.load(root)
    inputs = {p.relative_to(assets).as_posix(): digest(p)
              for p in contract.asset_paths(root, spec)}
    launchers = {name: digest(path) for name, path in contract.launcher_paths(root, spec).items()}
    version = json.loads((root / 'tools/dsh-runtime/package.json').read_text(encoding='utf-8'))[
        'dependencies']['@deepseek-ai/dsh']
    source = (root / 'tools/prepare-runtime-descriptor.py').read_text(encoding='utf-8')
    namespace = {}
    # READ_COMPATIBILITY 是描述符契约的一部分，直接取真源，不在这里复制一份。
    marker = 'READ_COMPATIBILITY = {'
    start = source.index(marker)
    end = source.index('\n}', start) + 2
    exec(compile(source[start:end], 'prepare-runtime-descriptor.py', 'exec'), namespace)
    previous = namespace['READ_COMPATIBILITY'].get(version, [])
    payload = {'baseVersion': (assets / 'offline-rootfs.version').read_text().strip(),
               'dshVersion': version, 'launcherContract': 'DSHA_ARM64_V2',
               'launcherInputs': launchers, 'bridgeProtocol': 3,
               'dataRead': previous + ['dsh-' + version], 'dataWrite': 'dsh-' + version,
               'inputs': inputs}
    identity = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return identity, len(inputs), len(launchers)


def check(root=None, descriptor=None):
    root = Path(root or ROOT).resolve()
    spec = contract.load(root)
    assets = root / 'app/src/main/assets'
    problems = []

    physical = contract.asset_paths(root, spec)          # B：不存在会抛 ValueError
    launchers = contract.launcher_paths(root, spec)

    target = Path(descriptor) if descriptor else assets / 'runtime-descriptor.json'
    if not target.is_file():
        raise ValueError('RUNTIME_DESCRIPTOR_MISSING: ' + str(target))
    declared = json.loads(target.read_text(encoding='utf-8'))
    if declared.get('version') != 1:
        problems.append('RUNTIME_DESCRIPTOR_VERSION: %r' % (declared.get('version'),))
    described = declared.get('inputs')
    described_launchers = declared.get('launcherInputs')
    if not isinstance(described, dict):
        problems.append('RUNTIME_DESCRIPTOR_INPUTS_TYPE')
        described = {}
    if not isinstance(described_launchers, dict):
        problems.append('RUNTIME_DESCRIPTOR_LAUNCHERS_TYPE')
        described_launchers = {}

    # C：实体 → 描述符
    for path in physical:
        name = path.relative_to(assets).as_posix()
        actual = digest(path)
        if name not in described:
            problems.append('RUNTIME_INPUT_UNDECLARED: ' + name)
        elif described[name] != actual:
            problems.append('RUNTIME_INPUT_DIGEST: ' + name)
    # C：描述符 → 实体（多出来的键一律失败，防止描述符里留已删文件的幽灵）
    present = {path.relative_to(assets).as_posix() for path in physical}
    for name in sorted(described):
        if name not in present:
            problems.append('RUNTIME_INPUT_ABSENT: ' + name)
    for name, path in sorted(launchers.items()):
        actual = digest(path)
        if name not in described_launchers:
            problems.append('RUNTIME_LAUNCHER_UNDECLARED: ' + name)
        elif described_launchers[name] != actual:
            problems.append('RUNTIME_LAUNCHER_DIGEST: ' + name)
    for name in sorted(described_launchers):
        if name not in launchers:
            problems.append('RUNTIME_LAUNCHER_ABSENT: ' + name)

    # D：runtimeId 必须能从契约重算出来
    if not problems:
        computed, asset_count, launcher_count = build_runtime_id(root)
        if computed != declared.get('runtimeId'):
            problems.append('RUNTIME_ID_MISMATCH: 描述符 %r ≠ 重算 %r'
                            % (declared.get('runtimeId'), computed))
    else:
        asset_count, launcher_count, computed = len(physical), len(launchers), None

    if problems:
        raise ValueError('; '.join(problems[:20]) + ('' if len(problems) <= 20
                                                     else ' (+%d more)' % (len(problems) - 20)))
    return {'status': 'PASS_RUNTIME_INPUT_CONTRACT', 'runtimeId': computed,
            'assets': asset_count, 'launchers': launcher_count,
            'descriptor': target.relative_to(root).as_posix()}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='真校验受管运行时输入契约（结构 / 实体 / 描述符 / runtimeId 四层）。')
    parser.add_argument('--check', action='store_true', help='执行校验（默认动作）')
    parser.add_argument('--json', action='store_true', help='以 JSON 输出')
    parser.add_argument('--root', help='仓库根目录（默认按本文件位置推导）')
    parser.add_argument('--descriptor', help='runtime-descriptor.json 路径（默认取仓库内那份）')
    args = parser.parse_args(argv)
    try:
        result = check(args.root, args.descriptor)
    except Exception as error:
        print('FAIL_RUNTIME_INPUT_CONTRACT: ' + str(error), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print('PASS runtime input contract: %d assets, %d launchers, runtimeId %s'
              % (result['assets'], result['launchers'], result['runtimeId']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
