# Q2 native editing-capture packet — preparation only

W385830, baton.codxpc claim E386207, assignment/ownership M386205; owner ruling checkpoint42da148f. Supersedes the execution proposal of M386203, preserving its packet and old Q1 evidence unchanged.
No build, engine operation, real credential access, provider call or native activation occurred during preparation. This packet proposes one future owner-selected editing attempt. It does not authorize that attempt.

## Fixed inputs and concrete placement

- **New image qualification is required.** Frozen manager/worker source is checkpoint42da148f plus the six owned paths in the parent candidate, bound by source-files.json/source.tar. The old accepted Q1 image34364fb1/source54fa is historical evidence only and is explicitly refused by this launcher. Three image files changed: codex_agent.py, provider_policy/codex.py and provider_policy/attribution.py. q1-build.json is the expected file/CLI identity, **not an observed build receipt**. No new image exists or is selected here. Independently accepted source checkpoint → separately selected rebuild/offline qualification → reviewed image evidence → owner-selected Q2 is the dependency order.
- `--image-evidence` supplies a separately reviewed Q1-format evidence bundle; `--image-evidence-sha256` binds the exact reviewed bytes. image_gate.py requires the changed worker-file hashes, pinned CLI binary/build, UID/home/tools/instructions, successful credential-free qualification, engine image identity, retained post-removal receipt and positive cleanup. The build's actual source checkpoint/manifest labels must agree with its observed identity; the launcher does not guess a future commit or digest kind. The new build may have a later checkpoint label; every worker file must match this packet exactly. The owner must select the bundle's review locator/hash; a self-asserted JSON review string is not authority. Runtime inspection must equal the reviewed image ID and complete labels before credentials are delivered. Historical q1-accepted-evidence.json is only a provenance/template input, never eligible for execution.
- Existing `gpt-6-astra`, Codex0.169.0, **fast unset**. Requested model is configured evidence, never actual model participation. Actual contributors stay unknown; no-reroute-observed is not proof of no rerouting. Stronger Claude requirements are unchanged.
- Credential reference `codex-pushcoin-subscription`, provider `operator-file`, source `/home/sl/.codex-pushcoin/auth.json` (the selected `~/.codex-pushcoin/auth.json`). This is a path reference only during preparation. No source stat/read or authentication probe occurs in --check.
- Host/runtime UID:GID1000:1000. Fresh private root `/var/tmp/baton-codex-q2-386207`, mode0700, umask077, at least4GiB free. Fresh public destination `work/records/2026/11/finding-v12-native-provider-selection/evidence/q2-execution-386207`. Existing roots refuse; no retry/resume into them.
- Frozen candidate manager source is unpacked under `ROOT/source`; the fresh disposable Git fixture is `ROOT/native/fixture`; state stores, command/event exchange, workspaces and private raw logs live only below `ROOT/native`. Provider home uses the production derived `ROOT/native/job-work/<Job identity hash>/<worker identity hash>/home`, with `codex/auth.json` and separate `instructions/WORKER.md`. Exact placement is retained in the private deployment, selection and launch documents. No protected repository mount or Git metadata is used.
- Private source registry is generated once, mode0600. Actual production `UserCredentialSources.resolve_file` and `single_worker._credential` perform automatic first initialization through CredentialHome/HomeMount, enforcing the common1,048,576-byte bound and exact bytes. There is no manual per-Job copy, source writeback or silent re-seed. Failed initialization remains held; this packet never withdraws its receipt or retries it. Retained refreshed credentials remain private after cessation.

## One bounded task through the real native boundary

Create a fresh local qualification Authority (UUID386207aa000000000000000000000001), one Work386207aa-W1, one Jobq2-386207 and one explicitly named implementation worker `qualification.codex` / `q2-codex`. These are qualification-local runtime identities, not impersonations of a v11 participant; W385830 remains the coordination authority. No second production backlog, live v11 session, reviewer, integrator or publisher is started.

