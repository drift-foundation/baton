import pathlib,runpy
held=runpy.run_path(str(pathlib.Path(__file__).with_name('repro-157602.py')))
assert len(held['calls'])==2,held['calls']
assert len(held['archives'])==2,held['archives']
assert [one['new_child_calls'] for one in held['observed']]==[1,0,1]
assert len(held['retained'])==2
print('Prior harness collision and repeat materialization reproducer now confirms independent failures and no repeat archive.')
