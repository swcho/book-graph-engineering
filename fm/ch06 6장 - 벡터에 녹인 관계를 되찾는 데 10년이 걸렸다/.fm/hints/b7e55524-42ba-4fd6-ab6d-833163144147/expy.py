# %% [markdown]
# # `layer()` 는 무엇을 계산하는가 — 행렬로 다시 쓰고, 진짜 GCN 과 나란히 놓기
#
# `content/ch06/code/ex3_message_passing.py` 의 `layer()` 는 한 줄로 말하면
# **「자기 벡터」와 「이웃 벡터의 평균」의 가중합**이다.
#
# $$h_i^{(l+1)} = w_s\, h_i^{(l)} + w_n \cdot \frac{1}{|N(i)|}\sum_{j \in N(i)} h_j^{(l)}$$
#
# 기본값은 $w_s = w_n = 0.5$. 이 노트북에서 확인할 것:
#
# 1. 파이썬 `dict` 루프를 **행렬 한 줄** $H^{(l+1)} = w_s H^{(l)} + w_n \hat{A} H^{(l)}$ 로 바꿔도 값이 같다.
# 2. 층을 쌓는 것은 **행렬 거듭제곱** $H^{(l)} = S^l H^{(0)}$ 이다 (비선형이 없으니까).
# 3. $S$ 가 행 확률행렬이라 $l \to \infty$ 면 **모든 노드가 같은 값**으로 수렴한다 = 과평활.
# 4. 진짜 GCN 은 여기에 **학습 가중치 $W$**, **비선형 $\sigma$**, **대칭 정규화**가 붙는다.

# %%
from collections import defaultdict

import numpy as np

np.set_printoptions(precision=3, suppress=True)


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# ex3_message_passing.py 와 똑같은 그래프·특징
EDGES = [("A", "B"), ("B", "C"), ("C", "D"), ("A", "E"), ("E", "F"), ("B", "E")]
FEAT = {"A": [4.0, 2.0], "B": [1.0, 5.0], "C": [0.0, 3.0],
        "D": [2.0, 1.0], "E": [3.0, 4.0], "F": [0.0, 2.0]}
NODES = sorted(FEAT)


def adjacency(edges):
    adj = defaultdict(set)
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    return adj


ADJ = adjacency(EDGES)
print("이웃 목록:", {k: sorted(ADJ[k]) for k in NODES})
print("차수 d_i:", {k: len(ADJ[k]) for k in NODES})

# 출력: 이웃 목록: {'A': ['B', 'E'], 'B': ['A', 'C', 'E'], 'C': ['B', 'D'], 'D': ['C'], 'E': ['A', 'B', 'F'], 'F': ['E']}
# 출력: 차수 d_i: {'A': 2, 'B': 3, 'C': 2, 'D': 1, 'E': 3, 'F': 1}

# %% [markdown]
# ## 1. 원본 `layer()` — dict 루프 그대로
#
# 눈여겨볼 점 두 가지.
#
# - 이웃 평균은 **자기 자신을 빼고** 낸다 ($j \in N(i)$, self-loop 없음).
# - 갱신은 전부 **입력 `feat` 만 읽어서** 만든다. 즉 동기 갱신(Jacobi)이지,
#   방금 고친 값을 다시 쓰는 순차 갱신(Gauss–Seidel)이 아니다.
# - 이웃이 없는 고립 노드는 평균이 $0$ 벡터라 $h_i^{(l+1)} = w_s h_i^{(l)}$, 즉 그냥 줄어든다.

# %%
def layer(feat, adj, w_self=0.5, w_nbr=0.5):
    """ex3_message_passing.py 원본 그대로."""
    out = {}
    for n, v in feat.items():
        nbrs = adj[n]
        if nbrs:
            avg = [sum(feat[m][i] for m in nbrs) / len(nbrs) for i in range(len(v))]
        else:
            avg = [0.0] * len(v)
        out[n] = [round(w_self * v[i] + w_nbr * avg[i], 3) for i in range(len(v))]
    return out


f1 = layer(FEAT, ADJ)
f2 = layer(f1, ADJ)
for name, f in [("0층", FEAT), ("1층", f1), ("2층", f2)]:
    print(name, {n: f[n] for n in NODES})

