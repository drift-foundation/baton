"""Show that the applied-boundary case admits a sibling PID namespace.

The inspected answer below differs from the expected Docker answer only in
``PidMode``: it joins another container instead of owning a private namespace.
The case under review still passes because it excludes only literal ``host``.
"""

from unittest.mock import patch

from tests.manager import test_lifecycle_composition as composition


case = composition.DockerComposition(
    "test_the_runtime_boundary_is_the_one_the_launcher_composed")
case.store = object()
case.attempt = "attempt-1"
case.prepared = lambda: (object(), {}, object())
case.attempt_row = lambda: {"runtime_id": "runtime-1"}
case.inspected = lambda _runtime_id: {
    "Mounts": [],
    "HostConfig": {
        "NetworkMode": "none",
        "PidMode": "container:sibling-runtime",
        "Privileged": False,
        "SecurityOpt": ["no-new-privileges"],
        "CapAdd": [],
        "CapDrop": ["ALL"],
        "PidsLimit": 512,
        "ReadonlyRootfs": True,
    },
    "Config": {"User": "65532:65532"},
}

with patch.object(composition, "request_runtime_start", return_value=None):
    case.test_the_runtime_boundary_is_the_one_the_launcher_composed()

print("security case accepted PidMode=container:sibling-runtime")
