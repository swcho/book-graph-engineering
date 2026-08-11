# %% [markdown]
# # 엣지 속성으로 검색하면 전체 스캔이 된다
#
# **질문**: 엣지 모델에서 "김하늘이 담당한 체결 건"을 찾으려면 어떻게 해야 하는가?
#
# **답**: 모든 엣지를 훑으며 `props["by"]`를 확인해야 한다. 엣지 속성에는 색인을 걸 수
# 없는 엔진이 많아 전체 스캔이 된다.
#
# 이 노트북은 같은 사실을 두 가지 모델로 저장해 놓고, 같은 질문을 던졌을 때
# "훑어야 하는 엣지 수"가 어떻게 달라지는지 세어 본다.
#
# - 모델 A (엣지): `(회사)-[:SIGNED {at, by}]->(계약)`
# - 모델 B (노드 승격): `(회사)-[:HAS]->(체결)-[:OF]->(계약)`, `(체결)-[:BY]->(담당자)`
#
# 비용 모형은 이렇게 쓴다. 전체 스캔은 엣지 수 $E$에 비례하고, 노드에서 인접 엣지만
# 따라가는 것은 그 노드의 차수 $d$에 비례한다.
#
# $$T_{\text{edge}} = \Theta(E), \qquad T_{\text{node}} = \Theta(d(v))$$

# %%
# 필요 패키지: plotly, kaleido  (없으면 시각화 셀만 건너뛰면 된다)
from collections import defaultdict

# --- 모델 A: 관계를 엣지로 ---
# 담당자(by)가 «엣지 속성»으로 들어가 있다. 읽기는 쉽지만 찾기는 어렵다.
EDGE_MODEL = [
    ("가온테크", "SIGNED", "C-2025-118", {"at": "2025-06-02", "by": "김하늘"}),
    ("가온테크", "SIGNED", "C-2024-002", {"at": "2024-01-15", "by": "박서준"}),
    ("나루소프트", "SIGNED", "C-2025-004", {"at": "2025-01-20", "by": "김하늘"}),
]

# --- 모델 B: 관계를 노드로 승격 ---
# 체결이 노드가 되고, 담당자도 노드가 된다. 담당자는 이제 «찾을 수 있는» 대상이다.
NODE_MODEL_NODES = {
    "s1": {"label": "체결", "at": "2025-06-02"},
    "s2": {"label": "체결", "at": "2024-01-15"},
    "s3": {"label": "체결", "at": "2025-01-20"},
}
NODE_MODEL_EDGES = [
    ("가온테크", "HAS", "s1"), ("s1", "OF", "C-2025-118"), ("s1", "BY", "김하늘"),
    ("가온테크", "HAS", "s2"), ("s2", "OF", "C-2024-002"), ("s2", "BY", "박서준"),
    ("나루소프트", "HAS", "s3"), ("s3", "OF", "C-2025-004"), ("s3", "BY", "김하늘"),
]

print(f"모델 A 엣지 {len(EDGE_MODEL)}개 / 모델 B 노드 {len(NODE_MODEL_NODES)}개, 엣지 {len(NODE_MODEL_EDGES)}개")
# 출력: 모델 A 엣지 3개 / 모델 B 노드 3개, 엣지 9개

# %% [markdown]
# ## 1단계 — 엣지 모델의 답: 전체 스캔
#
# 시작점으로 삼을 노드가 없다. "김하늘"은 노드가 아니라 문자열 속성값이므로,
# 그래프 탐색을 시작할 자리가 존재하지 않는다. 남은 방법은 하나뿐이다.
# **모든 엣지를 하나씩 꺼내서 `props["by"]`를 비교하는 것.**

# %%
def q_edge_model(who, edges=EDGE_MODEL):
    """«김하늘이 담당한 체결 건» — 엣지 모델에서는 모든 엣지를 훑어야 한다."""
    scanned = 0
    out = []
    for src, _rel, dst, props in edges:
        scanned += 1                      # 색인이 없으니 한 건도 건너뛸 수 없다
        if props.get("by") == who:
            out.append((src, dst, props["at"]))
    return out, scanned


rows_a, scanned_a = q_edge_model("김하늘")
print(f"결과 {len(rows_a)}건, 훑은 엣지 {scanned_a}개")
for r in rows_a:
    print("   ", r)
# 출력: 결과 2건, 훑은 엣지 3개
# 출력:     ('가온테크', 'C-2025-118', '2025-06-02')
# 출력:     ('나루소프트', 'C-2025-004', '2025-01-20')

# %% [markdown]
# 결과 2건을 얻기 위해 엣지 3개를 다 봤다. 엣지가 3개일 때는 아무렇지 않다.
# 문제는 이 3이 $E$라는 점이다. 엣지가 100만이면 100만을 훑는다.
#
# Cypher로 쓰면 이런 모양이 되고, 실행 계획에는 `AllRelationshipsScan`(또는
# `RelationshipTypeScan` + 필터)이 뜬다. 노드 시작점이 없어서 색인 탐색으로
# 들어갈 입구가 없기 때문이다.
#
# ```cypher
# MATCH (c:회사)-[s:SIGNED]->(k:계약)
# WHERE s.by = '김하늘'          // 엣지 속성 조건 → 관계 전체 스캔
# RETURN c, k, s.at
# ```

