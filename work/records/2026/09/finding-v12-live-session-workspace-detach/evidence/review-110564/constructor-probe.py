"""W106673 claim 110564: real constructor, isolated filesystem, no runtime.
Only chown is mocked so the ordinary reviewer can exercise construction.
Docker and credential materialization are explicit forbidden-call spies.
Run with /usr/bin/python3 -B from any directory.
"""
import json
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import live_controller_restore as candidate
import live_controller_diagnostic as previous
rows = []
for module in (candidate, previous):
    with tempfile.TemporaryDirectory(prefix="baton-w106673-review-110564-") as directory:
        fixture = module.Fixture.__new__(module.Fixture)
        credentials = Mock()
        credentials.materialize.side_effect = AssertionError("credential activity forbidden")
        with patch.object(module.os, "chown") as ownership, patch.object(module, "docker", side_effect=AssertionError("Docker forbidden")) as docker:
            try:
                fixture.__init__(Path(directory), "restored-first", "unused-network", credentials, time.monotonic() + 420)
            except module.wire.Refusal as failure:
                assert failure.args == ("diagnostic-arm-invalid",)
                assert fixture.arm == "cache"
                assert fixture.container is None
                assert fixture.delivery is None
                assert fixture.directory.name == "restored-first"
                rows.append({"module": module.__name__, "requested_arm": "restored-first", "recorded_arm": fixture.arm, "failure": failure.args[0], "container": fixture.container, "credential_calls": len(credentials.mock_calls), "mocked_chown_calls": ownership.call_count})
            else:
                raise AssertionError("constructor unexpectedly succeeded")
            docker.assert_not_called()
            assert credentials.mock_calls == []
print(json.dumps(rows, indent=2))
