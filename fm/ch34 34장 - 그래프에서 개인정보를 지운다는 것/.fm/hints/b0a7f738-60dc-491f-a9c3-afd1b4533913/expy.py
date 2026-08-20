# %% [markdown]
# # 관계 자체가 식별자다 — 구조적 재식별 실험
#
# **질문**: 그래프 익명화에서 속성보다 더 어려운 문제는 무엇인가?
#
# **답**: 관계 자체가 식별자라는 점이다. 속성을 다 지워도 이웃 모양이 유일하면
# 특정되며, 아직 제대로 된 해법이 없다.
#
# 이 노트북은 그 주장을 숫자로 확인한다.
#
# 1. 작은 그래프에서 **속성을 전부 제거**한다. 이름도, 팀도, 지역도 없다.
# 2. 그 상태에서 (a) 차수, (b) 이웃 차수 다중집합, (c) 1-hop/2-hop 이웃 구조로
#    노드가 **몇 개나 유일해지는지** 센다.
# 3. `k-degree` 익명화처럼 **엣지를 추가**해 유일성을 줄이고, 그 대가로
#    그래프 통계가 얼마나 **왜곡되는지** 수치로 본다.
#
# 34장 예제 `ex3_reidentify.py` 가 속성 조합(k-익명성)을 셌다면,
# 이 노트북은 그 마지막 문단 — "그런데 그래프에서는 하나 더 있다" — 를 잇는다.

# %%
# 필요 패키지: networkx, plotly, kaleido (expy.png 저장용)
#   pip install networkx plotly kaleido
# 확인 환경: Python 3.9.6 / networkx 3.2.1 / plotly 6.8.0

import random
from collections import Counter

import networkx as nx

SEED = 34
rng = random.Random(SEED)


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# dataviz 기준 팔레트 (light) — 카테고리 슬롯 1~3
C_BLUE, C_ORANGE, C_AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
SURFACE = "#fcfcfb"

print("seed =", SEED)
# 출력: seed = 34


# %% [markdown]
# ## 1. 실험용 그래프 — 속성을 전부 지운 상태
#
# 사내 협업 그래프를 흉내 낸 소규모 소셜 그래프를 쓴다.
# 실제 소셜 그래프처럼 차수가 한쪽으로 쏠려 있어야(허브가 있어야) 의미가 있으므로
# Barabási–Albert 선호적 연결 모델을 쓴다.
#
# 중요한 것은 **노드에 아무 속성도 붙이지 않는다**는 점이다.
# 이름, 팀, 지역, 입사연도, 생월 — 34장 예제 3에서 재식별에 쓰였던 속성들을
# 전부 지웠다고 가정한다. 남은 것은 `n0, n1, ...` 같은 무의미한 대체 키와
# **엣지**뿐이다.

# %%
N = 40
G = nx.barabasi_albert_graph(N, 2, seed=SEED)
G = nx.relabel_nodes(G, {i: "n%d" % i for i in G.nodes()})

# 속성은 하나도 없다. 확인해 둔다.
assert all(len(G.nodes[v]) == 0 for v in G.nodes)

print("노드 %d개, 엣지 %d개" % (G.number_of_nodes(), G.number_of_edges()))
print("차수 범위 %d ~ %d" % (min(dict(G.degree()).values()),
                            max(dict(G.degree()).values())))
print("노드 속성 개수:", sum(len(G.nodes[v]) for v in G.nodes))
print("샘플 노드 5개:", list(G.nodes)[:5])
# 출력:
# 노드 40개, 엣지 76개
# 차수 범위 2 ~ 11
# 노드 속성 개수: 0
# 샘플 노드 5개: ['n0', 'n1', 'n2', 'n3', 'n4']


