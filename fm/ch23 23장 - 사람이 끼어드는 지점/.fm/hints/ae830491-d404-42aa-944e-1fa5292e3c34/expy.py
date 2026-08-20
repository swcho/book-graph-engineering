# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# %% [markdown]
# # 승인 문턱은 무엇으로 정하는가 — 취향이 아니라 용량
#
# 23장 `ex3_gate_policy.py`의 재현입니다.
#
# **질문**: 승인 문턱(사람이 직접 검토할 금액 기준선)은 무엇으로 정해야 하는가?
#
# **답**: 취향이 아니라 **용량**으로 정한다.
# 검토 시간이 용량의 **70%**를 넘지 않는 문턱 중 **가장 낮은 것**을 고른다.
#
# 왜 이 두 조건이 한 쌍인지가 핵심입니다.
#
# - **70% 상한**: 검토 시간이 용량을 넘으면 큐가 쌓이고, 담당자가 대충 보기 시작하고,
#   결국 「전부 자동」과 같은 결과가 됩니다. 사람은 갈아 넣고 효과는 0인 최악의 결말이죠.
#   나머지 30%는 휴가·회의·급한 건을 위한 여유분입니다.
# - **그중 가장 낮은 것**: 문턱이 낮을수록 사람이 더 많이 보고, 자동 처리로 새 나가는
#   위험 금액이 줄어듭니다. 즉 용량이 허락하는 한 최대한 낮게 미는 것이 이득입니다.
#
# 수식으로 쓰면 이렇습니다.
#
# $$\text{capacity} = R \times W, \qquad \text{load}(t) = m \cdot \bigl|\{a \in A : a \ge t\}\bigr|$$
#
# $$t^{*} = \min\ \Bigl\{\, t \;\Bigm|\; \frac{\text{load}(t)}{\text{capacity}} \le 0.70 \,\Bigr\}$$
#
# 여기서 $R$은 담당자 수, $W$는 하루 근무 분, $m$은 1건 검토 분, $A$는 하루치 요청 금액 집합입니다.
#
# 그리고 자동 처리로 나가는 노출 위험액은
#
# $$\text{risk}(t) = \varepsilon \sum_{a < t} a$$
#
# $\varepsilon$은 자동 처리 오류율입니다. $\text{load}$는 $t$에 대해 단조 감소,
# $\text{risk}$는 단조 증가 — 그래서 **70% 선에 딱 붙는 지점**이 최적입니다.

# %%
import random

import plotly.graph_objects as go


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


REVIEW_MINUTES = 3        # 한 건 검토에 걸리는 시간 (m)
REVIEWERS = 2             # 검토 담당자 수 (R)
WORK_MINUTES = 8 * 60     # 하루 근무 시간 (W)
ERROR_RATE = 0.04         # 자동 처리 중 잘못된 비율 (ε)
TARGET = 0.70             # 용량 대비 상한

CAPACITY = REVIEWERS * WORK_MINUTES

print(f"하루 용량 = {REVIEWERS}명 x {WORK_MINUTES}분 = {CAPACITY}분")
print(f"= 최대 {CAPACITY // REVIEW_MINUTES}건 (100%) / {int(CAPACITY * TARGET) // REVIEW_MINUTES}건 (70%)")
# 출력: 하루 용량 = 2명 x 480분 = 960분
# 출력: = 최대 320건 (100%) / 224건 (70%)

# %% [markdown]
# ## 1단계 — 하루치 요청 분포를 만든다
#
# 환불 금액은 소액이 압도적으로 많고 고액이 드뭅니다. 로그정규분포가 이 모양에 맞습니다.
# 시드를 고정해 매번 같은 하루를 봅니다.
#
# $$\ln A \sim \mathcal{N}(\mu=10.4,\ \sigma=1.15)$$

# %%
def day(seed=7, n=1200):
    """하루치 환불 요청. 금액은 소액이 많고 고액이 드물다."""
    rng = random.Random(seed)
    return [int(rng.lognormvariate(10.4, 1.15)) for _ in range(n)]


amounts = day()
amounts_sorted = sorted(amounts, reverse=True)

