package com.deepseekharness.app.core;

import android.content.Context;
import com.deepseekharness.app.util.GuestCommandOutcome;
import com.deepseekharness.app.util.ProfileConfigPath;
import com.deepseekharness.app.util.ShellQuote;
import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicBoolean;
import org.json.JSONException;
import org.json.JSONObject;

/** 在容器内跑一次性脚本，把缺少推理档位的模型补齐；同一时刻只允许一个任务。 */
public final class ReasoningAutofit {
  private static final AtomicBoolean RUNNING = new AtomicBoolean(false);
  static final String SCRIPT = "reasoning-autofit.cjs";
  private final HarnessController controller;

  /** 阶段回调；参数是阶段名、已完成数与总数。 */
  public interface Progress {
    void update(String stage, int done, int total, String message);
  }

  /** 脚本返回值；字段直接对应容器内 JSON 的键。 */
  public static final class Result {
    public final String backup;
    public final boolean changed;
    public final int probed;
    public final JSONObject raw;
    public final int skipped;
    public final int total;
    public final int written;

    Result(JSONObject json) {
      raw = json;
      total = json.optInt("total", 0);
      written = json.optInt("written", 0);
      skipped = json.optInt("skipped", 0);
      probed = json.optInt("probed", 0);
      backup = json.optString("backup", "");
      changed = json.optBoolean("changed", false);
    }
  }

  public ReasoningAutofit(HarnessController controller) {
    this.controller = controller;
  }

  public static boolean isRunning() {
    return RUNNING.get();
  }

  /**
   * 执行一次补全；{@code probe} 为假时脚本只读不探测。
   *
   * @return 脚本自报的统计
   */
  public Result run(String profile, boolean probe, Progress progress)
      throws InterruptedException, IOException {
    if (!RUNNING.compareAndSet(false, true)) throw new IOException("REASONING_AUTOFIT_RUNNING");
    try {
      report(progress, "preparing", 0, 0, "");
      if (profile == null || profile.isEmpty()) profile = "web";
      if (!ProfileConfigPath.profile(profile)) throw new IOException("REASONING_AUTOFIT_PROFILE");
      File root = controller.proot().getRootfsDir().getAbsoluteFile();
      File script = new File(root, "root/.dsha-reasoning-autofit.cjs");
      // 上游 v0.2.2 起 HarnessController 不再提供 readAsset(String)（该类从 57 KB
      // 重构到 8 KB，读取职责已下放）。直接走 AssetManager，语义等价。
      String asset;
      try (java.io.InputStream input = controller.context().getAssets().open(SCRIPT)) {
        asset = new String(input.readAllBytes(), StandardCharsets.UTF_8);
      } catch (java.io.FileNotFoundException missing) {
        asset = "";
      }
      if (asset.isEmpty()) throw new IOException("REASONING_AUTOFIT_SCRIPT_MISSING");
      writeContainer(root, script, asset.getBytes(StandardCharsets.UTF_8));
      File progressFile = new File(root, "root/.dsha-reasoning-autofit.progress");
      StringBuilder command = new StringBuilder("node ");
      command.append(ShellQuote.arg("/root/.dsha-reasoning-autofit.cjs"));
      command.append(" /root/.dsh/node_modules --profile ");
      command.append(ShellQuote.arg("/root/.dsh/profiles/" + profile + "/cordis.patch.yml"));
      command.append(" --credentials ");
      command.append(ShellQuote.arg("/root/.dsh/.credentials.yaml"));
      command.append(" --progress ");
      command.append(ShellQuote.arg("/root/.dsha-reasoning-autofit.progress"));
      command.append(probe ? "" : " --no-probe");
      command.append(" 2>&1");
      report(progress, "probing", 0, 0, "");
      String output =
          GuestCommandOutcome.requireCompleted(
              controller.proot().execAndReadWithProotResult(command.toString(), 900_000L),
              "REASONING_AUTOFIT");
      int marker = output == null ? -1 : output.lastIndexOf("DSHA_REASONING_AUTOFIT=");
      if (marker < 0) throw new IOException("REASONING_AUTOFIT_NO_RESULT");
      try {
        JSONObject json = new JSONObject(output.substring(marker + 23).trim());
        if (!json.optBoolean("ok", true)) {
          throw new IOException(json.optString("error", "REASONING_AUTOFIT_FAILED"));
        }
        report(progress, "done", json.optInt("total", 0), json.optInt("total", 0), "");
        progressFile.delete();
        Result result = new Result(json);
        RUNNING.set(false);
        return result;
      } catch (JSONException error) {
        throw new IOException("REASONING_AUTOFIT_BAD_RESULT", error);
      }
    } catch (Throwable error) {
      RUNNING.set(false);
      throw error;
    }
  }

  private static void report(Progress progress, String stage, int done, int total, String message) {
    if (progress != null) progress.update(stage, done, total, message);
  }

  /**
   * 只允许写到 rootfs 内部。
   *
   * 2026-11-10 修：原实现走 {@code AndroidBackupFileSystem.atomic}，该路径用
   * {@code O_NOFOLLOW} 逐段打开父目录（{@code anchored()}），而应用私有目录的
   * 真实路径含 {@code /data/user/0}（指向 {@code /data/data} 的符号链接），
   * 于是必然抛 {@code PARENT_LINK}，自动适配从未成功启动过。
   *
   * 这里写入的是本 App 自己私有目录内的临时脚本，不是需要防符号链接攻击的备份记录，
   * 因此改回普通原子替换（同目录临时文件 + rename），语义足够且不再误伤。
   * 路径前缀校验保留，边界不变。
   */
  private static void writeContainer(File root, File target, byte[] bytes) throws IOException {
    String prefix = root.getAbsolutePath();
    if (!target.getAbsolutePath().startsWith(prefix + File.separator)) {
      throw new IOException("REASONING_AUTOFIT_PATH");
    }
    File directory = target.getParentFile();
    if (directory == null || !directory.isDirectory() && !directory.mkdirs()) {
      throw new IOException("REASONING_AUTOFIT_PARENT");
    }
    File temp = new File(directory, target.getName() + ".tmp");
    try (java.io.FileOutputStream out = new java.io.FileOutputStream(temp)) {
      out.write(bytes);
      out.getFD().sync();
    }
    if (!temp.renameTo(target)) {
      temp.delete();
      throw new IOException("REASONING_AUTOFIT_WRITE");
    }
  }

  /** 当前只支持默认的 web profile，保留参数以固定调用方签名。 */
  public static String defaultProfile(Context context) {
    return "web";
  }
}
