# WS-6 design — permanent dossiers, configured roots, and bootstrap

Status: reviewed; M1–M6 ruled, awaiting implementer revision
Date: 2026-08-15
Owner: `baton.reviewer`

## Scope

WS-6 makes repository evidence portable and navigable without making the
filesystem or Git part of Baton authority. It implements the confirmed
permanent-record, binding-authority, closure, reference, root, and external-
template rulings in `FINDING.md`.

It does not archive or move dossiers, hash-pin evidence, inspect Git during an
authority read, reconcile `work/open/`, migrate current finding folders,
expand the TUI into a file manager, or make templates protocol objects.

## 1. Configured root catalog and machine-local resolution

The strict accepted `baton.json` gains a portable root catalog. Root ids reuse
the proven protocol-10 grammar and address form unless K identifies a concrete
v11 conflict:

```text
ROOT_ID:RELATIVE/POSIX/PATH
```

A catalog entry contains stable logical identity/display metadata, never an
absolute checkout path. Root ids are independent of teams and routes. One team
may use several roots; several teams may reference one root.

A separately and explicitly supplied machine-local resolver maps the accepted
root ids to absolute base paths. Its exact application filename/flag belongs
in K's implementation plan. It is not persisted in SQLite, included in an
operation fingerprint, or required for canonical authority commands. Moving a
checkout changes only this local mapping.

Accepted generations may add roots. A used root id is never silently rebound
to a different logical root. A retired root remains readable in history but
cannot be reintroduced with a new meaning. New bindings, binding revisions,
and independent references require a live root. A dossier-relative reference
may still cite an already-existing immutable binding revision on a retired
root; that is historical provenance rather than new root use. Retirement has
no special stranding gate.

## 2. Work binding history

A Work exposes one effective binding and a bounded, paginated immutable
history. Every binding revision stores the complete portable locator and its
authority facts:

```text
Work id
binding revision and expected prior revision
root id
canonical path beneath work/records/YYYY/MM/
optional immutable Git provenance
actor plus resolved Current snapshot
rationale for every post-creation change
authority sequence and timestamp
```

The normalized path is exactly
`work/records/YYYY/MM/<stable-record>`: literal prefix, four-digit year,
two-digit month `01`–`12`, and one safe stable-record component. It is also
POSIX-relative and contained by syntax: no leading slash, backslash, empty
component, `.`/`..`, home expansion, edge whitespace, or escape. Validation
does not compare the date with creation time or stat the path. Artifact paths,
not the binding, address content below the dossier root.

Creation may atomically commit Work, its first discussion/message, and binding
revision 1. The creator may make this initial binding even when routing makes
another endpoint Current. Creation without a dossier remains valid.

After creation, only the live resolved Current handler of open Work may attach
the first binding or append a correction/provenance revision. The mutation
requires expected-prior CAS and a non-empty rationale. Transfer immediately
transfers this authority. Terminal Work refuses every binding mutation. WS-5
operation identities cover all binding mutations and replay the complete
original result.

Ordinary lifecycle never changes a binding. Closing preserves and freezes its
history without moving the dossier or requiring Git provenance. Lightweight
unbound Work closes normally.

## 3. Artifact references

A dossier-relative reference explicitly stores:

```text
bound Work id + immutable binding revision + relative artifact path
```

The Work id is explicit because one discussion may carry multiple `#WORK`
labels. Any existing bound Work may be named; a current discussion label is not
required. References never add labels or workflow edges. Publication selects
and stores the binding revision in the same transaction, so a later locator
correction cannot reinterpret old evidence.

An unbound Work refuses this dossier-relative form because no immutable binding
revision exists. The same asset remains citable through the independent root
form; Baton never invents a placeholder binding.

An independent reference explicitly stores:

```text
root id + repository/root-relative path
```

Both forms use the same root/path vocabulary, are ordered typed evidence
metadata, and round-trip losslessly through JSON and the shared TUI projection.
Neither reads, hashes, copies, ingests, or promises the existence of bytes.

Every public mutation may carry references; WS-6 does not restrict evidence to
selected message verbs. A reference-bearing act and all its result records,
messages where any, reference rows, selected binding revisions, workflow
effects, event, and WS-5 operation record commit whole or not at all.
References are normalized typed operation input, so identity and order
participate in the WS-5 fingerprint. Compound acts that create several
messages/records require explicit placement and may not silently copy, omit,
or infer placement.

