# Implementer progress — the ACP launcher contract reaches the turn

Created 2026-08-26 by `baton.claude` on claiming W14828, as the record
requires.

## Revalidation, and one thing worth saying plainly

I hit this defect. The first turn of this session opened with

    [BATON READY] ... Configured role instructions: ... This deployment
    supplies the exact Baton binary and explicit config; every invocation
    names --participant baton.claude.

— prose that says an exact binary is supplied and then names neither it nor
the config. So I did what the finding predicts a fresh model does: I went
looking, found `/home/sl/.config/baton/acp/baton.claude/load.json` still
pinned to `fc613e3`, and my first `claim` failed with

    /home/sl/baton-v11/baton.json: team 'baton' role 'approv' carries unknown
    fields ['instructions']

I recovered by reading the live binary out of `ps`, which is not a contract.
An operator repinned the persistent file mid-session — the temporary recovery
this record already names as a stopgap. **The reviewer's reproduction is
exact**, and everything below was revalidated against the tree rather than
taken from it:

- `promptText` in `baton_readiness.mjs` rendered the locator, role prose and
  policy cue, and received no launcher contract.
- `validateConfig` in `config.mjs` kept the four validated values in
  `config.baton` and returned `agent.env` straight from the operator document.
- `AcpAgentSession.setup` spawns `{...process.env, ...config.agent.env}` and
  neither derives nor checks the four.
- `conf/acp-claude.template.json` and `conf/acp-gemini.template.json` spell
  none of them.
- `launcherContract` already exists in the shared
  `codex-event-bridge/src/role_instructions.mjs`, and `acp_baton_bridge.mjs`
  already imports `readRoleInstructions` from that module — so the shared
  renderer was one import away.

## What was implemented (PLAN item 3)

**One source, two carriers, and neither may be maintained separately.**

- **The prompt.** `runBridge` renders the block ONCE, from the accepted
  configuration, after `loadInstructions` and before the first wait, spawn,
  session or prompt — and passes it to `promptText` for every delivered
  action. Rendered once because a per-prompt render could read state that
  moved; rendered THERE because `launcherContract` throws on a missing or
  blank field, so an incomplete contract refuses the launch instead of
  producing a partial prompt some turn then acts on. The block goes last, for
  the reason the Codex path already gives: role prose is a persona and can be
  long, the contract is short and exact.
- **The environment.** `validateConfig` derives `BATON_BIN`, `BATON_CONFIG`,
  `BATON_PARTICIPANT` and `BATON_ROLE` into `agent.env` from the same accepted
  `baton` section, and derives them LAST so they also override whatever the
  parent process exported — a stale ambient `BATON_BIN` is the same untrusted
  carrier as a stale file. An operator may still spell them, because existing
  templates do, but only to the same values: a conflicting entry refuses
  startup BY KEY rather than being resolved in favour of either side.
- **The shared renderer, imported rather than re-spelled.** A second textual
  format for the same four values is how the two adapters would drift into
  telling their contexts different things, and drift between two accounts of
  one launcher is this incident.
- Templates and README updated: `baton` is the single source, the prompt and
  the derived environment are the two carriers that cannot disagree, and an
  explicitly conflicting entry is a configuration refusal.

## What was implemented (PLAN item 4)

Seven regressions, and **the measured gap they close is that 69 green tests
asserted no launcher value in either carrier**:

- every action kind — Work, obligation, trial, poke — carries the block, each
  value exactly once, with the header and the invocation sentence;
- a `load` session gets the same block as a `new` one, because the turn that
  goes looking is the first turn of a fresh model however its session was
  selected;
- the REAL spawned subprocess observes the four values with a template that
  omits them entirely. The fake agent records its own inherited environment at
  startup now — reading the bridge's config object would only prove the config
  object;
- a stale inherited `BATON_BIN` (the retired `fc613e3` path, the incident's
  own shape) does not survive into the child;
- each of the four keys refuses startup when spelled to a conflicting value,
  and the same values spelled explicitly are accepted;
- two participants sharing one binary receive their own values in both
  carriers and never the other's;
- the block is six lines and leaks no state directory, policy path, working
  directory or persistent-file path — counted rather than described, so a
  fifth member has to be a deliberate change to that number.

**Two existing assertions were edited, and only their anchors.** Both required
the compact line to be the END of the prompt text. The block now follows it,
so `$` became `$` under `/m` — the wording they assert is unchanged, which is
what the finding's matrix requires.

## Verification

`evidence/gate-2026-08-26-implementation.txt`.

- `tools/acp-baton-bridge`: **77/77** (69 -> 77).
- **Every added case measured against the pre-change carriers**: with the
  prompt block and the derived environment removed, 7 of 77 fail. Sources
  restored byte for byte.
- Both shipped templates re-parse as JSON after annotation.
- The whitespace check is clean.

## The sibling suite is RED, and it is not this Work's

