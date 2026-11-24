# W385830 — native Codex implementation worker and explicit model attribution: consolidated implementation contract

Author: baton.prompt (K, model Fable 5.2), interactive copilot, no claim.
2026-11-23. Authority: M385877 (consolidate) and the owner rulings listed in
§2, all pinned in this dossier's FINDING.

**FOR REVIEW — NOT APPROVED.** This document consolidates; it approves
nothing and assigns no one. Research and design only: nothing was built,
launched or tested; no provider was called; no credential or registry was
read; no product, Git or live-instance change. Running Jobs, existing
instances and their admitted limits are untouched by anything here.

It is self-contained. It replaces, for reading, the first proposal and its
seven deltas, which are preserved unchanged and listed in §19.

## 0. How to read the status marks

Every rule carries one of three marks. They are never mixed in one
statement.

| Mark | Meaning |
| --- | --- |
| **[S]** | Selected by the owner. The source message is named. Not open |
| **[P]** | My implementation proposal: how a selected rule is carried out. Open to correction in review |
| **[Q]** | An unproved fact about a pinned provider build or the engine. Nothing depends on assuming it; it must be established by qualification before native use |

Evidence words for statements about today's code: **Confirmed** (I read
it), **Surveyed** (read by a read-only survey with citations; I re-read the
claims the design leans on), **Measured there** (an earlier dossier recorded
it from a real program). Source baseline: main HEAD 6079ad78. Paths:
`worker/` = `v12/worker/`, `wm/` = `v12/python/src/baton_v12/worker_manager/`,
`jm/` = `…/job_manager/`, `tools/` = `v12/python/tools/`.

## 1. Outcome and scope

A v12 Job can run its implementation phase on the Codex CLI and its
independent review phase on the Claude CLI, each with an explicitly
requested model, hand off through the existing native path, and show from
recorded evidence which provider build ran and which models the provider
reported as contributing to each result. A result that does not evidence
the requested model is refused and held, never silently accepted.

In scope:

- Codex as a fresh implementation worker.
- Explicit model request and attribution evidence for both providers'
  fresh turns.
- Two different provider workers under one Job.
- A retained provider home per worker.
- Both worker images, and what their qualification must establish.

Out of scope:

- Resumed or context-bound Codex sessions; any extension of the existing
  Claude context-reuse path.
- Codex as reviewer.
- The six-hour invocation ceiling and full descendant containment
  (W385263).
- Any change to scheduling, custody, recovery or the Plan/History view.
- The first native Job on this pipeline, which is a separate owner
  selection after qualification.

No new orchestration: the same worker exchange, custody, credential
delivery, limits, cancellation and recovery owners are used throughout.

## 2. Selected rules

| # | Rule | Source |
| --- | --- | --- |
| S1 | Codex implements; Claude with an explicitly selected Fable model reviews; delivery is direct implementation by codexpc with independent review | M385827, M385830, M385843 |
| S2 | No silent fallback or substitution. A result that does not evidence the requested model is refused and held | M385827; FINDING |
| S3 | The Job's shared identity keeps a provider-neutral tool-permission and environment policy. Each provider's command and environment configuration is bound separately in that worker's adapter identity. Different commands are allowed; a different selected policy is refused. Policy validation is not weakened | M385845 |
| S4 | Every worker in the new composition names an explicit model, the Codex implementer included. Existing admissions are unchanged | M385847 |
| S5 | Purpose: attribution. Retained per result: the requested model, the provider-reported models and their evidence, provider and CLI build, the exact attempt, and the resulting candidate or verdict. The requested model is intent, not proof | M385847 |
| S6 | Every model the provider reports is a contributor; none is primary. The requested model must appear among the evidenced contributors through an explicitly selected selector-to-identity mapping. No allowlist of additional contributors. A match establishes reported participation, not predominance or exclusive authorship | M385849 |
| S7 | Contributors are read only from provider fields that evidence actual participation in the invocation, never from request or configuration text or arbitrary mentions. A single-model field naming another contributor is not by itself conflicting when the requested model is also evidenced. Source evidence is preserved | M385851 |
| S8 | Codex CLI pin: 0.169.0. The retained host flag inventory is preparation, not proof of container compatibility | M385851 |
| S9 | The provider home is a retained, disk-backed work area managed mechanically by Baton: one stable home per worker; never shared between implementation and review; identity not regenerated on container or attempt restart; outside the checkout and proposal paths; operator home never exposed; credentials separately delivered; no elaborate access controls and no successor-access gate; retention does not assert session resume. Sharing and model-switch behaviour deferred | M385859 |
| S10 | The Codex worker uses subscription login credentials and the provider may keep its refreshed copy in its own retained home. API-key billing is not substituted. Refreshed credentials are never written back to the operator home nor exposed in ordinary candidate, evidence or log output | M385865 |
| S11 | One writer: a new container on a home is refused until the earlier runtime is confirmed stopped; admission then proceeds with no further owner approval. A stale or missing observation is not positive cessation | M385865 |
| S12 | Baton-managed replacement in a home is limited to explicitly identified Baton-owned instruction and configuration files. Provider session data and refreshed credentials are never overwritten at start | M385865 |
| S13 | Claude CLI pin: 2.1.247 retained. That exact build is qualified against the selected requirements, including explicit Fable selection and evidenced contributor reporting. An upgrade needs a demonstrated failure and an explicit selection, then its own qualification | M385872 |
| S14 | Consolidation is not implementation approval. Qualification must pass before native use. Implementation approval, when given, authorizes no provider call or other separately selected operation. Model selectors, the seed reference, the engine gates and the provider calls are raised at their qualification boundary | M385877 |
| S15 | No login-sharing prohibition is selected: a subscription pool is intended to serve several workers. Whether a refresh invalidates other copies of a login is an unresolved risk to qualify before shared-login use. Nothing here claims sharing is safe | M385877 |
| S16 | The re-seed operation is undecided. That is not a decision that homes are unrecoverable | M385872, M385877 |

