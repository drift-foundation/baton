# First v12 dogfood task

## Objective

Add focused unit coverage for
`v12/spike/ping-pong/preflight.py::_observed_readable`.

The production function asks a nominated OCI engine to run a disposable
`alpine:3.20` container as uid/gid 65532, with no network and the nominated
credential file mounted read-only at `/probe`. The container runs `test -r`;
it does not open or print credential content. The current harness tests
readiness with this function mocked, so the actual subprocess vector and its
answer mapping have no direct regression coverage.

## Required behavior

Add the smallest maintainable cases to
`v12/spike/ping-pong/test_harness.py` that establish all of these facts:

1. An absent nominated path returns the existing `probed: false` answer and
   invokes no subprocess.
2. A successful probe uses the nominated engine, `--rm`, uid/gid
   `65532:65532`, `--network none`, an exact read-only bind from the nominated
   file to `/probe`, the pinned `alpine:3.20` image and `test -r`.
3. Exit zero plus stdout `readable` maps to `probed: true, readable: true`;
   exit zero with the unreadable answer remains a completed negative probe.
4. A nonzero probe process remains `probed: false`, carries the bounded status
   already returned by production, and is not misreported as unreadable.

Do not change `preflight.py` unless a test exposes a genuine defect. Do not
read credential bytes, use a real credential, require a Docker daemon, weaken
an existing assertion, or broaden W17110's spike boundary. Mock the process
crossing and use a temporary ordinary file whose content is explicitly not a
credential.

## Delivered source subset

Preserve these repository-relative paths in the read-only input and editable
copy:

- `v12/spike/ping-pong/preflight.py`
- `v12/spike/ping-pong/trial.py`
- `v12/spike/ping-pong/test_harness.py`

The candidate output must preserve the same relative layout. No `.git`
directory or repository metadata is part of the delivery.

## Verification

Run from the delivered source root:

```text
python3 v12/spike/ping-pong/test_harness.py
```

Report the exact exit status and bounded output in `proposal/verification.txt`.
The operator will rerun the same command against the collected candidate.

## Candidate result

The declared `proposal` output contains `candidate/`, `change.patch`,
`result.json` and `verification.txt` as defined by W38956's `FINDING.md`.
`result.json` reports changed paths and a concise summary; it is not authority
for assignment identity, output bytes or verification success.
