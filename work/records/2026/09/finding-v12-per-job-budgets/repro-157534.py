"""Independent causal retry and post-import timeout observations."""
import json,os,subprocess
from tests.tools import test_execution_limits as tests
from baton_v12.integration import reconciliation

case=tests.TheComposedHostVerificationUsesTheJobsCeiling()
try:
    case.setUp();case._watching(failing=True)
    held=case.case.integrating(result_judgment_workers=case.case.judgment_workers())
    case.case.drive_job(held.job,held.composed,'job-a','integration','completed',ticks=4)
    observed=[]
    for index in range(4):
        before=len(case.seen);report=case.case.tick(held)
        observed.append({'tick':index+1,'host_calls_added':len(case.seen)-before,
            'deferred':[one for one in report['started'] if one['outcome']=='deferred']})
    deployment=case.case.deployment_of(held.composed)
    print(json.dumps({'case':'causal-timeout-retries','ticks':observed,'total_host_calls':len(case.seen),'judges':len(deployment.judges)},indent=2),flush=True)
finally:
    case.doCleanups()

case=tests.TheComposedHostVerificationUsesTheJobsCeiling()
try:
    case.setUp()
    held,deployment,result_id,result=case.case.pending_judgments()
    for execution in deployment.judges.values():
        case.case.judgment_turn(held,execution)
    accepted=list(case.case.shared_task_bytes and json.loads(case.case.shared_task_bytes)['verification'])
    home=os.path.realpath(deployment.integration_root)
    real=subprocess.run;captured=[]
    def failing(argv,**options):
        where=options.get('cwd')
        if list(argv)!=accepted or not where or os.path.commonpath([home,os.path.realpath(where)])!=home:
            return real(argv,**options)
        captured.append({'argv':list(argv),'seconds':options.get('timeout'),'where':where})
        raise subprocess.TimeoutExpired(argv,options.get('timeout'))
    subprocess.run=failing
    case.addCleanup(setattr,subprocess,'run',real)
    target_before=deployment.authority.canonical_target()
    reports=[]
    for index in range(4):
        report=case.case.tick(held)
        reports.append({'tick':index+1,'started':report['started'],'spoken':report['spoken']})
    final=reconciliation.result_of(deployment.integration,result_id)
    print(json.dumps({'case':'post-import-timeout','calls':captured,'reports':reports,
        'result_state':final['state'],'target_unchanged':target_before==deployment.authority.canonical_target(),
        'stage':case.case.states_for(held.job,held.composed,'job-b'),
        'temporary_directories_remaining':[one['where'] for one in captured if os.path.isdir(one['where'])]},indent=2,default=str),flush=True)
finally:
    case.doCleanups()
