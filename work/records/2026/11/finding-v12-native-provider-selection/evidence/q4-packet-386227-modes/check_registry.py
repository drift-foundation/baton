"""Deterministic checks of registry.py over temporary files. No real registry or login is touched."""
import json,os,sys,tempfile
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import registry
def main():
    rows={}
    with tempfile.TemporaryDirectory(prefix='baton-q4-registry-check-',dir='/var/tmp') as temp:
        temp=Path(temp);place=temp/'credential-sources.json'
        A=('operator-file','claude-primary-subscription','/synthetic/claude');B=('operator-file','codex-pushcoin-subscription','/synthetic/codex')
        def refused(name,call):
            before=place.read_bytes() if place.exists() else None
            try:call();raise AssertionError(name+' was not refused')
            except registry.RegistryRefusal as said:rows[name]='refused: '+str(said)[:70]
            assert (place.read_bytes() if place.exists() else None)==before,name+' changed the registry'
        first=registry.add(place,[A]);assert first['registry_created'] and first['mappings'][0]['outcome']=='added' and oct(place.stat().st_mode&0o777)=='0o600';rows['create']='added'
        again=registry.add(place,[A]);assert again['mappings'][0]['outcome']=='already-present';rows['same mapping again']='already-present, unchanged'
        both=registry.add(place,[A,B]);assert [m['outcome'] for m in both['mappings']]==['already-present','added'] and both['entries']==2;rows['add beside existing']='existing kept, new added'
        held=json.loads(place.read_text());assert [one['reference'] for one in held['sources']]==['claude-primary-subscription','codex-pushcoin-subscription']
        refused('different path for an existing pair',lambda:registry.add(place,[(A[0],A[1],'/synthetic/other')]))
        refused('pair requested twice',lambda:registry.add(place,[A,A]))
        refused('relative source path',lambda:registry.add(place,[('operator-file','x','relative')]))
        refused('relative registry path',lambda:registry.add('relative.json',[A]))
        place.chmod(0o644);refused('registry readable by others',lambda:registry.add(place,[B]));place.chmod(0o600)
        link=temp/'link.json';os.symlink(place,link);refused('registry is a symlink',lambda:registry.add(link,[B]))
        bad=temp/'bad.json';bad.write_text('{"schema":"other","sources":[]}');bad.chmod(0o600);refused('unsupported schema',lambda:registry.add(bad,[A]))
        dup=temp/'dup.json';dup.write_text(json.dumps(dict(schema=registry.SCHEMA,sources=[dict(provider=A[0],reference=A[1],path=A[2])]*2)));dup.chmod(0o600);refused('registry already ambiguous',lambda:registry.add(dup,[B]))
        assert not list(temp.glob('*.q4-*')),'a temporary file was left behind'
    print(json.dumps(dict(passed=True,cases=len(rows),rows=rows,real_registry_touched=False),indent=1))
if __name__=='__main__':main()
