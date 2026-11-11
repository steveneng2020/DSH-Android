# DSHA

> ## About this project
>
> Repository: [`steveneng2020/DSH-Android`](https://github.com/steveneng2020/DSH-Android)
>
> Package `dsh.android.dev`, release key cert SHA-256 `814ab103…3622f`;
> installing over an existing build requires the same signature.
>
> **Current release**: `DSHA v1.4 20261111@0.2.2-rc.1` / versionCode `20050357`
> / standard flavor (minSdk 30, system WebView).
>
> What's new in this release (see [CHANGELOG.md](CHANGELOG.md)):
> 1. Fixed the blank startup page after upgrades, the unresponsive "Start DSHA" button, and occasional stalls on the recovery page.
> 2. Fixed maintenance getting permanently stuck on "stop Web and terminal tasks", where retrying did nothing either: the stop barrier could not recognise the container supervisor this app launches itself, treated it as an unidentified process and never released the barrier.
> 3. Fixed old instances staying permanently at "identity unknown" and refusing to start after an APK upgrade or downgrade: a superseded-build check now recognises a package swap as a definite expiry and routes into the install-and-repair page instead of hanging.
> 4. Added automatic reasoning-effort adaptation: models that declare no reasoning effort get the declaration filled in (DSHA does not guess which levels a third-party model supports; undeclared means no reasoning level is shown). Additive only, with an automatic config backup before writing.
> 5. The launcher icon is tappable to switch between six palettes; the change takes effect immediately and is remembered. The About page and About dialog share the same icon source, so tapping either opens the switcher, and the icon now fills its canvas.
> 6. Plugin capability hints gained a native dependency precheck: a read-only inspection of the ABI and file header of bundled native modules, warned about but never blocking installation.
> 7. Added the changelog panel: the About page shows releases in blocks and can expand all of them; the About DSHA dialog embeds the same changelog inline.
> 8. Added upstream comparison: shows whether the code differs from upstream, read-only and never written back.
> 9. The About page community entry now uses the contact email steveneng@163.com; the update page's "view releases in browser" and its stable and preview links point at this repository instead of the upstream release page.
> 10. Release identity stays independent: package dsh.android.dev with its own release certificate, not interchangeable with upstream dsh.android.client; in-place upgrade requires the same signature.
> 11. Single variant: the compatibility line and GeckoView are removed; only Standard ships (Android 11+, arm64-v8a, system WebView).
> 12. Merged upstream DSHA 0.2.2 (upstream build357), bundling DSH 0.2.2-rc.1 on Ubuntu base 10: mobile UI v5, a standalone device-capability authorisation page, the maintenance-time plugin registration deadlock fix, and every upstream commit since the previous merge (upstream v0.2.1-rc.2, upstream build190). The branch was rebuilt on a real upstream commit (5e2dca92, 2026-11-11), so future upstream updates merge directly instead of being force-fitted.
>
> **In-app updates read [`updates.json`](updates.json) from this repository**, with APKs served from GitHub Releases.


<p align="center">
  <b>DeepSeek Harness launcher for Android</b><br>
  Run the full <a href="https://github.com/deepseek-ai/deepseek-harness">deepseek-harness</a> on your phone — no root, no Termux, nothing to type
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
  <b>English</b> · <a href="README.md">简体中文</a> · <a href="CHANGELOG.md">Changelog</a> · <a href="SECURITY.md">Security policy</a> · <a href="docs/security-model.en.md">Security model</a> · <a href="AGENTS.md">AGENTS.md (for AI / contributors)</a>
</p>

> 🤖 If you are an AI agent or a new contributor, read **[AGENTS.md](AGENTS.md)** first
> (structure, startup contracts, traps we already fell into). Don't scan the whole repo.

> [English documentation](docs/en/index.md).

---

## The icon

<p align="center">
  <img src="docs/assets/icon/default.png" width="180" alt="DSHA icon: the kun">
</p>

The app icon is a **kun** — a single silhouette, no double jade ring, no gilded outline.

> There is a fish in the Northern Darkness, its name is Kun. Kun is so vast that no one knows how many thousand li it spans.
> — Zhuangzi, *Free and Easy Wandering*

The image fits what this project does:

- **Kun is a fish that can transform into a peng** — a constrained form does not bind it. Android was never built for glibc Linux, yet a complete Ubuntu environment runs inside a phone all the same.
- **"No one knows how many thousand li" is a question of scale, not of capability** — the same agent harness does on a phone what it does on a server, with nothing cut down for the smaller screen.
- **The Northern Darkness is a dark sea at the far north** — that the starting point is out of sight does not matter; Kun does not explain where it came from.

### Six colour schemes

Switch them under Settings → About DSHA by tapping the icon at the top of the page; the choice applies immediately and is remembered.

| Default (ultramarine · light gold) | Ink Jade | Sky Blue |
|:---:|:---:|:---:|
| <img src="docs/assets/icon/default.png" width="96"> | <img src="docs/assets/icon/moyu.png" width="96"> | <img src="docs/assets/icon/tianqing.png" width="96"> |
| **Ochre** | **Jade Green** | **Purple Ribbon** |
| <img src="docs/assets/icon/zheshi.png" width="96"> | <img src="docs/assets/icon/biyu.png" width="96"> | <img src="docs/assets/icon/zishou.png" width="96"> |

Across the six, the kun body lightness distribution is 3 dark / 1 mid / 2 light, and every pair meets the hue or lightness separation target; none clips under circular or rounded-rectangle masks.

## What this is

DeepSeek Harness (`@deepseek-ai/dsh`) is DeepSeek's official agent harness — think Claude Code.
It is written for glibc Linux, and running it on Android directly hits a wall of problems:
native modules that won't compile, `link(2)` blocked by SELinux, sandboxes that won't start,
and a front end laid out for desktop screens.

**DSHA wraps all of that into a single APK.** Install, prepare the environment, open Web UI —
no Termux, no root, not a single command. Inside is a complete Ubuntu environment: `apt` works,
interactive PTYs work, native modules that need compiling install fine — the same stack you'd
use on a server.

This project is maintained by [@steveneng2020](https://github.com/steveneng2020).

---

## Device compatibility

Check your phone against this before installing.

### Supported range

| Item | Requirement |
|---|---|
| **Android version** | **11 (API 30) and above** |
| **CPU architecture** | **arm64-v8a only** |
| Web engine | System WebView |
| Experimental virtual display | Yes |
| Package size | about 280 MB |

**32-bit devices and x86 / x86_64 emulators are not supported at all** — the APK carries arm64 native libraries and an arm64 Ubuntu environment.

### Known behaviour per system

| System | Status | Notes |
|---|---|---|
| **Xiaomi / Redmi (MIUI, HyperOS)** | Needs manual allowance | The accessibility service (screen reading, automatic taps) gets rolled back by the system: re-enable it under Settings → Accessibility and lift the "background pop-up" restriction for this app |
| **Android 13+** | Notification permission needed | Notifications are off by default; task notices and background alerts need to be allowed manually |
| **Android 11+** | Fully supported | Wireless pairing (ADB over Wi-Fi) works from 11 up |
| **HarmonyOS / anco** | Not verified | Expected to run; no on-device regression yet |
| **OnePlus / OPPO / vivo (ColorOS, OriginOS)** | Battery exception needed | The system reclaims background processes; whitelist DSHA under Battery → Unrestricted or long-running tasks will be interrupted |
| **Emulators (including Waydroid)** | Not supported | No arm64 native environment; even with translation, the kernel features proot relies on are usually missing |

### Three things to do after first install

1. **Grant "All files access"** — otherwise data stays in the app-private directory and is lost on uninstall.
2. **Whitelist the app from battery optimisation** — otherwise background tasks get killed.
3. **If you need screen reading or automatic taps**, enable "DSHA 配对助手" under Accessibility and keep it on when the system warns it may be closed.

> Everything above is measured or already documented system behaviour. A model not listed here is not necessarily unusable — it simply has no verified result yet.

---

## Download

Latest builds: **[Releases](https://github.com/steveneng2020/DSH-Android/releases)**.

Current release: **`DSHA v1.4 20261111@0.2.2-rc.1`** · Standard · Android 11+ / arm64 · **303.18 MiB**

- Package `dsh.android.dev`; installing over
  an existing build requires the same signing key (cert SHA-256
  `814ab1037fb25c781236809c7dffff1a101385ae245b6d5b55b767e44e63622f`).
- **Environment**: bundled DSH `0.2.2-rc.1`, mobile UI `v5`; **proot** by default, **proroot** optional.
- **Backup**: one-tap backup/export; user data preserved.
- **Changes this release**: 12 items, see [CHANGELOG.md](CHANGELOG.md).

> **In-app updates**: the feed is [`updates.json`](updates.json) at this repository root,
> with APKs served from GitHub Releases.

### Getting started

1. Install the Standard APK. First launch prepares the bundled offline environment.
2. Enter the home screen after extraction; Web startup runs in the background. Open Web UI when it is ready and configure the model there.
3. Before migrating from the old package, export your backup and restore it in the new app. For later same-package updates, stop DSH normally before installing the signed APK.

The exact APK has scoped Android 13 checks for both runtimes, retained conversations, plugin state and immediate screen-off startup. Page latency still varies; this is not a universal performance, Doze, power or all-device guarantee. See the [changelog](CHANGELOG.md) and [known limits](#known-limits). [Download verification](docs/download-verification.en.md).


---

## Why DSHA

|  | What you get |
|---|---|
| 🚫 **Zero command-line barrier** | Offline Ubuntu rootfs bundled in the APK. No Termux, no pkg, nothing to type |
| 🐧 **Full glibc environment** | Not a trimmed distro: `apt` / PTY / native modules / Python / git all included. Third-party plugins run unmodified |
| ⚙️ **Dual runtime choice** | Default proot, optional proroot; actual performance depends on device, I/O, caches and plugins |
| 🔌 **The phone is the agent's hands** | Accessibility + ADB without Shizuku + an independent virtual display: read screens, tap, install apps, run automations — all built in |
| 💾 **Export for migration** | Data & backups exports password-free `.tar.gz` archives. Storage guidance shows the actual location; local copies are not guaranteed to survive uninstall |
| 🩺 **Failures that explain themselves** | Component-level checks + on-demand repair + startup diagnostics + an independent recovery DSH; when the web UI won't start, it names the plugin at fault |

---

## Core modules

### ① Setup & environment

| Capability | Details |
|---|---|
| Bundled offline rootfs | Ubuntu 24.04 (noble) arm64 inside the APK — deployment works with no network |
| Six-step install pipeline | Extract → base tools → Node.js → pnpm → dsh → patches; each step is probed before it runs and verified after; only failed items get repaired, never start from scratch |
| Per-step reinstall / update | rootfs, tools, Node and the harness are independent — reinstall any of them without re-downloading the rest |
| Two install paths | Prebuilt bundle or source build; the source path handles node-pty and other native module compilation automatically |
| Offline toolchain | curl / git / Python / CA certificates pinned via `packages.lock.json` — no dependency on the user running `apt` first |
| Mirrors & networking | apt falls back between official and USTC mirrors automatically; three DNS modes (auto / force IPv4 / system native), and a failed AAAA lookup retries resolution only — never replays the HTTP request |
| Versioned base environment | The Ubuntu base carries its own version number; app updates never rebuild the environment, and ordinary dsh updates never bump the base version |

### ② Runtime

| Capability | Details |
|---|---|
| proroot / proot dual runtime | Stable proot is the default; proroot can be selected in Configure, subject to device compatibility |
| Performance evidence | Limited same-phone samples are available; devices, caches and plugins affect results. See [performance evidence](docs/en/performance-startup-20261022.md), without a universal engine ranking |
| Bounded compatibility fallback | Retry proot once only after proroot exits before authentication without a plugin failure and guest exit is confirmed; slow startup never triggers fallback |
| Node.js 24 + pnpm 10 | Runtime pinned with the APK |
| Split-package updates | Ubuntu and the dsh runtime ship as separate packages inside the APK; cold installs extract both, partial updates read only the dsh package |
| Managed update trials | A new environment boots for real in an isolated area first — ports, auth, session read/write and plugin loading are verified before it is committed; failures roll back automatically |
| Foreground service + watchdog | Running state visible in the notification shade; the Web UI is pulled back up automatically if it dies |
| Slow-start protection | Waiting for auth has no kill timeout (a hint appears at 60 s); the watchdog never mistakes a slow start for a fault |

### ③ Data & backups

| Capability | Details |
|---|---|
| Storage and migration | Data & backups → Storage guidance shows the actual location. Updates preserve current data; export needed content before uninstalling |
| v5 backups and exports | New exports are password-free `.tar.gz` integrity archives. Internal automatic copies remain encrypted; older encrypted originals still require their original password |
| Automatic backup schedules | On by default: daily at a chosen time, every 1–168 hours, or after stopping DSH; running backups wait instead of interrupting your work; keeps the latest 3 verified copies |
| Scoped backups | Full / conversations only / plugins only / settings only; restoring a partial backup touches only its own scope |
| Restore on another device | Export actual conversations, attachments, settings and user plugins; check digests and scope before restore preview, retaining current content and conflicting originals |
| Credentials never enter backups | The bridge token is excluded whole; `.credentials.yaml` is stripped field-by-field — machine keys removed, user API keys kept |
| Older backup compatibility | Full authentication/digest verification precedes restore preview; unknown or incomplete dependencies are reported. The current APK rebuilds system plugins, retaining user originals |
| Corrupt session quarantine | Broken session files move to `corrupt-backup` where you can retrieve them — one bad file can't take down the whole web UI |
| Post-upgrade cleanup | Regenerable caches and surplus old copies are cleaned in idle time after upgrades; at least two healthy predecessors are kept, and modified originals are never touched |
| External workspace protection | Thorough reinstall and factory reset are removed; maintenance only detaches private references and retains external files and backups |

### ④ Device capabilities (the agent's hands on this phone)

The agent calls these through the local `127.0.0.1:3090` bridge (token-gated; `/app/help` lists every endpoint):

| Capability | Details |
|---|---|
| Screen control | **Via the accessibility service — no ADB needed**: structured screen dumps with tappable regions, tap by text or coordinates, text input, key events, swipes, PNG screenshots |
| Virtual display (experimental) | Standard / Android 11+: authorize ADB, Shizuku or Root, then create a display on its page. Accessibility alone does not create one; see the [setup guide](docs/virtual-screen-guide.md) |
| Wireless ADB | Built-in pairing (TLS 1.3-PSK + SPAKE2) and keep-alive — **no Shizuku required**; survives reboots |
| Shizuku / Root channels | Backup device-command channels, bound by the same command allowlist |
| Talking to the user | System notifications, in-app toasts, vibration (wake the user after long jobs), a three-option blocking prompt, share / open URLs |
| File exchange | Read directories and text files, export artifacts to `Download/DSHA`; credential areas (`.dsh` / `.ssh` / `.android`) are blocked from both reads and writes |
| Sensors & location | Light / accelerometer / gyroscope / magnetometer / barometer / step counter / location / flashlight — all off by default, granted per capability |
| Clipboard | Read and write (subject to Android foreground restrictions) |
| Dangerous-command gatekeeper | Device commands always pass through an allowlist parser: partitioning / formatting / SELinux / system property writes are rejected outright, unknown commands never pass; blocks return `[POLICY_BLOCKED]` instead of a "allow anyway" dialog |
| SMS reading | A separate sensitive capability: strictly read-only queries, confirmed per query by default, revocable, never restored from backups |

### ⑤ Terminal

| Capability | Details |
|---|---|
| Real PTY terminal | Termux terminal-emulator JNI: vim / htop / tmux and other full-screen TUIs just work |
| Phone keyboard compensation | Extra key row (Ctrl / Alt / Esc / arrows / Tab); pinch to change font size |
| Multiple tabs | Sessions persist across tab switches, rotation and language changes |
| Simple-terminal fallback | If PTY misbehaves on some device, switch to the simple terminal with the session kept alive in the background |

### ⑥ Web UI & access

| Capability | Details |
|---|---|
| Engine | Uses the system WebView, updated with the system |
| Mobile adaptation | Bundles [dsh-web-mobile](https://github.com/mexiaosqwq/dsh-web-mobile) **3.3.5** (MIT), retaining phone shortcuts and narrow-screen layout while fixing focus, dialogs and plugin cards |
| Picture-in-Picture | Off by default; users explicitly enable it. Normal return and background restoration retain the same-generation page |
| High refresh & power | Requests the user-selected refresh limit and returns control when idle; a successful request does not establish measured frame rate |
| Themes & languages | Dark / light / follow system; Simplified Chinese / English, following the system language by default |
| LAN access | Use dsh from a laptop or tablet browser over Wi-Fi. Token auth is fail-closed; on first hit it sets a `SameSite=Strict` cookie so the token never leaks through outbound links |
| Legacy browser compat | Injects `AbortSignal.any/timeout` and `crypto.randomUUID` polyfills (the latter is required over plain-HTTP LAN) |
| Streaming overlay | Agent output sticks to the top of the screen like lyrics; tool calls are translated into plain language; colors / opacity / line count adjustable; dangerous commands can be approved right on the overlay |
| Configurable port | Pick a custom Web port; conflicts fall back automatically with a clear explanation |

### ⑦ Plugin ecosystem

| Capability | Details |
|---|---|
| Plugin management | Install / update / enable / disable / delete / search / sort, entirely in-app; supports community plugins |
| Many install paths | GitHub shorthand / tree / blob / archive / Release links, direct HTTPS archive URLs, local import (format detected by content, not extension), or `dsha-plugin install` in the terminal |
| Multiple download sources | Automatic source selection with npm official and npmmirror; concurrent update checks, locked-version cache reuse, bounded fallback on failure |
| Dependencies and transactions | Bundled pnpm 10.34.5 permits unlocked resolution, lifecycle scripts and pnpmfile; actual locks/digests are recorded, archive traversal is rejected and rollback originals are retained |
| Enable after installation | Package format, paths, dependencies and digests are checked before automatic commit/enable; explicit disable and safe-mode choices remain. See [plugin details](docs/plugins.md) |
| Hard-dependency rewrite | Plugins that hardcode service dependencies get rewritten to runtime injection — one plugin can't drag down the whole plugin tree |
| Built-in plugin protection | Built-in plugins can't be deleted; disabled ones stay disabled across upgrades; configs import/export cleanly |

Main built-in plugins include: `dsh-web-mobile` (mobile adaptation), `dsh-status-overlay` (floating
bar), `dsh-task-notifier` (turn-complete notifications), `dsh-device-shell-guide` (device capability
guide), `dsh-computer-use-android` (Android Computer Use), `dsh-tool-vscreen` (virtual display
tools) and `dsh-auto-review` (official experimental Auto review entry).

### ⑧ Reliability & recovery

| Capability | Details |
|---|---|
| Install & repair page | Checks all six components and repairs on demand (certificate / npm issues, DNS, session-write patches…); only failed items are touched |
| Diagnostic reports | Environment checks and failure logs are exportable; startup diagnostics persist stage, actual plugin errors and exit codes — the last five runs, sanitized |
| Startup recovery | Definite startup / plugin faults enter the recovery page automatically; Safe Start uses an isolated profile with official components only, keeping original configs and plugin switches |
| Config snapshots | Automatic snapshots before configuration changes (three healthy + three pre-repair), so there's always something to roll back to |
| Plain-language plugin diagnosis | When the web UI won't start, it says "it's plugin X, it wants a service that doesn't exist, tap here to fix" — not a screen of Node stack traces |
| Independent recovery DSH | If the main environment breaks, an independent recovery environment takes over: its own runtime root, read-only diagnostics first, write repairs confirmed step by step natively |
| Script hot updates | Key scripts update incrementally from GitHub with **offline signature verification** (public key bundled; a bad signature rejects the whole batch) — no need to wait for a new APK |

### ⑨ Security (least privilege by default)

| Aspect | Approach |
|---|---|
| Usable with zero permissions granted | The minimal setup (no ADB, no file access, no LAN) still runs dsh fine; every capability is off by default and revocable at any time |
| API keys | Android Keystore + AES/GCM; keys never leave the Keystore; a failed read never wipes the stored ciphertext |
| Device commands | The allowlist is always on; Root / Shizuku / ADB share one policy; app termination verifies ownership per target to prevent PID-reuse mistakes |
| Bridge credential guard | `/app/export` and `/app/readfile` reject credential-area paths, with normalization and canonical-path checks; the documented recursive Root READ child-symlink gap remains, so this is not complete isolation |
| No telemetry | Nothing is uploaded — no logs, no usage data; network requests are limited to updates, plugin downloads and your configured model services |
| Honest disclosure | Known weaknesses (no kernel-level sandbox, legacy plaintext backups, signing key rotation pending…) are listed directly in the docs |

👉 For what each permission actually exposes and which parts of your phone the agent can reach, see the **[security model](docs/security-model.en.md)**.

---

## How this compares

Running dsh on Android has two paths, each with real costs — describing them beats name-calling:

| | **Container path** (DSHA's choice) | **Termux bootstrap path** |
|---|---|---|
| How | proot/proroot + full glibc rootfs | Termux packages running bare on Android's bionic |
| Setup | Install one APK | Install Termux → type commands → build a toolchain |
| Environment | Full Ubuntu — `apt` and native modules work | Needs per-package patches / rebuilds for bionic |
| Overhead | Syscall and file-I/O translation overhead varies by device and workload | No container layer; theoretically fastest |
| Sandboxing | Limited either way | Limited either way |

---

## Known limits

Listed honestly, so you don't discover them after installing:

| Item | Status | Notes |
|---|---|---|
| Architecture | ⚠️ arm64-v8a only | 32-bit and x86 devices are not supported |
| OS version | ✅ Android 11+ | Older systems are not supported; wireless pairing itself also needs 11+ |
| Size | ⚠️ Standard 303.18 MiB | The price of a bundled Ubuntu environment — in exchange for no downloads and no command line |
| bash tool | ✅ Works | Full Ubuntu bash; the agent runs shell commands without restriction |
| bash **sandbox isolation** | ⚠️ Unavailable | bubblewrap needs unprivileged user namespaces, and Android sepolicy refuses — neither the container path nor Termux can work around it. Constraints rely on dsh's permission modes: `danger-full-access` by default, switchable to `workspace-write` or `read-only` in Configure. Judge the risk yourself |
| Sundigital / HarmonyOS anco | ❓ Unverified | Plausible in theory; no real-device regression yet |
| Overlay | ⚠️ Needs permission | Self-drawn via `TYPE_APPLICATION_OVERLAY`; rootless devices can't get the real "status-bar lyrics" API |
| Data location | ⚠️ Needs file access | If "All files access" is denied, data stays in the private directory and is lost on uninstall (the self-check tells you which state you're in) |

---

## Architecture

```
┌──────────────────────── APK ────────────────────────┐
│ Native Android (Java 17 · Material3 · single :app)  │
│  ├ Launch / install-repair / configure / workspace  │
│  │   plugins / terminal                             │
│  ├ Web engine: system WebView                       │
│  ├ Foreground service + watchdog + notifications+PiP│
│  ├ App bridge :3090 (accessibility / vscreen /      │
│  │   interaction / files)                           │
│  ├ LAN proxy :3081 · ADB / Shizuku / Root channels  │
│  └ Overlay (TYPE_APPLICATION_OVERLAY)               │
├─────────────────────────────────────────────────────┤
│ proot (default) / proroot (optional)│
├─────────────────────────────────────────────────────┤
│ Ubuntu 24.04 arm64 · Node.js 24 · pnpm 10           │
│  └ @deepseek-ai/dsh  →  Web UI :auto                │
└─────────────────────────────────────────────────────┘
```

Data: see Data & backups → Storage guidance for the actual location; legacy `Documents/dshdata` remains readable.
Android Keystore protects API keys; local keys and automatic copies are not guaranteed to survive uninstall.

---

## Wireless ADB pairing (device shell)

Once paired, the agent can operate this phone directly — **no Shizuku needed**.

**First-time pairing (about 1 minute)**

1. System settings → "About phone" → tap "Build number" 7 times to enable developer options
2. Developer options → enable "Wireless debugging"
3. Open "Wireless debugging" → "Pair device with pairing code"; note the **IP:port** and the **6-digit code**
4. Back in DSHA → "Device capability grants" → enter them → Pair

> The pairing code requires Android 11+; on older systems use the Shizuku / Root channels —
> or skip pairing entirely, since the accessibility capabilities (screen reading, taps, input) need none.

With wireless debugging off, Verify existing connection can prepare the bundled offline dependencies first. `ADB_OFFLINE_READY` means dependencies are ready; enable wireless debugging and complete pairing or connection verification afterward.

**After pairing**: DSHA maintains the connection itself (keep-alive + reconnect); it survives reboots.

**Verify**: run `adb shell id` in the built-in terminal — `uid=2000(shell)` means success.

**Let the agent use it**: copy the skill packs into the agent's skill directory:

```bash
cp -r agent-skills/device-shell ~/.agents/skills/
cp -r agent-skills/screen-ocr-operator ~/.agents/skills/
```

`device-shell` covers command usage across the ADB / Shizuku / Root channels;
`screen-ocr-operator` adds screenshot + OCR + batched screen actions (for WebView / game canvases
where accessibility dumps come up empty).

---

## Building

Local builds need JDK 17, Android SDK (API 37), NDK 26 and Python 3.9+ — see [BUILD.md](BUILD.md):

```bash
bash build.sh                                # default: Standard Debug
bash build.sh :app:testStandardDebugUnitTest # pure-logic unit tests
python tools/verify-stability.py             # stability acceptance gate
```

The offline rootfs is not committed to Git. Release flow (signing, gates, on-device acceptance,
artifact replacement) is documented in [BUILD.md](BUILD.md) and [docs/releases/](docs/releases/).

---

## Documentation index

| Doc | Contents |
|---|---|
| [AGENTS.md](AGENTS.md) | Project structure, startup contracts, technical constraints, known traps (entry point for AI / new contributors) |
| [docs/security-model.md](docs/security-model.md) | Security model: boundaries of every permission and known weaknesses ([English](docs/security-model.en.md)) |
| [docs/plugins.md](docs/plugins.md) | Plugin installation and packaging requirements |
| [CHANGELOG.md](CHANGELOG.md) | Full changelog |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Roadmap and the "explicitly not doing" list |
| [docs/android-standard.md](docs/android-standard.md) | Device adaptation notes |
| [docs/releases/](docs/releases/) | Per-version release and acceptance records |

## Credits

- [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) — the harness itself
- [DSH-APP/DSHA](https://github.com/DSH-APP/DSHA) — the upstream Android packaging this project builds on; thanks to the original author [@qiannianhuanxiang](https://github.com/qiannianhuanxiang) and contributor [@ym2025szz](https://github.com/ym2025szz)
- [proroot](https://github.com/coderredlab/proroot) / [proot](https://github.com/termux/proot) — rootless containers (see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md))
- [Termux terminal-view / terminal-emulator](https://github.com/termux/termux-app) (Apache-2.0) — PTY terminal
- [dsh-web-mobile](https://github.com/mexiaosqwq/dsh-web-mobile) — bundled mobile adaptation
- [Shizuku](https://shizuku.rikka.app/) — backup device-command channel

## Community

| Topic | Channel |
|---|---|
| Bugs & feature requests | [GitHub Issues](https://github.com/steveneng2020/DSH-Android/issues) |
| Security vulnerabilities | See [SECURITY.md](SECURITY.md) (**not** a public issue) |
| Email | steveneng@163.com |

> This project maintains no official community channels; answers elsewhere do not represent it.


## License and disclaimer

### License

Released under the [MIT License](LICENSE). Full terms in [LICENSE](LICENSE).

**Copyright ownership** (three layers, all retained):

| Scope | Copyright |
|---|---|
| DeepSeek Harness itself ([deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness), MIT) | Copyright (c) 2026 DeepSeek |
| Upstream Android launcher DSHA ([DSH-APP/DSHA](https://github.com/DSH-APP/DSHA)) | Copyright (c) 2026 qiannianhuanxiang |
| Additions and modifications in this project ([DSH-Android](https://github.com/steveneng2020/DSH-Android)) | Copyright (c) 2026 steveneng2020 |
| Third-party components | Belong to their respective authors, enumerated in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) |

**Dependency layers**: this project is an Android launcher and contains no model or agent
implementation of its own. It bundles the official DeepSeek Harness npm runtime
(`@deepseek-ai/dsh`; version and provenance in `tools/dsh-runtime/package-lock.json`) and
continues the Android shell work of upstream DSHA on top of it. **It is not affiliated with,
sponsored by, or endorsed by the DeepSeek Harness authors or the upstream DSHA authors**, and
claims no copyright over DeepSeek Harness.

This project is a derivative work built on the layers above.
**The copyright and permission notices of both upstream layers must be retained in full.**

**Reuse requirement**: if you reference, quote, redistribute or merge this project's
code or derivative works, **you must retain complete attribution** — name this
repository (`https://github.com/steveneng2020/DSH-Android`) together with the
copyright notices above, and keep the full [LICENSE](LICENSE) text. Redistributing
after removing or altering the attribution does not comply with this project's
license terms.

### Disclaimer

**This project is provided for technical study and research only.**

| Item | Statement |
|---|---|
| **No commercial use** | Without written permission from the original author and this project's maintainer, **you may not use this project (source, binaries or derivative works) for any commercial purpose**, including sale, rental, paid distribution, bundling into commercial products, or use as part of a commercial service |
| **Use at your own risk** | Provided "as is", without warranty of any kind. **Any data loss, device damage, account suspension, service interruption or other direct/indirect loss arising from use is borne entirely by the user** |
| **No official affiliation** | This is a community build with **no affiliation, sponsorship or endorsement from DeepSeek or the upstream `DSH-APP/DSHA` authors**. Do not report issues to official channels |
| **Legal compliance** | **Use of this app or of any API service it connects to must strictly comply with the laws and regulations of your country or region. If your country or region does not permit such use, you must stop using and uninstall this app immediately.** Users must confirm that their use is lawful locally; all consequences of non-compliant use rest with the user |
| **Service terms** | Users are responsible for complying with the terms of service and billing rules of any model/API provider they connect to |
| **No support commitment** | The maintainer does not promise to fix defects, to keep updating, or that the software fits any particular purpose |
| **Third-party services** | This project provides no model or API service. You must supply your own and follow the provider's terms and billing |

### Security

See [SECURITY.md](SECURITY.md) for how to report vulnerabilities and for known security boundaries.
**Do not disclose unpatched security issues through public issues.**
