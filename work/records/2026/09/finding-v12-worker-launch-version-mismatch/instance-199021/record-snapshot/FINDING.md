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
