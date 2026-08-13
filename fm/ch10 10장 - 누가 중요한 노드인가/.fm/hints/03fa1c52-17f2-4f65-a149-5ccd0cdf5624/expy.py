# %% [markdown]
# # 모듈러리티 $Q$ 의 두 항을 손으로 뜯어보기
#
# $$
# Q \;=\; \sum_{c \in C}\left[\underbrace{\frac{l_c}{m}}_{\text{관측: 안쪽 엣지 비율}}
#          \;-\; \underbrace{\left(\frac{d_c}{2m}\right)^{2}}_{\text{기대: 구성 모형 귀무값}}\right]
# $$
#
# - $m$ : 전체 엣지 수
# - $l_c$ : 커뮤니티 $c$ 내부 엣지 수
# - $d_c$ : $c$ 에 속한 노드들의 차수 합
#
# 이 노트북에서 확인할 것
#
# 1. 작은 그래프(삼각형 두 개 + 다리)에서 두 항을 손으로 계산
# 2. 분할을 바꿔 가며 $Q$ 비교 — 왜 "전체 한 덩어리"가 0점인지
# 3. `networkx.community.modularity` 와 값이 일치하는지 대조
# 4. 차수를 보존한 무작위 재배선에서 $Q$ 가 0 근처로 떨어지는지 확인

# %%
import random

import networkx as nx
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

SEED = 42
random.seed(SEED)
np.random.seed(SEED)


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
# ## 1. 손으로 계산하는 모듈러리티
#
# 교과서 식 그대로 옮긴 구현. 항을 따로 뽑아 볼 수 있게 내역도 함께 돌려준다.

# %%
def modularity_terms(G, partition, gamma=1.0):
    """분할별 (l_c, d_c, 관측항, 기대항, 기여분) 내역과 Q 를 돌려준다."""
    m = G.number_of_edges()
    rows, q = [], 0.0
    for c in partition:
        s = set(c)
        l_c = sum(1 for u, v in G.edges() if u in s and v in s)
        d_c = sum(dict(G.degree(s)).values())
        obs = l_c / m
        exp = gamma * (d_c / (2 * m)) ** 2
        q += obs - exp
        rows.append({"nodes": sorted(s), "l_c": l_c, "d_c": d_c,
                     "obs": obs, "exp": exp, "delta": obs - exp})
    return q, rows


def report(name, G, partition, gamma=1.0):
    q, rows = modularity_terms(G, partition, gamma)
    print(f"[{name}]  m={G.number_of_edges()}  Q={q:+.4f}")
    print(f"  {'커뮤니티':<22}{'l_c':>4}{'d_c':>5}{'l_c/m':>9}{'(d_c/2m)^2':>13}{'차':>10}")
    for r in rows:
        label = str(r["nodes"])
        if len(label) > 20:
            label = label[:17] + "..."
        print(f"  {label:<22}{r['l_c']:>4}{r['d_c']:>5}"
              f"{r['obs']:>9.4f}{r['exp']:>13.4f}{r['delta']:>+10.4f}")
    return q


# %% [markdown]
# ## 2. 예제 그래프 — 삼각형 두 개를 다리 하나로 이음
#
# 노드 6개, 엣지 7개. 정답 분할은 삼각형 두 개다.
#
# 삼각형 $\{0,1,2\}$ 를 보면 $l_c = 3$, 차수는 $2,2,3$ 이므로 $d_c = 7$, $m = 7$.
#
# $$\frac{l_c}{m} - \left(\frac{d_c}{2m}\right)^2 = \frac{3}{7} - \left(\frac{7}{14}\right)^2
# = 0.4286 - 0.25 = 0.1786$$
#
# 삼각형이 둘이니 $Q = 2 \times 0.1786 = 0.3571$.

# %%
G = nx.Graph()
G.add_edges_from([(0, 1), (1, 2), (0, 2),      # 삼각형 A
                  (3, 4), (4, 5), (3, 5),      # 삼각형 B
                  (2, 3)])                     # 다리
