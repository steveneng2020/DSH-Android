# AGENTS.md — English contributor and agent guide
> **This guide is for AI agents and new contributors.** Read it once and you can work
> without scanning the whole repository. Read [README.en.md](README.en.md) first.
>
> **This is a fork**: [steveneng2020/DSH-Android](https://github.com/steveneng2020/DSH-Android),
> not the upstream [DSH-APP/DSHA](https://github.com/DSH-APP/DSHA). Package `dsh.android.dev`,
> release certificate SHA-256 `814ab103...3622f`, **not interchangeable** with upstream
> `dsh.android.client` / E7E3: no cross-install, no shared data (migrate with backup
> export/restore). Upstream is a read-only reference; this project does not push to it and
> does not publish to it.
>
> **Three copyright layers** (see [LICENSE](LICENSE)): DeepSeek Harness
> (`deepseek-ai/deepseek-harness`, MIT) -> upstream Android launcher DSHA (`DSH-APP/DSHA`)
> -> this project (`steveneng2020/DSH-Android`). This project contains no model or agent
> implementation; it bundles the official DSH npm runtime and is not affiliated with,
> sponsored by or endorsed by the authors of the two layers above.

## Repository facts (current; the code is authoritative)

- Shape: Gradle single module `:app`, **pure Java 17 (0 .kt files)**, arm64-v8a.
- App: package `dsh.android.dev`, `standard` flavor (minSdk 30, system WebView). Version and
  file names come from `app/build.gradle`; this file does not keep a second set of numbers.
- Bundled DSH: `@deepseek-ai/dsh` **0.2.2-rc.1**, locked by
  `tools/dsh-runtime/package-lock.json`. `Constants.DSH_VERSION`, `package.json`, the lock
  and `runtime-patches.json` must agree - `verifyBundledDshGeneration` rejects mixed
  generations at configuration time.
- Runtime: Ubuntu 24.04 arm64 + proot (default) / proroot (explicit opt-in), base identity 10.
- Updates: in-app "check for updates" reads only this repository's `main`
  [updates.json](updates.json); APKs are served from this repository's Releases.
  Maintenance rules in [UPDATES-HOWTO.md](UPDATES-HOWTO.md).
- Changelog must agree across three faces: `CHANGELOG.md` (repo),
  `docs/releases/build{code}-changes.{zh,en}.md` -> `app/src/main/res/{raw,raw-en}/changelog.md`
  (full text, generator-guarded), and `app/src/main/res/{raw,raw-en}/changelog_recent.json`
  (summary cards). When it drifts run `python3 tools/check-changelog-sync.py --write`;
  the gate runs in `ci-fast` and `verify-stability`.

### Build tasks (standard only)

```bash
python3 tools/run-host-tests.py --stage fast      # host tests
./gradlew :app:testStandardDebugUnitTest          # unit tests
./gradlew :app:assembleStandardRelease            # release build (needs release signing)
```

The `low` flavor still exists in the source tree but was **never released** and is not a
distribution target; user-facing docs do not mention it.

---

## Directory map (measured 2026-11-10)

```text
app/src/main/java/com/deepseekharness/app/          603 .java files (main)
├── *.java (root package, 29) Device/services: accessibility, bridge, LAN, overlay, Shizuku/Root, PTY
├── ui/      (91)             MainActivity, Fragments, Activities, dialogs
├── core/    (47)             HarnessController, maintenance barrier, backup tasks, diagnostics
├── runtime/ (56)             ProotBootstrap, ContainerRuntime, WebProcessManager, installation
├── backup/  (79)             v5 encrypted backup, restore, migration, historical formatting, automatic backup
├── vscreen/ (27)             Channels, preview, input, accessibility bridge
├── recovery/(5)              Independent emergency DSH lifecycle, separate from the main environment
├── bridge/  (9)              AppBridge contract, AdbBridge, LAN access
├── data/    (4)              KeyVault (Keystore), portable settings, export
├── device/ diagnostics/ screen/ capabilities/ skills/  23 total (device audit, diagnostics, screens, capability probes)
└── util/    (233)            Pure logic, no Android API imports; unit tests required

1072 .java files in total (incl. test 389, androidTest 10, debug 39, deviceAudit 21)
```

Counts are navigation aids, not contracts; `util/` holds 233 pure-logic classes, so check for
an existing class with the same responsibility before adding one.

### Root package (`com.deepseekharness.app`): devices and system services

| Class | Responsibility |
|---|---|
| `HttpShellService` | **3090 bridge**, historically about 105 KB and the largest class: 24 `/exec` / `/app/*` endpoints, token-gated |
| `DshaAccessibilityService` | `uiDump / uiTap / uiTapText / uiInput / uiKey / uiSwipe / uiScreenshot` and virtual-screen forwarding |
| `DeviceBridgeService` | ADB/Shizuku/Root channel selection and keepalive |
| `DeviceShellExecutor` / `DeviceAppInventory` / `DeviceSense` | Device commands (util allowlist), app inventory, sensors/location/flashlight |
| `LanProxyService` / `LanAuth` | LAN proxy `:3081`, fail-closed token authentication |
| `OverlayController` / `OverlayLines` | Streaming overlay: lyric-like AI output and command approval |
| `HarnessService` / `WebPreviewActivity` | Foreground service/watchdog and embedded Web preview (WebView/Gecko) |
| `PtySession` | Termux terminal-emulator JNI wrapper for a real PTY |
| `ShizukuShell` / `RootShell` / `ShellService` / `AdbKeepAliveReceiver` / `BootReceiver` | Channel implementations and boot/keepalive receivers |
| `DshaDocumentsProvider` | File-manager access to private directories, including MT Manager |
| `DeviceShellPolicy` / `DeviceShellExecutor` | Parse and guard managed device commands before execution; approval does not override explicit rejection, including through Root |
| `BridgeAskDialog` / `ConfirmReceiver` | Native business questions and security-notification replies; global confirmation does not answer business choices |
| `DshaApp` / `UpdateDownloadService` | Application entry, including early system-language capture; in-app update downloads |

For Root maintenance, use [permission architecture](docs/en/device-permissions-architecture.md) and the [pinned upstream review scope](docs/en/references-and-provenance.md): nine su candidates and metadata checks do not identify a manager or prove compatibility with every version. The 65-second budget covers result collection only. Review of `140c7ba` on 2026-10-22 found that recursive READ does not validate nested symlink targets, leaving an SMS-protection implementation gap. Do not describe this as documentation-only or complete bypass prevention. Record the unresolved state, regressions and device evidence separately. Historical `DangerShellGuard` is absent from the production call chain.

### Layer ownership — read before changing code

| Layer | Key classes | Responsibility |
|---|---|---|
| `ui/` | MainActivity / WelcomeActivity / Launch·Config·Settings·Plugin·Workspace Fragment / WebPreviewActivity | UI and startup gates |
| `core/` | `HarnessController` (historically about 57 KB, orchestration core) | Start/stop dsh and capture authenticated links. **Do not add new responsibilities here**; create focused collaborators |
| `core/` | `ConfigStore` | Sole configuration read/write entry: port/model/workdir/API key |
| `core/` | `InstallRepository` / `MaintenanceCoordinator` / `RuntimeTasks` / `StartupDiagnostics` | Install state, maintenance barrier, running-task locks, startup diagnostics |
| `runtime/` | `ProotBootstrap` / `ContainerRuntime` / `WebProcessManager` | proot command assembly, runtime/BINDS selection, Web stop with sentinel/PID/birth verification |
| `runtime/` | `InstallPipeline` / `ManagedRuntimeAssets` / `RuntimeTrial` | Six-step installation, managed assets, update trial |
| `backup/` | `NativeBackupJobs` / `BackupArchive` / `HostDataTransaction` / `AutomaticBackups` / historical `FactoryReset` | v5 encrypted backup/restore, data transactions, automatic plans, historical formatting |
| `recovery/` | `RecoveryController` / `RecoveryRuntime` / `RecoveryRepairBroker` | Independent emergency DSH, bypassing main-environment migration/startup lock |
| `vscreen/` | `VirtualScreenManager` / `VirtualScreenAccessibility` / `VirtualScreenPreviewView` | App-owned authenticated connection/heartbeat; input includes the latest frame sequence |
| `bridge/` | `AppBridge` contract / `AdbBridge` (TLS 1.3-PSK + SPAKE2 wireless pairing) / `LocalNetworkAccess` | Bridge seams and device channels |
| `data/` | `KeyVault` | Keystore AES/GCM encryption of API keys |
| `util/` | `Constants` / `ShellQuote` / `Query` / `WebProcSel` / `DeviceShellPolicy` / `HttpProtocol` / `BackupScope`, historically 118 | Pure logic without Android imports; **unit tests required** |

---

## Test layout (measured 2026-11-10)

`app/src/test/java/com/deepseekharness/app/` contains **389** test classes: `util/` 213,
`backup/` 54, `core/` 35, `runtime/` 30, `vscreen/` 28, `ui/` 14, `data/` 2, `recovery/` 2,
`bridge/` `capabilities/` `screen/` `skills/` 1 each, root 1.

**Static class counts are not execution counts** and are not pass evidence: actual
pass/fail/skip comes from the JUnit XML of that run and the receipts under
[docs/releases/](docs/releases/).

```bash
./gradlew :app:testStandardDebugUnitTest   # full unit tests (standard)
```

Locked invariants that refactoring must preserve:

- `ShellQuote`: POSIX single-quote escaping; malicious values cannot escape.
- `Query`: match each complete parameter name. `indexOf(key+"=")` allowed suffix hijacking and was fixed. An empty parameter differs from an absent one.
- `BackupScope`: partial backups must never be named `DSHA-backup-*`, or old versions may interpret them as full restores and remove configuration/plugins. `dshPaths` and `mergeSubdirs` correspond one to one.
- `WebProcSel`: recognize dsh processes and **never accidentally kill proot/proroot**; killing the container launcher can take the environment/application down with it.
- `DeviceShellPolicy`: default-deny allowlist; accept only a completely recognized single argv, never a user-supplied shell program.
- `HttpProtocol` / `SocketDispatch`: independent header-byte and total-deadline limits; bounded LAN registration, short requests, long streams, and reverse pumps.

---

## Security model

Read the [security model](docs/en/security-model.md) first. Essential boundaries:

- **Device-command allowlisting is always active** (`util/DeviceShellPolicy`). Formatting, partitions, SELinux, and system-property writes are rejected, as are unrecognized commands. Rejection returns `[POLICY_BLOCKED]` with exit 126 and **no “allow anyway” button**. Root/Shizuku/ADB share this policy.
- **Bridge credential guard** (`util/BridgePathPolicy`): `/app/export` and `/app/readfile` reject credential areas such as `.dsh`, `.ssh`, and `.android`, combining string rules with `getCanonicalPath()` against symlink bypasses.
- **Least-privilege defaults**: sensitive ADB, Root, SMS, sensors, location, overlay, and LAN capabilities default off and are revocable. DSHA still runs dsh with minimal configuration.
- **Backup credential exclusion**: bridge-token files are wholly excluded; `.credentials.yaml` removes local connection secrets field by field while retaining user API keys.
- **This is not a kernel sandbox**: containers, plugins, and terminals run under the app's Android UID. The allowlist protects bundled entry points, not arbitrary self-written code. Do not describe this as security isolation.
- Keep known weaknesses in the security model, including `danger-full-access`, historical plaintext backups, and pending signing-key rotation. Do not delete them.

---

## Technical constraints

### Versions and builds

- **Version and signing identity come from `app/build.gradle` and `ci/release-identity.json`**: package `dsh.android.dev`, certificate SHA-256 `814ab103...3622f`. E7E3 is the **upstream** debug certificate from the `dsh.android.client` era; it is unrelated to this fork and no build here may sign with it.
- `standard`: minSdk 30, system WebView; build task `assembleStandardRelease`. The source tree still carries the `low` flavor (minSdk 23, GeckoView 143) and `tools/build-low-proot.py`, but **that build was never released** and is not a distribution target; user-facing docs do not describe it, and `docs/android-low.md` is upstream historical material.
- Offline rootfs (`assets/offline-rootfs.bin`) is **not committed**; preparation scripts generate it. `offline-rootfs.layout=split-runtime-v1` marks separate Ubuntu and `dsh-runtime.bin` packages; builds check both digests.
- `tools/dsh-runtime/package-lock.json` locks new dsh dependencies. `tools/prepare-runtime-descriptor.py` generates independent managed-contract descriptors; the APK version is diagnostic context only. Update managed trees within the same base while keeping personal data in place. **UI-only APK updates do not replace the environment; ordinary dsh updates do not increment the Ubuntu base.**
- `tools/ubuntu-tools/packages.lock.json` locks offline curl/git/certificates (`tools/prepare-ubuntu-tools.py` generates `ubuntu-tools.bin`). Web ES compatibility dependencies are locked in `tools/web-compat/` (`node tools/prepare-web-compat.mjs`). Generated files are not committed, and builds verify digests.
- Chinese/English UI messages come from `tools/i18n/messages.json`, with a generated Java dictionary. Preferences: `system` (default), `zh`, `en`. **Capture system language at the earliest process stage** (`SystemLanguage.initialize()` before any `Locale.setDefault`), or “follow system” can lock itself after a switch. Language changes recreate UI without stopping terminals/Web; do not replace user input or original commands automatically.
- Old WebView polyfills for `AbortSignal.any/timeout` and `crypto.randomUUID` must precede application scripts in managed HTML and cover document-start and Worker execution.

### Data and backup

- **Automatic backup defaults on**, per the 2026-09-17 requirement overriding older off rules. `AutomaticBackups` supports daily time, 1–168-hour intervals, and after-stop modes (`util/AutomaticBackupPolicy` has tests). Defer while running rather than force-stopping Web/terminals. Retain the latest three verified automatic copies; do not automatically delete manual or unknown records.
- v5 user exports are password-free `DSHA-data-v5-<UUID>.tar.gz` containing DSHADATA integrity payloads. Internal automatic copies remain encrypted. Historical encrypted originals still require their password and complete authentication. Native API keys are excluded by default. Verify integrity/authentication before preflight and write only private numbered slots. User archives cannot activate local authorization; managed scripts, executable configuration, and unknown plugins are isolated first.
- Do not infer data format from APK/dsh versions. `DataFormatEvidence` keeps unchecked data unknown. A sender's claimed verified format does not authorize deleting originals.
- Upgrade maintenance may clean regenerable caches and excess copies while idle, preserving at least two healthy plan-matching copies. Never delete modified/extra-file originals. A verified rebuild establishes `retired-proof.json` before cleaning `previous-linux`.
- Production complete-format entry points/erasure backends are retired. Do not restore old cleanup. External-workspace maintenance disconnects private references only, without traversing, overwriting, or deleting its contents. Legitimate cache cleanup still requires controlled private targets and NOFOLLOW checks.
- Authorized upgrade acceptance uses original-package, same-signature, non-debuggable release APKs and non-destructive checks. Do not inject force-kill, deleted Bash, or bad-plugin faults into production data.

### Runtime and updates

- New managed updates use `ManagedRuntimeTransaction` / `HostDataTransaction`. A real isolated `RuntimeTrial` checks static assets/native modules, actual port/authentication, storage/session write-and-reopen, browser/backend handshake, and guest exit before commit. Receipts live outside rootfs and bind file digests. Keep at least the direct healthy predecessor.
- `RuntimeTrial` records actual `runtimeMode`. If selected proroot explicitly exits before authentication without plugin faults, `WebRuntimeFallback` may try proot once. **Do not report proot success as native proroot success.** Static checks select proot first; slow startup does not trigger retries.
- `RuntimeTrialRecords` rotates confirmed-closed scenes only: latest three successes and five failures. Do not automatically delete unclosed/abnormal directories or impose a permanent cumulative-trial cap.
- Readiness parses the real `/bin/bash` ELF and loader path. Use lstat for executable bits (`canExecute` is unreliable under Android W^X). A damaged system goes to environment repair rather than repeated configuration safe-start.
- Production plugin policy permits unlocked dependency resolution, lifecycle scripts, and pnpmfile. Links/local packages/updates auto-commit and enable after format/path/actual-dependency/digest/transaction checks. Preserve explicit user disabling and safe-mode intent; do not restore the native review gate. `plugin-transactions.py` records candidates/originals; uncommitted journals remain in maintenance gates.
- Separate system/user plugins. System source is not user-backup content; current APK managed proofs reconstruct it. `.disabled` intent wins over conflicting old entities.
- `NARB_DISABLE_NATIVE_CACHE=1` loads native extensions directly from bundled directories; default caching initially dangles under `--link2symlink`.

### Web, bridge, and terminal

- Main Web starts through the current managed dsh wrapper and fixed packaged entry with the common RuntimeTools environment. Default automatic port is `--port 0`, with actual port recorded after authentication. Explicit manual settings follow current selection policy. See [runtime mechanisms](docs/en/runtime-data-plugin-architecture.md), rather than copying an old fixed 3080 command. Execute proot from nativeLibraryDir, not filesDir as a W^X workaround.
- In the inspected previous snapshot, `WebPortPolicy.choose` selected fixed/local-backup/dynamic ports before startup. Backup memory is local only and does not migrate. That snapshot did not wire production `retryBindRace`; helper/tests alone did not establish automatic bind-race retry. Authentication, keepalive, and LAN use the actual port, never a port-inferred PID. Check the maintained [port page](docs/en/ports-and-networking.md) and final receipt for subsequent changes.
- Waiting for Web authentication has no forced termination deadline (60 seconds is a notice). Stop/maintenance share `WebProcessManager` PID and birth-identity checks.
- Feature-detect bridge protocol via `/app/version` (`BRIDGE_PROTOCOL=2`); plugins use `>=`, not `==`. Command query-string budgets must accommodate existing 8192-character commands.
- LAN body boundaries follow method, status, and explicit framing. Only a validated 101 WebSocket handshake switches to a tunnel. Do not strip hop-by-hop headers and still send mismatched encoded bodies.
- Native fork/exec handshake registers PTY birth identity: the child reads its own stat, the parent confirms, then exec occurs. Do not return to a single Java read after launch. PTY/simple terminals own separate tabs/sessions and retain processes through page/rotation/language changes. Closing a tab removes it only after confirming that session's exit. Session IDs increase permanently; display numbers independently reuse the lowest gap.

### Emergency, virtual screen, and devices

- **Independent emergency DSH:** `recovery/` bypasses main-environment migration/data binding/global startup lock. `tools/recovery-runtime/lock.json` independently pins archives. Emergency profiles expose only five controlled repair tools; a “native safe profile” cannot replace an independent root. `RecoveryRepairBroker` HTTP cannot confirm writes. Native confirmation binds candidate, source digest, and data generation, then uses the stop barrier and host transaction.
- Emergency asset deduplication: `recovery-asset-locations.json` maps physical locations only. Share packaged bytes only if the main archive SHA exactly matches the independent lock. Extracted roots remain independent; rescue does not read the main rootfs as a dependency.
- **Virtual screen** (Standard, API 30+): App owns managed Core. Raw coordinates require the latest observed frame; semantic node/editor and anchored actions have distinct identity/target checks. Do not require static pixels or silently fall back between modes. UNKNOWN is never replayed. See [architecture](docs/en/virtual-screen-architecture.md) and [ADR 0003](docs/en/adr/0003-virtual-screen-lifecycle-and-input.md).
- **Microphone:** declare both `RECORD_AUDIO` and `MODIFY_AUDIO_SETTINGS`. `BrowserMicrophone` requests permission only on Web request, not ordinary startup. Allow pure audio only from the current local page; reject camera/screen audio. An old callback cannot approve a new page.
- **Device-acceptance experience:** `uiautomator dump` suppresses other accessibility services. Screenshot grants bind DSH generation and expire on stop/disconnect/revocation. Store screenshots in app-private Pictures/DSHA, without all-files access. PiP can cover lower controls; automation must check actual visible region/orientation. Screenshots/UI reads must not put sensitive values in public evidence.
- Register `rikka.shizuku.ShizukuProvider`. Standard uses 13.1.5, Low 12.2.0; do not conceal minSdk 24 with overrideLibrary. Validate manager UID, Binder descriptor, one-shot request, and timeout in callbacks.
- Built-in `dsh-web-mobile` is 3.3.5 at upstream main `646fe837440f9939228bdba0024d407eaac01128`. `tools/apply-mobile-client-patches.mjs` manages local changes. Do not restore withdrawn upstream viewport changes or reapply rc1 navigation patches now owned upstream.

---

## Startup contracts

- `welcomed == false` → `WelcomeActivity` → Start → `MainActivity`. Main checks `welcomed` before entry; otherwise return to Welcome.
- Normal execution checks `.offline-extracted` and complete environment identity. Maintenance may allow a limited Main for configuration/logs; **it must not forge readiness markers**. Terminal/Web/plugin execution still passes environment gates.
- Startup failure enters native `StartupRecoveryActivity`; waiting for authentication alone is not failure. The latest five redacted startup records live independently in private storage.
- Compatibility retry occurs once only after confirmed proroot exit, before authentication, without explicit plugin failure. **Timeout cannot trigger it.**
- Host `ConfigurationSnapshots` stores each file's content outside rootfs, keeping three healthy and three pre-repair snapshots. A committed old journal must not overwrite later configuration edits.
- DocumentsProvider preserves existing opaque `root` and `linux/ubuntu/...` IDs. Resolve guest absolute links within rootfs; deleting a link does not recurse into its target. Validate an opened file descriptor before truncating a write target.
- SMS queries are a separate sensitive capability: strict `content query` for the current Android user only. Native preauthorization defaults off, is revocable, and is not restored from system backup.

---

## Known traps inherited from the original implementation

- **Stop uses PID files plus birth identity, not reverse port lookup.** Non-root `/proc/net/tcp` reads may silently be empty, and `/proc` can use hidepid. Startup writes `echo $$ > /root/.dsha-web.pid`, then `exec node`. Stop writes `/root/.dsha-stopped` first so the watchdog exits instead of instantly resurrecting. Check old-PID reuse with kernel `kill(pid,0)` and a second birth-identity check, never force-kill by bare PID/port/name.
- **SELinux blocks `link(2)` in app-private directories.** proot needs `--link2symlink`; rootfs `.l2s` for `PROOT_L2S_DIR` must bind to the same absolute host path, or dpkg hardlink chown/stat may report missing files.
- **Two signing keys have different roles:** release APKs use this fork's release certificate (`814ab103...3622f`, `keystore/release-signing.store`, alias `dsha-release`); a separate keystore signs incremental-update manifests. Never mix them. Changing the APK key would force users to uninstall and lose data.
- Android `FileInputStream(FileDescriptor)` does not take ownership. Host backups explicitly transfer ownership through ParcelFileDescriptor auto-closing streams.
- Data maintenance closes PTY/simple terminals before the RuntimeTasks barrier. A proroot terminal verifies/reaps the guest in its own current session; terminating only the launcher cannot release its work lock.
- Maintenance success text is not readiness proof. Stay on the native page if unready, without automatic navigation loops. Do not represent data-maintenance busy state with general plugin-query/terminal locks.

---

## Delivery and acceptance

- **One release channel only**: this repository's `main` [updates.json](updates.json) plus GitHub
  Releases (`steveneng2020/DSH-Android`). Do not touch the upstream repository, publish a
  Release there, or deploy a website. Steps in [UPDATES-HOWTO.md](UPDATES-HOWTO.md).
- **Mandatory checks** (missing one means the release is not done): package `dsh.android.dev`,
  certificate `814ab103...3622f` (v1/v2/v3), `debuggable=false`, minSdk 30, arm64-v8a,
  `versionCode` strictly greater than the published value in `updates.json`, asset/licence/ELF/
  plugin/emergency gates, and `sha256` and byte size matching the Release asset exactly.
- **State the acceptance scope honestly**: local verification must not be written up as a full
  device matrix. Virtual screen, accessibility, vendor ROM behaviour etc. are reported per actual
  evidence; what was not run is reported as not run.
- Large generated archives (rootfs / dsh-runtime / ubuntu-tools) are not committed; they are
  produced during the build with verified digests. Never upload private keys, user data, device
  screenshots or logs.

## Coding conventions

- Write comments/UI strings in Chinese; use Chinese commit messages with a `type:` prefix explaining why.
- Give each collaborator one responsibility. Put pure logic in `util/` with tests, and preserve historical SharedPreferences keys.
- Match existing style: guard risky operations with try/catch, degrade gracefully, and show useful failure toasts.
- Center native buttons/options consistently, including font padding. Ordinary cards, primary buttons, and text states share theme resources; no separate gradients or hardcoded colors creating mismatched frames. Layout changes run style acceptance through `LayoutAuditInstrumentation` in Chinese/English, day/night, short screens, and 1.3× text.
- App dialogs use `DshaDialogBuilder`. Custom content must scroll on short screens/large fonts. Render application state through `UiStateText` at display boundaries rather than caching a language.
- DNS defaults to `auto`: Node dual-stack lookup retries IPv 4 once only for `EAI_AGAIN` / `EAI_FAIL`, without replaying HTTP or downgrading explicit IPv 6. Configuration also offers `ipv4` (glibc `no-aaaa`) and `native`. Web/plugins/shell/PTY share RuntimeTools preload environment.

---

## Documentation and workflow references

| Document | Content |
|---|---|
| [BUILD](BUILD.en.md) | JDK 17/SDK 37/NDK 26/Python 3.9+, build, signing, publication/delivery |
| [Security model](docs/en/security-model.md) | Security boundaries and known weaknesses |
| [Plugins](docs/en/plugins.md) | Plugin installation, packaging contracts, validation scope |
| [Historical releases](docs/releases/) | Release notes and device acceptance, with each artifact's original attribution |
| [CHANGELOG](CHANGELOG.md) | Complete historical change record |
