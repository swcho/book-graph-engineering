# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# 표준 라이브러리만으로도 시뮬레이션 셀까지는 동작한다. 시각화 셀만 plotly가 필요하다.

# %% [markdown]
# # `ex5_debug_state.py` — '정리' 노드의 비용은 어떻게 변하는가
#
# **질문**: `ex5_debug_state.py`에서 '정리' 노드의 비용은 어떻게 변하는가?
#
# **답**: `20 + 회차 × 15`로 회차가 늘수록 비싸진다. 실제로 흔한 패턴이다.
#
# 원본 코드에서 해당 부분만 다시 보면 이렇다.
#
# ```python
# def 정리(s):
#     # 회차가 늘수록 비싸진다 — 실제로 흔한 패턴
#     cost = 20 + s["회차"] * 15
#     return {"쓴돈": cost, "기록": [f"정리 {cost}"]}
# ```
#
# 여기서 `회차`는 `Annotated[int, operator.add]` 리듀서를 달고 있어서 `검색` 노드가
# 매번 `+1`씩 누적한다. 즉 `정리`가 보는 `s["회차"]`는 **지금까지 돈 루프 횟수**다.
# 비용이 상수가 아니라 **회차에 비례해 커지는 값**이라는 게 이 예제의 핵심이다.
#
# 이 노트북은 LangGraph 없이 그 루프를 순수 파이썬으로 재현해서
# (1) 회차별 누적 비용, (2) 두 종료 조건 중 무엇이 먼저 걸리는지,
# (3) 왜 이 패턴이 위험한지를 수식과 그림으로 정리한다.

# %%
# --- 공통 헬퍼: 노트북 환경에서만 그림을 띄운다 ---
def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# 원본 ex5_debug_state.py 의 상수
BUDGET = 100        # 예산 상한
MAX_ROUND = 4       # 회차 상한
SEARCH_COST = 30    # 검색 노드 비용 (고정)
BASE = 20           # 정리 노드 기본 비용
SLOPE = 15          # 정리 노드 회차당 증가분 (기울기)

print(f"예산 {BUDGET}, 회차 상한 {MAX_ROUND}")
print(f"검색 비용 {SEARCH_COST} (고정), 정리 비용 = {BASE} + 회차 x {SLOPE} (가변)")

# 출력:
# 예산 100, 회차 상한 4
# 검색 비용 30 (고정), 정리 비용 = 20 + 회차 x 15 (가변)

# %% [markdown]
# ## 1. 루프를 순수 파이썬으로 재현
#
# 원본 그래프의 구조는 이렇다.
#
# ```
# START → 검색 → 정리 → route() ─┬→ 검색 (다시)
#                                └→ END
# ```
#
# `route()`의 종료 조건은 **두 가지**다.
#
# ```python
# def route(s):
#     if s["쓴돈"] >= BUDGET:      # (A) 예산 상한
#         return END
#     return END if s["회차"] >= 4 else "검색"   # (B) 회차 상한
# ```
#
# 한 회차(= 하나의 루프 반복)에서 일어나는 일:
#
# 1. `검색`이 `쓴돈 += 30`, `회차 += 1`
# 2. `정리`가 `쓴돈 += 20 + 회차 × 15` — 이때 `회차`는 방금 1 늘어난 값
# 3. `route()`가 갱신된 상태를 보고 계속할지 끝낼지 정한다

# %%
END = "END"


def simulate(budget=BUDGET, max_round=MAX_ROUND, base=BASE, slope=SLOPE,
             search_cost=SEARCH_COST, hard_cap=200):
    """ex5_debug_state.py 의 검색 → 정리 → route() 루프를 그대로 재현한다.

    반환: (회차별 기록 리스트, 종료를 유발한 조건 이름)
    """
    쓴돈, 회차 = 0, 0
    rows = []
    while True:
        # --- 검색 노드 ---
        쓴돈 += search_cost
        회차 += 1
        # --- 정리 노드 ---
        cost = base + 회차 * slope
        쓴돈 += cost
        rows.append({"회차": 회차, "검색": search_cost, "정리": cost, "누적": 쓴돈})
        # --- route() ---
        if 쓴돈 >= budget:
            return rows, "예산"
        if 회차 >= max_round:
            return rows, "회차"
        if 회차 >= hard_cap:            # 안전장치 (원본에는 없음)
            return rows, "무한"


