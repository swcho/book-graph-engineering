# %% [markdown]
# # 브랜디스 알고리즘의 표본 근사
#
# **질문.** 브랜디스 알고리즘으로 근사 계산을 하는 방법은 무엇인가?
#
# **답.** 모든 노드가 아니라 **표본으로 뽑은 sources 에서만 BFS 를 시작**한다.
# 표본 5% 로도 상위 20개는 대부분 일치한다.
#
# 이 노트북에서 확인할 것:
#
# 1. 전수 브랜디스 = 모든 $s$ 에 대해 BFS. 표본 브랜디스 = 뽑은 $s$ 에 대해서만 BFS
# 2. 표본 비율을 바꿔 가며 **상위 20 일치율**과 **실행 시간** 측정
# 3. $n/k$ 스케일이 왜 필요한가 (불편추정량)
# 4. 구조 있는 그래프 vs 완전 무작위 그래프 — 근사가 잘 듣는 조건
# 5. `nx.betweenness_centrality(k=...)` 의 실제 동작 확인

# %%
import random
import time
from collections import defaultdict, deque

import networkx as nx
import plotly.graph_objects as go
from plotly.subplots import make_subplots

SEED = 11
random.seed(SEED)


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
# ## 1. 그래프 두 개를 준비한다
#
# - **구조 있는 그래프**: 커뮤니티(뭉치) + 다리. 실무 그래프의 모양이다.
#   다리 노드에 매개 중심성이 몰려 있어서 「진짜 급소」가 존재한다.
# - **무작위 그래프**: 같은 간선 수의 Erdős–Rényi (최대 연결 요소만 남겨 노드 1194).
#   매개 중심성이 거의 평평해서 상위 20개라는 게 사실상 무작위다.
#
# 근사의 품질은 **그래프의 구조에 달려 있다**는 걸 보려면 둘 다 필요하다.


# %%
def make_structured(n, avg_deg=6, seed=SEED, groups=60):
    """커뮤니티 + 다리 구조 (10장 ex3_betweenness_cost.py 와 동일).

    groups 를 키우면 다리 노드가 많아져 «상위 20 고르기»가 진짜 순위 문제가 된다.
    """
    rnd = random.Random(seed)
    size = n // groups
    adj = defaultdict(set)
    for g in range(groups):  # 그룹 안은 촘촘하게
        lo, hi = g * size, min((g + 1) * size, n)
        members = list(range(lo, hi))
        for a in members:
            for _ in range(avg_deg // 2):
                b = rnd.choice(members)
                if a != b:
                    adj[a].add(b)
                    adj[b].add(a)
    for g in range(groups - 1):  # 그룹 사이는 다리 하나씩
        a, b = g * size, (g + 1) * size
        if b < n:
            adj[a].add(b)
            adj[b].add(a)
    for v in range(n):
        adj.setdefault(v, set())
    return {k: sorted(v) for k, v in adj.items()}


def make_random(n, m, seed=SEED):
    """같은 규모의 무작위 그래프. 최대 연결 요소만 남긴다."""
    g = nx.gnm_random_graph(n, m, seed=seed)
    g = g.subgraph(max(nx.connected_components(g), key=len)).copy()
    g = nx.convert_node_labels_to_integers(g)
    return {v: sorted(g.neighbors(v)) for v in g.nodes()}


N = 1200
G_STRUCT = make_structured(N)
M = sum(len(v) for v in G_STRUCT.values()) // 2
G_RANDOM = make_random(N, M)

print(f"구조 있는 그래프: 노드 {len(G_STRUCT)}, 간선 {M}")
print(f"무작위 그래프  : 노드 {len(G_RANDOM)}, 간선 {sum(len(v) for v in G_RANDOM.values()) // 2}")
# 출력: 구조 있는 그래프: 노드 1200, 간선 3071
# 출력: 무작위 그래프  : 노드 1194, 간선 3071

# %% [markdown]
# ## 2. 브랜디스 알고리즘 — `sources` 인자 하나가 전부다
#
# 전수 계산은 모든 노드를 한 번씩 시작점 $s$ 로 삼아 BFS 를 돈다.
#
# $$C_B(v) \;=\; \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}
#   \;=\; \sum_{s \neq v} \delta_{s\bullet}(v)$$
#
# 여기서 $\delta_{s\bullet}(v)$ 는 「시작점 $s$ 하나가 $v$ 에 기여한 몫」이고,
# 후방 패스에서 재귀로 계산된다.
#
# $$\delta_{s\bullet}(v) \;=\; \sum_{w:\,v \in \mathrm{pred}(w)}
#   \frac{\sigma_v}{\sigma_w}\bigl(1 + \delta_{s\bullet}(w)\bigr)$$
#
# **바깥 루프가 $s$ 에 대한 합**이라는 게 핵심이다.
# 합을 표본 평균으로 바꾸면 그대로 근사가 된다 — 알고리즘 내부는 한 줄도 안 바뀐다.


# %%
def brandes(adj, sources=None, scale=False):
    """브랜디스 알고리즘.

    sources 를 주면 그 노드에서만 BFS 를 시작한다(근사).
    scale=True 면 n/k 로 스케일해 «전수 계산과 같은 눈금»으로 만든다.
    """
    cb = {v: 0.0 for v in adj}
    src = list(adj) if sources is None else list(sources)
    for s in src:
        # --- 전방 패스: BFS 로 거리 dist 와 최단 경로 개수 sigma 를 센다 ---
        stack, pred = [], {v: [] for v in adj}
        sigma = {v: 0 for v in adj}
        sigma[s] = 1
        dist = {v: -1 for v in adj}
        dist[s] = 0
        q = deque([s])
        while q:
            v = q.popleft()
            stack.append(v)
            for w in adj[v]:
                if dist[w] < 0:
                    dist[w] = dist[v] + 1
                    q.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)
        # --- 후방 패스: 먼 노드부터 거꾸로 의존도를 누적한다 ---
        delta = {v: 0.0 for v in adj}
        while stack:
            w = stack.pop()
            for v in pred[w]:
                delta[v] += sigma[v] / sigma[w] * (1 + delta[w])
            if w != s:
                cb[w] += delta[w]
    if scale:
        f = len(adj) / len(src)  # ← 불편추정량으로 만드는 n/k 스케일
        cb = {v: c * f for v, c in cb.items()}
    return cb


