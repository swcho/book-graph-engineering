# %% [markdown]
# # `ex1`의 2홉 선호 수집 질의 뜯어보기
#
# **질문**: `ex1`의 그래프 질의는 어떻게 팀원의 선호를 모으는가?
#
# **답**: `(팀)<-[:R]-(사람)-[e:R]->(선호)` 2홉 패턴으로 팀에 속한 사람들의
# `Pref` 노드를 `DISTINCT`로 모은다.
#
# 원본 질의(`ex1_memory_shapes.py`의 `graph_search`):
#
# ```cypher
# MATCH (t:N {name:'결제팀'})<-[:R]-(p:N)-[e:R]->(pref:N)
# WHERE pref.kind='Pref'
# RETURN DISTINCT pref.name
# ```
#
# 「회식 장소를 정할 때 피해야 할 것은?」이라는 질문에 답하려면
# *팀 → 팀원 → 그 사람의 선호* 를 따라가야 한다.
# 이 경로는 사실을 저장할 때는 존재하지 않았다. 질문이 들어온 뒤에 만들어진다.
#
# 필요 패키지: kuzu, plotly, kaleido (없으면 해당 셀만 건너뛴다)

# %%
import os
import shutil
import tempfile

import kuzu


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
print("kuzu", kuzu.__version__)
# 출력: kuzu 0.11.3

# %% [markdown]
# ## 1. 같은 사실을 그래프 모양으로
#
# `ex1`은 노드 테이블을 `N` 하나, 관계 테이블을 `R` 하나만 둔다.
# 「사람인가 선호인가」는 **라벨이 아니라 `kind` 속성**으로 구분한다.
# 이 설계 때문에 질의에서 `WHERE pref.kind='Pref'` 같은 속성 필터가 필요해진다.

# %%
NODES = [
    ("나", "Person"),
    ("박민수", "Person"),
    ("이서연", "Person"),
    ("결제팀", "Team"),
    ("강남", "Place"),
    ("마포", "Place"),
    ("매운맛", "Pref"),
    ("채식", "Pref"),
]
EDGES = [
    ("나", "결제팀", "속함"),
    ("박민수", "결제팀", "이끔"),
    ("이서연", "결제팀", "속함"),
    ("나", "강남", "일함"),
    ("이서연", "마포", "삶"),
    ("박민수", "매운맛", "못먹음"),
    ("나", "채식", "선호"),
]


def build(path, nodes=NODES, edges=EDGES):
    db = kuzu.Database(path)
    c = kuzu.Connection(db)
    c.execute("CREATE NODE TABLE N(name STRING, kind STRING, PRIMARY KEY(name))")
    c.execute("CREATE REL TABLE R(FROM N TO N, kind STRING)")
    for n, k in nodes:
        c.execute("CREATE (:N {name:$n, kind:$k})", {"n": n, "k": k})
    for a, b, k in edges:
        c.execute(
            "MATCH (x:N {name:$a}), (y:N {name:$b}) CREATE (x)-[:R {kind:$k}]->(y)",
            {"a": a, "b": b, "k": k},
        )
    return c


def rows(res):
    out = []
    while res.has_next():
        out.append(res.get_next())
    return out


tmp = tempfile.mkdtemp()
conn = build(tmp + "/db")
print(f"노드 {len(NODES)}개, 간선 {len(EDGES)}개 적재 완료")
# 출력: 노드 8개, 간선 7개 적재 완료

# %% [markdown]
# ## 2. 홉을 하나씩 밟아 본다
#
# 2홉 패턴은 한 번에 이해하려 들면 방향 화살표가 헷갈린다.
# 왼쪽 홉과 오른쪽 홉을 따로 실행해 보면 명확해진다.
#
# ### 왼쪽 홉 — `(t:N {name:'결제팀'})<-[:R]-(p:N)`
#
# 간선은 *사람 → 팀* 방향으로 저장돼 있다(`속함`, `이끔`).
# 그래서 팀을 기준점으로 잡으면 화살표가 **들어오는** 방향(`<-`)이 된다.

