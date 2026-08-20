# %% [markdown]
# # ex4의 루프는 왜 '정체'로 끝났고 무엇을 아꼈는가
#
# 20장 `ex4_generator_critic.py`는 생성-검증 루프에 **네 가지 종료 조건**을 다 붙인다.
#
# | 상수 | 값 | 의미 |
# |---|---|---|
# | `MAX_ROUNDS` | 6 | 횟수 상한 |
# | `MAX_COST` | 90.0 | 예산 상한 |
# | `STALL_LIMIT` | 2 | 몇 번 연속 안 나아지면 정체로 볼까 |
# | 회차당 비용 | 22.0 | `generate`가 매 회차 더하는 값 |
#
# `generate`는 `rounds < 2`일 때만 섹션을 하나씩 채운다. 즉 **3회차부터는 산출물이
# 더 나아지지 않는다.** 이것이 실무에서 흔한 「모델이 더 못 고치는」 상황의 축약이다.
#
# 위반 건수를 $v_t$, 정체 창을 $w = \text{STALL\_LIMIT}+1 = 3$이라 하면 정체 판정은
#
# $$ \text{stalled}(t) = \big[\,|v_{1:t}| \ge w \,\big] \wedge \Big[\, v_t \ge \min(v_{t-w+1},\dots,v_{t-1}) \,\Big] $$
#
# **같음도 정체로 본다.** 나빠지는 것만 잡으면 이미 늦기 때문이다.

# %%
import plotly.graph_objects as go


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


REQUIRED = ["## 개요", "## 원인", "## 조치", "## 재발 방지"]
MAX_ROUNDS, MAX_COST, STALL_LIMIT = 6, 90.0, 2
COST_PER_ROUND = 22.0

print(f"필수 섹션 {len(REQUIRED)}개, 상한 = 횟수 {MAX_ROUNDS} / 예산 {MAX_COST:.0f} / 정체 {STALL_LIMIT}")
# 출력: 필수 섹션 4개, 상한 = 횟수 6 / 예산 90 / 정체 2

# %% [markdown]
# ## 1. ex4의 생성-검증을 그대로 축약 재현
#
# LangGraph 노드 세 개(`generate`, `critic`, `route`)를 순수 함수로 옮겼다.
# 그래프 배선만 뺐을 뿐 판정 로직은 원문과 동일하다.

# %%
def generate(text: str, rounds: int) -> str:
    """원문 generate. rounds < 2 일 때만 섹션을 하나 더 채운다."""
    have = [x for x in REQUIRED if x in text]
    if rounds < 2:
        have = REQUIRED[: len(have) + 1]
    return "\n\n".join(f"{x}\n내용" for x in have)


def critic(text: str) -> list:
    """원문 critic. 빠진 섹션 목록 = 위반."""
    return [x for x in REQUIRED if x not in text]


def stalled(scores: list) -> bool:
    """원문 stalled. 최근 STALL_LIMIT+1 개가 나아지지 않았나. 같음도 정체."""
    n = STALL_LIMIT + 1
    if len(scores) < n:
        return False
    w = scores[-n:]
    return w[-1] >= min(w[:-1])


# 회차를 하나씩 손으로 돌려 본다 (가드는 아직 안 건다)
text, rounds, cost, scores, trace = "", 0, 0.0, [], []
for _ in range(MAX_ROUNDS):
    text = generate(text, rounds)
    rounds, cost = rounds + 1, cost + COST_PER_ROUND
    miss = critic(text)
    scores.append(len(miss))
    trace.append((rounds, len([x for x in REQUIRED if x in text]), cost, len(miss), stalled(scores)))

print(f"{'회차':>4} {'섹션':>4} {'누적비용':>8} {'위반':>4} {'정체판정':>8}")
for r, sec, c, v, st in trace:
    print(f"{r:>4} {sec:>4} {c:>8.0f} {v:>4} {'예' if st else '아니오':>8}")
# 출력:   회차   섹션     누적비용   위반     정체판정
# 출력:    1    1       22    3      아니오
# 출력:    2    2       44    2      아니오
# 출력:    3    2       66    2        예
# 출력:    4    2       88    2        예
# 출력:    5    2      110    2        예
# 출력:    6    2      132    2        예

# %% [markdown]
# 위반이 **3 → 2 → 2**로 가고 3회차에서 처음 정체가 잡힌다.
# 창 $[3, 2, 2]$에서 $\min(3,2)=2$이고 마지막 값도 $2 \ge 2$이므로 「나아지지 않음」이다.
#
# ## 2. 가드 조합별로 언제 끝나는가
#
# 원문 `route`의 우선순위는 `성공 → 상한 → 예산 → 정체`다. 이 순서를 그대로 두고
# **어떤 가드를 켜느냐**만 바꿔 세 조합을 비교한다.

# %%
def run(use_rounds: bool, use_cost: bool, use_stall: bool):
    text, rounds, cost, scores = "", 0, 0.0, []
    while True:
        text = generate(text, rounds)
        rounds, cost = rounds + 1, cost + COST_PER_ROUND
        miss = critic(text)
        scores.append(len(miss))
        if not miss:
            return "성공", rounds, cost, scores
        if use_rounds and rounds >= MAX_ROUNDS:
            return "상한", rounds, cost, scores
        if use_cost and cost >= MAX_COST:
            return "예산", rounds, cost, scores
        if use_stall and stalled(scores):
            return "정체", rounds, cost, scores
        if rounds >= 20:                      # 안전망 (가드가 하나도 없을 때)
            return "안전망", rounds, cost, scores


