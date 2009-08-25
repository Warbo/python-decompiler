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

import os
import sys
from python_rewriter.base import grammar_def, strip_comments
from python_rewriter.nodes import *
from pymeta.grammar import OMeta

def assign_populate(tree):
	"""Takes the values of any assignments made and applies them to the
	name nodes they apply to."""
	# If this is a Node then we can get data from it
	if isinstance(tree, Node):
		# If we've found an assign then we need to find out what it's
		# assigning and what it's being bound to
		if tree.__class__ == Assign:
			def get_names(node):
				names = []
				if node.__class__ == AssName \
					and node.flags == 'OP_ASSIGN':
					names.append(node.name)
				elif node.__class__ == AssName \
					and node.flags == 'OP_DELETE':
					names.append('-'+node.name)
				for n in .nodes:
				if n.__class__ == AssName:
					to_ass.append(AssName.name)
				elif n.__class__ == 
	elif type(tree) == type([]):
		new_list = []
		for item in tree:
			new_list.append(assign_populate(item))
		return new_list
	elif type(tree) == type(()):
		new_tuple = ()
		for item in tree:
			new_tuple = new_tuple + (assign_populate(item),)
		return new_tuple
	elif type(tree) == type({}):
		new_dictionary = {}
		for k in tree.keys():
			new_dictionary[k] = assign_populate(tree[k])
		return new_dictionary
	else:
		return tree
		
def function_writer(f, i):
	"""Returns a definition of the given function f, at indentation
	level i, which makes as much of the definition explicit as possible.
	"""
	new_def = ''		# This will hold our eventual definition
	# If we have decorators...
	if f.decorators is not None:
		# Then recurse through each one and add it to our definition
		## FIXME: Decorators are ripe for throwing away:
		# @foo
		# def bar():
		#	pass
		# is the same as:
		# def bar():
		#	pass
		# bar = foo(bar)
		# Look into how to do this universally
		new_def = new_def + ('\n'+(i*'\t')).join(\
			[d.rec(i) for d in f.decorators])
		new_def = new_def + '\n'+(i*'\t')
	# Make a copy of the argument names so we can fiddle with it easily
	raw_args = f.argnames[:]
	final_args = []		# This will store our eventual arguments tuple
	
	## PROCESS ARGUMENTS IN REVERSE ORDER
	# This means we start with keyword dictionary arguments (ie. **foo)
	if f.kwargs is not None:
		# kwargs is a number, presumably the number of kwargs
		for x in range(f.kwargs):
			# These MUST appear at the end of the list, so pop the last
			# names from raw_args
			final_args.append('**'+raw_args.pop())
	# If an argument tuple has been passed (ie. *foo) then this will
	# precede a kwargs argument, or else be at the end of the tuple.
	# Either way the next pop from raw_args will get it
	if f.varargs is not None:
		for x in range(f.varargs):
			final_args.append('*'+raw_args.pop())
	# If any arguments have defaults (ie. foo=bar) then these MUST come
	# after arguments with no defaults, so we reverse the defaults
	# (using a slice with step -1) and pop the matching raw_args
	for default in f.defaults[::-1]:
		final_args.append(raw_args.pop()+'='+default.rec(i))
	# Now if there's anything left it will be a regular argument, so
	# keep popping until there are no more left
	while len(raw_args) > 0:
		final_args.append(raw_args.pop())
	# Now reverse the argument list to get the correct order
	final_args = final_args[::-1]
	
	# Start the core function definition
	# The definition line
	new_def = new_def+'def '+f.name+'('+', '.join(final_args)+'):'
	
	# Add the docstring (if it has one)
	new_def = new_def + '\n' + (i+1)*'\t' + \
			f.name+'.__setattr__("__doc__", '+ \
			transformer.pick_quotes(f.doc)+')'
	new_def = new_def + '\n' + (i+1)*'\t' + \
			f.name+'.__setattr__("func_doc", '+ \
			transformer.pick_quotes(f.doc)+')'
	
	# Add  the function's name
	new_def = new_def + '\n' + (i+1)*'\t' + \
			f.name+'.__setattr__("__name__", "'+ f.name + '")'
	new_def = new_def + '\n' + (i+1)*'\t' + \
			f.name+'.__setattr__("func_name", "'+ f.name + '")'
	
	# Add the function's module
	if f._module._name is None:
		new_def = new_def + '\n' + (i+1)*'\t' + \
			f.name+'.__setattr__("__module__", None)'
	else:
		new_def = new_def + '\n' + (i+1)*'\t' + \
			f.name+'.__setattr__("__module__", '+f._module._name+')'
	
	# The Stmt of the function's actual contents
	new_def = new_def + f.code.rec(i+1)
	
	## ADD IMPLICIT INTROSPECTION METADATA EXPLICITLY
	# Here we give the newly created function the introspection data
	# that the Python interpreter usually supplies. We do this outside
	# the function definition, ie. we go back to indentation i.
	# This data should have been inserted into the node by a
	# "populate_functions" pass over the AST
	
	# First we need to define a temporary function to assign properties
	new_def = new_def +'\n'+ i*'\t' +'def '+f.name
	# First we add the docstring
	new_def = new_def +'\n'+ i*'\t' +f.name+'.func_doc = '+\
		transformer.pick_quotes(f.doc)
	new_def = new_def +'\n'+ i*'\t' +f.name+'.__doc__ = '+\
		transformer.pick_quotes(f.doc)
	# Then the function's name
	new_def = new_def +'\n'+ i*'\t' +f.name+'.func_name = ' + f.name
	new_def = new_def +'\n'+ i*'\t' +f.name+'.__name__ = ' + f.name
	# Then the module where it's defined
	new_def = new_def +'\n'+ i*'\t' +f.name+'.__module__ = ' + f._mod
	new_def = new_def +'\n'+ i*'\t' +f.name+
	
