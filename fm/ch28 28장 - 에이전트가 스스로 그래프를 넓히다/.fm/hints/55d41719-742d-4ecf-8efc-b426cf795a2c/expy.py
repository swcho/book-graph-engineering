# %% [markdown]
# # 홉이 깊어지면 수확과 정확도가 왜 «같이» 나빠지는가
#
# **답: 1홉은 노드당 3.2건 · 정확도 86%, 4홉은 0.9건 · 38%.
# 수확과 정확도가 같이 내려가므로 한계 수확(= 새 사실 × 정확도)은 곱으로 무너진다.**
#
# 28장 `ex5_expansion_budget.py` 의 `YIELD_BY_HOP` 표를 그대로 재현하고,
# 원본이 «정책별 합계»로만 보여 준 것을 **홉 단위로 분해**한다.
# 홉마다 얼마를 쓰고 얼마를 건지는지, 그리고 **어디서 손익이 뒤집히는지**를 본다.
#
# ## 모형
#
# 씨앗 노드 $F_1 = 12$ 에서 시작한다. 홉 $h$ 에서 프론티어의 노드 하나를 넓히면
# 새 사실이 $y_h$ 건 나오고 그중 $a_h$ 비율이 맞다. 노드 하나 넓히는 값은 $c = 1{,}400$ 토큰.
#
# $$\text{새 사실}\;N_h = F_h\,y_h,\qquad
# \text{맞는 것}\;R_h = F_h\,y_h\,a_h,\qquad
# \text{틀린 것}\;W_h = F_h\,y_h\,(1-a_h),\qquad
# \text{토큰}\;T_h = F_h\,c$$
#
# 다음 홉의 프론티어는 **맞는 것만** 씨앗이 된다.
#
# $$F_{h+1} = \lfloor F_h\, y_h\, a_h \rfloor = \lfloor F_h\, g_h \rfloor,
# \qquad g_h \equiv y_h a_h$$
#
# 여기서 $g_h$ 를 **확장 계수**라고 부르자. $g_h > 1$ 이면 프론티어가 커지고
# $g_h < 1$ 이면 줄어든다. 수확 $y_h$ 와 정확도 $a_h$ 가 **같이** 내려가므로
# $g_h$ 는 두 번 깎인다 — 이게 이 문제의 핵심이다.
#
# ## 왜 둘이 같이 나빠지나
#
# 세 가지가 겹친다.
#
# 1. **프론티어 확장**: 홉이 깊어질수록 시드에서 멀어진다. 멀어진 노드는
#    질의와의 관련성이 낮아 «넓힐 거리»가 애초에 적다 → $y_h$ 감소.
# 2. **중복 재방문**: 프론티어가 커질수록 이미 방문한 영역과 겹친다.
#    새 사실로 세어지지 않는 중복이 늘어 실질 수확이 더 줄어든다.
# 3. **신뢰도 곱의 감쇠**: 홉 $h$ 의 사실은 홉 $h-1$ 의 사실 **위에** 얹힌다.
#    추론 결과의 신뢰도는 근거 중 가장 약한 것보다 강할 수 없고(28.3절),
#    독립 가정을 쓰면 경로 신뢰도는 곱이 된다.
#
#    $$A_h = \prod_{i=1}^{h} a_i$$
#
#    `ex5` 의 $a_h$ 는 «앞 홉이 맞았다는 조건 아래»의 조건부 정확도다.
#    `frontier = int(right)` 가 틀린 것을 **완벽히** 걸러 준다고 가정한 낙관적 모형이다.
#    거르지 않으면 실제 정확도는 $A_h$ 로 떨어진다. 아래에서 둘을 나란히 잰다.

# %%
# 필요 패키지: plotly, kaleido
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# ex5_expansion_budget.py 와 동일한 설정
YIELD_BY_HOP = {1: (3.2, 0.86), 2: (2.1, 0.71), 3: (1.4, 0.52), 4: (0.9, 0.38)}
COST_PER_EXPAND = 1_400          # 토큰
SEED_NODES = 12

