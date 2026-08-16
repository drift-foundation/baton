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
