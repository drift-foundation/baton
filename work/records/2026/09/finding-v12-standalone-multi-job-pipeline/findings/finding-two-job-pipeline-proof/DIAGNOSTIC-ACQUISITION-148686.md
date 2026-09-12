# W71879 — exact installed provider evidence acquisition

baton.tuner, claim148686; owner return148665. The requested offline inspection
cannot yet establish an authentication discriminator or safe detailed-error
contract. This is the owner's specified minimal acquisition fallback, ready for
independent review. It is not a classifier implementation or diagnostic acceptance.

Read the matching current FINDING.md, PLAN.md, PROGRESS.md and independent
review-2026-09-11T20-42-32Z.md at this record root. The parent's
FINDING/PLAN01:12:52Z requires useful nonsecret error detail, not merely a new label.

## Evidence and operational blocker

The retained run6 A container is
`a2b00b62bdbb3f413b6e4e9539cf71190b237430a8856367567315b4f98ef5af`.
Direct Docker inspection confirms it is exited, has a read-only root filesystem,
and uses provider image
`sha256:26cdfe7df693d3cfad0190e879e93ba9f3fea2086ecb5c7f1f4c2fe598aced99`.
Its mount destinations do not cover `/usr/local/lib/node_modules`.

The exact metadata copy below failed with exit1:
`permission denied while trying to connect to the docker API at unix:///var/run/docker.sock`.
No package metadata/code was acquired. Read-only `docker inspect` success does not
grant `docker cp` access. This is an operational execution-boundary finding, not
evidence of a Baton product defect. No socket, overlay filesystem, privileged
wrapper, engine substitution or escalation was used to evade it.

The host program `/home/sl/.local/bin/claude` resolves to
`/home/sl/.local/share/claude/versions/2.1.263`, SHA256
`26d020351e8112f4006790f3cfce43b4c9df0c1bb1d0e542364d64151b81d5ba`.
It was hashed, not executed. Host version directories contain2.1.241/2.1.250/2.1.263.
The repository image recipe pins2.1.247; historical W51487 evidence reports that
version. Neither attests the installed native binary, and a different host version
cannot establish this image's output vocabulary. W55361's reproducibility finding
already identifies the postinstall download behind the pinned npm version.

The current adapter and W55360 decision were readable. Only the observed
`terminal_reason: api_error` mapping is supported. Retained run6 reports have
api-error/status1, with authentication cause unknown. Discarded error detail
cannot be reconstructed. The local filename search was incomplete where private
`/tmp` directories refused reads; those refusals and absent guessed locators are
recorded in evidence/diagnostic-148686/operational-finding.json.

## Exact minimal next action

An operator with the existing Docker read boundary can perform this single
static copy. Alternatively, the deployment can authorize this exact copy for
baton.tuner. No new model/network/image-execution authority is needed or requested.
First confirm the same container is still exited, read-only and image-bound as
above, and that the fresh destination is absent. Do not overwrite a prior file.

```sh
docker cp a2b00b62bdbb3f413b6e4e9539cf71190b237430a8856367567315b4f98ef5af:/usr/local/lib/node_modules/@anthropic-ai/claude-code/package.json /tmp/w71879-148686-provider-package.json
```

Do not use `-L`. Return a non-symlink regular file, at most64KiB, plus its SHA256
and the exact source/container/image metadata. If the file is missing or a
symlink, report that fact without dereferencing it. The path is a conventional
npm location supported by the image recipe; its existence was not proved because
the daemon refused before resolving it. A missing file is a locator finding, not
permission to search credential homes.

This metadata-only step is the smallest concrete missing input. The tuner can
then inspect it as data and identify the exact `bin`/postinstall/native-install
code paths, without running npm, JavaScript, the native executable or any script.
The next static copy must name those actual installation paths and bind their
hashes to this image; it must not guess a host version or download a replacement.
If native code lives elsewhere, report its statically established locator before
copying it. No recursive copy of a home, `/run`, `/input`, `/output`, provider logs
or credential source is part of this acquisition. No container start/build/create
is required. The six historical runs remain untouched.

## What the acquired code must establish

Trace the exact version's structured JSON writer and upstream error construction
to establish which fields reach this adapter's `--output-format json` record.
Pin byte offsets/source symbols and hashes for each proposed discriminator and
explanation/status/request-identifier field. A SDK type in isolation, strings in
a binary without their call path, or current web documentation for another
version does not prove the active output contract. If stripped/opaque code cannot
establish the path, state that limit and identify the exact versioned vendor
schema/source needed; do not invent a network probe or classifier entry.

