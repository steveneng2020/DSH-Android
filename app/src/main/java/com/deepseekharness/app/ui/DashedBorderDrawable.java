package com.deepseekharness.app.ui;

import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.drawable.Drawable;

/**
 * 圆角描边底：同一路径先填后描，两笔各自成画。
 *
 * <p>刻意不用 {@link android.graphics.PathEffect} 虚线：早期虚线样式在部分设备上触发 4096
 * 纹理上限，整块背景变黑。描边宽度由外部按 dp 换算后传入。
 */
final class DashedBorderDrawable extends Drawable {
  private final Paint fillPaint;
  private final Path path;
  private final float radius;
  private final RectF rect;
  private final Paint strokePaint;
  private final float strokeWidth;

  /**
   * @param fillColor 填充色
   * @param strokeColor 描边色
   * @param radius 圆角半径（px）
   * @param strokeWidth 描边宽度（px）
   * @param dash 保留参数，当前实现不绘制虚线间隔
   * @param gap 保留参数，当前实现不绘制虚线间隔
   */
  DashedBorderDrawable(
      int fillColor, int strokeColor, float radius, float strokeWidth, float dash, float gap) {
    fillPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    strokePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    path = new Path();
    rect = new RectF();
    fillPaint.setStyle(Paint.Style.FILL);
    fillPaint.setColor(fillColor);
    strokePaint.setStyle(Paint.Style.STROKE);
    strokePaint.setColor(strokeColor);
    strokePaint.setStrokeWidth(strokeWidth);
    this.radius = radius;
    this.strokeWidth = strokeWidth;
  }

  @Override
  public void draw(Canvas canvas) {
    Rect bounds = getBounds();
    if (bounds.isEmpty()) return;
    // 描边以路径中心线为轴，向内收半笔宽才不会在边界被裁掉。
    float inset = strokeWidth / 2f;
    rect.set(bounds.left + inset, bounds.top + inset, bounds.right - inset, bounds.bottom - inset);
    path.reset();
    path.addRoundRect(rect, radius, radius, Path.Direction.CW);
    canvas.drawPath(path, fillPaint);
    canvas.drawPath(path, strokePaint);
  }

  @Override
  public int getOpacity() {
    return android.graphics.PixelFormat.TRANSLUCENT;
  }

  @Override
  public void setAlpha(int alpha) {
    fillPaint.setAlpha(alpha);
    strokePaint.setAlpha(alpha);
  }

  @Override
  public void setColorFilter(ColorFilter filter) {
    fillPaint.setColorFilter(filter);
    strokePaint.setColorFilter(filter);
  }
}
