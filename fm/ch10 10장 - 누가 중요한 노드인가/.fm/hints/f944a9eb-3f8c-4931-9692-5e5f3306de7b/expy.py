# %% [markdown]
# # 고유벡터 중심성 — 멱반복으로 직접 굴려 보기
#
# **원리**: "중요한 이웃을 가진 노드가 중요하다"
#
# $$
# \lambda x_v = \sum_{u \in N(v)} x_u
# \qquad\Longleftrightarrow\qquad
# A\mathbf{x} = \lambda \mathbf{x}
# $$
#
# 인접행렬 $A$의 **최대 고윳값 $\lambda_1$에 대응하는 고유벡터**가 곧 고유벡터 중심성이다.
# 이걸 고윳값 분해 없이 **곱셈 반복**만으로 뽑아내는 방법이 **멱반복(power iteration)** 이다.
#
# ```
# x ← (1, 1, ..., 1)
# repeat:  y ← A x  ;  x ← y / max(y)
# until 수렴
# ```
#
# 아래에서 회차별로 벡터가 어떻게 움직이는지, numpy 고유벡터와 정말 같은지,
# 그리고 언제 이 방법이 **실패**하는지를 순서대로 확인한다.

# %%
# 필요 패키지: numpy, plotly, kaleido
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

np.set_printoptions(precision=4, suppress=True)


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


print("numpy", np.__version__)
# 출력: numpy 2.0.2

# %% [markdown]
# ## 1. 장난감 그래프와 인접행렬
#
# ```
#   1 --- 2
#   |  \  |
#   |   \ |
#   4     3
# ```
#
# 노드 1은 2·3·4 모두와, 2와 3은 서로와 그리고 1과, 4는 1하고만 이어져 있다.
# 인접행렬 $A_{vu}=1 \iff v\text{—}u$ 엣지 존재.

# %%
NODES = ["n1", "n2", "n3", "n4"]
A = np.array(
    [
        [0, 1, 1, 1],
        [1, 0, 1, 0],
        [1, 1, 0, 0],
        [1, 0, 0, 0],
    ],
    dtype=float,
)

print("A =")
print(A)
print("차수(행 합) =", A.sum(axis=1))
# 출력: A =
# 출력: [[0. 1. 1. 1.]
# 출력:  [1. 0. 1. 0.]
# 출력:  [1. 1. 0. 0.]
# 출력:  [1. 0. 0. 0.]]
# 출력: 차수(행 합) = [3. 2. 2. 1.]

# %% [markdown]
# ## 2. 멱반복 — 회차별 벡터 변화
#
# 핵심은 두 줄뿐이다.
#
# $$
# \mathbf{y}^{(k)} = A\mathbf{x}^{(k-1)}, \qquad
# \mathbf{x}^{(k)} = \frac{\mathbf{y}^{(k)}}{\max_v y^{(k)}_v}
# $$
#
# 최댓값으로 나누는 이유: 나누지 않으면 매 회 $\lambda_1$배씩 커져 값이 폭발한다.
# 정규화는 **순위를 바꾸지 않는다**(모두 같은 양수로 나누므로).

# %%
def power_iteration(A, rounds=200, tol=1e-12, record=True):
    """멱반복. 최댓값(L-infinity) 정규화. history 는 회차별 x 벡터."""
    n = A.shape[0]
    x = np.ones(n)
    x = x / x.max()
    hist = [x.copy()]
    for k in range(1, rounds + 1):
        y = A @ x                       # y = A x  ← "이웃 값의 합"
        m = y.max()
        if m == 0:
            break
        nx = y / m                      # 최댓값으로 정규화
        delta = np.abs(nx - x).max()
        x = nx
        if record:
            hist.append(x.copy())
        if delta < tol:
            break
    return x, np.array(hist), k


x_star, hist, iters = power_iteration(A)

print(f"{'회차':>4}  " + "  ".join(f"{v:>7}" for v in NODES) + "     변화량")
for k, v in enumerate(hist[:11]):
    d = "" if k == 0 else f"{np.abs(hist[k] - hist[k-1]).max():.6f}"
    print(f"{k:>4}  " + "  ".join(f"{t:7.4f}" for t in v) + f"   {d:>10}")
