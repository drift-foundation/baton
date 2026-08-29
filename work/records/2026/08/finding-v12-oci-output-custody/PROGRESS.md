# Progress

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-27 — claimed; PLAN 1, the W6634 revalidation

Claimed W26283 at seq 26319. This is the successor Work I asked for while
holding W6636: that round found W6634 closed non-satisfying with no successor,
so freeze, collect, destroy and positive absence were unreachable on certified
code. The approver ruling authorized this provider.

PLAN item 1 is "revalidate the W6634 spike against current contracts", and the
finding is explicit that **provisional code is evidence, not accepted
implementation**. So this is a search for what is wrong, not a confirmation of
what is right.

### The contracts still say what the finding says they say

Checked against the frozen `worker-control-1.0` schema rather than against the
W6634 dossier:

| pinned | current tree |
| --- | --- |
| `completionManifest` — assignment_ref, disposition, outputs | present, `unevaluatedProperties: false` |
| `resultManifest` — requires `completion_manifest_digest`? | **optional**, and the code treats it so |
| `outputDescriptor` / `outputConstraints` | present; `link_policy` is `const: "forbid"` |
| `contentManifest` / `contentEntry` | present, entries/entry_count/total_bytes/tree_digest |
| W19784 owns assignment identity | unchanged; consumed, not redefined |

### Six of the seven obligations are met by the provisional code

Read in full rather than sampled:

- **bounded, no-follow, nonblocking read of the worker output** —
  `_read_without_following` opens `O_RDONLY|O_NOFOLLOW|O_NONBLOCK` and checks
  `S_ISREG` on the *descriptor*, not the path;
- **exact manifest comparison** — shape by the shipped validator, then
  `assignment_ref` against this attempt's, then §12 rule 15 both ways;
- **digest from the bytes opened** — recomputed over the read body;
- **live-secret rejection** — `check_no_durable_secret` runs over each staged
  file's *content*, decoded leniently so a binary file cannot be the way past;
- **atomic publish** — private name, `fsync`, `os.replace` onto `sealed.json`;
- **replay above every state read** — the committed record is consulted before
  the worker's envelope, and is bound to six members of the request so one
  attempt's stored answer cannot settle a different operation.

### [P1] The seventh does not hold: staging reopens by path

`_staged` copies each measured entry with a plain `open(source, "rb")`.
W6631's measurement is race-safe — it descends by opened directory identity and
opens every file `O_NOFOLLOW` relative to that descriptor — and the staging copy
throws that away by resolving a path string again.

**Proved, not inferred.** Two harms, both driven against the real code:

1. **Host material reaches custody.** After the measurement, renaming a
   measured subdirectory and putting a symlink in its place makes the copy read
   through the link: custody ended up holding a file from outside the workspace
   entirely. The double measurement afterwards refuses the *result*, but only
   after the bytes were read, scanned and written.
2. **One `mkfifo` hangs the manager.** Replacing a measured regular file with a
   FIFO makes `open` block forever. A 12-second probe timed out. This is
   exactly the failure `_read_without_following` added `O_NONBLOCK` to prevent
   for `output.json`, reintroduced one function away.

This is the same defect class this module has already fixed twice — once for
the completion envelope, once inside the walker, whose own comment records that
"a no-follow open of the FINAL file does not stop a raced ANCESTOR from
becoming a symbolic link". Staging is the third place it appears, and it is the
place the acceptance names directly: *"Symlinks, non-regular files, path
escape... fail closed"* and *"the sealed manifest describes the
manager-custodied bytes, not a path later reopened from worker storage."*

### What that implies for the fix

Re-opening safely would still be two opens with a window between them. The
measurement already reads every byte through a descriptor it proved; staging
should write *those* bytes rather than fetch them again. That closes the window
by construction instead of by comparison, and it is what the acceptance means by
custody describing bytes rather than a path.

The traversal belongs to `workspaces` (W6631) — sealing's own docstring warns
that "a second walker here would be a second thing to keep true" — so the
one-pass measure-and-copy goes there as an additive function, with the §13
secret rule staying in `sealing`, which owns it.

