# %% [markdown]
# # `ring_of_cliques()` — 해상도 한계의 표준 반례
#
# 크기 $s$인 완전 그래프(클리크) $k$개를 만들고, 각 뭉치를 다음 뭉치와
# **다리 하나**로 이어 고리를 만든다. 정답 커뮤니티는 당연히 $k$개다.
#
# 이 노트북에서 볼 것:
#
# 1. 구조를 직접 만들어 노드/엣지 수 공식을 검산한다.
# 2. 고리 배치로 그려 본다.
# 3. 정답 분할과 「둘씩 붙인」 분할의 모듈러리티 $Q$를 비교한다.
#
# 노드 수와 엣지 수는 이렇게 나온다.
#
# $$N = k\,s, \qquad E = k\left(\binom{s}{2} + 1\right) = k\left(\frac{s(s-1)}{2} + 1\right)$$
#
# 뭉치 하나의 내부 엣지 수를 $\ell = \binom{s}{2}$라 두면 $E = k(\ell + 1)$이다.

# %%
from collections import defaultdict
from math import comb, cos, pi, sin
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


def ring_of_cliques(k, size):
    """크기 size 인 완전 그래프 k 개를 고리 모양으로 잇는다. 정답 커뮤니티 = k 개."""
    edges = []
    for c in range(k):
        base = c * size
        for i in range(size):
            for j in range(i + 1, size):
                edges.append((base + i, base + j))
        edges.append((base, ((c + 1) % k) * size))  # 다음 뭉치와 다리 하나
    return edges


