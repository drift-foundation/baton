# Plan

**Status — proposed for product decision.** The live W5 → W6 → W101 stall
demonstrates the scheduling gap; no implementation is authorized yet.

1. [ready] Confirm the effective-urgency rules and the parked/containment
   boundaries with Slawomir.
2. [pending] Revalidate every canonical ordering surface and readiness
   consumer against the confirmed model.
3. [pending] Implement one canonical, overlap-safe derivation without changing
   explicit priority.
4. [pending] Add workflow tests for chains, diamonds, fan-out, closure, and a
   saturated reviewer route, plus JSON/TUI/readiness parity.
5. [pending] Run focused and complete v11 gates and return for independent
   review.
