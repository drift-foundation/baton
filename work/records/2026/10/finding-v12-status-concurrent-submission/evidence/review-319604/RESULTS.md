# Review319604 measurements

- Boundary probe: /tmp/w319114-boundary-1qhxlvuk; observations [true,true,true],
  outer transaction released afterwards. Public read_snapshot context/status;
  real SQLite and fake operations, no raw SQL or coordination-store access.
- Added middle-of-materialization advancement probe: wedge episodes.live_of,
  end_episode/open_next through separate real writer; candidate reports old
  episode/history coherently and next status reports episode2. Passed;
  /tmp/w319114-advance-2pafpafb retained.
- Existing 83 status/read-only passes0.189s from diagnosis319578 reused unchanged.
- Broader affected caller suites: test_sweep, test_scheduling, test_restart,
  test_recovery, test_exchange, test_ending, test_final_allocation_release.
  First310-test run1.265s:21 setup failures because /tmp is tmpfs and candidate
  disk root is nonwritable. No product assertion failure established there.
  Supported BATON_V12_DISK_ROOT=/home/sl/src/baton/.w319114-review-g3pn8ud7:
  all310 pass3.021s. Fixture root retained; no candidate mutation.
- Additional read_snapshot closed-handle probe yields raw ProgrammingError before
  its try block; noted capability gap, not used as a second acceptance blocker.
- No live provider, engine launch or product edit; original timeout/unable preserved.