def sample_sources(adj, frac, seed=3):
    """시작점을 무작위로 뽑는다. 시드를 고정하지 않으면 매번 순위가 흔들린다."""
    k = max(1, round(len(adj) * frac))
    return random.Random(seed).sample(sorted(adj), k)


def top_overlap(a, b, k=20):
    ta = {v for v, _ in sorted(a.items(), key=lambda x: -x[1])[:k]}
    tb = {v for v, _ in sorted(b.items(), key=lambda x: -x[1])[:k]}
    return len(ta & tb) / k


# %% [markdown]
# ## 3. 표본 비율을 바꿔 가며 재 본다
#
# 시작점을 $k$ 개만 뽑으면 BFS 를 $k$ 번만 돈다.
# 브랜디스의 비용이 $O(VE)$ = (시작점 수) × (BFS 비용) 이므로
# **실행 시간은 표본 비율에 정확히 비례**한다.
#
# 반면 상위 20 일치율은 비율에 비례하지 않는다. 훨씬 빨리 포화한다.

# %%
FRACS = [0.01, 0.02, 0.05, 0.10, 0.20, 0.50, 1.00]
REPEATS = 3  # 표본 시드를 바꿔 가며 평균낸다 (한 번만 재면 운에 좌우된다)
results = {}

for name, adj in (("구조 있음", G_STRUCT), ("무작위", G_RANDOM)):
    t0 = time.perf_counter()
    exact = brandes(adj)
    t_exact = time.perf_counter() - t0
    rows = []
    for f in FRACS:
        ovs, dts, k = [], [], 0
        for r in range(1 if f >= 1.0 else REPEATS):
            src = sample_sources(adj, f, seed=3 + r)
            k = len(src)
            t0 = time.perf_counter()
            approx = brandes(adj, src, scale=True)
            dts.append(time.perf_counter() - t0)
            ovs.append(top_overlap(exact, approx))
        rows.append((f, k, sum(dts) / len(dts), sum(ovs) / len(ovs)))
    results[name] = {"exact": exact, "t_exact": t_exact, "rows": rows}
    print(f"\n[{name}]  전수 계산 {t_exact:.2f}s  (노드 {len(adj)})")
    print(f"{'표본비율':>8} {'k':>6} {'시간(s)':>9} {'배속':>7} {'상위20 일치':>11}")
    print("-" * 46)
    for f, k, dt, ov in rows:
        print(f"{f * 100:>7.0f}% {k:>6} {dt:>9.2f} {t_exact / dt:>6.1f}x {ov * 100:>10.0f}%")

