# %% [markdown]
# # 가변 길이 경로 표기: Cypher `*1..3` vs SPARQL `+`
#
# **질문** — Cypher와 SPARQL의 가변 길이 경로 표기는 어떻게 다른가?
#
# **답** — Cypher는 `-[:ParentOf*1..3]->`로 상한을 반드시 쓸 수 있고,
# SPARQL은 `ex:parentOf+`로 «한 번 이상»만 표현할 수 있어 상한 표기가 없다.
#
# 이 노트북에서 확인할 것:
#
# 1. 깊은 사슬(depth 8) + 분기를 만들고
# 2. Cypher `*1..k` (k=1,2,3)와 SPARQL `+`(전이 폐쇄)의 **결과 행 수**를 비교
# 3. 깊이가 커질 때 두 결과가 어떻게 **벌어지는지**
# 4. SPARQL에서 상한을 흉내 내는 우회로(`p`, `p/p`, `p/p/p`의 명시적 펼침)와 그 함정
#
# 사슬 길이 $d$(노드 $d+1$개)의 경로 그래프에서, 정확히 $j$홉 떨어진 순서쌍의 수는
# $d+1-j$개다. 따라서
#
# $$|R_{\le k}(d)| = \sum_{j=1}^{\min(k,d)} (d+1-j), \qquad
#   |R_{+}(d)| = \sum_{j=1}^{d} (d+1-j) = \frac{d(d+1)}{2}$$
#
# 상한 $k$를 걸면 $O(kd)$로 **선형**, 상한이 없으면 $O(d^2)$로 **이차**로 자란다.
# 9장의 «상한을 걸어라»가 왜 표기 문제가 아니라 비용 문제인지가 여기서 나온다.

# %%
# 필요 패키지: rdflib>=7 (SPARQL), kuzu (Cypher), plotly + kaleido (그림)
#   pip install "rdflib>=7,<8" kuzu plotly kaleido
# 확인 시점: 2026-08, Python 3.9.6 / rdflib 7.6.0 / kuzu 0.11.3 / plotly 6.8.0

import os
import shutil
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


try:
    import kuzu
    HAS_KUZU = True
except ImportError:
    HAS_KUZU = False

try:
    from rdflib import Graph
    HAS_RDFLIB = True
except ImportError:
    HAS_RDFLIB = False

print(f"kuzu={HAS_KUZU}  rdflib={HAS_RDFLIB}")
# 출력: kuzu=True  rdflib=True

# %% [markdown]
# ## 1단계 — 같은 사실을 두 모델에 넣는다
#
# 깊은 사슬 `N0 -> N1 -> ... -> N8` (8홉)에 분기 두 개를 붙인다.
#
# ```
# N0 -> N1 -> N2 -> N3 -> N4 -> N5 -> N6 -> N7 -> N8
#  |           |
#  |           +-> X1
#  +-> B1 -> B2
# ```
#
# 엣지 목록 하나에서 Cypher용 DDL과 SPARQL용 Turtle을 같이 만든다.
# «같은 사실, 다른 문장»이라는 11장의 논지를 코드로 고정하는 것이다.

# %%
CHAIN = [f"N{i}" for i in range(9)]                      # N0..N8
EDGES = [(CHAIN[i], CHAIN[i + 1]) for i in range(8)]     # 사슬 8홉
EDGES += [("N0", "B1"), ("B1", "B2"), ("N2", "X1")]      # 분기
NODES = sorted({n for e in EDGES for n in e})

TTL = "@prefix ex: <http://example.org/> .\n"
TTL += "".join(f"ex:{n} a ex:Co ; ex:name '{n}' .\n" for n in NODES)
TTL += "".join(f"ex:{a} ex:parentOf ex:{b} .\n" for a, b in EDGES)

print(f"노드 {len(NODES)}개, 엣지 {len(EDGES)}개")
print(NODES)
# 출력: 노드 12개, 엣지 11개
# 출력: ['B1', 'B2', 'N0', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7', 'N8', 'X1']

