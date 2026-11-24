# W385830 — native Codex implementation worker and explicit Claude model selection: proposed implementation contract

Author: baton.prompt (K, model Fable 5.2), interactive copilot, no claim.
2026-11-23. Authority: M385830, M385843 and this dossier's FINDING.

**PROPOSED — NOT APPROVED.** Research and design only. Nothing was built,
launched or tested; no provider was called; no credential was read; no
product, Git or live-instance change. The only commands run were `--version`
and `--help` of the CLI builds installed on this host, which are **not** the
builds pinned in any worker image (captures in
`evidence/research-385843/`).

Source baseline: main HEAD 6079ad78. Paths: `worker/` = `v12/worker/`,
`wm/` = `v12/python/src/baton_v12/worker_manager/`, `jm/` =
`…/job_manager/`, `tools/` = `v12/python/tools/`. **Confirmed** = I read it.
**Surveyed** = read by a read-only survey pass with citations; I re-read the
claims the plan depends on most. **Measured** = an earlier dossier recorded
it from a real binary. Nothing here was measured by me.

## 1. Outcome

A v12 Job can run its implementation phase on the Codex CLI and its
independent review phase on the Claude CLI with an explicitly selected
model, hand off between them through the existing native path, and show from
recorded evidence which provider build and which model each phase actually
used. A requested model that was not the one observed is refused, never
silently accepted.

Fresh attempts only. No new orchestration: the same worker exchange,
custody, credential delivery, limits, cancellation and recovery owners.

## 2. What exists and can be reused

| Area | State today | Reuse |
| --- | --- | --- |
| Worker seam | `baton_worker.main(agent=…)`; the agent needs one `work(seen, declared)` method, plus optional `observed_activity` and `observed_invocation`. The worker itself owns launch validation, the exchange documents, the replay fence, output measurement and the activity publisher (**Surveyed**, `worker/baton_worker.py`; minimal example `worker/scripted_agent.py:36-100`) | Entirely |
| Generic work inside the Claude adapter | `worker/claude_agent.py` is 7379 lines. Roughly 85% is provider-neutral: source checkout, the Git line, verification, proposal and handoff production, review report parsing, native handoff, log room, bounds. It lives inside `ClaudeAgent` and its module (**Surveyed**, with a section map) | By hooks, not by copy (§4.2) |
| Credential delivery | Provider-neutral. A registry entry and a `--credential slot=provider:reference` operand deliver one read-only file per slot at `/run/baton/credentials/<slot>`, per attempt, torn down at every ending (**Surveyed**, `tools/user_credentials.py`, `wm/credentials.py`, `wm/oci.py:808-855`) | A `codex` slot needs no manager change |
| Per-worker image and profile | Allowed by owner ruling W202663: image, toolchain, runtime profile and credential policy digests are excluded from the Job input identity (**Confirmed**, `contracts/manifest.py:707-710`) | Yes |
| Network | A named network per worker deployment; real deployments use `bridge`; no allow-list or proxy (**Surveyed**) | Yes; both lanes must name the same network |
| Native handoff, review, verdict, custody | Provider-neutral documents (**Surveyed**) | Entirely |
| Stop, deadline, token expiry | Container-level; the provider is a child process with a timeout (**Surveyed**) | Entirely |
| Adapter tests | The provider is injected through `ClaudeAgent(run=…)`; fixtures are hand-built; no live provider (**Surveyed**, `tests/manager/test_claude_agent.py`) | Same pattern |
| Qualification packet | Image config and byte comparison against source, deterministic log, packaged `pool compose-worker` for both roles, capability candidates (**Confirmed** — I reviewed one: W385694 `qualification-385752`) | Same packet per image |

## 3. What is missing or fixed to Claude

