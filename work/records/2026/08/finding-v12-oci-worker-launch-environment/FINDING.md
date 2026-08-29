# Reference-worker launch environment through OCI

Date: 2026-08-27
Parent discovery: W6636, `work/records/2026/08/finding-v12-local-oci-lifecycle-composition/`

## Finding

**Observed:** The reference worker image contract requires four non-secret launch values: `BATON_WORKER_POSTURE`, `BATON_WORKER_SESSION`, `BATON_WORKER_CONTRACT`, and `BATON_WORKER_ROLE`.

**Confirmed:** The current manager-to-OCI adapter start path does not deliver those values, so an adapter-started reference worker is not runnable under the declared contract. W6636's approver authorized a separate correction Work.

**Confirmed boundary:** This Work owns the exact manager/adapter seam for those four non-secret values and no credential-bearing environment. It does not change the reference worker implementation or absorb the broader W6636 lifecycle matrix.

**Proposed:** Represent the four values explicitly in the launch request, validate them before the engine call, and translate them into the OCI environment without broad arbitrary-environment pass-through.

## Acceptance

- The manager supplies exactly the four required `BATON_WORKER_*` values through the typed adapter contract.
- The OCI adapter starts the reference worker with those exact values.
- Missing, duplicate, malformed, or unexpected launch values fail before container execution.
- Credential or other secret material cannot enter this environment seam.
- A positive real-Docker regression replaces the current expected launch failure and proves the reference worker becomes runnable.

## Open

- Exact type placement and validation ownership must be revalidated against the current launch request and adapter modules.

## Superseding decision — 2026-08-27

The proposal and acceptance text above that transport the four launch values
as four environment variables are superseded before acceptance. They remain
here as chronological context and are not a compatibility path.

The manager instead authors one versioned UTF-8 JSON launch document and the
OCI adapter mounts it read-only at the fixed worker path
`/run/baton/launch.json`. The document carries `schema`, `posture`, `session`,
`contract`, and `role`. The worker validates the complete document before use:
the schema/version is explicit, all required fields are present and typed, and
unknown properties fail closed. A missing, malformed, mutable, non-regular, or
wrong-version document refuses startup before any agent execution.

The fixed path needs no locator environment variable. The reference worker
must not accept `BATON_WORKER_POSTURE`, `BATON_WORKER_SESSION`,
`BATON_WORKER_CONTRACT`, or `BATON_WORKER_ROLE` as a fallback. This keeps the
worker-control boundary extensible through a versioned document rather than an
ever-growing environment-variable vocabulary.

The launch document is non-secret control metadata. Credentials remain a
separate transient read-only provider under `/run/baton/credentials`; they do
not enter the launch document, environment, argv, labels, or durable records.
Assignment input and worker output remain on their separately governed mounts.

## 2026-08-27 — independent review

**Confirmed P0:** The submitted implementation implements only the superseded
four-environment-variable proposal. `request_runtime_start` accepts an
`environment` operand, `run_vector` emits `--env`, absence is explicitly legal,
the lifecycle fixture invents the three caller values, and the reference
worker remains unchanged on its legacy environment reader. None of the required
manager-authored `/run/baton/launch.json` production, fixed read-only mount, or
worker-side strict document validation exists. Green tests and mutation results
for the retired transport are not acceptance evidence for the live contract.

**Confirmed boundary:** The superseding decision necessarily replaces the
earlier statement that this Work does not change the reference worker: the live
decision explicitly assigns complete launch-document validation and removal of
the environment fallback to that worker. The old boundary remains historical,
not actionable.

## Consent-posture supersession — 2026-08-27

The `posture` member in the preceding launch-document decision is superseded
before acceptance. V12 no longer launches a separate consent runtime. The one
claimed execution runtime receives a launch document containing `schema`,
`session`, `contract`, and `role`; consent/execution is not a runtime axis and
there is no constant posture value to transport.

The claimed container may receive the exact declared repository or other Work
source through read-only `/input`, because dispatch explicitly authorizes that
disclosure. The launch document still carries no source contents, credentials,
arbitrary environment, Baton authority locator, or host path. There is no
legacy environment fallback.

