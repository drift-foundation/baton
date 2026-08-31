# Progress

## 2026-08-30 — first implementer round (`baton.claude`, W51476 impl claim)

Done, green, and every wiring point refuted before it was kept. Operator-only:
nothing in `baton_v12` changed, and no second provider turn was taken.

### One hold, two call sites

`held_human_contract(document)` is the shared pure hold, in the shape
`held_task` already established in this file for exactly this reason: a
document checked twice by two different rules is not one hold. It runs at the
`preflight` -- beside the task, the policies, the record binding, the network,
the review route and the retention disposition -- and again inside
`input_manifest`, immediately before the contract is frozen. The composer used
to `dict(human_contract)` and rely on the whole-manifest validator; it now
applies the same function, so a contract read valid at the preflight and
changed afterwards is not the contract that gets frozen.

### Two grammars, both imported, and the narrower one is the real contract

That is the finding, and it is now measured rather than argued.
`artifactRef` is the frozen `$defs` shape and its `locator` pattern admits
`scheme:anything`; `contracts.manifest.check_uri` is what
`check_input_pair` actually applies and requires `scheme://` and an authority.
The hold applies BOTH -- the shape from `_validate_fragment`, then the locator
from the manifest's own owner. No third grammar is written here.

W39364's live invocation carried `baton:work/records/.../first-task.md`, the
ordinary opaque spelling. It satisfies the first owner and not the second,
which is why the two lifecycle times disagreed and the later one owned the
contract.

### Typed refusals only

Both owners are wrapped for `ContractRefusal` alone and the refusal carries
the owner's OWN sentence, as the record binding's locators already do. An
implementation defect inside a grammar owner propagates as itself: reporting
it as an `OperatorRefusal` would tell a human to edit a document that is fine
while hiding the boundary that actually failed.

### Cases, and what each was shown to prove

Removing the hold from BOTH call sites fails
`test_the_arc_refuses_before_a_single_side_effect` and
`test_the_composer_applies_the_same_hold`. Removing ONLY `check_uri` -- keeping
the loose shape check -- fails eleven cases including the named incident one.
Both runs were performed and restored.

`TheHumanContractIsHeldBeforeAnySideEffect`, 9 cases:

- the EXACT incident locator, named as its own case rather than a table row,
  so a regression that admits it again says so by name;
- eight further forms `artifactRef` admits and `check_uri` refuses;
- the frozen shape's own rules -- missing member, unexpected member, bad
  digest, negative size, text size, bad media type, identity with a slash,
  empty identity;
- a contract that is not a document, refused by type;
- an owner defect propagating as itself rather than as a bad grant;
- the composer applying the same hold;
- the arc-level acceptance below.

### The arc-level case is about ORDER, not about a message

Thirteen spies -- `stage_source`, `_copied_task`, `input_manifest`,
`assignment_workspace`, `compose_input_root`, `issue_offer`, `accept_offer`,
`submit_claim`, `record_attempt`, `activate_assignment`, `retain_manifest`,
`request_runtime_start` and `worker_entry.converse` -- and every one must have
a call count of zero. W39364's invocation reached its refusal with a staged
delivery, a submitted claim, an activated assignment and a materialized
credential slot already in place; this is what says none of that happens now.

### One thing the refutation run corrected in my own case

The first cut of `test_the_narrower_manifest_grammar_is_the_one_applied` also
listed a query and a fragment locator. Removing `check_uri` left those two
PASSING while the other ten failed: `artifactRef`'s own pattern is `[^?#]*`,
so the shape owner already refuses them. Listing them under the narrower owner
would have credited it with refusals the schema was making. They now have
their own case naming which owner gets there first, so a future edit to either
is visible. I would not have known without running the revert.

### Verification

    tests.tools.test_dogfood_operator                    146 tests
    + arc_engine + retry_engine + parallel_runner
    + intake + workspaces + text_sweep + dogfood_image   369 tests, OK
                                                         (107s, real Docker)

Whitespace clean.

## 2026-08-30 — second implementer round (`baton.claude`, W51476 impl claim)

Review [P1] accepted and closed, and the correction to my own record matters
as much as the code.

### The defect was one layer further out than the layer I fixed

`main` calls `capabilities(given)` BEFORE `compose`, and the real builder
`_launched` opens the authority, opens the control store and calls
`CredentialHome.materialize`. So the shared hold was correct at both places it
reached and the documented command reached it too late: W39364's exact
malformed contract still materialized the attempt's credential slot before
anything refused it. The retry branch three lines above already says "BOUND
BEFORE A CAPABILITY IS BUILT, because building one is already an outward act";
the ordinary branch did not do it.

`_held_grants(given)` now runs first. It is pure -- it reads the operator's own
task file and calls `frozen_task` and `preflight`, the same owners
`run_dogfood_task` uses, with the same operands. No store, no home, no engine.
A check written out again here would be a second thing to keep in agreement,
so there is none. Both existing holds stay: the inner preflight for a direct
caller of `run_dogfood_task`, and the composer's, which answers a different
question -- a document changed after it was read.

### My report claimed a spy that was not there

The last round's PROGRESS said the arc case proved "a materialized credential
slot" among its zero-count spies. It did not. That case calls
`run_dogfood_task` directly with an already-built `credential_delivery`, so
the builder is not in it at all, and `assignment_workspace` is a workspace
allocation rather than credential materialization. The reviewer caught the
claim and they were right; it is corrected here rather than quietly dropped.

The arc case remains useful and is kept, for exactly what it does prove: the
later source, authority, runtime and provider operations.

### Three command-level cases, two of which the boundary is required for

Removing `_held_grants(given)` fails
`test_the_command_refuses_before_it_builds_a_capability` and
`test_the_command_boundary_holds_every_grant_it_can_judge`. Run and restored.

- The first drives `main` with the incident locator, spies the capability
  builder AND `CredentialHome.materialize`, and requires both untouched. The
  BUILDER is the spy, so the case is about the order of the documented command
  rather than about a message.
- The second is the gate-not-a-wall control: sound grants still reach the
  builder. Without it the first would pass just as well if `main` had stopped
  building capabilities altogether.
- The third holds every grant the boundary can judge -- network, review route,
  retention disposition, record binding, human contract -- because a boundary
  that caught this Work's operand and nothing else would be one somebody has
  to remember to extend.

`TheDocumentedCommandIsOneGrantsFile`'s fixture now carries grants that pass
the boundary rather than placeholders. Patching `_held_grants` out of those
cases would have been hiding the act they are meant to run through.

### The documentation precision the review asked for

The canonical grammar is not uniformly `scheme://authority`: `file:` has its
own form, `file:///` and an absolute path with NO host, because a file locator
naming a host would be a claim about somebody else's filesystem. Both the
implementation comment and the test class docstring said the uniform thing
while the positive case already used both forms. Corrected.

### Verification, including the rerun the review required

    tests.tools.test_dogfood_operator                    155 tests, OK
    + arc_engine + retry_engine + parallel_runner
    + intake + workspaces + text_sweep + dogfood_image   378 tests, OK
                                                         (107s, real Docker)

Whitespace clean.
