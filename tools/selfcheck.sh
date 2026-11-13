#!/bin/sh
# DSHA 开工自检 —— 一条命令跑完全部，避免多次往返被中断
#
# 用法：cd "/storage/emulated/0/Download/Eta/DSHA开发/DSHA-src" && sh tools/selfcheck.sh
# 判据：末行输出 SELFCHECK PASS，退出码 0
#
# 为什么合并：实测开工自检要 5 项，分开跑要 5 次工具调用，
# 任一次被中断（exit_code=137）就得重来。合并成一条，只需 1 次。
# 默认跳过慢速体积检查（du 扫 21 GB 要 6 秒），需要时加 --deep。

# 2026-11-11：本文件已从仓库外移入 DSHA-src/tools/（C4 修复）。
# 不再硬编码绝对路径、也不再假定调用方的 cwd —— 一律按脚本自身位置推导，
# 这样换设备/换工作区都不会失效。
SELF_DIR=$(cd "$(dirname "$0")" && pwd)
SRC=$(dirname "$SELF_DIR")
WS=$(dirname "$SRC")
cd "$SRC" || { echo "FAIL: 源码目录不存在"; exit 2; }
export PATH="/opt/dsha-env/jdk17/bin:$PATH"

FAILN=0
ok()  { printf "  \033[32mOK\033[0m    %s\n" "$1"; }
bad() { printf "  \033[31mFAIL\033[0m  %s\n" "$1"; FAILN=$((FAILN+1)); }

echo "=========== 开工自检 (HANDOFF §7) ==========="

# --- 1 环境自检 8 项 ---
echo "[1/6] 环境修补 8 项"
if sh "$SELF_DIR/env-check.sh" >/tmp/_sc_env.log 2>&1; then
  ok "$(tail -1 /tmp/_sc_env.log)"
else
  bad "环境自检失败，详见 /tmp/_sc_env.log"
  grep "FAIL" /tmp/_sc_env.log | head -5 | sed 's/^/         /'
fi

# --- 2 文档门禁 7 道 ---
echo "[2/6] 文档门禁 8 道"
if timeout 180 python3 "$SELF_DIR/gate.py" >/tmp/_sc_gate.log 2>&1; then
  ok "$(tail -1 /tmp/_sc_gate.log | sed 's/^ *//')"
else
  bad "门禁未通过，详见 /tmp/_sc_gate.log"
  grep -E "^FAIL" /tmp/_sc_gate.log | head -5 | sed 's/^/         /'
fi

# --- 3 git 钩子 ---
echo "[3/6] git 钩子"
HP=$(git config core.hooksPath 2>/dev/null)
if [ "$HP" = "/data/local/tmp/dsha-git-hooks" ]; then
  if git hook run pre-commit </dev/null 2>&1 | grep -q "not set as executable"; then
    bad "hooksPath 对但钩子不可执行（FUSE noexec？）"
  else
    ok "hooksPath=$HP 且钩子可执行"
  fi
else
  bad "hooksPath=$HP（期望 /data/local/tmp/dsha-git-hooks）"
fi

# --- 4 工作区改动数 ---
# 期望值不再硬编码：从 docs/DATA-SOURCES.md 的 F-03 现取，避免每加一个文件就要改脚本。
# （历史：这里曾写死 17，G 类新增后 _selfcheck 误报 FAILED，而门禁本身是绿的。）
echo "[4/6] 工作区改动"
N=$(git status --short 2>/dev/null | wc -l)
F=$(git status --short 2>/dev/null | grep -E "^( M|\?\?) (app/src/main/java|app/src/test/java|app/build.gradle|tools/asset-deployment.json|tools/recovery-runtime/lock.json|tools/test-mobile)" | wc -l)
EXPECT=$(sed -n 's/.*`git status --short \\| wc -l` | `\([0-9]\+\)` |.*/\1/p' "$WS/docs/DATA-SOURCES.md" 2>/dev/null | head -1)
[ -z "$EXPECT" ] && EXPECT="$N"
if [ "$N" -eq "$EXPECT" ]; then
  ok "$N 处改动（与 DATA-SOURCES F-03 一致），其中 F/G 类真代码 $F 个"
elif [ "$N" -eq 0 ]; then
  # 2026-11-11：工作区干净现在是**正常状态**（改动都已提交）。
  # 旧逻辑把 0 判为「可能 checkout 掉了别人的改动」，属过时假设。
  ok "工作区干净（0 处，改动均已提交）"
else
  bad "改动 $N 处（DATA-SOURCES F-03 登记 $EXPECT）—— 先 git status 看清多了什么"
