import hashlib
import json
import time
import traceback
from pathlib import Path

start = time.monotonic()
evidence = Path(__file__).resolve().parent
report = {}
try:
    from tests.manager import test_boundary_inventory as b
    accepted = json.loads((evidence.parents[1] / "finding-consumption-subject-coverage/evidence/final-verification-121130.json").read_text())
    hashes = dict(accepted["runtime_hashes"], **{str(Path(b.__file__).relative_to(Path.cwd())): accepted["candidate_sha256"]})
    for name, sha in hashes.items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha, name
    report["hashes"] = hashes
    entries = b.receiving_entries()
    records = b.boundary_occurrences()
    claims = b._boundary_claims(records, entries, b.DELEGATED)
    resolved, residual = b._account_boundary_calls(records, claims, b.NOT_AN_ENTRY)
    wanted = sorted(r for r in residual if r.site.startswith("review_cycles.py:"))
    groups = []
    for call in sorted({r.call for r in wanted}):
        groups.append({"call": call, "instances": [{"occurrence": r._asdict(), "claims": sorted(claims.get(r, ())), "resolved_to": [one._asdict() for one in sorted(resolved.get(r, ()))], "residual": r in residual} for r in sorted(records) if r.call == call]})
    owner = b.EveryReceivingEntryHasOneOwner()
    report.update(entries=len(entries), occurrences=len(records), residual_occurrences=len(residual), module_residual_occurrences=len(wanted), module_residual_triples=sorted({(r.site, r.kind, r.label) for r in wanted}), groups=groups, module_entries=[{"entry": entry, "owner": owner.owner_of(entry), "claims": [r._asdict() for r in records if entry in claims.get(r, ())]} for entry in sorted(entries) if entry[1].startswith("review_cycles.py:")])
    print(json.dumps({"module_residual_occurrences": len(wanted), "groups": groups}, indent=2))
except BaseException:
    report["error"] = traceback.format_exc()
    raise
finally:
    report["seconds"] = time.monotonic() - start
    with (evidence / "trace-121208.json").open("x") as out:
        json.dump(report, out, indent=2)
    print("Elapsed:", report["seconds"])