| # | Finding | Where | Status |
| --- | --- | --- | --- |
| F1 | No Codex adapter, entry or image. Codex exists only in the August ping-pong spike, which says it must not be promoted | `worker/`; `v12/spike/ping-pong/README.md:3-8` | Confirmed |
| F2 | **The fresh Claude invocation passes no model.** Its argv is the program, three fixed flags and the prompt. `--model` is added only on the context-bound path | `worker/claude_agent.py:4369, 4373` | Confirmed |
| F3 | The runtime profile carries `"model": "opus"`, hard-coded, for every worker. It is digested but nothing delivers or enforces it. The launch document has no model member | `tools/next_run_bindings.py:360`; `wm/launch.py:90` | Confirmed / Surveyed |
| F4 | Retained real output of a fresh run without `--model` shows the account default was used. So today's "Opus" selections are labels, not selections | `work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-acceptance-invocation-ended-wording-1/` | Surveyed (Measured there) |
| F5 | **The pinned Claude build's result has no direct `model` field.** On 2.1.247, `--model claude-opus-5` produced a terminal record whose `modelUsage` named the selected model **and** a helper model. The worker reads only the direct `model` field, so its observed model is empty; and the host drops the observed-model check for current receipts | `work/records/2026/09/finding-v12-production-context-qualification-preparation/FINDING.md:2146-2460`; `worker/claude_agent.py:4589-4593`; `wm/provider_context.py:998-999` | Measured there / Confirmed in code |
| F6 | **A Codex lane beside a Claude lane would be refused today.** `tool_policy_digest` — the digest of the provider's argv and environment policy — is part of the Job input identity that every lane must share | `contracts/manifest.py:700-710`; `tools/next_run_bindings.py:267, 303` | Confirmed |
| F7 | `pool compose-worker` has no provider or model operand; every composed worker, reviewers included, is stamped `claude-fresh-implementation` with the Claude argv policy | `tools/pool.py:737-743`; `tools/next_run_bindings.py:338-386` | Surveyed |
| F8 | `separation_class` is the constant `provider-diverse` and is never computed or enforced; today's Claude/Claude pools carry that label | `tools/stage_execution.py:446-449`; `jm/scheduler.py:25-26, 55-60` | Surveyed |
| F9 | **Codex and the container posture collide on HOME.** The spike measured that Codex will not start with its state directory read-only, and refuses a HOME under a temporary directory. A v12 container has a read-only root and its only private writable scratch is tmpfs under `/tmp` | `work/records/2026/08/finding-v12-docker-ping-pong-smoke/`; `wm/oci.py:168-200` | Measured there / Confirmed |
| F10 | Codex's child process outlived a signal to the parent and held the pipes; the spike had to kill the whole process group. The v12 worker kills only the direct child | Spike `trial.mjs:146-175`; `worker/claude_agent.py:1982-1990` | Measured there / Confirmed |
| F11 | The provider inherits the worker's stdin. Codex reads stdin when it is piped | `worker/claude_agent.py` (no `stdin=`); host help text | Surveyed / host help |
| F12 | The context-bound (session reuse) path is Claude-literal in both worker and host | `worker/baton_worker.py:3345-3348`; `wm/provider_context.py:23-32` | Surveyed |
| F13 | No pinned production Codex build exists. The spike pinned 0.150.1; this host has 0.169.0. The Claude worker pins 2.1.247; this host has 2.1.330 | `v12/spike/ping-pong/Dockerfile.codex:13`; `worker/Dockerfile.claude:63`; captures | Confirmed |

## 4. Design

### 4.1 Scope boundary

In: Codex as a fresh **implementation** worker; explicit model selection and
observed-model evidence for **both** providers' fresh turns; composition of
two different provider workers under one Job; images; qualification.

Out: context-bound or resumed Codex sessions (F12); Codex as reviewer;
streaming or event parsing for monitoring; the worker ceiling and
containment work of W385263; any change to scheduling, custody or recovery.

### 4.2 Provider hooks instead of a second adapter

The provider-specific parts of the Claude adapter become a small set of
overridable members of the agent class, with today's values as the Claude
defaults:

- program and fixed arguments; how the model selector is added to argv;
- the provider's home layout and how the delivered credential is placed in
  it;
- where the provider's native session files are (for activity and
  retention);
- how the terminal outcome is read: success, the failure word, the
  diagnostic, the observed model.

A `CodexAgent` subclasses the same agent and overrides only those. Checkout,
verification, proposal, handoff, review and logging are inherited unchanged.
A Codex entry file constructs it, as `worker/dogfood_entry.py` constructs
the Claude one.

This is the smallest change that avoids a 7000-line copy. It is not a
refactor of the adapter: no orchestration moves. It does change
`claude_agent.py`, which is in the Claude image, so that image is rebuilt and
requalified (§6).

Two generic hardenings ride along because Codex needs them and Claude is
unharmed: the provider is started with no stdin (F11); and at the provider
time limit the provider's process group is ended, not only the direct child
(F10). The second is deliberately the minimum; full containment and its
evidence remain W385263's later slice and are not claimed here.

### 4.3 Explicit model, end to end

1. **Selected** per worker at composition: `pool compose-worker` gains a
   model operand. It is written into that worker's runtime profile in place
   of the hard-coded value, together with the identity the provider is
   expected to report. The profile digest already covers it and is already
   per-worker.
2. **Delivered** to the worker by one new versioned member of the launch
   document. (The implementer confirms the smallest versioned channel; the
   launch document is where the role and the limits already travel.)
