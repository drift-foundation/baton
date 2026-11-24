# W385853 — bounded worker-instruction delivery contract (proposed)

Author: baton.prompt (K, model Fable 5.2), interactive copilot, no claim.
2026-11-24. Base: checkpoint `317351e73c92749e201f536ba115c9fdf213077d`.
Status: **proposed; nothing here is implemented, selected or qualified.**
Reading only. No code, image, engine, credential, registry or provider.

This contract delivers the accepted worker instructions to native workers
through N2's managed home entries and binds them through N2's adapter
identity. It covers the six checks in
`evidence/consolidation-385856/LOADING-BOUNDARIES.md` (sha256 `09ebac37…`).
Four decisions are open; they are in §10 and nowhere else.

Marks: **[V]** verified in this repository's code or retained evidence;
**[D]** stated by vendor documentation, not verified on the pinned build;
**[A]** assumption; **[P]** proposed here.

## 1. What N2 already provides at 317351e7 [V]

Read from `provider_policy/__init__.py` (`52b4b188…`),
`provider_policy/home.py` (`56b2d7db…`), `worker/claude_agent.py`
(`6cf404df…`) and `tools/single_worker.py`.

- Adapter `baton.single-implementation-adapter/2` has a `managed_entries`
  member. It is `[]` for every selection today.
- The adapter is a pure function of the selection in the shared
  `provider_policy` package. Manager and worker each rebuild it and refuse
  any difference ("adapter is not this build's selected realization").
- The adapter digest is carried by the provider delivery, the attempt
  record and admission.
- `home.prepare(managed=…)` already places `(path, bytes, sha256)` entries:
  canonical relative path only, digest checked, atomic replace at every
  start, refusal if a path overlaps the credential or a declared
  provider-owned path. Production passes none.
- The worker's `_prepared_home` refuses a non-empty list: "managed-entry
  delivery is not selected by this build".
- The home is never seeded from the operator home; composition refuses a
  home root under the operator's `~/.claude` or `~/.codex`.
- Provider selection exists only under deployment `/7`. `/7` refuses
  context-reuse workers and publication workers. Only the Claude
  realization exists; there is no Codex realization.

## 2. Instruction files, exactly

| File | sha256 at 317351e7 | Bytes | Class | Native worker |
| --- | --- | --- | --- | --- |
| `docs/V12-WORKER-INSTRUCTIONS.md` | `369ccb173d0bec1b4ba109127677d611d36e327e17f11b82c3bf13bf2f28627b` | 5,646 | Worker policy | **Delivered, exact bytes** |
| `AGENTS.md` | `e9e3416d7a6c3dca4206c2379f6031fef79a92926a05ad64781e86c6d6aa8421` | 20,570 | Host-only | Never placed by Baton |
| `docs/HOST-INTEGRATION.md` | `7d33a568cbdef9e309159c0daed7413eb5490b0547fce7b86e926e89fcafa68e` | 1,287 | Host-only, read when selected | Never placed by Baton |
| Operator `~/.claude/CLAUDE.md`, anything under operator `~/.claude` or `~/.codex` | not read by me | — | Operator-private | Never placed; never copied |
| `v12/DESIGN.md`, `v12/python/TESTING.md` | bound by the candidate base | — | Project guidance the worker document refers to | In the candidate tree; read by reference; not copied |
| The task prompt | bound by task and prompt digests | — | Task | Unchanged, byte for byte |

One worker document serves every role. No other file is delivered.

## 3. Loading mechanism [P]

**Claude.** One managed entry in the Claude realization:

```
{"path": ".claude/CLAUDE.md", "sha256": "sha256:369ccb17…", "bytes": 5646,
 "kind": "worker-instructions"}
```

- The bytes come from the shared `provider_policy` package, which the
  manager imports and the image already copies whole (decision D2 selects
  how they get there).
- At every start, before the provider child exists, the worker hashes the
  package bytes, compares with the adapter entry, and passes the entry to
  the existing `home.prepare(managed=…)`. The refusal of a non-empty list
  is removed for exactly this closed entry.