## 4. Projection and navigation

Canonical JSON exposes the effective binding directly, a bounded binding-
history preview with a paginated pure read, and exact message references in
authored order. It always displays durable root ids and relative paths.

There is no availability/staleness field. The bounded TUI renders the same
portable facts at selected parity checkpoints; WS-6 adds no file-browser
interaction requirement.

An explicit client navigation action may combine a canonical locator with the
explicit local resolver. Missing mapping/path or host-open failure is a clear
non-mutating client error. It never searches cwd, guesses another root, uses
`work/open/`, or changes a database byte.

## 5. Templates and project bootstrap

Core numbered Markdown instruction patterns live in source `tmpl/` and ship as
separate byte-identical deployed assets in the exact CLI release's sibling
`tmpl/` directory beside `bin/`, `doc/`, and `conf/`. They are never embedded
in the zipapp or loaded through `importlib.resources`. Source bootstrap reads
source `tmpl/`; installed bootstrap reads its exact release's sibling `tmpl/`
and refuses clearly when those product assets are missing. The first standard
is `tmpl/work-basic-1.md`, which instructs an implementer to create a permanent
dossier normally containing `REPORT.md`, `PLAN.md`, and `PROGRESS.md` plus
context-specific evidence.

An explicit bootstrap operation targets one locally resolved root and creates:

```text
ROOT/tmpl/<selected numbered Markdown templates>
ROOT/work/open/
ROOT/work/records/
```

It never creates a particular Work dossier or `open/` symlink and never edits
Baton authority. It copies rather than links to an installation. Identical
existing assets may be reported already present; conflicting bytes, wrong
object type, symlink at a managed path, containment failure, or a target that
changes during the operation refuses without replacement. A newer release
never silently upgrades a project's vendored templates.

Distribution, coordination home, and project roots are three separate
ownership domains. A distribution install (for example `~/opt/baton` or
`/usr/lib/baton`) owns immutable versioned product assets. A coordination home
(for example `~/baton` or `~/.baton`) owns mailbox config/SQLite and the
machine-local root resolver. Project bootstrap targets one resolver-selected
repository root and creates project-owned, editable, Git-managed copies. No
path is inferred from another. `deploy` installs the software distribution;
mailbox `init` creates coordination authority; project `bootstrap` copies
defaults into a project and never writes back to or stays linked to the
distribution.

K's plan must state the filesystem containment and partial-failure model before
this slice begins. That safety model is operational, not Baton authority.

## 6. Required race and retry boundaries

Every committing transaction revalidates current root eligibility, Work/open
state, live Current authority where required, expected binding revision,
locator/reference containment, and the binding revision selected by a dossier
reference.

Required both-order races:

- binding revision versus another revision, Current transfer, Work close, and
  root retirement;
- reference publication versus binding correction, Work close, root
  retirement, and another carrying post;
- exact and conflicting WS-5 retries at each boundary.

Losing attempts leave no reference, binding revision, event, operation record,
or sequence hole unless they are exact replays of a committed operation.

## 7. Two implementation slices

### Slice A — authority and portable projection

Add accepted root catalog projection, binding/reference schema and
transitions, JSON/CLI surfaces, bounded history, TUI parity checkpoints, and
WF-13. Run focused tests and `just test-v11`, then stop for review. Slice A
does not touch filesystem templates, resolver navigation, build/deploy, or
bootstrap.

### Slice B — resolver, template distribution, and bootstrap

Only after Slice A acceptance: add source templates, separate template assets
to candidate/manifests/release layout and generic installer, explicit local
resolution/navigation, contained bootstrap, and WF-14. Verify source versus
temporary-installed-release parity and adversarial filesystem cases, then stop
for review. Production deployment and existing-project migration remain
separate later operations.

## 8. Workflow battery

### WF-13 — portable dossier authority across PushCoin and Drift

Run from source and packaged JSON CLI with selected shared-projection TUI
checkpoints.

1. Start from strict config declaring `pushcoin`, `drift`, and `baton` roots
   without host paths. Create PUSH-1 with initial
   `pushcoin:work/records/.../push-1` binding in the same transaction as Work
   and its first message.
2. Create LANG-42 unbound and route it to Lang Current. Prove requester and
   former handler cannot attach; Current attaches
   `drift:work/records/.../lang-42` as revision 1 with expected prior 0.
