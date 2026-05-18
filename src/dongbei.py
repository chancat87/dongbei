#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""dongbei语言执行器 {version}

用法：
    dongbei.py [--xudao] 源程序文件名...
    dongbei.py [--xudao] --bihua dongbei案例名...

要是命令行包含 --xudao（絮叨），在执行前先打印对应的 Python 代码。
"""

import io
import os
import re
import sys  # needed by 最高指示
import time  # needed by 打个盹

import lark
from lark.lexer import Lexer as _LarkLexer

from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_boolean("xudao", False, "絮叨: 在执行前先打印对应的 Python 代码。")
flags.DEFINE_boolean("bihua", False, "比划: 直接执行dongbei宝典案例。")

DONGBEI_VERSION = "0.0.16"

EXAMPLE_GROUP_SIZE = 5

KW_APPEND = "来了个"
KW_ASSERT = "保准"
KW_ASSERT_FALSE = "辟谣"
KW_BANG = "！"
KW_BANG_NARROW = "!"
KW_BASE_INIT = "领导的新对象"
KW_BECOME = "装"
KW_BEGIN = "开整："
KW_BREAK = "尥蹶子"
KW_CALL = "整"
KW_CHECK = "寻思："
KW_CLASS = "阶级"
KW_CLOSE_BRACKET = "」"
KW_CLOSE_PAREN = "）"
KW_CLOSE_PAREN_NARROW = ")"
KW_CLOSE_QUOTE = "”"
KW_COLON = "："
KW_COLON_NARROW = ":"
KW_COMMA = "，"
KW_COMMA_NARROW = ","
KW_COMPARE = "比"
KW_COMPARE_WITH = "跟"
KW_CONCAT = "、"
KW_CONTINUE = "接着磨叽"
KW_DEC = "稍稍"
KW_DEC_BY = "稍"
KW_DEL = "炮决"
KW_DOT = "的"
KW_SET_NONE = "削"
KW_DERIVED = "的接班银"
KW_DIVIDE_BY = "除以"
KW_ELSE = "要不行咧就"
KW_END = "整完了"
KW_END_LOOP = "磨叽完了"
KW_EQUAL = "一样一样的"
KW_EXTEND = "来了群"
KW_FROM = "从"
KW_DEF = "咋整："
KW_GREATER = "还大"
KW_IMPORT = "翠花，上"
KW_IN = "在"
KW_INC = "走走"
KW_INC_BY = "走"
KW_INDEX_1 = "的老大"
KW_INDEX_LAST = "的老幺"
KW_INDEX = "的老"
KW_1_INFINITE_LOOP = "从一而终磨叽："
KW_1_INFINITE_LOOP_EGG = "在苹果总部磨叽："  # 彩蛋
KW_INTEGER_DIVIDE_BY = "齐整整地除以"
KW_IS_LIST = "都是活雷锋"
KW_IS_NONE = "啥也不是"
KW_IS_VAR = "是活雷锋"
KW_LENGTH = "有几个坑"
KW_LESS = "还小"
KW_LOOP = "磨叽："
KW_MINUS = "减"
KW_MODULO = "刨掉一堆堆"
KW_NEGATE = "拉饥荒"
KW_NEW_OBJECT_OF = "的新对象"
KW_NOT_EQUAL = "不是一样一样的"
KW_OPEN_BRACKET = "「"
KW_OPEN_BRACKET_VERBOSE = "路银「"
KW_OPEN_PAREN = "（"
KW_OPEN_PAREN_NARROW = "("
KW_OPEN_QUOTE = "“"
KW_PERIOD = "。"
KW_PLUS = "加"
KW_RAISE = "整叉劈了："
KW_REMOVE_HEAD = "掐头"
KW_REMOVE_TAIL = "去尾"
KW_RETURN = "滚犊子吧"
KW_SAY = "唠唠"
KW_SAY_DIGU = "嘀咕"
KW_STEP = "步"
KW_STEP_LOOP = "蹿磨叽："
KW_THEN = "？要行咧就"
KW_TIMES = "乘"
KW_TUPLE = "抱团"
KW_TO = "到"
KW_YIELD = "出溜"

KEYWORDS = (
    KW_APPEND,
    KW_ASSERT,
    KW_ASSERT_FALSE,
    KW_BANG,
    KW_BANG_NARROW,
    KW_BASE_INIT,
    KW_BECOME,
    KW_BEGIN,
    KW_BREAK,
    KW_CHECK,
    KW_CLASS,
    KW_CLOSE_BRACKET,
    KW_CLOSE_PAREN,
    KW_CLOSE_PAREN_NARROW,
    KW_CLOSE_QUOTE,
    KW_COLON,
    KW_COLON_NARROW,
    KW_COMMA,
    KW_COMMA_NARROW,
    KW_COMPARE,
    KW_COMPARE_WITH,
    KW_CONCAT,
    KW_CONTINUE,
    KW_DEC,
    KW_DEC_BY,
    KW_DEL,
    KW_DERIVED,
    KW_SET_NONE,
    KW_DIVIDE_BY,
    KW_ELSE,
    KW_EXTEND,
    KW_END,  # must match 整完了 before matching 整
    KW_RAISE,  # must match 整叉劈了 before matching 整
    KW_CALL,  # 整
    KW_END_LOOP,
    KW_EQUAL,
    KW_1_INFINITE_LOOP,  # must match 从一而终磨叽 before 从
    KW_FROM,
    KW_DEF,
    KW_GREATER,
    KW_IMPORT,
    KW_1_INFINITE_LOOP_EGG,  # must match 在苹果总部磨叽 before 在
    KW_IN,
    KW_INC,
    KW_INC_BY,
    KW_INDEX_1,  # must match 的老大 before 的老
    KW_INDEX_LAST,  # must match 的老幺 before 的老
    KW_INDEX,  # must match 的老 before 的
    KW_NEW_OBJECT_OF,  # must match 的新对象 before 的
    KW_DOT,
    KW_INTEGER_DIVIDE_BY,
    KW_IS_LIST,
    KW_IS_NONE,
    KW_IS_VAR,
    KW_LENGTH,
    KW_LESS,
    KW_LOOP,
    KW_MINUS,
    KW_MODULO,
    KW_NEGATE,
    KW_NOT_EQUAL,
    KW_OPEN_BRACKET,
    KW_OPEN_BRACKET_VERBOSE,
    KW_OPEN_PAREN,
    KW_OPEN_PAREN_NARROW,
    KW_OPEN_QUOTE,
    KW_PERIOD,
    KW_PLUS,
    KW_REMOVE_HEAD,
    KW_REMOVE_TAIL,
    KW_RETURN,
    KW_SAY,
    KW_SAY_DIGU,
    KW_STEP,
    KW_STEP_LOOP,
    KW_THEN,
    KW_TIMES,
    KW_TUPLE,
    KW_TO,
    KW_YIELD,
)

# Maps a keyword to its normalized form.
KEYWORD_TO_NORMALIZED_KEYWORD = {
    KW_BANG: KW_PERIOD,
    KW_BANG_NARROW: KW_PERIOD,
    KW_OPEN_PAREN_NARROW: KW_OPEN_PAREN,
    KW_CLOSE_PAREN_NARROW: KW_CLOSE_PAREN,
    KW_COLON_NARROW: KW_COLON,
    KW_COMMA_NARROW: KW_COMMA,
    KW_OPEN_BRACKET_VERBOSE: KW_OPEN_BRACKET,
    KW_SAY: KW_SAY_DIGU,
}

# Maps a normalized keyword value to its Lark terminal name (underscore-prefixed = discarded).
_KW_VALUE_TO_TERMINAL = {
    KW_APPEND: "_KW_APPEND",
    KW_ASSERT: "_KW_ASSERT",
    KW_ASSERT_FALSE: "_KW_ASSERT_FALSE",
    KW_BASE_INIT: "_KW_BASE_INIT",
    KW_BECOME: "_KW_BECOME",
    KW_BEGIN: "_KW_BEGIN",
    KW_BREAK: "_KW_BREAK",
    KW_CALL: "_KW_CALL",
    KW_CHECK: "_KW_CHECK",
    KW_CLASS: "_KW_CLASS",
    KW_CLOSE_BRACKET: "_KW_CLOSE_BRACKET",
    KW_CLOSE_PAREN: "_KW_CLOSE_PAREN",
    KW_CLOSE_QUOTE: "_KW_CLOSE_QUOTE",
    KW_COLON: "_KW_COLON",
    KW_COMMA: "_KW_COMMA",
    KW_COMPARE: "_KW_COMPARE",
    KW_COMPARE_WITH: "_KW_COMPARE_WITH",
    KW_CONCAT: "_KW_CONCAT",
    KW_CONTINUE: "_KW_CONTINUE",
    KW_DEC: "KW_DEC",
    KW_DEC_BY: "_KW_DEC_BY",
    KW_DEL: "_KW_DEL",
    KW_DERIVED: "_KW_DERIVED",
    KW_DIVIDE_BY: "KW_DIVIDE_BY",
    KW_ELSE: "_KW_ELSE",
    KW_END: "_KW_END",
    KW_END_LOOP: "_KW_END_LOOP",
    KW_EQUAL: "KW_EQUAL",
    KW_EXTEND: "_KW_EXTEND",
    KW_FROM: "_KW_FROM",
    KW_DEF: "_KW_DEF",
    KW_GREATER: "KW_GREATER",
    KW_IMPORT: "_KW_IMPORT",
    KW_IN: "_KW_IN",
    KW_INC: "KW_INC",
    KW_INC_BY: "_KW_INC_BY",
    KW_INDEX: "_KW_INDEX",
    KW_INDEX_1: "KW_INDEX_1",
    KW_INDEX_LAST: "KW_INDEX_LAST",
    KW_1_INFINITE_LOOP: "_KW_1_INFINITE_LOOP",
    KW_1_INFINITE_LOOP_EGG: "_KW_1_INFINITE_LOOP_EGG",
    KW_INTEGER_DIVIDE_BY: "KW_INTEGER_DIVIDE_BY",
    KW_IS_LIST: "_KW_IS_LIST",
    KW_IS_NONE: "KW_IS_NONE",
    KW_IS_VAR: "_KW_IS_VAR",
    KW_LENGTH: "_KW_LENGTH",
    KW_LESS: "KW_LESS",
    KW_LOOP: "_KW_LOOP",
    KW_MINUS: "KW_MINUS",
    KW_MODULO: "KW_MODULO",
    KW_NEGATE: "_KW_NEGATE",
    KW_NEW_OBJECT_OF: "_KW_NEW_OBJECT_OF",
    KW_NOT_EQUAL: "KW_NOT_EQUAL",
    KW_OPEN_BRACKET: "_KW_OPEN_BRACKET",
    KW_OPEN_PAREN: "_KW_OPEN_PAREN",
    KW_OPEN_QUOTE: "_KW_OPEN_QUOTE",
    KW_PERIOD: "_KW_PERIOD",
    KW_PLUS: "KW_PLUS",
    KW_RAISE: "_KW_RAISE",
    KW_REMOVE_HEAD: "_KW_REMOVE_HEAD",
    KW_REMOVE_TAIL: "_KW_REMOVE_TAIL",
    KW_RETURN: "_KW_RETURN",
    KW_SAY_DIGU: "_KW_SAY_DIGU",
    KW_SET_NONE: "_KW_SET_NONE",
    KW_STEP: "_KW_STEP",
    KW_STEP_LOOP: "_KW_STEP_LOOP",
    KW_THEN: "_KW_THEN",
    KW_TIMES: "KW_TIMES",
    KW_TUPLE: "_KW_TUPLE",
    KW_TO: "_KW_TO",
    KW_YIELD: "_KW_YIELD",
    KW_DOT: "_KW_DOT",
}

# Types of tokens.
TK_KEYWORD = "KEYWORD"
TK_IDENTIFIER = "IDENTIFIER"
TK_STRING_LITERAL = "STRING"
TK_NON_TERMINATING_STRING_LITERAL = "NON_TERMINATING_STRING"
TK_NUMBER_LITERAL = "NUMBER"
TK_NONE_LITERAL = "NONE"
TK_CHAR = "CHAR"

# Statements.
STMT_APPEND = "APPEND"
STMT_ASSERT = "ASSERT"
STMT_ASSERT_FALSE = "ASSERT_FALSE"
STMT_ASSIGN = "ASSIGN"
STMT_BREAK = "BREAK"
STMT_CALL = "CALL"
STMT_CLASS_DEF = "CLASS"
STMT_COMPOUND = "COMPOUND"
STMT_CONDITIONAL = "CONDITIONAL"
STMT_CONTINUE = "CONTINUE"
STMT_DEC_BY = "DEC_BY"
STMT_DEL = "DEL"
STMT_SET_NONE = "SET_NONE"
STMT_EXPR = "EXPR"  # an expression statement
STMT_EXTEND = "EXTEND"
STMT_FUNC_DEF = "FUNC_DEF"
STMT_IMPORT = "IMPORT"
STMT_INC_BY = "INC_BY"
STMT_INFINITE_LOOP = "INFINITE_LOOP"
STMT_LIST_VAR_DECL = "LIST_VAR_DECL"
STMT_LOOP = "LOOP"
STMT_RAISE = "RAISE"
STMT_RANGE_LOOP = "RANGE_LOOP"
STMT_RETURN = "RETURN"
STMT_SAY = "SAY"
STMT_VAR_DECL = "VAR_DECL"
STMT_YIELD = "YIELD"


class _Dongbei_Error(Exception):
    """An error in a dongbei program."""

    def __init__(self, message):
        self.message = message


class SourceLoc:
    """A source file location."""

    def __init__(self, filepath="<unknown>", line=1, column=0):
        self.filepath = filepath
        self.line = line
        self.column = column

    def advance(self, string):
        """Moves the location forward by skipping the given string."""

        for char in string:
            if char == "\n":
                self.line += 1
                self.column = 0
            else:
                self.column += 1

    def clone(self):
        return SourceLoc(self.filepath, self.line, self.column)

    def __str__(self):
        return f"{self.filepath}:{self.line}:{self.column}"

    def __eq__(self, other):
        return (
            isinstance(other, SourceLoc)
            and self.filepath == other.filepath
            and self.line == other.line
            and self.column == other.column
        )

    def __ne__(self, other):
        return not self.__eq__(other)


class SourceCodeAndLoc:
    """Source code and its source file location."""

    def __init__(self, code, loc):
        self.code = code or ""
        if loc:
            self.loc = loc.clone()
        else:
            self.loc = SourceLoc()

    def clone(self):
        return SourceCodeAndLoc(self.code, self.loc.clone())

    def skip_char(self):
        assert self.code
        self.loc.advance(self.code[0])
        self.code = self.code[1:]

    def skip_chars(self, num):
        for x in range(num):
            self.skip_char()


class Token:
    def __init__(self, kind, value, loc):
        self.kind = kind
        self.value = value
        if loc:
            self.loc = loc.clone()  # a SourceLoc
        else:
            self.loc = SourceLoc()

    def __str__(self):
        return f"{self.kind} <{repr(self.value)}> @ {self.loc}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        # We don't compare loc as it's not intrinsic.
        return (
            isinstance(other, Token)
            and self.kind == other.kind
            and self.value == other.value
        )

    def __ne__(self, other):
        return not (self == other)


def identifier_token(name, loc):
    return Token(TK_IDENTIFIER, name, loc)


class Expr:
    def __init__(self):
        pass

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        # Strict type check: a subclass expr is not equal to its parent even if fields match.
        return type(self) == type(other) and self.equals(other)

    def equals(self, other):
        """Returns true if self and other (which is guaranteed to have the same type) are equal."""
        raise Exception("%s 这货没整 equals()，这不行啊！" % (type(self),))

    def __ne__(self, other):
        return not (self == other)

    def to_dongbei(self):
        """Returns the dongbei code for this expression."""
        raise Exception(f"{type(self)} 这货没整 to_dongbei()，咋跟它唠嗑啊！")

    def to_python(self):
        """Translates this expression to Python."""
        raise Exception("%s 这货没整 to_python()，程序没法跑！" % (type(self),))


def _dongbei_repr(value):
    """Converts a value to its dongbei repr."""
    if value is None:
        return KW_IS_NONE
    if type(value) == bool:
        return ID_TRUE if value else ID_FALSE
    if type(value) == list:
        return "「" + ", ".join(map(_dongbei_repr, value)) + "」"
    if type(value) == tuple:
        return f"（%s{KW_TUPLE}）" % (
            KW_COMPARE_WITH.join(_dongbei_repr(field) for field in value),
        )
    return repr(value)


def _dongbei_str(value):
    """Converts a value to its dongbei string."""
    if type(value) == str:
        return value
    return _dongbei_repr(value)


class ConcatExpr(Expr):
    def __init__(self, exprs):
        self.exprs = exprs

    def __str__(self):
        return "CONCAT_EXPR<%s>" % (self.exprs,)

    def equals(self, other):
        return self.exprs == other.exprs

    def to_dongbei(self):
        return KW_CONCAT.join(expr.to_dongbei() for expr in self.exprs)

    def to_python(self):
        return " + ".join(
            "_dongbei_str(%s)" % (expr.to_python(),) for expr in self.exprs
        )


class LengthExpr(Expr):
    def __init__(self, expr):
        self.expr = expr

    def __str__(self):
        return f"LENGTH<{self.expr}>"

    def equals(self, other):
        return self.expr == other.expr

    def to_dongbei(self):
        return f"{self.expr.to_dongbei()}{KW_LENGTH}"

    def to_python(self):
        return f"len({self.expr.to_python()})"


class NegateExpr(Expr):
    def __init__(self, expr):
        self.expr = expr

    def __str__(self):
        return f"NEGATE<{self.expr}>"

    def equals(self, other):
        return self.expr == other.expr

    def to_dongbei(self):
        code = self.expr.to_dongbei()
        return f"{KW_NEGATE} {code}"

    def to_python(self):
        code = self.expr.to_python()
        return f"-({code})"


class SubListExpr(Expr):
    def __init__(self, list_expr, remove_at_head, remove_at_tail):
        self.list = list_expr
        self.remove_at_head = remove_at_head
        self.remove_at_tail = remove_at_tail

    def __str__(self):
        return f"SUBLIST<{self.list}, {self.remove_at_head}, {self.remove_at_tail}>"

    def equals(self, other):
        return (
            self.list == other.list
            and self.remove_at_head == other.remove_at_head
            and self.remove_at_tail == other.remove_at_tail
        )

    def to_dongbei(self):
        code = self.list.to_dongbei()
        if self.remove_at_head:
            code += KW_REMOVE_HEAD
        if self.remove_at_tail:
            code += KW_REMOVE_TAIL
        return code

    def to_python(self):
        start_index = 1 if self.remove_at_head else 0
        end_index = -1 if self.remove_at_tail else None
        return f"({self.list.to_python()})[{start_index} : {end_index}]"


class IndexExpr(Expr):
    def __init__(self, list_expr, index_expr):
        self.list_expr = list_expr
        self.index_expr = index_expr

    def __str__(self):
        return f"INDEX_EXPR<{self.list_expr}, {self.index_expr}>"

    def equals(self, other):
        return self.list_expr == other.list_expr and self.index_expr == other.index_expr

    def to_dongbei(self):
        list_expr = self.list_expr.to_dongbei()
        index_expr = self.index_expr.to_dongbei()
        return f"{list_expr}{KW_INDEX}{index_expr}"

    def to_python(self):
        return f"({self.list_expr.to_python()})[({self.index_expr.to_python()}) - 1]"


class ObjectPropertyExpr(Expr):
    def __init__(self, object, property):
        self.object = object
        self.property = property

    def __str__(self):
        return f"PROPERTY_EXPR<{self.object}, {self.property}>"

    def equals(self, other):
        return self.object == other.object and self.property == other.property

    def to_dongbei(self):
        obj = self.object.to_dongbei()
        prop = f"【{self.property.value}】"
        return f"{obj}{KW_DOT}{prop}"

    def to_python(self):
        obj = self.object.to_python()
        prop = get_python_var_name(self.property.value)
        return f"({obj}).{prop}"


class MethodCallExpr(Expr):
    def __init__(self, object, call_expr):
        self.object = object
        self.call_expr = call_expr

    def __str__(self):
        return f"METHOD_CALL_EXPR<{self.object}, {self.call_expr}>"

    def equals(self, other):
        return self.object == other.object and self.call_expr == other.call_expr

    def to_dongbei(self):
        obj = self.object.to_dongbei()
        call = self.call_expr.to_dongbei()
        return obj + call

    def to_python(self):
        obj = self.object.to_python()
        call = self.call_expr.to_python()
        return f"({obj}).{call}"


def _dongbei_add(a, b):
    """dongbei专用的加法函数，能自动处理字符串和数字的拼接"""
    if isinstance(a, str) or isinstance(b, str):
        return str(a) + str(b)
    return a + b


ARITHMETIC_OPERATION_TO_PYTHON = {
    KW_MINUS: "-",
    KW_TIMES: "*",
    KW_DIVIDE_BY: "/",
    KW_INTEGER_DIVIDE_BY: "//",
    KW_MODULO: "%",
}


class ArithmeticExpr(Expr):
    def __init__(self, op1, operation, op2):
        self.op1 = op1
        self.operation = operation
        self.op2 = op2

    def __str__(self):
        return "ARITHMETIC_EXPR<%s, %s, %s>" % (self.op1, self.operation, self.op2)

    def equals(self, other):
        return (
            self.op1 == other.op1
            and self.operation == other.operation
            and self.op2 == other.op2
        )

    def to_dongbei(self):
        return f"{self.op1.to_dongbei()}{self.operation.value}{self.op2.to_dongbei()}"

    def to_python(self):
        if self.operation.value == KW_PLUS:
            # 对于加法，使用我们自定义的_dongbei_add函数
            return "_dongbei_add(%s, %s)" % (self.op1.to_python(), self.op2.to_python())
        else:
            # 其他运算保持原样
            return "%s %s %s" % (
                self.op1.to_python(),
                ARITHMETIC_OPERATION_TO_PYTHON[self.operation.value],
                self.op2.to_python(),
            )


class LiteralExpr(Expr):
    def __init__(self, token):
        self.token = token

    def __str__(self):
        return "LITERAL_EXPR<%s>" % (self.token,)

    def equals(self, other):
        return self.token == other.token

    def to_dongbei(self):
        if self.token.kind == TK_NUMBER_LITERAL:
            return str(self.token.value)
        if self.token.kind == TK_STRING_LITERAL:
            return "“%s”" % (self.token.value,)
        if self.token.kind == TK_NONE_LITERAL:
            return KW_IS_NONE
        raise Exception("见鬼了，不认识这 token：%s" % (self.token.kind,))

    def to_python(self):
        if self.token.kind == TK_NUMBER_LITERAL:
            return str(self.token.value)
        if self.token.kind == TK_STRING_LITERAL:
            return '"%s"' % (self.token.value,)
        if self.token.kind == TK_NONE_LITERAL:
            return "None"
        raise Exception("见鬼了，不认识这 token：%s" % (self.token.kind,))


class TupleExpr(Expr):
    def __init__(self, tuple):
        self.tuple = tuple

    def __str__(self):
        return "TUPLE_EXPR<%s>" % (self.tuple,)

    def equals(self, other):
        return self.tuple == other.tuple

    def to_dongbei(self):
        if not self.tuple:
            return KW_TUPLE

        return (
            KW_COMPARE_WITH.join(field.to_dongbei() for field in self.tuple) + KW_TUPLE
        )

    def to_python(self):
        if len(self.tuple) == 1:
            return f"({self.tuple[0].to_python()},)"

        return "(%s)" % (", ".join(field.to_python() for field in self.tuple))


def number_literal_expr(value, loc):
    return LiteralExpr(Token(TK_NUMBER_LITERAL, value, loc))


class VariableExpr(Expr):
    def __init__(self, var):
        self.var = var

    def __str__(self):
        return "VARIABLE_EXPR<%s>" % (self.var,)

    def equals(self, other):
        return self.var == other.var

    def to_dongbei(self):
        return f"【{self.var}】"

    def to_python(self):
        return get_python_var_name(self.var)


class ParenExpr(Expr):
    def __init__(self, expr):
        self.expr = expr

    def __str__(self):
        return "PAREN_EXPR<%s>" % (self.expr,)

    def equals(self, other):
        return self.expr == other.expr

    def to_dongbei(self):
        return f"（{self.expr.to_dongbei()}）"

    def to_python(self):
        return "(%s)" % (self.expr.to_python(),)


class CallExpr(Expr):
    def __init__(self, func, args):
        self.func = func
        self.args = args

    def __str__(self):
        return "CALL_EXPR<%s>(%s)" % (
            self.func,
            ", ".join(str(arg) for arg in self.args),
        )

    def equals(self, other):
        return self.func == other.func and self.args == other.args

    def to_dongbei(self):
        code = f"{KW_CALL}{self.func}"
        if self.args:
            code += "（" + "，".join(arg.to_dongbei() for arg in self.args) + "）"
        return code

    def to_python(self):
        return "%s(%s)" % (
            get_python_var_name(self.func),
            ", ".join(arg.to_python() for arg in self.args),
        )


class NewObjectExpr(Expr):
    def __init__(self, class_id, args):
        self.class_id = class_id
        self.args = args

    def __str__(self):
        return "NEW_OBJECT_EXPR<%s>(%s)" % (
            self.class_id,
            ", ".join(str(arg) for arg in self.args),
        )

    def equals(self, other):
        return self.class_id == other.class_id and self.args == other.args

    def to_dongbei(self):
        code = f"{self.class_id.value}{KW_NEW_OBJECT_OF}"
        if self.args:
            code += "（" + "，".join(arg.to_dongbei() for arg in self.args) + "）"
        return code

    def to_python(self):
        return "%s(%s)" % (
            get_python_var_name(self.class_id.value),
            ", ".join(arg.to_python() for arg in self.args),
        )


class ListExpr(Expr):
    def __init__(self, exprs):
        self.exprs = exprs

    def __str__(self):
        return "LIST(%s)" % (", ".join(str(expr) for expr in self.exprs))

    def equals(self, other):
        return self.exprs == other.exprs

    def to_dongbei(self):
        return (
            KW_OPEN_BRACKET
            + "，".join(expr.to_dongbei() for expr in self.exprs)
            + KW_CLOSE_BRACKET
        )

    def to_python(self):
        return "[%s]" % (", ".join(expr.to_python() for expr in self.exprs))


# Maps a dongbei comparison keyword to the Python version.
COMPARISON_KEYWORD_TO_PYTHON = {
    KW_GREATER: ">",
    KW_LESS: "<",
    KW_EQUAL: "==",
    KW_NOT_EQUAL: "!=",
}


class ComparisonExpr(Expr):
    def __init__(self, op1, relation, op2):
        self.op1 = op1
        self.relation = relation
        self.op2 = op2

    def __str__(self):
        return "COMPARISON_EXPR(%s, %s, %s)" % (self.op1, self.relation, self.op2)

    def equals(self, other):
        return (
            self.op1 == other.op1
            and self.relation == other.relation
            and self.op2 == other.op2
        )

    def to_dongbei(self):
        code = self.op1.to_dongbei()
        if self.relation.value == KW_IS_NONE:
            return code + KW_IS_NONE
        if self.relation.value in (KW_GREATER, KW_LESS):
            connector = KW_COMPARE
        else:
            connector = KW_COMPARE_WITH
        return code + connector + self.op2.to_dongbei() + self.relation.value

    def to_python(self):
        if self.relation.value == KW_IS_NONE:
            return f"({self.op1.to_python()}) is None"
        return "%s %s %s" % (
            self.op1.to_python(),
            COMPARISON_KEYWORD_TO_PYTHON[self.relation.value],
            self.op2.to_python(),
        )


class Statement:
    def __init__(self, kind, value):
        self.kind = kind
        self.value = value

    def __str__(self):
        value_str = str(self.value)
        return "%s <%s>" % (self.kind, value_str)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return (
            isinstance(other, Statement)
            and self.kind == other.kind
            and self.value == other.value
        )

    def __ne__(self, other):
        return not (self == other)


def keyword(str, loc):
    """Returns a keyword token whose value is the given string."""
    return Token(TK_KEYWORD, str, loc)


CHINESE_DIGITS = {
    "鸭蛋": 0,
    "零": 0,
    "一": 1,
    "二": 2,
    "俩": 2,
    "两": 2,
    "三": 3,
    "仨": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}


def try_parse_number(str):
    """Returns (number, remainder)."""

    m = re.match(r"^(-?[0-9]+(\.[0-9]*)?)(.*)", str)
    if m:
        number_str = m.group(1)
        remainder = m.group(3)
        if "." in number_str:
            return float(number_str), remainder
        return int(number_str), remainder
    for chinese_digit, value in CHINESE_DIGITS.items():
        if str.startswith(chinese_digit):
            return value, str[len(chinese_digit) :]
    return None, str


def tokenize_str_containing_no_keyword(chars, loc):
    """Returns a list of tokens."""
    tokens = []
    number, rest = try_parse_number(chars)
    if number is not None:
        tokens.append(Token(TK_NUMBER_LITERAL, number, loc))
        tokens.extend(tokenize_str_containing_no_keyword(rest, loc))
    elif rest:
        tokens.append(identifier_token(rest, loc))
    return tokens


class DongbeiParser(object):
    # TODO: split the code into lines to make skipping lines faster.
    def __init__(self):
        self.code_loc = SourceCodeAndLoc(None, None)

    @property
    def code(self):
        return self.code_loc.code

    @property
    def loc(self):
        return self.code_loc.loc

    def skip_char(self):
        self.code_loc.skip_char()

    def skip_chars(self, num):
        for x in range(num):
            self.skip_char()

    def skip_whitespace(self):
        """If the next char is a whitespace, skips it and returns True."""

        if self.code and self.code[0].isspace():
            self.skip_char()
            return True
        return False

    def skip_line(self):
        while self.code and self.code[0] != "\n":
            self.skip_char()
        if self.code and self.code[0] == "\n":
            self.skip_char()

    def skip_whitespace_and_comment(self):
        while True:
            old_loc = self.loc.clone()
            while self.skip_whitespace():
                pass
            if self.code.startswith("#"):  # comment
                self.skip_line()
            if self.loc == old_loc:  # cannot skip any further.
                return

    def tokenize_string_literal_and_rest(self):
        """Returns a list of tokens."""

        tokens = []
        loc = self.loc.clone()
        close_quote_pos = self.code.find(KW_CLOSE_QUOTE)
        if close_quote_pos < 0:
            tokens.append(Token(TK_NON_TERMINATING_STRING_LITERAL, self.code, loc))
            self.skip_chars(len(self.code))
            return tokens

        tokens.append(Token(TK_STRING_LITERAL, self.code[:close_quote_pos], loc))
        self.skip_chars(close_quote_pos)
        tokens.append(keyword(KW_CLOSE_QUOTE, self.loc))
        self.skip_chars(len(KW_CLOSE_QUOTE))
        tokens.extend(self.basic_tokenize())
        return tokens

    def try_parse_keyword(self, kw):
        """Returns (parsed keyword string, remaining code)."""
        orig_code_loc = self.code_loc.clone()
        for char in kw:
            self.skip_whitespace_and_comment()
            if not self.code.startswith(char):
                self.code_loc = orig_code_loc
                return None
            self.skip_char()
        return kw

    def basic_tokenize(self):
        """Returns a list of tokens from the dongbei code."""

        tokens = []
        while True:
            self.skip_whitespace_and_comment()
            if not self.code:
                return tokens

            # Parse 【标识符】.
            m = re.match("^(【(.*?)】)", self.code)
            if m:
                id = re.sub(r"\s+", "", m.group(2))  # Ignore whitespace.
                tokens.append(identifier_token(id, self.loc))
                self.skip_chars(len(m.group(1)))
                continue

            # Try to parse a keyword at the beginning of the code.
            matched_keyword = False
            for kw_str in KEYWORDS:
                kw_loc = self.loc.clone()
                kw = self.try_parse_keyword(kw_str)
                remaining_code = self.code_loc.clone()
                if kw:
                    kw_str = KEYWORD_TO_NORMALIZED_KEYWORD.get(kw_str, kw_str)
                    last_token = keyword(kw_str, kw_loc)
                    tokens.append(last_token)
                    if last_token.kind == TK_KEYWORD and last_token.value == KW_OPEN_QUOTE:
                        self.code_loc = remaining_code
                        tokens.extend(self.tokenize_string_literal_and_rest())
                    else:
                        self.code_loc = remaining_code
                        self.skip_whitespace()
                    matched_keyword = True
                    break

            if matched_keyword:
                continue

            tokens.append(Token(TK_CHAR, self.code[0], self.loc))
            self.skip_char()

    def tokenize(self, code, src_file):
        self.code_loc.code = code
        self.code_loc.loc = SourceLoc(filepath=src_file if src_file is not None else "<unknown>")
        return self._tokenize()

    def _tokenize(self):
        """Tokenizes self.code into tokens."""
        tokens = []
        last_token = Token(None, None, None)
        loc = self.loc.clone()
        chars = ""
        for token in self.basic_tokenize():
            last_last_token = last_token
            last_token = token
            if token.kind == TK_CHAR:
                if last_last_token.kind == TK_CHAR:
                    chars += token.value
                    continue
                else:
                    chars = token.value
                    loc = token.loc.clone()  # first char of a new run: snapshot its position
                    continue
            else:
                if last_last_token.kind == TK_CHAR:
                    # A sequence of consecutive TK_CHARs ended.
                    tokens.extend(tokenize_str_containing_no_keyword(chars, loc))
                tokens.append(token)
                chars = ""
        tokens.extend(tokenize_str_containing_no_keyword(chars, loc))
        return tokens

    def translate_tokens_to_statements(self, tokens):
        tree = _lark_parser.parse(tokens, start="start")
        return _lark_transformer.transform(tree)



# ── Lark-based parser (replaces hand-written recursive-descent) ──────────────

_DONGBEI_GRAMMAR = r"""
// Terminal naming convention:
//   _KW_*          underscore-prefixed → auto-discarded from Transformer items (structural punctuation).
//   KW_*           no underscore → kept in Transformer items so the method can extract .loc from the token.
//                  Only operator/relation keywords that need a real SourceLoc use this form.
//   IDENTIFIER / NUMBER_LITERAL / STRING_LITERAL  carry the original dongbei Token as .value.

