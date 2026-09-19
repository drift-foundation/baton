# Worker launch version mismatch silently waits on stdin

## 2026-09-17 — report and bounded research assignment

Owning v11 Work: W197661. Reviewer baton.codex, claim197664.
Source report: T197661/M197661, baton.prompt. No dossier existed at pickup.

**Reported:** in `/home/sl/baton-v12-instance-2026-09-17T20-29-21Z`, authority
`b6423787848c4a86a8c3a5df16b8e957`, Work `b6423787-W1`, Job
`codex-adapter-first`, attempt
`attempt-a79dc740be49f5f6bf1897e639eda2eecd3172854cc5507a4f8702fdcd7726db`,
provider image `sha256:2e222e4cf33ff7f52b2048ae1a9c0a2139707e36943328fdd8674b84937f2b13`
understands launch /1 and /2 but received /3 with job_execution and transport.
Container `5fbc769b2159` reportedly has matching labels, Python PID1 only,
empty logs/events, and PID1 waiting in anon_pipe_read. Manager reports runtime
running/exchange waiting, a published describe/work command and no receipt or
terminal state. Pure launch validation reportedly raises WorkerFault for the
unexpected members. These are prompt observations until independently checked.

**Scope:** bounded read/static diagnosis and correction plan, compatible provider
and integration image provenance, and explicit actionable mismatch behavior.
Do not start a model, build an image, restart/recover production, mutate its
store, stop/change the current runtime, release its claim, or run a blanket
test sweep. Preserve current and old-instance evidence. v11 remains coordination
authority. This is not evidence that the accepted shared-identity fix failed:
the prompt report explicitly identifies its own stale image selection.

**Operational note:** an initial guessed `manifest.json` at the instance root
does not exist. Supported evidence discovery identifies `deployment.json`,
`instance.json`, `distro/_internal/build-stamp.json`, and per-Job provider and
integration manifests instead. No missing file contents are inferred.

## 2026-09-17 — independent static diagnosis, claim197664

**Confirmed:** current `v12/worker/baton_worker.py:serve` catches WorkerFault
from `launched`, leaves `seen={}`, skips the exchange branch and calls
`read_frame(stdin)`. A correlatable invalid exchange launch therefore waits
for a stdin frame. Held-open empty stdin can block that read indefinitely.
No provider is dispatched. This is a current-source defect as well as a stale
image problem; this conclusion is static, not a production reproduction.

**Confirmed historical source:** the retained
`baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-149053/image-context/worker/baton_worker.py`
supports only /1 and /2 (`launched`, line550) and has the same fallback
(`serve`, line1881). A /3 document carrying job_execution and transport fails
member validation before schema diagnosis. Current source supports /1 through
/4 but still checks extra members before unknown schema, and its supported
version diagnostic omits /4. Its comment claiming version-first diagnosis is
inaccurate.

**Confirmed selected provenance:** current Job manifests select provider
`sha256:2e222e4cf33ff7f52b2048ae1a9c0a2139707e36943328fdd8674b84937f2b13`
and integration
`sha256:d739fefe6bf885db8ad79122611316f3fbe8b393fa4c821933388e8cd15e2533`.
Read-only Docker metadata reports creation times
2026-09-12T02:50:48.97652454Z and 2026-09-12T02:50:49.405741089Z, tags
baton-w71879-provider:candidate-149053 and
baton-w71879-integration:candidate-149053, entrypoints
python3 /opt/baton/dogfood_entry.py and python3 /opt/baton/integration_entry.py.
The historical independent review
`baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/review-2026-09-12T03-17-32Z.md`
binds those IDs to retained build/static custody, including 33 successful
commands. That historical acceptance does not establish /3 compatibility.
This claim inspected retained source and metadata, not newly extracted image
contents.

The fresh distro build stamp names dirty source commit
e486652c4ddebfb696e030b4b867e914248db542 and 25 changed entries. It describes
the manager distro, not worker image bytes. **Open:** no replacement compatible
provider/integration digest is proved. Current Dockerfile.integration requires
PROVIDER_BASE and recopies worker/adapter/integration sources, so compatible
provider ancestry alone cannot prove integration payload compatibility. Bind
both final image payloads to the selected manager launch contract.

**Coverage gap:** test_worker_entry.py's
`test_a_latched_launch_fault_answers_once_and_is_not_an_answer` supplies a
stdin request and checks the historical correlated fault. It cannot expose
the held-open empty-stdin exchange startup. Preserve valid one-shot behavior.

**Trust boundary:** worker_manager/exchange.py treats empty exchange as waiting;
its observation contract delegates termination to runtime observation and
freeze/intake gates. Do not forge exchange receipts/terminals, infer completed
work from exit, or trust invalid launch fields to execute providers or choose
arbitrary filesystem destinations.

**Proposed, awaiting selection:** diagnose unsupported schema before member
checks, listing all supported versions. Invalid exchange/future launches must
fail promptly without reading indefinitely from stdin. Select an explicit
startup-failure channel and compatibility rule for legacy one-shot faults.
Nonzero exit plus bounded sanitized stderr is a candidate, not an accepted
new wire contract. Manager observation must attribute failure to the exact
attempt without accepting diagnostics as work results. Image selection must
use digest-bound compatibility evidence, not mutable tags or manager stamps.

**Operational findings:** guessed worker.py/entry.py, manager/worker_entry.py
and tools/worker_image_build.py were absent. Actual sources are
v12/worker/baton_worker.py, v12/python/src/baton_v12/worker_manager/worker_entry.py
and v12/python/tools/worker_image.py. Config.Labels was absent in Docker's
template; metadata query without it succeeded. These are discovery errors,
not permission failures. No missing contents were inferred.

Verification: zero test/model/build/runtime execution; read/static analysis
and metadata-inspection wall time unmeasured. Live attempt and claim, stores,
containers and old-instance evidence remain untouched.

## 2026-09-17 — owner decision PINNED, and revalidation at implementation start

**Owner ruling (baton.slaw, seq197734, claim197733):** implement PLAN steps 1–3
of this dossier, then independent review. Prevent invalid exchange/future
launches from blocking on stdin; preserve correlation and supported one-shot
behavior; use focused deterministic verification. Image builds, deployment and
recovery remain separate Work. The operator confirmed the affected container
exited at 2026-09-17T21:38:49.851872871Z, `running=false`, `exit=137`, and that
the manager and publisher are stopped; the unresolved attempt and its evidence
are preserved.

**Revalidated at implementation start, claim197743** — every static claim above
still holds against the current tree:

- `v12/worker/baton_worker.py:serve` catches `WorkerFault` from `launched`,
  leaves `seen={}`, cannot reach the exchange branch (`seen.get("transport")`
  is `None`) and enters `read_frame(stdin)`. Confirmed.
- `launched` compares MEMBERS before it compares the SCHEMA, so an unknown
  version is refused by naming `/1`'s member set. Its own comment claims the
  opposite ("the refusal names the version rather than the members").
  Confirmed inaccurate.
- The supported-version sentence names `/1`, `/2` and `/3` and omits `/4`,
  which this same file reads. Confirmed.
- The retained September-12 image source at
  `prepared-149053/image-context/worker/baton_worker.py` defines only
  `LAUNCH_SCHEMA` and `EXCHANGE_LAUNCH_SCHEMA` and has the same
  `read_frame(stdin)` fallback. Confirmed.
- `test_worker_entry.test_a_latched_launch_fault_answers_once_and_is_not_an_answer`
  drives an INVALID `/2` document and expects the stdin correlated fault. It is
  the invalid-exchange case this ruling supersedes, not the supported one-shot
  behavior the ruling preserves.

### The startup-failure contract, as selected

**1. The schema is diagnosed FIRST.** `launched` refuses an unrecognised
version by naming the version and listing EVERY version this worker reads —
`/1`, `/2`, `/3` and `/4` — before any member comparison. Member, transport and
value checks are unchanged and follow, for recognised versions only. A future
manager's document then gets the sentence that says "wrong generation" instead
of a member list that reads like a corrupt file.

**2. `serve` waits on stdin only for the generation that speaks stdin.** A
launch document that is correlatable and fails validation is handled by its
DECLARED schema:

- declared `baton.worker-launch/1` — UNCHANGED. Latch the fault, answer exactly
  one correlated frame through the framing loop, exit `1`. `/1` is the
  diagnostic and test transport `worker_entry.converse` drives over stdin
  (`launch.py:97`), so a manager really is writing frames there, and the
  correlated fault is the better diagnostic.
- any other declared schema — `/2`, `/3`, `/4`, or a version from another
  generation. The manager for those speaks the FILE EXCHANGE, so nothing will
  ever be written to this container's stdin. The worker writes ONE bounded,
  sanitized, single-line diagnostic to stderr and exits `3` immediately.
  Nothing is read from stdin, nothing is written to stdout, no exchange
  document is written and the agent is never reached.

**The declared `schema` is the only member trusted from an invalid document,
and it is trusted for exactly one decision: which failure channel to use.** It
never selects a transport, an execution, a filesystem destination or a peer. A
document whose `schema` member is missing or is not text is not `/1`, so it
takes the prompt-failure path — the safe direction, because the cost of
failing fast where a manager would have written frames is a degraded
diagnostic, and the cost of waiting where nobody will write is the hang this
Work exists for.

**3. Exit `3` is new and is this program's own status, not a wire contract.**
`0` clean, `1` latched-and-answered or an abnormal framed ending, `2`
uncorrelated (nothing could be answered), `3` refused to start and said so only
on stderr, `4` the exchange sequence is accepted and unfinished. Nothing in the
manager maps worker exit codes to meanings — `worker_entry` compares status to
zero and `oci.observe` does not read it at all — so `3` adds an operator-visible
distinction without changing any manager rule.

**4. stderr is a diagnostic surface and NOT a new protocol event.** The manager
already carries bounded worker stderr (`worker_entry.MAX_STDERR`, 4096) and
already records the runtime's ending; nothing parses this sentence, and no
receipt, state or terminal document is improvised from an invalid launch. The
diagnostic is bounded to 1024 characters and reduced to one line of printable
ASCII, so a hostile launch document cannot forge framing, inject terminal
escapes or write an unbounded durable log.

**What this does NOT change.** Every correlation and trust check
(`read_launch`, `session_of`, `bind`, the entitlement rules), the valid
one-shot path, the exchange path, `serve_exchange`'s own codes, the manager's
observation vocabulary, and the rule that transport is selected only by a
VALIDATED document. No manager source change was needed or made.

**Still open and deliberately not taken here:** no compatible provider or
integration image digest is established by this claim, and PLAN step 4's
digest-bound image preparation and step 5's operator stop/fencing/recovery
remain separate and unselected. A corrected worker does not make the selected
September-12 pair compatible; it makes the incompatibility say so in under a
second instead of waiting forever.

## 2026-09-17 — independent source review, claim197850

The five-file candidate is accepted as a source correction; see
review-2026-09-17T22-10-41Z.md and REVIEW-EVIDENCE-197850.json for exact bytes,
229 passing deterministic tests, operational scope/accounting findings and
limits. Source acceptance does not authorize images or deployment.

**Clarification superseding overly broad prose above:** /3 and /4 may use null
transport, so later schema does not prove an exchange channel. The selected
implementation conservatively refuses invalid non-/1 documents on stderr;
validated null-transport behavior remains unchanged. worker_entry.MAX_STDERR
does not establish automatic production exchange stderr collection. The
diagnostic is emitted to container stderr; production collection was not
demonstrated. The implementer's reported engine/image builds cross the owner's
separate-build boundary and are returned for owner disposition, not silently
treated as additional execution authority. Cumulative accounting needs an
append-only correction for the reported confirmation run and reversal costs;
unknown historical seconds are not a new verification gate.

## 2026-09-17 — source candidate ACCEPTED; step 4 selected. Owner seq197881