rows, reason = simulate()

print("회차 | 검색 | 정리 | 누적 쓴돈 | route() 판단")
print("-" * 52)
for i, r in enumerate(rows):
    last = i == len(rows) - 1
    verdict = f"END ({reason} 상한)" if last else "검색 (계속)"
    print(f" {r['회차']:>3} | {r['검색']:>4} | {r['정리']:>4} | "
          f"{r['누적']:>9} | {verdict}")
print("-" * 52)
print(f"최종: 쓴돈 {rows[-1]['누적']}, 회차 {rows[-1]['회차']}, 종료 원인 = {reason} 상한")

# 출력:
# 회차 | 검색 | 정리 | 누적 쓴돈 | route() 판단
# ----------------------------------------------------
#    1 |   30 |   35 |        65 | 검색 (계속)
#    2 |   30 |   50 |       145 | END (예산 상한)
# ----------------------------------------------------
# 최종: 쓴돈 145, 회차 2, 종료 원인 = 예산 상한

# %% [markdown]
# ### 읽는 법
#
# - 1회차 `정리` 비용 = $20 + 1 \times 15 = 35$
# - 2회차 `정리` 비용 = $20 + 2 \times 15 = 50$ — 한 회차 만에 **43% 비싸졌다**
# - 누적 145로 예산 100을 넘겨서 **예산 상한(A)이 먼저 걸렸다**.
#   회차 상한 4는 구경도 못 했다.
#
# 그리고 중요한 건 넘긴 정도다. 예산은 100인데 실제로는 **145**를 썼다.
# `route()`는 *쓰고 난 뒤에* 검사하기 때문에 **45만큼 초과 지출**이 이미 확정된 상태다.
# 비용이 회차마다 커지는 패턴에서는 이 "마지막 한 걸음"이 점점 커진다.

# %%
# 마지막 한 걸음이 얼마나 크게 초과시키는가
초과 = rows[-1]["누적"] - BUDGET
마지막회차비용 = rows[-1]["검색"] + rows[-1]["정리"]
print(f"예산 {BUDGET} / 실제 {rows[-1]['누적']} → 초과 {초과} ({초과 / BUDGET:.0%})")
print(f"마지막 회차 한 번에 쓴 돈: {마지막회차비용} (검색 {rows[-1]['검색']} + 정리 {rows[-1]['정리']})")
print("route() 는 «쓴 뒤에» 검사한다. 초과분은 이미 확정이다.")

# 출력:
# 예산 100 / 실제 145 → 초과 45 (45%)
# 마지막 회차 한 번에 쓴 돈: 80 (검색 30 + 정리 50)
# route() 는 «쓴 뒤에» 검사한다. 초과분은 이미 확정이다.

# %% [markdown]
# ## 2. 왜 위험한가 — 선형이 아니라 이차로 자란다
#
# 회차 $k$의 `정리` 비용을
#
# $$c_k = 20 + 15k$$
#
# 라 두면, $n$회차까지의 누적은 등차수열의 합이다. 인덱스를 $k=0$부터 세면
#
# $$C(n)=\sum_{k=0}^{n-1}(20+15k)=20n+15\frac{n(n-1)}{2}$$
#
# 원본 코드는 `검색`이 `회차`를 먼저 1 올린 뒤 `정리`가 그 값을 보므로 실제로는
# $k=1$부터 세는 게 맞고, 그러면
#
# $$C_{\text{정리}}(n)=\sum_{k=1}^{n}(20+15k)=20n+15\frac{n(n+1)}{2}$$
#
# 인덱스를 어디서 시작하든 **$n^2$ 항이 남는다는 사실은 같다**. 이게 요점이다.
#
# 여기에 고정비 `검색` 30을 더하면 전체 누적은
#
# $$C_{\text{전체}}(n)=30n+20n+15\frac{n(n+1)}{2}=50n+\frac{15}{2}n(n+1)$$
#
# 일반화해서 기울기를 $s$, 기본비를 $b$, 검색비를 $f$라 하면
#
# $$C_{\text{전체}}(n)=(f+b)\,n+s\frac{n(n+1)}{2}=\underbrace{\frac{s}{2}n^{2}}_{\text{이차}}+\underbrace{\left(f+b+\frac{s}{2}\right)n}_{\text{일차}}$$
#
# **최고차항이 $\frac{s}{2}n^{2}$다.** 회차 상한 $n$을 두 배로 늘리면 최악 비용은
# 두 배가 아니라 **약 네 배**가 된다. 이것이 "회차 상한만 믿는" 설계가 위험한 이유다.

