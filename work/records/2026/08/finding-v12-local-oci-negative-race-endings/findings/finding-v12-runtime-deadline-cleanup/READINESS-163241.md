# W32577 readiness facts — claim163241

As of 2026-09-13T19:55:15Z. This completes the bounded read-only readiness assignment from
review-2026-09-13T19-48-10Z.md/pass163238. The engine gate is **not ready to run**.
The accepted candidate remains candidate-163184.json, SHA256
e006a1e264463454be3aedb3355905dea7d5ceff09b139170f2d49f286c09a10. All nine candidate and four protected hashes
still match; no product/test/DEPLOYMENT edits or tests ran during this claim.
PROGRESS.md remains the previous implementation account; this readiness work is
recorded here and in FINDING/PLAN. ENGINE-READINESS-162766.md is carried forward.

## Observed readiness facts

| Prerequisite | Evidence and status |
| --- | --- |
| Pinned interpreter | /usr/bin/python3 reports Python3.13.7 and jsonschema4.19.2 at /usr/lib/python3/dist-packages/jsonschema-4.19.2.dist-info (readiness-163241-21.log). Required4.26.0 is not satisfied. |
| Repository interpreter | /home/sl/src/baton/.venv/bin/python3 reports PackageNotFoundError for jsonschema (log22). .venv/pyvenv.cfg names /usr/bin/python3.13, version3.13.7, system packages disabled. |
| Other local environment metadata | environment-metadata-163241.json records discovered metadata from repository .venv, PEX venv cache, user Python library and system/local Python library roots. No installed4.26.0 found in that search. This is a bounded search, not a complete-machine absence proof. |
| Docker client/daemon | log20 reports client29.1.3/API1.52 and Server=null, then permission denied connecting to unix:///var/run/docker.sock. Daemon version/reachability and existing image metadata remain unavailable from this execution boundary. |
| Exact preloaded worker image | Not established. No image was inspected, selected, built, pulled, tagged or removed. No container was created. |
| DEPLOYMENT ownership | W161230 writer explicitly retains it in M163260. Current b6bfb940fe9186629b1c083608b26d8195ccf58abe0854deac59d1d87cb5b2e0 still matches. M163265 selects fresh-hash handback after both pending corrections. |

socket-metadata-163241.json records process/socket ownership and access metadata.
os.access reports read/write true, despite the actual API connection refusal;
permission-bit inspection therefore does not establish usable Docker access.
No alternate socket, privileged escalation or runtime workaround was attempted.
The broad initial file search hit unrelated private /tmp directories; exact
operational limitation is recorded in FINDING. All required dossier files read.

M163260 independently confirms the system/venv dependency mismatch and reports
/home/sl/src/baton/.venv/bin/pip exists and reports25.1.1. This corrects the older
inference from no pip on PATH: package installation may be mechanically possible,
but no install is included in this assignment. The same writer reports a broader
metadata survey found only4.19.2. That broader survey is attributed evidence,
not a probe executed or charged by this claim.

## Retained image provenance: leads, not a selected image

v12/testing/live_ab/live-images.json records historical integration image
sha256:d739fefe6bf885db8ad79122611316f3fbe8b393fa4c821933388e8cd15e2533,
provider sha256:2e222e4cf33ff7f52b2048ae1a9c0a2139707e36943328fdd8674b84937f2b13,
and base sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4.
Its selected-images locator is readable:
baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-152826/selected-images.json.
That file lists the integration/provider identities; it is not a current daemon
inspection or proof of the required reference-worker entrypoint.

historical-image-source-check-163241.json compares all ten recorded worker source
hashes. Seven match, but baton_worker.py, claude_agent.py and
integration_workload.py differ. The historical worker hash da34aa2c1dff8b9f25d748db79fc078c6082de9a13e5908c2cf247b99753a923
is now85b48a2461e259f345ea9f984db4f2c522f83be943b40837882ce5c8241278dd.
Do not substitute those historical images for the gate without explicit
source/provenance assessment. The Dockerfile Python base pin remains
sha256:8fef26df932191825664e4957ff488c96dfe64918327634a357a55facbc994d3;
it identifies the recipe base, not the resulting worker image.

