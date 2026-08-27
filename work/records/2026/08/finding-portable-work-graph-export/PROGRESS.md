# Progress

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-27 — claimed, and the approved ruling revalidated against the tree

Claimed W24755 at seq 24902. PLAN item 4 is the actionable one; items 1–3 are
done (design, reviewer revalidation, approver ruling).

Before writing anything I re-checked every pinned claim in `FINDING.md` and
`evidence/design-baseline-2026-08-27.md` against the current source, because a
reviewer proposal is decision support and not authority. **All of them hold.**
Recorded here rather than assumed, so a later reader can see what was checked
rather than that something was.

### The schema claims

| pinned claim | current tree |
| --- | --- |
| `edges(work, blocker, via_obligation, created_seq)` | confirmed, `authority.py:352`, `PRIMARY KEY (work, blocker)` |
| `work.parent`, `work.follow_up_of`, `work.duplicate_of` are FK endpoint columns | confirmed, `authority.py:296,315,316` |
| `work.last_changed_at` exists and is canonical | confirmed, `authority.py:321`, `TEXT NOT NULL` |
| `work.created_seq` / `closed_seq` | confirmed, `authority.py:317,318` |
| `_read_snapshot` is reentrant `BEGIN … ROLLBACK` | confirmed, `projection.py:41` |
| `jsonapi.PROJECTION_VERSION` is `12.5` | confirmed, so the ruled bump to `12.6` is still a minor step and not a collision |

### The ordering claims, which were the ones that could have rotted

The approved edge ordering keys `containment` on the child's `created_seq`,
`follow-up` on the successor's `created_seq` and `duplicate` on the duplicate's
`closed_seq`. Each is only deterministic if the underlying column cannot move
or be null when the relation exists, so each was checked rather than trusted:

- **`parent` is immutable.** There is no `SET parent` anywhere in
  `transitions.py`; it is written at creation only. Child `created_seq` is
  therefore exactly the moment the containment relation came into being.
- **`follow_up_of` is set at creation only** and refuses an open predecessor
  (`transitions.py:1070-1074`). Successor `created_seq` is exact.
- **`duplicate_of` is set only by a close carrying `outcome='rejected'`**, in
  the same `UPDATE` that writes `closed_seq` (`transitions.py:1356-1361`). A row
  with `duplicate_of` non-null therefore always has `closed_seq` non-null, so
  the ordering key cannot be null where the relation exists.

### The baseline

The six focused cases the design evidence names still pass unchanged:

```
tests/work/test_projection.py::test_links_expose_the_fan_in_deliberately
tests/work/test_terminal_outcomes.py::test_duplicate_link_rules_are_exact
tests/work/test_ws2_close.py::test_follow_up_targets_closed_work_only_and_gates_nothing
tests/work/test_w71_navigation.py::test_a_mid_read_commit_cannot_produce_a_mixed_tree
tests/work/test_w4996_dependency_graph.py::test_the_public_links_response_is_unchanged
tests/work/test_w4996_dependency_graph.py::test_every_edge_spells_its_direction_without_unicode_or_colour

6 passed
```

### One consequence of the schema worth stating before it looks like a gap

`FINDING.md` requires a duplicate typed edge to refuse. For the dependency
family the store already makes one impossible — `edges` is keyed
`(work, blocker)` — and the other three families are single-valued columns on
the child/successor/duplicate row, so a second edge of the same relation
between the same pair is likewise unrepresentable. The validation is therefore
written as a guard over the built projection rather than as a case the current
schema can reach through the authority. It is kept because the renderer and the
projection are separate boundaries and the renderer must not assume its input
was built by this projection, and the test drives it by handing the validator a
malformed envelope directly rather than by pretending the store can produce one.

## State

Revalidation done; implementation starting on PLAN item 4 in the recorded order:
projection, then pure renderer, then CLI surface, then the twelve acceptance
groups, then documentation.

## 2026-08-27 — PLAN item 4 implemented

Evidence: `evidence/w24755-2026-08-27-implementation.txt`.
Harness: `evidence/w24755-mutation-harness.py`.
No Git history or index was mutated.

