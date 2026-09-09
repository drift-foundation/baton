# Implementation progress

No implementation claim has begun. The actual change author appends the first
attributable entry here under its successful Work claim; reviewer findings and
coordination remain in FINDING/PLAN and append-only reviews.

## 2026-09-09 — baton.claude, claim 126590

**Claimed first**, at seq126590, before reading the dossier and before any
edit.

### Revalidation

Every symbol OBSERVATION.md and FINDING.md name is where they say, and the
contract fits the existing shapes without a schema change:

- `delegation.ManagerOperations.observe` composes seven members;
  `OBSERVATION_MEMBERS` and `unobserved()` are the two places that name them,
  and `_bound` adopts the document against that closed set and binds
  `claimed_by` to the stage's own offer.
- `projection._observed_state` reads durable refusal, failed start/preparation,
  `_ending_owed`, frozen output, then claim/runtime — and `_conversing` maps
  the exchange. `EXCHANGE_OWED = {"starting": "dispatch", "answering":
  "conclude"}` is what `owed_exchange` selects on.
- `tools/job_manager.py:_Observing` composes `ManagerOperations` with
  `observe_exchange=_exchange_read(observed)` and nothing else;
  `_exchange_read` takes the member by name deliberately.
- `attempt_runtime_of` already answers the fixed assignment, so the binding
  needs no second storage read.

No clarification of the pinned interface is needed; I am implementing it as
written.

### Question and budget, declared before any execution

Does a supplied integration observation bind to this stage's own claimed offer
and fixed assignment, map to the states OBSERVATION.md pins, and make an
ordinary sweep select `conclude` rather than `dispatch` — while an absent
callback changes nothing?

Budget: **cumulative 20s across every test and probe process**. I will use
focused selectors on the four owned test modules, retain each run and its
elapsed time, and stop at the limit and hand back the exact remaining question.

### Delivered — the pinned interface, as written

`OBSERVATION.md` revision 1 needed no clarification and none was taken.

**`delegation.py`.** `observe_integration` is a second optional capability,
typed separately from the exchange read — a deployment may compose either,
both or neither, and one capability answering both questions would let a
surface holding only the integration read reach the exchange. The canonical
observation gains `integration` as an **optional** member normalized to `None`,
which is the compatibility rule itself: an observation composed before it
existed keeps its exact previous behaviour.

`_bound` is where a supplied document is owned, because it is the one place
that has already proved **whose** claim this attempt is under — and that proof
is exactly what the document must be held against. Stage, episode and attempt
are compared with the requested operands and the offer with the **proved
claim** rather than the operand a second time; the assignment is compared with
the runtime's own fixed one, not with today's live Work, because a completed
integration is historical. The closed shape, the closed state set, a
non-boolean episode and generation, and the completion account's nine members
with its `quiescent|destroyed` exclusion report are all refused with the
existing vocabulary. Nothing here is an act: it validates a shape and its
bindings, and no member authorizes anything.

**`projection.py`.** `_integrating` maps the observation to the existing stage
words, **after** every earlier failure record keeps its precedence — a durable
refusal, a failed start or preparation, and an uncertain runtime all still
answer first. `pending` splits on the runtime axis rather than on the document,
so a running integration owes only the ordinary refresh and a quiet one owes
`conclude`; `answered` is `answering` whatever the runtime is doing, because
concluding delegates to the driver and changes no Job state by itself.
`unstarted` beside a started runtime, and `pending`/`answered` with no attached
runtime, fail closed.

**`tools/job_manager.py`.** `_Observing` takes the integration read by name and
**optionally** — a factory composed without one is still complete, where a
factory that cannot read the exchange is the default `--observe` replaces. The
surface gains no refresh and no serving act.

### Verified

All four owned suites: **135 tests, OK**. Method counts 18→36, 21→31, 36→41,
24→27. **4.3s against the declared 20s**, focused selectors only; every run and
its elapsed time is in the evidence.

Two existing assertions changed, both bounded to the optional member: the two
expected-member lists in `test_delegation.py` gain `integration: None`. No
other assertion in any owned file changed.

### One seam reported, not taken

`OBSERVATION_OPTIONAL`, `INTEGRATION_OBSERVATION_SCHEMA` and the member/state
tuples live in `delegation.py` and are **not** re-exported from
`job_manager/__init__.py`, which is not among this Work's seven paths. The
owned test imports them from their owner and says so. W122060 can do the same,
or a bounded follow-up can re-export them — reported rather than edited on the
way past.

### Next

Independent acceptance at `baton.bug`. This provider makes no claim that the
real integration terminal handoff or the final lifecycle is proved; W122060
owns the consumer and that proof.

## 2026-09-09 — baton.claude, claim 126679 (correction)

**Claimed first**, at seq126679. All three findings accepted; each is a real
misprojection of the same document.

**Budget: at most 15.7s remaining**, charged from the 20s with the 4.3s already
spent. Not reset by this claim. Each run below is recorded separately with its
own command and elapsed time. The correction's baseline is the candidate bytes
at handoff, retained in `evidence/review-126648-candidate.json`.

Question: does a supplied document project only for the stage kind it is
about, and does a validated completed account survive a later uncertain
refresh and a frozen output that is not its own?

### Delta

All three findings corrected in the seven paths; details, controls and every
run in `evidence/provider-126679.json`.

**[1]** The stage kind is now the **first** binding: the ids and the assignment
bind a document to an attempt, and every kind of stage has one, so without it
the same completed account projected an implementation stage completed with no
worker output. Another kind — or a missing one — refuses
`refused/operation-collision` before the state is read. The binding fixture's
STAGE names its kind, as the review requires.

**[2] and [3]** The integration branch moved above the generic worker rules and
below the named earlier failure guards. The uncertainty hold is now where
`OBSERVATION.md` puts it: inside `_integrating`, on the three states that would
otherwise earn an automatic act. `completed` and `held` are answered from the
document alone — a completed account is historical evidence about the fixed
assignment, and a mutable axis read afterwards is not a fact about it.

142 OK across the four owned suites. **1.1s spent of the 15.7s remaining**, not
reset by this claim; each run recorded separately. The reviewer's probe now
raises at its first case instead of reporting it, which is the correction
reaching the defect it was written to demonstrate.
