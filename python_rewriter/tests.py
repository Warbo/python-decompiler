import sys
from subprocess import call

class EscapeException(Exception):
	pass

if __name__ != '__main__' or len(sys.argv) == 1:
	class Test:
	
		def __init__(self, name, code, deps):
			self.name = name
			self.code = code
			self.deps = deps
			self.result = False
			self.message = self.name + ": Test didn't run"
	
		def get_tree(self):
			return base.parse(self.code)
	
		def run(self, grammar):
			self.message = self.name.upper() + '\n=======================\n'
			if self.code == '' and self.name is not 'Empty':
				self.message = self.message + 'No test set'
				return
			
			try:
				tree = self.get_tree()
			except SyntaxError:
				self.message = self.message + """Error in test.\n""" + self.code
				raise EscapeException()
			try:
				g_tree = grammar([tree])
				try:
					generated = g_tree.apply('thing',0)[0]
				except ParseError, e:
					if e.error is not None and len(e.error) > 0:
						self.message = self.message + """Error in grammar.\n""" + self.code + """\n\n""" + str(tree)
						raise EscapeException()
					else:
						self.message = self.message + """Died"""
						raise EscapeException()
				try:
					assert str(compiler.parse(generated)) == str(tree)
				except AssertionError:
					self.message = self.message + """Error, generated code does not match original.\n""" + self.code + """\n\n""" + str(tree) + """\n\n""" + generated
					raise EscapeException()
				except SyntaxError:
					self.message = self.message + """Error in generated code.\n""" + self.code + """\n\n""" + str(tree) + """\n\n""" + generated
					raise EscapeException()
				self.message = self.message + "OK"
				self.result = True
			except EscapeException:
				pass
	
	tests = [\
		Test('Empty','',['Statement','Module']), \
		Test('Addition','1+2', ['Statement', 'Constant']), \
		Test('And', '1 and True', ['Name', 'Constant']), \
		Test('Assign Attribute', 'x.name = "ex"', ['Statement', 'Name']), \
		Test('Assign List', '[a,b,c] = x', ['Statement', 'Name', 'Assign']), \
		Test('Assign Name', """x = 10
""", ['Name', 'Constant', 'Assign']), \
		Test('Assign Tuple', """
x, y, z = 1, 2, "10"
""", ['Tuple', 'Name', 'Constant', 'Assign']), \
		Test('Assert', """
assert 10 < 9
assert x < 5, "x is not less than five"
""", ['Compare', 'Constant']), \
		Test('Assign', 'x = y = 10', ['Name', 'Constant', 'Statement']), \
		Test('Augmenting Assign', 'x += 10', ['Statement', 'Name', 'Constant']), \
		Test('Backquote', '`something`+`some_function(some_arg)`', ['Statement', 'Add']), \
		Test('Bitwise And', 'a&b&(c&d)', ['Statement']), \
		Test('Bitwise Or', 'a|b|(c|d)', ['Statement']), \
		Test('Bitwise Exclusive Or', 'a^b^(c^d)', ['Statement']), \
		Test('Break', """x=0
while True:
	x += 1
	if x == 5:
		break
""", ['Statement']), \
		Test('Function Call', """str(x)
f(*[1,2,3])
g(*x*2)
h(**x)
i(a, b=5, *c, **d)
j(*a, **b)
""", ['Statement', 'Name']), \
		Test('Class', """class A(object):
	def __init__(self):
		pass
	
class B(A):
	
	def __init__(self):
		pass
	
class B():
	''' A docstring
	'''
	x = y
""", ['Statement', 'Pass', 'Function']), \
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
1.0e300000
-1.0e300000
"""+'"""SEXTUPLE"""'+"""
None""", ['Statement']), \
		Test('Continue', """for x in range(5):
	if x == 2:
		continue
	print str(x)""", ['Statement', 'Name', 'Function Call', 'Compare', 'Constant', 'Print New Line']), \
		Test('Decorators', """
def a(g):
	return g
@a
def f(x,y):
	print x+y
@dbus.service.signal(dbus_interface='com.example.Sample', signature='us')
def s(self, thing1, thing2):
	print str(thing1)+str(thing2)
class A:
	@a
	@b
	def c():
		pass
A()
""", ['Statement', 'Print New Line']), \
		Test('Deletion', """
del x
del(y)
del a, b, c
del x[a]
del x[a:b]
del x[a:b:c]
del a, b[x], c[x:y], d[x:y:z], e.a
del e.a
""", ['Statement', 'Name']), \
		Test('Dictionary', """x = 5
a = "s"
y = {a:1, 5:x}
{}
""", ['Statement', 'Name', 'Constant', 'Assign', 'Assign Name']), \
		Test('Discard', '5', ['Statement', 'Constant']), \
		Test('Division', 'x/10', ['Name', 'Constant']), \
		Test('Ellipsis', 'x[...,5]', ['Statement']), \
		Test('Expression', '', ['Statement']), \
		Test('Execute', """exec("x=True")
exec 'from sympy import *' in global_dict
exec 'a' in foo,bar""", ['Statement']), \
		Test('Rounded-Down Division', 'a//b//(c//d)', ['Statement']), \
		Test('For Loop', """for x in range(5):
	print str(x)
	for a, b in enumerate(range(10)):
		print str(a*b)
for i in attr1:
	i.go()
""", ['Statement', 'Print New Line']), \
		Test('From', """from os import get_cwd
from sys import exit as Exit
from pygame import draw, mixer as sound, surface
from .. import test
from ..subdir import something
""", ['Statement']), \
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
def l(a):
	return a
""", ['Statement', 'Print New Line']), \
		Test('GenExpr', 'print(x for x in range(5))', ['Statement', 'Print New Line']), \
		Test('GenExprFor', 'print(x for x in range(5))', ['Statement', 'Print New Line']), \
		Test('GenExprIf', """print(x for x in range(5) if x < 2)
newWidth = max(
	obj.width()
	for obj in objects
	if obj is not stringPict.LINE)""", ['Statement', 'Print New Line']), \
		Test('GenExprInner', 'print(x for x in range(5))', ['Statement', 'Print New Line']), \
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
	print 'd'""", ['Statement', 'Print New Line']), \
		Test('IfExp', """a = b if c > d else e""", ['Statement']), \
		Test('Import', """import os
