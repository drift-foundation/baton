# Bounded collection/custody correction — proposal, revision 2

baton.claude, W177936, revised under claim180580 on owner180577. **This is a
proposal. Nothing here is implemented.**

**Revision 2 supersedes revision 1 (`3e18b5e5…`) on two defects the owner
found, both real and both mine.** They are described in §2 rather than quietly
fixed, because each was a case of an assertion that would have looked like
evidence while proving nothing.

Evidence base, re-read at this claim: the operator walk
`operator-result-2026-09-15T18-29-34Z/walk-180078-operator-reported.json`
sha256 `d399a3a6705b3453007e6ff83aecb8ec23ce2704a3fb1e49ccc1adfabb62e3fb`,
the fixed-path result `…/metadata-180078-operator-reported.json`
sha256 `237d34b173cea22c7686e5c5d9dad66bf25f1e1e5d057e6b5ba7e77434109ffd`,
`review-2026-09-15T18-36-00Z.md`, and the accepted fixture at manifest
`5e789f4e3115b5eb9a7623772adf0a17aac3e45135afaa65bc11a35eb30e951f`.

## 1. What is established, and the one inference the fix turns on

Host collector: uid1000, gid1000, group1001. Inside `use-1/home`:

| count | type | uid | gid | mode | host readable | host searchable |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | directory | 1000 | 1001 | `0o2770` | yes | yes |
| 4 | directory | 65532 | 1001 | `0o2755` | yes | yes |
| **1** | **directory** | **65532** | **1001** | **`0o700`** | **no** | **no** |
| **3** | **regular** | **65532** | **1001** | **`0o600`** | **no** | — |
| 1 | regular | 65532 | 1001 | `0o644` | yes | — |
| 1 | symlink | 1000 | 1001 | `0o777` | — | — |

One real `opendir:EACCES`; 11 entries, depth 4; no bound reached; `use-2/home`
absent. **Setgid gave group ownership — everything is gid1001 — and setgid never
gives group permission bits.** The same distinction accepted R1 turned on at
178875, from the other side: there the manager had to produce a file the runtime
could write; here the runtime produces files the manager cannot read.

**The inference the fix depends on.** The runtime created *both* permissive and
restrictive objects. One umask cannot do that — umask only removes bits. And the
`0o700` directory carries gid1001 with **no setgid bit**, which a child of a
setgid parent inherits automatically; something chmodded it after creation. So
**the restrictive modes are explicitly set**, and a container umask — the
one-line fix — cannot work, because umask never adds bits back.

**Not established, and nothing below assumes it:** which directory produced the
EACCES, whether it contains the selected session, whether the three `0o600` files
include the session JSONL, or which original collection operation failed. The
original exception is lost.

## 2. The two defects in revision 1

**D1 — P1b would have made three absence claims vacuous.** Revision 1 said an
unreadable entry should be "recorded closed instead of raising". The fixture
asserts three *negatives* that are derived entirely from directory listings:
`unexpected-credential-entry` (home-wide), `project-key-ambiguous` (exactly one
project directory) and `foreign-session-state` (no other `.jsonl` under the
prefix). **An unenterable directory hides the names those claims are about**, so
tolerating it would have converted "we verified no foreign session and no
credential-shaped entry" into "we did not look" — while the export still said
the checks passed. Revision 2 draws the line at the right place (§3b).

**D2 — P1a did not distinguish the two turns, and would have broken accepted
R1.** Turn 2's home is **manager**-reconstructed: the controller creates the
restored session file with `private_file(target, raw, group=True, writable=True)`
at **`0o660`, owned by uid1000**, which accepted R1 at 178875 established as the
writable working copy. A turn-agnostic "relax the project directory and the
session file" would have aimed a chmod at that object — which uid65532 cannot
perform anyway (EPERM on a file it does not own), so the failure mode is a
*refusal in the wrong place* rather than a silent break, but the contract
violation was real and the intent was wrong. Revision 2 confines P1a to turn 1
and to runtime-owned objects, verified before the change (§3a).

## 3. The correction

### 3a. P1a — turn 1 only, runtime-owned only, verified through the descriptor it changes

At the end of the **first** invocation, after the provider exits and before the
worker writes its record, the worker relaxes **exactly two objects it owns**:

- the one observed project directory under `.claude/projects` → `0o2750`
- that directory's `<session-uuid>.jsonl` → `0o640`

**Turn 2 relaxes nothing.** The manager reconstructs that home and its restored
state is manager-owned `0o660` — already group-readable and group-writable, and
the accepted R1 contract. The worker asserts `turn == 1` before considering any
mode change; in turn 2 the code path does not run at all.

