# Plan

1. Revalidate W9901 and the W16793 matrix against the current authority tree.
2. Pin the smallest versioned principal, Work-scope and authorization-decision
   shapes; keep endpoint identity separate and keep hierarchy resolution out.
3. Version authority persistence and configuration/projection APIs around those
   shapes, including explicit treatment of schema-1 disposable stores.
4. Move route/capability decisions through the authority seam and persist their
   provenance on attributable acts.
5. Migrate claim capacity from participant-keyed to principal-keyed while
   preserving atomic one-live-claim enforcement and assignment fencing.
6. Add positive, negative, replay, race and reopen tests, including two endpoint
   addresses for one principal and one endpoint that cannot select another
   scope.
7. Return for independent review before the Worker Manager context correction
   consumes the new projection.

