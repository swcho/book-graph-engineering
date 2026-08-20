# %% [markdown]
# # 계보(lineage)를 거슬러 올라가는 가변 길이 경로 질의
#
# 29장 예제 3의 상황: 에이전트가 답을 하나 내놓았다.
# 「이 답은 무엇을 근거로 나왔나?」를 물으려면
# **답 → 실행 → 스텝 → 사실 → 출처**로 이어지는 엣지를 여러 홉(hop) 따라가야 한다.
#
# 홉 수가 노드마다 다르므로(1홉짜리도 있고 4홉짜리도 있다)
# 고정 길이 패턴으로는 못 쓰고 **가변 길이 경로** `[:Link*1..4]`를 쓴다.
#
# ```cypher
# MATCH (a:Node {id:'ans1'})-[:Link*1..4]->(x:Node)
# RETURN DISTINCT x.kind, x.label
# ```
#
# - `*1..4` — 1홉 이상 4홉 이하의 모든 경로
# - `DISTINCT` — 같은 노드에 여러 경로로 닿을 수 있으므로 중복 제거
# - 화살표 방향을 바꾸면(`<-`) 역방향 영향 분석이 된다

# %%
# 필요 패키지: kuzu, plotly, kaleido, networkx
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


def rows(r):
    out = []
    while r.has_next():
        out.append(tuple(r.get_next()))
    return out

# %% [markdown]
# ## 1. 계보 그래프 만들기
#
# 답(Answer) 하나가 실행(Run) 하나에서 나왔고, 실행은 스텝(Step) 셋을 포함하며,
# 스텝들은 사실(Fact)을 읽거나 만들었고, 사실마다 출처(Source)가 있다.
# 노드 종류가 달라도 전부 `Node` 테이블 하나에 `kind` 속성으로 담는다 — 그래야
# `[:Link*1..4]` 한 패턴으로 이질적인 계층을 통째로 훑을 수 있다.

# %%
NODES = [
    ("ans1",  "Answer", "3분기 환불률 증가 원인 = 배송 지연"),
    ("run1",  "Run",    "분석 워크플로 #4821"),
    ("step1", "Step",   "1. 환불 사유 집계"),
    ("step2", "Step",   "2. 배송 지표 조회"),
    ("step3", "Step",   "3. 상관 판단"),
    ("f1",    "Fact",   "환불 사유 1위 = 배송 지연 (41%)"),
    ("f2",    "Fact",   "3분기 평균 배송일 4.2일"),
    ("f3",    "Fact",   "배송 지연-환불 상관 0.71"),
    ("s1",    "Source", "주문 DB 스냅숏"),
    ("s2",    "Source", "물류 대시보드"),
    ("s3",    "Source", "에이전트 추론 규칙"),
]

LINKS = [
    ("ans1", "run1", "생성됨"),
    ("run1", "step1", "포함"), ("run1", "step2", "포함"), ("run1", "step3", "포함"),
    ("step1", "f1", "읽음"), ("step2", "f2", "읽음"), ("step3", "f3", "만듦"),
    ("f3", "f1", "기댐"), ("f3", "f2", "기댐"),
    ("f1", "s1", "출처"), ("f2", "s2", "출처"), ("f3", "s3", "출처"),
]

tmp = tempfile.mkdtemp()
db = kuzu.Database(tmp + "/db")
c = kuzu.Connection(db)
c.execute("CREATE NODE TABLE Node(id STRING, kind STRING, label STRING, PRIMARY KEY(id))")
c.execute("CREATE REL TABLE Link(FROM Node TO Node, kind STRING)")
for i, k, l in NODES:
    c.execute("CREATE (:Node {id:$i, kind:$k, label:$l})", {"i": i, "k": k, "l": l})
for a, b, k in LINKS:
    c.execute("MATCH (x:Node {id:$a}),(y:Node {id:$b}) CREATE (x)-[:Link {kind:$k}]->(y)",
              {"a": a, "b": b, "k": k})
print(f"노드 {len(NODES)}개, 엣지 {len(LINKS)}개 생성")
# 출력: 노드 11개, 엣지 12개 생성

# %% [markdown]
# ## 2. 카드의 질의 — 가변 길이 경로로 근거 전체 뽑기
#
# `ans1`에서 나가는 엣지를 1~4홉 따라가면 실행·스텝·사실·출처가 전부 잡힌다.

# %%
q = ("MATCH (a:Node {id:'ans1'})-[:Link*1..4]->(x:Node) "
     "RETURN DISTINCT x.kind, x.label ORDER BY x.kind, x.label")
for kind, label in rows(c.execute(q)):
    print(f"[{kind:<6}] {label}")
# 출력: [Fact  ] 3분기 평균 배송일 4.2일
# 출력: [Fact  ] 배송 지연-환불 상관 0.71
# 출력: [Fact  ] 환불 사유 1위 = 배송 지연 (41%)
# 출력: [Run   ] 분석 워크플로 #4821
# 출력: [Source] 물류 대시보드
# 출력: [Source] 에이전트 추론 규칙
# 출력: [Source] 주문 DB 스냅숏
# 출력: [Step  ] 1. 환불 사유 집계
# 출력: [Step  ] 2. 배송 지표 조회
# 출력: [Step  ] 3. 상관 판단

