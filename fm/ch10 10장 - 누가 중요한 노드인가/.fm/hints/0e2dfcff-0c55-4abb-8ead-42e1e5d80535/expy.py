# %% [markdown]
# # 브랜디스(Brandes) 알고리즘의 두 단계
#
# > **질문** 브랜디스 알고리즘의 두 단계는 무엇인가?
# >
# > **답** 전방 BFS로 각 노드의 최단 경로 수 $\sigma$ 와 선행자 목록 `pred` 를 모으고,
# > 후방으로 스택을 되짚으며 $\delta$ 의존도를 누적해 매개 중심성을 더한다.
#
# 이 노트북은 **아주 작은 그래프**에서 두 단계를 회차별로 찍어 보고,
# 마지막에 `networkx.betweenness_centrality` 와 값을 대조합니다.
#
# 매개 중심성의 정의:
#
# $$
# C_B(v) \;=\; \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}
# \;=\; \sum_{s \neq v} \delta_{s\bullet}(v)
# $$
#
# 브랜디스는 $\sigma_{st}(v)/\sigma_{st}$ 를 **쌍별로 만들지 않고**,
# 출발점 $s$ 하나당 $\delta_{s\bullet}(\cdot)$ 를 통째로 얻습니다.

# %%
# 필요 패키지: plotly, kaleido, networkx  (pip install plotly kaleido networkx)
from collections import deque
from pathlib import Path

import networkx as nx
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


HERE = Path(__file__).parent if "__file__" in globals() else Path.cwd()

# 작은 예제 그래프: A에서 D로 가는 최단 경로가 2개(B 경유 / C 경유)라 sigma가 갈라진다.
EDGES = [
    ("A", "B"),
    ("A", "C"),
    ("B", "D"),
    ("C", "D"),
    ("D", "E"),
    ("D", "G"),
    ("E", "F"),
]

adj = {}
for u, v in EDGES:
    adj.setdefault(u, []).append(v)
    adj.setdefault(v, []).append(u)
adj = {k: sorted(vs) for k, vs in sorted(adj.items())}

for v, nbrs in adj.items():
    print(f"{v}: {nbrs}")
# 출력:
# A: ['B', 'C']
# B: ['A', 'D']
# C: ['A', 'D']
# D: ['B', 'C', 'E', 'G']
# E: ['D', 'F']
# F: ['E']
# G: ['D']

# %% [markdown]
# ## 1단계 — 전방 BFS (forward pass)
#
# 출발점 $s$ 에서 BFS를 **한 번** 돌면서 네 가지를 만듭니다.
#
# | 자료구조 | 뜻 | 갱신 규칙 |
# |---|---|---|
# | `dist[v]` | $s{\to}v$ 최단 거리 | BFS 표준 |
# | `sigma[v]` = $\sigma_{sv}$ | $s{\to}v$ 최단 경로 **개수** | $\sigma_{sv} = \sum_{u \in pred(v)} \sigma_{su}$, 시작값 $\sigma_{ss}=1$ |
# | `pred[v]` | $v$ 의 **선행자 목록** | $dist[v] = dist[u]+1$ 인 간선 $(u,v)$ 를 전부 저장 |
# | `stack` | BFS 방문 순서 | 거리 **비내림차순**으로 쌓인다 |
#
# 핵심은 `if dist[w] < 0` (처음 보는 노드) 과 `if dist[w] == dist[v] + 1` (최단 경로 DAG 간선) 이
# **분리된 조건**이라는 점입니다. 이미 방문한 노드라도 거리가 정확히 1 더 크면
# 그 간선은 **또 다른 최단 경로**이므로 $\sigma$ 에 더하고 `pred` 에도 넣습니다.


# %%
def forward_bfs(adj, s, verbose=False):
    """1단계: 전방 BFS. stack, pred, sigma, dist 를 돌려준다."""
    stack, pred = [], {v: [] for v in adj}
    sigma = {v: 0 for v in adj}
    sigma[s] = 1
    dist = {v: -1 for v in adj}
    dist[s] = 0
    q = deque([s])
    step = 0
    while q:
        v = q.popleft()
        stack.append(v)
        for w in adj[v]:
            if dist[w] < 0:  # 처음 보는 노드
                dist[w] = dist[v] + 1
                q.append(w)
            if dist[w] == dist[v] + 1:  # 최단 경로 DAG 의 간선
                sigma[w] += sigma[v]
                pred[w].append(v)
        step += 1
        if verbose:
            print(
                f"  회차{step} pop={v:>1}  sigma={ {k: sigma[k] for k in adj} }"
                f"  pred[{v}]={pred[v]}"
            )
    return stack, pred, sigma, dist


