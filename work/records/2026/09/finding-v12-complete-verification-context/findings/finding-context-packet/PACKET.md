# The isolated correction packet — W321780

The smallest paired worker/operator correction, as an independently reviewable
packet with a composable preparation recipe. **Nothing here is executed and no
product file is edited.** Execution is gated in W321776; the final base and the
run-specific identities are deferred.

## The concrete task, in the contract's own roots

The measured 102-test credential gate, which VER-5 names as the acceptance
obligation and which a *different* passing subset may not substitute for.

```
verification (LITERAL argv, no environment assignment)
  ["python3", "-m", "unittest",
   "tests.tools.test_user_credentials",
   "tests.tools.test_dogfood_operator.TheDocumentedCommandIsOneGrantsFile.test_help_names_the_credential_source_the_launcher_requires",
   "tests.tools.test_dogfood_operator.ThePublicRecoveryEndsAnInterruptedAttempt.test_a_recovery_asks_for_no_credential",
   "tests.tools.test_dogfood_operator.TheArcMaterializesBetweenActivationAndRuntimeCreation.test_the_factory_runs_after_activation_and_before_runtime_start",
   "tests.tools.test_dogfood_operator.TheDocumentedRecoveryEndsRealAttachedState.test_an_uncertain_runtime_settles_nothing_and_keeps_the_bearer",
   "tests.manager.test_credentials.TheTrustedProfileMapsEverySlot.test_the_reference_is_opaque"]

verification_context
  candidate_destination  candidate              (view-relative) -- the WHOLE
                                                prepared repository lands here
  working_directory      candidate/v12/python   (view-relative)
  import_roots           ["src"]                (working-directory-relative)
  required_paths         ["src", "tests", "tests/tools", "tests/manager"]
                                                (working-directory-relative)
  candidate              LAUNCH CONSTRAINTS ONLY -- profile git-line;
                         declared_base <BASE>; pins one path, below.
                         No entry_head, no tree digest, no changed/removed:
                         those are the turn's OBSERVATIONS, published in its
                         result. See the lifecycle trace below
  inputs                 one, below             (destination view-relative,
                                                DISJOINT from `candidate`)
```

`PYTHONPATH` is **not** in the argv. It is derived — `import_roots` joined to the
holder's own materialized `working_directory` — which is the whole point:
September reached `PYTHONPATH=src` by a hand-set shell variable, and a hand-set
variable is not a contract. Both holders derive the same closed path from the
same declaration, and no ambient value is inherited.

## THE LAYOUT, RESOLVED RATHER THAN ASSUMED

Review 2026-10-18T09-16-00Z finding 2, and the contradiction was real. The first
draft selected `git-line` and then put the candidate at `v12/python` while
showing `src/` directly beneath it. A `git-line` candidate is the **whole
prepared repository** (`claude_agent.py:2011-2021`), so that layout would have
produced `view/v12/python/v12/python/src` — not the import root it drew. Putting
the whole candidate at the view root instead would drop the declared fixture
destination **inside** the candidate, which this packet correctly forbids.

The resolution is one level of nesting, and it is declared rather than inferred:

```
<view root>/
  candidate/                      candidate_destination -- the WHOLE
                                  prepared-line repository, full attribution
    v12/python/                   working_directory
      src/  tests/  ...           required_paths, working-directory-relative
    work/records/2026/08/.../evidence/vectors.json
                                  the candidate's OWN copy, at the only path
                                  the gate can read it from -- PINNED, not
                                  declared as an input
  sealed/
    worker-control-api-manifest-vectors/vectors.json
                                  the sealed input's declared destination,
                                  DISJOINT from `candidate`
```

**Why the fixture appears twice, which is the part that needs saying plainly.**
`tests/manager/input_roots.py:29-33` resolves the fixture as
`Path(__file__).resolve().parents[3] / ".." / "work" / "records" / ...` — four
levels up from `tests/manager`, then one more. With the working directory at
`candidate/v12/python`, that lands at
`candidate/work/records/.../vectors.json`, **inside the candidate**. No
declaration can move it; only a product edit could, and a preparation packet
that edited the product to suit its own layout would have changed what the gate
measures.

