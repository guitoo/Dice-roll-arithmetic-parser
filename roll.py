#!/usr/bin/env python

import sys
import operator
from random import randint
from sly import Lexer, Parser
from typing import List

symbol = {
    operator.add: "+",
    operator.sub: "-",
    operator.mul: "x",
    operator.truediv: "/",
}


class ExpressionBinOp:
    def __init__(self, left, op, right):
        self.left = left
        self.right = right
        self.op = op

    def eval(self):
        return self.op(self.left.eval(), self.right.eval())

    def soft_eval(self):
        return ExpressionBinOp(self.left.soft_eval(), self.op, self.right.soft_eval())

    def __str__(self):
        if self.op in [operator.mul, operator.truediv]:
            return f"{str(self.left)}{symbol[self.op]}{str(self.right)}"
        return f"({str(self.left)} {symbol[self.op]} {str(self.right)})"


class ExpressionNeg:
    def __init__(self, right):
        self.right = right

    def eval(self):
        return operator.neg(self.right.eval())

    def soft_eval(self):
        return ExpressionNeg(self.right.soft_eval())

    def __str__(self):
        return "(-" + str(self.right) + ")"


class ExpressionAdd(ExpressionBinOp):
    def __init__(self, left, right):
        super().__init__(left, operator.add, right)


class ExpressionSub(ExpressionBinOp):
    def __init__(self, left, right):
        super().__init__(left, operator.sub, right)


class ExpressionMul(ExpressionBinOp):
    def __init__(self, left, right):
        super().__init__(left, operator.mul, right)


class ExpressionDiv(ExpressionBinOp):
    def __init__(self, left, right):
        super().__init__(left, operator.truediv, right)


class ExpressionDice:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def eval(self):
        sum = 0
        for i in range(self.left.eval()):
            sum += randint(1, self.right.eval())
        return sum

    def soft_eval(self):
        # if self.left.eval() == 1:
        #     return ExpressionNum(randint(1,self.right.eval()))

        # expressions = []
        # for i in range(self.left.eval()):
        #     expressions.append(ExpressionNum(randint(1,self.right.eval())))
        # return ExpressionSum(expressions)

        rolls = []
        for i in range(self.left.eval()):
            rolls.append(randint(1, self.right.eval()))
        return ExpressionEvaluatedRoll(self, rolls)

    def __str__(self):
        return str(self.left) + "d" + str(self.right)


class ExpressionEvaluatedRoll:
    def __init__(self, dice: ExpressionDice, rolls: List[float]):
        self.dice = dice
        self.rolls = rolls

    def eval(self):
        return sum(self.rolls)

    def soft_eval(self):
        return self

    def __str__(self):
        if len(self.rolls) == 1:
            return f"{self.dice.left}d{self.dice.right}:{self.rolls[0]}"
        return f"{self.dice.left}d{self.dice.right}:({', '.join(str(roll) for roll in self.rolls)})"
        # return f"({', '.join(str(roll) for roll in self.rolls)})"


class ExpressionNum:
    def __init__(self, num):
        self.num = num

    def eval(self):
        return self.num

    def soft_eval(self):
        return self

    def __str__(self):
        return str(self.num)


class ExpressionList(list):
    def eval(self):
        return [item.eval() for item in self]

    def soft_eval(self):
        return ExpressionList([item.soft_eval() for item in self])

    def __str__(self):
        strings = [
            str(item)[1:-1]
            if isinstance(item, ExpressionSum)
            else str(item)
            for item in self
        ]
        return "[" + ", ".join(strings) + "]"


class ExpressionSum(list):
    def eval(self):
        return sum(item.eval() for item in self)

    def soft_eval(self):
        return ExpressionSum([item.soft_eval() for item in self])

    def __str__(self):
        if isinstance(self[0], ExpressionNeg):
            str_list = [f"-{self[0].right}"]
        else:
            str_list = [str(self[0])]
        for expr in self[1:]:
            if isinstance(expr, ExpressionNeg):
                str_list.append(f" - {expr.right}")
            else:
                str_list.append(f" + {expr}")
        return "(" + "".join(str_list) + ")"


class ExpressionRoot:
    def __init__(self, expr):
        self.expr = expr

    def eval(self):
        return self.expr.eval()

    def soft_eval(self):
        return ExpressionRoot(self.expr.soft_eval())

    def __str__(self):
        if isinstance(self.expr, ExpressionSum):
            return str(self.expr)[1:-1]
        return str(self.expr)


class RollLexer(Lexer):
    tokens = {INTEGER, MUL}
    ignore = " \t"
    literals = {"+", "-", "/", "(", ")", "d", ","}

    MUL = r"\*|x"

    @_(r"\d+")
    def INTEGER(self, t):
        t.value = int(t.value)
        return t

    def error(self, t):
        print("Illegal character '%s'" % t.value[0])
        self.index += 1


class RollParser(Parser):
    tokens = RollLexer.tokens
    # debugfile = 'parser.out'

    precedence = (
        ("left", ","),
        ("left", "-"),
        ("left", "+"),
        ("left", "MUL", "/"),
        ("left", "d"),
        ("right", "UMINUS"),
    )

    def __init__(self):
        pass

    @_("list_")
    def statement(self, p):
        return ExpressionRoot(p.list_)

    @_("expr")
    def statement(self, p):
        return ExpressionRoot(p.expr)

    @_("term")
    def expr(self, p):
        return p.term

    @_("sum_")
    def expr(self, p):
        return p.sum_

    @_('term "+" term')
    def sum_(self, p):
        return ExpressionSum([p.term0, p.term1])

    @_('sum_ "+" term')
    def sum_(self, p):
        list_ = p.sum_
        list_.append(p.term)
        return list_

    @_('term "-" term')
    def sum_(self, p):
        return ExpressionSum([p.term0, ExpressionNeg(p.term1)])

    @_('sum_ "-" term')
    def sum_(self, p):
        list_ = p.sum_
        list_.append(ExpressionNeg(p.term))
        return list_

    @_("term MUL term")
    def term(self, p):
        return ExpressionMul(p.term0, p.term1)

    @_('term "/" term')
    def term(self, p):
        return ExpressionDiv(p.term0, p.term1)

    @_('"-" term %prec UMINUS')
    def term(self, p):
        return ExpressionNeg(p.term)

    @_('"(" expr ")"')
    def term(self, p):
        return p.expr

    @_("INTEGER")
    def term(self, p):
        return ExpressionNum(p.INTEGER)

    @_('INTEGER "d" INTEGER')
    def term(self, p):
        return ExpressionDice(ExpressionNum(p.INTEGER0), ExpressionNum(p.INTEGER1))

    @_('"d" INTEGER')
    def term(self, p):
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
    soft_eval = ast.soft_eval()
    print(f"rolls: {str(soft_eval)}")
    print(soft_eval.eval())
