"""Read tracked checkpoint bytes only. Exact AST duplicates retain identifiers."""
import ast, collections, hashlib, io, json, subprocess, tarfile
base="b5abf7983fb07eb3a8268f2d4559a04de9c0f1bd"
modules=[]; functions=[]; copies=collections.defaultdict(list); roots=collections.Counter()
with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(["git","archive",base,"v12"]))) as archive:
    for f in archive:
        if not f.isfile(): continue
        roots[f.name.split("/")[1]]+=1
        if not f.name.endswith(".py") or not f.name.startswith(("v12/python/src/","v12/python/tools/","v12/worker/")): continue
        data=archive.extractfile(f).read(); modules.append((len(data.splitlines()),f.name))
        for node in ast.walk(ast.parse(data)):
            if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)): continue
            span=node.end_lineno-node.lineno+1; loc=f"{f.name}:{node.lineno} {node.name}"
            functions.append((span,loc))
            if span>=10:
                copies[hashlib.sha256(ast.dump(node).encode()).hexdigest()].append((span,loc))
print(json.dumps(dict(base=base,roots=roots,module_count=len(modules),function_count=len(functions),modules=sorted(modules,reverse=True)[:25],functions=sorted(functions,reverse=True)[:25],duplicates=sorted((v for v in copies.values() if len(v)>1),reverse=True)),indent=2))