3. **Applied:** the fresh argv carries the selector. No fallback-model option
   is ever passed.
4. **Observed:** the adapter extracts every model identity the provider's
   terminal output names — for Claude, the direct `model` field if present
   and the keys of `modelUsage` (F5) — and records, in the proposal or
   review result it already writes: the requested selector, the expected
   reported identity, the observed identities, and the CLI build.
5. **Enforced on the host at the ending**, before a candidate is accepted or
   a verdict recorded: the expected identity must be among the observed
   ones. If it is not, or nothing was observed, the result is refused with a
   typed cause and the phase is held for the owner — the same shape as the
   recovery-digest binding accepted in W385625. Nothing retries and nothing
   substitutes.
6. **Shown:** requested, expected and observed model and the CLI build appear
   in the attempt's published diagnostics.

What this evidence does and does not prove, stated in the contract so nobody
over-reads it: it proves the provider reported using the expected model in
that invocation. Where the provider also reports a helper model (F5), it
does not prove every token came from the selected one.

`separation_class` is computed from the composed workers' provider and model
instead of asserted (F8), so the label is true.

### 4.4 Two providers under one Job (F6)

`tool_policy_digest` must stop encoding one provider's command line.
**Proposed:** it becomes the digest of a provider-neutral tool policy — what
the owner actually selected: non-interactive, full in-container tool
permission, composed environment, no ambient credentials — identical for
every lane. Each provider's actual argv and environment policy move into
that worker's adapter document, which is already per-worker and bound by the
adapter digest.

The alternative is to add `tool_policy_digest` to the per-worker exclusions.
That is smaller, but an earlier review (206898 R2) warned specifically
against dropping policy digests from the Job identity, so I do not recommend
it. This is decision D5.

Either way digests change for newly composed instances only. Existing
instances and their evidence are untouched.

### 4.5 The Codex adapter

Deliberately **not fixed here**: the exact Codex argv, the event shapes it
parses, the session-file location and the credential file name. The pinned
build does not exist yet (F13), and the owner's instruction is to inventory
the pinned build before prescribing flags. What is fixed is the behaviour
each must deliver, and what the host build suggests is available:

| Need | Behaviour required | Host 0.169.0 help shows (reference only) |
| --- | --- | --- |
| Non-interactive single turn | One process, one prompt, exits | `codex exec [PROMPT]` |
| Full in-container tool permission | The owner-selected posture, equivalent to the Claude worker's | `--dangerously-bypass-approvals-and-sandbox`; `-s danger-full-access` |
| Explicit model | Selector on the command line | `-m, --model` |
| Working directory | The candidate root | `-C, --cd`; `--skip-git-repo-check` |
| No ambient configuration | No user config or rules from the image | `--ignore-user-config`, `--ignore-rules` |
| Machine-readable outcome | Success or a classified failure, and the model used | `--json` (JSONL events); `-o` (last message to a file) |
| Bounded reading | The existing reader keeps one ≤ 64 KiB record; a JSONL stream needs a bounded reader of the terminal events only, with the full stream retained in the existing provider log | — |
| Failure words | Mapped into the host's closed set (`api-error`, `start-error`, `timeout`, `unclassified`) unless a new word is approved | — |
| Activity and retention | From the provider's own session files, if the pinned build writes them where the adapter can read | Not established |

**Home and credential (F9).** Codex needs a writable home that is not under
a temporary directory, with its credential file inside it, while the
delivered credential is a read-only file elsewhere. Proposed: one additional
small private tmpfs mounted at the provider's home path for a Codex worker,
declared in that worker's deployment and composed into the run vector, with
the adapter linking the credential into it. That is a narrow change to the
container posture and is decision D6. **Undetermined** and to be answered by
qualification, not assumed: whether the pinned build accepts a linked
credential; whether its temporary-directory check is about the path or the
environment; and what it does when it wants to refresh a credential it
cannot write.

### 4.6 Images

- `Dockerfile.codex` mirrors `Dockerfile.claude`: same base family, trust
  store, tools, user, verifier scaffolding and layout marker, the same
  generic files, the Codex adapter and entry, and an exact Codex pin. A
  version gate test mirrors `tests/manager/test_dogfood_image.py`.
- `Dockerfile.claude` is rebuilt because `claude_agent.py` changes. Whether
  its CLI pin also moves depends on D1.

## 5. Slices

Each is independently reviewable. N1 and N2 are deterministic and can start
as soon as their decisions are answered.