## Pinned launch-document contract — 2026-08-28

Review item 1 requires the exact schema, version and bounds to be pinned here
before code changes proceed. This is that pin. It is written from the two
supersessions above and adds nothing to them; where it makes a choice those
left open, the choice is named as one.

**The document.** One UTF-8 JSON object, authored by the manager, materialized
as a manager-owned regular file and bind-mounted READ-ONLY at the fixed
container path `/run/baton/launch.json`. The path is a constant of this
contract at both ends: there is no locator environment variable, no
caller-selected target, and no arbitrary mount channel that could reach it.

**The schema constant.** `schema` is the literal `baton.worker-launch/1`. The
version is IN the name, exactly as `baton.worker-entry/1` carries the channel's
version, so a document from a different generation is refused by an equality
test rather than by parsing a separate version member.

**The members, and there are exactly four.** `schema`, `session`, `contract`,
`role`. All four required, all four strings, and any other top-level member
fails closed. There is NO `posture`: the consent-posture supersession above
removed the axis, and a member carrying a constant would be transporting a fact
that no longer exists.

**The value bounds.**

- `session` is the identity the manager minted for this container session:
  bounded non-empty text, at most 256 characters. That ceiling is the worker's
  own `MAX_IDENTITY`, because `session` is the value the worker-entry channel
  binds every frame to and a value the worker would refuse is not one the
  manager may write.
- `contract` and `role` are operator prose: bounded non-empty text, at most
  4096 characters each.
- No value carries `U+0000`. The retired environment transport also refused
  `U+000A`, because one `--env NAME=VALUE` argument cannot survive a newline.
  That refusal is NOT carried forward: a human contract is prose and may
  legitimately contain newlines, and keeping the ban would be preserving a
  retired transport's limitation as though it were a rule about the value.
- The whole document is at most 65536 bytes, which is the bound the worker
  reads under. A document larger than the members it may contain is refused
  before it is parsed.

**What is refused, at the worker, before any agent execution.** Absent,
unreadable, a symbolic link, not a regular file, writable for the container's
own view, wider than the byte ceiling, not UTF-8, not one JSON object, a
`schema` that is not the pinned constant, a missing member, an unknown member,
a wrong type, an empty or over-long value, and a start carrying only the
retired `BATON_WORKER_*` environment. The read is bounded, no-follow, and
proves the opened descriptor is a regular file — the same rule W26283 pinned
for every other worker-controlled or worker-visible byte this campaign reads.

**What the document never carries.** Credentials, bearer material, source
contents, arbitrary environment, a Baton authority locator, and any host path.
Credentials remain the separate transient read-only provider under
`/run/baton/credentials`; assignment input and worker output remain on their
own governed mounts. The manager walks the authored document under §13 before
it is written, so a live bearer cannot ride this channel any more than it can
ride the start vector.

### Clarification the supersessions force, and it is a decision — 2026-08-28

Removing `posture` from the document removes the reference worker's only
source for it. There is no environment fallback, the image is forbidden to
carry a default, and the ruling says there is no constant to transport. So the
worker-entry program can no longer ASK what kind of container it is: it is the
one runtime V12 launches, and `POSTURES`, `posture_of`, the posture-keyed
environment set and the posture-keyed operation set go with the axis rather
than being fed an invented value.

Two consequences are named rather than left to be discovered:

- `describe`'s answer loses `posture` and `environment` and gains `launch` —
  the sorted member names of the validated launch document, which is the exact
  analogue of what `environment` reported. This is a change to the ruled
  `baton.worker-entry/1` answer shape, forced by the ruling that removed the
  axis it reported.
- `consider` is KEPT as a known operation this runtime is not entitled to,
  rather than deleted. Deleting an operation from a ruled protocol is a larger
  decision than this Work holds, and keeping it preserves the entitlement
  proof: `consider` stays a real operation that a `work` container refuses,
  which is what makes that refusal mean anything.

