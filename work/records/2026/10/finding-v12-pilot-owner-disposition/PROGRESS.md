# Implementer progress — W321689

Author: `baton.claude` (role `impl`), v11 claim 323942, 2026-10-18.
Bound dossier: this directory. Blocker W321688 closed satisfying. Source base
`6348161e608187393e45454db63c192a93f6deb3`; `v12/python` is unchanged between
the W321688 checkpoint `433b09d6` and that base, the two intervening commits
being documentation only.

## 2026-10-18 — execution provenance determined BEFORE any source edit

The FINDING's execution-provenance checkpoint requires either the exact v12
Job/attempt identity or "the concrete unavailable operation and bounded
fallback before direct implementation". This is that record, written first.

**No v12 Job identity exists for this Work, and none can be created under its
accepted scope.** The two operations isolated v12 execution would require:

1. `baton-v12-stack bootstrap --inputs <deployment>.json --destination <root>`
   followed by `baton-v12-stack start` — installing and starting a NEW v12
   instance. That is a deployment/configuration act. This Work's own accepted
   scope states "No live provider/engine, production deployment/config
   changes", and owner M321677 defers deployment and pilot execution until
   after an independently reviewed packet (assessment owner decision 4). The
   operation is not unavailable mechanically; it is **unselected**, and
   selecting it here would be this implementer choosing the owner's gate.
2. `baton-v12-stack manager serve --engine docker --control ... --operations ...`
   with a configured implementation worker — which launches a Claude worker
   container and resolves provider credentials through the user's own
   `/home/sl/.baton/credential-sources.json` registry. That is live-provider
   execution. AGENTS.md "V12 verification defaults" admits a live provider only
   for a stated question deterministic coverage cannot answer; this Work has no
   such question, because its deliverable is authored source plus deterministic
   tests. The tree's fake/replay engines replay fixtures and cannot author an
   implementation, so there is no deterministic v12 execution path for this
   Work either.

Observed, so the blocker is not overstated: the machinery is present on this
host — `docker` 29.1.3 serving, prior `baton-v12-claude-worker` images
(`w239528-244216`, `w236087-236349`), archived instances under
`/home/sl/baton-v12/`. What is absent is the owner's selection of deployment
and live execution for W321689, not a capability. This is reported for owner
ruling in the handoff rather than resolved here.

**Bounded fallback taken** (OWNER-EXECUTION-20261018 names direct
shared-checkout implementation as the fallback once the blocker is recorded):
direct implementation of the paths below in this checkout; an isolated
candidate manifest with SHA-256 digests under `candidate-321689/` binding the
exact bytes for independent review; focused deterministic `unittest`
verification only. No deployment, no engine, no provider, no Git mutation.

## Owned paths

Product:

- `v12/python/tools/disposition_command.py` (new) — the owner disposition
  command: `pending`, `approve`, `deny`, `integrated`, `close`.
- `v12/python/tools/stack_command.py` — register the `disposition` subcommand.
- `v12/python/tools/bootstrap.py` — the selected owner grant.
- `v12/python/src/baton_v12/authority/core.py` — the `proposals_of` read and,
  after review 2026-10-18T16-55-00Z, the `bind_request` command-request
  binding.
- `v12/python/src/baton_v12/authority/api.py` — both of them on the
  configuration/operator face.
- `v12/python/tools/dossier_command.py` — the descriptor-anchored containment
  walk split so both commands share one implementation.

Tests (standing owner test-change authority 2026-09-13 applies; paths recorded
here as that ruling requires, not as a new approval gate):

- `v12/python/tests/tools/test_disposition_command.py` (new).
- `v12/python/tests/authority/test_session.py` — the pinned
  configuration-face enumeration gains `proposals_of`.
- `v12/python/tests/authority/test_boundary.py` — the pinned bootstrap-face
  enumeration gains `proposals_of` (and `open_readonly`, see below).
- `v12/python/tests/tools/test_bootstrap.py` — the selected owner grant.

No other Work's packet, pins or source is touched. W61981 owns
`v12/DESIGN.md`'s pending VER-1..5 addition; W321528 owns failed-run candidate
reporting. Neither is edited here.

