# %% [markdown]
# # 노드 D의 값에 구조가 녹아드는 과정 — 기여 계수로 분해하기
#
# `content/ch06/code/ex3_message_passing.py`가 보여 주는 것:
#
# > 0층에서 `[2.0, 1.0]`이던 D의 값에, 1층에서 C의 값이, 2층에서 B의 값까지 흘러든다.
# > **구조가 값에 녹아드는 과정**이다.
#
# 이 노트북은 그 "녹아듦"을 **숫자로 분해**한다.
# 층마다 D의 값이 원본 노드 A~F의 값 중 **누구 것을 얼마나** 담고 있는지 계수로 추적하고,
# 층이 깊어질수록 그 계수 분포가 어떻게 뭉개져서 되짚기가 어려워지는지 본다.

# %%
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


NODES = ["A", "B", "C", "D", "E", "F"]
EDGES = [("A", "B"), ("B", "C"), ("C", "D"), ("A", "E"), ("E", "F"), ("B", "E")]
# 시작 특징. «장애를 몇 번 겪었나, 팀 규모» 두 칸.
FEAT = {"A": [4.0, 2.0], "B": [1.0, 5.0], "C": [0.0, 3.0],
        "D": [2.0, 1.0], "E": [3.0, 4.0], "F": [0.0, 2.0]}

IDX = {n: i for i, n in enumerate(NODES)}
H0 = np.array([FEAT[n] for n in NODES], dtype=float)

A = np.zeros((6, 6))
for a, b in EDGES:
    A[IDX[a], IDX[b]] = 1.0
    A[IDX[b], IDX[a]] = 1.0

deg = A.sum(axis=1)
print("차수:", {n: int(deg[IDX[n]]) for n in NODES})
print("D의 이웃:", [n for n in NODES if A[IDX["D"], IDX[n]]])

# 출력: 차수: {'A': 2, 'B': 3, 'C': 2, 'D': 1, 'E': 3, 'F': 1}
# 출력: D의 이웃: ['C']

# %% [markdown]
# ## 1. 한 층은 사실 행렬 하나다
#
# 예제의 `layer()`는 자기 벡터와 이웃 **평균**을 반씩 섞는다.
#
# $$h_v^{(l+1)} = \tfrac12 h_v^{(l)} + \tfrac12 \cdot \frac{1}{|N(v)|}\sum_{u \in N(v)} h_u^{(l)}$$
#
# 여기엔 학습 가중치도 비선형 활성화도 없다. 그래서 **완전히 선형**이고, 전파 행렬 하나로 쓸 수 있다.
#
# $$P = \tfrac12 I + \tfrac12 D^{-1}A, \qquad H^{(l)} = P^{\,l} H^{(0)}$$
#
# $P$의 각 행은 합이 1이다 (자기 0.5 + 이웃들 0.5). 즉 **가중 평균**이고,
# $P^l$의 D행이 곧 "l층 D의 값에 각 원본 노드가 기여한 계수"다.

# %%
P = 0.5 * np.eye(6) + 0.5 * (A / deg[:, None])
print("전파 행렬 P (행=대상, 열=출처)")
for n in NODES:
    print(f"  {n}: " + "  ".join(f"{n2}={P[IDX[n], IDX[n2]]:.3f}" for n2 in NODES))
print("행 합:", P.sum(axis=1).round(6))

# 출력: 전파 행렬 P (행=대상, 열=출처)
# 출력:   A: A=0.500  B=0.250  C=0.000  D=0.000  E=0.250  F=0.000
# 출력:   B: A=0.167  B=0.500  C=0.167  D=0.000  E=0.167  F=0.000
# 출력:   C: A=0.000  B=0.250  C=0.500  D=0.250  E=0.000  F=0.000
# 출력:   D: A=0.000  B=0.000  C=0.500  D=0.500  E=0.000  F=0.000
# 출력:   E: A=0.167  B=0.167  C=0.000  D=0.000  E=0.500  F=0.167
# 출력:   F: A=0.000  B=0.000  C=0.000  D=0.000  E=0.500  F=0.500
# 출력: 행 합: [1. 1. 1. 1. 1. 1.]

# %%
# 원 예제의 출력과 일치하는지 확인 (원 예제는 층마다 round(...,3) 을 하므로 미세한 차이만 남는다)
MAX_L = 12
Hs = [H0.copy()]
Ps = [np.eye(6)]
for _ in range(MAX_L):
    Ps.append(P @ Ps[-1])
    Hs.append(P @ Hs[-1])