### What was built

| file | what |
| --- | --- |
| `src/baton_work/projection.py` | `work_graph`, its scope/node/edge builders and its validator |
| `src/baton_work/dot.py` | **new** — the pure renderer and the quoting rules |
| `src/baton_work/cli.py` | the `work-graph` grammar and the one raw-DOT branch |
| `src/baton_work/jsonapi.py` | projection **12.6** |
| `tests/work/test_w24755_work_graph_export.py` | **new** — 57 cases |
| `docs/EFFECTIVE-BATON.md` | "Exporting the Work graph" |
| `docs/BATON-WORK.md` | the console graph is a view, not an export |

Every approved surface works against a real authority, JSON is the default,
`format=dot` is the one raw-stdout branch and reaches it only after the same
projection-version, config, participant and dispatch validation every other
command passes through.

**One snapshot, two statements.** Every Work row and every current dependency
row are read in a constant number of ordered statements inside one
`_read_snapshot`; the other three families are derived from those same Work
rows, so the statement count does not grow with the graph.

### Three things the tree said that the design did not

Each came from driving the approved design against the real authority rather
than from reading it, and each changed a test.

**[1] The authority stores hostile titles that look unstorable.**
`validate_subject` refuses a literal newline or carriage return in a Work title
and refuses *nothing else* this export has to survive: a bare TAB, a NUL, a
right-to-left override and U+2028/U+2029 are all storable. U+2028 is the
sharpest — it *is* a line break to a great many consumers and the single-line
check does not see it. The renderer's visibility rule is therefore load-bearing
for real titles. The two the authority refuses are still driven at the renderer,
because a later relaxation of the title rule must not silently become a
DOT-injection defect.

**[2] The authority permits fewer parallel relations than the ruling assumes.**
`FINDING.md` says any of the four families may coexist on one pair. Reachable:

- containment + dependency — refused as a required-edge cycle;
- follow-up + dependency — refused; a follow-up predecessor is closed and a new
  blocker must be open;
- containment + duplicate — refused; a parent cannot close holding an open child;
- **dependency + duplicate — reachable**: A blocks B, then A closes as a rejected
  duplicate of B.

Two parallel edges is all the non-`strict` argument needs, so the case uses the
reachable pair. The renderer is separately held to four, because a later change
to the authority must not become a change to every previously exported document.

**[3] A module-scope name collision, and it was mine.** `projection.py` already
had `_graph_node` for the bounded dependency *neighbourhood*. I appended a second
definition of that name for the export. Python rebinds silently: W24755's own
suite passed while **eighty-eight** dependency-graph cases failed with a
`TypeError`. A focused run could not see it and the full gate reported it as
failures somewhere else entirely. The instance is renamed `_export_*`, and the
**class** is now checked directly by AST over every module in
`tests/work/test_boundaries.py`.

### Two clarifications inside the ruling, not against it

- **DOT v1's graph attributes had to carry the approver's range.** The
  determinism promise is that one authority, one snapshot and one *scope* give
  one document, so a scope operand the document did not spell would let two
  different questions produce identical bytes. `baton_scope_changed_from` and
  `baton_scope_changed_until` are emitted, `*` when absent.
- **`scope=selected|context` versus "a `baton_*` per node member".**
  `FINDING.md` says both and they conflict for one member. The explicit spelling
  wins as the more specific instruction; the mapping is total, so `selected` is
  still recoverable, and a case asserts every other member has its own
  attribute.

### Measured by removal

Every promise the export makes was removed from the source and the suite re-run.
**The first pass found five unestablished**, and the interesting ones were all
one shape — a second thing standing where the guard was:

- the projection's `status` default was masked by the CLI grammar's own default;
- the graph attribute `sorted()` was masked by a dict literal already written in
  sorted order — fixed at the rule, by giving both attribute lists one owner,
  rather than by contriving a case;
- the literal `null` was asserted nowhere, so rendering absent members as `""`
  passed everything;
- a streamed partial document was invisible, because the refusal cases only
  reach the projection and the renderer never runs;
