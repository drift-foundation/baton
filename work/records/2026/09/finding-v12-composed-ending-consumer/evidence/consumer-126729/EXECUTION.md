# W122060 consumer preflight — claim126729

Owner M126545 and handoff M126724 authorize only stage_execution.py and its
test plus attributable progress/evidence. OBSERVATION.md revision1 requires
the observation-only factory to read committed Authority/coordinator accounts
without an external act. Its inputs are only configuration, JobStore and
ControlStore; it receives no opened Authority or IntegrationStore.

Before the first verification process: question whether existing public store
openers can supply that read-only boundary. One disposable public-API probe,
at most2s, charged against this consumer piece's cumulative20s allocation.
No live store, raw SQL, private store access, provider-suite rerun, source
change or recovery proof is involved. Record each process and actual paths.
If the API cannot supply this boundary, return the exact capability finding
before any out-of-scope provider edit; preserve the prior lifecycle fixture.

Probe1 used an instant without required milliseconds and was correctly refused
by the coordinator clock validator. Correct that probe operand and repeat the
same question once under the same2s per-process/cumulative20s limits.

Probe2 confirmed coordinator open creates a missing database. Authority open
succeeded with only its main file read-only; its directory remained writable
for journal sidecars. Refine the same public-open check to a read-only directory
as well (restored by this probe's own finally block), then stop. This distinguishes
readable canonical data from permission to create write-side artifacts.
