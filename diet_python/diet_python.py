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
        | <and>
        | <assattr>
        | <asslist>
        | <assname>
        | <asstuple>
        | <assert>
        | <assign>
        | <augassign>
        | <backquote>
        | <bitand>
        | <bitor>
        | <bitxor>
        | <break>
        | <callfunc>
        | <class>
        | <compare>
        | <const>
        | <continue>
        | <decorators>
        | <dict>
        | <discard>
        | <div>
        | <ellipsis>
        | <emptynode>
        | <exec>
        | <expression>
        | <floordiv>
        | <for>
        | <from>
        | <function>
        | <genexpr>
        | <genexprfor>
        | <genexprif>
        | <genexprinner>
        | <getattr>
        | <global>
        | <if>
        | <ifexp>
        | <import>
        | <invert>
        | <keyword>
        | <lambda>
        | <leftshift>
        | <list>
        | <listcomp>
        | <listcompfor>
        | <listcompif>
        | <mod>
        | <module>
        | <mul>
        | <name>
        | <not>
        | <or>
        | <pass>
        | <power>
        | <print>
        | <printnl>
        | <raise>
        | <return>
        | <rightshift>
        | <slice>
        | <sliceobj>
        | <stmt>
        | <sub>
        | <subscript>
        | <tryexcept>
        | <tryfinally>
        | <tuple>
        | <unaryadd>
        | <unarysub>
        | <while>
        | <with>
        | <yield>

# a + b becomes a.__add__(b)
add ::= <anything>:a ?(a.__class__ == Add) => CallFunc(Getattr(a.left, '__add__'), [a.right], None, None).trans()

# a and b becomes a.__and__(b)
# a and b and c and d becomes a.__and__(b.__and__(c.__and__(d)))
and ::= <anything>:a ?(a.__class__ == And and len(a.nodes) > 2) => CallFunc(Getattr(a.nodes[0], '__and__'), [And(a.nodes[1:]).trans()], None, None).trans()
      | <anything>:a ?(a.__class__ == And) => CallFunc(Getattr(a.nodes[0], '__and__'), [a.nodes[1]], None, None).trans()

# Recurse through attribute assignment
assattr ::= <anything>:a ?(a.__class__ == AssAttr) => AssAttr(a.expr.trans(), a.attrname, a.flags)

asslist ::= <anything>:a ?(a.__class__ == AssList) => AssList([n.trans() for n in a.nodes])

assname ::= <anything>:a ?(a.__class__ == AssName) => AssName(a.name, a.flags)

asstuple ::= <anything>:a ?(a.__class__ == AssTuple) => AssTuple([n.trans() for n in a.nodes])

assert ::= <anything>:a ?(a.__class__ == Assert) => Assert(a.test.trans(), a.fail.trans())

assign ::= <anything>:a ?(a.__class__ == Assign) => Assign([n.trans() for n in a.nodes], a.expr.trans())

augassign ::= <anything>:a ?(a.__class__ == AugAssign) => 

backquote ::= <anything>:a ?(a.__class__ == Backquote) => 

bitand ::= <anything>:a ?(a.__class__ == Bitand) => 

bitor ::= <anything>:a ?(a.__class__ == Bitor) => 

bitxor ::= <anything>:a ?(a.__class__ == Bitxor) => 

break ::= <anything>:a ?(a.__class__ == Break) => 

# Recurse through function calls
callfunc ::= <anything>:a ?(a.__class__ == CallFunc and a.star_args is None and a.dstar_args is None) => CallFunc(a.node.trans(), [r.trans() for r in a.args])
           | <anything>:a ?(a.__class__ == CallFunc and a.star_args is None and a.dstar_args is not None) => CallFunc(a.node.trans(), [r.trans() for r in a.args], None, a.dstar_args.trans())
           | <anything>:a ?(a.__class__ == CallFunc and a.star_args is not None and a.dstar_args is None) => CallFunc(a.node.trans(), [r.trans() for r in a.args], a.star_args.trans())
           | <anything>:a ?(a.__class__ == CallFunc and a.star_args is not None and a.dstar_args is not None) => CallFunc(a.node.trans(), [r.trans() for r in a.args], a.star_args.trans(), a.dstar_args.trans())

class ::= <anything>:a ?(a.__class__ == Class) => Class()

compare ::= <anything>:a ?(a.__class__ == Compare) => Compare()

# Recurse through constants
const ::= <anything>:a ?(a.__class__ == Const) => Const(a.value)

continue ::= <anything>:a ?(a.__class__ == Continue) => Continue()

decorators ::= <anything>:a ?(a.__class__ == Decorators) => Decorators()

dict ::= <anything>:a ?(a.__class__ == Dict) => Dict()

# Recurse through operations which are not saved
discard ::= <anything>:a ?(a.__class__ == Discard) => Discard(a.expr.trans())

# a / b becomes a.__div__(b)
div ::= <anything>:a ?(a.__class__ == Div) => CallFunc(Getattr(a.left, '__div__'), [a.right], None, None).trans()

ellipsis ::= <anything>:a ?(a.__class__ == Ellipsis) => Ellipsis()

# FIXME: Should this exist?
emptynode ::= <anything>:a ?(a.__class__ == EmptyNode) => EmptyNode()

