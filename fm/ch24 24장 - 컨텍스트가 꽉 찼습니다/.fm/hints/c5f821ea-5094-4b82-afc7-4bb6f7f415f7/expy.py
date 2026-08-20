# %% [markdown]
# # 요약을 다섯 번 반복하면 전체 생존율은 어떻게 되는가
#
# **답: 한 번은 68%지만 다섯 번이면 23%다. 회차마다 확률이 곱해지기 때문이다.**
#
# 이 스크립트는 그 숫자를 네 단계로 쌓아 올린다.
#
# 1. 곱셈 모형: $S(n) = p^n$ — 왜 뺄셈이 아닌가
# 2. 책의 혼합 모형: 사실 종류마다 생존 확률이 다르다
# 3. 시뮬레이션 재현: 68% / 23%가 실제로 나오는지
# 4. 볼록성(젠센 부등식)과 생존자 편향: 왜 $0.64^5$보다 많이 남는가
#
# 필요 패키지: plotly, kaleido (정적 이미지 저장용). 나머지는 표준 라이브러리.

# %%
import math
import os
import random

import plotly.graph_objects as go


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
print("작업 폴더:", os.path.basename(HERE))
# 출력: 작업 폴더: c5f821ea-5094-4b82-afc7-4bb6f7f415f7

# %% [markdown]
# ## 1. 곱셈이지 뺄셈이 아니다
#
# 한 번 요약에서 한 사실이 살아남을 확률을 $p$라 하자. 회차가 독립이면
#
# $$S(n) = \underbrace{p \times p \times \cdots \times p}_{n\text{개}} = p^{\,n}$$
#
# 흔한 오해는 "한 번에 32% 잃으니 다섯 번이면 $32\times5=160\%$"라는 뺄셈식 계산이다.
# 이미 사라진 사실은 다시 사라질 수 없으므로 그런 일은 일어나지 않는다.


# %%
def survival_uniform(p, n):
    """모든 사실의 1회 생존 확률이 같을 때의 n회차 생존율."""
    return p**n


p1 = 0.68
print(f"{'회차':>4} {'곱셈모형 p^n':>14} {'(틀린) 뺄셈식':>16}")
for n in range(6):
    wrong = max(0.0, 1 - (1 - p1) * n)
    print(f"{n:>4} {survival_uniform(p1, n):>13.1%} {wrong:>15.1%}")
# 출력:
#   회차     곱셈모형 p^n      (틀린) 뺄셈식
#     0        100.0%          100.0%
#     1         68.0%           68.0%
#     2         46.2%           36.0%
#     3         31.4%            4.0%
#     4         21.4%            0.0%
#     5         14.5%            0.0%
# → 뺄셈식은 4회차에 "전멸"이라고 말한다. 곱셈은 결코 0에 닿지 않지만 지수로 줄어든다.

# %% [markdown]
# ### 반감기
#
# $p^n = 0.5$를 풀면 사실의 절반이 날아가는 데 몇 회차가 걸리는지 나온다.
#
# $$n = \frac{\ln 0.5}{\ln p}$$

# %%
for p in (0.90, 0.68, 0.64, 0.45):
    half = math.log(0.5) / math.log(p)
    print(f"p={p:.2f} → 반감기 {half:.2f}회차")
# 출력:
# p=0.90 → 반감기 6.58회차
# p=0.68 → 반감기 1.80회차
# p=0.64 → 반감기 1.55회차
# p=0.45 → 반감기 0.87회차
# → p=0.68이면 요약 두 번 만에 이미 절반이 사라진다.

# %% [markdown]
# ## 2. 책의 모형: 사실은 한 종류가 아니다
#
# 24장 `ex3_summary_drift.py`는 사실을 다섯 종류로 나누고 종류마다 다른 생존 확률을 준다.
# 비중 $w_k$로 섞으면 $n$회차 생존율의 기댓값은
#
# $$S(n) = \sum_k w_k \, p_k^{\,n}$$

