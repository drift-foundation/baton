# Progress

## 2026-09-04 — baton.claude — implementation

All eight plan items are done except item 8, which is an owner act after
review and is deliberately not performed here.

### The image (plan 1)

`Dockerfile.claude` moves from `node:22-bookworm-slim` to
`node:22-trixie-slim`. Debian bookworm's unversioned `python3` is 3.11 and
trixie's is 3.13.5, so this one line answers the floor.

Installing `python3.13` beside Debian's own, or importing an interpreter from
`python:3.13-slim` in a second stage, were both considered and rejected for
the same reason: they leave TWO Pythons in the artefact and make "which one
ran" a question every future probe has to answer. Moving the suite leaves
exactly one `python3`, changes no apt package NAME in the recipe, and keeps
Node 22 — which is the provider runtime and the reason this image is not the
reference image's `python:3.13-slim`. A gate case asserts the single
interpreter on the artefact, so a later edit that adds a second one fails.

### The two children (plan 2)

`claude_agent` now composes `PYTHONPYCACHEPREFIX`, `TMPDIR` and
`XDG_CACHE_HOME` for both the provider child and the inner verification child,
all under the private scratch and outside `candidate`. The environment stays
CLOSED — the test that proves `os.environ` is never forwarded now spells the
exact five-member set, so a sixth arriving without a decision fails there.

The provider's `HOME` is untouched: it is still `_prepared_home`, which holds
the link to the mounted bearer. The verification child's `HOME` was the
CANDIDATE ITSELF and is now a private credential-free home beside it — and
deliberately not the provider's home, because this child is provider-edited
code.

The provider half matters as much as the verifier half and an inspection
would miss it: the provider is prompted to run the verification command
itself, and `work` walks the tree AFTER that turn, so a provider that does as
it is asked contaminates the proposal even when the adapter's own verification
is perfectly clean.

`PYTHONDONTWRITEBYTECODE` is not relied on anywhere and the Dockerfile now
says why beside it: `compileall` writes bytecode as its purpose and ignores
that variable, and the adapter composes its children's environments rather
than inheriting the image's, so an image-level `ENV` reaches neither child.

### The operator's rerun (plan 3)

`_derived` gets an ephemeral root under the host's temporary directory —
outside the retained proposal by construction, and removed afterwards rather
than left for retention to reason about. Its environment is the HOST'S with
those three names overridden, which is a deliberate difference from the
adapter: this is the operator's own rerun on the operator's own host, and a
closed environment here would break a frozen command that legitimately needs
the host's `PATH` or locale. What is corrected is where it WRITES.

The proof is taken rather than asserted. The whole candidate is snapshotted by
path AND bytes before the rerun and compared after a successful one; a
difference is a typed `_Lost` naming what was added, removed or rewritten,
bounded to five paths each so 149 cache entries are a diagnostic rather than a
wall. Paths alone would miss an in-place rewrite and digests alone would miss
a pure addition, so both are measured.

The streams change from `DEVNULL` to captured, and the bytes go to this
process's own stderr and nowhere else. The returned record still carries only
`changed_paths`, `verification_argv`, `verification_status` and
`members_present` — a case asserts that member set exactly and that no value
in it contains the diagnostic — so nothing new reaches evidence, retention,
the recap or a Baton message. The bound is 4000 characters with the drop
stated.

### Evidence (plan 5, 6)

Offline: `tests.manager.test_claude_agent` 87 → 92 and
`tests.tools.test_dogfood_operator` 331 → 337, both baselines retained. Whole
tree 3735 cases with the seven failures and one error that reproduce without
this candidate (boundary inventory, catalog, parallel registry, host-state
credentials).

