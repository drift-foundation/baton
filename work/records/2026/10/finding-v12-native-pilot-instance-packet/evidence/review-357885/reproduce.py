import sys,pathlib,tempfile,shutil,json,time
p=pathlib.Path('/home/sl/src/baton/work/records/2026/10/finding-v12-native-pilot-instance-packet');sys.path.insert(0,str(p/'post-install-357462'))
import configure,prove
t=time.monotonic()
with tempfile.TemporaryDirectory(prefix='w325959-review-tamper-') as home:
 h=pathlib.Path(home); staged=h/'packet';shutil.copytree(p/'post-install-357462',staged);shutil.copytree(p/'revision-4',h/'revision-4')
 root=h/'destination';places,selector,_=prove.installed_shape(root,prove.Checks())
 for n in ['source-implementation-pilot','source-review-pilot']:pathlib.Path(places['repository'],n,'.simulated-git').mkdir(parents=True)
 for n in configure.PACKET_PINS:
  (staged/n).write_text(json.dumps(prove.retarget(prove.inputs(n),root),indent=1,sort_keys=True)+'\n')
 pins={n:configure._of(staged/n) for n in configure.PACKET_PINS}; selected=dict(configure.SELECTED,runtime_digest=selector['runtime']['digest'])
 recipe=h/'revision-4/configuration/manifest-inputs.json'; doc=json.loads(recipe.read_text());original=doc['proposed_accountability_documents']['credential_policy_digest']['digest'];doc['proposed_accountability_documents']['credential_policy_digest']['digest']='sha256:'+'0'*64;recipe.write_text(json.dumps(doc))
 before=prove.tree_digest(root)
 result=configure.compose(str(root),staged,runner=prove.repository_runner([]),pins=pins,selected=selected)
 manifest=configure.sealed_manifest(staged,selector['authority_uuid'],result['selected_work'],prove.inputs('task.json'),b'fixture task bytes')
 out={'accepted_plan_with_tampered_inherited_recipe':result['planned'],'default_inherited_pins':configure.INHERITED_PINS,'original_credential_digest':original,'manifest_credential_digest':manifest['credential_policy_digest'],'installation_unchanged':before==prove.tree_digest(root),'elapsed_seconds':time.monotonic()-t,'boundary':'Disposable, simulated repository answers; no Git or production access. Packet pins/selector retargeted to disposable fixture; inherited argument deliberately left at owner defaults.'}
 (p/'evidence/review-357885/TAMPER.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