# %%
# 닫힌 형식(closed form)과 시뮬레이션이 같은 값을 내는지 검증
def cost_closed_form(n, base=BASE, slope=SLOPE, search_cost=SEARCH_COST):
    """n 회차까지의 전체 누적 비용 — 닫힌 형식."""
    return (search_cost + base) * n + slope * n * (n + 1) // 2


def cost_cleanup_only(n, base=BASE, slope=SLOPE):
    """n 회차까지 «정리» 노드만의 누적 비용."""
    return base * n + slope * n * (n + 1) // 2


# 예산·회차 상한을 아주 크게 잡아 순수한 성장만 관찰한다
free, _ = simulate(budget=10**9, max_round=10)

print(" n | 정리 비용 | 정리 누적 | 전체 누적 | 닫힌식 | 일치 | 증가배수")
print("-" * 66)
prev = None
for r in free:
    n = r["회차"]
    cf = cost_closed_form(n)
    ratio = "" if prev is None else f"x{r['누적'] / prev:.2f}"
    print(f"{n:>2} | {r['정리']:>9} | {cost_cleanup_only(n):>9} | "
          f"{r['누적']:>9} | {cf:>6} | {'O' if cf == r['누적'] else 'X':^4} | {ratio:>8}")
    prev = r["누적"]

print("-" * 66)
print("n 이 2배(5→10) 될 때 누적은:",
      f"{free[9]['누적'] / free[4]['누적']:.2f}배  ← 2배가 아니다. n 이 커질수록 4배에 수렴한다")

# 출력:
#  n | 정리 비용 | 정리 누적 | 전체 누적 | 닫힌식 | 일치 | 증가배수
# ------------------------------------------------------------------
#  1 |        35 |        35 |        65 |     65 |  O   |
#  2 |        50 |        85 |       145 |    145 |  O   |    x2.23
#  3 |        65 |       150 |       240 |    240 |  O   |    x1.66
#  4 |        80 |       230 |       350 |    350 |  O   |    x1.46
#  5 |        95 |       325 |       475 |    475 |  O   |    x1.36
#  6 |       110 |       435 |       615 |    615 |  O   |    x1.29
#  7 |       125 |       560 |       770 |    770 |  O   |    x1.25
#  8 |       140 |       700 |       940 |    940 |  O   |    x1.22
#  9 |       155 |       855 |      1125 |   1125 |  O   |    x1.20
# 10 |       170 |      1025 |      1325 |   1325 |  O   |    x1.18
# ------------------------------------------------------------------
# n 이 2배(5→10) 될 때 누적은: 2.79배  ← 2배가 아니다. n 이 커질수록 4배에 수렴한다

# %% [markdown]
# ### 회차 상한만 두면 최악 비용이 제곱으로 튄다
#
# 회차 상한 $N$만 걸어 두고 예산 상한이 없다고 하자. 최악 비용은
#
# $$C_{\max}=C_{\text{전체}}(N)\approx\frac{s}{2}N^{2}$$
#
# 이므로 $N$을 4에서 8로 "조금만" 늘렸을 뿐인데 비용은 4배 가까이 뛴다.
# "재시도 5번까지만" 같은 회차 상한은 **직관적으로는 선형처럼 느껴지지만**
# 회차당 비용이 커지는 구조에서는 실제로 이차다.
#
# 그래서 **회차 상한과 예산 상한은 둘 다 있어야 한다.**
# 회차 상한은 무한 루프를 막고, 예산 상한은 *비용 폭발*을 막는다. 역할이 다르다.
# `ex5_debug_state.py`가 두 조건을 모두 넣어 둔 이유가 이것이고,
# 실제로 이 예제에서는 **예산 상한 쪽이 일을 했다**.