# %% [markdown]
# ## 2단계 — 노드 모델의 답: 인접 엣지만
#
# "김하늘"이 노드가 되면 이야기가 달라진다. 노드는 라벨+속성으로 색인을 걸 수 있으니
# $O(\log n)$(또는 해시면 $O(1)$)으로 찾아 들어가고, 거기서부터는 자기에게 붙은
# `BY` 엣지만 거꾸로 따라가면 된다. 나머지 그래프는 아예 만지지 않는다.

# %%
def q_node_model(who, edges=NODE_MODEL_EDGES):
    """노드 모델에서는 «김하늘»에게 들어오는 BY 엣지만 보면 된다."""
    incoming = defaultdict(list)          # 실제 엔진에서는 저장 구조 자체가 이 색인이다
    for src, rel, dst in edges:
        incoming[dst].append((src, rel))

    scanned = 0
    out = []
    for src, rel in incoming[who]:        # 김하늘의 차수만큼만 훑는다
        scanned += 1
        if rel != "BY":
            continue
        company = next(a for a, r, b in edges if b == src and r == "HAS")
        contract = next(b for a, r, b in edges if a == src and r == "OF")
        out.append((company, contract, NODE_MODEL_NODES[src]["at"]))
    return out, scanned


rows_b, scanned_b = q_node_model("김하늘")
print(f"결과 {len(rows_b)}건, 훑은 엣지 {scanned_b}개")
for r in rows_b:
    print("   ", r)
# 출력: 결과 2건, 훑은 엣지 2개
# 출력:     ('가온테크', 'C-2025-118', '2025-06-02')
# 출력:     ('나루소프트', 'C-2025-004', '2025-01-20')

# %% [markdown]
# 두 모델의 **결과는 완전히 같다**. 달라진 건 비용의 증가 곡선이다.
#
# | 모델 | 시작점 | 훑는 양 | 데이터가 10배 늘면 |
# |---|---|---|---|
# | A (엣지 속성) | 없음 | 전체 엣지 $E$ | 비용도 10배 |
# | B (노드 승격) | 색인된 담당자 노드 | 그 노드의 차수 $d$ | 그 사람 건수만큼만 |

# %% [markdown]
# ## 3단계 — 규모를 키워 본다
#
# 담당자가 100명이고 각자 계약을 고르게 나눠 가졌다고 하자.
# 엣지가 늘어날 때 두 모델이 훑는 양을 세어 본다.

# %%
import random

def build(n_edges, n_reps=100, seed=7):
    """담당자 n_reps 명이 계약 n_edges 건을 고르게 나눠 가진 데이터를 만든다."""
    rnd = random.Random(seed)
    reps = [f"담당자{i:03d}" for i in range(n_reps)]
    edge_model = [
        (f"회사{rnd.randrange(500)}", "SIGNED", f"C-{i:07d}",
         {"at": "2025-01-01", "by": reps[i % n_reps]})
        for i in range(n_edges)
    ]
    node_edges = []
    for i, (co, _r, contract, props) in enumerate(edge_model):
        sid = f"s{i}"
        node_edges += [(co, "HAS", sid), (sid, "OF", contract), (sid, "BY", props["by"])]
    return edge_model, node_edges


TARGET = "담당자000"
SIZES = [100, 1_000, 10_000, 100_000]
rows = []
for n in SIZES:
    em, nm = build(n)
    res_a, sc_a = q_edge_model(TARGET, em)

    # 노드 모델은 색인 조회 후 인접 엣지만 — 여기서는 BY 역인접만 세어 본다
    inc = defaultdict(list)
    for s, r, d in nm:
        if r == "BY":
            inc[d].append(s)
    sc_b = len(inc[TARGET])

    rows.append((n, len(res_a), sc_a, sc_b, sc_a / sc_b))

print(f"{'엣지 수':>9} {'결과':>5} {'A 스캔':>9} {'B 스캔':>7} {'배율':>9}")
for n, hits, sa, sb, ratio in rows:
    print(f"{n:>9,} {hits:>5} {sa:>9,} {sb:>7,} {ratio:>8,.0f}x")
# 출력:      엣지 수    결과      A 스캔    B 스캔        배율
# 출력:        100     1       100       1      100x
# 출력:      1,000    10     1,000      10      100x
# 출력:     10,000   100    10,000     100      100x
# 출력:    100,000  1000   100,000   1,000      100x

# %% [markdown]
# 담당자가 100명이므로 배율은 100배로 고정된다. 여기서 읽어야 할 것은 배율이 아니라
# **선택도(selectivity)** 다. 결과는 전체의 $1/100$인데 A 모델은 항상 100%를 읽는다.
# 담당자가 1만 명이면 A는 여전히 100%를 읽고 B는 0.01%만 읽는다. 즉
#
# $$\frac{T_{\text{edge}}}{T_{\text{node}}} \approx \frac{E}{E/R} = R \quad (R = \text{담당자 수})$$
#
# 카디널리티가 높은 속성일수록 전체 스캔의 낭비가 커진다. 색인이 가장 필요한 자리에서
# 색인을 걸 수 없는 것이 엣지 속성의 함정이다.

