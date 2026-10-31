import ast,pathlib
from unittest.mock import patch
from tests.manager import test_boundary_inventory as m
samples = {
"attribute": """
def _consume(record):
 return record["state"]
class Door:
 def door(self):
  return _consume(self.unvalidated)
""",
"external_call": """
import json
def _consume(record):
 return record["state"]
def door(store):
 return _consume(json.loads('{"state": 42}'))
""",
"global": """
import os
VALUE = os.environ.get('RAW')
def _consume(record):
 return record["state"]
def door(store):
 return _consume(VALUE)
"""}
for name,source in samples.items():
 m._clear_boundary_projections()
 try:
  with patch.object(m,'_sources',lambda:((pathlib.Path('sample.py'),ast.parse(source)),)):
   print(name,'validators',dict(m.owning_validators()))
   try:
    m.StageCProtections()._handed_owned('sample.py:_consume','record',m.EveryReceivingEntryHasOneOwner(),subtests=False)
    print('ACCEPTED')
   except AssertionError as e:print('REJECTED',str(e))
 finally:m._clear_boundary_projections()
