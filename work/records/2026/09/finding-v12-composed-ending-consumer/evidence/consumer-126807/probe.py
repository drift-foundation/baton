import json
from pathlib import Path
from tests.tools.test_stage_execution import OrdinaryTerminalLifecycle

case = OrdinaryTerminalLifecycle("test_one_job_completes_correction_integration_and_terminal_handoff")
try:
    case.setUp()
    case.test_one_job_completes_correction_integration_and_terminal_handoff()
    Path(__file__).with_name("terminal.json").write_text(json.dumps(case.terminal_evidence, indent=2) + "\n")
    print(json.dumps({"states": case.terminal_evidence["states"], "handoff": case.terminal_evidence["handoff"]}, indent=2))
finally:
    case.doCleanups()