Discrimination measured rather than argued: with `PYTHONPYCACHEPREFIX` removed
from the adapter's composed environment and from the operator's rerun, exactly
six cases fail that pass unmutated —
`test_a_real_compileall_leaves_the_candidate_cache_free`,
`test_every_ephemeral_root_is_outside_the_candidate`,
`test_the_pycache_prefix_is_set_because_compileall_ignores_the_other`,
`test_the_environment_is_composed_and_never_inherited`,
`test_a_real_compileall_leaves_the_retained_candidate_untouched` and
`test_the_ephemeral_root_is_outside_the_proposal_and_is_removed`.

Real image: `tests.manager.test_dogfood_image` 11 → 15 cases, built and
probed, passing. The gate evidence is
`evidence/gate-dogfood-image-2026-09-04.json`, every member of it MEASURED
from the artefact rather than typed beside it. Candidate image
`sha256:d15609b4792faf1e117335f97d9bf88d5d922c087bc89caa49339b2ab9dadccf`:
Python 3.13.5 on Debian 13, one interpreter, Claude 2.1.247, uid/gid
65532:65532, reviewed entrypoint, no manager package, no provider environment
variable, and the committed baseline's 154 files compiling to exit 0 with the
tree byte-identical afterwards and zero cache entries in it. The negative
control is in the same file: an invalid file exits non-zero and names both
`broken.py` and `SyntaxError`.

The compile mount is WRITABLE on purpose. A read-only bind would make the
cache-free result a property of the mount rather than of the composed
environment, and the environment is what the adapter and the operator actually
rely on.

### Not done, deliberately (plan 8)

The image is recorded as a CANDIDATE digest. Building a tag, passing this gate
and passing host tests do not select an image; the owning record selects a
validated immutable digest after independent review, and only that recorded
selection permits a fresh ordinary W71917 attempt. Nothing here promotes or
repairs run6's faulted, cache-contaminated proposal.

### One operational observation

Three of the files this plan schedules — `v12/worker/claude_agent.py`,
`v12/python/tools/dogfood_operator.py` and
`v12/python/tests/manager/test_claude_agent.py` — were mode `0444` in the
working tree, along with three other v12 source files this Work does not
touch. Git records `100644` for all of them and does not track the read bit,
so the state is local and invisible to `git status`. Write permission was
restored on exactly the files this plan authorizes, matching the tracked mode;
the other three read-only source files and every frozen `v12/evidence/*.json`
were left alone.

## 2026-09-04 — baton.claude — response to review-2026-09-04T13-56-04Z

Four P1s, all reproduced and corrected. All four were right, and two of them
were about the difference between a bound that was written and a bound that
was measured.

### [P1] The baseline probe staged the dirty checkout

The case copied `src`, `tests` and `tools` out of the WORKING TREE, which at
packaging time carried several other Works' dirty paths and this candidate's
own edits. `baseline_unchanged: true` therefore proved only that compiling did
not change that dirty staging — it said nothing about the committed baseline
that the test name, the acceptance, PROGRESS and the gate evidence all claim.

`committed()` now extracts the exact commit with a source archive and returns
which commit it was, so the sentence and the measurement are about one tree.
The case binds the commit and asserts its shape. The archive is checked for
content before use — a silently empty one would make every assertion below it
pass over nothing, which this campaign has already been bitten by once — and
the extracted tree is asserted cache-free rather than cleaned up after, since
a committed tree carrying bytecode is its own defect and not this gate's to
quietly repair. Read-only with respect to version control throughout: the
revision is read and an archive is written to a temporary path, nothing else.

The staged snapshot now records DIRECTORIES as well as files, for the same
reason the operator's does.

### [P1] The diagnostic bounded the printing, not the capture

`subprocess.PIPE` accumulated the whole stream in this process for as long as
the 900-second command ran, and the truncation happened after the child
exited. So a shouting command could exhaust the operator's memory with the
terminal bound perfectly intact, and the case that was supposed to prove
otherwise passed.

The child now writes to a file inside the ephemeral root this call already
owns — outside the retained proposal by construction, removed with everything
else — and `_shown` SEEKS to the tail, so at most `MAX_DIAGNOSTIC` bytes ever
enter this process however much was produced. The new case is a discriminator
rather than a repetition: it asserts `subprocess.run` returned no captured
stream at all, which the existing terminal-bound case cannot distinguish.