for l in (0, 1, 2):
    print(f"{l}층:", {n: np.round(Hs[l][IDX[n]], 3).tolist() for n in NODES})

# 출력: 0층: {'A': [4.0, 2.0], 'B': [1.0, 5.0], 'C': [0.0, 3.0], 'D': [2.0, 1.0], 'E': [3.0, 4.0], 'F': [0.0, 2.0]}
# 출력: 1층: {'A': [3.0, 3.25], 'B': [1.667, 4.0], 'C': [0.75, 3.0], 'D': [1.0, 2.0], 'E': [2.333, 3.5], 'F': [1.5, 3.0]}
# 출력: 2층: {'A': [2.5, 3.5], 'B': [1.847, 3.625], 'C': [1.042, 3.0], 'D': [0.875, 2.5], 'E': [2.194, 3.458], 'F': [1.917, 3.25]}
# 출력: → ex3_message_passing.py 의 실행 결과와 그대로 일치한다.

# %% [markdown]
# ## 2. D의 기여 계수를 층별로 추적한다
#
# $P^l$의 D행을 뽑으면 끝이다. 이 행의 $n$번째 값이
# "l층 D의 값 중 원본 노드 $n$의 값이 차지하는 비중"이다.

# %%
D = IDX["D"]
coef = np.array([Ps[l][D] for l in range(MAX_L + 1)])  # (층, 출처노드)

print("층 | " + " | ".join(f"{n:>6}" for n in NODES) + " | 기여노드수")
for l in range(0, 7):
    row = coef[l]
    print(f"{l:2d} | " + " | ".join(f"{v:6.3f}" for v in row) + f" | {int((row > 1e-9).sum())}")

# 출력: 층 |      A |      B |      C |      D |      E |      F | 기여노드수
# 출력:  0 |  0.000 |  0.000 |  0.000 |  1.000 |  0.000 |  0.000 | 1
# 출력:  1 |  0.000 |  0.000 |  0.500 |  0.500 |  0.000 |  0.000 | 2
# 출력:  2 |  0.000 |  0.125 |  0.500 |  0.375 |  0.000 |  0.000 | 3
# 출력:  3 |  0.021 |  0.188 |  0.458 |  0.312 |  0.021 |  0.000 | 5
# 출력:  4 |  0.045 |  0.217 |  0.417 |  0.271 |  0.047 |  0.003 | 6
# 출력:  5 |  0.067 |  0.232 |  0.380 |  0.240 |  0.073 |  0.010 | 6
# 출력:  6 |  0.084 |  0.240 |  0.348 |  0.215 |  0.096 |  0.017 | 6

# %% [markdown]
# 카드의 문장이 그대로 숫자로 나온다.
#
# | 층 | D의 값 | 분해 |
# |---|---|---|
# | 0 | `[2.0, 1.0]` | D 자신 100% |
# | 1 | `[1.0, 2.0]` | **C가 들어왔다** — D 0.5 + C 0.5 |
# | 2 | `[0.875, 2.5]` | **B까지 들어왔다** — D 0.375 + C 0.5 + B 0.125 |
# | 3 | `[0.958, 2.750]` | A, E까지 — 5개 노드 |
# | 4 | — | F까지 전부 — 6개 노드 |
#
# D→C는 1홉, D→C→B는 2홉이다. **홉 수 = 처음 등장하는 층**이다.

# %%
# 2층 D 값을 기여 계수로 직접 검산한다.
h2 = sum(coef[2][IDX[n]] * np.array(FEAT[n]) for n in NODES)
print("2층 D 재구성:", np.round(h2, 3), " / 실제:", np.round(Hs[2][D], 3))
print("  = 0.125·B[1,5] + 0.500·C[0,3] + 0.375·D[2,1]")
for l in range(0, 5):
    terms = " + ".join(f"{coef[l][IDX[n]]:.3f}·{n}" for n in NODES if coef[l][IDX[n]] > 1e-9)
    print(f"  {l}층 D = {np.round(Hs[l][D], 3)}  ←  {terms}")

# 출력: 2층 D 재구성: [0.875 2.5  ]  / 실제: [0.875 2.5  ]
# 출력:   = 0.125·B[1,5] + 0.500·C[0,3] + 0.375·D[2,1]
# 출력:   0층 D = [2. 1.]  ←  1.000·D
# 출력:   1층 D = [1. 2.]  ←  0.500·C + 0.500·D
# 출력:   2층 D = [0.875 2.5  ]  ←  0.125·B + 0.500·C + 0.375·D
# 출력:   3층 D = [0.958 2.75 ]  ←  0.021·A + 0.188·B + 0.458·C + 0.312·D + 0.021·E
# 출력:   4층 D = [1.08  2.891]  ←  0.045·A + 0.217·B + 0.417·C + 0.271·D + 0.047·E + 0.003·F