- The path does not overlap the credential (`.claude/.credentials.json`).
- Entry bound [P]: 16,384 bytes. Larger refuses.
- Argv, environment and every prompt are **not changed**.

**Codex.** Not in this slice. There is no Codex realization to add an entry
to. The requirement placed on N4: its realization declares one managed
entry with the same bytes, at the home file the N3 inventory shows
Codex 0.169.0 loads. The path is not written here.

**What makes the CLI read the entry.** Claude Code loads
`$HOME/.claude/CLAUDE.md` as user-level instructions **[D]**. That this
happens on 2.1.247 in `--print` mode in the worker container is **[A]**
(assumption A1, §7). Baton placing the file is provable. The CLI loading
it is not provable with a fake provider.

## 4. Exclusion mechanism [P]

Three parts. Only the first two are mechanical.

1. **Non-placement [V].** Baton places exactly the closed managed list and
   the credential reference. The home is never seeded from the operator
   home. No host file can arrive through Baton's composition.
2. **No selector.** No `AGENTS`-named or `CLAUDE.md`-named file is added
   under `v12/`; nothing in composition reads `AGENTS.md`; the worker
   document is not an auto-load filename in the source tree.
3. **Self-scoping text [V, already imported].** `AGENTS.md` opens by saying
   it applies to host agents and that a native worker follows its delivered
   contract instead. The worker document says it applies only when
   delivered. If a CLI or a model reads the root file from the candidate
   tree, the file itself says it does not govern.

What this contract does **not** do: suppress the CLI's own discovery of
files in the candidate tree. Doing so would also drop project guidance the
worker needs. No flag or setting is specified for it, because none is
verified on the pinned build (§7). Whether part 3 is sufficient exclusion
is decision D1.

**Retained home.** The managed entry is re-placed at every start, so a
provider or model cannot durably alter it. Other instruction-bearing files
a provider may write into its own home are not removed (owner ruling S12 of
the W385830 contract). A home is bound to one Job and one worker, so
nothing carries between Jobs or between implementation and review.

## 5. Identity binding [P]

- The entry is part of the adapter document, so the worker-instruction
  digest is inside the adapter digest that admission, the attempt record
  and the provider delivery already carry. No new identity is introduced
  and no schema number changes.
- A different instruction revision is a different adapter digest and a
  different worker profile identity.
- Status shows the delivered instruction digest beside the existing
  provider diagnostics [P]. No new record.
- Task identity, prompt digests, argv digests and candidate identity are
  unchanged.

## 6. Legacy and mixed-version behaviour

| Case | Behaviour |
| --- | --- |
| Deployments `/4`–`/6`, launch and policy `/1` | Byte-identical identities and execution; they never enter `provider_policy`. No instruction delivery |
| Context-reuse workers | Outside `/7` (refused by N2). No instruction delivery in this slice (decision D4) |
| Publication, integration, reconciliation workers | Provider-free. Nothing delivered |
| `/7` selection admitted before this change (empty list), run on the new build | Refused before the provider: the adapter is not this build's realization |
| New adapter (one entry) on the image built at 317351e7 | Refused before the provider by the existing non-empty-list refusal |
| A provider with no realization | Refused at composition, as now |

Nothing is reinterpreted silently. No `/7` deployment is in native use, so
no admitted work is stranded.

## 7. Pinned-CLI facts: verified, documented, assumed

**Verified for Claude 2.1.247** — source: retained offline probe inside
image `sha256:979f11d5…`, no credential, network or model call
(`work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/offline-transport-pass-2026-09-07.json`,
sha256 `1c8db12a…`):

