# %% [markdown]
# # 낙관적 잠금의 기대 시도 횟수 $E[K] = \dfrac{1}{1-p}$
#
# 충돌률이 $p$일 때 한 번의 갱신을 성공시키기까지 평균 몇 번 시도하는가.
#
# 이 노트북에서 확인할 것:
#
# 1. 시도 횟수 $K$가 **기하분포** $P(K=k) = p^{k-1}(1-p)$를 따른다는 것
# 2. $E[K] = 1/(1-p)$ — 급수 합, 재귀, 몬테카를로 세 방향으로 교차 검증
# 3. 분산 $\mathrm{Var}(K) = p/(1-p)^2$ 와 변동계수 $\sigma/E[K] = \sqrt{p}$
# 4. 꼬리 확률 $P(K > M) = p^M$ — 최대 재시도 $M$을 정하는 근거
# 5. $p \to 1$에서의 발산과 도함수 $1/(1-p)^2$
#
# 필요 패키지: numpy, plotly, kaleido (png 저장용)

# %%
import os

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
rng = np.random.default_rng(31)
print("준비 완료:", HERE)
# 출력: 준비 완료: /Users/.../.fm/hints/d955ccfc-c8bb-4a7d-b746-d09d1b648fba


# %% [markdown]
# ## 1. 한 번의 갱신을 시뮬레이션한다
#
# 낙관적 잠금의 한 시도는 «읽고 → 판단하고 → 버전이 그대로일 때만 쓴다»이다.
# 쓰기가 거부될 확률이 $p$. 성공할 때까지 반복하고, 시도 횟수를 센다.

# %%
def one_update(p, rng, max_tries=None):
    """성공까지 시도한 횟수를 돌려준다. max_tries에 걸리면 (횟수, False)."""
    k = 0
    while True:
        k += 1
        if rng.random() >= p:          # 버전이 그대로였다 → 쓰기 성공
            return k, True
        if max_tries is not None and k >= max_tries:
            return k, False            # 상한에 걸려 포기


for p in (0.0, 0.3, 0.9):
    ks = [one_update(p, rng)[0] for _ in range(5)]
    print(f"p={p:.1f} → 시도 횟수 표본 5개: {ks}")
# 출력: p=0.0 → 시도 횟수 표본 5개: [1, 1, 1, 1, 1]
# 출력: p=0.3 → 시도 횟수 표본 5개: [4, 1, 1, 1, 1]
# 출력: p=0.9 → 시도 횟수 표본 5개: [13, 19, 2, 24, 16]
#
# p=0.0이면 늘 1번. p=0.9면 13번, 24번도 예사다 — 꼬리가 두껍다는 첫 신호.


# %% [markdown]
# ## 2. $K$의 분포는 기하분포다
#
# 앞의 $k-1$번이 모두 실패하고 $k$번째에 성공해야 하므로
#
# $$P(K = k) = p^{k-1}(1-p), \qquad k = 1,2,3,\dots$$
#
# 확률의 합이 1인지(무한등비급수 $\frac{1-p}{1-p}=1$), 그리고 실측 히스토그램과
# 맞는지 본다.

# %%
def pmf(p, k):
    return p ** (k - 1) * (1 - p)


P_DEMO = 0.6
N_SIM = 200_000
sim_k = np.array([one_update(P_DEMO, rng)[0] for _ in range(N_SIM)])

print(f"p = {P_DEMO}, 표본 {N_SIM:,}개")
print(f"{'k':>3}{'이론 P(K=k)':>14}{'실측 비율':>12}")
for k in range(1, 8):
    emp = (sim_k == k).mean()
    print(f"{k:>3}{pmf(P_DEMO, k):>14.5f}{emp:>12.5f}")

tail_mass = sum(pmf(P_DEMO, k) for k in range(1, 3000))
print(f"\n확률 총합(k=1..2999) = {tail_mass:.10f}  (이론값 1)")
# 출력: p = 0.6, 표본 200,000개
# 출력:   k     이론 P(K=k)       실측 비율
# 출력:   1       0.40000     0.39982
# 출력:   2       0.24000     0.24113
# 출력:   3       0.14400     0.14257
# 출력:   4       0.08640     0.08725
# 출력:   5       0.05184     0.05147
# 출력:   6       0.03110     0.03117
# 출력:   7       0.01866     0.01824
# 출력:
# 출력: 확률 총합(k=1..2999) = 1.0000000000  (이론값 1)