# %% [markdown]
# ## 3. 왜 2층을 넘으면 되짚기가 어려워지나
#
# 이유가 셋 있다. 셋 다 숫자로 보인다.
#
# ### (a) 기여자가 늘고, 계수가 평평해진다
#
# 계수는 합이 1인 확률 분포다. **유효 기여자 수**를 엔트로피의 지수로 재면
#
# $$\text{eff}(l) = \exp\!\Big(-\sum_n c^{(l)}_n \log c^{(l)}_n\Big)$$
#
# 1이면 "한 노드가 다 설명한다", 6이면 "여섯 노드가 똑같이 기여한다 = 아무도 설명 못 한다".

# %%
def eff_contrib(c):
    p = c[c > 1e-12]
    return float(np.exp(-(p * np.log(p)).sum()))


print("층 | 유효기여자수 | 자기(D)비중 | 최대기여자")
for l in range(0, 9):
    c = coef[l]
    top = NODES[int(np.argmax(c))]
    print(f"{l:2d} | {eff_contrib(c):11.2f} | {c[D]:10.3f} | {top}({c.max():.3f})")

# 출력: 층 | 유효기여자수 | 자기(D)비중 | 최대기여자
# 출력:  0 |        1.00 |      1.000 | D(1.000)
# 출력:  1 |        2.00 |      0.500 | C(0.500)
# 출력:  2 |        2.65 |      0.375 | C(0.500)
# 출력:  3 |        3.31 |      0.312 | C(0.458)
# 출력:  4 |        3.87 |      0.271 | C(0.417)
# 출력:  5 |        4.32 |      0.240 | C(0.380)
# 출력:  6 |        4.68 |      0.215 | C(0.348)
# 출력:  7 |        4.94 |      0.194 | C(0.322)
# 출력:  8 |        5.14 |      0.178 | C(0.299)
# 출력: → 1층 "C가 절반" 은 설명이 된다. 8층 "여섯 노드가 대충 골고루" 는 설명이 아니다.

# %% [markdown]
# ### (b) 값에서 기여를 역산할 수 없다
#
# 층을 통과한 뒤 우리 손에 남는 건 계수가 아니라 **값 두 칸**이다.
# 미지수는 노드 6개 × 2차원 = 12개인데 관측은 2개. 애초에 부정방정식이다.
#
# 계수를 알고 있어도 마찬가지다. 2층 D는 $0.125B + 0.5C + 0.375D$이므로
# $B \mathrel{+}= \delta$, $C \mathrel{-}= 0.25\delta$ 로 맞바꾸면 **D의 값은 한 톨도 안 변한다.**
# "장애 4번 더 겪은 B"와 "장애 1번 덜 겪은 C"가 D 입장에서 구분이 안 된다는 뜻이다.

# %%
delta = np.array([4.0, 4.0])
ALT = {n: list(v) for n, v in FEAT.items()}
ALT["B"] = (np.array(FEAT["B"]) + delta).tolist()
ALT["C"] = (np.array(FEAT["C"]) - 0.25 * delta).tolist()
H0b = np.array([ALT[n] for n in NODES])
H2b = Ps[2] @ H0b

print("원본  B/C:", FEAT["B"], FEAT["C"], "→ 2층 D:", np.round(Hs[2][D], 3).tolist())
print("변형  B/C:", ALT["B"], ALT["C"], "→ 2층 D:", np.round(H2b[D], 3).tolist())
print("D의 값 차이:", np.round(H2b[D] - Hs[2][D], 12).tolist())
changed = [n for n in NODES if abs(H2b[IDX[n]] - Hs[2][IDX[n]]).max() > 1e-9]
print("2층에서 값이 달라진 노드:", changed, "/ D는 그대로:", "D" not in changed)

# 출력: 원본  B/C: [1.0, 5.0] [0.0, 3.0] → 2층 D: [0.875, 2.5]
# 출력: 변형  B/C: [5.0, 9.0] [-1.0, 2.0] → 2층 D: [0.875, 2.5]
# 출력: D의 값 차이: [0.0, 0.0]
# 출력: 2층에서 값이 달라진 노드: ['A', 'B', 'C', 'E', 'F'] / D는 그대로: True
# 출력: → 세상은 완전히 달라졌는데 D의 벡터는 한 톨도 안 움직였다.
# 출력:   D의 값만 보고서는 두 세계를 구별할 방법이 없다. 이것이 «되짚기 어렵다»의 실체다.

