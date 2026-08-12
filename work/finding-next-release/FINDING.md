# Next release scope and closure audit

Status: **release envelope ruled 2026-08-11 and updated 2026-08-12: version
1.1.0, protocol 10, `examples/baton.json` included, editor-exit confirmation
and whole-message save required; TUI bulk archive deferred to protocol 11;
polling reliability deferred; a versioned candidate deployment is required for
Slawomir's pre-release soak trial. Production activation remains deferred.**

## Frozen baseline

Baton 1.0.0 is committed and frozen. Do not modify the released
`bin/baton`, `bin/baton-tui`, distribution manifests, production deployment,
or production authority/config.

**Superseded 2026-08-11:** next-generation work was required to use a separate
Slawomir-created branch/worktree and versioned deployment directory. The
current ruling drops the branch requirement and defers real deployment until
the next major release. Every candidate artifact still keeps the same
executable names:

    <deploy-root>/v<version>/bin/baton
    <deploy-root>/v<version>/bin/baton-tui

The current source worktree is already ahead of the frozen artifacts with TUI
search and materialization work. Source implementation may continue here, but
the frozen 1.0 `bin/` and manifests remain untouchable until Slawomir performs
the deliberate 1.1 release build. Agents still never mutate Git state.

## Recommended identity — superseded by ruling

**Superseded proposal:** release `1.1.0`, retaining protocol 10. Search, expanded
materialization, and scoped-notice authoring are user-visible features, so a
minor version describes the release more honestly than `1.0.1`. This is a
recommendation, not a ruling. The confirmed section immediately below records
that Slawomir accepted it.

## Confirmed release envelope — 2026-08-11

Slawomir ruled:

1. the next release is **1.1.0**, retaining protocol 10;
2. `examples/baton.json` ships in the deployed payload;
3. the proposed cut line below stands: whole-message save is the first stretch
   item and enters 1.1.0 only if its design/review gate closes before freeze;
   Markdown rendering and the other named large features remain deferred by
   default.

The example config is a shipped template, not a deployed authority. No SQLite
store, accepted config state, or implicit config discovery enters the product
tree; a caller still supplies the actual authority config explicitly.

## Branch/worktree clarification — 2026-08-11

**Confirmed technical fact:** a separate branch is not a runtime-isolation
mechanism for current users. `bin/baton` and `bin/baton-tui` are self-contained
zipapps; changing `src/` does not change their packaged bytes. The deployer
likewise publishes the certified artifacts named by their manifests, not live
source. The versioned deployment directory and separate development
authority/config are the boundaries that prevent a beta from affecting
production.

A branch/worktree still has release-management value: it preserves a clean 1.0
maintenance line and avoids leaving source/artifact currency tests red while
1.1 source advances. That is Git hygiene, not production safety, and Slawomir
alone controls whether it is worth the cost.

## Branch and deployment scheduling ruling — 2026-08-11

Slawomir explicitly ruled: **drop the branch isolation requirement**. Source
work may continue in the current worktree. This changes no Git ownership:
Slawomir alone stages, commits, branches, tags, and moves history.

He also deferred real installation outside the repository to the **next major
release**, not 1.1.0. The destination is deliberately undecided; the leading
operational shape is `<mailbox-root>/bin/baton` and
`<mailbox-root>/bin/baton-tui`, so one mailbox root contains its authority data
and a compatible CLI/TUI. Co-location does not make the authority deployment
payload: tooling must never copy, discover, initialize, or mutate the config or
SQLite store. Do not hard-code `/home/sl/src/mailbox` until the destination is
separately ruled.

For 1.1 development, candidate artifacts are built into scratch/candidate
roots and exercised only with a separate development authority/config. Frozen
1.0 artifacts remain the production tools until Slawomir's release action.

## Findings eligible for the deliberate post-1.0 cleanup pass

These findings are represented in committed 1.0.0 or immediately following
approved documentation commits, have accepted implementation evidence, and
have no surviving implementation work that is not owned by another finding:

- `finding-agent-wakeup`
- `finding-attach-part-default-type`
- `finding-cli-read-authority`
- `finding-effective-baton-guide`
- `finding-human-console` and its completed child findings
- `finding-mailbox-conventions`
- `finding-nonempty-message-bodies` and `finding-tweet-authoring`
- `finding-orphan-publication-link`
- `finding-part-name-semantics`
- `finding-project-layout`
- `finding-protocol-10-umbrella`
- `finding-release-version`
- `finding-subject-normalization`

**Proposed closure action:** perform one read-only path/commit audit, then
remove these ephemeral folders in a deliberate cleanup change authorized and
committed by Slawomir. Do not delete them merely because they appear in this
list. Durable policy, product tests, and user documentation already stand
outside the folders.

## Cleanup audit correction — 2026-08-12

