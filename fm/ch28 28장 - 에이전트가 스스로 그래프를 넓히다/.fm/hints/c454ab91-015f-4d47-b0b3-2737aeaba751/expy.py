# %% [markdown]
# # `토큰 예산 60,000`이 63,000을 쓴 이유 — 검사 지점의 입도
#
# 28장 `ex5_expansion_budget.py`의 예산 검사 로직을 재현하고,
# 세 가지 검사 방식의 최종 토큰 사용량과 수확을 비교한다.
#
# - **(a) 홉 시작 전에만 검사** — 원본 `ex5`의 방식. 예산을 넘긴다.
# - **(b) 노드 단위 검사** — 홉 안에서 노드 하나 넓힐 때마다 검사한다.
# - **(c) 홉 예상 비용 사전 산정** — 홉을 시작하기 전에 그 홉이 쓸 비용을 미리 더해 본다.
#
# 핵심은 하나다. **초과량은 «검사 지점 사이의 최대 단위 작업 비용»으로 결정된다.**

# %%
# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)

import plotly.graph_objects as go


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# ex5 원본 파라미터
YIELD_BY_HOP = {1: (3.2, 0.86), 2: (2.1, 0.71), 3: (1.4, 0.52), 4: (0.9, 0.38)}
COST_PER_EXPAND = 1_400  # 노드 한 개를 넓히는 데 드는 토큰
SEED_NODES = 12
BUDGET = 60_000

print("홉  노드당 새 사실  맞을 확률   노드당 비용")
for h, (y, a) in YIELD_BY_HOP.items():
    print(f"{h:>2}{y:>14.1f}{a:>11.0%}{COST_PER_EXPAND:>14,}")
print(f"\n씨앗 노드 {SEED_NODES}개, 예산 {BUDGET:,} 토큰")

# 출력:
# 홉  노드당 새 사실  맞을 확률   노드당 비용
#  1           3.2        86%         1,400
#  2           2.1        71%         1,400
#  3           1.4        52%         1,400
#  4           0.9        38%         1,400
#
# 씨앗 노드 12개, 예산 60,000 토큰

# %% [markdown]
# ## (a) 홉 시작 전에만 검사 — 원본 `ex5`
#
# 정책 함수는 `lambda h, g, w, t: t < 60_000`. 홉 루프의 맨 앞에서 한 번만 불린다.
# 홉이 시작되고 나면 그 홉이 얼마를 쓰든 아무도 안 본다.
#
# $$ T_{\text{final}} = \sum_{h=1}^{H} c_h, \qquad c_h = f_h \cdot 1400 $$
#
# 여기서 $H$는 $\sum_{h<H} c_h < B$ 를 만족하는 마지막 홉이다.

# %%
def expand_hop_gate(budget=BUDGET, verbose=True):
    """(a) 홉을 «시작하기 전»에만 예산을 검사한다. ex5 원본과 동일."""
    frontier = SEED_NODES
    got = right = wrong = tok = 0.0
    trace = [(0, 0.0)]  # (넓힌 노드 누적 수, 누적 토큰)
    nodes_done = 0
    for hop in range(1, 5):
        if not (tok < budget):  # ← 검사는 여기 한 번뿐
            if verbose:
                print(f"  {hop}홉: 시작 전 누적 {tok:>7,.0f} → 예산 초과, 중단")
            break
        if verbose:
            print(
                f"  {hop}홉: 시작 전 누적 {tok:>7,.0f} < {budget:,} 통과 "
                f"→ 프런티어 {frontier}노드 × {COST_PER_EXPAND:,} = "
                f"{frontier * COST_PER_EXPAND:,} 토큰 소비"
            )
        y, acc = YIELD_BY_HOP[hop]
        new = frontier * y
        tok += frontier * COST_PER_EXPAND
        nodes_done += frontier
        trace.append((nodes_done, tok))
        r = new * acc
        got += new
        right += r
        wrong += new - r
        frontier = int(r)
    return got, right, wrong, tok, trace


print("(a) 홉 시작 전에만 검사")
a_got, a_right, a_wrong, a_tok, a_trace = expand_hop_gate()
print(f"\n  최종 토큰 {a_tok:,.0f}  (예산 {BUDGET:,}, 초과 {a_tok - BUDGET:+,.0f})")
print(f"  새 사실 {a_got:.0f}  맞는 것 {a_right:.0f}  틀린 것 {a_wrong:.0f}")

