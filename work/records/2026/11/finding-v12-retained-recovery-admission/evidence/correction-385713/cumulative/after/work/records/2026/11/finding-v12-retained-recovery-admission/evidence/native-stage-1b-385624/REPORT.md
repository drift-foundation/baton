# W385624 Stage 1-B — implementation report and evidence

Source: `ce6e1b2bf12519a84a3792f06562b7727dfe3021` (delivered Stage 1-A).
Contract: `STAGE-1-CONTRACT.md` SHA-256
`52c2c640fdbb791e70ae61edf7ef7db7190bacd767d6d044f678517d2e09e1bc`, accepted by
`review-2026-11-22T05-18-37Z.md`. Normative `v12/DESIGN.md` REC-8.
Owner-approved profile definition record `stage1-verification-review-1.json`,
SHA-256 `5a6a420e416caab0942f9709939ae01f1f2d9dabbd13e09ff3b03ea08d2932fb`.

Candidate bytes: `candidate.sha256` (one digest per changed path).

## What was delivered

Two installed verbs of the `manager` command plus one new manager operation
pair, under DESIGN REC-8:

| Verb | What it does | Writes |
| --- | --- | --- |
| `manager recovery-item` | presents the delivered Stage 1-A owner item, its diagnosis, the original failed verifier and its declared context, the retained candidate, the four digests a decision binds, the proposed correction, the approved profile/digest, the selectable stage sets, what is already decided, and whether the asker holds the capability | nothing |
| `manager recovery-decide` | the owner's `--approve` / `--deny` / `--hold`, bound to every operand above; an approval then asks the manager to admit the one linked successor | one decision journal act, and on approval one reservation plus one submission |

Product: `job_manager/retained_recovery.py` (decision, admission, review-only
evidence, owner read), `tools/recovery_decision.py` (the verbs and the
production owner-port factory), the `job_control.PROFILES` entry for
`stage1-verification-review/1`, the `documents` `recovery.successor` answer
contract, three public aliases on `fresh_attempt` so its instance/cessation
rules are reused rather than copied, and `Authority.authorize_capability`.

## Verification

Run with the AMBIENT interpreter: `just` and the prepared environment
(`v12/python/TESTING.md` §2) are not installed in this container, and
`python3 -m tools.environment interpreter` refuses accordingly. Validator in
use: `jsonschema` 4.19.2, the version `requirements.lock` pins. Declared
logical groups affected: `job_manager`, `authority`, `scans`, `tools-pure`.

Environment, stated because it bounds what could be run here: `/var/tmp` is
read-only, `/tmp` is a 32 MiB tmpfs, and the only writable disk-backed
filesystem is `/output`, which IS the checkout. Fixtures that require real
storage OUTSIDE the checkout
(`tests/tools/test_stack.py::_disk_root_outside_the_checkout`) therefore refuse
in `setUp` before any product code runs. That is pre-existing and was measured
identically at the base commit.

### The focused acceptance entry this Work's criterion names

    cd v12/python; PYTHONPATH=src python3 -m unittest -v \
        tests.job_manager.test_retained_recovery_admission

`focused.log` holds the run; its own tail carries the measured counts and
duration.

### Groups

`authority.log`, `job_manager.log` and `scans.log` hold accounted runs and
their final two lines. `tools-pure` is reported as INCOMPLETE rather than as a
verdict -- in this container every consumer of
`_disk_root_outside_the_checkout` refuses, so the group cannot produce a
meaningful accounted result at all, and `tools-pure-partial.log` is kept
labelled as the partial run it is. The tools-pure module this slice's change
actually bears on is verified separately and completely:
`tests.tools.test_parallel_runner`, 73/73 OK (`parallel-runner.log`), which is
what checks the new module's execution-registry entry and its declared
consumed input. `COUNTS.md` tabulates all of it.

### The pre-existing `job_manager` failures, named

- 85 x `tests.job_manager.test_fresh_attempt` — every one refuses in `setUp`
  with "no disk-backed directory outside the checkout was found"; an explicit
  `BATON_V12_STACK_TEST_ROOT` on `/tmp` is refused as tmpfs by the workspace
  boundary. Measured at the base commit with the same cause
  (`baseline-fresh-attempt.log`).
- 1 x `tests.job_manager.test_native_permission` — the same cause, reported by
  `stage_execution._outside` as "inside the checkout".
- 2 x `tests.job_manager.test_tool` and 1 x
  `tests.job_manager.test_store_readonly` — each asserts a store filename
  appears in a refusal whose long temporary path is sampled out of the
  message. Measured at the base commit with the identical three ids
  (`baseline-path-messages.log`).

No remaining failure involves a changed product path or this Work's own
acceptance module.

## Claims this report does NOT make

- No verifier was executed, no retained candidate was materialized into a
  workspace and no candidate was handed to independent review. Stage 1-C
  (W385625) owns those, and the admission answer's `readiness` member says so
  on every admission.
- No live provider, model, container, image or engine was used anywhere. The
  analysis, the diagnosis and the successor's verification account are
  scripted documents driven through the supported boundaries, which is what
  the contract asks for.
- No full-suite `test-all` checkpoint was selected or run.
- No Git state was mutated, and no live deployment, instance or Job was
  touched.
