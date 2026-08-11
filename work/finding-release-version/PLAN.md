# Plan — public release version

1. Identify the existing CLI/TUI version declarations and distribution fields,
   then select one shared release-version source — completed.
2. Set the project release to `1.0.0` and add offline `--version` handling to
   both entry points with the exact ruled output — completed.
3. Update generated help, manifests, README examples, and focused source and
   packaged regressions without touching protocol behavior — completed.
4. Rebuild both zipapps and submit a referenced focused handoff — completed.
5. Reviewer performs independent source/package/no-I/O checks and gives
   Slawomir the fresh TUI for the final human trial if behavior is affected —
   completed; no additional human interaction trial was needed for the offline
   version action, and Slawomir tested the combined TUI artifact.
6. Only after approval, rerun the full release suite, deterministic rebuild,
   packaged workflow smoke, and live doctor — completed; 2318 tests and all
   release checks passed.
