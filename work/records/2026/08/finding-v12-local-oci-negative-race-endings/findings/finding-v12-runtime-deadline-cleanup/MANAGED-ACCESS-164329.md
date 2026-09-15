# W32577 managed Docker access check — claim164329

Owner reroute164326 assigned exactly two read-only checks through baton.tuner's
own managed execution tools, then return to baton.ops. Both succeeded at 2026-09-13T22:57:46Z.
No tests, containers, builds, installs, image changes, escalation request or
engine-gate execution occurred.

| Standalone managed execution command | Result | Evidence SHA256 |
| --- | --- | --- |
| docker version | Exit0; client29.1.3/API1.52; server Engine29.1.3/API1.52, containerd2.2.1, runc1.3.4 | direct-version-164329.json: 07ea45acea2edaf07c7f9442edb59684d6448bc28dcb60c25093a924b1355932 |
| docker image inspect sha256:9b8c98820877e33d38d33352d86cc3810e5b72d4935a181b82b512b4d3291de8 | Exit0; exact requested immutable Id present, reference entrypoint, user65532:65532 | direct-image-inspect-164329.json: 6934f4d44771f3821775c2e818aee368f42fe1747cbac33c359ec1bf94348815 |

Full raw command output is retained in those two JSON evidence files. Image
RepoTags includes baton-w32577-reference:20260913, Config.Entrypoint is exactly
["python3", "/opt/baton/baton_worker.py"], and Config.User is65532:65532.
This is current managed-tuner image metadata evidence. The already pinned owner
build/COPY-byte evidence in FINDING supplies source correspondence; this claim
did not repeat the owner container/content probe. Interpreter provisioning and
prompt verification of /home/sl/src/baton/.venv/bin/python3 with Python3.13.7 and
jsonschema4.26.0 remain attributed to the existing owner/prompt evidence.

These commands were standalone tools.exec_command invocations with tty=true and
no sandbox override/escalation. The accounting helper only persists guards and
results; it does not launch Docker. This differs from the older denied readiness
probe, which launched Docker inside a Python subprocess wrapper. The observed
success supersedes the broad current inference that tuner cannot access Docker.
It does not erase that earlier failure or establish why the boundaries differ.
In particular, direct-command success is not proof that Docker launched by the
reviewed Python engine supervisor will inherit equivalent access. Ops must bind
the permitted final execution boundary; no additional wrapper/API probe was
assigned or attempted here.

Both probes had persisted expected2s + margin1s guards within the existing
20s aggregate readiness ceiling and author120s allowance, with10s per-call bound.
The tool orchestration measured invocation-to-completion elapsed and recorded
all output/exit status. No call yielded a running session or needed interruption.
This claim spent0.08s; readiness cumulative0.1772790560044814/20s,
remaining19.82272094399552s. Author cumulative68.5709876419988/120s, remaining51.4290123580012s,
30 retained ledger children. direct-probe-account-164329.py and original
verification-162766.json retain guards/results without resetting prior costs.
Reviewer unchanged5.285408751995419/60s, remaining54.71459124800458s.

Return both successful facts to baton.ops under reroute164326. M163303 remains
pending for its owner to resolve using the complete environment evidence and
permitted final invocation. Candidate163413 remains the accepted source/harness;
no candidate file changed in this claim. Proposed engine180s stays unactivated.
Pinned test execution, actual deadline engine acceptance and W161230 DEPLOYMENT
fresh-hash handback remain open; no Work or parent closure is claimed.