## 3. What exists today

### 3.1 Reused unchanged

| Area | State | Evidence |
| --- | --- | --- |
| Worker seam | The worker owns launch validation, exchange documents, the replay fence, output measurement and activity; an agent supplies one `work` method | Surveyed, `worker/baton_worker.py` |
| Generic work inside the Claude adapter | About 85% of `worker/claude_agent.py` (7379 lines) is provider-neutral: checkout, the Git line, verification, proposal, handoff, review report, logging, bounds | Surveyed |
| Credential delivery | One read-only file per slot at `/run/baton/credentials/<slot>`, per attempt, from a registry reference | Surveyed, `wm/credentials.py`, `wm/oci.py:808-855` |
| Per-worker image and profile | Image, toolchain, runtime-profile and credential-policy digests are outside the Job input identity | Confirmed, `contracts/manifest.py:707-710` |
| Native handoff, review, verdict, custody; stop, deadline, token expiry | Provider-neutral | Surveyed |
| One live allocation per worker | A uniqueness rule in the Job store | Confirmed, `jm/schema.py:312-314`, `jm/scheduler.py:372-396` |
| Per-worker path derivation | The source nomination `<instance>/repo/source-<worker_id>` | Confirmed, `tools/pool.py:790-791` |
| Adapter tests | Provider injected at its boundary; hand-built fixtures; no live provider | Surveyed, `tests/manager/test_claude_agent.py` |
| Qualification packet | Image config, byte comparison with source, deterministic log, packaged composition, capability candidate | Confirmed (W385694 packet, reviewed by me) |

### 3.2 Missing, or fixed to Claude

| # | Finding | Evidence |
| --- | --- | --- |
| F1 | No Codex adapter, entry or image; Codex exists only in the August spike | Confirmed, `v12/spike/ping-pong/README.md:3-8` |
| F2 | The fresh Claude turn passes no model; `--model` is added only on the context path | Confirmed, `worker/claude_agent.py:4369, 4373` |
| F3 | Every worker profile carries a hard-coded `"model": "opus"` that nothing delivers or enforces; the launch document has no model member | Confirmed / Surveyed, `tools/next_run_bindings.py:360`, `wm/launch.py:90` |
| F4 | A retained real fresh run without `--model` used the account default, so today's label is not a selection | Measured there (October pilot dossier) |
| F5 | On Claude 2.1.247 a result names models only in per-model usage entries, and named two for one invocation; the worker reads only a direct `model` field, so it observes nothing | Measured there (September qualification dossier); Confirmed, `worker/claude_agent.py:4589-4593` |
| F6 | The Job-shared `tool_policy_digest` is the digest of the Claude command line, so a Codex lane beside a Claude lane is refused | Confirmed, `contracts/manifest.py:700-710`, `tools/next_run_bindings.py:303-306` |
| F7 | `pool compose-worker` has no provider or model operand | Surveyed, `tools/pool.py:737-743` |
| F8 | `separation_class` is a constant, never computed | Surveyed, `tools/stage_execution.py:446-449` |
| F9 | The spike measured Codex 0.150.1 refusing a read-only state directory and a home under a temporary directory | Measured there; not known for 0.169.0 |
| F10 | The spike's Codex child outlived a signal to its parent; the worker ends only the direct child | Measured there; Confirmed, `worker/claude_agent.py:1982-1990` |
| F11 | The provider inherits the worker's stdin | Surveyed |
| F12 | The context-reuse path is Claude-literal in worker and host | Surveyed |
| F13 | The worker never measures the installed CLI build; the value is copied from the delivery | Surveyed |
| F14 | No directory today is both writable in the container and keyed by worker. The fresh Claude turn builds its home in per-child memory scratch | Surveyed; Confirmed, `worker/claude_agent.py:3530` |
| F15 | Container mounts are fixed typed families composed in one place; there is no generic mount list | Surveyed, `wm/oci.py:1551-1807` |
| F16 | Five ending kinds release a worker's slot after a release-blocker check without that code reading the runtime's state. Whether a container can still be alive there is not established | Confirmed, `jm/scheduler.py:33, 585-589` |
| F17 | Nothing sweeps the instance root; one deletion enumerates the credential home | Surveyed, `wm/credentials.py:851-879` |

## 4. Provider hooks

**[P]** The provider-specific parts of the Claude adapter become
overridable members of the agent class, with today's values as the Claude
defaults:

- the program, its fixed arguments, and how the model selector is added;
- the home location and the credential mode (§9);
- the Baton-managed entries (§10);
- the participation sources and how the terminal outcome is read (§7);
- where the provider's session files are, for activity reporting.

A `CodexAgent` subclasses the same agent and overrides only those. A Codex
entry file constructs it, as `worker/dogfood_entry.py` constructs the
Claude one. Checkout, verification, proposal, handoff, review and logging
are inherited unchanged. This is not a refactor: no orchestration moves.

**[P]** Two hardenings ride along, because Codex needs them and Claude is
unharmed: the provider is started with no stdin (F11), and at the provider
time limit its whole process group is ended (F10). The second is the
minimum only; the ceiling and containment evidence remain W385263's.

## 5. Tool policy and adapter identity

**[S3]** governs. **[P]** How:

**Shared: `baton.worker-tool-policy/2`.** What the owner selected for the
Job, naming no provider or program:

| Member | Value selected today |
| --- | --- |
| interaction | non-interactive, one prompt, one process |
| tool permission | full, inside the container |
| provider sandbox | none of its own; the container is the boundary |
| user configuration | none ambient; only what the adapter composes |
| credentials | as delivered to the worker; no ambient credential; nothing written to the operator's home |
| environment | composed, never inherited; a closed key list |
| ephemera | fresh per child |
| model substitution | none; no fallback model |

Its digest is the Job's `tool_policy_digest`, equal on every lane as today.

**Per worker: `baton.single-implementation-adapter/2`.** Adapter name,
engine, network and entrypoint as today, plus: the provider; its exact argv
and environment policy; its home location and credential mode; its managed
entries; its participation sources; and `implements_tool_policy`, the
digest of the shared policy it realises. Its digest is the worker's
`adapter_digest`, already per worker.

**"Implements" is bound three ways, so validation is not weakened:**

1. *One owned table* maps each shared policy member to each supported
   provider's concrete realisation. The composer builds the adapter
   document from that table. A provider with no entry for a selected value
   cannot be composed.
2. *Admission check, added:* a worker is admitted only if its adapter's
   `implements_tool_policy` equals the Job's `tool_policy_digest`. The
   existing equality across lanes stays.
3. *Worker check:* the provider is not started unless the argv about to run
   matches the delivered argv policy, as the context path already does.

**Versioning. [P]**

- Nothing already admitted changes: stored `/1` digests remain valid and
  mutually consistent.
- New composition emits `/2` only under an explicit composition selection,
  so an old composition can still be reproduced.
- `/1` and `/2` lanes cannot mix in one Job: their policy digests differ
  and the existing equality refuses them.
- The carrier for `implements_tool_policy` (deployment document revision or
  retained adapter document) is the implementer's choice; either is covered
  by the adapter digest.
- A capability qualified against an `/1` adapter does not carry over.

## 6. Explicit model and the attribution record

### 6.1 Selection and delivery

1. **[S4]** Composition under the new selection refuses a worker that names
   no model. **[P]** `pool compose-worker` gains provider and model
   operands; the requested selector and its mapped identity are written
   into that worker's runtime profile in place of the hard-coded value.
2. **[P]** The selector is delivered by one new versioned launch member and
   applied in the fresh argv. **[S2]** No fallback-model option is ever
   passed.
3. **[P]** A worker under the new composition with no delivered model
   refuses to start its provider.

### 6.2 The record

**[S5]** fixes what must be retained; **[P]** the members:

| Member | Meaning | Source |
| --- | --- | --- |
| attempt | Attempt id, phase, Job | Launch document |
| provider | Which adapter ran | Adapter identity |
| CLI build, selected | The pinned build the profile names | Composition |
| CLI build, evidenced | What the installed program reports, measured by the worker before the turn (today it is only copied, F13) | Worker |
| model, requested | The selector passed on the command line. Intent only | Composition → launch → argv |
| model, mapped identity | The identity the owner has selected as what the provider reports for that selector | Composition |
| contributors | Every identity read from participation sources, as a set: each once, in fixed sorted order | Adapter |
| contributor sources | Per contributor, the names of the fields it was read from. Names only | Adapter |
| evidence | Digest of the exact provider output read, and the retained log holding it | Adapter |
| outcome | `matched`, `missing`, `conflicting` | §6.4 |

**[P]** The record holds identities, versions, field names and digests
only: no provider content, no usage quantity, no role or rank per
contributor. Quantities remain in the retained raw output. *(Leaving
quantities out is my reading of "no primary designation"; it has not been
ruled on.)*

### 6.3 Where it travels and what it binds

**[P]**, implementing **[S5]**:

1. Written by the worker into the result document it already produces for
   the phase, so it is inside that attempt's frozen, digested output.
2. Bound on the host at the ending, in the settlement the Job store already
   writes for the attempt — beside the candidate checkpoint for an
   implementation, beside the verdict id for a review.
3. Enforced in that same ending, before a candidate is accepted or a
   verdict recorded.
4. Shown in the attempt's published diagnostics, and available to the
   History view of W385263 as a recorded fact.

### 6.4 Outcomes

| Outcome | When | Mark |
| --- | --- | --- |
| **matched** | The mapped identity is among the contributors, and the evidenced CLI build equals the selected one | S6; the CLI-build clause is P |
| **conflicting** | Contributors were read but the mapped identity is not among them; or the evidenced CLI build differs from the selected one | S2, S6; the CLI-build clause is P |
| **missing** | No contributor can be read (output absent, truncated, unparseable, over a bound, or with no participation source), or the CLI build cannot be measured | S2 |

- **[S6]** Additional contributors never change the outcome and no
  allowlist exists.
- **[S2]** Only `matched` proceeds. `missing` and `conflicting` are refused
  with a typed cause and the phase is held for the owner. Nothing retries,
  substitutes or infers from the requested selector. The owner may then
  select another model for subsequent execution; the held attempt keeps its
  record.
- **[P]** The mapping is compared by exact equality of the whole string: no
  alias, prefix, case or suffix matching; one mapped identity per selector;
  a selector with no selected mapping cannot be composed.

**What `matched` says [S6]:** the requested model was reported among the
contributors of this invocation, on this build. It does not say that model
did most of the work or all of it.

### 6.5 Wording on every surface

**[P]**, implementing **[S6]**:

| Shown | Never shown |
| --- | --- |
| "Requested: X" | "Model: X" as a statement of what ran |
| "Reported contributors: X, Y" | "Primary", "main", "helper", or any share |
| "Requested model reported: yes / no / no evidence" | "Produced by X", "Reviewed by X" |

