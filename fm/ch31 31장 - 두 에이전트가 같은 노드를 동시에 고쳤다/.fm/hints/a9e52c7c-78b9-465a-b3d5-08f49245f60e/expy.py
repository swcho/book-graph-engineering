# 필요 패키지: plotly, kaleido, numpy  (pip install plotly kaleido numpy)
# 표준 라이브러리만으로도 대부분의 셀은 돌아간다. 그래프 셀만 plotly/kaleido가 필요하다.

# %% [markdown]
# # 낙관적 잠금과 비관적 잠금의 갈림길은 어디인가?
#
# **답**: 충돌률 15~30% 근처. 그리고 판단을 잠금 밖으로 빼면 갈림길이 오른쪽으로 밀린다.
#
# 이 노트북은 그 갈림길이 사실 분수 하나로 정해진다는 것을 보인다.
#
# $$p^{*} = \frac{L}{X}$$
#
# - $L$ : 잠금을 잡고 푸는 값 (충돌이 없어도 매번 낸다)
# - $X$ : 임계 구간의 길이 = 충돌 났을 때 다시 해야 하는 일의 길이

# %%
import math
import random

# 31장 예제 3(ex3_lock_contention.py)의 값
HOLD_MS = 12.0          # 판단하는 시간 (읽고 나서 쓰기까지)
WRITE_MS = 1.5          # 쓰기
LOCK_ACQUIRE_MS = 2.2   # 잠금 획득 + 해제
N_OPS = 1000            # 총 연산 횟수

X_IN = HOLD_MS + WRITE_MS   # 판단이 잠금 «안»에 있을 때의 임계 구간
X_OUT = WRITE_MS            # 판단을 잠금 «밖»으로 뺐을 때의 임계 구간

print(f"X(판단 잠금 안)  = {X_IN} ms")
print(f"X(판단 잠금 밖)  = {X_OUT} ms")
print(f"L(잠금 획득)     = {LOCK_ACQUIRE_MS} ms")
# 출력:
# X(판단 잠금 안)  = 13.5 ms
# X(판단 잠금 밖)  = 1.5 ms
# L(잠금 획득)     = 2.2 ms


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1. 기하분포 — 기대 시도 횟수는 $1/(1-p)$
#
# 낙관적 잠금은 「쓰기 직전에 버전이 그대로인가」를 본다. 아니면 처음부터 다시 한다.
# 매 시도가 확률 $p$ 로 실패하면 성공까지의 시도 횟수 $K$ 는 기하분포를 따른다.
#
# $$P(K=k) = p^{k-1}(1-p)$$
#
# 재귀로 풀면 $E[K] = 1 + pE[K]$ 이므로
#
# $$E[K] = \frac{1}{1-p}$$
#
# 등비급수 미분으로도 같은 답이 나온다.
# $\sum_{k\ge1} k x^{k-1} = \frac{1}{(1-x)^2}$ 이므로 $E[K] = (1-p)\cdot\frac{1}{(1-p)^2}$.

# %%
def expected_tries(p):
    """기대 시도 횟수 = 1/(1-p)"""
    return 1.0 / (1.0 - p) if p < 1 else float("inf")


def mc_tries(p, trials=200_000, seed=31):
    """몬테카를로로 평균 시도 횟수를 잰다."""
    rng = random.Random(seed)
    total = 0
    for _ in range(trials):
        k = 1
        while rng.random() < p:
            k += 1
        total += k
    return total / trials


print(f"{'p':>6}{'이론 1/(1-p)':>16}{'몬테카를로':>14}{'오차':>10}")
print("-" * 46)
for p in (0.01, 0.05, 0.15, 0.30, 0.50, 0.70):
    t, m = expected_tries(p), mc_tries(p)
    print(f"{p:>6.2f}{t:>16.4f}{m:>14.4f}{abs(t - m) / t:>9.2%}")
# 출력:
#      p    이론 1/(1-p)        몬테카를로      오차
# ----------------------------------------------
#   0.01          1.0101        1.0103     0.02%
#   0.05          1.0526        1.0531     0.04%
#   0.15          1.1765        1.1772     0.06%
#   0.30          1.4286        1.4286     0.00%
#   0.50          2.0000        1.9967     0.17%
#   0.70          3.3333        3.3273     0.18%

