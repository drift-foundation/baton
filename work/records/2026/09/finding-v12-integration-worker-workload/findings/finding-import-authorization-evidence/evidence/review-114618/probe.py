"""Probe the next frozen-result binding, with real producer output as base."""
import copy
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[8]
sys.path[:0] = [str(REPO / 'v12/python'), str(REPO / 'v12/python/src')]
from tests.tools import test_integration_bundle as fixture
from baton_v12.contracts import digest
from baton_v12.contracts.canonical import canonical_bytes


def run_case(mode):
    case = fixture.ProducerCase('run')
    case.setUp()
    try:
        produced = case.compose()
        source = Path(produced['root'])
        root = Path(case.world.owner.root) / ('review114618-' + mode)
        for path in source.rglob('*'):
            if path.is_file():
                dest = root / path.relative_to(source)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(path.read_bytes())
        authority = json.loads((root / 'evidence/authority.json').read_bytes())
        review = json.loads((root / 'evidence/review.json').read_bytes())
        original_result = copy.deepcopy(review['review_result'])
        original_digest = review['review_result_digest']
        if mode == 'rewritten_output':
            output = authority['review']['documents'][0]
            entry = output['files'][0]
            previous = entry['bytes']
            payload = b'REVIEW114618 invented permission under the original result identity\n'
            entry.update(text=payload.decode(), bytes=len(payload), digest=hashlib.sha256(payload).hexdigest())
            output['bytes'] += len(payload) - previous
            output['tree_digest'] = digest([{'path': f['path'], 'bytes': f['bytes'], 'content_digest': 'sha256:' + f['digest']} for f in output['files']])
            artifact = next(a for a in review['review_result']['artifacts'] if a['output_name'] == output['output_name'])
            artifact.update(content_digest=output['tree_digest'], bytes=output['bytes'])
        elif mode == 'removed_outputs':
            authority['review']['documents'] = []
            review['review_result']['artifacts'] = []
        elif mode != 'control':
            raise ValueError(mode)
        envelope = json.loads((root / 'integration.json').read_bytes())
        for name, document in [('authority.json', authority), ('review.json', review)]:
            payload = canonical_bytes(document)
            (root / 'evidence' / name).write_bytes(payload)
            ref = next(r for r in envelope['evidence'] if r['name'] == name)
            ref.update(bytes=len(payload), digest=hashlib.sha256(payload).hexdigest())
        (root / 'integration.json').write_bytes(canonical_bytes(envelope))
        result = {'case': mode, 'original_digest_correct': digest(original_result) == original_digest,
                  'retained_result_digest': original_digest,
                  'actual_frozen_result_digest': digest(review['review_result']),
                  'identity_preserved': review['review_result_digest'] == original_digest and authority['review']['result_digest'] == original_digest}
        try:
            read = fixture.contract.read_bundle(str(root))
            result.update(accepted=True, document_count=len(read['review']['documents']),
                          invented_text_returned=any(b'REVIEW114618' in p for p in read['review']['documents'].values()))
        except Exception as error:
            result.update(accepted=False, error_type=type(error).__name__, error=str(error))
        return result
    finally:
        case.doCleanups()


out = {'boundary': 'Real producer and worker reader; derived copies alter materialized files and nested frozen artifact references but preserve original frozen result identity. No engine, live provider, Git operation or canonical store access.',
       'cases': [run_case(m) for m in ('control', 'rewritten_output', 'removed_outputs')]}
(HERE / 'probe.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out, indent=2))
