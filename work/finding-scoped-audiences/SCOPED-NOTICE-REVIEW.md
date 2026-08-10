# Scoped-notice implementation review — changes requested

Reviewed 2026-08-10 against the handoff subject
`Scoped notices landed: one frozen-audience mechanism, global included`.

Outcome: **changes requested**. The schema direction and selector grammar are
sound, but four public paths bypass or omit the frozen audience. The current
focused suite does not exercise them.

## R1 — `mark_notice_seen` delivers scoped content to a non-member

Severity: critical.

`Store.mark_notice_seen(participant, notice_id)` selects the notice by ID and
never checks `notice_audience`. Any configured participant who learns a scoped
notice ID can retrieve its content and create a seen receipt even when the
notice was not addressed to them. `list_notices`, `list_notice_activity` and
`see` use membership correctly; the TUI's explicit-open path does not.

Reproduced through the public Store API: publish `scope="acme.*"` from
`hq.lead`, then call `mark_notice_seen("hq.lead", notice_id)`. It returns the
team-only content instead of refusing.

Required:

- authorize explicit open against `notice_audience` in the same transaction
  that records the receipt;
- make the schema enforce that every `notice_seen(notice_id, participant)` is
  a member of `notice_audience`, preferably with a composite foreign key, so
  another code path cannot recreate the bypass;
- regress first open, repeat open, and no receipt/content on a non-member
  refusal, through both Store and the packaged TUI/open path.

## R2 — `has_unseen_notice` ignores membership

Severity: high.

The read-only probe used by `wait_for_message` asks only whether a live notice
lacks this participant's receipt. It does not require an audience row. A
scoped notice therefore reports work to every unrelated participant, causing
`wait` to enter `see` and take a write transaction even though `see` returns
nothing. This violates the scoped wakeup contract and restores avoidable
cross-team contention to the exact idle path the probe was created to keep
read-only.

Reproduced through the public Store API:
`has_unseen_notice("hq.lead")` returns true for an `acme.*` notice.

Required:

- use the same membership predicate in the probe as in `see`;
- add scoped-notice regressions for already-present, publish-while-blocked,
  degraded polling and the query-to-arm race;
- prove an unrelated participant neither receives nor records a receipt and
  does not enter the notice write path merely because another team has an
  unseen notice.

The unchanged global wait tests are useful parity evidence, but they cannot
catch a missing scope predicate because every participant belongs to a global
audience.

## R3 — `regen` can strand a frozen audience member

Severity: high.

`regen_instance` protects notice authors but never selects
`notice_audience.participant`. It therefore accepts a config that removes an
unseen scoped recipient, leaving a frozen live delivery for an identity that
the instance no longer accepts. This is the R3 failure the plan explicitly
required the implementation to prevent.

Reproduced through public operations: publish to `acme.*`, offer generation 2
without `acme.implementer`, and call `regen_instance` as the config authority.
The current build accepts the regeneration.

Required:

- include every member of a still-deliverable notice audience in the regen
  removal gate;
- pin when expiry/GC makes removal lawful without rewriting retained history;
- test scoped removal refusal and later lawful removal;
- replace the current “frozen against a later participant” test with an
  actual additive generation-2 regen. The present test never adds a configured
  participant; it calls `see("nobody.here")`, which fails only because that
  identity is undeclared. It does not prove the ruled behavior change.
- after real additive regen, prove the newcomer cannot receive the old global
  or scoped notice and does receive a later applicable publication.

## R4 — `dump` omits the new protocol table; `doctor` has no audience checks

Severity: high for auditability, medium for the immediate delivery path.

`dump()` promises every protocol table but its table list omits
`notice_audience`. The immutable answer to “who received this?” is therefore
absent from the inspection surface. Reproduced directly: `notice_audience` is
not a key in `dump(instance)`.

The plan also required doctor/trigger invariants. Current `doctor` has no
notice-audience pass. Add and test checks for at least:

- every notice has a non-empty frozen audience;
- every seen receipt belongs to that audience (also enforce in schema);
- audience addresses and scoped selectors remain syntactically valid;
- audience rows have a surviving notice and cannot be changed independently;
- a publication fault after some audience work rolls the notice, every
  audience row and every part back atomically;
- expire and GC remove notice, receipts, audience and parts together.

Add `notice_audience` to `dump` and to any explicit table-set assertions.

## R5 — the new audience is not observable on delivery or in the TUI

