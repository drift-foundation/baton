# Proposed next managed live correction

Prepared under W236087; not executed or authorized for execution by this implementation turn. Independent implementation review comes first. This is one managed Job using one candidate grant, not another standalone recall canary. The later owner selection must bind the actual built image and deployment manifest; this document does not pretend those presently unbuilt bytes have known digests.

## Provider-specific question

Does the production Claude CLI consume its conversation-specific JSONL, restored by the normal manager after positive original-runtime exclusion, and use independent-review feedback to produce a revised attributable proposal in a fresh worker? Existing deterministic tests establish the controller/custody path. Accepted W177936 evidence establishes isolated recall. Neither establishes this composed behavior with the actual provider and runtime artifact; one managed run answers that remaining question.

## Exact proposed workload and bounds

Select one disposable fixture repository, one Job, one implementation identity and a different review principal. Initial fixture `harness.py` prints `before`; the implementation task is: “Change harness.py to print ready. Change only harness.py. Run python3 harness.py and publish the ordinary proposal.” The independent first review must inspect the actual proposal and return changes-requested with: “Change the output to READY and preserve the trailing newline. Change only harness.py and rerun python3 harness.py.” A final independent review accepts only the actual corrected proposal with output `READY\n`, exact retained candidate bytes and successful verification. Unexpected failure or an additional correction request ends this one-run selection; no automatic retry or third implementer invocation.

Use one candidate context profile `/2`, requested model `opus`, the previously evidenced CLI build and auth mechanism, `/output` cwd and state allowlist `[".claude/projects/-output/{conversation_id}.jsonl"]`. Requested-model binding stays exact. Any supplied model/modelUsage is diagnostic. Profile max_entries 4096 and max_bytes 67108864 remain the existing hard maxima, with a tighter selected positive bound permissible before signing the final manifest. The final manifest must pin these limits, adapter/image/runtime/policy digests, storage pins and authority/Job IDs. Retain receipt `/3` and private bounded terminal outputs for both implementer invocations.

Proposed cap: 180 seconds per provider turn, two implementer invocations and two independent review invocations, 900 seconds overall plus 60 seconds for manager-owned stop/absence cleanup. These are proposed bounds for this managed four-turn workflow, not a reinterpretation of W177936's consumed two-turn/600-second allowance. No automatic production certification, enabling, integration, service replacement or Git history mutation follows. Keep all results and failures under the new run identity.

## Execution path to bind after review

Use the existing `tools.stage_execution:factory` and Job Manager owner APIs. Configure the private context storage through `configure_context_storage`, register the exact candidate profile through `certify_context_profile`, and issue exactly one `authorize_qualification_run` for the selected authority/Job/storage/profile. Submit the one Job once, with implementation and review stages only and the reserved receipt output declaration. The independent review's actual report drives correction; the operator never manufactures a verdict or supplies the implementation state to the reviewer.

The serving surface is the existing command below, from the reviewed v12 Python installation. Paths name proposed NEW run artifacts, not files already installed by this turn. The final owner packet must replace the unbound authority value and pin every file/digest before this becomes a runnable command:

```sh
BATON_V12_STAGE_EXECUTION_CONFIG=/home/sl/baton-runs/managed-correction-236087/deployment.json PYTHONPATH=src:. python3 -m tools.job_manager --store /home/sl/baton-runs/managed-correction-236087/jobs.sqlite3 --authority-uuid AUTHORITY_FROM_REVIEWED_MANIFEST --incarnation managed-correction-236087 serve --control /home/sl/baton-runs/managed-correction-236087/control.sqlite3 --operations tools.stage_execution:factory --interval 1
```

This existing CLI serves until stopped; `--once` is only one sweep, not the full correction. Do not wrap it in a bare timeout and claim runtime cleanup. The separately selected one-shot owner supervisor must stop admission after final review or first failure, obtain positive cleanup for all started runtimes via manager operations, stop serving, and retain the measured outcome. On uncertainty retain the hold and report failure; never start another run automatically.

## Promotion prerequisites and acceptance evidence

1. Independent approval of CANDIDATE.json and candidate.diff. The worker adapter changed, so the old image cannot honestly serve these bytes. Select construction of a refreshed immutable worker artifact and manager installation, then bind their real digests. No artifact build/deployment occurred here.
2. Select and pin the fixture source, nonsecret task/review documents, fresh Work/Job/authority identities, credential reference (never credential content), private storage roots, exact candidate profile and deployment, and a bounded owner supervisor. The CLI has no general terminal-Job one-shot flag or context-grant command; the supervisor must use existing owner APIs rather than fabricate journal records. This final executable packet remains a post-review preparation step, explicitly not live-ready in this handoff.
3. Collect the original and correction attempt/use/invocation IDs, one conversation ID, grant consumption, separate runtime identities and HOME directories; original writer revoked/checkpoint fenced and positive runtime absence before restoration; both immutable generations and actual `/3` receipt digests; review report provenance and exact feedback digest; first and revised retained proposal identities; final independent review of the revised proposal. The first checkpoint remains immutable and the second proposal must differ. Retained terminal bytes must match their receipt measurements; no direct reported model field is required.
4. Demonstrate no repeated invocation under duplicate observation and no extra runtime after the one correction. Retirement and any production certification are separate owner decisions; a successful managed correction is not automatic rollout or a global prerequisite for fresh-attempt development.
