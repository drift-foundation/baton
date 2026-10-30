# Implementer progress — W376246

## claim376274 — all five confirmed defects corrected

Authorization: owner E375491, reviewer allocation E376246 (the serial first
slice of W375516). Read at claim: this child's assignment, the parent review
2026-10-28T18-45-16Z's confirmed findings, and the parent PROGRESS history I
authored. Base `f36bcd75ed22430355efe1b274b8f236cb591f6b`.

Candidate: `v12/python/tools/bootstrap.py`
`c5d93be47dcf90687e554f2aa61095ebe127b23362a5bf9294aba0e37fc032a6` and
`v12/python/tests/tools/test_startup_prerequisites.py`
`9bd178d56e3a0f3466b0f936186d336ceeda1200144004cdeb014fb4acbdc70c`.
`tools/instance.py` and `tools/stack.py` remain UNTOUCHED, and W375516's
second read-only validation slice is not started here.

### The five corrections

1. **A racing object is REVALIDATED, not accepted.** `FileExistsError` used to
   `continue`, so a link, a non-directory or an inaccessible directory
   appearing between the inspection and the `mkdir` was treated as usable. It
   now goes back through `_usable_root` and refuses — and it is never owned,
   so it is not unwound and not repaired.
2. **Every created component is owned.** `os.makedirs` creates missing
   parents, and only the leaf was recorded, so the unwind left every
   intermediate behind. `_components` answers the non-existent ancestors
   outermost-first, each is created and owned individually, and
   `unwound_order` answers them INNERMOST-FIRST for removal — which matters
   because the unwind now refuses to remove a populated directory, so a
   shallow-first order would report the whole tree as foreign and leave it.
3. **The mode is named, not inherited.** Under `umask 000` a prepared root was
   0777 — world-writable mutable state nobody asked for. `PREREQUISITE_MODE`
   is 0700, passed to `mkdir` AND applied afterwards because a creation mode
   is umask-filtered. Only the directory this call just created is chmodded;
   no existing root ever is.
4. **The unwind no longer takes foreign children.** It used `shutil.rmtree`,
   so a directory this attempt created that somebody else had since written
   into had THEIR content deleted — the one thing an exact-owned unwind must
   never do. An empty one is removed; a populated one is left and the
   uncertainty is reported, naming how many entries this attempt did not
   create.
5. **The report applies the same ancestor rule.** The observation and the
   preparation disagreed: a root under a linked parent refused at prepare and
   was reported as fine, so an operator could be told a deployment was ready
   that an install would refuse to make.

### Verification

    tests.tools.test_startup_prerequisites   28 OK  (was 24)
    tests.tools.test_bootstrap              135 OK  (no regression)

Four new cases drive exactly the review's blockers, and three existing ones
were corrected to the new contract with their reasons recorded: the owned set
now includes the intermediate; the unwind is driven in `unwound_order`; and
the replaced-root case takes its place from that order. The new cases are a
prepared root private under `umask 000`, a populated owned directory left with
their file intact, a racing symlink refused and not owned (driven by patching
`os.mkdir` to create the link in the window), and a linked ancestor reported.

### Remaining scope — W375516's second slice, not this one

Application-read-only STORE validation, the `tools/stack.py` command wiring,
and the connected disposable-install demonstration through the real command.
The child assignment says that slice waits on this acceptance, so it is
deliberately not started.

Cumulative verification spending on this prerequisite work: W375516
claim376006 read-only only; claim376067 two focused runs (155 tests);
claim376157 three focused runs; claim376216 read-only only, no run; this claim
three focused runs (28 prerequisite cases twice while they were driven to real
outcomes, plus 135 bootstrap). No operational install, live provider or
engine, deployment, retained-store mutation or credential copying; every store
and root is disposable. No Git mutation.

## claim376325 — returned with no further edit; five items, one a regression I caused

Review 2026-10-28T18-59-24Z. The tree is unchanged by this claim: `bootstrap.py`
`c5d93be4…` and the test `9bd178d5…` are exactly the claim376274 bytes.

**I CAUSED ONE OF THESE.** My non-empty guard in `_remove_if_still_ours` now
refuses to remove a POPULATED directory — and the copied runtime `distro/` is
populated and is entirely this attempt's, so generic cleanup leaves it behind.
That is a regression from my own last claim, not a pre-existing gap. The guard
needs to distinguish the two cases rather than treat every directory alike: a
subtree this attempt created WHOLE (the runtime) is removable, and a directory
whose CONTENTS are not ours (a prepared root somebody wrote into) is not.
An explicit operand at the call site is the honest way to say which.

The rest, as the next claim's work list:

