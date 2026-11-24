# Owner-selected combined deadline qualification — passed

Owner explicitly approved replacing the continuous installed-stack deadline test with deterministic host-clock tests plus a short real-container worker test. This supersedes the earlier pending choice, not production limits.

- Host: 30 focused deadline/control, measurement/completion, settlement and owner-item tests passed in 11.326 seconds. These exercise real product owners with controlled clocks and deterministic engine doubles. No claim of a continuous installed-stack expiry run.
- Worker: exact publication image sha256:43482aa6d8777fc02a0a64ba20ea3a830a7b84a93ec584b25bbc7a3f527bf215, exact publication_entry.py hash 7136bc7a779520d68f814d58ebf3bb18aa158d905cfeaec002b7a01aaecfdd2b. The real image supervisor ran a deliberately blocked child under a three-second absolute deadline. It timed out, escalated past ignored SIGTERM, and positively observed the process group gone. Elapsed 5.013 seconds includes the two-second termination grace. Reusing the same expired deadline started no second child.
- Cleanup: probe container removed and exact-id absence checked. engine-fy4g2v0h/ retains log, inspect, id and cleanup result. No credentials, provider, Job, deployment or production profile change.

Combined with the separately successful installed recovery-9 publication/custody/review execution and packaged completion readback, the selected positive recovery and deadline evidence are now complete. Earlier failed/aborted qualification logs remain failures and are not relabelled success. Main Git checkpoint and canonical Work closure are still pending; no claim of a full suite or new live-model qualification.
