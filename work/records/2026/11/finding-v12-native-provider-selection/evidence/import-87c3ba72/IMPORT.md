# Accepted I2 import

Exact 22-path candidate 87c3ba728e7fe75e649816a3bc44ae0bb6ff7bc6b3b915a84e70bbb495aa1627 imported on 2d9a1f5a. Archive/path/hash/base/type/writability checked for all targets before writes; final bytes/modes verified. Accepted M386180, review-2026-11-25T06-17-11Z.md. Initial preflight M386182 refused two mode0444 files before any writes; owner repaired permissions, full preflight then passed. No Git mutation, engine/build/provider/credential operation.

Verification reused: 1240 run, 1237 pass, three independently confirmed baseline failures; exit1, not green. No test rerun for exact-byte import. L1-L6 remain as reviewed, including missing recovery CLI, interrupted-copy hold, whole-file leak-guard limits and separately owned baseline inventory failures. Q1 real-engine qualification and later native gates remain open.

Human checkpoint pending: Realize Codex homes and audited subscription credential lifecycle
