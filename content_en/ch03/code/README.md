# Chapter 3 — Why Seven Bridges Couldn't Be Crossed, and Why Tables Won

`Part 1 — Roots: Where the Graph Was All Along` | **English** | [한국어](../../../content/ch03/code/README.md) | [Contents](../../../README.en.md) | [Sources](../../../SOURCES.en.md)

> I got paged at 2 a.m. Database CPU pinned at 100% and not coming down.

This chapter looks at two things. How the graph came to be invented, and why it lost to the table for forty years. The second one matters more. If you do not know why tables won, you will move to a graph and repeat the same mistake.

## Sections

| # | Title |
|---|---|
| 3.1 | Throwing away the map is what produced the answer |
| 3.2 | So why did tables win for forty years |
| 3.3 | What tables missed: depth decides cost |
| 3.4 | Recursive CTEs: they work, but |
| 3.5 | The standards met in the middle |

## The chapter in one page

- Euler got his answer by discarding the map. What was left was degree, and you can cross every bridge exactly once only when the count of odd-degree vertices is 0 or 2.
- Tables won for forty years for three reasons: declarative queries, constraints, transactions. Check those three first when you pick a graph engine.
- What tables missed is not storage, it is following. A join multiplies the intermediate result every time it stacks; a traversal reads only what it visits. Measured, the gap was 78x at four hops.
- A recursive CTE does work, but it has nowhere to put a visited marker, so it miscounts "exactly k bridges." You can fix it. The fix is twenty lines.

## Keywords and primary sources

| Term | Status | Source |
|---|---|---|
| Seven Bridges of Königsberg | [Standard] | [scholarlycommons.pacific.edu/euler-works/53](https://scholarlycommons.pacific.edu/euler-works/53/) |
| degree | [Standard] | [scholarlycommons.pacific.edu/euler-works/53](https://scholarlycommons.pacific.edu/euler-works/53/) |
| relational model | [Standard] | [dl.acm.org/doi/10.1145/362384.362685](https://dl.acm.org/doi/10.1145/362384.362685) |
| recursive CTE | [Standard] | [sqlite.org/lang_with.html](https://www.sqlite.org/lang_with.html) |
| transaction, ACID | [Standard] | [sqlite.org/transactional.html](https://www.sqlite.org/transactional.html) |
| ISO/IEC 9075-16:2023 | [Standard] | [iso.org/standard/79473.html](https://www.iso.org/standard/79473.html) |
| ISO/IEC 39075:2024 | [Standard] | [iso.org/standard/76120.html](https://www.iso.org/standard/76120.html) |

**[Standard]** an official specification exists, **[De facto]** no specification but the industry uses it widely, **[Experimental]** still finding its footing.

## Running the examples

The example code is not duplicated per language. It lives once, in [`content/ch03/code/`](../../../content/ch03/code). Comments and printed output are Korean; the commands below are not.

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

Checked August 2026. Python 3.9+. **No dependencies** (`sqlite3` is in the standard library).

```bash
cd content/ch03/code
python3 graphdata.py          # sample graph statistics
python3 ex1_euler.py          # the Euler test
python3 ex2_sql_vs_graph.py   # what each extra hop costs
python3 ex3_recursive_cte.py  # where recursive CTEs stop working
python3 ex4_why_tables_won.py # why tables won
```

| File | What it shows |
|---|---|
| `graphdata.py` | 200 people, 1,163 friendships. Fixed seed, so the graph is the same every run |
| `ex1_euler.py` | The 1736 argument in 20 lines. Add one more bridge and the answer changes |
| `ex2_sql_vs_graph.py` | The point at four hops where joins run 78x slower than traversal |
| `ex3_recursive_cte.py` | Why a recursive CTE and a traversal return *different* answers |
| `ex4_why_tables_won.py` | Declarative queries, constraints, transactions |

Absolute timings differ per machine. Read the ratios only.

<!-- 실행 가이드 끝 -->

---

**What flips next chapter:** this chapter got us to "store the relations." The next one looks at what happened when that idea was pushed onto the entire web: the semantic web. The ambition was right and it got mocked for twenty years. Why that happened, and why we are pulling it back out now.

---

Previous: [Ch 2 From Harness Engineering to Graph Engineering](../../ch02/code/README.md) | [Contents](../../../README.en.md) | Next: [Ch 4 Why the Semantic Web Looked Like a Failure](../../ch04/code/README.md)

Found something wrong in this chapter? [File a factual error](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml) or [object to a status label](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml). English is fine.
