# Implementer delivery notes — W371294 claim375825

Appendix to `PROGRESS.md`, written after the implementation so the revalidation
above stays a record of what was true at claim.

## What was built

| Path | Role |
| --- | --- |
| `job_manager/role_contract.py` (new) | the closed descriptor, its pure validator, the bounded byte reader and the template binding |
| `job_manager/templates.py` | registers revision `/2`; `/1` and the configured default untouched |
| `tests/job_manager/test_role_contract.py` (new) | 74 cases: frozen positive vector, exact bounds, every refusal row, the reader, the registry |
| `tests/job_manager/test_templates.py` | two registered-set assertions updated — reason below |

### The positive vector is the owner's document, not mine

The approved `ROLE-CONTRACT.proposed.json` is read from the record **as bytes**
and compared against what the module composes, and its canonical digest is
asserted on both sides at `sha256:21b78036…acdffdaf` — the value the proposal
states. The proposal's own SHA-256 is asserted too, so an edited specification
fails the suite rather than silently redefining every bound below it. The
module also asserts the same identity **at import**, so a build that composed a
different descriptor cannot start.

### The validator is exact equality, in both directions

Every limit is checked as an equality rather than a range, which is what was
approved — and a case drives the **lower** direction as well as the higher one,
because a validator that accepted 1024 where 1048576 was selected would be
deciding that tighter is safer on an owner's behalf. `0` is not `false` and
`true` is not `1`: `contracts.own` keeps booleans and integers apart in the
value space and the comparisons keep them apart at the point of comparison.

### Two things the frozen schema taught me, recorded rather than smoothed over

1. **The frozen contract refuses first, and three of my assertions were
   wrong.** `validate_fragment(…, "outputDescriptor")` holds each output to
   the frozen `outputConstraints`, which already pins `link_policy` as a const,
   types `max_entries` as an integer and is `additionalProperties: false`. My
   first draft asserted this revision's own wording for a permissive link
   policy, a boolean limit and an invented limit member; the shared contract
   caught all three first. The cases now assert the refusal that actually
   happens and say that this revision's equality is a **second** line — and one
   case drives a fault the frozen fragment never sees (a missing `constraints`
   object) so that second line is shown to be live rather than dead.
2. **The descriptor could not be a template member.** `TEMPLATE_MEMBERS` is
   closed and `_exactly` requires every member, so adding `role_contract` to
   the `/2` entry would have added it to `/1` as well — which is exactly the
   silent reinterpretation of an already admitted Job that the admission slice
   exists to prevent. The binding therefore lives with the descriptor, in
   `role_contract.TEMPLATE_CONTRACTS`, and `contract_for("/1")` answers `None`
   because **absence is the preserved legacy path**. Import-time assertions
   hold the two tables together: the descriptor names the template it is
   registered under, and every declared output is produced by a role of that
   template and vice versa.

### `/2` is derived from `/1`, deliberately

The second entry is `dict(_AUTHORED[IMPLEMENTATION_REVIEW], version=…)`. A
second literal would let the two revisions' graphs drift while one descriptor
claimed to describe the workflow both run; the derivation makes "only the
version differs" structural, and a test asserts it. `_frozen` still copies
every mapping at every depth, so the two entries share no mutable member — and
a case drives that by deleting through the new entry's proxy.

## Changed test reason

`tests/job_manager/test_templates.py` carried two assertions that the
registered set is exactly one template. A second revision is the approved
carrier change and this module's own stated shape — *"a second revision is a
second entry in the table below rather than an edit to this one"*. Both were
updated under standing test authority to name the **complete** set of two, so a
third entry appearing without a decision still fails; one also now drives the
new entry's immutability, which it could not before.

## Verification

    tests.job_manager.test_role_contract                  74 OK   (new)
    tests.job_manager.test_templates + test_creation     198 OK
    tests.tools.test_creation_ports
      + test_job_task_delivery + test_connected_creation 143 OK
    tests.manager.test_contracts_inventory + test_frozen  33 OK

Full `tests/job_manager` discovery: 1449 tests with 3 errors, in
`test_native_permission`, `test_native_stop_restart` and
`test_serving_renewal`. **All three reproduce with the pristine committed
`templates.py` restored and `role_contract.py` removed**, so none is
attributable to this candidate; they are mock-driven `tools/stage_execution`
paths. Attribution was done by that swap rather than by calling them
pre-existing, because this tree also carries other owners' uncommitted work.

## What this slice is not

No installed capability document, qualification digest or grant; no
deployment `/3`, derivation `/1` or resolution `/2` carrier; no pre-creation
admission predicate or serving recheck; no `_for_task` manifest correction; no
DESIGN edit. Those are the proposal's later steps and W371295's
"Compose qualified role contract admission and provenance", which consumes this
contract. A resolution of a `/2` Job is byte-identical in shape to a `/1` one
today, and a case asserts the resolution carries no descriptor member — so
nothing downstream has silently acquired a new contract. No provider, engine,
deployment or live execution, and no Git mutation.