| Fact | Extent |
| --- | --- |
| Reports `2.1.247 (Claude Code)` | Verified |
| Help lists `--print`, `--output-format`, `--input-format`, `--verbose`, `--model`, `--session-id`, `--resume`, `--dangerously-skip-permissions`, `--tools`, `--setting-sources`, `--strict-mcp-config`, `--mcp-config`, `--max-budget-usd` | Presence in help only. The help bytes were not retained, only their digest |
| Help does not list `--max-turns` | Verified |
| Production argv `--print --dangerously-skip-permissions --output-format json <prompt>` completes turns with the credential at `$HOME/.claude/.credentials.json` | Exercised by production runs on this pin |

**Not verified for 2.1.247. Nothing in this contract depends on these
except A1.**

| # | Statement | Status |
| --- | --- | --- |
| A1 | Loads `$HOME/.claude/CLAUDE.md` in `--print` mode | [D] generally; [A] for the pin |
| A2 | Does not auto-load a root `AGENTS.md` (vendor guide: direct loading needs 2.1.277 or later) | [D]; [A] for the pin |
| A3 | Loads `CLAUDE.md` files from the working directory and its ancestors | [D]; [A] for the pin. The Baton tree has none; other source repositories may |
| A4 | Writes nothing at `.claude/CLAUDE.md` by itself | [A] |
| A5 | `--append-system-prompt`, `--settings`, `claudeMdExcludes` exist and behave as in the host 2.1.330 help | Unknown. Not probed on the pin. **Not used** |
| A6 | What `--setting-sources` does to instruction-file loading | Unknown. **Not used** |
| A7 | Any size limit or truncation applied to instruction files | Unknown |

**Codex 0.169.0.** Nothing is verified in an image. Host help captures
(`evidence/research-385843/` of W385830) are a different installation.
Vendor documentation **[D]**: global guidance from the Codex home, then
project root to working directory, 32 KiB default bound. On that reading
Codex *does* load the root `AGENTS.md` of a Baton candidate; this is why
D1 matters most for Codex.

## 8. The six acceptance checks

Deterministic, at the real composition, admission, worker launch and home
owners, with a recording fake provider. **A fake provider proves what Baton
composed and placed. It proves nothing about what a vendor CLI discovers
or loads.** Each check says which.

| # | Check (LOADING-BOUNDARIES) | Deterministic proof | Not proved here |
| --- | --- | --- | --- |
| 1 | Host edits receive host policy; no worker auto-load | Static: the tracked tree holds one root `AGENTS.md` and no `AGENTS*`/`CLAUDE.md` selector outside `work/records`; composition code never opens `AGENTS.md`; legacy and host paths place no worker document | What a host CLI loads |
| 2 | Every native role gets the exact worker-policy digest; host-only sentinel absent | Under `/7`, for each role in check 3: before the provider child starts, `.claude/CLAUDE.md` in the retained home has sha256 `369ccb17…`; status reports that digest. A sentinel planted in a fixture operator home, and the first line of `AGENTS.md`, appear in no prompt, argv, environment value or managed entry | That the CLI read the entry (A1); what the CLI finds in the candidate tree (A2, A3) |
| 3 | Fresh implementation, independent review, analysis, clarification response, continuation, context restore; matching prompt and argv digests | Each `/7` role that reaches the provider turn has the entry in place first. Prompt and argv digests for the same task equal those at 317351e7. Correction and manager restart reuse the home with the entry re-placed and equal. Context restore: `/7` with a context worker is refused (D4) | — |
| 4 | No source, candidate or protected Git change; private home imports no host instructions | Candidate tree and Git status are identical with and without delivery; the entry is in no frozen output, custody or handoff; the home holds only the credential reference, the managed entry and what the fake provider wrote; fixture operator sentinel absent | — |
| 5 | Missing, changed, oversized or unsupported policy or selector refuses before the provider; old identities not reinterpreted | Each refuses with zero provider invocations: package bytes absent; package bytes not matching the adapter digest; entry over the bound; path not canonical or overlapping the credential; entry not in the closed realization; both mixed-version rows of §6 | — |
| 6 | Byte budget over the whole selected chain; no silent truncation; task constraints survive | Accounting computed and asserted for what Baton composes: entry 5,646 ≤ 16,384; prompt unchanged. For the Baton tree under Codex's documented shared 32,768 bound: 20,570 + 5,646 = 26,216. Oversize refuses rather than truncates | Whether either pinned CLI truncates, and at what size (A7) |