- **the interleaved-writer case was the worst of them.** It took a fixed twelve
  exports, and over a small database all twelve finished before the writer's
  first commit — a consistency proof about a *quiet* store that would have passed
  for an exporter with no snapshot discipline at all. It now reads until the
  writer has moved the authority three times, under a deadline.

**All 34 mutations are caught.** The three mutated files are fingerprinted
before and after the harness run, so "everything was restored" is measured
rather than asserted.

### Gates

- v11 parallel — **3123 passed**
- v11 serial — **54 passed**
- ACP bridge acceptance — **77 pass, 0 fail**
- W24755's own suite — **57 passed**

### One edit to existing tests, named rather than left to be found

Six suites pinned `PROJECTION_VERSION == "12.5"`. Each asserts "the current
version is X and a `12.0` demand still succeeds within the major", so a MINOR
bump leaves every one testing exactly what it tested, and the bump to 12.6 is
the approver's explicit ruling. It is still an edit to existing assertions, so it
is stated here for review rather than buried in the diff.

## State

PLAN item 4 is complete and the whole gate is green. Passed to independent
review rather than closed — PLAN item 5 is the reviewer's, and no release
packaging was performed.

## 2026-08-27 — first review answered

Evidence: `evidence/w24755-2026-08-27-first-review-response.txt`.
Review: `review-2026-08-27T16-08-50Z.md`. **All four findings correct.**
No Git history or index was mutated.

### [P1] The range parser accepted more than RFC 3339

I delegated the grammar to `datetime.fromisoformat` and reasoned about exactly
one spelling — my own comment said "`Z` is the spelling RFC 3339 blesses and
`fromisoformat` accepts" and stopped there. "Whatever this Python happens to
parse" is not a contract a client can be held to or a future Python will keep.
The grammar is now written out and checked before the parse; the parse still
runs after, because a string can match the shape and name no moment.

**The fix had its own defect, and the accept-side case found it.** RFC 3339
§5.6 makes both `T` and `Z` case-insensitive, so `2026-08-27t00:00:00z` *is* the
contract — and `fromisoformat` rejects the lower-case `z`. A grammar admitting a
spelling the parser then called "not a moment" would have been worse than the
original. Case is normalized before parsing, and the measurement showed only the
`z` half is load-bearing on this CPython; the asymmetry is stated in the source
rather than left to be rediscovered.

### [P1] The renderer did not keep its own promise

`dot.py`'s docstring said it "VALIDATES ITS INPUT rather than trusting that the
projection built it". It owned container shapes and the relation enum and
nothing else. **That is a claim the code did not keep, which is worse than no
claim, because a reader stops checking** — the same failure I have been
correcting in my own tests all week, this time written into a module docstring.

The reviewer's requirement was *one enforcement*, not "add checks". The
projection's private validator is now public `validate_work_graph` and the
renderer calls it. It also takes nodes as a **sequence** rather than a mapping:
a caller that had already built a mapping would have collapsed two nodes sharing
an id before anything could object. A case asserts the rule text lives in one
module only, by AST plus phrase search.

### [P1] `selected` lost its `baton_*` member

I read `scope=selected|context` and "a `baton_*` per structured node member" as
competing and resolved the conflict. There was none: one is the readable role,
the other the exact boolean. Both are emitted now. Worse than the omission is
that I recorded the wrong reading as a deliberate clarification last round,
which made an unnecessary decision look considered.

### [P2] The team check sat outside the named snapshot

Split: operand validation stays outside and still refuses before a transaction
opens; the configured-team fact moved inside. Observed **at the connection** —
the `teams` query is recorded together with whether a transaction was open when
it ran — rather than inferred from where the call sits in the source.

### Measured by removal

Seven mutations added for the four findings. **Two of the first attempts were
UNSEEN, and both were my test's fault rather than the fix's:**

- the lower-case `t`/`z` normalization — my mutation removed only the `T` half,
  and this CPython accepts a lower-case `t` anyway;