start:      stmt*
start_expr: expr
start_stmt: stmt

// =================== Statements ===================
// Dangling-else resolved via matched/open split (standard unambiguous grammar).
// open_stmt: the outermost if has no matching else.
// matched_stmt: all ifs have paired elses (or no ifs present).

?stmt: open_stmt | matched_stmt

?open_stmt: _KW_CHECK expr _KW_THEN stmt                                             -> if_stmt
          | _KW_CHECK expr _KW_THEN matched_stmt _KW_ELSE open_stmt                  -> if_else_stmt

?matched_stmt: _KW_CHECK expr _KW_THEN matched_stmt _KW_ELSE matched_stmt            -> if_else_stmt
             | non_if_stmt

?non_if_stmt: _KW_IMPORT IDENTIFIER _KW_PERIOD                                       -> import_stmt
    | _KW_BEGIN stmt* _KW_END _KW_PERIOD                                              -> compound_stmt
    | _KW_ASSERT expr _KW_PERIOD                                                      -> assert_stmt
    | _KW_ASSERT_FALSE expr _KW_PERIOD                                                -> assert_false_stmt
    | _KW_RAISE expr _KW_PERIOD                                                       -> raise_stmt
    | _KW_SET_NONE expr _KW_PERIOD                                                    -> set_none_stmt
    | _KW_DEL expr _KW_PERIOD                                                         -> del_stmt
    | _KW_SAY_DIGU _KW_COLON expr _KW_PERIOD                                         -> say_stmt
    | _KW_RETURN expr _KW_PERIOD                                                      -> return_stmt
    | _KW_CONTINUE _KW_PERIOD                                                         -> continue_stmt
    | _KW_BREAK _KW_PERIOD                                                            -> break_stmt
    | func_def
    | IDENTIFIER _KW_IS_VAR _KW_PERIOD                                               -> var_decl_stmt
    | IDENTIFIER _KW_IS_LIST _KW_PERIOD                                              -> list_decl_stmt
    | IDENTIFIER _KW_CLASS _KW_DERIVED IDENTIFIER _KW_CLASS _KW_DEF method_def* _KW_END _KW_PERIOD -> class_def_stmt
    | expr _KW_FROM expr _KW_TO expr _KW_LOOP stmt* _KW_END_LOOP _KW_PERIOD         -> loop_stmt
    | expr _KW_FROM expr _KW_TO expr step_spec stmt* _KW_END_LOOP _KW_PERIOD        -> step_loop_stmt
    | expr _KW_IN expr _KW_LOOP stmt* _KW_END_LOOP _KW_PERIOD                       -> range_loop_stmt
    | expr _KW_1_INFINITE_LOOP stmt* _KW_END_LOOP _KW_PERIOD                        -> infinite_loop_stmt
    | expr _KW_1_INFINITE_LOOP_EGG stmt* _KW_END_LOOP _KW_PERIOD                    -> infinite_loop_stmt
    | expr _KW_BECOME expr _KW_PERIOD                                                -> assign_stmt
    | expr _KW_APPEND expr _KW_PERIOD                                                -> append_stmt
    | expr _KW_EXTEND expr _KW_PERIOD                                                -> extend_stmt
    | expr _KW_YIELD _KW_PERIOD                                                      -> yield_stmt
    | expr KW_INC _KW_PERIOD                                                         -> inc_stmt
    | expr _KW_INC_BY expr _KW_STEP _KW_PERIOD                                      -> inc_by_stmt
    | expr KW_DEC _KW_PERIOD                                                         -> dec_stmt
    | expr _KW_DEC_BY expr _KW_STEP _KW_PERIOD                                      -> dec_by_stmt
    | expr _KW_PERIOD                                                                -> expr_stmt

