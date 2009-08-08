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

def rec(self, i):
	"""This creates a matcher with the current instance as the input. It
	then applies the "thing" rule with "i" as the indentation argument.
	Finally it returns the result."""
	try:
		self.matcher = self.grammar([self])
	except Exception, e:
		print 'OOPS {'
		print 'Exception: ' + str(e)
		print 'Attempting: '+str(self.__class__)
		print '}'
		return ''
	try:
		r = self.matcher.apply('thing', i)
	except Exception, e:
		print 'ERR {'
		print 'Exception: '+str(e)
		print 'Attempting: '+str(self.__class__)
		print '}'
		return ''
	return r
	
Node.rec = rec

del(rec)