print("== 1단계: s=A 에서 전방 BFS ==")
stack, pred, sigma, dist = forward_bfs(adj, "A", verbose=True)
print()
print("dist :", dist)
print("sigma:", sigma)
print("pred :", {k: v for k, v in pred.items() if v})
print("stack:", stack, " <- 거리 비내림차순")
# 출력:
# == 1단계: s=A 에서 전방 BFS ==
#   회차1 pop=A  sigma={'A': 1, 'B': 1, 'C': 1, 'D': 0, 'E': 0, 'F': 0, 'G': 0}  pred[A]=[]
#   회차2 pop=B  sigma={'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 0, 'F': 0, 'G': 0}  pred[B]=['A']
#   회차3 pop=C  sigma={'A': 1, 'B': 1, 'C': 1, 'D': 2, 'E': 0, 'F': 0, 'G': 0}  pred[C]=['A']
#   회차4 pop=D  sigma={'A': 1, 'B': 1, 'C': 1, 'D': 2, 'E': 2, 'F': 0, 'G': 2}  pred[D]=['B', 'C']
#   회차5 pop=E  sigma={'A': 1, 'B': 1, 'C': 1, 'D': 2, 'E': 2, 'F': 2, 'G': 2}  pred[E]=['D']
#   회차6 pop=G  sigma={'A': 1, 'B': 1, 'C': 1, 'D': 2, 'E': 2, 'F': 2, 'G': 2}  pred[G]=['D']
#   회차7 pop=F  sigma={'A': 1, 'B': 1, 'C': 1, 'D': 2, 'E': 2, 'F': 2, 'G': 2}  pred[F]=['E']
#
# dist : {'A': 0, 'B': 1, 'C': 1, 'D': 2, 'E': 3, 'F': 4, 'G': 3}
# sigma: {'A': 1, 'B': 1, 'C': 1, 'D': 2, 'E': 2, 'F': 2, 'G': 2}
# pred : {'B': ['A'], 'C': ['A'], 'D': ['B', 'C'], 'E': ['D'], 'F': ['E'], 'G': ['D']}
# stack: ['A', 'B', 'C', 'D', 'E', 'G', 'F']  <- 거리 비내림차순

# %% [markdown]
# 회차4에서 `sigma[D]` 가 1에서 2가 되는 순간이 이 예제의 요점입니다.
# `D` 는 `B` 경유와 `C` 경유로 도달할 수 있으므로 $\sigma_{AD}=2$ 이고,
# 그 뒤 `E`, `G`, `F` 도 전부 $\sigma = 2$ 를 물려받습니다.
#
# 같은 거리에 있는 노드끼리의 간선(예: $dist[v] = dist[w]$)은
# `dist[w] == dist[v] + 1` 조건에서 자동으로 걸러집니다.

# %% [markdown]
# ## 2단계 — 후방 의존도 누적 (backward accumulation)
#
# `stack` 을 pop 하면 $s$ 에서 **먼 노드부터** 나옵니다.
# 그래서 $w$ 를 꺼낼 시점에는 $w$ 의 모든 후속자 처리가 이미 끝나 있고,
# `delta[w]` 가 **최종값으로 확정**되어 있습니다.
#
# $$
# \delta_{s\bullet}(v) \;=\; \sum_{w \,:\, v \in pred(w)} \frac{\sigma_{sv}}{\sigma_{sw}}\bigl(1 + \delta_{s\bullet}(w)\bigr)
# $$
#
# `1` 은 "목적지가 바로 $w$ 자신"인 항, `delta[w]` 는 "목적지가 $w$ 너머"인 항입니다.
# 확정된 $\delta_{s\bullet}(w)$ 를 그대로 $C_B(w)$ 에 더합니다(단 $w = s$ 는 제외).


# %%
def backward_accumulate(adj, s, stack, pred, sigma, cb, verbose=False):
    """2단계: 스택을 되짚으며 delta 를 누적하고 cb 에 더한다."""
    delta = {v: 0.0 for v in adj}
    stack = list(stack)
    step = 0
    while stack:
        w = stack.pop()
        step += 1
        terms = []
        for v in pred[w]:
            add = sigma[v] / sigma[w] * (1 + delta[w])
            delta[v] += add
            terms.append(f"delta[{v}] += {sigma[v]}/{sigma[w]}*(1+{delta[w]:.2f}) = {add:.2f}")
        if w != s:
            cb[w] += delta[w]
        if verbose:
            joined = "; ".join(terms) if terms else "(선행자 없음)"
            mark = "  -> cb 갱신 없음(w == s)" if w == s else f"  -> cb[{w}] += {delta[w]:.2f}"
            print(f"  회차{step} pop={w} delta[{w}]={delta[w]:.2f} 확정 | {joined}{mark}")
    return delta


