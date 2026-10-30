# Read-only collection for consumed C

Run from normal sl host terminal (do not sudo this outer helper):

```sh
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-standard-next-run-path/collect-c-347468.py
```

Helper SHA2567caed820d8c7927306e620661a872962df7228b47dfe1721edd875e031990893.
It invokes fixed read-only sudo collection and writes receipts under
operator-diagnostics-347468/. Return that directory for diagnosis. Optional
--check parses the collector without sudo or collection. No start,repair,retry,
recovery,reinstall,credential/DB/provider-transcript read or engine mutation.
Stop on refusal and preserve partial receipts; do not remove the receipt directory
to force a repeat. Missing reports/read errors remain unknown. The exact filtered
container listing and uid997 process metadata are observations,not automatic
release authority. The reviewer will determine the bounded fix from these facts.
