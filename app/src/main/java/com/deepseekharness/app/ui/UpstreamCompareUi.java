package com.deepseekharness.app.ui;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import com.deepseekharness.app.BuildConfig;
import com.deepseekharness.app.R;
import com.deepseekharness.app.core.TrustedNetwork;
import com.deepseekharness.app.util.Constants;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import javax.net.ssl.HttpsURLConnection;

/**
 * 「上游对比」区块：抓 GitHub 提交 Atom，判断本地基线是否还跟得上。
 *
 * <p>网络请求固定走单线程池，页面销毁时通过 {@link Session#cancel()} 打断，避免回调落到已卸载的视图。
 */
public final class UpstreamCompareUi {
  private static final String ATOM_PATH = "/commits/main.atom";
  private static final ExecutorService IO = Executors.newSingleThreadExecutor();

  private UpstreamCompareUi() {}

  /** 一次请求的生命周期句柄；取消后再提交会被立即打断。 */
  public static final class Session {
    private volatile boolean cancelled;
    private volatile Future<?> future;

    void attach(Future<?> task) {
      future = task;
      if (cancelled) task.cancel(true);
    }

    public void cancel() {
      cancelled = true;
      Future<?> task = future;
      if (task != null) task.cancel(true);
    }

    boolean isCancelled() {
      return cancelled;
    }
  }

  /**
   * 绑定区块内的控件。
   *
   * @param expandToggle 展开/收起开关
   * @param body 折叠正文
   * @param baseView 基线提交展示位
   * @param valueView 最新提交展示位
   * @param verdictView 结论展示位
   * @param checkButton 立即检查按钮
   * @param urlView 仓库地址展示位
   */
  public static Session wire(
      Context context,
      View root,
      int expandToggle,
      int body,
      int baseView,
      int valueView,
      int verdictView,
      int checkButton,
      int urlView) {
    Session session = new Session();
    View toggle = root.findViewById(expandToggle);
    View collapse = root.findViewById(body);
    if (toggle == null || collapse == null) return session;
    collapse.setVisibility(View.GONE);
    toggle.setOnClickListener(
        view -> {
          boolean opening = collapse.getVisibility() != View.VISIBLE;
          collapse.setVisibility(opening ? View.VISIBLE : View.GONE);
          ((TextView) view)
              .setText(
                  context.getString(
                      opening ? R.string.about_upstream_collapse : R.string.about_upstream_expand));
        });
    TextView base = root.findViewById(baseView);
    if (base != null) {
      base.setText(
          context.getString(
              R.string.about_upstream_base, shortSha(BuildConfig.UPSTREAM_BASE_COMMIT), BuildConfig.UPSTREAM_BASE_DATE));
    }
    TextView value = root.findViewById(valueView);
    TextView verdict = root.findViewById(verdictView);
    if (value != null) value.setText(R.string.about_upstream_not_checked_value);
    if (verdict != null) verdict.setText(R.string.about_upstream_not_checked);
    TextView url = root.findViewById(urlView);
    if (url != null) {
      url.setText(Constants.UPSTREAM_REPOSITORY_URL.replace("https://github.com/", "github.com/"));
    }
    Button check = root.findViewById(checkButton);
    if (check != null) {
      check.setOnClickListener(
          view -> {
            check.setEnabled(false);
            if (value != null) value.setText(R.string.about_upstream_checking);
            if (verdict != null) verdict.setText(R.string.about_upstream_checking);
            session.attach(
                IO.submit(
                    () -> {
                      UpstreamCompare.Result result = query(context);
                      new Handler(Looper.getMainLooper())
                          .post(
                              () -> {
                                if (session.isCancelled() || !check.isAttachedToWindow()) return;
                                check.setEnabled(true);
                                if (value != null) {
                                  value.setText(
                                      result.parsed == 0
                                          ? context.getString(
                                              R.string.about_upstream_unreadable_value)
                                          : shortSha(result.latest));
                                }
                                if (verdict != null) verdict.setText(verdictText(context, result));
                              });
                    }));
          });
    }
    return session;
  }

  /** 把结论翻成人话；落后时带上落后的提交数。 */
  static String verdictText(Context context, UpstreamCompare.Result result) {
    switch (result.verdict) {
      case SAME:
        return context.getString(R.string.about_upstream_same);
      case BEHIND:
        return context.getString(R.string.about_upstream_behind, result.distance);
      case BEYOND:
        return context.getString(R.string.about_upstream_beyond, result.window());
      case DIFFERS:
        return context.getString(R.string.about_upstream_differs);
      default:
        return context.getString(R.string.about_upstream_unreadable);
    }
  }

  static String shortSha(String sha) {
    if (sha == null) return "";
    return sha.length() < 7 ? sha : sha.substring(0, 7);
  }

  /**
   * 抓一次 Atom 并比较；任何网络/协议异常都折算成「读不出来」，不向上抛。
   *
   * <p>无网络、被墙、返回非 2xx 都走同一个兜底分支，界面只显示「无法读取」。
   */
  static UpstreamCompare.Result query(Context context) {
    HttpURLConnection connection = null;
    try {
      connection =
          (HttpURLConnection)
              new URL(Constants.UPSTREAM_REPOSITORY_URL + ATOM_PATH).openConnection();
      connection.setConnectTimeout(UpstreamCompare.TIMEOUT_MILLIS);
      connection.setReadTimeout(UpstreamCompare.TIMEOUT_MILLIS);
      connection.setRequestProperty("Accept", "application/atom+xml");
      connection.setRequestProperty("User-Agent", "DSHA-android");
      connection.setInstanceFollowRedirects(true);
      if (connection instanceof HttpsURLConnection) {
        try {
          ((HttpsURLConnection) connection).setSSLSocketFactory(TrustedNetwork.sockets(context));
        } catch (Exception ignored) {
          // 自定义信任链装不上时退回系统默认，不阻断检查。
        }
      }
      int code = connection.getResponseCode();
      if (code < 200 || code >= 300) {
        return new UpstreamCompare.Result(UpstreamCompare.Verdict.UNREADABLE, 0, "", 0);
      }
      try (InputStream stream = connection.getInputStream()) {
        String body = readBounded(stream, UpstreamCompare.MAX_BODY_BYTES);
        return UpstreamCompare.decide(body, BuildConfig.UPSTREAM_BASE_COMMIT);
      }
    } catch (Exception error) {
      return new UpstreamCompare.Result(UpstreamCompare.Verdict.UNREADABLE, 0, "", 0);
    } finally {
      if (connection != null) connection.disconnect();
    }
  }

  /** 最多读 {@code limit} 字节，超出部分直接丢弃。 */
  static String readBounded(InputStream stream, int limit) throws IOException {
    ByteArrayOutputStream buffer = new ByteArrayOutputStream(Math.min(limit, 8192));
    byte[] chunk = new byte[4096];
    int total = 0;
    while (total < limit) {
      int read = stream.read(chunk, 0, Math.min(4096, limit - total));
      if (read <= 0) break;
      buffer.write(chunk, 0, read);
      total += read;
    }
    return new String(buffer.toByteArray(), StandardCharsets.UTF_8);
  }
}
