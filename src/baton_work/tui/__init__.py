"""The v11 console — Gate B. A RENDERER of the canonical projection.

This package draws what `baton_work.projection` returns and calls
`baton_work.transitions` for actions. It holds no queries, no readiness
logic, no counters of its own: if a number on screen is wrong, the defect is
in the shared projection and gets fixed there for both surfaces — or it is a
missing semantic value, which is REPORTED AND RULED, never patched around
here (Gate B authorization, 2026-08-14).
"""

from baton_work.tui.app import run                             # noqa: F401
