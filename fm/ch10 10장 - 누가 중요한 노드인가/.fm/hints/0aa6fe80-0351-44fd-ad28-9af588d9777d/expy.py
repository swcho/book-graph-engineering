# %% [markdown]
# # 매개 중심성(Betweenness Centrality) 손으로 따라가기
#
# **정의.** 노드 $v$ 의 매개 중심성은
#
# $$C_B(v) \;=\; \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$$
#
# - $\sigma_{st}$ : $s \to t$ 최단 경로의 **개수**
# - $\sigma_{st}(v)$ : 그중 $v$ 를 **거쳐 가는** 것의 개수
#
# 즉 「모든 노드 쌍의 최단 경로 중 그 노드가 중간에 놓인 비율의 합」입니다.
# 최단 경로가 $\sigma_{st}$ 개면 각 경로가 $1/\sigma_{st}$ 씩만 기여합니다.
# (경로 하나에 표 한 장을 주고, 그 표를 경로 개수만큼 쪼개 나눠 가지는 셈입니다.)
#
# 무방향 그래프에서는 쌍 $(s,t)$ 를 한 번만 세고, 정규화는
# $\dfrac{1}{(n-1)(n-2)/2}$ 로 나눕니다.
#
# 필요 패키지: networkx, plotly, kaleido (없어도 앞부분 순수 파이썬 셀은 그대로 실행됩니다)

# %%
from collections import deque
from itertools import combinations


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# 다이아몬드 + 꼬리. 최단 경로가 «여러 개»가 되는 제일 작은 모양이다.
#
#     B
#    / \
#   A   D — E
#    \ /
#     C
EDGES = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("D", "E")]

adj = {}
for a, b in EDGES:
    adj.setdefault(a, set()).add(b)
    adj.setdefault(b, set()).add(a)
adj = {k: sorted(v) for k, v in sorted(adj.items())}
print(adj)
# 출력: {'A': ['B', 'C'], 'B': ['A', 'D'], 'C': ['A', 'D'], 'D': ['B', 'C', 'E'], 'E': ['D']}

# %% [markdown]
# ## 1단계 — 모든 쌍의 최단 경로를 전부 열거한다
#
# BFS 로 거리 층을 만든 뒤, 도착점에서 거꾸로 «거리가 1 작은 이웃»만 따라가면
# 최단 경로가 전부 나옵니다.

# %%
def bfs_dist(adj, s):
    d = {s: 0}
    q = deque([s])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in d:
                d[v] = d[u] + 1
                q.append(v)
    return d


def all_shortest(adj, s, t):
    d = bfs_dist(adj, s)
    if t not in d:
        return []
    out, stack = [], [(t, [t])]
    while stack:
        u, path = stack.pop()
        if u == s:
            out.append(list(reversed(path)))
            continue
        for v in adj[u]:
            if d.get(v, -1) == d[u] - 1:
                stack.append((v, path + [v]))
    return sorted(out)


for s, t in combinations(sorted(adj), 2):
    ps = all_shortest(adj, s, t)
    print(f"{s}-{t}: sigma={len(ps)}  " + " , ".join("→".join(p) for p in ps))
# 출력:
# A-B: sigma=1  A→B
# A-C: sigma=1  A→C
# A-D: sigma=2  A→B→D , A→C→D
# A-E: sigma=2  A→B→D→E , A→C→D→E
# B-C: sigma=2  B→A→C , B→D→C
# B-D: sigma=1  B→D
# B-E: sigma=1  B→D→E
# C-D: sigma=1  C→D
# C-E: sigma=1  C→D→E
# D-E: sigma=1  D→E

# %% [markdown]
# ## 2단계 — 쌍마다 $1/\sigma_{st}$ 씩 중간 노드에 나눠 준다
#
# 양 끝점($s$, $t$)은 「중간에 놓인」 게 아니므로 점수를 받지 않습니다.
# 예를 들어 $A$–$D$ 는 최단 경로가 2개이므로 $B$ 와 $C$ 가 각각 $1/2$ 만 받습니다.
# $A$–$E$ 도 경로가 2개인데, $D$ 는 **두 경로 모두**에 들어 있어
# $\sigma_{AE}(D)/\sigma_{AE} = 2/2 = 1$ 을 받습니다.

