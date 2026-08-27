# Implementer progress — the constrained OCI adapter core

Created 2026-08-24 by `baton.claude` on claiming W6632, as the record requires.

## Delivered

`v12/python/src/baton_v12/worker_manager/oci.py` with
`tests/manager/test_oci.py` — **33 methods, all passing**.

It implements the `start`/`list`/`stop` seam `attempts.py` **already calls**,
rather than a shape invented for this cut. That was revalidated against the tree
first: `adapter.start({"labels", "operation_id"})`, `adapter.list({"labels"})`
and `adapter.stop({"runtime_id", "operation_id"})`, with `documents.RUNTIME_LABELS`
as the label contract.

**No shell, ever.** Every invocation is a closed argument vector, so there is
nothing for an image name, a label value or a mount path to escape out of —
the class of defect this module *cannot have* rather than one it guards against.
Golden vectors for both engines: 41 arguments, restrictions first, labels in the
contract's own member order, image last and by digest.

**The restrictions are unconditional** — one table a reviewer can diff: every
capability dropped, no new privileges, no nested runtime, a fixed non-root user,
read-only root, no network, pid/memory/cpu ceilings, and small non-executable
tmpfs. A policy a caller can turn off is a default.

**Absence is proved, not inferred.** An empty listing, a stop acknowledgement
and engine prose are three different things and none of them is death. Only an
engine asked about *that exact identity* and answering that it does not exist
produces `absent`; a record with no state, a state that is not a record,
`Running` as prose, two runtimes for one identity and unparseable output are all
`uncertain`. A manager that treated confusion as death would release an
assignment whose worker is still running.

**Nothing infers authority from engine state.** A duplicate start fails closed
*before* anything is created — asked and refused with the engine's run vector
never reached, which the test asserts by counting vectors. An ambiguous
multi-match listing is returned **whole** for the manager to judge, because
`attempts.py` already refuses on it and an adapter that picked one would be
deciding authority.

**Runtime-neutral, one vocabulary.** Docker's label record and Podman's
comma-joined string both read into the frozen member set; a label set that is
not exactly that set refuses rather than being padded out. The `generation`
label comes back as the number it was, because `1` and `"1"` are one fact spelled
two ways and a comparison calling them different would report every
reconciliation as a mismatch.

**Labels carry no secret** — exactly the frozen `runtime.labels` document, which
is identities and digests. A caller-supplied label is refused, since a label is
readable by anything that can list containers.

Engine prose reaching a diagnostic is bounded at 240 characters, the W1593 rule.

## A defect my own tests caught

The image check was `startswith("sha256:")` plus a length, which accepts
**upper-case** hex. Two spellings of one image would be two images to every
comparison downstream. It is now the frozen digest pattern.

## Not finished, and it is the same gap as W6631

The receiving-boundary inventory. Two literal-label corrections are in (a shared
helper carrying its caller's word is a boundary the inventory cannot attribute —
the third time this campaign has taught me that), and what remains is the
declaration table: `DELEGATED` entries pointing each caller operand at
`_engine`, `_labels`, `_mounts` and `EnginePort`, and one probe per resulting
`(entry, label)`.

**This is now the same unfinished pass in two Works.** W6631's review requires
its inventory green there; W6632 adds more entries of exactly the same shape. I
think that argues for doing the declaration work as one deliberate pass rather
than twice in two claims, and I am flagging it rather than deciding it — the
reviewer may prefer them kept separate for independent review, which is a fair
call I should not make unilaterally.

## The gate

Focused: `test_oci` 33 pass; `test_dependencies` and `test_text_sweep` pass with
this cut's operands declared. `test_boundary_inventory` is red for the reason
above, and the full gate is additionally red from W6592's separately-tracked
changes-requested review. None of that is reported as anything else.

## What is deliberately absent

Source materialization, provider code, output acceptance, credential delivery
and manager lifecycle orchestration — the assignment excludes each. The
**isolated mutable engine smoke test** is not here either: the acceptance names
it separately, and it is a test of somebody else's daemon that must leave its own
resources absent. It is the natural next cut.

## State

**Awaiting independent review.**

## Review corrections — 2026-08-24

**Items 1–4 are done and the six additive reviewer cases are green.**
`test_oci` is 39, with `test_dependencies` and `test_text_sweep` beside it — 63
passing.