# 출력:
# (a) 홉 시작 전에만 검사
#   1홉: 시작 전 누적       0 < 60,000 통과 → 프런티어 12노드 × 1,400 = 16,800 토큰 소비
#   2홉: 시작 전 누적  16,800 < 60,000 통과 → 프런티어 33노드 × 1,400 = 46,200 토큰 소비
#   3홉: 시작 전 누적  63,000 → 예산 초과, 중단
#
#   최종 토큰 63,000  (예산 60,000, 초과 +3,000)
#   새 사실 108  맞는 것 82  틀린 것 25

# %% [markdown]
# ### 답이 여기 있다
#
# 2홉을 **시작할 때** 누적은 16,800이었다. $16{,}800 < 60{,}000$ 이므로 통과.
# 그런데 그 홉의 프런티어는 33노드였고, 홉 하나가 $33 \times 1400 = 46{,}200$ 을 썼다.
# 검사와 검사 사이에 46,200짜리 덩어리가 통째로 들어간 것이다.
#
# $$ 16{,}800 + 46{,}200 = 63{,}000 > 60{,}000 $$
#
# 예산은 «넘지 않게 막는 것»이 아니라 «넘은 다음에 알아차리는 것»이 되어 버렸다.

# %%
# 프런티어가 어떻게 커지는지 — 홉 비용이 커지면 초과 가능량도 같이 커진다
frontier = SEED_NODES
print("홉   프런티어      홉 비용   (검사 사이의 단위 작업 크기)")
hop_costs = []
for hop in range(1, 5):
    cost = frontier * COST_PER_EXPAND
    hop_costs.append(cost)
    print(f"{hop:>2}{frontier:>11}{cost:>13,}")
    y, acc = YIELD_BY_HOP[hop]
    frontier = int(frontier * y * acc)
print(f"\n가장 큰 홉 비용: {max(hop_costs):,}")

# 출력:
# 홉   프런티어      홉 비용   (검사 사이의 단위 작업 크기)
#  1         12       16,800
#  2         33       46,200
#  3         49       68,600
#  4         35       49,000
#
# 가장 큰 홉 비용: 68,600

# %% [markdown]
# ## 최악 초과량의 상한식
#
# 검사 조건이 «누적 $t$ 가 예산 $B$ 미만이면 진행»일 때, 마지막으로 통과한 시점의
# 누적은 최대 $B - 1$ 토큰이다(정수 토큰 기준). 그 뒤에 검사 없이 들어가는 단위 작업의
# 비용을 $c$ 라 하면
#
# $$ T_{\text{final}} \le (B - 1) + \max_h c_h $$
#
# $$ \text{초과량} = T_{\text{final}} - B \le \max_h c_h - 1 $$
#
# 즉 **초과 상한은 예산과 무관하고, 오로지 «검사 지점 사이 최대 단위 작업 비용»이 정한다.**
# 홉 단위 검사면 $c = f_h \cdot 1400$ (프런티어 크기에 비례),
# 노드 단위 검사면 $c = 1400$ 으로 고정된다.
#
# $$ \frac{\text{홉 단위 초과 상한}}{\text{노드 단위 초과 상한}} = \max_h f_h $$

# %%
worst_hop = max(hop_costs)
print(f"홉 단위 검사   초과 상한 ≤ {worst_hop - 1:>7,} 토큰  (예산 대비 {(worst_hop - 1) / BUDGET:>5.1%})")
print(f"노드 단위 검사 초과 상한 ≤ {COST_PER_EXPAND - 1:>7,} 토큰  (예산 대비 {(COST_PER_EXPAND - 1) / BUDGET:>5.1%})")
print(f"사전 비용 산정 초과 상한 ≤ {0:>7,} 토큰  (예산 대비 {0.0:>5.1%})")
print(f"\n이번 실행의 실제 초과: {a_tok - BUDGET:,.0f} 토큰 (2홉 비용 46,200이 만든 것)")
print(f"입도 비율 max f_h = {worst_hop / COST_PER_EXPAND:.0f}배")

# 출력:
# 홉 단위 검사   초과 상한 ≤  68,599 토큰  (예산 대비 114.3%)
# 노드 단위 검사 초과 상한 ≤   1,399 토큰  (예산 대비  2.3%)
# 사전 비용 산정 초과 상한 ≤       0 토큰  (예산 대비  0.0%)
#
# 이번 실행의 실제 초과: 3,000 토큰 (2홉 비용 46,200이 만든 것)
# 입도 비율 max f_h = 49배