# %% [markdown]
# ## 2. 구조 지식으로 노드를 좁힌다 — 정점 정련(vertex refinement)
#
# Hay 등(VLDB 2008)은 공격자가 가진 "구조 지식"을 계층으로 정의했다.
#
# $$
# H_0(v) = \varepsilon, \qquad
# H_1(v) = \deg(v), \qquad
# H_{i+1}(v) = \{\!\{\, H_i(u) \;:\; u \in N(v) \,\}\!\}
# $$
#
# $\{\!\{\cdot\}\!\}$ 는 다중집합(multiset)이다. 즉
#
# - $H_0$ — 아무것도 모름. 모든 노드가 한 덩어리.
# - $H_1$ — "그 사람 친구가 7명이다". 차수만 안다.
# - $H_2$ — "그 사람 친구들의 친구 수가 각각 1, 2, 2, 5명이다". 이웃 차수의 다중집합.
# - $H_3$ — 한 단계 더.
#
# 같은 $H_i$ 값을 갖는 노드들이 **후보 집합(candidate set)** 이고,
# 그 크기가 곧 구조적 $k$ 다.
#
# $$
# k_{\text{struct}}(H_i) = \min_{v \in V} \bigl| \{\, u \in V : H_i(u) = H_i(v) \,\} \bigr|
# $$
#
# 후보 집합 크기가 1이면 그 노드는 **혼자다 = 특정된다**.
# 속성을 다 지웠는데도 특정된다.

# %%
def refinement_signatures(G, iterations=3):
    """H_1 .. H_iterations 서명을 노드별로 계산한다."""
    sig = {v: G.degree(v) for v in G.nodes}          # H_1
    levels = {1: dict(sig)}
    for i in range(2, iterations + 1):
        nxt = {}
        for v in G.nodes:
            nxt[v] = tuple(sorted(str(sig[u]) for u in G.neighbors(v)))
        sig = nxt
        levels[i] = dict(sig)
    return levels


def uniqueness(sig):
    """서명 딕셔너리 → (유일 노드 수, 비율, 최소 후보집합 크기, 동치류 수)."""
    cnt = Counter(sig.values())
    uniq = sum(1 for v in sig.values() if cnt[v] == 1)
    return uniq, uniq / len(sig), min(cnt.values()), len(cnt)


levels = refinement_signatures(G, iterations=3)

print("%-8s %10s %8s %14s %10s" % ("지식", "동치류 수", "유일 노드", "유일 비율", "최소 k"))
print("-" * 56)
print("%-8s %10d %8d %13.1f%% %10d" % ("H0", 1, 0, 0.0, N))
for i in (1, 2, 3):
    uniq, ratio, kmin, groups = uniqueness(levels[i])
    print("%-8s %10d %8d %13.1f%% %10d" % ("H%d" % i, groups, uniq, ratio * 100, kmin))
# 출력:
# 지식        동치류 수    유일 노드     유일 비율     최소 k
# --------------------------------------------------------
# H0                1        0          0.0%         40
# H1                8        2          5.0%          1
# H2               37       34         85.0%          1
# H3               40       40        100.0%          1


# %% [markdown]
# ### 읽는 법
#
# - $H_0$ — 아무것도 모르면 40명 중 아무나. 안전하다.
# - $H_1$ (차수만) — 벌써 2명이 혼자다. 허브들이다. "지인 11명인 사람"은 한 명뿐이다.
# - $H_2$ (이웃 차수 다중집합) — **85%가 혼자**다. 한 홉만 더 봤는데 절벽이 생긴다.
# - $H_3$ — 100%. 전원이 유일하다.
#
# 34장 예제 3에서 속성 3개 → 4개로 갈 때 0.6% → 65.8% 로 뛰었던 그 절벽과
# 같은 모양이다. 다른 점은 **여기서는 지울 속성이 이미 하나도 없다**는 것이다.
# 지울 것이 없는데 특정된다. 이게 속성 익명화보다 어려운 이유다.

# %%
# 차수(H1)는 같지만 이웃 모양(H2)이 달라 갈라지는 노드들을 직접 본다.
by_deg = {}
for v in G.nodes:
    by_deg.setdefault(G.degree(v), []).append(v)