**Item 1 — the container name.** I interpolated the manager's operation
identity directly, producing `baton-runtime.start:<digest>` — a name **no
engine accepts**, so every start would have failed at the daemon. It is now a
*derivation*: the forbidden characters are substituted, totally rather than
stripped, so two identities differing only in characters an engine forbids
cannot collapse to one name. The manager's `runtime.start:<digest>` is
untouched — weakening it would let the engine's alphabet decide what an
operation is.

**Item 2 — positive absence.** Two defects, and the first is the dangerous one.
Matching `no such` or `not found` *anywhere* in stderr meant unrelated prose —
a missing network, an absent volume — read as this runtime being dead, which is
the one mistake that releases an assignment whose worker is still running.
Absence now requires the engine's own pinned sentences **and** the runtime id in
the text. Separately, a successful inspection had its `State` read from whatever
document came back: it must now **name the runtime asked about**, and an
inspection naming another id or none is `uncertain`.

**Item 3 — labels.** An extra `baton.v12.*` label was silently ignored, so
anything that could write one could attach `baton.v12.bearer` to a runtime this
manager then reconciled on without ever seeing it. The namespace is this
manager's, so an unknown member of it refuses. And each label now returns in the
type its **rule** gives it, on the way out as well as back: a digest label
reading `profile-latest` and a generation of `-1` were both accepted and
compared before.

**Item 4 — mount spellings, partly.** Sources and targets are canonicalized, so
`/srv//source/./` reaches the engine as `/srv/source`. The **allowed-roots
replacement for the denylist is not done** — see below.

## Not done

- **Item 4's second half.** The host-path denylist is still a denylist. The
  review is right that proof against assignment-owned, posture-specific allowed
  roots is the stronger contract — a denylist answers "is this one of the bad
  ones" when the rule is "is this one of ours". It needs the assignment's own
  roots threaded into the adapter, which is a design change rather than an edit.
- **Item 5's remainder** — the receiving inventory and probes, and the isolated
  Docker smoke with positive cleanup plus Podman.
- **Item 6** — focused, dependency and sweep gates are green; the inventory,
  isolated-engine, full source and locked gates were not run to completion.
## The assignment-root ruling, applied — 2026-08-25

THE RULING IS APPLIED, and it went further than my proposal in a way I had missed: I asked whether assignment_roots should be required and left the POSTURE implicit. You are right that roots alone cannot choose the topology, so both are required inputs now.

The denylist is GONE ENTIRELY. A source is admitted only because this manager created the root it lives under — proved to be OURS rather than proved not to be theirs, which is what makes a repository path refused for the right reason instead of because somebody remembered to list its prefix.

The topology is enforced where the mounts are built: CONSENT MOUNTS NOTHING, and one that could see the inputs would be the promotion the two-container topology exists to prevent. Execution may mount inputs or a descendant READ-ONLY and workspace or a descendant read/write. The private metadata root is never mountable at either posture, because a worker that could reach it could move another assignment's refs. Containment compares segments, so /srv/a-1/inputs-2 is not inside /srv/a-1/inputs.

Every public call site and golden vector moved with it, and five cases were added: ownership refusal for a repository, another assignment's roots, a prefix-sharing root, host state and the engine socket; the metadata root; inputs as evidence rather than scratch; consent mounting nothing while still starting; and both new inputs being required and closed.

tests.manager.test_oci — 45, all pass, including your test_a_repository_outside_assignment_owned_roots_is_not_mountable.

STILL OPEN from the correction plan, and I am not restating the smoke-test claim you already overruled: this module's receiving inventory and probes, and the isolated Docker positive-cleanup smoke plus compatible Podman coverage. Your record is explicit that the test module's note about smoke belonging to a separate cut does not supersede this dossier's acceptance, and I accept that.

## Assignment-root re-review correction — 2026-08-25

**Lexical containment is not mount authority.** `os.path.normpath` is a string
operation, so a symlink planted under the writable workspace passed the test
and the engine — the party that actually resolves the path — followed it out of
the assignment. `_canonical` resolves as the kernel would, and it is applied to
BOTH sides: resolving only the source would refuse every legitimate mount under
a symlinked root. The resolved source is what reaches argv, because proving one
path and emitting another leaves the engine free to resolve it again.

**Ambiguity is refused rather than resolved by iteration order.** A root inside
another gives a source two postures and lets whichever matched first decide
whether it may be written. Nested targets shadow; nested sources alias. Equality
is the degenerate case of both and is refused by the same rule.

**One delivery carries one identity.** The adapter held an image digest while
`start` took labels independently — two accounts nothing compared, and
reconciliation after a restart reads the labels and reasons about the image
from them. `RESOLVED_IDENTITY` is one record owned at construction: the argv
names its image, the labels must agree with it, and a mismatch is refused
before the engine is asked to create anything.

