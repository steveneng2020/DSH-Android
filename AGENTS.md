# AGENTS.md

> **本文件面向 AI 与新贡献者**：读完不用扫全库就能上手。先读 [README.md](README.md)。
>
> **这是 fork**：[steveneng2020/DSH-Android](https://github.com/steveneng2020/DSH-Android)，
> 不是上游 [DSH-APP/DSHA](https://github.com/DSH-APP/DSHA)。包名 `dsh.android.dev`、
> 发布证书 SHA-256 `814ab103…3622f`，与上游 `dsh.android.client` / E7E3 **互不通用**，
> 不存在覆盖安装关系，数据也不互通（迁移须用备份导出/恢复）。
> 上游仓库仅作只读参考，本项目不向其提交、不向其发布。
>
> **三层版权**（详见 [LICENSE](LICENSE)）：DeepSeek Harness（`deepseek-ai/deepseek-harness`，MIT）
> → 上游安卓启动器 DSHA（`DSH-APP/DSHA`）→ 本项目（`steveneng2020/DSH-Android`）。
> 本项目不含模型与 agent 实现，只随包分发 DSH 官方 npm 运行时；对前两层作者均无隶属或背书关系。

## 仓库事实（现行，以代码为准）

- 形态：Gradle 单模块 `:app`，**纯 Java 17（0 个 .kt）**，arm64-v8a。
- 应用：包名 `dsh.android.dev`，`standard` flavor（minSdk 30，系统 WebView）。
  版本号与文件名以 `app/build.gradle` 为准，本文件不另维护一组数字。
- 内置 DSH：`@deepseek-ai/dsh` **0.2.2-rc.1**，由 `tools/dsh-runtime/package-lock.json` 锁定；
  `Constants.DSH_VERSION`、`package.json`、锁文件与 `runtime-patches.json` 必须一致
  （`verifyBundledDshGeneration` 在配置期就拒绝混代）。
- 运行时：Ubuntu 24.04 arm64 + proot（默认）/ proroot（显式可选），基础环境身份 10。
- 更新：App 内「检查更新」只读本仓库 `main` 的 [updates.json](updates.json)，
  APK 由本仓库 Releases 提供；维护规则见 [UPDATES-HOWTO.md](UPDATES-HOWTO.md)。
- 更新记录三面必须一致：`CHANGELOG.md`（仓库）、`docs/releases/build{code}-changes.{zh,en}.md`
  → `app/src/main/res/{raw,raw-en}/changelog.md`（全文，生成器守）、
  `app/src/main/res/{raw,raw-en}/changelog_recent.json`（摘要卡）。
  漂了就 `python3 tools/check-changelog-sync.py --write`，门禁在 `ci-fast` 与 `verify-stability`。

### 构建任务（只有 standard）

```bash
python3 tools/run-host-tests.py --stage fast      # 宿主测试
./gradlew :app:testStandardDebugUnitTest          # 单测
./gradlew :app:assembleStandardRelease            # 正式包（需发布签名）
```

`low` flavor 仍存在于源码树，但**从未发布**，不作为分发目标；对外文档一律不提它。

---

## 目录地图（2026-11-10 实测数量）

```
app/src/main/java/com/deepseekharness/app/          603 个 .java（main）
├── *.java（根包，29 个）      设备与服务层：无障碍、桥、LAN、悬浮条、Shizuku/Root、PTY
├── ui/      （91 个）         界面：MainActivity + 各 Fragment / Activity / 对话框
├── core/    （47 个）         编排：HarnessController、维护屏障、备份任务、诊断
├── runtime/ （56 个）         容器：ProotBootstrap、ContainerRuntime、WebProcessManager、装机
├── backup/  （79 个）         数据：v5 加密备份、恢复、迁移、格式化、自动备份（最大的包）
├── vscreen/ （27 个）         独立虚拟屏：通道 / 预览 / 输入 / 无障碍桥
├── recovery/（5 个）          独立应急 DSH：与正式环境完全分开的生命周期
├── bridge/  （9 个）          AppBridge 契约、AdbBridge、LAN 访问
├── data/    （4 个）          KeyVault（Keystore）、便携设置、导出
├── device/ diagnostics/ screen/ capabilities/ skills/   共 23 个（设备审计与诊断、屏幕、能力探测）
└── util/    （233 个）        纯逻辑：不 import 任何 Android API，必须配单测

全线共 1072 个 .java（含 test 389、androidTest 10、debug 39、deviceAudit 21）
```

数量是导航线索，不是契约；`util/` 里放了 233 个纯逻辑类，改动前先确认既有类没有同名职责。

### 根包（`com.deepseekharness.app`）——设备与系统服务

| 类 | 职责 |
|---|---|
| `HttpShellService` | **3090 桥本体**（约 105 KB，最大的类）：`/exec` 与 `/app/*` 共 24 个端点，token 门控 |
| `DshaAccessibilityService` | 无障碍：`uiDump / uiTap / uiTapText / uiInput / uiKey / uiSwipe / uiScreenshot` + 虚拟屏转发 |
| `DeviceBridgeService` | 设备通道总管：ADB / Shizuku / Root 三通道选择与保活 |
| `DeviceShellExecutor` / `DeviceAppInventory` / `DeviceSense` | 设备命令执行（白名单在 util）、应用清单、传感器 / 位置 / 手电 |
| `LanProxyService` / `LanAuth` | 局域网代理 `:3081`（token fail-closed）与鉴权 |
| `OverlayController` / `OverlayLines` | 流式悬浮条（歌词式 AI 输出 + 命令批准） |
| `HarnessService` / `WebPreviewActivity` | 前台服务 + 看门狗；Web 内嵌预览（WebView / Gecko） |
| `PtySession` | Termux terminal-emulator JNI 包装（真 PTY 终端） |
| `ShizukuShell` / `RootShell` / `ShellService` / `AdbKeepAliveReceiver` / `BootReceiver` | 通道实现与开机 / 保活接收器 |
| `DshaDocumentsProvider` | 文件管理器访问私有目录（MT 管理器等） |
| `DeviceShellPolicy` / `DeviceShellExecutor` | 受管设备命令解析与执行前守卫；批准不覆盖显式拒绝，Root 也受此策略检查 |
| `BridgeAskDialog` / `ConfirmReceiver` | 原生业务提问与安全确认通知回执；业务选择不由全局确认代答 |
| `DshaApp` / `UpdateDownloadService` | Application 入口（系统语言锁存等）；应用内更新下载 |

Root 维护以 [权限架构](docs/device-permissions-architecture.md) 与 [固定上游源码核查范围](docs/references-and-provenance.md) 为准：九个 su 候选及 metadata 检查不等于管理器识别或全版本兼容；65 秒只限制结果收集。2026-10-22 对照 `140c7ba` 的审查发现递归 READ 尚未核验子链接目标，短信保护存在实现覆盖缺口，不能写成“仅有文档问题”或“完整防绕过”；未修状态、回归与设备证据须分别记录。历史 `DangerShellGuard` 已不在生产调用链。

### 分层归属（改代码前先看这里）

| 层 | 关键类 | 职责 |
|---|---|---|
| `ui/` | MainActivity / WelcomeActivity / Launch·Config·Settings·Plugin·Workspace Fragment / WebPreviewActivity | 界面与启动门禁 |
| `core/` | `HarnessController`（约 57 KB，编排核心） | 启动 / 停止 dsh、鉴权链接捕获；**不要再往里塞新职责**，新逻辑写成独立协作者 |
| `core/` | `ConfigStore` | 配置唯一读写入口（端口 / 模型 / workdir / API key） |
| `core/` | `InstallRepository` / `MaintenanceCoordinator` / `RuntimeTasks` / `StartupDiagnostics` | 安装状态、维护屏障、运行任务锁、启动诊断 |
| `runtime/` | `ProotBootstrap` / `ContainerRuntime` / `WebProcessManager` | proot 命令组装；运行时选择 + BINDS 挂载清单；停止 Web（哨兵 + pid + 出生身份核验） |
| `runtime/` | `InstallPipeline` / `ManagedRuntimeAssets` / `RuntimeTrial` | 六步安装编排、受管资产、更新试运行 |
| `backup/` | `NativeBackupJobs` / `BackupArchive` / `HostDataTransaction` / `AutomaticBackups` / `FactoryReset` | v5 加密备份 / 恢复 / 数据事务 / 自动计划 / 格式化 |
| `recovery/` | `RecoveryController` / `RecoveryRuntime` / `RecoveryRepairBroker` | 独立应急 DSH，不经正式环境的迁移与启动锁 |
| `vscreen/` | `VirtualScreenManager` / `VirtualScreenAccessibility` / `VirtualScreenPreviewView` | App 持有认证连接与心跳；输入必须带最新帧号 |
| `bridge/` | `AppBridge`（契约）/ `AdbBridge`（无线配对 TLS1.3-PSK + SPAKE2）/ `LocalNetworkAccess` | 桥接缝与设备通道 |
| `data/` | `KeyVault` | Keystore AES/GCM 加密 API key |
| `util/` | `Constants` / `ShellQuote` / `Query` / `WebProcSel` / `DeviceShellPolicy` / `HttpProtocol` / `BackupScope` 等 118 个 | 纯逻辑，全包零 Android import，**必须配单测** |

---

## 测试布局（2026-11-10 实测）

`app/src/test/java/com/deepseekharness/app/` 共 **389** 个测试类，分布：
`util/` 213、`backup/` 54、`core/` 35、`runtime/` 30、`vscreen/` 28、`ui/` 14、
`data/` 2、`recovery/` 2、`bridge/` `capabilities/` `screen/` `skills/` 各 1、根包 1。

**静态类数不等于执行数**，也不要拿本表当通过证据——实际通过/失败/跳过以当次
JUnit XML 与 [docs/releases/](docs/releases/) 的回执为准。

```bash
./gradlew :app:testStandardDebugUnitTest   # 全量单测（standard）
```

锁定的不变式（重构时绝不能改坏）：

- `ShellQuote`：POSIX 单引号转义，恶意值不能逃逸。
- `Query`：逐参数名匹配（`indexOf(key+"=")` 会被后缀劫持，已修）；「参数为空」≠「参数不存在」。
- `BackupScope`：部分备份绝不叫 `DSHA-backup-*`（否则老版本当全量恢复会清掉配置与插件）；`dshPaths` 与 `mergeSubdirs` 一一对应。
- `WebProcSel`：认得出 dsh 进程、**绝不误杀 proot/proroot**（杀到容器启动器 = 环境连 App 一起带走）。
- `DeviceShellPolicy`：白名单默认拒绝，只接受可完整识别的单条 argv，不执行用户提供的 shell 程序。
- `HttpProtocol` / `SocketDispatch`：头部字节与总截止独立上限；LAN 连接登记、短请求 / 长流 / 反向 pump 独立有界。

---

## 安全模型（设计围绕这些边界）

先读 [docs/security-model.md](docs/security-model.md)。要点：

- **设备命令白名单始终开启**（`util/DeviceShellPolicy`）：格式化 / 分区 / SELinux / 系统属性写入直接拒绝；不认识的命令不放行；拦截返回 `[POLICY_BLOCKED]` + 退出码 126，**没有「仍然允许」按钮**。Root / Shizuku / ADB 三通道同一套策略。
- **桥的凭据护栏**（`util/BridgePathPolicy`）：`/app/export`、`/app/readfile` 拒绝 `.dsh` / `.ssh` / `.android` 等凭据区；字符串判据 + `getCanonicalPath()` 双重核验，堵软链接绕法。
- **最小权限默认**：所有敏感能力（ADB、Root、短信、传感器、位置、悬浮窗、LAN）默认关闭、可撤销；最小配置下 DSHA 照常跑 dsh。
- **备份凭据排除**：桥 token 整文件排除；`.credentials.yaml` 字段级剔除本机密钥、保留用户 API key。
- **这不是内核沙箱**：容器、插件、终端都在 App 的 Android UID 下运行。白名单保护随包入口，不约束任意自写代码 —— 别在文档里宣称「安全隔离」。
- 已知弱点（含 `danger-full-access`、历史明文备份、签名密钥待轮换）直接写在安全模型文档里，别删。

---

## 技术约束（围绕这些设计）

### 版本与构建

- **版本与签名身份以 `app/build.gradle` 与 `ci/release-identity.json` 为准**：包名 `dsh.android.dev`，证书 SHA-256 `814ab103…3622f`。E7E3 是**上游** `dsh.android.client` 期用的调试证书，与本 fork 无关，本项目任何包都不得用它签名。
- `standard`：minSdk 30，系统 WebView，构建任务 `assembleStandardRelease`。源码树里还留着 `low` flavor（minSdk 23，带 GeckoView 143）与 `tools/build-low-proot.py`，但**该版本从未发布**，不是分发目标；对外文档不描述它，`docs/android-low.md` 属上游历史材料。
- 离线 rootfs（`assets/offline-rootfs.bin`）**不提交**，由准备脚本生成；APK 用 `offline-rootfs.layout=split-runtime-v1` 标记 Ubuntu 与 `dsh-runtime.bin` 分包，构建核验两份摘要。
- 新 dsh 依赖由 `tools/dsh-runtime/package-lock.json` 锁定；`tools/prepare-runtime-descriptor.py` 生成独立受管契约描述，APK 版本仅作诊断来源。相同基础版本更新受管树，个人数据保持原位；**不因 UI-only APK 更新替换环境，不因普通 dsh 更新递增 Ubuntu 基础环境版本**。
- 离线 curl / git / 证书由 `tools/ubuntu-tools/packages.lock.json` 锁定（`tools/prepare-ubuntu-tools.py` 生成 `ubuntu-tools.bin`）；网页 ES 兼容依赖锁在 `tools/web-compat/`（`node tools/prepare-web-compat.mjs`）。生成文件不提交，构建核验摘要。
- 中英文界面：文案目录 `tools/i18n/messages.json`，构建生成 Java 文案字典；偏好 `system`（默认）/ `zh` / `en`；**系统语言必须在进程最早时刻锁存**（`SystemLanguage.initialize()`，早于任何 `Locale.setDefault`），否则「跟随系统」切一次就自我锁死。语言切换只重建界面，不停终端或 Web；用户输入、命令原文不做自动替换。
- 旧 WebView 的 `AbortSignal.any/timeout` 与 `crypto.randomUUID` 补齐：兼容脚本须进入受管 HTML 的应用脚本之前，并覆盖文档起始与 Worker。

### 数据与备份

- **自动备份默认开启**（2026-09-17 要求，覆盖更早的禁用规则）：`AutomaticBackups` 支持每日指定时间、1–168 小时间隔、停止后三种模式（`util/AutomaticBackupPolicy` 有单测）；到期仍在运行则延后，不强停 Web / 终端；保留最近 3 份已验证自动副本，手动与未知记录不自动删除。
- 用户导出 v5 使用无需密码的 `DSHA-data-v5-<UUID>.tar.gz`，封装 DSHADATA 完整性载荷；内部自动副本仍加密，旧加密原件读取仍需原密码并完整认证。原生 API Key 默认排除；先完整性/认证核验再预检，只写私有编号槽位。本机授权状态不能从用户归档生效；受管脚本、可执行配置和未知插件先隔离。
- 数据格式不能由 APK 或 dsh 版本号推导：`DataFormatEvidence` 对未经完整检查的数据保留 unknown；发件人声称的已验证格式不能成为删除原件的依据。
- 覆盖更新闲时清理可再生缓存及多余副本：保留至少两份健康且字节符合计划的副本，修改过或含额外文件的原件不删除；新重建通过核验后建立 `retired-proof.json` 再清理 `previous-linux`。
- 完整格式化的生产入口与擦除后端已退休，不恢复旧清理流程。外置工作区维护只断开私有引用，不遍历、覆盖或删除其内容；合法缓存清理仍须受控私有目标与 NOFOLLOW 核验。
- 覆盖安装用原包名、同签名、非调试正式包，做非破坏性检查；不在正式数据上运行强杀、删 Bash、坏插件等故障注入。

### 运行时与更新

- 新受管更新使用 `ManagedRuntimeTransaction` / `HostDataTransaction`；真实隔离 `RuntimeTrial` 核验静态资产 / 原生模块、实际端口 / 鉴权、存储和会话写后重开、网页内核与后端握手及 guest 退出后才能提交。回执保存在 rootfs 外并绑定文件摘要；至少保留直接健康前代。
- `RuntimeTrial` 必须记录实际 `runtimeMode`。所选 proroot 在鉴权前明确退出且无插件故障时，可按 `WebRuntimeFallback` 仅重试一次 proot；**不能把 proot 成功报告成 proroot 原生成功**。静态检查先选 proot，慢启动不触发重试。
- `RuntimeTrialRecords` 只轮换已确认关闭的现场：保留最近 3 条成功和 5 条失败；未关闭或标记异常的目录不得自动删除，也不能以累计次数设永久上限。
- 就绪检查必须解析实际 `/bin/bash` 的 ELF 和加载器路径；可执行位用 lstat（受 Android W^X 影响的 canExecute 不可靠）。损坏系统不得反复执行配置安全启动，应进入环境修复。
- 当前插件策略允许未锁定依赖解析、生命周期脚本与 pnpmfile；链接/本地包/更新通过格式、路径、实际依赖与摘要及事务检查后自动提交启用。用户主动禁用与安全模式意图保持，不恢复旧原生审阅门槛。`plugin-transactions.py` 记录候选与原件，未提交日志继续进入维护门禁。
- 系统插件与用户插件分层：系统插件源码不进用户备份，由当前 APK 按精确受管证明重建；`.disabled` 与旧实体冲突时禁用意图优先。
- `NARB_DISABLE_NATIVE_CACHE=1` 让原生扩展直接从随包目录加载（默认缓存在 `--link2symlink` 下首次悬空）。

### Web / 桥 / 终端

- 主Web从当前受管dsh包装和固定包内入口启动，加载共享RuntimeTools环境。默认自动端口`--port 0`，成功鉴权后记录实际端口；显式手动配置按当前选择策略处理。完整环境与入口见[运行机制](docs/runtime-data-plugin-architecture.md)，不复制旧固定3080命令。proot从nativeLibraryDir执行，不能移到filesDir绕过Android W^X。
- `WebPortPolicy.choose`在启动前选择固定/本机备用/动态端口；备用记忆仅本机，不跨设备迁移。当前生产未接入`retryBindRace`，不得把helper及单测写成已实现的绑定竞态自动重试。鉴权、保活与LAN使用实际端口，不按端口猜PID终止，见[端口专页](docs/ports-and-networking.md)。
- Web 启动等待鉴权不设强制终止时限（60 秒仅提示）；停止与维护必须共用 `WebProcessManager` 的 PID 身份 / 出生身份核验。
- 3090 桥协议版本做特性检测（`/app/version`，`BRIDGE_PROTOCOL=2`）；插件判版本用 `>=` 而不是 `==`。命令查询串预算不得缩到低于 8192 字符需求。
- LAN 正文由方法、状态码和明确传输边界决定；只有真正验证过的 101 WebSocket 握手可切隧道；不把 hop-by-hop 头移除后继续发送不匹配的编码体。
- PTY 出生身份在原生 fork/exec 握手中登记：子进程自读 stat，父进程确认后才 exec；不得退回 Java 启动后单次读取。PTY 与简易终端独立标签和会话，跨切页 / 旋转 / 语言切换保持进程；关闭单个标签必须核验该会话退出后再移除。终端会话 ID 永久递增，显示编号独立复用最小空缺。

### 应急 / 虚拟屏 / 设备

- **独立应急 DSH**：`recovery/` 不经过正式环境的迁移、数据绑定及全局启动锁；归档由 `tools/recovery-runtime/lock.json` 单独锁定；应急 Profile 仅有五个受控修复工具。不能用「原生安全 Profile」替代独立运行根。`RecoveryRepairBroker` 的 HTTP 接口不能确认写入：原生确认绑定候选、源摘要及数据代次，再经停止屏障和宿主事务。
- 应急资产去重：`recovery-asset-locations.json` 仅映射物理位置；仅当正式归档 SHA 与独立应急锁完全相同才共用包内字节，解压运行根仍独立，不读取正式 rootfs 作为救援依赖。
- **虚拟屏**（Standard，API30+）：App持有受管Core。raw坐标输入要求最新已观察帧；semantic节点/editor与anchored动作各有独立身份和目标复核，不强制像素静止、不静默互相fallback。UNKNOWN不重放，详见[架构](docs/virtual-screen-architecture.md)和[ADR0003](docs/adr/0003-virtual-screen-lifecycle-and-input.md)。
- **麦克风**：清单同时声明 `RECORD_AUDIO` 与 `MODIFY_AUDIO_SETTINGS`；由 `BrowserMicrophone` 按网页请求申请，不能在普通启动时预授权；只放行当前本机页面的纯音频请求，摄像头 / 屏幕音频拒绝；旧回调不能批准新页。
- **设备验收经验**：`uiautomator dump` 会抑制其他无障碍服务；截图授权绑定 DSH generation，停止 / 断连 / 撤销后失效；截图存应用私有 Pictures/DSHA，无需所有文件访问；PiP 可能盖住底部控件，自动化必须核对实际可见区域与屏幕方向；截图 / 读屏不可将敏感值写入公开取证文件。
- Shizuku 必须注册 `rikka.shizuku.ShizukuProvider`；标准版 13.1.5 / 兼容版 12.2.0（不用 overrideLibrary 掩盖 minSdk 24）。回调严格核对管理器 UID、Binder 描述符、单次请求与超时。
- 内置移动插件 `dsh-web-mobile` 为 3.3.5，固定上游 main `646fe837440f9939228bdba0024d407eaac01128`；`tools/apply-mobile-client-patches.mjs` 管理本地差异，不恢复上游已撤回的视口改动；上游已接管的 rc1 导航补丁不要重新套回。

---

## 启动契约（不可破坏）

- `welcomed == false` → `WelcomeActivity` → 点开始 → `MainActivity`；`MainActivity` 进入前校验 `welcomed`，否则永远回 Welcome。
- 正常运行检查 `.offline-extracted` 与完整环境身份。维护页允许进入受限主界面查看配置和日志；**此入口不能伪造就绪标记**，终端、Web 与插件执行仍须通过环境门禁。
- 启动失败自动进入原生 `StartupRecoveryActivity`；等待鉴权本身不是故障。最近五次脱敏启动记录独立保存在私有目录。
- 兼容重试仅在 proroot 已确认退出、鉴权前且无明确插件故障时进行一次，**不能由超时触发**。
- 配置快照由宿主 `ConfigurationSnapshots` 执行：正文逐文件存于 rootfs 外，保留三份健康与三份修复前快照；旧日志已提交后不得覆盖后来修改的配置。
- DocumentsProvider 保留 `root` 和 `linux/ubuntu/...` 的既有不透明文档 ID；guest 绝对软链接按 rootfs 解析，删除链接不递归目标；写文件先验证已打开的文件描述符再截断。
- 短信查询属于独立敏感能力：只允许当前 Android 用户的严格 `content query`；原生预授权默认关闭、可撤销、不从系统备份恢复。

---

## 已知 trap（搬自原版，骨架已按此设计）

- **停止靠 pid 文件 + 出生身份，不靠端口反查**：`/proc/net/tcp` 非 root 读不到（静默空），`/proc` 有 hidepid。启动时 `echo $$ > /root/.dsha-web.pid` 再 `exec node`；停止先写哨兵 `/root/.dsha-stopped`（看门狗见到就退出，否则「秒复活」）。旧 PID 复用按内核 `kill(pid,0)` + 出生身份二次核验，不得按裸 PID / 端口 / 名称强杀。
- **app 私有目录禁 `link(2)`**（SELinux）：proot 必须带 `--link2symlink`；`PROOT_L2S_DIR` 在 rootfs 内的 `.l2s` 必须绑定到相同宿主绝对路径，否则 dpkg 安装对硬链接 chown/stat 会报文件不存在。
- **两把签名钥匙各管一件事**：线上 APK 用本 fork 发布证书（`814ab103…3622f`，`keystore/release-signing.store`，alias `dsha-release`），增量更新清单用独立 keystore，绝不混用。换钥 = 逼用户卸载重装丢数据。
- Android 的 `FileInputStream(FileDescriptor)` 不接管传入描述符：宿主备份通过 `ParcelFileDescriptor` 自动关闭流明确转移所有权。
- 数据维护先关闭 PTY 与简易终端再取 `RuntimeTasks` 屏障；proroot 终端按本次独立会话核验并回收 guest，不能只结束启动器就释放工作锁。
- 维护成功文案不能代替就绪检查；未就绪时留在原生页，不自动跳回循环。维护页忙状态不使用插件查询 / 终端等通用锁冒充数据维护。

---

## 交付与验收

- **发布通道只有一条**：本仓库 `main` 的 [updates.json](updates.json) + GitHub Releases（`steveneng2020/DSH-Android`）。
  不改上游仓库、不向其发 Release、不部署官网。发布步骤见 [UPDATES-HOWTO.md](UPDATES-HOWTO.md)。
- **必查项**（缺一项就不算发布完成）：包名 `dsh.android.dev`、证书 `814ab103…3622f`（v1/v2/v3）、
  `debuggable=false`、minSdk 30、arm64-v8a、`versionCode` 严格大于 `updates.json` 里的已发布值、
  资产/许可/ELF/插件与独立应急门禁、`sha256` 与字节数与 Release 附件逐字节一致。
- **验收范围如实声明**：本机验证不得扩写成「全部设备矩阵通过」。虚拟屏、无障碍、厂商 ROM
  等按实际设备证据逐条写，没跑就写没跑。
- 大生成归档（rootfs / dsh-runtime / ubuntu-tools）不入 Git，构建现场生成并核验摘要；
  私钥、用户数据、设备截图与日志不上传。

## 编码约定

- 注释与 UI 串用中文；提交信息用中文 + `type:` 前缀说明原因。
- 每个协作者单一职责；纯逻辑抽到 `util/` 并配测试；不改历史 SharedPreferences 键名。
- 匹配现有风格：try/catch 包住有风险操作、优雅降级、失败 toast 给用户。
- 原生按钮和选项统一居中与字体边距；普通卡片、主按钮及文字状态共用主题资源，不用独立渐变或硬编码颜色制造同类框色差。布局修订跑 `LayoutAuditInstrumentation` 的 style 中英文验收（日夜、短屏、1.3 倍字体）。
- 应用弹窗统一 `DshaDialogBuilder`，自定义内容必须能在短屏和大字体下滚动；应用状态经 `UiStateText` 按显示边界重新渲染，不缓存语言。
- DNS 默认 `auto`：Node 双栈 `lookup` 仅在 `EAI_AGAIN` / `EAI_FAIL` 时重试一次 IPv4，不重放 HTTP 请求，不降级显式 IPv6；配置页另有 `ipv4`（glibc `no-aaaa`）与 `native`。Web、插件、shell 与 PTY 共用 `RuntimeTools` 的预加载环境。

---

## 文档与流程参考

| 文档 | 内容 |
|---|---|
| [BUILD.md](BUILD.md) | 环境（JDK 17 / SDK 37 / NDK 26 / Python 3.9+）、构建、签名与发布交付流程 |
| [docs/security-model.md](docs/security-model.md) | 安全模型与已知弱点 |
| [docs/plugins.md](docs/plugins.md) | 插件安装、打包契约与验证范围 |
| [docs/releases/](docs/releases/) | 各版本发布说明与真机验收记录（新版本验收写这里） |
| [CHANGELOG.md](CHANGELOG.md) | 完整更新记录 |
