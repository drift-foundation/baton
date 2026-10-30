# W341357 producer slice — FRESH IDENTITY FOR AN ACCEPTED PREPARATION

`baton.claude`, claim345039, role `impl`. **Preparation only.** No Job
submitted, no attempt, no runtime, no engine, no provider, no credential read,
no version-control mutation, no host product or test edit, **and no product
test executed.** **The start is not selected.**

| | |
| --- | --- |
| base | `bc925cf5c62d69426ed5862af4d41f4d2a967b0f` |
| proposed run | `durable-capture-w341357-345039` |
| proposed root | `/home/sl/baton-instances/durable-capture-w341357-345039` — **absent**, created by step 1 |
| rebinds | `../execution-341637` — independently accepted (manifest `1f191e7b…`), selected once by owner342358, **failed provider authentication at 10.56s**. Preserved, seal still verifying |
| start | `start_authorized: false`, `start_selected: false` |
| exact commands | `COMMANDS.md` (six, no placeholders; step 5a–5e is the operator's post-run collection) |
| continues from | `recovery-341360/` — run341360's partial producer bytes, **unverified recovery input**, byte-unchanged from the accepted packet |
| vehicle pins | **unchanged for the seventh packet running** — controller `d12769df…`, baseline `8e5987f5…`, helper `af9e5ea6…`, 114 manager files |

## What this packet is, and what it deliberately is not

It is the **fresh identity and root binding** that
`review-2026-10-20T21-46-50Z.md` and reroute345036 asked for, and nothing else.

`../execution-341637` was independently accepted. Owner342358 selected it once.
That invocation failed provider authentication in 10.56 seconds —
`provider-failed`, `authentication_failed`, *"OAuth session expired and could
not be refreshed"*, from the provider's own supported non-secret diagnostic for
that exact attempt. **No producer work was attempted and nothing was lost:** the
review line's checkout was clean, `change.patch` is 0 bytes and `changed_paths`
is empty.

But that packet **cannot be launched again as written**, and this is checked in
its code rather than taken on the handoff:

- its root now **exists** and holds a composed packet, so `COMMANDS.md`'s
  precondition that the root is absent is false;
- `prepare.py stage` calls `root.mkdir(mode=0o700)` with no `exist_ok`, so a
  reused root raises — probe `existing-root`: *"FileExistsError: [Errno 17]
  File exists"*;
- `prepare.py bind` refuses a second composition — probe
  `rebind-over-a-composed-packet`: *"this root already holds a composed packet;
  composing a second one over it would replace the documents an owner may
  already have read"*.

**Both probes already existed.** This rebinding introduces no new refusal; the
two refusals that make the old root unusable were already regressions in the
accepted packet, and they are carried unchanged.

**It is NOT a new preparation campaign and NOT a redesign.** The reviewer
refused one and none is offered. Every worker-visible byte travels verbatim —
`TASK.md` `5f01bab8…`, `COMPLETION.md` `c8c5d4dd…`, `RECOVERY.md` `3a7ec1fa…` —
and so does the recovery input, every limit, and the gate.

## The owner-reported repair, stated as what it is

The owner reports that the Claude login and `just providers-check` completed on
2026-10-21; it is recorded in the bound `FINDING.md` and in reroute345036.

**This author repeated no check, probed no provider, read no credential value
and substituted no reference.** It clears the operational prerequisite the
review named. It does **not** establish that a subsequent attempt will
authenticate, how long the session stays valid, or anything whatsoever about
producer behaviour.

And the gap in my own preflight stands **reported, not widened**: it checks that
the registry names the reference and that the backing file exists, and
deliberately reads no value, so it cannot see an expired session and did not.
`review-2026-10-20T21-46-50Z.md` is explicit that it must not be turned into a
live probe as an incidental correction, and it is unchanged here.

## What changed, exactly

| changed | why |
| --- | --- |
| `PREPARATION-PINS.json` | run id; the task-input paths that moved with the packet directory; `continues_from`; `identity_rebinding`; three new decision sources |
| `prepare.py` | `PACKET_DIR`, `RUN`, `claim` — **the gate, the bounds and every refusal are byte-identical** — plus two stale operator-facing statements corrected (see below) |
| `verify-inputs.py` | `PACKET_DIR` only |
| `PROVENANCE.json` | the failed selection, the owner-reported repair and the preflight gap as three separate facts; four runs, zero gate measurements |
| `COMMANDS.md`, `OPERATOR.md`, this document | the printed identity, and the stale prose named below |
| `GATE-CHECK.json`, `LIMITS-CHECK.json`, `PREFLIGHT.json` | re-derived from **this** claim's composed documents |
| `decisions/` | two snapshots re-taken, three added; 28 → 31 |
| `PACKET-INPUTS.json`, `SHA256SUMS` | the resultant seal |

**Carried verbatim:** `TASK.md`, `RECOVERY.md`, `COMPLETION.md`,
`ENFORCEMENT.md`, `SHUTDOWN.md`, `FAILURE.md`, `collect.py`, `probe.py`.

### Stale prose I am correcting, and where it came from

These are **my** errors in the packet an independent reviewer accepted. The seal
and the pins were right; the prose was not refreshed with them, and I did not
notice when I sealed it.

- `PACKET.md` (this document) still described **`execution-340352`** in
  `execution-341637`: a retained candidate `433692c5`, a `CONTINUATION.md` that
  packet did not carry, "24 decision snapshots", "31 task inputs", "two gate
  modules owed", "forty-one" and then "fifty-two" probe counts. Rewritten here
  from measurement.
- `OPERATOR.md` carried the same stale counts, a three-run table and a
  supersedes list that stopped at `execution-340016`.
- `prepare.py`'s unselected-start warning said *"an earlier packet WAS selected
  and died at startup in 0.506s"*. **Two** packets have now been selected and
  neither ran. Corrected, and it is the only non-identity change to that file.
- `prepare.py`'s docstring still pointed at `recovery/` when the pins name
  `recovery-341360/`, and called the vehicle "now proven" on the strength of
  two runs it described as completed. Corrected to what the runs actually did.
- `LIMITS-CHECK.json`'s `note` named a preflight root from claim339628 and its
  `final_results` paths one from claim340016. Re-derived.

The stale text stays in `../execution-341637`, which is preserved unchanged.

## Read in this order

1. **`COMMANDS.md`** — the six exact commands, including the post-run
   collection that is **yours and not the worker's**.
2. **`OPERATOR.md`** — what each step does and what to expect.
3. **`SHUTDOWN.md`** — what the vehicle publishes when it ends, who can read
   it, and the rules: a missing final report is incomplete rather than success,
   **and an unavailable report names no cause**.
4. **`ENFORCEMENT.md`** — the vehicle, the composer's wrong start command, the
   900-second lease, the two measured ceilings.
5. **`FAILURE.md`** — the first selected execution of this Work and why it
   failed at startup.
6. **`RECOVERY.md`** — what the recovery input is, where it came from, and the
   collision-as-authorization defect already found in it.
7. **`COMPLETION.md`** — the supported completion mechanism and the 600/720/180
   planning cutoffs, read from the current protocol.
8. **`TASK.md`** — what the authoring turn is asked to do, in a fixed order.

`collect.py` and `probe.py` are the two executable documents: the first is the
operator's read-only post-run collection, the second re-runs all **fifty-five**
refusal and collection cases in about 2.2 seconds — including both reviewers'
collector fixture sets.

Evidence: `PREPARATION-PINS.json`, `PROVENANCE.json`, `PREFLIGHT.json`,
`GATE-CHECK.json`, `LIMITS-CHECK.json`, `decisions/` (**31** immutable
snapshots indexed by `decisions/INDEX.json`), `SHA256SUMS` and
`PACKET-INPUTS.json`.

## The record this packet is selected against

| run | provider served | ended | result |
| --- | --- | --- | --- |
| parent run340016 | 869.45s | on its own | candidate `433692c5` retained, **`verification-failed`**, independently **rejected** |
| parent run340352 | 904.78s | lease, signal 15 | **nothing frozen** |
| run341360 | 905.18s | lease, signal 15 | **nothing frozen** |
| run341637 | 10.56s | **provider authentication failure** | **no work attempted**; the turn never began |

**One retained candidate, zero accepted. Four runs, zero measurements of this
slice's gate.** Provider served ≈2690s; controller elapsed ≈2777s — separate
figures, since controller elapsed includes the bounded shutdown, cleanup sweeps
and publication.

The turn's order is unchanged and is the point of the preparation: apply the
recovery, **run the gate before any design or test expansion**, fix only
demonstrated failures, stop optional edits at 600s, end the provider turn by
720s, preserve ≥180s of margin. `TASK.md` enforces the order and
`COMPLETION.md` carries the mechanism where the worker reads it. **Ending the
turn IS freezing** — the provider process returning is the only trigger — and
none of the post-return steps happen if the lease kills the turn first.

## Preparation evidence, measured this claim

**No product test was executed to produce any of it. No instance was touched.**

- **Input check** 0.12s, exit 0 — 114 manager files, 3 supervisor files, 2
  preparation inputs, **41** task inputs, **31** decision snapshots, 4 checkout
  documents, 1 pinned controller, 1 pinned shutdown helper, **4** pinned
  recovery inputs, **1** gate module still owed, and **no decision-source
  drift** after re-taking `FINDING.md` and `PLAN.md`.
- **Preparation exercised once** into `/tmp/w341357-preflight3`: stage 0.12s,
  bootstrap `--no-repositories` 0.63s, bind 0.37s — **≈1.12s, all status 0**,
  ending `prepared-not-executed` / `start_selected false`, after `held_packet`
  re-pinned all **41** `fixture.files`.
- **The identity is correct in the bound document, read back rather than
  asserted**: the composed `PACKET.json` carries `run_id`
  `durable-capture-w341357-345039`, `work` `W341357`, `claim` `345039`.
- **The gate provably did not move.** The verification member digest
  re-derived from this claim's composed `task.json` is
  `2f7ed3dca95da498657a0e549e53107679fd7e8cf4503d5022555ba9e642176c` —
  **identical** to the digest `execution-341637` was accepted with. The run id
  and root travel in the submission and the packet, not in the verification
  argv.
- **The worker-visible bytes provably did not move**: `fixture.files` carries
  `TASK.md` `5f01bab8…`, `COMPLETION.md` `c8c5d4dd…`, `RECOVERY.md`
  `3a7ec1fa…` and all four recovery inputs at their accepted digests, including
  the two the reviewer published independently (`86be4114…`, `fb9f8e77…`).
- **Fifty-five probes, all behaving as intended, 2.236s** — carried unchanged.
  `probe.py` derives the run id from `prepare.py` by regex, so it followed the
  rebinding **without being edited**, which is itself a consistency check.
- **Generated limits agree**, re-read from this claim's composed documents:
  provider 3600, verification 30, one invocation, no retry, `report-and-hold`,
  4800 total, 60 cleanup, 1110 residual.
- **The composer is unchanged** at `09fbf3c5…` and line 721 still composes the
  unenforced `baseline.py` start. **The lease is unchanged**:
  `worker_manager/tokens.py:37` still reads `LIFETIME_SECONDS = 900`.
- **The sealed gate was NOT run here.** There is no product-test authority for
  this author and the classification belongs inside the isolated run.

Author evidence, **not** independent product acceptance.

## Disclosures, all retained

- **No authoring invocation has ever completed for this Work.** Two selected
  packets never ran — a startup failure at 0.506s and an authentication failure
  at 10.56s — and two cut-off runs froze nothing. A working session and one
  invocation are what is needed, not a new design.
- **The focused five-module gate has never been measured in any run.** Whether
  it fits the 30-second ceiling is **unproved**; the 13.642s / 1124-test
  baseline is the parent's twelve-module figure, measured out of boundary at
  claim339421, and is carried as context only. No coverage may be removed to
  force a pass, and review will check for it.
- **The recovery input has never been executed.** `_authorizes`, the versioned
  read API and all 62 named cases are **unverified**. Line counts and case
  names are not evidence that code works — I claimed otherwise once and the
  review rejected the claim.
- **The composer still emits the unenforced start.** Reported for
  classification, **not patched**; mitigated by `AUTHORING-COMMAND.json`,
  `PREPARED.json`'s `composer_start_is_unenforced` flag and both operator
  documents. Every later authoring packet inherits it.
- **The 900-second lease is enforced and unextended.** The 3600/4800 ceilings
  are requested bounds, not a promised run length; renewal remains W333485's
  unfinished work.
- **The structural credential preflight cannot detect an expired session.**
  Reported, not widened.
- **Two gate exclusions rest on out-of-boundary measurements** — the 51.333s
  and 19.888s figures for `test_authoring_shutdown_deadline` and
  `test_authoring_manager_guard`, measured by direct host execution at
  claim339421 outside that claim's preparation boundary. Stated rather than
  laundered, and not re-measured.
- **Two excluded modules already fail at base**, both explicitly unverified
  baseline reports with no cleanup selected: `tests.manager.test_boundary_inventory`
  and `tests.tools.test_packaging`'s subcommand case.
- **`AGENTS.md` at this base carries the older W321689 exception section**,
  because the host's replacement is an uncommitted working-tree edit. The
  exception is expired either way; this packet's documents are the authority on
  what is permitted here.
- **This packet's collector has been found wrong twice: seven defects across
  two reviews**, every one a claim stronger than its evidence. All seven are
  regression probes and both reviewers' fixture sets are pinned.
- **One probe is honest about its method.**
  `owed-gate-module-already-on-the-host` substitutes an existing module path
  for the owed name in the copy's `prepare.py`, because probing it literally
  would mean creating a product test file in the host working tree. Labelled
  `substituted: true`.

## Ownership and what is still owed

`baton.impl` owns this packet, `PROGRESS.md` and the isolated candidate; the
reviewer owns `FINDING.md`, `PLAN.md` and the reviews. W333485 owns the
separate serving-renewal preparation at `baton.codx`, with no dependency either
way. The declared candidate intersection remains `worker_manager/intake.py` and
`worker_manager/attempts.py` at the accepted bytes, for serial integration;
`tools/job_manager.py` and `job_manager/manager.py` are the sibling's declared
surfaces and any edit there requires an explicit overlap declaration first.

Still owed: independent review of **this** preparation; an exact separate
execution selection; a run that actually completes, which has never happened
for this Work; the five `TASK.md` steps; independent review of whatever
candidate a run returns; parent W333486's ordinary status/report integration,
full joined twelve-module gate, installed-bundle proof and joined acceptance;
and the parent's pending human checkpoint.

**Nothing in this packet selects or authorizes a start.**
