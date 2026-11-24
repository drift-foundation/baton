# Proposed follow-up Work — conversation resume under provider selection, revision 2

Author: baton.prompt (K, model Fable 5.2), interactive copilot, no claim.
2026-11-24. **A proposal. This file creates no Work and no dependency.**
Source: owner ruling in FINDING, "owner settles D4: defer conversation
resume implementation". DESIGN CTX-1 to CTX-5 are normative and unchanged.

Revises `FOLLOW-UP-RESUME-WORK-PROPOSED-2026-11-24.md` (unchanged, kept as
history; it is the file named in §10 of the delivery contract) for four
owner corrections: sequencing, attribution, continuity reporting and no
automatic fresh fallback. Changed places are marked **[R2]**. Nothing else
is added.

Instruction delivery stays bounded and separate:
`DELIVERY-CONTRACT-FINAL-2026-11-24.md`
(sha256 `c66c8c5e40fb9defa721daf356a8833daa531be190944971efcb470b58315965`), unchanged by this
revision.

## 1. Existing Work — none open covers this

Searched open Work by title (`context`, `resum`, `conversation`) and by id,
snapshot 386013.

| Work | State | Relation |
| --- | --- | --- |
| W174289 "Design concrete context reuse and restoration" | closed, satisfying | The design. Dossier `work/records/2026/09/finding-v12-context-reuse-design` |
| W236087 "Integrate managed session resume for reviewer corrections" | closed, satisfying, within its candidate-run scope | Legacy-path implementation and live restore proof. Dossier `…/09/finding-v12-managed-session-resume` |
| W177936 "Prepare production context qualification packet" | closed, satisfying | Its PLAN records production reuse as unqualified |
| W161234 and children | closed, satisfying | Correction and restart without duplicate execution |
| W385830 "Native Codex worker and explicit Claude model selection" | open, queued | Its contract excludes context-bound and resumed sessions (F12, S9, proof 47) |
| W110783 "Resume implementation ending after checkpoint fencing" | open, parked | Different subject: resuming an *ending*, not a conversation |
| W61981 / W321776 verification context | open | Different subject |

So: the legacy `/4`–`/6` path has an accepted resume mechanism of limited
scope; the provider-selection path `/7` has none and refuses context
workers; no open Work joins them. **Separate new Work is needed.**

## 2. Proposed Work

- **Title:** V12: Conversation resume for provider-selected Job workers
  (Claude and Codex)
- **Kind:** top-level, own dossier
  (`work/records/2026/11/finding-v12-provider-selected-conversation-resume`),
  classification `limitation`. Not a child of W385853 or W385830: it is
  separately scheduled and neither parent should wait on it to close.
- **Outcome:** under provider selection, a correction or restart of the
  same Job worker restores the provider's own conversation in a new
  container, bound and proved as CTX-1 to CTX-5 require. **[R2]** Where
  restoration is unproved or fails, the outcome stays explicitly unknown
  or failed, the evidence is preserved, and the recovery choice goes to
  Slawomir. No automatic fresh-context recovery is introduced.
- **Sequencing [R2]:** planned and tracked now. Implemented and reviewed
  as a native v12 Job, once native Codex and Claude execution and handoffs
  work. It does not block that initial pipeline.
- **First milestone:** a bounded contract only — reconcile the retained
  home (one mutable directory per Job and worker) with protected immutable
  context generations and single mutable use. That reconciliation is the
  open design question; nothing is implemented before the owner selects it.
- **Suggested split at its start (reviewer decides):** A — Claude under
  `/7`; B — Codex restoration. B cannot start before its own evidence.

## 3. Dependencies

**[R2]** Direction: this Work waits on the initial native pipeline. Nothing
in that pipeline waits on this Work. Creating and planning it needs none
of the rows below; they gate its implementation.

| Depends on | Why | Kind |
| --- | --- | --- |
| W385853 delivery accepted and imported | A resumed turn must carry the current label and worker-instruction digest; the label function and managed entry come from there | Hard, all parts |
| Native Claude and Codex execution and handoffs working (W385830: N2 packaged and qualified, N4 Codex adapter and its qualification) **[R2]** | The Work is implemented and reviewed as a native v12 Job on that pipeline | Hard for implementation and review; not for tracking or the contract |
| Pinned-build evidence of Codex session and resume operands and state layout | CTX-2 and CTX-5 forbid inferring layout or resume from another mode or build | Hard, Codex part only |
| Claude 2.1.247 evidence | `--session-id` and `--resume` are present in help [verified]; the September restore proof is on the legacy path and that CLI | Reusable; must be revalidated under `/7` |

