# W325959 revision 4 — native pilot preparation

Status: proposed packet for independent review; no deployment or launch selected.
This revision supersedes revisions 1–3 as the proposed preparation sequence only;
their files and review evidence remain historical. Decisions: ../FINDING.md,
../PLAN.md and reviews 2026-10-18T20-37-30Z, 20-41-30Z and 20-44-22Z.
Parent selection: baton:work/records/2026/10/finding-v12-development-coordination-pilot/SELECTION-325909.md.

Selected destination: `/home/sl/baton-instances/native-coordination-pilot-w321608-1`.
Selected source: `14e52d80679de5e844f72324df632da5e01cf393`.
Observed checkout HEAD during this preparation: `03b94fc80744671150cca1997712ee95a6537df5`;
`git diff --stat 14e52d80679de5e844f72324df632da5e01cf393 HEAD -- v12`
and the working-tree v12 diff are empty. The selected destination is absent.
Slawomir owns retention, backup/restore and Git. No existing deployment is reused.

## Deliverables and evidence

`prepare.py` is the disposable proof; `owner_operations.py` is the proposed
owner-run repository/configuration driver. They share the manifest, task,
configuration and submission composer and registration routine. The latter has
no simulated installer, Git runner, claims, receipts or diagnosis Work. It does
not submit or serve. `configuration/` holds pinned templates; every consumed
input/template is bound by `FROZEN-INPUTS.json`, verified before effects.
`MANIFEST.json` binds this packet, scripts, inputs and retained evidence.

Final coherent proof: `evidence/run-328521-4/PREPARATION.json`: 60 checks,
one successful composed scenario, one intentionally failed harness control,
zero unexpected failures, 0.060 seconds. Generated configuration, submission,
manifest, exact task bytes, authority readback, scoped grants, dossier documents
and repository report are under that run's `generated/`. These are **disposable
identities and paths**, never production inputs. `evidence/PIN-REFUSAL.json`
proves a changed frozen task refuses before creating root or evidence paths.
Earlier runs are retained, not overwritten.

The proof uses one real disposable authority and supported bootstrap installation
and in-place configuration. A recording runner substitutes nonfunctional repository
layouts and controlled Git readbacks; `_identity_of` substitutes a fixture bundle
identity, and `checkout` substitutes an external location. These boundaries prove
command composition, explicit no-repositories installation, installed-field
preservation, actual generated documents, route/grant ownership, positive runtime
consumer comparison and unchanged bytes on binding-drift refusal. They do not
prove Git objects, image availability, a real packaged executable, provider
behavior, live cessation or a useful authored quickstart. No Git command, engine,
provider, credential-content read, image build, serving or Job admission ran.

## Accountable inputs

The seven `inputs/*_policy.json`, `role_instructions.json` and `toolchain.json`
documents are concrete **proposals**, not grants. Their canonical digests replace
all seven inherited repeated-hex identities. `configuration/manifest-inputs.json`
maps each identity to its document. The source descriptor is inherited from the
frozen nominated-mount profile; its empty content inventory is not a source-tree
hash. Git-line base selection pins actual source use.

`inputs/native-finding.md` and `native-plan.md` bind the new flat native dossier;
the composer replaces the inherited unrelated dossier and repeated-hex record
hashes. The native authority generates the UUID, Work id, principal and generation
readbacks. The dossier root `native-pilot` maps to `<destination>/generated/dossiers`.
W325959 remains preparation provenance; it does not own the native deliverable.

`inputs/policy.json` replaces the prior pilot's 900/30 policy with the selected
3600/900 per-invocation policy; its canonical identity is used by workers, manifest
and submission. `execution_limits` in Job submission `/2` supplies the effective
provider-turn and verification-command ceilings. No cumulative limit is invented.
9000 seconds assumes exactly one provider and one verification invocation in each
of two stages; 9900 seconds is only a proposed operator observation window. The
120-second cleanup observation allowance is proposed, not a measured cessation
bound. The product stop-vector default is 30 seconds per runtime; uncertain runtime
state retains its hold irrespective of any observation window. No automatic retry.

Frozen profile/adapter provenance comes from the earlier failed-reporting packet,
with the original deployment retained under `inputs/deployment.json`. Selected
image: `sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2`,
reference `baton-v12-claude-worker:w239528-244216`, Claude CLI 2.1.247, model opus.
This is a proposed reuse by identity, not fresh image/provider certification.
Network is bridge; the single claude slot references operator-file
`w202663-development` via `/home/sl/.baton/credential-sources.json`. No secret
content is included. A separately selected engine inspect must confirm the exact
image before launch. An image build is a build, never called a read-only check.

The existing `v12/python/build/out/distro` predates the selected source and is
**not certified for this packet**. A fresh host bundle, its identity readback and
file digests remain a separately selectable build output. No invented bundle hash
is presented. Record/review those outputs before installation/admission.

## Proposed owner-run sequence (all commands below unexecuted)

Use an owner-prepared clean checkout at the selected base. Preparing that checkout
or invoking the repository operation below mutates Git and belongs to Slawomir.
The driver refuses a different source HEAD, dirty source, or an existing selected
destination. A failed partial preparation is retained for inspection; never rerun
blindly or delete it to make the freshness check pass.

