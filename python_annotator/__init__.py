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
Institute, who is persuing similar work in Java and Smalltalk."""
