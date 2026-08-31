# Does the new coverage actually catch anything?

Attempt `attempt-w51487-run4`. Six mutations of
`v12/spike/ping-pong/preflight.py::_observed_readable`, each applied to a
writable copy of the retained candidate, the harness run, the mutation
reverted. No Docker daemon and no credential is involved: the candidate's new
class mocks the process crossing.

| mutation | harness | caught by |
| --- | --- | --- |
| `--network none` dropped from the probe argv | exit 1 | `test_the_probe_asks_the_nominated_engine_about_the_exact_path` |
| `readonly=true` dropped from the bind | exit 1 | the same case |
| `--user` forced to `0:0` | exit 1 | the same case |
| stdout comparison replaced by a constant `readable: True` | exit 1 | `test_a_probe_that_ran_reports_what_it_found` (`said='unreadable'`) |
| a failed probe reported as `probed: True, readable: False` | exit 1 | `test_a_probe_that_did_not_run_is_not_an_unreadable_verdict` |
| the absent-path early return removed | exit 1 | `test_an_absent_path_is_not_probed_at_all` |

Every mutation is caught, and each by the case that owns the fact the task
asked for. A seventh mutation was attempted -- replacing the `returncode != 0`
guard -- and was abandoned rather than approximated: that source pattern occurs
twice in the file, so an edit to it would not have been the single-site change
the others are. The `unreadable-on-failure` mutation drives the same branch by
its return value and is the one reported.

The unmutated candidate: `Ran 30 tests, OK` (26 frozen cases plus the four new
ones).
