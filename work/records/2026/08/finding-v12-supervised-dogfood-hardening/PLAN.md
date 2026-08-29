# Plan

1. [parked] Wait for W38956's first useful positive result unless evidence
   exposes a false-success blocker.
2. Reconcile this inventory with W32382 and W36540; link or close duplicate
   portions rather than implementing them twice.
3. Split each independently reviewable hardening outcome into bounded Work
   before implementation.
4. Run the later-pass negative, restart, retry, cleanup and operational matrix
   against the accepted vertical slice.