Not dependencies, in either direction **[R2]**: W385853 and W385830 do not
wait on this Work to proceed, qualify or close; adoption of fresh-context
Jobs does not wait on it (AGENTS: context reuse is a deliverable, not a
gate on initial adoption).

Graph edges are installed by an eligible handler through supported
operations and read back before dependent execution. I install none.

## 4. Acceptance checks

Deterministic at real owners with a recording fake provider unless marked
live. A fake provider never proves that a vendor CLI resumed.

**Continuity**
1. Stop, new container, restore, correction: the next turn's argv carries
   the resume operand for the recorded conversation identity, runs in the
   retained workspace at the recorded candidate checkpoint, with the actual
   correction handoff (CTX-1, CTX-4).
2. The restored turn has a fresh attempt and execution identity (CTX-3).
3. Manager restart between save and restore reaches the same decision.
4. **[R2]** A turn is reported `resumed` only with validated provider
   continuity evidence: evidence from the provider's own output that it
   continued the intended conversation, retained and checked by the host.
   A resume operand in argv, a requested session id, a copied log and
   matching configuration, alone or together, are not that evidence
   (CTX-2). The exact evidence form is selected in this Work's contract
   against pinned-build output; it is not chosen here.
4a. *Live, separately selected:* the provider demonstrably recalls
   something only the earlier turn held.

**Attribution**
5. A resumed turn is bound to the same provider, requested model, reported
   identity, CLI build and profile as the generation it restores; any
   difference refuses as incompatible (CTX-2, CTX-4).
6. **[R2]** Model attribution follows the approved contributor-list rule
   unchanged, per turn: the requested model must appear; additional
   contributors are allowed. A contributor set that differs from the
   earlier turn's is not, by itself, a refusal or a hold.
7. **[R2]** Reporting has three distinct outcomes and never merges them:
   `resumed` (check 4 satisfied); restoration `unknown` (attempted,
   continuity unproved); restoration `failed`. An unknown or failed
   restoration is never relabelled `fresh`. `fresh` is used only for a
   turn that was started as a fresh invocation by selection.

**Instructions**
8. Every resumed turn carries the current execution-context label for its
   launch role and the current worker-instruction entry; label digest
   recorded and recomputed as in the delivery contract.
9. A context saved under one instruction or label digest and restored
   under another: one explicit, owner-selected behaviour (refuse, or
   restore with the new label and record both). Not decided here.
10. Prompt and argv digests agree between manager and worker for the
    resumed turn; legacy `/4`–`/6` context behaviour is byte-identical.

**Interrupted saves**
11. A final save that failed or is incomplete is an explicit recovery
    condition; the previous accepted generation is intact and still
    restorable (CTX-3).
12. Kill at each step of the save (before copy, mid-copy, before record,
    after record): a restart classifies each as complete or incomplete
    without guessing; none is silently treated as resumable.
13. An interrupted *turn* (provider killed mid-answer) with a non-empty
    home is not resumable on the evidence of the home alone.
14. **[R2]** No automatic fresh-context recovery. After an unknown or
    failed restoration, or an incomplete save, the stage is held; the
    generations, home, workspace checkpoint and logs are preserved
    untouched; one owner item presents the recovery choice to Slawomir
    with that evidence. Nothing retries, restores again or starts fresh
    until he chooses. A fresh invocation he selects is recorded as fresh
    and as his choice (CTX-3, CTX-4).

**Duplicate-start prevention**
15. One mutable use: a second restore of the same generation while the
    first use is unsettled refuses (CTX-3).
16. Restore requires positive cessation of the previous container; an
    uncertain holder stays pending, as the retained home does today.
17. Replay of the same restore request starts no second provider process
    and writes no second generation.
18. Two managers, or a restart during restore, start at most one.

**Refusals and custody**
19. Unknown previous invocation, replaced resource, missing generation or
    incompatible configuration each refuse explicitly (CTX-4).
20. Conversation state is protected custody: not in reviewer inputs,
    public logs or frozen outputs; retention is a positive inclusion list
    that excludes the credential; the whole home is never copied (CTX-5).
21. Implementation and review workers never share a context.

**Codex**
22. Checks 1–21 for the Codex realization, against operands and layout
    observed on the pinned build, not carried over from Claude.

## 5. Statements this Work must not make before its proofs

- That a retained home is a resumable conversation.
- That a correction turn under `/7` today continues a conversation. It is
  a fresh invocation with a handoff.
- That the September legacy proof covers `/7` or Codex.
- **[R2]** That a turn resumed because its argv carried a resume operand
  and its configuration matched.
