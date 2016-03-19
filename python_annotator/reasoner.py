"""This module implements a language based on Python which includes
direct support for declarative annotations and metadata. Such code
can be stripped of its metadata easily to produce runnable Python
code, and in fact when used this way, the metadata doesn't affect
the running of the code at all, and can be syntactically-correct
garbage for all its worth.

The interesting uses are not in stripping the metadata, but in adding
it, to produce specifications. This complements Python's built-in assert
functionality, since assert is a function which runs as part of the
code, and can thus change its execution in the general case. By having
declarative metadata we can do static analysis on the code as well, to
create relevant metadata, check whether the metadata and code match up
(useful for ensuring that a piece of code implements the required
specification) and for code synthesis from the metadata.

The function of this system is to implement the opposite of a static
language:

In a static language (C, C++, Java, etc.) unambiguous semantics and typing
allows a machine to reason on the code to produce fast results and
check for many errors, with the expense being that the programmer is
forced to jump through hoops such as declaring variables, declaring
types, only using the correct types in each variable, building
rigid class hierarchies, etc.

In a dynamic language like Python, names can be used without being
previously declared, names aren't restricted to referring to a specific
type (technically they are, but this type is "object", of which
everything is theoretically a specialisation (but this is broken
in Python 2.x)), the definitions of objects, classes (which are
objects) and types can be modified at any point in the code, which
makes the semantics dependent on the execution path, and so on.
This allows greater programming freedom and more code reuse, at the
expense of the machine's ability to understand the code by inspection.

Using a metadata system allows dynamic code such as Python to be
better-understood by a machine, without sacrificing its ease
of writing or its generality. For example, if we have a function:

def foo(bar):
	bar.x = False

There is metadata which can be extracted from this definition. This
includes "foo takes exactly one argument", "the type of foo's
argument is unrestricted", "foo causes its argument to contain the
attribute 'x' as a pointer to 'False'", and so on. This metadata is
not restricting the code in any way, it is simply describing known
properties of the code which would be obvious to a human who knows
Python, but need to be explicitly figured out by a computer. By
embedding this metadata in the language, it travels around with the
code it is desribing, plus it only needs to be extracted once
(verification is usually much simpler than derivation).

This project is inspired by Hesam Samimi of the Viewpoints Research
Institute, who is persuing similar work in Java and Smalltalk.

This contains a translator from regular Python to Diet Python, using
PyMeta (a Python implementation of the OMeta pattern matching system)"""

try:
	import psyco
	psyco.full()
except:
	pass

import os
import sys
from python_rewriter.base import grammar_def, strip_comments, parse, constants
from python_rewriter.nodes import *
from pymeta.grammar import OMeta

def get_units(tree, list=[]):
	"""Returns a list of all externally reusable bits of code
	(functions, classes, modules, etc.)."""
	if tree.__class__ in [Function, Class, Module]:
		to_return = []
		for lst in map(get_units, tree.asList()):
			to_return = to_return + lst
		return list+[tree]+to_return
	elif type(tree) in [type(''), type((1,2,3)), type([]), type({}),
		type(None), type(True), type(False), type(Ellipsis), type(1)]:
		return list
	else:
		to_return = []
		for lst in map(get_units, tree.asList()):
			to_return = to_return + lst
		return list+to_return

tree = parse(''.join(open('reasoner.py', 'r').readlines()))
print str(tree)
print '#########################'
print str(get_units(tree, []))

#def add(arg):
#	"""Runs transformations on the argument. If the argument has a trans
#	method, that is run; if it is a list, apply is mapped to the list;
#	if it is a "type" (None, str, etc.) then that is returned unchanged.
#	"""
#	if type(arg) in [type('string'), type(0), type(None)]:
#		return arg
#	elif type(arg) == type([0,1]):
#		return map(apply, arg)
#	elif type(arg) == type((0,1)):
#		return tuple(map(apply, arg))
#	elif 'trans' in dir(arg):
#		return arg.trans()
#	else:
#		raise Exception("Couldn't transform "+str(arg))

#def put(to_return, constraints):
#	"""Adds the constrints defined in the second argument, a list with
#	elements in the form (string_of_name_to_add_contraint_to,
#	string_of_condition_to_satisfy)"""
#	pass

# Our metadata is found by traversing the Abstract Syntax Tree of the
# code. Here we define the tree operations we wish to make, using
# PyMeta.