`native.py` calls the real Authority, JobStore, ControlStore, single_worker preflight/worker_operations, reconcile/status, source/input/launch/credential owners and OCI adapter. It uses the real command/event file exchange and the unchanged image entrypoint `python3 /opt/baton/codex_entry.py`. No direct host Codex exec and no substitute live worker loop. The launch binds the implementation role, instruction digest, requested model, execution ceilings and actual image observation. No full-Job success/acceptance sweep is performed: this is a capture for independent judgment of artifacts and verification.

The source starts with `message.txt` exactly `before\n`. The prompt requests only `after\n`, no other edit, no commit and no network tools. The deterministic workload verifier is:

```
python3 -I -c "from pathlib import Path; assert Path('message.txt').read_bytes()==b'after\\n'"
```

The authoritative argv is the JSON list in native.py/task.json: its Python literal contains one escaped newline, yielding the six bytes `after` plus LF. The task uses the supported **generic copy** profile over a tiny fresh Git repository. Thus the candidate has private copied Git metadata for the Codex working-directory check; no linked worktree or shared objects. Generic profile semantics are not changed. The preparation provider-seam check proves that the candidate contains `.git` before invoking the seam. Changes to other files, including copied Git metadata, are reported by the full-tree comparison and hold the narrow edit criterion; they are not silently excluded.

After positive container cessation the host additionally compares every candidate file with the original fixture using bounded no-follow reads, requiring exactly the one six-byte change. It executes no candidate-authored code. This check can establish the edit even if an execution fault prevented the worker's verifier from running; that distinction remains explicit in private evidence. Ordinary activity is opaque and needs no success catalogue; structural faults remain holds. A host byte check is never labelled a successful worker verification.

## Proposed execution settings and limits

| Boundary | Proposed setting |
| --- | --- |
| Provider budget | One native implementation attempt and one Codex CLI exec turn; no automatic retry, login probe, second turn or review call |
| Provider turn |180seconds, delivered in Job execution limits |
| Worker verification |15seconds, delivered in the same limits |
| Capture loop |240seconds maximum; one command sequence, replay fence prevents another work invocation |
| Owner process |300seconds, then90seconds cleanup/retention reserve; TERM/HUP/ALRM handled |
| Engine commands |Default30seconds, version/image/preflight15seconds; output cap2MiB combined per command |
| Runtime |2GiB,2CPUs,512pids, UID:GID1000:1000, readonly rootfs, all caps dropped, no-new-privileges; production mount table retained |
| Network |Docker **bridge**, no published port, no host network; ordinary outbound DNS/HTTPS and other bridge egress are permitted by Docker, **no hostname/IP allowlist or egress proxy is claimed** |
| Client configuration |Local Docker socket, private empty DOCKER_CONFIG and HOME, fixed PATH/TMPDIR; inherited GIT_* overrides refuse |
| Inventory reads |4096files,32MiB/file,128MiB per inventory; overflow/symlink/nonregular file holds inventory, never silently truncates it |

“One call” here is one provider invocation/CLI editing turn. A tool-using turn may perform multiple service requests internally; this launcher does not claim an HTTP-request/token quota. The180second ceiling and one invocation are the enforced limits. The existing source choice, model and unset tier are fixed. The remaining dependencies are the new image checkpoint/build/offline review and owner selection of this exact execution packet, including private placement, bridge egress and these bounds—not a request to reselect the account or model.

The script first validates its payload, discovers the engine version, inspects the newly qualified image, composes the fresh source/Job and lets the normal manager initialize credentials and launch once. Only the newly allocated worker can reach its private home. The original source is never mounted into the container. Supported manager cancellation fences the local assignment and orders cessation; exact label-checked cleanup then proves stop/removal. No blanket prune, protected Git mutation or image cleanup is included.

## Retention, projection, cleanup and acceptance

Everything generated by the selected attempt initially remains private: raw provider stdout/stderr, provider.invocation and sidecars, worker streams, command/receipt/state/terminal files, output metadata, instructions/selection, exact engine vectors/inspect/receipt, original fixture/candidate, cancellation, volatile-credential withdrawal, stores and diagnostics. Raw stream capture is the existing production attempt-log mechanism; every sidecar must be checked for failed/partial/overflow/absent capture. Do not infer complete output from a successful CLI exit or a log file's mere existence.

