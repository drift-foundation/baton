# W52821 reviewer baseline — 2026-09-01

No credential content, provider process, engine, authority mutation or runtime
was used for this baseline.

## Documented command

From `v12/python`:

```text
PYTHONPATH=src python3 tools/dogfood_operator.py --help
```

The command exits zero and advertises:

```text
usage: dogfood_operator ... [--credential-file CREDENTIAL_FILE] ...

--credential-file CREDENTIAL_FILE
    path to the provider credential this attempt delivers
```

There is no user-local source-registry operand and no provider-profile
selection at the command boundary.

## Exact source observations

- `dogfood_operator.py:main` parses `--credential-file` but carries no source
  configuration into the grants or composed assignment.
- The `__main__` block scans raw argv into one `_credential` pathname.
- Its `_provider(provider, reference)` explicitly discards both selection
  operands and opens that one pathname. Distinct trusted provider/reference
  selections therefore resolve to the same invocation-global source.
- `_launched` injects that callback into `CredentialHome.materialize` lazily,
  after activation and before runtime start. Its `materialized` list is local
  to one `_launched` invocation.
- `credentials.resolved_delivery` already resolves authorized slots to
  provider/reference pairs. `CredentialHome` already creates
  `credentials/<attempt_id>/<slot>`, refuses an existing exact-attempt root,
  and tears down only the given delivery.
- W52800's current source and signed-off record establish exact `0640` slot
  mode, configured group, private `0700` root and worker-side readability
  refusal. No W52821 patch is needed in that boundary.

## Baseline conclusion

The reproducible defect is source selection, not slot allocation: the command
can name one arbitrary host path but cannot resolve the assignment's exact
provider/reference through user-owned configuration. The shared
`/run/baton/credentials/claude` convention is therefore still the only live
operator path even though all downstream delivery is already attempt-private.
