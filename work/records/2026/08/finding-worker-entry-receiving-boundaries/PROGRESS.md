# Progress

## 2026-08-31 — first implementer round (`baton.claude`, W39666 impl claim)

**Plan items 3 and 4 are done.** Every `worker_entry.py` receiving entry and
both of W39356's retained OCI entries now have a real owner, a probe or a
witness, and the confirmed raw-`TypeError` defect is corrected first — as the
finding requires, because a claimed owner a value escapes is not an owner.

Files changed:

- `v12/python/src/baton_v12/worker_manager/worker_entry.py` (the correction)
- `v12/python/tests/manager/test_worker_entry.py` (its regressions)
- `v12/python/tests/manager/test_boundary_inventory.py` (the registrations,
  witnesses, probes and the slice check)

### The proposed model, revalidated against the scanner rather than adopted

The finding labelled its ownership model **Proposed** and required each
classification to be re-checked. I re-derived all of it from
`owning_validators()` before writing a table entry:

    worker_entry.py:converse
      ('identity', 'the launched worker session', 'caller:session')
      ('identity', 'a worker-entry operation identity', 'one')
    worker_entry.py:ChannelPort.__init__
      ('capability', "the channel's open operation", 'caller:open_channel')
    oci.py:exec_vector
      ('identity', 'a runtime id', 'caller:runtime_id')
      ('text', 'an exec program word', 'one')
    oci.py:_network
      ('text', 'an engine network', 'caller:network')

That subject column decides every classification here. `'one'` is a LOOP
VARIABLE: the per-member calls in `exec_vector` and `converse` are attributed
to the loop, not to the operand — which is correct, because the container rule
really is a second rule the layer never saw. So those operands are stated
composite owners, and the ones that are simply handed on are delegations. The
finding's proposal survived revalidation unchanged; this is the measurement
that says so rather than my agreement with it.

### The confirmed defect, corrected before anything was registered

Reproduced first, exactly as the finding records it:

    operations=None    -> TypeError: 'NoneType' object is not iterable
    operations=7       -> TypeError: 'int' object is not iterable
    operation_ids=None -> TypeError: 'NoneType' object is not iterable
    operation_ids=7    -> TypeError: 'int' object is not iterable

`converse` opened both collection checks with `list(...)`. The correction is
the idiom `exec_vector` already carries for exactly this reason — an explicit
`list`/`tuple` shape check, refusing anything that merely iterates:

    operations='describe'  -> ContractRefusal: a conversation's operations is
                              a list or tuple; this is 'describe'. ...

**The string case is why the shape is checked rather than iterated.** Today
`operations="describe"` refuses — but by naming `'d'`, which describes neither
what the caller passed nor what is wrong with it. `exec_vector` paid a review
round to learn the same thing about `list("python3")`; this is the second time
the package has met it, and the comment says so.

Three regressions in `test_worker_entry.py`: every non-iterable and mapping
refuses as a contract violation with the channel unopened; a string is not
eight operations; and a TUPLE is still accepted, with the sent order and
pairing preserved — so the shape rule cannot become a rule against composing a
conversation from an immutable sequence.

### What was registered, and under which vocabulary

**DELEGATED (4).** Real forwards, each driven at the site that has it:

    oci.py:run_vector.network        -> oci.py:_network  caller:network
    worker_entry.py:converse.engine  -> oci.py:_engine   caller:engine
    worker_entry.py:converse.runtime_id -> oci.py:exec_vector caller:runtime_id
    worker_entry.py:converse.channel_port
                                     -> worker_entry.py:ChannelPort.__init__
                                        caller:open_channel

`_network` is deliberately NOT added to `NOT_AN_ENTRY`. It is private, so it is
not a receiving site — but hiding it would leave the public operand it owns
unowned, which is the opposite of what W39356 recorded.

**STATED_OWNERS (6), each with a witness in `StatedRules`.** The two composite
sequence owners (`exec_vector.program`, `converse.operation_ids`), the closed
operation vocabulary (`converse.operations`), the forward to a stated owner
(`converse.program`), the positive-seconds rule owned at
`ChannelPort.__call__` (`converse.seconds`), and the internal channel
(`_Reader.__init__.channel`). Nothing was listed under `NO_PROBE`: every
crossing in this slice is reachable from a public operation with one operand
spoiled, and the slice check asserts that.

**PROBES (6).** The two entries that were already layer-owned and had no probe
— `ChannelPort.__init__.open_channel` and `converse.session` — plus one for
each delegation. Each drives the public operation of THIS slice rather than
the delegate, because a delegation nobody exercised at its own site is a rule
that site does not have.

### The slice check, and the reason it exists

`TheWorkerEntryTransportIsFullyInventoried`, five cases. The aggregate classes
are red on W48697's and W54802's debt, so a finished slice would be invisible
inside their failures and "still red, but less so" is not something a reviewer
can check. The class states the slice's own claim: the sites it covers, an
owner for every entry, a witness for every stated owner, exactly one probe for
every layer/delegated pair, and no `NO_PROBE` exemption anywhere in it. It
does not weaken or replace the aggregate assertions.