So the fixture is handled as **both**, with different jobs:

| copy | role | what protects it |
| --- | --- | --- |
| inside the candidate | the bytes the gate actually reads | a `candidate.pins` entry at the exact digest below — an edited fixture is a Stage-B `materialization` refusal, never a test pass |
| the sealed input at `sealed/...` | the independent reference both holders materialize from the seal | VER-2's overlap rule, satisfied because its **declared destination** is disjoint from `candidate` |

A holder compares them: the pin and the sealed input carry the **same digest**,
so if the candidate's copy drifts, the two disagree and Stage B refuses before
the command starts. That is how the external sealed fixture stays disjoint *and*
how both holders provably obtain identical bytes.

## The one declared immutable input

```
name            worker-control-api-manifest-vectors
destination     sealed/worker-control-api-manifest-vectors/vectors.json
content_digest  sha256:fcc19dbdf021246c61d516987e5672c93053ab57a2e151af6bb66b6e6c6a9903
bytes           19351

and the matching pin, inside the candidate, at the ONLY path the gate reads:

candidate.pins[0].path
                work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/findings/finding-worker-control-api-manifests/evidence/vectors.json
candidate.pins[0].content_digest
                sha256:fcc19dbdf021246c61d516987e5672c93053ab57a2e151af6bb66b6e6c6a9903
```

Both digests measured in this claim against the current canonical record, and
they are deliberately the same digest: the pin and the seal are two independent
holders of one fact.

**The destination changed in this correction.** It used to reproduce the
record's own repository layout at the view root, which review finding 2 showed
would place it inside a full-repository candidate — the overlap VER-2 refuses.
Its declared destination is now `sealed/...`, disjoint from `candidate`, and the
in-candidate path it used to name is a **pin** instead.

**HOW IT IS RESOLVED, not assumed.** The manager seals this file into the input
set at preparation time and the holder materializes it **from the seal**, by
`name`, verifying `content_digest` after materialization (Stage B,
`materialization`). Neither holder reads the host checkout by absolute path and
neither copies the repository: the declared set is the only thing that crosses
into a view, which is what makes the September layout reproducible instead of
re-derivable by hand.

## The preparation recipe — composable, with identities deferred

Review 2026-10-18T09-07-00Z finding 3: the first draft described the workload
rather than a Job somebody could compose. `<BASE>` and `<RUN>` are deferred
placeholders, not blanks to be guessed — and review 2026-10-18T09-38-00Z then
showed that the recipe's *order* was impossible and its *interfaces* were
misattributed, so what follows is a lifecycle trace rather than a parts list.

## THE LAUNCH ENVELOPE IS `/2`, AND `/3` IS WHAT THE TURN PRODUCES

Review 2026-10-18T09-38-00Z finding 2, and it was a circular bootstrap. The
previous draft had `TASK-INSTRUCTIONS.md` be the `instructions` member of a
`baton.dogfood-task/3` document whose job was to make `/3` exist — while also
selecting the existing image unchanged. Both selected holders speak `/2` and
only `/2`: `claude_agent.py:117` sets `TASK_SCHEMA = "baton.dogfood-task/2"`
and `dogfood_operator.py:768` sets `_TASK_SCHEMA = "baton.dogfood-task/2"`, each
a closed equality check. A `/3` launch would have **refused at both ends before
the implementation agent could type anything**.

So the two roles are named and kept apart:

| artifact | role | schema |
| --- | --- | --- |
| the launch task | **launch input** to the implementation Job, on the selected existing runtime | `baton.dogfood-task/2` |
| `TASK-INSTRUCTIONS.md` | the `instructions` member of **that `/2` task** | — |
| `CONTEXT-CONTRACTS.md` | **test data and acceptance surface** for the produced correction | defines `/3` |
| the `/3` fixtures | exercised deterministically against the **two new holders** the turn produces | `baton.dogfood-task/3` |

