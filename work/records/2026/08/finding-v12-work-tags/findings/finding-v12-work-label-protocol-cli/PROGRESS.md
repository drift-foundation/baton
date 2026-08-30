# Progress

## 2026-08-29 — implementation round (`baton.claude`)

State: **awaiting review, with a recommendation to park the remainder.**

### What this round actually decided

The Host boundary in `FINDING.md` required revalidating the v12 protocol and
CLI host before implementing, and that revalidation is the round's substance:
**v12 has no CLI and no protocol host.** The product is a Python distribution;
every `argparse`/`sys.argv` under `v12/` belongs to a test harness, a build
tool or the ping-pong spike. The canonical CLI this repository operates through
is the v11 binary, a different product that is not this Work's to extend.

The finding anticipated exactly this and said what to do: document the absence
and park the unavailable exposure rather than introducing a parallel CLI or
protocol product. That is what I did, and it is why almost no code was written.

### And the cut is largely already delivered

W29400 landed the approved contract at the only creation, mutation, projection
and search surfaces v12 has. I drove each confirmed-boundary bullet directly
rather than reading it off the source — zero/one/repeated create labels,
normalized deterministic sorting, `labels` on the projection, `[]` for an
unlabelled Work, `all_of` intersection, `none_of` exclusion, mixed composition,
the empty filter, and the explicit contradiction refusal. The mapping table is
in `FINDING.md`.

So the honest state is: the substance of W29401 exists and is tested; what
remains is CLI shape for a CLI that does not exist.

### The one thing worth adding, and why

`tests/authority/test_work_label_exposure.py` (7 cases). It holds the
acceptance matrix end-to-end at the surface that exists, and it holds one fact
I found while revalidating that nothing else asserts and that constrains
whoever eventually builds the CLI:

**the two label vocabularies overlap in spelling.** `canonical_label` admits
dots, so `baton.v12.work_id` — an OCI runtime label key the worker manager
writes on every container — is a perfectly valid Work label. That is safe,
because no behaviour is inferred from a Work label, and the test now asserts
that safety rather than assuming it. But it means the acceptance bullet asking
CLI parsing to prove non-dispatch is about COMMAND ROUTING: a future
implementer who tried to disambiguate Work labels from runtime labels by
inspecting the label text would build precisely the confusion the bullet exists
to prevent.

### Verification

    PYTHONPATH=src python3 -m unittest tests.authority.test_work_label_exposure
    -> 7 tests, OK

    ...with test_work_labels (52), test_boundary, test_dependencies and
    test_parallel_runner
    -> 140 tests, OK (1 skipped)

### Recommendation

Park W29401 on the absent host rather than closing it. The parked scope is
listed in `FINDING.md` and is only the hostless exposure — CLI operands,
commands, predicates, help, versioned output and the parsing regressions. It
becomes actionable as one piece the moment a v12 CLI or protocol host exists,
which is why I did not split it into a new record.

I have not parked it myself: the phase change is a scheduling act and this
round should be reviewed first.