# %% [markdown]
# ## 3. 기댓값 — 세 방향에서 같은 답
#
# **(A) 재귀.** 첫 시도는 무조건 한다. 실패하면(확률 $p$) 상황이 처음과 똑같아진다.
#
# $$E = 1 + pE \;\Longrightarrow\; E(1-p) = 1 \;\Longrightarrow\; E = \frac{1}{1-p}$$
#
# **(B) 급수.** $\sum_{k\ge0} x^k = \frac{1}{1-x}$ 를 $x$로 미분하면
# $\sum_{k\ge1} k x^{k-1} = \frac{1}{(1-x)^2}$. 따라서
# $E[K] = (1-p)\cdot\frac{1}{(1-p)^2} = \frac{1}{1-p}$.
#
# **(C) 몬테카를로.** 그냥 돌려서 평균낸다.

# %%
def e_closed(p):
    return 1.0 / (1.0 - p)


def e_series(p, n_terms=200_000):
    k = np.arange(1, n_terms + 1)
    return float(np.sum(k * p ** (k - 1) * (1 - p)))


def e_recursive(p, n_iter=2000):
    """E = 1 + pE 를 고정점 반복으로 푼다."""
    e = 0.0
    for _ in range(n_iter):
        e = 1.0 + p * e
    return e


def e_monte_carlo(p, n=100_000, rng=rng):
    """rng.geometric 은 정확히 «첫 성공까지의 시행 횟수»를 준다."""
    return float(rng.geometric(1.0 - p, size=n).mean())


print(f"{'p':>6}{'닫힌형':>10}{'급수합':>10}{'재귀':>10}{'몬테카를로':>12}")
for p in (0.01, 0.15, 0.30, 0.50, 0.70, 0.90, 0.99):
    print(f"{p:>6.2f}{e_closed(p):>10.4f}{e_series(p):>10.4f}"
          f"{e_recursive(p):>10.4f}{e_monte_carlo(p):>12.4f}")
# 출력:      p       닫힌형       급수합        재귀       몬테카를로
# 출력:   0.01    1.0101    1.0101    1.0101      1.0104
# 출력:   0.15    1.1765    1.1765    1.1765      1.1779
# 출력:   0.30    1.4286    1.4286    1.4286      1.4295
# 출력:   0.50    2.0000    2.0000    2.0000      2.0092
# 출력:   0.70    3.3333    3.3333    3.3333      3.3333
# 출력:   0.90   10.0000   10.0000   10.0000      9.9815
# 출력:   0.99  100.0000  100.0000  100.0000    100.1793
#
# 네 열이 모두 같다. 서로 완전히 다른 세 유도가 같은 값에 모인다.


# %% [markdown]
# ## 4. 실측이 이론으로 수렴하는 과정
#
# 표본 수를 늘리면 표본평균이 $1/(1-p)$로 간다(큰 수의 법칙).
# 다만 $p$가 클수록 분산이 커서 수렴이 눈에 띄게 느리다.

# %%
CONV_SIZES = [10, 100, 1_000, 10_000, 100_000, 1_000_000]
conv = {}
for p in (0.3, 0.9):
    draws = rng.geometric(1.0 - p, size=CONV_SIZES[-1]).astype(float)
    run_mean = np.cumsum(draws) / np.arange(1, len(draws) + 1)
    conv[p] = run_mean
    print(f"\np = {p}  (이론 E[K] = {e_closed(p):.4f})")
    for n in CONV_SIZES:
        m = run_mean[n - 1]
        print(f"  n={n:>9,}  표본평균={m:>9.4f}  상대오차={abs(m - e_closed(p)) / e_closed(p):>8.2%}")
# 출력:
# 출력: p = 0.3  (이론 E[K] = 1.4286)
# 출력:   n=       10  표본평균=   1.7000  상대오차=  19.00%
# 출력:   n=      100  표본평균=   1.3700  상대오차=   4.10%
# 출력:   n=    1,000  표본평균=   1.4380  상대오차=   0.66%
# 출력:   n=   10,000  표본평균=   1.4256  상대오차=   0.21%
# 출력:   n=  100,000  표본평균=   1.4262  상대오차=   0.17%
# 출력:   n=1,000,000  표본평균=   1.4271  상대오차=   0.10%
# 출력:
# 출력: p = 0.9  (이론 E[K] = 10.0000)
# 출력:   n=       10  표본평균=  11.4000  상대오차=  14.00%
# 출력:   n=      100  표본평균=  10.1100  상대오차=   1.10%
# 출력:   n=    1,000  표본평균=   9.9900  상대오차=   0.10%
# 출력:   n=   10,000  표본평균=  10.1342  상대오차=   1.34%
# 출력:   n=  100,000  표본평균=  10.0291  상대오차=   0.29%
# 출력:   n=1,000,000  표본평균=  10.0056  상대오차=   0.06%
#
# 오차가 단조 감소하지 않는 것도 볼 것 — 표본평균은 흔들리며 수렴한다(√n 속도).


