# %% [markdown]
# # 라벨 전파(Label Propagation)의 장단점 실험
#
# 카드 질문: **라벨 전파의 장단점은 무엇인가?**
#
# 답: **빠르지만 시드에 따라 결과가 달라진다.** 같은 데이터로 어제와 오늘 다른
# 커뮤니티가 나오면 보고서를 쓸 수 없다.
#
# 이 스크립트는 그 문장을 숫자로 확인한다.
#
# 1. **장점 — 싸다.** 한 라운드가 $O(m)$, 라운드 수가 거의 상수라 사실상 준선형이다.
# 2. **단점 — 비결정적이다.** 원인이 둘이다.
#    - (a) 노드 **방문 순서**를 라운드마다 섞는다
#    - (b) 이웃 라벨이 **동점**일 때 하나를 무작위로 고른다
# 3. **단점 — 수렴 보장이 없다.** 동기(synchronous) 갱신은 이분 구조에서 영원히 진동한다.
# 4. **완화책 — 준동기(semi-synchronous) 변형.** 그래프 색칠로 진동을 없앤다.
#
# 흔들림의 크기는 NMI(정규화 상호정보량)와 ARI(조정 랜드 지수)로 잰다.

# %%
import random
import time
from collections import Counter, defaultdict

import networkx as nx
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


print("networkx", nx.__version__, "| numpy", np.__version__)
# 출력: networkx 3.2.1 | numpy 2.0.2

# %% [markdown]
# ## 1. 실험용 그래프 — 정답을 아는 커뮤니티 구조
#
# `planted_partition_graph`로 **정답 분할이 알려진** 그래프를 만든다.
# 그룹 6개 × 25명 = 150 노드. 그룹 안 연결 확률 $p_{in}$, 그룹 밖 $p_{out}$.
#
# $p_{out}$을 조금 키우면 커뮤니티 경계가 흐려지고, 라벨 전파의 흔들림이 커진다.
# 여기서는 "경계가 애매하지만 사람 눈에는 보이는" 정도로 잡는다.

# %%
N_GROUPS, GROUP_SIZE = 6, 25
P_IN, P_OUT = 0.30, 0.025