import sys as System
if True:
	import StringIO
	import pygame, compiler
	import urllib2
print 'x'""", ['Statement', 'Print New Line']), \
		Test('Keyword', """def f(x, y, a=True, b="h"):
	if a:
		print x+y+b
f('c','d', a=False)""", ['Statement', 'Print New Line']), \
		Test('Lambda', """f = lambda x, y, a=2: x+y+a*a
lambda: 5*2
lambda x, y: x*y
filter(lambda x: x>5, range(10))
lambda x, y, z=func(15, a=Person()): z/x**y
lambda:'n/a'""", ['Statement', 'Call Function']), \
		Test('Left Shift', 'x<<(y<<z)', ['Statement']), \
		Test('List', """[1,2,3,[1,2,"s"]]
x = []""", ['Statement']), \
		Test('List Comprehension', '[str(x) for x in range(10)]', ['Statement']), \
		Test('List Comprehension For', '[x for x in range(5)]', ['Statement']), \
		Test('List Comprehension If', '[x for x in range(10) if x < 4]', ['Statement']), \
		Test('Modulo', '10%3', ['Statement']), \
		Test('Module', '''"""
Some text.
"""
True''', ['Statement', 'Name']), \
		Test('Multiplication', '5*x', ['Constant', 'Name']), \
		Test('Name', 'True', ['Constant']), \
		Test('Not', 'not True', ['Statement']), \
		Test('Or', '2<5 or True', ['Statement']), \
		Test('Pass', 'pass', ['Statement']), \
		Test('Power', '5**0.2', ['Statement']), \
		Test('Print Inline', """print "TEST",
print "1: %s 2: %s" % (a, b),
print '  %-15s %s' % (cmd, description),
print >> x, "thing",
print a, b,
""", ['Statement']), \
		Test('Print New Line', """print "TEST"
print "1: %s 2: %s" % (a, b)
print '  %-15s %s' % (cmd, description)
print
print >> x, 'thing'
print a, b
print(x for x in range(5))
#print "Creating %d trees of depth %d" % (5, 10)
""", ['Statement']), \
		Test('Raise', """raise ValueError()