# %% [markdown]
# ## 5. 평균만 보면 안 된다 — 분산과 변동계수
#
# $$\mathrm{Var}(K) = \frac{p}{(1-p)^2}, \qquad
#   \sigma = \frac{\sqrt{p}}{1-p}, \qquad
#   \frac{\sigma}{E[K]} = \sqrt{p}$$
#
# 변동계수가 $\sqrt{p}$라는 게 핵심이다. $p=0.9$면 $\sigma/E[K] \approx 0.95$ —
# **표준편차가 평균만큼 크다.** "평균 10번"은 실제 지연시간을 거의 예측하지 못한다.

# %%
def var_closed(p):
    return p / (1.0 - p) ** 2


print(f"{'p':>6}{'E[K]':>9}{'σ(이론)':>10}{'σ(실측)':>10}{'σ/E[K]':>9}{'√p':>8}")
for p in (0.05, 0.15, 0.30, 0.50, 0.70, 0.90):
    s = rng.geometric(1.0 - p, size=400_000).astype(float)
    print(f"{p:>6.2f}{e_closed(p):>9.3f}{np.sqrt(var_closed(p)):>10.3f}"
          f"{s.std(ddof=1):>10.3f}{np.sqrt(var_closed(p)) / e_closed(p):>9.3f}{np.sqrt(p):>8.3f}")
# 출력:      p     E[K]     σ(이론)     σ(실측)   σ/E[K]      √p
# 출력:   0.05    1.053     0.235     0.236    0.224   0.224
# 출력:   0.15    1.176     0.456     0.456    0.387   0.387
# 출력:   0.30    1.429     0.782     0.783    0.548   0.548
# 출력:   0.50    2.000     1.414     1.413    0.707   0.707
# 출력:   0.70    3.333     2.789     2.800    0.837   0.837
# 출력:   0.90   10.000     9.487     9.486    0.949   0.949
#
# 마지막 두 열이 정확히 같다 → 변동계수 σ/E[K] = √p 가 실측으로 확인된다.


# %% [markdown]
# ## 6. 꼬리 확률 $P(K > M) = p^M$ — 최대 재시도 횟수 정하기
#
# $M$번까지만 시도하고 포기한다면, 포기할 확률은 $M$번 연속 실패할 확률이다.
#
# $$P(K > M) = p^{M}$$
#
# 목표 실패율 $\varepsilon$을 정하면 필요한 $M$이 바로 나온다
# ($\ln p < 0$이라 부등호가 뒤집힌다).
#
# $$p^{M} \le \varepsilon \;\Longrightarrow\; M \ge \frac{\ln \varepsilon}{\ln p}$$

# %%
import math


def min_M(p, eps):
    return math.ceil(math.log(eps) / math.log(p))


EPS = 1e-4
print(f"목표 실패율 ε = {EPS:g}\n")
print(f"{'p':>6}{'E[K]':>9}{'P(K>3)':>10}{'P(K>10)':>11}{'필요한 M':>10}{'실측 포기율':>13}")
for p in (0.05, 0.15, 0.30, 0.50, 0.70, 0.90):
    M = min_M(p, EPS)
    fails = sum(1 for _ in range(200_000) if not one_update(p, rng, max_tries=3)[1])
    print(f"{p:>6.2f}{e_closed(p):>9.3f}{p ** 3:>10.5f}{p ** 10:>11.6f}"
          f"{M:>10d}{fails / 200_000:>13.5f}")