Workers composed under the earlier selection are shown as "not selected
(account default)" instead of the hard-coded label; that corrects a false
label (F3, F4) and changes no admission. **[P]** Separation class is
computed from the composed workers' provider and requested model.

## 7. Contributor evidence

**[S7]** governs. **[P]** How:

Each adapter carries a closed list of **participation sources** for its
pinned build: the exact fields of the provider's structured output whose
meaning is "this model did work in this invocation". Contributors are read
from those fields and nowhere else.

| Class of text | Collected? |
| --- | --- |
| A field on the list — for example a per-model usage entry, or the model named on a generated response | Yes |
| The requested selector, the argv, the launch document, the profile | Never |
| Provider output that echoes configuration | Never |
| Model names in generated text, tool input or output, files, prompts, error messages | Never |
| A structured model-naming field not on the list | Never; it stays in the retained raw output |

- All sources feed one set. A source naming exactly one model is one more
  source, not a ruling on which model "the" model was.
- The list is part of the adapter identity, so two workers that disagree
  about what counts as evidence have different identities.
- An adapter whose list is empty yields `missing` for every result. That is
  the fail-closed starting state.
- **[Q]** Which concrete fields qualify, for each pinned build, is
  confirmed against real output at qualification (§12). The Claude list is
  drafted from the September output of the same build; nothing is known for
  Codex 0.169.0.
- Not chosen by anyone: whether a usage entry with all-zero quantities
  evidences participation. Neither retained output shows one; it is brought
  as a question if a pinned build produces one.

## 8. The provider home

**[S9]**, **[S11]** govern. **[P]** How:

### 8.1 Binding

- **Key:** instance and worker id only. Not the attempt, container, Job,
  phase, profile digest, model or CLI build.
- **Place:** `<instance>/state/provider-homes/<worker_id>/`, containing
  `home/` (what the container sees) and a small manager-owned holder record
  the container never sees. Derived from the worker id as the source
  nomination is; a deployment cannot name another location.
- **Declared** by one new deployment member under a new deployment schema
  version. Earlier-version workers get exactly today's container.
- **Mounted** writable at one constant container path, as a new typed mount
  family with the existing no-nesting checks. Not under `/tmp`, `/scratch`,
  `/input` or `/output`. **[Q]** Its exact spelling is fixed at the image
  inventory, since a build may refuse some locations (F9).
- **Used by every worker of the new composition**, Claude and Codex. The
  Claude context-reuse path keeps its own home and is unchanged. *(Applying
  it to Claude workers follows "each worker gets its own stable home"; it
  moves those workers' fresh-turn home from per-child memory to retained
  disk.)*

### 8.2 Placement

Composition and start refuse a home that is, contains or lies inside the
workspace root, a source nomination, the launch home, the credential home,
the context store, the repository, or the operator's own provider
directories. The home is not an output, is in no manifest, and is never
sealed, collected or published.

### 8.3 Lifecycle

| Event | The home |
| --- | --- |
| First start of the worker | Created empty, owner-only, with the shared execution identity. Never seeded from the operator's home or host configuration |
| Container stop, removal, replacement; attempt end; cleanup; discard of execution roots | Unchanged |
| Next attempt of that worker, any Job or phase it serves | The same directory, as left, with no additional gate |
| Manager restart, reconcile, replay | The same directory; the path is re-derived, never re-minted |
| Removal | Only by an explicit operator act on the instance |

The holder record names the worker id, creation time and the attempt
holding the home or the last that did.

Not selected, therefore not specified: any size bound or expiry; what
happens when a worker id is recomposed with a different provider or model
(deferred by M385859). A full disk surfaces as an ordinary write failure.

### 8.4 One writer

1. The worker's single live allocation is the primary guarantee.
2. Starting a container records the attempt as holder. A start that finds
   a different holder proceeds only when that holder's runtime is confirmed
   stopped: recorded absent or destroyed, with cleanup `complete` or
   `retained`.
3. **[S11]** Not confirmation: no observation; an observation older than
   the holder's last recorded activity; a runtime recorded `uncertain`; a
   stop ordered but not confirmed; an attempt ending, provider exit or
   token expiry by itself.
4. The refusal is a pending state, not a request: the same start succeeds
   on a later pass once settlement records the earlier runtime gone. No
   owner item is opened.

Step 2 is needed because of F16. If implementation shows the allocation
alone always implies cessation, it reduces to an assertion.

### 8.5 What retention means

**[S9]** Files persist. No resume or session operand is passed because the
home is non-empty, and no result is described as continued from an earlier
session.

## 9. Credentials

**[S10]**, **[S12]** govern. **[P]** How:

### 9.1 Two modes, declared per adapter

| Mode | Used by | Behaviour |
| --- | --- | --- |
| Delivered | The Claude worker | As today: the credential is the read-only delivery and the home refers to it |
| Seeded and retained | The Codex worker | §9.2 |

### 9.2 Seeded and retained

1. The registry's login credential reaches the container by the existing
   read-only delivery.
2. If the home holds no credential at the provider's location, the adapter
   copies the seed there, owner-only. That is the only time Baton writes
   it.
3. **[S12]** Afterwards the copy belongs to the provider. Baton does not
   replace, compare, re-link or remove it at start, whatever the delivery
   then contains.
4. **[S10]** Nothing copies the home's credential outward: not to the
   delivery source, the registry, the operator's home, an output, custody,
   a proposal, a log or a diagnostic.
5. **[S10]** The Codex worker has no API-key slot and its provider
   environment no key variable. If the login cannot authenticate, the turn
   fails with a typed cause; no other billing route is tried.
