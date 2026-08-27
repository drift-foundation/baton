# Implementer progress — acquisition leaves the core manager

Created 2026-08-26 by `baton.claude` on claiming W15232, as the record
requires.

I raised the question this Work answers. W14251 attempted the neutral schema
revision, measured that `workspaces.py` refuses everything once `gitSource` and
`directorySource` are gone, and blocked rather than widen itself into deleting
a shipped module. This is that deletion, owned properly.

## Item 1 — revalidated, and the cut is clean

`workspaces.py`'s two halves separate exactly, computed from the call graph
rather than eyeballed:

    acquisition-only  GitPort, materialize_git_source,
                      materialize_directory_source, and ten private helpers
                      (_advertised, _agree, _destination, _place,
                      _private_metadata, _publish, _reach, _resolved, _seal,
                      _staging)
    shared            _real, _within, _walk, _open_directory, _read_exactly,
                      _read_all, _remove, _refuse, _denied, directory_manifest
    generic-only      assignment_workspace, discard_workspace, _contained

Nothing in the shared set is lost by removing the acquisition set, so this is a
removal rather than an amputation.

**No production caller outside the module.** Every reference to the three
public acquisition operations was in tests and the boundary inventory.

## Item 2 — there is no owner to re-home into, and I looked

The assignment permits re-homing "only behind an already pinned source-stager
or driver owner". There is none:

- the ledger has no Work matching `stager`, `acquisition` or `driver` beyond
  this one and its closed predecessor W6631;
- `work/records/2026/08/` holds no stager record;
- the umbrella FINDING mentions a source stager once, descriptively — "a
  source stager may clone Git, copy a directory, extract an archive, mount
  remote storage" — and names no Work, no module and no boundary.

So the answer is the assignment's own: **remove it, and do not invent a second
acquisition contract to preserve code the superseding ruling made ownerless.**
The behaviour is recoverable from W6631's record and history if a stager is
ever specified. What is not recoverable is the confusion of a manager that
still exports it.

## Item 3 — removed

- 13 definitions and 349 lines out of `workspaces.py`; exports narrowed from
  eleven names to seven.
- `check_content_manifest` and `validate_fragment` left the module's imports
  with them. Both were how it READ an acquisition descriptor or compared a
  CLAIMED manifest against a measured one — acts of interpreting an
  acquisition contract, and neither one a manager that receives an already
  staged directory performs. `check_content_manifest` stays in the TEST's
  imports, because checking a MEASURED manifest against the frozen shape is a
  generic property of what this manager still produces.
- Package exports, the declared-operand table, and the boundary inventory's
  stated owners, delegations, witnesses and probes all agree with the removal.

## Item 4 — the absence is asserted, not assumed

`TheCoreManagerDoesNotAcquireSources` replaces the two deleted test classes.
Deleting tests deserves saying plainly: a test of behaviour that no longer
exists asserts nothing, so what stands in their place is the absence itself —
no acquisition operation on the module or the package, no acquisition
definition named anywhere in the module's CODE, and the generic duties still
present and callable.

**One of those cases caught my own prose first.** The descriptor case read the
raw source and failed on the module comment explaining why the names are gone.
A case that cannot tell an explanation from a use punishes writing the
explanation down, so it parses the module and looks at names and string
operands instead.

**And one existing cleanup case used acquisition only as setup.** Its property
— cleanup removes read-only trees and leaves the origin untouched — is generic
and kept. The fixture stages a read-only tree directly now, which is also a
more honest picture of what this manager receives.

## Item 5 — the acceptance criterion, measured

Applying W14251's preserved `revise_schema.py` to both schema copies:

    tests.manager.test_workspaces   Ran 22 tests   OK

That is the whole point of this Work. Before it, the same patch made every
acquisition request refuse with "a directory source names definition
'directorySource', which is not one of the frozen worker-control schema's own
definitions", and W14251 could not measure its own contract change.

The other 15 failures and 61 errors under the patch are the vectors, fixtures
and conformance expectations — W14251's own PLAN item 5, and explicitly not
this Work's. **Both schema copies were restored** to their committed bytes
afterwards: W15232 unblocks that revision, it does not land it.

## Two long-standing failures went away

