"""Explicit audited withdrawal of a failed first initialization, never reseeding.

Trusted host-owner command. Reads the selected attempt's metadata and delegates
all D1 preconditions to provider_home; opens no credential source or engine.
"""
import argparse,json,sys
from datetime import datetime,timezone
from baton_v12.contracts import ContractRefusal,digest
from baton_v12.worker_manager import ControlStore,model_attribution,provider_home
COMMANDS=("credential-recovery-withdraw",)
def withdraw(control, *, attempt_id, receipt_id, decision_id):
    selected=model_attribution.selection_of(control,attempt_id)
    if selected is None:
        raise provider_home.HomeRefusal("credential recovery requires a retained provider selection")
    identity=selected['delivery']['home_identity']
    mount=provider_home.HomeMount(selected['home_root'],attempt_id=attempt_id,**identity)
    audit=provider_home.recover_failed_initialization(mount,control,receipt_id=receipt_id,decision_id=decision_id)
    return dict(state='withdrawn',attempt_id=attempt_id,receipt_id=receipt_id,
                decision_id=decision_id,audit_digest=digest(audit),automatic_retry=False)

def main(argv, *, clock=None, stream=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=COMMANDS)
    for name in ('control','attempt','receipt','decision'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args(argv)
    clock=clock or (lambda:datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z'))
    try:
        with ControlStore.open_readonly(args.control,incarnation='credential-recovery-owner',clock=clock) as control:
            result=withdraw(control,attempt_id=args.attempt,receipt_id=args.receipt,decision_id=args.decision)
    except (provider_home.HomeRefusal,ContractRefusal,OSError,ValueError,KeyError):
        # Neither secret contents, rejected values nor host paths enter refusal output.
        print(json.dumps(dict(state='held',reason='credential-recovery-preconditions-unproved')),file=stream or sys.stdout)
        return 1
    print(json.dumps(result,sort_keys=True),file=stream or sys.stdout)
    return 0
if __name__=='__main__':sys.exit(main(sys.argv[1:]))