# 출력: (시간·배속은 기계마다 다르다. 일치율과 k 는 시드 고정이라 재현된다)
# 출력:
# 출력: [구조 있음]  전수 계산 1.94s  (노드 1200)
# 출력:     표본비율      k     시간(s)      배속     상위20 일치
# 출력: ----------------------------------------------
# 출력:       1%     12      0.02  110.1x         87%
# 출력:       2%     24      0.04   52.5x         88%
# 출력:       5%     60      0.09   20.9x         92%
# 출력:      10%    120      0.18   10.5x         93%
# 출력:      20%    240      0.43    4.6x         98%
# 출력:      50%    600      0.94    2.1x        100%
# 출력:     100%   1200      1.88    1.0x        100%
# 출력:
# 출력: [무작위]  전수 계산 1.87s  (노드 1194)
# 출력:     표본비율      k     시간(s)      배속     상위20 일치
# 출력: ----------------------------------------------
# 출력:       1%     12      0.02  102.6x         18%
# 출력:       2%     24      0.04   50.6x         23%
# 출력:       5%     60      0.09   20.4x         37%
# 출력:      10%    119      0.19   10.1x         55%
# 출력:      20%    239      0.38    5.0x         68%
# 출력:      50%    597      0.94    2.0x         85%
# 출력:     100%   1194      1.91    1.0x        100%

# %% [markdown]
# 표본 5% 에서 **구조 있는 그래프는 92%**, **무작위 그래프는 37%**.
# 같은 알고리즘, 같은 표본인데 결과가 갈린다.
#
# 이유는 간단하다. 무작위 그래프에서는 매개 중심성이 거의 평평해서
# 1등과 100등의 차이가 표본 잡음보다 작다. 「상위 20개」라는 순위 자체가 무의미하다.
# 근사가 잘 듣는 건 **진짜 급소가 있는 그래프**에서다 (그리고 실무 그래프는 대개 그렇다).

# %% [markdown]
# ## 4. 왜 $n/k$ 로 스케일하는가 — 불편추정량
#
# 시작점 $s$ 를 균등하게 하나 뽑았을 때 그 기여의 기댓값은
#
# $$\mathbb{E}_s\bigl[\delta_{s\bullet}(v)\bigr]
#   \;=\; \frac{1}{n}\sum_{s} \delta_{s\bullet}(v)
#   \;=\; \frac{C_B(v)}{n}$$
#
# 이므로, $k$ 개 표본의 합에 $n/k$ 를 곱하면
#
# $$\hat{C}_B(v) \;=\; \frac{n}{k}\sum_{s \in S} \delta_{s\bullet}(v),
# \qquad \mathbb{E}\bigl[\hat{C}_B(v)\bigr] = C_B(v)$$
#
# 즉 **불편추정량(unbiased estimator)** 이 된다. 편향은 0이고 남는 건 분산뿐이다.
# 분산은 대략 $\mathrm{Var}(\hat{C}_B) = \frac{n^2}{k}\mathrm{Var}_s(\delta_{s\bullet})$ 로
# $k$ 에 반비례해 줄어든다 ⇒ 표준오차는 $1/\sqrt{k}$ 로 줄어든다.
#
# 스케일을 빼먹으면 값이 $k/n$ 배로 쪼그라든다.
# **순위만 볼 거면 상관없지만** 절대 임계값(예: 「0.01 이상만 경보」)을 쓰고 있으면
# 그 임계가 조용히 의미를 잃는다.

# %%
exact_s = results["구조 있음"]["exact"]
hot = max(exact_s, key=exact_s.get)  # 매개 중심성 1등 노드
src5 = sample_sources(G_STRUCT, 0.05)

