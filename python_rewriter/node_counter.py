"""
This script is used for profiling. Give it the filename of a list of files (one
per line) as an argument and it will try to compile each file, counting the
number of occurances of each AST node type as it goes.

This is useful to determine the precedence order of the "thing" rule in the base
grammar, so as to minimise the number of alternative that need to be tried.
"""

import sys
import compiler
import random

try:
	import psyco
	psyco.full()
except:
	pass


def count_down(node):
	"""Increments the counter for this node's class and recurses through its
	children."""
	# Assume that this is an AST node
	if issubclass(node.__class__, Node):
		node.__class__.counter += 1
		map(count_down, node.asList())
		return
	# If not, it may be a collection
	if '__iter__' in dir(node):
		map(count_down, node)
		return
	# If not, it is a built-in type
	return	

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print "Python code analyser, used for counting AST node frequency."
		print "Usage: node_counter.py filename [number]"
		print "Where filename is a file that contains a list of Python files,"
		print "one per line, that are to be scanned, and the optional number"
		print "argument indicates how many files are to be proccessed (chosen"
		print "at random from the input)"
		sys.exit()
	
	# First we instrument the compiler nodes
	sys.stderr.write('Grabbing nodes\n')
	import nodes
	nodelist = []
	sys.stderr.write('Instrumenting nodes\n')
	for node in [n for n in dir(nodes) if n[0].isupper()]:
		sys.stderr.write('Setting counter for '+node+'\n')
		exec('nodes.'+node+'.counter = 0')		# Give it a counter
		sys.stderr.write('Importing '+node+'\n')
		exec(node+' = nodes.'+node)		# Import it directly to our namespace
		nodelist.append(node)

	sys.stderr.write('Reading filenames\n')
	filenames = [line.strip() for line in open(sys.argv[1],'r').readlines()]

	if (len(sys.argv) > 2):
		sys.stderr.write('Explicit count given.\n')
		counter = int(sys.argv[2])
		if counter > len(filenames):
			sys.stderr.write('The given count is larger than the number of files given.\n')
			sys.stderr.write('Only '+len(filenames)+'files will be proccessed.\n')
			counter = len(filenames)
	else:
		counter = len(filenames)
	total = counter

	sys.stderr.write('Starting scan\n')
	while counter > 0:
		choice = random.randint(0,counter)
		filename = filenames.pop(choice)
		try:
			f = open(filename,'r')
			text = ''.join(f.readlines())
			f.close()
			tree = compiler.parse(text)
			count_down(tree)
		except Exception, e:
			# If it fails then just skip. We're not getting exact data anyway.
			sys.stderr.write(str(e))
			sys.stderr.write ('Ack')
			pass
		sys.stderr.write('\n'+str(counter))
		sys.stderr.flush()
		counter -= 1

	sys.stdout.write('\nsamples,')
	for node in nodelist:
		sys.stdout.write(node+',')
	sys.stdout.write('\n'+str(total)+',')
	for node in nodelist:
		sys.stdout.write(str(eval(node+'.counter'))+',')
