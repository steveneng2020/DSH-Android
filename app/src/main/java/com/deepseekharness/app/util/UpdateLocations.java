package com.deepseekharness.app.util;

import java.net.URI;
import java.util.Locale;

/**
 * 更新清单、发布页与 APK 产物的来源白名单；APK 身份另行校验。
 *
 * <p><b>本 fork 的改动</b>：上游用自有站点 {@code dsha.cc} 作为更新通道，
 * 但该站点不索引本 fork 的包，且实测 TLS 握手直接断开
 * （{@code SSL routines::unexpected eof}），App 内更新对它永远失败。
 * 本 fork 改用自己仓库的静态 JSON，推送新版本即可自更新。
 *
 * <p>上游 v0.2.2 的 {@code dsha.cc} 分支保留为兼容读取（旧清单若仍被引用不崩溃），
 * 但 {@link #FEED} 与 {@link #DEFAULT_PAGE} 指向本仓库，实际不再走它。
 */
public final class UpdateLocations {
  /** 本 fork 的更新清单：仓库 main 分支根目录的 updates.json。 */
  public static final String FEED =
      "https://raw.githubusercontent.com/"
          + com.deepseekharness.app.BuildConfig.FORK_REPOSITORY_SLUG
          + "/main/updates.json";

  /** 本 fork 的发布页。 */
  public static final String DEFAULT_PAGE =
      "https://github.com/" + com.deepseekharness.app.BuildConfig.FORK_REPOSITORY_SLUG + "/releases";

  private UpdateLocations() {}

  private static URI parse(String value) {
    try {
      if (value == null || value.length() > 8192) return null;
      URI uri = new URI(value);
      String path = uri.getPath(), raw = uri.getRawPath().toLowerCase(Locale.ROOT);
      if (!"https".equalsIgnoreCase(uri.getScheme())
          || uri.getHost() == null
          || uri.getRawUserInfo() != null
          || uri.getFragment() != null
          || uri.getPort() != -1 && uri.getPort() != 443
          || path == null
          || path.indexOf('\\') >= 0
          || path.contains("//")
          || raw.contains("%2f")
          || raw.contains("%5c")
          || raw.contains("%25")) return null;
      for (String part : path.split("/", -1))
        if (part.equals(".") || part.equals("..")) return null;
      for (int i = 0; i < path.length(); i++)
        if (path.charAt(i) < 32 || path.charAt(i) == 127) return null;
      return uri;
    } catch (Exception invalid) {
      return null;
    }
  }

  private static boolean host(URI uri, String name) {
    return uri != null && name.equalsIgnoreCase(uri.getHost());
  }

  /** 本 fork 仓库的 slug（小写，用于路径比对）。 */
  private static String forkSlug() {
    return com.deepseekharness.app.BuildConfig.FORK_REPOSITORY_SLUG.toLowerCase(Locale.ROOT);
  }

  public static boolean feed(String value) {
    URI uri = parse(value);
    if (uri == null || uri.getRawQuery() != null) return false;
    String path = uri.getPath();
    // 本 fork 的通道：raw.githubusercontent.com/<slug>/main/updates.json
    if (host(uri, "raw.githubusercontent.com"))
      return ("/" + com.deepseekharness.app.BuildConfig.FORK_REPOSITORY_SLUG + "/main/updates.json")
          .equals(path);
    // 上游旧通道：保留只读兼容，不作为默认来源。
    return host(uri, "dsha.cc") && "/api/updates.json".equals(path);
  }

  public static boolean page(String value) {
    URI uri = parse(value);
    if (uri == null || uri.getRawQuery() != null) return false;
    String path = uri.getPath();
    // 本 fork 的发布页：github.com/<slug>/releases[/latest|/tag/<tag>]
    String lower = path.toLowerCase(Locale.ROOT);
    String forkPrefix = "/" + forkSlug() + "/releases";
    if (host(uri, "github.com")
        && (lower.equals(forkPrefix)
            || lower.equals(forkPrefix + "/")
            || lower.equals(forkPrefix + "/latest")
            || lower.startsWith(forkPrefix + "/tag/") && lower.length() > forkPrefix.length() + 5))
      return true;
    // 上游站点与上游仓库页面：只读兼容。
    if (host(uri, "dsha.cc"))
      return path.equals("/") || path.equals("/download") || path.equals("/download/");
    String upPrefix = "/dsh-app/dsha/releases";
    return host(uri, "github.com")
        && (lower.equals(upPrefix)
            || lower.equals(upPrefix + "/")
            || lower.equals(upPrefix + "/latest")
            || lower.startsWith(upPrefix + "/tag/") && lower.length() > upPrefix.length() + 5);
  }

  public static boolean artifact(String value) {
    URI uri = parse(value);
    if (uri == null) return false;
    String path = uri.getPath().toLowerCase(Locale.ROOT);
    if (!path.endsWith(".apk")) return false;
    // 本 fork 的 Release 资产。
    if (host(uri, "github.com")
        && path.startsWith("/" + forkSlug() + "/releases/download/")) return true;
    // 上游资产与旧站点下载路径：只读兼容。
    return host(uri, "dsha.cc") && path.startsWith("/downloads/")
        || host(uri, "github.com") && path.startsWith("/dsh-app/dsha/releases/download/");
  }

  public static String releasePage(String value) {
    return page(value) ? value : DEFAULT_PAGE;
  }

  public static boolean redirect(String original, String next) {
    if (feed(original)) return feed(next);
    if (!artifact(original)) return false;
    if (artifact(next)) return true;
    URI uri = parse(next);
    return (host(uri, "release-assets.githubusercontent.com")
            || host(uri, "objects.githubusercontent.com"))
        && uri.getPath().startsWith("/github-production-release-asset");
  }

  /** Native UI renders this as plain text; controls cannot spoof surrounding status. */
  public static String notes(String value) {
    if (value == null) return "";
    StringBuilder out = new StringBuilder();
    for (int i = 0; i < value.length() && out.length() < 8192; i++) {
      char c = value.charAt(i);
      if (c == '\r') {
        if (i + 1 < value.length() && value.charAt(i + 1) == '\n') i++;
        out.append('\n');
      } else if (c == '\n'
          || c == '\t'
          || c >= 32 && c != 127 && !(c >= 0x202a && c <= 0x202e) && !(c >= 0x2066 && c <= 0x2069))
        out.append(c);
    }
    return out.toString();
  }
}
