# Current-instance fact sheet — what "this instance" means, and which records are historical

W325959, claim361756. Answers `review-2026-10-24T03-24-47Z.md`, which confirmed
two semantic blockers in `../quickstart-correction-361660/`. That packet is
preserved and superseded.

**R1 — assignment generation is not pool generation.** The previous revision
asserted that this deployment's pool generation 1 determines
`runtime-quiescence:1`, in the candidate, in this fact sheet's generation row
and in the checker's own rule. `Authority.cancel` instead fences
`gate_token(GATE_QUIESCENCE, str(expect["generation"]))` — the **exact
assignment's** generation. The axes diverge on this very instance: the review
assignment is generation 2 while pool, allocation and resource-token
generations are all 1. Corrected in all three places, with any literal gate
now labelled as an example for one assignment.

**R2 — a participant claim must be scoped to the evidence that supports it.**
The previous revision used this v11 coordination deployment's participant
roster to conclude that a participant is absent from instance 4's separate
v12 authority. That inference was invalid and is withdrawn. The claim is now
made from instance 4's own configuration and says what that configuration
supports: it configures no diagnostic handler.

It also answers `review-2026-10-24T03-10-08Z.md`, whose corrections are
carried forward unchanged.

This is the context the task `w321608-native-operator-quickstart-4` did not
supply. It said "this native v12 coordination instance" and named no
destination, authority, Job, bundle or reference precedence; the historical
dossiers in this repository describe **instance 1**, and both stages of the
live run judged that older surface. The correction is therefore a context
document plus a corrected candidate, not a runtime change.

**This is a direct development correction, not another v12 Job, not an amended
live receipt, and not permission to execute anything.** Nothing here was
submitted, started, stopped, retried or imported.

## Precedence — which source wins when two disagree

1. **The installed command and the installed configuration.** What
   `$DEST/distro/baton-v12-stack` actually parses and what
   `$DEST/deployment.json` actually records are the facts about this
   deployment. A source-level entry is not a deployed one, and the reverse is
   also true: this bundle's dispatcher differs from the bare source parser in
   one operand-ordering detail recorded below.
2. **The committed source at the declared base**, `614668e0`, for behaviour
   the CLI does not print.
3. **Records in `work/records/`**, which are evidence of how a thing was
   decided. A record describing another instance or another revision is a
   **historical** citation and must be marked as one wherever its
   instance/version differs from the row below.

## The current facts

| Fact | Value | Where it is read from |
| --- | --- | --- |
| destination (`$DEST`) | `/home/sl/baton-instances/native-coordination-pilot-w321608-4` | the installed tree |
| authority uuid | `19b4f1459c2442e4aec8c7cd23e92312` | `$DEST/authority-identity.json` |
| Work | `19b4f145-W1` | `$DEST/deployment.json` `job_work_id` / `review_work_id` |
| Job | `quickstart-d` | `$DEST/deployment.json` `job_bindings[0].job_id` |
| submission | `sub-w321608-quickstart-4` | the published status document |
| declared base / canonical target | `614668e0831e8c87cdae11ca43620e0d544a84d5` | `$DEST/deployment.json`, and the task |
| build stamp commit | `614668e0831e8c87cdae11ca43620e0d544a84d5` (`dirty: true`) | `baton-v12-stack identity` |
| installed executable | `sha256:f4e9cecf0ccb7211b5c36691a35d8499cff94c7e64f1aff18c36bb50b13206d3` | `../bundle-361217/BUNDLE.md`, confirmed by `identity` |
| bundle folder digest | `1b014603aec40e9f6d9c03a8b21ae74a02d9f1fef1ff95fc0f3e8a851a229c07`, 81 files | `../bundle-361217/MANIFEST.json` |
| stages | `implementation` then `review`, review `depends_on` implementation; no integration stage | the submission, and `view --job quickstart-d` |
| terminal policy | `report-and-hold` | the submission, printed by `view` |
| execution limits | **3600s provider turn / 900s verification command**, per invocation | the submission `execution_limits` |
| retention disposition | `retain` | `$DEST/deployment.json` |
| pool / policy generation | 1 | `$DEST/deployment.json` |
| allocation generation | 1, both stages | the published snapshot |
| resource-token generation | 1, both stages (`tokens.generation_of`) | `attempt-diagnostics` over the same document |
| **assignment** generation | **implementation 1, review 2** — and this is the only one the quiescence gate uses | the published snapshot, `receipts[].detail.result.assignment.generation` and `runtime.assignment.generation` |
| implementation worker / participant | `implementation-pilot` / `baton.claude-pilot` | `$DEST/deployment.json`, `fresh5-361402/configure-inputs.json` |
| review worker / participant | `review-pilot` / `baton.reviewer-pilot` | same |
| verification receipt actor | `baton.verifier-pilot` | `receipt_participants` |
| review receipt actor | `baton.reviewer-receipt-pilot` | `receipt_participants` |
| approval / owner | `baton.slaw` | `receipt_participants`, `owner_participant` |
| integration profile | `git`, integrator `baton.integrator-pilot` | `$DEST/deployment.json` — **configured for the deployment; this Job has no integration stage and does not use it** |
| launch home / log delivery root | `$DEST/state/launch` / `$DEST/state/launch/logs` | `$DEST/deployment.json` `launch_home`, and the directory exists with both attempts |
| workspace storage | `$DEST/state/workspaces` | `$DEST/deployment.json` |
| published status document | `$DEST/state/status.json` | the publisher |

