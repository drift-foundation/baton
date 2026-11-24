# W385830 — proposed implementation contract, revision 5 (delta)

Author: baton.prompt (K, model Fable 5.2), interactive copilot, no claim.
2026-11-23. Authority: M385851 and the FINDING entry "Codex CLI pin
selected — owner 2026-11-23".

**PROPOSED — NOT APPROVED.** Research and design only. Nothing built,
launched or tested; no provider call; no credential read.

Base text: `IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-23.md` as amended by
`-REV2-`, `-REV3-` and `-REV4-`; all four preserved unchanged. This file
folds in the Codex pin, replaces the "every evidenced source" rule of REV4
§2 with the owner's participation rule, amends the N1 verification list,
and raises the next decision.

## 1. Settled

| Settled by the owner | Source |
| --- | --- |
| **Codex CLI 0.169.0** is the pin for the Codex worker image | M385851 |
| The retained host flag inventory is preparation evidence, not proof of container compatibility | M385851 |
| The exact pinned build is qualified in the selected container posture before any native use | M385851 |
| The pin authorizes no build, credential access or provider call | M385851 |
| Contributors are collected **only from provider fields that evidence actual model participation in this invocation** — not from arbitrary model-name mentions in output | M385851 |
| No primary designation. A single-model field that names another contributor is not by itself conflicting when the requested model is also evidenced among the contributors | M385851 |
| Source evidence is preserved. Participation is never inferred from request or configuration text | M385851 |

## 2. The Codex pin (amends first contract §4.5, §4.6, §6.2, F13)

| Where | What the pin fixes |
| --- | --- |
| Image recipe | `Dockerfile.codex` installs exactly 0.169.0. A version gate test refuses any other build, as the Claude image's does |
| Worker profile | "CLI build, selected" for a Codex worker is 0.169.0; the worker measures the installed build and anything else is `conflicting` (REV3 §2.1) |
| Adapter | Written against the 0.169.0 inventory **taken inside the image** at the engine-only gate. The host captures in `evidence/research-385843/` guide the draft only; no flag, event shape or file location is fixed from them |
| Qualification | Unchanged in content: the engine-only gate, then real-provider question Q1, both on this exact build under the v12 posture. Neither is selected yet (D7) |

Still not established for 0.169.0, and not assumed: that it starts under a
read-only root; where it requires its home; whether it accepts a linked
credential; what it reports as model evidence. The August spike's findings
(F9, F10) were measured on 0.150.1 and are carried as questions for this
build, not as facts about it.

## 3. Contributor evidence (replaces REV4 §2 "every evidenced source feeds the same set")

### 3.1 Participation sources

Each provider adapter carries a **closed list of participation sources**
for its pinned build: the exact fields of the provider's own structured
output whose meaning, by the provider's own semantics, is "this model did
work in this invocation". Contributors are read from those fields and
nowhere else.

| Class of text | Collected? |
| --- | --- |
| A field in the list — for example a per-model usage entry, or the model named on a generated response | Yes |
| The requested selector, the argv, the launch document, the worker profile | Never |
| Provider output that echoes configuration: a start-up or settings record naming the model the session was configured with | Never — it restates the request |
| Model names in generated text, tool input or output, file contents, prompts, error messages | Never |
| A structured field naming a model that is not in the list | Never; it is left in the retained raw output |

Consequences:

- The list is part of the adapter, reviewed with it, and covered by the
  adapter identity digest (REV2), so two workers that disagree about what
  counts as evidence have different identities.
- The list is per pinned build. It is established from that build's
  inventory and its qualification output, not from another build's shape.
  For Claude 2.1.247 the retained September evidence shows per-model usage
  entries and no direct model field (F5); which of its fields qualify is
  confirmed against real output at Q2. For Codex 0.169.0 nothing is known
  until Q1.
- An adapter whose list is empty cannot produce a contributor, so every
  result is `missing`. That is the fail-closed starting state.

### 3.2 No primary; a differing single-model field

All participation sources feed one contributor set (REV4 §2: sorted, each
identity once, no quantity, no role). A source that names exactly one model
is one more source, not a ruling on which model "the" model was:

| Read from participation sources | Outcome |
| --- | --- |
| Requested model's mapped identity present; a single-model field names another model | **matched**; both are contributors |
| Mapped identity absent; any other contributors present | conflicting |
| Mapped identity appears only in non-participation text (a configuration echo, generated text) | conflicting if other contributors were read; missing if none |
| No participation source readable | missing |