## Pre-existing failures at the source base, not introduced here

Baseline run before any edit, at `433b09d6` with `v12/python` clean:

    PYTHONPATH=src python3 -m unittest tests.authority.test_boundary
    Ran 24 tests — FAILED (failures=3)

- `ExportedSurface.test_the_bootstrap_face_configures_and_reads_and_never_acts`
  — the pinned enumeration omits `Authority.open_readonly` (W126880). The
  public classmethod is reviewed and in use by `tools/dossier_command.py`; the
  enumeration simply was never updated. This file is already in my change set,
  so the omission is corrected there as an additive pin update.
- `EveryDiagnosticIsBoundedByTheRule.test_no_refusal_renders_an_unbounded_value`
  and `...test_every_named_site_covers_the_paths_it_was_written_for` — four
  unbounded caller-text interpolations in `src/baton_v12/authority/store.py`
  (`_writable` line 378, `_connect_readonly` lines 649 and 662). That is a
  product defect in a file **outside** this Work's scope and outside its
  acceptance. It is reported, not worked around and not papered over by
  editing the sweep's excuse list.

## 2026-10-18 — owner permits completing this Work directly

The FINDING's "owner permits W321689-only completion exception" supersedes the
stop-direct-implementation instruction for this Work: preserve the authored
work and finish its bounded outcome, reporting the execution path honestly.
That is what the entry above records and what the delivery below did. No v12
Job provenance is claimed for any byte of it, and the exception expires when
this Work closes.

## 2026-10-18 — delivered: the owner disposition command

One new packaged subcommand, `baton-v12-stack disposition`, with five verbs,
plus the one authority read and the one setup grant it needed. The operator
recipe is `PROCEDURE.md` in this dossier; the exact candidate bytes are bound
in `candidate-321689/DIGESTS.json`.

**What each acceptance clause is satisfied by.**

- *Pending owner action is discoverable.* `disposition pending` answers one
  closed `owner_action` per proposal and for the Work, derived from the
  receipts alone — no label, phase or Job status contributes — plus the
  dossier, its citations, the policy generation, and whether the asking
  participant holds each capability in the Work's own scope. It needed one new
  public read, `Authority.proposals_of(work_id)`: `proposal` answers from an
  identity the asker already holds, and nothing told the owner which identity.
  It is on the configuration/read face beside `works_with_labels`, not on the
  session, because it is an inventory question asked by an operator holding no
  claim.
- *Approve/deny the exact reviewed candidate.* `approve` and `deny` require
  `--expect-candidate-digest`, `--expect-review` and `--policy-generation` and
  compare all three before the session is asked. There is no `--actor`: the
  receipt's actor is the binding of the session minted for `--participant`.
- *Record human integration evidence.* `integrated` reads the human's
  `baton.v12.human-integration-record/1` document through W321688's
  descriptor-anchored containment, binds it to this authority, Work, proposal,
  candidate and commit, cites it by digest through `record_dossier_evidence`,
  then writes the authority's own immutable `integrate` receipt. Two durable
  acts, deliberately: a citation has no actor and a receipt has no commit.
- *Close with the selected acceptance.* `close --outcome satisfying` requires
  passed verification, accepted review, the owner's approval, the integration
  receipt and the cited record still intact under `--root`. `core.close`
  authorizes by capability and has no opinion about receipts, so without this
  a green execution flag would have terminalized the Work as satisfying; the
  acceptance check lives in the owner's command rather than being retrofitted
  into the generic transition, as the FINDING allows.
- *Refusals.* Stale candidate, wrong Work, missing/unaccepted/other review,
  stale policy generation, wrong actor, missing approval, missing or changed
  integration evidence, unknown outcome, and a non-satisfying closure handed
  candidate operands it would otherwise ignore — each refuses with its own
  sentence and writes nothing. Duplicate operation identities replay; changed
  retries collide on the signature.
- *Denial and non-satisfying closure preserve evidence.* Both paths report
  every proposal, receipt and citation that existed at the ending. There is no
  code in the command that deletes, rewrites or withdraws evidence.
