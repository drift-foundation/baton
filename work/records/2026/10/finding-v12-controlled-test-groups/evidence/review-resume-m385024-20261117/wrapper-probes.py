import ast,pathlib
from unittest.mock import patch
from tests.manager import test_boundary_inventory as m
samples={
"package_parser_wrapper": """import json
def _read():
 return json.loads('{"state": 42}')
def _consume(record):
 return record["state"]
def door(store):
 return _consume(_read())
""",
"package_environment_wrapper": """import os
def _read():
 return os.environ.get('RAW')
def _consume(record):
 return record["state"]
def door(store):
 return _consume(_read())
""",
"method_wrapper": """import json
def _consume(record):
 return record["state"]
class Door:
 def _read(self):
  return json.loads('{"state": 42}')
 def door(self):
  return _consume(self._read())
"""}
for name,source in samples.items():
 m._clear_boundary_projections()
 try:
  with patch.object(m,'_sources',lambda:((pathlib.Path('sample.py'),ast.parse(source)),)):
   print(name,'validators',dict(m.owning_validators()))
   try:m.StageCProtections()._handed_owned('sample.py:_consume','record',m.EveryReceivingEntryHasOneOwner(),subtests=False);print('ACCEPTED')
   except AssertionError as x:print('REJECTED',str(x))
 finally:m._clear_boundary_projections()
