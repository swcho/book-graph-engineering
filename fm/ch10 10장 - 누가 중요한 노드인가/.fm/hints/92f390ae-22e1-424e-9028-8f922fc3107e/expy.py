# %% [markdown]
# # 해상도 매개변수 $\gamma$ 가 하는 일
#
# 일반화 모듈러리티(Reichardt–Bornholdt, 2006)는 이렇게 생겼다.
#
# $$
# Q_\gamma = \sum_{c}\left[\frac{L_c}{m} - \gamma\left(\frac{d_c}{2m}\right)^2\right]
# $$
#
# - $L_c$: 커뮤니티 $c$ 안쪽 간선 수, $d_c$: $c$ 안 노드들의 차수 합, $m$: 전체 간선 수
# - $\gamma$ 는 **기대값 항** $(d_c/2m)^2$ 에만 곱해진다. 관측 항 $L_c/m$ 은 건드리지 않는다.
# - $\gamma$ 를 키우면 「큰 덩어리」에 물리는 벌점이 커져서 **잘게** 나뉘고,
#   줄이면 벌점이 약해져서 **크게** 뭉친다. $\gamma = 1$ 이 원래 뉴먼–거번 모듈러리티다.
#
# 아래에서 뭉치 고리(ring of cliques) 그래프를 만들어 놓고 $\gamma$ 를 스윕하면서
# 찾아진 커뮤니티 개수와 정답 대비 일치도(NMI)가 어떻게 움직이는지 본다.

# %%
import math
from collections import defaultdict

import networkx as nx
import plotly.graph_objects as go
from plotly.subplots import make_subplots

SEEDS = [0, 1, 2, 3, 4]  # 루뱅은 무작위성이 있다. 시드를 고정해 재현 가능하게.

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SOFT = "#52514e"
BLUE = "#2a78d6"
ORANGE = "#eb6834"


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


print("networkx", nx.__version__)
# 출력: networkx 3.2.1

# %% [markdown]
# ## 1. 정답이 뻔한 그래프 만들기
#
# 크기 4짜리 완전 그래프(clique) 16개를 고리 모양으로 이어 붙인다.
# 사람 눈으로 보면 정답은 명백하게 **16개 뭉치**다.

# %%
K, SIZE = 16, 4


def ring_of_cliques(k, size):
    """크기 size 인 완전 그래프 k 개를 고리로 잇는다. 정답 커뮤니티 = k 개."""
    g = nx.Graph()
    for c in range(k):
        base = c * size
        for i in range(size):
            for j in range(i + 1, size):
                g.add_edge(base + i, base + j)
        g.add_edge(base, ((c + 1) % k) * size)  # 다음 뭉치로 가는 다리 하나
    return g


G = ring_of_cliques(K, SIZE)
TRUTH = [set(range(c * SIZE, (c + 1) * SIZE)) for c in range(K)]

print(f"노드 {G.number_of_nodes()}, 간선 {G.number_of_edges()}, 정답 커뮤니티 {len(TRUTH)}개")
# 출력: 노드 64, 간선 112, 정답 커뮤니티 16개

# %% [markdown]
# ## 2. $\gamma$ 를 손으로 넣어 본 $Q_\gamma$ — 해상도 한계의 정체
#
# 「정답(뭉치 16개)」과 「이웃한 뭉치를 둘씩 붙인 답(8개)」의 $Q_\gamma$ 를 직접 비교한다.
# $\gamma = 1$ 에서 **붙인 쪽이 이기면** 그게 바로 해상도 한계다.
# 모듈러리티를 최대화하는 알고리즘은 점수가 높은 쪽을 고르므로 작은 뭉치를 붙여 버린다.

# %%
def modularity_gamma(g, comms, gamma=1.0):
    """Q_gamma = Σ_c [ L_c/m - gamma*(d_c/2m)^2 ]. gamma 는 기대값 항에만 곱해진다."""
    m = g.number_of_edges()
    deg = dict(g.degree())
    q = 0.0
    for c in comms:
        s = set(c)
        lc = sum(1 for v in s for u in g[v] if u in s) / 2
        dc = sum(deg[v] for v in s)
        q += lc / m - gamma * (dc / (2 * m)) ** 2
    return q


MERGED = [set(range(c * SIZE, (c + 2) * SIZE)) for c in range(0, K, 2)]  # 둘씩 붙인 답

print(f"{'gamma':>6} {'정답 Q(16개)':>14} {'붙인 Q(8개)':>13} {'이기는 쪽':>12}")
for g_ in (0.5, 0.8, 1.0, 1.2, 1.5, 2.0):
    qt = modularity_gamma(G, TRUTH, g_)
    qm = modularity_gamma(G, MERGED, g_)
    print(f"{g_:>6.1f} {qt:>14.4f} {qm:>13.4f} {'정답' if qt > qm else '붙인 쪽 (틀림)':>12}")