Severity: medium; required before calling scoped notices complete.

The schema stores `audience_kind` and `selector`, but `see`, notice listing,
`_notice_delivery`, `open_sent_notice` and the TUI do not expose/render them.
README and mailbox documentation do not document `send-notice --scope`, and
there is no packaged CLI regression for it. A recipient therefore cannot tell
whether a notice was global or scoped even though the finding requires that
distinction.

R4 of the plan review required exact wire/API/output shapes to be settled
before code. Pin one canonical audience representation and carry it through
Store delivery/preview/history, the built CLI, dump and the TUI. Reviewer
recommendation: one `audience` object containing the immutable kind, optional
selector and canonical participant set; the TUI may render that compactly as
`everyone` or the selector. If the canonical set is intentionally omitted
from ordinary delivery, record why and identify the audit API that exposes it.

Add README examples with the wildcard quoted, plus built-artifact tests that
exercise `--scope 'acme.*'`, delivery to a member and refusal/non-delivery to a
non-member.

## Evidence run

The implementation's own focused group passes:

```text
./.venv/bin/python3 -m pytest -q test_core_conformance.py \
  -k 'ScopeSelectors or ScopedNoticeAudience'
28 passed, 434 deselected
```

Independent public-path probes all fail against the current candidate:

```text
./.venv/bin/python3 -m pytest -q /tmp/test_scoped_notice_review.py
4 failed

- non-member explicit open did not refuse;
- non-member unseen probe returned true;
- regen accepted removal of a live audience member;
- dump omitted notice_audience.
```

`git diff --check` is clean and the packaged CLI identifies itself as
`baton 6.0.0 (protocol 10)`. These do not change the review outcome.

## Accepted portions

- Whole-segment selector matching, including exclusion of
  `baton_extra.reviewer`, is correct.
- The deeper-address reading (`baton.*` includes `baton.a.b`) is accepted.
- Empty/malformed expansion refusal and deterministic sorting are correct.
- Global and scoped publication use one frozen-audience storage mechanism.
- Audience insertion and content publication occur under one commit/rollback
  transaction; add the requested injected-fault proof.
- Quoting wildcard CLI examples is the correct shell guidance.

Do not begin multi-recipient directed schema work while its publication-retry
ruling remains open. These scoped-notice corrections are independent of that
ruling and may proceed now.

## Re-review 1 — 2026-08-10

Outcome remains **changes requested**.

R1, R2, R3's removal gate and the dump omission now pass the independent
public-path probes. The first re-run briefly observed R3 before the edited file
was complete; a clean re-run after the handoff state settled passes all four
original probes. The composite receipt foreign key is the right defence in
depth.

The handoff nevertheless says all five items are closed while these remain:

### RR1 — sent scoped notices are mislabeled as global

`open_sent_notice` omits `audience_kind` and `selector`. The TUI renderer treats
missing fields as the legacy global shape, so an author opening a sent
`acme.*` notice sees `To: everyone (notice)`.

Independent public-path reproduction:

```text
sent = store.open_sent_notice(notice_id, "hq.lead")["sent_notice"]
sent["audience_kind"]
KeyError: 'audience_kind'
```

Carry the two fields through `open_sent_notice` and add core plus TUI rendering
regressions for authored scoped and global notices. The received-notice path is
correct.

### RR2 — required acceptance tripwires are still absent

The implementation has no regressions for:

- an actual additive generation-2 regen proving a newcomer cannot receive an
  old global/scoped notice but does receive a later publication;
- scoped notice already present before `wait`;
- scoped notice published while blocked, including degraded polling and the
  query-to-arm race;
- an unrelated participant staying out of the receipt/write path while the
  scoped member wakes;
- injected failure after notice/audience insertion proving notice, audience
  and parts all roll back;
- any of the five new doctor branches;
- TUI audience rendering.

The current test named “frozen against a later participant” still never edits
the config or runs regen; it only asks an undeclared identity to call `see`.
Replace it with the real generation transition. The independent additive-regen
probe passes current behavior, but that does not leave a maintained tripwire.

The packaged CLI test is useful and passes the built path, but it covers none
of the wait/race/fallback or authored-detail cases above.

### RR3 — doctor must use the protocol's exact validators

