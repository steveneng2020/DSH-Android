package com.deepseekharness.app.ui;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import com.deepseekharness.app.R;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import org.json.JSONArray;
import org.json.JSONObject;
import com.deepseekharness.app.util.VersionSeparator;

/** 「更新日记」列表：默认只显示最近几条，点按钮展开全部。 */
public final class ChangelogPanel {
  static final int DEFAULT_VISIBLE = 5;

  private ChangelogPanel() {}

  /** 按控件 id 取容器并填充；容器缺失时返回 0。 */
  public static int populate(Context context, View root, int box, int list, int more) {
    View boxView = root.findViewById(box);
    ViewGroup listView = (ViewGroup) root.findViewById(list);
    Button moreButton = (Button) root.findViewById(more);
    if (boxView == null || listView == null) return 0;
    return populateInto(context, boxView, listView, moreButton);
  }

  /**
   * 填充列表。
   *
   * @return 条目总数；读取或渲染失败返回 0
   */
  public static int populateInto(Context context, View box, ViewGroup list, Button moreButton) {
    if (box == null || list == null) return 0;
    box.setVisibility(View.VISIBLE);
    final JSONArray entries;
    try {
      entries = readEntries(context);
    } catch (Exception error) {
      showMessage(context, list, R.string.about_changelog_unavailable);
      if (moreButton != null) moreButton.setVisibility(View.GONE);
      return 0;
    }
    if (entries == null || entries.length() == 0) {
      showMessage(context, list, R.string.about_changelog_unavailable);
      if (moreButton != null) moreButton.setVisibility(View.GONE);
      return 0;
    }
    int total = entries.length();
    final int visible = Math.min(DEFAULT_VISIBLE, total);
    try {
      render(context, list, entries, visible);
    } catch (Throwable error) {
      list.removeAllViews();
      showMessage(context, list, R.string.about_changelog_unavailable);
      if (moreButton != null) moreButton.setVisibility(View.GONE);
      return 0;
    }
    if (moreButton != null) {
      if (total <= visible) {
        moreButton.setVisibility(View.GONE);
      } else {
        moreButton.setVisibility(View.VISIBLE);
        moreButton.setText(context.getString(R.string.about_changelog_expand, total));
        moreButton.setOnClickListener(
            view -> {
              render(context, list, entries, total);
              view.setVisibility(View.GONE);
            });
      }
    }
    return total;
  }

  /** 读随包附带的更新日记；格式不对一律抛异常，由调用方降级成提示。 */
  static JSONArray readEntries(Context context) throws Exception {
    try (InputStream stream = context.getResources().openRawResource(R.raw.changelog_recent)) {
      ByteArrayOutputStream buffer = new ByteArrayOutputStream();
      byte[] chunk = new byte[8192];
      while (true) {
        int read = stream.read(chunk);
        if (read <= 0) break;
        buffer.write(chunk, 0, read);
      }
      JSONObject root = new JSONObject(buffer.toString("UTF-8"));
      if (root.optInt("schema", 0) != 1) throw new IllegalArgumentException("schema");
      JSONArray entries = root.optJSONArray("entries");
      if (entries == null || entries.length() == 0) throw new IllegalArgumentException("entries");
      for (int i = 0; i < entries.length(); i++) {
        JSONObject entry = entries.optJSONObject(i);
        if (entry == null) throw new IllegalArgumentException("entry");
        if (entry.optString("version", "").isEmpty()) {
          throw new IllegalArgumentException("version");
        }
        if (entry.optString("title", "").isEmpty()) throw new IllegalArgumentException("title");
        JSONArray bullets = entry.optJSONArray("bullets");
        if (bullets == null || bullets.length() == 0) {
          throw new IllegalArgumentException("bullets");
        }
      }
      return entries;
    }
  }

  /** 版本号与构建号拼一行，构建号缺失时只显示版本号。 */
  static CharSequence versionLine(JSONObject entry) {
    String version = entry.optString("version", "");
    String build = entry.optString("build", "");
    // 分隔符固定 U+2022（•），但它的字形天生偏下，必须由 VersionSeparator 做基线修正 ——
    // 直接拼字符串会看起来「掉下去」（2026-11-12 用户真机指出）。
    return build.isEmpty() ? version : VersionSeparator.between(version, build);
  }

  private static void render(Context context, ViewGroup list, JSONArray entries, int count) {
    list.removeAllViews();
    LayoutInflater inflater = LayoutInflater.from(context);
    float density = context.getResources().getDisplayMetrics().density;
    for (int i = 0; i < count; i++) {
      JSONObject entry = entries.optJSONObject(i);
      if (entry == null) continue;
      View item = inflater.inflate(R.layout.item_changelog_entry, list, false);
      ((TextView) item.findViewById(R.id.changelog_entry_version)).setText(versionLine(entry));
      ((TextView) item.findViewById(R.id.changelog_entry_title))
          .setText(entry.optString("title", ""));
      ViewGroup bullets = (ViewGroup) item.findViewById(R.id.changelog_entry_bullets);
      bullets.removeAllViews();
      JSONArray lines = entry.optJSONArray("bullets");
      if (lines != null) {
        for (int j = 0; j < lines.length(); j++) {
          String line = lines.optString(j, "");
          if (line.isEmpty()) continue;
          TextView bullet = new TextView(context);
          bullet.setText("· " + line);
          bullet.setTextSize(2, 12f);
          bullet.setTextColor(
              context.getResources().getColor(R.color.text_secondary, context.getTheme()));
          bullet.setLineSpacing(0f, 1.15f);
          LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
          params.bottomMargin = (int) (3f * density);
          bullets.addView(bullet, params);
        }
      }
      // 最后一条不画分隔线。
      item.findViewById(R.id.changelog_entry_divider)
          .setVisibility(i == count - 1 ? View.GONE : View.VISIBLE);
      list.addView(item);
    }
  }

  private static void showMessage(Context context, ViewGroup list, int message) {
    list.removeAllViews();
    TextView view = new TextView(context);
    view.setText(message);
    view.setTextSize(2, 12f);
    view.setTextColor(context.getResources().getColor(R.color.text_secondary, context.getTheme()));
    list.addView(view);
  }
}
