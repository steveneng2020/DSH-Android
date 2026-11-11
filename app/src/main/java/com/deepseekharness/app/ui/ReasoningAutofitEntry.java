package com.deepseekharness.app.ui;

import android.content.Context;
import android.graphics.Typeface;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import com.deepseekharness.app.R;
import com.deepseekharness.app.core.HarnessController;
import com.deepseekharness.app.core.ReasoningAutofit;
import com.deepseekharness.app.util.SensitiveData;
import com.deepseekharness.app.util.UiText;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

/** 设置页的「自动适配推理档位」入口；点击后一次性跑完，结果写回副标题并弹提示。 */
final class ReasoningAutofitEntry {
  private ReasoningAutofitEntry() {}

  /** 往设置页的体验卡片插入一行入口；卡片不在时什么都不做。 */
  static void install(SettingsFragment fragment, View root) {
    // 上游 v0.2.2 把设置页「体验」区重构为 settings_group_experience；
    // fork 早期用的 settings_experience_card 已不存在。
    LinearLayout card = root.findViewById(R.id.settings_group_experience);
    if (card == null) return;
    Context context = fragment.requireContext();
    LinearLayout row = new LinearLayout(context);
    row.setOrientation(LinearLayout.HORIZONTAL);
    row.setGravity(Gravity.CENTER_VERTICAL);
    row.setMinimumHeight(dp(context, 64));
    row.setPadding(dp(context, 13), dp(context, 11), dp(context, 13), dp(context, 11));
    row.setBackgroundResource(R.drawable.bg_ui2_row);
    row.setClickable(true);
    row.setFocusable(true);
    ImageView icon = new ImageView(context);
    icon.setImageResource(R.drawable.ic_settings);
    icon.setBackgroundResource(R.drawable.bg_logo);
    icon.setPadding(dp(context, 8), dp(context, 8), dp(context, 8), dp(context, 8));
    icon.setContentDescription(null);
    row.addView(icon, new LinearLayout.LayoutParams(dp(context, 32), dp(context, 32)));
    LinearLayout labels = new LinearLayout(context);
    labels.setOrientation(LinearLayout.VERTICAL);
    LinearLayout.LayoutParams labelsParams =
        new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f);
    labelsParams.leftMargin = dp(context, 12);
    labelsParams.rightMargin = dp(context, 8);
    labels.setLayoutParams(labelsParams);
    TextView title = new TextView(context);
    title.setText(UiText.text("自动适配推理档位"));
    title.setTextSize(13f);
    title.setTextColor(context.getColor(R.color.text));
    title.setIncludeFontPadding(false);
    title.setTypeface(title.getTypeface(), Typeface.BOLD);
    labels.addView(title);
    TextView status = new TextView(context);
    status.setText(UiText.text("为缺少推理等级的模型自动补全档位（只增不改，写入前自动备份）"));
    status.setTextSize(11f);
    status.setTextColor(context.getColor(R.color.text_muted));
    status.setIncludeFontPadding(false);
    status.setPadding(0, dp(context, 4), 0, 0);
    labels.addView(status);
    row.addView(labels);
    TextView arrow = new TextView(context);
    arrow.setText(UiText.text("›"));
    arrow.setTextSize(18f);
    arrow.setTextColor(context.getColor(R.color.text_muted));
    row.addView(arrow);
    card.addView(row, new LinearLayout.LayoutParams(-1, LinearLayout.LayoutParams.WRAP_CONTENT));
    Handler main = new Handler(Looper.getMainLooper());
    AtomicBoolean busy = new AtomicBoolean(false);
    row.setOnClickListener(
        view -> {
          // 连点保护：同一时间只允许一个任务，跑完前禁用整行。
          if (busy.getAndSet(true)) return;
          if (ReasoningAutofit.isRunning()) {
            busy.set(false);
            return;
          }
          row.setEnabled(false);
          status.setText(
              UiText.text("正在检查 %s/%s 个模型…").replaceFirst("%s", "0").replaceFirst("%s", "?"));
          ExecutorService executor =
              Executors.newSingleThreadExecutor(
                  runnable -> {
                    Thread thread = new Thread(runnable, "reasoning-autofit");
                    thread.setDaemon(true);
                    return thread;
                  });
          executor.execute(
              () -> {
                String message;
                try {
                  ReasoningAutofit.Result result =
                      new ReasoningAutofit(HarnessController.get(context))
                          .run(
                              ReasoningAutofit.defaultProfile(context),
                              true,
                              (stage, done, total, note) -> {
                                if (!"probing".equals(stage) || total <= 0) return;
                                String progress =
                                    UiText.text("正在检查 %s/%s 个模型…")
                                        .replaceFirst("%s", String.valueOf(done))
                                        .replaceFirst("%s", String.valueOf(total));
                                main.post(() -> status.setText(progress));
                              });
                  if (result.written == 0 && !result.changed) {
                    message = UiText.text("没有需要补全的模型");
                  } else {
                    message =
                        UiText.format(
                            "自动适配完成：写入 %s 个，跳过 %s 个，探测 %s 个",
                            result.written, result.skipped, result.probed);
                    if (!result.backup.isEmpty()) {
                      message += "\n" + UiText.format("已备份原配置：%s", result.backup);
                    }
                  }
                } catch (Exception error) {
                  message =
                      UiText.text("自动适配失败：%s")
                          .replace("%s", SensitiveData.redact(String.valueOf(error.getMessage())));
                }
                String text = message;
                main.post(
                    () -> {
                      status.setText(text);
                      row.setEnabled(true);
                      busy.set(false);
                      Toast.makeText(context, text, Toast.LENGTH_LONG).show();
                    });
                executor.shutdown();
              });
        });
  }

  private static int dp(Context context, int value) {
    return Math.round(value * context.getResources().getDisplayMetrics().density);
  }
}
