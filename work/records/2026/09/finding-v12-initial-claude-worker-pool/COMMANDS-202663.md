# Deployment commands — W202663

Rewritten at claim208463. **Every earlier version of this file described
`/home/sl/baton-v12-instance-2026-09-18T10-38-52Z`, which owner pass 208215
superseded and which now lives under `/home/sl/baton-v12/archive/`.** Those
paths are history, not instructions.

Three parts: what exists now, what the owner runs to install the next instance,
and what must be verified on it before anything is called ready.

## Part 1 — artefacts that exist (built and recorded)

### The two supported production images

```sh
cd /home/sl/src/baton/v12/python
PYTHONPATH=src:. python3 -m tools.worker_image \
  --engine docker \
  --context /home/sl/src/baton/v12 \
  --dockerfile /home/sl/src/baton/v12/worker/Dockerfile.claude \
  --tag baton-v12-w202663-provider:e486652c
# -> sha256:9ff3322f58f08275bfc4bb2cd511fb7a6b156e991449ee36f365d05e2133529d

docker build --no-cache --platform linux/amd64 \
  --build-arg PROVIDER_BASE=sha256:9ff3322f58f08275bfc4bb2cd511fb7a6b156e991449ee36f365d05e2133529d \
  --tag baton-v12-w202663-integration:e486652c \
  --file /home/sl/src/baton/v12/worker/Dockerfile.integration \
  /home/sl/src/baton/v12
# -> sha256:b9b75acc300170d99649d0497f9f93876ab5d8d73a9157c9861c5763f17c9561
```

Neither builds without this Work's `v12/.dockerignore` correction
(`FINDING.md` D1). Provenance: `PROVENANCE-202663.json` and
`COPIED-INPUTS-207111.json`.

### The two deterministic fixture images

```sh
C=/home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool/fixture-context
for n in producer integrator; do
  docker build --pull=false --no-cache --network none --platform linux/amd64 \
    --file $C/Dockerfile.$n \
    --tag baton-v12-w202663-fixture-$n:claim208217 $C
done
# producer   -> sha256:6ae290f9135c4c79bf2a74c2425deb839bccf77190927bf6529cf34bd622423f
# integrator -> sha256:9944eef7363e8f8fd0d917bd71fbe19dfb177b6232b7064f3c3a4785f307be0f
```

W198667's reviewed worker bytes at two entrypoints. They enter no provider and
read no credential.

### The emitting producer fixture (claim208916, review208890)

```sh
C=/home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool/fixture-context
docker build --pull=false --no-cache --network none --platform linux/amd64 \
  --file $C/Dockerfile.emitting \
  --tag baton-v12-w202663-fixture-emitting:claim208916 $C
# -> sha256:e48e72dfaaed321a34f1bfdd8ceca260c63d852c3fdc625da1458b02eaf7e9e8
```

The same reviewed producer plus deterministic prose on the wrapper's stdout
and stderr (`emitting_agent.py`), because a silent fixture cannot satisfy
nonempty retained logs. Selected with `compose-verification-208217.py
--emitting` for the implementation role only; its output is fixture output,
labelled in every line, and proves capture retention — never provider
evidence. `assert-capture-208916.py` is the executable form of that proof.

### The corrected runtime — already built and recorded

```
/home/sl/src/baton/v12/python/build/out/distro
# executable sha256:6af693b295dd666eaa9d118f2a6b4242a396f6a872ca4f68b7fc9f3373cae4ba
# whole bundle sha256:425e624e69deecb644546ff7891a84c2662ea79d5548145ab7dda61c1e9eccbb (81 files)
```

Built in claim209102 **after** the D7 correction (`FINDING.md` D7: a settled
allocation from a retired pool generation crashed the manager at restart),
with the corrected `/2` prospective snapshot taken BEFORE the build (109
inputs, `PROSPECTIVE-INPUTS-209102.json`). It supersedes `7040dd00…` — the
runtime at `instance-2026-09-19T04-02-31Z`, whose completed-lifecycle
evidence is preserved. Records: `RUNTIME-BUILD-209102.json`,
`BUNDLE-MANIFEST-209102.json`.

#### Superseded: the claim208531 build (history, preserved)

Built in claim208531 **after** the D4 correction — it supersedes
`sha256:48b12f15…` (the runtime installed at
`/home/sl/baton-v12/instance-2026-09-19T02-05-20Z`, which predates the
correction). `RUNTIME-BUILD-208531.json` records the build;
`BUNDLE-MANIFEST-208647.json` binds the complete one-folder bundle, digested
by `tools.instance.manifest` — the installer's own digester. The prospective
input snapshot taken before this build is PARTIAL
(`PROSPECTIVE-SUPERSESSION-208647.json`): identity is established, input-set
completeness is not. **Do not rebuild**: a rebuild produces a different
artefact, and installing it while citing these digests is exactly what
review208585 [R1] forbids.

