import ast,pathlib
from unittest.mock import patch
from tests.manager import test_boundary_inventory as m
samples={"map_parser": """import json
def _read():
 return list(map(lambda x: json.loads(x), ['{"state":42}']))
def _consume(record):
 return record["state"]
def door(store):
 return _consume(_read()[0])
""", "map_environment": """import os
def _read():
 return list(map(lambda x: os.environ.get(x), ['RAW']))
def _consume(record):
 return record["state"]
def door(store):
 return _consume(_read()[0])
"""}
for name,source in samples.items():
 m._clear_boundary_projections()
 try:
  with patch.object(m,'_sources',lambda:((pathlib.Path('sample.py'),ast.parse(source)),)):
   print(name,'validators',dict(m.owning_validators()))
   try:m.StageCProtections()._handed_owned('sample.py:_consume','record',m.EveryReceivingEntryHasOneOwner(),subtests=False);print('ACCEPTED')
   except AssertionError as x:print('REJECTED',str(x))
 finally:m._clear_boundary_projections()