6. The adapter reads the credential's content only to make the first copy.
   Records may say "credential present: seeded / retained" and nothing
   more.

The home is readable by every later attempt of that worker. That is the
selected arrangement.

### 9.3 Open matters — neither restricted nor claimed safe

These are stated so that nobody reads silence as a decision.

**Refresh across copies of one login [S15].**

- *The risk:* a subscription login is refreshed by the program, which then
  holds a newer credential than any other copy. If the provider treats the
  older copies as invalid, then a worker refreshing in its home could
  disable the registry seed, another worker seeded from the same login, or
  the operator's own session — and the reverse.
- *What is known:* nothing, for 0.169.0. I have assumed neither outcome.
- *What the contract does:* it places **no** restriction on several workers
  using one login, because a subscription pool serving several workers is
  the intended arrangement. It also makes no claim that doing so is safe.
- *What must happen first:* the behaviour is established by qualification
  before a login is actually shared between homes (§12, U5). Until then a
  shared-login deployment is unqualified, not forbidden.

**A retained login that stops working [S16].**

- *The gap:* when a home's credential can no longer authenticate —
  revoked, expired beyond refresh, or invalidated as above — the provider
  fails, the attempt ends as a typed provider failure, and the home is
  left as it is. Because Baton never overwrites a refreshed credential at
  start, the next attempt meets the same failure. The contract currently
  specifies no supported way to make that home usable again short of
  removing the home.
- *This is a gap, not a rule.* Nothing here forbids recovery.
- *Pending mechanism:* undecided. One candidate I raised earlier is an
  explicit operator act that replaces only the home's credential from the
  registry while no runtime holds the home. It is not approved, not
  rejected, and not part of this contract's implementation scope. Other
  mechanisms are equally open.
- *When it is decided:* once qualification, or a real lapse, shows what
  recovery is actually needed.

## 10. Baton-managed entries and W385853

**[S12]** governs. **[P]** How:

- Each adapter has a closed list of managed entries: Baton-owned
  instruction and configuration files, each by exact path in the home,
  each delivered from a digest-bound input and re-placed at every start.
- Credentials, provider session files, history, caches and anything a
  provider or model writes are never on it and are never replaced,
  truncated or removed at start.
- **The list is empty** until W385853's instruction delivery is selected
  and names its files. With an empty list, start changes nothing in the
  home.
- A path cannot be both managed and provider-written. **[Q]** Which paths
  each build writes is inventory; a collision is reported, not resolved by
  overwriting.

Relation to W385853 (worker instruction delivery):

- Both provider programs read global instructions and configuration from
  their home, so a retained home is part of each worker's instruction
  chain. **[Q]** Which home and project files each pinned build loads by
  itself is not established.
- This contract offers W385853 a placement point (the managed list) and a
  binding (the adapter identity). It does not decide W385853's selector,
  does not exclude host guidance, and puts no restriction on what a
  retained home may otherwise hold.
- W385853's three instruction documents were reviewed and accepted as
  editorial text (its `review-2026-11-23T16-16-25Z.md`). Native instruction
  delivery remains unfinished and is not delivered by this contract.

## 11. The Codex adapter and the images

### 11.1 Pins

| Image | CLI | Mark | Consequence |
| --- | --- | --- | --- |
| Codex worker | 0.169.0 | S8 | New recipe mirroring the Claude one: same base family, trust store, tools, user, verifier scaffolding and layout marker, the generic files, the Codex adapter and entry |
| Claude worker | 2.1.247 | S13 | Rebuilt only because the adapter changes; its CLI does not move |

**[P]** Each image has a version gate test that refuses any other build,
and the worker refuses to attribute a turn run on a build other than the
selected one. No code path tries a second build.

### 11.2 What the Codex adapter must deliver

Deliberately not fixed here: the exact Codex arguments, event shapes,
session-file location and credential file name. **[Q]** They are taken
from the 0.169.0 inventory inside its image. The host captures in
`evidence/research-385843/` guide the draft only.

| Need | Behaviour required | Host 0.169.0 help shows (reference only) |
| --- | --- | --- |
| Non-interactive single turn | One process, one prompt, exits | `codex exec [PROMPT]` |
| Full in-container tool permission | The selected shared policy | `--dangerously-bypass-approvals-and-sandbox`; `-s danger-full-access` |
| Explicit model | Selector on the command line | `-m, --model` |
| Working directory | The candidate root | `-C, --cd`; `--skip-git-repo-check` |
| No ambient configuration | Only what the adapter composes | `--ignore-user-config`, `--ignore-rules` |
| Machine-readable outcome | Success or a classified failure, and participation sources | `--json`; `-o` |
| Bounded reading | A bounded reader of the terminal events; the full stream stays in the existing provider log | — |
| Failure words | Mapped into the host's closed set unless a new word is approved | — |

How "no ambient configuration" is reconciled with delivered worker
instructions is W385853's selector question, not decided here.

## 12. Qualification — required before native use, none of it authorized

**[S14]** Nothing in this section is selected. Each step is raised for
selection when its boundary is reached.

### 12.1 Engine-only image gates (no provider, no credential)

Per image: it builds; the pinned program reports the pinned version; the
adapter files are byte-identical to source; the options the adapter uses
appear in the pinned build's own help; the program starts far enough under
the real container posture (read-only root, the home mount, composed
environment) to show whether it accepts that home. This is where each
build's inventory is taken and written into the adapter's fixtures.

### 12.2 Real-provider questions

Deterministic tests cannot answer these, because they are facts about the
provider's own behaviour. Each is one bounded invocation with a fixed
prompt, no repository content, the selected limits, and retained evidence.

