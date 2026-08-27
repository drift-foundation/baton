"""W6633 — build the reference worker image to ONE reproducible identity.

`work/records/2026/08/finding-v12-oci-reference-worker-image/`.

THE ACCEPTANCE NAMES AN IMMUTABLE IMAGE DIGEST, and `docker build` alone cannot
produce one. Fifth review [P1] refused a correction that redefined the artefact
as "equal layers plus selected config members", and it was right to: the OCI
image identity is the content digest of the image config, a manager pins and
launches that digest, and comparing a chosen subset of its inputs is not the
same claim.

WHAT IS ACTUALLY VOLATILE, MEASURED ON docker 29.1.3 WITH NO buildx. Two
`--no-cache` builds of the pinned recipe differ in FOUR places, and the record
this module corrects had only found one of them:

  1. `created` -- the wall clock at build time.
  2. `container` and `container_config` -- the classic builder's intermediate
     container id, a receipt for how the image was made.
  3. `config.Image` -- the parent chain id, the same kind of receipt.
  4. the recipe's OWN LAYERS. `COPY x /opt/baton/x` writes a tar carrying the
     directory entries it created, and their mtime is the build clock. The
     copied FILES keep their source mtime; the two directories do not.

  (4) is the one the previous correction reported as absent, having measured
  two builds that happened to start within the same wall-clock SECOND. It also
  explains the interaction that correction reported and could not attribute:
  the same-artefact case passes or fails depending on whether two builds land
  in one second, which is why it survived alone and failed in a full run.

SO THE BUILD HAS AN OUTPUT STEP. The engine builds; this normalizes the
volatile receipt metadata out of the result and loads it back, and the identity
of THAT image is what the manager pins. Two independent executions of the
recipe reach one digest.

WHAT IS NORMALIZED IS ONLY EVER THIS RECIPE'S OWN WORK, and the boundary is
derived from the pinned base rather than counted:

  a layer is this recipe's when its diff id is not one of the base image's;
  a history entry is this recipe's when it is newer than the base's `Created`.

So the base image's layers and its provenance travel through byte for byte. A
normalizer that rewrote them would be describing a different base from the one
the recipe pins, which is the property the digest pin exists to protect.

INSIDE THIS RECIPE'S LAYERS, EVERY MEMBER TIME IS NORMALIZED and nothing else
is. Bytes, mode, link target, ownership ids and member order are content and
survive; the mtime is a clock reading whatever member carries it.

SUPERSEDED 2026-08-26 (review [P1]): this said only DIRECTORY mtimes moved,
because a regular file's mtime "came out of the build context and is content".
The build context is a checkout and a checkout does not pin mtimes -- the
version-control source carries bytes and the executable bit and nothing about
when a working tree was populated -- so two fresh checkouts of one revision
produced two identities. The old text is kept here because the distinction it
drew (created by the copy versus supplied by the context) is the wrong one, and
the right one is what the SOURCE OF TRUTH pins.
"""

import hashlib
import io
import json
import pathlib
import shutil
import subprocess
import tarfile
import tempfile
import uuid

__all__ = ["EPOCH", "build_vector", "build_worker_image", "normalize_layout",
           "recipe_base", "staging_tag"]

# The one instant every normalized timestamp takes. Zero rather than
# `SOURCE_DATE_EPOCH`: this build has no upstream date to honour, and a
# constant is the value two independent runs agree on without arranging to.
EPOCH = 0
EPOCH_TEXT = "1970-01-01T00:00:00Z"

# The media type this module writes for a normalized layer. It writes
# UNCOMPRESSED tars, which is what the engine already saves, and it matters:
# for an uncompressed layer the blob digest and the `diff_id` are one value, so
# nothing here has to compress deterministically to be reproducible.
_LAYER_MEDIA = "application/vnd.oci.image.layer.v1.tar"


def _run(argv, timeout=900):
    finished = subprocess.run(argv, capture_output=True, timeout=timeout)
    if finished.returncode != 0:
        raise AssertionError(
            f"{' '.join(argv)} failed ({finished.returncode}): "
            f"{finished.stderr.decode('utf-8', 'replace')[:2000]}")
    return finished.stdout.decode("utf-8", "replace")


