from transformer import g
import compiler
from pymeta.runtime import ParseError

class EscapeException(Exception):
	pass

class Test:

	def __init__(self, name, code, deps):
		self.name = name
		self.code = code
		self.deps = deps
		self.result = False
		self.message = self.name + ": Test didn't run"

	def run(self, grammar):
		self.message = self.name + ': '
		if self.code == '':
			self.message = self.message + 'No test set'
			return
		try:
			try:
				tree = str(compiler.parse(self.code))
			except SyntaxError:
				self.message = self.message + """Error in test.\n""" + self.code
				raise EscapeException()
			try:
				matcher = grammar(tree)
				generated = matcher.apply('any')
			except ParseError:
				self.message = self.message + """Error in grammar.\n""" + self.code + """\n\n""" + tree
				raise EscapeException()
			try:
				assert str(compiler.parse(generated)) == tree
			except AssertionError:
				self.message = self.message + """Error, generated code does not match original.\n""" + self.code + """\n\n""" + tree + """\n\n""" + generated
				raise EscapeException()
			except SyntaxError:
				self.message = self.message + """Error in generated code.\n""" + self.code + """\n\n""" + tree + """\n\n""" + generated
				raise EscapeException()
			self.message = self.message + "OK"
			self.result = True
		except EscapeException:
			pass

