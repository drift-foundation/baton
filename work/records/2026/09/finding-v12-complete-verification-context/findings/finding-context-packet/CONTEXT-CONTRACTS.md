# Task `/3` and the fresh paired contracts — W321780

The exact representation the packet binds. `/2` is **frozen and untouched**:
`baton.dogfood-task/2` carries `source_profile` and `declared_base` (W71917),
its name is occupied by that shape, and widening it is what DESIGN VER-1 forbids.
So the declared verification context arrives as a **new version**, and the result
shapes that express the new outcome axes arrive as new versions beside the old
ones rather than as extra members on them.

Nothing here is implemented. This is the contract an independently reviewable
packet binds, for a delivery claim gated in W321776.

## ONE ROOT PER PATH FIELD, stated once

Review 2026-10-18T09-07-00Z finding 1: the first draft called
`required_paths` repository-relative while the example supplied
working-directory-relative values, and described `import_roots` both ways. One
root per field, and the concrete layout below matches it exactly:

| field | relative to |
| --- | --- |
| `working_directory` | the **view root** |
| `candidate_destination` | the **view root** |
| `inputs[].destination` | the **view root** |
| `import_roots` | **`working_directory`** |
| `required_paths` | **`working_directory`** |
| `candidate.pins` | **`candidate_destination`** |
| a result's `changed_paths` / `removed` | **`candidate_destination`** |

The **view root** is the private materialized verification view a holder builds.
Nothing is repository-relative at the task level: the repository is where the
packet's *provenance* points, and the view is where the command runs.

`inputs[].destination` is view-relative and is chosen so that it stays **outside
`candidate_destination`**. The first draft had it reproduce the repository layout
because the gate reads the fixture at a repository path; review
2026-10-18T09-16-00Z showed that this puts it inside a full-repository candidate
and trips the overlap refusal. A path the gate must read from inside the
candidate is a `candidate.pins` entry, not an input destination — `PACKET.md`
carries that mapping.

`candidate.pins` is a **fourth root** — relative to `candidate_destination`,
because it names bytes of the candidate rather than a place in the view. The
result's `changed_paths` and `removed` share that root; they are observations
rather than task members, per the split below.

## `baton.dogfood-task/3`

`/3` is `/2` plus one member, `verification_context`. `source_profile` and
`declared_base` keep their `/2` meaning exactly, so source provenance and
declared-base checks are preserved as VER-1 requires.

```
schema                "baton.dogfood-task/3"
task_id               opaqueId
instructions          text
source_root           the worker's own destination constant, as in /2
source_profile        as /2 (W71917)
declared_base         as /2 (W71917)
verification          LITERAL argv -- see below
verification_context  the document below
```

**`verification` IS LITERAL ARGV AND CARRIES NO ENVIRONMENT ASSIGNMENT.** The
first draft printed a shell `PYTHONPATH=...` prefix, which contradicted the
contract: imports derive from `import_roots`, so an argv carrying an environment
assignment would be a second, disagreeing source of the same fact. The executable
element is an argv list only.

### The ACTUAL `source_profile` variants, preserved

Review 2026-10-18T09-16-00Z finding 1, and it was right: I asserted `/2`
supports "exactly directory and git-line" and invented directory semantics.
`src/baton_v12/source_profiles/checkout.py` exposes **three** profiles, and
`tools/dogfood_operator.py:744-750` delegates the whole pairing to
`checkout_plan`, so these are the semantics `/3` preserves rather than
redefines:

| profile | `declared_base` | `source_root` | steps |
| --- | --- | --- | --- |
| `generic` | **refused** if present | the read-only mount itself | none |
| `git` | **required** | `<workspace>/checkout` | clone, then check out |
| `git-line` | **required** | the workspace, which already IS the checkout | none |