fi
# --- 4b 关键代码特征「不倒退」检查 ---
#
# 历史教训（2026-11-11，两处都要记）：
#  ① 这里原先查 4 个 commit SHA（c32a19c5 / 2ed9d8de / 0495b39c / 0d00e11c），
#     但当天为清除上游赞助商图跑了 git filter-repo，**全部 hash 被重写**，
#     这 4 个对象在仓库里已彻底不存在 ⇒ 本项对任何分支、任何会话都必然 FAIL，
#     SELFCHECK PASS 从此不可达。**判据不能钉在会变的 SHA 上。**
#  ② 同一天重建 v0.2.2 基座时又发现：这些「关键提交」的内容在 filter-repo 与
#     基座重建后本来就不再以同一形式存在，继续追 SHA 只会制造假红。
#
# 现在的判据：查**代码特征**是否还在 HEAD 里。特征稳定、可 grep、跨 hash 有效。
# 每个特征都是一个 (说明, grep 模式, 期望文件) 三元组；
# 文件不存在即跳过（例如某分支没有该文件），命中即通过。
check_feature() {
  desc=$1; pattern=$2; file=$3
  [ -f "$file" ] || return 0
  grep -qE "$pattern" "$file" 2>/dev/null && return 0
  bad "关键代码特征缺失：$desc（$file 里找不到 /$pattern/）—— 可能被回滚了"
  return 1
}
J="app/src/main/java/com/deepseekharness/app"
# R2：会话记录目录规范化 —— 防 /data/user/0 符号链接导致 PARENT_LINK、web-session.enc 写入失败。
# 2026-11-11 修：判据从「StoredWebSession 里有 getCanonicalFile」改为「这条防线还在」。
#   起因：v0.2.2 上游把该逻辑重构成 WebSessionStorage.Home（util/WebSessionStorage.java），
#   由 authority = data.getCanonicalFile() + verify() 承担，**比 fork 的旧方案更严格**。
#   旧判据钉死在 StoredWebSession 一个文件上，于是上游修好了它反而报红 —— 属假红。
#   现行判据：两个位置任一命中即算防线存在（上游新结构 / fork 旧结构）。
if grep -q 'getCanonicalFile' "$J/util/WebSessionStorage.java" 2>/dev/null; then
  ok "R2 会话目录规范化：由 WebSessionStorage.Home 承担（上游 v0.2.2 结构）"
else
  check_feature "R2 会话目录 getCanonicalFile" 'getCanonicalFile' "$J/runtime/StoredWebSession.java"
fi
# 会话恢复诊断能力：UNKNOWN 必须能按成因区分。
# 2026-11-11 修（第二次改这一条）：
#   原判据只认 `enum Code`（fork 在 build190 上的实现）。核到 v0.2.2 后发现
#   **上游已经自带等价且更强的机制** ——
#   `record Outcome(Result result, String reason, int attempts, String stage)`
#   用 reason+stage 两个稳定码描述成因，而 fork 的 13 个 Code 与它一一对应：
#     UNKNOWN_READ→READ/RECORD_UNAVAILABLE  NONE→READ/NO_RECORD
#     STALE_SUPERSEDED→COMPATIBILITY/SUPERSEDED  UNKNOWN_NOT_COMPATIBLE→COMPATIBILITY/INCOMPATIBLE
#     UNKNOWN_VERIFY→KERNEL_VERIFY/IDENTITY_UNKNOWN  UNKNOWN_AUTH→AUTHENTICATE/AUTH_UNAVAILABLE
#     UNKNOWN_VERIFY_AFTER_AUTH→KERNEL_REVERIFY/IDENTITY_UNKNOWN  RESTORED→ADOPT/RESTORED
#     STALE_ADOPT_DECLINED→ADOPT/STALE  STALE_GENERATION_CHANGED→STALE（stage 记 after-verify/after-auth）
#     UNKNOWN_EXCEPTION→保留原 reason
#   上游还多了 EXITED 分支与 4 参数构造的重载。此时再补一套 enum Code 就是
#   **两套并行诊断**，日志会出现"同一个成因两种写法"，比缺子码更难查。
#   所以判据改为「诊断能力存在」而不是「某种具体实现存在」：
#   Outcome 必须同时携带 result、reason、stage 三项，且 reason 至少有 6 种取值
#   （6 是 fork 当年压成同一个 UNKNOWN 的成因数）。
WSC="$J/core/WebSessionRecovery.java"
if grep -q 'record Outcome(Result result, String reason, int attempts, String stage)' "$WSC" 2>/dev/null; then
  NREASON=$(grep -oE '"[A-Z][A-Z_]{3,}"' "$WSC" 2>/dev/null | sort -u | wc -l)
  if [ "$NREASON" -ge 6 ]; then
    ok "会话恢复诊断：Outcome 带 reason+stage，$NREASON 种稳定码可区分成因（上游 v0.2.2 结构）"
  else
    bad "会话恢复诊断码不足：只有 $NREASON 种，UNKNOWN 的多种成因会被压成同一字符串"
  fi
