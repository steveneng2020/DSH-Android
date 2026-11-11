package com.deepseekharness.app.util;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

/**
 * 版本名白名单的边界。
 *
 * <p><b>为什么这个测试必须存在</b>：2026-11-12 发现 App 内「检查更新」永远说「暂无更新」。
 * 根因是 {@code UpdatePolicy.Release.valid()} 里那条从上游继承的正则
 * {@code [A-Za-z0-9][A-Za-z0-9._+-]{0,127}} **不含空格、不含 @**，
 * 而本项目发布的版本名是 {@code v1.4 20261111@0.2.2-rc.1} ——
 * **自己发布的更新包被自己的校验丢掉**。
 *
 * <p>这条链路上没有任何报错，只有「没有更新」四个字，所以只靠人工验收极难发现
 * （要恰好在新版本发布后点一次检查更新，并确认能看到新版本）。固化成单测才能防回归。
 *
 * <p>同时必须拒绝注入类输入：版本名会进文件名、日志与界面，
 * 放行换行 / 路径分隔符 / 双向文本覆盖符等于开一条注入通道。
 */
public class UpdatePolicyVersionNameTest {

  /** 直接命中 WhiteList，不经过 Release 构造（构造器会做别的规范化）。 */
  private static boolean accepted(String version) {
    UpdatePolicy.Release release =
        new UpdatePolicy.Release(
            20050357,
            version,
            UpdatePolicy.STABLE,
            "standard",
            30,
            "arm64-v8a",
            "https://raw.githubusercontent.com/steveneng2020/DSH-Android/main/apk/x.apk",
            "a".repeat(64),
            100,
            "说明",
            "https://github.com/steveneng2020/DSH-Android/releases/tag/v1.4-20261111");
    return release.valid();
  }

  @Test
  public void acceptsThisProjectsActualVersionName() {
    // 最关键的一条：本项目当前发布的版本名必须通过，否则更新推不出去。
    assertTrue("本项目的版本名必须被接受", accepted("v1.4 20261111@0.2.2-rc.1"));
  }

  @Test
  public void acceptsOptionalDshaPrefix() {
    assertTrue(accepted("DSHA v1.4 20261111@0.2.2-rc.1"));
  }

  @Test
  public void acceptsUpstreamHistoricalShape() {
    // 上游与历史包用「数字 + 可选 -rcN」，不能因为收紧校验把它们判死。
    assertTrue(accepted("1.2.0-rc1.3"));
    assertTrue(accepted("v1.2.3"));
    assertTrue(accepted("1.2.3"));
  }

  @Test
  public void rejectsPathTraversal() {
    assertFalse(accepted("v1.4 20261111@0.2.2-rc.1 ../etc"));
    assertFalse(accepted("../../etc/passwd"));
  }

  @Test
  public void rejectsControlAndNewline() {
    assertFalse(accepted("v1.4 20261111@0.2.2-rc.1\nNEWLINE"));
    assertFalse(accepted("v1.4\t20261111"));
  }

  @Test
  public void rejectsBidiOverride() {
    // U+202E RIGHT-TO-LEFT OVERRIDE：在界面上能把真实文件名倒着显示。
    assertFalse(accepted("v1.4 20261111@0.2.2-rc.1\u202Eevil"));
  }

  @Test
  public void rejectsDottedOrPaddedNames() {
    assertFalse("连续点会被当成路径", accepted("v1..4"));
    assertFalse("首尾空白", accepted(" v1.2.3"));
    assertFalse("以点开头会变隐藏文件", accepted(".v1.2.3"));
  }

  @Test
  public void rejectsMalformedBuildDate() {
    // 构建日期必须 8 位；7 位会被当成畸形版本名。
    assertFalse(accepted("v1.4 2026111@0.2.2-rc.1"));
  }
}
