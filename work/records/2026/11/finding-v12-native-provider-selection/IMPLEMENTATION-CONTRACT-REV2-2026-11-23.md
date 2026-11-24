# W385830 — proposed implementation contract, revision 2 (delta)

Author: baton.prompt (K, model Fable 5.2), interactive copilot, no claim.
2026-11-23. Authority: M385845 and the FINDING entry "D5 provider-neutral
policy selected — owner 2026-11-23".

**PROPOSED — NOT APPROVED.** Research and design only. Nothing built,
launched or tested; no provider call; no credential read.

`IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-23.md` stays the base text and is
preserved unchanged. This file replaces its §4.4 and the D4 and D5 rows of
its §7, adds proofs to §6.1, and raises the next decision. Paths as there.

## 1. Settled

| # | Settled by the owner | Source |
| --- | --- | --- |
| D5 | The shared Job identity keeps a **provider-neutral** tool-permission and environment policy. Each provider's exact command and environment configuration is bound separately, in that worker's adapter identity. Different CLI commands are allowed; a different selected permission policy is refused. The policy digest is not simply excluded and admission validation is not weakened | M385845 |
| D4 | No silent fallback or substitution. A result whose observed model is not the requested one is refused and held | Already selected (M385827, M385830, FINDING); listed in the first contract as a decision in error. It is not open |

Not selected by D5: the exact documents, their member names, or any
migration. Those are proposed below.

## 2. Tool policy and adapter identity (replaces first contract §4.4)

### 2.1 Today (Confirmed, `tools/next_run_bindings.py:303-306, 373-379`)

- The Job-shared `tool_policy_digest` is the digest of
  `baton.worker-tool-policy/1`, whose content is the **Claude** argv policy
  and environment policy.
- The per-worker adapter document, `baton.single-implementation-adapter/1`,
  embeds the same two Claude policies again, beside the adapter name and
  entrypoint.
- So the provider's command line is in the shared identity, and the adapter
  document adds nothing provider-specific that the shared one lacks.

### 2.2 Proposed documents

**Shared: `baton.worker-tool-policy/2`** — what the owner selected for the
Job, with nothing that names a provider or a program:

| Member | Selected value today |
| --- | --- |
| interaction | non-interactive, one prompt, one process |
| tool permission | full, inside the container |
| provider sandbox | none of its own; the container is the boundary |
| user configuration | none ambient; only what the adapter composes |
| credentials | the delivered slot only; no ambient credential; never written back |
| environment | composed, never inherited; the closed key list |
| ephemera | fresh per child |
| model substitution | none; no fallback model |

Its digest is the Job's `tool_policy_digest`. Every lane must carry the same
one, exactly as today.

**Per worker: `baton.single-implementation-adapter/2`**:

- adapter name, engine, network, entrypoint, as today;
- `provider` and its exact argv policy and environment policy (program,
  fixed arguments, how the model is passed, home, working directory);
- `implements_tool_policy`: the digest of the shared policy this adapter
  realises.

Its digest is the worker's `adapter_digest`, which is already per worker and
already bound into the capability tuple.

### 2.3 How "implements" is kept honest

A declaration alone would be the weakened validation the owner ruled out.
Three things bind it:

1. **One owned table.** For each supported provider, one place in the build
   maps each shared policy member to that provider's concrete realisation —
   for example "tool permission: full" to the Claude flag and to the Codex
   flag. The composer builds the adapter document **from** that table and a
   selected shared policy. An adapter document cannot be composed that
   claims a policy its argv does not realise, and a provider with no table
   entry for a policy value cannot be composed at all.
2. **Admission check.** A worker is admitted to a Job only if its adapter's
   `implements_tool_policy` equals the Job's `tool_policy_digest`. This is
   an added check beside the existing equality of `tool_policy_digest`
   across lanes, which stays.
3. **Worker check.** The worker refuses to start the provider unless the argv
   it is about to run matches the argv policy it was delivered, as the
   context-bound path already does for its own argv
   (`worker/claude_agent.py:4375-4376`).

So: a Codex lane and a Claude lane with different commands and the same
selected policy are admitted together. A lane whose selected policy differs
— say a restricted tool permission — has a different `tool_policy_digest`
and is refused by the existing equality. A lane whose adapter claims the
shared policy but was not composed from the table cannot be produced by the
supported composer, and a hand-edited one fails its digest binding.

### 2.4 Versioning and old admissions

- **Nothing already admitted changes.** Composed worker documents carry
  their digests as stored values. Existing deployments keep
  `tool-policy/1` and `adapter/1` digests, remain mutually consistent, and
  validate exactly as today. Their evidence and qualification packets keep
  their meaning.
- **New composition emits the `/2` documents.** Which is produced is decided
  by an explicit composition selection, not by the build date, so an
  operator can still reproduce an old composition.
- **`/1` and `/2` lanes never mix in one Job:** their `tool_policy_digest`
  values differ, so the existing equality refuses them. No special rule is
  needed.
- **For an adapter `/1` worker** the new admission check (2.3, item 2) is
  satisfied by construction and is evaluated the old way: its embedded
  policies are the `/1` shared policy.