### 3.3 Preserving the source evidence

The record gains one member (amends REV4 §2):

| Member | Meaning |
| --- | --- |
| **contributor sources** | For each contributor, the names of the participation sources it was read from. Names of fields only — no values, quantities or content |

With the existing evidence digest and retained log, a reader can go from a
contributor to the field it came from to the exact provider bytes. The
source names say where an identity was evidenced; they carry no rank.

## 4. Verification for N1 (amends REV3 §3 as amended by REV4 §5)

REV4 item 4 is replaced; items 23–29 are added. All others stand.

4. Contributors are read from each participation source alone, from
   several agreeing, and from several naming different models; each yields
   the union. With no participation source present the outcome is
   `missing`.
23. A model name appearing only in generated text, in tool output, in an
    error message or in the echoed prompt is not collected.
24. A configuration-echo record naming the requested model, with no
    participation source naming it, does not produce `matched`: the outcome
    is `conflicting` when other contributors were read and `missing` when
    none were.
25. A single-model participation field naming model Y while a usage source
    names the requested model X → `matched`, contributors X and Y.
26. The same field naming Y with X evidenced nowhere → `conflicting`.
27. A structured model-naming field that is not in the adapter's list is
    ignored and remains in the retained raw output.
28. The record names, per contributor, the participation sources it came
    from; those names are fields of the adapter's list and the record still
    carries no quantity, role or content.
29. Changing an adapter's participation-source list changes that worker's
    adapter identity digest.

## 5. What is now specifiable

| Slice | State |
| --- | --- |
| N1 | Specified. Each adapter's participation-source list starts from retained evidence and is confirmed at qualification; the deterministic tests use fixture output |
| N2 | Specified (REV2) |
| N3 | Codex pin settled. Still blocked on D6 and D3 |

## 6. The next decision for the owner

**Where does a provider that needs a writable home directory get one?**
(D6.)

Why it is needed. The v12 container has a read-only root; its private
writable memory is small non-executable scratch under `/tmp`; its one
writable disk location is the manager-owned work area
(`worker_manager/oci.py`, the restriction table). The August spike measured
that Codex would not start with its state directory read-only and refused a
home under a temporary directory. That was 0.150.1; 0.169.0 is unmeasured,
but the adapter and the image recipe have to be written toward one answer.

- **A — One additional private memory mount at the provider's home path,
  only for workers whose deployment declares it (recommended).** Same
  protections as the existing scratch (private to the container, no
  executables, no device or set-id files, size-bounded), gone when the
  container is destroyed, never collected as output. The credential stays a
  read-only delivered file; the adapter links it into the home. Claude
  workers and every existing composition get exactly today's container.
  Cost: one narrow, declared addition to the posture table, with a test
  that it is absent unless declared.
- **B — Put the home inside the existing writable disk work area.** No
  change to the posture table. Cost: provider state, and a link to the
  credential, sit on host disk in a manager-owned directory that outlives
  the container, next to material that is retained and collected. Keeping
  them out of custody and cleaning them up becomes this change's job.
- **C — Decide after the engine-only gate has shown what 0.169.0 actually
  requires.** No design commitment before facts. Cost: N3 cannot be written
  until that gate is selected and run, and the gate itself needs some home
  arrangement to test.

I recommend A. I have not assumed it. Approving A approves the mechanism
only; the mount's size is a value I would bring back from the image gate's
measurement rather than guess, and nothing is built or run by it.

## 7. Decisions still open after that

| # | Decision | Unblocks |
| --- | --- | --- |
| D3 | Codex credential kind and registry reference | N3, N5 |
| D1 (Claude) | Whether the Claude pin stays on 2.1.247 or moves | N4 |
| D2 (values) | Selector and mapped identity for the Fable reviewer and for the Codex implementer | N5 |
| D7 | Selection of the engine-only image gates and the two real-provider calls | N4, N5 |

## 8. Limits

- Nothing executed.
- Which concrete fields qualify as participation sources is not fixed here
  for either build. The examples in §3.1 are classes, not a list.
- Not settled, and I have not chosen: whether a per-model usage entry whose
  reported quantities are all zero evidences participation. Neither
  retained output shows one. If a pinned build produces such entries at
  qualification, I will bring that as a question with the output.
- Leaving usage quantities out of the record remains my reading of "no
  primary designation" (REV4 §9); M385851 did not address it.
- The posture description in §6 is from the restriction table and its
  comments; I did not trace every mount the run vector composes.