`checkout.py:216-221` states the second half as loudly as the first: a generic
profile carrying a base "would deliver the generic boundary while its author
believed a verification had happened". `/3` adds no profile, removes none, and
changes neither pairing. A `/3` task whose profile and base disagree is refused
by `checkout_plan`'s own rules at both holders, because both ask the same
package.

## THE BASE IS PROVENANCE; THE CANDIDATE IS CONTENT

Review finding 1's more serious half, and this was a defect rather than
imprecision. The first draft required the verification view to check out
`declared_base` and read it back. **That would discard the very changes the
verification exists to measure**, and the real worker says so:

- `claude_agent.py:2452-2521` (`_entered`) proves the line is clean and that
  `declared_base` is an **ancestor of** the entry head — never equal to it,
  because "an entry check that demanded `HEAD == base` would reject the second
  round".
- `claude_agent.py:2011-2021`: for a line the candidate **is** the mounted
  worktree; nothing is copied, and the baseline is a commit rather than a
  second tree on disk.
- `claude_agent.py:2077-2080` and `:2101`: verification runs over the
  **provider-modified worktree**, and `_commit` is reached only afterwards. The
  published `head` is created from the same measurement the verification ran
  over.

So a view built at `declared_base` would pass tests against old code, and
demanding that a finished candidate equal `declared_base` would reject
legitimate delivery. Three facts, kept apart:

| fact | what it is | what checks it |
| --- | --- | --- |
| `declared_base` | the revision the Work publishes against | **ancestry**, never equality |
| `entry_head` | where the line actually was when the turn was admitted | the manager's writer grant; the worker re-proves ancestry |
| the candidate | the bytes a holder must verify, **pre-publication** | the content binding below |

### A SEALED TASK HOLDS CONSTRAINTS; A RESULT HOLDS OBSERVATIONS

Review 2026-10-18T09-38-00Z finding 1, and it is a temporal contradiction
rather than a wording problem. My previous draft put `tree_digest`, `changed`
and `removed` in `verification_context` — a **required member of the input
task** — and had Stage A validate them before any provider work. A useful
authoring turn cannot know its own edits before it runs, and
`workspaces.compose_input_root:5779` onward with DESIGN ART-3 prohibit
rewriting the pre-claim input binding after the claim. Deferring `<TREE>` to
selection did not fix that; it only moved the impossible measurement.

So the two kinds of fact are separated, and the separation is the contract:

| kind | where it lives | when it is knowable |
| --- | --- | --- |
| **launch constraint** | the sealed task's `verification_context` | before the provider runs, from the task and the sealed inputs alone |
| **candidate observation** | the turn's own **published result** | after the provider finishes, before verification starts |

The sealed task's candidate member therefore carries **only** what is true at
sealing:

```
profile        "generic" | "git" | "git-line"   -- checkout.py's own PROFILES
declared_base  null for generic; required for the two version-control profiles
pins           ordered [{path, content_digest}] -- candidate-relative paths
               whose bytes the task requires UNCHANGED. A CONSTRAINT: every
               pin names a path that exists at sealing, with the digest it
               has at sealing
```

`entry_head` is **not** here either. It is the head the manager's writer grant
admitted, which the task author does not hold; the worker proves the
relationship (`_entered`) and publishes what it found.

### The measured candidate, published rather than declared

After the provider and before verification, the turn measures what changed and
publishes it. These members are **observations in the result**, and independent
review binds to that retained output — never to a rewritten task:

```
base           the declared base, carried through from the task
entry_head     the admitted entry head, measured; declared_base is its ANCESTOR
head           the commit this turn published, or null when it produced none
changed_paths  the bounded, status-reported collection
removed        the deletions, collected as their own set
collection     the DISCLOSURE of what the collection excluded
```

