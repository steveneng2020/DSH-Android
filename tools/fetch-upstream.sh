#!/bin/sh
# fetch-upstream.sh —— 拉取上游最新代码并做只读合并预演
#
# 为什么需要它：本地 upstream/* refs 是「上一次 fetch 时的快照」，不是实时状态。
# 2026-11-11 实测发现本地停在 2026-11-10 22:36，即一天前的快照 ——
# 在这种状态下做「合并预演」等于拿旧数据演练，结论不可信。
#
# 本脚本只做三件事，全部只读，不改任何本地分支：
#   1. git fetch upstream --tags      把上游最新提交取到本地
#   2. 报告上游自上次合并以来有多少新提交、都是什么
#   3. 在临时 worktree 里做一次 merge --no-commit --no-ff 预演，报冲突面
#
# 用法（从任意目录）：
#   sh tools/fetch-upstream.sh              # fetch + 报告 + 预演
#   sh tools/fetch-upstream.sh --no-dry-run # 只 fetch + 报告，跳过预演
#
# 退出码：
#   0  正常（无论有无新提交、有无冲突 —— 冲突是信息，不是错误）
#   1  环境问题（找不到仓库、fetch 失败、upstream remote 缺失）
#
# 相关约束：CONSTRAINTS-REGISTER §12 第 18 条（T19 细则，18.7 预演方法）

set -u

SELF_DIR=$(cd "$(dirname "$0")" && pwd)
SRC=$(dirname "$SELF_DIR")
WS=$(dirname "$SRC")
cd "$SRC" || { echo "FAIL 源码目录不存在: $SRC"; exit 1; }

DRY=1
for arg in "$@"; do
  case "$arg" in
    --no-dry-run) DRY=0 ;;
    -h|--help) sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "FAIL 未知参数: $arg"; exit 1 ;;
  esac
done

# ---------- 前置检查：T19 ⑧ upstream remote 必须可达 ----------
if [ "$(git remote -v | grep -c '^upstream')" -lt 1 ]; then
  echo "FAIL upstream remote 缺失 —— 无法拉取上游（T19 ⑧）"
  echo "    修复: git remote add upstream https://github.com/DSH-APP/DSHA.git"
  exit 1
fi

# ---------- 记录 fetch 前的状态，用于对比 ----------
BEFORE=""
for ref in $(git for-each-ref --format='%(refname)' refs/remotes/upstream/ | head -50); do
  :
done
# 用已知的上游主线做对比基准；没有则回落到第一个 upstream ref
BASELINE=""
for cand in upstream/v0.2.2 upstream/main; do
  if git rev-parse --verify "$cand" >/dev/null 2>&1; then BASELINE="$cand"; break; fi
done
if [ -n "$BASELINE" ]; then
  BEFORE=$(git rev-parse "$BASELINE")
  echo "fetch 前 $BASELINE = $(git rev-parse --short "$BASELINE")"
else
  echo "fetch 前：本地没有 upstream/* ref（首次拉取）"
fi

# ---------- 1. fetch ----------
echo
echo "=== 1/3 拉取上游 ==="
#
# 绝不加 --prune：2026-11-11 实测踩过 —— --prune 会把
# upstream/v0.2.2、upstream/main 这类「指向 tag 或旧提交」的 ref 删掉，
# 因为上游已把它们从 heads 移走。ref 一没，T19 ① 的 merge-base 就报空，
# 看起来像「fork 关系断了」，实际对象还在、关系完好。
# 也就是说：--prune 会**伪造一次断亲**，把人骗去重做分支。
# 只 fetch，不 prune。
if ! git fetch upstream --tags 2>&1 | grep -v 'would clobber existing tag' | tail -20; then
  echo "FAIL git fetch upstream 失败 —— 检查网络或 remote 可达性"
  exit 1
fi

# fetch 之后若关键 ref 缺失（历史上被 prune 过），按 SHA 补回，避免后续判据误报
if ! git rev-parse --verify upstream/v0.2.2 >/dev/null 2>&1; then
  if TAG=$(git rev-parse --verify refs/tags/v0.2.2 2>/dev/null); then
    git update-ref refs/remotes/upstream/v0.2.2 "$TAG" 2>/dev/null && \
      echo "已补回 upstream/v0.2.2 -> $(echo "$TAG" | cut -c1-12)（此前被 prune 删除）"
  fi
fi
if ! git rev-parse --verify upstream/main >/dev/null 2>&1; then
  if git ls-remote --exit-code --heads upstream main >/dev/null 2>&1; then
    git fetch upstream main:refs/remotes/upstream/main >/dev/null 2>&1 && \
      echo "已补回 upstream/main"
  fi
