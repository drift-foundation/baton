"""Deterministic direct-carrier ownership and provider-context reproduction.

Real disposable admission/bundle/entry owners; provider is injected at run.
No timed sleep, live provider, Git mutation or direct coordination-store access.
"""
import json
import os
import pathlib
import runpy
import subprocess

prior = runpy.run_path(str(pathlib.Path(__file__).with_name('repro-157052.py')))
assert all(not item['accepted'] for item in prior['observations'])

from tests.tools import test_execution_limits as cases
from baton_v12.job_manager import documents, submit, submission
from tests.job_manager import fixtures
import claude_agent
import integration_contract
import integration_entry


class Configured(cases.TheDirectIntegrationCarriesItsJobsOwnCeiling):
    def _configured_job(self):
        held = json.loads(json.dumps(fixtures.submission()).replace('job-', 'ceiling-job-').replace('sub-1', 'ceiling-sub-1').replace('0000000a-W', '0000000c-W'))
        held['schema'] = documents.SUBMISSION_SCHEMA
        held['jobs'][0]['execution_limits'] = {'provider_turn_seconds': 60, 'verification_command_seconds': 45}
        submit(self.fixture.world.jobs, held)
        return held['jobs'][0]['job_id']


case = Configured('test_the_port_materializes_a_third_version_carrying_the_job')
try:
    case.setUp()
    port, admitted = case._started()
    doc = case._materialized()
    bundle = os.path.join(case.fixture.root, 'bundles', case.attempt)
    taken = integration_contract.read_bundle(bundle)
    evidence = taken['evidence']
    # The workload's own public correlation path validates this same scope.
    import integration_workload
    authority = integration_workload._authorized_scope(taken['envelope']['paths'], evidence)
    print(json.dumps({'carrier_admission': admitted['outcome'],
                      'launch_job_id': doc['job_execution']['job_id'],
                      'bundle_authority_job_id': authority['scope']['job_id'],
                      'requested_provider_seconds': doc['job_execution']['execution_limits']['requested']['provider_turn_seconds']}, indent=2), flush=True)
    captured = []
    def runner(argv, **options):
        captured.append(options['timeout'])
        raise subprocess.TimeoutExpired(argv, options['timeout'])
    agent = claude_agent.ClaudeAgent(run=runner)
    agent._scratch = lambda: '/unused-scratch'
    agent._child_environments = lambda scratch: {'provider': {}}
    agent._revalidated_environment = lambda scratch, env: env
    launch_place = os.path.join(case.fixture.place('worker'), 'launch.json')
    with open(launch_place, 'w') as stream:
        json.dump(doc, stream)
    os.chmod(launch_place, 0o444)
    delivery = case.fixture.delivery()
    rc = integration_entry.main(agent=agent, launch_place=launch_place,
        assignment_root=delivery.assignment_root, result_root=delivery.result_root,
        bundle_root=bundle, target_root=case.fixture.target_place,
        scratch=case.fixture.place('probe-scratch'),
        revision=lambda place: taken['envelope']['eligibility']['expected_target_revision'])
    print(json.dumps({'entry_exit': rc, 'captured_provider_timeouts': captured,
                      'result': case._result()}, indent=2), flush=True)
    unknown = submission.boundary_seconds(case.fixture.world.jobs, 'job-never-admitted', 'host_verification')
    print(json.dumps({'unknown_job_host_seconds': unknown}), flush=True)
finally:
    case.doCleanups()