raw = brandes(G_STRUCT, src5, scale=False)
scaled = brandes(G_STRUCT, src5, scale=True)

print(f"1등 노드 = {hot}")
print(f"  전수 계산      : {exact_s[hot]:>12.1f}")
print(f"  표본 5% (스케일X): {raw[hot]:>12.1f}   ← 전수의 {raw[hot] / exact_s[hot]:.3f}배 (≈ k/n = 0.05)")
print(f"  표본 5% (n/k 곱): {scaled[hot]:>12.1f}   ← 전수의 {scaled[hot] / exact_s[hot]:.3f}배")
# 출력: 1등 노드 = 580
# 출력:   전수 계산      :     740890.7
# 출력:   표본 5% (스케일X):      36460.0   ← 전수의 0.049배 (≈ k/n = 0.05)
# 출력:   표본 5% (n/k 곱):     729200.0   ← 전수의 0.984배

# %% [markdown]
# ### 편향이 정말 0인지 — 시드를 바꿔 가며 여러 번
#
# 표본을 여러 번 다시 뽑아 추정치의 **평균**이 참값에 붙는지,
# 그리고 **퍼짐**이 $k$ 가 커질수록 좁아지는지 확인한다.

# %%
TRIALS = 20
unbiased = {}
for f in (0.02, 0.05, 0.10):
    ests = [brandes(G_STRUCT, sample_sources(G_STRUCT, f, seed=100 + t), scale=True)[hot] for t in range(TRIALS)]
    mean = sum(ests) / len(ests)
    var = sum((e - mean) ** 2 for e in ests) / (len(ests) - 1)
    sd = var**0.5
    unbiased[f] = ests
    print(
        f"k={round(len(G_STRUCT) * f):>4} ({f * 100:>3.0f}%)  "
        f"평균 {mean:>10.1f}  편향 {(mean / exact_s[hot] - 1) * 100:>+6.2f}%  "
        f"표준편차 {sd / mean * 100:>5.2f}%"
    )
print(f"참값                     {exact_s[hot]:>10.1f}")
# 출력: k=  24 (  2%)  평균   738532.2  편향  -0.32%  표준편차  1.86%
# 출력: k=  60 (  5%)  평균   738585.9  편향  -0.31%  표준편차  1.06%
# 출력: k= 120 ( 10%)  평균   740481.1  편향  -0.06%  표준편차  1.09%
# 출력: 참값                       740890.7

# %% [markdown]
# 평균은 참값 근처(편향 0.35% 이내)에서 흔들린다. **편향은 사실상 0**이다.
# 표준편차는 $k$ 가 커질수록 줄어든다: $1.86\% \to 1.06\% \to 1.09\%$.
# $k{=}24 \to 60$ (2.5배) 구간은 이론값 $1/\sqrt{2.5}\approx 1.58$ 배 감소($1.86\to1.18$ 예측)와 잘 맞는다.
# $k{=}120$ 에서 다시 오른 건 **20회 반복으로 추정한 표준편차 자체의 잡음**이다
# (표준편차의 상대오차가 $1/\sqrt{2(T-1)} \approx 16\%$ 나 된다). 추세는 $1/\sqrt{k}$ 다.
#
# > 주의: 이 노트북은 **비복원 추출**(`random.sample`)을 쓴다.
# > 균등 확률이므로 여전히 불편추정량이지만, 분산에는 유한모집단 보정
# > $\frac{n-k}{n-1}$ 이 붙어 복원 추출보다 조금 더 정확하다.

# %% [markdown]
# ## 5. 근사가 어디서 틀리는가 — 상위권 vs 하위권
#
# 표본 근사의 오차는 **값에 비례하지 않는다**.
# 매개 중심성이 큰 노드는 어느 시작점에서 보든 길목이라 표본이 작아도 잡힌다.
# 반면 값이 작은 노드는 「운 좋게 뽑힌 시작점 하나」에 좌우돼 상대오차가 크다.

# %%
pairs = sorted(((exact_s[v], scaled[v]) for v in G_STRUCT), key=lambda p: -p[0])
top20 = pairs[:20]
bottom = [p for p in pairs if p[0] > 0][-200:]


def rel_err(ps):
    return sum(abs(a - e) / e for e, a in ps) / len(ps) * 100


