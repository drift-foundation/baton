# Progress

2026-09-24, baton.tuner claim257612 on W247941: created W257627's planning
placement and D1/D2 contracts. D1 evidence command and planned test interfaces
are documentation, not executed evidence. No diagnosis, source correction,
image build, packet execution or live test performed. Historical evidence and
verification spending remain in W247941; ownership remains as recorded there.

2026-09-24, baton.tuner W257627 claim257715: authored DIAGNOSIS.md, EVIDENCE.json
and test_startup_boundary.py; updated this dossier FINDING/PLAN/PROGRESS only.
Read current handoff work-events through257715 and T257627 through257627;
revalidated claim and unchanged handoff with detail snapshot257731.

D1 reproduced missing-proposal TaskRefusal using all seven worker files matched
to IMAGE-ARTIFACT-244216.json for executed image c862c055...334ca2. Both real
exchange replays match original terminal/describe/work documents. Four tests
passed, unittest measured0.022s, 30s timeout/5s kill grace. This is the sole
focused test invocation under this claim; read/inspection wall times are not
claimed as a complete cumulative verification total. Prior campaign spending
remains in historical evidence.

No product or historical dossier edits, database access, credentials read,
container start/build, live provider, deployment mutation or Git mutation.
Read-only docker image inspect succeeded after an initial optional Labels
template error; absent Labels was command misuse, not a missing image.
Provider process seam was guarded against any call. Reproducer temporary
source/exchange trees were cleaned by their owning TemporaryDirectory helper.
Awaiting independent D1 review via baton.bug, then owner before any correction
or D2. Resource-hold recovery stays W257624.

## 2026-09-24 — baton.claude, claim 257839 — the bounded correction

**Selected scope only.** Owner reroute 257834 selects "only the bounded
output-declaration correction identified in DIAGNOSIS.md". **D2 is not begun**,
recovery scope is unchanged, no image was rebuilt, and no live provider or
deployed operation ran.

### The correction

`prepare_two_jobs.py:input_manifest` emitted `findings` and `logs`, both
required and both typed `text-result`. It now emits the **union** — `proposal`
as `git-change-proposal`, `findings` and `logs` as `directory-result` — with
**none required**. That is the product's own accepted shared-Job shape, not a
shape this dossier invented: `tests/tools/test_stage_execution.py:2438` already
carries it as `SHARED_OUTPUTS`, and `claude_agent.py:418-427` states the same
union and the per-role halves in the image itself.

### Where the obligation actually lives, which is the substance of this

Owner 257834 is right that "making outputs optional without downstream
validation is insufficient", and answering that objection is what made this a
correction rather than a loosening. **`required` is not what makes an
implementation produce a proposal.** `integration.driver._one_output` is: at
publication it selects the single output of TYPE `git-change-proposal` and
demands it `present` with both its artifact and its content manifest. So:

  * **optional is not permission** — a stage that published no proposal is
    refused at publication, by name, whatever its declaration said;
  * **one shared manifest is safe for two roles** — both stages declare
    `proposal` and only the implementation writes it, so a review result
    answers it absent and can never be published as one;
  * **the original declaration could never have published at all** — neither
    of its outputs carried a proposal type, so this selector finds zero and
    refuses. That is reached without the adapter at all, from the retained
    evidence's own `outputs` lists. The correction makes publication
    *reachable*; it does not let something through that used to be stopped.

The output TYPES therefore carry weight rather than decoration: three outputs
of one type would hand that selector three matches and no answer.

### A second defect in the same declaration, reported rather than repaired

Both original outputs were typed **`text-result`**, and the manager's own
`OUTPUT_TYPES` is `git-change-proposal, directory-result, record-output`.
`text-result` appears nowhere in product source. **Measured: no validator
enforces that vocabulary** — the type was accepted and would simply never have
matched a type-driven selector. So the correction's retyping of the review half
to `directory-result` is a real repair rather than a rename: the review turn
writes a *directory* of two files, which is what that type means.

The **absent enforcement** is a separate observation and is left as one. It is
in no owner's selected scope here, and inventing a validator would be exactly
the silent expansion `PLAN.md` forbids.

### Bound to the image's own constant

