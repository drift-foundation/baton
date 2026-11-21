# Owner-selected retirement of old local instances

Owner explicitly requested removal of old instance folders on 2026-11-21. Scope: the 59 named entries in entries.json under /home/sl/baton-instances; live v11 authority/config outside this root is excluded. No Git mutation.

Both native-labels-5 and native-handoffs-1 reported deadline cancellation with shutdown complete before their idle manager/publisher services were stopped through their installed justfiles. Before archive, no process cwd/executable, running Docker mount or mounted filesystem referenced the instance root.

The private safety archive retains all remaining files (including credentials and historical stores), without dereferencing symlinks. It must never be committed or published. Location: /home/sl/baton-retired-archives/retirement-20261121/instances.tar.zst. This is a same-host safety copy, not an off-machine backup. Required accepted candidates and reviews already live in their owning dossiers. No database is opened or edited for this cleanup.

Removal is gated on successful archive creation, archive-to-source comparison and digest capture. Completion and reclaimed size will be appended below.

## Completed

Removed all 59 inventoried entries (57 directories and two files). The instance root is empty. Archive creation and full decompressed archive-to-source content/metadata comparison both exited 0; no differences. No active cwd/executable/open fd, running Docker bind mount or mountpoint used the root at removal. Exact measured sizes and archive digest: RESULT.json. Net reclaimed: 42.49 GiB including the retained archive.

Recovery (operator only; archive includes secrets): verify with `sha256sum -c /home/sl/baton-retired-archives/retirement-20261121/archive.sha256`; extract only selected entries to a private disk-backed recovery directory using `tar --zstd -xf /home/sl/baton-retired-archives/retirement-20261121/instances.tar.zst -C <private-recovery-directory> <entry>`. Do not restart retired instances merely to inspect evidence; archived stores are opaque preservation, not permission for direct SQL reads. Existing instance-path references in historical dossiers are now recovery locators, not live files. This archive is local-only and not disaster recovery.