exec ::= <anything>:a ?(a.__class__ == Exec) => Exec()

expression ::= <anything>:a ?(a.__class__ == Expression) => Expression()

# a // b becomes a.__floordiv__(b)
floordiv ::= <anything>:a ?(a.__class__ == FloorDiv) => CallFunc(Getattr(a.left, '__floordiv__'), [a.right], None, None).trans()

for ::= <anything>:a ?(a.__class__ == For) => For()

from ::= <anything>:a ?(a.__class__ == From) => From()

function ::= <anything>:a ?(a.__class__ == Function) => Function()

genexpr ::= <anything>:a ?(a.__class__ == GenExpr) => GenExpr()

genexprfor ::= <anything>:a ?(a.__class__ == GenExprFor) => GenExprFor()

genexprif ::= <anything>:a ?(a.__class__ == GenExprIf) => GenExprIf()

genexprinner ::= <anything>:a ?(a.__class__ == GenExprInner) => GenExprInner()

# Recurse through attribute lookups
getattr ::= <anything>:a ?(a.__class__ == Getattr) => Getattr(a.expr.trans(), a.attrname)

global ::= <anything>:a ?(a.__class__ == Global) => Global()

if ::= <anything>:a ?(a.__class__ == If) => If()

ifexp ::= <anything>:a ?(a.__class__ == IfExp) => IfExp()

import ::= <anything>:a ?(a.__class__ == Import) => Import()

invert ::= <anything>:a ?(a.__class__ == Invert) => Invert()

keyword ::= <anything>:a ?(a.__class__ == Keyword) => Keyword()

lambda ::= <anything>:a ?(a.__class__ == Lambda) => Lambda()

leftshift ::= <anything>:a ?(a.__class__ == LeftShift) => LeftShift()

list ::= <anything>:a ?(a.__class__ == List) => List()

listcomp ::= <anything>:a ?(a.__class__ == ListComp) => ListComp()

listcompfor ::= <anything>:a ?(a.__class__ == ListCompFor) => ListCompFor()

listcompif ::= <anything>:a ?(a.__class__ == ListCompIf) => ListCompIf()

# a % b becomes a.__mod__(b)
mod ::= <anything>:a ?(a.__class__ == Mod) => CallFunc(Getattr(a.left, '__mod__'), [a.right], None, None).trans()

# Recurse through Python modules
module ::= <anything>:a ?(a.__class__ == Module) => Module(a.doc, a.node.trans())

# a * b becomes a.__mul__(b)
mul ::= <anything>:a ?(a.__class__ == Mul) => CallFunc(Getattr(a.left, '__mul__'), [a.right], None, None).trans()

# Recurse through names
name ::= <anything>:a ?(a.__class__ == Name) => Name(a.name)

# 
not ::= <anything>:a ?(a.__class__ == Not) => Not()

or ::= <anything>:a ?(a.__class__ == Or) => Or()

pass ::= <anything>:a ?(a.__class__ == Pass) => Pass()

power ::= <anything>:a ?(a.__class__ == Power) => Power()

print ::= <anything>:a ?(a.__class__ == Print) => Print()

printnl ::= <anything>:a ?(a.__class__ == Printnl) => Printnl()

raise ::= <anything>:a ?(a.__class__ == Raise) => Raise()

return ::= <anything>:a ?(a.__class__ == Return) => Return()

rightshift ::= <anything>:a ?(a.__class__ == RightShift) => RightShift()

slice ::= <anything>:a ?(a.__class__ == Slice) => Slice()

sliceobj ::= <anything>:a ?(a.__class__ == Sliceobj) => Sliceobj()

# Recurse through code blocks
stmt ::= <anything>:a ?(a.__class__ == Stmt) => Stmt([n.trans() for n in a.nodes])

# a - b becomes a.__sub__(b)
sub ::= <anything>:a ?(a.__class__ == Sub) => CallFunc(Getattr(a.left, '__sub__'), [a.right], None, None).trans()

subscript ::= <anything>:a ?(a.__class__ == Subscript) => Subscript()

tryexcept ::= <anything>:a ?(a.__class__ == TryExcept) => TryExcept()

tryfinally ::= <anything>:a ?(a.__class__ == TryFinally) => TryFinally()

tuple ::= <anything>:a ?(a.__class__ == Tuple) => Tuple()

unaryadd ::= <anything>:a ?(a.__class__ == UnaryAdd) => UnaryAdd()

unarysub ::= <anything>:a ?(a.__class__ == UnarySub) => UnarySub()

while ::= <anything>:a ?(a.__class__ == While) => While()

with ::= <anything>:a ?(a.__class__ == With) => With()

# Recurse through Yields
yield ::= <anything>:a ?(a.__class__ == Yield) => Yield(a.value.trans())

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
	print str(self)
	
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
		
		print str(tree)
		print
		print str(diet_tree)
		print
		
		print diet_code
		
	except Exception, e:
		sys.stderr.write(str(e)+'\n')
		sys.stderr.write('Unable to translate.\n')
		sys.exit(1)

if __name__ == '__main__':
	# TODO: Allow passing the initial indentation
	# TODO: Allow specifying an output file
	if len(sys.argv) == 2:
		translate(sys.argv[1])
	else:
		print "Usage: diet_python.py input_path_or_raw_python_code"
