"""Every path either supported recipe COPIES, checkout-side and image-side.

W202663 step 3a, answering review206578: "Provenance confirms the eight
enumerated file digests; it does NOT enumerate the source_profiles directory
copied by both recipes. Before final selection, record all copied input
paths/digests and retain image-side comparison evidence for them, including
source_profiles."

WHAT IT DOES. Reads each recipe's own `COPY` instructions rather than a list
written here -- a recipe that gains a path cannot leave this record describing
the old set -- expands each to the files it actually carries, digests them in
the checkout, digests the same paths inside a container run from the built
artefact, and compares.

WHAT IT IS NOT, narrowed after review207195. It is not prospective input
attestation, and it is not evidence that nothing ever moved since the build
either -- that was my wording and it claimed more than a comparison can. What
this establishes is EQUALITY AT OBSERVATION TIME: the bytes in the checkout and
the bytes in the artefact agree at the instant this ran. A file that changed
after the build and changed back would satisfy it. W197661's record names the
same gap; closing it needs a snapshot taken BEFORE a build, and the next build
of either recipe should take one rather than reconstructing it afterwards.

READ-ONLY. It runs one container per image with no network and no mounts, and
it builds nothing.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

CONTEXT = Path("/home/sl/src/baton/v12")
RECIPES = {
    "provider": (CONTEXT / "worker/Dockerfile.claude",
                 "sha256:9ff3322f58f08275bfc4bb2cd511fb7a6b156e99"
                 "1449ee36f365d05e2133529d"),
    "integration": (CONTEXT / "worker/Dockerfile.integration",
                    "sha256:b9b75acc300170d99649d0497f9f93876ab5d8d7"
                    "3a9157c9861c5763f17c9561"),
}

# `COPY <source>... <destination>`, with the line continuations both recipes
# use. Nothing here interprets flags: neither recipe carries one, and a recipe
# that grew a `--from` would be a different question this must not answer
# silently -- so it is refused instead.
_COPY = re.compile(r"^COPY\s+(.*)$")


def copies(recipe):
    """The (source, destination) pairs this recipe actually declares."""
    text = recipe.read_text(encoding="utf-8")
    joined, pending = [], ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        pending += " " + stripped
        if stripped.endswith("\\"):
            pending = pending[:-1]
            continue
        joined.append(pending.strip())
        pending = ""
    found = []
    for statement in joined:
        matched = _COPY.match(statement)
        if matched is None:
            continue
        words = matched.group(1).split()
        if any(word.startswith("--") for word in words):
            raise SystemExit(f"{recipe}: a COPY carries a flag this record "
                             f"does not interpret: {statement!r}")
        found.append((words[:-1], words[-1]))
    return found


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checkout_side(recipe):
    """Every FILE the recipe copies, expanded, digested in this checkout."""
    held = {}
    for sources, destination in copies(recipe):
        for source in sources:
            place = CONTEXT / source
            if place.is_dir():
                # A DIRECTORY COPY LANDS ITS CONTENTS AT THE DESTINATION, so
                # the image-side path of each file is destination/<relative>.
                # `__pycache__` is excluded by `.dockerignore` and is excluded
                # here for the same reason rather than by coincidence.
                for one in sorted(place.rglob("*")):
                    if not one.is_file() or "__pycache__" in one.parts:
                        continue
                    inside = one.relative_to(place)
                    held[f"{destination}/{inside}"] = {
                        "checkout": str(one.relative_to(CONTEXT.parent)),
                        "sha256": _digest(one)}
            else:
                # A MULTI-SOURCE COPY lands each file INSIDE the destination
                # directory; a single-source one lands AT the destination.
                where = (destination if len(sources) == 1
                         else f"{destination.rstrip('/')}/{place.name}")
                held[where] = {
                    "checkout": str(place.relative_to(CONTEXT.parent)),
                    "sha256": _digest(place)}
    return held


def image_side(image, paths):
    """The same paths, digested INSIDE a container run from the artefact."""
    script = "sha256sum " + " ".join(f"'{one}'" for one in sorted(paths))
    answered = subprocess.run(
        ["docker", "run", "--rm", "--network", "none", "--entrypoint", "sh",
         image, "-c", script],
        capture_output=True, timeout=300)
    if answered.returncode != 0:
        raise SystemExit(f"{image}: {answered.stderr.decode()[:2000]}")
    held = {}
    for line in answered.stdout.decode().splitlines():
        digest, _, where = line.partition(" ")
        held[where.strip()] = digest.strip()
    return held


def main():
    report = {"schema": "baton.w202663.copied-inputs/1",
              "claim": 207111,
              "what": "every path both supported recipes COPY, checkout-side "
                      "and image-side",
              "limitation": "EQUALITY AT OBSERVATION TIME and nothing more: "
                            "the checkout bytes and the artefact bytes agree "
                            "at the instant this ran. It is not prospective "
                            "input attestation, and it is not evidence that "
                            "nothing ever moved since the build -- a file "
                            "changed after the build and changed back would "
                            "satisfy it.",
              "images": {}}
    ok = True
    for name, (recipe, image) in RECIPES.items():
        declared = checkout_side(recipe)
        inside = image_side(image, declared)
        entries, equal = {}, True
        for where in sorted(declared):
            found = inside.get(where)
            agrees = found == declared[where]["sha256"]
            equal = equal and agrees
            entries[where] = {"checkout_path": declared[where]["checkout"],
                              "checkout_sha256": declared[where]["sha256"],
                              "image_sha256": found, "equal": agrees}
        ok = ok and equal
        report["images"][name] = {
            "recipe": str(recipe.relative_to(CONTEXT.parent)),
            "image_digest": image,
            "copied_paths": len(entries),
            "all_equal": equal,
            "entries": entries}
    report["all_equal"] = ok
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
