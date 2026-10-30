import json
from unittest.mock import patch
from baton_v12.job_manager import templates, execution_limits
from baton_v12.job_manager.submission import submit, boundary_seconds
from tests.job_manager.test_templates import request, configuration, JOB
from tests.job_manager.fixtures import JobManagerCase
c = JobManagerCase(); c.setUp()
try:
    r = request(template=templates.IMPLEMENTATION_REVIEW)
    before = templates.resolve(r, configuration=configuration())
    newer = dict(execution_limits.GENERATIONS[1]); newer['provider_turn'] = 7200
    with patch.dict(execution_limits.GENERATIONS, {2: newer}), patch.object(execution_limits, 'CURRENT_GENERATION', 2):
        after = templates.resolve(r, configuration=configuration())
        store = c.store()
        submit(store, before['submission'])
        result = {'same_template': before['template'] == after['template'],
                  'same_submission': before['submission'] == after['submission'],
                  'resolved_before': before['execution_limits'],
                  'resolved_after': after['execution_limits'],
                  'saved_resolution_submitted_provider_seconds': boundary_seconds(store, JOB, 'provider_turn')}
    definition = templates.template_of(templates.IMPLEMENTATION_REVIEW)
    old = definition['completion']['delivers']
    try:
        definition['completion']['delivers'] = 'not-the-reviewed-proposal'
        changed = templates.resolve(r, configuration=configuration())
        result['public_template_lookup_changes_later_resolution'] = changed['rules']['completion']['delivers']
    finally:
        definition['completion']['delivers'] = old
    r['scope'] = ['v12/python/src/baton_v12/job_manager/templates.py']
    scoped = templates.resolve(r, configuration=configuration())
    result['product_scope_becomes_test_scope'] = scoped['submission']['jobs'][0]['test_scope']
    print(json.dumps(result, indent=2))
finally:
    c.tearDown()
