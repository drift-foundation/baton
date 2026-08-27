# Repo Agent Rules

## Drift context (required)

This repository is for a PushCoin application. It will consists of a webapp, and a few UIs. The backend will be written in Drift programming language. Agents must understand core Drift semantics before making changes.

- Drift is a systems language with explicit ownership and moves.
- Borrowing/reference rules are enforced by the compiler.
- Resource lifetime is deterministic (RAII-style destruction), no GC assumptions.
- Concurrency is designed around Drift runtime primitives and virtual-thread style scheduling.

Primary docs (read first):

- Docs root: `https://github.com/drift-foundation/lang-toolchain/tree/main/docs`
- Language spec: `https://github.com/drift-foundation/lang-toolchain/tree/main/docs/design/drift-lang-spec.md`
- Stdlib spec: `https://github.com/drift-foundation/lang-toolchain/tree/main/docs/design/drift-stdlib-spec.md`
- Concurrency design: `https://github.com/drift-foundation/lang-toolchain/tree/main/docs/design/drift-concurrency.md`
- Tooling/packages: `https://github.com/drift-foundation/lang-toolchain/tree/main/docs/design/drift-tooling-and-packages.md`
- Effective guide: `https://github.com/drift-foundation/lang-toolchain/tree/main/docs/effective-drift.md`

Drift dependency policy:

- This repo tracks `drift-foundation/lang-toolchain` `main`.
- Compatibility target is current `main`, not historical snapshots.
- If a `main` change breaks this repo, treat it as immediate integration work.
- If breakage appears to be a Drift defect, follow the defect policy below and pin a minimal regression.

## Announcements

- Read and publish cross-team announcements from/to `/tmp/drift-announce/<iso-utc-datetime>-<repo>-release-notes.md`.

## Git usage (strict)

- Use `git` **only** for reviewing history or diffing (e.g. `git diff`, `git log`, `git show`, `git blame`).
- Agents never stage or unstage changes (`git add`, `git restore --staged`, and equivalents).
- Agents never perform mutating Git operations, including `git commit`, `merge`, `rebase`, `cherry-pick`, `reset`, `checkout`/`switch`, `stash`, branch/tag operations, or pushes.
- **Do not** wrap long lines (calls with many arguments, long expressions) for readability; avoid indentation churn, especially if code is deeply nested.
- **Do not** edit existing tests without clear confirmation it is OK. Do not bend tests around defects.

## Defect policy (strict)

- If behavior indicates a core defect (protocol parsing, state machine, concurrency, memory/lifetime, I/O correctness, or runtime integration), classify it immediately as `CORE_BUG`.
- Do not patch user-facing API code to avoid triggering a suspected `CORE_BUG` unless explicitly approved as a temporary workaround.

### Regression-first requirement (mandatory)

For every suspected `CORE_BUG`, do this in order:

1. Add a minimal failing regression test (prefer e2e/integration when relevant, unit otherwise).
2. Confirm it fails on current behavior.
3. Fix the root cause.
4. Confirm regression passes.
5. Only then consider refactor/cleanup.

### No semantic masking

Forbidden without explicit approval:

- Rewriting control flow primarily to bypass correctness defects.
- Rewriting ownership/lifetime patterns primarily to hide memory/concurrency defects.
- Any source change whose main purpose is to avoid fixing root cause.

### Stop-and-confirm gate

On first detection of a likely `CORE_BUG`, stop broader implementation changes and notify with:

- minimal repro
- failing test path
- suspected subsystem

Then continue with root-cause fix by default; ask before any temporary workaround.

### Temporary workaround protocol (opt-in only)

If user explicitly requests a temporary workaround:

- Keep it minimal and localized.
- Add a `progress.md` (or `TODO.md`) note referencing regression test and bug label.
- Do not mark complete until root-cause fix is landed or explicitly deferred.

### Completion criteria

A `CORE_BUG` is not done unless both are present:

- pinned regression test
- root-cause fix

Workaround-only changes must be reported as partial, not final resolution.

## Baton v11 coordination

This repository coordinates through the shared Baton protocol-11 authority.
Protocol 10's directed messages, notices, `send`/`reply`, message claims,
`claim --message-id`, and `see` are retired and are not fallbacks.

Before publishing or consuming a Baton handoff, read
`baton:docs/AGENTS-MAILBOX-PROTO.md` in full. Before every first assignment
also read `baton:docs/EFFECTIVE-BATON.md` and the exact dossier bound to the
Work. The launcher supplies the canonical v11 executable and explicit config;
never infer either, omit `--config`, or hard-code a host deployment path in
repository policy.

The `pc.code` ACP launcher supplies those values as `BATON_BIN` and
`BATON_CONFIG`, together with `BATON_PARTICIPANT=pc.code` and
`BATON_ROLE=impl`. A fresh implementation turn reads and validates those four
environment values before its first Baton operation. Missing or mismatched
values are a deployment blocker: do not search the repository or deployment
directories for a plausible executable or config.