annotation_finder = """
# "thing" matches anything, applying transforms to those which have them
thing ::= <add>
#        | <and>
#        | <assattr>
#        | <asslist>
#        | <assname>
#        | <asstuple>
#        | <assert>
#        | <assign>
#        | <augassign>
#        | <backquote>
#        | <bitand>
#        | <bitor>
#        | <bitxor>
#        | <break>
#        | <callfunc>
#        | <class>
#        | <compare>
#        | <const>
#        | <continue>
#        | <decorators>
#        | <dict>
#        | <discard>
#        | <div>
#        | <ellipsis>
#        | <emptynode>
#        | <exec>
#        | <expression>
#        | <floordiv>
#        | <for>
#        | <from>
#        | <function>
#        | <genexpr>
#        | <genexprfor>
#        | <genexprif>
#        | <genexprinner>
#        | <getattr>
#        | <global>
#        | <if>
#        | <ifexp>
#        | <import>
#        | <invert>
#        | <keyword>
#        | <lambda>
#        | <leftshift>
#        | <list>
#        | <listcomp>
#        | <listcompfor>
#        | <listcompif>
#        | <mod>
#        | <module>
#        | <mul>
#        | <name>
#        | <not>
#        | <or>
#        | <pass>
#        | <power>
#        | <print>
#        | <printnl>
#        | <raise>
#        | <return>
#        | <rightshift>
#        | <slice>
#        | <sliceobj>
#        | <stmt>
#        | <sub>
#        | <subscript>
#        | <tryexcept>
#        | <tryfinally>
#        | <tuple>
#        | <unaryadd>
#        | <unarysub>
#        | <while>
#        | <with>
#        | <yield>

add ::= <anything>:a ?(a.__class__ == Add) => put(a, [("'__add__' in dir(a.left)"), ('a.left.__add__', 'runnable'), ('a.left.__add__', 'accepts', 'a.right')]) 

if ::= <anything>:a ?(a.__class__ == If) => put(a, [])
"""

# Now we embed the transformations in every AST node, so that they can
# apply them recursively to their children
#finder = OMeta.makeGrammar(strip_comments(annotation_finder), globals())
#Node.finder = finder
#Node.annotation_finder = annotation_finder
#
#def ann(self):
#	"""This creates a tree transformer with the current instance as
#	the input. It then applies the "thing" rule. Finally it returns
#	the result."""
#	# Uncomment to see exactly which bits are causing errors
#	print str(self)
#	
#	self.annotator = self.finder([self])
#	
#	r = self.annotator.apply('thing')
#	
#	return r
	
#Node.ann = ann

#def annotate(path_or_text, initial_indent=0):
#	"""This performs the translation from annotated Python to normal
#	Python. It takes in annotated Python code (assuming the string to be
#	a file path, falling back to treating it as raw code if it is not a
#	valid path) and emits Python code."""
#	# See if the given string is a valid path
#	if os.path.exists(path_or_text):
#		# If so then open it and read the file contents into in_text
#		infile = open(path_or_text, 'r')
#		in_text = '\n'.join([line for line in infile.readlines()])
#		infile.close()
#	# Otherwise take the string contents to be in_text
#	else:
#		in_text = path_or_text
#		
#	# Wrap in try/except to give understandable error messages (PyMeta's
#	# are full of obscure implementation details)
#	try:
#		# Get an Abstract Syntax Tree for the contents of in_text
#		tree = parse(in_text)
#		
#		# Transform the Python AST into a Diet Python AST
#		annotated_tree = tree.ann()
#		
#		#print str(tree)
#		#print str(diet_tree)
#		
#		# Generate (Diet) Python code to match the transformed tree
#		annotated_code = annotated_tree.rec(initial_indent)
#		
#		print str(tree)
#		print
#		print str(annotated_tree)
#		print
#		
#		print annotated_code
#		
#	except Exception, e:
#		sys.stderr.write(str(e)+'\n')
#		sys.stderr.write('Unable to annotate.\n')
#		sys.exit(1)

#if __name__ == '__main__':
#	# TODO: Allow passing the initial indentation
#	# TODO: Allow specifying an output file
#	if len(sys.argv) == 2:
#		translate(sys.argv[1])
#	else:
#		print "Usage: python_annotator.py input_path_or_raw_python_code"
