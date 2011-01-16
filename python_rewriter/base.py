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

# Can't get my OMeta subclasses to work, and OMeta has no comment syntax
# so we have to remove comments from the grammar manually using this
def strip_comments(s):
	"""Strips comments (anything after a '#' up to a newline) from the
	given string, returning the resulting string."""
	r = ''
	in_comment = False
	for character in s:
		if in_comment:
			if character == '\n':
				r = r+character
				in_comment = False
		else:
			if character == '#':
				in_comment = True
			else:
				r = r+character
	return r

# Couldn't think of a simple way to do these inside the grammar, so put
# them in functions which are accessible from inside the grammar

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
	# First list the possibilities
	#quotes = ["'", '"']
	#quote_lines = ["'''", '"""']
	
	# If there's a new line then stick to multiline strings, otherwise
	# allow single and multiline.
	#if '\n' in string:
	#	try_quotes = quote_lines
	#else:
	#	try_quotes = quotes+quote_lines
	
	# Now step through them looking for one which isn't used in the
	# string
	#for quote_type in try_quotes:
	#	if quote_type not in string.replace('\\'+quote_type, ''): 
	#		return quote_type+string+quote_type
	# If we haven't returned yet then find possible candidates
	#candidates = []
	#for quote_type in try_quotes:
	#	if (not string.startswith(quote_type)) and (not string.endswith(quote_type)):
	#		candidates.append(quote_type)
	# Then choose the best
	#for quote_type in candidates:
	#	if string.count(quote_type) == min(map(string.count, candidates)):
	#		return quote_type+string.replace(quote_type, '\\'+quote_type_)+quote_type
	# If we're still here then something's not right, so just choose one
	#return '"""'+string.replace('"""', '\\"""')+'"""'
	
	# If the following covers all cases then we can remove the overly
	# complicated stuff above
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