# %% [markdown]
# ## 4단계 — 왜 엣지 속성에는 색인을 못 거는가
#
# 엔진마다 사정이 다르지만 대략 이렇다.
#
# | 엔진 | 관계/엣지 속성 색인 |
# |---|---|
# | Neo4j | 5.x부터 관계 속성 색인 지원(RANGE/TEXT/POINT/FULL-TEXT). 그전에는 없었다 |
# | 다수의 프로퍼티 그래프 엔진 | 노드 속성 색인만. 엣지 속성은 필터 조건으로만 쓰인다 |
# | RDF | 엣지에 속성 자체가 없다. 표현하려면 reification 또는 RDF-star가 필요하다 |
#
# 색인을 지원하더라도 **엣지는 노드에 매달린 저장 구조**라서, 엣지 속성 조건만으로는
# 탐색의 시작점이 정해지지 않는 경우가 많다. 그리고 "우리 엔진은 지원한다"에
# 설계를 걸어 두면, 엔진을 바꾸는 순간 질의가 조용히 전체 스캔으로 퇴화한다.

# %% [markdown]
# ## 5단계 — 그래서 승격 기준은 하나다
#
# 관계를 노드로 올릴지 판단하는 질문 세 개.
#
# 1. 그 관계에 속성이 붙나?
# 2. 그 관계가 제3의 대상과 이어지나?
# 3. **그 속성으로 검색하나?**
#
# 3번이 결정적이다. `props["by"]`를 `WHERE` 절에 쓰기 시작한 순간이 승격 신호다.
#
# > 속성은 **읽는** 것이고, 노드는 **찾는** 것이다.
#
# 승격은 늦게 해도 되지만 미루면 안 된다. 데이터가 쌓일수록 옮기는 값이 비례해 오르고,
# 정작 제일 오래 걸리는 일은 데이터 이동이 아니라 표기 통일이다.

# %%
# --- 시각화: 엣지 수 대비 스캔량 (로그-로그) ---
import os

def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    xs = [r[0] for r in rows]
    ys_a = [r[2] for r in rows]
    ys_b = [r[3] for r in rows]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "훑는 엣지 수 (로그-로그)",
            "엣지 100,000건일 때 읽은 양",
        ),
        column_widths=[0.58, 0.42],
    )

    fig.add_trace(go.Scatter(x=xs, y=ys_a, mode="lines+markers",
                             name="모델 A · 엣지 속성 (전체 스캔)",
                             line=dict(width=3, color="#d1495b"),
                             marker=dict(size=10, symbol="circle")),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=xs, y=ys_b, mode="lines+markers",
                             name="모델 B · 노드 승격 (인접 엣지)",
                             line=dict(width=3, color="#2a9d8f"),
                             marker=dict(size=10, symbol="square")),
                  row=1, col=1)

    last = rows[-1]
    fig.add_trace(go.Bar(x=["모델 A<br>엣지 속성", "모델 B<br>노드 승격"], y=[last[2], last[3]],
                         text=[f"{last[2]:,}건 읽음", f"{last[3]:,}건 읽음"],
                         textposition="outside", width=0.5,
                         marker_color=["#d1495b", "#2a9d8f"],
                         showlegend=False),
                  row=1, col=2)

    fig.update_xaxes(type="log", title_text="전체 엣지 수 E", row=1, col=1)
    fig.update_yaxes(type="log", title_text="훑은 엣지 수", row=1, col=1)
    fig.update_yaxes(title_text="읽은 엣지 수 (선형 축)", range=[0, last[2] * 1.25],
                     row=1, col=2)
    fig.update_layout(
        title="엣지 속성 검색은 전체 스캔, 노드 승격은 차수만큼",
        template="plotly_white", height=460, width=1040,
        legend=dict(orientation="h", y=-0.22, x=0),
        margin=dict(t=90, b=110),
    )

    _show(fig)
    out_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
    fig.write_image(out_png, scale=2)
    print("saved:", out_png)
except Exception as exc:  # kaleido/plotly 미설치 등
    print("시각화 건너뜀:", type(exc).__name__, exc)
# 출력: saved: .../expy.png

# %% [markdown]
# ## 정리
#
# - 엣지 모델에서 `by`로 찾으려면 **모든 엣지를 훑으며 `props["by"]`를 확인**해야 한다.
#   시작점이 될 노드가 없기 때문이다.
# - 엣지 속성 색인은 지원이 제한적이라(또는 아예 없어서) 전체 스캔으로 퇴화한다.
# - 담당자를 노드로 승격하면 색인 조회 한 번 + 인접 엣지 순회로 끝난다.
#   비용이 $\Theta(E)$에서 $\Theta(d(v))$로 바뀐다.
# - 판단 기준: **그 속성으로 검색하기 시작했는가.** 그렇다면 승격할 때다.
