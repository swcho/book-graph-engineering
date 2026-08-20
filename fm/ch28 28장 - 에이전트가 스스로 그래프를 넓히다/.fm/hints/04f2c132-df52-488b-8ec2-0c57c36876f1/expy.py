# %% [markdown]
# # 제약은 「지워져서」가 아니라 「묽어져서」 사라진다
#
# 28.4절의 그래프 드리프트를 두 단계로 나눠서 봅니다.
#
# 1. **묽어지는 단계** — 에이전트가 자기가 쓴 그래프를 읽고 또 쓰면
#    「제약」의 *비율*이 20%에서 9%로 내려간다. 제약 노드 개수 자체는 늘어난다.
# 2. **사라지는 단계** — 조회는 항상 상위 $k$개만 본다.
#    비율이 내려가면 그 $k$개 안에 제약이 **한 개도 안 들어오기 시작**한다.
#
# 즉 삭제(delete)는 한 번도 일어나지 않는데, 검색 결과에서는 사라집니다.
# 이 노트북은 2번 단계의 확률을 초기하분포로 정확히 계산하고,
# 이항 근사 및 몬테카를로 시뮬레이션으로 교차 검증합니다.
#
# 필요 패키지: `plotly`, `numpy`, `scipy`, `kaleido`(정적 이미지 저장용)

# %%
import math
import random

import numpy as np
import plotly.graph_objects as go
from scipy.stats import hypergeom


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


print("준비 완료")

# 출력: 준비 완료

# %% [markdown]
# ## 1단계 — 비율이 묽어지는 과정 재현
#
# 본문 `ex4_drift.py`의 축약판입니다. 에이전트는 그래프에서 사실 하나를 읽고,
# 그것에 이끌려 새 사실을 씁니다. 「무엇을 읽으면 무엇을 쓰는가」가 `EMIT`입니다.
#
# 제약이 줄어드는 이유는 자기 재생산율($0.35$)만이 아닙니다.
# 가장 흔한 종류인 「관계」가 제약을 낳아 주는 비율이 $0.05$로 극히 낮기 때문입니다.
# 살아남는 비율은 **자기 재생산율 × 전체 분포의 곱**이 결정합니다.

# %%
KINDS = ["관계", "선호", "제약", "사건"]
START = {"관계": 40, "선호": 30, "제약": 20, "사건": 10}
EMIT = {
    "관계": {"관계": 0.62, "선호": 0.18, "제약": 0.05, "사건": 0.15},
    "선호": {"관계": 0.20, "선호": 0.55, "제약": 0.10, "사건": 0.15},
    "제약": {"관계": 0.25, "선호": 0.20, "제약": 0.35, "사건": 0.20},
    "사건": {"관계": 0.40, "선호": 0.20, "제약": 0.05, "사건": 0.35},
}
GEN, PER_GEN = 100, 20


def run_drift(human_share, seed=3):
    rng = random.Random(seed)
    c = dict(START)
    for _ in range(GEN):
        new = dict(c)
        for _ in range(PER_GEN):
            if rng.random() < human_share:
                k = rng.choices(KINDS, [START[x] for x in KINDS])[0]
            else:
                s = rng.choices(KINDS, [c[x] for x in KINDS])[0]
                k = rng.choices(KINDS, [EMIT[s][x] for x in KINDS])[0]
            new[k] += 1
        c = new
    t = sum(c.values())
    return c, {k: c[k] / t for k in KINDS}


counts_0, share_0 = run_drift(0.0)
counts_2, share_2 = run_drift(0.2)

print(f"{'':>14}" + "".join(f"{k:>9}" for k in KINDS))
print(f"{'시작':>14}" + "".join(f"{START[k] / 100:>8.0%}" for k in KINDS))
print(f"{'사람 0%':>14}" + "".join(f"{share_0[k]:>8.0%}" for k in KINDS))
print(f"{'사람 20%':>14}" + "".join(f"{share_2[k]:>8.0%}" for k in KINDS))
print()
print(f"제약 개수: 시작 20개 -> {counts_0['제약']}개 (지워진 게 아니라 늘었다)")
print(f"제약 비율: 20% -> {share_0['제약']:.0%}  <- 사라진 건 이쪽")

