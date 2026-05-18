#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import unittest
from unittest.mock import patch

# Add the repo root to the beginning of the Python module path.
# Even if the user has installed dongbei locally, the version
# next to the test file will be used.
sys.path = [os.path.join(os.path.dirname(__file__), "..")] + sys.path

from src import dongbei as dongbei
from src.dongbei import ArithmeticExpr
from src.dongbei import CallExpr
from src.dongbei import ComparisonExpr
from src.dongbei import ConcatExpr
from src.dongbei import DongbeiParser
from src.dongbei import LiteralExpr
from src.dongbei import ParenExpr
from src.dongbei import parse_expr_from_str as ParseExprFromStr
from src.dongbei import parse_stmt_from_str as ParseStmtFromStr
from src.dongbei import parse_to_statements as ParseToStatements
from src.dongbei import tokenize_str_containing_no_keyword as TokenizeStrContainingNoKeyword
from src.dongbei import try_parse_number as TryParseNumber
from src.dongbei import STMT_ASSIGN
from src.dongbei import STMT_CALL
from src.dongbei import STMT_CONDITIONAL
from src.dongbei import STMT_DEC_BY
from src.dongbei import STMT_FUNC_DEF
from src.dongbei import STMT_INC_BY
from src.dongbei import STMT_INFINITE_LOOP
from src.dongbei import STMT_LOOP
from src.dongbei import STMT_SAY
from src.dongbei import Statement
from src.dongbei import TK_CHAR
from src.dongbei import TK_IDENTIFIER
from src.dongbei import TK_NUMBER_LITERAL
from src.dongbei import TK_STRING_LITERAL
from src.dongbei import Token
from src.dongbei import translate_dongbei_to_python as TranslateDongbeiToPython
from src.dongbei import VariableExpr
from src.dongbei import SourceLoc


def keyword(value):
    return dongbei.keyword(value, None)


def number_literal_expr(value):
    return dongbei.number_literal_expr(value, None)


def identifier_token(identifier):
    return dongbei.identifier_token(identifier, None)


def tokenize(code):
    return DongbeiParser().tokenize(code, None)


def translate_and_run(code):
    return dongbei.translate_and_run(code, None)


def string_literal_expr(value):
    return LiteralExpr(Token(TK_STRING_LITERAL, value, None))


class DongbeiParseExprTest(unittest.TestCase):
    def test_parse_number(self):
        self.assertEqual(ParseExprFromStr("5"), number_literal_expr(5))
        self.assertEqual(ParseExprFromStr("九"), number_literal_expr(9))

    def test_parse_string_literal(self):
        self.assertEqual(
            ParseExprFromStr("“ 哈  哈   ”"), string_literal_expr(" 哈  哈   ")
        )

    def test_parse_identifier(self):
        self.assertEqual(ParseExprFromStr("老王"), VariableExpr("老王"))

    def test_parse_parens(self):
        # Wide parens.
        self.assertEqual(ParseExprFromStr("（老王）"), ParenExpr(VariableExpr("老王")))
        # Narrow parens.
        self.assertEqual(ParseExprFromStr("(老王)"), ParenExpr(VariableExpr("老王")))

    def test_parse_call_expr(self):
        self.assertEqual(ParseExprFromStr("整老王"), CallExpr("老王", []))
        self.assertEqual(
            ParseExprFromStr("整老王（5）"), CallExpr("老王", [number_literal_expr(5)])
        )
        self.assertEqual(
            ParseExprFromStr("整老王(6)"), CallExpr("老王", [number_literal_expr(6)])
        )
        self.assertEqual(
            ParseExprFromStr("整老王(老刘，6)"),
            CallExpr("老王", [VariableExpr("老刘"), number_literal_expr(6)]),
        )
        self.assertEqual(
            ParseExprFromStr("整老王(“你”，老刘，6)"),
            CallExpr(
                "老王", [string_literal_expr("你"), VariableExpr("老刘"), number_literal_expr(6)]
            ),
        )
        self.assertEqual(
            ParseExprFromStr("整老王(“你”,老刘，6)"),
            CallExpr(
                "老王", [string_literal_expr("你"), VariableExpr("老刘"), number_literal_expr(6)]
            ),
        )

    def test_parse_call_expr_empty_parens(self):
        # regression: Lark grammar requires explicit empty-paren rule
        self.assertEqual(ParseExprFromStr("整老王（）"), CallExpr("老王", []))
        self.assertEqual(ParseExprFromStr("整老王()"), CallExpr("老王", []))

    def test_parse_call_expr_dotted_name(self):
        # module.func and obj.method tokenize as a single IDENTIFIER
        self.assertEqual(
            ParseExprFromStr("整random.choice（老刘）"),
            CallExpr("random.choice", [VariableExpr("老刘")]),
        )
        self.assertEqual(
            ParseExprFromStr("整老王.upper（）"),
            CallExpr("老王.upper", []),
        )

    def test_parse_term_expr(self):
        self.assertEqual(
            ParseExprFromStr("老王乘五"),
            ArithmeticExpr(VariableExpr("老王"), keyword("乘"), number_literal_expr(5)),
        )
        self.assertEqual(
            ParseExprFromStr("五除以老王"),
            ArithmeticExpr(number_literal_expr(5), keyword("除以"), VariableExpr("老王")),
        )
        self.assertEqual(
            ParseExprFromStr("五除以老王乘老刘"),
            ArithmeticExpr(
                ArithmeticExpr(number_literal_expr(5), keyword("除以"), VariableExpr("老王")),
                keyword("乘"),
                VariableExpr("老刘"),
            ),
        )

    def test_parse_arithmetic_expr(self):
        self.assertEqual(
            ParseExprFromStr("5加六"),
            ArithmeticExpr(number_literal_expr(5), keyword("加"), number_literal_expr(6)),
        )
        self.assertEqual(
            ParseExprFromStr("5加六乘3"),
            ArithmeticExpr(
                number_literal_expr(5),
                keyword("加"),
                ArithmeticExpr(
                    number_literal_expr(6), keyword("乘"), number_literal_expr(3)
                ),
            ),
        )
        self.assertEqual(
            ParseExprFromStr("5减六减老王"),
            ArithmeticExpr(
                ArithmeticExpr(
                    number_literal_expr(5), keyword("减"), number_literal_expr(6)
                ),
                keyword("减"),
                VariableExpr("老王"),
            ),
        )

    def test_parse_comparison_expr(self):
        self.assertEqual(
            ParseExprFromStr("5比6还大"),
            ComparisonExpr(number_literal_expr(5), keyword("还大"), number_literal_expr(6)),
        )
        self.assertEqual(
            ParseExprFromStr("老王加5比6还小"),
            ComparisonExpr(
                ArithmeticExpr(VariableExpr("老王"), keyword("加"), number_literal_expr(5)),
                keyword("还小"),
                number_literal_expr(6),
            ),
        )
        self.assertEqual(
            ParseExprFromStr("老王跟老刘一样一样的"),
            ComparisonExpr(VariableExpr("老王"), keyword("一样一样的"), VariableExpr("老刘")),
        )
        self.assertEqual(
            ParseExprFromStr("老王加5跟6不是一样一样的"),
            ComparisonExpr(
                ArithmeticExpr(VariableExpr("老王"), keyword("加"), number_literal_expr(5)),
                keyword("不是一样一样的"),
                number_literal_expr(6),
            ),
        )

    def test_parse_concat_expr(self):
        self.assertEqual(
            ParseExprFromStr("老王、2"),
            ConcatExpr([VariableExpr("老王"), number_literal_expr(2)]),
        )

    def test_parse_concat_expr(self):
        self.assertEqual(
            ParseExprFromStr("老王加油、2、“哈”"),
            ConcatExpr(
                [
                    ArithmeticExpr(VariableExpr("老王"), keyword("加"), VariableExpr("油")),
                    number_literal_expr(2),
                    string_literal_expr("哈"),
                ]
            ),
        )


