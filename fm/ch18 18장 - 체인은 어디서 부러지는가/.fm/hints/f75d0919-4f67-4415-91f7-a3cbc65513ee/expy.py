# %% [markdown]
# # 체인의 기대 비용은 어떻게 계산하는가
#
# 답: **한 회차에서 실패 지점까지 쓰는 기대 비용(도달 확률 누적)** 을 구하고,
# **전체 성공 확률의 역수**만큼 회차를 반복한다고 보고 곱한다.
#
# $$E[\text{총 비용}] = \frac{\sum_i c_i \prod_{j<i}(1-p_j)}{\prod_i (1-p_i)}$$
#
# 책 18장의 네 단계(실패율 5/8/18/10%)로 단계별로 확인하고,
# 그래프 방식 $\sum_i c_i/(1-p_i)$ 및 몬테카를로 시뮬레이션과 비교한다.

# %%
# 필요 패키지: plotly, kaleido (시각화·PNG 저장), numpy 불필요
import os
import random


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."

# 책 18장 steps.py 의 값: (이름, 시간(초), 토큰, 실패 확률)
STEPS = [
    ("문서 찾기", 12, 3_200, 0.05),
    ("요약",       8, 5_100, 0.08),
    ("초안 작성", 31, 8_400, 0.18),
    ("검토",      14, 4_300, 0.10),
]
PRICE_PER_MTOK = 4_000  # 원


def cost(tokens):
    return tokens / 1_000_000 * PRICE_PER_MTOK

# %% [markdown]
# ## 1단계 — 준비 운동: 기하분포 $E[N] = 1/p$
#
# 성공 확률 $p$인 시행을 성공할 때까지 반복하면 평균 몇 번인가?
#
# $$E[N] = p \cdot 1 + (1-p)(1 + E[N]) \;\Rightarrow\; E[N] = \frac{1}{p}$$
#
# 시뮬레이션으로 확인해 본다.

# %%
random.seed(42)

def trials_until_success(p):
    n = 1
    while random.random() >= p:
        n += 1
    return n

for p in (0.5, 0.2, 0.645):
    sim = sum(trials_until_success(p) for _ in range(100_000)) / 100_000
    print(f"성공 확률 {p:.3f} → 이론 1/p = {1/p:.3f}, 시뮬레이션 = {sim:.3f}")
# 출력: 성공 확률 0.500 → 이론 1/p = 2.000, 시뮬레이션 = 2.004
# 출력: 성공 확률 0.200 → 이론 1/p = 5.000, 시뮬레이션 = 5.011
# 출력: 성공 확률 0.645 → 이론 1/p = 1.550, 시뮬레이션 = 1.550

# %% [markdown]
# ## 2단계 — 한 회차의 기대 비용: 도달 확률 $r_i = \prod_{j<i}(1-p_j)$ 누적
#
# 단계 $i$의 비용은 그 단계에 **도달했을 때만** 쓴다. 그래서
#
# $$C_{\text{round}} = \sum_i r_i \, c_i, \qquad r_1 = 1,\; r_{i+1} = r_i (1-p_i)$$

# %%
print(f"{'단계':<8} {'실패율':>6} {'도달 확률 r':>12} {'시간(초)':>8} {'r×시간':>8}")
print("-" * 50)
reach = 1.0
t_round = tok_round = 0.0
for name, secs, tokens, p in STEPS:
    print(f"{name:<8} {p*100:>5.0f}% {reach:>12.4f} {secs:>8} {reach*secs:>8.2f}")
    t_round += reach * secs
    tok_round += reach * tokens
    reach *= (1 - p)

p_all_ok = reach  # 마지막까지 곱해진 값 = 전체 성공 확률
print("-" * 50)
print(f"한 회차 기대 시간  C_round = {t_round:.2f}초")
print(f"한 회차 기대 토큰          = {tok_round:,.0f}")
print(f"전체 성공 확률     P_ok    = {p_all_ok:.4f}")
# 출력: 문서 찾기    5%       1.0000       12    12.00
# 출력: 요약         8%       0.9500        8     7.60
# 출력: 초안 작성   18%       0.8740       31    27.09
# 출력: 검토        10%       0.7167       14    10.03
# 출력: 한 회차 기대 시간  C_round = 56.73초
# 출력: 한 회차 기대 토큰          = 18,468
# 출력: 전체 성공 확률     P_ok    = 0.6450

# %% [markdown]
# ## 3단계 — 합치기: 회차 수 $= 1/P_{ok}$ 를 곱한다
#
# $$E[\text{총 비용}] = C_{\text{round}} \times \frac{1}{P_{\text{ok}}}$$

# %%
def expected_chain(steps):
    """체인: 실패하면 처음부터. (기대 시간, 기대 토큰)"""
    t = tok = 0.0
    reach = 1.0
    for _, secs, tokens, p in steps:
        t += reach * secs
        tok += reach * tokens
        reach *= (1 - p)
    return t / reach, tok / reach  # reach == P_ok


def expected_graph(steps):
    """상태 그래프: 실패한 단계만 다시. 단계별 기하분포 1/(1-p)."""
    t = sum(secs / (1 - p) for _, secs, _, p in steps)
    tok = sum(tokens / (1 - p) for _, _, tokens, p in steps)
    return t, tok


one_shot_t = sum(s for _, s, _, _ in STEPS)
one_shot_tok = sum(k for _, _, k, _ in STEPS)
ct, ctok = expected_chain(STEPS)
gt, gtok = expected_graph(STEPS)

