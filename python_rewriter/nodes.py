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

# This function is monkey-patched into the nodes, to allow recursion
def rec(self, i):
	"""This creates a matcher with the current instance as the input. It
	then applies the "thing" rule with "i" as the indentation argument.
	Finally it returns the result."""
	self.matcher = self.grammar([self])
	r = self.matcher.apply('thing', i)
	return r

# Stick it into the superclass namespace
Node.rec = rec

# Now remove the definition from our namespace
del(rec)

# The namespace should now only comtain patched AST nodes, making
# from nodes import *
# a safe operation
