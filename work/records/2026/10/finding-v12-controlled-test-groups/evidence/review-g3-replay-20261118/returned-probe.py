import json,unittest
from tests.manager.token_support import TokenFixture
from baton_v12.worker_manager import tokens
from baton_v12.contracts import ContractRefusal
case=unittest.TestCase();f=TokenFixture(case)
try:
 held=f.held();cessation=f.launched(held)
 f.instant="2026-09-26T14:20:00.000Z"
 tokens.revoke(f.store,"line-7/workspace","workspace",execution="attempt-support",operation="runtime.start:support")
 tokens.returned(f.store,held,cessation=cessation,reclaiming=True)
 for phase in ("returned", "replacement acquired"):
  if phase=="replacement acquired": newer=f.held(operation="new-operation",execution="new-attempt",attempt="new-attempt")
  state=tokens.token_of(f.store,f.domain,held["generation"])
  try:
   result=tokens.journal_launch(f.store,held,"launch:support");outcome="ACCEPTED"
  except ContractRefusal as ex:outcome="REFUSED: "+ex.message
  print(json.dumps({"phase":phase,"revoked":state["revoked"],"returned":state["returned"],"fence":state["settlement_fence"],"outcome":outcome}))
finally:case.doCleanups()
