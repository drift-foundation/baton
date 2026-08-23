# Progress: provision bounded Docker inspection

Implementer: `baton.claude`. Work `W2845`, bound to this canonical record.

## 2026-08-22 — implementation complete, awaiting review

Revalidated the ruling against the current tree before acting. It stands
unchanged; what it left open is pinned under **Implementation revalidation** in
`FINDING.md`, and the material one is that a missing inspection rule now FAILS
the dispatcher preflight rather than being an optional extra.

### Changed

- `tools/codex-event-bridge/src/exec_policy.mjs` — the
  `managed-docker-inspection` profile: `DOCKER_INSPECTIONS`, `inspectionRules`,
  `auditInspectionRules`, `auditInspectionRulesFile`,
  `assertInspectionProvisioned`, and the `profile=` operand on the installed
  generator. `rulesFor` now shares one `allowRule` spelling with the new
  profile; its output is byte-unchanged.
- `tools/codex-event-bridge/src/event_bridge.mjs` — `start()` preflights the
  inspection profile ONCE, after the per-participant loop. The capability is
  the deployment host's rather than any identity's, and running it second keeps
  the per-participant refusal — the one carrying the exact install instructions
  — as the first thing a wrong file reports.
- `conf/codex-event-bridge.template.json` — the documented procedure appends
  the inspection profile into the same staged file, and states the boundary and
  the upgrade consequence.
- `tools/codex-event-bridge/smoke/exact_policy_matrix.mjs` — stages both
  generated profiles into the isolated `CODEX_HOME` and drives the four
  inspections as positives, unruled/mutable Docker as negatives, and probes
  that no negative mutated the runtime.

### Tests

- New `tools/codex-event-bridge/test/docker_inspection_policy.test.mjs` (11
  cases): the confirmed profile, exact satisfaction, the absent-rule defect,
  unrestricted `docker` and `docker image` as BROAD, eighteen mutable/unruled
  commands as EXTRA, operand-qualified inspections as a subset, non-bare Docker
  spellings, deny rules, unreadable files, profile independence on one file,
  and three dispatcher start refusals.
- New inspection cases in `test/exec_policy_cli.test.mjs` and new
  `tests/work/test_w2845_docker_inspection_policy.py` (the profile written out
  independently, the generator's exact emission, the audit's broad/extra split,
  and a check that each ruled prefix is a real Docker command).
- `tests/work/test_deploy_v11.py` — the DEPLOYED artifact emits and audits the
  inspection profile, refuses a misapplied `profile=` operand, the shipped
  template documents the step, and the documented procedure produces a file
  satisfying BOTH preflights while a participants-only file fails the
  inspection one.
- Five existing policy fixtures now carry the inspection rules, because
  `start()` preflights them. Additive; no assertion was changed or weakened.

Focused verification: `node --test` in `tools/codex-event-bridge` — 216 pass, 0
fail (was 201). `.venv/bin/python -m pytest tests/ -q` — 2873 pass, 0 fail.

### Evidence

`evidence/preflight-2026-08-22.txt`. Read-only throughout: the generator
prints, the auditor reads, and installing stays the operator's act. Nothing was
installed and the managed stack was not restarted.

### Left deliberately undone

- The LIVE managed inspection through an isolated app-server. It spends real
  model turns and stages a copy of the operator's Codex credential; the cases
  are in the matrix and the run belongs to the operator, per plan step 4.
- The parent `finding-v12-local-isolated-execution` plan index. W1425 is
  claimed by another handler and its `PLAN.md` already carries this item as
  step 1a; editing another handler's plan is not this implementer's to do.

### Observation for review, not corrected here

The preflight runs in `EventBridge.start()`, which is reached only when a
deployment configures `roleInstructions.execPolicyFile`. `codex-event-bridge
--start-thread` returns through `bootstrapThread` and never constructs the
bridge, so that bootstrap path preflights nothing. This is pre-existing and
unchanged by this Work — the inspection check sits exactly where the Baton
workflow check already sat — but it means the deployment's preflight coverage
depends on how the dispatcher is launched, and the live `infra.json` contexts
use the bootstrap form. Recorded rather than acted on: widening where the
preflight runs is outside this record's boundary.

### State

**Awaiting review.** No review pass has been recorded on this record yet.

## 2026-08-22 — round-1 review [P1] corrected, awaiting re-review

The review was right and the defect was larger than the two spellings it
demonstrated. My parser's stated safety property — "an unfamiliar construct is
invisible rather than misinterpreted as coverage" — was exactly backwards, and
I had written it confidently. Invisible IS coverage: a rule the auditor cannot
see is one it reports as absent, and absent is what satisfied means.

### What I found on top of the report

Probing the installed evaluator rather than reading my own regex: the policy
language is **Starlark**. Reversed keyword order and single quotes are two of
ten spellings that authorize unrestricted Docker — the others are mixed
quotes, positional operands, loose whitespace, a multi-line call, a variable,
a string concatenation and a `for` loop. No regular expression can be complete
against a full programming language.

**And it was never only a Docker defect.** The parser is shared with the Baton
workflow audit, so a reversed-keyword executable-only Baton rule was invisible
too — the broad-rule refusal W415's round-6 review established could be walked
past by respelling it. Fixed and covered in both lanes.

### Changed

- `tools/codex-event-bridge/src/exec_policy.mjs` — `readPolicy(text)` replaces
  the regular expression with a scanner that ACCOUNTS for every fragment:
  a fully decomposable `prefix_rule` (any keyword order, either quote style,
  positional or keyword, across lines), a blank line, a `#` comment, or
  UNACCOUNTED. Both `auditRules` and `auditInspectionRules` report
  `unaccounted` and both assertions refuse on it, quoting the fragment and
  saying to regenerate. `parseRules` is retained as `readPolicy(text).rules`.
  The superseded reasoning is kept in place with its correction beside it.

