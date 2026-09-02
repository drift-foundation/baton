# Preflight a v12 dogfood attempt before staging its source

Ledger Work: W62535

## Observed — 2026-09-01

W62098 run1 used a fresh authority and control store. The supervised operator
created the assignment input root and staged `inputs/source`, then refused the
offer because the store had not certified the named `dogfood` runtime profile.
After the profile was certified through the public Worker Manager API, retrying
the same attempt refused because source staging is deliberately one-shot and
the input directory already existed.

No worker container or provider turn started. The retained failed attempt is
`/tmp/w62098/run1` on the development host.

## Confirmed defect

A deployment/configuration prerequisite that can be proved without creating an
attempt is checked after durable source staging. A harmless setup error thereby
turns a never-launched attempt into a non-retryable partial attempt. The
stage-once refusal is correct; weakening it would permit measured input to be
replaced. The ordering is the defect.

The retained run and focused reproduction are recorded in
`evidence/research-2026-09-01/README.md`. The reproduction reaches the real
workspace, staging, control-store and offer operations: an uncertified store
leaves both the attempt root and staged source present, while committing no
offer and starting no runtime or provider turn. Certification followed by a
same-identity retry then reaches the correct stage-once refusal.

## Confirmed boundary closure

The runtime profile is not the only already-known deployment prerequisite
behind allocation:

- the operator reads the configured workspace group before allocation, but
  never proves that its granted storage path is the manager's configured
  workspace storage;
- credential slot/profile resolution is pure, yet runs only after claim and
  activation when the lazy adapter factory materializes the credential.

All three can be decided from grants plus the already-open control store,
without reading bearer bytes or acting on authority, filesystem allocation,
or the engine. Mutable Work eligibility and capacity are different: their
authoritative checks remain in offer issuance and cannot be made atomic with
source staging by an earlier read.

## Direction

The operator must prove the configured runtime profile, configured workspace
group and exact configured storage, and pure credential mapping before
allocating or staging assignment input. The proof should be one shared
deployment-readiness owner used by the documented launcher and direct arc,
and should return held capabilities/values for later consumption.

The Worker Manager needs a generic public certification read/require boundary
that owns the same adopted-store and typed-refusal semantics `issue_offer`
currently keeps private. The early requirement is fail-fast; `issue_offer`
still rechecks authoritatively before it commits an offer.

A focused regression must show that an uncertified profile, absent/mismatched
configured storage, or invalid credential mapping leaves no attempt root,
offer, claim, runtime, launch delivery, or credential material. Once the
prerequisite is corrected, the same identity is eligible because no attempt
was created. Stage-once remains unchanged after staging actually occurs.
Recovery of genuinely interrupted attempts remains explicit and does not
become implicit overwrite/retry.

## Confirmed configuration stability

The relevant manager configuration cannot change through the public API once
read successfully. Profile certification uses one fixed journal operation per
kind/name and puts the digest in its signature, so a changed digest collides;
there is no withdrawal operation. Workspace group/storage configuration is
likewise one-store immutable. A concurrent first certification can only make
an absent early read refuse conservatively, leaving the identity clean for a
retry. This Work needs no configuration generation or reservation.

## Bounded workaround

Retain run1 as evidence and start W62098 run2 with a new attempt identity only
after the fresh store is fully configured. Do not reuse or replace run1's
staged source.

## Approved direction — 2026-09-02

Approve the shared deployment-readiness owner described above. Before
`assignment_workspace` allocates or stages anything, it must require the exact
immutable runtime profile name/digest through a generic public Worker Manager
read/require operation, prove the configured workspace group and exact storage,
and resolve the credential slot/profile mapping without reading bearer bytes.
`issue_offer` keeps the authoritative mutable Work, capacity and certification
rechecks. No configuration generation or reservation mechanism is added.

Implementation remains an isolated v12 assignment; this approval does not
route the Work to the legacy v11 implementer.

## Observed second preflight failure — 2026-09-02

W33937 attempt `attempt-w33937-run2c` used the certified `dogfood` runtime
profile digest and pinned worker image
`sha256:896884b237a14d2397a9851dc1692cb34bedb46a367c2544de9e7499fd9bc124`.
The provider completed successfully and returned exactly the three authorized
text paths, but the operator's post-turn verification failed before running a
test: that image has Python 3.11.2 and no `jsonschema`, while the v12 Python
distribution requires Python >=3.13 and `jsonschema==4.26.0`.

The same exact retained candidate then ran 156 tests successfully in the
configured host v12 environment, including both independent W33937 review
probes. The candidate is not the cause. The certified profile/digest currently
asserts an intended environment without proving the selected image supplies
it. Preflight therefore admitted a runtime that could execute the model but
could not execute the assignment's declared verification vector.

The pre-staging readiness boundary must also prove that the selected runtime
and verification environment satisfy the exact declared toolchain/profile. A
Claude provider may need Node while the assignment verifier needs Python 3.13
and the locked Python closure; those may coexist in one image or be split into
separately declared provider and trusted-verifier environments, but an opaque
certified digest may not stand in for the executable fact. This decision does
not choose that packaging design.

Bounded stopgap: retain the clean failed-verification proposal, record the
image mismatch, and let independent review rerun the exact vector in the
configured host v12 environment. The external green run is evidence for
review, not a rewrite of the immutable proposal's `verification-failed`
disposition. Do not rebuild or mutate the retained artifact to make its status
look green.
