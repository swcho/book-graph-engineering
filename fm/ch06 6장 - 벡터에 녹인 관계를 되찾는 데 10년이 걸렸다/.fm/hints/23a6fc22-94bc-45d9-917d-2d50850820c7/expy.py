# %% [markdown]
# # 과평활(over-smoothing) — GNN을 2~3층에서 멈추는 이유
#
# 필요 패키지: `numpy`, `plotly`, `kaleido`
#
# GCN 한 층은 이웃 값을 뭉쳐 자기 값에 섞는다.
#
# $$H^{(l+1)} = \sigma\!\left(\hat{A}\,H^{(l)}\,W^{(l)}\right),\qquad
# \hat{A} = \tilde{D}^{-1/2}\,\tilde{A}\,\tilde{D}^{-1/2},\quad \tilde{A} = A + I$$
#
# 이 노트북은 **$\sigma$와 $W$를 빼고** 전파 연산 $\hat{A}$만 반복한다.
# 과평활은 학습 가중치가 만드는 현상이 아니라 **전파 연산 자체의 성질**이기 때문이다.
#
# $\hat{A}$는 대칭 행렬이고 고윳값이 $1 = \lambda_1 > \lambda_2 \ge \dots \ge \lambda_n > -1$ 범위에 있다.
# 따라서 $\hat{A}^L$을 반복하면 $\lambda_1 = 1$ 성분만 남고 나머지는 $\lambda_i^L \to 0$으로 사라진다.
# 남는 그 성분이 $\tilde{D}^{1/2}\mathbf{1}$, 즉 **차수에만 의존하는 값**이다.
# 노드의 정체성은 사라지고 "몇 개랑 연결됐나"만 남는다. 그게 과평활이다.

# %%
# 필요 패키지: numpy, plotly, kaleido
import os

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."
np.set_printoptions(precision=3, suppress=True)
print("준비 완료")
# 출력: 준비 완료

# %% [markdown]
# ## 1. 그래프 만들기 — 두 개의 뚜렷한 커뮤니티
#
# 6장 `corpus.py`의 구도를 본떠, "멱등성 없음 계열 장애 6건"과 "캐시 계열 장애 6건"이
# 몇 개의 다리로 이어진 그래프를 만든다. 노드가 원래 **구분되는 상태**에서 출발해야
# 층을 쌓을수록 그 구분이 사라지는 걸 볼 수 있다.

# %%
N = 12
GROUP = np.array([0] * 6 + [1] * 6)  # 0 = 멱등성 계열, 1 = 캐시 계열
LABEL = [f"d{i + 1:02d}" for i in range(N)]

EDGES = [
    # 커뮤니티 0 내부
    (0, 1), (0, 2), (1, 2), (1, 3), (2, 4), (3, 4), (4, 5), (3, 5),
    # 커뮤니티 1 내부
    (6, 7), (6, 8), (7, 8), (7, 9), (8, 10), (9, 10), (10, 11), (9, 11),
    # 두 커뮤니티를 잇는 다리 (실제 그래프는 좁은 세상이라 이런 지름길이 있다)
    (5, 6), (0, 11), (4, 9), (2, 7),
]

A = np.zeros((N, N))
for u, v in EDGES:
    A[u, v] = A[v, u] = 1.0

A_tilde = A + np.eye(N)                     # 자기 자신도 이웃으로 (self-loop)
deg = A_tilde.sum(axis=1)
D_inv_sqrt = np.diag(1.0 / np.sqrt(deg))
A_hat = D_inv_sqrt @ A_tilde @ D_inv_sqrt   # 대칭 정규화 인접행렬

print("차수(self-loop 포함):", deg.astype(int))
print("A_hat 대칭인가:", np.allclose(A_hat, A_hat.T))
# 출력: 차수(self-loop 포함): [4 4 5 4 5 4 4 5 4 5 4 4]
# 출력: A_hat 대칭인가: True

