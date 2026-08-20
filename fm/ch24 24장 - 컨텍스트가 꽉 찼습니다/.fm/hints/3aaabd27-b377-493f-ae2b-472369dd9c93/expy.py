# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# %% [markdown]
# # 대화 길이는 선형, 누적 비용은 제곱
#
# 24장 24.1절 / `ex1_growth.py`의 핵심을 단계적으로 재현한다.
#
# **질문** 대화 길이와 누적 비용은 각각 어떻게 자라는가?
#
# **답** 대화 길이는 **선형**으로, 누적 비용은 **제곱**으로 자란다.
# 이유는 하나다 — 스테이트리스 API라서 **매 턴 대화 전체를 다시 보내기** 때문이다.
#
# 턴 $t$에서 대화 길이를 $H(t)$, 그 턴에 새로 붙는 양을 $a$라 하면
#
# $$H(t) \approx a\,t \quad (\text{선형})$$
#
# 매 턴 $H(t)$를 통째로 다시 보내므로 누적 입력 토큰은
#
# $$S(t) = \sum_{k=1}^{t} H(k) \approx \frac{a}{2}\,t^2 \quad (\text{제곱})$$
#
# 따라서 **턴이 2배가 되면 비용은 4배**가 된다.

# %%
# 24장 ex1_growth.py와 동일한 파라미터
TURN_IN = 220  # 한 턴에 사용자가 넣는 토큰
TURN_OUT = 380  # 한 턴에 모델이 내놓는 토큰
TOOL_OUT = 1_400  # 도구 결과가 붙는 턴의 추가 토큰
TOOL_EVERY = 3  # 세 턴에 한 번 도구를 부른다

PRICE_IN = 3.0 / 1_000_000  # 달러, 입력 100만 토큰당
PRICE_OUT = 15.0 / 1_000_000  # 달러, 출력 100만 토큰당
KRW = 1_380

WINDOW = 200_000  # 모델이 받아 주는 최대 입력 토큰

# 한 턴에 «평균» 붙는 양 a
a = TURN_IN + TURN_OUT + TOOL_OUT / TOOL_EVERY
print(f"턴당 평균 증가량 a = {a:,.1f} 토큰")
# 출력: 턴당 평균 증가량 a = 1,066.7 토큰


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1단계 — 시뮬레이션
#
# 매 턴 하는 일은 딱 세 가지다.
#
# 1. 사용자 입력을 대화에 붙인다 (그리고 3턴마다 도구 결과도 붙는다)
# 2. **지금까지 쌓인 대화 전체**를 입력으로 보낸다  ← 여기가 제곱의 원인
# 3. 모델 출력을 대화에 붙인다

# %%
def simulate(turns):
    history = 0  # 지금까지 쌓인 대화 길이 (= 한 번 보낼 때의 입력 크기)
    sent_in = 0  # 누적으로 «보낸» 입력 토큰
    sent_out = 0
    rows = []
    for t in range(1, turns + 1):
        history += TURN_IN
        if t % TOOL_EVERY == 0:
            history += TOOL_OUT
        sent_in += history  # 매 턴 전체 대화를 «다시» 보낸다
        sent_out += TURN_OUT
        history += TURN_OUT
        cost_krw = (sent_in * PRICE_IN + sent_out * PRICE_OUT) * KRW
        rows.append(
            {
                "turn": t,
                "history": history,  # 대화 길이 (선형)
                "sent_in": sent_in,  # 누적 입력 (제곱)
                "krw": cost_krw,  # 누적 비용 (제곱)
                "window_use": history / WINDOW,
            }
        )
    return rows


rows = simulate(120)
marks = [1, 5, 10, 20, 40, 80, 120]

print(f"{'턴':>5}{'대화 길이':>12}{'누적 입력':>14}{'누적 비용':>12}{'창 사용률':>10}")
print("-" * 56)
for r in rows:
    if r["turn"] in marks:
        print(
            f"{r['turn']:>5}{r['history']:>12,}{r['sent_in']:>14,}"
            f"{r['krw']:>11,.0f}원{r['window_use']:>9.0%}"
        )
# 출력:
#     턴       대화 길이         누적 입력       누적 비용     창 사용률
# --------------------------------------------------------
#     1         600           220          9원       0%
#     5       4,400        11,300         86원       2%
#    10      10,200        50,200        286원       5%
#    20      20,400       206,600      1,013원      10%
#    40      42,200       840,800      3,796원      21%
#    80      84,400     3,387,800     14,655원      42%
#   120     128,000     7,642,400     32,583원      64%

# %% [markdown]
# 표를 세로로 읽으면 두 열의 **성격이 다르다**는 게 보인다.
#
# | 턴 | 대화 길이 | 배수 | 누적 입력 | 배수 |
# |---|---|---|---|---|
# | 20 | 20,400 | — | 206,600 | — |
# | 40 | 42,200 | ×2.07 | 840,800 | ×4.07 |
# | 80 | 84,400 | ×2.00 | 3,387,800 | ×4.03 |
#
# 턴이 2배가 될 때 대화 길이는 **2배**(선형), 누적 입력은 **4배**(제곱)다.