deg_with_many = sorted((d, vs) for d, vs in by_deg.items() if len(vs) >= 4)
d, group = deg_with_many[0]
print("차수 %d 인 노드 %d개 — H1 만으로는 구별 불가:" % (d, len(group)))
print("   ", group)
print()
print("그런데 H2(이웃 차수 다중집합)를 보면:")
h2 = levels[2]
h2cnt = Counter(h2.values())
for v in group:
    tag = "  ← 혼자다. 특정됨" if h2cnt[h2[v]] == 1 else "  (후보 %d명)" % h2cnt[h2[v]]
    print("    %-4s 이웃 차수 = %-24s%s" % (v, ",".join(h2[v]), tag))
# 출력:
# 차수 2 인 노드 17개 — H1 만으로는 구별 불가:
#     ['n12', 'n16', 'n17', 'n18', 'n19', 'n21', 'n22', 'n26', 'n29',
#      'n32', 'n33', 'n34', 'n35', 'n36', 'n37', 'n38', 'n39']
#
# 그런데 H2(이웃 차수 다중집합)를 보면:
#     n12  이웃 차수 = 5,6                       (후보 2명)
#     n16  이웃 차수 = 4,5                       (후보 2명)
#     n17  이웃 차수 = 11,9                      ← 혼자다. 특정됨
#     n18  이웃 차수 = 10,9                      ← 혼자다. 특정됨
#     n19  이웃 차수 = 5,5                       ← 혼자다. 특정됨
#     n21  이웃 차수 = 6,6                       ← 혼자다. 특정됨
#     n22  이웃 차수 = 4,6                       ← 혼자다. 특정됨
#     n26  이웃 차수 = 4,5                       (후보 2명)
#     n29  이웃 차수 = 3,5                       ← 혼자다. 특정됨
#     n32  이웃 차수 = 5,6                       (후보 2명)
#     n33  이웃 차수 = 11,5                      ← 혼자다. 특정됨
#     n34  이웃 차수 = 10,4                      ← 혼자다. 특정됨
#     n35  이웃 차수 = 10,6                      ← 혼자다. 특정됨
#     n36  이웃 차수 = 3,4                       (후보 2명)
#     n37  이웃 차수 = 11,6                      ← 혼자다. 특정됨
#     n38  이웃 차수 = 3,6                       ← 혼자다. 특정됨
#     n39  이웃 차수 = 3,4                       (후보 2명)
#
# 차수 2 를 공유하는 17명 중 11명이 «이웃이 누구인지»만으로 혼자가 된다.
# 지울 속성은 남아 있지 않았다.


# %% [markdown]
# ## 3. 이웃 "모양" — 1-hop / 2-hop 서브그래프
#
# $H_2$ 는 이웃의 차수만 본다. 실제 공격자는 더 강한 지식을 가질 수 있다.
# "내 친구 A와 B는 서로도 친구다" 같은 **이웃들 사이의 연결**까지 안다.
#
# 이걸 Zhou–Pei(ICDE 2008)는 **이웃 그래프(neighborhood graph)** 라고 불렀다.
# 노드 $v$ 의 반지름 $r$ 이웃 유도 부분그래프
#
# $$ \mathrm{Ego}_r(v) = G\bigl[\{\, u : d(u,v) \le r \,\}\bigr] $$
#
# 를 중심 노드를 표시한 채로 동형(isomorphism)까지 비교한다.
# 여기서는 Weisfeiler–Lehman 그래프 해시로 근사한다.

# %%
def ego_signature(G, radius):
    """반지름 r 이웃 유도 부분그래프의 WL 해시. 중심 노드는 속성으로 표시."""
    sig = {}
    for v in G.nodes:
        ego = nx.ego_graph(G, v, radius=radius)
        for u in ego.nodes:
            ego.nodes[u]["c"] = "1" if u == v else "0"
        sig[v] = nx.weisfeiler_lehman_graph_hash(ego, node_attr="c", iterations=3)
    return sig


