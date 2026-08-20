# %% [markdown]
# # ex3_budget_split.py — 세 가지 예산 배분 전략
#
# 20장 예제 3은 하나의 총예산을 여러 단계가 나눠 쓰는 상황에서
# **세 가지 배분 전략**을 비교한다.
#
# 1. **나누지 않음** — 먼저 오는 쪽이 다 쓴다 (`no_split`)
# 2. **균등 분배** — 총예산을 단계 수로 나눈다 (`even_split`)
# 3. **최소분 먼저 떼어 두기** — 최소 필요분을 예약하고 남는 걸 앞에서부터 쓴다 (`reserve_first`)
#
# 이 노트북에서는 세 전략을 그대로 구현하고, 총예산 $T$ 를 바꿔 가며
# **어느 지점에서 «검토» 단계가 굶는지**를 전략별로 대비한다.

# %%
# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
from plotly.subplots import make_subplots
import plotly.graph_objects as go


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1. 문제 설정
#
# 단계마다 두 개의 숫자가 있다.
#
# - $need_i$ — 그 단계가 **최소한** 있어야 일을 하는 양
# - $greedy_i$ — 여유가 있으면 **더 쓰고 싶은** 양
#
# 즉 단계 $i$ 의 «욕심껏 쓰고 싶은 양»은 $want_i = need_i + greedy_i$ 다.

# %%
TOTAL = 100.0

# (단계, 최소 필요 예산, 여유가 있으면 더 쓰는 양)
STAGES = [
    ("검색",  8,  40),
    ("요약",  6,  25),
    ("초안", 14,  60),
    ("검토", 10,  20),
]

NEED_SUM = sum(need for _, need, _ in STAGES)
WANT_SUM = sum(need + greedy for _, need, greedy in STAGES)

print(f"단계 수        {len(STAGES)}")
print(f"최소 필요분 합계 {NEED_SUM}")
print(f"욕심 합계       {WANT_SUM}")
print(f"전체 예산       {TOTAL:.0f}")
# 출력:
# 단계 수        4
# 최소 필요분 합계 38
# 욕심 합계       183
# 전체 예산       100

# %% [markdown]
# 욕심 합계 183 > 총예산 100 이다. 즉 **모두를 만족시킬 수는 없다.**
# 배분 전략이란 결국 «누구를 깎을 것인가»를 정하는 규칙이다.

# %% [markdown]
# ## 2. 전략 1 — 나누지 않음 (선착순)
#
# 앞 단계부터 원하는 만큼 다 준다. 남은 게 없으면 뒤는 0을 받는다.
#
# $$got_i = \min\left(want_i,\; T - \sum_{j<i} got_j\right)$$

# %%
def no_split(total):
    """먼저 오는 단계가 여유분을 다 쓴다."""
    left = total
    out = []
    for name, need, greedy in STAGES:
        want = need + greedy
        got = min(want, left)
        left -= got
        out.append((name, got, got >= need))
    return out


for row in no_split(TOTAL):
    print(row)
# 출력:
# ('검색', 48, True)
# ('요약', 31, True)
# ('초안', 21.0, True)
# ('검토', 0.0, False)

# %% [markdown]
# ## 3. 전략 2 — 균등 분배
#
# 단계가 $n$ 개면 각자 $T/n$ 씩. 단계별 사정을 전혀 안 본다.
#
# $$got_i = \frac{T}{n}$$

# %%
def even_split(total):
    share = total / len(STAGES)
    return [(n, share, share >= need) for n, need, _ in STAGES]


for row in even_split(TOTAL):
    print(row)
# 출력:
# ('검색', 25.0, True)
# ('요약', 25.0, True)
# ('초안', 25.0, True)
# ('검토', 25.0, True)

# %% [markdown]
# ## 4. 전략 3 — 최소분 먼저 떼어 두기
#
# 먼저 $\sum_i need_i$ 를 통째로 예약하고, 남은 여유분
# $spare = T - \sum_i need_i$ 를 앞 단계부터 욕심껏 나눠 준다.
#
# $$got_i = need_i + \min\left(greedy_i,\; spare - \sum_{j<i} extra_j\right)$$

# %%
def reserve_first(total):
    """최소 필요분을 먼저 떼어 두고 나머지를 앞에서부터 쓴다."""
    reserved = sum(need for _, need, _ in STAGES)
    spare = total - reserved
    out = []
    for name, need, greedy in STAGES:
        extra = min(greedy, spare)
        spare -= extra
        out.append((name, need + extra, True))
    return out


for row in reserve_first(TOTAL):
    print(row)
# 출력:
# ('검색', 48, True)
# ('요약', 28.0, True)
# ('초안', 14.0, True)
# ('검토', 10.0, True)