class DongbeiParseStatementTest(unittest.TestCase):
    def test_parse_conditional(self):
        self.assertEqual(
            ParseStmtFromStr("寻思：老王比五还大？要行咧就嘀咕：老王。"),
            Statement(
                STMT_CONDITIONAL,
                (
                    ComparisonExpr(
                        VariableExpr("老王"), keyword("还大"), number_literal_expr(5)
                    ),
                    # then-branch
                    Statement(STMT_SAY, VariableExpr("老王")),
                    # else-branch
                    None,
                ),
            ),
        )


class DongbeiTest(unittest.TestCase):
    def test_run_empty_program(self):
        self.assertEqual(translate_and_run(""), "")

    def test_run_hello_world(self):
        self.assertEqual(translate_and_run("嘀咕：“这旮旯儿嗷嗷美好哇！”。"), "这旮旯儿嗷嗷美好哇！\n")

    def test_run_hello_world2(self):
        self.assertEqual(translate_and_run("嘀咕：“你那旮旯儿也挺美好哇！”。"), "你那旮旯儿也挺美好哇！\n")

    def test_var_decl(self):
        self.assertEqual(translate_and_run("老张是活雷锋。"), "")

    def test_var_assignment(self):
        self.assertEqual(translate_and_run("老张是活雷锋。\n老张装250。\n嘀咕：老张。"), "250\n")

    def test_var_quotes_are_optional(self):
        self.assertEqual(translate_and_run("老张装二。嘀咕：【老张】。"), "2\n")

    def test_colon_can_be_narrow(self):
        self.assertEqual(translate_and_run("老张装二。嘀咕:【老张】。"), "2\n")

    def test_tokenize(self):
        self.assertEqual(tokenize("# 123456\n老张"), [identifier_token("老张")])
        self.assertEqual(tokenize("老张"), [identifier_token("老张")])
        self.assertEqual(TryParseNumber("老张"), (None, "老张"))
        self.assertEqual(
            list(TokenizeStrContainingNoKeyword("老张", None)), [identifier_token("老张")]
        )
        self.assertEqual(tokenize("老张是活雷锋"), [identifier_token("老张"), keyword("是活雷锋")])
        self.assertEqual(
            tokenize("老张是 活雷\n锋 。 "),
            [
                identifier_token("老张"),
                keyword("是活雷锋"),
                keyword("。"),
            ],
        )
        self.assertEqual(
            tokenize("老张是活雷锋。\n老王是活雷锋。\n"),
            [
                identifier_token("老张"),
                keyword("是活雷锋"),
                keyword("。"),
                identifier_token("老王"),
                keyword("是活雷锋"),
                keyword("。"),
            ],
        )
        self.assertEqual(
            tokenize("老张装250。\n老王装老张。\n"),
            [
                identifier_token("老张"),
                keyword("装"),
                Token(TK_NUMBER_LITERAL, 250, None),
                keyword("。"),
                identifier_token("老王"),
                keyword("装"),
                identifier_token("老张"),
                keyword("。"),
            ],
        )
        self.assertEqual(
            tokenize("嘀咕：“你好”。"),
            [
                keyword("嘀咕"),
                keyword("："),
                keyword("“"),
                Token(TK_STRING_LITERAL, "你好", None),
                keyword("”"),
                keyword("。"),
            ],
        )

    def test_tokenize_arithmetic(self):
        self.assertEqual(
            tokenize("250加13减二乘五除以九"),
            [
                Token(TK_NUMBER_LITERAL, 250, None),
                keyword("加"),
                Token(TK_NUMBER_LITERAL, 13, None),
                keyword("减"),
                Token(TK_NUMBER_LITERAL, 2, None),
                keyword("乘"),
                Token(TK_NUMBER_LITERAL, 5, None),
                keyword("除以"),
                Token(TK_NUMBER_LITERAL, 9, None),
            ],
        )

    def test_tokenize_loop(self):
        self.assertEqual(
            tokenize("老王从1到9磨叽：磨叽完了。"),
            [
                identifier_token("老王"),
                keyword("从"),
                Token(TK_NUMBER_LITERAL, 1, None),
                keyword("到"),
                Token(TK_NUMBER_LITERAL, 9, None),
                keyword("磨叽："),
                keyword("磨叽完了"),
                keyword("。"),
            ],
        )

    def test_tokenize_compound(self):
        self.assertEqual(
            tokenize("开整：\n  嘀咕：老王。\n整完了。"),
            [
                keyword("开整："),
                keyword("嘀咕"),
                keyword("："),
                identifier_token("老王"),
                keyword("。"),
                keyword("整完了"),
                keyword("。"),
            ],
        )

    def test_tokenizing_increments(self):
        self.assertEqual(
            tokenize("老王走走"),
            [
                identifier_token("老王"),
                keyword("走走"),
            ],
        )
        self.assertEqual(
            tokenize("老王走两步"),
            [
                identifier_token("老王"),
                keyword("走"),
                Token(TK_NUMBER_LITERAL, 2, None),
                keyword("步"),
            ],
        )

    def test_tokenizing_decrements(self):
        self.assertEqual(
            tokenize("老王稍稍"),
            [
                identifier_token("老王"),
                keyword("稍稍"),
            ],
        )
        self.assertEqual(
            tokenize("老王稍三步"),
            [
                identifier_token("老王"),
                keyword("稍"),
                Token(TK_NUMBER_LITERAL, 3, None),
                keyword("步"),
            ],
        )

    def test_tokenizing_concat(self):
        self.assertEqual(
            tokenize("老刘、二"),
            [
                identifier_token("老刘"),
                keyword("、"),
                Token(TK_NUMBER_LITERAL, 2, None),
            ],
        )

    def test_tokenizing_func_def(self):
        self.assertEqual(
            tokenize("写九九表咋整：整完了。"),
            [
                identifier_token("写九九表"),
                keyword("咋整："),
                keyword("整完了"),
                keyword("。"),
            ],
        )

    def test_tokenizing_func_call(self):
        self.assertEqual(
            tokenize("整写九九表"),
            [
                keyword("整"),
                identifier_token("写九九表"),
            ],
        )

    def test_parsing_increments(self):
        self.assertEqual(
            ParseToStatements("老王走走。"),
            [Statement(STMT_INC_BY, (VariableExpr("老王"), number_literal_expr(1)))],
        )
        self.assertEqual(
            ParseToStatements("老王走两步。"),
            [Statement(STMT_INC_BY, (VariableExpr("老王"), number_literal_expr(2)))],
        )

    def test_parsing_decrements(self):
        self.assertEqual(
            ParseToStatements("老王稍稍。"),
            [Statement(STMT_DEC_BY, (VariableExpr("老王"), number_literal_expr(1)))],
        )
        self.assertEqual(
            ParseToStatements("老王稍三步。"),
            [Statement(STMT_DEC_BY, (VariableExpr("老王"), number_literal_expr(3)))],
        )

    def test_parsing_loop(self):
        self.assertEqual(
            ParseToStatements("老王从1到9磨叽：磨叽完了。"),
            [
                Statement(
                    STMT_LOOP,
                    (
                        VariableExpr("老王"),
                        number_literal_expr(1),
                        number_literal_expr(9),
                        number_literal_expr(1),
                        [],
                    ),
                )
            ],
        )
        self.assertEqual(
            ParseToStatements("老王从二到十一步七蹿磨叽：磨叽完了。"),
            [
                Statement(
                    STMT_LOOP,
                    (
                        VariableExpr("老王"),
                        number_literal_expr(2),
                        number_literal_expr(10),
                        number_literal_expr(7),
                        [],
                    ),
                )
            ],
        )
        self.assertEqual(
            ParseToStatements("老王从二到十一步七减一蹿磨叽：磨叽完了。"),
            [
                Statement(
                    STMT_LOOP,
                    (
                        VariableExpr("老王"),
                        number_literal_expr(2),
                        number_literal_expr(10),
                        ArithmeticExpr(
                            number_literal_expr(7), keyword("减"), number_literal_expr(1)
                        ),
                        [],
                    ),
                )
            ],
        )
        self.assertEqual(
            ParseToStatements("老王从一而终磨叽：磨叽完了。"),
            [Statement(STMT_INFINITE_LOOP, (VariableExpr("老王"), []))],
        )
        self.assertEqual(
            ParseToStatements("老张在苹果总部磨叽：磨叽完了。"),
            [Statement(STMT_INFINITE_LOOP, (VariableExpr("老张"), []))],
        )

    def test_parsing_comparison(self):
        self.assertEquals(
            ParseToStatements("嘀咕：2比5还大。"),
            [
                Statement(
                    STMT_SAY,
                    ComparisonExpr(
                        number_literal_expr(2), keyword("还大"), number_literal_expr(5)
                    ),
                )
            ],
        )

    def test_parsing_func_def(self):
        self.assertEqual(
            ParseToStatements("写九九表咋整：整完了。"),
            [
                Statement(
                    STMT_FUNC_DEF,
                    (
                        identifier_token("写九九表"),
                        [],  # Formal parameters.
                        [],  # Function body.
                    ),
                )
            ],
        )
        self.assertEqual(
            ParseToStatements("写九九表咋整：嘀咕：1。整完了。"),
            [
                Statement(
                    STMT_FUNC_DEF,
                    (
                        identifier_token("写九九表"),
                        [],  # Formal parameters.
                        # Function body.
                        [
                            Statement(
                                STMT_SAY, LiteralExpr(Token(TK_NUMBER_LITERAL, 1, None))
                            )
                        ],
                    ),
                )
            ],
        )

    def test_parsing_func_def_with_param(self):
        self.assertEqual(
            ParseToStatements("【阶乘】（那啥）咋整：整完了。"),
            [
                Statement(
                    STMT_FUNC_DEF,
                    (
                        identifier_token("阶乘"),
                        [identifier_token("那啥")],  # Formal parameters.
                        [],  # Function body.
                    ),
                )
            ],
        )

    def test_parsing_func_call_with_param(self):
        self.assertEqual(
            ParseToStatements("整【阶乘】（五）。"),
            [Statement(STMT_CALL, CallExpr("阶乘", [number_literal_expr(5)]))],
        )

    def test_var_assignment_from_var(self):
        self.assertEqual(
            translate_and_run("老张是活雷锋。\n老王是活雷锋。\n" "老张装250。\n老王装老张。\n嘀咕：老王。"), "250\n"
        )

    def test_assignment_to_array_element(self):
        self.assertEqual(
            translate_and_run(
                """
张家庄都是活雷锋。
张家庄来了个五。
张家庄的老大 装 张家庄的老大乘二。
嘀咕：张家庄。"""
            ),
            "「10」\n",
        )

    def test_increments(self):
        self.assertEqual(translate_and_run("老张是活雷锋。老张装二。老张走走。嘀咕：老张。"), "3\n")
        self.assertEqual(translate_and_run("老张是活雷锋。老张装三。老张走五步。嘀咕：老张。"), "8\n")
        self.assertEqual(
            translate_and_run(
                """
张家庄都是活雷锋。
张家庄来了个二。
张家庄的老大走走。
嘀咕：张家庄的老大。
张家庄的老大走五步。
嘀咕：张家庄的老大。
"""
            ),
            """3
8
""",
        )

    def test_decrements(self):
        self.assertEqual(translate_and_run("老张是活雷锋。老张装二。老张稍稍。嘀咕：老张。"), "1\n")
        self.assertEqual(translate_and_run("老张是活雷锋。老张装三。老张稍五步。嘀咕：老张。"), "-2\n")
        self.assertEqual(
            translate_and_run(
                """
张家庄都是活雷锋。
张家庄来了个二。
张家庄的老大稍稍。
嘀咕：张家庄的老大。
张家庄的老大稍五步。
嘀咕：张家庄的老大。
"""
            ),
            """1
-4
""",
        )

    def test_loop(self):
        self.assertEqual(translate_and_run("老张从1到3磨叽：嘀咕：老张。磨叽完了。"), "1\n2\n3\n")

    def test_range_loop(self):
        self.assertEqual(
            translate_and_run(
                """
张家庄都是活雷锋。
张家庄来了个二。
张家庄来了个五。
张家庄来了个一。
老张在张家庄磨叽：
  嘀咕：老张。
磨叽完了。
"""
            ),
            """2
5
1
""",
        )

    def test_loop_with_no_statement(self):
        self.assertEqual(translate_and_run("老张从1到2磨叽：磨叽完了。"), "")

    def test_loop_with_multiple_statements(self):
        self.assertEqual(
            translate_and_run("老张从1到2磨叽：嘀咕：老张。嘀咕：老张加一。磨叽完了。"), "1\n2\n2\n3\n"
        )

    def test_loop_with_continue_and_break(self):
        self.assertEqual(
            translate_and_run(
                """
老张从一到十磨叽：
  寻思：老张跟二一样一样的？
  要行咧就接着磨叽。
  嘀咕：“老张是”、老张。
  寻思：老张比五还大？
  要行咧就尥蹶子。
磨叽完了。
"""
            ),
            """老张是1
老张是3
老张是4
老张是5
老张是6
""",
        )

    def test_infinite_loop(self):
        self.assertEqual(
            translate_and_run(
                """
老王装一。
老张从一而终磨叽：
嘀咕：老张、“和”、老王。
老王装老王加一。
寻思：老王比三还大？
要行咧就尥蹶子。
磨叽完了。
"""
            ),
            """1和1
1和2
1和3
""",
        )

    def test_infinite_loop_egg(self):
        self.assertEqual(
            translate_and_run(
                """
老王装一。
老张在苹果总部磨叽：
嘀咕：老张、“和”、老王。
老王装老王加一。
寻思：老王比三还大？
要行咧就尥蹶子。
磨叽完了。
"""
            ),
            """1和1
1和2
1和3
""",
        )

    def test_loop_with_composite_variable(self):
        self.assertEqual(
            translate_and_run(
                """
张家庄都是活雷锋。
张家庄来了个二。
张家庄的老大从一到三磨叽：
嘀咕：张家庄。
磨叽完了。
"""
            ),
            """「1」
「2」
「3」
""",
        )
        self.assertEqual(
            translate_and_run(
                """
张家庄都是活雷锋。
张家庄来了个二。
李家村都是活雷锋。
李家村来了个三。
李家村来了个五。
李家村来了个250。
张家庄的老大在李家村磨叽：
嘀咕：张家庄。
磨叽完了。
"""
            ),
            """「3」
「5」
「250」
""",
        )
        self.assertEqual(
            translate_and_run(
                """
张家庄都是活雷锋。
张家庄来了个二。
张家庄的老大从一而终磨叽：
嘀咕：张家庄。
尥蹶子。
磨叽完了。
"""
            ),
            """「1」
""",
        )
        self.assertEqual(
            translate_and_run(
                """
张家庄都是活雷锋。
张家庄来了个二。
张家庄的老大在苹果总部磨叽：
嘀咕：张家庄。
尥蹶子。
磨叽完了。
"""
            ),
            """「1」
""",
        )

    def test_print_bool(self):
        self.assertEqual(translate_and_run("老王是活雷锋。嘀咕：老王。嘀咕：老王啥也不是。"), "啥也不是\n没毛病\n")
        self.assertEqual(translate_and_run("嘀咕：五比二还大。"), "没毛病\n")
        self.assertEqual(
            translate_and_run("嘀咕：五比二还大、五比二还小、一跟2一样一样的、1跟二不是一样一样的。"), "没毛病有毛病有毛病没毛病\n"
        )

    def test_assert(self):
        self.assertEqual(translate_and_run("""保准三加二比五减一还大。"""), "")
        self.assertEqual(
            translate_and_run("""保准三加二比五减一还小。"""),
            """
整叉劈了：该着 3加2比5减1还小，咋有毛病了咧？
""",
        )
        self.assertEqual(
            translate_and_run("""辟谣三加二比五减一还大。"""),
            """
整叉劈了：3加2比5减1还大 不应该啊，咋有毛病了咧？
""",
        )
        self.assertEqual(translate_and_run("""辟谣三加二比五减一还小。"""), "")

    def test_raise(self):
        self.assertEqual(
            translate_and_run("""整叉劈了：“小朋友请回避！”。"""),
            """
整叉劈了：小朋友请回避！
""",
        )
        self.assertEqual(
            translate_and_run("""小王装2。整叉劈了：小王、“小朋友请回避！”。"""),
            """
整叉劈了：2小朋友请回避！
""",
        )

    def test_bang_narrow(self):
        self.assertEqual(translate_and_run("老王是活雷锋!老王装二!嘀咕：老王!"), "2\n")

    def test_delete(self):
        self.assertEqual(translate_and_run("老王是活雷锋。老王装二。削老王！嘀咕：老王。"), "啥也不是\n")
        self.assertEqual(
            translate_and_run(
                """
张家庄都是活雷锋。
张家庄来了个二。
张家庄来了个三。
削张家庄的老大！
嘀咕：张家庄。
"""
            ),
            "「啥也不是, 3」\n",
        )

    def test_number_literal(self):
        self.assertEqual(translate_and_run("嘀咕：零。"), "0\n")
        self.assertEqual(translate_and_run("嘀咕：鸭蛋。"), "0\n")
        self.assertEqual(translate_and_run("嘀咕：一。"), "1\n")
        self.assertEqual(translate_and_run("嘀咕：二。"), "2\n")
        self.assertEqual(translate_and_run("嘀咕：两。"), "2\n")
        self.assertEqual(translate_and_run("嘀咕：俩。"), "2\n")
        self.assertEqual(translate_and_run("嘀咕：三。"), "3\n")
        self.assertEqual(translate_and_run("嘀咕：仨。"), "3\n")
        self.assertEqual(translate_and_run("嘀咕：四。"), "4\n")
        self.assertEqual(translate_and_run("嘀咕：五。"), "5\n")
        self.assertEqual(translate_and_run("嘀咕：六。"), "6\n")
        self.assertEqual(translate_and_run("嘀咕：七。"), "7\n")
        self.assertEqual(translate_and_run("嘀咕：八。"), "8\n")
        self.assertEqual(translate_and_run("嘀咕：九。"), "9\n")
        self.assertEqual(translate_and_run("嘀咕：十。"), "10\n")
        self.assertEqual(translate_and_run("嘀咕：-10.5。"), "-10.5\n")
        self.assertEqual(translate_and_run("嘀咕：5.。"), "5.0\n")
        self.assertEqual(translate_and_run("嘀咕：-10。"), "-10\n")
        self.assertEqual(translate_and_run("嘀咕：拉饥荒十。"), "-10\n")
        self.assertEqual(translate_and_run("嘀咕：拉饥荒零。"), "0\n")

    def test_arithmetic(self):
        self.assertEqual(translate_and_run("嘀咕：五加二。"), "7\n")
        self.assertEqual(translate_and_run("嘀咕：五减二。"), "3\n")
        self.assertEqual(translate_and_run("嘀咕：五乘二。"), "10\n")
        self.assertEqual(translate_and_run("嘀咕：十除以二。"), "5.0\n")
        self.assertEqual(translate_and_run("嘀咕：十齐整整地除以三。"), "3\n")
        self.assertEqual(translate_and_run("嘀咕：十刨掉一堆堆三。"), "1\n")
        self.assertEqual(translate_and_run("嘀咕：十刨掉一堆堆五。"), "0\n")
        self.assertEqual(translate_and_run("嘀咕：五加七乘二。"), "19\n")
        self.assertEqual(translate_and_run("嘀咕：（五加七）乘二。"), "24\n")
        self.assertEqual(translate_and_run("嘀咕：(五加七)乘二。"), "24\n")
        self.assertEqual(translate_and_run("嘀咕：(五减（四减三）)乘二。"), "8\n")
        self.assertEqual(translate_and_run("嘀咕：拉饥荒（五加二）。"), "-7\n")
        self.assertEqual(
            translate_and_run(
                """
      张家庄都是活雷锋。
      张家庄来了个42。
      嘀咕：拉饥荒张家庄的老大。
      """
            ),
            "-42\n",
        )

    def test_concat(self):
        self.assertEqual(translate_and_run("嘀咕：“牛”、二。"), "牛2\n")
        self.assertEqual(translate_and_run("嘀咕：“老王”、665加一。"), "老王666\n")

    def test_compound(self):
        self.assertEqual(translate_and_run("开整：整完了。"), "")
        self.assertEqual(translate_and_run("开整：嘀咕：1。整完了。"), "1\n")
        self.assertEqual(translate_and_run("开整：嘀咕：1。嘀咕：2。整完了。"), "1\n2\n")

    def test_run_conditional(self):
        self.assertEqual(translate_and_run("寻思：5比2还大？要行咧就嘀咕：“OK”。"), "OK\n")
        self.assertEqual(translate_and_run("寻思：5比2还大？要行咧就开整：\n" "整完了。"), "")
        self.assertEqual(
            translate_and_run("寻思：5比2还大？\n" "要行咧就开整：\n" "    嘀咕：5。\n" "整完了。"), "5\n"
        )
        self.assertEqual(
            translate_and_run("寻思：5比6还大？要行咧就嘀咕：“OK”。\n" "要不行咧就嘀咕：“不OK”。"), "不OK\n"
        )
        self.assertEqual(
            translate_and_run(
                "寻思：5比6还大？\n"
                "要行咧就嘀咕：“OK”。\n"
                "要不行咧就开整：\n"
                "  嘀咕：“不OK”。\n"
                "  嘀咕：“还是不OK”。\n"
                "整完了。"
            ),
            "不OK\n还是不OK\n",
        )
        # Else should match the last If.
        self.assertEqual(
            translate_and_run(
                """
          寻思：2比1还大？   # condition 1: True
          要行咧就寻思：2比3还大？  # condition 2: False
              要行咧就嘀咕：“A”。  # for condition 2
              要不行咧就嘀咕：“B”。# for condition 2
          """
            ),
            "B\n",
        )

    def test_run_func(self):
        self.assertEqual(translate_and_run("埋汰咋整：嘀咕：“你虎了吧唧”。整完了。"), "")
        self.assertEqual(translate_and_run("埋汰咋整：嘀咕：“你虎了吧唧”。整完了。整埋汰。"), "你虎了吧唧\n")

    def test_func_call_with_param(self):
        self.assertEqual(
            translate_and_run("【加一】（那啥）咋整：嘀咕：那啥加一。整完了。\n" "整【加一】（五）。"), "6\n"
        )

    def test_func_with_return_value(self):
        self.assertEqual(
            translate_and_run("【加一】（那啥）咋整：滚犊子吧那啥加一。整完了。\n" "嘀咕：整【加一】（二）。"), "3\n"
        )

    def test_nested_func(self):
        self.assertEqual(
            translate_and_run(
                """
写三三表咋整：
  老王从一到三磨叽：
    王三表咋整：  # 定义一个套在“写三三表”套路里的套路。
      老张从老王到三磨叽：  # 内层套路可以引用外层套路的活雷锋。
        嘀咕：老王、“*”、老张、“=”、老王乘老张。
      磨叽完了。
    整完了。  # 内层套路定义结束。
    整王三表。  # 使用内层套路。
  磨叽完了。
整完了。

整写三三表。"""
            ),
            """1*1=1
1*2=2
1*3=3
2*2=4
2*3=6
3*3=9
""",
        )

    def test_array(self):
        self.assertEqual(
            translate_and_run(
                """
张家庄都是活雷锋。  # 张家庄是个群众变量。初始值是「」。
嘀咕：张家庄。
张家庄来了个二加三。  # 张家庄现在 = 「5」。
嘀咕：张家庄。
张家庄来了个“大”。   # 张家庄现在 = 「5, '大'」
嘀咕：张家庄。
嘀咕：张家庄有几个坑。
嘀咕：张家庄的老大。  # 第一个人（5）。
嘀咕：张家庄的老（三减一）。  # 第二个人（'大'）。
嘀咕：张家庄的老幺。  # 最后一个人（'大'）。
李家村都是活雷锋。  # 李家村也是个群众变量。初始值是「」。
李家村来了个三。  # 李家村现在 = 「3」。
李家村来了个张家庄。  # 群众的一个元素本身可以是群众。李家村现在 = 「3, 「5, '大'」」。
嘀咕：李家村。
嘀咕：李家村的老幺的老大。  # 5。
削张家庄。  # 张家庄现在啥也不是。
嘀咕：张家庄。
"""
            ),
            """「」
「5」
「5, '大'」
2
5
大
大
「3, 「5, '大'」」
5
啥也不是
""",
        )

    def test_nested_array(self):
        self.assertEqual(
            translate_and_run(
                """
      张家庄 装 「「一，二」，「三」」。
      嘀咕：张家庄的老二的老大。
      """
            ),
            """3
""",
        )

    def test_sub_list(self):
        self.assertEqual(
            translate_and_run(
                """
张家庄都是活雷锋。
张家庄来了个三。
张家庄来了个五。
张家庄来了个六。
嘀咕：张家庄掐头。
嘀咕：张家庄去尾。
嘀咕：张家庄。
"""
            ),
            """「5, 6」
「3, 5」
「3, 5, 6」
""",
        )

    def test_array_append(self):
        self.assertEqual(
            translate_and_run(
                """
张家庄都是活雷锋。  # 「」
李家村都是活雷锋。  # 「」
李家村来了个张家庄。  # 「「」」
李家村的老大来了个五。  # 「「5」」
嘀咕：张家庄。
嘀咕：李家村。
"""
            ),
            """「5」
「「5」」
""",
        )

    def test_array_extend(self):
        self.assertEqual(
            translate_and_run(
                """
张家庄都是活雷锋。  # 「」
李家村都是活雷锋。  # 「」
李家村来了个二。  # 「2」
李家村来了个五。  # 「2, 5」
张家庄来了群李家村。 # 「2, 5」
张家庄来了群李家村。 # 「2, 5, 2, 5」
嘀咕：张家庄。
"""
            ),
            """「2, 5, 2, 5」
""",
        )

    def test_array_literal(self):
        self.assertEqual(
            translate_and_run(
                """
        张家庄 装 「」。
        嘀咕：张家庄。
      """
            ),
            "「」\n",
        )
        self.assertEqual(
            translate_and_run(
                """
        张家庄 装 路银「」。
        嘀咕：张家庄。
      """
            ),
            "「」\n",
        )
        self.assertEqual(
            translate_and_run(
                """
        张家庄 装 「1，二加三，五减一」。
        嘀咕：张家庄。
      """
            ),
            "「1, 5, 4」\n",
        )
        self.assertEqual(
            translate_and_run(
                """
        张家庄 都是活雷锋。
        张家庄 来了群 「1，二加三，五减一」。
        嘀咕：张家庄。
        张家庄 来了群 「」。
        嘀咕：张家庄。
        张家庄 来了群路银 「7，8」。
        嘀咕：张家庄。
      """
            ),
            """「1, 5, 4」
「1, 5, 4」
「1, 5, 4, 7, 8」
""",
        )

    def test_del(self):
        self.assertTrue(
            "整叉劈了"
            in translate_and_run(
                """
老王是活雷锋。
炮决老王。
嘀咕：老王。
"""
            )
        )
        self.assertEqual(
            translate_and_run(
                """
张家庄都是活雷锋。
张家庄来了个五。
张家庄来了个六。
炮决张家庄的老大。
嘀咕：张家庄。
"""
            ),
            """「6」
""",
        )

    def test_recursive_func(self):
        self.assertEqual(
            translate_and_run(
                """
【阶乘】（那啥）咋整：
寻思：那啥比一还小？
要行咧就滚犊子吧一。
滚犊子吧那啥乘整【阶乘】（那啥减一）。
整完了。

嘀咕：整【阶乘】（五）。
        """
            ),
            "120\n",
        )

    def test_multi_arg_func(self):
        self.assertEqual(
            translate_and_run(
                """
求和（甲，乙）咋整：
  滚犊子吧 甲加乙。
整完了。

嘀咕：整求和（五，七）。
        """
            ),
            "12\n",
        )
        self.assertEqual(
            translate_and_run(
                """
求和（甲，乙）咋整：
  嘀咕：甲加乙。
整完了。

整求和（五，七）。
        """
            ),
            "12\n",
        )

    def test_normalizing_bang(self):
        self.assertEqual(
            translate_and_run("【加一】（那啥）咋整：嘀咕：那啥加一！整完了！\n" "整【加一】（五）！"), "6\n"
        )

    def test_import(self):
        self.assertEqual(
            translate_and_run(
                """
      翠花，上 re。
      寻思：整re.match（“a.*”，“abc”）？
      要行咧就嘀咕：“OK”。
      """
            ),
            "OK\n",
        )

    def test_command_line(self):
        with patch("sys.argv", ["dongbei_test.py", "arg1"]):
            self.assertTrue("dongbei_test.py" in translate_and_run("""嘀咕：最高指示。"""))

    def test_class_def(self):
        self.assertEqual(
            TranslateDongbeiToPython(
                """
      无产阶级的接班银Foo阶级咋整：
      整完了。
      """,
                None,
            ),
            """class Foo:
  pass""",
        )
        self.assertEqual(
            TranslateDongbeiToPython(
                """
      Xyz阶级的接班银Foo阶级咋整：
      整完了。
      """,
                None,
            ),
            """class Foo(Xyz):
  pass""",
        )

    def test_ctor_def(self):
        self.assertEqual(
            TranslateDongbeiToPython(
                """
      无产阶级的接班银有名阶级咋整：
        新对象咋整：
        整完了。
      整完了。
      """,
                None,
            ),
            """class 有名:

  def __init__(self):
    pass""",
        )

        self.assertEqual(
            TranslateDongbeiToPython(
                """
      有名阶级的接班银特有名阶级咋整：
        新对象（名字）咋整：
          俺的名字装名字。
        整完了。
      整完了。
      """,
                None,
            ),
            """class 特有名(有名):

  def __init__(self, 名字):
    (self).名字 = 名字""",
        )

    def test_ctor_call(self):
        self.assertEqual(
            translate_and_run(
                """
      无产阶级的接班银有名阶级咋整：
        新对象咋整：
          俺的名字装“无名”。
        整完了。
      整完了。

      老林 装 有名 的新对象。
      嘀咕：老林的名字。
      """
            ),
            """无名
""",
        )
        self.assertEqual(
            translate_and_run(
                """
      无产阶级的接班银有名阶级咋整：
        新对象（名字）咋整：
          俺的名字装名字。
        整完了。
      整完了。

      老林 装 有名 的新对象（“林蛋大”）。
      嘀咕：老林的名字。
      """
            ),
            """林蛋大
""",
        )

    def test_call_base_ctor(self):
        self.assertEqual(
            translate_and_run(
                """
无产 阶级的接班银 有名 阶级咋整：
  新对象（名字）咋整：
    俺的名字 装 名字。
  整完了。
整完了。

有名 阶级的接班银 特有名 阶级咋整：
  新对象咋整：
    整 领导的新对象（“赵英俊”）。
    俺的 年龄 装 25。
  整完了。
整完了。

老赵 装 特有名 的新对象。
嘀咕：老赵 的 名字。
嘀咕：老赵 的 年龄。 
      """
            ),
            """赵英俊
25
""",
        )
        self.assertEqual(
            translate_and_run(
                """
无产 阶级的接班银 有名 阶级咋整：
  新对象咋整：
    俺的名字 装 “有名”。
  整完了。
整完了。

有名 阶级的接班银 特有名 阶级咋整：
  新对象咋整：
    整 领导的新对象。
  整完了。
整完了。

老赵 装 特有名 的新对象。
嘀咕：老赵 的 名字。
      """
            ),
            """有名
""",
        )

    def test_class_method(self):
        # Calling a method in an expression.
        self.assertEqual(
            translate_and_run(
                """
无产 阶级的接班银 有名 阶级咋整：
  新对象（名字）咋整：
    俺的名字 装 名字。
  整完了。

  显呗咋整：
    嘀咕：“我你都不认识啊？我是那啥”、俺的名字、“！”。
    滚犊子吧 俺的名字！
  整完了。
整完了。

老赵 装 有名 的新对象（“赵英俊”）。
嘀咕：老赵 整 显呗。 
      """
            ),
            """我你都不认识啊？我是那啥赵英俊！
赵英俊
""",
        )
        # Calling a method in a statement.
        self.assertEqual(
            translate_and_run(
                """
无产 阶级的接班银 有名 阶级咋整：
  新对象（名字）咋整：
    俺的名字 装 名字。
  整完了。

  显呗咋整：
    嘀咕：“我你都不认识啊？我是那啥”、俺的名字、“！”。
    滚犊子吧 俺的名字！
  整完了。
整完了。

老赵 装 有名 的新对象（“赵英俊”）。
老赵 整 显呗。 
      """
            ),
            """我你都不认识啊？我是那啥赵英俊！
""",
        )

    def test_bool_literal(self):
        self.assertEqual(
            translate_and_run(
                """
      老王 装 没毛病。
      寻思：老王？
      要行咧就 嘀咕：“老王没毛病！”。
      """
            ),
            """老王没毛病！
""",
        )
        self.assertEqual(
            translate_and_run(
                """
      老王 装 有毛病。
      寻思：老王？
      要行咧就 嘀咕：“老王没毛病！”。
      要不行咧就 嘀咕：“老王有毛病！”。
      """
            ),
            """老王有毛病！
""",
        )

    def test_none_literal(self):
        self.assertEqual(
            translate_and_run(
                """
      老王 装 啥也不是。
      嘀咕：老王。
      寻思：老王？
      要行咧就 嘀咕：“老王没毛病！”。
      要不行咧就 嘀咕：“老王有毛病！”。
      """
            ),
            """啥也不是
老王有毛病！
""",
        )

    def test_tuple(self):
        self.assertEqual(
            translate_and_run(
                """
      老王装抱团。
      嘀咕：老王。
      """
            ),
            """（抱团）
""",
        )
        self.assertEqual(
            translate_and_run(
                """
      老王装三加一抱团。
      嘀咕：老王。
      """
            ),
            """（4抱团）
""",
        )
        self.assertEqual(
            translate_and_run(
                """
      老王装 四 跟 五 抱团。
      嘀咕：老王。
      """
            ),
            """（4跟5抱团）
""",
        )
        self.assertEqual(
            translate_and_run(
                """
      老王装 四 跟 五 跟 七 抱团。
      嘀咕：老王。
      """
            ),
            """（4跟5跟7抱团）
""",
        )
        self.assertEqual(
            translate_and_run(
                """
      老王装 四 跟 五跟二一样一样的 抱团。
      嘀咕：老王。
      """
            ),
            """（4跟有毛病抱团）
""",
        )
        self.assertEqual(
            translate_and_run(
                """
      老王装 五减一 跟 五跟二一样一样的 抱团。
      嘀咕：老王。
      """
            ),
            """（4跟有毛病抱团）
""",
        )
        self.assertEqual(
            translate_and_run(
                """
      老王装 五减一 跟 五跟二一样一样的 跟 七跟七一样一样的 抱团。
      嘀咕：老王。
      """
            ),
            """（4跟有毛病跟没毛病抱团）
""",
        )
        self.assertEqual(
            translate_and_run(
                """
      老王 装 五减一 跟 五跟二一样一样的 抱团。
      老张 装 老王的老大。
      老李 装 老王的老二。
      嘀咕：老王。
      嘀咕：老王 有几个坑。
      嘀咕：老张。
      嘀咕：老李。
      """
            ),
            """（4跟有毛病抱团）
2
4
有毛病
""",
        )

    @patch("src.dongbei.get_input")
    def test_repl_terminator1(self, mock_input):
        mock_input.return_value = "瞅你咋地"
        self.assertEqual([], list(dongbei.repl()))

    @patch("src.dongbei.get_input")
    def test_repl_terminator2(self, mock_input):
        mock_input.return_value = "瞅你咋的"
        self.assertEqual([], list(dongbei.repl()))

    @patch("src.dongbei.get_input")
    def test_repl_terminator3(self, mock_input):
        mock_input.return_value = "瞅你咋滴"
        self.assertEqual([], list(dongbei.repl()))

    @patch("src.dongbei.get_input")
    def test_repl_terminator4(self, mock_input):
        mock_input.return_value = "瞅你咋地？"
        self.assertEqual([], list(dongbei.repl()))

    @patch("src.dongbei.get_input")
    def test_repl_terminator5(self, mock_input):
        mock_input.return_value = "瞅你咋的?"
        self.assertEqual([], list(dongbei.repl()))

    @patch("src.dongbei.get_input")
    def test_repl_terminator3(self, mock_input):
        mock_input.return_value = "瞅你咋滴? "
        self.assertEqual([], list(dongbei.repl()))

    @patch("src.dongbei.get_input")
    def test_repl_one_line_statement(self, mock_input):
        mock_input.side_effect = ["嘀咕：“你干哈？”。", "瞅你咋地"]
        self.assertEqual(["你干哈？\n"], list(dongbei.repl()))

    @patch("src.dongbei.get_input")
    def test_repl_two_line_statement(self, mock_input):
        mock_input.side_effect = ["嘀咕：\\", "“你干哈？”。", "瞅你咋地"]
        self.assertEqual(["你干哈？\n"], list(dongbei.repl()))

    @patch("src.dongbei.get_input")
    def test_repl_multiple_statements(self, mock_input):
        mock_input.side_effect = ["老王装二。", "嘀咕：老王。", "嘀咕：\\", "“你干哈？”。", "瞅你咋地"]
        self.assertEqual(["", "2\n", "你干哈？\n"], list(dongbei.repl()))

    @patch("src.dongbei.get_input")
    def test_repl_expression(self, mock_input):
        mock_input.side_effect = ["二", "瞅你咋地"]
        self.assertEqual(["2\n"], list(dongbei.repl()))