HOPS = sorted(YIELD_BY_HOP)

print(f"{'홉':>3}{'노드당 새 사실 y':>18}{'조건부 정확도 a':>17}"
      f"{'확장 계수 g=y·a':>18}{'경로 신뢰도 ∏a':>17}")
print("-" * 74)
path = 1.0
for h in HOPS:
    y, a = YIELD_BY_HOP[h]
    path *= a
    print(f"{h:>3}{y:>18.1f}{a:>17.0%}{y * a:>18.3f}{path:>17.1%}")

# 출력:
#  홉        노드당 새 사실 y     조건부 정확도 a       확장 계수 g=y·a      경로 신뢰도 ∏a
# --------------------------------------------------------------------------
#   1               3.2              86%             2.752            86.0%
#   2               2.1              71%             1.491            61.1%
#   3               1.4              52%             0.728            31.8%
#   4               0.9              38%             0.342            12.1%

# %% [markdown]
# 표 한 줄에 답이 다 있다.
#
# * 수확 $y$: $3.2 \to 2.1 \to 1.4 \to 0.9$ — 홉당 대략 $\times 0.68$
# * 정확도 $a$: $86\% \to 71\% \to 52\% \to 38\%$ — 홉당 대략 $\times 0.83$
# * 둘의 곱인 확장 계수 $g$: $2.75 \to 1.49 \to \mathbf{0.73} \to 0.34$
#
# **홉 3에서 $g_3 = 0.728 < 1$ 로 내려간다.** 이 지점부터 프론티어는 스스로 줄어든다.
# 확장이 «자기 연료를 못 대는» 구간에 들어간 것이다.
#
# 그리고 경로 신뢰도 $\prod a$ 를 보라. 4홉 사실을 **거르지 않고** 그대로 쓰면
# 표시된 38%가 아니라 **12%** 다. `ex5` 의 38% 는 홉마다 틀린 것을 전부 솎아 냈을 때의 값이다.
# 즉 38%조차 낙관치다.

# %% [markdown]
# ## 1. 홉 단위 분해 — 원본 `expand()` 를 그대로 따라간다

# %%
def expand_trace():
    """ex5_expansion_budget.py 의 expand() 를 홉 단위로 기록한다."""
    frontier = SEED_NODES
    rows = []
    got = right = wrong = tok = 0.0
    for h in HOPS:
        y, acc = YIELD_BY_HOP[h]
        new = frontier * y
        cost = frontier * COST_PER_EXPAND
        r = new * acc
        w = new - r
        tok += cost
        got += new
        right += r
        wrong += w
        rows.append({
            "hop": h, "frontier": frontier,
            "new": new, "right": r, "wrong": w, "cost": cost,
            "cum_new": got, "cum_right": right, "cum_wrong": wrong, "cum_tok": tok,
        })
        frontier = int(r)          # 맞는 것만 다음 홉의 씨앗이 된다
    return rows


TRACE = expand_trace()

print(f"{'홉':>3}{'프론티어':>9}{'새 사실':>9}{'맞는 것':>9}{'틀린 것':>9}"
      f"{'토큰':>10}{'누적 토큰':>11}")
print("-" * 62)
for r in TRACE:
    print(f"{r['hop']:>3}{r['frontier']:>9}{r['new']:>9.1f}{r['right']:>9.1f}"
          f"{r['wrong']:>9.1f}{r['cost']:>10,.0f}{r['cum_tok']:>11,.0f}")

# 출력:
#  홉     프론티어      새 사실      맞는 것      틀린 것        토큰      누적 토큰
# --------------------------------------------------------------
#   1       12     38.4     33.0      5.4    16,800     16,800
#   2       33     69.3     49.2     20.1    46,200     63,000
#   3       49     68.6     35.7     32.9    68,600    131,600
#   4       35     31.5     12.0     19.5    49,000    180,600

