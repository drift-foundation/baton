"""Labelled synthetic image-gate cases; never actual qualification evidence."""
import copy,hashlib,json,tempfile
from pathlib import Path
from unittest import mock
from image_gate import qualify
P=Path(__file__).resolve().parent
def synthetic():
    e=json.loads((P/'q1-accepted-evidence.json').read_text());e['review']='SIMULATION-ONLY'
    k=e['retained'];ident=json.loads((P/'q1-build.json').read_text());img='sha256:'+'e'*64
    k['image-inspect.json']['Id']=img
    k['image-inspect.json']['Config']['Labels']={'org.opencontainers.image.revision':ident['source_commit'],'io.baton.q1.source':ident['source_manifest_sha256'],'io.baton.q1.packet':'q1-386185'}
    k['worker-observation.json']['identity']=ident
    for n in ('launched-image.json','receipt-after-removal.json'):
        k[n]['admitted_image']=img;k[n]['observation']['image_id']=img
    return e
def main():
    with tempfile.TemporaryDirectory(prefix='baton-q2-image-check-',dir='/var/tmp') as temp:
        path=Path(temp)/'synthetic.json'
        def check(e):
            raw=json.dumps(e).encode();path.write_bytes(raw)
            with mock.patch('subprocess.Popen',side_effect=AssertionError('no engine')):return qualify(path,hashlib.sha256(raw).hexdigest())
        assert check(synthetic())['image']=='sha256:'+'e'*64
        negatives=[]
        old=json.loads((P/'q1-accepted-evidence.json').read_text());negatives.append(old)
        for mutate in (
            lambda k:k['worker-observation.json']['identity']['image_files'].update({'/opt/baton/codex_agent.py':'0'*64}),
            lambda k:k['RESULT.json']['cleanup'].update(removed=False),
            lambda k:k['receipt-after-removal.json']['observation'].update(image_id='sha256:'+'f'*64),
            lambda k:k['worker-observation.json'].update(provider_called=True),
            lambda k:k['image-inspect.json']['Config']['Labels'].update({'org.opencontainers.image.revision':'wrong'}),
        ):
            e=copy.deepcopy(synthetic());mutate(e['retained']);negatives.append(e)
        for e in negatives:
            try:check(e)
            except AssertionError:pass
            else:raise AssertionError('invalid evidence accepted')
    print(json.dumps(dict(passed=True,positive=1,negative=len(negatives),real_engine_calls=0,synthetic_only=True)))
if __name__=='__main__':main()
