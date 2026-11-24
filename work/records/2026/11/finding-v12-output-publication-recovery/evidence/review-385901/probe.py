import sys,os,json,unittest
from pathlib import Path
from unittest.mock import patch
root=Path.cwd();sys.path[:0]=[str(root),str(root/'src')]
from tests.job_manager import test_publication_recovery_execution as cases
from baton_v12.worker_manager import attempt_runtime_of

class Cuts(cases.PublicationExecutionCase):
    def test_release_cleanup_cut(self):
        self.ready();self.launched();self.assertEqual(self.turn(),0)
        with patch('baton_v12.worker_manager.authorize_cleanup',side_effect=KeyboardInterrupt('after release')):
            with self.assertRaises(KeyboardInterrupt):self.tick(cases.PUBLISHED)
        self.assertIsNone(self.authority.assignment_of(cases.WORK_A))
        self.restarted()
        reports=[self.tick(cases.PUBLISHED) for _ in range(3)]
        state=attempt_runtime_of(self.control,self.publication_attempt)
        print('CLEANUP_CUT',json.dumps({'runtime':state,'spoken':[r['spoken'] for r in reports]},default=str))
        self.assertIn(state['cleanup'],('complete','retained'))

    def test_supervisor_completion_at_expiry(self):
        import publication_entry
        from types import SimpleNamespace
        child=SimpleNamespace(pid=99999999,returncode=0,poll=lambda:0)
        clock=iter([0.0,2.0])
        with patch.object(publication_entry.subprocess,'Popen',return_value=child),patch.object(publication_entry,'_excluded',return_value=True):
            result=publication_entry.supervised(['ignored'],'1970-01-01T00:00:01Z',clock=lambda:next(clock))
        print('DEADLINE_CUT',json.dumps(result))
        self.assertTrue(result['timed_out'])

if __name__=='__main__':unittest.main(verbosity=2)