print(f"상위 20개 평균 상대오차 : {rel_err(top20):>6.1f}%")
print(f"하위 200개 평균 상대오차: {rel_err(bottom):>6.1f}%")
print(f"값이 0으로 추정된 노드 수: {sum(1 for e, a in pairs if a == 0 and e > 0)} / {len(pairs)}")
# 출력: 상위 20개 평균 상대오차 :    3.0%
# 출력: 하위 200개 평균 상대오차:  139.0%
# 출력: 값이 0으로 추정된 노드 수: 265 / 1200

# %% [markdown]
# 상위 20개는 3% 오차인데 하위 200개는 139% 다. 그리고 **1200개 중 265개가 0으로 추정**됐다.
# 참값이 0 이 아닌데도 뽑힌 시작점 60개 중 어느 것도 그 노드를 지나가지 않은 것이다.
# 불편추정량이라도 「한 표본에서의 값」은 이렇게 통째로 사라질 수 있다.
#
# **값 자체를 보고할 거면 전수 계산을 써야 한다.**
# 근사는 「누가 위에 있나」에만 답한다. 다행히 실무에서 필요한 건 대개 그것뿐이다.

# %% [markdown]
# ## 6. `nx.betweenness_centrality(k=...)` 는 정확히 이 일을 한다
#
# networkx 구현(`networkx/algorithms/centrality/betweenness.py`)의 핵심 두 줄:
#
# ```python
# nodes = seed.sample(list(G.nodes()), k)      # ← 시작점 k 개를 비복원 추출
# ...
# if k is not None:
#     scale = scale * n / k                    # ← _rescale() 안의 n/k 보정
# ```
#
# 즉 (1) 시작점만 표본으로 뽑고 (2) $n/k$ 로 되돌린다. 우리가 위에서 손으로 한 것과 같다.
# `seed` 를 주지 않으면 호출할 때마다 순위가 흔들리므로 **반드시 고정**한다.

# %%
gx = nx.Graph()
for v, nbrs in G_STRUCT.items():
    gx.add_node(v)
    for w in nbrs:
        gx.add_edge(v, w)

nx_exact = nx.betweenness_centrality(gx, normalized=False)
nx_k60 = nx.betweenness_centrality(gx, k=60, seed=3, normalized=False)

# 우리 구현의 정규화 전 값과 비교 (무방향이라 networkx 는 0.5 를 곱한다)
print(f"nx 전수 1등          : {max(nx_exact.values()):>12.1f}")
print(f"우리 전수 1등 × 0.5  : {exact_s[hot] * 0.5:>12.1f}")
print(f"nx k=60 (n/k 자동보정): {max(nx_k60.values()):>12.1f}")
print(f"상위 20 일치 (nx 전수 vs nx k=60): {top_overlap(nx_exact, nx_k60) * 100:.0f}%")
# 출력: nx 전수 1등          :     370445.4
# 출력: 우리 전수 1등 × 0.5  :     370445.4
# 출력: nx k=60 (n/k 자동보정):     374612.0
# 출력: 상위 20 일치 (nx 전수 vs nx k=60): 90%

# %% [markdown]
# ### 함정 하나 — 유방향 + `normalized=False` 면 $n/k$ 보정이 통째로 빠진다
#
# `_rescale()` 은 `scale` 이 `None` 이면 아무것도 곱하지 않고 빠져나간다.
# 그런데 유방향 그래프에 `normalized=False` 를 주면 `scale = None` 이 된다.
# 결과적으로 **`k` 를 줘도 $n/k$ 보정이 적용되지 않아** 값이 $k/n$ 배로 나온다.
# 순위는 멀쩡하니 눈치채기 어렵다.

# %%
dg = nx.gnm_random_graph(300, 1200, seed=7, directed=True)
d_exact = nx.betweenness_centrality(dg, normalized=False)
d_k30 = nx.betweenness_centrality(dg, k=30, seed=1, normalized=False)
d_k30n = nx.betweenness_centrality(dg, k=30, seed=1, normalized=True)

