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

from transformer import grammar_def, strip_comments

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
	# The docstring (if it has one), at i+1 indentation
	if f.doc is not None:
		new_def = new_def + '\n' + (i+1)*'\t' + \
			transformer.pick_quotes(f.doc)
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
	
def function_data(tree):
	pass

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
function :i ::= 
