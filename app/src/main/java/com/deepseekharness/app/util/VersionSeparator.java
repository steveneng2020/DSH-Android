package com.deepseekharness.app.util;

import android.text.SpannableStringBuilder;
import android.text.Spanned;

/**
 * 版本号分隔符「・」的统一入口。
 *
 * <p><b>为什么用 U+30FB 全角中点，而不是 U+2022 实心圆点</b>：
 * {@code •}（U+2022 BULLET）的字形在设计上偏向基线下方 —— 它本来是给列表项目符号用的，
 * 放在「两侧都是正文数字」的行内位置看起来会「掉下去」。2026-11-12 用户在真机截图上
 * 指出 updated 页的版本行圆点偏低。
 *
 * <p>先后试过两种修法，都不合适：
 * <ol>
 *   <li>{@code TextPaint.baselineShift} 手动上移 —— 系数得靠系统字体猜（MiSans 实测需
 *       0.104em），而 {@code baselineShift} 是整数像素，12sp 下 33px × 0.10 = 3.3 被截成
 *       3px，误差可观；换字体就失准。
 *   <li>{@code ReplacementSpan.draw} 自算字形中心 —— 更脆，算错时连「是系数错了还是
 *       逻辑错了」都分不清（我在这条路上耗了三轮）。
 * </ol>
 *
 * <p>最终结论：**换字符比修字形更可靠**。{@code ・}（KATAKANA MIDDLE DOT）天生落在
 * x-height 中线附近，不需要任何排版干预；而且日语界面本来就用它，语种层面无冲突。
 * 代价是它比 {@code •} 宽（全角），但在「版本号 ・ build号」这种场景下反而更透气。
 *
 * <p>因此本类**不再做任何样式修正**，只提供统一的拼接入口与字符常量 ——
 * 保留它的理由是不让 7 处调用点各自硬编码字符串（那样迟早漂移，门禁 G13 也在查这个）。
 */
public final class VersionSeparator {

  /**
   * 分隔符本身：U+30FB 全角中点。
   *
   * <p><b>改这个字符之前先跑 {@code tools/check-version-separator.py}</b>，
   * 它会检查全仓是否统一，以及是否还有别处硬编码旧字符。
   */
  public static final String GLYPH = "・";

  /** 分隔符两侧是否加空格。全角字符本身占位较宽，加单空格在窄屏上会显得松散。 */
  private static final boolean PADDED = true;

  private VersionSeparator() {}

  /** 拼接「左 ・ 右」。两段内容保持调用方传入的原样。 */
  public static CharSequence between(CharSequence left, CharSequence right) {
    SpannableStringBuilder builder = new SpannableStringBuilder();
    builder.append(left);
    if (PADDED) builder.append(' ');
    builder.append(GLYPH);
    if (PADDED) builder.append(' ');
    builder.append(right);
    return builder;
  }

  /**
   * 带前缀行的版本串：{@code prefix + "\n" + left ・ right}。
   *
   * <p>单独一个方法是为了让「关于页」那种两行布局不必自己处理换行位置，
   * 避免把换行符拼进 {@link #between} 的入参里。
   */
  public static CharSequence withPrefix(
      CharSequence prefix, CharSequence left, CharSequence right) {
    SpannableStringBuilder builder = new SpannableStringBuilder();
    builder.append(prefix).append('\n');
    builder.append(between(left, right));
    return builder;
  }

  /**
   * 纯文本形式，给「复制到剪贴板」「写日志」这类地方用。
   *
   * <p>与 {@link #between} 保持同一分隔符，避免「界面看到的」和「复制出来的」不一致。
   */
  public static String plain(CharSequence left, CharSequence right) {
    return left.toString() + GLYPH + right.toString();
  }

  /** 兼容旧调用：某些地方需要 {@code Spanned} 类型。 */
  public static Spanned spanned(CharSequence left, CharSequence right) {
    return new SpannableStringBuilder(between(left, right));
  }
}