- *Owner capability is distinct from technical review.* `owner_participant` in
  the bootstrap input grants `approve`/`integrate`/`close` in each bound
  Work's scope and deliberately not `verify`/`review`. The pilot assessment's
  recorded gap was exactly this: nothing a composed deployment configured held
  `close` at all. The member never travels into the emitted `stage_execution`
  configuration, whose schema is closed and whose consumers serve execution.

**One correction found by probing my own cut, recorded because the reviewer
would otherwise have to find it:** the first draft of `integrated` cited the
record before checking the actor's `integrate` grant, so a participant with no
grant left a citation behind and only then was refused the receipt; and its
refusal text told an operator to retry a durable refusal, which cannot
succeed. Both are corrected and both have their own case.

**Verification.** All deterministic; no provider, engine, container, network
or deployment, and no Git command.

- Focused suite — 943 tests, 46.289s, 2 failures, both the pre-existing
  `store.py` diagnostic-bounding failures recorded above and unchanged from
  the pre-edit baseline. `evidence/claim-323942/FOCUSED.log`.
- The new command's own cases — 52 tests, 0.449s, driven through
  `stack_command.main(["disposition", ...])` so the installed dispatch table
  is part of what passes.
- Frozen one-folder bundle — built from these bytes with the prepared v12
  interpreter (PyInstaller 6.16.0, no install, no network) and driven with
  `PYTHONPATH` removed over a disposable store: seven scenarios, the whole
  owner path plus the two refusals that matter, 0.836s.
  `evidence/claim-323942/FROZEN-COMMAND.json` and `frozen_command.py`; binary
  SHA-256 `2b1caa50fa1af5f7...` as recorded there.
- Packaging gate against that bundle — 11 tests, OK, including "every
  subcommand this command serves is offered", which failed against a stale
  bundle before the rebuild and is the check that proves `disposition` is
  reachable from a deployment rather than only from a checkout.
  `evidence/claim-323942/PACKAGING.log`.

Cumulative verification spending for this claim, measured rather than
estimated where a run reported its own duration: about 155s of test runtime
(final focused 46.289s; an earlier interim focused pass 46.452s;
stack/packaging/version/instance 28.595s; bootstrap 17.680s; the authority and
record suites 2.426s; three packaging runs at 2.25-2.27s; the baseline
1.085s; and roughly a dozen runs of the new file at ~0.45s), plus two
PyInstaller builds at about 6s each and two frozen-command drives at 0.83s.
Separately, one full-suite `unittest discover` was started and ABANDONED at
the 10-minute tool limit, so 600s of wall clock was spent for no result: it is
not evidence and nothing is claimed from it. The v12 default of focused
deterministic verification is why the gate here is the focused set rather than
that sweep. Per-run timeouts were 540-580s.

**Not done, and named rather than implied.** No deployment-wide "every Work
waiting on a human" inventory: this authority's public reads answer about one
Work or about labels, and inventing that sweep would be surface this Work did
not select. `record read --locator` is how an operator gets from a dossier to
a Work id. No multi-approver threshold policy (W16830 owns it). No automatic
integration, no Git mutation, no live run. `store.py`'s two bounded-diagnostic
failures are reported, not fixed.

**Pending after independent review:** a human Git checkpoint for this slice.
Suggested message `v12: add the supported owner disposition and closure
commands`. No commit is claimed and none was made.

## 2026-10-18 — correction for review 2026-10-18T16-39-10Z (claim 324341)

Both P1 findings are real, were reproduced with the reviewer's own script, and
are the same defect one layer apart: the authority's operation signature covers
the operands IT takes, and this command's semantic operands — which record,
which commit, which acceptance — were not among them. So one identity could
mean two different acts, and an identity that meant the SAME act could be
refused because the filesystem had moved on under it. Corrected in one
milestone as the review directed, with no new child and no core redesign.

**P1 (a) — changed integration retry.** `integrated` now looks up its own
committed outcome first, through §8's read-only `operation_result`, and
compares every semantic operand against the DURABLE record before anything is
written: the committed receipt's proposal, receipt identity and actor; the
dossier's citation of the named reference and the operation that cited it; and,
when the record is intact, the whole document including `--commit`. An exact
retry replays and writes nothing; a changed retry refuses and — the part the
review called out — cites nothing, because a citation added by a refused retry
is new evidence attributed to an act that did not happen. Drift at the cited
reference no longer refuses a recovery: the committed receipt is replayed and
the drift is reported beside it as `evidence_now`.