# %%
# 회차 상한만 믿었을 때의 최악 비용 (예산 상한 없음)
print("회차 상한 N | 최악 누적 비용 | N=4 대비")
print("-" * 42)
base4 = cost_closed_form(4)
for N in (2, 4, 8, 16, 32):
    c = cost_closed_form(N)
    print(f"{N:>11} | {c:>14,} | x{c / base4:>6.1f}")
print("-" * 42)
print("N 2배 → 비용 3배 이상(점근적으로 4배). 상한을 «조금» 늘렸다는 감각이 배신한다.")

# 출력:
# 회차 상한 N | 최악 누적 비용 | N=4 대비
# ------------------------------------------
#           2 |            145 | x   0.4
#           4 |            350 | x   1.0
#           8 |            940 | x   2.7
#          16 |          2,840 | x   8.1
#          32 |          9,520 | x  27.2
# ------------------------------------------
# N 2배 → 비용 3배 이상(점근적으로 4배). 상한을 «조금» 늘렸다는 감각이 배신한다.

# %% [markdown]
# ## 3. 어느 조건이 먼저 걸리는가 — 파라미터를 바꿔 본다
#
# 두 종료 조건은 **경쟁 관계**다. 파라미터에 따라 어느 쪽이 먼저 발동하는지 갈린다.
#
# - **예산이 먼저 걸리는 영역**: 예산이 낮거나 기울기 $s$가 크다 →
#   회차 상한에 닿기 전에 돈이 떨어진다. (원본 기본값이 여기)
# - **회차가 먼저 걸리는 영역**: 예산이 넉넉하거나 기울기가 작다 →
#   회차 상한 $N$이 실질적인 브레이크다. 이 영역에서는 예산 상한이 **죽은 코드**다.
#
# 경계는 $C_{\text{전체}}(N)$과 예산을 비교하면 바로 나온다:
#
# $$\text{예산} > (f+b)N+s\frac{N(N+1)}{2}\;\Longrightarrow\;\text{회차 상한이 먼저}$$
#
# 기본값($f{=}30,\ b{=}20,\ s{=}15,\ N{=}4$)에서 임계 예산은 $350$이다.
# 즉 **예산이 350을 넘어야 비로소 회차 상한이 의미를 갖는다.**

# %%
# 예산을 바꿔 가며 어느 조건이 먼저 걸리는지 본다 (회차 상한 4 고정)
임계예산 = cost_closed_form(MAX_ROUND)
print(f"이론 임계 예산 = C_전체({MAX_ROUND}) = {임계예산}\n")

print("예산  | 종료 원인 | 돈 회차 | 최종 쓴돈 | 초과분")
print("-" * 52)
for budget in (60, 100, 150, 240, 350, 351, 500):
    rs, why = simulate(budget=budget)
    over = rs[-1]["누적"] - budget
    print(f"{budget:>5} | {why:^9} | {rs[-1]['회차']:>7} | {rs[-1]['누적']:>9} | "
          f"{over if why == '예산' else 0:>+6}")
print("-" * 52)
print("예산 350 이하 → 예산이 먼저. 351 이상 → 회차가 먼저.  이론값과 일치.")

# 출력:
# 이론 임계 예산 = C_전체(4) = 350
#
# 예산  | 종료 원인 | 돈 회차 | 최종 쓴돈 | 초과분
# ----------------------------------------------------
#    60 |    예산     |       1 |        65 |     +5
#   100 |    예산     |       2 |       145 |    +45
#   150 |    예산     |       3 |       240 |    +90
#   240 |    예산     |       3 |       240 |     +0
#   350 |    예산     |       4 |       350 |     +0
#   351 |    회차     |       4 |       350 |     +0
#   500 |    회차     |       4 |       350 |     +0
# ----------------------------------------------------
# 예산 350 이하 → 예산이 먼저. 351 이상 → 회차가 먼저.  이론값과 일치.