**Compatibility is not deferred.** `<BASE>`, `<RUN>` and the image digest stay
deferred; the *schema the launch speaks* does not, because deferring it is what
made the bootstrap circular. The correction is authored under `/2`, and `/3` is
first spoken by the code the correction creates — verified at both new holders
by the focused cases in `VERIFICATION.md`, which is W321776's claim to make.

## THE END-TO-END TRACE, one stage per row

Review finding 1 and 3 asked for this: for every stage, its input, its producer,
the **bytes actually available** there, and the immutable identity. The
demonstration edit is **a change to `claude_agent.py`'s task-schema acceptance
that nobody can know at sealing time**, because the whole point of the turn is
that the provider decides how to write it.

| stage | input | producer | bytes available | immutable identity |
| --- | --- | --- | --- | --- |
| 1 · seal | `TASK-INSTRUCTIONS.md`, the fixture, the argv, the launch constraints | the preparing party | the instruction text and the sealed fixture | the `/2` task's digest and the sealed input digests, **never rewritten afterwards** |
| 2 · materialize | that sealed set | manager: `workspaces.compose_input_root` **writes and binds `input.json` / `assignment.json`**; `source_boundary.nominate_source` **proves the source directory's identity without reading its contents** | the input root's documents, and the read-only mount at `SOURCE_TARGET` | the bound input manifest |
| 3 · line | the declared base | manager's review-cycle lifecycle: one durable private repository, detached, mounted writable at `WORKSPACE_TARGET` | the whole repository worktree | `<BASE>`, and the entry head the writer grant admitted |
| 4 · provider | the instruction text | the **implementation agent** | the worktree it edits in place | none yet — **this is the stage whose output nobody could have sealed** |
| 5 · measure | the edited worktree | `claude_agent._line_status` → `_line_delta`, then `_identical_bytes` | the bounded status-reported delta, proved byte-for-byte, with ignored/special exclusions **disclosed** | `changed_paths`, `removed`, `collection` |
| 6 · **worker view** | the measured candidate bytes and the declared sealed inputs | **new bounded worker materializer work** (below) — a disposable view the worker owns, **never the edited worktree** | the measured changed/deleted paths applied over the candidate's own bytes, plus each sealed input materialized by `name` | the `/2` result's `verification` member, produced in a view that is then destroyed |
| 7 · retain | the measurement | `claude_agent._publish_line`: `PATCH` (`diff --no-renames base..head`), the verification transcript, the result record, and `BUNDLE = "objects.bundle"` for `base..HEAD`. **No candidate tree, deliberately** | the **incremental** object transport plus the patch | `base`, `entry_head`, `head`, declared in `CLAIM_NAMESPACE` as `{base, head, transport, recap}` |
| 8 · **operator view** | that retained output **and the accepted-base object source** | the operator's own independent rerun, in its own ephemeral root (`dogfood_operator`, `dogfood-verify-` prefix, output captured to a file and kept out of durable members), plus new bounded materializer work | the accepted base's objects from the deployment's **own retained repository**, the transport's objects resolving `head`, and the same sealed inputs from the same seal | `result_digest`, `result_head`, `transport` |

### STAGE 6 IS A FRESH DISPOSABLE VIEW, and calling the worktree one was wrong

Review 2026-10-18T09-49-00Z, and this is the central requirement rather than a
refinement. My previous draft said the worker view was "the worktree itself" and
that "nothing is transported, because the edits are already here". That renames
the edited candidate a view; it does not isolate anything. DESIGN VER-3 requires
the worker **and** the independent operator each to materialize a **fresh
private verification view**, and verification may not modify retained candidate
bytes or add fixtures to the proposal output. The reassessment this Work
descends from identified direct-in-candidate verification as precisely the
missing behaviour — so I had reinstated the finding inside its own correction.

Two concrete consequences of getting it wrong, which is why an identity
comparison is no substitute:

- a command that **writes or deletes a source file** would alter the retained
  candidate, and a post-run digest would detect it only after the damage;
- a **timeout or start-failure cleanup** that removed this "view" would remove
  the **candidate**.

**And current code does verify in place.** `claude_agent._verify`'s own first
line is "the task's OWN command, in the candidate copy", and for a line profile
the candidate *is* `OUTPUT_ROOT` — the retained worktree. So the worker-side
fresh view is **new bounded worker materializer work**, named as new exactly as
the operator's is, and it is W321776's to implement:

| obligation | what the materializer must do |
| --- | --- |
| obtain the bytes | take the candidate's own bytes for every path, with the measured `changed_paths` applied and every `removed` path **absent** — the changes and deletions are reflected **before** the command starts |
| obtain the inputs | materialize each declared sealed input by `name` from the seal, at its view-relative destination, verified against `content_digest` |
| own the view | the view is created by this materializer and is the only thing it may delete |
| preserve | the retained candidate and the sealed inputs are byte-unchanged on success, on test failure, on timeout, on a failed start and on a partial materialization |
| clean up | cleanup removes the **view** and nothing else; the candidate and the seal are not this step's to touch |

The direct-verification exception is removed from every document in this packet,
not softened.

### STAGE 8'S TRANSPORT IS INCREMENTAL, so its prerequisites must be named

`claude_agent.py:3016-3018` creates `objects.bundle` for **`base..HEAD`**. That
range does not carry the base history, so a receiving repository that lacks
`base` cannot resolve `head` from the bundle alone — and my previous draft
described initialising the operator view and resolving `head` from the transport
without saying where the prerequisite objects come from.

They come from one named place: **the deployment's own retained repository, at
the accepted base** — the `repository` root of the instance layout, whose
`refs/heads/main` is advanced to an accepted commit only by
`tools/accepted_base.py` as a supported, receipted transition. The source driver
supplies the operator's view from that object source, and then the bundle is
applied over it.

| obligation | the refusal |
| --- | --- |
| the accepted-base object source is reachable and holds `base` | missing → `missing-input`, **before** verification |
| the bundle's prerequisites are satisfied in the receiving repository | unsatisfied → `materialization`, and the command does not start |
| the bundle resolves exactly the `head` the retained result published | mismatch → `materialization`; a bundle for some other head is not this result's candidate |
| the result record the evidence names is the one whose `head` was resolved | mismatch → `materialization`, so `result_digest` cannot drift from `result_head` |

**NOT FROM AN AMBIENT HOST CHECKOUT, and not inferred.** A digest proves which
objects were wanted; it does not supply missing ones. An operator that fell back
to whatever repository happened to be on the host would be verifying a candidate
assembled from an unaudited source, which is the same class of defect as
verifying in the candidate itself. This is the paired-view milestone's own
boundary, not a new generic staging mechanism.

### What is existing and what is NEW, named rather than blurred

Review finding 3 is right that I attributed byte transport to helpers that do
not do it. Corrected:

- **Existing, and it is the real transport:** `objects.bundle` for `base..HEAD`,
  declared in the claim metadata as `transport` beside `base` and `head`. That
  carries bytes, not digests.
- **Existing:** the operator's independent verification rerun in its own
  ephemeral root, refusing a root inside retained proposal storage.
- **Existing, but not what I said it was:** `compose_input_root` writes and
  binds `input.json`/`assignment.json`; it does not materialize this fixture
  into a verification view. `nominate_source` proves directory identity and
  reads no contents. `_line_delta` measures a **bounded** delta and discloses
  exclusions; it supplies no whole-tree identity.
- **Existing, and it is where verification runs TODAY:** `_verify`'s own first
  line is "the task's OWN command, in the candidate copy" — so the current
  worker verifies **in the candidate**, which for a line is the retained
  worktree. That is the behaviour VER-3 forbids and the behaviour this packet
  must replace, not describe.