# %%
KINDS = {
    # 종류        (비중, 1회 생존 확률)
    "숫자": (0.20, 0.55),  # 금액·개수 — 요약이 «대략»으로 바꾼다
    "고유명사": (0.20, 0.80),  # 이름 — 비교적 잘 남는다
    "결정": (0.20, 0.90),  # «~하기로 했다» — 요약이 제일 잘 지킨다
    "이유": (0.20, 0.45),  # «왜 그랬나» — 제일 먼저 날아간다
    "제약": (0.20, 0.50),  # «하면 안 된다» — 이것도 잘 날아간다
}
ROUNDS = 5


def survival_mixture(n):
    return sum(w * p**n for w, p in KINDS.values())


p_mean = sum(w * p for w, p in KINDS.values())
print(f"1회 생존 확률의 가중평균 E[p] = {p_mean:.3f}\n")
print(f"{'회차':>4} {'혼합 이론':>10}" + "".join(f"{k:>9}" for k in KINDS))
for n in range(ROUNDS + 1):
    per = "".join(f"{p**n:>9.0%}" for _, p in KINDS.values())
    print(f"{n:>4} {survival_mixture(n):>9.1%}" + per)
# 출력:
# 1회 생존 확률의 가중평균 E[p] = 0.640
#
#   회차      혼합 이론       숫자     고유명사       결정       이유       제약
#     0    100.0%     100%     100%     100%     100%     100%
#     1     64.0%      55%      80%      90%      45%      50%
#     2     44.1%      30%      64%      81%      20%      25%
#     3     32.5%      17%      51%      73%       9%      12%
#     4     25.2%       9%      41%      66%       4%       6%
#     5     20.4%       5%      33%      59%       2%       3%

# %% [markdown]
# ## 3. 시뮬레이션 재현 — 68%와 23%
#
# 책과 같은 시드(사실 생성 5, 압축 99)로 사실 200개를 굴린다.

# %%
N = 200


def make_facts(seed=5):
    rng = random.Random(seed)
    kinds = list(KINDS)
    return [{"id": i, "kind": rng.choice(kinds), "alive": True} for i in range(N)]


def compress(facts, rng):
    for f in facts:
        if f["alive"] and rng.random() > KINDS[f["kind"]][1]:
            f["alive"] = False
    return facts


facts = make_facts()
rng = random.Random(99)
kinds = list(KINDS)
sim_total, sim_per_kind = [], {k: [] for k in kinds}

print(f"{'요약 회차':>8}{'전체 생존':>10}" + "".join(f"{k:>9}" for k in kinds))
print("-" * 62)
for r in range(ROUNDS + 1):
    if r:
        compress(facts, rng)
    alive = sum(f["alive"] for f in facts)
    sim_total.append(alive / N)
    row = ""
    for k in kinds:
        tot = sum(1 for f in facts if f["kind"] == k)
        liv = sum(1 for f in facts if f["kind"] == k and f["alive"])
        sim_per_kind[k].append(liv / tot)
        row += f"{liv / tot:>8.0%}"
    print(f"{r:>8}{alive / N:>9.0%}" + row)
# 출력:
#    요약 회차     전체 생존       숫자     고유명사       결정       이유       제약
# --------------------------------------------------------------
#        0     100%    100%    100%    100%    100%    100%
#        1      68%     63%     74%     90%     49%     55%
#        2      52%     37%     65%     81%     35%     27%
#        3      40%     23%     56%     71%     11%     18%
#        4      30%     11%     47%     63%      5%      6%
#        5      23%      3%     37%     56%      0%      0%
# → 카드의 68%(1회)와 23%(5회)가 그대로 나온다.
# → 더 무서운 건 «이유»와 «제약»이 5회차에 0%라는 점이다.

# %%
# 이론값(64%, 20.4%)과 시뮬 표본값(68%, 23%)의 차이는 표본 오차 범위인가?
se = math.sqrt(N * p_mean * (1 - p_mean)) / N
print(f"1회차 이론 {survival_mixture(1):.1%}, 시뮬 {sim_total[1]:.1%}, 표준오차 ±{se:.1%}")
print(f"차이 {abs(sim_total[1] - survival_mixture(1)) / se:.2f} 표준오차 → 우연 범위")
# 출력:
# 1회차 이론 64.0%, 시뮬 68.5%, 표준오차 ±3.4%
# 차이 1.33 표준오차 → 우연 범위