ego1 = ego_signature(G, 1)
ego2 = ego_signature(G, 2)

rows = [
    ("H1  (차수)", levels[1]),
    ("H2  (이웃 차수 다중집합)", levels[2]),
    ("Ego1 (1-hop 이웃 구조)", ego1),
    ("Ego2 (2-hop 이웃 구조)", ego2),
]
print("%-26s %8s %10s %8s" % ("공격자의 구조 지식", "유일 노드", "유일 비율", "최소 k"))
print("-" * 58)
attack_table = []
for name, sig in rows:
    uniq, ratio, kmin, _ = uniqueness(sig)
    attack_table.append((name, ratio * 100))
    print("%-26s %8d %9.1f%% %8d" % (name, uniq, ratio * 100, kmin))
# 출력:
# 공격자의 구조 지식                    유일 노드      유일 비율    최소 k
# ----------------------------------------------------------
# H1  (차수)                            2       5.0%        1
# H2  (이웃 차수 다중집합)                 34      85.0%        1
# Ego1 (1-hop 이웃 구조)                  8      20.0%        1
# Ego2 (2-hop 이웃 구조)                 40     100.0%        1


# %% [markdown]
# 2-hop 이웃 구조까지 아는 공격자에게는 **40명 전원이 유일**하다.
# 익명 그래프인데 한 명도 숨지 못한다.
#
# 주의할 점: `Ego1`(20.0%)이 `H2`(85.0%)보다 **낮다**. 계층이 단조롭지 않다.
# 반지름 1 이웃 그래프는 이웃의 "전체 차수"를 못 본다 — 이웃이 그래프 밖으로
# 뻗은 엣지가 잘려 나가기 때문이다. 대신 이웃들끼리의 연결(삼각형)을 본다.
# 이 그래프는 선호적 연결로 만들어져 삼각형이 거의 없으니(군집계수 0.084)
# `Ego1` 은 대부분 그냥 별 모양이고, 그래서 정보가 적다.
#
# 즉 두 지식은 포함 관계가 아니라 **다른 종류**다. 공격자가 무엇을 아느냐에 따라
# 위험이 달라지고, 그래서 "이 그래프는 안전하다"를 한 숫자로 말할 수 없다.
# 속성 익명화에서는 준식별자 목록을 적어 놓고 조합 수를 세면 끝났다.
# 구조에서는 **공격자 지식의 종류 자체가 열린 집합**이다. 이것이 어려움의 핵심이다.

# %% [markdown]
# ## 4. 공격 시나리오 하나
#
# 34장 예제 1의 상황을 떠올려 보자. `김도현(p1)` 을 지웠다. 이름도 지웠다.
# 그런데 공격자는 김도현을 개인적으로 안다. 그가 아는 것은 이름이 아니라 **관계**다.
#
# > "그 사람은 지인이 7명이고, 그 지인들의 지인 수는 각각 …이었다."
#
# 이 지식만으로 익명 그래프에서 그를 찾을 수 있는지 본다.

# %%
target = max(G.nodes, key=lambda v: (len(set(levels[2][v])), G.degree(v)))
known_degree = G.degree(target)
known_neighbor_degrees = sorted(G.degree(u) for u in G.neighbors(target))

print("공격자가 아는 것 (이름 없음, 속성 없음):")
print("   본인 차수        =", known_degree)
print("   이웃들의 차수    =", known_neighbor_degrees)

cands = [v for v in G.nodes
         if G.degree(v) == known_degree
         and sorted(G.degree(u) for u in G.neighbors(v)) == known_neighbor_degrees]