print(f"...\n수렴까지 {iters}회, 최종 x = {x_star}")
# 출력:   회차       n1       n2       n3       n4     변화량
# 출력:     0   1.0000   1.0000   1.0000   1.0000
# 출력:     1   1.0000   0.6667   0.6667   0.3333     0.666667
# 출력:     2   1.0000   1.0000   1.0000   0.6000     0.333333
# 출력:     3   1.0000   0.7692   0.7692   0.3846     0.230769
# 출력:     4   1.0000   0.9200   0.9200   0.5200     0.150769
# 출력:     5   1.0000   0.8136   0.8136   0.4237     0.106441
# 출력:     6   1.0000   0.8843   0.8843   0.4876     0.070738
# 출력:     7   1.0000   0.8352   0.8352   0.4432     0.049133
# 출력:     8   1.0000   0.8683   0.8683   0.4731     0.033119
# 출력:     9   1.0000   0.8455   0.8455   0.4525     0.022794
# 출력:    10   1.0000   0.8610   0.8610   0.4665     0.015468
# 출력: ...
# 출력: 수렴까지 72회, 최종 x = [1.     0.8546 0.8546 0.4608]

# %% [markdown]
# 값이 위아래로 **번갈아 오버슛하면서** 폭이 줄어든다.
# 이 진동은 $\lambda_2$가 **음수**여서 $(\lambda_2/\lambda_1)^k$의 부호가 매 회 뒤집히기 때문이다(4절에서 확인).
#
# 순위는 `n1 > n2 = n3 > n4`. 차수 순위(`3, 2, 2, 1`)와 같지만,
# n4는 차수 비율로는 $1/3 = 0.333$인데 고유벡터로는 $0.4608$이다.
# **"중요한 이웃(n1)을 하나 가졌다"는 점이 값을 끌어올렸다.**

# %% [markdown]
# ## 3. numpy 고유벡터와 대조
#
# 멱반복이 정말 $A\mathbf{x}=\lambda\mathbf{x}$의 주고유벡터를 뽑았는지 확인한다.
# `np.linalg.eigh`(대칭행렬용)는 $L^2$ 정규화를 하므로, 비교하려면 **정규화를 맞춰야** 한다.

# %%
w, V = np.linalg.eigh(A)                 # 오름차순 고윳값
order = np.argsort(w)[::-1]
w, V = w[order], V[:, order]

lam1, lam2 = w[0], w[1]
v1 = V[:, 0]
if v1.sum() < 0:
    v1 = -v1                             # 부호는 자유 → 양수 쪽으로

print("고윳값 전체 :", w)
print("λ1 =", round(lam1, 6), " λ2 =", round(lam2, 6))
print()
print("numpy v1 (L2 정규화) :", v1)
print("numpy v1 (max 정규화):", v1 / v1.max())
print("멱반복 결과          :", x_star)
print("최대 오차            :", np.abs(v1 / v1.max() - x_star).max())
print()
print("검산  A x =", A @ x_star)
print("검산 λ1 x =", lam1 * x_star)
# 출력: 고윳값 전체 : [ 2.1701  0.3111 -1.      -1.4812]
# 출력: λ1 = 2.170086  λ2 = 0.311108
# 출력:
# 출력: numpy v1 (L2 정규화) : [0.6116 0.5227 0.5227 0.2818]
# 출력: numpy v1 (max 정규화): [1.     0.8546 0.8546 0.4608]
# 출력: 멱반복 결과          : [1.     0.8546 0.8546 0.4608]
# 출력: 최대 오차            : 3.2718272535703363e-13
# 출력:
# 출력: 검산  A x = [2.1701 1.8546 1.8546 1.    ]
# 출력: 검산 λ1 x = [2.1701 1.8546 1.8546 1.    ]