# %%
if HAS_KUZU:
    _tmp = tempfile.mkdtemp()
    conn = kuzu.Connection(kuzu.Database(f"{_tmp}/db"))
    conn.execute("CREATE NODE TABLE Co(name STRING, PRIMARY KEY(name))")
    conn.execute("CREATE REL TABLE ParentOf(FROM Co TO Co)")
    for n in NODES:
        conn.execute(f"CREATE (:Co {{name:'{n}'}})")
    for a, b in EDGES:
        conn.execute(f"MATCH (x:Co {{name:'{a}'}}), (y:Co {{name:'{b}'}}) "
                     f"CREATE (x)-[:ParentOf]->(y)")


def cypher_pairs(q):
    r = conn.execute(q)
    out = []
    while r.has_next():
        out.append(tuple(r.get_next()))
    return sorted(out)


if HAS_RDFLIB:
    g = Graph().parse(data=TTL, format="turtle")


def sparql_pairs(q):
    return sorted(tuple(str(x) for x in row) for row in g.query(q))


print("적재 완료")
# 출력: 적재 완료

# %% [markdown]
# ## 2단계 — Cypher는 상한을 «쓸 수 있다»
#
# | 표기 | 뜻 |
# |---|---|
# | `-[:ParentOf]->` | 정확히 1홉 |
# | `-[:ParentOf*1..3]->` | 1홉 이상 3홉 **이하** |
# | `-[:ParentOf*3]->` | 정확히 3홉 |
# | `-[:ParentOf*..5]->` | 1~5홉 (하한 생략 = 1) |
# | `-[:ParentOf*2..]->` | 2홉 이상 (상한 생략 = 엔진 기본값) |
# | `-[:ParentOf*]->` | 하한·상한 모두 엔진 기본값 |
#
# 핵심은 `*1..3`의 `3`이다. **질의문 안에** 홉 상한이 들어간다.

# %%
if HAS_KUZU:
    for k in (1, 2, 3, 30):
        q = (f"MATCH (a:Co)-[:ParentOf*1..{k}]->(b:Co) "
             f"RETURN a.name, b.name ORDER BY a.name, b.name")
        rows = cypher_pairs(q)
        tag = "(실질 무제한)" if k == 30 else ""
        print(f"  *1..{k:<2} → {len(rows):3d}행 {tag}")
# 출력:   *1..1  →  11행
# 출력:   *1..2  →  20행
# 출력:   *1..3  →  27행
# 출력:   *1..30 →  42행 (실질 무제한)
#
# 검산: 사슬 8홉이 8*9/2 = 36쌍, B 분기 3쌍, X1 분기 3쌍 → 42쌍.

# %% [markdown]
# ## 3단계 — SPARQL은 상한을 «쓸 수 없다»
#
# SPARQL 1.1 property path 연산자는 이게 전부다.
#
# | 표기 | 이름 | 뜻 | 중복 |
# |---|---|---|---|
# | `iri` | PredicatePath | 길이 1 |  |
# | `^elt` | InversePath | 역방향 |  |
# | `elt1/elt2` | SequencePath | 이어붙이기 | 보존 |
# | `elt1\|elt2` | AlternativePath | 둘 중 하나 | 보존 |
# | `elt*` | ZeroOrMorePath | 0회 이상 | **제거** |
# | `elt+` | OneOrMorePath | 1회 이상 | **제거** |
# | `elt?` | ZeroOrOnePath | 0회 또는 1회 | **제거** |
# | `!iri` | NegatedPropertySet | 목록 밖의 술어 | 보존 |
# | `(elt)` | GroupPath | 우선순위 묶음 |  |
#
# `{1,3}` 같은 **횟수 표기가 목록에 없다**. `+`는 «1회 이상»뿐이므로
# `*1..3`에 대응하는 표기가 존재하지 않는다.

# %%
if HAS_RDFLIB:
    Q_ONE = """PREFIX ex: <http://example.org/>
               SELECT ?a ?b WHERE { ?x ex:parentOf ?y . ?x ex:name ?a . ?y ex:name ?b }"""
    Q_PLUS = """PREFIX ex: <http://example.org/>
                SELECT ?a ?b WHERE { ?x ex:parentOf+ ?y . ?x ex:name ?a . ?y ex:name ?b }"""
    Q_STAR = """PREFIX ex: <http://example.org/>
                SELECT ?a ?b WHERE { ?x a ex:Co . ?x ex:parentOf* ?y .
                                     ?x ex:name ?a . ?y ex:name ?b }"""

    one, plus, star = sparql_pairs(Q_ONE), sparql_pairs(Q_PLUS), sparql_pairs(Q_STAR)
    print(f"  ex:parentOf   → {len(one):3d}행  (1홉)")
    print(f"  ex:parentOf+  → {len(plus):3d}행  (1홉 이상 = 전이 폐쇄)")
    print(f"  ex:parentOf*  → {len(star):3d}행  (0홉 포함 → 자기 자신 {len(star) - len(plus)}쌍 추가)")