# %%
score = {v: 0.0 for v in adj}
print(f"{'쌍':<8}{'sigma':>6}  {'각 중간 노드가 받는 몫':<28}")
print("-" * 52)
for s, t in combinations(sorted(adj), 2):
    ps = all_shortest(adj, s, t)
    if not ps:
        continue
    gain = {}
    for p in ps:
        for mid in p[1:-1]:                 # 양 끝을 뺀 «중간»만
            score[mid] += 1 / len(ps)
            gain[mid] = gain.get(mid, 0) + 1 / len(ps)
    desc = ", ".join(f"{v}+{g:.2f}" for v, g in sorted(gain.items())) or "(없음)"
    print(f"{s}-{t:<6}{len(ps):>6}  {desc:<28}")

print("\n누적 점수(정규화 전):", {v: round(x, 3) for v, x in score.items()})
# 출력:
# 쌍        sigma  각 중간 노드가 받는 몫
# ----------------------------------------------------
# A-B          1  (없음)
# A-C          1  (없음)
# A-D          2  B+0.50, C+0.50
# A-E          2  B+0.50, C+0.50, D+1.00
# B-C          2  A+0.50, D+0.50
# B-D          1  (없음)
# B-E          1  D+1.00
# C-D          1  (없음)
# C-E          1  D+1.00
# D-E          1  (없음)
#
# 누적 점수(정규화 전): {'A': 0.5, 'B': 1.0, 'C': 1.0, 'D': 3.5, 'E': 0.0}

# %% [markdown]
# ## 3단계 — 정규화
#
# 무방향 그래프에서 한 노드가 «낄 수 있는» 쌍의 최대 개수는
# $\binom{n-1}{2} = \dfrac{(n-1)(n-2)}{2}$ 입니다. 여기서 $n=5$ 이므로 6.
#
# $$C_B^{\text{norm}}(v) = \frac{C_B(v)}{(n-1)(n-2)/2}$$

# %%
n = len(adj)
norm = (n - 1) * (n - 2) / 2
bc = {v: s / norm for v, s in score.items()}
for v, x in sorted(bc.items(), key=lambda kv: -kv[1]):
    print(f"{v}  {x:.4f}")
print(f"\n정규화 상수 (n-1)(n-2)/2 = {norm:.0f}")
# 출력:
# D  0.5833
# B  0.1667
# C  0.1667
# A  0.0833
# E  0.0000
#
# 정규화 상수 (n-1)(n-2)/2 = 6

# %% [markdown]
# ### 읽는 법
# - $D$ 가 압도적입니다. $E$ 로 가는 **유일한** 문이고, $B$↔$C$ 우회로이기도 합니다.
# - $B$ 와 $C$ 는 서로 대체 가능합니다. 그래서 각자 절반씩만 가져갑니다.
#   만약 $C$ 를 지워 $A$–$D$ 경로가 하나뿐이 되면 $B$ 의 점수는 두 배로 뜁니다.
# - $E$ 는 잎(leaf)이라 어떤 경로의 중간도 될 수 없어 항상 0 입니다.

# %% [markdown]
# ## 4단계 — $1/\sigma$ 를 안 나누면 어떻게 되나
#
# 「경로마다 1점씩」 주는 잘못된 셈과 비교해 봅니다.
# 대체 경로가 많은 지점이 부풀려져서, 「없으면 갈라지는가」라는 원래 질문의 답이 흐려집니다.

# %%
wrong = {v: 0.0 for v in adj}
for s, t in combinations(sorted(adj), 2):
    for p in all_shortest(adj, s, t):
        for mid in p[1:-1]:
            wrong[mid] += 1                  # ← 나누지 않음

print(f"{'노드':<6}{'올바름(1/σ)':>14}{'틀림(경로당 1)':>16}")
for v in sorted(adj):
    print(f"{v:<6}{score[v]:>14.2f}{wrong[v]:>16.2f}")
# 출력:
# 노드      올바름(1/σ)     틀림(경로당 1)
# A               0.50            1.00
# B               1.00            2.00
# C               1.00            2.00
# D               3.50            5.00
# E               0.00            0.00

# %% [markdown]
# ## 5단계 — networkx 로 교차 검증
#
# `nx.betweenness_centrality(G)` 의 기본값이 바로 위의 정규화된 값입니다.

# %%
try:
    import networkx as nx
    G = nx.Graph(EDGES)
    nxbc = nx.betweenness_centrality(G)                     # normalized=True 가 기본
    raw = nx.betweenness_centrality(G, normalized=False)
    for v in sorted(G):
        print(f"{v}  손계산={bc[v]:.4f}  nx={nxbc[v]:.4f}  nx(raw)={raw[v]:.2f}")
    assert all(abs(bc[v] - nxbc[v]) < 1e-9 for v in G)
    print("\n일치")