# %% [markdown]
# 프론티어가 $12 \to 33 \to 49 \to 35$ 로 **커졌다가 꺾인다**.
# 그래서 **총** 새 사실은 홉 2~3 에서 최대($69.3$, $68.6$)가 된다.
# 노드당 수확은 계속 떨어지는데 총량이 늘어난 건 순전히 프론티어가 커져서다.
# 그런데 그 프론티어를 넓히는 값(토큰)도 같이 커진다 — 홉 3 하나가 68,600 토큰, 전체의 38%다.
#
# 그 68,600 토큰으로 얻은 게 **맞는 사실 35.7건, 틀린 사실 32.9건**이다.
#
# ## 2. 한계 수확 = 새 사실 수 × 정확도
#
# 홉 $h$ 를 «한 번 더» 도는 결정의 손익은 이렇게 잰다.
#
# $$\underbrace{R_h = N_h a_h}_{\text{한계 수확}},\qquad
# \underbrace{E_h = \frac{R_h}{T_h / 10^4}}_{\text{1만 토큰당 정확 사실}},\qquad
# \underbrace{V_h(k) = R_h - k\,W_h}_{\text{순가치}}$$
#
# $k$ 는 «틀린 사실 1건의 대가가 맞는 사실 1건 가치의 몇 배인가»다.
# 검토 비용·오답이 지운 정답·다운스트림 오염을 다 합친 값이라고 보면 된다.

# %%
print(f"{'홉':>3}{'한계 새 사실':>13}{'한계 맞는 것':>13}{'한계 토큰':>11}"
      f"{'한계 효율':>11}{'누적 효율':>11}{'순사실 R-W':>12}")
print("-" * 76)
for r in TRACE:
    marg_eff = r["right"] / (r["cost"] / 10_000)
    cum_eff = r["cum_right"] / (r["cum_tok"] / 10_000)
    print(f"{r['hop']:>3}{r['new']:>13.1f}{r['right']:>13.1f}{r['cost']:>11,.0f}"
          f"{marg_eff:>11.2f}{cum_eff:>11.2f}{r['right'] - r['wrong']:>12.1f}")

print("\n효율 단위: 맞는 사실 / 1만 토큰")
print("한계 효율은 홉 1 대비 홉 4 가 "
      f"{(TRACE[0]['right'] / TRACE[0]['cost']) / (TRACE[3]['right'] / TRACE[3]['cost']):.1f}배 나쁘다.")

# 출력:
#  홉      한계 새 사실      한계 맞는 것      한계 토큰      한계 효율      누적 효율   순사실 R-W
# ----------------------------------------------------------------------------
#   1          38.4          33.0     16,800      19.66      19.66        27.6
#   2          69.3          49.2     46,200      10.65      13.05        29.1
#   3          68.6          35.7     68,600       5.20       8.96         2.7
#   4          31.5          12.0     49,000       2.44       7.19        -7.6
#
# 효율 단위: 맞는 사실 / 1만 토큰
# 한계 효율은 홉 1 대비 홉 4 가 8.0배 나쁘다.

# %% [markdown]
# ## 3. 손익이 뒤집히는 지점은 «하나»가 아니다
#
# 무엇을 손익으로 재느냐에 따라 뒤집히는 홉이 다르다.
#
# | 기준 | 뒤집히는 곳 | 값 |
# |---|---|---|
# | **토큰 효율** $E_h$ 가 지금까지의 평균 아래로 | **홉 2** | $10.65 < 19.66$ |
# | **확장 계수** $g_h < 1$ (프론티어가 스스로 줄어듦) | **홉 3** | $g_3 = 0.728$ |
# | **순사실** $R_h - W_h < 0$ (틀린 게 더 많이 들어옴) | **홉 4** | $-7.6$ |
#
# 홉 2 는 이미 «비싸지기 시작»하는 곳이고, 홉 4 는 «해로워지는» 곳이다.
# `ex5` 가 «평소 2홉»을 권하는 근거가 첫 줄이고,
# «4홉은 사람 검토 대기로»가 셋째 줄이다.
#
# 틀린 것의 대가 $k$ 를 올리면 뒤집히는 지점이 앞으로 당겨진다.