cb = {v: 0.0 for v in adj}
print("== 2단계: s=A 후방 누적 ==")
delta = backward_accumulate(adj, "A", stack, pred, sigma, cb, verbose=True)
print()
print("delta(s=A):", {k: round(v, 3) for k, v in delta.items()})
print("cb   (s=A):", {k: round(v, 3) for k, v in cb.items()})
# 출력:
# == 2단계: s=A 후방 누적 ==
#   회차1 pop=F delta[F]=0.00 확정 | delta[E] += 2/2*(1+0.00) = 1.00  -> cb[F] += 0.00
#   회차2 pop=G delta[G]=0.00 확정 | delta[D] += 2/2*(1+0.00) = 1.00  -> cb[G] += 0.00
#   회차3 pop=E delta[E]=1.00 확정 | delta[D] += 2/2*(1+1.00) = 2.00  -> cb[E] += 1.00
#   회차4 pop=D delta[D]=3.00 확정 | delta[B] += 1/2*(1+3.00) = 2.00; delta[C] += 1/2*(1+3.00) = 2.00  -> cb[D] += 3.00
#   회차5 pop=C delta[C]=2.00 확정 | delta[A] += 1/1*(1+2.00) = 3.00  -> cb[C] += 2.00
#   회차6 pop=B delta[B]=2.00 확정 | delta[A] += 1/1*(1+2.00) = 3.00  -> cb[B] += 2.00
#   회차7 pop=A delta[A]=6.00 확정 | (선행자 없음)  -> cb 갱신 없음(w == s)
#
# delta(s=A): {'A': 6.0, 'B': 2.0, 'C': 2.0, 'D': 3.0, 'E': 1.0, 'F': 0.0, 'G': 0.0}
# cb   (s=A): {'A': 0.0, 'B': 2.0, 'C': 2.0, 'D': 3.0, 'E': 1.0, 'F': 0.0, 'G': 0.0}

# %% [markdown]
# 손으로 검산해 봅시다. $s=A$ 일 때 $\delta_{A\bullet}(D) = 3$ 이 맞나?
#
# - $t \in \{E, G\}$: $A{\to}t$ 최단 경로는 **전부** $D$ 를 지납니다 → 각각 기여 $1$.
# - $t = F$: 역시 전부 $D$ 를 지납니다 → 기여 $1$.
# - 합 $= 3$. ✅
#
# $\delta_{A\bullet}(B) = 2$ 는? $A{\to}D$ 최단 경로 2개 중 $B$ 를 지나는 건 1개이므로 $1/2$.
# $t \in \{E, G, F\}$ 도 각각 $1/2$. 합 $= 4 \times 0.5 = 2$. ✅
#
# 그리고 `pop=D` 회차에서 $\delta[D]=3$ 이 확정되려면 그 전에 `E`, `G` 가 이미 pop 되어 있어야 합니다.
# 최단 경로 DAG에서 후속자는 항상 $dist$ 가 1 더 크므로,
# **거리 비증가 순서 = 위상 정렬의 역순**이고 BFS 스택 pop 이 이 조건을 공짜로 줍니다.

# %% [markdown]
# ## 두 단계를 모든 출발점에 대해 반복 = 브랜디스 알고리즘


# %%
def brandes(adj, sources=None, normalized=False):
    cb = {v: 0.0 for v in adj}
    for s in sources if sources is not None else adj:
        stack, pred, sigma, _ = forward_bfs(adj, s)  # 1단계
        backward_accumulate(adj, s, stack, pred, sigma, cb)  # 2단계
    n = len(adj)
    for v in cb:  # 무향 그래프: (s,t)와 (t,s)를 두 번 셌으므로 /2
        cb[v] /= 2.0
        if normalized:
            cb[v] /= (n - 1) * (n - 2) / 2.0
    return cb


mine = brandes(adj)
print("출발점별 delta 누적 (s 하나씩):")
for s in adj:
    part = {v: 0.0 for v in adj}
    st, pr, sg, _ = forward_bfs(adj, s)
    backward_accumulate(adj, s, st, pr, sg, part)
    print(f"  s={s}: ", {k: round(v, 2) for k, v in part.items()})
