# Plan

1. [done] Add the fail-closed public launch-adoption seam.
2. [done] Bind adoption to exact expected session/contract/role and canonical
   authored bytes, including the authoring value and secret contract.
3. [done] Refuse every root entry except the fixed document and use no-follow
   descriptor-relative type/mode/read checks.
4. [done] Compose adoption into W39358's retry path and refuse an absent
   delivery for its retained started attempt.
5. [verified] All 33 launch tests pass, including the three reviewer witnesses.
6. [parent gate] The engine-level proof that retried cleanup removes the
   adopted root remains W39358's arc gate and does not keep this child open.
