# %% [markdown]
# # 여러 번 돌려 표를 세는 방식이 잘 갈라내는 이유
#
# **카드**: 여러 번 돌려 표를 세는 방식이 잘 갈라내는 이유는 무엇인가?
# → **지어낸 것은 매번 다르게 지어내기 때문이다. 반복 출현 횟수가 사실성의 신호가 된다.**
#
# 핵심 비대칭:
#
# - **참 트리플**은 원문에 닻이 있다. 실행마다 확률 $p$(높음)로 같은 트리플이 재출현한다.
#   $k$번 중 $m$번 이상 나올 확률은 이항분포로
#   $$P(\text{표} \ge m) = \sum_{j=m}^{k} \binom{k}{j} p^j (1-p)^{k-j}$$
# - **지어낸 트리플**은 닻이 없다. 넓은 후보 공간에서 매번 새로 뽑히므로,
#   특정 거짓이 한 번 나올 확률을 $q$(작음)라 하면 $k$번 연속 같은 거짓이 나올 확률은
#   대략 $q^k$ — **지수적으로 사라진다.**
#
# 그래서 "몇 번 나왔나"(표 수)가 참/거짓을 가르는 신호가 된다.
# (self-consistency, Wang et al. 2022, arXiv:2203.11171)

# %%
# 필요 패키지: plotly, kaleido (표준 라이브러리 외에는 시각화에만 필요)
import random
from collections import Counter

def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass

random.seed(20260814)

# %% [markdown]
# ## 1단계 — 가짜 추출기 시뮬레이션
#
# 15장 `extractor.py`와 같은 취지의 장난감 모델을 만든다.
#
# - **참 트리플 40개**: 실행마다 확률 $p = 0.85$로 출력에 포함된다 (원문에 닻이 있으니 재출현).
# - **지어낸 트리플**: 실행마다 8개를 후보 공간(주어 20 × 술어 10 × 값 30 = 6,000가지)에서
#   무작위로 새로 뽑는다 (닻이 없으니 매번 다르게 지어냄).

# %%
P_TRUE = 0.85     # 참 트리플이 한 번의 실행에서 재출현할 확률
N_HALL = 8        # 실행마다 지어내는 트리플 수
K_RUNS = 3        # 반복 실행 횟수

TRUE_FACTS = {(f"회사{i:02d}", "체결", f"C-2025-{100+i}") for i in range(20)} | \
             {(f"회사{i:02d}", "담당", f"직원{i:02d}") for i in range(20)}   # 참 40개

SUBJECTS = [f"회사{i:02d}" for i in range(20)]
FAKE_PREDS = ["업종", "규모", "모회사", "협업", "매출", "설립", "지분", "제휴", "평가", "등급"]
FAKE_VALS = [f"값{i:02d}" for i in range(30)]

def run_extractor():
    """한 번의 추출 실행: 참은 p로 재출현, 거짓은 매번 새로 지어냄."""
    out = {t for t in TRUE_FACTS if random.random() < P_TRUE}
    for _ in range(N_HALL):
        out.add((random.choice(SUBJECTS), random.choice(FAKE_PREDS), random.choice(FAKE_VALS)))
    return out

runs = [run_extractor() for _ in range(K_RUNS)]
votes = Counter()
for r in runs:
    for t in r:
        votes[t] += 1

n_true_seen = sum(1 for t in votes if t in TRUE_FACTS)
n_hall_seen = sum(1 for t in votes if t not in TRUE_FACTS)
print(f"3회 실행에서 관측된 고유 트리플: 참 {n_true_seen}개, 지어낸 것 {n_hall_seen}개")
# 출력: 3회 실행에서 관측된 고유 트리플: 참 40개, 지어낸 것 24개

# %% [markdown]
# ## 2단계 — 표 수 분포: 참은 3표에 몰리고 거짓은 1표에 몰린다
#
# 기대값으로 확인하면: 참 트리플이 3/3표를 받을 확률은 $0.85^3 \approx 0.614$.
# 반면 특정 거짓 트리플이 두 번 이상 나오려면 6,000가지 공간에서 같은 조합이
# 다시 뽑혀야 하므로 거의 일어나지 않는다.

# %%
dist = {"참": Counter(), "거짓": Counter()}
for t, v in votes.items():
    dist["참" if t in TRUE_FACTS else "거짓"][v] += 1

print(f"{'표 수':>4} {'참':>6} {'거짓':>6}")
for v in (1, 2, 3):
    print(f"{v:>3}/3 {dist['참'][v]:>6} {dist['거짓'][v]:>6}")
# 출력:  표 수      참     거짓
# 출력:    1/3      0     24
# 출력:    2/3     14      0
# 출력:    3/3     26      0
# → 지어낸 24개는 전부 1표. 같은 거짓이 두 번 나온 경우가 한 번도 없다.
# → 참 40개는 전부 2표 이상 — 원문에 닻이 있으니 반복해서 재출현한다.

# %% [markdown]
# ## 3단계 — 자기 보고 확신도는 갈라내지 못한다
#
# 모델의 자기 보고 확신도를 흉내 낸다. 15장 예제처럼 **거짓에도 높은 값**을 준다:
# 참은 $\mathcal{N}(0.90, 0.04)$, 거짓은 $\mathcal{N}(0.88, 0.04)$ — 분포가 겹친다.