### [P1] The snapshot omitted directories and read files whole

Only `os.walk`'s FILES were recorded, so an empty `__pycache__` produced an
identical snapshot before and after and was accepted — while being exactly the
entry the finding's candidate-clean rule names. The snapshot is now a typed
inventory of every entry: directories are `dir`, links carry their target,
files carry `file:<digest>`. Typing matters beyond the omission, because a
path that changes KIND compares as "the name is still there" to any
digest-only comparison; there is a case for that too.

Hashing is streamed in 1 MiB blocks, so this operator's memory is no longer a
function of somebody else's build output. The discriminator is the READ SIZE
and not the digest — a case comparing digests alone would agree with the
unbounded version — so it counts the largest single read and asserts no read
asked for a whole file.

### [P1] The child ephemera roots were named and absent

Only the outer directory was made. The three names pointed at directories that
did not exist, and an absent directory is one the child silently ignores; the
reviewer's probe found Python presented with that `TMPDIR` selecting `/tmp`.
The roots are now named in one place, `EPHEMERA_ROOTS`, and created there at
mode 0700 before either child starts — a name added without a directory, or a
directory made without a name, is now impossible rather than merely avoided.

Two cases: the roots exist with the intended mode, and a REAL interpreter given
the composed environment actually selects them for both its temporary files and
its bytecode, with the file it creates proved outside the candidate. The
string-comparison check the review called insufficient is kept beside them.

### Re-run evidence

`tests.manager.test_claude_agent` 92 → 94, `tests.tools.test_dogfood_operator`
337 → 341, `tests.manager.test_dogfood_image` 15 (unchanged count, corrected
content), all passing — 435 in the two offline modules together. Whole tree
3733 with the same seven failures and one error that reproduce without this
candidate.

Exact-image evidence regenerated as
`evidence/gate-dogfood-image-2026-09-04b.json`, schema
`baton.w85497.image-gate/2`, which names what it supersedes and why. The
baseline is now bound to commit `389cdd4edc29a6cdea78291c02adae89253629a2`:
168 entries, 154 files, compiled to exit 0 in the exact image, byte-identical
afterwards, zero added entries and zero cache entries. Candidate image
`sha256:851633956c737c34ba9feeb5157083c42261526445b3f60e0b1f7b133fcc968f` —
a different digest from the first pass, which is expected and is recorded in
the recipe itself: this build is not reproducible across days and the artefact
is SELECTED rather than rebuilt.

The first gate file is kept rather than deleted. Its measurements were real;
what was wrong was the tree they were taken over, and the superseding file
says so. Deleting evidence because a later pass found its scope too narrow
would leave the correction chain unreadable.

### Still open

Independent review. The image remains a CANDIDATE digest; selection is the
owning record's act after review, and nothing here permits a W71917 retry.

### One housekeeping note for the operator

The reviewer's reproduction left `/tmp/w85497-parent-4s2ajm8x` on this host
and recorded it for operator cleanup. This implementer has not removed it: it
is the reviewer's artefact and their own record names it.

## 2026-09-04 — baton.tuner — response to review-2026-09-04T14-44-23Z

All four requested source corrections are implemented in the authorized
adapter/operator paths, with five discriminating cases added to the scheduled
test files.

The worker now creates both complete child environments before the provider
runs. Every predictable directory is created exclusively: an existing name is
a refusal, never `exist_ok` state to chmod. Immediately before each child, the
adapter revalidates every path component with `lstat`, requires ordinary mode-
0700 directories beneath the exact scratch root, and refuses links or special
entries. A provider regression replaces both verifier roots with links to the
candidate; the adapter refuses before verification and writes no cache entry
through either link.