# %% [markdown]
# 소수점 13자리까지 일치한다. **멱반복 = 주고유벡터**가 맞다.
#
# 그리고 페론–프로베니우스 정리가 말한 대로,
# - $\lambda_1 = 2.1701$은 **실수·양수**이고 다른 고윳값보다 절댓값이 크며,
# - 그 고유벡터는 **모든 성분이 양수**다.
#
# 나머지 고유벡터들은 어떤지 보자.

# %%
for i in range(len(w)):
    v = V[:, i]
    sign = "양수만" if (v > 1e-12).all() or (v < -1e-12).all() else "부호 섞임 ✗"
    print(f"λ={w[i]:>8.4f}  v={np.round(v, 4)}  → {sign}")
# 출력: λ=  2.1701  v=[0.6116 0.5227 0.5227 0.2818]  → 양수만
# 출력: λ=  0.3111  v=[-0.2536  0.3682  0.3682 -0.8152]  → 부호 섞임 ✗
# 출력: λ= -1.0000  v=[ 0.      0.7071 -0.7071 -0.    ]  → 부호 섞임 ✗
# 출력: λ= -1.4812  v=[ 0.7494 -0.302  -0.302  -0.5059]  → 부호 섞임 ✗

# %% [markdown]
# **주고유벡터만 부호가 하나로 통일**되어 있다. 나머지는 "음수 중심성"이라 해석이 불가능하다.
# 그래서 고유벡터 중심성은 반드시 최대 고윳값 쪽을 쓴다.

# %% [markdown]
# ## 4. 수렴 속도는 $\left|\lambda_2/\lambda_1\right|^k$
#
# 시작 벡터를 고유벡터들의 합으로 쪼개면
#
# $$
# A^k\mathbf{x}^{(0)} = \lambda_1^{k}\Big[c_1\mathbf{v}_1
# + \sum_{i\ge 2} c_i\Big(\tfrac{\lambda_i}{\lambda_1}\Big)^{k}\mathbf{v}_i\Big]
# $$
#
# 괄호 안 뒷항은 공비 $\lambda_i/\lambda_1$ 인 등비수열이므로 0으로 사라진다.
# 즉 오차는 **$\left|\lambda_2/\lambda_1\right|^k$ 로 지수 감소**한다.
#
# 이 그래프에서 절댓값 2등 고윳값은 $0.3111$이 아니라 $-1.4812$임에 주의.
# 수렴을 지배하는 건 **절댓값**이다.

# %%
target = v1 / v1.max()
err = np.abs(hist - target).max(axis=1)

ratio = abs(w[np.argsort(np.abs(w))[::-1][1]]) / abs(lam1)   # |λ_(2nd by abs)| / |λ1|
print(f"절댓값 기준 2등 고윳값 = {w[np.argsort(np.abs(w))[::-1][1]]:.4f}")
print(f"수렴비 |λ2/λ1| = {ratio:.4f}")
print()
print(f"{'k':>3} {'실제 오차':>12} {'예측 C·r^k':>12}")
C = err[1] / ratio
for k in range(1, 11):
    print(f"{k:>3} {err[k]:>12.6f} {C * ratio**k:>12.6f}")
# 출력: 절댓값 기준 2등 고윳값 = -1.4812
# 출력: 수렴비 |λ2/λ1| = 0.6826
# 출력:
# 출력:   k    실제 오차   예측 C·r^k
# 출력:   1     0.187971     0.187971
# 출력:   2     0.145362     0.128300
# 출력:   3     0.085407     0.087571
# 출력:   4     0.065362     0.059772
# 출력:   5     0.041078     0.040797
# 출력:   6     0.029660     0.027846
# 출력:   7     0.019473     0.019006
# 출력:   8     0.013647     0.012973
# 출력:   9     0.009147     0.008855
# 출력:  10     0.006321     0.006044

# %% [markdown]
# 실제 오차가 예측 등비수열과 같은 기울기로 떨어진다(회차별 진동 때문에 살짝 요철이 있다).
#
# **스펙트럼 갭**($\lambda_1$과 $|\lambda_2|$의 벌어짐)이 클수록 빨리 수렴한다.
# 비율이 0.68이면 40회면 충분하지만, 0.99면 수천 회가 필요하다.