raise AssertionError('%s: %s' % (a, b)), None, x
raise
raise Thing(), something
raise Thing(), a, b
""", ['Statement']), \
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
		Test('Right Shift', 'a>>b>>c>>d>>(e>>f)', ['Statement']), \
		Test('Slice', """x[5:15]
y[:10]
z[a:]""", ['Statement']), \
		Test('Slice Object', """
x[start:end:step]
""", ['Statement']), \
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
""", ['Statement', 'Print New Line']), \
		Test('Try Finally', """try:
	print "x"
except:
	print "y"
finally:
	print 'z'
try:
	print "a"
finally:
	print 'b'
""", ['Statement', 'Print New Line']), \
		Test('Tuple', """(a, b, (c, d))
x=()""", ['Name']), \
		Test('Unary Addition', '+3', ['Statement']), \
		Test('Unary Subtraction', """-10
assert (-(1+x)**2).expand()""", ['Statement']), \
		Test('While Loop', """x = 1
while x < 5:
	print str(x)
	x += 1""", ['Statement', 'Print New Line']), \
		Test('With', """
with open('a', 'r') as f:
	read(f)
""", ['Statement', 'Function Call']), \
		Test('Yield', 'yield x', ['Statement']) \
	]

def do_file(grammar, testfile, name, do_print=False, notfile=None, workfile=None):
	if notfile is None: keepnot = False
	else: keepnot = True
	if workfile is None: keepwork = False
	else: keepwork = True
	
	# Attempt to parse the file contents into an AST
	try:
		tree = base.parse('\n'.join([l.rstrip() for l in testfile.readlines()]))
		testfile.close()
	except Exception, e:
		# If we fail then make a note of it as appropriate
		if keepnot:
			notfile.write(name+'\n')
			notfile.flush()
		# And output more information if asked to
		if do_print:
			testfile.seek(0)
			print ''.join(testfile.readlines())
			print
			print str(e)
			print "Error parsing input."
		# Now quit (we can't go any further)
		#sys.exit(0)
		return
			
	# Attempt to generate code from the AST
	try:
		matcher = grammar([tree])
		code = matcher.apply('python',0)[0]
	except ParseError, e:
		if e.error is not None and len(e.error) > 0:
			# If we fail then make a note of it as appropriate
			if keepnot:
				notfile.write(name+'\n')
				notfile.flush()
			# And output more information if asked to
			if do_print:
				print repr(tree)
				print
				print str(e)
				print "Error generating code"
			# Now quit (we can't go any further)
			#sys.exit(0)
			return
		else:
			print "Died at "+str(matcher.input.position)+" of "+str(matcher.input.data)
			return
			
	# Attempt to parse the generated code into an AST
	try:
		new_tree = base.parse(code)
		# Get rid of the code now that we don't need it
		del(code)
	except Exception, e:
		# If we fail then make a note of it if asked to
		if keepnot:
			notfile.write(name+'\n')
			notfile.flush()
		# And output more information if asked to
		if do_print:
			print repr(code)
			print
			print str(e)
			print "Error parsing generated code"
		# Now quit (we can't go any further)
		#sys.exit(0)
		return

	# Attempt to equate the two trees
	try:
		# repr(tree1) should equal repr(tree2)
		if repr(tree) == repr(new_tree):
			# If so then we have succeeded, note is as required
			if keepwork:
				workfile.write(name+'\n')
				workfile.flush()
			if do_print:
				print "Match"
		# Otherwise...
		else:
			# If they're not equal then make a note as required
			if keepnot:
				notfile.write(name+'\n')
				notfile.flush()
			# And output if we've been asked to
			if do_print:
				print
				print "DIDN'T MATCH"
				print '##############'
				tree1 = repr(tree)
				print '##############'
				tree2 = repr(new_tree)
				print '##############'
				for index in range(max(len(tree1), len(tree2))):
					if tree1[index] == tree2[index]:
						sys.stdout.write(tree1[index])
					else:
						print "FAIL HERE"
						print
						print tree1[index:]
						print
						print tree2[index:]
						break
		# Now quit				
		#sys.exit(0)
		return
				
	except Exception, e:
		# If there's an error then note it as appropriate
		if keepnot:
			notfile.write(name+'\n')
			notfile.flush()
		# And output more information if asked to
		if do_print:
			tree1 = repr(tree)
			tree2 = repr(new_tree)
			for index in range(max(len(tree1), len(tree2))):
				if tree1[index] == tree2[index]:
					sys.stdout.write(tree1[index])
				else:
					print "FAIL HERE"
					print
					print tree1[index:]
					print
					print tree2[index:]
					break
		# Now quit
		#sys.exit(0)
		return