| Slice | Outcome | Main area | Needs |
| --- | --- | --- | --- |
| **N1** | Explicit model for fresh turns: composition operand, launch member, argv, observed-model extraction, result fields, host enforcement at ending, diagnostics, computed separation class | `tools/pool.py`, `tools/next_run_bindings.py`, `wm/launch.py`, `worker/baton_worker.py`, `worker/claude_agent.py`, `tools/stage_execution.py`, `jm/review_driver.py`, `wm/failure_cause.py`, tests | D2, D4 |
| **N2** | Provider hooks; no-stdin and process-group hardening; provider-neutral tool policy with per-worker adapter policy | `worker/claude_agent.py`, `tools/next_run_bindings.py`, `contracts/manifest.py`, tests | D5 |
| **N3** | Codex adapter, entry and image recipe against the pinned build's inventory; provider home mount | `worker/codex_agent.py` and entry (new), `worker/Dockerfile.codex` (new), `wm/oci.py`, `tools/pool.py`, tests | D1, D3, D6; N2 |
| **N4** | Engine-only image gates for both images (no provider) | image gate tests | Engine selection (D7) |
| **N5** | Real-provider qualification: two narrow questions (§6.3) | evidence only | Owner selection (D7), credentials (D3) |
| **N6** | Packaging and worker qualification packets for both images; joined deterministic Codex-implementation → Claude-review proof under one Job | evidence; one joined test | N1–N5 |

The first native Job on this pipeline is a separate owner selection after
N6. It is not part of this contract.

## 6. Verification

### 6.1 Deterministic (default; fake provider at its normal boundary)

N1:

- composing a worker with a model writes it into that worker's profile and
  changes only that worker's profile digest;
- the fresh argv carries exactly the delivered selector and never a fallback
  option; with no model delivered the launch is refused, not defaulted;
- observed identities are extracted from a terminal record with a direct
  model field, from one with only usage keys including a helper model (the
  2.1.247 shape), and are empty for a record with neither;
- expected identity present → result proceeds; absent, empty, malformed or
  oversized → refused with the typed cause; no candidate accepted, no
  verdict recorded, phase held, nothing retried;
- an accepted review records requested, expected, observed and CLI build;
- the same checks for an implementation result;
- an old worker image that reports no model evidence is held, not accepted
  (fails closed);
- separation class reflects the composed workers.

N2:

- every existing Claude adapter case still passes with the hooks in place
  and the default values;
- the provider is started with no stdin;
- at the time limit the provider's whole process group is ended and the
  drain completes, including with a child that ignores the first signal;
- two workers with different provider argv policies and the same neutral
  tool policy are admitted under one Job; a worker whose neutral policy
  differs is still refused.

N3:

- the Codex adapter produces the same proposal, handoff and result documents
  as the Claude one for the same fake outcome;
- each terminal outcome of the pinned build's inventory maps to the right
  status and failure word; an unrecognised or truncated stream is
  `unclassified`, never success;
- the credential is linked, never read or copied into any output or log;
- the home mount is present only for a worker that declares it.

N6 joined: a Codex-profile implementation lane and a Claude-profile review
lane, both with fake providers, run one Job through admission, handoff,
review and verdict with the model evidence bound at each ending; a review
whose observed model lacks the expected identity leaves no verdict.

Test modules are registered once each (`tools/parallel_test.py`), in the
manager-pure group; image gates in manager-engine. Focused runs per
`v12/python/TESTING.md`; no full-suite run is selected.

### 6.2 Engine-only image gates (no provider, no credential)

Needs an engine but calls no model. Per image: it builds; the pinned CLI
reports the pinned version; the files under the adapter directory are
byte-identical to source; the flags the adapter uses appear in the pinned
build's own help; and, for Codex, the CLI starts far enough under the real
container posture (read-only root, the proposed home mount, composed
environment) to show whether it accepts that home. **This is where the
pinned-build flag inventory is taken** and written into the adapter's
fixtures.

### 6.3 Real-provider qualification (narrow, owner-selected)

Deterministic tests cannot answer these, because they are facts about the
provider's own behaviour:

| # | Question | Why a fake cannot answer it |
| --- | --- | --- |
| Q1 | Under the exact v12 container posture and the delivered read-only credential, does the pinned Codex build authenticate and complete one fixed trivial task with the adapter's exact argv, and what are its terminal events, exit status, reported model and session files? | Authentication, credential refresh and event shape are the provider's |
| Q2 | Does the pinned Claude build accept the selected Fable selector, and which identities does its terminal record then report? | Whether that build knows the selector, and what it reports, are the provider's. F5 shows the report is not what the code assumes |

Each is one bounded invocation with a fixed prompt, no repository content,
the selected limits, and retained evidence. Neither can force "model
unavailable"; the design therefore does not depend on how unavailability
looks — any outcome without the expected identity is refused.

