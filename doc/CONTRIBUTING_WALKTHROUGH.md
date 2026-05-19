# dongbei 代码导读：老铁，咱整起来！

> 这份文档专门写给想往 dongbei 里掺和一脚的新来的老铁。
> 看完这篇，你就能明白这个解释器是咋运转的，也知道咋加新特性、咋改 bug、咋跑测试。
> 全程用东北话，看不懂了就多念两遍，保管你明白过来。

---

## 目录

1. [大哥，你来了！](#大哥你来了)
2. [从源文件到屏幕：大水管走一遭](#从源文件到屏幕大水管走一遭)
3. [关键字大军：KW_* 和 KEYWORDS 元组](#关键字大军kw_-和-keywords-元组)
4. [分词：tokenize() 掰豆腐记](#分词tokenize-掰豆腐记)
5. [语法树：Lark 和 _DongbeiTransformer](#语法树lark-和-_dongbeitransformer)
6. [代码生成：translate_statement_to_python()](#代码生成translate_statement_to_python)
7. [手把手：加一个新关键字](#手把手加一个新关键字)
8. [加新的表达式](#加新的表达式)
9. [跑测试：别给自己挖坑](#跑测试别给自己挖坑)
10. [彩蛋和隐藏机关](#彩蛋和隐藏机关)
11. [整一个 PR 要注意啥](#整一个-pr-要注意啥)

---

## 大哥，你来了！

老铁，你既然翻到这儿来了，说明你是真有两下子，或者你是真闲得慌。不管哪个，都欢迎！

dongbei 是一门以东北方言词汇为关键字的编程语言，底下全是 Python 撑着。你在 `.dongbei` 文件里用大碴子话写代码，解释器把它翻成 Python，再跑起来。就这么个事儿。

**你得会啥：** Python 3 基本操作就够。不需要学过编译原理，不需要懂 Earley 文法，我这儿都给你解释明白。

**代码都在哪儿：**

```
src/        ← 唯一的源文件：dongbei.py（约 2100 行，整个解释器都在这儿）
            也有 dongbei.dongbei（用东北话写的东北话解释器，套娃）
test/       ← 测试（dongbei_test.py + dongbei_add_test.py + test_all 脚本）
demo/       ← 28 个 .dongbei 示例程序（斐波那契、汉诺塔、快速排序……）
doc/        ← 文档（cheatsheet、本文档……）
```

**先把环境整好：**

```bash
pip install -r requirements.txt
bash test/test_all          # 全绿了才算整好了
```

`test_all` 跑所有单元测试，还会把 `demo/` 里每个 `.dongbei` 文件都跑一遍。要是有一个没过，那就是哪儿有问题，得先查清楚再继续。

---

## 从源文件到屏幕：大水管走一遭

整个解释器是一根大水管——源码进去，输出出来，中间经过四个环节。这四个环节你得先有个印象，后面细说。

```
.dongbei 源码
    │
    ▼  tokenize()                         ← 分词：把大碴子话切成一个个 Token
    ▼  translate_tokens_to_statements()   ← 建树：Lark 把 Token 列表变成语法树
    ▼  translate_statement_to_python()    ← 翻译：把语法树每个节点变成 Python 字符串
    ▼  exec()                             ← 执行：Python 你来吧！
```

整个流程的入口是 `translate_and_run()`，它就把这四步串起来了：

```python
def translate_and_run(dongbei_code, src_file, xudao=False):
    py_code = translate_dongbei_to_python(dongbei_code, src_file, xudao=xudao)
    return run_py_code(py_code)
```

咱用最简单的一句话追一遍这四步，你就明白了。源码：

```
嘀咕："唉呀，这嘎哒真好！"。
```

**第一步，分词** — `tokenize()` 把这串字符切成 Token 列表：

```
KEYWORD <"嘀咕"> @ 1:0
KEYWORD <"："> @ 1:2
KEYWORD <"""> @ 1:3
STRING_LITERAL <"唉呀，这嘎哒真好！"> @ 1:4
KEYWORD <"""> @ 1:13
KEYWORD <"。"> @ 1:14
```

**第二步，建树** — Lark 语法分析器认出这是一条 `say_stmt`，`_DongbeiTransformer` 把它变成一个 Statement 对象：

```
Statement(kind=STMT_SAY, value=LiteralExpr("唉呀，这嘎哒真好！"))
```

**第三步，翻译** — `translate_statement_to_python()` 看到 `STMT_SAY`，生成：

```python
_dongbei_print("唉呀，这嘎哒真好！")
```

**第四步，执行** — `exec()` 跑这行 Python，`_dongbei_print()` 往屏幕和输出缓冲区一起打印：

```
唉呀，这嘎哒真好！
```

就这四步，所有的 dongbei 程序都是这么过来的。

**调试神器 `--xudao`：** 要是你想亲眼瞅瞅生成了啥 Python 代码，就加上这个参数：

```bash
src/dongbei.py --xudao 你的文件.dongbei
```

它会在执行前把翻译出来的 Python 代码哗哗地打出来。改代码的时候这东西特别好用。

---

## 关键字大军：KW_* 和 KEYWORDS 元组

dongbei 的关键字系统由两部分组成，缺一不可。

### 一、KW_* 常量

每个关键字都有一个 Python 常量，比如：

```python
KW_SAY_DIGU = "嘀咕"
KW_BECOME    = "装"
KW_END       = "整完了"
KW_CALL      = "整"
KW_PERIOD    = "。"
```

这么做的好处是：哪天你想改某个关键字的写法，只改这一个地方就够了，其他代码全部引用这个常量，不用到处翻。一个萝卜一个坑。

### 二、KEYWORDS 元组

这个元组把所有关键字**按顺序**排列，分词器就按这个顺序挨个儿尝试匹配。顺序不是随便排的——**长的先，短的后；具体的先，模糊的后**。

这是因为分词器是"贪心匹配"：遇到一段源码，从 KEYWORDS 里挨个试，第一个能匹配上的就算。要是先试短的，就会把长关键字的前缀先截走，后面剩的一坨垃圾就没法解析了。

源码里的注释把冲突写得明明白白：

| 必须先匹配 | 后匹配 | 原因 |
|---|---|---|
| `整完了` (KW_END) | `整` (KW_CALL) | `整完了` 开头是 `整`，要是先匹配 `整`，`完了` 就成野字了 |
| `整叉劈了：` (KW_RAISE) | `整` (KW_CALL) | 同上 |
| `从一而终磨叽：` (KW_1_INFINITE_LOOP) | `从` (KW_FROM) | `从一而终磨叽：` 开头是 `从` |
| `在苹果总部磨叽：` (KW_1_INFINITE_LOOP_EGG) | `在` (KW_IN) | 彩蛋，后面细说 |
| `的老大` → `的老幺` → `的老` → `的新对象` → `的` | — | 五层都是 `的` 开头，从长到短排 |

你要是加了新关键字，第一件事就是检查：它跟已有的哪个关键字有前缀重叠？有重叠的话，长的必须排前面。

### 三、规范化映射（KEYWORD_TO_NORMALIZED_KEYWORD）

东北人打字有时候用窄标点（半角），有时候用宽标点（全角）。这个字典把它们统一：

```python
KEYWORD_TO_NORMALIZED_KEYWORD = {
    KW_BANG: KW_PERIOD,          # "!" → "。"
    KW_BANG_NARROW: KW_PERIOD,   # "!" → "。"
    KW_OPEN_PAREN_NARROW: KW_OPEN_PAREN,  # "(" → "（"
    ...
    KW_SAY: KW_SAY_DIGU,         # "唠唠" → "嘀咕"（两种说法都行）
}
```

分词器匹配到别名之后，马上换成规范形式，后续代码只见规范形式，不用操心变体。

---

## 分词：tokenize() 掰豆腐记

东北话分词就像在市场买豆腐——豆腐这一大坨，你得自己知道往哪儿切。中文没有空格分隔词语，分词器得靠关键字表来切。

### 位置追踪

在开始分词之前，解释器准备好两个工具：

- **`SourceLoc`**：记录当前扫描位置（文件路径、行号、列号）。出错时告诉你哪行哪列出了问题。
- **`SourceCodeAndLoc`**：把源码字符串和 `SourceLoc` 绑在一起，提供逐字符推进的方法。

### Token 的结构

每个 Token 有三个字段：

```python
class Token:
    kind   # TK_KEYWORD / TK_IDENTIFIER / TK_STRING_LITERAL / TK_NUMBER_LITERAL / TK_CHAR
    value  # 实际的字符串内容
    loc    # SourceLoc（出错时定位用）
```

打印出来长这样：`KEYWORD <'嘀咕'> @ 文件.dongbei:1:0`

五种 Token 类型：
- `TK_KEYWORD`：关键字，比如 `嘀咕`、`装`、`。`
- `TK_IDENTIFIER`：变量名，用【方括号】括起来，比如 `【老王】`
- `TK_STRING_LITERAL`：字符串，比如 `"唉呀！"`
- `TK_NUMBER_LITERAL`：数字，比如 `二`、`42`
- `TK_CHAR`：上面都不是的单个字符，暂存着，后面再拼

### 主循环：basic_tokenize()

这是分词的心脏。每次循环处理一小段源码：

1. **跳过空白和注释**（`skip_whitespace_and_comment()`）
2. **试试是不是 `【标识符】`**：用正则匹配 `【…】`，内部空白被忽略，`【老  王】` 和 `【老王】` 是同一个标识符。
3. **挨个试 KEYWORDS**：按顺序对每个关键字调用 `try_parse_keyword()`，第一个匹配上就用它，跳出循环。
4. **都不是就发出 TK_CHAR**：吃掉一个字符，发一个 `TK_CHAR` 类型的 Token，留着后面拼数字或者识别符。

### try_parse_keyword() 的小心思

这个函数挺聪明的——它允许关键字内部有空白。比如 `嘀 咕` 和 `嘀咕` 都能匹配上 `KW_SAY_DIGU`。

做法是：遍历关键字字符串的每一个字符，每次尝试前先跳过空白，再检查当前源码是不是以该字符开头。匹配失败就回滚到尝试前的位置。

### 字符串字面量

遇到 `"` (`KW_OPEN_QUOTE`) 之后，控制权交给 `tokenize_string_literal_and_rest()`，它直接扫到下一个 `"` 为止，中间的内容原样变成 `TK_STRING_LITERAL`，关键字匹配在这段里完全不管用。这样 `"装"` 里的"装"就不会被当成赋值关键字。

### _tokenize()：拼接 TK_CHAR

`basic_tokenize()` 可能产生一串 `TK_CHAR`，比如 `老`、`王` 各一个。`_tokenize()` 把连续的 `TK_CHAR` 拼在一起，再交给 `tokenize_str_containing_no_keyword()` 识别成数字或者标识符。这是外部调用的公开入口：`tokenize(code, src_file)` → `_tokenize()` → `basic_tokenize()`。

### 具体追踪：`老王装二。`

这四个 Token 是咋来的：

| 源码片段 | 识别结果 |
|---|---|
| `老王` | 两个 TK_CHAR 拼在一起，识别为 `IDENTIFIER <老王>` |
| `装` | KEYWORDS 中 `KW_BECOME = "装"` 匹配，得到 `KEYWORD <装>` |
| `二` | TK_CHAR，`try_parse_number` 识别为 `NUMBER_LITERAL <2>` |
| `。` | KEYWORDS 中 `KW_PERIOD = "。"` 匹配，得到 `KEYWORD <。>` |

---

## 语法树：Lark 和 _DongbeiTransformer

Lark 就是咱们的语法裁缝，把一堆 Token（布料）按语法规则（样板）裁出语法树（衣服），然后 `_DongbeiTransformer` 这个老师傅把衣服改成咱想要的款式（AST 节点）。

### _DONGBEI_GRAMMAR

这是一个 Earley 文法，描述了 dongbei 语言的完整语法。摘几条关键规则：

```
?stmt: open_stmt | matched_stmt

?non_if_stmt:
    | _KW_SAY_DIGU _KW_COLON expr _KW_PERIOD       -> say_stmt
    | expr _KW_BECOME expr _KW_PERIOD               -> assign_stmt
    | expr _KW_FROM expr _KW_TO expr _KW_LOOP
        stmt* _KW_END_LOOP _KW_PERIOD               -> loop_stmt
    ...
```

规则名（`-> say_stmt`）直接对应 `_DongbeiTransformer` 里的同名方法。Lark 解析完了就调用对应方法，传入子节点列表。

**Terminal 命名约定**（见文法开头的注释）：
- `_KW_*`（下划线开头）：Lark 自动丢弃这些 token，不传给 Transformer。用于语法骨架（标点、关键字）。
- `KW_*`（无下划线）：保留，Transformer 能拿到，用于需要追踪源码位置的关键字（比如运算符）。
- `IDENTIFIER / NUMBER_LITERAL / STRING_LITERAL`：携带原始的 dongbei Token 作为 `.value`。

### _DongbeiLexer

Lark 需要一个词法器。`_DongbeiLexer` 把我们自己的 `Token` 列表包装成 Lark 能认的格式——把每个 dongbei Token 存到 `lark.Token.value` 里，Transformer 用 `_dk()` 解包出来：

```python
@staticmethod
def _dk(lark_tok):
    return lark_tok.value  # lark.Token → 原始 dongbei Token
```

### _DongbeiTransformer

每条语法规则对应一个方法。方法接收 `items`（子节点列表），返回一个 `Statement` 或 `Expr` 对象。

三个有代表性的例子：

**最简单的：`say_stmt`**

```python
def say_stmt(self, items):
    return Statement(STMT_SAY, items[0])
```

`items[0]` 就是 `expr` 解析出来的 `Expr` 对象，直接装进 Statement 的 `value`。

**稍微复杂的：`loop_stmt`**

```python
def loop_stmt(self, items):
    var_expr, from_expr, to_expr = items[0], items[1], items[2]
    stmts = list(items[3:])
    step_expr = number_literal_expr(1, _loc())   # 默认步长 1，合成出来的
    return Statement(STMT_LOOP, (var_expr, from_expr, to_expr, step_expr, stmts))
```

没有显式 `一步N蹿` 的循环，Transformer 在这里帮你塞了个默认步长 1。

**经典的悬挂 else：`if_else_stmt`**

悬挂 else（dangling else）是语法分析里的老大难问题：`如果 A 那么 如果 B 那么 C 否则 D`，这个 `否则 D` 到底归哪个 `如果`？

dongbei 用了教科书式的解法——把 `stmt` 分成两类：

- `open_stmt`：最外层的 `if` 没有 `else`（悬挂状态）
- `matched_stmt`：所有的 `if` 都配上了 `else`

规则强制要求：`else` 之前只能是 `matched_stmt`，这样 `else` 就只能属于最近的 `if`。Transformer 里 `if_else_stmt` 和 `if_stmt` 各处理有 else 和没 else 的情形。

### Expr 子类一览

| 类名 | 东北话语法示例 | `to_python()` 输出示例 |
|---|---|---|
| `LiteralExpr` | `二`、`"你好"` | `2`、`"你好"` |
| `VariableExpr` | `【老王】` | `老王` |
| `ArithmeticExpr` | `二加三` | `_dongbei_add(2, 3)` |
| `ComparisonExpr` | `二比三还小` | `(2) < (3)` |
| `ConcatExpr` | `一、二、三` | `str(1) + str(2) + str(3)` |
| `CallExpr` | `整【打招呼】（"老铁"）` | `打招呼("老铁")` |
| `NegateExpr` | `拉饥荒 三` | `-(3)` |
| `IndexExpr` | `【数组】的老二` | `数组[1]` |
| `LengthExpr` | `【数组】有几个坑` | `len(数组)` |
| `SubListExpr` | `【数组】掐头` | `数组[1:]` |
| `TupleExpr` | `一跟二抱团` | `(1, 2)` |
| `ObjectPropertyExpr` | `【对象】的【属性】` | `对象.属性` |
| `MethodCallExpr` | `【对象】整【方法】` | `对象.方法()` |
| `NewObjectExpr` | `【类名】的新对象（参数）` | `类名(参数)` |
| `ListExpr` | `「一，二，三」` | `[1, 2, 3]` |
| `ParenExpr` | `（表达式）` | `(表达式)` |

每个子类都有 `to_python()`（代码生成用）和 `to_dongbei()`（错误消息用）。

### 特殊标识符映射（_dongbei_var_to_python_var）

这些东北话标识符在翻译时自动换成对应的 Python 名字：

| 东北话 | Python | 含义 |
|---|---|---|
| `俺` | `self` | 方法里的 self |
| `没毛病` | `True` | 布尔真 |
| `有毛病` | `False` | 布尔假 |
| `新对象` | `__init__` | 构造方法 |
| `你吱声` | `input` | 读用户输入 |
| `最高指示` | `sys.argv` | 命令行参数 |
| `打个盹` | `time.sleep` | 睡眠函数 |

`get_python_var_name()` 统一查这张表，查不到就原样返回。

### 追踪续集：`老王装二。`

```
Token 列表 → Lark 匹配 assign_stmt 规则
  → _DongbeiTransformer.assign_stmt(items) 被调用
      items[0] = VariableExpr("老王")
      items[1] = LiteralExpr(Token(TK_NUMBER_LITERAL, 2, ...))
  → 返回 Statement(STMT_ASSIGN, (VariableExpr("老王"), LiteralExpr(2)))
```

---

## 代码生成：translate_statement_to_python()

`translate_statement_to_python()` 是超级翻译官，往里丢一个 Statement，出来一段 Python 字符串（不带末尾换行）。

结构很简单：一串 `if stmt.kind == STMT_*:` 判断，每种语句有自己的翻译逻辑。共 24 种 `STMT_*`，看三个有代表性的。

### 一、STMT_SAY → `_dongbei_print(...)`

```python
if stmt.kind == STMT_SAY:
    expr = stmt.value
    return indent + "_dongbei_print(%s)" % (expr.to_python(),)
```

`_dongbei_print()` 是个包装函数，它既往屏幕打印，也往 `_dongbei_output` 这个全局字符串追加内容。测试代码检查的就是 `_dongbei_output` 的值，这样不用 mock `sys.stdout` 也能断言输出。

### 二、STMT_LOOP → `for … in range(…)`

```python
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
```

注意 `(%s) + 1`——dongbei 的循环是**两端闭区间**，Python 的 `range` 是左闭右开，所以上界加一。这是有意为之的设计。

### 三、STMT_FUNC_DEF → `def func(params):`

```python
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
```

函数名和参数名都要过一遍 `get_python_var_name()`，把东北话标识符换成 Python 合法名字。

### exec() 的共享字典技巧

```python
exec(py_code, globals(), globals())
```

两个参数都传 `globals()`，让全局和局部命名空间共用同一个字典。这是为了让递归函数能找到自己——要是传不同字典，函数在自己内部找不到自身的名字，递归就炸了。`run_py_code()` 里有注释和 Stack Overflow 链接解释这个选择。

### 加法的特殊处理

`ArithmeticExpr.to_python()` 对加法单独处理：

```python
def to_python(self):
    if self.operation.value == KW_PLUS:
        return "_dongbei_add(%s, %s)" % (self.op1.to_python(), self.op2.to_python())
    else:
        return "%s %s %s" % (...)
```

`_dongbei_add()` 实现了 dongbei 的加法语义：只要任一操作数是字符串，两边都转成字符串再拼。这跟 Python 的 `+` 不一样——Python 里字符串和数字加会报错，dongbei 里不会。

---

## 手把手：加一个新关键字

说了半天，咋加新东西？咱们来整一个新的语句关键字：`歇会儿 N。`，让 dongbei 程序睡 N 秒。

> 注：现有代码里已经有 `ID_SLEEP = "打个盹"` 可以当普通函数调用，但那得写 `整【打个盹】（N）`。我们这里加的是更地道的语句式写法。

这件事要动七个地方，一步都不能少。

---

**第一步：加关键字常量**

在 `src/dongbei.py` 的 `KW_*` 常量区加一行：

```python
KW_SLEEP_STMT = "歇会儿"
```

---

**第二步：加进 KEYWORDS 元组**

把 `KW_SLEEP_STMT` 加进 `KEYWORDS`。先检查有没有前缀冲突——`歇会儿` 不是任何现有关键字的前缀，也没有现有关键字是它的前缀，直接加在合适的位置就行：

```python
KEYWORDS = (
    ...
    KW_SLEEP_STMT,   # 歇会儿
    ...
)
```

---

**第三步：加进 _KW_VALUE_TO_TERMINAL**

这个字典把关键字值映射到 Lark terminal 名字。下划线开头的 terminal 会被 Lark 自动丢弃（不传给 Transformer），语句关键字通常丢掉就行：

```python
_KW_VALUE_TO_TERMINAL = {
    ...
    KW_SLEEP_STMT: "_KW_SLEEP_STMT",
    ...
}
```

---

**第四步：加语法规则**

在 `_DONGBEI_GRAMMAR` 的 `non_if_stmt` 规则块里加一行：

```
    | _KW_SLEEP_STMT expr _KW_PERIOD                                                    -> sleep_stmt
```

同时在文法末尾的 terminal 声明区加一行（随便找个 `_KW_*: /x/` 旁边）：

```
_KW_SLEEP_STMT: /x/
```

这个正则 `/x/` 是占位符——`_DongbeiLexer` 根本不用正则匹配，它直接用预分词好的 Token 列表；terminal 声明只是让 Lark 知道这个名字存在。

---

**第五步：加 STMT_* 常量**

```python
STMT_SLEEP = "SLEEP"
```

---

**第六步：加 Transformer 方法**

在 `_DongbeiTransformer` 里加：

```python
def sleep_stmt(self, items):
    return Statement(STMT_SLEEP, items[0])
```

`items[0]` 是 `expr` 对应的 Expr 对象，存进 Statement 的 `value`。

---

**第七步：加代码生成**

在 `translate_statement_to_python()` 里加一个 `if` 分支：

```python
if stmt.kind == STMT_SLEEP:
    return indent + f"time.sleep({stmt.value.to_python()})"
```

`time` 模块在 `src/dongbei.py` 顶部已经导入，直接用。

---

**第八步：写测试、更新文档**

测试写法见下一节。`doc/cheatsheet.md` 里加上这个新关键字的说明，`README.md` 如果有语法速查也顺手更新。

---

完事了！整个过程就是：
**加关键字常量 → 加进 KEYWORDS → 加 terminal → 加语法规则 → 加 STMT 常量 → 加 Transformer → 加代码生成 → 加测试 → 更新文档**。九环扣着九环，一个都不能少，少一个编译器就给你整叉劈了。

---

## 加新的表达式

语句是一行完整的操作，表达式是语句里的值。加新表达式跟加新语句的步骤大差不差，区别是：要写一个 `Expr` 子类，而不是直接在 `translate_statement_to_python()` 里加分支。

举个例子：加一个取绝对值的表达式，语法是 `绝对 X`，翻成 Python 的 `abs(X)`。

### Expr 子类模板

```python
class AbsExpr(Expr):
    def __init__(self, expr):
        self.expr = expr

    def __str__(self):
        return f"ABS_EXPR<{self.expr}>"

    def equals(self, other):
        return self.expr == other.expr

    def to_dongbei(self):
        return f"绝对{self.expr.to_dongbei()}"

    def to_python(self):
        return f"abs({self.expr.to_python()})"
```

四个方法缺一不可：
- `equals()`：单元测试里比较两个 Expr 是否相等用的
- `to_python()`：代码生成，翻成 Python 表达式字符串
- `to_dongbei()`：**别偷懒跳过这个**——断言失败的报错消息用它生成可读的东北话描述，要是只有 `ABS_EXPR<...>` 用户看了一脸懵

关键字常量、KEYWORDS、_KW_VALUE_TO_TERMINAL 的步骤和加语句完全一样，不重复说了。

语法规则加在 `expr` / `atomic_expr` 一类的表达式规则里（视优先级而定）。Transformer 方法返回 `AbsExpr(items[0])` 即可。

---

## 跑测试：别给自己挖坑

测试不是为了整人，是为了你以后改代码的时候不给自己挖坑。你现在写的测试，就是将来那个自己的救命稻草。

### 测试文件一览

| 文件 | 测试内容 |
|---|---|
| `test/dongbei_test.py` | 主测试套件，5 个测试类，100+ 个方法 |
| `test/dongbei_add_test.py` | 专门测 `_dongbei_add()` 的字符串+数字拼接逻辑 |
| `test/test_all` | 跑所有单元测试 + 把 `demo/` 里每个 `.dongbei` 文件都跑一遍 |

**五个测试类：**

- `DongbeiParseExprTest`：测表达式解析，用 `parse_expr_from_str()` 直接给字符串，断言返回的 Expr 对象
- `DongbeiParseStatementTest`：测语句解析，用 `parse_stmt_from_str()`
- `DongbeiTest`：集成测试，用 `translate_and_run()` 跑完整程序，断言输出字符串
- `DongbeiTokenizerRecursionTest`：回归测试，确保大输入不会撑爆 Python 递归栈
- `DongbeiSourceLocTest`：确保 Token 的源码位置信息在 Lark Transformer 里没被丢掉

### 铁律：一个测试方法只测一件事

CLAUDE.md 里写得清楚：**每个测试方法只整一件事，不要把好几件不相干的事塞一个方法里**。

坏的写法（别学）：
```python
def test_sleep_various(self):
    # 测 int 参数
    self.assertEqual(translate_and_run("歇会儿 一。"), "")
    # 测 float 参数
    self.assertEqual(translate_and_run("歇会儿 零点五。"), "")
    # 测表达式参数
    self.assertEqual(translate_and_run("歇会儿 一加一。"), "")
```

好的写法：
```python
def test_sleep_with_int(self):
    ...

def test_sleep_with_float(self):
    ...

def test_sleep_with_expr(self):
    ...
```

一个萝卜一个坑，将来某个测试挂了，你一眼就知道哪个特性坏了。

### 给 `歇会儿` 写三种测试

**1. 分词测试（确认关键字能被识别）：**

```python
def test_tokenize_sleep_keyword(self):
    parser = DongbeiParser()
    tokens = parser.tokenize("歇会儿 一。", None)
    self.assertIn(Token(TK_KEYWORD, KW_SLEEP_STMT, None), tokens)
```

**2. 解析测试（确认 AST 结构正确）：**

```python
def test_parse_sleep_stmt(self):
    stmt = parse_stmt_from_str("歇会儿 一。")
    self.assertEqual(stmt.kind, STMT_SLEEP)
    self.assertEqual(stmt.value, LiteralExpr(Token(TK_NUMBER_LITERAL, 1, None)))
```

**3. 集成测试（确认翻译和执行都对）：**

```python
from unittest.mock import patch

def test_sleep_calls_time_sleep(self):
    with patch("time.sleep") as mock_sleep:
        translate_and_run("歇会儿 二。", None)
        mock_sleep.assert_called_once_with(2)
```

### 怎么跑单个测试

```bash
# 跑一整个文件
python3 -m unittest test.dongbei_test

# 跑一个类
python3 -m unittest test.dongbei_test.DongbeiTest

# 跑一个方法
python3 -m unittest test.dongbei_test.DongbeiTest.test_say_number

# 跑全套（含 demo）
bash test/test_all
```

---

## 彩蛋和隐藏机关

这个代码库里有几处让人会心一笑的设计，知道了你会觉得这帮人真的太坏了。

### 苹果总部

```python
KW_1_INFINITE_LOOP_EGG = "在苹果总部磨叽："  # 彩蛋
```

苹果公司总部的门牌号是"1 Infinite Loop, Cupertino, CA"（一号无限循环路）。这个关键字跟 `KW_1_INFINITE_LOOP = "从一而终磨叽："` 功能完全相同，只是多了个苹果梗。

注意 KEYWORDS 里的注释：`must match 在苹果总部磨叽 before 在`——这彩蛋关键字也得遵守前缀规则。

### REPL 退出咒

在交互式 REPL 里想退出？这三种拼法都能用：

- `瞅你咋的`
- `瞅你咋地`
- `瞅你咋滴`

东北人打字不讲究，三种结尾都认。

### exec() 的共享字典玄机

```python
# See https://stackoverflow.com/questions/871887/using-exec-with-recursive-functions
# Use the same dictionary for local and global definitions.
# Needed for defining recursive dongbei functions.
exec(py_code, globals(), globals())
```

两个 `globals()` 不是手抖，是有意为之，还贴心地附了 Stack Overflow 链接。

### 套娃解释器（src/dongbei.dongbei）

`src/dongbei.dongbei` 是用东北话写的东北话解释器，目前还在施工（`# 施工中，请戴好安全帽`）。等它写完，就可以用 dongbei 解释器来跑 dongbei 解释器，完美套娃。

### 树新蜂驱动开发（TnBD）

项目 README 里提到"树新蜂驱动开发"（TnBD），这是个谐音梗：TDD（Test-Driven Development）→ 树蜂蜂 → 树新蜂。精髓是先写文档和测试，代码跟上——跟 TDD 的"先写测试"异曲同工，但用东北话说出来格外有气势。

---

## 整一个 PR 要注意啥

提 PR 之前对着这个清单捋一遍，别让 CI 给你打脸：

- **文档先行**：先更新 `doc/cheatsheet.md`（语法说明）和 `README.md`（如有速查表），再写代码——树新蜂精神
- **测试必须有**：一个特性一个测试方法，别堆在一起
- **`bash test/test_all` 全绿**：单元测试 + 所有 demo 都得过，一个都不能差
- **关键字顺序**：加了新关键字，必须检查 KEYWORDS 里有没有前缀冲突，长的在前
- **函数名用 snake_case**：`translate_and_run` 对，`translateAndRun` 不行
- **注释和 PR 说明用东北方言**：这是项目文化，严肃认真地耍贫嘴
- **STMT_* 和 KW_* 都要加**：别忘了哪一环，九步走完才算整完了
- **发布流程**看 `DEVELOPE.md`：改版本号、打 tag、CD 自动发 PyPI 都在那儿写着

---

*老铁，整到这儿你已经把 dongbei 解释器从里到外翻了个遍。接下来就是放开手整，有问题去 GitHub Issues 上吱声，咱们一起把这门大碴子话的编程语言越整越好！*
