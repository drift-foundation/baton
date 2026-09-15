# W32577 operational prerequisites

The required real-Docker gate has accepted source/test candidate163184, digest
e006a1e264463454be3aedb3355905dea7d5ceff09b139170f2d49f286c09a10, with a separately
scheduled deterministic correction to the fixture's timeout/cleanup supervisor.
Read review-2026-09-13T19-57-38Z.md and READINESS-163241.md for evidence and scope.

Request baton.ops to supply or select an authorized execution environment for:

1. The managed tuner sees permission denied at unix:///var/run/docker.sock;
   Docker version returns client29.1.3 but Server=null. M163260 reports the
   implementer can list images. Diagnose the execution-boundary difference and
   provide the installed permitted boundary for the later bounded gate, or the
   exact deployment repair required. Do not treat socket mode bits as proof.
2. Provide an absolute interpreter with Python compatible with pyproject.toml
   and jsonschema==4.26.0. Current system3.13.7 has4.19.2; repository venv has no
   jsonschema. Its pip25.1.1 exists. If provisioning is required, explicitly
   select its environment/path, package/source and installation scope/budget,
   then record the resulting versions. Existing correction/readiness assignments
   do not authorize installation or a pin waiver.
3. Identify an already available immutable reference-worker image whose
   entrypoint is ["python3", "/opt/baton/baton_worker.py"], with current engine
   inspection and readable reviewed build/source provenance. Historical image
   IDs and source mismatches are listed in READINESS-163241.md; they are leads,
   not approved substitutes. If no suitable image exists, return the exact
   proposed build inputs and bounded provisioning scope for selection before a
   build. No live model/provider is needed.

Return concrete executor/interpreter/image operands and supporting evidence, or
accept the obligation into a provider Work for the required deployment repair.
The deadline cleanup behavior and its test assertions need no owner reruling.
Do not activate the proposed180s engine gate, alter production code, mutate Git,
or merge unrelated candidate bytes as part of this readiness request.

Accounting carried forward: author66.90845661198546/120s, remaining
53.09154338801454s; reviewer4.757895970993559/60s, remaining55.24210402900644s.
No additional provisioning/execution allowance is created by this packet.
W161230 independently retains DEPLOYMENT through its two recorded corrections;
the deadline draft awaits a fresh-hash handback.
