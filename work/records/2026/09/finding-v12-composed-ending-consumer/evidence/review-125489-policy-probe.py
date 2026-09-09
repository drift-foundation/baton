"""Same cumulative4s review budget: isolate the stale fixture policy pin."""
import hashlib
import json
import pathlib
import time

from baton_v12.authority import Authority
from baton_v12.job_manager import sweep
from tests.job_manager import fixtures
from tests.tools.test_stage_execution import TheComposedJobTraversesReviewAndAcceptance
from tools import stage_execution

class Case(TheComposedJobTraversesReviewAndAcceptance):
    def composed_document(self, **members):
        # Investigative fixture operand only; production configuration is not edited.
        authority = Authority.open(self.authority_path, expected_authority_uuid=self.config['authority_uuid'])
        try:
            members.setdefault('policy_generation', authority.policy_generation())
        finally:
            authority.dispose()
        return super().composed_document(**members)

started = time.monotonic()
case = Case()
result = {}
try:
    case.setUp()
    held = case.reviewed()
    case.drive(held.job, held.composed, 'integration', 'claimed')
    port = case.integration_port(held)
    document = case.composed_document(line_declared_base=case.base)
    result['investigative_policy_pin'] = document['policy_generation']
    result['configured_instruction_digest'] = document['integration_profile']['instructions_digest']
    result['actual_instruction_digest'] = 'sha256:' + hashlib.sha256(b'the configured integration instructions\n').hexdigest()
    composed = stage_execution.operations_from(document, held.job, held.control, engine_run=case.engine, credential_provider=lambda *_: case.secret, clock=lambda: fixtures.NOW, checkout=case.checkout, integration_port=port)
    case.addCleanup(composed.close)
    report = sweep(held.job, composed, now=fixtures.NOW)
    result['started'] = report['started']
    result['states'] = case.states(held.job, composed)
except Exception as failure:
    result['failure'] = {'type': type(failure).__name__, 'message': str(failure)}
finally:
    case.doCleanups()
result['elapsed_seconds'] = time.monotonic() - started
path = pathlib.Path(__file__).with_suffix('.json')
path.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
