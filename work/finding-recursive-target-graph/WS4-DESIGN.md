# WS-4 design — first-class discussions and `#WORK` labels

Author: `baton.implementer`
Date: 2026-08-15
Responding to: `c3ba3781c5b5ac233a2e25e3d6f16260` (design/ruling only)
No source, schema, or test edits made.

## 1. Inventory: what is implemented versus what was ruled

Implemented (WS-1..WS-3): `messages.work` — every message belongs to
exactly one Work; `seen(team, member, work)`; `work_participants(work,
team)`; `new_count` aggregates per Work over containment, gated by team
participation; every operator (`+`, `@`, `=>`, Next) is an argument of
`post <WORK>`; WS-2 immutable closure refuses posts to closed Work; WS-3
`accept` answers into the consumer Work's message list.

Ruled (2026-08-13, confirmed): a discussion is a reusable conversation;
a message belongs to exactly one DISCUSSION; `#WORK` labels are
many-to-many Gmail-style context — inert, never gating, never moving
Current, never satisfying an obligation, never touching readiness; `@`
and `+` are discussion tags; New deduplicates multiply-labelled
discussions at common ancestors.

The implemented model is therefore a deliberate WS-1-era narrowing
("Work-local discussion container"), now to be replaced. The couplings
that must not survive mechanically:

- **A1 `messages.work`** — the container IS the Work. Every consumer of
  `discussion(work)` (projection, TUI, New, WS-3's answer, WF stories)
  assumes it.
- **A2 `seen.work`** — cursors are per-Work; a multiply-labelled
  discussion would need N cursors or double-count.
- **A3 `obligations.work`** — WS-1 wake ("an obligation of the SAME
  work"), WS-2 close-withdrawal ("every pending @ the closing Work
  carries"), and WS-3 acceptance (grant scoped to "the requesting
  Work") all lean on one-obligation-one-Work. This is load-bearing and
  CORRECT product semantics; the design keeps it (see §4).
- **A4 `work_participants`** — participation feeds New's noise gate and
  the `+` fan-out record; under discussions, following/participation
  belongs to the discussion.
- **A5 close-refuses-posts** — WS-2's "closed work is immutable history;
  new evidence belongs in follow-up work" was stated when the message
  container WAS the Work. Under first-class discussions a message never
  mutates a Work row; the rule needs a discussion-level restatement
  (disposition D3).

## 2. Canonical records and invariants

- `discussions(id TEXT PK, created_seq, created_ts)` — identity
  `{uuid8}-D{seq}` (the Work-id pattern). Created atomically WITH its
  first message and any initial labels in one transaction; a discussion
  with zero messages never exists.
- `messages(seq PK, discussion REFERENCES discussions, author_team,
  author, body, ts)` — exactly one discussion per message; ordering is
  the global publication sequence (pagination cursor unchanged).
- `discussion_labels(discussion REFERENCES discussions, work REFERENCES
  work, added_seq, PK(discussion, work))` — the inert many-to-many.
  Add/remove are audited acts (`label`/`unlabel` events carrying
  discussion, work, actor, and the Work-team resolution snapshot);
  removal deletes the row — the events are the history. Duplicate add
  and absent remove refuse. Labels never appear on edges, obligations,
  or readiness paths.
- `discussion_followers(discussion, team, added_seq)` — replaces
  `work_participants` as the record `+` writes and New consults;
  contribution stays open to every configured member (R1 matrix), so
  following is attention wiring, not an ACL.
- `seen(team, member, discussion, seq)` — one cursor per member per
  discussion; `mark_seen` targets a discussion.
- Work creation: `create_work` atomically creates the Work, a NEW
  discussion, its `#WORK` label, and the first message — one transaction
  (today's creation atomicity, restated).
- Invariants: a message's discussion never changes; label add/remove
  never touches Work rows, edges, obligations, readiness, phase, or
  Current (break-sweep material); every label references live schema
  rows (FKs, the R52 discipline).

## 3. Label authority (disposition D1)

Labels are inert but not free: a label to Work W injects the discussion
into W's New and drill surfaces — noise, aimed at W's team.

- **Recommended:** `#W` may be added or removed by any configured member
  of W's OWNING team (contribution-grade, team-scoped). An outsider
  cannot decorate another team's Work merely by knowing its id; cross-
  team context arises the honest way — each team labels its own Work
  onto the shared discussion (exactly the convergence story: push's
  discussion is born with `#PUSH-1`; drift adds `#DRIFT-1` at
  acceptance).
- Alternatives: (a) current-handler-only — consistent with the ownership
  matrix but makes cheap context expensive; (b) any configured member —
  simplest, but licenses cross-team noise injection, which the finding
  names as the risk. Consequence of the recommendation: labelling is a
  new small entry in the authority matrix ("label your own team's
  Work"), below ownership, above nothing.
- Terminal Work may be LABELLED and unlabelled under the same rule
  (D3): the label is discussion context, not carrying activity on the
  closed record; the closed Work's own state stays byte-immutable.

## 4. Operators on discussions (dispositions D2, D8)

All three operators remain arguments of posting a message — now into a
discussion: `post DISCUSSION --body …`. The operator's WORK TARGET is
explicit, never inferred from labels or punctuation:

- `--on WORK` selects the one labelled Work an `@`, `=>`, or `--set-next`
  acts against. **Required whenever the discussion carries ≠ 1 label;
  with exactly one label it may be omitted but is still resolved,
  recorded, and echoed in the audit payload.** No operation ever affects
  several Works (the finding's leaning, adopted: one act, one Work,
  explicit).
- `@team.kind --on W`: creates the obligation ON W (A3 preserved —
  obligations stay Work-scoped, so WS-1 wake, WS-2 withdrawal-at-close,
  and WS-3's request-scoped grant survive unchanged). The old open
  question about route-tag pending/active/resolved lifecycle (D8) is
  thereby CLOSED without a new state machine: the discussion-level `@`
  lifecycle IS the obligation lifecycle already ruled
  (pending → responded/disposed/accepted/withdrawn).
- `=> team.kind --on W` (and `--set-next`): passes W's Current under the
  existing handler gate. A pass in a discussion never moves any other
  labelled Work.
- `+team.kind`: registers the expanded endpoints' teams as discussion
  FOLLOWERS (attention only). Exact expansion recorded as today;
  dedup per (team, message) unchanged; zero responsibility or readiness
  effects. Follower promotion: `=>`/`@` naming a following team is the
  promotion — atomic because it is one post transaction; no separate
  primitive.
- WS-3 `accept` (§6) is the fourth operator and gains one inert effect.

## 5. Seen and New over labels and containment (disposition D6)

- `New(member, W)` = count of DISTINCT messages m, in any discussion D
  carrying a label to W or to a containment descendant of W, with
  `m.seq > seen(member, D)`, counted ONCE — deduplication falls out of
  counting distinct message seqs, and a multiply-labelled discussion
  under one ancestor contributes each message once at that ancestor.
- The noise gate moves from team-participation to the labels themselves:
  a discussion enters my home's New only by carrying a label to my
  team's Work — which only my team can apply (D1). Cross-team
  discussions I merely follow appear in a follower surface, not in my
  Work tables.
- Label ADD makes the discussion's unseen backlog count at the newly
  labelled Work immediately (honest: the context is new to that Work);
  label REMOVE stops the counting; the cursor rows persist harmlessly.
  Per-member cursors never reset on relabelling.
- `mark_seen` stays the only cursor writer, per discussion, monotonic.

## 6. WS-3 acceptance reconciled

`accept` keeps every ruled effect — grant, terminal `accepted` state,
provenance edge, readiness, R47 wake — and its rationale message lands in
the CONSUMER'S ORIGINATING DISCUSSION (the one carrying `#CONSUMER-WORK`,
where the `@` was raised; the obligation gains a `discussion` column
recording where it was asked). In the same transaction the acceptance
adds the `#PROVIDER-WORK` label to that discussion (authority: the
provider labels its OWN Work — D1-consistent). Result: one conversation
now visibly spans both records as inert context, while the GATE remains
exclusively the explicit edge with `via_obligation`. Nothing about
labels enters the readiness predicate (break-sweep: drop the label —
gating unchanged; drop the edge — the association test fails).

## 7. Terminal Work and the discussion (disposition D3)

- **Recommended:** posting into a discussion is ALWAYS allowed — labels'
  states never gate conversation, and a message no longer mutates any
  Work row, so WS-2's Work-immutability is untouched in substance. The
  WS-2 surface rule "closed work refuses posts" is restated as: closed
  Work refuses CARRYING activity (@/=>/Next targeting it, rounds,
  reports, new edges); commentary in a discussion that happens to carry
  its label is context, like reading. New on a closed Work stops being
  interesting because closed Work leaves default tables; drill still
  shows the discussion.
- Relabelling around terminal Work: allowed under D1; removing the LAST
  live label (or the last label entirely) leaves an orphan discussion —
  allowed, still readable and postable, listed only via its followers'
  surfaces and the audit; a label can re-attach it later. The
  alternative (refuse removing the final label) manufactures a fake
  invariant the model does not need.
- Consequence to surface honestly: WF-06's "closed refuses posts"
  checkpoint and the WS-2 focused regression change their expected
  refusal set (posts move to discussions; the refusals stay for
  carrying operators).

## 8. Announcements (WF-07) without a notice object

An announcement is an ordinary discussion (typically labelled to the ops
team's own Work) whose message carries `+*.*`: full live-endpoint
expansion recorded in the act, every matching member's attention raised
exactly once per message (distinct-message counting per §5), zero
obligations, zero Current movement, zero readiness effects, wildcard
`@`/`=>` still refused. Only the follower/New wiring changes underneath;
the observable contract of WF-07 is preserved verbatim.

## 9. Schema boundary (disposition D7)

Fresh schema v8; no compatibility shim. No v11 authority exists outside
this repository's gates (deployment is explicitly held), so the honest
boundary is: WS-4 schema replaces the Work-local containers outright,
tests initialize fresh as they always have, and the release-catalog work
(held) ships v11 only after WS-4. A migration tool for pre-WS-4
databases would migrate data that exists nowhere; refusing to build it
is the smallest honest choice — but it is a product statement and listed
for confirmation.

## 10. WF-05/06/07 walked

- **WF-05**: three consumers create Works (each born with its own
  labelled discussion), each asks `@drift.bug` IN its discussion
  (`--on` its own Work); drift accepts each — the three consumer
  discussions each gain `#DRIFT-1`; deliberate drill from PUSH-1 →
  labels → DRIFT-1 → its `blocks` shows the siblings; default tables
  stay noise-scoped (no consumer sees siblings' Works in home); DEP=3;
  the label-versus-edge proof FINALLY lands: remove a label — readiness
  and DEP unchanged; the closure fanout unchanged.
- **WF-06**: the release epic's children each carry their own
  discussions; a shared "release readiness" discussion labelled to the
  root AND both children exercises dedup — one message counts once at
  the root (common ancestor) though reachable through two children; New
  decomposition (own + children − duplicates) asserted exactly.
- **WF-07**: as §8; plus one member marking the announcement discussion
  seen moves only their cursor.

## 11. Matrices and slices

Refusals: duplicate/absent label, outsider labelling a foreign Work,
`--on` absent with ≠1 label, `--on` naming an unlabelled Work (refuse:
the selection must be within the discussion's context — or allow any
Work? RECOMMEND refuse, keeping "the discussion carries its operating
context" honest — listed as D9), operators targeting closed Work,
wildcard `@`/`=>`. Races (both orders, `_write`-seam): label-vs-unlabel,
label-vs-work-close, post-vs-unlabel (message lands; label already gone —
legal serials), two creates of one label, accept-vs-unlabel of the
consumer label, mark_seen monotonic race. Crash: fault injection through
creation (work+discussion+label+message) and accept (now including the
provider label). Restart: full reconstruction of discussions, labels,
followers, cursors, New. Retry: the stated no-op-id boundary. One-
snapshot: discussion detail (messages page + labels + followers +
snapshot token) and every New/home read; purity hash-sweep extended over
the new tables. Source+packaged stories throughout; bounded TUI keeps
rendering the (now discussion-backed) message list and New with no new
navigation.

Slices — WS-4 should NOT land monolithically; the smallest honest split:

- **Slice A (model):** schema v8, discussions/labels/followers/seen,
  creation atomicity, label authority, plain posting, New/seen
  semantics, projections/pagination, WF-06 dedup story, its focused
  matrix. Operators keep their current call shape against the Work's
  born discussion, so every existing test stays green modulo mechanical
  container renames.
- **Slice B (operators + acceptance):** `--on` selection, obligations'
  discussion column, follower-based `+`, acceptance labelling, D3
  terminal-post restatement, WF-05/WF-07 under the new grammar, the
  race/fault matrix over operators.

Each slice ends at a reviewer gate with sweeps.

## 12. Dispositions required from Slawomir

1. **D1 label authority** — owning-team members (recommended);
   alternatives handler-only or anyone. Consequence: one new small
   authority-matrix row.
2. **D2 explicit selection** — `--on` mandatory at ≠1 label, always
   recorded; no multi-Work operations. Consequence: no punctuation
   inference anywhere; scripts must name their target.
3. **D3 terminal-Work restatement** — posting always allowed; closed
   Work refuses carrying activity only. Consequence: WS-2's closed-post
   refusal is formally superseded at the discussion surface.
4. **D4 orphan discussions** — creating unlabelled discussions and
   removing the last label are allowed (recommended). Consequence: a
   reachable-only-via-audit/follower conversation is a legal state.
5. **D5 acceptance labelling** — accept adds `#PROVIDER-WORK` to the
   consumer's originating discussion in the same transaction
   (recommended). Consequence: WS-3's association becomes humanly
   navigable context plus the unchanged formal gate.
6. **D6 seen/New** — per-discussion cursors, distinct-message counting,
   label add counts backlog immediately (recommended).
7. **D7 fresh schema, no migration** (recommended, §9).
8. **D8 route-tag lifecycle** — CLOSED by construction: the @ lifecycle
   is the obligation lifecycle; confirm no separate state machine.
9. **D9 `--on` scope** — the selected Work must be currently labelled on
   the discussion (recommended); alternative: any Work id.

Stopping here for reviewer and Slawomir rulings; no later-phase work
begun.

## Post-review corrections (578d052b, accepted for the red-team pass)

R54 — a Work has a discussion SET: Work detail lists related discussion
summaries (stable id, last-message seq, viewer New, deterministic order);
no merged single timeline; the born discussion is not a permanent primary.
R55 — bare-operator scope counts the ELIGIBLE set (labels passing the
operation's Work gate), not total labels; omission allowed only at
eligible-cardinality one; foreign context creates no ceremony.
R56 — participation is monotonic and separate from the obligation
lifecycle: own #WORK, +, incoming @, incoming => each add the team once;
nothing removes it in WS-4; expansion recorded even when deduplicated;
the follower surface includes @/=> participation, not only +.
R57 — New decomposition returns own + per-child + overlap + total with
total = own + sum(children) − overlap; ancestor dedup visible, jump-to-
unread honest.
R58 — the reviewer recommends the live-context boundary over my orphan
model: creation requires ≥1 authorized label; removing the final label
refuses; plain posting requires ≥1 labelled OPEN Work (follow-up Work
first when all context is terminal). Awaiting Slawomir's explicit choice.
R59 — accept tolerates a pre-existing provider label
(provider_label: added|existing audited); obligations.discussion applies
to EVERY response obligation (respond also answers into the originating
discussion); removing the consumer label never cancels the obligation.
R60 — Slice A's operator bridge is an internal test scaffold only, never
documented or packaged as public API; Slice B removes it before WS-4
acceptance; Slice A must expose the explicit discussion surface.

## Pre-implementation red-team notes (Slice A, resolved)

- **RT1 (resolved — consistent).** WS-2's "closed Work refuses posts"
  maps exactly onto live-context: a discussion whose only labels are
  terminal refuses new messages; the born-discussion bridge therefore
  preserves the observable refusal for every existing closed-work test.
- **RT2 (resolved — untouched).** Obligation withdrawal-at-close,
  obligation-backed waiting, and the WS-3 grant all key on
  `obligations.work`, which Slice A does not touch.
- **RT3 (resolved — bridge rule).** Internal message writers (post
  bridge, respond, accept) target the Work's BORN discussion, found
  derivably (the discussion sharing the Work's created_seq) — no
  primary-discussion column is added, honoring R54. Accept's create form
  births the provider's discussion in the same transaction.
- **RT4 (resolved — bridge rule).** The Work-addressed `mark-seen`
  bridge advances the viewer's cursor on EVERY discussion currently
  labelled to that Work (the only reading under per-discussion cursors
  that keeps "New drops to zero" true); the canonical public verb is
  discussion-scoped. Bridge internal, Slice B removes it.
- **RT9 (supersession, justified).** The WS-1 representation gated New
  by `work_participants` ("no aggregation across a team boundary"). The
  pinned discussion rulings define New as member-relative over labelled
  discussions with NO team gate — the noise boundary lives in home-table
  scoping, not in the counter. The one WS-1 assertion pinning the old
  gate (`test_new_is_per_member_and_decomposable`'s zero-children claim
  for an outside viewer) is superseded and will be rewritten with this
  note as justification. Not a contradiction: the ruling text always
  said "distinct messages unseen by the viewing member".
- **No unresolved product decision found.** Proceeding with Slice A.