def staging_tag(tag):
    """Allocate the reference the un-normalized build exists under.

    UNIQUE PER INVOCATION. Review [P1]: this derived one mutable tag from the
    destination alone, so two simultaneous builds for the same destination
    staged over each other -- either could save the other's un-normalized
    image, and either `finally` could delete the tag before the other had
    saved it. That is the opposite of what this function's own docstring
    claimed, and the claim is what made it easy to miss.

    THE DESTINATION STAYS IN THE READABLE PREFIX, so a leftover stage says
    which artefact it was on its way to being, and the suffix is what makes it
    one invocation's own. It is ALLOCATED rather than derived: two calls
    answer two references, and a caller that needs the same one twice has to
    hold on to it -- which is exactly what `build_worker_image` now does.
    """
    return f"{tag}-unnormalized-{uuid.uuid4().hex[:12]}"


def build_vector(engine, context, dockerfile, stage, platform):
    """The engine argv for one execution of the recipe, into `stage`.

    A GOLDEN VECTOR, for the same reason the OCI adapter has them: the flags
    this build must carry are a decision, and a case that had to run a real
    daemon to read them would be a case nobody runs when the daemon is absent.

    IT TAKES THE STAGE RATHER THAN DERIVING IT, since review [P1] made the
    stage an allocation. A vector that allocated its own would name a
    reference its caller could not save, remove, or even read back.

    `--no-cache` is unconditional and not a keyword a caller may relax. Fourth
    review [P1]: the "independent" rebuild reused the builder cache, so equal
    identities proved cache reuse rather than two executions arriving at one
    artefact.
    """
    return [engine, "build", "--no-cache", "--platform", platform,
            "--tag", stage, "--file", str(dockerfile), str(context)]


def recipe_base(dockerfile):
    """The base reference the recipe pins, read from the recipe itself.

    One place names the base -- the `FROM` line -- and everything that needs to
    know reads it there. A second copy of the digest in this module would be a
    second thing to keep true.
    """
    text = pathlib.Path(dockerfile).read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("FROM "):
            return line[len("FROM "):].strip()
    raise AssertionError(f"{dockerfile} names no base image")


def _base_facts(engine, base):
    """What of a built image belongs to the BASE rather than to the recipe.

    Both answers come from the base image the recipe pins, so neither is a
    number this module remembers: a recipe that grew a layer or a metadata
    instruction tomorrow needs no change here.

    THE LAYERS COME BACK IN ORDER, AS A SEQUENCE. Review [P1]: this returned a
    `frozenset` and the normalizer called every diff id found in it a base
    layer -- but image ancestry is an ordered PREFIX, not set membership. A
    built layout carrying one of two claimed base layers and not the other was
    accepted, its remaining layers rewritten, and a digest returned as though
    the pinned base had been established. The engine reports them in order;
    keeping that order is the whole of the fix.
    """
    layers = json.loads(_run([engine, "image", "inspect", base, "--format",
                              "{{json .RootFS.Layers}}"], timeout=120))
    created = _run([engine, "image", "inspect", base, "--format",
                    "{{.Created}}"], timeout=120).strip()
    return tuple(layers), created