The emitted set is checked against `claude_agent.COMMON_OUTPUTS` — the
adapter's own statement of which outputs a shared Job carries, and the set
`_selected` refuses any name outside. The emitted set is a *subset*, because
that constant also carries `provider-context-receipt`, which the adapter
publishes itself rather than taking from the manifest. Composer and image can
no longer drift apart silently.

At the manager, `sealing._answers_the_assignment` (§12 rule 15) admits both
roles' envelopes under the corrected declaration, and **refuses the
required-variant** of the same union — so both ends agree about what a shared
Job's stage may answer, and "required" was not an option downstream either.

### `test_declaration_union.py` — 15 cases, all passing

Adapter half, against the seven image-matched worker files staged by hash
exactly as D1 stages them:

  * the emitted declaration is the union, none required, each with its own
    type — read off the composer rather than described;
  * **both stage roles** pass output selection and reach the task-reading
    sentinel, with the provider seam guarded against any call. The original run
    only ever failed the implementation half, so a correction checked at one
    role would be half a correction;
  * **controls**: the original declaration still refuses with "declares no
    proposal", and adding `proposal` alone is still refused — the near miss
    owner 257834 names, measured rather than assumed. The two *original*
    declarations used by the controls are read from `EVIDENCE.json`, so they
    are what actually ran rather than a reconstruction;
  * each role's produced/absent split comes from the product's own `_selected`,
    and `_absent` turns the other half into `missing-optional` entries whose
    status is checked against `baton_worker.OUTPUT_STATUSES` rather than a
    string this test invented.

Downstream half, against the real contracts named above — deterministic
documents, no container, image, network or provider.

### An ordering defect the new module found in itself

`test_startup_boundary.py` and the new module each stage their own hash-matched
`claude_agent`, and in one process the first import wins for both. The accepted
module's origin guard refused mine, correctly. **The accepted module was not
edited**: the new one now evicts staged imports on entry and on cleanup, so each
module re-imports from the tree it verified and run order stops being a hidden
input. Proved by running both orders.

### Evidence

```sh
cd /home/sl/src/baton
PYTHONPATH="$PWD/v12/python/src:$PWD/v12/python:$PWD/work/records/2026/09/finding-v12-startup-failure-fresh-packet" \
  PYTHONDONTWRITEBYTECODE=1 timeout --signal=TERM --kill-after=5s 30s \
  /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
  -m unittest test_declaration_union test_startup_boundary
```

  * `test_declaration_union` alone — **15 cases, OK, 0.167s**;
  * **both modules, both orders — 19 cases, OK, 0.193s and 0.192s**, which is
    the accepted D1 evidence re-run unchanged beside the correction;
  * the composer's own suite `test_two_jobs` — **85 cases, OK, 69.365s**
    (and 69.349s on the first run after the edit) — against the corrected
    `prepare_two_jobs.py`, with no test edited. Its command is the one already
    recorded in the adoption-gate dossier;
  * hashes at hand-off:
    `prepare_two_jobs.py` `sha256:a3141d792aa3ef0aca4efe0a8e98b793195cb5f21b90eaa7dfaf18b36d51434f`,
    `test_declaration_union.py` `sha256:1cf06a1ad6977f983ed7754dfab35686e3d0d22c0a7fbb2ee803d5e778798d5c`.

### Ownership

`OWNERSHIP-257839.md` records the coordination owner 257834 asked for: the
composer is taken for its `outputs` list only, `test_declaration_union.py` is
new under this claim, and **no product file under `v12/` is edited or claimed**.
`two_jobs.py`, `verify_247941.py` and `two_job_supervisor.py` stay read-only.

### Preserved

The retained instance, its original manifests, `EVIDENCE.json`, `DIAGNOSIS.md`
and the accepted review are unchanged. The correction says what a future
preparation emits; nothing rewrites what the failed run declared.

### Cumulative verification spending

This claim: focused module runs at 0.016s twice (the two red fixture-fault
runs, where the first draft called an `_answered` helper that does not exist),
0.132s, 0.134s, 0.167s twice; two-module runs at 0.152/0.154/0.156/0.189/0.192/
0.193s with three red ordering runs at 0.022/0.023/0.134s; `test_startup_
boundary` alone 4 OK 0.022s; and `test_two_jobs` 85 OK 69.349s and 69.365s.

