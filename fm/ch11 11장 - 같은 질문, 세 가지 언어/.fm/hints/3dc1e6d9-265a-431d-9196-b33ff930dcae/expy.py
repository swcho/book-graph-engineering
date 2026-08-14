# %% [markdown]
# # `gremlin_style()` 는 무엇을 흉내 내는가
#
# 11장 `ex1_three_languages.py` 의 `gremlin_style()` 은 **Gremlin 엔진 없이**
# Gremlin 의 *순회 사고*(traversal thinking)를 파이썬으로 흉내 낸 함수다.
#
# | 언어 | 비유 | 대표 표기 | 성격 |
# |---|---|---|---|
# | Cypher | 그림 | `(c)-[:Signed]->(n)` | 선언형 |
# | SPARQL | 문장 | `?c ex:signed ?n .` | 선언형 |
# | **Gremlin** | **걸음** | `.out('signed')` | **명령형에 가깝다** |
#
# 책의 원본 함수는 주석으로 대응 관계를 박아 놓았다.
#
# ```python
# for company, end in ended.items():          # .hasLabel('Company').out('terminated')
#     for start in started.get(company, []):  # .in().out('signed')
#         if end < start:                     # .where(...)
#             out.append(company)
# ```
#
# 즉 **`for` 루프 한 겹 = 순회 단계(step) 하나**. 이 노트북은 그 대응을
# 눈에 보이게 만들려고, 체이닝 가능한 아주 작은 순회 클래스를 직접 만든다.
#
# 필요 패키지: plotly, kaleido (시각화용. 없으면 앞부분 셀만 돌려도 개념은 전부 보인다)

# %%
# 필요 패키지: plotly, kaleido
from collections import defaultdict


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1. 데이터 — 11장 `seed.py` 와 같은 사실
#
# 답해야 할 질문: **「해지했다가 그 뒤에 다시 계약한 고객은?」**

# %%
COMPANIES = [("가온테크", "A"), ("나루소프트", "B"), ("라온에너지", "C"), ("다올물산", "B")]
CONTRACTS = [
    ("M-2021-077", None, "2024-03-11"),
    ("C-2025-118", "2025-06-02", None),
    ("C-2025-004", "2025-01-20", None),
    ("M-2020-031", None, "2024-08-05"),
    ("C-2026-010", "2026-02-01", None),
]
SIGNED = [("가온테크", "C-2025-118"), ("나루소프트", "C-2025-004"),
          ("다올물산", "C-2026-010")]
TERMINATED = [("가온테크", "M-2021-077"), ("라온에너지", "M-2020-031")]

# 정점 = {id: (label, props)}  — 그래프 DB 의 노드 테이블에 해당
VERTICES = {}
for name, grade in COMPANIES:
    VERTICES[name] = ("Company", {"name": name, "grade": grade})
for cid, started, ended in CONTRACTS:
    VERTICES[cid] = ("Contract", {"id": cid, "startedOn": started, "endedOn": ended})

# 간선 = {(라벨, 출발): [도착, ...]}  — «인접 리스트». 순회의 전부다
EDGES = defaultdict(list)
for a, b in SIGNED:
    EDGES[("signed", a)].append(b)
for a, b in TERMINATED:
    EDGES[("terminated", a)].append(b)

# 역방향 색인. Gremlin 의 .in() 이 이걸 쓴다
EDGES_IN = defaultdict(list)
for (lab, a), bs in EDGES.items():
    for b in bs:
        EDGES_IN[(lab, b)].append(a)

print("정점", len(VERTICES), "개 / 간선", sum(len(v) for v in EDGES.values()), "개")
print("가온테크 의 out('terminated') =", EDGES[("terminated", "가온테크")])
# 출력: 정점 9 개 / 간선 5 개
# 출력: 가온테크 의 out('terminated') = ['M-2021-077']