print(f"요청 {len(amounts)}건, 합계 {sum(amounts):,}원")
print(f"최소 {min(amounts):,}원 / 중앙값 {amounts_sorted[len(amounts) // 2]:,}원 / 최대 {max(amounts):,}원")
# 출력: 요청 1200건, 합계 73,893,625원
# 출력: 최소 802원 / 중앙값 31,951원 / 최대 1,863,427원

# %% [markdown]
# ## 2단계 — 문턱 하나를 평가하는 함수
#
# 문턱 $t$가 주어지면 요청은 둘로 갈립니다.
# $t$ 이상은 사람이 보고(검토 시간 발생), $t$ 미만은 자동 처리(노출 위험액 발생).

# %%
def evaluate(amounts, threshold):
    reviewed = [a for a in amounts if a >= threshold]
    auto = [a for a in amounts if a < threshold]
    load = len(reviewed) * REVIEW_MINUTES
    risk = sum(auto) * ERROR_RATE
    return len(reviewed), load, CAPACITY, risk


n, load, cap, risk = evaluate(amounts, 100_000)
print(f"문턱 100,000원 → 검토 {n}건, {load}분, 용량 대비 {load / cap:.0%}, 위험액 {risk:,.0f}원")
# 출력: 문턱 100,000원 → 검토 183건, 549분, 용량 대비 57%, 위험액 1,306,610원

# %% [markdown]
# ## 3단계 — 책에 나온 후보 문턱들을 나란히 놓는다
#
# 양 끝(「전부 사람」/「전부 자동」)이 왜 답이 아닌지가 이 표에서 바로 보입니다.

# %%
CANDIDATES = (0, 50_000, 100_000, 300_000, 1_000_000, 10**9)

print(f"{'문턱':>12}{'볼 건수':>10}{'검토(분)':>10}{'용량대비':>10}{'위험액':>16}  판정")
print("-" * 74)
for t in CANDIDATES:
    n, load, cap, risk = evaluate(amounts, t)
    label = "전부 사람" if t == 0 else ("전부 자동" if t == 10**9 else f"{t:,}원")
    verdict = "OK" if load / cap <= TARGET else "용량 초과"
    print(f"{label:>12}{n:>10}{load:>10}{load / cap:>9.0%}{risk:>15,.0f}원  {verdict}")
# 출력:         문턱   볼 건수  검토(분)  용량대비          위험액  판정
# 출력: --------------------------------------------------------------------------
# 출력:    전부 사람      1200      3600     375%              0원  용량 초과
# 출력:    50,000원       412      1236     129%      672,804원  용량 초과
# 출력:   100,000원       183       549      57%    1,306,610원  OK
# 출력:   300,000원        32        96      10%    2,291,931원  OK
# 출력: 1,000,000원         1         3       0%    2,881,208원  OK
# 출력:    전부 자동         0         0       0%    2,955,745원  OK

# %% [markdown]
# 「전부 사람」은 용량의 **375%**입니다. 3.75일치 일을 하루에 밀어 넣는 셈이죠.
# 그 정책의 실제 결과는 「전부 자동」과 같습니다 — 다만 사람을 태워 가면서요.
#
# 「전부 자동」은 위험액 2,955,745원이 그대로 노출됩니다.
#
# 후보 중 70% 이내인 것은 100,000 / 300,000 / 1,000,000 / 전부 자동입니다.
# 그중 **가장 낮은** 100,000원이 답 — 위험액이 제일 작으니까요.
# 하지만 후보 목록이 성글면 답도 성글어집니다. 다음 단계에서 촘촘히 훑습니다.

# %% [markdown]
# ## 4단계 — 촘촘히 훑어 「70% 이내 중 가장 낮은 문턱」을 찾는다

# %%
GRID = list(range(0, 1_000_001, 10_000))
rows = [(t,) + evaluate(amounts, t) for t in GRID]

chosen = next(t for t, n, load, cap, risk in rows if load / cap <= TARGET)
c_n, c_load, c_cap, c_risk = evaluate(amounts, chosen)

print("문턱 10,000원 간격 탐색 (70% 경계 부근)")
for t, n, load, cap, risk in rows:
    if 50_000 <= t <= 120_000:
        mark = " <== 선택" if t == chosen else ""
        print(f"  {t:>9,}원  {n:>4}건  {load:>5}분  {load / cap:>6.1%}  위험 {risk:>11,.0f}원{mark}")