// 一步N蹿磨叽：syntax: NUMBER_LITERAL(=1) 步 N 蹿磨叽：
step_spec: NUMBER_LITERAL _KW_STEP expr _KW_STEP_LOOP                               -> step_spec_rule

?func_def: IDENTIFIER _KW_OPEN_PAREN param_list _KW_CLOSE_PAREN _KW_DEF stmt* _KW_END _KW_PERIOD -> func_def_with_params
         | IDENTIFIER _KW_DEF stmt* _KW_END _KW_PERIOD                              -> func_def_no_params

method_def: IDENTIFIER _KW_OPEN_PAREN param_list _KW_CLOSE_PAREN _KW_DEF stmt* _KW_END _KW_PERIOD -> method_def_with_params
          | IDENTIFIER _KW_DEF stmt* _KW_END _KW_PERIOD                             -> method_def_no_params

param_list: IDENTIFIER (_KW_COMMA IDENTIFIER)*

// =================== Expressions ===================

// Concatenation (lowest precedence, left-associative via list)
?expr: concat_expr

concat_expr: non_concat_expr (_KW_CONCAT non_concat_expr)*

// non_concat_expr: comparison, tuple, or plain arithmetic.
// 跟 is dual-role (comparison op AND tuple separator); Earley resolves the ambiguity.
?non_concat_expr: compare_expr
               | tuple_expr
               | arith_expr