s = sum(d_exact.values())
print(f"유방향, normalized=False  전수 합계  : {s:>10.1f}")
print(f"유방향, normalized=False  k=30 합계  : {sum(d_k30.values()):>10.1f}  ← 약 k/n=0.1 배")
print(f"                                비율 : {sum(d_k30.values()) / s:>10.3f}")
print(f"유방향, normalized=True   k=30/전수  : {sum(d_k30n.values()) / sum(nx.betweenness_centrality(dg).values()):>10.3f}  ← 정상")
# 출력: 유방향, normalized=False  전수 합계  :   272827.0
# 출력: 유방향, normalized=False  k=30 합계  :    26478.0  ← 약 k/n=0.1 배
# 출력:                                 비율 :      0.097
# 출력: 유방향, normalized=True   k=30/전수  :      0.971  ← 정상

# %% [markdown]
# ## 7. 그림으로
#
# - 왼쪽 위: 표본 비율 vs 상위 20 일치율. 구조 있는 그래프는 5% 에서 이미 90% 를 넘는다
# - 오른쪽 위: 표본 비율 vs 실행 시간. 정확히 선형이다 (BFS 를 $k$ 번 도니까)
# - 왼쪽 아래: $n/k$ 스케일 추정치의 퍼짐. $k$ 가 커질수록 참값으로 좁아진다
# - 오른쪽 아래: 전수 vs 표본 5% 산점도. 상위권은 대각선에 붙고 하위권만 흩어진다

# %%
C_STRUCT, C_RANDOM, C_EXACT, C_GRID = "#2563eb", "#dc2626", "#111827", "#d1d5db"

fig = make_subplots(
    rows=2,
    cols=2,
    subplot_titles=(
        "상위 20 일치율 — 5% 면 충분한가",
        "실행 시간 — 표본 비율에 정비례",
        f"n/k 스케일 추정치의 퍼짐 (노드 {hot}, {TRIALS}회 반복)",
        "전수 vs 표본 5% — 상위권만 맞는다",
    ),
    vertical_spacing=0.14,
    horizontal_spacing=0.10,
)

# (1) 일치율
for name, color in (("구조 있음", C_STRUCT), ("무작위", C_RANDOM)):
    rows = results[name]["rows"]
    fig.add_trace(
        go.Scatter(
            x=[f * 100 for f, _, _, _ in rows],
            y=[ov * 100 for _, _, _, ov in rows],
            mode="lines+markers",
            name=name,
            line=dict(color=color, width=2.5),
            marker=dict(size=8),
            legendgroup=name,
        ),
        row=1,
        col=1,
    )
fig.add_vline(x=5, line=dict(color="#9ca3af", dash="dot"), row=1, col=1)
fig.add_annotation(x=5, y=18, text="표본 5%", showarrow=False, xanchor="left", font=dict(size=11, color="#6b7280"), row=1, col=1)

# (2) 실행 시간
rows = results["구조 있음"]["rows"]
fig.add_trace(
    go.Scatter(
        x=[f * 100 for f, _, _, _ in rows],
        y=[dt for _, _, dt, _ in rows],
        mode="lines+markers",
        name="표본 브랜디스",
        line=dict(color=C_STRUCT, width=2.5),
        marker=dict(size=8),
        showlegend=False,
    ),
    row=1,
    col=2,
)
fig.add_hline(
    y=results["구조 있음"]["t_exact"],
    line=dict(color=C_EXACT, dash="dash"),
    annotation_text="전수 계산",
    annotation_position="bottom left",
    annotation_font=dict(size=11),
    row=1,
    col=2,
)

# (3) 불편성
for f, ests in unbiased.items():
    k = round(len(G_STRUCT) * f)
    fig.add_trace(
        go.Box(
            y=ests,
            name=f"k={k}<br>({f * 100:.0f}%)",
            marker_color=C_STRUCT,
            boxpoints="all",
            jitter=0.5,
            pointpos=0,
            marker=dict(size=4, opacity=0.5),
            showlegend=False,
        ),
        row=2,
        col=1,
    )
fig.add_hline(
    y=exact_s[hot],
    line=dict(color=C_EXACT, dash="dash"),
    annotation_text="참값",
    annotation_position="top left",
    annotation_font=dict(size=11),
    row=2,
    col=1,
)