print(f"\n선택된 문턱: {chosen:,}원 "
      f"(검토 {c_n}건 / {c_load}분 / 용량 대비 {c_load / c_cap:.1%} / 위험액 {c_risk:,.0f}원)")
# 출력: 문턱 10,000원 간격 탐색 (70% 경계 부근)
# 출력:     50,000원   412건   1236분  128.8%  위험     672,804원
# 출력:     60,000원   327건    981분  102.2%  위험     859,307원
# 출력:     70,000원   287건    861분   89.7%  위험     963,331원
# 출력:     80,000원   241건    723분   75.3%  위험   1,099,369원
# 출력:     90,000원   206건    618분   64.4%  위험   1,218,650원 <== 선택
# 출력:    100,000원   183건    549분   57.2%  위험   1,306,610원
# 출력:    110,000원   168건    504분   52.5%  위험   1,368,851원
# 출력:    120,000원   147건    441분   45.9%  위험   1,465,566원
# 출력:
# 출력: 선택된 문턱: 90,000원 (검토 206건 / 618분 / 용량 대비 64.4% / 위험액 1,218,650원)

# %% [markdown]
# 후보를 촘촘히 하니 100,000원이 아니라 **90,000원**이 답입니다.
# 위험액이 1,306,610원 → 1,218,650원으로 약 88,000원 줄었습니다. 같은 인원으로요.
#
# ### 격자 없이 정확히 구하기
#
# 격자 탐색은 어차피 근사입니다. 70% 안에서 볼 수 있는 최대 건수는
#
# $$k = \left\lfloor \frac{0.70 \times \text{capacity}}{m} \right\rfloor = \left\lfloor \frac{0.70 \times 960}{3} \right\rfloor = 224$$
#
# 이므로, 금액을 내림차순 정렬해 **225번째로 큰 금액보다 1원 많은 값**이 가능한 최저 문턱입니다.

# %%
k = int(TARGET * CAPACITY) // REVIEW_MINUTES
exact = amounts_sorted[k] + 1          # k번째까지만 사람이 본다
e_n, e_load, e_cap, e_risk = evaluate(amounts, exact)

print(f"70% 이내 최대 검토 건수 k = {k}건")
print(f"정확한 최저 문턱 = {exact:,}원")
print(f"  → 검토 {e_n}건 / {e_load}분 / 용량 대비 {e_load / e_cap:.1%} / 위험액 {e_risk:,.0f}원")
print(f"격자(90,000원) 대비 위험액 {c_risk - e_risk:,.0f}원 절감")
# 출력: 70% 이내 최대 검토 건수 k = 224건
# 출력: 정확한 최저 문턱 = 84,954원
# 출력:   → 검토 224건 / 672분 / 용량 대비 70.0% / 위험액 1,155,666원
# 출력: 격자(90,000원) 대비 위험액 62,984원 절감

# %% [markdown]
# ## 5단계 — 「취향으로 정하면」 어떻게 되는가
#
# 「10만 원 정도가 적당해 보인다」는 감각적 문턱과, 용량으로 계산한 문턱을 비교합니다.
# 중요한 것은 취향 문턱이 **틀렸다**가 아니라, 용량이 바뀌면 같이 움직여야 하는데
# 취향은 안 움직인다는 점입니다.

# %%
print(f"{'담당자 수':>10}{'용량(분)':>10}{'70% 건수':>10}{'용량기반 문턱':>16}{'취향 문턱(10만)':>18}")
print("-" * 66)
for r in (1, 2, 3, 5):
    cap_r = r * WORK_MINUTES
    k_r = int(TARGET * cap_r) // REVIEW_MINUTES
    t_r = amounts_sorted[k_r] + 1 if k_r < len(amounts_sorted) else 1
    n_fix, load_fix, _, _ = evaluate(amounts, 100_000)
    print(f"{r:>10}{cap_r:>10}{k_r:>10}{t_r:>15,}원{load_fix / cap_r:>16.0%}")
