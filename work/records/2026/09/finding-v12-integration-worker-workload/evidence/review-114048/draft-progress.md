

## 2026-09-07 — baton.claude — claim113667, the workload, the entry, the recipe and the joined proof

**This turn delivers the remaining W110935 scope.** The four paths that had
been absent through four handbacks exist, the second registry entry is added,
and the joined provider-driven proof the acceptance asks for runs against a
real producer bundle. What it does NOT deliver is said in its own section
below rather than at the end.

### Revalidation before acting

The three reviewed hashes in `evidence/review-113446/audit.json` still matched
the tree, all four remaining paths were absent, and the accepted W112630 child
hashes were unchanged. `claude_agent.py` is still
`9a16f57c516660f2ccb2ad56fc404c91bc2c575bf3dd52970f64017b1ee29955` and this
turn did not touch it. Nothing below was acted on without that check.

### What was built, in the order claim113568 scheduled

**`v12/worker/integration_workload.py`** owns everything between an assignment
arriving and a result being composed: the correlation set, the whole-path
preflight, one provider turn through the reviewed `invoke_provider`, its own
read-back of every scheduled path's bytes and modes, the report check and the
conservative ending. It never writes into the target — the provider performs
the import, which is what makes this a model-driven workload rather than a
copier with a result document.

**`v12/worker/integration_entry.py`** is the one-shot composition: read the
launch through `baton_worker`'s own readers, read the assignment through the
contract's, refuse a second turn over a terminal result, run the workload,
publish exactly one result. It is not `baton_worker.main` and consumes no
command frames; three exit statuses say what happened.

**`v12/worker/Dockerfile.integration`** derives from an explicitly SELECTED
provider base digest, taken as a required build argument with no default, and
adds only the integration modules and the entrypoint.

**`v12/python/tests/manager/test_integration_image.py`** plus the second
`parallel_test.py` registration ask the recipe what it says and stage the exact
file set it copies into a directory holding nothing else, then import the entry
there with an isolated child interpreter.

### The three decisions a reviewer should check first

They are in the dated FINDING entry with their reasoning; here is what they
are, so a reader of this record does not have to go looking.

**`refused` is published only when NO provider was started.** That is the
concrete form of the pinned conservative rule, and it is stronger than it may
look: a provider that wrote nothing, said so in a well-formed report, and left
every scheduled path byte-identical still ends `held`.
`test_a_clean_provider_refusal_after_writable_work_is_still_held` asserts that,
including `moved == 0` — nothing changed, and it is held anyway, because
restoration of bytes is not absence of mutation. The cost is real and is named
in FINDING: a legitimate provider-side refusal reaches an operator rather than
settling.

**The bundle identity is measured, not read.** The workload walks the mounted
bundle and recomputes the producer's whole-file manifest;
`test_the_measured_identity_is_the_producers_own_answer` holds it equal to
`compose_bundle`'s own `bundle_digest` and distinct from `envelope_digest`, and
`test_a_file_the_envelope_never_named_changes_the_identity` shows the case that
`read_bundle` accepts and the measurement does not.

**An API gap was found, recorded, and worked around WITHOUT touching accepted
bytes.** `integration_contract` exposes no public bounded reader, no
whole-bundle measurement and no canonical JSON form; all three are needed here
and `contracts.canonical` cannot be imported from a container. The workload
implements its own and holds them equal to their owners by conformance
(`TheTwoSpellingsOfCanonicalJsonAgree`, and the manifest comparison above)
rather than by assertion. The bounded owner change that would remove the
duplication is named in FINDING for whoever schedules it; I did not propose or
make it here.

### The joined proof, and what makes it joined

An accepted bundle composed by `tools/integration_bundle.compose_bundle` from
the real admission world — not a fixture shaped like one — carried through the
real `integration_entry.main` into a provider-driven import of a disposable
target, by an injected provider PROCESS that reads the bundle root, the report
path and the whole path table out of the composed prompt and performs actual
filesystem edits. The result is parsed by the manager's own
`runtime.observed_delivery` after being published through the manager's own
five-step atomic publication rules.

