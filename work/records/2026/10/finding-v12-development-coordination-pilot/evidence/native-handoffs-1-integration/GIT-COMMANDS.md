# Selective Git commands for the owner (not run by K)

Preflight before staging (read-only):

```sh
cd /home/sl/src/baton
git status --porcelain -- v12            # exactly 30 " M" and 6 "??" lines, all in imported-paths.txt
sha256sum -c work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-handoffs-1-integration/post-import.sha256
```

Stage exactly the 36 accepted paths (nothing else under v12 is changed):

```sh
cd /home/sl/src/baton
xargs -a work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-handoffs-1-integration/imported-paths.txt git add --
git diff --cached --stat                 # 36 files
```

Optionally stage the pilot dossier records and evidence (owner's choice; untracked owner files under the W385331 dossier are yours):

```sh
git add -- work/records/2026/10/finding-v12-development-coordination-pilot/PROGRESS.md \
           work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-handoffs-1-recovery \
           work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-handoffs-1-continuation \
           work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-handoffs-1-correction \
           work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-handoffs-1-correction-2 \
           work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-handoffs-1-integration \
           work/records/2026/11/finding-v12-native-agent-handoffs-discovery
```

Commit with the prepared message:

```sh
git commit -F work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-handoffs-1-integration/commit-message.txt
git rev-parse HEAD                       # report this identity back on T321608
```

Expected outcome: a new commit on main whose `v12/` tree carries exactly the 36 accepted paths at the candidate bytes (`post-import.sha256`); `git status --porcelain -- v12` empty afterwards. Separate approval boundaries, not part of this commit: worker image rebuild (`v12/worker/claude_agent.py` is a Dockerfile input), instance update, any live launch.
