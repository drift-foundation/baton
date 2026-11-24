# W385830 — N1/N2 implementation assignment against checkpoint 9f979022

Author: baton.prompt (K, model Fable 5.2), interactive copilot, no claim.
2026-11-24. Authority: M385887 (owner approval of N1 and N2) and the owner
instruction of 2026-11-24 to resume preparation after W385695 closed.

Preparation only. Nothing was built, run or tested. No product file, Git
state, engine, credential, registry or provider was touched. The approved
contract and its addendum are not edited.

## 1. Handoff

- **Outcome.** Deterministic slices N1 (explicit model request and
  attribution) and N2 (provider hooks, shared policy and adapter identity,
  Job-and-worker-bound retained home, one writer, credential modes, managed
  entries) as one exact candidate with focused deterministic evidence,
  passed to independent exact-byte review.
- **Contract.** `IMPLEMENTATION-CONTRACT-CONSOLIDATED-REV2-2026-11-23.md`
  (sha256 `dc3245c0c5594f15d22c87cd9b9a19352c633c3e4ef9a52f070f24d87960bd87`),
  §4–§10 and §13 proofs 1–47, read with
  `IMPLEMENTATION-CONTRACT-N1N2-ADDENDUM-2026-11-23.md`
  (sha256 `c4d2c4b7ebe4c60b6e5eb9543ff4664d2fd86511c6b8a4f538c2b58e27d07117`):
  proof 31 replaced, 31a–31d added. Both hashes re-measured today.
- **Base.** Commit `9f9790222dfd004bc8f19d5c378c3acdb00fd4ca`. `v12/` is
  clean against it except `v12/DESIGN.md` (see §3, item 1).
- **Implementer.** codexpc through `baton.codx` (route `implpc`), per S1.
  Reviewer: independent exact-byte review; K/Fable unless the owner names
  another.
- **Where the work is done.** A disposable copy at the base, under
  `work/scratch/`. The protected checkout is not edited; import of accepted
  bytes is a separate owner-selected step.
- **Order inside the slice.** N2 first (hooks, policy and adapter identity,
  home), then N1 on top (the model selector and the participation-source
  list are members of the adapter identity N2 creates). One candidate, one
  review. Returning N2 alone for review first is allowed if it is complete
  with its proofs.
- **Verification required.** Each of proofs 1–47, 31a–31d shown by a named
  deterministic test, with a table from proof number to test id. Fake
  providers at the normal provider boundary, labelled simulated. Existing
  tests of the touched modules pass with no expectation weakened; any
  changed expectation is listed with its reason. Recipes and interpreter
  per `v12/python/TESTING.md` (`just test-one`, `just test-group`); log,
  ledger and source identity retained together.
- **Not selected.** Full suite; `tests.manager.test_checkpoint_profiles`;
  the `_engine` and `_integration` engine modules; any image build,
  container, install, credential or registry read, provider call or native
  launch; the Codex image inventory (N3); N4, N5, N6.
- **Handoff condition.** Candidate manifest (base, path set, sha256 and
  mode per path), the proof table, retained logs, PROGRESS entry by the
  implementer, then `pass` to review. A partial result is returned with an
  exact checkpoint, not held.
- **Next milestone after acceptance.** Owner import and Git checkpoint;
  then W385853's delivery delta against the accepted N2 interface. N3 is
  selected separately and does not wait for this.

## 2. Limits of the assignment

- **In scope:** what proofs 1–47 and 31a–31d require, and routine
  deterministic corrections within them (no further owner round, M385887).
- **Old admissions are preserved.** Under the earlier selection every
  composed document, digest, run vector and argv is byte-identical to
  today (proofs 19, 30, 33). New behaviour appears only under the explicit
  new composition selection.
- **Out of scope, not to be touched for this slice:** scheduling, custody,
  recovery and publication behaviour; the context-reuse path; the Plan and
  History view; the six-hour ceiling and descendant containment (W385263);
  any Codex adapter, entry or image recipe; `v12/DESIGN.md`.
- **Starting states that are correct, not gaps:** the managed-entry list is
  empty (§10); the Codex participation-source list is empty, so every Codex
  result is `missing` (addendum §2.2); the selector-to-identity mapping
  holds only fixture values in tests — no real model identifier is written
  into product source (requested selectors and mapped identities are owner
  selections at the Q1/Q2 boundary).