- the offset requirement — my refusal case used a bare date `2026-01-01`, which
  fails the grammar for a *different* reason (no time part at all), so making
  the offset optional changed nothing observable. A complete date-time carrying
  no offset is now the case.

**All 41 mutations caught.** Source fingerprinted before and after.

### Gates

- this Work — **64 passed** (57 mine, 3 the reviewer's unmodified, 4 new)
- v11 parallel — **3130 passed**; v11 serial — **54 passed**
- ACP bridge — **77 pass, 0 fail**

## State

All four findings answered; awaiting the second review pass. Nothing closed.

## 2026-08-27 — second review answered

Evidence: `evidence/w24755-2026-08-27-second-review-response.txt`.
Review: `review-2026-08-27T16-24-41Z.md`. **Both findings correct.**
No Git history or index was mutated.

### [P1] RFC 3339 fractions were truncated to microseconds

My grammar allowed one or more fractional digits and then handed the whole
spelling to `datetime`, which holds only microseconds and drops the rest without
complaint. `...00.0000001Z` and `...00.0000009Z` both became `...00.000000Z` —
two different half-open bounds collapsed into one, so the export silently
answered a question the operator did not ask and two distinct approved scopes
became indistinguishable in the JSON and the DOT metadata.

The fraction is now carried separately. `datetime` still validates the calendar
and rolls the offset to UTC — a regex has no opinion about February 30th, and an
offset shift can move the date — but it no longer owns the fraction. That is
sound because RFC 3339 offsets are whole minutes, so a UTC shift cannot change
the sub-second part.

**The fix had a trap I had to find before it bit.** A variable-length fraction
cannot be compared as *text*: `...00:00:00Z` and `...00:00:00.0000001Z` compare
`Z` against `0`, so the whole second sorts **after** the instant a tenth of a
microsecond later, and the range would select the wrong side of that boundary
while looking entirely reasonable. Fixed-width padding is not available either,
because the fraction has no bound. Comparison therefore goes through an explicit
ordering key — fixed-width whole second, then canonical digits — and the
published text is only ever an identity. Its case drives *selection* rather than
the key, because which Work the operator gets is the question.

### [P1] The renderer owned presence but not type

Presence is not ownership when the value goes on to mean something.
`selected="false"` is truthy, so it rendered as selected; `title=7` escaped as
`AttributeError` from `.encode()` rather than as a refusal naming the member.

**The whole fixed schema**, not the two values the review found — a pair of
one-off guards would have left every other member as it was and would have to be
extended by whoever next noticed one. `type(value) is expected` rather than
`isinstance`, because `bool` subclasses `int` and `created_seq=True` would
otherwise pass as an integer.

And it lives in the **one** validator, not beside it: the presence checks the
renderer used to make itself are gone rather than kept alongside. Two boundaries
checking the same thing is how they come to disagree — the correction the first
review already made once.

### Measured by removal

Six mutations added for the two findings. **Two came back UNSEEN and both were
mine rather than the fix's:**

- the fraction mutation swapped which spelling `datetime` parsed, but the
  canonical text is built from the separately-kept fraction either way — a
  no-op. Re-anchored on the line that *builds* the text, which is where the
  truncation actually happened.
- the `bool`-as-`int` mutation was invisible because my type-corruption table
  offered one wrong value per type, and for an int member that value was a
  string — which fails an `isinstance` check too. Two wrong values per type now.

**All 47 mutations caught.** Source fingerprinted before and after.

### Gates

- this Work — **69 passed** (57 first-round, 5 reviewer regressions across two
  passes all unmodified, 7 added for the two rounds of fixes)
- v11 parallel — **3135 passed**; v11 serial — **54 passed**
- ACP bridge — **77 pass, 0 fail**

## State

Both findings answered; awaiting the third review pass. Nothing closed.

Worth stating plainly across the three rounds: every finding so far has been a
place where I proved a narrower thing than I claimed — a grammar I reasoned
about for one spelling, a docstring promising validation the code did not do,
presence checked and called ownership. The measurement keeps catching the same
shape in my *tests* too, twice more this round.

## 2026-08-27 — third review answered

Evidence: `evidence/w24755-2026-08-27-third-review-response.txt`.
Review: `review-2026-08-27T16-39-54Z.md`. **The finding is correct.**
No Git history or index was mutated.

### [P1] Closed vocabularies were not owned

I proved `status`, `phase` and `outcome` are *text* and called that owning the
structured input. A forged `status="bogus"`, `phase="review"` or
`outcome="done"` rendered a complete-looking document, and each of those members
supplies both the readable node-state label and a machine-readable attribute.

**Six members, not the three that were found.** `origin`, `classification` and
`priority` are closed in exactly the same way and reach exactly the same two
places; validating only the named three would be the
guard-extended-one-member-at-a-time shape the second review already corrected.
`team` is deliberately absent — its domain is the accepted configuration, a
*store* fact, and the renderer is pure; the projection admits the team inside
its own snapshot, which is the second review's [P2].

The vocabularies are the authority's own, imported rather than restated, and a
case asserts that **by identity** so a renderer-only copy fails rather than
drifts.

### The import that made that possible, and the rule that bounds it

Reusing the canonical tuples means the read side importing from the write
module. `projection.py` has imported only `authority` since it was written, and
`test_the_read_side_never_commits` is a source-*text* check that would not
notice if that import later grew into a mutation. So the import takes **names,
never the module**, and the narrowing is now an enforced rule
(`test_the_read_side_imports_only_vocabulary_from_transitions`): every name
`projection` takes from `transitions` must resolve to text or a tuple of text.

I considered relocating the vocabularies to `authority.py` instead and did not:
44 references across five modules and another Work's file, for a structural
change this review did not ask for.

### On the pattern

Four rounds, four findings, one shape — I proved something narrower than I
claimed and wrote the claim down anyway:

| round | the claim | what the code did |
| --- | --- | --- |
| 1 | the renderer validates its input | checked container shapes |
| 1 | timezone-bearing RFC 3339 | whatever `fromisoformat` parsed |
| 2 | the renderer owns its members | checked presence |
| 3 | the renderer owns its members | checked presence and type |

The common cause is that I write the general sentence first and implement the
case in front of me. The mutation pass catches this in the **tests** every time
— six unestablished guards in round one, two in each round since — but it cannot
catch it in **prose**, because a docstring is not executable. What has worked is
the reviewer reading the claim and asking what enforces it.

Concretely, for the rest of this Work: where a comment or docstring states a
general rule, there is a case named for that rule, or the sentence is narrowed
to what the code does. The two boundary tests added this round are that applied
to the two claims I made today.

### Gates

- this Work — **73 passed** (57 first-round, 6 reviewer regressions across three
  passes all unmodified, 10 added for the three rounds of fixes)
- boundaries — **5 passed**
- v11 parallel — **3140 passed**; v11 serial — **54 passed**
- ACP bridge — **77 pass, 0 fail**
- **50 mutations, all caught**; source fingerprinted before and after

## State

Finding answered; awaiting the fourth review pass. Nothing closed.

## 2026-08-27 — fourth review answered

Evidence: `evidence/w24755-2026-08-27-fourth-review-response.txt`.
Review: `review-2026-08-27T16-54-31Z.md`. **Both findings correct**, and one of
them names a defect in a test of mine rather than only in the code.
No Git history or index was mutated.

### [P1] Individually valid values formed impossible states

`status`, `phase` and `outcome` are one state and I validated them as three
fields. Every value in an open-node-with-an-outcome is individually type-correct
and in-domain, so last round's enum guards could not see the contradiction. The
same gap let a containment edge name an obligation it cannot have come from.
Both are now cross-member rules in the shared validator.

**And the review found a test of mine asserting the wrong thing.**
`test_null_is_accepted_exactly_where_the_contract_allows_it` asserted that
`phase=null` renders on an *open* node. The confirmed schema forbids it. It
passed because the validator treated the three members independently — so my
case and my code agreed with each other and both disagreed with the schema.
That is worse than a missing case: **a test asserting the wrong thing is a
defect with a guard in front of it.** Corrected to the two valid paired states,
keeping the line the original was reaching for.

### [P1] "The whole input validated" excluded scope and counts

The renderer required `scope` and `counts` and validated neither. A forged
closure became an authoritative-looking graph attribute; a count contradicting
its own array was ignored — and a count is the cheapest thing in the document
for a reader to trust.

One shared result validator now owns the whole document, and **the projection
runs it on its own output** before answering: a producer exempt from the rules
its consumer enforces is how the two come to disagree. Counts are *proved* from
the arrays.

A consequence I fixed in the same round: the interval rule then existed in two
places, the operand path and the document path — the duplication three earlier
rounds corrected elsewhere. `_export_scope` now parses and delegates; every rule
about the result is stated once.

### The commitment from last round, applied and already earning

I said that where a comment states a general rule there would be a case named
for it, or the sentence would be narrowed. The renderer's contract is now an
explicit eight-line table, and
`test_the_renderer_refuses_one_input_per_category_it_claims_to_own` drives one
malformed input per line **and** asserts the prose and the table name the same
categories.

**It failed on its first run**, which is the point: my prose said "every
member's presence, type and closed vocabulary" while the table said "member
presence" and "member type". Drift of exactly the kind four reviews have been
finding — caught by the case instead of by the reviewer.

### Gates

- this Work — **86 passed** (65 definitions, parameterized)
- boundaries — **5 passed**
- v11 parallel — **3153 passed**; v11 serial — **54 passed**
- ACP bridge — **77 pass, 0 fail**
- **60 mutations, all caught**; source fingerprinted before and after

## State

Both findings answered; awaiting the fifth review pass. Nothing closed.

## 2026-08-27 — fifth review answered

Evidence: `evidence/w24755-2026-08-27-fifth-review-response.txt`.
Review: `review-2026-08-27T17-09-43Z.md`. **The finding is correct**, and it is a
call I made deliberately last round and got wrong.
No Git history or index was mutated.

### [P1] A structured bound was not required to be canonical

`_export_scope_document` validated each bound with `_export_instant` and
*discarded* the canonical value, so the renderer emitted whatever the caller
spelled. `2026-01-01T01:00:00+01:00` and `2026-01-01T00:00:00Z` are one approved
lower bound and produced different `baton_scope_changed_from` bytes.

**I decided this on purpose.** I judged that requiring canonical form would be
unkind to a structured caller and settled for "parses as RFC 3339". That was
wrong by an argument I had already made myself: two rounds earlier I added the
range to the DOT graph attributes precisely so two different scopes could not
produce identical bytes. One scope producing *different* bytes is the same
promise broken from the other side, and I did not connect the two.

The document rule now requires each non-null bound to equal its
canonicalization, symmetrically. The operand path is untouched and still accepts
every legal spelling — and that is a case rather than an intention, alongside
the promise itself end to end: four legal spellings of one instant through the
real CLI must give byte-identical DOT. That is the converse of a case this suite
has carried since the opening round (two scopes over one snapshot must *differ*)
and neither implies the other. The review found the half that was missing.

### A flaky mutation detection, found while measuring this round

Not a review finding — found by the harness, and reported because it means one
guard was weaker than four rounds of evidence claimed.

The mutation that moves the snapshot-sequence sample *outside* the read
transaction came back UNSEEN. Run alone, the interleaved-writer case catches it;
run beside the others it does not, because it can only observe the defect when a
commit lands in the microseconds between the rollback and the sample. **A guard
whose detection is a coin flip is not a guard**, and it had been reported as
caught in every previous round.

The property is now also observed deterministically at the connection, the same
way the configured-team read is. The end-to-end case stays — it establishes the
whole property against a real racing writer, and the new one establishes the
exact mechanism reliably. Neither replaces the other.

### Gates

- this Work — **95 passed**; boundaries — **5 passed**
- v11 parallel — **3162 passed**; v11 serial — **54 passed**
- ACP bridge — **77 pass, 0 fail**
- **62 mutations, all caught**; source fingerprinted before and after

## State

Finding answered; awaiting the sixth review pass. Nothing closed.