# 출력:
#                      관계       선호       제약       사건
#             시작     40%     30%     20%     10%
#          사람 0%     42%     30%      9%     19%
#         사람 20%     42%     29%     12%     17%
#
# 제약 개수: 시작 20개 -> 197개 (지워진 게 아니라 늘었다)
# 제약 비율: 20% -> 9%  <- 사라진 건 이쪽

# %% [markdown]
# ## 2단계 — 상위 $k$개에 제약이 하나도 안 들어올 확률
#
# 전체 사실이 $N$개, 그중 제약이 $K = pN$개일 때
# 조회가 상위 $k$개를 뽑는다고 합시다.
# 「제약과의 관련도」가 질의마다 특별히 높지 않다고 보면(즉 순위가 종류에 중립),
# 뽑히는 제약 개수 $X$는 **초기하분포**를 따릅니다.
#
# $$X \sim \mathrm{Hypergeom}(N,\ K,\ k), \qquad
# P(X = 0) \;=\; \frac{\binom{N-K}{k}}{\binom{N}{k}}$$
#
# $N \gg k$이면 복원추출과 다를 게 없어 **이항 근사**가 잘 맞습니다.
#
# $$P(X = 0) \;\approx\; (1 - p)^{k}$$
#
# 그리고 top-$k$ 안의 제약 기대 개수는 $\mathbb{E}[X] = kp$입니다.
# $k = 10$, $p = 0.09$면 $0.9$개 — **평균 한 개도 안 되는** 상태입니다.

# %%
N = 2000  # 전체 사실 수
K_TOPK = 10  # 조회가 보는 상위 개수


def p_miss_exact(p, N=N, k=K_TOPK):
    """초기하분포: top-k에 제약이 0개일 확률"""
    return float(hypergeom.pmf(0, N, round(p * N), k))


def p_miss_approx(p, k=K_TOPK):
    """이항 근사"""
    return (1 - p) ** k


print(f"N={N}, top-k={K_TOPK}\n")
print(f"{'제약 비율':>10}{'제약 수':>9}{'E[X]=kp':>10}{'P(X=0) 정확':>13}{'이항 근사':>11}{'오차':>10}")
print("-" * 64)
for label, p in [("시작 20%", 0.20), ("사람개입 12%", 0.12), ("경보선 10%", 0.10), ("드리프트 9%", 0.09)]:
    e, a = p_miss_exact(p), p_miss_approx(p)
    print(f"{label:>10}{round(p * N):>9}{K_TOPK * p:>10.2f}{e:>13.3%}{a:>11.3%}{abs(e - a):>10.4%}")

# 출력:
# N=2000, top-k=10
#
#      제약 비율     제약 수   E[X]=kp    P(X=0) 정확      이항 근사        오차
# ----------------------------------------------------------------
#     시작 20%      400      2.00      10.677%    10.737%   0.0604%
#   사람개입 12%      240      1.20      27.764%    27.850%   0.0856%
#    경보선 10%      200      1.00      34.780%    34.868%   0.0874%
#    드리프트 9%      180      0.90      38.855%    38.942%   0.0868%

# %% [markdown]
# 정확값과 이항 근사가 0.1%p 이내로 일치합니다. 이후로는 근사식으로 이야기해도 됩니다.
#
# 읽는 법: 제약 비율이 **20% → 9%로 절반 조금 넘게** 떨어졌는데,
# 「제약을 하나도 못 보는 조회」는 **10.7% → 38.9%로 3.6배**가 됐습니다.
# 비율은 선형으로 묽어지지만 조회 실패는 $(1-p)^k$라 훨씬 가파르게 오릅니다.

