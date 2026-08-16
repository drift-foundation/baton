"""Baton v11 Work graph — Gate A vertical slice.

A RESTART, not an extension: nothing here imports `baton_core`, by ruling
(2026-08-11, reuse is cherry-pick-after-revalidation) and by test
(`tests/work/test_boundaries.py`). The public surface grows step by step with
the plan in `work/records/2026/08/finding-recursive-target-graph/IMPLEMENTATION-PLAN.md`;
what is not exported there does not exist yet.
"""

from baton_work.authority import (             # noqa: F401
	Authority,
	WorkError,
	PROTOCOL_VERSION,
	SCHEMA_VERSION,
	cell_width,
	validate_handle,
)