print("차수:", dict(G.degree()))
# 출력: 차수: {0: 2, 1: 2, 2: 3, 3: 3, 4: 2, 5: 2}

q_true = report("정답 분할 (삼각형 2개)", G, [{0, 1, 2}, {3, 4, 5}])
# 출력: [정답 분할 (삼각형 2개)]  m=7  Q=+0.3571
# 출력:   커뮤니티                   l_c  d_c    l_c/m   (d_c/2m)^2         차
# 출력:   [0, 1, 2]                3    7   0.4286       0.2500   +0.1786
# 출력:   [3, 4, 5]                3    7   0.4286       0.2500   +0.1786

print(f"\n손계산 검산: 2*(3/7 - (7/14)**2) = {2 * (3 / 7 - (7 / 14) ** 2):.4f}")
# 출력: 손계산 검산: 2*(3/7 - (7/14)**2) = 0.3571

# %% [markdown]
# ## 3. 분할을 바꿔 가며 $Q$ 비교
#
# 핵심 관찰 두 가지.
#
# - **전체를 한 덩어리로** 묶으면 $l_c = m$, $d_c = 2m$ 이라 $Q = 1 - 1 = 0$.
#   관측 항만 썼다면 이 답이 만점(=1)이었을 것이다. 기대 항이 그걸 정확히 상쇄한다.
# - **노드마다 하나씩** 쪼개면 $l_c = 0$ 이라 $Q = -\sum_i (d_i/2m)^2 < 0$. 음수.

# %%
partitions = {
    "정답 (삼각형 2개)":   [{0, 1, 2}, {3, 4, 5}],
    "전체 한 덩어리":       [{0, 1, 2, 3, 4, 5}],
    "다리 기준 어긋난 분할": [{0, 1, 2, 3}, {4, 5}],
    "엉뚱하게 섞음":        [{0, 3}, {1, 4}, {2, 5}],
    "노드 하나씩":          [{v} for v in G.nodes()],
}

scores = {}
for name, part in partitions.items():
    scores[name] = report(name, G, part)
    print()
# 출력: [정답 (삼각형 2개)]  m=7  Q=+0.3571
# 출력:   [0, 1, 2]     l_c=3 d_c=7   0.4286 - 0.2500 = +0.1786
# 출력:   [3, 4, 5]     l_c=3 d_c=7   0.4286 - 0.2500 = +0.1786
# 출력:
# 출력: [전체 한 덩어리]  m=7  Q=+0.0000
# 출력:   [0..5]        l_c=7 d_c=14  1.0000 - 1.0000 = +0.0000
# 출력:
# 출력: [다리 기준 어긋난 분할]  m=7  Q=+0.1224
# 출력:   [0, 1, 2, 3]  l_c=4 d_c=10  0.5714 - 0.5102 = +0.0612
# 출력:   [4, 5]        l_c=1 d_c=4   0.1429 - 0.0816 = +0.0612
# 출력:
# 출력: [엉뚱하게 섞음]  m=7  Q=-0.3367
# 출력:   [0, 3]        l_c=0 d_c=5   0.0000 - 0.1276 = -0.1276
# 출력:   [1, 4]        l_c=0 d_c=4   0.0000 - 0.0816 = -0.0816
# 출력:   [2, 5]        l_c=0 d_c=5   0.0000 - 0.1276 = -0.1276
# 출력:
# 출력: [노드 하나씩]  m=7  Q=-0.1735
# 출력:   여섯 개 모두 l_c=0, 기대항 벌점만 남는다 (-0.0204 x4, -0.0459 x2)

print("Q 순위:")
for name, q in sorted(scores.items(), key=lambda kv: -kv[1]):
    print(f"  {q:+.4f}  {name}")
# 출력: Q 순위:
# 출력:   +0.3571  정답 (삼각형 2개)
# 출력:   +0.1224  다리 기준 어긋난 분할
# 출력:   +0.0000  전체 한 덩어리
# 출력:   -0.1735  노드 하나씩
# 출력:   -0.3367  엉뚱하게 섞음

