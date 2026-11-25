"""Deterministic matrix for observe.py over synthetic snapshots. No engine, store or provider."""
import copy,hashlib,json,os,sys,tempfile
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import observe
A='attempt-'+'a'*64;B='attempt-'+'b'*64
def main():
    with tempfile.TemporaryDirectory(prefix='baton-q4-observe-check-386227-',dir='/var/tmp') as temp:
        temp=Path(temp);custody=temp/'workspaces'/A/'custody';(custody/A/'proposal').mkdir(parents=True)
        body=b'synthetic custody bytes\n';(custody/A/'proposal/message.txt').write_bytes(body);(custody/A/'logs').write_bytes(body)
        artifact=dict(output_name='proposal',artifact_id=A+':proposal',media_type='application/octet-stream',bytes=len(body),content_digest='sha256:'+hashlib.sha256(body).hexdigest(),locator='file://'+str(custody/A/'proposal'))
        identity=dict(attempt=A,stage_id='job/implementation',work_id='W1',authority_uuid='u'*32,custody_root=custody)
        completed=dict(stage_id='job/implementation',state='completed',attempt_id=A,episode=1,episodes=[dict(episode=1,attempt_id=A)],exchange=None,artifacts=[artifact],runtime=dict(execution_runtime='destroyed',assignment=dict(work_ref=dict(authority_uuid='u'*32,work_id='W1'))))
        frozen=dict(attempt_id=A,result_id='result-'+A,disposition='completed',manifest_digest='sha256:'+'1'*64,artifacts=[dict(output_name='proposal',artifact_id=A+':proposal',bytes=len(body),content_digest=artifact['content_digest'])])
        manifest=dict(outputs=[dict(name='proposal',status='present'),dict(name='logs',status='present')])
        filed=dict(output_name='logs',artifact_id=A+':logs',bytes=len(body),content_digest=artifact['content_digest'],locator='file://'+str(custody/A/'logs'))
        waiting=dict(completed,state='waiting',artifacts=None,exchange=dict(state='waiting',terminal=None),runtime=dict(completed['runtime'],execution_runtime='running'))
        def ask(stage,held=frozen,sealed=manifest,**changes):return observe.observe(stage,lambda one:held,lambda one:sealed,**dict(identity,**changes))
        rows={}
        def expect(name,call,want):
            try:got=call();answer=(None if got[0] is None else got[0]['kind'],got[1])
            except AssertionError as refused:answer=('REFUSED',str(refused)[:80])
            rows[name]=answer;assert answer[0]==want[0] and (want[1] is None or answer[1]==want[1]),(name,answer,want)
        def changed(**members):
            stage=copy.deepcopy(completed);stage.update(members);return stage
        # Still running: keep waiting, even though the custody directory and file already exist.
        expect('waiting-with-custody-directory-present',lambda:ask(waiting),(None,True))
        expect('offered-no-attempt',lambda:ask(dict(state='offered',exchange=None),attempt=None),(None,True))
        # Transient forms.
        expect('exchange-answered-terminal',lambda:ask(dict(waiting,exchange=dict(state='answered',terminal={'ending':'answered'}))),('exchange',False))
        expect('exchange-faulted-terminal',lambda:ask(dict(waiting,exchange=dict(state='faulted',terminal={'ending':'faulted'}))),('exchange',False))
        expect('exchange-answered-without-terminal',lambda:ask(dict(waiting,exchange=dict(state='answered',terminal=None))),(None,True))
        # Durable form: the 386221 snapshot shape.
        expect('completed-custody',lambda:ask(completed),('custody',False))
        expect('completed-and-exchange-terminal',lambda:ask(changed(exchange=dict(state='answered',terminal={'ending':'answered'}))),('exchange',False))
        # Identity disagreements refuse; they are neither waited on nor accepted.
        expect('completed-other-attempt',lambda:ask(changed(attempt_id=B)),('REFUSED',None))
        expect('completed-watching-other-attempt',lambda:ask(completed,attempt=B),('REFUSED',None))
        expect('completed-no-attempt-bound',lambda:ask(completed,attempt=None),('REFUSED',None))
        expect('completed-other-episode-attempt',lambda:ask(changed(episodes=[dict(episode=1,attempt_id=B)])),('REFUSED',None))
        expect('completed-other-work',lambda:ask(completed,work_id='W2'),('REFUSED',None))
        expect('completed-other-stage',lambda:ask(completed,stage_id='job/review'),('REFUSED',None))
        expect('completed-runtime-still-running',lambda:ask(changed(runtime=dict(completed['runtime'],execution_runtime='running'))),('REFUSED',None))
        expect('completed-no-frozen-result',lambda:ask(completed,held=None),('REFUSED',None))
        expect('completed-frozen-other-attempt',lambda:ask(completed,held=dict(frozen,attempt_id=B)),('REFUSED',None))
        expect('completed-frozen-not-completed',lambda:ask(completed,held=dict(frozen,disposition='unable')),('REFUSED',None))
        expect('completed-no-artifacts',lambda:ask(changed(artifacts=[])),('REFUSED',None))
        expect('completed-frozen-digest-differs',lambda:ask(completed,held=dict(frozen,artifacts=[dict(frozen['artifacts'][0],content_digest='sha256:'+'0'*64)])),('REFUSED',None))
        outside=temp/'elsewhere';outside.write_bytes(body)
        expect('completed-artifact-outside-custody',lambda:ask(changed(artifacts=[dict(artifact,locator='file://'+str(outside))])),('REFUSED',None))
        expect('completed-manifest-lacks-proposal',lambda:ask(completed,sealed=dict(outputs=[dict(name='proposal',status='missing-optional')])),('REFUSED',None))
        expect('completed-manifest-unreadable',lambda:ask(completed,sealed=None),('REFUSED',None))
        expect('completed-custody-path-missing',lambda:ask(changed(artifacts=[dict(artifact,locator='file://'+str(custody/A/'gone'))])),('REFUSED',None))
        both=dict(frozen,artifacts=frozen['artifacts']+[dict(output_name='logs',artifact_id=A+':logs',bytes=len(body),content_digest=artifact['content_digest'])])
        expect('completed-with-file-artifact',lambda:ask(changed(artifacts=[artifact,filed]),held=both),('custody',False))
        link=custody/A/'linked';os.symlink(custody/A/'proposal',link)
        expect('completed-artifact-symlink',lambda:ask(changed(artifacts=[dict(artifact,locator='file://'+str(link))])),('REFUSED',None))
        (custody/A/'logs').write_bytes(b'tampered custody bytes!\n')
        expect('completed-file-artifact-bytes-differ',lambda:ask(changed(artifacts=[artifact,filed]),held=both),('REFUSED',None))
        # Ended without a result: stop waiting, no observation.
        for state in observe.ENDED_WITHOUT_RESULT:expect('ended-'+state,lambda state=state:ask(dict(waiting,state=state,exchange=None)),(None,False))
        print(json.dumps(dict(passed=True,cases=len(rows),rows=rows,engine_calls=0,provider_calls=0,credential_reads=0),indent=1))
if __name__=='__main__':main()