**THERE IS NO WHOLE-TREE DIGEST, and removing it is the correction.**
`claude_agent._line_status:2759` records owner ruling 2026-09-21T12:47:17Z
retiring the whole-checkout rehash **by name**: "the superseded broad regime
walked and hashed the whole checkout to catch what an index trick can hide from
status; the ruling retires that guarantee by name, and what remains is honest:
the delivered changes are still proved byte-for-byte (`_identical_bytes`), and a
path status cannot see is neither measured nor delivered." My `tree_digest` over
the whole candidate, with "nothing is excluded silently", reinstated exactly
that retired guarantee — and asserted a scope the adapter does not have, since
`_line_delta` is explicitly bounded and **discloses** its ignored and special
exclusions.

What this packet binds instead is what the adapter actually produces: the
bounded changed set proved byte-for-byte, the deletions as their own set, and
the exclusion disclosure carried forward so a reader is told what was not
measured. If a broader guarantee is ever required for acceptance, that is an
**owner decision with a stated unmet requirement**, not something a preparation
packet may assert into existence.

### `pins` as an input constraint, which is all it ever needed to be

The 102 gate resolves its fixture through `tests/manager/input_roots.py:29-33`,
which walks `parents[3] / ".."` from its own file — so the path it reads lands
**inside** a full-repository candidate, and no declaration can move it without
editing the product. A pin is decidable at sealing: the path exists, its digest
is measured, and Stage A can check the sealed set agrees with it. Stage B then
checks the materialized view still holds those bytes. Nothing about a pin
depends on what the provider will do, which is why it survives the split while
`changed`/`removed` do not. `PACKET.md` carries the concrete mapping.

### `verification_context`

```
working_directory     view-relative, canonical, contained; no "", ".", ".."
candidate_destination view-relative, canonical, contained
candidate             the LAUNCH-CONSTRAINT document above: profile,
                      declared_base, pins. No post-provider member
import_roots          ordered, each working-directory-relative and contained
required_paths        ordered, each working-directory-relative and contained
inputs                ordered declared immutable inputs:
    name              opaqueId, unique within the task
    destination       view-relative, canonical, contained
    content_digest    sha256:<64 hex>
    bytes             integer >= 0
```

`working_directory` may lie **inside** `candidate_destination` — it does in the
concrete packet, because the command runs in the candidate's own Python subtree.
That is not the overlap the rule forbids: VER-2's overlap refusal is about a
**sealed input destination** and the candidate, where indistinguishable bytes
would let verification feed fixtures into the proposal.

## TWO PREFLIGHT STAGES, because they can see different things

Review finding 1's second half, and it is a real correction rather than a
wording change: the first draft required *every* missing required path to refuse
before materialization, and a path inside a view that does not exist yet cannot
be checked there — nor before the implementation has created or deleted it.

**STAGE A — STATIC, before materialization and before any provider work.**
Decidable from the task and the sealed inputs alone:

| refusal | because |
| --- | --- |
| absolute or `~` path in any member | the meaning would depend on the host that read it |
| `.`, `..` or empty segment | escapes whatever root it is joined to |
| duplicate `inputs[].destination` | the second would silently overwrite the first |
| input destination inside `candidate_destination`, or the reverse | VER-2's overlap: a sealed input under the candidate is indistinguishable from candidate bytes, and verification could then add fixtures to the proposal |
| malformed or non-`sha256:` digest | an input nobody can verify is not sealed |
| a declared input absent from the sealed set, or digest-mismatched there | `missing-input`, decided against the seal rather than against the view |
| `verification` empty, or not a list of non-empty strings | there is no command |
| `verification_context` present under `/2` | **VER-1's refusal direction**: an older holder refuses new semantics rather than ignoring the member |
| `verification_context` absent under `/3` | a `/3` task without the context it exists to declare |
| `candidate.profile` not one of `checkout.py`'s `PROFILES` | the profile vocabulary is that package's, not this document's |
| `generic` with a `declared_base`, or `git`/`git-line` without one | `checkout_plan`'s own pairing, asked rather than copied |
| any post-provider member in the sealed task — `entry_head`, `tree_digest`, `changed`, `removed` | **a sealed task cannot carry what the turn has not done yet**, and ART-3 forbids rewriting the input binding after the claim to insert it |
| a `candidate.pins` path that is not candidate-relative and contained | the same containment rule as every other path member |
| a duplicate `candidate.pins` path | two digests for one path is not one constraint |
| a `candidate.pins` path absent from the sealed set, or digest-mismatched there | decided against the **seal**, at sealing time, like every other Stage-A input question |

