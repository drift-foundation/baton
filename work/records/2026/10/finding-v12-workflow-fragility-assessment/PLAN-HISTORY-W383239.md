# Current milestone — five bounded proposals, then joined owner decision

Owner E370866 selects planning only. ASSESSMENT.md remains the historical rationale; new child FINDING/PLAN documents specify concrete deliverables. Claim E371041 establishes allocation and actual edges; ALLOCATION-371041.json records readback. New descriptor/wire/spec semantics require owner approval before DESIGN amendment or dependent product implementation.

| Work | Finite planning delivery | Assigned endpoint |
| --- | --- | --- |
| W371072 | Residual role descriptor and admission enforcement, exact compatibility/requiredness and proposed DESIGN delta | baton.codx |
| W371073 | Narrow safe adapter-failure wire/producer/reader proposal reusing accepted W333486 diagnostics | baton.codx |
| W371074 | Supported stopped-failed settlement command, axes/preconditions/replay and proposed spec delta | baton.codx |
| W371075 | Fresh installer prerequisites and create-while-serving ownership/guard plan | baton.impl |
| W371076 | Composed deterministic actual-role workflow proof plan consuming the four approved proposal outcomes | baton.codx, blocked |

W371076 waits on W371072/73/74/75 and W370688. W370555 is already closed satisfying and is consumed as accepted evidence, not a new blocker. W370747 waits on W371076 and retains containment of all five. Read back actual graph before release. No speculative dependencies between the first four: they own disjoint proposal documents; dependent semantic choices must be marked proposed until approved. Future actual shared-file changes require serial ownership and explicit implementation allocation.

Each child returns baton.bug for independent planning review, then owner decision on concrete contracts. A successful planning child closes only after its bounded deliverable is accepted; no runtime/product success inferred. Once joined plan is accepted, this umbrella reconciles the five approved proposals, bounded implementation order, actual future dependencies, file ownership and integrated acceptance consumer, and returns owner. Do not mark umbrella done on partial planning.

Existing W370555/W370688 are reused unchanged; W370560 owns retained-instance disposition and cleanup boundary; W370268/W321608 own adoption. No new gate on active corrections or broad v13 refactor. Routine startup planning queues normally behind any active impl claim; no interruption. Product source/tests and DESIGN remain read-only, with no engine/provider, live retry, install, deployment, cleanup mutation or Git change.

Reviewer owns umbrella and child FINDING/PLAN/reviews. Assigned child handlers own PROPOSAL/PROGRESS/new evidence only. Historical assessment/source pins remain unchanged; proposal artifacts get exact new hashes for review. Human Git checkpoint belongs after accepted concrete delivery, never agent Git mutation.
