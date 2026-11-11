package com.deepseekharness.app.util;

import android.text.SpannableStringBuilder;
import android.text.Spanned;
import android.text.TextPaint;
import android.text.style.MetricAffectingSpan;

/**
 * 版本号分隔符「•」的垂直居中修正。
 *
 * <p><b>为什么需要这个类</b>：{@code •}（U+2022 BULLET）字形在设计上偏向基线下方 ——
 * 它本来是给列表项目符号用的，不是给「两侧都是正文数字」的行内分隔用的。直接写进 TextView
 * 看起来会「掉下去」，与左右两段不在同一条视觉中线上（2026-11-12 用户在真机上指出）。
 *
 * <p><b>为什么不用 {@code ·}（U+00B7 MIDDLE DOT）</b>：中圆点确实天然居中，但笔画太轻，
 * 与「v1.4 20261111@0.2.2-rc.1」这种长串数字并排时几乎看不见。
 * 早期代码注释里写过「U+00B7 基线偏低」，那是不准确的 —— 真正的理由是笔画太轻。
 *
 * <p><b>为什么不用 {@code RelativeSizeSpan} 缩字号</b>：缩放只改大小不改基线位置，
 * 低就是低，实测无效。必须改成基线。
 *
 * <p><b>为什么用 {@link MetricAffectingSpan} 而不是 {@code ReplacementSpan}</b>：
 * {@code TextPaint} 自带 {@code baselineShift} 字段，系统在排版时会把绘制基线整体平移，
 * 一行代码就能做到，且与字号、density、字体 metrics 全部自动适配。
 * 手写 {@code ReplacementSpan.draw} 需要自己算 ascent/x-height/字形中心，容易算错，
 * 而且出错时很难判断是算错了还是系数不对。
 */
public final class VersionSeparator {

  /**
   * 分隔符本身。
   *
   * <p><b>改这个字符之前先想清楚</b>：{@code tools/check-version-separator.py} 会检查
   * 全仓版本号分隔符是否统一为 U+2022，改动会直接让门禁变红。
   */
  public static final String GLYPH = "\u2022";

  /**
   * 基线补偿（单位：像素，随字号缩放）。
   *
   * <p>负值 = 向上提。{@code •} 偏低，所以取负。
   *
   * <p><b>这个值需要真机确认</b>：不同系统字体里 bullet 的实际位置不同（MIUI 可能换过字体）。
   * 0.10 倍字号是个保守初值 —— 偏少一点比过冲好，过冲会让圆点撞到上一行。
   * 调整方法：改这个数字 → 重新构建 → 装机看「关于页」的版本行。
   */
  private static final float BASELINE_SHIFT = -0.10f;

  private VersionSeparator() {}

  /**
   * 返回「左 + 空格 + 垂直居中• + 空格 + 右」的富文本。
   *
   * <p>两段内容都保持调用方传进来的原样，只把中间的分隔符换成带基线修正的 span，
   * 因此不会改动任何版本号字符串本身的来源。
   */
  public static CharSequence between(CharSequence left, CharSequence right) {
    SpannableStringBuilder builder = new SpannableStringBuilder();
    builder.append(left);
    builder.append(' ');
    int start = builder.length();
    builder.append(GLYPH);
    int end = builder.length();
    builder.setSpan(new ShiftedBullet(), start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
    builder.append(' ');
    builder.append(right);
    return builder;
  }

  /**
   * 带前缀行的版本串：{@code prefix + "\n" + left + " • " + right}。
   *
   * <p>为什么单独一个方法：关于页是「第一行产品名、第二行版本 • build」，前缀里的换行
   * 必须保留，而 {@code •} 的偏移只能作用在最后那一小段上。调用方自己拼字符串再套 span
   * 容易把 span 范围算错（实测：先拼后 span 会把前缀也套进去，整行都往上飘）。
   */
  public static CharSequence withPrefix(CharSequence prefix, CharSequence left, CharSequence right) {
    SpannableStringBuilder builder = new SpannableStringBuilder();
    builder.append(prefix).append('\n');
    builder.append(between(left, right));
    return builder;
  }

  /**
   * 纯文本形式，给「复制到剪贴板」「写日志」这类不需要视觉修正的地方用。
   *
   * <p>用普通空格而不是细空格：粘出去的内容要能在任意编辑器里正常对齐。
   */
  public static String plain(CharSequence left, CharSequence right) {
    return left.toString() + " " + GLYPH + " " + right.toString();
  }

  /** 把圆点的绘制基线上移固定比例，使其在高度方向居中。 */
  private static final class ShiftedBullet extends MetricAffectingSpan {

    /**
     * 本 span 对基线的偏移量（像素，负值=上移）。
     *
     * <p><b>这里必须是「赋值」，不能是「累加」</b> —— 2026-11-12 实测踩到：
     * 初版写的是 {@code paint.baselineShift += ...}，理由是"沿用调用方可能已设过的值"。
     * 但 {@code MetricAffectingSpan} 在排版流程里对**同一个 TextPaint 实例**
     * 会多次调用 {@code updateMeasureState} / {@code updateDrawState}
     * （测量一次、绘制一次，布局变化还会再来），
     * 于是每次调用都再叠一遍偏移 ⇒ 圆点被越推越高，最终被推出可视区域。
     * 真机表现就是"看起来像个小点/像没生效"。
     *
     * <p>正确做法：每次都按字号算出**目标绝对值**再赋值，重复调用结果不变（幂等）。
     * 代价是无法叠加调用方原有的 baselineShift —— 但本类只用于版本号分隔符，
     * 调用链上没有别人设置这个字段，可接受。
     */
    private static int shift(TextPaint paint) {
      return Math.round(paint.getTextSize() * BASELINE_SHIFT);
    }

    @Override
    public void updateDrawState(TextPaint paint) {
      paint.baselineShift = shift(paint);
    }

    @Override
    public void updateMeasureState(TextPaint paint) {
      // 测量阶段也要同步偏移，否则 span 前后的空格宽度会按未偏移的高度算，导致行高跳动。
      paint.baselineShift = shift(paint);
    }
  }
}
