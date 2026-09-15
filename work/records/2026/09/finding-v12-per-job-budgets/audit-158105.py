"""Read-only provenance validation; no candidate or Git mutation."""
import difflib,hashlib,json,pathlib,subprocess,time
root=pathlib.Path('/home/sl/src/baton');record=pathlib.Path(__file__).resolve().parent
foreign=root/'work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/evidence/completion-observation-153138'
start=time.monotonic()
previous=json.loads((record/'review-158071.json').read_text())
packet=json.loads((record/'provenance-158092.json').read_text())
head=subprocess.check_output(['git','log','-1','--format=%H'],cwd=root,text=True).strip()
def sha(data):return hashlib.sha256(data).hexdigest()
rows=[];overlaps=[]
for row in packet:
    name=row['path'];current=(root/name).read_bytes()
    answer={'path':name,'candidate_sha256':sha(current),'candidate_bytes':len(current),'owner':'W156162','candidate_matches_packet':sha(current)==row['candidate_sha256'] and len(current)==row['candidate_bytes'],'candidate_matches_last_review':sha(current)==previous['candidate_after'][name]['sha256']}
    if row['tracked_at_head']:
        base=subprocess.check_output(['git','show',head+':'+name],cwd=root)
        answer.update(base_sha256=sha(base),base_bytes=len(base),base_matches_packet=sha(base)==row['base_sha256'] and len(base)==row['base_bytes'])
    else:
        answer.update(base_sha256=None,base_bytes=None,base_matches_packet=row['base_sha256'] is None and row['base_bytes'] is None)
    if name.endswith('/stage_execution.py') or name.endswith('/test_stage_execution.py'):
        old=(foreign/'base'/name).read_bytes();new=(foreign/'candidate'/name).read_bytes()
        diff=subprocess.check_output(['git','diff',head,'--',name],cwd=root,text=True)
        (record/('overlap-158105-'+pathlib.Path(name).name+'.diff')).write_text(diff)
        hunks=[]
        for chunk in diff.split('\n@@ ')[1:]:
            body='@@ '+chunk
            owned='W71879' if ('test_readonly_reconciled_completion_without_runtime_reaches_outer_observer' in body or '-        row = attempt_runtime_of(self.control, stage["attempt_id"])' in body) else 'W156162'
            hunks.append({'header':body.splitlines()[0],'sha256':sha(body.encode()),'owner':owned})
        # Exact foreign candidate method is already present among current bytes.
        def method(text,marker):
            begin=text.index(marker);end=text.find('\n    def ',begin+len(marker))
            return text[begin:] if end<0 else text[begin:end]
        marker=('    def test_readonly_reconciled_completion_without_runtime_reaches_outer_observer(' if '/tests/' in name else '    def observe_integration(')
        candidate_method=method(new.decode(),marker);current_method=method(current.decode(),marker)
        overlap={'path':name,'foreign_work':'W71879','foreign_base_sha256':sha(old),'foreign_candidate_sha256':sha(new),'foreign_base_equals_current_head':old==base,'foreign_method_sha256':sha(candidate_method.encode()),'foreign_method_matches_current':candidate_method==current_method,'current_diff_hunks':hunks}
        overlaps.append(overlap);answer['owner']='W156162 plus retained W71879 hunk'
    rows.append(answer)
assert len(rows)==27 and len({one['path'] for one in rows})==27
assert all(one['candidate_matches_packet'] and one['candidate_matches_last_review'] and one['base_matches_packet'] for one in rows)
assert all(one['foreign_base_equals_current_head'] and one['foreign_method_matches_current'] for one in overlaps),overlaps
result={'work':'W156162','claim':158105,'base_commit':head,'rows':rows,'overlaps':overlaps,'elapsed_seconds':time.monotonic()-start,'runtime_tests_run':0,'prior_review_seconds':previous['review_spent_seconds'],'author_spent_seconds':previous['author_spent_seconds'],'author_measured_runs':previous['author_measured_runs']}
result['review_spent_seconds']=result['prior_review_seconds']+result['elapsed_seconds']
(record/'review-158105.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'base_commit':head,'paths':len(rows),'new_paths':sum(one['base_sha256'] is None for one in rows),'all_packet_base_candidate_hashes_match':True,'overlaps':overlaps,'audit_seconds':result['elapsed_seconds'],'review_spent_seconds':result['review_spent_seconds']},indent=2))