# 출력:   ex:parentOf   →  11행  (1홉)
# 출력:   ex:parentOf+  →  42행  (1홉 이상 = 전이 폐쇄)
# 출력:   ex:parentOf*  →  54행  (0홉 포함 → 자기 자신 12쌍 추가)
#
# Cypher *1..30 과 SPARQL + 가 42행으로 정확히 일치한다.
# «무제한»에서는 두 언어가 같은 답을 낸다. 갈리는 건 «상한»뿐이다.

# %% [markdown]
# 여기서 대응이 딱 보인다.
#
# | | 1홉 | 1~3홉 | 무제한 |
# |---|---|---|---|
# | Cypher | `*1..1` → 11행 | `*1..3` → **27행** | `*1..30` → 42행 |
# | SPARQL | `ex:parentOf` → 11행 | **표기 없음** | `ex:parentOf+` → 42행 |
#
# 양 끝은 같은 답을 낸다. 가운데 칸만 SPARQL에 없다.
# 그리고 `+`가 내는 42행은 `*1..3`의 27행보다 **56% 많다**.
# 사슬이 길어지면 이 배수가 커진다(4단계).

# %% [markdown]
# ## 4단계 — 상한이 없으면 결과가 «이차»로 자란다
#
# 사슬 길이 $d$를 늘려 가며 $|R_{\le k}(d)|$와 $|R_{+}(d)|$를 실제로 세어 본다.
# 앞의 식대로라면 $k$ 고정은 선형, `+`는 이차여야 한다.

# %%
def chain_ttl(d):
    ns = [f"C{i}" for i in range(d + 1)]
    t = "@prefix ex: <http://example.org/> .\n"
    t += "".join(f"ex:{a} ex:parentOf ex:{b} .\n" for a, b in zip(ns, ns[1:]))
    return t


DEPTHS = list(range(1, 17))
counts = {1: [], 2: [], 3: [], "plus": []}