# %%
hop1 = rows(conn.execute("MATCH (t:N {name:'결제팀'})<-[e:R]-(p:N) RETURN p.name, e.kind"))
print("1홉 (팀원):", hop1)
# 출력: 1홉 (팀원): [['나', '속함'], ['박민수', '이끔'], ['이서연', '속함']]

# 방향을 잘못 쓰면 아무것도 안 나온다 — 화살표 방향이 곧 의미다
wrong = rows(conn.execute("MATCH (t:N {name:'결제팀'})-[:R]->(p:N) RETURN p.name"))
print("방향 뒤집었을 때:", wrong)
# 출력: 방향 뒤집었을 때: []

# %% [markdown]
# ### 오른쪽 홉 — `(p:N)-[e:R]->(pref:N)` + `WHERE pref.kind='Pref'`
#
# 사람에서 **나가는** 간선을 전부 따라간 뒤, 도착 노드의 `kind`가 `Pref`인 것만 남긴다.
# 간선 `kind`는 제한하지 않는다는 점이 중요하다.
# `선호`(먹고 싶다)와 `못먹음`(못 먹는다)이 **둘 다** 걸린다.
# 질문이 「피해야 할 것」이므로 두 종류 모두 회피 후보이기 때문이다.

# %%
for person, _ in hop1:
    out = rows(conn.execute("MATCH (p:N {name:$n})-[e:R]->(x:N) RETURN x.name, x.kind, e.kind", {"n": person}))
    keep = [(a, c) for a, b, c in out if b == "Pref"]
    print(f"{person:<4} 나가는 간선 {out}  → Pref만: {keep}")
# 출력: 나   나가는 간선 [['결제팀', 'Team', '속함'], ['강남', 'Place', '일함'], ['채식', 'Pref', '선호']]  → Pref만: [('채식', '선호')]
# 출력: 박민수  나가는 간선 [['결제팀', 'Team', '이끔'], ['매운맛', 'Pref', '못먹음']]  → Pref만: [('매운맛', '못먹음')]
# 출력: 이서연  나가는 간선 [['결제팀', 'Team', '속함'], ['마포', 'Place', '삶']]  → Pref만: []

# %% [markdown]
# ## 3. 두 홉을 붙인 원본 질의
#
# 한 패턴 안에서 `(t)<-[:R]-(p)-[e:R]->(pref)` 로 이어 쓰면
# 가운데 `p`가 두 홉을 잇는 **연결 변수**가 된다.
# 「팀에 속하면서 동시에 선호를 가진 사람」만 자동으로 남는다.

# %%
Q = (
    "MATCH (t:N {name:'결제팀'})<-[:R]-(p:N)-[e:R]->(pref:N) "
    "WHERE pref.kind='Pref' "
    "RETURN DISTINCT pref.name"
)
print("원본 질의 결과:", [r[0] for r in rows(conn.execute(Q))])
# 출력: 원본 질의 결과: ['매운맛', '채식']   (순서는 보장되지 않는 집합이다)

# 누가 왜 걸렸는지 함께 보기 (DISTINCT 없이 경로 그대로)
detail = rows(
    conn.execute(
        "MATCH (t:N {name:'결제팀'})<-[:R]-(p:N)-[e:R]->(pref:N) "
        "WHERE pref.kind='Pref' RETURN p.name, e.kind, pref.name"
    )
)
for a, b, c in detail:
    print(f"  결제팀 <- {a} -[{b}]-> {c}")
# 출력:   결제팀 <- 나 -[선호]-> 채식
# 출력:   결제팀 <- 박민수 -[못먹음]-> 매운맛

# %% [markdown]
# ## 4. `DISTINCT`는 왜 필요한가
#
# 그래프 질의는 **행 단위가 아니라 경로 단위**로 결과를 낸다.
# 서로 다른 사람이 같은 선호 노드를 가리키면 같은 이름이 여러 번 나온다.
# 위 데이터는 우연히 겹치는 사람이 없어 차이가 안 보이니,
# 「이서연도 채식」과 「나도 매운맛 못 먹음」을 추가해 보자.