M163260 reports visible image tags baton-w71879-integration:candidate-149053 and
candidate-141676, analogous provider tags, and baton-w85497-dogfood:candidate
through candidate4. The writer explicitly did not inspect or certify them.
These are operator lookup leads only. This tuner cannot establish their immutable
IDs, entrypoints, current availability or source correspondence through the
observed denied Docker boundary.

## Concrete next gate packet and unresolved execution facts

The source-reviewed selector remains:

```text
tests.manager.test_runtime_deadline_engine.DeadlineDocker.test_reached_fence_exact_removal_providers_custody_and_discharge
```

readiness-bindings-163241.json binds the selector, inherited fixture, dependency
pin, Dockerfile, worker, worker schema and current DEPLOYMENT bytes. Run only after
a later assignment supplies an existing usable absolute interpreter satisfying
jsonschema4.26.0, a reachable Docker execution boundary, and an independently
assessed preloaded worker immutable image ID whose entrypoint is exactly
["python3", "/opt/baton/baton_worker.py"]. Set PYTHONPATH=src and
BATON_W32577_IMAGE_DIGEST to that selected ID from v12/python; use the chosen
interpreter with -W error -m unittest and the exact selector above. Those two
operand values are intentionally unresolved; this is not a runnable authorization.

The real-engine question remains exact running-container removal after fencing,
both real delivery-provider endings, retained custody/output and sibling
preservation, followed by distinct local lane release and Authority gate discharge.
Authority and agent are deterministic boundary fixtures; no live model is needed.

Accounting source revalidation: setUpClass sets one monotonic180s deadline;
each Docker child uses min(30s, remaining). The override avoids inherited image
build/pull setup. Container names are registered before creation and remove_everything
is registered after inherited setup, so its first cleanup occurs before directory
removal/store cleanup. Runtime and sibling removals and absence checks share the
same180s deadline. There is **no separate cleanup reserve**: an exhausted deadline
or outer process termination can prevent cleanup calls. Before execution, the
reviewer must select an outer guard/resource-cleanup strategy that reserves cleanup
within the proposed180s total and retains exact owned names after interruption;
this claim does not change that fixture or activate a new execution bank. Any
needed fixture/harness change must be explicitly selected and reviewed before use.

## Documentation coordination and accounting

Canonical W161230 detail at163246: queued to baton.decide, handler null, pending
owner obligation163010. Asynchronous requestM163249 was answered by retained
writer baton.claude in M163260. Exact release gates: correct managed-storage
semantics under review19:07:44, and resolve/apply SCOPE-AMENDMENT-162980 about
result.managed queue readers (which changes the documented limitation). M163265
selects option(b): writer completes those edits, then explicitly hands back the
file with a fresh hash. Retain DEPLOYMENT-DEADLINE-DRAFT-162766.md until then.
No release is inferred from the Work being unclaimed or routed to the approver.

readiness-probe-163241.py persisted expected2s + margin1s before each of three
children, each timeout at most10s and fitting both readiness20s and author120s.
Logs20-22 and verification-162766.json retain successes and failures. Readiness
actual **0.09727905600448139/20s**, author cumulative **66.90845661198546/120s**, remaining
**53.09154338801454s**, all22 children retained. This20s ceiling is charged within120s,
not a separate bank or reset. Reviewer remains4.757895970993559/60s, remaining
55.24210402900644s (review-ledger-163219.json). No test/runtime/image/install/model
execution occurred; the three probes were version/metadata reads only.

Return to baton.feat with these facts. Required pinned-dependency verification,
real-engine acceptance and final documentation remain due. W32577/W32382/W33755
remain open; missing readiness is not a reason to rerun accepted source tests.
