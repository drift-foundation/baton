# Lines a tier-aware qualification launcher needs

For codexpc's next packet revision. Not applied by me. They assume the
service-tier candidate `9c365d72…` is imported, and refer to
`evidence/qualification-preparation-r2/`.

1. `selection.template.json`: add `"service_tier": null`. Null or absent
   means none requested. No default; the owner selects `fast` explicitly.
2. `render_commands.py`, in `render`: refuse any value other than `None`
   and `"fast"`:
   `if s.get("service_tier") not in (None, "fast"): raise ValueError("unrealized service tier")`
3. `prepare_context.py:83`:
   `argv = agent.provider_argv(prompt, model=s['explicit_model'], service_tier=s.get('service_tier'))`
   and add to `live-context.json`:
   `service_tier={"requested": s.get("service_tier"), "observed": None}`.
4. `capture.py:111`, replace the fixed length check:
   `if argv[6] != '--model' or (len(argv), argv[8:-1]) not in ((9, []), (11, ['-c', 'service_tier="fast"'])): raise SystemExit('wrong argv shape')`
5. Acceptance text: the requested tier is taken from the selection. An
   observed tier is recorded only from provider-produced evidence of the
   same run, with its source. A requested `fast` with no such evidence is
   reported as "requested, not observed". A rejected key or an error
   naming `service_tier` is evidence that the build does not support it
   and is retained as that.
6. The one-invocation rule stands. A tiered run and an untiered run are
   two invocations and need two selections.