# Do imports first. These are expensive (especially base) so they'e conditional
are_imported = __name__ != '__main__'
no_arguments = len(sys.argv) == 1
file_of_files = "-f" in sys.argv
if are_imported or no_arguments or not file_of_files:
	import base
	from base import grammar as g
	from pymeta.runtime import ParseError
	import compiler
	try:
		import psyco
		psyco.full()
	except:
		pass

# Run the following if we've been imported or if we've not been given any
# arguments
if are_imported or no_arguments:
	# Run the tests
	for test in tests:
		test.run(g)

	# These will store our results
	failed = []
	succeeded = []
	unknown = []

	# Go through each test
	for test in tests:
		# Assign it to the relevant list based on its result
		if not test.result:
			failed.append(test)
		else:
			succeeded.append(test)

	# Now go through (a copy of) each failed test
	for test in failed[:]:
		# See if any features it relies on also failed
		for dep in test.deps:
			for test2 in failed[:]:
				if test2.name == dep:
					# If so then move it to the "unknown" list
					try:
						failed.remove(test)
						unknown.append(test)
					except ValueError:
						pass

	# Now our "succeeded" list will contain every successful feature
	# The "failed" list will contain those features which don't work
	# The "unknown" list will have those with no information (ie.
	# their tests require dependencies to work before running) 
	if __name__ == '__main__':
		# Output the results
		for s in succeeded:
			print s.message

		for u in unknown:
			print u.name + ': Unknown (depends on broken rules)'

		for f in failed:
			print f.message

# If we've got arguments then run the following instead
else:
	# A "-f" argument means "test the files named in this file"
	if file_of_files:
		
		# Make some defaults
		keepnot = False
		keepwork = False
		
		# See if we've been given files to write to
		# "-w" should be followed by a file to append successes to
		if '-w' in sys.argv:
			workfile = sys.argv[sys.argv.index('-w')+1]
			keepwork = True
		else: workfile = None
		# "-n" should be followed by a file to append failures to
		if '-n' in sys.argv:
			notfile = sys.argv[sys.argv.index('-n')+1]
			keepnot = True
		else: notfile = None
		
		# Generate the filenames we're to test
		infile = open(sys.argv[sys.argv.index('-f')+1], 'r')
		lines = [line.strip() for line in infile.readlines()]
		
		# Test each file by calling do_file.
		# We could easily do testing concurrently, but I only have
		# one processor, so haven't bothered doing it yet).
		for num, line in enumerate(lines):
			arguments = ['python', 'tests.py', line]
			if keepnot:
				arguments.extend(['-n', notfile])
			if keepwork:
				arguments.extend(['-w', workfile])
			call(arguments)
			#do_file(open(line, 'r'), line, False, open(notfile, 'a'), open(workfile, 'a'))
			# Give a progress indicator (the number remaining)
			sys.stderr.write(str(len(lines)-num)+'\n')
			sys.stderr.flush()
	
	# If we have no list of files, we should use the first argument
	else:
		# Define defaults
		do_print = True
		keepnot = False
		keepwork = False
		workfile = None
		notfile = None
		# See if we have output files to append to
		# "do_print" indicates that we should output test
		# information to the console
		if '-w' in sys.argv:
			do_print = False
			keepwork = True
			workfile = open(sys.argv[sys.argv.index('-w')+1], 'a')
		if '-n' in sys.argv:
			do_print = False
			keepnot = True
			notfile = open(sys.argv[sys.argv.index('-n')+1], 'a')
			
		# The file to use
		name = sys.argv[1]
		testfile = open(name, 'r')
		
		# Now test the contents
		do_file(g, testfile, name, do_print, notfile, workfile)
