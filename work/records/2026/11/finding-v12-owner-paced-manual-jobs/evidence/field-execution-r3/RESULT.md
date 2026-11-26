# First MANUAL field run that completed — packet r3

Recorded by K (`baton.prompt`, Fable 5.2) from the run root `/var/tmp/baton-manual-field.lw8K8KWf`, which the owner ran and which is kept in place. This directory holds copies of the run's small evidence files and both reports (`SHA256SUMS`, 26 files); the 6 GB of source clone, build, bundle and instance stay in the root. I prepared packet r3, so this is my reading of my own packet's run, not an independent review. `FACTS.json` is derived from the copied files by the checks below.

- Packet: `../field-76b2f2b2-r3/`, manifest `df46073ef97dc30a232c65ff6098b2ff42620817b3612b223177c4b3cd706f9e`. Exit 0.
- Packaged source: `76b2f2b2359a1211139625f8f5062d980c5f68bf` plus `packaging-fix.patch` `9ff28a67…`, clone commit `a24fe259…`; the installed stack reported that commit, frozen, clean.
- Transcript SHA-256 `b27a6f6fa9e3b422cb673b21e15fb9423c1774a367997809388482aa0ef599bf`. No traceback in it.

## What the run showed

| Step | Observed in the evidence |
| --- | --- |
| Packaged composition before Docker | `PREFLIGHT PASSED`; the installed bundle carries `worker_instructions.md` byte-equal to source |
| Create and add `guide` | one phase, `queued`, no selection instant, no attempt (`initial.status.json`) |
| `start guide` | completed; report 127 bytes, equal to the text computed on the host from the pinned `v12/QUICKSTART.md` blob (26,309 bytes) |
| Restart | `stop` ended manager pid 3294481 and publisher 3294482; `start` began manager 3295240 and publisher 3295241 and waited for a fresh snapshot. Before and after: same attempt `attempt-4bbe704b…`, same result record, same selection instant, 14,926 ms charged both times; report bytes identical |
| Add `overview` | present with no selection and no attempt while `guide` stays completed (`added.status.json`) |
| `start overview` | completed on the same worker `field-research`, second attempt `attempt-8f6d1173…`; report 123 bytes, equal to the text computed from the pinned `v12/README.md` blob (20,934 bytes) |
| Before close | Job on the to-do list with both phases finished |
| `close field-survey` | `MANUAL · CLOSED`, `2 finished · 0 failed · 0 never selected`; `monitor --todo` says no open MANUAL Jobs; both reports read again and equal |
| Budget | 28,906 ms charged of 360 s: 15.0 s for `guide` plus 14.1 s for `overview` by their own selection and settlement instants. The pauses and the restart added nothing |
| Cleanup | field image deleted, network removed, no retained runtime reported |

Each phase has exactly one episode in the final status.

## What it does not show

- Containers were not counted, so a second launch of the same attempt would not have been noticed. One episode per phase and no leftover container are the only indications.
- The status document's `incarnation` is the publisher's fixed name, so it does not show the restart; the process identifiers in the transcript do. My earlier suggestion to compare that member was wrong.
- The provider was the deterministic fixture. No model, no real credential, one worker, no hold, no `finish-phase`, no capacity wait, no budget expiry.

## Verification of the packaging correction with this run

- The working tree's `v12/python/packaging/stack.spec` (`05b11b25…`) is byte-equal to the spec this run packaged.
- `tests.tools.test_packaging` with the run's bundle named as the bundle under test and the gate variable set: 13 of 13 pass, including the new carried-file case and the new no-bundle case.
- The stale bundle under `v12/python/build/out/` still predates the fix; the bundle case fails against it until it is rebuilt.
