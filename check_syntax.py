import ast
with open('app.py', 'r', encoding='utf-8') as f:
    src = f.read()
try:
    ast.parse(src)
    print('Syntax OK')
except SyntaxError as e:
    print('SYNTAX ERROR:', e)
