#!/usr/bin/env python3
"""把六套启动图标从 res 合成为 README 用的 PNG（docs/assets/icon/*.png）。

## 为什么要有这个脚本

2026-11-11 推送前检查发现 README 与 README.en.md 共 14 个链接错误：
`docs/assets/icon/{default,moyu,tianqing,zheshi,biyu,zishou}.png` 全部不存在。
README 用它们展示「六套配色」，缺图等于首页六张挂图。

手工用 PIL 补一次图能过门禁，但**换个会话就没人知道那 6 张图是怎么来的**，
改配色时也不会同步。所以固化成脚本：输入变了就重跑，输出可复现。

## 图标是怎么构成的（照 Android 自适应图标语义）

`mipmap-anydpi-v26/ic_launcher_<k>.xml` 声明：

    <background android:drawable="@color/dsha_launcher_background_<k>" />
    <foreground android:drawable="@drawable/dsha_launcher_foreground_<k>" />

而 `drawable/dsha_launcher_foreground_<k>.xml` 是一个 `<inset inset="16.67%">`，
包住 `@drawable/dsha_brand_fg_<k>`。那个 drawable 在 `drawable-nodpi/` 下，
是 512×512 的 RGBA 位图。

所以合成规则就是：**背景纯色 + 前景位图按 16.67% 内缩叠上去**，
再裁成圆角矩形（模拟桌面图标外形）。不要用 `mipmap-*/ic_launcher_fg_*.png`
—— 那是更旧的位图，图案与当前自适应图标不一致（本轮踩过：用它合出来的
是另一套鱼的造型，差点写进 README）。

## 跑法

    python3 tools/render-readme-icons.py            # 输出到 docs/assets/icon/
    python3 tools/render-readme-icons.py --check    # 只校验现有图是否与源一致

依赖 Pillow。`--check` 用逐像素比较，不依赖 PNG 字节，避免不同 zlib 版本误报。
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / 'app/src/main/res'
OUT = ROOT / 'docs/assets/icon'
SIZE = 512
CORNER_RATIO = 0.22
# 与 drawable/dsha_launcher_foreground_<k>.xml 的 android:inset="16.67%" 一致
INSET_RATIO = 0.1667

# 与 res/values/launcher_icon.xml 的 dsha_launcher_background_<k> 一致
BACKGROUNDS = {
    'default': (0x5C, 0x2E, 0x0A),
    'moyu': (0x1A, 0x1A, 0x1A),
    'tianqing': (0x14, 0x28, 0x6B),
    'zheshi': (0x4E, 0x0C, 0x0C),
    'biyu': (0x0E, 0x3A, 0x1C),
    'zishou': (0x3A, 0x12, 0x59),
}


def compose(key):
    from PIL import Image, ImageDraw

    source = RES / ('drawable-nodpi/dsha_brand_fg_%s.png' % key)
    if not source.is_file():
        raise SystemExit('MISSING_FOREGROUND: %s' % source)
    rgb = BACKGROUNDS[key]

    plate = Image.new('RGBA', (SIZE, SIZE), rgb + (255,))
    mask = Image.new('L', (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, SIZE - 1, SIZE - 1], radius=int(SIZE * CORNER_RATIO), fill=255)
    canvas = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    canvas.paste(plate, (0, 0), mask)

    foreground = Image.open(source).convert('RGBA')
    if foreground.size != (SIZE, SIZE):
        foreground = foreground.resize((SIZE, SIZE), Image.LANCZOS)
    inset = int(round(SIZE * INSET_RATIO))
    inner = SIZE - inset * 2
    foreground = foreground.resize((inner, inner), Image.LANCZOS)
    canvas.alpha_composite(foreground, (inset, inset))
    return canvas


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--check', action='store_true',
                        help='只校验现有 PNG 是否与当前资源一致，不写文件')
    args = parser.parse_args(argv)

    try:
        from PIL import Image
    except ImportError:
        print('FAIL MISSING_PILLOW: 需要 Pillow（pip install Pillow）', file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    problems = []
    for key in BACKGROUNDS:
        expected = compose(key)
        target = OUT / ('%s.png' % key)
        if args.check:
            if not target.is_file():
                problems.append('MISSING: %s' % target.relative_to(ROOT))
                continue
            actual = Image.open(target).convert('RGBA')
            if actual.size != expected.size:
                problems.append('SIZE: %s %s != %s'
                                % (target.name, actual.size, expected.size))
                continue
            # 逐像素比较：不受 PNG 编码器版本影响
            if actual.tobytes() != expected.tobytes():
                problems.append('STALE: %s 与当前 res 资源不一致，请重跑本脚本'
                                % target.relative_to(ROOT))
            continue
        expected.save(target, 'PNG', optimize=True)
        print('%-9s %6d B  %s' % (key, target.stat().st_size, target.relative_to(ROOT)))

    if args.check:
        if problems:
            for problem in problems:
                print('FAIL README_ICON_%s' % problem, file=sys.stderr)
            return 1
        print('PASS README icons: %d 套与 res 资源逐像素一致' % len(BACKGROUNDS))
    return 0


if __name__ == '__main__':
    sys.exit(main())
