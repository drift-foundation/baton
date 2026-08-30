# Plan: injected worker agents still require the scripted default

1. [done 2026-08-29] Revalidate the reported import order, public seam, existing
   worker tests, and W39357 stopgap against the current tree.
2. [done 2026-08-29] Record the exact correction boundary and add focused
   missing-default, default-construction, and falsey-injection regressions.
3. [done 2026-08-29] Move scripted-default loading into the `None` branch
   without changing reference-worker behavior. `_scripted_default()` holds the
   import; `main` selects on `agent is None` rather than truthiness.
4. [transferred to W39357; not a W39770 closure gate] Remove
   the provider-image stopgap. NOTE for whoever does it: W39357's guard case
   `test_the_scripted_default_is_present_only_as_the_seam_stopgap` asserts
   that `baton_worker.py` still contains the literal
   `from scripted_agent import ScriptedAgent`. That string is STILL present —
   inside `_scripted_default` — so the guard did not fire when the seam was
   corrected and no longer discriminates. It should assert the absence of the
   import from `main` itself, or simply be removed with the COPY.
5. [done 2026-08-29] Focused worker, provider-image and dependency gates run:
   test_worker_image 106 OK, and 385 OK across test_dogfood_image,
   test_claude_agent, test_worker_container, test_lifecycle_composition,
   test_worker_entry, test_worker_entry_engine, test_frozen,
   test_dependencies, test_text_sweep and test_parallel_runner — the one
   failure is W39357's own open regression, not this seam's.
6. [done 2026-08-29] Independent review signed off the implementation in
   `review-2026-08-29T22-29-33Z.md`.
