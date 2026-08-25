# Implementer progress — output freeze and sealed artifact receiver

Created 2026-08-24 by `baton.claude` on claiming W6628.

## First claim, 2026-08-24: dossier and revalidation, no implementation

The dossier was created and the frozen output contracts revalidated against the
current tree. Two things the contract already decides — and which an
implementer could easily re-decide wrongly — are in `FINDING.md`:
`missing-optional` is a reported STATUS rather than an absence, and `frozen`
and `sealed` are distinct states with `invalid` reachable from `frozen`, so
freezing is not accepting.

Nothing was implemented: `W6628 → W6592` was installed as the handoff required,
and W6592 was open with changes requested. A receiver built against a guess at
where that public seam would land is the unindexed second boundary the
dependency exists to prevent.

## Second claim, 2026-08-25: the implementation

W6592 closed satisfying, so the seam is the accepted one.

**`schema.py` — three tables, and the store version moved with them (7 → 8).**
`manifests` keyed by the digest that identifies a document; `outputs` keyed by
the ATTEMPT, because an attempt freezes once and a table that could hold two
would make "which of these is this attempt's result" unanswerable;
`output_artifacts` as the indexed half of a record that lives whole in the
retained manifest.

**`manifests.py` — a digest is not a record.** Before this the store held
`attempts.input_digest` and not one byte of the document it names, so a freeze
could not compare a sealed result against the OUTPUT DECLARATIONS that document
carries — it had never seen them. The key being the digest makes retention
idempotent by construction and stops a stored body from drifting from its key.
`load_manifest` requires the definition it must be rather than defaulting it:
a retained RESULT manifest is a perfectly valid thing to hold, and naming one
as an attempt's input digest would let its similarly shaped output rows be read
as trusted declarations. Being at the named key is not being the named thing.

**`output.py` — the freeze and the receiver.** The four preconditions are read
from durable state and not one is a claim the caller supplied about itself:
the fixed four-part assignment, the session's binding, a terminal
`worker_disposition` that EQUALS the declared one, and a positive `quiescent`
observation. `uncertain` is a failure to look and `destroyed` is a writer that
was never observed to have finished, so neither is quiescence. The liveness
read is inside the write and is still only a read, which the module says out
loud rather than implying.

The receiver validates the sealed observation through the contracts composite,
then adds the half a validator cannot know: that the document belongs to THIS
attempt. The assignment, the input and policy digests, the disposition, the
freeze operation id AND its signature are all compared. Then the declarations
are compared BOTH WAYS — every result output must be declared, and every
declaration must be answered, because a declaration silently dropped is a
question the result pretends was never asked.

**The record identity is the ACT, not the bytes.** `output.record:` is derived
from the attempt and its assignment, so the same result replays and changed
bytes under that identity refuse. If the identity varied with the bytes, two
different results would be two different operations and both would commit,
which is the opposite of what an immutable record means.

**Replay asks nothing about today.** The frozen host was corrected for this
twice — once for consulting the output axis ahead of the journal, once for
leaving the declaration lookup ahead of it. A case drives both: after freezing,
the axis is moved to `invalid` and the retained declaration is deleted, and an
exact retry still reproduces the first answer.

## What the acceptance asked for, and where each line is

- *Quiescence proved before freeze, `freeze-requested` and `frozen` distinct* —
  `QuiescenceIsProvedBeforeFreeze` drives all four non-quiescent values;
  `FreezingIsNotAccepting` shows a failed seal leaving the axis at
  `freeze-requested`, which is a real durable state rather than a pretence
  that the freeze never happened.
- *The manifest, count, bytes and digest recomputed rather than adopted* — the
  contracts composite recomputes §12 rule 6's aggregates and tree digest, and
  the stored `manifest_digest` is the recomputation rather than the member the
  document filled in about itself. A case asserts that equality directly.
- *Immutable staging identity, so a retry names the same material* — the fixed
  record operation above.
- *Effectively-once acceptance through W4's journal* — `store.transact` and
  `store.replay`; no second journal was added.
- *Caller-local refusals; engine and adapter status carry no authority
  meaning* — the adapter is asked for a seal and its ANSWER is validated; a
  witness case drives an adapter that reports success and answers with
  something that is not a result, and the axis stays where the durable state
  honestly is.
- *`missing-optional` recorded as the answer it is* —
  `MissingOptionalIsAnAnswer`: it is reported in the frozen answer, it carries
  no artifact row, and it is preserved whole in the retained document.

## Verification

`tests/manager/test_output.py` — **55 cases, all passing.**

The gates a new manager module always costs, extended rather than exempted:
the boundary inventory's ownership, probe and witness tables (39 new probes, 3
stated owners with 2 witness cases), the text sweep's table (6 new callables
and 3 new constants), and the declared-operand list.

    cd v12/python && just build
    # Ran 903 tests -- FAILED (failures=12, skipped=1)

