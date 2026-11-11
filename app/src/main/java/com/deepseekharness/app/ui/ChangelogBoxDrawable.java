package com.deepseekharness.app.ui;

import android.content.Context;
import com.deepseekharness.app.R;

/** 更新日志卡片底色；尺寸与圆角在此按屏幕密度换算，颜色跟随主题。 */
final class ChangelogBoxDrawable {
  private static final float DASH_DP = 4f;
  private static final float GAP_DP = 4f;
  private static final float RADIUS_DP = 18f;
  private static final float STROKE_DP = 1f;

  private ChangelogBoxDrawable() {}

  static DashedBorderDrawable create(Context context) {
    float density = context.getResources().getDisplayMetrics().density;
    float dash = density * DASH_DP;
    return new DashedBorderDrawable(
        context.getColor(R.color.card),
        context.getColor(R.color.line),
        density * RADIUS_DP,
        density * STROKE_DP,
        dash,
        density * GAP_DP);
  }
}