# %% [markdown]
# ## 2. 전파 연산자의 고유값 — 과평활의 속도가 여기 적혀 있다
#
# $\hat{A}$의 고윳값을 보면 **몇 층 만에 뭉개지는지**가 미리 계산된다.
# 층 $L$을 지난 뒤 남는 "노드 간 차이"의 크기는 대략 $\lambda_{\text{sub}}^{L}$로 줄어든다.
# 여기서 $\lambda_{\text{sub}} = \max_{i \ge 2} |\lambda_i|$ 이다.

# %%
eigvals = np.sort(np.linalg.eigvalsh(A_hat))[::-1]
lam1 = eigvals[0]
lam_sub = max(abs(eigvals[1]), abs(eigvals[-1]))

print("고윳값 (큰 순):", np.round(eigvals, 3))
print(f"λ1     = {lam1:.6f}   ← 항상 1. 이 성분만 살아남는다")
print(f"λ_sub  = {lam_sub:.6f}   ← 차이를 나르는 성분. 층마다 이만큼씩 줄어든다")
for L in (2, 3, 10, 20):
    print(f"  {L:2d}층 → 노드 간 차이가 {lam_sub ** L:.2e} 배")
# 출력: 고윳값 (큰 순): [ 1.     0.761  0.7    0.542  0.35   0.25   0.101 -0.051 -0.092 -0.162
# 출력:  -0.25  -0.349]
# 출력: λ1     = 1.000000   ← 항상 1. 이 성분만 살아남는다
# 출력: λ_sub  = 0.760567   ← 차이를 나르는 성분. 층마다 이만큼씩 줄어든다
# 출력:    2층 → 노드 간 차이가 5.78e-01 배
# 출력:    3층 → 노드 간 차이가 4.40e-01 배
# 출력:   10층 → 노드 간 차이가 6.48e-02 배
# 출력:   20층 → 노드 간 차이가 4.20e-03 배

# %% [markdown]
# ## 3. 층을 쌓아 보기
#
# 초기 특징은 커뮤니티마다 다른 값을 준다(0번 그룹 $\approx -1$, 1번 그룹 $\approx +1$).
# 층을 돌 때마다 세 가지를 잰다.
#
# 1. **디리클레 에너지** $E(H) = \operatorname{tr}\!\left(H^{\top}(I - \hat{A})H\right)$ — 이웃끼리 얼마나 다른가. $0$이면 완전히 평평하다.
# 2. **커뮤니티 분리도** $\dfrac{\lVert \bar{h}_{0} - \bar{h}_{1}\rVert}{\lVert H \rVert_F / \sqrt{N}}$ — 두 커뮤니티를 여전히 구분할 수 있는가 (스케일 축소 효과를 나눠서 제거).
# 3. **평균 쌍별 코사인 거리** — 크기 말고 **방향**으로도 구분이 되는가.

# %%
rng = np.random.default_rng(6)
H0 = np.where(GROUP[:, None] == 0, -1.0, 1.0) + 0.15 * rng.standard_normal((N, 2))

L_MAX = 60
history = [H0.copy()]
H = H0.copy()
for _ in range(L_MAX):
    H = A_hat @ H          # 한 층 = 이웃 뭉치기 한 번
    history.append(H.copy())


def dirichlet(H_):
    return float(np.trace(H_.T @ (np.eye(N) - A_hat) @ H_))


def separation(H_):
    m0, m1 = H_[GROUP == 0].mean(axis=0), H_[GROUP == 1].mean(axis=0)
    scale = np.linalg.norm(H_) / np.sqrt(N)
    return float(np.linalg.norm(m0 - m1) / (scale + 1e-300))


def mean_cos_dist(H_):
    U = H_ / (np.linalg.norm(H_, axis=1, keepdims=True) + 1e-300)
    C = U @ U.T
    iu = np.triu_indices(N, k=1)
    return float(np.mean(1.0 - C[iu]))


energy = np.array([dirichlet(h) for h in history])
sep = np.array([separation(h) for h in history])
cosd = np.array([mean_cos_dist(h) for h in history])

print(" 층 | 디리클레에너지 | 커뮤니티분리도 | 평균코사인거리")
for L in [0, 1, 2, 3, 5, 10, 20, 40, 60]:
    print(f"{L:3d} | {energy[L]:14.3e} | {sep[L]:14.3e} | {cosd[L]:14.3e}")
