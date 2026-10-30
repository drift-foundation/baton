# claim 378950 — the one red case outside this outcome, attributed

`tests.tools.test_environment` keeps ONE failure after this claim:

    FAIL: TheBootstrapRecipeReachesTheHelper
          .test_a_named_distribution_that_is_absent_is_refused_BY_NAME
    AssertionError: 'no built runtime at' not found in ''

It is not this claim's, and it is not this Work's. Three independent
attributions, none of which is "it was already like that":

## 1. It reproduces at this claim's INPUT bytes

An isolated snapshot outside the checkout, at `/var/tmp/w376956-attribution/
baton/v12/...` (the `v12` level kept, because the suites resolve repository
assets through `parents[4]`), with this claim's edits reversed from
`tools/bootstrap.py` until the file digests
`8a710afc4a6ad809a72602ad4e5e7cbb76cf3ba224e2fe92d6bfb2d83a38b8f4` — the exact
bytes review 2026-10-29T00-25-45Z pinned and accepted as a checkpoint. The same
case fails there.

## 2. The failure never reaches this Work's code

Driving the recipe directly shows the cause, which is an ImportError during
module initialization — long before `install`, the copy ledger or the cleanup:

    just --justfile v12/justfile bootstrap <inputs> <destination> <no-such-distro>
    rc 1, stdout ''
    Traceback (most recent call last):
      ... tools/bootstrap.py", line 3480, in main
          admitted = admit(taken.destination, taken.distro)
      ... bootstrap.py", line 1810, in checkout
          from tools import stage_execution
      ... stage_execution.py", line 53, in <module>
          from baton_v12.integration import (...)
      ... job_manager/role_contract.py", line 514, in <module>
          for _consumer, _namespace in zip(CONSUMERS, _namespaces()):
      ... job_manager/role_contract.py", line 510, in _namespaces
          from ..integration.driver import CLAIM_NAMESPACE
    ImportError: cannot import name 'admit_candidate' from partially
                 initialized module 'baton_v12.integration.admission'
                 (most likely due to a circular import)

The recipe's stdout is empty because the helper never ran. The case asserts the
helper's refusal, so an empty stdout is the whole failure.

## 3. The modules in that cycle are foreign in-flight edits

    git status --porcelain
      M  v12/python/src/baton_v12/job_manager/templates.py
      ?? v12/python/src/baton_v12/job_manager/role_contract.py

`role_contract.py` is UNTRACKED — it is not in HEAD at all — and HEAD's
`templates.py` does not import it (`git show HEAD:...templates.py | grep -c
role_contract` answers `0`). The module-level assertion at `role_contract.py:
514` imports `integration.driver` while `baton_v12.integration` is still
initializing, which is the cycle. Both files belong to another participant's
live work; neither is this Work's, and nothing here was edited to
accommodate or to repair them.

Read-only inspection only (`git status`, `git show`). No version-control
mutation, and no foreign-path repair.
