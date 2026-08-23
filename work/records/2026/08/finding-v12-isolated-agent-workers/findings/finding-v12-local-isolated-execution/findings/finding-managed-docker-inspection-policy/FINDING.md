# Finding: authorize bounded Docker inspection for managed M2 review

Child of W1425, the v12 M2 local-isolated-execution milestone.

## Observed

Two managed `baton.codex` turns were quarantined after requesting interactive
approval for the read-only command
`docker version --format '{{json .}}'`. Restarting created a safe fresh context
but did not change the execution policy, so the same research step failed
again.

## Confirmed boundary

The managed policy may authorize only these read-only Docker prefixes:

- `docker version`
- `docker info`
- `docker inspect`
- `docker image inspect`

It must not authorize an executable-only `docker` prefix. Mutable runtime
operations are exercised through the constrained Worker Manager adapter, not
directly by a model-issued Docker command.

## Acceptance

The deployment-owned generator emits the four ruled prefixes, its auditor and
tests distinguish them from an unrestricted Docker rule, the installed policy
can be provisioned without hand editing, and a managed turn can execute each
inspection without requesting interactive approval. Negative evidence proves
that representative mutable Docker commands remain unauthorized.

## Implementation revalidation — 2026-08-22 (baton.claude, W2845)

Every claim above was re-checked against the current tree before acting. The
confirmed boundary is unchanged and nothing here supersedes it; the entries
below are decisions the ruling left open, pinned so review can rule on them.

**Confirmed against the live deployment.** The operator had already hand-added
the four rules to `~/.codex/rules/baton.rules`, keeping the pre-fix file as
`baton.rules.before-docker-inspection-20260822`. The hand-installed text is

```text
prefix_rule(pattern=["docker", "version"], decision="allow")
prefix_rule(pattern=["docker", "info"], decision="allow")
prefix_rule(pattern=["docker", "inspect"], decision="allow")
prefix_rule(pattern=["docker", "image", "inspect"], decision="allow")
```

which the generator now reproduces byte-for-byte
(`evidence/preflight-2026-08-22.txt`). That backup is also the exact policy the
two quarantined turns ran under, so it serves as the negative baseline.

### Pinned implementation decisions

- **A SECOND profile, `managed-docker-inspection`, not more entries in the
  `managed-work-workflow` set.** The workflow profile is one participant's
  authority over the coordination authority and every rule in it names a
  binary, a config and a participant. Host inspection names none of them.
  Merging the two would produce a rule set that changes when an unrelated
  identity does, and an audit that could not say which ruling a refusal came
  from. The generator prints it from `profile=managed-docker-inspection`,
  taking no other operand, and the operator runs it ONCE per deployment rather
  than once per participant.
- **The pattern names a bare `docker`, while every Baton rule names an ABSOLUTE
  executable.** A prefix rule matches the argv it is given: the dispatcher
  hands a managed turn the absolute installed Baton path, but a turn inspecting
  the host types `docker version`, and a pattern of `/usr/bin/docker` would
  never match it. This genuinely pins less than the Baton rules do — PATH
  decides which `docker` runs — and it is accepted because the capability is
  read-only and the verb slot is still exact. It is also the shape the operator
  installed by hand and the shape the quarantined command took.
- **A missing inspection rule FAILS the dispatcher preflight**, exactly like a
  missing ruled verb. The failure is identical — the turn escalates for
  interactive approval, the non-interactive dispatcher denies it, the context
  is quarantined and the Work sits unclaimed — so treating it as an optional
  extra would leave the defect reachable. A host without Docker still installs
  the four rules; they authorize a command that then fails on its own terms,
  which is an error the model can read rather than an approval request nobody
  is there to answer. **Consequence for deployment:** a policy file generated
  before this change carries no Docker rule and the dispatcher will refuse to
  start until it is regenerated. That refusal names the four missing prefixes.
- **BROAD and EXTRA are reported separately**, because they need different
  corrections. `docker` alone — and `docker image` alone, which an operator
  might reach for while reading the fourth prefix — covers a ruled inspection
  AND every mutable command beside it, so the correction is to remove that
  rule. `docker run` covers no ruled inspection at all, so the correction is to
  delete it and reach the runtime through the Worker Manager adapter. A narrow
  rule never cancels a broad one; both are simply present.
- **No list of forbidden Docker subcommands is maintained.** The profile is the
  four prefixes and anything else naming a Docker executable is outside it,
  whatever it does. This is the same reasoning that let the Baton extra-verb
  test avoid maintaining a second copy of Baton's grammar. A representative
  mutable set lives in the regressions as a sample, never as the implementation.
- **The audit recognises any executable slot naming Docker**, not just the bare
  spelling the generator emits, so `/usr/bin/docker run` is reported rather than
  invisible. An absolute-path INSPECTION rule is reported too: it is a different
  command string, and the auditor cannot know the path resolves to the same
  binary.
- **A ruled inspection carrying operands is a subset, not extra.**
  `docker version --format '{{json .}}'` — the command the quarantined turns
  ran — authorizes less than `docker version` already does. It does not COVER
  the ruled prefix on its own, so a policy holding only the qualified form still
  fails the preflight.
- **Both profiles audit independently on the one nominated file.** Neither
  counts the other's rules as a defect, and a Docker defect stays a Docker
  refusal rather than surfacing as a Baton one.

### Acceptance not established here

The dispatcher preflight reads the file the deployment NOMINATES; it is not a
measurement of the policy the app-server actually loaded. The effective
boundary is established by the live matrix in
`tools/codex-event-bridge/smoke/exact_policy_matrix.mjs`, which now stages both
generated profiles into an isolated `CODEX_HOME` and drives the four
inspections as positives and unruled/mutable Docker as negatives. That run is
manual: it needs a Codex binary, spends real model turns, and stages a copy of
the operator's Codex credential. It is left to the operator/reviewer, per this
record's plan step 4.

## Correction after independent review — 2026-08-22 (baton.claude)

`review-2026-08-22T05-48-15Z.md` requested changes with one release-blocking
P1: valid alternate rule syntax bypassed the unrestricted-Docker refusal. The
review was right, the defect was worse than the two spellings it demonstrated,
and it was never only a Docker defect. Evidence:
`evidence/correction-2026-08-22.txt`.

### Superseded 2026-08-22 — "an unfamiliar construct is invisible rather than
### misinterpreted as coverage"

That sentence was the parser's stated safety property, written when the
auditor was one regular expression matching
`prefix_rule(pattern=[...], decision="...")`. **It is exactly backwards.**
Invisible IS misinterpreted as coverage: a rule the auditor cannot see is a
rule it reports as absent, and absent is what "satisfied" means. The reviewer
proved it against the installed evaluator — appending either

```text
prefix_rule(decision="allow", pattern=["docker"])
prefix_rule(pattern=['docker'], decision='allow')
```

to the four exact rules makes `codex execpolicy check` authorize
`docker run --privileged alpine` while the audit returned `satisfied: true`.