# %%
# 기울기를 바꿔 가며 (회차 상한 4 고정). 예산 두 값에서 비교한다.
for bd in (100, 400):
    print(f"[예산 {bd}]  기울기 s | 종료 원인 | 돈 회차 | 최종 쓴돈 | 초과분 | 정리 비용 추이")
    print("-" * 80)
    for s in (0, 5, 10, 15, 30, 60):
        rs, why = simulate(budget=bd, slope=s)
        over = max(0, rs[-1]["누적"] - bd)
        trail = " → ".join(str(r["정리"]) for r in rs)
        print(f"{'':>10}{s:>8} | {why:^7} | {rs[-1]['회차']:>7} | "
              f"{rs[-1]['누적']:>9} | {over:>+6} | {trail}")
    print("-" * 80)
    print()

print("예산 100 에서는 기울기가 0이어도 2회차 만에 예산이 걸린다 — 예산이 너무 빡빡하다.")
print("예산 400 으로 올리면 s 가 작을 때는 «회차»가, s 가 커지면 «예산»이 먼저 걸린다.")
print("즉 어느 조건이 실질적 브레이크인지는 (예산, 기울기) 조합이 정한다.")

# 출력:
# [예산 100]  기울기 s | 종료 원인 | 돈 회차 | 최종 쓴돈 | 초과분 | 정리 비용 추이
# --------------------------------------------------------------------------------
#                  0 |  예산   |       2 |       100 |     +0 | 20 → 20
#                  5 |  예산   |       2 |       115 |    +15 | 25 → 30
#                 10 |  예산   |       2 |       130 |    +30 | 30 → 40
#                 15 |  예산   |       2 |       145 |    +45 | 35 → 50
#                 30 |  예산   |       2 |       190 |    +90 | 50 → 80
#                 60 |  예산   |       1 |       110 |    +10 | 80
# --------------------------------------------------------------------------------
#
# [예산 400]  기울기 s | 종료 원인 | 돈 회차 | 최종 쓴돈 | 초과분 | 정리 비용 추이
# --------------------------------------------------------------------------------
#                  0 |  회차   |       4 |       200 |     +0 | 20 → 20 → 20 → 20
#                  5 |  회차   |       4 |       250 |     +0 | 25 → 30 → 35 → 40
#                 10 |  회차   |       4 |       300 |     +0 | 30 → 40 → 50 → 60
#                 15 |  회차   |       4 |       350 |     +0 | 35 → 50 → 65 → 80
#                 30 |  예산   |       4 |       500 |   +100 | 50 → 80 → 110 → 140
#                 60 |  예산   |       3 |       510 |   +110 | 80 → 140 → 200
# --------------------------------------------------------------------------------
#
# 예산 100 에서는 기울기가 0이어도 2회차 만에 예산이 걸린다 — 예산이 너무 빡빡하다.
# 예산 400 으로 올리면 s 가 작을 때는 «회차»가, s 가 커지면 «예산»이 먼저 걸린다.
# 즉 어느 조건이 실질적 브레이크인지는 (예산, 기울기) 조합이 정한다.

# %% [markdown]
# ## 4. 시각화
#
# 두 장을 그린다.
#
# 1. **회차 대비 누적 비용 곡선** — 기울기 $s$별 곡선과 예산선(100), 회차 상한선(4).
#    직선이 아니라 **위로 휘는 곡선**이라는 게 눈으로 보인다.
# 2. **(예산, 기울기) 격자 히트맵** — 어느 종료 조건이 먼저 발동하는지.
#    두 영역을 가르는 경계는 앞서 구한 $C_{\text{전체}}(N)=\text{예산}$ 곡선이다.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

NS = list(range(0, 11))
SLOPES = [0, 15, 30]
COLORS = {0: "#8899a6", 15: "#e05252", 30: "#7a4fd0"}

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=(
        "회차 대비 누적 비용 — 이차로 자란다",
        "(예산, 기울기) 격자 — 어느 조건이 먼저 걸리나",
    ),
    horizontal_spacing=0.13,
)