# %% [markdown]
# ## 2. 아주 작은 순회 엔진
#
# Gremlin 순회의 상태는 **트래버서(traverser) 집합**이다. 여기서는 한 트래버서를
# `{"_": 현재정점, 별칭: 정점, ...}` 딕셔너리로 둔다. 단계(step)는 이 집합을
# 다른 집합으로 바꾸는 함수일 뿐이다.
#
# $$\text{frontier}_{k+1} \;=\; \mathrm{step}_k(\text{frontier}_k)$$
#
# - `hasLabel` / `has` / `where_` → **필터** (집합이 줄어든다)
# - `out` / `in_` → **평탄화 사상**(flatMap, 집합이 늘거나 줄거나)
# - `as_` / `select` → **경로 기억과 되돌아가기** (움직이지 않는다)

# %%
class Traversal:
    """체이닝 가능한 순회. 각 단계마다 프론티어를 기록한다."""

    def __init__(self, rows, trace=None, log=True):
        self.rows = rows
        self.trace = [] if trace is None else trace
        self._log = log

    def _next(self, name, rows):
        t = Traversal(rows, self.trace, self._log)
        t.trace.append((name, [r["_"] for r in rows]))
        return t

    # --- 시작 단계 ---
    @classmethod
    def V(cls, log=True):
        t = cls([{"_": v} for v in VERTICES], [], log)
        t.trace.append(("V()", list(VERTICES)))
        return t

    # --- 필터 단계 ---
    def hasLabel(self, label):
        return self._next(f".hasLabel('{label}')",
                          [r for r in self.rows if VERTICES[r["_"]][0] == label])

    def where_(self, pred, name=".where(...)"):
        return self._next(name, [r for r in self.rows if pred(r)])

    # --- 이동 단계 ---
    def out(self, edge):
        rows = [dict(r, _=dst) for r in self.rows for dst in EDGES[(edge, r["_"])]]
        return self._next(f".out('{edge}')", rows)

    def in_(self, edge):
        rows = [dict(r, _=src) for r in self.rows for src in EDGES_IN[(edge, r["_"])]]
        return self._next(f".in('{edge}')", rows)

    # --- 경로 단계 (제자리) ---
    def as_(self, name):
        return self._next(f".as('{name}')", [dict(r, **{name: r["_"]}) for r in self.rows])

    def select(self, name):
        return self._next(f".select('{name}')", [dict(r, _=r[name]) for r in self.rows])

    # --- 종결 단계 ---
    def values(self, prop):
        return sorted({VERTICES[r["_"]][1][prop] for r in self.rows})

    def dedup(self):
        seen, rows = set(), []
        for r in self.rows:
            if r["_"] not in seen:
                seen.add(r["_"])
                rows.append(r)
        return self._next(".dedup()", rows)

    def toList(self):
        return [r["_"] for r in self.rows]


def prop(vid, key):
    return VERTICES[vid][1][key]


# %% [markdown]
# ## 3. 걸어 본다 — 단계마다 프론티어가 어떻게 변하는가
#
# Gremlin 이라면 이렇게 쓴다.
#
# ```groovy
# g.V().hasLabel('Company').as('c')
#      .out('terminated').as('o')
#      .select('c').out('signed').as('n')
#      .where('o', lt('n')).by('endedOn').by('startedOn')
#      .select('c').dedup().values('name')
# ```

# %%
t = (Traversal.V()
     .hasLabel("Company").as_("c")
     .out("terminated").as_("o")
     .select("c")
     .out("signed").as_("n")
     .where_(lambda r: prop(r["o"], "endedOn") < prop(r["n"], "startedOn"),
             ".where(o.endedOn < n.startedOn)")
     .select("c")
     .dedup())

for i, (step, frontier) in enumerate(t.trace):
    print(f"{i}  {step:<34} {len(frontier)}개  {frontier}")