print()
print("C_B (raw):", {k: round(v, 3) for k, v in mine.items()})
# 출력:
# 출발점별 delta 누적 (s 하나씩):
#   s=A:  {'A': 0.0, 'B': 2.0, 'C': 2.0, 'D': 3.0, 'E': 1.0, 'F': 0.0, 'G': 0.0}
#   s=B:  {'A': 0.5, 'B': 0.0, 'C': 0.0, 'D': 3.5, 'E': 1.0, 'F': 0.0, 'G': 0.0}
#   s=C:  {'A': 0.5, 'B': 0.0, 'C': 0.0, 'D': 3.5, 'E': 1.0, 'F': 0.0, 'G': 0.0}
#   s=D:  {'A': 0.0, 'B': 0.5, 'C': 0.5, 'D': 0.0, 'E': 1.0, 'F': 0.0, 'G': 0.0}
#   s=E:  {'A': 0.0, 'B': 0.5, 'C': 0.5, 'D': 4.0, 'E': 0.0, 'F': 0.0, 'G': 0.0}
#   s=F:  {'A': 0.0, 'B': 0.5, 'C': 0.5, 'D': 4.0, 'E': 5.0, 'F': 0.0, 'G': 0.0}
#   s=G:  {'A': 0.0, 'B': 0.5, 'C': 0.5, 'D': 5.0, 'E': 1.0, 'F': 0.0, 'G': 0.0}
#
# C_B (raw): {'A': 0.5, 'B': 2.0, 'C': 2.0, 'D': 11.5, 'E': 5.0, 'F': 0.0, 'G': 0.0}
#
# 참고: 위 표는 이미 2로 나눈 뒤가 아니라 s별 delta 합이고,
# C_B (raw) 는 그 세로 합을 2로 나눈 값이다. 예) D: (3+3.5+3.5+0+4+4+5)/2 = 11.5

# %% [markdown]
# ## networkx 와 대조
#
# `networkx.betweenness_centrality` 는 바로 이 브랜디스 알고리즘을 씁니다.

# %%
G = nx.Graph()
G.add_edges_from(EDGES)

nx_raw = nx.betweenness_centrality(G, normalized=False)
nx_norm = nx.betweenness_centrality(G, normalized=True)
my_norm = brandes(adj, normalized=True)

print(f"{'node':>5} {'내 raw':>9} {'nx raw':>9} {'내 norm':>9} {'nx norm':>9}  일치")
ok = True
for v in sorted(adj):
    same = abs(mine[v] - nx_raw[v]) < 1e-9 and abs(my_norm[v] - nx_norm[v]) < 1e-9
    ok &= same
    print(f"{v:>5} {mine[v]:>9.3f} {nx_raw[v]:>9.3f} {my_norm[v]:>9.3f} {nx_norm[v]:>9.3f}  {'O' if same else 'X'}")
print()
print("전부 일치?", ok)
# 출력:
#  node     내 raw    nx raw    내 norm   nx norm  일치
#     A     0.500     0.500     0.033     0.033  O
#     B     2.000     2.000     0.133     0.133  O
#     C     2.000     2.000     0.133     0.133  O
#     D    11.500    11.500     0.767     0.767  O
#     E     5.000     5.000     0.333     0.333  O
#     F     0.000     0.000     0.000     0.000  O
#     G     0.000     0.000     0.000     0.000  O
#
# 전부 일치? True

# %% [markdown]
# ## 시각화
#
# 왼쪽: $s=A$ 에서의 **최단 경로 DAG**. 화살표는 `pred` 관계(선행자 → 노드),
# 노드 라벨은 $\sigma$ 값, 세로 열은 `dist` 계층입니다.
# 오른쪽: 두 단계를 모든 $s$ 에 대해 돌려 얻은 **매개 중심성**. 원 크기·색이 $C_B$.

# %%
POS = {  # x = dist(A, v) 계층, y = 갈래
    "A": (0.0, 0.0),
    "B": (1.0, 1.0),
    "C": (1.0, -1.0),
    "D": (2.0, 0.0),
    "E": (3.0, 0.7),
    "G": (3.0, -0.9),
    "F": (4.0, 0.7),
}

fig = make_subplots(
    rows=1,
    cols=2,
    subplot_titles=(
        "1단계: s=A 의 최단 경로 DAG (라벨 = sigma)",
        "2단계 누적 결과: 매개 중심성 C_B",
    ),
    horizontal_spacing=0.09,
)

# --- 왼쪽: 최단 경로 DAG ---
dag_edges = [(u, w) for w in pred for u in pred[w]]
ex, ey = [], []
for u, w in dag_edges:
    ex += [POS[u][0], POS[w][0], None]
    ey += [POS[u][1], POS[w][1], None]