except ImportError:
    print("networkx 없음 — 건너뜀")
# 출력:
# A  손계산=0.0833  nx=0.0833  nx(raw)=0.50
# B  손계산=0.1667  nx=0.1667  nx(raw)=1.00
# C  손계산=0.1667  nx=0.1667  nx(raw)=1.00
# D  손계산=0.5833  nx=0.5833  nx(raw)=3.50
# E  손계산=0.0000  nx=0.0000  nx(raw)=0.00
#
# 일치

# %% [markdown]
# ## 6단계 — 10장의 회사 그래프
#
# 차수(아는 사람 수) 1등과 매개 1등이 **다른 사람**이라는 게 10장의 핵심입니다.
# 특히 서영업은 이웃이 3명뿐이라 차수로는 눈에 안 띄는데,
# 외주 공장으로 가는 **유일한** 통로라서 매개는 상위권입니다.

# %%
ORG_EDGES = [
    ("김개발", "개발1"), ("김개발", "개발2"), ("김개발", "개발3"),
    ("김개발", "개발4"), ("김개발", "개발5"), ("김개발", "개발6"),
    ("개발1", "개발2"), ("개발2", "개발3"), ("개발3", "개발4"),
    ("개발4", "개발5"), ("개발5", "개발6"),
    ("정영업", "한영업"), ("정영업", "오영업"), ("정영업", "서영업"),
    ("한영업", "오영업"), ("오영업", "서영업"),
    ("강디자", "윤디자"), ("강디자", "임디자"), ("윤디자", "임디자"),
    ("대표", "김개발"), ("대표", "정영업"), ("대표", "강디자"),
    ("서영업", "공장A"),                      # ← 회사와 공장을 잇는 단 하나의 다리
    ("공장A", "공장B"), ("공장A", "공장C"), ("공장B", "공장C"),
    ("청소담당", "개발1"), ("청소담당", "윤디자"),
]

org = {}
for a, b in ORG_EDGES:
    org.setdefault(a, set()).add(b)
    org.setdefault(b, set()).add(a)
org = {k: sorted(v) for k, v in org.items()}

org_score = {v: 0.0 for v in org}
for s, t in combinations(sorted(org), 2):
    ps = all_shortest(org, s, t)
    for p in ps:
        for mid in p[1:-1]:
            org_score[mid] += 1 / len(ps)
m = len(org)
org_bc = {v: s / ((m - 1) * (m - 2) / 2) for v, s in org_score.items()}
org_deg = {v: len(nb) / (m - 1) for v, nb in org.items()}

print(f"{'노드':<8}{'매개':>10}{'차수':>10}{'이웃 수':>8}")
for v in sorted(org, key=lambda x: -org_bc[x])[:6]:
    print(f"{v:<8}{org_bc[v]:>10.3f}{org_deg[v]:>10.3f}{len(org[v]):>8}")

print("\n차수 1등:", max(org_deg, key=org_deg.get))
print("매개 1등:", max(org_bc, key=org_bc.get))

# 이웃이 똑같이 3명인 사람들끼리 매개만 비교하면 «급소»가 드러난다
print("\n이웃 3명짜리끼리 매개 비교:")
for v in sorted((v for v in org if len(org[v]) == 3), key=lambda x: -org_bc[x]):
    print(f"  {v:<8}{org_bc[v]:>8.3f}")
# 출력:
# 노드            매개        차수   이웃 수
# 대표           0.597     0.167       3
# 김개발          0.504     0.389       7
# 정영업          0.484     0.222       4
# 서영업          0.294     0.167       3
# 공장A          0.209     0.167       3
# 강디자          0.182     0.167       3
#
# 차수 1등: 김개발
# 매개 1등: 대표
#
# 이웃 3명짜리끼리 매개 비교:
#   대표        0.597
#   서영업       0.294
#   공장A       0.209
#   강디자       0.182
#   개발1       0.093
#   윤디자       0.052
#   오영업       0.013
#   개발2       0.009
#   개발3       0.003
#   개발4       0.003
#   개발5       0.003