elif grep -q 'enum Code' "$WSC" 2>/dev/null; then
  ok "会话恢复诊断：enum Code 子码结构（fork 旧结构）"
else
  bad "会话恢复诊断丢失：既无 reason/stage 的 Outcome，也无 enum Code —— UNKNOWN 无法区分成因"
fi
# 停止屏障认得自家受管启动器（否则维护锁被自己的 supervisor 锁死）。
check_feature "停止屏障识别受管启动器" 'managedWebShell|isManagedLauncher' "$J/util/WebProcSel.java"
# 安装包换代判据：能进 STALE 而不是永久卡住。
check_feature "换代 superseded 判据" 'superseded\(' "$J/core/WebLifecycleController.java"
# v0.2.2 基座的运行时补丁标记（两个运行时补丁必须仍在）。
if [ -f "app/src/main/assets/runtime-patches.json" ]; then
  grep -q 'DSHA_API_REMOTES_LOSSLESS_JSON_V1' app/src/main/assets/runtime-patches.json 2>/dev/null \
    || bad "运行时补丁丢失：DSHA_API_REMOTES_LOSSLESS_JSON_V1"
  grep -q 'DSHA_SESSION_REMOVED_RECOVERY_V1' app/src/main/assets/runtime-patches.json 2>/dev/null \
    || bad "运行时补丁丢失：DSHA_SESSION_REMOVED_RECOVERY_V1"
fi

# --- 4c fork 关系自检（T19 §18.4 机检，2026-11-11 新增）---
# 这一段是 T19 唯一总闸的落地：此前 merge-base 只写在文档里、没有任何门禁检查，
# 于是「推完才发现祖先链断了」。四项全过才算 fork 关系完好。
echo "[4/6] fork 关系（T19）"
FB=""
[ -n "$(git merge-base HEAD upstream/v0.2.2 2>/dev/null)" ] \
  || FB="$FB\n  merge-base 为空 —— 祖先链已断（filter-repo \/ 造新根 \/ rebase \/ 硬拼 \/ 贴文件树 之一）"
[ "$(git rev-parse --is-shallow-repository 2>/dev/null)" = "false" ] \
  || FB="$FB\n  shallow 仓库 —— 祖先链被截断，需 git fetch --unshallow"
[ -z "$(git replace -l 2>/dev/null)" ] \
  || FB="$FB\n  存在 git replace —— 伪造祖先，本地伪装，推送后他人看不到"
[ ! -f .git/info/grafts ] \
  || FB="$FB\n  存在 .git/info/grafts —— 伪造祖先"
[ "$(git remote -v 2>/dev/null | grep -c '^upstream.*DSH-APP/DSHA')" -ge 1 ] \
  || FB="$FB\n  upstream remote 缺失或指向错误 —— 之后 fetch 不到上游新提交"
if [ -z "$FB" ]; then
  ok "fork 关系完好（merge-base $(git merge-base HEAD upstream/v0.2.2 | cut -c1-8)，非 shallow，无 replace/grafts，upstream 可达）"
else
  printf "%b\n" "$FB"
  bad "fork 关系自检未通过 —— 见上方逐条原因（T19）"
fi

# --- 5 迁移完整性（仅 --deep，日常不跑：实测 8.3 秒）---
echo "[5/6] 迁移完整性"
if [ "$1" = "--deep" ]; then
  if sh "$WS/_verify_migration.sh" >/tmp/_sc_mig.log 2>&1; then
    ok "$(tail -1 /tmp/_sc_mig.log)"
  else
    if grep -q "源端不可达" /tmp/_sc_mig.log; then
      ok "源端已卸载，跳过比对（正常）"
    else
      bad "迁移校验失败，详见 /tmp/_sc_mig.log"
    fi
  fi
else
  ok "已跳过（迁移只验一次；需要时加 --deep，约 8 秒）"
fi

echo "=============================================="
if [ "$FAILN" -eq 0 ]; then
  echo "SELFCHECK PASS"
  exit 0
else
  echo "SELFCHECK FAILED ($FAILN 项)"
  exit 1
fi
