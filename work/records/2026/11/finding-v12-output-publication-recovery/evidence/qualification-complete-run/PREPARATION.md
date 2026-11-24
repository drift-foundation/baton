# Fresh recovery-8 with corrected qualification checks

Reuses the packaging-owner-20261124T073402Z runtime and existing exact images. No source/image build. Creates an independent /3 original, then executes the already selected publication/custody/review gate. Recovery-7 and its retired review are untouched.

Changes from qualification-status-review-run: correct runtime identity and exact writable-path checks from qualification-runtime-posture; fail immediately on terminal review failures from qualification-interrupted-review; final recovery phase runs through its tested interrupt-forwarding wrapper via exec, keeping cleanup alive on Ctrl+C. Setup/producer phases retain the previous wrappers. No deadline or retry policy is changed.

Preparation checks: source/runtime/input pins and absent destination pass; all Python scripts parse; shell syntax passes; the corrected posture's four negative probes and interrupt/terminal-state four checks are retained in their source packets. No installation or engine execution in preparation.

Owner command: python3 /tmp/baton-w385695-complete-recovery.py recovery. Deadline qualification remains a separate subsequent gate.
