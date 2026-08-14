# %% [markdown]
# # 세 언어의 차이가 가장 크게 벌어지는 지점 — 경로 표현
#
# **질문**: 세 언어의 차이가 가장 크게 벌어지는 지점은 어디인가?
#
# **답**: 경로 표현이다. Cypher는 상한을 쓸 수 있고, SPARQL은 표준에 상한 표기가 없고,
# SQL은 재귀 CTE 스무 줄이 된다.
#
# 이 노트북은 **똑같은 질문** — "어떤 회사의 1~3단계 아래 자회사 전부" — 를 세 가지
# 의미론으로 직접 구현해서, 어디에서 갈라지는지를 결과와 줄 수로 확인한다.
#
# | 언어 | 표기 | 상한 | 이 노트북의 구현 |
# |---|---|---|---|
# | Cypher | `-[:ParentOf*1..3]->` | 문법에 있음 | 깊이 3에서 끊는 BFS |
# | SPARQL | `ex:parentOf+` | 표준에 없음 | 무한 이행 폐쇄 + 사후 필터 |
# | SQL | `WITH RECURSIVE ...` | 손으로 적음 | sqlite3 재귀 CTE |
#
# 상한이 있는지 없는지는 표기 취향 문제가 아니다. 9장의 «상한을 걸어라»를
# 언어 안에서 지킬 수 있는가 아닌가가 갈린다.

# %%
# 필요 패키지: plotly, kaleido (시각화용). 나머지는 표준 라이브러리(sqlite3, collections)만 쓴다.
# 원 예제(ex2_path_queries.py)는 kuzu + rdflib 로 실제 엔진을 돌리지만,
# 여기서는 «의미론»만 파이썬으로 재현해서 엔진 없이 차이를 보인다.

import sqlite3
import textwrap
from collections import deque


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# 11장 seed.py 의 PARENT_OF 를 5단계까지 늘렸다.
# 상한 3 과 «상한 없음»이 실제로 달라지려면 깊이가 4 이상이어야 하니까.
PARENT_OF = [
    ("가온테크", "가온소프트"),
    ("가온소프트", "가온연구소"),
    ("가온연구소", "가온랩스"),
    ("가온랩스", "가온마이크로"),
    ("가온마이크로", "가온나노"),
]
ROOT = "가온테크"
print(f"간선 {len(PARENT_OF)}개, 뿌리 {ROOT} 에서 최대 깊이 5")
# 출력: 간선 5개, 뿌리 가온테크 에서 최대 깊이 5

# %% [markdown]
# ## 1. Cypher — 상한을 언어가 받아 준다
#
# ```cypher
# MATCH (a:Co)-[:ParentOf*1..3]->(b:Co)
# RETURN a.name, b.name ORDER BY a.name, b.name
# ```
#
# `*1..3` 이 전부다. 하한 1, 상한 3. 엔진은 깊이 4로 내려가지 않는다.
# 탐색 비용이 $O(d^{k})$ (분기수 $d$, 홉 수 $k$) 로 폭발하는 걸 **질의문 한 글자**로 막는다.

# %%
CYPHER = "MATCH (a:Co)-[:ParentOf*1..3]->(b:Co) RETURN a.name, b.name ORDER BY a.name, b.name"

adj = {}
for p, c in PARENT_OF:
    adj.setdefault(p, []).append(c)


def cypher_bounded(source, lo=1, hi=3):
    """-[:ParentOf*lo..hi]-> 의 의미론. 상한에서 «가지를 자른다»."""
    out, q = set(), deque([(source, 0)])
    while q:
        node, d = q.popleft()
        if d >= hi:            # ← 상한. 여기서 더 안 내려간다
            continue
        for nxt in adj.get(node, []):
            if d + 1 >= lo:
                out.add((nxt, d + 1))
            q.append((nxt, d + 1))
    return sorted(out, key=lambda x: (x[1], x[0]))


cy = cypher_bounded(ROOT)
print(f"Cypher *1..3 → {len(cy)}행")
for name, d in cy:
    print(f"  {d}홉  {name}")
# 출력: Cypher *1..3 → 3행
# 출력:   1홉  가온소프트
# 출력:   2홉  가온연구소
# 출력:   3홉  가온랩스