# %% [markdown]
# ## 5. 원문 실행 결과 재현 (T = 100)
#
# 원문 `main()` 이 찍는 표와 같은 내용이다.

# %%
STRATEGIES = [
    ("나누지 않음", no_split),
    ("균등 분배", even_split),
    ("최소분 먼저", reserve_first),
]


def starved_count(rows):
    """플래그가 아니라 «실제로» 최소분을 못 받은 단계를 센다."""
    needs = {n: need for n, need, _ in STAGES}
    return sum(1 for name, got, _ in rows if got < needs[name])


print(f"{'단계':<6} {'나누지 않음':>12} {'균등 분배':>10} {'최소분 먼저':>12}")
print("-" * 44)
table = {label: fn(TOTAL) for label, fn in STRATEGIES}
for i, (name, need, _) in enumerate(STAGES):
    vals = " ".join(f"{table[label][i][1]:>11.1f}" for label, _ in STRATEGIES)
    print(f"{name:<6} {vals}")
print("-" * 44)
for label, _ in STRATEGIES:
    print(f"{label:<12} 굶은 단계 {starved_count(table[label])}개")
# 출력:
# 단계        나누지 않음      균등 분배      최소분 먼저
# --------------------------------------------
# 검색           48.0        25.0        48.0
# 요약           31.0        25.0        28.0
# 초안           21.0        25.0        14.0
# 검토            0.0        25.0        10.0
# --------------------------------------------
# 나누지 않음       굶은 단계 1개
# 균등 분배        굶은 단계 0개
# 최소분 먼저       굶은 단계 0개

# %% [markdown]
# 총예산 100 에서 **«나누지 않음»만 검토 단계가 0을 받는다.**
# 검색(48)과 요약(31)이 여유분을 다 써 버려서 초안은 21밖에 못 받고,
# 검토 차례에는 남은 게 없다.
#
# 하필 검토가 **품질을 지키는 단계**다.
# 제일 중요한 단계가 제일 마지막에 있어서 제일 먼저 굶는 구조다.

# %% [markdown]
# ## 6. 총예산을 바꿔 가며 — 검토 단계는 언제부터 살아나나
#
# 각 전략에서 검토 단계가 최소분 10을 받으려면 총예산이 얼마여야 하는지
# 손으로도 풀 수 있다.
#
# | 전략 | 검토가 받는 양 | $got_{검토} \ge 10$ 조건 |
# |---|---|---|
# | 나누지 않음 | $\max(0,\ T - 153)$ | $T \ge 163$ |
# | 균등 분배 | $T/4$ | $T \ge 40$ |
# | 최소분 먼저 | $10$ (단, $T \ge 38$) | $T \ge 38$ |
#
# ($153 = 48 + 31 + 74$, 앞 세 단계의 $want$ 합계)
#
# 모든 단계가 굶지 않는 임계 예산은 또 다르다.
# 균등 분배는 제일 큰 최소분(초안 14)에 4를 곱한 **56** 이 필요하다.

# %%
def first_ok_budget(fn, hi=400):
    """모든 단계가 최소분을 받는 최소 총예산(정수 스캔)."""
    for t in range(0, hi + 1):
        if starved_count(fn(float(t))) == 0:
            return t
    return None


for label, fn in STRATEGIES:
    print(f"{label:<12} 모든 단계가 사는 최소 총예산 = {first_ok_budget(fn)}")
# 출력:
# 나누지 않음       모든 단계가 사는 최소 총예산 = 163
# 균등 분배        모든 단계가 사는 최소 총예산 = 56
# 최소분 먼저       모든 단계가 사는 최소 총예산 = 38

# %% [markdown]
# `reserve_first` 의 임계값 38 은 정확히 $\sum_i need_i$ 다.
# **이론적 하한과 같다.** 이보다 적은 예산으로는 어떤 전략도 모두를 살릴 수 없다.
#
# > 주의 — 원문 `reserve_first` 는 «충분한가» 플래그를 항상 `True` 로 돌려준다.
# > $T < 38$ 이면 `spare` 가 음수라 실제 배정은 최소분보다 적은데도 «예»라고 말한다.
# > 위 `starved_count()` 는 플래그 대신 배정량을 직접 비교해서 이걸 잡는다.

# %%
budgets = list(range(0, 201, 2))
review_need = dict((n, need) for n, need, _ in STAGES)["검토"]

curves = {}
starve_curves = {}
for label, fn in STRATEGIES:
    curves[label] = [fn(float(t))[3][1] for t in budgets]      # 검토 배정량
    starve_curves[label] = [starved_count(fn(float(t))) for t in budgets]

for label, _ in STRATEGIES:
    ys = curves[label]
    print(f"{label:<12} T=100 → 검토 {ys[budgets.index(100)]:>5.1f} | "
          f"T=200 → 검토 {ys[-1]:>5.1f}")
