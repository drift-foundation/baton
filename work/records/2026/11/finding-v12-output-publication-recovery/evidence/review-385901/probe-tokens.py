import sys,os,json,unittest
from pathlib import Path
root=Path.cwd();sys.path[:0]=[str(root),str(root/'src')]
from tests.job_manager import test_publication_recovery_execution as cases
from baton_v12.worker_manager import tokens,attempt_runtime_of
from baton_v12.job_manager import publication_execution,projection

class Tokens(cases.PublicationExecutionCase):
    def token(self):
        place=Path(self.storage)/self.publication_attempt/'workspace';s=place.stat()
        domain=tokens.domain_of('workspace',f'{s.st_dev}:{s.st_ino}')
        held=tokens.outstanding(self.control,domain);self.assertEqual(len(held),1)
        return domain,held[0]['generation']
    def test_success_returns_exact_generation(self):
        self.ready();self.launched();domain,generation=self.token()
        self.assertEqual(self.turn(),0);self.tick(cases.PUBLISHED)
        state=tokens.token_of(self.control,domain,generation)
        print('SUCCESS_TOKEN',json.dumps(state,default=str));self.assertTrue(state['returned'])
    def test_unknown_runtime_keeps_token_and_review_closed(self):
        self.ready();self.launched();domain,generation=self.token()
        self.engine_hook=lambda argv: {'status':125,'stdout':'','stderr':'Cannot connect to the Docker daemon'} if argv[1] in ('ps','inspect') else None
        self.serving()
        for _ in range(3):self.tick(cases.PUBLISHED)
        state=tokens.token_of(self.control,domain,generation)
        read=publication_execution.publication_readiness(self.jobs,'D1')
        print('UNCERTAIN_TOKEN',json.dumps({'token':state,'readiness':read,'runtime':attempt_runtime_of(self.control,self.publication_attempt)},default=str))
        self.assertFalse(state['returned']);self.assertFalse(self.gate()['open']);self.assertEqual(self.review_offers(),[])

if __name__=='__main__':unittest.main(verbosity=2)