- **Carrying the claim.** Admission must be able to read
  `implements_tool_policy` for a worker. Today a deployment carries the
  adapter's name and digest. Whether the member travels in the deployment
  document (a new deployment schema revision beside `/4`–`/6`) or is
  resolved from a retained adapter document is the implementer's choice;
  either way it is covered by the adapter digest. **To confirm at
  implementation:** the smallest versioned carrier.
- The worker manifest contract is unchanged: `tool_policy_digest` remains
  one opaque digest member.
- The context-bound path keeps its own Claude argv and environment policy
  digests (`wm/provider_context.py:31-32`). It is out of scope and
  untouched.
- A capability qualified against an `adapter/1` digest does not carry over
  to an `adapter/2` worker; both images are requalified, as the first
  contract already requires.

### 2.5 Normative implication

DESIGN already says providers and models are independently configured
runtime capabilities (ID-6), and that one Job may fan out to several
providers with each execution bound to its own runtime configuration, "do
not require runtime identity equality across executions" (ID-4, owner
clarification 2026-09-28). The selected approach fits that text. One
clarifying sentence is proposed for the owner's approval; nothing is drafted
into DESIGN:

> Owner clarification (W385830): the tool-permission and environment policy
> a Job is admitted under is provider-neutral and shared by every execution
> of the Job. Each execution's provider-specific command and environment
> configuration is bound to its own adapter identity and MUST be composed
> from, and declare, the shared policy it realises. Executions MAY use
> different provider commands; an execution under a different selected
> policy, or whose adapter does not realise the Job's policy, MUST be
> refused.

## 3. Added deterministic proofs (adds to first contract §6.1, slice N2)

**Positive — mixed provider.**

1. A Codex-provider worker and a Claude-provider worker composed from the
   same selected shared policy have equal `tool_policy_digest`, different
   `adapter_digest`, and are admitted as the implementation and review lanes
   of one Job.
2. Each worker's delivered argv policy is its own provider's; the worker
   starts its provider only when the actual argv matches it.
3. The joined N6 proof runs that Job through handoff, review and verdict.

**Negative — policy mismatch.**

4. One lane composed under a different selected policy (for example a
   restricted tool permission) → refused at admission for unequal
   `tool_policy_digest`, before any effect.
5. A worker whose adapter document names a different
   `implements_tool_policy` than the Job's → refused.
6. An adapter document altered after composition (argv changed, claim kept)
   → refused on its digest binding.
7. Composition for a provider with no table entry for a selected policy
   value → refused; no document is produced.
8. A worker whose actual argv differs from its delivered argv policy →
   refuses to start the provider.

**Preservation.**

9. A retained pre-change worker document (for example the two under
   `work/records/2026/11/finding-v12-proposal-output-limit/evidence/qualification-385752/`)
   still validates, and reproduces its recorded digests when composed with
   the old selection.
10. A `/1` lane and a `/2` lane in one Job are refused.
11. Every existing Claude composition and adapter test passes unchanged
    under the old selection.

## 4. The next decision for the owner

**Must every worker name an explicit model — the Codex implementer
included?**

M385827 selected explicit Fable for the Claude reviewer and said no Codex
model override was selected. The design needs to know, before slice N1 is
built, whether "no model named" is a permitted state.

- **A — Explicit on every worker (recommended).** Composition refuses a
  worker with no model. The Codex lane carries a named model, selected later
  with the Codex pin. Requested, expected and observed model are then
  recorded and checked on both lanes by one rule.
  No lane can run on "whatever the account defaults to", which is exactly
  the situation finding F4 found on today's Claude workers.
- **B — Explicit where selected; otherwise a recorded provider default.** A
  worker may be composed with "provider default". Its observed model is
  recorded, but there is nothing to check it against.
  Less to select now. Cost: the Codex lane's model can change underneath a
  Job with no refusal — a silent change of the kind the owner has ruled out
  for the reviewer.

This asks only whether a model must be named. It does not ask for the
identifiers: those depend on the CLI pins and are raised with them. I
recommend A and have not assumed it.

## 5. Decisions still open after that

| # | Decision | Unblocks |
| --- | --- | --- |
| D1 | CLI pins: which Codex build; whether the Claude pin moves | N3, N4 |
| D2 (rest) | The exact Fable selector and expected reported identity; the Codex model identifier | N5; values only — N1 does not wait for them |
| D3 | Codex credential kind and registry reference | N3, N5 |
| D6 | One private provider-home mount for workers that declare it | N3 |
| D7 | Selection of the engine-only image gates and the two real-provider calls | N4, N5 |

With D5 settled, slice N2 can be specified for implementation now; N1 can as
soon as §4 is answered.

## 6. Limits

- Nothing executed.
- That a deployment carries only the adapter's name and digest, not the
  document, is a survey statement I did not re-read; §2.4 leaves the carrier
  to the implementer for that reason.
- The policy members in §2.2 are my reading of what is selected today from
  the Claude argv and environment policy and the owner's "full in-container
  provider tool permissions"; the member names are proposals.
