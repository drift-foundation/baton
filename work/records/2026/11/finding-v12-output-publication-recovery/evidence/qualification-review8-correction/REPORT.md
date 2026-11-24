# Recovery-8 reviewer correction

Owner selected direct correction before another qualification. No protected Git mutation, instance update, Job restart or live model call was made.

## Findings and changes

- The required verification copied the read-only candidate into the adapter's 32 MiB private `/tmp`. The retained tree is about 1.7 GiB. `tmpfs-probe.py` invokes the real adapter in the selected image and reproduces ENOSPC and `not-run`. The corrected adapter uses the existing per-attempt disk-backed `/scratch`; supervisor ledgers remain small and private. `disk-probe.log` proves a 40 MiB source verifies with >31 MiB of `/tmp` free. This engine-only probe overlays the exact corrected adapter read-only; the forthcoming refresh script repeats it against a built image without the overlay.
- A supervisor returning without a completion record was incorrectly classified as timeout. It now returns unclassified with an explicit missing-record explanation. Actual deadline expiry remains a timeout. Copy preparation failure is recorded as copy-failed or copy-deadline without exposing raw exception text.
- Publication recovery kept reporting an open review after the host froze its `unable` result. Recovery observation now reports exceptional and owes the existing owner notification. Notification still requires positive cessation; no verdict, retry, cleanup or episode retirement is fabricated. The existing generic held-review custody policy remains intact, and the owner item names retained-runtime cleanup.

## Verification

Affected logical group: job_manager. Prepared interpreter and supported focused recipe; disk fixture roots outside the checkout.

- Focused initial checks: 32 passed in 13.111 s.
- Three affected modules: 437 collected/executed/passed, 0 skips/failures/errors, 143.231 s. Source identity before the final status ordering adjustment is source-before-status-order.json.
- Final connected class: 28 collected/executed/passed, 0 skips/failures/errors, 80.597 s. Covers the final source, including failure notification and restart replay without retry. These overlap the wider run and must not be added as unique tests.
- Engine-only probes: basic supervisor passes; old memory placement reproduces ENOSPC; corrected disk placement passes. No credentials or real providers.
- The supported read-only publication-status command was exercised against recovery-8. Its deadline has since elapsed; status-corrected-final.json reports exceptional with the separate expiry cause. No manager was resumed to publish a new owner item there.

The first read-only CLI probe used the unsupported global-options-first ordering for publication-status and refused before reading; the command-first invocation succeeded. Existing ResourceWarnings in tests are retained. One host `tail` utility crashed reading manager.log; `cat` read the same file successfully.

## Remaining and operator command

`python3 /tmp/baton-w385695-refresh-review.py`

This verifies 56 source identities, runs packaging, builds a provider image by replacing only claude_agent.py over the qualified pinned provider base, then the labelled scripted CLI fixture. It checks adapter bytes in both images and the disk-copy behavior in the built fixture. It creates no Job and calls no live model. Durable script: owner-refresh.py. `--check` passed without building.

After this build, bind its exact runtime/image identities into a fresh bounded scripted recovery gate; the independent deadline gate and human Git checkpoint remain outstanding. Do not rerun recovery-8, which is expired. Its exited reviewer and frozen evidence remain retained. W385695 is not closed or qualified by these source tests.
