"""Positive, conservative cessation proof for a consumed managed allocation.

Caller must first exclude every process under the allocation's exclusive uid
and hold broker admission closed. This module does not stop a live run or retry
an attempt. It preserves owner evidence, fences the controller, and refuses any
unsettled token or runtime. External observations use the normal engine adapter.
"""
import json

from baton_v12.worker_manager import ControlStore, attempts
from tools import authoring_baseline as baseline
from tools import authoring_enforcement as enforcement
from tools import job_manager, next_run as nr


def prove(control, packet, adapter):
    # Include ALL attempts in this isolated store, even admission interrupted
    # before Job episode linkage. Do not infer absence from the selected Job.
    inventory = attempts.runtime_recovery_inventory(control)
    evidence = []
    for item in inventory:
        token, runtime = item['token'], item['runtime']
        if token is None or not token['returned']:
            raise nr.Refusal('attempt has no positive resource cessation; recovery held')
        exact = runtime['runtime_id'] or token['container']
        if exact is None or token['container'] not in (None, exact):
            raise nr.Refusal('runtime identity unresolved; recovery held')
        observation = adapter.observe(exact)
        # Quiescent containers may restart. A returned token AND current exact
        # absence establishes the stronger condition used by this continuation.
        if observation.get('runtime_id') != exact or observation.get('state') != 'absent':
            raise nr.Refusal('runtime is live or uncertain; recovery held')
        evidence.append(dict(item, observation=observation))
    # No admission owner remains (the host excluded processes), and the old
    # consumed selection cannot be started again. Preserve a durable halt too.
    enforcement.halt(control, packet['run_id'])
    return {'state': 'ceased', 'run_id': packet['run_id'], 'authority_uuid': packet['deployment']['authority_uuid'], 'attempts': evidence, 'admission': 'halted'}


def inspect(packet_path):
    packet = baseline.held_packet(packet_path)
    baseline.verify_imported_sources(packet)
    enforcement.verify_controller(packet)
    with open(packet['deployment']['config_path'], encoding='utf-8') as handle:
        configuration = json.load(handle)
    engines = {worker['deployment']['engine'] for worker in configuration['workers']}
    if len(engines) != 1:
        raise nr.Refusal('one exact engine required for recovery')
    adapter = job_manager._Reclaiming(job_manager._ReclaimAdapter(engines.pop(), enforcement.bounded_engine))
    with ControlStore.open(packet['deployment']['control_store'], incarnation=packet['run_id'] + '-recovery', clock=enforcement.utc) as control:
        return prove(control, packet, adapter)
