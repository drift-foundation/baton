# Retry the first useful task after retained review exists

Work: W51487
Follow-up of: W39364
Dependency: W51473

## Purpose

W39364 spent its one authorized provider attempt and closed with an explicit
candidate rejection. Closed Work does not reopen. This record is the only
place a later fresh attempt may be considered after the operator can retain a
candidate for direct independent review.

## Boundary

- W51473 must close satisfying first: explicit retention, honest terminal
  retained resolution, and a real-Docker retained-candidate gate.
- The prior credential/network authorization was bounded to one supervised
  attempt and is consumed. Obtain a new explicit operator authorization and
  exact grants; infer nothing from W39364.
- Revalidate the frozen four-file task against the then-current checkout.
- Run at most the newly authorized number of fresh attempts. No retry reuses
  the rejected worker result or provider conversation.
- Retain the candidate, bounded worker account and correlated redacted
  evidence. Independently diff and run the exact harness outside the worker.
- Record explicit accept or reject; never write the candidate into the
  canonical checkout automatically.

W51476 is a separately scheduled preflight hardening defect. It becomes
critical here only if current revalidation shows it can make the later result
falsely succeed; otherwise the dry document-pair precheck remains required
before spending a newly authorized attempt.

## 2026-08-31 — approver ruling: task-scoped retry authorization

The per-attempt authorization proposed in M51757 and the Boundary rule to run
at most a newly authorized numeric count are superseded for W51487. The
authorization is now scoped to this fixed Work rather than to one provider
turn. Fresh attempts may continue until W51487 reaches a terminal disposition
while all of the following remain unchanged:

- the frozen four-file task and its acceptance boundary;
- credential source `/run/baton/credentials/claude`;
- Docker network `bridge`;
- retention disposition `retain`.

Every attempt still uses fresh identities and retains correlated evidence; no
attempt reuses a rejected result or provider conversation, and no candidate is
written into the canonical checkout automatically. Stop and return to the
approver only for a new material blocker, a change to the task or grants, or
explicit cancellation. An unchanged retry does not require another approval.

## 2026-08-31 — first live retry result and material blocker

Attempt `attempt-w51487-run2` reached an honest terminal `retained` ending,
removed its runtime, and preserved a directly reviewable candidate and bounded
worker account. Independent review confirmed that the candidate is
byte-identical to the frozen four-file input and that the exact 26-test harness
still passes; those are baseline facts, not completion of the assigned task.

The worker account reports `provider-failed`, provider exit status 1, no
verification attempted, and an empty patch. Credential-free probes establish
that the image contains a working provider CLI and that DNS and TCP 443 work
from the authorized posture. An invented invalid credential reproduces the
same immediate API-error shape, making rejection of the configured credential
the leading explanation, but not a measured fact. No participant opened or
recorded the authorized credential.

This is a new material blocker under the task-scoped retry ruling above. The
candidate is rejected, W51487 remains open, and no unchanged retry should run
until the operator verifies or repairs the unchanged credential source and
explicitly returns the Work. Review:
`review-2026-08-31T08-57-18Z.md`.

## 2026-08-31 — approver ruling: refresh the staged credential

`claude auth status --text` reports an authenticated Claude Max host session.
Without opening either credential, metadata shows the host source
`/home/sl/.claude/.credentials.json` is a regular `0600 sl:sl` file newer than
the regular `0400 sl:sl` staged source `/run/baton/credentials/claude`. The
operator therefore authorizes replacing only the staged source from the
current authenticated host source, restoring mode `0400` and owner `sl:sl`.
No credential content is published or recorded. After metadata/readability
verification, W51487 resumes under the existing task-scoped retry grant; the
task, `bridge` network, `retain` disposition and no-auto-apply boundary remain
unchanged.

Reviewer revalidation after M52739 observes the replaced staged credential as
a regular file, mode `0400`, owner `sl:sl`, 509 bytes, readable by the managed
operator; its content was not opened. The frozen checkout and clean staged
source still match all four hashes in
`dry-revalidation-2026-08-31T08-46-13Z.md`. The next attempt must use fresh
authority, Work, offer, attempt, runtime, control, launch, and storage
identities and must not reuse run2's rejected result or provider conversation.

## 2026-08-31 — run3 refutes authentication and locates credential readability

