import compiler

from pymeta.grammar import OMeta

#tree = str(compiler.parseFile('transformer.py'))

prog = """
import StringIO as Jeff
from lxml.etree import Element, SubElement
from threading import Thread

#def square(num1, num2):
#	def each(x):
#		return x**2
#	x = each(num1) + each(num2)
#	return num*num

#print square(1., -3.2)

#x = 1 + 2 * 3 / 4 - 1
#print str(x) + 'hel',
#print 'lo'
#a, b = x, y
#c = (a, (x,y))
#d = [a, b, c, (x, y)]
#e = d.sort()
"""

print prog

tree = str(compiler.parse(prog))

print tree


gram = """

any ::= <thing 0>*:t													=> t



thing :i ::= <string i>:s												=> s
           | <quoted i>:q												=> q
           | <module i>:m												=> m
           | <stmt i>:s													=> s
           | <assign i>:a												=> a
           | <assname i>:a												=> a
           | <asstuple i>:a												=> a
           | <name i>:n													=> n
           | <add i>:a													=> a
           | <sub i>:s													=> s
           | <mul i>:m													=> m
           | <div i>:d													=> d
           | <power i>:p												=> p
           | <return i>:r												=> r
           | <const i>:c												=> c
           | <unarysub i>:u												=> u
           | <tuplenode i>:t											=> t
           | <listnode i>:l												=> l
           | <import i>:m												=> m
           | <from i>:f													=> f
           | <callfunc i>:c												=> c
           | <printnl i>:p												=> p
           | <print i>:p												=> p
           | <getattr i>:a												=> a
           | <function i>:f												=> f
           | <discard i>:d												=> d
           | <sep i>:s													=> ''
           | <tuple i>:t												=> t
           | <list i>:l													=> l
           | <none i>:n													=> n
           | <num i>:n													=> str(n)
           | <anything>:a												=> a



num :i ::= '-' <digit>+:whole '.' <digit>+:frac							=> '-'+''.join(whole)+'.'+''.join(frac)
         | '-' <digit>+:whole '.'										=> '-'+''.join(whole)+'.'
         | '-' <digit>+:whole											=> '-'+''.join(whole)
         | <digit>+:whole '.' <digit>+:frac								=> ''.join(whole)+'.'+''.join(frac)
         | <digit>+:whole '.'											=> ''.join(whole)+'.'
         | <digit>+:whole												=> ''.join(whole)



sep :i ::= <token ', '>													=> ', '



quoted :i ::= <token "'"> <quoteval i>:q								=> q

quoteval :i ::= <token "'">											=> ''
              | <anything>:a <quoteval i>:q								=> a+q



tuple :i ::= <token '('> <tupleval i>:t									=> t

tupleval :i ::= <token ')'>												=> ''
              | <thing i>:t <tupleval i>:v								=> t+v



list :i ::= <token '['> <listval i>:l									=> l

listval :i ::= <token ']'>												=> ''
             | <thing i>:t <listval i>:v								=> t+v



none :i ::= <token 'None'>												=> 'None'



module :i ::= <token 'Module'> <modcontents i>:t						=> t

modcontents :i ::= <token '('> <none i> <sep i> <tupleval i>:t			=> t
                 | <token '('> <quoted i>:d <sep i> <tupleval i>:t		=> '""'+'"' + \"""\n\""" + d + \"""\n\""" + '""'+'"' + t



stmt :i ::= <token 'Stmt'> <stmtcontents i>:s							=> s

stmtcontents :i ::= <token '(['> <stmtlines i>:s <token ')'>			=> s

stmtlines :i ::= <token ']'>											=> ''
               | <thing i>:t <stmtlines i>:s							=> i*'\t' + t + \"""\n\""" + s



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



assign :i ::= <token 'Assign(['> <assignleft i>:l <sep i>
                                 <assignright i>:r <token ')'>			=> l+r

assignleft :i ::= <token ']'>											=> ''
                | <sep i> <assignleft i>:l								=> l
                | <thing i>:t <assignleft i>:l							=> t+' = '+l

assignright :i ::= <thing i>:t											=> t



assname :i ::= <token 'AssName'> <assnamecontents i>:a					=> a

assnamecontents :i ::= <token '('> <quoted i>:name <sep i>
                                   <quoted i>:op <token ')'>			=> name



asstuple :i ::= <token 'AssTuple(['> <asstuplecontents i>:a <token ')'>	=> '('+a[:-2]+')'

asstuplecontents :i ::= <token ']'>										=> ''
                      | <sep i> <asstuplecontents i>:l					=> l
                      | <thing i>:t <asstuplecontents i>:l				=> t+', '+l



add :i ::= <token 'Add'> <addcontents i>:a								=> a

addcontents :i ::= <token '(('> <thing i>:left <sep i>
                                <thing i>:right <token '))'>			=> left + ' + ' + right



sub :i ::= <token 'Sub'> <subcontents i>:s								=> s

subcontents :i ::= <token '(('> <thing i>:left <sep i>
                                <thing i>:right <token '))'>			=> left + ' - ' + right



mul :i ::= <token 'Mul'> <mulcontents i>:m								=> m

mulcontents :i ::= <token '(('> <thing i>:left <sep i>
                                <thing i>:right <token '))'>			=> left + ' * ' + right



div :i ::= <token 'Div'> <divcontents i>:d								=> d

divcontents :i ::= <token '(('> <thing i>:left <sep i>
                                <thing i>:right <token '))'>			=> left + ' / ' + right



power :i ::= <token 'Power(('> <thing i>:o <sep i>
                              <thing i>:p <token '))'>					=> o+'**'+p



unarysub :i ::= <token 'UnarySub('> <thing i>:t <token ')'>				=> '-'+t



const :i ::= <token 'Const'> <constcontents i>:c						=> c

constcontents :i ::= <token '('> <thing i>:value <token ')'>			=> value



string :i ::= <quoted i>:q												=> '\"""'+q+'\"""'



callfunc :i ::= <token 'CallFunc'> <callfunccontents i>:c				=> c

callfunccontents :i ::= <token '('> <thing i>:n <sep i>
                                    <token '['> <callfuncargs i>:a <sep i>
                                    <thing i>:three <sep i>
                                    <thing i>:four <token ')'>			=> n+'('+a+')'

callfuncargs :i ::= <token ']'>											=> ''
                  | <sep i> <callfuncargs i>:a							=> ', '+a
                  | <thing i>:t <callfuncargs i>:a						=> t+a



discard :i ::= <token 'Discard'> <tuple i>								=> ''



printnl :i ::= <token 'Printnl(['> <printcontents i>:p <sep i>
                                  <thing i>:x <token ')'>				=> 'print('+p+')'

printcontents :i ::= <token ']'>										=> ''
                   | <quoted i>:q <printcontents i>:p					=> "'"+q+"'"+p
                   | <sep i> <printcontents i>:p						=> ', '+p
                   | <thing i>:t <printcontents i>:p					=> t+p



print :i ::= <token 'Print(['> <printcontents i>:p <sep i>
                               <thing i>:x <token ')'>					=> 'print('+p+'),'



import :i ::= <token 'Import(['> <importcontents i>:i <token ')'>		=> i

importcontents :i ::= <token ']'>										=> ''
                    | <token '('> <quoted i>:m <sep i>
                      <none i> <token ')' <importcontents i>:c			=> 'import '+m+c
                    | <token '('> <quoted i>:m <sep i>
                      <quoted i>:n <token ')'> <importcontents i>:c		=> 'import '+m+' as '+n+c
                    | <sep i> <importcontents i>:c						=> \"""\n\"""+c



from :i ::= <token 'From('> <quoted i>:m <sep i> <token '['>
            <fromcontents i>:c <sep i> <thing i>:X <token ')'>			=> 'from '+m+' import '+c

fromcontents :i ::= <token ']'>											=> ''
                  | <token '('> <quoted i>:m <sep i>
                    <none i> <token ')'> <fromcontents i>:c				=> m+c
                  | <token '('> <quoted i>:m <sep i>
                    <quoted i>:n <token ')'> <fromcontents i>:c			=> m+' as '+n+c
                  | <sep i> <fromcontents i>:c							=> ', '+c



name :i ::= <token 'Name'> <namecontents i>:n							=> n

namecontents :i ::= <token '('> <quoted i>:n <token ')'>				=> n



tuplenode :i ::= <token 'Tuple(['> <tuplenodecontents i>:t ')'			=> '('+t[:-2]+')'

tuplenodecontents :i ::= ']'											=> ''
                       | <sep i> <tuplenodecontents i>:t				=> t
                       | <thing i>:t <tuplenodecontents i>:c			=> t+', '+c



listnode :i ::= <token 'List(['> <listnodecontents i>:l <token ')'>		=> '['+l[:-2]+']'

listnodecontents :i ::= ']'												=> ''
                      | <sep i> <listnodecontents i>:l					=> l
                      | <thing i>:t <listnodecontents i>:l				=> t+', '+l



getattr :i ::= <token 'Getattr('> <thing i>:o <sep i>
                                  <thing i>:a <token ')'>				=> o+'.'+a



return :i ::= <token 'Return('> <thing i>:t <token ')'>					=> 'return '+t

"""



print "Making"

g = OMeta.makeGrammar(gram, {})

print "Treeing"

ast_tree = g(tree)

#test_tree = g(test)

#print test_tree.apply('literal')

print "Applying"

mod = ast_tree.apply('any')

for l in mod:
	print l

#c = ast_tree.apply('const')
