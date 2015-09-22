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
from python_rewriter.base import grammar_def, parse, constants
from python_rewriter.nodes import *
from pymeta.grammar import OMeta

extra_filters = []

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
		transformed = arg.trans()
		# If we've got any extra transformations to apply then do them now
		for func in extra_filters:
			transformed = func(transformed)
		return transformed
	else:
		raise Exception("Couldn't transform "+str(arg))

def comparison_to_and(node):
	"""Turns a series of comparisons into a nested series of independent
	comparisons. The behaviour is similar to logical and, including the
	restriction that the expression on the right should not be evaluated unless
	the expression on the left is true. The difficulty is that each expression
	should only be evaluated once, if at all. Thus if we had a comparison like:
	a < b < c == d >= e < f
	We cannot rewrite this as a < b and b < c and c == d and d >= e and e < f
	since in the case that they are all true, the expressions b, c, d and e will
	all be evaluated twice. Thus we must rely on the comparison methods to
	handle these correctly, and pass the right-hand expressions as strings to be
	evaled as needed (otherwise they would be evaluated as they are passed to
	the function, which would break the restriction that they should only be
	evaluated when the expressions to their left are true).
	Thus we extend the comparison method signature with a list of expressions to
	evaluate in the case that their first one succeeds. This should be
	implemented recursively, popping the head off the list, evaluating it and
	storing the result in a temporary variable. We can then do 2 comparisons
	against the temporary variable, which eliminates the need to evaluate the
	expressions twice. The tail of the list should be passed to this comparison
	so that it can recurse until it's empty.
	a.__lt__(b, [('__lt__','c'),('__eq__','d'),('__ge__','e'),('__lt__','f')])"""
	left = node.expr
	op = {'==':'__eq__', '!=':'__ne__', '>':'__gt__', '<':'__lt__', \
		'>=':'__ge__', '<=':'__le__'}[node.ops[0][0]]
	ops = [(op[a[0]],a[1]) for a in node.ops]
	if len(ops) == 1:
		return CallFunc(Getattr(apply(node.expr), Name(ops[0][0])),[apply(ops[0][1])])
	else:
		first_op = ops.pop(0)
		from python_rewriter.base import grammar
		matcher = grammar([apply(a[1])])
		val,err = matcher.apply('thing',0)
		return CallFunc(Getattr(apply(node.expr), Name(first_op[0])), \
			[apply(first_op[1]),List([ \
				Tuple([Const(a[0]),Const(val)]) for a in ops \
			])] \
		)

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
        | <anything>:a !(sys.stdout.write('FAIL '+str(a)+' ENDFAIL'))

# a + b becomes a.__add__(b)
add ::= <anything>:a ?(a.__class__ == Add) => apply(CallFunc(Getattr(a.left, Name('__add__')), [a.right], None, None))

# Recurse through "and" keywords
and ::= <anything>:a ?(a.__class__ == And) => And(apply(a.nodes))

# Recurse through attribute assignment
assattr ::= <anything>:a ?(a.__class__ == AssAttr) => AssAttr(apply(a.expr), apply(a.attrname), apply(a.flags))

# Recurse through list assignment
asslist ::= <anything>:a ?(a.__class__ == AssList) => AssList(apply(a.nodes))

# Recurse through name assignment
# Could turn into a function if we had reified, mutable namespace. For example:
# foo = bar
# Could be turned into:
# locals().__setitem__(foo, bar)
# Except that modifying the locals() dictionary gives undefined behaviour
assname ::= <anything>:a ?(a.__class__ == AssName) => AssName(apply(a.name), apply(a.flags))

# Recurse through tuple assignment
# Could replace with a loop, but would need to ensure it behaves like an atomic
# tuple assignment
asstuple ::= <anything>:a ?(a.__class__ == AssTuple) => AssTuple(apply(a.nodes))

# Recurse through assertions
# Node type seems extraneous, but assert() can still be implemented as a
# function so no real need to change it
assert ::= <anything>:a ?(a.__class__ == Assert) => Assert(apply(a.test), apply(a.fail))

# Recurse through assignments
assign ::= <anything>:a ?(a.__class__ == Assign) => Assign(apply(a.nodes), apply(a.expr))

# a += b becomes a = a.__add__(b), etc.
augassign ::= <anything>:a ?(a.__class__ == AugAssign) !(self.ins(a.node)) <thing 0>:node !(self.ins(a.expr)) <thing 0>:expr => apply(parse(node+'='+node+a.op[0]+expr))

# `something` becomes repr(something)
backquote ::= <anything>:a ?(a.__class__ == Backquote) => apply(CallFunc(Name('repr'), [a.expr], None, None))

