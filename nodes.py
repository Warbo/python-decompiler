"""
Every AST node class is injected into this namespace.

Useful for importing all nodes at once.
"""

import compiler

for name in dir(compiler.ast):
	cls = eval('compiler.ast.'+name)
	try:
		if issubclass(cls, compiler.ast.Node):
			exec('from compiler.ast import '+name) 
	except TypeError:
		pass

del(cls)
