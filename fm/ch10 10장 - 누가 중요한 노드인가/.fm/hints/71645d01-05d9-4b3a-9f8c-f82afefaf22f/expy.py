# %% [markdown]
# # 근사가 잘 듣는 그래프 vs 안 듣는 그래프
#
# `ex3_betweenness_cost.py`의 마지막 문단이 주장하는 건 이것이다.
#
# > 이 예제의 그래프는 커뮤니티와 다리가 있는 «구조 있는» 그래프다.
# > 완전 무작위 그래프에서 같은 실험을 하면 일치율이 10~50%로 떨어진다.
# > 매개 중심성이 거의 평평해서 상위 20개라는 게 사실상 무작위이기 때문이다.
#
# 이 노트북에서 **같은 크기·같은 엣지 수**의 두 그래프를 만들어 직접 확인한다.
#
# | 그래프 | 만드는 법 | 매개 중심성 분포 |
# |---|---|---|
# | 구조 있음 | 커뮤니티 여러 개 + 그룹 사이 다리 하나씩 | 뾰족하다 (다리 노드가 독점) |
# | 무작위 (에르되시–레니) | 같은 엣지 수를 무작위 쌍에 뿌린다 | 평평하다 (모두 비슷) |
#
# 표본 근사의 성패를 가르는 건 **알고리즘이 아니라 값의 분포**다.
#
# ## 신호 대 잡음
#
# 브랜디스 표본 근사는 전체 $n$개 출발점 중 $k$개만 골라 BFS를 돌리고 결과를 되돌린다.
#
# $$\hat{c}(v) = \frac{n}{k} \sum_{s \in S} \delta_s(v), \qquad |S| = k$$
#
# 이건 불편 추정량이고, 표준오차는 표본 크기의 제곱근에 반비례한다.
#
# $$\mathrm{SE}[\hat{c}(v)] \;=\; \frac{n\,\sigma_v}{\sqrt{k}} \;\propto\; \frac{1}{\sqrt{k}}$$
#
# 우리가 원하는 건 값이 아니라 **순위**다. 노드 $v$와 $w$의 순위가 뒤집히지 않으려면
# 참값의 간극이 잡음보다 커야 한다.
#
# $$\mathrm{SNR}_{v,w} \;=\; \frac{|c(v) - c(w)|}{\sqrt{\mathrm{SE}[\hat c(v)]^2 + \mathrm{SE}[\hat c(w)]^2}} \;\gg\; 1$$
#
# 분모(잡음)는 $k$만 늘리면 줄어든다. 문제는 **분자(신호)**다.
# 분포가 평평하면 커트라인 근처의 $|c(v)-c(w)|$가 0에 가깝고, $k$를 아무리 키워도 SNR이 안 올라간다.
# 그래서 무작위 그래프의 «상위 20개»는 표본을 바꿀 때마다 다른 20개가 나온다.
# 근사가 틀린 게 아니라, **애초에 상위 20개라는 게 존재하지 않는다**.

# %%
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용)
import random
import time
from collections import defaultdict, deque

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


N = 800          # 노드 수
AVG_DEG = 6      # 평균 차수
TOPK = 20        # «상위 20개»
TRIALS = 10      # 표본 시드를 바꿔 몇 번 반복할지
RATES = (0.01, 0.05, 0.10, 0.20)

KOR = "Apple SD Gothic Neo, AppleGothic, Noto Sans KR, sans-serif"
C_STRUCT = "#2563eb"   # 구조 있음
C_RANDOM = "#ea580c"   # 무작위

print(f"노드 {N}개, 평균 차수 {AVG_DEG}, 상위 {TOPK}개 비교, 표본 시드 {TRIALS}개")
# 출력:
# 노드 800개, 평균 차수 6, 상위 20개 비교, 표본 시드 10개


# %% [markdown]
# ## 1단계 — 두 그래프를 만든다
#
# `make()`는 에셋의 `ex3_betweenness_cost.py`에 있는 것 그대로다.
# 그룹 안은 촘촘하게 잇고, 그룹 사이는 **다리 하나씩만** 놓는다.
# 그 다리 위에 앉은 노드가 그룹 간 최단 경로를 전부 독점한다 — 이게 «진짜 급소»다.
#
# 비교 대상인 에르되시–레니 그래프 $G(n, m)$는 **엣지 수를 똑같이 맞춘다.**
# 밀도가 달라서 생기는 차이가 아니라 **배치가 달라서 생기는 차이**라는 걸 못 박기 위해서다.