# a & b becomes a.__and__(b)
bitand ::= <anything>:a ?(a.__class__ == Bitand and len(a.nodes) > 2) => apply(CallFunc(Getattr(Bitand(a.nodes[:-1]), '__and__'), [a.nodes[-1]], None, None))
         | <anything>:a ?(a.__class__ == Bitand) => apply(CallFunc(Getattr(a.nodes[0], '__and__'), [a.nodes[1]], None, None))

# a | b becomes a.__or__(b)
bitor ::= <anything>:a ?(a.__class__ == Bitor and len(a.nodes) > 2) => apply(CallFunc(Getattr(Bitor(a.nodes[:-1]), '__or__'), [a.nodes[-1]], None, None))
        | <anything>:a ?(a.__class__ == Bitor) => apply(CallFunc(Getattr(a.nodes[0], '__or__'), [a.nodes[1]], None, None))

# a ^ b becomes a.__xor__(b)
bitxor ::= <anything>:a ?(a.__class__ == Bitxor and len(a.nodes) > 2) => apply(CallFunc(Getattr(Bitxor(a.nodes[:-1]), '__xor__'), [a.nodes[-1]], None, None))
         | <anything>:a ?(a.__class__ == Bitxor) => apply(CallFunc(Getattr(a.nodes[0], '__xor__'), [a.nodes[1]], None, None))

# Recurse through breaks
# Could replace this by converting programs to Continuation Passing Style
break ::= <anything>:a ?(a.__class__ == Break) => Break()

# Recurse through function calls
# Function calls are pretty much required. We could replace with __call__, but
# that would make an infinite regression to __call__.__call__.__call__..........
callfunc ::= <anything>:a ?(a.__class__ == CallFunc) => CallFunc(apply(a.node), apply(a.args), apply(a.star_args), apply(a.dstar_args))

# Recurse through class definitions
# Could replace with a call to a __new__ method
class ::= <anything>:a ?(a.__class__ == Class) => Class(apply(a.name), apply(a.bases), apply(a.doc), apply(a.code), apply(a.decorators))

# Recurse through comparisons
compare ::= <anything>:a ?(a.__class__ == Compare) => Compare(apply(a.expr), map(apply,a.ops)) #apply(comparison_to_and(a))

# Recurse through constants
# We could call the namespace here, and use its getter method to construct the
# number objects as needed.
const ::= <anything>:a ?(a.__class__ == Const) => Const(a.value)

# Recurse through continues
# Could be removed if we implemented Continuation Passing Style
continue ::= <anything>:a ?(a.__class__ == Continue) => Continue()

# Recurse through decorators
# Simple to eliminate. Do it soon!
decorators ::= <anything>:a ?(a.__class__ == Decorators) => Decorators(apply(a.nodes))

# Recurse through dictionaries
# Could use a __new__ method.
dict ::= <anything>:a ?(a.__class__ == Dict) => Dict(apply(a.items))

# Recurse through operations which are not saved
# Doesn't show up in the final code, so no need to simplify
discard ::= <anything>:a ?(a.__class__ == Discard) => Discard(apply(a.expr))

# a / b becomes a.__div__(b)
div ::= <anything>:a ?(a.__class__ == Div) => apply(CallFunc(Getattr(a.left, '__div__'), [a.right], None, None))

# Recurse through ellipses
# Global namespace call
ellipsis ::= <anything>:a ?(a.__class__ == Ellipsis) => Ellipsis()

# Recurse through empty nodes
emptynode ::= <anything>:a ?(a.__class__ == EmptyNode) => EmptyNode()

# Recurse through code interpretation
# Just a function call syntax
exec ::= <anything>:a ?(a.__class__ == Exec) => Exec(apply(a.expr), apply(a.locals), apply(a.globals))

# Recurse through expressions
# Once again, function call syntax so no need to change
expression ::= <anything>:a ?(a.__class__ == Expression) => Expression(apply(a.node))

# a // b becomes a.__floordiv__(b)
floordiv ::= <anything>:a ?(a.__class__ == FloorDiv) => apply(CallFunc(Getattr(a.left, '__floordiv__'), [a.right], None, None))

# Recurse through for loops
# Could maybe do something with map, or __iter__?
for ::= <anything>:a ?(a.__class__ == For) => For(apply(a.assign), apply(a.list), apply(a.body), apply(a.else_))

# Recurse through namespace injections
# Would be nice to give the local namespace a method to do this, but alas it
# would break CPython semantics
from ::= <anything>:a ?(a.__class__ == From) => From(apply(a.modname), apply(a.names), apply(a.level))

