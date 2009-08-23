#!/usr/bin/env python

# TODO Should we put requires=['pymeta']?

from distutils.core import setup

setup(name='Python Rewriter', \
	version='0.2', \
	description='Tools to automatically rewrite Python code', \
	author='Chris Warburton', \
	author_email='chriswarbo@gmail.com', \
	url='http://gitorious.org/python-decompiler'
	packages=['python_rewriter', 'diet_python'], \
	provides=['python_rewriter'])