# %% [markdown]
# ### (c) 과평활 — 층이 깊어지면 모든 노드가 같아진다
#
# $P$는 확률 행렬이라 $l \to \infty$ 에서 모든 행이 같은 정상 분포로 수렴한다.
# 이 대칭 그래프에서는 차수 비례다.
#
# $$\pi_n = \frac{\deg(n)}{\sum_m \deg(m)}$$
#
# 즉 **어느 노드에서 출발했든 기여 계수가 같아진다** → 모든 노드 벡터가 같은 값이 된다.
# 그때 D의 값은 D에 대해 아무것도 말해 주지 않는다.

# %%
pi = deg / deg.sum()
P50 = np.linalg.matrix_power(P, 50)
print("정상 분포 π:", {n: round(float(pi[IDX[n]]), 4) for n in NODES})
print("50층 D행 :", {n: round(float(P50[D][IDX[n]]), 4) for n in NODES})

print("\n층 | 노드간 최대거리 | D의 계수와 π의 거리")
for l in range(0, MAX_L + 1, 2):
    spread = max(np.linalg.norm(Hs[l][i] - Hs[l][j]) for i in range(6) for j in range(i + 1, 6))
    print(f"{l:2d} | {spread:15.3f} | {np.abs(coef[l] - pi).sum():18.3f}")

# 출력: 정상 분포 π: {'A': 0.1667, 'B': 0.25, 'C': 0.1667, 'D': 0.0833, 'E': 0.25, 'F': 0.0833}
# 출력: 50층 D행 : {'A': 0.1666, 'B': 0.25, 'C': 0.1668, 'D': 0.0835, 'E': 0.2499, 'F': 0.0833}
# 출력:
# 출력: 층 | 노드간 최대거리 | D의 계수와 π의 거리
# 출력:  0 |           4.243 |              1.833
# 출력:  2 |           1.908 |              1.250
# 출력:  4 |           1.215 |              0.875
# 출력:  6 |           0.883 |              0.626
# 출력:  8 |           0.659 |              0.453
# 출력: 10 |           0.486 |              0.328
# 출력: 12 |           0.356 |              0.239
# 출력: → 2~3층은 «C가 절반» 처럼 아직 읽히는 구간이다. 그 위는 빠르게 뭉개진다.

# %% [markdown]
# ## 4. 시각화
#
# - **좌상**: 층별 D의 기여 계수 행렬 ($P^l$의 D행). 0층 one-hot → 대각선처럼 번져 나간다.
# - **우상**: D의 «팀 규모» 값을 원본 노드별 기여량으로 쌓았다. 막대 전체 높이가 그 층의 D 값.
# - **좌하**: 유효 기여자 수. 1 → 6 으로 올라가면 설명력이 사라진다.
# - **우하**: 노드 벡터 사이의 최대 거리. 0으로 수렴하는 게 과평활이다.

# %%
SURFACE = "#fcfcfb"
INK, INK2 = "#0b0b0b", "#52514e"
SERIES = {"A": "#2a78d6", "B": "#eb6834", "C": "#1baf7a",
          "D": "#eda100", "E": "#e87ba4", "F": "#008300"}
BLUE_SEQ = [[0.0, "#fcfcfb"], [0.15, "#cde2fb"], [0.4, "#86b6ef"],
            [0.7, "#2a78d6"], [1.0, "#0d366b"]]

L_SHOW = 8
layers = list(range(L_SHOW + 1))
z = np.vstack([coef[:L_SHOW + 1], pi[None, :]])
ylabels = [f"{l}층" for l in layers] + ["∞ (정상분포)"]

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=("① D의 기여 계수 — 층이 오를수록 번진다",
                    "② D의 «팀 규모» 값이 어느 노드에서 왔나",
                    "③ 유효 기여자 수 (exp 엔트로피)",
                    "④ 노드 간 최대 거리 — 과평활"),
    horizontal_spacing=0.11, vertical_spacing=0.15,
)

fig.add_trace(go.Heatmap(
    z=z, x=NODES, y=ylabels, colorscale=BLUE_SEQ, zmin=0, zmax=1,
    text=np.where(z > 1e-9, np.round(z, 3).astype(str), ""),
    texttemplate="%{text}", textfont=dict(size=9),
    xgap=2, ygap=2, showscale=False,
    hovertemplate="%{y} · 출처 %{x}<br>기여 계수 %{z:.4f}<extra></extra>",
), row=1, col=1)