- **NEW BOUNDED WORK, TWO MATERIALIZERS, both W321776's:** the **worker's**
  disposable view (stage 6), because nothing today builds one; and the
  **operator's** (stage 8), because `_publish_line` retains **no candidate
  tree**, so nothing builds a second worktree from the retained transport
  either. Both are named as new rather than credited to an existing helper.

**A digest list is not bytes, and that was the flaw in the previous draft.** The
operator obtains bytes from the transport and the seal; the digests it then
publishes are what it *measured*, afterwards.

### The remaining selections

| element | selection |
| --- | --- |
| run identity | `<RUN>` — allocated when the owner selects execution |
| declared base | `<BASE>` — the commit of **accepted** W321528 delivery; `tools/accepted_base.py` is the supported transition that records a human-accepted base |
| source profile | `git-line`, with the pairing asked of `checkout_plan` by both holders rather than restated — `dogfood_operator.py:744-750` already delegates exactly this |
| candidate → view mapping | the whole candidate tree at `candidate/`, `working_directory` at `candidate/v12/python`, the sealed input at `sealed/...`; declared in the task and inferred by neither holder |
| worker image / runtime | the existing digest-bound worker image and the single-implementation supervisor, unchanged; no new image is built |
| provider for the implementation | the **implementation agent** — a real provider turn, because authoring the correction is authoring code |
| provider for runtime verification | deterministic **fake/replay** providers at their own boundary |
| focused verification invocation | the literal argv above in each view, plus the negatives in `VERIFICATION.md` |

**No generic recursive copier and no maintenance container** — VER-3 forbids
both and this packet asks for neither. The genuinely new things are the **two
view materializers**, stages 6 and 8, each declared as new work with its scope
stated rather than smuggled in as an existing interface. They are not a widening
of VER-3: they are what satisfying its isolation requirement costs, and the
previous draft avoided that cost by calling the edited worktree a view.

**THE IMPLEMENTATION AGENT AND THE REPLAY PROVIDER ARE NOT THE SAME THING, and
conflating them is the mistake this row exists to prevent.** A replay provider
proves the *runtime* behaves — that a context is built, refused, cleaned up — and
it **does not author the correction**. The paired holder change is written by an
implementation turn. So a packet that ran only replay providers would prove the
plumbing and deliver no code, and a packet that claimed a replay run had produced
the correction would be claiming authorship for a fixture.

## Bounds, and no live selection

No live run is selected by this packet. When the owner selects one, these are the
proposed bounds — a selection, not a correctness claim:

| bound | value | why |
| --- | --- | --- |
| implementation invocations | 1 | one paired correction |
| provider turn | 900s | the two 600s turns in this campaign both timed out, and a paired holder change is larger than W321528's slice |
| verification command | 30s | the gate measured 0.222s in this claim; 30s is the composer's fresh-mode constant and is ample |
| total | 1500s | turn plus launch, materialization, freeze and cessation |
| cleanup | 60s | unchanged |
| retry | none | a failed paired correction returns for coordination with its evidence |

The deterministic provider is the default for runtime verification, per the
standing v12 ruling. This packet names **no live provider question** beyond the
authorship turn itself, and invents none.

## The upstream sequence, retained explicitly

1. **W321688** delivers and is accepted; human checkpoint **W322125**.
2. **W321528** delivers and is accepted — its candidate `2c89d3aa` is
   **unaccepted** today and must not be bound as a base.
3. Slawomir commits the accepted result; that commit becomes `<BASE>`.
4. **W321776** — the paired product delivery — waits on W321528 *and* this
   packet, and binds `<BASE>` with these pins re-measured against it.

This packet is **disjoint** and is corrected now. It is not gated on upstream
implementation, and it binds no unaccepted candidate.

## What the packet does NOT do

No product edit, no live model, no engine or container, no deployment, no Git
mutation, no whole-suite expansion, and no edit to W321528's packet or to
`claude_agent.py` — that overlap is gated in W321776 and stays there.
