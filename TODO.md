# TODO

Code quality issues found during review of `src/dongbei.py`.

- [x] **#1** Remove dead `KW_PLUS` entry and stale comments from `ARITHMETIC_OPERATION_TO_PYTHON` (lines 549–588) — `KW_PLUS` maps to `"_dongbei_add"` in the dict but `ArithmeticExpr.ToPython()` special-cases `KW_PLUS` before ever consulting the dict, making that entry unreachable. Three inline comments (lines 549, 579, 582) are stale implementation notes. Remove the dead dict entry and the three comments.

- [x] **#2** Delete unused `yield_loc` variable (line 1243) — `yield_loc = self.loc` is computed but never referenced, unlike the neighbouring `inc_loc`/`dec_loc` which are passed into `NumberLiteralExpr`.

- [x] **#3** Fix recursive `BasicTokenize` to avoid `RecursionError` on large files (lines 951–989) — recurses once per token consumed; Python's default limit is ~1000 frames, so files with ~1000+ tokens will crash. Acknowledged by TODO on line 878. Convert to an iterative `while self.code:` loop.

- [x] **#4** Rename `list` parameter in `SubListExpr.__init__` to avoid shadowing the built-in (line 448) — rename to `list_expr` to match the convention already used in `IndexExpr`.

- [x] **#5** Fix typo `"fof"` → `"for"` in comment (line 1177).

- [x] **#6** Replace `type() ==` comparisons with `isinstance()` (lines 280, 352) — the `Expr.__eq__` form (line 352) intentionally rejects subclasses; add a comment explaining why. The `SourceLoc` one (line 280) has no such reason and should use `isinstance()`.

- [x] **#7** Replace O(n) token list slicing with an index pointer — every `TryConsumeToken`/`ConsumeToken` call does `self.tokens = self.tokens[1:]`, copying O(remaining) references and making parsing O(n²). Replace with a `(tokens, pos)` pair and advance the integer index; backtracking becomes a single integer save/restore.

## Lark migration cleanup (`src/dongbei.py`)

- [x] **#8** Delete ~440 lines of dead hand-written parser methods (lines 1105–1545) — `TryParseObjectExpr`, `TryParseAtomicExpr`, `TryParseTermExpr`, `TryParseArithmeticExpr`, `TryParseCallExpr`, `TryParseTupleExpr`, `TryParseNonConcatExpr`, `TryParseExpr`, `TryParseCompOrArithExpr`, `TryParseFuncDef`, `ParseMethodDefs`, `ParseStmt`, `ParseExprList`, and all `TryConsumeToken`/`ConsumeToken`/`TryConsumeKeyword`/`ConsumeKeyword` helpers are unreachable since `TranslateTokensToStatements` and all `Parse*FromStr` functions now go through Lark. Note: `ParseStmts` and `TryParseStmt` are called inside this dead code but are not even defined — the dead code would crash if ever reached.

- [x] **#9** Eliminate transformer pass-through methods by marking grammar rules transparent — `arith_expr`, `term_expr`, `atom_expr`, `object_expr`, `call_expr`, and `func_def` transformer methods all just do `return items[0]`; they exist only because those grammar rules lack the `?` transparent prefix. Prefix them with `?` in `_DONGBEI_GRAMMAR` and delete the six pass-through methods.

- [x] **#10** Collapse duplicated no-args-paren call rules — `call_func_no_args` and `call_func_no_args_paren` produce identical `CallExpr(name, [])` results, as do `call_base_init_no_args` and `call_base_init_no_args_paren`. The duplication exists because `expr_list` requires ≥1 element. Make the args optional in `call_expr` (e.g. `_KW_CALL IDENTIFIER (_KW_OPEN_PAREN expr_list? _KW_CLOSE_PAREN)?`) and collapse the four rules to two.

- [x] **#11** Propagate real source locations through the transformer — `_loc()` always returns a fresh dummy `SourceLoc("<unknown>:1:0")`. Every `Keyword`, `NumberLiteralExpr`, and `Token` synthesised in `_DongbeiTransformer` loses its source position, degrading error messages. Pass the actual `SourceLoc` from the nearest input token instead.

## Post-migration documentation debt (`src/dongbei.py`)

- [x] **#12** Update the grammar header comment to document the `KW_X` vs `_KW_X` convention — the comment currently says "All `_KW_*` terminals are underscore-prefixed → auto-discarded" but 15 operator terminals (`KW_PLUS`, `KW_MINUS`, etc.) are intentionally non-filtered so the transformer can extract their `SourceLoc`. Add a sentence explaining that non-underscore operator terminals exist specifically to carry source locations into transformer `items`.

- [x] **#13** Document the remaining `_loc()` call sites as intentional — `loop_stmt`, `method_def_no_params`, and `method_def_with_params` still call `_loc()` for synthesized tokens (the step-1 literal in a plain loop, and the implicit `self` parameter). Without explanation these look like oversights left over from #11. Add a brief comment at each call site explaining why there is no source token to take the loc from.

- [x] **#14** Guard against silent index drift in transformer methods — transformer methods like `comp_greater` rely on hard-coded `items[2]` to reach the `KW_GREATER` token; if anyone adds another non-filtered terminal to that grammar rule the index shifts silently and the wrong loc is used. Consider adding an assertion (e.g. `assert self._dk(items[2]).value == KW_GREATER`) at each loc-extraction site so a mismatch fails loudly rather than producing a wrong source position.

## Migration leftovers (`src/dongbei.py`)

- [x] **#15** Fix `_DongbeiLexer` docstring — says "LALR parser" but the actual parser is Earley (see `lark.Lark(..., parser="earley", ...)`). One-word fix.

- [x] **#16** Delete dead `TryParseExprFromStr` — never called from anywhere in the codebase. Its `(None, tokens)` failure return is also misleading: in the old recursive-descent interface `tokens` meant "remaining tokens"; here it is the full input list. `ParseExprFromStr` already creates a fresh parser per call so there is nothing to corrupt on failure; callers that want try-semantics can wrap it in `try/except` directly.

- [x] **#17** Drop the vestigial `[]` from `ParseExprFromStr` and `ParseStmtFromStr` return values — both return `(result, [])` where the empty list was the old "remaining tokens" from the recursive-descent interface. With Lark the remainder is always empty (Lark parses the whole input or raises). All ~30 call sites already discard it with `[0]`. Change both functions to return the result directly and update the call sites.

## Pre-existing bugs now more visible after migration

- [x] **#18** Fix identifier and number literal tokens always reporting loc `{1,0}` — `_Tokenize()` captures `loc = self.loc.Clone()` once at the top of the method and never updates it, so every `TokenizeStrContainingNoKeyword` call gets the initial position. Individual `TK_CHAR` tokens from `BasicTokenize()` do carry correct per-character locs, but `_Tokenize()` ignores them. Fix: when starting a new run of `TK_CHAR` tokens (i.e. when `last_last_token.kind != TK_CHAR`), update `loc` from the first char token's `.loc`. This bug predates the migration but is now more glaring since keyword locs are correct and `DongbeiSourceLocTest` exists to catch regressions.