# %%
# 배수를 직접 확인한다
by_turn = {r["turn"]: r for r in rows}
for lo, hi in [(10, 20), (20, 40), (40, 80), (60, 120)]:
    h = by_turn[hi]["history"] / by_turn[lo]["history"]
    s = by_turn[hi]["sent_in"] / by_turn[lo]["sent_in"]
    c = by_turn[hi]["krw"] / by_turn[lo]["krw"]
    print(f"{lo:>3}턴 → {hi:>3}턴 : 대화 길이 x{h:.2f}   누적 입력 x{s:.2f}   비용 x{c:.2f}")
# 출력:
#  10턴 →  20턴 : 대화 길이 x2.00   누적 입력 x4.12   비용 x3.53
#  20턴 →  40턴 : 대화 길이 x2.07   누적 입력 x4.07   비용 x3.75
#  40턴 →  80턴 : 대화 길이 x2.00   누적 입력 x4.03   비용 x3.86
#  60턴 → 120턴 : 대화 길이 x2.00   누적 입력 x4.02   비용 x3.91

# %% [markdown]
# 비용 배수가 4보다 약간 작은 건 출력 토큰($\propto t$, 선형) 이 섞여 있어서다.
# 턴이 길어질수록 입력이 지배하므로 비용 배수도 4에 수렴한다.

# %% [markdown]
# ## 2단계 — 닫힌 식과 맞춰 보기
#
# $$H(t) \approx a\,t, \qquad S(t) \approx \frac{a}{2}t^2 + \frac{a}{2}t = \frac{a}{2}t(t+1)$$

# %%
print(f"{'턴':>5}{'실제 대화 길이':>14}{'a*t':>10}{'실제 누적입력':>14}{'a/2*t(t+1)':>14}")
print("-" * 58)
for t in marks:
    r = by_turn[t]
    print(f"{t:>5}{r['history']:>14,}{a * t:>10,.0f}{r['sent_in']:>14,}{a / 2 * t * (t + 1):>14,.0f}")
# 출력:
#     턴      실제 대화 길이       a*t       실제 누적입력    a/2*t(t+1)
# ----------------------------------------------------------
#     1           600     1,067           220         1,067
#     5         4,400     5,333        11,300        16,000
#    10        10,200    10,667        50,200        58,667
#    20        20,400    21,333       206,600       224,000
#    40        42,200    42,667       840,800       874,667
#    80        84,400    85,333     3,387,800     3,456,000
#   120       128,000   128,000     7,642,400     7,744,000

# %% [markdown]
# 대화 길이는 $a\,t$와 거의 정확히 맞는다.
# 누적 입력은 초반에만 이론값보다 낮고(1턴 220 vs 1,067),
# 턴이 늘수록 이론값에 수렴한다(120턴에서 7,642,400 vs 7,744,000, 99%).
# 초반이 낮은 이유는 도구 결과가 3턴마다 «뒤늦게» 붙고,
# 그 턴의 모델 출력은 «다음» 턴부터 재전송되기 때문이다. 차수는 처음부터 $t^2$다.
#
# 차수를 직접 재 보자. $\log S$ 를 $\log t$ 에 대해 회귀하면 기울기가 지수다.

# %%
import math

lo, hi = 20, 120
slope_hist = (math.log(by_turn[hi]["history"]) - math.log(by_turn[lo]["history"])) / (
    math.log(hi) - math.log(lo)
)
slope_sent = (math.log(by_turn[hi]["sent_in"]) - math.log(by_turn[lo]["sent_in"])) / (
    math.log(hi) - math.log(lo)
)
print(f"대화 길이의 차수  ≈ {slope_hist:.3f}   (1 이면 선형)")
print(f"누적 입력의 차수  ≈ {slope_sent:.3f}   (2 이면 제곱)")
# 출력: 대화 길이의 차수  ≈ 1.025   (1 이면 선형)
# 출력: 누적 입력의 차수  ≈ 2.015   (2 이면 제곱)

# %% [markdown]
# ## 3단계 — «창이 아직 남았으니 괜찮다»가 틀린 이유
#
# 120턴에서도 창 사용률은 64%다. 아직 안 찼다.
# 그런데 누적 비용은 이미 20턴의 **32배**다. 돈이 창보다 먼저 터진다.

# %%
r20, r120 = by_turn[20], by_turn[120]
print(f"20턴  : 창 {r20['window_use']:.0%},  누적 비용 {r20['krw']:,.0f}원")
print(f"120턴 : 창 {r120['window_use']:.0%},  누적 비용 {r120['krw']:,.0f}원")
print(f"→ 창은 {r120['window_use'] / r20['window_use']:.1f}배인데 비용은 {r120['krw'] / r20['krw']:.1f}배")
# 출력: 20턴  : 창 10%,  누적 비용 1,013원
# 출력: 120턴 : 창 64%,  누적 비용 32,583원
# 출력: → 창은 6.3배인데 비용은 32.2배

