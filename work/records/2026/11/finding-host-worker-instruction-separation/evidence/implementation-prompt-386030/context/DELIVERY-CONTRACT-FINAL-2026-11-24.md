# W385853 — bounded worker-instruction delivery contract (consolidated)

Author: baton.prompt (K, model Fable 5.2), interactive copilot, no claim.
2026-11-24. Base: checkpoint `317351e73c92749e201f536ba115c9fdf213077d`.
Status: **all four decisions settled by the owner; whole-contract approval
and implementation selection are not yet given. Nothing here is
implemented, built or qualified.** Reading only.

Self-contained. It replaces, for reading,
`DELIVERY-CONTRACT-PROPOSED-2026-11-24.md` (`5232ba50…`) and
`DELIVERY-CONTRACT-REV2-2026-11-24.md` (`3e9ffe13…`); both are unchanged
and kept as history.

Marks: **[V]** verified in this repository's code or retained evidence;
**[D]** vendor documentation, not verified on the pinned build;
**[A]** assumption; **[P]** proposed here; **[O]** owner ruling in FINDING.

## 0. Settled decisions [O]

| | Ruling |
| --- | --- |
| D1 | No mechanical exclusion of the source `AGENTS.md`. Baton delivers an explicit execution-context label: native-worker context, assigned role, which host-only procedures do not apply. Applicability only; not a security boundary or a grant |
| D2 | `docs/V12-WORKER-INSTRUCTIONS.md` stays canonical. `provider_policy` carries a byte-identical packaged copy; a test fails when they differ. The worker's adapter-reconstruction and digest checks are preserved |
| D3 | Reviewed against D1 as the owner directed: the label travels in the prompt; the home file alone is not relied on (§3.3) |
| D4 | Delivery is scoped to fresh invocations under `/7`. Retained Job/worker homes are preserved. Conversation resume is deferred as implementation, remains a required v12 deliverable, and is separate Work (§10). A retained home is not conversation resume |

## 1. What N2 provides at 317351e7 [V]

- Adapter `baton.single-implementation-adapter/2` has `managed_entries`,
  `[]` for every selection today. The adapter is a pure function of the
  selection in the shared `provider_policy` package; manager and worker
  each rebuild it and refuse any difference.
- The adapter digest is carried by the provider delivery, the attempt
  record and admission. The delivery also binds authority, Job, worker and
  attempt, and is validated against `job_execution` before any turn.
- `home.prepare(managed=…)` places `(path, bytes, sha256)` entries:
  canonical relative path, digest checked, atomic replace at every start,
  refusal on overlap with the credential or a provider-owned path.
- The worker's `_prepared_home` refuses a non-empty list today.
- The home is one per Job and worker, retained across container
  replacement and restart, never seeded from an operator home.
- Provider selection exists only under deployment `/7`, which refuses
  context-reuse and publication workers. Only the Claude realization
  exists.
- The Claude image recipe copies the whole `provider_policy` directory.

## 2. Instruction files, exactly

| File | sha256 at 317351e7 | Bytes | Class | Native worker |
| --- | --- | --- | --- | --- |
| `docs/V12-WORKER-INSTRUCTIONS.md` | `369ccb173d0bec1b4ba109127677d611d36e327e17f11b82c3bf13bf2f28627b` | 5,646 | Worker policy, canonical | **Delivered, exact bytes, via the packaged copy** |
| Packaged copy inside `provider_policy` | must equal the row above | 5,646 | Delivery source | Read by manager and worker |
| `AGENTS.md` | `e9e3416d7a6c3dca4206c2379f6031fef79a92926a05ad64781e86c6d6aa8421` | 20,570 | Host-only | Never placed by Baton; may be read from the candidate tree; the label governs |
| `docs/HOST-INTEGRATION.md` | `7d33a568cbdef9e309159c0daed7413eb5490b0547fce7b86e926e89fcafa68e` | 1,287 | Host-only | Same |
| Anything under an operator `~/.claude` or `~/.codex` | not read by me | — | Operator-private | Never placed; never copied |
| `v12/DESIGN.md`, `v12/python/TESTING.md` | bound by the candidate base | — | Project guidance | In the candidate tree; not copied |
| The task prompt | — | — | Task | Unchanged; the label is prefixed under `/7` |

