# %% [markdown]
# # 층별 상한은 곱해진다 — 전역 예산이 필요한 이유
#
# **질문**: 층마다 상한을 둬도 안전하지 않은 이유는 무엇인가?
#
# **답**: 곱하면 커진다. 전역 예산을 하나 더 두고 모든 층이 보게 해야 한다.
#
# 층이 $L$개이고 각 층의 상한이 $c_1, c_2, \dots, c_L$일 때
# 최악의 총 호출 수는 **합이 아니라 곱**이다.
#
# $$N_{\max} = \prod_{k=1}^{L} c_k$$
#
# 층별 리뷰는 $c_k$ 하나씩만 본다. 아무도 $\prod$ 을 계산하지 않는다.

# %%
# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# 실행: python3 expy.py  (또는 VSCode에서 셀 단위 실행)

import math
import os

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


COST_PER_CALL = 1.8  # 호출 1회당 원
print(f"호출 단가 {COST_PER_CALL}원")
# 출력: 호출 단가 1.8원

# %% [markdown]
# ## 1단계 — 세 층의 상한을 곱해 본다
#
# 바깥 루프 5회, 안쪽 루프 4회, 도구 재시도 3회.
# 각 층만 보면 "다섯 번, 네 번, 세 번"이라 아주 온건해 보인다.

# %%
def layer_counts(outer, inner, tool):
    """각 층이 «자기 상한»만 볼 때의 누적 최대 호출 수."""
    return outer, outer * inner, outer * inner * tool


for name, (o, i, t) in [
    ("보수적", (5, 4, 3)),
    ("살짝 넉넉", (8, 6, 5)),
]:
    lo, li, lt = layer_counts(o, i, t)
    print(f"{name:<8} 상한 {o}·{i}·{t}  누적 {lo:>3} → {li:>3} → {lt:>3}회"
          f"   합 {o+i+t:>3}회   곱 {lt:>3}회   {lt * COST_PER_CALL:>7,.0f}원")
# 출력: 보수적      상한 5·4·3  누적   5 →  20 →  60회   합  12회   곱  60회      108원
# 출력: 살짝 넉넉    상한 8·6·5  누적   8 →  48 → 240회   합  19회   곱 240회      432원

# %% [markdown]
# 상한을 층마다 "조금씩만" 올렸는데(5→8, 4→6, 3→5)
# 합은 12→19로 1.6배지만 **곱은 60→240으로 4배**다.
#
# 직관이 더하기로 굴러가는 동안 시스템은 곱하기로 자란다.
# 그래서 각 층 코드를 따로 리뷰하면 아무 문제가 없어 보인다.

# %%
# 층 상한을 하나씩만 올려 보면 — 어느 층을 건드려도 곱이 튄다
BASE = (5, 4, 3)
print(f"{'바깥':>4} {'안쪽':>4} {'도구':>4} {'총 호출':>8} {'값':>9} {'기준 대비':>9}")
base_n = math.prod(BASE)
for combo in [(5, 4, 3), (6, 4, 3), (5, 5, 3), (5, 4, 4), (6, 5, 4), (8, 6, 5)]:
    n = math.prod(combo)
    print(f"{combo[0]:>4} {combo[1]:>4} {combo[2]:>4} {n:>8} "
          f"{n * COST_PER_CALL:>8,.0f}원 {n / base_n:>8.1f}x")
# 출력:   바깥   안쪽   도구    총 호출        값     기준 대비
# 출력:    5    4    3       60      108원      1.0x
# 출력:    6    4    3       72      130원      1.2x
# 출력:    5    5    3       75      135원      1.2x
# 출력:    5    4    4       80      144원      1.3x
# 출력:    6    5    4      120      216원      2.0x
# 출력:    8    6    5      240      432원      4.0x

# %% [markdown]
# ## 2단계 — 층 상한만 있는 루프를 실제로 돌려 본다
#
# 중첩 루프를 그대로 실행해서 호출이 몇 번 일어나는지 센다.
# 각 층은 자기 상한만 안다. 서로의 존재를 모른다.

# %%
def run_layered_only(outer, inner, tool):
    """전역 예산 없음. 각 층이 자기 상한까지 다 돈다."""
    calls = 0
    for _ in range(outer):
        for _ in range(inner):
            for _ in range(tool):
                calls += 1
    return calls, calls * COST_PER_CALL, "층 상한 소진"


