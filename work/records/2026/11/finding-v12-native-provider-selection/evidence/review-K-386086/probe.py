import json, os, sys, tempfile
from pathlib import Path
R = '/var/tmp/baton-k-review-386086'
sys.path[:0] = [R + '/repo/v12/python', R + '/repo/v12/python/src']
from baton_v12.provider_policy.home import prepare, credential_state
from baton_v12.worker_manager.provider_home import initialize_credential
out = {}
def tried(f):
    try: return 'ok: ' + repr(f())
    except BaseException as e: return type(e).__name__ + ': ' + str(e)[:110]
def fresh(name):
    base = Path(tempfile.mkdtemp(prefix=name + '-', dir=R + '/roots'))
    home = base / 'home'; state = base / 'state'; home.mkdir(mode=0o700); state.mkdir(mode=0o700)
    seed = base / 'seed'; seed.write_bytes(b'SYNTHETIC-NOT-A-CREDENTIAL'); seed.chmod(0o600)
    return base, home, state, seed
P = 'store/credential'
calls = []
def seeder(home, seed):
    def run():
        calls.append('source-read'); prepare(str(home), credential_path=P, delivered=str(seed), mode='seeded-retained'); return 'seeded'
    return run
# P1: the source is unavailable on the very first start; then it is fixed.
base, home, state, seed = fresh('p1'); missing = base / 'absent-source'
out['P1_first_start_source_absent'] = tried(lambda: initialize_credential(str(home), str(state), P, seeder(home, missing)))
out['P1_home_after_failure'] = tried(lambda: credential_state(str(home), P))
out['P1_home_entries'] = sorted(os.listdir(home)); out['P1_receipt'] = json.loads((state / 'credential.json').read_text())
out['P1_retry_with_good_source'] = tried(lambda: initialize_credential(str(home), str(state), P, seeder(home, seed)))
# P2: normal first start, then restart variants.
base, home, state, seed = fresh('p2'); calls.clear()
out['P2_first'] = tried(lambda: initialize_credential(str(home), str(state), P, seeder(home, seed)))
seed.unlink()
def boom(): raise AssertionError('source must not be resolved on restart')
out['P2_restart_source_deleted'] = tried(lambda: initialize_credential(str(home), str(state), P, boom))
cred = home / P; new = home / 'store/.new'; new.write_bytes(b'SYNTHETIC-REFRESHED'); new.chmod(0o600); os.rename(new, cred)
out['P2_restart_after_rename_refresh'] = tried(lambda: initialize_credential(str(home), str(state), P, boom)); out['P2_bytes_kept'] = cred.read_bytes().decode()
out['P2_worker_side_prepare_no_delivery'] = tried(lambda: prepare(str(home), credential_path=P, delivered='/nonexistent/slot', mode='seeded-retained'))
cred.chmod(0o644)
out['P2_restart_refresh_left_0644'] = tried(lambda: initialize_credential(str(home), str(state), P, boom))
cred.chmod(0o600); cred.unlink()
out['P2_restart_credential_lost'] = tried(lambda: initialize_credential(str(home), str(state), P, boom))
out['P2_worker_side_after_loss'] = tried(lambda: prepare(str(home), credential_path=P, delivered=str(base / 'seed2'), mode='seeded-retained'))
out['P2_source_reads_total'] = len(calls)
# P3: receipts hold no credential bytes or digests.
base, home, state, seed = fresh('p3'); initialize_credential(str(home), str(state), P, seeder(home, seed))
out['P3_receipts'] = [json.loads((state / 'credential.json').read_text()), json.loads((home / '.baton-credential.json').read_text())]
out['P3_modes'] = {str(p.relative_to(base)): oct(p.stat().st_mode & 0o777) for p in [home / P, home / '.baton-credential.json', state / 'credential.json']}
out['P3_distinct_inode'] = (home / P).stat().st_ino != seed.stat().st_ino
# P4: qualification helper.
from tools.qualification_credentials import prepare_selected
base = Path(tempfile.mkdtemp(prefix='p4-', dir=R + '/roots')); base.chmod(0o700); root = base / 'root'; root.mkdir(mode=0o700)
src = base / 'src'; src.write_bytes(b'SYNTHETIC-NOT-A-CREDENTIAL'); src.chmod(0o600)
cfg = base / 'cfg.json'; cfg.write_text(json.dumps({'reference': 'synthetic-ref', 'path': str(src)})); cfg.chmod(0o600)
sel = dict(authorization_credential_copy='SYNTHETIC', credential_source_reference='synthetic-ref', credential_path_evidence='SYNTHETIC', credential_storage_mode_evidence='SYNTHETIC',
           private_retention_and_cleanup_owner='SYNTHETIC', refresh_copy_disposition='SYNTHETIC', uid=os.getuid(), gid=os.getgid(), execution_root=str(root),
           codex_home_relative_to_home='synthetic-codex-home', credential_relative_path='synthetic-name', instruction_relative_to_home='synthetic-instructions/worker.md')
out['P4_unauthorized'] = tried(lambda: prepare_selected(dict(sel, authorization_credential_copy=None), str(cfg))); out['P4_nothing_created'] = not (root / 'live').exists()
out['P4_first'] = tried(lambda: prepare_selected(sel, str(cfg)))
c = root / 'live/home/synthetic-codex-home/synthetic-name'; c.write_bytes(b'SYNTHETIC-REFRESHED'); src.unlink(); cfg.unlink()
out['P4_repeat_without_source_or_config'] = tried(lambda: prepare_selected(sel, str(cfg))); out['P4_bytes_kept'] = c.read_bytes().decode()
c.unlink(); out['P4_repeat_after_loss'] = tried(lambda: prepare_selected(sel, str(cfg)))
json.dump(out, open(R + '/probe.json', 'w'), indent=1); print(json.dumps(out, indent=1))
