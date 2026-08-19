# Finding: add a basic command quick reference to EFFECTIVE-BATON

## Observation — 2026-08-19

`docs/EFFECTIVE-BATON.md` demonstrates the common Baton operations throughout
its workflow narrative: `create`, `claim`, `classify`, `say`, `pass`, `close`,
directed requests and their dispositions, `wait`, and explicit claim recovery.
The examples are substantive, but a participant looking for the spelling of
one ordinary command must already know which conceptual section contains it.

The request used the familiar verb “send”. Protocol 11 deliberately has no
`send`: plain, included, and directed conversational messages all use `say`.
The guide states that protocol-10 `send` is retired, but it does not provide a
compact translation at the point where a new operator looks for commands.

## Confirmed correction — 2026-08-19

Add a compact **Basic command quick reference** near the beginning of
`docs/EFFECTIVE-BATON.md`, after setup and before the detailed straight-through
workflow.

The reference must:

- give copyable v11 forms for the common reads and acts: `home`, `detail`,
  `create`, `claim`, plain `say`, directed `say request=... on=...`, `pass`,
  `close`, and `release`;
- name `respond`, `dispose`, and `accept` as the three obligation dispositions
  and point to the detailed cross-team section rather than duplicating it;
- state prominently that v11 uses `say`, not `send`, and that `pass` is a
  threadless Work handoff rather than a message;
- retain explicit `--config` and `--participant` identity through the guide's
  existing `$BATON` convention;
- point readers to `baton --help` and `baton --help VERB` for the authoritative
  operand grammar;
- remain a quick lookup, not a second exhaustive contract or a rewrite of the
  existing scenario-based explanations.

No protocol, schema, CLI, or runtime behavior changes belong to this Work.

## Implementation revalidation — 2026-08-19

The canonical `aba69d0` CLI help confirms the required forms and operands.
`home` has no required operand; `detail` and `claim` require `work=`; `create`
requires `team=`, `kind=`, `title=`, `origin=`, `body=`, and
`classification=`; and both plain and directed messages are forms of `say`.
The directed form requires `request=` and `on=`, with blocking still the
default. `pass` requires `work=`, `to=`, and `comment=` and describes itself
as a threadless Work event. `close` requires `work=`, `outcome=`, and
`rationale=`. `release` requires `work=`, the exact claimant in `expect=`, and
`reason=`. The three obligation dispositions remain `respond`, `dispose`, and
`accept`.

The guide already defines `$BATON` with both explicit `--config` and
`--participant` and already contains the detailed scenario explanations. The
smallest correction is therefore one lookup section immediately before “The
straight-through path,” plus a focused test in the existing W104 guide suite.
No later ruling or current CLI behavior supersedes the confirmed W87 scope.

## Acceptance

- A reader can find the basic command spellings from the top portion of the
  guide without searching the whole document.
- The reference contains no retired `send` example and cannot imply that
  `pass` posts a message.
- Existing documentation contract tests remain green; add a focused
  documentation regression that pins the reference's presence and the
  `send`-to-`say` distinction.

## Implementation evidence — 2026-08-19

`docs/EFFECTIVE-BATON.md` now has a “Basic command quick reference” immediately
before the straight-through scenario. It uses the guide's explicit `$BATON`
identity convention and gives the confirmed forms for `home`, `detail`,
`create`, `claim`, plain and directed `say`, `pass`, `close`, and `release`.
The adjacent prose prominently translates retired `send` to `say`, defines
`pass` as a threadless Work handoff rather than a message, names all three
obligation dispositions, links to the detailed cross-team section, and points
to `baton --help` plus `baton --help VERB` as the grammar authority.

The focused W104 guide suite now pins the section boundary, required command
forms, disposition names, `say`/`send` distinction, threadless `pass`, detail
link, and help commands. Verification completed with:

- W104 plus active-public-document tests: 22 passed.
- Deployed-layout packaging regression: 1 passed.
- Complete `just test-v11` gate: 2,033 non-serial tests and 11 serial tests
  completed without failure; the ACP bridge test command also completed.
- Scoped and whole-tree `git diff --check`: clean.

No protocol, application, schema, CLI, runtime, or unrelated documentation
file was changed for W87.