### Tests — 6 new Node cases plus deployed coverage

`tools/codex-event-bridge/test/policy_syntax.test.mjs`: the audit refuses all
ten spellings; the same hole is closed for the Baton profile; an unreadable
construct is refused rather than ignored, with the fragment quoted; blank
lines and comments are accounted for; the ruled prefixes are still recognised
in another valid spelling (fail-closed, not fail-blind); and **the installed
`codex execpolicy check` confirms each fixture really does authorize
`docker run --privileged alpine`** while the audit refuses it.

`tests/work/test_deploy_v11.py` — the deployed artifact carries the same
refusals, because a release shipping the old parser ships the hole.

### The oracle earned its place immediately

My multi-line fixture used tab indentation. The evaluator rejected the whole
file rather than authorizing it — Starlark forbids tabs — so the case failed
and I corrected the fixture. A test written from my reading of the language
would have been wrong in the same direction as the parser. The oracle cases
skip when Codex is absent; the pure-audit cases always run.

### Verification

`tools/codex-event-bridge` `npm test` — 222 pass, 0 fail (was 216). Full
pytest — 2873 pass, 0 fail. The live nominated policy still audits satisfied
for all three participants and the inspection profile, with no unaccounted
constructs. Read-only throughout: nothing installed, nothing restarted.

## Round 4 — the operand literals (2026-08-22)

`review-2026-08-22T13-29-42Z.md` requested changes with one release-blocking
P1. All three reported candidates were reproduced against the tree before any
edit, and they are real.

**The same class of defect a fourth time, one layer further in.** Rounds 1, 2
and 3 corrected what this module read as SYNTAX — the call shape, the string
escapes, the whitespace. Round 4 is a call built entirely from string
literals, in a shape the scanner fully decomposes, that the evaluator still
refuses to load. `decompose` stopped at "every operand is a plain literal" and
never asked whether the evaluator ACCEPTS those literals.

The consequence is round 3's, not round 1's: Codex loads NO rule from the
file — including the four inspection rules an operator installed correctly —
while the preflight advertises the deployment as ready, the next managed
inspection escalates for approval, and the non-interactive dispatcher
quarantines the context.

### Changed

- A REPEATED named operand makes the construct UNACCOUNTED. Last-value-wins
  was this module's semantics, not the evaluator's.
- An EMPTY PATTERN is UNACCOUNTED, in the keyword and the positional
  spelling, because both reach the same evaluator.
- The DECISION DOMAIN is the measured one: `allow`, `prompt`, `forbidden`,
  case-sensitive. Anything else is UNACCOUNTED.
- The refusal now names the operand-literal rules beside the whitespace ones,
  so an operator is not sent looking for whitespace that is not there.

### Found while measuring, not in the review

- **A duplicate `decision` is the same parse error and audited exact the same
  way.** The overwrite was never specific to `pattern`; correcting only the
  reported operand would have left an identical hole one keyword away.
- **The domain is case-sensitive.** `Allow` and `ALLOW` are refused by the
  evaluator, and a domain read off a grammar would probably have folded case.
- **An empty string ELEMENT is not an empty PATTERN.** `pattern=[""]` loads,
  and covers nothing because no argv element equals the empty string. It stays
  accounted; refusing it would be fail-blind.

### Superseded test coverage

`W2845: a deny rule is never inspection coverage` and the `deny` branch of
`W415: a BROAD rule is refused, not counted as coverage` spelled the
restriction `decision="deny"`, which the evaluator refuses — so both asserted
the audit's answer about a file Codex will not load, and neither could have
caught this. Both now use `forbidden`, which is evaluator-valid and still not
coverage. This was an explicit requirement of the review.

### Tests

`test/policy_syntax.test.mjs`: eleven evaluator-invalid literal candidates on
the inspection profile and three on the Baton profile, each confirmed
unloadable by the oracle before the audit is asked to refuse it; an
accepted-literals case pinning `prompt`, `forbidden` and the empty element;
and an oracle case re-measuring the accepted decision domain, so a future
Codex that changes it fails as a stale fixture rather than leaving the audit
quietly wrong. `tests/work/test_w2845_docker_inspection_policy.py` gains the
same three cases, and the deployed-artifact matrix in
`tests/work/test_deploy_v11.py` carries the refusals and the
fail-closed-is-not-fail-blind cases, because a release shipping the old
`decompose` ships the hole.

### Verification