# %%
# 24장 도입부의 «6.4배 청구서»를 재현한다.
# 20턴을 가정하고 예산을 잡았는데 실제 사용자는 평균 47턴을 썼다.
assumed, actual = 20, 47
print(f"가정 {assumed}턴 : {by_turn[assumed]['krw']:,.0f}원/대화")
print(f"실제 {actual}턴 : {by_turn[actual]['krw']:,.0f}원/대화")
print(f"→ 청구서 배수 {by_turn[actual]['krw'] / by_turn[assumed]['krw']:.1f}배")
print(f"   (턴 배수는 {actual / assumed:.2f}배일 뿐인데)")
# 출력: 가정 20턴 : 1,013원/대화
# 출력: 실제 47턴 : 5,184원/대화
# 출력: → 청구서 배수 5.1배
# 출력:    (턴 배수는 2.35배일 뿐인데)

# %% [markdown]
# 턴 수는 2.35배 늘었을 뿐인데 청구서는 5.1배다. $2.35^2 \approx 5.5$ 니 제곱이 맞다.
# 책의 6.4배는 도구 사용량 등 파라미터 차이지만, **메커니즘은 이 제곱 그대로**다.

# %% [markdown]
# ## 4단계 — 그래프로 확인
#
# 왼쪽은 선형(직선), 오른쪽은 제곱(위로 휘는 곡선).
# 아래 로그–로그 그래프에서는 기울기가 각각 1과 2인 직선으로 보인다.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

turns = [r["turn"] for r in rows]
hist = [r["history"] for r in rows]
sent = [r["sent_in"] for r in rows]
krw = [r["krw"] for r in rows]

fig = make_subplots(
    rows=2,
    cols=2,
    subplot_titles=(
        "대화 길이 — 선형 (기울기 1)",
        "누적 입력 토큰 — 제곱 (기울기 2)",
        "누적 비용(원) — 제곱",
        "로그-로그: 기울기가 곧 차수",
    ),
)

fig.add_trace(go.Scatter(x=turns, y=hist, name="대화 길이", line=dict(color="#2563eb")), row=1, col=1)
fig.add_trace(
    go.Scatter(x=turns, y=[a * t for t in turns], name="a·t (이론)", line=dict(color="#93c5fd", dash="dash")),
    row=1,
    col=1,
)
fig.add_trace(go.Scatter(x=turns, y=sent, name="누적 입력", line=dict(color="#dc2626")), row=1, col=2)
fig.add_trace(
    go.Scatter(
        x=turns,
        y=[a / 2 * t * (t + 1) for t in turns],
        name="a/2·t(t+1) (이론)",
        line=dict(color="#fca5a5", dash="dash"),
    ),
    row=1,
    col=2,
)
fig.add_trace(go.Scatter(x=turns, y=krw, name="누적 비용", line=dict(color="#b45309")), row=2, col=1)
fig.add_trace(go.Scatter(x=turns, y=hist, name="대화 길이(log)", line=dict(color="#2563eb")), row=2, col=2)
fig.add_trace(go.Scatter(x=turns, y=sent, name="누적 입력(log)", line=dict(color="#dc2626")), row=2, col=2)

fig.update_xaxes(title_text="턴", row=1, col=1)
fig.update_xaxes(title_text="턴", row=1, col=2)
fig.update_xaxes(title_text="턴", row=2, col=1)
fig.update_xaxes(title_text="턴 (log)", type="log", row=2, col=2)
fig.update_yaxes(title_text="토큰", row=1, col=1)
fig.update_yaxes(title_text="토큰", row=1, col=2)
fig.update_yaxes(title_text="원", row=2, col=1)
fig.update_yaxes(title_text="토큰 (log)", type="log", row=2, col=2)

fig.update_layout(
    title="대화 길이는 선형, 누적 비용은 제곱 — 매 턴 전체를 다시 보내기 때문",
    height=760,
    width=1100,
    template="plotly_white",
)

_show(fig)
fig.write_image("expy.png", scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# | 항목 | 자라는 모양 | 턴 2배일 때 |
# |---|---|---|
# | 대화 길이 $H(t)$ | 선형 $O(t)$ | 2배 |
# | 매 턴 보내는 입력 | 선형 $O(t)$ | 2배 |
# | **누적 입력 / 누적 비용** $S(t)$ | **제곱 $O(t^2)$** | **4배** |
#
# - 제곱의 원인은 모델 API가 스테이트리스라서 **매 턴 대화 전체를 재전송**하기 때문이다.
# - 그래서 «창이 아직 안 찼으니 괜찮다»는 잘못된 안심이다. **비용은 창이 차기 훨씬 전에 문제가 된다.**
# - 20턴 기준으로 잡은 예산이 47턴 실사용에서 무너지는 이유가 이 제곱이다.
# - 완화 수단: 요약/압축(24.2~24.3), 오프로딩(24.4), 계층 기억(24.5),
#   그리고 접두사 재전송분을 싸게 만드는 **프롬프트 캐싱**.
