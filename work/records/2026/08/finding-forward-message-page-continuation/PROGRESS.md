# Progress — forward Message pages advertise an unproved continuation

Owned exclusively by the implementer (`baton.claude` under v11).

## Step 1 — W130 implemented (2026-08-17)

Claimed W130. This is the defect I reported from the W76 review and
deliberately did not fix there, because the review scoped me to the
reverse direction and said to preserve the forward contract. It is now
its own Work, which is the right shape: it is a pre-existing canonical
JSON defect, not part of the W76 newest-first contract.

Reproduced before changing anything, against projection 6.2: five
messages, `after=0 limit=5` returns all five with `next_after=6`, and
following that cursor yields `[]`.

### The correction

The forward branch of `projection.thread` now reads at most `limit + 1`,
keeps the first `limit` in ascending order, and sets `next_after` only
when the extra PROOF row shows another page exists — the same rule the
reverse branch already had. `after` exclusivity, ordering, references,
personal-new computation, `last_seq` and snapshot handling are all
untouched, and the reverse direction is unchanged.

The two directions now share one honest rule instead of one honest rule
and one hopeful one.

### Evidence

New `tests/work/test_w130_forward_continuation.py` (12): the reported
boundary; fewer-than-limit; limit-plus-one chaining to a final page that
closes the chain; a parametrised walk over five shapes — including two
exact multiples and a single-message thread — asserting every advertised
cursor opens a NON-EMPTY page and that traversal is complete, ordered
and duplicate-free; cursor exclusivity and retry stability against an
unchanged snapshot; the proof row never reaching the payload; the
reverse direction unchanged; and the surrounding thread facts
(`last_seq`, `new`, `snapshot_seq`, `local_id`) untouched.

Break-sweep: restoring the length-equals-limit rule reds 4.

### The workflow proof, extended as the finding directs

`tests/work/workflows/test_ws4_wf01.py` gained an exact-multiple case
(six messages in pages of two, ending on a FULL page that must still
close the chain, plus a retry-stability check), and — more usefully —
its shared `_walk` helper now asserts that every page it is sent to is
non-empty and within its own limit.

That second change is the one that matters. The old walker counted rows
and pages, so a collection that ended by handing out a cursor to an
empty page still looked correct: the final empty page simply added zero
rows and terminated the loop. The walker is shared by the
`work-threads`, `threads` and `thread` traversals, so the assertion now
holds all three to the promise, in both the source and packaged JSON
lanes.