# This is the grammar, defined in OMeta, which does our translation
grammar_def = """

# "python" is used to output Python code from an AST node. The number given
# to the "thing"  (usually 0) is the number of tabs to use as the initial
# indentation.
python :i ::= <thing i>:t => t

# A "thing" matches an AST node or a constant (constants can be supplied
# through the global "constants")
thing :i ::= <node i>+:t => ''.join(t)
          | <anything>:a ?(type(a) in constants) => a

# A "node" is an AST node. The handling of each is deferred to the 
# appropriate rule for that node type
node :i ::= <delete i>:d => d
          | <add i>:a => a
          | <and i>:a => a
          | <assattr i>:a => a
          | <asslist i>:a => a
          | <assname i>:a => a
          | <asstuple i>:a => a
          | <assert i>:a => a
          | <assign i>:a => a
          | <augassign i>:a => a
          | <backquote i>:b => b
          | <bitand i>:b => b
          | <bitor i>:b => b
          | <bitxor i>:b => b
          | <break i>:b => b
          | <callfunc i>:c => c
          | <class i>:c => c
          | <compare i>:c => c
          | <const i>:c => c
          | <continue i>:c => c
          | <decorators i>:d => d
          | <dict i>:d => d
          | <discard i>:d => d
          | <div i>:d => d
          | <ellipsis i>:e => e
          | <emptynode i>:e => e
          | <exec i>:e => e
          | <expression i>:e => e
          | <floordiv i>:e => e
          | <for i>:f => f
          | <from i>:f => f
          | <function i>:f => f
          | <genexpr i>:g => g
          | <genexprfor i>:g => g
          | <genexprif i>:g => g
          | <genexprinner i>:g => g
          | <getattr i>:g => g
          | <global i>:g => g
          | <if i>:g => g
          | <ifexp i>:g => g
          | <import i>:g => g
          | <invert i>:g => g
          | <keyword i>:k => k
          | <lambda i>:l => l
          | <leftshift i>:l => l
          | <list i>:l => l
          | <listcomp i>:l => l
          | <listcompfor i>:l => l
          | <listcompif i>:l => l
          | <mod i>:m => m
          | <module i>:m => m
          | <mul i>:m => m
          | <name i>:n => n
          | <not i>:n => n
          | <or i>:o => o
          | <pass i>:p => p
          | <power i>:p => p
          | <print i>:p => p
          | <printnl i>:p => p
          | <raise i>:r => r
          | <return i>:r => r
          | <rightshift i>:r => r
          | <slice i>:s => s
          | <sliceobj i>:s => s
          | <stmt i>:s => s
          | <sub i>:s => s
          | <subscript i>:s => s
          | <tryexcept i>:t => t
          | <tryfinally i>:t => t
          | <tuple i>:t => t
          | <unaryadd i>:u => u
          | <unarysub i>:u => u
          | <while i>:w => w
          | <with i>:w => w
          | <yield i>:y => y
## UNCOMMENT THE FOLLOWING TO MAKE DEBUGGING EASIER
#		  | <anything>:a => 'FAIL'+str(a)

# Add is addition, with a left and a right
# We want the left and right, joined by a plus sign '+'
add :i ::= <anything>:a ?(a.__class__ == Add) => '('+str(a.left.rec(i))+' + '+str(a.right.rec(i))+')'

# Matches a chain of logical AND operations on booleans
and :i ::= <anything>:a ?(a.__class__ == And) => '('+') and ('.join([n.rec(i) for n in a.nodes])+')'

# Matches the binding of an object to a member name of another object
assattr :i ::= <anything>:a ?(a.__class__ == AssAttr) => a.expr.rec(i)+'.'+a.attrname

# Matches the binding of a list of items
asslist :i ::= <anything>:a ?(a.__class__ == AssList) => '[' + ', '.join([n.rec(i) for n in a.nodes]) + ']'

# AssName assigns to a variable name
# We want the variable name
assname :i ::= <anything>:a ?(a.__class__ == AssName) => a.name

# Matches the assignment of multiple names to multiple objects
asstuple :i ::= <anything>:a ?(a.__class__ == AssTuple) => '(' + ', '.join([n.rec(i) for n in a.nodes]) + ')'

# Matches a debug test
assert :i ::= <anything>:a ?(a.__class__ == Assert) ?(a.fail is None) => 'assert '+a.test.rec(i)
            | <anything>:a ?(a.__class__ == Assert) ?(not a.fail is None) => 'assert '+a.test.rec(i)+', '+a.fail.rec(i)

# Assign binds an expression "expr" to the list of things "nodes"
# We want the list to be joined by equals signs and followed by expr
assign :i ::= <anything>:a ?(a.__class__ == Assign) => ' = '.join([n.rec(i) for n in a.nodes]) + ' = ' + a.expr.rec(i)

# Matches an in-place change to something
augassign :i ::= <anything>:a ?(a.__class__ == AugAssign) => a.node.rec(i) + a.op + a.expr.rec(i)

# Matches deprecated object representations
backquote :i ::= <anything>:a ?(a.__class__ == Backquote) => '`'+a.expr.rec(i)+'`'

# Matches bitwise AND
bitand :i ::= <anything>:a ?(a.__class__ == Bitand) => '('+'&'.join(['('+n.rec(i)+')' for n in a.nodes])+')'

# Matches bitwise OR
bitor :i ::= <anything>:a ?(a.__class__ == Bitor) => '('+'|'.join(['('+n.rec(i)+')' for n in a.nodes])+')'

# Matches bitwise XOR
bitxor :i ::= <anything>:a ?(a.__class__ == Bitxor) => '('+'^'.join(['('+n.rec(i)+')' for n in a.nodes])+')'

# Matches an escape from a loop
break :i ::= <anything>:a ?(a.__class__ == Break) => 'break'

# Matches the sending of a message to an object
callfunc :i ::= <anything>:a ?(a.__class__ == CallFunc) ?(a.star_args is None) ?(a.dstar_args is None) => a.node.rec(i)+'('+(', '.join([n.rec(i) for n in a.args]))+')'
              | <anything>:a ?(a.__class__ == CallFunc) ?(len(a.args) > 0) ?(not a.star_args is None) ?(a.dstar_args is None) => a.node.rec(i)+'('+(', '.join([n.rec(i) for n in a.args]))+', *'+a.star_args.rec(i)+')'
              | <anything>:a ?(a.__class__ == CallFunc) ?(len(a.args) > 0) ?(a.star_args is None) ?(not a.dstar_args is None) => a.node.rec(i)+'('+(', '.join([n.rec(i) for n in a.args]))+', **'+a.dstar_args.rec(i)+')'
              | <anything>:a ?(a.__class__ == CallFunc) ?(len(a.args) > 0) ?(not a.star_args is None) ?(not a.dstar_args is None) => a.node.rec(i)+'('+(', '.join([n.rec(i) for n in a.args]))+', *'+a.star_args.rec(i)+', **'+a.dstar_args.rec(i)+')'
              | <anything>:a ?(a.__class__ == CallFunc) ?(len(a.args) == 0) ?(not a.star_args is None) ?(a.dstar_args is None) => a.node.rec(i)+'(*'+a.star_args.rec(i)+')'
              | <anything>:a ?(a.__class__ == CallFunc) ?(len(a.args) == 0) ?(a.star_args is None) ?(not a.dstar_args is None) => a.node.rec(i)+'(**'+a.dstar_args.rec(i)+')'
              | <anything>:a ?(a.__class__ == CallFunc) ?(len(a.args) == 0) ?(not a.star_args is None) ?(not a.dstar_args is None) => a.node.rec(i)+'(*'+a.star_args.rec(i)+', **'+a.dstar_args.rec(i)+')'


# Matches the description of an object type
class :i ::= <anything>:a ?(a.__class__ == Class) ?(v[1] < 6 or a.decorators is None) ?(len(a.bases) == 0) ?(a.doc is None) => 'class '+a.name+\""":\n\"""+a.code.rec(i+1)
           | <anything>:a ?(a.__class__ == Class) ?(v[1] < 6 or a.decorators is None) ?(len(a.bases) == 0) ?(not a.doc is None) => 'class '+a.name+\""":\n\"""+('\t'*(i+1))+pick_quotes(a.doc)+a.code.rec(i+1)
           | <anything>:a ?(a.__class__ == Class) ?(v[1] < 6 or a.decorators is None) ?(len(a.bases) > 0) ?(a.doc is None) => 'class '+a.name+'('+(', '.join([n.rec(i) for n in a.bases]))+\"""):\n\"""+a.code.rec(i+1)
           | <anything>:a ?(a.__class__ == Class) ?(v[1] < 6 or a.decorators is None) ?(len(a.bases) > 0) ?(not a.doc is None) => 'class '+a.name+'('+(', '.join([n.rec(i) for n in a.bases]))+\"""):\n\"""+('\t'*(i+1))+pick_quotes(a.doc)+a.code.rec(i+1)
           | <anything>:a ?(a.__class__ == Class) ?(v[1] > 6 and not a.decorators is None) ?(len(a.bases) == 0) ?(a.doc is None) => a.decorators.rec(i)+\"""\n\"""+(i*'\t')+'class '+a.name+\""":\n\"""+a.code.rec(i+1)
           | <anything>:a ?(a.__class__ == Class) ?(v[1] > 6 and not a.decorators is None) ?(len(a.bases) == 0) ?(not a.doc is None) => a.decorators.rec(i)+\"""\n\"""+(i*'\t')+'class '+a.name+'\""":\n\"""+((i+1)*'\t')+pick_quotes(a.doc)+\"""\"""+a.code.rec(i+1)
           | <anything>:a ?(a.__class__ == Class) ?(v[1] > 6 and not a.decorators is None) ?(len(a.bases) > 0) ?(a.doc is None) => a.decorators.rec(i)+\"""\n\"""+(i*'\t')+'class '+a.name('+(', '.join([n.rec(i) for n in a.bases]))+\"""):\"""+a.code.rec(i+1)
           | <anything>:a ?(a.__class__ == Class) ?(v[1] > 6 and not a.decorators is None) ?(len(a.bases) > 0) ?(not a.doc is None) => a.decorators.rec(i)+\"""\n\"""+(i*'\t')+'class '+a.name+'('+(', '.join([n.rec(i) for n in a.bases]))+\""":\n\"""+((i+1)*'\t')+pick_quotes(a.doc)+a.code.rec(i+1)           

# Compare groups together comparisons (==, <, >, etc.)
# We want the left-hand expression followed by each operation joined with its right-hand-side
compare :i ::= <anything>:a ?(a.__class__ == Compare) => '(' + a.expr.rec(i) + ' ' + ' '.join([o[0]+' '+o[1].rec(i) for o in a.ops]) + ')'

# Const wraps a constant value
# We want strings in quotes and numbers as strings
const :i ::= <anything>:a ?(a.__class__ == Const) ?(a.value is None) => ''
           | <anything>:a ?(a.__class__ == Const) => repr(a.value)
# <anything>:a ?(a.__class__ == Const) ?(type(a.value) == unicode) => 'u'+pick_quotes(a.value)
#           | <anything>:a ?(a.__class__ == Const) ?(type(a.value) == str) => pick_quotes(a.value)
#           | <anything>:a ?(a.__class__ == Const) ?(a.value is None) => ''
#           | <anything>:a ?(a.__class__ == Const) ?(not type(a.value) == str) => repr(a.value)

# Continue
continue :i ::= <anything>:a ?(a.__class__ == Continue) => 'continue'

# Matches transformations applied to functions and classes
decorators :i ::= <anything>:a ?(a.__class__ == Decorators) => '@'+((\"""\n\"""+'\t'*i + '@').join([n.rec(i) for n in a.nodes]))

# Matches any nodes which represent deletions
delete :i ::= <anything>:a ?(a.__class__ == AssTuple) ?(is_del(a)) => 'del('+', '.join([n.rec(i)[4:] for n in a.nodes])+')'
            | <anything>:a ?(a.__class__ == AssName) ?(a.flags == 'OP_DELETE') => 'del '+a.name
            | <anything>:a ?(a.__class__ == AssAttr) ?(a.flags == 'OP_DELETE') => 'del '+a.expr.rec(i)+'.'+a.attrname
            | <anything>:a ?(a.__class__ == Slice) ?(a.flags == 'OP_DELETE') ?(a.upper is None) ?(a.lower is None) => 'del '+a.expr.rec(i)+'[:]'
            | <anything>:a ?(a.__class__ == Slice) ?(a.flags == 'OP_DELETE') ?(a.upper is None) ?(not a.lower is None) => 'del '+a.expr.rec(i)+'['+a.lower.rec(i)+':]'
            | <anything>:a ?(a.__class__ == Slice) ?(a.flags == 'OP_DELETE') ?(not a.upper is None) ?(a.lower is None) => 'del '+a.expr.rec(i)+'[:'+a.upper.rec(i)+']'
            | <anything>:a ?(a.__class__ == Slice) ?(a.flags == 'OP_DELETE') ?(not a.upper is None) ?(not a.lower is None) => 'del '+a.expr.rec(i)+'['+a.lower.rec(i)+':'+a.upper.rec(i)+']'
            | <anything>:a ?(a.__class__ == Subscript) ?(a.flags == 'OP_DELETE') => 'del '+a.expr.rec(i)+'['+', '.join([s.rec(i) for s in a.subs])+']'

# Matches unordered key/value collections
dict :i ::= <anything>:a ?(a.__class__ == Dict) => '{'+(', '.join([o[0].rec(i)+':'+o[1].rec(i) for o in a.items]))+'}'

# Matches statements where a value is not bound to a name
discard :i ::= <anything>:a ?(a.__class__ == Discard) => a.expr.rec(i)

# Matches division
div :i ::= <anything>:a ?(a.__class__ == Div) => '(('+a.left.rec(i)+')/('+a.right.rec(i)+'))'

# Matches Ellipsis singleton (used for slicing N-dimensional objects)
ellipsis :i ::= <anything>:a ?(a.__class__ == Ellipsis) => '...'

# FIXME: Do we need this?
emptynode :i ::= <anything>:a ?(a.__class__ == EmptyNode) => ''

# Matches the dynamic execution of a string, file or piece of code
exec :i ::= <anything>:a ?(a.__class__ == Exec) ?(a.globals is None) ?(a.locals is None) => 'exec('+a.expr.rec(i)+')'
          | <anything>:a ?(a.__class__ == Exec) ?(a.globals is None) ?(not a.locals is None) => 'exec('+a.expr.rec(i)+', '+a.locals.rec(i)+')'
          | <anything>:a ?(a.__class__ == Exec) ?(not a.globals is None) ?(not a.locals is None) => 'exec('+a.expr.rec(i)+', '+a.globals.rec(i)+', '+a.locals.rec(i)+')'

# Don't know what this does :( Current plan: Keep testing code until we
# come across something that uses it, then study that code to see what
# it is
expression :i ::= <anything>:a ?(a.__class__ == Expression) => 'FAIL'

# Matches integer division
floordiv :i ::= <anything>:a ?(a.__class__ == FloorDiv) => '(' + a.left.rec(i) + ' // ' + a.right.rec(i) + ')'

# Matches for loops
for :i ::= <anything>:a ?(a.__class__ == For) ?(a.else_ is None) => 'for '+a.assign.rec(i)+' in '+a.list.rec(i)+\""":\n\"""+a.body.rec(i+1)
         | <anything>:a ?(a.__class__ == For) ?(not a.else_ is None) => 'for '+a.assign.rec(i)+' in '+a.list.rec(i)+\""":\n\"""+a.body.rec(i+1)+\"""\n\"""+(i*'\t')+\"""else:\n\"""+a.else_.rec(i+1)

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

function :i ::= <anything>:a ?(a.__class__ == Function) ?(a.decorators is None) ?(a.varargs is None) ?(a.kwargs is None) ?(a.doc is None) => 'def '+a.name+'('+', '.join(tuple_args(a.argnames)[::-1][len(a.defaults):][::-1]+([a.argnames[::-1][x]+'='+y.rec(i) for x,y in enumerate(a.defaults[::-1])][::-1]))+\"""):\"""+a.code.rec(i+1)
              | <anything>:a ?(a.__class__ == Function) ?(a.decorators is None) ?(a.varargs is None) ?(a.kwargs is None) ?(not a.doc is None) => 'def '+a.name+'('+', '.join(tuple_args(a.argnames)[::-1][len(a.defaults):][::-1]+([a.argnames[::-1][x]+'='+y.rec(i) for x,y in enumerate(a.defaults[::-1])][::-1]))+\"""):\n\"""+('\t'*(i+1))+pick_quotes(a.doc)+a.code.rec(i+1)
              | <anything>:a ?(a.__class__ == Function) ?(a.decorators is None) ?(a.varargs is None) ?(not a.kwargs is None) ?(a.doc is None) => 'def '+a.name+'('+', '.join(tuple_args(a.argnames)[::-1][len(a.defaults)+1:][::-1]+([a.argnames[-2::-1][x]+'='+y.rec(i) for x,y in enumerate(a.defaults[::-1])][::-1])+['**'+a.argnames[-1]])+\"""):\"""+a.code.rec(i+1)
              | <anything>:a ?(a.__class__ == Function) ?(a.decorators is None) ?(a.varargs is None) ?(not a.kwargs is None) ?(not a.doc is None) => 'def '+a.name+'('+', '.join(tuple_args(a.argnames)[::-1][len(a.defaults)+1:][::-1]+([a.argnames[-2::-1][x]+'='+y.rec(i) for x,y in enumerate(a.defaults[::-1])][::-1])+['**'+a.argnames[-1]])+\"""):\n\"""+('\t'*(i+1))+pick_quotes(a.doc)+a.code.rec(i+1)
              | <anything>:a ?(a.__class__ == Function) ?(a.decorators is None) ?(not a.varargs is None) ?(a.kwargs is None) ?(a.doc is None) => 'def '+a.name+'('+', '.join(tuple_args(a.argnames)[::-1][len(a.defaults)+1:][::-1]+([a.argnames[-2::-1][x]+'='+y.rec(i) for x,y in enumerate(a.defaults[::-1])][::-1])+['*'+a.argnames[-1]])+\"""):\"""+a.code.rec(i+1)              
              | <anything>:a ?(a.__class__ == Function) ?(a.decorators is None) ?(not a.varargs is None) ?(a.kwargs is None) ?(not a.doc is None) => 'def '+a.name+'('+', '.join(tuple_args(a.argnames)[::-1][len(a.defaults)+1:][::-1]+([a.argnames[-2::-1][x]+'='+y.rec(i) for x,y in enumerate(a.defaults[::-1])][::-1])+['*'+a.argnames[-1]])+\"""):\n\"""+('\t'*(i+1))+pick_quotes(a.doc)+a.code.rec(i+1)
              | <anything>:a ?(a.__class__ == Function) ?(a.decorators is None) ?(not a.varargs is None) ?(not a.kwargs is None) ?(a.doc is None) => 'def '+a.name+'('+', '.join(tuple_args(a.argnames)[::-1][len(a.defaults)+2:][::-1]+([a.argnames[-3::-1][x]+'='+y.rec(i) for x,y in enumerate(a.defaults[::-1])][::-1])+['*'+a.argnames[-2], '**'+a.argnames[-1]])+\"""):\"""+a.code.rec(i+1)
              | <anything>:a ?(a.__class__ == Function) ?(a.decorators is None) ?(not a.varargs is None) ?(not a.kwargs is None) ?(not a.doc is None) => 'def '+a.name+'('+', '.join(tuple_args(a.argnames)[::-1][len(a.defaults)+2:][::-1]+([a.argnames[-3::-1][x]+'='+y.rec(i) for x,y in enumerate(a.defaults[::-1])][::-1])+['*'+a.argnames[-2], '**'+a.argnames[-1]])+\"""):\n\"""+('\t'*(i+1))+pick_quotes(a.doc)+a.code.rec(i+1)
              | <anything>:a ?(a.__class__ == Function) ?(not a.decorators is None) ?(a.varargs is None) ?(a.kwargs is None) ?(a.doc is None) => a.decorators.rec(i)+\"""\n\"""+(i*'\t')+'def '+a.name+'('+', '.join(tuple_args(a.argnames)[::-1][len(a.defaults):][::-1]+([a.argnames[::-1][x]+'='+y.rec(i) for x,y in enumerate(a.defaults[::-1])][::-1]))+\"""):\"""+a.code.rec(i+1)
              | <anything>:a ?(a.__class__ == Function) ?(not a.decorators is None) ?(a.varargs is None) ?(a.kwargs is None) ?(not a.doc is None) => a.decorators.rec(i)+\"""\n\"""+(i*'\t')+'def '+a.name+'('+', '.join(tuple_args(a.argnames)[::-1][len(a.defaults):][::-1]+([a.argnames[::-1][x]+'='+y.rec(i) for x,y in enumerate(a.defaults[::-1])][::-1]))+\"""):\n\"""+('\t'*(i+1))+pick_quotes(a.doc)+a.code.rec(i+1)
              | <anything>:a ?(a.__class__ == Function) ?(not a.decorators is None) ?(a.varargs is None) ?(not a.kwargs is None) ?(a.doc is None) => a.decorators.rec(i)+\"""\n\"""+(i*'\t')+'def '+a.name+'('+', '.join(tuple_args(a.argnames)[::-1][len(a.defaults)+1:][::-1]+([a.argnames[-2::-1][x]+'='+y.rec(i) for x,y in enumerate(a.defaults[::-1])][::-1])+['**'+a.argnames[-1]])+\"""):\"""+a.code.rec(i+1)
              | <anything>:a ?(a.__class__ == Function) ?(not a.decorators is None) ?(a.varargs is None) ?(not a.kwargs is None) ?(not a.doc is None) => a.decorators.rec(i)+\"""\n\"""+(i*'\t')+'def '+a.name+'('+', '.join(tuple_args(a.argnames)[::-1][len(a.defaults)+1:][::-1]+([a.argnames[-2::-1][x]+'='+y.rec(i) for x,y in enumerate(a.defaults[::-1])][::-1])+['**'+a.argnames[-1]])+\"""):\n\"""+('\t'*(i+1))+pick_quotes(a.doc)+a.code.rec(i+1)
              | <anything>:a ?(a.__class__ == Function) ?(not a.decorators is None) ?(not a.varargs is None) ?(a.kwargs is None) ?(a.doc is None) => a.decorators.rec(i)+\"""\n\"""+(i*'\t')+'def '+a.name+'('+', '.join(tuple_args(a.argnames)[::-1][len(a.defaults)+1:][::-1]+([a.argnames[-2::-1][x]+'='+y.rec(i) for x,y in enumerate(a.defaults[::-1])][::-1])+['*'+a.argnames[-1]])+\"""):\"""+a.code.rec(i+1)
              | <anything>:a ?(a.__class__ == Function) ?(not a.decorators is None) ?(not a.varargs is None) ?(a.kwargs is None) ?(not a.doc is None) => a.decorators.rec(i)+\"""\n\"""+(i*'\t')+'def '+a.name+'('+', '.join(tuple_args(a.argnames)[::-1][len(a.defaults)+1:][::-1]+([a.argnames[-2::-1][x]+'='+y.rec(i) for x,y in enumerate(a.defaults[::-1])][::-1])+['*'+a.argnames[-1]])+\"""):\n\"""+('\t'*(i+1))+pick_quotes(a.doc)+a.code.rec(i+1)
              | <anything>:a ?(a.__class__ == Function) ?(not a.decorators is None) ?(not a.varargs is None) ?(not a.kwargs is None) ?(a.doc is None) => a.decorators.rec(i)+\"""\n\"""+(i*'\t')+'def '+a.name+'('+', '.join(tuple_args(a.argnames)[::-1][len(a.defaults)+2:][::-1]+([a.argnames[-3::-1][x]+'='+y.rec(i) for x,y in enumerate(a.defaults[::-1])][::-1])+['*'+a.argnames[-2], '**'+a.argnames[-1]])+\"""):\"""+a.code.rec(i+1)
              | <anything>:a ?(a.__class__ == Function) ?(not a.decorators is None) ?(not a.varargs is None) ?(not a.kwargs is None) ?(not a.doc is None) => a.decorators.rec(i)+\"""\n\"""+(i*'\t')+'def '+a.name+'('+', '.join(tuple_args(a.argnames)[::-1][len(a.defaults)+2:][::-1]+([a.argnames[-3::-1][x]+'='+y.rec(i) for x,y in enumerate(a.defaults[::-1])][::-1])+['*'+a.argnames[-2], '**'+a.argnames[-1]])+\"""):\n\"""+('\t'*(i+1))+pick_quotes(a.doc)+a.code.rec(i+1)

# Matches list-generating expressions
genexpr :i ::= <anything>:a ?(a.__class__ == GenExpr) => '('+a.code.rec(i)+')'

# Matches the loops of a list-generating expression
genexprfor :i ::= <anything>:a ?(a.__class__ == GenExprFor) => 'for '+a.assign.rec(i)+' in '+a.iter.rec(i)+' '.join([n.rec(i) for n in a.ifs])

# Matches any conditions on members in a list-generating expression
genexprif :i ::= <anything>:a ?(a.__class__ == GenExprIf) => 'if '+a.test.rec(i)

# Matches the body of a list-generating expression
genexprinner :i ::= <anything>:a ?(a.__class__ == GenExprInner) => a.expr.rec(i)+' '+' '.join([n.rec(i) for n in a.quals])

# Matches the retrieval of an object's attribute
getattr :i ::= <anything>:a ?(a.__class__ == Getattr) => a.expr.rec(i)+'.'+a.attrname

# Matches the injection of a variable from a parent namespace
global :i ::= <anything>:a ?(a.__class__ == Global) => 'global '+', '.join(a.names)

# Matches if, elif and else conditions
if :i ::= <anything>:a ?(a.__class__ == If) ?(len(a.tests) == 1) ?(a.else_ is None) => 'if '+a.tests[0][0].rec(i)+\""":\n\"""+a.tests[0][1].rec(i+1)
        | <anything>:a ?(a.__class__ == If) ?(len(a.tests) == 1) ?(not a.else_ is None) => 'if '+a.tests[0][0].rec(i)+\""":\n\"""+a.tests[0][1].rec(i+1)+\"""\n\"""+(i*'\t')+\"""else:\n\"""+a.else_.rec(i+1)
        | <anything>:a ?(a.__class__ == If) ?(len(a.tests) > 1) ?(a.else_ is None) => 'if '+a.tests[0][0].rec(i)+\""":\n\"""+a.tests[0][1].rec(i+1)+''.join([\"""\n\"""+('\t'*i)+'elif '+n[0].rec(i)+\""":\n\"""+n[1].rec(i+1) for n in a.tests[1:]])
        | <anything>:a ?(a.__class__ == If) ?(len(a.tests) > 1) ?(not a.else_ is None) => 'if '+a.tests[0][0].rec(i)+\""":\n\"""+a.tests[0][1].rec(i+1)+''.join([\"""\n\"""+('\t'*i)+'elif '+n[0].rec(i)+\""":\n\"""+n[1].rec(i+1) for n in a.tests[1:]])+\"""\n\"""+(i*'\t')+\"""else:\n\"""+a.else_.rec(i+1)

ifexp :i ::= <anything>:a ?(a.__class__ == IfExp) => '(' + a.then.rec(i) + ') if (' + a.test.rec(i) + ') else (' + a.else_.rec(i) + ')'

# Matches the access of external modules
import :i ::= <anything>:a ?(a.__class__ == Import) => 'import '+', '.join(import_match(a.names))

invert :i ::= <anything>:a ?(a.__class__ == Invert) => '(~('+a.expr.rec(i)+'))'

# Matches a key/value pair in an argument list
keyword :i ::= <anything>:a ?(a.__class__ == Keyword) => a.name+'='+a.expr.rec(i)

# Matches anonymous functions
# FIXME: What do the flags represent?
lambda :i ::= <anything>:a ?(a.__class__ == Lambda) => 'lambda '+set_defaults(a.argnames, [n.rec(i) for n in a.defaults])+': '+a.code.rec(i)

# Matches leftwards bit shifts
leftshift :i ::= <anything>:a ?(a.__class__ == LeftShift) => '(('+a.left.rec(i)+')<<('+a.right.rec(i)+'))'

# Matches a mutable, ordered collection 
list :i ::= <anything>:a ?(a.__class__ == List) => '['+', '.join([n.rec(i) for n in a.nodes])+']'

# Matches lists-creating expressions
listcomp :i ::= <anything>:a ?(a.__class__ == ListComp) => '['+a.expr.rec(i)+' '.join([n.rec(i) for n in a.quals])+']'

# Matches transformations applied to existing lists in generating expressions
listcompfor :i ::= <anything>:a ?(a.__class__ == ListCompFor) => ' for '+a.assign.rec(i)+' in '+a.list.rec(i)+''.join([n.rec(i) for n in a.ifs])

# Matches selection conditions in list-generating expressions
listcompif :i ::= <anything>:a ?(a.__class__ == ListCompIf) => ' if '+a.test.rec(i)


# Matches remainder functions (the remainder of the left after dividing
# by the right)
mod :i ::= <anything>:a ?(a.__class__ == Mod) => '(('+a.left.rec(i)+') % ('+a.right.rec(i)+'))'

# Modules contain a Stmt node, and optionally a doc string
# We want the doc string (if it has one) followed by the Stmt
module :i ::= <anything>:a ?(a.__class__ == Module) ?(a.doc is None)    => a.node.rec(i)
            | <anything>:a ?(a.__class__ == Module) ?(a.doc is not None) => pick_quotes(a.doc)+a.node.rec(i)

# Matches multiplication
mul :i ::= <anything>:a ?(a.__class__ == Mul) => '(('+a.left.rec(i)+') * ('+a.right.rec(i)+'))'

# Matches the use of a variable name
name :i ::= <anything>:a ?(a.__class__ == Name) => a.name

# Matches the negation of a boolean
not :i ::= <anything>:a ?(a.__class__ == Not) => '(not ('+a.expr.rec(i)+'))'

# Matches a chain of logical OR operations on booleans
or :i ::= <anything>:a ?(a.__class__ == Or) => '(('+') or ('.join([n.rec(i) for n in a.nodes])+'))'

# Matches a placeholder where indentation requires a code block but no
# code is needed
pass :i ::= <anything>:a ?(a.__class__ == Pass) => 'pass'

# Matches exponentiation
power :i ::= <anything>:a ?(a.__class__ == Power) => '(('+a.left.rec(i)+')**('+a.right.rec(i)+'))'

# Matches outputting text (without a newline)
print :i ::= <anything>:a ?(a.__class__ == Print) ?(a.dest is None) => 'print '+', '.join([n.rec(i) for n in a.nodes])+','
           | <anything>:a ?(a.__class__ == Print) => 'print >> '+a.dest.rec(i)+', '+', '.join([n.rec(i) for n in a.nodes])+','

# Matches outputting text with a newline
printnl :i ::= <anything>:a ?(a.__class__ == Printnl) ?(a.dest is None) => 'print '+', '.join([n.rec(i) for n in a.nodes])
             | <anything>:a ?(a.__class__ == Printnl) => 'print >> '+a.dest.rec(i)+', '+', '.join([n.rec(i) for n in a.nodes])

# Matches error passing
raise :i ::= <anything>:a ?(a.__class__ == Raise) => 'raise '+', '.join([t[0] for t in [[e] for n,e in enumerate([a.expr3,a.expr2,a.expr1]) if e is not None or any([a.expr1,a.expr2,a.expr3][-(n+1):])] if (t[0] is not None and t.__setitem__(0,t[0].rec(i))) or (t[0] is None and t.__setitem__(0, 'None')) or True][::-1])

# Matches the passing of return values from functions, etc.
return :i ::= <anything>:a ?(a.__class__ == Return) => 'return '+a.value.rec(i)

rightshift :i ::= <anything>:a ?(a.__class__ == RightShift) => '(('+a.left.rec(i)+')>>('+a.right.rec(i)+'))'

# Matches a subset of an ordered sequence
# We want the upper and lower boundaries if present, subscripting the
# sequence expression with them, separated by a colon (blank for None)
slice :i ::= <anything>:a ?(a.__class__ == Slice) ?(a.upper is None) ?(a.lower is None) => a.expr.rec(i)+'[:]'
           | <anything>:a ?(a.__class__ == Slice) ?(a.upper is None) ?(not a.lower is None) => a.expr.rec(i)+'['+a.lower.rec(i)+':]'
           | <anything>:a ?(a.__class__ == Slice) ?(not a.upper is None) ?(a.lower is None) => a.expr.rec(i)+'[:'+a.upper.rec(i)+']'
           | <anything>:a ?(a.__class__ == Slice) ?(not a.upper is None) ?(not a.lower is None) => a.expr.rec(i)+'['+a.lower.rec(i)+':'+a.upper.rec(i)+']'

sliceobj :i ::= <anything>:a ?(a.__class__ == Sliceobj) => ':'.join([n.rec(i) for n in a.nodes])

# Stmt is a statement (code block), containing a list of nodes
# We want each node to be on a new line with i tabs as indentation
# We make a special case if the 'statement' is a constant None, since this ends
# up putting 
stmt :i ::= <anything>:a ?(a.__class__ == Stmt) => (\"""\n\"""+'\t'*i)+(\"""\n\"""+'\t'*i).join([n.rec(i)+';'*len([b for b in [0] if len(a.nodes)>e+1 and a.nodes[e+1].__class__ == Discard and a.nodes[e+1].expr.__class__ == Const and a.nodes[e+1].expr.value is None]) for e,n in enumerate(a.nodes)])

# Matches subtraction
sub :i ::= <anything>:a ?(a.__class__ == Sub) => '(('+a.left.rec(i)+') - ('+a.right.rec(i)+'))'

# Matches extracting item(s) from a collection based on an index or key
subscript :i ::= <anything>:a ?(a.__class__ == Subscript) => a.expr.rec(i)+'['+', '.join([s.rec(i) for s in a.subs])+']'

# Matches try/except blocks
tryexcept :i ::= <anything>:a ?(a.__class__ == TryExcept) ?(a.else_ is None) => 'try:'+a.body.rec(i+1)+\"""\n\"""+i*'\t'+(\"""\n\"""+i*'\t').join(['except'+' '.join([' '+e.rec(i) for e in [h[0]] if not e is None])+', '.join([', '+n.rec(i) for n in [h[1]] if not n is None])+':'+h[2].rec(i+1) for h in a.handlers])
               | <anything>:a ?(a.__class__ == TryExcept) ?(not a.else_ is None) => 'try:'+a.body.rec(i+1)+\"""\n\"""+i*'\t'+(\"""\n\"""+i*'\t').join(['except '+' '.join([' '+e.rec(i) for e in [h[0]] if not e is None])+', '.join([', '+n.rec(i) for n in [h[1]] if not n is None])+':'+h[2].rec(i+1) for h in a.handlers])+\"""\n\"""+'\t'*i+\"""else:\"""+a.else_.rec(i+1)

# Catches finally clauses on try/except blocks
tryfinally :i ::= <anything>:a ?(a.__class__ == TryFinally) ?(a.body.__class__ == TryExcept) => a.body.rec(i)+\"""\n\"""+i*'\t'+'finally:'+a.final.rec(i+1)
                | <anything>:a ?(a.__class__ == TryFinally) => 'try:'+a.body.rec(i+1)+\"""\n\"""+i*'\t'+'finally:'+a.final.rec(i+1)

# Matches an immutable, ordered collection
tuple :i ::= <anything>:a ?(a.__class__ == Tuple) ?(len(a.nodes) > 1) => '('+', '.join([n.rec(i) for n in a.nodes])+')'
           | <anything>:a ?(a.__class__ == Tuple) ?(len(a.nodes) == 1) => '('+a.nodes[0].rec(i)+',)'
           | <anything>:a ?(a.__class__ == Tuple) ?(len(a.nodes) == 0) => '()'

# Matches a positive operator
unaryadd :i ::= <anything>:a ?(a.__class__ == UnaryAdd) => '(+'+a.expr.rec(i)+')'

# Matches a negative operator
unarysub :i ::= <anything>:a ?(a.__class__ == UnarySub) => '(-'+a.expr.rec(i)+')'

# Matches a while loop
while :i ::= <anything>:a ?(a.__class__ == While) ?(a.else_ is None) => 'while '+a.test.rec(i)+\""":\n\"""+a.body.rec(i+1)
           | <anything>:a ?(a.__class__ == While) ?(not a.else_ is None) => 'while '+a.test.rec(i)+\""":\n\"""+a.body.rec(i+1)+\"""\n\"""+(i*'\t')+\"""else:\n\"""+a.else_.rec(i+1)

# Matches object-style try/catch
with :i ::= <anything>:a ?(a.__class__ == With) ?(a.vars is not None) => 'with '+a.expr.rec(i)+' as '+a.vars.rec(i)+\""":\n\"""+('\t'*(i+1))+a.body.rec(i+1)
          | <anything>:a ?(a.__class__ == With) => 'with '+a.expr.rec(i)+\""":\n\"""+('\t'*(i+1))+a.body.rec(i+1)

# Matches generator values
yield :i ::= <anything>:a ?(a.__class__ == Yield) => 'yield '+a.value.rec(i)

"""

# These are the objects which will be available to the matcher
args = globals()
args['constants'] = [str, int, float, complex]
args['import_match'] = import_match
args['tuple_args'] = tuple_args
args['is_del'] = is_del
args['pick_quotes'] = pick_quotes

# grammar is the class, instances of which can match using grammar_def
stripped = strip_comments(grammar_def)
grammar = OM.makeGrammar(stripped, args)

# Give every AST node access to the grammar
Node.grammar = grammar

def parse(code):
	"""This parses the given code using Python's compiler module, but
	with our monkey patching applied to the nodes."""
	return compiler.parse(code)

# Cleanup the namespace a little
del stripped
del args

if __name__ == '__main__':
		print parse('1 + 2').rec(0)
