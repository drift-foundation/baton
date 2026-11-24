# W385830 — addendum to the approved contract: the two review qualifications of M385887

Author: baton.prompt (K, model Fable 5.2), interactive copilot, no claim.
2026-11-23. Authority: M385887 and the FINDING entry "N1/N2 deterministic
implementation approved — owner 2026-11-23".

The approved text is `IMPLEMENTATION-CONTRACT-CONSOLIDATED-REV2-2026-11-23.md`
(sha256 dc3245c0c5594f15d22c87cd9b9a19352c633c3e4ef9a52f070f24d87960bd87).
That file is not edited: the approval names its hash. This addendum records
the two technical qualifications the approval carried, as corrected
contract and verification wording. It is read together with that file and
changes nothing else in it.

Nothing was executed. No coding, build, engine operation, credential or
registry read, or provider call.

## 1. What is approved, and what is not

| Approved (M385887) | Not approved |
| --- | --- |
| Slice N1: explicit model request, contributor attribution, evidence binding and enforcement, diagnostics, separation classification | N3, the engine inventory |
| Slice N2: provider hooks, shared policy and per-worker adapter identity, Job-and-worker-bound retained disk homes, single-writer protection, the selected credential and managed-entry behaviour | N4 beyond its prerequisites |
| Ordinary private compilation and focused deterministic tests within N1 and N2 | N5: image and real-provider qualification; native use |
| Routine in-scope deterministic corrections, with no further owner approval round | Any credential or registry read, image build, install, engine operation or live call |

Unchanged requirements: old admissions are preserved; an exact reviewed
candidate and independent review are still required.

## 2. Qualification 1 — what an inventory can and cannot source (applies to N3 and N4; does not block N1 or N2)

The approved contract let the N4 adapter's fixtures be "taken from" the N3
inventory, and proof 50a required every event shape to trace to it. A
no-provider inventory never sees a real turn, so it cannot supply turn
events. The corrected wording:

### 2.1 Two kinds of evidence, two sources

| What the adapter needs | Its only acceptable source |
| --- | --- |
| Program version; commands and options; how a model is named on the command line; required home location; files created or read on start | The N3 pinned-image inventory for that exact build |
| Anything a real turn produces: terminal events, exit behaviour on success and on each failure, participation sources, session files written during a turn | **Retained exact-build evidence** — output already retained in a dossier from a real run of that exact build — **or** a separately selected provider qualification (Q1, Q2) |

Never a source for either: another build's output, the host installation's
captures, vendor documentation by itself, or a shape written from
expectation.

### 2.2 Consequences

- **Replaces §11.2's opening sentence.** The Codex adapter's arguments and
  home handling are taken from the N3 inventory. Its turn-event parsing is
  taken from retained exact-build evidence or from Q1. Until one of those
  exists for 0.169.0, the adapter's turn-event fixtures do not exist, its
  participation-source list is empty, and every Codex result is `missing`
  (the fail-closed state the contract already defines).
- **For Claude 2.1.247** retained exact-build evidence does exist: the
  September qualification dossier's real output of that build. Its
  fixtures may be traced to those retained bytes. That covers what was
  recorded there and nothing beyond it.
- **For Codex 0.169.0** no retained exact-build turn output exists. The
  August spike ran 0.150.1 and is not a source.
- **Slice N4 is therefore two parts.** N4a — arguments, entry, recipe,
  home handling — depends on N3. N4b — turn-event parsing and
  participation sources — depends on retained exact-build evidence or on
  the selected Q1. N4b may follow N5's provider question rather than
  precede it; the joined proof (N6) needs both.
- **Replaces "Its output is an input document for the adapter slice"** in
  §12.1 with: its output is the input for the adapter's arguments and home
  handling only.

### 2.3 Corrected proof

**50a (replaces the approved 50a).** Every fixture the adapter's tests use
carries a recorded source, and the check fails for any fixture without one:

- an option or start-time fact names the retained N3 inventory entry for
  that exact build;
- a turn-event shape, exit behaviour or participation source names the
  retained real output of that exact build — by dossier path and digest —
  or the retained evidence of a selected provider qualification;
- a fixture built only to exercise a refusal (malformed, truncated,
  oversized, unknown shape) is marked synthetic and may be used only to
  prove refusal or `missing` / `unclassified`, never to prove a successful
  reading.

Proofs 48 and 49 are read with this: "each terminal outcome in the pinned
build's inventory" becomes "each terminal outcome evidenced for the pinned
build under 50a".

N1's and N2's own tests use fixture identifiers and fake providers to
prove Baton's behaviour, not a provider's shape; they are unaffected. The
same marking applies to them: a fake provider's output is labelled
simulated and proves nothing about what a real build emits.