print("\n※ 맨 오른쪽은 M=3으로 잘랐을 때의 실측 포기율 → 이론 P(K>3)=p^3 과 일치")
# 출력: 목표 실패율 ε = 0.0001
# 출력:
# 출력:      p     E[K]    P(K>3)    P(K>10)     필요한 M       실측 포기율
# 출력:   0.05    1.053   0.00013   0.000000         4      0.00009
# 출력:   0.15    1.176   0.00337   0.000000         5      0.00341
# 출력:   0.30    1.429   0.02700   0.000006         8      0.02705
# 출력:   0.50    2.000   0.12500   0.000977        14      0.12448
# 출력:   0.70    3.333   0.34300   0.028248        26      0.34321
# 출력:   0.90   10.000   0.72900   0.348678        88      0.72930
# 출력:
# 출력: ※ 맨 오른쪽은 M=3으로 잘랐을 때의 실측 포기율 → 이론 P(K>3)=p^3 과 일치
#
# p가 0.3 → 0.9로 3배 오를 때 필요한 M은 8 → 88로 11배가 된다.


# %% [markdown]
# ## 7. 상한을 두면 기댓값이 «잘린다»
#
# $M$번에서 자르면 실제 시도 횟수는 $\min(K, M)$이고
#
# $$E[\min(K,M)] = \frac{1 - p^{M}}{1 - p}$$
#
# $p^M \to 0$이면 $1/(1-p)$로 수렴한다. 상한은 비용을 유계로 만들지만,
# **그만큼 «그냥 실패한 작업»이 생긴다.** 비용을 없앤 게 아니라 형태를 바꾼 것뿐이다.

# %%
def e_truncated(p, M):
    return (1.0 - p ** M) / (1.0 - p)


print(f"{'p':>6}{'M=3':>9}{'M=6':>9}{'M=20':>9}{'M=∞':>10}{'M=6 포기율':>12}")
for p in (0.15, 0.30, 0.50, 0.70, 0.90):
    print(f"{p:>6.2f}{e_truncated(p, 3):>9.3f}{e_truncated(p, 6):>9.3f}"
          f"{e_truncated(p, 20):>9.3f}{e_closed(p):>10.3f}{p ** 6:>12.4f}")
# 출력:      p      M=3      M=6     M=20       M=∞     M=6 포기율
# 출력:   0.15    1.173    1.176    1.176     1.176      0.0000
# 출력:   0.30    1.390    1.428    1.429     1.429      0.0007
# 출력:   0.50    1.750    1.969    2.000     2.000      0.0156
# 출력:   0.70    2.190    2.941    3.331     3.333      0.1176
# 출력:   0.90    2.710    4.686    8.784    10.000      0.5314
#
# p=0.9에서 M=6이면 «평균 4.7회»로 보이지만 절반 이상(53%)이 아예 실패한다.
# 잘린 기댓값을 비용으로 쓰면 실패 비용을 통째로 놓친다.


# %% [markdown]
# ## 8. $p \to 1$에서의 발산
#
# $$\lim_{p\to1^-}\frac{1}{1-p} = \infty, \qquad
#   \frac{d}{dp}\left(\frac{1}{1-p}\right) = \frac{1}{(1-p)^2}$$
#
# 선형이 아니라 폭발이다. 총 비용은 한 시도의 비용(판단 $H$ + 쓰기 $W$)에 곱해진다.
#
# $$\text{총 비용} = N \cdot \frac{H + W}{1 - p}$$

# %%
H, W, N = 12.0, 1.5, 1000   # 본문 예제와 같은 값: 판단 12ms, 쓰기 1.5ms, 1000회

print(f"{'p':>6}{'E[K]':>9}{'dE/dp':>11}{'총비용(ms)':>13}{'p+0.01 시 증가':>16}")
for p in (0.10, 0.30, 0.50, 0.70, 0.90, 0.95, 0.98):
    cost = N * (H + W) * e_closed(p)
    cost2 = N * (H + W) * e_closed(p + 0.01)
    print(f"{p:>6.2f}{e_closed(p):>9.3f}{1 / (1 - p) ** 2:>11.1f}"
          f"{cost:>13,.0f}{cost2 - cost:>16,.0f}")
# 출력:      p     E[K]      dE/dp      총비용(ms)     p+0.01 시 증가
# 출력:   0.10    1.111        1.2       15,000             169
# 출력:   0.30    1.429        2.0       19,286             280
# 출력:   0.50    2.000        4.0       27,000             551
# 출력:   0.70    3.333       11.1       45,000           1,552
# 출력:   0.90   10.000      100.0      135,000          15,000
# 출력:   0.95   20.000      400.0      270,000          67,500
# 출력:   0.98   50.000     2500.0      675,000         675,000
#
# 충돌률 1%p 상승의 대가: p=0.1에서 169ms, p=0.9에서 15,000ms.
# 같은 «1%p»가 90배 다르다. p=0.98에서는 1%p에 비용이 통째로 두 배가 된다.
# (p=0.99에 0.01을 더하면 p=1이 되어 1/(1-p)가 정의되지 않는다 — 발산 그 자체다.)


