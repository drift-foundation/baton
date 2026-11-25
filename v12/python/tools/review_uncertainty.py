"""Read delivered ordinary-review owner items; no runtime or credential access."""
import argparse,json,sys
from datetime import datetime,timezone
from baton_v12.job_manager import JobStore
from baton_v12.job_manager.review_uncertainty import items_of
COMMANDS=("review-uncertainty-items",)
def main(argv, *, clock=None, stream=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=COMMANDS)
    parser.add_argument('--jobs',required=True)
    parser.add_argument('--authority-uuid',required=True)
    args=parser.parse_args(argv)
    clock=clock or (lambda:datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace('+00:00','Z'))
    with JobStore.open_readonly(args.jobs,authority_uuid=args.authority_uuid,incarnation='review-uncertainty-reader',clock=clock) as store:
        print(json.dumps({'items':items_of(store)},sort_keys=True),file=stream or sys.stdout)
    return 0
if __name__=='__main__':sys.exit(main(sys.argv[1:]))
