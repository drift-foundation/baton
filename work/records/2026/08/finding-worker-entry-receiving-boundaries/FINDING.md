# Inventory the worker-entry transport's receiving boundaries

Work: W39666
Origin: W39356's worker-entry transport implementation, message M39666

## Finding

W39356 introduced a bounded Docker worker-entry conversation and recorded three
boundary calls that could not safely be registered while the shared inventory
was under another participant's edit:

```text
oci.py:_network              text      an engine network
oci.py:exec_vector           text      an exec program word
worker_entry.py:converse     identity  a worker-entry operation identity
```

W36540 has closed, the inventory completes in bounded time after W54182, and
the debt can now be revalidated against the current tree.

## 2026-08-31 reviewer rescan

**Observed.** W39666 had no canonical dossier binding when claimed. The durable
references lived in W39356 and the later inventory records. This record is the
canonical dossier created from those retained references; it does not replace
or rewrite them.

**Observed.** The current discovery reports ten caller entries in
`worker_entry.py`:

```text
worker_entry.py:ChannelPort.__init__  open_channel   owned, no probe
worker_entry.py:_Reader.__init__      channel        unowned
worker_entry.py:converse              channel_port   unowned
worker_entry.py:converse              engine         unowned
worker_entry.py:converse              operation_ids  unowned
worker_entry.py:converse              operations     unowned
worker_entry.py:converse              program        unowned
worker_entry.py:converse              runtime_id     unowned
worker_entry.py:converse              seconds        unowned
worker_entry.py:converse              session        owned, no probe
```

The two existing owners are real layer owners: `ChannelPort.__init__` applies
`boundaries.capability(..., "the channel's open operation")`, and `converse`
applies `boundaries.identity(..., "the launched worker session")`. Neither has
an entry-keyed probe in `EveryProbeProvesItArrived`.

**Observed.** The original three validator sites now map to receiving entries
as follows:

- `_network` is private and is not itself a receiving entry. Its real caller
  crossing is `('caller', 'oci.py:run_vector', 'network')`, currently unowned;
  the owner is the `_network` helper and should be declared as a delegation.
- `exec_vector`'s per-word `boundaries.text` call is not attributed through the
  loop to `('caller', 'oci.py:exec_vector', 'program')`, currently unowned. The
  function also owns the list/tuple shape, non-empty constraint, word ceiling,
  and every member, so this is a composite stated owner rather than merely a
  text label pasted onto the container.
- `converse`'s per-id `boundaries.identity` call is not attributed through the
  loop to `('caller', 'worker_entry.py:converse', 'operation_ids')`, currently
  unowned. It also owns cardinality, length and uniqueness, so this too is a
  composite stated owner.

**Confirmed defect.** `converse` currently begins both collection checks with
`list(...)`. A non-iterable caller value therefore escapes the manager's
contract vocabulary as raw Python:

```text
operations=None      -> TypeError: 'NoneType' object is not iterable
operations=7         -> TypeError: 'int' object is not iterable
operation_ids=None   -> TypeError: 'NoneType' object is not iterable
operation_ids=7      -> TypeError: 'int' object is not iterable
```

This is not an inventory-only omission. A claimed owner needs a witness that
can drive every part of the rule, and these values prove the collection-shape
part has no contract owner yet. Correct the behavior before registering the
stated owners.

**Confirmed scope.** W48697's later durable ruling assigns general `oci`
inventory debt to its parked module-decomposition umbrella while repeatedly
preserving all of `worker_entry` for W39666. W39666 therefore owns:

1. every current `worker_entry.py` receiving entry; and
2. the two OCI receiving entries corresponding exactly to W39356's retained
   `_network` and exec-program obligations.

It does not absorb adjacent OCI entries merely because they share a function.
For example, the currently unowned `exec_vector.engine` and the missing probe
for its already-owned `runtime_id`, plus `run_vector.interactive` and the
adapter's forwarded network/interactive operands, remain in W48697's general
OCI rescan unless that owner records an explicit supersession.

## Ownership model to revalidate at implementation start

**Proposed.** Prefer the existing inventory vocabulary rather than adding
boundary calls just to satisfy discovery:

- declare real forwarding paths in `DELEGATED` (notably `run_vector.network`,
  `converse.engine`, `converse.runtime_id`, and `converse.channel_port`) and
  drive the public receiving site to the delegate's exact refusal label;
- use `STATED_OWNERS` plus `WITNESSES`/`StatedRules` for closed vocabularies,
  collection shape/member rules, positive seconds, and the already-validated
  internal channel handed to `_Reader`;
- keep the direct layer owners for `open_channel` and `session`, and add exact
  probes for those entry keys;
- do not list a value under `NO_PROBE`: all crossings in this slice are
  directly driveable; and
- do not add `_network` to `NOT_AN_ENTRY` as a way to hide it. Its boundary
  call owns `run_vector.network` through a real delegation.

The implementer must revalidate each proposed table classification against the
then-current scanner. A table entry is not acceptance unless its witness reaches
the named owner and fails if that owner is removed.

## Minimal reproductions

From `v12/python`:

```sh
PYTHONPATH=src python3 -m unittest \
  tests.manager.test_boundary_inventory.EveryReceivingEntryHasOneOwner
```

On the 2026-08-31 tree this completes in about half a second and reports 133
global unowned entries; the W39666 slice is the eight `worker_entry.py` rows
listed above plus the two historical OCI rows. The global total is evidence,
not this Work's acceptance count.

The raw-TypeError reproduction calls `converse` with otherwise valid operands
and substitutes `None` or `7` independently for `operations` and
`operation_ids`. Each currently raises `TypeError`; each corrected case must
raise `ContractRefusal` before the channel is opened.

**Verification baseline, 2026-08-31.** The unchanged functional transport and
stated-owner declaration gates are green: 55 tests pass in 0.009 seconds for
`tests.manager.test_worker_entry` plus
`EveryStatedOwnerHasAWitness`. The bounded `EveryProbeProvesItArrived` gate
runs 5 tests in 2.106 seconds: all 549 declared probes arrive, while its two
catalog-completeness assertions fail on the already-recorded 46 missing pairs.
Exactly two of those 46 are current W39666 pairs (`ChannelPort.open_channel`
and `converse.session`); the other 44 remain outside this slice except where a
new owner added here necessarily creates its corresponding new probe duty.

## Acceptance boundary

- A fresh discovery has zero unowned entries at every `worker_entry.py` site.
- `run_vector.network` delegates to `_network`, and `exec_vector.program` has
  one truthful composite owner, preserving W39356's exact historical debt.
- Every affected layer/delegated `(entry, label)` has exactly one probe, and
  every stated owner has an entry-keyed witness in `StatedRules`.
- Malformed `operations` and `operation_ids` containers refuse as contract
  violations before channel open; valid list/tuple inputs preserve order,
  cardinality, distinct operation identities, and the existing closed
  operation vocabulary.
- Existing functional transport behavior remains unchanged: the focused
  `test_worker_entry` suite passes.
- Add a slice-specific inventory regression so W39666 can be verified while
  W48697's unrelated aggregate debt remains parked. Do not weaken or replace
  the aggregate owner/probe assertions.
- The full aggregate inventory is allowed to remain red only for entries
  outside this recorded slice, with the residual grouped output reported.

## 2026-08-31 implementer revalidation and outcome

**Confirmed, by re-derivation rather than by agreement.** The ownership model
above was labelled **Proposed** and required re-checking against the
then-current scanner. `owning_validators()` reports:

```text
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
```

The subject column decides every classification. `'one'` is a LOOP VARIABLE,
so the per-member calls in `exec_vector` and `converse` are attributed to the
loop rather than to the operand — correctly, because a container's shape,
cardinality and emptiness are a genuinely second rule the layer never saw.
Every proposal in the section above survived unchanged.

**The confirmed defect is corrected.** `converse` no longer opens either
collection check with `list(...)`; both operands are held to an explicit
`list`/`tuple` shape first, in the idiom `exec_vector` already carries for the
same reason. The refusal names the string hazard, which is the case that
matters: `operations="describe"` used to iterate eight characters and refuse by
naming `'d'` — a refusal that describes neither what was passed nor what is
wrong with it.

**Registered.** 4 delegations (`run_vector.network`, `converse.engine`,
`converse.runtime_id`, `converse.channel_port`), 6 stated owners each with a
witness (`exec_vector.program`, `converse.program`, `converse.operations`,
`converse.operation_ids`, `converse.seconds`, `_Reader.__init__.channel`), and
6 probes — the two previously unprobed layer entries plus one per delegation.
Nothing was placed in `NO_PROBE` and `_network` was not placed in
`NOT_AN_ENTRY`, as this record's model required.

**All 22 registrations are mutation-tested.** Each removed in turn; the slice
check `TheWorkerEntryTransportIsFullyInventoried` catches every one.

**Acceptance boundary, measured.** A fresh discovery has zero unowned
`worker_entry.py` entries and zero unowned W39666 OCI entries. Aggregate
residual: unowned 133 → 123, owned-but-never-probed 46 → 44, and
probed-but-never-owned 3 → 3, with the same five aggregate failures in the
same two separately routed families. `exec_vector.engine`,
`run_vector.interactive`, `run_vector.workspace_group` and
`exec_vector.runtime_id`'s missing probe are untouched and remain
W48697's.

Implementer account and exact commands: `PROGRESS.md`, first round.

## 2026-08-31 independent review

**Confirmed.** The collection-shape correction, ownership registrations,
witnesses and probes satisfy their recorded behavioral boundaries. Focused
worker-entry and inventory tests pass, every declared probe reaches its named
boundary under `ResourceWarning`-as-error, and all 255 adjacent OCI/operator
tests pass.

**Changes requested.** The slice-specific probe assertion currently checks
only that no wanted pair is missing. It does not reject an extra, stale, or
wrong-label probe attached to an entry in this slice, so it does not yet prove
the acceptance rule that the affected pairs are exact while the aggregate is
red on unrelated debt. The declared probes for slice entries must equal the
wanted set in both directions, with an added-extra mutation proving the
negative direction. See
`review-2026-08-31T17-55-24Z.md`.
