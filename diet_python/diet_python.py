"""This module implements the language "Diet Python", which is a Python
dialect with no syntactic sugar. In fact, it aims to use the smallest
amount of syntax possible whilst remaining compatible with Python.

For example, in regular Python the expression "1+x" will do the same
thing as "1.__add__(x)". Thus in Diet Python we can get rid of the +
syntax, since our function calling syntax suffices. Whilst it may be
more pleasant to use the former syntax, such things make language
translation and automatic introspection more difficult, thus Diet Python
does not have them.

This contains a translator from regular Python to Diet Python, using
PyMeta (a Python implementation of the OMeta pattern matching system)"""

try:
	import psyco
	psyco.full()
except:
	pass

import os
import sys
from python_rewriter.base import grammar_def, strip_comments, parse, constants
from python_rewriter.nodes import *
from pymeta.grammar import OMeta

# Diet Python is implemented by transforming the Abstract Syntax
# Tree. Here we define the tree transformations we wish to make, using
# PyMeta.

tree_transform = """
# "thing" matches anything, applying transforms to those which have them
thing ::= <add>
        | <callfunc>
        | <const>
        | <discard>
        | <div>
        | <getattr>
        | <module>
        | <mul>
        | <name>
        | <statement>
        | <sub>

# a + b becomes a.__add__(b)
add ::= <anything>:a ?(a.__class__ == Add) => CallFunc(Getattr(a.left, '__add__'), [a.right], None, None).trans()

# Recurse through function calls
callfunc ::= <anything>:a ?(a.__class__ == CallFunc and a.star_args is None and a.dstar_args is None) => CallFunc(a.node.trans(), [r.trans() for r in a.args])
           | <anything>:a ?(a.__class__ == CallFunc and a.star_args is None and a.dstar_args is not None) => CallFunc(a.node.trans(), [r.trans() for r in a.args], None, a.dstar_args.trans())
           | <anything>:a ?(a.__class__ == CallFunc and a.star_args is not None and a.dstar_args is None) => CallFunc(a.node.trans(), [r.trans() for r in a.args], a.star_args.trans())
           | <anything>:a ?(a.__class__ == CallFunc and a.star_args is not None and a.dstar_args is not None) => CallFunc(a.node.trans(), [r.trans() for r in a.args], a.star_args.trans(), a.dstar_args.trans())

# Recurse through constants
const ::= <anything>:a ?(a.__class__ == Const) => Const(a.value)

# Recurse through operations which are not saved
discard ::= <anything>:a ?(a.__class__ == Discard) => Discard(a.expr.trans())

# a / b becomes a.__div__(b)
div ::= <anything>:a ?(a.__class__ == Div) => CallFunc(Getattr(a.left, '__div__'), [a.right], None, None).trans()

# Recurse through attribute lookups
getattr ::= <anything>:a ?(a.__class__ == Getattr) => Getattr(a.expr.trans(), a.attrname)

# Recurse through Python modules
module ::= <anything>:a ?(a.__class__ == Module) => Module(a.doc, a.node.trans())

# a * b becomes a.__mul__(b)
mul ::= <anything>:a ?(a.__class__ == Mul) => CallFunc(Getattr(a.left, '__mul__'), [a.right], None, None).trans()

# Recurse through names
name ::= <anything>:a ?(a.__class__ == Name) => Name(a.name)

# Recurse through code blocks
statement ::= <anything>:a ?(a.__class__ == Stmt) => Stmt([n.trans() for n in a.nodes])

# a - b becomes a.__sub__(b)
sub ::= <anything>:a ?(a.__class__ == Sub) => CallFunc(Getattr(a.left, '__sub__'), [a.right], None, None).trans()

"""

