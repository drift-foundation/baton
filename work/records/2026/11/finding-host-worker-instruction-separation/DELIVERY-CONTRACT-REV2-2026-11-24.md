# W385853 — bounded worker-instruction delivery contract, revision 2 (proposed)

Author: baton.prompt (K, model Fable 5.2), interactive copilot, no claim.
2026-11-24. Base: checkpoint `317351e73c92749e201f536ba115c9fdf213077d`.
Status: **proposed; nothing here is implemented, selected or qualified.**
Reading only. No code, image, engine, credential, registry or provider.

Revises `DELIVERY-CONTRACT-PROPOSED-2026-11-24.md` (sha256 `5232ba50…`,
unchanged, kept as history) for the owner ruling in FINDING, "owner selects
explicit native execution-context label". Sections 1, 2 and 7 of the first
contract stand as written and are not repeated. Sections 3, 4, 5, 6, 8, 9
and 10 are replaced by this file.

Marks: **[V]** verified in this repository's code or retained evidence;
**[D]** vendor documentation, not verified on the pinned build;
**[A]** assumption; **[P]** proposed here.

## 0. What changed

| | First contract | Revision 2 |
| --- | --- | --- |
| D1 | Open | **Settled by the owner:** no mechanical exclusion of the source `AGENTS.md` |
| Exclusion | Non-placement plus self-scoping text | Non-placement plus a delivered **execution-context label** that names the role and says which host-only instructions do not apply |
| Prompts | Unchanged | Under `/7` only: the label is a fixed prefix; the rest of each prompt is byte-identical |
| D3 | Open: home file alone? | Reviewed against the ruling (§3.3): the label travels in the prompt, the one channel verified on the pin. The home file no longer gates native use |
| Worker document | One managed home entry | Unchanged |
| Open decisions | D1–D4 | D2 next, then D4 (§9) |

## 1. Two delivered things

1. **Worker instructions** — the exact bytes of
   `docs/V12-WORKER-INSTRUCTIONS.md` (sha256 `369ccb17…`, 5,646 bytes), one
   managed home entry at `.claude/CLAUDE.md`, as in the first contract §3.
   Same for every role.
2. **Execution-context label** — new. A short model-facing text that says:
   this is a native v12 worker run, the assigned role, what applies, and
   which host-only procedures do not. Rendered per run from a closed
   template. Delivered at the front of the prompt.

Nothing else is delivered. Baton still never places `AGENTS.md`,
`docs/HOST-INTEGRATION.md` or anything from an operator home. If a CLI or a
model reads the root `AGENTS.md` from the candidate tree, that is accepted;
the label is what tells the worker how to treat it.

## 2. The label

### 2.1 Text [P — draft; these bytes become the bound template]

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

- Substitutions, all from validated inputs, none from the environment,
  the working directory or a file:
  - `{role}`: the launch document's validated `role` [V: `baton_worker`
    validates it; the manager fills it from the worker's configured launch
    role]. Closed vocabulary for this slice: `implementation`, `review`.
  - `{home}`, `{entry}`, `{digest}`: the adapter's `home`, and the path and
    sha256 of its worker-instructions managed entry.
- The text carries **no** Job, attempt, worker or authority identifier and
  no protocol path. Existing rule kept: the provider is not told about the
  protocol [V: `_prompt` docstring]. Execution binding is by record (§4),
  not by printing identifiers to the model.
- One blank line follows the label, then the existing prompt.
- Bound [P]: rendered label at most 2,048 bytes. Larger refuses.
- "Read that file" makes the worker document reachable through the prompt
  whether or not the CLI auto-loads the home file (assumption A1).

### 2.2 Roles and turn kinds

The label names the **launch role**. The turn kind is already said by the
existing prompt builders, which are unchanged:

| Turn | Builder [V] | Launch role | Label |
| --- | --- | --- | --- |
| Fresh implementation | `_prompt` | implementation | implementation |
| Correction of the same Job | `_prompt` | implementation | implementation |
| Clarification or finding continuation | `_handoff_prompt` | implementation | implementation |
| Independent review | `_review_prompt` | review | review |
| Clarification response by the reviewer | `_response_prompt` | review | review |
| Provider turn for a workload the adapter does not own (`_provider(None, …)`, includes analysis) | caller's prompt | the launch role of that worker **[A]** — I did not trace which roles reach it | that role, or refusal if outside the vocabulary |
| Context restore | `_prompt` with feedback | — | Not under `/7` (D4) |

Integration, publication and reconciliation workers run no provider and get
no label.

## 3. Delivery mechanism [P]

### 3.1 Where the label is added

- In the worker's `_provider`, only when a `/7` provider selection is
  present. All three provider call sites pass through it [V], and it is
  where the actual argv is compared with `provider_policy.argv(adapter,
  selection, prompt)`.
