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
    prefs(context).edit().putInt(KEY_INDEX, index).apply();
    return applied;
  }

  /** 提示已切换为哪套图标。 */
  public static void toastApplied(Context context, int index) {
    String label = context.getString(LABELS[index]);
    Toast.makeText(
            context, context.getString(R.string.icon_style_applied, label), Toast.LENGTH_SHORT)
        .show();
  }

  private static SharedPreferences prefs(Context context) {
    return context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
  }
}