print(f"한 번에 성공하면      {one_shot_t:>6.1f}초  {cost(one_shot_tok):>7.1f}원")
print(f"체인 기대 비용        {ct:>6.1f}초  {cost(ctok):>7.1f}원   (= {t_round:.2f} × {1/p_all_ok:.3f})")
print(f"그래프 기대 비용      {gt:>6.1f}초  {cost(gtok):>7.1f}원   (= Σ c_i/(1-p_i))")
print(f"그래프가 아끼는 시간  {(1 - gt/ct)*100:>5.1f}%")
# 출력: 한 번에 성공하면        65.0초     84.0원
# 출력: 체인 기대 비용          87.9초    114.5원   (= 56.73 × 1.550)
# 출력: 그래프 기대 비용        74.7초     95.7원   (= Σ c_i/(1-p_i))
# 출력: 그래프가 아끼는 시간   15.1%

# %% [markdown]
# ## 4단계 — 몬테카를로 시뮬레이션으로 공식 검증
#
# 공식이 맞는지, 실제로 체인을 10만 번 돌려서 평균을 재 본다.

# %%
random.seed(7)

def simulate_chain_once(steps):
    """성공할 때까지 처음부터 반복. 총 소요 시간을 돌려준다."""
    total = 0.0
    while True:
        ok = True
        for _, secs, _, p in steps:
            total += secs
            if random.random() < p:
                ok = False
                break  # 실패 지점까지만 쓰고 회차 종료
        if ok:
            return total

N = 100_000
sim_t = sum(simulate_chain_once(STEPS) for _ in range(N)) / N
print(f"공식      : {ct:.2f}초")
print(f"시뮬레이션: {sim_t:.2f}초  (10만 회 평균)")
# 출력: 공식      : 87.95초
# 출력: 시뮬레이션: 87.97초  (10만 회 평균)

# %% [markdown]
# ## 5단계 — 마지막 단계 실패율을 키우면: 체인 vs 그래프
#
# 체인은 분모 $P_{ok}$가 곱셈으로 작아져 비용이 **비선형으로** 튀고,
# 그래프는 해당 항 $c_4/(1-p_4)$만 늘어난다. 뒤쪽 실패율이 높을수록 격차가 벌어진다.

# %%
import plotly.graph_objects as go

p_lasts = [i / 100 for i in range(0, 61, 5)]
chain_ts, graph_ts = [], []
for p_last in p_lasts:
    steps = STEPS[:-1] + [("검토", 14, 4_300, p_last)]
    chain_ts.append(expected_chain(steps)[0])
    graph_ts.append(expected_graph(steps)[0])

fig = go.Figure()
fig.add_scatter(x=[p * 100 for p in p_lasts], y=chain_ts,
                name="체인 (실패하면 처음부터)", mode="lines+markers",
                line=dict(color="#d62728", width=3))
fig.add_scatter(x=[p * 100 for p in p_lasts], y=graph_ts,
                name="그래프 (실패한 단계만 다시)", mode="lines+markers",
                line=dict(color="#1f77b4", width=3))
fig.add_hline(y=one_shot_t, line_dash="dot", line_color="gray",
              annotation_text="한 번에 성공 (65초)")
fig.update_layout(
    title="마지막 단계 실패율에 따른 기대 시간 — 체인 vs 상태 그래프",
    xaxis_title="마지막 단계(검토) 실패율 (%)",
    yaxis_title="기대 총 시간 (초)",
    width=800, height=500, template="plotly_white",
    legend=dict(x=0.02, y=0.98),
)
_show(fig)
fig.write_image(os.path.join(HERE, "expy.png"), scale=2)

for p_last, c, g in zip(p_lasts[::4], chain_ts[::4], graph_ts[::4]):
    print(f"검토 실패율 {p_last*100:>3.0f}% → 체인 {c:>6.1f}초, 그래프 {g:>6.1f}초, 격차 {c-g:>5.1f}초")
print("expy.png 저장 완료")
# 출력: 검토 실패율   0% → 체인   79.2초, 그래프   73.1초, 격차   6.0초
# 출력: 검토 실패율  20% → 체인   98.9초, 그래프   76.6초, 격차  22.3초
# 출력: 검토 실패율  40% → 체인  131.9초, 그래프   82.5초, 격차  49.5초
# 출력: 검토 실패율  60% → 체인  197.9초, 그래프   94.1초, 격차 103.8초
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# 체인의 기대 비용 계산은 두 겹이다.
#
# 1. **한 회차의 기대 비용**: 각 단계 비용에 도달 확률 $r_i = \prod_{j<i}(1-p_j)$를 곱해 누적
#    — 실패 지점 뒤의 비용은 도달 확률이 곱해지며 자동으로 빠진다.
# 2. **회차 반복**: 전체 성공 확률 $P_{ok} = \prod_i(1-p_i)$의 역수(기하분포 기대값)를 곱한다.
#
# $$E[\text{총 비용}] = \frac{\sum_i c_i \prod_{j<i}(1-p_j)}{\prod_i (1-p_i)}$$
#
# 그래프는 실패한 단계만 다시 하므로 $\sum_i c_i/(1-p_i)$ — 뒤쪽 실패율이 높거나
# 단계가 많을수록 체인의 분모가 작아져 격차가 벌어진다.