1. **The post-`mkdir` `chmod` follows a replacement symlink.** It chmods BY
   NAME, so a racer replacing the new directory with a link has its foreign
   0755 target changed to 0700 and the replacement recorded as owned. It must
   be descriptor-bound: open the created directory `O_DIRECTORY|O_NOFOLLOW`,
   then `fchmod`/`fstat` the object this call made rather than the name.
2. **`chmod`/`lstat` `OSError` returns success silently.** Both `continue`, so
   a root that could not be made private is reported as prepared. It must
   refuse, and the created object must still be owned so the unwind can try.
3. **`_components` accepts a foreign object at an ancestor.** Discovery stops
   at the first existing path and never validates it, so a FILE at an
   intermediate is not refused where one at the leaf is. Every existing
   ancestor needs the `_usable_root` treatment, not only the immediate parent.
4. **The partial-copy identity is captured too late.** `runtime_identity` is
   set after `copytree` returns, so a copy that fails midway leaves the
   partial tree unowned. It must be captured as soon as the directory exists.

And the scope correction I accept: the **connected disposable-install proof**
(success plus create/copy/store/selector failure, races, nested creation,
foreign preservation, owned runtime cleanup, private access) belongs HERE per
this child's FINDING/PLAN and E376271 — only the read-only command and store
validation belong to W376254. My previous handoff placed it in the parent, and
that was wrong.

Verification spending this claim: read-only reading of the review and no run,
because nothing was changed.

## claim376352 — my own regression fixed; four findings and the proof remain

Candidate: `tools/bootstrap.py`
`cd69806cf4abc5dc88ee03ea4642cfa25076f8b0a9dd3d58c154f0d6b397d5d2` and
`tests/tools/test_startup_prerequisites.py`
`cdbd8aa190730c9ef7eeed675561ab23cea4c18daf49864e2091ba589c95b4c1`.

I fixed the one finding I introduced rather than leaving it in the tree while
the rest waits. `_remove_if_still_ours` takes an explicit `whole=` operand:
`whole=True` says the SUBTREE is this attempt's, which the copied runtime is
(`copytree` created every entry under it), so it is removed recursively;
without it the prepared-root rule is unchanged and a populated directory is
left with the uncertainty reported. The caller knows which it holds and says
so; the helper does not guess. `install` passes `whole=True` for the runtime
only.

Two cases drive both halves: a populated wholly-owned subtree removed, and a
prepared root with somebody else's file still refused.

    tests.tools.test_startup_prerequisites   30 OK  (was 28)
    tests.tools.test_bootstrap              135 OK  (no regression)

### Still open — the four findings and the connected proof

1. the post-`mkdir` `chmod` follows a replacement symlink; it must be
   descriptor-bound (`O_DIRECTORY|O_NOFOLLOW`, then `fchmod`/`fstat`);
2. `chmod`/`lstat` `OSError` returns success silently and must refuse, with
   the created object still owned;
3. `_components` accepts a foreign object at an existing ancestor — every
   ancestor needs the `_usable_root` treatment, not only the immediate parent;
4. `runtime_identity` is captured after `copytree` returns, so a partial copy
   is unowned; it must be captured as soon as the directory exists;

and the connected disposable-install proof — success plus create/copy/store/
selector failure, the races above, nested creation, foreign preservation,
owned runtime cleanup and private access — which belongs here, as the review
corrected me.

Verification spending this claim: two focused runs (30 prerequisite cases and
135 bootstrap). No operational install, live provider, engine, deployment or
retained-store action; no foreign chmod or repair.

## claim376381 — findings 1 and 2: creation is descriptor-bound

Candidate: `tools/bootstrap.py`
`483179752aab53cdbd1865688cf573102b2394ac17eae6abf9ac09a92217f4f7` and
`tests/tools/test_startup_prerequisites.py`
`633308c032ac4891875b3d932350bccfbfde6e0b1943e21b96d42b68ffa88e25`.

**Finding 1 — the post-`mkdir` `chmod` followed a replacement.** The mode was
applied with `os.chmod(part)` straight after the `mkdir`, so a racer swapping
the new directory for a link had its FOREIGN target chmodded from 0755 to 0700
and the replacement recorded as this attempt's. The created directory is now
opened `O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC` — which refuses the link
outright — and the `fstat`/`fchmod` that follow are about THE OBJECT THIS CALL
CREATED rather than whatever now answers to the name.

**Finding 2 — an error there returned success.** Both calls used to
`continue`, so a root that could not be made private was reported as prepared.
Both refuse now, and the directory is recorded as ours BEFORE the `fchmod`, so
the unwind can try to remove it however the function leaves.

Two cases drive them: a replacement injected between `mkdir` and the open,
asserting the foreign target's 0755 is untouched and the replacement is never
owned; and `os.fchmod` made to fail, asserting the refusal and that what was
created is still owned.

    tests.tools.test_startup_prerequisites   32 OK  (was 30)
    tests.tools.test_bootstrap              135 OK  (no regression)