| # | Question |
| --- | --- |
| Q1 | Under the exact container posture, seeded from the selected login, does Codex 0.169.0 authenticate and complete one fixed trivial task with the adapter's exact arguments? What are its terminal events, exit status and participation sources? Where did credential and session files appear; did the home's credential change during the turn (by size and time only); and does the seeded value appear anywhere in its output (by a check that does not record the value)? |
| Q2 | Does Claude 2.1.247 accept the selected Fable selector on a fresh turn, and which participation sources and contributors does its output then carry? |

### 12.3 What Claude 2.1.247 must meet [S13]

**[P]** My reading of "the selected requirements"; correct here if the set
should differ.

| # | Requirement | Established by | Fails when |
| --- | --- | --- | --- |
| C1 | The installed program reports 2.1.247 without network or credential | Image gate | Anything else, or unmeasurable |
| C2 | It accepts an explicit model selector on a fresh turn with the adapter's exact arguments | Image gate (help); Q2 | Option absent, or the turn rejected for the selector |
| C3 | Asked for the selected Fable selector, it runs the turn without refusing or substituting | Q2 | Selector rejected, or no evidence of that model |
| C4 | Its output carries at least one participation source readable within bounds | Q2 | No field evidences which models did work |
| C5 | The contributors include an identity the owner accepts as the requested model | Q2, then the owner's mapping selection | No such identity |

Any failure is the demonstrated need **[S13]**. Nothing then changes by
itself: the pin stays, the Claude reviewer stays unqualified, and the owner
is asked to select an alternative build, which is pinned and qualified from
the start. One call cannot show these hold on every later turn; the
per-attempt record does that.

### 12.4 Unproved facts

| # | Not yet known | Answered by |
| --- | --- | --- |
| U1 | Whether Codex 0.169.0 starts under the v12 posture with a disk home at the chosen path | Image gate |
| U2 | Where it keeps credential and session files, and which home or project files it loads as instructions or configuration | Image gate |
| U3 | Whether it authenticates from a seeded login copy and completes a turn | Q1 |
| U4 | Whether and when it refreshes, and that the refreshed copy lands in the home and nowhere else | Q1, then inspection of the home's file names, sizes and times |
| U5 | Whether a refresh in one place invalidates other copies of the same login | Not answerable by one call; needs its own selected procedure before shared-login use |
| U6 | Whether the build can emit credential material into its own output | Q1 check |
| U7 | What it reports as model participation | Q1 |
| U8 | Which registry login seeds the Codex worker | Owner selection at the Q1 boundary; I have read no registry |
| U9 | What Claude 2.1.247 writes into a retained home, and which files it loads from one | Image gate |

### 12.5 Packets

One per image, as W385694's: image config and identity, byte comparison of
image files with source, deterministic log, packaging identity, packaged
composition output for the role, capability candidate, and an explicit
statement of what was not run.

## 13. Slices and deterministic verification

Each slice is independently reviewable. All verification here uses a fake
provider at its normal boundary; test modules are registered once each;
focused runs per `v12/python/TESTING.md`; no full-suite run is selected.

| Slice | Outcome | Depends on |
| --- | --- | --- |
| N1 | Explicit model request, attribution record, binding and enforcement at the ending, diagnostics, computed separation class | — |
| N2 | Provider hooks; no-stdin and process-group hardening; `/2` tool policy and adapter identity; retained home, holder check, credential modes, managed entries | — |
| N3 | Codex adapter, entry and image recipe | N2; inventory from N4 for its fixtures |
| N4 | Engine-only image gates for both images | Images; selection |
| N5 | Q1 and Q2 | Selection; U8; requested selectors |
| N6 | Qualification packets; joined Codex-implementation → Claude-review proof under one Job with fake providers | N1–N5 |

Main areas (evidence of where the behaviour lives, not an edit list):
`tools/pool.py`, `tools/next_run_bindings.py`, `contracts/manifest.py`,
`wm/launch.py`, `wm/oci.py`, `worker/baton_worker.py`,
`worker/claude_agent.py`, `tools/stage_execution.py`,
`jm/review_driver.py`, `wm/failure_cause.py`, new `worker/codex_agent.py`
and entry, new `worker/Dockerfile.codex`, tests.

### N1 — model and attribution

Selection and delivery:

1. Composing under the new selection without a model, or with a selector
   that has no selected mapping, is refused for every role and provider.
   With one, only that worker's profile digest changes.
2. The fresh argv carries exactly the delivered selector and no fallback
   option. A new-composition launch with no model is refused by the
   worker.

The record:

3. The worker measures the CLI build from the program; a build other than
   the selected one yields `conflicting`, and no other build is tried.
4. Contributors are read from each participation source alone, from
   several agreeing, and from several naming different models; each yields
   the union. With none present the outcome is `missing`.
5. Truncated, oversized, unparseable or absent output yields `missing`.
   Nothing is inferred from the requested selector.
6. A model name appearing only in generated text, tool output, an error
   message, the echoed prompt or a configuration-echo record is not
   collected. If that is the only place the requested model appears, the
   outcome is `conflicting` when other contributors were read and
   `missing` when none were.
7. A structured model-naming field not on the adapter's list is ignored
   and stays in the retained output.
8. Requested model plus one or several additional contributors →
   `matched`; all are recorded; no allowlist is consulted or exists.
9. A single-model source naming Y while another names the requested X →
   `matched`, contributors X and Y. The same with X evidenced nowhere →
   `conflicting`.
10. A contributor differing from the mapped identity only by case, prefix
    or suffix does not match.
11. The same contributors in different orders, or with different usage
    figures, produce byte-identical records. The record carries per
    contributor its source field names, and no quantity, role or provider
    content.