print()
print("차수만으로 좁힌 후보    :", sum(1 for v in G.nodes if G.degree(v) == known_degree), "명")
print("이웃 차수까지 쓴 후보   :", len(cands), "명 ->", cands)
print("정답과 일치?            :", cands == [target], "(실제:", target, ")")
# 출력:
# 공격자가 아는 것 (이름 없음, 속성 없음):
#    본인 차수        = 10
#    이웃들의 차수    = [2, 3, 3, 3, 3, 4, 4, 5, 6, 9]
#
# 차수만으로 좁힌 후보    : 2 명
# 이웃 차수까지 쓴 후보   : 1 명 -> ['n1']
# 정답과 일치?            : True (실제: n1 )
#
# 삭제 요청을 처리한 쪽은 "이름을 지웠다"고 답했다. 그런데 공격자는
# 이름을 쓰지 않았다. 관계만 썼고, 한 번에 맞혔다.


# %% [markdown]
# ## 5. 방어 시도 — $k$-차수 익명화 (Liu & Terzi, SIGMOD 2008)
#
# 속성에 대한 $k$-익명성의 그래프 버전 중 가장 단순한 것.
# **차수 수열**이 $k$-익명이 되게 만든다. 즉 어떤 차수 값이든 그 차수를 가진
# 노드가 $k$개 이상이 되게 한다.
#
# $$
# \forall v \in V : \bigl|\{\, u \in V : \deg(u) = \deg(v) \,\}\bigr| \ge k
# $$
#
# 방법은 **엣지 추가**다. 차수를 낮출 수는 없으니(엣지를 지우면 남의 이력이
# 깨진다 — 34장 예제 4) 올려서 맞춘다.
#
# 1. 차수를 내림차순으로 정렬해 크기 $k$ 이상의 연속 그룹으로 자른다.
# 2. 각 그룹의 목표 차수 = 그룹 내 최대 차수.
# 3. 부족분만큼 엣지를 추가한다.
#
# 여기서 "공짜가 아니다"가 드러난다. 없던 관계를 **만들어 넣는** 것이다.

# %%
def k_degree_anonymize(G, k, seed=SEED):
    """탐욕적 k-차수 익명화. 엣지만 추가한다. (교육용 단순 구현)"""
    r = random.Random(seed)
    H = G.copy()
    order = sorted(H.nodes, key=lambda v: -H.degree(v))

    # 1~2. 연속 그룹 → 목표 차수
    target = {}
    i = 0
    n = len(order)
    while i < n:
        end = min(i + k, n)
        if n - end < k:          # 남는 꼬리는 마지막 그룹이 흡수
            end = n
        grp = order[i:end]
        t = max(H.degree(v) for v in grp)
        for v in grp:
            target[v] = t
        i = end

    # 3. 부족분 채우기
    added, overshoot = 0, 0
    guard = 0
    while guard < 20000:
        guard += 1
        deficit = {v: target[v] - H.degree(v) for v in H.nodes}
        need = sorted([v for v in H.nodes if deficit[v] > 0],
                      key=lambda v: (-deficit[v], v))
        if not need:
            break
        v = need[0]
        # (a) 서로 부족한 두 노드를 짝지으면 왜곡이 가장 적다
        partner = None
        for u in need[1:]:
            if u != v and not H.has_edge(u, v):
                partner = u
                break
        # (b) 짝이 없으면 아무 비이웃과 잇는다. 상대는 목표를 초과한다.
        if partner is None:
            pool = [u for u in H.nodes if u != v and not H.has_edge(u, v)]
            if not pool:
                break
            pool.sort(key=lambda u: (H.degree(u), u))
            partner = pool[r.randrange(min(3, len(pool)))]
            overshoot += 1
        H.add_edge(v, partner)
        added += 1
    return H, added, overshoot


def degree_k(H):
    """실제 달성한 차수 익명성 k = 가장 작은 차수 그룹의 크기."""
    return min(Counter(dict(H.degree()).values()).values())


def stats(H):
    return {
        "edges": H.number_of_edges(),
        "avg_deg": 2 * H.number_of_edges() / H.number_of_nodes(),
        "clustering": nx.average_clustering(H),
        "apl": nx.average_shortest_path_length(H),
        "assort": nx.degree_assortativity_coefficient(H),
        "deg_k": degree_k(H),
    }


base = stats(G)
print("원본:", {kk: (round(float(vv), 4) if not isinstance(vv, int) else vv)
                for kk, vv in base.items()})