# %% [markdown]
# ## 4. `networkx` 구현과 대조
#
# `nx.community.modularity` 는 Newman–Girvan 행렬형
# $Q = \frac{1}{2m}\sum_{ij}\left[A_{ij}-\frac{d_i d_j}{2m}\right]\delta(c_i,c_j)$
# 를 쓴다. 커뮤니티형과 **같은 식**이므로 값이 일치해야 한다.

# %%
from networkx.algorithms.community import modularity as nx_modularity

print(f"  {'분할':<22}{'직접 계산':>12}{'networkx':>12}{'일치':>7}")
for name, part in partitions.items():
    mine, _ = modularity_terms(G, part)
    theirs = nx_modularity(G, [set(c) for c in part])
    print(f"  {name:<22}{mine:>12.6f}{theirs:>12.6f}{str(abs(mine - theirs) < 1e-12):>7}")
# 출력:   분할                           직접 계산    networkx     일치
# 출력:   정답 (삼각형 2개)               0.357143    0.357143   True
# 출력:   전체 한 덩어리                  0.000000    0.000000   True
# 출력:   다리 기준 어긋난 분할              0.122449    0.122449   True
# 출력:   엉뚱하게 섞음                  -0.336735   -0.336735   True
# 출력:   노드 하나씩                   -0.173469   -0.173469   True

# %% [markdown]
# ## 5. 기대 항의 정체 — 구성 모형을 직접 돌려보기
#
# 기대 항 $(d_c/2m)^2$ 은 "차수는 보존하고 연결만 무작위로 다시 이었을 때
# 커뮤니티 $c$ 안쪽 엣지의 기대 비율"이다. 스텁(반쪽 엣지)을 실제로 섞어서
# 그 주장이 맞는지 몬테카를로로 확인한다.

# %%
def stub_shuffle_internal_ratio(G, community, trials=20000, rng=None):
    """스텁을 무작위로 짝지어 community 내부 엣지 비율의 평균을 낸다."""
    rng = rng or random.Random(SEED)
    stubs = [v for v, d in G.degree() for _ in range(d)]
    inside = set(community)
    m = G.number_of_edges()
    total = 0.0
    for _ in range(trials):
        s = stubs[:]
        rng.shuffle(s)
        cnt = sum(1 for i in range(0, len(s), 2)
                  if s[i] in inside and s[i + 1] in inside)
        total += cnt / m
    return total / trials


comm = {0, 1, 2}
d_c = sum(dict(G.degree(comm)).values())
theory = (d_c / (2 * G.number_of_edges())) ** 2
sim = stub_shuffle_internal_ratio(G, comm, trials=20000)
print(f"이론 (d_c/2m)^2 = {theory:.4f}")
print(f"스텁 섞기 실측   = {sim:.4f}   (20000회)")
# 출력: 이론 (d_c/2m)^2 = 0.2500
# 출력: 스텁 섞기 실측   = 0.2308   (20000회)

print("\n작은 그래프라 자기루프/중복엣지 배제 효과로 약간 낮게 나온다.")
print("관측 l_c/m = %.4f 는 두 값 모두보다 확실히 크다." % (3 / 7))
# 출력: 작은 그래프라 자기루프/중복엣지 배제 효과로 약간 낮게 나온다.
# 출력: 관측 l_c/m = 0.4286 는 두 값 모두보다 확실히 크다.

# %% [markdown]
# ## 6. 큰 그래프에서: 커뮤니티 구조 vs 무작위 재배선
#
# 계획된 분할 모형(planted partition)으로 커뮤니티 4개짜리 그래프를 만들고,
# **차수를 보존한 채** 엣지를 재배선한 그래프와 $Q$ 를 비교한다.
#
# 같은 라벨을 그대로 쓰면 재배선 그래프의 $Q$ 는 0 근처로 떨어져야 한다.
# 최적화까지 돌리면 무작위 그래프에서도 $Q$ 가 0.2~0.3 정도 나온다는 것도 함께 본다
# — "$Q>0$ 이니까 커뮤니티가 있다"고 말하면 안 되는 이유다.

