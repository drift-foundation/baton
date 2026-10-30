
## 2026-10-22 — baton.claude, claim352586 — THE SELECTED RUN STARTED, AND THE ENVELOPE PERMISSION IS LIVE

Claimed W341357 at snapshot352586 after reading current canonical state
(queued, unclaimed, routed `baton.impl`, `last_change_seq 352577`, open
blockers 0, `pickup overdue`), the complete handoff through `work-events` (90
events, `next_after` null — no pagination remaining) and thread T341357 in full
(**6 messages**, `last_seq 352206`, one more than the last claim read: the
owner shutdown/preservation requirement M352206). Read
`review-2026-10-22T14-45-31Z.md`, the current `FINDING.md` and `PLAN.md`,
`COMMANDS.md` and `OPERATOR.md`.

**Owner reroute352577 selected exactly one invocation** of `execution-352156`,
manifest `9bda87e4ad655da1c1a452b901f994c5da7b4647d1a64c02ab2287866086dc2e`,
accepted by `review-2026-10-22T14-45-31Z.md`, at the fresh root
`/home/sl/baton-instances/durable-capture-w341357-352156`, with the selection
**pinned in `FINDING.md` and `PLAN.md` before execution**, pre-stage
capability then post-bind actual-boundary preflight, the generated enforced
`AUTHORING-COMMAND.json` only, bounds 3600/30/4800/60, stop at original origin
+ 4740 and expiry + 4800, one invocation, no retry, report-and-hold.

### Revalidated before acting

Manifest `9bda87e4…` **exactly as selected**. Seal 80 of 80, zero failures,
**both ways** — 81 files on disk, nothing sealed-but-missing, nothing on disk
but unsealed except `SHA256SUMS` itself. Input check exit 0 in **0.067s**: 115
manager files, 3 supervisor files, 2 preparation inputs, 68 task inputs, 59
decision snapshots, 4 checkout documents, 1 pinned controller, 1 pinned
shutdown helper, 2 pinned recovery inputs, 1 gate module still owed. It
reported `DECISION-SOURCE DRIFT` on `FINDING.md` and `PLAN.md` — the
reviewer's own post-sealing updates — **reported and deliberately not
resealed**, because resealing would change the manifest the owner selected.
Proposed root absent; the other ten W341357/W333486 roots all present and
untouched.

**The pins I was told to write add to that same reported drift, on purpose.**
Owner352577 requires the selection pinned in `FINDING.md` and `PLAN.md` before
execution, and those two files are exactly the two the packet snapshots. So I
appended an attributed implementer section to each, naming the selection, the
revalidation and what it does not establish, and left the sealed snapshots
alone. Live digests after the pin: `FINDING.md`
`c6a03479afeb45a14f8083fefa2d5eef1edafed6f509cf59e41d6fa02826dc5a`, `PLAN.md`
`0cef8a875dad42ba629609c82b6519c7d8b26ad14f613c8e1827e74e1d2b3fba`. The
reviewer owns the rest of both documents and I changed nothing else in them.

**Pre-stage capability: capable, zero denials, 0.081s**, bound to that
manifest — engine answers, image `baton-v12-claude-worker:w239528-244216`
config digest `sha256:c862c055…` equal to the pin, runtime binary `04aa459a…`
equal to the pin, distro present, credential reference `w202663-development`
present in `/home/sl/.baton/credential-sources.json` with provider
`operator-file` and its backing file present, **no credential value read**,
root absent.

**Both checks are REGENERATED, not recovered.** M352206 announced the `/tmp`
wipe and it happened: the author's claim352156 copies of the capability check
and the boundary preflight are gone, along with `/tmp/w341357-preflight11` —
which is also why the reviewer regenerated preparation rather than inspecting
that tree. I rewrote both checks against the same packet pins and the composed
packet and say so in each report, rather than presenting them as the
historical bytes.

### Stage, bootstrap, bind

Stage **0.076s**, bootstrap **0.649s**, bind **0.377s**, **all status 0**.
Authority `33bac7926fdd4ddfb15a3eae7fb4f6eb`, composed packet
`bab5b3e828e07052431c4e73e622a6b462ff61c9e97a5e42f0a2c390c3b39336` — both
different from the reviewer's and from the preflight's, as `OPERATOR.md` step
2 says to expect, because `--no-repositories` generates this instance's own
authority uuid and `bind` derives the Work id from it.

Read back from the bound documents rather than asserted:

- `PREPARED.json`: work **`W341357`** (not the scaffold's parent id), state
  `prepared-not-executed`, `start_authorized` false, `start_selected` false,
  `composer_start_is_unenforced` true.
- 115 manager members, and the member **set and every digest equal to the
  accepted W348979 binding's `manager_files` as a whole** — set equality and
  zero digest disagreements, checked against `HOST-POLICY.json` at
  `8309fd6e…`. Every staged byte on disk re-hashed against the packet's own
  map: zero disagreements.
- `packages` exactly `["baton_v12","tools"]`.
- **The one correction, read back:** `supervisor.path` is
  `<root>/code/v12/python/tools/authoring_baseline.py` — the module the
  controller actually imports — at `8e5987f5…`, which is also the digest the
  binding declares for the deferred dependency. The staged `supervisor/`
  directory copy is still present at the same `8e5987f5…` as provenance, and
  **the digest pin did not move**; only the path this packet names changed.
- Controller `248ee9ed…` and shutdown helper `af9e5ea6…` equal to the
  binding's own declarations for both.
- 68 `fixture.files`, **all 68 verified** against `fixture.source_root`
  `/home/sl/src/baton`, zero mismatches, including `recovery-345822/`'s
  `candidate.patch` at `294368c5…` and its `INDEX.json` at `70e1f2b1…`.
- `task.json`: `task_id durable-capture-w341357-352156`, `declared_base
  bc925cf5c62d69426ed5862af4d41f4d2a967b0f`, verification argv naming exactly
  the **five** gate modules and admitting no skip.
- `submission.json`: provider 3600s, verification 30s, `terminal_policy
  report-and-hold`, one implementation stage, profile
  `claude-fresh-implementation`.
- Bounds 3600/4800/60, one invocation, retry false.

**The generated enforced command agreed with `COMMANDS.md` step 4
byte-for-byte** — working directory, all three environment assignments and the
argv, with `python3` resolving to the `/usr/bin/python3` the generated document
names. I used only that document.

### The actual boundary preflight, and a defect of mine inside it

**Available, zero denials, 0.379s**, child status 0. A child spawned with the
controller's exact working directory, `PYTHONPATH` and
`BATON_V12_STAGE_EXECUTION_CONFIG` **read from the generated
`AUTHORING-COMMAND.json` rather than retyped**, calling the staged
controller's own `bounded_engine`, so the engine call is a grandchild — the
depth the real run uses. `baton_v12` and `tools` both resolved inside the
staged source. Engine version status 0 in 0.045s; image inspect status 0 in
0.005s returning `sha256:c862c055…`, equal to the pin, **at the boundary**.

And `main`'s first three statements, in `main`'s order, against this composed
packet: **`held_packet`, `verify_imported_sources` and `verify_controller` all
accept, in 0.00734s.** That is the window run348852 died in at line 554 and
run350529 died in at line 564. It stops at `main`'s next statement, the
authoring lock at `authoring_enforcement.py:566` — no lock taken, no store
opened, no image verified by the controller, no Job, no container, no provider
call, no credential value read.

**My own defect, caught by running the check rather than reading it.** The
first boundary report came back `denied` on both engine probes with
`AttributeError: 'dict' object has no attribute 'returncode'`. The denial was
false and it was mine: `single_worker._engine_run` returns a **mapping** with
`status`/`stdout`/`stderr`, and my harness assumed a `CompletedProcess`. Had I
believed it, I would have reported a capability denial for a probe that
actually succeeded and stopped the turn on my own bug. Corrected to read the
mapping, and the corrected report records the return keys it actually saw.

### The run

Launched **once**, at **2026-10-22T15:23:19Z**, pid 11500, using only
`packet/AUTHORING-COMMAND.json`'s `start` with its generated environment and
working directory. `packet/commands.json`'s `start` was not used.
`evidence/run-352156/LAUNCH.json` records the argv, environment, cwd and pid.

**It started.** Four selected packets in a row never produced a turn and three
of those died in startup; this one is past that window. Thirty seconds in,
read from the live root rather than inferred: the authoring lock exists,
`control.sqlite3`, `jobs.sqlite3` and `integration.sqlite3` are open beside
bootstrap's `authority.sqlite3`, `packet/workspaces` is created, a manager
status snapshot is publishing, and the engine reports one container up on
image config `c862c055…` — the pinned worker image.

**THE ENVELOPE PERMISSION IS LIVE, AND THIS IS THE FIRST RUN THAT PROVES IT.**
Read from the manager snapshot, not from a document: envelope `started_at`
**2026-10-22T15:23:20.487Z** and `stop_at` **2026-10-22T16:42:20.487Z** —
origin + **4740s** to the millisecond. The attempt's token was acquired at
15:23:25.388Z with `expires_at` **2026-10-22T16:43:20.487Z** — origin +
**4800s**, `expired` false, carrying the job's 3600s provider and 30s host
verification boundaries and the 60s cleanup reserve. The 900-second default
that cut off run340352 at 904.78s and run341360 at 905.18s **did not apply**:
W333485's accepted correction, consumed through W348979's corrected binding, is
doing what it was accepted to do. Attempt
`attempt-1fb667f9830837e5d30365fa94c79e8374b347c957f2fb8b86427150f234390d`,
runtime `11a76501b451966c9732ff4c2169ef2d382b1c366a132435187350c29ca148fb`,
`execution_runtime running`, assignment generation 1 to `baton.impl`,
`work_ref 33bac792-W1`, domain `workspace:66306:3314008`.

**What that is not.** A started controller and an acquired token are not a
completed turn, not an accepted candidate and not proof that R1 or R2 were
reproduced or corrected. The gate passing in run345822 is exactly why
acceptance was withheld. The run's own result, and the host-side collection
that only exists after the worker is gone, are the evidence — not this.
