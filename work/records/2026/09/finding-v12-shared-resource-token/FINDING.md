# G1 — one shared resource-token owner, integrated with ControlStore, attempts and OCI

Bound dossier for v11 Work W275617, "V12: Shared resource-token lifecycle and Docker
enforcement". Created by baton.claude under claim 275634, 2026-09-26, because owner
275617 requires the dossier bound and the decision pinned BEFORE implementation.

## Authority and exact selection

Owner 275617 (thread T275617) selects **G1 only** from
`baton:work/records/2026/09/finding-v12-design-alignment-audit/AUDIT.md`, under the
accepted specification `baton:v12/DESIGN.md`. The audit's G1 row asks for:

> One shared token owner integrated with ControlStore, attempts and OCI: atomic
> conflict/resource pins; exact launch operation; typed container binding;
> generation-safe return; bounded renewal vs expiry; overdue restart and unknown
> hold. Pin duration/grace/version policy before execution.

**Excluded by the owner, explicitly:** the token-bound maintenance filesystem
executor (G2), the workspace/removal consumer (G3), context save/restore (G4), and
every other audit recommendation. No W270664 reroute. No broad suite, live
provider or engine, deployment, cleanup or Git mutation.

## The governing specification, pinned by digest

    v12/DESIGN.md   7f504a5edbb46acae739cab0727173fc1c51098300ae8048d25b56bba274cee0   59518 bytes

That is the amendment I signed off on at W274875 (review-2026-09-26T12-14-30Z.md).
The requirements this Work must satisfy are TOK-1 … TOK-12, DB-1 … DB-7, HOST-1 and
the section 17 proof rows for token admission, return/handoff, expiry, renewal and
maintenance/reset. **If DESIGN.md changes, this digest is stale and the pin must be
re-read rather than assumed.**

## THE DECISION: one owner module, and W270664's token records are SUPERSEDED by it

Owner 275617: "do not start a second removal-specific lease system". The current
tree contains exactly such a thing — my own. Under W270664 I added
`TOKEN_SECONDS`, `TOKEN_BOUND_KIND`, `TOKEN_REVOKED_KIND`, `TOKEN_CEASED_KIND`,
`token_of`, `bind_token_container`, `revoke_expired_token`, `_token_terms` and an
expiry gate inside `_admitted_removal`, all in
`v12/python/src/baton_v12/worker_manager/workspaces.py` (dac1ba4e at that hand-off).
It is removal-specific by construction: its identities embed the attempt and a
removal ordinal, and it governs one boundary.

**So the decision is: a new module owns the token, and the W270664 records become a
CONSUMER of it rather than a parallel system.** Concretely:

* **New owner:** `v12/python/src/baton_v12/worker_manager/tokens.py`. Nothing else
  mints, renews, revokes or settles a resource token.
* **W270664's four record kinds are retired at the point G3 migrates its consumer**
  — not silently re-labelled, and not duplicated. Until then they remain as the
  accepted removal evidence; this Work does not edit them, because G3 owns that
  consumer and the owner excluded it here.
* **Why not extend `workspaces.py`:** the conflict domain of a shared token is not
  a workspace. It must name attempts, contexts, lines and custody storage, and
  `workspaces.py` cannot own facts about contexts without becoming the second
  general-purpose module this audit is trying to remove.

## Exact owned paths

Mine under this Work:

    v12/python/src/baton_v12/worker_manager/tokens.py              NEW, the owner
    v12/python/src/baton_v12/worker_manager/store.py               ONLY if a schema/table is needed (see below)
    work/records/2026/09/finding-v12-shared-resource-token/        this dossier
      FINDING.md, PLAN.md, PROGRESS.md, VERIFICATION-SELECTORS.md
      test_shared_resource_token.py                                the bounded selector

Read-only for this Work, and NOT edited here: `workspaces.py`, `intake.py`,
`custody.py`, `oci.py`, `attempts.py`, `provider_context.py`, every tool, and every
sibling dossier. Touching `workspaces.py`'s removal token is G3's work.

## Schema and API impact, stated before implementation

**Preferred: no schema change.** The existing `operations` journal already carries
everything a token needs — a derived operation identity, a kind, a recomputed
signature and a committed document — and every W270664 record uses it. A token is
then: one `*.token-acquired` record per (conflict domain, generation), plus
`*.launch`, `*.bound`, `*.renewed`, `*.returned`, `*.revoked` and `*.ceased`
records at derived identities, read back through `replay`.

**What would force a schema change, named honestly so it is a decision and not a
surprise:** efficient "is any token outstanding for this conflict domain?" queries.
The journal is keyed by operation identity, so the ordinal-walk pattern I used in
W270664 (`standing_removal`) works but is O(generations) per question and cannot be
indexed. If measurement shows that is unacceptable at the real admission sites, the
minimal addition is ONE table — `resource_tokens(domain TEXT PRIMARY KEY, generation
INTEGER, operation TEXT, state TEXT, expires_at TEXT, container TEXT)` — as a
PROJECTION of the journal, never as the authority. **That is a `store.py` schema
change and needs its compatibility effect recorded and reviewed before I write it.**
I will implement journal-only first and report the measurement.