# %% [markdown]
# ## 3. 왜 `*1..4`인가 — 상한을 바꿔 보면 안다
#
# 상한이 낮으면 깊은 곳(출처)까지 못 닿고, 상한이 없으면(`*`) 그래프가 크면
# 탐색이 폭발한다. 계보 깊이가 「답→실행→스텝→사실→출처」로 최대 4홉이므로
# `*1..4`가 정확한 상한이다. DISTINCT가 필요한 이유도 확인한다:
# `f1`에는 「step1→f1」(2홉)과 「step3→f3→f1」(3홉) 두 경로로 닿는다.

# %%
for lo, hi in [(1, 1), (1, 2), (1, 3), (1, 4)]:
    got = rows(c.execute(
        f"MATCH (a:Node {{id:'ans1'}})-[:Link*{lo}..{hi}]->(x:Node) "
        "RETURN count(x), count(DISTINCT x)"))
    paths, uniq = got[0]
    print(f"*{lo}..{hi}: 도달 경로 {paths}개 → DISTINCT 노드 {uniq}개")
# 출력: *1..1: 도달 경로 1개 → DISTINCT 노드 1개
# 출력: *1..2: 도달 경로 4개 → DISTINCT 노드 4개
# 출력: *1..3: 도달 경로 7개 → DISTINCT 노드 7개
# 출력: *1..4: 도달 경로 12개 → DISTINCT 노드 10개

# %% [markdown]
# `*1..4`에서 경로는 12개인데 노드는 10개 — `f1`, `f2`가 두 경로씩으로 닿아서다.
# `RETURN DISTINCT`가 없으면 같은 노드가 두 번 나온다.
#
# ## 4. 반대 방향 — 「이 출처가 틀리면 뭐가 무너지나」
#
# **같은 엣지**를 방향만 뒤집어 따라가면 영향 분석이 된다.
# 정방향이 「왜 이 답이 나왔나」, 역방향이 「이게 틀리면 뭐가 무너지나」.

# %%
q_rev = ("MATCH (a:Node)-[:Link*1..4]->(s:Node {id:'s2'}) "
         "RETURN DISTINCT a.kind, a.label ORDER BY a.kind")
print("물류 대시보드(s2)가 틀렸다면 영향받는 것:")
for kind, label in rows(c.execute(q_rev)):
    print(f"  [{kind:<6}] {label}")
# 출력: 물류 대시보드(s2)가 틀렸다면 영향받는 것:
# 출력:   [Answer] 3분기 환불률 증가 원인 = 배송 지연
# 출력:   [Fact  ] 3분기 평균 배송일 4.2일
# 출력:   [Fact  ] 배송 지연-환불 상관 0.71
# 출력:   [Run   ] 분석 워크플로 #4821
# 출력:   [Step  ] 3. 상관 판단
# 출력:   [Step  ] 2. 배송 지표 조회
# (같은 kind 안의 순서는 비결정적 — ORDER BY가 a.kind만 정렬하므로)

# %% [markdown]
# ## 5. 계보 그래프 시각화
#
# `ans1`에서 각 노드까지의 최단 홉 수를 계층으로 삼아 그린다.
# `*1..4`가 훑는 범위가 곧 이 그림 전체다.

# %%
import networkx as nx
import plotly.graph_objects as go

G = nx.DiGraph()
kind_of = {i: k for i, k, _ in NODES}
label_of = {i: l for i, _, l in NODES}
G.add_nodes_from(kind_of)
G.add_edges_from([(a, b) for a, b, _ in LINKS])

depth = nx.single_source_shortest_path_length(G, "ans1")  # ans1로부터 홉 수
by_depth = {}
for n, d in depth.items():
    by_depth.setdefault(d, []).append(n)
pos = {}
for d, ns in by_depth.items():
    for i, n in enumerate(sorted(ns)):
        pos[n] = (i - (len(ns) - 1) / 2, -d)

COLOR = {"Answer": "#d62728", "Run": "#9467bd", "Step": "#1f77b4",
         "Fact": "#2ca02c", "Source": "#ff7f0e"}

edge_x, edge_y = [], []
for a, b in G.edges():
    edge_x += [pos[a][0], pos[b][0], None]
    edge_y += [pos[a][1], pos[b][1], None]

fig = go.Figure()
fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines",
                         line=dict(color="#aaaaaa", width=1.2),
                         hoverinfo="none", showlegend=False))
for kind in ("Answer", "Run", "Step", "Fact", "Source"):
    ns = [n for n in G.nodes if kind_of[n] == kind]
    fig.add_trace(go.Scatter(
        x=[pos[n][0] for n in ns], y=[pos[n][1] for n in ns],
        mode="markers+text", name=kind,
        text=[n for n in ns], textposition="bottom center",
        hovertext=[label_of[n] for n in ns],
        marker=dict(size=26, color=COLOR[kind], line=dict(width=1, color="#333"))))
fig.update_layout(
    title="계보 그래프 — ans1에서 [:Link*1..4]로 닿는 범위 (y축 = 홉 수)",
    xaxis=dict(visible=False), yaxis=dict(visible=False),
    width=820, height=520, plot_bgcolor="white")

_show(fig)
out_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(out_png, scale=2)  # kaleido 필요
print("saved:", out_png)
# 출력: saved: .../expy.png

# %%
shutil.rmtree(tmp, ignore_errors=True)
print("정리 완료")
# 출력: 정리 완료
