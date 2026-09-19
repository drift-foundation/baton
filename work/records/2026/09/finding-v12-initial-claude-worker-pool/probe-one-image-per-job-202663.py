"""Measure whether one Job can carry TWO worker images.

W202663. The owner selected "compatible Claude provider and integration
images". `Dockerfile.integration` builds ON a selected provider digest and is
therefore a DIFFERENT artefact with a DIFFERENT entrypoint, so a pool that uses
both is a pool whose implementation/review workers and whose integration worker
name two image digests.

This probe asks the REAL product validators whether that is expressible. It
reads only; it starts nothing, submits nothing and mutates no deployment.

TWO RULES ARE IN QUESTION, and only the first is probed as a live refusal
because the second needs a live stage row:

  single_worker.py:267   a deployment's `image_digest` must EQUAL its own
                         `input_manifest["worker_image_digest"]`;
  single_worker.py:1303  a Job's `input_digest` must EQUAL that manifest's
                         `manifest_digest`, and `baton.v12.job-submission/2`
                         gives a Job exactly ONE `input_digest`.

Together they force every worker serving one Job onto one manifest and
therefore onto one image. The second is read from the source and from
W197661's own measured account of it ("ONE MANIFEST PER JOB, NOT ONE PER ROLE
... review and integration were refused with 'the Job names another bootstrap
input'"), not claimed as newly measured here.

THE INPUT IS A REAL COMPOSED DOCUMENT, not a fixture: the integration worker
the owner's PREVIOUS instance was configured with. Reading it is also how this
probe establishes that the previous instance carries the same latent defect.
"""
import json
from pathlib import Path
import sys

REPO = Path("/home/sl/src/baton")
sys.path.insert(0, str(REPO / "v12/python"))
sys.path.insert(0, str(REPO / "v12/python/src"))

PRIOR = Path("/home/sl/baton-v12-instance-2026-09-17T20-29-21Z/deployment.json")

# The two artefacts this Work built. They are DIFFERENT digests by
# construction: the second is built FROM the first and adds four modules.
PROVIDER = ("sha256:9ff3322f58f08275bfc4bb2cd511fb7a6b156e991449"
            "ee36f365d05e2133529d")
INTEGRATION = ("sha256:b9b75acc300170d99649d0497f9f93876ab5d8d73a91"
               "57c9861c5763f17c9561")


def _refusal(thunk):
    """Run it and answer the refusal text, or None if it was accepted."""
    from baton_v12.authority import core

    try:
        thunk()
    except core.Refusal as refused:
        return str(refused)
    except Exception as thrown:                      # pragma: no cover
        return f"{type(thrown).__name__}: {thrown}"
    return None


def main():
    from tools import single_worker

    prior = json.loads(PRIOR.read_text())
    by_role = {one["role"]: one["deployment"] for one in prior["workers"]}
    integration = by_role["integration"]

    found = {
        "schema": "baton.w202663.probe/1",
        "what": "can one Job's pool name two worker images",
        "read_only": True,
        "prior_instance": {
            "path": str(PRIOR),
            "note": "READ as evidence only; not started, changed or reused.",
            "implementation_image": by_role["implementation"]["image_digest"],
            "review_image": by_role["review"]["image_digest"],
            "integration_image": integration["image_digest"],
            "implementation_manifest_digest":
                by_role["implementation"]["input_manifest"]["manifest_digest"],
            "review_manifest_digest":
                by_role["review"]["input_manifest"]["manifest_digest"],
            "integration_manifest_digest":
                integration["input_manifest"]["manifest_digest"]},
    }
    found["prior_instance"]["two_images"] = (
        by_role["implementation"]["image_digest"]
        != integration["image_digest"])
    found["prior_instance"]["two_manifests"] = (
        by_role["implementation"]["input_manifest"]["manifest_digest"]
        != integration["input_manifest"]["manifest_digest"])

    # THE CONTROL. The document exactly as it was composed: its own image and
    # its own manifest agree, so rule 267 has nothing to say about it. If this
    # refuses for an unrelated reason the probe below proves nothing, which is
    # why it is asked first.
    control = _refusal(
        lambda: single_worker._held(dict(integration),
                                    roles=("integration",)))
    found["control_unchanged_document"] = control

    # THE PROBE. The SAME document with only the image moved to the one the
    # implementation and review workers would have to share. Nothing else
    # changes, so whatever comes back is about the image pairing alone.
    moved = dict(integration)
    moved["image_digest"] = by_role["implementation"]["image_digest"]
    found["probe_integration_worker_on_the_provider_image"] = _refusal(
        lambda: single_worker._held(moved, roles=("integration",)))

    # AND THE SAME QUESTION ON THIS WORK'S OWN TWO ARTEFACTS, so the answer is
    # about the images W202663 actually built rather than last night's.
    #
    # THE MANIFEST IS RESEALED, and it has to be. A first draft moved
    # `worker_image_digest` and left `manifest_digest` alone, so the document
    # refused one rule EARLIER -- "a manifest that does not identify itself is
    # not one" -- and proved nothing about the image pairing. The seal is
    # recomputed with the product's own canonical digest so that the only
    # remaining disagreement is the one under test.
    from baton_v12.contracts import canonical

    sealed = dict(integration["input_manifest"], worker_image_digest=PROVIDER)
    sealed.pop("manifest_digest")
    sealed["manifest_digest"] = canonical.digest(sealed)
    ours = dict(integration)
    ours["image_digest"] = INTEGRATION
    ours["input_manifest"] = sealed
    found["probe_w202663_pair"] = _refusal(
        lambda: single_worker._held(ours, roles=("integration",)))
    found["probe_w202663_pair_note"] = (
        "the integration worker on this Work's integration image, under the "
        "manifest the implementation and review workers would have to share "
        "(it names the provider image); the manifest is resealed so the only "
        "disagreement left is the image")

    found["the_second_rule_read_not_measured"] = {
        "where": "v12/python/tools/single_worker.py:1303",
        "text": "if job.get('input_digest') != manifest['manifest_digest']: "
                "_refuse('the Job names another bootstrap input')",
        "job_carries_one": "baton.v12.job-submission/2 gives a Job a single "
                           "input_digest and a list of stages",
        "already_measured_by": "W197661 compose_lifecycle.py R2 -- 'three "
                               "role-specific manifests produce three seals "
                               "of which the Job can name exactly one'"}
    print(json.dumps(found, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
