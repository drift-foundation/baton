# The dogfood worker recipe is not reproducible across days

Status: confirmed operational defect; approved reuse-by-digest correction

Work: `W55361`

Discovered while retrying the first useful supervised task under `W51487`.

## Finding

**Observed.** Two normalized, no-source-change builds of `v12/worker/Dockerfile.claude` made on different days produced different image identities:

- run 4: `sha256:b471399a7dcb8300795fe884c471b817ec1d61644130d66ec12fbd4fef76c003`
- run 5: `sha256:8af96742a89489ae974943284fcc65a5fd58e02263a9ae2142b3d0afa4f9c0e6`

The retained comparison is `work/records/2026/08/finding-first-useful-task-second-attempt/evidence/w51487-run6/image-control.md`. The image sizes also differed by 32 bytes.

**Observed.** Both images have the same five base layer diff IDs, the same four repository-copy diff IDs, and the same user-creation diff ID. They differ in exactly these recipe layers:

1. `npm install -g "@anthropic-ai/claude-code@${CLAUDE_VERSION}"`
2. `apt-get update && apt-get install ... ca-certificates python3`

The locally retained `node:22-bookworm-slim` currently resolves to `node@sha256:83f487e0a63425e5b4d146fb5e5be574bcbe1b7b843d3ebafdd95eaf7767a7e5`, and its five layers match both compared images. Therefore the moving `FROM node:22-bookworm-slim` tag is a real future-drift risk, but it was not the observed source of the run-4/run-5 difference.

**Observed.** Both builds name Claude Code version `2.1.247`. Pinning that top-level version did not close the npm layer's inputs. The recipe also resolves Debian packages from the current mirror state on every build.

**Operational limitation.** The retained image manifests and layer identities were readable, but starting a container or requesting image history was denied by the local Docker API. This managed reviewer did not request escalation. Consequently the exact installed Debian package versions and the exact provider postinstall/native-artifact bytes could not be recovered here. An authorized implementation or release environment must inventory and record them; they must not be inferred from the layer identities.

**Confirmed.** `v12/python/tools/worker_image.py` normalizes build receipts, selected volatile config, and tar member mtimes. It deliberately preserves content bytes and base identity. Its existing tests require genuine content differences to remain different image identities. Changing the normalizer to erase fetched-content differences would falsify artifact identity and is outside the correction.

**Confirmed.** The original reproducibility ruling in `work/records/2026/08/finding-worker-image-reproducibility/` was deliberately limited to a pinned base plus repository `COPY` and deterministic metadata. Its plan states that a recipe which installs anything could not make that claim. The dogfood recipe exceeds that closed-input boundary because it performs both npm and apt network installation.

**Impact.** An unchanged repository tree does not identify one dogfood worker artifact across days. A supervised run can silently test a different provider or operating-system payload even when the visible Dockerfile and top-level provider version are unchanged. The run-6 control showed that the image difference did not cause that attempt's provider failure, but it consumed a control run and prevents a strong attribution claim.

## Required ruling — superseded 2026-08-31

**Superseded by the approved ruling below.** This section records the choices
that were presented to the approver. Its cross-day byte-reconstruction goal is
not the current MVP requirement.

The approver must select the durable external-input boundary. These are not equivalent operationally:

1. **Proposed, recommended: content-addressed foundation.** Publish a dogfood foundation image containing the explicit-platform Node base, Python, certificates, Claude package, transitive dependencies, and provider native payload. Address it by immutable digest. Make `Dockerfile.claude` start from that digest and return its changing portion to the already-supported `COPY` plus deterministic-metadata shape. The foundation needs its own reproducible, locked provenance and durable artifact availability; a digest that exists only in one local Docker store is insufficient.
2. **Alternative: fully locked assembly.** Build from a digest-pinned base and immutable Debian snapshot or content-addressed `.deb` inputs, exact package versions/checksums, npm package/lock integrity, and a content-addressed provider native payload. Prefer network-disabled assembly from locally staged locked artifacts. Verification against a remote checksum fails closed on drift but does not by itself guarantee later reconstructability if the bytes disappear.
3. **Not a reproducibility fix: reuse-only policy.** Record and reuse the already-built image digest for one supervised episode, and stop claiming that rebuilding the recipe yields the same artifact. This prevents silent substitution within the episode but would explicitly narrow, not satisfy, this finding's cross-day reproducibility requirement.

The recommended foundation boundary minimizes the mutable dogfood recipe and reuses the normalization contract already proven by `W6633`, but it introduces a separately owned artifact and provenance lifecycle. That ownership and distribution decision requires approval before implementation.

## Acceptance boundary presented for approval — superseded 2026-08-31

**Superseded by the approved MVP boundary below.** In particular, an
independent rebuild is no longer required to reproduce the prior image digest.

Whichever durable boundary is approved:

- The canonical recipe names an explicit platform and an immutable `FROM ...@sha256:...`; a moving tag is not the identity boundary.
- Every apt, npm, transitive, and provider-postinstall/native input is represented in a durable lock/provenance manifest with cryptographic identity and a reproducible availability source. The manifest contains no credentials.
- The canonical assembly does not resolve mutable package indexes or unverified remote payloads. Prefer a network-disabled final assembly from locked artifacts or a content-addressed foundation.
- Two genuinely independent no-cache builds from the same locked inputs, after the existing normalization step, have identical config and image digests. A same-session repeated build alone is not evidence of cross-day input closure.
- Negative tests mutate or substitute each locked artifact class and demonstrate rejection or a changed identity. Missing locked bytes fail closed rather than falling back to current upstream content.
- Existing worker function, no-secret image checks, and dogfood boundary checks continue to pass.
- Documentation and handoffs distinguish rebuilding the locked recipe from reusing one already-built digest.
- The broad prose in `worker_image.py` is qualified to say that independent executions converge only when recipe content inputs and the base identity are the same. The normalizer's content-preserving behavior is not weakened.

