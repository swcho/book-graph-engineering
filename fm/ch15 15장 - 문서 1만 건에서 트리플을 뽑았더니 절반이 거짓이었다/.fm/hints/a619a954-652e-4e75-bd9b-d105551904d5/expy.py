# %% [markdown]
# # F1 점수는 어떻게 계산하는가?
#
# $$F_1 = \frac{2 \times \text{정밀도} \times \text{재현율}}{\text{정밀도} + \text{재현율}}$$
#
# 정밀도(precision)와 재현율(recall)의 **조화 평균**이다.
# 아래 셀들을 순서대로 실행하며 (1) 정밀도·재현율·F1 계산,
# (2) 산술 평균과의 차이, (3) 극단 케이스, (4) P–R 평면 위 F1 등고선을 확인한다.

# %%
# 필요 패키지: plotly, kaleido (시각화 셀에만 필요. 계산 셀은 표준 라이브러리만 사용)
def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass

# %% [markdown]
# ## 1. 정밀도·재현율·F1 계산
#
# 15장 예제처럼, 문서에서 뽑은 트리플(GOT)과 손으로 만든 정답(GOLD)을 집합으로 비교한다.
#
# - 맞음 $TP = |GOT \cap GOLD|$, 틀림 $FP = |GOT - GOLD|$, 놓침 $FN = |GOLD - GOT|$
# - $\text{정밀도} = \dfrac{TP}{TP+FP}$ (뽑은 것 중 맞은 비율)
# - $\text{재현율} = \dfrac{TP}{TP+FN}$ (정답 중 건진 비율)

# %%
# 장난감 예제: 정답 9건, 뽑은 것 11건 (15장의 정밀도 0.636 / 재현율 0.778 상황을 축소 재현)
GOLD = {("가온테크", "체결", f"C-{i:03d}") for i in range(9)}          # 정답 9건
GOT = {("가온테크", "체결", f"C-{i:03d}") for i in range(7)}           # 그중 7건을 맞히고
GOT |= {("가온테크", "업종", "IT"), ("마루상사", "모회사", "다올"),     # 거짓 4건을 섞어 뽑았다
        ("가온테크", "협업", "나루"), ("가온테크", "계약일", "06-02")}

tp = len(GOT & GOLD)
fp = len(GOT - GOLD)
fn = len(GOLD - GOT)
prec = tp / (tp + fp) if tp + fp else 0.0
rec = tp / (tp + fn) if tp + fn else 0.0
f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0

print(f"맞음 {tp}  틀림 {fp}  놓침 {fn}")
print(f"정밀도 {prec:.3f}  재현율 {rec:.3f}  F1 {f1:.3f}")
# 출력:
# 맞음 7  틀림 4  놓침 2
# 정밀도 0.636  재현율 0.778  F1 0.700

# %% [markdown]
# ## 2. 산술 평균 vs 기하 평균 vs 조화 평균
#
# 두 양수 $a, b$에 대해
#
# $$\text{조화} = \frac{2ab}{a+b} \;\le\; \text{기하} = \sqrt{ab} \;\le\; \text{산술} = \frac{a+b}{2}$$
#
# F1은 조화 평균이라 **작은 값 쪽으로 끌려간다**. 한쪽이 0에 가까우면 F1도 0에 가깝다.

# %%
import math

def means(p, r):
    arith = (p + r) / 2
    geom = math.sqrt(p * r)
    harm = 2 * p * r / (p + r) if p + r else 0.0
    return arith, geom, harm

cases = [(0.9, 0.9), (0.9, 0.5), (0.636, 0.778), (1.0, 0.1), (1.0, 0.01)]
print(f"{'P':>6} {'R':>6} | {'산술':>6} {'기하':>6} {'조화(F1)':>8}")
for p, r in cases:
    a, g, h = means(p, r)
    print(f"{p:>6.3f} {r:>6.3f} | {a:>6.3f} {g:>6.3f} {h:>8.3f}")
# 출력:
#      P      R |   산술   기하 조화(F1)
#  0.900  0.900 |  0.900  0.900    0.900
#  0.900  0.500 |  0.700  0.671    0.643
#  0.636  0.778 |  0.707  0.703    0.700
#  1.000  0.100 |  0.550  0.316    0.182
#  1.000  0.010 |  0.505  0.100    0.020

# %% [markdown]
# ## 3. 극단 케이스 — 왜 산술 평균이면 안 되는가
#
# 정답 100개 중 **딱 1개만 뽑아서 맞힌** 시스템: $P = 1.0$, $R = 0.01$.
#
# - 산술 평균 $= 0.505$ → 반타작처럼 보이지만 실제로는 거의 쓸모없는 시스템
# - $F_1 \approx 0.020$ → 쓸모없음을 정직하게 보여준다
#
# 코너 케이스도 확인한다: $P + R = 0$이면 관례상 $F_1 = 0$, $P = R$이면 $F_1 = P$.

# %%
def f1_score(p, r):
    return 2 * p * r / (p + r) if p + r else 0.0

print(f"P=1.0, R=0.01 → 산술 {means(1.0, 0.01)[0]:.3f}, F1 {f1_score(1.0, 0.01):.3f}")
print(f"P=0.0, R=0.0  → F1 {f1_score(0.0, 0.0):.3f}  (분모 0은 F1=0으로 정의)")
print(f"P=R=0.7      → F1 {f1_score(0.7, 0.7):.3f}  (두 값이 같으면 F1도 같다)")

