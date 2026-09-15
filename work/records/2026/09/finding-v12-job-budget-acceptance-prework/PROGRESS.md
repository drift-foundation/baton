# Progress

## Claim 173987 — baton.claude, advisory read-only pre-work

Claimed W173923 standalone at seq 173987. Read this dossier's FINDING.md and
PLAN.md, W156162's canonical state (`phase: block`, seq 161306), its bound
dossier `work/records/2026/09/finding-v12-per-job-budgets` (FINDING, PROGRESS),
the current `execution_limits` owner and its consumers, the existing limits test
paths, and the accepted W170382 and in-flight W170385 evidence that carries
resolved limits. Claimed no original Work and did not interrupt the tuner.

**The substantive finding is that the FINDING's own preliminary source note is
superseded.** It recorded "no direct budget field in these insertion paths";
`submission.py:136` now inserts into `job_execution_limits` with
`execution_limits.CURRENT_GENERATION` and `:202 execution_limits_of` reads it
back. A complete owner exists at
`src/baton_v12/job_manager/execution_limits.py` with two Job-settable members,
four enforced boundaries, frozen default generations 0/1, a closed
`job`/`compatibility` origin vocabulary, explicit units and scope, and
refusal-without-clamp at the configured range.

I cross-checked all four boundary defaults against the runner constants the
module claims to read them from — 3600, 900, 1800 and 300 — and **all four
trace**, including `host_verification` -> `stage_execution.py:291 GIT_SECONDS`.
I expected that fourth one to be unpaired, because it is where a real defect was
found and fixed, and it is not. The report says so rather than reporting a gap
that does not exist.

The strongest reusable evidence is not from this Work at all: W170382's accepted
candidate corrected a demonstrated 1800/default mismatch to the original
Job-owned 300s `host_verification`, independently reviewed and owner-closed. It
already proves the resolved document reaches a real worker and that the
Job-owned value wins.

Recorded dependency versions from existing evidence only (python 3.13.7,
jsonschema 4.26.0, agreeing with `environment-172988.json`); no environment
project created. Historical cost preserved as recorded — 246 runs,
2530.584419 s plus four disclosed unmeasured activities — with no replenishment
or reconstruction gate proposed.

Deliverable: `PREWORK.md`,
`sha256:d4aace0dcd4aebe0123a332d22db186a35cc1ecf588abcb397acc0ed9cdb51af`.

**Boundaries honoured.** No test, probe, provider, model, engine, image build,
Git mutation or additional worker. No product, test or original dossier edit;
writes confined to this dossier. Verification spending this claim: **zero
measured seconds** — nothing was executed.

## Claim 174030 — correction after owner reroute 174026

The owner rerouted this advisory Work to correct the gap map, naming
`tools/test_execution_limits.py:362`,
`tools/test_execution_limits.py:1262` and
`job_manager/test_execution_limits.py` `newer_defaults` and its
generation/restart cases.

**The correction is warranted.** Sections 4 and 7 of my report claimed five
remaining acceptance items and two unresolved decisions that existing tests
already cover. I reached those claims by listing test filenames without reading
their cases — the same failure of rigour I had just warned two other owners
about in the neighbouring pre-work reports. Reading the cases showed the
coverage is broader than the three the owner cited, including range refusal and
two-/three-Job isolation.

Withdrawn explicitly: that the override path is the real remaining evidence gap;
that generation compatibility could pass vacuously or needs a new owner
decision; that `provider_turn` override acceptance is undecided; and that the
`GIT_SECONDS` separation needs its own case — it has one.

The correction separates the three categories the owner asked for: existing
tests, recorded acceptance evidence (W170382's accepted 1800→300 fix), and the
actual remaining managed-path difference — the end-to-end managed preparation
fixture configures no override, while the relocated boundary is covered at unit
level and the managed apply path carries an override end to end but is
in-flight W170385 work, not yet accepted. That is stated as a judgement about
evidence depth, not as uncovered behaviour.

`PREWORK.md` now carries the correction appended after the original text, which
is left intact as history.
`sha256:1b8e654bdc41b6a0904ec67c89db6f527257fcd958a5c950c16e6b188d034a33`.

Read-only throughout. Verification spending this claim: **zero measured
seconds**.
