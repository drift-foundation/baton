"""Read-only checks of current old gates and inert proposed shape; no qualification."""
from pathlib import Path
import sys,json,time,hashlib
started=time.monotonic()
root=next(p for p in Path(__file__).resolve().parents if (p/"v12/justfile").exists())
sys.path[:0]=[str(root/"v12/python"),str(root/"v12/python/src")]
from tools import bootstrap,instance
from baton_v12.contracts import digest
assert bootstrap.SCHEMA=="baton.v12.stack-bootstrap/1"
assert any("schema" in x for x in bootstrap._missing({"schema":"baton.v12.stack-bootstrap/2"}))
assert "exchange_qualification" in bootstrap._unknown({"exchange_qualification":{}})
assert instance.malformed({"schema":"baton.v12.stack-instance/2"},"synthetic.json") is not None
here=Path(__file__).parent
qualification=json.loads((here/"QUALIFICATION.synthetic.json").read_text())
evidence=json.loads((here/"EVIDENCE.synthetic.json").read_text())
assert qualification["evidence_digest"]==digest(evidence)
assert qualification["workers"]==evidence["workers"]
assert qualification["host_runtime_digest"]==evidence["host_runtime_digest"]
assert set(qualification)=={"schema","host_runtime_digest","workers","evidence_digest"}
assert len(evidence["checks"])==7
print(json.dumps({"kind":"read-only-old-gates-and-synthetic-shape","assertions":9,"seconds":time.monotonic()-started,"product_qualification":False,"provider_calls":0,"engine_calls":0}))