# %%
print(f"{'구간':>26}{'P(놓침)':>10}{'배수':>8}")
print("-" * 44)
base = p_miss_approx(0.20)
for label, p in [("드리프트 전 20%", 0.20), ("사람 개입 20% 넣어도 12%", 0.12), ("에이전트만 9%", 0.09)]:
    v = p_miss_approx(p)
    print(f"{label:>26}{v:>10.1%}{v / base:>8.2f}x")

print()
for p in (0.20, 0.12, 0.09):
    # 제약을 한 번이라도 보려면 평균 몇 번 조회해야 하나 (기하분포 기댓값)
    hit = 1 - p_miss_approx(p)
    print(f"비율 {p:.0%}: 제약을 한 번 보기까지 평균 조회 {1 / hit:.2f}회, "
          f"연속 5회 조회에서 전멸할 확률 {p_miss_approx(p) ** 5:.2%}")

# 출력:
#                         구간     P(놓침)      배수
# --------------------------------------------
#                 드리프트 전 20%     10.7%    1.00x
#          사람 개입 20% 넣어도 12%     27.9%    2.59x
#                   에이전트만 9%     38.9%    3.63x
#
# 비율 20%: 제약을 한 번 보기까지 평균 조회 1.12회, 연속 5회 조회에서 전멸할 확률 0.00%
# 비율 12%: 제약을 한 번 보기까지 평균 조회 1.39회, 연속 5회 조회에서 전멸할 확률 0.17%
# 비율 9%: 제약을 한 번 보기까지 평균 조회 1.64회, 연속 5회 조회에서 전멸할 확률 0.90%

# %% [markdown]
# ## 몬테카를로 검증
#
# 실제로 $N$개에서 비복원으로 $k$개를 뽑아 보고, 이론값과 맞는지 확인합니다.

# %%
rng = np.random.default_rng(28)
TRIALS = 200_000

print(f"{'p':>6}{'이론 P(X=0)':>14}{'시뮬레이션':>12}{'차이':>10}{'E[X] 이론':>11}{'E[X] 시뮬':>11}")
print("-" * 64)
for p in (0.20, 0.12, 0.10, 0.09):
    K = round(p * N)
    draws = rng.hypergeometric(K, N - K, K_TOPK, size=TRIALS)
    sim_miss = float((draws == 0).mean())
    th = p_miss_exact(p)
    print(f"{p:>6.2f}{th:>14.3%}{sim_miss:>12.3%}{abs(th - sim_miss):>10.3%}"
          f"{K_TOPK * p:>11.2f}{draws.mean():>11.2f}")

# 출력:
#      p     이론 P(X=0)       시뮬레이션        차이    E[X] 이론    E[X] 시뮬
# ----------------------------------------------------------------
#   0.20       10.677%     10.806%    0.129%       2.00       2.00
#   0.12       27.764%     27.786%    0.021%       1.20       1.20
#   0.10       34.780%     34.810%    0.030%       1.00       1.00
#   0.09       38.855%     38.921%    0.067%       0.90       0.90

# %% [markdown]
# 이론값과 0.13%p 이내로 일치합니다. 초기하 모델이 맞습니다.
#
# ## $k$를 키우면 해결될까
#
# $(1-p)^k$에서 $k$를 키우면 놓침 확률은 내려갑니다. 하지만
#
# $$k^{*} = \frac{\ln \varepsilon}{\ln(1-p)}$$
#
# 이 「놓침 확률을 $\varepsilon$ 이하로 만드는 최소 $k$」입니다.
# $p$가 묽어질수록 필요한 $k$가 커지고, $k$는 컨텍스트 예산(24장)에 직접 부딪힙니다.

# %%
print(f"{'제약 비율':>10}" + "".join(f"{f'ε={e:.0%}':>10}" for e in (0.10, 0.05, 0.01)))
print("-" * 40)
for p in (0.20, 0.12, 0.09, 0.05):
    row = "".join(f"{math.ceil(math.log(e) / math.log(1 - p)):>10}" for e in (0.10, 0.05, 0.01))
    print(f"{p:>10.0%}{row}")

