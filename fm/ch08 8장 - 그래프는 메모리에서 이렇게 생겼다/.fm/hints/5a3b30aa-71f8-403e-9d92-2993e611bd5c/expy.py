# %% [markdown]
# # 지역성(locality)은 어떻게 측정하는가 — 엣지 양 끝 번호 차이의 평균
#
# 8장 `ex4_relabel.py`는 지역성을 딱 한 줄로 잰다.
#
# ```python
# def locality(edges):
#     """엣지 양 끝 번호 차이의 평균. 작을수록 좋다."""
#     return sum(abs(a - b) for a, b in edges) / len(edges)
# ```
#
# 수식으로 쓰면 엣지 집합 $E$에 대해
#
# $$L(G) \;=\; \frac{1}{|E|} \sum_{(u,v)\in E} \bigl| u - v \bigr|$$
#
# 이다. **작을수록 좋다.** 이유는 알고리즘이 아니라 캐시다. CSR의 이웃 배열은
# 4바이트 정수를 연속으로 놓고, 캐시 한 줄은 64바이트다. 즉
#
# $$\frac{64\ \text{byte}}{4\ \text{byte/int}} = 16\ \text{개}$$
#
# 가 **한 번에** 올라온다. 이웃 번호가 평균 16보다 가깝게 모여 있으면 한 번 읽어 온
# 줄을 여러 번 쓰고, 멀면 매번 새 줄을 가져온다.
#
# 이 노트북은 (1) 손으로 계산 → (2) 무작위·클러스터·재배치 후 비교 →
# (3) 분포와 캐시 줄 임계선 16 → (4) 이 지표의 **두 가지 한계** 순서로 간다.
#
# 필요 패키지: 계산은 표준 라이브러리만. 마지막 시각화 셀만 plotly, kaleido, numpy를 쓴다.

# %%
import os
import random
import statistics
from collections import defaultdict, deque


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _HERE = os.getcwd()

SEED = 20260801  # 난수 시드 고정
INTS_PER_LINE = 16  # 캐시 줄 64바이트 / 4바이트 정수


def locality(edges):
    """엣지 양 끝 번호 차이의 절댓값 평균. 8장 ex4_relabel.py 그대로."""
    return sum(abs(a - b) for a, b in edges) / len(edges)


# 손으로 확인할 만큼 작은 그래프. 노드 0~5.
TOY = [(0, 1), (1, 2), (2, 3), (0, 5), (3, 4)]
gaps = [abs(a - b) for a, b in TOY]
print("엣지      :", TOY)
print("|u-v|     :", gaps)
print(f"합 {sum(gaps)} / 엣지 {len(gaps)}개 = 평균 {locality(TOY):.2f}")
# 출력: 엣지      : [(0, 1), (1, 2), (2, 3), (0, 5), (3, 4)]
# 출력: |u-v|     : [1, 1, 1, 5, 1]
# 출력: 합 9 / 엣지 5개 = 평균 1.80

# %% [markdown]
# 평균 1.80. 엣지 다섯 개 중 넷이 「바로 옆 번호」라서 값이 작다.
# `(0, 5)` 하나가 5를 보태 평균을 1.0에서 1.8로 밀어 올렸다.
# **엣지 하나가 평균을 움직인다** — 나중에 볼 한계의 씨앗이다.
#
# 이제 노드 번호를 뒤섞어 보자. 그래프의 **구조는 그대로**인데 지표만 나빠져야 한다.
# 지역성은 그래프의 성질이 아니라 **번호 매김(labeling)의 성질**이기 때문이다.