# 출력:  층 | 디리클레에너지 | 커뮤니티분리도 | 평균코사인거리
# 출력:   0 |      7.351e+00 |      1.973e+00 |      1.088e+00
# 출력:   1 |      3.104e+00 |      1.905e+00 |      1.084e+00
# 출력:   2 |      1.770e+00 |      1.899e+00 |      1.077e+00
# 출력:   3 |      1.022e+00 |      1.883e+00 |      1.067e+00
# 출력:   5 |      3.416e-01 |      1.829e+00 |      1.017e+00
# 출력:  10 |      2.212e-02 |      1.221e+00 |      4.041e-01
# 출력:  20 |      9.281e-05 |      1.026e-01 |      1.736e-03
# 출력:  40 |      1.633e-09 |      4.312e-04 |      3.047e-08
# 출력:  60 |      2.875e-14 |      1.809e-06 |      5.362e-13

# %% [markdown]
# 20층에서 디리클레 에너지가 $10^{-4}$, 코사인 거리가 $10^{-3}$이다.
# 노드들이 **사실상 같은 벡터**가 됐다는 뜻이다.
# 60층이면 $10^{-13}$ — float32 정밀도($\approx 10^{-7}$) 아래라서
# 실제 학습에서는 아예 **구분 불가능**이다.

# %% [markdown]
# ## 4. 무엇으로 수렴하는가 — "차수만 남는다"
#
# 이론은 $\hat{A}^{L}H^{(0)} \to c \cdot \tilde{D}^{1/2}\mathbf{1}$ 이라고 말한다.
# 즉 층을 무한히 쌓으면 노드 $i$의 값은 $\sqrt{d_i}$에 비례할 뿐,
# **처음에 무슨 특징을 넣었는지와 무관해진다**. 확인해 본다.

# %%
H_far = history[L_MAX]
v_theory = np.sqrt(deg) / np.linalg.norm(np.sqrt(deg))
v_actual = H_far[:, 0] / np.linalg.norm(H_far[:, 0])
if np.dot(v_theory, v_actual) < 0:
    v_actual = -v_actual

print("이론값 √d 방향  :", np.round(v_theory, 4))
print(f"{L_MAX}층 실제 방향 :", np.round(v_actual, 4))
print(f"코사인 유사도   : {float(np.dot(v_theory, v_actual)):.10f}")
print(f"√d 와의 상관계수: {np.corrcoef(np.sqrt(deg), v_actual)[0, 1]:.10f}")
# 출력: 이론값 √d 방향  : [0.277 0.277 0.31  0.277 0.31  0.277 0.277 0.31  0.277 0.31  0.277 0.277]
# 출력: 60층 실제 방향 : [0.277 0.277 0.31  0.277 0.31  0.277 0.277 0.31  0.277 0.31  0.277 0.277]
# 출력: 코사인 유사도   : 0.9999999998
# 출력: √d 와의 상관계수: 0.9999999146

# %% [markdown]
# 60층을 지나자 12개 노드의 값이 **차수가 4냐 5냐** 두 종류로만 갈렸다.
# 원래 있던 "멱등성 계열 / 캐시 계열" 구분은 완전히 녹아 없어졌다.
# 노드 분류를 하려던 모델이라면 이 시점에서 아무것도 못 한다.

# %% [markdown]
# ## 5. 반대편 손익 — 그럼 왜 1층으로 끝내지 않는가
#
# 과평활만 보면 층은 적을수록 좋다. 그런데 층 $L$은 **몇 홉까지 보는가**이기도 하다.
# $L$층 GNN에서 노드 하나의 수용 영역(receptive field)은 정확히 $L$홉 이웃이다.
# 얻는 것(수용 영역)과 잃는 것(분리도)을 같은 표에 놓는다.

