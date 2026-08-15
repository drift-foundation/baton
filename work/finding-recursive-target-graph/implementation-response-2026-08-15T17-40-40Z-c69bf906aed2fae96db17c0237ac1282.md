# WS-6 design — implementer contradiction review

Author: `baton.implementer`
Date: 2026-08-15
Responding to: `5cad530f8a6efb6f7b69349548ba7636` (review only)
Reviewed against: strict config (`config.py` refuses unknown fields at
every level), schema v12, the WS-5 operation/fingerprint machinery, the
public CLI/JSON/projection surfaces, the workflow driver and packaged
archive, and the current build tooling. No source, schema, test, or
PROGRESS change made; this document is the only artifact.

## 1. Contradictions and missing product rulings

No hard contradiction with the pinned rulings or the implemented
surfaces was found. The v10 `ROOT_ID:RELATIVE/POSIX/PATH` address form
has no v11 conflict: the colon separator collides with no v11 grammar
(work/discussion ids use `-`, endpoints use `.`), and the reference
vocabulary matches the v10 `text/vnd.baton.references` lines this
repository already exchanges. Findings that need a ruling or an
explicit confirmation before Slice A:

- **M1 — reference-bearing surfaces.** "Every public message-authoring
  surface" would put `--ref` on say, create, respond, accept, and the
  revise rationale, changing every one of their WS-5 typed-input
  fingerprints. RECOMMEND: Slice A limits reference authoring to `say`
  and `create` (the surfaces WF-13 exercises); respond/accept bodies
  may cite evidence in prose and gain `--ref` in a later slice if
  wanted. Smaller honest surface, no fingerprint churn on the
  obligation family.
- **M2 — dossier-reference target scope.** The design stores "bound
  Work id + binding revision + path" but does not say which Works may
  be named. RECOMMEND: the referenced bound Work must currently carry
  a `#WORK` label on the discussion (the D9 discipline: the discussion
  carries its operating context). WF-13 step 3 already conforms —
  LANG-42 is labelled onto Push's discussion by the acceptance before
  Lang anchors a LANG-42-relative proof there. Cross-dossier evidence
  outside the labelled context uses the independent form.
- **M3 — reference to an UNBOUND Work.** Revision selection is
  impossible, so it must refuse ("no binding to anchor"); stating it
  avoids an implementation-invented rule. Mechanical confirmation.
- **M4 — binding-path prefix enforcement.** The permanent-record
  ruling fixes `work/records/...`; the validation-boundary ruling
  limits commit-time checks to protocol facts and containment syntax.
  RECOMMEND: bindings require the literal `work/records/` prefix plus
  full containment syntax, but Baton does NOT validate the YYYY/MM
  numerals or depth — those are repository convention, and pinning
  them would make Baton police filesystem shape it never reads.
- **M5 — corrections and retired roots.** "A retired root refuses new
  bindings/references": confirm that EVERY new binding revision —
  first attach and correction alike — requires a live root, while
  committed history on a retired root stays valid and readable. A Work
  bound to a retired root corrects by naming a live root. No stranding
  gate is needed at retirement (existing bindings remain valid protocol
  state by the open-record ruling). RECOMMEND as stated.
- **M6 — Slice B build-tooling boundary.** Templates ship "in each
  exact versioned CLI product release" and WF-14 requires packaged
  bootstrap byte-parity, so Slice B must touch `tools/build_zipapp.py`
  (embed `tmpl/` in the archive, read via `importlib.resources`) and
  the release layout tooling. Confirm this bounded build change is
  inside Slice B's release rather than the held deployment work.

## 2. Test-story implementability through the public surfaces

WF-13 is implementable as written once Slice A adds: the config root
catalog, the binding transitions/verbs, `--ref` on say/create, and the
binding/reference projections. Notes:

- Step 1's strict config: `config.py` refuses unknown fields at every
  level, so the root catalog is a real (mechanical) schema extension —
  allowed-field sets, validation, projection, and the generation diff
  summary all change together; the workflow driver's `document()`
  builder gains a `roots` parameter.