**Owner ruling (baton.slaw, seq197881, claim197880):** accept the five-file
source candidate of `review-2026-09-17T22-10-41Z.md`; pin this decision in
FINDING and update PLAN. Record the prior excluded Docker executions and
correct the incomplete timing **without rerunning for accounting**. Address the
non-blocking pipe-cleanup and documentation findings. **Select PLAN step 4:**
prepare compatible provider and integration images with immutable base, exact
source/build provenance and final image digests; necessary image builds and
bounded deterministic container smoke checks are authorized, with no live
models. Return changed files and image evidence for independent review.
Production deployment, restart, resubmission and recovery remain separate; the
stopped instance and unresolved attempt are preserved.

Independent review `review-2026-09-17T22-10-41Z.md` (claim197850, sha256
`10cce0abb1cffb380fd4d1e9e0e5cff1197964023a22ebf49d1119fb9712c01b`) accepted
the bounded source correction with no blocking defect, bound all five hashes
and ran 229 deterministic tests.

### Clarification of the 2026-09-17 pinned contract — review finding 4

The startup-failure contract pinned above is **unchanged in behaviour** and its
DESCRIPTION was wrong in one respect, which this entry corrects rather than
rewrites.

That entry said "every later generation ... speaks the file exchange". **That
is false:** `/3` and `/4` carry the transport as a MEMBER and may validly name
none, in which case a valid document of either version uses the framing loop —
which the code always did and `test_a_supported_NULL_TRANSPORT_launch_still_uses_the_framing_loop`
pins.

**What the decision actually rests on**, and how it should be read: it is a
CONSERVATIVE REFUSAL-CHANNEL POLICY. When a launch document has been refused,
the member that would say which channel its manager intended is part of the
document just refused, so it cannot be relied on. `/1` has no transport member
at all and is therefore unambiguously the framing-loop generation. For every
other declared version the worker cannot tell, and of the two ways to be wrong
— waiting on a stdin nobody writes to, or reporting on stderr — only the first
is unbounded. The comments in `baton_worker.py` now say this.

**And `worker_entry.MAX_STDERR` is not what the earlier entry implied.** It is
the FRAMED transport's own collection bound and is not evidence that the
file-exchange path imports a container's stderr. On the exchange path the
diagnostic is an operator-readable container fact — the engine's log and its
recorded ending — which is exactly what the reported incident had none of. No
production collection of it is claimed.

### A measured limit: the integration entry is silent, though it does not hang

`integration_entry.main`'s non-managed branch catches `WorkerFault` from
`launched` and `return`s `2` with no diagnostic at all. Review finding 4 named
this from reading; the step-4 smoke below **measured** it: the integration
candidate given a `baton.worker-launch/5` delivery exits `2` with an EMPTY
stderr, while the provider candidate under the identical delivery exits `3`
with the bounded sentence.

It does not hang, so the defect this Work corrects is not present there; what
is missing is the diagnostic. **This is a recorded follow-on and is deliberately
not taken here** — the owner's selection for this claim is the image
preparation, and widening a bounded correction into a second entrypoint without
a ruling is how a bounded correction stops being one.

### Accounting correction for claim197743 — reconstructed, NOT re-measured

Review finding 2 is right. `EVIDENCE-197743.json`'s "about 116.5 seconds"
omitted two Docker-executing runs. Per the owner's instruction nothing was
rerun to settle this; the figures below are reconstructed from the outputs
those runs actually printed.

Docker-executing runs in claim197743 — the image gate builds a real image from
`v12/worker` and runs real containers:

| run | unittest | wall | outcome |
| --- | --- | --- | --- |
| five-suite adjacent set (first attempt) | 75.046s | 75.328s | **1 failure** — the superseded `/2` container case; NOT previously reported |
| `test_worker_container` alone | 31.103s | 31.314s | OK |
| six-suite adjacent set | 84.214s | 84.534s | OK |
| confirmation rerun, three worker suites | 31.367s | 31.615s | OK — reported in pass197848 but omitted from the total |

Local-only: `test_worker_entry` 0.009s and 0.010s, `test_exchange` 0.410s and
0.421s. Reproduction probes: the PRE-correction reversal blocked four cases at
a 3.0s bound and one at 1.0s, about 13.0s measured inside the script; the
post-correction runs are about 0.001s each and were run four times.

**Corrected claim197743 total: about 235.6s measured** (≈237s wall), against
the ≈116.5s reported. The difference is the unreported failed first run and the
confirmation rerun. This is an accounting correction and not a budget gate —
owner ruling 2026-09-14 stands.

### Step 4 — the compatible pair, prepared and smoked

Package: `prepared-197885/`. Shape taken from the independently accepted
`prepared-149053/build_images.py`, which was reviewed for exactly this act.

- **Immutable base**
  `sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4`
  — the already-validated provider installation (runtime 2.1.247, trust store,
  `python3`, `git`) that `prepared-149053` bound and whose
  `provider-installation.json` is copied beside the script unchanged.
  Reinstalling any of it would mint a second unreviewed provider installation
  for one deployment.
- **Builds** are `--pull=false --no-cache --network none --platform linux/amd64`
  over that digest, so the only new bytes are this repository's own reviewed
  source. `Dockerfile.provider` is COPY-only; the integration image uses the
  tree's own `worker/Dockerfile.integration` with `PROVIDER_BASE` set to the
  same immutable digest, as `prepared-149053` did.
- **Frozen context**, `image-context-manifest.json`, proved twice before the
  build: against itself and against the reviewed tree. Five of the eleven
  entries are byte-identical to the September-12 context —
  `dogfood_entry.py`, the control schema, both `source_profiles` modules and
  `Dockerfile.integration` — so what changed is exactly the worker, the
  adapter and the three integration modules.
- **Final digests.** provider
  `sha256:35f36286cb1653712dc3a62b3e5ba9b02d06e04ac4306a77e31a1c11777f0e06`,
  integration
  `sha256:dac354d89aa879fe0b802bda48f04d0b7e52c95c92fc22a97d84f6e1d23b4407`.
  **These are CANDIDATES.** Selecting a digest is a separate deployment act
  that nothing in this claim performs or claims.
- **Payload bound to the launch contract, both ways.** Every image-delivered
  file was read out of a NEVER-STARTED container and its bytes compared:
  `/opt/baton/baton_worker.py` is `sha256:8a5f4895ff7f…` in BOTH images — the
  exact accepted corrected source. Base-layer ancestry is an ordered prefix
  match, platform `linux/amd64`, user `65532:65532`, the expected entrypoints,
  and no credential environment override.
- **Bounded deterministic smoke, no model, no credential, no network.** In a
  real container under the manager's own `oci.RESTRICTIONS`: both images report
  `SUPPORTED_LAUNCH_SCHEMAS` as `/1`–`/4` and both VALIDATE a `/3` composed by
  the manager's own `launch.launch_document` with limits resolved and sealed by
  the manager's own functions. The provider image's real entrypoint answered
  one `describe` over the framed channel — `describe` dispatches no provider by
  contract — correlated, exit 0. And under a `/5` delivery with stdin held open
  and empty for the whole run, the provider image exited **3** with zero stdout
  bytes and the bounded sentence on stderr: **the reported incident's exact
  shape, at the artefact, ending immediately instead of waiting.**

**What this does NOT establish.** The pair is not selected, not installed, not
deployed. No Job was submitted, no attempt retried, no production store or
runtime touched. The old September-12 pair remains incompatible with the
manager's launch contract and is preserved as evidence, as are the stopped
instance and the unresolved attempt.

## 2026-09-17 — step4 review corrections, claim197955

**Confirmed, superseding smoke claims above:** all six retained smoke vectors
append confinement flags AFTER IMAGE, making them application arguments rather
than Docker options. The reported manager confinement/no-network properties
were not applied by those flags. The purported held-open provider check uses
subprocess.run(input=b""), which closes stdin; it proves an EOF case instead.
No held-open integration case exists in the helper. See
review-2026-09-17T22-27-16Z.md and REVIEW-EVIDENCE-197955.json for exact evidence
and the selected correction. Neither finding asserts observed model/network
activity. Preserve all historical outputs and fix the helper/smoke in a new
episode; source acceptance remains, image acceptance is withheld.

The corrected author accounting is recorded history. New prospective build
authority does not retroactively authorize earlier excluded runs. Reviewer
claim197850 also withdraws its local-only/no-engine characterization of the
lost-result invocation that included the full tools.test_execution_limits:
the new handoff identifies that module as engine-executing. Exact execution
and duration of that invocation remain unknown; its processes were previously
confirmed ended. No rerun is requested for accounting.

## 2026-09-17 — step-4 smoke evidence CORRECTED. Claim197975

Independent review `review-2026-09-17T22-27-16Z.md` (claim197955, sha256
`d1e4fccebe2b7a503475fb47422c874e5e6a8f5a7c331a59771f7801d7ceb4db`) withheld
step-4 image acceptance on two blocking evidence findings. Both are correct,
both were verified against the previous episode's own retained vectors, and
both are corrected here. **The source acceptance of claim197850 stands and is
untouched; nothing in this entry changes a product file.** No image was
rebuilt: the two immutable candidates prepared in claim197885 are reused
exactly.

### R1 — the confinement flags were application arguments. SUPERSEDED

`prepared-197885/build_images.py:confined` appended the restriction table to
the whole argv its callers had **already ended with the image reference**, and
`docker run [OPTIONS] IMAGE [COMMAND] [ARG...]` makes everything after the
image the container's own argv. Verified in that episode's retained
`result.json`: all six smoke vectors put the image before `--cap-drop` —
provider validation has the image at index 7 and `--cap-drop` at index 10;
provider refusal has the image at index 5 and `--cap-drop` at index 6.

**Therefore these claims about claim197885's smoke are WITHDRAWN:** that its
containers ran with no network, a read-only root, dropped capabilities,
`no-new-privileges`, or pid/memory/cpu bounds. They did not. The image's own
`USER 65532:65532` still applied, because that is baked into the artefact, and
it is not evidence of anything else. Nothing here alleges that model or network
traffic actually occurred — the containers ran `python3 -c` over a mounted
document and the entrypoint over a refused one — but an unproved confinement
claim is withdrawn rather than argued down.

**The correction**, in `corrected-197975/smoke_images.py`: the vector is
composed from three separate operands — options, image, arguments — so the
image cannot be handed to the composer in the middle of its own options; the
restriction table comes from the manager's own `oci.RESTRICTIONS` with **no
fallback at all**, and a preparation that cannot read it refuses; a focused
vector regression runs **before any container starts** and fails the whole
preparation, checking that every restriction precedes the image, that only the
application arguments follow it, that the image is named once, that an empty,
malformed or non-flag table and a mutable tag are each refused, and that the
superseded shape is the one that fails; and the confinement is then asserted
from the **engine's own `HostConfig` for the exact container**, because a
string containing the right flags is an argument about a string.

Measured on all six corrected containers: `NetworkMode` `none`,
`ReadonlyRootfs` true, `CapDrop` `["ALL"]`, `SecurityOpt`
`no-new-privileges`/`label=disable`, `PidsLimit` 512, `Memory` 2147483648,
`NanoCpus` 2000000000, `User` `65532:65532`.

### R2 — `input=b""` was an end of input, not a held-open stdin. SUPERSEDED

`subprocess.run(input=...)` and `Popen.communicate()` both close the writer —
`_communicate` closes stdin whenever `input` is falsy, confirmed by reading
CPython's own source — and `--interactive` does not keep a producer's pipe
open. The previous episode's "held open" run therefore handed the container an
immediate EOF, which a worker is entitled to answer by ending.

**Therefore the claim that claim197885 measured the candidate exiting while
stdin remained open is WITHDRAWN.** What it measured is an EOF smoke. The
`3` it recorded is still a true exit status for that input, and the previous
episode's outputs are preserved and are to be read as EOF smoke.

