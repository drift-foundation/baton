# Progress

## 2026-08-31 — first implementer round (`baton.claude`, W52800 impl claim)

Implemented to the pinned ruling. PLAN steps 3 and 4 are done; step 5 is done
except the boundary inventory, whose result is recorded below.

### The manager half

`RUNTIME_FILE = 0o640` is the ruled slot mode, exported and asserted by
literal. `VOLATILE_FILE = 0o600` stays as decision history and nothing creates
a slot at it. The volatile root stays `0o700` and manager-owned, so the slot
cannot be reached by traversal.

`_reader_group` is the one owner for "who may read a live bearer". It takes
the nominal `WorkspaceGroup` and refuses a bare integer, which is the same
hold `oci.run_vector` applies to the same capability for the other half of the
same grant -- the `--group-add` that lets the runtime use it. An integer
accepted here would be this module deciding who may read a bearer.

`CredentialHome.materialize` gained a required keyword-only `workspace_group`,
held with the other operands BEFORE the attempt root exists, and the creation
order is the ruled one:

    1. exclusive-create the slot EMPTY at a mode no broader than 0640
    2. fchown the DESCRIPTOR to the configured gid (-1 owner: custody stays)
    3. fchmod the STILL-EMPTY descriptor to exactly 0640
    4. only then the bearer bytes

Every step before the write is on an empty inode, so a failure at any of them
unwinds a file that never held a bearer. Step 3 is what makes the mode exact
rather than whatever the umask left: `os.open`'s mode is filtered by it, so a
service umask of 077 would otherwise create an unreadable slot and nothing
would say so. All three act on the descriptor rather than the path.

### Recovery proves the ruled fact before it reads

`CredentialHome.adopt` gained the same capability and `_proved_slot`: a live
slot must be a regular file at exactly `0640`, owned by this manager, in the
configured gid, proved by `lstat` -- not `stat`, because a symlink resolving
to a correct-looking file elsewhere is the substitution this exists against --
and proved BEFORE the read-back. Refusing after the bytes are in memory would
be refusing a value already registered.

`OciAdapter._recovered` passes the group it already validated at construction;
the ordinary retry builder passes `_configured_group(store)`. One capability,
both halves of the grant.

### The adapter half

`claude_agent._prepared_home` asked `os.path.exists`, which is a `stat`. That
is the whole distinction W52800 cost: a slot the fixed uid cannot open passed
it, was symlinked into the private home, and became a provider that printed
`Not logged in` and exited 1 with an unpublishable diagnostic. It now asks
`os.access(slot, os.R_OK)` after the existing missing check and raises a
DISTINCT bounded refusal. `os.access` answers for the effective identity
without a descriptor onto bearer bytes.

Missing and unreadable stay different refusals because they are different
operator actions: a delivery that did not happen, versus one whose permissions
do not admit this runtime.

### Cases, each shown to fail first

Reverting the manager to `0600` with no `fchown`/`fchmod` fails four cases and
errors four more. Removing the adapter guard fails
`test_an_unreadable_credential_refuses_before_the_provider_runs`. Both runs
performed and restored.

New coverage:

- the literal mode, the literal gid, manager ownership, and `other` empty --
  asserted separately, because "readable by the container" and "readable by
  anyone" are different claims and only one is ruled;
- four umasks including `0o077`, each requiring exactly `0640`;
- the ORDER, watched through `os.open`/`fchown`/`fchmod`/`os.write` with the
  file's SIZE at each step, so the bearer is provably written last -- a `stat`
  afterwards cannot tell that order from the reverse;
- a group that is not the deployment's capability refused, with no root made
  and no bearer registered;
- the adapter's unreadable refusal, asserting no provider was launched.

`test_the_bearer_bytes_are_never_opened` already proves the check reads
nothing -- it replaces the slot with a directory and requires the turn to
complete, which still holds with the new guard. I wrote a second case for that
property, found it redundant and weaker, and deleted it rather than claim two.

### The real-container gate

`test_credentials_engine` gained the positive and negative halves, measured
INSIDE a container because that is the only place the question is real -- the
manager's `stat` of its own file cannot answer what a different uid may do:

