#!/usr/bin/env python3
"""G13：版本号分隔符必须统一为「・」（U+30FB 全角中点）。

## 这条门禁为什么存在

2026-11-12 用户在真机截图上指出更新页版本行的分隔符位置不对：
「DSHA v1.4 20261111@0.2.2-rc.1 ? build20050357」里 `build` 前面那个符号偏低。

排查发现两层问题：

1. 字符选错：原本用 `•`（U+2022 BULLET）。它是给列表符号设计的，字形天生偏基线下方，
   放进「两侧都是正文数字」的位置就掉下去。试过 `baselineShift` 手动上移与
   `ReplacementSpan` 自算中心两种修法，都要依赖系统字体猜系数，换字体即失准。
   **换字符比修字形可靠**：`・`（U+30FB KATAKANA MIDDLE DOT）天生在中线附近。
2. 没有统一入口：7 处版本号拼接各自硬编码字面量，改一处改不全。

所以判据是：全仓版本号分隔一律走 `util/VersionSeparator`，且它的 GLYPH 必须是 U+30FB。

## 判据

① 除 VersionSeparator 外，Java/XML 源里不允许出现 `"•"` 或 `"・"` 的字面量拼接
② VersionSeparator.GLYPH 必须是 U+30FB
③ 不允许再引入 baselineShift / MetricAffectingSpan 之类的字形修正
   —— 换字符之后不需要它，留着只会让下一个人以为还要靠系数调

## 为什么第 ③ 条值得单独查

我在这上面耗了三轮：先写 `+=` 累加导致偏移越叠越高，又凭经验取 -0.10em 而没拿
用户真实字体验证。教训是「能用字符解决的，不要用排版 hack」，第 ③ 条就是防止
后人把 hack 加回来。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEP = ROOT / 'app/src/main/java/com/deepseekharness/app/util/VersionSeparator.java'
GLYPH = '\u30fb'
# 历史上用过的分隔符，都不允许再作为字面量出现在调用点
LEGACY = ['\u2022', '\u00b7']
SCAN_SUFFIXES = {'.java', '.xml'}
SKIP_DIRS = {'build', '.gradle', '.git'}


def iter_sources():
    for root in (ROOT / 'app/src/main', ROOT / 'app/src/test'):
        if not root.is_dir():
            continue
        for path in root.rglob('*'):
            if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            yield path


def main():
    problems = []

    # ① 只查「版本号与 build 号之间」的分隔符。
    #
    # 2026-11-12 第一版判据写的是「全仓不许出现 · 或 • 字面量」，结果报了 80 多处 ——
    # 那些全是「包名 · Android 14」「已启用 · 3」这类普通分隔，与版本号无关。
    # **判据范围划错会制造大量假红，反而让人忽略真正的问题**（MEMORY §4 第 40 条）。
    #
    # 正确范围：同一行里同时出现版本号特征（build / VERSION_ / version）与分隔符字面量。
    literal = re.compile(r'"\s*[' + ''.join(LEGACY) + r']\s*"')
    version_hint = re.compile(r'build|VERSION_|version|versionName', re.IGNORECASE)
    offenders = []
    for path in iter_sources():
        if path == SEP:
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.split('\n'), 1):
            stripped = line.lstrip()
            if stripped.startswith(('//', '*', '/*')):
                continue
            if literal.search(line) and version_hint.search(line):
                offenders.append('%s:%d  %s'
                                 % (path.relative_to(ROOT), lineno, stripped[:90]))
    if offenders:
        problems.append(
            '版本号分隔符仍是硬编码字面量，必须改用 VersionSeparator.between(left, right)：\n      '
            + '\n      '.join(offenders))

    # ② ③ VersionSeparator 自身
    if not SEP.is_file():
        problems.append('缺少 app/src/main/java/com/deepseekharness/app/util/VersionSeparator.java')
    else:
        src = SEP.read_text(encoding='utf-8')
        m = re.search(r'GLYPH\s*=\s*"([^"]*)"', src)
        if not m:
            problems.append('VersionSeparator 里找不到 GLYPH 常量')
        else:
            decoded = m.group(1).encode().decode('unicode_escape')
            if decoded != GLYPH:
                problems.append('VersionSeparator.GLYPH 是 U+%04X，期望 U+30FB「・」'
                                % (ord(decoded[0]) if decoded else 0))
        # 只看代码行，注释里提到这些词是允许的（本文件头就在解释为什么放弃它们）
        code_lines = [ln for ln in src.split('\n')
                      if not ln.lstrip().startswith(('//', '*', '/*'))]
        code = '\n'.join(code_lines)
        if ('baselineShift' in code or 'MetricAffectingSpan' in code
                or 'ReplacementSpan' in code):
            problems.append(
                'VersionSeparator 又引入字形修正（baselineShift / MetricAffectingSpan / '
                'ReplacementSpan）。换字符后不需要它 —— 见 MEMORY §4 第 58 条：'
                '能用字符解决的就不要用排版 hack')

    if problems:
        for problem in problems:
            print('FAIL  G13 %s' % problem, file=sys.stderr)
        return 1
    print('G13 版本号分隔符：统一 U+30FB「・」，无字形修正 ✅')
    return 0


if __name__ == '__main__':
    sys.exit(main())
