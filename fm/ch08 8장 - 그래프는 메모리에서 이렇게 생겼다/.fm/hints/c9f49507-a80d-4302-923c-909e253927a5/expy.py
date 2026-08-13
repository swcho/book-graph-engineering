# %% [markdown]
# # 2홉 비용은 왜 «차수의 제곱합»인가 — 유도와 검증
#
# **Q.** 2홉 탐색 비용은 무엇에 비례하는가?
# **A.** 차수의 제곱합 $\sum_v \deg(v)^2$ 에 비례한다. 평균 차수는 이 값을 잡아내지 못한다.
#
# 이 스크립트는 「$\sum d^2$ 이다」를 외우는 대신 **왜 그렇게 나오는지 한 줄씩 유도하고
# 실제 카운트로 확인한다.**
#
# 유도의 씨앗은 한 줄이다. 시작 노드 $u$ 에서 2홉을 펼치면
#
# $$\text{cost}(u) \;=\; \sum_{v \in N(u)} \deg(v)$$
#
# 1홉으로 이웃 $v$ 들을 만나고, 각 $v$ 에서 다시 이웃 목록 $\deg(v)$ 개를 훑기 때문이다.
# 이걸 **모든 시작 노드에 대해 더하면** 노드 $v$ 는 정확히 $\deg(v)$ 개의 $u$ 의 이웃 목록에
# 등장하므로
#
# $$\sum_{u \in V} \text{cost}(u) \;=\; \sum_{v \in V} \deg(v) \cdot \deg(v) \;=\; \sum_{v} \deg(v)^2$$
#
# 필요 패키지: plotly, kaleido (마지막 시각화 셀에서만 사용. 없으면 그 셀만 건너뛴다)

# %%
import math
import random
from collections import defaultdict


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


def make(n=50_000, avg_deg=12, skew=False, seed=20260801):
    """8장 graphgen.py 와 같은 생성기. skew=True 면 선호적 연결(쏠린 차수)."""
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


def adjacency(edges):
    adj = defaultdict(list)
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    return adj


def degrees(adj):
    return {u: len(vs) for u, vs in adj.items()}


print("생성기 준비 완료")
# 출력: 생성기 준비 완료

# %% [markdown]
# ## 1단계 — 손으로 셀 수 있는 그래프에서 유도를 확인한다
#
# 별 모양(star) 그래프를 보자. 가운데 노드 $c$ 에 잎 4개가 붙어 있다.
#
# - $\deg(c)=4$, 잎은 각각 $\deg=1$.
# - 잎에서 출발하면: 1홉으로 $c$ 하나, 거기서 $c$ 의 이웃 4개를 훑는다 → $\text{cost}=4$.
# - 가운데에서 출발하면: 1홉으로 잎 4개, 각 잎의 이웃 1개씩 → $\text{cost}=4$.
#
# 전체 합은 $4 \times 4 + 4 = 20$. 그리고
# $\sum d^2 = 4^2 + 1^2\!\times\!4 = 20$. 맞는다.
#
# 아래 코드는 이 계산을 «예측식»과 «실제 순회» 두 방법으로 각각 돌려 비교한다.


# %%
def cost_predicted(adj, deg, u):
    """예측: 이웃들의 차수 합. O(deg(u)) 로 싸게 구한다."""
    return sum(deg[v] for v in adj[u])


def cost_measured(adj, u):
    """실측: 실제로 2홉을 펼치며 «만진 엣지 수»와 «서로 다른 도달 노드 수»를 센다."""
    touched = 0
    reached = set()
    for v in adj[u]:
        for w in adj[v]:  # 이 루프가 진짜 비용이다
            touched += 1
            reached.add(w)
    return touched, len(reached)


def check(label, edges, n_nodes):
    adj = adjacency(edges)
    deg = degrees(adj)
    total_pred = sum(cost_predicted(adj, deg, u) for u in adj)
    total_meas = sum(cost_measured(adj, u)[0] for u in adj)
    sq = sum(d * d for d in deg.values())
    print(f"{label:<14} 노드 {n_nodes:>3}  Σ예측 {total_pred:>7,}  Σ실측 {total_meas:>7,}  Σd² {sq:>7,}")
    return sq