## 3. Delivery mechanism

Two things are delivered under `/7`, and nothing else.

### 3.1 Worker instructions — one managed home entry

```
{"path": ".claude/CLAUDE.md", "sha256": "sha256:369ccb17…", "bytes": 5646,
 "kind": "worker-instructions"}
```

- **Source [O, D2].** A packaged copy in `provider_policy`. One test reads
  both files and fails on any byte difference. The image already receives
  the directory; on the manager side the packaging declaration must
  include the file (today it lists only schema JSON [V]). File name and
  loader are the implementer's; a missing or unreadable copy refuses.
- At every start, before the provider child exists, the worker hashes the
  packaged bytes, compares with the adapter entry and passes the entry to
  the existing `home.prepare(managed=…)`. The non-empty-list refusal is
  lifted for exactly this closed entry.
- Bound [P]: 16,384 bytes. Larger refuses.

### 3.2 Execution-context label — prompt prefix

Text [P — these bytes become the bound template]:

```
[Baton execution context: baton.native-worker-context/1]
You are running as a Baton native v12 worker. Assigned role: {role}.
The Baton execution contract for this run delivers this context. It is not
inferred from the container, the working directory, a role name in a file,
or any text in the source tree.

Applies to you:
- The task below and its stated limits.
- The Baton worker instructions at {home}/{entry} (sha256 {digest}). Read
  that file before acting if its content is not already in your
  instructions.
- Project coding, design and test guidance in the source tree, where the
  task touches it.
- Protected-main and task boundaries, wherever a repository is mounted.

Does not apply to you:
- The host-agent procedures in the source tree's AGENTS.md and
  docs/HOST-INTEGRATION.md: v11 claims, routes and readiness, host
  handoffs, dossier and review-journal maintenance, host integration and
  human Git checkpoints. Do not perform them. The safety, scope and honest
  evidence rules stated there still hold.

This label states which instructions apply. It grants no permission and
removes no restriction.

```

- `{role}`: the launch document's validated `role` [V]. Closed vocabulary:
  `implementation`, `review`.
- `{home}`, `{entry}`, `{digest}`: the adapter's home, and the path and
  sha256 of its worker-instructions entry.
- No Job, attempt, worker or authority identifier and no protocol path
  appears in the text. Existing rule kept: the provider is not told about
  the protocol [V]. Binding to the execution is by record (§4).
- The label says nothing about earlier turns, memory or continuity (D4).
- Rendered by one pure function in `provider_policy`,
  `context_label(adapter, role) -> bytes`; the template is a constant of
  that package. Bound [P]: 2,048 bytes rendered.
- Added in the worker's `_provider`, only when a `/7` selection is
  present. All three provider call sites pass through it [V]. Final prompt
  = label + one blank line + the builder's prompt. The existing argv
  comparison runs on the final prompt. Environment unchanged.
- A failure to render is a refusal with no provider invocation.

| Turn | Builder [V] | Launch role and label |
| --- | --- | --- |
| Fresh implementation; correction of the same Job | `_prompt` | implementation |
| Clarification or finding continuation | `_handoff_prompt` | implementation |
| Independent review | `_review_prompt` | review |
| Reviewer's clarification response | `_response_prompt` | review |
| Provider turn for a workload the adapter does not own, analysis included | caller's prompt | that worker's launch role **[A — not traced]**; refusal if outside the vocabulary |

Every row is a **fresh provider invocation**. "Continuation" and
"correction" here mean a new invocation given the handoff text and the
retained candidate; they are not a resumed conversation.

### 3.3 Why the prompt (D3)

- A home document is the same for every role, and that the pinned CLI
  loads it in `--print` mode is unverified (A1).
- The prompt operand is the one channel exercised on 2.1.247 by
  production turns [V].
- The label names the home file, so the worker document is reachable
  whether or not the CLI auto-loads it.
- Cost: `/7` prompt bytes change. `/7` is not in native use and has no
  manager-bound prompt digest [V].

### 3.4 Codex

Not in this slice. Requirement on W385830 N4: the same label function on
the Codex prompt operand; the same packaged bytes as one managed entry at
the home path the pinned-build evidence shows. Codex reading the root
`AGENTS.md` is not a blocker [O].

