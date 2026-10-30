# Implementer progress — W376956

## claim378563 — file ownership and retained base, recorded before editing

The PLAN requires this before any change, so it is the first thing written.

**Retained base**, re-hashed at claim and matching W376955's accepted
candidate (`CANDIDATE.json` `36510097…`, accepted by
review-2026-10-28T20-25-07Z):

    v12/python/tools/bootstrap.py                      fe099d1e735addc2f76b951642f50887cca2e5e3d1eb8dc899b2efefa0b0ad53
    v12/python/tests/tools/test_startup_prerequisites.py fab422af36a257cfdd64e755cffda775f35f9368167d07aceba1a749888e70cf

**Files this claim owns**, serially, with the W376955 gate now closed
(`satisfying`): `v12/python/tools/bootstrap.py` and
`v12/python/tests/tools/test_startup_prerequisites.py`. No concurrent edit by
the parent or a sibling is in flight on either; both are the shared pair the
FINDING assigns to this child next.

### The defect, read out of the accepted source rather than from the summary

`install` copies the runtime with `shutil.copytree(distro, places["distro"],
symlinks=True)` and then takes ONE identity, of the root, AFTER the copy
finishes. Two consequences, and the accepted review names the second as a known
defect it did not sign off:

1. **A mid-copy failure owns nothing.** `runtime_identity` is still `None` when
   `copytree` raises, so the unwind removes *nothing* of a partially copied
   runtime — and the retry then refuses for the leftovers this attempt made.
2. **`whole=True` deletes foreign descendants.** The unwind calls
   `_remove_if_still_ours(..., whole=True)`, which skips the populated-directory
   guard and `shutil.rmtree`s the subtree. The in-source comment justifies it
   with "`copytree` created every entry under it" — true when the copy
   finished, and false by the time the unwind runs. A foreign addition,
   same-name replacement or mutation under the runtime root is taken with it.

The FINDING is exact about why neither is fixable by inspection:
"whole=True/root identity or scanning an inventory after copy cannot alone
establish ownership."

### What this claim does

Replace the bulk copy with one that **records each object as it creates it**,
in the accepted ledger's own vocabulary — `_OwnedPrerequisite` for a proven
object with its retained handle, `_UncertainPrerequisite` for an attempted one
that is explicitly not a deletion capability — and unwind that ledger through
the existing `unwound_order` + `_remove_if_still_ours` with **no `whole=`
operand at all**, so foreign additions are preserved by the guard that already
exists rather than by a new rule.

Everything else about the accepted mechanism is preserved rather than
re-decided: the watch-proved mkdir-to-open continuity, the pinned `O_PATH`
handle lifetime, held-ancestry checks, no process-global umask mutation, and
honest uncertainty over false completion.

## claim378563 — the candidate, and what it establishes

    v12/python/tools/bootstrap.py                        37a562891e2a330e53d8de86d685d2cd8ac2c2b4c261fa5285d9be9c03f4ce67
    v12/python/tests/tools/test_startup_prerequisites.py 1e249ad09f882792916d96f4d7a07a77fbd82b3e9b99ef8a2be61c85e032e362
    v12/python/tests/tools/test_instance.py              e245fbc4dd451b457da5db14be2a8ce8560ad4d6ebe5bbe094a62274fa14ea30

