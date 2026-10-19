"""Read-only prelaunch input check; no Job or provider execution."""
import importlib.util,json,pathlib
P=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('packet_prepare',P/'prepare.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.pins()
print(json.dumps({'state':'prelaunch-input-pins-match','base':module.BASE,'run':module.RUN}))