# %% [markdown]
# ## 2. 대기열 — 비관적 잠금 쪽의 $\rho/(1-\rho)$
#
# 비관적 잠금은 먼저 잠그고 시작한다. 잠금이 붙들려 있는 비율을 $\rho$ 라 하면
# 정상 상태에서 앞에 $n$ 명이 있을 확률이 $(1-\rho)\rho^n$ (M/M/1)이고,
#
# $$E[n] = \frac{\rho}{1-\rho}, \qquad W_q = \frac{\rho}{1-\rho}\,X$$
#
# 낙관적의 $1/(1-p)$ 와 **같은 등비급수**가 한 번 더 나온다. 이래서 계산이 예쁘게 끝난다.

# %%
def mm1_wait(rho, service_ms):
    """M/M/1 평균 대기 시간 (서비스 시간 제외)"""
    return (rho / (1.0 - rho)) * service_ms if rho < 1 else float("inf")


def mm1_sim(rho, service_ms, n=200_000, seed=31):
    """단일 서버 FIFO 큐를 직접 돌려서 평균 대기 시간을 잰다."""
    rng = random.Random(seed)
    lam = rho / service_ms          # 도착률
    t_arrive = 0.0
    t_free = 0.0                    # 서버가 비는 시각
    wait_sum = 0.0
    warmup = n // 10
    counted = 0
    for i in range(n):
        t_arrive += rng.expovariate(lam)
        start = max(t_arrive, t_free)
        if i >= warmup:
            wait_sum += start - t_arrive
            counted += 1
        t_free = start + rng.expovariate(1.0 / service_ms)
    return wait_sum / counted


print(f"{'rho':>6}{'이론 Wq(ms)':>16}{'시뮬레이션':>14}")
print("-" * 36)
for rho in (0.10, 0.30, 0.50, 0.70):
    print(f"{rho:>6.2f}{mm1_wait(rho, X_IN):>16.3f}{mm1_sim(rho, X_IN):>14.3f}")
# 출력:
#    rho     이론 Wq(ms)        시뮬레이션
# ------------------------------------
#   0.10           1.500         1.490
#   0.30           5.786         5.762
#   0.50          13.500        13.376
#   0.70          31.500        31.018
#
# 큐 시뮬레이션은 수렴이 느려서 rho가 클수록 오차가 눈에 띈다.
# 그래도 rho/(1-rho) 꼴로 폭발한다는 성질은 그대로 보인다.

# %% [markdown]
# ## 3. 두 비용 곡선
#
# 판단 시간 $H$ 를 잠금 밖에 두든 안에 두든 **양쪽 다 한 번은 낸다**. 그 부분을
# $H_{\text{out}}$ 이라 두고 공통으로 빼 두면 두 식은 이렇게 된다.
#
# $$C_{\text{opt}}(p) = N\Big(H_{\text{out}} + \frac{X}{1-p}\Big)$$
# $$C_{\text{pess}}(p) = N\Big(H_{\text{out}} + X + L + \frac{p^{2}}{1-p}X\Big)$$
#
# $X$ 가 임계 구간(= 재시도 단위)의 길이다.
# 판단이 잠금 안이면 $H_{\text{out}}=0,\ X=13.5$, 밖이면 $H_{\text{out}}=12,\ X=1.5$.

# %%
def c_opt(p, x, h_out=0.0, n=N_OPS, max_tries=None):
    e = expected_tries(p)
    if max_tries is not None:
        e = min(e, max_tries)
    return n * (h_out + e * x)


def c_pess(p, x, h_out=0.0, n=N_OPS, lock=LOCK_ACQUIRE_MS):
    queue = mm1_wait(p, x)
    return n * (h_out + x + lock + p * queue)