**P1 (b) — transient closure acceptance.** The selected acceptance is now
composed into the close's own durable `rationale` as one canonical
`owner-closure-acceptance: {...}` line (`ACCEPTANCE_SCHEMA`), so it survives in
the canonical record, rides the close operation signature — a retry naming a
different candidate collides instead of replaying somebody else's decision —
and is read back by `pending`, which also now reports `close_decision` and the
operator's own prose separately. §7's close takes a durable rationale and
nothing else an owner command may write, and the review explicitly did not
prescribe a generic close redesign, so a new authority column was not the
answer; the rationale is also the right place on the merits, since "because
candidate X with these four receipts was integrated by a human at commit C" is
precisely why this Work is satisfying. A `--rationale` carrying the marker is
refused: the command composes the clause from what it verified.

`close` also looks up its committed outcome first and replays it instead of
re-deriving the acceptance from disk — the lost-response case the review
reproduced, where an edited record made an identical retry exit 2 while the
Work was already closed and satisfying. A changed retry (other outcome, actor,
prose, proposal or candidate) refuses; a close under a NEW identity against a
closed Work is still refused by the authority's own sentence. `pending --root`
reports the accepted record's current state.

**Verification, all deterministic; no provider, engine, container, network,
deployment or Git command.**

- The reviewer's own `evidence/review-324303/reproduce.py`, re-run unchanged
  against the corrected bytes: `changed_integration_retry` now exits 2 with
  one citation and `replayed: false`;
  `exact_close_retry_after_evidence_change` now exits 0 with `replayed: true`,
  `evidence_now: changed` and the Work still closed; the closed readback
  carries `closure_acceptance`, `close_decision` and `rationale`. Captured at
  `evidence/claim-324341/REVIEWER-REPRODUCTION-AFTER.json`.
- Focused suite — 959 tests, 46.458s, the same 2 pre-existing `store.py`
  diagnostic-bounding failures and nothing else.
  `evidence/claim-324341/FOCUSED.log`.
- The command's own cases — 68 (16 new, in `WhatOneIdentityMEANS`), 0.636s,
  covering first execution, exact retry, retry after drift and after deletion,
  changed record/commit/candidate/receipt/actor/citation-operation retries,
  changed outcome/actor/prose on close, the hand-written marker, the
  non-satisfying replay, the operand-shape rules on both retry paths, and the
  fresh terminal readback of the acceptance.
- Frozen one-folder bundle rebuilt from the corrected bytes and driven with
  `PYTHONPATH` removed: 10 scenarios, 1.061s, now including the changed
  integration retry, the closed readback with acceptance and decision, the
  exact close retry after drift, and the changed close retry.
  `evidence/claim-324341/FROZEN-COMMAND.json`, binary SHA-256
  `1ff7e22e87bf5429...`.
- Packaging gate against that bundle — 11 tests, OK.
  `evidence/claim-324341/PACKAGING.log`.

Cumulative verification spending across both claims: about 215s of measured
test runtime (155s recorded for claim 323942, plus 51.661s focused, 2.204s
packaging and roughly a dozen runs of the new file at ~0.5s here), three
PyInstaller builds at about 6s each, three frozen-command drives at 0.83-1.06s,
and the 600s abandoned full-suite discover already disclosed above — still not
evidence and still claimed for nothing.

Changed paths and digests are unchanged in SET and refreshed in CONTENT:
`candidate-321689/DIGESTS.json` now binds the corrected bytes. `PROCEDURE.md`
documents the replay semantics and the new readback. No other Work's packet,
pins or source was touched; W321528 (claude_agent/baseline paths) and W324214
(its own record directory only) remain disjoint from everything here.

## 2026-10-18 — correction for review 2026-10-18T16-55-00Z (claim 324497)

