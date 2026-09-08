# Stable-access plan revalidation

2026-09-07, baton.tuner, W105706 claim 106738. Dossier-only research and planning.

## Observed current seams

- workspaces.py: WORKSPACE_DIR remains 02770; prove_workspace_group requires
  exact mode and configured gid. adopt_workspace_group only changes the root.
  Ordinary allocation and its precreated result directory use that contract.
- line_assignment_workspace proves the reserved path and persisted device/inode,
  substitutes the line for output and mints AllocatedRoots with a required grant.
  _granted_roots currently reconstructs the object; a new line-specific marker
  and its pin would have to survive this reconstruction explicitly.
- oci._roots preserves AllocatedRoots object identity, whereas mappings are
  canonicalized. OciAdapter.start currently passes only the workspace pathname
  and gid to prove_workspace_group. This is the added source seam beyond the
  historical six-path proposal.
- review_cycles.create_line materializes outside its final transaction and
  publishes idle inside act without access provisioning. The new initial pass
  belongs after the final state/pin recheck, not in the unprotected interval.
  Filesystem failure is not rolled back by the ledger transaction.
- grant_writer validates a checkpoint before its final transaction. That
  transaction currently checks admissible state; the prior review requires
  rechecking the generation and checkpoint that justified earlier validation.
  The revised pass is proof-only, with no routine recursive mutation.
- writer_boundary substitutes and grants line roots; review_boundary grants
  ordinary output roots and nominates the line as read-only source. Therefore
  _grant_required or the presence of a grant cannot classify development output.
- GitCheckpointProfile.materialize/freeze/validate delegates Git to an injected
  runner. Freeze creates retained refs; later writers must work with these
  manager-created entries under the stable policy.
- Dockerfile.claude specifies USER 65532:65532 and the exec-form Python
  dogfood_entry.py entrypoint. That entrypoint composes baton_worker.main with
  ClaudeAgent and does not establish an explicit umask. This inspection is not
  an observation of the creation mask in a running image.
- input_roots.configured_group offers a login-group fallback. The proposed real
  engine proof must require an explicit dedicated group and cannot use that
  fallback as deployment evidence.

## Proposed scope and ownership

PLAN.md owns the exact eight-path proposal and current verification sequence.
Source hashes are retained separately; they do not approve candidate bytes.
Shared review_cycles.py, oci.py and tests are serialized: access first, then
custody W105982 after revalidation. Existing unrelated source/test/registry
changes observed by git status are outside this planning assignment.

Initial 0664/02775/0775 provisioning, later proof-only admission and read-only
review mounts replace the old private-group/routine-repair plan. The ordinary
02770 allocation remains independently checked. Actual cooperative creation
requires explicit fixture and deployment setup; no hidden worker/recipe edit is
inside this proposal.

## Operational findings and validation

Two guessed optional test locators were absent:
v12/python/tests/manager/test_claude_agent_engine.py and
v12/python/tests/manager/test_claude_image.py. Repository file enumeration found
the actual test_dogfood_image.py, test_worker_image.py and test_claude_agent.py.
The missing guesses are research errors, not inaccessible required Work
records or evidence of a Baton defect. No claim depends on their contents.
All bound dossier and required policy files were readable.

Two attempted JavaScript orchestration cells failed to parse before any tool
execution. Corrected calls used a literal heredoc argument; successful writes
followed. They produced no partial source mutation.

Validation is document/path/hash/whitespace review only. No production or
existing-test bytes changed; no runtime capability or suite result is claimed.
The newly planned engine test path intentionally does not exist yet.
PROGRESS.md is unchanged. Initial runtime proof, complete custody composition,
revised independent review and owner execution choices remain outstanding.

Completed checks: eight proposed implementation paths resolve as seven existing
paths plus the deliberately new test module; ten inspected source/test/recipe
SHA-256 values are unchanged; PROGRESS matches its pre-revision contents; the
five revised/preserved dossier/evidence files pass trailing-whitespace checks;
git diff --check passes. The validator's printed file count said six; the checked
list contains five. This counting correction does not alter any checked result.