# 출력: 0층 {'A': [4.0, 2.0], 'B': [1.0, 5.0], 'C': [0.0, 3.0], 'D': [2.0, 1.0], 'E': [3.0, 4.0], 'F': [0.0, 2.0]}
# 출력: 1층 {'A': [3.0, 3.25], 'B': [1.667, 4.0], 'C': [0.75, 3.0], 'D': [1.0, 2.0], 'E': [2.333, 3.5], 'F': [1.5, 3.0]}
# 출력: 2층 {'A': [2.5, 3.5], 'B': [1.847, 3.625], 'C': [1.042, 3.0], 'D': [0.875, 2.5], 'E': [2.194, 3.458], 'F': [1.917, 3.25]}

# %% [markdown]
# ## 2. 손으로 한 노드만 확인 — D 노드
#
# $D$ 의 이웃은 $C$ 하나뿐이다. 그래서 1층 계산은
#
# $$h_D^{(1)} = 0.5 \cdot [2,\,1] + 0.5 \cdot [0,\,3] = [1.0,\,2.0]$$
#
# 2층에서는 $C$ 의 1층 값 $[0.75, 3.0]$ 이 들어온다. 그런데 $C$ 의 1층 값 안에는
# 이미 $B$ 가 섞여 있다. 그래서 **2층이면 2홉 정보가 도착**한다. $A$ 와 $D$ 는 3홉이라
# 아직 안 닿는다.

# %%
h_D0, h_C0 = np.array(FEAT["D"]), np.array(FEAT["C"])
print("D 1층 =", 0.5 * h_D0 + 0.5 * h_C0)
print("D 2층 =", 0.5 * np.array(f1["D"]) + 0.5 * np.array(f1["C"]))
print("2층 D 에 B 가 실제로 기여했나:", "B" in ADJ["C"])

# 출력: D 1층 = [1. 2.]
# 출력: D 2층 = [0.875 2.5  ]
# 출력: 2층 D 에 B 가 실제로 기여했나: True

# %% [markdown]
# ## 3. 행렬 형태로 일반화
#
# 노드를 행, 특징을 열로 쌓은 행렬 $H^{(l)} \in \mathbb{R}^{n \times d}$ 를 두자.
# 인접행렬 $A$ ($A_{ij}=1$ 이면 연결), 차수 대각행렬 $D = \mathrm{diag}(d_1,\dots,d_n)$ 에 대해
# **행 정규화 인접행렬**을 정의한다.
#
# $$\hat{A} = D^{-1} A, \qquad (\hat{A} H)_i = \frac{1}{d_i}\sum_{j \in N(i)} h_j$$
#
# $\hat{A}H$ 의 $i$ 행이 곧 「$i$ 의 이웃 평균」이다. 그러면 `layer()` 전체가 한 줄이 된다.
#
# $$\boxed{\;H^{(l+1)} = w_s H^{(l)} + w_n \hat{A} H^{(l)} = \underbrace{(w_s I + w_n \hat{A})}_{=\,S} H^{(l)}\;}$$
#
# $S$ 는 **그래프만으로 정해지는 고정 연산자**다. 특징이 무엇이든 바뀌지 않는다.

# %%
n = len(NODES)
idx = {v: i for i, v in enumerate(NODES)}
A = np.zeros((n, n))
for a, b in EDGES:
    A[idx[a], idx[b]] = A[idx[b], idx[a]] = 1.0
deg = A.sum(1)
A_hat = A / deg[:, None]              # D^{-1} A : 행 정규화
W_S, W_N = 0.5, 0.5
S = W_S * np.eye(n) + W_N * A_hat     # 전파 연산자

H0 = np.array([FEAT[v] for v in NODES])
H1, H2 = S @ H0, S @ (S @ H0)

print("S =\n", S)
print("행 합(모두 1이어야 함):", S.sum(1))
print("\n행렬 1층:\n", H1)
print("dict 1층과 최대 차이:", np.abs(H1 - np.array([f1[v] for v in NODES])).max())
print("dict 2층과 최대 차이:", np.abs(H2 - np.array([f2[v] for v in NODES])).max())

