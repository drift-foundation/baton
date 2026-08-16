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