star = [(0, 1), (0, 2), (0, 3), (0, 4)]
path = [(i, i + 1) for i in range(4)]
ring = [(i, (i + 1) % 5) for i in range(5)]

check("별(star)", star, 5)
check("경로(path)", path, 5)
check("고리(ring)", ring, 5)
# 출력: 별(star)        노드   5  Σ예측      20  Σ실측      20  Σd²      20
# 출력: 경로(path)       노드   5  Σ예측      14  Σ실측      14  Σd²      14
# 출력: 고리(ring)       노드   5  Σ예측      20  Σ실측      20  Σd²      20

# %% [markdown]
# 세 값이 **정확히** 같다. 근사가 아니라 항등식이다.
#
# 노드 5개, 엣지 4~5개로 규모는 비슷한데 별 그래프의 비용(20)이 경로(14)보다 크다.
# 노드 수도 엣지 수도 비슷한데 비용이 다른 첫 번째 증거다. 차이는 오직 **분포**에서 온다.
#
# ## 2단계 — 행렬로 보면 한 줄 증명이 된다
#
# 인접 행렬 $A$ 에서 $(A^2)_{ij}$ 는 $i$ 에서 $j$ 로 가는 길이 2 워크의 개수다.
# 2홉 탐색이 훑는 총량은 이 워크의 총 개수, 즉 $A^2$ 의 모든 원소 합이다.
# $\mathbf{1}$ 을 전부 1인 벡터라 하면 $A\mathbf{1}$ 은 **차수 벡터**이므로
#
# $$\mathbf{1}^{\mathsf T} A^2 \mathbf{1} \;=\; (A\mathbf{1})^{\mathsf T}(A\mathbf{1}) \;=\; \|A\mathbf{1}\|^2 \;=\; \sum_v \deg(v)^2$$
#
# $A$ 가 대칭이라는 것 하나만 쓴 두 줄 증명이다. 참고로 $\operatorname{tr}(A^2)=\sum_v \deg(v)=2E$ 로,
# 「제자리로 돌아오는 워크」는 제곱합이 아니라 엣지 수만 본다. 제곱합은 **퍼져 나가는** 쪽의 양이다.