# %%
sizes = [30, 30, 30, 30]
p_in, p_out = 0.35, 0.02
G_big = nx.planted_partition_graph(len(sizes), sizes[0], p_in, p_out, seed=SEED)
truth = [set(range(i * sizes[0], (i + 1) * sizes[0])) for i in range(len(sizes))]

q_planted_truth = nx_modularity(G_big, truth)
q_planted_opt = nx_modularity(
    G_big, nx.community.louvain_communities(G_big, seed=SEED))

rewired = nx.double_edge_swap(
    G_big.copy(), nswap=10 * G_big.number_of_edges(),
    max_tries=200 * G_big.number_of_edges(), seed=SEED)
q_rewired_truth = nx_modularity(rewired, truth)
q_rewired_opt = nx_modularity(
    rewired, nx.community.louvain_communities(rewired, seed=SEED))

print(f"노드 {G_big.number_of_nodes()}, 엣지 {G_big.number_of_edges()}")
print(f"  원본  · 정답 라벨 Q = {q_planted_truth:+.4f}")
print(f"  원본  · 루뱅 최적 Q = {q_planted_opt:+.4f}")
print(f"  재배선 · 정답 라벨 Q = {q_rewired_truth:+.4f}   <- 0 근처로 붕괴")
print(f"  재배선 · 루뱅 최적 Q = {q_rewired_opt:+.4f}   <- 무작위여도 0은 아니다")
# 출력: 노드 120, 엣지 728
# 출력:   원본  · 정답 라벨 Q = +0.5843
# 출력:   원본  · 루뱅 최적 Q = +0.5843
# 출력:   재배선 · 정답 라벨 Q = -0.0132   <- 0 근처로 붕괴
# 출력:   재배선 · 루뱅 최적 Q = +0.2443   <- 무작위여도 0은 아니다

# %% [markdown]
# ### 귀무 분포와 비교하기
#
# 제대로 된 검정은 "재배선을 여러 번 반복해 $Q$ 분포를 만들고 관측 $Q$ 와 비교"다.

# %%
null_qs = []
for i in range(30):
    r = nx.double_edge_swap(
        G_big.copy(), nswap=10 * G_big.number_of_edges(),
        max_tries=200 * G_big.number_of_edges(), seed=SEED + i)
    null_qs.append(nx_modularity(r, truth))

null_qs = np.array(null_qs)
print(f"재배선 30회 · 정답 라벨 Q: 평균 {null_qs.mean():+.4f}, "
      f"표준편차 {null_qs.std():.4f}, 최대 {null_qs.max():+.4f}")
print(f"관측 Q = {q_planted_truth:+.4f}  ->  z = "
      f"{(q_planted_truth - null_qs.mean()) / null_qs.std():.1f}")
# 출력: 재배선 30회 · 정답 라벨 Q: 평균 -0.0041, 표준편차 0.0148, 최대 +0.0253
# 출력: 관측 Q = +0.5843  ->  z = 39.7

# %% [markdown]
# ## 7. 시각화
#
# - 왼쪽 위: 예제 그래프(삼각형 2개 + 다리)
# - 오른쪽 위: 분할별 두 항 분해 — 관측 항(파랑)에서 기대 항(주황)을 뺀 것이 $Q$
# - 왼쪽 아래: 분할별 최종 $Q$
# - 오른쪽 아래: 원본 vs 재배선 그래프의 $Q$ 비교

# %%
pos = nx.spring_layout(G, seed=SEED)
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=("예제 그래프: 삼각형 2개 + 다리",
                    "분할별 두 항 분해 (관측 − 기대)",
                    "분할별 최종 Q",
                    "커뮤니티 구조 vs 차수보존 재배선"),
    specs=[[{"type": "scatter"}, {"type": "bar"}],
           [{"type": "bar"}, {"type": "bar"}]])

# (1) 그래프
ex, ey = [], []
for u, v in G.edges():
    ex += [pos[u][0], pos[v][0], None]
    ey += [pos[u][1], pos[v][1], None]
fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines",
                         line=dict(color="#94a3b8", width=2),
                         hoverinfo="skip", showlegend=False), row=1, col=1)
colors = ["#2563eb"] * 3 + ["#f97316"] * 3
fig.add_trace(go.Scatter(
    x=[pos[v][0] for v in G.nodes()], y=[pos[v][1] for v in G.nodes()],
    mode="markers+text", text=[str(v) for v in G.nodes()],
    textposition="middle center", textfont=dict(color="white", size=13),
    marker=dict(size=30, color=colors, line=dict(color="white", width=2)),
    hovertext=[f"node {v}, deg {G.degree(v)}" for v in G.nodes()],
    hoverinfo="text", showlegend=False), row=1, col=1)
fig.update_xaxes(visible=False, row=1, col=1)
fig.update_yaxes(visible=False, row=1, col=1)

# (2) 두 항 분해
names = list(partitions)
obs_sum = [sum(r["obs"] for r in modularity_terms(G, partitions[n])[1]) for n in names]
exp_sum = [sum(r["exp"] for r in modularity_terms(G, partitions[n])[1]) for n in names]
fig.add_trace(go.Bar(x=names, y=obs_sum, name="관측 Σ l_c/m",
                     marker_color="#2563eb"), row=1, col=2)
fig.add_trace(go.Bar(x=names, y=[-e for e in exp_sum], name="기대 −Σ(d_c/2m)²",
                     marker_color="#f97316"), row=1, col=2)

# (3) 최종 Q
qs = [scores[n] for n in names]
fig.add_trace(go.Bar(x=names, y=qs, name="Q",
                     marker_color=["#16a34a" if q > 0 else "#dc2626" for q in qs],
                     text=[f"{q:+.3f}" for q in qs], textposition="outside",
                     showlegend=False), row=2, col=1)
fig.add_hline(y=0, line=dict(color="#64748b", width=1), row=2, col=1)

# (4) 원본 vs 재배선
big_labels = ["원본<br>정답 라벨", "원본<br>루뱅", "재배선<br>정답 라벨", "재배선<br>루뱅"]
big_vals = [q_planted_truth, q_planted_opt, q_rewired_truth, q_rewired_opt]
fig.add_trace(go.Bar(x=big_labels, y=big_vals,
                     marker_color=["#16a34a", "#16a34a", "#dc2626", "#f97316"],
                     text=[f"{v:+.3f}" for v in big_vals], textposition="outside",
                     showlegend=False), row=2, col=2)
fig.add_hline(y=0, line=dict(color="#64748b", width=1), row=2, col=2)

fig.update_layout(
    title="모듈러리티 Q = Σ [ l_c/m − (d_c/2m)² ]  —  관측에서 기대를 뺀다",
    barmode="relative", height=900, width=1280,
    template="plotly_white", margin=dict(t=150),
    legend=dict(orientation="h", y=1.08, x=0.55))
fig.update_xaxes(tickangle=-20)

_show(fig)
fig.write_image("expy.png", scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# | 항 | 식 | 역할 |
# |---|---|---|
# | 관측 | $l_c/m$ | 실제로 커뮤니티 안에 갇힌 엣지 비율 |
# | 기대 | $(d_c/2m)^2$ | 차수 보존 무작위 재배선에서 기대되는 같은 비율 |
#
# - 기대 항이 **제곱**인 이유: 엣지의 양 끝이 **둘 다** 그 커뮤니티에 떨어져야 하므로
#   확률 $d_c/2m$ 을 두 번 곱한다.
# - 기대 항이 없으면 "전체를 한 덩어리로"가 항상 만점이다. 기대 항이 그 답을 정확히 0점으로 만든다.
# - 재배선 그래프에서 같은 라벨의 $Q$ 는 0으로 붕괴한다 — 기대 항이 제 몫을 한다는 증거.
# - 단, 무작위 그래프에서도 **최적화**를 돌리면 $Q$ 가 0.2~0.3 나온다.
#   $Q$ 값 하나로 "커뮤니티가 있다"고 결론짓지 말고 귀무 분포와 비교할 것.