# 출력:
# 원본: {'edges': 76, 'avg_deg': 3.8, 'clustering': 0.0843, 'apl': 2.65,
#        'assort': -0.2507, 'deg_k': 1}
# deg_k = 1 -> 원본은 차수만으로도 유일해지는 사람이 있다. k-익명이 아니다.


# %% [markdown]
# ## 6. 트레이드오프를 숫자로
#
# $k$ 를 키우면 유일성은 줄어든다. 대신 그래프가 원본이 아니게 된다.
# 왜곡을 네 가지로 잰다.
#
# - **엣지 증가율** — 없던 관계를 몇 % 만들어 넣었나
# - **평균 군집계수** — 삼각형 구조. 커뮤니티 탐지가 여기에 기댄다
# - **평균 최단경로** — 확산·추천 분석이 여기에 기댄다
# - **차수 동류성(assortativity)** — 허브끼리 붙는 성향. 사회망의 특징적 지표
#
# 그리고 **핵심**: 차수를 $k$-익명으로 만들어도 $H_2$/Ego2 유일성은 어떻게 되나.

# %%
KS = [2, 3, 4, 5, 6, 8, 10]
sweep = []

hdr = ("k", "달성k", "추가엣지", "엣지+%", "H1유일%", "H2유일%", "Ego2유일%",
       "군집계수", "평균경로", "동류성")
print("%3s %5s %8s %7s %8s %8s %10s %9s %9s %8s" % hdr)
print("-" * 88)
u1b = uniqueness(levels[1])[1] * 100
u2b = uniqueness(levels[2])[1] * 100
ue2b = uniqueness(ego2)[1] * 100
print("%3s %5d %8s %7s %7.1f%% %7.1f%% %9.1f%% %9.4f %9.3f %8.3f"
      % ("원본", base["deg_k"], "-", "-", u1b, u2b, ue2b,
         base["clustering"], base["apl"], base["assort"]))

for k in KS:
    H, added, over = k_degree_anonymize(G, k)
    st = stats(H)
    lv = refinement_signatures(H, iterations=2)
    u1 = uniqueness(lv[1])[1] * 100
    u2 = uniqueness(lv[2])[1] * 100
    ue2 = uniqueness(ego_signature(H, 2))[1] * 100
    grow = (st["edges"] - base["edges"]) / base["edges"] * 100
    sweep.append({"k": k, "added": added, "over": over, "grow": grow,
                  "u1": u1, "u2": u2, "ue2": ue2,
                  "clu": st["clustering"], "apl": st["apl"],
                  "assort": st["assort"], "deg_k": st["deg_k"]})
    print("%3d %5d %8d %6.1f%% %7.1f%% %7.1f%% %9.1f%% %9.4f %9.3f %8.3f"
          % (k, st["deg_k"], added, grow, u1, u2, ue2,
             st["clustering"], st["apl"], st["assort"]))
# 출력:
#   k 달성k  추가엣지   엣지+%  H1유일%  H2유일%  Ego2유일%    군집계수    평균경로    동류성
# ----------------------------------------------------------------------------------------
# 원본    1     -       -     5.0%    85.0%    100.0%    0.0843    2.650   -0.251
#   2    2     4     5.3%     0.0%    87.5%    100.0%    0.1164    2.601   -0.245
#   3    3     6     7.9%     0.0%    70.0%    100.0%    0.1565    2.585   -0.193
#   4    4     4     5.3%     0.0%    67.5%    100.0%    0.1376    2.591   -0.206
#   5    5     9    11.8%     0.0%    52.5%    100.0%    0.1448    2.513   -0.188
#   6    6    13    17.1%     0.0%    57.5%    100.0%    0.2173    2.541   -0.099
#   8    8    16    21.1%     0.0%    32.5%    100.0%    0.2255    2.456   -0.137
#  10    8    30    39.5%     0.0%    50.0%    100.0%    0.2158    2.344   -0.023