**The correction** owns the pipe: `Popen` with an explicit writer that is never
written to and never closed until the container's own exit has been observed,
`communicate` never called, both streams drained by threads using `read1` so a
bounded answer from a still-running container is actually visible, one bounded
observation, and then stop, remove and a **confirmed positive absence** from
the engine for the exact named container — because killing a Docker client does
not prove its container ended.

**And a negative control, because the mechanism has to be shown to work.** An
invalid `baton.worker-launch/1` document, whose preserved contract is to latch
and WAIT for a frame, was **still running at 15.013 s** with the writer held
open, and was then stopped, removed and confirmed absent. If it had ended, no
held-open claim beside it would have been worth anything.

### What the corrected smoke measured

Against the existing immutable candidates, no rebuild, no model, no credential,
no network, every container confined and proved so from the engine:

| run | result |
| --- | --- |
| negative control, invalid `/1`, held open | **still running at 15.013 s**, then stopped, removed, absent |
| provider, `/5`, **genuinely** held-open stdin | **exit 3** at 0.200 s, zero stdout bytes, the bounded sentence on stderr |
| integration, `/5`, held-open stdin | exit 2 at 0.150 s, **empty stderr** — the recorded limit, now measured under a held-open writer too |
| provider reads | `/1`–`/4`, and validates the manager's own `/3` |
| integration reads | `/1`–`/4`, and validates the manager's own `/3` |
| provider `describe` | correlated answer, exit 0, under the manager's send-then-close shape — labelled as a conversation and NOT as a held-open run |

The candidate digests are unchanged and remain **candidates**: provider
`sha256:35f36286…`, integration `sha256:dac354d8…`. Nothing is selected,
installed or deployed. The two never-started inspection containers from
claim197885 are untouched; every container this correction created was removed
and confirmed absent.

### Accounting

This correction cost about 108.6 s measured: three runs of the corrected script
within this claim — a first pass without the `describe` case (16.010 s,
complete), a second that failed on a blocking drain and left no container
behind (76.2 s, confirmed), and the final complete run (16.260 s) — of which
only the final output is retained, plus 0.13 s of local tests. Nothing was
rerun for accounting.

The reviewer also **withdrew** claim197850's "local deterministic only"
characterization of its earlier lost-output invocation, having identified that
it included the full `tools.test_execution_limits` module, which this record's
own evidence labels engine-executing. Its duration and exact activity remain
unknown; the prior process-exit observation stands. No retrospective run is
warranted, and prospective build authority does not reach backwards.

## 2026-09-17 — review198033: R1/R2 observations accepted; R3/R4 remain

The corrected vectors and retained container inspections establish confinement
and a real held-open writer. All19 checked hashes match. However, gone() treats
any inspect error as positive absence: a fake daemon-unavailable response
reproduces absent=true. Exceptions after launch bypass cleanup, and pre-launch
remove(name) does not prove ownership. The helper also permits complete=true
without asserting the four principal refusal/validation outcomes. These facts
supersede claims that the helper guarantees exact cleanup and successful smoke
acceptance on all paths, not the successful historical outputs themselves.
See review-2026-09-17T22-39-55Z.md and REVIEW-EVIDENCE-198033.json. Correct R3/R4
with fake-engine tests and retained-result replay in a new preserved episode;
no rebuild or broad rerun. Source acceptance stands; final step4 acceptance
is withheld, and production remains untouched.

## 2026-09-17 — smoke helper's own failure paths corrected. Claim198054

Independent review `review-2026-09-17T22-39-55Z.md` (claim198033, sha256
`a4b2fc553990b61410c99eebc0fcb2bb3b14c6ae0022c28b0686996c311b742f`) accepted
the R1/R2 corrections and the observations `corrected-197975` recorded, and
withheld final step-4 acceptance on two further findings about the helper
itself. Both are correct and both are corrected in `corrected-198054/`.
`prepared-197885/` and `corrected-197975/` are preserved unchanged — verified
file by file against their own recorded hashes. No image was rebuilt and no
product file changed; the claim197850 source acceptance stands.

### R3 — absence was inferred from a failure. CORRECTED

Measured on this engine, and it is worse than a style point: `docker inspect`
exits **1 with `[]` on stdout** both for an object that does not exist and for
a daemon it cannot reach. Only the stderr prose separates them —
`error: no such object: <name>` against
`failed to connect to the docker API …`. The previous `gone()` answered
`absent=true` for every non-zero status, so **a daemon outage during cleanup
would have been recorded as "removed, confirmed absent"**. `remove()` ignored
the stop and rm statuses. `held_open` had no enclosing `finally` after `Popen`,
so a failed write, inspection or wait skipped removal entirely. And it opened
by removing whatever held the name — deleting an object whose ownership it had
never established.

The correction: absence is **positive or it is `uncertain`**, decided by the
manager's own `oci._absent_prose` imported rather than copied, so a sentence
about another identity is not this container's absence either; a name already
taken is a **refusal** rather than something to delete; the container is owned
by the **ID the engine reports after launch** and every later act names that
ID; cleanup lives in a `finally`, retains the engine's own answers for stop,
rm and the final look, and attaches itself to a primary failure instead of
replacing it.

Fifteen fake-engine checks run before any container starts and fail the whole
preparation: matching absence, daemon unavailable, permission denied, a foreign
absence sentence, present, two objects for one identity, non-JSON, claiming a
free/taken/unknown name, cleanup proved, cleanup refused on a foreign sentence,
cleanup not claimed under uncertainty, retained engine answers, and an engine
that cannot be run at all.

### R4 — `complete` only required that the runs ended. CORRECTED

It never asserted exit 3 with an empty stdout and a bounded diagnostic for the
provider's refusal, exit 2 for the integration's, the supported/validated
payloads of either reads run, or the negative control's state **as the engine
sees it** rather than as a client polled it. Four of the six runs could have
ended in a traceback and the preparation would still have said complete. The
results were right; the criterion was not.

`judge` is now the single acceptance predicate — **30 checks** across the six
runs, including every confinement field claimed (network, read-only root,
`CapDrop`, both security options, pids, memory, cpu, both tmpfs mounts, user),
the cleanup proof, the negative control's engine-reported `State.Running`, the
diagnostic's shape and the four generations named in it, both reads payloads,
and the correlated `describe` answer.

**And the criterion is itself proved.** A judgement regression replays the
retained `corrected-197975` results — enriched with the container inspections
that episode retained beside them, which is where the negative control's
`State.Running` lives — and requires them to **pass**; then applies **twenty
mutations** and requires each to be **refused**: provider exiting 1, writing to
stdout, losing its diagnostic, losing one version from it, ending in a
traceback; integration exiting 3 or speaking; a reads payload missing a
generation, not validating the `/3`, or failing; a negative control that ended
or that the engine says is not running; a refused `describe` or one for another
session; confinement without a memory bound, with a network, with a writable
root, without the tmpfs; a container left behind; and a held-open run
relabelled a conversation. Two more require that a missing run is not a pass.

### What the corrected helper measured

Same immutable candidates, no rebuild, no model, no credential, no network;
six confined containers, each claimed by name, owned by ID and proved absent
afterwards by the engine's own sentence:

| run | result |
| --- | --- |
| negative control, invalid `/1`, held open | client poll `None` **and the engine reports `Running: true`** at 15.014 s |
| provider, `/5`, held-open stdin | **exit 3** at 0.150 s, zero stdout, the bounded one-line diagnostic naming all four generations |
| integration, `/5`, held-open stdin | exit 2, zero stdout, empty stderr — the recorded limit |
| provider / integration reads | exit 0; `supported` is `/1`–`/4` and `validated` is the manager's `/3` members |
| provider `describe` | one correlated answer, exit 0, under the send-then-close conversation shape |

Digests unchanged and still **candidates**: provider `sha256:35f36286…`,
integration `sha256:dac354d8…`. Nothing selected, installed or deployed. The
two never-started inspection containers from claim197885 remain untouched.

### Accounting

About 33 s measured this claim: one run that failed in its own absence
regression because the fixture named a different identity than its fake absence
sentence — the rule refusing a foreign sentence, which is the rule working
(0.202 s) — and the complete run (16.198 s), plus the package and
untouched-ness verification. Nothing was rerun for accounting. Work cumulative
about 485 s.

## 2026-09-17 — review198094, remaining creation-ownership defect

All46 local regression predicates pass and all29 checked hashes match. R4's
principal result validation and R3's absence classification/finally handling
are corrected. R3's ownership claim is still overstated: held_open falls back
to stop/rm by name if owned_id is missing, and otherwise adopts the ID from a
late name inspection without creation proof. A read-only free-name check cannot
reserve that name. A fake-process reproduction of the actual function confirms
cleanup targets the name after startup failure with owned_id null. This
supersedes the claim that every destructive cleanup is restricted to proven
ownership. See review-2026-09-17T22-50-56Z.md and REVIEW-EVIDENCE-198094.json.
Correct only the remaining creation-ownership path and its focused regressions;
preserve existing episodes and successful smoke facts. No rebuild or broad
rerun is needed. Source acceptance stands; final step4 acceptance is withheld.

## 2026-09-17 — container ownership proved at creation. Claim198115

Independent review `review-2026-09-17T22-50-56Z.md` (claim198094, sha256
`e392f9ee88fe708f3d0634386e214fb2506ae2f18a3690f0550d4994be873113`) accepted
the absence classifier, the `finally` cleanup and R4's principal result checks,
replayed all 8 + 15 + 23 regression checks independently, and withheld final
step-4 acceptance on one remaining ownership defect. It is correct and is
corrected in `corrected-198115/`. All three prior packages are preserved
unchanged — verified file by file against their own recorded hashes (15, 14 and
24 files, no drift). No image rebuilt, no product file changed.

### The remaining R3 — a name lookup is not creation ownership. CORRECTED

`corrected-198054`'s `held_open` ended with
`released(found["owned_id"] or name, …)`, and `owned_id` was only assigned by
an inspection that ran **after** the observation. A failure before that point —
the reviewer drove a `BrokenPipeError` on the conversation write — left it null
and the `finally` then **stopped and removed whatever currently held the
name**. `claim_the_name` was a read-only preflight, not a reservation: another
container can take the name between the look and the launch, and this run would
then fail and destroy the winner. Even the ordinary path adopted the id a name
lookup returned without proving this invocation had created it.

**Ownership is now taken at creation, atomically.** Every run passes
`--cidfile` at a private per-run path that does not exist beforehand. Measured
on this engine: the id is written as part of creating the container, and a
second run against an existing cidfile is refused outright —
`container ID file found, make sure the other container isn't running`. An id
read out of that private path was therefore created by **this** invocation,
which is exactly what a name lookup can never establish.

**And unproved ownership is never destructive.** If the cidfile is absent,
unreadable or not an id, the run issues **no stop and no rm at all**, records
the exact uncertainty and the name it had asked for, and leaves it for an
operator. Every later inspection names the owned id and is checked to be about
it. The name preflight survives as a convenience and is labelled as one.

### The orchestration regression — at the boundary the defect lived on

The previous episode's fake-engine tests exercised the helper functions; this
defect lived in how the orchestration used them. Fourteen checks now drive
`held_open` itself with fake process and engine seams, before any container
starts:

- a name stolen after a free preflight — the launch fails, no id is ever
  written — issues **zero** stop or rm, refuses rather than reporting success,
  and never names the winner in any command;
- a write failure after an **owned** creation cleans up exactly two commands,
  both naming its own id;
- an engine that cannot be inspected after an owned creation still cleans its
  own id and does not claim the cleanup was proved;
- an uncertain creation adopts nothing and refuses;
- and an empty, prose, short or missing cidfile is `unproved` while a written
  one is ownership.

The judgement regression gains two mutations for the same property: ownership
that was never proved, and a cleanup naming a container this run did not
create. Both are refused. The acceptance predicate is now **36 checks**.