All W257624 and W247941 spending stands unchanged, as recorded in those
dossiers' PROGRESS files.

### Constraints held

No live provider or engine, no deployed mutation, no image rebuild, no
container start, no deletion, no preserved-snapshot edit, no Git mutation, no
accepted test edited, no D2 work, recovery scope unchanged, W44342 untouched.

## 2026-09-24 — baton.claude, claim 258139 — the downstream evidence

Owner reroute 258136, after review-2026-09-24T15-33-06Z returned the
correction as **acceptance pending downstream evidence**: "Use emitted
manifests and deterministic provider output for both roles; carry actual
result bytes through sealing/intake and stage-result readers. Show positive
receipts and rejection of missing implementation proposal or review
findings/logs. Replace the task-reader sentinel as the positive proof and
correct the inaccurate test description."

The review's three findings were all correct, and each is answered below.
**No product file is edited in this round either**, and the composer is
unchanged from claim 257839.

### The sentinel is no longer the positive proof

Both roles now run the image-matched `ClaudeAgent.work` **to completion**
against the emitted manifest, writing real trees under a real `/output`:

  * implementation → `proposal/` with `candidate/`, `change.patch`,
    `result.json`, `verification.txt`, and the candidate carries the whole
    staged tree;
  * review → `findings/` with `report.json` and `findings.txt`, and `logs/`
    with `review.json`.

The sentinel cases are **kept and relabelled** as admission checks — the
question they ask is whether a declaration is *accepted*, which is what D1
diagnosed — and the module now says so rather than offering them as evidence
that anything was produced.

### The inaccurate description is corrected

The old docstring claimed a deterministic provider writes declared bytes while
the provider mock refused to be called at all. The module docstring now states
exactly what is real, what is supplied, and what is *not* executed.

### Actual bytes through the real readers

  * **`baton_worker.answered`** — the worker's own reader — holds each role's
    answers against the declarations and **measures** the trees, so the content
    manifests are measurements rather than strings. Proved to depend on the
    bytes: changing the provider's findings text changes the tree digest.
  * **`baton_worker.publish_completion`** writes the real
    `/output/output.json`.
  * **`sealing._completion_envelope`** reads those bytes back off the
    filesystem, validates them with the settled `completionManifest`
    validator, holds the assignment reference and recomputes the digest, with
    the manager's recomputed digest equal to the published one. *(Corrected
    under claim 258235: this is envelope **validation**, not a committed
    receipt. Calling it a "positive receipt" or a "whole chain" overstated it,
    as review-2026-09-24T16-14-50Z found. The committed receipts are in the
    next round below.)* It refuses an envelope answering another
    assignment's generation, and refuses the required-variant of the union;
    the worker refuses to publish that variant in the first place.
  * The frozen results handed to `integration.driver._one_output` are now
    built from those **measured** content manifests, so publication selects
    the bytes the turn wrote.

### The negatives

  * **Review missing findings or logs earns no verdict.**
    `review_cycles._review_result` requires separately frozen findings and
    logs, and refuses by name when either is absent. Reached from the real
    review turn's own measured artifacts, and a real turn whose provider
    reported nothing answers `unable` with `findings` absent, so there is
    nothing for that reader to admit.
  * **An implementation that produced no candidate.** This one **corrected me
    twice**, and the record says so. I expected the empty turn to answer its
    proposal absent so `_one_output` would refuse it — it does not: the
    adapter writes the proposal tree either way, because the transcript and the
    empty patch *are* the account of a turn that produced nothing. I then
    expected `_claim_of` to discriminate; it does not **under this profile**,
    because a claim carries a base and a head and these runs use the
    version-control-free `generic` profile, so neither turn attaches one and
    that reader refuses both. What does discriminate, measured from two real
    turns, is the **disposition**: `completed` versus `unable`. That is exactly
    the member publication's precondition reads — `retain_proposal` refuses an
    attempt with "no completed frozen result to propose" — and the test says
    plainly that **the precondition itself is not executed here**, because it
    takes a live manager store and a publisher session. What is established is
    that the value it reads differs between the two turns.

