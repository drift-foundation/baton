# Plan

1. [complete 2026-09-06] Revalidate the accepted runtime and
   candidate-admission leaves and freeze their shared composition under K's
   ownership. Both prove more than this plan assumed; FINDING records what
   that changed about items 2 and 3.
2. [complete 2026-09-06, by composition rather than construction] The
   live-grant-to-exclusive-access seam is `runtime.compose_assignment` and
   the instruction/result exchange is the durable delivery, both accepted
   under W101490. `execution.integrate_next` calls them in the one order
   their proofs require and adds the decision they deferred: which
   coordinator verb a model's claim earns.
3. [complete 2026-09-06] Prove one clean model-driven import and one
   pre-mutation refusal without a VCS adapter or Git-history mutation. The
   model is an injected port whose contract is the durable files; no case
   starts a runtime, reaches a daemon or runs a version control system, and
   an AST gate holds the module to that.
4. [complete 2026-09-06] Add focused stale-fence, competing-writer,
   quiescence and target-byte tests: 27 cases across five classes, one per
   acceptance clause.
5. [complete 2026-09-06 after the third review] Run focused component gates
   and independent implementation review. The first two reviews requested
   corrections in `review-2026-09-06T14-35-14Z.md` and
   `review-2026-09-06T15-03-04Z.md`; the final review signed off in
   `review-2026-09-06T15-20-27Z.md`.
6. [complete 2026-09-06] Revalidate the queued entry from its accepted
   producers under the live grant before `port.run`; bind the invoked model
   runtime to the same current attempt whose post-run state is required to be
   quiescent; and replace the no-op happy/refusal fixtures with target-byte,
   preflight and stale-evidence cases that can fail when no import occurred or
   a refusal changed the target.

   `admit_candidate` is now `resolved_account` plus `enqueue`, so execution
   re-runs ADMISSION'S OWN resolution under the grant and compares it member
   for member with the entry -- selectors taken from the stored account, never
   from a caller. The attempt must be non-quiescent when the port is asked and
   quiescent before settlement, so an observation made before the model ran
   cannot authorize what it wrote afterwards. The test port performs a bounded
   transformation against a disposable target and every case snapshots its
   bytes and modes.
7. [complete 2026-09-06] Add the missing live-grant cutpoint
   immediately before `port.run`, and bind port invocation to a manager state
   that proves no current, cancelling or uncertain writer may already exist.
   The delivery must exist before that runtime starts. Map ordinary stale
   execution-time producer/target refusal to terminal entry refusal and queue
   progress, reserving target hold for integrity or ambiguous custody. Complete
   the happy-path evidence by deriving the model's verification from final
   bytes/modes and asserting the imported path's expected ordinary mode.

   Drive the two deterministic review reproductions: a grant ended during
   `_current()` must prevent `port.run`, and an `uncertain` current-attempt
   runtime must prevent it. Preserve the independent post-run grant and
   quiescence checks.

Not implemented here, by scope: staging or committing anything (Slawomir
keeps Git index and history ownership), policy decisions, candidate repair,
and every form of automatic recovery. An unanswered attempt is reported as
`running` with its grant intact; W101493 owns what happens next.

   All four are corrected. The grant is re-read immediately before the port
   receives writable work as well as after the model answers -- two cutpoints
   for two races. `not-started` is the ONE state a port is asked in, which also
   makes `materialize_delivery`'s before-the-runtime contract realizable.
   Execution-time preflight failures take the verb this record already ruled,
   split on the coordinator's own refusal category: ordinary refuses the entry
   and releases so the queue moves on, integrity blocks and retains. The fake
   model derives its verification from the bytes and mode it reads back, and
   every imported path's mode is asserted against one an importer established.
   Both reviewer reproductions now refuse with the model never asked and the
   target unchanged.