# %% [markdown]
# ### 이 표가 말하는 것
#
# 1. **$H_1$ 유일성은 0%가 된다.** 차수만 보는 공격자는 완전히 막혔다.
#    $k$-차수 익명화는 **자기가 약속한 것만** 정확히 지킨다.
# 2. **$H_2$ 유일성은 잘 안 내려간다.** $k=2$ 에서는 85% → **87.5%로 오히려
#    올라간다.** 엣지를 추가하면 이웃들의 차수가 바뀌면서 없던 유일 조합이
#    새로 생기기 때문이다. 방어가 다른 축에서 역효과를 낸다.
#    $k=8$ 에서 32.5%까지 내려가지만 $k=10$ 에서 다시 50%로 튄다.
#    **단조롭지 않다** — "k를 키우면 안전해진다"가 성립하지 않는다.
# 3. **Ego2 유일성은 전 구간 100%다.** 2-hop을 아는 공격자에게는
#    어떤 $k$에서도 아무 방어가 되지 않았다.
# 4. 그런데 **비용은 확실히 든다.** 엣지가 5~40% 늘고,
#    군집계수가 0.084 → 0.226(**+168%**)으로 부풀고,
#    평균 최단경로가 2.65 → 2.34로 짧아지고,
#    동류성이 −0.251 → −0.023(거의 0)으로 밀린다.
#    커뮤니티 탐지, 확산 시뮬레이션, 추천 — 이 지표들에 기대는 분석은
#    전부 다른 답을 낸다. "없던 친구 관계를 30개 만들어 넣은" 그래프다.
# 5. $k=10$ 목표에서 **달성 $k$ 는 8**이다. 탐욕 채우기가 목표를 못 맞췄다.
#    강한 보장을 원할수록 엣지를 더 넣어야 하고, 그래도 보장이 깨진다.
#
# **정리하면 — 정확도는 확실히 내주고, 익명성은 한 축에서만 산다.**
# 34장 예제 2의 네 수준 표와 같은 구조다. 완벽한 칸이 없다.
#
# 더 강한 보장인 $k$-이웃 익명성(Zhou–Pei), $k$-자기동형(Zou et al.),
# $k$-동형(Cheng et al.) 은 Ego$_r$ 까지 막지만 비용이 급격히 커지고,
# 게다가 이들은 모두 "공격자의 지식이 이 계층에 갇혀 있다"는 가정에 기댄다.
# Narayanan–Shmatikov 의 시드 확장 공격처럼 **다른 그래프를 보조 정보로 쓰는**
# 공격에는 이 방어들이 전제부터 무너진다. 그래서 "아직 제대로 된 해법이 없다".