# %%
print(f"{'k':>4}" + "".join(f"{'홉 ' + str(h):>12}" for h in HOPS) + f"{'멈출 홉':>10}")
print("-" * 64)
for k in [0.5, 1, 2, 3, 5]:
    vals = [r["right"] - k * r["wrong"] for r in TRACE]
    stop = next((r["hop"] - 1 for r, v in zip(TRACE, vals) if v < 0), 4)
    print(f"{k:>4}" + "".join(f"{v:>12.1f}" for v in vals) + f"{stop:>10}")

print("\nk = 틀린 사실 1건의 대가 / 맞는 사실 1건의 가치")
print("«멈출 홉» = 순가치가 처음 음수가 되기 «직전» 홉까지만 돈다는 뜻")

# 출력:
#    k          홉 1        홉 2        홉 3        홉 4    멈출 홉
# ----------------------------------------------------------------
#  0.5        30.3        39.2        19.2         2.2         4
#    1        27.6        29.1         2.7        -7.6         3
#    2        22.3         9.0       -30.2       -27.1         2
#    3        16.9       -11.1       -63.1       -46.6         1
#    5         6.1       -51.3      -129.0       -85.7         1
#
# k = 틀린 사실 1건의 대가 / 맞는 사실 1건의 가치
# «멈출 홉» = 순가치가 처음 음수가 되기 «직전» 홉까지만 돈다는 뜻

# %% [markdown]
# 틀린 사실이 맞는 사실만큼만 비싸도($k=1$) 4홉은 손해다.
# 두 배 비싸면($k=2$) 3홉부터 손해고, 세 배면 **2홉도 못 간다**.
# «그래프에 바로 쓰지 말고 검토 대기열로»는 사실상 $k$ 를 낮추는 조치다.
#
# ## 4. 원본 정책 표 재현 — 그리고 예산 버그
#
# `ex5` 의 네 정책을 그대로 돌린다. 위 홉 단위 분해의 누적값과 정확히 맞아야 한다.

# %%
POLICIES = {
    "끝까지 (4홉)":         lambda h, g, w, t: True,
    "2홉까지":              lambda h, g, w, t: h <= 2,
    "토큰 예산 60,000":     lambda h, g, w, t: t < 60_000,
    "틀린 것 30개 넘으면 중단": lambda h, g, w, t: w < 30,
}


def expand(policy):
    frontier = SEED_NODES
    got = right = wrong = tok = 0.0
    hops = 0
    for h in HOPS:
        if not policy(h, got, wrong, tok):
            break
        y, acc = YIELD_BY_HOP[h]
        new = frontier * y
        tok += frontier * COST_PER_EXPAND
        r = new * acc
        got += new
        right += r
        wrong += new - r
        frontier = int(r)
        hops = h
    return got, right, wrong, tok, hops


print(f"{'정책':<24}{'홉':>4}{'새 사실':>9}{'맞는 것':>9}{'틀린 것':>9}"
      f"{'토큰':>10}{'맞는 것/1만토큰':>16}")
print("-" * 84)
for name, pol in POLICIES.items():
    g, r, w, t, hops = expand(pol)
    eff = r / (t / 10_000) if t else 0
    print(f"{name:<24}{hops:>4}{g:>9.0f}{r:>9.0f}{w:>9.0f}{t:>10,.0f}{eff:>16.1f}")

print("\n검증: «끝까지» 누적이 홉 분해와 같은가:",
      abs(expand(POLICIES["끝까지 (4홉)"])[3] - TRACE[-1]["cum_tok"]) < 1e-9)
print("예산 60,000 정책이 실제로 쓴 토큰: "
      f"{expand(POLICIES['토큰 예산 60,000'])[3]:,.0f}  ← 예산 초과")
print("  2홉 «시작 시점» 누적 16,800 → 통과 → 그 홉이 46,200 을 더 씀")