# 출력: S =
# 출력:  [[0.5   0.25  0.    0.    0.25  0.   ]
# 출력:  [0.167 0.5   0.167 0.    0.167 0.   ]
# 출력:  [0.    0.25  0.5   0.25  0.    0.   ]
# 출력:  [0.    0.    0.5   0.5   0.    0.   ]
# 출력:  [0.167 0.167 0.    0.    0.5   0.167]
# 출력:  [0.    0.    0.    0.    0.5   0.5  ]
# 출력: 행 합(모두 1이어야 함): [1. 1. 1. 1. 1. 1.]
# 출력: 행렬 1층:
# 출력:  [[3.    3.25 ] [1.667 4.   ] [0.75  3.   ] [1.    2.   ] [2.333 3.5  ] [1.5   3.   ]]
# 출력: dict 1층과 최대 차이: 0.000333  (원본의 round(...,3) 때문, 값은 동일)
# 출력: dict 2층과 최대 차이: 0.000444

# %% [markdown]
# ## 4. 층 쌓기 = 행렬 거듭제곱, 그리고 과평활
#
# `layer()` 에는 비선형이 없다. 그래서 $l$ 층은 그냥
#
# $$H^{(l)} = S^l H^{(0)}$$
#
# 이다. **$L$ 층을 쌓아도 결국 선형 변환 하나**라는 뜻이고, 이게 진짜 GNN 과의 첫 번째 차이다.
#
# $S$ 는 행 합이 1인 확률행렬(게으른 무작위 보행, lazy random walk)이다. 그래프가 연결되어 있으면
# $S^l \to \mathbf{1}\pi^\top$ 로 수렴하고, 정상분포는 차수에 비례한다.
#
# $$\pi_i = \frac{d_i}{\sum_j d_j} = \frac{d_i}{2m}$$
#
# 즉 **모든 노드가 「차수로 가중한 전체 평균」이라는 똑같은 한 점으로 빨려 들어간다.**
# 이것이 과평활(over-smoothing)의 정체다.

# %%
pi = deg / deg.sum()
limit = pi @ H0                       # 모든 노드가 수렴할 값
print("정상분포 π =", pi)
print("수렴 목적지 =", limit)

traj = [H0]
for _ in range(30):
    traj.append(S @ traj[-1])
traj = np.array(traj)                 # (층, 노드, 특징)

for l in [0, 1, 2, 5, 10, 30]:
    spread = traj[l].std(0).mean()
    print(f"{l:2d}층  A={traj[l][0]}  퍼짐(노드간 표준편차)={spread:.4f}")

# 출력: 정상분포 π = [0.167 0.25  0.167 0.083 0.25  0.083]
# 출력: 수렴 목적지 = [1.833 3.333]
# 출력:  0층  A=[4. 2.]      퍼짐(노드간 표준편차)=1.4172
# 출력:  1층  A=[3.   3.25]   퍼짐(노드간 표준편차)=0.6873
# 출력:  2층  A=[2.5 3.5]     퍼짐(노드간 표준편차)=0.4832
# 출력:  5층  A=[2.062 3.461] 퍼짐(노드간 표준편차)=0.2713
# 출력: 10층  A=[1.917 3.378] 퍼짐(노드간 표준편차)=0.1221
# 출력: 30층  A=[1.837 3.335] 퍼짐(노드간 표준편차)=0.0052

# %% [markdown]
# ### 수렴 속도는 고윳값이 정한다 — $w_s$ 의 진짜 역할
#
# $\hat{A}$ 의 고윳값을 $\mu$ 라 하면 $S = w_s I + w_n \hat{A}$ 의 고윳값은
#
# $$\lambda = w_s + (1 - w_s)\,\mu \qquad (w_n = 1 - w_s)$$
#
# 즉 **$w_s$ 는 모든 고윳값을 1 쪽으로 끌어당기는 손잡이**다. $\mu_1 = 1$ 은 그대로 1,
# 나머지는 1 에 가까워진다. 층마다 신호가 $|\lambda_2|$ 배씩 줄어드니 $w_s$ 를 키우면
# 과평활이 느려진다 — 잔차 연결(residual)이 노리는 효과가 이것이다.
#
# 덤으로 $w_s > 0$ 은 음수 고윳값($\mu \approx -0.86$)도 0 근처로 밀어내
# 진동(이분 그래프에서 값이 좌우로 튀는 현상)을 없앤다. 이게 「게으른(lazy)」 보행의 뜻이다.

