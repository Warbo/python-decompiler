"""
Every AST node class is injected into this namespace.

Useful for importing all nodes at once.
"""

import compiler

# Go through everything in the compiler.ast module
for name in dir(compiler.ast):
	# Instantiate whatever we've come across
	cls = eval('compiler.ast.'+name)
	
	# If we've found a type of Node then import it
	try:
		if issubclass(cls, compiler.ast.Node):
			exec('from compiler.ast import '+name)
	# Otherwise forget it and move on
	except TypeError:
		pass

# Get rid of our temporary variable, to keep this namespace clean
del(cls)

# The namespace should now only contain patched AST nodes, making
# from nodes import *
# a safe operation