print("판단이 잠금 «안»에 있을 때 (X = 13.5ms) — 책 예제 3의 표를 그대로 재현\n")
print(f"{'충돌률':>8}{'낙관적(ms)':>14}{'기대 시도':>11}{'비관적(ms)':>14}{'승자':>10}")
print("-" * 57)
for p in (0.01, 0.05, 0.15, 0.30, 0.50, 0.70):
    o = c_opt(p, X_IN, max_tries=6)
    q = c_pess(p, X_IN)
    e = min(expected_tries(p), 6)
    print(f"{p:>7.0%}{o:>14,.0f}{e:>11.2f}{q:>14,.0f}"
          f"{'낙관적' if o < q else '비관적':>10}")
# 출력:
# 판단이 잠금 «안»에 있을 때 (X = 13.5ms) — 책 예제 3의 표를 그대로 재현
#
#      충돌률      낙관적(ms)      기대 시도      비관적(ms)        승자
# ---------------------------------------------------------
#      1%        13,636       1.01        15,701       낙관적
#      5%        14,211       1.05        15,736       낙관적
#     15%        15,882       1.18        16,057       낙관적
#     30%        19,286       1.43        17,436       비관적
#     50%        27,000       2.00        22,450       비관적
#     70%        45,000       3.33        37,750       비관적

# %% [markdown]
# ## 4. 두 식을 빼면 분모가 사라진다
#
# $$
# \frac{C_{\text{opt}} - C_{\text{pess}}}{N}
# = \frac{X}{1-p} - X - L - \frac{p^2}{1-p}X
# = X\frac{1-p^2}{1-p} - X - L
# = X(1+p) - X - L
# = Xp - L
# $$
#
# $1-p^2=(1-p)(1+p)$ 로 약분되어 **$p$ 의 일차식**만 남는다. 그래서
#
# $$p^{*} = \frac{L}{X}$$
#
# $H_{\text{out}}$ 은 양쪽에 똑같이 들어가므로 뺄셈에서 사라진다. 갈림길은 오직 $L/X$ 다.

# %%
def crossover_numeric(x, h_out=0.0, lo=1e-9, hi=0.999999):
    """이분법으로 C_opt = C_pess 인 p를 찾는다. 구간 안에 없으면 None."""
    f = lambda p: c_opt(p, x, h_out) - c_pess(p, x, h_out)
    if f(lo) * f(hi) > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


for label, x, h_out in (("판단이 잠금 안", X_IN, 0.0),
                        ("판단을 잠금 밖으로", X_OUT, HOLD_MS)):
    num = crossover_numeric(x, h_out)
    formula = LOCK_ACQUIRE_MS / x
    num_s = f"{num:.6f}" if num is not None else "(0,1) 안에 없음"
    print(f"[{label}]  X = {x} ms")
    print(f"    수치 이분법 p* = {num_s}")
    print(f"    공식  L/X   = {formula:.6f}  ({formula:.1%})")
# 출력:
# [판단이 잠금 안]  X = 13.5 ms
#     수치 이분법 p* = 0.162963
#     공식  L/X   = 0.162963  (16.3%)
# [판단을 잠금 밖으로]  X = 1.5 ms
#     수치 이분법 p* = (0,1) 안에 없음
#     공식  L/X   = 1.466667  (146.7%)
#
# 16.3% -> 146.7%. 확률은 1을 넘을 수 없으니, 판단을 잠금 밖으로 빼면
# «어떤 충돌률에서도» 낙관적이 이긴다. 갈림길이 그래프 밖으로 밀려난 것이다.

# %% [markdown]
# ## 5. 왜 하필 「15~30%」라고 말하는가
#
# $p^{*}=L/X$ 는 절대 시간이 아니라 **비율**이다.
# 「잠금 잡고 푸는 값이 임계 구간의 1/7 ~ 1/3」이면 갈림길이 15~30%에 놓인다.
# 실무 환경의 $L/X$ 가 흔히 그 범위라서 경험칙으로 굳었다.

# %%
print(f"{'X(ms)':>8}{'p* = L/X':>12}    (L = 2.2ms 고정)")
print("-" * 34)
for x in (7.3, 9.0, 11.0, 13.5, 14.7, 22.0, 2001.5):
    tag = ""
    if x == X_IN:
        tag = "  <- 책의 기본 값"
    if x == 2001.5:
        tag = "  <- 잠금 안에서 모델을 부르면(2초)"
    print(f"{x:>8.1f}{LOCK_ACQUIRE_MS / x:>11.2%}{tag}")