### What the corrected helper measured

Same immutable candidates, no rebuild. Six containers, each created with a
private cidfile, **owned by the id the engine wrote there**, inspected by that
id and released by that id, every one proved absent afterwards by the engine's
own absence sentence — and in every case the cleaned id is the created id:

| run | result |
| --- | --- |
| negative control, invalid `/1`, held open | client poll `None`, engine reports `Running: true` |
| provider, `/5`, held-open stdin | **exit 3**, zero stdout, the bounded one-line diagnostic |
| integration, `/5`, held-open stdin | exit 2, silent — the recorded limit |
| provider / integration reads | `/1`–`/4`, and the manager's `/3` validated |
| provider `describe` | one correlated answer, exit 0 |

Regressions: 8 vector, 15 absence, 14 orchestration, 25 judgement; verdict 36
predicates. Digests unchanged and still **candidates**. The two never-started
inspection containers from claim197885 remain untouched, and the six cidfiles
are retained under `corrected-198115/owned-ids/` as the ownership evidence.

### Accounting

About 33 s this claim: one run that failed in its own orchestration regression
because the fixture refused the *preflight* inspection too, so no container was
ever created and the case tested nothing (0.202 s), and the complete run
(16.194 s), plus the preservation checks. Nothing rerun for accounting. Work
cumulative about 518 s.

## 2026-09-17 — independent final step4 acceptance, claim198155

Review-2026-09-17T23-00-20Z.md accepts the creation-ownership correction and
immutable provider35f36286/integrationdac354d8 pair for the bounded launch
compatibility evidence. All62 independent fake-engine/replay checks, all36
retained-result predicates and all35 hashes pass. Current image metadata agrees
with retained provenance. Six cidfile IDs agree with owned and cleanup IDs.
See REVIEW-EVIDENCE-198155.json and REVIEW-IMAGES-198155.json for exact bindings.
This supersedes the remaining R3/step4-withheld status, preserving all prior
findings and flawed evidence as history. No image deployment, production retry
or recovery is selected here. The silent integration exit2 limitation remains
recorded; pass baton.decide for the next bounded owner disposition.

## 2026-09-18 — step 4 ACCEPTED; the next bounded selection PINNED. Owner seq198635

Independent review `review-2026-09-17T23-00-20Z.md` (claim198155, sha256
`55caf0ad65d649a5fabc5b7d34836a65e05391742682c0b08b62fefd064b3d03`) **accepted
the step-4 preparation and its bounded image compatibility evidence**, binding

- provider `sha256:35f36286cb1653712dc3a62b3e5ba9b02d06e04ac4306a77e31a1c11777f0e06`
- integration `sha256:dac354d89aa879fe0b802bda48f04d0b7e52c95c92fc22a97d84f6e1d23b4407`

both from immutable base `sha256:0697b659…`. It ran 62 independent local
regression checks, re-evaluated all 36 acceptance predicates on the retained
results, matched all 35 package/source hashes, confirmed each of the six
cidfiles against its owned and cleanup id, and matched current read-only image
metadata to the retained records. It explicitly does **not** claim full `/4`
session reuse or any live provider completion, and the integration
non-managed silent `exit 2` remains recorded.

**Owner ruling (baton.slaw, seq198635, claim198634) — PINNED:** accept step 4.
Pin the next bounded selection in FINDING and PLAN, then:

1. **Prepare ONE reproducible deployment packet** binding the installed
   manager, the accepted image IDs, the configuration and the required
   directories.
2. **In a SEPARATE DISPOSABLE INSTANCE**, exercise the real installed
   coordination and worker path with a **deterministic fake provider**, through
   **task receipt, candidate collection, independent review and
   report-and-hold**.
3. **Label any fixture image differences explicitly**; do not claim live
   provider coverage.
4. Bounded local builds and container execution for this smoke are authorized.
   **No live models and no broad suites.**
5. Return the packet and its evidence for independent review.
6. **Preserve the stopped production instance and the unresolved attempt**; no
   production restart, recovery or resubmission.

### What the packet has to bind, established by measurement

- **The installed manager.** `v12/python/build/out/distro/baton-v12-stack`,
  version `12.0.0`, launcher sha256
  `04d69e37a6e99621b5e7342aa6d6dfbdd7dcae0624301f827abf258c66c89e6c`, built
  2026-09-17T14:29:28 local, build stamp commit
  `e486652c4ddebfb696e030b4b867e914248db542` **dirty, 25 changed entries**,
  Python 3.13.7, `Linux-6.17.0-41-generic-x86_64-with-glibc2.42`. This is the
  same build the stopped production instance runs.
- **A provenance caveat that must travel with it, stated as the inference it
  is.** That build was made from a DIRTY tree, and W194457's
  shared-workspace-identity candidate — still awaiting its own independent
  review — has file modification times EARLIER than the build, so the bundle
  very likely embeds those unreviewed manager bytes. I could not prove it
  either way from the artefact: a byte search of the launcher and
  `base_library.zip` for `declared_identity_mapping` and
  `SUPPORTED_IDENTITY_MAPPING` found nothing, **and neither did the control** —
  `establish_line_access` and the historical `_provision_line_access` are also
  absent from a raw search, because module bytes live compiled inside the PYZ.
  The method cannot answer the question and is recorded so nobody repeats it.
  This claim's accepted product correction is NOT affected: it lives in
  `v12/worker/baton_worker.py`, which travels in the IMAGES and not in the
  manager bundle.
- **The accepted image IDs**, above, unchanged and unselected until an owner
  selects them.
- **The configuration and required directories**, from the bootstrap input
  document (`baton.v12.stack-bootstrap/1`) plus its deferred `workers` section,
  which is where `image_digest` is actually bound — the stopped instance's
  `deployment.json` still names the stale `sha256:2e222e4c…` there, which is
  the original incident's selection.

### The fixture-image difference this smoke will have to label

The accepted provider image's entrypoint injects the REAL adapter
(`dogfood_entry.py` → `ClaudeAgent`). A deterministic fake provider is a
DIFFERENT artefact — the reference recipe's `scripted_agent.py` seam — so any
instance exercise that runs it is running an image that is **not** the accepted
one. That difference is a labelled property of the evidence, not a detail: the
accepted digests are what a production selection would use, and the fixture
digest is what the lifecycle was actually exercised with.

## 2026-09-18 — review198695: draft packet incomplete; stale dependency corrected

**Supersession:** W194457 is not awaiting review. Canonical detail at
snapshot198697 reports closed/satisfying, last change197265, accepting
REVIEW-CANDIDATE-195787.json and review-2026-09-17T15-56-45Z.md. Earlier dossier
and packet statements to the contrary are stale. This does not prove installed
bundle contents; dirty stamp/mtime/raw search cannot settle that separate fact.

Packet-198640 matches its recorded hashes but binds only the launcher of a
one-folder runtime, imports source bootstrap rather than proving installed
behavior, and supplies example configuration instead of a concrete runnable
packet. Its verifier silently omits base-ancestry checks when inspection fails.
The selected disposable lifecycle was not started. Review-2026-09-18T00-36-37Z.md
records the corrections and directs continuation under owner198635's existing
authority, without a new permission gate. Freeze full runtime and concrete
inputs, fail closed, and complete the real installed fake-provider lifecycle
with canonical evidence and owned cleanup. Preserve stopped production and
the draft; no deployment/recovery approval is implied.

## 2026-09-18 — premise CORRECTED; the installed-path exercise, measured. Claim198750

Independent review `review-2026-09-18T00-36-37Z.md` (claim198695, sha256
`17cdad0e1aa243f6461a07c3a67bed27cff1c5e44aa13a75f0756594d7a985ce`) did not
accept `packet-198640` as a reproducible deployment and required five
corrections. All five are addressed in `instance-198750/`; the draft packet is
preserved unchanged.

### 1. The stale W194457 premise is WITHDRAWN

This dossier repeatedly asserted that W194457 awaits independent review. **It is
closed, outcome satisfying**, accepting `REVIEW-CANDIDATE-195787.json` and
`review-2026-09-17T15-56-45Z.md`. I confirmed that against canonical detail. The
assertion was wrong in `packet-198640` and in the FINDING and PROGRESS entries
that carried it.

**What survives is a different and smaller fact:** the installed bundle's source
composition is unknown. Timestamps and a failed byte search establish neither a
reviewed nor an unreviewed payload, and I should not have joined that unknown to
a pending-review claim that was false. Binding the existing installed distro for
this isolated exercise therefore needs no further owner gate; its provenance
limitation is stated and is not a production approval.

### 2. The whole installed runtime is bound

`runtime-manifest.json` carries the complete one-folder manifest — **81 files**,
digest `73b8cab34a7e47857695cad4e80551de607d82aa77ee3ca39b72f7c89166ded6` —
produced by `tools.instance.manifest`, the deployment's own producer, which
records symlinks as link text and refuses one pointing out of the bundle. The
disposable installed copy was verified against it **entry by entry** and is
byte-identical.

### 3. Verification fails closed, and writes its own evidence

`instance-198750/verify.py` supersedes the draft verifier without overwriting it
or its results. Every prerequisite records an explicit `False` when it cannot be
established — the draft added its base-ancestry obligation *only if* the base
inspection succeeded, so a failed inspection dropped an obligation and could
still answer `all_true`. Three fake-command regressions drive exactly that.
**41 checks, all passing.**

### 4. What the exercise actually established, measured

- **The fixture image is built and labelled:**
  `sha256:edd20e9c3f0a15bdd445c7b83fcb8b5f8a52f6dc42d1d639a0fef9db3ccfacf4`,
  over the same immutable base, `--pull=false --no-cache --network none`. **One
  labelled difference:** it carries `scripted_agent.py` and enters
  `baton_worker.py`, so `main()` loads the deterministic scripted default; the
  accepted provider carries no scripted agent and enters `dogfood_entry.py`,
  which injects the real adapter. No live provider coverage is claimed.
- **A separate disposable instance** was bootstrapped from the installed distro
  at `/home/sl/baton-v12-disposable-198750`, authority
  `742fe75be3924967b48d181e3b2f490a`, in 4.003 s. The stopped production
  instance was not read from, written to, started or changed.
- **Task receipt is PROVED canonically.** A `baton.v12.job-submission/2`
  document was accepted through the installed `manager submit` and read back
  through `manager status` — no store was opened directly. The projection shows
  the implementation stage `queued`, review and integration `blocked`, and
  `terminal_policy` `report-and-hold`. The shipped example document carries
  placeholders; **five selections had to be supplied, each named by its own
  canonical refusal**, and all five are recorded.

### 5. The concrete blocker, measured three ways

**Candidate collection cannot proceed without a capacity selection, and the
deployment deliberately refuses to invent one.** The installed scheduler refuses
at startup in its own words:

> this deployment configures no execution capacity and this instance holds work
> it could not serve, so it refuses at startup rather than reporting an idle
> stack: 1 Job(s) in the Job store (w197661-fixture-lifecycle). Nothing was
> expired, abandoned, repaired or executed — configure the workers this work
> needs, or point this instance at its own stores.

That is the correct fail-closed behaviour. Measured three ways: the bootstrap
reports `workers_by_role` all empty; the scheduler refuses by name; and the
submission reader refused five placeholder selections one at a time.

**What composing capacity requires**, established by reading the code and the
production instance rather than guessed: three worker deployments — all three
roles, once any worker is configured — each a
`baton.v12.single-worker-deployment/4` of 29 members, **plus a digest-sealed
23-member `input_manifest` whose `manifest_digest` must equal the Job's
`input_digest`** (`single_worker.py:1303` compares them). So the manifest, its
seal, the submission and the worker deployment are one coherent chain rather
than four documents. **No shipped tool emits any of it:**
`tools.single_worker` and `tools.stage_execution` have no command-line entry,
and `bootstrap` holds `workers` and `jobs` in `DEFERRED` precisely because a
worker's sealed manifest cannot be written before the instance exists.

