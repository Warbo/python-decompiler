#!/usr/bin/env python

import nodes
import random
import sys

class Tree(object):
	"""Stores an AST, along with various parameters about it."""

	def __init__(self, count, bias):
		"""Creates a Tree storing the given properties."""
		self.count = count + count%2		# We round count to an even number
		if count < 4:
			count = 4
		self.bias = bias
		# We create an AST with a single number
		self.ast = nodes.Module(None,nodes.Stmt([nodes.Discard(nodes.Const(random.randint(1,1000000)))]))
		# This gives us 4 nodes as a starting point
		self._count = 4
		while self._count < self.count:
			self.add_nodes()

	def add_nodes(self):
		"""This picks a random path down the AST with the given left-right bias,
		until it hits a Const. It then replaces the Const with an arithmetic
		node, containing 2 Consts. This bumps up the node count by 2."""
		
		def swap_const(node, bias):
			"""A helper function which drills down an AST to find a Const to
			swap."""
			if node.__class__ == nodes.Const:
				cls = random.choice([nodes.Add,nodes.Sub,nodes.Mul,nodes.Mod,nodes.Div,nodes.Power])
				return cls([nodes.Const(random.randint(1,1000000)),nodes.Const(random.randint(1,1000000))])
			else:
				if random.random < bias:
					return node.__class__([swap_const(node.left, self.bias),node.right])
				else:
					return node.__class__([node.left,swap_const(node.right, self.bias)])
		self.ast = nodes.Module(None,nodes.Stmt([nodes.Discard(swap_const(self.ast.node.nodes[0].expr, self.bias))]))
		self._count += 2

class Sample(object):
	"""A sample of ASTs with the given characteristics."""

	def __init__(self, max_nodes, sample_number):
		"""Creates a sample of Trees. The sample contains random Trees starting
		with 4 nodes (Module(Stmt([Discard(Const(x))]))) and going up to
		max_nodes nodes. The sample contains sample_number Trees of each number
		of nodes, with an even spread from left-leaning to right-leaning."""
		self.max_nodes = max_nodes
		self.sample_number = sample_number
		self.biases = [float(b)/float(self.sample_number) for b in range(self.sample_number+1)]
		self.trees = {}
		for n in range(4,self.max_nodes,2):
			self.trees[n] = []
			for bias in self.biases:
				sys.stderr.write('.')
				sys.stderr.flush()
				self.trees[n].append(Tree(n,bias))

	def time(self,grammar):
		"""Times how long it takes for the given grammar to parse the ASTs in
		this sample."""

		def time_tree(tree):
			"""Helper function to time an individual Tree."""
			sys.stderr.write(',')
			sys.stderr.flush()
			results = []
			matcher = base.grammar([tree.ast])
			start_time = time.clock()
			for _ in xrange(100):
				try:
					code, err = matcher.apply("thing", 0)
					results.append(code)
					del(code)
					del(err)
				except ParseError, e:
					continue
		
			end_time = time.clock()
			return float(end_time - start_time) / float(len(results))

		self.times = {}
		for n in range(4,self.max_nodes,2):
			self.times[n] = {}
			for i,tree in enumerate(self.trees[n]):
				self.times[n][str(self.biases[i])] = time_tree(tree)
				tree = None

		return self.times

def make_graph(d):
	"""Converts a dictionary given by Sample.time into a graph."""
	points = []
	keys = d.keys()
	keys.sort
	for n in keys:
		keys2 = d[n].keys()
		keys2.sort()
		l = []
		for k in keys2:
			l.append(d[n][k])
		points.append(l)

	import enthought.mayavi.mlab
	surface = enthought.mayavi.mlab.surf(points)
	enthought.mayavi.mlab.show()

if __name__ == '__main__':
	import time
	import base
	from pymeta.runtime import ParseError
	if len(sys.argv) != 3:
		print 'Usage: ast_generator.py max repeats'
		sys.exit(0)
	sample = Sample(int(sys.argv[1]), int(sys.argv[2]))
	make_graph(sample.time(base.grammar))
	raw_input()
