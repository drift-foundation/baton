# Progress

## 2026-08-30 — first round (`baton.claude`, W43977 impl claim)

No dossier was bound at the claim; this record is created beside its two
siblings, and FINDING.md says so.

### The rescan the research required

Both blockers have landed — W43974 removed the free `name` operand and W43975
added the composition and adopted-state surface — so this scans the final
source rather than the baseline the research mapped. Sixteen caller crossings
over `custody.py`; seven already owned, nine not.

### Two of the nine were an ownership gap, not a registration gap

The research's instruction cuts both ways: do not copy validators in merely to
satisfy the table, and equally, do not register an owner where no rule lives.

`adopted_directory_custody` held neither its attempt nor its root kind, and it
derives an operation identity from both — so an unheld identity looked one up
for a name this manager never allocated. A read, but a read of somebody else's
act. Both are held now.

The root kind had no owner anywhere: the same inline `if` in three places,
which is three places to edit and a rule owned nowhere. `check_custody_root`
is its one named owner now, in the shape `check_custody_operation` has had for
the verb since W36540, and the three copies call it.

### The remaining seven are delegations, each naming a site that refuses

`custody_act` is a composer: it hands every operand to the private composer
that owns it and then to the engine port, and owning them again there would be
a second spelling of five rules. Registered to `oci.py:_engine`,
`oci.py:EnginePort.__init__`, `custody.py:check_custody_operation`,
`custody.py:check_custody_root`, `custody.py:_derived_root` and
`custody.py:_custody_vector`. The two public composition entries delegate only
the root kind, holding the attempt and the capability themselves.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_custody
    -> 117 tests, OK.

    A direct scan through the gate's own resolver: zero unowned `custody.py`
    entries, where there were nine.

### Debts my own sibling Works had created, paid here

The scan also found six unowned entries from functions I added under W43975
and W47225: `launch.adopt`'s session, contract and role, and the storage of
`adopted_assignment_workspace` and `discard_execution_roots`. They are
registered — the launch three to `launch.py:_value`, exactly where
`materialize` already delegates the same three, which is the whole reason
adoption reuses the authoring owner rather than re-implementing its rules; the
two storages to `workspaces.py:_real`, beside `discard_workspace`. Leaving
them for whoever next ran the inventory would have been a debt those Works
created and this one walked past.

### THE GATE CANNOT BE GREEN WITHIN THIS WORK'S SCOPE, and that is a finding

The contract asks to "make the focused inventory gate green". `custody.py` is
now at ZERO unowned entries, where it had nine, and every entry my sibling
Works introduced is owned. **131 crossings in ten other modules still have no
owner** — `workspaces.py` 27, `documents.py` 25, `oci.py` 15, `handshake.py`
14, `lanes.py` 12, `attempts.py` 12, `authority_port.py` 10, `worker_entry.py`
8, `intake.py` 4, `sessions.py` 4.

`worker_entry.py`'s eight are explicitly W39666's. The rest belong to no Work
I hold. So `EveryReceivingEntryHasOneOwner` still reports three failures —
`test_every_receiving_entry_has_an_owning_validator`,
`test_every_boundary_call_belongs_to_an_entry_or_is_declared` and
`test_the_universe_sees_every_persisted_column_that_is_read` — and none of
them is about custody. Registering other modules' crossings under this claim
would be inventing ownership for code I have not read, which is precisely what
the pinned research forbids.

### The focused classes are SLOW -- `EveryReceivingEntryHasOneOwner` — `EveryReceivingEntryHasOneOwner`
alone ran 11 tests in 874 seconds, which is why the pinned research recorded a
90-second interrupt rather than a result. A full run is in progress; the gate
is completion of all three focused classes and the module, and this record
will not claim it until that is what happened.

## 2026-08-30 — second round (`baton.claude`, W43977 impl claim)

Thank you for attaching the dossier as the binding; that omission is closed.

### [P0] Every declaration now has its own witness

Thirteen delegations had zero probes, which is not optional coverage — the
gate requires one exact driver per `(entry, label)`, and the parent plan
requires it to prove the DELEGATE's own refusal rather than an earlier
envelope.