The two in-scope OCI entries are written out in the class, so any later
expansion of this slice into W48697's territory shows up in a diff rather than
in a passing test.

### Every registration mutation-tested

A completeness check that cannot fail is not evidence, so each of the 22
registrations was removed in turn and the slice check re-run:

    10 table entries (4 DELEGATED, 6 STATED_OWNERS)   all CAUGHT
     6 probes, dropped by key                          all CAUGHT
     6 witnesses, dropped by entry                     all CAUGHT

### Verification

    tests.manager.test_worker_entry                          57 tests, OK
      (54 before; the three new collection-shape regressions)
    EveryStatedOwnerHasAWitness + StatedRules                72 tests, OK
      (66 before; the six new witnesses)
    TheWorkerEntryTransportIsFullyInventoried                 5 tests, OK
    TheDiscoveryProjectionsAreBoundedAndImmutable
      + TheProbeDriverIsBounded                              11 tests, OK
    all six together                                        145 tests, OK, 2.0s
    EveryProbeProvesItArrived
      .test_every_declared_probe_reaches_its_named_boundary   1 test, OK, 2.0s
    tests.manager.test_oci + tests.tools.test_dogfood_operator
                                                            255 tests, OK

`tools/dogfood_operator.py` is the one production caller of `converse`; it
passes a list and a list comprehension, and its suite is green.

### The aggregate residual, grouped and reported rather than absorbed

    EveryReceivingEntryHasOneOwner + EveryProbeProvesItArrived
    -> 17 tests, FAILED (failures=5)   — the same five as the baseline

    unowned entries          133 -> 123
      workspaces 27, documents 25, handshake 14, oci 13, attempts 12,
      lanes 12, authority_port 10, intake 4, sessions 4, credentials 2
      worker_entry.py left unowned: NONE
      the two W39666 OCI entries left unowned: NONE

    owned but never probed    46 -> 44
      intake 17, oci 10, sessions 7, workspaces 5, handshake 4, attempts 1
      W39666 slice pairs missing a probe: NONE

    probed but never owned     3 -> 3   (unchanged; all three handshake/lanes)

The ten newly owned entries are exactly this slice. The probe deficit falls by
two because the slice's two already-owned entries gained probes; the four new
delegations each brought their own, so they add nothing to the debt.

### Scope kept

`oci.py:exec_vector.engine`, `oci.py:run_vector.interactive`,
`oci.py:run_vector.workspace_group` and the missing probe for
`exec_vector.runtime_id` are still unowned or unprobed. They are W48697's under
its durable ruling and were deliberately not claimed here, even though three of
them share a function with entries this Work does own.

Whitespace clean; no line I added exceeds the file's width.

### State

Awaiting independent review. Passing back rather than closing.

## 2026-09-01 — second implementer round (`baton.claude`, W39666 impl claim)

**The [P2] is corrected. One test method changed; no production source, no
table entry, no probe and no witness moved.**

### The gap, and why the global check could not cover it

`test_every_probed_owner_in_the_slice_has_exactly_one_probe` asserted only
`wanted - declared`. So a probe registered for one of this Work's entries under
the WRONG LABEL — or a second, stale label on an entry already probed —
passed the slice's own acceptance. `EveryProbeProvesItArrived`'s global
assertion is exact in both directions and would have caught it, but it is
deliberately red
on W48697's and W54802's parked debt, which is the whole reason this slice
check exists. A one-directional check inside a red aggregate is a check that
cannot fail for half its subject.

Corrected as the review asked: the declared set is narrowed to
`slice_entries()` and compared for EQUALITY. A probe this slice does not own is
now as much a defect as one it owns and lacks.

### The direction the removal mutations could not reach, now measured

The earlier round mutated by REMOVING each of the 22 registrations, which only
ever exercised `wanted - declared`. Four added-probe mutations exercise the
other side:

    CAUGHT  a WRONG LABEL on a real slice pair
    CAUGHT  a second label on an already-probed entry
    CAUGHT  a probe for an entry this slice STATES rather than probes
    CAUGHT  the retained OCI entry probed under the wrong label

All four fail the slice check now and none of them would have before. The
twelve removal mutations from the first round were re-run against the corrected
test and all still bite, so the new direction was added without weakening the
old one.

### Verification — the reviewer's own commands

    test_worker_entry + EveryStatedOwnerHasAWitness + StatedRules
      + TheWorkerEntryTransportIsFullyInventoried
      + TheDiscoveryProjectionsAreBoundedAndImmutable
      + TheProbeDriverIsBounded                      145 tests, OK
    EveryProbeProvesItArrived
      .test_every_declared_probe_reaches_its_named_boundary
      under -W error::ResourceWarning                  1 test, OK
    test_oci + tests.tools.test_dogfood_operator      255 tests, OK

Same figures as the review recorded. The aggregate residual is untouched: this
round changed one assertion inside this Work's own slice check.

### State

Awaiting independent review. Passing back rather than closing.
