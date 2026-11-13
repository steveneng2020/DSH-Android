# DSHA v1.5 20261113@0.2.2-rc.1・ build20060457

This release fixes the separator rendering and the update check on top of v1.4, and ports four robustness features missing upstream.

- Fixed the app icon on the update page header and in file managers not following the colour scheme: it was hard-wired to the old default image, so those two places kept showing the old artwork after switching icons.
- The version separator is now the full-width middle dot ・. The previous solid bullet sits low by design, so it never lined up with the digits beside it; changing the character is more reliable than patching the baseline, and no glyph workaround remains.
- Fixed "check for updates" always reporting no update: the version-name check inherited an upstream pattern that rejects spaces and @, while this project's name is `v1.5 20261112@0.2.2-rc.1` — so our own release was discarded by our own validation, silently.
- Reading the update feed now retries: timeouts already existed (15 s connect / 30 s read), but a single network hiccup forced a manual retry. Up to three attempts with 1 s / 2 s backoff, only for transient network errors; certificate and manifest errors are not retried.
- Safe mode now blocks installing and enabling plugins: previously it only toggled a banner while install and enable still worked, which made the mode meaningless. Disabling and uninstalling stay allowed.
- Fixed the Web entry button sticking at "opening…" after the Web generation changed: a changed generation means the one being awaited is gone. It now resets to retryable with "Web restarted, open it again" instead of being treated as a failure.
- Virtual screen now debounces consecutive frame rejections: occasional rejections are normal, but three in a row means the session's frame sequence no longer matches the picture. The stale session is dropped and rebuilt instead of leaving taps unresponsive.
- Fixed the release-notes dialog showing "this installation does not include release notes for the current build": after the title generator switched separators, the reading side still matched the old format and rejected the notes.
