# Readiness inventory — next useful documentation checkpoint

W376804, claim 376826. **Preparation only.** No build, pull, engine, provider,
install, deployment, retry, cleanup, source or Git mutation was performed.
Every field below is marked CONFIRMED (measured this claim) or UNKNOWN
(needs an owner selection or an owner elsewhere).

## 1. The candidate source checkpoint — CONFIRMED, and it moved

`8876bf950ff1f8ab8767ce9786df268cc9d767c6` is **current HEAD**, and its
history is exactly:

    8876bf95  Implement stopped-failure settlement and expose installed commands   (HEAD)
    ef703336  Fix verifier roots for descendant processes
    f36bcd75  fix(v12): align template Job observation with serving inputs

So the FINDING's three named ingredients are all in one line of history, and
**the verifier source is now committed** — `ef703336` is HEAD~1. That is a
change since the W325695 work: those ten paths were a dirty candidate and are
now history.

**What is still uncommitted in `v12`, and whose it is** — this matters because
the FINDING forbids importing evolving dirty modules:

| path | owner |
| --- | --- |
| `job_manager/templates.py`, `tests/job_manager/test_templates.py` | W371294 (accepted, closed) |
| `job_manager/role_contract.py`, `role_capability.py` + their tests | W371294 / W376723 (under review) |
| `tools/bootstrap.py`, `tests/tools/test_startup_prerequisites.py` | W376246 (under review) |
| `v12/DESIGN.md` | fragility-assessment record |
| `tests/tools/test_stopped_settlement_joined.py` | W375446 |

**Consequence for this checkpoint:** a run pinned at `8876bf95` gets NONE of
those. If the useful task needs the template `/2` registry, the role contract
or the capability predicate, an explicit source export or a further commit is
required — and that is an owner selection, not something to infer.

## 2. The existing image — CONFIRMED incompatible with HEAD, by one commit

Image `sha256:47e733834bb690fd4601e102f81e527a08b6ffe55da8b8cb345f45edfcb1517e`
is bound under W325695 `preparation-376414`, selection
`7ab020e2d08f74296fb08bf1d0a44b8bfd1b8d8b76a34f96727502520fd6eac1`. Its
context is a frozen copy of the ten accepted paths at `ef703336`.

`8876bf95` changed eleven files — `QUICKSTART.md`, `worker_manager/schema.py`,
`stopped_settlement.py`, `tokens.py`, `workspaces.py`, three test modules,
`tools/job_manager.py`, `tools/single_worker.py`, `tools/stopped_settlement.py`.
**None of those ten image paths is among them**, but `single_worker.py` and
`schema.py` ARE in the host package the image is launched by.

So, stated exactly: **the image's own closure is still byte-current for the
worker side at HEAD, and it is NOT the qualified image for this checkpoint,**
because its selection was taken at `ef703336` and the host package has moved.
Whether a rebuild is genuinely needed is UNKNOWN and is the first thing an
owner should decide — I did not rebuild, pull or run it, and I am not
relabelling it.

## 3. W325695 mechanism evidence — CONFIRMED absent

The kernel/mount mechanism is **not** proved. Selection B ran once under
E376729 and produced a durable `failed-or-uncertain` receipt with
`create_intent: false`, `owned: false`, `container_id: null`,
`provider_invoked: false` — nothing created, nothing owned. The preflight
`inspect` answered the ordinary `no such object` (status 1 nested, exit 0
direct, identical stderr), `exact_absence` stayed false and the execution
phase raised `ValueError`. **So if this checkpoint uses that image, the
verifier topology evidence it would rely on does not exist yet**, and W325695
owns that proof. Named as a blocker rather than waived.

## 4. The smallest subset, by the FINDING's own list

| prerequisite | state |
| --- | --- |
| corrected shared declarations | CONFIRMED available — W370688 successor inventory `00add5d1…`, provenance `f36bcd75`, which is in HEAD's history. Its simulated provider/Git proof does not certify real transport. |
| actual role input/output compatibility | UNKNOWN for `/2`; the predicate exists (W376723, under review) and `/1` remains the explicit supported path |
| qualified fixed-observation host package | UNKNOWN. Package `1da85eed` does NOT contain the observation correction and may not be relabelled. A candidate-specific package at `8876bf95` is the likely minimum. |
| matching worker | UNKNOWN — see §2 |
| verifier topology evidence | ABSENT — see §3 |
| isolated fresh storage | proposable now: a fresh destination with the no-overlap checks `bootstrap.custody` already performs |
| failure/settlement/retention ownership | CONFIRMED present in HEAD — `8876bf95` adds `stopped_settlement` and the installed command; W375444/W375445 own it and W375446 owns the joined evidence |

## 5. Template path — keep `/1` explicit

The useful task should name `implementation-review/1` explicitly if it uses
the supported path. `/2` is registered only in the uncommitted W371294
candidate, its descriptor binding is `role_contract`'s, and the configured
default is still `/1`. Turning this run into a `/2` or cutover proof is NOT
selected, and nothing here does so silently.

## 6. Exact next selections, for the owner to choose between

**A — read-only readiness, no build.** Pin `8876bf95`; run the installed
read-only commands against a fresh destination; produce no image. Cheapest,
and it answers nothing about the learning question.

**B — candidate package + worker at `8876bf95`.** Build a candidate-specific
manager package and a matching worker from an explicit source export of
`8876bf95` (never the dirty tree). Proposed per-invocation bounds from the
FINDING: **provider 3600 s, verification 900 s**. Logical credential
references only. Two independent role identities. Fresh destination with
no-overlap checks. Retained evidence on failure, **no retry and no deletion on
unknown effects**.

**C — correction exposure.** The historical unlimited-correction authorization
is SPENT. If corrections are wanted, they must be selected explicitly with a
stated ceiling; I propose none implicitly.

For B, the timeout/cancellation/failed-settlement commands are the installed
`stopped_settlement` ones added in `8876bf95`, with exact-runtime identity and
supervisor-stop conditions recorded — not a bespoke launcher.

## 7. Classified non-gating

Queue/startup (W371075), typed-diagnostic polish (W371073 chain), broad
certification, context-reuse completion and authority cutover are **not**
prerequisites for this learning question. W376246/W375516 installer work is
not gating either: it hardens prepare/cleanup, and this checkpoint can use a
fresh destination without it.

## 8. TEMPLATE-JOBS.md objective — UNKNOWN, needs one read

The FINDING asks that the earlier guide objective be revalidated so the task
stays useful rather than duplicating existing documentation. I did not read
the current guide against HEAD this claim and am not asserting it is still
useful. That is the one remaining preparation step inside this slice.

## Verification spending

Read-only: the assignment, FINDING/PLAN, `git log`, one `git show --stat`,
`git status --porcelain v12`, and the W325695 receipt I had already captured.
No suite was run — nothing was changed. No engine, provider, build, install or
Git mutation.