## The gate is red, and the list is byte-identical to before this claim

Twelve failures, all pre-existing, every one naming `oci.py` or
`workspaces.py` — W6632's and W6631's. Fifty-seven cases were added and not one
failure was. `evidence/gate-after-2026-08-25.txt` diffs clean against the same
list filed in W6627's dossier.

## Operational finding — the boundary inventory resolves private helpers by NAME

**Observed 2026-08-25.** `tests/manager/test_boundary_inventory.py` keys its
functions by LEXICAL SITE, and its own header says why: an inventory that
cannot tell `AuthorityPort.claim` from a module-level `claim` silently merges
them. But `_returned_origins` — the fixpoint that resolves what a private
helper HANDS BACK — is keyed by the helper's NAME alone, across the whole
package.

So two modules with a private helper of the same name collapse into one entry,
and one of them becomes invisible to the inventory. I hit it directly: naming
this module's attempt reader `_attempt`, as `sessions.py` already does, made
two of W6627's adopted column entries stop being wanted — a green-looking
narrowing of the universe caused by a name.

**Avoided rather than worked around:** this module's reader is `_attempt_of`,
and the reason is written at the site. **Not fixed here:** correcting
`_returned_origins` changes how every module's entries are derived and is a
change to a shared gate, which is not this Job's to make under this claim. It
is the same name-collapsing defect the file's header describes for functions,
surviving one level down in its origin resolution, and it deserves its own
Work.

## One edit outside this Work, named because it is one

`tests/manager/test_sessions.py` (W6627's, currently in review) asserted
`SCHEMA_VERSION == 7`. This slice moves it to 8, so that literal had to change.
It is now `assertGreater(..., 6)` with the reasoning at the site: the property
that case owns is that a store written before the agent session existed cannot
be adopted, and which number the CURRENT shape is at is the newest slice's fact
— `test_store` already pins that the store records this constant. W6628's own
case is `assertGreater(..., 7)` for the same reason. **W6627's reviewer should
see this**, since it edits a case they are reviewing.

## Not done, and named rather than rounded up

- **The `sealed` transition.** The axis has `frozen → sealed` and this module
  never writes it. `invalid` is reachable from `frozen`, so material can be
  frozen and then found invalid; sealing is W6634's, and collapsing the two
  here would have removed the state that expresses it.
- **Filesystem and OCI collection, credentials, retention and cleanup.** Not
  in the brief and not in the acceptance.
- **The 12 pre-existing failures.** Untouched.

## Review correction — 2026-08-25

**[P1] Quiescence was decided outside the freeze transaction.** The runtime and
disposition preconditions were proved from an attempt row adopted BEFORE
`transact` took the write lock, and nothing re-read them inside. A newer
`uncertain` or `destroyed` observation committing in that window left the
transaction recording `freeze-requested` from a stale `quiescent` row — the
output axis claiming a freeze was requested after the durable evidence had
stopped proving the writer stopped.

I wrote in that module's own header that the liveness read is inside the write
"and is still only a read", and then left the two axis reads outside it
entirely. The reviewer is right that the check outside cannot authorize the
write.

**The decisive check is now a row re-read inside the `output.freeze`
transaction**, before the output transition. The outside check remains and is
now what it always was: an optimistic early refusal that answers the ordinary
case without taking a write lock. Both call ONE helper, because two spellings
of one rule is how the outer and inner answers come to differ.

**Measured, and recorded rather than assumed:** only the quiescence half can
move in that window. `worker_disposition` is terminal-once — every disposition
beyond `none` has an empty successor set — so a disposition proved terminal and
equal outside is still both inside, and that half of the helper is inert under
the lock. It is kept because factoring the pair is what stops the quiescence
rule from being written twice, and a case pins the transition map it relies on:
if that axis ever stops being terminal-once, the gate says so.

**Two regressions beside the reviewer's**: that a plainly unready attempt never
reaches the journal at all (the split is real, not decorative), and the
terminal-once reliance above.

    cd v12/python && PYTHONPATH=src python3 -m unittest tests.manager.test_output
    # Ran 58 tests -- OK

    just build   # Ran 947 tests -- FAILED (failures=14, skipped=1)

**Fourteen, and none of them is this Work's.** Twelve are the pre-existing
`oci.py` and `workspaces.py` failures. The other two are the reviewer's
additive cases on **W6630**, which landed in the tree while this correction was
being made: `test_a_live_bearer_never_becomes_a_manager_signature` and
`test_a_portable_refusal_cannot_carry_an_interpolated_bearer`. W6630 is a
separate Work, queued at `baton.impl` and not held by this claim; I am taking
it next.

## State

**Awaiting final review.**