A Stage-A refusal is `refused` with its cause, `command: not-run`, and
**nothing materialized**.

**STAGE B — VIEW PREFLIGHT, after materialization and immediately before the
command starts.** Decidable only once the view exists:

| refusal | cause |
| --- | --- |
| `working_directory` absent in the view | `invalid-layout` |
| an `import_root` absent in the view | `invalid-layout` |
| a `required_path` absent in the view | `missing-input` |
| an input's materialized bytes do not match its declared digest | `materialization` |
| a `candidate.pins` path absent, or present at other bytes | `materialization` |
| a path the RETAINED RESULT reports changed is absent, or present at other bytes | `materialization` |
| a path the RETAINED RESULT reports removed is **present** in the view | `materialization` |
| `git-line`: `declared_base` is not an ancestor of `entry_head`, or either object is not in the line | `invalid-layout` |

**THE BASE IS NEVER CHECKED OUT INTO THE VERIFICATION VIEW.** The old Stage-B
row demanding a readback at `declared_base` is gone, and its removal was the
previous correction: the view holds the **changed candidate**, and the base
appears only as the ancestry question above.

| the accepted-base object source does not hold `base` | `missing-input` |
| the object transport's prerequisites are unsatisfied in the receiving view | `materialization` |
| the transport does not resolve the `head` the retained result published | `materialization` |

**STAGE B RUNS IN BOTH VIEWS, AND NEITHER OF THEM IS THE EDITED CANDIDATE.**
Review 2026-10-18T09-49-00Z, and I had written an exception here that should
never have existed: that the worker's own view "needs no such comparison"
because it *is* where the edits were made. Renaming the edited worktree a view
supplies no isolation. DESIGN VER-3 requires a **fresh private view at each
holder**, and a command that wrote or deleted a source path would otherwise
alter the retained candidate — while a timeout cleanup that removed that "view"
would remove the candidate. The exception is gone, and the rows above apply to
the worker's materialized view exactly as they apply to the operator's.

Each view is bound to the published result's reported `changed_paths`/`removed`,
so "an unchanged base was substituted for the changed candidate" refuses because
the view does not hold the paths that result says were changed.

A Stage-B refusal is `refused` with its cause and `command: not-run`; **the
holder's own view is cleaned up and nothing else is**, and the retained
candidate and the sealed inputs are byte-unchanged — on a refusal, on a test
failure, on a timeout, on a failed start and on a partial materialization alike.

**CANDIDATE DELETION IS REFLECTED, NOT REPAIRED.** If the implementation deleted
a path the task requires, Stage B says `missing-input` and the command does not
run. That is a context failure and therefore **supplies no verdict about the
candidate** — the deletion is reported, not silently tolerated and not read as a
test failure.

## The fresh paired contracts

VER-1 requires fresh proposal **and evidence** contracts. The first draft defined
the worker side only; the operator side is the other half of the pair.

### `baton.dogfood-context/1` — the durable context outcome

```
schema      "baton.dogfood-context/1"
outcome     "ready" | "refused"
stage       null when ready; "static" | "view"
cause       null when ready; otherwise exactly one of
            "missing-input" | "invalid-layout" | "materialization" | "start-failure"
detail      a BOUNDED STRUCTURAL fact: which declared member or input name
            failed. Never child output, never a credential, never an absolute
            host path, never arbitrary exception prose.
```

### `baton.dogfood-proposal/3` — the worker's result