COMBOS = [
    ("네 조건 전부 (원문 ex4)", True, True, True),
    ("횟수 상한만",             True, False, False),
    ("예산 상한만",             False, True, False),
]

results = []
for name, ur, uc, us in COMBOS:
    why, r, c, sc = run(ur, uc, us)
    results.append((name, why, r, c, sc[-1]))

print(f"{'가드 조합':<22} {'끝난 이유':<8} {'회차':>4} {'누적비용':>8} {'최종위반':>8}")
print("-" * 56)
for name, why, r, c, v in results:
    print(f"{name:<22} {why:<8} {r:>4} {c:>8.0f} {v:>8}")
# 출력: 가드 조합                  끝난 이유       회차     누적비용     최종위반
# 출력: --------------------------------------------------------
# 출력: 네 조건 전부 (원문 ex4)     정체          3       66        2
# 출력: 횟수 상한만                상한          6      132        2
# 출력: 예산 상한만                예산          5      110        2

# %% [markdown]
# **세 조합 모두 최종 위반은 2로 똑같다.** 더 돌려도 결과가 나아지지 않았다는 뜻이다.
# 달라지는 건 오직 「얼마를 쓰고 멈췄나」다.
#
# $$ \Delta_{\text{절약}} = 132 - 66 = 66 \quad (\text{6회차} - \text{3회차} = \text{세 회차}) $$
#
# 절약률은 $66/132 = 50\%$. 예산 상한만 둔 경우와 비교해도 $110 - 66 = 44$를 아꼈다.

# %%
saved_rounds = results[1][2] - results[0][2]
saved_cost = results[1][3] - results[0][3]
print(f"횟수 상한만 대비: {saved_rounds}회차 / {saved_cost:.0f} 절약 ({saved_cost / results[1][3]:.0%})")
print(f"예산 상한만 대비: {results[2][2] - results[0][2]}회차 / {results[2][3] - results[0][3]:.0f} 절약")
# 출력: 횟수 상한만 대비: 3회차 / 66 절약 (50%)
# 출력: 예산 상한만 대비: 2회차 / 44 절약

# %% [markdown]
# ## 3. 누적 비용 곡선과 종료 지점
#
# 누적 비용은 $c(t) = 22t$인 직선이다. 가드가 하는 일은 이 직선을 **어디서 자르느냐**뿐이다.

# %%
xs = [t for t in range(1, MAX_ROUNDS + 1)]
ys = [COST_PER_ROUND * t for t in xs]
viol = [3, 2, 2, 2, 2, 2]

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=xs, y=ys, mode="lines+markers", name="누적 비용 (22/회차)",
    line=dict(color="#94a3b8", width=3, dash="dot"),
    marker=dict(size=8, color="#94a3b8"),
    hovertemplate="%{x}회차 · 누적 %{y:.0f}<extra></extra>",
))
fig.add_hline(y=MAX_COST, line=dict(color="#f59e0b", width=1.5, dash="dash"),
              annotation_text="MAX_COST = 90", annotation_position="top left")

COLORS = {"정체": "#2563eb", "상한": "#dc2626", "예산": "#f59e0b"}
for name, why, r, c, v in results:
    fig.add_trace(go.Scatter(
        x=[r], y=[c], mode="markers+text", name=f"{name} → {why} ({c:.0f})",
        marker=dict(size=18, symbol="x-thin", line=dict(width=4, color=COLORS[why]), color=COLORS[why]),
        text=[f" {why} {c:.0f}"], textposition="middle right",
        textfont=dict(size=12, color=COLORS[why]),
        hovertemplate=f"{name}<br>{r}회차 · {c:.0f} · 위반 {v}<extra></extra>",
    ))

fig.add_annotation(x=3, y=66, ax=3, ay=132, xref="x", yref="y", axref="x", ayref="y",
                   showarrow=True, arrowhead=3, arrowwidth=2, arrowcolor="#2563eb",
                   text="세 회차 · 66 절약", font=dict(size=12, color="#2563eb"))

fig.update_layout(
    title="ex4 — 가드 조합별 종료 지점 (위반 3→2→2, 최종 위반은 셋 다 2)",
    xaxis=dict(title="회차", dtick=1, range=[0.5, 7.2],
               ticktext=[f"{t}<br>위반 {v}" for t, v in zip(xs, viol)], tickvals=xs),
    yaxis=dict(title="누적 비용", range=[0, 150]),
    template="plotly_white", width=900, height=560,
    margin=dict(b=150, l=70, r=40, t=70),
    legend=dict(orientation="h", yanchor="top", y=-0.24, x=0),
)
_show(fig)
fig.write_image("expy.png", scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# - **왜 정체로 끝났나** — 위반이 3→2→2로 가며 3회차에 마지막 값이 창의 최솟값보다
#   줄지 않았다. `route`의 우선순위상 상한(3<6)과 예산(66<90)에 안 걸린 채 정체가 잡혔다.
# - **무엇을 아꼈나** — 횟수 상한만 있었다면 6회차까지 돌아 **132**를 썼다.
#   실제로는 3회차 **66**에서 끝났으니 **세 회차, 비용 66**을 아꼈다.
# - **왜 이유를 남기나** — 「상한」은 더 돌리면 될 수도 있다는 뜻이고 「정체」는 더 돌려도
#   안 된다는 뜻이다. 대응이 다르므로 불리언 하나로는 이 구분이 안 된다.