**Independent review and report-and-hold were not reached**, and are not claimed.
No container was started by this exercise: the fixture image was built, not run.


## 2026-09-18T00-56-06Z — review198800: capacity composition remains implementation work

The claim198750 description of missing capacity as a new selection blocker is superseded. The refusal establishes an unconfigured disposable instance; owner198635 already selected its deterministic lifecycle. Existing dogfood_operator.input_manifest and prepared-149053/deployment.py documents provide composition references. Complete the coherent sealed inputs, worker configuration and submission, then measure candidate collection, independent review and report-and-hold. Preserve the partial receipt and historical evidence. Runtime binding and base-inspection corrections pass 27 independent checks; see `review-2026-09-18T00-56-06Z.md` and `REVIEW-EVIDENCE-198800.json`.


## 2026-09-18T01-08-25Z — review198896: policy serialization is not configuration validation

The claims in instance-198871/compose.py and EVIDENCE-198871.json that the configuration or first layer validates are superseded by this inspection: the script only serializes policy dictionaries and computes hashes; no canonical configuration validator is called. Three file hashes and seven content digests agree. Distinct principal minting and all three remaining lifecycle outcomes remain unproved. See `review-2026-09-18T01-08-25Z.md` and REVIEW-EVIDENCE-198896.json. Continue the existing owner198635 selection; no new approval gate follows.


## 2026-09-18T01-21-09Z — review198974: credential fixture stopgap and composed input mismatch

Confirmed deployment limitation: single_worker unconditionally resolves a nonempty credential delivery even for the selected offline fake provider. Before any workaround, record it here: a labelled private synthetic non-bearer source is a bounded fixture stopgap within owner198635, not live authentication and not a product fix. No real credentials are inherited. Independent _matches probes also refuse review/integration because their manifest seals differ from the Job input_digest. Three individually valid manifests are not a valid stage chain. Placeholder provenance and success exit after failed configuration remain review corrections; see `review-2026-09-18T01-21-09Z.md` and REVIEW-EVIDENCE-198974.json.


## 2026-09-18T01-52-22Z — confirmed finalization replay defect after intake

Independent review199151 corroborates two retained installed reconcile refusals for attempt-432eb7b77502fbb65e041e5400c54464ae47353749dc5fa9408acb6f617c7af9. Current end_implementation calls _collected/request_intake, whose frozen-only _collectable guard precedes receipt replay and refuses already-sealed output. The initial post-intake failure remains unknown; missing fixture proposal metadata is a separate confirmed gap. Published status shows answering without the recorded refusal. See `review-2026-09-18T01-52-22Z.md` and REVIEW-EVIDENCE-199151.json for proposed bounded replay/visibility correction and acceptance. Pass baton.decide for new runtime scope; existing deterministic fixture work remains authorized. Preserve failed disposable evidence and production.


# Owner ruling seq199199 — PINNED BEFORE EDITS (claim199233)

Selected: the bounded correction in `review-2026-09-18T01-52-22Z.md`.

> Make finalization replay after committed intake preserve exact receipt/result
> identity, custody and fencing, without duplicate collection/publication or
> false success. Expose deferred-finalization reasons and exact attempts through
> the operator status surface. Correct fixture proposal metadata and full
> Job/target/producer verification, then complete the already-authorized
> disposable deterministic lifecycle through publication, independent review and
> report-and-hold. Use focused cut-point/restart tests and reuse accepted
> evidence. Coordinate with W198667 without interrupting its active logging
> claim or overwriting Codex-owned files. Return for independent review.
> Preserve failed evidence and stopped production; no live model, production
> restart, recovery or resubmission.

## The defect this authorizes correcting, stated exactly

`job_manager/review_driver.end_implementation` documents that every one of its
nine steps replays and that a process death between any two re-enters and
finishes. Step five does not.

`_collected` calls `intake.request_intake`, which calls `_collectable` BEFORE
`store.transact` or `record_intake`. `_collectable` admits `output == "frozen"`
only. `record_intake` has a proper replay path keyed on `intake_operation`, but
this entry never reaches it once the output axis is `sealed` -- and `sealed` is
the state a SUCCESSFUL intake leaves behind (`intake.py` observes it at the end
of `_seal`). So an ending that got past intake and failed afterwards refuses at
step five forever.

Measured, not reasoned about: two `serve --once` reconciles 72 seconds apart on
the retained disposable instance each owed `conclude` for
`attempt-432eb7b7…` and each deferred it with the identical
`refused/precondition` "output is sealed; custody is taken of a FROZEN result".
The reviewer reproduced the source path independently and confirmed the
container exited 0 with `Running=false, Pid=0`.

**What is still unknown, and is not to be asserted:** which step after intake
failed the FIRST time. The scripted fixture's missing `baton.git-proposal/1`
metadata is a confirmed fixture gap and a plausible publication trigger, not a
recovered original exception.

## Not in scope of this ruling

Production restart, recovery or resubmission; live models; cleanup or disposal
of the retained failed attempt and its container; any weakening of custody
validation or blanket admission of sealed outputs.


## 2026-09-18T02-10-32Z — review199281: intake-entry correction passes; full ruling incomplete

At the hashes in `review-2026-09-18T02-10-32Z.md`, 14 added tests pass and confirm committed receipt replay without duplicate collection. They do not execute full end_implementation or publication/checkpoint/cleanup cut points, and the named during-retention case injects no failure. Complete owner199199 visibility, genuine orchestration/restart tests and valid fixture lifecycle under existing authority. Prior instance-199021 verifier/result edits need an explicit historical supersession note; preserve future episode evidence separately. REVIEW-EVIDENCE-199281.json records hashes and measured checks.


# Evidence supersession — appended, never rewritten (claim199391)

Review 2026-09-18T02-10-32Z is right, and this is the record it asks for.

`instance-199021/verify_lifecycle.py` was EDITED IN PLACE in claim199233 to
correct the weak bootstrap-binding branch, and `instance-199021/
verification.json` was regenerated over the old one. `EVIDENCE-199021.json`
therefore no longer describes all the bytes at that path: its recorded hash for
the verifier is the pre-correction one, and the result document beside it is the
35-check run rather than the 33-check run it names.

**Nothing is repaired retroactively.** `EVIDENCE-199021.json` keeps its bytes and
its hashes. What it described is superseded here rather than rewritten, and the
supersession is the durable record of the difference:

| path | as EVIDENCE-199021 recorded it | as it is now | by |
| --- | --- | --- | --- |
| `instance-199021/verify_lifecycle.py` | the 33-check verifier | the 35-check verifier with the full Job/target/producer binding | claim199233, under owner ruling seq199199 |
| `instance-199021/verification.json` | the 33-check result | the 35-check result | claim199233 |

**And the rule going forward, which is the reviewer's and which I am adopting:**
a verifier revision and its result go under a FRESH episode path. This claim's
own verifier work is `instance-199391/`, and `instance-199021/` is not written
to again.


## 2026-09-18T02-59-56Z — review199559: conclude still has no durable reason

`review-2026-09-18T02-59-56Z.md` and REVIEW-EVIDENCE-199559.json supersede claim199391 R2a DONE: new storage covers admit/claim only. Independent sweep/status probe returns a conclude refusal but status answering with deferral null. Both _converse and _recover_endings need observation persistence/resolution, including older pending episodes. Schema required-table enumeration also omits deferrals. 288 focused tests pass. Full real-seam duplicate-effect proof and the selected installed fixture lifecycle remain outstanding. Existing owner199199 authority applies without a new permission gate.


## 2026-09-18T03-18-24Z — review199679: original visibility probe corrected, lifecycle still open

`review-2026-09-18T03-18-24Z.md` and REVIEW-EVIDENCE-199679.json confirm all seven candidate hashes and 133 passing focused tests. The prior conclude refusal now appears in public status with exact attempt attribution. This bounded correction is accepted; real publication-seam restart/no-duplicate-effect proof, older-ending/stale-clear visibility boundary and the selected installed fixture lifecycle remain required. Continue owner199199 without another permission gate; preserve production and historical evidence.


## 2026-09-18T03-33-36Z — review199777: status correction passes; cited Authority replay proof is a fake

`review-2026-09-18T03-33-36Z.md` and REVIEW-EVIDENCE-199777.json confirm five hashes and 63 passing tests. Stale-row distinction is verified. Claim199738 R1 done is superseded: the cited ProducerCase uses in-memory LinePublisher, proving local-journal replay rather than durable Authority behavior. Actual Authority publication/restart proof and selected installed lifecycle remain required under owner199199; no new permission gate.


## 2026-09-18T03-41-56Z — review199839 accepts real Authority replay proof; installed outcome still pending

`review-2026-09-18T03-41-56Z.md` and REVIEW-EVIDENCE-199839.json confirm both hashes and three real-Authority publication tests passing, including republishing after reopening the manager. This supersedes the fake-publisher evidence objection for bounded exact publication replay. It does not complete the still-unimplemented installed fixture lifecycle. Continue owner199199 without another permission gate and preserve historical/production evidence.


## 2026-09-18T03-53-16Z — review199914: proposing fixture is copied but never selected

`review-2026-09-18T03-53-16Z.md` and REVIEW-EVIDENCE-199914.json confirm three hashes and 13 tests returning OK with an unclosed-file ResourceWarning. Dockerfile enters baton_worker.py, whose default still selects original ScriptedAgent rather than ProposingAgent. Correct image composition and warning, then complete installed lifecycle under owner199199. Claim199877 blocker-removed conclusion is superseded pending actual entrypoint proof; historical first post-intake failure remains unknown.


## 2026-09-18T04:06Z — claim200000: the fixture is selected, and the lifecycle found two real defects

Answering `review-2026-09-18T03-53-16Z.md`, which was right: the previous recipe
copied `proposing_agent.py` and then entered `baton_worker.py`, so `main` took
`_scripted_default()` and ran the old agent. The image now enters
`proposing_entry.py` and carries no second agent to fall back to, and the
selection is observed **inside the built image** rather than inferred from the
recipe.

Running the installed lifecycle then surfaced two defects that no unit case
could have:

1. **No bootstrap ever established the Authority's canonical target.**
   `publish_candidate` compares the worker's declared base against it, and it
   answered its own placeholder `base-1`. Every first publication in a fresh
   deployment was refused, the stage deferred `conclude`, and it asked again
   forever. `set_policy` already existed for the other end of the line;
   what was missing was the first value.

2. **The declared outputs dirtied the private line.** On the `git-line` profile
   they are written into the worktree, and `freeze` refuses a line with
   worktree changes — so writing the outputs is what stopped the freeze. The
   real adapter already reserves them in the repository's local exclude file;
   the fixture now does the same.

**And one finding not fixed:** a `ProfileRefusal` inside `conclude` propagated
out of `manager.serve` and killed the manager process. The deferral machinery
exists so a refusal at that cut point is recorded and retried; this one takes
the whole serving loop down. It died loudly with a traceback rather than hanging
silently, which is a different failure from the one this Work reported.

### What the run reached

Capacity bootstrapped, Job submitted, scheduler started, the container ran from
the new image, the agent committed on the private line, the stage concluded, and
**candidate publication was reached**: the manager materialized a review line
whose checkout carries `w197661-fixture.txt` with exactly the declared bytes and
whose custody holds the proposal tree. Independent review was admitted and
claimed and its container ran, but **faulted**: its `inputs/source` is empty, so
the frozen checkpoint was never delivered into the review container. Whether
that is this composition's doing or the review-stage delivery's is not
diagnosed. Report-and-hold is unreached.

## 2026-09-18T04-38-48Z — review200179: fixture root and bootstrap preflight corrections

