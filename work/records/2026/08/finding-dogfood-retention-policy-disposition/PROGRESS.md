# Progress

## 2026-08-30 — first implementer round (`baton.claude`, W51473 impl claim)

Done, green, and both halves refuted before they were kept. The correction is
operator-only: nothing in `baton_v12` changed.

### The operand

`retention_disposition` is a new required member of `GRANT_MEMBERS`, held by
`held_disposition` and refused in `preflight` beside the network and the
review route -- before anything is staged or started. It has no default and is
not derived from `retention_policy_digest`.

ONE VOCABULARY, IMPORTED. `held_disposition` reads
`worker_manager.RETENTION_DISPOSITIONS` and `_keeps_material` reads
`intake.KEEPS_MATERIAL`. A tuple spelled here would be a second vocabulary
that agrees until one of the two is edited -- and the one that matters is the
manager's, because it is what `decide_retention` enforces and what `_settle`
reads to choose the ending.

`_custody` now passes the held operand to `decide_retention`, and the record
keeps the manager's COMMITTED answer, as it already did.

### The half a literal swap would have missed

The FINDING is right that `retain` alone would have preserved the bytes and
left the command unresolved forever. `_ended_however` treated every cleanup
answer but `complete` as a failure, and the manager deliberately ends
`retained` whenever anything is kept -- "reporting kept material as cleaned up
would erase the reason it still exists".

So the EXPECTED ending is now derived, and derived from the COMMITTED decision
rather than from the grants or the record: `retained` when the committed
disposition keeps material, `complete` otherwise. An ending that does not
match is unresolved and the sentence names the committed disposition, so an
operator can tell which of the two lies happened -- material cleaned up that
policy said to keep, or material surviving that policy said to remove.

Positive runtime absence is still required for both. `retained` does not relax
it: the material staying is a fact about custody and the runtime being gone is
a fact about the engine.

### The keep is proved on the disk, after the removal

`_kept` opens every retained artifact's locator and requires a directory.
`_settle` discards the execution roots INSIDE the terminal transaction, so
this is the first moment "the candidate is still there" is a fact rather than
a plan. A keep whose locator is gone or whose scheme this operator cannot open
is unresolved -- reporting it resolved would be W39364's false clean ending in
a new place.

The locator is now part of the record. `evidence["custody"]` carries
`custody_locator`, `_CUSTODY_SHAPE` requires it and `_committed` compares it
against the manager's own intake row -- so the locator an operator reads is
the locator the manager committed, and `_kept` opens THAT rather than a path
recomposed here. It decodes with `_proposal_root`, the same owner `_derived`
uses, because two spellings of one path is the defect this dossier has now
recorded four times.

### Retry and replay stay exact

`_bound` holds the grants' `retention_disposition` against the record's
COMMITTED `retention.disposition`. It is not a flat evidence member, so the
generic `_RETRY_BINDING` loop cannot reach it, and leaving it out would leave
the one operand that decides which ending is expected free to differ between a
run and its retry. A record with no committed retention is not a disagreement:
`retry_handoff` refuses that separately and for a better reason.

An edited record still cannot mint a decision -- `_committed` replay-reads
`retentions_of` and compares the disposition, which it already did.

### Cases, each shown to fail first

Reverting ONLY the resolution rule fails
`test_an_intended_keep_ending_retained_is_resolved` for both keeping
dispositions and one direction of the mismatch case. Reverting ONLY the
operand back to the literal fails `test_the_grant_is_what_reaches_the_manager`
for `retain` and `quarantine`. Both were run and restored.

Injected (`test_dogfood_operator.RetentionIsAnOperatorDecision`, 11 cases):
the manager's vocabulary is the one used and not a copy; absent, empty,
near-miss and wrong-typed dispositions are refused by name; preflight refuses
before staging; the grant REACHES `decide_retention` for all three
dispositions; an intended keep ending `retained` resolves, for `retain` AND
`quarantine`, so nothing is reading `retain` by name; an explicit discard
ending `complete` still resolves; both mismatch directions are unresolved; a
keep whose material is gone and a keep whose scheme cannot be opened are both
unresolved; the positive `_kept` proof passes on a real directory; a retry
that disagrees with the committed decision is refused and one that agrees
proceeds.