# --- (1) 누적 비용 곡선 ---
for s in SLOPES:
    ys = [cost_closed_form(n, slope=s) for n in NS]
    label = f"기울기 s={s}"
    if s == 0:
        label += " (선형 기준 — 비용이 안 커진다면)"
    elif s == SLOPE:
        label += " (원본)"
    fig.add_trace(
        go.Scatter(
            x=NS, y=ys, mode="lines+markers",
            name=label,
            line=dict(color=COLORS[s], width=3 if s == SLOPE else 2,
                      dash="dot" if s == 0 else "solid"),
            marker=dict(size=7 if s == SLOPE else 5),
            hovertemplate="회차 %{x}<br>누적 %{y}<extra></extra>",
        ),
        row=1, col=1,
    )

# 예산선 · 회차 상한선
fig.add_hline(y=BUDGET, line=dict(color="#d98a1f", width=2, dash="dash"),
              annotation_text=f"예산 {BUDGET}", annotation_position="bottom left",
              annotation_font=dict(size=11, color="#d98a1f"),
              row=1, col=1)
fig.add_vline(x=MAX_ROUND, line=dict(color="#3d8b5f", width=2, dash="dash"),
              annotation_text=f"회차 상한 {MAX_ROUND}",
              annotation_position="bottom right",
              annotation_font=dict(size=11, color="#3d8b5f"),
              row=1, col=1)

# 실제 시뮬레이션이 멈춘 지점
fig.add_trace(
    go.Scatter(
        x=[rows[-1]["회차"]], y=[rows[-1]["누적"]], mode="markers",
        name="원본 실행 종료 지점",
        marker=dict(size=15, color="#e05252", symbol="x-thin",
                    line=dict(width=3, color="#e05252")),
        hovertemplate="종료: 회차 %{x}, 쓴돈 %{y}<extra></extra>",
    ),
    row=1, col=1,
)
fig.add_annotation(
    x=rows[-1]["회차"], y=rows[-1]["누적"], xref="x", yref="y",
    text=f"<b>여기서 END</b><br>쓴돈 {rows[-1]['누적']} (예산 {BUDGET} 초과)",
    showarrow=True, arrowhead=2, arrowcolor="#e05252", arrowwidth=1.5,
    ax=-40, ay=-115, font=dict(size=11, color="#e05252"), align="left",
)

# --- (2) 히트맵: 어느 조건이 먼저 걸리나 ---
budgets = list(range(50, 801, 25))
slopes = list(range(0, 41, 2))
z = []           # 0 = 예산 먼저, 1 = 회차 먼저
hover = []
for s in slopes:
    zr, hr = [], []
    for bd in budgets:
        rs, why = simulate(budget=bd, slope=s)
        zr.append(0 if why == "예산" else 1)
        hr.append(f"예산 {bd}, 기울기 {s}<br>종료: {why} 상한"
                  f"<br>돈 회차 {rs[-1]['회차']}, 쓴돈 {rs[-1]['누적']}")
    z.append(zr)
    hover.append(hr)

fig.add_trace(
    go.Heatmap(
        x=budgets, y=slopes, z=z,
        colorscale=[[0.0, "#f2c1c1"], [0.49, "#f2c1c1"],
                    [0.51, "#bcd9c8"], [1.0, "#bcd9c8"]],
        zmin=0, zmax=1, showscale=False,
        text=hover, hovertemplate="%{text}<extra></extra>",
        xgap=0.5, ygap=0.5,
    ),
    row=1, col=2,
)

# 이론 경계선: 예산 = C_전체(N) 을 기울기별로 계산
boundary_b = [cost_closed_form(MAX_ROUND, slope=s) for s in slopes]
fig.add_trace(
    go.Scatter(
        x=boundary_b, y=slopes, mode="lines",
        name="이론 경계  예산 = C(N)",
        line=dict(color="#22303c", width=3),
        hovertemplate="기울기 %{y}<br>임계 예산 %{x}<extra></extra>",
    ),
    row=1, col=2,
)

