# Focused verification the packet must satisfy — W321780

Outcome-based, deterministic by default, and bounded to the affected boundaries.
No whole-suite expansion: VER-5 names the obligations and these are them, one
row per obligation with the shape of the check rather than a command, because
the implementer chooses commands.

## The named acceptance obligation

**The 102-test credential gate, in BOTH independently materialized views, with
zero skips, import errors and fixture errors.** A different passing subset does
not substitute for it — VER-5 says so and the reassessment says the September
102 was hand-assembled and therefore proves no paired holder behaviour.

Measured in this claim on the current tree, for provenance rather than as
acceptance: **102 tests, OK, 0.222s**, with the one immutable input pinned in
`PACKET.md`. That establishes the vector and its fixture are intact today; it
does **not** establish worker or operator materialization, which is precisely
what the delivery must prove.

## Paired construction and version agreement

| obligation | the check |
| --- | --- |
| both holders build a FRESH PRIVATE view | **neither view is the edited candidate.** The worker materializes a disposable view it owns from the measured candidate bytes and the sealed inputs; the operator materializes its own from the retained output -- the accepted-base object source, the transport resolving the published `head`, and the same sealed inputs from the same seal. Each refuses unless it holds every path the retained result reported changed, at those bytes. The gate then passes in each independently |
| version agreement | the same `/3` task is accepted by both holders with identical closed members |
| legacy refusal | a `/3` `verification_context` offered under `/2` **refuses**, and a `/3` task with the member absent refuses; neither silently ignores it |
| closed PYTHONPATH | the derived import path equals `import_roots` joined to `working_directory` and nothing else |
| ambient independence | with a hostile `PYTHONPATH` exported in the environment, the gate still passes and the hostile entry is absent from the child's path |

## Refusal, in its two stages

Review 2026-10-18T09-07-00Z finding 1: a required path inside a view that does
not exist yet cannot be checked before materialization, nor before the
implementation has created or deleted it. So the obligations split by what each
stage can actually see. `CONTEXT-CONTRACTS.md` carries the full tables.

**STAGE A, static — refuses before materialization AND before provider work, and
each case asserts that NOTHING was materialized:** absolute path; `~` path; `..`
segment; empty segment; duplicate input destination; input destination inside
the candidate; candidate inside an input destination; malformed digest; a
declared input absent from the sealed set; a declared input digest-mismatched in
the seal; empty or non-list `verification`; a `/3` context offered under `/2`; a
`/3` task with the context absent.

**STAGE B, view preflight — refuses after materialization and immediately
before the command starts, in BOTH holders' fresh private views, with
`command: not-run`, that holder's OWN view cleaned up and nothing else, and the
retained candidate and sealed inputs byte-unchanged:** absent `working_directory`; absent
`import_root`; absent `required_path` (→ `missing-input`); a materialized input
whose bytes do not match its declared digest (→ `materialization`); a candidate
whose `candidate.pins` do not hold, or which does not hold what the
RETAINED RESULT reported changed or removed (→ `materialization`); a `git-line` whose `declared_base` is not an ancestor of
`entry_head` (→ `invalid-layout`); an accepted-base object source that does not
hold `base` (→ `missing-input`); an unsatisfied object-transport prerequisite,
or a transport resolving some other head (→ `materialization`).

**The old row demanding a readback at `declared_base` is gone**, and its removal
is review finding 1's correction: a view built at the base would discard the
changes the verification exists to measure.

**AND A CANDIDATE DELETION IS A STAGE-B REFUSAL, NOT A TEST FAILURE.** If the
implementation deleted a path the task requires, Stage B answers
`missing-input`, the command does not run, and **no verdict about the candidate
is supplied**. A check that let that arrive as `failed` would be reporting a
context fault as evidence about the code.

## Candidate exactness, preservation and cleanup

Review 2026-10-18T09-16-00Z finding 1 names four behaviours explicitly. They are
the first four rows, and each one is a thing the *first* draft of this packet
would have got wrong by checking the base out into the view:

| obligation | the check |
| --- | --- |
| **the CHANGED candidate is what runs** | an edit made at stage 4 -- unknown when the task was sealed -- is read at its edited bytes by the command in BOTH views, proved by a case whose edit changes the gate's outcome; the sealed input digest is unchanged across the whole trace |
| **a deletion stays absent** | a path the retained result reports removed is absent in EACH view; present → Stage-B `materialization`, and the command does not start |
| **a substituted base refuses** | the base tree offered in place of the changed candidate does not hold the paths the retained result reported changed; `refused`/`materialization`, `command: not-run`, no verdict |
| **existing profile/base pairings still hold** | `generic` with a base, and `git`/`git-line` without one, are refused by `checkout_plan` at **both** holders; the three profiles and their `source_root`s are unchanged |
| the pinned fixture is unchanged | the `candidate.pins` entry matches, and matches the sealed input's digest, at Stage A against the seal and at Stage B in the view; a drifted in-candidate fixture refuses rather than passing the gate |
| the base's role is ancestry only | `declared_base` is never checked out into the verification view; for `git-line`, it must be an ancestor of `entry_head`, and a line on another history refuses |
| retained candidate unmodified | after verification, the candidate's digests are unchanged |
| sealed inputs unmodified | after verification, each input's digest equals its declared `content_digest` |
| no fixtures in the proposal | the proposal output contains no path that the verification created |
| **a command that WRITES a source path cannot reach the candidate** | in EACH view, a command deliberately writes a path that exists in the candidate; afterwards the retained candidate's and every sealed input's bytes are unchanged |
| **a command that DELETES a source path cannot reach the candidate** | likewise for a deliberate deletion, in each view |
| **cleanup removes the view and nothing else** | after cleanup the view is gone and the retained candidate and sealed inputs are byte-for-byte intact |
| cleanup on timeout | a timed-out command leaves no derived view, and leaves the candidate and the sealed inputs unchanged |
| cleanup on start failure | likewise, and the outcome is `start-failure` rather than a command verdict |
| cleanup on partial materialization | a failure part-way leaves no half-built view, and nothing retained is altered |
| **the transport's prerequisites are required, not assumed** | an operator view whose accepted-base object source lacks `base` refuses `missing-input`; an unsatisfied bundle prerequisite, or a transport resolving some other head, refuses `materialization`. No fallback to an ambient host checkout |

## Safe durable outcomes

| obligation | the check |
| --- | --- |
| distinct outcomes | `ready`/`refused` and `not-run`/`passed`/`failed`/`timed-out` are each reachable and each distinct in the durable record |
| ONLY the five legal combinations | each row of `CONTEXT-CONTRACTS.md`'s table is produced, and each illegal combination is refused as malformed: `passed` with a null or nonzero status, `failed` with `0` or null, `refused` carrying a command verdict, `not-run` or `timed-out` carrying a status |
| the paired operator evidence | `baton.dogfood-operator-evidence/1` is produced by the independent operator and bound to the RETAINED OUTPUT it verified — `result_digest`, `result_head` and `transport` — plus what it measured in its own view and the exact `task_id`, task digest and sealed input digests it observed |
| the evidence identifies a GENERIC candidate too | a generic-profile candidate has no commit and no transport: its retained output IS the candidate tree, so `result_head` and `transport` are null, `candidate_base` is null, and the evidence binds `result_digest` and the measured paths. Nothing asks for a head it cannot have |
| legacy results are not reinterpreted | a `/2` result's absent `context`/`command` reads as "this version could not say", never as `not-run` and never as `passed` |
| one closed cause | a refusal carries exactly one of the four causes |
| verdict discipline | only `passed`/`failed` from a command started in a `ready` context supplies a candidate verdict; the other combinations preserve the candidate and assert nothing |
| exit status honesty | `exit_status` is present only when the child supplied one, and `null` is never read as a pass |
| nothing unsafe durable | the record carries no child output, no credential, no absolute host path and no exception prose — asserted by driving a failing command whose output contains a marker string and a fake credential, and checking neither reaches the record |

## What this claim measured, and what it did not

**Measured:** the 102 vector and its one immutable input, on the current tree,
read-only — 102 PASS 0.222s, `vectors.json` digest and size pinned.

**Not measured, and not claimable until delivery:** every row above. They are
the contract the packet binds, not results. No paired holder exists yet, which
is the finding this Work descends from.