# %% [markdown]
# ## 4. 왜 $0.64^5 = 10.7\%$가 아니라 20%대인가
#
# 1회 생존율이 64%로 같아도, **모두 똑같이 64%**인 경우와 **평균이 64%인 여러 종류가 섞인** 경우의
# 5회차 결과가 다르다. $f(x)=x^n$이 아래로 볼록($f''(x)=n(n-1)x^{n-2}>0$)하므로 젠센 부등식에 의해
#
# $$\mathbb{E}[p^{\,n}] \;\ge\; \left(\mathbb{E}[p]\right)^{n}$$
#
# $p$가 넓게 흩어져 있을수록 격차가 커진다.

# %%
print(f"{'회차':>4} {'균질 0.64^n':>12} {'혼합 E[p^n]':>12} {'배율':>7}")
for n in range(ROUNDS + 1):
    u, m = survival_uniform(p_mean, n), survival_mixture(n)
    print(f"{n:>4} {u:>11.1%} {m:>11.1%} {m / u:>6.2f}x")
# 출력:
#   회차   균질 0.64^n   혼합 E[p^n]      배율
#     0      100.0%      100.0%   1.00x
#     1       64.0%       64.0%   1.00x
#     2       41.0%       44.1%   1.08x
#     3       26.2%       32.5%   1.24x
#     4       16.8%       25.2%   1.50x
#     5       10.7%       20.4%   1.90x

# %% [markdown]
# ### 생존자 편향: 조건부 생존율이 회차마다 «올라간다»
#
# $$\frac{S(n+1)}{S(n)}$$
#
# 약한 종류(이유·제약)는 이미 전멸했고 튼튼한 종류(결정)만 남았기 때문이다.
# 그래서 "20%나 남았네"는 좋은 소식이 아니다. 남은 20%가 온통 «결론»뿐이라는 뜻이다.

# %%
for n in range(ROUNDS):
    ratio = survival_mixture(n + 1) / survival_mixture(n)
    print(f"{n}회차 → {n + 1}회차 조건부 생존율 {ratio:.3f}")
# 출력:
# 0회차 → 1회차 조건부 생존율 0.640
# 1회차 → 2회차 조건부 생존율 0.689
# 2회차 → 3회차 조건부 생존율 0.736
# 3회차 → 4회차 조건부 생존율 0.777
# 4회차 → 5회차 조건부 생존율 0.808

# %%
# 5회차 생존 사실의 «구성»은 어떻게 바뀌었나 (이론값 기준)
tot5 = survival_mixture(ROUNDS)
print("5회차에 남은 사실의 종류별 구성비:")
for k, (w, p) in KINDS.items():
    print(f"  {k:>6}: 처음 {w:>4.0%} → 남은 것 중 {w * p**ROUNDS / tot5:>5.1%}")
# 출력:
# 5회차에 남은 사실의 종류별 구성비:
#     숫자: 처음  20% → 남은 것 중  4.9%
#  고유명사: 처음  20% → 남은 것 중 32.2%
#     결정: 처음  20% → 남은 것 중 58.0%
#     이유: 처음  20% → 남은 것 중  1.8%
#     제약: 처음  20% → 남은 것 중  3.1%

# %% [markdown]
# ## 5. 대응책을 수식으로 — 요약의 요약을 하지 않으면 지수가 사라진다
#
# 매번 «원문»에서 다시 요약하면 회차가 아무리 늘어도 $S = p$로 고정된다($p^n$이 아니다).
# 원문을 외부에 들고 있어야(오프로딩) 가능한 일이다.

# %%
print(f"{'회차':>4} {'요약의 요약 p^n':>16} {'매번 원문에서 p':>16}")
for n in range(1, ROUNDS + 1):
    print(f"{n:>4} {survival_mixture(n):>15.1%} {survival_mixture(1):>15.1%}")
# 출력:
#   회차   요약의 요약 p^n     매번 원문에서 p
#     1           64.0%           64.0%
#     2           44.1%           64.0%
#     3           32.5%           64.0%
#     4           25.2%           64.0%
#     5           20.4%           64.0%

# %% [markdown]
# ## 6. 그림으로 보기

