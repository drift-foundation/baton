# Plan

1. Revalidate W9901, W16821 and the current proposal/receipt implementation.
2. Pin separate versioned policy snapshot, attestation and aggregate-decision
   records, including exact provenance and replay operands.
3. Implement direct M3 one-of/all-of/threshold evaluation through the authority
   authorization seam, without implementing hierarchy resolution.
4. Version persistence, projections and any worker-control receipt exchange;
   keep frozen 1.0 meanings intact or record an explicit supersession.
5. Make duplicate, denial, stale-policy, stale-target and concurrent-threshold
   outcomes deterministic and journalled.
6. Add positive, negative, replay and race tests, then return for independent
   review before M3 proposal-pipeline closure.

