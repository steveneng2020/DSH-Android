#!/usr/bin/env python3
"""按 README 的描述重绘「鲲」启动图标（单剪影 / 无玉璧双环 / 无描金）。

## 形状定义（改图标先读这段）

README 的判据三句话，逐一对应到实现：

- **一尾鲲**：侧视鱼形，头朝右、尾在左，背拱腹深，尾鳍分叉。
- **单剪影**：整条鱼是**一个颜色、一块实心形**。没有眼睛、鳞、鳃线、
  没有任何内部线条。**鳍必须是轮廓本身的凸起，不能是叠加上去的独立图形** ——
  叠加一旦没对准，就会变成悬浮碎片，那不是剪影。
- **无玉璧双环**：不套圆形环框。
- **无描金**：无金色描边 / 外发光 / 高光边；鱼身只有一种颜色。

## 走过的弯路（别再犯）

1. 第一版把鱼体、背鳍、胸鳍、尾鳍做成**四个独立多边形靠叠加**。
   胸鳍没叠进鱼体 ⇒ 出现一块**悬浮的独立碎片**，直接违反「单剪影」。
2. 鱼体用「背线 + reversed(腹线)」拼多边形。腹线本来就是尾→吻，
   反转后路径从尾部跳回吻端，**多边形自交，鱼身沿中线裂成上下两片**。
   教训：闭合轮廓的环绕顺序必须一路走通，不能中途折返。

现在用 **OUTLINE 一条闭合点列**：吻端→背线→背鳍凸起→背线→尾上叶→
尾内凹→尾下叶→腹线→胸鳍凸起→腹线→回到吻端。从结构上保证只有一块形。

## 产出

    drawable-nodpi/dsha_brand_fg_<scheme>.png      自适应图标前景（512，画满画布）
    mipmap-<dpi>/ic_launcher_<scheme>.png          圆角矩形（旧系统 / IconSwitcher.PREVIEWS）
    mipmap-<dpi>/ic_launcher_round_<scheme>.png    圆形（Manifest 的 roundIcon）
    docs/assets/icon/<scheme>.png                  README 展示图（512）

前景画满画布是对的：`drawable/dsha_launcher_foreground_<scheme>.xml` 是
`<inset inset="16.67%">`，那一步会把前景缩进到中央 66.7%（自适应图标安全区）。

    python3 tools/render-kun-icon.py            # 全部重绘
    python3 tools/render-kun-icon.py --check    # 只校验，不写文件
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / 'app/src/main/res'
DOCS_ICON = ROOT / 'docs/assets/icon'

# 与 res/values/launcher_icon.xml 的 dsha_launcher_background_<scheme> 一致
BACKGROUNDS = {
    'default': '#5C2E0A',
    'moyu':    '#1A1A1A',
    'tianqing': '#14286B',
    'zheshi':  '#4E0C0C',
    'biyu':    '#0E3A1C',
    'zishou':  '#3A1259',
}

# 鱼身单色（不描金）
FOREGROUNDS = {
    'default': '#E8C87A',
    'moyu':    '#D2D2D2',
    'tianqing': '#A8CDE8',
    'zheshi':  '#DDA76A',
    'biyu':    '#93D6AC',
    'zishou':  '#CBA9EA',
}

DENSITIES = {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}
SUPERSAMPLE = 4
FG_SIZE = 512
ICON_SIZE = 512

# 一条闭合轮廓：吻端(右) → 背线 → 背鳍凸起 → 背线 → 尾上叶 → 尾内凹 →
# 尾下叶 → 腹线 → 胸鳍凸起 → 腹线 → 回到吻端。
OUTLINE = [
    # 吻端（右）→ 背线向后
    (0.530, 0.000),
    (0.497, 0.058),
    (0.432, 0.118),
    (0.335, 0.168),
    (0.225, 0.202),
    (0.150, 0.214),
    # 背鳍：宽基三角帆，峰顶落在基座中后段。
    # 注意别把它读成「朝前的刺」—— 鱼头朝右，尾在左，鳍尖朝左后方是后掠，正常。
    (0.072, 0.222),
    (-0.010, 0.300),
    (-0.092, 0.352),
    (-0.175, 0.316),
    (-0.238, 0.226),
    # 背线继续到尾柄
    (-0.335, 0.162),
    (-0.420, 0.092),
    (-0.472, 0.046),
    # 尾：上叶 → 内凹 → 下叶（鲲尾宜大）
    (-0.598, 0.158),
    (-0.786, 0.272),
    (-0.632, 0.014),
    (-0.772, -0.176),
    (-0.690, -0.238),
    # 尾根下缘平滑接腹线
    (-0.505, -0.058),
    (-0.448, -0.030),
    # 腹线：一路平滑向前，**不要加任何下垂凸起**。
    # 2026-11-12 教训：加过一处腹鳍凸起（约 x=0.06 处的 -0.20 → -0.26），
    # 在圆形遮罩里看起来像肚子上挂了一块异物，不是鳍。鲲在 README 里
    # 只要求「一尾鲲、单剪影」，没有要求画全所有鳍；少画一个鳍远好过留一个瘤。
    (-0.345, -0.092),
    (-0.215, -0.152),
    (-0.065, -0.192),
    (0.062, -0.204),
    (0.195, -0.186),
    (0.325, -0.150),
    (0.443, -0.088),
    (0.508, -0.028),
]


def _catmull_rom(points, samples=14, closed=True):
    """Catmull-Rom 插值。多边形直接画会有折角，必须平滑。"""
    pts = list(points)
    if closed:
        pts = [pts[-1]] + pts + [pts[0], pts[1]]
    else:
        pts = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(len(pts) - 3):
        p0, p1, p2, p3 = pts[i], pts[i + 1], pts[i + 2], pts[i + 3]
        for s in range(samples):
            t = s / samples
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                       + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                       + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    return out


def kun_polygon():
    """返回唯一那条闭合曲线。多于一条就意味着「叠加」，禁止。"""
    return _catmull_rom(OUTLINE)


def draw_kun(size, color, fill_ratio=0.90):
    """在 size×size 透明画布上居中画出鲲，返回 RGBA 图层。"""
    from PIL import Image, ImageDraw

    big = size * SUPERSAMPLE
    layer = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    poly = kun_polygon()
    # 归一化系 y 向上为正，图像系 y 向下为正 ⇒ 映射时必须取负。
    # 2026-11-12 教训：漏了这一步，整条鱼**上下镜像** —— 背鳍被画到肚子上
    # （圆形遮罩里看成一个下垂的瘤），背部反而成了平边。图仍「像鱼」，
    # 所以肉眼很容易放过；必须靠 audit_single_silhouette 的方向判据拦住。
    flipped = [(p[0], -p[1]) for p in poly]
    xs = [p[0] for p in flipped]
    ys = [p[1] for p in flipped]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    bw, bh = x1 - x0, y1 - y0
    scale = (big * fill_ratio) / max(bw, bh)
    ox = (big - bw * scale) / 2 - x0 * scale
    oy = (big - bh * scale) / 2 - y0 * scale
    ImageDraw.Draw(layer).polygon(
        [(p[0] * scale + ox, p[1] * scale + oy) for p in flipped], fill=color)
    return layer.resize((size, size), Image.LANCZOS)


def _rounded_mask(size, radius_ratio=0.22):
    from PIL import Image, ImageDraw
    big = size * SUPERSAMPLE
    mask = Image.new('L', (big, big), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, big - 1, big - 1], radius=int(big * radius_ratio), fill=255)
    return mask.resize((size, size), Image.LANCZOS)


def _circle_mask(size):
    from PIL import Image, ImageDraw
    big = size * SUPERSAMPLE
    mask = Image.new('L', (big, big), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, big - 1, big - 1], fill=255)
    return mask.resize((size, size), Image.LANCZOS)


def compose(scheme, size, shape='rounded'):
    """背景色 + 鲲，按 shape 裁形（square / rounded / round）。"""
    from PIL import Image

    plate = Image.new('RGBA', (size, size), BACKGROUNDS[scheme])
    plate.alpha_composite(draw_kun(size, FOREGROUNDS[scheme]))
    if shape == 'round':
        plate.putalpha(_circle_mask(size))
    elif shape == 'rounded':
        plate.putalpha(_rounded_mask(size))
    return plate


def foreground(scheme, size=FG_SIZE):
    """自适应图标前景：只含鱼形，背景透明，画满画布。"""
    from PIL import Image
    layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    layer.alpha_composite(draw_kun(size, FOREGROUNDS[scheme]))
    return layer


def audit_single_silhouette(scheme, size=256):
    """结构自检：证明「单剪影」不是靠肉眼说的。

    三条判据，对应 README 的「一尾鲲、单剪影」：
      1. 连通块 == 1 —— 多于 1 就说明有碎片（第一版胸鳍就是悬浮的独立块）
      2. 内部孔洞 == 0 —— 有孔洞说明鱼身里有镂空/线条（眼睛、鳃线、描边）
      3. 主色占比 >= 0.93 —— 只有一种颜色；剩余百分比是降采样抗锯齿产生的
         边缘过渡，不是描金。实测单一描金填充为 94.8%，若有第二层色块会明显下降。

    返回 (ok, 说明)。不通过时 main() 直接失败，避免把坏图写进仓库。
    """
    from collections import Counter, deque
    from PIL import Image

    image = foreground(scheme, size).convert('RGBA')
    width, height = image.size
    pixels = image.load()

    def solid(x, y):
        return pixels[x, y][3] > 128

    seen = [[False] * width for _ in range(height)]
    components = 0
    for y in range(height):
        for x in range(width):
            if solid(x, y) and not seen[y][x]:
                components += 1
                queue = deque([(x, y)])
                seen[y][x] = True
                while queue:
                    cx, cy = queue.popleft()
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = cx + dx, cy + dy
                        if (0 <= nx < width and 0 <= ny < height
                                and solid(nx, ny) and not seen[ny][nx]):
                            seen[ny][nx] = True
                            queue.append((nx, ny))

    outside = [[False] * width for _ in range(height)]
    queue = deque()
    for x in range(width):
        for y in (0, height - 1):
            if not solid(x, y) and not outside[y][x]:
                outside[y][x] = True
                queue.append((x, y))
    for y in range(height):
        for x in (0, width - 1):
            if not solid(x, y) and not outside[y][x]:
                outside[y][x] = True
                queue.append((x, y))
    while queue:
        cx, cy = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if (0 <= nx < width and 0 <= ny < height
                    and not solid(nx, ny) and not outside[ny][nx]):
                outside[ny][nx] = True
                queue.append((nx, ny))
    holes = sum(1 for y in range(height) for x in range(width)
                if not solid(x, y) and not outside[y][x])

    counter = Counter()
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a == 255:
                counter[(r, g, b)] += 1
    total = sum(counter.values()) or 1
    dominant = (counter.most_common(1)[0][1] / total) if counter else 0.0

    # 方向判据：背鳍尖必须是整条鱼**最高**的点，且它的水平位置应在鱼身中后段。
    # 若 y 忘取负（上下镜像），最高点会跑到最左端的尾鳍下叶，x 占比 < 0.25。
    xs = [x for y in range(height) for x in range(width) if solid(x, y)]
    top_y = min(y for y in range(height) if any(solid(x, y) for x in range(width)))
    top_xs = [x for x in range(width) if solid(x, top_y)] if xs else []
    span = (max(xs) - min(xs)) or 1
    top_fraction = ((sum(top_xs) / len(top_xs)) - min(xs)) / span if top_xs else 0.0

    problems = []
    if not (0.38 <= top_fraction <= 0.68):
        problems.append('最高点在横向 %.0f%% 处（应在 38~68%%，背鳍位置；'
                        '偏小说明鱼上下镜像了）' % (top_fraction * 100))
    if components != 1:
        problems.append('连通块 %d 个（应为 1，出现碎片）' % components)
    if holes != 0:
        problems.append('内部孔洞 %d 个（应为 0，出现镂空/线条）' % holes)
    if dominant < 0.93:
        problems.append('主色占比 %.1f%%（应 >= 93%%，出现第二种颜色）' % (dominant * 100))
    return (not problems), '块=%d 孔=%d 主色=%.1f%% 鳍位=%.0f%%' % (
        components, holes, dominant * 100, top_fraction * 100), problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--check', action='store_true', help='只校验，不写文件')
    args = parser.parse_args(argv)

    try:
        from PIL import Image
    except ImportError:
        print('FAIL MISSING_PILLOW', file=sys.stderr)
        return 1

    failed = False
    for scheme in BACKGROUNDS:
        ok, summary, issues = audit_single_silhouette(scheme)
        if not ok:
            failed = True
            for issue in issues:
                print('FAIL SILHOUETTE[%s]: %s' % (scheme, issue), file=sys.stderr)
        elif not args.check:
            print('  单剪影自检 %-9s %s' % (scheme, summary))
    if failed:
        return 1

    problems = []
    written = 0

    def emit(path, image):
        nonlocal written
        if args.check:
            if not path.is_file():
                problems.append('MISSING %s' % path.relative_to(ROOT))
                return
            actual = Image.open(path).convert('RGBA')
            if actual.size != image.size or actual.tobytes() != image.tobytes():
                problems.append('STALE %s' % path.relative_to(ROOT))
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, 'PNG', optimize=True)
        written += 1

    for scheme in BACKGROUNDS:
        emit(RES / ('drawable-nodpi/dsha_brand_fg_%s.png' % scheme),
             foreground(scheme))
        for dpi, px in DENSITIES.items():
            emit(RES / ('mipmap-%s/ic_launcher_%s.png' % (dpi, scheme)),
                 compose(scheme, px, 'rounded'))
            emit(RES / ('mipmap-%s/ic_launcher_round_%s.png' % (dpi, scheme)),
                 compose(scheme, px, 'round'))
        emit(DOCS_ICON / ('%s.png' % scheme), compose(scheme, ICON_SIZE, 'rounded'))

    if args.check:
        if problems:
            for problem in problems:
                print('FAIL KUN_ICON_%s' % problem, file=sys.stderr)
            return 1
        print('PASS kun icon: %d 套图标与生成器一致' % len(BACKGROUNDS))
        return 0

    print('已重绘 %d 个图标文件（%d 套配色）' % (written, len(BACKGROUNDS)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