## What the live run actually produced, and its exact identity

Both stages of `quickstart-d` **completed**; allocations released, runtimes
destroyed, tokens returned (published snapshot `2026-10-24T03:09:30.489Z`;
independently hashed by the reviewer in `../evidence/review-361632/READBACK.json`).
That pipeline result is preserved and is not what this correction touches.

What the implementation stage produced is a candidate whose **content** is
about the wrong deployment:

| Retained artifact | sha256 | bytes |
| --- | --- | --- |
| `proposal/change.patch` | `9468ec71a9a1e693e2d7718b1584ec60f82c9ffbda0ca9dc504c9e3887e1bdfd` | 11317 |
| `proposal/result.json` | `af9df6dc7a1da3f20ed6e2ef1f0c26671470cb5f7a318f97b502df19509187e9` | 1203 |
| review `findings/report.json` | `f1b569316d97fb0803f912af1d83916e353198352d7b14fbf537842bb9ee41ff` | 7888 |

Proposal head `5d747fecc950989a7ef0a0d50e58a1d2e15a657f`, declared and entry
base `614668e0…`, one changed path, `v12/QUICKSTART.md`. The retained
reviewer's verdict was `ACCEPTED` — and it says, in its own words, that it
checked the claims against `git show 14e52d80:…`. **Both documents are
retained unchanged.** Nothing in this packet rewrites them, and the review's
verdict is preserved as the record of what that reviewer judged, not
corrected in place.

## The five content defects, and the fact each one contradicts

| # | What the retained candidate says | What is true of this deployment |
| --- | --- | --- |
| 1 | `DEST=…native-coordination-pilot-w321608-1` | the destination is `…-w321608-4` |
| 2 | "The Job is `quickstart-a`" (and `view --job quickstart-a`, twice) | the Job is `quickstart-d` |
| 3 | "built from the selected source `14e52d80679de5e844f72324df632da5e01cf393`, which is also the Job's declared base" | the build stamp and the declared base are both `614668e0…` |
| 4 | "`attempt-diagnostics` and `manager fresh-attempt` … are **not in this build**" | **both are in this build.** `baton-v12-stack --help` lists `attempt-diagnostics`; `manager … fresh-attempt --help` prints its operands; `attempt-diagnostics $DEST/state/status.json` produces a report over this instance's own document |
| 5 | the diagnosis route participant is `baton.diagnostician-pilot` | the cited record (`matrix-325259/MATRIX3.md`, PACKET §9 table) names **`baton.diagnostician`**, and **this instance's configuration configures no diagnostic handler at all** — see the scope note below |

Defect 5 was not in the review's required list. It was found by checking the
claim rather than substituting the identifiers, which is what
`review-2026-10-24T03-10-08Z.md` asks for.