- The label is rendered by one pure function in the shared
  `provider_policy` package:
  `context_label(adapter, role) -> bytes`. The manager imports the same
  function. The template text is a constant of that package.
- Final prompt = label + blank line + the builder's prompt. The argv check
  runs on the final prompt. Argv differs from 317351e7 only in that last
  operand. Environment unchanged.
- No turn under `/7` may reach the provider child without the label: the
  render happens before the argv comparison and a failure to render is a
  refusal with no provider invocation.

### 3.2 Where the worker document is placed

Unchanged from the first contract §3: one closed managed entry, digest
checked against the package bytes, placed by the existing
`home.prepare(managed=…)` at every start, 16,384-byte bound, the
non-empty-list refusal in `_prepared_home` lifted for exactly this entry.

### 3.3 D3 reviewed against the ruling

- A home document is the same bytes for every role, so it cannot identify
  the role. And that the pinned CLI loads it in `--print` mode is not
  verified (A1).
- The prompt operand is the one channel known to reach the model on
  2.1.247: production turns act on it [V, by exercise].
- Therefore: label in the prompt; worker document in the home and named by
  the label. A1 becomes an observation for the inventory, not a gate.
- Cost accepted by this design: `/7` prompt bytes change. No `/7`
  deployment is in native use and `/7` has no manager-bound prompt digest
  (that exists only for context turns, which `/7` refuses) [V].

### 3.4 Codex

Not in this slice; no realization exists. Requirement on N4: the same label
function, added to the prompt operand of the Codex invocation; the same
worker bytes as one managed entry at the home path the N3 inventory shows.
Per the ruling, Codex loading the root `AGENTS.md` is not a blocker.

## 4. Identity binding [P]

- **Adapter.** The Claude adapter document gains one member:

  ```
  "context_label": {"schema": "baton.native-worker-context/1",
                    "template_sha256": "sha256:…", "placement": "prompt-prefix",
                    "roles": ["implementation", "review"], "bound": 2048}
  ```

  and its `managed_entries` gains the worker-instructions entry. Both are
  inside the adapter digest that admission, the attempt record and the
  provider delivery already carry [V]. A changed template, role list or
  worker document is a different adapter digest and worker profile.
- **Execution.** The rendered label is a pure function of the adapter and
  the role. The provider delivery already binds adapter digest, Job,
  worker and attempt, and is validated against `job_execution` before any
  turn [V]. So for one attempt there is exactly one correct label.
- **Record.** The worker reports `context_label_digest` (sha256 of the
  bytes it actually prefixed) and the role, with the provider record it
  already writes for the turn. The manager recomputes the digest from its
  own admitted adapter and the worker's configured role and compares at
  the ending. A missing or different digest is a refused result, typed
  `context-label-missing` or `context-label-mismatch`, held like an
  attribution refusal. The exact record member is named at assignment.
- **Status** shows the role, the label digest and the worker-instruction
  digest beside the existing provider diagnostics.
- Whether the added adapter member advances the adapter schema string is
  an implementation finding. Required either way: §5's refusals.
- Task identity and candidate identity are unchanged.

## 5. Legacy and mixed-version behaviour

| Case | Behaviour |
| --- | --- |
| Deployments `/4`–`/6`, launch and policy `/1` | Byte-identical prompts, argv, identities and execution. No label, no worker document |
| Context-reuse workers | Outside `/7`. No label. Host twin `context_prompt` untouched (D4) |
| Integration, publication, reconciliation | Provider-free. Nothing delivered |
| `/7` selection admitted at 317351e7 (no label member), run on the new build | Refused before the provider: not this build's realization |
| New adapter on the image built at 317351e7 | Refused before the provider: non-empty managed list; adapter differs from that build's realization |
| Role outside the adapter's role list | Refused before the provider |
| A provider with no realization | Refused at composition, as now |

Nothing is reinterpreted silently.

## 6. The six acceptance checks, revised

Deterministic, at the real composition, admission, worker launch, home and
ending owners, with a recording fake provider that retains the argv, the
environment and the home it was given. **This proves what Baton composed,
placed and passed. It does not prove a vendor CLI loaded a file, or that a
model understood the label.**