# 출력:
# 나누지 않음       T=100 → 검토   0.0 | T=200 → 검토  30.0
# 균등 분배        T=100 → 검토  25.0 | T=200 → 검토  50.0
# 최소분 먼저       T=100 → 검토  10.0 | T=200 → 검토  30.0

# %% [markdown]
# ## 7. 그림
#
# - 왼쪽: 총예산에 따라 **검토 단계가 받는 양**. 점선(=10)이 최소 필요분.
#   선이 점선 아래면 그 예산에서 검토는 굶는다.
# - 오른쪽: $T=100$ 일 때 전략별 배분을 쌓은 막대.

# %%
COLORS = {"나누지 않음": "#d1495b", "균등 분배": "#edae49", "최소분 먼저": "#2a9d8f"}
STAGE_COLORS = ["#4c78a8", "#72b7b2", "#f58518", "#e45756"]

fig = make_subplots(
    rows=1, cols=2,
    column_widths=[0.58, 0.42],
    subplot_titles=("총예산 대비 «검토» 단계 배정량", "T = 100 일 때 단계별 배분"),
)

for label, _ in STRATEGIES:
    fig.add_trace(
        go.Scatter(x=budgets, y=curves[label], mode="lines", name=label,
                   line=dict(color=COLORS[label], width=3),
                   hovertemplate="총예산 %{x}<br>검토 %{y:.1f}<extra>" + label + "</extra>"),
        row=1, col=1,
    )

fig.add_hline(y=review_need, line_dash="dash", line_color="#888",
              annotation_text="검토 최소분 10", annotation_position="top left",
              row=1, col=1)

# 모든 단계가 사는 임계 예산을 점으로 찍는다
for label, fn in STRATEGIES:
    t = first_ok_budget(fn)
    fig.add_trace(
        go.Scatter(x=[t], y=[fn(float(t))[3][1]], mode="markers+text",
                   marker=dict(color=COLORS[label], size=13, symbol="circle",
                               line=dict(color="white", width=2)),
                   text=[f"T={t}"], textposition="top center",
                   textfont=dict(color=COLORS[label], size=12),
                   showlegend=False, hoverinfo="skip"),
        row=1, col=1,
    )

for i, (name, _, _) in enumerate(STAGES):
    fig.add_trace(
        go.Bar(x=[label for label, _ in STRATEGIES],
               y=[table[label][i][1] for label, _ in STRATEGIES],
               name=name, marker_color=STAGE_COLORS[i], showlegend=False,
               text=[f"{name} {table[label][i][1]:.0f}" for label, _ in STRATEGIES],
               textposition="inside", insidetextanchor="middle",
               textfont=dict(color="white", size=13)),
        row=1, col=2,
    )

fig.update_layout(
    barmode="stack",
    title="예산 배분 전략 세 가지 — 뒤쪽 단계는 언제 굶는가",
    template="plotly_white",
    height=540, width=1100,
    margin=dict(t=110, b=110),
    legend=dict(orientation="h", yanchor="top", y=-0.16,
                xanchor="center", x=0.28, title_text=""),
)
fig.update_xaxes(title_text="총예산 T", row=1, col=1)
fig.update_yaxes(title_text="검토 단계 배정량", row=1, col=1)
fig.update_yaxes(title_text="배정량 누적", row=1, col=2)

_show(fig)

import os
_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_png, scale=2)
print("saved:", _png)
# 출력:
# saved: .../expy.png

# %% [markdown]
# ## 8. 정리
#
# | 전략 | T=100 검토 배정 | 모두 사는 최소 T | 성격 |
# |---|---|---|---|
# | 나누지 않음 | **0.0** | 163 | 선착순. 뒤가 굶는다 |
# | 균등 분배 | 25.0 | 56 | 안전하지만 낭비 (요약은 6이면 되는데 25) |
# | 최소분 먼저 | 10.0 | **38** | 하한과 같다. 대개 답 |
#
# - «나누지 않음»은 총예산이 **욕심 합계에 가까워질 때까지** 뒤쪽을 굶긴다.
#   여기서는 163 이 필요한데, 실제 총예산은 100 이다.
# - «균등 분배»는 굶기지는 않지만 단계별 사정을 무시한다.
#   요약은 6이면 되는데 25를 받고, 그만큼이 다른 데 못 간다.
# - «최소분 먼저»는 하한 38 에서 이미 모두를 살린다.
#   단, **«최소가 얼마인지»를 알아야** 쓸 수 있다.
#   그건 실측해야 하고, 실측하려면 단계별 토큰을 따로 세고 있어야 한다.
#   그 계측을 안 해 두면 이 전략을 못 쓴다.