**The inventory is complete for this module**, measured rather than asserted:
zero `oci.py` mentions in the probe gate and none in the unowned list. Finding
that required giving `_canonical` a literal label — a computed one is a
boundary the inventory cannot attribute, which is the third time this
distribution has been corrected for the same thing.

**Real engine evidence exists.** The adapter now runs against a real daemon
through its own `EnginePort`, with the applied restrictions read back from the
engine's record rather than from the argv this suite chose. Skipped per engine
when one is absent — the policy this dossier requires — and a case keeps the
covered engines and `ENGINES` the same list.

## Verification

`evidence/gate-after-correction-2026-08-25.txt`. `test_oci` 56/56;
`test_oci_engine` 12 with the five Podman cases skipped and Docker green. The
pre-existing twelve are now seven, all of them other modules', and nothing was
added.

One interaction is reported and NOT explained: two of W6633's container cases
pass alone, pass beside this module's engine gate, pass in the locked build,
and fail in a full source run. The measurement is in the evidence file rather
than a guess in this one.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.

## Fifth review correction — 2026-08-25

All three items from `review-2026-08-25T15-07-37Z.md` are corrected and its
five additive methods are green. Two of the three needed a decision rather
than an edit, and both are recorded rather than assumed.

**[P0] The absence sentence has to be the thing that names the runtime.** The
previous version asked two separate questions of one diagnostic — is there an
absence phrase anywhere, and is the requested identity anywhere — and answered
"absent" when both were true. The review's

    Error: No such container: runtime-2; request was for runtime-1

is the whole finding: two fragments are not an association, and this is the one
branch that releases an assignment whose worker may still be running. Each
engine's own complete form is now a pattern that CAPTURES the identity, and
only a captured identity equal to the one asked about is absence. Per engine
rather than pooled — a docker adapter reading podman's phrasing would be taking
evidence from a daemon it is not talking to.

**[P1] Four digests, and the two halves survive the restart by different
routes.** The review is right that a green case named
`..._three_digests_and_nothing_else` is how a narrowing of a confirmed contract
stops looking like one. It counts four now and asserts the member tuple itself,
so the next change to it has to come through that case.

- **The image is the ENGINE'S fact.** Read from the listing rather than from a
  label, because a label is what this manager wrote about a delivery and the
  engine's record is what is actually running — and those are only the same
  while nobody has replaced anything, which is what reconciliation exists for.
  Measured against a real Docker 29.1.3 daemon rather than assumed: `ps
  --no-trunc --format {{json .}}` answers `Image` as the `sha256:` reference,
  because this adapter always starts by digest. Podman answers `ImageID` too
  and it is asked for first. A listing naming no image, or naming a tag, is
  refused: a tag is a pointer that was true when somebody last pushed.
- **The policy has no engine fact, so it is a label.** `runtime.labels` gains
  `policy_digest`. This is the second time this build has extended those labels
  past the frozen host's set and it is the same argument that added
  `participant`: reconciliation decides by comparing labels, so a member of the
  resolved identity the engine cannot report does not survive a restart at all.

**[P1] The cleanup proof selected nothing this module creates.** MARK is a
LABEL and never a name — every runtime name is derived from
`runtime.start:<digest>` — so `--filter name=baton-w6632-engine` matched none
of them and reported empty whatever survived. It queries the label namespace
the runtimes actually carry now, and requires the query to have SUCCEEDED
before reading its result as absence. `remove_everything` surfaces failure too:
a refused `rm` is not by itself a failure, because a name is registered the
instant it can exist, but a container still present afterwards is — and that is
a question for the engine rather than for its prose.

## One thing this correction REACHED rather than owns

`attempts.policy_digest` is nullable, so making it a runtime label means an
attempt recorded without one can no longer start a runtime. That is the right
answer — a delivery whose policy this manager cannot name is one no later
reconciliation can describe — but *when `request_runtime_start` refuses* is a
lifecycle rule belonging to W5/W6636, not to this adapter core.

It is implemented here because the label member is useless without it, and it
is refused explicitly in `_runtime_labels`, with a message naming the missing
policy digest rather than surfacing as a digest complaint about `None` two
layers down. **Flagged for the reviewer to confirm or reroute.** I am not
treating my own reach as a ruling.

## The fixtures that moved, named because they are other cuts'

