"""Add (provider, reference) -> path mappings to a baton.user-credential-sources/1 registry.

The supported registry format, nothing else. Only the registry document is read or written.
A source path is recorded as text and is never opened, stat-ed or resolved here.

Conflict rules, each a refusal that changes nothing:
  - the registry exists and is not a private ordinary file owned by this user;
  - it is not the supported schema, or already holds a duplicated pair;
  - a wanted pair is already mapped to a DIFFERENT path (never overwritten).
A wanted pair already mapped to the same path is left as it is. Entries this call does not
name are preserved byte for byte in meaning and order. The write is atomic and mode 0600.
"""
import argparse,json,os,stat,sys
from pathlib import Path
SCHEMA='baton.user-credential-sources/1'
class RegistryRefusal(Exception):pass
def _read(path):
    try:fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    except FileNotFoundError:return None
    except OSError as failed:raise RegistryRefusal('the registry cannot be opened as an ordinary file ('+type(failed).__name__+')')
    with os.fdopen(fd,'rb') as stream:
        info=os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.geteuid() or stat.S_IMODE(info.st_mode)&0o077:
            raise RegistryRefusal('the registry is not a private ordinary file owned by this user')
        raw=stream.read(1048577)
    if len(raw)>1048576:raise RegistryRefusal('the registry is larger than 1 MiB')
    try:held=json.loads(raw)
    except ValueError:raise RegistryRefusal('the registry is not one JSON document')
    if type(held) is not dict or set(held)!={'schema','sources'} or held['schema']!=SCHEMA or type(held['sources']) is not list:
        raise RegistryRefusal('the registry is not a '+SCHEMA+' document')
    seen=set()
    for one in held['sources']:
        if type(one) is not dict or set(one)!={'provider','reference','path'} or any(type(one[k]) is not str or not one[k] for k in one):
            raise RegistryRefusal('the registry holds a malformed source entry')
        pair=(one['provider'],one['reference'])
        if pair in seen:raise RegistryRefusal('the registry already maps one pair twice')
        seen.add(pair)
    return held
def add(path,wanted):
    """wanted: list of (provider, reference, absolute path). Returns what happened per pair."""
    path=Path(path)
    if not path.is_absolute():raise RegistryRefusal('the registry is named by an absolute path')
    for provider,reference,source in wanted:
        if not all(type(x) is str and x for x in (provider,reference,source)) or not os.path.isabs(source):
            raise RegistryRefusal('a mapping names a provider, a reference and an absolute source path')
    if len({(p,r) for p,r,_ in wanted})!=len(wanted):raise RegistryRefusal('one pair is requested twice')
    held=_read(path);created=held is None
    held=held or dict(schema=SCHEMA,sources=[])
    present={(one['provider'],one['reference']):one['path'] for one in held['sources']};answer=[]
    for provider,reference,source in wanted:
        existing=present.get((provider,reference))
        if existing is None:
            held['sources'].append(dict(provider=provider,reference=reference,path=source));answer.append(dict(provider=provider,reference=reference,outcome='added'))
        elif existing==source:answer.append(dict(provider=provider,reference=reference,outcome='already-present'))
        else:raise RegistryRefusal('a requested pair is already mapped to a different path; nothing was changed')
    if created or any(one['outcome']=='added' for one in answer):
        temporary=path.with_name(path.name+'.q4-'+str(os.getpid()))
        fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        try:
            with os.fdopen(fd,'w') as stream:
                stream.write(json.dumps(held,indent=2)+'\n');stream.flush();os.fsync(stream.fileno())
            os.replace(temporary,path)
        except BaseException:
            try:os.unlink(temporary)
            except FileNotFoundError:pass
            raise
    return dict(registry_created=created,entries=len(held['sources']),mappings=answer)
def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry',required=True)
    parser.add_argument('--map',action='append',required=True,metavar='PROVIDER:REFERENCE=/ABSOLUTE/PATH')
    taken=parser.parse_args(argv);wanted=[]
    for one in taken.map:
        pair,_,source=one.partition('=');provider,_,reference=pair.partition(':');wanted.append((provider,reference,source))
    try:print(json.dumps(add(taken.registry,wanted),indent=1));return 0
    except RegistryRefusal as refused:
        print(json.dumps(dict(refused=str(refused))));return 2
if __name__=='__main__':sys.exit(main())