| # | Check | Deterministic proof | Not proved here |
| --- | --- | --- | --- |
| 1 | Host edits receive host policy; no worker auto-load | Static: one root `AGENTS.md`; no `AGENTS*`/`CLAUDE.md` selector added outside `work/records`; composition never opens `AGENTS.md`. `/4`–`/6` turns: recorded prompt equals the 317351e7 prompt byte for byte and contains no label marker | What a host CLI loads |
| 2 | Every native role gets the label, the right role and the exact worker-policy digest | For an implementation worker and a review worker under `/7`: the recorded prompt starts with exactly `context_label(adapter, role)`; the role in it is the launched role and never the other; the digest printed in the label equals the sha256 of `.claude/CLAUDE.md` found in the home before the child started (`369ccb17…`). The label contains the three required statements (native worker, role, host-only procedures do not apply) — asserted on the rendered bytes. No content line of `AGENTS.md` or of a fixture operator home appears in any prompt, argv, environment value or managed entry (the *name* `AGENTS.md` does appear, in the label) | That the CLI auto-loads the home file (A1); what the CLI finds in the tree (A2, A3); comprehension |
| 3 | Every turn kind; prompt and argv agreement | For each row of §2.2 that reaches the provider: recorded prompt = label + blank line + the prompt the same builder produces at 317351e7 for the same task; argv equals `provider_policy.argv` over that prompt; nothing else in argv differs. Correction and manager restart: same home, entry re-placed and equal, label equal. A worker of one role reusing nothing of the other's home [V by N2] . Context restore: `/7` with a context worker refused (D4) | — |
| 4 | No source, candidate or protected Git change; home imports no host instructions | Candidate tree and Git status identical with and without delivery; neither label nor entry appears in any frozen output, custody or handoff; home holds only the credential reference, the managed entry and what the fake provider wrote | — |
| 5 | Refusal before the provider; old identities not reinterpreted | Zero provider invocations for each: role outside the list; template bytes not matching `template_sha256`; rendered label over 2,048 bytes; worker-document bytes absent, changed or over 16,384; entry path not canonical or overlapping the credential; both mixed-version rows of §5. At the ending: a result without `context_label_digest`, or with one that differs from the manager's recomputation, is refused and held with its typed cause, across passes and a restart | — |
| 6 | Byte budget over the selected chain; no silent truncation; task constraints survive | Asserted for what Baton composes: label ≤ 2,048; entry 5,646 ≤ 16,384; final prompt = label + original, original bytes intact as a suffix. Oversize refuses, never truncates. For the Baton tree under Codex's documented shared 32,768 bound: 20,570 + 5,646 = 26,216 (label is in the prompt, outside that bound) | Whether either pinned CLI truncates instruction files or a long prompt (A7) |

Affected groups: `manager-pure`, `tools-pure`. Exact modules named at
assignment. Prepared interpreter, focused recipes. No full suite.

**Visibility to the model** can only be shown by a real turn: one added
question in the separately selected qualification call, asking the worker
to state its role and the worker-instruction digest it was given. Until
then the claim is "composed, placed, passed and bound".

## 7. Prerequisites and coordination with W385830

- Deterministic implementation needs nothing from the inventory.
- Inventory items I1–I6 (posted on T385830 seq 386004) change standing:
  - I1 (home file auto-loaded) and I2 (tree files auto-loaded): now
    **informational**, no longer gates. D1 is settled and the label names
    the home file.
  - I3 (home paths the program rewrites), I4 (help bytes retained), I5
    (size limits) stand.
  - I6 becomes: the qualification turn carries the one question above.
    Live call; selected separately.
- One image rebuild and one qualification covering N2 and this slice, as
  before.
- Shared paths: `provider_policy/__init__.py`, `worker/claude_agent.py`
  (`_provider`, `_prepared_home`), the manager's ending check and status
  rendering, `v12/PROVIDER-SELECTION.md`, and their tests. The `_prompt`
  docstring's statement of what the provider is told needs one sentence
  for the label. Serial after 317351e7; codxpc's N3 packet does not touch
  these (T385853 seq 385999).
- N4 inherits §3.4.

Not authorized by this contract: any build, image or engine operation,
credential or registry read, provider call, install, native use, protected
Git mutation.

## 8. Limits stated plainly

- The label is instruction applicability. It is not a security boundary
  and grants nothing (owner ruling). Protected-main and task boundaries
  are enforced where they already are, not by this text.
- A model can ignore or misread the label. No deterministic check covers
  that.
- The label wording in §2.1 is my draft of the ruling. Approving this
  contract approves those bytes.

## 9. Unresolved decisions

**Next: D2 — where do the delivered worker-instruction bytes live?**
(The label template is a constant of `provider_policy` and is not part of
this question.)

- A byte-identical copy inside `provider_policy`, with a test that fails
  if it differs from `docs/V12-WORKER-INSTRUCTIONS.md` (recommended).
  Keeps N2's closed table, the worker's own rebuild check, and the image
  build context (`v12`).
- Move the canonical document into the package and repoint `AGENTS.md`:
  one file, but reopens the accepted editorial import.
- Manager supplies the bytes at composition: no copy, but the worker can
  no longer rebuild the adapter itself, which weakens N2's check.

After D2, one remains: **D4** — context-reuse turns are outside this
delivery because `/7` refuses context workers; confirm, or select
extending `/7` first.
