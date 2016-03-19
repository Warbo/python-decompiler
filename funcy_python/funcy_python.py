"""Funcy Python ("Funky Python") is a language similar to Python but
which is functional.

We can express any Python code as Smalltalk-style message passing, for example:

if a < b:
	print 'foo'

Is equivalent to:

a.__lt__(b).ifTrue('print('foo')')

As long as True and False have the methods:

def a(x):
	exec(x)

def b(x):
	pass

True.ifTrue = a
False.ifTrue = b

In Python, functions become methods by having their first argument (typically
called "self") implicit ly bound to an object. We can be more functional if we
force those bindings to be explicit, and thus:

class A:
	def foo(self, x):
		return str(self)+str(x)
a = A()
a.foo(12)

is equivalent to:

class A:
	pass

def foo(self, x):
	return str(self)+str(x)

a = A()
foo(a, 12)

Now, this is more functional, but we've lost our api. No worries though, since
we can recreate the bound "self" argument without having to rely on an
interpreter to do it for us implicitly:

def foo(self):
	def foo2(x):
		return str(self)+str(x)
	return foo2

a = A()
a.foo = foo(a)
a.foo(12)

Rather than creating a method of a class, of which a is an instance, we have
instead created a closure which contains a in its environment.

You may have noticed that class A has become pretty redundant. We can replace it
with the following:

A = object.__new__()
"""

from python_rewriter.base import grammar

def list_to_pairs(l):
	"""Takes a list and returns nested tail-recursive pairs. For example
	['a','b','c','d'] becomes ('a',('b',('c','d')))."""
	if len(l) < 3:
		return l
	else:
		first = l.pop(0)
		return (first,list_to_pairs(l))
	

funcy_grammar = """
# This grammar turns a Diet Python AST into Funcy Python

thing :i ::= <super i>

stmt :i ::= <anything>:a ?(a.__class__ == Stmt) a.nodes

"""