- **Fixture provenance.** A Claude fixture that claims a real 2.1.247
  shape cites the retained September bytes by dossier path and digest;
  everything else is marked synthetic or simulated (addendum §2.3, §6).

## 3. What changed under the contract since it was written

The contract was read against `6079ad78`. W385695 then changed 56 paths
under `v12/` (18,800 lines added), including most of the files the
contract cites. I re-read each cited place at `9f979022`. The findings F2,
F3, F5, F6, F7, F8, F10, F11, F14 still hold; their locations moved. Four
things are new and bear on the work.

1. **The approved ID-4 sentence is not in the checkpoint.** It is in the
   working tree of `v12/DESIGN.md` only (uncommitted, with the W385263
   clarification beside it). `9f979022` does not contain it. The
   implementer builds from the commit and does not edit DESIGN; the owner's
   next checkpoint should carry that text before or with the N1/N2 import.
   This dossier is also untracked; the two hashes above are what pin the
   approved bytes.

2. **A supervisor for the provider now exists.** `worker/bounded_command.py`
   (new) runs a required review's provider under `--exec`, becomes the
   subreaper and ends every descendant
   (`worker/claude_agent.py:4500-4537`). Every other turn still goes
   through `_run_provider` (`:1999-2030`), which ends the direct child only
   and passes no stdin setting. Proofs 23 and 24 are therefore still owed
   for the unsupervised turn. The mechanism is the implementer's choice;
   the supervised review path must behave exactly as accepted in W385695,
   and a second, competing containment mechanism is to be avoided where the
   existing one can be reused.

3. **A publication worker and lane now exist, and invoke no provider.**
   `bootstrap.WORKER_ROLES` adds `publication` (`tools/bootstrap.py:48-57`);
   `pool compose-worker` composes it with `provider: None`, its own
   `baton.worker-tool-policy/1` digest and no credential
   (`tools/pool.py:865-1075`); the scheduler has a publication lane
   (`jm/scheduler.py:43-44`). S4 and proof 1 say "every worker … every
   role". My reading, inside the approved scope ("no change to recovery"):
   the model, adapter-identity, home and attribution rules apply to workers
   that invoke a provider; the publication worker is composed exactly as
   today under either selection and gets no model, no home and no `/2`
   adapter. The implementer first establishes how the existing lane
   equality treats the publication lane and keeps that treatment unchanged.
   Open to correction.

4. **A second path now accepts a candidate.** Proof 14 requires that a
   `missing` or `conflicting` attribution accepts no candidate. At the
   checkpoint an implementation candidate can also be accepted through an
   approved publication recovery (`jm/publication_execution.py`:
   `take_custody` `:1955`, `hand_off` `:2154`, `deliver_review_item`
   `:2650`), which does not pass through `end_implementation`
   (`jm/review_driver.py:653`) and carries no attribution. For a Job under
   the new composition that path would hand a candidate to review with no
   evidence of the requested model, against S2. This is the one concrete
   conflict; it needs an owner decision (§5). It does not delay the start.

Current locations of the cited places (evidence, not an edit list):

| Finding | At 9f979022 |
| --- | --- |
| F2 fresh argv carries no model | `worker/claude_agent.py:4476`; context path `:4480` |
| F3 hard-coded model label | `tools/next_run_bindings.py:360`, `:609` |
| F5 only a direct `model` field is read | `worker/claude_agent.py:4743-4744` |
| F6 tool policy digest is the Claude command | `tools/next_run_bindings.py:303`; adapter digest `:382` |
| F7 no provider or model operand | `tools/pool.py:1182-1213`; role check `:718` |
| F8 separation class is a constant | `tools/stage_execution.py:459`, `:7335`; closed set `jm/scheduler.py:56` |
| F10, F11 direct child only; stdin inherited | `worker/claude_agent.py:1999-2030`, `:5092` |
| F14 home in per-child scratch | `worker/claude_agent.py:3721`, `:3733` |
| F16 slot release without runtime state | `jm/scheduler.py:677-698` |
| One live allocation per worker | `jm/schema.py:324`, `:941` |
| Per-worker source nomination | `tools/pool.py:830` |
| Job id on stage and launch | `tools/single_worker.py:3579`; `wm/launch.py:170`, `:375` |
| Mount families | `wm/oci.py:739-1335`, context `:4447` |
| Deployment schema versions | `tools/single_worker.py:116-123` (`/4`, `/5`, `/6`) |

