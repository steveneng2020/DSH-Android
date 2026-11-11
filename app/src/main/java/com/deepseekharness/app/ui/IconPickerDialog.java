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
    // fork：图标出处与寓意（用户要求）。放在副标题下方，一次说清「这是什么、为什么是它」，
    // 免得每次看到弹窗都得回去查 README 的「图标寓意」节。
    TextView lore = new TextView(context);
    lore.setText(R.string.icon_style_lore);
    lore.setTextSize(11f);
    lore.setTextColor(context.getColor(R.color.text_secondary));
    lore.setLineSpacing(0, 1.15f);
    LinearLayout.LayoutParams loreParams = new LinearLayout.LayoutParams(-1, -2);
    loreParams.topMargin = dp(context, 8);
    content.addView(lore, loreParams);
    LinearLayout list = new LinearLayout(context);
    list.setOrientation(LinearLayout.VERTICAL);
    // 六行 × 64dp + 图标寓意 + 内联提示在窄屏上会超出对话框高度，LinearLayout 会把最后加进去的
    // 子视图压成一条线（实测：提示条被压扁成细缝）。所以列表包进 ScrollView，高度取屏高的 42%：
    // 高度不足时列表自己滚动，上方的图标寓意与下方的内联提示都保持 wrap_content 的完整高度。
    //
    // 不能用 0dp + weight=1：content 本身是 wrap_content，父高度不确定时 weight 分到的剩余空间
    // 为 0，列表会被压成看不见（实测丢过一次）。必须是明确的像素高度。
    android.widget.ScrollView listScroll = new android.widget.ScrollView(context);
    listScroll.setFillViewport(false);
    listScroll.addView(list, new android.widget.FrameLayout.LayoutParams(-1, -2));
    int screenH = context.getResources().getDisplayMetrics().heightPixels;
    int listMax = Math.round(screenH * 0.42f);
    LinearLayout.LayoutParams listScrollParams = new LinearLayout.LayoutParams(-1, listMax);
    listScrollParams.topMargin = dp(context, 12);
    content.addView(listScroll, listScrollParams);
    // 切换结果就地显示在弹窗内，不再用 Toast —— Toast 浮在屏幕底部，
    // 会盖住对话框下方的「交流与反馈」等外部内容，且位置不受本弹窗控制。
    // 这里做成一条与列表同宽的内联提示：图标跟随所选配色 + 文案。
    LinearLayout appliedBar = new LinearLayout(context);
    appliedBar.setOrientation(LinearLayout.HORIZONTAL);
    appliedBar.setGravity(Gravity.CENTER_VERTICAL);
    appliedBar.setVisibility(View.GONE);
    appliedBar.setPadding(dp(context, 12), dp(context, 10), dp(context, 12), dp(context, 10));
    appliedBar.setMinimumHeight(dp(context, 44));
    GradientDrawable barBg = new GradientDrawable();
    barBg.setCornerRadius(dp(context, 12));
    barBg.setStroke(dp(context, 1), context.getColor(R.color.line));
    appliedBar.setBackground(barBg);
    ImageView appliedIcon = new ImageView(context);
    appliedIcon.setId(R.id.icon_applied_icon);
    int appliedIconSize = dp(context, 24);
    appliedBar.addView(appliedIcon, new LinearLayout.LayoutParams(appliedIconSize, appliedIconSize));
    TextView appliedText = new TextView(context);
    appliedText.setId(R.id.icon_applied_text);
    appliedText.setTextSize(13f);
    appliedText.setTextColor(context.getColor(R.color.text_secondary));
    LinearLayout.LayoutParams appliedTextParams = new LinearLayout.LayoutParams(0, -2, 1f);
    appliedTextParams.leftMargin = dp(context, 8);
    appliedBar.addView(appliedText, appliedTextParams);
    LinearLayout.LayoutParams appliedBarParams = new LinearLayout.LayoutParams(-1, -2);
    appliedBarParams.topMargin = dp(context, 14);
    content.addView(appliedBar, appliedBarParams);
    // 历史残留：原实现预留了一个弹窗持有位，实际从未使用；保留以与 dex 字节码保持一致。
    AlertDialog[] dialogHolder = new AlertDialog[1];
    // 内联提示的自动隐藏：2.6s 后收起，与 Toast.LENGTH_SHORT 观感接近。
    Runnable hideApplied = () -> appliedBar.setVisibility(View.GONE);
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
            // 内联提示：图标用该配色的预览图，文案与 Toast 时期保持一致。
            appliedIcon.setImageResource(IconSwitcher.PREVIEWS[index]);
            appliedText.setText(
                context.getString(
                    R.string.icon_style_applied, context.getString(IconSwitcher.LABELS[index])));
            appliedBar.setVisibility(View.VISIBLE);
            appliedBar.removeCallbacks(hideApplied);
            appliedBar.postDelayed(hideApplied, 2600);
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