G = nx.planted_partition_graph(N_GROUPS, GROUP_SIZE, P_IN, P_OUT, seed=42)
NODES = sorted(G.nodes())
ADJ = {v: sorted(G.neighbors(v)) for v in NODES}
GROUND_TRUTH = np.array([v // GROUP_SIZE for v in NODES])  # 정답 라벨

print(f"노드 {G.number_of_nodes()}개, 간선 {G.number_of_edges()}개")
print(f"평균 차수 {2 * G.number_of_edges() / G.number_of_nodes():.2f}")
print(f"정답 커뮤니티 {N_GROUPS}개, 각 {GROUP_SIZE}명")
# 출력: 노드 150개, 간선 802개
# 출력: 평균 차수 10.69
# 출력: 정답 커뮤니티 6개, 각 25명

# %% [markdown]
# ## 2. 라벨 전파 구현 (Raghavan et al., 2007)
#
# 절차는 놀랄 만큼 단순하다.
#
# 1. 모든 노드에 서로 다른 라벨을 준다: $L_0(v) = v$
# 2. 노드를 **무작위 순서**로 돌면서, 이웃에서 가장 많은 라벨로 바꾼다
#    $$L(v) \leftarrow \arg\max_{\ell} \; \bigl|\{u \in N(v) : L(u) = \ell\}\bigr|$$
# 3. 최댓값이 여럿이면 그중 **하나를 무작위로** 고른다
# 4. 모든 노드가 이미 이웃 최다 라벨을 갖고 있으면 멈춘다
#
# 비용: 한 라운드에서 각 노드가 자기 이웃을 한 번씩 훑으므로
# $\sum_v \deg(v) = 2m$, 즉 **라운드당 $O(m)$**이다. 라운드 수는 실측상 5회 안팎에서
# 대부분 정리되므로 전체가 사실상 $O(m)$ 준선형이다. 모듈러리티 최적화가
# 그리디 병합에서 $O(n^2 \log n)$까지 가는 것과 대비된다.
#
# 무작위성이 들어가는 자리를 **두 개의 스위치**로 분리해 두었다.
# `shuffle_order`(방문 순서), `random_tie`(동점 처리).

# %%
def label_propagation(adj, seed=0, rounds=100, shuffle_order=True, random_tie=True):
    """비동기 라벨 전파. 무작위성 두 원인을 스위치로 분리.

    returns: (labels_array, n_rounds, n_updates_per_round)
    """
    rnd = random.Random(seed)
    nodes = sorted(adj)
    label = {v: i for i, v in enumerate(nodes)}
    order = list(nodes)
    history = []

    for r in range(rounds):
        if shuffle_order:
            rnd.shuffle(order)
        changed = 0
        for v in order:
            if not adj[v]:
                continue
            cnt = Counter(label[u] for u in adj[v])
            top = max(cnt.values())
            best = [l for l, c in cnt.items() if c == top]
            if random_tie:
                pick = rnd.choice(best)  # 동점 → 무작위
            elif label[v] in best:
                pick = label[v]  # 동점 → 자기 라벨 유지 (결정적)
            else:
                pick = min(best)  # 그마저 없으면 가장 작은 라벨
            if label[v] != pick:
                label[v] = pick
                changed += 1
        history.append(changed)
        if changed == 0:
            break
    return np.array([label[v] for v in nodes]), r + 1, history


def n_comms(labels):
    return len(set(labels.tolist()))


def to_communities(labels, nodes):
    g = defaultdict(list)
    for v, l in zip(nodes, labels.tolist()):
        g[l].append(v)
    return list(g.values())


lab0, rounds0, hist0 = label_propagation(ADJ, seed=0)
print(f"seed=0: 커뮤니티 {n_comms(lab0)}개, 라운드 {rounds0}회, 라운드별 변경 수 {hist0}")
# 출력: seed=0: 커뮤니티 6개, 라운드 9회, 라운드별 변경 수 [135, 62, 33, 17, 9, 7, 2, 2, 0]

# %% [markdown]
# ## 3. 장점 확인 — 비용은 $O(m)$
#
# 그래프 크기를 키우며 실행 시간을 잰다. 간선 수에 거의 **선형**으로 붙는지 본다.

# %%
cost_rows = []
for n_grp in [4, 10, 20, 40, 70, 100]:
    g_size = 60
    p_out = 2.0 / (g_size * (n_grp - 1))  # 평균 차수를 14 근처로 고정
    g = nx.planted_partition_graph(n_grp, g_size, 0.20, p_out, seed=7)
    adj = {v: sorted(g.neighbors(v)) for v in g.nodes()}
    t0 = time.perf_counter()
    _, rr, _ = label_propagation(adj, seed=0)
    dt = time.perf_counter() - t0
    m = g.number_of_edges()
    cost_rows.append((g.number_of_nodes(), m, rr, dt))
    print(f"n={g.number_of_nodes():5d}  m={m:7d}  라운드={rr:2d}  전체 {dt * 1000:7.1f} ms  "
          f"라운드당 {dt / rr / m * 1e6:.3f} µs/간선")
# 출력: n=  240  m=   1681  라운드= 4  전체     2.7 ms  라운드당 0.407 µs/간선
# 출력: n=  600  m=   4052  라운드= 5  전체     8.4 ms  라운드당 0.417 µs/간선
# 출력: n= 1200  m=   8258  라운드= 8  전체    27.0 ms  라운드당 0.409 µs/간선
# 출력: n= 2400  m=  16507  라운드=10  전체    69.1 ms  라운드당 0.418 µs/간선
# 출력: n= 4200  m=  29016  라운드= 6  전체    75.6 ms  라운드당 0.434 µs/간선
# 출력: n= 6000  m=  41571  라운드=16  전체   291.3 ms  라운드당 0.438 µs/간선

# %% [markdown]
# 노드가 25배 늘어도 **라운드당 간선 하나에 드는 시간은 0.41 µs로 거의 상수**다.
# 라운드 수는 4~16 사이에서 왔다 갔다 할 뿐 $n$에 비례해 늘지 않는다.
# 이것이 라벨 전파를 쓰는 **유일하고 강력한 이유**다: 억 단위 간선에서도 돈다.
#
# ## 4. 흔들림을 재는 자 — NMI와 ARI
#
# 두 분할 $X, Y$를 비교한다. 분할 결과에서 라벨 **이름**은 의미가 없으므로,
# 이름에 무관한 지표를 써야 한다.
#
# **NMI** (정규화 상호정보량, 산술평균 정규화):
# $$\mathrm{NMI}(X,Y) = \frac{2\,I(X;Y)}{H(X) + H(Y)}, \qquad
# I(X;Y) = \sum_{i,j} \frac{n_{ij}}{n} \log \frac{n\,n_{ij}}{a_i b_j}$$
#
# **ARI** (조정 랜드 지수, 우연 일치를 기댓값으로 빼 준다):
# $$\mathrm{ARI} = \frac{\sum_{ij}\binom{n_{ij}}{2} - \frac{\sum_i \binom{a_i}{2}\sum_j \binom{b_j}{2}}{\binom{n}{2}}}
# {\frac{1}{2}\left[\sum_i \binom{a_i}{2} + \sum_j \binom{b_j}{2}\right] - \frac{\sum_i \binom{a_i}{2}\sum_j \binom{b_j}{2}}{\binom{n}{2}}}$$
#
# 둘 다 1이면 완전히 같은 분할, 0이면 우연 수준이다.
# ARI가 더 엄격하다 — NMI는 "잘게 쪼갠 분할"에 후한 편이다.

# %%
def contingency(x, y):
    xs, ys = sorted(set(x.tolist())), sorted(set(y.tolist()))
    xi = {v: i for i, v in enumerate(xs)}
    yi = {v: i for i, v in enumerate(ys)}
    c = np.zeros((len(xs), len(ys)))
    for a, b in zip(x.tolist(), y.tolist()):
        c[xi[a], yi[b]] += 1
    return c


def nmi(x, y):
    c = contingency(x, y)
    n = c.sum()
    a, b = c.sum(axis=1), c.sum(axis=0)
    hx = -np.sum((a / n) * np.log(a / n + 1e-300))
    hy = -np.sum((b / n) * np.log(b / n + 1e-300))
    nz = c > 0
    mi = np.sum((c[nz] / n) * np.log(n * c[nz] / np.outer(a, b)[nz]))
    if hx + hy == 0:
        return 1.0
    return float(2 * mi / (hx + hy))


def ari(x, y):
    c = contingency(x, y)
    n = c.sum()
    comb2 = lambda v: v * (v - 1) / 2  # noqa: E731
    sij = comb2(c).sum()
    sa = comb2(c.sum(axis=1)).sum()
    sb = comb2(c.sum(axis=0)).sum()
    exp = sa * sb / comb2(n)
    mx = (sa + sb) / 2
    if mx == exp:
        return 1.0
    return float((sij - exp) / (mx - exp))


# 감각 잡기: 정답과 자기 자신, 정답과 무작위
rng = np.random.default_rng(0)
shuffled = rng.permutation(GROUND_TRUTH)
print(f"정답 vs 정답      NMI={nmi(GROUND_TRUTH, GROUND_TRUTH):.3f}  ARI={ari(GROUND_TRUTH, GROUND_TRUTH):.3f}")
print(f"정답 vs 무작위     NMI={nmi(GROUND_TRUTH, shuffled):.3f}  ARI={ari(GROUND_TRUTH, shuffled):.3f}")
# 출력: 정답 vs 정답      NMI=1.000  ARI=1.000
# 출력: 정답 vs 무작위     NMI=0.067  ARI=0.015

# %% [markdown]
# ## 5. 단점 확인 — 시드만 바꿔 30번 돌린다
#
# 그래프도, 코드도, 파라미터도 전부 동일하다. **난수 시드만** 바뀐다.
# "어제와 오늘"이 바로 이것이다.

# %%
SEEDS = list(range(30))
runs = {}
for s in SEEDS:
    lab, rr, _ = label_propagation(ADJ, seed=s)
    runs[s] = lab

counts = [n_comms(runs[s]) for s in SEEDS]
gt_nmi = [nmi(GROUND_TRUTH, runs[s]) for s in SEEDS]
gt_ari = [ari(GROUND_TRUTH, runs[s]) for s in SEEDS]

print(f"커뮤니티 개수 분포: {dict(sorted(Counter(counts).items()))}")
print(f"개수 범위 {min(counts)} ~ {max(counts)} (평균 {np.mean(counts):.2f})")
print(f"정답과의 NMI: 최소 {min(gt_nmi):.3f} / 평균 {np.mean(gt_nmi):.3f} / 최대 {max(gt_nmi):.3f}")
print(f"정답과의 ARI: 최소 {min(gt_ari):.3f} / 평균 {np.mean(gt_ari):.3f} / 최대 {max(gt_ari):.3f}")
# 출력: 커뮤니티 개수 분포: {1: 3, 3: 4, 4: 2, 5: 13, 6: 8}
# 출력: 개수 범위 1 ~ 6 (평균 4.53)
# 출력: 정답과의 NMI: 최소 0.000 / 평균 0.778 / 최대 1.000
# 출력: 정답과의 ARI: 최소 0.000 / 평균 0.670 / 최대 1.000

# %% [markdown]
# 커뮤니티가 **1개에서 6개까지** 나온다. 최악의 시드에서는 그래프 전체가 한 덩어리로
# 뭉개져(monster community) NMI가 0이 된다. 같은 입력에 같은 코드인데도.
#
# 보고서에 "우리 조직은 5개 팀으로 나뉩니다"라고 쓸 수 있는가? 쓸 수 없다.
# 내일 돌리면 6개일 수도, 1개일 수도 있다. **이것이 이 카드의 답이다.**
#
# ## 6. 실행 쌍끼리 비교 — 정답을 몰라도 흔들림은 보인다
#
# 실무에서는 정답 분할을 모른다. 그래도 **실행끼리** 비교하면 불안정성이 드러난다.

# %%
K = len(SEEDS)
pair_nmi = np.ones((K, K))
pair_ari = np.ones((K, K))
for i in range(K):
    for j in range(i + 1, K):
        pair_nmi[i, j] = pair_nmi[j, i] = nmi(runs[SEEDS[i]], runs[SEEDS[j]])
        pair_ari[i, j] = pair_ari[j, i] = ari(runs[SEEDS[i]], runs[SEEDS[j]])

off = ~np.eye(K, dtype=bool)
print(f"실행 쌍 NMI: 평균 {pair_nmi[off].mean():.3f}  최소 {pair_nmi[off].min():.3f}")
print(f"실행 쌍 ARI: 평균 {pair_ari[off].mean():.3f}  최소 {pair_ari[off].min():.3f}")
print(f"완전히 동일한 분할(ARI=1) 쌍 비율: {(pair_ari[off] > 0.999).mean() * 100:.1f}%")
# 출력: 실행 쌍 NMI: 평균 0.628  최소 0.000
# 출력: 실행 쌍 ARI: 평균 0.488  최소 0.000
# 출력: 완전히 동일한 분할(ARI=1) 쌍 비율: 2.3%

# %% [markdown]
# ## 7. 비결정성의 두 원인 분해
#
# 무작위성이 들어가는 자리는 정확히 둘이다.
#
# | 변형 | 방문 순서 | 동점 처리 |
# |---|---|---|
# | A. 원논문 그대로 | 무작위 | 무작위 |
# | B. 순서만 무작위 | 무작위 | 최소 라벨 (결정적) |
# | C. 동점만 무작위 | 고정 (ID 순) | 무작위 |
# | D. 둘 다 고정 | 고정 (ID 순) | 자기 라벨 유지 (결정적) |
#
# D는 **완전히 결정적**이다 — 시드를 바꿔도 항상 같은 답이 나온다.
# 그러면 D를 쓰면 되는 것 아닌가? 결과를 보자.

# %%
VARIANTS = {
    "A.순서+동점 무작위": dict(shuffle_order=True, random_tie=True),
    "B.순서만 무작위": dict(shuffle_order=True, random_tie=False),
    "C.동점만 무작위": dict(shuffle_order=False, random_tie=True),
    "D.둘 다 고정(결정적)": dict(shuffle_order=False, random_tie=False),
}

variant_stats = {}
for name, kw in VARIANTS.items():
    labs = [label_propagation(ADJ, seed=s, **kw)[0] for s in SEEDS]
    aris = [ari(labs[i], labs[j]) for i in range(len(labs)) for j in range(i + 1, len(labs))]
    cs = [n_comms(l) for l in labs]
    variant_stats[name] = dict(
        mean_ari=float(np.mean(aris)),
        min_ari=float(np.min(aris)),
        n_distinct=len({tuple(l.tolist()) for l in labs}),
        counts=cs,
        gt_nmi=float(np.mean([nmi(GROUND_TRUTH, l) for l in labs])),
    )
    print(f"{name:20s} 실행쌍 ARI 평균 {np.mean(aris):.3f}  "
          f"서로 다른 분할 {variant_stats[name]['n_distinct']:2d}/30개  "
          f"커뮤니티 수 {min(cs)}~{max(cs)}  "
          f"정답 NMI 평균 {variant_stats[name]['gt_nmi']:.3f}")
# 출력: A.순서+동점 무작위     실행쌍 ARI 평균 0.488  서로 다른 분할 30/30개  커뮤니티 수 1~6  정답 NMI 평균 0.778
# 출력: B.순서만 무작위       실행쌍 ARI 평균 0.285  서로 다른 분할 16/30개  커뮤니티 수 1~4  정답 NMI 평균 0.226
# 출력: C.동점만 무작위       실행쌍 ARI 평균 0.700  서로 다른 분할 21/30개  커뮤니티 수 1~7  정답 NMI 평균 0.098
# 출력: D.둘 다 고정(결정적)   실행쌍 ARI 평균 1.000  서로 다른 분할  1/30개  커뮤니티 수 1~1  정답 NMI 평균 0.000

# %% [markdown]
# 여기서 이 실험의 핵심 반전이 나온다.
#
# **무작위성을 덜어낼수록 품질이 무너진다.** 정답과의 NMI가
# A 0.78 → B 0.23 → C 0.10 → D 0.00 으로 떨어진다.
# D는 30번 모두 같은 답을 주지만 그 답은 "커뮤니티 1개", 즉 그래프 전체가 한 덩어리다.
# 재현 가능한 쓰레기를 얻은 것이다. B와 C는 더 나쁘다 — 품질은 무너졌는데
# 재현성도 못 얻었다(실행쌍 ARI 0.29, 0.70).
#
# 이유는 라벨 전파의 작동 원리에 있다. 무작위성은 **대칭을 깨는 장치**다.
# 초기에는 모든 라벨의 세력이 같아서 동점이 사방에서 발생하는데, 이때 무작위로
# 갈라 주지 않으면 한 라벨이 연쇄적으로 전체를 먹어 버린다(거대 커뮤니티 붕괴,
# monster community). 즉 **비결정성은 떼어낼 수 있는 결함이 아니라
# 알고리즘이 작동하는 메커니즘의 일부**다.
#
# 그래서 현실적인 처방은 "무작위성 제거"가 아니라 **시드 고정 + 여러 시드 합의**다.
#
# ## 8. 수렴 보장이 없다 — 동기 갱신의 진동
#
# 원논문의 비동기 갱신은 "고칠 게 없으면 멈춘다"로 대개 끝나지만,
# **이론적 수렴 보장은 없다**. 특히 모든 노드를 이전 라운드 라벨만 보고 한꺼번에
# 갱신하는 **동기(synchronous)** 방식은 이분 구조에서 영원히 진동한다.
#
# 완전 이분 그래프 $K_{a,b}$를 보자. 한쪽 전부가 상대편의 라벨을 받고, 상대편도
# 동시에 이쪽 라벨을 받는다. 두 집단의 라벨이 매 라운드 **맞바꿔진다**.

# %%
def label_propagation_sync(adj, rounds=20, seed=0):
    """동기 갱신 — 모든 노드가 '직전 라운드' 라벨만 보고 동시에 갱신."""
    rnd = random.Random(seed)
    nodes = sorted(adj)
    label = {v: i for i, v in enumerate(nodes)}
    hist = []
    for _ in range(rounds):
        new = {}
        for v in nodes:
            if not adj[v]:
                new[v] = label[v]
                continue
            cnt = Counter(label[u] for u in adj[v])
            top = max(cnt.values())
            best = sorted(l for l, c in cnt.items() if c == top)
            new[v] = rnd.choice(best)
        changed = sum(1 for v in nodes if new[v] != label[v])
        hist.append(changed)
        label = new
    return np.array([label[v] for v in nodes]), hist


B = nx.complete_bipartite_graph(6, 6)
badj = {v: sorted(B.neighbors(v)) for v in B.nodes()}

_, sync_hist = label_propagation_sync(badj, rounds=20, seed=1)
_, async_rounds, async_hist = label_propagation(badj, seed=1, rounds=20)
print(f"K(6,6) 동기   라운드별 변경 노드 수: {sync_hist}")
print(f"K(6,6) 비동기 라운드별 변경 노드 수: {async_hist}  (라운드 {async_rounds}회에 정지)")
# 출력: K(6,6) 동기   라운드별 변경 노드 수: [12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12]
# 출력: K(6,6) 비동기 라운드별 변경 노드 수: [11, 2, 0]  (라운드 3회에 정지)

# %% [markdown]
# 동기 갱신은 20라운드 내내 12개 노드가 전부 뒤집힌다. **주기 2의 진동**이고,
# 라운드를 늘려도 끝나지 않는다. 비동기는 2라운드에 멈춘다.
#
# 그래서 원논문도 비동기를 택했다. 하지만 비동기의 대가가 바로 **방문 순서 의존성**,
# 즉 위에서 본 비결정성이다. **진동을 피하려고 무작위 순서를 도입했고,
# 그 무작위 순서가 결과를 흔든다.** 이 맞교환이 라벨 전파의 본질적 성질이다.
#
# ## 9. 준동기(semi-synchronous) 변형
#
# Cordasco & Gargano(2010)의 준동기 변형은 이 맞교환을 깬다.
#
# 1. 그래프를 **색칠**한다 (인접한 노드는 다른 색)
# 2. 같은 색 노드끼리는 서로 인접하지 않으므로 **독립집합**이다
# 3. 색 클래스 단위로 동시에 갱신하고, 색은 순차적으로 처리한다
#
# 독립집합 안에서는 서로의 라벨을 보지 않으니 동시 갱신해도 충돌이 없다.
# 그래서 **동기 방식의 병렬성**(색 클래스 안은 한꺼번에)과 **비동기 방식의 수렴성**을
# 동시에 얻는다. 원논문 대비 얻는 것은 **수렴 보장**과 **병렬화 가능성**이지
# 결정성 그 자체가 아니다 — 동점 처리를 무작위로 두면 여전히 시드에 따라 흔들린다.
# 색칠은 그리디로 $O(m)$이라 비용도 그대로다.

# %%
def label_propagation_semisync(adj, seed=0, rounds=100, random_tie=True):
    """준동기 — 그래프 색칠 후 색 클래스 단위로 동시 갱신."""
    g = nx.Graph()
    g.add_nodes_from(adj)
    for v, nb in adj.items():
        for u in nb:
            g.add_edge(v, u)
    coloring = nx.coloring.greedy_color(g, strategy="largest_first")
    classes = defaultdict(list)
    for v, c in coloring.items():
        classes[c].append(v)
    classes = [sorted(classes[c]) for c in sorted(classes)]

    rnd = random.Random(seed)
    nodes = sorted(adj)
    label = {v: i for i, v in enumerate(nodes)}
    hist = []
    for r in range(rounds):
        changed = 0
        for cls in classes:  # 색 순서는 고정
            snapshot = dict(label)
            for v in cls:  # 같은 색끼리는 인접하지 않음 → 동시 갱신 안전
                if not adj[v]:
                    continue
                cnt = Counter(snapshot[u] for u in adj[v])
                top = max(cnt.values())
                best = [l for l, c in cnt.items() if c == top]
                if random_tie:
                    pick = rnd.choice(best)
                else:
                    pick = label[v] if label[v] in best else min(best)
                if label[v] != pick:
                    label[v] = pick
                    changed += 1
        hist.append(changed)
        if changed == 0:
            break
    return np.array([label[v] for v in nodes]), r + 1, hist, len(classes)


_, ss_r, ss_hist, ncolors = label_propagation_semisync(badj, seed=1, rounds=20)
print(f"K(6,6) 준동기 색 {ncolors}개, 라운드별 변경 {ss_hist} (라운드 {ss_r}회에 정지)")

ss_runs = [label_propagation_semisync(ADJ, seed=s)[0] for s in SEEDS]
ss_aris = [ari(ss_runs[i], ss_runs[j]) for i in range(len(ss_runs)) for j in range(i + 1, len(ss_runs))]
print(f"150노드 준동기: 커뮤니티 수 {min(n_comms(l) for l in ss_runs)}~{max(n_comms(l) for l in ss_runs)}, "
      f"실행쌍 ARI 평균 {np.mean(ss_aris):.3f}, "
      f"정답 NMI 평균 {np.mean([nmi(GROUND_TRUTH, l) for l in ss_runs]):.3f}")

ssd_runs = [label_propagation_semisync(ADJ, seed=s, random_tie=False)[0] for s in SEEDS]
print(f"150노드 준동기(동점도 결정적): 서로 다른 분할 {len({tuple(l.tolist()) for l in ssd_runs})}종, "
      f"커뮤니티 {n_comms(ssd_runs[0])}개, 정답 NMI {nmi(GROUND_TRUTH, ssd_runs[0]):.3f}")
# 출력: K(6,6) 준동기 색 2개, 라운드별 변경 [11, 4, 0] (라운드 3회에 정지)
# 출력: 150노드 준동기: 커뮤니티 수 2~6, 실행쌍 ARI 평균 0.672, 정답 NMI 평균 0.880
# 출력: 150노드 준동기(동점도 결정적): 서로 다른 분할 1종, 커뮤니티 1개, 정답 NMI 0.000

# %% [markdown]
# 준동기는 $K_{6,6}$에서 진동 없이 3라운드에 멈추고, 150노드 그래프에서는
# 정답 NMI 평균 0.88로 원논문 비동기(0.78)보다 오히려 낫다.
# 하지만 동점을 결정적으로 처리하면 여기서도 커뮤니티 1개로 붕괴한다 —
# **준동기가 고쳐 주는 것은 진동이지 비결정성이 아니다.**
#
# ## 10. 실무 처방 — 합의 군집화(consensus clustering)
#
# 무작위성을 없앨 수 없다면 **여러 번 돌려서 합의를 본다.**
#
# 1. 시드를 바꿔 $R$번 돌린다
# 2. 공동출현 행렬(co-association) $C_{uv} = \frac{1}{R}\sum_r \mathbb{1}[L_r(u) = L_r(v)]$
# 3. $C_{uv} \ge \tau$ 인 쌍만 남긴 그래프의 연결 성분을 최종 분할로 삼는다
#
# "몇 번을 돌려도 늘 같이 묶이는 노드"만 같은 커뮤니티로 인정하는 것이다.
# 덤으로 $C_{uv}$ 자체가 **신뢰도**가 된다 — 보고서에 "이 두 사람은 30번 중 28번
# 같은 팀으로 묶였습니다"라고 쓸 수 있다.

# %%
co = np.zeros((len(NODES), len(NODES)))
for s in SEEDS:
    l = runs[s]
    co += (l[:, None] == l[None, :])
co /= len(SEEDS)

consensus_rows = []
for tau in (0.5, 0.6, 0.7, 0.8, 0.9):
    H = nx.from_numpy_array((co >= tau).astype(int))
    comps = list(nx.connected_components(H))
    cl = np.empty(len(NODES), dtype=int)
    for ci, c in enumerate(comps):
        for v in c:
            cl[v] = ci
    consensus_rows.append((tau, len(comps), nmi(GROUND_TRUTH, cl), ari(GROUND_TRUTH, cl), cl))
    print(f"τ={tau}: 커뮤니티 {len(comps):2d}개  크기 {sorted((len(c) for c in comps), reverse=True)[:7]}  "
          f"정답 NMI {nmi(GROUND_TRUTH, cl):.3f}  ARI {ari(GROUND_TRUTH, cl):.3f}")

best_tau, _, best_nmi, best_ari, consensus_labels = max(consensus_rows, key=lambda r: r[3])
print(f"\n최선 τ={best_tau} → NMI {best_nmi:.3f} / ARI {best_ari:.3f} "
      f"(단일 실행 평균 NMI {np.mean(gt_nmi):.3f})")
# 출력: τ=0.5: 커뮤니티  4개  크기 [75, 25, 25, 25]  정답 NMI 0.819  ARI 0.563
# 출력: τ=0.6: 커뮤니티  5개  크기 [49, 26, 25, 25, 25]  정답 NMI 0.916  ARI 0.811
# 출력: τ=0.7: 커뮤니티  7개  크기 [25, 25, 25, 25, 25, 24, 1]  정답 NMI 0.992  ARI 0.992
# 출력: τ=0.8: 커뮤니티  8개  크기 [25, 25, 25, 25, 24, 22, 3]  정답 NMI 0.976  ARI 0.970
# 출력: τ=0.9: 커뮤니티  9개  크기 [25, 25, 25, 24, 24, 22, 3]  정답 NMI 0.968  ARI 0.961
# 출력:
# 출력: 최선 τ=0.7 → NMI 0.992 / ARI 0.992 (단일 실행 평균 NMI 0.778)

# %% [markdown]
# 개별 실행은 평균 NMI 0.78로 흔들리는데(최악 0.00), 30번을 합의하면 τ=0.7에서
# NMI 0.99로 정답을 거의 그대로
# 복원한다. **불안정한 알고리즘을 여러 번 돌려 안정적인 추정기로 바꾼 것**이다.
# 비용은 $R$배 늘지만 원래가 $O(m)$이라 감당된다 — 이것이 라벨 전파의 속도를
# 실제로 쓰는 방식이다.
#
# ## 11. 비교 대상 — 루뱅은 얼마나 안정적인가
#
# 참고로 모듈러리티 기반(루뱅)도 무작위성이 있지만, 목적함수를 놓고 **개선 방향으로만**
# 움직이므로 분할이 훨씬 덜 흔들린다. 대신 해상도 한계라는 다른 병이 있다(10.4절).

# %%
lv_runs = []
for s in SEEDS[:15]:
    comms = nx.community.louvain_communities(G, seed=s)
    lab = np.empty(len(NODES), dtype=int)
    for ci, c in enumerate(comms):
        for v in c:
            lab[v] = ci
    lv_runs.append(lab)

lv_aris = [ari(lv_runs[i], lv_runs[j]) for i in range(len(lv_runs)) for j in range(i + 1, len(lv_runs))]
print(f"루뱅 실행쌍 ARI 평균 {np.mean(lv_aris):.3f} (최소 {np.min(lv_aris):.3f}), "
      f"커뮤니티 수 {[n_comms(l) for l in lv_runs][:8]}...")
print(f"라벨 전파 실행쌍 ARI 평균 {pair_ari[off].mean():.3f} (최소 {pair_ari[off].min():.3f})")
# 출력: 루뱅 실행쌍 ARI 평균 0.983 (최소 0.907), 커뮤니티 수 [6, 6, 6, 6, 6, 6, 6, 6]...
# 출력: 라벨 전파 실행쌍 ARI 평균 0.488 (최소 0.000)

# %% [markdown]
# ## 12. 시각화

# %%
fig = make_subplots(
    rows=2,
    cols=2,
    subplot_titles=(
        "① 시드 30개 → 커뮤니티 개수가 1~6개로 흔들린다",
        "② 실행 쌍끼리의 ARI (1=동일 분할)",
        "③ 무작위성을 없앨수록 품질이 무너진다 — 답은 제거가 아니라 합의",
        "④ K(6,6): 동기는 영원히 진동, 비동기·준동기는 정지",
    ),
    specs=[[{"type": "bar"}, {"type": "heatmap"}], [{"type": "bar"}, {"type": "scatter"}]],
    vertical_spacing=0.16,
    horizontal_spacing=0.11,
)

# ① 시드별 커뮤니티 개수
fig.add_trace(
    go.Bar(
        x=SEEDS,
        y=counts,
        marker_color=["#d62728" if c != N_GROUPS else "#2ca02c" for c in counts],
        text=counts,
        textposition="outside",
        name="커뮤니티 수",
        showlegend=False,
        hovertemplate="seed=%{x}<br>커뮤니티 %{y}개<extra></extra>",
    ),
    row=1,
    col=1,
)
fig.add_hline(y=N_GROUPS, line_dash="dash", line_color="#555", row=1, col=1,
              annotation_text="정답 6개", annotation_position="top right")

# ② 실행쌍 ARI 히트맵
fig.add_trace(
    go.Heatmap(
        z=pair_ari,
        x=SEEDS,
        y=SEEDS,
        colorscale="RdYlGn",
        zmin=0,
        zmax=1,
        colorbar=dict(title="ARI", len=0.38, y=0.81, x=1.005),
        hovertemplate="seed %{x} vs %{y}<br>ARI %{z:.3f}<extra></extra>",
    ),
    row=1,
    col=2,
)

# ③ 재현성 vs 품질
vnames = list(variant_stats) + ["E.준동기(색칠)", f"F.합의(τ={best_tau})", "G.루뱅(참고)"]
repro = [variant_stats[n]["mean_ari"] for n in variant_stats] + [
    float(np.mean(ss_aris)), 1.0, float(np.mean(lv_aris))]
quality = [variant_stats[n]["gt_nmi"] for n in variant_stats] + [
    float(np.mean([nmi(GROUND_TRUTH, l) for l in ss_runs])), best_nmi,
    float(np.mean([nmi(GROUND_TRUTH, l) for l in lv_runs]))]
fig.add_trace(
    go.Bar(x=vnames, y=repro, name="재현성 (실행쌍 ARI)", marker_color="#1f77b4",
           text=[f"{v:.2f}" for v in repro], textposition="outside",
           hovertemplate="%{x}<br>재현성 %{y:.3f}<extra></extra>"),
    row=2, col=1,
)
fig.add_trace(
    go.Bar(x=vnames, y=quality, name="품질 (정답과의 NMI)", marker_color="#d62728",
           text=[f"{v:.2f}" for v in quality], textposition="outside",
           hovertemplate="%{x}<br>품질 %{y:.3f}<extra></extra>"),
    row=2, col=1,
)

# ④ 진동
fig.add_trace(
    go.Scatter(x=list(range(1, len(sync_hist) + 1)), y=sync_hist, mode="lines+markers",
               name="동기(synchronous)", line=dict(color="#d62728", width=3)),
    row=2, col=2,
)
fig.add_trace(
    go.Scatter(x=list(range(1, len(async_hist) + 1)), y=async_hist, mode="lines+markers",
               name="비동기(asynchronous)", line=dict(color="#2ca02c", width=3)),
    row=2, col=2,
)
fig.add_trace(
    go.Scatter(x=list(range(1, len(ss_hist) + 1)), y=ss_hist, mode="lines+markers",
               name="준동기(semi-sync)", line=dict(color="#1f77b4", width=3, dash="dot")),
    row=2, col=2,
)

fig.update_xaxes(title_text="난수 시드", row=1, col=1)
fig.update_yaxes(title_text="커뮤니티 개수", row=1, col=1, range=[0, 7.5])
fig.update_xaxes(title_text="시드", row=1, col=2)
fig.update_yaxes(title_text="시드", row=1, col=2, autorange="reversed")
fig.update_yaxes(title_text="점수 (1 = 최선)", row=2, col=1, range=[0, 1.22])
fig.update_xaxes(title_text="라운드", row=2, col=2)
fig.update_yaxes(title_text="라벨이 바뀐 노드 수", row=2, col=2)

fig.update_layout(
    title_text="라벨 전파: 싸지만 흔들린다 — 같은 그래프, 시드만 바꾼 30회 실행",
    height=880,
    width=1350,
    showlegend=True,
    legend=dict(orientation="h", y=-0.09, x=0.30),
    template="plotly_white",
    bargap=0.25,
    barmode="group",
)

_show(fig)

fig.write_image("expy.png", scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 13. 정리
#
# | 항목 | 라벨 전파 | 모듈러리티 최적화(루뱅/라이덴) |
# |---|---|---|
# | 비용 | 라운드당 $O(m)$, 사실상 준선형 | $O(m \log n)$ 이상, 그리디 병합은 더 비쌈 |
# | 파라미터 | 없음 (커뮤니티 수도 자동) | 해상도 $\gamma$ |
# | 재현성 | **시드마다 다름** | 대체로 안정 |
# | 병리 | 거대 커뮤니티 붕괴, 진동 | 해상도 한계(작은 뭉치 병합) |
#
# 실무 수칙:
#
# 1. **시드를 고정하고, 고정했다는 사실을 문서에 적는다.** 파이프라인 인자로 노출한다.
# 2. **한 번만 돌리지 않는다.** 여러 시드로 돌려 실행쌍 NMI/ARI를 함께 보고한다.
#    평균 ARI가 0.5 수준이면 그 분할은 보고서에 올릴 물건이 아니다.
# 3. 무작위성을 **없애지는 말 것.** 없애면 재현은 되지만 거대 커뮤니티로 붕괴한다.
#    대신 **합의 군집화**로 안정적인 분할과 신뢰도를 함께 얻는다.
# 4. 진동이 걱정되면(동기 구현·병렬 구현) **준동기 변형**을 쓴다.
# 5. 커뮤니티 **개수는 알고리즘이 아니라 쓰임새로 정한다.**
# 6. 라벨 전파는 "억 단위 간선을 한 번 훑어보는 정찰"에 쓰고, 최종 보고에는
#    라이덴처럼 안정적인 방법을 쓴다.