# (4) 산점도
rest = pairs[20:]
fig.add_trace(
    go.Scatter(
        x=[e for e, _ in rest],
        y=[max(a, 1.0) for _, a in rest],
        mode="markers",
        name="나머지",
        marker=dict(size=4, color="#9ca3af", opacity=0.5),
        showlegend=False,
    ),
    row=2,
    col=2,
)
fig.add_trace(
    go.Scatter(
        x=[e for e, _ in top20],
        y=[a for _, a in top20],
        mode="markers",
        name="상위 20",
        marker=dict(size=9, color=C_STRUCT, line=dict(width=1, color="white")),
        showlegend=False,
    ),
    row=2,
    col=2,
)
lo = min(e for e, _ in pairs if e > 0)
hi = max(e for e, _ in pairs)
fig.add_trace(
    go.Scatter(
        x=[lo, hi],
        y=[lo, hi],
        mode="lines",
        line=dict(color=C_EXACT, dash="dash", width=1.5),
        showlegend=False,
    ),
    row=2,
    col=2,
)

fig.update_xaxes(title_text="표본 비율 (%)", type="log", row=1, col=1)
fig.update_yaxes(title_text="상위 20 일치율 (%)", range=[0, 105], row=1, col=1)
fig.update_xaxes(title_text="표본 비율 (%)", row=1, col=2)
fig.update_yaxes(title_text="실행 시간 (초)", row=1, col=2)
fig.update_yaxes(title_text="추정 매개 중심성", row=2, col=1)
fig.update_xaxes(title_text="전수 계산 값 (log)", type="log", row=2, col=2)
fig.update_yaxes(title_text="표본 5% 추정 (log)", type="log", row=2, col=2)

fig.update_layout(
    title=dict(text="브랜디스 표본 근사 — 5% 로 상위권을 맞힌다", font=dict(size=20)),
    height=820,
    width=1150,
    template="plotly_white",
    font=dict(size=13),
    legend=dict(orientation="h", y=1.06, x=0.0),
    margin=dict(t=120, b=60, l=70, r=40),
)
fig.update_xaxes(gridcolor=C_GRID)
fig.update_yaxes(gridcolor=C_GRID)

_show(fig)

# %%
import os

try:
    _here = os.path.dirname(os.path.abspath(__file__))
except NameError:  # 주피터에서는 __file__ 이 없다
    _here = os.getcwd()
OUT = os.path.join(_here, "expy.png")
fig.write_image(OUT, scale=2)
print("저장:", OUT, os.path.getsize(OUT), "bytes")
# 출력: 저장: .../expy.png 358207 bytes   (바이트 수는 렌더러 버전에 따라 조금 달라진다)

# %% [markdown]
# ## 정리
#
# | 항목 | 내용 |
# |---|---|
# | 방법 | 브랜디스의 **바깥 루프(시작점 $s$)만 표본으로** 줄인다. 내부 BFS/후방 패스는 그대로 |
# | 비용 | $O(VE) \to O(kE)$. 시간은 표본 비율에 **정비례** |
# | 보정 | $\hat{C}_B = \frac{n}{k}\sum_{s\in S}\delta_{s\bullet}$ ⇒ **불편추정량** |
# | 오차 | 표준오차 $\propto 1/\sqrt{k}$. 상위권은 정확, 하위권은 크게 틀림 |
# | 조건 | 구조(커뮤니티+다리) 있는 그래프에서 5% ≈ 92% 일치. 무작위 그래프는 37% |
# | 필수 | **시드 고정.** 안 하면 실행할 때마다 순위가 바뀐다 |
#
# 후속 연구는 「어떤 시작점을 뽑을까」와 「몇 개면 충분한가」를 파고들었다.
#
# - **Brandes & Pich (2007)** — 시작점(pivot) 선택 전략 비교. 결론은 균등 무작위가 견고
# - **Geisberger, Sanders, Schultes (2008)** — 시작점 근처 노드가 과대평가되는 편향을 선형 스케일로 보정
# - **Riondato & Kornaropoulos (2016)** — 노드가 아니라 **최단 경로 자체**를 표본으로. VC 차원으로
#   $\varepsilon$-근사에 필요한 표본 수를 그래프 크기와 **무관하게** 정한다
# - **Borassi & Natale (2019) KADABRA** — 양방향 BFS + 적응적 표본으로 더 빠르게
