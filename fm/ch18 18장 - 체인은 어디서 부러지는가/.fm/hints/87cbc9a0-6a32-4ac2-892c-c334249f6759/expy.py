# %% [markdown]
# # 체인과 그래프의 격차는 어떤 조건에서 벌어지는가
#
# 체인과 상태 그래프의 차이는 「실패했을 때 무엇을 버리는가」다.
#
# - **체인** — 어느 단계에서 실패하든 **처음부터** 다시. 앞 단계 결과를 전부 버린다.
# - **그래프** — 체크포인트 덕분에 **실패한 단계만** 다시. 앞의 결과는 그대로 남는다.
#
# 단계 비용 $c_i$, 실패 확률 $p_i$일 때 기대 비용은
#
# $$E_{\text{chain}} = \frac{\sum_{i=1}^{n} c_i \prod_{j<i}(1-p_j)}{\prod_{i=1}^{n}(1-p_i)}
# \qquad\qquad
# E_{\text{graph}} = \sum_{i=1}^{n} \frac{c_i}{1-p_i}$$
#
# 분모의 $\prod(1-p_i)$가 핵심이다. 체인은 「전부 한 번에 성공할 확률」로 나누기 때문에
# 단계가 많아지거나($n\uparrow$) 어느 한 단계의 실패율이 오르면($p\uparrow$) 비용이 **지수적으로** 커진다.
# 그래프는 단계별로 독립이라 **선형**으로만 는다.
#
# 이 스크립트는 두 가지를 스윕해서 격차(체인/그래프 비율)가 언제 벌어지는지 본다.
# 1. **실패하는 단계의 위치** — 같은 실패율이라도 뒤쪽 단계가 실패하면 버리는 게 더 많다
# 2. **단계 수** — 단계가 많을수록 「전부 성공」이 어려워진다

# %%
# 필요 패키지: plotly, kaleido (pip install plotly kaleido)
import math
import os


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


def expected_chain(costs, fail_probs):
    """체인 — 어느 단계에서 실패하든 처음부터.
    한 «회차»의 기대 비용을 구하고, 전부 성공할 확률로 나눈다."""
    p_all_ok = math.prod(1 - p for p in fail_probs)
    round_cost = 0.0
    reach = 1.0                     # 이 단계까지 도달할 확률
    for c, p in zip(costs, fail_probs):
        round_cost += reach * c     # 도달했으면 비용을 낸다 (실패해도 낸다)
        reach *= 1 - p
    return round_cost / p_all_ok if p_all_ok > 0 else float("inf")


def expected_graph(costs, fail_probs):
    """상태 그래프 — 실패한 단계만 다시. 단계별 기대 시도 횟수는 1/(1-p)."""
    return sum(c / (1 - p) for c, p in zip(costs, fail_probs))


# 책 ex1의 네 단계 (이름, 시간(초), 실패 확률)
STEPS = [
    ("문서 찾기", 12, 0.05),
    ("요약",       8, 0.08),
    ("초안 작성", 31, 0.18),
    ("검토",      14, 0.10),
]
costs = [s for _, s, _ in STEPS]
probs = [p for _, _, p in STEPS]
ct, gt = expected_chain(costs, probs), expected_graph(costs, probs)
print(f"한 번에 성공하면 {sum(costs)}초")
print(f"체인 기대 {ct:.0f}초 / 그래프 기대 {gt:.0f}초 → 비율 {ct/gt:.2f}배")
# 출력: 한 번에 성공하면 65초
# 출력: 체인 기대 88초 / 그래프 기대 75초 → 비율 1.18배

# %% [markdown]
# ## 실험 1 — 같은 실패율, 위치만 다르면
#
# 단계 6개(비용 각 1, 기본 실패율 2%)에서 **한 단계만** 실패율 $p$를 올린다.
# 그 단계가 첫 번째냐 마지막이냐에 따라 격차가 얼마나 다른지 본다.
#
# 그래프 쪽은 위치와 무관하다($\sum c_i/(1-p_i)$는 순서를 모른다).
# 체인은 $i$번째 단계가 실패하면 $1..i$를 전부 다시 하므로, **뒤쪽 실패일수록 버리는 게 많다**.

