"""Run the real offline and live phases against fake_engine.py. Simulation only.

Docker is substituted at subprocess.Popen; Git really runs, only inside the temporary root.
The two login paths are replaced by synthetic files, and an audit hook fails the check if
either real login path, or the user's ordinary credential registry, is ever opened.
"""
import hashlib,importlib.util,json,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from unittest import mock
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('q4owner',P/'owner-run.py');owner=importlib.util.module_from_spec(spec);spec.loader.exec_module(owner)
OFFLINE=('offline-pass','build-fail','wrong-version','image-drift')
LIVE=('accepted','uncertain','wrong-contributor','no-report','no-edit','launch-fail','stall','oversize-claude-login')
FORBIDDEN=(owner.CODEX_LOGIN,owner.CLAUDE_LOGIN,'/home/sl/.baton/credential-sources.json')
def main():
    scenario=sys.argv[1]
    assert scenario in OFFLINE+LIVE,scenario
    temporary=Path(tempfile.mkdtemp(prefix='baton-q4-prep-'+scenario+'-',dir='/var/tmp'))
    owner.ROOT=temporary/'run';owner.DEST=temporary/'public'
    touched=[]
    def audit(event,args):
        if event=='open' and args and isinstance(args[0],(str,bytes,os.PathLike)) and os.fsdecode(args[0]) in FORBIDDEN:touched.append(os.fsdecode(args[0]))
    sys.addaudithook(audit)
    for name in ('CODEX_LOGIN','CLAUDE_LOGIN'):
        place=temporary/('synthetic-'+name.lower());place.write_bytes(b'{"synthetic_q4_only":true}\n');place.chmod(0o600);setattr(owner,name,str(place))
    state=temporary/'fake-state.json'
    def stage(word):
        held=json.loads(state.read_text()) if state.exists() else dict(codex_labels={'org.opencontainers.image.revision':owner.BASE})
        held['scenario']=word;state.write_text(json.dumps(held))
    real=subprocess.Popen;calls=[]
    def popen(argv,*args,**kw):
        calls.append(list(argv))
        if argv[0]=='docker':return real([sys.executable,'-B',str(P/'fake_engine.py'),str(state),str(P),str(owner.ROOT),*argv[1:]],*args,**kw)
        assert argv[0]=='git',argv
        return real(argv,*args,**kw)
    packet=hashlib.sha256((P/'payload.json').read_bytes()).hexdigest()
    owner.CODEX_IMAGE='sha256:'+'e'*64
    clean={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    with mock.patch.dict(os.environ,clean,clear=True),mock.patch('subprocess.Popen',side_effect=popen):
        stage(scenario if scenario in OFFLINE else 'accepted')
        code=owner.offline('SIMULATION-ONLY',packet)
        first=json.loads((owner.ROOT/'OFFLINE-RESULT.json').read_text())
        assert first['provider_calls']==0 and first['credential_reads']==0 and first['ceased'] and first['removed'],first
        assert json.loads((owner.DEST/'OFFLINE-RESULT.json').read_text())==first
        engine=json.loads(state.read_text())
        assert not engine['containers'] and not any(a[0] in ('create','start') for a in engine['log']),'the offline phase started a worker container'
        answer=dict(scenario=scenario,offline_exit=code,offline=dict(passed=first['passed'],error_type=first['error_type'],builds=first['builds'],inventory_runs=first['inventory_runs']))
        if scenario in OFFLINE:
            if scenario=='offline-pass':
                registry=json.loads((owner.ROOT/'credential-sources.json').read_text())
                assert sorted(one['reference'] for one in registry['sources'])==['claude-primary-subscription','codex-pushcoin-subscription'] and oct((owner.ROOT/'credential-sources.json').stat().st_mode&0o777)=='0o600'
                assert code==0 and first['passed'] and first['cli_version'].startswith('2.1.247') and first['image_files_equal_source'] and first['workers']==['impl-codex','review-claude'] and first['routing']==owner.ROUTING,first
                assert first['review_selection']['requested_model']=='claude-fable-5[1m]' and first['review_selection']['reported_identity']=='claude-fable-5'
            else:
                assert code==1 and not first['passed'] and first['error_type'],first
                assert not (owner.ROOT/'instance/deployment.json').exists(),'an instance was configured after a failed image gate'
        else:
            assert code==0 and first['passed'],first
            stage(scenario)
            if scenario=='stall':owner.LIVE_SECONDS=42
            if scenario=='oversize-claude-login':Path(owner.CLAUDE_LOGIN).write_bytes(b'x'*4097)
            started=time.monotonic()
            code=owner.live('SIMULATION-ONLY',packet,hashlib.sha256((owner.ROOT/'OFFLINE-RESULT.json').read_bytes()).hexdigest())
            elapsed=time.monotonic()-started
            verdict=json.loads((owner.ROOT/'RESULT.json').read_text());engine=json.loads(state.read_text())
            assert json.loads((owner.DEST/'RESULT.json').read_text())==verdict
            assert verdict['acceptance']=='held-for-private-evidence-review' and verdict['native_job_success'] is False
            assert verdict['ceased'] and verdict['removed'] and not engine['containers'],('containers remain',verdict,list(engine['containers']))
            assert verdict['worker_containers']<=2 and sum(1 for a in engine['log'] if a[0]=='build')==1
            answer.update(live_exit=code,elapsed_seconds=round(elapsed,1),live={k:verdict[k] for k in ('outcome','error_type','implementation_state','review_state','review_verdict_recorded','owner_items','owner_item_destinations','codex_configured_model_accepted','claude_attribution_matched','worker_containers','edit_verified','changed_paths','volatile_credentials_withdrawn','implementation_completion','review_completion')})
            if scenario=='accepted':
                assert code==0 and verdict['outcome']=='review-verdict-recorded' and verdict['review_verdict_recorded']=='accepted' and verdict['owner_items']==0,verdict
                assert verdict['edit_verified'] and verdict['changed_paths']==['message.txt'] and verdict['claude_attribution_matched'] and verdict['codex_configured_model_accepted'] and verdict['worker_containers']==2
                assert verdict['implementation_completion']=='custody' and verdict['review_completion']=='custody' and verdict['volatile_credentials_withdrawn'] is True
                seam=json.loads(next((owner.ROOT/'simulated').glob('review-*/provider-seam.json')).read_text())
                assert seam['candidate_seen']=='after\n' and seam['argv'][seam['argv'].index('--model')+1]=='claude-fable-5[1m]' and '/run/baton/credentials/claude' in seam['mount_targets']
                answer['review_seam']=dict(candidate_seen=seam['candidate_seen'],mount_targets=seam['mount_targets'],layout_preflights=seam['layout']['preflights_before_provider'])
            elif scenario=='uncertain':
                assert code==0 and verdict['outcome']=='review-uncertain-owner-item' and verdict['review_verdict_recorded'] is None and verdict['owner_items']==1 and verdict['owner_item_destinations']==['baton.slaw'],verdict
                assert verdict['review_state']!='completed' and verdict['worker_containers']==2
            elif scenario in ('wrong-contributor','no-report'):
                assert verdict['review_verdict_recorded'] is None and verdict['owner_items']==0 and verdict['review_state']!='completed' and verdict['outcome']!='review-verdict-recorded',verdict
                assert verdict['worker_containers']==2
            elif scenario=='no-edit':
                assert not verdict['edit_verified'],verdict
            elif scenario=='launch-fail':
                assert code==1 and verdict['review_verdict_recorded'] is None and verdict['outcome']!='review-verdict-recorded',verdict
            elif scenario=='oversize-claude-login':
                assert code==1 and verdict['outcome']=='error' and verdict['worker_containers']==0 and verdict['implementation_state'] is None,verdict
            elif scenario=='stall':
                assert code==1 and verdict['outcome']=='wall-bound' and verdict['review_verdict_recorded'] is None and elapsed<owner.LIVE_SECONDS+owner.CLEANUP_SECONDS,verdict
    assert not touched,('a real credential path was opened',touched)
    answer.update(commands=len(calls),real_engine_calls=0,real_credential_reads=0,forbidden_paths_opened=touched)
    if '--evidence' in sys.argv:
        retained=Path(sys.argv[sys.argv.index('--evidence')+1]);assert not retained.exists();retained.mkdir(parents=True)
        for name in ('OFFLINE-RESULT.json','RESULT.json','private-error.json','containers.json','cleanup-all.json','live/private-error.json','live/conclusions.json','live/owner-items.json','live/completion.json','live/cleanup-all.json','live/containers.json'):
            if (owner.ROOT/name).is_file():shutil.copyfile(owner.ROOT/name,retained/name.replace('/','-'))
        for seam in (owner.ROOT/'simulated').glob('*/provider-seam.json') if (owner.ROOT/'simulated').is_dir() else []:shutil.copyfile(seam,retained/('seam-'+seam.parent.name.split('-')[0]+'.json'))
        (retained/'engine-operations.json').write_text(json.dumps([a[:2] if a[0] in ('ps','inspect','image') else a[:1] for a in json.loads(state.read_text())['log']]))
    print(json.dumps(answer))
    for here,dirs,files in os.walk(temporary):os.chmod(here,0o700)
    shutil.rmtree(temporary);assert not temporary.exists()
    print(json.dumps(dict(assertions_passed=True,temporary_root_removed=True)))
if __name__=='__main__':main()
