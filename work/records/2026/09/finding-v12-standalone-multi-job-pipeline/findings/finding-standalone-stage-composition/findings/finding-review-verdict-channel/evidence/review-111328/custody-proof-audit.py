"""Inspect the claimed joined proof through public custody views; no live runtime."""
import json,sys
from pathlib import Path
root=next(p for p in Path(__file__).resolve().parents if (p/"v12/python/src").is_dir())
sys.path[:0]=[str(root/"v12/python/src"),str(root/"v12/python")]
from tests.job_manager import test_review_driver as t
from baton_v12.worker_manager import intake_receipt_of,retentions_of,load_manifest,frozen_output_of
c=t.TheFirstVerdictGoesThroughTheOrderedEnding(); c.setUp()
try:
 h=c.reviewed(record=False)
 before=c.verdicts(h)
 answer,steps,adapter=c.ending(h)
 retained=load_manifest(c.control,h["result_digest"],"resultManifest")
 vector=t._result_vector()
 out={"scope":"existing isolated fixture with its _frozen_endings substitutions; not a production failure", "verdicts_before":before,"verdicts_after":c.verdicts(h),"outcome":answer["outcome"],"reported_cleaned_up":answer["cleaned_up"],"reported_receipt_digest":answer["receipt_digest"],"actual_intake_receipt":intake_receipt_of(c.control,h["attempt_id"]),"actual_retentions":retentions_of(c.control,h["attempt_id"]),"steps":steps,"terminal_is_unchanged_published_vector_completion":h["terminal"]["manifest_digest"]==vector["completion_manifest_digest"]}
finally:c.doCleanups()
Path(__file__).with_suffix(".json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps(out,indent=2))