# %%
N = 6
BASE_P = 0.02
P_SWEEP = [i / 100 for i in range(0, 51, 2)]     # 0% ~ 50%
POSITIONS = {"첫 단계 실패": 0, "중간 단계 실패": N // 2, "마지막 단계 실패": N - 1}

ratio_by_pos = {}
for label, idx in POSITIONS.items():
    ratios = []
    for p in P_SWEEP:
        fp = [BASE_P] * N
        fp[idx] = p
        c = [1.0] * N
        ratios.append(expected_chain(c, fp) / expected_graph(c, fp))
    ratio_by_pos[label] = ratios

print(f"{'실패율':>6} {'첫 단계':>8} {'중간':>8} {'마지막':>8}   (체인/그래프 비율)")
for p in (0.10, 0.30, 0.50):
    i = P_SWEEP.index(p)
    row = [ratio_by_pos[k][i] for k in POSITIONS]
    print(f"{p*100:>5.0f}% {row[0]:>8.2f} {row[1]:>8.2f} {row[2]:>8.2f}")
# 출력:    실패율     첫 단계       중간      마지막   (체인/그래프 비율)
# 출력:    10%     1.05     1.10     1.13
# 출력:    30%     1.06     1.26     1.38
# 출력:    50%     1.06     1.50     1.78

# %% [markdown]
# 같은 50% 실패율인데 첫 단계면 1.06배(거의 격차 없음), 마지막 단계면 1.78배.
# 첫 단계 실패는 버릴 «앞 단계 결과»가 없어서 체인도 그래프와 다를 게 없다.
# **뒤쪽 단계가 자주 실패할수록** 체인이 버리는 «이미 낸 값»이 커져서 격차가 벌어진다.
#
# ## 실험 2 — 단계 수를 늘리면
#
# 모든 단계의 실패율을 $p$로 같게 두고 단계 수 $n$을 늘린다. 균일한 경우 비율은
#
# $$\frac{E_{\text{chain}}}{E_{\text{graph}}} = \frac{1-(1-p)^n}{\,n\,p\,(1-p)^{n-1}}$$
#
# 분모의 $(1-p)^{n-1}$ 때문에 $n$이 커지면 **지수적으로** 벌어진다.

# %%
N_SWEEP = list(range(2, 13))
P_LEVELS = [0.05, 0.15, 0.30]

ratio_by_p = {}
for p in P_LEVELS:
    ratios = []
    for n in N_SWEEP:
        c = [1.0] * n
        fp = [p] * n
        ratios.append(expected_chain(c, fp) / expected_graph(c, fp))
    ratio_by_p[p] = ratios

print(f"{'단계 수':>6} " + " ".join(f"{'p=' + format(p, '.0%'):>8}" for p in P_LEVELS))
for j, n in enumerate(N_SWEEP):
    if n in (2, 4, 8, 12):
        print(f"{n:>6} " + " ".join(f"{ratio_by_p[p][j]:>8.2f}" for p in P_LEVELS))
# 출력:   단계 수     p=5%    p=15%    p=30%
# 출력:      2     1.03     1.09     1.21
# 출력:      4     1.08     1.30     1.85
# 출력:      8     1.20     1.89     4.77
# 출력:     12     1.35     2.85    13.85

# %% [markdown]
# $p=5\%$면 12단계여도 1.35배 — 체인으로 버틸 만하다.
# $p=30\%$면 12단계에서 14배 가까이 벌어진다. **실패율과 단계 수가 곱으로 작용**한다.

# %%
# 시각화 — 두 실험을 나란히
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 팔레트 (dataviz 검증된 기본값, 라이트 서피스)
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]   # blue, orange, aqua
SURFACE, GRID, MUTED, INK = "#fcfcfb", "#e1e0d9", "#898781", "#0b0b0b"

fig = make_subplots(
    rows=1, cols=2, horizontal_spacing=0.11,
    subplot_titles=("뒤쪽 단계가 실패할수록 (n=6)", "단계가 많을수록 (균일 실패율)"),
)

for color, (label, ratios) in zip(SERIES, ratio_by_pos.items()):
    fig.add_trace(go.Scatter(
        x=[p * 100 for p in P_SWEEP], y=ratios, name=label,
        mode="lines", line=dict(color=color, width=2), legendgroup="1",
    ), row=1, col=1)

for color, p in zip(SERIES, P_LEVELS):
    fig.add_trace(go.Scatter(
        x=N_SWEEP, y=ratio_by_p[p], name=f"실패율 {p:.0%}",
        mode="lines+markers", line=dict(color=color, width=2),
        marker=dict(size=8), legendgroup="2",
    ), row=1, col=2)

fig.update_layout(
    title=dict(text="체인/그래프 기대 비용 비율 — 격차가 벌어지는 두 조건",
               font=dict(size=16, color=INK)),
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
    font=dict(family="AppleGothic, sans-serif", size=12, color=INK),
    width=980, height=440,
    legend=dict(orientation="h", y=-0.18, font=dict(size=11)),
    margin=dict(t=80, b=90),
)
fig.update_xaxes(title_text="한 단계의 실패율 (%)", row=1, col=1,
                 gridcolor=GRID, linecolor=MUTED, title_font=dict(color=MUTED))
fig.update_xaxes(title_text="단계 수 n", row=1, col=2,
                 gridcolor=GRID, linecolor=MUTED, title_font=dict(color=MUTED))
fig.update_yaxes(title_text="체인 ÷ 그래프 (배)", row=1, col=1,
                 gridcolor=GRID, linecolor=MUTED, title_font=dict(color=MUTED))
fig.update_yaxes(title_text="체인 ÷ 그래프 (배, log)", type="log", row=1, col=2,
                 gridcolor=GRID, linecolor=MUTED, title_font=dict(color=MUTED))

_show(fig)

_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."
fig.write_image(os.path.join(_here, "expy.png"), scale=2)   # kaleido 필요
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# - 격차는 **뒤쪽 단계가 자주 실패할수록**, 그리고 **단계가 많을수록** 벌어진다.
#   두 조건 모두 체인의 분모 $\prod(1-p_i)$를 갉아먹고, 뒤쪽 실패는 「이미 낸 값」을 통째로 버리게 만들기 때문.
# - 뒤집으면 — 단계가 두세 개고 실패가 드물면 체인으로 충분하다. 대부분의 시스템은 거기서 시작하는 게 맞다.
# - 그리고 구조를 그래프로 바꿔도 **실패율 자체는 안 줄어든다**. 줄어드는 것은 실패의 *값*(다시 내는 비용)이다.