// Comparison expressions (all forms)
compare_expr: arith_expr _KW_COMPARE arith_expr KW_GREATER                          -> comp_greater
    | arith_expr _KW_COMPARE arith_expr KW_LESS                                      -> comp_less
    | arith_expr KW_IS_NONE                                                          -> comp_is_none
    | arith_expr _KW_COMPARE_WITH arith_expr KW_EQUAL                                -> comp_eq
    | arith_expr _KW_COMPARE_WITH arith_expr KW_NOT_EQUAL                            -> comp_neq

// Tuple element: comparison or plain arithmetic (but not another tuple)
?tuple_element: compare_expr | arith_expr

// Tuple expressions (right-recursive; elements may be comparison expressions)
tuple_expr: tuple_element _KW_TUPLE                                                  -> singleton_tuple_expr
          | tuple_element _KW_COMPARE_WITH tuple_expr                                -> cons_tuple_expr

// Additive (left-recursive)
?arith_expr: arith_expr KW_PLUS term_expr                                            -> add_expr
           | arith_expr KW_MINUS term_expr                                           -> sub_expr
           | term_expr

// Multiplicative (left-recursive)
?term_expr: term_expr KW_TIMES atom_expr                                             -> mul_expr
          | term_expr KW_DIVIDE_BY atom_expr                                         -> div_expr
          | term_expr KW_INTEGER_DIVIDE_BY atom_expr                                 -> idiv_expr
          | term_expr KW_MODULO atom_expr                                            -> mod_expr
          | atom_expr

