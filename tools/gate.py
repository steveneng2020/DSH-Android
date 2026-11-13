#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DSHA on Eta 交接门禁（对应 WorkBuddy 参考例子的四门禁，按本项目实际精简为三道）

参考例子有 4 个门禁，但那是为 smali 工程 + GitHub 远端定制的：
  check_doc_remote        -> DSHA 侧 origin 不可推（§8.3），无远端可比，去掉
  check_handoff_uniqueness-> 保留（基线 vs HEAD 漂移）
  check_doc_numbers       -> 保留（文档数字 vs 仓库源头）
  check_doc_consistency   -> 保留（跨文档同一事实）

用法：
    cd "/storage/emulated/0/Download/Eta/DSHA开发/DSHA-src"
    export PATH="/opt/dsha-env/jdk17/bin:$PATH"
    python3 ../_gate.py

退出码 0 = GATE PASS；非 0 = 有 FAIL。
"""
import os
import pathlib
import re
import subprocess
import sys

# 2026-11-11：本文件已从「仓库外」移入 DSHA-src/tools/（C4 修复），
# 路径改为按脚本自身位置推导，不再硬编码绝对路径 —— 硬编码会让换设备/换工作区即失效，
# 那是 C4 的另一半问题。
#   tools/gate.py -> 上一层是 DSHA-src，再上一层是工作区根（含 docs/）
SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WS = os.path.dirname(SRC)
DOC = os.path.join(WS, "docs", "交接规程.md")
DS = os.path.join(WS, "docs", "DATA-SOURCES.md")

fails = []
warns = []


DEEP = "--deep" in sys.argv   # 体积类检查很慢（du 扫 21 GB），默认跳过

_cache = {}


def run(cmd, cwd=SRC):
    """带缓存的命令执行：同一命令一次运行内只跑一次。"""
    key = (cmd, cwd)
    if key in _cache:
        return _cache[key]
    try:
        out = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=120
        ).stdout.strip()
    except Exception:
        out = ""
    _cache[key] = out
    return out


def read(p):
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        fails.append("文件不存在: %s" % p)
        return ""


# ---------------------------------------------------------------- 门禁 1：数字
def gate_numbers():
    """文档里出现的数字必须与仓库真实值一致。"""
    print("[1/7] check_doc_numbers  文档数字 vs 仓库源头")
    if not os.path.exists(DOC):
        fails.append("G1 交接规程.md 不存在")
        return
    doc = read(DOC)

    truth = {
        "HEAD": run("git rev-parse --short HEAD"),
        "branch": run("git branch --show-current"),
        "changes": run("git status --short | wc -l"),
        "java": run("find app/src -name '*.java' | wc -l"),
        "gradle_home": run("du -sm /opt/dsha-env/gradle-home | cut -f1") if DEEP else "skip",
        "deps_count": run("ls deps | wc -l"),
        "docs_md": run("ls -1 %s/docs/*.md 2>/dev/null | wc -l" % WS),
    }
    apk = os.path.join(SRC, "app/build/outputs/apk/low/debug/app-low-debug.apk")
    truth["apk_bytes"] = str(os.path.getsize(apk)) if os.path.exists(apk) else "0"

    checks = [
        ("HEAD", r"\b" + re.escape(truth["HEAD"]) + r"\b", "HEAD %s" % truth["HEAD"]),
        ("branch", r"`?" + re.escape(truth["branch"]) + r"`?", "分支 %s" % truth["branch"]),
        ("changes", r"实测\s*" + truth["changes"] + r"\s*处", "改动 %s 处" % truth["changes"]),
        ("docs_md", r"顶层\s*" + truth["docs_md"] + r"\s*个", "docs 顶层 %s 个" % truth["docs_md"]),
    ]
    for name, pat, label in checks:
        if not re.search(pat, doc):
            warns.append("G1 文档未见预期值：%s" % label)

    # 反例：文档里不该出现的旧错值
    stale = {
        r"docs/`\s*29\s*个": "docs/ 29 个（旧错值，应为 25）",
        r"工作区\s*28\s*处改动": "28 处改动（旧错值，应为 17）",
        r"1402\s*MB": "1402 MB（旧错值，应为 1349）",
        r"（42 项，39 MB": "deps 42 项 39 MB（旧错值，应为 45 项 40 MB）",
    }
    for pat, desc in stale.items():
        if re.search(pat, doc):
            fails.append("G1 文档残留旧错值：%s" % desc)

    print("    真值: HEAD=%s branch=%s changes=%s java=%s gradle_home=%sMB deps=%s docs_md=%s"
          % (truth["HEAD"], truth["branch"], truth["changes"], truth["java"],
             truth["gradle_home"], truth["deps_count"], truth["docs_md"]))


# ------------------------------------------------------------ 门禁 2：基线漂移
def gate_baseline():
    """交接文档头部的基线不能落后 HEAD 太多，否则新会话拿着旧基线开工。"""
    print("[2/7] check_handoff_uniqueness  基线 vs HEAD 漂移")
    head = run("git rev-parse --short HEAD")
    try:
        n = int(run("git rev-list --count %s..HEAD" % head) or 0)
    except ValueError:
        n = 0
    doc = read(DOC)
    m = re.search(r"基线提交：`([0-9a-f]{7,40})`", doc)
    if not m:
        fails.append("G2 交接规程.md 头部找不到「基线提交：`xxxxxxxx`」")
        return
    base = m.group(1)
    if len(base) == 40:
        base = base[:8]
    drift = run("git rev-list --count %s..HEAD" % base)
    try:
        drift = int(drift or 0)
    except ValueError:
        drift = -1
    if drift < 0:
        fails.append("G2 文档基线 %s 在仓库里不存在（历史被改写？）" % base)
        return
    if drift > 5:
        fails.append("G2 文档基线 %s 落后 HEAD %s 共 %d 个提交（容差 5）"
                     % (base, head, drift))
    else:
        print("    基线 %s -> HEAD %s，落后 %d（<=5 允许）" % (base, head, drift))


# ---------------------------------------------------------- 门禁 3：跨文档一致
def gate_consistency():
    """同一事实在不同文档里必须一致；DATA-SOURCES 登记的值要与实际采集相符。"""
    print("[3/7] check_doc_consistency  跨文档同一事实")
    doc = read(DOC)
    ds = read(DS)
    if not ds:
        return

    # 3.1 两份文档写的 APK 字节数必须一致（忽略千分位写法差异）
    def apk_bytes_in(text):
        raw = re.findall(r"50[59],?95[0-9],?[0-9]{3}", text)
        return {r.replace(",", "") for r in raw}

    a = apk_bytes_in(doc)
    b = apk_bytes_in(ds)
    if a and b and a != b:
        fails.append("G3 两份文档的 APK 字节数不一致: %s vs %s" % (a, b))
    if not a:
        warns.append("G3 交接规程.md 未写 APK 字节数（F-04）")

    # 3.2 17 处改动必须在两处一致
    for name, text in (("交接规程", doc), ("DATA-SOURCES", ds)):
        m = re.search(r"工作区改动数.*?`(\d+)`|实测\s*(\d+)\s*处", text)
        if m:
            v = m.group(1) or m.group(2)
            real = run("git status --short | wc -l")
            if v != real:
                fails.append("G3 %s 写改动 %s 处，实际 %s" % (name, v, real))

    # 3.3 1,048,576 硬限制只能在一处主写，另一处只许引用
    if "1,048,576" in doc and "1,048,576" not in ds:
        print("    OK: 1,048,576 只在交接规程 §8.6 主写（符合单一主写）")
    if ds.count("1,048,576") > 1:
        warns.append("G3 DATA-SOURCES 多处出现 1,048,576，应只做引用")

    # 3.4 DATA-SOURCES 自己登记的真值不能过期（数据源漂移是最隐蔽的错）
    ds_checks = [
        ("F-01", r"F-01.*?`([0-9a-f]{7,40})`", run("git rev-parse --short HEAD")),
        ("F-03", r"F-03.*?`(\d+)`", run("git status --short | wc -l")),
        ("F-07", r"F-07.*?`(\d+)`", run("find app/src -name '*.java' | wc -l")),
        ("F-08", r"F-08.*?`(\d+)`", run("find app/src -type f | grep -v /build/ | wc -l")),
        ("F-09", r"F-09.*?`(\d+)` MB", run("du -sm /opt/dsha-env/gradle-home | cut -f1") if DEEP else None),
        ("F-10", r"F-10.*?`(\d+)` 项", run("ls deps | wc -l")),
        ("F-11", r"F-11.*?`(\d+)`", run("find .git/objects -type f | wc -l")),
        ("F-12", r"F-12.*?`(\d+)`", run("ls -1 %s/docs/*.md 2>/dev/null | wc -l" % WS)),
    ]
    for fid, pat, real in ds_checks:
        m = re.search(pat, ds, re.S)
        if not m:
            warns.append("G3 DATA-SOURCES 找不到 %s 的真值行" % fid)
            continue
        if real and m.group(1) != real.strip():
            fails.append("G3 DATA-SOURCES 的 %s 登记为 %s，实测 %s（数据源漂移）"
                         % (fid, m.group(1), real.strip()))


def gate_entry_chain():
    """入口链完整性：START2.md -> HANDOFF-新会话.md -> 交接规程.md

    同时检查与另一盒项目（WorkBuddy2API，START1.md）不冲突。
    为什么要查：第一版只写了交接规程，漏了入口文件，用户直接问
    「怎么没看见类似 START 文件」；后来又发现两盒项目都叫 START 会读错。
    这种结构性遗漏必须由门禁拦。
    """
    print("[4/7] check_entry_chain  入口链 START2 -> HANDOFF -> 规程")
    start2 = os.path.join(WS, "START2.md")
    handoff = os.path.join(WS, "docs", "HANDOFF-新会话.md")
    wb_start1 = "/storage/emulated/0/Download/Eta/WorkBuddy2API开发/P0-work-rc8/START1.md"
    PKG = "dsh.android.dev"
    OTHER_PKG = "com.workbuddy2api.dev"

    # START2.md 必须存在，且自报项目名与包名，且要求先确认
    if not os.path.exists(start2):
        fails.append("G4 缺 START2.md（工作区根）—— 新会话没有入口")
    else:
        txt = read(start2)
        if "DSHA" not in txt:
            fails.append("G4 START2.md 没有自报项目名 DSHA")
        if PKG not in txt:
            fails.append("G4 START2.md 没有写包名 %s" % PKG)
        if OTHER_PKG in txt and "START1" not in txt:
            fails.append("G4 START2.md 提到另一项目却没说 START1")
        if "确认" not in txt:
            fails.append("G4 START2.md 缺少「先报项目名等用户确认」的指令")

        # 关键：START2 里写的每个绝对路径必须真实存在。
        # 实测踩过三次：
        #   1) 写过 /docs/emulated/... 这种不存在的路径
        #   2) 正则只认 /storage/ 开头，漏掉 /docs/ 开头
        #   3) 排除反引号当边界，结果 markdown 里 `path` 全被跳过，等于没查
        # 现在：不设前缀白名单，也不排除反引号，取所有 / 开头的连续 token 再验。
        for m in re.finditer(r"/[A-Za-z\u4e00-\u9fff][\w./\-\u4e00-\u9fff]*", txt):
            p = m.group(0).rstrip("。，、：:），)")
            if p.endswith(".md") and not p.endswith(".md"):
                pass
            if os.path.exists(p):
                continue
            if "..." in p or p.endswith("/"):
                continue          # 省略写法（/storage/...）不是真路径
            parts = p.strip("/").split("/")
            if len(parts) < 2:
                continue                      # 太短，不像真路径
            if "." not in parts[-1] and len(parts) < 3:
                continue                      # `/docs/emulated` 这种可能是泛写
            probe, ok_parent = p, False
            while "/" in probe[1:]:
                probe = probe.rsplit("/", 1)[0]
                if os.path.exists(probe):
                    ok_parent = True
                    break
            if not ok_parent:
                fails.append("G4 START2.md 路径整条不存在：%s" % p)
            elif "." in parts[-1]:
                fails.append("G4 START2.md 文件不存在：%s" % p)

        # 必须指向 HANDOFF（允许写目录 + 文件名两段的形式）
        if "HANDOFF-新会话.md" not in txt:
            fails.append("G4 START2.md 没有指向 HANDOFF-新会话.md")
        elif not os.path.exists(handoff):
            fails.append("G4 START2 指向的 HANDOFF 不存在：%s" % handoff)

        # 尺寸：入口必须短。超了说明又把正文塞进入口了
        sz = os.path.getsize(start2)
        if sz > 2600:
            warns.append("G4 START2.md 已 %d B，超过 2600 —— 入口该保持精简" % sz)

        # 一致性：START2 说「不要跑构建」，HANDOFF §7 却要求跑 env_check/gate
        # 实测踩过：助手读完 HANDOFF 就照着跑 _env_check.sh，而 START2 写着
        # 「不要跑构建、不要验证环境」，两份文档互相矛盾，助手只能自己猜。
        handoff_txt = read(handoff)
        # 【关键】START2 的唯一职责是「报项目名等确认」，不许夹带任何执行内容。
        # 历史教训（2026-11-09 21:28）：为了让「重复发同样指令」能继续，加过
        # 「又发一次 = 视为确认」规则，结果助手看到用户发「读 START2.md」就判定
        # 「这是重复发送」，直接跳过报项目名 —— **把设计的初衷彻底破坏**。
        # 现在反向检查：出现「视为确认 / 自检 / 跑命令 / 第 2 步」即 FAIL。
        forbidden = {
            "视为确认": "会跳过报项目名（实测已破坏设计）",
            "又发一次": "同上，等于允许跳过确认",
            "_selfcheck.sh": "START2 不该让助手跑命令，自检在 HANDOFF 里",
            "第 2 步": "说明 START2 又变成了流程手册，它只该有一步",
            "不要跑构建": "同类矛盾源头，已全部移到 HANDOFF",
        }
        for word, why in forbidden.items():
            if word in txt:
                fails.append("G4 START2.md 含「%s」—— %s。"
                             "START2 只做一件事：报项目名等确认" % (word, why))

        # 【关键】报项目名那个代码块必须窄，否则手机上被横向截断，
        # 用户看不到完整路径，「核对」就失效了。
        # 实测：`目录：/storage/emulated/0/Download/Eta/DSHA开发` 40 字符 → 被截成 `/…/Eta/DSHA;`
        first_block = re.search(r"```\n(.*?)```", txt, re.S)
        if first_block:
            for ln in first_block.group(1).splitlines():
                if len(ln) > 28:
                    fails.append("G4 START2 报项目名的代码块里有一行 %d 字符"
                                 "（上限 28），手机上会被截断：%r" % (len(ln), ln[:40]))

        # 必须明确「无论第几次都先报」，否则助手会自己推测
        if not re.search(r"无论.{0,6}第几?次", txt):
            fails.append("G4 START2.md 没写「无论第几次都先报项目名」—— "
                         "助手会自行判断「重复发送 = 继续」而跳过确认")

    # 另一盒项目也要在，否则 START1/START2 编号失去意义
    if not os.path.exists(wb_start1):
        warns.append("G4 另一盒项目的 %s 不存在，START1/START2 编号可能已过时" % wb_start1)
    else:
        w = read(wb_start1)
        if OTHER_PKG not in w:
            fails.append("G4 START1.md 没有写它自己的包名 %s" % OTHER_PKG)
        if PKG in w and "START2" not in w:
            warns.append("G4 START1.md 提到了 %s 却没说 START2" % PKG)

    # HANDOFF 必须存在、九段完整、且用 START2 作开场
    if not os.path.exists(handoff):
        fails.append("G4 缺 docs/HANDOFF-新会话.md")
    else:
        h = read(handoff)
        if "交接规程" not in h:
            fails.append("G4 HANDOFF 没有引用 交接规程")
        if "读 START2" not in h:
            fails.append("G4 HANDOFF 没有提到「读 START2」开场指令")
        # 结构按「要素」查，不写死编号 —— 段数可以演进（原九段已压成八段）
        required_topics = {
            "铁律": r"##\s*\d+\.\s*.*铁律",
            "项目坐标": r"##\s*\d+\.\s*.*坐标",
            "环境": r"##\s*\d+\.\s*.*环境",
            "固定动作": r"##\s*\d+\.\s*.*固定动作",
            "当前状态": r"##\s*\d+\.\s*.*状态",
            "必读顺序": r"##\s*\d+\.\s*.*必读",
            "开工自检": r"##\s*\d+\.\s*.*自检",
        }
        for name, pat in required_topics.items():
            if not re.search(pat, h):
                fails.append("G4 HANDOFF 缺少必需章节：「%s」" % name)

    # 文档里不许再引导「读交接规程全文」，也不许只写无编号的「读 START」
    doc = read(DOC)
    if re.search(r"读\s*/storage/\S*交接规程\.md\s*全文", doc):
        fails.append("G4 交接规程仍在引导「读交接规程全文」——应指向 START2")

    def bad_start(text):
        """找无编号的「读 START」，但排除描述门禁本身的语境。

        排除条件：同一行里带引号『』或出现在表格的「抓什么类型的问题」列里。
        实测踩过：门禁说明表里写「无编号的『读 START』」被判成真实指令。
        """
        hits = []
        for i, line in enumerate(text.splitlines(), 1):
            if not re.search(r"读\s+START(?!\d)", line):
                continue
            if "「读 START」" in line or "『读 START』" in line:
                continue          # 是在描述这个问题本身
            hits.append(i)
        return hits

    for name, txt in (("交接规程", doc), ("HANDOFF", read(os.path.join(WS, "docs", "HANDOFF-新会话.md")))):
        hits = bad_start(txt)
        if hits:
            fails.append("G4 %s 第 %s 行存在无编号的「读 START」——"
                         "两盒项目并存会读错，必须写 START1/START2"
                         % (name, ",".join(map(str, hits[:5]))))

    if not fails:
        print("    START2.md(%dB) -> HANDOFF-新会话.md -> 交接规程.md  链路完整"
              % (os.path.getsize(start2) if os.path.exists(start2) else 0))
        if os.path.exists(wb_start1):
            print("    START1.md(WorkBuddy2API/%s) 与 START2.md(DSHA/%s) 编号互不冲突"
                  % (OTHER_PKG, PKG))


def gate_env_integrity():
    """环境完整性：git 配置是否真的指向存在的路径、FUSE 限制是否已被记录、体积数字是否与实测一致。

    为什么要查：2026-11-09 复测发现
      - core.hooksPath 仍指向不存在的 /root/work/... （文档说已改，其实没改）
      - /storage 是 FUSE，不支持可执行位，钩子永远生效不了（文档完全没提）
      - DSHA-src 体积文档写 ~5,000MB，实测 2,971MB
    这些都是「能算出来但没人算」的事实，必须进自动门禁。
    """
    print("[5/7] check_env_integrity  git 配置 / FUSE 限制 / 体积一致性")

    # 5.1 core.hooksPath 必须指向真实存在、且位于可执行文件系统上的目录
    hp = run("git config core.hooksPath")
    doc_all = read(DOC) + read(os.path.join(WS, "docs", "HANDOFF-新会话.md"))
    if not hp:
        warns.append("G5 未设置 core.hooksPath（钩子不生效）")
    else:
        target = hp if os.path.isabs(hp) else os.path.join(SRC, hp)
        if not os.path.isdir(target):
            fails.append("G5 core.hooksPath=%s 指向的目录不存在 —— 钩子会静默失效" % hp)
        else:
            # 目录存在还不够：必须确认钩子「真能被 git 执行」
            try:
                probe = subprocess.run(
                    "git hook run pre-commit </dev/null 2>&1",
                    shell=True, cwd=SRC, capture_output=True, text=True, timeout=20
                ).stdout
            except subprocess.TimeoutExpired:
                probe = "timeout"
            if "not set as executable" in probe or "cannot find a hook" in probe:
                fails.append(
                    "G5 core.hooksPath=%s 的钩子**无法执行**（%s）—— "
                    "/storage 挂载带 noexec 且丢弃执行位，应指到 /data/local/tmp/dsha-git-hooks"
                    % (hp, probe.strip().splitlines()[0] if probe.strip() else "未知"))

    # 5.2 /storage 是 noexec + FUSE 丢弃执行位，文档必须写明这个限制
    fs_type = run("stat -f -c %%T %s" % SRC)
    mount_line = run("grep ' /storage/emulated ' /proc/mounts 2>/dev/null")
    is_noexec = "noexec" in mount_line
    if "fuse" in fs_type.lower() or is_noexec:
        if "noexec" not in doc_all:
            fails.append("G5 /storage 挂载带 noexec（FUSE 丢弃执行位），"
                         "但文档没写 —— 新会话会用 ./script.sh 然后 Permission denied")
        if "sh .git-hooks/pre-commit" not in doc_all:
            warns.append("G5 文档没给钩子失效时的兜底跑法（sh .git-hooks/pre-commit）")

    # 5.3 文档里的 DSHA-src 体积必须与实测一致（容差 10%）—— 仅 --deep 时测
    m = re.search(r"`DSHA-src`\s*\|\s*([\d,]+)\s*MB", doc_all) if DEEP else None
    if not DEEP and re.search(r"`DSHA-src`\s*\|\s*[\d,]+\s*MB", doc_all):
        print("    体积检查已跳过（用 --deep 启用，省 ~5 秒）")
    if m:
        claimed = int(m.group(1).replace(",", ""))
        real = run("du -sm %s | cut -f1" % SRC)
        try:
            real = int(real)
        except ValueError:
            real = 0
        if real and abs(claimed - real) > real * 0.10:
            fails.append("G5 文档写 DSHA-src %d MB，实测 %d MB（偏差 %d%%）"
                         % (claimed, real, abs(claimed - real) * 100 // real))
        elif real:
            print("    DSHA-src 体积 %d MB（文档 %d MB，容差内）" % (real, claimed))
    elif DEEP:
        warns.append("G5 文档未见 DSHA-src 体积数字")


def gate_doc_freshness():
    """文档新鲜度：三份交接文档的时间戳/基线必须同步。

    对照 WorkBuddy 的 check_doc_freshness.py。为什么要查：
    2026-11-09 实测发现 MEMORY.md 写 19:20、HANDOFF 写 18:30、DATA-SOURCES 写 18:30，
    三份文档自称的「最后刷新」各不相同 —— 说明有一份没跟着更新。
    新会话看到三个时间会不知道该信哪个，等于没有时间戳。
    """
    print("[6/7] check_doc_freshness  三份文档的时间戳/基线同步")
    files = {
        "HANDOFF": os.path.join(WS, "docs", "HANDOFF-新会话.md"),
        "MEMORY": os.path.join(WS, "MEMORY.md"),
        "规程": os.path.join(WS, "docs", "交接规程.md"),
        "DATA": os.path.join(WS, "docs", "DATA-SOURCES.md"),
    }
    pats = {
        "HANDOFF": r"生成时间：(\d{4}-\d{2}-\d{2})[ 　]*(\d{2}:\d{2})",
        "MEMORY": r"最后刷新\s*(\d{4}-\d{2}-\d{2})[ 　]*(\d{2}:\d{2})",
        "规程": r"最后核验：(\d{4}-\d{2}-\d{2})[ 　]*(\d{2}:\d{2})",
        "DATA": r"\| 2026-(\d{2})-(\d{2}) (\d{2}:\d{2}) \|",
    }
    seen = {}
    for name, path in files.items():
        if not os.path.exists(path):
            if name == "MEMORY":
                fails.append("G6 缺 MEMORY.md（跨会话事实载体）")
            else:
                warns.append("G6 缺 %s" % path)
            continue
        txt = read(path)
        if name == "DATA":
            m = re.search(pats[name], txt)
            stamp = ("2026-" + m.group(1) + "-" + m.group(2) + " " + m.group(3)) if m else None
        else:
            m = re.search(pats[name], txt)
            stamp = (m.group(1) + " " + m.group(2)) if m else None
        if not stamp:
            warns.append("G6 %s 找不到时间戳（正则 %s）" % (name, pats[name]))
        else:
            seen[name] = stamp

    if len(set(seen.values())) > 1:
        fails.append("G6 三份文档时间戳不同步：%s —— "
                     "说明有一份没跟着更新，新会话不知道信哪个"
                     % "，".join("%s=%s" % (k, v) for k, v in sorted(seen.items())))
    elif seen:
        print("    时间戳一致：%s" % list(seen.values())[0])

    # 基线提交必须在 HANDOFF / MEMORY / 规程 三处一致
    heads = {}
    for name in ("HANDOFF", "MEMORY", "规程"):
        txt = read(files[name])
        # 2026-11-11 修：原正则只在全文抓「第一个反引号包裹的 7~40 位十六进制」，
        # 于是 HANDOFF 里 OCR 例子的日期 20261110 被当成基线（实测 FAIL：
        # "HANDOFF 的基线 20261110 与 HEAD 不符"）—— 那是正文里的一个日期，
        # 不是基线。判据必须锚在「基线 / HEAD」这些词上，不能全文瞎抓。
        m = re.search('(?:HEAD|基线提交|基线)[^\\n]{0,12}?`(\\b[0-9a-f]{7,40}\\b)`', txt)
        if m:
            heads[name] = m.group(1)
    real = run("git rev-parse --short HEAD")
    for name, h in heads.items():
        if not real.startswith(h) and not h.startswith(real):
            fails.append("G6 %s 的基线 %s 与 HEAD %s 不一致" % (name, h, real))


def gate_fork_topology():
    """G9 fork 拓扑体检（T19 §12 18.10 第②项的落地）。

    为什么要有这一道：`_selfcheck.sh` 的 `[4/6]` 段只在**开工时**跑，
    而破坏拓扑的动作往往发生在「开发完、准备推送」之间。`_gate.py` 是交付前
    必跑的最后一道，把同一组判据再放一遍，才能覆盖那段窗口。

    与 `[4/6]` 的分工：那段查**当下状态**，这里额外查**历史上有没有做过**——
    reflog 里出现 filter-repo / rebase 改写上游祖先、分支里有多个无父根，
    这些是「已经发生过」的证据，光看当前 merge-base 是看不出来的
    （当事人可以事后 graft 或重新接一个假父）。
    """
    problems = []

    def sh(args, cwd=SRC):
        try:
            r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=60)
            return (r.stdout or "").strip(), r.returncode
        except Exception:
            return "", 1

    if not os.path.isdir(os.path.join(SRC, ".git")):
        fails.append("G9 找不到 .git，无法检查 fork 拓扑")
        return

    # ① 总闸：merge-base 必须非空
    base, rc = sh(["git", "merge-base", "HEAD", "upstream/v0.2.2"])
    if rc != 0 or not base:
        problems.append("merge-base 为空 —— 祖先链已断（D1 filter-repo / D2 造新根 / "
                        "D3 rebase / D4 硬拼 / D5 贴文件树）")

    # ② 不得是 shallow（D7）
    shallow, _ = sh(["git", "rev-parse", "--is-shallow-repository"])
    if shallow != "false":
        problems.append("shallow 仓库 —— 祖先链被截断，需 git fetch --unshallow")

    # ③ 不得有 replace / grafts 伪造祖先（D6）
    rep, _ = sh(["git", "replace", "-l"])
    if rep:
        problems.append("存在 git replace（%d 条）—— 伪造祖先，推送后他人看不到"
                        % len(rep.splitlines()))
    if os.path.isfile(os.path.join(SRC, ".git", "info", "grafts")):
        problems.append("存在 .git/info/grafts —— 伪造祖先")

    # ④ upstream remote 必须可达（T19 ⑧）
    remotes, _ = sh(["git", "remote", "-v"])
    if len([l for l in remotes.splitlines() if l.startswith("upstream")]) < 1:
        problems.append("upstream remote 缺失 —— 之后 fetch 不到上游新提交")

    # ④b ref 丢失的真假判断（2026-11-11 新增）
    #
    # 踩过的坑：tools/fetch-upstream.sh 第一版加了 `git fetch --prune`，
    # 结果把 upstream/v0.2.2、upstream/main 两个 ref 删了（上游已从 heads 移走它们）。
    # ref 一没，merge-base 报空，**看起来就像 fork 关系断了** —— 足以把人骗去重建分支。
    # 而实际对象都在，用 SHA 仍能算出 merge-base。
    #
    # 所以「merge-base 为空」不能直接判「断亲」，必须先分清是哪种：
    #   对象在 -> 只是 ref 丢了，可补回，关系完好
    #   对象不在 -> 真断了
    up_sha, rc_sha = sh(["git", "rev-parse", "upstream/v0.2.2"])
    if rc_sha != 0 or not up_sha:
        # ref 缺失，尝试用 tag 兜底判断对象是否还在
        tag_sha, rc_tag = sh(["git", "rev-parse", "refs/tags/v0.2.2"])
        if rc_tag == 0 and tag_sha:
            obj, rc_obj = sh(["git", "cat-file", "-t", tag_sha])
            if rc_obj == 0 and obj.strip() == "commit":
                problems.append(
                    "upstream/v0.2.2 ref 缺失，但对象 %s 仍在 —— "
                    "这是 ref 被 --prune 误删（**假断亲**），关系完好。"
                    "修复: git update-ref refs/remotes/upstream/v0.2.2 %s"
                    % (tag_sha[:12], tag_sha))
            else:
                problems.append("upstream/v0.2.2 缺失且对象不存在 —— 真断亲或未 fetch")
        else:
            problems.append("upstream/v0.2.2 ref 与 tag 都缺失 —— 先跑 tools/fetch-upstream.sh")

    # ④c 禁止在 fetch 时用 --prune（会制造假断亲）
    #     检查手段：仓库存不存在被 prune 过的痕迹 —— 有 upstream ref 数明显少于上游
    #     实际 heads+tags 数时，说明曾被 prune。此处只做提醒，不阻断（可能是正常清理）。
    up_refs, _ = sh(["git", "for-each-ref", "--format=%(refname)", "refs/remotes/upstream/"])
    n_up_refs = len([l for l in up_refs.splitlines() if l.strip()])
    if n_up_refs == 0:
        problems.append("refs/remotes/upstream/ 下无任何 ref —— "
                        "要么没 fetch，要么被 --prune 清空（假断亲）")

    # ⑤ 历史上不得有改写痕迹：reflog 里出现 filter-repo / rebase 到上游祖先
    #    这是「光看当前状态看不出来」的那一类：事后 graft 一下，merge-base 会「看起来」正常
    reflog, _ = sh(["git", "reflog", "--all", "--date=iso"])
    bad_reflog = [l for l in reflog.splitlines()
                  if "filter-repo" in l or "filter_repo" in l]
    if bad_reflog:
        problems.append("reflog 里有 filter-repo 痕迹 %d 条 —— "
                        "历史已被重写，当前 merge-base 可能靠 graft 伪装" % len(bad_reflog))

    # ⑥ 只允许一个无父根：多个根 = 有人塞进过无关历史
    roots, rc = sh(["git", "rev-list", "--max-parents=0", "HEAD"])
    if rc == 0:
        n_roots = len([l for l in roots.splitlines() if l.strip()])
        if n_roots > 2:
            # 上游本身可能有多根（历史迁移），这里只在明显异常时报
            problems.append("HEAD 有 %d 个无父根 —— 疑似混入无关历史" % n_roots)

    # ⑥b T20：声明类产物必须与 fork 版对齐（2026-11-11 真机验收暴露）
    man = os.path.join(SRC, 'app/src/main/AndroidManifest.xml')
    if os.path.exists(man):
        mt = open(man, encoding='utf-8').read()
        # a) 必须恰好 6 个图标 alias（LauncherDefault/Moyu/Tianqing/Zheshi/Biyu/Zishou）
        n_alias = mt.count('<activity-alias')
        # 准确数量是 6（六套图标各一个）。此前写成 13 是误读：
        # 当时用 grep -A3 activity-alias | grep 数的是匹配行而非 alias 块。n_alias = mt.count('<activity-alias')
        if n_alias != 6:
            problems.append(
                'T20② activity-alias 数量为 %d，期望 6 —— '
                '六套图标切换会静默失效（apply() 抛异常被 catch 吞掉，用户看到切换成功实际没变）'
                % n_alias)
        # b) MainActivity 不得再声明 LAUNCHER（否则两个桌面图标）
        #   定位 MainActivity 自己的 <activity> 块：从 android:name=".ui.MainActivity"
        #   往前找到最近的 <activity，往后找到最近的 </activity>，只在这段内判定。
        #   2026-11-11 修：原实现从 find(".ui.MainActivity") 直接吃到第一个 </activity>，
        #   会把紧随其后的 activity-alias 里的 LAUNCHER 扫进来，造成假红。
        _i = mt.find('.ui.MainActivity')
        seg = ''
        if _i >= 0:
            _s = mt.rfind('<activity', 0, _i)
            _e = mt.find('</activity>', _i)
            seg = mt[_s:_e] if _s >= 0 and _e > _i else ''
        _main_has_launcher = ('CATEGORY_LAUNCHER' in seg or 'category.LAUNCHER' in seg)
        if _main_has_launcher:
            problems.append(
                'T20② MainActivity 仍声明 LAUNCHER —— 桌面会出现两个图标；'
                '桌面入口必须完全交给 activity-alias')
        # c) 三个 fork Activity 必须注册
        for act in ('OnboardingPrepareActivity', 'SkillsActivity', 'WelcomeActivity'):
            if act not in mt:
                problems.append('T20① Manifest 缺少 %s 声明' % act)
        # d) IconSwitcher.restoreIfNeeded 必须被 DshaApp 调用
        app = os.path.join(SRC, 'app/src/main/java/com/deepseekharness/app/DshaApp.java')
        if os.path.exists(app):
            if 'restoreIfNeeded' not in open(app, encoding='utf-8').read():
                problems.append(
                    'T20③ DshaApp.onCreate 未调用 IconSwitcher.restoreIfNeeded() —— '
                    '覆盖安装后图标选择会被重置且无提示')
        print('    T20: alias=%d, MainActivity-有LAUNCHER=%s'
              % (n_alias, _main_has_launcher))

    # ⑥c T20⑥：包级 icon 与 alias 级 icon 不同步的检查（2026-11-11 新增）
    #
    # 场景：<application android:icon> 是包级、固定默认；六套配色是 <activity-alias android:icon>。
    # 切 alias 不改包级 icon，于是凡系统按包级取图的地方（Toast / 通知 / 任务快照）永远显示默认。
    # 判据：与配色相关的 Toast 不得用 Toast.makeText（它会自动套包级 icon）。
    if os.path.exists(man):
        pkg_icon = ''
        for line in mt.splitlines():
            if 'android:icon=' in line and 'activity-alias' not in line:
                _m2 = re.search(r'android:icon="([^"]+)"', line)
                if _m2:
                    pkg_icon = _m2.group(1)
                    break
        sw = os.path.join(SRC, 'app/src/main/java/com/deepseekharness/app/ui/IconSwitcher.java')
        if os.path.exists(sw):
            st = open(sw, encoding='utf-8').read()
            # toastApplied 里若仍出现 Toast.makeText 作为主路径（不在 except 兜底里），则报
            _ti = st.find('toastApplied')
            if _ti >= 0:
                _seg = st[_ti:_ti + 2500]
                # 允许 except 兜底里出现，主路径不应出现
                _main = _seg
                _exc = _main.find('catch (RuntimeException customUnavailable)')
                if _exc >= 0:
                    _main = _main[:_exc]
                if 'Toast.makeText' in _main:
                    problems.append(
                        'T20⑥ toastApplied 主路径仍用 Toast.makeText —— '
                        'Android 11+ 会自动套包级 icon（%s），切换配色后提示里仍是默认图标' % (pkg_icon or '?'))
        print('    T20⑥: 包级 icon=%s' % (pkg_icon or '(未取到)'))

    # ⑦ 冲突面必须可登记：A 数应远大于 M 数（T19 ⑩）
    ns, rc = sh(["git", "diff", "--name-status", "upstream/v0.2.2", "HEAD"])
    if rc == 0:
        a = len([l for l in ns.splitlines() if l.startswith("A")])
        m = len([l for l in ns.splitlines() if l.startswith("M")])
        print("    fork 冲突面：%d A / %d M（A 应远大于 M）" % (a, m))
        if m > a:
            warns.append("G9 冲突面 M(%d) > A(%d) —— fork 改动过多落在上游已有文件上，"
                         "下次合并成本会上升（T19 ⑩）" % (m, a))

    print("    merge-base=%s  shallow=%s  replace=%d  roots=%s"
          % ((base[:12] or "(空)"), shallow,
             len(rep.splitlines()) if rep else 0,
             len(roots.splitlines()) if roots else "?"))

    for p in problems:
        fails.append("G9 fork 拓扑：%s" % p)


def gate_workspace_copy():
    """START1/START2 只允许存在一处：项目目录内的源文件。

    历史：2026-11-09 为了「让助手第一句就能读到」，曾在 /workspace、
    /storage/emulated/0、/storage/emulated/0/Download 各放一份副本。
    实测无效（助手仍搜不到，反而更慢），且多副本必然漂移。
    操作员裁定：**只保留项目目录内的源文件，其余删除。**

    本门禁改为反向检查：任何地方出现副本就 FAIL。
    唯一合法位置：
      DSHA开发/START2.md
      WorkBuddy2API开发/P0-work-rc8/START1.md
    """
    print("[7/7] check_workspace_copy  副本必须已清除（只留项目目录内源文件）")
    legal = {
        os.path.join(WS, "START2.md"),
        "/storage/emulated/0/Download/Eta/WorkBuddy2API开发/P0-work-rc8/START1.md",
        os.path.join(WS, "START1.md"),   # 允许但通常不存在
    }
    watch_dirs = ["/workspace", "/storage/emulated/0", "/storage/emulated/0/Download"]
    stray = []
    for d in watch_dirs:
        for name in ("START1.md", "START2.md"):
            p = os.path.join(d, name)
            if os.path.exists(p) and p not in legal:
                stray.append(p)
    if stray:
        fails.append("G7 存在多余副本（应在项目目录内唯一）：%s —— "
                     "副本必然漂移且实测拖慢新会话，请删除" % "、".join(stray))
    else:
        print("    无多余副本；源文件仅 2 处：DSHA开发/START2.md、P0-work-rc8/START1.md")


def gate_self_count():
    """门禁数量不能漂移：文档写「N 道」必须等于代码里 gate_* 函数的个数。

    实测踩过：加了第 7 道 `check_workspace_copy` 后，HANDOFF 仍写「GATE PASS（6 道）」，
    是**新会话的助手**发现的（2026-11-09 21:22）。这类「文档描述工具自身」的数字
    最容易漏改，必须自动查。
    """
    # 排除本函数自身 —— 它也是 def gate_*，但不算一道检查
    n_code = sum(1 for line in open(__file__, encoding="utf-8")
                 if line.startswith("def gate_") and "gate_self_count" not in line)
    problems = []
    targets = [
        (os.path.join(WS, "docs", "HANDOFF-新会话.md"), r"GATE PASS（(\d+) 道"),
        (os.path.join(WS, "docs", "交接规程.md"), r"(\d+) 道门禁|^七道门禁"),
    ]
    for path, pat in targets:
        if not os.path.exists(path):
            continue
        txt = open(path, encoding="utf-8").read()
        for m in re.finditer(r"GATE PASS（(\d+) 道", txt):
            if int(m.group(1)) != n_code:
                problems.append("%s 写「GATE PASS（%s 道）」，代码是 %d 道"
                                % (os.path.basename(path), m.group(1), n_code))
        for cn, num in (("六", 6), ("七", 7), ("八", 8), ("五", 5), ("九", 9)):
            if ("%s道门禁" % cn) in txt and num != n_code:
                problems.append("%s 写「%s道门禁」，代码是 %d 道"
                                % (os.path.basename(path), cn, n_code))
    for pr in problems:
        fails.append("G8 门禁数量漂移：%s" % pr)

    # 同时核对 DATA-SOURCES 里若有登记
    ds = os.path.join(WS, "docs", "DATA-SOURCES.md")
    if os.path.exists(ds):
        for m in re.finditer(r"门禁[^\n]*?(\d+)\s*道", open(ds, encoding="utf-8").read()):
            if int(m.group(1)) != n_code:
                fails.append("G8 DATA-SOURCES 写「%s 道门禁」，代码是 %d 道"
                             % (m.group(1), n_code))


def gate_build_naming():
    """G12 builds/ 产物文件名必须带「主要更新内容」标签，正式版还要带 -release。

    2026-11-11 用户原话：
      「build 同一版本 app 因不断测试，数量很多，很乱，在时间后增加：-主要更新内容。
        当是最后发布的正式版时，额外加上 release。把该要求写到门禁中。」

    为什么必须进门禁而不是只改脚本：builds/ 里当时已经堆了 36 个 apk，
    其中 2005/2010/2022/2058/2108 五个包名字只差时刻，事后根本分不清哪个改了什么。
    只靠人记得传 --note，一定会忘。

    判据分两层：
      ① 规范本身可执行：target_name() 真的会拼出 -<标签> 与 -release
      ② 现存产物：带完整时间戳的产物必须带标签；-release 只对正式发布的包要求，
         不追溯历史包（改名会破坏 updates.json 与已发布 Release 的对应关系）。
    """
    print("[8/9] check_build_naming  builds/ 产物命名规范")
    script = os.path.join(SRC, "tools", "export-release-apk.py")
    if not os.path.exists(script):
        fails.append("G12 缺 tools/export-release-apk.py")
        return
    src = open(script, encoding="utf-8").read()

    # ① 行为验证，不是文本验证。
    # 2026-11-11 教训（MEMORY §4 第 40 条）：断言脚本里的字符串存在，不等于它真的会那么做。
    # 这里直接 import 该模块、真调 target_name()，看三种形态各自拼出什么。
    import importlib.util
    spec = importlib.util.spec_from_file_location("_export_apk_probe", script)
    probe = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(probe)
    except Exception as exc:
        fails.append("G12 export-release-apk.py 无法加载：%s" % exc)
        return
    if not hasattr(probe, "target_name"):
        fails.append("G12 export-release-apk.py 没有 target_name()")
        return

    apk = os.path.join(SRC, "app/build/outputs/apk/standard/release/app-standard-release.apk")
    if not os.path.exists(apk):
        warns.append("G12 找不到产物，无法验证命名行为")
        return

    class _Facts(dict):
        pass

    facts = _Facts(versionName="v1.4 20261111@0.2.2-rc.1")
    cases = [
        (dict(note="", release=False), None, "无标签测试包（应只有 版本+时间）"),
        (dict(note="图标提示条修复", release=False), "图标提示条修复", "带标签测试包"),
        (dict(note="图标提示条修复", release=True), "-release", "正式版（须带 -release）"),
    ]
    for kwargs, expect, label in cases:
        try:
            got = probe.target_name(facts, pathlib.Path(apk), **kwargs)
        except Exception as exc:
            fails.append("G12 target_name(%s) 抛异常：%s" % (kwargs, exc))
            continue
        if not got.endswith(".apk"):
            fails.append("G12 %s：产物名 %r 不以 .apk 结尾" % (label, got))
        if expect is None:
            # 无标签时必须「版本-日期-时刻」三段，不能多出标签
            if not re.fullmatch(r"DSHA-v[\d.]+-\d{8}-\d{4}\.apk", got):
                fails.append("G12 %s：期望 DSHA-v<版本>-<日期>-<时刻>.apk，实际 %r" % (label, got))
        elif expect not in got:
            fails.append("G12 %s：期望含 %r，实际 %r" % (label, expect, got))
    # 净化必须真的生效：非法字符不能进文件名
    dirty = probe.target_name(facts, pathlib.Path(apk), note="a/b:c*d", release=False)
    if any(ch in dirty for ch in '/\\:*?"<>|'):
        fails.append("G12 标签净化失效：%r 仍含非法字符" % dirty)
    print("    命名行为验证通过（无标签/带标签/正式版/净化 四种形态）")

    # ② 现存产物。规范自 2026-11-11 23:00（北京时间）起生效：
    #    此前产出的历史包只 WARN —— 改名会破坏 updates.json 与已发布 Release 的对应关系，
    #    这是用户明确要求「不要批量改名」的边界（见 docs/交接规程.md §4.3b）。
    builds = os.path.join(WS, "builds")
    if not os.path.isdir(builds):
        warns.append("G12 找不到 builds/ 目录，跳过产物检查")
        return
    CUTOFF = 1794409200          # 2026-11-11 23:00:00 +0800
    pattern = re.compile(r"^DSHA-v[\d.]+-(\d{8})-(\d{4})(-(.*))?\.apk$")
    new_bad, old_bad = [], []
    for name in sorted(os.listdir(builds)):
        if not name.endswith(".apk"):
            continue
        m = pattern.match(name)
        if not m:
            continue
        rest = m.group(3)
        if rest and rest.strip("-"):
            continue
        path = os.path.join(builds, name)
        (new_bad if os.path.getmtime(path) >= CUTOFF else old_bad).append(name)
    if new_bad:
        fails.append(
            "G12 规范生效后仍有产物不带「主要更新内容」标签：%s。"
            "构建完必须 python3 tools/export-release-apk.py --note '改了什么'"
            "（正式版再加 --release）" % "、".join(new_bad[:6]))
    if old_bad:
        warns.append(
            "G12 builds/ 里有 %d 个 2026-11-11 23:00 前的历史包没有标签（不追溯，"
            "改名会破坏 updates.json 与已发布 Release 的对应）：%s… 可在下次清 builds/ 时一并处理"
            % (len(old_bad), "、".join(old_bad[:4])))
    if not new_bad and not old_bad:
        print("    builds/ 内产物命名全部合规")


def main():
    if not os.path.isdir(SRC):
        print("FAIL: 找不到 %s" % SRC)
        return 2
    gate_self_count()
    gate_numbers()
    gate_baseline()
    gate_consistency()
    gate_entry_chain()
    gate_env_integrity()
    gate_doc_freshness()
    gate_workspace_copy()
    gate_fork_topology()
    gate_build_naming()

    print()
    for w in warns:
        print("WARN  %s" % w)
    for f in fails:
        print("FAIL  %s" % f)
    if fails:
        print("\nGATE FAILED  (%d fail, %d warn)" % (len(fails), len(warns)))
        return 1
    print("\nGATE PASS  (0 fail, %d warn)" % len(warns))
    return 0


if __name__ == "__main__":
    sys.exit(main())