# 출력:
#  gamma      정답 Q(16개)      붙인 Q(8개)        이기는 쪽
#    0.5         0.8259        0.8661    붙인 쪽 (틀림)
#    0.8         0.8071        0.8286    붙인 쪽 (틀림)
#    1.0         0.7946        0.8036    붙인 쪽 (틀림)   ← 고전 모듈러리티가 지는 지점
#    1.2         0.7821        0.7786           정답
#    1.5         0.7634        0.7411           정답
#    2.0         0.7321        0.6786           정답

# %% [markdown]
# 기대값 항에 곱해지는 $\gamma$ 가 커질수록 **큰 커뮤니티가 더 크게 손해**를 본다.
# $d_c$ 는 커뮤니티가 커질수록 커지고, 벌점은 $d_c^2$ 에 비례하기 때문이다.
# 그래서 「병합해서 얻는 이득」이 줄고, 최적해가 잘게 쪼개지는 쪽으로 이동한다.

# %% [markdown]
# ## 3. 정답 대비 일치도 재기 — NMI
#
# 두 분할이 얼마나 같은지를 재는 표준 지표. 1이면 완전히 같고 0이면 무관하다.
#
# $$
# \mathrm{NMI}(X, Y) = \frac{2\,I(X;Y)}{H(X) + H(Y)}
# $$

# %%
def nmi(part_a, part_b):
    """정규화 상호정보량. 두 분할은 같은 노드 집합을 덮는다고 가정."""
    n = sum(len(c) for c in part_a)
    lab_a = {v: i for i, c in enumerate(part_a) for v in c}
    lab_b = {v: i for i, c in enumerate(part_b) for v in c}
    joint = defaultdict(int)
    for v in lab_a:
        joint[(lab_a[v], lab_b[v])] += 1

    def entropy(part):
        return -sum((len(c) / n) * math.log(len(c) / n) for c in part if c)

    ha, hb = entropy(part_a), entropy(part_b)
    mi = 0.0
    for (a, b), nij in joint.items():
        pij = nij / n
        mi += pij * math.log(pij / ((len(part_a[a]) / n) * (len(part_b[b]) / n)))
    return 0.0 if ha + hb == 0 else 2 * mi / (ha + hb)


print(f"정답 vs 정답  NMI = {nmi(TRUTH, TRUTH):.3f}")
print(f"정답 vs 둘씩붙임 NMI = {nmi(TRUTH, MERGED):.3f}")
print(f"정답 vs 전체하나 NMI = {nmi(TRUTH, [set(G.nodes())]):.3f}")
# 출력:
# 정답 vs 정답  NMI = 1.000
# 정답 vs 둘씩붙임 NMI = 0.857
# 정답 vs 전체하나 NMI = 0.000

# %% [markdown]
# ## 4. $\gamma$ 스윕
#
# `networkx.community.louvain_communities(G, resolution=γ)` 를 $\gamma$ 를 바꿔 가며 돌린다.
# 시드 5개의 평균을 쓴다 (루뱅은 시드에 따라 답이 흔들리므로).

# %%
N_STEPS = 40
GAMMAS = [round(0.2 * (24.0 / 0.2) ** (i / (N_STEPS - 1)), 3) for i in range(N_STEPS)]  # 0.2 ~ 24, 로그 간격

counts, scores = [], []
for gamma in GAMMAS:
    cs, ss = [], []
    for seed in SEEDS:
        part = nx.community.louvain_communities(G, resolution=gamma, seed=seed)
        cs.append(len(part))
        ss.append(nmi(TRUTH, [set(c) for c in part]))
    counts.append(sum(cs) / len(cs))
    scores.append(sum(ss) / len(ss))

for i in range(0, N_STEPS, 4):  # 4칸마다 하나씩만 출력
    print(f"gamma={GAMMAS[i]:<7} 커뮤니티 {counts[i]:>5.1f}개  NMI {scores[i]:.3f}")
# 출력:
# gamma=0.2     커뮤니티   5.0개  NMI 0.725
# gamma=0.327   커뮤니티   7.2개  NMI 0.828
# gamma=0.534   커뮤니티   7.2개  NMI 0.828
# gamma=0.873   커뮤니티   8.8개  NMI 0.873   ← gamma≈1 에서 뭉치를 붙여 버린다
# gamma=1.426   커뮤니티  16.0개  NMI 1.000
# gamma=2.33    커뮤니티  16.0개  NMI 1.000
# gamma=3.807   커뮤니티  16.0개  NMI 1.000
# gamma=6.22    커뮤니티  16.0개  NMI 1.000
# gamma=10.163  커뮤니티  16.0개  NMI 1.000
# gamma=16.606  커뮤니티  32.0개  NMI 0.908   ← 너무 키우면 뭉치를 쪼개 버린다

# %% [markdown]
# ## 5. 안정 구간(plateau) 찾기
#
# 실무 절차는 이렇다.
#
# 1. $\gamma$ 를 넓게 스윕한다 (보통 로그 눈금으로 0.1 ~ 10).
# 2. **커뮤니티 개수가 $\gamma$ 를 흔들어도 잘 안 변하는 구간**을 찾는다. 그게 plateau다.
# 3. plateau 한가운데 값을 고른다. 경계 근처 값은 조금만 흔들려도 답이 바뀐다.
# 4. 그래도 남는 질문 — 「정답이 몇 개인지」는 알고리즘이 아니라 **쓰임새**가 정한다.

