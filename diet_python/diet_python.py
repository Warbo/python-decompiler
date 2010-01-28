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

def apply(arg):
	"""Runs transformations on the argument. If the argument has a trans
	method, that is run; if it is a list, apply is mapped to the list;
	if it is a "type" (None, str, etc.) then that is returned unchanged.
	"""
	if type(arg) in [type('string'), type(0), type(None)]:
		return arg
	elif type(arg) == type([0,1]):
		return map(apply, arg)
	elif type(arg) == type((0,1)):
		return tuple(map(apply, arg))
	elif 'trans' in dir(arg):
		return arg.trans()
	else:
		raise Exception("Couldn't transform "+str(arg))

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
add ::= <anything>:a ?(a.__class__ == Add) => apply(CallFunc(Getattr(a.left, '__add__'), [a.right], None, None))

# a and b becomes a.__and__(b)
# a and b and c and d becomes a.__and__(b.__and__(c.__and__(d)))
and ::= <anything>:a ?(a.__class__ == And and len(a.nodes) > 2) => apply(CallFunc(Getattr(a.nodes[0], '__and__'), apply([And(a.nodes[1:])]), None, None))
      | <anything>:a ?(a.__class__ == And) => apply(CallFunc(Getattr(a.nodes[0], '__and__'), [a.nodes[1]], None, None))

# Recurse through attribute assignment
assattr ::= <anything>:a ?(a.__class__ == AssAttr) => AssAttr(apply(a.expr), apply(a.attrname), apply(a.flags))

# Recurse through list assignment
asslist ::= <anything>:a ?(a.__class__ == AssList) => AssList(apply(a.nodes))

# Recurse through name assignment
assname ::= <anything>:a ?(a.__class__ == AssName) => AssName(apply(a.name), apply(a.flags))

# Recurse through tuple assignment
asstuple ::= <anything>:a ?(a.__class__ == AssTuple) => AssTuple(apply(a.nodes))

# Recurse through assertions
assert ::= <anything>:a ?(a.__class__ == Assert) => Assert(apply(a.test), apply(a.fail))

# Recurse through assignments
assign ::= <anything>:a ?(a.__class__ == Assign) => Assign(apply(a.nodes), apply(a.expr))

# a += b becomes a = a.__add__(b), etc.
augassign ::= <anything>:a ?(a.__class__ == AugAssign) => apply(parse(a.node.rec(0)+'='+a.node.rec(0)+a.op[0]+a.expr.rec(0)))

# Recurse through backquotes
backquote ::= <anything>:a ?(a.__class__ == Backquote) => Backquote(apply(a.expr))

# Recurse through bitwise AND
bitand ::= <anything>:a ?(a.__class__ == Bitand) => Bitand(apply(a.nodes))

# Recurse through bitwise OR
bitor ::= <anything>:a ?(a.__class__ == Bitor) => Bitor(apply(a.nodes))

# Recurse through bitwise XOR
bitxor ::= <anything>:a ?(a.__class__ == Bitxor) => Bitxor(apply(a.nodes))

# Recurse through breaks
break ::= <anything>:a ?(a.__class__ == Break) => Break()

# Recurse through function calls
callfunc ::= <anything>:a ?(a.__class__ == CallFunc) => CallFunc(apply(a.node), apply(a.args), apply(a.star_args), apply(a.dstar_args))

# Recurse through class definitions
class ::= <anything>:a ?(a.__class__ == Class) => Class(apply(a.name), apply(a.bases), apply(a.doc), apply(a.code), apply(a.decorators))

# Recurse through comparisons
compare ::= <anything>:a ?(a.__class__ == Compare) => Compare(apply(a.expr), apply(a.ops))

# Recurse through constants
const ::= <anything>:a ?(a.__class__ == Const) => Const(apply(a.value))

# Recurse through continues
continue ::= <anything>:a ?(a.__class__ == Continue) => Continue()

# Recurse through decorators
decorators ::= <anything>:a ?(a.__class__ == Decorators) => Decorators(apply(a.nodes))

# Recurse through dictionaries
dict ::= <anything>:a ?(a.__class__ == Dict) => Dict(apply(a.items))