# %%
mu = np.sort(np.linalg.eigvals(A_hat).real)[::-1]
print("Â 의 고윳값 μ =", np.round(mu, 3))
for ws in [0.0, 0.5, 0.9]:
    lam = np.sort(np.abs(ws + (1 - ws) * mu))[::-1]
    print(f"w_self={ws:.1f}  |λ| 상위 3 = {np.round(lam[:3], 3)}"
          f"  → 10층 뒤 잔여 신호 ≈ {lam[1] ** 10:.4f}")

# 출력: Â 의 고윳값 μ = [ 1.     0.707  0.194 -0.333 -0.707 -0.86 ]
# 출력: w_self=0.0  |λ| 상위 3 = [1.    0.86  0.707]  → 10층 뒤 잔여 신호 ≈ 0.2223
# 출력: w_self=0.5  |λ| 상위 3 = [1.    0.854 0.597]  → 10층 뒤 잔여 신호 ≈ 0.2053
# 출력: w_self=0.9  |λ| 상위 3 = [1.    0.971 0.919]  → 10층 뒤 잔여 신호 ≈ 0.7428
# 출력: (w_s=0 일 때 2등은 μ=-0.86 에서 온 «진동» 성분이다. w_s=0.5 면 그게 0.07 로 죽고,
# 출력:  w_s=0.9 면 모든 |λ| 가 1 에 붙어 30층을 가도 값이 안 뭉갠다.)

# %% [markdown]
# ## 5. 진짜 GCN 과 무엇이 다른가
#
# Kipf & Welling (2017) 의 GCN 한 층은 이렇다.
#
# $$H^{(l+1)} = \sigma\!\left( \tilde{D}^{-1/2}\tilde{A}\tilde{D}^{-1/2}\, H^{(l)} W^{(l)} \right),
# \qquad \tilde{A} = A + I$$
#
# `layer()` 와 비교하면 차이는 정확히 세 가지다.
#
# | 항목 | `layer()` | GCN |
# |---|---|---|
# | 이웃 섞는 법 | $w_s I + w_n D^{-1}A$ (자기/이웃 비중을 사람이 정함) | $\tilde{D}^{-1/2}\tilde{A}\tilde{D}^{-1/2}$ (self-loop 를 넣고 **대칭** 정규화) |
# | 특징 변환 | 없음 (항등, 차원 고정) | $W^{(l)}$ — **학습되는** 가중치, 차원도 바꿈 |
# | 비선형 | 없음 (층 = 선형) | $\sigma$ = ReLU 등 |
#
# ### (a) 대칭 정규화의 계수
#
# $$\left(\tilde{D}^{-1/2}\tilde{A}\tilde{D}^{-1/2}\right)_{ij} = \frac{1}{\sqrt{(d_i+1)(d_j+1)}}$$
#
# - 자기 자신 계수는 $1/(d_i+1)$ — **차수마다 다르다.** `layer()` 의 $w_s=0.5$ 는 모든 노드에 똑같다.
# - 이웃 계수가 **보내는 쪽 차수 $d_j$ 에도 반비례**한다. 인기 노드(허브)의 목소리가 자동으로 작아진다.
#   `layer()` 의 평균은 받는 쪽 차수만 본다.
# - 행렬이 대칭이라 고윳값이 실수 $[-1, 1]$ 안에 들어와 스펙트럼 해석·수치 안정성이 좋다.

# %%
A_tilde = A + np.eye(n)
d_tilde = A_tilde.sum(1)
D_inv_sqrt = np.diag(1.0 / np.sqrt(d_tilde))
S_gcn = D_inv_sqrt @ A_tilde @ D_inv_sqrt

print("S_gcn =\n", S_gcn)
print("대칭인가:", np.allclose(S_gcn, S_gcn.T), " | 행 합:", np.round(S_gcn.sum(1), 3))
print("\n노드별 «자기 자신» 계수")
print("  layer()    :", {v: W_S for v in NODES})
print("  GCN 1/(d+1):", {v: round(float(1 / (deg[idx[v]] + 1)), 3) for v in NODES})

