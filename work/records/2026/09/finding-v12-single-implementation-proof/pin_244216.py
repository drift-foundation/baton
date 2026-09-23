"""Record the SELECTION before execution. Owner reroute 244214."""
import hashlib
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[4]

ACCEPTED_ADAPTER = (
    "18c34ff52faa150237df0c8d0206b805801ee71cb9e7a4ec6e84e4379d7f9d8d")
PRESERVED_IMAGE = "baton-v12-claude-worker:w236087-236349"
PRESERVED_DIGEST = (
    "sha256:2e9e84ff23319778760d5b22c70d543d4290931510a3ab3ecf40bcdaad7456bd")
NEW_REFERENCE = "baton-v12-claude-worker:w239528-244216"

FINDING = """
## 2026-09-23 -- OWNER: build the corrected worker image, bind it, prepare the packet

Owner reroute 244214, recorded here BEFORE execution as it requires:

    "Owner selects corrected worker-image build and successor packet
     preparation using source accepted in review-2026-09-23T03-19-21Z.md.
     Record selection before execution. Preserve existing images, consumed
     instances and evidence; build a distinct image, verify accepted adapter
     bytes, bind actual image and worker digests, and provide exact bounded
     commands retaining 180/300/60 limits. Coordinate with tuner W244180
     without overlapping files."

### What is selected

A DISTINCT image, `%(reference)s`, built from the accepted source. The existing
`%(preserved)s` at `%(preserved_digest)s` is PRESERVED and is not retagged,
rebuilt or removed: it is what every earlier packet in this campaign is bound
to, and W236087's own packet still names it.

The adapter bytes that must be in it are the ones independent review accepted
at 2026-09-23T03:19:21Z: `v12/worker/claude_agent.py`
`%(adapter)s`, carrying `PROVIDER_UMASK = 0o077`. The build VERIFIES that
digest inside the built artefact rather than trusting the build context, for
the reason the recipe already gives about itself: "a recipe naming a suite and
an image carrying an interpreter are two facts and only the second one runs."

### What the image does and does not settle

It makes a live run POSSIBLE on the corrected adapter. It does not make one
authorized, and it does not establish the CLI's behaviour under the new mask --
review 2026-09-23T03:19:21Z is explicit that the retained `0o755` modes are
consistent with umask creation but do not exclude an explicit `chmod` or a
reset mask, and only a real turn under this image can answer that. The packet
says so.

### Coordination with W244180

The tuner's Work is bound to `work/records/2026/09/finding-v12-review-job-
preparation/` and is preparing the operator recipe for the REVIEWER Job
W239533. It was `active` and working when this claim began. There is no file
overlap: that dossier is its own, this one is W239528's, and the product paths
below are pinned here. Nothing in this claim touches its dossier or W239533.

### The recipe is not reproducible, and that is measured rather than assumed

`Dockerfile.claude` records it: two builds of an unchanged tree produced
different digests, identical in the base and `COPY` layers and differing only
in `npm install` and `apt-get install`, because the `FROM` is a tag, apt takes
what the mirror serves and the pinned provider runs a `postinstall` that
fetches a native binary. So the ARTEFACT is selected by digest, not by recipe,
and the packet binds the digest this build actually produced.
"""

PLAN = """# Current action -- the corrected worker image and its packet

## Active -- claim 244216, baton.claude

Owner reroute 244214. The selection is recorded in FINDING before execution, as
that reroute requires.

## PINNED -- before any edit or build

Accepted adapter source, from review 2026-09-23T03:19:21Z:

    v12/worker/claude_agent.py
        %(adapter)s

PRESERVED and not touched:

    %(preserved)s
        %(preserved_digest)s
    every consumed instance under /home/sl/baton-runs/
    both manager-source snapshots and their manifests

The new artefact is DISTINCT: `%(reference)s`.

## Steps

1. Record the selection and this pin. (done -- `pin_244216.py`)
2. Build the distinct image from the accepted source.
3. VERIFY the accepted adapter digest inside the built artefact, and record the
   image's own config digest and worker-file digests.
4. Bind the actual image reference, config digest and worker digests into a
   successor packet; retain 180/300/60.
5. Exact bounded commands; independent review.

## Not in scope

Any live provider execution. Retagging, rebuilding or removing the preserved
image. Any recovery, reviewer stage, resume or closure. Anything in W244180's
dossier or in W239533.

---

"""


def sha(path):
    reading = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            reading.update(block)
    return reading.hexdigest()


def main():
    found = sha(ROOT / "v12/worker/claude_agent.py")
    if found != ACCEPTED_ADAPTER:
        raise SystemExit(
            f"the working tree's claude_agent.py is {found} and independent "
            f"review accepted {ACCEPTED_ADAPTER}; the selection is for the "
            f"ACCEPTED source and this build must not proceed over anything "
            f"else")
    values = {"adapter": ACCEPTED_ADAPTER, "preserved": PRESERVED_IMAGE,
              "preserved_digest": PRESERVED_DIGEST,
              "reference": NEW_REFERENCE}
    finding = HERE / "FINDING.md"
    if "build the corrected worker image" not in \
            finding.read_text(encoding="utf-8"):
        finding.write_text(
            finding.read_text(encoding="utf-8").rstrip("\n") + "\n"
            + (FINDING % values), encoding="utf-8")
    plan = HERE / "PLAN.md"
    body = plan.read_text(encoding="utf-8")
    if "claim 244216" not in body:
        head = body.split("\n", 1)[0]
        plan.write_text((PLAN % values) + body.replace(
            head, "# Historical action" + head.split("action", 1)[-1], 1),
            encoding="utf-8")
    print(f"accepted adapter verified in the tree: {found}")
    print("selection recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