tests = [\
	Test('Addition','1+2', ['Statement', 'Constant']), \
	Test('And', '1 and True', ['Name', 'Constant']), \
	Test('Assign Attribute', 'x.name = "ex"', ['Statement', 'Name']), \
	Test('Assign Name', """x = 10
del x
del(y)""", ['Name', 'Constant', 'Assign']), \
	Test('Assign Tuple', 'x, y, z = 1, 2, "10"', ['Tuple', 'Name', 'Constant', 'Assign']), \
	Test('Assert', 'assert 10 < 9', ['Compare', 'Constant']), \
	Test('Assign', 'x = y = 10', ['Name', 'Constant', 'Statement']), \
	Test('Augmenting Assign', 'x += 10', ['Statement', 'Name', 'Constant']), \
	Test('Backquote', '', ['Statement']), \
	Test('Bitwise And', '', ['Statement']), \
	Test('Bitwise Or', '', ['Statement']), \
	Test('Bitwise Exclusive Or', '', ['Statement']), \
	Test('Break', """x=0
while True:
	x += 1
	if x == 5:
		break
""", ['Statement']), \
	Test('Function Call', """str(x)
f(*[1,2,3])
g(*x*2)""", ['Statement', 'Name']), \
	Test('Class', """class A(object):
	def __init__(self):
		pass

class B(A):

	def __init__(self):
		pass""", ['Statement']), \
	Test('Compare', 'x < y and 1 == 5 and 2 > 8', ['Name', 'Constant', 'And']), \
	Test('Constant', """1
-5
3.4
-12.45
-8.048e-16
10+5j
u"Unicode"
'SINGLE'
"DOUBLE"
'''Triple'''
"""+'"""SEXTUPLE"""', ['Statement']), \
	Test('Continue', """for x in range(5):
	if x == 2:
		continue
	print str(x)""", ['Statement', 'Name', 'Function Call', 'Compare', 'Constant']), \
	Test('Decorators', """
def a(g):
	return g
@a
def f(x,y):
	print x+y
@dbus.service.signal(dbus_interface='com.example.Sample', signature='us')
def s(self, thing1, thing2):
	print str(thing1)+str(thing2)
""", ['Statement']), \
	Test('Dictionary', """x = 5
a = "s"
y = {a:1, 5:x}
{}
""", ['Statement', 'Name', 'Constant', 'Assign', 'Assign Name']), \
	Test('Discard', '5', ['Statement', 'Constant']), \
	Test('Division', 'x/10', ['Name', 'Constant']), \
	Test('Ellipsis', '', ['Statement']), \
	Test('Expression', '', ['Statement']), \
	Test('Execute', 'exec("x=True")', ['Statement']), \
	Test('Rounded-Down Division', '', ['Statement']), \
	Test('For Loop', """for x in range(5):
	print str(x)
	for a, b in enumerate(range(10)):
		print str(a*b)""", ['Statement']), \
	Test('From', """from os import get_cwd
from sys import exit as Exit
from pygame import draw, mixer as sound, surface""", ['Statement']), \
	Test('Function', """def f(x, y=False, z="TEST", a="ING"):
	if y:
		print x
def g():
	print z
def h((x, (y, q)), z="a", w="b", v="c"):
	\"""Function h.\"""
	print w
def i(*a):
	print str(a)
def j(**a):
	print str(a)
def k(*a, **b):
	print str(a)+str(b)
""", ['Statement']), \
	Test('GenExpr', 'print(x for x in range(5))', ['Statement']), \
	Test('GenExprFor', 'print(x for x in range(5))', ['Statement']), \
	Test('GenExprIf', 'print(x for x in range(5) if x < 2)', ['Statement']), \
	Test('GenExprInner', 'print(x for x in range(5))', ['Statement']), \
	Test('Get Attribute', 'x.name', ['Statement']), \
	Test('Global', """global x
x = 2""", ['Statement']), \
	Test('If', """if x < 2:
	print "a"
elif x > 2:
	print "b"
elif x == 2:
	if y:
		print x
	print "c"
else:
	print 'd'""", ['Statement']), \
	Test('Import', """import os
import sys as System
if True:
	import StringIO
	import pygame, compiler
	import urllib2
print 'x'""", ['Statement']), \
	Test('Keyword', """def f(x, y, a=True, b="h"):
	if a:
		print x+y+b
f('c','d', a=False)""", ['Statement']), \
	Test('Lambda', """f = lambda x, y, a=2: x+y+a*a
lambda: 5*2
lambda x: x*x
filter(lambda x: x>5, range(10))""", ['Statement']), \
	Test('Left Shift', '', ['Statement']), \
	Test('List', """[1,2,3,[1,2,"s"]]
x = []""", ['Statement']), \
	Test('List Comprehension', '[str(x) for x in range(10)]', ['Statement']), \
	Test('List Comprehension For', '[x for x in range(5)]', ['Statement']), \
	Test('List Comprehension If', '[x for x in range(10) if x < 4]', ['Statement']), \
	Test('Modulo', '10%3', ['Statement']), \
	Test('Module', 'True', ['Statement', 'Name']), \
	Test('Multiplication', '5*x', ['Constant', 'Name']), \
	Test('Name', 'True', ['Constant']), \
	Test('Not', 'not True', ['Statement']), \
	Test('Or', '2<5 or True', ['Statement']), \
	Test('Pass', 'pass', ['Statement']), \
	Test('Power', '5**0.2', ['Statement']), \
	Test('Print Inline', 'print "TEST",', ['Statement']), \
	Test('Print New Line', 'print "TEST"', ['Statement']), \
	Test('Raise', 'raise ValueError()', ['Statement']), \
	Test('Return', """def f(x):
	return x*x
def g():
	return
def h():
	return None
def i():
	return 1, 2
def j():
	return 1 / (math.hypot(point_position[0] - position[0], point_position[1] - position[1])**2 + 0.000001)
""", ['Statement']), \
	Test('Right Shift', '', ['Statement']), \
	Test('Slice', """x[5:15]
y[:10]
z[a:]""", ['Statement']), \
	Test('Slice Object', '', ['Statement']), \
	Test('Statement', 'True', ['Module', 'Name']), \
	Test('Subtraction', '1-x', ['Constant', 'Name']), \
	Test('Subscription', """x[5]
del x[y]
del(y[x])""", ['Statement']), \
	Test('Try Except', """try:
	[0,1,2].remove(5)
except ValueError:
	print "No 5"
except SyntaxError, e:
	print "Syntax Error: "+str(e)
except:
	print 'Other Error'
	try:
		print "Nested"
	except:
		print "Nest fail"
	else:
		print 'Nest worked'
""", ['Statement']), \
	Test('Try Finally', """try:
	print "x"
except:
	print "y"
finally:
	print 'z'""", ['Statement']), \
	Test('Tuple', """(a, b, (c, d))
x=()""", ['Name']), \
	Test('Unary Addition', '+3', ['Statement']), \
	Test('Unary Subtraction', '-10', ['Statement']), \
	Test('While Loop', """x = 1
while x < 5:
	print str(x)
	x += 1""", ['Statement']), \
	Test('With', '', ['Statement']), \
	Test('Yield', '', ['Statement']) \
]

for test in tests:
	test.run(g)

failed = []
succeeded = []
unknown = []

for test in tests:
	if not test.result:
		failed.append(test)
	else:
		succeeded.append(test)

for test in failed[:]:
	for dep in test.deps:
		for test2 in failed[:]:
			if test2.name == dep:
				try:
					failed.remove(test)
					unknown.append(test)
				except ValueError:
					pass

for s in succeeded:
	print s.message

for u in unknown:
	print u.name + ': Unknown (depends on broken rules)'

for f in failed:
	print f.message
