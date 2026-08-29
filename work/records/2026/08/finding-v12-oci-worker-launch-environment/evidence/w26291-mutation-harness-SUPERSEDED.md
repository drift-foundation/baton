# `w26291-mutation-harness.py` is superseded — 2026-08-28

W26291's first implementation delivered four `BATON_WORKER_*` values as `--env`
arguments, and this dossier superseded that design BEFORE acceptance. The nine
mutations in `w26291-mutation-harness.py` therefore establish guards on a
contract that no longer exists, and a green run of it is not acceptance
evidence for anything live. The 2026-08-27 review said so explicitly.

**The file is kept exactly as it was produced.** It is how the retired design
was measured, and the reasoning that was superseded is what tells the next
reader why the current contract is not the obvious one. It does not run against
the current tree: the anchors it names went with the design.

**What replaced it:** `w26291-launch-document-mutations.py`, which measures the
live `/run/baton/launch.json` contract across BOTH trees — the manager's
`launch.py` and `oci.py`, and the worker's `baton_worker.py` — against the
real-engine `test_worker_container` suite as well as the in-process ones.

**The duplicate is gone.** An identical scratch copy sat at the record root as
`w26291_mutation.py`; the review asked for it to go and it has been removed. No
unique evidence was in it — both copies were byte-identical at sha256
`0686a08cb4ae64f8044ab54410bf3fcb386f34268fd4cf495f05591baa3a6ac7`, which is
also the digest of the file still here.

**The other retired evidence.**
`w26291-2026-08-27-launch-environment.txt` is the handoff account of the same
superseded transport and is kept for the same reason. Its `check_input_pair`
note is also overtaken: **W26296**
(`work/records/2026/08/finding-check-input-pair-inventory-follow-up`) owns that
inventory follow-up, the registration has landed, and the accepted full-tree
baseline is now SIX failures, all in `test_boundary_inventory`.
