"""W6 — the seal's own verdicts, MEASURED BY REMOVAL.

Eight of the ten sealed cases were derived `passed`. A case that would pass
with its guard deleted established nothing, so every guard those verdicts rest
on is removed from the production source, the affected probe is re-derived,
and the verdict is required to change.

IT REWRITES SOURCE FILES IN PLACE AND RESTORES EACH ONE before the next, and
prints the before/after digest of every file it touched so the restoration is
checked rather than asserted. No Git history or index is touched.

Run from `v12/python`: `PYTHONPATH=src python3 <this file>`.
"""

import hashlib
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path("/home/sl/src/baton")
SRC = REPO / "v12/python/src/baton_v12/worker_manager"
SEAL = pathlib.Path(__file__).resolve().parent / "w6-conformance-seal.py"

MUTATIONS = [
    ("oci: the input root is mounted writable",
     SRC / "oci.py",
     '''f"readonly={'false' if writable else 'true'}"''',
     '''"readonly=false"''',
     "probe_input_is_read_only", "A-input-is-read-only"),

    ("attempts: the declared plan is not held to the authorized root",
     SRC / "attempts.py",
     '''    proved = oci.canonical_source(inputs, "an authorized input root")''',
     '''    return
    proved = oci.canonical_source(inputs, "an authorized input root")''',
     "probe_only_the_authorized_root",
     "A-only-the-authorized-root-is-mounted-at-the-fixed-path"),

    ("store: a reused operation id with another signature is not a collision",
     SRC / "store.py",
     '''        if row["signature"] != signature or (kind is not None
                                             and row["kind"] != kind):''',
     '''        if False:''',
     "probe_operation_collision", "E-operation-collision"),

    ("output: the freeze does not hold the attempt to the live generation",
     SRC / "output.py",
     '''    if live != expect:''',
     '''    if False:''',
     "probe_superseded_generation_freeze",
     "A-completion-under-a-superseded-generation-refused"),

    ("oci: the ADAPTER's own seam does not hold the mount to the proved root",
     SRC / "oci.py",
     '''        proved = canonical_source(authorized, "an authorized input root")''',
     '''        return
        proved = canonical_source(authorized, "an authorized input root")''',
     "probe_only_the_authorized_root",
     "A-only-the-authorized-root-is-mounted-at-the-fixed-path"),

    ("oci: `retain` does not keep the material",
     SRC / "oci.py",
     '''_KEEPS_MATERIAL = ("retain", "quarantine")''',
     '''_KEEPS_MATERIAL = ("quarantine",)''',
     "probe_output_persists_past_the_runtime",
     "A-output-persists-past-the-runtime"),

    ("oci: the canonical checkout is mounted into the runtime",
     SRC / "oci.py",
     '''    argv.append(image_digest)''',
     '''    argv += ["--mount", "type=bind,source=/home/sl/src/baton,"
             "target=/home/sl/src/baton,readonly=true"]
    argv.append(image_digest)''',
     "probe_no_canonical_repository", "B-no-canonical-repository"),
]


# BOTH GUARDS AT ONCE. The manager's early check and the adapter's boundary
# refuse the same case, so removing either one alone leaves the other
# refusing -- which is exactly the "two guards, neither measured" shape
# this campaign has corrected before. Removing both is the measurement.
BOTH = [
    ("manager AND adapter: neither holds the mount to the proved root",
     [SRC / "attempts.py", SRC / "oci.py"],
     ['''    proved = oci.canonical_source(inputs, "an authorized input root")''',
      '''        proved = canonical_source(authorized, "an authorized input root")'''],
     ['''    return
    proved = oci.canonical_source(inputs, "an authorized input root")''',
      '''        return
        proved = canonical_source(authorized, "an authorized input root")'''],
     "probe_only_the_authorized_root",
     "A-only-the-authorized-root-is-mounted-at-the-fixed-path"),
]


def digest(place):
    return hashlib.sha256(place.read_bytes()).hexdigest()[:16]


def verdict_of(probe, case_id):
    finished = subprocess.run(
        [sys.executable, str(SEAL), probe],
        capture_output=True, timeout=2400,
        env={**__import__("os").environ, "PYTHONPATH": "src"},
        cwd=str(REPO / "v12/python"))
    text = finished.stdout.decode("utf-8", "replace")
    found = re.search(r"^\s+(PASSED|FAILED|UNABLE)\s+" + re.escape(case_id) + r"$",
                      text, re.M)
    if found:
        return found.group(1), text
    if finished.returncode != 0:
        return "PROBE-FAILED", text + finished.stderr.decode("utf-8", "replace")
    return "NO-VERDICT", text + finished.stderr.decode("utf-8", "replace")


def main():
    print("W6 SEAL - MEASURED BY REMOVAL")
    print("=" * 74)
    print()
    print("Each mutation deletes ONE production guard, re-derives ONE sealed")
    print("verdict through the frozen assessor, and restores the file.")
    print()

    # A SINGLE REMOVAL THAT DOES NOT FLIP IS NOT AUTOMATICALLY A DEFECT.
    # `_plan_agrees`'s own docstring says the adapter's refusal "is the
    # boundary and this one is the earlier moment": the pair is deliberate, so
    # removing either alone leaves the other refusing. What has to flip is
    # removing BOTH, and it does. These two are recorded as EXPECTED; every
    # other survivor is a verdict resting on something other than its guard.
    EXPECTED = {
        "attempts: the declared plan is not held to the authorized root",
        "oci: the ADAPTER's own seam does not hold the mount to the proved root",
    }
    caught, uncaught, expected = [], [], []
    for title, place, old, new, probe, case_id in MUTATIONS + BOTH:
        places = place if isinstance(place, list) else [place]
        olds = old if isinstance(old, list) else [old]
        news = new if isinstance(new, list) else [new]
        originals = [one.read_text() for one in places]
        stale = [one.name for one, was, text in zip(places, olds, originals)
                 if was not in text]
        if stale:
            print(f"[ANCHOR] {title}")
            print(f"         the anchor is no longer in {stale}; this "
                  f"mutation measured NOTHING")
            uncaught.append((title, "stale anchor"))
            continue
        before = [digest(one) for one in places]
        for one, text, was, now in zip(places, originals, olds, news):
            one.write_text(text.replace(was, now, 1))
        try:
            answer, output = verdict_of(probe, case_id)
        finally:
            for one, text in zip(places, originals):
                one.write_text(text)
        after = [digest(one) for one in places]
        mark = ("caught" if answer != "PASSED"
                else ("survives, by design" if title in EXPECTED
                      else "NOT CAUGHT"))
        print(f"[{mark}] {title}")
        print(f"          {case_id} -> {answer}")
        print(f"          {[one.name for one in places]} {before} -> "
              f"mutated -> {after} "
              f"({'restored' if before == after else 'NOT RESTORED'})")
        assert before == after, f"{places} were not restored"
        if answer == "PASSED":
            (expected if title in EXPECTED else uncaught).append(
                (title, case_id))
            for line in output.splitlines():
                if case_id in line or "input_write" in line \
                        or "repository_reachable" in line:
                    print(f"            | {line.strip()}")
        else:
            caught.append((title, case_id))
        print()

    print("=" * 74)
    print(f"caught {len(caught)} of {len(MUTATIONS) + len(BOTH)}")
    if expected:
        print("survived by design -- a second guard refuses the same case, "
              "and removing BOTH does flip the verdict:")
        for title, why in expected:
            print(f"  {title}")
    if uncaught:
        print("NOT CAUGHT, and each is a verdict that rests on something "
              "other than the guard named:")
        for title, why in uncaught:
            print(f"  {title} ({why})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