Real Docker, no live provider
(`test_dogfood_retry_engine`, 2 new cases against the test-owned proposal
agent): a `retain` run resolves, ends `retained` with the runtime absent, and
leaves a candidate that is STILL READABLE after the command returns -- and the
case then performs the acceptance itself, diffing the retained candidate
against the measured input (`["added.py"]`) and rerunning the task's own
verification command outside the worker (exit 0). Its control proves an
explicit discard still ends `complete` with the tree gone, so the change
cannot have made every run retain.

### Verification

    tests.tools.test_dogfood_operator                    137 tests
    + arc_engine + retry_engine + parallel_runner
    + intake + workspaces + text_sweep + dogfood_image   360 tests, OK
                                                         (107s, real Docker)

Whitespace clean. `tools/` is outside the boundary inventory's scope, so the
new public `held_disposition` adds nothing to that backlog -- checked rather
than assumed.

### One thing a reviewer should look at

Three registered gates named the disposition for the first time
(`test_dogfood_arc_engine`, `test_dogfood_retry_engine`, and the operator
suite's fixtures). Each names `discard-after-intake` -- the behaviour they
were written against -- so what they prove is unchanged. The retry engine's
`world()` grew a `retention` parameter, which is what the new retained gate
varies.

## 2026-08-30 — second implementer round (`baton.claude`, W51473 impl claim)

Review [P1] accepted without qualification and closed. The reviewer is right,
and the sharp part of the finding is the part I should have caught: the
function's own comment said the locator was "PROVED to be openable" while its
only positive check was `os.path.isdir`, which performs a `stat`. A directory
at mode `000` passed it. The claim was stronger than the code -- the exact
failure this campaign keeps finding in other people's work and has now found
in mine.

### The proof is the act now

`_traversed` opens each directory with `O_RDONLY | O_DIRECTORY | O_NOFOLLOW`,
lists it on the descriptor, and stats every entry descriptor-relative. Each
step needs exactly what one bad mode withholds:

    000     `os.open` refuses                    -- no read
    r--     the descriptor-relative stat refuses -- no search
    --x     `os.open` refuses                    -- no read
    a file  `O_DIRECTORY` refuses                -- in the same act as the open

AND IT DESCENDS, because the documented uses do: `_changed_paths` walks the
whole candidate tree and the verification rerun executes with `candidate` as
its `cwd`, so a root that opens over a subtree that does not is still a
candidate the review contract cannot act on. Bounded at `MAX_KEPT_DEPTH`
64 -- the manager's own `workspaces.MAX_DEPTH` -- because a walk with no limit
is a walk somebody else decides the cost of, and this one runs over material a
worker wrote.

DESCRIPTOR-RELATIVE AND NO-FOLLOW, the same idiom `workspaces._emptied` uses
over the same kind of tree: a name resolved afresh at each step is a name
something else can move between the check and the use, and a link followed
here would be this operator proving something about a directory nobody
retained.

NOTHING IS MUTATED. No write, no create, no chmod -- a proof that changed the
material a reviewer is about to read would be a worse thing than the gap it
closes. There is a case that hashes the modes and sizes of the whole tree
before and after and requires them identical.

### Six new cases, four of which the old check passed

Reverting `_kept` to the `isdir` form fails exactly:

    test_a_retained_directory_that_cannot_be_opened_is_not_resolved
    test_a_retained_directory_that_cannot_be_traversed_is_not_resolved
    test_a_retained_subtree_that_cannot_be_opened_is_not_resolved
    test_every_retained_artifact_is_asked_about

The other two -- a locator naming a file, and the no-mutation proof -- pass
either way, which is correct and is why they are not claimed as regressions.

The first is the reviewer's reproduction, run rather than described. Every
fixture restores the mode in a cleanup, because a test that left a `000`
directory behind would make the tree harder to work in than it found it.

`_kept` also now asks about EVERY artifact rather than stopping at the first
failure: an operator reading this record is deciding what to do about their
kept material, and "the first one failed" is less use than knowing which.

### The reviewer's own path, against the fix

Their temporary reproduction was left in place per managed-turn policy, so I
ran the corrected `_kept` against it directly:

    file:///tmp/w51473-inaccessible.m9YE06
    -> "artifact 'proposal-1' was retained and its custody locator ... is not
        a directory this operator can open (PermissionError); a keep nobody
        can open is not a candidate anybody can review"

Left in place, untouched.

### Verification, including the rerun the review required

    tests.tools.test_dogfood_retry_engine (real Docker)     4 tests, OK (92s)
      -- including the retained gate, which still resolves, still leaves the
         candidate readable, and still performs the independent diff and the
         verification rerun after the command returns
    tests.tools.test_dogfood_operator                     152 tests, OK
    + arc_engine + retry_engine + parallel_runner
    + intake + workspaces + text_sweep + dogfood_image    375 tests, OK (107s)

Whitespace clean.

## 2026-08-30 — third implementer round (`baton.claude`, W51473 impl claim)

Review [P1] accepted and closed. Both halves were right, and the second half
is the one worth dwelling on: my POSITIVE fixture was an empty directory, so
the case that existed to keep the negative ones honest was locking a false
positive in. A proof is only as good as the thing it is proved against.

### Files are opened now, not stat-ed and skipped

`_traversed` opened and traversed DIRECTORIES and only `stat`ed everything
else. `filecmp.cmp` -- which is what `_changed_paths` runs -- OPENS those
files. So a regular file at mode `000` inside a perfectly traversable tree
passed a proof whose entire purpose is that the bytewise diff can read it.

`_readable` now opens each regular file `O_RDONLY | O_NOFOLLOW`
descriptor-relative and closes it. OPENING IS THE PROOF AND READING IS NOT
NEEDED: a zero-byte file is a legitimate member -- the first live attempt's
`change.patch` was exactly that -- so requiring a byte would refuse material
the contract allows. What is in question is permission, and `os.open` answers
it.

An entry that is neither a regular file nor a directory is now REFUSED BY KIND
rather than skipped. The diff reads regular files and walks directories; a
link, a fifo, a socket or a device is not something it can read, and the
manager's own copier refuses links at any depth -- so one in custody is a tree
this operator should not be calling reviewable.

Entry count is bounded at `MAX_SOURCE_ENTRIES` beside the existing depth
bound, for the reason the depth bound already had.

### `candidate/` is required, because both documented uses need it

The traversal alone admitted an empty proposal root: it opens and lists
perfectly while the verification rerun has no `cwd` and the diff has nothing
to compare. `_has_candidate` requires the fixed `CANDIDATE_TARGET` directory,
asked AFTER the traversal so a root this operator cannot read reports that
rather than reporting a missing member it was never able to look for -- and on
the SAME descriptor, because re-opening the root to ask the second question
would be asking about whatever answers to that name by then.

### The fixtures were the other half of the finding

`proposal()` now builds what `_derived` actually produces: `candidate/` with a
file below it and the three siblings beside it. It replaced the empty root in
the positive case, in the all-artifacts case and in the no-mutation case.

Four new cases, and reverting `_kept` to the second round's proof fails
exactly these four:

    test_a_retained_regular_file_that_cannot_be_read_is_not_resolved
    test_a_retained_proposal_with_no_candidate_is_not_resolved
    test_a_wholly_empty_retained_root_is_not_resolved
    test_an_entry_the_diff_cannot_read_is_refused_by_kind

The third is named separately on purpose: it is exactly what the previous
round's positive fixture was.

### Both reviewer reproductions, run against the fix

Left in place per managed-turn policy and asked directly:

    file:///tmp/w51473-unreadable-file.IPYbB6
      -> "... custody tree ... cannot be read (PermissionError); the
          documented independent diff opens every file in it"
    file:///tmp/w51473-inaccessible.m9YE06
      -> "... is not a directory this operator can open (PermissionError) ..."

Both untouched.

### Still narrower than rerunning the verification, deliberately

That already happened at `_derived`, over the same custody tree and before the
ending. What this answers is whether the ending left it usable. Running a
worker-influenced command a second time at the terminal boundary would be a
new act rather than a proof about an old one.

### Verification, including the rerun the review required

    tests.tools.test_dogfood_retry_engine (real Docker)     4 tests, OK (92s)
      -- the retained gate still resolves, still leaves the candidate
         readable, and still performs the independent diff and verification
         rerun after the command returns
    tests.tools.test_dogfood_operator                     159 tests, OK
    + arc_engine + retry_engine + parallel_runner
    + intake + workspaces + text_sweep + dogfood_image    382 tests, OK (107s)

The shared-suite ambiguity the review noted is gone: W51476 settled its
`_held_grants` fixture updates, so this run is attributable.

Whitespace clean.