# Recurse through function definition
# Could use a __new__, but would need to add meta info like code, arguments, etc.
function ::= <anything>:a ?(a.__class__ == Function) => Function(apply(a.decorators), apply(a.name), apply(a.argnames), apply(a.defaults), apply(a.flags), apply(a.doc), apply(a.code))

# Recurse through generative expressions
# Should be some way to __new__ this
genexpr ::= <anything>:a ?(a.__class__ == GenExpr) => GenExpr(apply(a.code))

# Recurse through generative for loops
# Ditto
genexprfor ::= <anything>:a ?(a.__class__ == GenExprFor) => GenExprFor(apply(a.assign), apply(a.iter), apply(a.ifs))

# Recurse through conditional generation
# Ditto
genexprif ::= <anything>:a ?(a.__class__ == GenExprIf) => GenExprIf(apply(a.test))

# Recurse through generative expressions
# Ditto
genexprinner ::= <anything>:a ?(a.__class__ == GenExprInner) => GenExprInner(apply(a.expr), apply(a.quals))

# Recurse through attribute lookups
# Oops, infinite recursion!
#getattr ::= <anything>:a ?(a.__class__ == Getattr) => Callfunc(Getattr(a.expr, Name('__getattribute__')), a.attrname)
# Could maybe use objects' namespaces?
getattr ::= <anything>:a ?(a.__class__ == Getattr) => Getattr(apply(a.expr), apply(a.attrname))

# Recurse through global definitions
# Could use globals()
global ::= <anything>:a ?(a.__class__ == Global) => Global(apply(a.names))

# Recurse through conditional code
# Not possible to change without altering Python's True and False object APIs
if ::= <anything>:a ?(a.__class__ == If) => If(apply(a.tests), apply(a.else_))

# Recurse through conditional code
ifexp ::= <anything>:a ?(a.__class__ == IfExp) => IfExp(apply(a.test), apply(a.then), apply(a.else_))

# Recurse through namespace gathering
# Would be nice to change, since it's a keyword, but would require a namespace
# method
import ::= <anything>:a ?(a.__class__ == Import) => Import(apply(a.names))

# Recurse through value inversion
invert ::= <anything>:a ?(a.__class__ == Invert) => Invert(apply(a.expr))

# Recurse through keywords
# Could perhaps use dictionaries as **varargs
keyword ::= <anything>:a ?(a.__class__ == Keyword) => Keyword(apply(a.name), apply(a.expr))

# Recurse through anonymous functions
# Could use __new__ but would require adding meta-info once again
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
# No actual code, no no need to change
module ::= <anything>:a ?(a.__class__ == Module) => a#Module(apply(a.doc), apply(a.node))

# a * b becomes a.__mul__(b)
mul ::= <anything>:a ?(a.__class__ == Mul) => apply(CallFunc(Getattr(a.left, '__mul__'), [a.right], None, None))

# Recurse through names
# Maybe make it a namespace lookup message
name ::= <anything>:a ?(a.__class__ == Name) => Name(apply(a.name))

# Recurse through negation
not ::= <anything>:a ?(a.__class__ == Not) => Not(apply(a.expr))

# Recurse through disjunction
or ::= <anything>:a ?(a.__class__ == Or) => Or(apply(a.nodes))

# Recurse through placeholders
# Hopefully not needed with continuation passing style
pass ::= <anything>:a ?(a.__class__ == Pass) => Pass()

# a**b becomes a.__pow__(b)
power ::= <anything>:a ?(a.__class__ == Power) => apply(CallFunc(Getattr(a.left, '__pow__'), [a.right], None, None))

# Recurse through output
# TODO: At a future point, when we implement namespaces and things, we
# should try to replace this with a function call "print()", however at
# the moment that would break our compatibility with regular Python.
# Firstly the 'functiony' syntax above can only call the equivalent of
# "print 'xyz'" whilst we need it to follow the "print 'xyz',"
# behaviour (ie. don't put a new line unless we've put one in the
# argument). We can call "print('xyz')," but then we would need to
# handle the comma on top of our generic function handling code, which
# doesn't make anything simpler so there's no point. Thus we need our
# own definition for print() which doesn't add the newline. This is
# difficult since "print('xyz')" is not treated by Python as a function
# call (even though we'd like to implement it with one), but instead as
# "print 'xyz'", so there's no existing function we can just override.
# As a consequence, "print" can be (and is) treated as a keyword in
# Python, so even if we did define a "print()" function, the name would
# not be allowed. Once namespace support is added then we can give the
# function a unique, non-conflicting, non-keyword name, so that we can
# replace these print calls with, for example "print_('xyz')" (and
# if this conflicts with something in the code then simply add numbers
# to the end until it doesn't), but then this causes issues since this
# might be overridden in local namespaces. Whilst an interesting feature
# this would still be an extension to Python, which breaks Diet Python's
# purpose, so we'd need to make sure it can never be overridden from
# within the code we are translating.
# Since implementing this depends upon the way we do namespaces I'll
# leave it at that for now.
print ::= <anything>:a ?(a.__class__ == Print) => Print(apply(a.nodes), apply(a.dest))

