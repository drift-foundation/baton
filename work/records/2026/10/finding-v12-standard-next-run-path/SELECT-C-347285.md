# Concrete C selection after accepted B

B accepted in review-2026-10-21T15-16-49Z.md. No repeated installation/allocation/check required.

Owner selection text:

> Select exactly one Stage C invocation w339626-live-345599 through the installed client, authority15c5c8ce04d14f3e83651355085a03a8,Work15c5c8ce-W1,uid997/gid986. Bind generated PACKET SHA2564d24ec31635de45c4bdfa72247bbedb28e673fc2985026dd6b4c825df27a2dc5 and input SHA2565fc07524d1255a92d0f4b94a31317fa338013eb3997c7b70c989f19059bbd9dd. Provider300/verifier30/total600/cleanup60,one invocation,no retry,existing lease900. Use run-c-347285.py from normal sl host terminal,never sudo the helper. Retain receipts and private final reports for independent review. No recovery,second start or general longer-Job deployment is selected.

Helper SHA256 `03592c6d522dc7717d33e4c34a3b87e74036d84a92cf524671f22032cfc125e5`. The flag does not grant authority; this remains
unselected until owner disposition. Optional read-only check is the same command
without the flag. After exact selection, one runnable command:

```sh
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-standard-next-run-path/run-c-347285.py --execute-selected-run
```

Keep this in a supervised foreground host terminal. The helper calls installed
client start once, then status, recording stdout/stderr/status/duration in fresh
operator-c-receipts-347285/. It refuses an existing receipt directory. No fallback
sudo, retry, deletion, reallocation, configuration edit or direct controller call.
If interrupted or result unknown, preserve receipts and inspect cessation; never
repeat start. A helper/dispatch exit is not proof of runtime cessation or product
acceptance. Return start/status receipts and operator-accessible nonsecret final
outcome/controller/manager/progress and candidate/cleanup identities under
/var/lib/baton-next-run/w339626-live-345599/packet/ for independent collection.
Do not copy provider transcript or credential contents. Missing final reports
remain incomplete evidence; no cleanup or recovery is implicitly selected.