# %% [markdown]
# ## 2. SPARQL — 상한 표기가 표준에 없다
#
# ```sparql
# SELECT ?p ?c WHERE { ?a ex:parentOf+ ?b . ?a ex:name ?p . ?b ex:name ?c }
# ```
#
# SPARQL 1.1 속성 경로에는 `*`(0회 이상), `+`(1회 이상), `?`(0 또는 1회)만 있다.
# `{1,3}` 같은 **횟수 상한 문법이 없다**. 초안 단계에 있었으나 표준에서 빠졌다.
#
# 즉 SPARQL 은 «1~3홉»을 물어볼 수 없고, «1홉 이상 전부»만 물어본 다음
# 홉 수를 버린 답을 받는다. 그래서 상한은 언어 밖에서 걸어야 한다.
# 질의 타임아웃, `LIMIT`, 아니면 깊이를 손으로 펼쳐 쓰기.

# %%
SPARQL_PLUS = """PREFIX ex: <http://example.org/>
SELECT ?p ?c WHERE { ?a ex:parentOf+ ?b . ?a ex:name ?p . ?b ex:name ?c }
ORDER BY ?p ?c"""


def sparql_plus(source):
    """ex:parentOf+ 의 의미론. 상한 없이 도달 가능한 전부. 홉 수는 결과에 없다."""
    out, q = set(), deque([source])
    while q:
        node = q.popleft()
        for nxt in adj.get(node, []):
            if nxt not in out:
                out.add(nxt)
                q.append(nxt)
    return sorted(out)


sp = sparql_plus(ROOT)
print(f"SPARQL + → {len(sp)}행: {sp}")
print(f"\nCypher 가 준 것: {sorted(n for n, _ in cy)}")
print(f"SPARQL 이 준 것: {sp}")
print(f"덤으로 딸려온 것: {sorted(set(sp) - {n for n, _ in cy})}  ← 4홉, 5홉")
# 출력: SPARQL + → 5행: ['가온나노', '가온랩스', '가온마이크로', '가온소프트', '가온연구소']
# 출력:
# 출력: Cypher 가 준 것: ['가온랩스', '가온소프트', '가온연구소']
# 출력: SPARQL 이 준 것: ['가온나노', '가온랩스', '가온마이크로', '가온소프트', '가온연구소']
# 출력: 덤으로 딸려온 것: ['가온나노', '가온마이크로']  ← 4홉, 5홉

# %% [markdown]
# ### SPARQL 에서 상한을 흉내 내는 두 가지
#
# **(a) 사후 필터** — 결과에 홉 수가 없으니 애초에 필터할 열이 없다.
# 깊이를 알려면 경로를 되짚어야 하고, 그건 이미 «질의 밖»의 일이다.
#
# **(b) 명시적 펼치기** — 홉 수만큼 대안(`|`)을 손으로 늘어놓는다. 이게 실무 해법이다.
#
# ```sparql
# SELECT ?p ?c WHERE {
#   ?a ex:parentOf | ex:parentOf/ex:parentOf | ex:parentOf/ex:parentOf/ex:parentOf ?b .
#   ?a ex:name ?p . ?b ex:name ?c
# } ORDER BY ?p ?c
# ```
#
# 상한 3 은 대안 3개. 상한 6 이면 6개. Cypher 의 `*1..6` 한 글자가
# SPARQL 에서는 줄 수로 자란다.

# %%
SPARQL_UNROLLED = """PREFIX ex: <http://example.org/>
SELECT ?p ?c WHERE {
  ?a ex:parentOf | ex:parentOf/ex:parentOf | ex:parentOf/ex:parentOf/ex:parentOf ?b .
  ?a ex:name ?p . ?b ex:name ?c
} ORDER BY ?p ?c"""


def sparql_unrolled(source, hi=3):
    """대안(|)을 hi 개 펼친 것과 같은 의미론. 결과는 Cypher 와 같아진다."""
    out, frontier = set(), {source}
    for _ in range(hi):
        frontier = {n for f in frontier for n in adj.get(f, [])}
        out |= frontier
    return sorted(out)


un = sparql_unrolled(ROOT)
print(f"펼친 SPARQL → {len(un)}행: {un}")
print(f"Cypher 결과와 같은가: {'예' if un == sorted(n for n, _ in cy) else '아니오'}")
# 출력: 펼친 SPARQL → 3행: ['가온랩스', '가온소프트', '가온연구소']
# 출력: Cypher 결과와 같은가: 예

