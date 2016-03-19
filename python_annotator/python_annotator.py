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
from python_rewriter.base import parse, constants
from python_rewriter.nodes import *

def add_annotations(node):
	"""This adds annotation assertions to the given node, and
	recursively to its children. It returns the number of annotations
	made (ie. zero means no changes too place)."""
	# Initialise the change counter
	count = 0
	# We can't do anything to "types" so if we've been given one, return
	if type(node) in [type(''), type((,)), type([]), type({}),
		type(None), type(True)]:
		return count
	# Here we define the annotations we're going to check for
	# TODO: Make this more extensible, ie. read them from some external
	# source rather than having them hard-coded

	# First give the node a set of annotations if it doesn't have one
	if 'annotations' not in dir(node):
		node.annotations = set([])

	# Now go through each Node possibility
	if node.__class__ == Add:
		node.annotations = node.annotations.union(set([
			'"__add__" in dir(node.left)',
			'"__call__" in dir(node.left.__add__)'
		]))

	for child in node.asList():
		count += add_annotations(child)
	return count

def annotate(path_or_text, initial_indent=0):
	"""This performs the translation from annotated Python to normal
	Python. It takes in annotated Python code (assuming the string to be
	a file path, falling back to treating it as raw code if it is not a
	valid path) and emits Python code."""
	# See if the given string is a valid path
	if os.path.exists(path_or_text):
		# If so then open it and read the file contents into in_text
		infile = open(path_or_text, 'r')
		in_text = '\n'.join([line for line in infile.readlines()])
		infile.close()
	# Otherwise take the string contents to be in_text
	else:
		in_text = path_or_text

	# Wrap in try/except to give understandable error messages (PyMeta's
	# are full of obscure implementation details)
	try:
		# Get an Abstract Syntax Tree for the contents of in_text
		tree = parse(in_text)

		# Transform the Python AST into a Diet Python AST
		annotated_tree = tree.ann()

		#print str(tree)
		#print str(diet_tree)

		# Generate (Diet) Python code to match the transformed tree
		annotated_code = annotated_tree.rec(initial_indent)

		print str(tree)
		print
		print str(annotated_tree)
		print

		print annotated_code

	except Exception, e:
		sys.stderr.write(str(e)+'\n')
		sys.stderr.write('Unable to annotate.\n')
		sys.exit(1)

if __name__ == '__main__':
	# TODO: Allow passing the initial indentation
	# TODO: Allow specifying an output file
	if len(sys.argv) == 2:
		translate(sys.argv[1])
	else:
		print "Usage: python_annotator.py input_path_or_raw_python_code"
