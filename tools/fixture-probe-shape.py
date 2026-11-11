#!/usr/bin/env python3
"""校验 check-test-runtime-fixture.py 的 JSON 输出结构（只读，不判断夹具是否就绪）。

## 为什么单独成文件

2026-11-11 往 `.github/workflows/docs-check.yml` 里加这个校验时，第一版是内联
heredoc：`python3 - <<'PY' … PY`。但 YAML 的 `run: |` 块里每一行都带缩进，
heredoc 的**结束标记也带上了缩进**，shell 就不认它，脚本会在 CI 里诡异地
把后续行当成 Python 源码继续喂进去。这类错误本地跑 `python3 tools/xxx.py`
完全复现不出来，只有 CI 上炸。

**结论：workflow 里不要写内联 heredoc，宁可多一个文件。**

## 判据边界

本脚本只回答「探针输出的结构对不对」，不回答「夹具准没准备好」。

- 夹具未准备 ⇒ `check-test-runtime-fixture.py` 返回 1，但 JSON 结构仍然合法，
  那是 CI 的正常状态（夹具是本地构建产物，在 `.gitignore` 里）。**不算失败。**
- 结构损坏（缺键、类型不对）⇒ 说明探针本身坏了，**必须失败** ——
  否则一条永远绿、永远没在查东西的检查会混过去（MEMORY §4 第 40 条）。

退出码：结构合法 → 0；结构损坏或输入不可解析 → 1。
"""
import json
import sys

REQUIRED_KEYS = {
    'pointer': str,
    'producer': str,
    'prepare': str,
    'pointerPresent': bool,
    'affected': int,
    'affectedByStage': dict,
}


def main(argv):
    if len(argv) != 2:
        print('用法: python3 tools/fixture-probe-shape.py <fixture.json>', file=sys.stderr)
        return 2
    try:
        with open(argv[1], encoding='utf-8') as handle:
            data = json.load(handle)
    except Exception as error:
        print('FAIL FIXTURE_PROBE_SHAPE: 无法解析探针输出：%s' % error, file=sys.stderr)
        return 1
    if not isinstance(data, dict):
        print('FAIL FIXTURE_PROBE_SHAPE: 顶层不是对象', file=sys.stderr)
        return 1
    problems = []
    for key, kind in REQUIRED_KEYS.items():
        if key not in data:
            problems.append('缺键 %s' % key)
        elif not isinstance(data[key], kind):
            problems.append('%s 类型是 %s，期望 %s'
                            % (key, type(data[key]).__name__, kind.__name__))
    stages = data.get('affectedByStage')
    if isinstance(stages, dict):
        for name, count in stages.items():
            if not isinstance(count, int):
                problems.append('affectedByStage.%s 不是整数' % name)
        if sum(stages.values()) != data.get('affected') and not problems:
            problems.append('affectedByStage 之和 %d 与 affected %s 不一致'
                            % (sum(stages.values()), data.get('affected')))
    if problems:
        for problem in problems:
            print('FAIL FIXTURE_PROBE_SHAPE: ' + problem, file=sys.stderr)
        return 1
    state = '已就绪' if data['pointerPresent'] else '未准备（CI 正常）'
    print('PASS fixture probe shape: 夹具%s，清单声明 %d 条依赖（%s）'
          % (state, data['affected'],
             ', '.join('%s=%d' % item for item in sorted(data['affectedByStage'].items()))))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