Proved positive: add, edit, edit at `100755`, delete; the manager-bound
identities in the result; the target really carrying the candidate bytes and
mode; `.git/index` and `HEAD` untouched; the composed environment carrying no
ambient credential and the prompt carrying no launch session; and no second
provider turn over a terminal result.

Proved negative, each with the provider count asserted at zero where a refusal
is claimed: a late invalid row that stops an import whose first row was valid,
base-byte and base-mode drift, a read-only directory that is refused rather
than repaired, a link at a scheduled path, an addition over an existing path,
revision drift and an unreadable revision, a foreign assignment, launch, role
or evidence projection, a review that did not accept, an absent test scope, an
existing-test change outside the accepted Job's scheduled scope (and the same
change inside it, admitted), an unreadable envelope, foreign instructions,
provider failure and timeout, missing, malformed, foreign and out-of-scope
reports, a partial import, a clean provider refusal, version-control metadata
that moved, and a result above the delivery bound refused rather than
truncated.

WHERE A DERIVED BUNDLE IS USED, IT IS NAMED IN THE CASE. The accepted world's
checkpoint carries one reviewed path, so cases needing a second row or a
contradictory projection republish a bundle derived from the real one with one
declared difference. Every positive import and every identity comparison runs
against the producer's own published bytes.

### What is NOT delivered, named rather than left to be discovered

No image was built, pulled or selected; no container was started; no credential
was mounted and no live provider was called. `Dockerfile.integration` requires
a base digest operand, so this Work ships no built-artefact gate for the
integration image at all — the deterministic recipe and packaged-layout suite
is what exists, and an artefact gate follows the first selected base digest.
The production descriptor-bound runner remains W110774's. No version-control
mutation of this repository of any kind was performed.

### Verification

| Module | Result |
| --- | --- |
| `tests.manager.test_integration_worker` | 62 passing, 0 failures |
| `tests.manager.test_integration_image` | 12 passing, 0 failures |
| `tests.manager.test_claude_agent` | **172 passing, unchanged** |
| `tests.tools.test_integration_bundle` | **83 passing, unchanged** |

The two unchanged counts are the ones that matter for files this claim did not
touch. Transcript: `evidence/implementation-113667/focused.txt`.

| Path | SHA-256 |
| --- | --- |
| `v12/worker/integration_workload.py` | `1725d917184addad6b589901db447afb5f8e7fbe2f6545d4cdd8924d0a494bc5` |
| `v12/worker/integration_entry.py` | `7cb26737a5694f6e2e5eb2869c28bb5425703ba339ab3633eab388f3608a1679` |
| `v12/worker/Dockerfile.integration` | `afce1f01f41b593d57c19740c353c5ac5fad53e30bde4da4bbd08ce962ae8d28` |
| `v12/python/tests/manager/test_integration_image.py` | `c941e1a99023e43181480928c36936bb9d783e2b44c2687eb57de5ea80d0d78e` |
| `v12/python/tests/manager/test_integration_worker.py` | `77359725e7b875ea4305e183ea56c46fb0fd783001905201211e94bd5315281a` |
| `v12/python/tools/parallel_test.py` | `5bf2cbfbf29c603f07f811a1d5f968257798e1944d91bed0d97fe9aa393bf302` |

The three accepted W112630 child files and `claude_agent.py` are byte-identical
and were not touched; `evidence/implementation-113667/audit.json` binds all of
it.

**Canonical v12 source gate: GATE_SUMMARY**, retained at
`evidence/implementation-113667/subtree-gate.txt`. Handed over red with the
**distribution unchanged**: six boundary-inventory, four live-engine cleanup,
one authority-catalog, one registry error — the same twelve this campaign has
carried throughout, unwaived. The count moved by exactly the tests added. No
new failure and no new diagnostic.

Awaiting independent review. W110774 remains gated until this capability is
accepted.
