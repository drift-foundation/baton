"""Does a forged `directory_custody` member in a committed cleanup result open a resource release?"""
import json, sys, unittest
sys.path[:0] = ['src', '.']
from tests.manager import test_intake as suite
from baton_v12.worker_manager import intake
class Govern:
    released = []
    def release(self, *a, **k): self.released.append(k)
fixture = suite.TheCommittedCleanupIsReadableWithoutActing("test_" + "x") if False else None
class Probe(suite.TheCommittedCleanupIsReadableWithoutActing):
    def runTest(self): pass
probe = Probe(); probe.setUp()
try:
    settled = probe.settled("retain")
    print("committed ending state/custody/cleanup:", settled.get("state"), settled.get("directory_custody") is not None, settled.get("cleanup"))
    row = probe.store._connection.execute("SELECT operation_id, result FROM operations WHERE kind='runtime.destroy'").fetchone()
    doc = json.loads(row["result"])
    print("writer-cessation record present:", intake._writer_cessation_of(probe.store, doc) is not None)
    govern = Govern()
    intake.authorize_cleanup(probe.store, probe.port, suite.Custodian(), attempt_id=suite.ATTEMPT, retention_policy_digest=suite.RETENTION, govern=govern)
    print("releases with the honest record:", len(govern.released))
    # remove the real cessation evidence, then forge a custody member where none was recorded
    probe.store._connection.execute("DELETE FROM operations WHERE kind = 'cleanup.writer-cessation'")
    govern = Govern(); govern.released.clear()
    intake.authorize_cleanup(probe.store, probe.port, suite.Custodian(), attempt_id=suite.ATTEMPT, retention_policy_digest=suite.RETENTION, govern=govern)
    print("releases with no cessation evidence and an honest record:", len(govern.released))
    doc["directory_custody"] = {"forged": True}
    govern.released.clear()
    probe.store._connection.execute("UPDATE operations SET result=? WHERE operation_id=?", (json.dumps(doc, sort_keys=True), row["operation_id"]))
    govern = Govern()
    try:
        intake.authorize_cleanup(probe.store, probe.port, suite.Custodian(), attempt_id=suite.ATTEMPT, retention_policy_digest=suite.RETENTION, govern=govern)
        print("releases with the forged record:", len(govern.released), govern.released[:1])
    except Exception as e:
        print("forged record refused:", type(e).__name__, str(e)[:160])
finally:
    probe.doCleanups()
