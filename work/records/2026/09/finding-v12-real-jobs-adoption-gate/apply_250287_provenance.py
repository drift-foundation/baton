"""Claim-250287: the diagnostic resolves PRODUCTION from the selected snapshot.

Review 2026-09-23T19:04:38Z: "Import behavior now avoids caller cwd dependence
but is NOT pinned to the selected manager snapshot... production tools/baton_v12
must resolve to the selected snapshot. Record actual module __file__
values/digests. This distinction has been the review requirement, not merely
making imports work from several directories."

What I did last claim was make the imports work from anywhere -- which is a
different property, and I answered the wrong requirement with it. The snapshot
holds `baton_v12` and `tools` and NOTHING else, so the fixture package `tests`
must still come from the checkout; that is the only thing the checkout may
supply, and it is put on the path AFTER the snapshot so it can never win a
production name.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "diagnostic_main_admissions.py"

OLD = '''HERE = os.path.dirname(os.path.abspath(__file__))
# THE IMPORT PATH IS PINNED HERE, not left to the caller's cwd. Review
# 2026-09-23T19:01:02Z: three runs I reported as "2/0 held" were entirely
# `ModuleNotFoundError: tests` -- they never reached a lifecycle at all, and I
# read their absence of a success as a contradicting result. That was my
# error, and the cause was running from the dossier instead of the
# distribution. This module now binds both itself and the distribution, so it
# runs identically from any directory.
CHECKOUT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(HERE)))))
DISTRIBUTION = os.path.join(CHECKOUT, "v12", "python")
for one in (HERE, DISTRIBUTION, os.path.join(DISTRIBUTION, "src")):
    if one not in sys.path:                                  # pragma: no cover
        sys.path.insert(0, one)
'''

NEW = '''HERE = os.path.dirname(os.path.abspath(__file__))
# PRODUCTION RESOLVES TO THE SELECTED SNAPSHOT. Review 2026-09-23T19:04:38Z:
# what I pinned last claim was cwd independence, and the requirement is
# PROVENANCE -- `baton_v12` and `tools` must be the bytes ASSESSMENT-249338.md
# selected, not the checkout's. Cwd independence is a consequence here, not
# the point.
#
# The snapshot holds `baton_v12` and `tools` and nothing else, so the fixture
# package `tests` must come from the checkout. That is the ONLY thing the
# checkout supplies, and it sits AFTER the snapshot on the path so it can
# never win a production name.
SNAPSHOT = "/home/sl/baton-runs/independent-review-247947/manager-source"
CHECKOUT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(HERE)))))
DISTRIBUTION = os.path.join(CHECKOUT, "v12", "python")
if not os.path.isdir(os.path.join(SNAPSHOT, "baton_v12")):
    raise SystemExit(
        f"REFUSED: the selected manager snapshot is not at {SNAPSHOT}; "
        f"a diagnostic that silently falls back to the checkout measures "
        f"different bytes than the ones this gate pinned")
for one in (DISTRIBUTION, HERE, SNAPSHOT):
    while one in sys.path:                                   # pragma: no cover
        sys.path.remove(one)
    sys.path.insert(0, one)


def provenance():
    """Where each module this run depends on ACTUALLY came from.

    Printed with the receipt, because "it imported" and "it imported the
    selected bytes" are different claims and only one of them is the
    requirement.
    """
    import hashlib
    held = {}
    for name in sorted(sys.modules):
        if name.split(".")[0] not in ("baton_v12", "tools", "tests"):
            continue
        place = getattr(sys.modules[name], "__file__", None)
        if not place:
            continue
        under = ("snapshot" if os.path.realpath(place).startswith(
                     os.path.realpath(SNAPSHOT) + os.sep)
                 else "checkout" if os.path.realpath(place).startswith(
                     os.path.realpath(CHECKOUT) + os.sep)
                 else "elsewhere")
        with open(place, "rb") as handle:
            digest = hashlib.sha256(handle.read()).hexdigest()
        held[name] = {"file": place, "from": under, "sha256": digest}
    misplaced = sorted(name for name, one in held.items()
                       if name.split(".")[0] in ("baton_v12", "tools")
                       and one["from"] != "snapshot")
    return {"modules": held, "production_not_from_snapshot": misplaced}
'''

OLD_PRINT = '''        print(json.dumps({
            "launch_homes": homes,'''

NEW_PRINT = '''        print(json.dumps({
            "provenance": provenance(),
            "launch_homes": homes,'''


def swap(body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times, not once")
    return body.replace(old, new, 1)


def main():
    body = PLACE.read_text(encoding="utf-8")
    body = swap(body, OLD, NEW, "the import block")
    body = swap(body, OLD_PRINT, NEW_PRINT, "the receipt")
    PLACE.write_text(body, encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    for absent in ('os.path.join(DISTRIBUTION, "src")',):
        if absent in written:
            raise SystemExit(f"REFUSED: {absent!r} survives in the file")
    for present in ("SNAPSHOT =", "def provenance():",
                    "production_not_from_snapshot",
                    '"provenance": provenance(),'):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    compile(written, str(PLACE), "exec")
    print("production imports pinned to the snapshot, and verified on disk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
