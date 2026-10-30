# The gate failed, and here is exactly where. Read this before you touch anything.

Recorded by `baton.claude`, claim345388, from the retained evidence of run
`durable-capture-w341357-345039` and from the committed base. Every line and
file reference below was **read in the tree**, not carried from a handoff.

## What the last run established

It ran once, **ended on its own at 461.10s** against a 900-second lease
(`provider.status 0`, `failure_reason null`, no interruption), returned the
first candidate this slice has produced, and **measured the five-module gate
for the first time in this campaign**:

```
Ran 864 tests in 12.817s
FAILED (failures=9, errors=7)
```

**The 30-second verification ceiling fits with room.** That question had been
open and explicitly unproved in every packet for this Work. Two qualifiers,
stated rather than buried: unittest's self-reported interval is not the
adapter's whole wall clock, and **the gate exited 1**, so nothing about the
candidate is accepted.

**All 16 failing cases are in `tests.manager.test_maintenance`.** The other four
gate modules — `test_intake`, `test_attempts`, `test_contracts_inventory` and
the new `test_attempt_failure_cause` with its 63 cases — reported no failure.
Every traceback frame is in `tests/manager/test_maintenance.py` (21 frames) or
`src/baton_v12/worker_manager/workspaces.py` (15 frames), and **no path this
candidate changed appears in any traceback**.

That is *not* a general exoneration of the candidate and
`review-2026-10-21T10-42-55Z.md` says so: absence from a traceback does not
prove absence of a defect, and **no base measurement of this argv exists in any
run**, so "pre-existing" is a hypothesis.

## The conflict, with the four places it lives

**1. The fixture stores whatever spelling `tempfile` hands it.**
`tests/manager/test_maintenance.py:135-137`:

```python
root = tempfile.TemporaryDirectory(prefix="v12-maintenance-")
self.addCleanup(root.cleanup)
self.root = root.name
```

`self.storage`, `self.home`, `self.workspace` and `self.result` are all built
from `self.root`.

**2. Under the verifier, that spelling is a `/proc/self/fd` alias — on purpose.**
`v12/worker/claude_agent.py:3262-3301`, `_pinned_environment`, opens each
verifier root *before the provider runs* and exports it as
`/proc/self/fd/<n>`, because "checking a pathname immediately before launch
still leaves a check/use interval" and a provider descendant could replace the
checked name with a link. `TMPDIR` is one of `EPHEMERA_ROOTS` (line 3129).
`_revalidated_directories` (3303-3327) then re-validates the held objects and
**refuses if the environment no longer names its held directory**.

**This boundary is correct and it is not yours to widen, disable or work
around.**

**3. Production requires a canonical place, and is right to.**
`worker_manager/workspaces.py:6221-6228`, `_composed_line_roots`:

```python
if (os.path.islink(place) or not os.path.isdir(place)
        or os.path.realpath(place) != place
        or not place.startswith(reserved + os.sep)):
    _denied("the writable line is its own directory in the reserved manager namespace")
```

A `/proc`-aliased place can never satisfy `realpath(place) == place`. That
accounts for the five line-layout `ERROR`s. The object-identity check that
follows (`(held.st_dev, held.st_ino) != (device, inode)`) is the replacement
refusal and **must still be exercised**.

**4. The fixture hides the child's failure instead of reporting it.**
`tests/manager/test_maintenance.py:249-252`, `MaintenanceCase.executed`:

```python
done = subprocess.run([sys.executable, "-c", program, *operands],
                      capture_output=True, timeout=120)
return done.stdout.decode("utf-8", "replace")
```

`returncode` and `stderr` are **discarded**. A child that cannot resolve a path
belonging to its parent's descriptor table produces empty stdout, and the
caller's indexing turns that into the `IndexError`s at lines **331** and
**821**. The reviewer's inference — a `/proc/self/fd` path of the parent cannot
resolve in that child — matches this code. **It has not been confirmed
dynamically. Confirming it is step 1.**

Both source files are byte-identical to the committed base `bc925cf5`, and
neither is among the candidate's changed paths.

## My reasoning about the correction, which you must confirm rather than trust

I think canonicalising the **fixture's own derived root** is not a weakening,
and here is the argument so you can check it instead of taking it:

- the verifier's check/use protection is about the roots it **opened before the
  provider ran**. Its authority is the held descriptors, and
  `_revalidated_directories` re-checks exactly those;