`test_no_declared_owner_is_stale` had been failing on
`workspaces.py:materialize_git_source`'s `base_revision.algorithm` and
`base_revision.hex` since before this session, and I have been reporting them
as somebody else's in three handoffs. They were this module's, and they are
gone with it. The orphan set drops from 18 to 17 for the same reason.

## Verification

`evidence/gate-2026-08-26-removal.txt`.

## State

**Awaiting independent review.** No repository state was mutated.


## Review corrections — 2026-08-26

### [P1] The retained manager still provisioned acquisition-specific capacity

The review is right, and the interesting part is WHY my cut missed it.

I separated this module's two halves by closing the CALL GRAPH over each,
which treats a function as one node. `assignment_workspace` calls nothing from
the acquisition set, so it came out "generic" — while the acquisition-specific
work sat INSIDE it, allocating a third root for version-control metadata on
every assignment whether its staged input was a directory, an archive, a
database snapshot, media or a format nobody has written yet.

**A call-graph closure cannot see inside a node.** It answered "which
functions belong to the acquisition half" correctly and could not answer
"which work inside a retained function is acquisition-specific", which is a
different question I never asked. That is worth writing down because the same
method will be used again on the next module.

The same vocabulary survived independently in the adapter: `oci.ROOT_NAMES`
was closed over three roots, so `_roots` refused an otherwise complete generic
root set and the core still understood an acquisition format after the
operations that consumed that root were gone.

Both are two roots now — `inputs`, read-only evidence, and `workspace`, the
only writable tree. A stager or driver needing private capacity allocates its
own under an explicit owner: private ephemeral space is generic runtime
capacity, not protocol vocabulary this manager provisions.

Four fixtures carried the third root and are narrowed with it, and the case
that asserted a private metadata root is never mountable went with the root it
was about.

### [P2] The module contract advertised the deleted component

Rewritten around what remains: two assignment-private roots, the measured
directory manifest, containment, and cleanup. It states what this component no
longer does and why, and points at the records for the reasoning that was
superseded rather than keeping it as the live contract. The empty
`delivering a source` section is gone.

### Verification

`tests.manager.test_workspaces` 23/23, `tests.manager.test_oci` green, and the
boundary inventory back to its pre-existing six failures with nothing naming
`workspaces.py` or `oci.py`.

Two `test_sealing` failures are **W6634's**, not this Work's: its review added
`test_collection_uses_immutable_custody_not_the_live_workspace` and
`test_two_names_cannot_alias_or_nest_the_same_output_tree` after I passed that
Work back, and it is routed to the reviewer. One `test_intake` failure is
W6629's for the same reason, and `test_worker_image_build` is W6633's.

## State

**Awaiting independent re-review.** No repository state was mutated.


## Re-review [P2] corrected — 2026-08-26

Three stale surfaces, all describing behaviour this Work deleted:

- `oci.py` still explained that a private acquisition root exists as
  manager-owned metadata that neither posture mounts — beside a contract that
  no longer has one;
- `test_workspaces.py` still opened by promising pinned revision/ref and
  shared-metadata cases and explaining why its now-deleted half used a fake
  repository;
- two constants that half left behind.

All three are corrected. The test module contract is rewritten around what
remains — the generic directory measurement, assignment-private workspaces,
containment and cleanup — and says plainly what it no longer covers and why,
pointing at the records for the superseded reasoning.

### This is the second time this campaign, so it is gated now

W14828 had the same shape twice: correct the code, leave the prose beside it
telling the next maintainer the opposite. Here it was the code corrected and
three explanations left standing.

`test_no_surface_still_describes_the_acquisition_specific_root` checks the
removed root name as a STRING OPERAND across `workspaces.py` and `oci.py`, and
pins `ROOT_NAMES` to the two generic roots.

**Operand rather than word, deliberately.** A root name is a literal these
modules act on; an explanation of why that root is gone is prose which should
be free to say so. An earlier attempt at exactly this kind of case failed on a
module's own comment — a case that punishes the explanation it wanted written
down. Measured: reintroducing the root into `ROOT_NAMES` turns the case red,
source restored byte for byte.

### Verification

`tests.manager.test_workspaces` and `tests.manager.test_oci`: **98/98**, up
from 97 for the added gate.

## State

**Awaiting independent re-review.** No repository state was mutated.
