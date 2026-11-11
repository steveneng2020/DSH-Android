#!/usr/bin/env python3
"""G13：版本号分隔符必须是 U+2022「•」，且必须经 VersionSeparator 做基线修正。

## 这条门禁为什么存在

2026-11-12 用户在真机截图上圈出更新页的版本行：
「DSHA v1.4 20261111@0.2.2-rc.1 • build20050357」里的那个圆点**明显偏低**，
与两侧数字不在同一条视觉中线上。

排查发现两个问题叠在一起：

1. `•`（U+2022 BULLET）的字形本身就偏基线下方 —— 它是给列表符号设计的，
   不是给「两侧都是正文数字」的行内分隔设计的。直接拼进字符串必然偏低。
2. 全仓有 7 处版本号拼接，**每处都各自硬编码 `" • "`**，没有任何统一的修正入口。
   于是「改一处」永远改不全，也无法复用垂直居中的处理。

所以修法是：所有版本号分隔一律走 `util/VersionSeparator`，
由它统一施加 `TextPaint.baselineShift`。

## 判据

① 全仓 Java/XML 源里，**不允许**再出现 `" • "` 这种字面量拼接（除非在
   VersionSeparator 自己内部）。
② `VersionSeparator.GLYPH` 必须是 U+2022。
③ `VersionSeparator` 必须真的做了基线修正（`baselineShift` + `MetricAffectingSpan`），
   否则它只是个字符串常量包装，等于没修。

## 为什么不用「检查有没有字符串 •」这么简单

历史教训（MEMORY §4 第 40 条）：断言「产物里有这个字符串」不等于「它按预期工作」。
所以第 ③ 条专门验证**修正机制存在**，而不是只验证字符对不对。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEP = ROOT / 'app/src/main/java/com/deepseekharness/app/util/VersionSeparator.java'
BULLET = '\u2022'
# 版本号拼接的字面量形态：引号里只有空格 + 圆点（可能带 build 等后缀）
LITERAL = re.compile(r'"\s*' + re.escape(BULLET) + r'\s*"')
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

    # ① 字面量拼接：除 VersionSeparator 外一律不允许
    offenders = []
    for path in iter_sources():
        if path == SEP:
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.split('\n'), 1):
            if line.lstrip().startswith(('//', '*', '/*')):
                continue          # 注释里提到圆点是允许的
            if LITERAL.search(line):
                offenders.append('%s:%d  %s'
                                 % (path.relative_to(ROOT), lineno, line.strip()[:90]))
    if offenders:
        problems.append(
            '版本号分隔符仍是硬编码字面量「" • "」，必须改用 '
            'VersionSeparator.between(left, right)：\n      '
            + '\n      '.join(offenders))

    # ② ③ VersionSeparator 自身
    if not SEP.is_file():
        problems.append('缺少 app/src/main/java/com/deepseekharness/app/util/VersionSeparator.java')
    else:
        src = SEP.read_text(encoding='utf-8')
        glyph = re.search(r'GLYPH\s*=\s*"([^"]*)"', src)
        if not glyph:
            problems.append('VersionSeparator 里找不到 GLYPH 常量')
        else:
            raw = glyph.group(1)
            decoded = raw.encode().decode('unicode_escape')
            if decoded != BULLET:
                problems.append(
                    'VersionSeparator.GLYPH 是 U+%04X，期望 U+2022「•」'
                    % (ord(decoded[0]) if decoded else 0))
        if 'baselineShift' not in src:
            problems.append(
                'VersionSeparator 没有使用 baselineShift —— 圆点仍会偏低，'
                '等于只是把字符包了一层常量')
        if 'MetricAffectingSpan' not in src:
            problems.append(
                'VersionSeparator 没有用 MetricAffectingSpan / ReplacementSpan —— '
                'baseline 不会被排版引擎应用')

    if problems:
        for problem in problems:
            print('FAIL  G13 %s' % problem, file=sys.stderr)
        return 1
    print('G13 版本号分隔符：统一 U+2022 且经 VersionSeparator 修正基线 ✅')
    return 0


if __name__ == '__main__':
    sys.exit(main())