**Probing further made the scale clear.** The policy language is Starlark. A
variable, a string concatenation and a `for` loop each authorize the same
thing, and so do positional operands, mixed quotes, loose whitespace and a
multi-line call. No regular expression can ever be complete against a full
programming language, so the previous approach was not one spelling short — it
was the wrong shape.

### The corrected boundary — confirmed 2026-08-22

**The module stops parsing a language and starts ACCOUNTING for a file.** The
nominated policy is deployment-owned and generated by this module; in the
approved state it holds exactly the generated rules, blank lines and `#`
comments. `readPolicy` scans it and every fragment falls into one of three
places:

- a `prefix_rule(...)` it can fully decompose into string literals — in any
  keyword order, either quote style, positional or keyword, across lines;
- a blank line or a `#` comment; or
- **UNACCOUNTED**, which fails the preflight closed with the fragment quoted
  and an instruction to regenerate.

"I do not understand this file" and "this file is exact" are different
answers, and only one of them was ever safe to give.

**Fail-closed is not fail-blind.** An operator who hand-wrote the approved
rules in another valid spelling has a correct policy, and the preflight says
so rather than reporting them missing. Regressions cover both directions.

**The same hole existed in the BATON workflow profile.** The parser is shared,
so a reversed-keyword executable-only Baton rule was invisible exactly as the
Docker one was, and the broad-rule refusal that W415's round-6 review
established could be walked past by respelling it. Both audits now refuse on
unaccounted content and both are covered.

### Pinned: the real evaluator is the oracle for these regressions

`tools/codex-event-bridge/test/policy_syntax.test.mjs` asks
`codex execpolicy check` whether each fixture genuinely authorizes an unruled
mutable command, and only then asserts that the audit refuses that same file.
This is deliberate rather than decorative: the previous parser was wrong about
what the language accepts, so a test written from my reading of the language
would have been wrong the same way. It was — the multi-line fixture originally
used tab indentation, and the evaluator rejected the whole file instead of
authorizing, because Starlark forbids tabs. The oracle caught it. The oracle
cases skip when Codex is absent; the pure-audit cases always run.

The deployed-artifact matrix in `tests/work/test_deploy_v11.py` carries the
same coverage, because a release shipping the old parser ships the hole.

## Correction after re-review — 2026-08-22 (baton.claude)

`review-2026-08-22T06-59-24Z.md` confirmed round 1's spellings as refused and
found the same class of defect one level down: ordinary Starlark string
escapes. Evidence: `evidence/correction-round2-2026-08-22.txt`.

### Superseded 2026-08-22 — the partial escape decoder

`stringLiteral` treated every backslash sequence as syntax it fully
understood. It decoded `\n` and `\t` and otherwise dropped the backslash and
copied the next character — which is not Starlark's semantics. So a rule whose
pattern was written `"\x64ocker"`, `"docker"` or `"\144ocker"` read here
as a rule for `x64ocker` / `u0064ocker` / `144ocker` — a rule for nothing,
invisible to the Docker audit — while the installed evaluator decoded the
executable as `docker` and authorized `docker run --privileged alpine`. The
audit reported `satisfied: true` with `broad`, `extra` and `unaccounted` all
empty. The shared reader meant an escaped ABSOLUTE executable hid from the
Baton workflow audit the same way.

**This is round 1's mistake repeated at a smaller scale.** Round 1 replaced a
regular expression that claimed to parse a language; the replacement still
claimed to decode that language's strings. Partial understanding presented as
full accounting is the defect both times.

### The corrected boundary — confirmed 2026-08-22

**Only the escapes this module's own generator can emit are accepted:** `\\`,
`\"` and `\'`, which is what `JSON.stringify` produces for a backslash or a
quote inside an operand, and which decode identically here and in Starlark.
Every other escape sequence makes the construct UNACCOUNTED, so hex, Unicode,
long-Unicode, octal and anything neither reviewer nor implementer has thought
of all fail the preflight closed. Raw and triple-quoted strings were already
unaccounted and remain so.

**Fail-closed is not fail-blind, and there is a regression for it.** A policy
generated for a path containing a backslash, or a participant containing a
quote, still round-trips through its own auditor. **A deployment needing any
OTHER escape cannot be audited by this preflight**, and that refusal is the
honest answer: its exact evaluator semantics would have to be established
against the oracle first rather than guessed a second time.

The oracle regressions now cover the escape families on BOTH profiles: each
fixture is shown to really authorize an unruled command before the audit is
asked to refuse the same file.

## Correction after third review — 2026-08-22 (baton.claude)

`review-2026-08-22T12-51-09Z.md` confirmed the escape families as refused and
found the same class of defect a third time, on the DENIAL side: whole-file
accounting classified every JavaScript whitespace character as harmless.
Evidence: `evidence/correction-round3-2026-08-22.txt`.

### Superseded 2026-08-22 — "skip every `\s` character"

`readPolicy` skipped every character JavaScript calls whitespace, at the top
level and, through `trim()`, inside a construct. The installed evaluator does
not. The reviewer placed one TAB before the fourth generated inspection rule:
`auditInspectionRules` returned `missing=[]`, `broad=[]`, `extra=[]`,
`unaccounted=[]`, `satisfied=true`, and `codex execpolicy check` refused the
same file with `Parse error: tabs are not allowed`, making no authorization
decision at all.

**This round differs from the two before it in a way worth stating.** Rounds 1
and 2 were privilege escalation — the evaluator authorized more than the audit
could see. Here the evaluator authorizes NOTHING: it cannot load the file, so
none of the four rules is in force, including the ones the operator correctly
installed. The dispatcher preflight nevertheless advertises inspection as
provisioned, the next managed inspection escalates for approval, the
non-interactive dispatcher denies it and the context is quarantined — which is
the exact incident this Work exists to prevent, reached from the opposite
direction.

### The corrected boundary — confirmed 2026-08-22

**The accepted whitespace was MEASURED against the installed evaluator, not
read off a grammar** (codex-cli 0.149.0). It accepts LF, spaces between tokens,
trailing spaces, blank lines, CRLF, comment lines and a missing final newline.
It refuses a TAB anywhere in code — line start, between operands, even between
`prefix_rule` and its `(` — a statement indented by SPACES, a lone CR, a form
feed, a vertical tab, an NBSP, and a line terminator inside a string literal.

So the rule is now:

- **the only accepted whitespace is SPACE and LF**, the two characters this
  module's own generator emits, wherever they appear — top level or between
  operands inside a rule;
- **a top-level construct must BEGIN its line.** This is a refusal to read
  indentation rather than a reproduction of it: the evaluator rejects an
  indented statement whether a tab or a space indents it, and this module has
  now been wrong three times about what it can safely interpret;
- **a line terminator inside a string literal makes the construct
  UNACCOUNTED**, because it ends the literal in Starlark rather than becoming
  part of the operand;
- everything else that is whitespace at all is UNACCOUNTED and fails closed.

**A SPACE-indented rule is refused too, and it was not in the review.** It was
found while establishing what the evaluator does with tabs. Correcting only the
reported character would have left an identical defect one keystroke away.

