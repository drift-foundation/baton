# Progress

Implementation has not started. Research evidence is in FINDING.md; the
assigned implementation author records subsequent checkpoints here.

## 2026-09-07 — baton.claude — the proof-only consumption gate

Claimed W105982 after the owner's nine-path approval and after W106896, the
access provider's reviewed checkpoint, closed satisfying. Revalidated its
accepted bytes first: `_prove_line_access` and `_provision_line_access` are in
`workspaces.py`, and the stable modes are the ruled `02775`/`0775`/`0664`.
State: **awaiting independent review.**

Eight of the nine approved paths changed; the ninth,
`tests/manager/test_private_line_access_engine.py`, is the provider's shared
serial module and needed no addition to carry this gate, so it is untouched
rather than edited for the sake of the list. No path outside the approved set
was written.

### What the correction is

The gap was a SUBJECT gap before it was a permission one. `custody._derived_root`
addresses `<storage>/<attempt>/workspace`, and a writer attempt is mounted at
the line checkout — so an ordinary receipt was accurate about directories that
had nothing to do with the tree the manager actually read, and it ran last
anyway. Naming the right tree is therefore most of the work, and proving the
manager can read it is the rest.

`review_cycles.consumption_subject` resolves WHICH line, from the store and
from nothing else: the attempt's own active writer at this exact generation,
that writer's line, the line's assignment binding, and the object pin the line
recorded when it was materialized. It derives the custody sibling the same way,
from the recorded line path, so the adapter's answer can be compared against an
independent derivation rather than against itself.

`workspaces.prove_line_consumable` proves access by PERFORMING the open. A mode
bit is a claim about a permission rather than the permission, and `os.access`
answers for a hypothetical; both are wrong the moment supplementary groups or a
read-only mount are involved. It walks no-follow at every component, counts a
symlink without following it, includes the private metadata because the
checkpoint profile reads the repository and not only the payload, and changes
nothing. A tree the manager cannot read is evidence, and the operator's mode
ruling is not this function's to re-decide.

`OciAdapter.prove_line_consumable` asks the three questions in order: the store
answers which line, the adapter's actual roots are compared against that answer
so a cross-wired map refuses instead of sealing somebody else's tree, and only
then is the filesystem opened. It re-resolves afterwards, because a traversal
takes real time and the durable state that authorized it is state another act
can move. It also holds the retained sibling outside the writer's own mount:
bytes the worker can still reach are not retained.

`review_driver.end_implementation` runs the gate after the stop and the
disposition and before the first completion read. After, because a proof taken
while the worker is still writing is about a tree that is still changing;
before, because a consumer that discovers the denial halfway through sealing
has already produced a partial account of somebody's work. `IMPLEMENTATION_ENDING`
gained `consume` in that position and cleanup is still last, which is exactly
why cleanup could never have been what made the line readable.

### One check removed rather than written

I wrote an exclusivity count — a line with two active writers is not one an
attempt may be sealed from — and then found `line_one_active_writer`, a UNIQUE
index over `line_writers(line_id) WHERE state = 'active'`. A second active
writer cannot exist to be counted, so the check was unreachable and is gone;
the dependency is pinned by a case that asserts the schema carries the rule, so
if it ever stops, the gate says so. That is this codebase's own correction and
it caught me the same way it has caught others.

### Verification

The five scoped modules are 345 tests, all passing. `tests/job_manager` is 390
and `tests/integration` 401, both passing. The whole `tests/manager` suite is
2735 tests with 10 failures, and every one is pre-existing: four are Docker
engine state from earlier runs, and six are `test_boundary_inventory`.

One of those six is worth reporting precisely, because it is NEW relative to my
earlier baseline note and I did not want to assert it away.
`test_every_declared_probe_reaches_its_named_boundary` names
`('adopted', 'review_cycles.py:writer_of', 'line_writers.writer_id')`. I proved
it is not mine by NEUTRALIZING my own addition — renaming `consumption_subject`
out of the module and re-running that single test, which failed identically —
and then restoring the file and re-running its suite green. That is the
before/after comparison the earlier composer review correctly said my evidence
lacked; it is available here because neutralizing my own function needs no Git
mutation. The entry belongs to the access provider's landing, not to this
candidate.

I also removed a second boundary owner while investigating: `consumption_subject`
briefly validated `line_writers.writer_id` itself before handing it to
`writer_of`, which already owns that identity and that row. One value with two
owners is what the inventory refuses, and the extra call is gone.

Candidate digests:

| Path | SHA-256 |
| --- | --- |
| `worker_manager/review_cycles.py` | `34f2310512b20b4860cdbeb218bf6d9c2e506314d0ce8419a3527f726f7782d0` |
| `worker_manager/workspaces.py` | `4148db65dd381b962c7cee25367af238824be6198d1bda70c9e5ed7427e255f6` |
| `worker_manager/oci.py` | `a5ee85189d9b68cc067908c93706fc61b9561f2b4d882f2c9ce50f37920389a0` |
| `job_manager/review_driver.py` | `78ddccdf39cf46882f72dbe12b7b1501322f7da7689eb071ac3012a5f5f4b7a1` |
| `tests/manager/test_review_cycles.py` | `2afbaea65992e8c7a4695ad6ddccb376b0336b889c4d78dd12a8e86adcde53bc` |
| `tests/manager/test_workspaces.py` | `660196eb8a881250261da9f5b9e0e799104409d4726bd94016c3f639b25daefa` |
| `tests/manager/test_oci.py` | `44301b30f600abb4ce24e8c7dfb7a515fbad5778f7282b0a13f4b5d80f6cd2b8` |
| `tests/job_manager/test_review_driver.py` | `2b759a9ad7ec3bb9042c4f137b36c68035c18be8e9d948caae40cf470526a1df` |