# 원본 파라미터 위치
fig.add_trace(
    go.Scatter(
        x=[BUDGET], y=[SLOPE], mode="markers+text",
        name="원본 설정 (예산 100, s=15)",
        marker=dict(size=14, color="#22303c", symbol="star"),
        text=["  원본"], textposition="middle right",
        textfont=dict(size=11, color="#22303c"),
        hovertemplate="원본: 예산 100, 기울기 15<extra></extra>",
    ),
    row=1, col=2,
)

# 영역 라벨
fig.add_annotation(x=170, y=36, xref="x2", yref="y2", showarrow=False,
                   text="<b>예산이 먼저</b><br>(비용 폭발을 예산이 막는다)",
                   font=dict(size=12, color="#a33"), align="center")
fig.add_annotation(x=650, y=6, xref="x2", yref="y2", showarrow=False,
                   text="<b>회차가 먼저</b><br>(예산 상한은 죽은 코드)",
                   font=dict(size=12, color="#2f6b48"), align="center")

fig.update_xaxes(title_text="회차 n", row=1, col=1, dtick=1)
fig.update_yaxes(title_text="누적 쓴돈", row=1, col=1)
fig.update_xaxes(title_text="예산", row=1, col=2)
fig.update_yaxes(title_text="정리 노드 기울기 s", row=1, col=2)

fig.update_layout(
    title=dict(
        text="<b>정리 비용 = 20 + 회차 x 15</b> — 회차마다 비싸지면 누적은 이차로 자란다"
             f"  (회차 상한 {MAX_ROUND} 고정)",
        x=0.5, xanchor="center", font=dict(size=16),
    ),
    template="plotly_white",
    width=1350, height=620,
    legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5),
    margin=dict(t=100, b=120, l=70, r=40),
)

_show(fig)

# %%
import os

_out = os.path.join(os.path.dirname(os.path.abspath(__file__))
                    if "__file__" in globals() else ".", "expy.png")
fig.write_image(_out, width=1350, height=620, scale=2)
print(f"저장 완료: {_out}")

# 출력:
# 저장 완료: .../2c3b87dd-4d2c-43a5-88c3-49d7b554f477/expy.png

# %% [markdown]
# ## 5. 정리
#
# | 항목 | 내용 |
# |---|---|
# | 정리 노드 비용 | `20 + 회차 × 15` — **회차에 비례해 커진다** |
# | 1·2회차 비용 | 35 → 50 (한 회차에 +15, 43% 증가) |
# | 누적 비용 | $C(n)=20n+15\frac{n(n-1)}{2}$ — **선형이 아니라 이차** |
# | 최고차항 | $\frac{s}{2}n^{2}$ — 회차 상한 2배 = 최악 비용 약 4배 |
# | 원본 실행 결과 | 2회차에 쓴돈 145 → **예산 상한이 먼저** 발동 (회차 상한 4는 미도달) |
# | 임계 예산 | 350 — 이보다 커야 회차 상한이 실질적 브레이크가 된다 |
#
# **핵심 세 줄**
#
# 1. `정리`가 `s["회차"]`를 읽어 비용을 계산한다는 건, 이 노드가 **상태에 의존해 점점
#    비싸지는** 노드라는 뜻이다. 에이전트가 맥락을 계속 쌓아 두고 매번 전부 요약/정리하는
#    실제 패턴이 정확히 이 모양이다 — 그래서 주석에 "실제로 흔한 패턴"이라 적혀 있다.
# 2. 이런 구조에서 **회차 상한만 두는 건 안전장치로 부족하다**. 회차는 선형으로 세지만
#    비용은 이차로 자라기 때문에, "재시도 5번까지" 같은 감각적인 상한이 비용을 배신한다.
# 3. 그래서 `route()`는 **예산 검사를 회차 검사보다 먼저** 한다. 그리고 이 예제에서
#    실제로 일을 한 것도 예산 조건이었다. 다만 `route()`는 *쓰고 난 뒤*에 검사하므로
#    145로 45만큼 초과했다 — 상한은 초과분까지 감안해서 잡아야 한다.
#
# 20장에서 다룰 "언제 멈출 것인가"가 바로 이 지점이다.