- a directory a test creates *inside* those roots **during** verification is the
  fixture's own object. Resolving it to its canonical spelling gives the
  provider no name to swap, because the provider is already gone and the
  descriptors remain the verifier's authority;
- the production refusal at `workspaces.py:6221-6228` is untouched by this and
  **must still fire** for a non-canonical place, a link, and a replaced object.

**If that argument is wrong, say so and stop — do not weaken either check to
make a test pass.** The mechanism and the files are yours to choose;
canonicalising fixture-owned derived paths is a *suggestion*, not a prescription,
and `review-2026-10-21T10-42-55Z.md` is explicit on that.

## The sixteen cases. All of them must still exist and still mean what they mean.

Seven `ERROR`s:

| case | class |
| --- | --- |
| `test_a_LINE_composed_preparation_is_REVALIDATED_and_not_refused` | `THEREVALIDATIONComparesTheLayoutItsRecordIsAbout` |
| `test_a_LINE_home_NAMED_workspace_is_still_the_line_layout` | `THEREVALIDATIONComparesTheLayoutItsRecordIsAbout` |
| `test_a_REPLACED_LINE_object_is_refused_by_the_COMPOSED_boundary` | `THEREVALIDATIONComparesTheLayoutItsRecordIsAbout` |
| `test_a_REPLACED_inputs_root_under_the_LINE_layout_still_refuses` | `THEREVALIDATIONComparesTheLayoutItsRecordIsAbout` |
| `test_the_RECORD_STATES_which_layout_each_path_completed_over` | `THEREVALIDATIONComparesTheLayoutItsRecordIsAbout` |
| `test_a_second_preparation_finds_it_established_rather_than_replacing_it` | `ThePreparationEffectHappensInsideTheExecution` |
| `test_the_real_programs_document_is_the_one_this_module_accounts_for` | `TheVocabularyAndTheSchemaAreOneContract` |

Nine `FAIL`s:

| case | class |
| --- | --- |
| `test_INACCESSIBLE_output_names_the_exact_entry_and_preserves_it` | `TheSELECTEDOutputIsAccessibleOrItIsAnError` |
| `test_a_TRAVERSAL_FAILURE_is_an_answer_and_not_silence` | `TheSELECTEDOutputIsAccessibleOrItIsAnError` |
| `test_an_UNREACHABLE_ROOT_is_the_first_thing_that_is_inaccessible` | `TheSELECTEDOutputIsAccessibleOrItIsAnError` |
| `test_an_ATTEMPT_layout_record_is_compared_whole` | `THEREVALIDATIONComparesTheLayoutItsRecordIsAbout` |
| `test_exactly_one_mount_is_composed_and_it_is_the_workspace` | `TheMountIsTheDerivedRootAndNeverTheHome` |
| `test_the_home_and_its_credential_siblings_are_not_mounted` | `TheMountIsTheDerivedRootAndNeverTheHome` |
| `test_the_EXPECTED_root_is_composed_from_configuration_and_the_attempt` | `TheORDINARYEndingCompletesWithNoHelperOrItHolds` |
| `test_the_HOLDER_adopts_with_its_own_capability` | `TheADOPTIONTakesTheCapabilityAndNotANumber` |
| `test_the_LEGAL_second_run_is_arbitrated_through_the_REAL_caller` | `TheEXECUTIONAllowanceIsTheAttemptsOwnCurrentRun` |

Two of them — `test_a_REPLACED_LINE_object_is_refused_by_the_COMPOSED_boundary`
and `test_a_REPLACED_inputs_root_under_the_LINE_layout_still_refuses` — are the
**replacement refusals**. A "fix" that makes those pass by never reaching the
refusal has broken them, not repaired them. They must fail the composition for
the right reason and say so.

## Where the raw evidence is

`../evidence/run-345039/GATE-CLASSIFICATION.json` carries the derivation, with
`WHAT_IS_ESTABLISHED` and `WHAT_IS_NOT_ESTABLISHED` kept apart, and the raw
stream's **locator and sha256**. The raw verification stream was deliberately
**not** copied into the dossier: it is the gate's own output from a tree the
provider edited with the attempt's credential mount readable, and the
proposal's own `verification.txt` refuses to reproduce it for that reason.
Read the original in place through the supported reader:

```
baton-v12-stack logs --logs <launch-home>/logs --attempt <attempt-id> locators
```

The reviewer independently hashed that stream at
`d3c37969f1a83ede1c9871481064670522f7c35cc222ca901cbcb9264b3743a1` and
extracted the same 16 headers and the same summary.