# %%
self_reported = {}
for t in votes:
    mu = 0.90 if t in TRUE_FACTS else 0.88
    self_reported[t] = min(0.99, max(0.5, random.gauss(mu, 0.04)))

def eval_rule(picked):
    tp = len(picked & TRUE_FACTS)
    prec = tp / len(picked) if picked else 0.0
    rec = tp / len(TRUE_FACTS)
    return prec, rec, len(picked)

rules = {
    "자기 보고 ≥ 0.90": {t for t in votes if self_reported[t] >= 0.90},
    "표 ≥ 1/3 (전부)":   {t for t in votes if votes[t] >= 1},
    "표 ≥ 2/3":          {t for t in votes if votes[t] >= 2},
    "표 = 3/3":          {t for t in votes if votes[t] >= 3},
}

results = {}
print(f"{'기준':<18} {'정밀도':>7} {'재현율':>7} {'뽑은 수':>7}")
for name, picked in rules.items():
    prec, rec, n = eval_rule(picked)
    results[name] = (prec, rec)
    print(f"{name:<18} {prec:>7.3f} {rec:>7.3f} {n:>7}")
# 출력: 기준                   정밀도     재현율    뽑은 수
# 출력: 자기 보고 ≥ 0.90       0.625   0.375      24
# 출력: 표 ≥ 1/3 (전부)        0.625   1.000      64
# 출력: 표 ≥ 2/3               1.000   1.000      40
# 출력: 표 = 3/3               1.000   0.650      26
#
# → 자기 보고: 정밀도 0.625 — 거짓이 그대로 섞여 들어온다 (참과 분포가 겹치므로).
# → 표 ≥ 2/3: 이 시뮬레이션에서는 정밀도·재현율 모두 1.000 — 깔끔하게 갈라진다.
# → 표 = 3/3: 정밀도는 1.000이지만 재현율 0.650 — "확실한 것만 고르는" 쪽으로 치우친다.
# → 대가는 비용: 3번 돌리면 API 비용도 3배. 그래서 애매한 것에만 쓴다.

# %% [markdown]
# ## 4단계 — 시각화
#
# 왼쪽: 표 수 분포 — 지어낸 것(주황)은 1표에 몰리고, 참(파랑)은 3표에 몰린다.
# 오른쪽: 판별 기준별 정밀도·재현율 — 표 세기(≥2/3)가 자기 보고보다 훨씬 잘 갈라낸다.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

C_TRUE, C_HALL = "#2a78d6", "#eb6834"   # 참=파랑, 거짓=주황
C_PREC, C_REC = "#1baf7a", "#eda100"    # 정밀도=아쿠아, 재현율=노랑

fig = make_subplots(
    rows=1, cols=2, horizontal_spacing=0.14,
    subplot_titles=("표 수 분포 (3회 반복)", "판별 기준별 정밀도·재현율"),
)

xs = ["1/3", "2/3", "3/3"]
fig.add_trace(go.Bar(name="참 트리플", x=xs, y=[dist["참"][v] for v in (1, 2, 3)],
                     marker_color=C_TRUE, text=[dist["참"][v] for v in (1, 2, 3)],
                     textposition="outside"), row=1, col=1)
fig.add_trace(go.Bar(name="지어낸 트리플", x=xs, y=[dist["거짓"][v] for v in (1, 2, 3)],
                     marker_color=C_HALL, text=[dist["거짓"][v] for v in (1, 2, 3)],
                     textposition="outside"), row=1, col=1)

rule_names = list(results)
fig.add_trace(go.Bar(name="정밀도", x=rule_names, y=[results[r][0] for r in rule_names],
                     marker_color=C_PREC, text=[f"{results[r][0]:.2f}" for r in rule_names],
                     textposition="outside"), row=1, col=2)
fig.add_trace(go.Bar(name="재현율", x=rule_names, y=[results[r][1] for r in rule_names],
                     marker_color=C_REC, text=[f"{results[r][1]:.2f}" for r in rule_names],
                     textposition="outside"), row=1, col=2)

fig.update_layout(
    title="지어낸 것은 매번 다르게 지어낸다 — 반복 출현 횟수가 사실성의 신호",
    barmode="group", bargap=0.3, bargroupgap=0.08,
    template="plotly_white", width=1060, height=460,
    font=dict(size=13), legend=dict(orientation="h", y=-0.18),
    paper_bgcolor="#fcfcfb", plot_bgcolor="#fcfcfb",
)
fig.update_yaxes(title_text="트리플 수", row=1, col=1)
fig.update_yaxes(title_text="값", range=[0, 1.12], row=1, col=2)

import os
_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else "."
fig.write_image(os.path.join(_here, "expy.png"), scale=2)
_show(fig)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# - 참 트리플은 원문이라는 고정점이 있어 실행마다 **수렴**한다 ($0.85^3 \approx 0.61$이 3/3표).
# - 지어낸 트리플은 넓은 후보 공간에서 매번 새로 뽑혀 **흩어진다** — 이 시뮬레이션에서
#   거짓 24개 전부가 1표에 그쳤고, 참 40개는 전부 2표 이상이었다.
# - 자기 보고 확신도는 거짓에도 높은 값을 주므로 임계값을 어디에 두어도 못 가른다.
# - 표 세기는 정밀도를 크게 올리지만 재현율을 깎고(3/3 기준) 비용이 반복 횟수에 비례한다.
#   → 책의 절충: 1차는 싼 근거 검사, 표 세기는 **애매한 소수에만**.