3. Publish Push's report with a PUSH-1 dossier-relative reproduction, request
   `@lang.bug`, accept into LANG-42, and add the blocker edge. Lang posts a
   LANG-42-relative proof plus an independent `baton:docs/...` reference.
   Assert authored order and immutable selected binding revisions.
4. Correct LANG-42's locator under CAS. The old proof remains anchored to
   revision 1; a new proof names revision 2. Race same-prior corrections and
   accept one. Transfer Current and prove binding authority transfers.
5. Provide no local resolver and no filesystem paths. Repeat every canonical
   JSON read and TUI checkpoint: locators remain visible and database bytes
   remain unchanged. Only explicit navigation refuses locally.
6. Close LANG-42 satisfying without Git provenance. PUSH-1 unblocks and closes
   independently. Binding history freezes; no close touches `work/open/` or
   manufactures an archive/seal. Create and close one lightweight unbound Work
   without a placeholder binding.
7. Restart at selected checkpoints. Exercise exact/conflicting op-id retry and
   the close/transfer/root-retirement/binding/reference races. Assert one
   coherent history, dense audit, and no partial rows.

### WF-14 — source/package bootstrap and root relocation

1. Bootstrap an empty temporary root through the source CLI. Assert exact
   `tmpl/`, `work/open/`, `work/records/` shape and template bytes.
2. Assemble and install a candidate into a temporary release target, then
   bootstrap another root through that exact installed CLI plus sibling
   `tmpl/`; require template-byte and project-shape equality with source.
3. Repeat against identical assets and prove no rewrites.
4. At every managed target, try conflicting bytes, wrong file/directory type,
   symlinks, traversal, a root outside the configured resolver, and a target
   changed between validation and write. Refuse without overwrite or escape.
5. Relocate a checkout by editing only the local root resolver. Explicit
   navigation finds the same logical binding at the new path while accepted
   config generation, SQLite hash, binding, messages, and audit remain
   unchanged.
6. Present a newer template set and prove bootstrap does not replace the
   project's vendored copy; adoption stays an explicit repository change.

## 9. Acceptance evidence

- Focused config/schema/transition/projection/CLI/TUI parity tests.
- WF-13 and WF-14 from source and packaged artifacts.
- Restart, fault injection, both-order races, and WS-5 retry.
- Canonical-read database hash purity without resolver/checkouts.
- Source/temporary-installed-release template byte and bootstrap-shape parity;
  a copy-isolated zipapp without sibling assets refuses bootstrap.
- Break-sweeps for Current authority, CAS, binding-revision anchoring, root
  retirement, filesystem-probe contamination, resolver leakage into authority,
  overwrite/symlink containment, and silent template upgrade.
- `git diff --check`, `just test-v11`, and the applicable full candidate gate.

K must review this design against the current strict config, schema, public
CLI/projection, and packaging surfaces before implementation. A material
product choice returns to Slawomir; this document does not release code.

All WS-6 implementation and trials use a separate v11 config/database/runtime
beside the live deployed v10 coordination authority. No workflow, test drive,
bootstrap, or fault injection may touch or stop v10; cutover is later work.

Current project-root mappings normally point under `~/src/*`. The coordination
home may live under `~/src/`, `~/baton`, or another explicit path and may be
Git-managed externally. WS-6 neither forbids that nor implements SQLite backup
or Git integration; a valid authority backup requires a separately defined
consistent snapshot procedure. Exact distribution release directories remain
immutable regardless of project/coordination Git state.

## 10. Implementer-review disposition

K's contradiction review is preserved as
`implementation-response-2026-08-15T17-09-14Z-4aa5527c7a582d33bda2c644be5529f4.md`.
Slawomir ruled M1–M6 afterward:

- M1: every mutation may carry references; no verb-limited surface.
- M2: any existing bound Work may be cited without a discussion label.
- M3: unbound Work refuses only dossier-relative citation; independent root
  citation remains available.
- M4: bindings enforce exact `work/records/YYYY/MM/<stable-record>` shape.
- M5: historical binding citations survive root retirement; new bindings,
  revisions, and independent refs require a live never-reused root.
- M6: templates are separate deployed sibling assets, never zipapp resources.

K must incorporate these rulings into a revised two-slice plan and return it
for review. No implementation is released by this disposition.