**Policy to pin before execution** (audit: "Pin duration/grace/version policy"):
these are profile selections, and I am pinning them as defaults this Work uses,
subject to owner correction — token lifetime 900s; stop grace 30s before a stop is
treated as unresolved; renewal permitted only while unexpired, bounded to 4
renewals per generation; token record version 1. **None is invented silently: each
appears in the dossier and each is a named operand, not a literal buried in a call.**

## First executable milestone

**One shared token acquired and returned around a real OCI-launched execution, with
a competing caller refused.** Concretely: `tokens.acquire` for a conflict domain
derived from an attempt; the launch operation journalled before any container
exists; the eventual container bound by typed evidence from the OCI boundary;
normal return conditional on confirmed termination of that exact container (TOK-5);
and a second caller for the same domain refused while the first is outstanding.
Everything through a real disposable `ControlStore` and a controlled engine
boundary — no live Docker, per the owner and DESIGN §19.

Not in the first milestone, and scheduled after it in PLAN: gen1/gen2/gen3
exclusion, late-binding refusal, renewal-versus-expiry arbitration, lost replies,
restart reconciliation, engine-failure holds.

## Preserved, not traded away

W270664's regression evidence and its accepted probes; W257624's restoration
region; the accepted no-implicit-reopen refusal; positive shutdown and recovery
behaviour already in the tree. No external I/O under a database transaction — the
rule this Work's own admission and settlement must obey, and the one DB-1 states.

## 2026-09-26T13:29Z — reviewer continuation clarification

Under claim275658, review-2026-09-26T13-29-00Z.md records no implementation
candidate yet. Return directly to implementation under existing owner275617.
The earlier owned-path restriction declaring every production caller read-only
is superseded as a proposed implementation plan: implementer must pin minimal
caller/adapter/serving ownership to deliver the expressly selected connection.
G2/G3 filesystem/removal migration remains excluded. No files assigned to other
Work are silently taken over by this clarification.

The earlier attempt-derived domain wording is narrowed: conflicting attempts
must resolve to the same durable resource domain and pins. Attempt identity is
the holder, not an escape from resource exclusion. Binding must precede writable
effects, with late/uncertain launch held through exact reconciliation/cessation.
The numerical policy remains an author-selected profile proposal, not an owner
ruling. No new approval gate is introduced for routine implementation, minimal
recorded schema decisions or continued focused verification.

Operational finding: tokens.py and PROGRESS.md were absent on read. No tests
executed, no implementation acceptance, and no sibling evidence modified.

## 2026-09-26T13:41Z — owner split supersedes monolithic execution

Owner instructions in T275617 at275694 and275705 select this Work as an open
umbrella, with separately executable children and actual authority graph ordering.
They explicitly supersede the earlier monolithic G1 implementation sequence.
Exact scopes/graph operations remain in that canonical instruction; no duplicate
prose dependency graph is created here. Implementer must complete the authorized
coordination, preserve current bytes and transfer exact exclusive ownership,
then release the umbrella to baton.decide open and unaccepted. No child starts
before graph ordering and ownership are established.

Review-2026-09-26T13-41-00Z.md preserves the incomplete candidate and records
source findings for child continuation. tokens.py and PROGRESS.md now exist,
superseding the earlier absence observation; the production connection remains
unimplemented. No software acceptance or completed milestone is claimed.
Owner275660 requires human Git checkpoints for accepted major milestones;
this routine correction/coordination pass is not one. No agent Git mutation.

## 2026-09-26 — reviewer graph preparation authorized explicitly

Owner275757 arrived after this review's initial discussion read. It explicitly
authorized reviewer/planning-route graph preparation. After pass275768, the
still-unclaimed umbrella was rerouted at275771 and claimed at275772 without
taking over another handler. This supersedes the prior requested impl-only
coordination next action. Exactly three child Work were created in planning:
W275774, W275775, W275776. Their scopes and dependencies live in canonical
authority, not a duplicated dossier graph.

Candidate custody transfers to W275774 as unaccepted input: tokens.py hash
f4bfb71fa44c60e4284caec67815fdc4ed87aba03c214cf4e6bd21fef30c6f80 and parent
selector hash1c1490e39cbaf9d732dbb6ca226bdc2fde23c484cc78a1b7cd5531597197ba39.
The parent selector/PROGRESS and review manifests remain historical evidence;
the child creates its own dossier and selector rather than overwriting them.
W275774 exclusively owns further token implementation and necessary minimal
attempts/OCI/serving connections after pinning exact paths in its dossier;
later children obtain those paths only through accepted serial handoff. The
umbrella performs no further product/test execution. Preserve W270664 files.

## Owner coordination ruling — 2026-09-26

Owner instruction: "good, keep an eye on the work, coordinate unless spec needs
adjusting which requires my approval". Prompt is authorized to monitor canonical
Work state and evidence and coordinate ordinary continuation, correction,
ownership and handoffs within the accepted specification and selected scope.
Use actual Baton graph operations for scheduling relationships, under the
appropriate handler authority; prose is not a dependency mechanism.

Any proposed specification adjustment requires explicit owner approval before
changing the specification or implementing the changed behavior. Do not infer
approval from an implementation difficulty, a reviewer suggestion or this
coordination delegation. Preserve independent review, human milestone Git
checkpoints and Slawomir's exclusive Git ownership. Prompt remains non-routable
and cannot impersonate another participant or consume managed readiness.
