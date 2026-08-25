# Plan: run safe v12 tests across available cores

1. [pending] Inventory v12 Python test modules by resource ownership and pin
   the initial parallel-safe and mandatory-serial sets.
2. [pending] Implement the bounded parallel runner, deterministic result
   aggregation, operator worker override and explicit serial registry.
3. [pending] Add the documented `just` entry point and regression tests for
   collection, failure propagation, cleanup and registry completeness.
4. [pending] Run repeated success/failure trials and the complete existing
   source, installed-layout and container gates; record serial-versus-parallel
   timing and CPU evidence.
5. [pending] Return for independent review before replacing the canonical v12
   verification command.