for d in DEPTHS:
    gd = Graph().parse(data=chain_ttl(d), format="turtle") if HAS_RDFLIB else None
    if HAS_RDFLIB:
        n = len(set(gd.query(
            "PREFIX ex: <http://example.org/> "
            "SELECT DISTINCT ?x ?y WHERE { ?x ex:parentOf+ ?y }")))
        counts["plus"].append(n)
    else:
        counts["plus"].append(d * (d + 1) // 2)
    for k in (1, 2, 3):
        counts[k].append(sum(d + 1 - j for j in range(1, min(k, d) + 1)))

print("  d   k=1  k=2  k=3   +      +/k=3")
for i, d in enumerate(DEPTHS):
    p = counts["plus"][i]
    print(f" {d:2d}  {counts[1][i]:4d} {counts[2][i]:4d} {counts[3][i]:4d} "
          f"{p:5d}   {p / counts[3][i]:5.2f}x")
# 출력:   d   k=1  k=2  k=3   +      +/k=3
# 출력:   1     1    1    1     1    1.00x
# 출력:   2     2    3    3     3    1.00x
# 출력:   3     3    5    6     6    1.00x
# 출력:   4     4    7    9    10    1.11x
# 출력:   5     5    9   12    15    1.25x
# 출력:   6     6   11   15    21    1.40x
# 출력:   7     7   13   18    28    1.56x
# 출력:   8     8   15   21    36    1.71x
# 출력:   9     9   17   24    45    1.88x
# 출력:  10    10   19   27    55    2.04x
# 출력:  11    11   21   30    66    2.20x
# 출력:  12    12   23   33    78    2.36x
# 출력:  13    13   25   36    91    2.53x
# 출력:  14    14   27   39   105    2.69x
# 출력:  15    15   29   42   120    2.86x
# 출력:  16    16   31   45   136    3.02x
#
# 검증: rdflib 실측값이 d(d+1)/2와 정확히 일치한다.
# d=16에서 이미 3배. d=100이면 5050 vs 297로 17배가 된다.

# %% [markdown]
# ## 5단계 — SPARQL에서 상한을 흉내 내는 우회로
#
# 표기가 없으니 «펼쳐 쓴다». 1~3홉은 `p | p/p | p/p/p`.
#
# 다만 함정이 있다. SPARQL 1.1은 `*`, `+`, `?`만 **중복을 제거**하고
# `/`, `|`, `!`는 **중복을 보존**한다. 그래서 펼친 질의는
# 1홉이면서 동시에 2홉인 쌍(분기·다중 경로가 있을 때)을 여러 번 낸다.
# `SELECT DISTINCT`를 반드시 붙여야 `*1..3`과 행 수가 맞는다.

# %%
if HAS_RDFLIB:
    P = "ex:parentOf"
    unrolled = " | ".join("/".join([P] * i) for i in (1, 2, 3))

    q_bag = (f"PREFIX ex: <http://example.org/>\n"
             f"SELECT ?a ?b WHERE {{ ?x {unrolled} ?y . ?x ex:name ?a . ?y ex:name ?b }}")
    q_set = q_bag.replace("SELECT ?a ?b", "SELECT DISTINCT ?a ?b")

    n_bag = len(list(g.query(q_bag)))
    n_set = len(list(g.query(q_set)))
    print(f"  펼침 (DISTINCT 없음) → {n_bag}행  ← |,/ 는 중복을 보존한다")
    print(f"  펼침 (DISTINCT)      → {n_set}행")
    print(f"  Cypher *1..3         → 27행")
    print(f"  일치? {n_set == 27}")
# 출력:   펼침 (DISTINCT 없음) → 27행  ← |,/ 는 중복을 보존한다
# 출력:   펼침 (DISTINCT)      → 27행
# 출력:   Cypher *1..3         → 27행
# 출력:   일치? True
#
# 참고: 이 그래프는 두 노드 사이 경로가 유일해서 bag/set 행 수가 같다.
#       다중 경로(다이아몬드)를 넣으면 갈라진다 → 6단계.

# %%
# 다중 경로를 넣어 중복 보존이 실제로 문제가 되는지 본다.
# D0 -> D1 -> D3,  D0 -> D2 -> D3  (D0에서 D3까지 2홉 경로가 두 개)
DIAMOND = """@prefix ex: <http://example.org/> .
ex:D0 ex:parentOf ex:D1 . ex:D0 ex:parentOf ex:D2 .
ex:D1 ex:parentOf ex:D3 . ex:D2 ex:parentOf ex:D3 .
"""
if HAS_RDFLIB:
    gd = Graph().parse(data=DIAMOND, format="turtle")
    unr = " | ".join("/".join(["ex:parentOf"] * i) for i in (1, 2, 3))
    for label, q in (
        ("+ (중복 제거)", "SELECT ?x ?y WHERE { ?x ex:parentOf+ ?y }"),
        ("펼침 (bag)", f"SELECT ?x ?y WHERE {{ ?x {unr} ?y }}"),
        ("펼침 (DISTINCT)", f"SELECT DISTINCT ?x ?y WHERE {{ ?x {unr} ?y }}"),
    ):
        rows = list(gd.query("PREFIX ex: <http://example.org/> " + q))
        print(f"  {label:<18} {len(rows)}행")
# 출력:   + (중복 제거)          5행
# 출력:   펼침 (bag)           6행
# 출력:   펼침 (DISTINCT)      5행
#
# bag 6행 = (D0,D3)이 두 경로 때문에 두 번. 상한 우회로에 DISTINCT가 왜 필수인지.

# %% [markdown]
# ## 6단계 — 그림으로
#
# 왼쪽: 사슬 깊이가 늘 때 상한 있는 질의(선형)와 `+`(이차)의 결과 행 수.
# 오른쪽: 예제 그래프에서 홉 수별 새로 늘어나는 쌍의 누적. `*1..3` 선이 어디서 끊기고
# `+`가 어디까지 가는지.

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

if HAS_PLOTLY:
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("사슬 깊이 d 대비 결과 행 수",
                        "예제 그래프: 홉 상한별 누적 쌍 수"),
    )

    PAL = {1: "#8C9BAB", 2: "#5B8FF9", 3: "#1F6FEB", "plus": "#D9534F"}
    for k in (1, 2, 3):
        fig.add_trace(go.Scatter(x=DEPTHS, y=counts[k], mode="lines+markers",
                                 name=f"상한 k={k} (선형)",
                                 line=dict(color=PAL[k], width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=DEPTHS, y=counts["plus"], mode="lines+markers",
                             name="ex:parentOf+ (이차)",
                             line=dict(color=PAL["plus"], width=3)), row=1, col=1)

    # 오른쪽: 예제 그래프의 홉별 누적 (kuzu 실측, 없으면 BFS 계산)
    ks = list(range(1, 9))
    if HAS_KUZU:
        cum = [len(cypher_pairs(f"MATCH (a:Co)-[:ParentOf*1..{k}]->(b:Co) "
                                f"RETURN a.name, b.name")) for k in ks]
    else:
        adj = {}
        for a, b in EDGES:
            adj.setdefault(a, []).append(b)
        cum, front, seen = [], {n: {n} for n in NODES}, set()
        for _ in ks:
            nxt = {}
            for s, cur in front.items():
                nx = {y for x in cur for y in adj.get(x, [])}
                nxt[s] = nx
                seen |= {(s, y) for y in nx}
            front = nxt
            cum.append(len(seen))

    fig.add_trace(go.Bar(x=[f"*1..{k}" for k in ks], y=cum, name="Cypher 표기 가능",
                         marker_color=["#1F6FEB"] * 3 + ["#C6D4E3"] * 5,
                         showlegend=False), row=1, col=2)
    fig.add_hline(y=cum[-1], line=dict(color=PAL["plus"], dash="dash", width=2),
                  annotation_text=f"ex:parentOf+ = {cum[-1]}행 (상한 표기 불가)",
                  annotation_position="top left", row=1, col=2)

    fig.update_xaxes(title_text="사슬 깊이 d", row=1, col=1)
    fig.update_xaxes(title_text="Cypher 홉 상한", row=1, col=2)
    fig.update_yaxes(title_text="결과 행 수", row=1, col=1)
    fig.update_yaxes(title_text="누적 쌍 수", row=1, col=2)
    fig.update_layout(
        title="상한을 쓸 수 있느냐가 결과 크기를 정한다 — Cypher *1..k vs SPARQL +",
        template="plotly_white", height=460, width=1100,
        legend=dict(orientation="h", y=-0.18),
        font=dict(family="AppleGothic, Apple SD Gothic Neo, NanumGothic, sans-serif"),
    )
    _show(fig)
    out = os.path.join(HERE, "expy.png")
    fig.write_image(out, scale=2)      # kaleido 필요
    print(f"저장: {out}")
# 출력: 저장: .../expy.png

# %% [markdown]
# ## 정리
#
# | | Cypher | SPARQL 1.1 |
# |---|---|---|
# | 1홉 이상 | `*1..` / `*` | `+` |
# | 0홉 이상 | (별도 표기 필요) | `*` |
# | 0 또는 1홉 | `*0..1` | `?` |
# | **1~3홉** | **`*1..3`** | **표기 없음** |
# | 정확히 3홉 | `*3` | `p/p/p` |
# | 우회로 | 불필요 | `p\|p/p\|p/p/p` + `DISTINCT`, 타임아웃, `LIMIT` |
#
# - SPARQL 초안에는 `{n}`, `{n,m}`, `{n,}`, `{,m}`이 있었는데 표준에서 빠졌다.
#   중복 보존/제거 semantics를 어떻게 정할지 경험이 부족했고, 경로 개수 세기의
#   복잡도가 문제였다(2012-04-12 W3C SPARQL WG). README.md 참조.
# - 역설: 2024년 GQL 표준이 채택한 정량 경로 패턴 표기가 바로 `{1,3}`이다.
#   SPARQL이 버린 중괄호를 그래프 질의 표준이 되찾아 왔다.

# %%
if HAS_KUZU:
    shutil.rmtree(_tmp, ignore_errors=True)
    print("정리 완료")
# 출력: 정리 완료
