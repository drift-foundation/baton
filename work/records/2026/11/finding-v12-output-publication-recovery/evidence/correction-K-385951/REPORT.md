# W385695 — C5 script cleanup corrections R1 and R2 (review 2026-11-24T05-49-33Z, M385949/M385951)

**For independent review. Preparation only. Not accepted, not imported, not qualified.**
Author: baton.prompt (K), owner-selected interactive continuation, no claim.
No product source change, source test rerun, host import, protected Git mutation, image build, engine or container operation, live model call or credential read.

No new decision is raised.

## 1. Source: unchanged, not repackaged

Accepted manifest `162152b462b8ab0907a43b5dd41f85e8c7c2a6218053b6a93bbf9edc1762a8dd` in `evidence/correction-K-385937/`. `source-unchanged.json` records the check at sealing: 50 scratch paths equal the manifest by sha256 and mode (scratch head `6d6a4fc8`, clean), and both earlier packets still match their own indexes. I did not read or touch the host import.

## 2. Scripts

| File | Reviewed (revision 4) | This packet (revision 5) |
| --- | --- | --- |
| `qualify-w385695.sh` | `d8c579d3…` | `622d776c619dfb3757d7d7e76e9325f4b6bf33de06d9410555b948477301200d` |
| `option-a-setup.sh` | `976476ac…` | `d6aed7b5103e0efe33b883aad5457b82a147cb27c05cf2223fe09538e9f0a233` |
| `cli-in-image-driver.py` | `b3a722ef…` | unchanged, `b3a722ef406bb81ed0e84cadf2c0a4983dc3fe92a61532b9992d9a4217a1370d` |

`provenance/*.r4-to-r5.diff` is the whole change. The stack functions remain byte-identical in the two shell scripts.

## 3. R1 — a missing or unreadable operation record stays unresolved

**Start intent, both scripts.** After the intent, reconciliation now proceeds only on one of three positive facts:

- the completion record exists;
- the start command's own record is readable (exactly a pid and a start time) and that process has positively ended;
- this same invocation wrote the intent and never reached the fork. It knows that from a stage it sets before writing the intent and changes before forking; a later invocation never has it.

Anything else is `UNRESOLVED`: no record, an empty one, or one that does not parse. The intent is retained, nothing is stopped or filed as reconciled, and `start_stack` refuses to start over it. The three-second allowance remains only to let a just-forked child of the same invocation write its record; when it runs out the answer is unresolved, not ended.

**Pause intent.** The same rule. With no readable record of the pause request the phase is `UNRESOLVED` and the intent is retained. A container found paused is still released and read back, because releasing is safe either way; what stays open is that an unrecorded request might pause afterwards.

A pause that is positively settled is now filed (`pause-intent` becomes `pause-reconciled`), and the `deadline` phase refuses to freeze anything while an unreconciled pause intent is present.

**An unresolved intent is the operator's to clear** once they have established that nothing is running. No script removes it.

## 4. R2 — a failed image removal fails the phase

A removal that fails now sets the unresolved flag, so `cleanup` exits nonzero. `images.owned` is not edited, the message names the recorded image id, and nothing is forced. Successful removal, positive absence and a tag that now names another image keep their outcomes.

## 5. Evidence

Doubles only. Prepared interpreter, disk-backed scratch, bytecode writing off.

| Run | Result |
| --- | --- |
| Reviewer's `probe-restart.py`, packet path changed only | 3/3 (was 0/3) |
| `probes/probe-cleanup-r5.py` (new) | 17/17 |
| Reviewer's `probe-cleanup-cuts.py` and `probe-driver-ownership.py`, path changed only | 3/3 and 1/1 |
| Reviewer's copy of `probe-qualification-r3.py`, byte-identical | 4/4 |
| `probes/probe-cleanup-r4.py`, fixtures corrected (below) | 10/10 |
| `harness/qualify/run-affected-r5.sh`, the scenarios these edits touch | 9/9 as required |

**The new probe** asks the exact functions of both scripts:

- *Start, negative:* no record; five unreadable records; an invocation that forked and finds no record; a new start attempted over a retained intent (refused, nothing started).
- *Start, positive:* completion record; recorded command positively ended (its stack is then stopped); recorded command still running (waited for, then reconciled); intent written and never forked.
- *Pause:* no record and two unreadable records (unresolved, intent retained, the paused container still released); completed request (filed); recorded request positively ended; `deadline` refusing over a retained intent.
- *Images:* failed removal (exit 1, record kept, one removal asked, not forced); success; positive absence; tag naming another image; engine not answering.

**One probe of mine had to change.** `probe-cleanup-r4.py` built its retained pause states without any record of the request and expected them to resolve. That is exactly the state R1 says must not resolve. Its fixtures now carry the completion record; its assertions are unchanged. The revision-4 copy is in the earlier packet.

The 40-scenario matrix was not repeated. I reran only the scenarios whose path these edits touch. A first version of that short runner was generated by a filter of mine that dropped two expectation lines and picked up two unrelated scenarios; I discarded its log, wrote the runner by hand and ran the nine again.

## 6. Limits

- Unchanged from the last packet: token ownership is unproved against an installed bundle; the product's `status` is read as text; a process outside the stack's records is reported, not signalled.
- A script killed with SIGKILL still runs no cleanup. What changed is that a later invocation no longer treats a missing record as cessation. That later-invocation path is exercised at function level, not by killing a whole phase.
- Every engine phase, the fixture image build and the in-image CLI check remain unexecuted.