# %% [markdown]
# ## (b) 노드 단위 검사
#
# 홉 안으로 들어가 노드 하나를 넓힐 때마다 검사한다.
# 예산이 바닥나면 홉을 **중간에서** 끊는다. 그 홉의 수확은 넓힌 노드 수만큼만 얻는다.

# %%
def expand_node_gate(budget=BUDGET, verbose=True):
    """(b) 노드 하나를 넓히기 전마다 예산을 검사한다."""
    frontier = SEED_NODES
    got = right = wrong = tok = 0.0
    trace = [(0, 0.0)]
    nodes_done = 0
    for hop in range(1, 5):
        y, acc = YIELD_BY_HOP[hop]
        expanded = 0
        for _ in range(frontier):
            if tok + COST_PER_EXPAND > budget:  # ← 노드마다 검사
                break
            tok += COST_PER_EXPAND
            expanded += 1
            nodes_done += 1
            trace.append((nodes_done, tok))
        if verbose:
            if expanded == frontier:
                mark = ""
            elif expanded == 0:
                mark = "  ← 예산 소진, 홉에 진입 못 함"
            else:
                mark = "  ← 홉 중간에서 끊김"
            print(f"  {hop}홉: 프런티어 {frontier:>3}노드 중 {expanded:>3}노드 넓힘, 누적 {tok:>7,.0f}{mark}")
        if expanded == 0:
            break
        new = expanded * y
        r = new * acc
        got += new
        right += r
        wrong += new - r
        frontier = int(r)
    return got, right, wrong, tok, trace


print("(b) 노드 단위 검사")
b_got, b_right, b_wrong, b_tok, b_trace = expand_node_gate()
print(f"\n  최종 토큰 {b_tok:,.0f}  (예산 {BUDGET:,}, 초과 {b_tok - BUDGET:+,.0f})")
print(f"  새 사실 {b_got:.0f}  맞는 것 {b_right:.0f}  틀린 것 {b_wrong:.0f}")

# 출력:
# (b) 노드 단위 검사
#   1홉: 프런티어  12노드 중  12노드 넓힘, 누적  16,800
#   2홉: 프런티어  33노드 중  30노드 넓힘, 누적  58,800  ← 홉 중간에서 끊김
#   3홉: 프런티어  44노드 중   0노드 넓힘, 누적  58,800  ← 예산 소진, 홉에 진입 못 함
#
#   최종 토큰 58,800  (예산 60,000, 초과 -1,200)
#   새 사실 101  맞는 것 78  틀린 것 24

# %% [markdown]
# ## (c) 홉 예상 비용 사전 산정
#
# 홉을 시작하기 전에 «이 홉은 얼마 쓸 것인가»를 미리 계산해서 더해 본다.
# $t + c_h > B$ 면 그 홉을 아예 시작하지 않는다. 예산은 **절대** 넘지 않는다.
# 대신 남은 예산을 못 쓰고 버리는 손해가 생긴다.

# %%
def expand_precost(budget=BUDGET, verbose=True):
    """(c) 홉의 예상 비용을 미리 산정해서 들어갈지 말지 정한다."""
    frontier = SEED_NODES
    got = right = wrong = tok = 0.0
    trace = [(0, 0.0)]
    nodes_done = 0
    for hop in range(1, 5):
        est = frontier * COST_PER_EXPAND  # ← 이 홉의 예상 비용
        if tok + est > budget:
            if verbose:
                print(f"  {hop}홉: 예상 {est:,} → 누적이 {tok + est:,.0f}이 되어 예산 초과. 홉 자체를 건너뜀")
            break
        if verbose:
            print(f"  {hop}홉: 예상 {est:,} → 누적 {tok + est:>7,.0f} ≤ {budget:,} 진행")
        y, acc = YIELD_BY_HOP[hop]
        new = frontier * y
        tok += est
        nodes_done += frontier
        trace.append((nodes_done, tok))
        r = new * acc
        got += new
        right += r
        wrong += new - r
        frontier = int(r)
    return got, right, wrong, tok, trace


print("(c) 홉 예상 비용 사전 산정")
c_got, c_right, c_wrong, c_tok, c_trace = expand_precost()
print(f"\n  최종 토큰 {c_tok:,.0f}  (예산 {BUDGET:,}, 초과 {c_tok - BUDGET:+,.0f})")
print(f"  새 사실 {c_got:.0f}  맞는 것 {c_right:.0f}  틀린 것 {c_wrong:.0f}")
print(f"  못 쓰고 남긴 예산 {BUDGET - c_tok:,.0f} 토큰 ({(BUDGET - c_tok) / BUDGET:.0%})")