# %%
perm = [3, 0, 5, 1, 4, 2]  # 노드 i를 perm[i]로 다시 번호 매김
toy_shuffled = [(perm[a], perm[b]) for a, b in TOY]
print("다시 번호 매긴 엣지:", toy_shuffled)
print("|u-v|             :", [abs(a - b) for a, b in toy_shuffled])
print(f"평균 {locality(TOY):.2f} -> {locality(toy_shuffled):.2f}")
print("차수 분포, 연결 구조, 엣지 개수는 하나도 바뀌지 않았다.")
# 출력: 다시 번호 매긴 엣지: [(3, 0), (0, 5), (5, 1), (3, 2), (1, 4)]
# 출력: |u-v|             : [3, 5, 4, 1, 3]
# 출력: 평균 1.80 -> 3.20
# 출력: 차수 분포, 연결 구조, 엣지 개수는 하나도 바뀌지 않았다.

# %% [markdown]
# ## 실제 크기에서 — 무작위 / 클러스터 / 재배치 후
#
# 8장 `graphgen.make()`와 `ex4_relabel.py`의 `clustered()`, `bfs_order()`를 가져온다.
#
# - **무작위 그래프**: 아무 두 노드나 잇는다. 원래 구조가 없다.
# - **클러스터 그래프**: 커뮤니티 60개가 뚜렷하지만 **번호를 일부러 뒤섞어** 둔다.
#   적재 순서가 구조와 무관한 현실을 흉내 낸 것이다.
# - **재배치 후**: BFS로 만난 순서대로 번호를 다시 매긴다. 제일 싼 재배치다.
#
# 여기에 하나 더 넣는다. **다리 없는 클러스터** — 커뮤니티를 잇는 엣지 400개를 뺀
# 그래프다. 뒤에서 「평균이 꼬리에 끌려간다」를 보일 때 이게 결정적인 대조군이 된다.

# %%
N = 20_000
AVG_DEG = 12
GROUPS = 60