**The exact scope of the defect-5 claim.** What is read here is
`$DEST/deployment.json` and the packet inputs that produced it. They name
every participant this deployment selects: the two stage workers
`baton.claude-pilot` and `baton.reviewer-pilot`
(`workers[].deployment.participant`), the three receipt actors
`baton.verifier-pilot`, `baton.reviewer-receipt-pilot` and `baton.slaw`, and
the integrator `baton.integrator-pilot`. There is no diagnostic handler among
them and no key of any kind mentioning diagnosis. So the supported statement
is **"this configuration configures no diagnostic handler"**, and that is
what the candidate says.

What is *not* claimed, because nothing read here could establish it: that no
such participant exists in instance 4's **authority**. That is a separate
store with its own roster, this packet opens no store, and the v11
coordination deployment this implementer runs under is a different system
whose participant list says nothing about the v12 authority. The earlier
revision of this fact sheet (`../quickstart-correction-361660/CONTEXT.md`)
argued from that v11 roster; that inference was invalid and is withdrawn
here. The defect in the retained candidate stands on the narrower ground:
`baton.diagnostician-pilot` is not the name the cited record uses, and this
deployment configures no handler under any name.

## Two behaviours the corrected candidate states that the retained one did not

**The deployed dispatcher takes `--instance` after the subcommand, and only
immediately after it.** The bare source parser
(`v12/python/tools/stack.py`) declares `--instance` as a *top-level* option,
so `stack --instance X start` is the source form. The frozen command is the
other way round — `tools/stack_command.py` appends the verb and lifts a
leading `--instance`/`--root` pair back to the front. Measured on the
installed command:

- `baton-v12-stack monitor --instance <file> --interval 3` → parsed (refused
  only because the file named did not exist)
- `baton-v12-stack monitor --interval 3 --instance <file>` → `error:
  unrecognized arguments: --instance …`
- `baton-v12-stack --instance <file> start` → `refused: no subcommand named
  '--instance'`

So the retained candidate's `start --instance $DEST/instance.json` form is
**correct for the deployed command**, and it is kept. What is added is the
ordering rule, because the obvious "fix" against the source parser would
break every line.

**`attempt-diagnostics` takes one positional status document and has no
`--help`.** `baton-v12-stack attempt-diagnostics --help` prints `attempt
diagnostics unavailable: input is unreadable or not a supported status
document` and exits 2 — that is dispatch treating `--help` as a filename, not
a help interface. Its own usage line is `attempt-diagnostics
<status-document.json>`, and it "takes no store, instance or engine operand"
(`v12/python/tools/attempt_diagnostics.py`).

## Citations: current versus historical

| Locator | Status |
| --- | --- |
| `fresh5-361402/COMMANDS.md`, `fresh5-361402/INDEX.json` | **current** — how this instance was prepared and installed |
| `bundle-361217/BUNDLE.md` | **current** — the bundle this instance runs |
| `v12/STACK.md`, `v12/DESIGN.md`, `v12/instance-retention.md` | current, revision-independent |
| `revision-4/INSTANCE-PACKET.md` | **historical** — instance 1, source `14e52d80` |
| `finding-v12-pilot-workflow-rehearsal/PACKET.md` | the reasoning stands; **its instance identifiers are instance 1's** |
| `finding-v12-pilot-owner-disposition/PROCEDURE.md` | the procedure stands; operands must be taken from the row table above |
| `matrix-325259/MATRIX3.md`, `rehearsal-324985/RECEIPT-BOUNDARY.md` | the measurements stand; they are **not** statements about this deployment's configured participants |

## Boundaries of this packet

No provider, engine, `fresh-attempt`, `submit`, `start`/`stop`, deployment or
import ran, **and nothing was cancelled, reopened or retried** — the
assignment generations above are read from the retained snapshot of two
stages that have already completed. **No store was opened**: the
configuration facts come from `deployment.json`, `authority-identity.json`,
`generated/submission.json` and the published `state/status.json`, which are
files this deployment wrote. The reads performed were: `identity`, `--help`
on each subcommand,
`status --instance`, `view --status … --job quickstart-d`,
`attempt-diagnostics` over the published document, and two deliberately
non-existent `--instance` paths to measure operand ordering. Every one of
these opens no store and writes nothing; `status` and `view` read the
published snapshot only. The retained artifacts were read and hashed, never
modified. No Git mutation.
