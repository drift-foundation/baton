"""Bounded engine client for Q4: the accepted Q1/Q2 runner with explicit budgets.

runner_base.py is byte-identical to the accepted Q2 runner. This adds only what two roles
need: a fixed number of worker containers, each from one pinned image in a fixed order; a
fixed number of offline inventory runs (network none, no mounts, --rm); a fixed number of
builds; and a cleanup that walks every container this run created, label-checked.
"""
import json,time
from runner_base import Commands as Base,cleanup as cleanup_one,extract,safe_root,save,sha
class Commands(Base):
    def __init__(self,root,*,worker_images=(),inventory_runs=0,builds=0,seconds=1200):
        super().__init__(root);self.deadline=time.monotonic()+seconds
        self.worker_images=list(worker_images);self.inventory_budget=inventory_runs;self.build_budget=builds
        self.containers=[];self.workers=0;self.inventories=0;self.built=0
    def __call__(self,argv,seconds=None,cap=2*1024*1024):
        launching=argv[0]=='docker' and argv[1] in ('run','create')
        if argv[0]=='docker' and argv[1]=='build':
            assert self.built<self.build_budget,'build budget exhausted';self.built+=1;self.builds=0
        if launching:
            if '--rm' in argv:
                assert argv[1]=='run' and self.inventories<self.inventory_budget,'inventory budget exhausted'
                assert argv[argv.index('--network')+1]=='none' and not any(x in argv for x in ('--mount','-v','--volume','--env-file')),'inventory run must be offline and unmounted'
                self.inventories+=1;kind='inventory'
            else:
                assert self.workers<len(self.worker_images),'worker container budget exhausted; no retry or extra container'
                assert argv[-1]==self.worker_images[self.workers],'worker container from an unexpected image or out of order'
                self.workers+=1;kind='worker'
            self.launches=0
        try:return super().__call__(argv,seconds=seconds,cap=cap)
        finally:
            if launching and self.created is not None and all(one['name']!=self.created for one in self.containers):
                self.containers.append(dict(name=self.created,labels=dict(self.expected_labels),kind=kind,image=argv[-1] if kind=='worker' else None))
                save(self.root/'containers.json',self.containers)
def cleanup_all(run,root,seconds=150):
    """Every container this run created, by exact name, label-checked. No prune, no image removal."""
    answers=[];deadline=time.monotonic()+seconds
    for one in run.containers:
        run.created=one['name'];run.expected_labels=one['labels']
        answer=cleanup_one(run,root);run.deadline=min(run.deadline,deadline);answers.append(dict(answer,kind=one['kind']))
    answer=dict(containers=answers,ceased=all(a.get('ceased') is True for a in answers),removed=all(a.get('removed') is True for a in answers))
    save(root/'cleanup-all.json',answer);return answer