Five test modules built runtime labels or recorded an attempt without a policy
digest: `test_attempts`, `test_sessions`, `test_boundary_inventory`, `test_oci`
and `test_oci_engine`. Each records one now. **No assertion is weakened** —
what changed is that their fixtures satisfy an extended contract. Two existing
assertions did move and both are strengthenings the contract forced: the golden
argv length is 43 rather than 41 because there are eight labels, and the
identity-count case now asserts four members and their names.

The cost was not free and the number is worth recording: at one point the label
change had `test_boundary_inventory` failing **593** times, all from a handful
of shared fixture helpers that start a runtime. It is back to seven.

## The OCI inventory, measured again

Zero unowned, zero unprobed, zero probed-never-owned for `oci.py`. One probe
was added, and finding it was the audit's own work: `OciAdapter.__init__ /
identity` was owned under two labels — the document envelope and each digest
inside it — and only the envelope was probed. It is driven with the EMPTY
STRING rather than the surrogate, because `own` walks the envelope for
encodability first and a surrogate would prove the envelope's rule instead.

`_image_identity` takes a LITERAL label at its owner. That is the fourth time
this distribution has been corrected for a computed one, so the reason is a
comment at the site rather than something to learn again.

## Verification

`evidence/gate-after-fifth-correction-2026-08-25.txt`.

- `test_oci` **64** (59 + five of mine), `test_oci_engine` **14** with Docker
  29.1.3 green and the five podman cases skipped, `test_attempts` **52**.
- Adjacent twelve modules: **522, OK**.
- `test_boundary_inventory`: the same **seven** pre-existing failures, naming
  four sites this correction does not touch.
- Full source suite **1189, nine failures**; locked installed-layout build
  **1189, the same nine**. Seven are the boundary inventory's, one is W6633's
  image gate, and one is reported below. **The five OCI failures the review
  reported are gone and nothing was added.**

## Reported and not fixed

`tests.manager.test_secrets.TheRefusalConstructorIsTheOneCrossing.
test_the_substitute_cannot_quote_a_live_bearer_substring` — a reviewer
regression added to **W6630** after this participant passed that Work back, and
it is a real defect in that correction: §13's substitute message is exempted
from the containment guard as a whole, so a live bearer that is a 32-character
SUBSTRING of this build's constant prose leaves inside the replacement. W6630
is routed to `baton.feat` and is not held by this claim, so fixing it here
would be executing Work nobody claimed. Reported on that thread and here.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.


## Sixth review correction — 2026-08-26

Both findings are corrected, and the [P0] is the one worth reading.

**Discovery has to be broader than comparison, and asking the engine both
questions was the defect.** `list_vector` filtered on all eight labels,
including the three resolved-identity digests — and a real engine applies every
filter before it returns a row. So a runtime from THIS attempt under an old
policy never appeared in stdout, never reached the comparison that would have
refused it, and `start` read the empty candidate set as "nothing exists" and
created a second runtime for one attempt.

This module's own docstring has said the opposite from the beginning: "a stale
identity is refused rather than filtered away, because it is not absent, it is
WRONG, and dropping it leaves a mislabelled runtime running." That was true of
everything except the query that finds the runtime. The fake engine could not
show it, because a fake that ignores the filters it was handed is a fake that
agrees with whatever the adapter believes.

The engine answers which runtimes belong to this ATTEMPT; the adapter decides
in process whether each is this delivery's. `_CANDIDATE_LABELS` is DERIVED from
the frozen label set minus the resolved identity, so a label added tomorrow
becomes a selector or a comparison by which list it belongs to rather than by
somebody remembering this site.

**Narrowing the filters did not narrow the ownership.** The whole label set is
still owned before the engine is asked anything, so an invented member, a
missing member or a text-shaped digest still refuses before a query exists.
Only which of those proved values become filters changed, and a case pins it.

**The target's spelling is checked before `normpath` can erase it** — the rule
`_canonical` already followed for a host source and that this side was missing.
`/workspace/../etc` was accepted and emitted as `target=/etc`, moving the
assignment's writable bind over the image filesystem.

## One existing assertion revised, under explicit confirmation

`test_the_listing_filters_on_every_label` required a filter for EVERY label,
which is the defect stated as an expectation. The review gives explicit
case-specific confirmation to revise it; it now asserts the candidate selector
in the contract's own order and asserts each identity digest is NOT among the
filters — a digest used as a filter is a runtime the engine hides rather than
one this adapter refuses.

## Verification

`evidence/gate-after-sixth-correction-2026-08-25.txt`.

- `test_oci` **70/70** (66 before): the review's two kept as written, one
  revised one-for-one, four new — ownership before the query, a stale
  candidate refused for each of the three digests, a stale candidate stopping
  a start before any create, and an ordinary start still creating.
- **Measured to fail without the corrections**: reverting both gives three
  failures, restored byte for byte.
- **Against a real daemon**, because the defect was about what a real engine
  does: `test_oci_engine` 14 green on docker 29.1.3, including the
  duplicate-start refusal that drives the candidate query.
- Adjacent **564 OK**. Source suite and locked build both **1228, eleven
  failures**, and `test_oci` is not among them.

## Reported and not fixed

- **W6630**, `test_secrets.…test_the_pair_assertions_cannot_quote_a_live_bearer`
  (two subcases) — a seventh-review regression posted minutes after this
  participant passed W6630 back, and a real defect in that correction: the
  constructor's category and code assertions run BEFORE the §13 message guard
  and interpolate the rejected operand with `repr`, so a live bearer supplied
  as an invalid category or code escapes in an `AssertionError` the crossing
  never sees. Reported on T6630 with the direction I would take.
- **W6633**, the two `tests.tools.test_worker_image_build` regressions,
  already reported on their own thread.

The remaining seven are the long-standing boundary-inventory failures.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.


## Seventh review correction — 2026-08-26

The review is about my own previous correction, and it is right. I moved the
three resolved digests out of the engine filters and STOPPED THERE — leaving
the attempt id, the four parts of the assignment and the generation as exact
filters — so I fixed one instance of the defect and left the same defect, in
the same boundary, one field over. A runtime carrying this attempt id under
generation 0 while the request says 1 is still hidden, `start` reads absence,
and it reaches `run`.

The post-read half was incomplete the same way: `list` parsed the whole label
record and compared only the engine image and the three digests, never the
assignment values it had asked for. **Engine-side selection is not proof that a
returned record has the values requested** — which is my own correction's
sentence, and I had not applied it to the half I had just written.

**The general rule is what was missing.** Any assignment fact used as a filter
hides a runtime that contradicts it, and a contradictory runtime is exactly
what this adapter exists to refuse. It was never about digests specifically.

So the selector is the minimal ownership key — `runtime_attempt_id` alone, the
one label that answers "is this runtime this attempt's" and cannot disagree
without meaning a different attempt — and the complete returned record is
compared in process, member by member across the whole frozen label set.

**Two comparisons, two questions.** The new loop asks whether a candidate is
the runtime the CALLER named; the existing one asks whether it is the one THIS
ADAPTER resolved. `list` is reachable without `start`, so neither implies the
other.

## The selector assertion, revised a second time

It required the attempt AND the four assignment parts — the first correction's
incomplete rule written down as an expectation. Under the review's explicit
confirmation it now requires exactly one filter and asserts that EVERY other
member of the frozen set is absent, not just the three digests.

## A pair of gate numbers that did not describe one tree

Recorded rather than tidied. The source run finished at 1241 tests with 9
failures and the locked build that followed reported 1244 with 13 failures and
2 errors. That is not an installed-layout difference: a reviewer added three
cases to `test_secrets.py` under W6630 while the build was running. **A pair of
gate numbers taken across a moving tree is two measurements of two things**, so
both were re-taken and now agree at 1244 — the same discipline the W10265
harness needed, applied to my own evidence.

## Verification

`evidence/gate-after-seventh-correction-2026-08-26.txt`.

- `test_oci` **74/74** (70 before), with the review's two kept as written and
  two added; **both halves measured to fail** without them, restored byte for
  byte.
- `test_oci_engine` **14** green against docker 29.1.3 — the defect is about
  what a real daemon does with a filter, so the duplicate-start refusal
  driving the candidate query against a real one matters here.
- Adjacent **486 OK**. Source suite and locked build both **1244, fifteen
  failures**, and `test_oci` is not among them.

## Reported and not fixed

- **W6630**, three new `test_secrets` cases from its eighth review, posted
  mid-correction. All three are real defects in that Work's last correction —
  mine — and the review is right that the decision I recorded there is not
  established: membership hashes a rejected operand before the safe renderer
  runs, the redaction sentence and type name it composes are themselves
  unproved against the live snapshot, and two later type assertions still use
  `type(value).__name__` instead of the metaclass-safe helper this module
  already owns.
- **W6633**, the two `tests.tools.test_worker_image_build` cases already
  reported on T6633.

Both are routed to `baton.feat`. The remaining seven are the long-standing
boundary-inventory failures.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.
