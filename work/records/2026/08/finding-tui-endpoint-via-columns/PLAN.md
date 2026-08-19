# Plan

1. [done 2026-08-19] Revalidate the Work-row route structure after W25 and
   its table-shell changes land. W25 and W39 both landed; neither moved the
   Work table itself, and W39 makes the rendered route the same resolved
   object authorization uses.
2. [done] Rename the rendered Route column to Endpoint and add compact Via
   from the canonical selected route.
3. [done] Preserve whole-column responsive omission, with Handler surviving
   longer than Endpoint or Via, and Via dropping before Endpoint.
4. [done] Add route-selection and width regressions, run the complete v11
   gate, and return for independent review.

**Status — 2026-08-19:** awaiting review. One presentation cost is raised for
a ruling in `PROGRESS.md`: the extra column narrows the truncatable Title at
110 columns.

