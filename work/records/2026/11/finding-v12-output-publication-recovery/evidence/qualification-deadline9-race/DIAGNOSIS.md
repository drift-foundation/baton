
## 2026-11-24T08:33:41.241361+00:00 — deadline-9 qualification race, not a deadline proof

Publisher container c0117a8f… ran from 08:22:23.374299131Z to 08:22:23.606530597Z (232 ms), exited 0, and was already exited in the watcher's captured inspect. Docker refused the later pause as not running. The watcher recorded pause-unacknowledged and pause-op-done, but the parent waited the full 600-second observation allowance before failing. Cleanup stopped services and the selected container is absent. No deadline qualification is claimed; successful recovery-9 remains accepted and retained. Evidence: evidence/qualification-deadline9-race/.

Owner approved short, explicitly selected limits for future deadline tests; full-duration runs only when duration matters. The current product profile pins 900 seconds, so no installed limit has been silently changed. A deterministic way to hold the publisher before adoption plus an explicitly selected short test limit is needed before another engine attempt. The prepared fail-fast script stops immediately on an acknowledged failed pause; it alone does not fix the pause race and is not a launch packet.
