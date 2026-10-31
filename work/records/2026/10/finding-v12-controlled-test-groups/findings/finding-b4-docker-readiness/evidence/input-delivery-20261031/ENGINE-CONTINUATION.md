# Proposed engine continuation; not executed or authorized by this slice

DockerDelivery and DockerConfiguredGroup inherit Delivery -> composition.Lifecycle.
Lifecycle.setUpClass (test_lifecycle_composition.py:125-166) calls Docker build using
v12/worker/Dockerfile and v12/worker as context, timeout1800; creates a unique
baton-lifecycle:<uuid12> tag, resolves exact image ID, and registers exact-tag image
removal. The Dockerfile copies baton_worker.py, scripted_agent.py and the frozen
worker-control schema on pinned python base 8fef26df932191825664e4957ff488c96dfe64918327634a357a55facbc994d3.
It uses the worker entrypoint; these classes exercise actual request_runtime_start,
not just arbitrary Python payloads. Selected source hashes are in engine-inputs.json.
The initial-access historical Git-capable image alone is not evidence of matching
this worker artifact, and selecting it previously did not authorize substitution here.

Proposed next allocation: either explicitly select one isolated local build of those
stable source bytes, or supply an independently selected installed image with matching
worker/schema provenance and permit a test-file-local setup override (avoiding changes
to K's shared Lifecycle). The stock inherited setup builds once for EACH subclass;
prefer one selected reusable digest and a local override after coordination, not two
implicit builds. Do not reuse initial-access image without that provenance decision.

Once selected, run only the two engine classes serially from the allocated snapshot:
just test-one tests.manager.test_input_delivery.DockerDelivery tests.manager.test_input_delivery.DockerConfiguredGroup
Use prepared interpreter, BATON_TEST_ENGINE=docker, actual gid1001 membership,
BATON_V12_WORKSPACE_GROUP=1001, fresh external disk root, unique run label and exact
container-ID cleanup supervision. Propose a separately selected build allowance
(1800s if needed) and 600s focused execution plus120s cleanup. Retain source/image
hashes, label/ID evidence, observed UID/GID and mount denials, case ledger and empty
root; preserve historical containers/images. These are proposed boundaries, not a
run undertaken here. Inspect every identity expectation: execution identity differs
from image-default/consent identity; same-owner permission probes cannot impersonate
the old foreign-UID proof. Preserve actual read-only mount denials and custody behavior.