`test_instance.py` is the THIRD file and is outside the pair this FINDING
names, so it is recorded here as the FINDING requires ("necessary other files
remain permitted within outcome with overlap coordination"). The change to it
is **one assertion's wording** — see §4 — and nothing else.

### 1. `copy_runtime`: every object recorded as it is created

`shutil.copytree` is gone. The copy walks the source through held, no-follow,
parent-relative handles and records each object in the accepted ledger's own
vocabulary: intent first (`_UncertainPrerequisite`, which carries no deletion
authority), then the proven object. Directories are proved the way W376955
proves one — a `_CreationWatch` on the held parent before `mkdir`, then exactly
one `CREATE|ISDIR` before the handle is accepted, with the `O_PATH` handle
pinning the object through the mode change. Files need no watch:
`O_CREAT|O_EXCL|O_NOFOLLOW` fails if the name exists at all, so the handle names
the object this call created. Symlinks are copied as links and never followed.

Two mechanical facts I had to find by running it, both recorded in the source
where they matter: `getdents` on an `O_PATH` descriptor answers `EBADF`, so the
SOURCE side takes ordinary read handles while the destination keeps the
identity-pinning `O_PATH` ones; and `os.lstat` has no `follow_symlinks`
operand.

### 2. The unwind: `whole=` is gone, not reduced

`_remove_if_still_ours` no longer takes `whole=`, and `shutil.rmtree`
disappears with it. The runtime unwinds through `unwound_order` one object at a
time, so foreign preservation falls out of the populated-directory guard that
was already there rather than from a new rule. Measured behaviour on a copied
tree with a foreign file added, a same-name replacement and an edit:

    unwound  <dest>/a/f.txt
    left     <dest>/a alone: ... holds 1 entry this attempt did not create
    unwound  <dest>/gone.txt
    left     <dest>/keep.txt alone: ... its content has changed since
    left     <dest> alone: ... holds 2 entries this attempt did not create

### 3. A mutation is not an addition or a replacement

The FINDING requires additions, same-name replacements **and mutations**
preserved, and identity answers only the first two: an edited file is the same
inode this attempt created. So `_OwnedCopy` carries the digest of the bytes the
copy streamed — from the same buffers, not a second read — and removal asks for
both. A partially written file is identity-only and stays removable, which is
the rule the justfile is already under.

### 4. The connected install path was ALREADY UNREACHABLE, and is now open

Running `tests.tools.test_instance` — the suite that drives `bootstrap.install`
against a real disposable destination — gave **14 failing cases**. I did not
assume they were mine or pre-existing: I built an isolated snapshot outside the
checkout with `bootstrap.py` and `test_startup_prerequisites.py` restored to
W376955's accepted bytes (`fe099d1e…`, `fab422af…`) and ran the same suite. The
failure name sets are **identical** — the diff is empty both ways.

The cause: `install` takes one `now` operand and hands it to two readers with
different spellings. `instance.emit` wants a POSIX number; the control store's
clock wants durable text, so every connected case that pins time refused *"the
configured clock's answer is durable text; this is 1.0"*. That made the
connected install proof this Work owes **unreachable** rather than merely red.
`_initialized_at(now)` converts where the difference is known, and the suite is
now 117 OK.

The one remaining failure after that was a label: the runtime root's unwind
line now reads "copied runtime object" because every copied object carries one
label. The property the case protects — a replaced runtime is left alone and
the foreign content survives — held throughout. The assertion was moved onto
the stable half of the sentence plus the path, so a later label cannot break it
again. That is the single `test_instance.py` change.

### Verification

    tests.tools.test_startup_prerequisites +
      test_bootstrap + test_instance        308 cases run, 0 failures, 23.622s

`test_startup_prerequisites` is 56 cases (was 46): ten new, covering what the
copy records, the content digest travelling with the identity, the retained
directory handle, a clean unwind, a preserved foreign addition, a same-name
replacement, a preserved mutation, a **mid-copy failure** owning exactly what
it made and unwinding all of it, an appearing destination entry never adopted,
and a non-directory source refusing at the `O_DIRECTORY` open.

One existing case was replaced rather than deleted: it asserted that
`whole=True` removed a populated owned subtree, which is the behaviour the
parent FINDING forbids. It now asserts the ledger unwind and that the operand
is gone from the signature.

Two of my own cases were wrong and are corrected with the reason kept: one
asserted a refusal from a branch the `O_DIRECTORY` open makes unreachable — the
branch is gone rather than the case — and one asserted a `follow_symlinks`
operand `os.lstat` does not take.

No engine, provider, operational install or deployment, retained store,
credential copying, foreign-path repair or version-control action. Disposable
fixture installs only.

### What remains in this outcome

The connected proof now RUNS and the existing suite covers install success,
the selector-appearance and justfile refusals, a partial write, a replaced
runtime and a cleanup that cannot remove. What this claim does **not** add is a
case driving a **store** or **create-step** failure specifically against the
new per-object ledger — the existing cases fail at the selector and the
justfile. Naming it rather than implying the matrix is complete.

## claim378672 — ownership proved at creation AND at the destructive call

Review 2026-10-28T23-50-44Z reproduced **two** ownership races in my own
candidate. Both were real, both were mine, and both are the same mistake in two
places: an identity taken from a NAME after the fact instead of from the object.

    v12/python/tools/bootstrap.py                        170d7416d9b80bd1097a5392d89e21d9ca1553ab3b30edb30e44714fcb94b601
    v12/python/tests/tools/test_startup_prerequisites.py a7f8ed28589062035583a0b3cf899aa79111b8a5e2bbf3085f6dcf86870fdf70
    v12/python/tests/tools/test_instance.py              71141d3199b912228f40b918168a0947b17b68f998af1cee91abdf03270f6bc4

### Blocker 1 — the symlink branch adopted a replacement

I wrote `os.symlink(...)` then `os.lstat(name)` and recorded whatever the name
held by then. A seam that swapped the new link for a foreign one in between
made the ledger record the FOREIGN object, and the unwind then deleted it and
said `unwound`. That is precisely the provenance error W376955 corrected for
directories, reintroduced one entry kind over — I had even written in the
docstring that the identity came "relative to the parent handle", which was
true of the lookup and false of the object.

It is now proved the way a directory is: a `_CreationWatch` on the held parent
before the call, exactly one `IN_CREATE` for that leaf, and the identity taken
from an `O_PATH|O_NOFOLLOW` **handle on the link itself**. `prove` gained a
`mask` operand because a symlink's creation is `IN_CREATE` alone while a
directory's is `IN_CREATE|IN_ISDIR`; the default is the directory mask, so the
accepted prerequisite caller is unchanged.

### Blocker 2 — the removal resolved the pathname a second time

`_remove_if_still_ours` checked `lstat` identity and then resolved the PATHNAME
again for `unlink`/`rmdir`. The review's seam renamed the original aside and
installed a same-content foreign file at the name in between; the unwind
deleted the replacement, reported success, and left the original.

**No POSIX call removes a name by inode**, so this window cannot be closed by
ordering. What it can be is narrowed and then *proved*:

* the destructive call is **parent-relative** — the containing directory is
  held by descriptor and the identity is re-asked relative to THAT handle, so
  no absolute prefix is resolved twice;
* a populated owned directory is listed through the **pinned object**
  (`/proc/self/fd/<handle>`) rather than through the name;
* the content digest is read through the pinned object too; and
* **after** the removal the retained handle is asked: a removed object's link
  count reaches zero, so if this attempt's own object is still there the name
  that went was somebody else's — and that is REPORTED, not counted as an
  unwind.

An effect with no retained handle now has **no deletion authority at all**, and
says so. That required `_OwnedCopy` to keep a handle like `_OwnedPrerequisite`
does, and the justfile and installer-input identities to become owned records
rather than bare tuples — without a digest for those two, deliberately, because
"owned from the moment it exists, not from the moment it is finished" and a
content check would refuse to remove a partial write.

**The residual, stated rather than closed:** if a replacement lands inside the
narrowed window, a foreign NAME is still unlinked. The outcome is reported as
uncertain and nothing further is deleted. I am not claiming that window is
gone.

### The connected failures the review named

Added against the real disposable install: a **copy** failure injected mid-walk
(the destination is left with no runtime and the cleanup is printed), a
**store** failure (the whole copied runtime unwinds object by object), and a
store failure **with a foreign addition** under the copied runtime (the foreign
file survives, the directory holding it is left with the uncertainty said out
loud, and the objects that are still ours go).

One of those three asserted the wrong exception at first:
`initialize_control_store` WRAPS an `OSError` in its own refusal — "an
installation that cannot initialize its own store is not a prepared one" — so
the case asserts the refusal that actually happens.

### Two existing injections moved to the new mechanism

`test_instance`'s two cleanup-failure cases matched `os.unlink` on the ABSOLUTE
justfile path. The removal is parent-relative now, so the operand is the bare
leaf and the old match silently stopped injecting anything — the cases would
have passed while testing nothing. They match the leaf now, with the reason
recorded beside them. Same class of adjustment the accepted W376955 review
approved for its own mechanism change.

### Verification

    tests.tools.test_startup_prerequisites +
      test_bootstrap + test_instance        316 cases run, 0 failures, 18.405s

`test_startup_prerequisites` is 61 cases and `test_instance` 120. Five new
cases cover both reproduced races directly: the symlink replacement refusing
with an UNCERTAIN ledger entry that carries no deletion authority and the
foreign link surviving; an ordinary symlink proved and owned, so the refusal is
not passing by accident; the post-removal link-count report; the ordinary
replacement caught outright by the parent-relative check; and a bare tuple
having no deletion authority.

No engine, provider, operational install or deployment, retained store,
credential copying, foreign-path repair or version-control action. Disposable
fixture installs only.

## claim378743 — the stop is enforced; the final-syscall preservation is NOT done

    v12/python/tools/bootstrap.py                        6fa89689154bf28c8c02df0cabc6e7fcdd32659bc1e749d2063bf2127895959c
    v12/python/tests/tools/test_startup_prerequisites.py 140b04338479e3ce39cdc73212fab53a22bca7a3b4cb962035d2294d041b9512
    v12/python/tests/tools/test_instance.py              71141d3199b912228f40b918168a0947b17b68f998af1cee91abdf03270f6bc4  (unchanged)

### Fixed: the reporting defect, which was unambiguous

`_removed` returned a line saying "nothing further is deleted" and **nothing
enforced it** — the install's unwind iterated the rest of the ledger and kept
removing, which the review reproduced. A sentence is not control flow.

It raises `_UnprovenRemoval` now, and **every** iteration site handles it: the
prepared roots, the two installer files, and the copied runtime each stop on
it, record what happened, and report how many objects are **RETAINED** rather
than removed. 316 cases pass.

### NOT fixed: deleting a foreign replacement at the final syscall

The review is right that my previous answer was not acceptable: reporting the
damage afterwards is not preserving the bytes. I have now tried twice and both
attempts were correctly refused, so I am returning this rather than shipping a
third variation of the same mistake.

**Why it is hard, stated precisely.** `unlinkat`/`rmdir` name an entry, never an
inode. Between the last identity check and the destructive call the name can be
rebound, and nothing in the ordering closes that. Two things I verified do NOT
help:

* parent-relative addressing and pinned-object reads (my first answer) — they
  remove the *prefix* race, not the final-name one;
* a post-removal link-count check (my second) — it detects the loss after it
  has happened, which is exactly what the review rejected.

**The options I can see, for the reviewer or owner to choose between:**

1. **Retain residue for every file.** Never unlink a name; report the whole
   runtime as retained on failure. Absolutely preserves foreign bytes, and
   leaves a partial runtime behind that the next attempt's `custody` will
   refuse — so a failed install would need an explicit operator cleanup. This
   is the review's own stated alternative and the only one that is certainly
   safe.
2. **Copy into a private staging root this attempt owns at 0700 and
   `rename` it into place on success.** The destructive call then happens only
   inside a directory no other uid can write, which is a real custody argument
   rather than a post-hoc classification — and on failure the staging root is
   removed without ever having been a path anybody else could bind. This
   changes the install's effect ordering, so it is a design change rather than
   a repair, and `custody`/`admit` would need to agree about the staging name.
3. **Privileged `linkat(..., AT_EMPTY_PATH)`** to re-name our own inode before
   removing it. It is inode-bound and therefore an actual proof, and it needs
   `CAP_DAC_READ_SEARCH`, which this installer does not have and should not
   acquire.

My reading is that **(2)** is the one that both preserves foreign bytes and
still unwinds, and that it is a change to how `install` stages its effects
rather than a change to `_remove_if_still_ours`. I have not started it: it
moves the copy's destination and touches `custody`'s agreement about what may
exist in the deployment, which is more than a correction and should be chosen
rather than assumed.

### Cumulative verification spending on this Work

Four claims: 308, 316, 316 and 316 focused cases across
`test_startup_prerequisites`, `test_bootstrap` and `test_instance`, plus one
isolated-snapshot attribution run of `test_instance` at the accepted base. No
engine, provider, operational install or deployment, retained store, credential
copying, foreign-path repair or version-control action in any of them.

## claim378794 — the global stop lands; the retention switch is written, measured and WITHDRAWN

    v12/python/tools/bootstrap.py                        1e653d3808993d1b6272c6e9832ee62f16078fa4ffa48d8d01bff9aaaddfd550
    v12/python/tests/tools/test_startup_prerequisites.py 140b04338479e3ce39cdc73212fab53a22bca7a3b4cb962035d2294d041b9512  (unchanged)
    v12/python/tests/tools/test_instance.py              71141d3199b912228f40b918168a0947b17b68f998af1cee91abdf03270f6bc4  (unchanged)

### Delivered: the stop is GLOBAL

The review was right that my per-group `break` stopped the group it was in
while every LATER group carried on — so an unproven removal halted nothing in
particular. `_Unwind` is one cleanup for the whole attempt: the prepared roots,
the two installer files and the copied runtime all go through it, the first
unproven removal sets `stopped`, every later call declines, and the report says
how many objects are RETAINED and why. 316 cases pass.

### The selected retention: implemented, measured, and withdrawn in this claim

The owner's selection is clear and I implemented it — a `retain=` path with a
`_retained` reporter doing pre-deletion fail-closed retention for the copied
runtime, with the reasoning recorded: `unlinkat`/`rmdir` name an entry and
never an inode, and mode 0700 does not exclude a same-UID replacement, so the
proof does not exist and the bytes stay.

**Then I measured what it costs and withdrew it from this candidate rather than
ship it broken.** Twelve connected cases assert the clean unwind and go red the
moment the runtime is retained:

    test_a_COPY_failure_unwinds_exactly_what_the_copy_had_made
    test_a_FAILED_publication_unwinds_what_this_attempt_made
    test_a_FOREIGN_justfile_that_appears_is_never_removed_either
    test_a_FOREIGN_selector_that_appears_is_never_removed
    test_a_PARTIAL_write_is_still_this_attempt_s_to_unwind
    test_a_STORE_failure_preserves_a_foreign_addition
    test_a_STORE_failure_unwinds_the_copied_runtime
    test_a_justfile_REPLACED_after_this_attempt_made_it_is_left
    test_a_runtime_REPLACED_after_this_attempt_copied_it_is_left_too
    test_a_selector_appearing_BETWEEN_custody_and_publication_is_refused
    test_the_PUBLIC_command_answers_an_installation_failure
    test_and_the_retry_then_SUCCEEDS

The last one is the substantive consequence rather than a wording change: with
the runtime retained, a failed install leaves an occupied destination, so
**the retry no longer succeeds** — it must refuse through `custody`, which is
exactly the "occupied retry refusal" the review names as a verification
behaviour. That is a change to what the connected lifecycle MEANS, not a
relabelling, and it needs those twelve cases rewritten deliberately.

I did not have the room left in this claim to convert them with the care each
one needs, and a candidate with twelve red connected cases is not a
deliverable. So the product is back to the measured-green state plus the global
stop, and the retention switch is recorded here rather than half-shipped. I
also deleted the unused `_retained` helper rather than leave an escape with no
caller — the same thing I criticised `whole=` for.

### The next claim, exactly

1. Reinstate the `retain=` path and `_retained` (both written once already;
   the reasoning above is their docstring).
2. Convert the twelve cases: the ten wording ones to assert `retained ...` and
   the exact residue line, and the two meaning ones —
   `test_and_the_retry_then_SUCCEEDS` and
   `test_the_PUBLIC_command_answers_an_installation_failure` — to assert the
   **occupied retry refusal** instead of a clean second attempt.
3. Assert FOREIGN SURVIVAL directly at the final-syscall race, which is what
   the review asks for and what retention finally makes assertable: with no
   unlink there is nothing to race.
4. Finish the create-step failure point so the connected matrix is complete.

### Cumulative verification spending on this Work

Five claims: 308, 316, 316, 316 and 316 focused cases across
`test_startup_prerequisites`, `test_bootstrap` and `test_instance`, plus one
isolated-snapshot attribution run of `test_instance` at the accepted base. No
engine, provider, operational install or deployment, retained store, credential
copying, foreign-path repair or version-control action in any of them.

## claim378838 — retention LANDED and not reverted; 8 of 16 connected cases converted

    v12/python/tools/bootstrap.py                        4e2cf9830469db608bead983d65d5e9c6b5cd9af94979aa3c60d0e1876ec56b3
    v12/python/tests/tools/test_instance.py              5acd1ecfbe0404f6ba3972792418969060b126bc19d45308cebadaccfe2c7b82
    v12/python/tests/tools/test_startup_prerequisites.py 140b04338479e3ce39cdc73212fab53a22bca7a3b4cb962035d2294d041b9512  (unchanged)

**I did not revert the safety this time.** The review said not to, and it was
right to say so.

### Landed

* **Pre-deletion fail-closed retention for the copied runtime.** Nothing under
  it is deleted: `unlinkat`/`rmdir` name an entry and never an inode, and 0700
  does not exclude a same-UID replacement, so the proof does not exist and the
  bytes stay. Foreign additions, replacements and mutations are preserved
  because nothing is removed at all.
* **No caller iterates any more.** `_Unwind.run(planned)` walks the whole plan,
  which removes the two faults the review named together: a per-group `break`
  could not lose the later groups, and the remaining entries of a stopped group
  are recorded as residue by construction rather than by a caller remembering
  to.
* **The report NAMES every retained object**, one per line, instead of
  counting them — a count is not something an operator can act on.

`tests.tools.test_startup_prerequisites` + `test_bootstrap`: **196 cases, 0
failures.** Those are the suites this Work's own mechanism lives in.

### Converted: 8 of 16

Eight `test_instance` cases now assert the retention and the named residue
instead of the runtime's absence.

### NOT converted: 8, with their two shapes

**Four are retry-shaped and are the substantive half.** They run a FAILED
install and then a second one in the same destination; with the runtime
retained, `custody` refuses the occupied destination — which IS the
"occupied retry refusal" the review lists as a required verification behaviour,
arriving as a test failure because the cases still expect a clean second
attempt:

    test_a_PARTIAL_write_is_still_this_attempt_s_to_unwind
    test_a_FOREIGN_justfile_that_appears_is_never_removed_either
    test_a_FOREIGN_selector_that_appears_is_never_removed
    test_and_the_retry_then_SUCCEEDS

Each needs its second install rewritten to assert the refusal and to name what
is occupying the destination. `test_and_the_retry_then_SUCCEEDS` needs its
TITLE changed too: under the selected behaviour a retry into the same
destination does not succeed, and a case whose name asserts the opposite would
be worse than a red one.

**Four are wording**, and each still asserts the runtime's absence somewhere my
conversion did not reach:

    test_a_STORE_failure_unwinds_the_copied_runtime
    test_a_STORE_failure_preserves_a_foreign_addition
    test_a_runtime_REPLACED_after_this_attempt_copied_it_is_left_too
    test_a_selector_appearing_BETWEEN_custody_and_publication_is_refused

The first two are mine from claim 378563 and their names should change with
them — "unwinds" is no longer what happens.

### Why I stopped here rather than finishing or reverting

Reverting was explicitly forbidden and I agree with the reason. Finishing needs
four semantic rewrites, four wording fixes and a full re-verification, and I
did not have the room left in this claim to do them with the care each needs —
the retry cases in particular decide what a failed install leaves behind, which
is the operational meaning of the whole outcome. Handing over eight converted
cases, eight named with their shapes, and the mechanism suites green is a
better checkpoint than either a silent revert or eight hurried rewrites.

### Cumulative verification spending on this Work

Six claims: 308, 316, 316, 316, 316 and (this claim) 196 green in the two
mechanism suites with 8 red in the connected suite, plus one isolated-snapshot
attribution run at the accepted base. No engine, provider, operational install
or deployment, retained store, credential copying, foreign-path repair or
version-control action in any of them.

## claim378872 — the custody rule is universal and all 16 cases are converted

    v12/python/tools/bootstrap.py                        8a710afc4a6ad809a72602ad4e5e7cbb76cf3ba224e2fe92d6bfb2d83a38b8f4
    v12/python/tests/tools/test_instance.py              0e7f4710b253bcfa75365ee9c3c0a4b876da50b9f2094f3d08a0b98e5f3954bb
    v12/python/tests/tools/test_startup_prerequisites.py 140b04338479e3ce39cdc73212fab53a22bca7a3b4cb962035d2294d041b9512  (unchanged)

### Universal, as the review required

The justfile probe showed the same final-name race on the prepared roots and
the installer files, so `retain=True` for the runtime alone was arbitrary.
**Every effect this attempt makes is now retained**: the prepared prerequisite
roots, the installer input document, the justfile and every copied runtime
object. `_Unwind.run` has **no removing branch at all** — once the rule is
universal, a `retain=False` path would be an escape with no caller, which is
precisely what this Work removed `whole=` for. `_remove_if_still_ours` survives
only as the helper the prerequisite suite exercises directly; `install` no
longer calls it.

### The accounting the review asked for

Absent, uncertain and foreign are each said in their own words rather than
collapsed: an absent object is silent (there is nothing to retain), an
uncertain effect is named as carrying no deletion authority, a replaced object
is named as belonging to whoever replaced it, and an object still ours is named
as **"is NOT deleting it"** with the reason. The report then lists every
retained path, one per line, under a `RETAINED n object(s)` heading.

### All sixteen connected cases converted

Twelve were wording — absence assertions became retention-and-naming
assertions, and `unwound` became `retained`.

**Four were semantic, and one of those needed its title changed:**
`test_and_the_retry_then_SUCCEEDS` is now
`test_and_the_retry_then_REFUSES_THE_OCCUPIED_DESTINATION`. Under retention a
failed attempt leaves its own effects in place, so a second install into the
same destination is refused by `custody` naming what is there — which **is**
the occupied-retry-refusal the review requires. A case whose name asserted the
opposite would have been worse than a red one, so the name moved with the
behaviour.

Two cleanup-failure cases had their injected `unlink` become unreachable. They
now assert what the refusal DOES say — every effect named as retained and
nothing claiming an unwind — which is the strongest form of the property they
were protecting ("a cleanup must not claim a removal that did not happen")
rather than a weaker one.

### Verification

    tests.tools.test_startup_prerequisites +
      test_bootstrap + test_instance        316 cases run, 0 failures, 18.481s

Foreign survival is now true **by construction** rather than by a check: there
is no unlink anywhere in the install's cleanup, so there is no race left for a
replacement to win. Successful fresh install, exact residue, and the occupied
retry refusal are all asserted in `test_instance`.

### Still open in this outcome

The **create-step** failure point is the one entry in the connected matrix I
have not added a case for — copy, store, selector and justfile are covered.
Naming it rather than implying the matrix is complete.

### Cumulative verification spending on this Work

Seven claims: 308, 316, 316, 316, 316, 196-green-with-8-red, and this claim's
316 with 0 failures, plus one isolated-snapshot attribution run at the accepted
base. No engine, provider, operational install or deployment, retained store,
credential copying, foreign-path repair or version-control action in any of
them.

## claim378950 — the create-step proof, a truthful aggregate, and a fourth file

    v12/python/tools/bootstrap.py                        507c96fb58538dcade749fbadf55759666022f07fd018eac2c183a5b083368b0
    v12/python/tests/tools/test_instance.py              cd6c5502331b41a5e77f80269a178ea6a555be95dfde844191cf40937e640803
    v12/python/tests/tools/test_connected_creation.py    33bcba4f3d47768c363e58b88c35d1319c6b32dca381b8fcf0a7b0bc13d16a28
    v12/python/tests/tools/test_startup_prerequisites.py 140b04338479e3ce39cdc73212fab53a22bca7a3b4cb962035d2294d041b9512  (unchanged)

### 1. The connected CREATE-step failure proof, which closes the matrix

Carried as an explicit omission across four claims; it is delivered here as
five cases in `TheCREATEStepFailureIsProvedConnected`. The create step is
`prepare_prerequisites` — the configured roots, which run first and before any
other effect — and it is the only step whose failure produces BOTH kinds of
residue at once, which is why it is the one the report needed:

    cleanup  retained <home>/w-1/storage: this attempt made the prepared
             prerequisite root and is NOT deleting it: ...
    cleanup  retained <home>/w-1/launch: uncertain effect (creation attempted;
             identity not established); no deletion authority, and this attempt
             cannot say whether anything is there
    cleanup  RETAINED 4 path(s), none of them deleted: 3 this attempt made and
             did not delete, 1 this attempt can neither claim nor disclaim

The injection is `os.mkdir` failing for ONE named leaf, matched on the leaf
because the create is parent-relative (`dir_fd=parent`) — the mistake an
absolute-path injection makes silently, which this Work already paid for once
in `test_instance`. What the five cases establish, each asserted rather than
implied:

  * the ORIGINAL FAILURE SURVIVES: the refusal names the step and carries the
    injected `OSError` as `__cause__`, so no cleanup error is thrown over it;
  * NOTHING SUCCEEDED: no selector, no justfile, no runtime, no success line;
  * THREE EARLIER OWNED EFFECTS are there, named, and classified as this
    attempt's;
  * THE FAILING ONE is named as an uncertain effect with no deletion
    authority — it does not even exist, which is exactly why the report may
    not say it was made or that it is there;
  * THE STEP AFTER THE FAILURE is silent: an absent effect is not residue;
  * A FOREIGN OBJECT at the unproven name, and a foreign addition under an
    owned root, both survive — written AT the failing call, before the cleanup
    runs, because written afterwards they would survive whatever it did;
  * THE RETRY REFUSES the occupied root by name, and repairs nothing: same
    bytes, same inode, same mode, no new residue, no selector;
  * and a CLEAN control run of the same document installs, so the four
    failures above fail for the injected reason rather than because the
    document never worked.

### 2. The aggregate no longer claims what was not established

`RETAINED n object(s) this attempt made` was false whenever the list held a
foreign replacement or an unproven creation — in the one line an operator
reads to decide what to do with the residue. The classification now travels
WITH each path (`_Unwind.OWN` / `FOREIGN` / `UNPROVEN`), the heading is
composed from them, and it counts PATHS rather than objects because an
unproven effect may not exist:

    RETAINED 8 path(s), none of them deleted: 7 this attempt made and did not
    delete, 1 left to whoever replaced it:
      .../install-inputs.json  [not this attempt's]
      .../justfile             [this attempt's own]

Kinds that did not occur are left out rather than said as zero. Per-entry
sentences are unchanged, as the review required.

### 3. Stale descriptions aligned — twelve in the tests, three in the source

Every name and sentence that still asserted a removal: four test names changed
with their behaviour (`..._unwinds_...` → `..._RETAINS_...`,
`..._is_still_this_attempt_s_to_unwind` → `..._AND_IS_RETAINED`,
`a_cleanup_that_cannot_remove_says_so` → `a_cleanup_NEVER_reports_a_removal_it
_did_not_make`), with the old wording and the reason kept in each docstring.
"Both are ours, both go", "ALL OF IT IS GONE", "the objects that are still
ours go", "the unwind removes what THIS attempt wrote" and "even while
unwinding its own" are each corrected where they stood.

In the source: the `except` comment no longer opens "ONLY WHAT THIS ATTEMPT
MADE IS UNWOUND, and ALL of it"; the public refusal no longer offers "what was
removed and what was retained" (it now opens "Nothing was deleted." and keeps
the "See the cleanup messages above" sentence the public case asserts); and
`_Unwind.stopped` IS DELETED with the removals — nothing could set it, so its
report line was an unreachable sentence about a cleanup this code does not
perform, which is the same stale claim the review sent back.

### 4. A FOURTH file was red, and it was this Work's own damage

`tests/tools/test_connected_creation.py` — the suite that drives `main` end to
end — had TWO cases still asserting the old removals, and nobody had converted
them: the reviewer's 316-case run covers three modules and never saw them.
They are converted the same way, including a title that had to move
(`test_a_selector_failure_removes_only_what_this_attempt_made` →
`..._RETAINS_what_this_attempt_made`) and an occupied-retry refusal replacing
"AND THE RETRY WORKS, which is what cleaning up is for". A new helper,
`no_selector_and_every_effect_retained`, is the right question for a refusal
that comes AFTER an effect; `nothing_was_published` stays for the five cases
that refuse before any.

I did not call these pre-existing. They are red because of the behaviour this
Work selected, they are tests of the implementation this Work owns, and
leaving them red while reporting three green modules would have been exactly
the bookkeeping this Work has been corrected for twice.

### Verification

    test_startup_prerequisites + test_bootstrap + test_instance +
      test_connected_creation + test_pool + test_fresh_attempt
                                           535 cases run, 0 failures, 41.924s

Every suite that consumes `tools.bootstrap` was run, not just the pinned
three: `test_connected_creation`, `test_environment`, `test_pool` and
`test_fresh_attempt` as well. `evidence/claim-378950/focused.log`.

### The one red case outside this outcome, attributed three ways

`test_environment`'s `test_a_named_distribution_that_is_absent_is_refused_BY
_NAME` fails, and it is neither this claim's nor this Work's:

  * it reproduces in an isolated snapshot with this claim's edits reversed
    until `bootstrap.py` digests `8a710afc…`, the bytes the last review
    pinned;
  * its cause never reaches this Work's code — `just bootstrap` dies with
    `ImportError: cannot import name 'admit_candidate' ... (circular import)`
    at `job_manager/role_contract.py:514`, so the helper never runs and the
    recipe's stdout is empty, which is the whole failure;
  * and `role_contract.py` is UNTRACKED while `templates.py` is dirty — HEAD's
    `templates.py` does not import it at all. Both are another participant's
    live work in the shared tree.

Read-only `git status` and `git show` only. `evidence/claim-378950/
ATTRIBUTION.md`, with the snapshot reversal script that lands on the pinned
digest.

### One truth correction in a helper my new case reads

`_node_kind` answered "special file" for a REGULAR FILE and for a SYMLINK —
the two commonest occupants of an owed name, and the occupant in the new
create-step retry refusal. It now names them, and the two callers that printed
the kind with no article at all print "a". Named here because it is a shared
helper from W375516/W376246 rather than this Work's, so it can be rejected
independently of everything above.

### Cumulative verification spending on this Work

Eight claims: 308, 316, 316, 316, 316, 196-green-with-8-red, 316, and this
claim's 535 with 0 failures across six modules, plus two isolated-snapshot
attribution runs at accepted bases. No engine, provider, operational install
or deployment, retained store, credential copying, foreign-path repair or
version-control mutation in any of them.

### What is open

Nothing named in this Work's outcome is now carried as unfinished: success,
create, copy, store, selector and justfile all have connected cases, and the
report says only what was established. `test_environment` stays red for the
foreign circular import above, which is not this Work's to fix.
