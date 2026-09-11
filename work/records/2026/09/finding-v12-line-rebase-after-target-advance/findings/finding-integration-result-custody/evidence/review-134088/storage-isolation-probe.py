import json
from tests.integration.test_reconciliation import ResultCase
c=ResultCase()
try:
 c.setUp()
 before=c.git(c.line,"show-ref")
 held=c.prepare(workspace=c.place(c.line))
 after=c.git(c.line,"show-ref")
 assert held["state"]=="prepared" and before!=after
 print(json.dumps({"state":held["state"],"workspace_is_original_line":held["workspace"]["path"]==c.line,"producer_refs_before":before,"producer_refs_after":after,"prepared_reference":held["prepared"]["reference"]},indent=2))
finally:
 c.doCleanups()
