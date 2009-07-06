#!/usr/bin/env python

import compiler
import sys

from pymeta.grammar import OMeta, OMetaGrammar

def strip_comments(s):
	"""Simple Python loop to strip out anything on a line after a #."""
	r = ''
	in_comment = False
	for character in s:
		if in_comment:
			if character == '\n':
				r = r + character
				in_comment = False
		else:
			if character == "#":
				in_comment = True
			else:
				r = r + character
	return r

gram = """
# This grammar matches against the ASTs produced by Python 2.x's
# compiler module. It produces Python code to match the AST.

# The parameter "i" given to most rules is the desired level of
# indentation for the generated code. The number used in the rule "any"
# is sufficient to indent the whole output, since it is subsequently
# passed to every other rule.

# "any" is the entry point into the AST. It matches any number of AST
# nodes and outputs the generated code. The number given to the "things"
# is the initial amount of indentation to use in the output.

any ::= <thing 0>*:t													=> ''.join(t)

# A "thing" is anything of interest. It will match anything, since it
# includes a trivial match at the bottom. The trick here is in the
# ordering. Strings are first, since they can contain any text whilst
# still remaining just data. Nodes follow, then data structures, and
# finally a trivial match.

# "string" matches anything in quotes, and outputs that including the
# quotes (to get an output without the quotes used "quoted")
thing :i ::= <string i>:s												=> s

           # "module" is a Python module, ie. a file of Python code
           | <module i>:m												=> m

           # "class" is a Python class
           | <class i>:c												=> c

           # "stmt" is a statement, ie. a list of commands
           | <stmt i>:s													=> s

           # "assign" is the binding of a value to something
           | <assign i>:a												=> a

           # "assname" is the binding of a value to a variable name
           | <assname i>:a												=> a

           # "asstuple" is the binding of members of one tuple to another
           | <asstuple i>:a												=> a

           | <augassign i>:a											=> a

           # "name" calls a variable
           | <name i>:n													=> n

           # "if" matches if statements
           | <if i>:f													=> f

           | <for i>:f													=> f

           | <while i>:w												=> w

           # "not" matches a not operation
           | <not i>:n													=> n

           # "and" matches an and operation
           | <and i>:a													=> a

           # "or" matches an or operation
           | <or i>:o													=> o

           # "dict" matches a Python dictionary datastructure
           | <dict i>:d													=> d

           # "pass" matches a pass statement
           | <pass i>:p													=> p

           ## The following all end up with surrounding brackets. It's
           ## not pretty, but it does the job for now.

           # "add" is addition
           | <add i>:a													=> '('+a+')'

           # "sub" is subtraction
           | <sub i>:s													=> '('+s+')'

           # "mul" is multiplication
           | <mul i>:m													=> '('+m+')'

           # "div" is division
           | <div i>:d													=> '('+d+')'

           # "power" is exponentiation
           | <power i>:p												=> '('+p+')'

           # "return" is a return statement
           | <return i>:r												=> r

           # "const" is a constant value
           | <const i>:c												=> c

           # "unarysub" negates a value (eg. unary sub of 1 is -1)
           | <unarysub i>:u												=> u

           # "tuplenode" is a tuple in the original code (not to be
           # confused with "tuple" which is a series of values in
           # brackets)
           | <tuplenode i>:t											=> t

           # "listnode" is a list in the original code (not to be
           # confused with "list" which is a series of values in square
           # brackets)
           | <listnode i>:l												=> l

           # "import" imports modules into the current namespace, and
           # possibly renames them if instructed to
           | <import i>:m												=> m

           # "from" imports specified things from one module into the
           # current namespace, renaming them if instructed to
           | <from i>:f													=> f

           # "callfunc" is a function call, complete with arguments
           | <callfunc i>:c												=> c

           # "printnl" is a normal print statement, ending the line and
           # flushing the output buffer
           | <printnl i>:p												=> p

           # "print" is a print statement followed by a comma, which
           # prevents the buffer from flushing and doesn't end in a new
           # line
           | <print i>:p												=> p

           # "getattr" gets a value from some namespace (for example a
           # property of an object)
           | <getattr i>:a												=> a

           | <compare i>:c												=> c

           | <subscript i>:s											=> s

           | <tryexcept i>:t											=> t

           # "function" is a function definition, complete with code and
           # arguments
           | <function i>:f												=> f

           # "discard" wraps commands which have no effect on the
           # program
           | <discard i>:d												=> d

           # "sep" is a comma followed by a space, used as a separator
           # in tuples and lists
           | <sep i>:s													=> ''

           # "tuple" matches a series of comma-separated values in
           # brackets. Not to be confused with "tuplenode" which matches
           # a Python tuple datastructure
           | <tuple i>:t												=> t

           # "list" matches a series of comma-separated values in square
           # brackets. Not to be confused with "listnode" which matches
           # a Python list datastructure
           | <list i>:l													=> l

           # "none" matches Python's null value. Note that this
           # is simply the text "None", and thus should be used
           # carefully around things like strings, which could contain
           # those four characters
           | <none i>:n													=> n

           # "num" matches a number, positive or negative, integer or
           # decimal
           | <num i>:n													=> str(n)

           # This catches anything else that occurs in the stream if it
           # doesn't match something above. It consumes 1 character at a
           # time
           | <anything>:a												=> a


## The following match the AST nodes of the compiler module

# Matches addition
add :i ::= <token 'Add'> <addcontents i>:a								=> a

addcontents :i ::= <token '(('> <thing i>:left <sep i>
                                <thing i>:right <token '))'>			=> left + ' + ' + right


# Matches an and operator
and :i ::= <token 'And(['> <andcontents i>:a <token ')'>				=> a

andcontents :i ::= <token ']'>											=> ''
                 | <sep i> <andcontents i>:a							=> ' and '+a
                 | <thing i>:t <andcontents i>:a						=> '('+t+')'+a


# Matches the assignment of an attribute								#################################
assattr :i ::= ' '


# Matches binding a value to a variable name
assname :i ::= <token 'AssName'> <assnamecontents i>:a					=> a

assnamecontents :i ::= <token '('> <quoted i>:name <sep i>
                                   <quoted i>:op <token ')'>			=> name


# Matches binding multiple values at once
asstuple :i ::= <token 'AssTuple(['> <asstuplecontents i>:a <token ')'>	=> '('+a[:-2]+')'

asstuplecontents :i ::= <token ']'>										=> ''
                      | <sep i> <asstuplecontents i>:l					=> l
                      | <thing i>:t <asstuplecontents i>:l				=> t+', '+l


# Matches an assertion													###################################
assert :i ::= ' '


# Matches a value binding
assign :i ::= <token 'Assign(['> <assignleft i>:l <sep i>
                                 <assignright i>:r <token ')'>			=> l+r

assignleft :i ::= <token ']'>											=> ''
                | <sep i> <assignleft i>:l								=> l
                | <thing i>:t <assignleft i>:l							=> t+' = '+l

assignright :i ::= <thing i>:t											=> t


# Matches a combined operation and assign, such as "+=" or "/="
augassign :i ::= <token 'AugAssign('> <thing i>:l <sep i>
                                      <quoted i>:o <sep i>
                                      <thing i>:r <token ')'>			=> l+' '+o+' '+r


#																		####################################
backquote :i ::= ' '


#																		#####################################
bitand :i ::= ' '


#																		####################################
bitor :i ::= ' '


#																		###############################
bitxor :i ::= ' '


#																		####################################
break :i ::= ' '


# Matches a function call
callfunc :i ::= <token 'CallFunc'> <callfunccontents i>:c				=> c

callfunccontents :i ::= <token '('> <thing i>:n <sep i>
                                    <token '['> <callfuncargs i>:a <sep i>
                                    <thing i>:three <sep i>
                                    <thing i>:four <token ')'>			=> n+'('+a+')'

callfuncargs :i ::= <token ']'>											=> ''
                  | <sep i> <callfuncargs i>:a							=> ', '+a
                  | <thing i>:t <callfuncargs i>:a						=> t+a


# Matches a Python class
class :i ::= <token 'Class('> <quoted i>:n <sep i> <token '['>
             <classcontents i>:c <sep i> <none i> <sep i> <stmt i+1>:s
             <token ')'>												=> 'class '+n+'('+c+\"""):\n\"""+s

classcontents :i ::= <token ']'>										=> ''
                   | <sep i> <classcontents i>:c						=> ', '+c
                   | <thing i>:t <classcontents i>:c					=> t+c


# Matches comparisons
compare :i ::= <token 'Compare('> <thing i>:l <sep i>
               <token '['> <comparecontents i>:r <token ')'>			=> '('+l+') '+r

comparecontents :i ::= <token ']'>										=> ''
                     | <sep i> <comparecontents i>:r					=> r
                     | <token '('> <quoted i>:c <sep i> <thing i>:r
                       <token ')'> <comparecontents i>:e				=> c+' ('+r+') '+e


# Matches constants
const :i ::= <token 'Const'> <constcontents i>:c						=> c

constcontents :i ::= <token '('> <thing i>:value <token ')'>			=> value


#																		#######################################
continue :i ::= ' '


#																		###################################
decorators :i ::= ' '


# Matches a dictionary datastructure
dict :i ::= <token 'Dict(['> <dictcontents i>:d <token ')'>				=> '{'+d+'}'

dictcontents :i ::= <token ']'>											=> ''
                  | <sep i> <dictcontents i>:d							=> ', '+d
                  | <token '('> <thing i>:k <sep i>
                                <thing i>:v <token ')'>
                                <dictcontents i>:d						=> k+':'+v+d


# Matches possibly redundant commands
discard :i ::= <token 'Discard('> <thing i>:t <token ')'>				=> t


# Matches division
div :i ::= <token 'Div'> <divcontents i>:d								=> d

divcontents :i ::= <token '(('> <thing i>:left <sep i>
                                <thing i>:right <token '))'>			=> left + ' / ' + right


#																		###################################
ellipsis :i ::= ' '


#																		##################################
expression :i ::= ' '


#																		###################################
exec :i ::= ' '


#																		###################################
floordiv :i ::= ' '


# Matches for loops
for :i ::= <token 'For('> <assname i>:a <sep i> <thing i>:c <sep i>
                          <stmt i+1>:s <sep i> <none i> <token ')'>		=> 'for '+a+' in '+c+\""":\n\"""+s


# Matches namespace injections
from :i ::= <token 'From('> <quoted i>:m <sep i> <token '['>
            <fromcontents i>:c <sep i> <thing i>:X <token ')'>			=> 'from '+m+' import '+c

fromcontents :i ::= <token ']'>											=> ''
                  | <token '('> <quoted i>:m <sep i>
                    <none i> <token ')'> <fromcontents i>:c				=> m+c
                  | <token '('> <quoted i>:m <sep i>
                    <quoted i>:n <token ')'> <fromcontents i>:c			=> m+' as '+n+c
                  | <sep i> <fromcontents i>:c							=> ', '+c


# Matches a Python function definition
function :i ::= <token 'Function('>
                <thing i>:d <sep i>
                <quoted i>:n <sep i>
                <token '['> <functionargs i>:a <sep i>
                <thing i>:X <sep i>
                <thing i>:Y <sep i>
                <thing i>:Z <sep i>
                <thing i+1>:s <token ')'>								=> 'def ' + n + '(' + a + '):' + \"""\n\""" + s

functionargs :i ::= <token ']'>											=> ''
                  | <sep i> <functionargs i>:f							=> ', '+f
                  | <quoted i>:q <functionargs i>:f						=> q+f
                  | <thing i>:t <functionargs i>:f						=> t+f


#																		################################
genexpr :i ::= ' '


#																		##############################
genexprfor :i ::= ' '


#																		################################
genexprif :i ::= ' '


#																		##############################
genexprinner :i ::= ' '


# Matches attribute lookup
getattr :i ::= <token 'Getattr('> <thing i>:o <sep i>
                                  <quoted i>:a <token ')'>				=> o+'.'+a


#																		##########################
global :i ::= ' '


#If([(Compare(Name('keyPressed'), [('==', Const('space'))]), Stmt([AugAssign(Subscript(Name('velocity'), 'OP_APPLY', [Const(0)]), '+=', Const(10)), AugAssign(Subscript(Name('velocity'), 'OP_APPLY', [Const(0)]), '*=', Const(50)), AugAssign(Subscript(Name('velocity'), 'OP_APPLY', [Const(1)]), '+=', Const(10)), AugAssign(Subscript(Name('velocity'), 'OP_APPLY', [Const(1)]), '*=', Const(50))]))], None)
# Matches an if statement
if :i ::= <token 'If([('> <thing i>:c <sep i>
                         <stmt i+1>:s <token ')'> <sep i>
                         <elifs i>:e <sep i> <else i>:x <token ')'>		=> "if "+c+\""":\n\"""+s+\"""\n\"""+e+\"""\n\"""+x

elifs :i ::= <token ']'>												=> ''
           | <sep i> <elifs i>:e										=> e
           | <token '('> <thing i>:c <sep i>
                         <stmt i+1>:s <token ')'> <elifs i>:x			=> "elif "+c+\""":\n\"""+s+x

else :i ::= <none i>													=> ''
          | <stmt i+1>:s												=> \"""else:\n\"""+s


# Matches module imports
import :i ::= <token 'Import(['> <importcontents i>:c <token ')'>		=> c

importcontents :i ::= <token ']'>										=> ''
                    | <token '('> <quoted i>:m <sep i>
                      <none i> <token ')'> <importcontents i>:c			=> 'import '+m+c
                    | <token '('> <quoted i>:m <sep i>
                      <quoted i>:n <token ')'> <importcontents i>:c		=> 'import '+m+' as '+n+c
                    | <sep i> <importcontents i>:c						=> \"""\n\"""+c


#																		############################
import :i ::= ' '


#																		################################
keyword :i ::= ' '


#																		############################
lambda :i ::= ' '


#																		##########################
leftshift :i ::= ' '


# Matches a list datastructure
listnode :i ::= <token 'List(['> <listnodecontents i>:l <token ')'>		=> '['+l[:-2]+']'

listnodecontents :i ::= ']'												=> ''
                      | <sep i> <listnodecontents i>:l					=> l
                      | <thing i>:t <listnodecontents i>:l				=> t+', '+l


#																		###############################
listcomp :i ::= ' '


#																		##############################
listcompfor :i ::= ' '


#																		###########################
listcompif :i ::= ' '


#																		###########################
mod :i ::= ' '


# Matches a Python module and its contents
module :i ::= <token 'Module'> <modcontents i>:t						=> t

modcontents :i ::= <token '('> <none i> <sep i> <tupleval i>:t			=> t
                 | <token '('> <quoted i>:d <sep i> <tupleval i>:t		=> '""'+'"' + \"""\n\""" + d + \"""\n\""" + '""'+'"' + t


# Matches multiplication
mul :i ::= <token 'Mul'> <mulcontents i>:m								=> m

mulcontents :i ::= <token '(('> <thing i>:left <sep i>
                                <thing i>:right <token '))'>			=> left + ' * ' + right


# Matches a variable name
name :i ::= <token 'Name'> <namecontents i>:n							=> n

namecontents :i ::= <token '('> <quoted i>:n <token ')'>				=> n


# Matches a not operation
not :i ::= <token 'Not('> <thing i>:t <token ')'>						=> 'not ('+t+')'


# Matches an or operator
or :i ::= <token 'Or(['> <orcontents i>:o <token ')'>					=> o

orcontents :i ::= <token ']'>											=> ''
                | <sep i> <orcontents i>:o								=> ' or '+o
                | <thing i>:t <orcontents i>:o							=> '('+t+')'+o


# Matches a pass statement
pass :i ::= <token 'Pass()'>											=> 'pass'


# Matches exponentiation
power :i ::= <token 'Power(('> <thing i>:o <sep i>
                              <thing i>:p <token '))'>					=> o+'**'+p

# Matches print with no newline
print :i ::= <token 'Print(['> <printcontents i>:p <sep i>
                               <thing i>:x <token ')'>					=> 'print('+p+'),'

printcontents :i ::= <token ']'>										=> ''
                   | <quoted i>:q <printcontents i>:p					=> "'"+q+"'"+p
                   | <sep i> <printcontents i>:p						=> ', '+p
                   | <thing i>:t <printcontents i>:p					=> t+p


# Matches print
printnl :i ::= <token 'Printnl(['> <printcontents i>:p <sep i>
                                  <thing i>:x <token ')'>				=> 'print('+p+')'


#																		##########################
raise :i ::= ' '


# Matches return statements
return :i ::= <token 'Return('> <thing i>:t <token ')'>					=> 'return '+t


#																		#########################
rightshift :i ::= ' '


#																		#########################
slice :i ::= ' '


#																		########################
sliceobj :i ::= ' '


# Matches a series of Python commands
stmt :i ::= <token 'Stmt'> <stmtcontents i>:s							=> s

stmtcontents :i ::= <token '(['> <stmtlines i>:s <token ')'>			=> s

stmtlines :i ::= <token ']'>											=> ''
               | <thing i>:t <stmtlines i>:s							=> i*'\t' + t + \"""\n\""" + s


# Matches subtraction
sub :i ::= <token 'Sub'> <subcontents i>:s								=> s

subcontents :i ::= <token '(('> <thing i>:left <sep i>
                                <thing i>:right <token '))'>			=> left + ' - ' + right


# Matches indexing of an object (eg. mylist[5])
subscript :i ::= <token 'Subscript('> <thing i>:l <sep i>
                 <quoted i> <sep i>
                 <token '['> <thing i>:s <token '])'>					=> l+'['+s+']'

#TryExcept(Stmt([Printnl([Const('x')], None)]), [(Name('SyntaxError'), None, Stmt([Pass()])), (Name('ParseError'), None, Stmt([Printnl([Const('y')], None)])), (None, None, Stmt([Printnl([Const('z')], None)]))], None)
# Matches "try:" "except:" statements
tryexcept :i ::= <token 'TryExcept('> <stmt i+1>:t <sep i> <token '['>
                 <trycontents i>:e <sep i> <none i> <token ')'>			=> \"""try:\n\"""+t+e
               | <token 'TryExcept('> <stmt i+1>:t <sep i> <token '['>
                 <trycontents i>:e <sep i> <stmt i+1>:s <token ')'>		=> \"""try:\n\"""+t+e+\"""\n\"""+(i*'\t')+\"""else:\n\"""+s

trycontents :i ::= <token ']'>											=> ''
                 | <sep i> <trycontents i>:t							=> t
                 | <token '('> <none i> <sep i> <none i> <sep i>
                   <stmt i+1>:e <token ')'> <trycontents i>:c			=> \"""except:\n\"""+e+c
                 | <token '('> <thing i>:x <sep i> <none i>:y <sep i>
                   <stmt i+1>:e <token ')'> <trycontents i>:c			=> 'except '+x+\""":\n\"""+e+c
                 | <token '('> <thing i>:x <sep i> <thing i>:y <sep i>
                   <stmt i+1>:e <token ')'> <trycontents i>:c			=> 'except '+x+', '+y+\""":\n\"""+e+c


#																		#############################
tryfinally :i ::= ' '


# Matches a tuple datastructure
tuplenode :i ::= <token 'Tuple(['> <tuplenodecontents i>:t ')'			=> '('+t[:-2]+')'

tuplenodecontents :i ::= ']'											=> ''
                       | <sep i> <tuplenodecontents i>:t				=> t
                       | <thing i>:t <tuplenodecontents i>:c			=> t+', '+c


#																		###################
unaryadd :i ::= ' '


# Matches negative values
unarysub :i ::= <token 'UnarySub('> <thing i>:t <token ')'>				=> '-'+t


# Matches while loops
while :i ::= <token 'While('> <thing i>:t <sep i>
                              <stmt i+1>:s <sep i>
                              <thing i> <token ')'>						=> 'while '+t+\""":\n\"""+s


#																		#######################
with :i ::= ' '


#																		#########################
yield :i ::= ' '


## The following match common value formats used in the above

# Matches numbers
num :i ::= '-' <digit>+:whole '.' <digit>+:frac							=> '-'+''.join(whole)+'.'+''.join(frac)
         # whole negative reals
         | '-' <digit>+:whole '.'										=> '-'+''.join(whole)+'.'
         # negative integers
         | '-' <digit>+:whole											=> '-'+''.join(whole)
         # positive reals
         | <digit>+:whole '.' <digit>+:frac								=> ''.join(whole)+'.'+''.join(frac)
         # positive whole reals and zero
         | <digit>+:whole '.'											=> ''.join(whole)+'.'
         # positive integers and zero
         | <digit>+:whole												=> ''.join(whole)


# Matches comma separation
sep :i ::= <token ', '>													=> ', '


# Matches a value in quotes, returning the value with no quotes
# (also see "string")
quoted :i ::= <token "'"> <quoteval i>:q								=> q

quoteval :i ::= <token "'">												=> ''
              | <anything>:a <quoteval i>:q								=> a+q


# Matches a value in quotes, returning the value and the quotes. For
# a rule which doesn't return the quotes see "quoted"
string :i ::= <quoted i>:q												=> '\"""'+q+'\"""'


# Matches a series of comma-separated values in brackets
tuple :i ::= <token '('> <tupleval i>:t									=> t

tupleval :i ::= <token ')'>												=> ''
              | <thing i>:t <tupleval i>:v								=> t+v


# Matches a series of comma-separated values in square brackets
list :i ::= <token '['> <listval i>:l									=> l

listval :i ::= <token ']'>												=> ''
             | <thing i>:t <listval i>:v								=> t+v


# Matches Python's null object
none :i ::= <token 'None'>												=> 'None'
"""

g = OMeta.makeGrammar(strip_comments(gram), {})

if __name__ == '__main__':
	toparse = sys.argv[1]

	tree = str(compiler.parseFile(toparse))

	print "Assigning input"

	ast_tree = g(tree)

	print "Applying grammar"

	generated = ast_tree.apply('any')

	try:
		assert str(compiler.parse(generated)) == tree
		print "Success"
	except:
		print "Fail"
		print tree
		print ''
		print generated