**UNACCOUNTED content is now reported BEFORE missing, broad and extra.** A file
this module cannot fully read is a file whose other answers are not
trustworthy: the reviewer's candidate otherwise refuses with "does not
authorize [docker image inspect]" and tells the operator to install a rule the
file already contains. Where the evaluator has refused the whole file, every
rule is inert and only one of them looked wrong.

**The refusal renders the character that caused it.** A tab appears as `\t` and
an indented rule as `\x20\x20prefix_rule(...)`, because a fragment quoted back
with its whitespace swallowed by the terminal is indistinguishable from the
approved rule.

**Fail-closed is not fail-blind, and there are regressions in both
directions.** The exact generated policy, a missing final newline, trailing
spaces, blank lines, blank lines of spaces, comment lines, spaces inside a rule
and a rule spanning lines all still audit exact, and each was confirmed
loadable by the installed evaluator. The live 94-rule policy is unchanged and
still audits satisfied for all three participants and the inspection profile.

A COMMENT is accounted for wherever it sits — on its own line, indented, or
trailing the rule it explains. All three were put in front of the evaluator,
which loads them; refusing an operator's note beside a rule would be fail-blind
in the direction round 1 warned about. Only STATEMENTS must begin their line.

**STATED LIMITATION: one spelling the evaluator accepts is refused
deliberately.** CRLF line endings, which this generator never emits. The cost
is one regeneration and a message that says so, against two quarantined review
turns in the other direction. A deployment that needs them must establish the
semantics against the oracle and widen the accepted set explicitly, as this
round did.

**The reader is shared, so the BATON workflow profile carried the same hole**
for a third time: a tab-indented or space-indented Baton rule audited exact on
a file Codex refuses to load, which would leave the workflow preflight passing
while the participant could commit no canonical operation at all. Covered on
both profiles, in the module tests and in the deployed-artifact matrix.

### Fourth independent review — observed 2026-08-22

**Observed:** whole-file accounting still reports `satisfied=true` for three
literal-only `prefix_rule` calls the installed evaluator refuses: duplicate
named operands, an empty pattern, and an invalid decision literal. A duplicate
`pattern` is silently overwritten by `decompose`; empty patterns and arbitrary
decision strings are returned as parsed rules. With the other exact inspection
rules present, all three candidates return `missing=[]`, `broad=[]`,
`extra=[]`, and `unaccounted=[]`, while `codex execpolicy check` refuses the
file with `repeated named argument`, `pattern cannot be empty`, or
`invalid decision` respectively.

**Confirmed:** this is another false-ready availability failure. Codex loads
none of the nominated file, but the dispatcher preflight advertises the four
inspection rules as provisioned. Exact reproduction is retained in
`evidence/fourth-review-invalid-literal-calls-2026-08-22.txt`; the independent
verdict is `review-2026-08-22T13-29-42Z.md`.

**Required:** repeated operands, empty patterns, and decisions outside an
evaluator-established accepted domain must be UNACCOUNTED rather than parsed.
Both profiles need pure-audit and installed-evaluator regressions, plus the
deployed-artifact coverage. The current `decision="deny"` unit case is not an
evaluator-valid restriction and must not stand as the semantic oracle.

## Correction after fourth review — 2026-08-22 (baton.claude)

All three reported candidates were reproduced against the tree before any
edit, and the fourth round is the same class of defect a fourth time — one
semantic layer further in. Rounds 1, 2 and 3 corrected what this module read
as SYNTAX (the call shape, the string escapes, the whitespace). Round 4 is a
call built entirely from string literals, in a shape the scanner fully
decomposes, that the evaluator still refuses to load. Evidence:
`evidence/correction-round4-2026-08-22.txt`.

### Superseded 2026-08-22 — "fully decomposed into string literals" was the end of the question

`decompose` returned a rule as soon as every operand was a plain literal. It
was not asking whether the evaluator would ACCEPT those literals, so three
kinds of file passed: a repeated named operand (silently overwritten, so the
audit read whichever value the call ended on), an empty pattern, and any
decision string at all. In each case Codex loads NO rule from the file —
including the four inspection rules an operator installed correctly — while
the preflight advertises the deployment as ready. That is round 3's
false-ready availability failure, not round 1's privilege escalation.

**A fourth case the review did not have.** The overwrite was never specific to
`pattern`: `decision="allow", decision="allow"` is the same `repeated named
argument` parse error and audited exact the same way. Correcting only the
reported operand would have left an identical hole one keyword away — exactly
what round 3 found with the space-indented rule.

### The corrected boundary — confirmed 2026-08-22

- **A repeated named operand makes the construct UNACCOUNTED.** Last-value-wins
  is this module's semantics, not the evaluator's.
- **An empty pattern is UNACCOUNTED**, in the keyword and the positional
  spelling, because both reach the same evaluator.
- **The decision domain was MEASURED, not derived** (codex-cli 0.149.0): the
  evaluator loads exactly `allow`, `prompt` and `forbidden`, case-sensitively,
  and refuses `deny`, `forbid`, `ask`, `bogus`, `reject`, `warn`, `allowed`,
  `Allow`, `ALLOW` and the empty string. Anything outside the measured three is
  UNACCOUNTED — including a spelling a later Codex might add, which is the same
  stated limitation this module already carries for CRLF.
- **Only `allow` is coverage, and only `allow` is what the generator emits.**
  `prompt` and `forbidden` are accounted for because they LOAD: refusing an
  operator's valid restriction would be fail-blind in the direction round 1
  warned about. They are read, and reported as not-capability.
- **An empty string ELEMENT is a different question and stays accounted.**
  `pattern=[""]` loads, and it covers nothing because no argv element equals
  the empty string. The evaluator's complaint is about an empty PATTERN.
- **The refusal now names the operand-literal rules** beside the whitespace
  ones, so an operator reading it is not sent looking for whitespace that is
  not there.
- **The scanner is shared, so the BATON workflow profile carried it for the
  fourth time** and is covered on both the pure-audit and the oracle side.

### Superseded 2026-08-22 — the `decision="deny"` unit cases

`W2845: a deny rule is never inspection coverage` and the `deny` branch of
`W415: a BROAD rule is refused, not counted as coverage` both asserted the
audit's answer about a decision the installed evaluator REFUSES, so they were
describing a file Codex will not load and could never have caught this defect.
Both now spell the restriction `forbidden`, which is evaluator-valid and still
not coverage. `deny` has its own unaccounted case beside the other invalid
literals, and both suites now confirm the fixture against the oracle before
asserting the audit.

### Unchanged: fail-closed is not fail-blind

The installed 95-rule policy still reads with zero unaccounted content, the
inspection profile still audits satisfied, and `baton.codex` and `baton.tuner`
still audit satisfied for all thirty ruled verbs. Nothing this round refuses
was accounted for before it.

## Fifth independent review — 2026-08-22

**Observed:** `splitTopLevel` removes every empty comma-separated field, rather
than only the one empty tail created by a valid trailing comma. As a result,
malformed list and call forms such as `pattern=["docker",, "image", "inspect"]`
and `prefix_rule(, pattern=[...], decision="allow")` are decomposed into the
same exact rule as their valid spellings.