# 출력:
# 정책                        홉      새 사실      맞는 것      틀린 것        토큰      맞는 것/1만토큰
# ------------------------------------------------------------------------------------
# 끝까지 (4홉)                  4      208      130       78   180,600             7.2
# 2홉까지                      2      108       82       25    63,000            13.1
# 토큰 예산 60,000              2      108       82       25    63,000            13.1
# 틀린 것 30개 넘으면 중단          3      176      118       58   131,600             9.0
#
# 검증: «끝까지» 누적이 홉 분해와 같은가: True
# 예산 60,000 정책이 실제로 쓴 토큰: 63,000  ← 예산 초과
#   2홉 «시작 시점» 누적 16,800 → 통과 → 그 홉이 46,200 을 더 씀

# %% [markdown]
# ## 5. 그림
#
# 네 장으로 본다.
#
# 1. 홉별 **노드당 수확 $y$** 와 **정확도 $a$** — 문제의 두 축이 같이 내려간다
# 2. 홉별 **한계 맞는 것 / 틀린 것**과 순사실 — 홉 4 에서 부호가 뒤집힌다
# 3. **누적 토큰 대 누적 정확 사실** — 수확 체감 곡선
# 4. **효율**(1만 토큰당 정확 사실) 한계 대 누적 — 홉 2 에서 이미 갈라진다

# %%
C_YIELD, C_ACC = "#4C78A8", "#E45756"
C_RIGHT, C_WRONG, C_NET = "#54A24B", "#E45756", "#B279A2"

hop = [r["hop"] for r in TRACE]
ys = [YIELD_BY_HOP[h][0] for h in HOPS]
accs = [YIELD_BY_HOP[h][1] for h in HOPS]
rights = [r["right"] for r in TRACE]
wrongs = [r["wrong"] for r in TRACE]
nets = [r["right"] - r["wrong"] for r in TRACE]
marg_eff = [r["right"] / (r["cost"] / 10_000) for r in TRACE]
cum_eff = [r["cum_right"] / (r["cum_tok"] / 10_000) for r in TRACE]
cum_tok = [r["cum_tok"] for r in TRACE]
cum_right = [r["cum_right"] for r in TRACE]

fig = make_subplots(
    rows=2, cols=2,
    specs=[[{"secondary_y": True}, {"secondary_y": True}],
           [{"secondary_y": False}, {"secondary_y": False}]],
    subplot_titles=(
        "1. 노드당 수확과 정확도 — 둘이 같이 내려간다",
        "2. 홉별 한계 수확: 맞는 것 vs 틀린 것",
        "3. 누적 토큰 대비 누적 정확 사실 (수확 체감)",
        "4. 효율 — 한계 vs 누적 (1만 토큰당 정확 사실)",
    ),
    vertical_spacing=0.16, horizontal_spacing=0.11,
)

# 1
fig.add_trace(go.Bar(x=hop, y=ys, name="노드당 새 사실 y", marker_color=C_YIELD,
                     text=[f"{v:.1f}" for v in ys], textposition="inside",
                     insidetextanchor="middle", textfont=dict(color="white")),
              row=1, col=1, secondary_y=False)
fig.add_trace(go.Scatter(x=hop, y=accs, name="정확도 a", mode="lines+markers+text",
                         line=dict(color=C_ACC, width=3), marker=dict(size=10),
                         text=[f"{v:.0%}" for v in accs], textposition="top right"),
              row=1, col=1, secondary_y=True)

# 2
fig.add_trace(go.Bar(x=hop, y=rights, name="맞는 것", marker_color=C_RIGHT,
                     text=[f"{v:.1f}" for v in rights], textposition="outside"),
              row=1, col=2, secondary_y=False)
fig.add_trace(go.Bar(x=hop, y=wrongs, name="틀린 것", marker_color=C_WRONG,
                     text=[f"{v:.1f}" for v in wrongs], textposition="outside"),
              row=1, col=2, secondary_y=False)
fig.add_trace(go.Scatter(x=hop, y=nets, name="순사실 (맞는 것 - 틀린 것)",
                         mode="lines+markers", line=dict(color=C_NET, width=3, dash="dot"),
                         marker=dict(size=9)),
              row=1, col=2, secondary_y=True)
fig.add_hline(y=0, line=dict(color="#888", width=1), row=1, col=2, secondary_y=True)

