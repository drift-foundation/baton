import ast, sys

def stripped(path):
    tree = ast.parse(open(path, encoding='utf-8').read())
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:] or [ast.Pass()]
    return ast.dump(tree)

a, b = sys.argv[1], sys.argv[2]
same = stripped(a) == stripped(b)
print('AST WITH EVERY DOCSTRING STRIPPED IS IDENTICAL:', same)
sys.exit(0 if same else 1)
