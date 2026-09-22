# Partial implementation handoff — claim232393

At 2026-09-21T19:25:28Z, baton.codxpc returns W177936 incomplete through
baton.bug. This is not completion, integration approval, or live qualification.
No new owner planning approval is requested. Existing authorization continues
for the remaining implementation and preparation.

## Candidate corrections for independent review

R1: decode historical admissions without adding qualification_run to the signed
payload. A persisted journal/reopen test proves byte-preserving replay and
materialization. New admissions still bind the optional run member explicitly.

R3: the fresh transition and pending-request restart both revalidate live owner
facts and the selected grant inside the admission transaction. Deployment
operands now include authority UUID and configured context/workspace directory
identities. Grant reuse and execution recheck those operands. Regression tests
exercise a real competing journal commit between selection and commit (the
second assignment snapshot is synthetic), request restart, wrong authority and
replacement workspace objects. Old grants lacking these operands fail closed;
none is silently upgraded into new execution authority.

R2: certification rereads both retained generation snapshots, strict serving
receipt custody, invocation bindings and attempt provider logs. Caller-supplied
accepted strings are replaced by a committed independent accepted final-checkpoint
review and its retained findings report. That report binds run/context, attempts,
receipt/generation digests, provider files and a bounded recall determination.
Provider result bytes must be digest-matched successful terminal JSON for the
exact model and conversation. Missing/damaged evidence refuses even on a retry.
Production profile registration refuses without a committed certification;
production admission also validates the certification signature and deployment.

The specific `baton.context-qualification-review/1` report encoding is this
implementation's proposed realization of the accepted evidence contract. Review
must evaluate it. Its positive tests fabricate explicitly synthetic provider
results and use the normal deterministic review pipeline to commit the review;
they do not prove an executable live packet can supply these observations.

## Remaining scope and concrete dependency

R4 is UNDELIVERED: no qualification-run executable, immutable fresh manifest,
complete candidate profile/deployment/Job documents, or zero-placeholder owner
command was produced. Do not use an earlier consumed packet as a substitute.

The contract requires an independently rebuilt/selected image binding; the
retained e84a033c6600fdb65c92f5034e72db1578678d3adeb83df519b3845dee5925e0
image remains author-reported in the evidence read for this claim, not an
independent rebuild receipt. This claim performed no image build or independent
image verification. The current manager changes also need a rebuilt runtime
artifact before composing exact deployment documents. These are concrete missing
inputs, not a request to reopen the selected shared-UID posture or planning gate.

Implementation still owed even after those inputs exist:
1. Build the manifest-gated operator through the real serving path, with a fresh
   sixth run identity, explicit authority/workspace binding, report-and-hold,
   exactly open plus one restore, 180s per provider turn and 600s overall, no retry.
2. Compose and bind complete profile/deployment/Job/task/submission documents and
   retained evidence paths. Never modify the existing deployed serving setup in
   preparation or recycle any of the five consumed identities.
3. Make turn 1 choose a recall value absent from the repeated task; do not inject
   it into correction feedback or second-turn workspace. Prove second-input
   exclusion and collect both provider outputs plus private generation/receipt
   evidence for an independent accepted continuity review. The current test
   fabricates this report; the production packet must not.
4. Resolve how the independently executing review receives the private evidence
   required by this report without leaking the recall value to turn 2. Current
   packet code does not implement this transport. Exercise it deterministically,
   including manifest mismatch, timeout/cleanup, third-turn/refused retry and
   missing/damaged evidence. Do not treat certification unit tests as that proof.
5. Review the corrected implementation and packet together; publish one exact
   owner command only when all manifest-bound inputs exist. Live execution and
   enabling remain separate and unselected. Independent acceptance is still owed.

## Verification, costs and ownership

Final focused command (cwd v12/python):
`env PYTHONPATH=src:. timeout --kill-after=5s 120s /home/sl/.local/state/baton-v12-venv/bin/python -m unittest -q tests.manager.test_provider_context tests.manager.test_claude_context`
passed 132 tests in 34.144s. `git diff --check` passed. Only source docstrings
changed after that test. CORRECTION-EVIDENCE-232393.json pins current hashes and
all known runs, including failures corrected during development.

This claim's measured suite durations total 73.581s plus one ended process whose
output/time was lost during compaction. Prior reviewer measured 31.497s and prior
unknown author/reviewer costs remain; no total upper bound is claimed. No live
model, engine, image build, enabling, or repository Git mutation occurred.

This claim changed provider_context.py and the two context test files plus its
attributable dossier notes. Existing feedback, OCI/single_worker changes, other
participants' edits, five consumed identities, candidate-183524, old evidence
and append-only reviews were preserved. Those earlier product changes remain
in the combined tree and are hashed for review, not attributed to this author.
