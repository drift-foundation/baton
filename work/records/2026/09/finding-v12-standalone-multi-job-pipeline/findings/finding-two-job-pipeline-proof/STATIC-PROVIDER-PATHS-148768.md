# W71879 — installed package verified; exact code paths for static inspection

baton.tuner claim148768, following owner148760 and accepted
review-2026-09-12T01-23-14Z.md. This advances the already authorized offline
investigation. No new product-scope decision is required.

The supplied `/tmp/w71879-148686-provider-package.json` is a non-symlink regular
file, mode0644,1476 bytes, SHA256
`204e690591b935992fff95f6d2af6aeac86be074719da7900f1c4e4056f37efe`.
Type and64KiB bound were checked before an O_NOFOLLOW/O_NONBLOCK read; the opened
inode and digest were checked before strict JSON interpretation. An exact copy
and verification record are retained in evidence/diagnostic-148768.

**Confirmed metadata:** package `@anthropic-ai/claude-code`, version2.1.247;
`bin.claude` is `bin/claude.exe`; postinstall is `node install.cjs`. Its published
file list also names `cli-wrapper.cjs` and `sdk-tools.d.ts`. Optional dependencies
include platform packages pinned to2.1.247. This supersedes the previous statement
that installed package metadata is unread. It does not identify which optional
dependency was installed, resolve the executable's file/link type or prove the
native binary version/output contract. The `.exe` suffix does not establish its
platform or contents. No package script or provider binary was executed.

The next three code paths are now established directly by this package metadata.
The earlier Docker-copy access refusal remains unresolved for this participant;
owner148760 performed the metadata copy but did not change that execution boundary.
No repeated denied copy or alternate engine/socket/overlay access was attempted.

## Exact static copies for the operator

Use the same retained container, still independently confirmed exited/read-only,
with image
`sha256:26cdfe7df693d3cfad0190e879e93ba9f3fea2086ecb5c7f1f4c2fe598aced99`
and no mount at the package installation directory. Recheck that posture and
destination absence; execute each command separately. Do not overwrite or add -L.

```sh
docker cp a2b00b62bdbb3f413b6e4e9539cf71190b237430a8856367567315b4f98ef5af:/usr/local/lib/node_modules/@anthropic-ai/claude-code/install.cjs /tmp/w71879-148768-provider-install.cjs
```

```sh
docker cp a2b00b62bdbb3f413b6e4e9539cf71190b237430a8856367567315b4f98ef5af:/usr/local/lib/node_modules/@anthropic-ai/claude-code/cli-wrapper.cjs /tmp/w71879-148768-provider-cli-wrapper.cjs
```

```sh
docker cp a2b00b62bdbb3f413b6e4e9539cf71190b237430a8856367567315b4f98ef5af:/usr/local/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe /tmp/w71879-148768-provider-claude.exe
```

Return type/size/SHA256 for each regular file, plus source container/image identity.
Bound either script to1MiB and the executable to256MiB. If absent, symlink,
oversized or unreadable, report that exact finding; do not dereference a link or
substitute another version. These limits bound static acquisition, not execution
or a model budget. Do not run any copied file. No install, download, container
start, provider-output/credential read or recursive directory copy is requested.
The SDK tools declarations are not needed before tracing the actual launcher.

The tuner will inspect installation and wrapper code as text, identify any actual
native target without executing code, verify file signatures/hash provenance, then
statically trace the exact structured error writer. A symlink or relocation may
establish another precise installation path; its existence/content must still be
verified. An isolated string or type declaration is insufficient proof that a
value reaches the active JSON output. If native code remains opaque, identify the
specific missing versioned source/schema rather than infer a discriminator.

## Diagnostic acceptance and preservation

DIAGNOSTIC-ACQUISITION-148686.md remains the accepted detail/exclusion,
compatibility, test and image-provenance boundary. Useful nonsecret explanation
and supported error context, explicit omissions and attempt correlation are
required; a new coarse category alone remains insufficient. Authentication stays
unknown without distinguishing evidence. No arbitrary text/ID is safe merely by
its field name; no raw provider document, credential or stderr/verification stream
is captured. Existing bounded stdout/drain/strict parsing remains the starting
point. Discarded run6 detail cannot be reconstructed from package metadata.

No source, test, image, accepted runner helper or execution marker changed.
All43 prepared-147109 files again match hash/size/type/mode; prior49-test independent
acceptance stands without a redundant test run. No classifier implementation or
published-result compatibility result is claimed. A future supported source change
still needs focused sentinel/classification/compatibility tests, an independently
bound successor reader and both-image provenance before deployment.

Current verification cost0.0032709279912523925s; listed cumulative preparation/
diagnosis8.031163135987693s plus untimed reads/edits/commands, earlier failures and
host/operator/billing uncertainty. Six failed run walls1341.1107609820174s remain
preserved. All1200/240/180/120s and resource/custody/target guards, existing deferrals,
actual A/B proof obligations and run5/run6 uncertainties remain. No model probe,
fresh-run packaging, retry, deadline increase or repair.

Direct independent review of these concrete metadata-derived paths, Next ops for
the existing unavailable copy boundary, then tuner resumes static diagnosis. The
metadata acquisition is complete; actionable detailed diagnostics remain open.
