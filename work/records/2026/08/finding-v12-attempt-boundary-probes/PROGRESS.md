# Implementer progress — adopted-attempt boundary probes

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-29 — derived, and the family is larger than the finding said

Claimed W35557 at seq 36164. **No production code was changed.** No Git
history or index was mutated.

### PLAN 1 — enumerated, and the enumeration found more than four

`evidence/w35557-before-2026-08-29.txt` is the full before-state. The four
omissions the finding names are there:

    attempts.py:_attempts  attempts.assignment_principal
    attempts.py:_attempts  attempts.assignment_scope
    attempts.py:_attempts  attempts.input_digest
    attempts.py:_attempts  attempts.runtime_attempt_id

And so is the same family's other half, which the finding does not mention and
which the derivation had to account for: **seven STALE probes** declared for
`output.py:_attempt_of` — probed, never owned. Three modules read this one
table through `boundaries.row(..., ATTEMPT_COLUMNS)`, and each was covered
differently: two by hand-written column lists and the third not at all. One of
those lists had drifted out of date in the other direction.

### PLAN 2 — one derivation for every site that adopts the row

`attempt_probes()` derives from `schema.ATTEMPT_COLUMNS` for each of
`attempts.py:_attempts`, `intake.py:_attempt_of` and `output.py:_attempt_of`,
skipping only what `NO_PROBE` and `owned_by_sqlite` already exclude, and each
site is driven through its own module's public operation -- driving somebody
else's would prove somebody else's owner. Both hand-written lists are gone.

**The exclusion reads `NO_PROBE` rather than keeping a second list.** The
acceptance asks for exclusions that are "explicit, justified, and checked as
live owned entries", and `NO_PROBE` plus
`test_every_unprobed_entry_is_a_real_owned_entry` is exactly that mechanism,
already there and already carrying the identical exemption for `outputs` and
`intakes`. A second list would be an exemption that can be lifted in one place
and not the other.

**`runtime_attempt_id` is the one exclusion**, because every site selects
`WHERE runtime_attempt_id = ?`: a spoiled value is not a malformed row this
build adopts, it is a row the query does not return, and the caller receives
"no runtime attempt" -- a different boundary answering a different question.

### The guard caught me over-declaring, which is the point of it

I first declared that exemption at all three sites. Two of them named nothing:
the inventory attributes this column's crossing to `attempts.py:_attempts`
alone. `test_every_unprobed_entry_is_a_real_owned_entry` failed on both,
which is precisely what it exists for -- "no probe" must not become a way to
retire an entry by declaring it. One entry now, not three.

### PLAN 3 — every generated probe ARRIVES

`test_every_declared_probe_reaches_its_named_boundary` passes over the whole
declared set: every derived attempt probe reaches `a persisted attempt` rather
than an earlier refusal.

### The measured result

`evidence/w35557-after-2026-08-29.txt`. Missing 28 -> 24, stale 9 -> 2, and the
diff is exactly the eleven entries this family owns: the four omissions and the
seven stale ones, with nothing new appearing. What remains belongs to other
families -- `sessions`, `handshake`, `retentions` and four `oci`/`workspaces`
caller entries -- and is outside this record's boundary.

### A correction to two handoffs I have already made

In W32649's and W34998's pass-back comments I wrote that "the inventory's
missing and stale lists are both empty". That was wrong. I had been reading
those lists through a `grep` filtered to lane- and destroy-related words, and
the header lines matched the filter while the other families' entries did not
-- so an empty-looking result meant "none of MINE", and I reported it as
"none". The narrower claims in those handoffs were true: no lane entry and no
destroy entry was missing or stale. The general one was not, and this record is
where I say so rather than leaving it in two ledger comments.

### PLAN 4 — the module and the shards agree

`evidence/w35557-gate-2026-08-29.txt`. The whole module fails exactly the five
boundary-inventory checks the isolated shards fail, and no attempt-column entry
appears in either. `test_every_declared_probe_reaches_its_named_boundary` is
in neither list.

The module run takes **1288 seconds for 96 tests**, which is why the runner
shards it and why the two verdicts had to be taken separately rather than
assumed equal.

### Reported rather than fixed

Two `tests.manager.test_runtime_lane` shards fail in this transcript. They are
**W32649's second review round** — its reviewer added regressions showing that
the lane's WRITE paths (`_no_predecessor_holds` and the occupancy conflict
branch) read persisted rows without owning the derived/stored relation I fixed
on the READ paths. W32649 is unclaimed and changes-requested; it is not this
Work's to correct while I hold W35557.

## State

**PLAN 1–4 done. Passed back for independent review.**
