# DSHA v1.4 20261111@0.2.2-rc.1・ build20050357

This build is rebuilt on upstream DSHA 0.2.2 (upstream build357), bundling DSH 0.2.2-rc.1 on Ubuntu base 10.

- Fixed the blank startup page after upgrades, the unresponsive "Start DSHA" button, and occasional stalls on the recovery page.
- Fixed maintenance getting permanently stuck on "stop Web and terminal tasks", where retrying did nothing either: the stop barrier could not recognise the container supervisor this app launches itself, treated it as an unidentified process and never released the barrier.
- Fixed old instances staying permanently at "identity unknown" and refusing to start after an APK upgrade or downgrade: a superseded-build check now recognises a package swap as a definite expiry and routes into the install-and-repair page instead of hanging.
- Added automatic reasoning-effort adaptation: models that declare no reasoning effort get the declaration filled in (DSHA does not guess which levels a third-party model supports; undeclared means no reasoning level is shown). Additive only, with an automatic config backup before writing.
- The launcher icon is tappable to switch between six palettes; the change takes effect immediately and is remembered. The About page and About dialog share the same icon source, so tapping either opens the switcher, and the icon now fills its canvas.
- The post-switch notice now appears as an inline bar inside the icon dialog instead of a Toast floating at the bottom of the screen: the bar shows the chosen palette's icon and text and hides itself after 2.6 s. The six-row list became scrollable and the bar keeps a fixed minimum height, so it is no longer squeezed to a sliver on short screens.
- Fixed a crash after switching the icon from the About page: the switch callback used to require the page context, which throws once the page is gone and takes the process down; it now silently skips the refresh when no context is available.
- Plugin capability hints gained a native dependency precheck: a read-only inspection of the ABI and file header of bundled native modules, warned about but never blocking installation.
- Added the changelog panel: the About page shows releases in blocks and can expand all of them; the About DSHA dialog embeds the same changelog inline.
- Added upstream comparison: shows whether the code differs from upstream, read-only and never written back.
- The About page community entry now uses the contact email steveneng@163.com; the update page's "view releases in browser" and its stable and preview links point at this repository instead of the upstream release page.
- Release identity stays independent: package dsh.android.dev with its own release certificate, not interchangeable with upstream dsh.android.client; in-place upgrade requires the same signature.
- Single variant: the compatibility line and GeckoView are removed; only Standard ships (Android 11+, arm64-v8a, system WebView).
- Merged upstream DSHA 0.2.2 (upstream build357), bundling DSH 0.2.2-rc.1 on Ubuntu base 10: mobile UI v5, a standalone device-capability authorisation page, the maintenance-time plugin registration deadlock fix, and every upstream commit since the previous merge (upstream v0.2.1-rc.2, upstream build190). The branch was rebuilt on a real upstream commit (5e2dca92, 2026-11-11), so future upstream updates merge directly instead of being force-fitted.