# 출력:
#      제약 비율     ε=10%      ε=5%      ε=1%
# ----------------------------------------
#        20%        11        14        21
#        12%        19        24        37
#         9%        25        32        49
#         5%        45        59        90

# %% [markdown]
# 20%일 때 top-11이면 되던 것이 9%가 되면 top-25가 필요합니다.
# 검색기를 그대로 두면 제약은 조용히 시야 밖으로 밀려납니다.
#
# ## 시각화

# %%
ps = np.linspace(0.01, 0.30, 300)
fig = go.Figure()

for k, color in [(5, "#e15759"), (10, "#4e79a7"), (20, "#59a14f")]:
    fig.add_trace(go.Scatter(
        x=ps * 100, y=(1 - ps) ** k * 100,
        mode="lines", name=f"top-{k}",
        line=dict(width=3, color=color),
        hovertemplate="제약 비율 %{x:.1f}%<br>놓침 %{y:.1f}%<extra>top-" + str(k) + "</extra>",
    ))

for x, txt, dash in [(20, "시작 20%", "dot"), (12, "사람 개입 12%", "dot"), (9, "드리프트 9%", "dash")]:
    fig.add_vline(x=x, line=dict(color="#888", width=1, dash=dash),
                  annotation_text=txt, annotation_position="top",
                  annotation_font=dict(size=11, color="#666"))

fig.add_trace(go.Scatter(
    x=[20, 9], y=[(1 - 0.20) ** 10 * 100, (1 - 0.09) ** 10 * 100],
    mode="markers+text", name="top-10 이동",
    marker=dict(size=13, color="#4e79a7", line=dict(width=2, color="white")),
    text=["10.7%", "38.9%"], textposition="middle right",
    textfont=dict(size=12, color="#4e79a7"), showlegend=False,
))

fig.update_layout(
    title="제약이 묽어질수록 top-k 조회에서 제약이 한 개도 안 뽑힐 확률",
    xaxis_title="그래프 안의 제약 비율 p (%)",
    yaxis_title="P(top-k 안에 제약 0개)  (%)",
    template="plotly_white", width=900, height=520,
    legend=dict(x=0.98, y=0.98, xanchor="right", yanchor="top"),
    margin=dict(t=90),
)
fig.update_xaxes(range=[1, 30])
fig.update_yaxes(range=[0, 100])

_show(fig)

try:
    fig.write_image("expy.png", scale=2)
    print("expy.png 저장 완료")
except Exception as exc:  # kaleido 미설치 등
    print(f"이미지 저장 실패: {exc}")

# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# | 관찰 | 값 |
# |---|---|
# | 제약 **개수** | 20개 → 197개 (**늘었다**) |
# | 제약 **비율** | 20% → 9% |
# | top-10에 제약 0개일 확률 | 10.7% → 38.9% (3.6배) |
# | top-10 안의 제약 기대 개수 | 2.0개 → 0.9개 |
# | 놓침 10% 이하로 만들 $k$ | 11 → 25 |
#
# - 제약을 지운 주체는 아무도 없습니다. 삭제 로그를 뒤져도 안 나옵니다.
#   **비율**이 묽어졌고, 조회가 상위 $k$개만 보기 때문에 결과에서 빠졌을 뿐입니다.
# - 사람이 쓰기의 20%를 담당해도 9%가 12%로 완화될 뿐, 방향은 그대로입니다.
#   놓침 확률은 여전히 시작 대비 2.6배입니다.
# - 그래서 개입 지점은 개별 사실이 아니라 **비율**입니다.
#   「관계가 55%를 넘으면 관계 쓰기 중단」, 「제약이 10% 아래면 경보」 같은
#   종류별 비율 상한/하한을 매일 쿼리 한 줄로 재야 합니다.
#   이 지표가 없으면 묽어지는 것을 영영 못 봅니다.
