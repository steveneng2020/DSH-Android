# DSHA v1.4 20261111@0.2.2-rc.1 / build20050357

This build is rebuilt on the DSHA upstream 0.2.2 (build357) base, bundling DSH 0.2.2-rc.1; the Ubuntu base environment remains 10.

- Base upgrade: from upstream 0.2.1-rc.2 (build190) to 0.2.2 (build357), including mobile UI v5, a standalone device-capability authorisation page, and the maintenance-time plugin registration deadlock fix.
- Single variant: the compatibility line and GeckoView are removed; only Standard ships (Android 11+, arm64-v8a, system WebView).
- Fork features retained: tappable app icon with six colour schemes, the update-log panel, upstream comparison, automatic reasoning-level fitting, and the plugin native-dependency check.
- Release identity stays independent: package `dsh.android.dev` with this fork's own release certificate, not interchangeable with upstream `dsh.android.client`; upgrading over an existing install requires the same signature.
- The update feed still points at this repository's `updates.json`; APKs are served from this repository's Releases.

This build's `versionCode` is `20050357`. Users on an older build will not see it under "check for updates" (the updater requires a larger versionCode) and must download and install it manually.
Actual software checks and on-device acceptance are limited to this round's delivery receipt and do not prove a complete device matrix.