**Open, and it needs an owner:** whether `consider`, `ScriptedAgent.consider`
and the rest of the consent vocabulary should be removed from
`baton.worker-entry/1` now that no consent runtime exists. This Work
deliberately does not decide it.

## 2026-08-28 — the re-reviewed findings, corrected

**Confirmed corrected — the mode is ESTABLISHED, not requested.** A creation
mode is filtered by the process umask, so `materialize` authored a 0400
document under the ordinary service umask 077 — one the container's fixed uid
65532 cannot read, which is the unrunnable worker this Work exists to fix,
arriving silently and only on a host whose umask happens to be restrictive.
The file is now created at 0000 and `fchmod`ed to 0444 on the descriptor that
wrote it, after the last byte: exact whatever the ambient umask is, with no
writable interval and no instant at which a partial document is readable.

**Confirmed decision — the canonical start REQUIRES a materialized launch
document.** The operand stays optional at CONSTRUCTION, because the runtime
half of the adapter (list, observe, stop, destroy, seal, collect) is
constructible without one exactly as `outputs` is. It is refused at START,
before the engine is asked anything, beside the authorized-root refusal and
for the same reason: a container launched with nothing at
`/run/baton/launch.json` cannot correlate a single thing it says, and "the
worker refuses it later" is a container that died rather than a delivery this
manager declined.

**Confirmed decision — the launch root has ONE ending, on the SAME evidence.**
`launch.discard` had no production caller, so a refused start and a destroyed
runtime both left an attempt-private root and a world-readable document behind
for good. It is now discarded from the two places that establish that no
runtime can hold the mount — `_undelivered` and `_torn_down`'s absence — and
an absence that cannot be proved leaves it `unresolved` rather than removed.
It is reported BESIDE the credential ending and never folded into it: a
delivery with no credential still has a launch document, so one listing
settles two named endings.

**Confirmed correction — `describe.launch` reports all four members.** The
implementation stripped `schema` and answered three, on the argument that the
version is the program's business. That is a plausible proposal and it is not
the recorded decision: the pin above says `launch` is "the sorted member names
of the validated launch document", and that document has four. The ruling wins
over the implementation's preference, and an operator reading `describe` now
sees which generation the container was launched under.

**Confirmed correction — the module contract said 0400 under 0500.** It says
0444 under 0555, which is what was pinned and what is implemented.

## 2026-08-28 — second re-review

**Confirmed P1:** the new mandatory-launch check refuses directly before
`_refused_start`. When the adapter already holds a same-attempt materialized
credential delivery but no launch delivery, the engine is correctly untouched
but the credential root and live bearer registration remain stranded. Exact
output and a durable reproduction are in
`review-2026-08-28T08-33-46Z.md` and
`evidence/w26291-missing-launch-credential-reproduction.py`.

## 2026-08-28 — the missing-launch refusal, corrected

**Confirmed corrected — a missing launch document refuses THROUGH the
settlement rather than past it.** The check called `_denied` directly, above
the attempt checks, with a comment saying nothing had been created yet so there
was nothing to settle. That is true only when no OTHER provider has
materialized anything, and a canonical adapter may already hold a credential
delivery whose root and live registration exist before `start` is called. The
refusal therefore stranded a bearer on a path with no runtime id for the
ordinary destroy crossing to name — the exact W26284 start-failure invariant
this manager was corrected for once.

**Confirmed placement, and it is the decision worth recording.** The refusal
now sits AFTER both attempt checks and goes through `_refused_start`.
`_refused_start` settles by asking which runtimes carry THESE labels, so a
delivery belonging to a different attempt must refuse above that line: an
empty answer about attempt 2 says nothing about attempt 1's runtime, and
acting on it would be inferring absence from the wrong question. A same-attempt
delivery is settled; a mismatched one is refused untouched and without asking
the engine anything at all.

**Confirmed unchanged — an adapter with neither delivery still reaches no
engine.** `_undelivered` answers `not-delivered` for both without listing when
there is nothing to settle, so the "refused before the engine" property the
first re-review asked for survives exactly where it applies.