### What is real and what is supplied

One capability is injected — `ClaudeAgent(run=...)`, as the accepted adapter
suite injects it. The stand-in provider writes files into the working directory
it is given, which is the only way a real provider changes anything. The review
line's three object names are **answered** through that same seam rather than
executed, and the case asserts the exact vectors: `rev-parse --verify` only,
six of them (the observation brackets the provider turn), and one provider
call. **No repository is created, read or modified**, and no container, image,
network, live provider or credential is reached.

The worker half is the image-matched source and the manager half is the current
tree — stated in the module, because what this pairs is "this image's worker
against this manager", which is what a fresh packet would actually have.

### Evidence

```sh
cd /home/sl/src/baton
PYTHONPATH="$PWD/v12/python/src:$PWD/v12/python:$PWD/work/records/2026/09/finding-v12-startup-failure-fresh-packet" \
  PYTHONDONTWRITEBYTECODE=1 timeout --signal=TERM --kill-after=5s 120s \
  /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
  -m unittest test_declaration_union test_startup_boundary
```

  * `test_declaration_union` alone — **28 cases, OK, 0.286s**;
  * **both modules, both orders — 32 cases, OK, 0.304s and 0.306s**;
  * the composer's suite `test_two_jobs` — **85 cases, OK, 69.847s** — with
    `prepare_two_jobs.py` unchanged from claim 257839;
  * hashes at hand-off:
    `prepare_two_jobs.py` `sha256:a3141d792aa3ef0aca4efe0a8e98b793195cb5f21b90eaa7dfaf18b36d51434f` (unchanged),
    `test_declaration_union.py` `sha256:4624d83e6dfb822c066ff5fe6186ab3b74cdd2049843556e2362e66cd7cde7e7`.

### Cumulative verification spending

This claim: the red runs that found my own fixture defects — 28 cases with 10
errors and 3 failures at 0.282s, then 2 failures at 0.285s, then 1 at 0.288s
twice — and the green runs 0.283/0.286s, both-order runs
0.305/0.307/0.311/0.313s and the final 0.304/0.306s, plus `test_two_jobs`
85 OK 69.847s.

Claim 257839's spending stands as recorded above. All W257624 and W247941
spending stands unchanged in those dossiers.

### Constraints held

No live provider, engine or container; no deployed mutation; no image rebuild;
no deletion; no preserved-snapshot edit; no Git mutation and no repository
created or read; no product file edited; no accepted test edited; no output-type
redesign; no D2 work; recovery scope unchanged; W44342 untouched.

## 2026-09-24 — baton.claude, claim 258235 — committed receipts and the gate

Owner reroute 258233, after review-2026-09-24T16-14-50Z found two portions of
owner 258136 still unmet. **Both findings were right**, and the wording they
objected to is corrected in place above rather than left standing.

### What was overstated, and is now accurate

`sealing._completion_envelope` **validates** an envelope. It does not freeze,
commit or collect anything, so the previous round's "positive receipts" and
"whole chain" described more than it established. Those cases are kept —
envelope validation is real and worth having — but they are now labelled as
validation, and the receipts are produced separately and for real.

### Committed receipts, with nothing composed

A disposable `ControlStore` is opened per case and an attempt is carried
through the **supported** path — `issue_offer`, `accept_offer`,
`record_attempt`, `submit_claim`, `activate_assignment`, and the runtime and
disposition observations — and then:

  * **`output.request_freeze`** and **`intake.request_intake`** are called with
    an adapter whose `seal` and `collect` **are** `sealing.sealed_result` and
    `sealing.collected_result` over the tree the adapter turn actually wrote.
    `OciAdapter`'s own methods are thin wrappers over exactly those two calls;
    what is stood in for is the **container**, not the manager.
  * The intake receipt comes back `custody: accepted`, its manifest digest
    equals the freeze's, and its artifacts are exactly the half that role
    produced.
  * Both are **read back out of the store** — `frozen_output_of`,
    `intake_receipt_of`, `load_manifest` — and the retained result manifest
    carries the measured content for the produced half and `None` for the
    other.
  * **Custody holds the same bytes**, walked and compared file by file against
    the tree the turn wrote.