Pushcoin's coordination identities are:

- `pc.prompt`, role `prompt`: Slawomir's human-attached interactive
  copilot. It is not a routable Handler and has no readiness consumer.
- `pc.plan`, role `rview`: managed research, planning, coordination, and
  independent review.
- `pc.code`, role `impl`: primary implementation and implementation-owned
  tests.
- `pc.slaw`, role `approv`: human approval and narrow abandoned-claim
  recovery.
- `pc.tuner`, role `tuner`: documentation, recipes, packaging, deployment
  UX, templates, and explicitly assigned final polish.

Resolve role-only instructions to those identities and never substitute an
identity from another team. Every invocation names the exact participant,
for example:

```text
<launcher-supplied-baton> --config <launcher-supplied-config> --participant pc.plan detail work=W…
<launcher-supplied-baton> --config <launcher-supplied-config> --participant pc.plan claim work=W…
<launcher-supplied-baton> --config <launcher-supplied-config> --participant pc.plan say thread=T… body="…"
<launcher-supplied-baton> --config <launcher-supplied-config> --participant pc.plan pass work=W… to=pc.impl comment="…"
```

Canonical Baton operations are one standalone direct execution each. In
particular, issue `claim work=W…` alone and do not combine it with reads,
pipes, shell control syntax, or another mutation. A readiness result is
advisory: `wait` is read-only and claims nothing, while the atomic `claim`
is the final authority. No participant starts routed execution before its
claim succeeds. Act on every wake and finish the episode by passing or closing
the Work rather than leaving it held.

Threads and Messages carry discussion; Work Events carry workflow acts.
`pass` is the claimant's threadless handoff and releases the claim
atomically. A directed request uses `say ... request=pc.KIND on=W…` and
blocks by default unless `wait=false` is explicitly honest. Never mutate or
read the SQLite authority directly; use only the canonical CLI views and
operations.

## Confirmed decisions are pinned before implementation

Baton discussion is coordination evidence, not a durable specification.
Before implementing a confirmed product, UX, protocol, or operational
decision, record it chronologically in the owning dossier's `FINDING.md` and
reflect its current actionable state in `PLAN.md`. Revalidate it against the
current tree at implementation start. If a later ruling changes it, append an
explicit dated supersession and update the plan; never erase or silently
rewrite the earlier decision.

Implementation and review handoffs reference the exact finding, plan,
implementer progress, and newest review paths discussed. After context loss,
resume from those records rather than memory or a subject line.

## Permanent finding dossiers

New finding dossiers are permanent canonical records at
`work/records/YYYY/MM/finding-stable-name/`:

```text
work/
  open/
    finding-friendly-name -> ../records/YYYY/MM/finding-stable-name
  records/
    YYYY/
      MM/
        finding-stable-name/
```

- Create no new `work/finding-*` dossier. Remaining folders in that layout
  are legacy items awaiting deliberate cleanup.
- Choose the year/month at creation. The canonical `work/records/...` path
  never moves, is never archived or deleted by lifecycle, and is the only path
  used in Baton bindings, messages, handoffs, reviews, and cross-references.
  Never bind `work/open/…`, an absolute checkout path, or a Git commit as the
  primary locator.
- `work/open/` is a maintained human convenience index of relative symlinks
  for still-open records. It is not protocol state and carries no lifecycle
  semantics.
- Every dossier has exactly one corresponding Work on the authoritative Baton
  ledger, bound with root `pc` to its canonical repository-relative path.
  Create the Work and dossier together when possible; once a dossier exists,
  create and bind its Work before further execution or handoff.
- A top-level record owns `FINDING.md`, `PLAN.md`, and implementer-owned
  `PROGRESS.md`. The finding preserves chronological evidence and decisions;
  the plan names what is actionable now; progress is the implementer's claim
  of current state.
- `PROGRESS.md` has one writer, `pc.code`. Reviewer and tuner evidence goes
  into `FINDING.md`, `PLAN.md`, evidence files, or append-only review
  journals, never implementer progress.
- Each review pass is a new
  `review-YYYY-MM-DDTHH-MM-SSZ.md` file in the record root, using UTC.
  Reviews are append-only; never edit or delete an earlier review.
- Work findings serially to completion. Re-read the whole record and
  revalidate captured claims when an item starts. Record resolved or
  superseded outcomes explicitly rather than deleting stale history.
- A causally tied child lives below
  `work/records/YYYY/MM/finding-<parent>/findings/finding-<child>/`, with its
  own finding, plan, progress, and review journal. Use a top-level record when
  it is independent or separately scheduled. Keep at most two child levels;
  promote deeper or independently scheduled work to a new top-level record
  with an explicit forwarding note at the old permanent path.
- Parent containment organizes accountability but does not itself block
  execution. Use explicit Baton dependency edges for execution gates. A
  parent cannot close while it has an open child.
- Anything that must stand alone—tests, user docs, durable policy—still lives
  outside the dossier. A record is durable evidence, not a hiding place for
  product artifacts.
