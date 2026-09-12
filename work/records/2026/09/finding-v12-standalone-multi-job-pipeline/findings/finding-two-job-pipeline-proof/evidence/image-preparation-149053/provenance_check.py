from pathlib import Path
import ast,difflib,hashlib,json,stat,time
repo=Path('/home/sl/src/baton');r=repo/'work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof';p=r/'prepared-149053';e=r/'evidence/image-preparation-149053'
t=time.monotonic();report={'work':'W71879','claim':149053,'manifests':{},'provider_chain':{},'source_bindings':{},'changed_copies':[],'unchanged_copies':[]}
def hash_(p):return 'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()
for rel,expected in [('evidence/diagnostic-148870/candidate-manifest.json','0c13a9034aef59636214749876bb83960c18a457dc79a992cf1c6b2c15d0028f'),('prepared-147109/candidate-manifest.json','94d8b8e83b5d11a25edc8b91ae54e9bef98bc7a718cd8d17616784a00ea22cb2'),('evidence/run6-freeze-146988/candidate-manifest.json','87a320bdee36cfdca8e7d18372e65ff26eeb314eeda948db3402692b328dd0a9')]:
    m=r/rel;assert hash_(m)=='sha256:'+expected
    files=json.loads(m.read_text())['files'];checked={}
    for name,rec in files.items():
        f=repo/name;s=f.lstat()
        assert stat.S_ISREG(s.st_mode) and hash_(f)==rec['sha256'] and s.st_size==rec['bytes'] and oct(stat.S_IMODE(s.st_mode))==rec['mode'],name
    report['manifests'][rel]={'sha256':hash_(m),'verified_files':len(files)}
old=json.loads((r/'prepared-146897/evidence/provenance.json').read_text())
for name,rec in old['provider_chain'].items():
    f=repo/name
    if rec.get('expected_absence_matches'):
        assert not f.exists() and not f.is_symlink();report['provider_chain'][name]={'absent':True}
    else:
        assert hash_(f)=='sha256:'+rec['sha256'],name
        report['provider_chain'][name]={'sha256':hash_(f)}
for group in ('source_requirements','current_observation_sources'):
    for name,expected in old[group].items():
        assert hash_(repo/name)==expected;report['source_bindings'][name]=expected
for name in ('v12/worker/claude_agent.py','v12/python/tests/manager/test_claude_agent.py'):
    report['source_bindings'][name]=hash_(repo/name)
patch=[]
for f in sorted((r/'prepared-148870').rglob('*')):
    if not f.is_file() or '__pycache__' in f.parts:continue
    rel=str(f.relative_to(r/'prepared-148870'))
    if rel=='candidate-images.json':new=p/'offline-images.json'
    elif rel=='test_run6_preparation.py':new=p/'test_run7_preparation.py'
    else:new=p/rel
    if f.read_bytes()==new.read_bytes():report['unchanged_copies'].append(rel)
    else:
        report['changed_copies'].append({'old':rel,'new':str(new.relative_to(p))})
        if f.suffix in ('.py','.sh','.json'):
            patch.extend(difflib.unified_diff(f.read_text().splitlines(True),new.read_text().splitlines(True),fromfile='prepared-148870/'+rel,tofile='prepared-149053/'+str(new.relative_to(p))))
for f in p.glob('*.py'):ast.parse(f.read_text(),filename=str(f))
assert not Path('/home/sl/.local/state/baton/v12/w71879-run7').exists()
for name in ('candidate-images.json','selected-images.json','execution-review.json','validation.json','frozen-config','image-build'):
    assert not (p/name).exists(),name
report['fresh_external_root_absent']=True;report['actual_image_and_input_outputs_absent']=True
report['historical_baseline_observation']={'commit':'2fbb2d456638e5706218020aebfa47f0a82c8920','tree':'3492ba64448ab9d39bde53ee6456ce24e74ece2c','status':'clean','command_boundary':'direct git --no-optional-locks show/status; no mutation'}
report['image_read_observation']={'command_boundary':'direct docker image inspect with metadata-only format','immutable_base':'sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4','old_images':json.loads((p/'offline-images.json').read_text()),'platform':'linux/amd64','user':'65532:65532','entrypoints_match':True,'old_images_inherit_exact_base_layers':True,'new_images_built':False}
report['verification_seconds']=time.monotonic()-t
(e/'provenance.json').write_text(json.dumps(report,indent=2)+'\n')
(e/'preparation-delta.patch').write_text(''.join(patch))
print(json.dumps({k:report[k] for k in ('manifests','verification_seconds','changed_copies')},indent=2))
