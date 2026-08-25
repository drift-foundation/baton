# Plan: run safe v12 tests across available cores

1. [done 2026-08-25] Inventory v12 Python test modules by resource ownership
   and pin the initial parallel-safe and mandatory-serial sets. The 28 pure
   modules, one Docker module and packaging/installed-layout stages are named
   in FINDING.md. Record the 423.54-second, 100%-CPU pure serial baseline in
   `evidence/serial-pure-baseline-2026-08-25.txt`.
2. [next] Implement the standard-library repository runner under
   `v12/python/tools/`:
   - collect exact unittest ids in disposable child interpreters;
   - fail closed unless every discovered module belongs to exactly one explicit
     parallel/serial registry;
   - partition pure tests by concrete TestCase class, with individual-method
     shards for boundary inventory's two aggregate owner/probe classes;
   - default jobs from `os.process_cpu_count()`, capped by ready shards, and
     accept only a lower whole-number override;
   - run each shard in a fresh process, retain deterministic sorted reporting,
     and return nonzero if any shard fails;
   - on signal/fault terminate and reap every child process group and clean the
     runner's disposable result root.
3. [next] Add `parallel-test` and `parallel-gate` recipes without replacing
   canonical `gate`. `just parallel-gate 8` is the documented override. Order:
   version, parallel source shards, source serial Docker registry, then the
   existing locked `build`/installed-layout stage. Emit a final phase summary
   that distinguishes parallel source, serial source and serial installed
   results.
4. [next] Add runner regressions using disposable fake suites: deterministic
   collection/output under inverted completion; registry completeness and
   duplicate/missing-id refusal; default/override bounds; failure propagation;
   no phase overlap; interrupt/internal-fault descendant reaping; result-root
   cleanup; and exact jobs=1/default id/outcome parity. Register the new test
   module atomically so completeness never has a transitional exception.
5. [next] Verify without weakening the current gate:
   - run jobs=1 and default on the same tree three times each and compare median
     wall time plus `/usr/bin/time -v` user/system/CPU/RSS evidence;
   - require identical collected test ids, failures/skips and deterministic
     final output apart from explicitly normalized durations;
   - run injected failure and interrupt trials, then prove no child processes
     or runner temporary roots remain;
   - run the source Docker module alone and after the parallel phase, prove no
     suite-prefixed containers/images remain, and never overlap two Docker
     runs;
   - run the complete locked installed-layout stage and confirm package origins
     remain in site-packages.
6. [next] Return the dedicated recipes and evidence for independent review.
   Do not replace canonical `gate` until reviewer sign-off; replacement is a
   separate recorded decision after parity and cleanup are proved.