Not re-read today: `contracts/manifest.py`, `wm/launch.py`, `wm/oci.py`,
`wm/credentials.py` and `tools/next_run_bindings.py` are unchanged since
the contract's base, so its citations there stand. The digest-derived
directory construction the addendum points to
(`wm/provider_context.py:762-837`) is in a file W385695 changed by seven
lines; the implementer confirms the construction where it now sits.

## 4. Graph gates

State read today (snapshot 385963): W385830 open, queued, no handler, on
`baton.decide`, no edges. W385695 closed `satisfying` with the owner's
closure naming `9f979022`. W385853 and W385263 open, queued, no handler,
no edges.

**No gate is installed.** I attempted two of the operations below as
`baton.prompt`; both were refused, correctly: "baton.prompt is not a
resolved handler of baton.decide (route 'approv', handlers ['slaw'])".
Nothing was changed and I did not retry another way. The gates are the
owner's to install; the commands are in §4.1.

| Gate | State |
| --- | --- |
| N1/N2 serial behind W385695's recovery | Satisfied by closure. No edge is needed; an edge to closed Work would gate nothing |
| N1/N2 as its own Work under W385830 | Prepared (command 1). The umbrella stays open through N3–N6 and joined acceptance |
| W385853 delivery follows the accepted N2 interface | Prepared (command 2): an edge on the N1/N2 Work, not on the umbrella, so it clears at N1/N2 acceptance |
| W385263 A1 held behind this Work (M385843; its PLAN "A1 held for native provider preparation") | Prepared (command 3): an edge on W385830. That holds A1 until the whole of W385830 closes, which is how the hold is recorded; if it was meant to clear at N1/N2, name the N1/N2 Work in `on=` instead |
| N3, N4, N5, N6 | No Work. Each is raised at its boundary; nothing depends on guessing them |
| File ownership | While the N1/N2 Work is claimed, its claimant alone edits the §13 main-area files. W385853 and W385263 edit none of them until their edges clear |

### 4.1 Owner commands

Each is one standalone command. `B` stands for
`/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw`,
run from the repository root. Command 1 creates the Work on
`baton.decide`, so it releases nothing; command 5 is the release.

1. Create the N1/N2 Work; its answer names the new id, written `<N>` below.

   `B create team=baton kind=decide origin=decomposition classification=limitation parent=2b077949-W385830 title="W385830 N1/N2: model attribution, provider hooks, policy, retained home" "body=$(cat work/records/2026/11/finding-v12-native-provider-selection/ASSIGNMENT-N1N2-WORK-BODY.txt)"`

2. `B block work=2b077949-W385853 on=<N> rationale="Native instruction delivery follows the accepted N2 interface (M385887); both edit worker/claude_agent.py, worker/Dockerfile.claude and the prompt and argv builders."`

3. `B block work=2b077949-W385263 on=2b077949-W385830 rationale="A1 implementation is held behind native provider preparation by owner direction (M385843)."`

4. Read back: `B links work=<N>` and `B links work=2b077949-W385830`.
   Expected: `<N>` has parent W385830 and blocks W385853; W385830 contains
   `<N>` and blocks W385263.

5. Release: `B reroute work=<N> to=baton.codx reason="N1/N2 approved in M385887; W385695 closed at 9f979022; assignment ASSIGNMENT-N1N2-2026-11-24.md"`.
   Expected: `<N>` queued on `baton.codx`, route `implpc`, ready, no
   handler. codexpc then claims it and begins from §1.

## 5. The one decision raised

**When a Job composed under the new selection has its implementation
candidate published by an approved publication recovery, what happens to
the attribution requirement?**

| Option | Effect |
| --- | --- |
| A — refuse | Publication recovery is not admitted for a Job whose producing worker is under the new composition; the typed refusal says attribution is not carried by recovery. S2 holds. Smallest change; such Jobs have no publication recovery until a later slice adds it |
| B — carry and enforce | The recovery binds the producing attempt's attribution record and enforces it at custody. S2 holds and recovery stays available, but it changes recovery (outside the approved scope) and depends on the failed attempt having retained a readable record |
| C — accept unattributed | The recovered candidate goes to review marked "no evidence". Contradicts S2 as written |

I recommend A. Until it is answered the implementer leaves the publication
files unchanged and N1 is not accepted; everything else proceeds.

## 6. Limits

- I read code and records; I ran nothing. Line numbers are from the
  working tree, whose `v12/` product files equal the commit.
- How the existing lane-equality check treats the publication lane (§3,
  item 3) is not established by me.
- The size of the change is not estimated.
