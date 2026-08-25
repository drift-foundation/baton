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