The deliberate cleanup audit supersedes the eligibility claim above for two
folders. `finding-human-console` is not removable while
`tests/packaging/test_docs_consistency.py` reads its `FINDING.md`, `PLAN.md`,
and `TRIAL.md` as normative test inputs. That permanent dependency on an
ephemeral finding violates the repository policy and must be moved to a
durable owner or deliberately retired before the finding can close.

`finding-protocol-10-umbrella` is also not removable yet. Its `BULK-TRASH.md`
still preserves Slawomir's chronological bulk-selection and recoverable-Trash
rulings, and `POST-CUTOVER-AUDIT.md` remains the live cutover index. The
applicable history must first be carried into its durable or currently open
owner with later Archive/protocol-11 rulings explicitly marked as
supersessions rather than silently replacing the earlier decisions.

Nine other audited folders were removed after commit `f20d5b2`; the exact
scope and verification are recorded in
`review-2026-08-12T14-41-51Z.md`. One non-behavioral follow-up remains:
`tests/core/test_core_references.py` must replace its prose citation to the
removed `finding-mailbox-conventions` with the durable owner,
`docs/AGENTS-MAILBOX-PROTO.md` section "File references travel as their own
part".

## Recommended release scope

### Required 1.1 release mechanics

1. **Artifact isolation and currency** — leave frozen 1.0 artifacts/manifests
   untouched during source work; build 1.1 candidates only in scratch roots and
   use a separate development authority/config.
2. **Release gate** — deterministic rebuild, full tests, packaged workflows,
   artifact/manifests verification, human console trial, and independent
   review before Slawomir replaces any production artifact.

The implemented deployment recipe and its ruled future payload remain a
separate next-major finding. No external publish or stable-pointer activation
is a 1.1 acceptance step.

### Product work recommended for inclusion

1. **TUI metadata search** (`finding-tui-message-search`) — implementation and
   focused/PTY tests exist. Add the missing append-only independent review
   record and human trial; keep author/subject-only, literal filter-in-place,
   clear/reset, and Sent behavior.
2. **Materialize every fully viewable part** (`finding-save-message`) — the
   prerequisite real-`m` repair is signed off. Answered/closed, Sent, and seen
   notices save; unclaimed inbound pending and transient content remain
   refused. Whole-message save remains the separate stretch item below.
3. **TUI scoped-notice audience entry**
   (`finding-scoped-audiences/findings/finding-tui-notice-scope-picker`) —
   use an editable filter/combobox rather than an exhaustive scope drop-box.
   It presents only `*` and configured team scopes—never exact participants.
   Typing narrows team-scope suggestions, while a complete typed scope such as
   `web.*` remains publishable even when it was not pre-listed;
   preserve the audience through confirmation, draft/reopen, and failure and
   leave expansion/authorization to the core.
4. **Config regeneration wording** (`finding-config-regen-wording`) — clarify
   proposed-config editing versus audited `regen` acceptance and forbidden raw
   database edits; rebuild the next version's pinned documentation manifest.
5. **Polling reliability contract** (`finding-reviewer-polling-reliability`) —
   pin public exit statuses and level-triggered readiness, suppress duplicate
   ready notifications/back off, require a single-instance liveness check, and
   state honestly that a detached process cannot schedule a model turn. Baton
   must not grow an arbitrary-command wake hook.

### Proposed cut line

**First stretch feature:** whole-message save/chosen output path from
`finding-save-message`. The contract is confirmed—preserve transient refusal,
keep external leaves as pinned references, preserve ordered typed parts, reuse
no-clobber/idempotent publication—but the representation and UI still need a
design/review gate. Include it only if that gate closes before code freeze.

**Deferred by default:**

- `finding-tui-markdown-rendering` — well specified but a substantial renderer,
  hostile-text, layout, source-toggle, and dependency review;
- `finding-claim-progress` — new durable progress/blocker/priority state;
- `finding-message-reactions-voting` and `finding-decision-obligations` — new
  durable decision and reaction state with one authorization ruling still to
  confirm;
- the architecture half of `finding-live-first-mailbox-upgrade` — a new
  audited retirement ceremony, not required for this feature release.

These are not rejected. They are separated because combining new schema,
priority semantics, voting, Markdown rendering, deployment, and the existing
console work would turn one reviewable minor release into another protocol
program.

## Findings that must remain open — current-state clarification 2026-08-12

- `finding-scoped-audiences` cannot be removed before its TUI scope-picker
  child lands in the 1.1 commit. Both parent and child now explicitly mark the
  older WIP checkpoint superseded and the child source is reviewer-approved.
- `finding-save-message` remains present through the candidate gate. Its
  whole-message-save source is signed off; deployed exercise remains.
- `finding-reviewer-polling-reliability` remains open until its Baton-side
  tests/docs and external-runner limitation are both recorded truthfully.
