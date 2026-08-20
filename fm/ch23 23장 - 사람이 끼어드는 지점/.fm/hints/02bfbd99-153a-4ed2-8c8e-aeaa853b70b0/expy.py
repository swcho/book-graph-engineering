# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# 표준 라이브러리만으로도 통계 계산 부분은 동작한다. 시각화 셀만 plotly가 필요하다.

# %% [markdown]
# # `lognormvariate(10.4, 1.15)` 뜯어보기
#
# `ex3_gate_policy.py`는 하루치 환불 요청 금액을 **로그정규분포**로 만든다.
#
# ```python
# def day(seed=7, n=1200):
#     rng = random.Random(seed)
#     return [int(rng.lognormvariate(10.4, 1.15)) for _ in range(n)]
# ```
#
# $X = e^{Z}$, $Z \sim \mathcal{N}(\mu, \sigma^2)$, $\mu = 10.4$, $\sigma = 1.15$.
#
# 이 노트북은 네 단계로 확인한다.
#
# 1. 표본 생성 (시드 고정)
# 2. 히스토그램 — 선형 x축 vs 로그 x축
# 3. 이론값(중앙값 $e^{\mu}$, 평균 $e^{\mu+\sigma^2/2}$)과 표본 통계 비교
# 4. 문턱별 초과 비율(생존함수) — "10만 원 문턱이면 몇 %가 사람에게 가는가"

# %%
import math
import random
import statistics
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


MU = 10.4
SIGMA = 1.15
HERE = Path(__file__).parent if "__file__" in globals() else Path.cwd()
print(f"mu={MU}, sigma={SIGMA}")
# 출력: mu=10.4, sigma=1.15

# %% [markdown]
# ## 1. 표본 생성 — 원본 코드 그대로
#
# `random.Random(7)`로 시드를 고정하므로 누가 몇 번을 돌려도 같은 표가 나온다.
# 정책 문서에 실릴 숫자는 재현 가능해야 한다.

# %%
def day(seed=7, n=1200):
    """하루치 환불 요청. 금액은 소액이 많고 고액이 드물다."""
    rng = random.Random(seed)
    return [int(rng.lognormvariate(MU, SIGMA)) for _ in range(n)]


amounts = day()
print(f"건수      : {len(amounts):,}")
print(f"합계      : {sum(amounts):,}원")
print(f"최소 / 최대: {min(amounts):,}원 / {max(amounts):,}원")
print(f"앞 10건    : {[f'{a:,}' for a in amounts[:10]]}")
# 출력: 건수      : 1,200
# 출력: 합계      : 73,893,625원
# 출력: 최소 / 최대: 802원 / 1,863,427원
# 출력: 앞 10건    : ['21,822', '45,298', '36,739', '5,595', '6,560',
#                     '13,904', '12,638', '42,282', '88,922', '14,830']

# %% [markdown]
# 최소 802원, 최대 186만 원. **2,300배** 차이다.
# 정규분포에서는 절대 나올 수 없는 폭이고, 바로 이 폭 때문에
# "문턱을 어디에 둘 것인가"가 의미 있는 질문이 된다.

# %% [markdown]
# ## 2. 히스토그램 — 선형 x축 vs 로그 x축
#
# 같은 데이터를 두 가지 축으로 본다.
#
# - **선형 축**: 왼쪽에 벽처럼 몰리고 오른쪽으로 꼬리가 길게 늘어진다 (우편향).
# - **로그 축**: $\log X \sim \mathcal{N}(\mu, \sigma^2)$이므로 **종 모양**으로 펴진다.
#
# 로그 축에서 종 모양이 나오면 "이 데이터는 로그정규분포다"의 눈으로 하는 검사가 된다.

# %%
log_amounts = [math.log(a) for a in amounts]

fig_hist = make_subplots(
    rows=1,
    cols=2,
    subplot_titles=("선형 x축 — 오른쪽 꼬리", "로그 x축 — 종 모양"),
)
fig_hist.add_trace(
    go.Histogram(x=amounts, nbinsx=80, name="금액", marker_color="#4C78A8"),
    row=1,
    col=1,
)
fig_hist.add_trace(
    go.Histogram(x=log_amounts, nbinsx=50, name="ln(금액)", marker_color="#F58518"),
    row=1,
    col=2,
)
fig_hist.add_vline(
    x=MU, line_dash="dash", line_color="#333",
    annotation_text=f"mu={MU}", row=1, col=2,
)
fig_hist.update_xaxes(title_text="금액(원)", row=1, col=1)
fig_hist.update_xaxes(title_text="ln(금액)", row=1, col=2)
fig_hist.update_layout(
    title_text="lognormvariate(10.4, 1.15) 표본 1,200건",
    showlegend=False,
    height=420,
    template="plotly_white",
)
_show(fig_hist)
print("선형축 히스토그램: 왼쪽 벽 + 긴 오른쪽 꼬리 / 로그축: 대칭 종 모양")
# 출력: 선형축 히스토그램: 왼쪽 벽 + 긴 오른쪽 꼬리 / 로그축: 대칭 종 모양