# %% [markdown]
# ## 5. 실패 사례 (1) — 이분 그래프의 진동
#
# 무향 그래프가 **이분(bipartite)** 이면 스펙트럼이 0 대칭이라 $\lambda_n = -\lambda_1$,
# 즉 $|\lambda_1| = |\lambda_2|$ 가 되어 **부등호 조건이 깨진다**.
#
# 가장 작은 예: 노드 두 개, 엣지 하나.
# $A=\begin{pmatrix}0&1\\1&0\end{pmatrix}$, 고윳값 $\pm 1$.

# %%
B = np.array([[0.0, 1.0], [1.0, 0.0]])
print("고윳값:", np.linalg.eigvalsh(B))

x = np.array([1.0, 0.0])
print("\nx0 =", x)
for k in range(1, 7):
    y = B @ x
    x = y / y.max()
    print(f"x{k} = {x}")
print("\n→ 영원히 진동. 절대 수렴하지 않는다.")
# 출력: 고윳값: [-1.  1.]
# 출력:
# 출력: x0 = [1. 0.]
# 출력: x1 = [0. 1.]
# 출력: x2 = [1. 0.]
# 출력: x3 = [0. 1.]
# 출력: x4 = [1. 0.]
# 출력: x5 = [0. 1.]
# 출력: x6 = [1. 0.]
# 출력:
# 출력: → 영원히 진동. 절대 수렴하지 않는다.

# %% [markdown]
# ### 고치는 법: shifted power iteration
#
# $A$ 대신 $A+I$ 에 멱반복을 돌린다. 고윳값만 1씩 밀리고 **고유벡터는 그대로**다.
#
# $$(A+I)\mathbf{x} = A\mathbf{x}+\mathbf{x} = (\lambda+1)\mathbf{x}$$
#
# $\pm 1 \to 2, 0$ 이 되어 절댓값 동점이 깨진다.

# %%
Bs = B + np.eye(2)
print("A+I 고윳값:", np.linalg.eigvalsh(Bs))

x = np.array([1.0, 0.0])
for k in range(1, 7):
    y = Bs @ x
    x = y / y.max()
    print(f"x{k} = {np.round(x, 6)}")
print("→ 즉시 (1, 1) 로 수렴. 대칭인 두 노드가 같은 점수를 받는 게 맞다.")
# 출력: A+I 고윳값: [0. 2.]
# 출력: x1 = [1. 1.]
# 출력: x2 = [1. 1.]
# 출력: x3 = [1. 1.]
# 출력: x4 = [1. 1.]
# 출력: x5 = [1. 1.]
# 출력: x6 = [1. 1.]
# 출력: → 즉시 (1, 1) 로 수렴. 대칭인 두 노드가 같은 점수를 받는 게 맞다.

# %% [markdown]
# ## 6. 실패 사례 (2) — 끊어진 그래프 (기약성 위반)
#
# 페론–프로베니우스는 그래프가 **연결(기약, irreducible)** 일 때만 유일한 양수 해를 보증한다.
# 삼각형 하나 + 떨어진 엣지 하나를 붙여 보자.

# %%
# 노드 0,1,2 = 삼각형(λ1=2) / 노드 3,4 = 엣지 하나(λ1=1)
C2 = np.zeros((5, 5))
for a, b in [(0, 1), (1, 2), (0, 2), (3, 4)]:
    C2[a, b] = C2[b, a] = 1.0

xc, _, it = power_iteration(C2)
print("고윳값:", np.round(np.linalg.eigvalsh(C2), 4))
print(f"멱반복 결과 ({it}회):", np.round(xc, 6))
print("→ 떨어진 조각(노드 3,4)이 통째로 0점. 「그 팀은 전원 무의미」라는 보고서가 된다.")
# 출력: 고윳값: [-1. -1. -1.  1.  2.]
# 출력: 멱반복 결과 (40회): [1. 1. 1. 0. 0.]
# 출력: → 떨어진 조각(노드 3,4)이 통째로 0점. 「그 팀은 전원 무의미」라는 보고서가 된다.

