#!/usr/bin/python2

import mglobals

#Lexer

tokens         = ('PRINT','INT','BOOL','PLUS','MINUS','EQUALS','IDENTIFIER',\
		  'INPUT','AND','OR','NOT','IF','ELSE','IS','TRUE','FALSE',\
		  'DOUBLEEQUALS','NOTEQUALS','LPAREN','RPAREN','LBRACKET',\
		  'RBRACKET','LBRACE','RBRACE','COMMA','COLON')
t_PRINT        = r'print'
t_INPUT        = r'input'
t_PLUS         = r'\+'
t_EQUALS       = r'='
t_MINUS        = r'-'
t_AND          = r'and'
t_OR           = r'or'
t_NOT          = r'not'
t_IF           = r'if'
t_ELSE         = r'else'
t_IS           = r'is'
t_DOUBLEEQUALS = r'=='
t_NOTEQUALS    = r'!='
t_LPAREN       = r'\('
t_RPAREN       = r'\)'
t_LBRACKET     = r'\['
t_RBRACKET     = r'\]'
t_LBRACE       = r'\{'
t_RBRACE       = r'\}'
t_COMMA        = r'\,'
t_COLON        = r'\:'

t_ignore = ' \t'
t_ignore_COMMENT = r'\#.*'

reserved = {
	'print':'PRINT',
	'input':'INPUT'
}

def t_INT(t):
	r'\d+'
	try:
		t.value = int(t.value)
	except ValueError:
		print "integer value too large", t.value
		t.value = 0
	return t
def t_BOOL(t):
	r'\d+'

def t_newline(t):
	r'\n+'
	t.lexer.lineno += t.value.count("\n")
	
def t_IDENTIFIER(t):
	r'[a-zA-Z\_][a-zA-Z0-9\_]*'
	t.type = reserved.get(t.value,'IDENTIFIER')
	return t

def t_error(t):
	print "Illegal character '%s'" % t.value[0]
	t.lexer.skip(1)

import ply.lex as lex

lexer = lex.lex()

#Parser
from compiler.ast import *

precedence = (
	('nonassoc','IDENTIFIER','PRINT'),
	('left','PLUS','MINUS')
)

def p_program(t):
	'''program : module'''
	t[0] = t[1]

def p_module(t):
	'''module : statement'''
	t[0] = Module(None,t[1])
	
def p_statement(t):
	'''statement : simple_statement
	             | statement simple_statement'''
	if(len(t)==2):
		t[0] = Stmt([t[1]])
	elif(len(t)==3):
		t[0] = Stmt(t[1].nodes + [t[2]])
	

def p_simple_statement(t):
	'''simple_statement : PRINT expression
	                    | name EQUALS expression
			    | target EQUALS expression 
	                    | expression '''
	if(len(t)==3):
		# PRINT expression
		t[0] = Printnl([t[2]],None)
	elif(len(t)==4):
		# name EQUALS expression
		t[0] = Assign([AssName(t[1].name,'OP_ASSIGN')],t[3])
	elif(
	elif(len(t)==2):
		# expression
		t[0] = Discard(t[1])

def p_expression_singular(t):
	'''expression : name
	              | decimalinteger '''
	t[0] = t[1]


def p_expression_unarysub(t):
	'''expression : MINUS expression'''
	t[0] = UnarySub(t[2])

def p_expression_add(t):
	'''expression : expression PLUS expression'''
	t[0] = Add((t[1],t[3]))
	

def p_expression_nested(t):
	'''expression : LPAREN expression RPAREN'''
	t[0] = t[2]


def p_expression_input(t):
	'''expression : INPUT LPAREN RPAREN '''
	t[0] = CallFunc(Name('input'),[])


def p_decimalinteger(t):
	'decimalinteger : INT'
	t[0] = Const(t[1])

def p_name(t):
	'name : IDENTIFIER'
	t[0] = Name(t[1])



def p_error(t):
	print "Syntax error with %s" %(t)
	print "Syntax error at '%s' on line %s with token:" % (t.value , t.lineno)
	print "    ",t

import ply.yacc as yacc
parser = yacc.yacc()