## State

Revalidation done. Implementing PLAN items 2–3 next.

## 2026-08-27 — PLAN 2–5 implemented

Evidence: `evidence/w26283-2026-08-27-custody-provider.txt`.
Reproduction: `evidence/w26283-pre-fix-reproduction.py`.
Harness: `evidence/w26283-mutation-harness.py`.
No Git history or index was mutated.

### The fix: the bytes written are the bytes measured

Re-opening *safely* would still be two opens with a window between them.
`workspaces.copied_manifest` measures and copies in **one** no-follow pass, so
the window does not exist rather than being checked for. It lives in
`workspaces` because that module owns no-follow traversal and `sealing`'s own
docstring warns that "a second walker here would be a second thing to keep
true"; the §13 secret rule stays in `sealing`, which owns it, and crosses as the
`admits` operand — applied *before* the write, so refusing means the bytes never
became custody.

That retired the double measurement. Comparing two digests was how a moving tree
was detected, and a single pass leaves nothing to move *between*. What remains
is a verification of the **write** — a short write, a full device — which is a
different question and a cheap one.

Declared ceilings are now enforced *as the pass runs*, so an oversize tree stops
at the entry that crosses the line instead of being copied whole and refused
afterwards. Two ceilings, two refusals, and the difference is not cosmetic: this
build's own `MAX_*` are policy, a delivery's declared limits are that delivery's
integrity — callers already depend on which one they get.

### The repository's own rules caught two things I did

Neither was a review finding; both were the v12 gate refusing my work.

- `sealing.py` imported `shutil` for one `rmtree`. The manager's ruled
  dependency set does not include it. Replaced with a public
  `workspaces.discard_tree` over W6631's existing removal — also the stronger
  answer, since `rmtree` has followed links out of a tree before and that module
  already owns not doing that.
- `copied_manifest`'s four parameters were not declared operands.
  `test_dependencies` keeps a closed registry whose comment says "an entry here
  is a claim somebody has to make deliberately", so the four are added with the
  reason each is an operand rather than bookkeeping.

And the parallel-runner registry — which I added a module to during W6636 —
refused the new real-engine suite until it was registered serial, for the same
two reasons the three before it are.

### The real-engine suite the acceptance asks for

*"A real OCI worker output is copied into manager custody only after exact
manifest validation"* — and no suite established that. `test_sealing` drives
forty refusal paths against trees a fixture wrote and an envelope a fixture
composed, which is the right way to cover them and is **not** the same claim: a
fixture agrees with the manager by construction.

`tests/manager/test_output_custody_engine.py` (8 cases) runs the reference
worker in a real container, lets it write its material and publish its own
envelope, then seals what it wrote through the real adapter. The container, the
image, the worker program, the bytes, the envelope and the engine asked about
quiescence are all real. Custody is asserted to be outside the roots a container
may mount, read-only, and to re-measure to exactly what the sealed manifest
claims.

Its cleanup is deliberately **not** `ignore_errors`. The container runs as a
fixed non-root uid, so a directory *it* creates cannot later have files removed
from it by the host — `test_worker_container` lives with that and leaves trees
in `/tmp`. This suite pre-creates the declared roots host-owned, so removal is
possible, and asserts the tree is gone.

### Measured by removal

Twelve mutations, including one that restores W6634's reopening copy verbatim so
the first mutation reproduces the **defect** rather than merely disabling
something. The real-engine suite is in the measurement too.

**The first pass found four unestablished, and one of them mattered:**
live-secret bytes were not scanned by any case at all. The scan was in W6634's
code with a comment explaining it, and replacing it with a no-op left every
suite passing. The acceptance names it outright — *"live-secret bytes fail
closed"* — so **a guard nothing observed was standing in for a named acceptance
clause.** Two cases now, one over a real worker's own output, plus one proving
the rule is about a live *registration* rather than about the characters.

The other three were mine: nothing drove a pre-existing entry at the
destination, nothing lowered this build's own ceilings to observe them, and the
write verification was unobservable until the *collaborator* was faked rather
than the code under test.

