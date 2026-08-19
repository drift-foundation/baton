# Progress — public documentation cutover

Owned exclusively by the implementer (`baton.claude` under v11).

## Step 1 — W103, the unblocked surface (2026-08-17)

Claimed W103. Rewrote the active public entry points; historical release
records and dossiers were left byte-honest, as the finding requires.

### `docs/AGENTS-MAILBOX-PROTO.md`

Replaced wholesale with the protocol-11 agent contract, keeping the
filename because participating repositories point their policy at that
exact path. A note at the top says so explicitly, and says the v10
mailbox is retired rather than a fallback — otherwise the stable path
silently changes meaning under readers who never re-read it.

It teaches what an agent actually has to get right: claim before
executing; `wait` is participant-relative and read-only; the action key
is an assignment EPISODE, not Work identity; `pass` is one atomic
threadless event whose phase comes from the destination route; a
directed request waits by default; `release` is an exact
compare-and-swap; heartbeat silence is not failure; retries are
effectively-once on the EFFECTIVE operands. The one-live-consumer
convention is kept and extended with the W49 lesson — a queued readiness
line is an edge to re-evaluate, never authority to act from.

### `README.md`

Replaced, not line-edited, per the explicit instruction. 868 lines of
protocol-10 product manual became a concise v11 entry point: the
topology diagram from the finding, the three boundaries it names, a
quickstart exercising only `just deploy-v11` / `init` / `activate` and
the v11 surfaces, the strict `VERB key=value` grammar with real
examples, what a team actually does with Work, and a documentation table
that LINKS to the operator contract rather than duplicating it.

### Removals

`docs/LEGACY-CUTOVER-ON-DEMAND.md` was live fallback guidance, not a
release record, and is gone. `assets/artwork/baton-tui.png` visibly
depicted the retired v10 inbox, so it was removed rather than
relabelled. The finding allows replacing it with a sanitized v11
capture or removing it until one exists; producing a trustworthy
screenshot needs a scratch authority and a human eye on what it exposes,
so removal is the honest interim. No v11 image is claimed to exist.

### Distribution boundary

`tools/deploy_work.py` now ships `doc/AGENTS-MAILBOX-PROTO.md` with the
release, so a team bootstraps its agent policy from the same exact
release as its CLI. Verified against a scratch `just deploy-v11`: the
deployed copy is byte-equal to source, names protocol 11, and every
documented installed path exists.

### Verified

Every repository-local README link resolves. A vocabulary scan of the
active documents finds no `baton-tui`, `send-notice`,
`baton-codex-monitor`, `codex-baton-stack`, or protocol-10 launch
instruction outside the one sentence that explicitly names the
retirement.

## Deferred, with reasons

**The Codex documents.** `docs/CODEX-APP-SERVER-EVENT-CONNECTIVITY.md`
and `tools/codex-event-bridge/README.md` are in W103's inventory, but
the finding requires them to describe the stack shape that exists AFTER
W101 removes `stack.mjs`, `baton_source.mjs`, and the monitor entry
points. W101 is blocked (below), so writing that prose now would
document a shape the tree does not have — the hybrid the finding
explicitly forbids. Held until W101 lands.

**`tools/acp-baton-bridge/README.md`** is a small self-contained
correction (co-deployment wording; stop freezing a projection major in
prose) and is not blocked; it is simply not done yet.

## W101 is blocked, and the constraint is live

W101 is claimed by me and deliberately NOT started. Its own record
carries a superseding execution order: it must not remove or rewrite the
live Codex paths until W102 completes the standalone cutover and
verifies every v10 consumer is gone.

That constraint is currently TRUE, not theoretical. Twenty-one live
processes import `tools/codex-event-bridge/src/stack.mjs` and
`src/baton_source.mjs` FROM THIS WORKING TREE, alongside the deployed
v10 CLI, and they own the app server for the reviewing Codex session.
Deleting those files now would break the participant doing the review.
W102 is still in review with `baton.ops`.

Baton's dependency graph made W101 actionable because W2 closed; the
ordering constraint lives in the record, not the edge. Recorded here so
the next reader does not conclude the graph was wrong.

## Step 2 — W103 R1-R6 (2026-08-17)

**R3 was a correctness bug in the contract I wrote, and the important
one.** The agent policy said `wait` returns only ready UNCLAIMED Work.
The canonical projection also returns Work to its exact claimant so the
same participant can continue an active episode — the half that matters
after a restart. An agent following the shipped policy could have walked
past its own claimed Work, which is precisely the failure mode this
session hit and fixed elsewhere. Both halves are now stated, with the
restart case named, and a regression asserts both are present.

**R4 — I certified grammar that is still in review.** The README and
agent policy described W159's wait-by-default as current while W159 sits
in changes-requested. Documentation describes the CERTIFIED release, not
the intended next patch, so that wording is removed: the request text
now says what is true today — one obligation, ownership unmoved, and
that Work which cannot proceed suspends on that exact obligation. The
default returns when W159 is accepted.

