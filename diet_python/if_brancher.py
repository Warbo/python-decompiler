#!/usr/bin/env python

"""Transforms a Python AST such that if-conditions are replaced by
Smalltalk-style messages. For instance, take the following Python code:

if a < b:
	print "a is smaller"
elif b < a:
	print "b is smaller"
else:
	print "both equal"

First we can replace the syntactic sugar of "elif" to give:

if a < b:
	print "a is smaller"
else:
	if b < a:
		print "b is smaller"
	else:
		print "both equal"
 
 Now, to do this in an Object Oriented way we need the following:

def first_path(first, second):
	exec(first)

def second_path(first, second):
	exec(second)

These encapsulate the behaviour of "if" and "else" respectively. Now we need to
replace the clumsy expression evaluation with what it actually is: method calls.

The expression "a < b" is, in Python, equivalent to the method call
"a.__lt__(b)". This method returns either a True object or a False object. This
encapsulates all of the functionality needed for our if statements, so let's use
it: We firstly say that:

True.__if__ = first_path
False.__if__ = second_path

Now if we call "True.__if__(x, y)" then x will always be executed. If we
instead run "False.__if__(x, y)" then y will always be executed. Since our
comparisons always give a True or False we can say "(a < b).__if__(x, y)" and,
depending on whether the comparison gives a True or False object, the code x or
y will be executed. To handle arbitrary objects we need to cast the comparison
to a True or False, but casting in Python is implemented as functions too so
that's fine :) To rewrite the above example using this new style would yield:

(a<b).__if__(
	'print "a is smaller"',
	'(b<a).__if__(
		"print \"b is smaller\"",
		"print \"both equal\""
	)'
)

This may be less readable than the original, but we can automatically translate
so we don't care. Note that we can't translate back in the general case, since
this style is more general and expressive than the keyword syntax. For example:

(a>(
	(b<c).__if__(
		"print \"c is bigger than b\"\nreturn c",
		"print \"b is bigger then c\"\nreturn b"
	)
)).__if__(
	'print "a is biggest"',
	'print "and is the biggest"'
)

This code would directly translate to the following keyword syntax:

if a > (
	if b < c:
		print "c is bigger than b"
		return c
	else:
		print "b is bigger than c"
		return b
):
	print "a is biggest"
else:
	print "and is biggest"

Now, this is quite clearly syntactically incorrect. We could of course do this:

if max([b,c]) == b:
	print "b is bigger than c"
else:
	print "c is bigger than b"
if a > max([b,c]):
	print "a is biggest"
else:
	print "and is biggest"

but it would be intractable to automatically recognise such things. Note that
we couldn't do it with a lambda either, since lambdas don't allow if statements.
In the general case we'd have to make each condition a function, which would
pollute the namespace, or we could exec and eval strings which, lo and behold,
our new syntax is doing already ;)

A nice effect of doing this transformation is that it makes the "if", "elif"
and "else" keywords completely redundant, so we can throw them away and never
bother implementing them if we don't need to, as long as we have objects and
functions :)
"""

from python_rewriter.nodes import *

def replace_elifs(node):
	"""Takes an AST and replaces the 'elif' conditions in any If nodes,
	recursively."""

	# We want to replace If nodes containing elif clauses, so look for them
	if node.__class__ == If:
		# Take the first (condition,code) pair
		cond1 = node.tests[0]
		# If there are elifs...
		if len(node.tests) > 1:
			# ... replace them with unwrap_if and insert in a new If node
			# (transforming its True and False branches first)
			return If([(cond1[0], replace_elifs(cond1[1]))], \
				unwrap_if(node.tests[1:], replace_elifs(node.else_)))
		else:
			# Otherwise return a new If with the branches transformed
			return If([(cond1[0], replace_elifs(cond1[1]))], \
				replace_elifs(node.else_))
	else:
		# If we've not got an If node then simply recurse
		try:
			# map our transformation to members of any lists or tuples
			if type(node) in [type([]), type((0,1))]:
				return map(replace_elifs, node)
			# Stmt nodes are weird: their contents is [nodes] but asList only
			# gives nodes, breaking the *varargs technique used below
			if node.__class__ == Stmt:
				return Stmt(map(replace_elifs, node.asList()))
			# If we're not in a list or Stmt, return a new instance of our
			# class, with transformed children
			return node.__class__(*map(replace_elifs, node.asList()))
		except:
			# If an error occurs it's because strings, numbers, None, etc. don't
			# have an asList method. Since they're leaves, just return them.
			return node

def unwrap_if(tests, else_):
	"""Returns a recursive set of If nodes which capture the tests and else
	statements given. tests is a list of tuples of the form (condition, code)
	where 'code' is run if 'condition' is true, checking the next pair in the
	list if 'condition' is false. If every condition in the list is false then
	'else_' is run."""
	# Act on a copy of the given (condition,code) pairs
	ts = tests[:]
	# Grab the last test (which, if it fails, leads to the else_)
	if_ = ts.pop()
	# Give this its own If node, with its code as the True branch and else_ as
	# the False branch
	node = If((if_[0], if_[1]), else_)

	# Now loop through the remaining tests, which are elifs
	while len(ts) > 0:
		# Take a test off the end...
		if_ = ts.pop()
		# ... and make it an independent If node, using the previously defined
		# node as the else_
		node = If((if_[0], if_[1]), Stmt([node]))

	# Our node should now be an If with no elifs, with a cascade of Ifs in the
	# else clause(s)
	return node

def replace_ifs(node):
	"""Given an AST node, replaces if statements with calls to __if__."""
	# Get rid of elif statements
	tree = replace_elifs(node)
	# We want to transform If nodes
	if tree.__class__ == If:
		# Call the __if__ method of the condition instead (and recurse through
		# the If's children)
		return CallFunc(Getattr(CallFunc(Name('bool'),[node.tests[0][0]]), \
			Name('__if__')), [replace_ifs(node.tests[0][1]), replace_ifs(node.else_)])
	# If it's not an If node then recurse
	else:
		try:
			# Iterators should get mapped (but NOT strings, hence why we don't
			# use __iter__ as a test at the moment)
			if type(node) in [type([]), type((0,1))]:
				return map(replace_ifs, node)
			# Stmt nodes are a bit weird: they contain a list called nodes so
			# that instantiation is Stmt(nodes), however the asList method
			# doesn't give [nodes], it just gives nodes, which means we can't
			# use the *varargs technique below
			if node.__class__ == Stmt:
				return Stmt(map(replace_ofs, node.asList()))
			# Otherwise just go ahead and create a new node of the same class,
			# with members mapped with this transformation
			return node.__class__(*map(replace_ifs, node.asList()))
		except:
			# If we get an error it's because strings, None, numbers, etc. don't
			# have an asList method. These are leaves anyway, so we don't need
			# to recurse into them
			return node