# Recurse through operations which are not saved
discard ::= <anything>:a ?(a.__class__ == Discard) => Discard(apply(a.expr))

# a / b becomes a.__div__(b)
div ::= <anything>:a ?(a.__class__ == Div) => apply(CallFunc(Getattr(a.left, '__div__'), [a.right], None, None))

# Recurse through ellipses
ellipsis ::= <anything>:a ?(a.__class__ == Ellipsis) => Ellipsis()

# Recurse through empty nodes
emptynode ::= <anything>:a ?(a.__class__ == EmptyNode) => EmptyNode()

# Recurse through code interpretation
exec ::= <anything>:a ?(a.__class__ == Exec) => Exec(apply(a.expr), apply(a.locals), apply(a.globals))

# Recurse through expressions
expression ::= <anything>:a ?(a.__class__ == Expression) => Expression(apply(a.node))

# a // b becomes a.__floordiv__(b)
floordiv ::= <anything>:a ?(a.__class__ == FloorDiv) => apply(CallFunc(Getattr(a.left, '__floordiv__'), [a.right], None, None))

# Recurse through for loops
for ::= <anything>:a ?(a.__class__ == For) => For(apply(a.assign), apply(a.list), apply(a.body), apply(a.else_))

# Recurse through namespace injections
from ::= <anything>:a ?(a.__class__ == From) => From(apply(a.modname), apply(a.names), apply(a.level))

# Recurse through function definition
function ::= <anything>:a ?(a.__class__ == Function) => Function(apply(a.decorators), apply(a.name), apply(a.argnames), apply(a.defaults), apply(a.flags), apply(a.doc), apply(a.code))

# Recurse through generative expressions
genexpr ::= <anything>:a ?(a.__class__ == GenExpr) => GenExpr(apply(a.code))

# Recurse through generative for loops
genexprfor ::= <anything>:a ?(a.__class__ == GenExprFor) => GenExprFor(apply(a.assign), apply(a.iter), apply(a.ifs))

# Recurse through conditional generation
genexprif ::= <anything>:a ?(a.__class__ == GenExprIf) => GenExprIf(apply(a.test))

# Recurse through generative expressions
genexprinner ::= <anything>:a ?(a.__class__ == GenExprInner) => GenExprInner(apply(a.expr), apply(a.quals))

# Recurse through attribute lookups
getattr ::= <anything>:a ?(a.__class__ == Getattr) => Getattr(apply(a.expr), apply(a.attrname))

# Recurse through global definitions
global ::= <anything>:a ?(a.__class__ == Global) => Global(apply(a.names))

# Recurse through conditional code
if ::= <anything>:a ?(a.__class__ == If) => If(apply(a.tests), apply(a.else_))

# Recurse through conditional code
ifexp ::= <anything>:a ?(a.__class__ == IfExp) => IfExp(apply(a.test), apply(a.then), apply(a.else_))

# Recurse through namespace gathering
import ::= <anything>:a ?(a.__class__ == Import) => Import(apply(a.names))

# Recurse through value inversion
invert ::= <anything>:a ?(a.__class__ == Invert) => Invert(apply(a.expr))

# Recurse through keywords
keyword ::= <anything>:a ?(a.__class__ == Keyword) => Keyword(apply(a.name), apply(a.expr))

# Recurse through anonymous functions
lambda ::= <anything>:a ?(a.__class__ == Lambda) => Lambda(apply(a.argnames), apply(a.defaults), apply(a.flags), apply(a.code))

# Recurse through left bit shifts
leftshift ::= <anything>:a ?(a.__class__ == LeftShift) => LeftShift((apply(a.left), apply(a.right)))

# Recurse through lists
list ::= <anything>:a ?(a.__class__ == List) => List(apply(a.nodes))

# Recurse through list comprehensions
listcomp ::= <anything>:a ?(a.__class__ == ListComp) => ListComp(apply(a.expr), apply(a.quals))

# Recurse through list loops
listcompfor ::= <anything>:a ?(a.__class__ == ListCompFor) => ListCompFor(apply(a.assign), apply(a.list), apply(a.ifs))