### 6.4 Qualification packets

One per image, as W385694's: image config and identity, byte comparison of
image files with source, deterministic log, packaging identity, packaged
`pool compose-worker` output for the role, capability candidate, and an
explicit statement of what was not run.

## 7. Decisions for the owner

All seven are real; none is answered by anything I found. Proposed order,
each with what it unblocks:

| # | Decision | Options and recommendation | Unblocks |
| --- | --- | --- | --- |
| **D1** | **CLI pins.** Codex: which exact build. Claude: stay on 2.1.247 or move | Codex: the spike's 0.150.1 is the only build proved in a container, in August; a current build has the flags listed in §4.5 but is unproved. Claude: 2.1.247 is unproved for the Fable selector the owner wants. Recommendation: choose a current Codex build and decide the Claude pin from Q2's answer, accepting requalification of whichever image moves | N3, N4 |
| **D2** | **Model selections.** The exact Fable selector and the identity it is expected to report; and for Codex either an explicit model or an explicit, recorded "provider default" | M385827 selected no Codex model. I recommend an explicit Codex model, so that "no silent substitution" holds on both lanes. I have not guessed any identifier | N1, N5 |
| **D3** | **Codex credential.** Which kind of credential the Codex worker uses and its registry reference | The spike used a login credential file. Whether that kind survives a read-only delivery through a token refresh is unknown (Q1). An API-key credential avoids refresh. Owner's choice; I have read no credential | N3, N5 |
| **D4** | **Model mismatch policy.** Refuse and hold, as designed in §4.3 | Recommended: refuse the result, record the typed cause, hold for the owner, no retry. The alternative — accept and flag — contradicts "no silent fallback" | N1 |
| **D5** | **Tool policy digest.** Provider-neutral shared policy (recommended) or per-worker exclusion | §4.4 | N2 |
| **D6** | **Provider home mount.** Approve one private tmpfs at the provider home for workers that declare it | Narrow posture change, needed by F9. Alternative: none found that keeps the read-only root | N3 |
| **D7** | **Execution selections.** Engine-only image gates (§6.2) and the two real-provider calls (§6.3) | Both are materially different execution and need selecting when their slice is reached | N4, N5 |

If the owner prefers one question at a time, D5 comes first: it decides
whether a mixed-provider Job is admissible at all, and N1 and N2 can then
start while D1–D3 are considered.

## 8. Overlap

| Path | Also changed by | Handling |
| --- | --- | --- |
| `tools/pool.py`, `tools/stage_execution.py`, `tools/parallel_test.py`, `DEPLOYMENT.md` | W385695's remaining checkpoints (publication lane, pool/2, new test module) | Serial; agree order at claim time |
| `jm/scheduler.py` | W385695 | Only touched here if separation class is computed there; prefer computing it in composition |
| `worker/claude_agent.py`, `worker/baton_worker.py`, `worker/Dockerfile.claude` | W385263 slice L1 (ceiling and containment), later | N2's process-group change is the minimum; L1 builds on it. Serial |
| The Claude worker image | Every Job that binds image 19eb459b… including W385695's running one | A rebuilt image is a new digest and is requalified. Running and already-admitted Jobs keep the image they were admitted with |
| `contracts/manifest.py`, `tools/next_run_bindings.py`, `wm/launch.py`, `wm/oci.py`, `wm/failure_cause.py` | Not in W385695's declared set | Free, subject to confirmation at claim time |
| W385263 A1 (`tools/job_observation.py`, viewer, status) | — | No overlap |

## 9. What this contract does not claim

- That any Codex build works in a v12 container. Only the August spike ran
  one, under a looser posture, and it is not conformance evidence.
- That the pinned Claude build supports the Fable selector.
- That observed-model evidence proves exclusive use of the selected model.
- That the size of the work is known. N1 and N2 are well bounded. N3's size
  depends on the pinned build's output format and on F9, and should be
  re-estimated after N4.

## 10. Limits of this research

- Nothing was executed except host `--version` and `--help`.
- Surveyed claims I did not re-read include: the full section map of
  `claude_agent.py`; that `wm/failure_cause.py` restricts failure words to
  four; the spike's measured Codex behaviours; the W385695 path list.
- Not traced: what stdin an exchange-transport worker actually has; whether
  `tools/worker_image.py` handles the tag-based Claude recipe; the
  agent-session schema's Codex app-server vocabulary, which belongs to a
  different session model and is not used here.
- Codex session-file location, event shapes and credential file name are
  deliberately not stated: they are the pinned build's to answer.
