# App 内更新清单维护说明

App 的「检查更新」读取本仓库根目录的 [`updates.json`](updates.json)：

```
https://raw.githubusercontent.com/steveneng2020/DSH-Android/main/updates.json
```

## 发布新版本的四步

0. **先把正式包输出到 `builds/`**：`python3 tools/export-release-apk.py`
   （校验包身份与签名后复制 + 写 `.sha256`；详见 [BUILD.md](BUILD.md)）。
1. **删除旧 Release**（`../.push-to-github.sh` 已自动处理，含同名 tag）
   旧包与新版 versionCode 常常相同，留着会让更新检查指向旧包。
2. **上传新 APK** 到新 Release，记录它的 `sha256` 与字节数。
3. **改 `updates.json`**：
   - `versionCode` 必须 **大于** 已发布版本，否则 App 判定「暂无更新」
   - `version`、`url`、`sha256`、`bytes` 与新包一致
4. **提交并推送** `updates.json` 到 `main`（App 从 `main` 分支读取）。

## versionCode 编码规则（不要简单 +1）

```
2  00  05  0  190
│   │   │   │  └── 上游构建版本号（完整 3 位：190）
│   │   │   └───── 连接位，固定 0
│   │   └───────── 正式版顺序号（05 = 第 5 个正式版）
│   └───────────── 固定 00
└───────────────── 渠道位：2 = 正式版，1 = 测试版
```

**两条规则**：
1. **顺序号**是本项目第几个正式发布版，连续递增。
2. **末三位**是所基于的上游构建号，改版本时**不动它**。
3. **测试版只改渠道位**：前 4 位 `2005` → `1005`，其余完全相同。

### 已发布版本对照

| 版本 | versionCode | 顺序号 | 说明 |
|---|---|---|---|
| v1 | `20010190` | 1 | 首个正式版 |
| v1.1 | `20020190` | 2 | |
| v1.2 | `20030190` | 3 | |
| v1.3 | `20040190` | 4 | |
| **v1.4** | `20050190` | 5 | 当前版本 |
| v1.5（计划） | `20060190` | 6 | **不是 `20050191`** |
| v1.4 测试版 | `10050190` | 5 | 只改渠道位 |

> 以上 `v1`~`v1.4` 的 versionCode 均取自 `builds/` 下真实 APK 的 `aapt2 dump badging`，非推算。

## 字段约束

`UpdatePolicy.Release.valid()` 会逐项校验，任一项不过就被丢弃：

| 字段 | 约束 |
|---|---|
| `versionCode` | > 0 |
| `version` | 通过版本名校验；`@` 前私有段形如 `DSHA vN ` 判 stable，含 `-` 判 preview |
| `channel` | 只能是 `stable` 或 `preview` |
| `flavor` | 只能是 `standard` 或 `low` |
| `minSdk` | 23–100 |
| `abi` | 只能是 `arm64-v8a` |
| `url` | 必须是 `https://github.com/steveneng2020/DSH-Android/releases/download/` 下的 `.apk` |
| `pageUrl` | 必须是 `https://github.com/steveneng2020/DSH-Android/releases` 或其 tag 页 |
| `sha256` | 64 位十六进制，下载后逐字节校验 |
| `bytes` | > 0，且不超过上传预留上限 |

## 为什么不再用上游的 `dsha.cc`

上游更新通道不索引本项目的包，且自 2026-11 起 TLS 握手直接断开
（`SSL routines::unexpected eof`）。因此白名单已切换到本仓库；旧域名不再被接受。
