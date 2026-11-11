package com.deepseekharness.app.util;

import java.net.URI;
import java.util.List;
import java.util.ArrayList;
import java.util.Collections;

/** 更新选择只看版本码、通道和安装变体，不从 rc/low 文件名猜版本先后。 */
public final class UpdatePolicy {
  public static final String STABLE = "stable", PREVIEW = "preview";

  private UpdatePolicy() {}

  public static final class Release {
    public final int versionCode, minSdk;
    public final String version, channel, flavor, abi, url, sha256, notes, pageUrl;
    public final long bytes;

    public Release(
        int code,
        String version,
        String channel,
        String flavor,
        int minSdk,
        String abi,
        String url,
        String sha256,
        long bytes,
        String notes,
        String pageUrl) {
      this.versionCode = code;
      this.version = version;
      this.channel = channel;
      this.flavor = flavor;
      this.minSdk = minSdk;
      this.abi = abi;
      this.url = url;
      this.sha256 = sha256;
      this.bytes = bytes;
      this.notes = UpdateLocations.notes(notes);
      this.pageUrl = UpdateLocations.releasePage(pageUrl);
    }

    public boolean valid() {
      return versionCode > 0
          && minSdk >= 23
          && minSdk <= 100
          && versionNameValid(version)
          && (STABLE.equals(channel) || PREVIEW.equals(channel))
          && ("standard".equals(flavor) || "low".equals(flavor))
          && "arm64-v8a".equals(abi)
          && UpdateLocations.artifact(url)
          && UpdateLocations.page(pageUrl)
          && sha256 != null
          && sha256.matches("[a-fA-F0-9]{64}")
          && bytes > 0
          && bytes <= 1024L * 1024 * 1024;
    }
  }

  /**
   * 版本名是否可接受。
   *
   * <p><b>为什么不能沿用上游那条正则</b>：上游 {@code valid()} 用的是
   * {@code [A-Za-z0-9][A-Za-z0-9._+-]{0,127}} —— **不含空格、不含 @**。
   * 而本项目的版本名是 {@code v1.4 20261111@0.2.2-rc.1}（带空格与 @），
   * 于是**自己发布的更新包会被自己的校验丢掉**：App 内「检查更新」永远说「暂无更新」。
   * 2026-11-12 实测：{@code updates.json} 登记的正是这个串，用上游正则判定为 REJECT。
   *
   * <p>判据分两支：
   * <ul>
   *   <li>带构建日期形态（{@code v1.4 20261111@0.2.2-rc.1}）—— 本项目实际用的形态，
   *       允许「前缀 + 版本 + 空格 + 8 位日期 @ 打包版本」
   *   <li>简单形态（{@code v1.2.3}）—— 兼容上游与历史包
   * </ul>
   *
   * <p>两支都**不允许**换行、路径分隔符、控制字符与双向文本覆盖符 —— 版本名会进
   * 文件名、日志与界面，放行这些等于开一条注入通道。
   */
  private static boolean versionNameValid(String version) {
    if (version == null || version.isEmpty() || version.length() > 160) return false;
    // 先做一遍字符白名单：拦住控制字符、换行、路径分隔符、Unicode 双向覆盖符。
    for (int i = 0; i < version.length(); i++) {
      char c = version.charAt(i);
      boolean ok =
          (c >= 'A' && c <= 'Z')
              || (c >= 'a' && c <= 'z')
              || (c >= '0' && c <= '9')
              || c == '.'
              || c == '_'
              || c == '+'
              || c == '-'
              || c == '@'
              || c == ' ';
      if (!ok) return false;
    }
    // 不允许「以点或连字符开头」（会变隐藏文件 / 非法文件名），也不允许连续两点。
    if (version.startsWith(".") || version.startsWith("-")) return false;
    if (version.contains("..")) return false;
    // 不允许首尾空白。
    if (!version.equals(version.trim())) return false;

    // 形态一：{版本} + 空格 + 8 位构建日期 + @ + 打包版本
    if (version.matches(
        "(?:(?:DSHA )?(?:v|rc)[0-9]+(?:\\.[0-9]+)*) [0-9]{8}@[A-Za-z0-9][A-Za-z0-9._+-]{0,63}"))
      return true;
    // 形态二：简单版本号，含上游历史格式 `1.2.0-rc1.3`。
    // 上游与历史包用的是「数字开头 + 可选 -rcN 后缀」，必须继续接受，
    // 否则 UpdatePolicyTest 里已有的 release 样本会被判非法（实测会红）。
    return version.matches(
        "[0-9]+(?:\\.[0-9]+)*(?:-[A-Za-z0-9]+(?:\\.[0-9]+)*)?"
            + "|(?:DSHA )?(?:v|rc)[0-9]+(?:\\.[0-9]+)*");
  }

  public static String defaultChannel(String version) {
    return version != null && version.contains("-") ? PREVIEW : STABLE;
  }

  /** The v1 feed records one complete signer, never an unknown or partial signer set. */
  public static boolean feedIdentityMatches(
      String installedPackage, List<String> installedSigners, String packageName, String signer) {
    return installedPackage != null
        && installedPackage.equals(packageName)
        && signer != null
        && installedSignersMatch(
            installedSigners, Collections.singletonList(signer.toLowerCase(java.util.Locale.ROOT)));
  }

  /** 旧稳定包可由两种通道选中，不能用发布通道或当前偏好猜测查询来源。 */
  public static String restoreCheckedChannel(
      boolean recorded, String checkedChannel, String releaseChannel) {
    if (recorded)
      return STABLE.equals(checkedChannel) || PREVIEW.equals(checkedChannel)
          ? checkedChannel
          : null;
    // 旧选择契约明确禁止稳定通道接收预览包，只有这一种旧来源可以确定。
    return PREVIEW.equals(releaseChannel) ? PREVIEW : null;
  }

  public static Release select(
      List<Release> releases, int currentCode, String flavor, int sdk, String channel) {
    if (!STABLE.equals(channel) && !PREVIEW.equals(channel))
      throw new IllegalArgumentException(com.deepseekharness.app.util.UiText.text("未知更新通道"));
    Release best = null;
    for (Release r : releases) {
      if (!r.valid() || !flavor.equals(r.flavor) || r.minSdk > sdk || r.versionCode <= currentCode)
        continue;
      if (STABLE.equals(channel) && !STABLE.equals(r.channel)) continue;
      if (best == null
          || r.versionCode > best.versionCode
          || (r.versionCode == best.versionCode && STABLE.equals(r.channel))) best = r;
    }
    return best;
  }

  public static boolean https(String value) {
    try {
      URI uri = new URI(value);
      return "https".equalsIgnoreCase(uri.getScheme())
          && uri.getHost() != null
          && uri.getRawUserInfo() == null
          && uri.getFragment() == null;
    } catch (Exception e) {
      return false;
    }
  }

  /** Match the complete current signer set; neither an empty set nor a subset is trusted. */
  public static boolean installedSignersMatch(List<String> installed, List<String> candidate) {
    if (installed == null
        || candidate == null
        || installed.isEmpty()
        || installed.size() != candidate.size()) return false;
    ArrayList<String> oldHashes = new ArrayList<>(installed),
        newHashes = new ArrayList<>(candidate);
    for (List<String> hashes : List.of(oldHashes, newHashes))
      for (String hash : hashes) if (hash == null || !hash.matches("[a-f0-9]{64}")) return false;
    Collections.sort(oldHashes);
    Collections.sort(newHashes);
    return oldHashes.equals(newHashes);
  }
}
