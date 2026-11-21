# Selective Git commands for the owner (not run by K)

Preflight before staging (read-only):

```sh
cd /home/sl/src/baton
git status --porcelain -- v12            # exactly 12 " M" lines, all in imported-paths.txt
sha256sum -c work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-handoffs-composer-integration/post-import.sha256
```

Stage exactly the 12 accepted paths (nothing else under v12 is changed):

```sh
cd /home/sl/src/baton
xargs -a work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-handoffs-composer-integration/imported-paths.txt git add --
git diff --cached --stat                 # 12 files
```

Optionally stage the pilot dossier records and the W385331 dossier (owner's choice):

```sh
git add -- work/records/2026/10/finding-v12-development-coordination-pilot/PROGRESS.md \
           work/records/2026/10/finding-v12-development-coordination-pilot/config \
           work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-handoffs-composer \
           work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-handoffs-composer-integration \
           work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-handoffs-2-qualification \
           work/records/2026/11/finding-v12-native-agent-handoffs-discovery
```

Commit with the prepared message:

```sh
git commit -F work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-handoffs-composer-integration/commit-message.txt
git rev-parse HEAD                       # report this identity back on T321608
```

Expected outcome: a new commit on main whose `v12/` tree carries exactly the 12 accepted paths at the candidate bytes (`post-import.sha256`); `git status --porcelain -- v12` empty afterwards. That commit is the checkpoint the qualification `bind` step consumes (`config/native-handoffs-2-qualify.sh bind`: it proves all 43 joined paths at `HEAD` and refuses anything else; the helpers, packet history and reviews are unchanged by this integration). Separate approval boundaries, not part of this commit: bundle build, worker image build, installation, any live launch.
