package com.deepseekharness.app.ui;

import android.content.ComponentName;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.widget.Toast;
import com.deepseekharness.app.R;

/**
 * 切换桌面图标：六个别名 Activity 同时只有一个处于启用状态。
 *
 * <p>别名写在宿主 manifest 里，命名空间固定为构建 namespace（不是 applicationId）。
 * 当前选择同时落到组件启用状态与 {@code dsha_icon_style} 偏好，卸载重装后可从偏好恢复。
 */
public final class IconSwitcher {
  public static final String ALIAS_NAMESPACE = "com.deepseekharness.app";
  public static final String[] ALIAS_SUFFIXES = {
    "LauncherDefault",
    "LauncherMoyu",
    "LauncherTianqing",
    "LauncherZheshi",
    "LauncherBiyu",
    "LauncherZishou"
  };
  public static final int COUNT = ALIAS_SUFFIXES.length;
  private static final String KEY_INDEX = "index";
  /** 用户是否显式选过图标；用于区分「从未选过」与「选过但被覆盖安装重置」。 */
  private static final String KEY_EXPLICIT = "explicit";
  private static final String PREFS = "dsha_icon_style";
  public static final int[] LABELS = {
    R.string.icon_style_default,
    R.string.icon_style_moyu,
    R.string.icon_style_tianqing,
    R.string.icon_style_zheshi,
    R.string.icon_style_biyu,
    R.string.icon_style_zishou
  };
  public static final int[] PREVIEWS = {
    R.mipmap.ic_launcher_default,
    R.mipmap.ic_launcher_moyu,
    R.mipmap.ic_launcher_tianqing,
    R.mipmap.ic_launcher_zheshi,
    R.mipmap.ic_launcher_biyu,
    R.mipmap.ic_launcher_zishou
  };

  private IconSwitcher() {}

  static String aliasName(int index) {
    return ALIAS_NAMESPACE + "." + ALIAS_SUFFIXES[index];
  }

  /** 全部别名的完整组件名，顺序与 {@link #LABELS} 一致。 */
  public static String[] aliases() {
    String[] names = new String[ALIAS_SUFFIXES.length];
    for (int i = 0; i < names.length; i++) names[i] = aliasName(i);
    return names;
  }

  /**
   * 读当前图标序号。
   *
   * <p>先看组件启用状态（真实生效值），读不到再退回偏好里的记录；两者都无效时归零。
   * 部分 ROM 会对未声明的别名抛异常，逐个跳过即可。
   */
  public static int current(Context context) {
    PackageManager manager = context.getPackageManager();
    for (int i = 0; i < ALIAS_SUFFIXES.length; i++) {
      try {
        ComponentName component = new ComponentName(context, aliasName(i));
        if (manager.getComponentEnabledSetting(component)
            == PackageManager.COMPONENT_ENABLED_STATE_ENABLED) return i;
      } catch (RuntimeException ignored) {
        // 别名缺失或系统拒绝查询时继续看下一个。
      }
    }
    int saved = prefs(context).getInt(KEY_INDEX, 0);
    return saved < 0 || saved >= ALIAS_SUFFIXES.length ? 0 : saved;
  }

  /** 启用指定别名并停用其余别名；任一组件写入失败时返回 false，但偏好仍会更新。 */
  public static boolean apply(Context context, int index) {
    if (index < 0 || index >= ALIAS_SUFFIXES.length) return false;
    PackageManager manager = context.getPackageManager();
    boolean applied = true;
    for (int i = 0; i < ALIAS_SUFFIXES.length; i++) {
      int state =
          i == index
              ? PackageManager.COMPONENT_ENABLED_STATE_ENABLED
              : PackageManager.COMPONENT_ENABLED_STATE_DISABLED;
      try {
        manager.setComponentEnabledSetting(
            new ComponentName(context, aliasName(i)), state, PackageManager.DONT_KILL_APP);
      } catch (RuntimeException ignored) {
        applied = false;
      }
    }
    // 同时记下「用户显式选过」，供启动时判断是否需要把组件状态拉回偏好值。
    // 没有这个标记就无法区分「从未选过」和「选过但被覆盖安装重置」。
    prefs(context).edit().putInt(KEY_INDEX, index).putBoolean(KEY_EXPLICIT, true).apply();
    return applied;
  }

  /**
   * 启动时把组件启用状态对齐到偏好。
   *
   * <p>为什么需要：覆盖安装会让系统把 6 个 activity-alias 重置成 manifest 默认值
   * （只有 LauncherDefault 为 true），而 SharedPreferences 里的选择仍然保留。
   * 于是用户上次选的配色看起来"丢了"——实际是组件状态被系统重置，
   * 而 current() 优先读组件状态，读到的就是被重置后的 0。
   *
   * <p>只在「用户显式选过」时恢复；首次安装不动，避免覆盖 manifest 的默认值。
   */
  public static void restoreIfNeeded(Context context) {
    SharedPreferences p = prefs(context);
    if (!p.getBoolean(KEY_EXPLICIT, false)) return;
    int saved = p.getInt(KEY_INDEX, 0);
    if (saved <= 0 || saved >= ALIAS_SUFFIXES.length) return;
    // 已经一致就不写，避免每次启动都触发组件状态变更（可能引起桌面重绘）。
    if (current(context) == saved) return;
    apply(context, saved);
  }

  /**
   * 提示已切换为哪套图标。
   *
   * <p>用自定义视图而不是 {@code Toast.makeText}：后者在 Android 11+ 会在左侧套上
   * **应用级**图标（manifest 的 {@code android:icon}，这里固定为 ic_launcher_default）。
   * 于是切到「赭石」时，提示里配的还是默认黄色图标 —— 与真正生效的配色不一致。
   * 自定义视图把图标换成 PREVIEWS[index]，与用户刚选的那套对齐。
   */
  public static void toastApplied(Context context, int index) {
    String label = context.getString(LABELS[index]);
    String text = context.getString(R.string.icon_style_applied, label);
    Toast toast;
    try {
      android.widget.LinearLayout row = new android.widget.LinearLayout(context);
      row.setOrientation(android.widget.LinearLayout.HORIZONTAL);
      row.setGravity(android.view.Gravity.CENTER_VERTICAL);
      int pad = Math.round(12 * context.getResources().getDisplayMetrics().density);
      row.setPadding(pad, pad, pad, pad);

      android.widget.ImageView icon = new android.widget.ImageView(context);
      icon.setImageResource(PREVIEWS[index]);
      int size = Math.round(28 * context.getResources().getDisplayMetrics().density);
      row.addView(icon, new android.widget.LinearLayout.LayoutParams(size, size));

      android.widget.TextView labelView = new android.widget.TextView(context);
      labelView.setText(text);
      labelView.setTextSize(14f);
      int gap = Math.round(10 * context.getResources().getDisplayMetrics().density);
      android.widget.LinearLayout.LayoutParams lp =
          new android.widget.LinearLayout.LayoutParams(-2, -2);
      lp.leftMargin = gap;
      row.addView(labelView, lp);

      toast = new Toast(context);
      toast.setDuration(Toast.LENGTH_SHORT);
      toast.setView(row);
    } catch (RuntimeException customUnavailable) {
      // 自定义视图在任何 ROM 上都不该是致命路径：失败就退回纯文字。
      toast = Toast.makeText(context, text, Toast.LENGTH_SHORT);
    }
    toast.show();
  }

  private static SharedPreferences prefs(Context context) {
    return context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
  }
}