### The stage-result readers, fed the committed bindings

`review_cycles._review_result` is handed the **committed frozen result read
out of the store**, not a document this record shaped. It admits the review
attempt's — and every artifact locator points into the custody this manager
took, not into the worker's writable output. It refuses the implementation
attempt's committed result by name, which is the real "completed attempt of
this shared Job with neither review half", and refuses either half alone.

### The publication gate is executed

`integration.driver.retain_proposal` is **called**, not cited:

  * **positive** — a committed implementation result is retained, and the
    retained proposal manifest is bound to it member by member: `result_id`
    and `result_manifest_digest` equal the committed freeze's, the input
    manifest digest is the one retained at admission, the proposal artifact is
    `<attempt>:proposal` located in custody, and `output_digest` is the
    **measured** tree digest of the bytes the adapter wrote;
  * **negative, missing proposal** — the review stage's committed completed
    result is refused, and **nothing is retained**: the store holds zero
    proposal manifests afterwards, which is what makes "refused before
    publication" a fact rather than a reading of the message;
  * **negative, no completed result** — an implementation turn that produced
    no candidate is `unable`, and retention refuses it with "no completed
    frozen result to propose" before it looks at any output. **This is the
    precondition the previous round named and did not execute.**

### What is supplied, stated in the module

Three things, each named where it is used: the provider seam; the container
side of the runtime adapter (`Sealer`); and, for the retention case only, the
**worker's own claim** as a fixture — a proposal claim carries a base and a
head, and the version-control-free `generic` profile these turns run produces
neither. It is carried the way a worker carries it, in the completion
envelope's `result_metadata`, through the real freeze into the committed
result; every other member of the retained manifest is read back from its
accepted producer. Its `transport` names `change.patch`, a file the adapter
genuinely wrote, because the reader checks it against the measured entries.

The generic-profile evidence stays labelled as such. It does not prove the
packet's version-controlled proposal contract, and nothing here claims it does.

### Evidence

```sh
cd /home/sl/src/baton
PYTHONPATH="$PWD/v12/python/src:$PWD/v12/python:$PWD/work/records/2026/09/finding-v12-startup-failure-fresh-packet" \
  PYTHONDONTWRITEBYTECODE=1 timeout --signal=TERM --kill-after=5s 180s \
  /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
  -m unittest test_declaration_union test_startup_boundary
```

  * `test_declaration_union` alone — **37 cases, OK, 0.509s**;
  * **both modules, both orders — 41 cases, OK, 0.539s and 0.531s**;
  * hashes at hand-off: `prepare_two_jobs.py`
    `sha256:a3141d792aa3ef0aca4efe0a8e98b793195cb5f21b90eaa7dfaf18b36d51434f`
    (unchanged since 257839), `test_declaration_union.py`
    `sha256:f6d40f6b516b35995c3cbb431dc51489d0ef7c92cff11a32261b2cd80f0f34c7`.

The composer suite was not re-run this round: `prepare_two_jobs.py` is
byte-identical to the state it passed under, and no product file changed.

### Ownership

Unchanged. This round edited **only** `test_declaration_union.py`. It reaches
more manager modules — `output`, `intake`, `offers`, `review_cycles`,
`sealing`, `integration.driver`, `workspaces` — and **reads** all of them. It
also imports the accepted offer fixtures from `tests.manager.test_offers`
rather than reimplementing an Authority session, and edits nothing there.

### Cumulative verification spending

This claim: probe runs while building the fixture (untimed, four of them, two
red on the participant binding and the retained-manifest member names), the
red module run 37 cases 1 error 0.518s, and green runs 0.509s twice, with
both-order runs 0.530/0.531/0.533/0.539s.

Claims 258139 and 257839 stand as recorded above; all W257624 and W247941
spending stands unchanged in those dossiers.

### Constraints held

No live provider, engine or container; no deployed mutation; no image rebuild;
no deletion; no preserved-snapshot edit; no Git mutation and no repository
created or read; no product file edited; no accepted test edited; no
output-type redesign; no D2 work; recovery scope unchanged; W44342 untouched.
Every store, workspace and custody root is a per-case temporary directory
removed by its own cleanup.