# 출력:
#    X(ms)    p* = L/X    (L = 2.2ms 고정)
# ----------------------------------
#      7.3     30.14%
#      9.0     24.44%
#     11.0     20.00%
#     13.5     16.30%  <- 책의 기본 값
#     14.7     14.97%
#     22.0     10.00%
#   2001.5      0.11%  <- 잠금 안에서 모델을 부르면(2초)

# %% [markdown]
# ## 6. 덤 — 충돌률 자체도 창 길이에 비례한다
#
# $p$ 는 고정 상수가 아니다. 다른 작업이 초당 $\lambda$ 번 같은 노드를 건드린다면
# 창 길이 $X$ 안에 끼어들 확률은
#
# $$p(X) = 1 - e^{-\lambda X} \approx \lambda X \quad (\lambda X \ll 1)$$
#
# $X$ 를 줄이면 **가로축의 $p$ 도 왼쪽으로** 움직인다. 갈림길은 오른쪽으로 밀리고
# 현재 위치는 왼쪽으로 간다. 양쪽에서 벌어진다.

# %%
for lam_per_s in (5, 20, 50):
    lam = lam_per_s / 1000.0     # ms 당 도착률
    p_in = 1 - math.exp(-lam * X_IN)
    p_out = 1 - math.exp(-lam * X_OUT)
    print(f"초당 {lam_per_s:>3}회 경쟁 →  p(X=13.5) = {p_in:6.2%}, "
          f"p(X=1.5) = {p_out:6.2%}   ({p_in / p_out:.1f}배 감소)")
# 출력:
# 초당   5회 경쟁 →  p(X=13.5) =  6.53%, p(X=1.5) =  0.75%   (8.7배 감소)
# 초당  20회 경쟁 →  p(X=13.5) = 23.66%, p(X=1.5) =  2.96%   (8.0배 감소)
# 초당  50회 경쟁 →  p(X=13.5) = 49.08%, p(X=1.5) =  7.23%   (6.8배 감소)

# %% [markdown]
# ## 7. 그래프 — 갈림길이 오른쪽으로 밀리는 것을 눈으로
#
# 왼쪽: 판단이 잠금 안 ($X=13.5$). 두 곡선이 16.3%에서 만난다.
# 오른쪽: 판단을 잠금 밖으로 ($X=1.5$). 낙관적 곡선이 끝까지 아래에 있다.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ps = [i / 400 for i in range(1, 241)]      # 0.0025 ~ 0.60

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=("판단이 잠금 «안» (X = 13.5ms)",
                    "판단을 잠금 «밖»으로 (X = 1.5ms)"),
    horizontal_spacing=0.09,
)

for col, (x, h_out) in enumerate(((X_IN, 0.0), (X_OUT, HOLD_MS)), start=1):
    opt = [c_opt(p, x, h_out) for p in ps]
    pes = [c_pess(p, x, h_out) for p in ps]
    fig.add_trace(go.Scatter(x=ps, y=opt, name="낙관적 잠금",
                             line=dict(color="#2E86DE", width=3),
                             legendgroup="opt", showlegend=(col == 1)),
                  row=1, col=col)
    fig.add_trace(go.Scatter(x=ps, y=pes, name="비관적 잠금",
                             line=dict(color="#EE5A24", width=3),
                             legendgroup="pes", showlegend=(col == 1)),
                  row=1, col=col)

    star = crossover_numeric(x, h_out)
    if star is not None:
        fig.add_trace(go.Scatter(
            x=[star], y=[c_opt(star, x, h_out)], mode="markers+text",
            marker=dict(color="#111", size=12, symbol="x"),
            text=[f" p* = {star:.1%}"], textposition="top right",
            showlegend=False), row=1, col=col)
        fig.add_vline(x=star, line=dict(color="#888", dash="dot"),
                      row=1, col=col)
    else:
        fig.add_annotation(
            x=0.5, y=0.9, xref=f"x{col} domain", yref=f"y{col} domain",
            text=f"p* = L/X = {LOCK_ACQUIRE_MS / x:.0%} → 화면 밖<br>"
                 f"전 구간에서 낙관적이 이긴다",
            showarrow=False, font=dict(size=13, color="#2E86DE"),
            bgcolor="rgba(255,255,255,0.75)", row=1, col=col)

    # 15~30% 경험칙 띠
    fig.add_vrect(x0=0.15, x1=0.30, fillcolor="#f1c40f", opacity=0.16,
                  line_width=0, row=1, col=col)

