# Plan

1. Read the parent and independent assembly acceptance; snapshot the two-path
   baseline. Enumerate current singleton-role consumers and exact new variant.
2. Record the new document members and held worker/pool interface here before
   edits. Use an explicit variant preserving old one-Job refusals; report any
   required external schema/path or assertion change before that edit.
3. Implement the configuration/pool result through existing public owners and
   add focused positive, duplicate identity, role/session, activation/replay and
   capacity/eligibility controls in the existing stage test module.
4. Before suites, record the question, command/scope and budget. Focused first,
   then one relevant broader regression sweep if retained evidence cannot answer
   changed boundaries. Do not run live OCI/model campaigns.
5. Return exact hashes, new variant/held pool interface, source/assertion delta
   and evidence through independent review. Shared paths transfer to the
   per-Job cut only after acceptance; no full-pipeline claim.

State: bounded plan created from M119126; baton.claude implements under its
own successful claim and returns for independent review. Live gates belong
to Baton. No product/test edits were made during placement.

## 2026-09-09 — enumerated before editing, claim129811

### Baseline revalidated, and it MOVED

The FINDING quotes `stage_execution.py` at `db280363…`. The tree holds
`da339acb…`, which is W119114's independently accepted candidate (closed
satisfying), and `tests/tools/test_stage_execution.py` at `62d8b13e…`. The
FINDING's own instruction is to revalidate the final accepted bytes before
successor implementation; these are them, and the line numbers it quotes have
moved with them.

### Every singleton-role consumer, enumerated

1. `_held_workers` (342) — refuses a repeated role outright.
2. `_sessions` caller (498) — collapses `workers` by role to derive the
   PUBLISHER participant from "the" implementation worker.
3. `Integration.required_tests` (1226) — refuses unless exactly one
   implementation worker, because the required tests come from one producer's
   configured task.
4. the integration worker lookup (1408) — `next(... if role == "integration")`.
5. `StageDeployment._roles` (1537) — collapses by role; `line()` (1552) reads
   `_roles["implementation"]["deployment"]` for the source nomination.
6. `_pool` (1776) — already emits one entry per CONFIGURED worker, so it is
   multi-capable today.
7. `_resolved` (1979) and the observation readers (2074) — already per-worker.

### The exact new variant

`MULTI_CONFIG_SCHEMA = "baton.v12.stage-execution-deployment/2"`, selected by
the document's own `schema`. `/1` is unchanged and closed: it still refuses two
workers for one role, and no assertion of its is loosened. `/2` admits several
workers per role. The member list is otherwise identical, so nothing outside
this file changes.

### The held worker and pool shape

Each held entry keeps its exact shape — `{worker_id, role, deployment}` — and
the list may now hold several entries with one role. Every existing per-worker
rule still applies to every entry: the Authority comparison, `single_worker`'s
own launch validation, launch-role agreement, the outside-the-checkout paths,
and the participant/principal independence rule across roles. `/2` adds one
rule `/1` got for free from its uniqueness: **worker identities are unique
across the whole pool.** Every role must still be served by at least one
worker. `_pool` needs no change; it emits one eligible entry per worker.

### The role-to-workers seam the next cut selects on

`StageDeployment._roles` becomes role → LIST, with two readers:

- `workers_for(role)` — every configured worker for a role, in configuration
  order. This is the seam; it never reduces a role to a singleton.
- `sole_worker(role)` — the one worker for a role, refusing when there is more
  than one. The four consumers above that genuinely need one producer today
  call this, so `/1` behaves exactly as it does now and `/2` refuses those
  per-Job questions with a sentence naming the next cut rather than silently
  picking the first worker.

The publisher session is the one generalization: `Authority.publish` takes the
PRODUCER's live assignment, so a pool with several producers needs one
publisher session per distinct implementation participant. `publishers` is that
mapping; `published_proposal` selects by the writer's own recorded participant,
which under `/1` is the same single session it uses today.

**What this cut does NOT do:** per-Job source, task, line, checkpoint or target
binding. `line()` still selects one global Work and source, and under `/2` it
refuses through `sole_worker`. Pool acceptance alone is not multi-Job execution.

### Question, budget and selectors, before any run

Do distinct implementation workers and independent review workers survive
configuration, activation and reconstruction with their intended eligible
kinds, profile and capacity — while every `/1` refusal stands unchanged?

Budget: **200s cumulative**, every run recorded with its command and wall time.
Selectors: `tests.tools.test_stage_execution`, then one broader sweep only if a
changed boundary is not answered by retained evidence.