- Step 4's same-prior correction race and step 7's retry/race matrix
  map directly onto the existing `_interleave`/spawn and WS-5
  machinery; nothing needs a private surface.
- Step 5 ("no resolver, no filesystem") holds by construction in
  Slice A since no resolver exists yet; the canonical-read purity hash
  is the existing pattern.
- WF-14 is implementable in Slice B given a `bootstrap` verb, the
  explicit resolver input (below), source `tmpl/`, and archive asset
  embedding. Step 5's relocation assertion (SQLite hash unchanged) is
  the existing purity pattern. One addition to WF-14 step 4: include a
  resolver mapping whose base path itself does not exist — refusal
  must name the missing base, not invent it.

## 3. Corrected two-slice plan (separate review stops)

**Slice A — portable authority (schema v13).**
1. Config: top-level `roots` catalog (grammar in §4), strict-field
   validation, projection into a `roots` table (handle, display,
   removed), add/retire rules with never-reuse, generation diff
   entries; wfdriver `document(roots=...)`.
2. Schema: `bindings` (work FK, revision UNIQUE per work, prior, root,
   path, optional git provenance, actor, rationale nullable only for
   revision 1 at creation, seq, ts) and `message_references`
   (message_seq, ordinal, kind dossier|independent, work FK nullable,
   binding_revision, root, path) — both append-only.
3. Transitions: `create_work(..., binding_root=, binding_path=)`
   committing revision 1 atomically; `bind_work` (attach/correct:
   Current-only in-lock, expected-prior CAS, non-empty rationale, live
   root, containment, terminal refusal); `--ref` parsing on say/create
   (M1) with in-lock revalidation of label context (M2), bound state
   (M3), root liveness, and the selected effective binding revision.
   WS-5 op-ids on all of it; normalized ref lists fingerprint per R83.
4. Projections: detail gains effective `binding` + bounded
   `bindings` preview (count/truncated/cursor, R75 pattern) + paged
   `bindings WORK` read; thread messages gain ordered `references`;
   TUI parity checkpoint renders root:path facts.
5. WF-13 source+packaged; focused matrix: authority/CAS/containment
   refusals, both-order races (binding vs binding/transfer/close/
   retirement; reference vs correction/close/retirement/post), crash
   injection through the reference-bearing post and the binding
   attach, restart, WS-5 exact/conflicting retries, purity hashes.
   Break-sweeps: Current gate, CAS, revision anchoring, root
   retirement, prefix/containment, and a filesystem-probe
   contamination sweep (insert an os.stat into the commit path — the
   purity/no-probe regression must bite).
   Stop for review.

**Slice B — resolver, templates, bootstrap.**
1. Source `tmpl/work-basic-1.md`; zipapp/release embedding with
   byte-parity assertions.
2. Explicit resolver input (§4) + a read-only `resolve` verb mapping a
   canonical locator to an absolute path (prints; never opens, never
   mutates); refusals for unknown root/missing mapping.
3. `bootstrap` verb with the containment/partial-failure model (§4);
   WF-14 source+packaged; sweeps: overwrite/symlink containment,
   silent template upgrade, resolver leakage into authority (assert no
   resolver value ever reaches SQLite or a fingerprint).
   Stop for review. Deployment/migration stay held.

## 4. Proposed exact mechanics (delegated points)

- **Root catalog shape.** In `baton.json`:
  `"roots": {"pushcoin": {"display": "PushCoin monorepo"}}` — ids
  follow the existing handle grammar (`validate_handle`), the same
  discipline as team handles; entries are strict objects (display
  required, nothing else in Slice A). Retirement = the id absent from
  the next accepted generation, projected as `removed=1`; reintroduction
  refuses ("never silently reused").
- **Address form.** `ROOT_ID:RELATIVE/POSIX/PATH` retained verbatim
  from v10 for CLI input (`--ref pushcoin:work/records/...`), stored
  decomposed as (root, path); JSON always emits the decomposed object.
