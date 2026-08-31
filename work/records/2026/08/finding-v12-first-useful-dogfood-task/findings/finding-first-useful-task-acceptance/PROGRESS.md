# Progress

## 2026-08-30 — first implementer round (`baton.claude`, W39364 impl claim)

W39358 closed satisfying at seq 49176, so PLAN item 1 is unblocked and this
round did it. **No execution claim has been accepted and no run was started.**
Three things gate the run; two were known and one was measured this round.

### The two operator grants, still not supplied

The FINDING is explicit: "The live run requires two explicit human/operator
grants: the exact credential source operand and the exact network posture.
Neither is inferred from W17110 or selected by an implementer. The run does
not start until both are supplied." Neither arrived with the assignment, and
neither is mine to choose. Revalidated against the tree, they are exactly:

  1. **The credential source operand** -- the `--credential-file PATH` of the
     documented command. `claude_agent.py` requires a credential at
     `/run/baton/credentials/claude` (`CREDENTIAL_ROOT` + `CREDENTIAL_SLOT`)
     and REFUSES an absent slot rather than falling back:
     "this container has no credential at ...; the operator authorizes the
     exact credential source and this adapter has no home-directory or
     ambient fallback". The provider reads it as `.credentials.json` through
     a symlink in a private home, so the operand names a file in the provider
     credentials-document shape rather than a bare key. The path is not the
     secret and never lands in the grants file (13); the bytes are read once
     into memory by the launcher.

  2. **The network posture** -- the `network` grant. The documented example is
     a user-defined network name (`"baton-dogfood"`). This is the one grant
     the frozen task cannot succeed under `"none"`, because a provider-backed
     worker IS a network client -- but WHICH network, and whether it is the
     right posture for a supervised live run, is an operator decision and is
     recorded rather than assumed.

### The measured blocker: the frozen subset cannot run its own verification

Staged the frozen three-path subset into a clean root and ran the frozen
verification command. 11 of 26 cases error before the worker contributes
anything, because `test_harness.py:402` reads a FOURTH file, `trial.mjs`,
which the subset does not deliver. Adding that one path makes the command
pass. Full measurement, both directions, and the `node`-on-PATH precondition
that goes with it: `evidence/w39364-subset-revalidation.md`.

This is not mine to fix. `evidence/first-task.md` is the PARENT's frozen
artefact and this child's FINDING says to use it verbatim; amending the
delivered subset would be an implementer selecting the delivery the milestone
exists to measure. As written, W39364's own acceptance criterion -- "a
reviewer independently ... runs `python3 v12/spike/ping-pong/test_harness.py`
outside the worker" -- is unsatisfiable on the frozen subset.

### What IS revalidated and ready

- The three named paths exist and the harness passes in the canonical checkout
  (26 tests, OK).
- The task document shape is settled: `held_task` takes exactly `schema`,
  `task_id`, `instructions`, `verification`, `source_root`; `source_root` must
  be the fixed `"source"` (`SOURCE_TARGET`, and `claude_agent.SOURCE_ROOT`
  holds the other half by equality); `verification` is the frozen argv
  `["python3", "v12/spike/ping-pong/test_harness.py"]`, which `_derived`
  reruns with `cwd` at the collected candidate -- the same command the
  acceptance asks a reviewer to run.
- `GRANT_MEMBERS` is a closed set of 31 members with no defaults and nothing
  read from the environment. Every one but the two above is deployment or
  identity material this round can compose.
- The dogfood image's entry is `dogfood_entry.py` calling
  `baton_worker.main(agent=ClaudeAgent())`, at `/opt/baton/dogfood_entry.py`
  -- the exact path `dogfood_operator.WORKER_PROGRAM` execs, which W39358's
  real-engine gate now holds.

I deliberately did NOT author `task.json` or a grants file this round: both
would have to embed the unresolved subset decision, and a prepared artefact
carrying an implementer's guess at a frozen delivery is worse than none.

### Next, in order

1. The parent rules on the subset (add `trial.mjs`, or re-scope).
2. The operator supplies the credential source operand and the network
   posture.
3. Then: one fresh attempt from clean operator-owned roots, bounded correlated
   transcript retained, independent inspection, and an explicit accept/reject.

## 2026-08-30 — second implementer round: THE RUN HAPPENED

All three gates cleared: the four-file supersession (M50427), the credential
source and the network posture (M50427, verified M51386). **One supervised
attempt ran, for real, and resolved.** Exit 0.

Full acceptance record: `acceptance-2026-08-30T22-49Z.md`.
Retained evidence: `evidence/w39364-run1/`.

### Disposition: REJECT the candidate; the platform arc is PROVEN

Two separate facts about one run, kept separate. A real container ran the real
worker, held a real correlated `describe`+`work` conversation with a real
provider turn on the authorized credential and network, and the manager froze,
collected, receipted, retained, normalized custody and destroyed the runtime --
eighteen journalled operations, all committed, `resolved: true`,
`unresolved: []`. That is the milestone, and it worked.

The worker then answered `unable`, and its candidate is byte-identical to the
delivery. The sealed content manifest says so file by file and `change.patch`
is zero bytes; the operator's own independent derivation says
`changed_paths: []`. None of the frozen task's four required facts is
established. `verification_status: 0` is the 26 PRE-EXISTING cases still
passing over an unchanged harness -- a baseline, not a result, and reading it
as acceptance would be the exact mistake the acceptance criteria exist to
prevent.

### Two findings, both in the operator, which this child does not own

**[P0] The retention disposition is hard-coded, so no candidate survives.**
`dogfood_operator.py:1227` passes `disposition="discard-after-intake"` as a
literal; the `retention_policy_digest` grant names a policy whose disposition
nothing reads. The manager has `retain` and `quarantine` and the operator never
asks for either. Measured consequence: the sealed result's own locator names a
`proposal/` directory that does not exist, and `result.json` -- the 388 bytes
that would say WHY the provider was unable -- was destroyed before any human
could read it. So W39364's acceptance step ("a reviewer independently diffs the
candidate ... and runs the harness outside the worker") and this assignment's
own "retain ... external candidate" are both unreachable through the documented
command as written.

**[P1] `preflight` does not hold `human_contract`.** My first invocation was
refused by `check_input_pair` inside `compose_input_root` -- AFTER the source
was staged, the claim submitted, the assignment activated and the credential
slot materialized. `human_contract.locator` passes the `artifactRef` pattern
(`scheme:anything`) and fails the manifest's `check_uri`
(`scheme://authority`): two grammars, only the later one enforced. That is
precisely the interval `preflight`'s docstring says it exists to remove, and
its own history records the same defect being fixed for the record binding.
No runtime started and no provider turn occurred, so the authorized attempt
was not consumed -- but the claim and activation were, which is why the run
that followed used fresh roots and fresh identities.

### Two things I got wrong, found by using the thing for real

- My first `human_contract.locator` was the opaque `baton:<path>`. Corrected to
  canonical `file:///<abs>`, and I then validated the WHOLE document pair with
  `check_input_pair` in a dry run -- no claim, no container -- before spending
  the attempt.
- That dry run also caught `__pycache__/*.pyc` in the staged tree, left by my
  own baseline harness run inside the staging directory. Bytecode is not one of
  the four frozen paths. Restaged clean; the delivery the worker received is
  exactly four files.

Both are the same lesson this campaign keeps teaching: the executing case
found them, and a dry run that composes the real documents costs one minute
and saves an authorized attempt.

### Not done, and why

I did not re-run to recover the worker's account. One attempt was authorized,
one was taken, and a second would discard the account again for the same
reason. The P0 belongs before another attempt is worth taking.
