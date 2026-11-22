# Approved heavy native execution profile

Canonical Work: W385649; thread T385649. Separately scheduled prerequisite to
W385623 native correction execution, within the W9901 delivery campaign.

## Owner decision and current gap — 2026-11-22

Owner M385638 approves provider 7200 seconds, stage 9000 seconds, Job 21600
seconds including queue, ordinary verification unchanged at 900. Existing clock
origins, retry/correction/shutdown behavior remain unchanged. The running and
previously admitted Jobs retain their original profiles and deadlines.

M385647 preparation establishes that the installed runtime lacks registration.
The existing create CLI supports the necessary profile selector and provider
limit override, but job_control.agreeing rightly refuses inconsistent ceilings.
Register new immutable native-handoff-heavy/1; preserve native-handoff/1 exactly,
including zero correction rounds and one resolved clarification continuation.
This is execution policy registration, not implementation of Stage 1 recovery.

Preparation and exact proposed definition:
../finding-v12-retained-failure-analysis/evidence/heavy-profile-preparation-385646/PREREQUISITE.md
and PROFILE-DEFINITION.json (sha256
25b45962a2c785ceff8f0ebb53bc3778e29c54de3bb10e3a75027b800e1769cb).
That digest is evidence identity, not a newly invented wire field.

The profile source is independent of unaccepted retained f13e0b12. Do not import
or silently join that candidate. Runtime/source compatibility must be qualified
before its use in the later native correction Job.

## Implementation revalidation — E385652, 2026-11-22

Existing control profile membership and continuation table are the only missing registration seams. The CLI already supplies provider overrides; agreeing retains mismatch rejection. Added isolated candidate profile/docs and additive tests preserve old entries and enforcement owners. Connected deterministic evidence reaches real creation/readback and both worker roles with injected runner. Source review packet: evidence/implementation-385652/REPORT.md; no runtime/package/live acceptance claimed.
