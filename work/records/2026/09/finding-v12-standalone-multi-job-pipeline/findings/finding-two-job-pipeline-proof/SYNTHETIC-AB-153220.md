# W71879 — deterministic A/B provider scenario, tuner153220

Owner153217 confirms the previous six observer tests passed on the operator host in3.477s and assigns the parent14:09:10Z/14:30:00Z deterministic scenario. Implementation is ready for the full operator test, without a preparatory reviewer-model turn.

From `/home/sl/src/baton/v12/python`, run this one command:

```sh
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 ../testing/standalone_ab/scenario.py
```

The command prepares a unique retained `/tmp/baton-synthetic-ab-*` root, builds provider/integration test images from the locally verified immutable base sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4, prepares disposable Git repositories and initial target ownership, provisions fresh public owners, submits once and starts the normal CLI factory. The operator needs Docker access, supplementary gid1001 and the existing `sudo chown` initial-target preparation privilege. This managed turn did not execute disposable Git setup, image construction or the container scenario. The command and its initial ownership step are concrete and documented in v12/testing/standalone_ab/README.md. No additional live-run permission or review-model gate is requested.

## Boundary and actual obligations

The test image replaces only the existing provider executable. ClaudeAgent, worker framing, integration workload and protocol/application modules remain unchanged. The provider matches explicit standalone-ab-v1 role/task text and fixture bytes, authors prescribed A/B edits, reads and checks actual candidate trees, runs checks, validates current derived candidate/causal evidence, and writes ordinary reports with current assignment/bundle digests. Reports explicitly label simulated judgments. It never writes Authority/manager state or receipts.

Both profile networks and image builds use network none. A private registry contains synthetic bytes; no real provider credentials or live model execution are involved. Real containers, worker/subprocess framing, independent private lines, frozen output custody, review, merge/reconciliation, causal test execution, downstream authorization receipts, leases and terminal observation remain. Existing whole1200/implementation240/review-or-judge180/integration120 limits and resource checks remain.

The scenario requires both Jobs complete, all three B derived judgments accepted, no live labelled runtime, clean unchanged original source, clean final target and passing final target tests. Run state, sample/status/serve/test evidence and setup/run wall times remain under the printed root. Failure containment is limited to that invocation's serve process and Authority-labelled containers; no retry or repair. This is simulated-provider coordination evidence; full scenario success is pending the operator result, and live-provider acceptance is separate.

## Changed paths and validation

New directory `v12/testing/standalone_ab/` contains standalone setup/runner, copied clock/read-only failure/target helpers, provider fixture executable, baseline/task/effect fixtures, README and source provenance. New `v12/python/tests/tools/test_standalone_ab.py` adds seven focused tests. `v12/README.md` links the command. No existing test assertions or protocol/application source were changed. New fixtures/tests are within the recorded W71830 standing authority.

The seven focused checks pass: actual provider subprocess writes only A scope; B check fails original base and passes isolated/merged fixture; unknown task or baseline drift refuses; original review validates bytes and writes ordinary report; all derived roles bind current candidate/causal checks; integration copies exact blobs and reports current operands; rendered eight-worker/judge deployment uses fresh public owners and network none. Unit derived-candidate reads and parsed integration bundle operands are explicitly controlled fixtures, not full pipeline acceptance; the operator scenario uses real Git reads and bundle validation. Python syntax, new-file whitespace, CLI help and README diff checks pass. The first five checks also passed before the additional coverage. Logs and exact24-path candidate hashes (23 new files plus README) are in `evidence/synthetic-ab-153220/`.

The original run10 result hash is unchanged, and the prior observer fix bytes remain. Historical358-entry custody still matches except its intentionally changed README and the earlier observer source/test deltas (those two still match preserved pre-fix bases). Historical packages, reviewer markers and live roots were not edited. Old acceptance bindings remain historical and do not approve this new scenario.

## Cost and next step

Current measured checks 0.939145608980s; cumulative recorded preparation/checks 121.978023511896s including the operator3.477s, plus retained uncertainty. Managed claim wall at this record 885.306s since14:33:13Z, including reading/reasoning/edits/checks, not model billing time; canonical pass records final handoff latency. Nine failed plus one interrupted live walls2945.872874202047s remain. No new container/model runtime was spent here.

Pass directly to baton.ops for the exact command and reported result. The full deterministic scenario remains unexecuted until that result; run10 remains interrupted and unsuccessful.