- **Local resolver.** An explicit per-invocation flag,
  `--roots-file PATH`, naming a JSON document
  `{"roots": {"pushcoin": "/abs/checkout"}}`. No default filename
  search, no cwd walk, no environment variable, never persisted,
  never fingerprinted, accepted ONLY by `resolve` and `bootstrap`
  (canonical verbs refuse it, the `--op-id`-on-reads pattern).
- **Bootstrap containment and partial failure.** Two phases. Phase 1
  (validate, no writes): realpath the resolver base and require it to
  exist and be a directory; compute every managed target; refuse if
  any target's parent chain contains a symlink (O_NOFOLLOW dir-fd
  walk), any existing target has conflicting bytes or wrong type, or
  any path escapes the base by containment syntax or realpath. Phase 2
  (create): directories via mkdir (EEXIST tolerated for identical
  intent), files via O_CREAT|O_EXCL through the dir-fd chain; byte-
  identical existing files reported "already present". On any phase-2
  failure (including a target changed since phase 1, caught by O_EXCL/
  O_NOFOLLOW): stop immediately, report exactly what was created, and
  never delete, overwrite, or replace anything — a re-run against the
  partial result is idempotent because identical assets are
  "already present" and conflicts refuse. Bootstrap never touches any
  path outside the resolved base and never opens the Baton authority.

Stopping here; no implementation begun. Material choices M1–M6 return
for ruling; everything else above is mechanical and recommended with
rationale in place.


# Corrected two-slice plan after the M1–M6 rulings

Date: 2026-08-15, responding to `74e23e047358c0a19afafa4bc873bf66`.
The rulings supersede my M1/M2/M4/M6 recommendations; this section is
the corrected concrete plan plus the only remaining questions found.

## Remaining questions (only two; recommendations attached)

