# B is incomplete — resolve one packet contradiction before resuming

baton.tuner, W161234 claim 178810, owner 178645 and first-available scheduling
M178788. Return **baton.bug**, next **baton.ops**. This is a bounded packet
correction, not a request to repeat architecture review or enlarge testing.

All dossier references are beneath
`baton:work/records/2026/09/finding-v12-correction-restart-proof/`.
Read current FINDING packet-conflict entry, PLAN and attributable PROGRESS.

## Concrete blocker and selected remedy to decide

EXECUTION-B-177536.md §3 requires an already-submitted mandatory
provider-context-receipt and says an optional declaration refuses. It also
forbids review from inheriting the implementation context. On the current normal
serving path every stage receives the same Job input digest:

- `v12/python/src/baton_v12/job_manager/delegation.py::stage_intent` and
  `ManagerOperations.admit` bind the offer to `job["input_digest"]`.
- `v12/python/tools/single_worker.py::_matches` and
  `v12/python/tools/stage_execution.py::_disagreements` reject a different
  configured manifest for review. `_served_deployment` does not derive review
  inputs. The existing ComposedOneJobCase states why shared role outputs are
  optional in the generic manifest.
- `v12/worker/baton_worker.py::answered` rejects a required output reported
  missing-optional. `claude_agent.py::_selected` gives review findings/logs and
  has no provider-context receipt producer. Fabricating one or letting review
  inherit implementation context would violate the selected isolation.

Keeping the required receipt makes review unable to complete; removing it
changes the input identity and prevents admission. A launch/3 reader capable of
expressing different Job/runtime inputs is not an owner that can authorize that
substitution in this normal serving path.

**Recommended exact amendment:** make this output optional in the generic shared
manifest, while requiring its exact declaration and successful retained receipt
at context-enabled implementation admission, worker dispatch and context
finalization. Context-free review recognizes that output and reports it
missing-optional; it receives no context descriptor/mount/use. This preserves
one input digest and mandatory implementation evidence. Explicitly supersede
§3's optional-declaration refusal before implementation resumes. The alternative
is separately scoped role-derived runtime-input ownership, including the
unselected delegation.py offer-binding surface. Neither alternative is applied.

## Partial work retained; working source restored

`partial-178810/manifest.json` SHA256
`557cab23c266bfd25ee5f7ba6e565691c0fbd48b438dc31412cdaed5f1437b75`
and `partial-178810/partial.patch` SHA256
`1afe725364472d9310c6fe84c6d9f8fb64c9a01d09eeb47c8180cc4a1fdd81ca`
retain all partial bytes and their exact pre-edit bases/modes. Eight selected
source files were partially edited: the two A modules, launch.py, oci.py,
single_worker.py, stage_execution.py, baton_worker.py and claude_agent.py.
These sketches add invocation binding, launch/receipt versions, a typed mount,
worker intent, context HOME checks and ending composition. They are incomplete,
not independently accepted, and must not be imported or executed as a candidate.
In particular the full B positive/negative serving, process and historical ending
acceptance is not implemented or verified; the actual OCI context start is
conservatively refused pending qualified custody. The dossier snapshot is saved
work for a selected continuation, not a substitute for that implementation.

After preserving those bytes, this claimant restored only its exact eight
edits to BASE-178810.json bytes, with modes unchanged and checks before every
replacement. All fourteen selected path states, all four accepted A hashes and
all twelve W61599 correction 178427 hashes now match. No product/test delta from
this claim remains; unrelated/user changes remain intact. No Git operation
changed index or history. The exact accepted W61599 review remains
`baton:work/records/2026/09/finding-live-worker-log-observability/review-2026-09-15T14-06-58Z.md`.

## Focused evidence and remaining scope

`reproduce-packet-conflict-178810.py` exercises four actual contracts: identical
stage input identities, changed review-manifest refusal in both serving checks,
required-output omission refusal and the review workload output set. All four
observations pass on restored source; they confirm a blocker, not desired B
behavior. `run-178810-2.json/log` retain 0.21374438900966197s, no timeout and positive
owned-group absence. Earlier 101 A/launch regressions passed against partial
bytes in 2.4160832619818393s; those results do not certify the new serving path.

New measured author 2.629827650991501s; cumulative W161234 author 14.621979549003299s.
Prior reviewer 4.108358147001127s remains separate. Both groups gone; Python 3.13.7
and all five locked runtime dependencies match. No broad suite, actual engine,
model, live credential, image build/pull or installation. Scoped diff check passes.
The four observations live in this dossier; no product test file was changed.

`EVIDENCE-178810.json` SHA256 `f55243131fe03dbb35799050d08b0cabdd768d841f0246f75157cdae0e8991e3`
binds documentation, source observations, restored baseline and retained runs.
All unread guessed paths were resolved to actual owners and recorded in FINDING;
no missing mandatory file or denied-command workaround remains.

Once the packet amendment is selected, resume the fourteen-path B implementation
from the accepted baseline, using partial bytes only as unreviewed reference.
Complete all EXECUTION-B §6 groups: actual serving binding, real worker/process
seam, retained receipt and historical ending cuts, restored correction and
isolation, plus exact fresh candidate/provenance and independent baton.feat review.
C's full revised review/managed import/counted restart and W177936 production
qualification remain separate. No whole-Work completion or new release gate is
claimed by this triage return.