Detailed text and identifiers are not intrinsically safe because their names
sound useful. Establish whether each value is a provider-owned constant, bounded
typed code, or arbitrary text capable of echoing a request, header or credential.
Only an evidenced collection and publication boundary may cross into retained
artifacts. Preserve meaningful supported explanation and error context; explicitly
mark absent, unavailable or withheld detail. A new coarse label alone does not
satisfy the owner. Pattern-based redaction without a demonstrated exclusion
boundary must not be advertised as making arbitrary provider prose safe.

Keep current bounded in-memory stdout collection, strict/total JSON handling,
overflow/partial refusal and drain deadline. Keep provider stderr and both
verification streams unread on DEVNULL. No credential payload is read to build a
redaction list. No arbitrary raw document, unknown member, parser exception or
unrecognized diagnostic text is retained. Authentication remains unknown unless
the exact supported signal distinguishes it. Static discovery can establish a
future classifier contract; it cannot diagnose the lost historical run6 error.

## Implementation, regression and provenance implications

Once supported evidence exists, the explicitly assigned product boundary is
`v12/worker/claude_agent.py`: parsing, `_provider`, and the three publication sites
for dogfood-proposal/1, dogfood-proposal/2 and review-log/1. Preserve existing
status, failure_reason, seconds_bound, success/failure and recap behavior while
independently reviewing any added diagnostic structure. Detail must be correlated
through existing task, artifact, attempt and assignment ownership. It must not
decide lifecycle success or replace the accepted first-failure observation.

The accepted runner's `failure_observation.py` currently emits only its four
closed reason words, status and unknown authentication cause. Merely adding detail
inside the image would leave that reader blind. A separately bound successor
helper must validate any new published diagnostic contract and safely expose its
supported detail/omissions while retaining all correlation/no-follow/bounds guards.
Do not edit prepared-147109 in place; its existing four-helper review binding and
43-file manifest remain valid historical evidence.

Focused synthetic cases belong in
`v12/python/tests/manager/test_claude_agent.py`, with actual pipe/drainer coverage
and proposal/review/recap sink checks. They must cover exact supported values,
unknown/auth-ambiguous cases, success, malformed/duplicate/deep/partial/oversized
JSON, and secret sentinels in explanations, codes, IDs, keys, nested fields and
every rejected input. Any accepted detail must demonstrate useful preservation
and credential exclusion together. Test old published-result compatibility and
new reader compatibility. Existing assertions change only as necessary for the
explicit reviewed boundary under W71830 standing authority; no tests changed now.

Both provider and integration images copy `claude_agent.py`; a source change makes
the current provider image above and integration image
`sha256:8e84757c898b15b98fce42ca2d5a3a4ba07e44c0c744978870bdf36a4aa2cdb2`
stale for that change. Any later package must bind the changed source, exact
provider installation evidence, new image content/digests, compatible helper and
independent review. Static acquisition authorizes no build, image selection,
execution marker, fresh-run packaging or model retry. A rebuilt tag cannot stand
in for new immutable provenance.

## Verification and handoff

evidence/diagnostic-148686/source-and-preservation.json binds the read policy,
adapter/test/image sources and verifies all43 accepted prepared-147109 files by
hash, size, regular-file type and mode. Its manifest SHA256 remains
`94d8b8e83b5d11a25edc8b91ae54e9bef98bc7a718cd8d17616784a00ea22cb2`.
No executable candidate changed, so the prior49-test independent acceptance
stands; no new classifier or compatibility tests are falsely claimed to pass.

Preservation/source verification cost0.00365550399874337s. Listed cumulative
preparation/diagnosis is8.02408010199036s plus untimed reads, hashing, edits, failed
commands, host/operator and provider-billing uncertainty. Six failed run walls
remain1341.1107609820174s. No reserve transfer or tool wall-time double counting.
Keep1200/240/180/120s and all resource/custody/target/success guards and existing
deferrals. Actual A/B settlement, derived judgments/import, causal/terminal proof,
run5 writer/coordinator uncertainty and run6 provider cause remain open.

Pass directly to baton.feat for independent review of this requested fallback,
Next baton.ops for the precise unavailable static-copy action. No repeated generic
planning gate is proposed. Diagnostic implementation resumes when exact-version
evidence is readable; a label-only change does not complete the requirement.
