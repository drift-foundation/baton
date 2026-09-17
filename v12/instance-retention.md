# Initial v12 instance retention policy

Retain all intaken artifacts and their provenance. Do not automatically discard
or delete them. Any later cleanup policy must be selected explicitly before use.

This policy selects the bootstrap retention disposition `retain`. It does not
create Jobs, authorize execution, or change the current v11 coordination authority.