# 격자 위에서 min(P,R) <= 조화 <= 기하 <= 산술 <= max(P,R) 항상 성립하는지 확인
# (P=R일 때 세 평균이 같아지는데 부동소수점 오차가 1e-17쯤 생기므로 tol을 둔다)
tol = 1e-9
ok = True
for p in [i / 20 for i in range(1, 21)]:
    for r in [j / 20 for j in range(1, 21)]:
        a, g, h = means(p, r)
        ok &= (min(p, r) <= h + tol) and (h <= g + tol) and (g <= a + tol) and (a <= max(p, r) + tol)
print(f"격자 400점에서 min ≤ 조화 ≤ 기하 ≤ 산술 ≤ max: {ok}")
# 출력:
# P=1.0, R=0.01 → 산술 0.505, F1 0.020
# P=0.0, R=0.0  → F1 0.000  (분모 0은 F1=0으로 정의)
# P=R=0.7      → F1 0.700  (두 값이 같으면 F1도 같다)
# 격자 400점에서 min ≤ 조화 ≤ 기하 ≤ 산술 ≤ max: True

# %% [markdown]
# ## 4. 시각화
#
# - 왼쪽: 정밀도–재현율 평면 위 $F_1$ 등고선. $P = R$ 대각선에 대해 대칭이고,
#   축(한쪽이 0) 근처에서는 다른 쪽이 아무리 커도 $F_1$이 낮다 — 등고선이 축에 붙지 않는다.
# - 오른쪽: $P = 0.9$로 고정하고 $R$을 움직일 때 세 평균의 비교.
#   재현율이 무너져도 산술 평균은 0.45 아래로 내려가지 않지만 F1은 0으로 떨어진다.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

n = 101
axis_vals = [i / (n - 1) for i in range(n)]
z = [[f1_score(p, r) for p in axis_vals] for r in axis_vals]  # 행=R, 열=P

# 순차(sequential) 색: 한 가지 파랑 계열, 밝음→어두움
blues = [[0.0, "#f3f8fe"], [0.33, "#cde2fb"], [0.66, "#86b6ef"], [1.0, "#1c5cab"]]

fig = make_subplots(
    rows=1, cols=2, column_widths=[0.52, 0.48], horizontal_spacing=0.14,
    subplot_titles=("F1 등고선 (P–R 평면)", "P=0.9 고정, R에 따른 세 평균"),
)

fig.add_trace(go.Contour(
    x=axis_vals, y=axis_vals, z=z,
    colorscale=blues, contours=dict(start=0.1, end=0.9, size=0.1, showlabels=True,
                                    labelfont=dict(size=10, color="#52514e")),
    colorbar=dict(title="F1", x=0.44, thickness=12),
    hovertemplate="P=%{x:.2f} R=%{y:.2f}<br>F1=%{z:.3f}<extra></extra>",
), row=1, col=1)
# 예제 1의 지점 표시
fig.add_trace(go.Scatter(
    x=[0.636], y=[0.778], mode="markers+text", text=["예제 (F1 0.700)"],
    textposition="bottom right", textfont=dict(size=11, color="#0b0b0b"),
    marker=dict(size=10, color="#eb6834", line=dict(width=2, color="#fcfcfb")),
    showlegend=False, hovertemplate="P=0.636 R=0.778<br>F1=0.700<extra></extra>",
), row=1, col=1)

rs = [i / 200 for i in range(201)]
P_FIX = 0.9
series = [("산술 평균", "#2a78d6", [(P_FIX + r) / 2 for r in rs]),
          ("기하 평균", "#eb6834", [math.sqrt(P_FIX * r) for r in rs]),
          ("조화 평균 (F1)", "#1baf7a", [f1_score(P_FIX, r) for r in rs])]
for name, color, ys in series:
    fig.add_trace(go.Scatter(
        x=rs, y=ys, mode="lines", name=name, line=dict(width=2, color=color),
        hovertemplate="R=%{x:.2f} → %{y:.3f}<extra>" + name + "</extra>",
    ), row=1, col=2)

fig.update_xaxes(title_text="정밀도 P", range=[0, 1], row=1, col=1)
fig.update_yaxes(title_text="재현율 R", range=[0, 1], row=1, col=1)
fig.update_xaxes(title_text="재현율 R (P=0.9 고정)", range=[0, 1], row=1, col=2)
fig.update_yaxes(title_text="평균값", range=[0, 1], row=1, col=2)
fig.update_layout(
    width=1000, height=460, paper_bgcolor="#fcfcfb", plot_bgcolor="#fcfcfb",
    font=dict(color="#0b0b0b", size=13),
    legend=dict(orientation="h", yanchor="bottom", y=1.06, xanchor="right", x=1),
    margin=dict(t=70, b=60, l=60, r=20),
)

import os
_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."
fig.write_image(os.path.join(_here, "expy.png"), scale=2)  # kaleido 필요
print("expy.png 저장 완료")
_show(fig)
# 출력:
# expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# - $F_1 = \dfrac{2PR}{P+R}$ — 정밀도와 재현율의 **조화 평균**.
# - 조화 평균은 항상 산술 평균 이하이고, 작은 값 쪽으로 끌려간다.
#   그래서 정밀도·재현율 **둘 다** 좋아야만 F1이 좋다.
# - $P+R=0$이면 $F_1=0$으로 정의하고, $P=R$이면 $F_1=P=R$이다.
# - 단, F1 하나만 보면 무엇을 고칠지 모른다 — 15장의 요지대로 오류를 종류별로 나눠야 개선이 시작된다.