12. The evidence digest matches the retained log's bytes.

Binding and enforcement:

13. An accepted implementation's ending settlement carries the attribution
    beside the candidate checkpoint; an accepted review's beside the
    verdict id; each is reachable from the other by identity.
14. `missing` or `conflicting` → refused with its typed cause: no
    candidate accepted, no verdict recorded, dependents stay closed, the
    phase is held, nothing retries. A passing verification does not rescue
    it.
15. A record naming another attempt is refused.
16. Restart between the worker's result and the ending replays the same
    decision.
17. A pre-change worker image under the new composition is held as
    `missing`.

Display and preservation:

18. Diagnostics show requested selector, mapped identity, contributors,
    both CLI builds and the outcome in the §6.5 words; no surface, record
    or log line written by this change carries a primary, helper or share
    designation.
19. A worker composed under the earlier selection behaves exactly as
    today and is shown as "not selected (account default)".
20. Separation class reflects the composed providers and requested models.
21. Changing an adapter's participation-source list changes that worker's
    adapter digest.

### N2 — hooks, policy, home, credentials

Hooks and hardening:

22. Every existing Claude adapter case passes with the hooks in place and
    default values.
23. The provider is started with no stdin.
24. At the time limit the provider's whole process group is ended and the
    drain completes, including with a child that ignores the first signal.

Tool policy and adapter identity:

25. A Codex-provider and a Claude-provider worker composed from the same
    shared policy have equal `tool_policy_digest`, different
    `adapter_digest`, and are admitted as two lanes of one Job.
26. Each worker starts its provider only when the actual argv matches its
    delivered argv policy.
27. A lane composed under a different selected policy is refused at
    admission before any effect.
28. A worker whose adapter names a different `implements_tool_policy` is
    refused; an adapter document altered after composition is refused on
    its digest.
29. Composition for a provider with no table entry for a selected policy
    value produces no document.
30. A retained pre-change worker document still validates and reproduces
    its recorded digests under the old selection; a `/1` and a `/2` lane
    in one Job are refused; existing composition tests pass unchanged
    under the old selection.

Home binding and placement:

31. Two workers of one instance — same provider, different roles —
    resolve to different homes; one worker resolves to the same home on
    every derivation; a deployment naming another location is refused.
32. A file written in attempt 1 is present, byte-identical, in attempt 2
    of the same worker: after a normal end, a failed attempt, container
    removal, and a manager restart between them. A different Job served by
    that worker sees the same home with no approval or extra record.
33. A worker composed under the earlier deployment version has no home
    mount and a byte-identical run vector.
34. A home overlapping the workspace root, a source nomination, the launch
    or credential home, the context store or the repository is refused at
    composition and at start. The mount source is always under the
    instance root; the operator's home is never a source or ancestor.
35. The home never appears in an input manifest, output, custody, proposal
    or sealed result; attempt cleanup, discard of execution roots and the
    credential-orphan sweep leave it untouched.
36. A new home is empty; nothing from the host is copied in.

One writer:

37. A second admission to a worker with a live allocation is refused.
38. A start whose home names another holder is refused and pending for
    each non-confirmation in §8.4 item 3, and proceeds on the next pass
    after settlement records that runtime gone, with no owner record
    created.
39. Restart between recording the holder and starting the container
    replays to the same holder.

Credentials and managed entries:

40. *Delivered mode:* behaviour is today's; the credential's bytes exist
    nowhere under the home after a turn.
41. *Seeded mode, empty home:* the seed is copied once, owner-only.
    *Credential present:* start leaves it byte-identical, including when
    the delivery now holds different bytes.
42. A fake provider rewrites the credential during a turn; the next
    attempt of that worker sees the rewritten bytes; the delivery source,
    the registry fixture and every path outside the home are unchanged.
43. A sentinel credential value appears in no result, manifest, custody,
    proposal, Baton-written attempt log, diagnostic or status document.
44. The Codex provider environment has no API-key variable and its
    credential profile no key slot; an authentication failure ends the
    turn with a typed cause, leaves the home unchanged, and nothing else
    is tried.
45. Two seeded-mode workers naming the same credential reference are
    composed and admitted; nothing refuses them. *(Asserts that no sharing
    prohibition exists; it proves nothing about provider behaviour.)*
46. Managed entries are re-placed at every start; with an empty list,
    start changes nothing in the home. Session-like files a fake provider
    leaves are untouched. An adapter declaring a managed path that is also
    its credential location is refused at composition.

Honesty:

47. No argv carries a resume or session operand because the home is
    non-empty; no result or diagnostic describes a turn as resumed.
    Diagnostics show the home's worker id, its holder and that it is
    retained.

### N3 — Codex adapter

48. For the same fake outcome the Codex adapter produces the same
    proposal, handoff and result documents as the Claude one.
49. Each terminal outcome in the pinned build's inventory maps to the
    right status and failure word; an unrecognised or truncated stream is
    `unclassified`, never success.
50. The image version gates refuse any build other than 0.169.0 and
    2.1.247 respectively.

### N6 — joined

51. A Codex-profile implementation lane and a Claude-profile review lane,
    both with fake providers, run one Job through admission, handoff,
    review and verdict with attribution bound at each ending; a review
    whose contributors lack the mapped identity leaves no verdict.

## 14. Normative text — proposed, needs the owner's explicit approval

DESIGN already says providers and models are independently configured
runtime capabilities (ID-6) and that executions of one Job need not share a
runtime identity (ID-4). One clarifying sentence is proposed. Nothing has
been drafted into `v12/DESIGN.md`, and it must be approved and pinned
before dependent implementation:

> Owner clarification (W385830): the tool-permission and environment policy
> a Job is admitted under is provider-neutral and shared by every execution
> of the Job. Each execution's provider-specific command and environment
> configuration is bound to its own adapter identity and MUST be composed
> from, and declare, the shared policy it realises. Executions MAY use
> different provider commands; an execution under a different selected
> policy, or whose adapter does not realise the Job's policy, MUST be
> refused.

Whether the attribution record and the retained provider home also need
normative sentences is a question for the reviewer of this contract; I
have drafted none.

## 15. Overlap and order

| Path | Also changed by | Handling |
| --- | --- | --- |
| `tools/pool.py`, `tools/stage_execution.py`, `tools/parallel_test.py`, `DEPLOYMENT.md` | W385695's remaining checkpoints | Serial; order agreed at claim time |
| `worker/claude_agent.py`, `worker/Dockerfile.claude`, the context prompt and argv builders, the future Codex adapter | W385853's instruction-delivery change | Proposed serial order: N2, then W385853's delivery on top, because N2 creates the identity its digest binds into. A proposal on T385853 (M385863); no dependency is installed and no overlapping edit is assigned |
| `worker/claude_agent.py`, `worker/baton_worker.py` | W385263's later ceiling and containment slice | N2's process-group change is the minimum; that slice builds on it. Serial |
| The Claude worker image | Every Job bound to the current image, including the running native Job | A rebuilt image is a new digest and is requalified. Running and already-admitted Jobs keep the image they were admitted with |
| W385263 A1 (observation, viewer, status) | — | No overlap; A1 is held behind this Work by M385843 |

## 16. What approving this contract would and would not do

| Would | Would not |
| --- | --- |
| Fix the behaviour N1, N2 and the deterministic part of N3 must deliver, and the verification that shows it | Authorize any build, image, engine operation, credential or registry read, provider call or install |
| Allow those slices to be assigned for direct implementation and independent exact-byte review | Qualify either pinned build, or permit native use |
| Fix the `[P]` proposals as the design unless corrected in review | Decide any `[Q]` fact, U1–U9, or the two open matters in §9.3 |
| — | Change any running Job, existing instance or admitted limit |
| — | Approve the DESIGN sentence in §14, which needs its own explicit approval |

## 17. Decisions at their boundaries

Raised one at a time when the boundary is reached, per **[S14]**.

| Boundary | Decision |
| --- | --- |
| Before assignment | Approval or correction of this contract; the DESIGN sentence; the order with W385853 and W385695 |
| When images can be built | Selection of the engine-only gates |
| Before Q1 and Q2 | The requested selector for each worker; the seed login reference (U8); selection of each call |
| After Q1 and Q2 | The mapped identity for each selector; whether 2.1.247 met C1–C5 |
| Before a login is shared between homes | How U5 is qualified |
| When a recovery requirement is established | The mechanism for a lapsed retained login |
| Deferred by the owner | Sharing and model-switch behaviour for a home |

## 18. Limits

- Nothing was executed except, earlier, `--version` and `--help` of the
  CLI builds installed on this host, which are not the pinned images.
- Surveyed, not re-read by me: the section map of `claude_agent.py`; that
  failure words are a closed set of four; the spike's measured Codex
  behaviours; the mount families; the absence of an instance sweep.
- The two-contributor behaviour of Claude 2.1.247 comes from the
  September dossier, not from me.
- My readings and additions, each open to correction: leaving usage
  quantities out of the record (§6.2); exact-string mapping (§6.4); the
  holder check (§8.4 step 2); the two credential modes (§9.1); the
  managed-entry list as a placement point (§10); requirements C1–C5
  (§12.3); applying the retained home to Claude workers (§8.1).
- The size of N3 is not known until the 0.169.0 inventory exists.

## 19. Earlier files, preserved unchanged

This document supersedes them for reading. They remain the decision
history, including four recommendations of mine that were not selected or
were withdrawn: a declared helper list (REV3 §4), a private memory home
(REV5 §6), an API-key credential (REV6 §7), and a one-login-per-home
composition refusal together with a re-seed act (REV7, REV8).

| File | sha256 |
| --- | --- |
| `IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-23.md` | 68599861e3af9f0763f08d97ff9b44dcb75c36581155a9c4f173b1ce2891c9d7 |
| `IMPLEMENTATION-CONTRACT-REV2-2026-11-23.md` | df42c0387f13eecaa45dd23685d536a2c3bbd0cb50c80ec2ae070919dffae955 |
| `IMPLEMENTATION-CONTRACT-REV3-2026-11-23.md` | 3a3d36c372866330e6c4d632917985820bfd1a4fe03c1204ef60c01c196451d6 |
| `IMPLEMENTATION-CONTRACT-REV4-2026-11-23.md` | c9c99b5e52180e283659aa4989b0052110011bc476105e60326e40d301e8d0b6 |
| `IMPLEMENTATION-CONTRACT-REV5-2026-11-23.md` | a87f38a63ea828356f258ba11751f2c6c750fa49a5060196a8c3bfeb2a6d6171 |
| `IMPLEMENTATION-CONTRACT-REV6-2026-11-23.md` | a7b2fadeb2b388b2cc91742a53238584a668a4d8f744d199841687088b148ecb |
| `IMPLEMENTATION-CONTRACT-REV7-2026-11-23.md` | 042025f78b95d5e3b7890ab49185c2bc6d53ec01df219ce5ef2a07aa0912bfff |
| `IMPLEMENTATION-CONTRACT-REV8-2026-11-23.md` | adcca6f3e02ff1cba9b05dcd182bc3ced253f46e1fbea2c9cf0ac2da320db551 |