class DongbeiTokenizerRecursionTest(unittest.TestCase):
    def test_tokenize_large_input(self):
        # BasicTokenize recurses once per token; Python's default limit is ~1000.
        # A program with 1000+ tokens should not raise RecursionError.
        code = ("老王是活雷锋。\n" * 400)  # 400 statements * ~3 tokens each ≈ 1200 tokens
        try:
            translate_and_run(code)
        except RecursionError:
            self.fail("BasicTokenize hit Python recursion limit on large input")


class DongbeiSourceLocTest(unittest.TestCase):
    """Verify that source locations survive the Lark transformer.

    Each test picks a string where the operator keyword is NOT at column 0,
    so a wrong loc (the dummy _loc() default of <unknown>:1:0) is distinguishable
    from the correct one.
    """

    def test_arithmetic_op_loc(self):
        # "五加老王": 五 at col 0, 加 at col 1 (KW_PLUS).
        expr = ParseExprFromStr("五加老王")
        self.assertEqual(expr.operation.loc, SourceLoc("<unknown>", 1, 1))

    def test_comparison_eq_loc(self):
        # "五跟老王一样一样的": 一样一样的 starts at col 4 (after 五跟老王).
        expr = ParseExprFromStr("五跟老王一样一样的")
        self.assertEqual(expr.relation.loc, SourceLoc("<unknown>", 1, 4))

    def test_comparison_is_none_loc(self):
        # "老王啥也不是": 啥也不是 starts at col 2 (after 老王).
        expr = ParseExprFromStr("老王啥也不是")
        self.assertEqual(expr.relation.loc, SourceLoc("<unknown>", 1, 2))

    def test_op_loc_with_filename(self):
        # When tokenized with a named source file, operator loc carries the filename.
        parser = DongbeiParser()
        tokens = parser.tokenize("五加老王", "foo.dongbei")
        tree = dongbei._lark_parser.parse(tokens, start="start_expr")
        expr = dongbei._lark_transformer.transform(tree)
        self.assertEqual(expr.operation.loc, SourceLoc("foo.dongbei", 1, 1))

    def test_op_loc_on_line2(self):
        # 加 is on line 2 (preceded by newline after 五 on line 1).
        expr = ParseExprFromStr("五\n加老王")
        self.assertEqual(expr.operation.loc, SourceLoc("<unknown>", 2, 0))

    def test_number_literal_loc_after_op(self):
        # In "五加六": 五 at col 0, 加 at col 1, 六 at col 2.
        expr = ParseExprFromStr("五加六")
        self.assertEqual(expr.op2.token.loc, SourceLoc("<unknown>", 1, 2))

    def test_identifier_loc_after_keyword(self):
        # In "翠花，上random。": KW_IMPORT spans cols 0-3, so random starts at col 4.
        stmt = ParseStmtFromStr("翠花，上random。")
        self.assertEqual(stmt.value.loc, SourceLoc("<unknown>", 1, 4))


if __name__ == "__main__":
    unittest.main()