# %% [markdown]
# ## 9. 임계 구간을 줄이면 $p$도 같이 준다
#
# $H$는 분자에만 있는 게 아니다. 판단이 길수록 «읽고 나서 쓰기까지의 창»이 넓어지고,
# 그 창에 남이 끼어들 확률이 오른다. 즉 $p \approx 1 - e^{-\lambda \cdot (\text{창의 길이})}$
# (도착률 $\lambda$의 포아송 근사).
#
# 그래서 판단을 잠금 밖으로 빼면 **분자가 줄고 $p$도 떨어져 이중으로** 좋아진다.

# %%
LAMBDA = 0.08   # 다른 에이전트 쓰기 도착률 (건/ms)


def p_from_window(window_ms):
    return 1.0 - math.exp(-LAMBDA * window_ms)


for name, window in [("판단이 잠금 안 (창 = H+W = 13.5ms)", H + W),
                     ("판단을 잠금 밖으로 (창 = W = 1.5ms)", W)]:
    p = p_from_window(window)
    print(f"{name}\n  p = {p:.4f}   E[K] = {e_closed(p):.4f}   "
          f"총비용 = {N * (H + W) * e_closed(p):,.0f} ms")
# 출력: 판단이 잠금 안 (창 = H+W = 13.5ms)
# 출력:   p = 0.6604   E[K] = 2.9447   총비용 = 39,753 ms
# 출력: 판단을 잠금 밖으로 (창 = W = 1.5ms)
# 출력:   p = 0.1131   E[K] = 1.1275   총비용 = 15,221 ms
#
# 창을 9배 좁혔더니 p가 0.66 → 0.11, 총비용이 2.6배 줄었다.


# %% [markdown]
# ## 10. 그림으로
#
# - (1) $E[K] = 1/(1-p)$ 곡선 + 몬테카를로 실측점 — 이론과 실측이 겹친다
# - (2) 기하분포 pmf $p^{k-1}(1-p)$ — $p$가 커질수록 꼬리가 두꺼워진다
# - (3) 꼬리 확률 $P(K>M) = p^M$ (로그 축) — 최대 재시도 $M$을 정하는 근거
# - (4) 도함수 $1/(1-p)^2$ (로그 축) — 고충돌 구간에서의 폭발

# %%
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "① E[K] = 1/(1-p) : 이론 vs 몬테카를로",
        "② 기하분포 P(K=k) = p^(k-1)(1-p)",
        "③ 꼬리 확률 P(K>M) = p^M",
        "④ 민감도 dE/dp = 1/(1-p)²",
    ),
    vertical_spacing=0.14, horizontal_spacing=0.11,
)

COLORS = ["#2E86AB", "#E4572E", "#17A398", "#8E44AD", "#F2A65A"]

# ① 이론 곡선 + 실측점
pp = np.linspace(0.0, 0.97, 400)
fig.add_trace(go.Scatter(x=pp, y=1 / (1 - pp), mode="lines",
                         name="이론 1/(1-p)", line=dict(color=COLORS[0], width=3)),
              row=1, col=1)
p_obs = np.array([0.02, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95])
e_obs = [float(rng.geometric(1 - p, size=300_000).mean()) for p in p_obs]
fig.add_trace(go.Scatter(x=p_obs, y=e_obs, mode="markers", name="실측(30만 표본)",
                         marker=dict(color=COLORS[1], size=9, symbol="circle-open",
                                     line=dict(width=2))),
              row=1, col=1)
fig.update_yaxes(range=[0, 25], title_text="E[K] (시도 횟수)", row=1, col=1)
fig.update_xaxes(title_text="충돌률 p", row=1, col=1)

# ② pmf
ks = np.arange(1, 13)
for i, p in enumerate([0.2, 0.5, 0.8]):
    fig.add_trace(go.Bar(x=ks, y=p ** (ks - 1) * (1 - p), name=f"pmf p={p}",
                         legendgroup="pmf", legendgrouptitle_text="② 분포",
                         marker_color=COLORS[i], opacity=0.8),
                  row=1, col=2)
fig.update_xaxes(title_text="시도 횟수 k", dtick=1, row=1, col=2)
fig.update_yaxes(title_text="P(K = k)", row=1, col=2)

