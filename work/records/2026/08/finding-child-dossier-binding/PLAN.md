# Plan

**Status:** W309 round-one corrections independently reviewed and signed off
2026-08-17; ready to close satisfying. The umbrella-binding stopgap is no
longer needed after deployment of this correction.

1. Revalidate the repository's canonical child-depth policy against the
   current binding parser and projection contract.
2. Extend only the canonical relative-shape validator to accept ruled child
   records; preserve all containment and traversal refusals.
3. Add focused source/packaged positive and adversarial tests, including exact
   replay and revision preservation.
4. Run the complete v11 gate and return for independent review.