calls, cost, why = run_layered_only(8, 6, 5)
print(f"층 상한만: {calls}회, {cost:,.0f}원, 끝난 이유 = {why}")
# 출력: 층 상한만: 240회, 432원, 끝난 이유 = 층 상한 소진

# %% [markdown]
# ## 3단계 — 전역 예산을 «상태»에 두고 모든 층이 본다
#
# 핵심은 두 가지다.
#
# 1. 예산 카운터가 **하나**뿐이고 모든 층이 같은 것을 읽는다.
# 2. 그 카운터는 전역 변수가 아니라 **상태(state)** 에 있다.
#    전역 변수면 프로세스가 재시작될 때 리셋되어 예산이 부활한다.

# %%
class Budget:
    """모든 층이 공유하는 전역 예산. 상태 객체로 들고 다닌다."""

    def __init__(self, limit_won):
        self.limit = limit_won
        self.spent = 0.0

    def can_spend(self):
        return self.spent + COST_PER_CALL <= self.limit

    def charge(self):
        self.spent += COST_PER_CALL


def run_with_global(outer, inner, tool, budget_won):
    """층 상한 + 전역 예산. 모든 층이 budget 을 본다."""
    b = Budget(budget_won)
    calls = 0
    for _ in range(outer):
        if not b.can_spend():
            break
        for _ in range(inner):
            if not b.can_spend():
                break
            for _ in range(tool):
                if not b.can_spend():
                    break
                b.charge()
                calls += 1
    why = "전역 예산" if not b.can_spend() else "층 상한 소진"
    return calls, b.spent, why


for budget in (100, 200, 300, 500, 1000):
    c, s, why = run_with_global(8, 6, 5, budget)
    print(f"전역 예산 {budget:>5}원 → {c:>3}회 호출, {s:>6.1f}원 사용, 끝난 이유 = {why}")
# 출력: 전역 예산   100원 →  55회 호출,   99.0원 사용, 끝난 이유 = 전역 예산
# 출력: 전역 예산   200원 → 111회 호출,  199.8원 사용, 끝난 이유 = 전역 예산
# 출력: 전역 예산   300원 → 166회 호출,  298.8원 사용, 끝난 이유 = 전역 예산
# 출력: 전역 예산   500원 → 240회 호출,  432.0원 사용, 끝난 이유 = 층 상한 소진
# 출력: 전역 예산  1000원 → 240회 호출,  432.0원 사용, 끝난 이유 = 층 상한 소진

# %% [markdown]
# 예산 500원부터는 층 상한이 먼저 걸린다. 즉 **전역 예산이 무력해진 상태**다.
#
# 요령: 전역 예산이 층 상한보다 **먼저** 걸리게 잡는다.
# 그러면 층 상한은 «안전망»이 되고 전역 예산이 «실질 제어»가 된다.
#
# $$\text{budget} < c_{\text{outer}} \cdot c_{\text{inner}} \cdot c_{\text{tool}} \cdot \text{unit}$$

# %%
LAYER_MAX_COST = 8 * 6 * 5 * COST_PER_CALL
for budget in (100, 300, 432, 500):
    role = "실질 제어" if budget < LAYER_MAX_COST else "무력 (층 상한이 먼저)"
    print(f"예산 {budget:>4}원 vs 층 상한 곱 {LAYER_MAX_COST:.0f}원 → {role}")
# 출력: 예산  100원 vs 층 상한 곱 432원 → 실질 제어
# 출력: 예산  300원 vs 층 상한 곱 432원 → 실질 제어
# 출력: 예산  432원 vs 층 상한 곱 432원 → 무력 (층 상한이 먼저)
# 출력: 예산  500원 vs 층 상한 곱 432원 → 무력 (층 상한이 먼저)

# %% [markdown]
# ## 4단계 — 전역 예산이 전역 «변수»면 재개할 때 리셋된다
#
# 20장이 반복해 말하는 함정. 예산을 모듈 전역에 두면
# 워커가 죽었다 살아날 때마다 예산이 새로 채워진다.
# 세 번 재시작하면 예산도 세 배가 된다.

# %%
_MODULE_SPENT = 0.0  # 나쁜 예: 전역 변수


def resume_global_var(times, budget_won):
    """재개할 때마다 프로세스가 새로 뜬다고 가정 — 전역이 리셋된다."""
    global _MODULE_SPENT
    total = 0.0
    for _ in range(times):
        _MODULE_SPENT = 0.0            # 프로세스 재시작 = 리셋
        while _MODULE_SPENT + COST_PER_CALL <= budget_won:
            _MODULE_SPENT += COST_PER_CALL
        total += _MODULE_SPENT
    return total


