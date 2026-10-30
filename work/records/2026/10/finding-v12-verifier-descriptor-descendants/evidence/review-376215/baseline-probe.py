import importlib.util,sys,unittest
import tools
spec=importlib.util.spec_from_file_location("tools.single_worker",sys.argv[1]);module=importlib.util.module_from_spec(spec);sys.modules["tools.single_worker"]=module;spec.loader.exec_module(module);tools.single_worker=module
suite=unittest.defaultTestLoader.loadTestsFromName("tests.tools.test_single_worker.AFaultedTerminalSurvivesTheContainerThatWroteIt.test_a_real_observing_status_run_mutates_no_durable_state")
result=unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
