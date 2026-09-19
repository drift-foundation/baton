# W197661 — the deployment packet, claim198640

Owner seq198635: *"prepare one reproducible deployment packet binding the
installed manager, accepted image IDs, configuration and required
directories."* This is that packet.

**It selects nothing.** It binds what a deployment would use. It installs
nothing, starts nothing, submits no Job, calls no model, reads no credential
and touches no production store or runtime. Selecting a digest is an owner act
and nothing here performs one.

`deployment-packet.json` is the machine-readable binding.
`verify_packet.py` re-derives every claim in it and is how a reviewer checks
this rather than believing it — **27 checks, all passing**, results in
`verification.json`. It deploys nothing either.

## What it binds

**The installed manager.** `v12/python/build/out/distro/baton-v12-stack`,
version `12.0.0`, launcher sha256 `04d69e37a6e99621b5e7342aa6d6dfbdd7dcae0624301f827abf258c66c89e6c`,
build stamp commit `e486652c` **dirty, 25 changed entries**, Python 3.13.7 on
`Linux-6.17.0-41-generic-x86_64`. The verifier re-reads `identity`, holds it
against the binding, and checks the manager's self-reported sha256 against the
bytes on disk.

**A caveat that travels with it, stated as the inference it is.** That build
came from a dirty tree, and W194457's shared-workspace-identity candidate —
awaiting its own review — has modification times earlier than the build, so the
bundle very likely embeds unreviewed manager bytes. I could not settle it from
the artefact: a byte search for the candidate's markers found nothing **and
neither did the control**, because module bytes live compiled inside the PYZ.
The method cannot answer the question; it is recorded so nobody repeats it.
W197661's own accepted correction is unaffected — it lives in
`v12/worker/baton_worker.py`, which travels in the **images**, not in this
bundle.

**The accepted image IDs.** Provider `sha256:35f36286…`, integration
`sha256:dac354d8…`, both from immutable base `sha256:0697b659…`, accepted by
`review-2026-09-17T23-00-20Z.md`. The verifier asks the engine for each: id
equality, `65532:65532`, the expected entrypoint, no credential environment
override, and ordered base-layer ancestry.

**The configuration, in the two parts it actually has.** The instance selection
is `baton.v12.stack-bootstrap/1`. The capacity selection is separate and is
**where `image_digest` is bound** — `bootstrap.DEFERRED` holds `workers` out of
the instance document because a worker's `deployment` carries a digest-sealed
input manifest naming an Authority and a Work, which cannot be written before
the instance exists. That is not a detail: **it is where the incident lives.**
The stopped production instance's `deployment.json` still names
`sha256:2e222e4c…` as its worker image, and the verifier confirms that it still
does and that it names neither accepted image.

**The required directories**, derived by calling `bootstrap.layout(destination)`
rather than transcribed — the verifier re-derives them and compares, so a
layout change in the code fails this packet instead of silently outdating it.

## Reproducing an installation from it

```sh
cd v12 && just setup                          # ONE TIME: the build environment
cd v12 && just build                          # ONE TIME: the one-folder runtime
cd v12 && just bootstrap <INPUTS> <DESTINATION> <DISTRO>
<DESTINATION>/distro/baton-v12-stack identity # bind what was installed
# then the capacity selection, per worker, naming the accepted image digest
```

The owner-only selections the bootstrap refuses by name rather than inventing —
`image_digest`, `adapter_name`/`adapter_digest`, the profile and policy digests,
and the credential selections — are listed in the packet under
`configuration.part_two_capacity_selection.owner_only_selections`. The accepted
reference for composing them is
`work/records/2026/09/finding-v12-stack-launcher/DEPLOYMENT-INPUTS-185653.md`.

## The fixture-image rule, before any instance exercise runs

The owner requires a **deterministic fake provider** for the disposable-instance
exercise and requires fixture differences labelled explicitly. The difference is
concrete: the accepted provider image injects the **real** adapter
(`dogfood_entry.py` → `ClaudeAgent`), while a deterministic fake provider uses
the reference recipe's `scripted_agent.py` seam. **An instance exercise that
runs a fake provider is running an image that is not the accepted one.**

So the rule, and the verifier holds the recipes to it: the accepted digests are
what a production selection would use; the fixture digest is what a lifecycle
was actually exercised with; evidence names **both** and never substitutes one
for the other; and **no live provider coverage may be claimed from a fixture
run.**

## What this packet does NOT do

It does not carry out the disposable-instance exercise — task receipt, candidate
collection, independent review and report-and-hold. That half of owner seq198635
is **not done** and is returned with its exact remaining scope rather than
partially performed. See `PROGRESS.md` for the claim's account and
`EVIDENCE-198640.json` for the measurements.