After stop/removal, collect.py writes a bounded private hash/size inventory of the workspace, logs and launch exchange. The manager image receipt is read again and the control store reopened; equality with the pre-removal receipt is recorded. The volatile credential delivery is withdrawn through CredentialHome only after exact positive container absence. The retained Job/worker home and refreshed login remain private and untouched; container removal withdraws runtime access. A failed removal retains the credential slot and hold rather than deleting a possibly live mount. No source writeback occurs in this composition.

Only a fixed public RESULT.json is promoted: packet/source/image identity, configured model, error **type** (no exception prose), terminal/capture/edit/image/cleanup booleans and private-root locator. No raw stdout, candidate content, credentials, command tokens, session files, prompts or unreviewed model text enters ordinary evidence. The script always labels acceptance `held-for-private-evidence-review` and native_job_success:false. Exit0 means a protocol terminal was captured and cleanup completed; it does **not** mean authentication, edit acceptance or model success. A faulted turn may legitimately be a captured terminal.

Independent authorized private-evidence review must establish, before Q2 is considered useful qualification:

1. Exactly one provider invocation, exact gpt-6-astra argv, tier absent, CLI0.169.0 and instruction/context-label evidence for implementation; no contributor inference from configuration.
2. Actual newly qualified launched image bound to that attempt and retained after removal/reopen; complete raw event streams or a precisely named incomplete capture.
3. The requested edit and deterministic verification observations, distinguishing worker verification from the post-cessation host byte comparison; every unexpected changed path disclosed.
4. Framed invocation ending and authenticated service completion if observed, kept separate from substantive correctness. Ordinary new activity types are retained as opaque evidence and are not automatic holds or success. Malformed structural framing, explicit execution faults, missing required configuration/image evidence, mismatch/reroute and incomplete output still hold. The reviewer decides whether artifacts/verification satisfy the task; uncertainty goes to Slawomir, never a guessed verdict.
5. Positive cessation/removal and volatile credential withdrawal, retained private home/session evidence, no retries. Failed criteria return one bounded correction/decision, not another live call.

A later authorized sanitization step can copy minimum exact-build event records into ordinary fixtures, replacing credentials/account/session identifiers and unneeded content with explicit redactions while preserving causal shapes and private source hashes. This preparation neither opens existing private Q1/live homes nor pre-invents those future records. The private root and accepted image remain host-local; no off-host backup or shared-login/refresh qualification is claimed. Existing I2 baseline failures and L1–L6 remain; Q2 does not close Q3/Q4, resume, broad native readiness or stronger Claude requirements.

## Sandbox acceptance and uncertainty disposition

The owner explicitly accepts Codex's own sandbox and approval bypass inside the isolated Docker worker, tool access to the copied login and open bridge egress. The prompt is a task instruction, not the filesystem/egress isolation boundary. The container mount contract protects host files/protected checkout. This ruling is not execution authorization. Source credential writeback is absent; effects of service-side refresh on the original source are unqualified. Retained copied/refreshed login survives cleanup privately.

Native handoff `escalate` can preserve a hold and route to the operator without scheduling a writer. Ordinary checkpoint review accepts only accepted/changes-requested/rejected; absent/uncertain output produces no verdict and stays held, but does not automatically produce an operator escalation. Therefore this Q2 capture explicitly returns to independent review through coordination; if that reviewer is uncertain, it must name the evidence and ask Slawomir. The narrower native ordinary-review escalation gap remains a gate for the composed Codex → Claude review path, not a new successful verdict or parser workaround.

Prior review suggestions N1–N4 remain disclosed: exceptional close/reopen can interrupt final result writing, an already-gone first inspect can abort capture, a lost terminal can consume the full240s, and volatile-withdrawal true can mean nothing remained to withdraw. Such cases cannot establish qualification; inspect private logs and retain holds. No live retry is selected. N5's simulation attribution is corrected here; N6's historical roots remain outside this packet and are not cleaned.
