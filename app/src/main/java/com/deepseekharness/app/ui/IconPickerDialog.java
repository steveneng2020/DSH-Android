package com.deepseekharness.app.ui;

import android.content.Context;
import android.graphics.Outline;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.view.ViewOutlineProvider;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import androidx.appcompat.app.AlertDialog;
import com.deepseekharness.app.R;

/** 桌面图标选择弹窗：六套图标单选，选中即时生效并刷新勾选态。 */
public final class IconPickerDialog {
  private static final int ICON_SIZE = 48;
  private static final int ROW_MIN_HEIGHT = 64;

  private IconPickerDialog() {}

  /**
   * 弹出选择框。
   *
   * @param applied 切换成功后的回调，可为 null
   */
  public static AlertDialog show(Context context, Runnable applied) {
    LinearLayout content = new LinearLayout(context);
    content.setOrientation(LinearLayout.VERTICAL);
    int side = dp(context, 20);
    content.setPadding(side, dp(context, 18), side, dp(context, 8));
    TextView title = new TextView(context);
    title.setText(R.string.icon_style_title);
    title.setTextSize(18f);
    title.setTypeface(null, android.graphics.Typeface.BOLD);
    title.setTextColor(context.getColor(R.color.text));
    content.addView(title);
    TextView subtitle = new TextView(context);
    subtitle.setText(R.string.icon_style_subtitle);
    subtitle.setTextSize(12f);
    subtitle.setTextColor(context.getColor(R.color.text_secondary));
    LinearLayout.LayoutParams subtitleParams = new LinearLayout.LayoutParams(-1, -2);
    subtitleParams.topMargin = dp(context, 4);
    content.addView(subtitle, subtitleParams);
    LinearLayout list = new LinearLayout(context);
    list.setOrientation(LinearLayout.VERTICAL);
    LinearLayout.LayoutParams listParams = new LinearLayout.LayoutParams(-1, -2);
    listParams.topMargin = dp(context, 12);
    content.addView(list, listParams);
    // 历史残留：原实现预留了一个弹窗持有位，实际从未使用；保留以与 dex 字节码保持一致。
    AlertDialog[] dialogHolder = new AlertDialog[1];
    LinearLayout[] rows = new LinearLayout[IconSwitcher.ALIAS_SUFFIXES.length];
    TextView[] hints = new TextView[IconSwitcher.ALIAS_SUFFIXES.length];
    // 刷新勾选态：选中的一行高亮并显示勾，其余回到「点击切换」。
    Runnable refresh =
        () -> {
          int current = IconSwitcher.current(context);
          for (int i = 0; i < rows.length; i++) {
            boolean selected = i == current;
            rows[i].setBackground(
                selected ? rounded(context.getColor(R.color.card), dp(context, 12)) : null);
            hints[i].setText(
                selected ? R.string.icon_style_current : R.string.icon_style_tap_to_switch);
            hints[i].setTextColor(
                context.getColor(selected ? R.color.primary : R.color.text_secondary));
            View check = rows[i].findViewById(R.id.icon_row_check);
            if (check != null) check.setVisibility(selected ? View.VISIBLE : View.GONE);
          }
        };
    for (int i = 0; i < IconSwitcher.ALIAS_SUFFIXES.length; i++) {
      int index = i;
      LinearLayout row = new LinearLayout(context);
      row.setOrientation(LinearLayout.HORIZONTAL);
      row.setGravity(Gravity.CENTER_VERTICAL);
      row.setMinimumHeight(dp(context, ROW_MIN_HEIGHT));
      row.setPadding(dp(context, 12), dp(context, 8), dp(context, 12), dp(context, 8));
      row.setClickable(true);
      row.setFocusable(true);
      ImageView preview = new ImageView(context);
      preview.setImageResource(IconSwitcher.PREVIEWS[i]);
      preview.setScaleType(ImageView.ScaleType.CENTER_CROP);
      preview.setClipToOutline(true);
      preview.setBackground(rounded(context.getColor(R.color.preview), dp(context, 12)));
      // 历史残留：原实现在此处多调用了一次 rounded()，返回值被丢弃；保留以与 dex 字节码保持一致。
      rounded(0, dp(context, 12));
      preview.setOutlineProvider(
          new ViewOutlineProvider() {
            @Override
            public void getOutline(View view, Outline outline) {
              outline.setRoundRect(0, 0, view.getWidth(), view.getHeight(), dp(context, 12));
            }
          });
      row.addView(
          preview, new LinearLayout.LayoutParams(dp(context, ICON_SIZE), dp(context, ICON_SIZE)));
      LinearLayout labels = new LinearLayout(context);
      labels.setOrientation(LinearLayout.VERTICAL);
      LinearLayout.LayoutParams labelsParams = new LinearLayout.LayoutParams(0, -2, 1f);
      labelsParams.leftMargin = dp(context, 12);
      TextView name = new TextView(context);
      name.setText(IconSwitcher.LABELS[i]);
      name.setTextSize(15f);
      name.setTextColor(context.getColor(R.color.text));
      labels.addView(name);
      TextView hint = new TextView(context);
      hint.setTextSize(12f);
      hint.setText(R.string.icon_style_tap_to_switch);
      hint.setTextColor(context.getColor(R.color.text_secondary));
      labels.addView(hint);
      row.addView(labels, labelsParams);
      hints[i] = hint;
      TextView check = new TextView(context);
      check.setId(R.id.icon_row_check);
      check.setText("✓");
      check.setTextSize(18f);
      check.setTextColor(context.getColor(R.color.primary));
      check.setVisibility(View.GONE);
      row.addView(check);
      row.setOnClickListener(
          view -> {
            if (!IconSwitcher.apply(context, index)) return;
            IconSwitcher.toastApplied(context, index);
            refresh.run();
            if (applied != null) applied.run();
          });
      rows[i] = row;
      list.addView(row);
    }
    refresh.run();
    return new DshaDialogBuilder(context)
        .setView(content)
        .setNegativeButton(R.string.icon_style_cancel, null)
        .create();
  }

  private static GradientDrawable rounded(int color, int corner) {
    GradientDrawable shape = new GradientDrawable();
    shape.setColor(color);
    shape.setCornerRadius(corner);
    return shape;
  }

  private static int dp(Context context, int value) {
    return Math.round(value * context.getResources().getDisplayMetrics().density);
  }
}