# 출력: S_gcn =
# 출력:  [[0.333 0.289 0.    0.    0.289 0.   ]
# 출력:  [0.289 0.25  0.289 0.    0.25  0.   ]
# 출력:  [0.    0.289 0.333 0.408 0.    0.   ]
# 출력:  [0.    0.    0.408 0.5   0.    0.   ]
# 출력:  [0.289 0.25  0.    0.    0.25  0.354]
# 출력:  [0.    0.    0.    0.    0.354 0.5  ]
# 출력: 대칭인가: True  | 행 합: [0.911 1.077 1.03  0.908 1.142 0.854]
# 출력: (행 합이 1이 아니다 — 대칭 정규화는 확률행렬이 아니다. 평균이 아니라 «필터»다)
# 출력: 노드별 «자기 자신» 계수
# 출력:   layer()    : 전부 0.5
# 출력:   GCN 1/(d+1): {'A': 0.333, 'B': 0.25, 'C': 0.333, 'D': 0.5, 'E': 0.25, 'F': 0.5}

# %% [markdown]
# ### (b) 학습 가중치 $W$ — 「무엇을 섞을지」가 아니라 「섞은 걸 어떻게 볼지」
#
# $S$ 는 **어디서 정보를 가져올지**만 정한다. $W$ 는 **가져온 특징을 어떤 축으로 다시 볼지**를 학습한다.
# 여기서는 학습 대신 손으로 정한 $W$ 를 꽂아 두 칸(장애 횟수, 팀 규모)을
# 「위험 점수 $=$ 장애 $-\,0.5\times$ 팀규모」 한 칸으로 눌러 본다.
# `layer()` 에는 이런 $W$ 가 아예 없으므로 특징 차원도 영원히 2 로 고정이다.
#
# ### (c) 비선형 $\sigma$ — 없으면 층이 접힌다
#
# $\sigma$ 가 없으면 $S(SHW_1)W_2 = S^2 H (W_1W_2)$ 라서 2층 = 1층. **ReLU 가 있어야 층이 층 노릇을 한다.**

# %%
W1 = np.array([[1.0], [-0.5]])        # 학습됐다고 치는 가중치

mid = S_gcn @ H0 @ W1                 # 1층 결과(활성화 전)
lin2 = S_gcn @ mid                    # 비선형 없는 2층
relu2 = np.maximum(S_gcn @ np.maximum(mid, 0), 0)   # ReLU 를 낀 2층
fold = S_gcn @ S_gcn @ H0 @ W1        # 층을 접어 1층으로 만든 것

print("비선형 없는 2층 == 접은 1층 (S²HW):", np.allclose(lin2, fold))
print("노드   1층(활성화 전)   선형2층   ReLU2층")
for v in NODES:
    i = idx[v]
    print(f"  {v}      {mid[i, 0]:7.3f}      {lin2[i, 0]:7.3f}  {relu2[i, 0]:7.3f}")

# 출력: 비선형 없는 2층 == 접은 1층 (S²HW): True
# 출력: 노드   1층(활성화 전)   선형2층   ReLU2층
# 출력:   A        0.856        0.486    0.486
# 출력:   B        0.308        0.328    0.421
# 출력:   C       -0.321        0.038    0.145
# 출력:   D        0.138       -0.062    0.069
# 출력:   E        0.387        0.369    0.421
# 출력:   F       -0.146        0.064    0.137
# 출력: → C 의 음수(-0.321)가 선형 경로에서는 이웃 B·D 로 그대로 새어 나가 D 를 음수로 만든다.
# 출력:   ReLU 는 그 음수를 0 으로 막는다. 순위도 달라진다(선형: E>F>C, ReLU: E>C>F).
# 출력:   즉 σ 가 있어야 «층마다 다른 계산»이 된다.

