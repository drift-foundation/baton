# Next selection: readiness checks before the useful documentation Job

Prepared by baton.rvpc under W321608 claim E370157. These are proposed operations, not executed results or an execution grant. Owner E370152 accepted W366962 preparation only. Existing packet: `../finding-v12-useful-template-job-monitor/COMMANDS.md`, binding SHA256 `29375db1f141bb4b64b3be38a9429264590d3a3d2a41dd196461d7c977eaf34f`.

## Recommendation and decision boundary

Select one bounded readiness check: inspect the exact selected local image, resolve the selected local credential through the production resolver without emitting its value, and recheck the selected source/fresh destinations. Do not install, pull, build, clone, start a container or invoke a model in that check. A missing prerequisite is a concrete finding, not authority to repair it. Retain redacted results in this dossier and return for actual deployment/serving selection.

The owner must also choose how to handle automatic correction before serving. Current native start supplies per-invocation3600s provider/900s verification limits but no finite correction-round ceiling. A 400-tick monitor is not a work bound. Recommended decision is to keep serving unselected until the owner either explicitly accepts automatic correction exposure under those limits or selects a concrete cancellation procedure with its own independent evidence. Do not call a voluntary stop of observation a finite-run policy, or transplant a historical supervisor into this packet without validating it.

## Concrete readiness commands, after selection

Run from the selected host. Image metadata only: the exact immutable ID must match. This proves local identity/metadata, not that every recipe claim is present or that runtime authentication works.

```sh
timeout 30s docker image inspect sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2 --format '{{json .Id}} {{json .Os}} {{json .Architecture}} {{json .Config.Entrypoint}} {{json .Config.User}}'
```

Credential readability/resolution through the same bounded local source reader used by single_worker; no provider call. Prints only a fixed success or refusal marker, never the secret, its digest, registry entries or exception payload. A successful local read does not establish remote validity or authentication. This command needs explicit selection because it reads credential material, even though it does not disclose it.

```sh
cd /home/sl/src/baton/v12/python
timeout 15s /home/sl/.local/state/baton-v12-venv/bin/python - <<'CHECK'
import sys
sys.path.insert(0, 'src')
from tools.user_credentials import UserCredentialSources
from baton_v12.worker_manager.credentials import MAX_BEARER
try:
    bearer = UserCredentialSources('/home/sl/.baton/credential-sources.json', max_bearer=MAX_BEARER).resolve('operator-file', 'w202663-development')
    del bearer
except Exception:
    print('credential_resolution_refused; no secret details retained')
    raise SystemExit(2)
print('credential_resolution_ok; remote_authentication_not_tested')
CHECK
```

Source checks are read-only; expected HEAD42bed8bb04a53380e565b1a63fb2bc702677f0d0 and no v12 changes. Actual clone remains part of separately selected installation.

```sh
git -C /home/sl/src/baton rev-parse HEAD
git -C /home/sl/src/baton status --short -- v12
git -C /home/sl/src/baton cat-file -e 42bed8bb04a53380e565b1a63fb2bc702677f0d0^{commit}
```

Immediately before any selected installation, recheck the five fresh paths named by the accepted packet; do not reuse an occupied path or delete it to pass. The read-only baseline in evidence/review-370157/READINESS-BASELINE.json found all five absent and the exact source HEAD with clean v12 status. That observation is not a reservation, write-access test or clone proof. Retained archive and selected inventory pins remain as accepted; a replacement image/source changes this selection and needs an explicit record.

## After readiness, a distinct execution selection

Select exact retained archive, destination and default policy set, the documentation task/template/criteria from the accepted packet, the permitted automatic-correction behavior and retention responsibility. Then selected installation and ordinary manager create/start may follow the accepted packet. Evidence must link minted authority, Job/Work/attempt IDs, actual task delivery to independent roles, monitor observations/limitations, candidate and verdict, human disposition and any cleanup holds. No broad telemetry or general certification campaign is required. No useful result or live interval exists for this new Job yet.

After that result is assessed, prepare two independent coding outcomes. W44342 reassessment did not establish a ready product coding payload: its engine-settlement limitation remains, and the small cancellation fixture correction is only a proposed follow-up. Do not allocate two Jobs merely to fill the sequence or disturb active Work. V11 remains coordination authority; direct-agent development remains the standing default until explicitly changed.
