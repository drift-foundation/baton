import datetime, hashlib, json, os, signal, sys, time
import publication_entry as p
# No adoption inputs, provider, credentials, or production profile overrides.
# Exercise the actual image's supervisor with a deliberately nonfinishing child.
seconds=3
absolute=datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(seconds=seconds)
instant=absolute.isoformat().replace('+00:00','Z')
marker='/tmp/child-ready'
program="import pathlib, signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); pathlib.Path('/tmp/child-ready').write_text('ready'); time.sleep(120)"
start=time.monotonic()
result=p.supervised([sys.executable,'-c',program],instant)
assert os.path.isfile(marker), 'fixture child did not start'
assert result['started'] and result['timed_out'] and result['group_gone'],result
assert result['status'] is None,result
elapsed=time.monotonic()-start
assert elapsed<15,elapsed
# The same absolute deadline is already spent: replay starts no new child.
again=p.supervised([sys.executable,'-c',"open('/tmp/repeated','w').write('bad')"],instant)
assert not again['started'] and again['timed_out'] and again['group_gone'],again
assert not os.path.exists('/tmp/repeated')
print(json.dumps({'scope':'real-container worker supervisor only; host expiry/owner-item proof separate','deadline_seconds':seconds,'elapsed_seconds':elapsed,'first':result,'same_deadline_again':again,'publication_entry_sha256':hashlib.sha256(open('/opt/baton/publication_entry.py','rb').read()).hexdigest()},indent=2))
