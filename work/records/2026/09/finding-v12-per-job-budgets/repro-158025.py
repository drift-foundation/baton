"""Measure both configured host failure boundaries and their original scratch."""
import json,os,subprocess,tempfile
from unittest.mock import patch
from tests.tools import test_execution_limits as tests
from tools import stage_execution
from baton_v12.integration import reconciliation

results=[]
for phase in ('causal','post-import'):
    for failure in ('timeout','start-failure'):
        case=tests.TheComposedHostVerificationUsesTheJobsCeiling()
        try:
            case.setUp()
            if phase=='post-import':
                held,deployment,result_id,result=case.case.pending_judgments()
                for execution in deployment.judges.values():
                    case.case.judgment_turn(held,execution)
                argv=json.loads(case.case.shared_task_bytes)['verification']
            else:
                # This setup helper composes a serving instance, so use it only
                # BEFORE starting the actual traversal, never after judgments.
                argv=case.required_argv()
                deployment=case.case.deployment_of(case.case._composed)
            home=os.path.realpath(deployment.integration_root)
            calls=[];scratch=[];owners=[];reports=[]
            real=subprocess.run;making=tempfile.mkdtemp;running=stage_execution._ConfiguredExecution._run
            def execute(words,**options):
                cwd=options.get('cwd')
                if list(words)!=list(argv) or not cwd or os.path.commonpath([home,os.path.realpath(cwd)])!=home:
                    return real(words,**options)
                calls.append({'argv':list(words),'seconds':options.get('timeout'),'cwd':cwd})
                if failure=='timeout': raise subprocess.TimeoutExpired(words,options.get('timeout'))
                raise FileNotFoundError('deterministic missing host executable')
            def creating(*args,**kwargs):
                where=making(*args,**kwargs)
                if kwargs.get('dir') and os.path.realpath(kwargs['dir'])==home:
                    scratch.append(where)
                return where
            def owned(owner,*args,**kwargs):
                owners.append({'owner':type(owner).__name__,'scope':owner._scope})
                return running(owner,*args,**kwargs)
            with patch.object(subprocess,'run',execute),patch.object(tempfile,'mkdtemp',creating),patch.object(stage_execution._ConfiguredExecution,'_run',owned):
                if phase=='causal':
                    held=case.case.integrating(result_judgment_workers=case.case.judgment_workers())
                    case.case.drive_job(held.job,held.composed,'job-a','integration','completed',ticks=4)
                    deployment=case.case.deployment_of(held.composed)
                before=deployment.authority.canonical_target()
                for _ in range(4):
                    report=case.case.tick(held)
                    reports.append({'started':report['started'],'spoken':report['spoken']})
                after=deployment.authority.canonical_target()
            assert len(calls)==1 and calls[0]['seconds']==77,calls
            assert len(scratch)==1,scratch
            expected='_CausalObserver' if phase=='causal' else '_ImportedVerifier'
            assert owners and all(one['owner']==expected and one['scope'][2]==phase for one in owners),owners
            assert before==after
            assert all(os.path.isdir(where) for where in scratch)
            states=case.case.states_for(held.job,held.composed,'job-b')
            result_state=reconciliation.result_of(deployment.integration,result_id)['state'] if phase=='post-import' else None
            retained=[{'scope':key[0],'message':message} for key,message in deployment._host_observation_failures.items()]
            held.composed.close()
            present_after_close=[where for where in scratch if os.path.isdir(where)]
            assert present_after_close==scratch
            results.append({'phase':phase,'failure':failure,'host_calls':calls,'owners':owners,'scratch_created':scratch,'scratch_after_composition_close':present_after_close,'target_unchanged':True,'job_b_stages':states,'post_import_result_state':result_state,'retention':retained,'reports':reports})
        finally:
            case.doCleanups()
print(json.dumps(results,indent=2,default=str))