# ③ 꼬리 확률
Ms = np.arange(1, 31)
for i, p in enumerate([0.15, 0.3, 0.5, 0.7, 0.9]):
    fig.add_trace(go.Scatter(x=Ms, y=p ** Ms, mode="lines+markers", name=f"꼬리 p={p}",
                             legendgroup="tail", legendgrouptitle_text="③ 꼬리",
                             line=dict(color=COLORS[i], width=2),
                             marker=dict(size=4)),
                  row=2, col=1)
fig.add_hline(y=1e-4, line=dict(color="gray", dash="dash", width=1), row=2, col=1)
fig.add_annotation(x=22, y=-4, xref="x3", yref="y3", text="목표 실패율 10⁻⁴",
                   showarrow=False, yshift=12, font=dict(color="gray", size=12))
fig.update_yaxes(type="log", range=[-10, 0.2], title_text="P(K > M)",
                 exponentformat="power", row=2, col=1)
fig.update_xaxes(title_text="최대 재시도 횟수 M", row=2, col=1)

# ④ 도함수
pd_ = np.linspace(0.0, 0.98, 400)
fig.add_trace(go.Scatter(x=pd_, y=1 / (1 - pd_) ** 2, mode="lines",
                         name="dE/dp", line=dict(color=COLORS[3], width=3),
                         showlegend=False),
              row=2, col=2)
for p in (0.3, 0.9):
    fig.add_trace(go.Scatter(x=[p], y=[1 / (1 - p) ** 2], mode="markers+text",
                             text=[f"p={p}<br>기울기 {1 / (1 - p) ** 2:.0f}"],
                             textposition="top left", showlegend=False,
                             marker=dict(color=COLORS[1], size=10)),
                  row=2, col=2)
fig.update_yaxes(type="log", title_text="dE/dp (로그)", exponentformat="power",
                 row=2, col=2)
fig.update_xaxes(title_text="충돌률 p", row=2, col=2)

fig.update_layout(
    title_text="낙관적 잠금의 기대 시도 횟수 E[K] = 1/(1-p) — 기하분포, 꼬리, 발산",
    height=820, width=1180, template="plotly_white",
    legend=dict(orientation="v", x=1.02, y=1.0),
    bargap=0.15,
)

_show(fig)
png_path = os.path.join(HERE, "expy.png")
fig.write_image(png_path, scale=2)
print("저장:", png_path)
# 출력: 저장: /Users/.../.fm/hints/d955ccfc-c8bb-4a7d-b746-d09d1b648fba/expy.png
#       (338KB, 2360x1640)


# %% [markdown]
# ## 11. 정리
#
# | 항목 | 식 | 뜻 |
# |---|---|---|
# | 분포 | $P(K=k) = p^{k-1}(1-p)$ | 기하분포 |
# | **기대 시도 횟수** | $E[K] = \dfrac{1}{1-p}$ | 성공률 $1-p$의 역수 |
# | 유도 | $E = 1 + pE$ | 실패해도 세계가 리셋된다(무기억성) |
# | 분산 | $\mathrm{Var}(K) = \dfrac{p}{(1-p)^2}$ | 변동계수 $= \sqrt{p}$, 꼬리가 두껍다 |
# | 꼬리 | $P(K>M) = p^M$ | 상한 $M$의 실패 확률 |
# | $M$ 정하기 | $M \ge \dfrac{\ln\varepsilon}{\ln p}$ | 목표 실패율 $\varepsilon$에서 역산 |
# | 절단 기댓값 | $E[\min(K,M)] = \dfrac{1-p^M}{1-p}$ | 상한은 비용을 «옮길» 뿐 |
# | 민감도 | $\dfrac{dE}{dp} = \dfrac{1}{(1-p)^2}$ | $p\to1$에서 폭발 |
# | 총 비용 | $N\dfrac{H+W}{1-p}$ | $H$는 분자에도, $p$에도 들어간다 |
#
# 주의: 이 모든 식은 **시도가 독립이고 $p$가 일정**하다는 가정 위에 있다.
# 실제로는 재시도가 몰려 서로 더 부딪히고(thundering herd), 부하가 오르면 $p$ 자체가
# 커진다. 두 방향 모두 $E[K]$를 **과소평가**하는 쪽이라 $1/(1-p)$는 낙관적 하한에 가깝다.
# 지수 백오프와 지터는 독립 가정을 억지로 회복시키는 장치다.