print("\n답:", t.values("name"))
# 출력:
# 0  V()                                9개  ['가온테크', '나루소프트', '라온에너지', '다올물산', 'M-2021-077', 'C-2025-118', 'C-2025-004', 'M-2020-031', 'C-2026-010']
# 1  .hasLabel('Company')               4개  ['가온테크', '나루소프트', '라온에너지', '다올물산']
# 2  .as('c')                           4개  ['가온테크', '나루소프트', '라온에너지', '다올물산']
# 3  .out('terminated')                 2개  ['M-2021-077', 'M-2020-031']
# 4  .as('o')                           2개  ['M-2021-077', 'M-2020-031']
# 5  .select('c')                       2개  ['가온테크', '라온에너지']
# 6  .out('signed')                     1개  ['C-2025-118']
# 7  .as('n')                           1개  ['C-2025-118']
# 8  .where(o.endedOn < n.startedOn)    1개  ['C-2025-118']
# 9  .select('c')                       1개  ['가온테크']
# 10  .dedup()                           1개  ['가온테크']
#
# 답: ['가온테크']

# %% [markdown]
# 볼 것 세 가지.
#
# 1. `.out('terminated')` 에서 **4 → 2** 로 줄었다. 해지 이력이 없는 회사는 여기서 탈락한다.
#    필터를 안 썼는데도 이동 자체가 필터로 동작한다.
# 2. `.select('c')` 는 **움직이지 않는다**. 아까 `.as('c')` 로 기억해 둔 회사로 되돌아온다.
#    책의 주석 `# .in().out('signed')` 가 뜻하는 「되돌아가기」가 이것이다.
#    (역간선을 타고 `.in('terminated')` 로 돌아가도 같은 결과가 나온다.)
# 3. `.where(...)` 는 **이미 좁혀진 1개**만 검사한다. 순서를 내가 정했으니까.
#
# ## 4. 책의 원본 함수와 나란히
#
# 원본은 클래스 없이 `for` 루프 두 겹 + `if` 한 줄로 같은 순회를 한다.

# %%
def gremlin_style():
    """책 원본. 딕셔너리가 인접 리스트, for 루프가 이동 단계다."""
    ended = {a: next(e for c, s, e in CONTRACTS if c == b) for a, b in TERMINATED}
    started = defaultdict(list)
    for a, b in SIGNED:
        started[a].append(next(s for c, s, e in CONTRACTS if c == b))
    out = []
    for company, end in ended.items():          # .hasLabel('Company').out('terminated')
        for start in started.get(company, []):  # .in().out('signed')
            if end < start:                     # .where(...)
                out.append(company)
    return sorted(set(out))                     # .dedup().values('name')


print("원본 gremlin_style() :", gremlin_style())
print("순회 클래스          :", t.values("name"))
print("같은가:", gremlin_style() == t.values("name"))
# 출력: 원본 gremlin_style() : ['가온테크']
# 출력: 순회 클래스          : ['가온테크']
# 출력: 같은가: True

# %% [markdown]
# ## 5. 대조 — 같은 답을 선언형으로 쓰면
#
# 선언형(Cypher/SPARQL)의 사고는 「**조건을 만족하는 모양**을 적는다」다.
# 파이썬으로 흉내 내면 집합 컴프리헨션 한 줄이 된다. 순서가 사라진 게 핵심이다.

# %%
declarative = sorted({
    c
    for c, o in TERMINATED          # 패턴: (c)-[:Terminated]->(o)
    for c2, n in SIGNED             # 패턴: (c)-[:Signed]->(n)
    if c == c2                      # 같은 c 로 묶는다 (조인)
    and prop(o, "endedOn") < prop(n, "startedOn")   # WHERE
})
print("선언형(컴프리헨션):", declarative)
print("명령형(순회)      :", t.values("name"))
# 출력: 선언형(컴프리헨션): ['가온테크']
# 출력: 명령형(순회)      : ['가온테크']

# %% [markdown]
# 두 코드의 차이가 곧 두 언어관의 차이다.
#
# - **선언형**: `TERMINATED × SIGNED` 를 전부 훑는 것처럼 써 놓았다.
#   실제로 어느 쪽부터 훑을지는 **엔진(최적화기)** 이 정한다. 여기서는 파이썬이
#   써 있는 그대로 $|T| \times |S| = 2 \times 3 = 6$ 쌍을 검사한다.
# - **명령형(순회)**: 「Company 부터 → 해지 계약으로 → 되돌아와 → 신규 계약으로」라는
#   **순서를 내가 정했다**. 그래서 마지막 비교는 1번만 했다.
#
# 그래서 Gremlin 은 세밀한 제어가 되고, 대신 최적화기가 도와줄 여지가 적다.