fig.add_trace(
    go.Scatter(x=ex, y=ey, mode="lines", line=dict(color="#9aa5b1", width=2), hoverinfo="skip", showlegend=False),
    row=1,
    col=1,
)
# 최단 경로에 못 들어간 간선 (같은 거리끼리 등) 은 점선으로
dag_set = {frozenset(e) for e in dag_edges}
nx_, ny_ = [], []
for u, v in EDGES:
    if frozenset((u, v)) not in dag_set:
        nx_ += [POS[u][0], POS[v][0], None]
        ny_ += [POS[u][1], POS[v][1], None]
if nx_:
    fig.add_trace(
        go.Scatter(x=nx_, y=ny_, mode="lines", line=dict(color="#d9dee3", width=1, dash="dot"),
                   hoverinfo="skip", showlegend=False),
        row=1,
        col=1,
    )
fig.add_trace(
    go.Scatter(
        x=[POS[v][0] for v in adj],
        y=[POS[v][1] for v in adj],
        mode="markers+text",
        marker=dict(size=44, color=[dist[v] for v in adj], colorscale="Blues", cmin=-1, cmax=5,
                    line=dict(color="#33445c", width=2)),
        text=[f"{v}<br>σ={sigma[v]}" for v in adj],
        textposition="middle center",
        textfont=dict(size=11, color="#10202e"),
        hovertext=[f"{v}: dist={dist[v]}, sigma={sigma[v]}, pred={pred[v]}, delta={delta[v]:.2f}" for v in adj],
        hoverinfo="text",
        showlegend=False,
    ),
    row=1,
    col=1,
)

# --- 오른쪽: 매개 중심성 ---
ex2, ey2 = [], []
for u, v in EDGES:
    ex2 += [POS[u][0], POS[v][0], None]
    ey2 += [POS[u][1], POS[v][1], None]
fig.add_trace(
    go.Scatter(x=ex2, y=ey2, mode="lines", line=dict(color="#c3cbd3", width=2), hoverinfo="skip", showlegend=False),
    row=1,
    col=2,
)
vals = [mine[v] for v in adj]
fig.add_trace(
    go.Scatter(
        x=[POS[v][0] for v in adj],
        y=[POS[v][1] for v in adj],
        mode="markers+text",
        marker=dict(
            size=[36 + 32 * (mine[v] / max(vals)) for v in adj],
            color=vals,
            colorscale="OrRd",
            cmin=0,
            cmax=max(vals),
            line=dict(color="#5c3320", width=2),
            colorbar=dict(title="C_B", x=1.01, len=0.75),
        ),
        text=[f"{v}<br>{mine[v]:.2f}" for v in adj],
        textposition="middle center",
        textfont=dict(size=11, color="#20120a"),
        hovertext=[f"{v}: C_B(raw)={mine[v]:.3f}, 정규화={my_norm[v]:.3f}" for v in adj],
        hoverinfo="text",
        showlegend=False,
    ),
    row=1,
    col=2,
)

fig.update_xaxes(visible=False, range=[-0.6, 4.6])
fig.update_yaxes(visible=False, range=[-1.7, 1.7], scaleanchor=None)
fig.update_layout(
    title="브랜디스 알고리즘의 두 단계: 전방 BFS(sigma/pred) → 후방 delta 누적",
    width=1100,
    height=470,
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=30, r=90, t=90, b=30),
)

out = HERE / "expy.png"
fig.write_image(str(out), scale=2)  # 필요 패키지: kaleido
print("저장:", out.name, "존재:", out.exists())
_show(fig)
# 출력:
# 저장: expy.png 존재: True

# %% [markdown]
# ## 한 줄로 다시
#
# > **1단계(전방)**: $s$ 에서 BFS 한 번 → 최단 경로 수 $\sigma$ 와 선행자 `pred` 로
# > **최단 경로 DAG** 를 만들고, 방문 순서를 스택에 쌓는다.
# >
# > **2단계(후방)**: 스택을 pop 하며(= 먼 노드부터)
# > $\delta_v \mathrel{+}= \frac{\sigma_v}{\sigma_w}(1+\delta_w)$ 로 의존도를 아래에서 위로 접어 올리고,
# > 확정된 $\delta_w$ 를 $C_B(w)$ 에 더한다.
#
# 이 구조 덕분에 쌍별 의존도 $\sigma_{st}(v)/\sigma_{st}$ 를 **한 번도 만들지 않고**
# 비용이 $\Theta(V^3)$·$\Theta(V^2)$ 공간에서 $O(VE)$·$O(V+E)$ 공간으로 떨어집니다.
