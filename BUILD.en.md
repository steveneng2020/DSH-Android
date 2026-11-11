# DSHA build instructions

> **This file describes the fork only** ([steveneng2020/DSH-Android](https://github.com/steveneng2020/DSH-Android)).
> Upstream [DSH-APP/DSHA](https://github.com/DSH-APP/DSHA) has its own build docs; do not mix them.
>
> Version, package and signing identity come from `app/build.gradle` and
> `ci/release-identity.json` (`dsh.android.dev`, certificate `814ab103...3622f`); this file does
> not duplicate those numbers.

Read [README](README.en.md), [AGENTS](AGENTS.en.md) and [CONTRIBUTING](CONTRIBUTING.en.md) first.

## Environment and variants

| Input | Requirement |
|---|---|
| JDK / native application language | Java 17, no Kotlin |
| Gradle / AGP | Repository Wrapper 9.3.1 / AGP 9.1.1 |
| Android SDK | `platforms;android-37.0`, build-tools 36.0.0; compile/target API 37 |
| NDK | 26.3.11579264 (only needed when changing JNI) |
| Python / Node | Python 3.9+ for generators; CI pinning is in `ci/toolchain.lock.json`; Node 24 |
| Standard | minSdk 30, system WebView, arm64-v8a |

**Only standard is built.** The source tree still carries the `low` flavor (minSdk 23, GeckoView), but it was never released and is not a distribution target. Windows skips cannot stand in for Linux-specific tests.

Set `sdk.dir` in local `local.properties`, and point JAVA_HOME, ANDROID_SDK_ROOT/ANDROID_HOME, and DSHA_PYTHON to installed tools. Do not copy another developer's absolute toolchain paths. `app/build.gradle` defines `versionCode`, `versionName`, and `dshaApkNameVersion`; this page does not maintain another competing set of current version numbers.

## Input preparation and proofs

Git retains the complete application, resources, locked generators/checkers, and small precompiled JNI/vendor/interpreter dependencies required for builds and covered by notices/locks. Large generated rootfs, DSH, and recovery archives are excluded from Git. Retain the actual restrictions on unknown-source or closed-source vendor inputs; do not claim all native vendor code is reproducible from source. See [CONTRIBUTING](CONTRIBUTING.en.md) for exact boundaries and nine explicit audit-JSON exceptions: six build-input metadata files plus three historical-document/provenance metadata files, without opening the whole audit directory.

Distributable source uses actual LF bytes. Eleven managed/canonical bytepins in `.gitattributes` and historical originals retain exact bytes; do not normalize signed inputs across the repository. Nineteen small binary inputs remain as listed and are not rewritten by text newline rules. Shared UUID validation comes from Ids; four call sites have their shared dependency restored while preserving historical UUID format.

Ubuntu base identity is independent of DSH and UI versions. `offline-rootfs.bin` / `dsh-runtime.bin` use split-runtime-v1. `tools/recovery-runtime/lock.json` constrains independent emergency pinned inputs; the main environment cannot become a rescue dependency. A source checkout without large archives is not a complete APK and cannot skip integrity gates.

When managed inputs change, update assets through their actual generators, then explicitly generate proofs:

```bash
python3 tools/prepare-backup-assets.py --write
python3 tools/prepare-runtime-descriptor.py --write
python3 tools/prepare-test-runtime.py
```

Check generated proofs against actual bytes. Normal Gradle builds use check mode; an old cache must not skip new inputs. `app/build/test-runtimes/current.json` and source/content fingerprints constrain the current fixture. An arbitrary old directory is not the current runtime.

## Software validation

```bash
python3 tools/run-host-tests.py --check-manifest
python3 tools/run-host-tests.py --stage fast
python3 tools/check-source-hygiene.py
./gradlew :app:testStandardDebugUnitTest :app:testLowDebugUnitTest \
  :app:lintStandardRelease :app:lintLowRelease
python3 tools/run-host-tests.py --stage runtime
python3 tools/verify-stability.py --stage software
```

On Windows use `gradlew.bat` and a real Python executable instead of an unavailable system alias. When AGP/aapt2 cannot run, `tools/run-unit-tests.py` is a pure-logic fallback, not a replacement for full Android compilation, APK checks, or resource gates. Classify platform skips, unrun items, and Lint warnings honestly rather than calling them passes.

`tools/verify-plugin-upgrade-gate.py` checks automatic commit/enable behavior, user disabling/safe mode, actual dependencies, plugin transactions, and managed assets. Production plugins permit unlocked resolution, lifecycle scripts, and pnpmfile. Do not revive historical “native review/dependency freeze” test criteria as current requirements.

## Release packaging and signing

Explicitly supply existing `DSHA_KEYSTORE`, `DSHA_KEYSTORE_PASSWORD`, and `DSHA_KEY_PASSWORD` (optional `DSHA_KEY_ALIAS`). `ci/release-identity.json` defines the signing identity: certificate SHA-256 `814ab103...3622f`, alias `dsha-release`, same key as the installed build so upgrades install over it. **E7E3 belongs to the upstream `dsh.android.client` era and must never be used here.** A key filename containing debug does not make a release APK debuggable; verify actual `debuggable=false`.

```bash
./gradlew :app:assembleStandardRelease
```

The delivery scope is standard. Software validation covers the standard tests and Release Lint,
plus the actual standard APK/assets/ELF, signing, licensing, plugin/emergency gates, and exact
digests. Record selected JUnit classes, skips, cache reuse, and unrun scope separately, without
claiming a clean whole-repository or fully cold-network build.

Product: `app/build/outputs/apk/standard/release/app-standard-release.apk`. Verify package
`dsh.android.dev`, certificate `814ab103...3622f` (v1/v2/v3), `debuggable=false`, minSdk 30,
arm64-v8a, `sha256` and byte size.

**Publishing** (this repository is the only channel; see [UPDATES-HOWTO.md](UPDATES-HOWTO.md)):
upload the APK to a Release here, update `updates.json` (`versionCode` strictly greater than the
published value), push `main`. Do not touch the upstream repository, publish there, or deploy a
website. Never upload private keys, user data, device screenshots or logs.

## Phones and acceptance scope

Phone operations follow the current authorization; do not infer an exit from a "normal Stop"
message. Old build130/build142 audit results belong to their original dates and artifacts and
cannot be reused as evidence for a new build. Linux tmpfs tests do not prove persistent-disk,
power-loss or Android FUSE behaviour, and no software check proves a real device matrix.
Virtual screen, accessibility and vendor ROM behaviour are declared per actual evidence; what was
not run is reported as not run.

Before maintaining source, consult the [project handbook](docs/en/project-architecture-handbook.md) and [documentation index](docs/en/index.md). Engine, port, and DNS pages separate current defaults from historical migrations.