# %%
tmp2 = tempfile.mkdtemp()
EDGES2 = EDGES + [("이서연", "채식", "선호"), ("나", "매운맛", "못먹음")]
conn2 = build(tmp2 + "/db", NODES, EDGES2)

no_distinct = [
    r[0]
    for r in rows(
        conn2.execute(
            "MATCH (t:N {name:'결제팀'})<-[:R]-(p:N)-[e:R]->(pref:N) WHERE pref.kind='Pref' RETURN pref.name"
        )
    )
]
with_distinct = [
    r[0]
    for r in rows(
        conn2.execute(
            "MATCH (t:N {name:'결제팀'})<-[:R]-(p:N)-[e:R]->(pref:N) WHERE pref.kind='Pref' RETURN DISTINCT pref.name"
        )
    )
]
print("DISTINCT 없이:", no_distinct)
print("DISTINCT 있이:", with_distinct)
# 출력: DISTINCT 없이: ['매운맛', '매운맛', '채식', '채식']
# 출력: DISTINCT 있이: ['매운맛', '채식']

# %% [markdown]
# 경로가 4개(나→채식, 나→매운맛, 박민수→매운맛, 이서연→채식)이므로 행도 4개다.
# 「회식 때 피할 것」은 **집합**이지 세는 대상이 아니므로 `DISTINCT`로 접는다.
#
# 반대로 「몇 명이 이 선호를 갖는가」를 알고 싶다면 `DISTINCT`를 빼고
# `count(*)`로 세면 된다. 같은 패턴이 다른 질문에도 쓰인다.

# %%
cnt = rows(
    conn2.execute(
        "MATCH (t:N {name:'결제팀'})<-[:R]-(p:N)-[e:R]->(pref:N) "
        "WHERE pref.kind='Pref' RETURN pref.name, count(p) ORDER BY pref.name"
    )
)
print("선호별 인원수:", cnt)
# 출력: 선호별 인원수: [['매운맛', 2], ['채식', 2]]

# %% [markdown]
# ## 5. 다른 모양은 왜 못 하나
#
# 같은 질문을 평평한 텍스트와 키-값으로 던져 본다.

# %%
FACTS = [
    "저는 서울 강남에서 일합니다",
    "회사는 결제팀이고 팀장은 박민수입니다",
    "박민수 팀장은 매운 음식을 못 먹습니다",
    "지난주에 팀 회식을 마포에서 했습니다",
    "저는 회식 때 채식만 합니다",
    "이서연 님이 새로 팀에 왔습니다",
    "이서연 님은 마포에 삽니다",
]

flat = [f for f in FACTS if "회식" in f]  # 낱말 "회식"으로 찾기
print("평평한 텍스트:", flat)
# 출력: 평평한 텍스트: ['지난주에 팀 회식을 마포에서 했습니다', '저는 회식 때 채식만 합니다']

kv = {"일하": ("근무지", "강남"), "식성": ("식성", "채식")}
hit = [f"{n}={v}" for k, (n, v) in kv.items() if k in "회식 장소를 정할 때 피해야 할 것은?"]
print("키-값:", hit or "✗ 칸 없음")
# 출력: 키-값: ✗ 칸 없음

# %% [markdown]
# - **평평한 텍스트**: 낱말 「회식」이 든 두 줄은 찾지만, 박민수의 매운맛은 못 찾는다.
#   그 문장에는 「회식」이라는 낱말이 없기 때문이다. 사람과 선호를 잇는 *구조*가 없다.
# - **키-값**: 「팀원 전체의 회피 항목」이라는 칸을 미리 만들어 두지 않았으니 답이 없다.
#   그리고 그런 칸을 전부 미리 만들어 둘 수는 없다. 질문은 무한하다.
# - **그래프**: 팀 → 팀원 → 선호 경로를 *따라가면* 된다. 저장할 때 질문을 몰라도 된다.