# 출력:
# (c) 홉 예상 비용 사전 산정
#   1홉: 예상 16,800 → 누적  16,800 ≤ 60,000 진행
#   2홉: 예상 46,200 → 누적이 63,000이 되어 예산 초과. 홉 자체를 건너뜀
#
#   최종 토큰 16,800  (예산 60,000, 초과 -43,200)
#   새 사실 38  맞는 것 33  틀린 것 5
#   못 쓰고 남긴 예산 43,200 토큰 (72%)

# %% [markdown]
# ## 세 방식 비교

# %%
rows = [
    ("(a) 홉 시작 전에만", a_got, a_right, a_wrong, a_tok, worst_hop - 1),
    ("(b) 노드 단위", b_got, b_right, b_wrong, b_tok, COST_PER_EXPAND - 1),
    ("(c) 홉 예상 비용 사전 산정", c_got, c_right, c_wrong, c_tok, 0),
]

header = f"{'검사 방식':<26}{'새 사실':>8}{'맞는 것':>8}{'틀린 것':>8}{'토큰':>9}{'예산차':>9}{'남긴 예산':>10}{'초과상한':>10}"
print(header)
print("-" * len(header))
for name, g, r, w, t, ub in rows:
    print(f"{name:<26}{g:>8.0f}{r:>8.0f}{w:>8.0f}{t:>9,.0f}{t - BUDGET:>+9,.0f}{max(0, BUDGET - t):>10,.0f}{ub:>10,}")

print("\n맞는 것 / 1만 토큰")
for name, g, r, w, t, ub in rows:
    print(f"  {name:<26}{r / (t / 10_000):>6.1f}")

# 출력:
# 검사 방식                       새 사실    맞는 것   틀린 것      토큰     예산차    남긴 예산     초과상한
# -----------------------------------------------------------------------------------------------
# (a) 홉 시작 전에만                 108      82      25   63,000   +3,000         0    68,599
# (b) 노드 단위                      101      78      24   58,800   -1,200     1,200     1,399
# (c) 홉 예상 비용 사전 산정            38      33       5   16,800  -43,200    43,200         0
#
# 맞는 것 / 1만 토큰
#   (a) 홉 시작 전에만            13.1
#   (b) 노드 단위                 13.2
#   (c) 홉 예상 비용 사전 산정      19.7

# %% [markdown]
# ### 읽는 법
#
# - **(a)** 는 예산을 5% 넘겼다. 이번엔 3,000이었지만 이건 «운»이다.
#   프런티어가 49였다면 68,600짜리 홉이 통째로 들어가 초과가 **68,599**까지 갈 수 있다.
#   예산의 100%를 넘는 초과가 상한선 안에 있다는 뜻이다.
# - **(b)** 는 예산을 지키면서 수확의 94%를 건졌다. 손해는 1,200 토큰(노드 하나 값 미만)의 낭비뿐.
# - **(c)** 는 예산을 절대 안 넘지만 72%를 못 쓰고 남겼다. 안전 대신 «홉 전체를 통째로 포기»한다.
#   효율(맞는 것/1만 토큰)이 제일 높게 나오는데, 이건 정확도 높은 1홉만 돌았기 때문이지
#   좋은 정책이라서가 아니다. 절대 수확은 3분의 1이다.
#
# 실무 조합은 **(b) + (c)**: 홉 예상 비용으로 «들어갈지»를 정하고,
# 예상이 빗나갈 때를 대비해 노드 단위 검사를 안전망으로 둔다.

# %% [markdown]
# ## 누적 토큰 곡선

# %%
# 세 정책 모두 노드당 1,400으로 같은 기울기라 선이 겹친다.
# 굵기/점선/투명도를 달리해 셋을 모두 보이게 한다.
series = [
    ("(a) 홉 시작 전에만 검사", a_trace, "#d62728", "solid", 11, 0.35),
    ("(b) 노드 단위 검사", b_trace, "#2ca02c", "dash", 3.5, 1.0),
    ("(c) 홉 예상 비용 사전 산정", c_trace, "#1f77b4", "dot", 3.5, 1.0),
]

