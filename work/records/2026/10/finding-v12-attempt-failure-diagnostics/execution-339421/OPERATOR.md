# Owner operations — W333486 execution packet, revision 5

**`COMMANDS.md` has the five exact commands with no placeholders.** This
document is what each one does and what to expect. Read both.

**The start is NOT SELECTED.** Every input gate this Work had is closed —
W333735 at `a9f4fa4d`, W334910 at `fb487979`, W338305 at
`bc925cf5c62d69426ed5862af4d41f4d2a967b0f`, and the W337955 scheduling edge
removed at339410 as fulfilled. That is not a start. What remains is independent
preparation review and then an exact execution selection. Steps 0 to 3 are
authorized preparation and produce no execution.

**Three things that will bite you if you skip the rest:**

1. **Do not use `commands.json`'s `start`.** The accepted composer still
   generates the unenforced supervisor invocation. Use step 4 /
   `packet/AUTHORING-COMMAND.json`.
2. **Do not expect a 3600-second run.** `tokens.LIFETIME_SECONDS` is still 900
   and renewal is not in this base. The two corrections make that lease
   *enforced* and its *ending* bounded — neither makes it longer.
3. **A missing or partial final report is incomplete, not success.** Three
   files matter after a run; `SHUTDOWN.md` names them and step 5 lists them.

Nothing below has been executed against the selected root. Preparation was
exercised once into `/tmp/w333486-preflight-339421`; the proposed root
`/home/sl/baton-instances/attempt-diagnostics-w333486-339421` is untouched and
**does not exist**, no Job is submitted, no engine or container was invoked, no
provider was contacted, no credential was read.

This packet **supersedes `../execution-333504`, `../execution-333707`,
`../execution-334663` and `../execution-337453`**, all preserved unchanged. The
failed instance at
`/home/sl/baton-instances/attempt-diagnostics-w333486-334663` is preserved and
is **never reused, rerun or recovered**.

## Why revision 5 exists

`../execution-337453` was independently accepted as preparation
(review-2026-10-20T02-05-28Z) and then held for the finalization assessment.
That assessment produced the shutdown correction, the correction was accepted
and committed, and it moved exactly the bytes execution-337453 pinned:

| input | execution-337453 | this packet |
| --- | --- | --- |
| `tools/authoring_enforcement.py` | `bc8c0363…` | **`d12769df…`** |
| supervisor `baseline.py` | `c1b0a10e…` | **`8e5987f5…`** |
| `tools/authoring_shutdown.py` | *did not exist* | **`af9e5ea6…`** |

So that packet is not launchable — not because anything is wrong with it, but
because its pins describe a vehicle that is no longer the accepted one. The new
`tools/authoring_shutdown.py` is imported by the controller, so it had to reach
the staged composition: **114 pinned manager files, up from 113.** Measured, not
assumed: importing the controller from a staged source with that file removed
fails with `ModuleNotFoundError`. `SHUTDOWN.md` is the whole account.

## Step 0 — read-only input check

Opens no store, writes nothing, starts nothing. **Run this first.**