```
schema       "baton.dogfood-proposal/3"
...           every /2 member, unchanged
context      a baton.dogfood-context/1 document
command      "not-run" | "passed" | "failed" | "timed-out"
exit_status  an integer ONLY when the child supplied one; otherwise null
```

### `baton.dogfood-operator-evidence/1` — the independent operator's result

The operator materializes its **own** view and runs the **same** argv. Its
document is separate because it is a separate observation, and it is **bound to
the exact thing it observed** so it cannot be read as evidence about something
else:

```
schema             "baton.dogfood-operator-evidence/1"
task_id            the exact task observed
task_digest        sha256 of the canonical task bytes
candidate_profile  the profile observed, from checkout.py's PROFILES
candidate_base     the declared base; NULL for a generic candidate
candidate_entry    git-line only: the entry head the base is an ancestor of
result_head        the head the RETAINED RESULT published; null for generic
result_digest      sha256 of the retained result record's canonical bytes --
                   WHAT THIS EVIDENCE IS ABOUT, named once
transport          the retained object transport the operator consumed, or
                   null when the profile retained a candidate tree instead
candidate_changed  [{path, content_digest}] -- MEASURED in the operator's own
                   view, over the paths the retained result reported
candidate_removed  ordered paths the operator observed ABSENT
inputs             [{name, content_digest}] -- the sealed set as materialized
context            a baton.dogfood-context/1 document
command            "not-run" | "passed" | "failed" | "timed-out"
exit_status        integer or null, on the same rule
```

**THE EVIDENCE IS ABOUT A RETAINED OUTPUT, not about a task.** `result_digest`
names the exact published result the operator independently verified, and
`result_head`/`transport` name where it got the bytes from. That is review
2026-10-18T09-38-00Z finding 1 pointed at the evidence: the changed candidate is
an **observation**, so what a second holder confirms is the observation's
retained record — never a task member that could not have carried it.

`candidate_head` was removed one correction earlier, for a different reason that
still holds: it could not identify a generic candidate, which has no commit at
all. There is also **no `candidate_tree` and no whole-tree digest**. The
operator measures the paths the retained result **reported**, which is the same
bounded scope the adapter measures, and inherits the same honest limit — a path
status could not see is neither measured nor delivered.

The operator's members are **measured, not copied from the task.** Evidence that
restated the declaration would agree with the task by construction and prove
nothing about the view; the whole reason there are two holders is that their
measurements can disagree.

**LEGACY FIELDS ARE NOT REINTERPRETED.** `/2` results carry no `context` and no
`command`. A consumer reading a `/2` result must not infer either: absence is
"this version could not say", never "not-run" and never "passed". That is the
same refusal direction as the task, pointed at results.

### The allowed combinations, closed

Review finding 2 asks for these constrained rather than implied:

| `context.outcome` | `cause` | `command` | `exit_status` | verdict |
| --- | --- | --- | --- | --- |
| `ready` | null | `passed` | `0` | **verdict: candidate passed** |
| `ready` | null | `failed` | nonzero integer | **verdict: candidate failed** |
| `ready` | null | `timed-out` | null | none |
| `ready` | null | `not-run` | null | none |
| `refused` | exactly one | `not-run` | null | none |

Everything else is a **malformed result** and is refused as such by both holders.
In particular: `passed` may not carry a null or nonzero status; `failed` may not
carry `0` or null; `refused` may never carry a command verdict; and `not-run`
and `timed-out` may never carry a status. A verdict exists only in the first two
rows — `refused`, `not-run` and `timed-out` preserve the candidate and assert
nothing about its correctness.

## Cleanup and preservation

VER-3/VER-4: a timeout, a start failure or a partial materialization cleans up
the **derived views this run owns** and retains source and candidate.
Verification cannot modify retained candidate bytes or sealed inputs, and cannot
add fixtures to the proposal output — which is why input destinations may not
overlap the candidate, and why the cleanup boundary is the derived view rather
than anything the manager did not create.
