# W319114 R1 correction — proposed execution selection

Second proposed execution for this Work. The first grant was consumed: it timed
out at 600 provider seconds, and the three-file candidate it left is sealed,
reviewed and carries one requested correction (R1). This packet asks the provider
for THAT CORRECTION ALONE, starting from the reviewed candidate rather than from
the repository baseline, so a grant is not spent redoing accepted work.

Owner selection is required before any of this runs. Nothing here has been
executed; the preparation has only been preflighted in a disposable root.

## What is different from the consumed run

| | consumed run (319417) | this packet (319624) |
|---|---|---|
| declared base | `9055843b` repository baseline | `aa637298b` the reviewed candidate |
| scope | the whole coherence correction | R1 only: refuse before observing |
| provider turn | 600s — **timed out** | 900s proposed |
| total / cleanup | 900s / 60s | 1500s / 60s |
| verification | 83 tests, frozen argv | unchanged |
| run id | `status-race-w319114-319417` | `status-race-r1-w319114-319624` |

THE TURN BOUND IS A SELECTION, NOT A CORRECTNESS QUESTION. 600 seconds was not
enough for the whole correction and the run was lost to it. This delta is far
smaller — the design is settled and the required change is a guard plus
regressions — so 600 would very likely be enough. 900 is proposed because losing
a second grant to the same bound costs more than the extra seconds do. Select 600
for parity if you prefer; nothing else in the packet changes.

## The real-provider question

Can a fresh worker take an independently reviewed candidate and land the ONE
correction a review asked for — a bounded refusal that keeps a caller's
transaction intact — through the adopted v12 pipeline, with real provider
invocation, contained deterministic verification and a retained result?

The consumed run answered the first half of the adoption question: a real
provider did produce useful, reviewable code through this pipeline. What is
unproved is the review-correction loop closing through v12, and today's provider
authentication. Deterministic fixtures reproduce and verify the defect — this
record does so below — but cannot author the proposal or establish that
authentication.

## Commands

Proposed new destination: `/home/sl/baton-instances/status-race-r1-w319114-319624`.
It must not exist; its parent must already exist. Execute from `/home/sl/src/baton`:

```sh
python3 -B work/records/2026/10/finding-v12-status-concurrent-submission/prepare_r1.py stage --root /home/sl/baton-instances/status-race-r1-w319114-319624 --source reconstruct

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/status-race-r1-w319114-319624/code/v12/python/src:/home/sl/baton-instances/status-race-r1-w319114-319624/code/v12/python python3 -B -m tools.bootstrap --inputs /home/sl/baton-instances/status-race-r1-w319114-319624/bootstrap-inputs.json --destination /home/sl/baton-instances/status-race-r1-w319114-319624/instance --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro --no-repositories

python3 -B work/records/2026/10/finding-v12-status-concurrent-submission/prepare_r1.py bind --root /home/sl/baton-instances/status-race-r1-w319114-319624
```

`--source reconstruct` IS THE OPERATOR'S STEP AND IS WHY THESE ARE YOUR COMMANDS.
It clones the host repository into the new root and fetches the sealed candidate
commit out of this dossier's digest-bound bundle. The host repository is read and
never written and no commit is created anywhere, but it is still a Git operation
that writes — into the disposable clone — and repository agents do not perform
those. The preparing agent used `--source <existing checkout>` instead, which
only reads. Both routes pass the SAME gate: HEAD, tree, parent commit, worktree
cleanliness and four pinned file digests must equal the sealed candidate, or
preparation refuses.

These steps only prepare. Preserve `PREPARED.json`, `packet/PACKET.json` and all
artifact digests in the execution handoff. Fresh bootstrap creates the isolated
UUID; never reuse a preflight authority. Do not invoke the installed justfile
start: the selected runner is the digest-bound Python supervisor. Execute the
exact `start` argv from `packet/commands.json` with its `environment` applied.
Start alone owns submission; no manual second submit. Preserve stdout/stderr,
`outcome.json` and every referenced artifact.

## Pinned selections

Existing image `baton-v12-claude-worker:w239528-244216`, config digest
`sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2`,
Claude CLI 2.1.247, bridge network, operator-file credential reference
`w202663-development` via `/home/sl/.baton/credential-sources.json`. No
credential contents were read and current authentication is unproved.

Base `aa637298bac292058b659df5d147fbddd82c49a6`, parent
`9055843b5d258f5bfbb523815d034ee0c14075d6`, tree
`57f5d49cc89fd543345eddf84cb2a95f03eecfd0`. Every reused composer, supervisor,
manager and evidence byte is pinned in `PINS-319624.json` and
`PREPARATION-PINS.json`; preparation refuses on any drift. One implementation
invocation, no automatic retry, no review worker admitted.

## What the preparing agent measured, on the exact pinned base

- The frozen verification argv: **83 tests pass in 0.187s** — the 30-second
  verification bound is ample.
- R1 still reproduces, through the reviewer's own retained probe: three external
  observations with `in_transaction` true, caller boundary released afterwards.
  So the task describes a live blocker, not a historical one.
- The ORIGINAL race is genuinely fixed on this base: the baseline reproducer
  raises `KeyError: 'job-a/implementation'` at `9055843b` and no longer
  reproduces at `aa637298b`. The task tells the worker not to redo that work,
  and this is why that instruction is true.
- Full preparation chain preflighted in a disposable root: stage, supported
  bootstrap `--no-repositories` (0.62s), bind with `held_packet` and
  imported-source validation (0.43s). Composed `declared_base`,
  `line_declared_base`, candidate fixture pins and bounds all verified.

## On any refusal, timeout or uncertain cessation

Retain evidence and return the exact checkpoint through v11; do not recycle this
run identity. Collect proposal base/head/tree, complete changed paths, patch and
file hashes, verification result, worker exit and supervisor cleanup evidence.
Independently preserve proposal bytes before releasing mutable storage — the
consumed run's survival depended on exactly that.

READ THE SUPERVISOR'S WORDING WITH CARE. The consumed run's `outcome.json` said
"no proposal" while a useful sealed candidate existed: the supervisor excludes
noncompleted dispositions from its successful-proposal inventory. A
timeout/unable result does not mean nothing was produced. Check
`packet/workspaces/.baton-review-lines/*/checkout` and the sealed proposal files
before concluding the run was empty.

Route W319114 to `baton.rvpc` for review of the exact retained bytes and
independent deterministic verification. The runner admits no review worker and
issues no acceptance. Human-plus-agent integration stays separate.