The new doctor pass calls `ADDRESS_RE.match` and `SCOPE_RE.match` directly. It
therefore omits the protocol's 64-character bounds; an overlong address or
selector that matches the regex is reported healthy. Use the same exact
address predicate as config validation and `validate_scope` (catching its
error), then break-test the boundary. Doctor is specifically the corruption
path, so “the normal writer cannot create it” is not sufficient.

### Re-review evidence

```text
./.venv/bin/python3 -m pytest -q /tmp/test_scoped_notice_review.py
5 passed, 1 failed

failure: sent scoped notice has no audience_kind

./.venv/bin/python3 -m pytest -q test_core_conformance.py \
  -k 'ScopeSelectors or ScopedNoticeAudience'
33 passed, 434 deselected

git diff --check
clean
```

## Re-review 2 — 2026-08-10

Outcome remains **changes requested**, narrowed to two corrections.

The six public core probes now pass; the expanded scoped core group reports
34 passed, the focused notice TUI group reports 8 passed, and diff check is
clean. R1–R4, additive regen, atomic rollback, doctor exact validators and the
received-notice audience display are accepted.

### RR4 — authored sent-notice rendering still drops the audience

`open_sent_notice` now correctly returns `audience_kind` and `selector`, but
the TUI branch for `sent_notice` calls `_sent_content_lines(..., notice=True)`
and `_sent_content_lines` never uses its `notice` parameter. The author sees
headers and content with no `To:` audience line. The two new TUI tests exercise
`audience_line` and received `_notice_lines`, not the authored sent-notice
branch that RR1 identified.

Independent reproduction:

```text
_sent_content_lines(scoped_envelope, 80, notice=True)
['  Sent', '', '  From:    hq.lead', '  Subject: team', '  Kind:    review', '']
```

Fix the sent-notice rendering branch and pin it through `_detail_lines` or the
state/open path for both scoped and global authored notices. A helper-only test
is insufficient because that is how the unused `notice=True` binding passed.

### RR5 — the scoped query-to-arm race is still not pinned

The new tests cover an already-present scoped notice, ordinary publish while
blocked, and degraded polling. None publishes from the deterministic
`wait:armed` fault seam between the first query and the post-arm requery. Add
the scoped equivalent of `test_notice_arm_race_closed_by_requery`, asserting
the member receives it despite a long rescan interval and an unrelated
participant does not acquire a receipt. This is an explicit acceptance item,
not inferred from the ordinary watch-wakeup test.

Current independent evidence:

```text
./.venv/bin/python3 -m pytest -q /tmp/test_scoped_notice_review.py
6 passed, 1 failed

failure: sent-notice renderer does not show the scoped audience
```

## Re-review 3 — final scoped-notice outcome

Outcome: **approved** for the scoped/global notice half of Stage 2.2.

RR4 is fixed through the sent-notice renderer, not only the core envelope.
RR5 now publishes from the deterministic `wait:armed` seam and proves the
post-arm requery wakes the scoped member without making the unrelated
participant eligible.

Final independent evidence:

```text
./.venv/bin/python3 -m pytest -q /tmp/test_scoped_notice_review.py
7 passed

./.venv/bin/python3 -m pytest -q test_core_conformance.py \
  -k 'ScopeSelectors or ScopedNoticeAudience or ScopedNoticeWakeup or ScopedNoticeAtomicity or NoticeAudienceDoctor'
39 passed, 441 deselected

./.venv/bin/python3 -m pytest -q test_tui_render.py -k 'audience or notice'
9 passed, 263 deselected

just test
2130 passed in 179.76s

git diff --check
clean
```

Built artifacts and manifests agree:

```text
bin/baton
9736b18daefde9f64c6793d041afb53219c0113c5ff2200b643627af464f701b

bin/baton-tui
5b68c4d26202cbe8e7cc1768591a76b59b86d57bac68618e9313ac6cbaf4c489

baton_core/_impl.py
1f55db6223fa38e3e2546c47d568c59e7d20d8b522ccbbab2684cc40a835165f

AGENTS-MAILBOX-PROTO.md
5e300d76649d0a9d144a522e1ec39c937be138e8a0c2631550ff5544c3637323
```

Versions report `baton 6.0.0 (protocol 10)` and `baton-tui 0.2.0`.

This approval does not cover multi-recipient directed publication. Its retry
ruling is now closed: protocol 10 remains at-least-once with an immutable,
sender-supplied possible-duplicate warning. Its
`publications`/`publication_audience` schema remains unwritten and unreviewed.