# Recurse through conditional list comprehension
listcompif ::= <anything>:a ?(a.__class__ == ListCompIf) => ListCompIf(apply(a.test))

# a % b becomes a.__mod__(b)
mod ::= <anything>:a ?(a.__class__ == Mod) => apply(CallFunc(Getattr(a.left, '__mod__'), [a.right], None, None))

# Recurse through Python modules
module ::= <anything>:a ?(a.__class__ == Module) => Module(apply(a.doc), apply(a.node))

# a * b becomes a.__mul__(b)
mul ::= <anything>:a ?(a.__class__ == Mul) => apply(CallFunc(Getattr(a.left, '__mul__'), [a.right], None, None))

# Recurse through names
name ::= <anything>:a ?(a.__class__ == Name) => Name(apply(a.name))

# Recurse through negation
not ::= <anything>:a ?(a.__class__ == Not) => Not(apply(a.expr))

# Recurse through disjunction
or ::= <anything>:a ?(a.__class__ == Or) => Or(apply(a.nodes))

# Recurse through placeholders
pass ::= <anything>:a ?(a.__class__ == Pass) => Pass()

# Recurse through exponentiation
power ::= <anything>:a ?(a.__class__ == Power) => Power((apply(a.left), apply(a.right)))

# Recurse through output
print ::= <anything>:a ?(a.__class__ == Print) => Print(apply(a.nodes), apply(a.dest))

# Recurse through output
printnl ::= <anything>:a ?(a.__class__ == Printnl) => Printnl(apply(a.nodes), apply(a.dest))

# Recurse through errors
raise ::= <anything>:a ?(a.__class__ == Raise) => Raise(apply(a.expr1), apply(a.expr2), apply(a.expr3))

# Recurse through GOTOs
return ::= <anything>:a ?(a.__class__ == Return) => Return(apply(a.value))

# Recurse through right bit shifts
rightshift ::= <anything>:a ?(a.__class__ == RightShift) => RightShift((apply(a.left), apply(a.right)))

# Recurse through list slicing
slice ::= <anything>:a ?(a.__class__ == Slice) => Slice(apply(a.expr), apply(a.flags), apply(a.lower), apply(a.upper))

# Recurse through list slicing objects
sliceobj ::= <anything>:a ?(a.__class__ == Sliceobj) => Sliceobj(apply(a.nodes))

# Recurse through code blocks
stmt ::= <anything>:a ?(a.__class__ == Stmt) => Stmt(apply(a.nodes))

# a - b becomes a.__sub__(b)
sub ::= <anything>:a ?(a.__class__ == Sub) => apply(CallFunc(Getattr(a.left, '__sub__'), [a.right], None, None))

# Recurse through indexing
subscript ::= <anything>:a ?(a.__class__ == Subscript) => Subscript(apply(a.expr), apply(a.flags), apply(a.subs))

# Recurse through fallbacks
tryexcept ::= <anything>:a ?(a.__class__ == TryExcept) => TryExcept(apply(a.body), apply(a.handlers), apply(a.else_))

# Recurse through cleanups
tryfinally ::= <anything>:a ?(a.__class__ == TryFinally) => TryFinally(apply(a.body), apply(a.final))

# Recurse through immutable lists
tuple ::= <anything>:a ?(a.__class__ == Tuple) => Tuple(apply(a.nodes))

# Recurse through +ve
unaryadd ::= <anything>:a ?(a.__class__ == UnaryAdd) => UnaryAdd(apply(a.expr))

# Recurse through -ve
unarysub ::= <anything>:a ?(a.__class__ == UnarySub) => UnarySub(apply(a.expr))

# Recurse through boundless loops
while ::= <anything>:a ?(a.__class__ == While) => While(apply(a.test), apply(a.body), apply(a.else_))

# Recurse through with?
with ::= <anything>:a ?(a.__class__ == With) => With(apply(a.expr), apply(a.vars), apply(a.body))

# Recurse through Yields
yield ::= <anything>:a ?(a.__class__ == Yield) => Yield(apply(a.value))

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