def populate_functions(tree, module):
	"""Recursively add metadata to functions in the given AST."""
	# We're interested in functions
	if tree.__class__ == Function:
		# The module we've been passed is where this function's defined
		tree._module = module
		# The "code" of a function is implementation-dependent, and even
		# then subject to change, so we should be able to do what we
		# like with it and only unportable, CPython-specific (ie. bad)
		# code will be affected, if any exists
		tree._code = ''
		tree._globals = module.globals

def populate_modules(tree, module=None, level=0):
	"""Recursively add metadata to modules in the given AST."""
	# Attempt to add this module as an attribute to the given node
	# Needs to be try/except enclosed since we may have a type, rather
	# than an object, and types are builtin crap which don't support
	# attribute assignment
	try:
		tree._module = module
	except TypeError:
		pass
		
	# These are the names of the possible attributes we may be
	# interested in
	attributes = ['code', 'locals', 'bases', 'kwargs', 'nodes', \
		'real', 'tests', 'ops', 'dest', 'dstar_args', 'modname', \
		'isnumeric', 'star_args', 'name', 'level', 'ifs', 'list', \
		'globals', 'defaults', 'right', 'fail', 'isdecimal', \
		'argnames', 'decorators', 'body', 'args', 'attrname', \
		'handlers', 'items', 'assign', 'subs', 'names', 'iter', \
		'imag', 'is_outmost', 'expr', 'value', 'final', \
		'conjugate', 'expr2', 'expr1', 'quals', 'test', 'node', \
		'expr3', 'grammar', 'varargs', 'else_', 'doc', 'flags', \
		'op', 'left']
	
	# Modules are a special case, since they change the module data
	if tree.__class__ == Module:
		# We can forget about the module which this module node's in,
		# since we should have already assigned its metadata which
		# includes it :)
		tree.__setattribute__('_namespace', {})
		# Thus we need to recurse through everything that we care about
		# which may be in this node
		for name in set(attributes).intersection(set(dir(tree))):
			try:
				tree.__setattr__(name, \
					populate_modules(tree.__getattribute__(name), tree))
			except AttributeError:
				pass
		return tree
	
	# We need to populate our module's namespace, so we need to take
	# account of everything that may affect it
	if tree.__class__ == AssName:
		tree._module._namespace[tree.name] = 
	if tree.__class__ == Import:
		for name in tree.names:
			if name[1] is None:
				tree._module._namespace[name[0]] = Module(None, None)
			else:
				tree._module._namespace[name[1]] = Module(None, None)
				
	# If we're not a Module, but we're still a Node, then do the same
	# recursion, but with the module we've been given
	if isinstance(tree, Node):
		for name in set(attributes).intersection(set(dir(tree))):
			try:
				tree.__setattr__(name, \
					populate_modules(tree.__getattribute__(name), \
						module))
			except AttributeError:
				pass
		return tree
	# We may be a list, tuple, dictionary, number or string
	elif type(tree) == type([]):
		# We're a list
		old_list = tree[:]		# Copy it
		new_list = []		# Make a new list to return
		while len(old_list) > 0:
			new_list.append(populate_modules(old_list.pop(0), module))
		return new_list
	elif type(tree) == type(()):
		# We're a tuple
		new_tuple = ()		# Make a new tuple to return
		for item in tree:
			new_tuple = new_tuple + (populate_modules(item, module),)
		return new_tuple
	elif type(tree) == type({}):
		# We're a dictionary
		new_dictionary = {}
		for k in tree.keys():
			new_dictionary[k] = populate_modules(tree[k], module)
		return new_dictionary
	return tree
		

grammar_def = grammar_def + """
# a + b becomes a.__add__(b)
add :i => add :i ::= <anything>:a ?(a.__class__ == Add) => a.left.rec(i)+'.__add__('+a.right.rec(i)+')'

# assert things becomes assert(things)
assert :i ::= <anything>:a ?(a.__class__ == Assert) ?(a.fail is None) => 'assert('+a.test.rec(i)+')'
            | <anything>:a ?(a.__class__ == Assert) ?(not a.fail is None) => 'assert('+a.test.rec(i)+', '+a.fail.rec(i)+')'

# a += b becomes a = a.__add__(b)
# To do this we put the left = left then transform the operation and append it to the end
augassign :i ::= <anything>:a ?(a.__class__ == AugAssign) => a.node.rec(i)+' = '+eval('parse('+a.node.rec(i)+a.op[:-1]+a.expr.rec(i)))

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

"""

grammar = OMeta.makeGrammar(grammar_def, globals())

def translate(path_or_text, initial_indent=0):
	if os.exists(path_or_text):
		infile = open(path_or_text, 'r')
		in_text = '\n'.join([line for line in infile.readlines()])
	else:
		in_text = path_or_text
	try:
		tree = parse(in_text)
		tree = assign_populate(tree)
		tree = populate_modules(tree)
		tree = populate_functions(tree)
		matcher = grammar([tree])
		diet_code = matcher.apply('python', initial_indent)
		return diet_code
	except Exception, e:
		print str(e)
		print 'Unable to translate.'
		sys.exit(1)

if __name__ == '__main__':
	if len(sys.argv) == 2:
		print translate(sys.argv[1])