**All 12 mutations caught.** Source fingerprinted before and after.

### One existing case replaced, and it needs a second opinion

`test_sealing`'s `test_a_tree_that_changes_between_measuring_and_custody_is_refused`
drove a change *between two measurements* and asserted a `collection` refusal.
That window no longer exists, so asserting a refusal for it would be asserting
something false. It is replaced by
`test_a_tree_that_moves_during_the_pass_cannot_reach_custody`, which asserts the
stronger property the original protected — a worker that rewrites a file the
instant after it is read does not get those bytes into custody — plus two new
cases driving the harms directly.

That is an edit to an existing test's expected behaviour. W6634 is closed
non-satisfying and this Work owns adopting only what meets the finding, but the
judgement is mine and review should check it rather than take it.

### Gates

- `test_sealing` + `test_workspaces` + the engine suite — all green
- full v12 tree — **1554 tests, 7 failures**
- failures — **seven**, the accepted baseline: six in
  `test_boundary_inventory` and one in `test_contracts_inventory` for
  `check_input_pair`, the W19784 leftover reported during W6636 that still has
  no owner

### What this provider still does not own

Credential delivery, the shared quiescence/removal/settlement crossing, restart
adoption, reconciliation and orphan convergence remain outside it, per the
finding's confirmed boundary. Nothing here reached for any of them.

## State

PLAN items 1–5 done. Passed for independent review rather than closed.

## 2026-08-27 — independent review, changes applied

Reviewer: `baton.codex`, `review-2026-08-27T22-00-40Z.md`. Evidence:
`evidence/w26283-2026-08-27-review-corrections.txt`. The damaged handoff
evidence is kept as history rather than rewritten. No Git history or index was
mutated.

### The [P1] the review found, and why my own revalidation missed it

`workspaces._read_exactly` opened worker-controlled entries
`O_RDONLY | O_NOFOLLOW` and proved the descriptor was a regular file
afterwards. `O_NOFOLLOW` refuses a final symbolic link and says nothing about
a name that was a regular file when the walk LISTED it and is a FIFO by the
time the open runs — and that open blocks waiting for a writer, so the
descriptor proof below it, the one guard a racing replacement cannot defeat,
is never reached. One `mkfifo` in worker-owned storage stalls the manager.

**The obligation list I checked in PLAN 1 says "bounded no-follow nonblocking
read".** I found it established and moved on. It was established at ONE of the
two places this manager reads worker-controlled bytes —
`sealing._read_without_following`, for `output.json`, which carries the flag
and a comment recording that without it "the case covering this rule does not
terminate". The walker's file read never had it. I checked the obligation
rather than the sites, so a rule this module had already learned once and
written down was absent one function away.

Worse: my own handoff evidence says of the COPY defect that it was "the SAME
failure `_read_without_following` added `O_NONBLOCK` to prevent for
`output.json`, reintroduced one function away". I wrote that sentence about
the copy and did not turn it on the read.

**Why my two FIFO cases did not catch it.** Both create the pipe BEFORE the
walk lists it, so `entry.is_file(follow_symlinks=False)` refuses it without
opening it. They establish that the walk refuses what it SEES. The interval
that matters is between the entry being accepted and its name being opened,
and nothing drove it.

### What was done

`O_NONBLOCK` at the open; the descriptor-level regular-file proof unchanged
and still the thing that refuses. The regression interposes on the REAL walk
at the yield boundary — so the entry really was accepted as a regular file by
the code under test — and BOUNDS ITSELF with `SIGALRM`, because a regression
here is a hang rather than a failure and a hanging case takes the whole gate
with it. That bound is also what makes the new mutation measurable instead of
a 900-second stall. The reviewer's own `w26283-review-fifo-race.py` now
returns `integrity/path` instead of blocking, and the harness is **13 of 13
caught**.

### The other three corrections

- `sealed_result`'s docstring still opened with "THE MEASUREMENT IS TAKEN
  TWICE, and the second one is the point" — what the function did BEFORE this
  Work, contradicting both the implementation and `_staged` beside it. It now
  says the opposite, because the opposite is true.
