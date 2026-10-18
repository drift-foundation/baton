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
- `v12/python/src/baton_v12/authority/core.py` — `proposals_of` read.
- `v12/python/src/baton_v12/authority/api.py` — `proposals_of` on the
  configuration/read face.

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