`node --test` in `tools/codex-event-bridge` — 267 pass, 0 fail (was 263 after
this turn's W4303 work landed in the same tree; 227 at round 3). Full pytest —
2847 parallel + 52 serial, 0 fail. `tools/acp-baton-bridge` 55, `v12` 159.
The live nominated policy still reads 95 rules with 0 unaccounted, the
inspection profile still audits satisfied, and `baton.codex` and `baton.tuner`
still audit satisfied for all thirty ruled verbs — nothing this round refuses
was accounted for before it. Read-only throughout; no Docker command was
executed and mutable Docker was evaluated through `codex execpolicy` only.

### State

**Awaiting re-review.** The live matrix remains the operator acceptance step
and is still not run from an implementer turn.

## 2026-08-22 — round-2 review [P1] corrected, awaiting re-review

The review was right, and this is round 1's mistake repeated one level down.
Round 1 I replaced a regular expression that claimed to parse a language. The
replacement still claimed to decode that language's *strings*: `stringLiteral`
decoded `\n` and `\t` and otherwise dropped the backslash and copied the next
character. So `\x64ocker` read as `x64ocker` — a rule for nothing, invisible to
the Docker audit — while the evaluator decoded it as `docker` and authorized a
privileged container. Partial understanding presented as full accounting is
the defect both times.

### Changed

Only the escapes this module's own generator can emit are accepted — `\\`,
`\"`, `\'`, which is what `JSON.stringify` produces and which decode
identically here and in Starlark. Every other escape makes the construct
UNACCOUNTED and fails the preflight closed. The correction is a REMOVAL, not a
better decoder.

### Tests

The escape families joined the existing oracle case, so each is shown to
really authorize `docker run --privileged alpine` before the audit is asked to
refuse the same file. The Baton profile gained oracle coverage of its own
(hex- and octal-escaped absolute executable authorizing an unruled verb). A
new case proves fail-closed is not fail-blind: a generated policy for a path
containing a backslash, or a participant containing a quote, still round-trips
through its own auditor. `tests/work/test_deploy_v11.py` carries the same
refusals for the deployed artifact.

### Verification

`tools/codex-event-bridge` `npm test` — 223 pass, 0 fail (was 222). Full
pytest — 2873 pass, 0 fail. The live nominated policy still audits satisfied
for all three participants and the inspection profile, with no unaccounted
constructs. Read-only throughout; mutable Docker was evaluated through
`codex execpolicy` only and never executed.

### Stated limitation

A deployment whose paths need any escape other than those three cannot be
audited by this preflight. That is recorded in `FINDING.md` as the honest
answer rather than closed by guessing evaluator semantics a second time.

### State

**Awaiting re-review.** The live matrix remains the operator acceptance step.

## 2026-08-22 — round-3 review [P1] corrected, awaiting re-review

The review was right, and this is the same mistake a third time: a JavaScript
reading of the language standing in for an accounting of the file. `readPolicy`
skipped every character JS calls `\s`, so a TAB before the fourth generated
rule audited exact.

**What is different about this round, and why it is worse than it looks.**
Rounds 1 and 2 were privilege escalation — the evaluator authorized more than
the audit could see. Here the evaluator authorizes *nothing*: `Parse error:
tabs are not allowed` refuses the whole file, so none of the four rules is in
force, including the ones the operator installed correctly. The preflight
called that deployment ready.

### Changed

- The accepted whitespace is SPACE and LF, the two characters this generator
  emits, everywhere — top level and between operands inside a rule. It was
  MEASURED against `codex execpolicy check`, not read off a grammar.
- A top-level construct must BEGIN its line. That is a refusal to read
  indentation, not a reproduction of it.
- A line terminator inside a string literal makes the construct UNACCOUNTED;
  in Starlark it ends the literal rather than joining the operand.
- UNACCOUNTED is reported BEFORE missing/broad/extra. The reviewer's candidate
  otherwise refuses with "does not authorize [docker image inspect]" and tells
  the operator to install a rule the file already holds.
- The refusal renders the offending character: `\t`, `\x20\x20prefix_rule(...)`.
  A fragment whose whitespace the terminal swallowed looks exactly like the
  approved rule.

### Found while establishing the tab semantics, not in the review

A SPACE-indented statement is refused by the evaluator too ("unexpected new
indentation block"). Correcting only the reported character would have left an
identical defect one keystroke away. Refused, and covered.

### Tests

`test/policy_syntax.test.mjs` gained a measured table of eleven whitespace
candidates on both profiles, an accepted-spellings table, and an oracle case
asserting the evaluator cannot LOAD any refused candidate — so a future Codex
that started accepting one fails as a stale fixture rather than leaving the
audit quietly wrong. `tests/work/test_w2845_docker_inspection_policy.py` and
the deployed-artifact matrix in `tests/work/test_deploy_v11.py` carry the same
refusals and the same fail-closed-is-not-fail-blind cases.

### Verification

`npm test --prefix tools/codex-event-bridge` — 227 pass, 0 fail, 0 skipped
(was 223). Full pytest — 2824 parallel + 52 serial = 2876 pass, 0 fail (was
2873). The live nominated policy still reads with 0 unaccounted and audits
satisfied for all three participants and the inspection profile. It gained one
unrelated rule during this turn — a `node` rule for
`tools/codex-event-bridge/test/runtime_publisher.test.mjs`, appended by the
operator — taking it from 94 to 95. That rule is outside both audited profiles
and neither audit reports it; noted because earlier evidence in this record
says 94.
Read-only throughout; no Docker command was executed and mutable Docker was
evaluated through `codex execpolicy` only.

### Stated limitation

CRLF line endings are refused although the evaluator accepts them; this
generator never emits them. Recorded in `FINDING.md` rather than left to be
discovered. Comments are accounted for wherever they sit — own line, indented,
or trailing a rule — because all three load and refusing them would be
fail-blind.

### State

**Awaiting re-review.** The live matrix remains the operator acceptance step
and is still not run from an implementer turn.

## 2026-08-22 — round-5 review [P1] corrected, awaiting re-review

`review-2026-08-22T14-41-58Z.md`. All five reported forms reproduced against
the tree before any edit, and the review is right. Evidence:
`evidence/correction-round5-2026-08-22.txt`.

### The defect

`splitTopLevel` ended with `parts.filter((part) => part.trim() !== "")` under
a comment saying a trailing comma leaves an empty tail. The comment is true;
the code discards every empty field wherever it sits. So

```text
prefix_rule(pattern=["docker",, "image", "inspect"], decision="allow")
prefix_rule(pattern=[,"docker", "image", "inspect"], decision="allow")
prefix_rule(, pattern=["docker", "image", "inspect"], decision="allow")
prefix_rule(pattern=["docker", "image", "inspect"],, decision="allow")
prefix_rule(pattern=["docker", "image", "inspect"], decision="allow",,)
```

each decomposed into the same rule as its valid spelling and audited
`satisfied=true unaccounted=0`, while the evaluator refused the whole file
with `unexpected symbol ','` and loaded NONE of it — including the three
rules the operator installed correctly. Rounds 3 and 4's false-ready failure,
one punctuation layer in.

### Changed

`splitTopLevel` returns `null` — this module's existing "cannot account for
this" answer — instead of a filtered list, and `stringList` and `decompose`
both propagate it. Exactly one empty TAIL is dropped. `()` and `[]` hold no
field at all and are unchanged: an empty operand list is still round 4's
empty-pattern refusal.

### Found while measuring, not in the review

Two more forms, both refused by the evaluator and both previously exact:

- a DOUBLE trailing comma inside the pattern list, not only in the call;
- an empty middle field in the POSITIONAL spelling, which reaches the same
  evaluator and so has to reach the same refusal.

Correcting only the five reported forms would have left both.

### Tests

`test/policy_syntax.test.mjs` gains four cases — pure audit on the inspection
profile, the same on the Baton profile, the valid trailing comma in all four
places it can appear, and the oracle asserting BOTH directions: a refused
fixture the evaluator starts accepting is a stale fixture, and a trailing
comma it starts refusing would mean the audit had gone fail-blind the other
way. `tests/work/test_w2845_docker_inspection_policy.py` gains three
(pure-audit refusal, valid trailing comma, oracle), and
`tests/work/test_deploy_v11.py` carries the same refusals through the
DEPLOYED module, because a release shipping the old `splitTopLevel` ships the
hole.

Mutation-checked: restoring the single `filter` line fails exactly the two
new pure-audit Node cases and the two new Python lanes, and nothing else.

### Verification

- `tools/codex-event-bridge npm test` — 272 tests, 271 pass, **1 fail**.
- `pytest -n auto -m "not serial" tests/work` — 2850 passed.
- `pytest -m serial tests/work` — 52 passed.
- `tools/acp-baton-bridge npm test` — 55 passed. `v12 npm test` — 161 passed.
- Whitespace-damage check clean. Live nominated policy unchanged: 95 rules,
  0 unaccounted, inspection profile satisfied, `baton.codex`, `baton.tuner`
  and `baton.prompt` all satisfied.

### The one failing Node test is not this Work's

`test/failed_turn_settlement.test.mjs`, "a failed turn discovered only during
reconnect is settled", fails with
`{deliverable: true, orphan: null, incidents: 0}` against an expected
`{deliverable: false, orphan: '7ba67cb8-W2907', incidents: 1}`.

It is not mine and I did not touch it: the file is untracked and belongs to
the W4303 settlement work in flight, it imports no policy module, and it
fails IDENTICALLY with this round's change reverted — which I checked rather
than asserted. Reported here and in the handoff rather than fixed, worked
around, or left for the reviewer to trip over.

### Observed, not acted on

`test/policy_syntax.test.mjs` creates its fixture directory with
`mkdtempSync("/tmp/w2845-syntax-")` and never removes it, so every run leaves
one behind. That is my file and the same class of leak W2907 exists to fix in
`v12/`. I have not changed it in this round: it is unrelated to the P1 under
review and would add surface to a fifth review pass. Worth a follow-up.

### State

**Awaiting re-review.** The live exact-policy matrix remains the operator
gate and was not run from this turn. The reviewer's stated condition for it —
that the nominated-file preflight reject evaluator-invalid comma fields — is
now met.

## 2026-08-22 — round-6 review [P2] corrected, awaiting re-review

`review-2026-08-22T15-10-46Z.md`. Reproduced before any edit; the review is
right. Evidence: `evidence/correction-round6-2026-08-22.txt`.

### This one points the other way

Rounds 1-5 were privilege escalation or false-ready: the audit called a file
exact that the evaluator read more permissively, or could not read at all.
This one hides nothing. The evaluator loads the file and authorizes exactly
the ruled inspections; the dispatcher refuses to start and demands a
regeneration that cannot change what Codex authorizes. Fail-closed became
fail-blind, which this record has warned about since round 1.

**And it contradicts my own measurement.** Round 3's accepted table already
records "blank lines, including ones holding a tab". The table was right and
the code did not implement it — the same shape as round 5, where the comment
stated the rule and the `filter` under it did something else. Two rounds
running, the defect sat between a correct written rule and the line below it.

### Changed

`readPolicy` decides blank-line whitespace for the whole LINE, via
`blankLineEnd`, and the tolerated set is exactly SPACE and TAB — measured one
character at a time rather than reasoned from `ACCEPTED_WHITESPACE`.

That it is a LINE rule and not a character exemption is load-bearing: a
TRAILING tab after a rule is the same character and the evaluator refuses it.
A character-level exemption would have accepted it and reopened round 3. It is
covered as a negative, beside form feed, vertical tab, NBSP, U+3000 and U+FEFF
on their own lines — every one of which the evaluator refuses even alone.

### Measured

TAB, SPACE+TAB, and a tab-only last line with or without a final newline all
LOAD. Vertical tab, form feed, NBSP, U+1680, U+2000, U+2028, U+2029, U+202F,
U+205F, U+3000 and U+FEFF each make the evaluator refuse the whole file even
alone on a line.

### Stated limitation, narrowed rather than widened

A blank line holding a lone CARRIAGE RETURN loads in the evaluator and is
still refused here, under the CRLF limitation this module has carried since
round 3. A lone CR is a whole-file line-ending property and this generator
emits LF; a TAB arrives from an operator pressing Tab on an empty line, which
is exactly the case the accepted-spelling boundary exists for. Re-measured and
stated so the next reader knows the narrowing is deliberate.

### Tests

`test/policy_syntax.test.mjs` gains three cases — the accepted blank lines on
both profiles, the negatives that must not reopen round 3 (including round 3's
own fixtures re-asserted), and the oracle in both directions.
`tests/work/test_w2845_docker_inspection_policy.py` gains three and
`tests/work/test_deploy_v11.py` carries both halves through the DEPLOYED
module. Mutation-checked: restoring the one-line refusal fails exactly the two
new pure-audit lanes and nothing else.

### Verification

- `tools/codex-event-bridge npm test` — 283 tests, 282 pass, **1 fail**.
- `pytest -n auto -m "not serial" tests/work` — 2853 passed.
- `pytest -m serial tests/work` — 52 passed.
- `tools/acp-baton-bridge npm test` — 55. `v12 npm test` — 161.
- Whitespace-damage check clean. Live nominated policy unchanged: 95 rules,
  0 unaccounted, inspection profile and all three dispatched participants
  satisfied. This round only ADDS accepted spellings, so no file that audited
  exact before it can fail now.

### The one failing Node test is W4303's

`failed_turn_settlement.test.mjs`, "a reconnect settlement racing late
turn/completed files one incident", asserting `2 !== 1` on "concurrent
settlement observers filed the same incident twice". It is a reviewer-added
regression for W4303's current review round, in an untracked file that imports
no policy module, and it fails identically with this round's change reverted —
checked, not asserted. Reported, not touched.

### Still open from round 5

`policy_syntax.test.mjs` creates its fixture directory with `mkdtempSync` and
never removes it. Unchanged this round for the same reason: unrelated to the
finding under review. Worth a follow-up.

### State

**Awaiting re-review.** The live exact-policy matrix remains the operator gate
and was not run from this turn.

## 2026-08-22 — round-7 review [P2] corrected, awaiting re-review

`review-2026-08-22T15-47-35Z.md`. Reproduced before any edit; the review is
right. Evidence: `evidence/correction-round7-2026-08-22.txt`.

### The rule was pinned in round 3 and never implemented

Round 3's measured table says a comment is accounted for wherever it sits,
"indented, or trailing a rule", and round 3 has an accepted-spelling case for
an indented comment. That case passes because a SPACE is accepted whitespace
and falls through to the comment branch by accident — nothing implements
indentation. Round 6 then added a case named "tab inside a comment" that puts
the tab AFTER the `#`, which reads like coverage of this and is not.

So this is the second round running where a correct written rule and the code
under it disagreed, and the third where measuring rather than reading is what
found the gap. Round 6's blank-line rule and this one are the same shape one
case apart.

### Changed

`commentLineEnd` scans from the START of the line: SPACE/TAB indentation
followed by `#` consumes the line as a comment; anything else does not. At an
`OTHER_WHITESPACE` character the scanner now tries the blank-line rule and
then this one before refusing.

It is deliberately a LINE rule and not a character exemption, and the case
that proves the difference is `rule<TAB># note` — a tab-indented comment
SHARING a line with a rule, which the evaluator refuses because that tab is in
code. A character-level exemption would have accepted it. It is covered as a
negative.

### Measured

One tab, several tabs, and space+tab mixed before `#` all LOAD, as does the
same at end of file with or without a final newline. A form feed, vertical tab
or NBSP before `#` each make the evaluator refuse the whole file. A tab before
a rule, trailing a rule, or sharing a line with one is refused exactly as
before.

### Tests

`test/policy_syntax.test.mjs` gains three cases — the accepted indented
comments on both profiles, the negatives including rounds 3 and 6 re-asserted
rather than trusted, and the oracle in both directions.
`tests/work/test_w2845_docker_inspection_policy.py` gains three and
`tests/work/test_deploy_v11.py` carries both halves through the DEPLOYED
module. Mutation-checked: dropping the `commentLineEnd` branch fails exactly
the two new pure-audit lanes and nothing else.

One fixture correction worth naming: my first NBSP negative used a literal
character that did not survive the edit as an NBSP, so the case passed
vacuously. It now uses an explicit ` ` escape — and it failed loudly
first, which is why I noticed.

### Verification

- `tools/codex-event-bridge npm test` — 286 tests, 285 pass, **1 fail**: the
  W4303 reviewer regression, which imports no policy module and which this
  round's reviewer disclosed in the same report.
- `pytest -n auto -m "not serial" tests/work` — 2883 passed.
- `pytest -m serial tests/work` — 52 passed.
- `tools/acp-baton-bridge npm test` — 55. `v12 npm test` — 186.
- Whitespace-damage check clean. Live nominated policy unchanged: 95 rules,
  0 unaccounted, inspection profile and all three dispatched participants
  satisfied. This round only ADDS accepted spellings.

### Unchanged

The carriage-return limitation stands and was re-measured: a CR before a
comment loads in the evaluator and is still refused here, under the CRLF
boundary carried since round 3.

### Still open from round 5

`policy_syntax.test.mjs` leaks its `mkdtempSync` fixture directory. Unrelated
to the finding under review; still worth a follow-up.

### State

**Awaiting re-review.** The live exact-policy matrix remains the operator gate
and was not run from this turn.

## 2026-08-22 — round-8 review [P2] corrected, awaiting re-review

`review-2026-08-22T16-46-17Z.md`. Reproduced before any edit; the review is
right. Evidence: `evidence/correction-round8-2026-08-22.txt`.

### The round-3 promise, kept rather than narrowed

Round 3 pinned that a comment is accounted for "wherever it sits", and the
review is right that inside a literal call is one of those places — and right
that the alternative was to supersede that promise explicitly and justify the
narrower boundary. There is no justification available: the evaluator loads
the comment and honours the rule, so refusing it only rejects correct operator
text.

### A mask, not a parser

Comment spans are blanked to spaces before any structural scan, so
`matchingParen`, the whitespace accounting and the operand reader never see
comment text. That is what satisfies the review's other constraint directly: a
body carrying quotes, commas, brackets or parentheses cannot become syntax
because it never reaches the splitter. The reproduction showed one such
comment producing FOUR unaccounted fragments — comment punctuation being read
as structure, exactly what the review warned about. Length is preserved, so
every quoted refusal fragment still lines up with the original text.

### Two boundaries the mask does not cross, both measured

- A `#` inside a STRING is data; a regression reads the operand back through
  the scanner to prove `not#docker` is one string.
- A TAB before the `#` is a tab in CODE and stays refused, because the
  evaluator refuses it — measured inside a construct this round rather than
  assumed from the top-level case.

### Tests

`test/policy_syntax.test.mjs` gains three cases,
`tests/work/test_w2845_docker_inspection_policy.py` three, and
`tests/work/test_deploy_v11.py` carries both halves through the DEPLOYED
module. Rounds 3, 6 and 7's negatives are re-asserted inside the new cases
rather than trusted. Mutation-checked: replacing the mask with the raw text
fails exactly the two new pure-audit lanes.

### Verification

- `tools/codex-event-bridge npm test` — **293 pass, 0 fail**.
- `pytest -m serial tests/work` — 52 passed.
- `pytest -n auto -m "not serial" tests/work` — 2905 passed, 2 failed.
- `tools/acp-baton-bridge npm test` — 55 passed.
- `v12 npm test` — 196 tests, 191 pass, 5 failed.
- Whitespace-damage check clean. Live nominated policy unchanged: 95 rules,
  0 unaccounted, inspection profile and all three dispatched participants
  satisfied. This round only ADDS accepted spellings.

### The seven other failures are not this Work's

Two are W4996's reviewer-added cases against `src/baton_work/tui/graph.py`;
five are W2929's, from `review-2026-08-22T17-30-46Z.md` against
`v12/src/worker_manager/`. Both Works are queued on `baton.impl` awaiting
their own turns, neither shares a module with
`tools/codex-event-bridge/src/exec_policy.mjs`, and neither was touched from
here.

### Still open from round 5

`policy_syntax.test.mjs` leaks its `mkdtempSync` fixture directory. Unrelated
to the finding under review; still worth a follow-up.

### State

**Awaiting re-review.** The live exact-policy matrix remains the operator gate
and was not run from this turn.

## Round 9 — the mask's index space (2026-08-22)

`review-2026-08-22T17-42-34Z.md`, one [P2]. Reproduced before any edit;
correct. Evidence: `evidence/correction-round9-2026-08-22.txt`.

### What I had wrong

I introduced this last round, in the change that added masking. `maskComments`
built its output with `[...text]` — code POINTS — while the masking loop and
every scanner below it index by UTF-16 code UNITS. One emoji in a comment made
the two spaces diverge, so mask writes landed one element late, the mask
stopped lining up with the source, and a later VALID rule was misclassified.
The evaluator loaded those policies and authorized the ruled inspection; only
the audit refused them. That is the rounds 6-8 direction a fourth time: no
capability hidden, but a valid policy refused at startup with a regeneration
request that cannot change what Codex authorizes.

`text.split("")` is the correction, and `maskComments` now throws unless the
mask is the source's exact length.

### Tests — 32 Node (30 before), plus both pytest lanes

The reviewer's two additive cases are retained. Added: five astral fixtures —
top-level comment, in-rule comment, trailing comment on an operand line,
several at both levels, and astral inside a string operand — each with a LATER
rule, which is the only thing that makes drift observable at all. Run through
the pure audit, `assertInspectionProvisioned`, the managed-workflow profile,
and the installed evaluator as the oracle; then the same fixtures in
`test_w2845_docker_inspection_policy.py` and, on BOTH shared profiles, in the
deployed-artifact lane of `test_deploy_v11.py`.

Mutation: reverting to `[...text]` fails exactly two Node cases and two pytest
cases — one of each is the reviewer's.

**The length throw is NOT witnessed** and cannot be from outside the module.
It is unreachable while the mask is correct, and the only way to reach it is
to reintroduce the defect. Recorded as a guard rather than presented as
covered; see `FINDING.md`.

### Verification

- `tools/codex-event-bridge npm test` — **297 pass, 0 fail**.
- `pytest -n auto -m "not serial" tests/work` — 2916 passed, 5 failed.
- `pytest -m serial tests/work` — 52 passed.
- `tools/acp-baton-bridge npm test` — 55 passed. `v12 npm test` — 200/202.
- Whitespace check clean. Live nominated policy unchanged: 95 rules, 0
  unaccounted, inspection profile and all three participants satisfied.

### The seven failures are not this Work's

One is W4615's reviewer case against my own correction there; four are
W4996's against the dependency graph; two are W2929's in `v12`. All three
Works are queued on `baton.impl` awaiting their own turns, none shares a
module with `exec_policy.mjs`, and none was touched from here.

### Still open from round 5

`policy_syntax.test.mjs` leaks its `mkdtempSync` fixture directory.

### State

**Awaiting re-review.** The live exact-policy matrix remains the operator gate
and was not run from this turn.

## The matrix oracle — 2026-08-22

`review-2026-08-22T20-31-27Z.md`, one P1, after
`review-2026-08-22T18-25-27Z.md` signed off the generator, auditor and
parser. Nothing in `exec_policy.mjs` changed this turn. Evidence:
`evidence/correction-oracle-2026-08-22.txt`.

### What was wrong

The matrix observed only the METHOD names of server requests during a turn: a
Docker positive passed when that list was empty and a negative passed when it
was not. The operator run produced an empty list for ALL EIGHT cases, so one
body of evidence read as PASS on four and FAIL on four.

The review is right that this is a shared oracle defect rather than a
disagreement about expected approval behaviour. "No approval arrived" is
neither "the inspection ran" nor "the command was refused".

### Changed

`src/command_oracle.mjs`, pure: one turn, one requested command, the observed
approvals, a verdict with a reason. A ruled inspection passes only when
exactly one agent command item matching the request is `completed` at exit 0
with no correlated approval. An unruled command is refused only when it is
`declined`, or when a correlated approval was denied and the item reached a
terminal state that is not `completed`.

A bare `failed` is NOT a refusal — a Docker command can fail on its own
merits, and reading that as the boundary would make the matrix pass while the
boundary was wide open. Approvals are correlated by thread, turn and item id
rather than counted; an approval raised by something else says nothing about
this command.

`runCase` reads the exact turn back after completion through `thread/read`
with `includeTurns`, selected by the id `turn/start` returned.

### Measuring the schema caught a defect of my own

The reviewer left the generated schema in place, so I read the field names
and enums out of it rather than from the review's prose. `source` carries
`"default": "agent"` and is NOT required — and my first filter demanded it.
An item that omits the field is the ordinary agent case, so requiring it
would have reported a ruled inspection that ran perfectly as "the model never
attempted the command": the exact ambiguity this correction removes,
reintroduced through the fix. It has its own case now.

### Verification

- `tools/codex-event-bridge npm test` — **311 pass, 0 fail** (297 before).
- 14 synthetic-turn cases covering absent, wrong, duplicate, extra,
  completed, failed, declined and inProgress items, correlated and unrelated
  approvals, and the schema-default source.
- Five mutations, each fails the cases that name it.
- `pytest -n auto -m "not serial" tests/work` — 2953 passed, 3 failed;
  acp-baton-bridge 55/55; v12 238/239; whitespace clean. None of those four
  is this Work's — three are W4996 reviewer cases and one is W2929's, from
  reviews that landed while this turn was running.

### Not done, and not mine

The credential-bearing matrix rerun. It needs live provider credentials and a
running app-server, it has been the operator gate throughout this Work, and
installation plus the managed-stack restart stay blocked behind it. Claiming
the boundary verified without it would be the same kind of inference the
finding is about.

### State

**Awaiting re-review of the oracle**, with the live rerun still the operator
gate.

## The matrix oracle, round 2 — 2026-08-22

`review-2026-08-22T21-02-03Z.md`, one P1, against the oracle I landed earlier
in this session. Reproduced before any edit; correct. Evidence:
`evidence/correction-oracle-round2-2026-08-22.txt`.

### What I had wrong

Two faults with one shape: I checked that an approval was ABOUT this item and
never that it was the right KIND of approval, or that the client actually
ANSWERED it.

**Identity is not sufficient.** The installed schema gives
`item/fileChange/requestApproval` and `item/permissions/requestApproval` the
same `threadId`/`turnId`/`itemId` triple as the command approval. So a
file-change or permission prompt in the same turn was read as
command-execpolicy evidence — and that can ACCEPT an unruled case whose
command merely `failed`, which is the exact state the correction otherwise
refuses. Refusing a bare `failed` was the point; an unrelated approval let it
back in through the other door.

**An observed request is not an answered one.** `respondError` returns false
when it cannot send, and `runCase` discarded the result. The matrix's claim is
that it denies exactly as the dispatcher denies; an unanswered prompt shows
only that the boundary asked.

### Changed

`approvalsFor` matches method and identity. `runCase` records `denied` from
`respondError`'s own result. The unruled approval path requires a SENT denial
on top of the terminal non-completed item. A ruled inspection still fails on
the mere request, answered or not — the reason those four are ruled is that
nothing asks about them at all. A direct `declined` still needs no approval,
and a bare `failed` is still insufficient.

### The fixture spelling, and why it mattered

My synthetic approvals said `commandExecution/requestApproval`; the schema
defines `item/commandExecution/requestApproval`. Method-blind correlation hid
it exactly — a name nothing compares cannot be wrong. The fixtures build from
the exported constant now, so the product and the cases cannot drift apart
again. The review is right that the spelling was a symptom rather than a
separate slip.

### Verification

- `tools/codex-event-bridge npm test` — **316 pass, 0 fail** (311 before).
- 19 oracle cases; four mutations, each fails the cases that name it.
- `pytest -n auto -m "not serial" tests/work` — 2953 passed, 3 failed (all
  W4996 reviewer cases); acp-baton-bridge 55/55; v12 239/239; whitespace
  clean; the matrix parses.

### Still the operator gate

The credential-bearing rerun, installation and the managed-stack restart. The
review says to hold them until this boundary is corrected AND independently
re-reviewed, so they wait on the re-review rather than on this turn.

### State

**Awaiting re-review of the corrected correlation.**

## The absent command items are the SERVER, not the prompt — 2026-08-23

Implementer: baton.claude. Evidence: `evidence/measured-cause-2026-08-23.txt`.

### Why I measured before implementing

Item 27's items 1 and 2 — a dedicated Docker phase and a stricter prompt —
only help if the model is not invoking the shell tool. That is a claim about
the world, and it is cheap to test.

### The decisive probe

A turn cannot be argued into having run a command; it can be caught having run
one. Asked for `date +%s%N` — a value it cannot know without executing — the
agent returned a nanosecond timestamp **inside the run window**, and
`thread/read includeTurns` returned **no `commandExecution` item** for that
turn. An independent `/bin/echo` probe agrees.

`CommandExecutionThreadItem` is declared in the installed schema's `ThreadItem`
union, so this is the running server (codex-cli 0.149.0) not recording it.

### What that means

**The diagnosis behind items 1 and 2 is refuted.** The model does invoke the
tool. A stricter prompt would change behaviour that is already correct, and
the eight cases would fail identically. So I did not implement them — and I am
not proposing an oracle relaxation either, because the review is right that
none is acceptable.

The oracle's premise is not met by this server build. That is a deployment
fact for `baton.ops`, not something an implementer can prompt around.

### What I did implement

Item 3, the bounded missing-attempt diagnostic — right whatever the cause, and
the thing that made the cause findable. A fail-closed rejection that retains
nothing is a correct rejection nobody can act on, which is how eight cases
became "the reason is not recoverable".

It renders the turn id and status, the ordered item types, agent-message text
truncated with its true length, and any agent commands. The exclusions are the
design: `reasoning` items contribute their type and nothing else. It decides
nothing — giving it a verdict would make prose evidence again.

Item 4's diagnostic regressions are added. Item 5's boundaries and the oracle
are untouched.

### Verification

- codex-event-bridge **328/328**; pytest **2977 + 52 serial**;
  acp-baton-bridge 55/55; v12 492/492; matrix syntax and whitespace clean.
- The live 21-case matrix is **not** rerun: on the measured evidence it fails
  the same eight cases for the same reason, and producing that result again is
  not evidence anybody needs.

### State

**Awaiting independent review**, and `baton.ops` needs the measured cause
before accepting item 27 as written.

## The bounded diagnostic, actually bounded — 2026-08-23

`review-2026-08-23T04-49-11Z.md`, one P2. Reproduced first: the reviewer's
1000 commands of 1000 characters produced a **1,029,041-character** summary.
Correct. Evidence:
`evidence/correction-bounded-diagnostic-2026-08-23.txt`.

### A cap on the parts is not a bound on the whole

I capped each agent message and called the helper bounded. It then emitted
every item type, every message, every command and each full command string,
and concatenated all of them into the summary.

**What makes it worse than an oversight is when it fires.** This diagnostic
exists for the moment a model goes off-script — which is exactly the moment a
turn has a thousand items, and exactly the moment the operator log must stay
readable. The one input that triggers it is the one input that broke it.

I also wrote "BOUNDED ON PURPOSE" in the doc comment. A comment claiming a
property the code does not have is worse than no comment: it is the reason
nobody looks.

### The correction

Hard caps on counts as well as sizes, kept **private**, with a caller-supplied
`limit` able only to tighten — an exported helper its caller can make
unbounded is unbounded, and "no current caller passes a large limit" is a
property of today's callers.

True totals are always reported and every cut list carries an explicit
omission marker, because the **count is often the finding**: eight cases with
zero command items is the whole of this Work's current state.

Same reproduction now: **1,029,041 → 3,095** characters, both totals intact.

### Verification

- codex-event-bridge **333/333**; pytest **2977 + 52 serial**; acp 55/55;
  v12 492/492; matrix syntax and whitespace clean.
- Six mutations, all six witnessed. H4 keeps every hard constant and only lets
  `limit` through unclamped — a private maximum a parameter can exceed is not
  a maximum.

### State

**Awaiting re-review.** The strict oracle, the eight exact commands, the Baton
cases, the non-mutation probe and cleanup are unchanged, and the live matrix
still cannot pass on this build — W7989.

## The bounded diagnostic, bounded in every dimension — 2026-08-23

`review-2026-08-23T05-04-02Z.md`, one P2. Both shapes reproduced against the
shipped helper before any edit. Correct. Evidence:
`evidence/correction-bounded-diagnostic-round2-2026-08-23.txt`.

### A clamp a non-number walks through is not a clamp

`Math.min(NaN, hardMaximum)` is NaN, and `length > NaN` is false — so
`limit: NaN` did not tighten the cap, it **removed** it.

**The failure direction is the point.** A clamp that fails toward a smaller
cap announces itself the first time a diagnostic looks truncated. This one
failed *off*, which looks like nothing at all until the day it matters — the
same day this diagnostic exists for.

### A hard property that depends on the protocol is the protocol's

I capped the *count* of item types and not the *strings*, and the same held
for the turn id, the turn status and each command status. Protocol-conforming
values are small — a fact about conforming producers, which this helper's
stated hard-output property was resting on, in a diagnostic whose whole
purpose is the turn that did something unexpected.

Every externally supplied string retained in the result or the summary is
capped now.

### Verification

- codex-event-bridge **336/336**; pytest **2977 + 52 serial**; acp 55/55;
  v12 492/492; matrix syntax and whitespace clean. No Docker command executed.
- Five mutations, four witnessed. The summary backstop is **inert** with every
  field capped — recorded, kept for the next uncapped field somebody adds, and
  not counted as a guard.

### State

**Awaiting re-review.** The strict oracle, the eight exact commands, the Baton
cases, the non-mutation probe and cleanup are unchanged, and the live matrix
still cannot pass on this build — W7989.