**Every check is made through the descriptor that is then modified**, so there is
no window between checking and changing:

1. open with `O_NOFOLLOW` (`|O_DIRECTORY` for the directory) — a symlink in
   either position refuses rather than redirecting the chmod;
2. `fstat` that descriptor and require `S_ISDIR`/`S_ISREG` as appropriate,
   `st_uid == 65532` and `st_gid == GROUP`;
3. `fchmod` the same descriptor.

**Anything else refuses with a registered code and relaxes nothing** — a
manager-owned object, a wrong type, a symlink, a second project directory, a
missing expected `UUID.jsonl`, a nested or foreign session, a credential-shaped
entry. The worker never widens to make a run pass.

`0o2750` keeps the setgid bit so entries created later still inherit gid1001,
matching the manager's own `0o2770` convention. Nothing else changes:
`.claude.json`, the credential link, other sessions and every cache entry keep
the modes the CLI gave them.

**Why the worker and not the manager.** A manager-side chmod is the host reaching
into runtime-owned state to grant itself access — what PACKET §4 excludes and the
review forbade. Here the owning identity opens two of its own objects to a group
both already belong to. No UID override, no identity switch, no chmod of a
protected root, no `_checked_directory` weakening.

**Exact path:** `evidence/qualification_worker.py`. PACKET keeps the worker
unchanged *unless the correction demonstrably requires it and the reason is
recorded*: only the owning identity may open its own objects, so this cannot live
anywhere else, and this paragraph is the record.

### 3b. P1b — where incomplete coverage must refuse

The rule follows from what each absence claim actually reads:

| Observation | Behaviour | Why |
| --- | --- | --- |
| **Unreadable regular file** | record closed, continue | its **name** is in the parent listing, so credential-shaped, project-count and foreign-`.jsonl` checks are unaffected; only its digest is unavailable |
| **Unenterable / unlistable directory** | **REFUSE**, registered code `state-coverage-incomplete` | the names beneath it are hidden, so every absence claim below it would be vacuous |
| Unreadable **selected** session file | **REFUSE**, specific code | it is the one file that must actually be read |

So the tolerance is exactly as wide as the evidence stays sound and no wider. A
private cache file the manager never needed no longer ends the run as
`unclassified`; a directory it could not enter still stops it, now with a code
that says why.

