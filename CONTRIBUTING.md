# 构建、验证与提交

> **本文件只针对 fork（[steveneng2020/DSH-Android](https://github.com/steveneng2020/DSH-Android)）。**
> 上游 [DSH-APP/DSHA](https://github.com/DSH-APP/DSHA) 另有其流程，不要混用。
> 包名 `dsh.android.dev`、证书 SHA-256 `814ab103…3622f`，与上游 `dsh.android.client` / E7E3 互不通用。

先读 [README](README.md)、[AGENTS](AGENTS.md)、[BUILD](BUILD.md)。
项目特有操作见[接手指南](docs/接手指南.md)，约束见[工程规范](docs/engineering-standard.md)。


## 源码与工具身份

Java 17，单模块 `:app`，纯 Java（0 个 .kt）。只发布 `standard`：minSdk 30、系统 WebView、arm64-v8a、包名 `dsh.android.dev`。源码树里的 `low` flavor（minSdk 23、Gecko）从未发布，不是分发目标。

- 应用版本及固定文件名规则：`app/build.gradle`。
- DSH 版本及 npm 内容：`tools/dsh-runtime/package.json`、`package-lock.json`。
- 随包工具：`tools/runtime-tools.lock.json`。
- 内置插件：`app/src/main/assets/builtin-plugins.json`。
- 运行期补丁 active/specialized/retired：`app/src/main/assets/runtime-patches.json`。
- 独立应急归档：`tools/recovery-runtime/lock.json`。正式环境更新不能擅自替换独立应急锁。
- CI 工具与历史发布证书：`ci/toolchain.lock.json`、`ci/release-identity.json`。

可规范化源码使用实际LF，19项必要小型二进制及历史原件保持原字节。`.gitattributes`列出的12项managed/canonical精确bytepin不做行尾转换；不要全库改写或通过忽略换行的哈希掩盖包内内容变化。生成的Java、描述符和证明由对应脚本生成，四处UUID调用补齐共享Ids依赖，保持历史UUID格式。

## 准备输入

APK的约85MB offline-rootfs是经过打包变换的层，不能还原约304MB原始rootfs；本轮不提供“从APK恢复全部构建输入”的helper或承诺。完整源码ZIP的最终SHA-256写在Release正文，不放进该ZIP自身README形成自引用。

完整源码保留构建必需、已有跟踪且具备notice/锁的小型JNI/vendor/解释器预编译依赖；来源未知或闭源限制照实披露，这不等于所有vendor native均可从源码复现。按实际材料说明来源、许可与构建路径，不为“纯源码”口号删除构建消费者依赖。保留清单还包括27个必需历史构建源码和唯一website测试夹具，不进行网站部署。

不上传私钥、用户数据、设备截图/原日志或历史审计原材料。大生成归档不入Git，Release源码ZIP只收登记并核验的原始大构建输入。`docs/audits/`的JSON仅保留以下9项，维持原路径：前6项为构建/CI消费元数据，后3项为真实历史文档保存/来源元数据。它们不是设备原日志，也不是开放整个历史审计目录的例外：

- `docs/audits/build154/retired-audit-sources.json`
- `docs/audits/build154/engineering-retired-sources.json`
- `docs/audits/build156/retired-test-control-sources.json`
- `docs/audits/build156/third-party-license-sources.json`
- `docs/audits/build156/retired-asset-sources.json`
- `docs/audits/build156/retired-environment-data-sources.json`
- `docs/audits/build154/history-document-sources.json`
- `docs/audits/build156/shellservice-source-provenance.json`
- `docs/audits/build156/source-docs-retained.json`

文档闭合另按[文档总索引](docs/documentation-index.md)中的精确清单纳入6篇真实历史说明、已追回并核对原摘要的Termux历史README及5份本轮新建导航副本。导航副本逐字节复制指定原文，不伪称追回的历史保存件；旧历史原件和上游许可证不改写。其余历史JSON台账、设备原始日志/截图与私有取证不因正文引用自动纳入。

完整生成入口：

```bash
python3 tools/prepare-dsh-runtime.py
python3 tools/build-standard-runtime.py
python3 tools/prepare-ubuntu-tools.py
python3 tools/prepare-runtime-tools.py
python3 tools/generate-builtin-plugins.py
python3 tools/generate-credential-paths.py
node tools/prepare-web-compat.mjs
python3 tools/prepare-backup-assets.py --write
python3 tools/prepare-runtime-descriptor.py --write
python3 tools/prepare-test-runtime.py
```

基础 Ubuntu 原始归档仍是单独固定输入，不能把依赖安装或 dsh 升级误当成基础环境版本升级。独立应急的历史 pinned 副本要保留，不能因正式归档变化自动解除摘要核对。

## 验证

源码快速层不依赖私钥：

```bash
python3 tools/run-host-tests.py --check-manifest
python3 tools/run-host-tests.py --stage fast
python3 tools/check-source-hygiene.py
```

完整输入准备后，运行当前正式源集的单测和 Release Lint：

```bash
./gradlew :app:testStandardDebugUnitTest :app:lintStandardRelease
python3 tools/verify-stability.py --stage software
python3 tools/run-host-tests.py --stage runtime
```

不能运行 AGP/aapt2 的宿主可以使用 `tools/run-unit-tests.py` 作为纯逻辑后备；它编译测试辅助类，但不替代 Android 构建。`-O` 测试被入口拒绝，发布核验的检查也不会被 Python 优化删去。

`ci-fast` 执行源码和协议检查。完整包 `ci-package` 需要核对过的二进制输入，并且只生成未签名包；不得用于安装。仓库保护、线上工作流完成和实际 Linux/Android 矩阵必须以真实运行证据记录，不由配置文件推导。

## 正式打包

显式配置 `DSHA_KEYSTORE`、`DSHA_KEYSTORE_PASSWORD`、`DSHA_KEY_PASSWORD`，可另设 `DSHA_KEY_ALIAS`。缺少口令不隐式使用缺省值。只允许本 fork 发布证书（`814ab103…3622f`，alias `dsha-release`），不换成 debug 或临时 CI 证书；**E7E3 是上游证书，不得使用**。

```bash
./gradlew :app:assembleStandardRelease
```

发布 `standard`，实际包必须核对 `dsh.android.dev`、证书 `814ab103…3622f`（v1/v2/v3）、`debuggable=false`、minSdk 30、arm64-v8a、资产、许可、ELF、插件与独立应急门禁。测试与 Lint 结果按当次实际执行记录，不称完整冷网络已验。

本轮暂停所有手机操作，不安装、启动、停止、输入或对话，不为补证重新连接ADB。历史同签名覆盖记录保留原包归属，不转记新包；不卸载、不清数据、不注入故障、不生成额外审计APK。

发布通道只有本仓库 [`updates.json`](updates.json) + GitHub Releases：上传 APK → 更新 `updates.json`
（`versionCode` 严格大于已发布值）→ 推送 `main`。不改上游仓库、不向其发 Release、不部署网站。
没有实际 tag/上传结果前不声称发布完成。

## 修改与评审

分支默认 `codex/`。保持旧 SharedPreferences 键、数据格式读取、文档 ID、原件与未知进程停止屏障。明确记录更改的职责、持久化字段、协议和验证证据。

修缺陷要用实际生产入口或隔离真实依赖重现；源码约束检查和设备运行证据分别记录。原始数据只读，历史记录标版本与时间；没有硬件证据的情况不写成已验证。所有审计项都有处置和残余，不能用一个白名单或未经校准的分数宣称债务已清。

修改前按[文档总索引](docs/documentation-index.md)定位实现、平台依据和测试；涉及默认值/权限/网络时同步维护专页与迁移说明，不只更新代码注释。