Twenty-five probes now cover this Work's sites: the eight custody
delegations, each driving the composer or port that actually refuses; the
three `launch.adopt` values, through the authoring owner adoption reuses; the
two workspace storages and their two attempt identities; and the eleven
layer-owned entries at the same sites, including both rules the typed seam
carries — that it IS the act, and that it names the identity the receipt is
signed with.

Each varies exactly one operand, because `_custody_vector` holds the engine,
then the image digest, then the verb, and only then performs the durable
lookup that owns the attempt and the root kind: a probe spoiling two would
prove the earlier rule twice and the later one never. Every one was driven and
asserted to name its own label.

### [P0] The injected engine answer is discoverable now

You were right that this is structural rather than a missing table row.
`EnginePort.__call__` already OWNED the answer — `boundaries.document(answer,
"the engine's answer", required=("status", "stdout", "stderr"))` and the
status and stream checks are right there — but `CAPABILITIES` did not name
`_run`, so the universe could not discover the crossing at all. Every vector
this module composes, and every custody listing, inspection, stop and removal,
arrives back through that one port.

`_run` is named now, the crossing appears as
`('injected', 'oci.py:EnginePort.__call__', 'run')`, it is layer-owned by the
check that was always there, and it has its probe. Modelled once at the real
crossing rather than once per custody vector, exactly as you asked.

### [P1] The counts now describe the patched source

FINDING.md distinguishes the baseline — sixteen crossings, nine then unowned —
from the seventeen the patched source has, and says eight delegations rather
than seven.

### [P0] The green gate: a ruling, not a reinterpretation

You are right that I replaced "make the gate green" with "make custody absent
from one failure list", and that is not mine to do. I have not touched the 131
entries in the ten other modules, and I am asking for the scope ruling rather
than deciding it — see the handoff.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_custody
      tests.manager.test_launch tests.manager.test_workspaces
      tests.manager.test_oci tests.manager.test_dependencies
      tests.manager.test_intake tests.manager.test_attempts
    -> 734 tests, OK (1 skipped). Whitespace passed.

    Direct projection: zero missing probes and zero wrong labels across all
    twenty-five (entry, label) pairs this Work declares; zero unowned
    `custody.py` entries.

The focused inventory classes still take about seven minutes each here, so the
full three-class run is reported in the handoff rather than claimed from a
partial one.

### A regression of mine the probe gate caught, and fixed

Running the probe gate surfaced eight failures that were nothing to do with
registration: `intake.py`'s destroy-observation probes no longer reached the
boundary they NAME. W43975 made the directory-custody seam mandatory at every
ending's ENTRY, so the probe drivers' fake adapters were refused for want of a
capability before the observation each probe is about. Three fakes now carry
the seam — the shared `_Custodian` and the two ending-specific ones — which is
the same rule the gate applies to every other driver.

That is a defect W43975 introduced into this file and nobody had run the gate
since. It is fixed here because this Work is the one editing the file.

### The probe gate now

    PYTHONPATH=src python3 -m unittest
      tests.manager.test_boundary_inventory.EveryProbeProvesItArrived
    -> 5 tests in 1023s, 2 failures, down from 10.

The eight destroy-observation failures are gone. The two that remain are
`test_every_owned_entry_has_exactly_one_probe` and
`test_the_missing_probe_check_can_actually_fail`, and both are the global
debt: 57 `(entry, label)` pairs across the other ten modules have no probe,
exactly as 131 entries there have no owner. **Zero of either belongs to
`custody.py`, and zero belongs to any site this Work declares** — all
twenty-five of its pairs are present and each was driven and asserted to name
its own label.

## 2026-08-30 — third round (`baton.claude`, W43977 impl claim)

### [P0] Discovery is fixed structurally, and all four entries exist

You diagnosed it exactly. `ast.walk` is BREADTH-FIRST, so
`EnginePort.__call__`'s join -- `taken = boundaries.document(answer, ...)` at
the top level -- was visited before the branch assignments to `answer` inside
the `if`, and origin propagation died there.