# %% [markdown]
# ## 3. SQL — 재귀 CTE
#
# SQL 에는 «경로»라는 개념이 없다. 조인을 반복하는 재귀 블록을 직접 짜야 한다.
# 그리고 그 안에서 **세 가지를 손으로 처리**한다.
#
# 1. 깊이 세기 (`depth + 1`)
# 2. 상한 걸기 (`WHERE d.depth < 3`)
# 3. 순환 차단 (경로 문자열 검사 — 없으면 무한 루프)
#
# 앞의 두 언어는 1·3 을 엔진이 해 주고, Cypher 는 2 도 문법으로 해 준다.
# SQL 은 셋 다 내 몫이다. 그래서 스무 줄이 된다.

# %%
SQL_RECURSIVE = textwrap.dedent("""
    WITH RECURSIVE
      descendant (root, node, depth, path) AS (
          -- 씨앗: 1홉
          SELECT p.parent, p.child, 1,
                 '/' || p.parent || '/' || p.child || '/'
            FROM parent_of p
        UNION ALL
          -- 재귀: 한 홉 더. 상한과 순환 차단이 여기 들어간다
          SELECT d.root, p.child, d.depth + 1,
                 d.path || p.child || '/'
            FROM descendant d
            JOIN parent_of p
              ON p.parent = d.node
           WHERE d.depth < 3
             AND d.path NOT LIKE '%/' || p.child || '/%'
      )
    SELECT root, node, MIN(depth) AS depth
      FROM descendant
     WHERE root = ?
     GROUP BY root, node
     ORDER BY depth, node
""").strip()

con = sqlite3.connect(":memory:")
con.execute("CREATE TABLE parent_of (parent TEXT, child TEXT)")
con.executemany("INSERT INTO parent_of VALUES (?,?)", PARENT_OF)

sql_rows = con.execute(SQL_RECURSIVE, (ROOT,)).fetchall()
print(f"SQL 재귀 CTE → {len(sql_rows)}행")
for _, node, d in sql_rows:
    print(f"  {d}홉  {node}")
print(f"\nCypher 결과와 같은가: {'예' if [(n, d) for _, n, d in sql_rows] == cy else '아니오'}")
# 출력: SQL 재귀 CTE → 3행
# 출력:   1홉  가온소프트
# 출력:   2홉  가온연구소
# 출력:   3홉  가온랩스
# 출력:
# 출력: Cypher 결과와 같은가: 예

# %% [markdown]
# ### 순환이 있으면 차이가 더 벌어진다
#
# `가온나노 -> 가온테크` 를 넣어 순환을 만들어 보자.
#
# - Cypher: `*1..3` 이 상한이므로 그냥 멈춘다.
# - SPARQL: `+` 는 **집합 의미론**이라 이미 본 노드를 다시 안 돈다. 멈춘다.
# - SQL: 상한과 순환 차단 중 **하나라도 빼면 무한 루프**다. 안전장치가 질의문 안에 있다.

# %%
PARENT_OF_CYCLE = PARENT_OF + [("가온나노", "가온테크")]
adj_backup = adj
adj = {}
for p, c in PARENT_OF_CYCLE:
    adj.setdefault(p, []).append(c)

print(f"Cypher *1..3 (순환)  {len(cypher_bounded(ROOT))}행  → 상한이 멈춰 준다")
print(f"SPARQL +   (순환)  {len(sparql_plus(ROOT))}행  → 집합 의미론이 멈춰 준다")

con.execute("DELETE FROM parent_of")
con.executemany("INSERT INTO parent_of VALUES (?,?)", PARENT_OF_CYCLE)
n_guard = len(con.execute(SQL_RECURSIVE, (ROOT,)).fetchall())
SQL_NO_GUARD = "\n".join(ln for ln in SQL_RECURSIVE.splitlines() if "NOT LIKE" not in ln)
n_noguard = len(con.execute(SQL_NO_GUARD, (ROOT,)).fetchall())
print(f"SQL 재귀 (순환)     {n_guard}행  → 순환 차단을 «내가» 적어야 한다")
print(f"  순환 차단만 뺐을 때: {n_noguard}행 (상한 3 이 없다면 무한 루프)")
adj = adj_backup
# 출력: Cypher *1..3 (순환)  3행  → 상한이 멈춰 준다
# 출력: SPARQL +   (순환)  6행  → 집합 의미론이 멈춰 준다 (뿌리 자신도 도달 대상이 된다)
# 출력: SQL 재귀 (순환)     3행  → 순환 차단을 «내가» 적어야 한다
# 출력:   순환 차단만 뺐을 때: 3행 (상한 3 이 없다면 무한 루프)