Reviewer baton.rvpc, claim200179. All seven candidate hashes match; five static
entrypoint tests and two deterministic seam probes succeed. Read
`review-2026-09-18T04-38-48Z.md`, `REVIEW-EVIDENCE-200179.json` and
`review-probes-200179.py` for the exact evidence and required correction.

**Confirmed:** ProposingAgent's review branch reads `/output`, but the review
mount contract puts the checkpoint at read-only `/input/source` and gives the
reviewer separate writable output. The tests conflate these roots. This
supersedes the inference above that host `inputs/source` emptiness proves the
checkpoint was never delivered; a separately bound mount is not established by
listing its host mountpoint. The agent fault is observed; the actual engine
mount was not independently inspected because Docker socket access was denied.

**Confirmed:** the new conflicting-base refusal runs after route, Work and
grant composition. The real-function/in-memory-authority probe records eleven
effects before refusal. Correct at bootstrap preflight with a no-effects
regression. **Confirmed:** instance-200000's copied verifier still names the
198943 destination and old attempt; it does not verify the latest lifecycle.
Replacement runtime/full fixture provenance and independent review/report-and-
hold acceptance remain required under existing owner199199/198635 authority.
Carry the reported typed ProfileRefusal escape forward with focused evidence;
do not conflate it with the fixture's wrong review root or swallow arbitrary
programming faults. No product changes or production operations by reviewer.


## 2026-09-18T04:43Z — claim200254: the fixture reviewed its own output root

Answering `review-2026-09-18T04-38-48Z.md`.

**R1.** `proposing_agent._review` ran all three observations against
`self.root` — the reviewer's separate *writable* result directory — so the
verdict was about whatever happened to be in the output root. The real contract
has two roots: `review_cycles.review_boundary` nominates the frozen line and
`source_boundary` binds it read-only at `/input/<source_root>`, which is where
`claude_agent`'s own review turn reads it. My three review cases hid this by
handing the implementation repository in as the review output root. Both are
corrected, and the base now comes from the frozen task and is proved against the
line rather than guessed as `HEAD~1`.

**And I withdraw the delivery diagnosis.** Claim200000
reported that the frozen checkpoint was never delivered into the review
container, on the evidence that the attempt's *host* `inputs/source` was empty.
An empty host directory is a mountpoint. That is not evidence about what the
container received, and the fixture's own root-selection defect explains the
fault on its own. The earlier claim is corrected by appending.

**R2.** The single-initial-target refusal ran after routes, Work and grants were
written, leaving partial Authority state and contradicting `prepare`'s own
promise. It is a preflight fault now, refused before a writable Authority is
even opened.

**The typed profile refusal** is contained by name: `ProfileRefusal` joins
`ContractRefusal` as a condition in the serving loop, with durable attribution
in the deferral, and a programming error still escapes.

**R3.** The verifier is replaced under a fresh episode, bound to this run's exact
identities and fail-closed. 33 of 36 checks hold — including candidate
publication, a sealed output naming this Work, and the established canonical
target. It fails on review ending, verdict acceptance and report-and-hold.


## 2026-09-18T05-14-53Z — review200453: unobserved verifier, completed review, integration input refusal

Read review-2026-09-18T05-14-53Z.md, REVIEW-EVIDENCE-200453.json and review-probes-200453.py. All nine candidate hashes match. The split-root correction passes focused tests; real prepare with a mocked opener refuses conflicting bases before either opening or composition. 36 tests pass; nine bootstrap tests are blocked in setup by unavailable writable disk-backed storage outside the checkout.

**Supersession of claim200254 diagnosis:** its verifier calls status without control/observation and does not require canonical=true. The retained canonical publisher snapshot at 05:01:22.081Z reports implementation and review completed, integration claimed. The retained manager.log contains a reconcile report identifying integration launch refusal: the task has no verification command. Thus all-three-claimed, review-unfinished and one-line-log claims are not supported. Full verdict/result acceptance still needs exact records, and report-and-hold remains unproved. Fix the empty verification fixture input and use the real status/ending contracts; no conclude receipt or job.outcome exists in those contracts.

**Confirmed remaining product finding:** _recover_endings still catches only ContractRefusal. An injected ProfileRefusal escapes the real recovery function with zero deferral calls; the live-path tuple did not cover this route. Complete narrow recovery containment and attribution under owner199199. Verifier provenance checks also need immutable expected image/runtime/config/result bindings, including runtime links. The separate launch-refusal visibility limitation is observed: _launch does not persist the reason in the deferral axis. Preserve all prior evidence and production, use fresh evidence episodes, and do not bypass required verification.


## 2026-09-18T05:28Z — claim200564: the diagnosis is withdrawn, and the lifecycle moved five walls

Answering `review-2026-09-18T05-14-53Z.md`.

**R1, the historical diagnosis, WITHDRAWN and corrected by appending.**
claim200254's verifier called `status` without `--control` or `--observe`, so
`tools/job_manager._status` supplied `Unobserved()` and answered
`canonical=false` — and the verifier never looked at that flag. Everything I
reported from it about where the run stopped was therefore about an
unobserved projection. The retained canonical publisher snapshot at
2026-09-18T05:01:22.081Z says what actually happened: implementation
**completed**, review **completed**, integration **claimed**. So
"all three stages sit at claimed", "the review stage did not finish" and "the
manager did not crash and its log holds one line" are all withdrawn. The
retained `manager.log` does hold a full reconcile report, and it names the
reason the integration never launched: the configured implementation task
declared no verification command. The reviewer read the same bytes I had and
reached the fact I did not.

**And the three final predicates were invented.** `episodes[].ended_state`
describes a recorded offer ending and is null on an ordinarily completed
stage; no `conclude` receipt exists by design, because receipt acts are
`admit` and `claim` only; and `job.status` has no `outcome` member at all. A
predicate that can never hold is not a failing check, it is a broken one.

**R2, the recovery containment, was real and is fixed.** `_recover_endings`
caught only `ContractRefusal` while `_converse` had learned the typed pair, so
a `ProfileRefusal` from a RESUMED `conclude` escaped the sweep and ended
`serve` — the same failure the live-path fix was written for, still reachable
through the restart path it is most likely to be met on. One owner for the
translation now, both boundaries catching the same pair.

**R1c, the lifecycle, moved from one wall to five and stopped at a sixth.**
With a real required command in the task and a producer that runs it, the
integration stopped refusing for a missing verification command and began
refusing for reasons nobody had reached before: missing
`integration_instructions` wiring, a credential slot name the integration port
requires literally, and — the one worth keeping — **every `bootstrap` run bumps
the Authority's approval policy generation while the emitted configuration pins
the value from its input**, so a freshly bootstrapped deployment cannot satisfy
its own pin unless the composition predicts the bump. Past all five, the
integration launched, and the Authority issued all three receipts:
verification **passed** on the required test, review **accepted**, approval
**approved**. It stops at the integrator itself: this package's fixture image
carries a PROPOSING agent and no integrating one, so the integration container
runs the wrong workload. Report-and-hold is still unreached, and this is
returned incomplete rather than reported as finished.

## 2026-09-18T06-19-15Z — review200867: recovery accepted; installed acceptance pending

All six claim200564 hashes match; 224 independent focused tests pass. The shared typed-refusal boundary now covers recovery with prior-episode attribution and durable retry evidence; R2 is accepted at the exact hashes in `review-2026-09-18T06-19-15Z.md`. R1a historical withdrawal is accepted. Retained canonical status confirms completed implementation/review and exceptional integration; its log reports three accepted receipts but no integration result/hold. Complete the deterministic integrator and contract-derived verifier under existing authority.

Clarification superseding the composer's fail-closed claim: policy_pin reads current generation plus7, but main neither bootstraps nor checks the resulting generation; a manual observation does not establish that executable gate. The clean-destination log also shows pin1/Authority9 followed by generation23 receipts and multiple serving initializations, so final provenance must distinguish initial composition from subsequent policy/bootstrap changes. This does not independently establish a sealed-input change. Exact evidence, limits and next steps are in the new review and REVIEW-EVIDENCE-200867.json. No product changes by reviewer; prior evidence preserved.


## 2026-09-18T06:26Z — claim200930: a corrected claim, a measured provenance record, and a calibrated instrument

Answering `review-2026-09-18T06-19-15Z.md`, which accepts R2 and the R1a
withdrawal.

**A claim of mine was false and is corrected.** I described
`compose_lifecycle.policy_pin` as fail-closed. It is not: it reads the
Authority's generation and adds an observed bump, and `main` composes documents
without bootstrapping, so nothing ever compared the prediction against the
result. A manual post-check I performed and reported is not an executable gate,
and calling one the other is the same kind of claim review200453 already
corrected me on. `BOOTSTRAP_POLICY_BUMP` is now labelled an observation of this
tree rather than a bootstrap contract, `policy_pin` says it only predicts, and
`check_policy_pin` is the real comparison — called by the verifier, a required
check, and refusing before anything is called ready.

**"Composed once from the final wiring" was looser than the evidence.**
`PROVENANCE-clean.json` records what actually changed and when, measured rather
than characterized: the destination was installed once and its Job submitted
once against a sealed input manifest that did NOT change
(`sha256:d4cd8ad2…` as submitted and as currently composed), and its capacity
was bootstrapped twice, the second differing from the first in exactly one
member — the approval policy pin, 1 to 23. Later policy activity at a
destination is not evidence that a Job's sealed input drifted, and the two facts
are recorded separately rather than one inferred from the other.

**The verifier is replaced, and this time it is calibrated.** Its predicates are
pure functions over documents, so 31 fixture cases drive them over one
successful shape it must accept and every broken shape it must refuse — which is
what would have caught the three invented members in the first place. Against
the real episode it reports 18 of 26 checks holding and returns non-zero: the
canonical projection, both completed stages, the candidate bytes, the custody
attempt BOUND rather than counted, the read-only Authority, the measured pin
equality and all five provenance bindings against a sealed immutable
expectation. The eight that fail are exactly the integration outcome and its
records, which have not happened.

**Still not done: the integrating workload.** The fixture image carries a
proposing agent; the integration container needs one that performs the import
through the real delivery/result contract. `integration_entry.main(agent=…)` is
the seam, the same shape `proposing_entry.py` already uses. Returned as exact
remaining scope with report-and-hold behind it.

## 2026-09-18T06-41-32Z — review200998: verifier still incomplete

Confirmed synthetic false positives for jointly absent provenance/attempt identities,
indirect writable Authority opener, and overwrite of claim-named verification evidence.
The real record reader remains a stub. This supersedes claim200930 completion claims
for whole R1b/R3; prior bounded corrections remain accepted. See review-2026-09-18T06-41-32Z.md and
REVIEW-EVIDENCE-200998.json. Complete reader calibration and deterministic lifecycle
under existing selection; no additional authority gate.


## 2026-09-18T06:50Z — claim201089: four verifier defects, and a fact I asserted that was not mine to assert

Answering `review-2026-09-18T06-41-32Z.md`. All four findings were mine.

**R1. The verifier accepted the ABSENCE of the evidence it exists to check.**
Replacing `expected` with an unrelated document and `measured` with an empty one
made all five provenance comparisons `None == None`; removing every stage
`attempt_id`, the verdict's attempt and the line's custody made those compare
equal too. Zero failed checks, twice. A required value is proved present and
well-formed before it is compared now, and every identity is bound rather than
merely matched.

**R2. A second path still opened the Authority for writing.** I corrected
`read_authority` to `open_readonly` and left `check_policy_pin` defaulting to
`Authority.open`, which takes a write lock and sets a persistent journal mode.
The reviewer's mocked-default probe recorded one writable call and zero
read-only ones. Corrected at the default, which is the thing that runs.

**R3. The evidence of a run could be overwritten by the next one.** `write_text`
under a reusable default claim, with the "do not overwrite" rule written as a
comment rather than enforced. The result is created with `O_EXCL` now, a
collision is refused, and `--claim` is required with no default that can
silently collide.

