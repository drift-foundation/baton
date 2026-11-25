"""Read-only gate for a separately reviewed Q1-format offline evidence bundle.

Hashes bind bytes, not authority. The owner must select the review and exact bundle
hash before execution. q1-build.json here is an expectation, never a build receipt.
"""
import hashlib,json,re
from pathlib import Path
P=Path(__file__).resolve().parent
OLD='sha256:34364fb17d18b9abd1d155c33123888313a31141cc433322e68a7ad170a98fa7'
def qualify(path,digest):
    assert path.is_absolute() and not path.is_symlink()
    raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==digest,'image evidence digest mismatch'
    evidence=json.loads(raw)
    assert evidence['review'] and evidence['review'] not in ('pending','unselected','OWNER_MESSAGE_ID')
    assert evidence['manifest_files_verified']>0
    kept=evidence['retained'];expected=json.loads((P/'q1-build.json').read_text())
    result=kept['RESULT.json'];assert result['passed'] is True and result['error'] is None
    assert result['provider_calls']==0 and result['cleanup']['ceased'] is True and result['cleanup']['removed'] is True
    image=kept['image-inspect.json'];identity=image['Id']
    assert re.fullmatch('sha256:[0-9a-f]{64}',identity) and identity!=OLD,'old Q1 image cannot qualify changed worker'
    assert image['Config']['Entrypoint']==['python3','/opt/baton/codex_entry.py']
    worker=kept['worker-observation.json'];observed=worker['identity']
    for name in ('cli_version','codex_binary_bytes','codex_binary_sha256','image_files'):
        assert observed[name]==expected[name],name
    assert worker['codex_binary_sha256']==expected['codex_binary_sha256']
    assert worker['provider_called'] is False and worker['uid']==1000 and worker['gid']==1000
    assert worker['home']=='/run/baton/provider-home' and worker['codex_home']=='/run/baton/provider-home/codex'
    assert worker['instruction_sha256']==expected['image_files']['/opt/baton/provider_policy/worker_instructions.md']
    assert all(worker['tools'][name]['exit_status']==0 for name in ('codex','git','python3','sh','sha256sum'))
    labels=image['Config']['Labels']
    assert labels['org.opencontainers.image.revision']==observed['source_commit']
    assert labels['io.baton.q1.source']==observed['source_manifest_sha256']
    receipt=kept['launched-image.json'];assert receipt==kept['receipt-after-removal.json']
    assert receipt['admitted_image']==identity and receipt['observation']['image_id']==identity
    assert receipt['observation']['started_at'] and receipt['observation']['runtime_id']
    return dict(image=identity,labels=labels,evidence_sha256=digest,review=evidence['review'],retained=evidence)