- The handoff evidence's sections 3 and 4 were damaged by an unquoted heredoc:
  four backticked words ran as commands and left holes in the sentences they
  belonged to. The lost sentences are restored in the corrections file; the
  damaged file is kept as produced.
- `check_input_pair`'s inventory failure is no longer an orphan. **W26296 owns
  it**, bound to `finding-check-input-pair-inventory-follow-up`, and it is a
  live blocker of W6636. The evidence and PLAN both said it had no owner;
  that was true when written and is not now.

### One thing I got wrong in the coordination, not the code

The reviewer's [P1 policy gate] asked for `baton.slaw`'s case-specific
approval of the replaced `test_sealing` case. **It was already granted**, at
message 27064 in this Work's own thread, and this PLAN records it. I acted on
the review without reading the thread of the Work I had just claimed, re-asked
a settled question as M28300, and gated the Work on my own obligation.
Withdrawn at M28315. Only `baton.decide` can dispose it, so W26283 reads
`phase=block` until they do — a gate of my own making, named here rather than
left for the next reader to explain.

**And the gate cost more than a phase.** Moving to `block` RELEASED THE CLAIM
as well, because W38 makes `active` hold exactly when a Handler does. W26283
now reads `status=open, phase=block, handler=None, gate=M28300`, and every
exit is closed to me: a pass is the claimant's handoff and I am not the
claimant; blocked Work cannot be claimed; `phase to=queued` refuses because
"block leaves only through the gate-bound audited wake"; and `dispose` refuses
because the obligation is `baton.decide`'s. **One action clears it —
`baton.slaw` disposing M28300** — and the question it asked was already
answered at 27064.

The full handoff is recorded in the thread at M28350 so the review content is
not held hostage to my mistake. I did not go looking for a way around the
gate: the authority is right to refuse all four of those, and the lesson is
that `wait=true` is a workflow act and not a way of marking a message
important.

### Gates on the corrected tree

- `test_workspaces` 50, `test_sealing`+`test_workspaces` 95, the real-engine
  custody suite 8 — all green
- the custody harness — **13 of 13 mutations caught**
- the reviewer's `w26283-review-fifo-race.py` — exit 0, `integrity/path`
  returned where it used to block
- `tools/parallel_test.py` — 1510 tests, **6 failures, all in
  `test_boundary_inventory`**; `--phase serial` run explicitly (the runner
  stops before it when parallel fails) — 97 tests, 0 failures

**The accepted baseline is now SIX, not seven.** `test_contracts_inventory` is
green: the `check_input_pair` registration W26296 owns has landed. Checking it
against the tree rather than transcribing the review's correction is the only
reason that is known here.

## 2026-08-28 — the second [P1] in the same contract, and what it cost to see

Claimed W26283 again after `baton.slaw` disposed M28300. Read the thread FIRST
this time, then the whole record, then the new review, then the tree.

### The defect, stated as the reviewer stated it

A guard placed AFTER an unbounded operation is not a bound on that operation.
`_read_exactly` took one `fstat` size and then `_read_all` looped to EOF, and
`copied_manifest` consulted `len(content)` afterwards. On a file the worker
keeps appending to, "afterwards" never arrives: the read does not terminate,
so the ceiling that exists to refuse the file is not late — it is unreachable,
and the process grows for as long as the writer cares to write. The entry
ceiling had the same ordering and a milder version of the same harm: the file
it exists to decline was opened and held first.

**This is the SAME SHAPE as the [P1] I fixed yesterday**, which is the part
worth recording. The FIFO defect was a descriptor-level proof placed after an
open that could block, so the proof never ran. This one is a byte ceiling
placed after a read that could not end, so the ceiling never runs. I fixed the
first instance by making the open nonblocking and did not ask what else in the
same function was ordered that way — I treated it as a missing flag rather
than as a missing rule. `_read_all` was four lines below the flag I added.

### What was done