# %% [markdown]
# ## 3. 이론값 vs 표본 통계
#
# | 통계량 | 공식 |
# |---|---|
# | 최빈값 | $e^{\mu - \sigma^2}$ |
# | 중앙값 | $e^{\mu}$ |
# | 평균 | $e^{\mu + \sigma^2/2}$ |
# | 표준편차 | $e^{\mu+\sigma^2/2}\sqrt{e^{\sigma^2}-1}$ |
#
# 평균이 **$e^{\mu}$가 아니라** $e^{\mu+\sigma^2/2}$라는 점이 핵심이다.
# 지수함수가 볼록해서 $E[e^Z] > e^{E[Z]}$ (옌센 부등식)가 되기 때문이다.

# %%
mode_t = math.exp(MU - SIGMA**2)
median_t = math.exp(MU)
mean_t = math.exp(MU + SIGMA**2 / 2)
sd_t = mean_t * math.sqrt(math.exp(SIGMA**2) - 1)

mean_s = statistics.mean(amounts)
median_s = statistics.median(amounts)
sd_s = statistics.stdev(amounts)

print(f"{'통계량':<10}{'이론값':>14}{'표본값':>14}")
print("-" * 38)
print(f"{'최빈값':<10}{mode_t:>14,.0f}{'-':>14}")
print(f"{'중앙값':<10}{median_t:>14,.0f}{median_s:>14,.0f}")
print(f"{'평균':<10}{mean_t:>14,.0f}{mean_s:>14,.0f}")
print(f"{'표준편차':<10}{sd_t:>14,.0f}{sd_s:>14,.0f}")
print(f"\n평균 / 중앙값 = {mean_t / median_t:.2f}배  ← 우편향의 지문")
# 출력: 통계량                  이론값           표본값
# 출력: --------------------------------------
# 출력: 최빈값                8,756             -
# 출력: 중앙값               32,860        31,966
# 출력: 평균                 63,656        61,578
# 출력: 표준편차            105,615       103,311
# 출력:
# 출력: 평균 / 중앙값 = 1.94배  ← 우편향의 지문

# %% [markdown]
# **최빈값 8.8천 < 중앙값 3.3만 < 평균 6.4만.**
#
# "평균 환불 금액 6.4만 원"이라는 요약만 보고 문턱을 6만 원에 두면
# 절반쯤 걸릴 것 같지만, 실제로는 **약 30%**만 걸린다.
# 평균은 소수의 고액 건이 끌어올린 값이다.

# %% [markdown]
# ### 분위수
#
# $p$ 분위수는 정규분포표만 있으면 손으로도 나온다.
#
# $$x_p = e^{\mu + \sigma z_p}, \qquad z_p = \Phi^{-1}(p)$$

# %%
ND = statistics.NormalDist()
print(f"{'분위수':>8}{'z_p':>9}{'이론값(원)':>14}{'표본값(원)':>14}")
print("-" * 45)
srt = sorted(amounts)
for p in (0.01, 0.10, 0.25, 0.50, 0.75, 0.90, 0.99):
    z = ND.inv_cdf(p)
    theory = math.exp(MU + SIGMA * z)
    sample = srt[min(int(p * len(srt)), len(srt) - 1)]
    print(f"{p:>8.0%}{z:>9.3f}{theory:>14,.0f}{sample:>14,.0f}")
# 출력:      분위수      z_p        이론값(원)        표본값(원)
# 출력: ---------------------------------------------
# 출력:       1%   -2.326         2,264         2,314
# 출력:      10%   -1.282         7,527         7,758
# 출력:      25%   -0.674        15,129        15,010
# 출력:      50%    0.000        32,860        31,981
# 출력:      75%    0.674        71,372        67,576
# 출력:      90%    1.282       143,456       138,920
# 출력:      99%    2.326       477,013       523,825

