# Successor qualification launcher — credential lifecycle only

Supersedes manual credential staging in M386071 packet71c44a15. The predecessor remains immutable; its capture.py, prepare_context.py, instruction challenge, login-status-before-exec rule, one exec maximum, bounds, redaction/private retention, cleanup and J1/N4b acceptance remain in force. Stage A is already complete; do not rerun it.

Configure the selected source once in a private mode0600 JSON file outside the execution root: exactly `{"reference": "<selected opaque reference>", "path": "<selected absolute source file>"}`. This is source configuration, **not a credential copy**. No source or file has been selected/read here. Fill the successor selection template only from explicit owner rulings, including copy authorization, source configuration, lifecycle source export, model, image/tools and live authorization. Do not put bearer bytes in the selection. The source configuration and original source may subsequently disappear: repeated preparation preserves the initialized home without reading either. Missing credentials or partial/missing lifecycle state refuse for recovery.

Use a private0700 execution root outside every Git repository, fresh for this qualification; run as the selected non-root UID:GID. The automated helper creates `live/{home,credential-state,workspace,private-output}`, securely copies the selected credential into its evidenced relative path, and retains an external receipt. It refuses a partial preexisting live directory. It never writes back to the source. Lifecycle source export must match `lifecycle-files.json`; the candidate is not yet independently accepted/imported.

Code-only preflight (does not resolve/read credentials):

```
<prepared-python> prepare_launch.py <selected-settings.json> --check
```

Only after separate credential/live execution selection and successful claim:

```
<prepared-python> prepare_launch.py <selected-settings.json>
```

The second command automates the copy and returns the existing bounded engine vectors; it never invokes the engine/provider. No manual per-Job copying remains. Run it before the predecessor context/instruction staging and workspace preparation. Rendered engine vectors are not permission to launch; exact selected source/copy/model/image and execution authority still apply. Keep the receipt directory outside all mounts. Repeating preparation is not permission to repeat the live call. Retain refreshed home and receipt together; cleanup requires positive runtime cessation and the selected private-retention decision. No automatic recovery/reset command is provided.

The existing renderer still pins the retained N3 image17d250b7 (git absent). New image46a46ee4 has retained B3 tool evidence but is not silently selected here. **Stage B remains blocked** until owner image/tool selection is incorporated into a separately reviewed execution packet, alongside source, explicit model and execution authorization. This successor implements credential-copy automation, not N4b parsing or native-use qualification. No successful turn fixture is invented.

Synthetic tests of the actual helper are in tests.tools.test_provider_selection.QualificationCredentialPreparation. They prove automatic copy, independent inode/private permissions, refreshed credential preservation with deleted source+config, missing-credential refusal and no writes/access under null selection.