def _normalized_layer(path):
    """One layer tar, rewritten with fixed directory times and stable order.

    PAX rather than GNU format, because a tar's own header dialect is part of
    its bytes and the default has changed between Python versions; naming it
    means this module's output does not move when the interpreter does.
    """
    out = io.BytesIO()
    with tarfile.open(path) as source:
        members = sorted(source.getmembers(), key=lambda entry: entry.name)
        with tarfile.open(fileobj=out, mode="w",
                          format=tarfile.PAX_FORMAT) as target:
            for member in members:
                # THE COPY OF THE HEADER IS DELIBERATE. `getmembers` hands back
                # live objects and this rewrites two of their fields; mutating
                # the source's own would make a second pass over the same
                # archive see the first pass's answer.
                entry = tarfile.TarInfo(member.name)
                for field in ("mode", "uid", "gid", "size", "mtime", "type",
                              "linkname", "devmajor", "devminor"):
                    setattr(entry, field, getattr(member, field))
                # EVERY MEMBER TIME, not only the directories.
                #
                # Review [P1] SUPERSEDES the rule that used to be here, and
                # the superseded reasoning is worth keeping because it was
                # nearly right: a regular file's mtime "came out of the build
                # context and is content". The build context is a checkout,
                # and a checkout does not pin mtimes -- the version-control
                # source carries file bytes and the executable bit and nothing
                # about when a working tree was populated. So two fresh
                # checkouts of one revision present identical worker bytes
                # under different ambient clocks, and the identity this step
                # exists to produce depended on when somebody cloned.
                #
                # I drew the line between "the copy created it" and "the
                # context supplied it". The line that matters is what the
                # SOURCE OF TRUTH actually pins, and it pins neither.
                #
                # The real-engine case could not have caught this: it builds
                # twice from one context, so both builds see one set of source
                # mtimes.
                entry.mtime = EPOCH
                # The owner NAMES are a lookup in whatever passwd file the
                # builder had; the numeric ids above are the fact.
                entry.uname = entry.gname = ""
                entry.pax_headers = {}
                target.addfile(entry, source.extractfile(member)
                               if member.isreg() else None)
    return out.getvalue()


def _digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _blob(layout, digest):
    algorithm, value = digest.split(":")
    return layout / "blobs" / algorithm / value


def _write_blob(layout, data):
    digest = _digest(data)
    path = _blob(layout, digest)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return digest, len(data)


