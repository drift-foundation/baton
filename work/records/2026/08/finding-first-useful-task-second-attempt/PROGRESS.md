# Progress

## 2026-08-31 — first implementer round (`baton.claude`, W51487 impl claim)

**One fresh attempt ran under the task-scoped authorization and resolved.**
Exit 0, `retained`, candidate preserved and reviewed. Disposition: **REJECT
the candidate; the retained-review platform is PROVEN; the provider turn did
not happen.**

Full acceptance record: `acceptance-2026-08-31T08-52Z.md`.
Evidence: `evidence/w51487-run2/`, including the worker's own account.

### What W51473 bought, exercised for the first time by a live attempt

`cleanup: {cleanup: "retained", state: "absent"}` with committed disposition
`retain`, and the operator still reporting `resolved: true`, `unresolved: []`,
exit 0. The material stayed, the runtime went, and the command called that
what it is. Then the acceptance W39364's own criteria required and could not
reach was actually performed: the retained candidate diffed file by file
against the measured input, and the frozen command rerun outside the worker in
the retained tree -- 26 tests, OK, exit 0.

### The answer W39364 destroyed

`proposal/result.json` survived this time and it is the whole finding:

    "disposition": "provider-failed",
    "provider": { "status": 1, "seconds_bound": 3600 },
    "why": "the provider exited 1; its own diagnostic is not published,
            because the process that wrote it holds this attempt's credential"

The task was never attempted. This is not a provider that tried and failed at
the work; it is a provider turn that did not happen, so the rejection is not a
judgement about any model's output -- there is no output to judge. Zero-byte
`change.patch` and `no verification was attempted` both agree.

### Three credential-free probes, and the honest size of the conclusion

None touched the authorized source. Egress from the exact posture works (DNS
and TCP 443, no credential mounted), so this is not a network fault and not
W17110's TLS trust-store defect. The CLI is present and functional in the
image. And a credentials document I INVENTED reproduces the exact signature:
exit 1, `is_error: true`, `terminal_reason: "api_error"`,
`duration_api_ms: 0`.

So the most likely cause is that the authorized credential is not accepted --
expired, invalid, or short a scope. **Stated as the inference it is.** Other
API errors also exit 1. I did not read the credential and will not; which one
it is belongs to the operator who owns the source. `evidence/w51487-run2/
diagnosis.md` has the measurements.

### Three findings

1. **The credential source needs checking before another attempt.** Every
   other input is proven good -- task, delivery, image, network, posture,
   retention, arc. An unchanged retry under the standing authorization would
   very likely reproduce this exact result, so it is not worth spending. I
   stopped rather than burn attempts against a fixed cause.
2. **[P1, `claude_agent`] A provider failure is not diagnosable from the
   retained evidence.** `status: 1` and, by sound design, nothing else. Three
   probes outside the attempt to reach "probably the credential" is not
   something a supervised pilot can depend on. The CLI already emits a
   structured `terminal_reason` on stdout rather than the stream that may
   carry the bearer; the safe form is a CLOSED VOCABULARY -- map it to one of
   this deployment's own words and publish only the mapped word. W17110's
   `trial.mjs` classifier, which this frozen task exists to cover, is that
   shape already. Not this child's file; offered rather than taken.
3. **[P2, operator] The `now` grant is clock-relative and judged late.** My
   first invocation set `now` ~20 minutes ahead; `issue_offer` computes the
   expiry from the manager's clock, `OFFER_TTL_SECONDS` is 120, and
   `accept_offer` compares the grant -- so it refused `offer ... expired`
   AFTER `stage_source` wrote the delivery and an offer was issued. The
   manager settled that offer `expired` cleanly and no claim, runtime or
   provider turn followed. Preflight cannot catch it and nothing says `now` is
   clock-relative rather than a free identity. The attempt that ran used fresh
   identities, fresh roots and a real instant.

### What I did not do

I did not retry. The authorization permits unchanged retries without further
approval, and an unchanged retry against a cause I have located would be
spending real provider turns to reproduce a known answer. I also did not read
the credential, did not copy the retained candidate into the canonical
checkout, and did not touch `claude_agent`.

### Verification

    the attempt                              exit 0, resolved, retained
    independent diff over the retained tree  four paths, all identical
    the frozen command, rerun outside        26 tests, OK, exit 0
    runtime absence, credential teardown,
      staged-source and canonical-checkout
      immutability                           all measured after the fact

Whitespace clean.

