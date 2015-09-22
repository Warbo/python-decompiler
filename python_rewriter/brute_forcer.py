#!/usr/bin/env python
import compiler
try:
	import psyco
	psyco.full()
except:
	pass

#chars = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
#	'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y',
#	'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
#	'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y',
#	'Z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '~', '`',
#	'!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '-', '+',
#	'=', '{', '[', '}', ']', ':', ';', '"', "'", '\\', '|', '<', ',',
#	'>', '.', '/', '?',' ']
chars = ['a', 'b', 'c', 'None', ' ', '0', '9', '~', '`',
	'!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '-', '+',
	'=', '{', '[', '}', ']', ':', ';', '"', "'", '\\', '|', '<', ',',
	'>', '.', '/', '?']

length = 0
found = False

def find_match(string):
	try:
		tree = compiler.parse(string)
		print '.',
		for n in [tree.node.nodes[0]]:
			if n.__class__ == compiler.ast.Discard and \
				n.expr.__class__ == compiler.ast.Const and\
				n.expr.value is None:
				return True
		else:
			raise Exception()
	except:
		return False

def do_words(length,start,chars):
	if length == 1:
		return [start+c for c in chars if find_match(start+c)]
	else:
		results = []
		[results.extend(do_words(length-1, start+c, chars)) for c in chars]
		return results

while not found:
	length += 1
	results = do_words(length, '', chars)
	if len(results) > 0: found = True
	print str(length)

print str(results)