def resume_stateful(times, budget_won):
    """좋은 예: 예산이 체크포인트된 상태에 있어 재개해도 이어진다."""
    b = Budget(budget_won)             # 상태에서 복원된 것으로 간주
    for _ in range(times):
        while b.can_spend():
            b.charge()
    return b.spent


print(f"3번 재개 — 전역 변수: {resume_global_var(3, 300):.1f}원 (예산 300원인데!)")
print(f"3번 재개 — 상태 보관: {resume_stateful(3, 300):.1f}원")
# 출력: 3번 재개 — 전역 변수: 896.4원 (예산 300원인데!)
# 출력: 3번 재개 — 상태 보관: 298.8원

# %% [markdown]
# ## 5단계 — 그래프로 대비: 곱셈 폭발 vs 전역 캡의 평탄화

# %%
fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=("층 상한만 — 곱해서 폭발", "전역 예산 캡 — 평탄화"),
)

# 왼쪽: 층 수를 늘릴 때 합 vs 곱
per_layer = 4
layers = list(range(1, 8))
sums = [per_layer * L for L in layers]
prods = [per_layer ** L for L in layers]

fig.add_trace(go.Scatter(x=layers, y=sums, name="직관 (합 4L)",
                         mode="lines+markers", line=dict(color="#4C78A8")),
              row=1, col=1)
fig.add_trace(go.Scatter(x=layers, y=prods, name="실제 (곱 4^L)",
                         mode="lines+markers", line=dict(color="#E45756")),
              row=1, col=1)

# 오른쪽: 층 상한을 올릴 때 실제 호출 수 — 전역 캡 유무
scale = [(3, 2, 2), (4, 3, 2), (5, 4, 3), (6, 5, 4), (7, 5, 4), (8, 6, 5)]
labels = [f"{o}·{i}·{t}" for o, i, t in scale]
no_cap = [math.prod(c) for c in scale]
cap150 = [run_with_global(*c, 150)[0] for c in scale]
cap60 = [run_with_global(*c, 60)[0] for c in scale]

fig.add_trace(go.Scatter(x=labels, y=no_cap, name="전역 캡 없음",
                         mode="lines+markers", line=dict(color="#E45756")),
              row=1, col=2)
fig.add_trace(go.Scatter(x=labels, y=cap150, name="전역 예산 150원",
                         mode="lines+markers", line=dict(color="#54A24B")),
              row=1, col=2)
fig.add_trace(go.Scatter(x=labels, y=cap60, name="전역 예산 60원",
                         mode="lines+markers", line=dict(color="#72B7B2")),
              row=1, col=2)

fig.update_yaxes(type="log", title_text="최대 호출 수 (로그)", row=1, col=1)
fig.update_xaxes(title_text="층 수 L (층당 상한 4)", row=1, col=1)
fig.update_yaxes(title_text="실제 호출 수", row=1, col=2)
fig.update_xaxes(title_text="층별 상한 (바깥·안쪽·도구)", row=1, col=2)
fig.update_layout(
    title="층마다 상한을 둬도 안전하지 않은 이유 — 곱하면 커진다",
    height=460, width=1000, template="plotly_white",
)

_show(fig)
fig.write_image(os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png"),
                scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# | | 층별 상한만 | 층별 상한 + 전역 예산 |
# |---|---|---|
# | 최악 호출 수 | $\prod c_k$ — 층이 늘수록 지수적 | $\lfloor \text{budget} / \text{unit} \rfloor$ — 상수 |
# | 층 하나 완화 시 | 전체가 배수로 튐 | 변화 없음 (캡이 먼저 걸림) |
# | 코드 리뷰로 발견되나 | 아니오 (각 층은 다 합리적) | 예 (숫자가 한 곳에 있음) |
# | 역할 | 안전망 | 실질 제어 |
#
# - 층별 상한은 **필요하지만 충분하지 않다**. 없애라는 얘기가 아니다.
# - 전역 예산은 모든 층이 **같은 카운터**를 보게 해야 의미가 있다.
# - 그 카운터는 전역 변수가 아니라 **상태**에 둔다. 안 그러면 재개할 때 리셋된다.
# - 끝난 이유(`상한` / `예산` / `정체`)를 상태에 남긴다. 대응이 각각 다르다.