# The definitions below try to write straight to code, so they need to
# be rewritten as tree transforms like the above
"""# assert things becomes assert(things)
assert :i ::= <anything>:a ?(a.__class__ == Assert) ?(a.fail is None) => 'assert('+a.test.rec(i)+')'
            | <anything>:a ?(a.__class__ == Assert) ?(not a.fail is None) => 'assert('+a.test.rec(i)+', '+a.fail.rec(i)+')'

# a += b becomes a = a.__add__(b)
# To do this we put the left = left then transform the operation and append it to the end
augassign :i ::= <anything>:a ?(a.__class__ == AugAssign) => a.node.rec(i)+' = '+eval('parse("'+a.node.rec(i)+a.op[:-1]+a.expr.rec(i)+'").rec('+str(i)+').strip()')

# Ideally we only want to call functions as attributes of named objects,
# so we split apart chained function calls and assign each to a
# temporary variable before we continue
callfunc :i ::= <anything>:a ?(a.__class__ == CallFunc)

# a / b becomes a.__div__(b)
div :i ::= <anything>:a ?(a.__class__ == Div) => a.left.rec(i)+'.__div__('+a.right.rec(i)+')'


# Function definition involves more than it appears at first glance. We
# need to:
# * make a callable object (ie. the function)
#
# * bind the function's docstring to func_doc and __doc__ (even if it's
#    None)
# * bind the function's name to func_name and __name__
# * bind the name of the module we're in to __module__
# * bind a tuple of default argument values to func_defaults
# * compile the function's code and bind it to func_code
# * bind the namespace of __module__ to func_globals
# * bind a dictionary of the function's namespace to func_dict
# * bind a tuple of the function's free variables to func_closure
function :i ::= <anything>:a ?(a.__class__ == Function) => function_writer(a, i)

# a * b becomes a.__mul__(b)
mul :i ::= <anything>:a ?(a.__class__ == Mul) => a.left.rec(i)+'.__mul__('+a.right.rec(i)+')'

# a - b becomes a.__sub__(b)
sub :i ::= <anything>:a ?(a.__class__ == Sub) => a.left.rec(i)+'.__sub__('+a.right.rec(i)+')'

"""

# Now we embed the transformations in every AST node, so that they can
# apply them recursively to their children
transforms = OMeta.makeGrammar(strip_comments(tree_transform), globals())
Node.tree_transform = tree_transform
Node.transforms = transforms

def trans(self):
	"""This creates a tree transformer with the current instance as
	the input. It then applies the "thing" rule. Finally it returns
	the result."""
	# Uncomment to see exactly which bits are causing errors
	#print str(self)
	
	self.transformer = self.transforms([self])
	
	r = self.transformer.apply('thing')
	
	return r
	
Node.trans = trans

def translate(path_or_text, initial_indent=0):
	"""This performs the translation from Python to Diet Python. It
	takes in Python code (assuming the string to be a file path, falling
	back to treating it as Python code if it is not a valid path) and
	emits Diet Python code."""
	# See if the given string is a valid path
	if os.path.exists(path_or_text):
		# If so then open it and read the file contents into in_text
		infile = open(path_or_text, 'r')
		in_text = '\n'.join([line for line in infile.readlines()])
		infile.close()
	# Otherwise take the string contents to be in_text
	else:
		in_text = path_or_text
		
	# Wrap in try/except to give understandable error messages (PyMeta's
	# are full of obscure implementation details)
	try:
		# Get an Abstract Syntax Tree for the contents of in_text
		tree = parse(in_text)
		
		# Transform the Python AST into a Diet Python AST
		diet_tree = tree.trans()
		
		#print str(tree)
		#print str(diet_tree)
		
		# Generate (Diet) Python code to match the transformed tree
		diet_code = diet_tree.rec(initial_indent)
		
		return diet_code
		
	except Exception, e:
		sys.stderr.write(str(e)+'\n')
		sys.stderr.write('Unable to translate.\n')
		sys.exit(1)

if __name__ == '__main__':
	# TODO: Allow passing the initial indentation
	# TODO: Allow specifying an output file
	if len(sys.argv) == 2:
		print translate(sys.argv[1])
	else:
		print "Usage: diet_python.py input_path_or_raw_python_code"
