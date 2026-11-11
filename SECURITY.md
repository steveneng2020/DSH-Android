# 安全策略 / Security Policy

> 本文件适用于 **本 fork（[steveneng2020/DSH-Android](https://github.com/steveneng2020/DSH-Android)）**，
> 不适用于上游 [DSH-APP/DSHA](https://github.com/DSH-APP/DSHA)。
> 上游有自己的安全策略与维护渠道，请勿把本仓库的策略套用到上游。

---

## 报告漏洞 / Reporting a Vulnerability

**请不要用公开 Issue 报告安全问题。** 公开 Issue 会在修复前暴露攻击面。

### 推荐方式：GitHub 私密漏洞报告

1. 打开 <https://github.com/steveneng2020/DSH-Android/security/advisories/new>
2. 填写复现步骤、影响范围、你的联系方式
3. 该通道仅仓库维护者可见

### 备用方式：邮件

- 邮箱：**steveneng@163.com**
- 邮件标题建议以 `[SECURITY]` 开头
- 请包含：受影响的版本（`versionName` / `versionCode`）、复现步骤、影响评估

> 若涉及**开源许可 / 著作权**而非技术漏洞，也走同一邮箱，标题写 `[LICENSE]`。

---

## 我们承诺 / What to Expect

| 阶段 | 目标时间 |
|---|---|
| 确认收到 | **7 天内** |
| 初步评估（是否成立、影响范围） | **14 天内** |
| 修复或缓解措施 | 视严重度，**30–90 天** |
| 公开披露 | 修复发布后，与报告者协商署名 |

- 我们会在修复版本发布后，于 `docs/releases/` 的发布说明中记录（不含利用细节）。
- 若你希望匿名，请在报告中说明。
- 本项目为个人维护的社区 fork，**没有赏金计划**，但会在发布说明中致谢（除非你要求匿名）。

---

## 支持范围 / Supported Versions

只支持**本仓库 Releases 中的最新版本**。

| 版本 | 是否支持 |
|---|---|
| 最新 Release | ✅ 接受报告并修复 |
| 上一个 Release | ⚠️ 视情况（重大安全问题会修） |
| 更早版本 | ❌ 请先升级 |
| 上游 `DSH-APP/DSHA` 的版本 | ❌ 请报告给上游 |

> 本 fork 与官方包名不同（`dsh.android.dev` vs `dsh.android.client`），
> 报告时请确认你用的是**哪个包**：`adb shell pm list packages | grep dsha`。

---

## 本项目已知的安全边界（不是漏洞）

这些是**已记录的已知限制**，不作为漏洞受理，但欢迎讨论改进方案：

| 边界 | 说明 | 详见 |
|---|---|---|
| 无内核级沙箱 | bubblewrap 需要 unprivileged user namespace，Android sepolicy 不提供 | [README › 已知限制](README.md#已知限制) |
| 默认 `danger-full-access` | agent 默认拥有容器内完整权限，可在配置页改为 `workspace-write` / `read-only` | [安全模型](docs/security-model.md) |
| 容器内 root ≠ Android root | `proot` 的 `-0` 只是 uid 映射，不代表获得宿主机 root | [安全模型](docs/security-model.md) |
| 无障碍 / ADB / Shizuku 通道 | 均为用户显式授权，默认关闭，可随时撤销 | [设备权限架构](docs/device-permissions-architecture.md) |
| 历史明文备份 | 旧格式备份可能未加密；新 v5 导出为完整性归档（非加密） | [v5 备份格式](docs/backup-format-v5.md) |
| 签名密钥轮换 | 历史签名密钥需轮换，属已知待办 | 维护者内部跟踪，不接受外部报告 |

> 完整的安全模型（每项权限到底暴露什么）见 **[docs/security-model.md](docs/security-model.md)**
> 与英文版 **[docs/security-model.en.md](docs/security-model.en.md)**。

---

## 我们不会做的事

- ❌ 不会在 APK 中植入遥测、后门或未声明的网络请求（更新 / 插件下载 / 模型调用除外）
- ❌ 不会上传你的日志、会话或设备数据
- ❌ 不会伪造官方签名（本 fork 使用**自己的**签名证书，绝不冒用官方 E7E3）
- ❌ 不会以官方名义发布或收费

---

## 依赖与第三方组件

本 APK 包含大量第三方组件（含 GPL-2.0 的 `proot` 二进制）。若你发现**许可合规**问题
（而非技术漏洞），请见：

- [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) —— 完整第三方声明
- [GPL-SOURCE-OFFER.md](GPL-SOURCE-OFFER.md) —— GPL 源码获取的书面要约
