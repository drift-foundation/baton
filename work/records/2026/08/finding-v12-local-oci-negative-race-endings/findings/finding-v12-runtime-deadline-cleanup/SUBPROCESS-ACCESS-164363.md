# W32577 pinned-interpreter subprocess access check — claim164363

Owner reroute164359 assigned the two read-only Docker metadata commands as
subprocesses of /home/sl/src/baton/.venv/bin/python3 through the managed script
launch boundary intended for engine-gate.py. Both completed with **exit1** and:

```text
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

Version stdout contains client29.1.3/API1.52 only. Image inspection stdout is[];
that is an access failure, not evidence that the image is absent. The exact image
operand was sha256:9b8c98820877e33d38d33352d86cc3810e5b72d4935a181b82b512b4d3291de8.
Direct standalone Docker success remains recorded in MANAGED-ACCESS-164329.md.
Together these results isolate the observed access difference to invocation
boundaries; they do not establish a daemon outage or missing image.

## Exact invocation and evidence

Both launches used standalone tools.exec_command, cwd=/home/sl/src/baton,
tty=true, default installed sandbox policy, and no escalation/override:

```text
/home/sl/src/baton/.venv/bin/python3 /home/sl/src/baton/work/records/2026/08/finding-v12-local-oci-negative-race-endings/findings/finding-v12-runtime-deadline-cleanup/subprocess-probe-164363.py version
/home/sl/src/baton/.venv/bin/python3 /home/sl/src/baton/work/records/2026/08/finding-v12-local-oci-negative-race-endings/findings/finding-v12-runtime-deadline-cleanup/subprocess-probe-164363.py inspect
```

The script invokes subprocess.run with capture_output=True and timeout<=10s,
without an alternate environment/socket or privileged wrapper. Commands are
exactly docker version and docker image inspect with the immutable ID above.
This exercises the pinned-Python-to-Docker subprocess edge used by the supervisor;
it does not execute the supervisor, test child or any container.

- subprocess-probe-164363.py SHA256 2ac2aa605005935a90dff4b3700efe05f53820b1b1a5f9581a628a9661d19d47.
- subprocess-version-164363.json SHA256 315c86e638777d5fffe24fc4b325b363c8f86c016bae15dac174157ce5df227b.
- subprocess-image-inspect-164363.json SHA256 281d41db5ab5410044464d27b4a723639285aabbc336a1938849b8dcfddac3cd.

Both evidence files include exact argv, cwd, interpreter, metadata, stderr,
stdout, guards, exit code and elapsed time. The pinned interpreter itself works
and reports Python3.13.7/jsonschema4.26.0. No package or test execution was needed
to confirm those already installed metadata. No direct Docker command was repeated.

## Accounting and return

Each child had a persisted expected2s+margin1s guard fitting the existing20s
readiness ceiling and author120s allowance, with10s timeout. Both denials are
charged. This claim spent0.010592196005745791s; readiness cumulative0.1878712520102272/20s,
remaining19.812128747989775s, within author68.58157983800454/120s, remaining51.418420161995456s.
All32 rows remain in verification-162766.json; no reset or additional bank.
Reviewer unchanged5.285408751995419/60s, remaining54.71459124800458s.

Return to baton.ops: the unresolved operational prerequisite is a permitted
managed launch boundary for the accepted Python supervisor and its Docker
subprocesses. Owner interpreter and current reference-image provisioning remain
valid; no rebuild, install or socket-permission change is inferred from this
failure. Ops must supply the exact repair/allowed invocation before final gate
selection. M163303 stays pending for ops resolution.

No tests, containers, builds, installs, escalation, live models, image mutation
or candidate changes occurred. Candidate163413 remains accepted; engine180s is
unactivated. Required pinned acceptance tests, actual deadline engine evidence,
W161230 DEPLOYMENT handback and all Work/parent closure remain open.
