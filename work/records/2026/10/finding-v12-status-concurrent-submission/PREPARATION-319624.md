# Preparation record — baton.claude, claim 319624

NOT `PROGRESS.md`. Review 2026-10-18T02-54-37Z reserves that file for the actual
change author, and this claim authored no product change: its milestone was to
prepare the fresh correction packet. The future isolated worker's account belongs
in `PROGRESS.md` when it exists.

Read first: canonical `detail` at snapshot319622 (queued, unclaimed, routed
baton.impl, no next, no obligations, no open blockers, binding revision 1 at this
dossier), then the standalone claim; `work-events` complete, events 319114
through 319624 with `next_after` null; `thread` T319114, both messages, no
pagination. Then this dossier: FINDING, PLAN, TASK, OPERATOR, the three reviews,
`PREPARATION-PINS.json`, `prepare.py`, `reproduce.py`, and the evidence under
`evidence/diagnosis-319578` and `evidence/review-319604`.

## The milestone, as the handoff states it

Prepare the smallest fresh v12 correction packet from the retained checkpoint and
review R1, and return it for owner live selection. Explicitly NOT direct
host/v11 implementation, not spent-run reuse, not a live retry, not integration.
The single live grant was consumed.

So no product or test file is touched by this claim. `git status` shows no
product modification, and the host repository is at `9055843b` with a clean
product tree.

## What the packet is, and the one decision in it

`OPERATOR-319624.md` is the executable proposal; `TASK-319624.md` is what the
worker receives; `prepare_r1.py` prepares it; `PINS-319624.json` binds every
input; `evidence/preparation-319624/PREFLIGHT.json` is the measured preflight.

THE ONE REAL DESIGN DECISION: the worker's declared base is the REVIEWED
CANDIDATE `aa637298b`, not the repository baseline `9055843b`. The review
accepted the candidate's coherence work and asked for one correction, so basing a
fresh run on the baseline would spend a provider grant re-deriving accepted work
and would hand the next reviewer a delta it has already judged. Basing on the
candidate makes the worker's delta exactly R1.

That required solving how the candidate reaches a fresh run. The host repository
does not contain `aa637298b` — it lived in the consumed run's private workspace —
and fetching it into the host repository would be a host Git mutation. So
`prepare_r1.py` reconstructs it inside the fresh external root from the host
repository plus this dossier's digest-bound `objects.bundle`, and refuses unless
the reconstruction's HEAD, tree, parent, worktree cleanliness and four pinned
file digests equal the sealed pins.

## WHAT I DID NOT RUN, AND WHY IT MATTERS

`--source reconstruct` performs `git clone`, `git fetch` and `git checkout`. Those
write only into a brand-new disposable clone and never touch the host repository's
index or history — but they are still Git operations that write, and AGENTS names
`checkout` and branch operations among the prohibited ones while this dossier's
own FINDING says host agents never mutate Git state. I did not run them.

Instead `--source` is an EXPLICIT REQUIRED OPERAND with two routes that pass one
gate. I preflighted with `--source <the retained candidate checkout>`, which only
reads: that checkout survives from the consumed run, is clean, and sits at exactly
the sealed head and tree. The owner's run uses `--source reconstruct`. Both end in
`verified()`, so a source that is not bit-for-bit the sealed candidate refuses
whoever produced it.

This is named as a residual limit rather than smoothed over: the clone-and-fetch
mechanics are the one step the preflight did not execute, and they run first for
the owner. What de-risks them is that the bundle was independently verified
read-only — it carries `aa637298b` and requires `9055843b`, which is host HEAD —
and that its output is gated by the same digest checks.

## Measured, on the exact pinned base

    frozen verification argv .............. 83 tests PASS   0.187s
    R1 reproduces (reviewer's own probe) .. observations [true,true,true]
    original race at 9055843b ............. CONFIRMED KeyError 'job-a/implementation'
    original race at aa637298b ............ no longer reproduces
    stage --source <retained checkout> .... pass
    tools.bootstrap --no-repositories ..... pass            0.624s
    bind (held_packet + imported sources) . pass            0.427s
    git bundle verify ..................... okay, read-only against the host repo
    PREPARATION-PINS.json ................. files + 108 manager files, no drift

The last two race measurements are the ones that make `TASK-319624.md` honest. It
tells the worker the coherence work is done and must not be redone, and that R1 is
the one live blocker; both halves are verified rather than asserted from the
record. The composed packet was inspected too: `declared_base` and
`line_declared_base` are the candidate, the fixture pins are the candidate's
bytes and are verified under the nominated source at bind, and the bounds compose
as selected.

## The bound I propose changing, and why it is the owner's call

The consumed grant died at `turn_seconds` 600 while attempting the whole
correction. This delta is much smaller — a guard and its regressions, with the
design settled — so 600 would probably suffice. I propose 900 (total 1500) because
losing a second grant to the same bound costs more than the seconds do. Stated as
a selection, not a correctness claim: choosing 600 for parity changes nothing else
in the packet.

## What the task asks for, bounded

R1 only: `status` and `stage_states` must never reach an external observation
while a Job-store transaction is held; a safe early refusal is sufficient and
broader refactoring is not requested; the caller's transaction must be neither
committed nor rolled back. The required regressions are stated as OUTCOMES, and
the first one is deliberately strict — record the `in_transaction` state at each
observation, because the review found the existing test endorsed boundary
preservation without establishing the exclusion, and a test that only asserts
"a refusal was raised" would repeat that mistake.

The review's secondary note — `read_snapshot` on a closed handle raising a raw
`ProgrammingError` — is carried as an explicitly bounded item with instructions to
leave it alone if it grows. It is not the acceptance blocker.

## Not claimed

No Job submitted, no provider or engine invoked, no container started, no
credential contents read, no host product or test edit, no Git operation that
writes anywhere by this agent, no reuse of the consumed run's identity or
authority, and no canonical store access except through the v11 CLI. Provider
authentication remains unproved; the selected durable destination does not exist
yet; the W319114 defect is still present in the repository at `9055843b` and this
claim did not fix it, by design.

Cumulative verification spending this claim: about 2 seconds of measured
deterministic runs (83-test vector, two race reproductions, one boundary probe)
plus about 1 second of preparation steps. No broad suite was run and none is
implicated: this claim changed no product code.

A human Git checkpoint is not due for a preparation pass. The W319114 dossier is
entirely untracked in the host repository; whether to commit the preparation
records is Slawomir's call, and the packet does not depend on it.
