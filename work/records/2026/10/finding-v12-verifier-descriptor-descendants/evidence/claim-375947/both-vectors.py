import os, sys, tempfile
sys.path.insert(0,'src'); sys.path.insert(0,'.')
from baton_v12.worker_manager import oci, source_boundary, workspaces
from baton_v12.worker_manager.store import ControlStore
from tests.manager import input_roots
home = tempfile.mkdtemp(); store = ControlStore.open(os.path.join(home,"c.sqlite3"),
    incarnation="i", clock=lambda: "2026-10-28T00:00:00.000Z")
group = input_roots.configured_group(store); identity = workspaces.identity_for(group)
storage = os.path.join(home,"layout"); os.makedirs(storage, 0o700)
I = {"image_digest":"sha256:"+"d"*64,"profile_digest":"sha256:"+"b"*64,
     "policy_digest":"sha256:"+"d"*64,"adapter_digest":"sha256:"+"c"*64}
doc = source_boundary.compose_verifier_layout(marker=source_boundary.image_layout_marker(),
    identity=identity, **I)
d = source_boundary.materialize_verifier_layout(storage, document=doc)
L = {"runtime_attempt_id":"attempt-x","authority_uuid":"2b077949c86e8bef24304f59c28ec398",
 "work_id":"2b077949-W325695","participant":"baton.claude","generation":1,
 "principal":"principal:org-a","effective_scope":"scope:deployment",
 "profile_digest":I["profile_digest"],"policy_digest":I["policy_digest"],
 "adapter_digest":I["adapter_digest"]}
def v(**kw):
    h = dict(image_digest=I["image_digest"], labels=L, posture="execution", name="probe",
             assignment_roots={"inputs":os.path.join(home,"in"),"workspace":os.path.join(home,"out")},
             workspace_group=group); h.update(kw); return oci.run_vector("podman", **h)
t = lambda a: [a[i+1] for i,o in enumerate(a) if o=="--tmpfs"]
print("document uid/gid/mode:", doc["uid"], doc["gid"], oct(doc["mode"]))
print("\nUNSELECTED tmpfs operands:"); [print("  ",x) for x in t(v())]
print("\nSELECTED tmpfs operands:"); [print("  ",x) for x in t(v(layout_delivered=d))]
print("\nunselected argv length:", len(v()))
print("unselected identical to layout_delivered=None:", v()==v(layout_delivered=None))
print("committed SCRATCH_MOUNTS value restored:", source_boundary.SCRATCH_MOUNTS == (("/tmp",64<<20),("/dev/shm",16<<20)))
print("aggregate equal across both tables:",
      sum(s for _t,s in source_boundary.SCRATCH_MOUNTS)==sum(s for _t,s in source_boundary.SELECTED_SCRATCH_MOUNTS))
store.close()
