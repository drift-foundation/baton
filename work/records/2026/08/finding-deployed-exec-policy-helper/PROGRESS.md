# Progress

**State — 2026-08-21:** round-2 review corrections implemented; awaiting
independent review.

## Response to `review-2026-08-21T04-26-31Z.md`

All three findings confirmed and fixed. Nothing was argued down.

- **P1 — the two-target template documented a one-target installation.**
  Confirmed: `event_bridge.mjs:147-155` preflights every
  `targets.*.identity.participant` against the single `execPolicyFile`, and
  the template configures `baton.codex` and `baton.tuner`. The generator
  interface stays singular, as the review asked; the shipped instruction now
  carries the composition — run once per participant, APPEND into
  `baton.rules.staged`, then `mv` it into place — and says why staging rather
  than redirecting onto the live file: `>` truncates it before any operand is
  validated, and a second `>` drops the first participant's rules. The
  template comment also states outright that the one file must carry the
  rules for ALL configured identities.
- **P2 — the overwrite regression checked the name, not the bytes.**
  Confirmed. `exec_policy_cli.test.mjs` now reads the pre-existing
  `baton.rules` back and asserts it is still exactly `untouched\n`.
- **P2 — "same artifact the dispatcher imports" was wrong.** Confirmed:
  `conf/infra.example.json` runs the dispatcher from
  `<source>/tools/codex-event-bridge/bin/codex-event-bridge` and the release
  ships no `bin/codex-event-bridge`. Every such claim is replaced with the
  confirmed statement — the release carries a byte-equal immutable COPY of
  the reviewed source helper, and byte parity is the guarantee. Nothing now
  implies this Work co-deploys the dispatcher.

## What changed

- `tools/codex-event-bridge/src/exec_policy.mjs` — the strict, stdout-only
  direct invocation (`identityFromOperands`, `generate`, `USAGE`, and a
  guarded `invokedDirectly` entry). The reviewed exports are byte-for-byte
  unchanged: `RULED_VERBS`, `rulesFor`, `parseRules`, `auditRules`,
  `auditRulesFile`, `assertPolicyProvisioned`. Direct invocation is detected
  by realpath-comparing `process.argv[1]` against this module's own path, so
  importing it stays silent — the bridge imports it during startup preflight.
  Round 2 corrected the header's artifact-identity claim.
- `tools/deploy_work.py` — `SOURCE_SHARED_GATE` carries
  `tools/codex-event-bridge/src/exec_policy.mjs`, so the release installs it
  at `lib/codex-event-bridge/src/exec_policy.mjs`. No third `bin/` entry
  point; the W163 two-entry pin is unchanged. Round 2 corrected the comment.
- `conf/codex-event-bridge.template.json` — the execPolicyFile comment names
  the installed generator, states that the one file must authorize every
  configured identity, and shows the runnable once-per-participant staged
  procedure. No checkout locator remains.
- `tools/codex-event-bridge/test/exec_policy_cli.test.mjs` (new) — source-side
  regressions named `W415 packaging: …` so the focused pattern selects them:
  output parity with `rulesFor()`, operand-order independence,
  creates-nothing AND overwrites-nothing (asserted on bytes), silence on
  import, the malformed-operand matrix, and a
  generate→`assertPolicyProvisioned` round trip.
- `tests/work/test_deploy_v11.py` — six additive cases on the ACTUAL deployer
  lane, using the existing `dist` fixture: deployed byte-parity with source;
  the shipped template names the installed path, no checkout path, every
  configured participant, and the append-into-staged procedure; the deployed
  generator run from the immutable target with no `PYTHONPATH` emits output
  byte-identical to the source helper AND the four literal approved rules;
  every malformed invocation is refused with empty stdout; importing the
  deployed artifact emits nothing; W415's
  exact-only/exact+broad/broad-only/extra-verb/other-participant matrix runs
  through the DEPLOYED module's exports; and the new P1 case follows the
  shipped procedure for BOTH template identities, proving the deployed
  auditor accepts the combined file for each while a one-participant file
  refuses the other.

## Verification

- `npm test` in `tools/codex-event-bridge`: 172 pass, 0 fail;
  `--test-name-pattern=W415`: 27 pass (baseline was 22).
- `.venv/bin/python3 -m pytest tests/work/test_deploy_v11.py`: 18 passed.
- `test_w163_deploy_bridge.py`, `test_w415_approval_incidents.py`,
  `test_w459_fresh_contexts.py`: 75 passed.
- The complete v11 gate: 2784 passed (non-serial) and 52 passed (serial).
- The ACP acceptance in `tools/acp-baton-bridge`: 55 pass, 0 fail.
- The whitespace check over the diff is clean.
- The P1 case was checked against its own negative: driving the combined-file
  assertions with a one-participant file fails with the deployed auditor's
  `does not authorize [claim, say, pass, close] for baton.tuner`.

## Boundaries held

- No schema, authority, config-grammar, or runtime-dispatch change.
- The four-verb capability is unchanged; nothing widens it. The generator
  interface stays singular — one participant per invocation.
- `bin/` still ships exactly `baton` and `acp-baton-bridge`.
- No existing test's assertions were edited or weakened; every test change is
  a new file or a new function, except the round-2 strengthening of
  assertions in the file this Work added.

## Not done here

- The `d46ab1e` release is immutable, so its recorded source-helper stopgap
  still applies to that rollout. This change takes effect in the next
  deployment.
- Nothing was staged or recorded in history; the working tree carries the
  diff for Slawomir.