**R2 — the entry point routed readers into the retired model.** The
documentation table linked EFFECTIVE-BATON, which W104 has not
rewritten. The link is removed with a sentence saying why and that it
returns. The regression for this SELF-RETIRES: it only forbids the link
while that file still contains v10 vocabulary, so it stops constraining
the moment W104 lands.

**R1 — split rather than left dangling.** The ACP README was not blocked
and is done: co-deployment stated without contradiction, and the
projection major no longer frozen in prose, because a number restated
there is a second source of truth that goes stale silently. The two
Codex documents genuinely cannot be written yet, so per the review's own
alternative they now have a tracked child, W233, with its own record
stating the W102 -> W101 -> W233 ordering and why anticipating a removal
is the same defect as lagging one.

**R5 — the acceptance claims are now standing checks.** A manual pass
and a scratch verification do not protect a release from regression. New
tests/work/test_w103_public_docs.py scans the active documents for
retired launch paths, refuses taught mailbox verbs while allowing them
to be NAMED as retired, resolves every README repository link, and pins
both halves of the wait contract. test_deploy_v11.py now asserts the
deployed agent policy is byte-equal to source and names protocol 11.
Historical evidence is excluded by construction rather than by
exception, so release notes and dossiers stay byte-honest.

One thing the scan taught me while writing it: my first version checked
each LINE for the retirement disclaimer, and failed on my own text
because the sentence wraps across two lines. It now reads a window,
which is what a prose scan has to do.

**R6** — PLAN.md now reflects completed, split, and deferred state
rather than the original queued list.

Gate: 1025 passed + 4 serial + acp 35/35 on 32 cores; diff --check clean.

## Step 3 — revalidation on the current tree (2026-08-19)

Re-claimed as W3 after the projection-12 cutover renumbered the ledger.
Every deferral this record carried was re-checked against the tree
rather than trusted, and two of them are resolved by facts that changed
while the record waited.

**The W101 blocker is GONE, and the deferral with it.**
`tools/codex-event-bridge/src/stack.mjs` and `src/baton_source.mjs` no
longer exist; the v11 cutover removed them, and nothing on this host
imports them any more. The constraint recorded above — twenty-one live
processes holding those files open — was true when it was written and
is now historical. `docs/CODEX-APP-SERVER-EVENT-CONNECTIVITY.md` and
`tools/codex-event-bridge/README.md` were re-read against the shipped
bridge: they describe the standalone app server, the generic event
dispatcher and the separately launched `codex-baton-bridge`, the
documented entry points all exist in `tools/codex-event-bridge/bin/`,
and the retired stack vocabulary is absent. **Outcome: satisfied, not
by me — the rewrite landed with the cutover.** The tracked child this
record split them into (W233 in the old numbering) has no successor on
the current ledger and needs none.

**`docs/EFFECTIVE-BATON.md` is v11, so the parked link is back.** W104
landed; the README's documentation table links it again, and the
self-retiring regression stopped constraining exactly as designed.

**R4's parked wording returns, because the behaviour is certified.**
W159's wait-by-default is in the shipped grammar (`say`'s `wait=` help
states the default) and in the accepted operating guide. The agent
policy and the README now say that a directed request BLOCKS by
default, suspends the Work you are executing on that exact obligation,
releases your claim, refuses when you are not executing it, and takes
`wait=false` as the explicit asynchronous override.

**The agent contract was missing an entire wake class.** `wait` returns
four action kinds; the shipped policy taught three. A poke addressed to
this participant is a certified participant action — it rode the 12.0
major — and an agent following the policy met an entry it had never
been told about. This is R3's defect one level up, and it is the gap I
reported as an operational finding while implementing W17: the poke
primitive shipped with no operator documentation at all. It is closed
here for the agent contract and the README:

- the policy's `wait` list names pokes as the fourth kind and says they
  come LAST, because a question never displaces the workflow you were
  woken for;
- a new bullet teaches `poke`/`poke-answer`: it names a participant and
  never a route, carries no workflow authority, and its one terminal
  answer reports runner facts whose vocabularies all lead with
  `unknown` — meaning the adapter cannot see it, never that it is fine;
- and that the authority reports canonical Work state BESIDE the
  agent's claim rather than instead of it, because the disagreement is
  the useful part;
- the README gains the same fact at product level plus one grammar
  example.

**Standing checks, not prose promises.** Two regressions were added to
`tests/work/test_w103_public_docs.py`. The first derives the wake kinds
from `participant_actions` itself and requires the policy to teach each
one, so a fifth kind fails on the day it ships rather than on the day
somebody notices the prose is short — the generalization of R3. The
second ties the blocking-default wording to the grammar's own help
text, so if that default ever changes the documentation fails with it.

**Deliberately NOT documented here.** `teams` and `inbox` (W25) are in
review, not certified. R4's rule is this record's own: documentation
describes the certified release, not the intended next patch. Their
operator prose ships with that Work, in the same review.

## Verification (2026-08-19)

- `tests/work/test_w103_public_docs.py` — 10 passed (2 added).
- The complete v11 gate, `just test-v11`, exits 0 on this tree: **1990
  passed** (parallel), **40 passed** (serial), ACP acceptance green.