The operator now creates its verification root beneath explicit `/tmp`, not
the ambient `tempfile` selection, and refuses any resolved candidate/proposal
descendant before starting the command. All three child-visible roots are
created at mode 0700. Cleanup no longer uses `ignore_errors=True`: an
obstruction becomes typed `_Lost` naming the residue path and exception class,
without reproducing child bytes.

Candidate snapshots use `lstat` for every entry. FIFOs, sockets, devices and
other special entries are typed and never opened. Regular files are opened
with no-follow/nonblocking flags, validated by `fstat`, and still digested in
1 MiB chunks. The post-command FIFO case runs against a real FIFO; this
managed test host forbids pathname-socket binding, so the socket regression
supplies the kernel type at the `lstat` seam and makes `os.open` a tripwire,
including on the post-command snapshot path.

Offline verification passes all 440 cases:

`PYTHONPATH=src:.:../worker python3 -m unittest tests.manager.test_claude_agent tests.tools.test_dogfood_operator`

The required real-image gate was attempted, not skipped, and could not start:
Docker is installed but this managed context receives permission denied on
`/var/run/docker.sock`. Per managed-turn policy no escalation was requested.
`tests.manager.test_dogfood_image` therefore ran zero cases and failed its
required prerequisite exactly as designed. The exact-image rerun, regenerated
evidence, and immutable replacement proposal remain pending an authorized
Docker-capable provider; the candidate digest is not selected and W71917 must
not be retried.

## 2026-09-04 — baton.tuner — Docker-provider result revalidation

`baton.ops` reported that the Docker-capable module passed its existing 15
cases, but also reported candidate image
`sha256:851633956c737c34ba9feeb5157083c42261526445b3f60e0b1f7b133fcc968f`.
That is exactly the image digest recorded before this correction. The source
bytes are demonstrably different: the prior immutable proposal carries
`claude_agent.py` digest
`sha256:4ccf903c043ab0d989dc44059f6bba0cc0414bd25fc1d33d40e50296d283aa23`,
while the corrected working file is
`sha256:51a6bf29e07cce5e010083f31ca61af54686265dc98a9a75763877fd1357e3b5`.

The image gate explained the false acceptance: it bound the bytes of
`baton_worker.py`, but asserted only the presence of `claude_agent.py`. A stale
adapter could therefore pass every existing artefact case. The scheduled
`test_dogfood_image.py` now adds a sixteenth case that compares the exact
`/opt/baton/claude_agent.py` digest in the built image with the current recipe
input. This is necessary acceptance coverage, not a new product boundary.

No schema-2 evidence was rewritten and no replacement proposal was packaged:
both would falsely bind old-image evidence to new source. The Docker-capable
gate must be rerun with the new discriminator, report 16/16, and record the
new image digest plus the measured adapter digest before schema-3 evidence and
the immutable proposal can be produced. The image remains unselected and
W71917 remains ineligible for retry.

## 2026-09-04 — baton.tuner — corrected image gate and review package

The Docker-capable rerun answered the discriminator rather than repeating the
old gate. `baton.slaw` rebuilt and preserved the current worker context as
`baton-w85497-dogfood:candidate3`; all 16 image cases passed in 1.901 seconds.
The new immutable image ID is
`sha256:9a21a7aa3920ce921fee160d7d478a50b7827eb9e883e703ce27ce2398105851`,
and `/opt/baton/claude_agent.py` measured
`sha256:51a6bf29e07cce5e010083f31ca61af54686265dc98a9a75763877fd1357e3b5`,
exactly matching the corrected source.

Append-only schema-3 evidence is recorded at
`evidence/gate-dogfood-image-2026-09-04c.json`. It explicitly supersedes the
schema-2 image evidence because that image predates the containment correction
and its 15-case gate did not bind adapter bytes. Neither earlier evidence file
was edited or removed.

