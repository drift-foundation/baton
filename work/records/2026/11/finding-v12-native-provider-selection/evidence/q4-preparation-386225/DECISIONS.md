# Owner decisions, all together

Four choices, then two execution selections. Nothing else is open for the first Codex → Claude Job.

| # | Decision | Recommendation | What the alternative costs |
| --- | --- | --- | --- |
| D1 | Claude selector and the identity it must report | Request `claude-fable-5[1m]`, require reported identity `claude-fable-5`. It is the only pair with retained evidence on CLI 2.1.247. | Any other pair is untested on this build. A wrong pair holds the review after one Claude call; nothing is accepted. |
| D2 | Claude credential reference | Name the registry reference you want the reviewer to use (name only). The October pilot used `operator-file:w202663-development`. | None; it must be named by you. I do not read the registry. |
| D3 | Reviewer container posture and Job limits | Same posture as accepted for Codex: bridge egress, uid:gid 1000:1000, read-only root, dropped capabilities. Limits: 600 s provider-turn ceiling (one value per Job, sized for the review), 15 s verification, 20 min whole-Job wall bound enforced by the operator stopping the instance, one invocation per role, no retry, no correction round. | Network `none` is not possible for a provider call. Tighter egress is a product feature that does not exist yet. |
| D4 | Prove the uncertainty path live | No. Rely on the deterministic proof, configure routing, and read the owner queue after the run. If the real review happens to be uncertain, that is the live proof. | Yes costs one extra Claude call on a deliberately undecidable review, as a second Job in the same instance. |

Execution selections, in order (see `PATH.md`):

| Selection | What runs | Credentials / provider |
| --- | --- | --- |
| A | One Claude image build from `b5abf798`, an offline inventory of it, one instance install (builds the runtime bundle from source), two worker compositions, one empty start and stop. | None. Network only for the image build's package downloads. |
| B | One Job: one Codex implementation turn, one Claude review turn. | Real Codex login (already selected) and the Claude credential from D2. |

After B: a separately authorized private-evidence review, as for Q2.