### Still open

3. `_components` accepts a foreign object at an existing ancestor — every
   ancestor needs the `_usable_root` treatment, not only the immediate parent;
4. `runtime_identity` is captured after `copytree` returns, so a partial copy
   is unowned; it must be captured as soon as the directory exists;

and the connected disposable-install proof, which belongs here.

Verification spending this claim: two focused runs (32 prerequisite cases and
135 bootstrap). No operational install, live provider, engine, deployment or
retained-store action; no foreign chmod — a case now proves that.

## claim376409 — finding 3: every existing ancestor is proved a directory

Candidate: `tools/bootstrap.py`
`46b5b29d017f42643be01a2e2d9cfd7433861e1e777ef5ae8f0f2a39f27d1120` and
`tests/tools/test_startup_prerequisites.py`
`cdf5afd5cb6bee66224d64e46179293ecc90cb150c64c2a32962d958237c4c92`.

The realpath rule added earlier catches a LINK anywhere in the ancestry,
because `realpath` resolves all of them — but a plain FILE at an intermediate
resolves to itself, so it escaped the check a file at the leaf gets and the
`mkdir` beneath it failed with a bare OS error instead of this module's own
refusal. `_usable_root` now walks up from the parent to the first existing
ancestor and proves it is a directory, refusing with the object's kind named
and nothing created beneath it.

One case drives it: a file at `<home>/w-1`, asserting the refusal names "not a
directory" and "beneath another object's name", that the owned set is empty,
and that the foreign file's bytes are intact.

    tests.tools.test_startup_prerequisites   33 OK  (was 32)
    tests.tools.test_bootstrap              135 OK  (no regression)

### Still open — one finding and the connected proof

4. `runtime_identity` is captured after `copytree` RETURNS, so a copy that
   fails midway leaves the partial tree unowned; it must be captured as soon
   as the directory exists.

And the connected disposable-install proof — success plus create/copy/store/
selector failure, the races, nested creation, foreign preservation, owned
runtime cleanup and private access — which belongs here. Finding 4 changes
what `install` owns and when, which is the same contract that proof
establishes, so the two are one step rather than two.

Verification spending this claim: two focused runs (33 prerequisite cases and
135 bootstrap). No operational install, live provider, engine, deployment or
retained-store action; no foreign chmod or repair.

## claim376923 — returned retaining every open finding; no source edit

Review 2026-10-28T19-57-29Z. The tree is unchanged by this claim:
`bootstrap.py` `46b5b29d…` and `test_startup_prerequisites.py` `cdf5afd5…`
are exactly the claim376409 bytes. **I am not requesting continuation
permission** — it is already granted — and I am not claiming a finding count.
My E376429 "one finding remaining" statement was FALSE and is withdrawn.

### Every open finding, retained

**A. The post-`mkdir` open/`fchmod` adopts a foreign ORDINARY replacement.**
`O_NOFOLLOW` refuses a symlink but not a directory. A racer that swaps my new
directory for its own ordinary directory is opened normally, chmodded to 0700
and recorded as mine. `O_NOFOLLOW` was the wrong instrument for this half: the
fix needs creation provenance — compare `fstat(handle)` against a fresh
`lstat` of the NAME before any `fchmod`, refuse on mismatch, and state the
residual window honestly rather than implying the binding is airtight.

**B. An `open` PermissionError invents a replacement diagnosis and leaves the
root untracked.** My refusal says "something replaced it" for ANY `OSError`.
`EACCES`/`EPERM` is an access failure, not a replacement; `ENOENT`/`ELOOP`/
`ENOTDIR` suggest one. And the created directory must be recorded as owned —
flagged uncertain — rather than left untracked, which is the residue the
unwind exists to remove.

**C. `_remove_if_still_ours(whole=True)` deletes a foreign file added after
the copy.** `rmtree` takes whatever appeared since. The runtime's entry
inventory needs recording right after `copytree`, with removal only when the
current inventory is a subset of it and reported uncertainty otherwise.

**D. Partial-copy ownership** — `runtime_identity` is still captured after
`copytree` returns, so a mid-way failure leaves the partial tree unowned.

**E. The connected disposable-install outcome** — success plus create/copy/
store/selector failure, races, nested creation, foreign preservation, owned
runtime cleanup and private access, through the real command. The review is
explicit that the existing 168 green tests do not cover the reproduced
defects, so new regression coverage rides with each correction above.

### Why no edit this claim

A, B and C all change what "created by this attempt" means at the same two
call sites, and D changes it at a third; E is what proves them together. I did
not have the room to change that lifecycle and prove it, and four rounds of
fragments have been correctly refused here. The findings above are stated
precisely enough to start on A immediately.

Verification spending this claim: read-only reading of the review. No run,
because nothing was changed.