fig = go.Figure()
for name, trace, color, dash, width, opacity in series:
    xs = [p[0] for p in trace]
    ys = [p[1] for p in trace]
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="lines",
            name=name,
            opacity=opacity,
            line=dict(color=color, dash=dash, width=width),
            hovertemplate="넓힌 노드 %{x}개<br>누적 %{y:,.0f} 토큰<extra>" + name + "</extra>",
        )
    )
    # 각 정책이 멈춘 지점
    fig.add_trace(
        go.Scatter(
            x=[xs[-1]],
            y=[ys[-1]],
            mode="markers+text",
            marker=dict(color=color, size=13, symbol="circle", line=dict(color="white", width=1.5)),
            text=[f"{ys[-1]:,.0f}"],
            textposition="middle right" if name.startswith("(c)") else "top center",
            textfont=dict(color=color, size=12),
            showlegend=False,
            hoverinfo="skip",
        )
    )

# (a)의 «검사 지점» — 홉 경계에서만 예산을 본다
fig.add_trace(
    go.Scatter(
        x=[p[0] for p in a_trace[:-1]],
        y=[p[1] for p in a_trace[:-1]],
        mode="markers",
        name="(a)의 예산 검사 지점 (홉 경계뿐)",
        marker=dict(color="#d62728", size=14, symbol="diamond-open", line=dict(width=2.5)),
        hovertemplate="검사: 누적 %{y:,.0f}<extra></extra>",
    )
)

fig.add_hline(
    y=BUDGET,
    line=dict(color="#888888", dash="dash", width=2),
    annotation_text=f"예산 {BUDGET:,}",
    annotation_position="bottom left",
)

# 초과 구간 강조
fig.add_annotation(
    x=a_trace[-1][0],
    y=a_tok,
    text=f"<b>초과 +{a_tok - BUDGET:,.0f}</b>",
    showarrow=True,
    arrowhead=2,
    ax=-40,
    ay=-45,
    font=dict(color="#d62728", size=13),
)
fig.add_annotation(
    x=a_trace[1][0],
    y=a_trace[1][1],
    text="2홉 시작 시 누적 16,800 → 검사 통과<br>이 홉이 46,200을 더 쓴다 (검사 없음)",
    showarrow=True,
    arrowhead=2,
    ax=90,
    ay=55,
    align="left",
    font=dict(size=11),
)
# 검사 없이 흘러가는 구간
fig.add_vrect(
    x0=a_trace[1][0],
    x1=a_trace[2][0],
    fillcolor="#d62728",
    opacity=0.06,
    line_width=0,
    annotation_text="2홉 — 검사 없이 46,200 소비",
    annotation_position="top left",
    annotation_font=dict(size=11, color="#d62728"),
)

fig.update_layout(
    title="예산 검사 입도에 따른 누적 토큰 — 홉 단위 검사는 예산을 넘긴다",
    xaxis_title="넓힌 노드 누적 개수",
    yaxis_title="누적 토큰",
    template="plotly_white",
    width=1020,
    height=600,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    hovermode="closest",
)
fig.update_yaxes(tickformat=",")

_show(fig)

import os

try:
    _here = os.path.dirname(os.path.abspath(__file__))
except NameError:  # 주피터 커널에서는 __file__ 이 없다
    _here = os.getcwd()
_png = os.path.join(_here, "expy.png")
fig.write_image(_png, scale=2)  # kaleido 필요
print(f"저장: {_png}")

# 출력:
# 저장: <hint dir>/expy.png

# %% [markdown]
# ## 정리
#
# | 질문 | 답 |
# |---|---|
# | 왜 63,000을 썼나 | 2홉 시작 시 누적 16,800으로 검사를 통과했고, 그 홉이 46,200을 더 썼다 |
# | 무엇이 초과량을 정하나 | 검사 지점 사이의 최대 단위 작업 비용 $\max_h c_h$ |
# | 초과 상한 | $T \le (B-1) + \max_h c_h$, 즉 초과 $\le \max_h c_h - 1$ |
# | 고치는 법 1 | 노드 단위 검사 — 초과 상한이 1,399로 떨어진다 |
# | 고치는 법 2 | 홉 예상 비용 사전 산정 — 초과 0이지만 남는 예산을 버린다 |
#
# 일반화하면 이렇다. **예산을 «단위 작업 앞»에서만 보면
# 단위 작업 하나가 남은 예산보다 클 때 못 막는다.**
# 그래프 확장뿐 아니라 배치 잡, 재시도 루프, 도구 호출 예산 어디서나 같은 모양으로 난다.