# %% [markdown]
# ## 4. 문턱별 초과 비율 — 생존함수
#
# 승인 관문의 실전 질문은 하나다.
#
# > 문턱을 $t$에 두면 하루 1,200건 중 몇 건이 사람에게 가는가?
#
# $$P(X \ge t) = 1 - \Phi\!\left(\frac{\ln t - \mu}{\sigma}\right)$$
#
# 그리고 `ex3_gate_policy.py`의 용량 설정은:
# 검토 3분 × 담당자 2명 × 480분 ⇒ **하루 320건 / 960분**.
# 규칙은 "검토 부하가 용량의 70%를 넘지 않는 문턱 중 가장 낮은 것".

# %%
REVIEW_MINUTES = 3
REVIEWERS = 2
WORK_MINUTES = 8 * 60
ERROR_RATE = 0.04
CAPACITY = REVIEWERS * WORK_MINUTES  # 960분


def survival(t):
    if t <= 0:
        return 1.0
    return 1.0 - ND.cdf((math.log(t) - MU) / SIGMA)


THRESHOLDS = [0, 50_000, 100_000, 300_000, 1_000_000, 10**9]
rows = []
print(f"{'문턱':>12}{'이론 초과율':>12}{'사람이 볼 건수':>14}"
      f"{'검토 시간':>11}{'용량 대비':>10}{'자동 위험액':>14}")
print("-" * 75)
for t in THRESHOLDS:
    reviewed = [a for a in amounts if a >= t]
    auto = [a for a in amounts if a < t]
    load = len(reviewed) * REVIEW_MINUTES
    risk = sum(auto) * ERROR_RATE
    ratio = load / CAPACITY
    label = "전부 사람" if t == 0 else ("전부 자동" if t == 10**9 else f"{t:,}원")
    rows.append((label, t, len(reviewed), ratio, risk))
    print(f"{label:>12}{survival(t):>12.2%}{len(reviewed):>14}"
          f"{load:>10}분{ratio:>10.0%}{risk:>13,.0f}원")
# 출력:           문턱      이론 초과율      사람이 볼 건수      검토 시간     용량 대비        자동 위험액
# 출력: ---------------------------------------------------------------------------
# 출력:        전부 사람     100.00%          1200      3600분      375%            0원
# 출력:      50,000원      35.75%           412      1236분      129%      672,804원
# 출력:     100,000원      16.66%           183       549분       57%    1,306,610원
# 출력:     300,000원       2.72%            32        96분       10%    2,291,931원
# 출력:   1,000,000원       0.15%             1         3분        0%    2,881,208원
# 출력:        전부 자동       0.00%             0         0분        0%    2,955,745원

# %% [markdown]
# 이론 초과율과 표본 건수가 잘 맞는다 (10만 원: 이론 16.66% → 200건 기대, 표본 183건).
#
# **결론**: 70% 기준을 만족하는 가장 낮은 문턱은 **10만 원**(용량의 57%)이다.
# 5만 원은 129%로 초과 — 밀린 건이 쌓이고, 담당자가 대충 보기 시작하고,
# 결국 "전부 자동"과 같아진다. 사람을 갈아 넣고 효과는 0인 상태.

# %%
# 문턱을 연속적으로 훑으며 "용량 대비 부하"와 "자동 처리 위험액"의 트레이드오프를 그린다.
grid = [math.exp(x / 100) for x in range(int(100 * math.log(1000)),
                                          int(100 * math.log(3_000_000)), 3)]
load_pct, risk_won, n_reviewed = [], [], []
srt_amounts = sorted(amounts)
total = sum(amounts)
for t in grid:
    # sorted 배열에서 t 미만 건수/합계를 누적으로 구한다
    n_auto = sum(1 for a in srt_amounts if a < t)
    s_auto = sum(a for a in srt_amounts if a < t)
    n_rev = len(amounts) - n_auto
    n_reviewed.append(n_rev)
    load_pct.append(n_rev * REVIEW_MINUTES / CAPACITY * 100)
    risk_won.append(s_auto * ERROR_RATE)

fig_tr = make_subplots(specs=[[{"secondary_y": True}]])
fig_tr.add_trace(
    go.Scatter(x=grid, y=load_pct, name="검토 부하 (용량 대비 %)",
               line=dict(color="#4C78A8", width=3)),
    secondary_y=False,
)
fig_tr.add_trace(
    go.Scatter(x=grid, y=risk_won, name="자동 처리 위험액 (원)",
               line=dict(color="#E45756", width=3)),
    secondary_y=True,
)
fig_tr.add_hline(y=70, line_dash="dash", line_color="#4C78A8",
                 annotation_text="용량 70% 상한", secondary_y=False)
