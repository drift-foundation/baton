# The review's nominated-engine finding, measured rather than read

`baton.claude`, implementer, 2026-08-31. This confirms
`review-2026-08-31T17-15-35Z.md` against the retained run4 candidate before
spending anything on a fresh attempt, as the revalidation rule requires.

Nothing here touched the retained custody tree or the canonical checkout. A
WRITABLE COPY of run4's candidate was made at `/tmp/w51487/run5/run4-recheck`,
each mutation was applied to that copy's `preflight.py` and reverted, and the
copy is scratch.

## What was mutated

Seven single-substitution mutations of production `_observed_readable`, the
six from `evidence/w51487-run4/mutation-check.md` plus the one the review says
is missing:

    [engine, "run", "--rm", "--user", ...   ->   ["docker", "run", "--rm", "--user", ...

## Result

Baseline: the candidate's own harness, 30 tests, exit 0, nothing failing.

| mutation | harness exit | caught by |
| --- | ---: | --- |
| **the nominated engine becomes the literal `"docker"`** | **0** | **nothing** |
| `--network none` dropped | 1 | `test_the_probe_asks_the_nominated_engine_about_the_exact_path` |
| `readonly=true` dropped | 1 | same case |
| identity forced to `0:0` | 1 | same case |
| stdout comparison replaced by a constant | 1 | `test_a_probe_that_ran_reports_what_it_found` |
| a failed probe reported as unreadable | 1 | `test_a_probe_that_did_not_run_is_not_an_unreadable_verdict` |
| absent-path short circuit removed | 1 | `test_an_absent_path_is_not_probed_at_all` |

**The review is right, and this is the measurement rather than the reading.**
Six of the seven regressions are each caught by the case that owns the
corresponding fact. The seventh — the one the frozen task's second required
fact exists to protect — passes untouched, because the helper supplies the same
literal value the assertion expects.

Reproduce with `mutation_check.py`, retained beside this file:

    python3 mutation_check.py \
        /tmp/w51487/run4/storage/attempt-w51487-run4/custody/\
attempt-w51487-run4/proposal/candidate \
        /tmp/scratch-copy