# %%
def matrix_check(edges, n):
    A = [[0] * n for _ in range(n)]
    for a, b in edges:
        A[a][b] = A[b][a] = 1
    A2 = [[sum(A[i][k] * A[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
    total = sum(sum(row) for row in A2)
    trace = sum(A2[i][i] for i in range(n))
    deg = [sum(row) for row in A]
    return total, sum(d * d for d in deg), trace, 2 * len(edges)


rnd = random.Random(3)
small = sorted({(min(a, b), max(a, b)) for a, b in ((rnd.randrange(8), rnd.randrange(8)) for _ in range(20)) if a != b})
for name, e, n in (("별", star, 5), ("고리", ring, 5), ("무작위 8노드", small, 8)):
    tot, sq, tr, twoE = matrix_check(e, n)
    print(f"{name:<12} 1ᵀA²1 = {tot:>4}   Σd² = {sq:>4}   tr(A²) = {tr:>4}   2E = {twoE:>4}")
# 출력: 별            1ᵀA²1 =   20   Σd² =   20   tr(A²) =    8   2E =    8
# 출력: 고리           1ᵀA²1 =   20   Σd² =   20   tr(A²) =   10   2E =   10
# 출력: 무작위 8노드      1ᵀA²1 =  108   Σd² =  108   tr(A²) =   28   2E =   28
#
# 세 그래프 모두 1ᵀA²1 과 Σd² 가 일치하고, tr(A²) 는 2E 와 일치한다.

# %% [markdown]
# ## 3단계 — 같은 평균 차수, 다른 분포
#
# 이제 규모를 올린다. 노드 5만 개, 목표 평균 차수 12로 두 그래프를 만든다.
#
# - **고른 분포**: 아무 노드에나 균등하게 붙인다.
# - **쏠린 분포**: 이미 차수가 높은 노드에 더 붙는다(선호적 연결). 실제 소셜·웹 그래프가 이쪽이다.
#
# 평균은 맞춰 두고 $\sum d^2$ 만 본다.

# %%
N = 50_000
graphs = {}
for label, skew in (("고른 분포", False), ("쏠린 분포", True)):
    e = make(n=N, avg_deg=12, skew=skew)
    adj = adjacency(e)
    deg = degrees(adj)
    vals = sorted(deg.values(), reverse=True)
    graphs[label] = {"edges": e, "adj": adj, "deg": deg, "vals": vals}

hdr = f"{'그래프':<10} {'노드':>7} {'엣지':>9} {'평균차수':>9} {'최대차수':>9} {'Σd²':>16} {'배수':>7}"
print(hdr)
print("-" * len(hdr))
base = None
for label, g in graphs.items():
    vals = g["vals"]
    sq = sum(d * d for d in vals)
    g["sq"] = sq
    g["mean"] = sum(vals) / len(vals)
    base = base or sq
    print(
        f"{label:<10} {len(vals):>7,} {len(g['edges']):>9,} {g['mean']:>9.1f} "
        f"{vals[0]:>9,} {sq:>16,} {sq / base:>6.1f}x"
    )
# 출력: 그래프             노드        엣지      평균차수      최대차수              Σd²      배수
# 출력: -------------------------------------------------------------------------
# 출력: 고른 분포       50,000   299,958      12.0        25        7,494,946    1.0x
# 출력: 쏠린 분포       50,000   280,374      11.2    30,267    1,520,876,110  202.9x

# %% [markdown]
# 노드 수는 같고, 엣지 수는 쏠린 쪽이 **더 적고**, 평균 차수도 쏠린 쪽이 **더 낮다.**
# 그런데 $\sum d^2$ 는 **203배**다. 세 가지 상식적인 지표가 전부 쏠린 쪽 손을 들어 주는데
# 실제 비용은 두 자릿수 배로 벌어진다.
#
# ## 4단계 — 평균이 못 잡는 부분은 정확히 «분산»이다
#
# 왜 평균이 실패하는지는 대수적으로 분리된다. $\bar d = \frac{1}{n}\sum d_v$,
# $\sigma^2 = \frac{1}{n}\sum (d_v-\bar d)^2$ 라 하면
#
# $$\sigma^2 = \frac{1}{n}\sum d_v^2 - \bar d^2 \quad\Longrightarrow\quad \boxed{\;\sum_v d_v^2 = n\left(\bar d^{\,2} + \sigma^2\right)\;}$$
#
# - $n\bar d^{\,2}$ : 평균이 설명하는 부분.
# - $n\sigma^2$ : **평균이 전혀 모르는 부분.**
#
# 평균 차수만 보고 용량을 산정하면 두 번째 항을 0으로 가정하는 셈이다.

# %%
print(f"{'그래프':<10} {'n·d̄²':>15} {'n·σ²':>17} {'합':>17} {'실제 Σd²':>17} {'분산 몫':>9}")
for label, g in graphs.items():
    vals, n = g["vals"], len(g["vals"])
    mean = g["mean"]
    var = sum((d - mean) ** 2 for d in vals) / n
    a, b = n * mean * mean, n * var
    print(f"{label:<10} {a:>15,.0f} {b:>17,.0f} {a + b:>17,.0f} {g['sq']:>17,} {b / (a + b) * 100:>8.1f}%")
    g["var"] = var
# 출력: 그래프                  n·d̄²              n·σ²                 합            실제 Σd²      분산 몫
# 출력: 고른 분포            7,197,984           296,962         7,494,946         7,494,946      4.0%
# 출력: 쏠린 분포            6,288,766     1,514,587,344     1,520,876,110     1,520,876,110     99.6%

# %% [markdown]
# 항등식이 소수점 없이 맞는다. 그리고 쏠린 그래프에서는 비용의 **99.6%가 분산 항에서 나온다.**
# 평균만 본 예측치는 실제의 1/242이다.
#
# 이것이 **젠슨 부등식**의 구체적 사례다. $f(x)=x^2$ 는 볼록이므로 항상
#
# $$\mathbb{E}[d^2] \;\ge\; \left(\mathbb{E}[d]\right)^2$$
#
# 등호는 분산이 0일 때(모든 차수가 같을 때)뿐이다. 즉 **평균 차수로 계산한 비용은 언제나
# 과소 추정이며, 언제 얼마나 과소인지는 분포의 쏠림이 정한다.** 코시-슈바르츠로 쓰면
# $\sum d^2 \ge (\sum d)^2 / n = 4E^2/n$ 이라는 하한, 그리고
# $\sum d^2 \le d_{\max}\sum d = 2E\,d_{\max}$ 라는 상한을 얻는다.

# %%
for label, g in graphs.items():
    vals, n = g["vals"], len(g["vals"])
    E = len(g["edges"])
    lo = (sum(vals)) ** 2 / n  # = 4E²/n
    hi = vals[0] * sum(vals)  # = 2E·d_max
    print(f"{label:<10} 하한 4E²/n = {lo:>15,.0f}  ≤  Σd² = {g['sq']:>15,}  ≤  2E·d_max = {hi:>17,}")
    print(f"{'':10}   상한까지 여유 {hi / g['sq']:.1f}배 (최대 차수 노드가 비용을 얼마나 독점하는지의 척도)")
# 출력: 고른 분포      하한 4E²/n =       7,197,984  ≤  Σd² =       7,494,946  ≤  2E·d_max =        14,997,900
# 출력:              상한까지 여유 2.0배 (최대 차수 노드가 비용을 얼마나 독점하는지의 척도)
# 출력: 쏠린 분포      하한 4E²/n =       6,288,766  ≤  Σd² =   1,520,876,110  ≤  2E·d_max =    16,972,159,716
# 출력:              상한까지 여유 11.2배 (최대 차수 노드가 비용을 얼마나 독점하는지의 척도)

# %% [markdown]
# ## 5단계 — 항등식을 5만 노드에서도 확인한다
#
# 1단계에서 손으로 확인한 $\sum_u \text{cost}(u) = \sum_v d_v^2$ 를 큰 그래프에서도 확인한다.
# 여기서 중요한 비대칭이 있다. 예측값 $\sum_{v\in N(u)}\deg(v)$ 는 이웃의 **차수만 더하므로**
# 전체를 다 구해도 $O(E)$ 다. 반면 실제 순회는 이웃의 **이웃 목록을 다 읽어야** 하므로
# $O(\sum d^2)$ 다. 그래서 예측은 전부 돌리고, 실측은 표본만 돌린다.

# %%
for label, g in graphs.items():
    adj, deg = g["adj"], g["deg"]
    total_pred = sum(cost_predicted(adj, deg, u) for u in adj)
    print(f"{label:<10} Σ_u cost(u) = {total_pred:>16,}   Σd² = {g['sq']:>16,}   일치 {total_pred == g['sq']}")
# 출력: 고른 분포      Σ_u cost(u) =        7,494,946   Σd² =        7,494,946   일치 True
# 출력: 쏠린 분포      Σ_u cost(u) =    1,520,876,110   Σd² =    1,520,876,110   일치 True

# %%
# 표본 시작 노드에서 실제로 순회해 «만진 엣지 수»가 예측과 같은지 본다.
rnd = random.Random(11)
print(f"{'그래프':<10} {'시작노드':>8} {'예측':>10} {'실측 touched':>13} {'서로 다른 도달':>13} {'중복률':>8}")
for label, g in graphs.items():
    adj, deg = g["adj"], g["deg"]
    nodes = sorted(adj)
    picks = rnd.sample(nodes, 2) + [max(nodes, key=lambda u: deg[u])]
    for u in picks:
        pred = cost_predicted(adj, deg, u)
        if pred > 5_000_000:  # 슈퍼 노드는 실측이 너무 오래 걸린다
            print(f"{label:<10} {u:>8} {pred:>10,} {'(생략: 예측 500만 초과)':>26}")
            continue
        touched, reached = cost_measured(adj, u)
        print(f"{label:<10} {u:>8} {pred:>10,} {touched:>13,} {reached:>13,} {touched / max(reached, 1):>7.1f}x")
# 출력: 그래프            시작노드         예측    실측 touched      서로 다른 도달      중복률
# 출력: 고른 분포         29647        135           135           126     1.1x
# 출력: 고른 분포         36685        167           167           155     1.1x
# 출력: 고른 분포          5279        317           317           292     1.1x
# 출력: 쏠린 분포         30516     60,209        60,209        41,489     1.5x
# 출력: 쏠린 분포         29611     27,694        27,694        24,710     1.1x
# 출력: 쏠린 분포             2    343,759       343,759        49,874     6.9x

# %% [markdown]
# 실측 `touched` 가 예측과 **정확히** 일치한다. 그리고 두 가지가 더 보인다.
#
# 1. **`touched` 와 `reached` 는 다른 양이다.** $\sum d^2$ 는 «만진 엣지 수»(작업량)를 재고,
#    `reached` 는 중복을 제거한 결과 집합 크기다. 노드 2번은 34만 개를 만져서 5만 개를 얻는다
#    (중복률 6.9배). 「일은 많이 했는데 결과는 작다」가 된다.
#    **비용은 결과 크기가 아니라 작업량이 정한다.** 그래서 결과 개수로 용량을 산정하면 틀린다.
# 2. **쏠린 그래프에서는 «평범한» 노드조차 비싸다.** 무작위로 뽑은 노드의 비용이 2.7만~6만이다.
#    자기 차수는 10 남짓인데 이웃 중 하나가 슈퍼 노드라서 그렇다. 쏠림의 벌점은
#    슈퍼 노드 본인에게만 청구되지 않고, 슈퍼 노드에 «닿는 모든 노드»에게 청구된다.
#
# ## 6단계 — 무작위 이웃의 기대 차수: 친구 관계 역설
#
# 왜 「평범한 노드도 비싸다」가 되는지 확률로 설명된다. 무작위 노드 하나를 잡고
# 그 이웃 하나를 무작위로 골랐을 때, 그 이웃의 기대 차수는 $\bar d$ 가 아니다.
# 차수 $d$ 인 노드는 이웃으로 뽑힐 기회가 $d$ 번 있으므로 뽑힐 확률이 차수에 비례한다.
#
# $$\mathbb{E}[\deg(\text{무작위 이웃})] \;=\; \frac{\sum_v d_v \cdot d_v}{\sum_v d_v} \;=\; \frac{\mathbb{E}[d^2]}{\mathbb{E}[d]}$$
#
# 그리고 1홉 비용의 기대값 $\mathbb{E}[\text{cost}] = \bar d \cdot \frac{\mathbb{E}[d^2]}{\mathbb{E}[d]} = \mathbb{E}[d^2]$.
# **2홉 비용의 평균이 곧 차수의 2차 모멘트다.** 여기서 제곱합이 다시 나온다.

# %%
print(f"{'그래프':<10} {'E[d]':>8} {'E[d²]/E[d]':>12} {'역설 배수':>10} {'E[d²]=Σd²/n':>14}")
for label, g in graphs.items():
    vals, n = g["vals"], len(g["vals"])
    Ed = sum(vals) / n
    Ed2 = g["sq"] / n
    print(f"{label:<10} {Ed:>8.1f} {Ed2 / Ed:>12.1f} {Ed2 / Ed / Ed:>9.1f}x {Ed2:>14,.0f}")
# 출력: 그래프            E[d]   E[d²]/E[d]      역설 배수    E[d²]=Σd²/n
# 출력: 고른 분포          12.0         12.5       1.0x            150
# 출력: 쏠린 분포          11.2       2712.2     241.8x         30,418

# %% [markdown]
# 쏠린 그래프에서 「내 친구의 평균 친구 수」는 내 친구 수의 **242배**다.
# 1홉에서는 12명을 보는데 2홉에서는 3만 개를 만지는 이유가 이 한 줄이다.
#
# ## 7단계 — 멱법칙에서 제곱합이 폭발하는 이유
#
# 실제 그래프의 차수 분포는 대개 멱법칙에 가깝다. $P(d=k) \propto k^{-\gamma}$.
# 그러면 2차 모멘트는
#
# $$\mathbb{E}[d^2] \;=\; \sum_{k} k^2 \cdot c\,k^{-\gamma} \;=\; c\sum_k k^{\,2-\gamma}$$
#
# $\sum k^{-p}$ 는 $p>1$ 에서만 수렴한다. 여기서는 $p=\gamma-2$ 이므로 **수렴 조건은 $\gamma>3$.**
# 관측된 소셜·웹 그래프의 $\gamma$ 는 대개 2.1~2.5다. 즉 **2차 모멘트가 발산한다.**
#
# 발산한다는 말의 실무적 의미는 이것이다. 평균 $\mathbb{E}[d]$ 는 $\gamma>2$ 면 유한하므로
# 데이터가 늘어도 안정된 값에 수렴한다. 그래서 평균 차수를 보고 있으면 「그래프가 안정적으로
# 커지고 있다」고 착각한다. 그런데 $\mathbb{E}[d^2]$ 는 유한한 값으로 수렴하지 않고
# **$n$ 이 커질수록 계속 커진다.** 노드당 2홉 비용 자체가 증가한다.

# %%
print(f"{'n':>8}  {'고른: Σd²/n':>12}  {'쏠린: Σd²/n':>12}  {'쏠린 d_max':>10}")
for n in (5_000, 10_000, 20_000, 40_000, 80_000):
    row = []
    for skew in (False, True):
        e = make(n=n, avg_deg=12, skew=skew)
        d = degrees(adjacency(e))
        row.append((sum(v * v for v in d.values()) / len(d), max(d.values())))
    print(f"{n:>8}  {row[0][0]:>12,.0f}  {row[1][0]:>12,.0f}  {row[1][1]:>10,}")
# 출력:        n     고른: Σd²/n     쏠린: Σd²/n    쏠린 d_max
# 출력:     5000           150         4,844       3,705
# 출력:    10000           150         8,426       6,933
# 출력:    20000           150        14,746      13,173
# 출력:    40000           150        25,618      24,811
# 출력:    80000           150        44,049      46,464

# %% [markdown]
# **고른 분포는 150에서 꼼짝하지 않는다.** $n$ 을 16배 늘려도 노드당 2홉 비용은 그대로다.
# 여기서는 「노드 수」가 실제로 비용을 예측한다(총 비용 $=150n$, 선형).
#
# **쏠린 분포는 노드당 비용 자체가 계속 커진다.** $n$ 을 16배(5천→8만) 늘리는 동안
# $\mathbb{E}[d^2]$ 가 9.1배가 됐다. 지수로 읽으면
#
# $$\frac{\log 9.1}{\log 16} \approx 0.80 \quad\Longrightarrow\quad \mathbb{E}[d^2] \sim n^{0.8},\qquad \sum d^2 \sim n^{1.8}$$
#
# 총 2홉 비용이 $n^{1.8}$ 이다. 노드를 2배 늘리면 비용은 2배가 아니라 3.5배가 된다.
# 「100만에서 멀쩡하고 10만에서 죽는」 그래프의 정체가 이 초선형 지수다.
# (지수 0.8 은 이 생성기의 고유한 값이다. 이론적으로는
# $d_{\max} \sim n^{1/(\gamma-1)}$, $\mathbb{E}[d^2] \sim n^{(3-\gamma)/(\gamma-1)}$ 이므로
# $\gamma$ 가 3에 가까울수록 지수가 0에 가까워지고, 2에 가까울수록 1에 가까워진다.
# 중요한 것은 정확한 지수가 아니라 **0이 아니라는 사실**이다.)
#
# ## 8단계 — 3홉으로 가면 지수가 하나 더 붙는다
#
# 같은 행렬 논법을 한 번 더 쓴다. 길이 3 워크의 총수는
#
# $$\mathbf{1}^{\mathsf T} A^3 \mathbf{1} \;=\; (A\mathbf{1})^{\mathsf T} A (A\mathbf{1}) \;=\; 2\!\!\sum_{\{u,v\}\in E}\!\! d_u d_v$$
#
# 이제 **엣지 양 끝의 차수 곱**이 더해진다. 슈퍼 노드가 다른 슈퍼 노드와 이어져 있으면
# 그 엣지 하나가 $d_u d_v$ 만큼 기여한다. 홉이 늘어날 때마다 쏠림의 벌점이 곱으로 커진다.

# %%
print(f"{'그래프':<10} {'2홉 Σd²':>16} {'3홉 2Σd_u·d_v':>18} {'3홉/2홉':>9}")
for label, g in graphs.items():
    deg = g["deg"]
    three = 2 * sum(deg[a] * deg[b] for a, b in g["edges"])
    print(f"{label:<10} {g['sq']:>16,} {three:>18,} {three / g['sq']:>8.1f}x")
# 출력: 그래프                2홉 Σd²       3홉 2Σd_u·d_v     3홉/2홉
# 출력: 고른 분포             7,494,946         93,490,042     12.5x
# 출력: 쏠린 분포         1,520,876,110     35,123,314,976     23.1x

# %% [markdown]
# 고른 그래프는 홉이 하나 늘 때 12.5배 — 정확히 평균 차수다. 예상대로다
# ($2\sum_E d_u d_v \approx 2E\bar d^{\,2} = n\bar d^{\,3}$, $\sum d^2 \approx n\bar d^{\,2}$, 비 $=\bar d$).
#
# 쏠린 그래프는 23.1배다. 두 그래프의 **절대 격차**는 2홉의 203배에서 3홉의 375배로 벌어진다.
# 홉이 늘어날수록 쏠림의 벌점이 누적된다.
#
# 다만 23.1배는 「1,500배쯤 되겠지」라는 순진한 예상보다 훨씬 작다. 이유가 중요하다.
# 이 생성기의 허브는 **잎에만 붙어 있다**(비동류적, disassortative). 그래서 엣지의
# $d_u d_v$ 곱에서 한쪽은 항상 작다. 만약 허브끼리 서로 연결된 그래프(동류적, assortative)라면
# 그 엣지 하나가 $d_u d_v$ 만큼 기여하면서 3홉 비용이 폭발한다.
#
# 즉 **2홉 비용은 차수 분포만으로 결정되지만($\sum d^2$), 3홉부터는 «누가 누구와 붙어 있는지»가
# 함께 들어온다.** 이것이 2홉이 특별한 이유이고, 「2홉 비용 = 제곱합」이라는 깔끔한 명제가
# 정확히 2홉에서만 성립하는 이유다.
#
# ## 9단계 — 시각화
#
# 네 장으로 정리한다.
#
# 1. 차수 분포(로그-로그). 고른 쪽은 평균 근처에 뭉치고, 쏠린 쪽은 직선 꼬리를 갖는다.
# 2. $\sum d^2$ 에 대한 누적 기여. 상위 몇 개 노드가 비용의 몇 %를 먹는지.
# 3. 시작 노드별 2홉 비용 분포. 평균이 어디에 있고 실제 질의가 어디에 흩어져 있는지.
# 4. $n$ 이 늘 때 노드당 비용의 추이. 한쪽은 수평선, 한쪽은 우상향 직선.

# %%
OUT = "expy.png"
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    COLOR = {"고른 분포": "#4C78A8", "쏠린 분포": "#E45756"}

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "① 차수 분포 (로그-로그)",
            "② Σd² 누적 기여 — 상위 노드 몇 개가 비용을 먹는다",
            "③ 시작 노드별 2홉 비용 (점선 = 평균 = E[d²])",
            "④ n 이 늘 때 노드당 2홉 비용 Σd²/n",
        ),
        horizontal_spacing=0.11,
        vertical_spacing=0.14,
    )

    # ① 차수 분포
    for label, g in graphs.items():
        cnt = defaultdict(int)
        for d in g["vals"]:
            cnt[d] += 1
        xs = sorted(cnt)
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=[cnt[x] for x in xs],
                mode="markers",
                name=label,
                marker=dict(color=COLOR[label], size=5, opacity=0.7),
                legendgroup=label,
            ),
            row=1,
            col=1,
        )

    # ② 누적 기여
    for label, g in graphs.items():
        vals = g["vals"]
        tot, acc, xs, ys = g["sq"], 0, [], []
        for i, d in enumerate(vals, 1):
            acc += d * d
            xs.append(i)
            ys.append(acc / tot * 100)
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="lines",
                name=label,
                line=dict(color=COLOR[label], width=2),
                legendgroup=label,
                showlegend=False,
            ),
            row=1,
            col=2,
        )

    # ③ 시작 노드별 비용
    for label, g in graphs.items():
        adj, deg = g["adj"], g["deg"]
        costs = [max(cost_predicted(adj, deg, u), 1) for u in adj]
        fig.add_trace(
            go.Histogram(
                x=[math.log10(c) for c in costs],
                name=label,
                marker=dict(color=COLOR[label]),
                opacity=0.65,
                nbinsx=60,
                legendgroup=label,
                showlegend=False,
            ),
            row=2,
            col=1,
        )
        m = math.log10(g["sq"] / len(g["vals"]))
        fig.add_vline(x=m, line=dict(color=COLOR[label], width=2, dash="dot"), row=2, col=1)
    fig.update_layout(barmode="overlay")

    # ④ 스케일링
    ns = [5_000, 10_000, 20_000, 40_000, 80_000]
    for label, skew in (("고른 분포", False), ("쏠린 분포", True)):
        ys = []
        for n in ns:
            d = degrees(adjacency(make(n=n, avg_deg=12, skew=skew)))
            ys.append(sum(v * v for v in d.values()) / len(d))
        fig.add_trace(
            go.Scatter(
                x=ns,
                y=ys,
                mode="lines+markers",
                name=label,
                line=dict(color=COLOR[label], width=2),
                legendgroup=label,
                showlegend=False,
            ),
            row=2,
            col=2,
        )

    fig.update_xaxes(type="log", title_text="차수 d", row=1, col=1)
    fig.update_yaxes(type="log", title_text="노드 수", row=1, col=1)
    fig.update_xaxes(type="log", title_text="차수 내림차순 노드 순위", row=1, col=2)
    fig.update_yaxes(title_text="Σd² 누적 기여 (%)", range=[0, 105], row=1, col=2)
    fig.update_xaxes(title_text="log₁₀(2홉 비용)", row=2, col=1)
    fig.update_yaxes(title_text="노드 수", row=2, col=1)
    fig.update_xaxes(type="log", title_text="노드 수 n", row=2, col=2)
    fig.update_yaxes(type="log", title_text="Σd² / n", row=2, col=2)

    fig.update_layout(
        title=dict(
            text="2홉 비용 ∝ Σd² — 평균 차수는 같고 분포만 다른 두 그래프 (n=50,000, 평균차수 12)",
            x=0.5,
            xanchor="center",
            y=0.975,
        ),
        height=800,
        width=1180,
        template="plotly_white",
        legend=dict(orientation="h", y=1.035, x=0.5, xanchor="center", yanchor="bottom"),
        margin=dict(t=125, b=60, l=70, r=40),
        font=dict(size=12),
    )

    _show(fig)
    fig.write_image(OUT, scale=2)
    print(f"저장: {OUT}")