# %% [markdown]
# ## 6. 시각화
#
# 네 칸으로 정리한다.
#
# 1. 그래프 구조와 0층 특징
# 2. 층이 깊어질 때 각 노드의 특징 1 궤적 — 점선은 수렴 목적지 $\pi^\top H^{(0)}$
# 3. 노드 간 퍼짐의 로그 감소 = 과평활 속도
# 4. 노드별 「자기 자신」 계수: `layer()` 의 고정 $w_s$ vs GCN 의 $1/(d_i+1)$

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
INK, INK2, MUTED, SURF = "#0b0b0b", "#52514e", "#c8c7c1", "#fcfcfb"
SYM = ["circle", "square", "diamond", "triangle-up", "x", "star"]

POS = {"A": (0.0, 1.0), "B": (1.0, 1.4), "C": (2.0, 1.0),
       "D": (3.0, 1.3), "E": (0.7, 0.0), "F": (1.7, -0.5)}

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=("① 그래프와 0층 특징 [장애수, 팀규모]",
                    "② 층별 특징1 궤적 — 모두 한 점으로",
                    "③ 노드 간 퍼짐 (로그) = 과평활 속도",
                    "④ 「자기 자신」 계수: layer() vs GCN"),
    vertical_spacing=0.14, horizontal_spacing=0.10)

# ① 그래프
for a, b in EDGES:
    fig.add_trace(go.Scatter(x=[POS[a][0], POS[b][0]], y=[POS[a][1], POS[b][1]],
                             mode="lines", line=dict(color=MUTED, width=2),
                             hoverinfo="skip", showlegend=False), row=1, col=1)
fig.add_trace(go.Scatter(
    x=[POS[v][0] for v in NODES], y=[POS[v][1] for v in NODES],
    mode="markers+text", marker=dict(size=34, color=SURF, line=dict(color=INK, width=2)),
    text=NODES, textposition="middle center", textfont=dict(color=INK, size=13),
    hovertext=[f"{v}: {FEAT[v]} (d={int(deg[idx[v]])})" for v in NODES],
    hoverinfo="text", showlegend=False), row=1, col=1)
for v in NODES:
    fig.add_annotation(x=POS[v][0], y=POS[v][1] - 0.28, text=f"{FEAT[v][0]:.0f}, {FEAT[v][1]:.0f}",
                       showarrow=False, font=dict(color=INK2, size=11), row=1, col=1)

# ② 층별 궤적
L = 16
for k, v in enumerate(NODES):
    fig.add_trace(go.Scatter(
        x=list(range(L + 1)), y=traj[:L + 1, idx[v], 0], mode="lines+markers",
        name=v, legendgroup=v, line=dict(color=PAL[k], width=2),
        marker=dict(size=7, symbol=SYM[k], line=dict(color=SURF, width=1)),
        hovertemplate=f"{v} · %{{x}}층: %{{y:.3f}}<extra></extra>"), row=1, col=2)
fig.add_hline(y=limit[0], line=dict(color=INK2, width=1.5, dash="dot"), row=1, col=2)
fig.add_annotation(x=9.5, y=3.7, xanchor="left", showarrow=False,
                   text=f"점선 = 수렴 목적지 πᵀH⁽⁰⁾ = {limit[0]:.3f}<br>(차수로 가중한 전체 평균)",
                   align="left", font=dict(color=INK2, size=11), row=1, col=2)

# ③ 퍼짐 감소
spread = traj[:L + 1].std(1).mean(1)
fig.add_trace(go.Scatter(x=list(range(L + 1)), y=spread, mode="lines+markers",
                         line=dict(color=PAL[0], width=2), marker=dict(size=7),
                         showlegend=False,
                         hovertemplate="%{x}층: 표준편차 %{y:.4f}<extra></extra>"), row=2, col=1)
fig.add_annotation(x=2, y=np.log10(spread[2]), text="관행이 멈추는 2~3층", ax=48, ay=-38,
                   arrowhead=0, arrowcolor=INK2, font=dict(color=INK2, size=11), row=2, col=1)

# ④ 자기 계수 (겹침 방지로 좌우 살짝 어긋나게)
xs = np.arange(n, dtype=float)
gcn_self = np.array([1 / (deg[idx[v]] + 1) for v in NODES])
fig.add_trace(go.Scatter(x=xs - 0.13, y=[W_S] * n, mode="markers", name="layer() : w_self = 0.5 고정",
                         marker=dict(size=14, symbol="circle", color=PAL[0],
                                     line=dict(color=SURF, width=2)),
                         hovertemplate="%{y:.3f}<extra>layer()</extra>"), row=2, col=2)
