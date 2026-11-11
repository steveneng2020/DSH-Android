package com.deepseekharness.app.ui;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;

/** 关于对话框：GitHub 仓库 / QQ 交流群入口（欢迎页 + 设置页 + 顶栏共用）。 */
public final class AboutDialog {

  /** 本 fork 的仓库地址（上游是 DSH-APP/DSHA，此处指自己的仓库）。 */
  public static final String GITHUB_URL =
      "https://github.com/" + com.deepseekharness.app.BuildConfig.FORK_REPOSITORY_SLUG;

  /** 本 fork 维护者（GitHub 用户名）；关于页的「交流与反馈」指向其主页。 */
  public static final String MAINTAINER = "steveneng2020";
  /** 本 fork 的联系邮箱（原 QQ 群已停用，改用邮箱）。 */
  public static final String CONTACT_EMAIL = "steveneng@163.com";

  private AboutDialog() {}

  public static AlertDialog show(Context ctx) {
    String version = "unknown";
    try {
      version = ctx.getPackageManager().getPackageInfo(ctx.getPackageName(), 0).versionName;
    } catch (Exception ignored) {
    }
    android.view.View content =
        android.view.LayoutInflater.from(ctx)
            .inflate(com.deepseekharness.app.R.layout.dialog_about, null);
    ((android.widget.TextView) content.findViewById(com.deepseekharness.app.R.id.about_version))
        .setText(com.deepseekharness.app.util.UiText.format("DSHA %s", version));
    android.widget.ImageView icon =
        content.findViewById(com.deepseekharness.app.R.id.about_app_icon);
    if (icon != null) {
      // 图标与桌面启动图标同源：在「关于」页直接点图标开切换器，不必再进设置。
      Runnable refresh =
          () -> icon.setImageResource(IconSwitcher.PREVIEWS[IconSwitcher.current(ctx)]);
      refresh.run();
      icon.setClickable(true);
      icon.setOnClickListener(
          v -> IconPickerDialog.show(ctx, refresh).show());
    }
    android.widget.TextView repository =
        content.findViewById(com.deepseekharness.app.R.id.about_repository);
    repository.setText(Uri.parse(GITHUB_URL).getPath().substring(1));
    android.widget.TextView community =
        content.findViewById(com.deepseekharness.app.R.id.about_community);
    community.setText(CONTACT_EMAIL);
    AlertDialog dialog = new DshaDialogBuilder(ctx).setView(content).create();
    content
        .findViewById(com.deepseekharness.app.R.id.about_close)
        .setOnClickListener(v -> dialog.dismiss());
    content
        .findViewById(com.deepseekharness.app.R.id.about_github)
        .setOnClickListener(v -> openBrowser(ctx, GITHUB_URL));
    content
        .findViewById(com.deepseekharness.app.R.id.about_qq)
        .setOnClickListener(v -> openEmail(ctx, CONTACT_EMAIL));
    // fork：关于对话框内联更新日记（与关于页一致，按版本分块）。
    android.view.View changelogBox = content.findViewById(com.deepseekharness.app.R.id.about_changelog_box);
    android.view.ViewGroup changelogList = content.findViewById(com.deepseekharness.app.R.id.about_changelog_list);
    if (changelogBox != null && changelogList != null) {
      ChangelogPanel.populateInto(ctx, changelogBox, changelogList, null);
    }
    dialog.show();
    return dialog;
  }

  public static void openBrowser(Context ctx, String url) {
    try {
      ctx.startActivity(
          new Intent(Intent.ACTION_VIEW, Uri.parse(url)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
    } catch (Exception e) {
      Toast.makeText(
              ctx,
              com.deepseekharness.app.util.UiText.format("打不开，请手动访问：%s", url),
              Toast.LENGTH_SHORT)
          .show();
    }
  }

  /** 联系邮箱入口：交给系统邮件客户端；没有可用客户端时退化为「请手动发信」提示。 */
  public static void openEmail(Context ctx, String address) {
    try {
      ctx.startActivity(
          new Intent(
                  Intent.ACTION_SENDTO,
                  Uri.parse("mailto:" + Uri.encode(address)))
              .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
    } catch (Exception e) {
      Toast.makeText(
              ctx,
              com.deepseekharness.app.util.UiText.format("没有可用的邮件应用，请手动发信至：%s", address),
              Toast.LENGTH_SHORT)
          .show();
    }
  }
}