// Postfix / prefix (left-recursive for postfix, right-recursive for negate)
?atom_expr: _KW_NEGATE atom_expr                                                     -> negate_expr
          | atom_expr KW_INDEX_1                                                     -> index1_expr
          | atom_expr KW_INDEX_LAST                                                  -> index_last_expr
          | atom_expr _KW_INDEX object_expr                                          -> index_expr
          | atom_expr _KW_DOT IDENTIFIER                                             -> dot_expr
          | atom_expr call_expr                                                      -> method_call_expr
          | atom_expr _KW_LENGTH                                                     -> length_expr
          | atom_expr _KW_REMOVE_HEAD                                                -> remove_head_expr
          | atom_expr _KW_REMOVE_TAIL                                                -> remove_tail_expr
          | object_expr

?object_expr: _KW_TUPLE                                                              -> empty_tuple_expr
           | NUMBER_LITERAL                                                          -> num_literal_expr
           | KW_IS_NONE                                                              -> none_literal_expr
           | _KW_OPEN_QUOTE STRING_LITERAL _KW_CLOSE_QUOTE                          -> str_literal_expr
           | IDENTIFIER _KW_NEW_OBJECT_OF _KW_OPEN_PAREN expr_list _KW_CLOSE_PAREN -> new_object_with_args_expr
           | IDENTIFIER _KW_NEW_OBJECT_OF                                           -> new_object_expr
           | IDENTIFIER                                                              -> variable_expr
           | _KW_OPEN_PAREN expr _KW_CLOSE_PAREN                                    -> paren_expr
           | call_expr
           | _KW_OPEN_BRACKET _KW_CLOSE_BRACKET                                    -> empty_list_expr
           | _KW_OPEN_BRACKET expr_list _KW_CLOSE_BRACKET                           -> list_literal_expr

?call_expr: _KW_CALL _KW_BASE_INIT _KW_OPEN_PAREN expr_list _KW_CLOSE_PAREN        -> call_base_init
         | _KW_CALL _KW_BASE_INIT _KW_OPEN_PAREN _KW_CLOSE_PAREN                    -> call_base_init
         | _KW_CALL _KW_BASE_INIT                                                    -> call_base_init
         | _KW_CALL IDENTIFIER _KW_OPEN_PAREN expr_list _KW_CLOSE_PAREN             -> call_func
         | _KW_CALL IDENTIFIER _KW_OPEN_PAREN _KW_CLOSE_PAREN                       -> call_func
         | _KW_CALL IDENTIFIER                                                       -> call_func

expr_list: expr (_KW_COMMA expr)* _KW_COMMA?

