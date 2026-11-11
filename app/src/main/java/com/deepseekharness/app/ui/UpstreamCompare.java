package com.deepseekharness.app.ui;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** 把上游提交流与本地基线提交比出「一致 / 落后 / 已分叉」，纯逻辑无网络。 */
public final class UpstreamCompare {
  private static final Pattern COMMIT_ID =
      Pattern.compile("<id>tag:github\\.com,2008:Grit::Commit/([0-9a-f]{40})</id>");
  static final int MAX_BODY_BYTES = 65536;
  static final int MAX_COMMITS = 100;

  /**
   * 与代码无关的提交标题前缀；判定「是否落后」时不计入。
   *
   * <p>上游仓库每天自动刷新 star 曲线图、偶尔补 README 赞助商，这类提交不改变任何
   * 代码。若把它们算进落后数量，本项目会永久显示「落后 N 个提交」，而功能其实
   * 完全同步——2026-11-10 实测 a8f898d..main 的 35 个提交里 33 个是 star 曲线、
   * 2 个是 README 赞助商，零代码改动。
   */
  private static final Pattern NON_CODE_TITLE =
      Pattern.compile("^\\s*(chore\\(star-history\\)|docs:|chore\\(deps\\)|chore\\(release\\))",
                      Pattern.CASE_INSENSITIVE);

  /** 从 Atom 正文里按出现顺序取出「提交标题」，与 {@link #parseCommits} 一一对应。 */
  public static List<String> parseTitles(String body) {
    List<String> titles = new ArrayList<>();
    if (body != null && !body.isEmpty()) {
      Matcher matcher = TITLE_TAG.matcher(body);
      while (matcher.find() && titles.size() < MAX_COMMITS) {
        titles.add(matcher.group(1).replaceAll("\\s+", " ").trim());
      }
    }
    return titles;
  }

  /** Atom 里每个 entry 的 `<title>…</title>`（跳过 feed 自身的 title）。 */
  private static final Pattern TITLE_TAG =
      Pattern.compile("<entry>\\s*<id>[^<]*</id>\\s*<link[^>]*/>\\s*<title>([^<]*)</title>",
                      Pattern.DOTALL);

  /** 是否为不改变代码的提交（图表刷新、纯文档、依赖与发布元数据）。 */
  static boolean isNonCode(String title) {
    return title != null && NON_CODE_TITLE.matcher(title).find();
  }
  static final int TIMEOUT_MILLIS = 8000;

  /** 比较结论。 */
  public enum Verdict {
    /** 上游最新提交就是本地基线。 */
    SAME,
    /** 基线出现在上游历史里，但不在最新。 */
    BEHIND,
    /** 上游历史里找不到基线，且本地只落后有限提交（Atom 窗口不足）。 */
    BEYOND,
    /** 上游历史里找不到基线，且无法确认是「窗口不足」还是真分叉。 */
    DIFFERS,
    /** 内容为空或读不出来。 */
    UNREADABLE
  }

  /** 比较结果；{@code latest} 是上游最新提交，{@code parsed} 是解析出的提交条数。 */
  public static final class Result {
    public final int distance;
    public final String latest;
    public final int parsed;
    public final Verdict verdict;

    Result(Verdict verdict, int distance, String latest, int parsed) {
      this.verdict = verdict;
      this.distance = distance;
      this.latest = latest == null ? "" : latest;
      this.parsed = parsed;
    }

      public boolean hasDistance() {
      return verdict == Verdict.BEHIND;
    }

    /** Atom 窗口内没找到基线；返回窗口条数，供文案说明「至少落后这么多」。 */
    public int window() {
      return parsed;
    }
  }

  private UpstreamCompare() {}

  /** 从 Atom 正文里按出现顺序取提交哈希，最多 {@link #MAX_COMMITS} 条。 */
  public static List<String> parseCommits(String body) {
    List<String> commits = new ArrayList<>();
    if (body != null && !body.isEmpty()) {
      Matcher matcher = COMMIT_ID.matcher(body);
      while (matcher.find() && commits.size() < MAX_COMMITS) commits.add(matcher.group(1));
    }
    return commits;
  }

  /**
   * 比较上游提交流与期望的基线提交。
   *
   * @param body Atom 正文
   * @param expected 本地基线提交，可只给前缀；空表示无法比对
   */
  public static Result decide(String body, String expected) {
    List<String> commits = parseCommits(body);
    if (commits.isEmpty()) return new Result(Verdict.UNREADABLE, 0, "", 0);
    String wanted = expected == null ? "" : expected.trim().toLowerCase(Locale.ROOT);
    if (wanted.isEmpty()) return new Result(Verdict.DIFFERS, 0, commits.get(0), commits.size());
    List<String> titles = parseTitles(body);
    for (int i = 0; i < commits.size(); i++) {
      if (commits.get(i).startsWith(wanted)) {
        // 只统计基线之后真正改代码的提交；图表/文档提交不算落后。
        int codeAhead = 0;
        for (int j = 0; j < i; j++) {
          String title = j < titles.size() ? titles.get(j) : "";
          if (!isNonCode(title)) codeAhead++;
        }
        return codeAhead == 0
            ? new Result(Verdict.SAME, 0, commits.get(0), commits.size())
            : new Result(Verdict.BEHIND, codeAhead, commits.get(0), commits.size());
      }
    }
    // 基线落在窗口之外。GitHub 的 commits/*.atom 实测只返回最近 20 条，
    // 而本项目同步上游代码后，上游会持续推送 star 曲线刷新等非代码提交，
    // 基线很快就被挤出窗口——这不代表功能落后。
    // 若窗口内**全部**是非代码提交，说明代码层面仍与上游一致，判 SAME。
    int codeInWindow = 0;
    for (int j = 0; j < commits.size(); j++) {
      String title = j < titles.size() ? titles.get(j) : "";
      if (!isNonCode(title)) codeInWindow++;
    }
    if (codeInWindow == 0) {
      return new Result(Verdict.SAME, 0, commits.get(0), commits.size());
    }
    // 窗口内确有代码提交、但基线仍不可见 ⇒ 至少落后这么多，不谎称已分叉。
    return new Result(Verdict.BEYOND, codeInWindow, commits.get(0), commits.size());
  }

  /** 对外只读视图。 */
  public static List<String> commits(String body) {
    return Collections.unmodifiableList(parseCommits(body));
  }
}