# %% [markdown]
# 두 조각의 $\lambda_1$이 **같으면** 더 나쁘다. 고유공간이 2차원이 되어 답이 유일하지 않고,
# 시작 벡터에 따라 순위가 바뀐다. 삼각형 두 개를 떼어 놓고 확인한다.

# %%
C3 = np.zeros((6, 6))
for a, b in [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5)]:
    C3[a, b] = C3[b, a] = 1.0

for start in ([1, 1, 1, 1, 1, 1], [1, 1, 1, 0.1, 0.1, 0.1], [0.1, 0.1, 0.1, 1, 1, 1]):
    x = np.array(start, dtype=float)
    for _ in range(200):
        x = (C3 @ x) / (C3 @ x).max()
    print(f"시작 {start} → {np.round(x, 4)}")
print("→ 시작 벡터에 따라 답이 달라진다. 유일성이 깨졌다 (λ1=2 가 중복).")
print("실무 규칙: 연결 요소(connected component)별로 따로 계산할 것.")
# 출력: 시작 [1, 1, 1, 1, 1, 1] → [1. 1. 1. 1. 1. 1.]
# 출력: 시작 [1, 1, 1, 0.1, 0.1, 0.1] → [1.  1.  1.  0.1 0.1 0.1]
# 출력: 시작 [0.1, 0.1, 0.1, 1, 1, 1] → [0.1 0.1 0.1 1.  1.  1. ]
# 출력: → 시작 벡터에 따라 답이 달라진다. 유일성이 깨졌다 (λ1=2 가 중복).
# 출력: 실무 규칙: 연결 요소(connected component)별로 따로 계산할 것.

# %% [markdown]
# ## 7. 10장 회사 그래프 — 차수와 고유벡터는 다른 사람을 가리킨다
#
# `org.py` 의 EDGES 를 그대로 쓴다. 일부러 세 사람을 심어 둔 데이터다.
#
# - **김개발**: 아는 사람이 제일 많다 (차수 1등)
# - **서영업**: 외주 공장으로 가는 유일한 통로다 (매개 1등)
# - **대표**: 힘 있는 사람들과만 이어져 있다

# %%
EDGES = [
    ("김개발", "개발1"), ("김개발", "개발2"), ("김개발", "개발3"),
    ("김개발", "개발4"), ("김개발", "개발5"), ("김개발", "개발6"),
    ("개발1", "개발2"), ("개발2", "개발3"), ("개발3", "개발4"),
    ("개발4", "개발5"), ("개발5", "개발6"),
    ("정영업", "한영업"), ("정영업", "오영업"), ("정영업", "서영업"),
    ("한영업", "오영업"), ("오영업", "서영업"),
    ("강디자", "윤디자"), ("강디자", "임디자"), ("윤디자", "임디자"),
    ("대표", "김개발"), ("대표", "정영업"), ("대표", "강디자"),
    ("서영업", "공장A"),
    ("공장A", "공장B"), ("공장A", "공장C"), ("공장B", "공장C"),
    ("청소담당", "개발1"), ("청소담당", "윤디자"),
]

names = sorted({x for e in EDGES for x in e})
idx = {v: i for i, v in enumerate(names)}
M = np.zeros((len(names), len(names)))
for a, b in EDGES:
    M[idx[a], idx[b]] = M[idx[b], idx[a]] = 1.0

eig_pi, hist_org, it_org = power_iteration(M, rounds=500)
deg = M.sum(axis=1)
deg_c = deg / (len(names) - 1)

w_org = np.linalg.eigvalsh(M)[::-1]
gap = abs(w_org[1]) / abs(w_org[0])
print(f"노드 {len(names)}개, 수렴 {it_org}회, λ1={w_org[0]:.4f}, |λ2/λ1|={gap:.4f}\n")

print(f"{'노드':<10}{'차수':>6}{'차수중심성':>12}{'고유벡터':>12}")
print("-" * 42)
for v in sorted(names, key=lambda v: -eig_pi[idx[v]]):
    print(f"{v:<10}{int(deg[idx[v]]):>6}{deg_c[idx[v]]:>12.3f}{eig_pi[idx[v]]:>12.4f}")
