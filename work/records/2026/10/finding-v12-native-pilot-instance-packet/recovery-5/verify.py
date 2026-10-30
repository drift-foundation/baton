"""Deterministic shared-control startup/recovery and guarded-byte application proof."""
import copy
import json
import os
from pathlib import Path
import tempfile
import time

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import JobStore, submit
from baton_v12.worker_manager import ControlStore, outstanding_offers, recover_on_restart
from baton_v12.worker_manager.workspaces import configured_workspace_storage, hold_manager_instance
from tools import single_worker
import recover_packet as repair

NOW = '2026-10-19T04:35:00.000Z'
UUID = '0000000000000000000000000000000a'
checks = []

def check(label, value):
    assert value, label
    checks.append(label)


def no_engine(*args, **kwargs):
    raise AssertionError('No engine operation is permitted by this proof')


def encoded(value):
    return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode()

started=time.monotonic()
packet=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='w325959-recovery-5-') as directory:
    root=Path(directory)/'instance';root.mkdir()
    fixture=Path(directory)/'packet';(fixture/'after').mkdir(parents=True)
    data=(packet/'before/deployment.json').read_text().replace(str(repair.DEST),str(root))
    deployment=json.loads(data)
    workers=[w['deployment'] for w in deployment['workers']]
    for worker in workers:
        for member in ('workspace_storage','credential_home','launch_home','nominated_source'):
            Path(worker[member]).mkdir(parents=True,exist_ok=True)
    (root/'db').mkdir()
    selector={'authority_uuid':UUID,'control_store':str(root/'db/control.sqlite3'),'job_store':str(root/'db/jobs.sqlite3')}
    (root/'instance.json').write_bytes(encoded(selector))
    submission=json.loads((repair.DEST/'generated/submission.json').read_text())
    with JobStore.open(selector['job_store'],authority_uuid=UUID,incarnation='fixture-submit',clock=lambda:NOW) as jobs:
        submit(jobs,submission)
    with ControlStore.open(selector['control_store'],incarnation='fixture-before-restart',clock=lambda:NOW) as control:
        provider=object()
        single_worker.worker_preflight(workers[0],control,credential_provider=provider,engine_run=no_engine)
        committed=configured_workspace_storage(control).place
        before=repair.read_state(root)
        try:
            single_worker.worker_preflight(workers[1],control,credential_provider=provider,engine_run=no_engine)
        except ContractRefusal as refusal:
            check('distinct role roots refuse at the actual worker_preflight boundary', 'already configured with workspace store' in str(refusal))
        else:
            raise AssertionError('distinct root accepted')
        check('failed preflight preserves committed root',configured_workspace_storage(control).place==committed)
        check('failed preflight preserves both admitted episodes and Job state',repair.read_state(root)==before)
        guards=[hold_manager_instance(control,w['workspace_storage']) for w in workers]
        for guard in guards: guard.release()
    # A fresh manager handle recovers the same stores and the same episode IDs.
    corrected=copy.deepcopy(workers)
    for worker in corrected: worker['workspace_storage']=committed
    with ControlStore.open(selector['control_store'],incarnation='fixture-after-restart',clock=lambda:NOW) as control:
        for worker in corrected:
            check('shared-root worker preflight passes '+worker['launch_role'],single_worker.worker_preflight(worker,control,credential_provider=provider,engine_run=no_engine) is provider)
        check('role launch homes remain separate',corrected[0]['launch_home']!=corrected[1]['launch_home'])
        check('role credential homes remain separate',corrected[0]['credential_home']!=corrected[1]['credential_home'])
        check('no live offers reached before refusal',outstanding_offers(control)==[])
        recovery=recover_on_restart(control,now=NOW)
        check('public recovery neither abandons nor repeats an unissued episode',not recovery['abandoned'] and not recovery['recoverable'])
        check('restart preflight and public recovery preserve original episodes',repair.read_state(root)==before)
        hold_manager_instance(control,committed).release()
    # Exact guarded application exercised against a disposable representation,
    # with real public readbacks (no mocked state/store access).
    pin={'destination':str(root),'state':before,'guard_roots':sorted({w['workspace_storage'] for w in workers}),'changes':{},'preserved_files':{},'stores':{}}
    for name,record in json.loads((packet/'CHANGE.json').read_text())['changes'].items():
        old=(packet/'before'/name).read_text().replace(str(repair.DEST),str(root)).encode()
        new=(packet/'after'/name).read_text().replace(str(repair.DEST),str(root)).encode()
        target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(old)
        out=fixture/'after'/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(new)
        pin['changes'][name]={'before':repair.sha(old),'after':repair.sha(new),'mode':target.stat().st_mode&0o777}
    # Selector is immutable and stores cannot be replaced under the packet.
    pin['preserved_files']['instance.json']={'sha256':repair.sha((root/'instance.json').read_bytes()),'mode':(root/'instance.json').stat().st_mode&0o777}
    for name in ('job_store','control_store'):
        path=Path(selector[name]);st=path.stat();pin['stores'][name]={'path':str(path),'device':st.st_dev,'inode':st.st_ino}
    (fixture/'CHANGE.json').write_bytes(encoded(pin))
    # A stale pinned episode must refuse, even with matching candidate bytes.
    stale=copy.deepcopy(pin)
    stale['state']['jobs'][0]['stages'][0]['episode']=2
    (fixture/'CHANGE.json').write_bytes(encoded(stale))
    try: repair.execute(root,fixture,'apply')
    except RuntimeError as failure: check('retained episode drift refuses before replacement','state changed' in str(failure))
    else: raise AssertionError('episode drift accepted')
    (fixture/'CHANGE.json').write_bytes(encoded(pin))
    candidate=fixture/'after/deployment.json';saved=candidate.read_bytes();candidate.write_bytes(saved+b' ')
    try: repair.execute(root,fixture,'apply')
    except RuntimeError as failure: check('candidate tampering refuses before replacement','candidate digest mismatch' in str(failure))
    else: raise AssertionError('candidate tampering accepted')
    candidate.write_bytes(saved)
    chosen=root/'deployment.json';old=chosen.read_bytes();chosen.write_bytes(old+b' ')
    try: repair.execute(root,fixture,'apply')
    except RuntimeError as failure: check('byte drift refuses before replacements','byte drift' in str(failure))
    else: raise AssertionError('drift accepted')
    check('other configuration unchanged on refusal',repair.sha((root/'inputs.json').read_bytes())==pin['changes']['inputs.json']['before'])
    chosen.write_bytes(old)
    answer=repair.execute(root,fixture,'apply')
    check('guarded four-file application succeeds',answer['state_preserved'])
    check('application is replayable without changed stores',repair.execute(root,fixture,'apply')['state_preserved'])
    check('separate guarded recovery succeeds without submission or startup',repair.execute(root,fixture,'recover')['state_preserved'])
    check('same two original episodes retained through application and recovery',repair.read_state(root)==before)
    for name,item in pin['changes'].items():
        check('exact reviewed bytes imported '+name,repair.sha((root/name).read_bytes())==item['after'])
answer={'label':'DISPOSABLE deterministic fixture; no live deployment mutation or engine/provider','checks':checks,'count':len(checks),'recovery':recovery,'seconds':time.monotonic()-started}
(packet/'evidence/VERIFICATION.json').write_bytes(encoded(answer))
print(json.dumps({'checks':len(checks),'seconds':answer['seconds']}))