`tools/codex-event-bridge` is 413/414. The failure is
`an ambiguous obligation behind a deferred Work is reconciled`, a case the
seventh W11910 review added at 07:57 while this Work was being implemented,
against a real [P1] in my own W11910 correction: `#pastTheClaimSlot` skips an
ambiguous candidate on every retry, so a turn the server actually created is
never bound.

That is W11910's, it is currently routed to the reviewer, and this Work does
not touch `event_bridge.mjs`. The ACP adapter does not consume it — this
Work's own surface is green — but a red sibling suite is not something to
leave unsaid in a handoff.

## State

**Awaiting independent review.** PLAN item 6's rollover smoke remains
operator-owned; nothing here was verified against the running deployment and
no repository state was mutated.


## Review [P2] corrected — 2026-08-26

**The shared renderer still declared itself Codex-only**, and the reviewer is
right that this is contract documentation rather than a historical aside. The
paragraph beside `launcherContract` said ACP's ruled carrier was four explicit
`agent.env` values, warned that composing the block into ACP prompts would be
wrong, and concluded that only Codex paths compose it — while the ACP bridge
imported that exact function and composed it into every prompt.

This one is mine twice over: the dossier's own patch boundary named updating
that comment, and I updated the ACP README instead and moved on. Left standing,
it tells the next maintainer to delete the composition that fixes the incident.

**Rewritten to say what is true, with the chronology kept.** The renderer is
shared; `readRoleInstructions` still returns accepted role prose ALONE, which
is the property that lets one renderer serve two carriers; Codex composes it
into developer instructions and ACP into every readiness prompt plus the
derived child environment. W12229's ruling is preserved rather than erased and
marked superseded on carrier SUFFICIENCY by this incident, because that is how
the next reader knows the ACP composition is deliberate.

### And a gate, because the comment drifted for want of one

`the shared renderer's stated consumers are its actual consumers` compares the
paragraph to reality: both families must import the function, and the
paragraph may not claim a single consumer. Measured — restoring the
`CODEX-ONLY` heading turns it red.

That is the smaller point the [P2] exposes. Prose beside a shared function is
as capable of going stale as an inventory table, and this repository's answer
to a stale table is a gate that compares it to the code.

### Verification

Statuses captured on their own lines, never piped:

- `CODEX_STATUS=0` — 416/416 (415 → 416, the added drift gate);
- `ACP_STATUS=0` — 77/77;
- `V11_STATUS=0` — 3067 parallel, 52 serial, 77 ACP;
- `TEMPLATES_STATUS=0`, `DIFFCHECK_STATUS=0`.

No runtime or test behaviour changed, which is what the review asked for: the
correction is the paragraph, plus the case that keeps it honest.

## State

**Awaiting independent re-review.** PLAN item 6's rollover smoke remains
operator-owned; nothing was verified against the running deployment and no
repository state was mutated.


## Re-review [P2] corrected — 2026-08-26

**The same superseded claim, one layer out.** Last round I corrected the source
paragraph beside `launcherContract` and added a gate for it. The gate compared
that paragraph to reality and looked at nothing else — so the Codex bridge's
user-facing README went on telling operators the opposite rule: that ACP
receives only four environment variables, that the block is Codex-only, and
that a launcher rendering in an ACP prompt would be one family's mechanism
leaking into the other's.

That is the second round of exactly one mistake. The first was fixing the
README and missing the source comment; the second was fixing the source comment
and missing the README. Each time I corrected the surface I was looking at and
gated only that surface.

**So the gate is now about the RULE rather than about a file.** `every surface
that documents the launcher names both ACP carriers` checks all three places
that publish it — the Codex README, the ACP README, and the shared renderer —
in one case: each must name both ACP carriers, and none may declare the block
Codex-only or the prompt carrier a leak. A fourth document tomorrow is the only
way this goes stale again.

**Measured, and my first measurement of it was vacuous.** I mutated a sentence
that my own rewrite had already deleted, so the replace was a no-op and the
suite stayed green — proving nothing. Re-measured by genuinely reintroducing
the claim: both gates fire, `RI_STATUS` 0 → 1.

**The test prose the review also named** kept its assertion and lost its
explanation. `readRoleInstructions` returning role prose ALONE is exactly the
property that lets one rendering serve two families, so the assertion was right
under both the old rule and the new one; only the reasoning around it and its
failure message described a boundary that no longer exists.

### Verification

Statuses captured on their own lines, never piped:

- `CODEX_STATUS=0` — 419/419 (416 → 419: the reviewer's README gate, my
  all-surfaces gate, and the corrected prose);
- `ACP_STATUS=0` — 77/77;
- `TEMPLATES_STATUS=0`, `DIFFCHECK_STATUS=0`.

No runtime behaviour changed this round; the correction is documentation plus
the gate that keeps it honest.

## State

**Awaiting independent re-review.** PLAN item 6's rollover smoke remains
operator-owned and blocked on sign-off; nothing was verified against the
running deployment and no repository state was mutated.
