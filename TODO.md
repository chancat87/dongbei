# TODO

Code quality issues found during review of `src/dongbei.py`.

- [x] **#1** Remove dead `KW_PLUS` entry and stale comments from `ARITHMETIC_OPERATION_TO_PYTHON` (lines 549–588) — `KW_PLUS` maps to `"_dongbei_add"` in the dict but `ArithmeticExpr.ToPython()` special-cases `KW_PLUS` before ever consulting the dict, making that entry unreachable. Three inline comments (lines 549, 579, 582) are stale implementation notes. Remove the dead dict entry and the three comments.

- [x] **#2** Delete unused `yield_loc` variable (line 1243) — `yield_loc = self.loc` is computed but never referenced, unlike the neighbouring `inc_loc`/`dec_loc` which are passed into `NumberLiteralExpr`.

- [ ] **#3** Fix recursive `BasicTokenize` to avoid `RecursionError` on large files (lines 951–989) — recurses once per token consumed; Python's default limit is ~1000 frames, so files with ~1000+ tokens will crash. Acknowledged by TODO on line 878. Convert to an iterative `while self.code:` loop.

- [x] **#4** Rename `list` parameter in `SubListExpr.__init__` to avoid shadowing the built-in (line 448) — rename to `list_expr` to match the convention already used in `IndexExpr`.

- [x] **#5** Fix typo `"fof"` → `"for"` in comment (line 1177).

- [x] **#6** Replace `type() ==` comparisons with `isinstance()` (lines 280, 352) — the `Expr.__eq__` form (line 352) intentionally rejects subclasses; add a comment explaining why. The `SourceLoc` one (line 280) has no such reason and should use `isinstance()`.

- [ ] **#7** Replace O(n) token list slicing with an index pointer — every `TryConsumeToken`/`ConsumeToken` call does `self.tokens = self.tokens[1:]`, copying O(remaining) references and making parsing O(n²). Replace with a `(tokens, pos)` pair and advance the integer index; backtracking becomes a single integer save/restore.