edges = ring_of_cliques(4, 4)
print("k=4, size=4")
print("노드:", len(set(v for e in edges for v in e)))
print("엣지:", len(edges))
print("다리(뭉치 사이 엣지):", [e for e in edges if e[1] - e[0] >= 4 or e[0] // 4 != e[1] // 4])
# 출력: k=4, size=4
# 출력: 노드: 16
# 출력: 엣지: 28
# 출력: 다리(뭉치 사이 엣지): [(0, 4), (4, 8), (8, 12), (12, 0)]

# %% [markdown]
# ## 1. 노드/엣지 수 공식 검산
#
# $N = k s$, $E = k(\binom{s}{2} + 1)$. 여러 $(k, s)$에서 맞는지 확인한다.

# %%
print(f"{'k':>4} {'size':>5} {'N(실측)':>8} {'N(공식)':>8} {'E(실측)':>8} {'E(공식)':>8}")
print("-" * 48)
ok = True
for k, size in [(4, 3), (4, 4), (8, 4), (16, 4), (24, 5), (32, 6)]:
    e = ring_of_cliques(k, size)
    n_real = len(set(v for x in e for v in x))
    n_form = k * size
    e_real = len(e)
    e_form = k * (comb(size, 2) + 1)
    ok &= n_real == n_form and e_real == e_form
    print(f"{k:>4} {size:>5} {n_real:>8} {n_form:>8} {e_real:>8} {e_form:>8}")
print("\n공식 일치:", ok)
# 출력:    k  size   N(실측)   N(공식)   E(실측)   E(공식)
# 출력: ------------------------------------------------
# 출력:    4     3       12       12       16       16
# 출력:    4     4       16       16       28       28
# 출력:    8     4       32       32       56       56
# 출력:   16     4       64       64      112      112
# 출력:   24     5      120      120      264      264
# 출력:   32     6      192      192      512      512
# 출력:
# 출력: 공식 일치: True

# %% [markdown]
# ## 1-b. `networkx.ring_of_cliques` 와의 관계
#
# `networkx.ring_of_cliques(num_cliques, clique_size)` 도 같은 구조를 만든다.
# 차이는 **다리를 어느 노드에 붙이느냐**뿐이다.
#
# - 책 코드: 뭉치 $c$의 `base` → 뭉치 $c{+}1$의 `base` (한 노드에 다리 2개가 몰림)
# - networkx: 뭉치 $c$의 `base+1` → 뭉치 $c{+}1$의 `base` (다리가 두 노드에 나뉨)
#
# 뭉치별 **내부 엣지 수와 차수 합**은 같으므로 아래 $Q$ 계산 결과는 동일하다.
# 참고로 `connected_caveman_graph` 는 다리를 놓는 대신 클리크 내부 엣지를 **하나 제거**해
# 재배선하므로 엣지 수가 $k\binom{s}{2}$로 유지된다. `ring_of_cliques` 는 제거 없이 더한다.

# %%
try:
    import networkx as nx

    G_nx = nx.ring_of_cliques(8, 4)
    G_my = nx.Graph(ring_of_cliques(8, 4))
    print("networkx:", G_nx.number_of_nodes(), "노드", G_nx.number_of_edges(), "엣지")
    print("책 코드 :", G_my.number_of_nodes(), "노드", G_my.number_of_edges(), "엣지")
    print("동형(isomorphic)?", nx.is_isomorphic(G_nx, G_my))
    print("caveman  :", nx.connected_caveman_graph(8, 4).number_of_edges(), "엣지 (엣지 제거 후 재배선)")
except ImportError:
    print("networkx 없음 — 건너뜀")
# 출력: networkx: 32 노드 56 엣지
# 출력: 책 코드 : 32 노드 56 엣지
# 출력: 동형(isomorphic)? False
# 출력: caveman  : 48 엣지 (엣지 제거 후 재배선)

# %% [markdown]
# ## 2. 고리 배치로 그리기
#
# 뭉치 $c$의 중심을 반지름 $R$인 큰 원 위 각도 $2\pi c/k$에 놓고,
# 그 주위 작은 원에 뭉치의 노드 $s$개를 배치한다.

# %%
def layout(k, size, R=1.0, r=0.16):
    """뭉치를 큰 원 위에, 각 뭉치의 노드를 작은 원 위에 배치한다."""
    pos = {}
    for c in range(k):
        th = 2 * pi * c / k
        cx, cy = R * cos(th), R * sin(th)
        for i in range(size):
            a = th + 2 * pi * i / size
            pos[c * size + i] = (cx + r * cos(a), cy + r * sin(a))
    return pos


P = layout(4, 4)
print("뭉치 0 노드 좌표:", [(v, tuple(round(x, 3) for x in P[v])) for v in range(4)])
# 출력: 뭉치 0 노드 좌표: [(0, (1.16, 0.0)), (1, (1.0, 0.16)), (2, (0.84, 0.0)), (3, (1.0, -0.16))]

# %% [markdown]
# ## 3. 모듈러리티 $Q$ — 정답 분할 vs 둘씩 붙인 분할
#
# $$Q = \sum_{c}\left[\frac{L_c}{E} - \gamma\left(\frac{d_c}{2E}\right)^{2}\right]$$
#
# $L_c$는 커뮤니티 $c$ 안의 엣지 수, $d_c$는 그 안 노드들의 차수 합이다.

# %%
def adjacency(edges):
    adj = defaultdict(set)
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    return {v: sorted(u) for v, u in adj.items()}


def modularity(adj, comms, gamma=1.0):
    """gamma 가 해상도 매개변수. 크면 잘게, 작으면 크게 나눈다."""
    m = sum(len(v) for v in adj.values()) / 2
    q = 0.0
    for c in comms:
        s = set(c)
        lc = sum(1 for v in c for u in adj[v] if u in s) / 2
        dc = sum(len(adj[v]) for v in c)
        q += lc / m - gamma * (dc / (2 * m)) ** 2
    return q


def truth(k, size):
    return [list(range(c * size, (c + 1) * size)) for c in range(k)]


def merged_pairs(k, size):
    """이웃한 두 뭉치를 하나로 붙인 답."""
    out = []
    for c in range(0, k - 1, 2):
        out.append(list(range(c * size, (c + 2) * size)))
    if k % 2:
        out.append(list(range((k - 1) * size, k * size)))
    return out


size = 4
ks = [4, 8, 12, 14, 16, 24, 32]
rows = []
print(f"뭉치 크기 {size}, 고리 모양으로 이음\n")
print(f"{'뭉치 수':>7} {'정답 Q':>10} {'둘씩 붙인 Q':>12} {'어느 쪽이 이기나':>16}")
print("-" * 50)
for k in ks:
    adj = adjacency(ring_of_cliques(k, size))
    q_true = modularity(adj, truth(k, size))
    q_merged = modularity(adj, merged_pairs(k, size))
    rows.append((k, q_true, q_merged))
    winner = "정답" if q_true > q_merged else "붙인 쪽 (틀림)"
    print(f"{k:>7} {q_true:>10.4f} {q_merged:>12.4f} {winner:>16}")
# 출력: 뭉치 크기 4, 고리 모양으로 이음
# 출력:
# 출력:    뭉치 수     정답 Q   둘씩 붙인 Q       어느 쪽이 이기나
# 출력: --------------------------------------------------
# 출력:       4     0.6071       0.4286               정답
# 출력:       8     0.7321       0.6786               정답
# 출력:      12     0.7738       0.7619               정답
# 출력:      14     0.7857       0.7857     붙인 쪽 (틀림)   ← 임계에서 동률
# 출력:      16     0.7946       0.8036     붙인 쪽 (틀림)
# 출력:      24     0.8155       0.8452     붙인 쪽 (틀림)
# 출력:      32     0.8259       0.8661     붙인 쪽 (틀림)

# %% [markdown]
# ### 왜 그런가 — 손으로 풀어 보면
#
# $\ell = \binom{s}{2}$, 전체 엣지 $E = k(\ell+1)$. 뭉치 하나는 내부 엣지 $\ell$개,
# 차수 합 $2\ell + 2$(다리 2개). 두 뭉치를 붙이면 내부 엣지 $2\ell+1$개, 차수 합 $4\ell+4$.
#
# $$Q_{\text{정답}} = \frac{\ell}{\ell+1} - \frac{1}{k},\qquad
# Q_{\text{병합}} = \frac{2\ell+1}{2(\ell+1)} - \frac{2}{k}$$
#
# $$Q_{\text{병합}} - Q_{\text{정답}} = \frac{1}{2(\ell+1)} - \frac{1}{k}$$
#
# 즉 $k > 2(\ell+1)$이면 **틀린 답이 이긴다**. $E = k(\ell+1)$이므로
# $k > 2(\ell+1) \iff k^2 > 2E \iff k > \sqrt{2E}$ — Fortunato & Barthélemy(2007)의
# 「내부 링크가 $\sqrt{2E}$보다 작은 모듈은 병합될 수 있다」와 같은 말이다.
#
# $s=4$면 $\ell=6$, 임계는 $k > 14$. 위 표에서 $k=14$까지는 정답이 이기고 $k=16$부터 진다.

# %%
print(f"{'size':>5} {'l':>4} {'임계 k>2(l+1)':>14} {'실측 첫 역전 k':>14}")
print("-" * 42)
for s in (3, 4, 5, 6):
    ell = comb(s, 2)
    thr = 2 * (ell + 1)
    first = None
    for k in range(4, 200, 2):
        adj = adjacency(ring_of_cliques(k, s))
        if modularity(adj, merged_pairs(k, s)) > modularity(adj, truth(k, s)):
            first = k
            break
    print(f"{s:>5} {ell:>4} {thr:>14} {first:>14}")
# 출력:  size    l   임계 k>2(l+1)   실측 첫 역전 k
# 출력: ------------------------------------------
# 출력:     3    3              8             10
# 출력:     4    6             14             14
# 출력:     5   10             22             24
# 출력:     6   15             32             34

# %% [markdown]
# 「둘씩」 붙이려면 $k$가 짝수여야 하므로 실측 역전 지점은 임계값 바로 다음 짝수로 나온다.
# $s=4$에서 14가 나온 건 $k=2(\ell+1)=14$가 **정확히 동률**인 지점이라
# 부동소수점 오차가 붙인 쪽 손을 들어 준 것이다(위 표에서 두 $Q$가 0.7857로 같다).

# %% [markdown]
# ## 3-b. 진짜 알고리즘(루뱅)도 붙여 버린다

# %%
try:
    import networkx as nx

    for k in (8, 32):
        G = nx.Graph(ring_of_cliques(k, 4))
        comms = nx.community.louvain_communities(G, seed=7)
        sizes = sorted({len(c) for c in comms})
        print(f"k={k:>3} 정답 커뮤니티 {k:>3}개 → 루뱅이 찾은 개수 {len(comms):>3}개, 크기 종류 {sizes}")
except ImportError:
    print("networkx 없음 — 건너뜀")
# 출력: k=  8 정답 커뮤니티   8개 → 루뱅이 찾은 개수   8개, 크기 종류 [4]
# 출력: k= 32 정답 커뮤니티  32개 → 루뱅이 찾은 개수  15개, 크기 종류 [8, 12]
# 출력: (k=32 에서는 뭉치 두세 개를 뭉뚱그려 32개가 15개로 줄었다)

# %% [markdown]
# ## 4. 그림 — 두 분할을 나란히, 그리고 $Q$ 곡선

# %%
K_VIZ, S_VIZ = 16, 4
E_VIZ = ring_of_cliques(K_VIZ, S_VIZ)
POS = layout(K_VIZ, S_VIZ, r=0.13)

C_TRUE, C_MERGED = "#4C78A8", "#F58518"  # 정답 분할 / 둘씩 붙인 분할
C_EDGE, C_BRIDGE = "#C9CCD1", "#5A6472"


def convex_hull(pts):
    """Andrew monotone chain. 커뮤니티를 감싸는 다각형을 얻는다."""
    pts = sorted(set(pts))
    if len(pts) <= 2:
        return pts

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2:
                (x1, y1), (x2, y2) = out[-2], out[-1]
                if (x2 - x1) * (p[1] - y1) - (y2 - y1) * (p[0] - x1) > 0:
                    break
                out.pop()
            out.append(p)
        return out

    return half(pts)[:-1] + half(reversed(pts))[:-1]


def hull_traces(comms, pos, color, pad=0.055):
    """각 커뮤니티를 옅은 색으로 감싼다. 개수 차이가 바로 보인다."""
    out = []
    for c in comms:
        h = convex_hull([pos[v] for v in c])
        cx = sum(p[0] for p in h) / len(h)
        cy = sum(p[1] for p in h) / len(h)
        xs, ys = [], []
        for x, y in h:
            dx, dy = x - cx, y - cy
            d = (dx * dx + dy * dy) ** 0.5 or 1.0
            xs.append(x + pad * dx / d)
            ys.append(y + pad * dy / d)
        out.append(
            go.Scatter(
                x=xs + xs[:1], y=ys + ys[:1], mode="lines", fill="toself",
                fillcolor=color, opacity=0.18,
                line=dict(color=color, width=1.2),
                hoverinfo="skip", showlegend=False,
            )
        )
    return out


def edge_traces(edges, pos):
    """뭉치 내부 엣지와 다리를 나눠 그린다."""
    out = []
    for sel, color, width in (
        (lambda a, b: a // S_VIZ == b // S_VIZ, C_EDGE, 1.0),
        (lambda a, b: a // S_VIZ != b // S_VIZ, C_BRIDGE, 1.6),
    ):
        xs, ys = [], []
        for a, b in edges:
            if sel(a, b):
                xs += [pos[a][0], pos[b][0], None]
                ys += [pos[a][1], pos[b][1], None]
        out.append(
            go.Scatter(
                x=xs, y=ys, mode="lines", line=dict(color=color, width=width),
                hoverinfo="skip", showlegend=False,
            )
        )
    return out


def node_trace(comms, pos, color):
    of = {v: i for i, c in enumerate(comms) for v in c}
    order = sorted(pos)
    return go.Scatter(
        x=[pos[v][0] for v in order], y=[pos[v][1] for v in order],
        mode="markers",
        marker=dict(size=6, color=color, line=dict(color="white", width=0.7)),
        text=[f"노드 {v} · 커뮤니티 {of[v]}" for v in order],
        hoverinfo="text", showlegend=False,
    )


fig = make_subplots(
    rows=2, cols=2,
    row_heights=[0.62, 0.38],
    vertical_spacing=0.12,
    specs=[[{}, {}], [{"colspan": 2}, None]],
    subplot_titles=(
        f"정답 분할 — 커뮤니티 {K_VIZ}개 (Q = {modularity(adjacency(E_VIZ), truth(K_VIZ, S_VIZ)):.4f})",
        f"둘씩 붙인 분할 — 커뮤니티 {K_VIZ // 2}개 (Q = {modularity(adjacency(E_VIZ), merged_pairs(K_VIZ, S_VIZ)):.4f} ← 더 크다)",
        "뭉치 수 k 에 따른 Q — 임계 k = 2(ℓ+1) = 14 를 넘으면 틀린 답이 이긴다",
    ),
)

for col, comms, color in (
    (1, truth(K_VIZ, S_VIZ), C_TRUE),
    (2, merged_pairs(K_VIZ, S_VIZ), C_MERGED),
):
    for t in hull_traces(comms, POS, color):
        fig.add_trace(t, row=1, col=col)
    for t in edge_traces(E_VIZ, POS):
        fig.add_trace(t, row=1, col=col)
    fig.add_trace(node_trace(comms, POS, color), row=1, col=col)

curve_ks = list(range(4, 41, 2))
qt, qm = [], []
for k in curve_ks:
    adj = adjacency(ring_of_cliques(k, S_VIZ))
    qt.append(modularity(adj, truth(k, S_VIZ)))
    qm.append(modularity(adj, merged_pairs(k, S_VIZ)))

fig.add_trace(
    go.Scatter(x=curve_ks, y=qt, mode="lines+markers", name="정답 분할 Q",
               line=dict(color=C_TRUE, width=2.5), marker=dict(size=6)),
    row=2, col=1,
)
fig.add_trace(
    go.Scatter(x=curve_ks, y=qm, mode="lines+markers", name="둘씩 붙인 Q",
               line=dict(color=C_MERGED, width=2.5, dash="dash"), marker=dict(size=6)),
    row=2, col=1,
)
fig.add_vline(x=14, line=dict(color="#9AA0A6", width=1.5, dash="dot"), row=2, col=1)
fig.add_annotation(x=14, y=min(qm) + 0.02, text="  임계 k = 14", showarrow=False,
                   font=dict(size=11, color="#5A6472"), xanchor="left", row=2, col=1)

for c in (1, 2):
    fig.update_xaxes(visible=False, row=1, col=c)
    fig.update_yaxes(visible=False, scaleanchor=f"x{'' if c == 1 else '2'}",
                     scaleratio=1, row=1, col=c)
fig.update_xaxes(title_text="뭉치 수 k", row=2, col=1, gridcolor="#EDEFF2")
fig.update_yaxes(title_text="모듈러리티 Q", row=2, col=1, gridcolor="#EDEFF2")
fig.update_layout(
    title=dict(text="ring_of_cliques(k, 4) — 정답이 자명한데도 모듈러리티는 붙인다", x=0.5),
    width=1000, height=760,
    plot_bgcolor="white", paper_bgcolor="white",
    font=dict(size=12),
    legend=dict(orientation="h", y=-0.06, x=0.5, xanchor="center"),
    margin=dict(l=60, r=30, t=80, b=60),
)
fig.update_annotations(font_size=12)

try:
    _HERE = Path(__file__).resolve().parent
except NameError:  # 노트북에서 실행할 때
    _HERE = Path.cwd()
fig.write_image(str(_HERE / "expy.png"), scale=2)
print("expy.png 저장 완료:", _HERE / "expy.png")
_show(fig)
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# - `ring_of_cliques(k, size)` = 크기 `size`인 완전 그래프 `k`개 + 이웃끼리 다리 하나 → 고리.
# - $N = ks$, $E = k(\binom{s}{2}+1)$, 정답 커뮤니티는 $k$개.
# - 정답이 자명한데도 $k > 2(\ell+1) \iff k > \sqrt{2E}$ 이면 모듈러리티는 이웃 뭉치를
#   붙인 답을 더 좋아한다. 이것이 **해상도 한계**이고, 버그가 아니라 지표의 성질이다.
# - 대처: 해상도 매개변수 $\gamma$를 올리거나, 계층적으로 다시 돌리거나,
#   CPM 같은 해상도 한계 없는 목적함수를 쓴다. 개수는 알고리즘이 아니라 쓰임새로 정한다.