# 출력:      담당자 수    용량(분)   70% 건수      용량기반 문턱     취향 문턱(10만)
# 출력: ------------------------------------------------------------------
# 출력:         1       480       112        143,864원             114%
# 출력:         2       960       224         84,954원              57%
# 출력:         3      1440       335         58,789원              38%
# 출력:         5      2400       560         34,668원              23%

# %% [markdown]
# 담당자가 1명이면 「10만 원 고정」 정책은 용량의 **114%** — 큐가 쌓입니다.
# 담당자가 5명이면 용량의 23%만 쓰고 놀립니다. 문턱을 34,668원까지 내릴 수 있었는데
# 잡을 수 있었던 위험을 그냥 흘려보내는 거죠.
#
# 같은 문턱이 인원에 따라 과부하도 되고 낭비도 됩니다.
# 그래서 문턱은 숫자를 고르는 일이 아니라 **용량에 연결하는 일**입니다.

# %% [markdown]
# ## 6단계 — 문턱 대비 용량 사용률 / 노출 위험액 곡선
#
# 두 곡선이 반대로 움직입니다. 70% 가로선과 만나는 가장 왼쪽 지점이 답입니다.

# %%
xs = list(range(0, 300_001, 2_000))
util = []
risks = []
for t in xs:
    _, load, cap, risk = evaluate(amounts, t)
    util.append(load / cap * 100)
    risks.append(risk)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=xs, y=util, name="용량 사용률 (%)", mode="lines",
    line=dict(color="#2E86DE", width=3), yaxis="y",
    hovertemplate="문턱 %{x:,}원<br>사용률 %{y:.1f}%<extra></extra>"))
fig.add_trace(go.Scatter(
    x=xs, y=risks, name="자동 처리 노출 위험액 (원)", mode="lines",
    line=dict(color="#E17055", width=3, dash="dot"), yaxis="y2",
    hovertemplate="문턱 %{x:,}원<br>위험액 %{y:,.0f}원<extra></extra>"))

fig.add_hline(y=TARGET * 100, line=dict(color="#B33771", width=2, dash="dash"),
              annotation_text="용량 70% 상한", annotation_position="top right")
fig.add_vline(x=exact, line=dict(color="#10AC84", width=2),
              annotation_text=f"선택 문턱 {exact:,}원", annotation_position="top left")
fig.add_vline(x=100_000, line=dict(color="#8395A7", width=1, dash="dot"),
              annotation_text="취향 문턱 100,000원", annotation_position="bottom right")

fig.update_layout(
    title="승인 문턱: 용량 사용률과 노출 위험액의 맞교환",
    xaxis=dict(title="승인 문턱 (원)", tickformat=","),
    yaxis=dict(title="용량 사용률 (%)", range=[0, 200], color="#2E86DE"),
    yaxis2=dict(title="노출 위험액 (원)", overlaying="y", side="right",
                tickformat=",", color="#E17055"),
    legend=dict(orientation="h", y=-0.2),
    template="plotly_white", width=980, height=560,
)

_show(fig)
fig.write_image("expy.png", scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# | 정하는 방식 | 문턱 | 용량 대비 | 노출 위험액 |
# |---|---|---|---|
# | 전부 사람 | 0원 | 375% | 0원 (실제로는 붕괴) |
# | 취향 | 100,000원 | 57% | 1,306,610원 |
# | **용량** | **84,954원** | **70.0%** | **1,155,666원** |
# | 전부 자동 | ∞ | 0% | 2,955,745원 |
#
# - 문턱은 **취향이 아니라 용량**으로 정한다.
# - 규칙: **검토 시간이 용량의 70%를 넘지 않는 문턱 중 가장 낮은 것**.
# - 70% 상한은 큐 붕괴를 막고, 남은 30%는 휴가·회의·급한 건의 여유분이다.
# - 「가장 낮은 것」인 이유는 용량이 허락하는 만큼 최대한 많이 잡는 것이 이득이기 때문이다.
# - 인원·검토 시간·요청 분포가 바뀌면 문턱도 다시 계산해야 한다. 상수로 박아 두면 취향으로 되돌아간다.
# - 금액만이 유일한 축은 아니다. 신규 고객·반복 환불·이상 패턴을 섞으면 같은 용량으로 더 잡는다.
#   다만 시작은 금액이 좋다. 계산되고, 설명되고, 감사도 통과한다.
