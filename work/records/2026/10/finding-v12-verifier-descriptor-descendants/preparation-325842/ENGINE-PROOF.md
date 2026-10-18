# Proposed kernel proof — not executed or selected

Question: with the actual engine, new reviewed image and declared nonroot identity,
do immutable-parent private tmpfs mount roots resist provider-UID rename/removal/
symlink substitution while ordinary descendants and the exact nested validator
use plain paths, and does teardown stop even a detached descendant? Deterministic
composition cannot prove Linux mount or engine namespace behavior. No model needed.

After implementation review, build/select the corrected image through existing
image provenance workflow, record its digest and exact worker/layout bytes. Do not
substitute a mutable tag, pull a new image implicitly, or reuse the authoring image
as correction proof. At that point select this one no-provider proof separately:

    python3 -B work/records/2026/10/finding-v12-verifier-descriptor-descendants/preparation-325842/engine-proof.py --image sha256:<reviewed-64-hex-image> --execute-reviewed

The digest is necessarily supplied by later reviewed image construction; no image
is built by this preparation. Review source/image binding before filling it in.
A root-owned0755 /run/baton-verifier scaffold must already exist in the image.
This script never starts the provider entrypoint, mounts credentials, host source,
output, authority or Docker socket. No network. One exact object only;20s receipt
window, subprocess deadlines10s, forced exact-object teardown30s and inspect10s;
allow120s external wall deadline including creation/start. No retry. On cleanup
failure preserve object ID and resolve exact cessation, never report acceptance.
Successful payload deliberately leaves a detached sleeper: final exact-container
absence proves mount/process lifetime ended, not leader wait alone.

kernel-payload.py tests same-UID root rename/removal/link refusal, unchanged inode,
ordinary child/grandchild markers, current image nested validator and a live detached
descendant. It uses only inert data. It does NOT prove candidate/credential isolation,
full product wiring, every timeout branch, capacity fit or resource exhaustion.
The topology excludes the unrelated16MiB legacy-log decoy because this diagnostic
has no worker/log delivery; product composition still accounts it in LAYOUT.json.
The2GiB ceiling is unchanged. A receipt is kernel mechanism evidence only.

Product acceptance additionally needs deterministic new/old image-layout refusal,
identity/mode/missing/false-mount rejection, resource/floor accounting, start/timeout
outcomes and candidate/sealed-input preservation, plus exact affected command in
the corrected worker environment. Preserve prior186 proof, then join it on accepted
W321528 source with new cases. Do not relabel old failed formal verification.
This proposed run does not authorize engine use in the correction-authoring Job.