# %% [markdown]
# ## 7단계 — 그림으로 보기
#
# 왼쪽: 다이아몬드 예제. 노드 크기·색이 매개 중심성입니다.
# 오른쪽: 쌍 $A$–$D$ 의 두 최단 경로가 각각 $1/2$ 씩 나눠 갖는 모습.

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    pos = {"A": (0, 0), "B": (1, 0.8), "C": (1, -0.8), "D": (2, 0), "E": (3, 0)}
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("매개 중심성 (정규화)",
                                        "A–D 최단 경로 2개 → 각 1/2"))

    # --- 왼쪽: 전체 그래프 + 중심성 ---
    ex, ey = [], []
    for a, b in EDGES:
        ex += [pos[a][0], pos[b][0], None]
        ey += [pos[a][1], pos[b][1], None]
    fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines",
                             line=dict(color="#b8bec9", width=2),
                             hoverinfo="skip", showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=[pos[v][0] for v in pos], y=[pos[v][1] for v in pos],
        mode="markers+text",
        text=[f"{v}<br>{bc[v]:.2f}" for v in pos], textposition="top center",
        marker=dict(size=[22 + 60 * bc[v] for v in pos],
                    color=[bc[v] for v in pos], colorscale="YlOrRd",
                    cmin=0, cmax=0.6, line=dict(color="#333", width=1),
                    colorbar=dict(title="C_B", x=0.44, len=0.8)),
        showlegend=False), row=1, col=1)

    # --- 오른쪽: A–D 의 두 경로 ---
    fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines",
                             line=dict(color="#dde1e7", width=2),
                             hoverinfo="skip", showlegend=False), row=1, col=2)
    for path, color, name in ((["A", "B", "D"], "#e4572e", "A→B→D  (1/2)"),
                              (["A", "C", "D"], "#2e86ab", "A→C→D  (1/2)")):
        fig.add_trace(go.Scatter(
            x=[pos[v][0] for v in path], y=[pos[v][1] for v in path],
            mode="lines", line=dict(color=color, width=5), name=name,
            opacity=0.85), row=1, col=2)
    fig.add_trace(go.Scatter(
        x=[pos[v][0] for v in pos], y=[pos[v][1] for v in pos],
        mode="markers+text", text=list(pos), textposition="top center",
        marker=dict(size=24, color="#ffffff", line=dict(color="#333", width=2)),
        showlegend=False), row=1, col=2)

    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    fig.update_layout(width=1000, height=470, template="plotly_white",
                      title="매개 중심성: 최단 경로가 여러 개면 1/σ 씩 나눠 더한다",
                      legend=dict(orientation="h", x=0.58, y=-0.02),
                      margin=dict(b=70))
    _show(fig)
    fig.write_image("expy.png", scale=2)
    print("expy.png 저장")
except ImportError as e:
    print("plotly/kaleido 없음 — 건너뜀:", e)
# 출력: expy.png 저장

# %% [markdown]
# ## 마무리 — 정의는 쉬운데 계산은 비싸다
#
# 정의를 곧이곧대로 구현하면 **모든 쌍**의 최단 경로를 전부 열거해야 합니다.
# 실무에서는 브랜디스(Brandes) 알고리즘을 씁니다. 각 시작 노드마다
#
# 1. BFS 로 거리와 최단 경로 개수 $\sigma$ 를 세고 (전방 패스),
# 2. 먼 노드부터 거꾸로 내려오며 의존도
#    $\delta_s(v) = \sum_{w:\,v \in \text{pred}(w)} \dfrac{\sigma_v}{\sigma_w}\bigl(1 + \delta_s(w)\bigr)$
#    를 누적합니다 (후방 패스).
#
# 경로를 **열거하지 않고** 개수만 세므로 $O(VE)$ (가중치 없는 그래프) 에 끝납니다.
# 그래도 100만 노드에서는 며칠이 걸리므로, 10장은 시작 노드를 5% 만 표본으로
# 뽑는 근사를 권합니다. 값 자체가 아니라 **순위**만 필요할 때 잘 듣습니다.

# %%
try:
    import networkx as nx
    G2 = nx.Graph(ORG_EDGES)
    b_exact = nx.betweenness_centrality(G2)
    b_k = nx.betweenness_centrality(G2, k=8, seed=42)     # 시작 노드 8개만 표본
    top = lambda d, n=3: [v for v, _ in sorted(d.items(), key=lambda x: -x[1])[:n]]
    print("전수 상위3:", top(b_exact))
    print("표본 상위3:", top(b_k))
except ImportError:
    print("networkx 없음 — 건너뜀")
# 출력:
# 전수 상위3: ['서영업', '대표', '김개발']
# 표본 상위3: ['서영업', '대표', '김개발']
