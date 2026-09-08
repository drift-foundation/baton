"""Use an actual public eligibility answer at the consumer's declared seam."""
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
    consumer.receipts()
    control = consumer.verify.calls[0]
    for s in (consumer.verify, consumer.review, consumer.approve):
        s.calls.clear()
    # All other consumer fixture seams remain explicit. The eligibility shape
    # is the unchanged real owner's answer, not an invented test projection.
    consumer.accepted = actual
    try:
        answer = consumer.receipts()
        outcome = {'returned': answer}
    except Exception as exc:
        outcome = {'exception': type(exc).__name__, 'message': str(exc)}
    results = {'actual_eligibility': actual, 'actual_keys': sorted(actual),
               'evidence_keys': sorted(actual['evidence']), 'consumer_outcome': outcome,
               'receipt_calls': [len(s.calls) for s in (consumer.verify, consumer.review, consumer.approve)],
               'control_emitted_verification': control}
    Path(__file__).with_name('probe.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps({k:v for k,v in results.items() if k not in ('actual_eligibility',)}, indent=2))
finally:
    consumer.doCleanups()
    life.doCleanups()
