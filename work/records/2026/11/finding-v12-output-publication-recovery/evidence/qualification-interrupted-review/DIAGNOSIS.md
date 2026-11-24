# Interrupted review qualification

The reviewer reports settlement-expired, no verdict. The first gate stopped its manager just after the review admission (07:37:10Z), because of the incorrect runtime-user assertion. The resume started at 07:39:50Z. offers.SETTLE_SECONDS is 60; settle_claim retires an uncommitted claim after that deadline. This is claim settlement, not provider timeout, and no reviewer execution is established. Publication/custody remains retained. A second restart cannot revive the retired claim.

Ctrl+C interrupted the Python wrapper and shell together. The wrapper did not wait through cleanup; manager/publisher remained. Coordinator used this instance's supported just stop and confirmed both PIDs stopped. Docker ps -a filtered by this exact authority returned no containers. No container or evidence was removed.

Harness corrections prepared: fail immediately when review.state becomes a terminal failure instead of polling for 4800 seconds; run the shell in its own session and forward interrupt as TERM while waiting for its cleanup, so Ctrl+C cannot simply abandon the supervisor. These do not alter any Job or claim deadline, retry policy or accepted product source. Old qualification scripts/evidence remain unchanged.