# %%
def khop_coverage(k):
    """각 노드가 k홉 안에 도달하는 노드 수의 평균 (자기 자신 포함)."""
    reach = np.eye(N, dtype=bool)
    frontier = np.eye(N, dtype=bool)
    for _ in range(k):
        frontier = (frontier @ (A > 0)) & ~reach
        reach |= frontier
    return reach.sum(axis=1).mean()


print(" L | 수용영역 | 늘어난 양 | 분리도 | 유지율 | 판정")
prev = None
for L in range(0, 9):
    cov = khop_coverage(L)
    gain = 0.0 if prev is None else cov - prev
    keep = sep[L] / sep[0] * 100
    if prev is None:
        verdict = "출발점"
    elif gain > 0.5:
        verdict = "수용영역 확장 중 — 층값 함"
    else:
        verdict = "확장 끝 — 과평활 손해만"
    print(f"{L:2d} | {cov:8.2f} | {gain:9.2f} | {sep[L]:6.3f} | {keep:5.1f}% | {verdict}")
    prev = cov
# 출력:  L | 수용영역 | 늘어난 양 | 분리도 | 유지율 | 판정
# 출력:  0 |     1.00 |      0.00 |  1.973 | 100.0% | 출발점
# 출력:  1 |     4.33 |      3.33 |  1.905 |  96.5% | 수용영역 확장 중 — 층값 함
# 출력:  2 |     9.33 |      5.00 |  1.899 |  96.2% | 수용영역 확장 중 — 층값 함
# 출력:  3 |    12.00 |      2.67 |  1.883 |  95.4% | 수용영역 확장 중 — 층값 함
# 출력:  4 |    12.00 |      0.00 |  1.863 |  94.4% | 확장 끝 — 과평활 손해만
# 출력:  5 |    12.00 |      0.00 |  1.829 |  92.7% | 확장 끝 — 과평활 손해만
# 출력:  6 |    12.00 |      0.00 |  1.774 |  89.9% | 확장 끝 — 과평활 손해만
# 출력:  7 |    12.00 |      0.00 |  1.690 |  85.6% | 확장 끝 — 과평활 손해만
# 출력:  8 |    12.00 |      0.00 |  1.569 |  79.5% | 확장 끝 — 과평활 손해만

# %% [markdown]
# 3층에서 수용 영역이 그래프 전체를 덮고 **더 늘어나지 않는다**.
# 그런데 분리도는 계속 깎인다. 4층부터는 **새로 얻는 정보 없이 손해만 본다.**
# 이 교차점이 "2~3층에서 멈춘다"는 관행의 실체다.
#
# 실제 그래프도 좁은 세상(small-world)이라 평균 최단 경로가 6 안팎이다.
# 2~3홉이면 이미 그래프 상당 부분이 수용 영역에 들어온다.
# 층을 더 쌓아 얻을 새 정보는 거의 없고, 과평활 손해만 남는다.

# %% [markdown]
# ## 6. 시각화

# %%
layers = np.arange(L_MAX + 1)
fig = make_subplots(
    rows=1, cols=3,
    subplot_titles=(
        "① 노드 값이 한 점으로 뭉친다",
        "② 디리클레 에너지 = 이웃 간 차이 (로그)",
        "③ 얻는 것(수용영역) vs 잃는 것(분리도)",
    ),
    specs=[[{}, {}, {"secondary_y": True}]],
)

# ① 노드별 값 궤적
for i in range(N):
    color = "#2E6BE6" if GROUP[i] == 0 else "#E0603A"
    fig.add_trace(
        go.Scatter(
            x=layers, y=[h[i, 0] for h in history],
            mode="lines", line=dict(color=color, width=1.6),
            name=("멱등성 계열" if GROUP[i] == 0 else "캐시 계열"),
            legendgroup=str(GROUP[i]), showlegend=(i in (0, 6)),
            hovertemplate=f"{LABEL[i]} · %{{x}}층 · %{{y:.4f}}<extra></extra>",
        ),
        row=1, col=1,
    )
fig.add_vrect(x0=2, x1=3, fillcolor="#FFD166", opacity=0.30, line_width=0, row=1, col=1)