# 출력: 노드 19개, 수렴 104회, λ1=3.6146, |λ2/λ1|=0.7782
# 출력:
# 출력: 노드            차수       차수중심성        고유벡터
# 출력: ------------------------------------------
# 출력: 김개발            7       0.389      1.0000
# 출력: 개발3            3       0.167      0.6016
# 출력: 개발4            3       0.167      0.5985
# 출력: 개발2            3       0.167      0.5761
# 출력: 개발5            3       0.167      0.5618
# 출력: 개발1            3       0.167      0.4809
# 출력: 개발6            2       0.111      0.4321
# 출력: 대표             3       0.167      0.3636
# 출력: 정영업            4       0.222      0.1649
# 출력: 청소담당           2       0.111      0.1623
# 출력: 강디자            3       0.167      0.1494
# 출력: 윤디자            3       0.167      0.1058
# 출력: 오영업            3       0.167      0.0861
# 출력: 서영업            3       0.167      0.0769
# 출력: 임디자            2       0.111      0.0706
# 출력: 한영업            2       0.111      0.0694
# 출력: 공장A            3       0.167      0.0270
# 출력: 공장B            2       0.111      0.0103
# 출력: 공장C            2       0.111      0.0103

# %% [markdown]
# 읽는 법:
#
# - **김개발 1.0000** — 차수도 1등, 고유벡터도 1등. 개발팀 6명이 서로 붙어 있고 그 한가운데다.
# - **개발3 (차수 3) 0.6016 vs 정영업 (차수 4) 0.1649** — **차수가 더 낮은데 고유벡터가 3.6배다.**
#   개발3의 이웃이 "김개발"이라는 거물이기 때문. 이게 이 지표의 정체다.
# - **개발6은 차수가 2로 개발1~5보다 적은데도 0.4321** 로 대표(차수 3, 0.3636)를 앞선다.
#   이웃 수가 아니라 이웃의 질이 순위를 정한다.
# - **서영업 0.0769** — 매개 중심성 1등(공장 가는 유일한 길)인데 고유벡터는 하위권.
#   이웃(정영업·오영업·공장A)이 안 중요하니까. **구조적 급소는 이 지표로 절대 안 잡힌다.**
# - **공장A/B/C는 0.03 이하** — 김개발 덩어리에서 멀수록 값이 지수적으로 죽는다.
# - **|λ2/λ1| = 0.7782** 라 수렴에 104회 걸렸다. 커뮤니티가 뚜렷할수록 갭이 좁고 느리다.
#
# 고유벡터 중심성은 **밀집한 덩어리 안쪽을 편애**한다. 지표는 질문에 맞춰 고르는 것이다.

# %% [markdown]
# ## 8. 시각화
#
# 네 개의 패널로 정리한다.
#
# 1. 장난감 그래프의 회차별 벡터 변화 (목표값으로 수렴)
# 2. 오차의 지수 감소 (로그 축) vs 예측 $\left|\lambda_2/\lambda_1\right|^k$
# 3. 이분 그래프의 진동 (수렴 실패)
# 4. 회사 그래프에서 차수 중심성 vs 고유벡터 중심성 (순위가 갈리는 지점)

# %%
K = 25
fig = make_subplots(
    rows=2,
    cols=2,
    subplot_titles=(
        "① 멱반복 회차별 벡터 (점선 = 주고유벡터)",
        "② 오차의 지수 감소  |λ₂/λ₁|ᵏ",
        "③ 이분 그래프: 영원히 진동 (수렴 실패)",
        "④ 회사 그래프: 차수 vs 고유벡터",
    ),
    vertical_spacing=0.14,
    horizontal_spacing=0.10,
)

palette = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]