def make(n=N, avg_deg=AVG_DEG, skew=False, seed=SEED):
    """8장 graphgen.make() — 무작위(또는 선호적 연결) 그래프."""
    rnd = random.Random(seed)
    edges = set()
    if not skew:
        for a in range(n):
            for _ in range(avg_deg // 2):
                b = rnd.randrange(n)
                if a != b:
                    edges.add((min(a, b), max(a, b)))
        return sorted(edges)
    targets = [0, 1, 2]
    for a in range(3, n):
        for _ in range(avg_deg // 2):
            b = rnd.choice(targets)
            if a != b:
                edges.add((min(a, b), max(a, b)))
                targets.append(b)
        targets.append(a)
    return sorted(edges)


def clustered(n=N, groups=GROUPS, avg_deg=AVG_DEG, seed=7, bridges=True):
    """커뮤니티가 뚜렷하되 번호는 뒤섞인 그래프. 8장 ex4_relabel.py 그대로.
    bridges=False 면 커뮤니티 사이 다리를 만들지 않는다(이 노트북에서 추가한 대조군)."""
    rnd = random.Random(seed)
    perm = list(range(n))
    rnd.shuffle(perm)
    size = n // groups
    edges = set()
    for g in range(groups):
        members = [perm[i] for i in range(g * size, min((g + 1) * size, n))]
        for a in members:
            for _ in range(avg_deg // 2):
                b = rnd.choice(members)
                if a != b:
                    edges.add((min(a, b), max(a, b)))
    if bridges:
        for _ in range(n // 50):  # 커뮤니티 사이를 잇는 다리 몇 개
            a, b = rnd.randrange(n), rnd.randrange(n)
            if a != b:
                edges.add((min(a, b), max(a, b)))
    return sorted(edges)


def bfs_order(edges, n):
    """BFS 로 만난 순서대로 번호를 다시 매긴다. 8장 ex4_relabel.py 그대로."""
    adj = defaultdict(list)
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    new, cnt = {}, 0
    for seed in range(n):
        if seed in new:
            continue
        q = deque([seed])
        new[seed] = cnt
        cnt += 1
        while q:
            u = q.popleft()
            for v in adj[u]:
                if v not in new:
                    new[v] = cnt
                    cnt += 1
                    q.append(v)
    return new


def relabel(edges, n=N):
    m = bfs_order(edges, n)
    return [(m[a], m[b]) for a, b in edges]


e_random = make()
e_cluster = clustered()
e_nobridge = clustered(bridges=False)

GRAPHS = [
    ("무작위", e_random),
    ("무작위 + 재배치", relabel(e_random)),
    ("클러스터(뒤섞임)", e_cluster),
    ("클러스터 + 재배치", relabel(e_cluster)),
    ("다리 없는 클러스터 + 재배치", relabel(e_nobridge)),
]
for label, e in GRAPHS:
    print(f"{label:<26} 엣지 {len(e):>7,}  평균 |u-v| = {locality(e):>9,.1f}")
# 출력: 무작위                       엣지 119,964  평균 |u-v| =   6,668.6
# 출력: 무작위 + 재배치                엣지 119,964  평균 |u-v| =   5,869.7
# 출력: 클러스터(뒤섞임)                엣지 117,953  평균 |u-v| =   6,672.9
# 출력: 클러스터 + 재배치               엣지 117,953  평균 |u-v| =   2,114.0
# 출력: 다리 없는 클러스터 + 재배치         엣지 117,553  평균 |u-v| =      98.1

# %% [markdown]
# 읽는 법.
#
# - **무작위**는 재배치해도 6,669 → 5,870, 겨우 1.1배다. 8장 결론 그대로다.
#   *구조가 없으면 재배치할 것도 없다.*
# - **클러스터**는 6,673 → 2,114, 3.2배 좋아졌다. 방향은 맞다.
# - 그런데 **다리 400개만 빼면** 같은 재배치가 98.1까지 내려간다. **68배**다.
#   커뮤니티 크기가 $20000/60 \approx 333$이니 그 안에 갇힌 셈이다.
#
# 전체 엣지의 0.34%(400/117,953)가 평균을 98에서 2,114로, 즉 **21배** 밀어 올렸다.
# 이게 뒤에서 볼 한계 1의 실제 증거다.
#
# 평균 옆에 **분포**를 놓아 보자.

# %%
def stats(edges):
    g = sorted(abs(a - b) for a, b in edges)
    n = len(g)
    same_line = sum(1 for a, b in edges if a // INTS_PER_LINE == b // INTS_PER_LINE)
    return {
        "평균": sum(g) / n,
        "중앙값": statistics.median(g),
        "p90": g[int(n * 0.90)],
        "p99": g[int(n * 0.99)],
        "최대": g[-1],
        "|u-v|<16": sum(1 for x in g if x < INTS_PER_LINE) / n,
        "같은 줄": same_line / n,
    }


COLS = ["평균", "중앙값", "p90", "p99", "최대", "|u-v|<16", "같은 줄"]
STATS = {label: stats(e) for label, e in GRAPHS}
print(f"{'그래프':<26}" + "".join(f"{c:>12}" for c in COLS))
print("-" * 110)
for label, _ in GRAPHS:
    s = STATS[label]
    cells = "".join(
        f"{s[c]:>11.1%}" if c in ("|u-v|<16", "같은 줄") else f"{s[c]:>12,.1f}"
        for c in COLS
    )
    print(f"{label:<26}{cells}")
# 출력: 그래프                                  평균         중앙값         p90         p99         최대    |u-v|<16       같은 줄
# 출력: --------------------------------------------------------------------------------------------------------------
# 출력: 무작위                            6,668.6     5,863.0    13,707.0    17,987.0    19,958.0        0.1%        0.1%
# 출력: 무작위 + 재배치                     5,869.7     5,311.0    11,843.0    14,181.0    14,304.0        0.2%        0.1%
# 출력: 클러스터(뒤섞임)                     6,672.9     5,856.0    13,704.0    18,024.0    19,947.0        0.2%        0.1%
# 출력: 클러스터 + 재배치                    2,114.0     1,579.0     5,828.0     6,442.0     6,525.0        7.4%        3.9%
# 출력: 다리 없는 클러스터 + 재배치               98.1        89.0       197.0       236.0       250.0        9.7%        4.8%

# %% [markdown]
# ## 한계 1 — 평균이라서 꼬리를 못 잡는다
#
# 마지막 두 줄을 나란히 보자.
#
# | | 평균 | 같은 캐시 줄 비율 |
# |---|---|---|
# | 클러스터 + 재배치 | 2,114.0 | 3.9% |
# | 다리 없는 클러스터 + 재배치 | 98.1 | 4.8% |
#
# 평균은 **21.5배** 차이 난다. 그런데 캐시가 실제로 신경 쓰는 「같은 줄 비율」은
# 3.9% 대 4.8%, **1.2배**다. 지표가 차이를 20배쯤 과장한 것이다.
# 원인은 다리 400개다. 이 엣지들은 $|u-v|$가 수천이라 평균에 어마어마하게 기여하지만,
# 어차피 캐시 미스 400번일 뿐이다.
#
# 반대 방향으로도 속는다. 엣지 수와 평균 $|u-v|$가 거의 같은 두 그래프를 손으로 짓자.
#
# - **A**: 모든 엣지가 $|u-v| = 20$. 고르게 조금씩 멀다.
# - **B**: 엣지 95%가 $|u-v| = 1$, 5%가 $|u-v| = 400$. 대부분 붙어 있고 소수가 아주 멀다.
#
# $$L_A = 20, \qquad L_B \approx 0.95 \times 1 + 0.05 \times 400 = 20.95$$
#
# 지표는 「B가 A보다 약간 나쁘다」고 말한다. 캐시는 정반대로 말한다.

# %%
M = 20_000


def synth_uniform(m=M, d=20, seed=SEED):
    rnd = random.Random(seed)
    return [(u, u + d) for u in (rnd.randrange(0, N - d) for _ in range(m))]


def synth_bimodal(m=M, near=1, far=400, p_far=0.05, seed=SEED):
    rnd = random.Random(seed)
    out = []
    for _ in range(m):
        d = far if rnd.random() < p_far else near
        u = rnd.randrange(0, N - d)
        out.append((u, u + d))
    return out


SYNTH = [("A: 전부 |u-v|=20", synth_uniform()), ("B: 95%는 1, 5%는 400", synth_bimodal())]
for label, e in SYNTH:
    s = stats(e)
    print(
        f"{label:<22} 평균 {s['평균']:>6.2f}  중앙값 {s['중앙값']:>6.1f}  "
        f"p99 {s['p99']:>6.1f}  같은 캐시 줄 {s['같은 줄']:>6.1%}"
    )
print("\n평균은 거의 같은데 같은 캐시 줄에 들어오는 비율은 자릿수로 다르다.")
# 출력: A: 전부 |u-v|=20       평균  20.00  중앙값   20.0  p99   20.0  같은 캐시 줄   0.0%
# 출력: B: 95%는 1, 5%는 400   평균  21.97  중앙값    1.0  p99  400.0  같은 캐시 줄  88.8%
# 출력:
# 출력: 평균은 거의 같은데 같은 캐시 줄에 들어오는 비율은 자릿수로 다르다.

# %% [markdown]
# A는 **모든** 엣지가 20 떨어져 있어서 같은 줄에 들어오는 경우가 아예 없다(0.0%).
# B는 열 중 아홉이 같은 줄에 들어온다(88.8%). 그런데 지표는 B를 더 나쁘게 채점했다.
#
# 평균은 **분포의 모양을 지운다.** 실무에서 쓸 만한 보완은 **중앙값, p90,
# 「같은 캐시 줄 비율」**을 같이 보는 것이다. 셋 다 엣지 한 번 훑기로 구할 수 있다.

# %%
# 꼬리가 평균을 얼마나 끌고 가는지 — 긴 엣지 상위 1%를 빼고 다시 재 본다.
for label, e in GRAPHS:
    g = sorted(abs(a - b) for a, b in e)
    cut = int(len(g) * 0.99)
    trimmed = sum(g[:cut]) / cut
    full = sum(g) / len(g)
    print(
        f"{label:<26} 전체 평균 {full:>9,.1f}  상위 1% 제외 {trimmed:>9,.1f}  "
        f"꼬리 기여 {1 - trimmed / full:>6.1%}"
    )
# 출력: 무작위                       전체 평균   6,668.6  상위 1% 제외   6,547.4  꼬리 기여   1.8%
# 출력: 무작위 + 재배치                전체 평균   5,869.7  상위 1% 제외   5,785.0  꼬리 기여   1.4%
# 출력: 클러스터(뒤섞임)                전체 평균   6,672.9  상위 1% 제외   6,551.6  꼬리 기여   1.8%
# 출력: 클러스터 + 재배치               전체 평균   2,114.0  상위 1% 제외   2,070.0  꼬리 기여   2.1%
# 출력: 다리 없는 클러스터 + 재배치         전체 평균      98.1  상위 1% 제외      96.7  꼬리 기여   1.5%

# %% [markdown]
# ## 한계 2 — 절댓값은 캐시 줄 경계와 무관하다
#
# 이 지표는 $|u-v|$가 작으면 「같은 줄」이라고 가정한다. 그런데 캐시 줄은
# **정렬된 경계**로 잘려 있다. 4바이트 정수 16개마다 새 줄이 시작된다.
# 어떤 노드 번호 $u$가 들어가는 줄은
#
# $$\text{line}(u) = \left\lfloor \frac{u}{16} \right\rfloor$$
#
# 이다. $|u-v| = 1$이어도 경계를 밟으면 **줄이 갈린다.**

# %%
for u, v in [(16, 17), (15, 16), (0, 15), (0, 16), (100, 101), (111, 112)]:
    same = u // INTS_PER_LINE == v // INTS_PER_LINE
    print(
        f"({u:>3}, {v:>3})  |u-v| = {abs(u - v):>2}  "
        f"줄 {u // INTS_PER_LINE} / {v // INTS_PER_LINE}  "
        f"{'같은 줄' if same else '줄 갈림 ← 지표는 구분 못 함'}"
    )
# 출력: ( 16,  17)  |u-v| =  1  줄 1 / 1  같은 줄
# 출력: ( 15,  16)  |u-v| =  1  줄 0 / 1  줄 갈림 ← 지표는 구분 못 함
# 출력: (  0,  15)  |u-v| = 15  줄 0 / 0  같은 줄
# 출력: (  0,  16)  |u-v| = 16  줄 0 / 1  줄 갈림 ← 지표는 구분 못 함
# 출력: (100, 101)  |u-v| =  1  줄 6 / 6  같은 줄
# 출력: (111, 112)  |u-v| =  1  줄 6 / 7  줄 갈림 ← 지표는 구분 못 함

# %% [markdown]
# $|u-v| = 1$인 두 쌍이 한쪽은 같은 줄, 한쪽은 갈렸다. $|u-v| = 15$는 같은 줄인데
# $|u-v| = 16$은 갈렸다. 절댓값만 보는 지표는 이 차이를 전혀 못 본다.
#
# $u$가 균일하다고 보면 거리 $d$인 엣지가 같은 줄에 들어올 확률은 정확히
#
# $$P(\text{same line} \mid d) = \max\!\left(0,\; \frac{16 - d}{16}\right)$$
#
# 다. $d = 1$이면 $15/16 = 93.75\%$, $d = 8$이면 절반, $d = 15$면 $1/16$,
# $d \ge 16$이면 **0**이다. 「$d < 16$이면 히트」라는 순진한 해석과는 꽤 다르다.

# %%
print(f"{'d':>3} {'이론 (16-d)/16':>16} {'실측':>10}")
rnd = random.Random(SEED)
TRIALS = 200_000
for d in (1, 2, 4, 8, 12, 15, 16, 20, 32):
    hit = 0
    for _ in range(TRIALS):
        u = rnd.randrange(N - d)
        if u // INTS_PER_LINE == (u + d) // INTS_PER_LINE:
            hit += 1
    theory = max(0.0, (INTS_PER_LINE - d) / INTS_PER_LINE)
    print(f"{d:>3} {theory:>15.2%} {hit / TRIALS:>10.2%}")
# 출력:   d     이론 (16-d)/16         실측
# 출력:   1          93.75%     93.73%
# 출력:   2          87.50%     87.44%
# 출력:   4          75.00%     75.12%
# 출력:   8          50.00%     50.19%
# 출력:  12          25.00%     25.12%
# 출력:  15           6.25%      6.23%
# 출력:  16           0.00%      0.00%
# 출력:  20           0.00%      0.00%
# 출력:  32           0.00%      0.00%

# %% [markdown]
# 실측이 이론과 맞는다. 여기서 나오는 실용적 결론이 하나 있다.
# 평균이 16 **아래로** 내려가야 비로소 「캐시 줄을 재사용한다」고 말할 수 있는 게 아니고,
# 16 아래에서도 히트율은 $d$에 따라 **선형으로** 떨어진다. 그리고 16 이상에서는
# 평균이 100이든 2,000이든 같은 줄 확률은 **똑같이 0**이다.
# 그래서 「6,669 → 2,114로 3.2배 개선」이라는 말은 캐시 히트 관점에서 거의 의미가 없다.

# %% [markdown]
# ## 시각화
#
# 네 칸으로 정리한다.
#
# 1. 그래프별 평균 $|u-v|$ (로그 축) — 재배치 효과와 임계선 16
# 2. $|u-v|$ 분포와 캐시 줄 임계선 16
# 3. 한계 1: 「평균」과 「같은 캐시 줄 비율」의 산점도. 지표가 충실하다면 점들이
#    단조 감소 곡선에 놓여야 한다. A와 B는 평균이 거의 같은데 y가 89%p 벌어지고,
#    2,114와 98은 평균이 21배 다른데 y는 거의 같다.
# 4. 한계 2: 거리 $d$일 때 같은 줄 확률 — 실제 vs 지표의 가정

# %%
try:
    import numpy as np
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    COLOR = {
        "무작위": "#cbd5e1",
        "무작위 + 재배치": "#94a3b8",
        "클러스터(뒤섞임)": "#f59e0b",
        "클러스터 + 재배치": "#2563eb",
        "다리 없는 클러스터 + 재배치": "#059669",
    }

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "① 평균 |u-v| (작을수록 좋다, 로그 축)",
            "② |u-v| 분포 — 점선이 캐시 줄 임계 16",
            "③ 한계 1: 평균이 같은 줄 비율을 정하지 못한다",
            "④ 한계 2: 거리 d 일 때 같은 캐시 줄 확률",
        ),
        horizontal_spacing=0.11,
        vertical_spacing=0.19,
    )

    # ① 평균 막대
    labels = [lb for lb, _ in GRAPHS]
    means = [STATS[lb]["평균"] for lb in labels]
    fig.add_trace(
        go.Bar(
            x=[lb.replace(" + ", "<br>+ ") for lb in labels],
            y=means,
            marker_color=[COLOR[lb] for lb in labels],
            text=[f"{m:,.0f}" for m in means],
            textposition="outside",
            showlegend=False,
        ),
        row=1,
        col=1,
    )
    fig.add_hline(
        y=INTS_PER_LINE,
        line=dict(color="#dc2626", dash="dot"),
        annotation_text="캐시 줄 16",
        annotation_position="bottom left",
        row=1,
        col=1,
    )

    # ② 분포 (로그 구간 히스토그램)
    bins = np.logspace(0, np.log10(N), 44)
    for lb in ("클러스터(뒤섞임)", "클러스터 + 재배치", "다리 없는 클러스터 + 재배치"):
        e = dict(GRAPHS)[lb]
        g = np.abs(np.array([a - b for a, b in e]))
        cnt, _ = np.histogram(g, bins=bins)
        fig.add_trace(
            go.Scatter(
                x=bins[:-1],
                y=cnt / cnt.sum(),
                mode="lines",
                name=lb,
                line=dict(color=COLOR[lb], width=2, shape="hv"),
                fill="tozeroy",
                opacity=0.35,
            ),
            row=1,
            col=2,
        )
    fig.add_vline(
        x=INTS_PER_LINE,
        line=dict(color="#dc2626", dash="dot"),
        annotation_text="16",
        annotation_position="top",
        row=1,
        col=2,
    )

    # ③ 한계 1 — 평균(x)이 같은 캐시 줄 비율(y)을 정하지 못한다
    s_synth = {lb: stats(e) for lb, e in SYNTH}
    pts = [
        ("무작위", "#cbd5e1", "top center"),
        ("클러스터 + 재배치", "#2563eb", "top center"),
        ("다리 없는 클러스터 + 재배치", "#059669", "top right"),
        (SYNTH[0][0], "#dc2626", "middle right"),
        (SYNTH[1][0], "#7c3aed", "top center"),
    ]
    lookup = {**STATS, **s_synth}
    fig.add_trace(
        go.Scatter(
            x=[lookup[lb]["평균"] for lb, _, _ in pts],
            y=[lookup[lb]["같은 줄"] * 100 for lb, _, _ in pts],
            mode="markers+text",
            marker=dict(size=16, color=[c for _, c, _ in pts], line=dict(width=1, color="#334155")),
            text=[
                f"{lb}<br>{lookup[lb]['평균']:,.0f} / {lookup[lb]['같은 줄']:.1%}"
                for lb, _, _ in pts
            ],
            textposition=[p for _, _, p in pts],
            textfont=dict(size=10),
            showlegend=False,
            cliponaxis=False,
        ),
        row=2,
        col=1,
    )
    # A -> B: 평균은 거의 같은데 y가 89%p 벌어진다
    fig.add_annotation(
        x=np.log10(s_synth[SYNTH[1][0]]["평균"]),
        y=s_synth[SYNTH[1][0]]["같은 줄"] * 100,
        ax=np.log10(s_synth[SYNTH[0][0]]["평균"]),
        ay=s_synth[SYNTH[0][0]]["같은 줄"] * 100,
        xref="x3",
        yref="y3",
        axref="x3",
        ayref="y3",
        showarrow=True,
        arrowhead=3,
        arrowwidth=2,
        arrowcolor="#dc2626",
        text="",
    )
    fig.add_annotation(
        x=np.log10(46),
        y=52,
        xref="x3",
        yref="y3",
        showarrow=False,
        xanchor="left",
        align="left",
        text="평균은 20 → 22 (거의 그대로)<br>같은 줄 비율은 0% → 89%<br><b>순위가 뒤집힌다</b>",
        font=dict(size=11, color="#dc2626"),
    )
    fig.add_vline(
        x=INTS_PER_LINE,
        line=dict(color="#dc2626", dash="dot"),
        row=2,
        col=1,
    )

    # ④ 한계 2 — P(same line | d)
    ds = np.arange(1, 33)
    fig.add_trace(
        go.Scatter(
            x=ds,
            y=[max(0.0, (INTS_PER_LINE - d) / INTS_PER_LINE) * 100 for d in ds],
            mode="lines+markers",
            name="실제: (16-d)/16",
            line=dict(color="#2563eb", width=2),
        ),
        row=2,
        col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=ds,
            y=[100.0 if d < INTS_PER_LINE else 0.0 for d in ds],
            mode="lines",
            name="지표의 가정: d<16 이면 히트",
            line=dict(color="#dc2626", width=2, dash="dash", shape="hv"),
        ),
        row=2,
        col=2,
    )

    LOG_N = float(np.log10(N))
    fig.update_yaxes(
        type="log", title_text="평균 |u-v|", range=[0.7, LOG_N + 0.35], row=1, col=1
    )
    fig.update_xaxes(
        type="log", title_text="|u-v| (로그)", range=[0, LOG_N], row=1, col=2
    )
    fig.update_yaxes(title_text="엣지 비율", row=1, col=2)
    fig.update_xaxes(
        type="log",
        title_text="평균 |u-v| (로그) — 지표가 말하는 값",
        range=[0.7, LOG_N + 0.35],
        row=2,
        col=1,
    )
    fig.update_yaxes(
        title_text="같은 캐시 줄 비율 (%)",
        range=[-16, 116],
        row=2,
        col=1,
    )
    fig.update_xaxes(title_text="거리 d = |u-v|", dtick=4, row=2, col=2)
    fig.update_yaxes(title_text="같은 줄 확률 (%)", range=[-5, 108], row=2, col=2)
    fig.update_layout(
        title_text="지역성 = 엣지 양 끝 번호 차이의 절댓값 평균 — 효과와 두 가지 한계",
        template="plotly_white",
        width=1340,
        height=820,
        margin=dict(t=90, b=120),
        legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"),
    )

    _show(fig)
    out = os.path.join(_HERE, "expy.png")
    fig.write_image(out, scale=2)
    print("expy.png 저장 완료:", out)
except ImportError as e:  # 필요 패키지: plotly, kaleido, numpy
    print("시각화 생략 (필요 패키지: plotly, kaleido, numpy):", e)
# 출력: expy.png 저장 완료: .../expy.png

# %% [markdown]
# ## 정리
#
# 1. 지역성 = $\dfrac{1}{|E|}\sum_{(u,v)\in E}|u-v|$. **엣지 양 끝 노드 번호 차이의
#    절댓값 평균**이다. 작을수록 한 번 읽어 온 캐시 줄을 여러 번 쓴다.
# 2. 기준선은 **16**이다. 캐시 줄 64바이트 ÷ 4바이트 정수 = 16개가 한 번에 올라온다.
# 3. 이 값은 그래프의 성질이 아니라 **번호 매김의 성질**이다. 구조를 안 건드리고 번호만
#    바꿔도 값이 바뀐다. 그래서 BFS 순서로 재배치하면 클러스터 그래프에서 값이 준다.
# 4. 무작위 그래프에서는 재배치해도 6,669 → 5,870, 1.1배뿐이다. **없는 구조는 못 살린다.**
# 5. **한계 1 — 평균이라 꼬리를 못 잡는다.** 다리 400개(전체의 0.34%)가 평균을 98 →
#    2,114로 21배 밀어 올리는데, 정작 같은 캐시 줄 비율은 4.8% → 3.9%로 1.2배만 변한다.
#    합성 A/B에서는 순위가 아예 뒤집힌다. 중앙값·p90·「같은 줄 비율」을 함께 봐야 한다.
# 6. **한계 2 — 절댓값은 캐시 줄 경계와 무관하다.** 줄은 16 배수마다 정렬돼 잘리므로
#    $|u-v|=1$도 경계를 밟으면 갈린다. 실제 확률은 $\max(0,(16-d)/16)$이라 16 아래에서도
#    선형으로 떨어지고, 16 이상에서는 평균이 100이든 2,000이든 **똑같이 0**이다.
# 7. 그래도 이 지표를 쓰는 이유는 **싸고 방향이 맞기** 때문이다. 엣지를 한 번 훑으면
#    끝이고, 재배치 전후 **배수**를 비교하는 용도로는 충분히 쓸 만하다.
#    절대 수치를 캐시 미스율로 읽지만 않으면 된다.
