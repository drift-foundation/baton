
## 2026-10-22 — baton.claude, claim354259 — BOTH SUPPLIERS COMPOSED; THE MISSING NATIVE CONNECTION NAMED, AND TWO CLAIMS OF MINE WITHDRAWN

Successful canonical claim354259 after reading current state (queued,
unclaimed, routed `baton.impl`, `last_change_seq 354255`, zero open blockers),
the complete handoff through `work-events` (62 events, `next_after` null) and
thread T325959 in full (5 messages, `last_seq 329708`, unchanged). Read
`review-2026-10-22T18-59-23Z.md` and `REVIEW-INPUTS-354242.json`.

### Three findings against my last claim, all correct, all absorbed

**1. I omitted a whole supplier.** All seven W333485 `bootstrap-347778`
paths were still at base bytes; I had composed the 24 diagnostics paths and
described that as composing both suppliers. **Corrected this claim**: all 7 are
now composed with digests verified, and the two suppliers are **provably
disjoint** — the intersection of their path sets is empty, so no
inter-supplier merge was needed. Against the current baseline the permission
supplier is 6 clean + 1 new file, **zero base mismatches**.

**2. `tokens.renew` is not the accepted W333485 contribution.** I called it the
supplier. It carries W275775 citations throughout. The accepted supplier adds
something different — an execution-envelope `permission` on acquisition — and
its own `_extended` **refuses renewal for an envelope-bearing token**: *"an
execution envelope has a fixed terminal deadline and cannot be renewed"*. So
renewal was never the route; the accepted mechanism **excludes** it for the
tokens it governs. **Withdrawn.**

**3. My renewal arithmetic was wrong.** I wrote that 900 × (1+4) covers
3600 + 900. `_extended` composes the new deadline from `taken =
control._now()` — the current clock plus seconds, not prior expiry plus
seconds — so four timely early renewals guarantee no such total. **Withdrawn.**

### What the permission supplier actually delivers, and where the gap really is

My last claim called the gap "one missing argument". That was imprecise. The
argument exists, is accepted, and is **plumbed end to end**:
`stage_execution.operations_from(permission_policy=…)` →
`single_worker.worker_operations(permission_policy=…)` → `_Composition` →
`permission, permission_eligible = self.permission_policy(control, stage,
job_execution)` → `prepared_workspace_governance(…, permission=…,
permission_eligible=…)` → `reserve` → `tokens.acquire(…, permission=…)`. And
`acquire` branches: `permission is None` → `seconds = LIFETIME_SECONDS` (900);
a permission given → *"choose a duration or an execution envelope, not both"*,
with the deadline taken from the envelope's `started_at < stop_at <
expires_at`.

**So what is missing is a CALLER.** Exactly one exists —
`authoring_enforcement.py:304` — and the native entry point
`stage_execution.factory(job_store, control_store)`, the `module:attribute`
`tools.job_manager` loads, calls `operations_from` **without** a
`permission_policy`. Default `None`, so `permission` stays `None`, so the
native acquisition takes 900 regardless of the Job's 3600. That is consistent
with the owner's recorded failure, and it is the demonstrated missing native
connection.

### The sizing rule needs no owner choice, and I am not returning one

`authoring_enforcement.permission_policy` refuses unless the limits equal the
Job's own admitted resolution rebuilt through `execution_limits.resolved`,
refuses if `provider_turn + ordinary_verification > total − cleanup`, and its
eligibility predicate refuses acquisition when `remaining < provider_turn +
ordinary_verification`. So **the accepted, independently reviewed mechanism
already defines one attempt's need** — one provider turn plus one verification,
with a positive cleanup reserve. That is not an invocation-count assumption I
would be adding, and my framing of it as a possible owner decision last claim
was premature. It is also **per attempt**, not cumulative: two stages are two
attempts with two independent envelopes, so it does not contradict
`revision-4/inputs/policy.json`'s "No product cumulative ceiling", which is
about the Job, nor make the 9000/9900 observation window a cap.

### The real remaining question, which is engineering and not policy

`tokens.py:384-385`, verbatim: *"The caller's independent execution controller
owns `stop_at`; the token retains permission through `expires_at` for the
required cleanup interval."* An envelope therefore needs a **deadline owner**.
Authoring has one — the controller persists its envelope and the policy reads
it back. **Native has none**, and the authoring policy is not transplantable:
it binds `packet['run_id']`, the persisted `KIND:run_id` record,
`packet['bounds']` and a HALT record, and its fixed 4800/60 is explicitly not a
native policy.

So the next concrete step is to identify or compose the **native** deadline
owner — which party owns a native stage's `started_at`/`stop_at`/`expires_at`,
derived from the Job's own resolved limits plus a cleanup reserve — and then
supply a native `permission_policy` from `factory`. **I did not establish
whether a suitable owner already exists in the serving loop or must be
composed**, and that decides the size of the remaining change.

### Verification

- **Joined 12-module gate on both suppliers composed: 1260 tests, 14.254s,
  OK, exit 0, zero skips.**
- **The permission supplier's own module: `tests.job_manager.test_serving_renewal`,
  14 tests, 0.213s, OK.** That file could not run at all before this claim
  composed it; it passing on the current baseline is what shows the permission
  contribution genuinely exists in this candidate rather than being cited as
  history.
- `COMBINED-MANIFEST.json`: **31 paths — 30 byte-identical to their supplier, 1
  three-way merged** (`attempts.py` at `e929d730…`, unchanged from last claim
  and independently re-verified by the reviewer).

### Still not done

No native deadline owner identified or composed and no native
`permission_policy` supplied, so the connection is still missing and the 900
ceiling still stands on the native path. No focused deterministic native
two-stage seam proof — the ceiling is established by reading the composed bytes
and by the owner's recorded failure, not by an executed reproduction at the
acquisition boundary. No proof of work beyond 900 for implementation and
review, no expiry/cancellation/cleanup or unknown-hold proof, no
replay/restart/no-revival proof. No new owner-produced expiry joined through
durable capture, `/7` status and the packaged report. No installation or
recovery operands.

### Boundaries and cost

No live instance, engine, provider or credential; no deployment, recovery,
start or migration; **no Git mutation** — version-control operations were reads
only (`show`, `archive`, `diff`). No shared-tree import or edit; the
composition lives only under `/tmp/w325959-354165`. Nothing was implemented, so
no expired-token revival, deadline reset or invented cap was possible. The
failed native episode and the `quickstart-a` / `sub-w321608-quickstart-1`
identities are untouched. Measured this claim: joined gate 14.254s, serving
renewal 0.213s, composition and mismatch verification well under a second,
plus unmeasured reading and hashing. Product tests executed: two runs, both in
the isolated root under M353196. Jobs 0; attempts 0; runtimes 0; provider calls
0; engine calls 0; credential reads 0; live invocations 0. Prior attributions
stay with their own Work.