The inventory row gains one closed field, `content`, with values `read`,
`excluded` (today's `.claude.json` case) and `unreadable:<errno-category>` — so a
deliberate exclusion is never confused with an access failure. `sha256` stays
`None` for both, which is precisely why the distinction has to be explicit.
Byte and entry bounds are unaffected: sizes come from `lstat`, not from reading.

**The promoted set does not change.** One observed project directory, its exact
expected `UUID.jsonl`, nothing nested or foreign, credential entries still
refused, digest still verified on copy.

### 3c. P1c — the closed collection diagnostics

From `review-2026-09-15T18-36-00Z.md`, unchanged. A closed `step` recorded before
each of `source-inventory`, `subset-selection`, `private-layout-save`,
`destination-home`, `state-copy`, `restored-inventory`, `reconstruction-event`,
`restored-validation`. On failure the export carries **only** the closed step, a
category from `known-refusal` / `unregistered-refusal` / `os-error` / `other`, and
the bounded errno enum `EACCES, EPERM, ENOENT, ENOTDIR, ELOOP, ENOSPC, EDQUOT,
EIO, none`. Never exception text, type names, path names or arbitrary arguments.
Existing outcome, refusal and model predicates unchanged; relationships validated
at the public projection boundary.

**These are not an extra.** Had they existed, this campaign would not have needed
two operator inspections to learn the failure was a permission denial in
collection.

## 4. What this correction does not promise

**If the `0o700` directory is not the project directory, the run still refuses.**
P1a relaxes exactly two named objects; a different runtime-owned directory
elsewhere in the home stays unenterable, and P1b then refuses at
`state-coverage-incomplete` rather than proceeding on a vacuous claim. That is a
worse outcome than passing and a much better one than today: the export names the
step and the errno, so the *next* decision is made with attribution instead of
inference. Widening P1a to relax every runtime-owned directory would make the run
pass and qualify nothing, and is rejected in §6.

## 5. Exact paths

| Path | Change |
| --- | --- |
| `evidence/qualification_worker.py` | P1a: turn-1-only, runtime-owned-only relaxation of exactly two objects, verified and changed through one no-follow descriptor |
| `evidence/qualification_contract.py` | P1b: the file/directory coverage rule, `state-coverage-incomplete`, the `content` field; P1c: step/category/errno vocabulary and projection relationships |
| `evidence/qualification-fixture.py` | P1c: controller records the step before each collection operation and exports the closed failure triple |
| `evidence/test_qualification.py` | §7 |
| `evidence/qualification-manifest.json` | rebound digests; identity fields untouched |
| `OPERATOR-178579.md` | the changed collection contract and the new approved digest |

**Unchanged:** the image, two user turns, 180 s per invocation, the 600 s
envelope, the artifact and continuity contracts, the model predicate and its
diagnostics, the fixed three-root reservation, the shutdown receipt discipline,
`_checked_directory`, the runtime UID, `--group-add`, the restored `0o660`
working copy, `0o640` read-only inputs, `0o600` manager-private files and
`0o2770` manager roots. **No new run identity.**

## 6. Alternatives rejected

- **Container umask** — one line, cannot work; the modes are explicit (§1).
- **Manager-side chmod of runtime state** — the host granting itself access to
  another identity's files; excluded by PACKET §4 and the review.
- **Relax every runtime-owned directory** — makes the run pass and qualifies
  nothing; the exact shape of what is promoted is the experiment.
- **Tolerate unenterable directories** — revision 1's defect D1; it would report
  absence checks as passed without having looked.
- **Collect as uid65532** (runtime publishes, manager does not scrape) — coherent
  and larger: a new identity surface, new ordering and new custody questions.
  **Deferred, not dismissed.** Evidence of the symptom is not evidence that this
  is the smallest cure, and it deserves deliberate selection. If §4's limitation
  turns out to bind — a blocking directory that is not the project directory —
  this is the natural next candidate, and the P1c diagnostics are what would
  establish that.

## 7. Focused verification

Deterministic and offline; all 67 existing tests keep passing; run plan is
PACKET §7 unchanged.

**P1a**
1. Turn 1 changes **exactly two** objects' modes — project directory `0o2750`,
   selected session `0o640` — and every other object in a synthetic home keeps
   its mode, asserted over call sites rather than prose.
2. **Turn 2 changes nothing**, and a synthetic manager-owned restored file at
   `0o660` is **still `0o660`** afterwards — the accepted R1 contract held
   directly, since that is what revision 1 would have broken.
3. Ownership and type are checked through the descriptor that is modified: a
   manager-owned object, a wrong type and a symlink in either position each
   refuse with a registered code and leave every mode unchanged.
4. A second project directory, a missing expected `UUID.jsonl`, a nested session
   and a credential-shaped entry each refuse and relax nothing.

**P1b**
5. An unreadable **non-selected** file yields `content: unreadable:EACCES`,
   `sha256: None`, and the run continues with an unchanged promoted set.
6. An unreadable **selected** file refuses with its specific code.
7. **An unenterable directory refuses `state-coverage-incomplete`** — and the
   pointed case: that directory *contains* a foreign `.jsonl` and a
   credential-shaped entry, so the test proves the run refuses rather than
   reporting those absence checks as passed. This is D1's regression test.
8. `.claude.json` still reports `content: excluded`, distinct from
   `unreadable:*`, and is never opened.

**P1c**
9. Each of the eight steps under known refusal, unregistered refusal, `OSError`
   and non-`OSError`, each producing the right step, category and errno; canary
   secrets planted in exception arguments never reach the export; malformed
   diagnostic records refused at the projection boundary.

**End to end**
10. A synthetic home with a runtime-owned `0o700` directory and `0o600` files,
    walked by a non-owner in the group: **before the correction it fails
    `unclassified`; after it, the project-directory case completes and the
    other-directory case refuses with a named step and errno.** Both halves,
    because §4 says the second is a real outcome.
11. One reversal probe per new guard, each failing exactly where it should, in
    isolated copies with `__pycache__` removed and `-B`.

**No live model, engine, image, credential or network operation; no broad suite;
no predecessor rerun.**

## 8. What this proposal does not claim

It does not establish which directory produced the `EACCES`, whether it contains
the selected session, or which original operation failed; §4 states what follows
if the unknown falls the other way, and P1c is what would make the next failure
attributable. It recovers nothing about the consumed run: identity 180078 stays
consumed, both consumed trees keep their timestamps, and no chmod, chown, repair,
marker reset or rerun of them is proposed. Model acceptance is untouched —
`modelUsage` stays expected-plus-other with two keys, G1 stays unqualified.
G4/G6 first-use only, G2/G3/G5 unobserved, G7 qualification-only, G8 not composed.
W161234, C1 and C2 remain independent.

**Nothing here is implemented.** Owner selection, then implementation under its
own claim, then independent review, then a separately selected live run with its
own fresh identity.