def _canonical(document):
    """This module's own bytes for a JSON document it authors.

    Sorted keys and no insignificant whitespace, for the reason every other
    canonical form in this distribution gives: two spellings of one document
    would be two digests, and a digest is the whole point here.
    """
    return json.dumps(document, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def normalize_layout(layout, base_layers, base_created, reference):
    """Rewrite a saved OCI layout in place and answer its new identity.

    Separated from the engine calls so the rule can be read -- and tested --
    without a daemon. Everything it needs about the base arrives as data.
    """
    layout = pathlib.Path(layout)
    index = json.loads((layout / "index.json").read_text(encoding="utf-8"))
    if len(index["manifests"]) != 1:
        raise AssertionError(
            f"a built image is one manifest; this layout carries "
            f"{len(index['manifests'])}, so there is no single identity to "
            f"normalize")
    described = index["manifests"][0]
    manifest = json.loads(_blob(layout, described["digest"])
                          .read_text(encoding="utf-8"))
    config = json.loads(_blob(layout, manifest["config"]["digest"])
                        .read_text(encoding="utf-8"))

    # ANCESTRY IS AN ORDERED PREFIX, NOT SET MEMBERSHIP, and this is decided
    # before anything is rewritten.
    #
    # Review [P1]: this asked whether each diff id was IN the base's set, so a
    # built layout carrying one of two claimed base layers and not the other
    # was accepted -- its remaining layers rewritten, and a digest returned as
    # though the pinned base had been established. An image descends from a
    # base by carrying that base's layers, in that base's order, at the front;
    # anything else is a different image that happens to share bytes.
    #
    # So the recipe's own layers are the SUFFIX, taken by position. That is
    # also stricter in a way set membership could never be: a recipe layer
    # whose digest happened to equal a base layer's is still the recipe's,
    # because of where it is.
    base = tuple(base_layers)
    diffs_now = config["rootfs"]["diff_ids"]
    if not base:
        raise AssertionError(
            "no layer of this build came from the pinned base; the base "
            "facts describe a different image from the one that was built")
    if tuple(diffs_now[:len(base)]) != base:
        raise AssertionError(
            f"this build does not begin with the pinned base's "
            f"{len(base)} layer(s) in the base's own order, so it did not "
            f"descend from the image the recipe pins; sharing some layers is "
            f"not ancestry")
    if len(diffs_now) <= len(base):
        raise AssertionError(
            "no layer of this build is the recipe's own; the pinned base "
            "already accounts for every layer, so there is nothing this "
            "recipe added and nothing to normalize")

    # THE LAYERS. A diff id the base already had travels untouched; anything
    # else is this recipe's own and is rewritten.
    layers, diffs = [], []
    for at, described_layer in enumerate(manifest["layers"]):
        diff = diffs_now[at]
        if at < len(base):
            layers.append(described_layer)
            diffs.append(diff)
            continue
        data = _normalized_layer(_blob(layout, described_layer["digest"]))
        digest, size = _write_blob(layout, data)
        layers.append({"mediaType": _LAYER_MEDIA, "digest": digest,
                       "size": size})
        diffs.append(digest)
    # THE CONFIG. Three receipts removed and every timestamp this build wrote
    # replaced by the one instant.
    config["created"] = EPOCH_TEXT
    config.pop("container", None)
    config.pop("container_config", None)
    config.get("config", {}).pop("Image", None)
    for entry in config["history"]:
        if entry.get("created", "") > base_created:
            entry["created"] = EPOCH_TEXT
    config["rootfs"]["diff_ids"] = diffs

    body = _canonical(config)
    config_digest, config_size = _write_blob(layout, body)
    manifest["config"] = {"mediaType": manifest["config"]["mediaType"],
                          "digest": config_digest, "size": config_size}
    manifest["layers"] = layers
    manifest_body = _canonical(manifest)
    manifest_digest, manifest_size = _write_blob(layout, manifest_body)
    index["manifests"] = [{
        "mediaType": described["mediaType"], "digest": manifest_digest,
        "size": manifest_size,
        "annotations": {"org.opencontainers.image.ref.name": reference}}]
    (layout / "index.json").write_text(
        _canonical(index).decode("utf-8"), encoding="utf-8")
    # THE LEGACY MANIFEST, because `docker load` still asks for one. It names
    # paths inside the archive rather than digests, so it is written from the
    # values just computed rather than kept in step by hand.
    (layout / "manifest.json").write_text(json.dumps([{
        "Config": "blobs/sha256/" + config_digest.split(":")[1],
        "RepoTags": [reference],
        "Layers": ["blobs/sha256/" + one["digest"].split(":")[1]
                   for one in layers]}]), encoding="utf-8")
    stale = layout / "repositories"
    if stale.exists():
        stale.unlink()
    return config_digest


# How much engine or exception prose reaches cleanup evidence. Bounded for the
# reason every diagnostic in this repository is: the text is an engine's, the
# destination is a log, and an unbounded operand makes the size of a durable
# line somebody else's decision.
MAX_CLEANUP_PROSE = 2000


def build_worker_image(engine, context, dockerfile, tag, platform):
    """Build the recipe and answer the ONE identity two builds agree on.

    The staging tag exists only between the build and the load, and it is
    removed on every path: an image nobody normalized is not the artefact, and
    leaving it would let a later reader pin the wrong one.
    """
    context = pathlib.Path(context)
    dockerfile = pathlib.Path(dockerfile)
    base = recipe_base(dockerfile)
    base_layers, base_created = _base_facts(engine, base)
    # ALLOCATED ONCE and threaded through build, save and cleanup. Nothing
    # below re-derives it, which is the whole of review [P1]'s correction:
    # two invocations for one destination now hold two references and neither
    # can save or delete the other's image.
    staging = staging_tag(tag)
    work = pathlib.Path(tempfile.mkdtemp(prefix="v12-worker-image-"))
    try:
        _run(build_vector(engine, context, dockerfile, staging, platform))
        _run([engine, "save", "--output", str(work / "built.tar"), staging])
        layout = work / "layout"
        layout.mkdir()
        _run(["tar", "xf", str(work / "built.tar"), "-C", str(layout)])
        identity = normalize_layout(layout, base_layers, base_created, tag)
        _run(["tar", "cf", str(work / "normalized.tar"), "-C", str(layout),
              "."])
        _run([engine, "load", "--input", str(work / "normalized.tar")])
    except BaseException as failure:
        # THE EARLIER FAILURE STAYS PRIMARY, and the cleanup becomes EVIDENCE
        # ATTACHED TO IT.
        #
        # Eighth review [P1]: the removal ran in `finally` and its result was
        # only inspected after the protected body succeeded, so on this path
        # the answer was discarded while the exception unwound -- the
        # "cleanup evidence in the log" the comment promised did not exist.
        # And a removal that RAISED replaced the build failure outright, which
        # is the worse half: an operator reading a timeout has no idea the
        # build failed first.
        #
        # `add_note` is exactly the shape this needs. The primary exception is
        # the one that propagates, and the cleanup outcome travels with it
        # rather than instead of it.
        trouble = _cleaned_up(engine, staging, work)
        if trouble is not None:
            failure.add_note(trouble)
        raise
    trouble = _cleaned_up(engine, staging, work)
    if trouble is not None:
        # NO EARLIER FAILURE, so this one is the primary. A run that built,
        # saved, normalized and loaded and then could not clean up is a run
        # whose success would otherwise be a lie: the mutable un-normalized
        # image is still under a readable staging tag, and an operator can
        # mistake it for build output.
        raise AssertionError(trouble)
    return identity


def _cleaned_up(engine, staging, work):
    """Remove the staging image and the scratch tree; answer what went wrong.

    ANSWERS RATHER THAN RAISES, because its caller has to decide whether this
    is the primary failure or evidence attached to one. A helper that raised
    could only ever be the primary, which is the defect it exists to correct.

    THE SCRATCH TREE GOES WHATEVER HAPPENS. It carries no evidence anybody can
    act on -- an extracted layer tarball in a temporary directory -- and
    leaving it behind on an engine's bad day would turn one failure into a
    disk that fills.
    """
    try:
        removed = subprocess.run([engine, "image", "rm", "--force", staging],
                                 capture_output=True, timeout=120)
        if removed.returncode == 0:
            return None
        detail = removed.stderr.decode("utf-8", "replace")[:MAX_CLEANUP_PROSE]
        return (f"{engine} refused to remove the staging image {staging}: "
                f"{detail}; the un-normalized image is still here and an "
                f"operator can mistake it for build output")
    except Exception as thrown:
        # A CLEANUP THAT COULD NOT RUN IS THE SAME KIND OF FACT as one that
        # ran and refused: the staging image may still be there, and the
        # operator needs to know which engine and which tag to look at.
        # Bounded like every other diagnostic, because a subprocess exception
        # can carry an engine's whole output.
        return (f"{engine} could not be asked to remove the staging image "
                f"{staging}: "
                f"{type(thrown).__name__}: {str(thrown)[:MAX_CLEANUP_PROSE]}; "
                f"the un-normalized image may still be here")
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _main(argv):
    """Build the worker image and print the one digest to pin.

    An operator has to be able to produce the artefact the manager will
    launch, and a build path that only a test module knows how to drive is one
    they cannot. The default platform is asked of the ENGINE rather than
    assumed, for the reason the daemon gate gives: the same recipe on two
    architectures is two artefacts.
    """
    import argparse

    here = pathlib.Path(__file__).resolve().parents[2] / "worker"
    parser = argparse.ArgumentParser(
        prog="worker_image",
        description="Build the v12 reference worker image reproducibly.")
    parser.add_argument("--engine", default="docker")
    parser.add_argument("--context", default=str(here))
    parser.add_argument("--dockerfile", default=str(here / "Dockerfile"))
    parser.add_argument("--tag", required=True)
    parser.add_argument("--platform", default=None)
    taken = parser.parse_args(argv)
    platform = taken.platform or _run(
        [taken.engine, "version", "--format",
         "{{.Server.Os}}/{{.Server.Arch}}"], timeout=120).strip()
    print(build_worker_image(taken.engine, taken.context, taken.dockerfile,
                             taken.tag, platform))
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(_main(sys.argv[1:]))