**Confirmed:** five empty-field placements all made the inspection audit return
`missing=[]`, `broad=[]`, `extra=[]`, `unaccounted=[]`, `satisfied=true`, while
the installed evaluator refused every nominated file with `unexpected symbol
','` and loaded none of its rules. This is another false-ready availability
failure. Exact reproduction is retained in
`evidence/fifth-review-empty-comma-fields-2026-08-22.txt`; the independent
verdict is `review-2026-08-22T14-41-58Z.md`.

**Required:** preserve at most one trailing comma, but make an empty head or
middle field and a second trailing comma UNACCOUNTED in both the call operand
list and the pattern list. Cover the correction with pure-audit,
installed-evaluator, and deployed-artifact regressions for both profiles.

## Correction after fifth review — 2026-08-22 (baton.claude)

Reproduced against the tree before any edit: all five reported forms audited
`satisfied=true unaccounted=0` while the evaluator refused the whole file.
Two more forms found by probing rather than by reading: the same empty middle
field inside the pattern list with a DOUBLE trailing comma, and an empty
middle field in the POSITIONAL spelling. Evidence:
`evidence/correction-round5-2026-08-22.txt`.

### Superseded 2026-08-22 — "a trailing comma leaves an empty tail"

The line this round removes is

```js
// A trailing comma leaves an empty tail, which is valid syntax and not
// an operand.
return parts.filter((part) => part.trim() !== "");
```

The comment is true. The code does not implement it. "One empty tail is
valid" became "every empty field anywhere is discarded", and that gap is the
whole defect: an empty head field, an empty middle field and a second
trailing comma each reached `stringList` and `decompose` as a well-formed
operand list.

**Kept in place with its correction beside it, because the shape of the
mistake is the record's subject.** This is the fifth round of one class:
rounds 1 and 2 read the language's SYNTAX and its STRING ESCAPES, round 3 its
WHITESPACE, round 4 its OPERAND LITERALS, and this one its PUNCTUATION. Every
time, a rule that was nearly right was applied uniformly where the evaluator
applies it in exactly one position.

### The corrected boundary — measured 2026-08-22

Against codex-cli 0.149.0, not read off a grammar:

| form | evaluator | audit |
| --- | --- | --- |
| one trailing comma in the call | loads | exact |
| one trailing comma in the pattern list | loads | exact |
| one in both at once | loads | exact |
| one in the positional spelling | loads | exact |
| empty head field | refuses, `unexpected symbol ','` | UNACCOUNTED |
| empty middle field | refuses | UNACCOUNTED |
| second trailing comma | refuses | UNACCOUNTED |
| empty middle field, positional | refuses | UNACCOUNTED |

`splitTopLevel` now returns `null` — the module's existing "I cannot account
for this" answer — instead of a filtered list, and both callers propagate it.
`()` and `[]` hold no field at all and are unchanged: an empty operand list
is still round 4's empty-pattern refusal, reached for the reason round 4
established rather than as a comma question.

### Unchanged: fail-closed is not fail-blind

For the fifth time this is asserted rather than assumed. Every valid trailing
comma still audits exact, and the oracle confirms the evaluator LOADS each of
those fixtures and still authorizes `docker image inspect` under them. The
live nominated policy still reads 95 rules with 0 unaccounted, and the
inspection profile and all three dispatched participants still audit
satisfied — the same numbers as before this round, which is what says the
refusal is narrow.

## Sixth independent review — 2026-08-22

**Observed:** `readPolicy` refuses every `OTHER_WHITESPACE` character before
asking whether the line is blank. A line containing only a TAB therefore
becomes UNACCOUNTED even though the installed evaluator loads the file. This
is the evaluator behavior already measured and recorded above as “blank
lines, including ones holding a tab”; the valid-spelling regression matrix
omits that one recorded case.

**Confirmed:** with the four exact inspection rules followed by a TAB-only
blank line, `auditInspectionRules` returns `missing=[]`, `broad=[]`,
`extra=[]`, `unaccounted=["\\t"]`, `satisfied=false`. The installed
`codex execpolicy check` loads the same file and returns `decision="allow"`
for `docker version`. This is fail-blindness and an availability defect, not
a privilege-expansion defect: dispatcher startup rejects a valid exact policy
and asks the operator to regenerate content Codex already accepts. The exact
result is retained in `review-2026-08-22T15-10-46Z.md`.

**Required:** account for evaluator-valid TAB-only blank lines without
accepting a TAB before or inside a statement. Add pure-audit and installed-
evaluator regressions for both profiles, plus deployed-artifact coverage; keep
the existing tab-before-rule and tab-between-token refusals as the negative
boundary.

## Sixth independent review — 2026-08-22

**Observed:** `readPolicy` sent every `OTHER_WHITESPACE` character straight to
`refuseLine`, so a TAB on an otherwise blank line was treated exactly like a
TAB before or inside a statement.

**Confirmed:** one tab-only blank line appended to the four exact inspection
rules audited `unaccounted: ["\t"] satisfied: false`, while the installed
evaluator loaded that same file and returned `allow` for `docker version`.
Verdict: `review-2026-08-22T15-10-46Z.md`.

**Required:** account for evaluator-valid tab-only blank lines without
accepting a tab before or inside a statement, with pure-audit, oracle and
deployed-artifact coverage on both profiles, retaining round 3's negatives.

## Correction after sixth review — 2026-08-22 (baton.claude)

Reproduced before any edit. Evidence:
`evidence/correction-round6-2026-08-22.txt`.

### This one is the OPPOSITE direction, and that is the finding

Rounds 1 through 5 were all privilege escalation or false-ready: the audit
called a file exact that the evaluator either read more permissively or could
not read at all. This one hides nothing. The evaluator loads the file and
authorizes exactly the ruled inspections; the dispatcher refuses to start and
asks the operator to regenerate a file whose regeneration cannot change what
Codex authorizes.

**It contradicts this record's own measurement.** Round 3's accepted table
already says "blank lines, including ones holding a tab". The table was right
and the code did not implement it — the same shape as round 5, where the
comment stated the rule and the `filter` did something else. Two rounds
running, the defect was between a correct written rule and the line under it.

### The tolerance is a property of the LINE, measured per character

Against codex-cli 0.149.0, one character per otherwise-blank line: TAB,
SPACE+TAB and a tab-only last line all LOAD; vertical tab, form feed, NBSP,
U+1680, U+2000, U+2028, U+2029, U+202F, U+205F, U+3000 and U+FEFF each make
the evaluator refuse the whole file even alone on a line. So the accepted
blank-line whitespace is exactly SPACE and TAB, and `blankLineEnd` decides it
for the whole line rather than exempting a character.

That distinction is load-bearing: a TRAILING tab after a rule is the same
character, and the evaluator refuses it. A character-level exemption would
have accepted it and reopened round 3. It is covered as a negative.

### Stated limitation, re-measured and narrowed rather than widened

A blank line holding a lone CARRIAGE RETURN loads in the evaluator and is
still refused here. That is the CRLF limitation this module has carried since
round 3, not a new one: a lone CR is a whole-file line-ending property and
this generator emits LF. A TAB is different in kind — it arrives from an
operator pressing Tab on an empty line while hand-editing the ruled file,
which is precisely the case the accepted-spelling boundary exists for.
Recorded so the next reader knows the narrowing is deliberate and measured.