fig.add_trace(go.Scatter(x=xs + 0.13, y=gcn_self, mode="markers", name="GCN : 1/(dᵢ+1) — 차수마다 다름",
                         marker=dict(size=14, symbol="diamond", color=PAL[1],
                                     line=dict(color=SURF, width=2)),
                         hovertemplate="%{y:.3f}<extra>GCN</extra>"), row=2, col=2)
for k, v in enumerate(NODES):
    fig.add_annotation(x=xs[k], y=0.055, text=f"d={int(deg[idx[v]])}", showarrow=False,
                       font=dict(color=INK2, size=11), row=2, col=2)

fig.update_xaxes(visible=False, row=1, col=1)
fig.update_yaxes(visible=False, row=1, col=1, scaleanchor="x", scaleratio=1)
fig.update_xaxes(title_text="층 l", row=1, col=2)
fig.update_yaxes(title_text="특징1 (장애 횟수)", row=1, col=2)
fig.update_xaxes(title_text="층 l", row=2, col=1)
fig.update_yaxes(title_text="노드 간 표준편차", type="log", row=2, col=1,
                 tickvals=[1.0, 0.5, 0.2, 0.1, 0.05], ticktext=["1", "0.5", "0.2", "0.1", "0.05"])
fig.update_xaxes(tickvals=list(xs), ticktext=NODES, range=[-0.5, n - 0.5], row=2, col=2)
fig.update_yaxes(title_text="자기 자신 계수", range=[0, 0.62], row=2, col=2)
fig.update_xaxes(showgrid=False, zeroline=False, linecolor=MUTED, ticks="outside", tickcolor=MUTED)
fig.update_yaxes(gridcolor="#eceae5", zeroline=False, linecolor=MUTED)

fig.update_layout(
    template="simple_white", width=1200, height=820,
    paper_bgcolor=SURF, plot_bgcolor=SURF,
    font=dict(color=INK, size=12),
    title=dict(text="layer(): H⁽ˡ⁺¹⁾ = w_s H⁽ˡ⁾ + w_n Â H⁽ˡ⁾ — 층을 쌓으면 구조가 값에 녹는다",
               font=dict(size=17)),
    legend=dict(orientation="h", yanchor="top", y=-0.13, xanchor="center", x=0.5,
                bgcolor="rgba(0,0,0,0)", tracegroupgap=6),
    margin=dict(l=70, r=40, t=80, b=130))
for a in fig.layout.annotations[:4]:
    a.font.size = 13

_show(fig)

import pathlib
_out = pathlib.Path(__file__).parent if "__file__" in globals() else pathlib.Path.cwd()
fig.write_image(str(_out / "expy.png"), scale=2)
print("saved:", _out / "expy.png")

# 출력: saved: .../expy.png

# %% [markdown]
# ## 정리
#
# - `layer()` 가 계산하는 것: **각 노드마다 「자기 벡터」와 「이웃 벡터 평균」의 가중합.** 기본 $w_s=w_n=0.5$.
# - 행렬로 쓰면 $H^{(l+1)} = (w_s I + w_n D^{-1}A)H^{(l)} = S H^{(l)}$. 층 쌓기 = $S^l$.
# - $S$ 가 확률행렬이라 $S^l H^{(0)} \to \mathbf{1}(\pi^\top H^{(0)})$ — 차수 가중 전체 평균 한 점으로 수렴(과평활).
#   여기서는 $[1.833,\ 3.333]$. 그래서 2~3층에서 멈춘다.
# - 진짜 GCN 과의 차이 세 가지: **학습 가중치 $W$**(특징 변환·차원 변경),
#   **비선형 $\sigma$**(없으면 여러 층이 한 층으로 접힘), **대칭 정규화 $\tilde{D}^{-1/2}\tilde{A}\tilde{D}^{-1/2}$**
#   (self-loop 포함, 자기 계수가 $1/(d_i+1)$ 로 차수마다 다름, 허브의 발언권이 줄어듦).