# print xyz becomes print xyz+newline,
printnl ::= <anything>:a ?(a.__class__ == Printnl) => apply(Print(a.nodes+[Const(\"""\n\""")], a.dest))

# Recurse through errors
# Uses a function-style syntax anyway
raise ::= <anything>:a ?(a.__class__ == Raise) => Raise(apply(a.expr1), apply(a.expr2), apply(a.expr3))

# Recurse through GOTOs
# Can be done away with in continuation passing style
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

# a[b] becomes a.__getitem__(b)
# TODO: Check a.flags for deletion (__delitem__) and things
subscript ::= <anything>:a ?(a.__class__ == Subscript) => apply(CallFunc(Getattr(a.expr, Name('__getitem__')), a.subs))

# Recurse through fallbacks
# Continuation Passing Style should be able to overcome this
tryexcept ::= <anything>:a ?(a.__class__ == TryExcept) => TryExcept(apply(a.body), apply(a.handlers), apply(a.else_))

# Recurse through cleanups
# Ditto
tryfinally ::= <anything>:a ?(a.__class__ == TryFinally) => TryFinally(apply(a.body), apply(a.final))

# Recurse through immutable lists
# A __new__ might be in order
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
#from python_rewriter.base import grammar
import sys
transforms = OMeta.makeGrammar(strip_comments(tree_transform), globals())

# Patch the grammar for recursion
def ins(self, val):
	"""This is a very dangerous function! We monkey-patch PyMeta grammars with
	this so that we can insert an arbitrary value as the next input. This allows
	us to recurse without having to	instantiate another matcher (we effectively
	use the existing input as a stack). Beware of leaving cruft behind on the
	input!"""
	# Insert the value
	self.input.data.insert(self.input.position, val)
	# Throw away any cached input
	self.input.tl = None
	self.input.memo = {}
	# Ensure success, if needed
	return True

transforms.ins = ins


Node.tree_transform = tree_transform
Node.transforms = transforms

def trans(self):
	"""This creates a tree transformer with the current instance as
	the input. It then applies the "thing" rule. Finally it returns
	the result."""
	# Uncomment to see exactly which bits are causing errors
	#print str(self)
	
	self.transformer = self.transforms([self])
	
	r,err = self.transformer.apply('thing')

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
		diet_tree = apply(tree)
		#print str(tree)
		#print str(diet_tree)
		
		# Generate (Diet) Python code to match the transformed tree
		from python_rewriter.base import grammar
		matcher = grammar([diet_tree])
		diet_code,err = matcher.apply('thing', initial_indent)
		
		#print str(tree)
		#print
		#print str(diet_tree)
		#print
		
		return diet_code
		
	except Exception, e:
		sys.stderr.write(str(e)+'\n')
		sys.stderr.write('Unable to translate.\n')
		sys.exit(1)

if __name__ == '__main__':
	# TODO: Allow passing the initial indentation
	if len(sys.argv) > 1:
		args = sys.argv
		if '-in' in args:
			in_file = args[args.index('-in')+1]
		else:
			print "Usage: diet_python.py -in input_path [-out output_path] [-extra foo]"
			sys.exit(1)
		if '-out' in args:
			out_file = args[args.index('-out')+1]
		else:
			out_file=None
		# "-extra foo" will include the transformations from foo.py
		while '-extra' in args:
			# Grab the filename
			i = args.index('-extra')
			n = args[i+1]
			# Import it
			try:
				exec('import '+n)
				# Fill its namespace with our node classes
				for obj in dir():
					if obj[0].isupper():
						exec(n+'.'+obj+' = '+obj)
				extra_filters.extend(eval(n+'.extra_filters'))
			except:
				print 'Failed to import '+n
				sys.exit(1)
			# Remove it from the arguments
			args.pop(i)
			args.pop(i)
		# Now run the translation
		code = translate(in_file)
		if out_file is None:
			print code
		else:
			o = open(out_file, 'w')
			o.write(code)
			o.close()
	else:
		print "Usage: diet_python.py -in input_path [-out output_path] [-extra foo]"