## Seventh independent review — 2026-08-22

**Observed:** the round-6 whole-line exception accepts a TAB-only blank line,
but a TAB-indented comment is consumed as UNACCOUNTED before `readPolicy`
reaches its comment branch. The existing round-6 “tab inside a comment” case
puts the tab after `#` and therefore does not exercise indentation.

**Confirmed:** the four exact inspection rules plus `\t# operator note` make
the installed evaluator return `allow` for `docker version`, while the audit
returns `unaccounted=["\\t# operator note"]` and `satisfied=false`. This is a
false refusal of a valid exact policy, and contradicts the already-pinned rule
that comments may be indented. Exact reproduction:
`evidence/seventh-review-tab-indented-comments-2026-08-22.txt`; verdict:
`review-2026-08-22T15-47-35Z.md`.

**Required:** account for SPACE/TAB indentation before comments without
widening tabs before, inside or after rules. Cover both shared profiles in the
pure audit, installed-evaluator oracle, and deployed artifact.

## Correction after seventh review — 2026-08-22 (baton.claude)

Reproduced before any edit. Evidence:
`evidence/correction-round7-2026-08-22.txt`.

### The rule was pinned in round 3 and never implemented

Round 3's measured table says a comment is accounted for wherever it sits,
"indented, or trailing a rule", and round 3's own accepted-spelling case
proves an indented comment loads. It passes because a SPACE is accepted
whitespace and falls through to the comment branch by accident — not because
anything implements indentation. Round 6 then added a case named "tab inside
a comment" that places the tab AFTER the `#`, which looks like coverage of
this and is not.

**So this is the second round running where a correct written rule and the
code under it disagreed**, and the third where the gap was found by measuring
rather than reading. The blank-line rule of round 6 and this one are the same
shape one case apart.

### The correction, and why it stays a LINE rule

`commentLineEnd` scans from the START of the line: SPACE/TAB indentation
followed by `#` consumes the line as a comment; anything else does not. That
is deliberately not a character exemption, and the case that proves the
difference is `rule<TAB># note` — a tab-indented comment SHARING a line with
a rule, which the evaluator refuses because that tab is in code. A
character-level exemption would have accepted it.

Measured per form (codex-cli 0.149.0): one tab, several tabs, and space+tab
mixed before `#` all LOAD, as does the same at end of file with or without a
final newline; a form feed, vertical tab or NBSP before `#` each make the
evaluator refuse the whole file; and a tab before a rule, trailing a rule, or
sharing a line with one is refused exactly as before.

### Unchanged

The carriage-return limitation is untouched and re-measured: a CR before a
comment loads in the evaluator and stays refused here, under the standing
CRLF boundary. Rounds 3 and 6 keep their full negative sets, re-asserted on
both profiles rather than trusted, and the live nominated policy still reads
95 rules with 0 unaccounted — this round only ADDS accepted spellings, so
nothing that audited exact before it can fail now.

## Eighth independent review — 2026-08-22

**Observed:** the round-7 correction accounts for indentation before a
top-level comment but not for a comment inside an otherwise supported
multi-line `prefix_rule(...)`. `matchingParen` retains the comment and
`splitTopLevel` passes it into `decompose` as operand text, making the exact
rule unaccounted.

**Confirmed:** placing `# operator note inside the call` immediately after the
opening parenthesis of the fourth exact inspection rule makes the installed
evaluator return `allow` for `docker image inspect node:24-slim`, while the
audit reports that rule unaccounted, the inspection missing, and
`satisfied=false`. This is another fail-blind startup refusal and contradicts
the round-3 promise that comments are accounted for “wherever” they sit.

**Required:** account for evaluator-valid comments inside the bounded literal
call without interpreting comment contents as delimiters, and retain `#`
inside a quoted string as data. Measure indentation/end-of-line spellings and
cover both shared profiles in pure-audit, installed-evaluator, and deployed-
artifact regressions. Review:
`review-2026-08-22T16-46-17Z.md`; evidence:
`evidence/eighth-review-comment-inside-rule-2026-08-22.txt`.

## Correction after the eighth review — 2026-08-22 (baton.claude)

Reproduced before any edit. Evidence:
`evidence/correction-round8-2026-08-22.txt`.

### The round-3 promise, kept rather than narrowed

Round 3 pinned that a comment is accounted for "wherever it sits". The review
is right that inside a literal call is one of the places it sits, and right
that the alternative was to supersede that promise explicitly and justify the
narrower boundary. There is no justification available: the evaluator loads
the comment and honours the rule, so refusing it only rejects correct
operator text. The promise is kept.

### A mask, not a parser — which is the review's other requirement

Comment spans are blanked to spaces before any structural scan, so
`matchingParen`, the whitespace accounting and the operand reader never see
comment text. A body carrying quotes, commas, brackets or parentheses cannot
become syntax because it never reaches the splitter — the reproduction showed
one such comment producing FOUR unaccounted fragments, which is precisely
comment punctuation being read as structure.

Length is preserved, so every offset and therefore every quoted refusal
fragment still lines up with the original text.

### Two boundaries the mask does not cross, both measured

- A `#` inside a STRING is data. The walk tracks quote state with the same
  escape rule the rest of the module uses, and a regression reads the operand
  back through the scanner to prove `not#docker` is one string rather than a
  truncated one with a comment after it.
- A TAB before the `#` is a tab in CODE and stays refused, because the
  evaluator refuses it — measured this round, inside a construct, not assumed
  from the top-level case.

### Unchanged

Rounds 3, 6 and 7 keep their full negative sets, re-asserted inside the new
cases rather than trusted. The live nominated policy still reads 95 rules with
0 unaccounted; this round only ADDS accepted spellings.

## Ninth independent review — 2026-08-22

**Confirmed:** the round-eight correction closes the reported in-rule comment
case and retains its punctuation, quoted-hash, and tab-in-code boundaries. All
293 pre-existing bridge tests pass.

**Observed:** the new mask does not preserve the source's index space for
non-BMP text. `[...text]` creates an array of Unicode code points, while the
masking loop and every structural scanner use UTF-16 code-unit offsets into
the JavaScript string. An emoji in an evaluator-valid top-level or in-rule
comment shifts later mask assignments. The evaluator loads both candidates
and authorizes the exact inspection, while preflight reports later valid text
unaccounted and refuses startup.

**Required:** create and mutate the mask in the same code-unit index space as
the source, assert exact length preservation, and cover astral comments with a
following construct on both shared profiles and in the deployed artifact.
Verdict: `review-2026-08-22T17-42-34Z.md`; reproduction:
`evidence/ninth-review-astral-comment-mask-2026-08-22.txt`.

## Round-9 correction — 2026-08-22

The ninth review is correct and was reproduced before any edit. The decision
it settles is small and worth pinning, because it is the kind that returns:

**The comment mask lives in the source's index space, and that is checked, not
assumed.** `maskComments` builds its output with `text.split("")` — one element
per UTF-16 code UNIT — because the masking loop, `matchingParen`, the
whitespace accounting, the operand reader and every offset this module takes
into the policy text are code units. `[...text]` iterates code POINTS, which
agrees only while the text is entirely BMP; after one astral character the two
spaces diverge by one element each, mask writes land late, and the joined mask
no longer indexes the source. The function now throws if the mask is not the
source's exact length.

RECORDED: that length throw is unwitnessed and cannot be witnessed from
outside the module — it is unreachable while the mask is built correctly. It
stays as a guard against a future scanner change, named as unwitnessed rather
than counted as covered. A reviewer who prefers it removed can say so.

Astral text OUTSIDE a comment is ordinary operand data and is read as itself;
a regression asserts the emoji-bearing operand comes back unshifted.

### Unchanged

This round changes the mask's REPRESENTATION and nothing about what it masks.
Rounds 3, 6, 7 and 8 keep their full negative sets and are re-asserted by the
green suite. The live nominated policy still reads 95 rules with 0
unaccounted, on the inspection profile and for all three dispatched
participants.

## Tenth independent review — 2026-08-22

**Confirmed:** the round-nine correction is sound. `text.split("")` gives the
mask one element per UTF-16 code unit, matching every scanner offset into the
source; the exact-length guard checks the invariant before the mask is used.
The correction does not change what counts as a comment, string, escape, or
accepted whitespace.

The astral fixtures retain a later construct so the original drift cannot pass
vacuously, and cover both shared profiles plus the deployed artifact. The
bridge suite passes 297/297, the focused W2845 suite passes 24/24, and the
deployed exact-policy boundary passes. No further reviewer finding remains.

**Signed off for operator acceptance.** The operator-only live matrix,
installation of the exact generated policy, and managed-stack restart remain
the final gate. Review: `review-2026-08-22T18-25-27Z.md`.

## Operator acceptance attempt — 2026-08-22

**Observed:** the first live-matrix invocation used the currently deployed
`c529b28` Baton and stopped after its first positive case because the matrix
now names W4303's mandatory `release episode=` operand while that older
deployment does not accept it. The credential and all staging directories
were disposed. This is candidate-version skew, not a W2845 policy result.

The matrix was then run against an isolated current-tree deployment. Every
managed-work positive and negative preceding the Docker section passed, all
four ruled Docker inspections ran without an approval request, and none of
the four unruled Docker commands changed the runtime. However, all four
unruled cases also produced NO approval request. The matrix requires an
approval request that its client denies as the observable proof of
fail-closure, so it failed all four negative cases rather than guessing why no
mutation occurred. The installed evaluator independently reports `allow` for
`docker version` and no matching rule for `docker ps -a` or `docker rm -f ...`;
that confirms the intended rule shape but does not establish what stopped the
live turn.

**Required before acceptance:** make the live negative oracle distinguish and
prove the actual terminal outcome of each commanded tool attempt. A denied
approval request remains acceptable evidence, but absence of mutation alone
is not: the model may decline the command, the tool may fail independently,
or policy may refuse it without emitting that request. Retain the existing
positive cases, prove that each negative was actually attempted and refused
by the intended boundary, and re-run the complete credential-bearing matrix.
Do not install or restart until that gate passes.

Evidence: `evidence/live-matrix-2026-08-22.txt`.

## Operator-acceptance oracle review — 2026-08-22

**Confirmed:** the operator correctly declined to infer policy refusal from
an unchanged runtime and an empty approval list. The signed-off generator,
auditor and scanner remain accepted; this is a defect in the manual matrix's
observation boundary.

**Observed:** `runCase` records only approval RPC method names. It therefore
does not prove the requested Docker command was attempted. The same defect is
present on both sides: a negative with no request may have been skipped, and a
positive with no request may also have been skipped despite being reported
PASS.

**Confirmed local provider boundary:** codex-cli 0.149.0 exposes exact
`commandExecution` items through `thread/read(includeTurns=true)`, with the
command string, stable item id, source, terminal status, output and exit code.
Approval requests carry the same thread/turn/item identities. The matrix can
therefore prove the exact attempted command and terminal policy result without
guessing from mutation or prose.

The implementation-ready correction and P1 severity are in
`review-2026-08-22T20-31-27Z.md`; exact provider-schema evidence is retained
in `evidence/operator-oracle-review-2026-08-22.txt`. Strengthen both positives
and negatives, rerun the complete credential-bearing matrix, and keep
installation/restart blocked until it passes.

## Matrix oracle correction — 2026-08-22

**AN ABSENCE OF EVIDENCE IS NOT EVIDENCE.** The matrix counted approval
requests: a ruled inspection passed on an empty list and an unruled command
passed on a non-empty one. The operator run produced an empty list for all
eight cases, which is what made the defect visible — one body of evidence
reading as PASS on four cases and FAIL on four. "No approval arrived" is
neither "the inspection ran" nor "the command was refused".

The verdict is now about ONE IDENTIFIED COMMAND ITEM from the turn the
app-server recorded: exactly one agent `commandExecution` matching the
request, `completed` at exit 0 with no correlated approval for a ruled
inspection; `declined`, or a correlated approval denied and a terminal
non-completed item, for an unruled one.

**A BARE `failed` IS NOT A REFUSAL.** A Docker command can fail on its own
merits — a stopped daemon, an absent object — and reading that as the
boundary would make the matrix pass while the boundary was wide open.

**APPROVALS ARE CORRELATED, NEVER COUNTED**, by thread, turn and item id. An
approval raised by something else in the same run says nothing about this
command, and counting it was half the original defect.

**THE ORACLE IS PURE**, which is what lets every item shape be driven
deterministically rather than waited for during a credential-bearing run.

### Recorded

Reading the INSTALLED schema rather than the review's prose caught a defect
in my own correction: `CommandExecutionThreadItem.source` carries a default
of `agent` and is not required, and my first filter demanded it. An item that
omits the field is the ordinary agent case, so requiring it would have
reported a ruled inspection that ran perfectly as never attempted — the exact
ambiguity being fixed, reintroduced by the fix.

## Matrix-oracle correction re-review — 2026-08-22

**Confirmed P1:** recorded command items are now selected exactly, but the
approval half of the verdict is neither typed nor proven denied.
`runCase` records every server request, calls `respondError`, and discards its
boolean result. `approvalsFor` then treats any recorded request with matching
thread/turn/item ids as the approval evidence.

The installed schema makes the distinction observable and necessary. Its
exact command method is `item/commandExecution/requestApproval`, while
`item/fileChange/requestApproval` and `item/permissions/requestApproval` also
carry `threadId`, `turnId`, and `itemId`. Either unrelated request therefore
rescues a bare failed Docker item as a supposed command-policy refusal. A real
command approval whose denial could not be sent does the same, because
`CodexClient.respondError` returns false on that failure and the matrix ignores
it. Observation is not denial.

The synthetic helper currently spells the command method
`commandExecution/requestApproval`, without the schema's `item/` prefix. That
fixture passes only because the oracle never examines the method, so it must
be corrected alongside the production correlation.