## 3. Qualification 2 — deriving the home path (applies to N2 now)

The approved §8.1 wrote the place as
`<instance>/state/job-work/<job_id>/provider-homes/<worker_id>/`. Read
literally, that puts Job and worker text into path components. The
corrected rule:

### 3.1 Rule

1. **Canonical identity first.** The home's identity is one canonical
   structured value naming the instance's authority, the Job id and the
   worker id, each as the exact value the Job store and the worker
   document hold — not a display name, title or any free text.
2. **Path components are derived, never copied.** Each path component
   that distinguishes one home from another is a fixed-length digest of
   that canonical value, in a fixed safe alphabet. No Job or worker text
   appears in the path. The existing context store already derives its
   directory this way from a canonical member set
   (`wm/provider_context.py:762-837`); the same construction is used.
3. **Unambiguous encoding.** The canonical value is encoded so that member
   boundaries cannot be confused: two different (Job, worker) pairs can
   never produce the same encoded bytes, whatever characters the ids
   contain.
4. **Bound, not only named.** The manager-owned record beside the home
   stores the plain canonical identity. At every start the manager
   re-derives the path from the attempt's Job and worker, and requires the
   record found there to state exactly that identity. A mismatch, a
   missing record beside an existing home, or a path that is not an
   ordinary owned directory is refused.
5. **Layout is the implementer's choice within these rules.** The
   `job-work/<job_id>/provider-homes/<worker_id>/` spelling in §8.1 is
   illustrative of the nesting only. Whether one digest covers the pair or
   one covers the Job and another the pair is free, provided homes of one
   Job can be found together from the records.

Nothing about what the home is changes: Job-bound persistence and
separate homes per worker remain as selected.

### 3.2 Corrected and added proofs (N2)

**31 (replaces the approved 31).** Within one Job, two workers — same
provider, different roles — resolve to different homes. The same Job and
worker resolve to the same home on every derivation and after a manager
restart. A deployment naming another location, or a start with no Job id,
is refused.

**31a.** Job and worker ids containing path separators, `.` and `..`,
leading dashes, whitespace, control characters, non-ASCII text, or of
great length, each resolve to a home whose path lies under the homes root,
has only fixed-length safe components, and contains none of the id's text.

**31b.** Pairs chosen to collide under naive joining — ids that differ
only by case; (`a`, `bc`) and (`ab`, `c`); an id equal to another id plus
a separator and suffix — resolve to different homes.

**31c.** A home whose record names a different Job or worker than the
attempt being started, or which has no record, is refused at start and is
not mounted, modified or removed.

**31d.** The record's plain identity lets diagnostics name the Job and
worker of a home; the path alone is not parsed for it.

## 4. Order of execution, as recorded — not as installed

| Item | State |
| --- | --- |
| W385695 checkpoint-2 recovery (codexpc) | In progress under its own claim. Not interrupted, not reallocated |
| N1 and N2 | Approved. Shared-file implementation is serial **behind** that recovery. Not yet assigned or released |
| Assignment and gates | The coordinator establishes the bounded assignment and the actual graph gates before dependent execution is released. This document installs no dependency |
| W385853 runtime instruction delivery | Follows the accepted N2 interface. No runtime edit ownership is assigned |
| N3 inventory; N5 gate; Q1, Q2 | Not selected; raised at their boundaries |

Shared files, for whoever takes the assignment (evidence of overlap, not
an edit list): `tools/pool.py`, `tools/stage_execution.py`,
`tools/parallel_test.py` and `DEPLOYMENT.md` with W385695;
`worker/claude_agent.py`, `worker/Dockerfile.claude` and the context
prompt and argv builders with W385853's later delivery.

## 5. Still pending at their boundaries

Unchanged from §17 of the approved contract, with one addition from §2:

| Boundary | Decision |
| --- | --- |
| Independent of N1 and N2 | Selection of the N3 inventory |
| Before N4b | Whether Codex turn-event evidence comes from Q1 or from another selected exact-build source |
| When finished images can be built | Selection of the N5 gate |
| Before Q1 and Q2 | Requested selectors; the seed login reference; each call |
| After Q1 and Q2 | Mapped identities; whether 2.1.247 met C1–C5 |
| Before a login is used from more than one home | How refresh invalidation is qualified |
| When a recovery requirement is established | The mechanism for a lapsed retained login |

## 6. Limits

- Nothing executed.
- That the September dossier's retained bytes are complete enough to
  source every Claude fixture N1 needs is not checked here; the
  implementer cites what is actually retained and marks the rest
  synthetic.
- §3.1 item 4's start-time record check is the mechanism I propose for
  "binding"; it adds a refusal for a home with a wrong or missing record
  and no other behaviour.