- `finding-live-first-mailbox-upgrade`, `finding-claim-progress`,
  `finding-tui-markdown-rendering`, and reactions/decisions remain scheduled
  future work unless Slawomir explicitly promotes one into the cut line.

## Release acceptance

The release is ready only when every included finding has a current FINDING,
PLAN, implementer-owned PROGRESS, newest append-only review outcome of approved,
focused break checks, full-suite evidence, a packaged human trial, and no open
child. The candidate zipapps must run from a scratch distribution root with the
repository absent. Slawomir's deliberate 1.1 artifact rebuild/release remains
separate from ordinary source work; no next-major deployment or stable-pointer
activation occurs in this release.

## Candidate soak and final inclusion ruling — 2026-08-11

Slawomir ruled the remaining cut and trial questions:

- TUI search receives independent review first, then Slawomir exercises it as
  part of a deployed-candidate soak before clearing the release.
- A successful external body edit going directly to the existing Send Y/n
  confirmation is required in 1.1.0.
- Whole-message save to a chosen path is required in 1.1.0. The earlier
  stretch/cut option is superseded; its design/review gate remains mandatory,
  but it is no longer optional release scope.
- Reviewer polling reliability is deferred. It is an external Codex-runner
  lifecycle problem for this release; Baton must not invent an arbitrary wake
  hook to pretend otherwise.
- The pre-release workflow supports a human-run command in the shape
  `just deploy DEST 1.1.0`, followed by a period of real use and a separate
  human release clearance. This re-enables a non-production 1.1 candidate
  install; it does not authorize production activation or settle the
  next-major permanent destination.

### Existing-authority compatibility

No fresh mailbox, authority rebuild, or schema migration is required. Release
1.1.0 retains protocol 10 and the included source changes add no authority
schema version. A 1.1 CLI/TUI can open the existing protocol-10 config and
SQLite store directly. Operations performed during the soak are real claims,
receipts, messages, notices, replies, and closes on that authority.

Participant-local TUI drafts are the one versioned local-state exception. The
1.1 console reads draft formats 1 and 2 and writes format 2 so a scoped notice
cannot lose its audience. After 1.1 writes that file, the frozen 1.0 TUI will
refuse the newer draft file; it will not corrupt the mailbox or broadcast the
draft. The 1.0 CLI remains usable against the protocol-10 authority.

When every included source/review gate is complete, `baton.reviewer` sends a
notice telling Slawomir that the deliberate build/deploy/soak trial may start.

## Bulk select/trash inclusion ruling — 2026-08-11

Slawomir added **bulk select/trash** to the required 1.1.0 release scope. The
request is owned by `work/finding-tui-bulk-select-trash/`. Inclusion is
confirmed; implementation is blocked on the product meaning of trash. Current
protocol 10 has no trash lifecycle, and its deletion guards reserve authority
removal for retention, notice expiry, and `gc`, while the console's existing
`D` removes only unsent participant-local drafts. No implementation may infer
authority deletion or hide unresolved work before the finding records the
explicit lifecycle and persistence ruling.

## RC deployment handoff ruling — 2026-08-11

Slawomir ruled the immediate handoff after the bulk-archive correction:

> When K is done, review bulk archive then ping me to run just deploy to
> produce an RC binary

This sharpens the existing candidate sequence. After `baton.implementer`
hands off the completed correction, `baton.reviewer` independently re-reviews
the bulk-archive implementation and its verification. An approval triggers a
direct Baton message to Slawomir to run the ruled `just deploy DEST 1.1.0`
shape; Slawomir's deployment produces the release-candidate binaries used for
the soak and final release gate. A changes-requested result returns to K and
does not trigger the deployment ping.

This ruling does not authorize an agent to deploy, choose `DEST`, replace the
frozen 1.0 artifacts, activate a production pointer, commit, or tag. Those
ownership and production boundaries remain unchanged.

## Bulk archive deferral and SQLite ownership ruling — 2026-08-12

Slawomir ruled that SQLite is the metastore owner for participant-scoped
archive metadata. The protocol-10 participant-local JSON design must not ship,
so bulk archive is postponed to protocol 11 and removed from the 1.1.0 release
scope. This explicitly supersedes the 2026-08-11 inclusion ruling and the RC
handoff's dependency on bulk-archive approval.

The archive lifecycle remains metadata-only and must not alter delivery,
claim, receipt, retention, or content state. Protocol 11 will own the schema,
migration, compatibility, and transactional bulk-operation design. For 1.1,
K withdraws the JSON/UI implementation, the reviewer verifies the scoped
withdrawal and included-finding reconciliation, then directly tells Slawomir
to proceed with the human `just deploy DEST 1.1.0` candidate, testing, and RC
phase. Agents still do not deploy or choose `DEST`.