**R4. And the stub asserted something about the lifecycle that was false.**
`read_records` returned "this episode has no accepted verdict or checkpoint
yet". The reviewer pointed out that implementation and review both COMPLETED in
that episode, so those records exist — and reading them proves it: the line is
`accepted`, the verdict's disposition is `accepted`, the checkpoint names
`w197661-fixture.txt` and the declared base, and the producer's frozen result is
`completed`. Real read-only adapters now read all three through their owning
contracts. The report-and-hold terminal is the integration stage observation's
own state, whose owner composes an Authority and sessions and is not a read-only
path — so it answers `unread` WITH ITS REASON, and `judge` fails that separately
from a record that is genuinely missing.

**Against the real episode the verifier now holds 34 of 37 checks** and still
returns non-zero. The three that fail are the integration stage, the unread
terminal and the unreached hold — which is the truth, and no longer a claim
about records that were there all along.

**Still not done:** the deterministic integrator and report-and-hold.

## Review201153 — bounded verifier fixes accepted, complete acceptance still pending

Original missing-value probes now fail; read-only pin default and exclusive output
creation verified under mocks. Remaining false positives: boolean provenance values
and a missing verdict checkpoint identity. Collision unit test depends on installed
deployment; captured-shape test does not exercise adapters. Terminal reader and
deterministic lifecycle remain incomplete. See review-2026-09-18T07-01-24Z.md and
REVIEW-EVIDENCE-201153.json. This supersedes claim201089 all-four-complete wording,
not its accepted bounded corrections. Preserve all future intermediate artifacts.


## 2026-09-18T07:07Z — claim201215: presence was not validation, and `held` was not success

Answering `review-2026-09-18T07-01-24Z.md`, which accepts the joint-absence,
read-only-default and exclusive-creation corrections and names what is still
wrong. Both findings were mine, and so was the terminal reading.

**R1. Presence is not validation.** `_present` accepted every non-container
scalar, so setting all five provenance members to `False` on BOTH sides passed
every check — a comparison of two well-typed-looking nothings is the same defect
wearing a scalar. And `Checks.named` treated `wanted=None` as "no binding
requested", so REMOVING the verdict's `checkpoint_id` — the identity the check
exists to bind — turned the check off and reported a pass. Each required value
is now checked for the shape its own kind promises (identity, digest, manifest,
list, text), and a required reference is `binding`, which has two sides by
definition and no optional-operand escape.

**R2. Two tests were not what they looked like.** The collision case patched the
readers and left `check_policy_pin`, whose default reads the emitted
`deployment.json` and the INSTALLED Authority — a unit case about a file
collision made one real deployment call. It replaces every boundary `main`
reaches now, and the read-only default is exercised separately under a mocked
Authority, including a wrong prediction and the disposal. And the
captured-records case only compared the keys of a saved file, so an adapter
regression could not fail it; `read_records` itself is now driven over faithful
owner doubles — including the two members I originally guessed wrong,
`runtime_attempt_id` on the attachment and `assignment_ref` in the retained
result manifest — and a case asserts the adapter's output and the captured
record agree member for member.

**And `held` is not proof of a successful report-and-hold.**
`stage_execution.managed_account` writes `held` for a held queue entry or an
ending that was not `answered`, `answered` for an imported settled execution,
and `completed` once the integration receipt exists. I read the Job's terminal
POLICY name as an integration state and asserted the opposite of what the
contract says. The predicate is `completed` now, with a second check that `held`
is never mistaken for it.

**Artifacts are preserved.** `verification-201215.json` joins the three earlier
ones; nothing is removed, and the disclosure of the earlier deletion stands.

**Still not done:** the deterministic integrator, its terminal reader and
report-and-hold.

## Review201261 — bounded verifier corrections accepted; lifecycle remains incomplete

Candidate hashes match and 58 unmodified focused tests pass. Accept claim201215
validation, mandatory-binding, test-isolation/adapter and terminal-vocabulary
corrections. Retained verifier still fails integration completion, unread terminal
and completed integration account. See review-2026-09-18T07-16-17Z.md and
REVIEW-EVIDENCE-201261.json. Continue the selected deterministic integrating workload,
read-only terminal reader and report-and-hold chain; no additional permission gate.


## 2026-09-18T07:22Z — claim201324: the integrator exists, and one Job names one image

Answering `review-2026-09-18T07-16-17Z.md`, which accepts the verifier
corrections and asks for the deterministic integrating workload.

**The integrator is built and tested.** `ImportingAgent` performs the provider
turn deterministically: it reads the ACCEPTED bundle through
`integration_contract`, writes every scheduled row from the content-addressed
blob that row declares, at the reviewed mode, through a staging entry and a
no-follow descent; it deletes what the table says to delete; and it writes the
contract's own `baton.integration-report/1` document where the workload's prompt
asked for it. `importing_entry.py` injects it through
`integration_entry.main(agent=…)` — the documented seam — so the launch reader,
the bundle correlation, the whole-path preflight, the read-back of every
scheduled path and the conservative ending are all the accepted code's. It is a
LABELLED deterministic stand-in for a model-driven provider turn and claims no
model coverage. 19 cases, including the contract's own `check_report` accepting
what it writes.

**And selecting it is refused by a contract, which is the concrete blocker.**
The integration image builds (`sha256:7ae92b9c…`), but a deployment cannot hand
it to only its integrator: `tools/single_worker.py:267` refuses a worker whose
`image_digest` differs from the Job input manifest's `worker_image_digest`, and
a Job names exactly ONE input manifest. Composing with a per-role image returns
*"the bootstrap input manifest names another worker image"* from three
validators. This is the same one-manifest-per-Job shape claim199285 recorded for
role-specific manifests, met from the other side.

**The one shape that fits.** A single image whose entry dispatches on a FACT of
the delivery rather than on a name — `integration_entry` already does exactly
this, choosing its managed-apply branch on the presence of the apply-request
document — so a fixture entry can read whether this container was given an
integration assignment. That is designed, not built: it changes the proposing
image's context and therefore the sealed `EXPECTED.json` inputs, which needs its
own episode rather than a reseal.

## Review201388 — bounded importer accepted; fresh delivery-dispatched fixture next

77 focused tests pass; five hashes match. Image-selection refusal agrees with
single_worker manifest/image equality. Accept helper coverage, not lifecycle
completion. integration_entry managed-apply branch ignores agent= and constructs
ManagedApplyAgent; only ordinary integration invokes the injected importer. Read
review-2026-09-18T07-34-10Z.md and REVIEW-EVIDENCE-201388.json.
Continue existing selected fresh one-image episode using actual delivery dispatch,
real entry tests, terminal reader and report-and-hold; no new authority gate.


## 2026-09-18T07:38Z — claim201432: which branch runs, measured instead of assumed

Answering `review-2026-09-18T07-34-10Z.md`, which accepts the importer helper and
names a gap in what I proved about it.

**The reviewer is right and the distinction matters.**
`integration_entry.main` checks for `APPLY_REQUEST_DOCUMENT` FIRST: when it is
there the entry constructs `ManagedApplyAgent` and IGNORES its `agent=` operand
entirely, reaching `workload.managed_apply` through `baton_worker.main`. Only the
ordinary branch passes an injected agent into `workload.integrate`. My case
mocked `main`, so it proved which agent was HANDED OVER and not which branch
would run it.

**Which delivery this deployment emits, measured two ways.**
`stage_execution._prepares` reads `integration_preparation` and defaults to
False, and only the managed path composes an apply request. This episode's
bootstrap input, install input and emitted `deployment.json` all OMIT that
member, and the retained clean destination holds no `managed-results`, no
`apply-input` and no `managed-apply.json` anywhere. So the delivery its
integrator receives is the ORDINARY one — which is the branch that runs an
injected agent, and `ImportingAgent` is therefore the right shape for this
selection. That was true when I claimed it and I had not checked; it is measured
now.

**The dispatch is covered at the real boundary.** Five cases drive the actual
`integration_entry.main` over both deliveries with only its two owners replaced:
an apply request reaches `baton_worker.main` with a `ManagedApplyAgent` and the
injected agent is NOT the one used; an ordinary delivery reaches the workload
with exactly this agent; the composed documents and the retained run each show
which one this deployment selects; and an unreadable delivery REFUSES rather
than falling back to proposing — the fallback a one-image fixture must never
have.

**Still not done:** the fresh one-image episode, the contract-bound terminal
reader and report-and-hold.

## Review201475 — existing-entry branch coverage accepted; implementation remains

23 local importer cases pass; candidate hashes match. Ordinary integration selection
is supported by composed inputs and _prepares default. Fresh one-image dispatcher
is still unbuilt; existing-entry refusal test is not proof of its fallback behavior.
Terminal reader must follow ordinary account, superseding managed_account as the
reader plan for this episode. See review-2026-09-18T07-45-26Z.md and
REVIEW-EVIDENCE-201475.json. Continue fresh episode/lifecycle within existing scope.

## Findings from the first terminating run (claim201492)

**F1 — two canonical readers of the same store disagree about a completed
integration.** The publisher's observed snapshot answers integration
`completed`; `baton-v12-stack manager --store db/jobs.sqlite3 status --control
db/control.sqlite3` under a fresh `--incarnation` answers `starting` — with
identical receipts (`admit/performed`, `claim/performed`) and the integration
result document on disk saying `outcome: "integrated"`. An operator or verifier
who trusts the canonical status verb concludes the lifecycle is still executing
when it has terminated. Evidence: `instance-201492/build/status-run4.json` vs
`instance-201492/build/projection-run4.json`. Reproduction: let all three stages
complete, then run the manager status subcommand directly with a new incarnation.

**F2 — a deployment's approval pin goes stale under its own successful run.**
The configured pin was measured EQUAL (9 == 9) immediately before the start and
is UNEQUAL afterwards (configured 9, Authority 10).
`integration.driver._accepted_receipts` refuses unless these are equal, so a
deployment resumed after its own successful lifecycle defers at its integration,
with the reason only in a tick report. Evidence:
`instance-201492/verification-201492-run4.json`.

**F3 — every bootstrap moves the policy generation** (+7 on a repeat, +8 on a
first), so a composition that pinned the number it read before bootstrapping is
stale by the time the manager reads it. This is distinct from F2: F3 is the
bootstrap, F2 is the run.

**F4 — the pool generation makes a destination effectively single-use.**
`stage_execution._pool_generation` refuses with "activating this deployment's
pool would answer generation 2 and the configuration names 1", and a
re-bootstrap over an existing pool is what moves it. This is why every live
attempt in this campaign needed a fresh destination root, and it is the dominant
cost of each run. Evidence: `instance-201492/build/start-2.log`.

## Review201732 — read-only terminal owner already exists

review-2026-09-18T08-30-08Z.md and REVIEW-EVIDENCE-201732.json accept bounded dispatcher/importer
coverage (46 local tests), not lifecycle completion. StageObservation.observe_integration
already opens read-only owner handles and calls ordinary Integration.account. This
explicitly supersedes claim201492 managed_account blocker explanation. Compare
status with its integration observation factory before attributing F1 to incarnation.
F2 resume failure remains inferred; post-run pin mismatch is observed. Preserve
F3/F4 evidence without universal single-use claims. Finish verification against
retained run4 first; post-build seal is not prospective build provenance.

## Corrections to the claim201492 findings (claim201770)

**F1 IS WITHDRAWN. It was my defect, not the product's.** I reported that two
canonical readers of the same store disagreed about a completed integration, and
proposed it as a high-severity product finding. Review201732 [R2] said to run a
controlled comparison before attributing it, and the comparison refutes it.

`tools/job_manager.py` composes `_ReadOnly(control)` when `--observe` is absent
and `_Observing(control, observed)` when it is present, and `_Observing` is the
only one that contributes `observe_integration` (`_integration_read`, ~216-230).
The projection consults that account before its generic worker rules. So the two
documents I set beside each other were not two readers of one store — they were
one reader invoked with and without the operand that lets it look.