fi

# ---------- 2. 报告上游变化 ----------
echo
echo "=== 2/3 上游变化 ==="
AFTER_REF="$BASELINE"
if [ -z "$AFTER_REF" ]; then
  for cand in upstream/v0.2.2 upstream/main; do
    if git rev-parse --verify "$cand" >/dev/null 2>&1; then AFTER_REF="$cand"; break; fi
  done
fi

if [ -n "$BASELINE" ] && [ -n "$AFTER_REF" ]; then
  AFTER=$(git rev-parse "$AFTER_REF")
  if [ "$BEFORE" = "$AFTER" ]; then
    echo "上游无新提交（$AFTER_REF 仍是 $(git rev-parse --short "$AFTER_REF")）"
  else
    N=$(git rev-list --count "$BEFORE..$AFTER" 2>/dev/null || echo "?")
    echo "上游有新提交：$N 个（$(git rev-parse --short "$BEFORE") -> $(git rev-parse --short "$AFTER")）"
    echo "--- 最近 15 条 ---"
    git log --oneline --no-decorate -15 "$BEFORE..$AFTER" 2>/dev/null
  fi
else
  echo "无法对比（首次拉取或基线缺失）；当前上游 refs："
  git for-each-ref --format='  %(refname:short)  %(objectname:short)' refs/remotes/upstream/ | head -10
fi

# 上游 main 通常领先最新的发布 tag（CI / 文档类提交）。分别报出来，
# 免得只盯 v0.2.2 而漏掉 main 上的东西。
if git rev-parse --verify upstream/main >/dev/null 2>&1 && \
   git rev-parse --verify upstream/v0.2.2 >/dev/null 2>&1; then
  MAIN_AHEAD=$(git rev-list --count upstream/v0.2.2..upstream/main 2>/dev/null || echo 0)
  if [ "$MAIN_AHEAD" != "0" ]; then
    echo
    echo "注意：upstream/main 比 upstream/v0.2.2 多 $MAIN_AHEAD 个提交 ——"
    echo "      这些是 v0.2.2 之后的提交（多为 CI / 文档）。要不要跟，由你判断："
    git log --oneline --no-decorate -10 upstream/v0.2.2..upstream/main 2>/dev/null | sed 's/^/        /'
    echo "      跟的话：git merge upstream/main（同样走 T19，禁用 filter-repo / rebase / 硬拼）"
  fi
fi

# ---------- 3. 只读合并预演 ----------
echo
if [ "$DRY" = "0" ]; then
  echo "=== 3/3 已按 --no-dry-run 跳过预演 ==="
  exit 0
fi

echo "=== 3/3 只读合并预演（不提交、不改分支）==="

# T19 ①：总闸必须先过，否则预演没有意义
BASE=$(git merge-base HEAD "$AFTER_REF" 2>/dev/null)
if [ -z "$BASE" ]; then
  echo "FAIL merge-base 为空 —— 祖先链已断，预演无意义（T19 ①）"
  echo "    先查 D1~D7 哪一种：filter-repo / 造新根 / rebase / 硬拼 / 贴文件树 / graft / shallow"
  exit 1
fi
echo "merge-base = $(echo "$BASE" | cut -c1-12)"

WT=/tmp/dsha-upstream-dryrun
rm -rf "$WT"
if ! git worktree add --detach "$WT" HEAD >/dev/null 2>&1; then
  echo "FAIL 无法创建临时 worktree: $WT"
  exit 1
fi

CONFLICTS=0
(
  cd "$WT" || exit 1
  git merge --no-commit --no-ff "$AFTER_REF" >/tmp/dsha-dryrun.log 2>&1
  echo "--- merge 输出（前 12 行）---"
  head -12 /tmp/dsha-dryrun.log
  echo "--- 冲突文件 ---"
  CF=$(git diff --name-only --diff-filter=U 2>/dev/null)
  if [ -z "$CF" ]; then
    echo "（无冲突，自动合并成功）"
  else
    echo "$CF" | head -40
    echo "冲突文件数：$(echo "$CF" | wc -l)"
  fi
  git merge --abort >/dev/null 2>&1
)
git worktree remove --force "$WT" >/dev/null 2>&1

echo
echo "=== 提示 ==="
echo "冲突里的生成物（raw*/changelog.md、values*/ui_strings.xml、runtime-descriptor.json 等）"
echo "重跑对应脚本即可，不需手合 —— 见 CONSTRAINTS-REGISTER §12 18.6 生成物豁免清单。"
echo "真正的合并请走: git merge $AFTER_REF   （不要用 filter-repo / rebase / 硬拼，见 T19）"