It separates **refusals** — base bytes, the 114 pinned manager files, the
pinned corrected controller and the pinned shutdown helper (each checked against
the pin, the packet's manager source *and* the base), the bootstrap binary, a
damaged decision snapshot, an absent task input, a checkout document missing
from the base, an already-present gate module, a provenance claiming an
authorized or selected start, an absent `ENFORCEMENT.md` or `SHUTDOWN.md` —
from **reports**: a `DECISION-SOURCE DRIFT` section that exits 0, because the
turn reads immutable snapshots and an ordinary update to the reviewer-owned
`FINDING.md` or `PLAN.md` must not invalidate a sealed packet.

Measured here: 0.116s, clean, no drift.

## Step 1 — stage

The `--acknowledge-unselected-start` flag is required and is not ceremony:
without it this refuses and prints why, including the startup failure. It proves
every base byte **before** creating anything, then creates the root `0700`,
refuses an existing one, and writes the base's manager and supervisor source
into it. A refused stage leaves the filesystem exactly as it found it — all
nineteen probes that could create a root also assert that it was not created.

## Step 2 — bootstrap this instance's own authority

`--no-repositories` is deliberate. It generates this instance's own authority
uuid, so **expect your composed packet digest to differ from the preflight's** —
`bind` derives the Work id from that uuid and it travels into the submission.
The preflight's uuid `a5cdffad82ca410caca041b69b91d6f0` and packet digest
`199e6323…` are facts about the throwaway root, not proposed production
identities.

## Step 3 — bind

Composes the packet documents under `<root>/packet/`, proves them
(`held_packet` re-pins every artifact including all 20 `fixture.files`;
`verify_imported_sources` proves the process is running the staged code),
refuses a root that already holds a composed packet, and writes
`<root>/packet/AUTHORING-COMMAND.json`. Ends with `PREPARED.json: state
prepared-not-executed, start_selected false, composer_start_is_unenforced
true`. **No Job is submitted.**

## Step 4 — start: NOT SELECTED YET

`packet/AUTHORING-COMMAND.json` carries exactly the step 4 command,
machine-readable, with the controller's and the shutdown helper's staged paths
and digests. The invocation is unchanged by either correction; `--status-path`,
`--child-of` and `--lock-fd` are internal, passed by the watchdog to the child.

Measured in preparation, read-only: the corrected controller's own
`verify_controller` **accepts** this packet from the staged source and
**refuses** one imported from the host checkout. A packet pinning the
**superseded** controller digest is refused before any root is created, and so
is one that fails to pin the shutdown helper.

`SIGINT`/`SIGTERM` sets the enforcement stop and begins the reserved cleanup
window; the controller requests the child's bounded shutdown by writing its
deadline, then terminates it, and reports `state: held`. **A held outcome is not
proof of cessation**, and a missing final status snapshot is also held.

Before starting, confirm the credential profile this packet names resolves in
your own private registry (`/home/sl/.baton/credential-sources.json`, slot
`claude`, reference `w202663-development`) and that the image reference is
available. This packet reads no credential, carries no bearer and contacted no
registry.

## Five things to know before a start is selected

1. **The previous start failed in 0.506s.** Two managers for one workspace;
   `hold_manager_instance` correctly refused. Corrected — but **no authoring
   invocation has ever completed for this Work**, and two corrected failures are
   not evidence that a full invocation completes. If this one also fails, the
   honest account of how far it got is the deliverable, and the failed instance
   is preserved rather than retried.

2. **The 900-second lease is enforced, not extended.** Expect expiry at 900
   seconds with cessation ordered, partial output retained and a held outcome.
   `TASK.md` item 6 instructs the turn to report the actual expiry, cleanup,
   retained-output and recovery behaviour, naming each of the three final-result
   files by presence and content.

3. **The verification ceiling is 30 seconds and is not this packet's to set.**
   The ten gate modules measure 13.642s (1124 tests, zero skips), leaving
   ≈16.36s for the two the turn must write. That fit **remains unproved**, and
   no coverage may be removed to force a pass. Two real-process modules are
   excluded from the gate for measured ceiling reasons —
   `test_authoring_shutdown_deadline` at 51.333s for 4 tests, over the whole
   ceiling by itself, and `test_authoring_manager_guard` at 19.888s for 7 — with
   their coverage carried by reused accepted proofs.

4. **Two excluded test modules already fail at base**, both explicitly
   unverified baseline reports with no cleanup selected:
   `tests.manager.test_boundary_inventory` and `tests.tools.test_packaging`'s
   subcommand case, which holds the source command table against the installed
   bundle. A source-level case is **not** proof that a rebuilt bundle carries a
   new verb.

5. **A bounded first milestone is allowed.** PLAN permits delivering a coherent
   slice that fits 900 seconds with the remaining work stated explicitly — but
   not weakening final acceptance, and not promising full completion in one run.

## Step 5 — after a run, if one is selected

Read the three final results (`COMMANDS.md` step 5) before concluding anything.
`SHUTDOWN.md` has the rule: a missing or partial report is incomplete, never
acceptance and never proof of cessation; phase evidence names the last step
*entered*, not finished.

The retained proposal is immutable and is **not** an accepted candidate. An
independent reviewer consumes it through v11 after exact runtime cessation; no
automatic integration, no self-acceptance. A failed or partial run is preserved
and reported with its evidence rather than retried silently. Parent W325959
consumes this jointly with W333485, and the human Git checkpoint the parent PLAN
carries remains pending.

## Retained temporary paths

Left in place for you rather than removed. None is a selected root; none holds a
credential or a submitted Job.

- `/tmp/w333486-preflight-339421` — this revision's exercised preparation root
- `/tmp/w333486-base-339421` — a clean export of the declared base (including
  the supervisor directory the enforcement tests need), used for the gate
  measurements
- `/tmp/w333486-probe-339421` — the probe copies and their roots
- `/tmp/w333486-helper-probe-339421` — the staged source with
  `tools/authoring_shutdown.py` removed, which proves the import fails
- the earlier revisions' roots: `/tmp/w333486-preflight-337453`,
  `/tmp/w333486-probe-drift-453`, `/tmp/w333486-base-fb48`,
  `/tmp/w333486-preflight-334663`, `/tmp/w333486-probe-drift-663`,
  `/tmp/w333486-base-a9f4`, `/tmp/w333486-preflight-333707`,
  `/tmp/w333486-probe-drift-707`, `/tmp/w333486-base-probe`,
  `/tmp/w333486-preflight-333504`, `/tmp/w333486-probe-drift`

The **failed selected run** is not in this list: it lives at
`/home/sl/baton-instances/attempt-diagnostics-w333486-334663` and is preserved
as evidence, not as a temporary path.
