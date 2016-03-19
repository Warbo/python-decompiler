"""This module is used to translate and transform Python source code.

The object "grammar" converts from a Syntax Tree (eg. created by Python's
compiler module's "parse" functions) into Python code. This is done by calling
"foo = grammar(<starting node>)" then running foo.apply('python', 0).

Your own arbitrary transformations can be added to the grammar, which is then
applied recursively down the tree."""

from sys import version_info as v, argv, exit
import compiler
import compiler.ast as ast
from pymeta.grammar import OMeta as OM
from nodes import *
try:
	import psyco
	psyco.full()
except:
	pass

# Couldn't think of a simple way to do these inside the grammar, so put
# them in functions which are accessible from inside the grammar
def add_semis(nodes):
	for i,n in enumerate(nodes):
		if n.__class__ == Discard and n.expr.__class__ == Const and \
			n.expr.value is None:
			nodes[i-1].semi = True
	return nodes

def semi(node):
	if node.semi:
		return ';'
	else:
		return ''

def import_match(names):
	"""Adds "as" clauses to any import statements which supply them."""
	r = []
	for name in names:
		if name[1] is None:
			r.append(name[0])
		else:
			r.append(name[0]+' as '+name[1])
	return r


def tuple_args(list):
	"""Turns tuples such as ('a', 'b', ('c', 'd')) into strings such as
	'(a, b, (c, d))'"""
	to_return = []
	for arg in list:
		if type(arg) == str:
			to_return.append(arg)
		elif type(arg) == tuple:
			to_return.append('('+', '.join(tuple_args(arg))+')')
	return to_return

def is_del(thing):
	"""Returns boolean whether this is a deletion node."""
	try:
		return thing.flags == 'OP_DELETE'
	except AttributeError:
		try:
			return all(map(is_del, thing.nodes))
		except AttributeError:
			pass
	return False

def pick_quotes(string):
	"""Picks some appropriate quotes to wrap the given string in."""
	return repr(string)

def set_defaults(argnames, defaults):
	"""Given a list argnames and a list defaults, this will return a
	string of the relevant argnames set to the defaults. In other words,
	argnames of [a, b, c, d] and defaults of [5, x] will give a string
	"a, b, c=5, d=x", suitable for defining a function with."""
	# For no arguments this is trivial
	if len(argnames) == 0:
		return ''
	# For no defaults we don't need to assign anything
	if len(defaults) == 0:
		return ','.join(argnames)
	# If every argument has a default then we can just iterate through
	if len(argnames) == len(defaults):
		to_return = []
		for x in range(0, len(argnames)):
			to_return.append(str(argnames[x])+'='+str(defaults[x]))
		return ','.join(to_return)
	# If we've reached here then we have arguments and defaults of
	# differing number

	# First split apart those args with defaults from those without
	# (defaults ONLY occur at the end of the argument list)
	with_defs = argnames[-1*(len(defaults)):]
	without_defs = argnames[:-1*(len(defaults))]

	# Now create the contents of our eventual return string
	# Start with the arguments without defaults, since they're easy
	to_return = without_defs
	# Now add those with defaults, along with their defaults
	for x in range(0, len(defaults)):
		to_return.append(with_defs[x]+'='+defaults[x])
	# And we're done
	return ','.join(to_return)

def make_list(foo):
	"""Returns the argument if it has a length, otherwise returns an empty list.
	"""
	try:
		return list(foo)
	except:
		return []

