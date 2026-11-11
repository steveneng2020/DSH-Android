package com.deepseekharness.app.util;

import java.io.File;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 插件原生依赖体检：只读 ELF 头判断按 ABI 能否加载，不改动任何文件。
 *
 * <p>扫描上限 {@link #MAX_FILES} 个 {@code .node}，超过 {@link #MAX_PREVIEW_BYTES} 的文件不再
 * 读头，结果按「路径 + 大小 + 修改时间」缓存，避免每次进设置页都重新读盘。
 */
public final class NativeDepPrecheck {
  static final int CACHE_LIMIT = 256;
  static final int ELFCLASS64 = 2;
  static final int EM_AARCH64 = 183;
  static final int HEADER_BYTES = 64;
  static final int MAX_FILES = 64;
  static final long MAX_PREVIEW_BYTES = 10_485_760L;
  private static final Map<String, Cached> CACHE =
      Collections.synchronizedMap(
          new LinkedHashMap<String, Cached>(32, 0.75f, true) {
            @Override
            protected boolean removeEldestEntry(Map.Entry<String, Cached> eldest) {
              return size() > CACHE_LIMIT;
            }
          });

  /** 单个原生库的判定结果。 */
  public enum Status {
    /** 64 位小端 ARM 可加载。 */
    OK,
    /** ELF 但不是 AArch64。 */
    NON_AARCH64,
    /** 不是 ELF 文件。 */
    NOT_ELF,
    /** 超过只读预览上限。 */
    TOO_LARGE,
    /** 打不开或读失败。 */
    UNREADABLE
  }

  private NativeDepPrecheck() {}

  /** 一条扫描结果。 */
  public static final class Finding {
    public final long bytes;
    public final String path;
    public final Status status;

    Finding(String path, Status status, long bytes) {
      this.path = path;
      this.status = status;
      this.bytes = bytes;
    }
  }

  /** 缓存键：文件大小与修改时间任一变化都要重读。 */
  private record Cached(long size, long modified, Status status) {}

  public static void clearCache() {
    CACHE.clear();
  }

  /** 扫描目录下所有 {@code .node}，返回按目录名排序的结果。 */
  public static List<Finding> inspect(File root) {
    List<Finding> findings = new ArrayList<>();
    if (root != null && root.isDirectory()) scan(root, root, findings, new int[] {0});
    return findings;
  }

  private static void scan(File root, File directory, List<Finding> findings, int[] count) {
    File[] files = directory.listFiles();
    if (files == null) return;
    Arrays.sort(files, Comparator.comparing(File::getName));
    for (File file : files) {
      if (count[0] >= MAX_FILES) return;
      // 符号链接目录不跟随，避免在插件目录里绕圈。
      if (file.isDirectory() && !java.nio.file.Files.isSymbolicLink(file.toPath())) {
        scan(root, file, findings, count);
      } else if (file.isFile() && file.getName().endsWith(".node")) {
        count[0]++;
        findings.add(classify(root, file));
      }
    }
  }

  static Finding classify(File root, File file) {
    String path = file.getAbsolutePath();
    long size = file.length();
    long modified = file.lastModified();
    Cached cached = CACHE.get(path);
    if (cached != null && cached.size() == size && cached.modified() == modified) {
      return new Finding(relative(root, file), cached.status(), size);
    }
    Status status = readStatus(file, size);
    CACHE.put(path, new Cached(size, modified, status));
    return new Finding(relative(root, file), status, size);
  }

  private static String relative(File root, File file) {
    String base = root.getAbsolutePath();
    String path = file.getAbsolutePath();
    if (path.startsWith(base + File.separator)) path = path.substring(base.length() + 1);
    return path.replace(File.separatorChar, '/');
  }

  /** 只读 ELF 头：魔数、位宽、字节序与 {@code e_machine}。 */
  static Status readStatus(File file, long size) {
    if (size > MAX_PREVIEW_BYTES) return Status.TOO_LARGE;
    if (size < 20) return Status.NOT_ELF;
    byte[] header = new byte[HEADER_BYTES];
    try (RandomAccessFile stream = new RandomAccessFile(file, "r")) {
      int read = stream.read(header);
      if (read < 20) return Status.NOT_ELF;
      if (header[0] != 0x7f || header[1] != 'E' || header[2] != 'L' || header[3] != 'F') {
        return Status.NOT_ELF;
      }
      int elfClass = header[4] & 0xff;
      // EI_DATA 只支持小端（1）；大端架构在本机不可能加载。
      if ((header[5] & 0xff) != 1) return Status.NON_AARCH64;
      int machine =
          ByteBuffer.wrap(header, 18, 2).order(ByteOrder.LITTLE_ENDIAN).getShort() & 0xffff;
      return elfClass == ELFCLASS64 && machine == EM_AARCH64 ? Status.OK : Status.NON_AARCH64;
    } catch (IOException | SecurityException error) {
      return Status.UNREADABLE;
    }
  }

  /** 需要提醒用户的结果：读不出、非 AArch64、超大或非 ELF。 */
  public static boolean needsAttention(Finding finding) {
    return finding != null && finding.status != Status.OK;
  }

  /** 从体检结果里挑出需要提醒的条目。 */
  public static List<Finding> attention(List<Finding> findings) {
    List<Finding> result = new ArrayList<>();
    if (findings != null) {
      for (Finding finding : findings) {
        if (needsAttention(finding)) result.add(finding);
      }
    }
    return result;
  }

  public static String targetAbi() {
    return "arm64-v8a";
  }
}