# ① 회차별 벡터
for i, nm in enumerate(NODES):
    fig.add_trace(
        go.Scatter(
            x=list(range(min(K, len(hist)))),
            y=hist[:K, i],
            mode="lines+markers",
            name=nm,
            line=dict(color=palette[i], width=2),
            marker=dict(size=5),
        ),
        row=1, col=1,
    )
    fig.add_hline(y=target[i], line=dict(color=palette[i], dash="dot", width=1), row=1, col=1)

# ② 오차 감소
fig.add_trace(
    go.Scatter(x=list(range(1, K)), y=err[1:K], mode="lines+markers",
               name="실제 오차", line=dict(color="#C44E52", width=2)),
    row=1, col=2,
)
fig.add_trace(
    go.Scatter(x=list(range(1, K)), y=[C * ratio**k for k in range(1, K)],
               mode="lines", name=f"C·{ratio:.3f}ᵏ",
               line=dict(color="#555555", dash="dash", width=2)),
    row=1, col=2,
)

# ③ 이분 그래프 진동
xb = np.array([1.0, 0.0])
osc = [xb.copy()]
for _ in range(14):
    yb = B @ xb
    xb = yb / yb.max()
    osc.append(xb.copy())
osc = np.array(osc)
for i, nm in enumerate(["a", "b"]):
    fig.add_trace(
        go.Scatter(x=list(range(len(osc))), y=osc[:, i], mode="lines+markers",
                   name=f"이분·{nm}", line=dict(color=palette[i], width=2)),
        row=2, col=1,
    )

# ④ 회사 그래프 비교
order_org = sorted(names, key=lambda v: -eig_pi[idx[v]])
fig.add_trace(
    go.Bar(x=order_org, y=[deg_c[idx[v]] for v in order_org],
           name="차수 중심성", marker_color="#B0B0B0"),
    row=2, col=2,
)
fig.add_trace(
    go.Bar(x=order_org, y=[eig_pi[idx[v]] for v in order_org],
           name="고유벡터 중심성", marker_color="#4C72B0"),
    row=2, col=2,
)

fig.update_yaxes(title_text="x 값", row=1, col=1)
fig.update_xaxes(title_text="반복 회차 k", row=1, col=1)
fig.update_yaxes(title_text="최대 오차 (log)", type="log", row=1, col=2)
fig.update_xaxes(title_text="반복 회차 k", row=1, col=2)
fig.update_yaxes(title_text="x 값", row=2, col=1)
fig.update_xaxes(title_text="반복 회차 k", row=2, col=1)
fig.update_yaxes(title_text="중심성 (최댓값 정규화)", row=2, col=2)
fig.update_xaxes(tickangle=-45, row=2, col=2)

fig.update_layout(
    height=820, width=1280,
    title_text="고유벡터 중심성 — 멱반복의 수렴, 실패, 그리고 차수와의 차이",
    template="plotly_white",
    barmode="group",
    legend=dict(orientation="h", yanchor="bottom", y=-0.13, xanchor="center", x=0.5),
)

_show(fig)
fig.write_image("expy.png", scale=2)
print("saved expy.png")
# 출력: saved expy.png

# %% [markdown]
# ## 정리
#
# | 항목 | 내용 |
# |---|---|
# | 원리 | 중요한 이웃을 가진 노드가 중요하다 |
# | 식 | $\lambda x_v=\sum_{u\in N(v)}x_u$, 즉 $A\mathbf{x}=\lambda\mathbf{x}$ |
# | 계산 | 멱반복: $\mathbf{x}\leftarrow A\mathbf{x}$, 최댓값 정규화, 수렴까지 반복 |
# | 비용 | 1회 $O(E)$ — 인접 리스트로 곱하면 행렬을 만들 필요가 없다 |
# | 보증 | 페론–프로베니우스: 연결(기약) 그래프면 양수 해가 유일 |
# | 속도 | $\lvert\lambda_2/\lambda_1\rvert^k$ — 스펙트럼 갭이 좁으면 느리다 |
# | 실패 | 이분 그래프(진동 → $A+I$ 로 shift), 비연결(0점 연쇄 → 요소별 계산) |
# | 성향 | 밀집한 덩어리 안쪽을 편애. 구조적 급소(매개 1등)는 못 잡는다 |
