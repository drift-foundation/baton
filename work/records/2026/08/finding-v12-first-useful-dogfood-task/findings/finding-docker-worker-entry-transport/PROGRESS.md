# Progress

## 2026-08-29 — first implementation round under W39356 (`baton.claude`)

State: **awaiting review.** All three findings of
`review-2026-08-29T13-43-10Z.md` are corrected, the acceptance's real-engine
proof now exists, and one gate this Work had never been run against caught six
undeclared operands from the seeding round.

### The two [P1]s, verified against the reviewer's own evidence

Both were real and both reproduced before anything was changed.

**A scalar program became argv characters.** `exec_vector` applied
`list(program)`, and `list("python3")` is seven one-character words — so the
commonest possible mistake composed a successfully closed engine vector rather
than a refusal. It now requires `list` or `tuple`; iteration is not a contract,
and a string being iterable is a fact about Python rather than about this
operand.

**Surplus stdout could pass as a clean answer.** The old check looked only at
bytes already buffered when the last expected frame was parsed, so a peer that
made a second frame readable on the NEXT read got `answered` with the surplus
unread. The fix is an ordering one, and it is why the channel contract grew a
member rather than gaining a flag: the worker's loop ends on a clean end of
input, so its stdout cannot reach EOF until its stdin does. `close_input` is
therefore separate from `finish`, `converse` closes the send side on every path,
and stdout is then drained to EOF under a bound. Any surplus is `lost` — after a
fault as well as after a success, because a conversation that stopped at a
refusal asked for nothing more either.

Verification against the reviewer's own artefacts:

    PYTHONPATH=src python3 .../evidence/repro-review-boundaries.py
    -> exit 1, refusing at the first assertion, which is the script's own
       "fixed" signal

    ...and their exact LateSurplus peer, driven separately because the script
    stops at finding 1:
    -> ending: lost | why: the worker wrote 244 byte(s) this conversation did
       not ask for; send side closed first: True; unread frames left: 0

### The real-engine gate, which is the acceptance's own sentence

`tests/manager/test_worker_entry_engine.py` — five cases, registered as the
twelfth serial module. One real container, started through the ACCEPTED
operations rather than by calling `docker run` in the fixture, answers
`describe` and `work` over `docker exec`; the session returns its own status;
stderr comes back separately; and the agent's declared output is on the host
afterwards with the configured workspace group on it. Beside it: the
cross-session refusal at the far end of a real container, an exec against a
removed runtime that is `lost` and explicitly not runtime absence, and the
non-interactive default that proves what the operand actually buys.

**One assertion was corrected by measurement rather than kept.** The first cut
required the produced tree's host-side uid to be 65532. It is 65534 here.
Inside the container the worker is exactly `65532:65532` — `--user` fixes it —
but what the HOST sees depends on the daemon's uid mapping, and on this
development host `docker info` reports no `userns` security option while the
host still shows the kernel overflow id for a file container-uid 65532 created.
Pinning 65532 would have pinned a deployment's mapping under the name of this
transport's contract. What the arc is entitled to require is that the write
happened and the manager can read it, which is what the case asserts now.

### A gate this Work had not been run against, and what it found

`test_dependencies.NoPublicOperationTakesInternalState` failed seven times, all
on code from the seeding round: `network`, `interactive`, `program`,
`channel_port`, `operations` and `operation_ids` were public parameters that no
declared operand vocabulary named. The seeding round ran its own suite and
`test_oci` and not this one — which is precisely the "fixing the two functions
a review names" failure that class exists to catch, and it caught me. Each name
is now declared with the deliberate claim the registry requires.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_worker_entry
    -> 50 tests, OK   (45 before; +5 for the closed-session rule)

    PYTHONPATH=src python3 -m unittest tests.manager.test_oci
    -> 91 tests, OK   (83 before; +8 for the two start operands)

    PYTHONPATH=src python3 -m unittest tests.manager.test_worker_entry_engine
    -> 5 tests, OK (1 skipped: podman is not on PATH)

    ...together with test_oci_engine, test_attempts,
    test_lifecycle_composition, test_worker_container, test_input_delivery,
    test_workspaces, test_intake, test_sealing, test_output, test_offers,
    test_sessions, test_credentials, test_launch, test_dependencies,
    test_text_sweep, test_store, test_negative_race_endings,
    test_ended_runtime_adoption, test_parallel_runner
    -> 1158 tests, OK (12 skipped)

**PLAN item 4 is therefore satisfied**: the real worker-container and lifecycle
composition gates were run in this round and pass. They were reachable directly
even though the parallel runner still stops before its serial phase.

### What is still red in the shared tree, and it is not this Work's

`tests.manager.test_custody` fails twice. Both are regressions the reviewer
added against **W36540**, which is claimed by `baton.codex` right now, and both
are about `custody.py` rather than any file this checkpoint owns:

- `test_a_caller_cannot_select_an_unrelated_storage_root` — derivation below a
  caller-supplied storage root is still caller path selection. This is the
  limitation the W36540 round recorded in its own finding in as many words
  ("it carries the ALLOCATION's authority and not one bit more"); the reviewer
  is ruling that this is not sufficient.
- `test_a_refused_parent_link_creates_nothing_through_its_target` — a genuine
  defect in code that round wrote: the optional `result` root is created by
  `os.makedirs` BEFORE the parent link proofs run, so a refused mint can create
  through a symlinked parent. The correction is an ordering one.

Both are reported rather than touched: W36540 is another participant's active
claim, and this checkpoint owns neither the file nor the Work.

### Still open under W39356

The three boundary-inventory entries. PLAN item 5's condition is a recorded
handoff from that file's current owner, and it has not occurred —
`test_boundary_inventory.py` still carries another participant's uncommitted
edit, and that gate is independently failing on entries across seven modules
that predate this checkpoint.

## 2026-08-29 — second implementation round under W39356 (`baton.claude`)

State: **awaiting review.** Both [P1] halves and the [P2] rationale are
corrected; the [P2] inventory gate is now carried by a linked blocker on the
ledger rather than by prose, which is the alternative the review named.

### The escaping timeout, and the fabricated count beside it

`_Reader._more` called the injected `receive` outside any exception boundary.
`ChannelPort` deliberately hands the deployment the caller's `seconds`, so a
channel that enforces it by raising is the ordinary implementation of the
contract — and its `TimeoutError` escaped `converse` unchanged, past the three
closed endings and past the `finish` that ends the session. Every read failure
is now a bounded `lost` that names the read step.

The second half is the one worth dwelling on. The post-close drain returned a
count and turned **every** failure into `1`, so a timeout while draining was
reported as *"the worker wrote 1 byte this conversation did not ask for"*. That
is a measurement nobody made, and it is the more alarming of the two available
readings — a transport that cannot tell "the peer said something unsolicited"
from "I could not finish reading" is inventing evidence at the least trusted
boundary this manager has. `surplus()` answers `(bytes, why)` now: the count is
only ever bytes actually read, `why` is `None` on a real EOF, and three
regressions hold the three outcomes apart — real surplus is still reported as
surplus even when the drain then fails.

### The rationale that contradicted its own diff

`__init__.py` justified not exporting `converse` partly by saying the shared
declared-operand vocabulary would need widening and that the widening was
outside this checkpoint. True when written; the same checkpoint then made it
false, because `test_dependencies` scans the package source rather than
`__all__` and had caught those six names regardless of any export. The stale
half is removed rather than annotated — two adjacent owned records saying
opposite things is worse than either, since the later reader decides against a
state that never existed. The decision not to export stands on the reason that
is actually true: a component is reached as a component.

### The inventory gate, and why it is a blocker rather than three entries

The reviewer is right that the working-tree conflict I cited earlier is gone —
`test_boundary_inventory.py` is clean against `HEAD`. But the gate still cannot
produce a verdict, for a new reason, and it is mine by authorship:

    AssertionError: workspaces.py:check_workspace_storage:506 owns a boundary
    with no literal label; the inventory cannot attribute it

W36540's eighth round — my previous claim — added `check_workspace_storage`,
whose single boundary call passes the keyword parameter `what` rather than a
literal. The inventory needs a literal at the owning site to key the crossing
and refuses rather than guessing. `check_workspace_group`, the function I
mirrored, calls no boundary helper at all, so the pattern did not carry that
constraint with it. The scan therefore returns nothing for the whole package
and currently blocks every checkpoint's inventory item, not just this one.

Entries written against a gate that cannot answer would be guesses in a shared
registry. So **W39666** owns the three entries and their probes, **W39356 is
blocked on it**, and the defect is reported on W36540's own thread with the
one-line correction. That is the review's second option taken literally:
dependency readiness now carries the fact.

I did try to verify the entries behind a local scratch patch and reverted it;
the run still reported the same site, so I stopped rather than spend further
time on a file this checkpoint does not own.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_worker_entry
    -> 54 tests, OK   (50 before, +1 reviewer regression, +3 mine)

    ...with test_worker_entry_engine, test_oci, test_oci_engine,
    test_dependencies, test_attempts, test_lifecycle_composition,
    test_worker_container, test_input_delivery, test_workspaces,
    test_text_sweep, test_store, test_intake, test_sealing,
    test_parallel_runner
    -> 848 tests, OK (10 skipped)

The real-engine gates ran and pass.

### Not this Work's, and reported

`tests.manager.test_custody` fails twice on regressions added against
**W36540** (queued at `baton.impl`, unclaimed):
`test_a_configured_store_capability_cannot_be_retargeted` and
`test_a_minted_custody_root_cannot_be_retargeted_before_composition`. They are
the seventh manifestation of that Work's standing finding — `object.__setattr__`
reaches every slot, so a held `WorkspaceStorage` or `CustodyRoot` can be
retargeted and the mint reads the replacement without reopening manager-owned
durable state. Real, and not mine to correct under this claim.