# 3
fig.add_trace(go.Scatter(x=[0] + cum_tok, y=[0] + cum_right, name="누적 정확 사실",
                         mode="lines+markers+text", line=dict(color=C_RIGHT, width=3),
                         marker=dict(size=11),
                         text=[""] + [f"{h}홉" for h in hop], textposition="top left",
                         showlegend=False),
              row=2, col=1)
fig.add_trace(go.Scatter(x=[0, cum_tok[-1]], y=[0, cum_tok[-1] * cum_eff[0] / 10_000],
                         name="홉 1 효율을 유지했다면", mode="lines",
                         line=dict(color="#888", width=2, dash="dash")),
              row=2, col=1)

# 4
fig.add_trace(go.Scatter(x=hop, y=marg_eff, name="한계 효율", mode="lines+markers+text",
                         line=dict(color=C_ACC, width=3), marker=dict(size=10),
                         text=[f"{v:.1f}" for v in marg_eff], textposition="top right"),
              row=2, col=2)
fig.add_trace(go.Scatter(x=hop, y=cum_eff, name="누적 효율", mode="lines+markers",
                         line=dict(color=C_YIELD, width=3, dash="dash"), marker=dict(size=10)),
              row=2, col=2)

fig.update_xaxes(title_text="홉", tickvals=hop, row=1, col=1)
fig.update_xaxes(title_text="홉", tickvals=hop, row=1, col=2)
fig.update_xaxes(title_text="누적 토큰", row=2, col=1)
fig.update_xaxes(title_text="홉", tickvals=hop, row=2, col=2)
fig.update_yaxes(title_text="노드당 새 사실", range=[0, 4.2], row=1, col=1, secondary_y=False)
fig.update_yaxes(title_text="정확도", range=[0, 1.05], tickformat=".0%",
                 row=1, col=1, secondary_y=True)
fig.update_yaxes(title_text="사실 수", range=[0, 58], row=1, col=2, secondary_y=False)
fig.update_yaxes(title_text="순사실", range=[-45, 58], row=1, col=2, secondary_y=True)
fig.update_yaxes(title_text="누적 정확 사실", row=2, col=1)
fig.update_yaxes(title_text="맞는 사실 / 1만 토큰", range=[0, 22], row=2, col=2)

fig.update_layout(
    title="ex5_expansion_budget.py — 홉이 깊어질수록 수확과 정확도가 같이 나빠진다",
    template="plotly_white", width=1180, height=760, barmode="group",
    legend=dict(orientation="h", yanchor="bottom", y=-0.13, xanchor="center", x=0.5),
    margin=dict(t=90, b=110),
)

_show(fig)
fig.write_image("expy.png", scale=2)
print("expy.png 저장 완료")

# 출력:
# expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# * `YIELD_BY_HOP` 은 홉당 **두 번** 나빠진다. 수확 $3.2 \to 0.9$ (약 $\times 0.28$),
#   정확도 $86\% \to 38\%$ (약 $\times 0.44$). 곱인 한계 수확은 **$\times 0.12$** 로 무너진다.
# * 프론티어가 커져서 홉 2~3 의 **총** 수확은 오히려 크지만, 그 홉의 토큰도 같이 커진다.
#   1만 토큰당 정확 사실은 $19.7 \to 10.7 \to 5.2 \to 2.4$ 로 단조 감소한다.
# * 뒤집히는 지점: **효율은 홉 2**, **프론티어 재생산($g<1$)은 홉 3**, **순사실은 홉 4**.
# * 표시된 홉별 정확도(38%)조차 «앞 홉을 완벽히 걸렀을 때»의 조건부 값이다.
#   거르지 않으면 경로 신뢰도는 $0.86 \times 0.71 \times 0.52 \times 0.38 = 12\%$ 다.
# * 그래서 «평소 2홉, 가끔 4홉 + 사람 검토 대기»가 나온다.
#   깊은 홉을 아예 막는 게 아니라, 깊은 홉의 결과를 **그래프에 바로 쓰지 않는** 것이 요점이다.