- **Q1 — configuration-family references.** M1 says EVERY public
  mutation may carry references. `init`/`regen` are configuration
  acts: their events live in the same audit stream, so references are
  mechanically possible, but citing work evidence on a topology
  acceptance has no story. RECOMMEND: the configuration family
  refuses `--ref` in Slice A ("a configuration acceptance carries no
  work evidence") — one refusal, reversible later without schema
  change. If "every public mutation" is meant literally, the plan
  below works unchanged with the refusal dropped.
- **Q2 — references on a protected no-op.** A losing `mark-seen`
  commits NO domain event (WS-5 R76), so a reference has no act to
  commit with. RECOMMEND: a reference-bearing mark that turns out to
  be a no-op refuses whole ("nothing was committed to carry the
  evidence") rather than silently dropping the references — the
  explicit-placement discipline applied to the degenerate case.

## Slice A — portable authority (schema v13); separate review stop

1. **Root catalog.** `baton.json` top-level `"roots"`: strict objects
   (`display` required). Root ids use the v10 grammar exactly:
   1–64 bytes, dotted lowercase/underscore segments
   (`[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)*`), NOT `validate_handle` —
   a new `validate_root_id`. Projection to a `roots` table (root,
   display, removed); generations may add roots; a used id is never
   rebound or reintroduced; retirement = absence from the next
   accepted generation, projected `removed=1`; diff summary entries.
   `wfdriver.document(roots=...)`.
2. **Schema.** `bindings(work FK, revision UNIQUE per work, prior,
   root, path, git_provenance NULL, actor, rationale, seq, ts)` with
   the M4 shape enforced at validation: literal `work/records/` prefix,
   4-digit year, month `01`–`12`, exactly ONE safe stable-record
   component, full containment syntax, no probing.
   `act_references(seq REFERENCES events, ordinal, kind
   dossier|independent, work FK NULL, binding_revision NULL, root,
   path)` — ordered typed rows keyed by the ACT's event, so every
   mutation family shares one mechanism and messages simply join
   through their seq.
3. **Reference grammar and placement (M1).** One repeatable `--ref`
   flag, discriminated by the left-of-colon token: the v10 root
   grammar (lowercase/underscore/dots) cannot collide with a Work id
   (`{uuid8}-W{n}`), so `pushcoin:docs/x.md` is independent and
   `fefefefe-W3:repro/run.sh` is dossier-relative. Order of flags is
   the stored ordinal order. Dossier form resolves and stores the
   target's EFFECTIVE binding revision in the committing transaction;
   unbound target refuses (M3); no label requirement and no label,
   participation, dependency, or workflow effect (M2). Dossier
   citation of an existing immutable revision stays valid after root
   retirement; independent references and every NEW binding revision
   require a live root (M5). Compound placement: plain `--ref`
   attaches to the PRIMARY act event; `accept` — the one mutation with
   two caller-meaningful products — additionally takes `--answer-ref`
   for the emitted answer message, and a bare `--ref`/`--answer-ref`
   split makes placement explicit with no copy/drop/guess. References
   join the WS-5 normalized typed-input fingerprint as the ordered
   list of decomposed tuples.
4. **Transitions.** `create_work(..., binding=ROOT:PATH?)` committing
   revision 1 atomically (creator authority per ruling); `bind_work`
   attach/correct (live Current in-lock, expected-prior CAS, non-empty
   rationale, live root, M4 shape, terminal refusal); `--ref` plumbed
   through every mutation verb per M1 with in-lock revalidation (root
   liveness for independent/new-binding, target bound state and
   effective revision for dossier form); WS-5 op-ids everywhere.
5. **Projections.** `detail`: effective `binding` direct + bounded
   history preview (count/truncated/cursor) + paged `bindings WORK`
   read (R75 pattern). `thread` messages and `events` rows expose
   ordered `references`. TUI parity checkpoint renders root:path
   facts. All reads pure, hash-swept.
6. **WF-13 (amended to the rulings).** As drafted, with: step 3's
   proof cites LANG-42 from a discussion where it is NOT labelled
   (M2); a root-retirement leg — retire a scratch root mid-story,
   prove an old dossier citation still publishes by revision, an
   independent reference to the retired root refuses, and the bound
   Work corrects to a live root (M5); and a per-family reference
   sweep (one `--ref`-bearing act per mutation family, M1).
7. **Focused matrix and sweeps.** Authority/CAS/M4-shape/containment
   refusals; both-order races (binding vs binding/transfer/close/
   retirement; reference vs correction/close/retirement/post); crash
   injection through a reference-bearing compound accept; restart;
   WS-5 exact/conflicting retries incl. fingerprint sensitivity to
   reference order; purity hashes. Break-sweeps: Current gate, CAS,
   revision anchoring, retired-root acceptance, M4 shape, placement
   silently guessed, filesystem-probe contamination (an os.stat in
   the commit path must turn a regression red).
   Run focused + `just test-v11`; stop for review.

## Slice B — distribution assets, resolver, bootstrap; separate stop

Per M6, templates are exact-release ASSETS, never zipapp-embedded and
never importlib resources.

1. **Source templates.** Top-level `tmpl/work-basic-1.md` (numbered
   editions; a changed instruction is a new file).
2. **Release layout.** Extend the existing candidate/manifest/release
   tooling (`tools/build_release.py`, DISTRIBUTION manifests) so each
   exact CLI product release carries sibling `tmpl/` beside
   `bin/ doc/ conf/`, with manifest-listed digests; generic installer
   support copies it like the other siblings. Packaged-mode tests
   build a TEMPORARY exact-release layout under the test tmp dir and
   assert byte parity with source `tmpl/` — the operational gate:
   nothing reads, writes, links, or stops the live v10 install or
   mailbox, and the trial CLI runs with its own config/database/
   process set throughout.
3. **Resolver.** Explicit `--roots-file PATH` (JSON
   `{"roots": {"pushcoin": "/abs/base"}}`), accepted only by
   `resolve` and `bootstrap`; no default search, no env var, never
   persisted, never fingerprinted; canonical verbs refuse it.
   `resolve` maps a canonical locator to an absolute path and prints
   it — read-only, no open, no mutation, refusals for unknown root /
   missing mapping / missing base.
4. **Bootstrap.** Copies the selected numbered templates from THIS
   release's `tmpl/` (source mode: the source tree's `tmpl/`;
   packaged mode: the temporary release layout's sibling `tmpl/` —
   same bytes proven, satisfying temporary-target parity) into the
   resolved project root, creating `tmpl/`, `work/open/`,
   `work/records/`; two-phase containment/partial-failure model as
   proposed in §4 above (validate-all then O_EXCL/dir-fd create;
   identical → "already present"; conflict/symlink/type/traversal/
   changed-target → refuse; never delete, overwrite, or write back to
   the distribution; idempotent re-run).
5. **WF-14 (amended).** As drafted plus: the missing-resolver-base
   refusal; the distribution-immutability proof (bootstrap never
   writes into the release layout it copied from); and the
   newer-release non-upgrade case against the temporary layouts.
6. Sweeps: overwrite/symlink containment, silent template upgrade,
   resolver leakage into authority or fingerprints, distribution
   write-back. Run focused + `just test-v11`; stop for review.
   Production `~/baton` deploy, mailbox creation, migration, and
   cutover remain held.

No implementation begun; awaiting the Slice A release after this plan
is reviewed.


## Amendment: the three-domain location model (2026-08-15)

Incorporating `f00c4555ab7b878f2918b675a18bfc51`, which crossed the
corrected plan in flight. WS-6 operates over THREE independent
location domains, and no path is ever inferred from another:

1. **Distribution root** (e.g. `~/opt/baton`, `/usr/lib/baton`):
   immutable exact product releases — sibling `bin/ doc/ conf/ tmpl/`
   assets. Written only by distribution deploy/install; bootstrap
   copies FROM here and never writes back (the Slice B
   distribution-immutability sweep).
2. **Coordination home / instance root** (e.g. `~/baton`, `~/.baton`):
   mailbox config, the SQLite authority, instance-owned state, and the
   MACHINE-LOCAL ROOTS RESOLVER. The resolver's conventional home is
   this domain, but per the pinned addressing ruling it remains
   EXPLICITLY supplied to the verbs that may use it (`resolve`,
   `bootstrap`) — its location in domain 2 is convention, never a
   default search path, and it never enters authority state or
   fingerprints.
3. **Project roots**: resolver-selected repositories owning the
   editable vendored `tmpl/`, `work/open/`, `work/records/`, and the
   dossiers themselves.

Three distinct operations, one per domain: distribution deploy/install
(held), mailbox/instance init (the existing `init`, domain 2), and
project bootstrap (Slice B, domain 3). Slice B's WF-14 gains the
cross-domain proofs: bootstrap writes only into the resolved project
root — never the distribution it copied from, never the coordination
home — and the operational gate keeps every test's three domains
inside the test's own temporary directories, far from the live v10
install and mailbox. Slice A is unaffected: it touches only the
authority (domain 2 state) and the portable address vocabulary.


## Amendment 2: placement boundary (2026-08-15)

Incorporating `40a598f96571544136df76bf03bf6e75`:

- Project roots normally resolve under `~/src/*`; the coordination
  home may live under `~/src/`, `~/baton`, or another explicit path
  and may itself be Git-managed EXTERNALLY for recovery/provenance.
  Neither convention becomes a default: every base still arrives
  through the explicit resolver, and WS-6 code never assumes `~/src`.
- WS-6 adds NO Git authority and NO SQLite-backup mechanism. A raw
  live DB/WAL copy is not a proven recovery snapshot; a consistent
  stopped/checkpointed or backup-API procedure is separate later work.
  Consequence for the plan: Slice A/B tests continue to use their
  existing checkpoint-then-hash discipline as a TEST oracle only, and
  nothing in WS-6 presents any copy mechanism as a recovery feature.
- The distribution location is stable and each exact installed version
  directory is immutable; project/coordination Git never modifies
  distribution bytes. This strengthens the Slice B sweeps already
  planned: distribution write-back and any mutation of an installed
  version directory are refusal/red-sweep material.


## Amendment 3: from-scratch coordination-home onboarding (planning only)

Incorporating `27facb53002b458e0475a0d3b1b6d09c` (Q1/Q2 resolved as
ruled: references on every mutation literally, incl. generation-one
activation with independent refs against the proposed catalog; a
reference-bearing protected no-op refuses whole).

1. **Names.** The desired UX owns the word `init`: `baton init DIR`
   becomes the coordination-home SCAFFOLD (writes editable templates,
   never a database). The existing generation-one operation — which
   consumes an edited, validated config and atomically creates the
   unique SQLite authority — is renamed `baton activate` (it
   ACTIVATES the proposed generation under a named participant; regen
   remains the N+1 acceptance). `check` is the pure validator. No
   alias for the old `init` meaning survives (v11 is unshipped;
   wfdriver/fixtures/tests migrate mechanically in the implementing
   slice). Three verbs, three meanings: scaffold / check / activate —
   none of them project `bootstrap`, which stays the domain-3 vendor
   operation.
2. **Scaffold tree and the pure `check`.** `init DIR` creates, under
   the two-phase O_EXCL containment model already specified:

       DIR/baton.json    — a commented generation-1 template with a
                           freshly generated authority_uuid, skeleton
                           instance/teams/roots stanzas for the
                           operator to edit
       DIR/roots.json    — the machine-local resolver template
                           (domain-2-owned, never authority state)

   No SQLite file, no mailbox state, no canned or placeholder-bound
   database ever ships or is copied — activation is the ONLY database
   creator. Identical existing files report "already present";
   conflicting bytes/type/symlink/containment refuse without
   replacement. `baton check DIR|--config PATH` runs the SAME strict
   validation the acceptance path uses (plus resolver-file syntax when
   present), prints a JSON summary (generation, instance identity,
   teams, roots) or the JSON exit-one refusal, and writes no byte —
   hash-provable purity, usable repeatedly while editing.
3. **Activation.** `activate` keeps today's init_from_config
   semantics unchanged: strict validation of the EDITED document,
   required `--participant` validated against the proposed
   generation-1 document, optional `--op-id` (WS-5 protected,
   exact/conflicting lookup against an existing authority behind the
   current-generation identity gate), the atomic create-if-absent
   link commit point, and the concurrent-activation race where
   exactly one initializer wins and losers refuse structurally with
   the winner's bytes untouched.
4. **WF-15 — empty directory to two working members** (source +
   packaged, temporary domains only): `mkdir` → `init .` (scaffold
   shape and byte parity across modes) → operator edit (the test
   writes teams/roots) → `check .` repeatedly, pure by hash, refusing
   the half-edited document with the exact strict-field error →
   `activate --participant … --op-id …` → two configured members run
   `home`/`say`/`thread` against the accepted generation → partial
   filesystem cases: scaffold into a directory with a conflicting
   `baton.json` (refuse, no replacement), identical re-scaffold
   ("already present", idempotent), missing/read-only target
   (refusal names the base) → concurrent `activate` race (two spawned,
   one winner, structured loser, no partial database) → protected
   activation retry replays the committed result. Nothing touches the
   live v10 domains.
5. **Slice placement.** All of it — the `init` rename-and-scaffold,
   `check`, the `activate` rename, and WF-15 — lands in SLICE B,
   beside the resolver and project bootstrap, under the same
   filesystem-safety review stop: these are the filesystem-writing
   domain-2 operations, and Slice A stays purely
   authority/addressing with its own unchanged stop. The Slice B stop
   is therefore strengthened, not weakened: one review covers every
   new filesystem writer (scaffold, bootstrap) plus the renamed
   activation surface, with the shared containment, idempotence,
   write-back, and v10-isolation sweeps.

Planning only; no implementation until this boundary is confirmed and
Slice A is explicitly released.


## Amendment 4: R86/R87 onboarding corrections (planning only)

Incorporating `9cedfd41387ac2b609e8b0d9c26f0f31`.

- **R86 — strict JSON stays strict.** The scaffold writes THREE files:
  a VALID strict-JSON `baton.json` carrying a freshly generated
  authority UUID and an intentionally incomplete topology (empty
  `teams`, empty `roots`), a valid strict-JSON `roots.json` resolver
  template (empty mapping), and a separate `BATON-SETUP.md` Markdown
  instruction file explaining exactly what to fill in and in what
  order (edit → check → activate). No comments, no ignored
  instruction fields, no `.example` renaming step. `check` then
  refuses the pristine scaffold with the REAL semantic message (an
  authority needs at least one team/participant), which WF-15 asserts
  verbatim — the scaffold never teaches an input form that `check` or
  `activate` would refuse lexically.
- **R87 — `init DIR` is one-shot.** Because every scaffold generates a
  fresh UUID, no second invocation can honestly reproduce the first,
  so there is no recognition rule to get wrong: `init` refuses
  whenever ANY managed file (`baton.json`, `roots.json`,
  `BATON-SETUP.md`) already exists at the target, naming the file; it
  never compares, overwrites, or adopts an existing file as "its own".
  The earlier "identical re-scaffold is idempotent" case is WITHDRAWN
  from WF-15 and replaced by the one-shot refusal case. The
  idempotence property remains ONLY where it is honest: domain-3
  `bootstrap`, whose template bytes are fixed release assets with no
  generated content, keeps its identical-bytes "already present" rule.
- The public `init`/`check`/`activate` vocabulary is explicitly
  Slawomir's ruling to make; this plan proposes it and binds nothing.

Planning only; Slice A and every filesystem change remain held.


## Amendment 5: final onboarding shape (supersedes Amendments 3–4 where they differ)

Incorporating the ruling in `f9698dc913b916c3dc7287a004ce4eef`: the
public flow is exactly two steps, and there is NO `check` command —
one validation surface, not two.

    baton init .
    # edit the generated coordination configuration
    baton activate . --participant team.member

1. **`init DIR` — scaffold only, one-shot (R87).** Writes three
   files under the two-phase O_EXCL containment model and creates no
   SQLite authority:
   - `baton.json` — VALID strict JSON (R86): a freshly generated
     authority UUID and an intentionally incomplete topology (empty
     `teams`, empty `roots`); no comments, no ignored instruction
     fields;
   - `roots.json` — valid strict JSON resolver template (empty
     mapping); non-authoritative, domain-2-owned;
   - `BATON-SETUP.md` — the separate Markdown instructions (what to
     fill, then `activate`).
   Because the UUID is generated, no re-run can honestly reproduce
   the first scaffold: `init` REFUSES whenever any managed file
   already exists, naming it — it never compares, overwrites, or
   adopts an operator-edited config. Idempotence lives only in
   domain-3 `bootstrap`, whose bytes are fixed release assets.
2. **`activate DIR --participant team.member [--op-id …]` — the ONE
   authoritative validation and creation.** Runs the strict
   generation-one validation (including the proposed participant)
   and only after it succeeds atomically creates/binds the unique
   database via the existing create-if-absent link commit. Any
   validation failure emits the structured JSON refusal and leaves
   NO database and NO accepted state — the operator edits and
   retries; the pristine scaffold's refusal is the real semantic
   message (an authority needs at least one team/participant). WS-5
   op-id protection, the existing-authority identity-gated
   exact/conflicting lookup, and the one-winner concurrent race all
   carry over unchanged.
3. **Resolver validation timing.** `roots.json` is validated only
   when an explicit resolver-consuming operation (`resolve`,
   `bootstrap`) uses it; an incomplete or absent local mapping never
   blocks or invalidates authority activation.
4. **WF-15 (revised, no `check`).** Empty dir → `init .` (shape and
   byte-form parity across modes; managed-file one-shot refusal on
   re-run) → `activate` against the PRISTINE scaffold refuses with
   the semantic topology message and provably leaves no database →
   the test edits teams/roots → a half-edited document refuses with
   the exact strict-field error, again leaving nothing → `activate
   --participant … --op-id …` succeeds atomically → protected
   re-activation replays → two configured members run
   `home`/`say`/`thread` → concurrent-activation race (one winner,
   structured losers, winner's bytes untouched) → partial-filesystem
   refusals (conflicting file, missing/read-only target naming the
   base). All domains temporary; live v10 untouched.
5. Slice placement unchanged: all of it in Slice B under the single
   strengthened filesystem-safety stop; Slice A remains pure
   authority/addressing.

Planning only; awaiting confirmation and the Slice A release.
