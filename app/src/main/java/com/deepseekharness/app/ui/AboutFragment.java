package com.deepseekharness.app.ui;

import android.os.Bundle;
import android.view.*;
import android.widget.*;
import android.content.Intent;
import androidx.fragment.app.Fragment;
import com.deepseekharness.app.*;
import com.deepseekharness.app.util.UiText;

public final class AboutFragment extends Fragment {
  /** 「检查上游更新」的在途请求：离开页面时必须取消，否则回调打到已销毁的视图上。 */
  private UpstreamCompareUi.Session upstreamSession;

  @Override
  public void onDestroyView() {
    UpstreamCompareUi.Session session = upstreamSession;
    upstreamSession = null;
    if (session != null) session.cancel();
    super.onDestroyView();
  }

  @Override
  public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle saved) {
    CardPage ui = new CardPage(requireContext(), UiText.choose("关于 DSHA", "About DSHA"), "");
    android.widget.FrameLayout emblem = new android.widget.FrameLayout(requireContext());
    android.widget.ImageView mark = new android.widget.ImageView(requireContext());
    // fork：图标随当前配色变化，点击可切换（上游是固定装饰图）。
    // 图标要「充满」画布：PREVIEWS 里的图自带圆角底，再套 bg_ui2_mark + padding
    // 会把它压小一圈。故改为 CENTER_CROP + 零内边距 + 圆角裁剪，尺寸 80dp。
    mark.setScaleType(android.widget.ImageView.ScaleType.CENTER_CROP);
    mark.setClipToOutline(true);
    mark.setPadding(0, 0, 0, 0);
    mark.setContentDescription(UiText.text("应用图标：点击切换配色"));
    // refreshIcon 由切换器回调，切完立刻刷新本页预览，不必退出重进。
    Runnable refreshIcon =
        () -> mark.setImageResource(IconSwitcher.PREVIEWS[IconSwitcher.current(requireContext())]);
    refreshIcon.run();
    mark.setClickable(true);
    mark.setFocusable(true);
    mark.setOnClickListener(v -> IconPickerDialog.show(requireContext(), refreshIcon).show());
    emblem.addView(
        mark, new android.widget.FrameLayout.LayoutParams(ui.dp(80), ui.dp(80), Gravity.CENTER));
    ui.content.addView(emblem, new LinearLayout.LayoutParams(-1, ui.dp(100)));
    TextView brand = ui.text("DSHA", 30, R.color.text);
    brand.setTypeface(null, android.graphics.Typeface.BOLD);
    brand.setGravity(Gravity.CENTER);
    brand.setPadding(0, ui.dp(16), 0, ui.dp(10));
    ui.content.addView(brand);
    TextView version =
        ui.text(
            "DeepSeek Harness for Android\n"
                + BuildConfig.VERSION_NAME
                + " • build"
                + BuildConfig.VERSION_CODE,
            12,
            R.color.text_secondary);
    version.setGravity(Gravity.CENTER);
    version.setPadding(0, 0, 0, ui.dp(24));
    ui.content.addView(version);
    LinearLayout metadata = ui.card();
    ui.kv(metadata, UiText.choose("包名", "Package"), BuildConfig.APPLICATION_ID);
    ui.kv(
        metadata,
        UiText.choose("当前版本", "Edition"),
        false
            ? UiText.choose("兼容版 · Android 6+", "Compatibility · Android 6+")
            : UiText.choose("标准版 · Android 11+", "Standard · Android 11+"));
    ui.kv(metadata, "DSH", com.deepseekharness.app.util.Constants.DSH_VERSION);
    ui.kv(metadata, UiText.choose("架构", "Architecture"), "arm64-v8a");
    ui.kv(metadata, UiText.choose("开源许可", "License"), "MIT");
    ui.label(UiText.choose("了解更多", "Learn more"));
    LinearLayout links = ui.card();
    ui.entry(
        links,
        UiText.choose("项目仓库", "Repository"),
        android.net.Uri.parse(AboutDialog.GITHUB_URL).getHost()
            + android.net.Uri.parse(AboutDialog.GITHUB_URL).getPath(),
        R.drawable.ic_ui_link,
        () -> AboutDialog.openBrowser(requireContext(), AboutDialog.GITHUB_URL));
    ui.entry(
        links,
        UiText.choose("交流与反馈", "Community and feedback"),
        // fork：上游指向 QQ 群，本项目不维护社群，改为维护者主页 + 问题反馈。
        UiText.format("@%s · 问题反馈", AboutDialog.MAINTAINER),
        R.drawable.ic_ui_chat,
        () ->
            new DshaDialogBuilder(requireContext())
                .setTitle(UiText.choose("交流与反馈", "Community and feedback"))
                .setItems(
                    new String[] {
                      UiText.choose("打开维护者主页", "Open maintainer profile"),
                      UiText.choose("打开问题反馈", "Open issue tracker")
                    },
                    (d, i) -> {
                      if (i == 0)
                        AboutDialog.openBrowser(
                            requireContext(), "https://github.com/" + AboutDialog.MAINTAINER);
                      else
                        AboutDialog.openBrowser(
                            requireContext(), AboutDialog.GITHUB_URL + "/issues");
                    })
                .show());
    ui.entry(
        links,
        UiText.choose("开源许可", "Open-source licenses"),
        UiText.choose("DSHA 与随包第三方组件", "DSHA and bundled components"),
        R.drawable.ic_recovery_document,
        this::showLicenses);
    // 更新日记 + 上游对比：与「关于」对话框同一套组件，直接内联进卡片页。
    try {
      LinearLayout changelogBox = new LinearLayout(requireContext());
      changelogBox.setOrientation(LinearLayout.VERTICAL);
      changelogBox.setPadding(ui.dp(14), ui.dp(14), ui.dp(14), ui.dp(14));
      changelogBox.setBackground(ChangelogBoxDrawable.create(requireContext()));
      LinearLayout.LayoutParams boxParams = new LinearLayout.LayoutParams(-1, -2);
      boxParams.topMargin = ui.dp(20);
      changelogBox.setLayoutParams(boxParams);
      TextView changelogTitle =
          ui.text(getString(R.string.about_changelog_title), 13, R.color.text);
      changelogTitle.setTypeface(null, android.graphics.Typeface.BOLD);
      changelogBox.addView(changelogTitle);
      LinearLayout changelogList = new LinearLayout(requireContext());
      changelogList.setOrientation(LinearLayout.VERTICAL);
      LinearLayout.LayoutParams listParams = new LinearLayout.LayoutParams(-1, -2);
      listParams.topMargin = ui.dp(6);
      changelogBox.addView(changelogList, listParams);
      ui.content.addView(changelogBox);
      ChangelogPanel.populateInto(requireContext(), changelogBox, changelogList, null);
      LinearLayout upstreamBlock = new LinearLayout(requireContext());
      upstreamBlock.setOrientation(LinearLayout.VERTICAL);
      LinearLayout.LayoutParams upstreamParams = new LinearLayout.LayoutParams(-1, -2);
      upstreamParams.topMargin = ui.dp(10);
      changelogBox.addView(upstreamBlock, upstreamParams);
      TextView upstreamToggle =
          ui.text(getString(R.string.about_upstream_expand), 12, R.color.text_secondary);
      upstreamToggle.setId(R.id.about_upstream_toggle);
      upstreamToggle.setPadding(0, ui.dp(6), 0, ui.dp(6));
      upstreamBlock.addView(upstreamToggle);
      LinearLayout upstreamBody = new LinearLayout(requireContext());
      upstreamBody.setOrientation(LinearLayout.VERTICAL);
      upstreamBody.setId(R.id.about_upstream_body);
      upstreamBody.setVisibility(View.GONE);
      upstreamBlock.addView(upstreamBody);
      TextView upstreamBase = ui.text("", 11, R.color.text_secondary);
      upstreamBase.setId(R.id.about_upstream_base);
      TextView upstreamLatest = ui.text("", 11, R.color.text_secondary);
      upstreamLatest.setId(R.id.about_upstream_latest);
      TextView upstreamVerdict = ui.text("", 11, R.color.text_secondary);
      upstreamVerdict.setId(R.id.about_upstream_verdict);
      upstreamBody.addView(upstreamBase);
      upstreamBody.addView(upstreamLatest);
      upstreamBody.addView(upstreamVerdict);
      ui.button(upstreamBody, getString(R.string.about_upstream_check), false, () -> {})
          .setId(R.id.about_upstream_check);
      upstreamSession =
          UpstreamCompareUi.wire(
              requireContext(),
              upstreamBlock,
              upstreamToggle.getId(),
              upstreamBody.getId(),
              upstreamBase.getId(),
              upstreamLatest.getId(),
              upstreamVerdict.getId(),
              R.id.about_upstream_check,
              R.id.about_upstream_url);
    } catch (Throwable ignored) {
      TextView fallback = new TextView(requireContext());
      fallback.setText(R.string.about_changelog_unavailable);
      fallback.setTextColor(requireContext().getColor(R.color.text_secondary));
      fallback.setTextSize(12f);
      ui.content.addView(fallback);
    }
    ui.footer.setVisibility(View.GONE);
    return ui.root;
  }

  private void showLicenses() {
    try {
      String[] listed = requireContext().getAssets().list("licenses");
      if (listed == null || listed.length > 128) throw new java.io.IOException("LICENSE_INDEX");
      String[] names =
          java.util.Arrays.stream(listed)
              .filter(name -> name.matches("[A-Za-z0-9_.-]+\\.txt"))
              .sorted()
              .toArray(String[]::new);
      new DshaDialogBuilder(requireContext())
          .setTitle(UiText.choose("随包许可全文", "Bundled license texts"))
          .setItems(names, (dialog, index) -> showLicense(names[index]))
          .setNegativeButton(android.R.string.cancel, null)
          .show();
    } catch (java.io.IOException failure) {
      Toast.makeText(
              requireContext(),
              UiText.choose("无法读取随包许可清单。", "Unable to read the bundled license list."),
              Toast.LENGTH_LONG)
          .show();
    }
  }

  private void showLicense(String name) {
    final View owner = getView();
    final android.content.res.AssetManager assets = requireContext().getAssets();
    new Thread(
            () -> {
              String content;
              try (var in = assets.open("licenses/" + name);
                  var out = new java.io.ByteArrayOutputStream()) {
                byte[] bytes = new byte[8192];
                int count;
                while ((count = in.read(bytes)) != -1) {
                  if (out.size() + count > 1024 * 1024)
                    throw new java.io.IOException("LICENSE_SIZE");
                  out.write(bytes, 0, count);
                }
                content = out.toString("UTF-8");
              } catch (java.io.IOException failure) {
                content = UiText.choose("无法读取此许可全文。", "Unable to read this license text.");
              }
              final String text = content;
              new android.os.Handler(android.os.Looper.getMainLooper())
                  .post(
                      () -> {
                        if (!isAdded() || getView() != owner) return;
                        CardSheet.show(requireContext(), name, text);
                      });
            },
            "license-read")
        .start();
  }
}
