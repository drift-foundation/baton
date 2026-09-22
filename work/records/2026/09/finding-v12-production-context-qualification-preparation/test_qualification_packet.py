"""Actual serving and review transport with a simulated engine/provider."""
import copy,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
import qualification_packet as packet
from tests.manager import test_claude_context as serving
from baton_v12.contracts import digest
from baton_v12.worker_manager import provider_context as context, attempts, review_cycles
HERE=Path(__file__).parent.resolve()

class CapsulePipeline(serving.ServingContextCase):
    FINDINGS=packet.FEEDBACK
    corrected_ready=serving.RestoredCorrectionBoundary.corrected_ready
    RUN='qualification-transport-fixture'

    def setUp(self):
        super().setUp()
        self.context_profile['qualification']='candidate'
        self.context_digest=digest(self.context_profile)
        self.final_capsule=None
        self.verifier_calls=[]
        patch=mock.patch.object(serving.oci.OciAdapter,'_context_execution',self.real_context_execution)
        patch.start()
        self.addCleanup(patch.stop)

    def serving(self,**members):
        job,control,composed=super().serving(**members)
        context.authorize_qualification_run(control,run_id=self.RUN,profile_digest=self.context_digest,storage_path=str(self.context_root),authority_uuid=self.config['authority_uuid'],job_id='job-a',note='deterministic actual transport')
        return job,control,composed

    def turn(self,control,role,attempt_id,roots,**operands):
        room=Path(self.config['launch_home'])/'logs'/attempt_id
        room.mkdir(parents=True,exist_ok=True)
        with mock.patch.dict(os.environ,{'BATON_ATTEMPT_LOG_ROOM':str(room)}):
            return super().turn(control,role,attempt_id,roots,**operands)

    def provider(self,edits=None,status=0):
        original=super().provider(edits=edits,status=status)
        def run(argv,**options):
            if argv[0]!='claude': return original(argv,**options)
            if '--model' not in argv:
                if self.final_capsule is None: return original(argv,**options)
                reviewed=subprocess.run([sys.executable,str(HERE/'qualification-review-232542.py'),'--capsule',str(self.final_capsule),'--approved-capsule',self.capsule_digest],capture_output=True,timeout=10)
                self.verifier_calls.append(reviewed.returncode)
                if reviewed.returncode: return subprocess.CompletedProcess(argv,reviewed.returncode)
                Path(options['cwd'],'review-report.json').write_bytes(reviewed.stdout)
                return subprocess.CompletedProcess(argv,0)
            script='''import json,os,secrets,sys
from pathlib import Path
argv,edits=json.loads(sys.argv[1])
state=Path(os.environ['HOME'])/'.claude/projects/output/session.json'
previous=json.loads(state.read_text()) if state.exists() else None
assert (previous is not None)==('--resume' in argv)
token=previous['token'] if previous else secrets.token_hex(16)
state.parent.mkdir(parents=True,exist_ok=True)
for parent in (state.parent,state.parent.parent): parent.chmod(0o700)
state.write_text(json.dumps({'session':argv[-2],'token':token,'turn':2 if previous else 1}))
state.chmod(0o600)
for path,text in edits.items(): Path(path).write_text(text)
print(json.dumps({'type':'result','subtype':'success','is_error':False,'session_id':argv[-2],'model':'deterministic-model','result':'RECALL:'+token}))
'''
            return subprocess.run([sys.executable,'-c',script,json.dumps([argv,edits or {}])],**options)
        return run

    def collected(self):
        held,first,reviewer,second=self.corrected_ready()
        roots=self.mounted(held.composed,'implementation',second)
        feedback=serving.RestoredCorrectionBoundary.feedback_file(self,held,second).read_bytes()
        source=self.worker_of(held.composed,'implementation').stage._prepared[second]['boundary']['boundary'].source.place
        captured=packet.capture_inputs(self.task_bytes,feedback,roots['workspace'],inputs=roots['inputs'],source=source)
        self.assertEqual(self.turn(held.control,'implementation',second,roots,edits={'harness.py':"print('second')\n"}),0)
        self.drive(held.job,held.composed,'implementation','completed')
        owner=context.context_use_of(held.control,second)['context_id']
        paths=[Path(self.config['launch_home'])/'logs'/attempt/'provider.stdout.log' for attempt in (held.attempt_id,second)]
        capsule=packet.capsule(held.control,run_id=self.RUN,context_id=owner,provider_paths=paths,second_inputs=captured)
        self.final_capsule=Path(self.root)/'private-review-capsule.json'
        self.capsule_digest=packet.publish(self.final_capsule,capsule)
        self.assertFalse(self.final_capsule.is_relative_to(Path(roots['workspace'])))
        return held,reviewer,capsule

    def final_review(self,held,reviewer):
        self.drive(held.job,held.composed,'review','waiting')
        [last]=[one for one in self.worker_of(held.composed,'review').stage._prepared if one!=reviewer]
        self.turn(held.control,'review',last,self.mounted(held.composed,'review',last))
        return last

    def test_real_guard_capture_verifier_and_committed_review(self):
        held,reviewer,capsule=self.collected()
        last=self.final_review(held,reviewer)
        self.assertEqual(self.verifier_calls,[0])
        self.drive(held.job,held.composed,'review','completed')
        assignment=attempts.assignment_of(held.control,last)
        attachment=review_cycles.review_for_attempt(held.control,attempt_id=last,generation=assignment['generation'])
        verdict_id=review_cycles._id('verdict',{'attachment_id':attachment['attachment_id'],'disposition':'accepted'})
        verdict=review_cycles.verdict_of(held.control,verdict_id)
        frozen=serving.load_manifest(held.control,verdict['review_result']['manifest_digest'],'resultManifest')
        findings=next(one for one in frozen['outputs'] if one['name']=='findings')
        report_digest=next(one['content_digest'] for one in findings['content_manifest']['entries'] if one['path']=='report.json')
        context.retire_context(held.control,capsule['context_id'])
        context.certify_production_profile(held.control,dict(self.context_profile,qualification='production'),{'run_id':self.RUN,'context_id':capsule['context_id'],'continuity':{'verdict_id':verdict_id,'report_digest':report_digest},'evidence_refs':[report_digest]})

    def test_leak_mismatch_and_missing_transport_refuse(self):
        held,reviewer,original=self.collected()
        for member in ('task','feedback','workspace'):
            capsule=copy.deepcopy(original)
            token=json.loads(packet.unblob(capsule['providers'][0]['content']))['result'][7:].encode()
            if member=='workspace': capsule['second_inputs']['trees']['workspace']['files'].append({'path':'leak.txt','content':packet.blob(token)})
            else: capsule['second_inputs'][member]=packet.blob(token)
            raw=packet.encoded(capsule)
            with self.subTest(member=member),self.assertRaisesRegex(packet.Refusal,'leaked'): packet.review(raw,packet.sha(raw))
        for kind in ('filename', 'directory'):
            capsule=copy.deepcopy(original)
            token=json.loads(packet.unblob(capsule['providers'][0]['content']))['result'][7:]
            if kind=='filename': capsule['second_inputs']['trees']['workspace']['files'].append({'path':token,'content':packet.blob(b'')})
            else: capsule['second_inputs']['trees']['workspace']['directories'].append(token)
            raw=packet.encoded(capsule)
            with self.subTest(kind=kind),self.assertRaisesRegex(packet.Refusal,'leaked'): packet.review(raw,packet.sha(raw))
        for mount in ('inputs', 'source'):
            capsule=copy.deepcopy(original)
            capsule['second_inputs']['trees'][mount]['files'].append({'path':'leak.txt','content':packet.blob(token.encode())})
            raw=packet.encoded(capsule)
            with self.subTest(mount=mount),self.assertRaisesRegex(packet.Refusal,'leaked'): packet.review(raw,packet.sha(raw))
        for mount in ('workspace', 'inputs', 'source'):
            capsule=copy.deepcopy(original)
            del capsule['second_inputs']['trees'][mount]
            raw=packet.encoded(capsule)
            with self.subTest(missing=mount),self.assertRaisesRegex(packet.Refusal,'mount coverage'): packet.review(raw,packet.sha(raw))
        for member in ('task','feedback'):
            capsule=copy.deepcopy(original)
            capsule['second_inputs'][member]=packet.blob(b'changed input')
            raw=packet.encoded(capsule)
            with self.subTest(changed=member),self.assertRaises(packet.Refusal): packet.review(raw,packet.sha(raw))
        capsule=copy.deepcopy(original)
        result=json.loads(packet.unblob(capsule['providers'][1]['content']))
        result['result']='RECALL:'+'f'*32
        capsule['providers'][1]['content']=packet.blob(packet.encoded(result))
        raw=packet.encoded(capsule)
        with self.assertRaisesRegex(packet.Refusal,'recall differs'): packet.review(raw,packet.sha(raw))
        with self.assertRaisesRegex(packet.Refusal,'capsule digest'): packet.review(self.final_capsule.read_bytes(),packet.sha(b'wrong'))
        with self.assertRaises(FileExistsError): packet.publish(self.final_capsule,original)
        self.final_capsule=Path(self.root)/'absent.json'
        self.final_review(held,reviewer)
        self.assertEqual(self.verifier_calls,[2])
        self.assertIsNone(held.control.operation_record(context._id('context-certification',digest(dict(self.context_profile,qualification='production')))))

class Boundary(unittest.TestCase):
    def test_capture_keeps_empty_directory_and_file_names(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'empty').mkdir()
            (root/'named').write_bytes(b'')
            captured=packet.capture_inputs(b'task',b'feedback',root,inputs=root,source=root)
            self.assertEqual(captured['trees']['workspace']['directories'],['empty'])
            self.assertEqual([row['path'] for row in captured['trees']['workspace']['files']],['named'])

    def test_nofollow_nonblocking_duplicate_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            os.mkfifo(root/'fifo')
            with self.assertRaises(packet.Refusal): packet.read(root/'fifo')
            (root/'data').write_bytes(b'abc')
            (root/'link').symlink_to(root/'data')
            with self.assertRaises(OSError): packet.read(root/'link')
            with self.assertRaises(packet.Refusal): packet.capture_inputs(b'task',b'feedback',root,inputs=root,source=root)
            with self.assertRaises(packet.Refusal): packet.closed(b'{"x":1,"x":2}')
if __name__=='__main__': unittest.main()