# %%
x = list(range(ROUNDS + 1))
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=x, y=[survival_uniform(p1, n) for n in x], name="균질 0.68ⁿ (곱셈)",
        mode="lines+markers", line=dict(color="#888", dash="dot", width=2),
    )
)
fig.add_trace(
    go.Scatter(
        x=x, y=[survival_uniform(p_mean, n) for n in x], name="균질 0.64ⁿ",
        mode="lines+markers", line=dict(color="#bbb", dash="dash", width=2),
    )
)
fig.add_trace(
    go.Scatter(
        x=x, y=[survival_mixture(n) for n in x], name="혼합 이론 Σwₖpₖⁿ",
        mode="lines+markers", line=dict(color="#1f77b4", width=3),
    )
)
fig.add_trace(
    go.Scatter(
        x=x, y=sim_total, name="시뮬레이션 (책, n=200)",
        mode="lines+markers", line=dict(color="#d62728", width=3),
        marker=dict(size=10, symbol="square"),
    )
)
fig.add_trace(
    go.Scatter(
        x=x, y=[max(0.0, 1 - (1 - p1) * n) for n in x], name="(틀린) 뺄셈식 1−0.32n",
        mode="lines", line=dict(color="#ff7f0e", dash="longdash", width=2),
    )
)

for n, label in ((1, "68%"), (5, "23%")):
    fig.add_annotation(
        x=n, y=sim_total[n], text=f"<b>{label}</b>", showarrow=True, arrowhead=2,
        ax=30, ay=-35, font=dict(size=15, color="#d62728"),
    )

fig.update_layout(
    title="요약 반복과 사실 생존율 — 회차마다 확률이 곱해진다",
    xaxis_title="요약 회차 n",
    yaxis_title="전체 생존율 S(n)",
    yaxis=dict(tickformat=".0%", range=[0, 1.05]),
    xaxis=dict(dtick=1),
    template="plotly_white",
    width=980,
    height=560,
    legend=dict(x=0.98, y=0.98, xanchor="right", yanchor="top", bgcolor="rgba(255,255,255,0.75)"),
)
_show(fig)

out = os.path.join(HERE, "expy.png")
fig.write_image(out, scale=2)
print("저장:", os.path.basename(out))
# 출력: 저장: expy.png

# %%
# 종류별 생존 곡선 — «무엇이» 남는가
fig2 = go.Figure()
palette = {"결정": "#2ca02c", "고유명사": "#1f77b4", "숫자": "#ff7f0e", "제약": "#9467bd", "이유": "#d62728"}
for k in kinds:
    fig2.add_trace(
        go.Scatter(x=x, y=sim_per_kind[k], name=f"{k} (p={KINDS[k][1]})",
                   mode="lines+markers", line=dict(color=palette[k], width=3))
    )
fig2.update_layout(
    title="같은 23% 안에서도 «이유»와 «제약»은 5회차에 0%가 된다",
    xaxis_title="요약 회차 n", yaxis_title="종류별 생존율",
    yaxis=dict(tickformat=".0%", range=[0, 1.05]), xaxis=dict(dtick=1),
    template="plotly_white", width=980, height=520,
)
_show(fig2)
print("종류별 5회차 생존율:", {k: f"{sim_per_kind[k][5]:.0%}" for k in kinds})
# 출력: 종류별 5회차 생존율: {'숫자': '3%', '고유명사': '37%', '결정': '56%', '이유': '0%', '제약': '0%'}

# %% [markdown]
# ## 정리
#
# - 한 번 요약: **68%**. 다섯 번: **23%**. 회차마다 확률이 **곱해지기** 때문이다 ($S(n)=p^n$ 꼴).
# - 균질 모형이라면 $0.64^5 = 10.7\%$까지 떨어졌겠지만, 사실 종류마다 생존 확률이 달라
#   (젠센 부등식) 20%대에서 멈춘다. 좋은 소식이 아니다 — 남은 것이 «결정»에 몰려 있다는 뜻이다.
# - 대응: ① 요약의 요약을 하지 않는다(매번 원문에서 → 지수가 사라진다),
#   ② 보존할 종류를 프롬프트에 못 박아 $p_k$를 1에 가깝게 만든다,
#   ③ 절감률만이 아니라 «참조되는 사실의 잔존율»을 함께 잰다.