# %% [markdown]
# ## 4. 줄 수와 결과를 나란히
#
# 이게 «가장 크게 벌어지는 지점»의 정량적 모습이다.

# %%
def nlines(q):
    return len([ln for ln in q.strip().splitlines() if ln.strip()])


ROWS = [
    ("Cypher\n*1..3", nlines(CYPHER), len(cy), "상한 O"),
    ("SPARQL\n+", nlines(SPARQL_PLUS), len(sp), "상한 X"),
    ("SPARQL\n펼쳐 쓰기", nlines(SPARQL_UNROLLED), len(un), "상한 △"),
    ("SQL\n재귀 CTE", nlines(SQL_RECURSIVE), len(sql_rows), "상한 손으로"),
]
print(f"{'언어':<16}{'줄 수':>6}{'결과행':>8}  상한")
for label, ln, rows, cap in ROWS:
    print(f"{label.replace(chr(10), ' '):<16}{ln:>6}{rows:>8}  {cap}")
print(f"\nSQL 은 Cypher 보다 {nlines(SQL_RECURSIVE) / nlines(CYPHER):.0f}배 길다")
# 출력: 언어               줄 수     결과행  상한
# 출력: Cypher *1..3          1       3  상한 O
# 출력: SPARQL +              3       5  상한 X
# 출력: SPARQL 펼쳐 쓰기        5       3  상한 △
# 출력: SQL 재귀 CTE          21       3  상한 손으로
# 출력:
# 출력: SQL 은 Cypher 보다 21배 길다

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

labels = [r[0] for r in ROWS]
lines = [r[1] for r in ROWS]
rows_n = [r[2] for r in ROWS]
COLORS = ["#4C78A8", "#E45756", "#F58518", "#72B7B2"]

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=("질의문 줄 수 — 같은 질문, 같은 답",
                    "결과 행 수 — 상한이 없으면 답이 달라진다"),
)
fig.add_trace(
    go.Bar(x=labels, y=lines, marker_color=COLORS,
           text=[f"{v}줄" for v in lines], textposition="outside",
           showlegend=False),
    row=1, col=1,
)
fig.add_trace(
    go.Bar(x=labels, y=rows_n, marker_color=COLORS,
           text=[f"{v}행" for v in rows_n], textposition="outside",
           showlegend=False),
    row=1, col=2,
)
fig.add_hline(y=len(cy), line_dash="dot", line_color="#888",
              annotation_text="1~3홉의 정답 3행", annotation_position="bottom left",
              row=1, col=2)
fig.update_yaxes(title_text="줄", range=[0, max(lines) * 1.25], row=1, col=1)
fig.update_yaxes(title_text="행", range=[0, max(rows_n) * 1.35], row=1, col=2)
fig.update_layout(
    title="경로 표현 — 세 언어가 갈라지는 자리",
    template="plotly_white", height=460, width=980,
    margin=dict(t=110, b=60),
)
_show(fig)

import pathlib
out = pathlib.Path(__file__).with_name("expy.png") if "__file__" in dir() else pathlib.Path("expy.png")
fig.write_image(str(out), scale=2)
print(f"저장: {out}")
# 출력: 저장: .../expy.png

# %% [markdown]
# ## 정리
#
# - `MATCH`, `WHERE`, `RETURN` 수준에서 세 언어는 **거의 번역이 된다**. 문장 모양만 다르다.
#   Cypher 는 그림, SPARQL 은 문장, Gremlin 은 걸음.
# - 번역이 깨지는 자리가 **경로 표현**이다.
#   - Cypher `*1..3` — 상한이 문법에 있다. 한 글자로 폭발을 막는다.
#   - SPARQL `+` — 표준에 상한 표기가 **없다**. 타임아웃·`LIMIT`·펼쳐 쓰기로 우회한다.
#   - SQL `WITH RECURSIVE` — 깊이·상한·순환 차단을 다 손으로 적어 스무 줄이 된다.
# - 그래서 이 차이는 «문법 취향»이 아니라 **운영 안전장치를 언어가 주는가**의 차이다.
#   9장의 «상한을 걸어라»를 Cypher 는 질의문 안에서, SPARQL 은 질의문 밖에서 지킨다.
# - 이식을 대비하려면: 질의문을 한곳에 모으고, `ORDER BY` 를 강제하고,
#   엔진 고유 함수를 격리하고, 각 질의가 답하는 질문을 주석으로 남긴다.