### What this candidate does not claim

No live runtime proof. The exact-image, dedicated-group execution the PLAN's
focused verification describes belongs to W105706 and is not performed here;
these are host fixtures, and a fixture that models a denied directory is not a
demonstration that the deployed identity is denied. No mode is repaired, no
custody receipt is written, no detach mechanism is adopted, and the ordinary
receipts still claim only the ordinary roots they were always accurate about.
W106673 remains an open experimental child, so this Work cannot close on this
candidate alone.

## 2026-09-07 — baton.claude — three refusal boundaries closed

Reclaimed after `review-2026-09-07T05-03-18Z.md`. All three probes in
`evidence/review_consumption_gaps.py` reproduced before I changed anything, and
all three were real.

**P1, checkpoint consumption.** The early adapter gate runs before sealing,
retention, publication and an EXTERNAL Authority fence, so re-resolving right
after that walk cannot protect the profile read at the far end — the probe
replaces the checkout during the fence call and gets a checkpoint frozen over
the replacement. `freeze_checkpoint` now re-reads the line row and re-proves its
recorded object immediately before `profile.freeze`, through one
`_consumable_line` helper, because a row loaded before an external call is a
memory rather than a fact. It asks about the LINE'S object identity and nothing
else, which is what lets it run after the checkpoint has legitimately revoked
the writer and what leaves the preparing/frozen replay paths exactly as they
were — one of the new cases proves an unchanged line still freezes and still
replays identically.

**P2, the granted principal.** `_same_assignment` compares Authority, Work and
generation; all three can agree while the attempt's assignment names a different
participant or principal from the one the writer was granted to. The accepted
launch boundary `_writer_access` already required both equalities, so a
consumption gate that did not was authorizing a subject the launch would have
refused. Both are compared now, at both resolutions.

**P2, the entry ceiling.** The bound was tested only for entries the walk OPENS,
so a trailing run of symlinks was counted and waved through however long it was.
Every entry is measured against the ceiling now; the target is still never
followed and no mode is touched.

**The two `__all__` entries are withdrawn.** PLAN does not presume new public
exports, so both helpers are private: `workspaces._prove_line_consumable` and
`review_cycles.consumption_subject` is out of `__all__`. The underscore form
matches `workspaces._prove_execution_workspace`, which `oci` already calls
across modules. **The rename means the reviewer's probe needs one line changed**
— it calls `workspaces.prove_line_consumable`. Run against the private name, all
three probes pass; my own regressions cover the same three behaviours under
`test_workspaces` and `test_review_cycles` so the coverage does not depend on
the probe file.

**The pre-custody driver-test baseline the review asked for** is at
`evidence/pre-custody/test_review_driver.py`
(`fc8aa8dc37decc5631dc6f64e66c7bbeecccfd55000e86a2de3fb1e9c95bcb9c`) with the
exact diff beside it at `test_review_driver.diff`. It was reconstructed by
inverting this candidate's three edits, and the diff shows what that is: two
removed lines, both halves of moving one `_Adapter` construction inside the
`with _endings()` block so the recorder could be passed to it. Everything else
is addition. No existing assertion changed.

Verification. The reviewer's three probes pass against the private name. The
scoped modules are 350 tests; `tests/job_manager` 390 and `tests/integration`
401 pass. The whole `tests/manager` suite is 2739 tests with the same 10
pre-existing failures as the previous round — four Docker engine state and six
`test_boundary_inventory`, including the one I proved is not mine by
neutralizing my own function.

Corrected digests:

| Path | SHA-256 |
| --- | --- |
| `worker_manager/review_cycles.py` | `e085f0a0020b23a08650e8b60db78e27bb5ee9d273ae89474099481462f0d377` |
| `worker_manager/workspaces.py` | `19ea613d2da8cf47f6a25bbad76372f1b91eae9b57130e017ddfee2e964d40b9` |
| `worker_manager/oci.py` | `101a2c1754cfb2ea7fc6e08783a902c4e944b33ed7b0189130aaf8c6ff79f566` |
| `job_manager/review_driver.py` | `78ddccdf39cf46882f72dbe12b7b1501322f7da7689eb071ac3012a5f5f4b7a1` |
| `tests/manager/test_review_cycles.py` | `5e24cc14c4fe134f23664229dda84736954d72b3f21dc1ebd2aae666fce961de` |
| `tests/manager/test_workspaces.py` | `8874973c44e83f1ccbf0c1a19fc3ac1953f220c9312d551ca0e9fe63175935d5` |
| `tests/manager/test_oci.py` | `44301b30f600abb4ce24e8c7dfb7a515fbad5778f7282b0a13f4b5d80f6cd2b8` |
| `tests/job_manager/test_review_driver.py` | `2b759a9ad7ec3bb9042c4f137b36c68035c18be8e9d948caae40cf470526a1df` |

Still not claimed: live runtime proof, which stays with W105706. W106673 remains
open, so this Work cannot close on this candidate alone.
