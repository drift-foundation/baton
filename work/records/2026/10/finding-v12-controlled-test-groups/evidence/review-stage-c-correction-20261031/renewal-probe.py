import unittest,json
from tests.manager.token_support import TokenFixture
from baton_v12.worker_manager import tokens
case=unittest.TestCase();f=TokenFixture(case)
try:
 held=f.held()
 tokens.renew(f.store,held,execution="attempt-support",operation="runtime.start:support",expected_revision=0)
 f.instant="2030-01-01T00:00:00.000Z"
 print("honest expired",tokens.token_of(f.store,f.domain,held["generation"])["expired"])
 row=f.store._connection.execute("SELECT operation_id,result FROM operations WHERE kind=?",(tokens.RENEWED_KIND,)).fetchone()
 doc=json.loads(row["result"]);doc["expires_at"]="2099-01-01T00:00:00.000Z"
 f.store._connection.execute("UPDATE operations SET result=? WHERE operation_id=?",(json.dumps(doc),row["operation_id"]))
 print("corrupted renewal expired",tokens.token_of(f.store,f.domain,held["generation"])["expired"])
finally:case.doCleanups()
