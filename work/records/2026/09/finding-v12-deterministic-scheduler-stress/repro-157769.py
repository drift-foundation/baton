"""Validate the retained corrected export without rerunning its schedules."""
import json,pathlib
from tests.tools import scheduler_trace
record=pathlib.Path(__file__).parent
exports=json.loads((record/'trace-157712-composed.json').read_text())['schedules']
assert len(exports)==18
by_name={one['name']:one['artifact'] for one in exports}
for name,artifact in by_name.items():
    assert scheduler_trace.validate(artifact)==[],name
    assert not [one for one in artifact['records'] if one['act']=='submit'],name
matrix=by_name['composed-second-team-matrix']['scenario']['note']
assert 'policy/denied' in matrix['refused_without_grant']['cause']
assert 'policy/denied' in matrix['refused_at_another_scope']['cause']
assert matrix['composed']['participant']=='other.reviewer'
assert matrix['composed']['principal']=='principal:other.reviewer'
assert 'scope:deployment' in matrix['composed']['evidence']
wrong=by_name['composed-wrong-repository']['scenario']['note']['refused']
assert wrong['owner']=='review_cycles.create_line'
assert wrong['asked']=="deployment.line_for('job-b')"
assert 'ProfileRefusal' in wrong['cause']
print(json.dumps({'validated_export_count':len(exports),'submit_records_in_this_composed_export':0,
                  'matrix_configuration_evidence':matrix,'line_refusal_evidence':wrong},indent=2))
