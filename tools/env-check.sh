#!/bin/sh
# DSHA on Eta 环境修补自检（交接规程 §6.8 的可执行版）
# 用法：cd "/storage/emulated/0/Download/Eta/DSHA开发/DSHA-src" && sh ../_env_check.sh
# 判据：全部 OK，退出码 0。有 FAIL 先修 §六，不要改代码。

cd "/storage/emulated/0/Download/Eta/DSHA开发/DSHA-src" || { echo "FAIL: 源码目录不存在"; exit 2; }
export PATH="/workspace/env/jdk17/bin:$PATH"

FAILN=0
ok()   { printf "  OK    %s\n" "$1"; }
bad()  { printf "  FAIL  %s\n" "$1"; FAILN=$((FAILN+1)); }

echo "=== 1. /opt/android-sdk 软链 ==="
if [ -L /opt/android-sdk ] && [ -d /opt/android-sdk ]; then
  ok "/opt/android-sdk -> $(readlink /opt/android-sdk)"
else
  bad "/opt/android-sdk 不是有效软链（§6.1）"
fi

echo "=== 2. build-tools/37.0.0（AGP 按 <ver>/aapt2 找）==="
[ -x /opt/sdk37/build-tools/37.0.0/aapt2 ] && ok "aapt2 存在且可执行" || bad "缺 37.0.0/aapt2（§6.2）"

echo "=== 3. build-tools/36.0.0（BUILD.md 要求）==="
[ -f /opt/sdk37/build-tools/36.0.0/package.xml ] && ok "package.xml 存在" || bad "缺 36.0.0/package.xml（§6.3）"

echo "=== 4. platforms/android-37.0 ==="
[ -d /opt/sdk37/platforms/android-37.0 ] && ok "android-37.0 可达" || bad "缺 android-37.0（§6.4）"

echo "=== 5. aapt2 能真跑 ==="
V=$(/opt/android-sdk/build-tools/37.0.0/aapt2 version 2>&1 | head -1)
case "$V" in
  *"Android Asset Packaging"*) ok "$V" ;;
  *) bad "aapt2 无法运行: $V（§6.5）" ;;
esac

echo "=== 6. 四个 asset 必须是实体文件（软链会断）==="
for f in dsh-runtime.bin dsh-runtime.inputs.json ubuntu-tools.bin offline-rootfs.bin; do
  P="app/src/main/assets/$f"
  if [ -L "$P" ]; then
    bad "$f 是软链（必须实体化，§6.6）"
  elif [ -f "$P" ]; then
    ok "$f $(stat -c %s "$P")B"
  else
    bad "$f 缺失（§6.6）"
  fi
done

echo "=== 7. git 可用 ==="
if [ "$(git rev-parse --is-inside-work-tree 2>/dev/null)" = "true" ]; then
  ok "git 可识别  基线与 HEAD: $(git rev-parse --short HEAD)  分支: $(git branch --show-current)"
else
  bad "git 不可用（§6.7：补 objects / hooksPath / safe.directory）"
fi

echo "=== 8. 工具链文件存在 ==="
for p in /workspace/env/jdk17/bin/java /workspace/env/gradle-9.3.1/bin/gradle; do
  [ -x "$p" ] && ok "$p" || bad "$p 不存在"
done
[ -d /workspace/env/gradle-home ] && ok "gradle-home $(du -sm /workspace/env/gradle-home | cut -f1)MB" || bad "gradle-home 不存在"

# 时区：本机 Debian 默认 UTC，TZ 为空。直接 `date` 会比北京时间慢 8 小时且可能跨天，
# 交付包命名与文档时间戳会整批写错（MEMORY §4 第 35 条）。这里只提示，不计入 FAILN 以外的新项。
if [ "$(TZ=Asia/Shanghai date +%z)" = "+0800" ]; then
  ok "时区 OK（北京 $(TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M')；本机默认 UTC，取时间必须带 TZ=Asia/Shanghai）"
else
  bad "TZ=Asia/Shanghai 不可用，无法取北京时间——禁止用裸 date 写时间戳"
fi

echo
if [ "$FAILN" -eq 0 ]; then
  echo "ENV CHECK PASS"
  exit 0
else
  echo "ENV CHECK FAILED ($FAILN 项)"
  exit 1
fi
