#!/usr/bin/env python

"""
This replaces Python's boolean logic keywords with method calls. This changes
the language semantics and thus could change the behaviour of code, which is why
it is kept separate from the main Diet Python translations.

What we want to do is get rid of keywords, like "a and b", and replace them with
a more late-bound implementation "a.__logand__(b)". This is similar to Python's
use of "__and__" for "+", "__sub__" for "-" and so on, although the main Python
implementations do not support such transformations for the boolean operators.

NOTE: We put "log" in the method names to prevent conflict with the bitwise
logic.
"""

def replace_ors(node):
	"""Replace all occurances of "or" with calls to "__logor__"."""
	if node.__class__ == Or:
		# Or nodes can contain 2 or more nodes, we have to handle them all. We
		# also have to respect the premature optimisation that if any is True
		# then the rest aren't evaluated. Thus the expression a or b or c or d
		# cannot be turned into simply a.__logor__(b).__logor__(c).__logor__(d)
		# because this will evaluate them all. Instead we need to pass in the
		# expressions as strings, and eval them if needed, so our call becomes
		# a.__logor__('''b.__logor__("""c.__logor__('d')""")''')

		# We replace Ors recursively. If there's only 2 nodes to compare then
		# we convert the first to a boolean, then recurse our tree
		# transformations through the second node, then pretty print the result
		# into a string which we wrap with a Const node and pass into a method
		# call of __logor__ on the boolean of the first node
		if len(node.nodes) == 2:
			return CallFunc(Getattr(CallFunc(Name('bool'),[node.nodes[0]]), \
				Name('__logor__')), [Const(apply(node.nodes[-1]]).rec(0))])
		# Otherwise we build a nested series of ors (ie. "a or b or c or d"
		# becomes "a or (b or (c or d))") which we do recursively, and then we
		# apply ourselves to it recursively to complete the translation
		else:
			return CallFunc(Getattr(CallFunc(Name('bool'),[node.nodes[0]]), \
				Name('__logor__')), [Const(apply(Or(node.nodes[1:])).rec(0))])
	else:
		# If we've not got an Or node then simply recurse
		try:
			# map our transformation to members of any lists or tuples
			if type(node) in [type([]), type((0,1))]:
				return map(replace_ors, node)
			# Stmt nodes are weird: their contents is [nodes] but asList only
			# gives nodes, breaking the *varargs technique used below
			if node.__class__ == Stmt:
				return Stmt(map(replace_ors, node.asList()))
			# If we're not in a list or Stmt, return a new instance of our
			# class, with transformed children
			return node.__class__(*map(replace_ors, node.asList()))
		except:
			# If an error occurs it's because strings, numbers, None, etc. don't
			# have an asList method. Since they're leaves, just return them.
			return node

def replace_ands(node):
	"""Replace all occurances of "and" with calls to "__logand__"."""
	if node.__class__ == And:
		# We've got to be careful that we don't evaluate any expressions after
		# one which returns False, since this would break existing code that
		# depends on the assumption that such expressions will not be evaluated

		# If we have exactly 2 expressions then we simply build a string out of
		# the second and send it to the boolean value of the first, which will
		# presumably eval it if needed
		if len(node.nodes) == 2:
			return CallFunc(Getattr(CallFunc(Name('bool'),node.nodes[0]),
				Name('__logand__')), [Const(apply(node.nodes[-1]).rec(0))])
		else:
			return CallFunc(Getattr(CallFunc(Name('bool'),node.nodes[0]),
				Name('__logand__')), [Const(apply(And(node.nodes[1:])).rec(0))])
	else:
		# If we've not got an And node then simply recurse
		try:
			# map our transformation to members of any lists or tuples
			if type(node) in [type([]), type((0,1))]:
				return map(replace_ands, node)
			# Stmt nodes are weird: their contents is [nodes] but asList only
			# gives nodes, breaking the *varargs technique used below
			if node.__class__ == Stmt:
				return Stmt(map(replace_ands, node.asList()))
			# If we're not in a list or Stmt, return a new instance of our
			# class, with transformed children
			return node.__class__(*map(replace_ands, node.asList()))
		except:
			# If an error occurs it's because strings, numbers, None, etc. don't
			# have an asList method. Since they're leaves, just return them.
			return node

def replace_nots(node):
	"""Replace all occurances of "not" with calls to "__lognot__"."""
	if node.__class__ == Not:
		# We replace "not foo" with "bool(foo).__lognot__()
		return CallFunc(Getattr(CallFunc(Name('bool'),[node.expr]), Name('__lognot__')), [])
	else:
		# If we've not got an Not node then simply recurse
		try:
			# map our transformation to members of any lists or tuples
			if type(node) in [type([]), type((0,1))]:
				return map(replace_nots, node)
			# Stmt nodes are weird: their contents is [nodes] but asList only
			# gives nodes, breaking the *varargs technique used below
			if node.__class__ == Stmt:
				return Stmt(map(replace_nots, node.asList()))
			# If we're not in a list or Stmt, return a new instance of our
			# class, with transformed children
			return node.__class__(*map(replace_nots, node.asList()))
		except:
			# If an error occurs it's because strings, numbers, None, etc. don't
			# have an asList method. Since they're leaves, just return them.
			return node

def replace_logic(node):
	"""Replaces all boolean logic under this node with method calls."""
	if node.__class__ == Or:
		return replace_ors(node)
	elif node.__class__ == And:
		return replace_ands(node)
	elif node.__class__ == Not:
		return replace_nots(node)
	else:
		try:
			# map our transformation to members of any lists or tuples
			if type(node) in [type([]), type((0,1))]:
				return map(replace_logic, node)
			# Stmt nodes are weird: their contents is [nodes] but asList only
			# gives nodes, breaking the *varargs technique used below
			if node.__class__ == Stmt:
				return Stmt(map(replace_logic, node.asList()))
			# If we're not in a list or Stmt, return a new instance of our
			# class, with transformed children
			return node.__class__(*map(replace_logic, node.asList()))
		except:
			# If an error occurs it's because strings, numbers, None, etc. don't
			# have an asList method. Since they're leaves, just return them.
			return node