**Required:** correlate only the exact command-execution approval method.
Ruled positives fail if such a request was observed at all; an unruled
approval-path negative passes only when the response was successfully sent as
a denial and the command item has the already-ruled terminal non-completed
state. Preserve direct `declined` without approval and preserve bare `failed`
as insufficient. Two additive regressions are retained.

Independent baseline was 311/311. With the retained cases the bridge suite is
311 passed, 2 failed. Evidence:
`evidence/review-command-approval-correlation-2026-08-22.txt`; verdict:
`review-2026-08-22T21-02-03Z.md`. The credential-bearing matrix and
install/restart remain blocked.

## Matrix oracle, second correction — 2026-08-22

**CORRELATION IS METHOD AND IDENTITY, NOT IDENTITY ALONE.** The installed
schema gives file-change and permission approvals the same
`threadId`/`turnId`/`itemId` triple as the command approval, so matching only
the identity read a prompt about a different boundary as command-execpolicy
evidence — and that can accept an unruled command that merely `failed`, the
one state this oracle most needs to refuse. Refusing a bare failure was the
point; an unrelated approval let it back in through the other door.

**AN OBSERVED REQUEST IS NOT AN ANSWERED ONE.** `respondError` returns false
when it cannot send, and discarding that turned an unanswered prompt into
proof that policy refused. The unruled approval path requires a SENT denial;
a ruled inspection still fails on the mere REQUEST, answered or not, because
the reason those four are ruled is that nothing asks about them at all.

Neither correction makes an approval mandatory: a direct `declined` is still
a refusal with nothing to correlate, and that has its own case so the
tightening cannot quietly become a requirement.

### Recorded

My synthetic fixtures used a method name the schema does not define, and
method-blind correlation hid it — a name nothing compares cannot be wrong.
They build from the exported constant now. The wrong spelling was a symptom
of the same missing check rather than a separate slip, which is why fixing
the check is what fixes it.

## Matrix-oracle second-correction re-review — 2026-08-22

**Confirmed corrected and signed off:** approval evidence is now joined by
the installed schema's exact method
`item/commandExecution/requestApproval` as well as thread, turn and item
identity. File-change, permissions and other request methods cannot rescue a
bare failed command. The live matrix records `respondError`'s boolean on the
same request, and an approval-path refusal requires at least one successfully
sent denial plus the already-required terminal non-completed command item.

The conservative distinctions remain intact: a ruled inspection fails on any
correlated command approval request whether its denial was sent or not; a
direct `declined` item needs no approval; and a bare `failed` item remains
insufficient. The exact installed schema confirms the method and shared
identity fields. The bridge suite passes 316/316 and the matrix parses.

No reviewer finding remains in this oracle correction. Independent verdict:
`review-2026-08-22T21-12-54Z.md`; evidence:
`evidence/review-command-approval-correlation-round2-2026-08-22.txt`.

This is not operator acceptance. The complete credential-bearing matrix may
now be rerun; exact policy installation and managed-stack restart remain
blocked until that live gate passes.

## Final operator matrix still observes no Docker command — 2026-08-23

**Observed:** the corrected credential-bearing operator matrix passed every
Baton authority and negative-mutation case, but all eight Docker cases had no
agent `commandExecution` item. The four ruled inspection commands therefore
did not prove execution, and the four unruled commands did not prove a policy
refusal. The corrected oracle rejected all eight cases instead of treating an
absent command as evidence. No Docker mutation occurred; the staged Codex
credential and both staging directories were disposed successfully.

**Confirmed:** this is not operator acceptance and the exact policy must not
be installed from this result. Before the gate can be rerun, the live driver
must make the requested Docker command observable as the exact
`commandExecution` item the oracle already requires. Absence remains neither
successful execution nor a policy refusal. The correction must preserve the
passing Baton matrix, fail-closed negative cases, and cleanup boundary.

Evidence:
`evidence/live-matrix-final-2026-08-23.txt`.

## Reviewer diagnosis of the absent Docker attempts — 2026-08-23

**Confirmed:** the conservative oracle is still the correct acceptance
boundary. Codex app-server records a shell attempt as a `commandExecution`
turn item, emits `item/started` before an approval decision, and retains the
terminal item in `thread/read(includeTurns=true)`. The final operator run's
absence of that item therefore means that the model did not initiate the
requested shell command; it is not a renamed item or an oracle/schema
mismatch. Official provider reference:
`https://developers.openai.com/codex/app-server/`.

**Observed:** `runCase` creates a fresh thread, but its prompt only says to
"run" and "report" the command. The Docker cases come after thirteen other
credential-bearing model turns. The retained operator report contains no
bounded transcript or item-type inventory for an absent attempt, so it cannot
distinguish a model self-refusal, a prose-only answer, or another failure to
invoke the shell. The exact cause inside the model is therefore **Open**.
The same ruled command, `docker version --format '{{json .}}'`, completed at
exit 0 when invoked directly in this managed reviewer turn, confirming that
the installed reviewer boundary can execute it; that does not substitute for
the required isolated managed-turn evidence.

**Proposed for `baton.ops` acceptance:** preserve the oracle and the exact
command set. Split the Docker gate into a dedicated fresh app-server phase
that runs before the Baton cases and fails fast. Make the developer and user
instructions require exactly one shell-execution tool call for the literal
command, forbid answering from prior knowledge or pre-judging policy, and
require waiting for the tool's terminal result before reporting. For the safe
absent-target negatives, state that the operator deliberately expects the
execution boundary to refuse the submitted command; the model must still
submit it rather than self-refuse. When the exact command item is absent,
retain a bounded diagnostic containing the turn status, item-type inventory,
and agent-message text. Do not weaken `requestedItem`, accept prose, or use
the direct experimental `command/exec` endpoint as operator acceptance: the
gate is specifically evidence from a managed turn.

After implementation and focused prompt/diagnostic regressions, independently
review the change and rerun the complete credential-bearing matrix. Preserve
the passing Baton authority cases, negative-mutation probe, credential
cleanup, and the existing 21/21 install/restart gate.

Reviewer proposal and evidence:
`review-2026-08-23T04-13-22Z.md` and
`evidence/reviewer-driver-correction-2026-08-23.txt`.

## The absent command items are the SERVER, not the prompt — 2026-08-23

**A DIAGNOSIS IS A CLAIM ABOUT THE WORLD, AND THIS ONE WAS TESTABLE.** The
proposed correction rested on the model not invoking the shell tool. A turn
asked for `date +%s%N` returned a nanosecond timestamp inside the run window —
a value it cannot know without executing — while `thread/read includeTurns`
recorded no `commandExecution` item at all. An independent `/bin/echo` probe
agrees, and the item type is declared in the installed schema. The command
runs; the turn record does not carry it.

So a stricter prompt, a dedicated phase and a demand to wait for the terminal
tool result would each change behaviour that is already correct, and the eight
cases would fail in exactly the same way. Implementing them would have
produced a second identical failure and a second round of the same diagnosis.

**AND NO ORACLE RELAXATION.** The review is right that none is acceptable. The
premise is unmet by this build, which is a deployment fact rather than
something an implementer can prompt around — an app-server that records
command items, a different managed-turn transport for the same evidence, or an
explicit decision that this gate cannot be proven here.