fig.update_yaxes(title_text="총 비용 (ms, 1000회)", row=1, col=1)
fig.update_xaxes(title_text="충돌률 p", tickformat=".0%", range=[0, 0.6])
fig.update_layout(
    title="갈림길 p* = L / X  —  노란 띠가 «15~30%» 경험칙 구간",
    width=1100, height=520, template="plotly_white",
    legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
)

_show(fig)

import os
_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_png, scale=2)
print("저장:", _png)
# 출력:
# 저장: .../a9e52c7c-78b9-465a-b3d5-08f49245f60e/expy.png

# %% [markdown]
# ## 8. 몬테카를로 대조 — 공식이 정말 맞나
#
# 낙관적 쪽만 실제로 굴려 본다. 기하분포로 시도 횟수를 뽑아 총 시간을 재고,
# 공식 $N\cdot X/(1-p)$ 와 맞춰 본다.

# %%
def mc_optimistic_total(p, x, h_out=0.0, n=N_OPS, seed=31, reps=200):
    rng = random.Random(seed)
    acc = 0.0
    for _ in range(reps):
        t = 0.0
        for _ in range(n):
            k = 1
            while rng.random() < p:
                k += 1
            t += h_out + k * x
        acc += t
    return acc / reps


print(f"{'p':>6}{'공식(ms)':>14}{'몬테카를로':>14}{'오차':>9}   (X = 13.5)")
print("-" * 50)
for p in (0.05, 0.163, 0.30, 0.50):
    f = c_opt(p, X_IN)
    m = mc_optimistic_total(p, X_IN)
    print(f"{p:>6.3f}{f:>14,.0f}{m:>14,.0f}{abs(f - m) / f:>8.2%}")
# 출력:
#      p       공식(ms)        몬테카를로      오차
# --------------------------------------------------
#  0.050        14,211        14,216    0.04%
#  0.163        16,129        16,142    0.08%
#  0.300        19,286        19,286    0.00%
#  0.500        27,000        26,955    0.16%

# %% [markdown]
# ## 9. 정리
#
# $$p^{*} = \frac{L}{X} = \frac{\text{잠금 획득 비용}}{\text{임계 구간(= 재시도 단위) 길이}}$$
#
# | | $X$ | $p^{*}$ |
# |---|---|---|
# | 판단이 잠금 안 (책 기본값) | 13.5 ms | **16.3%** → 「15~30% 근처」 |
# | 판단을 잠금 밖으로 | 1.5 ms | **146.7%** → 갈림길이 화면 밖 |
# | 잠금 안에서 모델 호출 (2초) | 2001.5 ms | **0.11%** → 사실상 항상 비관적 |
#
# - 낙관적의 $1/(1-p)$ 는 기하분포 기댓값, 비관적의 $\rho/(1-\rho)$ 는 대기열 기댓값.
#   같은 등비급수라서 빼면 $1-p^2$ 가 약분되고 $Xp-L$ 만 남는다.
# - 그래서 갈림길은 **비율** $L/X$ 하나로 정해진다. 절대 시간이 아니다.
# - 판단(모델 호출)을 잠금 밖으로 빼면 $X$ 가 줄어 갈림길이 **오른쪽으로** 밀리고,
#   동시에 $p \approx \lambda X$ 도 줄어 현재 위치가 **왼쪽으로** 간다.
# - 15~30%는 $L/X$ 가 실무에서 흔히 놓이는 구간일 뿐이다. 직접 재서 넣어야 한다.