# %%
# 두 방식이 실제로 몇 번 비교했는지 세어 본다
decl_cmp = sum(1 for c, o in TERMINATED for c2, n in SIGNED)
trav_cmp = len([r for (s, f) in t.trace if s.startswith(".where") for r in f])
print(f"선언형 컴프리헨션이 훑은 쌍   : {decl_cmp}")
print(f"순회가 .where 에 도달시킨 쌍 : {trav_cmp}")
# 출력: 선언형 컴프리헨션이 훑은 쌍   : 6
# 출력: 순회가 .where 에 도달시킨 쌍 : 1

# %% [markdown]
# ## 6. 프론티어 크기를 그림으로
#
# 순회는 **깔때기**다. 단계마다 트래버서 집합이 어떻게 변했는지 본다.

# %%
try:
    import plotly.graph_objects as go

    steps = [s for s, _ in t.trace]
    sizes = [len(f) for _, f in t.trace]
    members = ["<br>".join(f) for _, f in t.trace]
    KIND = {"V()": "시작", ".hasLabel": "필터", ".where": "필터",
            ".out": "이동", ".in": "이동", ".as": "제자리",
            ".select": "제자리", ".dedup": "제자리"}
    palette = {"시작": "#8899aa", "필터": "#d9822b", "이동": "#2c7fb8", "제자리": "#bfc7d1"}

    def kind(s):
        for k, v in KIND.items():
            if s.startswith(k):
                return v
        return "제자리"

    kinds = [kind(s) for s in steps]
    fig = go.Figure()
    for k in ("시작", "이동", "필터", "제자리"):
        idx = [i for i, kk in enumerate(kinds) if kk == k]
        if not idx:
            continue
        fig.add_bar(
            x=[f"{i}. {steps[i]}" for i in idx],
            y=[sizes[i] for i in idx],
            name=k, marker_color=palette[k],
            text=[sizes[i] for i in idx], textposition="outside",
            customdata=[members[i] for i in idx],
            hovertemplate="<b>%{x}</b><br>프론티어 %{y}개<br>%{customdata}<extra></extra>",
        )
    fig.update_layout(
        title="Gremlin 식 순회의 프론티어 — 단계마다 트래버서가 몇 개 남는가",
        xaxis_title="순회 단계 (step)", yaxis_title="프론티어 크기",
        barmode="overlay", template="plotly_white",
        height=460, width=1000, legend_title="단계 종류",
    )
    fig.update_xaxes(tickangle=-35, categoryorder="array",
                     categoryarray=[f"{i}. {s}" for i, s in enumerate(steps)])
    fig.update_yaxes(range=[0, 11])
    fig.add_annotation(x="3. .out('terminated')", y=2.4, ax=60, ay=-80,
                       text="이동이 곧 필터<br>(해지 이력 없는 회사 탈락)",
                       showarrow=True, arrowhead=2, font=dict(size=11))
    _show(fig)
    fig.write_image("expy.png", scale=2)
    print("expy.png 저장")
except ImportError as e:
    print("시각화 건너뜀:", e)
# 출력: expy.png 저장

# %% [markdown]
# ## 정리
#
# - `gremlin_style()` 은 **Gremlin 의 순회 사고를 파이썬으로 구현**한 것이다.
#   엔진(Gremlin Server / TinkerPop)이 필요해서 실제 Gremlin 을 못 돌리는 대신,
#   문법이 아니라 **사고 방식**이 다르다는 걸 보여 준다.
# - `.hasLabel('Company').out('terminated')` 같은 **단계별 이동을 `for` 루프로** 표현한다.
#   인접 리스트(딕셔너리) 조회가 `.out()`, 루프 중첩이 단계 연결, `if` 가 `.where()` 다.
# - 프론티어(중간 정점 집합)가 단계마다 줄었다 늘었다 하는 걸 내가 눈으로 좇을 수 있다.
#   그게 명령형 순회의 장점이자, 최적화기가 끼어들 자리가 없다는 대가다.