# This is the grammar, defined in OMeta, which does our translation
grammar_def = """#
# "python" is used to output Python code from an AST node. The number given
# to the "thing"  (usually 0) is the number of tabs to use as the initial
# indentation.
python :i ::= <thing i>:t => t

# A "thing" matches an AST node or a constant (constants can be supplied
# through the global "constants")
thing :i ::= <node i>:t => ''.join(t)
          | <anything>:a ?(type(a) in constants) => a

# A "node" is an AST node. The handling of each is deferred to the
# appropriate rule for that node type. Note that the order is mostly arbitrary,
# since the definitions don't overlap, except for "delete" which must occur
# first. The rest are alphabetical, for lack of a better order.
node :i ::= <delete i>:d => d
          | <name i>:n => n
          | <getattr i>:g => g
          | <callfunc i>:c => c
          | <const i>:c => c
          | <stmt i>:s => s
          | <assign i>:a => a
          | <assname i>:a => a
          | <discard i>:d => d
          | <if i>:g => g
          | <function i>:f => f
          | <compare i>:c => c
          | <subscript i>:s => s
          | <assattr i>:a => a
          | <return i>:r => r
          | <keyword i>:k => k
          | <tuple i>:t => t
          | <add i>:a => a
          | <from i>:f => f
          | <list i>:l => l
          | <printnl i>:p => p
          | <for i>:f => f
          | <not i>:n => n
          | <mod i>:m => m
          | <class i>:c => c
          | <tryexcept i>:t => t
          | <unarysub i>:u => u
          | <import i>:g => g
          | <and i>:a => a
          | <dict i>:d => d
          | <augassign i>:a => a
          | <asstuple i>:a => a
          | <raise i>:r => r
          | <slice i>:s => s
          | <sub i>:s => s
          | <module i>:m => m
          | <or i>:o => o
          | <pass i>:p => p
          | <mul i>:m => m
          | <assert i>:a => a
          | <listcompfor i>:l => l
          | <listcomp i>:l => l
          | <div i>:d => d
          | <tryfinally i>:t => t
          | <break i>:b => b
          | <lambda i>:l => l
          | <bitor i>:b => b
          | <continue i>:c => c
          | <while i>:w => w
          | <backquote i>:b => b
          | <decorators i>:d => d
          | <global i>:g => g
          | <listcompif i>:l => l
          | <power i>:p => p
          | <genexpr i>:g => g
          | <genexprfor i>:g => g
          | <genexprinner i>:g => g
          | <floordiv i>:e => e
          | <asslist i>:a => a
          | <bitand i>:b => b
          | <yield i>:y => y
          | <exec i>:e => e
          | <ifexp i>:g => g
          | <print i>:p => p
          | <with i>:w => w
          | <unaryadd i>:u => u
          | <genexprif i>:g => g
          | <rightshift i>:r => r
          | <leftshift i>:l => l
          | <bitxor i>:b => b
          | <sliceobj i>:s => s
          | <invert i>:g => g
          | <ellipsis i>:e => e
          | <emptynode i>:e => e
          | <expression i>:e => e
## UNCOMMENT THE FOLLOWING TO MAKE DEBUGGING EASIER
#		  | <anything>:a => 'FAIL'+str(a)

# Add is addition, with a left and a right
# We want the left and right, joined by a plus sign '+'
add :i ::= <anything>:a ?(a.__class__ == Add) !(self.ins(a.left)) !(self.ins(a.right)) <thing i>:right <thing i>:left => '(('+str(left)+') + ('+str(right)+'))'

# Matches a chain of logical AND operations on booleans
# NOTE: We must add a.nodes on to the stack in reverse order, then pop them back
# in the right order with n_things
and :i ::= <anything>:a ?(a.__class__ == And) <none_list a.nodes>:nodelist !([self.ins(n) for n in nodelist[::-1]]) <n_things len(nodelist) i>:ns => '('+') and ('.join(ns)+')'

# Matches the binding of an object to a member name of another object
assattr :i ::= <anything>:a ?(a.__class__ == AssAttr) !(self.ins(a.expr)) <thing i>:e => e+'.'+a.attrname

# Matches the binding of a list of items
# NOTE: We must add a.nodes on to the stack in reverse order, then pop them back
# in the right order with n_things
asslist :i ::= <anything>:a ?(a.__class__ == AssList) <none_list a.nodes>:nodelist !([self.ins(n) for n in nodelist[::-1]]) <n_things len(nodelist) i>:ns => '[' + ', '.join(ns) + ']'

# AssName assigns to a variable name
# We want the variable name
assname :i ::= <anything>:a ?(a.__class__ == AssName) => a.name

# Matches the assignment of multiple names to multiple objects
# NOTE: We must add a.nodes on to the stack in reverse order, then pop them back
# in the right order with n_things
asstuple :i ::= <anything>:a ?(a.__class__ == AssTuple) <none_list a.nodes>:nodelist !([self.ins(n) for n in nodelist[::-1]]) <n_things len(nodelist) i>:ns => '(' + ', '.join(ns) + ')'

# Matches a debug test
assert :i ::= <anything>:a ?(a.__class__ == Assert) ?(a.fail is None) !(self.ins(a.test)) <thing i>:test => 'assert '+test
            | <anything>:a ?(a.__class__ == Assert) ?(not a.fail is None) !(self.ins(a.test)) <thing i>:test !(self.ins(a.fail)) <thing i>:fail => 'assert '+test+', '+fail

# Assign binds an expression "expr" to the list of things "nodes"
# We want the list to be joined by equals signs and followed by expr
# NOTE: We must add a.nodes on to the stack in reverse order, then pop them back
# in the right order with n_things
assign :i ::= <anything>:a ?(a.__class__ == Assign) <none_list a.nodes>:nodelist !([self.ins(n) for n in nodelist[::-1]]) <n_things len(nodelist) i>:ns !(self.ins(a.expr)) <thing i>:expr => ' = '.join(ns) + ' = ' + expr

# Matches an in-place change to something
augassign :i ::= <anything>:a ?(a.__class__ == AugAssign) !(self.ins(a.node)) <thing i>:node !(self.ins(a.expr)) <thing i>:expr => node + a.op + expr

# Matches deprecated object representations
backquote :i ::= <anything>:a ?(a.__class__ == Backquote) !(self.ins(a.expr)) <thing i>:expr => '`'+expr+'`'

# Matches bitwise AND
# NOTE: We must add a.nodes on to the stack in reverse order, then pop them back
# in the right order with n_things
bitand :i ::= <anything>:a ?(a.__class__ == Bitand) <none_list a.nodes>:nodelist !([self.ins(n) for n in nodelist[::-1]]) <n_things len(nodelist) i>:ns => '(('+')&('.join(ns)+'))'

# Matches bitwise OR
# NOTE: We must add a.nodes on to the stack in reverse order, then pop them back
# in the right order with n_things
bitor :i ::= <anything>:a ?(a.__class__ == Bitor) <none_list a.nodes>:nodelist !([self.ins(n) for n in nodelist[::-1]]) <n_things len(nodelist) i>:ns => '(('+')|('.join(ns)+'))'

# Matches bitwise XOR
# NOTE: We must add a.nodes on to the stack in reverse order, then pop them back
# in the right order with n_things
bitxor :i ::= <anything>:a ?(a.__class__ == Bitxor) <none_list a.nodes>:nodelist !([self.ins(n) for n in nodelist[::-1]]) <n_things len(nodelist) i>:ns => '(('+')^('.join(ns)+'))'

# Matches an escape from a loop
break :i ::= <anything>:a ?(a.__class__ == Break) => 'break'

# Matches the sending of a message to an object
# NOTE: We must add a.args on to the stack in reverse order, then pop them back
# in the right order with n_things
callfunc :i ::= <anything>:a ?(a.__class__ == CallFunc) <callfunc_star a.star_args i>:star <callfunc_dstar a.dstar_args i>:dstar !(self.ins(a.node)) <thing i>:n <none_list a.args>:arglist !([self.ins(argument) for argument in arglist[::-1]]) <n_things len(arglist) i>:args => n+'('+', '.join(args+star+dstar)+')'

callfunc_star :s :i ::= ?(s is None) => []
                      | !(self.ins(s)) <thing i>:star => ['*'+star]

callfunc_dstar :d :i ::= ?(d is None) => []
                       | !(self.ins(d)) <thing i>:dstar => ['**'+dstar]

# Matches the description of an object type
class :i ::= <anything>:a ?(a.__class__ == Class) <class_decorators a.decorators i>:decs <class_doc a.doc i+1>:d <class_bases a.bases i>:bases !(self.ins(a.code)) <thing i+1>:code => decs+'class ' + a.name + bases + \""":\n\""" + d + code

# Formats a class's docstring for use in <class>
class_doc :d :i ::= ?(d is None) => ''
                  | ?(d is not None) => ('\t'*i)+pick_quotes(d)+\"""\n\"""

# Formats a class's superclasses for use in <class>
class_bases :b :i ::= <none_list b>:blist ?(len(blist) == 0) => ''
                    | <none_list b>:blist ?(len(blist) > 0) !([self.ins(base) for base in blist[::-1]]) <n_things len(blist) i>:bases => '(' + ', '.join(bases) + ')'

# Formats a class's decorators for use in <class>
class_decorators :d :i ::= <none_list d>:dlist ?(len(dlist) == 0) => ''
                         | <none_list d>:dlist !([self.ins(dec) for dec in dlist[::-1]]) <n_things len(dlist) i>:decs => decs + \"""\n\""" + ('\t' * i)

# Compare groups together comparisons (==, <, >, etc.)
# We want the left-hand expression followed by each operation joined with its right-hand-side
compare :i ::= <anything>:a ?(a.__class__ == Compare) !(self.ins(a.expr)) <thing i>:expr <comparison_ops a.ops i>:ops => '(' + expr + ' ' + ' '.join(ops) + ')'

# Makes a list of comparison types (==, <=, etc.) for use in <compare>
comparison_ops :o :i ::= <none_list o>:olist ?(len(olist) == 0) => []
                       | <none_list o>:olist ?(len(olist) == 1) !(self.ins(olist[0][1])) <thing i>:rhs => [olist[0][0]+' '+rhs]
                       | <none_list o>:olist ?(len(olist) > 1) <comparison_ops olist[0] i>:s <comparison_ops olist[1:] i>:xs => x+xs

# Makes a list of the right-hand-side of comparisons for use in <compare>
comparison_rhss :o :i ::= <none_list o>:olist !([self.ins(c[1]) for c in olist[::-1]]) <n_things len(olist) i>:rhss => rhss

# Const wraps a constant value
# We want strings in quotes and numbers as strings
const :i ::= <anything>:a ?(a.__class__ == Const) ?(a.value is None) => ''
           | <anything>:a ?(a.__class__ == Const) ?(a.value == float('inf')) => '1e30000'
           | <anything>:a ?(a.__class__ == Const) ?(a.value == float('-inf')) => '-1e30000'
           | <anything>:a ?(a.__class__ == Const) ?(a.value != a.value) => '(float("nan"))'
           | <anything>:a ?(a.__class__ == Const) => repr(a.value)
# <anything>:a ?(a.__class__ == Const) ?(type(a.value) == unicode) => 'u'+pick_quotes(a.value)
#           | <anything>:a ?(a.__class__ == Const) ?(type(a.value) == str) => pick_quotes(a.value)
#           | <anything>:a ?(a.__class__ == Const) ?(a.value is None) => ''
#           | <anything>:a ?(a.__class__ == Const) ?(not type(a.value) == str) => repr(a.value)

# Continue
continue :i ::= <anything>:a ?(a.__class__ == Continue) => 'continue'

# Matches transformations applied to functions and classes
decorators :i ::= <anything>:a ?(a.__class__ == Decorators) <none_list a.nodes>:nodelist !(a.nodes is not None and [self.ins(n) for n in nodelist[::-1]]) <n_things len(nodelist) i>:decs => '@'+((\"""\n\"""+'\t'*i + '@').join(decs))

# Matches any nodes which represent deletions
delete :i ::= <anything>:a ?(a.__class__ == AssTuple) ?(is_del(a)) <none_list a.nodes>:nodelist !([self.ins(n) for n in nodelist[::-1]]) <n_things len(nodelist) i>:dels => 'del('+', '.join([n[4:] for n in dels])+')'
            | <anything>:a ?(a.__class__ == AssName) ?(a.flags == 'OP_DELETE') => 'del '+a.name
            | <anything>:a ?(a.__class__ == AssAttr) ?(a.flags == 'OP_DELETE') !(self.ins(a.expr)) <thing i>:expr => 'del '+expr+'.'+a.attrname
            | <anything>:a ?(a.__class__ == Slice) ?(a.flags == 'OP_DELETE') ?(a.upper is None) ?(a.lower is None) !(self.ins(a.expr)) <thing i>:expr => 'del '+expr+'[:]'
            | <anything>:a ?(a.__class__ == Slice) ?(a.flags == 'OP_DELETE') ?(a.upper is None) ?(not a.lower is None) !(self.ins(a.expr)) <thing i>:expr !(self.ins(a.lower)) <thing i>:lower => 'del '+expr+'['+lower+':]'
            | <anything>:a ?(a.__class__ == Slice) ?(a.flags == 'OP_DELETE') ?(not a.upper is None) ?(a.lower is None) !(self.ins(a.expr)) <thing i>:expr !(self.ins(a.upper)) <thing i>:upper => 'del '+expr+'[:'+upper+']'
            | <anything>:a ?(a.__class__ == Slice) ?(a.flags == 'OP_DELETE') ?(not a.upper is None) ?(not a.lower is None) !(self.ins(a.expr)) <thing i>:expr !(self.ins(a.lower)) <thing i>:lower !(self.ins(a.upper)) <thing i>:upper => 'del '+expr+'['+lower+':'+upper+']'
            | <anything>:a ?(a.__class__ == Subscript) ?(a.flags == 'OP_DELETE') !(self.ins(a.expr)) <thing i>:expr <none_list a.subs>:sublist !([self.ins(s) for s in sublist[::-1]]) <n_things len(sublist) i>:subs => 'del '+expr+'['+', '.join(subs)+']'

# Matches unordered key/value collections
dict :i ::= <anything>:a ?(a.__class__ == Dict) <none_list a.items>:itemlist !([self.ins(o[0]) for o in itemlist[::-1]]) <n_things len(itemlist) i>:keys !([self.ins(o[1]) for o in itemlist[::-1]]) <n_things len(itemlist) i>:values => '{'+(', '.join([':'.join(pair) for pair in zip(keys,values)]))+'}'

# Matches statements where a value is not bound to a name
discard :i ::= <anything>:a ?(a.__class__ == Discard) !(self.ins(a.expr)) <thing i>:expr => expr

# Matches division
div :i ::= <anything>:a ?(a.__class__ == Div) !(self.ins(a.left)) <thing i>:left !(self.ins(a.right)) <thing i>:right => '(('+left+')/('+right+'))'

# Matches Ellipsis singleton (used for slicing N-dimensional objects)
ellipsis :i ::= <anything>:a ?(a.__class__ == Ellipsis) => '...'

# FIXME: Do we need this?
emptynode :i ::= <anything>:a ?(a.__class__ == EmptyNode) => ''

# Matches the dynamic execution of a string, file or piece of code
exec :i ::= <anything>:a ?(a.__class__ == Exec) ?(a.globals is None) ?(a.locals is None) !(self.ins(a.expr)) <thing i>:expr => 'exec ('+expr+')'
          | <anything>:a ?(a.__class__ == Exec) ?(a.globals is None) ?(not a.locals is None) !(self.ins(a.expr)) <thing i>:expr !(self.ins(a.locals)) <thing i>:locals => 'exec ('+expr+') in ('+locals+')'
          | <anything>:a ?(a.__class__ == Exec) ?(not a.globals is None) ?(not a.locals is None) !(self.ins(a.expr)) <thing i>:expr !(self.ins(a.locals)) <thing i>:locals !(self.ins(a.globals)) <thing i>:globals => 'exec ('+expr+') in ('+locals+'), ('+globals+')'

# Don't know what this does :( Current plan: Keep testing code until we
# come across something that uses it, then study that code to see what
# it is
expression :i ::= <anything>:a ?(a.__class__ == Expression) => 'FAIL'

# Matches integer division
floordiv :i ::= <anything>:a ?(a.__class__ == FloorDiv) !(self.ins(a.left)) <thing i>:left!(self.ins(a.right)) <thing i>:right=> '(' + left + ' // ' + right + ')'

# Matches for loops
for :i ::= <anything>:a ?(a.__class__ == For) ?(a.else_ is None) !(self.ins(a.assign)) <thing i>:assign !(self.ins(a.list)) <thing i>:list !(self.ins(a.body)) <thing i+1>:body => 'for '+assign+' in '+list+\""":\n\"""+body
         | <anything>:a ?(a.__class__ == For) ?(not a.else_ is None) !(self.ins(a.assign)) <thing i>:assign !(self.ins(a.list)) <thing i>:list !(self.ins(a.body)) <thing i+1>:body !(self.ins(a.else_)) <thing i+1>:else_ => 'for '+assign+' in '+list+\""":\n\"""+body+\"""\n\"""+(i*'\t')+\"""else:\n\"""+else_

# Matches namespace injections
from :i ::= <anything>:a ?(a.__class__ == From) => 'from '+(a.level*'.')+a.modname+' import '+', '.join(import_match(a.names))

# Matches function definition
# Don't be scared by the list comprehensions, they only match argument
# defaults! The list of argument names is "argnames", any defaults (eg.
# "True" for "arg1=True") are given as the list "defaults". To match
# names to defaults we need to reverse both using [::-1], since the last
# default is the last argument, but the first default isn't necessarily
# the first argument. Then join them with an '=' and reverse this list
# to get the correct order. This is added to the names without defaults.
# If "varargs" and/or "kwargs" are not None then the last 1 or 2 names
# should be prepended by '*' and '**' respectively (only the last one if
# one or the other isn't None, both if both, '*' coming before '**').
# Using [-2::-1] and [-3::-1] reverses & chops off 1 or 2 args as needed
# tuple_args recursively turns nested arguments into appropriate strings

function :i ::= <anything>:a ?(a.__class__ == Function) <function_decorators a.decorators i>:decs ?(a.varargs is None) ?(a.kwargs is None) <function_doc a.doc i+1>:doc <none_list a.defaults>:deflist !([self.ins(d) for d in deflist[::-1]]) <n_things len(deflist) i>:defaults !(self.ins(a.code)) <thing i+1>:code => decs+'def '+a.name+'('+', '.join(tuple_args(a.argnames)[::-1][len(a.defaults):][::-1]+([a.argnames[::-1][x]+'='+y for x,y in enumerate(defaults[::-1])][::-1]))+\"""):\"""+doc+code
              | <anything>:a ?(a.__class__ == Function) <function_decorators a.decorators i>:decs ?(a.varargs is None) ?(not a.kwargs is None) <function_doc a.doc i+1>:doc <none_list a.defaults>:deflist !([self.ins(d) for d in deflist[::-1]]) <n_things len(deflist) i>:defaults !(self.ins(a.code)) <thing i+1>:code => 'def '+a.name+'('+', '.join(tuple_args(a.argnames)[::-1][len(a.defaults)+1:][::-1]+([a.argnames[-2::-1][x]+'='+y for x,y in enumerate(defaults[::-1])][::-1])+['**'+a.argnames[-1]])+\"""):\"""+code
              | <anything>:a ?(a.__class__ == Function) <function_decorators a.decorators i>:decs ?(not a.varargs is None) ?(a.kwargs is None) <function_doc a.doc i+1>:doc <none_list a.defaults>:deflist !([self.ins(d) for d in deflist[::-1]]) <n_things len(deflist) i>:defaults !(self.ins(a.code)) <thing i+1>:code => 'def '+a.name+'('+', '.join(tuple_args(a.argnames)[::-1][len(a.defaults)+1:][::-1]+([a.argnames[-2::-1][x]+'='+y for x,y in enumerate(defaults[::-1])][::-1])+['*'+a.argnames[-1]])+\"""):\"""+code
              | <anything>:a ?(a.__class__ == Function) <function_decorators a.decorators i>:decs ?(not a.varargs is None) ?(not a.kwargs is None) <function_doc a.doc i+1>:doc <none_list a.defaults>:deflist !([self.ins(d) for d in deflist[::-1]]) <n_things len(deflist) i>:defaults !(self.ins(a.code)) <thing i+1>:code => 'def '+a.name+'('+', '.join(tuple_args(a.argnames)[::-1][len(a.defaults)+2:][::-1]+([a.argnames[-3::-1][x]+'='+y for x,y in enumerate(defaults[::-1])][::-1])+['*'+a.argnames[-2], '**'+a.argnames[-1]])+\"""):\"""+code

# Formats a function's decorators for use in <function>
function_decorators :d :i ::= ?(d is None) => ''
                            | ?(d is not None) !(self.ins(d)) <thing i>:decs => decs+\"""\n\"""+(i*'\t')

function_doc :d :i ::= ?(d is None) => ''
                     | ?(d is not None) => \"""\n\"""+('\t'*(i))+pick_quotes(d)

# Matches list-generating expressions
genexpr :i ::= <anything>:a ?(a.__class__ == GenExpr) !(self.ins(a.code)) <thing i>:code => '('+code+')'

# Matches the loops of a list-generating expression
genexprfor :i ::= <anything>:a ?(a.__class__ == GenExprFor) !(self.ins(a.assign)) <thing i>:assign !(self.ins(a.iter)) <thing i>:iter <none_list a.ifs>:iflist !([self.ins(z) for z in iflist[::-1]]) <n_things len(iflist) i>:ifs => 'for '+assign+' in '+iter+' '.join(ifs)

# Matches any conditions on members in a list-generating expression
genexprif :i ::= <anything>:a ?(a.__class__ == GenExprIf) !(self.ins(a.test)) <thing i>:test => ' if '+test

# Matches the body of a list-generating expression
genexprinner :i ::= <anything>:a ?(a.__class__ == GenExprInner) <none_list a.quals>:quallist !([self.ins(n) for n in quallist[::-1]]) <n_things len(quallist) i>:quals !(self.ins(a.expr)) <thing i>:expr => expr+' '+' '.join(quals)

# Matches the retrieval of an object's attribute
getattr :i ::= <anything>:a ?(a.__class__ == Getattr) !(self.ins(a.expr)) <thing i>:expr !(self.ins(a.attrname)) <getattr_name i>:attrname => expr+'.'+attrname

# Selects a node or a string, for use in <getattr>
getattr_name :i ::= <thing i>:n => n
                  | <anything>:n ?(type(n) == type('string')) => n

# Matches the injection of a variable from a parent namespace
global :i ::= <anything>:a ?(a.__class__ == Global) => 'global '+', '.join(a.names)

# Matches if, elif and else conditions
if :i ::= <anything>:a ?(a.__class__ == If) <none_list a.tests>:testlist ?(len(testlist) == 1) !(self.ins(testlist[0][0])) <thing i>:test !(self.ins(testlist[0][1])) <thing i+1>:code <if_else a.else_ i+1>:else_ => 'if '+test+\""":\n\"""+code+\"""\n\"""+(i*'\t')+else_+\"""\n\"""
        | <anything>:a ?(a.__class__ == If) <none_list a.tests>:testlist ?(len(testlist) > 1) !(self.ins(testlist[0][0])) <thing i>:test !(self.ins(testlist[0][1])) <thing i+1>:code <if_else a.else_ i+1>:else_ !([self.ins(n[0]) for n in reversed(testlist[1:])]) <n_things len(testlist)-1 i>:ifs !([self.ins(n[1]) for n in reversed(testlist[1:])]) <n_things len(testlist)-1 i+1>:thens => 'if '+test+\""":\n\"""+code+''.join([\"""\n\"""+('\t'*i)+'elif '+(\""":\n\""".join(pair)) for pair in zip(ifs,thens)])+\"""\n\"""+('\t'*i)+else_+\"""\n\"""

# Formats an else statement for use in <if>
if_else :e :i ::= ?(e is None) => ''
                | ?(e is not None) !(self.ins(e)) <thing i>:else_ => \"""else:\n\"""+else_

ifexp :i ::= <anything>:a ?(a.__class__ == IfExp) !(self.ins(a.then)) <thing i>:then !(self.ins(a.test)) <thing i>:test !(self.ins(a.else_)) <thing i>:else_ => '(' + then + ') if (' + test + ') else (' + else_ + ')'

# Matches the access of external modules
import :i ::= <anything>:a ?(a.__class__ == Import) => 'import '+', '.join(import_match(a.names))

invert :i ::= <anything>:a ?(a.__class__ == Invert) !(self.ins(a.expr)) <thing i>:expr => '(~('+expr+'))'

# Matches a key/value pair in an argument list
keyword :i ::= <anything>:a ?(a.__class__ == Keyword) !(self.ins(a.expr)) <thing i>:expr => a.name+'='+expr

# Matches anonymous functions
# FIXME: What do the flags represent?
lambda :i ::= <anything>:a ?(a.__class__ == Lambda) <none_list a.defaults>:deflist !([self.ins(n) for n in deflist[::-1]]) <n_things len(deflist) i>:defaults !(self.ins(a.code)) <thing i>:code => 'lambda '+set_defaults(a.argnames, defaults)+': '+code

# Matches leftwards bit shifts
leftshift :i ::= <anything>:a ?(a.__class__ == LeftShift) !(self.ins(a.left)) <thing i>:left !(self.ins(a.right)) <thing i>:right => '(('+left+')<<('+right+'))'

# Matches a mutable, ordered collection
list :i ::= <anything>:a ?(a.__class__ == List) <none_list a.nodes>:nodelist !([self.ins(n) for n in nodelist[::-1]]) <n_things len(nodelist) i>:nodes => '['+', '.join(nodes)+']'

# Matches lists-creating expressions
listcomp :i ::= <anything>:a ?(a.__class__ == ListComp) !(self.ins(a.expr)) <thing i>:expr <none_list a.quals>:quallist !([self.ins(n) for n in quallist[::-1]]) <n_things len(quallist) i>:quals => '['+expr+' '.join(quals)+']'

# Matches transformations applied to existing lists in generating expressions
listcompfor :i ::= <anything>:a ?(a.__class__ == ListCompFor) !(self.ins(a.assign)) <thing i>:assign !(self.ins(a.list)) <thing i>:list_ <none_list a.ifs>:iflist !([self.ins(n) for n in iflist[::-1]]) <n_things len(iflist) i>:ifs => ' for '+assign+' in '+list_+''.join(ifs)

# Matches selection conditions in list-generating expressions
listcompif :i ::= <anything>:a ?(a.__class__ == ListCompIf) !(self.ins(a.test)) <thing i>:test => ' if '+test

# Matches remainder functions (the remainder of the left after dividing
# by the right)
mod :i ::= <anything>:a ?(a.__class__ == Mod) !(self.ins(a.left)) <thing i>:left !(self.ins(a.right)) <thing i>:right => '(('+left+') % ('+right+'))'

# Modules contain a Stmt node, and optionally a doc string
# We want the doc string (if it has one) followed by the Stmt
module :i ::= <anything>:a ?(a.__class__ == Module) ?(a.doc is None) !(self.ins(a.node)) <thing i>:node => node
            | <anything>:a ?(a.__class__ == Module) ?(a.doc is not None) !(self.ins(a.node)) <thing i>:node=> pick_quotes(a.doc)+node

# Matches multiplication
mul :i ::= <anything>:a ?(a.__class__ == Mul) !(self.ins(a.left)) <thing i>:left !(self.ins(a.right)) <thing i>:right => '(('+left+') * ('+right+'))'

# Matches the use of a variable name
name :i ::= <anything>:a ?(a.__class__ == Name) => a.name

# Matches the negation of a boolean
not :i ::= <anything>:a ?(a.__class__ == Not) !(self.ins(a.expr)) <thing i>:expr => '(not ('+expr+'))'

# Matches a chain of logical OR operations on booleans
or :i ::= <anything>:a ?(a.__class__ == Or) <none_list a.nodes>:nodelist !([self.ins(n) for n in nodelist[::-1]]) <n_things len(nodelist) i>:nodes => '(('+') or ('.join(nodes)+'))'

# Matches a placeholder where indentation requires a code block but no
# code is needed
pass :i ::= <anything>:a ?(a.__class__ == Pass) => 'pass'

# Matches exponentiation
power :i ::= <anything>:a ?(a.__class__ == Power) !(self.ins(a.left)) <thing i>:left !(self.ins(a.right)) <thing i>:right => '(('+left+')**('+right+'))'

# Matches outputting text (without a newline)
print :i ::= <anything>:a ?(a.__class__ == Print) ?(a.dest is None) <none_list a.nodes>:nodelist !([self.ins(n) for n in nodelist[::-1]]) <n_things len(nodelist) i>:nodes => 'print '+', '.join(nodes)+','
           | <anything>:a ?(a.__class__ == Print) !(self.ins(a.dest)) <thing i>:dest <none_list a.nodes>:nodelist !([self.ins(n) for n in nodelist[::-1]]) <n_things len(nodelist) i>:nodes => 'print >> '+dest+', '+', '.join(nodes)+','

# Matches outputting text with a newline
printnl :i ::= <anything>:a ?(a.__class__ == Printnl) ?(a.dest is None) <none_list a.nodes>:nodelist !([self.ins(n) for n in nodelist[::-1]]) <n_things len(nodelist) i>:nodes => 'print '+', '.join(nodes)
             | <anything>:a ?(a.__class__ == Printnl) !(self.ins(a.dest)) <thing i>:dest <none_list a.nodes>:nodelist !([self.ins(n) for n in nodelist[::-1]]) <n_things len(nodelist) i>:nodes => 'print >> '+dest+', '+', '.join(nodes)

# Matches error passing
raise :i ::= <anything>:a ?(a.__class__ == Raise) <raise_exprs a.expr1 a.expr2 a.expr3 i>:exprs => 'raise '+exprs

raise_exprs :f :s :t :i ::= <raise_expr1 f s t i>:first <raise_expr2 f s t i>:second <raise_expr3 f s t i>:third => ', '.join(first+second+third)

raise_expr1 :f :s :t :i ::= ?(f is not None) !(self.ins(f)) <thing i>:first => [first]
                          | ?(s is not None or t is not None) => ['None']
                          | ?(f is None and s is None and t is None) => []

raise_expr2 :f :s :t :i ::= ?(s is not None) !(self.ins(s)) <thing i>:second => [second]
                          | ?(t is not None) => ['None']
                          | ?(s is None and t is None) => []

raise_expr3 :f :s :t :i ::= ?(t is not None) !(self.ins(t)) <thing i>:third => [third]
                          | ?(t is None) => []

# Matches the passing of return values from functions, etc.
return :i ::= <anything>:a ?(a.__class__ == Return) !(self.ins(a.value)) <thing i>:value => 'return '+value

rightshift :i ::= <anything>:a ?(a.__class__ == RightShift) !(self.ins(a.left)) <thing i>:left !(self.ins(a.right)) <thing i>:right => '(('+left+')>>('+right+'))'

# Matches a subset of an ordered sequence
# We want the upper and lower boundaries if present, subscripting the
# sequence expression with them, separated by a colon (blank for None)
slice :i ::= <anything>:a ?(a.__class__ == Slice) !(self.ins(a.expr)) <thing i>:expr <slice_upper a.upper i>:upper <slice_lower a.lower i>:lower => expr+'['+lower+':'+upper+']'

slice_upper :u :i ::= ?(u is None) => ''
                    | ?(u is not None) !(self.ins(u)) <thing i>:upper => upper

slice_lower :l :i ::= ?(l is None) => ''
                    | ?(l is not None) !(self.ins(l)) <thing i>:lower => lower

sliceobj :i ::= <anything>:a ?(a.__class__ == Sliceobj) <none_list a.nodes>:nodelist !([self.ins(n) for n in nodelist[::-1]]) <n_things len(nodelist) i>:nodes => ':'.join(nodes)

# Stmt is a statement (code block), containing a list of nodes
# We want each node to be on a new line with i tabs as indentation
# We make a special case if the 'statement' is a constant None, since this ends
# up putting a semicolon
stmt :i ::= <anything>:a ?(a.__class__ == Stmt) <none_list a.nodes>:nodelist !([self.ins(n) for n in nodelist[::-1]]) <n_things len(nodelist) i>:nodes => (\"""\n\"""+'\t'*i)+(\"""\n\"""+'\t'*i).join([n+';'*len([b for b in [0] if len(a.nodes)>e+1 and a.nodes[e+1].__class__ == Discard and a.nodes[e+1].expr.__class__ == Const and a.nodes[e+1].expr.value is None]) for e,n in enumerate(nodes)])

# Matches subtraction
sub :i ::= <anything>:a ?(a.__class__ == Sub) !(self.ins(a.left)) <thing i>:left !(self.ins(a.right)) <thing i>:right => '(('+left+') - ('+right+'))'

# Matches extracting item(s) from a collection based on an index or key
subscript :i ::= <anything>:a ?(a.__class__ == Subscript) !(self.ins(a.expr)) <thing i>:expr <none_list a.subs>:sublist !([self.ins(s) for s in sublist[::-1]]) <n_things len(sublist) i>:subs => expr+'['+', '.join(subs)+']'

# Matches try/except blocks
tryexcept :i ::= <anything>:a ?(a.__class__ == TryExcept) <tryexcept_else a.else_ i>:else_ !(self.ins(a.body)) <thing i+1>:body <one_except a.handlers i>:hs => 'try:'+body+\"""\n\"""+i*'\t'+(\"""\n\"""+i*'\t').join(hs)+else_

one_except :e :i ::= ?(len(e) > 0) <h_zero e[0] i>:h <h_one e[0] i>:h1 !(self.ins(e[0][2])) <thing i+1>:h2 <one_except e[1:] i>:next => ['except' + ' '.join(h) + ', '.join(h1) + ':' + h2]+next
                   | ?(len(e) == 0) => []

h_zero :h :i ::= ?(h[0] is None) => []
               | ?(h[0] is not None) !(self.ins(h[0])) <thing i>:h0 => [' '+h0]

h_one :h :i ::= ?(h[1] is None) => []
              | ?(h[1] is not None) !(self.ins(h[1])) <thing i>:h1 => [', '+h1]

tryexcept_else :e :i ::= ?(e is not None) !(self.ins(e)) <thing i+1>:else_ => \"""\n\"""+'\t'*i+\"""else:\"""+else_
                       | ?(e is None) => ''

# Catches finally clauses on try/except blocks
tryfinally :i ::= <anything>:a ?(a.__class__ == TryFinally) ?(a.body.__class__ == TryExcept) !(self.ins(a.body)) <thing i>:body !(self.ins(a.final)) <thing i+1>:final => body+\"""\n\"""+i*'\t'+'finally:'+final
                | <anything>:a ?(a.__class__ == TryFinally) !(self.ins(a.body)) <thing i+1>:body !(self.ins(a.final)) <thing i+1>:final => 'try:'+body+\"""\n\"""+i*'\t'+'finally:'+final

# Matches an immutable, ordered collection
tuple :i ::= <anything>:a ?(a.__class__ == Tuple) ?(len(a.nodes) > 1) <none_list a.nodes>:nodelist !([self.ins(n) for n in nodelist[::-1]]) <n_things len(nodelist) i>:nodes => '('+', '.join(nodes)+')'
           | <anything>:a ?(a.__class__ == Tuple) ?(len(a.nodes) == 1) !(self.ins(a.nodes[0])) <thing i>:node => '('+node+',)'
           | <anything>:a ?(a.__class__ == Tuple) ?(len(a.nodes) == 0) => '()'

# Matches a positive operator
unaryadd :i ::= <anything>:a ?(a.__class__ == UnaryAdd) !(self.ins(a.expr)) <thing i>:expr => '(+'+expr+')'

# Matches a negative operator
unarysub :i ::= <anything>:a ?(a.__class__ == UnarySub) !(self.ins(a.expr)) <thing i>:expr => '(-'+expr+')'

# Matches a while loop
while :i ::= <anything>:a ?(a.__class__ == While) ?(a.else_ is None) !(self.ins(a.test)) <thing i>:test !(self.ins(a.body)) <thing i+1>:body => 'while '+test+\""":\n\"""+body
           | <anything>:a ?(a.__class__ == While) ?(not a.else_ is None) !(self.ins(a.test)) <thing i>:test !(self.ins(a.body)) <thing i+1>:body !(self.ins(a.else_)) <thing i+1>:else_ => 'while '+test+\""":\n\"""+body+\"""\n\"""+(i*'\t')+\"""else:\n\"""+else_

# Matches object-style try/catch
with :i ::= <anything>:a ?(a.__class__ == With) ?(a.vars is not None) !(self.ins(a.expr)) <thing i>:expr !(self.ins(a.vars)) <thing i>:vars !(self.ins(a.body)) <thing i+1>:body => 'with '+expr+' as '+vars+\""":\n\"""+('\t'*(i+1))+body
          | <anything>:a ?(a.__class__ == With) !(self.ins(a.expr)) <thing i>:expr !(self.ins(a.body)) <thing i+1>:body => 'with '+expr+\""":\n\"""+('\t'*(i+1))+body

# Matches generator values
yield :i ::= <anything>:a ?(a.__class__ == Yield) !(self.ins(a.value)) <thing i>:value => 'yield '+value

# Matches exactly n things
n_things :n :i ::= ?(n == 0) => []
                 | ?(n == 1) <thing i>:t => [t]
                 | ?(n > 1) <thing i>:t <n_things n-1 i>:ts => [t]+ts

# Calling functions in list recursions can have a habit of performing one extra
# call. This ensures that no cruft gets left on the input stream after calling
# self.ins inside a list comprehension. It always matches.
cleanup ::= <anything>:a ?(a == [None])
          | ?(1 == 1)

none_list :a ::=  => make_list(a)
"""

# These are the objects which will be available to the matcher
import sys
args = globals()
args['constants'] = [str, int, float, complex]
args['import_match'] = import_match
args['tuple_args'] = tuple_args
args['is_del'] = is_del
args['pick_quotes'] = pick_quotes
args['make_list'] = make_list
args['sys'] = sys

# grammar is the class, instances of which can match using grammar_def
grammar = OM.makeGrammar(grammar_def, args)

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

grammar.ins = ins

def parse(code):
	"""This parses the given code using Python's compiler module, but
	with our monkey patching applied to the nodes."""
	return compiler.parse(code)

# Cleanup the namespace a little
del args

if __name__ == '__main__':
		matcher = grammar([parse('1<2')])
		try:
			result,err = matcher.apply('python',0)
			print result
		except:
			print ':('
		pass