// =================== Terminal declarations ===================
// Patterns are placeholders; actual matching is done by _DongbeiLexer.
IDENTIFIER:              /x/
NUMBER_LITERAL:          /x/
STRING_LITERAL:          /x/
_KW_APPEND:              /x/
_KW_ASSERT:              /x/
_KW_ASSERT_FALSE:        /x/
_KW_BASE_INIT:           /x/
_KW_BECOME:              /x/
_KW_BEGIN:               /x/
_KW_BREAK:               /x/
_KW_CALL:                /x/
_KW_CHECK:               /x/
_KW_CLASS:               /x/
_KW_CLOSE_BRACKET:       /x/
_KW_CLOSE_PAREN:         /x/
_KW_CLOSE_QUOTE:         /x/
_KW_COLON:               /x/
_KW_COMMA:               /x/
_KW_COMPARE:             /x/
_KW_COMPARE_WITH:        /x/
_KW_CONCAT:              /x/
_KW_CONTINUE:            /x/
KW_DEC:                  /x/
_KW_DEC_BY:              /x/
_KW_DEL:                 /x/
_KW_DERIVED:             /x/
KW_DIVIDE_BY:            /x/
_KW_ELSE:                /x/
_KW_END:                 /x/
_KW_END_LOOP:            /x/
KW_EQUAL:                /x/
_KW_EXTEND:              /x/
_KW_FROM:                /x/
_KW_DEF:                 /x/
KW_GREATER:              /x/
_KW_IMPORT:              /x/
_KW_IN:                  /x/
KW_INC:                  /x/
_KW_INC_BY:              /x/
_KW_INDEX:               /x/
KW_INDEX_1:              /x/
KW_INDEX_LAST:           /x/
_KW_1_INFINITE_LOOP:     /x/
_KW_1_INFINITE_LOOP_EGG: /x/
KW_INTEGER_DIVIDE_BY:    /x/
_KW_IS_LIST:             /x/
KW_IS_NONE:              /x/
_KW_IS_VAR:              /x/
_KW_LENGTH:              /x/
KW_LESS:                 /x/
_KW_LOOP:                /x/
KW_MINUS:                /x/
KW_MODULO:               /x/
_KW_NEGATE:              /x/
_KW_NEW_OBJECT_OF:       /x/
KW_NOT_EQUAL:            /x/
_KW_OPEN_BRACKET:        /x/
_KW_OPEN_PAREN:          /x/
_KW_OPEN_QUOTE:          /x/
_KW_PERIOD:              /x/
KW_PLUS:                 /x/
_KW_RAISE:               /x/
_KW_REMOVE_HEAD:         /x/
_KW_REMOVE_TAIL:         /x/
_KW_RETURN:              /x/
_KW_SAY_DIGU:            /x/
_KW_SET_NONE:            /x/
_KW_STEP:                /x/
_KW_STEP_LOOP:           /x/
_KW_THEN:                /x/
KW_TIMES:                /x/
_KW_TUPLE:               /x/
_KW_TO:                  /x/
_KW_YIELD:               /x/
_KW_DOT:                 /x/
"""


class _DongbeiLexer(_LarkLexer):
    """Custom Lark lexer that feeds pre-tokenized dongbei Tokens into the Earley parser."""

    __future_interface__ = 0

    def __init__(self, lexer_conf):
        pass

    def lex(self, token_list):
        """Yield lark.Token objects wrapping each dongbei Token.

        The original dongbei Token is preserved as lark.Token.value so
        the Transformer can recover it.
        """
        for dk_tok in token_list:
            if dk_tok.kind == TK_KEYWORD:
                terminal = _KW_VALUE_TO_TERMINAL.get(dk_tok.value)
                if terminal is None:
                    raise ValueError(f"这关键字咱不认识：{dk_tok}，整啥呢？")
                yield lark.Token(terminal, dk_tok)
            elif dk_tok.kind == TK_IDENTIFIER:
                yield lark.Token("IDENTIFIER", dk_tok)
            elif dk_tok.kind == TK_NUMBER_LITERAL:
                yield lark.Token("NUMBER_LITERAL", dk_tok)
            elif dk_tok.kind == TK_STRING_LITERAL:
                yield lark.Token("STRING_LITERAL", dk_tok)
            else:
                raise ValueError(f"解析器这儿整了个不认识的 token，整叉劈了：{dk_tok}")


def _loc():
    """Returns a dummy SourceLoc for synthesised tokens."""
    return SourceLoc()


class _DongbeiTransformer(lark.Transformer):
    """Converts a Lark parse tree into dongbei Statement / Expr AST nodes."""

    # ── helper ──────────────────────────────────────────────────────────────

    @staticmethod
    def _dk(lark_tok):
        """Unwrap a lark.Token to get the underlying dongbei Token."""
        return lark_tok.value

    # ── start rules ─────────────────────────────────────────────────────────

    def start(self, items):
        return list(items)

    def start_expr(self, items):
        return items[0]

    def start_stmt(self, items):
        return items[0]

    # ── statements ──────────────────────────────────────────────────────────

    def import_stmt(self, items):
        return Statement(STMT_IMPORT, self._dk(items[0]))

    def compound_stmt(self, items):
        return Statement(STMT_COMPOUND, list(items))

    def assert_stmt(self, items):
        return Statement(STMT_ASSERT, items[0])

    def assert_false_stmt(self, items):
        return Statement(STMT_ASSERT_FALSE, items[0])

    def raise_stmt(self, items):
        return Statement(STMT_RAISE, items[0])

    def set_none_stmt(self, items):
        return Statement(STMT_SET_NONE, items[0])

    def del_stmt(self, items):
        return Statement(STMT_DEL, items[0])

    def say_stmt(self, items):
        return Statement(STMT_SAY, items[0])

    def return_stmt(self, items):
        return Statement(STMT_RETURN, items[0])

    def continue_stmt(self, items):
        return Statement(STMT_CONTINUE, None)

    def break_stmt(self, items):
        return Statement(STMT_BREAK, None)

    def if_stmt(self, items):
        expr, then_stmt = items
        return Statement(STMT_CONDITIONAL, (expr, then_stmt, None))

    def if_else_stmt(self, items):
        expr, then_stmt, else_stmt = items
        return Statement(STMT_CONDITIONAL, (expr, then_stmt, else_stmt))

    def var_decl_stmt(self, items):
        return Statement(STMT_VAR_DECL, self._dk(items[0]))

    def list_decl_stmt(self, items):
        return Statement(STMT_LIST_VAR_DECL, self._dk(items[0]))

    def class_def_stmt(self, items):
        # grammar: IDENTIFIER(class) _KW_CLASS _KW_DERIVED IDENTIFIER(base) _KW_CLASS _KW_DEF method* _KW_END _KW_PERIOD
        class_tok = self._dk(items[0])   # the new class (e.g. 无产 or Foo)
        base_tok = self._dk(items[1])    # the base class
        methods = list(items[2:])
        return Statement(STMT_CLASS_DEF, (base_tok, class_tok, methods))

    def loop_stmt(self, items):
        var_expr, from_expr, to_expr = items[0], items[1], items[2]
        stmts = list(items[3:])
        step_expr = number_literal_expr(1, _loc())  # synthesised constant — no source token
        return Statement(STMT_LOOP, (var_expr, from_expr, to_expr, step_expr, stmts))

    def step_loop_stmt(self, items):
        var_expr, from_expr, to_expr, step_expr = items[0], items[1], items[2], items[3]
        stmts = list(items[4:])
        return Statement(STMT_LOOP, (var_expr, from_expr, to_expr, step_expr, stmts))

    def step_spec_rule(self, items):
        # NUMBER_LITERAL(1) _KW_STEP step_expr _KW_STEP_LOOP → return step_expr
        return items[1]  # items[0] is the number literal (always 1), items[1] is step_expr

    def range_loop_stmt(self, items):
        var_expr, range_expr = items[0], items[1]
        stmts = list(items[2:])
        return Statement(STMT_RANGE_LOOP, (var_expr, range_expr, stmts))

    def infinite_loop_stmt(self, items):
        var_expr = items[0]
        stmts = list(items[1:])
        return Statement(STMT_INFINITE_LOOP, (var_expr, stmts))

    def assign_stmt(self, items):
        return Statement(STMT_ASSIGN, (items[0], items[1]))

    def append_stmt(self, items):
        return Statement(STMT_APPEND, (items[0], items[1]))

    def extend_stmt(self, items):
        return Statement(STMT_EXTEND, (items[0], items[1]))

    def yield_stmt(self, items):
        return Statement(STMT_YIELD, items[0])

    def inc_stmt(self, items):
        # items: [expr, KW_INC token]
        assert self._dk(items[1]).value == KW_INC
        return Statement(STMT_INC_BY, (items[0], number_literal_expr(1, self._dk(items[1]).loc)))

    def inc_by_stmt(self, items):
        return Statement(STMT_INC_BY, (items[0], items[1]))

    def dec_stmt(self, items):
        # items: [expr, KW_DEC token]
        assert self._dk(items[1]).value == KW_DEC
        return Statement(STMT_DEC_BY, (items[0], number_literal_expr(1, self._dk(items[1]).loc)))

    def dec_by_stmt(self, items):
        return Statement(STMT_DEC_BY, (items[0], items[1]))

    def expr_stmt(self, items):
        expr = items[0]
        if isinstance(expr, CallExpr):
            return Statement(STMT_CALL, expr)
        return Statement(STMT_EXPR, expr)

    # ── function / method definitions ────────────────────────────────────────

    def func_def_no_params(self, items):
        func_tok = self._dk(items[0])
        stmts = list(items[1:])
        return Statement(STMT_FUNC_DEF, (func_tok, [], stmts))

    def func_def_with_params(self, items):
        func_tok = self._dk(items[0])
        params = items[1]   # list from param_list
        stmts = list(items[2:])
        return Statement(STMT_FUNC_DEF, (func_tok, params, stmts))

    def method_def_no_params(self, items):
        func_tok = self._dk(items[0])
        stmts = list(items[1:])
        params = [identifier_token(ID_SELF, _loc())]  # implicit self — no source token
        return Statement(STMT_FUNC_DEF, (func_tok, params, stmts))

    def method_def_with_params(self, items):
        func_tok = self._dk(items[0])
        params = items[1]   # list from param_list
        stmts = list(items[2:])
        all_params = [identifier_token(ID_SELF, _loc())] + params  # implicit self — no source token
        return Statement(STMT_FUNC_DEF, (func_tok, all_params, stmts))

    def param_list(self, items):
        return [self._dk(tok) for tok in items]

    # ── expressions ──────────────────────────────────────────────────────────

    def concat_expr(self, items):
        if len(items) == 1:
            return items[0]
        return ConcatExpr(list(items))

    def comp_greater(self, items):
        # items: [left_expr, right_expr, KW_GREATER token]
        assert self._dk(items[2]).value == KW_GREATER
        return ComparisonExpr(items[0], keyword(KW_GREATER, self._dk(items[2]).loc), items[1])

    def comp_less(self, items):
        # items: [left_expr, right_expr, KW_LESS token]
        assert self._dk(items[2]).value == KW_LESS
        return ComparisonExpr(items[0], keyword(KW_LESS, self._dk(items[2]).loc), items[1])

    def comp_is_none(self, items):
        # items: [left_expr, KW_IS_NONE token]
        assert self._dk(items[1]).value == KW_IS_NONE
        return ComparisonExpr(items[0], keyword(KW_IS_NONE, self._dk(items[1]).loc), None)

    def comp_eq(self, items):
        # items: [left_expr, right_expr, KW_EQUAL token]
        assert self._dk(items[2]).value == KW_EQUAL
        return ComparisonExpr(items[0], keyword(KW_EQUAL, self._dk(items[2]).loc), items[1])

    def comp_neq(self, items):
        # items: [left_expr, right_expr, KW_NOT_EQUAL token]
        assert self._dk(items[2]).value == KW_NOT_EQUAL
        return ComparisonExpr(items[0], keyword(KW_NOT_EQUAL, self._dk(items[2]).loc), items[1])

    def singleton_tuple_expr(self, items):
        return TupleExpr((items[0],))

    def cons_tuple_expr(self, items):
        # items[0]: head element; items[1]: tail TupleExpr
        return TupleExpr((items[0],) + items[1].tuple)

    # Arithmetic; items: [left_expr, KW_OP token, right_expr]
    def add_expr(self, items):
        assert self._dk(items[1]).value == KW_PLUS
        return ArithmeticExpr(items[0], keyword(KW_PLUS, self._dk(items[1]).loc), items[2])

    def sub_expr(self, items):
        assert self._dk(items[1]).value == KW_MINUS
        return ArithmeticExpr(items[0], keyword(KW_MINUS, self._dk(items[1]).loc), items[2])

    def mul_expr(self, items):
        assert self._dk(items[1]).value == KW_TIMES
        return ArithmeticExpr(items[0], keyword(KW_TIMES, self._dk(items[1]).loc), items[2])

    def div_expr(self, items):
        assert self._dk(items[1]).value == KW_DIVIDE_BY
        return ArithmeticExpr(items[0], keyword(KW_DIVIDE_BY, self._dk(items[1]).loc), items[2])

    def idiv_expr(self, items):
        assert self._dk(items[1]).value == KW_INTEGER_DIVIDE_BY
        return ArithmeticExpr(items[0], keyword(KW_INTEGER_DIVIDE_BY, self._dk(items[1]).loc), items[2])

    def mod_expr(self, items):
        assert self._dk(items[1]).value == KW_MODULO
        return ArithmeticExpr(items[0], keyword(KW_MODULO, self._dk(items[1]).loc), items[2])

    # Postfix / prefix
    def negate_expr(self, items):
        return NegateExpr(items[0])

    def index1_expr(self, items):
        # items: [atom_expr, KW_INDEX_1 token]
        assert self._dk(items[1]).value == KW_INDEX_1
        return IndexExpr(items[0], number_literal_expr(1, self._dk(items[1]).loc))

    def index_last_expr(self, items):
        # items: [atom_expr, KW_INDEX_LAST token]
        assert self._dk(items[1]).value == KW_INDEX_LAST
        return IndexExpr(items[0], number_literal_expr(0, self._dk(items[1]).loc))

    def index_expr(self, items):
        return IndexExpr(items[0], items[1])

    def dot_expr(self, items):
        return ObjectPropertyExpr(items[0], self._dk(items[1]))

    def method_call_expr(self, items):
        return MethodCallExpr(items[0], items[1])

    def length_expr(self, items):
        return LengthExpr(items[0])

    def remove_head_expr(self, items):
        return SubListExpr(items[0], 1, None)

    def remove_tail_expr(self, items):
        return SubListExpr(items[0], None, 1)

    # Object expressions
    def empty_tuple_expr(self, items):
        return TupleExpr(())

    def num_literal_expr(self, items):
        return LiteralExpr(self._dk(items[0]))

    def none_literal_expr(self, items):
        # items: [KW_IS_NONE token]
        assert self._dk(items[0]).value == KW_IS_NONE
        return LiteralExpr(Token(TK_NONE_LITERAL, None, self._dk(items[0]).loc))

    def str_literal_expr(self, items):
        return LiteralExpr(self._dk(items[0]))

    def new_object_expr(self, items):
        return NewObjectExpr(self._dk(items[0]), [])

    def new_object_with_args_expr(self, items):
        class_tok = self._dk(items[0])
        args = items[1]
        return NewObjectExpr(class_tok, args)

    def variable_expr(self, items):
        return VariableExpr(self._dk(items[0]).value)

    def paren_expr(self, items):
        return ParenExpr(items[0])

    def list_literal_expr(self, items):
        return ListExpr(items[0])

    def empty_list_expr(self, items):
        return ListExpr([])

    # Call expressions
    def call_base_init(self, items):
        args = items[0] if items else []
        return CallExpr("super().__init__", args)

    def call_func(self, items):
        func_name = self._dk(items[0]).value
        args = items[1] if len(items) > 1 else []
        return CallExpr(func_name, args)

    def expr_list(self, items):
        return list(items)


# Cached Lark parser (compiled once at import time).
_lark_parser = lark.Lark(
    _DONGBEI_GRAMMAR,
    parser="earley",
    lexer=_DongbeiLexer,
    start=["start", "start_expr", "start_stmt"],
    ambiguity="resolve",
)
_lark_transformer = _DongbeiTransformer()


ID_ARGV = "最高指示"
ID_INIT = "新对象"
ID_SELF = "俺"
ID_YOU_SAY = "你吱声"
ID_TRUE = "没毛病"
ID_FALSE = "有毛病"
ID_SLEEP = "打个盹"

# Maps a dongbei identifier to its corresponding Python identifier.
_dongbei_var_to_python_var = {
    ID_ARGV: "sys.argv",
    ID_INIT: "__init__",
    ID_SELF: "self",
    ID_YOU_SAY: "input",
    ID_TRUE: "True",
    ID_FALSE: "False",
    ID_SLEEP: "time.sleep",
}


def get_python_var_name(var):
    if var in _dongbei_var_to_python_var:
        return _dongbei_var_to_python_var[var]

    return var


# Expression grammar:
#
#   Expr ::= NonConcatExpr |
#            Expr 、 NonConcatExpr
#   NonConcatExpr ::= TupleExpr | CompOrArithExpr
#   CompOrArithExpr ::= ComparisonExpr | ArithmeticExpr
#   TupleExpr ::= CompOrArithExpr 抱团 |
#                 CompOrArithExpr 跟 TupleExpr
#   ComparisonExpr ::= ArithmeticExpr 比 ArithmeticExpr 还大 |
#                      ArithmeticExpr 比 ArithmeticExpr 还小 |
#                      ArithmeticExpr 跟 ArithmeticExpr 一样一样的 |
#                      ArithmeticExpr 跟 ArithmeticExpr 不是一样一样的
#   ArithmeticExpr ::= TermExpr |
#                      ArithmeticExpr 加 TermExpr |
#                      ArithmeticExpr 减 TermExpr
#   TermExpr ::= AtomicExpr |
#                TermExpr 乘 AtomicExpr |
#                TermExpr 除以 AtomicExpr |
#                TermExpr 齐整整地除以 AtomicExpr
#   AtomicExpr ::= ObjectExpr | AtomicExpr 的老 ObjectExpr | AtomicExpr 的 Identifier |
#                  AtomicExpr CallExpr | AtomicExpr 有几个坑 |
#                  AtomicExpr 掐头 | AtomicExpr 去尾 | NegateExpr
#   NegateExpr ::= 拉饥荒 AtomicExpr
#   ObjectExpr ::= 抱团 | LiteralExpr | VariableExpr | ParenExpr | CallExpr |
#                  「 ExprList 」 |
#                  Identifier 的新对象 | Identifier 的新对象（ExprList）
#   ParenExpr ::= （ Expr ）
#   CallExpr ::= 整 Identifier |
#                整 Identifier（ExprList）
#   ExprList ::= Expr |
#                Expr，ExprList

# Not meant to be in DongbeiParser.
def parse_expr_from_str(str):
    parser = DongbeiParser()
    tokens = parser.tokenize(str, None)
    tree = _lark_parser.parse(tokens, start="start_expr")
    return _lark_transformer.transform(tree)


# Not meant to be in DongbeiParser.
def parse_stmt_from_str(str):
    parser = DongbeiParser()
    tokens = parser.tokenize(str, None)
    tree = _lark_parser.parse(tokens, start="start_stmt")
    return _lark_transformer.transform(tree)


def translate_statement_to_python(stmt, indent=""):
    """Translates the statements to Python code, without trailing newline."""

    if stmt.kind == STMT_VAR_DECL:
        var_token = stmt.value
        var = get_python_var_name(var_token.value)
        return indent + "%s = None" % (var,)

    if stmt.kind == STMT_LIST_VAR_DECL:
        var_token = stmt.value
        var = get_python_var_name(var_token.value)
        return indent + "%s = []" % (var,)

    if stmt.kind == STMT_ASSIGN:
        var_expr, expr = stmt.value
        var = var_expr.to_python()
        return indent + "%s = %s" % (var, expr.to_python())

    if stmt.kind == STMT_APPEND:
        var_expr, expr = stmt.value
        var = var_expr.to_python()
        return indent + "(%s).append(%s)" % (var, expr.to_python())

    if stmt.kind == STMT_EXTEND:
        var_expr, expr = stmt.value
        var = var_expr.to_python()
        return indent + "(%s).extend(%s)" % (var, expr.to_python())

    if stmt.kind == STMT_SAY:
        expr = stmt.value
        return indent + "_dongbei_print(%s)" % (expr.to_python(),)

    if stmt.kind == STMT_YIELD:
        expr = stmt.value
        return indent + f"yield ({expr.to_python()})"

    if stmt.kind == STMT_INC_BY:
        var_expr, expr = stmt.value
        var = var_expr.to_python()
        return indent + f"{var} += {expr.to_python()}"

    if stmt.kind == STMT_DEC_BY:
        var_expr, expr = stmt.value
        var = var_expr.to_python()
        return indent + "%s -= %s" % (var, expr.to_python())

    if stmt.kind == STMT_LOOP:
        var_expr, from_val, to_val, step_expr, stmts = stmt.value
        var = var_expr.to_python()
        loop = indent + "for %s in range(%s, (%s) + 1, %s):" % (
            var,
            from_val.to_python(),
            to_val.to_python(),
            step_expr.to_python(),
        )
        for s in stmts:
            loop += "\n" + translate_statement_to_python(s, indent + "  ")
        if not stmts:
            loop += "\n" + indent + "  pass"
        return loop

    if stmt.kind == STMT_RANGE_LOOP:
        var_expr, range_expr, stmts = stmt.value
        var = var_expr.to_python()
        loop = indent + "for %s in %s:" % (var, range_expr.to_python())
        for s in stmts:
            loop += "\n" + translate_statement_to_python(s, indent + "  ")
        if not stmts:
            loop += "\n" + indent + "  pass"
        return loop

    if stmt.kind == STMT_INFINITE_LOOP:
        var_expr, stmts = stmt.value
        var = var_expr.to_python()
        loop = indent + "for %s in _dongbei_1_infinite_loop():" % (var,)
        for s in stmts:
            loop += "\n" + translate_statement_to_python(s, indent + "  ")
        if not stmts:
            loop += "\n" + indent + "  pass"
        return loop

    if stmt.kind == STMT_FUNC_DEF:
        func_token, params, stmts = stmt.value
        func_name = get_python_var_name(func_token.value)
        param_names = map(lambda tk: get_python_var_name(tk.value), params)
        code = indent + "def %s(%s):" % (func_name, ", ".join(param_names))
        for s in stmts:
            code += "\n" + translate_statement_to_python(s, indent + "  ")
        if not stmts:
            code += "\n" + indent + "  pass"
        return code

    if stmt.kind == STMT_CALL:
        func = stmt.value.func
        args = stmt.value.args
        func_name = get_python_var_name(func)
        code = indent + "%s(%s)" % (
            func_name,
            ", ".join(arg.to_python() for arg in args),
        )
        return code

    if stmt.kind == STMT_RETURN:
        return indent + "return " + stmt.value.to_python()

    if stmt.kind == STMT_COMPOUND:
        code = indent + "if True:"
        stmts = stmt.value
        if stmts:
            for s in stmts:
                code += "\n" + translate_statement_to_python(s, indent + "  ")
        else:
            code += "\n" + indent + "  pass"
        return code

    if stmt.kind == STMT_CONDITIONAL:
        condition, then_stmt, else_stmt = stmt.value
        code = indent + "if %s:\n" % (condition.to_python(),)
        code += translate_statement_to_python(then_stmt, indent + "  ")
        if else_stmt:
            code += "\n" + indent + "else:\n"
            code += translate_statement_to_python(else_stmt, indent + "  ")
        return code

    if stmt.kind == STMT_SET_NONE:
        return indent + stmt.value.to_python() + " = None"

    if stmt.kind == STMT_DEL:
        return indent + "del " + stmt.value.to_python()

    if stmt.kind == STMT_IMPORT:
        return indent + f"import {stmt.value.value}"

    if stmt.kind == STMT_BREAK:
        return indent + "break"

    if stmt.kind == STMT_CONTINUE:
        return indent + "continue"

    if stmt.kind == STMT_ASSERT:
        return (
            indent
            + f'assert {stmt.value.to_python()}, "该着 {stmt.value.to_dongbei()}，咋有毛病了咧？"'
        )

    if stmt.kind == STMT_ASSERT_FALSE:
        return (
            indent
            + f'assert not ({stmt.value.to_python()}), "{stmt.value.to_dongbei()} 不应该啊，咋有毛病了咧？"'
        )

    if stmt.kind == STMT_RAISE:
        return indent + f"raise _Dongbei_Error({stmt.value.to_python()})"

    if stmt.kind == STMT_CLASS_DEF:
        subclass, baseclass, methods = stmt.value
        baseclass_decl = ""
        if baseclass.value != "无产":
            baseclass_decl = "(" + get_python_var_name(baseclass.value) + ")"
        code = indent + f"class {get_python_var_name(subclass.value)}{baseclass_decl}:\n"
        if not methods:
            return code + indent + "  pass"
        for method in methods:
            code += "\n" + translate_statement_to_python(method, indent + "  ")
        return code

    if stmt.kind == STMT_EXPR:
        return indent + stmt.value.to_python()

    raise Exception("俺不懂 %s 语句咋执行。" % (stmt.kind))


# Not meant to be in DongbeiParser.
def parse_to_statements(code):
    parser = DongbeiParser()
    tokens = parser.tokenize(code, None)
    return parser.translate_tokens_to_statements(tokens)


_dongbei_output = ""


def _dongbei_append_output(s):
    global _dongbei_output
    _dongbei_output += s


def _dongbei_print(value):
    s = _dongbei_str(value)
    print(s)
    _dongbei_append_output(s + "\n")


def _dongbei_1_infinite_loop():
    while True:
        yield 1


def translate_dongbei_to_python(code: str, src_file: str, xudao: bool = False) -> str:
    parser = DongbeiParser()
    tokens = parser.tokenize(code, src_file)
    statements = parser.translate_tokens_to_statements(tokens)

    py_code_lines = []
    for s in statements:
        py_code_lines.append(translate_statement_to_python(s))
    py_code = "\n".join(py_code_lines)
    if xudao:
        print("Python 代码：")
        print(py_code)
        print()
    return py_code


def run_py_code(py_code: str) -> str:
    """Runs the given python code.

    Args:
        py_code: the python code

    Returns:
        the output of the python code
    """
    global _dongbei_output
    _dongbei_output = ""
    # See https://stackoverflow.com/questions/871887/using-exec-with-recursive-functions
    # Use the same dictionary for local and global definitions.
    # Needed for defining recursive dongbei functions.
    try:
        exec(py_code, globals(), globals())
    except Exception as e:
        _dongbei_print(f"\n整叉劈了：{e}")
    return _dongbei_output


def translate_and_run(dongbei_code: str, src_file: str, xudao: bool = False) -> str:
    """Translates the given dongbei code to python and runs it.

    Args:
        dongbei_code: the dongbei code
        src_file: path to the source file containing the dongbei code; used for error reporting
        xudao: if True, print the python code translated from the dongbei code

    Returns:
        the output of the dongbei code
    """

    py_code = translate_dongbei_to_python(dongbei_code, src_file=src_file, xudao=xudao)
    return run_py_code(py_code)


def get_input(prompt: str) -> str:
    return input(prompt)


def repl():
    """dongbei 语言 REPL.

    Yields:
        output of each statement
    """

    print("你要跟 dongbei 大哥唠嗑啊？开整吧！要是一句话太长咧你就用\\拆开唠。")
    while True:
        dongbei_code = ""
        prompt = "你瞅啥？ "
        while True:
            line = get_input(prompt)
            if line.endswith("\\"):  # 未完待续
                dongbei_code += line.rstrip("\\") + "\n"
                prompt = "你还瞅啥？ "
            else:
                dongbei_code += line
                break
        if re.fullmatch(r"(瞅你咋的|瞅你咋地|瞅你咋滴)(\?|？|)", dongbei_code.strip()):
            print("完犊子了！")
            break

        try:
            py_code = translate_dongbei_to_python(dongbei_code, src_file="你瞅那动静")
        except Exception as e1:
            try:
                py_code = translate_dongbei_to_python(
                    f"嘀咕：{dongbei_code}。", src_file="你瞅那玩意儿"
                )
            except Exception as e2:
                if "\n" in dongbei_code:
                    # Multi-line code.
                    print(f"你要瞅：\n{dongbei_code}")
                else:
                    # Single-line code.
                    print(f"你要瞅：{dongbei_code}")

                print(e1)
                print(e2)

        try:
            yield run_py_code(py_code)
        except Exception as e:
            print(e)


def dongbei_cli(argv):
    if argv and (
        argv[0].endswith(".exe")
        or os.path.basename(argv[0]) in ("dongbei", "dongbei.py")
    ):
        argv = argv[1:]

    if len(argv) == 0:
        for output in repl():
            pass
        return

    if len(argv) > 1:
        sys.exit(
            "dongbei大哥一次只能上手一个源文件；不然扒蒜老妹儿会觉得大哥不够专一，把大哥爆锤。\n"
            f"你咋给了 {len(argv)} 个源文件咧："
            f"{'、'.join(argv)}。"
        )

    program = argv[0]

    if FLAGS.bihua:
        curr_src_base = os.path.dirname(os.path.abspath(__file__))
        example_program = os.path.join(curr_src_base, f"../demo/{program}.dongbei")

        if not os.path.exists(example_program):
            print(f"dongbei 大哥尽力了，但 dongbei 大哥没有找到案例 「{program}」。")
            print()

            all_examples = sorted(
                map(
                    lambda example_file: os.path.splitext(example_file.name)[0],
                    os.scandir(os.path.join(curr_src_base, "../demo")),
                )
            )
            print("俺这儿有这些案例，挑一个试试：")
            for i in range(0, len(all_examples), EXAMPLE_GROUP_SIZE):
                print(", ".join(all_examples[i : i + EXAMPLE_GROUP_SIZE]))
            sys.exit(1)

        print(f"执行 dongbei 案例: 「{program}」")
        print()
        program = example_program

    with io.open(program, "r", encoding="utf-8") as src_file:
        if FLAGS.xudao:
            print(f"整上 {program} 喽……")
        try:
            translate_and_run(src_file.read(), src_file=program, xudao=FLAGS.xudao)
        except Exception as e:
            print(e)


def main():
    app.run(dongbei_cli)


if __name__ == "__main__":
    main()
