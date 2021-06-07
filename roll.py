#!/usr/bin/env python

import sys
import operator
from random import randint
from sly import Lexer, Parser

symbol = {
    operator.add: '+',
    operator.sub: '-',
    operator.mul: 'x',
    operator.truediv: '/',
}

class ExpressionOperator():

    def __init__(self, left, op, right):
        self.left=left
        self.right=right
        self.op=op

    def eval(self):
        return self.op(self.left.eval(), self.right.eval())

    def __str__(self):
        return '(' + str(self.left) + symbol[self.op] + str(self.right) + ')'

class ExpressionNeg():

    def __init__(self, right):
        self.right=right

    def eval(self):
        return operator.neg(self.right.eval())

    def __str__(self):
        return '(-' + str(self.right) + ')'

class ExpressionAdd(ExpressionOperator):

    def __init__(self, left, right):
        super().__init__(left, operator.add, right)

class ExpressionSub(ExpressionOperator):

    def __init__(self, left, right):
        super().__init__(left, operator.sub, right)

class ExpressionMul(ExpressionOperator):

    def __init__(self, left, right):
        super().__init__(left, operator.mul, right)

class ExpressionDiv(ExpressionOperator):

    def __init__(self, left, right):
        super().__init__(left, operator.truediv, right)

class ExpressionDice():

    def __init__(self, left, right):
        self.left=left
        self.right=right

    def eval(self):
        return  sum([ randint(1,self.right.eval()) for _ in range(self.left.eval())])

    def __str__(self):
        return str(self.left) + 'd' + str(self.right)

class ExpressionNum():

    def __init__(self, num):
        self.num=num

    def eval(self):
        return self.num

    def __str__(self):
        return str(self.num)

class ExpressionList(list):

    def eval(self):
        return [ item.eval() for item in self ]

    def __str__(self):
        return '[' + ", ".join([ str(item) for item in self ]) + ']'

class RollLexer(Lexer):
    tokens = { INTEGER }
    ignore = ' \t'
    literals = { '=', '+', '-', '*', 'x', '/', '(', ')', 'd' , ','}

    @_(r'\d+')
    def INTEGER(self, t):
        t.value = int(t.value)
        return t

    def error(self, t):
        print("Illegal character '%s'" % t.value[0])
        self.index += 1

class RollParser(Parser):
    tokens = RollLexer.tokens

    precedence = (
        ('left', ','),
        ('left', '+', '-'),
        ('left', '*', 'x', '/'),
        ('left', 'd'),
        ('right', 'UMINUS'),
        )

    def __init__(self):
        pass

    @_('list_')
    def statement(self, p):
        return p.list_

    @_('expr')
    def statement(self, p):
        return p.expr

    @_('expr "+" expr')
    def expr(self, p):
        return ExpressionAdd( p.expr0, p.expr1)

    @_('expr "-" expr')
    def expr(self, p):
        return ExpressionSub( p.expr0, p.expr1)

    @_('expr "*" expr')
    def expr(self, p):
        return ExpressionMul( p.expr0, p.expr1)

    @_('expr "x" expr')
    def expr(self, p):
        return ExpressionMul( p.expr0, p.expr1)

    @_('expr "/" expr')
    def expr(self, p):
        return ExpressionDiv( p.expr0, p.expr1)

    @_('"-" expr %prec UMINUS')
    def expr(self, p):
        return ExpressionNeg(p.expr)

    @_('"(" expr ")"')
    def expr(self, p):
        return p.expr

    @_('INTEGER')
    def expr(self, p):
        return ExpressionNum(p.INTEGER)
    
    @_('INTEGER "d" INTEGER')
    def expr(self, p):
        return ExpressionDice(ExpressionNum(p.INTEGER0), ExpressionNum(p.INTEGER1))
    
    @_('"d" INTEGER')
    def expr(self, p):
        return ExpressionDice(ExpressionNum(1), ExpressionNum(p.INTEGER))

    @_('expr "," expr')
    def list_(self, p):
        return ExpressionList([p.expr0, p.expr1])

    @_('list_ "," expr')
    def list_(self, p):
        list_ = p.list_
        list_.append(p.expr)
        return list_

if __name__ == "__main__":
    lexer = RollLexer()
    parser = RollParser()
    text = "".join(sys.argv[1:])
    ast = parser.parse(lexer.tokenize(text))
    print(f"evaluating: {str(ast)}")
    print(ast.eval())
