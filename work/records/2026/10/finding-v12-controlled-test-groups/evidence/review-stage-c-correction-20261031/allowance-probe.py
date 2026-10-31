from baton_v12.worker_manager import custody
from baton_v12.worker_manager.custody import ContractRefusal
bad=[True,"bad",float("inf"),float("-inf"),float("nan"),{},[]]
count=0
for v in bad:
 for a,b in [(None,v),(1,v),(v,120),(lambda:v,120)]:
  try:custody.allowed(a,b)
  except ContractRefusal:count+=1
  else:raise AssertionError((a,b))
for a,b,want in [(None,120,120),(lambda:None,120,120),(2.9,120,2),(-1,120,0),(130,120,120),(0,120,0)]:assert custody.allowed(a,b)==want
print(count,"invalid-input refusals and 6 valid-path checks passed")