Both findings are real and were reproduced with the reviewer's own script. They
also share one root cause, which the review named precisely: the command was
still comparing semantic operands BY HAND, and one of the things it compared
against was the cited file's current bytes. Mutable bytes are not a request
identity, so the comparison stopped holding the moment somebody edited the
record — and the `close` comparison, written by hand, simply omitted
`--expect-assignment` altogether. Both are now gone, replaced by one mechanism.

**The mechanism: the authority journals the command's request.** New bounded
API extension, which the review permitted and which needs no schema change
because it uses the operation journal that already exists:
`Authority.bind_request(work_id, request, *, operation_id)` on the operator
face beside `accept_base`. It binds the whole request document into the
operation signature, so the AUTHORITY decides what a retry is: an exact retry
replays the committed binding, and a request differing in any member collides
as "reused for different operands". It performs no transition, grants nothing,
writes no Work state, and is bounded by `own` like every other document
operand. `core.bind_request` carries the reasoning in full.

`integrated` and `close` each bind their complete canonical request under
`--operation-id` before any effect, and perform their authority acts under
identities derived from it (`<op>:integrate`, `<op>:close`; the citation keeps
`--evidence-operation-id`). Consequences, which are exactly the review's
required behaviours:

- A changed `--commit` refuses **regardless of later file availability** —
  after the record drifts, and after it is deleted. Nothing on disk is read to
  make that decision.
- `--expect-assignment` is part of the request, by presence AND value, so a
  close performed without an assignment precondition cannot be retried with
  one, or the reverse.
- An exact retry still replays after drift or deletion, with the drift
  reported beside the committed outcome as `evidence_now`.
- A collision answers JSON on stdout naming the request the identity already
  carries and the one just supplied, because that is the one refusal an
  operator cannot diagnose from their own command line.

`approve` and `deny` deliberately bind nothing, and the module docstring says
why: everything they record is already in the authority's approval signature,
and their two extra operands are compared against immutable facts (a
proposal's candidate digest, an accepted review's receipt identity), so a
changed retry is refused by the comparison rather than replayed. A binding
there would be ceremony that checks nothing.

**Two refusals deliberately precede the binding** so a correctable mistake does
not consume the command identity: a participant holding no `close` capability,
and a Work with a live assignment where `--expect-assignment` was omitted. Add
the operand and rerun the same command — which a case now proves.

**Verification, all deterministic; no provider, engine, container, network,
deployment or Git command.**

- Both reviewer scripts, re-run unchanged:
  `evidence/review-324482/reproduce.py` → `changed_commit_after_drift` exit 2
  with `performed: nothing` and one citation; `changed_close_assignment` exit 2
  with `performed: nothing`. `evidence/review-324303/reproduce.py` → still
  exit 2 / one citation for the changed integration retry, and still exit 0
  with `replayed: true`, `evidence_now: changed` and the Work closed for the
  exact close retry after drift. Captured at
  `evidence/claim-324497/REVIEWER-324482-REPRODUCTION-AFTER.json` and
  `REVIEWER-324303-REPRODUCTION-AFTER.json`.
- Focused suite — 966 tests, 46.701s, the same 2 pre-existing `store.py`
  diagnostic-bounding failures and nothing else.
  `evidence/claim-324497/FOCUSED.log`.
- The command's own cases — 75 (7 new in `WhatTheREQUESTBindingDecides`),
  0.721s: the reviewer's two scenarios, the changed commit after DELETION, the
  dropped assignment precondition, the binding's own replay/collision/verb/
  Work/document rules, and the derived-identity length bound.
- Frozen one-folder bundle rebuilt from these bytes and driven with
  `PYTHONPATH` removed — 12 scenarios, 1.261s, now including the added
  assignment precondition and the changed commit after drift.
  `evidence/claim-324497/FROZEN-COMMAND.json`, binary SHA-256
  `1cee05f6aff1f3b9...`.
- Packaging gate against that bundle — 11 tests, OK.

Cumulative verification spending across all three claims: about 265s of
measured test runtime (215s recorded through claim 324341, plus 46.701s
focused, 2.204s packaging and roughly a dozen runs of the new file at ~0.7s
here), four PyInstaller builds at about 6s each, four frozen-command drives at
0.83–1.26s, and the already-disclosed 600s abandoned full-suite discover, which
remains not evidence and is claimed for nothing.

