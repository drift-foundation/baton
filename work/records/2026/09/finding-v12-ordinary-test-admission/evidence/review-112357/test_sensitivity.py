"""Does the submitted new regression test reject the known broken reader?"""
import ast
import json
from pathlib import Path
from unittest import mock
from baton_v12.integration import driver
from tests.integration.test_driver import TheReaderConsumesTheOwnersActualAnswer as Case

here = Path(__file__).resolve().parent
prior = here.parent / 'review-112277/candidate/v12/python/src/baton_v12/integration/driver.py'
tree = ast.parse(prior.read_text())
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'ordinary_test_evidence')
namespace = dict(vars(driver))
exec(compile(ast.Module(body=[function], type_ignores=[]), str(prior), 'exec'), namespace)
case = Case('test_the_consumer_reads_that_document_without_raising')
try:
    case.setUp()
    with mock.patch.object(driver, 'ordinary_test_evidence', namespace['ordinary_test_evidence']):
        case.test_the_consumer_reads_that_document_without_raising()
    result = {'known_broken_reader': str(prior), 'new_regression_passes_against_broken_reader': True,
              'reason': 'The mocked frozen_output_of returns None, so refusal precedes the evidence/head access.'}
finally:
    case.doCleanups()
(here / 'test-sensitivity.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