# %%
def make(n, avg_deg=6, seed=11, groups=None):
    """커뮤니티 + 다리 구조. 에셋 ex3_betweenness_cost.py 와 동일."""
    rnd = random.Random(seed)
    groups = groups or max(4, n // 60)
    size = n // groups
    adj = defaultdict(set)
    for g in range(groups):                     # 그룹 안은 촘촘하게
        lo, hi = g * size, min((g + 1) * size, n)
        members = list(range(lo, hi))
        for a in members:
            for _ in range(avg_deg // 2):
                b = rnd.choice(members)
                if a != b:
                    adj[a].add(b); adj[b].add(a)
    for g in range(groups - 1):                 # 그룹 사이는 다리 하나씩
        a, b = g * size, (g + 1) * size
        if b < n:
            adj[a].add(b); adj[b].add(a)
    for v in range(n):
        adj.setdefault(v, set())
    return {k: sorted(v) for k, v in adj.items()}


def erdos_renyi(n, m, seed=7):
    """G(n, m) — 엣지 m 개를 무작위 쌍에 뿌린다. 구조가 «없는» 대조군."""
    rnd = random.Random(seed)
    adj = {v: set() for v in range(n)}
    seen = set()
    while len(seen) < m:
        a, b = rnd.randrange(n), rnd.randrange(n)
        if a == b:
            continue
        e = (a, b) if a < b else (b, a)
        if e in seen:
            continue
        seen.add(e)
        adj[e[0]].add(e[1]); adj[e[1]].add(e[0])
    return {k: sorted(v) for k, v in adj.items()}


def edge_count(adj):
    return sum(len(v) for v in adj.values()) // 2


G_STRUCT = make(N, AVG_DEG, seed=11)
M = edge_count(G_STRUCT)
G_RANDOM = erdos_renyi(N, M, seed=7)
GRAPHS = {"구조 있음": G_STRUCT, "무작위(ER)": G_RANDOM}

for name, adj in GRAPHS.items():
    degs = sorted(len(v) for v in adj.values())
    print(f"{name:<10} 노드 {len(adj)}  엣지 {edge_count(adj)}  "
          f"평균차수 {2*edge_count(adj)/len(adj):.2f}  차수범위 {degs[0]}~{degs[-1]}")
# 출력:
# 구조 있음      노드 800  엣지 2273  평균차수 5.68  차수범위 0~13
# 무작위(ER)    노드 800  엣지 2273  평균차수 5.68  차수범위 1~16


# %% [markdown]
# ## 2단계 — 매개 중심성 (브랜디스)
#
# `sources`를 주면 그 노드들에서만 BFS를 시작한다. 그게 곧 표본 근사다.
# 반환값은 스케일을 안 맞춘 원합계라서, 전수와 비교하려면 $n/k$를 곱해야 한다.
# 다만 **순위만 볼 거라면 곱하든 말든 결과가 같다.**

# %%
def brandes(adj, sources=None):
    """브랜디스 알고리즘. sources 를 주면 그 노드에서만 시작한다(근사)."""
    cb = {v: 0.0 for v in adj}
    for s in (sources if sources is not None else adj):
        stack, pred = [], {v: [] for v in adj}
        sigma = {v: 0 for v in adj}; sigma[s] = 1
        dist = {v: -1 for v in adj}; dist[s] = 0
        q = deque([s])
        while q:
            v = q.popleft(); stack.append(v)
            for w in adj[v]:
                if dist[w] < 0:
                    dist[w] = dist[v] + 1; q.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]; pred[w].append(v)
        delta = {v: 0.0 for v in adj}
        while stack:
            w = stack.pop()
            for v in pred[w]:
                delta[v] += sigma[v] / sigma[w] * (1 + delta[w])
            if w != s:
                cb[w] += delta[w]
    return cb


EXACT = {}
for name, adj in GRAPHS.items():
    t0 = time.perf_counter()
    EXACT[name] = brandes(adj)
    print(f"{name:<10} 전수 계산 {time.perf_counter() - t0:.2f}s")
# 출력:
# 구조 있음      전수 계산 0.84s
# 무작위(ER)    전수 계산 1.08s


# %% [markdown]
# ## 3단계 — 분포를 본다. 여기서 이미 답이 나온다
#
# 일치율을 재기 **전에** 값의 분포부터 본다. 순위 실험은 이 분포의 결과일 뿐이다.

# %%
def sorted_vals(c):
    return sorted(c.values(), reverse=True)


def describe(c, k=TOPK):
    v = sorted_vals(c)
    n = len(v)
    total = sum(v)
    mean = total / n
    med = v[n // 2]
    return {
        "최댓값": v[0],
        f"{k}위 값": v[k - 1],
        "중앙값": med,
        "평균": mean,
        f"상위{k}중앙 / 전체중앙": (v[k // 2] / med) if med else float("inf"),
        f"{k}위/{2*k}위 상대간극": ((v[k - 1] - v[2 * k - 1]) / v[k - 1]) if v[k - 1] else 0.0,
    }


hdr = list(describe(EXACT["구조 있음"]).keys())
print(f"{'':<12}" + "".join(f"{h:>22}" for h in hdr))
for name in GRAPHS:
    d = describe(EXACT[name])
    print(f"{name:<12}" + "".join(f"{d[h]:>22,.2f}" for h in hdr))
# 출력:
#                                최댓값                 20위 값                   중앙값                    평균         상위20중앙 / 전체중앙          20위/40위 상대간극
# 구조 있음                   355,795.01             27,241.64                553.34              6,403.96                306.76                  0.44
# 무작위(ER)                  13,851.81              7,275.91              1,943.90              2,431.46                  4.12                  0.13


# %% [markdown]
# 숫자 하나만 보면 된다. **상위 20의 중앙값 ÷ 전체 중앙값**이
#
# - 구조 있는 그래프에서 **307배**
# - 무작위 그래프에서 **4.1배**
#
# 307배면 표본 잡음이 값을 두세 배 흔들어도 순위가 안 바뀐다.
# 4.1배면 잡음이 그대로 순위를 뒤집는다. «커트라인 근처가 다 고만고만하다»는 뜻이다.
#
# 20위와 40위의 상대 간극(0.44 vs 0.13)도 같은 이야기를 한다.
# 무작위 그래프는 20위와 40위가 13%밖에 차이 안 난다 — **20위와 40위를 구분할 근거가 없다.**

# %% [markdown]
# ## 4단계 — 표본 근사 상위 20 일치율
#
# 표본율 1 / 5 / 10 / 20 %, 각각 시드 10개로 반복한다.
# 완전히 무작위로 20개를 찍었을 때의 기대 일치율은 $k/n = 20/800 = 2.5\%$다.

# %%
def top_set(c, k=TOPK):
    return {v for v, _ in sorted(c.items(), key=lambda x: (-x[1], x[0]))[:k]}


def run_trials(adj, exact_c, rate, trials=TRIALS, k=TOPK):
    """표본율 rate 로 trials 번 근사. (일치율 리스트, 스케일 보정한 추정값 리스트) 반환."""
    nodes = sorted(adj)
    n = len(nodes)
    ks = max(5, int(n * rate))
    truth = top_set(exact_c, k)
    overlaps, estimates = [], []
    for t in range(trials):
        s = random.Random(1000 + t).sample(nodes, ks)
        ap = brandes(adj, s)
        overlaps.append(len(truth & top_set(ap, k)) / k)
        estimates.append({v: x * n / ks for v, x in ap.items()})   # n/k 로 스케일 보정
    return overlaps, estimates


RESULT, EST_5PCT = {}, {}
t0 = time.perf_counter()
for name, adj in GRAPHS.items():
    RESULT[name] = {}
    for rate in RATES:
        ov, est = run_trials(adj, EXACT[name], rate)
        RESULT[name][rate] = ov
        if rate == 0.05:
            EST_5PCT[name] = est
print(f"실험 총 소요 {time.perf_counter() - t0:.1f}s\n")

print(f"{'그래프':<12}{'표본율':>8}{'평균 일치율':>12}{'최저':>8}{'최고':>8}   시드별")
for name in GRAPHS:
    for rate in RATES:
        ov = RESULT[name][rate]
        avg = sum(ov) / len(ov)
        print(f"{name:<12}{rate*100:>7.0f}%{avg*100:>11.1f}%{min(ov)*100:>7.0f}%{max(ov)*100:>7.0f}%"
              f"   {[round(x*100) for x in ov]}")
print(f"\n무작위로 20개 찍었을 때 기대 일치율 = {TOPK}/{N} = {TOPK/N*100:.1f}%")
# 출력:
# 실험 총 소요 7.0s
#
# 그래프              표본율      평균 일치율      최저      최고   시드별
# 구조 있음             1%       71.5%     65%     75%   [65, 70, 70, 75, 75, 70, 75, 75, 70, 70]
# 구조 있음             5%       82.0%     70%     90%   [70, 85, 85, 85, 80, 80, 90, 85, 75, 85]
# 구조 있음            10%       83.0%     75%     95%   [75, 95, 80, 90, 80, 85, 90, 85, 75, 75]
# 구조 있음            20%       88.5%     85%     90%   [90, 90, 85, 90, 85, 90, 85, 90, 90, 90]
# 무작위(ER)           1%       13.5%     10%     20%   [10, 10, 15, 20, 10, 10, 20, 20, 10, 10]
# 무작위(ER)           5%       34.0%     25%     45%   [35, 25, 35, 35, 35, 45, 35, 35, 25, 35]
# 무작위(ER)          10%       39.0%     30%     50%   [50, 35, 35, 30, 45, 35, 40, 40, 35, 45]
# 무작위(ER)          20%       58.5%     50%     70%   [60, 50, 60, 55, 55, 55, 60, 70, 50, 70]
#
# 무작위로 20개 찍었을 때 기대 일치율 = 20/800 = 2.5%


# %% [markdown]
# 에셋의 «10~50%»가 그대로 재현된다 (ER: 13.5 / 34.0 / 39.0 / 58.5%).
#
# 눈여겨볼 두 가지.
#
# 1. **구조 있는 그래프는 표본 1%로도 71.5%를 맞힌다.** 5%에서 82%, 그 뒤로는 완만하다.
#    쓸 만한 상위권은 표본을 조금만 써도 잡힌다.
# 2. **무작위 그래프는 표본을 20배(1%→20%) 늘려도 58.5%다.** 잡음을 줄여도 신호가 없으니
#    수렴이 느리다. $k \to n$이면 물론 100%가 되지만, 그건 전수 계산이다.
#
# 그리고 무작위 그래프의 «상위 20개»는 애초에 의미가 없다. 2.5%보다 높다고 안심할 게 아니다 —
# 상위 20위와 40위의 참값 차이가 13%뿐인데 그중 20개를 골라낸들 뭘 하겠나.

# %% [markdown]
# ## 5단계 — 신호 대 잡음을 직접 잰다
#
# 시드 10개의 추정값에서 노드별 표준편차를 구해 **잡음**을,
# 참값의 인접 순위 간극에서 **신호**를 잰다. 커트라인($k=20$) 주변에서 비교한다.

# %%
def snr_at_cut(exact_c, estimates, k=TOPK):
    order = [v for v, _ in sorted(exact_c.items(), key=lambda x: (-x[1], x[0]))]
    mean_of = lambda v: sum(e[v] for e in estimates) / len(estimates)
    sd_of = lambda v: (sum((e[v] - mean_of(v)) ** 2 for e in estimates) / len(estimates)) ** 0.5
    a, b = order[k - 1], order[k]        # 20위와 21위
    hi, lo = order[k // 2], order[2 * k]  # 10위와 40위
    signal_adj = abs(exact_c[a] - exact_c[b])
    signal_win = abs(exact_c[hi] - exact_c[lo])
    noise = (sd_of(a) ** 2 + sd_of(b) ** 2) ** 0.5
    return {
        "신호(20위-21위)": signal_adj,
        "신호(10위-40위)": signal_win,
        "잡음(표본 표준편차)": noise,
        "SNR(인접)": signal_adj / noise if noise else float("inf"),
        "SNR(창)": signal_win / noise if noise else float("inf"),
    }


SNR = {name: snr_at_cut(EXACT[name], EST_5PCT[name]) for name in GRAPHS}
keys = list(SNR["구조 있음"].keys())
print("표본율 5% 기준\n")
print(f"{'':<12}" + "".join(f"{h:>22}" for h in keys))
for name in GRAPHS:
    print(f"{name:<12}" + "".join(f"{SNR[name][h]:>22,.2f}" for h in keys))
# 출력:
# 표본율 5% 기준
#
#                        신호(20위-21위)           신호(10위-40위)           잡음(표본 표준편차)               SNR(인접)                SNR(창)
# 구조 있음                     1,490.25            154,664.11             16,342.60                  0.09                  9.46
# 무작위(ER)                      24.33              1,677.04              3,255.18                  0.01                  0.52


# %% [markdown]
# 두 가지를 읽어야 한다.
#
# **SNR(인접)은 둘 다 1보다 훨씬 작다.** 20위와 21위를 표본으로 구분하는 건 어느 쪽에서도 불가능하다.
# 그래서 «상위 20 일치율»이 구조 있는 그래프에서도 100%가 아니라 82%인 것이다 —
# 틀리는 건 언제나 **커트라인 바로 근처**다. 이건 근사의 한계지 그래프의 문제가 아니다.
#
# **차이는 창(window)을 넓혔을 때 갈린다.** 10위와 40위처럼 확실히 떨어진 두 노드를 보면
#
# - 구조 있음: SNR **9.46** — 신호가 잡음의 열 배쯤 된다. 10위와 40위를 헷갈릴 일이 없다.
# - 무작위: SNR **0.52** — 신호가 잡음보다 **작다**. 10위와 40위조차 구분이 안 된다.
#
# 무작위 그래프의 잡음(3,255)은 20위 참값(7,276)의 45%다. 신호와 잡음이 같은 크기다.
# 이 상태에서 «상위 20개»를 뽑으면 그건 순위가 아니라 추첨이다.
#
# 결론은 하나다. 잡음은 $1/\sqrt{k}$로 줄일 수 있다. **신호는 그래프가 정해 준다.**

# %% [markdown]
# ## 6단계 — 실무용 사전 점검
#
# 여기까지는 «정답을 알고» 비교한 것이다. 실무에서는 전수 계산 결과가 없다.
# 그런데 다행히, **분포 모양은 표본 추정값만으로도 알 수 있다.**
# 5% 표본을 한 번 돌리고 그 값들의 분포를 보면 된다.

# %%
def precheck(c, k=TOPK):
    v = sorted(c.values(), reverse=True)
    n = len(v)
    total = sum(v)
    mean = total / n
    med = v[n // 2]
    sd = (sum((x - mean) ** 2 for x in v) / n) ** 0.5
    asc = sorted(v)
    gini = (2 * sum((i + 1) * x for i, x in enumerate(asc))) / (n * total) - (n + 1) / n
    return {
        "상위/중앙값 비율": (v[k // 2] / med) if med else float("inf"),
        "변동계수 CV": sd / mean if mean else 0.0,
        "커트라인 간극": ((v[k - 1] - v[2 * k - 1]) / v[k - 1]) if v[k - 1] else 0.0,
        "상위5% 점유율": (sum(v[: n // 20]) / total) if total else 0.0,
        "지니": gini,
    }


keys = list(precheck(EXACT["구조 있음"]).keys())
print(f"{'그래프':<12}{'출처':<10}" + "".join(f"{h:>18}" for h in keys))
for name in GRAPHS:
    for src, c in (("전수", EXACT[name]), ("5% 표본", EST_5PCT[name][0])):
        p = precheck(c)
        print(f"{name:<12}{src:<10}" + "".join(f"{p[h]:>18.3f}" for h in keys))
# 출력:
# 그래프         출처                 상위/중앙값 비율           변동계수 CV           커트라인 간극          상위5% 점유율                지니
# 구조 있음       전수                   306.758             5.311             0.444             0.763             0.896
# 구조 있음       5% 표본                412.425             5.351             0.417             0.782             0.914
# 무작위(ER)     전수                     4.121             0.809             0.128             0.162             0.427
# 무작위(ER)     5% 표본                  6.699             1.062             0.113             0.210             0.517


# %% [markdown]
# **표본만 봐도 판정이 된다.** 상위/중앙값 비율이 412 vs 6.7 — 두 자릿수 가까이 벌어진다.
# 지니도 0.91 vs 0.52, 상위 5% 점유율도 78% vs 21%로 갈린다. 전수를 안 돌려도 결론이 같다.
#
# 주의할 점 하나. 표본 추정은 잡음 때문에 분포를 **실제보다 뾰족하게** 만든다
# (307 → 412, 4.1 → 6.7). 즉 이 점검은 «통과» 쪽으로 편향돼 있다.
# 그래서 임계값은 넉넉히 잡아야 한다 — 「비율 5 이상이면 OK」 같은 기준은
# 완전 무작위 그래프도 통과시킨다.
#
# | 판정 | 상위/중앙값 비율 (5% 표본 기준) | 뜻 | 할 일 |
# |---|---|---|---|
# | 초록 | $\ge 50$ | 급소가 확실히 있다 | 표본 1~5%로 충분 |
# | 노랑 | $10 \sim 50$ | 애매하다 | 표본율 두 배로 늘려 상위 $k$가 안 바뀌는지 확인 |
# | 빨강 | $< 10$ | 평평하다 | 근사 순위를 믿지 마라. 전수를 쓰거나 지표를 바꿔라 |
#
# 값이 하나 더 있으면 좋다: **커트라인 간극**. 20위와 40위의 상대 차이가 0.2 미만이면
# 「상위 20」이라는 컷 자체가 임의적이라는 신호다. $k$를 늘리거나 «상위권»을 집합으로 보고해야 한다.

# %%
def verdict(c, k=TOPK):
    p = precheck(c, k)
    r, g = p["상위/중앙값 비율"], p["커트라인 간극"]
    if r >= 50 and g >= 0.2:
        return "초록 — 표본 1~5%로 상위권을 믿어도 된다"
    if r >= 10:
        return "노랑 — 표본율을 두 배로 늘려 상위 k 안정성을 확인하라"
    return "빨강 — 근사 순위를 믿지 마라 (분포가 평평하다)"


for name in GRAPHS:
    print(f"{name:<12} {verdict(EST_5PCT[name][0])}")
# 출력:
# 구조 있음      초록 — 표본 1~5%로 상위권을 믿어도 된다
# 무작위(ER)     빨강 — 근사 순위를 믿지 마라 (분포가 평평하다)


# %% [markdown]
# 전수 계산 없이, 5% 표본 한 번으로 두 그래프가 정확히 갈렸다.
#
# 그래도 «노랑» 구간(비율 10~50)은 판정이 애매하다. 표본 잡음이 비율을 부풀릴 수 있으니
# 경계에 걸린 그래프는 숫자 하나로 끝내지 말고 **안정성 확인으로 넘기는 게** 맞다.
# 처방은 간단하다 — 표본율만 두 배로 늘려 다시 돌리고, 상위 $k$가 유지되는지 본다.

# %%
# 노랑 처방 실행 — 표본율을 두 배로 늘렸을 때 상위 k 가 얼마나 유지되나
print(f"{'그래프':<12}{'5% vs 10% 상위20 일치':>24}")
for name, adj in GRAPHS.items():
    nodes = sorted(adj)
    a = brandes(adj, random.Random(77).sample(nodes, int(N * 0.05)))
    b = brandes(adj, random.Random(77).sample(nodes, int(N * 0.10)))
    print(f"{name:<12}{len(top_set(a) & top_set(b)) / TOPK * 100:>23.0f}%")
# 출력:
# 그래프                5% vs 10% 상위20 일치
# 구조 있음                            80%
# 무작위(ER)                          45%


# %% [markdown]
# 정답을 몰라도 판정이 된다. **표본율만 바꿔 두 번 돌려 보고 상위 $k$가 흔들리면 근사를 못 믿는 것이다.**
# 80%면 커트라인 근처만 몇 개 바뀐 것이고, 45%면 절반 이상이 갈아치워진 것이다.
# 이게 실무에서 제일 싼 점검이다 — 추가 비용은 BFS 몇십 번.

# %% [markdown]
# ## 7단계 — 시각화

# %%
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "① 매개 중심성 분포 (값 / 평균, 로그축)",
        "② 표본율별 상위 20 일치율",
        "③ 커트라인 주변 신호 대 잡음 (5% 표본, ±1σ)",
        "④ 상위 x% 노드가 차지하는 매개 중심성 총합 비율",
    ),
    vertical_spacing=0.14, horizontal_spacing=0.09,
)

# ① 정렬된 분포 (평균으로 정규화 → 스케일 무관 비교)
for name, color in (("구조 있음", C_STRUCT), ("무작위(ER)", C_RANDOM)):
    v = sorted_vals(EXACT[name])
    mean = sum(v) / len(v)
    fig.add_trace(go.Scatter(
        x=list(range(1, len(v) + 1)), y=[max(x / mean, 1e-4) for x in v],
        mode="lines", name=name, legendgroup=name,
        line=dict(color=color, width=2.5)), row=1, col=1)
fig.add_vline(x=TOPK, line=dict(color="#64748b", width=1, dash="dot"), row=1, col=1)
fig.add_annotation(x=1.36, y=1.75, xref="x", yref="y", text="상위 20 커트라인",
                   showarrow=False, xanchor="left",
                   font=dict(size=11, color="#64748b"), row=1, col=1)

# ② 표본율별 일치율
for i, (name, color) in enumerate((("구조 있음", C_STRUCT), ("무작위(ER)", C_RANDOM))):
    xs = [f"{int(r*100)}%" for r in RATES]
    ys, errs = [], []
    for r in RATES:
        ov = RESULT[name][r]
        m = sum(ov) / len(ov)
        ys.append(m * 100)
        errs.append(((sum((x - m) ** 2 for x in ov) / len(ov)) ** 0.5) * 100)
    fig.add_trace(go.Bar(
        x=xs, y=ys, name=name, legendgroup=name, showlegend=False,
        marker_color=color, opacity=0.9,
        error_y=dict(type="data", array=errs, color="#334155", thickness=1.2, width=6),
        ), row=1, col=2)
    # 값 라벨은 오차막대 위에 직접 찍는다. 묶음 막대라 xshift 로 각 막대 중앙에 맞춘다.
    for x, y, e in zip(xs, ys, errs):
        fig.add_annotation(x=x, y=y + e, xref="x2", yref="y2", text=f"{y:.0f}%",
                           showarrow=False, yanchor="bottom", yshift=9,
                           xshift=-24 if i == 0 else 24,
                           font=dict(size=11, color=color), row=1, col=2)
fig.add_hline(y=TOPK / N * 100, line=dict(color="#94a3b8", width=1.5, dash="dash"), row=1, col=2)
fig.add_annotation(x=-0.47, y=101, xref="x2", yref="y2",
                   text="점선 = 완전 무작위로 20개 찍었을 때 기대치 2.5%",
                   showarrow=False, font=dict(size=10, color="#94a3b8"),
                   xanchor="left", row=1, col=2)

# ③ 커트라인 주변 ±1σ 밴드
WIN = 40
for name, color, fillc in (("구조 있음", C_STRUCT, "rgba(37,99,235,0.20)"),
                           ("무작위(ER)", C_RANDOM, "rgba(234,88,12,0.20)")):
    ex = EXACT[name]
    order = [v for v, _ in sorted(ex.items(), key=lambda x: (-x[1], x[0]))][:WIN]
    mean = sum(ex.values()) / len(ex)
    ests = EST_5PCT[name]
    mu = [sum(e[v] for e in ests) / len(ests) / mean for v in order]
    sd = [(sum((e[v] - sum(f[v] for f in ests) / len(ests)) ** 2 for e in ests) / len(ests)) ** 0.5 / mean
          for v in order]
    xs = list(range(1, WIN + 1))
    fig.add_trace(go.Scatter(
        x=xs + xs[::-1],
        y=[m + s for m, s in zip(mu, sd)] + [max(m - s, 1e-3) for m, s in zip(mu, sd)][::-1],
        fill="toself", fillcolor=fillc, line=dict(width=0), hoverinfo="skip",
        showlegend=False, legendgroup=name), row=2, col=1)
    fig.add_trace(go.Scatter(
        x=xs, y=[ex[v] / mean for v in order], mode="lines",
        line=dict(color=color, width=2.5), name=name, legendgroup=name,
        showlegend=False), row=2, col=1)
fig.add_vline(x=TOPK, line=dict(color="#64748b", width=1, dash="dot"), row=2, col=1)
fig.add_annotation(x=WIN, y=1.72, xref="x3", yref="y3", xanchor="right",
                   text="밴드(잡음)가 위아래 순위 간격보다 넓으면 순위가 뒤집힌다",
                   showarrow=False, font=dict(size=10, color="#64748b"), row=2, col=1)

# ④ 누적 점유율 (집중도)
for name, color in (("구조 있음", C_STRUCT), ("무작위(ER)", C_RANDOM)):
    v = sorted_vals(EXACT[name])
    total = sum(v)
    cum, acc = [], 0.0
    for x in v:
        acc += x
        cum.append(acc / total * 100)
    fig.add_trace(go.Scatter(
        x=[(i + 1) / len(v) * 100 for i in range(len(v))], y=cum, mode="lines",
        line=dict(color=color, width=2.5), name=name, legendgroup=name,
        showlegend=False), row=2, col=2)
fig.add_trace(go.Scatter(
    x=[0, 100], y=[0, 100], mode="lines", line=dict(color="#94a3b8", width=1.5, dash="dash"),
    name="완전 균등", showlegend=False), row=2, col=2)
fig.add_annotation(x=60, y=52, xref="x4", yref="y4", text="완전 균등선",
                   showarrow=False, font=dict(size=10, color="#94a3b8"), row=2, col=2)

fig.update_yaxes(type="log", dtick=1, title_text="매개 중심성 / 평균", row=1, col=1)
fig.update_xaxes(type="log", dtick=1, title_text="순위 (로그)", row=1, col=1)
fig.update_yaxes(title_text="상위 20 일치율 (%)", range=[0, 105], row=1, col=2)
fig.update_xaxes(title_text="표본율 (출발점 비율)", row=1, col=2)
fig.update_yaxes(type="log", dtick=1, title_text="매개 중심성 / 평균", row=2, col=1)
fig.update_xaxes(title_text=f"정확한 순위 (1~{WIN}위)", dtick=5, row=2, col=1)
fig.update_yaxes(title_text="누적 점유율 (%)", row=2, col=2)
fig.update_xaxes(title_text="상위 노드 비율 (%)", row=2, col=2)

fig.update_layout(
    title=dict(text="근사가 잘 듣는 그래프 vs 안 듣는 그래프 — 노드 800개, 엣지 2,273개로 동일",
               font=dict(size=19)),
    template="plotly_white", font=dict(family=KOR, size=12),
    width=1400, height=940, bargap=0.35,
    legend=dict(orientation="h", yanchor="bottom", y=1.045, xanchor="right", x=1),
    margin=dict(t=120, b=60, l=70, r=40),
)
for a in fig.layout.annotations[:4]:
    a.font.size = 13

fig.write_image("expy.png", scale=2)
print("expy.png 저장 완료")
_show(fig)
# 출력:
# expy.png 저장 완료


# %% [markdown]
# ## 정리
#
# - **근사의 성패는 알고리즘이 아니라 값의 분포가 정한다.** 같은 노드 수, 같은 엣지 수인데
#   배치만 바뀌어도 5% 표본 일치율이 82% ↔ 34%로 갈린다.
# - **표본을 늘리면 잡음은 $1/\sqrt{k}$로 줄지만 신호는 안 는다.** 평평한 그래프에서
#   표본율을 20배 늘려도 58.5%에서 멈추는 이유다.
# - **실무 사전 점검**은 5% 표본 한 번으로 끝난다. 상위/중앙값 비율 $\ge 50$ 이고
#   커트라인 간극 $\ge 0.2$면 초록. 애매하면 표본율을 두 배로 늘려 상위 $k$가 유지되는지만 보면 된다.
# - **다행히 실제 그래프는 대개 구조가 있다.** 조직도, 소셜 그래프, 인프라 토폴로지, 지식 그래프에는
#   다리와 급소가 실재한다. 그래서 에셋 마지막 줄이 「근사가 잘 듣는 건 진짜 급소가 있는
#   그래프에서다. 그리고 대개 그렇다」로 끝난다. 다만 «대개»를 «항상»으로 읽지는 말 것.
