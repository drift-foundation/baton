# Implementer progress — W325959

Author: `baton.claude` (role `impl`), v11 claim 325968, 2026-10-18.
Bound dossier: this directory. Parent `W321608`. Owner selection
`baton:work/records/2026/10/finding-v12-development-coordination-pilot/SELECTION-325909.md`
(M325952 / E325954). Pinned source `14e52d80679de5e844f72324df632da5e01cf393`;
the working tree carries no product change and this Work authors none.

## Operational finding, recorded before any edit

**The bound dossier carried no `FINDING.md` and no `PLAN.md` when this claim
opened** — the directory existed and was empty, and `T325959` says the
"Dossier FINDING/PLAN will pin acceptance and ownership" in the future tense. I
am not proceeding without a scope source: the authoritative sources I can read
and am working from are the thread message `T325959` (which states the selected
outcome in full), the owner selection sheet `SELECTION-325909.md`, and the
accepted W321690 packet and its evidence. Both absent files are reported here
and in the handoff rather than guessed at; if the reviewer's FINDING/PLAN
narrows this scope, that narrowing is theirs to apply.

## Owned paths

Only this dossier. The W321690 parent artifacts, the three child dossiers and
every product file are untouched; accepted evidence is read and cited, never
modified.

## What this Work owes, from T325959 and the selection sheet

One immutable, instance-specific **preparation** packet — configuration,
submission, provenance and operator commands — for one new native v12
operator-quickstart Work. No execution, no launch, no cutover, no product
source change, and no live authority. Destination
`/home/sl/baton-instances/native-coordination-pilot-w321608-1` (fresh,
retained). Two stages only (implementation + independent review), separate
verify/review receipt actors, `baton.slaw` as human owner, dedicated diagnostic
ownership. An unresolved production value stays explicit and non-executable.

## 2026-10-18 — claim 325968: the pins, revalidated at the selected source

Everything below was read from the tree at `14e52d80` in this claim, not
carried over from the W321690 packet, and two pins moved:

* **`git diff --stat 372281f4 14e52d80 -- v12/` is NOT empty.** `2aa8ca56`
  added `v12/python/tools/worker_visibility.py` (1004 lines) and its tests
  (1426). So the W321690 packet's "record-only commits since" line does not
  hold at this source, and this packet re-states the provenance rather than
  inheriting it. `worker_visibility` is a separate tool and is **not** one of
  the thirteen `stack_command` subcommands — the installed surface is
  unchanged at thirteen.
* **The submission schema to pin is `baton.v12.job-submission/2`**, not `/1`.
  `documents.SUBMISSION_SCHEMAS` accepts both, but
  `SUBMISSION_LIMITS_SCHEMAS` is `('baton.v12.job-submission/2',)` — the
  `execution_limits` member a Job uses to carry the selected 3600 s provider
  turn exists only in `/2`. A `/1` submission cannot express the owner's
  selected limit at all.

Unchanged and re-read: thirteen subcommands; `bootstrap` REQUIRED nine /
OPTIONAL seven / `owner_participant` with grants `approve`,`integrate`,`close`;
`CURRENT_GENERATION` 1 with 3600/900/1800/300 and bounds 1/86400; authority
schema 6; `baton.v12.stack-instance/1`; `baton.v12.instance-recovery-set/3`.

**Two product facts that decide the packet's shape.**

1. `bootstrap`'s own validator makes the **integration role optional** —
   "owner 2026-09-20T14:57:48Z (W202663, the PR model): integration is a human
   act or an explicitly submitted ordinary Job, never an obligatory worker".
   So the two-stage pin W321690 established by driving it is also the
   product's own configured position, not a workaround. The `integration_profile`
   *document* is still REQUIRED at install, and its `integrator_participant`
   must therefore be named even though this Job submits no integration stage.
2. `bootstrap` **defers `jobs` and `workers`**: a fresh installation configures
   neither, because a worker's `deployment` carries a digest-sealed input
   manifest naming the Authority and the Work, which cannot be written before
   the instance exists. Preparation is therefore **two passes**, and the packet
   says so rather than pretending one command composes everything.

**No total or cleanup reserve exists as a product setting.** T325959 asks for
"3600s provider limits with total/cleanup reserves". `execution_limits` says in
its own words that each value is a per-invocation ceiling and that "none of
them is a cumulative allowance, a remaining balance, a budget the Job spends
down, or a limit on how long an agent may work in total"; cumulative accounting
and per-role pools are deferred. A Job can express exactly two members —
`provider_turn_seconds` and `verification_command_seconds`. The packet
therefore pins those two and states the total and the cleanup allowance as an
**operator-side wall-clock envelope**, explicitly not a configured limit. The
only teardown number in the product is `oci.stop_vector`'s `seconds=30` stop
timeout.
