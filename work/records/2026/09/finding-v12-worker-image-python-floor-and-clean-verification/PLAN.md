# Plan

1. Change `v12/worker/Dockerfile.claude` so the built dogfood artefact carries
   Python 3.13 or newer while preserving Node 22, the exact Claude version,
   fixed non-root identity, entrypoint, credential absence, read-only-root
   compatibility and explicit network posture. Treat every build as a
   candidate until its immutable digest is selected after review.
2. In `v12/worker/claude_agent.py`, compose explicit cache/temp roots outside
   `candidate` for both the provider child and the inner verification child.
   Preserve the provider's prepared credential `HOME`, keep the environment
   closed, and give verification a separate non-credential home. Open and
   retain the verifier's four directory objects before the provider runs, pass
   only those descriptor-bound `/proc/self/fd/<n>` roots to verification, and
   validate the held objects immediately before launch; pathname-only
   revalidation does not close the surviving-descendant race. Do not rely on
   Dockerfile environment inheritance or `PYTHONDONTWRITEBYTECODE`.
3. In `v12/python/tools/dogfood_operator.py::_derived`, run independent
   verification with its Python/cache/temp writes outside the retained
   custody candidate. Prove a successful compile leaves the candidate's
   complete entry and byte inventory unchanged. Keep verification output out
   of proposal and durable evidence, while surfacing a bounded useful failure
   diagnostic to the supervising operator and retaining the typed nonzero
   verification refusal.
4. Add or adjust only the bounded tests in
   `v12/python/tests/manager/test_claude_agent.py`,
   `v12/python/tests/manager/test_dogfood_image.py`, and
   `v12/python/tests/tools/test_dogfood_operator.py`. This is the explicit
   scheduled authority to update the existing exact child-environment
   expectation and image probe in those files; do not weaken credential,
   stream, non-root, no-manager, network-none, entrypoint, or immutable-byte
   assertions.
5. Prove offline that provider and inner-verifier cache roots are outside the
   candidate; a real `compileall` success leaves a retained candidate
   path/byte-identical and cache-free; and invalid syntax returns the typed
   failure while its bounded diagnostic remains operator-visible and absent
   from every durable member. Add an after-validation interleaving that
   replaces a verifier root while the child is launched and prove the child
   follows the held directory object rather than the replacement. Retain the
   87-case Claude-agent and 331-case dogfood-operator baselines.
6. Build `Dockerfile.claude` in the serial real-image gate. Against that exact
   artefact, prove `sys.version_info >= (3, 13)`, the pinned Claude version,
   unchanged v12 baseline compilation, candidate cleanliness, fixed uid/gid,
   reviewed entrypoint bytes, no manager package, no credential or provider
   environment, and `--network none` for every probe that needs no egress.
   A missing daemon, registry, or build network fails the required gate rather
   than skipping it.
7. Package the exact recipe, runner, adapter, scheduled tests and record files
   as a digest-bound proposal and obtain independent review. Record the built
   candidate image digest and gate evidence, but do not call it selected in an
   implementation handoff.
8. After approval, explicitly select the validated immutable image digest in
   this owning record through the established selection process. Only that
   recorded selection permits a fresh ordinary W71917 attempt; never promote
   or repair run6's faulted, cache-contaminated proposal.

## Status

All eight items are complete. Review
`review-2026-09-04T21-41-01Z.md` approved the exact proposal and image, and the
owning finding records the immutable image selection that permits the fresh
W71917 attempt.
