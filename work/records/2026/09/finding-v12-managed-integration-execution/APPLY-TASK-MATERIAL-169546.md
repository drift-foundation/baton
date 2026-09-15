# Apply task material ownership — W161230 reviewer research169546

## Confirmed facts

The stage row has no apply task_digest reader. The current deployment producer
has no completed apply-specific stable-material assembler either; making the
resolver argument mandatory does not create that owner answer. The author's
observation of a missing assembled operand is valid.

However, needing the collected digest to build the final managed apply envelope
does NOT imply needing that digest to name stable task material. Selected
SLICE2-SCOPE-165724.md, composition step4, explicitly says task_digest names
stable request/task material, not the self-containing envelope. The existing
managed_execution.managed_task takes task_digest and parent.collected_digest as
separate operands. integration_capacity._owned_plan requires both planned
members but carries no collected_digest; admit_integration_phase resolves the
preparation's successful ended content and writes the parent-content binding at
admission, not at initial root planning. Existing collected-content/authorization
checks remain mandatory. No future receipt or content digest may be fabricated.

## Ownership answer and implementation direction

The owner of the initial digest is the integration composition's immutable
task/input producer, measuring the stable task material that the configured
apply workload is actually asked to execute. It is not the stage scheduler or
the future result collector. Construct this answer where the accepted
orchestration plan and ordinary input are assembled, then pass its measured
digest to capacity and recover it from the committed plan on subsequent sweeps.

Proposed implementation direction, to be revalidated by the implementer against
actual configured workload bytes and the selected source scope:

1. Identify and hold the actual integration/apply task material using the
   configured integration worker's existing task/input owner. single_worker
   configuration already retains validated task_bytes; establish whether those
   bytes are exactly the stable apply instruction material intended here. Do
   not assume a bootstrap/producer task is equivalent merely because it exists.
2. If those are the intended material, hash those actual held immutable bytes
   and preserve their association with the exact parent and preparation in the
   committed orchestration/input. If richer stable instruction material is
   needed, compose and persist that explicit material from actual known
   Job/source/target/preparation/workload facts before hashing it. A phase label,
   arbitrary constant, unrelated test digest or invented future collected digest
   is not an adequate replacement for the material the apply must later obey.
3. Keep runtime assignment, collected content, current grant/fence/CAS and final
   result bindings in their existing later owners. The planned task digest is
   not permission to issue/apply before preparation and independent acceptance.
   Slice2 still stops with apply planned and the root held.
4. Verify stable replay of the material/digest and refusal when the material
   changes. The future slice3 task producer/consumer must reconstruct the same
   stable-material identity while separately binding actual collected output;
   no self-containing envelope hash or weakening of managed_task semantics.

This is clarification of the selected stable-material versus late-envelope
boundary and a concrete next composition investigation, not a claim that a
ready-made apply producer exists or approval for derived apply execution. No
new generic schema/API, relaxed closed document, provisional/sentinel member,
mutable plan or slice3 implementation is selected. If the actual workload
requires one of those to provide truthful material, return that exact boundary
and a bounded selection proposal; do not invent an owner answer. Continue all
remaining selected construction/lifecycle work that does not depend on that
unresolved extension. The lack of a collected digest alone is not such proof.