# ② 디리클레 에너지 + 이론 감쇠선
fig.add_trace(
    go.Scatter(x=layers, y=energy, mode="lines",
               line=dict(color="#7B4FD1", width=2.4), name="디리클레 에너지"),
    row=1, col=2,
)
fig.add_trace(
    go.Scatter(x=layers, y=energy[0] * lam_sub ** (2 * layers), mode="lines",
               line=dict(color="#9AA0A6", width=1.6, dash="dash"),
               name=f"이론 감쇠 λ_sub^2L (λ={lam_sub:.3f})"),
    row=1, col=2,
)
fig.add_hline(y=1e-7, line=dict(color="#C62828", width=1, dash="dot"),
              annotation_text="float32 정밀도 한계", annotation_position="bottom right",
              row=1, col=2)

# ③ 수용영역 vs 분리도
ks = list(range(9))
cov = [khop_coverage(k) for k in ks]
fig.add_trace(
    go.Scatter(x=ks, y=cov, mode="lines+markers",
               line=dict(color="#1F9D6B", width=2.4), marker=dict(size=7),
               name="수용영역 (도달 노드 수)"),
    row=1, col=3, secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=ks, y=sep[:9], mode="lines+markers",
               line=dict(color="#E0603A", width=2.4), marker=dict(size=7),
               name="커뮤니티 분리도"),
    row=1, col=3, secondary_y=True,
)
fig.add_vrect(x0=2, x1=3, fillcolor="#FFD166", opacity=0.30, line_width=0,
              annotation_text="관행: 2~3층", annotation_position="bottom left",
              row=1, col=3)

fig.update_xaxes(title_text="층 L", row=1, col=1)
fig.update_xaxes(title_text="층 L", row=1, col=2)
fig.update_xaxes(title_text="층 L", row=1, col=3)
fig.update_yaxes(title_text="특징 0번 차원 값", row=1, col=1)
fig.update_yaxes(title_text="에너지", type="log", row=1, col=2)
fig.update_yaxes(title_text="도달 노드 수", row=1, col=3, secondary_y=False)
fig.update_yaxes(title_text="분리도", row=1, col=3, secondary_y=True)
fig.update_layout(
    title="과평활: 층을 쌓을수록 모든 노드가 같아진다",
    height=480, width=1380, template="plotly_white",
    legend=dict(orientation="h", y=-0.20),
)

_show(fig)
png_path = os.path.join(HERE, "expy.png")
fig.write_image(png_path, scale=2)
print("저장:", png_path)
# 출력: 저장: <hint dir>/expy.png

# %% [markdown]
# ## 7. 정리
#
# | 관찰 | 의미 |
# |---|---|
# | $\hat{A}$의 고윳값이 $\lambda_1 = 1$, 나머지 $\lvert\lambda_i\rvert < 1$ | 층을 쌓으면 $\lambda_1$ 성분만 남는다 |
# | 60층 결과가 $\sqrt{d_i}$에 정확히 비례 (상관계수 $\approx 1.0$) | 남는 정보는 **차수뿐**. 노드 정체성은 사라진다 |
# | 디리클레 에너지가 $\lambda_{\text{sub}}^{2L}$ 속도로 붕괴 | 이웃 간 차이가 지수적으로 사라진다 = 과평활 |
# | 수용 영역은 3홉이면 포화, 분리도는 계속 감소 | 4층부터는 **얻는 것 없이 잃기만 한다** |
#
# 그래서 관행이 2~3층이다. 6장의 표현으로는,
# **"층을 돌 때마다 구조가 값에 녹아든다"** 는 이득과
# **"깊게 쌓으면 모든 노드가 비슷해진다"** 는 손해가 만나는 지점이 거기다.
#
# 덧붙여, 층이 깊어질수록 **되짚기**도 같이 무너진다.
# 1층이면 "이 이웃이 이만큼 기여했다"를 말할 수 있지만,
# 2층부터는 기여가 이웃의 이웃까지 섞여 설명이 어려워진다.
# 얕게 쌓는 관행은 과평활 대책이면서 동시에 설명 가능성을 붙잡는 수단이기도 하다.