## 2026-08-31 — second implementer round (`baton.claude`, W51487 impl claim)

The credential was replaced (M52739) and I ran one fresh attempt,
`attempt-w51487-run3`, with entirely fresh authority, Work, offer, attempt,
control store, launch home, storage and credential-home identities, from a
clean four-file staging never executed in place. Exit 0, `retained`,
`resolved`, `unresolved: []`. Neither run 2's result nor its conversation was
reused, and nothing was written into the canonical checkout.

**Same disposition: REJECT. And this time the blocker is LOCATED.**

Full write-up: `evidence/w51487-run3/blocker.md`. Retained evidence, including
the worker's account: `evidence/w51487-run3/`.

### My previous inference is refuted, and I say so plainly

Last round I concluded the likeliest cause was that the authorized credential
was not being accepted by the API. The credential was replaced and the result
is IDENTICAL -- same `provider-failed`, same status 1, same custody content
digest `sha256:e002024b...` as run 2. That inference was wrong. It was
labelled an inference, and this is what refuting one looks like.

### The provider is not failing to authenticate; it cannot READ the file

Credential-free, in the image, nothing mounted:

    claude --print --permission-mode acceptEdits 'hi'
    -> EXIT=1, stdout "Not logged in · Please run /login"

That is the attempt's exact signature. And `acceptEdits` is a VALID choice --
an invalid mode gives a usage error listing the allowed ones. `claude_agent`
calls that tuple "the single operand a golden test cannot establish" and asks
the first live turn to prove it: **it is proven correct.**

`credentials.py` writes the attempt slot at `VOLATILE_FILE = 0o600` owned by
the manager's uid; the container is the fixed uid 65532. Reproduced with a
file of my own containing `{"not":"a credential"}`, mounted as the adapter
mounts the slot:

    os.path.exists -> True     os.access R_OK -> False
    open -> PermissionError 13     uid 65532, file uid 1000, mode 0o600

And `claude_agent._prepared_home` guards on `os.path.exists`, not
readability -- so nothing refuses, the unreadable slot is symlinked into the
private home, and the CLI's EACCES becomes an unpublishable exit 1.

### W33935's defect, the third time

Same shape, third occurrence, each found by something actually running:
the two `/input` documents at `0400` (fixed by W33935); the staged source tree
at `0600` (fixed by `_frozen_delivery` under W39358, found by the first real
worker turn); and now the credential slot at `0600`.

The frozen task this attempt exists to perform is adding coverage for
`preflight.py::_observed_readable` -- W17110's probe that runs a container as
uid 65532 with the credential mounted and runs `test -r`. The spike built a
probe for exactly this failure; neither the manager nor the worker asks it.

### A remedy shape, measured rather than guessed -- and not taken

The manager already adds the workspace group to the execution container
(`--group-add`, W33936). At `0640` with that group:

    groups [1000, 65532] | access R_OK -> True | open -> ok

So the slot can be readable by the container's uid WITHOUT becoming
world-readable, which matters more here than for `/input`: this one is a
bearer, and `0444` would be the wrong answer. The worker half is
`_prepared_home` asking readability rather than existence, so an unreadable
delivery is a typed refusal naming the cause. Both files belong to other
Work; measured so the next one need not guess.

### Stopped, as the authorization directs

"Stop again on any new material blocker." This is one, it is not mine to fix,
and a further unchanged retry would reproduce it exactly. I did not read the
credential, did not touch `credentials.py` or `claude_agent.py`, and applied
nothing to the checkout.

### The acceptance, performed again on the retained candidate

    independent diff, four paths        all identical to the measured input
    python3 v12/spike/ping-pong/test_harness.py, rerun outside the worker
                                        26 tests, OK
    runtime absence, credential teardown, staged-source and
    canonical-checkout immutability     all measured after the fact

Whitespace clean.

## 2026-08-31 — fourth implementer round (`baton.claude`, W51487 impl claim)

**Plan item 7 is done. The provider turn happened and the task was performed.**

