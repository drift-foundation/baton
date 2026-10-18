# Implementer progress — W321688

## Claim 321732 (baton.claude, impl) — stable flat binding and recovery contract

Read first: canonical `detail` at snapshot321730 (queued, unclaimed, routed
baton.impl, no next, no obligations, no open blockers, binding revision 1 at this
directory, parent W39435, blocking W321689/W321690/W39435), then the standalone
claim. Then `work-events` complete, events 321688 → 321732, `next_after` null;
`thread` T321688, its single message, no pagination. Then this dossier's FINDING
and PLAN, the parent pilot record
`work/records/2026/10/finding-v12-development-coordination-pilot/FINDING.md`
including M321677, and W39435's PLAN for the approved flat-set direction.

**Base revalidated on pickup, as the PLAN requires.** The PLAN names
`3dcf6dc4bcee97e932d17c93ac13c5811b3af188`; that is HEAD, and the product tree is
clean. `PREPARATION-PINS.json`-style drift was not applicable here — this Work
edits source rather than composing a packet — but every file I touched was read at
HEAD before editing. W61981's and W321528's packets and pins were not opened.

### What was missing, and what it now is

The assessment's finding: identities and history exist, and there is no canonical
dossier binding at all. `authority/api.py` had `create_work` and projections and
no record address; `authority/schema.py` documents clean initialization; and
`stack_command.COMMANDS` had no record verb, so a deployed bundle could not answer
"where does this Work's record live" even if an API existed.

Delivered, smallest shape that satisfies the acceptance:

**`authority/dossier.py` (new)** — the locator grammar and nothing else. No
store, no filesystem, no I/O. One flat segment; no `/`, `\` or `:`; no dot- or
hyphen-prefix; lowercase, digits, single hyphens, bounded at 96, ending in a
required 8-hex collision suffix. Evidence references are repository-relative with
no absolute, empty, dot or parent segment; digests are `sha256:<64 hex>`.

**`authority/schema.py`** — `work_dossier` (work_id primary key, locator UNIQUE,
operation_id UNIQUE) and `work_dossier_evidence` (per `(work_id, reference)`, with
its digest and act). Both directions unique because they answer different
questions: one record per Work, one Work per record. **No route, phase, parent or
campaign column** — the absence is what enforces W39435's direction rather than a
rule somebody has to remember. SCHEMA_VERSION 5 → 6.

**`authority/core.py` + `api.py`** — `bind_dossier`, `dossier_of`,
`dossier_work`, `record_dossier_evidence`, `dossier_evidence`, on the TRUSTED
BOOTSTRAP face. A record's address is allocated once by whoever stands the Work
up; putting it on the session would have let a claimant rename its own durable
record. The reads are there too because operators, materializers and reviewers
hold no claim and should need none.

**`tools/dossier_command.py` (new) + `stack_command.py`** — the installed
`record` verb: `bind`, `read`, `cite`, `verify`, `recovery-manifest`,
`recovery-check`. Read verbs take a read-only authority handle, so asking a
serving deployment where a record lives takes no write lock on it.

**THE DIVISION OF LABOUR IS THE DESIGN DECISION.** The authority stores
references and NEVER OPENS A FILE — DB-1 forbids external I/O inside a store
transaction — so filesystem resolution is the command's. `cite` digests a file and
hands over the digest; `verify` compares citations against a root. That is also
what makes the honest refusal possible at all: without a recorded digest, "a file
by that name exists" would be the strongest available claim.

### Acceptance, clause by clause

| clause | where it is driven |
| --- | --- |
| exact authority+Work → one stable dossier | `test_an_exact_authority_and_work_resolve_to_one_dossier`, and through the command |
| exact retry replays | `test_an_EXACT_RETRY_replays_the_first_answer` |
| changed retry refuses | `test_a_CHANGED_RETRY_is_refused_as_reused_operands` |
| collision refuses, both sides | `test_a_COLLISION_is_refused_and_names_the_holder`, `test_REBINDING_under_a_new_operation_is_refused` |
| escape refuses before partial effects | `TheLocatorGrammarRefusesPathsAndEscapes` — each asserts the store is still unbound |
| wrong authority refuses | `test_ANOTHER_AUTHORITYS_work_id_is_not_in_this_store`, `test_a_store_opened_under_the_WRONG_EXPECTED_UUID_refuses` |
| stale/rewritten evidence refuses | `test_the_SAME_reference_at_a_DIFFERENT_digest_is_refused` |
| relations cannot rename it | `RelationshipChangesMoveNothing` — labels (via the session), route handlers, reopen |
| absent/inaccessible evidence is honest refusal | `VerifyResolvesCitationsHonestly` — `present`/`absent`/`unreadable`/`changed`/`not-a-regular-file` are five outcomes, not one |
| closed version compatibility, explicit refusal | `TheSchemaBoundaryIsClosedAndExplicit` — older AND newer refused, and the file is byte-identical after a refused open |
| complete recovery set; partial refuses | `test_the_manifest_names_the_WHOLE_recovery_set_with_digests`, `test_a_PARTIAL_instance_is_refused_as_not_recoverable` |
| missing/mismatched member blocks admission | `test_a_CHANGED_member_is_refused`, `test_a_MISSING_member_is_refused_and_named` |
| possible old writer blocks admission | `test_a_POSSIBLE_OLD_WRITER_holds_admission_even_when_bytes_match` |
| identities/receipts/history/artifacts survive | `test_the_RESTORED_authority_still_answers_identity_record_and_history` |

`RECOVERY.md` is the pinned procedure: ownership, the compatibility boundary, the
closed member set, how a cut is taken, the three refusals, and readback as
acceptance. **Slawomir owns production backup and restore**; the rehearsal is
disposable fixtures only and no real instance was read, copied or restored.

### THE ONE THING I ALLOCATED THAT IS NOT MINE TO ALLOCATE

Every previous authority schema bump cites an **approver ruling** that allocated
the number — M33752 for 2, M35002 for 4, M35127 for 5. I allocated **6** because
the binding cannot be stored without a relation to store it in, and the ruling for
it is **OWED rather than cited**. The schema comment says so in terms. Treat a
missing ruling as a reason to withhold acceptance of this number, not as
permission to renumber it later. The retention consequence is also stated rather
than hidden: any retained v12 authority at 5 becomes unreadable by this build,
which is the documented boundary the refusal and `RECOVERY.md` exist for.

### Test paths changed, and why — standing authority (owner 2026-09-13)

- `tests/authority/test_dossier.py` (new), 34 cases.
- `tests/tools/test_dossier_command.py` (new), 28 cases.
- `tests/authority/test_boundary.py` — two EXHAUSTIVE REGISTRIES extended
  additively: the authority's table set, and the bootstrap face's public surface.
- `tests/authority/test_session.py` — the configuration/session disjointness set,
  likewise additive, with the reason the five names are configuration-side.
- `tests/authority/test_catalog.py` — the suite file list, so the new module is
  part of one gate rather than a loose file.

No existing assertion was weakened or removed; every edit adds members to a
registry that exists to be exhaustive.

### Measured

    tests.authority.{test_store,test_principal_scope,test_work_labels,
      test_work_label_exposure,test_operations,test_session,test_catalog,
      test_assignment,test_contract,test_claim_result,test_identity,
      test_dossier} + tests.tools.test_dossier_command ... 426 PASS  0.81s
    tests.tools.test_bootstrap + tests.tools.test_stack ..  254 PASS 43.7s
    tests.tools.{test_version,test_instance,
      test_attempt_logs_command} .......................... PASS (with
      test_packaging; see the finding below)
    tests.integration.test_driver, tests.integration.test_reconciliation,
      tests.job_manager.{test_managed_integration_capacity,
      test_review_driver,test_tool}, tests.manager.{test_intake,
      test_w197661_verifier}, tests.tools.{test_accepted_base,test_pool}
      .................................................... 984 run, 4 failures,
      all four pre-existing and owner-deferred (below)

### THREE RED RESULTS THAT ARE NOT MINE, PROVEN RATHER THAN ASSERTED

I ran the boundary analyzer against the **committed** authority package
reconstructed from HEAD and compared offender lists.

1. `tests.authority.test_boundary.test_no_refusal_renders_an_unbounded_value`
   and `test_every_named_site_covers_the_paths_it_was_written_for` —
   **IDENTICAL offender lists at HEAD and in my tree**: four unbounded refusal
   diagnostics in `authority/store.py` (`_writable` `what`; `_connect_readonly`
   `type(failure).__name__` twice and `failure`). My own sites were offenders at
   first and are now proven bounded — `label_of(what)` in the three new exported
   helpers, `name_of(count)` in `core.py`. **I did not touch `store.py`**: the
   fix is product prose in a file this Work does not own, and changing an
   accepted refusal's wording to make a gate green is not an implementer's call.

2. `tests.authority.test_boundary.test_the_bootstrap_face_configures_and_reads_and_never_acts`
   — after my additive registry entry the ONLY remaining difference is
   `open_readonly`, which exists on the facade at HEAD and is absent from the
   committed expectation. Pre-existing registry omission. **Deliberately not
   fixed**: if some Work intends to remove that method, a registry entry from me
   would mask the decision. Reported for the reviewer instead.

3. `tests.integration.test_driver` — 4 failures asserting a workspace root no
   longer exists. **W270664 owns workspace deletion safety, is parked at
   baton.decide by owner deferral, and its current checkpoint says "preserve all
   known failures" and "ordinary initial Job completion preserves workspace and
   performs no deletion".** Known, owned and deliberately preserved. Also not a
   tmpfs artefact: they persist with a disk-backed `BATON_V12_DISK_ROOT`.

### ONE RED RESULT THAT *IS* MINE, AND IS CORRECT

`tests.tools.test_packaging.test_every_subcommand_this_command_serves_is_offered`
fails because it runs the **built bundle** at `v12/python/build/out/distro`, whose
build stamp is commit `446fa8f7`, dated 2026-09-21 — months before HEAD. It
offers every current verb except `record`.

That is the test doing its job: a new subcommand is not installed until the
bundle is rebuilt. **A build is not authorized by this claim** (M321677 selects
preparation, no deployment or live run), so I did not run one. `just build` then
`just test-packaging` is the step that closes it, and the owner selects when.
I did not weaken the test to hide this.

### Not claimed

No live provider or engine; no deployment, bundle build or configuration change;
no production backup or restore and no live instance read, copied or restored; no
v11 store adoption or migration; no broad dossier migration, graph UI or
navigation views; no Git mutation. W61981 and W321528 packets and pins untouched.
No existing v11 dossier locator moved — nothing in this change reads or writes a
repository record path at all.

The pilot itself is not run: this is P2's provider, and W321689 (owner
disposition) and W321690 (joined rehearsal) consume it under their own edges.
W39435's broader obligations are not closed by this child.

Cumulative verification this claim: roughly 48 seconds of measured deterministic
test execution across the vectors above, plus two boundary-analyzer comparisons
against HEAD. No live or long-running suite was run.

A human Git checkpoint is due on acceptance, not on this pass; suggested message:
`v12: bind one Work to one canonical flat dossier (W321688)`.

### Files

Product: `authority/dossier.py` 4508ff3577f0 (new), `authority/schema.py`
e96f702484a8, `authority/core.py` e6569eca4398, `authority/api.py` df6d90dd6d15,
`tools/dossier_command.py` 1d6d6db806ea (new), `tools/stack_command.py`
c86c0a4a536c. Tests: `tests/authority/test_dossier.py` ab493c66d88c (new),
`tests/tools/test_dossier_command.py` 51d1c377af66 (new),
`tests/authority/test_boundary.py` b58d1ccee28a,
`tests/authority/test_session.py` 4804ed2651d3,
`tests/authority/test_catalog.py` 7e70f111ed33. All under `v12/python/`.
Dossier: this record, `RECOVERY.md`, `CANDIDATE-321732.json` 56be03a16398.
FINDING and PLAN are the reviewer's and untouched.


## Claim 321989 (baton.claude, impl) — review P1a/P1b corrected

APPEND-ONLY, per the rule the W316915 record now carries. Read first: `detail`
at snapshot321988, `work-events` after 321879 (events 321887→321989), `thread`
T321688 all four messages, then `review-2026-10-18T08-25-00Z.md`, the current
PLAN and `evidence/review-321887`.

**The schema ruling I said was owed is granted.** Owner M321965/M321966 approve
authority schema 6 for the pilot with explicit refusal of schema 5 and no
migration, old stores preserved with their matching old build. The candidate
marked that ruling owed; it is now cited rather than owed.

### P1b — evidence resolution escaped the root

Reproduced: a reference the authority accepts as relative, symlinked to a file
outside `--root`, could be cited and then verified as intact — **exit 0 twice**.
`os.path.join` plus `isfile`/`open` both follow symlinks, so out-of-root bytes
were being certified as this dossier's evidence under this root.

`_contained_read` replaces that. It refuses a symlink **at every depth**, not
just the leaf — an intermediate `a -> /tmp` puts `a/b` out of root as surely as
a final link does. It refuses a link pointing *inside* too, because a target can
be replaced after the answer, so a contained resolution cannot depend on where
one pointed at check time. And the race is closed by reading the descriptor it
checked: `O_NOFOLLOW` open, `fstat` that descriptor, digest that same
descriptor, nothing re-resolved by name after the decision. Five distinct
states now, not three. `_cite` validates the grammar **before** any filesystem
access, which was P1b's second half.

### P1a — recovery completeness was not validated

Reproduced by the reviewer through the public command: a synthetic manifest
naming one ordinary file as `authority_store` returned 0 with `faults: []` and
`schema_compatible: true`; a manifest over three dummy files with no instance
identity or provenance also returned 0.

Corrected, and the document shape had to change with it —
`baton.v12.instance-recovery-set/1` could not express a closed set, so it is
now `/2`:

- the instance is validated first (schema, `authority_uuid`, `destination`);
- the member set is **closed** — every required store and provenance entry;
- provenance is bound **by value**: `deployment.json` digested, `identity` and
  `runtime` bound by canonical bytes;
- sidecar **bytes** are digested, not their names — a `-wal` is where a store's
  newest commits live;
- retained `state`/`logs`/`repository` are bound by content manifest (sorted
  `path:digest`, count, byte total), which binds the bytes without copying a
  deployment's retained output into a manifest;
- `_check` requires that closed set, honours `missing_members`, and validates
  provenance and retained trees;
- **compatibility and identity are read from the restored store's own `meta`**,
  not from the emitting build's constant — that was the review's point, and
  there is deliberately no public API for it because `Authority.open` *refuses*
  an incompatible store, which is correct and is why it cannot answer "which
  version is this";
- `--root` is **always** honoured — as-recorded relative to the manifest's
  destination, or side-by-side with `--flat`. Before, `--root` was ignored
  without `--flat` and the original absolute paths were checked, so a restore
  was never actually examined.

**And a clean report no longer claims the old runtime stopped.** The review is
explicit that a destination directory disappearing is not proof of cessation,
and the first cut treated exactly that as the accounting — my own test helper
called it `accounted()`. Now `operator_must_account_for_writers` is always true
and the clean message says these checks found no fault and do **not** establish
that the previous instance stopped, naming that no absence of a directory proves
it.

### The misleading fixtures, replaced

The old recovery class built two dummy SQLite headers, cited a synthetic digest
with no matching artifact, and omitted `deployment.json` while expecting a
complete restore to succeed — it asserted the defect. It is removed and replaced
by `tests/tools/test_dossier_recovery.py`, whose authority store is a **real**
one created by the real opener (so its own `meta` answers the identity and
compatibility questions), with real provenance and real retained trees.

### ONE DEFECT OF MY OWN, found by driving it

The manifest's read-only identity read **creates** a `-shm` beside a WAL store —
W316915's own measurement, in this very repository. Reading identity *after*
digesting the members produced a manifest that omitted a sidecar its own read had
just made, and `_check` then correctly flagged it as a writer signal: this
program making its own evidence look tampered with. Identity is now read first,
so whatever the read creates is part of what the manifest describes.

### Measured

    test_dossier_recovery (new) + test_dossier_command
      + tests.authority.test_dossier ....................... 81 PASS  0.216s
    isolated PyInstaller bundle build ..................... built
    tests.tools.test_packaging against that bundle ........ 10 PASS, 1 FAIL

`test_every_subcommand_this_command_serves_is_offered` **now passes** — the
`record` verb is offered by a real bundle, which is the failure I reported last
claim. The one remaining failure is the version stamp: the bundle was built from
a non-repository isolated copy, so its stamp says "source commit unknown". That
is an artefact of building outside a checkout and is not about the `record`
verb; a build from the repository records its commit. I did not weaken it.

### Delivery, as the review directed

The reviewed source-tree bytes are **preserved unchanged** — the review said to
preserve them and not overwrite unrelated work. This correction is delivered as
an isolated candidate at `/home/sl/baton-instances/w321688-321989-candidate`
plus `correction-321989/correction.patch` applied to those bytes, with every
digest in `correction-321989/CORRECTION.json` 90057d44508c. No Git operation of
any kind was performed. `authority/dossier.py`, `core.py`, `schema.py`,
`api.py` and `tools/stack_command.py` are byte-identical to the reviewed
candidate.

### Not claimed

No live engine or provider; no production restore or live instance access; no
host product edit this claim; no Git operation; no deployment — the bundle build
is local preparation into an isolated output, which the review states needs no
extra approval. W61981, W321528 and other Work bytes untouched. The pilot is
still not run: W321689 and W321690 consume this under their own edges.

Cumulative verification this claim: about 3 seconds of focused deterministic
execution, one isolated bundle build, and the packaging vector against it.


## Claim 322124 (baton.claude, impl) — review P1/P1/P2 corrected

APPEND-ONLY. Read: `detail` at snapshot322123, `work-events` after 321989
(events 322053→322124), `thread` T321688 all five messages, then
`review-2026-10-18T08-48-00Z.md`, the current PLAN and `evidence/review-322055`.

Owner schema 6 is resolved (M321965/M321966) and is not reopened here. All
three remaining findings were real.

### P1 — the parent-directory replacement race was still open

My previous fix lstat'ed each component and then opened the **whole
pathname**: `O_NOFOLLOW` guards only the final component, so replacing a parent
between its lstat and the open let the open resolve through a new symlink and
return outside bytes as `present`. The reviewer reproduced it with a real
interleaving. My static symlink tests could not have caught it, and I said they
closed a race they did not.

Now every component is **opened relative to the previous component's
descriptor** with `O_DIRECTORY|O_NOFOLLOW`. The path is never re-resolved by
name, so a replacement after a component is open cannot change what that
descriptor refers to — check and use are the same act. The final open adds
`O_NONBLOCK` so a FIFO cannot hang the check, and `fstat` refuses anything but a
regular file. A symlink at any depth, including the root itself, is named
`escapes-root`; Linux answers `ENOTDIR` for `O_DIRECTORY` on a directory link,
so the naming `lstat` runs only *after* the open has already refused and adds no
window.

### P1 — the retained inventory was iterated, not required

Deleting `retained` from a generated manifest and every restored tree with it
returned 0 with a clean report — the completeness defect again, on the new axis.
`RETAINED` is now a **closed required inventory** on both sides, with
`required_retained` declared and compared. An omitted field, an absent
configured root or an unreadable tree is a fault; only a root the instance
contract does not name is legitimate absence.

Two audit findings in the walk were also right. `os.walk` without `onerror`
**silently skips** what it cannot read, so an unreadable subtree shrank the
manifest and still looked complete — it now has a handler and reports
`unreadable`. And **directory symlinks appear in `dirnames`, never
`filenames`**, so my walk bound none of them despite a comment claiming it did;
they are recorded now.

### P2 — the read-only compatibility boundary

I ran raw `mode=ro` SQLite and recorded the `-shm` it created in the manifest.
The reviewer is right that including the write does not make the check
read-only, and `_check` called it *after* reporting the set unchanged — so a
check could modify the set it had just certified.

`Authority.stored_identity` is added as the supported public observation: the
authority's own read-only probe, the one `open` itself uses, exposed because
`open` **refuses** an incompatible store and therefore cannot answer which
version it is. `_stored_identity` no longer runs SQL and probes a **copy** of
the store and its sidecars. And `unchanged_after_observation` re-reads every
store and sidecar after the probe, so byte identity is **measured** rather than
asserted — on success and on refusal.

### Measured

    test_dossier_recovery + test_dossier_command
      + tests.authority.test_dossier ....................... 92 PASS  0.231s
    isolated PyInstaller bundle ........................... rebuilt
    tests.tools.test_packaging against it ................. 10 PASS, 1 FAIL

The packaging stamp limitation, recorded honestly as asked: the one failure is
`test_it_says_its_version_with_NO_checkout_and_NO_repository_tool`, because the
bundle was built from a non-repository isolated copy and its stamp says "source
commit unknown". An artefact of building outside a checkout, not a defect in the
`record` verb; the subcommand-offered case passes and `record` runs from the
bundle.

### The subtree-to-repository path mapping

Stated explicitly, as the review's operational finding required. **The isolated
candidate root IS the Python subtree**, so repository paths map by stripping the
`v12/python/` prefix: repository `v12/python/tools/dossier_command.py` is
candidate `tools/dossier_command.py`. `CORRECTION.json` carries this under
`SUBTREE_TO_REPOSITORY_PATH_MAPPING` with the candidate root's contents.

### Delivery and not claimed

Isolated candidate plus `correction-322124/correction.patch`;
`CORRECTION.json` 12de0922b84f. Corrected: `dossier_command.py`
7b477aa81381, `authority/api.py` 9c8562b77d20, `test_dossier_recovery.py`
9dffaff5d041, `test_dossier_command.py` fbb88efcbe7f. Unchanged from the
previous correction: `authority/dossier.py`, `core.py`, `schema.py`,
`tools/stack_command.py`. The reviewed source-tree bytes are preserved; no host
product edit this claim and no Git operation of any kind.

No live engine or provider, no production restore or live instance access, no
deployment — the bundle build is local preparation into an isolated output. No
broad suite. W61981, W321528 and other Work bytes untouched; W321689/W321690/
W39435 remain gated.

Cumulative verification this claim: about 3 seconds of focused deterministic
execution plus one isolated bundle build and the packaging vector against it.


## Claim 322217 (baton.claude, impl) — wired to the real instance contract

APPEND-ONLY. Read: `detail` at snapshot322216, `work-events` after 322124
(events 322134→322217), `thread` T321688, then
`review-2026-10-18T09-04-00Z.md`, the current PLAN and `evidence/review-322176`.
Schema 6 stays resolved; the owner near-completion exception applies.

### P1 — recovery was agreeing with a double, not with the contract

The reviewer's reproduction is decisive. `tools.instance.emit` does **not**
emit `authority_store`, and its validator **requires** `command`, `state`,
`logs` and `repository`. My code looked for an `authority_store` member and
hand-validated only schema, UUID and destination. So a *genuine* instance
refused with `missing_members=[authority_store]`, while a handcrafted selector
carrying an invented member and missing three required ones passed — and a
restore with all three retained trees deleted returned 0 clean. That is
producer/consumer disagreement dressed as validation, and my fixture was the
thing I had agreed with.

Corrected by consuming the contract instead of paraphrasing it:

- `tools.instance.malformed` is the validator now, in its own words.
- the authority store resolves through `tools.instance.layout()`, its **actual
  supported declaration** — `emit` has no such member precisely because the
  layout owns where stores live ("derived, never configured twice").
- `job_store` and `control_store` are cross-checked against what the
  destination derives, so a selector disagreeing with its own destination
  refuses.
- `state`, `logs` and `repository` are **required** by `instance._MEMBERS`, so
  `not-configured` is no longer a bypass: a manifest claiming one was never
  configured is a fault (`not-configured-but-required`).
- the restored selector is read, validated and its layout derived, so the
  restored instance/config binding is **verified** rather than taken from the
  manifest.

### The remaining probe-on-original

`_manifest` still called `_stored_identity` without `scratch`, so only `_check`
copied — and the comment beside it still described creating an SHM before
hashing it. Both commands probe a copy now, and neither claims the other's
evidence.

### The fixture is real now

`instance.layout` + `instance.emit` build the selector and
`instance.malformed` must **accept** it — asserted in `setUp`, so the fixture
cannot drift back into a double. Real `Authority`, `JobStore` and `ControlStore`
through their own supported openers; no dummy SQLite headers. And every path is
**derived** from the layout rather than spelled, because the contract's
directory names are its business — `stores` is `db`, `repository` is `repo` —
and a test hard-coding either would assert against a guess. Retargeting those
turned three green assertions red until I fixed them, which is the point.

### Measured

    tests.tools.test_dossier_recovery ..................... 41 PASS  0.219s
    + test_dossier_command + tests.authority.test_dossier
      + tests.tools.test_instance ....................... 211 run,
      210 PASS, 1 FAIL                                          0.624s

The one failure is
`tests.tools.test_instance.TheBootstrapPreparesTheRepositories.test_the_source_is_INFERRED_from_this_distribution_s_checkout`:
"no checkout containing v12/justfile was found". It **passes in the repository
tree**, measured this claim. Same class as the packaging build-stamp
limitation — an artefact of running the suite outside a checkout, not a defect,
and not weakened. `tools/instance.py` is byte-identical: the contract is
consumed, never broadened or weakened to match a test.

### Delivery and not claimed

`correction-322217/CORRECTION.json` 7123abff9369. Corrected:
`dossier_command.py` ed5d8b5581b6, `test_dossier_recovery.py` 40c8f2bca027.
Unchanged from the previous correction: `authority/api.py`, `dossier.py`,
`core.py`, `schema.py`, `tools/stack_command.py`, `test_dossier_command.py`.
The descriptor-containment correction the reviewer accepted is preserved intact.

No live engine or provider, no production restore or live instance access, no
host product edit this claim, no Git operation of any kind, no deployment, no
broad suite. W61981, W321528 and other Work bytes untouched;
W321689/W321690/W39435/W321528 gates remain, and the human checkpoint is
separately W322125. Packaging stamp limitation unchanged and still disclosed;
no new package signoff is claimed.

Cumulative verification this claim: under a second of focused deterministic
execution.


## Claim 322286 (baton.claude, impl) — the restored selector, required and bound

APPEND-ONLY. Read: `detail` at snapshot322285 (queued, unclaimed, routed
baton.impl, next baton.bug, no obligations), then the standalone claim;
`work-events` after 322217 (322243 → 322286); `thread`; then
`review-2026-10-18T09-12-00Z.md`, the current PLAN and FINDING, and
`evidence/review-322245`. **The finding was correct and I reproduced both
halves of it at the real public boundary before changing anything.**

### What was accepted that should not have been

`recovery-check` read the restored instance selector **only if it happened to
exist**, so deleting it added no fault. A selector that did exist was validated
structurally — and its `instance_digest`, which the manifest had recorded all
along, was never compared, and its `authority_uuid` was never compared with the
set's. So both of these returned exit 0, `faults: []` and
`schema_compatible: true`:

- the restored selector removed after a complete restore;
- the restored selector structurally valid, carrying a different 32-hex UUID.

A set whose own instance document is gone, or describes somebody else's
deployment, is not a restorable deployment. Saying so after an operator admits
it is too late, which is the whole reason this command refuses rather than
reports.

### The correction, and the one rewrite that is SUPPORTED rather than tolerated

The selector is now a required member with its own closed states —
`not-in-manifest`, `absent`, `unreadable`, `malformed`, `another-authority`,
`changed`, `relocated`, `present` — and every state but the last two is a
fault. `another-authority` is kept distinct from `changed` deliberately: intact,
valid bytes that name the wrong deployment is the loudest version of this fault
and collapsing it into "changed" would lose that.

**The review asked for the relocation case to be bound explicitly instead of
accepting arbitrary changed bytes, and that could not be done from a digest.**
A relocated restore legitimately rewrites the selector's `destination`, which
changes its digest, so digest-only leaves two choices: accept any rewrite, or
refuse every restore that moved. Neither is honest. So the manifest now carries
the selector **document** — `baton.v12.instance-recovery-set/3` — and the one
legal rewrite is `destination` set to the root the set actually landed under,
with every other member byte-identical. A rewrite to some third path is
`changed`, and the report names the differing members rather than saying only
that the digest moved.

A `/2` manifest carries no selector document and is **refused rather than
checked by digest** — the same no-migration direction as the store itself.

### What I measured

- **100 focused tests, OK, 0.382s** (`correction-322286/FOCUSED.log`):
  `test_dossier` + `test_dossier_command` + `test_dossier_recovery`, with six
  new cases at the existing real public boundary — removed selector,
  another-authority selector, otherwise-changed selector, the supported
  relocation, relocation to a third path, and a manifest lacking the `/3`
  document — plus the valid complete restore still clean.
- **The exact candidate at the command boundary**
  (`correction-322286/PACKAGED-COMMAND.json`, driver `packaged_command.py`):
  all six scenarios through `packaging/stack.spec`'s own entry script, on a
  real instance built by `instance.emit`/`layout` and the supported store
  openers. Manifest `/3` records the selector document; the unchanged restore
  and the relocation exit 0 with `faults: []`; the four defects exit 2 with
  `restored-instance-selector` and their distinct states.

### NO FROZEN BUNDLE WAS BUILT, and that is a real gap in this evidence

PyInstaller is **not installed in this environment**. Installing it would reach
an external index and change the environment, so I did not. The driver runs the
spec's own frozen script as a subprocess with the spec's own import path, which
measures argv parsing, dispatch, stdout and exit codes on the candidate's bytes
and **does not measure freezing**. The older bundle was not used, because the
review is right that an older bundle cannot establish a changed command's
behaviour. The separate build-stamp limitation is unchanged and still disclosed.

### The registry update, and one I made and then took back

`stored_identity` is registered on the bootstrap public surface in
`tests/authority/test_boundary.py`.

**I also added it to the session/configuration disjointness set in
`test_session.py` and then removed it**, because that set is computed from
`Core` and `stored_identity` is an api-level static probe that never reaches
Core — the test said so immediately. `test_session.py` is byte-identical to the
host tree, and I am recording the wrong turn because the reviewer should not
have to infer it from an absent change.

### Known failures that are not mine, each measured this claim

- `test_boundary.ExportedSurface` still fails on **`open_readonly`**, which has
  been on the authority bootstrap face since committed HEAD and has never been
  in that registry. Measured both trees this claim: the host fails with **two**
  extras (`open_readonly`, `stored_identity`) and the candidate with **one**
  (`open_readonly`). Registering mine strictly closed my own addition. Whether
  `open_readonly` belongs on that face is not this Work's decision and I did
  not make it.
- `test_boundary.EveryDiagnosticIsBoundedByTheRule` — two diagnostic-bounding
  failures, **identical on the host tree**, previously reported.
- `test_catalog.TheMigrationChecklistIsRead` — two failures that are
  **isolated-checkout artifacts, not defects**: the case resolves frozen Node
  evidence at `REPOSITORY/v12/test`, and the candidate root holds `v12/python`'s
  contents directly, so the path lands at `/home/sl/v12/test`. **Both pass on
  the host tree**, which is how I know.

### Digests and scope

`correction-322286/DIGESTS.json` **e33655bba347** binds every candidate file,
the host tree's current bytes for comparison, and every evidence artifact.
Changed this claim: `tools/dossier_command.py` **3c7bd4da5c49**,
`tests/tools/test_dossier_recovery.py` **726ff6f31ed7**,
`tests/authority/test_boundary.py` **e1748fc9e364**. Unchanged and carried
forward: `stack_command.py` c86c0a4a536c, `test_dossier_command.py`
fbb88efcbe7f, `test_dossier.py` ab493c66d88c, `test_session.py` 4804ed2651d3,
`test_catalog.py` 7e70f111ed33, `dossier.py` 4508ff3577f0, `schema.py`
e96f702484a8, `core.py` e6569eca4398, `api.py` 9c8562b77d20. `RECOVERY.md` now
documents the required selector, its states and the single supported rewrite.

The accepted corrections are preserved intact: descriptor-anchored containment,
the real instance producer and validator, the real store openers, the required
retained roots, and both identity probes on scratch copies.

No live engine or provider, no production restore, no live instance access, no
host product edit, **no Git operation of any kind**, no deployment, no broad
suite. W61981, W321528 and other Work bytes untouched;
W321689/W321690/W39435/W321528 gates remain and the human checkpoint is
separately W322125. Schema 6 is unchanged and already approved; no new package
signoff is claimed.

Cumulative verification this claim: about 1.4 seconds of focused deterministic
execution — 0.382s focused, 0.960s registry, plus the six-scenario command run —
against about 1 second across the prior three claims.


## Claim 322441 (baton.claude, impl) — the null selector I crashed on

APPEND-ONLY. Read: `detail` at snapshot322440 (queued, unclaimed, routed
baton.impl, next baton.bug, no obligations, binding revision 1 here), then the
standalone claim; `work-events` after 322286 (322364 → 322441), `next_after`
null; then `review-2026-10-18T09-29-00Z.md`, `evidence/review-322366`, the
current PLAN, FINDING and `OWNER-EXECUTION-20261018.md`.

**The finding is correct and the defect is mine** — introduced by the
claim-322286 correction, two claims after the thing it was fixing.

### One variable carrying two facts

`held_selector` carried both "did JSON come back" and "what came back". A file
holding a valid JSON `null` parses fine and yields `None`, so the
`if held_selector is not None` guard skipped the contract validator, the state
stayed at its initial `present`, and the success branch indexed `None` —
`TypeError` out of the public command instead of a closed refusal.

The two facts are separate now: a `read` flag says whether JSON came back, and
**every** parsed value goes through `instance_contract.malformed`.

**I did not add a local `isinstance` check, and that is deliberate.** I wrote
one first, then measured what the real validator does with each value:

    None -> an instance selector is one document, not NoneType
    []   -> an instance selector is one document, not list
    'x'  -> an instance selector is one document, not str
    3    -> an instance selector is one document, not int
    True -> an instance selector is one document, not bool

It already answers, with bounded words, for every one. My check would have been
a **second definition of what a selector is** — which is exactly the mistake
that put a handcrafted selector in this fixture two reviews ago. So it came out.

### Measured

- **102 focused tests, OK, 0.408s** (`correction-322441/FOCUSED.log`), run with
  `PYTHONPATH=src` from the candidate root — the import path the reviewer
  correctly identified as required. Two new cases at the real public boundary:
  JSON `null` refusing as `malformed` with the validator's own word `NoneType`
  in `why` and **no traceback**, and the four representative non-objects each
  refusing the same way. The second case removes the original destination
  first, so its exit 2 is **the selector's answer** rather than the writer
  uncertainty a surviving destination correctly raises.
- **Eleven scenarios at the command boundary**
  (`correction-322441/PACKAGED-COMMAND.json`): the six from last claim plus the
  five malformed values, each exiting 2 with `malformed`, the validator's type
  name, and no traceback.

### THE FROZEN-BUNDLE GAP, with the governed route named

The review asked for a governed build route if one exists. **One exists:**
`v12/justfile:131-139`, recipe `build`. **It cannot be taken here**, and the
reason is its first step:

    pip install --no-cache-dir --disable-pip-version-check \
        --require-hashes --ignore-installed -r requirements.build.lock

That must reach an index. Measured this claim: PyInstaller is absent from the
system interpreter **and** from the repository `.venv`, and there is no local
wheel or cached artifact anywhere on this host — `--no-cache-dir` would forbid
using one regardless. This review authorizes no network install, so the route is
**named and not taken**.

What the evidence is instead, stated plainly: the spec's own entry script, run
as a subprocess with the spec's own import path. It measures argv parsing, verb
dispatch, stdout and exit codes on the candidate's bytes. **It does not measure
freezing.** This is carried to final acceptance as a residual operational gap,
not relabelled, and the 2026-09-21 bundle at `v12/python/build/out/distro` —
which contains none of this change — was not substituted for it.

### The recovery documentation now says what the code does

`RECOVERY.md` claimed the schema answer was "reported from the manifest". It is
not: `_check` reads it from the **restored store's own metadata** through
`Authority.stored_identity`, and compares the manifest's recorded version
against that rather than trusting it in its place — so a manifest disagreeing
with the bytes beside it is itself a fault. The paragraph also now records that
the probe reads a **scratch copy**, because `mode=ro` is SQLite's promise about
the database and not about its coordination files, and that
`unchanged_after_observation` re-reads every member afterwards to prove the set
was left alone rather than assert it.

### Digests and scope

`correction-322441/DIGESTS.json` **e8f3f8d96aea**. Changed this claim:
`tools/dossier_command.py` **32c3c4b7eef4**,
`tests/tools/test_dossier_recovery.py` **8e10098799e0**. Unchanged and carried
forward: `test_boundary.py` e1748fc9e364, `stack_command.py` c86c0a4a536c,
`test_dossier_command.py` fbb88efcbe7f, `test_dossier.py` ab493c66d88c,
`test_session.py` 4804ed2651d3, `test_catalog.py` 7e70f111ed33, `dossier.py`
4508ff3577f0, `schema.py` e96f702484a8, `core.py` e6569eca4398, `api.py`
9c8562b77d20. `RECOVERY.md` dccc61a2a79c.

Everything previously accepted is preserved: the required and bounded selector
binding with its named destination-only relocation, descriptor-anchored
containment, the real instance producer and validator, the real store openers,
the required retained roots, and both identity probes on scratch copies. The
four known registry and catalog failures are unchanged and still not mine —
`open_readonly` predates committed HEAD, the two diagnostic failures reproduce
identically on the host tree, and the two catalog failures are
isolated-checkout artifacts that pass on the host.

No live engine or provider, no production restore, no live instance access, no
host product edit, **no Git operation of any kind**, no deployment, no
integration, no broad suite. Schema 6 unchanged and already approved.
W321689/W321690/W39435/W321528 gates remain; W322125 remains the separate human
Git checkpoint.

Cumulative verification this claim: about 1.5 seconds of focused deterministic
execution — 0.408s focused, 1.007s registry, plus the eleven-scenario command
run — against about 2.4 seconds across the prior four claims.