In an owner shell, set `SOURCE` to that absolute selected checkout, `PACKET` to
this revision's absolute directory, `DEST` to the selected destination above, and
`PY` to the prepared interpreter returned by `python3 -m tools.environment interpreter`
from `$SOURCE/v12/python`. These are shell variables, not inferred deployment paths.

1. If a matching prepared environment is unavailable, explicitly select and run
   `just -f "$SOURCE/v12/justfile" setup`. Build to a new output directory with
   `just -f "$SOURCE/v12/justfile" build /tmp/w325959-owner-build` and read
   `/tmp/w325959-owner-build/out/distro/baton-v12-stack identity`. Set
   `DISTRO=/tmp/w325959-owner-build/out/distro` (the packaging spec COLLECT name
   is `distro`). Record the real identity plus every bundle file's SHA-256; independent
   review must bind that output before using it. No existing old distro is substituted.
2. From `$SOURCE/v12/python`, with `PYTHONPATH=src:.`, run:
   `"$PY" "$PACKET/owner_operations.py" repositories --owner-selected --source "$SOURCE"`.
   This calls supported `bootstrap.prepare_repositories` once with both workers
   in the plan. It creates independent target.git, workspace,
   source-implementation-pilot and source-review-pilot using `clone --no-local`,
   proves distinct common directories/no borrowed objects and selected base
   availability. The plan-only placeholder Work id is never registered.
3. Install exactly once using the now-prepared repositories:
   `just -f "$SOURCE/v12/justfile" bootstrap "$PACKET/configuration/install-inputs.json" "$DEST" "$DISTRO" "--no-repositories"`.
   This worker-free install creates the actual authority and preserves explicit
   integration_target/integration_workspace. Normal repository-producing install
   would refuse the existing paths; the explicit option is essential.
4. From `$SOURCE/v12/python`, `PYTHONPATH=src:.`:
   `"$PY" "$PACKET/owner_operations.py" configure --owner-selected`.
   It checks real repository independence and HEADs before writes, registers
   routes, creates native W1 with contract `v12-assignment-1`, grants capabilities in `scope:native-pilot-quickstart`, binds a flat dossier,
   stages exact task bytes, seals the manifest and invokes supported bootstrap
   **in place**, without destination/distro operands. It preserves installed
   selections and writes `$DEST/generated/` with fully resolved inputs and
   submission. It leaves the real Work unclaimed on impl. Read back the actual
   UUID/Work/policy generation and canonical target; the target must equal the
   selected base. No diagnostic placeholder Work is created in this path.
5. Independently review those actual generated artifacts and the actual bundle/image
   provenance. Only after separate admission/launch selection, submit from
   `$SOURCE/v12/python`, `PYTHONPATH=src:.`:
   `"$PY" -m tools.job_manager --store "$DEST/db/jobs.sqlite3" --incarnation w325959-owner-submit-1 --authority-uuid ACTUAL_UUID submit --document "$DEST/generated/submission.json"`.
   Replace ACTUAL_UUID with the exact installed readback; never a preflight UUID.
   Then use `just -f "$SOURCE/v12/justfile" start "$DEST"` and the corresponding
   `status`, `monitor`, and `stop` recipes. Submission and serving are separate
   from this packet's preparation and were not executed.

## Ownership, delivery and recovery

| Purpose | Native participant/route |
| --- | --- |
| Author | baton.claude-pilot / impl |
| Independent reviewer | baton.reviewer-pilot / rview; outgoing owner |
| Verification receipt | baton.verifier-pilot / scoped verify |
| Review receipt | baton.reviewer-receipt-pilot / scoped review |
| Human disposition | baton.slaw / owner; scoped approve, integrate, close |
| Dedicated diagnosis | baton.diagnostician-pilot / diagnosis |

The required integration profile still names baton.integrator-pilot and bootstrap
registers its scoped integration capability; there is no integration worker or
stage and no automatic integration admission. Owner has neither verify nor review.
The independent receipt actors must evaluate real evidence; no preflight receipt
is usable. An actual exceptional outcome gets a separately created diagnostic
Work on diagnosis without stealing its execution claim or clearing runtime holds.

The task changes only v12/QUICKSTART.md. Its structural check proves four headings,
length floor and absence of TODO/TBD/FIXME; semantic review must judge command
correctness and usefulness. Preserve exact retained candidate bytes and reviewer
verdict, then human approval/integration/closure and the native readback. The
accepted W321690 `PACKET.md` section 9 owns the disposition procedure; do not
substitute a fixture or completed stage for those receipts.

Stopping a supervisor is not container cessation. Preserve unknown-runtime gates,
exact attempt/operation identities and private outputs, inspect retained status
and logs, and use supported reconciliation. `record recovery-check` reports/refuses;
it does not admit. Slawomir owns backup/restore with one writable authority.
Withdrawal preserves native history; no backlog migration, reverse-copy authority,
cutover or successful context-reuse claim follows from this packet.

Human Git checkpoint remains pending after independent acceptance. Suggested commit:
`docs: prepare instance-specific native v12 pilot packet`. No commit was made.