Disposition (mine, as implementer; the terminal one is the reviewer's): the
candidate is worth ACCEPTING. Full record: `acceptance-2026-08-31T16-40Z.md`.
Evidence: `evidence/w51487-run4/`.

### The gate, revalidated before spending anything

The four frozen source files and the 3,291-byte human contract hash exactly to
the values in `dry-revalidation-2026-08-31T08-46-13Z.md`. The clean staging is
again 4 entries, 85,999 bytes, tree digest `sha256:9e70c733…`, with no
bytecode. Credential metadata only: `/run/baton/credentials/claude` is a
regular 509-byte `0400 sl:sl` file, `test -r` succeeds; no bytes opened.

### What was fresh, and what the reviewer required

Authority `1e49a06dad63423da2eb087bd230dd7c`, Work `1e49a06d-W51487`, offer
`offer-w51487-run4`, attempt `attempt-w51487-run4`, runtime `840cd967e67d…`,
incarnation `w51487-run4`, and fresh control, launch, storage, credential-home
and source roots. Nothing from run2, run3 or W39364 was reused.

The image was **rebuilt from the current W52800-corrected tree**:
`sha256:b471399a7dcb8300795fe884c471b817ec1d61644130d66ec12fbd4fef76c003`,
which differs from run3's `sha256:9b83e49c…`. That difference is the corrected
`claude_agent.py` travelling into the artefact.

Grants diff against run3, checked line by line before the run: the identities,
the five roots, the image digest, the record-binding digests and `now`. The
task, credential source, `bridge`, `retain`, the seven policy digests, the
adapter/toolchain/profile identities and the human contract are unchanged, as
the standing grant requires.

### The run

    PYTHONPATH=src python3 tools/dogfood_operator.py \
        --grants /tmp/w51487/run4/grants.json \
        --evidence /tmp/w51487/run4/evidence.json \
        --credential-file /run/baton/credentials/claude
    -> exit 0, 2m34s

18 operations committed, `offer.issue` through `runtime.destroy`. Terminal
`retained`, `cleanup {retained, absent}`, `resolved: true`, `unresolved: []`,
conversation `answered` on `describe` and `work`.

### The difference from run2 and run3

`changed_paths: ["v12/spike/ping-pong/test_harness.py"]`. Not an empty patch,
not an unchanged candidate — 5,584 bytes adding 106 lines and removing zero,
with `preflight.py`, `trial.py` and `trial.mjs` byte-identical to the frozen
originals. The task's four required facts each have a case, its constraints are
each honoured, and the harness rerun outside the worker reports **30 tests, OK**
— the 26 frozen cases plus four new ones.

**The coverage catches things, and that was measured.** Six mutations of
`_observed_readable` — dropping `--network none`, dropping `readonly=true`,
forcing `--user 0:0`, replacing the stdout comparison with a constant,
reporting a failed probe as unreadable, and removing the absent-path early
return — are all caught, each by the case that owns the corresponding fact.
`evidence/w51487-run4/mutation-check.md`.

### The worker said `verification-failed`, and the control says why

`result.json` records `verification: {status: 1}`. The independent rerun says
0. Both are honest; they ran in different places, and the frozen harness is not
indifferent to which.

Inside the worker image as uid 65532, read-only root, no credential, no
network: the candidate gives 30 tests with 2 failures, both in the pre-existing
`AnAncestorDecidesReadabilityToo` and none of them new. **The UNMODIFIED frozen
source in the same posture gives 26 tests with the same 2 failures.** So the
frozen harness already ends 1 there, before this task's candidate exists: those
two cases assert that a `0o700` directory makes a file unreadable, which is only
true for a process that does not own the tree, and inside the container the tree
is owned by the running uid.

`verification-failed` was therefore unreachable-by-any-candidate for this task
in this worker. That is a finding about the frozen task's verification command,
not about the work. `evidence/w51487-run4/verification-discrepancy.md` carries
the exact commands. The worker's own stdout was NOT read — it is code from a
tree the provider edited, running with the credential mount readable — so both
container runs above are credential-free reproductions.

### Measured after the fact

Runtime absent by engine inspection and by the manager's own observation; zero
containers named `w51487`. Credential teardown leaves one empty directory and
nothing else. The four staged files and the four canonical files both hash to
the frozen digests, and a porcelain status of `v12/spike/ping-pong/` is empty.
Nothing was written into the canonical checkout and I did not read the
credential.

### One thing I added to the record

`prepare_attempt.py`, beside this record. The operator command opens an
authority and expects a configured control store, and nothing said where those
come from — every earlier attempt reconstructed that step by hand from the test
fixtures, and my first invocation of this one refused for exactly that reason.
It mints no identity of its own, reads every value out of the grants file, and
refuses rather than adopts an authority store that already exists.

### State

Awaiting independent terminal accept or reject for W38956. Passing back rather
than closing.

## 2026-08-31 — fifth implementer round (`baton.claude`, W51487 impl claim)

**Plan item 8 could not be produced. Two fresh attempts, both REJECTED, and the
round stops on a new material blocker that is not mine to fix.**

Full record: `acceptance-2026-08-31T17-26Z.md`. Evidence:
`evidence/w51487-run5/`, `evidence/w51487-run6/`.

### The review was revalidated before anything was spent

`review-2026-08-31T17-15-35Z.md` says run4's nominated-engine case cannot catch
a production hard-code of `"docker"`. I measured it rather than believed it: on
a writable copy of the retained candidate — never the custody tree, never the
checkout — substituting `["docker", "run", ...]` for `[engine, "run", ...]`
leaves the harness at exit 0 with nothing failing, while the other six
mutations are each caught by the case that owns their fact. **The review is
right and the required correction is the right one.**
`evidence/w51487-run5/run4-engine-recheck.md`, reproducible with the
`mutation_check.py` retained beside it.

### Two attempts, and the second one is a control

Both under the unchanged task-scoped grant with wholly fresh authority, Work,
offer, attempt, runtime, incarnation, control, launch, storage, credential-home
and source identities, and no reuse of any earlier result or conversation.

    run5   17:20:42Z   image sha256:8af96742a894…   rebuilt from the current tree
    run6   17:23:01Z   image sha256:b471399a7dcb…   run4's exact artefact

Both: `provider-failed`, provider status 1, `changed_paths: []`, zero-byte
patch, custody digest `sha256:e002024b…` — run2's and run3's digest, an
untouched delivery.

Run5 changed exactly one input relative to run4's success: the image, rebuilt
because the standing handoff requires building from the current tree. So run6
held that input at run4's own digest and changed nothing else. **It failed
identically. The rebuilt image is not the cause**, and
`evidence/w51487-run6/image-control.md` has the layer comparison: the four
`COPY` layers carrying this repository's code are byte-identical across both
artefacts, and only the two network-fetch layers move.

### This is not run3's blocker, and W52800 is why I can say so

`_prepared_home` now raises `TaskRefusal` for a slot this identity cannot open,
and a refusal is a different disposition from `provider-failed`. What we got is
only reachable after the provider process actually ran. The credential was
delivered, was readable, and the provider then failed.

Credential-free in the exact posture: the CLI works, DNS and TCP 443 work over
`--network bridge`, and both "no credential" and "an invented invalid
credential mounted as the adapter mounts it" give exit 1 `Not logged in`.
Metadata only: `/run/baton/credentials/claude` is still a regular 509-byte
`0400 sl:sl` file, mtime 09:06:32Z — **the same unchanged bytes that produced a
real provider turn at 16:33Z.**

### The inference, labelled, and the second explanation I cannot exclude

The staged credential is a 09:06Z snapshot of a document the provider normally
refreshes in place, delivered read-only into a container that cannot write a
refresh back — so a snapshot with an expiry stops working while its bytes never
change. That fits every measurement and explains the 47-minute difference.

**It is not proven.** An account-level refusal such as a usage limit exits 1 in
the same shape, and I cannot separate the two from outside because the
provider's own diagnostic is deliberately unpublished. That is the run2 P1
finding arriving a second time; it has now cost two rounds and it is still not
this Work's file.

### Two concerns put on the ledger rather than offered again

The run2 round offered the provider-diagnosability defect as a P1 and left it
off the ledger; it bit again this round and cost a second one. It is now
**W55360**. The recipe-reproducibility limit run6 uncovered is **W55361**.
Neither is this Work's file and neither blocks it; both are now findable by
somebody other than the reader of this record.

### What I did not do

I did not retry a third time against a cause I have narrowed and cannot fix —
the standing grant permits unchanged retries, and spending provider turns to
reproduce a known answer is the same waste I stopped for in the run2 round. I
did not read the credential, did not use it outside a supervised attempt, did
not touch `claude_agent.py`, `credentials.py` or the frozen task, did not
mutate run4's retained candidate, and applied nothing to the canonical
checkout.

### Verification

    both attempts                           exit 0, resolved, retained
    runtime absence, credential teardown    measured after each run
    independent diff, four paths each       all identical to the delivery
    the frozen command, rerun outside       26 tests, OK, in both trees
    staged source and canonical checkout    all eight files at frozen digests;
                                            porcelain of the spike tree empty
    the review's finding, mutation-tested   confirmed

Whitespace clean.

### State

Blocked on an operator act. Passing back with the blocker rather than closing,
and rather than burning further attempts.