Attempt `attempt-w51487-run3` used the replaced credential and wholly fresh
identities, yet produced the same retained `provider-failed`/status-1 account,
empty patch, and unchanged candidate as run2. This refutes the earlier leading
inference that the configured credential was rejected by the API.

The new material blocker is confirmed at the manager/worker boundary.
`credentials.py` creates every volatile slot with `VOLATILE_FILE = 0o600`
owned by the manager, while the execution container runs as uid 65532.
`claude_agent._prepared_home` tests only `os.path.exists(slot)`, so an
unreadable slot passes its guard and is symlinked into the provider home. A
credential-free reproduction as uid 65532 observes the slot but gets
`EACCES`; an uncredentialed Claude invocation then produces the same immediate
exit-1 shape as the attempt. The provider argv, including `acceptEdits`, is
independently shown valid.

The candidate is rejected and further unchanged retries stop. The separately
accountable correction is owned by the child record
`findings/finding-runtime-credential-slot-readability/`; W51487 cannot finish
before that correction closes satisfying and a fresh retained attempt reaches
independent review. Review: `review-2026-08-31T09-16-34Z.md`.

## 2026-08-31 — credential blocker closed; fresh attempt authorized to resume

W52800 closed satisfying after independent third-round sign-off in
`findings/finding-runtime-credential-slot-readability/review-2026-08-31T16-20-31Z.md`.
The live slot is now created at exact `0640` in the configured workspace group
below the manager-owned `0700` root; recovery re-proves that boundary; and the
worker distinguishes an unreadable slot before provider launch. The retained
real-container evidence proves readability with the configured supplementary
group and unreadability without it.

Reviewer revalidation after closure confirms that the frozen four source files
and the human contract still have the exact hashes and byte sizes recorded in
`dry-revalidation-2026-08-31T08-46-13Z.md`. Metadata only confirms the unchanged
staged source `/run/baton/credentials/claude` is a regular 509-byte `0400`
`sl:sl` file; no credential bytes were opened.

The next retained attempt therefore proceeds under the unchanged task-scoped
grant: the same frozen task, credential source, `bridge` network, `retain`
disposition and no-auto-apply boundary. It must use wholly fresh authority,
Work, offer, attempt, runtime, control, launch and storage identities, and must
rebuild the worker image from the current W52800-corrected tree rather than
reuse run3's pre-correction image digest. Run2/run3 results and provider
conversations are evidence only and are never resumed.

## 2026-08-31 — run4: the provider turn happened and the task was performed

Attempt `attempt-w51487-run4` ran under the unchanged task-scoped grant with
wholly fresh identities and the worker image rebuilt from the W52800-corrected
tree (`sha256:b471399a…`, not run3's `sha256:9b83e49c…`). Exit 0, 2m34s,
terminal `retained`, `resolved: true`, `unresolved: []`.

Unlike run2 and run3, the provider ran. The candidate changes exactly
`v12/spike/ping-pong/test_harness.py`, adding 106 lines and removing none;
`preflight.py`, `trial.py` and `trial.mjs` are byte-identical to the frozen
originals. The four new cases establish all four facts the frozen task
required, and six mutations of `_observed_readable` are each caught by the case
that owns the corresponding fact. Independently rerun outside the worker the
harness reports 30 tests, OK.

**A new fact about the frozen task, and it is not a defect in the candidate.**
The worker recorded `verification-failed`, status 1. Measured afterwards
credential-free: inside the worker image as uid 65532, the UNMODIFIED frozen
source already ends 1, failing the same two pre-existing
`AnAncestorDecidesReadabilityToo` cases as the candidate does — they assert
that a `0o700` directory makes a file unreadable, which is only true for a
process that does not own the tree. So `verification-failed` was
unreachable-by-any-candidate for this task in this worker, and no provider
output could have avoided it. Evidence:
`evidence/w51487-run4/verification-discrepancy.md`.

The implementer's reading is that the candidate is worth accepting; the
terminal accept or reject for W38956 is the reviewer's. Acceptance record:
`acceptance-2026-08-31T16-40Z.md`. Evidence: `evidence/w51487-run4/`.
The deployment preparation each attempt needs — absent from the record until
now, and reconstructed by hand for every earlier attempt — is written down as
`prepare_attempt.py` beside this record.
