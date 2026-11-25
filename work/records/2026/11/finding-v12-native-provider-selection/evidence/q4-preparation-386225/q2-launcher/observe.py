"""How the launcher decides a stage's capture is over. Observation only, never acceptance.

Two forms are recognised and nothing else:

  exchange   the transient manager exchange reports answered/faulted with a terminal;
  custody    the manager has already settled the stage: it reports `completed`, and the
             control store holds this exact attempt's frozen result and custody artifacts.

The 386221 launcher knew only the first. Real reconciliation settled the stage and cleared
the exchange between two polls, so it waited out the whole capture bound. The custody form
is proved by identity, never by elapsed time or by a directory existing. The manager's two
records (Job status and control store) must agree with each other and with the
content-addressed result manifest; a file artifact is re-hashed, a directory artifact is the
manager's sealed tree and is located but not re-hashed here (byte verification of the edit
stays with collect.py after cessation): a completed stage
whose evidence does not bind to the watched attempt RAISES (the capture fails, held) and is
not waited on and not accepted. Neither form says the task succeeded; the reviewer judges.
"""
import hashlib,os,stat
from pathlib import Path
MAX_ARTIFACT=64*1024*1024
SETTLED_RUNTIME=('destroyed','absent')
ENDED_WITHOUT_RESULT=('exceptional','failed','blocked','cancelled')

def _sha(path):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as stream:
        info=os.fstat(stream.fileno());assert stat.S_ISREG(info.st_mode) and info.st_size<=MAX_ARTIFACT,'custody artifact is not a bounded regular file'
        digest=hashlib.sha256();count=0
        while raw:=stream.read(65536):count+=len(raw);digest.update(raw)
    return count,'sha256:'+digest.hexdigest()

def exchange_terminal(stage):
    seen=stage.get('exchange') or {}
    if seen.get('state') in ('answered','faulted') and seen.get('terminal') is not None:
        return dict(kind='exchange',state=seen['state'],exchange=seen)
    return None

def completed_custody(stage,frozen,manifest,*,attempt,stage_id,work_id,authority_uuid,custody_root):
    """The durable form, or None while the stage is not completed. Raises on any identity disagreement."""
    if stage.get('state')!='completed':return None
    assert attempt,'a completed stage was observed before any attempt was bound'
    assert stage.get('stage_id')==stage_id and stage.get('attempt_id')==attempt,'completed stage names another attempt'
    episodes=stage.get('episodes') or []
    assert episodes and episodes[-1].get('attempt_id')==attempt and episodes[-1].get('episode')==stage.get('episode'),'current episode names another attempt'
    runtime=stage.get('runtime') or {}
    assignment=(runtime.get('assignment') or {}).get('work_ref') or {}
    assert assignment=={'authority_uuid':authority_uuid,'work_id':work_id},'completed runtime is assigned to another Work'
    assert runtime.get('execution_runtime') in SETTLED_RUNTIME,'completed stage whose runtime is not settled'
    assert type(frozen) is dict and frozen.get('attempt_id')==attempt and frozen.get('disposition')=='completed','no completed frozen result for this attempt'
    assert frozen.get('result_id') and str(frozen.get('manifest_digest','')).startswith('sha256:')
    present={one.get('name') for one in ((manifest or {}).get('outputs') or []) if one.get('status')=='present'}
    assert 'proposal' in present,'the sealed result manifest does not record a present proposal'
    shown={one['output_name']:one for one in (stage.get('artifacts') or [])}
    held={one['output_name']:one for one in (frozen.get('artifacts') or [])}
    assert shown and set(shown)==set(held) and 'proposal' in shown,'status and control store disagree about custody outputs'
    root=Path(custody_root).resolve();proved={}
    for name,one in sorted(shown.items()):
        assert one['artifact_id']==attempt+':'+name==held[name]['artifact_id'],'custody artifact belongs to another attempt'
        assert one['content_digest']==held[name]['content_digest'] and one['bytes']==held[name]['bytes']
        assert one['locator'].startswith('file://')
        place=Path(one['locator'][len('file://'):])
        assert name in present,'custody output absent from the sealed result manifest'
        assert not place.is_symlink() and place.resolve().is_relative_to(root) and place.exists(),'custody artifact missing or outside this attempt custody'
        if place.is_dir():form='sealed-tree'
        else:
            form='file';assert _sha(place)==(one['bytes'],one['content_digest']),'custody artifact bytes differ from the frozen record'
        proved[name]=dict(artifact_id=one['artifact_id'],bytes=one['bytes'],content_digest=one['content_digest'],form=form)
    return dict(kind='custody',state='completed',attempt_id=attempt,result_id=frozen['result_id'],manifest_digest=frozen['manifest_digest'],artifacts=proved,execution_runtime=runtime['execution_runtime'])

def observe(stage,frozen_of,manifest_of,**identity):
    """One poll. Returns (observation or None, keep_waiting)."""
    seen=exchange_terminal(stage)
    if seen is not None:return seen,False
    if stage.get('state')=='completed':
        frozen=frozen_of(identity['attempt']) if identity['attempt'] else None
        return completed_custody(stage,frozen,manifest_of(frozen) if frozen else None,**identity),False
    return None,stage.get('state') not in ENDED_WITHOUT_RESULT