Changed-path SET is unchanged; `candidate-321689/DIGESTS.json` binds the
corrected bytes. `PROCEDURE.md` documents the request binding, the derived
identities and the two pre-binding refusals. The two pinned surface
enumerations gain `bind_request` for the same reason they gained
`proposals_of`. W321528 and W324214 remain untouched.

## 2026-10-18 — correction for review 2026-10-18T17-12-52Z (claim 324624)

The finding is real and the diagnosis is exact: I had let a journal result at
an operator-supplied identity stand in for "this request was validated". The
citation identity is an operand, so any result there — an ordinary
`record cite`, or anything else that used it — made a *fresh* request skip
first-execution validation and write an integration receipt for a commit
nobody had read. A journal result is not a provenance.

**The rule now.** Exactly one thing may justify skipping validation: THIS
complete request having been validated and bound before. The request binding
is the only durable record of that, because validation precedes it and the
authority refuses to bind a different request under that identity. So both
composite verbs read `operation_result(--operation-id)` — the binding, not the
act — to decide whether anything may be assumed.

**And a result at any act identity must be that act's own.** Each committed
result is checked against its closed member set and its operands before it is
used or reported: a citation must be a citation of this Work and reference
recorded by that act (`_citation_fault`), the derived receipt identity must
carry an integration receipt for this proposal, receipt identity and actor
(`_integration_fault`), and the derived close identity must carry a close with
this outcome and actor (`_closure_fault`). A foreign result refuses before any
effect rather than being reported as this command's outcome.

**The citation is always re-offered** unless this same request already made
it. A pre-existing citation is convergent for the same reference and digest
and refused for a different one, so offering it is what proves it is the
evidence this request just read — rather than this command deciding that for
itself, which was the defect. That refusal now also prints the digest the
command read beside whatever the identity already holds, because "operation id
was reused for different operands" alone leaves an operator comparing nothing.

**Genuine partial recovery is preserved and now has its own cases.** A request
bound with nothing cited yet revalidates (it needs the digest) and completes;
if the record has drifted in the meantime it refuses honestly, having recorded
nothing; and a fully committed integration still replays after drift or
deletion with the drift reported separately.

**Verification, all deterministic; no provider, engine, container, network,
deployment or Git command.**