fig_tr.add_vline(x=100_000, line_dash="dot", line_color="#333",
                 annotation_text="10만 원 문턱")
fig_tr.update_xaxes(type="log", title_text="문턱 (원, 로그 축)")
fig_tr.update_yaxes(title_text="검토 부하 (용량 대비 %)", secondary_y=False)
fig_tr.update_yaxes(title_text="자동 처리 위험액 (원)", secondary_y=True)
fig_tr.update_layout(
    title_text="문턱 트레이드오프 — 부하는 내려가고 위험액은 올라간다",
    height=420,
    template="plotly_white",
    legend=dict(orientation="h", y=1.12, x=0),
)
_show(fig_tr)

# %% [markdown]
# ## 정적 이미지 저장
#
# 위 두 그림을 세로로 합쳐 `expy.png`로 저장한다.

# %%
fig = make_subplots(
    rows=2,
    cols=2,
    specs=[
        [{"type": "xy"}, {"type": "xy"}],
        [{"type": "xy", "colspan": 2, "secondary_y": True}, None],
    ],
    subplot_titles=(
        "선형 x축 — 오른쪽으로 긴 꼬리",
        "로그 x축 — 정규분포 종 모양",
        "문턱 트레이드오프 (검토 부하 vs 자동 처리 위험액)",
    ),
    vertical_spacing=0.16,
)
fig.add_trace(go.Histogram(x=amounts, nbinsx=80, marker_color="#4C78A8",
                           showlegend=False), row=1, col=1)
fig.add_trace(go.Histogram(x=log_amounts, nbinsx=50, marker_color="#F58518",
                           showlegend=False), row=1, col=2)
fig.add_trace(go.Scatter(x=grid, y=load_pct, name="검토 부하 (용량 대비 %)",
                         line=dict(color="#4C78A8", width=3)),
              row=2, col=1, secondary_y=False)
fig.add_trace(go.Scatter(x=grid, y=risk_won, name="자동 처리 위험액 (원)",
                         line=dict(color="#E45756", width=3)),
              row=2, col=1, secondary_y=True)
fig.add_vline(x=median_t, line_dash="dash", line_color="#333",
              annotation_text=f"중앙값 {median_t:,.0f}", row=1, col=1)
fig.add_vline(x=MU, line_dash="dash", line_color="#333",
              annotation_text=f"mu={MU}", row=1, col=2)
fig.add_hline(y=70, line_dash="dash", line_color="#4C78A8",
              row=2, col=1, secondary_y=False)
fig.add_vline(x=100_000, line_dash="dot", line_color="#333",
              annotation_text="10만 원", row=2, col=1)
fig.update_xaxes(title_text="금액(원)", row=1, col=1)
fig.update_xaxes(title_text="ln(금액)", row=1, col=2)
fig.update_xaxes(type="log", title_text="문턱 (원, 로그 축)", row=2, col=1)
fig.update_yaxes(title_text="용량 대비 %", row=2, col=1, secondary_y=False)
fig.update_yaxes(title_text="위험액(원)", row=2, col=1, secondary_y=True)
fig.update_layout(
    title_text="lognormvariate(10.4, 1.15) — 중앙값 32,860원 / 평균 63,656원",
    height=800,
    width=1100,
    template="plotly_white",
    legend=dict(orientation="h", y=0.42, x=0.02),
)
_show(fig)

out = HERE / "expy.png"
fig.write_image(str(out), scale=2)
print(f"저장: {out}  ({out.stat().st_size:,} bytes)")
# 출력: 저장: .../expy.png  (253,328 bytes)

# %% [markdown]
# ## 한 줄 정리
#
# `lognormvariate(10.4, 1.15)`는 **중앙값 3.3만 원 / 평균 6.4만 원 / 최빈값 8.8천 원**의
# 우편향 금액 분포를 만든다. 소액이 압도적으로 많고 고액이 드물지만 합계에는 크게 기여한다.
#
# 금액은 여러 요인이 **곱셈적**으로 작용해 만들어지므로, 로그를 취하면 덧셈이 되고
# 중심극한정리에 의해 정규분포가 된다 — 이것이 로그정규분포를 쓰는 이론적 근거다.
#
# 이 꼬리 모양 덕분에 "검토 부하가 용량의 70%를 넘지 않는 가장 낮은 문턱"이라는
# 23.3절의 규칙이 **10만 원**이라는 구체적인 답으로 떨어진다.
