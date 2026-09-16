"""W183883 follow-up: real functions, inert runtime, substituted repository runner."""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest import mock
D=Path(__file__).resolve().parent
ROOT=D.parents[4]
sys.path[:0]=[str(ROOT/'v12/python'),str(ROOT/'v12/python/src')]
sys.dont_write_bytecode=True
from tools import bootstrap,instance
from tests.tools.test_instance import TheBootstrapPreparesTheRepositories

def main():
    began=time.monotonic()
    scratch=Path(tempfile.mkdtemp(prefix='w183883-review188639-',dir='/tmp'))
    result={'claim':188639,'scratch_retained':str(scratch),'cases':{}}
    author=json.loads((D/'EVIDENCE-188582.json').read_text())
    hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in author['candidates']}
    assert hashes==author['candidates']
    result['candidate_hashes']=hashes
    runtime=scratch/'runtime'
    (runtime/'_internal/rpds').mkdir(parents=True)
    (runtime/'baton-v12-stack').write_text('inert launcher')
    (runtime/'_internal/rpds/rpds.so').write_text('inert native bytes')
    identity={'command':'baton-v12-stack','frozen':True,'python':'3.13.7','platform':'Linux','machine':'x86_64','schema_assets':{'agent-session-1.0':10,'worker-control-1.0':20},'native_rpds':str(runtime/'_internal/rpds/rpds.so')}
    def fixture(label):
        f=TheBootstrapPreparesTheRepositories()
        f.root=scratch/label
        f.destination=str(f.root/'deployment')
        f.places=instance.layout(f.destination)
        f.bootstrap=bootstrap
        f.issued=[]; f.answers={}; f.common={}
        return f
    # Accepted input-only operand is no longer emitted into the actual schema.
    installed=Path('/var/tmp/w183883-standalone-188434/deployment')
    cfg=json.loads((installed/'deployment.json').read_text())
    bootstrap.validated(cfg)
    doc={key:copy.deepcopy(cfg[key]) for key in bootstrap.REQUIRED if key in cfg}
    doc.update(schema=bootstrap.SCHEMA,state_root=str(installed),repository_source='/fixture/source')
    doc['workers']=[{'worker_id':w['worker_id'],'role':w['role'],'participant':w['deployment']['participant'],'deployment':copy.deepcopy(w['deployment'])} for w in cfg['workers']]
    doc['jobs']=[{'job_id':'fixture','work_id':cfg['job_work_id'],'line_declared_base':cfg['line_declared_base'],'canonical_target_id':cfg['canonical_target_id'],'source_worker_id':doc['workers'][0]['worker_id']}]
    principals={w['participant']:w['deployment']['principal'] for w in doc['workers']}
    emitted=bootstrap.configuration(doc,principals)
    assert 'repository_source' not in emitted
    bootstrap.validated(emitted)
    result['cases']['R1_real_validator']={'accepted':True,'repository_source_emitted':False}
    # Existing and racing foreign justfiles remain protected.
    f=fixture('existing'); Path(f.destination).mkdir(parents=True)
    marker=Path(f.places['justfile']); marker.write_text('foreign owner marker')
    try:
        with mock.patch.object(bootstrap,'_identity_of',return_value=identity):
            bootstrap.install(f.destination,str(runtime),{'authority_uuid':'a'*32},stream=io.StringIO())
    except bootstrap.BootstrapRefusal as e: refused=str(e)
    else: raise AssertionError('existing justfile accepted')
    assert marker.read_text()=='foreign owner marker'
    result['cases']['R3_existing_preserved']={'refusal':refused,'unchanged':True}
    f=fixture('race'); original_manifest=instance.manifest
    def appeared(path):
        value=original_manifest(path)
        if str(path)==f.places['distro']:
            Path(f.places['justfile']).write_text('foreign raced marker')
        return value
    try:
        with mock.patch.object(bootstrap,'_identity_of',return_value=identity),mock.patch.object(instance,'manifest',side_effect=appeared):
            bootstrap.install(f.destination,str(runtime),{'authority_uuid':'a'*32},stream=io.StringIO())
    except bootstrap.BootstrapRefusal as e: refused=str(e)
    else: raise AssertionError('racing justfile accepted')
    assert Path(f.places['justfile']).read_text()=='foreign raced marker'
    result['cases']['R3_race_preserved']={'refusal':refused,'unchanged':True}
    # A failed selector write leaves our justfile, removed runtime, and no selector.
    f=fixture('retry')
    with mock.patch.object(bootstrap,'_identity_of',return_value=identity):
        try:
            with mock.patch.object(instance,'create',side_effect=OSError('injected transient selector write failure')):
                bootstrap.install(f.destination,str(runtime),{'authority_uuid':'a'*32},stream=io.StringIO())
        except OSError as e: initial=str(e)
        else: raise AssertionError('injection did not fire')
        try: bootstrap.install(f.destination,str(runtime),{'authority_uuid':'a'*32},stream=io.StringIO())
        except bootstrap.BootstrapRefusal as e: retry=str(e)
        else: raise AssertionError('unexpected successful retry')
    result['cases']['R3_own_leftover_blocks_retry']={'initial_error':initial,'retry_refusal':retry,'justfile_present':Path(f.places['justfile']).exists(),'runtime_present':Path(f.places['distro']).exists(),'selector_present':Path(f.places['instance']).exists()}
    # Corrected structural/path and mapping refusals issue no clone calls.
    for mode in ('missing','traversal','mismatch'):
        f=fixture(mode); given=f.document()
        if mode=='missing':given={'repository_source':'/fixture/source'}
        if mode=='traversal':given['workers'][0]['worker_id']='x/../../../escape'; given['jobs'][0]['source_worker_id']='x/../../../escape'
        if mode=='mismatch':given['integration_target']='/elsewhere/target'
        try:bootstrap.prepare_repositories(given,f.places,runner=f.runner,stream=io.StringIO())
        except bootstrap.BootstrapRefusal as e:refused=str(e)
        else:raise AssertionError(mode)
        assert f.issued==[] and not Path(f.destination).exists()
        result['cases']['fixed_'+mode]={'refusal':refused,'calls':f.issued,'destination_absent':True}
    # Deterministic lock-boundary interleaving: another completed installation
    # exists when this attempt acquires the lock. No actual process is launched.
    f=fixture('custody_after_wait'); actual_lock=bootstrap.serialized
    @contextlib.contextmanager
    def after_wait(places,wait):
        with actual_lock(places,wait) as lock:
            Path(places['distro']).mkdir()
            Path(places['instance']).write_text('foreign selector')
            Path(places['justfile']).write_text('foreign justfile')
            yield lock
    with mock.patch.object(bootstrap,'serialized',after_wait):
        made=bootstrap.prepare_repositories(f.document(),f.places,runner=f.runner,stream=io.StringIO())
    clones=[c for c in f.issued if c[1]=='clone']
    assert len(clones)==5 and Path(f.places['instance']).read_text()=='foreign selector'
    result['cases']['R2_custody_not_rechecked_under_lock']={'clones_after_foreign_install':clones,'returned_prepared':made,'foreign_selector_preserved':True}
    # Explicit repository selections agree, but mutable worker storage is ignored.
    f=fixture('storage'); given=f.document()
    for worker in given['workers']:
        worker['deployment']['workspace_storage']=str(scratch/'shared-worker-storage')
    bound=bootstrap.repositories_bound(bootstrap.workspace_bound(given,f.places),f.places)
    bootstrap.repositories_agree(bound,f.places)
    made=bootstrap.prepare_repositories(bound,f.places,runner=f.runner,stream=io.StringIO())
    configured=bootstrap.configuration(bound)
    storage=[w['deployment']['workspace_storage'] for w in configured['workers']]
    assert all(not Path(p).is_relative_to(f.destination) for p in storage)
    result['cases']['R4_external_storage_accepted']={'prepared_count':len(made['prepared']),'emitted_workspace_storage':storage,'destination':f.destination,'limits':'Configuration mapping and preparation accepted; this wrapper fixture is not a full manager-valid deployment.'}
    # Use the real accepted retained configuration to prove storage is a legal
    # runtime path outside its instance; the current installer does not rebind it.
    result['cases']['R4_real_configuration_storage']={'destination':str(installed),'validated':True,'workspace_storage':[w['deployment']['workspace_storage'] for w in emitted['workers']]}
    result['seconds']=time.monotonic()-began
    result['limits']='No actual Git, Authority open, store read, live stack, provider, engine or Job. Actual installer/validator functions, real ordinary files, inert runtime identity and fake repository subprocess runner. Deterministic lock-boundary injection, not a real concurrent deployment.'
    (D/'REVIEW-EVIDENCE-188639.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'seconds':result['seconds'],'scratch':str(scratch),'cases':list(result['cases'])},indent=2))
if __name__=='__main__':main()
