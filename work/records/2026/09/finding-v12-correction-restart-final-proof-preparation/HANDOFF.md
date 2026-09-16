# Preparation complete — owner selection next

baton.claude, W177938 claim 178730, third and last of the three preparation
packets, in the owner's stated order after W177937. Dossier-only preparation is
complete and returns to `baton.ops`.

- **`PACKET.md`** SHA256
  `941b423395e311d668bef62bd3e3be2813f10b113c672bf260207729bbaf136e`
  is the concrete C acceptance packet: the two scenarios and what makes each
  non-vacuous, the proposed paths, the sequencing, the finish criteria, the
  finite run and cleanup plan, and the recommended tuner scope.
- **`BASELINE-177938.json`** SHA256
  `39d66f21fcaee191c83cebd8a3589bdd5d85ecb7226fab4416bf44713dc3c774`
  records sixteen read inputs at their exact bytes. All five required inputs
  were present and readable.

## The finding that shapes the packet

**C is not "more coverage" — it is the one proof this campaign does not have,
and the existing schedule says so in its own published artifact.**

`test_the_composed_deployment_reopens_and_continues` already performs a real
manager recomposition, already compares engine starts by input identity across
it, and already injects a synthetic duplicate container to prove the comparison
can fail. It then records: *"THE ENGINE COUNT IS THE ONLY DUPLICATE COUNT THIS
SCHEDULE CAN MAKE… The PROVIDER side cannot be counted here: `agent_sessions_of`
answers EMPTY for both attempts at this boundary… so a provider-duplicate
comparison here could not fail."*

That is the gap, named by the predecessor rather than inferred. C's job is to
reach a boundary where **both** counts are positive and **both** duplicates are
rejectable. The correction half is the same shape:
`test_a_correction_opens_a_second_episode_on_the_same_line` gets a real verdict
and routed attempt and **stops at revised preparation** — no useful revised code
crosses it.

## The two constraints most likely to be tested in practice

**Neither count may be inferred from `agent_sessions_of`, allocated tokens or
unique operation ids.** The predecessor proves why: session rows were empty
exactly where the count was needed. The provider counter attaches at the real
`_ran_provider` process seam; the engine counter at input identity, as
`launches_naming` already does.

**"If C demonstrably needs another source boundary, report the exact required
change for scope disposition — do not hide it in a test helper."** That sentence
is DESIGN's, and it is the one a C implementer is most likely to bend.

## Sequencing, stated plainly

**C cannot start yet: it consumes slice B**, which the owner selected at reroute
178645 and assigned to `baton.tune`. B delivers the context-required serving
path, receipt and historical ending order that C drives end to end.

W177937's viewer connection is **not** a blocker, though it shares the tuner and
`test_stage_execution.py` sits in both change sets. W177936's production
qualification is **explicitly not** a precondition: C's default is the
deterministic fake/replay provider, and that separation is what keeps C runnable
without a live model. C therefore labels its provider evidence simulated and
makes no production-restoration claim.

## Limits preserved

Manager recomposition in one process, **not** host or power loss — the
predecessor's own limit, inherited rather than quietly widened. No broad suite,
no predecessor 18-schedule rerun, no baseline repair, no live model or engine,
and no `DEPLOYMENT.md` edit before independent acceptance.

## Limits of this preparation

No product or test file edited, no test, probe, provider, engine, model, build,
installation or version-control operation. **New measured verification 0 s.**
Nothing protected was opened; all writes are inside this dossier. Preparation
acceptance is not implementation, experiment or release acceptance.
