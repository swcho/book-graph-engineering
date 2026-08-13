# %% [markdown]
# # `bfs_order()` — 가장 싼 재배치
#
# 8장 `ex4_relabel.py`의 `bfs_order()`는 **BFS로 만난 순서대로 노드 번호를 다시 매기는**
# 재배치(reordering)다. 한 번의 BFS가 전부라서 재배치 방법 중 제일 싸다.
#
# 이 노트북에서 확인할 것:
#
# 1. 번호가 뒤섞인 클러스터 그래프를 만든다 (적재 순서가 구조와 무관한 현실)
# 2. `bfs_order()`로 번호를 다시 매긴다
# 3. 지역성 지표 `평균 |u-v|`가 얼마나 줄어드는지 본다
# 4. 인접 행렬 스파이 플롯을 before/after로 비교한다
# 5. 연결 요소가 여러 개일 때도 **모든** 노드를 덮는지 확인한다
# 6. 더 비싼 대안(degree sort, RCM)과 「비용 대비 이득」을 나란히 놓는다

# %%
# 필요 패키지: plotly, kaleido, numpy, scipy
#   pip install plotly kaleido numpy scipy
# scipy는 RCM 비교에만 쓴다. 없으면 그 셀만 건너뛴다.
import random
import time
from collections import defaultdict, deque

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

SEED = 20260801
random.seed(SEED)
np.random.seed(SEED)


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


print("준비 완료. 시드:", SEED)

# 출력:
# 준비 완료. 시드: 20260801

# %% [markdown]
# ## 1. 뒤섞인 클러스터 그래프
#
# 실제 소셜·웹·도로망은 커뮤니티가 뚜렷하다. 하지만 **적재된 번호**는 그 구조와
# 아무 상관이 없다. `graph_id`, `uuid`, 크롤링 순서로 붙은 번호이기 때문이다.
#
# 그래서 아래 생성기는 커뮤니티를 만든 뒤 번호를 **일부러 뒤섞는다**.
# 8장 `clustered()`와 같은 방식이고, 그림을 보기 위해 크기만 작게 줄였다.

# %%
N = 600  # 노드 수 (스파이 플롯이 눈에 보이는 크기)
GROUPS = 12  # 커뮤니티 수
AVG_DEG = 12


