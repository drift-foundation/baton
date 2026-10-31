"""Run from repo root with PYTHONPATH=v12/python/src:v12/python; disposable store only."""
import ast,json,pathlib,unittest
from unittest.mock import patch
from tests.manager import test_boundary_inventory as m
from tests.manager.token_support import TokenFixture
from baton_v12.worker_manager import tokens,custody
source = """
def _consume(record):
    return record["state"]
def door(store):
    row = store._connection.execute("SELECT * FROM held").fetchone()
    return _consume(row)
"""
m._clear_boundary_projections()
try:
    with patch.object(m,'_sources',lambda:((pathlib.Path('sample.py'),ast.parse(source)),)):
        print('validators:',dict(m.owning_validators()))
        m.StageCProtections()._handed_owned('sample.py:_consume','record',m.EveryReceivingEntryHasOneOwner())
        print('UNSOUND WITNESS: passed with no validators')
finally:m._clear_boundary_projections()
c=unittest.TestCase();f=TokenFixture(c)
try:
    held=f.held(); f.instant='2030-01-01T00:00:00.000Z'
    print('before corruption expired:',tokens.token_of(f.store,f.domain,held['generation'])['expired'])
    row=f.store._connection.execute('SELECT operation_id,result FROM operations WHERE kind=?',(tokens.ACQUIRED_KIND,)).fetchone()
    document=json.loads(row['result']);document['expires_at']='2099-01-01T00:00:00.000Z'
    f.store._connection.execute('UPDATE operations SET result=? WHERE operation_id=?',(json.dumps(document),row['operation_id']))
    print('after corruption expired:',tokens.token_of(f.store,f.domain,held['generation'])['expired'])
finally:c.doCleanups()
for seconds,most in [(None,'bad'),(1,float('inf')),(float('nan'),120)]:
    try:print('allowed',repr(seconds),repr(most),'returned',repr(custody.allowed(seconds,most)))
    except Exception as exc:print('allowed',repr(seconds),repr(most),type(exc).__name__,str(exc))
