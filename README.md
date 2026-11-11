# DSHA

> ## 关于本项目
>
> 仓库：[`steveneng2020/DSH-Android`](https://github.com/steveneng2020/DSH-Android)
>
> 包名 `dsh.android.dev`，发布密钥签名证书 SHA-256 `814ab103…3622f`；
> 覆盖安装需与已装应用同签名。
>
> **当前发布**：`DSHA v1.4 20261111@0.2.2-rc.1` / versionCode `20050357`
> / standard flavor（minSdk 30，系统 WebView）。
>
> 本版更新（详见 [CHANGELOG.md](CHANGELOG.md)）：
> 1. 修复升级后启动页空白、点「启动 DSHA」无反应，以及偶发卡在恢复页的问题。
> 2. 修复维护流程永久卡在「停止 Web 与终端任务」且点「重试」无效：停止屏障原先认不出本应用自己拉起的容器 supervisor，把它当成未识别进程一直不放行。
> 3. 修复升级、降级 APK 后旧实例永久停在「身份未知」而无法启动：新增换代判据，安装包换代判为确定性过期并进入安装与修复页，不再挂起。
> 4. 新增自动适配推理档位：为未声明推理档位的模型补齐声明（DSHA 不猜测第三方模型支持哪些档位，未声明即不显示推理等级），只增不改，写入前自动备份配置。
> 5. 应用图标可点击切换，提供六套配色，切换后立即生效并记住选择；关于页与关于对话框的图标同源，点图标即可切换，图标改为充满画布。
> 6. 插件能力提示新增原生依赖体检：只读检查插件自带原生模块的 ABI 与文件头，不兼容时提示但不阻止安装。
> 7. 新增更新日记面板：关于页按版本分块展示，可展开全部；「关于 DSHA」对话框内也内联同一份更新日记。
> 8. 新增上游对比：显示与上游代码是否一致，只读不写回。
> 9. 关于页交流入口改为联系邮箱 steveneng@163.com；更新页「在浏览器查看发布页」与稳定版、预览版链接指向本仓库，不再跳转上游发布页。
> 10. 发行身份保持独立：包名 dsh.android.dev、自有发布证书，与上游 dsh.android.client 互不通用，覆盖安装需同签名。
> 11. 单变体：移除兼容线与 GeckoView，只发布 Standard（Android 11 及以上、arm64-v8a、系统 WebView）。
> 12. 合并上游 DSHA 0.2.2（上游 build357），内置 DSH 0.2.2-rc.1、Ubuntu 基础环境 10：含移动界面 v5、设备能力授权页独立成页、维护期插件注册死锁修复，以及上一次合并（上游 v0.2.1-rc.2，上游 build190）以来上游的全部提交。以真实上游提交（5e2dca92，2026-11-11）为祖先重建分支，后续上游更新可直接 merge，不再需要硬拼。
>
> App 内更新读取本仓库的 [updates.json](updates.json)，APK 由本仓库 Releases 提供。


<p align="center">
  <b>DeepSeek Harness 安卓启动器</b><br>
  在手机上跑完整的 <a href="https://github.com/deepseek-ai/deepseek-harness">deepseek-harness</a> —— 免 ROOT，免 Termux，装完即用
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT"></a>
  <a href="https://github.com/steveneng2020/DSH-Android/releases/latest"><img src="https://img.shields.io/github/v/release/steveneng2020/DSH-Android?sort=date&color=blue" alt="release"></a>
  <a href="https://github.com/steveneng2020/DSH-Android/stargazers"><img src="https://img.shields.io/github/stars/steveneng2020/DSH-Android?style=flat" alt="stars"></a>
  <img src="https://img.shields.io/badge/Android-11%2B-3DDC84?logo=android&logoColor=white" alt="android">
  <img src="https://img.shields.io/badge/arch-arm64--v8a-lightgrey" alt="arch">
  <img src="https://img.shields.io/badge/flavor-standard-blue" alt="flavor">
</p>

<p align="center">
  <a href="README.en.md">English</a> · <b>简体中文</b> · <a href="CHANGELOG.md">更新记录</a> · <a href="SECURITY.md">安全策略</a> · <a href="docs/security-model.md">安全模型</a> · <a href="AGENTS.md">AGENTS.md（给 AI / 开发者）</a>
</p>

> 🤖 下一个 AI / 开发者请先读 **[AGENTS.md](AGENTS.md)**（项目结构、启动契约、踩过的坑），不要先全库扫描。

> 中文文档索引 [docs/documentation-index.md](docs/documentation-index.md) · [English](docs/en/index.md)。

---

## 图标寓意

<p align="center">
  <img src="docs/assets/icon/default.png" width="180" alt="DSHA 图标：鲲">
</p>

应用图标是一尾**鲲**——单剪影，无玉璧双环，无描金。

> 北冥有鱼，其名为鲲。鲲之大，不知其几千里也。
> ——《庄子·逍遥游》

取这个意象，是因为它对应的正是这个项目在做的事：

- **鲲是鱼，却能化而为鹏**——受限的形体挡不住它。安卓本不是给 glibc Linux 准备的，但一个完整的 Ubuntu 环境照样能在手机里跑起来。
- **「不知其几千里也」是尺度问题，不是能力问题**——同一个 agent harness，在服务器上能做的，在手机上一样能做，不因为屏幕小而减配。
- **北冥是极北的暗海**——起点在看不见的地方，这不重要；鲲不解释自己从哪里来。

### 六套配色

入口在「设置 → 关于 DSHA」，点页面顶部的图标即可切换，立即生效并记住选择。

| 默认（群青·缃金） | 墨玉 | 天青 |
|:---:|:---:|:---:|
| <img src="docs/assets/icon/default.png" width="96"> | <img src="docs/assets/icon/moyu.png" width="96"> | <img src="docs/assets/icon/tianqing.png" width="96"> |
| **赭石** | **碧玉** | **紫绶** |
| <img src="docs/assets/icon/zheshi.png" width="96"> | <img src="docs/assets/icon/biyu.png" width="96"> | <img src="docs/assets/icon/zishou.png" width="96"> |

六套的鲲身明度分布为深 3 / 中 1 / 浅 2，两两色相差或明度差均达标；圆形与圆角矩形遮罩下均无裁切。

## 这是什么

DeepSeek Harness（`@deepseek-ai/dsh`）是 DeepSeek 官方的 agent harness，类 Claude Code。
它是为 glibc Linux 写的，直接在安卓上跑会撞上一堆事：原生模块编译不过、`link(2)` 被
SELinux 挡住、沙箱起不来、前端按桌面布局排版。

**DSHA 把这些全部封在一个 APK 里。** 装 APK、准备环境、打开 Web UI —— 不需要 Termux、
不需要 ROOT、不需要敲一行命令。里面是一个完整的 Ubuntu 环境：`apt` 能用、
交互式 PTY 能用、需要编译的原生模块能装，跟你在服务器上用是同一套东西。

本项目由 [@steveneng2020](https://github.com/steveneng2020) 维护。

---

## 手机系统适配

装之前先对号入座。

### 支持范围

| 项目 | 要求 |
|---|---|
| **Android 版本** | **11（API 30）及以上** |
| **CPU 架构** | **仅 arm64-v8a** |
| Web 内核 | 系统 WebView |
| 实验性虚拟屏 | ✅ 可用 |
| 包体 | 约 280 MB |

**32 位设备、x86 / x86_64 模拟器一律不支持**——APK 内是 arm64 原生库与 arm64 Ubuntu 环境。

### 各系统的已知行为

| 系统 | 状态 | 说明 |
|---|---|---|
| **小米 / Redmi（MIUI、HyperOS）** | ⚠️ 需手动放行 | 无障碍服务（读屏、自动点按）会被系统回滚，需在「设置 → 无障碍」里重新开启，并关闭该应用的「权限管理 → 后台弹出界面」限制 |
| **Android 13+** | ⚠️ 需授权通知 | 通知权限默认关闭，任务通知与后台提醒需要手动允许 |
| **Android 11+** | ✅ 完整支持 | 无线配对（ADB 无线调试）从 11 起可用 |
| **华为鸿蒙（HarmonyOS / anco）** | ❓ 未验证 | 理论上可运行，尚无真机回归记录 |
| **一加 / OPPO / vivo（ColorOS、OriginOS）** | ⚠️ 需省电例外 | 系统会在后台清理进程，需把 DSHA 加入「电池 → 不受限制」白名单，否则长时间任务会被中断 |
| **模拟器（含 Waydroid）** | ❌ 不支持 | 无 arm64 原生环境；即使转译，proot 依赖的内核特性也常缺失 |

### 首次安装后建议做三件事

1. **授予「所有文件访问」**——否则数据留在应用私有目录，卸载即丢失。
2. **把应用加入省电白名单**——否则后台任务会被系统杀掉。
3. **需要读屏/自动点按时**，在无障碍里开启「DSHA 配对助手」，并在系统提示「该应用可能被系统关闭」时选择保持开启。

> 以上均为实测或已记录的系统行为，未列出的机型不代表不能用，只是尚无验证结论。

---

## 下载

本项目的最新构建见 **[Releases](https://github.com/steveneng2020/DSH-Android/releases)**。

当前发布：**`DSHA v1.4 20261111@0.2.2-rc.1`** · Standard 标准版 · Android 11+ / arm64 · **303.18 MiB**

- 包名 `dsh.android.dev`；覆盖安装需与已装应用同签名
  （证书 SHA-256 `814ab1037fb25c781236809c7dffff1a101385ae245b6d5b55b767e44e63622f`）。
- **环境与交互**：内置 DSH `0.2.2-rc.1`、移动 UI `v5`，默认 **proot**、可选 **proroot**。
- **备份与数据保护**：一键备份/导出，保留用户数据；外置工作区内容保留。
- **本版更新**：12 项，详见 [CHANGELOG.md](CHANGELOG.md)。

> **App 内更新**：更新清单是本仓库根目录的 [`updates.json`](updates.json)，
> APK 走 GitHub Releases。


### 开始使用

1. 安装标准版 APK，首次启动准备内置离线环境。
2. 解压完成进入主页，Web 在后台启动；就绪后进入 Web UI，在网页中配置模型。
3. 从旧包迁移请先导出备份，再在新包恢复；以后同包覆盖更新前，请先正常停止 DSH。

精确 APK 已在 Android 13 对两种运行时、旧会话、插件状态及立即息屏启动做有限检查；页面延迟仍有波动，不承诺所有机型普遍提速或完整 Doze/功耗验收。详见[更新记录](CHANGELOG.md)与[已知限制](#已知限制)。[下载校验](docs/download-verification.md)。


---

## 为什么是 DSHA

|  | 说明 |
|---|---|
| 🚫 **零命令行门槛** | 内置离线 Ubuntu rootfs，APK 装完就能用。不装 Termux、不配 pkg、不敲命令 |
| 🐧 **完整 glibc 环境** | 不是裁剪版：`apt` / PTY / 原生模块 / Python / git 都在。第三方插件不用改就能跑 |
| ⚙️ **双运行时选择** | 默认proot、可选proroot；实际性能取决于设备、I/O、缓存和插件，不以历史异条件样本给引擎排名 |
| 🔌 **手机就是 agent 的手** | 无障碍 + ADB 免 Shizuku 直连 + 独立虚拟屏：读屏、点按、装应用、跑自动化，全部内置 |
| 💾 **导出后迁移数据** | “数据与备份”导出无需密码的 `.tar.gz`；数据位置可在存储指南查看，本机副本不保证卸载后存续 |
| 🩺 **坏了能自己说清哪坏了** | 组件级自检 + 按需修补 + 启动诊断 + 独立应急 DSH；Web 起不来时直接点名是哪个插件 |

---

## 核心模块

### ① 装机与环境

| 能力 | 说明 |
|---|---|
| 内置离线 rootfs | Ubuntu 24.04 (noble) arm64 打进 APK，无网也能完成环境部署 |
| 六步安装流水线 | 解压 → 基础工具 → Node.js → pnpm → dsh → 补丁，每步先探测再执行、装完即校验；只修失败项，不从头重来 |
| 分步重装 / 更新 | rootfs、工具、Node、harness 相互独立，可单独重装，不重复下载 |
| 双装机路径 | 预构建包与源码构建都支持，源码路径自动处理 node-pty 等原生模块编译 |
| 离线工具链 | curl / git / Python / 证书随包锁定版本（`packages.lock.json`），不依赖用户先跑 `apt` |
| 镜像与网络 | apt 源官方 / 中科大镜像自动回退；DNS 三模式（auto / 强制 IPv4 / 系统原生），AAAA 被拒时仅重试解析、不重放 HTTP 请求 |
| 基础环境版本化 | Ubuntu 基础环境独立编号；界面更新不重建环境，普通 dsh 更新不递增基础版本 |

### ② 运行时

| 能力 | 说明 |
|---|---|
| proroot / proot 双运行时 | 默认稳定的 proot；可在“配置”选择 proroot，实际兼容结果依机型 |
| 性能证据 | 有同台有限样本，设备、缓存和插件状态影响明显；见[性能记录](docs/performance-startup-20261022.md)，不作为普遍引擎排名 |
| 有限兼容回退 | proroot 在鉴权前明确退出且无插件故障时，确认 guest 退出后仅重试一次 proot；慢启动不触发回退 |
| Node.js 24 + pnpm 10 | 运行环境随包锁版本 |
| 分包更新 | Ubuntu 与 dsh 运行时在 APK 内分包；冷安装两份都解压，局部更新只读 dsh 包 |
| 受管更新试运行 | 新环境先在隔离区真实启动、验证端口 / 鉴权 / 会话读写 / 插件加载，全过后才切换提交，失败自动回切 |
| 前台服务 + 看门狗 | 通知栏可见运行状态；Web 掉了自动拉起，不用手动重启 |
| 慢启动保护 | 等待鉴权不设强杀时限（60 秒仅提示），看门狗不会把慢启动当故障误杀 |

### ③ 数据与备份

| 能力 | 说明 |
|---|---|
| 数据位置与迁移 | “数据与备份 → 存储指南”查看实际位置；升级保留当前数据，卸载前请导出需要保留的内容 |
| v5 备份与导出 | 新导出为无需密码的 `.tar.gz` 完整性归档；内部自动副本仍加密，旧加密原件读取仍需原密码 |
| 自动备份计划 | 默认开启：每天指定时间 / 每隔 1–168 小时 / 停止 DSH 后，三种模式；运行中自动延后不打断工作；保留最近 3 份已验证副本 |
| 分范围备份 | 全量 / 只对话 / 只插件 / 只设置任选，恢复时只覆盖对应内容 |
| 换机恢复 | 导出实际对话、附件、设置及用户插件，先校验摘要和范围再预检恢复，保留当前内容与冲突原件 |
| 凭据不进备份 | 桥 token 整文件排除；`.credentials.yaml` 字段级剔除本机密钥、保留用户 API key |
| 兼容旧备份 | 先完整认证/摘要核验再预检；未知或依赖不完整时如实提示。系统插件由当前 APK 重建，用户原件继续保留 |
| 会话损坏隔离 | 坏掉的会话文件挪到 `corrupt-backup` 可取回，不让一个坏文件卡住整个 Web |
| 覆盖更新自动清理 | 升级后闲时清理可再生缓存与多余旧副本；保留至少两份健康前代，改过的原件不动 |
| 外置工作区保护 | 彻底重装与完整格式化已移除；维护只断开外置引用，保留其文件和备份 |

### ④ 设备能力（让 agent 真正操作这台手机）

agent 通过本机 `127.0.0.1:3090` 桥调用以下能力（token 门控，`/app/help` 有完整端点清单）：

| 能力 | 说明 |
|---|---|
| 屏幕操作 | **无障碍服务实现，不需要 ADB**：读屏结构化输出（带可点击区域坐标）、按文字 / 坐标点按、输入、按键、滑动、截屏存 PNG |
| 独立虚拟屏（实验） | Standard / Android 11+，先授权 ADB、Shizuku 或 Root 任一通道，再到虚拟屏页面创建屏幕；仅开启无障碍不会创建虚拟屏，详见[开启说明](docs/virtual-screen-guide.md) |
| ADB 无线直连 | 内置无线配对（TLS 1.3-PSK + SPAKE2）与保活，**不需要 Shizuku**，重启手机自动恢复 |
| Shizuku / Root 通道 | 备用设备命令通道，与 ADB 同受命令白名单约束 |
| 与用户交互 | 系统通知、App 内提示、震动（长任务叫醒用户）、弹窗三选项征询、分享 / 打开链接 |
| 文件交换 | 读目录 / 文本文件、导出产物到 `Download/DSHA`；凭据区（`.dsh` / `.ssh` / `.android`）读写均被拒绝 |
| 传感器与位置 | 光线 / 加速度 / 陀螺仪 / 磁力计 / 气压 / 步数 / 定位 / 手电筒 —— 默认关闭，逐项授权 |
| 剪贴板 | 读写剪贴板（受系统前台限制） |
| 危险命令守门人 | 设备命令始终走白名单解析：格式化 / 分区 / SELinux / 系统属性等直接拒绝；不认识的命令不放行；拦截返回 `[POLICY_BLOCKED]` 而不是弹「仍然允许」 |
| 短信读取 | 独立敏感能力，仅限严格只读查询，默认每条确认，授权可撤销、不随备份迁移 |

### ⑤ 终端

| 能力 | 说明 |
|---|---|
| 真 PTY 终端 | Termux terminal-emulator JNI 实现：vim / htop / tmux 等全屏 TUI 可用 |
| 手机键盘补偿 | 扩展键行（Ctrl / Alt / Esc / 方向键 / Tab），双指缩放调字号 |
| 多标签 | 多会话并存，跨切页 / 旋转 / 语言切换保持进程与状态 |
| 简易终端兜底 | PTY 在个别机型异常时可切回简易终端，会话保留在后台 |

### ⑥ Web UI 与访问

| 能力 | 说明 |
|---|---|
| 内核 | 使用系统 WebView，随系统更新 |
| 移动端适配 | 内置 [dsh-web-mobile](https://github.com/mexiaosqwq/dsh-web-mobile) **3.3.5**（MIT），保留手机快捷键和窄屏适配，修复焦点、弹窗及插件卡片 |
| 画中画 | 默认关闭，用户主动开启后使用 PiP 小窗；正常返回与后台恢复保留同代网页实例 |
| 高刷与省电 | 按用户上限请求刷新率，空闲交还系统；实际帧率依设备和系统，不把请求成功当作性能证明 |
| 深浅色与多语言 | 深色 / 浅色 / 跟随系统；简体中文 / English，默认跟随系统语言 |
| 局域网访问 | 电脑 / 平板浏览器直接用手机上的 dsh。token 鉴权 fail-closed，命中后回设 `SameSite=Strict` Cookie，不让 token 随外链泄漏 |
| 老浏览器兼容 | 自动注入 `AbortSignal.any/timeout` 与 `crypto.randomUUID` polyfill（局域网 HTTP 下必需） |
| 流式悬浮条 | AI 输出像歌词一样贴在屏幕顶部，工具调用翻译成人话；底色 / 透明度 / 行数可调；危险命令可直接在悬浮条上批准 |
| 端口可配 | Web 端口自定义，冲突自动回退并说明 |

### ⑦ 插件生态

| 能力 | 说明 |
|---|---|
| 插件管理 | 安装 / 更新 / 启停 / 删除 / 搜索 / 排序，全在 App 内；支持社区插件 |
| 多样安装方式 | GitHub 简写 / tree / blob / archive / Release 链接、HTTPS 压缩包直链、本地导入（按内容识别格式）、终端 `dsha-plugin install` |
| 多下载源 | 自动择源，支持 npm 官方源与 npmmirror，更新检查多路并发、锁定版本复用缓存、失败有限回退 |
| 依赖与事务 | 随包 pnpm 10.34.5，允许未锁定依赖解析、生命周期脚本和 pnpmfile；记录实际锁与目录摘要，拒绝归档越界并保留回切原件 |
| 安装后自动启用 | 包格式、路径、依赖与摘要检查后自动提交并启用；用户主动禁用和安全模式意图保持，详见[插件说明](docs/plugins.md) |
| 硬依赖自动改造 | 插件写死的服务依赖就地改成运行时注入 —— 一个插件不拖挂整棵插件树 |
| 内置插件保护 | 内置插件不可删除；用户禁用过的，升级后保持禁用；配置可导入导出 |

主要内置插件包括：`dsh-web-mobile`（移动端适配）、`dsh-status-overlay`（悬浮条）、
`dsh-task-notifier`（回合完成通知）、`dsh-device-shell-guide`（设备能力引导）、
`dsh-computer-use-android`（Android Computer Use）、`dsh-tool-vscreen`（虚拟屏工具）、
`dsh-auto-review`（官方实验性 Auto review 入口）。

### ⑧ 可靠性与应急

| 能力 | 说明 |
|---|---|
| 安装与修复页 | 检查全部六项组件并按需修复（证书 / npm 异常、DNS、会话写入补丁等），只处理失败项 |
| 诊断报告 | 环境检查 + 失败日志可导出；启动诊断保存阶段、实际插件错误与退出码，最近五次脱敏留存 |
| 启动恢复 | 明确的启动 / 插件故障自动进入恢复页；安全启动用独立 profile 只加载官方基础组件，原配置与插件开关保留 |
| 配置快照 | 配置变更前自动留快照（三份健康 + 三份修复前），坏了能回滚 |
| 插件故障人话诊断 | Web 起不来时直接说「是插件 X、它要的服务不存在、点这里修」，而不是甩一屏 Node 堆栈 |
| 独立应急 DSH | 正式环境损坏时进入独立应急环境：独立运行根、只读诊断先行，写入修复需原生逐步确认 |
| 脚本增量热更新 | 关键脚本可从 GitHub 增量更新并**离线验签**（公钥内置，签名不符整批拒绝），不必等新 APK |

### ⑨ 安全（默认最小权限）

| 层面 | 做法 |
|---|---|
| 什么权限都不给也能用 | 最小配置（不给 ADB、不给文件权限、不开局域网）下 DSHA 照常跑 dsh；每项能力默认关闭、随时撤销 |
| API key | Android Keystore + AES/GCM，密钥不出 Keystore；失败不清空旧密文 |
| 设备命令 | 白名单始终开启，Root / Shizuku / ADB 三通道同一套策略，应用停止前逐个核验归属，防 PID 复用误伤 |
| 桥凭据护栏 | `/app/export`、`/app/readfile` 拒绝凭据区路径，有规范化与 canonical path 检查；已知 Root 递归 READ 子链接缺口见安全文档，不视为完整隔离 |
| 无遥测 | 不上传任何日志或使用数据；更新、插件下载、模型调用之外不发起网络请求 |
| 诚实披露 | 已知弱点（无内核级沙箱、历史明文备份、签名密钥待轮换等）在文档里直接列出 |

👉 每项权限到底暴露了什么、agent 碰得到手机的哪些部分，见 **[安全模型](docs/security-model.md)**。

---

## 与同类方案的关系

安卓上跑 dsh 目前有两条路，各有代价，说清楚比互相贴标签有用：

| | **容器派**（DSHA 走这条） | **Termux bootstrap 派** |
|---|---|---|
| 做法 | proot/proroot + 完整 glibc rootfs | 用 Termux 的包在 Android bionic 上裸跑 |
| 装机 | 装 APK 就完事 | 装 Termux → 敲命令 → 装工具链 |
| 环境 | 完整 Ubuntu，`apt` 与原生模块随便用 | 需要为 bionic 逐个打补丁 / 重编 |
| 开销 | 存在系统调用与文件 I/O 转译开销，实际耗时依设备与场景 | 无容器层，理论最快 |
| 沙箱 | 两边都受限 | 两边都受限 |

---

## 已知限制

诚实列出来，省得你装完才发现：

| 项目 | 状态 | 说明 |
|---|---|---|
| 架构 | ⚠️ 仅 arm64-v8a | 32 位与 x86 设备不支持 |
| 系统 | ✅ Android 11+ | 低版本系统不受支持；无线配对等能力本身也需 11+ |
| 包体 | ⚠️ 本次 Standard 303.18 MiB | 内置完整 Ubuntu 环境的代价，换来的是免下载、免命令行 |
| bash 工具 | ✅ 可用 | 完整 Ubuntu 的 bash，agent 跑 shell 命令没有限制 |
| bash 的**沙箱隔离** | ⚠️ 不可用 | bubblewrap 要 unprivileged user namespace，Android sepolicy 不给 —— 容器派和 Termux 派都一样绕不过。约束靠 dsh 的权限档位：默认 `danger-full-access`，可在配置页改成 `workspace-write` 或 `read-only`。请自行判断风险 |
| 卓易通 / 鸿蒙 anco | ❓ 未验证 | 理论可行，尚无真机回归 |
| 悬浮条 | ⚠️ 需要授权 | 用 `TYPE_APPLICATION_OVERLAY` 自绘；免 ROOT 拿不到真正的「状态栏歌词」接口 |
| 数据位置 | ⚠️ 需要文件权限 | 「所有文件访问」被拒时数据留在私有目录，卸载即丢（自检会明确告知当前状态） |

---

## 架构

```
┌──────────────────────── APK ────────────────────────┐
│ 原生 Android（Java 17 · Material3 · 单模块 :app）    │
│  ├ 启动 / 安装修复 / 配置 / 工作区 / 插件 / 终端     │
│  ├ 网页内核：系统 WebView                            │
│  ├ 前台服务 + 看门狗 + 通知 + 画中画                 │
│  ├ App 桥 :3090（无障碍 / 虚拟屏 / 交互 / 文件）     │
│  ├ LAN 代理 :3081 · ADB / Shizuku / Root 设备通道    │
│  └ 悬浮条（TYPE_APPLICATION_OVERLAY）                │
├─────────────────────────────────────────────────────┤
│ proot（默认）/ proroot（可选，依机型核验）           │
├─────────────────────────────────────────────────────┤
│ Ubuntu 24.04 arm64 · Node.js 24 · pnpm 10           │
│  └ @deepseek-ai/dsh  →  Web UI :auto                │
└─────────────────────────────────────────────────────┘
```

数据：实际位置以“数据与备份 → 存储指南”为准；旧 `Documents/dshdata` 数据继续兼容读取。
API key 由 Android Keystore 保护，本机密钥与自动副本不保证卸载后存续。

---

## ADB 无线配对（设备 Shell 能力）

配好之后 agent 就能直接操作这台手机，**不需要 Shizuku**。

**首次配对（约 1 分钟）**

1. 系统设置 →「关于手机」→ 连点「版本号」7 次开启开发者选项
2. 开发者选项 → 打开「无线调试」
3. 进入「无线调试」→「使用配对码配对设备」，记下 **IP:端口** 与 **6 位配对码**
4. 回到 DSHA →「设备能力授权」页 → 填入 → 配对

> 无线调试的配对码需要 Android 11+；老系统可走 Shizuku / Root 通道，或直接用无障碍能力（读屏、点按、输入不需要任何配对）。

无线调试尚未开启时，“验证已有连接”可以先准备内置离线依赖；出现 `ADB_OFFLINE_READY` 仅表示依赖就绪。之后仍需打开无线调试并完成配对或连接验证。

**配对之后**：DSHA 自己维护连接（保活 + 重连），重启手机后也会自动恢复，不用再操作。

**验证**：内置终端里跑 `adb shell id`，输出 `uid=2000(shell)` 即成功。

**让 agent 用起来**：把技能包复制到 agent 的技能目录：

```bash
cp -r agent-skills/device-shell ~/.agents/skills/
cp -r agent-skills/screen-ocr-operator ~/.agents/skills/
```

`device-shell` 覆盖 ADB / Shizuku / Root 三通道的命令用法；
`screen-ocr-operator` 提供截屏 + OCR + 批量屏幕操作（无障碍读屏拿不到内容的 WebView / 游戏画面用）。

---

## 构建

本地构建需要 JDK 17、Android SDK（API 37）、NDK 26 与 Python 3.9+，详见 [BUILD.md](BUILD.md)：

```bash
bash build.sh                                # 默认构建 Standard Debug
bash build.sh :app:testStandardDebugUnitTest # 纯逻辑单测
python tools/verify-stability.py             # 稳定性验收门禁
```

离线 rootfs 不提交 Git；发布流程（签名、门禁、真机验收、产物替换）见 [BUILD.md](BUILD.md) 与 [docs/releases/](docs/releases/)。

---

## 文档索引

| 文档 | 内容 |
|---|---|
| [AGENTS.md](AGENTS.md) | 项目结构、启动契约、技术约束与踩坑记录（AI / 新贡献者入口） |
| [SECURITY.md](SECURITY.md) | **本项目**的安全策略与漏洞报告渠道 |
| [docs/security-model.md](docs/security-model.md) | 安全模型：每项权限的边界与已知弱点（[英文版](docs/security-model.en.md)） |
| [docs/plugins.md](docs/plugins.md) | 插件安装与打包要求 |
| [CHANGELOG.md](CHANGELOG.md) | 完整更新记录 |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 路线图与「明确不做」清单 |
| [docs/android-standard.md](docs/android-standard.md) | 设备适配说明 |
| [docs/releases/](docs/releases/) | 各版本发布与验收记录 |

## 致谢

- [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) —— 本体
- [DSH-APP/DSHA](https://github.com/DSH-APP/DSHA) —— 安卓封装的上游实现，本项目在其基础上继续开发；
  感谢原作者 [@qiannianhuanxiang](https://github.com/qiannianhuanxiang) 与贡献者 [@ym2025szz](https://github.com/ym2025szz)
- [proroot](https://github.com/coderredlab/proroot) / [proot](https://github.com/termux/proot) —— 免 ROOT 容器（见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)）
- [Termux terminal-view / terminal-emulator](https://github.com/termux/termux-app)（Apache-2.0）—— PTY 终端
- [dsh-web-mobile](https://github.com/mexiaosqwq/dsh-web-mobile) —— 内置移动端适配
- [Shizuku](https://shizuku.rikka.app/) —— 备用设备命令通道

## 交流

| 事宜 | 渠道 |
|---|---|
| 缺陷与功能建议 | [GitHub Issues](https://github.com/steveneng2020/DSH-Android/issues) |
| 安全漏洞 | 见 [SECURITY.md](SECURITY.md)（**不要**用公开 Issue） |
| Email | steveneng@163.com |

> 本项目不维护任何官方社群；其他渠道的答复不代表本项目。


## 许可与免责声明

### 许可

本项目以 [MIT 许可证](LICENSE) 发布，完整条款见 [LICENSE](LICENSE)。

**版权归属**（三层，缺一不可）：

| 范围 | 版权 |
|---|---|
| DeepSeek Harness 本身（[deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness)，MIT） | Copyright (c) 2026 DeepSeek |
| 上游安卓启动器 DSHA（[DSH-APP/DSHA](https://github.com/DSH-APP/DSHA)） | Copyright (c) 2026 qiannianhuanxiang |
| 本项目的新增与修改（[DSH-Android](https://github.com/steveneng2020/DSH-Android)） | Copyright (c) 2026 steveneng2020 |
| 第三方组件 | 归各组件作者所有，逐项列于 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) |

**依赖层次**：本项目是安卓启动器，自身不含模型与 agent 实现；它随包分发 DeepSeek Harness
官方 npm 运行时（`@deepseek-ai/dsh`，版本与来源见 `tools/dsh-runtime/package-lock.json`），
并在此之上延续上游 DSHA 的安卓外壳开发。**对 DeepSeek Harness 与上游 DSHA 的作者均无隶属、
赞助或背书关系**；本项目不主张对 DeepSeek Harness 的任何著作权。

本项目是在上游实现基础上继续开发的衍生作品。**以上两层的版权声明与许可声明必须完整保留**。

**二次使用要求**：若需参考、引用、分发或合并本项目的代码或衍生作品，**须保留完整出处**——
注明本项目仓库地址 `https://github.com/steveneng2020/DSH-Android` 及上述版权声明，
并保留 [LICENSE](LICENSE) 全文。移除或篡改出处标识后再分发不符合本项目的许可要求。

### 免责声明

**本项目仅供技术学习与研究使用。**

| 项 | 说明 |
|---|---|
| **不得商用** | 未经原作者与本项目维护者书面许可，**不得将本项目（含源码、二进制、衍生作品）用于任何商业用途**，包括但不限于售卖、租赁、收费分发、捆绑进商业产品或作为商业服务的组成部分 |
| **风险自担** | 本项目按「现状」提供，不附带任何明示或暗示的担保。使用本软件可能造成的**数据丢失、设备损坏、账号封禁、服务中断或任何其他直接/间接损失，全部由使用者自行承担** |
| **无官方关系** | 本项目是社区二次开发版本，**与 DeepSeek 官方、`DSH-APP/DSHA` 上游作者均无隶属、赞助或背书关系**。任何问题请勿向官方渠道提交 |
| **法律合规** | **使用本 App 或其接入的 API 服务，须严格遵守所在国家或地区的相关法律及规定。若所在国家或地区不允许使用，须立即停止使用并卸载本 App。** 使用者须自行确认其使用行为在当地合法；因违规使用产生的一切后果由使用者自负 |
| **服务条款** | 使用者须自行确保其使用行为符合所接入模型/API 服务商的使用条款与计费规则 |
| **不提供担保** | 维护者不承诺修复缺陷、不承诺持续更新、不对任何特定用途的适用性作出保证 |
| **第三方服务** | 本项目本身不提供任何模型或 API 服务。使用者需自行准备并遵守相应服务商的条款与计费规则 |

### 安全

漏洞报告方式与已知安全边界见 [SECURITY.md](SECURITY.md)。**请勿通过公开 Issue 披露未修复的安全问题。**
