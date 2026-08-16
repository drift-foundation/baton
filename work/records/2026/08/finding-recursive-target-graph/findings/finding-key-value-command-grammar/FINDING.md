# Finding: v11 operation commands are cumbersome flag-oriented shell syntax

## Observed

During the second v11 trial, wiring one release dependency required:

```text
block 8b92cb10-W11 --on 8b92cb10-W12
```

The public grammar mixes positional operands and conventional `--option`
flags. It is serviceable for argparse-driven scripts but unnecessarily awkward
in the TUI command bar, where Work operations are the domain language.

## Confirmed decision — 2026-08-15

**Confirmed by Slawomir during the second v11 trial.** V11 operations use an
order-independent key/value grammar after the verb:

```text
block work=8b92cb10-W11 on=8b92cb10-W12
create team=baton kind=ops title="Cut next v11 trial release" origin=self-initiated body="Release gate"
```

The same operation grammar is used by the standalone CLI and the TUI command
bar. Executable-level bootstrap options such as `--config` and `--participant`
may remain conventional global options before the verb; the operation itself
uses `key=value` tokens. V11 replaces the current operation syntax rather than
carrying two permanent dialects.

Keys may appear in any order. Values containing spaces are quoted using the
same tokenization rules in the shell and command bar. Each token splits at its
first `=`, so a value may itself contain `=`. Unknown keys, missing required
keys, malformed tokens, and duplicate singular keys refuse. Only parameters
declared repeatable may occur more than once, preserving occurrence order.
Parsing performs no shell evaluation and never guesses a key from position.

Use semantic parameter names: the general dependency operation is
`block work=<consumer> on=<provider>`, not release-specific terminology.

This is queued for the next immutable revision. The current trial grammar and
authority are not rewritten in place.

## Pre-cutover audit — 2026-08-16

**Confirmed by source inspection.** `src/baton_work/cli.py` still defines the
public operation surface with argparse positional operands and `--option`
flags; the shared strict `key=value` operation grammar does not exist. This
Work is open in fact. It is a parser/public-interface change with substantial
regression scope, but it changes no persisted authority schema. It must be
implemented and reviewed before the fresh cutover rather than recreated as
unfinished Work afterward. Its dependent command-assist and batch Work remain
separate and will be classified by the same open-Work audit.

## Implementation boundary pin — 2026-08-16 (implementer, per T13 #162)

Inventory of every public v11 command, with the launcher/operation
boundary applied before editing:

**Launcher context (conventional options, BEFORE the verb):** `--config`,
`--participant`, `--expect-projection`. Nothing else. The former pre-verb
`--op-id`, `--ref`, and `--answer-ref` move INTO the operation grammar as
`op-id=`, `ref=` (repeatable, ordered), and `answer-ref=` (repeatable,
ordered), because operation identity and asset references are operation
semantics: they commit with the act, participate in retry fingerprints,
and are refused by pure reads and filesystem verbs through the SAME ruled
semantic refusals as before (the parser accepts the keys; the operation
decides).

**Operation grammar (every verb operand):** strict order-independent
`key=value` tokens after the verb, one dialect for the standalone CLI and
the TUI command bar. Tokens split at the FIRST `=` (values may contain
`=`); shells and the command bar share shlex quoting; no shell
evaluation; no positional inference. Unknown keys, missing required keys,
malformed tokens (no `=`, empty key), duplicate singular keys, retired
flag/positional spellings, and mixed dialects refuse BEFORE authority
access, with no residue. Repeatable keys (`ref`, `answer-ref`,
`template`, `assign`, `label`) preserve occurrence order.

**Semantic renames folded in:** `phase work=W to=X [reason=…]
[wait=gates|OBLIGATION_SEQ]` replaces the two `--wait-on-*` flags with
one `wait=` condition (matching the transition's own parameter);
`classify work=W as=VALUE`; `assess obligation=N as=VALUE`; `accept
obligation=N body=… (into=W | create=true kind=… title=… …)` — the
boolean `create` takes the literal value `true`. All other keys keep
their established names (`work=`, `thread=`, `obligation=`, `on=`,
`to=`, `expect=`, `reason=`, `directory=`, `locator=`, `root=`,
`template=`, `timeout=`, `after=`, `limit=`, `refresh=`, …).

Every verb — lifecycle (`init directory=…`, `activate directory=…`,
`regen`, `resolve locator=…`, `bootstrap root=…`), mutations, and pure
reads (`detail work=…`, `tree [work=…]`, `thread thread=…`, …) — uses
the one dialect; no second permanent grammar survives. No boundary
contradiction was found in the pinned text under this reading.

## Follow-up ruling — 2026-08-16: transfer is an explicit `pass`

**Confirmed by Slawomir during the fresh v11 trial.** The existing compound
form

```text
say thread=T body="..." on=W pass-to=team.kind phase=PHASE
```

is authoritative and atomic, but its verb reads like informal discussion and
hides the workflow act an operator is trying to perform. A baton transfer gets
its own canonical operation surface:

```text
pass work=W to=team.kind phase=PHASE thread=T comment="..."
```

`comment=` is deliberate: the text is durable handoff evidence, not a rewrite
of the Work description or contract. A pass still commits one indivisible
transition: append the comment to the chosen labelled Thread, change Current
and destination Phase, apply any explicit planned Next supported by the
transition, and release the sender's active claim. Refusal leaves both message
and workflow state unchanged.

Plain `say` remains discussion and may retain the independent `request=` (`@`)
operator. The new canonical `pass` replaces `say ... pass-to=...` for ownership
transfer rather than creating two permanent transfer dialects. Existing
immutable trial clients keep their shipped syntax; this is new Work and does
not reopen completed W13.