**A FAIL-CLOSED REJECTION THAT RETAINS NOTHING IS ONE NOBODY CAN ACT ON.**
That is how eight cases became "the reason is not recoverable", and it is why
the bounded diagnostic was worth implementing whatever the cause: it is what
made the cause findable. It says what happened and decides nothing — giving it
a verdict would make prose evidence again, which is what the oracle exists to
prevent.

## Reviewer correction after decisive live measurement — 2026-08-23

**Superseded:** the earlier reviewer inference that the model did not initiate
the shell command, and the corresponding proposal to fix that with a stronger
prompt or Docker-first phase, are superseded by the implementer's live
measurement. A managed turn returned a fresh nanosecond timestamp inside its
measured run window, which it could only obtain by executing `date +%s%N`;
`thread/read(includeTurns=true)` nevertheless contained only `userMessage`
and `agentMessage`. The independent `/bin/echo` probe agrees. The model did
execute; this codex-cli 0.149.0 app-server did not retain the documented
`commandExecution` item.

**Confirmed:** the strict oracle remains right and must not be relaxed. The
official app-server contract describes a shell execution as a
`commandExecution` item, emits its lifecycle items, and exposes stored turns
through `thread/read(includeTurns=true)`. The running deployment does not meet
that contract for these probes. A compatible server build, an independently
ruled transport that still proves the same managed turn, or an explicit
operator decision to wait is required before the 21/21 gate can pass. Direct
`command/exec`, agent prose, and absence of mutation remain insufficient.

**Changes requested on the diagnostic only:** the diagnostic addition is
useful and does not influence verdicts, but it is not yet bounded as claimed.
Only each agent message is truncated. The number of messages and item types,
the number of commands, and every command string remain unlimited. A pure
1,000-command turn produced a 1,029,041-character `summary`. Apply hard caps
to total items/messages/commands and to each command string, report true
totals and truncation, and add regressions for many messages, many commands,
and a long command. Keep reasoning payloads excluded and keep the diagnostic
outside every verdict.

Review: `review-2026-08-23T04-49-11Z.md`; evidence:
`evidence/review-bounded-diagnostic-2026-08-23.txt`.

## The bounded diagnostic, actually bounded — 2026-08-23

**A CAP ON THE PARTS IS NOT A BOUND ON THE WHOLE.** Each agent message was
truncated and nothing else was: every item type, every message, every command
and each full command string were emitted and concatenated. A thousand
commands produced a megabyte.

**AND THE INPUT THAT TRIGGERS IT IS THE INPUT THAT BROKE IT.** This diagnostic
exists for the moment a model goes off-script — which is exactly when a turn
has a thousand items and exactly when the operator log has to stay readable.
A bound that holds for well-behaved turns is not a bound.

**AN EXPORTED HELPER ITS CALLER CAN MAKE UNBOUNDED IS UNBOUNDED.** The caps
are private and `limit` may only tighten. "No current caller passes a large
limit" is a property of today's callers.

**THE COUNT IS OFTEN THE FINDING.** True totals are reported even when the
lists are cut, and every cut carries an explicit omission marker. Eight cases
with zero command items is the whole of this Work's current state — a
diagnostic that silently dropped 990 commands would be hiding the thing worth
knowing.

### Recorded

I wrote "BOUNDED ON PURPOSE" in the doc comment of a helper that was not. A
comment asserting a property the code lacks is worse than no comment: it is
the reason nobody checks. One mutation keeps every hard constant and only lets
the caller's `limit` through unclamped, and it fails — a private maximum a
parameter can exceed is not a maximum.

## Bounded-diagnostic re-review, round 2 — 2026-08-23

**Confirmed:** the correction bounds schema-shaped high-cardinality turns and
retains true counts and omission markers without influencing the verdict.

**Observed P2:** the hard-bound claim still has two holes. Passing `limit:
NaN` makes both per-item caps `NaN`, for which `clip` returns the complete
message or command. Independently, item-type strings are count-capped but not
length-capped; a one-million-character type yields a one-million-character
summary. Turn id/status and command status are copied without a hard string
bound as well. The helper is therefore bounded only while its caller and the
server supply expected values, not in every dimension as recorded.

Normalize invalid caller limits and cap every externally supplied string in
the returned structure/summary (or enforce an equivalent hard whole-result
bound), with whole-result regressions for `NaN` and oversized metadata. Keep
the strict oracle, true totals, omission markers, reasoning exclusion, and
diagnostic-only boundary unchanged. Review:
`review-2026-08-23T05-04-02Z.md`.

## The bounded diagnostic, bounded in every dimension — 2026-08-23

**A CLAMP A NON-NUMBER WALKS THROUGH IS NOT A CLAMP.** `Math.min(NaN, max)` is
NaN and `length > NaN` is false, so a `NaN` limit did not tighten the cap — it
removed it. And the failure direction is what makes that dangerous: a clamp
failing toward a SMALLER cap announces itself the first time output looks
truncated, while one failing OFF looks like nothing until the day it matters,
which is the day this diagnostic exists for.

**A HARD PROPERTY THAT DEPENDS ON THE PROTOCOL BEING OBEYED IS THE
PROTOCOL'S.** The counts were capped and the strings were not — item types,
the turn id, the turn status, each command status. Protocol values are small,
and resting a stated hard-output bound on that is resting it on conforming
producers, inside a helper whose entire purpose is the turn that did something
unexpected.

**AND THE BOUND IS ON THE WHOLE, NOT THE SUM OF PROMISES.** The regression
asserts a fixed maximum for the COMPLETE serialized diagnostic under every
dimension at once — two thousand items, each a million characters, oversized
metadata, and a caller trying to switch the cap off — while the true counts
survive, because the count is the finding.

### Recorded

The summary backstop is INERT once every field is capped: removing it changes
nothing and it is not counted as a guard. It is kept for the next field added
without a cap — which is precisely the failure corrected twice in two rounds
— and the comment says that rather than implying it protects anything today.

## Bounded-diagnostic final re-review — 2026-08-23

**Signed off:** invalid caller limits now fall back to private maxima; every
retained external string is length-capped; count caps, true totals, omission
markers, and reasoning exclusion remain; and the complete serialized result
has an adversarial fixed-bound regression. The prior `NaN` and oversized-type
reproductions are corrected, and the full bridge suite passes 336/336. The
helper remains diagnostic-only and the strict oracle is unchanged.

This is not live operator acceptance. W7989 remains the provider/deployment
gate preventing the strict 21-case matrix from observing the required managed
turn evidence. Review: `review-2026-08-23T05-13-32Z.md`.

## Final v11 disposition — 2026-08-23

The operator discontinued this strict v11 live certification under W7989's
second decision. The exact policy, strict oracle, bounded diagnostics, and
deterministic regressions remain valid safeguards, but the current managed
custom-tool deployment cannot expose the structured live evidence required by
the 21-case acceptance matrix. The Work closes cancelled rather than claiming
a live pass. No oracle is weakened; v12's external Worker Manager owns the
replacement execution and evidence boundary.
