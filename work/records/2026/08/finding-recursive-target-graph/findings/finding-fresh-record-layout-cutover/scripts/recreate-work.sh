#!/bin/sh
# W92: recreate the still-relevant open Work in the FRESH schema-15
# authority. Exactly the 13 items inventoried in ../INVENTORY.md §F —
# nothing else crosses over; trial threads, messages, queue state, and
# closed Work retire with the old authority.
#
# Usage: BW=/path/to/bin/baton-work CONFIG=/path/to/baton.json \
#        ROOT=<configured-root-id> sh recreate-work.sh
# Each create is effectively-once (--op-id), so a crashed run reruns safely.
# The umbrella design record is the canonical dossier for every item whose
# finding lives among its children.
set -eu

: "${BW:?BW=/path/to/bin/baton-work}"
: "${CONFIG:?CONFIG=/path/to/baton.json}"
: "${ROOT:?ROOT=configured root id for the baton repository}"

RECORD="work/records/2026/08/finding-recursive-target-graph"
AS="--participant baton.claude"

# Fresh-schema rule: creation requires a concrete classification. The
# bug-queue items were confirmed UX defects in the trial; the feature
# requests are deliberate design decisions.
make() { # op kind classification title
  op="$1"; kind="$2"; cls="$3"; title="$4"
  "$BW" --config "$CONFIG" $AS --op-id "w92-recreate-$op" create \
    --team baton --kind "$kind" --title "$title" \
    --origin self-initiated --classification "$cls" \
    --body "Recreated at the W92 records/open cutover from the retired schema-14 trial ($op). Decision provenance: $RECORD. Trial history is not migrated." \
    --binding "$ROOT:$RECORD"
}

make w2  bug  confirmed-defect "Rename the v11 executable to baton"
make w3  bug  confirmed-defect "Fix the init activation command hint"
make w4  bug  confirmed-defect "Configure repository roots in baton.json"
make w6  bug  confirmed-defect "Render confirmed defects as defct"
make w9  bug  confirmed-defect "Confirm before exiting the TUI"
make w12 bug  confirmed-defect "Show the Work ID in Work details"
make w10 feat design-choice "Add three-level priority to Work"
make w13 feat design-choice "Use key-value syntax for v11 operations"
make w14 feat design-choice "Add context-sensitive command-bar assistance"
make w19 feat design-choice "Add multiline command batch mode"
make w34 feat design-choice "Add ultra-short local Work selectors"
make w78 feat design-choice "Add project metadata and composable Work filters"
make w84 feat design-choice "Highlight recently changed Work"

# Reviewer follow-up 80bbe488 (2026-08-16): the TUI Work-search request is
# recreated PARKED — deferred beyond this release; pin in
# findings/finding-tui-work-search/.
SEARCH_ID=$("$BW" --config "$CONFIG" $AS --op-id "w92-recreate-wsearch" create \
  --team baton --kind feat --title "Search Work from the TUI" \
  --origin self-initiated --classification design-choice \
  --body "Recreated at the W92 cutover; deferred beyond this release. Pin: $RECORD/findings/finding-tui-work-search." \
  --binding "$ROOT:$RECORD" \
  | sed -n 's/.*"work_id": "\([^"]*\)".*/\1/p')
"$BW" --config "$CONFIG" $AS --op-id "w92-park-wsearch" phase "$SEARCH_ID" \
  --to parked --reason "deferred beyond the fresh-authority release (reviewer follow-up 80bbe488)"

echo "14 Work items recreated with canonical record bindings (1 parked)."