The replacement review package is assembled at
`/tmp/w85497-proposal-2026-09-04T18-50-58Z`. It contains the six scheduled
source/test paths, FINDING/PLAN/PROGRESS, all three chronological image-evidence
files, a base-relative patch, per-path base/candidate digests, the exact image
and adapter digests, explicit exclusions for every other dirty checkout path,
and self-contained digest recomputation instructions. The package is made
read-only after recomputation. It remains a review candidate, not a selected
image, and no W71917 attempt is authorized by its existence.

## 2026-09-04 — baton.tuner — response to review-2026-09-04T18-59-48Z

The surviving-descendant P1 is reproduced and corrected at the verifier launch
boundary. The prior implementation created the right roots and revalidated
their pathnames immediately before launch, but the verifier still resolved
those same provider-writable names. The check/use interval therefore remained.

The adapter now opens the verifier's `HOME`, `PYTHONPYCACHEPREFIX`, `TMPDIR`,
and `XDG_CACHE_HOME` directories before the provider starts and retains those
four directory descriptors through the provider turn. Verification receives
only `/proc/self/fd/<n>` names plus the exact inherited descriptor set. Its
last pre-launch validation uses `fstat` on the held objects, not `lstat` or
`realpath` on names the provider controls, and refuses a removed object, a
mode change, or an environment/descriptor mismatch. Every descriptor closes
in the outer `finally`, including provider failure and no-change paths.

Two cases are added to the already scheduled
`v12/python/tests/manager/test_claude_agent.py`. One proves all four verifier
roots are descriptor-bound and explicitly inherited. The discriminator
replaces `verification-ephemera/pycache` with a symlink to `candidate` inside
the injected launch seam — after the final held-object validation and before
the real interpreter resolves its environment. Real `compileall` exits zero,
the candidate remains cache-free, and bytecode appears beneath the renamed
original directory object. The existing static provider-symlink refusal stays
and now refuses the removed held object before verification.

Offline verification passes all 442 cases:

`PYTHONPATH=src:.:../worker python3 -m unittest tests.manager.test_claude_agent tests.tools.test_dogfood_operator`

The corrected adapter digest is
`sha256:516d350e3ca367b61fd33520cbfe3de4d69dbe9dee0da0a6553bd37c3349b60c`.
Focused `git diff --check` passes. The required exact-image gate was attempted
with the recorded command and could not start because this managed tuner is
still denied `/var/run/docker.sock`; it ran zero cases and failed the required
prerequisite rather than skipping it. A Docker-capable provider must rebuild
from the current worker context, run the full 16-case image gate, report the
new immutable image and embedded-adapter digests, and preserve the image before
schema-4 evidence and a replacement immutable proposal can be produced. The
schema-3 evidence and its image are superseded candidates, not selected, and
W71917 remains ineligible for retry.

## 2026-09-04 — baton.tuner — descriptor-bound image gate and packaging

`baton.slaw` rebuilt the current worker context and preserved it as
`baton-w85497-dogfood:candidate4`. The required exact-image module passed all
16 cases in 1.979 seconds. The new immutable image ID is
`sha256:979f11d53433f2930d69b70d81e265332547895cbd674e3e8b190cafb236243f`;
its `/opt/baton/claude_agent.py` digest is
`sha256:516d350e3ca367b61fd33520cbfe3de4d69dbe9dee0da0a6553bd37c3349b60c`,
exactly matching the current descriptor-bound source.

Append-only schema-4 evidence is recorded at
`evidence/gate-dogfood-image-2026-09-04d.json`. It supersedes schema 3 because
that image predates the surviving-descendant correction; no earlier evidence
file was edited or removed.

The replacement package is assembled at
`/tmp/w85497-proposal-2026-09-04T19-27-03Z` from the same declared base
`389cdd4edc29a6cdea78291c02adae89253629a2`. It carries the six scheduled
source/test paths, FINDING/PLAN/PROGRESS, all four chronological image-evidence
files, the base-relative patch and per-path digests. Every unrelated dirty
checkout path is explicitly excluded. The package remains a review candidate,
not an image selection, and W71917 was not retried.