# %% [markdown]
# ## 6. 시각화 — 2홉이 지나가는 길
#
# 왼쪽 홉(팀 ← 사람)은 파란색, 오른쪽 홉(사람 → 선호)은 빨간색,
# 패턴에 걸리지 않는 간선은 회색으로 그린다.

# %%
try:
    import plotly.graph_objects as go

    POS = {
        "결제팀": (0.0, 0.0),
        "나": (1.0, 1.0),
        "박민수": (1.0, 0.0),
        "이서연": (1.0, -1.0),
        "채식": (2.2, 1.2),
        "매운맛": (2.2, -0.2),
        "강남": (2.2, 0.5),
        "마포": (2.2, -1.2),
    }
    TEAM = {"나", "박민수", "이서연"}
    PREF = {n for n, k in NODES if k == "Pref"}

    def edge_class(a, b):
        if b == "결제팀" and a in TEAM:
            return "hop1"
        if a in TEAM and b in PREF:
            return "hop2"
        return "other"

    COLOR = {"hop1": "#2563eb", "hop2": "#dc2626", "other": "#c7cbd1"}
    WIDTH = {"hop1": 3.0, "hop2": 3.0, "other": 1.2}

    fig = go.Figure()
    seen = set()
    for a, b, k in EDGES:
        cls = edge_class(a, b)
        x0, y0 = POS[a]
        x1, y1 = POS[b]
        fig.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line=dict(color=COLOR[cls], width=WIDTH[cls]),
                hovertext=f"{a} -[{k}]-> {b}",
                hoverinfo="text",
                name={"hop1": "1홉: 팀 <- 사람", "hop2": "2홉: 사람 -> 선호", "other": "패턴 밖"}[cls],
                showlegend=cls not in seen,
            )
        )
        seen.add(cls)
        fig.add_annotation(
            x=x1, y=y1, ax=x0, ay=y0, xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=3, arrowsize=1.4, arrowwidth=WIDTH[cls],
            arrowcolor=COLOR[cls], text="", standoff=16,
        )
        fig.add_annotation(
            x=(x0 + x1) / 2, y=(y0 + y1) / 2, text=k, showarrow=False,
            font=dict(size=10, color=COLOR[cls]), bgcolor="rgba(255,255,255,0.75)",
        )

    KIND_COLOR = {"Team": "#0f766e", "Person": "#1e3a8a", "Pref": "#991b1b", "Place": "#6b7280"}
    fig.add_trace(
        go.Scatter(
            x=[POS[n][0] for n, _ in NODES],
            y=[POS[n][1] for n, _ in NODES],
            mode="markers+text",
            marker=dict(size=42, color=[KIND_COLOR[k] for _, k in NODES], line=dict(color="white", width=2)),
            text=[n for n, _ in NODES],
            textposition="middle center",
            textfont=dict(color="white", size=11),
            hovertext=[f"{n} ({k})" for n, k in NODES],
            hoverinfo="text",
            showlegend=False,
        )
    )
    fig.update_layout(
        title="(팀)&lt;-[:R]-(사람)-[e:R]-&gt;(선호) — DISTINCT 결과: 매운맛, 채식",
        xaxis=dict(visible=False, range=[-0.6, 3.0]),
        yaxis=dict(visible=False, range=[-1.8, 1.8]),
        plot_bgcolor="white",
        width=900,
        height=520,
        legend=dict(orientation="h", y=-0.05),
    )
    _show(fig)
    fig.write_image(os.path.join(HERE, "expy.png"), scale=2)
    print("expy.png 저장")
except ImportError as e:
    print("시각화 건너뜀:", e)
# 출력: expy.png 저장

# %%
shutil.rmtree(tmp, ignore_errors=True)
shutil.rmtree(tmp2, ignore_errors=True)
print("정리 완료")
# 출력: 정리 완료
