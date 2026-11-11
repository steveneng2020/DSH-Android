# DSHA 构建说明

> **本文件只描述 fork（[steveneng2020/DSH-Android](https://github.com/steveneng2020/DSH-Android)）的构建。**
> 上游 [DSH-APP/DSHA](https://github.com/DSH-APP/DSHA) 有自己的构建文档，不要混用。
>
> 版本、包名与签名一律以 `app/build.gradle` 和 `ci/release-identity.json` 为准
> （`dsh.android.dev`，证书 `814ab103…3622f`），本文件不复制这些数字。

先读 [README](README.md)、[AGENTS](AGENTS.md)、[贡献流程](CONTRIBUTING.md)。
应用版本以 `app/build.gradle` 为准，DSH 依赖以 `tools/dsh-runtime/package.json` 与其锁文件为准。

## 环境与 flavor

| 输入 | 要求 |
|---|---|
| JDK / 语言 | Java 17，无 Kotlin（0 个 .kt） |
| Gradle / AGP | Wrapper 9.3.1 / AGP 9.1.1 |
| Android SDK | `platforms;android-37.0`、build-tools 36.0.0；compile/target API 37 |
| NDK | 26.3.11579264（只在改 JNI 时需要） |
| Python / Node | 生成器 Python 3.9+，CI 锁定版本见 `ci/toolchain.lock.json`；Node 24 |
| standard | minSdk 30，系统 WebView，arm64-v8a |

**只构建 standard。** 源码树里还留着 `low` flavor（minSdk 23，带 GeckoView），但它从未发布，
不是分发目标。

## 输入准备与证明

Git保留完整应用、资源、锁定生成/校验脚本，以及构建必需且有notice/锁的小型JNI/vendor/解释器预编译依赖；大型rootfs、DSH和recovery生成归档不入Git。来源未知或闭源的vendor限制按实际材料保留，不能宣称所有vendor native均可从源码复现。精确边界与9个显式审计JSON白名单见[CONTRIBUTING](CONTRIBUTING.md)：原6项构建输入元数据加3项历史文档/来源元数据，不开放整个audit目录。

可分发源码写LF原字节；`.gitattributes`中的12项managed/canonical bytepin及历史原件保留精确原字节，不能全库规范化已签名输入。小型二进制输入19项按清单保留，不以文本行尾规则改写。共享UUID校验由Ids提供，补齐四处调用依赖并保持历史格式。

Ubuntu基础环境身份独立于DSH与UI版本。`offline-rootfs.bin` / `dsh-runtime.bin`为split-runtime-v1，独立应急pinned输入由`tools/recovery-runtime/lock.json`约束，不能用正式环境作为救援依赖。没有大归档的源码检出不能直接当成完整APK，也不能跳过完整性门禁。

受管输入发生变化时，按实际生成入口更新资产，再显式生成证明：

```bash
python3 tools/prepare-backup-assets.py --write
python3 tools/prepare-runtime-descriptor.py --write
python3 tools/prepare-test-runtime.py
```

生成的证明需与真实字节核对；普通 Gradle 构建使用 check，不能靠旧缓存跳过新输入。当前夹具由 `app/build/test-runtimes/current.json` 及源/内容指纹约束，不能把任一旧目录称为当前运行时。

## 软件验证

```bash
python3 tools/run-host-tests.py --check-manifest
python3 tools/run-host-tests.py --stage fast
python3 tools/check-source-hygiene.py
./gradlew :app:testStandardDebugUnitTest :app:testLowDebugUnitTest \
  :app:lintStandardRelease :app:lintLowRelease
python3 tools/run-host-tests.py --stage runtime
python3 tools/verify-stability.py --stage software
```

Windows 使用 `gradlew.bat`，并以真实 Python 可执行文件代替不可用的系统别名。无法运行 AGP/aapt2 时，`tools/run-unit-tests.py` 是纯逻辑后备，不替代 Android 全编译、APK 或完整资源门禁。平台跳过、未运行项与 Lint 警告如实分类，不写成通过。

`tools/verify-plugin-upgrade-gate.py` 检查当前自动提交/启用、用户禁用与安全模式、实际依赖、插件事务及受管资产。正式插件允许未锁定解析、生命周期脚本和 pnpmfile；不能把历史“原生审阅/依赖冻结”的测试口径复活为当前要求。

## 正式打包与签名

显式提供已有 `DSHA_KEYSTORE`、`DSHA_KEYSTORE_PASSWORD`、`DSHA_KEY_PASSWORD`（可选 `DSHA_KEY_ALIAS`）。
签名身份以 `ci/release-identity.json` 为准：证书 SHA-256 `814ab103…3622f`，alias `dsha-release`，
与已装机包同签名，可覆盖安装。**E7E3 是上游 `dsh.android.client` 期的证书，与本 fork 无关，不得使用。**
密钥文件名含 debug 不表示正式 APK 可调试；必须核对实际 `debuggable=false`。

```bash
./gradlew :app:assembleStandardRelease
```

产物：`app/build/outputs/apk/standard/release/app-standard-release.apk`。

**正式版必须输出到 `builds/` 目录**（`/storage/emulated/0/Download/Eta/DSHA开发/builds`）：

```bash
python3 tools/export-release-apk.py            # 校验后输出 + 写 .sha256
python3 tools/export-release-apk.py --dry-run  # 只校验，不复制
```

该脚本会先核对包名 `dsh.android.dev`、证书 `814ab103…3622f`、`debuggable=false`、
minSdk 30、arm64-v8a、v1/v2/v3 签名，以及与 `updates.json` 的 sha256/字节数一致，
任一不符就拒绝输出 —— 防止把调试包或探针包混进 `builds/`。
命名规范 `DSHA-<版本>-<YYYYMMDD>-<HHMM>.apk`，日期时刻取产物 mtime 的**北京时间**。
交付前核对：包名 `dsh.android.dev`、证书 `814ab103…3622f`（v1/v2/v3）、`debuggable=false`、
minSdk 30、arm64-v8a、资产/许可/ELF/插件与独立应急门禁、`sha256` 与字节数。

**发布**（本仓库唯一通道，详见 [UPDATES-HOWTO.md](UPDATES-HOWTO.md)）：
上传 APK 到本仓库 Release → 更新 `updates.json`（`versionCode` 必须严格大于已发布值）→
推送 `main`。不改上游仓库、不向其发 Release、不部署网站。
私钥、用户数据、设备截图与日志不上传。

## 验收范围

手机操作按当前授权执行；不通过「正常 Stop」文案猜测已退出。Linux 侧软件检查不证明
持久磁盘/掉电/Android FUSE 行为，也不证明真实设备矩阵。虚拟屏、无障碍、厂商 ROM
等能力按实际设备证据逐条声明，未跑就写未跑。

维护源码前先看[项目总手册](docs/project-architecture-handbook.md)和[文档总索引](docs/documentation-index.md)；引擎、端口、DNS的当前默认值与历史迁移分别有专页。
