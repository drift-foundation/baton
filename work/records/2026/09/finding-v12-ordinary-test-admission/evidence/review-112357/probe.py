"""Exercise the corrected schema read with an actual public eligibility answer.

Producer and receipt seams are explicit fixtures: this is not full admission.
"""
import copy
import json
from pathlib import Path
from baton_v12.worker_manager import integration_checkpoint
from tests.job_manager.test_review_driver import TheWorkerCompletionTraversesPublicCustody as Lifecycle
from tests.integration.test_driver import TheReceiptBoundaryRefusesBeforeItWritesAnything as Consumer

life = Lifecycle('test_actual_completion_reaches_first_verdict_and_public_custody')
consumer = Consumer('test_the_unchanged_control_writes_exactly_three_receipts')
try:
    life.setUp()
    held = life.produced()
    ending = life.end(held)
    assert ending['outcome'] == 'accepted'
    actual = integration_checkpoint(life.control, ending['line_id'])
    consumer.setUp()
    consumer.accepted = copy.deepcopy(actual)
    base, head = actual['evidence']['base'], actual['evidence']['head']
    consumer.claim.update(base=base, head=head)
    consumer.observed = {'base': base, 'head': head}
    consumer.proposal.update(target=base, candidate_digest=head)
    consumer.retain()
    positive = consumer.receipts()[2]
    positive_calls = [len(s.calls) for s in (consumer.verify, consumer.review, consumer.approve)]
    for s in (consumer.verify, consumer.review, consumer.approve):
        s.calls.clear()
    consumer.accepted['evidence']['head'] = 'f' * 40
    try:
        consumer.receipts()
        negative = {'accepted': True}
    except Exception as exc:
        negative = {'exception': type(exc).__name__, 'message': str(exc)}
    result = {'actual_eligibility': actual, 'positive_receipts': positive,
              'positive_calls': positive_calls, 'wrong_head': negative,
              'negative_calls': [len(s.calls) for s in (consumer.verify, consumer.review, consumer.approve)]}
    assert positive_calls == [1, 1, 1]
    assert negative.get('exception') == 'ContractRefusal'
    assert result['negative_calls'] == [0, 0, 0]
    Path(__file__).with_name('probe.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('actual_eligibility', 'positive_receipts')}, indent=2))
finally:
    consumer.doCleanups()
    life.doCleanups()
