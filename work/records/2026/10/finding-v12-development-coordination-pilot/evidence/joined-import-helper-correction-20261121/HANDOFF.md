# Helper-only H1/H2 correction

Owner explicitly assigned the interactive coordinator this bounded correction; M385487 supersedes the K assignment. Original packet is unchanged. Corrected helper SHA256 `bad0b3cfbf003d336e75ab29723c6ab6cba6f020e8846da2264aa2d43743437d`. No import was run.

H1: concrete M385484 manifest/tree pins are bound; absent/malformed pins refuse before I/O. Wrong manifest or tree refuses before host access. H2: exact mode and arity validation; help alone is inert; only literal import with two operands dispatches mutation.

Five focused checks passed, including missing/malformed pins, wrong valid-format pins, invalid modes/arity, inert help and explicit-only import dispatch (import spy only). Actual host read-only preflight: 20 paths, zero faults; report in preflight/PREFLIGHT.json. Product tests were not repeated; accepted source bytes unchanged. Original helper and evidence preserved. See helper.patch, check.py and check.log.

Pending independent helper delta review. The replacement command uses this helper with the ORIGINAL joined-composition-20261121 packet; do not use the original unbound helper. Import remains unexecuted; no Git mutations, builds or live changes. Source acceptance remains tree959f9524c94138325c724db84262dd009fa0eacedc3370e7142cc49904ed752b.