`_origins` now iterates to a FIXED POINT. One more pass would have caught this
particular chain and a chain one link longer would have needed another; a
fixed point needs no guess about depth. It terminates because origins only
gain names and each is derived from names already bound, over a finite set of
locals.

`EnginePort.__call__` also read its streams through a LOOP VARIABLE -- `for
stream in ("stdout", "stderr")` -- so the inventory could not see WHICH
members this manager consumes. A member the universe cannot name is a crossing
nobody can be asked to own or witness. The two reads are literal now; same
rule, same owner, only the spelling changed.

The universe discovers all four: `run`, `run.status`, `run.stdout`,
`run.stderr`.

### The owners: an attempt that made the rules WRONG, reverted

`boundaries.injected` is "the answer of a capability trusted deployment
supplied", which is exactly what these members are, so I named it as their
owner. It was wrong twice:

- it proves an injected answer is DURABLE TEXT, so on the status it refused
  every integer an engine has ever returned;
- durable text refuses the EMPTY string, so on the streams it made "nothing on
  stderr" a fault -- which is the ordinary case `_stream` exists to allow, and
  its own docstring says so.

Both are reverted, and 30 failures plus 99 errors in `test_oci` are what said
so. **An owner that makes the rule wrong is not an owner**, and I would rather
report a real gap than register a false one. `run.status` and the two streams
are therefore discovered and layer-unowned.

Closing that honestly needs a boundary kind these members can actually be held
under -- a whole number that may be zero, and text that may be empty -- or an
extension of an existing one. That is a change to the boundaries layer, which
is neither this Work's file nor a thing to do quietly under a registration
claim. It is the one item I am handing back rather than deciding.

`_status` was extracted as a named owner regardless, because the rule was
inline in the middle of its caller and a rule written there is one nobody can
name.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_oci
      tests.manager.test_custody tests.manager.test_launch
      tests.manager.test_workspaces tests.manager.test_intake
      tests.manager.test_attempts
    -> 713 tests, OK. Whitespace passed.

## 2026-08-30 — fourth round (`baton.claude`, W43977 impl claim)

### [P0] The three members are owned, by the route you named

`STATED_OWNERS` at `oci.py:_status` and `oci.py:_stream`, with no new boundary
kind and no `boundaries.injected`. That is the right shape and the rationale
each entry carries is why: neither rule IS a boundary kind and neither could
honestly become one — an exit status is a whole number that may be **zero**,
and an engine stream is text that may be **empty**, which is exactly what a
quiet engine writes. The kinds that exist refuse both, which is what last
round's attempt proved at the cost of thirty failures and ninety-nine errors.

Three independent witnesses, one per member, each asserting the ADMITTED case
as well as the refused one: status zero is ordinary, an empty `stdout` is
ordinary, and a quiet `stderr` is not a fault. `stdout` and `stderr` share an
owner and are witnessed separately, because two entries that share a rule are
still two crossings.

Each spoiled value is JSON data and wrong only for its member. My first cut
used a float and a bytestring, and the ENVELOPE refused them first — so those
probes would have proved the envelope's rule and called it the member's, which
is the trap this file warns about in as many words.

### Where the ledger stands

    total unowned entries: 131

That is the pre-existing debt exactly — the three this Work surfaced are
owned, and nothing was added. `WITNESSES` and `STATED_OWNERS` agree.

### Verification

    PYTHONPATH=src python3 -m unittest
      tests.manager.test_boundary_inventory.StatedRules
    -> 65 tests, OK, including the three new witnesses.

    PYTHONPATH=src python3 -m unittest tests.manager.test_oci
      tests.manager.test_custody tests.manager.test_launch
      tests.manager.test_workspaces tests.manager.test_intake
      tests.manager.test_attempts tests.manager.test_dependencies
    -> 734 tests, OK (1 skipped). Whitespace passed.

Custody is complete: zero unowned entries, zero unprobed pairs, every
declaration witnessed. What remains is the global scope question, still with
`baton.decide` at seq 48312.
