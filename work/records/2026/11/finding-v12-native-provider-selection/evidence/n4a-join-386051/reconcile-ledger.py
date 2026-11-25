from pathlib import Path
import sys,json,io
repo=Path('/home/sl/src/baton/work/scratch/w385830-join-386051/repo')
sys.path.insert(0,str(repo/'v12/python'))
from tools.parallel_test import account,present_accounting
E=Path(__file__).resolve().parent
for group in sys.argv[1:]:
 summary=json.loads((E/(group+'.summary.json')).read_text())
 reports=[]
 for p in sorted((E/'isolated-shards'/group).glob('*.report.json')):
  r=json.loads(p.read_text());r['label']=p.name;reports.append(r)
 ledger=account(summary['collected_ids'],reports)
 out=io.StringIO();present_accounting(ledger,out)
 lines=out.getvalue().splitlines()
 match=lines[-2:]==summary['accounting_lines'][-2:]
 ledger['retained_shards']=len(reports);ledger['matches_supported_runner_accounting']=match
 (E/(group+'.ledger.json')).write_text(json.dumps(ledger,indent=2)+'\n')
 print(group,lines[-2:], 'matches_runner',match)