- The reviewer's E324601 scenario: exit 2, no integration receipt, the
  unrelated citation untouched, and the honest `'absent'` sentence because no
  record ever existed. `evidence/claim-324624/REVIEWER-324601-REPRODUCTION-AFTER.json`
  (their script verbatim except that it no longer assumes stdout is JSON — a
  refusal's sentence is on stderr; their own assertions are kept).
- Both earlier reviewer probes re-run unchanged and still correct:
  `REVIEWER-324303-REPRODUCTION-AFTER.json`,
  `REVIEWER-324482-REPRODUCTION-AFTER.json`.
- Focused suite — 976 tests, 46.863s, the same 2 pre-existing `store.py`
  diagnostic-bounding failures and nothing else. `FOCUSED.log`.
- The command's own cases — 85 (10 new in `WhatJUSTIFIESSkippingValidation`):
  the standalone citation with no record, with other bytes, and with the SAME
  bytes (convergent and legitimate); an identity carrying something that is
  not a citation; an identity carrying another reference's citation; a derived
  receipt identity carrying another receipt; a derived close identity carrying
  another act; a bound request whose citation never committed completing; the
  same with a drifted record refusing; and a completed integration still
  replaying after drift.
- Frozen one-folder bundle rebuilt from these bytes and driven with
  `PYTHONPATH` removed — 13 scenarios, 1.317s, now including the standalone
  citation case. `FROZEN-COMMAND.json`, binary SHA-256 `dc80e42eb77876db...`.
- Packaging gate against that bundle — 11 tests, OK. `PACKAGING.log`.

Cumulative verification spending across all four claims: about 315s of
measured test runtime (265s recorded through claim 324497, plus 46.863s
focused, 2.192s packaging and roughly a dozen runs of the new file at ~0.8s
here), five PyInstaller builds at about 6s each, five frozen-command drives at
0.83–1.32s, and the already-disclosed 600s abandoned full-suite discover, which
remains not evidence and is claimed for nothing.

Changed-path SET is unchanged at ten; `candidate-321689/DIGESTS.json` binds
the corrected bytes and its own SHA-256 is
`917cdb207d92903f35ffd742d931cec8fa376e9b64b8519b0a0188a048c8794b`. W321528
and W324214 remain untouched.

## 2026-10-18 — correction for review 2026-10-18T17-21-14Z (claim 324685)

Confirmed, and the cause is the ordering I chose last turn: the request was
bound BEFORE the citation, so a refused citation left the binding behind, and
the next identical call treated "this request was validated" as "its citation
succeeded". `_citation_fault` compared the Work, the reference and the
recording act — not the digest — so a citation of other bytes satisfied it and
the receipt was written on evidence the command had never matched.

**The correction is the one the review suggested: bind the validated evidence
digest.** The request is no longer "integrate citing that reference" but
"integrate citing THOSE BYTES, which I read and validated".

- First execution validates the record and binds `evidence_digest` with the
  rest of the request.
- A recovery takes that digest out of the journal (`_bound_evidence_digest`)
  instead of off the disk, so the citation step needs no filesystem at all.
- `_citation_fault` now compares the digest too, so a citation of other bytes
  can never satisfy this request — on the first call or the hundredth.
- The identity-provenance checks moved BEFORE the binding, so a conflict
  refuses identically every time and does not consume the command identity.

One behaviour changed deliberately, and it is an improvement rather than a
concession: a request bound with nothing cited yet now COMPLETES after the
record drifts or is deleted, citing exactly the bytes it validated, with the
drift reported as `evidence_now`. It previously refused, because it re-read
the file to find something to cite — which was the same filesystem dependence
these three reviews have been removing. A satisfying closure still refuses
while the cited record is not intact, so nothing rests on stale evidence; a
case asserts both halves.

**The failure matrix the review asked for** is now a test class rather than
another anecdote: `TheFailureMatrix` stops the command after validation, after
the binding and after the citation — each state built through the public acts
the command itself uses, in its own order — and reruns it, three times over:
untouched, with the record edited, and with the record deleted. Plus a changed
request after each interruption, a completed command replayed at every later
invocation, and the closure's own two stages.

**Verification, all deterministic; no provider, engine, container, network,
deployment or Git command.**

- The reviewer's E324673 two-call probe, re-run unchanged: both calls exit 2
  with `performed: nothing`, naming the validated digest against the cited
  one, and no integration receipt exists.
  `evidence/claim-324685/REVIEWER-324673-REPRODUCTION-AFTER.json`.
- The three earlier probes re-run: E324601 (its own variant that does not
  assume stdout is JSON), E324482 and E324303, all still correct. Same
  directory.
- Focused suite — 982 tests, 47.031s, the same 2 pre-existing `store.py`
  diagnostic-bounding failures and nothing else. `FOCUSED.log`.
- The command's own cases — 91 (6 new in `TheFailureMatrix`, plus the
  rewritten conflicting-citation and drift-recovery cases).
- Frozen bundle rebuilt from these bytes and driven with `PYTHONPATH` removed
  — 14 scenarios, 1.557s, now including the conflicting citation built through
  the installed `record cite` verb and retried. `FROZEN-COMMAND.json`, binary
  SHA-256 `8f6d6f2257aadc6c...`.
- Packaging gate against that bundle — 11 tests, OK.

Cumulative verification spending across all five claims: about 365s of measured
test runtime (315s recorded through claim 324624, plus 47.031s focused, 2.196s
packaging and roughly a dozen runs of the new file at ~0.9s here), six
PyInstaller builds at about 6s each, six frozen-command drives at 0.83–1.56s,
and the already-disclosed 600s abandoned full-suite discover, which remains not
evidence and is claimed for nothing.

Changed-path SET is unchanged at ten; `candidate-321689/DIGESTS.json` binds the
corrected bytes and its own SHA-256 is
`dbc163c7dc3f08fcf17030b78923029431c2f615c9bf9c797c5c9223a62b1c77`. W321528 and
W324214 remain untouched.
