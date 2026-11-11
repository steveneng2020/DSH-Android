# Build, validate, and submit

> **This file covers the fork only** ([steveneng2020/DSH-Android](https://github.com/steveneng2020/DSH-Android)).
> Upstream [DSH-APP/DSHA](https://github.com/DSH-APP/DSHA) has its own process; do not mix them.
> Package `dsh.android.dev`, certificate SHA-256 `814ab103...3622f`, not interchangeable with
> upstream `dsh.android.client` / E7E3.

Read [README](README.en.md), [AGENTS](AGENTS.en.md) and [BUILD](BUILD.en.md) first.

## Source and tool identity

Java 17, single `:app` module, pure Java (0 .kt files). Only `standard` ships: minSdk 30, system WebView, arm64-v8a, package `dsh.android.dev`. The `low` flavor (minSdk 23, Gecko) still exists in the tree but was never released and is not a distribution target.

- Application version and fixed filename rules: `app/build.gradle`.
- DSH version and npm content: `tools/dsh-runtime/package.json`, `package-lock.json`.
- Bundled tools: `tools/runtime-tools.lock.json`.
- Built-in plugins: `app/src/main/assets/builtin-plugins.json`.
- Active/specialized/retired runtime patches: `app/src/main/assets/runtime-patches.json`.
- Independent emergency archives: `tools/recovery-runtime/lock.json`. Updating the main environment must not silently replace this lock.
- CI tools and historical release certificate: `ci/toolchain.lock.json`, `ci/release-identity.json`.

Normalizable source uses actual LF. Nineteen necessary small binaries and historical originals retain exact bytes. Do not transform line endings in the twelve managed/canonical bytepins listed by `.gitattributes`, rewrite the whole repository, or use newline-insensitive hashes to conceal packaged-content changes. Corresponding scripts generate Java, descriptors, and proofs. Four UUID call sites restore the shared Ids dependency while preserving the historical UUID format.

## Prepare inputs

Historical F8's 999-member Java proof, prior staged reading/style-equivalence proofs, and F7 host-Core rebinding failure/fix positive/negative controls keep their original records. They are not the current adoption scope or test numbers. Old software, APK, and device conclusions belong to their own source/digests; final software and precise APK results are bound by the unified receipt.

The APK's approximately 85 MB offline-rootfs is a transformed packaging layer and cannot reconstruct the approximately 304 MB original rootfs. This work provides no “recover all inputs from APK” helper or guarantee. The final complete source ZIP's SHA-256 belongs in the Release body, not the ZIP's own README.

Complete source retains build-required, already tracked, notice/lock-covered small JNI/vendor/interpreter precompiled dependencies. Disclose unknown-source or proprietary limits; this does not make all vendor native code source-reproducible. Describe provenance, licensing, and build paths from actual material. Do not delete required consumer inputs to advertise “pure source.” The retention inventory also includes 27 necessary historical build sources and one website test fixture, without deploying the website.

Do not upload private keys, user data, device screenshots/raw logs, or historical audit source material. Large generated archives are excluded from Git. Release source ZIPs contain only registered, verified original large inputs. `docs/audits/` allows exactly these nine JSON files at original paths: six consumed by build/CI and three preserving real historical documents/provenance. They are not raw device logs or a general exception for the whole historical audit directory:

- `docs/audits/build154/retired-audit-sources.json`
- `docs/audits/build154/engineering-retired-sources.json`
- `docs/audits/build156/retired-test-control-sources.json`
- `docs/audits/build156/third-party-license-sources.json`
- `docs/audits/build156/retired-asset-sources.json`
- `docs/audits/build156/retired-environment-data-sources.json`
- `docs/audits/build154/history-document-sources.json`
- `docs/audits/build156/shellservice-source-provenance.json`
- `docs/audits/build156/source-docs-retained.json`

Documentation closure follows the exact [documentation-index](docs/en/index.md) inventory: six genuine historical explanations, a recovered Termux historical README checked against its original digest, and five newly created navigation mirrors. Mirrors copy specified source text byte for byte and do not pretend to be recovered historical preservation originals. Do not rewrite old originals or upstream licenses. Other historical JSON ledgers, raw device logs/screenshots, and private forensic material are not included merely because prose refers to them.

Complete generation entry points:

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

The original Ubuntu archive remains a separately fixed input. Installing dependencies or upgrading DSH does not itself upgrade base-environment identity. Preserve historical pinned emergency copies; changed main archives must not automatically relax their digest checks.

## Validation

The fast source stage needs no private key:

```bash
python3 tools/run-host-tests.py --check-manifest
python3 tools/run-host-tests.py --stage fast
python3 tools/check-source-hygiene.py
```

After complete inputs are ready, run unit tests and Release Lint for the current production source set:

```bash
./gradlew :app:testStandardDebugUnitTest :app:lintStandardRelease

python3 tools/verify-stability.py --stage software
python3 tools/run-host-tests.py --stage runtime
```

A host unable to run AGP/aapt2 may use `tools/run-unit-tests.py` as a pure-logic fallback. It compiles test support classes but does not replace an Android build. Test entry points reject `-O`, and release checks do not disappear under Python optimization.

`ci-fast` runs source/protocol checks. Complete `ci-package` needs verified binary inputs and produces unsigned packages only; never install them. Record repository protection, completed online workflows, and actual Linux/Android matrices from real execution evidence, not configuration files.

## Release packaging

Explicitly configure `DSHA_KEYSTORE`, `DSHA_KEYSTORE_PASSWORD`, `DSHA_KEY_PASSWORD`, and optionally `DSHA_KEY_ALIAS`. Missing passwords no longer fall back implicitly. Use only this fork's release certificate (`814ab103...3622f`, alias `dsha-release`); **E7E3 is the upstream certificate and must not be used**, nor debug or temporary CI certificates.

```bash
./gradlew :app:assembleStandardRelease
```

The delivery scope is `standard`. Check the actual package for `dsh.android.dev`, certificate `814ab103...3622f` (v1/v2/v3), `debuggable=false`, minSdk 30, arm64-v8a, assets, licensing, ELF, plugins, and independent emergency gates. Report tests and Release Lint per actual execution; do not claim a fully cold-network build.

All phone operations are paused: no installation, startup, stop, input, conversation, or ADB reconnection for evidence. Historical same-signature upgrade records retain their original APK attribution, not a new APK's. Do not uninstall, clear data, inject faults, or create extra audit APKs.

**Publishing** uses only this repository's [`updates.json`](updates.json) plus GitHub
Releases: upload the APK, update `updates.json` (`versionCode` strictly greater than the
published value), push `main`. Do not touch the upstream repository, publish there, or
deploy a website. Do not claim publication before an actual tag/upload result exists.

## Changes and review

Use the `codex/` branch prefix by default. Preserve old SharedPreferences keys, data-format readers, document IDs, originals, and stop barriers for unknown processes. State the changed responsibilities, persisted fields, protocols, and validation evidence.

Reproduce fixes through the real production entry point or isolated real dependencies. Record source-constraint checks separately from device behavior. Original data is read-only, and historical records state version/time. Without hardware evidence, do not say a device path is verified. Every audit item needs a disposition and remaining limits; an allowlist or uncalibrated score cannot establish that all debt is gone.

Before editing, use the [documentation index](docs/en/index.md) to locate implementation, platform references, and tests. Changes to defaults, permissions, or networking must update the topic page and migration explanation, not just code comments.