# %%
best, run_start = (0, None, None), 0
for i in range(1, len(GAMMAS) + 1):
    if i == len(GAMMAS) or counts[i] != counts[run_start]:
        if i - run_start > best[0]:
            best = (i - run_start, GAMMAS[run_start], GAMMAS[i - 1])
        run_start = i

width, lo, hi = best
mid = math.sqrt(lo * hi)  # 로그 눈금이므로 기하평균이 「한가운데」다
print(f"가장 긴 안정 구간: gamma {lo} ~ {hi} (스윕 점 {width}개), 커뮤니티 개수 고정")
print(f"추천 gamma = {mid:.2f}  (구간 한가운데)")
# 출력:
# 가장 긴 안정 구간: gamma 1.261 ~ 14.688 (스윕 점 21개), 커뮤니티 개수 고정
# 추천 gamma = 4.30  (구간 한가운데)

# %%
fig = make_subplots(
    rows=2,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.12,
    subplot_titles=("찾아진 커뮤니티 개수 (정답 16개)", "정답 대비 일치도 NMI"),
)

fig.add_trace(
    go.Scatter(
        x=GAMMAS, y=counts, mode="lines+markers", line=dict(color=BLUE, width=2),
        marker=dict(size=6), name="커뮤니티 개수",
        hovertemplate="γ=%{x}<br>커뮤니티 %{y:.1f}개<extra></extra>",
    ),
    row=1, col=1,
)
fig.add_hline(y=K, row=1, col=1, line=dict(color=INK_SOFT, width=1, dash="dot"))

fig.add_trace(
    go.Scatter(
        x=GAMMAS, y=scores, mode="lines+markers", line=dict(color=ORANGE, width=2),
        marker=dict(size=6), name="NMI",
        hovertemplate="γ=%{x}<br>NMI %{y:.3f}<extra></extra>",
    ),
    row=2, col=1,
)

TICKS = [0.2, 0.5, 1, 2, 5, 10, 20]
XRANGE = [math.log10(0.16), math.log10(30)]  # 로그 축의 range 는 log10 값으로 준다
fig.update_xaxes(
    type="log", range=XRANGE, tickmode="array", tickvals=TICKS, ticktext=[str(t) for t in TICKS],
    title_text="해상도 매개변수 γ (로그 눈금)", row=2, col=1,
)
fig.update_xaxes(
    type="log", range=XRANGE, tickmode="array", tickvals=TICKS,
    ticktext=[str(t) for t in TICKS], row=1, col=1,
)
fig.update_yaxes(title_text="개수", row=1, col=1)
fig.update_yaxes(title_text="NMI", range=[0, 1.08], row=2, col=1)
fig.update_layout(
    title="γ 를 키우면 잘게, 줄이면 크게 — 뭉치 고리 16개에서의 스윕",
    showlegend=False,
    height=620,
    width=900,
    paper_bgcolor=SURFACE,
    plot_bgcolor=SURFACE,
    font=dict(color=INK, size=13),
    margin=dict(t=90, r=40, b=60, l=70),
)
fig.update_xaxes(gridcolor="#e7e6e2", zeroline=False)
fig.update_yaxes(gridcolor="#e7e6e2", zeroline=False)

# 안정 구간 음영. 축을 log 로 바꾼 «뒤에» add_shape 로 직접 얹는다.
for xref, yref in (("x", "y domain"), ("x2", "y2 domain")):
    fig.add_shape(
        type="rect", xref=xref, yref=yref, x0=lo, x1=hi, y0=0, y1=1,
        fillcolor=BLUE, opacity=0.10, line_width=0, layer="below",
    )
fig.add_annotation(
    xref="x", yref="y", x=math.log10(mid), y=K, yshift=20,
    text=f"안정 구간(plateau) γ {lo} ~ {hi}", showarrow=False,
    font=dict(color=INK_SOFT, size=12),
)

_show(fig)

import os

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(out, scale=2)
print("저장:", out)
# 출력: 저장: .../92f390ae-22e1-424e-9028-8f922fc3107e/expy.png

# %% [markdown]
# ## 정리
#
# - $\gamma$ 는 $Q_\gamma$ 의 **기대값 항** $(d_c/2m)^2$ 에 곱해지는 계수다. 관측 항은 그대로다.
# - 크게 → 병합 이득이 줄어 **잘게** 나뉜다. 작게 → 벌점이 약해져 **크게** 뭉친다.
# - $\gamma = 1$ 이 고전 모듈러리티이며, 이 값에서 해상도 한계(작은 뭉치 병합)가 나타날 수 있다.
# - 「옳은 $\gamma$」를 주는 공식은 없다. 스윕해서 plateau를 찾고, 최종 개수는 쓰임새로 정한다.