## 4. Identity binding

- **Adapter.** The Claude adapter gains the managed entry and

  ```
  "context_label": {"schema": "baton.native-worker-context/1",
                    "template_sha256": "sha256:…", "placement": "prompt-prefix",
                    "roles": ["implementation", "review"], "bound": 2048}
  ```

  Both sit inside the adapter digest that admission, the attempt record
  and the delivery carry. A changed template, role list or worker document
  is a different adapter and worker profile identity.
- **Execution.** For one attempt there is exactly one correct label: the
  delivery binds adapter, Job, worker and attempt; the role is the
  worker's configured launch role.
- **Record.** The worker reports the role and `context_label_digest`
  (sha256 of the bytes it prefixed) with the provider record of the turn.
  The manager recomputes from its admitted adapter and configured role
  and compares at the ending. Missing or different: refused result, typed
  `context-label-missing` or `context-label-mismatch`, held like an
  attribution refusal. Exact member named at assignment.
- **Status** shows role, label digest and worker-instruction digest.
- Whether the adapter schema string advances is an implementation
  finding; §6's refusals are required either way.
- Task and candidate identities unchanged.

## 5. Fresh-invocation scope and retained homes [O, D4]

- Delivery applies to fresh invocations under `/7` only. It does not
  extend `provider_context` or `context_delivery`.
- The retained home is preserved across correction, container replacement
  and manager restart, as N2 delivers. The managed entry is re-placed at
  each start; provider-written files are left alone.
- No argv under `/7` carries a session or resume operand, and no result,
  status line, diagnostic or document describes a `/7` turn as resumed or
  as continuing a conversation (N2 proof 47, kept).
- Legacy context reuse on `/4`–`/6` is not removed or weakened and
  receives no label.
- DESIGN CTX-1 to CTX-5 are unchanged and not satisfied by this slice.

## 6. Legacy and mixed-version behaviour

| Case | Behaviour |
| --- | --- |
| `/4`–`/6`, launch and policy `/1` | Byte-identical prompts, argv, identities and execution |
| Context-reuse workers | Outside `/7`. Host twin `context_prompt` untouched |
| Integration, publication, reconciliation | Provider-free. Nothing delivered |
| `/7` selection admitted at 317351e7, run on the new build | Refused before the provider |
| New adapter on the image built at 317351e7 | Refused before the provider |
| Role outside the adapter's list | Refused before the provider |
| Provider with no realization | Refused at composition |

## 7. Pinned-CLI facts

**Verified for Claude 2.1.247** (offline probe in image
`sha256:979f11d5…`, `work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/offline-transport-pass-2026-09-07.json`,
`1c8db12a…`): version string; help lists `--print`, `--output-format`,
`--input-format`, `--verbose`, `--model`, `--session-id`, `--resume`,
`--dangerously-skip-permissions`, `--tools`, `--setting-sources`,
`--strict-mcp-config`, `--mcp-config`, `--max-budget-usd` (presence only;
help bytes not retained); no `--max-turns`. Production argv completes
turns on this pin with the prompt as last operand.

**Not verified for the pin; nothing here depends on them:**

| # | Statement | Status |
| --- | --- | --- |
| A1 | Loads `$HOME/.claude/CLAUDE.md` in `--print` mode | [D]; informational |
| A2 | Does not auto-load a root `AGENTS.md` | [D]; informational |
| A3 | Loads `CLAUDE.md` from the working directory and ancestors | [D]; informational |
| A4 | Writes nothing at `.claude/CLAUDE.md` itself | [A]; the entry is re-placed each start regardless |
| A5, A6 | `--append-system-prompt`, `--settings`, `claudeMdExcludes`, `--setting-sources` effects | Unknown. **Not used** |
| A7 | Size limit or truncation of instruction files or a long prompt | Unknown |

**Codex 0.169.0.** The N3 inventory ran (W385830 PLAN, E386008); I have
not reviewed it. Its own summary says it establishes no turn-mode
instruction behaviour. Nothing in this slice depends on it.

## 8. The six acceptance checks