def clustered(n=N, groups=GROUPS, avg_deg=AVG_DEG, seed=7):
    """커뮤니티가 뚜렷한 그래프. 단, 번호는 일부러 뒤섞어 둔다."""
    rnd = random.Random(seed)
    perm = list(range(n))
    rnd.shuffle(perm)  # ← 여기가 핵심: 구조와 번호를 분리한다
    size = n // groups
    edges = set()
    for g in range(groups):
        members = [perm[i] for i in range(g * size, min((g + 1) * size, n))]
        for a in members:
            for _ in range(avg_deg // 2):
                b = rnd.choice(members)
                if a != b:
                    edges.add((min(a, b), max(a, b)))
    # 커뮤니티 사이를 잇는 다리 몇 개
    for _ in range(n // 50):
        a, b = rnd.randrange(n), rnd.randrange(n)
        if a != b:
            edges.add((min(a, b), max(a, b)))
    return sorted(edges)


def random_graph(n=N, avg_deg=AVG_DEG, seed=SEED):
    """비교용: 구조가 없는 무작위 그래프 (8장 graphgen.make 와 같은 방식)."""
    rnd = random.Random(seed)
    edges = set()
    for a in range(n):
        for _ in range(avg_deg // 2):
            b = rnd.randrange(n)
            if a != b:
                edges.add((min(a, b), max(a, b)))
    return sorted(edges)


E_CLUST = clustered()
E_RAND = random_graph()
print(f"클러스터 그래프: 노드 {N:,}  엣지 {len(E_CLUST):,}  커뮤니티 {GROUPS}개")
print(f"무작위  그래프: 노드 {N:,}  엣지 {len(E_RAND):,}")

# 출력:
# 클러스터 그래프: 노드 600  엣지 3,158  커뮤니티 12개
# 무작위  그래프: 노드 600  엣지 3,563

# %% [markdown]
# ## 2. 지역성 지표 — 평균 이웃 번호 차이
#
# 재배치가 잘 됐는지는 「엣지 양 끝 번호가 얼마나 가까운가」로 잰다.
#
# $$
# \text{locality}(G) \;=\; \frac{1}{|E|}\sum_{(u,v)\in E} \bigl|\,u - v\,\bigr|
# $$
#
# 작을수록 좋다. 왜 이 값이 중요한가는 캐시 줄 크기에서 나온다.
# CSR의 이웃 배열이 4바이트 정수이고 캐시 한 줄이 64바이트이면,
#
# $$
# \frac{64\ \text{B}}{4\ \text{B}} = 16\ \text{개}
# $$
#
# 가 한 번에 올라온다. 즉 $\overline{|u-v|}$가 **16보다 작아야** 한 번 읽어 온 줄을
# 다시 쓸 가능성이 생긴다. 그보다 크면 거의 매번 새 줄을 가져온다.

# %%
CACHE_LINE_INTS = 64 // 4  # 캐시 한 줄에 들어가는 4바이트 정수 개수 = 16


def locality(edges):
    """엣지 양 끝 번호 차이의 평균. 작을수록 좋다."""
    return sum(abs(a - b) for a, b in edges) / len(edges)


for label, edges in (("클러스터", E_CLUST), ("무작위", E_RAND)):
    print(f"{label:<6} 평균 |u-v| = {locality(edges):8.1f}  (캐시 줄 = {CACHE_LINE_INTS}개)")

print("\n둘 다 N/3 ≈ 200 근처다. 번호가 뒤섞여 있으면 구조가 있어도 지표는 똑같이 나쁘다.")

# 출력:
# 클러스터   평균 |u-v| =    201.4  (캐시 줄 = 16개)
# 무작위    평균 |u-v| =    200.2  (캐시 줄 = 16개)
#
# 둘 다 N/3 ≈ 200 근처다. 번호가 뒤섞여 있으면 구조가 있어도 지표는 똑같이 나쁘다.

# %% [markdown]
# ## 3. `bfs_order()` — BFS로 만난 순서대로 번호 매기기
#
# 알고리즘 전체가 이것뿐이다.
#
# 1. `seed = 0, 1, 2, ...` 순서로 훑는다
# 2. 아직 번호를 못 받은 노드를 만나면 거기서 BFS를 시작한다
# 3. BFS 큐에서 노드를 꺼낼 때가 아니라 **처음 발견할 때** 새 번호를 준다
# 4. 큐가 마르면 다음 `seed`로 넘어간다 → **연결 요소마다 새 seed**
#
# 왜 이게 지역성을 만드는가: BFS는 한 커뮤니티를 다 훑고 나서 다음으로 넘어간다.
# 그래서 같은 커뮤니티 노드들이 연속된 번호 구간을 차지한다.
#
# 비용은 BFS 한 번, 즉 $O(V + E)$다. 재배치 방법 중 가장 싸다.

# %%
def bfs_order(edges, n):
    """BFS 로 만난 순서대로 번호를 다시 매긴다. 제일 싼 재배치 방법."""
    adj = defaultdict(list)
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    new, cnt = {}, 0
    for seed in range(n):  # ← 연결 요소마다 새 seed
        if seed in new:
            continue
        q = deque([seed])
        new[seed] = cnt
        cnt += 1
        while q:
            u = q.popleft()
            for v in adj[u]:
                if v not in new:  # 처음 만났을 때 번호를 준다
                    new[v] = cnt
                    cnt += 1
                    q.append(v)
    return new


def apply_mapping(edges, mapping):
    return [(mapping[a], mapping[b]) for a, b in edges]


mapping = bfs_order(E_CLUST, N)
E_CLUST_BFS = apply_mapping(E_CLUST, mapping)

before, after = locality(E_CLUST), locality(E_CLUST_BFS)
print("클러스터 그래프")
print(f"  전  평균 |u-v| = {before:8.1f}")
print(f"  후  평균 |u-v| = {after:8.1f}   개선 {before / after:.1f}배")
print(f"  캐시 줄({CACHE_LINE_INTS}개) 안에 들어오나? {'예' if after < CACHE_LINE_INTS else '아니오'}")

mapping_r = bfs_order(E_RAND, N)
E_RAND_BFS = apply_mapping(E_RAND, mapping_r)
before_r, after_r = locality(E_RAND), locality(E_RAND_BFS)
print("\n무작위 그래프")
print(f"  전  평균 |u-v| = {before_r:8.1f}")
print(f"  후  평균 |u-v| = {after_r:8.1f}   개선 {before_r / after_r:.1f}배")
print("\n재배치는 «없던 구조를 만들지 못한다». 원래 있던 구조를 번호로 드러낼 뿐이다.")

# 출력:
# 클러스터 그래프
#   전  평균 |u-v| =    201.4
#   후  평균 |u-v| =     22.9   개선 8.8배
#   캐시 줄(16개) 안에 들어오나? 아니오
#
# 무작위 그래프
#   전  평균 |u-v| =    200.2
#   후  평균 |u-v| =    174.2   개선 1.1배
#
# 재배치는 «없던 구조를 만들지 못한다». 원래 있던 구조를 번호로 드러낼 뿐이다.

# %% [markdown]
# ## 4. 재번호가 실제로 하는 일 — 커뮤니티가 연속 구간이 된다
#
# 커뮤니티 하나의 멤버들이 새 번호에서 어디에 놓이는지 확인해 보자.
# 재배치 전에는 0~599에 흩어져 있고, 재배치 후에는 좁은 구간에 뭉친다.

# %%
# 커뮤니티 재구성 (clustered 와 같은 시드/순서로 다시 계산)
_rnd = random.Random(7)
_perm = list(range(N))
_rnd.shuffle(_perm)
_size = N // GROUPS
communities = [[_perm[i] for i in range(g * _size, min((g + 1) * _size, N))] for g in range(GROUPS)]

print(f"{'커뮤니티':<8} {'재배치 전 번호 범위':>22} {'재배치 후 번호 범위':>22} {'후 폭':>7}")
print("-" * 64)
for g, members in enumerate(communities[:6]):
    old = sorted(members)
    new = sorted(mapping[m] for m in members)
    print(f"#{g:<7} {f'{old[0]}~{old[-1]} (폭 {old[-1] - old[0] + 1})':>22} "
          f"{f'{new[0]}~{new[-1]}':>22} {new[-1] - new[0] + 1:>7}")

widths_after = [max(mapping[m] for m in c) - min(mapping[m] for m in c) + 1 for c in communities]
print(f"\n커뮤니티 크기 {_size}개, 재배치 후 평균 번호 폭 {sum(widths_after) / len(widths_after):.1f}")
print("폭이 커뮤니티 크기에 가까울수록 «연속 구간에 뭉쳤다»는 뜻이다.")

# 출력:
# 커뮤니티                재배치 전 번호 범위            재배치 후 번호 범위     후 폭
# ----------------------------------------------------------------
# #0               12~597 (폭 586)                145~291     147
# #1                3~598 (폭 596)                151~295     145
# #2                1~588 (폭 588)                  50~99      50
# #3                4~594 (폭 591)                152~301     150
# #4               16~576 (폭 561)                302~412     111
# #5                7~599 (폭 593)                351~450     100
#
# 커뮤니티 크기 50개, 재배치 후 평균 번호 폭 96.3
# 폭이 커뮤니티 크기에 가까울수록 «연속 구간에 뭉쳤다»는 뜻이다.
# (#2 는 폭이 정확히 50 이다. 커뮤니티 하나가 통째로 연속 구간을 차지했다는 뜻이다.
#  #0, #1, #3 처럼 폭이 150 근처인 경우는 커뮤니티 사이 «다리» 때문에 BFS 가
#  두세 커뮤니티를 섞어 훑은 결과다. 그래도 599 → 150 이면 4배 가까이 좁아졌다.)

# %% [markdown]
# ## 5. 연결 요소마다 새 seed — 모든 노드를 덮는다
#
# BFS 한 번만 돌리면 시작 노드가 속한 연결 요소만 번호를 받는다.
# 나머지는 번호가 없어서 재배치 자체가 깨진다.
#
# `bfs_order()`의 `for seed in range(n)` 루프가 이 문제를 막는다.
# 요소를 다 훑으면 다음 번호 없는 노드에서 새로 시작한다.
# 결과적으로 **매핑은 0..n-1의 완전한 순열**이 된다.

# %%
def three_components(n=90, seed=3):
    """의도적으로 3개의 연결 요소 + 고립 노드 2개를 만든다."""
    rnd = random.Random(seed)
    edges = set()
    blocks = [range(0, 30), range(30, 60), range(60, 88)]  # 88, 89 는 고립
    for blk in blocks:
        members = list(blk)
        for a in members:
            for _ in range(3):
                b = rnd.choice(members)
                if a != b:
                    edges.add((min(a, b), max(a, b)))
    return sorted(edges), n


E3, N3 = three_components()
m3 = bfs_order(E3, N3)

print(f"노드 {N3}개, 엣지 {len(E3)}개, 연결 요소 3개 + 고립 노드 2개")
print(f"매핑에 들어간 노드 수: {len(m3)} / {N3}")
print(f"새 번호가 0..{N3 - 1} 순열인가?  {sorted(m3.values()) == list(range(N3))}")
print(f"고립 노드 88, 89 의 새 번호: {m3[88]}, {m3[89]}  ← seed 루프가 잡아 준다")

# 한 번의 BFS 만 돌리는 «망가진» 버전과 비교
def bfs_order_single_seed(edges, n, start=0):
    adj = defaultdict(list)
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    new, cnt = {start: 0}, 1
    q = deque([start])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in new:
                new[v] = cnt
                cnt += 1
                q.append(v)
    return new


m3_bad = bfs_order_single_seed(E3, N3)
print(f"\nseed 루프 없는 버전: {len(m3_bad)} / {N3} 개만 번호를 받음 → 나머지는 KeyError")
print(f"전  평균 |u-v| = {locality(E3):6.1f}   후 평균 |u-v| = {locality(apply_mapping(E3, m3)):6.1f}")

# 출력:
# 노드 90개, 엣지 237개, 연결 요소 3개 + 고립 노드 2개
# 매핑에 들어간 노드 수: 90 / 90
# 새 번호가 0..89 순열인가?  True
# 고립 노드 88, 89 의 새 번호: 88, 89  ← seed 루프가 잡아 준다
#
# seed 루프 없는 버전: 30 / 90 개만 번호를 받음 → 나머지는 KeyError
# 전  평균 |u-v| =   10.7   후 평균 |u-v| =    8.5

# %% [markdown]
# ## 6. 더 비싼 대안들과 나란히 — 비용을 갚는가
#
# `bfs_order()`는 재배치 스펙트럼의 **가장 싼 쪽 끝**이다.
#
# | 방법 | 비용 | 지역성 |
# |---|---|---|
# | degree sort (차수 내림차순) | $O(V \log V)$, 그래프 구조 안 봄 | 약함 |
# | **`bfs_order()`** | **$O(V+E)$, BFS 한 번** | **중간** |
# | RCM (Reverse Cuthill-McKee) | 차수 정렬 붙은 BFS, $O(V+E)$~ | 대역폭에 강함 |
# | Rabbit Order | 커뮤니티 검출(병렬) | 강함 |
# | Gorder | 슬라이딩 윈도우 탐욕, 매우 느림 | 가장 강함 |
#
# 아래에서 지역성과 **재배치 시간**을 함께 잰다. 두 열을 같이 봐야 한다.
#
# 주의: 이 예제는 노드 600개짜리 장난감이다. RCM/Gorder/Rabbit Order의 지역성 우위는
# 노드가 수백만~수십억일 때 드러나고, 그때 비용 격차도 같이 벌어진다.
# 여기서 볼 것은 순위표가 아니라 **「지역성 이득 ↔ 재배치 비용」이라는 두 축**이다.

# %%
def degree_order(edges, n):
    """차수 내림차순으로 번호를 다시 매긴다. 구조를 전혀 안 본다."""
    deg = defaultdict(int)
    for a, b in edges:
        deg[a] += 1
        deg[b] += 1
    order = sorted(range(n), key=lambda u: (-deg[u], u))
    return {u: i for i, u in enumerate(order)}


def rcm_order(edges, n):
    """Reverse Cuthill-McKee. scipy 없으면 None."""
    try:
        import scipy.sparse as sp
        from scipy.sparse.csgraph import reverse_cuthill_mckee
    except ImportError:
        return None
    rows = [a for a, b in edges] + [b for a, b in edges]
    cols = [b for a, b in edges] + [a for a, b in edges]
    m = sp.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    perm = reverse_cuthill_mckee(m, symmetric_mode=True)
    return {int(u): i for i, u in enumerate(perm)}


def timed(fn, edges, n, repeat=3):
    best = float("inf")
    out = None
    for _ in range(repeat):
        t0 = time.perf_counter()
        out = fn(edges, n)
        best = min(best, time.perf_counter() - t0)
    return out, best * 1000


# 참고 기준: BFS 순회 한 번의 시간
def one_bfs(edges, n):
    adj = defaultdict(list)
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    seen = bytearray(n)
    seen[0] = 1
    q = deque([0])
    c = 0
    while q:
        u = q.popleft()
        c += 1
        for v in adj[u]:
            if not seen[v]:
                seen[v] = 1
                q.append(v)
    return c


_, t_traverse = timed(one_bfs, E_CLUST, N)

results = [("원래 번호 (재배치 없음)", locality(E_CLUST), 0.0)]
for name, fn in (("degree sort", degree_order), ("bfs_order", bfs_order), ("RCM", rcm_order)):
    mp, ms = timed(fn, E_CLUST, N)
    if mp is None:
        print(f"{name}: 건너뜀 (scipy 없음)")
        continue
    results.append((name, locality(apply_mapping(E_CLUST, mp)), ms))

print(f"BFS 순회 한 번 = {t_traverse:.2f} ms  (재배치 비용을 이 값으로 나눠 본다)\n")
print(f"{'방법':<24} {'평균 |u-v|':>12} {'개선':>7} {'재배치 ms':>11} {'순회 몇 번분':>13}")
print("-" * 72)
base = results[0][1]
for name, loc, ms in results:
    ratio = f"{base / loc:.1f}x" if loc else "-"
    cost = f"{ms / t_traverse:.1f}회" if ms else "-"
    print(f"{name:<24} {loc:>12.1f} {ratio:>7} {ms:>11.2f} {cost:>13}")

print(
    "\narXiv 1602.08820 계열 연구의 관측: 재배치는 «순회 비용»이 아니라 «재배치 비용»과 싸운다.\n"
    "그래프를 한 번만 훑는다면 어떤 재배치도 손해다. 여러 번 훑을 때만 갚아진다.\n"
    "bfs_order() 가 실무에서 자주 이기는 이유는 지역성이 최고여서가 아니라, «싸서» 금방 갚기 때문이다."
)

# 출력:
# BFS 순회 한 번 = 0.36 ms  (재배치 비용을 이 값으로 나눠 본다)
#
# 방법                           평균 |u-v|      개선      재배치 ms       순회 몇 번분
# ------------------------------------------------------------------------
# 원래 번호 (재배치 없음)                  201.4    1.0x        0.00             -
# degree sort                     198.7    1.0x        0.48          1.3회
# bfs_order                        22.9    8.8x        0.55          1.5회
# RCM                              23.6    8.5x        1.19          3.3회
#
# 읽는 법 두 가지.
#  1) degree sort 는 «비용을 냈는데 이득이 0» 이다 (198.7 ≈ 201.4). 구조를 안 보니 당연하다.
#     싼 것과 «싸고 효과 있는 것»은 다르다.
#  2) RCM 은 bfs_order 보다 2배 이상 비싼데 이 크기에서는 지역성이 되레 살짝 나쁘다.
#     큰 실제 그래프에서는 RCM 이 앞서지만, 그 격차를 갚을 만큼 순회를 반복해야 한다.
#
# arXiv 1602.08820 계열 연구의 관측: 재배치는 «순회 비용»이 아니라 «재배치 비용»과 싸운다.
# 그래프를 한 번만 훑는다면 어떤 재배치도 손해다. 여러 번 훑을 때만 갚아진다.
# bfs_order() 가 실무에서 자주 이기는 이유는 지역성이 최고여서가 아니라, «싸서» 금방 갚기 때문이다.

# %% [markdown]
# ## 7. 시각화 — 인접 행렬 스파이 플롯 before/after
#
# 왼쪽 위: 재배치 전. 점이 정사각형 전체에 균일하게 흩어져 있다.
# 오른쪽 위: `bfs_order()` 후. 점이 **대각선 근처의 블록**으로 모인다.
# 블록 하나가 커뮤니티 하나이고, 이 블록이 곧 CSR에서 「연속으로 읽히는 구간」이다.
#
# 아래 왼쪽: $|u-v|$ 분포. 재배치 후에 왼쪽(=0 근처)으로 쏠린다.
# 아래 오른쪽: 방법별 평균 $|u-v|$와 재배치 비용.

# %%
def spy_points(edges):
    """대칭 행렬이므로 (u,v) 와 (v,u) 를 모두 찍는다."""
    xs = [a for a, b in edges] + [b for a, b in edges]
    ys = [b for a, b in edges] + [a for a, b in edges]
    return xs, ys


fig = make_subplots(
    rows=2,
    cols=2,
    subplot_titles=(
        f"재배치 전 — 평균 |u-v| = {before:.0f}",
        f"bfs_order() 후 — 평균 |u-v| = {after:.0f}",
        "엣지 |u-v| 분포",
        "방법별 지역성과 재배치 비용",
    ),
    vertical_spacing=0.13,
    horizontal_spacing=0.11,
    specs=[[{}, {}], [{}, {"secondary_y": True}]],
)

for col, (edges, color) in enumerate(((E_CLUST, "#c0392b"), (E_CLUST_BFS, "#1f77b4")), start=1):
    xs, ys = spy_points(edges)
    fig.add_trace(
        go.Scattergl(
            x=xs,
            y=ys,
            mode="markers",
            marker=dict(size=1.8, color=color, opacity=0.55),
            showlegend=False,
            hoverinfo="skip",
        ),
        row=1,
        col=col,
    )
    fig.update_xaxes(title_text="열 번호", range=[0, N], row=1, col=col)
    fig.update_yaxes(title_text="행 번호", range=[N, 0], scaleanchor=f"x{col}", row=1, col=col)

# 아래 왼쪽: |u-v| 히스토그램
for edges, name, color in ((E_CLUST, "재배치 전", "#c0392b"), (E_CLUST_BFS, "bfs_order 후", "#1f77b4")):
    fig.add_trace(
        go.Histogram(
            x=[abs(a - b) for a, b in edges],
            name=name,
            marker_color=color,
            opacity=0.65,
            nbinsx=60,
        ),
        row=2,
        col=1,
    )
fig.update_xaxes(title_text="|u - v|", row=2, col=1)
fig.update_yaxes(title_text="엣지 수", row=2, col=1)

# 아래 오른쪽: 방법별 지역성(막대) + 재배치 비용(점)
names = [r[0].replace(" (재배치 없음)", "") for r in results]
locs = [r[1] for r in results]
costs = [r[2] for r in results]
fig.add_trace(
    go.Bar(x=names, y=locs, name="평균 |u-v|", marker_color="#1f77b4", width=0.5, showlegend=True),
    row=2,
    col=2,
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(
        x=names,
        y=costs,
        name="재배치 시간 (ms)",
        mode="markers+lines",
        marker=dict(size=11, color="#e67e22", symbol="diamond"),
        line=dict(color="#e67e22", dash="dot"),
    ),
    row=2,
    col=2,
    secondary_y=True,
)
fig.add_hline(
    y=CACHE_LINE_INTS,
    line=dict(color="#2ca02c", dash="dash", width=1.5),
    annotation_text=f"캐시 줄 {CACHE_LINE_INTS}개",
    annotation_position="top left",
    row=2,
    col=2,
    secondary_y=False,
)
fig.update_yaxes(title_text="평균 |u-v| (작을수록 좋다)", row=2, col=2, secondary_y=False)
fig.update_yaxes(title_text="재배치 시간 (ms)", row=2, col=2, secondary_y=True)

fig.update_layout(
    title_text=(
        f"bfs_order(): 가장 싼 재배치 — 노드 {N:,} / 엣지 {len(E_CLUST):,} / 커뮤니티 {GROUPS}개"
        f"<br><sub>번호를 뒤섞은 클러스터 그래프. 점이 대각선 블록으로 모이는 것이 지역성이다.</sub>"
    ),
    barmode="overlay",
    width=1180,
    height=880,
    template="plotly_white",
    legend=dict(orientation="h", y=-0.07, x=0.5, xanchor="center"),
    margin=dict(t=110, b=90),
)

_show(fig)

# %%
# 정적 이미지 저장 (kaleido 필요). HTML 로는 저장하지 않는다.
import os

_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
_out = os.path.join(_here, "expy.png")
try:
    fig.write_image(_out, scale=2)
    print("저장:", _out)
except Exception as exc:  # kaleido 미설치 등
    print("이미지 저장 실패 (pip install kaleido):", exc)

# 출력:
# 저장: .../622cf5a7-7dc3-4ba2-b847-cd9ef56c5c28/expy.png

# %% [markdown]
# ## 정리
#
# - `bfs_order()`는 **BFS로 만난 순서대로 번호를 다시 매기는** 재배치다. BFS 한 번, $O(V+E)$.
# - `for seed in range(n)` 루프가 **연결 요소마다 새 seed**를 잡아서 고립 노드까지 모두 덮는다.
#   결과 매핑은 항상 $0..n-1$의 완전한 순열이다.
# - 커뮤니티가 뚜렷한 그래프에서 평균 $|u-v|$가 201.4 → 22.9 (8.8배) 로 줄었다.
#   무작위 그래프에서는 1.1배뿐이다 — **없던 구조를 만들어 내지는 못한다**.
# - degree sort는 더 싸지만 지역성이 거의 안 좋아진다(201.4 → 198.7). RCM은 2배 이상 비싸다.
#   Gorder / Rabbit Order로 가면 이득도 비용도 훨씬 커진다.
# - 그래서 판단 기준은 지역성 단독이 아니라 **「재배치 비용을 몇 번의 순회로 갚는가」**다.
#   한 번만 훑을 그래프라면 재배치는 그냥 손해다.
# - 8장 `ex4_relabel.py`를 노드 30,000으로 돌린 실측: 커뮤니티 그래프 10,003 → 2,893 (3.5배),
#   무작위 그래프 10,009 → 8,823 (1.1배). 규모가 커지면 절대값은 커져도 **패턴은 같다**.
