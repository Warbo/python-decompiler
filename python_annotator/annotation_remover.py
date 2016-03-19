"""
This contains a translator from annotated Python to regular Python,
using PyMeta (a Python implementation of the OMeta pattern matching
system)"""

try:
	import psyco
	psyco.full()
except:
	pass

import os
import sys
from python_rewriter.base import strip_comments
from pymeta.grammar import OMeta

# Our metadata is found by traversing the code

## TODO: Give comments and strings higher priority than code, so that
## we don't accidentally remove '# meta{...}meta' or 
## 'my_string = "meta{...}meta"'
## 
annotation_finder = """
# Annotations are of the form 'meta{...}meta'
annotation ::= <token 'meta{'> <annotation_contents>		=> ''

# If we've reached a '}meta' then stop matching, otherwise keep going
annotation_contents ::= <token '}meta'>						=> ''
                      | <anything> <annotation_contents>	=> ''

# A statement is a series of annotations or anything else
statement ::= <annotation>+									=> ''
            | <anything>+:a									=> ''.join(a)

# A program is a series of statements
program ::= <statement>+:a									=> ''.join(a)

"""

# Now we embed the transformations in every AST node, so that they can
# apply them recursively to their children
finder = OMeta.makeGrammar(strip_comments(annotation_finder), globals())

def strip_annotations(path_or_text):
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
		# Generate Python code
		stripper = finder(in_text)
		stripped_code = stripper.apply(program)
		
		print stripped_code
		
	except Exception, e:
		sys.stderr.write(str(e)+'\n')
		sys.stderr.write('Unable to strip.\n')
		sys.exit(1)

if __name__ == '__main__':
	# TODO: Allow passing the initial indentation
	# TODO: Allow specifying an output file
	if len(sys.argv) == 2:
		strip_annotations(sys.argv[1])
	else:
		print "Usage: annotation_remover.py input_path_or_raw_python_code"