Affected groups: `manager-pure`, `tools-pure`. Exact modules are named at
assignment. Prepared interpreter, focused recipes. No full suite.

**Vendor loading (A1–A4, A7)** is established only by the pinned-image
inventory or, where a turn is needed, the selected qualification call
(§9). Until then the delivery is "placed and bound", not "loaded".

## 9. Prerequisites and coordination with W385830

- **Deterministic implementation needs nothing from the inventory.**
  W385965 is closed satisfying; this slice can be assigned on 317351e7.
- **Native use needs these from the N3 pinned-image inventory**, for
  Claude 2.1.247 and Codex 0.169.0:
  - I1: whether the home instruction file is loaded in the non-interactive
    mode the adapter uses, and its exact path (A1; the Codex path).
  - I2: which files in the working directory and its ancestors are loaded
    by the program itself (A2, A3).
  - I3: which home paths the program creates or rewrites on start (A4).
  - I4: the full help text retained as bytes, not flag booleans.
  - I5: any observable size limit on instruction files (A7).
  - I6: which of I1, I2, I5 can be observed without a provider call. Those
    that cannot move to the qualification turn as one added sentinel
    question. That is a live call and is selected separately.
- **One image rebuild, not two.** This slice changes the worker and the
  shared package, so the Claude image must be rebuilt for it. N2's bytes
  are also not yet packaged. If packaging and qualification of N2 are
  selected before this slice is accepted, a second rebuild and a second
  qualification follow. Proposed order: this slice accepted, then one
  packaging and one qualification covering both.
- **Shared paths:** `provider_policy/__init__.py`, `worker/claude_agent.py`
  (`_prepared_home`), status rendering in `tools/job_observation.py`,
  `v12/PROVIDER-SELECTION.md`, and their tests. Serial after 317351e7; no
  other Work holds them now.
- N4 (Codex adapter) inherits the requirement in §3 and decision D1.

Not authorized by this contract: any build, image or engine operation,
credential or registry read, provider call, install, native use, protected
Git mutation.

## 10. Unresolved decisions

D1 can change the design. D2–D4 are independent of each other.

**D1 — Is self-scoping text sufficient exclusion of the host-only root
`AGENTS.md`?**
- Yes (recommended): exclusion is non-placement plus the applicability
  statements already in both documents. Works on any build and keeps
  project guidance.
- No: mechanical exclusion is required. For Claude no mechanism is verified
  on the pin; it waits for the inventory and may need a pin move. For
  Codex the documented choices drop all project guidance or none, so this
  is a capability gap that blocks Codex native use until solved.

**D2 — Where do the delivered bytes live?**
- A byte-identical copy inside `provider_policy`, with a test that fails if
  it differs from `docs/V12-WORKER-INSTRUCTIONS.md` (recommended). Keeps
  N2's closed table and the image build context (`v12`).
- Move the canonical document into the package and repoint `AGENTS.md`:
  one file, but reopens the accepted editorial import.
- Manager supplies the bytes at composition: no copy, but the worker can
  no longer rebuild the adapter itself, which weakens N2's check.

**D3 — May delivery rest on the home file alone (A1)?**
- Yes, with A1 a named gate before native use (recommended; it is what
  "reuse the managed entries" selects, and prompts and their digests stay
  untouched).
- No: also put the same bytes in every `/7` prompt now. Independent of
  vendor loading, but changes every prompt builder and its digest.
  If A1 later fails, this is the fallback; it is specified here so that
  failure needs no new design round.

**D4 — Context-reuse turns are outside this delivery.**
N2 refuses `/7` together with a context worker, so there is no place to
bind a digest for them. Check 3's "context restore" becomes proof of that
refusal. Confirm, or select extending `/7` to context workers as separate
work first.