except ImportError as exc:
    print(f"시각화 건너뜀 (필요 패키지: plotly, kaleido) — {exc}")
# 출력: 저장: expy.png

# %% [markdown]
# ## 정리
#
# | 단계 | 얻은 것 |
# |---|---|
# | 시작 노드 하나 | $\text{cost}(u)=\sum_{v\in N(u)}\deg(v)$ |
# | 모든 시작 노드 | $\sum_u \text{cost}(u)=\sum_v \deg(v)^2$ — **항등식** |
# | 행렬 | $\mathbf{1}^{\mathsf T}A^2\mathbf{1}=\|A\mathbf{1}\|^2=\sum_v \deg(v)^2$ |
# | 평균과의 관계 | $\sum d^2 = n(\bar d^{\,2}+\sigma^2)$ — 평균은 첫 항만 안다 |
# | 젠슨 | $\mathbb{E}[d^2]\ge(\mathbb{E}[d])^2$ — 평균 기반 추정은 항상 과소 |
# | 확률 | 무작위 이웃의 기대 차수 $=\mathbb{E}[d^2]/\mathbb{E}[d]$ |
# | 멱법칙 | $\gamma\le 3$ 이면 $\mathbb{E}[d^2]$ 발산 → 노드당 비용이 $n$ 과 함께 증가 |
# | 3홉 | $2\sum_{\{u,v\}\in E} d_u d_v$ — 분포만이 아니라 연결 구조까지 들어온다 |
#
# 한 줄로: **2홉 비용은 차수의 2차 모멘트다. 평균은 1차 모멘트다. 1차만 재면
# 분산 항 전부를 0으로 가정한 셈이고, 쏠린 그래프에서 그 항이 비용의 99%다.**