The measurement, same destination, same store, same incarnation
`c201492-verify`, same authority and control store, one flag different:

| invocation | integration state |
| --- | --- |
| `status --control …` | `starting` |
| `status --control … --observe tools.stage_execution:observing_factory` | `completed` |

Retained in `instance-201492/build/projection-run4.json` (unobserved),
`build/projection-observed-run4.json` (observed) and, as a structured
measurement, `CAPTURED-terminal.json`'s `observation_gap`. `measure_observation_gap`
in the verifier reruns it, and `TheOBSERVEOperandIsTheCONTROLLEDComparison`
pins it — including a case that refuses to claim a gap when both sides agree.

What may remain is much narrower and is **not** claimed here as a defect: an
operator who omits `--observe` is told `starting` for a terminated integration
with nothing pointing at the missing operand. That is a UX question about a
correctly-behaving command, and it belongs to its own Work rather than to this
one. `observing_factory` also refuses unless `BATON_V12_STAGE_EXECUTION_CONFIG`
is set, which is a second thing an operator must know.

**F2 IS NARROWED to what was observed.** What is measured is a POST-RUN
mismatch: the configured pin is 9 and the Authority's generation is 10, having
been measured equal at 9 immediately before the start. What I additionally
asserted — that a resumed deployment would therefore defer at its integration —
is an INFERENCE from reading `integration.driver._accepted_receipts`, and I did
not reproduce it. Neither did I establish which event moved the generation.
Both are now stated as not established.

Two facts that must not be merged, and the verifier checks them apart:
- the receipt that settled this episode records `decision.policy_generation: 9`,
  so it was ACCEPTED under the configured pin, and a later advance cannot
  un-accept it;
- the deployment's readiness to authorize a NEW action is what the 9-vs-10
  mismatch bears on.

**F3 and F4 stand as recorded observations, with their scope stated.**
`start-2.log` proves one refusal — "activating this deployment's pool would
answer generation 2 and the configuration names 1" — and that is what it proves.
It does not establish universal single-use semantics for a destination, and the
claim that a destination is "effectively single-use" is my operational
experience across this campaign's runs rather than a demonstrated rule. F3's +7
and +8 are likewise counts I observed, not a derived law.

Diagnosing and classifying F2/F3/F4 properly is separate work; this Work is not
widened to cover it.

## Review201853 — remaining verifier gaps

review-2026-09-18T08-46-39Z.md and REVIEW-EVIDENCE-201853.json: seven hashes match, 89 tests
pass, but independent document probes accept missing/wrong terminal episode and
wrong proposal Authority. read_terminal still opens writable JobStore.open; inner
read-only handles do not prove the whole adapter read-only. No actual run4 mutation
is alleged. Bounded observation/chain corrections accepted; full acceptance pending.

## F5 — the Job store has no read-only opener, and a verifier pays for it

Recorded at claim201869 on review201853 [R2]'s direction. **This is a static
capability finding about the API. It is not an allegation that the retained run4
destination was mutated — it was not, and the measurement below says so.**

`baton_v12/job_manager/store.py:187 JobStore.open` is the only opener the Job
store has. It connects writable, `_initialize`s an absent store, `_adopt`s or
migrates an existing one, and requests WAL. Three sibling stores already have the
read-only counterpart it lacks:

- `baton_v12/worker_manager/store.py:323 ControlStore.open_readonly`
- `baton_v12/authority/store.py:272 Authority.open_readonly`
- `IntegrationStore.open_readonly`, used by `observe_integration` itself

So `StageObservation.observe_integration` opens both of *its* owners read-only —
which is why review201732 was right to call it the read-only reader — while
anything composing it through `observation_from` must first obtain a JobStore,
and the only way to do that is the write-capable opener.

**Observed, not merely argued.** A verifier case handed the opener an *empty
file* — which passes an `is_file()` guard — and `JobStore.open` wrote a complete
716KB initialized database into a path that was only being read. That is the
`_initialize` branch doing exactly what it is for, reached by a reader.

**What the retained destination actually experienced.** Measured across one full
read, with every handle closed before the second measurement: `jobs.sqlite3` is
byte-identical (`43f1bb04…` before and after), and no `-wal` or `-shm` survives.
During the read SQLite's sidecars exist; a clean close removes them. run4 is
intact.

**RESOLVED at claim201954.** `JobStore.open_readonly` now exists at
`v12/python/src/baton_v12/job_manager/store.py`, on review201931's direction
that the earlier record-before-product-change instruction was not a fresh
permission gate. The nonmutating half of `_adopt` was factored into
`_recognized` and is shared; `_adopt` itself is unchanged and still migrates.
Covered by `v12/python/tests/job_manager/test_store_readonly.py` (30 cases) and
reversal-probed. The verifier now opens through it and `judge` REQUIRES a
read-only owner rather than reporting a writable one.

**Bounded resolution as recorded, now applied.**
Add `JobStore.open_readonly(path, *, authority_uuid, incarnation, clock)`
mirroring `ControlStore.open_readonly`: a `mode=ro` URI, a refusal for a path
that is not an existing regular file, a refusal for an empty store rather than
initializing it, adopt-verify without migrating, no WAL request, and no
write-capable fallback on a read failure. That is product API and is **not**
added here.

**The interim, which is a guard rather than a claim.** `read_terminal` refuses
before the opener runs unless the path is an existing regular file whose first
bytes are SQLite's own header — the same rule `ControlStore.open_readonly`
applies, read off the bytes because there is no opener to delegate to, and with
no SQL issued. It then reports the opener by name, states plainly that it is
**not** read-only, and measures the store's data and sidecars across the read.
The verifier never describes a writable opener as read-only.

## Review201931 — R1 accepted; F5 prerequisite proceeds

review-2026-09-18T08-58-46Z.md and REVIEW-EVIDENCE-201931.json accept the episode/Authority
bindings (117 tests and three independent probes). The header guard does not
prevent migrations. F5 now records the required bounded prerequisite; review201853
record-before-change wording was not a new permission gate. Complete the readonly
JobStore API and verifier adapter under existing authorized verification scope,
with exact ownership coordination. This supersedes F5 authorization-pending
wording, preserving its capability findings and historical measurements.

## Review202028 — F5 accepted; F2 generation mechanism confirmed locally

review-2026-09-18T09-13-34Z.md and REVIEW-EVIDENCE-202028.json:196 focused tests pass,
five hashes match. F5 readonly API and adapter accepted. Prior F5 not-added/interim
paragraphs are historical and superseded by claim201954 implementation and this
review. Synthetic integration advances generation7 to8 while its receipt retains
decision7: integrate calls set_policy(canonical_target), which bumps generation.
Separate historical completion acceptance from future authorization readiness;
explicitly supersedes unconditional post-run equality as a historical gate.
Preserve mismatch diagnostic, acceptance-time binding and provenance limitation;
do not repin or change product policy. Run4 9/10/receipt9 fits the mechanism but
its event history was not independently read here.

### F5 supersession note (claim202052)

Review202028 observed that F5 above still carries its original
not-added/interim paragraphs beneath the resolution line inserted at
claim201954, and asked for an explicit supersession rather than another rewrite
of old history. So, appended:

Everything in F5 from "**Bounded resolution as recorded, now applied.**"
onward — the bounded resolution described in the future tense, the "NOT added
here: product API" sentence, and "**The interim, which is a guard rather than a
claim**" with its header-check description — is **HISTORICAL**. It records what
was true at claim201869, when the gap was open. It was superseded at
claim201954:

- `JobStore.open_readonly` exists and is the verifier's opener;
- the interim `_store_refusal` / `_SQLITE_MAGIC` header guard is **deleted**;
- the refusals belong to the owner, which is what let the valid-old-schema case
  be refused at all — the header guard could not.

Those paragraphs are left in place because they are the record of a state this
campaign actually passed through, and rewriting them would erase the reason the
opener was needed.

## F2 — RESOLVED as to mechanism (claim202052)

The generation advance is **by design**, and my original framing of it as a
defect was wrong. Confirmed against the current tree at
`v12/python/src/baton_v12/authority/core.py`: `integrate` takes its
authorization decision through `_require_capability`, *then* calls
`set_policy("canonical_target", proposal["candidate_digest"])`, and `set_policy`
unconditionally calls `_bump_policy_generation`. The integration receipt is
written carrying the earlier decision. So a completed integration necessarily
ends with the Authority one generation past its own receipt.

Reproduced deterministically in
`v12/python/tests/authority/test_integration_generation.py` (9 cases) through
the existing `WorkflowCase` fixture, no raw store access: generation **7 → 8**,
canonical target advanced to the proposal's candidate, integration receipt
recording `decision.policy_generation: 7` — the same numbers review202028
measured independently.

Retained run4's pin 9 / current 10 / receipt 9 is exactly this shape.

**The product source already documents the consequence.**
`tools/stage_execution.py:3103`: `_accepted_receipts` "checks the deployment pin
against the Authority's CURRENT generation before it issues anything, so issuing
at reconciliation time — after the first Job's integration bumped that
generation — can only ever refuse." The design already routes around it:
`StageComposition._source_receipts` issues each Job's three receipts while its
pin is still current, and the later branch proves them historically.

**What I withdraw.** The claim that a resumed deployment would defer at its
integration, as to *completed* work: run4 was restarted at generation 10 with
pin 9 during claim201770 and all three stages reported `completed` with one
episode each. Reading a completed stage does not reach `_accepted_receipts`.

**What remains unestablished, and is not claimed.** Whether a deployment with
*new* work to integrate reaches that guard through any particular caller. The
callee's own comparison is read at `driver.py:1111-1115`; its callers are not
all traced.

**What this changes in the instrument.** Post-run pin equality is no longer a
gate on historical completion — it is a **readiness** fact, reported separately
and visibly. Historical completion is proved by the owned terminal, proposal,
result, target and receipt, plus the receipt's acceptance-time generation, which
remains a required check.

**No product change is proposed.** F3 and F4 remain bounded observations and no
bootstrap or pool redesign is scheduled.

## Review202123 — historical completion accepted, readiness conjunction corrected next

review-2026-09-18T09-27-13Z.md and REVIEW-EVIDENCE-202123.json accept historical completion
within deterministic-fixture/provenance limits. Four hashes match;143 tests pass.
ready currently requires both current=configured and current=configured+1; move
the historical one-step observation outside readiness gating, preserving its
diagnostic. No new lifecycle or product-policy change. Locator correction: F2
generation suite actually lives at v12/python/tests/manager/test_integration_generation.py.
The digest-bound result is instance-201492/verification-202052-accepted.json.

### F2 locator correction (claim202140)

F2 above cites the reproduction at
`v12/python/tests/authority/test_integration_generation.py`. That was where the
file was first written; it is **not** where it lives. The actual path is
`v12/python/tests/manager/test_integration_generation.py`.

It moved because `tests/authority/test_catalog.py`
`test_the_suite_is_one_gate_and_not_a_pile_of_files` enumerates the Authority
suite's files by name, so adding one there means editing a catalog this Work
does not own. The file sits with this Work's other suites and imports the
Authority fixture instead. Its content, its 9 cases and its measured 7 → 8 with
receipt decision 7 are unchanged.

Corrected by this appended note rather than by editing the F2 text, which is the
implementer history of what was believed when it was written.

## Review202183 — signed off for owner disposition

review-2026-09-18T09-35-51Z.md and REVIEW-EVIDENCE-202183.json:147 tests pass, three hashes
match, both independent readiness probes now behave correctly. Historical
deterministic completion and corrected reporter accepted. No further report fix
requested. Carry post-build input-attestation limitation, new-work caller unknown
and F3/F4 observations to owner disposition; no deployment/Git authority implied.