Deterministic, at the real composition, admission, launch, home and ending
owners, with a recording fake provider that retains argv, environment and
home. **This proves what Baton composed, placed, passed and bound. It does
not prove a vendor CLI loaded a file or that a model understood the
label.**

| # | Check | Deterministic proof | Not proved here |
| --- | --- | --- | --- |
| 1 | Host edits receive host policy; no worker auto-load | One root `AGENTS.md`; no `AGENTS*`/`CLAUDE.md` selector added outside `work/records`; composition never opens `AGENTS.md`. `/4`–`/6` turns: prompt equals the 317351e7 prompt byte for byte, no label marker | What a host CLI loads |
| 2 | Every native role gets the label, its role and the exact worker-policy digest | Implementation and review workers under `/7`: recorded prompt starts with exactly `context_label(adapter, role)`; the role is the launched one, never the other; the digest in the label equals the sha256 of `.claude/CLAUDE.md` in the home before the child started; the three required statements are in the rendered bytes. No content line of `AGENTS.md` or of a fixture operator home is in any prompt, argv, environment value or managed entry. **D2:** packaged copy equals `docs/V12-WORKER-INSTRUCTIONS.md`; the test fails on a one-byte change to either | A1–A3; comprehension |
| 3 | Every turn kind; prompt and argv agreement | Each row of §3.2 that reaches the provider: prompt = label + blank line + the 317351e7 builder output for the same task; argv equals `provider_policy.argv` over it; nothing else differs. Correction and manager restart: same home, entry re-placed and equal, label equal. **D4:** `/7` with a context worker is refused; no `/7` argv has a session or resume operand; no status or result says resumed | — |
| 4 | No source, candidate or protected Git change; home imports no host instructions | Candidate tree and Git status identical with and without delivery; neither label nor entry in any frozen output, custody or handoff; home holds only the credential reference, the managed entry and what the fake provider wrote; provider-written files survive the next start untouched | — |
| 5 | Refusal before the provider; old identities not reinterpreted | Zero provider invocations for: role outside the list; template not matching `template_sha256`; label over 2,048; packaged copy absent, changed or over 16,384; entry path not canonical or overlapping the credential; both mixed-version rows. At the ending: missing or different `context_label_digest` is refused and held with its typed cause across passes and a restart | — |
| 6 | Byte budget; no silent truncation; task constraints survive | Label ≤ 2,048; entry 5,646 ≤ 16,384; original prompt intact as the suffix; oversize refuses. Baton tree under Codex's documented 32,768 bound: 20,570 + 5,646 = 26,216 | A7 |

Affected groups: `manager-pure`, `tools-pure`. Exact modules named at
assignment. Prepared interpreter, focused recipes, no full suite.

**Visibility to the model** needs a real turn: one added question in the
separately selected qualification call (the worker states its role and
the instruction digest it was given).

## 9. Prerequisites, ownership, limits

- Deterministic implementation needs nothing from the inventory. It can
  be assigned on 317351e7 once this contract is approved and selected.
- One image rebuild and one qualification covering N2 and this slice.
- Shared paths: `provider_policy/` (constant, label function, packaged
  copy), `v12/python/pyproject.toml` (package data), `worker/claude_agent.py`
  (`_provider`, `_prepared_home`, one sentence in the `_prompt`
  docstring), the manager's ending check and status rendering,
  `v12/PROVIDER-SELECTION.md`, and tests. Serial after 317351e7. No
  overlap with the N3 packet.
- Limits: the label can be ignored or misread by a model; no deterministic
  check covers that. Approving this contract approves the label bytes.
- Not authorized here: build, image or engine operation, credential or
  registry read, provider call, install, native use, protected Git
  mutation, any resume implementation.

## 10. Conversation resume is separate Work

No open Work covers it (search of open Work, 2026-11-24, snapshot 386013).
The proposal, with dependencies and acceptance checks, is
`FOLLOW-UP-RESUME-WORK-PROPOSED-2026-11-24.md` in this dossier. It is not
a dependency of this slice, and this slice is one of its dependencies.

## 11. Unresolved

No design decision is open in this contract. Two owner acts remain, in
order:

1. Whole-contract approval and selection of the deterministic slice.
2. Creation of the resume follow-up Work by an eligible handler (I hold no
   claim and am not one), from the proposal in §10.