## Verification baseline

From `v12/python`:

```text
PYTHONPATH=src python3 -m unittest tests.tools.test_worker_image_build
Ran 29 tests in 0.019s
OK
```

The real dogfood image build test was not run: this reviewer cannot use the local Docker execution API, and the current recipe requires network package resolution. That is an explicit verification gap for the eventual authorized implementation environment.

## 2026-08-31 approved superseding ruling

**Approved by `baton.slaw`, Work event 55641.** Worker images are selected and
reused by immutable digest. Starting another attempt, including a retry for the
same Work, is not a reason to rebuild the image.

A rebuild is authorized only by an explicit update event: an upgrade, worker
source change, security correction, platform change, or deliberate refresh.
The result of such a rebuild is a new artifact. It is not required to be
byte-identical to the previously selected artifact, even if the mutable
upstreams happened to resolve to the same visible versions. The new artifact
must be validated, its digest recorded, and it must be explicitly selected
before an attempt may use it. It never silently replaces the image selected
for ongoing Work.

This explicitly supersedes:

- the recommended content-addressed-foundation decision proposed above;
- the earlier statement that reuse-only semantics would not satisfy W55361;
- the cross-day byte-reconstruction acceptance boundary above; and
- W51487's standing instruction to rebuild merely because a new attempt was
  starting. W51487 remains entitled to select a newly built image when an
  actual worker source correction must travel, as happened for W52800, but a
  later attempt reuses that selected digest until another explicit update is
  recorded.

**Confirmed existing mechanism.** `dogfood_operator.py` already accepts only a
`sha256:` image digest in the grants, places it in the sealed input manifest
and retained evidence, and holds a handoff retry to the same digest. The
manager launches the digest, not a tag. The defect is therefore not a missing
runtime digest fence; it is the operational rule that told a fresh attempt to
create and select a fresh artifact without an update decision.

**Confirmed authority boundary.** The dogfood operator explicitly is not an
authorization service: it executes the grants it was given. It cannot infer
from a digest whether the build was justified, validated, or selected for the
owning Work. Do not turn it into a second policy store. The authoritative
selection is a chronological decision in the owning Work's `FINDING.md`
(digest, approved update reason, validation evidence, and selection event),
with the one currently actionable digest reflected in that Work's `PLAN.md`.
The attempt grants and retained evidence then provide the executable and
auditable equality points. A reviewer compares those values; a new grants file
does not by itself constitute a selection decision.

**Confirmed remaining prose defect.** `tools/worker_image.py` says without
qualification that two independent recipe executions reach one digest. That
is true only when the base identity and every content input are unchanged. Its
normalizer removes volatile build metadata and mtimes; it correctly preserves
different fetched payload bytes. The prose must be narrowed without weakening
the normalizer or its reference-image tests.

## Approved MVP acceptance boundary

- The dogfood operator/runbook says that a new attempt reuses the image digest
  already selected for its ongoing Work and does not invoke a build merely for
  freshness.
- The selected digest and the event that selected it are recorded durably in
  the owning Work's chronological finding and current plan. A grants file,
  sealed input manifest, and evidence record continue to name the exact digest
  used by each attempt, but none silently becomes the selection authority.
- A new digest can be selected only after a recorded update reason from the
  approved list, successful artifact validation, and an explicit selection
  step. Building an image does not itself select it.
- A negative regression proves that a changed digest cannot be treated as an
  unchanged retry or silently spliced into retained evidence. Preserve the
  existing `_RETRY_BINDING` image-digest refusal.
- The normalizer's module/CLI prose states its real boundary: independent
  executions converge only for identical base identity and content inputs.
  Different upstream payload bytes remain different identities.
- The Dockerfile may continue to resolve mutable upstream content for this
  MVP, but its comments must not claim the visible top-level provider version
  completely identifies the resulting artifact. The validated image digest is
  the artifact identity.
- Existing operator, worker-image, dogfood recipe-inspection, real image, and
  no-secret gates remain green. No provider call or fresh supervised attempt is
  required for this policy correction.

## Revalidated patch boundary

**Proposed.** Keep the correction deliberately smaller than the rejected
content-locking design:

1. qualify `v12/python/tools/worker_image.py`'s independent-execution prose;
2. state the selected-artifact/rebuild boundary in
   `v12/python/tools/dogfood_operator.py` and the dogfood Dockerfile comments;
3. add focused tests beside `test_dogfood_operator.py` and
   `test_worker_image_build.py` only where executable behavior changes or an
   existing digest fence needs to be preserved; and
4. append, rather than rewrite, the supersession to active dogfood Work that
   still carries a rebuild-per-attempt instruction.

Do not pin apt/npm inputs, introduce a foundation image, erase content
differences in normalization, rebuild a dogfood image, or run another provider
attempt under this MVP Work. Those are all outside the approved boundary.

**Focused pre-change baseline, 2026-08-31.** Without Docker or a provider call:

```text
test_worker_image_build + TheRecipeIsInspectableWithoutADaemon
36 tests in 0.019s, OK

test_dogfood_operator
159 tests in 0.460s, OK
```

These green tests confirm the existing digest-shaped grants, evidence, retry
binding, normalizer, and inspectable recipe behavior. They do not yet state the
approved cross-attempt selection rule; that is the implementation delta.