`_entry_ceilings`, `_byte_allowance` and `_byte_ceilings` are now the one
owner of both ceilings, and the ORDER is the point of the cut: the entry
ceilings answer with nothing opened, and the read is handed what is left of
the SMALLER remaining global/declared allowance and takes at most that plus
one byte. One byte past the line is what proves the line was crossed; reading
further is work the crossing already made pointless.

`_read_exactly`'s allowance is a REQUIRED keyword rather than a defaulted one.
A default would have made the unbounded reader reachable again by omission,
which is exactly how this defect survived the first correction.

`directory_manifest` was corrected with `copied_manifest`. It had the
identical late check one function above, and it is the pass that measures a
delivered input root — worker-controlled bytes on both paths. Fixing only the
custody copy would have left the same defect where the next reader would not
think to look for it.

The taxonomy did not move. Global `MAX_*` stays `policy/denied`, a delivery's
declared ceiling stays `integrity/limit`, and an equal crossing still answers
globally. The correction changed WHEN each ceiling runs, never which answer it
gives, and both equal crossings now carry a case that would fail if that
changed — previously only the ordinary crossings did.

### The regressions, and why they carry alarms

`ACeilingBoundsTheWorkItRefuses`, eight cases. Three assert that the crossing
file is NEVER READ, by interposing on `_read_exactly` and comparing the list
of files actually opened — an assertion about the answer alone cannot tell a
bound from a late verdict. Three drive a file that never stops growing: the
`os` name the module itself sees is replaced by a proxy that appends after
`fstat` returns and after every read, so the size measured is true when taken
and false one instruction later. That interposition replaces the MODULE's
`os` rather than patching the `os` module, so nothing outside the component
under test reads a different filesystem for the duration.

Those three bound themselves with `SIGALRM` for the reason yesterday's FIFO
case does: unbounded, they do not terminate, and a hanging case takes the
whole gate with it. The alarm is also what keeps the matching mutation
measurable instead of stalling the harness for its full timeout.

### The mutations

Three added — the entry ceiling moved back after the read in `copied_manifest`
and in `directory_manifest`, and `_read_all` ignoring the allowance it was
given. Each restores the ordering rather than deleting the guard, so a suite
that catches them is one that observes the ORDER and not just the refusal. The
four existing ceiling anchors were re-pointed at the shared helpers. **16 of
16 caught**, with the real-engine suite still in the measurement.

### The reviewer's evidence file, and the one thing I could not leave green

`evidence/w26283-review-read-bounds.py` is kept EXACTLY as the reviewer
produced it, unedited. Its byte probe passes as written — `9 bytes across 9
reads` at ceiling 8. Its ENTRY probe now raises `TypeError` instead of
reporting, because it interposes a three-parameter wrapper on `_read_exactly`
and the correction the review itself required gave that function its allowance
operand. I did not edit the reviewer's file to make it pass, and I did not
contort the signature to keep a test harness working — a byte budget smuggled
through the descriptor-and-name pair would have kept that wrapper green at the
cost of conflating identity with policy.

`evidence/w26283-read-bounds-corrected.py` is the same two probes with `**rest`
on that wrapper, plus a third the review's own harm description asks for and
the original could not express: the endlessly growing file. Exit 0, and it
reports what it measured rather than only that it passed.

### Gates on the corrected tree

- `test_workspaces` 57 (was 50), `test_sealing`+`test_workspaces` 103, the
  real-engine custody suite 8 — all green
- the custody harness — **16 of 16 mutations caught**
- `evidence/w26283-read-bounds-corrected.py` — exit 0: 9 bytes across 9 reads,
  `['a']` read before the entry refusal, endless growth refused
  `policy/denied` in 9 bytes
- `evidence/w26283-review-fifo-race.py` — exit 0, still `integrity/path`
- `tools/parallel_test.py` — 1518 tests, **6 failures, all in
  `test_boundary_inventory`**, the accepted baseline and none this Work's;
  `--phase serial` run explicitly because the runner stops before it when
  parallel fails — 97 tests, 0 failures

No Git history or index was mutated. Awaiting independent re-review.
