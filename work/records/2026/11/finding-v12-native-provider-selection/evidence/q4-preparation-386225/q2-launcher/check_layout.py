"""Deterministic layout and verification-literal checks. No engine, credential or provider.

Runs the frozen worker and manager source unchanged. Proves the guard still
refuses a marker image with no delivered selection, that the supported
composition produces a selection the worker accepts, and what the task's
verification argv accepts and rejects.
"""
import ast,hashlib,json,os,subprocess,sys,tarfile,tempfile,shutil
from pathlib import Path
from unittest import mock
P=Path(__file__).resolve().parent
def literal(path):
    for node in ast.walk(ast.parse(Path(path).read_text())):
        if isinstance(node,ast.Assign) and getattr(node.targets[0],'id',None)=='verification':return ast.literal_eval(node.value)
    raise AssertionError('no verification argv')
def matrix(argv,room):
    answer={}
    for label,body in (('after-newline',b'after\n'),('before-newline',b'before\n'),('after-no-newline',b'after'),('after-backslash-n',b'after\\n')):
        cell=Path(room)/label;cell.mkdir(parents=True);(cell/'message.txt').write_bytes(body)
        answer[label]=subprocess.run(argv,cwd=cell,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15).returncode
    return answer
def main():
    with mock.patch.dict(os.environ,{k:v for k,v in os.environ.items() if not k.startswith('GIT_')},clear=True),tempfile.TemporaryDirectory(prefix='baton-q2-layout-check-386221-',dir='/var/tmp') as temp:
        temp=Path(temp);source=temp/'run/source'
        with tarfile.open(P/'source.tar') as archive:archive.extractall(source,filter='data')
        sys.path[:0]=[str(source/'v12/python/src'),str(source/'v12/worker'),str(source/'v12/python/src/baton_v12'),str(P)]
        import native,claude_agent,codex_agent
        from baton_v12.worker_manager import source_boundary,workspaces
        # 1. Marker identity: frozen source == qualified image record == this build's own composed topology.
        marker=native.marker(temp/'run/native')
        assert marker==source_boundary.image_layout_marker()
        marker_place=source/'v12/worker/verifier-layout-marker.json'
        # 2. The guard, unchanged: marker image + no delivered selection refuses before any provider.
        agent=codex_agent.CodexAgent(run=mock.Mock(side_effect=AssertionError('no process in a layout check')),home=str(temp/'scratch'))
        refusals={}
        with mock.patch.object(codex_agent.CodexAgent,'LAYOUT_MARKER',str(marker_place)),mock.patch.object(codex_agent.CodexAgent,'LAYOUT_DOCUMENT',str(temp/'absent.json')):
            try:agent._layout_preflight();raise AssertionError('guard weakened: missing selection accepted')
            except claude_agent.TaskRefusal as refused:refusals['missing_selection']=str(refused)[:160]
        assert 'no trusted layout selection was delivered' in refusals['missing_selection']
        # 3. The supported composition: the manager's own composer and materializer, this deployment's identity.
        digests=dict(image_digest='sha256:'+'e'*64,profile_digest='sha256:'+'1'*64,policy_digest='sha256:'+'2'*64,adapter_digest='sha256:'+'3'*64)
        from baton_v12.worker_manager import ControlStore
        control=ControlStore.open(str(temp/'control.sqlite3'),incarnation='q2-layout-check',clock=native.now)
        workspaces.configure_workspace_group(control,os.getgid())
        identity=workspaces.identity_for(workspaces.configured_workspace_group(control))
        document=source_boundary.compose_verifier_layout(marker=marker,identity=identity,**digests)
        home=temp/'launch';home.mkdir(mode=0o700)
        delivered=source_boundary.materialize_verifier_layout(str(home),document=document)
        place=delivered.place;control.close()
        with mock.patch.object(codex_agent.CodexAgent,'LAYOUT_MARKER',str(marker_place)),mock.patch.object(codex_agent.CodexAgent,'LAYOUT_DOCUMENT',str(place)):
            selection=agent._selected_layout()
        assert selection==document and selection['roots']==marker['roots'] and (selection['uid'],selection['gid'])==(os.getuid(),os.getgid())
        # 4. A selection from another topology still refuses.
        wrong=temp/'wrong.json';wrong.write_text(json.dumps(dict(document,layout_digest='0'*64)))
        with mock.patch.object(codex_agent.CodexAgent,'LAYOUT_MARKER',str(marker_place)),mock.patch.object(codex_agent.CodexAgent,'LAYOUT_DOCUMENT',str(wrong)):
            try:agent._selected_layout();raise AssertionError('guard weakened: foreign topology accepted')
            except claude_agent.TaskRefusal as refused:refusals['foreign_topology']=str(refused)[:160]
        # 5. A legacy (null) selection is refused by composition for a marker image only at the worker; the composer refuses a missing marker.
        try:source_boundary.compose_verifier_layout(marker=None,identity=identity,**digests);raise AssertionError('composed without a marker')
        except Exception as refused:refusals['compose_without_marker']=type(refused).__name__
        # 6. Verification argv: this packet's, and the 386214 literal for the record.
        argv=literal(P/'native.py');mine=matrix(argv,temp/'v-new')
        assert mine=={'after-newline':0,'before-newline':1,'after-no-newline':1,'after-backslash-n':1},mine
        previous=P.parent/'readiness-final-386214/q2/native.py';before=None
        if previous.is_file():before=dict(argv=literal(previous),exit_status=matrix(literal(previous),temp/'v-old'))
        print(json.dumps(dict(passed=True,marker_sha256=hashlib.sha256(marker_place.read_bytes()).hexdigest(),layout_digest=marker['layout_digest'],guard_refusals=refusals,selection_accepted=True,verification=dict(argv=argv,exit_status=mine),verification_386214=before,engine_calls=0,provider_calls=0,credential_reads=0),indent=1))
if __name__=='__main__':main()