# %% [markdown]
# ## 7. 시각화

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("속성을 다 지운 뒤에도 유일해지는 노드 비율",
                        "k-차수 익명화의 트레이드오프"),
        horizontal_spacing=0.13,
    )

    # 패널 A — 구조 지식별 유일 비율 (단일 계열, 직접 라벨)
    names = [r[0].split("(")[0].strip() for r in rows]
    vals = [r[1] for r in attack_table]
    fig.add_trace(
        go.Bar(x=names, y=vals, marker_color=C_BLUE,
               marker_line_width=0, width=0.55,
               text=["%.0f%%" % v for v in vals],
               textposition="outside", textfont=dict(color=INK, size=12),
               hovertemplate="%{x}<br>유일 노드 %{y:.1f}%<extra></extra>",
               showlegend=False),
        row=1, col=1,
    )

    # 패널 B — k별 지표 (모두 %, 축 하나)
    ks = [s["k"] for s in sweep]

    # Ego2 는 전 구간 100%. 중립 회색 참조선으로 둔다 (계열 색을 쓰지 않는다)
    fig.add_trace(
        go.Scatter(x=ks, y=[s["ue2"] for s in sweep], mode="lines",
                   line=dict(color=INK2, width=2, dash="dash"),
                   name="Ego2 유일 노드 비율(%) — 변화 없음",
                   hovertemplate="Ego2 유일 %{y:.0f}%<extra></extra>"),
        row=1, col=2,
    )
    fig.add_annotation(x=ks[len(ks) // 2], y=100, text="Ego2 유일 100% — 꿈쩍도 않는다",
                       yshift=12, showarrow=False,
                       font=dict(color=INK2, size=11), row=1, col=2)

    series = [
        ("H2 유일 노드 비율(%)", [s["u2"] for s in sweep], C_BLUE),
        ("추가된 엣지 비율(%)", [s["grow"] for s in sweep], C_ORANGE),
        ("군집계수 변화율(%)", [(s["clu"] - base["clustering"]) / base["clustering"] * 100
                            for s in sweep], C_AQUA),
    ]
    for nm, ys, col in series:
        fig.add_trace(
            go.Scatter(x=ks, y=ys, name=nm, mode="lines+markers",
                       line=dict(color=col, width=2),
                       marker=dict(color=col, size=8,
                                   line=dict(color=SURFACE, width=2)),
                       hovertemplate=nm + " %{y:.1f}%<extra></extra>"),
            row=1, col=2,
        )
        fig.add_annotation(x=ks[-1], y=ys[-1], text=nm.split("(")[0].strip(),
                           xanchor="left", xshift=8, showarrow=False,
                           font=dict(color=col, size=11), row=1, col=2)

    fig.update_layout(
        template="simple_white",
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        font=dict(color=INK, size=12),
        title=dict(text="관계 자체가 식별자다 — 노드 40개 · 엣지 76개 익명 그래프",
                   font=dict(size=16, color=INK)),
        legend=dict(orientation="h", y=-0.22, x=0.42,
                    font=dict(color=INK2, size=11)),
        width=1080, height=500, margin=dict(l=60, r=150, t=90, b=110),
    )
    fig.update_yaxes(title_text="유일 노드 비율 (%)", range=[0, 112],
                     gridcolor=GRID, showgrid=True, row=1, col=1)
    fig.update_yaxes(title_text="비율 / 변화율 (%)", range=[-10, 190],
                     gridcolor=GRID, showgrid=True, row=1, col=2)
    fig.update_xaxes(title_text="공격자의 구조 지식", row=1, col=1)
    fig.update_xaxes(title_text="목표 k (차수 익명성)", dtick=1,
                     range=[1.6, 10.5], row=1, col=2)

    _show(fig)
    fig.write_image("expy.png", scale=2)
    print("expy.png 저장 완료")
except Exception as e:                      # noqa: BLE001
    print("시각화 건너뜀:", type(e).__name__, e)
# 출력: expy.png 저장 완료


# %% [markdown]
# ## 8. 한 줄 정리
#
# 속성 재식별은 **셀 수 있고 대응책이 있다** — 일반화, 억제, 잡음.
# 구조 재식별은 **지울 것이 이미 없는데도 일어나고**, 대응책이
# 그래프 자체를 바꿔야 하며, 그렇게 해도 한 계층만 막는다.
#
# | | 속성 재식별 | 구조 재식별 |
# |---|---|---|
# | 식별자 | 속성 조합 (팀+지역+직군+입사연도) | 엣지 조합 (차수, 이웃 모양) |
# | 지우면? | 속성을 빼면 없어진다 | **뺄 것이 없다.** 엣지는 남의 이력이기도 하다 |
# | 지표 | $k$-익명성 | 후보 집합 크기 / $k$-차수·$k$-이웃·$k$-자기동형 |
# | 대응 비용 | 정확도 하락 | **그래프 구조 왜곡** — 없던 관계 생성 |
# | 상태 | 성숙 | 미해결. 보조 그래프 공격에는 전제부터 무너짐 |
#
# 실무 결론은 34장의 것과 같다. 완전 삭제라는 마법은 없으니
# **무엇이 깨지는지 먼저 세고, 방침을 표로 적고, 방침 없는 것에서 멈춘다.**
