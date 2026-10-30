# Exact continuation decision — prepared, not selected

W339972 closed satisfying at343920; parent woke343921. Its accepted entry is installed and managed check/inspect passed. Closure explicitly grants no arm/start. Original selection339891 was attempted once and consumed; a further invocation requires the owner decision below. No new packet, preparer script or repeated test campaign is needed.

## Proposed selection

Select one implementation invocation through baton.codx / baton.codxpc using installed selection `w339626-custody-v2`, digest `04cc16db980abb8c10dbbdcf2d3e589f524c768f2ba1982f479615a232f52227`, successor packet `7fa243deaad910fe21baea9bc29be80c0081071088ab5625a4df342acadb4ba5`. Exact candidate340184/review340257 and installed acceptance review343619 remain provenance. Existing authority `5a2f5ddc15f247e68f1cbe93b4de93d3`, Work `5a2f5ddc-W1`, Job `job-baton-standard-next-run-w339626-339782`, run `baton-standard-next-run-w339626-339782` are preserved in private `/var/lib/baton-managed-runs/w339626-custody-v2`; original /tmp instance remains fenced evidence. No new authority, separate submit or bootstrap.

Preserve base bc925cf5c62d69426ed5862af4d41f4d2a967b0f, task339833, image sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2, fresh provider context and bound sources/runtime/helpers. Bounds:900s enforced resource lease,3600s provider ceiling,30s final verifier,4800s total,60s cleanup,one invocation/no retry. No renewal assumption. A failed/unknown start remains held, not permission to repeat.

After that explicit selection, operator alone arms the reviewed digest:

```sh
sudo /usr/bin/python3 -I /root/baton-managed-entry-340184/installer.py arm w339626-custody-v2 04cc16db980abb8c10dbbdcf2d3e589f524c768f2ba1982f479615a232f52227
```

Then route to baton.codx. Under its own claim the mapped managed executor invokes exactly once:

```sh
/usr/bin/sudo -n /opt/baton-managed-entry/entry.py start w339626-custody-v2
```

These are decision-ready commands, not actions performed or selected by this file. Arming does not launch; successful consumption is not product acceptance. On refusal, report it and stop; never clear consumption, bypass the entry or use PREPARED-339833.md's historical /tmp/env command. That older command set is superseded for execution by this installed custody path, while its original evidence remains immutable.

## Result collection and acceptance

Capture managed command stdout/stderr/exit and actual elapsed time; retain final enforcement/manager/workload artifacts, attempt identity and candidate provenance. Private outcome location is `/var/lib/baton-managed-runs/w339626-custody-v2/packet/outcome.json` plus its enforcement/manager siblings. Root-private evidence must remain protected: if managed receipt collection cannot read it, operator supplies nonsecret final-report/candidate evidence copies for independent review, without granting a broad read/exec interface or copying credentials/raw provider logs. Inaccessible is not absent. Missing final reports are incomplete, not success or cessation; retain exact unknowns. No raw store reads.

The implementation outcome remains one reusable next-run path and two input-only demonstrations with unchanged preparer code and honest whole-path <=60s timing to observed substantive work. Include routine input assembly/validation/launch; no per-run scripting or packet engineering. Deterministic providers exercise affected owners and are labelled as simulated. This one-time implementation bootstrap does not satisfy routine-start timing. Full acceptance remains independent and outcome-based as in TASK-339833 and DESIGN OBS-0. No sibling reassignment or extra live verification.

Human checkpoint for accepted boundary remains pending per343920: "Validate managed controller custody and exact sudo admission". Product-delivery checkpoint later: "Add reusable enforced next-run preparation". No commit or candidate import is asserted. Credential provisioning/image inspection do not establish current provider authentication; this review does not read or refresh credentials or select a live authentication probe.