DIM = 1  # 1번 칸 = «팀 규모». 모든 노드가 0 이 아니라 기여가 전부 보인다.
for n in NODES:
    fig.add_trace(go.Bar(
        x=layers, y=[coef[l][IDX[n]] * FEAT[n][DIM] for l in layers],
        name=n, legendgroup=n, marker=dict(color=SERIES[n], line=dict(color=SURFACE, width=2)),
        hovertemplate=f"%{{x}}층 · {n}(원본 {FEAT[n][DIM]})의 기여<br>%{{y:.3f}}<extra></extra>",
    ), row=1, col=2)

fig.add_trace(go.Scatter(
    x=layers, y=[eff_contrib(coef[l]) for l in layers], mode="lines+markers",
    line=dict(color="#2a78d6", width=2), marker=dict(size=8), showlegend=False,
    hovertemplate="%{x}층 · 유효 기여자 %{y:.2f}개<extra></extra>",
), row=2, col=1)
fig.add_hline(y=6, line=dict(color=INK2, width=1, dash="dot"), row=2, col=1,
              annotation_text="전 노드 균등 = 6", annotation_font=dict(size=10, color=INK2))

spread = [max(np.linalg.norm(Hs[l][i] - Hs[l][j]) for i in range(6) for j in range(i + 1, 6))
          for l in range(MAX_L + 1)]
fig.add_trace(go.Scatter(
    x=list(range(MAX_L + 1)), y=spread, mode="lines+markers",
    line=dict(color="#eb6834", width=2), marker=dict(size=8), showlegend=False,
    hovertemplate="%{x}층 · 최대거리 %{y:.3f}<extra></extra>",
), row=2, col=2)

fig.add_vrect(x0=1.5, x1=3.5, fillcolor="#1baf7a", opacity=0.09, line_width=0, row=2, col=2,
              annotation_text="관행: 2~3층", annotation_font=dict(size=10, color=INK2))

fig.update_layout(
    title=dict(text="노드 D — 구조가 값에 녹아드는 과정과 되짚기의 한계",
               font=dict(size=19, color=INK)),
    barmode="stack", bargap=0.28, height=910, width=1180,
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
    font=dict(color=INK2, size=12),
    legend=dict(title="원본 노드 (0층)", orientation="h", yanchor="bottom", y=1.055,
                xanchor="right", x=1.0, bgcolor="rgba(0,0,0,0)"),
    margin=dict(t=150, b=60, l=70, r=40),
)
fig.update_xaxes(showgrid=False, linecolor="#dcdbd6", ticks="outside", tickcolor="#dcdbd6")
fig.update_yaxes(showgrid=True, gridcolor="#eceae5", zeroline=False, linecolor="#dcdbd6")
fig.update_yaxes(autorange="reversed", showgrid=False, row=1, col=1)
fig.update_xaxes(title_text="출처 노드 (0층 원본 값)", row=1, col=1)
fig.update_xaxes(title_text="층", dtick=1, row=1, col=2)
fig.update_yaxes(title_text="기여량 (합 = D의 값)", row=1, col=2)
fig.update_xaxes(title_text="층", dtick=1, row=2, col=1)
fig.update_yaxes(title_text="유효 기여자 수", range=[0, 6.6], row=2, col=1)
fig.update_xaxes(title_text="층", dtick=2, row=2, col=2)
fig.update_yaxes(title_text="max ‖h_i − h_j‖", row=2, col=2)
for a in fig.layout.annotations[:4]:
    a.font = dict(size=13, color=INK)

_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
_png = os.path.join(_here, "expy.png")
fig.write_image(_png, scale=2)
_show(fig)
print("저장 완료:", os.path.basename(_png))

# 출력: 저장 완료: expy.png

# %% [markdown]
# ## 정리
#
# | 관점 | 얻는 것 | 잃는 것 |
# |---|---|---|
# | 1층 | D가 C를 안다 (계수 0.5) | 거의 없음 |
# | 2층 | D가 B까지 안다 (계수 0.125) — 링크 예측이 되는 지점 | 기여자 3개, 아직 읽힌다 |
# | 4층+ | 그래프 전체를 안다 | 유효 기여자 4~6개, 계수가 π로 수렴 |
# | ∞ | 아무것도 모른다 | 모든 노드가 같은 벡터 (과평활) |
#
# **2~3층에서 멈추는 관행의 이유가 여기 있다.**
# 구조를 값에 녹이는 이득(이웃이 비슷하면 벡터도 비슷해진다)은 2층이면 대체로 얻고,
# 되짚기를 잃는 손실은 그 위에서 급격히 커진다.