## Part 2 — installing the next instance (the OWNER runs this)

Owner ruling 208460: *"Owner will install a fresh timestamped instance under
/home/sl/baton-v12/ afterward; no agent replacement/reset of the current
instance."* Nothing in this Work installs it, and the current instance is
preserved as evidence.

```sh
cd /home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool
./install-next-instance.sh
```

One command, no operands. It refuses unless the bundle on disk still digests
as the reviewed artefact above, selects and retains one fresh UTC timestamp in
`selected-instance.txt`, passes the reviewed distro EXPLICITLY to
`just bootstrap` (so nothing is rebuilt), and compares the installed identity
back against the same records. `install-inputs.json` beside this file names no
workers and no Jobs, which is what a fresh install is. The destination must
not exist — the installer refuses an existing runtime in place (`FINDING.md`
D3), and that refusal is correct.

## Part 3 — verification owed on that instance, in order

Each step names what it proves and what it does not. **`just start` is the
INSTALLED path; running the checkout instead proves nothing about the installed
runtime** — a line review207292 drew and this file keeps.

1. **Identity.** `just --justfile <dest>/justfile identity` and compare
   `instance.json`'s `identity.sha256` against the digest recorded for the
   rebuilt runtime. This establishes identity, not behaviour — the owner's own
   qualification in pass 208215.

2. **Compose the deterministic verification pool.** No file is edited: the
   composer takes the retained instance and reads its persisted identity.
   ```sh
   cd /home/sl/src/baton/v12/python
   PYTHONPATH=src:. python3 <dossier>/compose-verification-208217.py \
     --instance "$(cat <dossier>/selected-instance.txt)"
   PYTHONPATH=src:. python3 -m tools.bootstrap --inputs <dossier>/pool-bootstrap-inputs.json
   ```
   Expect `complete: true, refused: []`. This regenerates
   `pool-bootstrap-inputs.json` and `pool-submission.json` for that instance.

3. **Check the policy pin, every time — as a gate.**
   ```sh
   <dossier>/check-policy-pin.sh
   ```
   It selects the retained instance FIRST (review208585 [R2]: importing the
   composer without `select_instance` reads the historical instance's pin) and
   exits nonzero on inequality — recompose and re-apply then; do not start.
   Measured on the superseded instance: the bump is **per Work** — 7 with one
   Work, 14 with two. Predictions are checked, never trusted.

4. **Start and submit.** With `DEST="$(cat <dossier>/selected-instance.txt)"`
   and `UUID` read from `$DEST/authority-identity.json`:
   ```sh
   just --justfile "$DEST/justfile" start
   cd /home/sl/src/baton/v12/python
   PYTHONPATH=src:. python3 -m tools.job_manager \
     --store "$DEST/db/jobs.sqlite3" \
     --incarnation w202663-verification-submit \
     --authority-uuid "$UUID" \
     submit --document <dossier>/pool-submission.json
   ```
   (`verify-next-instance.sh` prints exactly this with every value filled in.)
   The fixture images enter no provider, so this reaches no model.

5. **Carry it to a terminal report-and-hold**, and prove each of these
   separately rather than inferring one from another: configured identity,
   runtime-recorded attribution, actual execution, and completion. The
   integration image's execution is **not** proved by its attempt record.

6. **Capture proof.** Read the retained streams with
   `tools.attempt_logs_command … locators` and then `read`. The claim208217 run
   left all six streams absent and the native room empty, which proves the
   reader works and nothing about captured bytes: a real proof needs a
   workload that actually emits and nonempty bytes read back after cleanup.

7. **Cleanup, fencing and recovery.** Supervisor stop is not cleanup; account
   for destroyed runtimes, not-started runtimes and held allocations as
   distinct facts.

8. **Then, and only then, the real Claude pool.** Recompose
   `compose-pool-207219.py` for the new authority and destination, re-verify
   its pin, and rewrite part 2 of this file against it. That pool's
   implementation and review workers enter a REAL provider; submitting its Job
   starts model turns and is not authorized by this Work.

## What this Work has not established

- that the corrected runtime behaves as intended once installed — only that
  the correction's own focused cases pass in the checkout;
- that the nominated development source carries the accepted prerequisites;
- a COMPLETE prospective build-input snapshot: the one taken before the
  claim208531 build is PARTIAL (it omitted the build lock, the spec and the
  recipe — `PROSPECTIVE-SUPERSESSION-208647.json`), the omissions cannot be
  reconstructed for that build, and the corrected `prospective-snapshot.py`
  must run immediately before the next selected build.