- uid 65532 WITH `--group-add <configured gid>` -> `readable`;
- uid 65532 WITHOUT it -> `unreadable`.

The probe answers `readable`/`unreadable` and never content, the same shape
`preflight._observed_readable` uses in the spike and for the same reason.

### Verification

    tests.manager.test_credentials                          86 tests
    tests.manager.test_claude_agent                         68 tests
    + oci, intake, attempts, sessions, secrets, dogfood_image,
      dogfood_operator, ended_runtime_adoption,
      refused_session_cleanup, failed_start_destroy       1046 tests, OK
    tests.manager.test_credentials_engine (real Docker)      9 tests, one
      pre-existing failure -- see below

### Two things a reviewer should see

**`test_nothing_this_module_made_survives_it` fails on pre-existing litter.**
It asks the daemon globally for `name=baton-runtime.start` rather than for
this module's own mark, and 23 such containers exist, all created 2026-08-30
around 14:00 -- fourteen hours before this Work. The count was 23 before my
runs and 23 after; my two new cases use `--rm`. I did not delete them:
removing containers is destructive and they are not mine to judge. Reported
rather than cleaned.

**The boundary inventory is still running when this was written.** It is the
suite with the known global backlog W43977 is blocked on, and my change adds
two public keyword operands (`materialize`/`adopt`'s `workspace_group`) of the
same shape `oci.run_vector` and `OciAdapter.__init__` already carry without
inventory entries. If it reports more than that known backlog, the delta is
mine and I will say so in the next round rather than let the number stand
unexplained.

## 2026-08-31 — second implementer round (`baton.claude`, W52800 impl claim)

All three review findings accepted and closed. The first round was passed back
before its terminal evidence existed, which the review is right to call out;
this round records it.

### [P0] Recovery now proves the ROOT before any child or bearer read

The reviewer is right that this is load-bearing rather than tidy, and the
sentence that settles it is theirs: *"Materialization setting 0700 earlier is
not evidence at restart; adoption exists precisely because this process did
not create the state it is accepting."*

The approved argument has two halves -- the slot is group-readable at `0640`,
AND the root above it stays manager-owned at `0700` so host members of that
group cannot traverse to it. My first cut proved only the first half at the
one boundary that inherits somebody else's filesystem state. A root widened to
`0770` hands every host member of the configured group a path to the bearer; a
substituted root means every child check happens under a pathname whose
custody nobody proved.

`_proved_root` runs before the slot loop: an ordinary directory, mode exactly
`0700`, owned by this manager, by `lstat` so a link is refused as itself
rather than resolved. An `lstat` that FAILS is a bounded refusal too -- a door
promising a typed answer owes one even when the filesystem will not answer.

### [P1] One constant, one answer

I exported `RUNTIME_FILE = 0o640` and kept `VOLATILE_FILE = 0o600` beside it
"as decision history", and the suite asserted both. That is two
authoritative-looking modes for one file, and a future caller reaching for the
established name would have recreated the exact defect with a constant that
said it was the contract. The reviewer's framing is the right one: decision
history belongs in the append-only finding; an exported constant is an
executable claim about what is true NOW.

`VOLATILE_FILE` is now `0o640` and `RUNTIME_FILE` is gone. The literal case
asserts one mode.

### New negative recovery cases, each refused before re-registration

`refuses_recovery` asserts both halves every time: the typed refusal, and that
`live_secret(BEARER)` is still false afterwards. A refusal that had already
re-registered would leave a live value no `Delivery` owns -- the shape this
module's own fourth review found.

    a widened root (0770)          refused
    a substituted root (symlink)   refused, as itself
    a root that cannot be lstat'd  refused, driven by an untraversable parent
    a slot mode widened (0644)     refused
    a slot mode narrowed (0600)    refused
    a link where the slot was      refused

Removing `_proved_root` fails the three root cases; run and restored.

### One case skips, and the reason is measured

The group-drift arrangement skips: on this host `chown(2)` answers `EINVAL`
for EVERY gid, including ones this process belongs to, so a foreign group
cannot be arranged at all. The skip message says so with the errno rather than
"cannot arrange".

WHAT THAT MEANS FOR THE gid COVERAGE, stated plainly rather than left for a
reader to infer. The configured group here equals the manager's primary group,
so `fchown(handle, -1, gid)` is a no-op that succeeds and the sandbox never
exercises a real group CHANGE. What is proved is that the call is made with
the ruled operands, on an empty descriptor, before the write, and that the
resulting slot carries the configured gid. A deployment whose workspace group
differs from the manager's primary group is where that step does real work.

### [P1] Terminal evidence

Real-container gate, by exact selectors, bounded transcript preserved at
`evidence/docker-readability-gate.txt`:

    test_the_execution_runtime_can_actually_READ_its_credential ... ok
    test_a_runtime_without_the_ruled_group_cannot_read_it ... ok
    Ran 2 tests -- OK

Both use `--rm` and neither depends on the unrelated global-litter assertion.
I did not remove the 23 pre-existing `baton-runtime.start-*` containers; they
were created 2026-08-30 around 14:00, the count was 23 before my runs and 23
after, and removing containers is destructive and not mine to judge.

Unit sweep, after this round's changes:

    test_credentials, test_claude_agent, test_oci, test_intake,
    test_attempts, test_sessions, test_secrets, test_dogfood_operator,
    test_ended_runtime_adoption, test_refused_session_cleanup,
    test_failed_start_destroy, test_lifecycle_composition
    -> 1071 tests, OK (3 skipped)

Whitespace check clean.

## 2026-08-31 — third implementer round (`baton.claude`, W52800 impl claim)

Answering `review-2026-08-31T15-45-28Z.md`. Both live findings are corrected;
its third finding is the one its own 15:52Z correction superseded, and the fact
it asked for is recorded below rather than re-measured.

### [P1] The live `0600` prose is gone, and the historical `0600` prose is not

Four live descriptions contradicted the ruled contract. Each now states the
ruled `0640` slot in the configured workspace group under the `0700`
manager-only root:

- `credentials.py`, `materialize`'s ordering docstring, step 3 — said the
  bearer "reaches a 0600 file under a 0700 private root";
- `credentials.py`, `adopt`'s read-back comment — said "reading this manager's
  own 0600 file is not publishing it", and now names what `_proved_slot` has
  just proved rather than a mode nothing writes;
- `launch.py`, beside `READ_ONLY_FILE` — said credentials "have the opposite
  mode: 0600 under a 0700 root", which is the one place a reader looking at the
  world-readable launch document is sent to for the contrasting rule; and
- `test_credentials.py`, `test_the_required_modes_are_exactly_these` — its
  comment still described the superseded two-constant arrangement, saying
  `VOLATILE_FILE` was decision history that nothing creates a slot at,
  immediately above the assertion that it is `0o640`.

The reviewer named three; `launch.py` is the fourth and is the same defect, so
it is corrected under the same ruling rather than left for a later round.

WHAT DELIBERATELY STAYS. `credentials.py`'s module docstring, the rationale
above `VOLATILE_FILE`, and `test_credentials.py`'s
`test_a_delivered_credential_is_readable_by_its_ruled_group_only` docstring all
still discuss `0600` — each explicitly as the superseded behaviour and why it
was wrong. `test_a_restrictive_umask_cannot_narrow_the_ruled_mode` also names
`0600`, as the mode a `0o077` umask would silently produce; that is a live
hazard description and is accurate. The `0o600` arrangement in the drift case
is a spoiler, not a contract.

### [P1] Owner and group drift are now driven, on any host, without privilege

`test_a_slot_whose_mode_gid_or_owner_drifted_is_refused` named three fields and
arranged one and a half: there was no owner-drift case at all, and its group
case called `chown(2)`, which answers `EINVAL` on this host for every gid
including ones this process belongs to, so that subtest skipped. Two of the
four fields `_proved_slot` compares were undriven.

Split, so each case arranges what it can honestly arrange:

- `test_a_slot_whose_mode_or_kind_drifted_is_refused` keeps the real-filesystem
  cases — a widened `0644`, a narrowed `0600`, and a symlink where the slot
  was — because an unprivileged owner can really do all three.
- `test_a_slot_whose_owner_or_group_drifted_is_refused` controls what
  `os.lstat` ANSWERS for exactly the one slot path, which is the boundary
  `_proved_slot` decides on, and drives `st_uid` and `st_gid` drift
  deterministically. Nothing depends on privilege to give an inode away. The
  helper delegates every other path to the real `os.lstat` — `adopt` proves the
  ROOT through the same call, and a blanket substitution would be arranging a
  different test — and the real `os.lstat` is restored before the discard runs.
- `test_the_drift_arrangement_can_actually_fail` measures the substitution
  itself: a wrapper that quietly returned the honest answer would make both
  cases above pass against an implementation that compares nothing. It requires
  the drifted uid to differ by exactly one with mode and gid untouched, the
  root's answer to be unchanged, and the same delivery to adopt cleanly and
  re-register the bearer once the substitution is gone.

Both new cases still assert the second half `refuses_recovery` exists for:
`live_secret(BEARER)` is false after the refusal, so the refusal landed before
the read.

SHOWN TO FAIL FIRST. With `or found.st_uid != os.getuid() or found.st_gid !=
gid` removed from `_proved_slot`, `RestartAdoptsOnlyAnExactAgreement` reports
`FAILED (failures=2)` — both new subtests, `ContractRefusal not raised`. The
comparison was restored and the class is green again.

### [P1, superseded] The inventory fact, linked rather than re-measured

Per the review's 2026-08-31T15:52Z correction, W54182 owns the hours-long
inventory defect and makes it non-gating here. Its `FINDING.md` preserves the
terminal result: one discovery-tree run completed in 2,376.290 seconds with 22
failures and 5 errors, and a retry held the ACP turn to its two-hour deadline.
That is the fact this Work links; no aggregate run was made in this round.

THE DELTA QUESTION IS NOW CHEAP, so it is answered rather than deferred. W54182
also corrected the inventory's runtime, so the scan takes seconds. Measured on
this tree: the two new public `workspace_group` operands ARE new receiving
entries — `('caller', 'credentials.py:CredentialHome.materialize',
'workspace_group')` and the same for `adopt` — and both are unowned by the
inventory's rules, taking `test_every_receiving_entry_has_an_owning_validator`
from the 131-entry baseline recorded in W48697 to 133. They are validated in
code: `_reader_group` refuses anything that is not the nominal
`WorkspaceGroup` and then calls `check_workspace_group`. That is a
hand-written refusal rather than a `boundaries.<kind>` call, which is why the
inventory cannot see it — the identical shape as the three sibling
`workspace_group` operands that predate this Work at `oci.py:run_vector`,
`oci.py:OciAdapter.__init__` and `workspaces.py:assignment_workspace`.

W48697 already owns that global debt, so the delta is recorded on its thread
(message 54844) rather than filed as new Work, together with the observation
that its module list does not yet include `credentials`. I registered no
ownership to move a count; W48697's approver ruling forbids exactly that.
The separate probe-side debt is W54802.

### Verification, with the exact commands

From `v12/python`:

    PYTHONPATH=src python3 -m unittest tests.manager.test_credentials \
        tests.manager.test_claude_agent
    -> Ran 160 tests, OK, no skips (was 158 with 1 skipped)

    PYTHONPATH=src python3 -m unittest -v \
        tests.manager.test_credentials.RestartAdoptsOnlyAnExactAgreement
    -> Ran 12 tests, OK, no skips (was 10 with 1 skipped subtest)

    PYTHONPATH=src python3 -m unittest tests.manager.test_launch \
        tests.manager.test_text_sweep tests.manager.test_secrets
    -> Ran 126 tests, OK

    the scoped whitespace check over the three changed files -> clean

The skip the previous round reported honestly is gone, because the coverage no
longer needs the host to do something the host refuses to do.

### State

Plan step 3's requested correction is complete. Awaiting review; passing back
rather than closing.
