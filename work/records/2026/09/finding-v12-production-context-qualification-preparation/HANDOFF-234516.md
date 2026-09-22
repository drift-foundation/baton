# Claim234516 — isolated canary packet ready for independent review

Owner234513 / FINDING 2026-09-22T00:20:58Z selected the isolated construction
instead of general private-evidence delivery and a dedicated reviewer image.
This claim implements that preparation in isolated_canary.py and nine focused
deterministic tests, with CANARY-MANIFEST-234516.json, CANARY-OPERATOR-234516.md,
CANARY-COMMAND-234516.txt and CANARY-EVIDENCE-234516.json. No product source or
older candidate/evidence/test changes. The strict terminal contract dependency
is unchanged. Historical unfinished production evidence remains preserved.

Manifest SHA256:
1ad6342ab05ad765f51d251190f2a48591e15164b1170b27399ee1e63f77f62d

## Independent review target

Review the actual controller and mounted worker code, not only the test verdict:
- two fresh Docker workers, empty read-only input/source/workspace roots, distinct
  HOME and disposable tmpfs; only the exact designated session file reconstructed;
- strict provider build/model/session/result checks, no canary in second prompt;
- exact image/uid/mount/runtime inspection, successful first stop/removal before
  state read or second admission, protected evidence and independent --review;
- exclusive consumed identity, no third turn/retry, 180s per provider invocation,
  420s controller, 600s overall envelope, parent process-group fencing and exact
  label-bound cleanup with uncertainty reported as failure;
- manifest audit, pinned code and supporting evidence, zero-placeholder command.

The session path .claude/projects/-output/<UUID>.jsonl is the candidate's exact
allowlist, not a newly demonstrated provider fact. The real provider must create
and resume it; otherwise this experiment refuses without widening the copy.
The fake provider deliberately writes other HOME files, and the second worker
asserts they are absent. Tests exercise the same worker/controller code with only
the Docker/provider boundary simulated, plus a real subprocess output/timeout
boundary and real parent supervisor timeout. They do not emulate kernel mount
permissions or count as a live image/provider qualification.

The final nine-test suite passes in 0.3639068159973249 supervisor seconds,
0.298 unittest seconds. Earlier iterations: eight tests0.31390757707413286s,
nine tests0.3638895699987188s. New measured test total1.0417039630701765s;
all groups absent and no harness timeout. The first iteration exposed a scandir
ResourceWarning, corrected before the final run. Final timeout test intentionally
terminates a sleeping child; its InterruptedError traceback in the retained log
is expected failure-path evidence, while the suite and cleanup assertions pass.
Offline exact-digest audit and git diff --check pass. No broad suite repeated
because no product code changed. No live/engine/image build/installation or Git
mutation. Prior totals and unknowns remain in CANARY-EVIDENCE and older records;
they are not erased or converted into a manufactured cumulative upper bound.

## Meaning and next action

This is a qualification-specific direct-Docker fixture under the owner's
simplification. Its two fixture attempt names are bound to W177936/run/session;
they are explicitly not v12 scheduler assignments or serving receipts. It never
opens coordination storage, consumes a production grant, injects a verdict or
certifies/enables production. Independent offline review evaluates the actual
protected run evidence after both workers stop. A recall match proves neither
cache savings nor the full production certification contract.

After this independent packet review, pass baton.decide for the exact live-run
selection. No further implementation gap is claimed for the selected isolated
fixture; provider behavior, real mount enforcement and real cleanup remain the
honest live facts the prepared experiment will observe. Production R1–R3 and
four capsule/275 guard tests plus the unchanged verified manager/image evidence
remain separate. Do not present this fixture's output as full-config production
certification or silently revive the superseded reviewer-image requirement.
