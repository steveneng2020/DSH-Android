# GPL / LGPL 源码获取要约 · Source Offer

> 本文件是 DSHA（[`steveneng2020/DSH-Android`](https://github.com/steveneng2020/DSH-Android)）
> 对随 APK 分发的 GPL 与 LGPL 组件所做的**书面要约**，依据 GPL-2.0 第 3 条与
> LGPL-3.0 第 4(d) 条。它回应 [SECURITY.md](SECURITY.md) 中「许可合规问题」的指向。

## 一、适用范围

本要约仅覆盖下列以二进制形式随 APK 分发的组件。**DSHA 自有代码是 MIT**，不在本要约范围内。

| 随包二进制 | 许可 | 来源 |
|---|---|---|
| `libproot.so` | GPL-2.0 | Termux 分支 proot |
| `libprootloader.so` | GPL-2.0 | Termux 分支 proot |
| `libprootloader32.so` | GPL-2.0 | Termux 分支 proot |
| `libtalloc.so` | LGPL（家族，具体版本待核） | Samba talloc |

另有 `libproot_legacy.so`、`libprootloader_legacy.so`（GPL-2.0），仅属于源码树中的
`low` flavor —— 该 flavor **从未发布、本项目不分发它**，因此不构成分发行为；若你自行构建，
需自行承担相应义务。

完整的第三方组件清册见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)：
该文件由 `python tools/generate-third-party-notices.py` 从实际锁与资产生成，
`--check` 会在漂移时报错，因此它比任何手写清单更可信。

## 二、要约内容

**我们向任何收到本 APK 的主体提供上述组件对应的完整源码**，收取的费用不超过我们实际执行
源码分发的成本（通常为 0）。获取方式：

1. **首选：直接取上游源码。** proot 为 Termux 分支的公开项目，talloc 为 Samba 子项目，
   两者源码均可从其上游仓库或其发行版源码包获得。这种方式最快，且拿到的就是未经我们改动的原版。
2. **要 DSHA 这一侧的材料**（例如我们针对 API 23 的构建脚本与本地改动）：
   在本仓库提交 Issue，标题注明 `GPL source offer`，并写明你收到的 APK 版本
   （`versionCode` 或 `versionName`）。我们会在仓库中追加对应材料，或给出可下载地址。

## 三、溯源结论（2026-11-11 核实）

本节说明这些二进制到底来自哪里，以及**哪些点已经证明、哪些还不能证明**。
逐项细节与可复核的摘要记录在 [`tools/gpl-binaries.lock.json`](tools/gpl-binaries.lock.json)，
由 `python3 tools/check-proot-provenance.py` 守着：磁盘上二进制一变就会红。

| 二进制 | 许可 | 上游版本 | 版本依据 |
|---|---|---|---|
| `libproot.so` | GPL-2.0 | termux/proot **v5.1.107.91** | 二进制内嵌 `v5.1.107.91`，由 Termux 构建脚本 `-DVERSION=` 写入 |
| `libprootloader.so` | GPL-2.0 | termux/proot **v5.1.107.91** | 与 `libproot.so` 同一 Termux 包、同一工具链（clang 17.0.2 r487747d） |
| `libprootloader32.so` | GPL-2.0 | termux/proot **v5.1.107.91** | 同上，32 位 loader 变体 |
| `libtalloc.so` | **LGPL-3.0** | Samba talloc **2.4.3** | 工具链为 clang 19.0.1；Termux 当前 2.5.0 实测为 clang 22/21 构建，故不是 2.5.0 |

**已证明**：

- proot 三项的源码可从 `https://github.com/termux/proot/archive/v5.1.107.91.zip` 取得，
  实测 sha256 = `a7bc2fab34bf9a39073e8291f08a662e848c61a67494e59f5f84f5ca10690128`，与
  Termux 打包脚本登记值一致。
- 构建方为 `termux/termux-packages` 提交 `8ec1d20717`（2026-08-16），
  编译参数 `PROOT_WITH_LIBANDROID_SHMEM=true`、`-DARG_MAX=131072 -DVERSION="5.1.107.91"`，
  依赖 `libandroid-shmem`、`libtalloc`。
- talloc 源码可从 `https://www.samba.org/ftp/talloc/talloc-2.4.3.tar.gz` 取得，
  实测 sha256 = `dc46c40b9f46bb34dd97fe41f548b0e8b247b77a918576733c528e83abd854dd`，
  与 Termux 打包脚本登记值一致；该源码的 `LICENSE` 是 **LGPL-3.0**。

**仍不能证明（如实写出）**：

1. **proot 三项缺少同版本 deb 副本做逐字节比对。** Termux 官方池只保留最新
   `5.1.107.102`，`archive.termux.dev` 当前不可达，所以拿不到 `5.1.107.91` 的包。
   因此以上证明的是「由该源码版本、按该参数构建」，**不是**「与某个 deb 逐字节相同」。
2. **`libtalloc.so` 的版本是推定而非字节比对。** 依据是工具链差异与 Termux 版本时间线，
   2.4.3 的 deb 同样已下架，无法比对。
3. `libprootloader32.so` 是 32 位 loader 备用路径，本项目未验证它在运行期是否真的被加载。

换句话说：**源码要约现在指向确切版本，可复核；但二进制与发布包之间的逐字节对应仍缺一步。**
把缺口写出来比假装没有更有用。

## 四、与 MIT 许可证的关系

DSHA 自有代码以 [MIT](LICENSE) 发布。MIT 与 GPL 是不同层：本仓库整体不是 GPL 项目，
但**随包的 proot / talloc 二进制仍各自受 GPL / LGPL 约束**，不因 APK 顶层许可是 MIT 而改变。
分发这些二进制的任何人（不只是我们）都要自行履行相应义务。

## 五、维护

新增或替换上述任何二进制时，必须同步更新本文件与 `THIRD_PARTY_NOTICES.md`。
`tools/check-third-party-notices.py` 会拦截未登记的新 JNI 成员。
