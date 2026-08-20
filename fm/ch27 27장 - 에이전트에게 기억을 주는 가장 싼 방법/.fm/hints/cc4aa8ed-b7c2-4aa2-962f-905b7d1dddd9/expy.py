# %% [markdown]
# # 사실이 늘 때: 「전부 컨텍스트에」 $O(N)$ vs 「그래프 조회」 $O(1)$
#
# 사실이 $N$개 있을 때 하루 입력 토큰 비용을 두 방식으로 계산한다.
#
# - **전부 컨텍스트에**: 매 턴 사실 $N$개를 전부 프롬프트에 붙인다
#   $$C_\text{all}(N) = N \cdot t \cdot T \cdot p \cdot r$$
# - **그래프 조회**: 질문에 걸린 상위 $k$개만 붙인다 ($k$는 $N$과 무관)
#   $$C_\text{graph}(N) = k \cdot t \cdot T \cdot p \cdot r \;=\; \text{const}$$
#
# 여기서 $t$ = 사실 하나의 토큰 수, $T$ = 하루 턴 수, $p$ = 토큰당 단가(USD),
# $r$ = 환율. **$N$은 첫 식에만 들어간다.** 그래서 하나는 기울기가 있고 하나는 평평하다.
#
# 책의 `ex4_memory_cost.py`와 같은 상수를 쓴다.

# %%
# 필요 패키지: plotly, kaleido (표 부분은 표준 라이브러리만으로 동작)

def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


PRICE_IN = 3.0 / 1_000_000   # 입력 토큰 1개당 USD
KRW = 1_380                  # 환율
TOK_PER_FACT = 22            # 사실 하나를 프롬프트에 넣는 값(토큰)
TURNS = 200                  # 하루 대화 턴 수
HIT = 10                     # 그래프 조회가 실제로 걸어 오는 사실 수 (k)

# 사실 하나를 하루 동안 컨텍스트에 «상주»시키는 값
UNIT = TOK_PER_FACT * TURNS * PRICE_IN * KRW


def cost_all(n):
    """전부 컨텍스트에 — 사실 수에 비례. O(N)"""
    return n * UNIT


def cost_graph(n, k=HIT):
    """그래프 조회 — 걸리는 건 늘 k개. n을 아예 안 쓴다. O(1)"""
    return k * UNIT


print(f"사실 1개를 하루 상주시키는 값 = {TOK_PER_FACT} tok x {TURNS} turn "
      f"x ${PRICE_IN * 1_000_000:.0f}/Mtok x {KRW}원 = {UNIT:.3f}원/일")
print(f"그래프 쪽 상수 비용 = {HIT}개 x {UNIT:.3f}원 = {cost_graph(0):,.0f}원/일 (N과 무관)")

# 출력:
# 사실 1개를 하루 상주시키는 값 = 22 tok x 200 turn x $3/Mtok x 1380원 = 18.216원/일
# 그래프 쪽 상수 비용 = 10개 x 18.216원 = 182원/일 (N과 무관)


# %% [markdown]
# ## 1. 책의 표를 그대로 재현한다
#
# 사실 수를 50 → 5,000으로 **100배** 늘리면 어느 쪽이 얼마나 오르는가.

# %%
print(f"{'사실 수':>8}{'전부 넣기 토큰':>16}{'전부 넣기/일':>14}"
      f"{'그래프/일':>12}{'배율':>8}")
print("-" * 60)
for n in (50, 200, 1_000, 5_000):
    a, g = cost_all(n), cost_graph(n)
    print(f"{n:>8,}{n * TOK_PER_FACT * TURNS:>16,}{a:>13,.0f}원"
          f"{g:>11,.0f}원{a / g:>7.0f}x")

# 출력:
#     사실 수        전부 넣기 토큰       전부 넣기/일       그래프/일      배율
# ------------------------------------------------------------
#       50         220,000          911원        182원      5x
#      200         880,000        3,643원        182원     20x
#    1,000       4,400,000       18,216원        182원    100x
#    5,000      22,000,000       91,080원        182원    500x


# %% [markdown]
# 사실이 **100배** 늘 때 「전부 넣기」도 정확히 **100배** 오른다 (911원 → 91,080원).
# 「그래프 조회」는 **182원 그대로**다. 몇 개가 쌓였든 걸어 오는 건 10개니까.
#
# 5,000개면 하루 91,080원, 한 달이면 **273만 원**이다.
#
# > 조회 «시간»도 마찬가지다. 책 예제에서 사실을 100배 늘려도 조회는 2~7ms 사이에서
# > 논다. 규칙 없이 오르내리는 건 이 규모에서 «측정 잡음»이 지배해서고,
# > 5,000개짜리가 50개짜리보다 빠르게 나오기도 한다. 색인이 일하고 있다는 뜻이다.

# %%
print(f"{'사실 수':>8}{'월 비용(전부)':>16}{'월 비용(그래프)':>16}{'월 절감':>14}")
print("-" * 56)
for n in (50, 200, 1_000, 5_000):
    a, g = cost_all(n) * 30, cost_graph(n) * 30
    print(f"{n:>8,}{a:>15,.0f}원{g:>15,.0f}원{a - g:>13,.0f}원")

# 출력:
#     사실 수        월 비용(전부)       월 비용(그래프)          월 절감
# --------------------------------------------------------
#       50         27,324원          5,465원       21,859원
#      200        109,296원          5,465원      103,831원
#    1,000        546,480원          5,465원      541,015원
#    5,000      2,732,400원          5,465원    2,726,935원


# %% [markdown]
# ## 2. 토큰 값만 보면 손익 분기점은 어디인가
#
# $C_\text{all}(N) = C_\text{graph}$ 를 풀면
#
# $$N \cdot t \cdot T \cdot p \cdot r = k \cdot t \cdot T \cdot p \cdot r \quad\Longrightarrow\quad N^{*} = k$$
#
# 단가도 턴 수도 환율도 **전부 약분되어 사라진다.** 남는 건 $k$ 하나다.
# 즉 조회가 10개를 걸어 온다면 **사실 10개**에서 이미 두 방식이 같아진다.
# 「2배는 싸야 갈아탈 값을 한다」는 여유를 두면 $N = 2k = 20$ — 책이 말한 «20개»가 이 숫자다.

# %%
def breakeven_tokens(k=HIT, margin=1.0):
    """토큰 값만 볼 때의 분기점. margin=2 면 «2배 싸질 때»."""
    return k * margin


for m in (1.0, 2.0, 5.0):
    n = breakeven_tokens(margin=m)
    print(f"그래프가 {m:>3.0f}배 싸지는 지점: 사실 {n:>4.0f}개  "
          f"(전부 {cost_all(n):>8,.0f}원/일 vs 그래프 {cost_graph(n):,.0f}원/일)")

# 출력:
# 그래프가   1배 싸지는 지점: 사실   10개  (전부      182원/일 vs 그래프 182원/일)
# 그래프가   2배 싸지는 지점: 사실   20개  (전부      364원/일 vs 그래프 182원/일)
# 그래프가   5배 싸지는 지점: 사실   50개  (전부      911원/일 vs 그래프 182원/일)


# %% [markdown]
# ## 3. 사람 유지 비용을 더하면 분기점이 밀린다
#
# 위 계산에는 **그래프를 세우고 유지하는 사람 시간**이 빠져 있다.
# 그걸 하루치로 환산한 상수 $H$를 그래프 쪽에 더하면
#
# $$N \cdot u = k \cdot u + H \quad\Longrightarrow\quad N^{*} = k + \frac{H}{u}, \qquad u = t \cdot T \cdot p \cdot r = 18.216\ \text{원/일}$$
#
# $u$가 **사실 하나의 하루 값**이므로, $H/u$는 「사람 값이 사실 몇 개어치인가」다.
# 사람 하루가 사실 수백 개어치이기 때문에 분기점이 10에서 수백~수천으로 밀린다.

# %%
DEV_DAY_KRW = 400_000          # 개발자 1일 인건비 가정
SETUP_DAYS = 2                 # 세우는 데 이틀 (책: "옮기는 데 이틀이면 된다")
AMORTIZE_DAYS = 365            # 1년에 걸쳐 나눠 문다


def breakeven_with_people(maint_days_per_year, k=HIT):
    """세팅 + 연간 유지 사람 시간을 하루로 환산해 더한 분기점."""
    h = (SETUP_DAYS + maint_days_per_year) * DEV_DAY_KRW / AMORTIZE_DAYS
    return h, k + h / UNIT


print(f"{'연간 유지(사람일)':>16}{'하루 사람값 H':>14}{'H/u(사실 몇 개어치)':>20}{'분기점 N*':>12}")
print("-" * 64)
for d in (0, 2, 6, 12, 16, 24, 48):
    h, n = breakeven_with_people(d)
    print(f"{d:>16}{h:>13,.0f}원{h / UNIT:>19,.0f}{n:>12,.0f}")

# 출력:
#       연간 유지(사람일)      하루 사람값 H       H/u(사실 몇 개어치)      분기점 N*
# ----------------------------------------------------------------
#                0        2,192원                120         130
#                2        4,384원                241         251
#                6        8,767원                481         491
#               12       15,342원                842         852
#               16       19,726원              1,083       1,093
#               24       28,493원              1,564       1,574
#               48       54,795원              3,008       3,018


# %% [markdown]
# 표를 읽는 법. **세팅 이틀만 치고 유지 비용이 0이어도 분기점은 이미 10 → 130으로 밀린다.**
# 현실적으로 그래프는 스키마가 자라고 개체 해상도가 어긋나고 유효 시각을 닫아 줘야 하므로,
# **연 16일쯤(월 1.3일) 손이 간다고 보면 분기점이 약 1,093개** — 책이 기준으로 쓰는
# «사실 1,000개»가 딱 이 대역이다.
#
# 정리하면 두 개의 분기점이 있다.
#
# | | 분기점 | 뜻 |
# |---|---|---|
# | 토큰만 | $N^{*} = k = 10$ | 이론상 여기서 이미 그래프가 싸다 |
# | 토큰 + 사람 | $N^{*} = k + H/u \approx 1{,}000$ | 실무에서 실제로 갈아타는 지점 |
#
# 이게 「처음부터 그래프로 가지 마라」의 근거다.
# 사실 50개짜리 시스템에서 그래프를 세우면 하루 911원을 아끼려고 하루 19,726원을 쓰는 셈이다.

# %%
for n in (50, 1_000, 5_000):
    h, _ = breakeven_with_people(16)
    graph_total = cost_graph(n) + h
    verdict = "전부 넣기가 싸다" if cost_all(n) < graph_total else "그래프가 싸다"
    print(f"사실 {n:>5,}개 | 전부 넣기 {cost_all(n):>8,.0f}원/일 | "
          f"그래프 {cost_graph(n):>5,.0f}+{h:,.0f}={graph_total:>8,.0f}원/일 | {verdict}")

# 출력:
# 사실    50개 | 전부 넣기      911원/일 | 그래프   182+19,726=  19,908원/일 | 전부 넣기가 싸다
# 사실 1,000개 | 전부 넣기   18,216원/일 | 그래프   182+19,726=  19,908원/일 | 전부 넣기가 싸다
# 사실 5,000개 | 전부 넣기   91,080원/일 | 그래프   182+19,726=  19,908원/일 | 그래프가 싸다


# %% [markdown]
# ## 4. 곡선으로 보기 (로그 x축)
#
# 로그 x축에서 상수는 **수평선**, 비례는 **오른쪽으로 오르는 곡선**이 된다.
# 두 선이 만나는 곳이 분기점이다. 사람 값을 더하면 수평선이 위로 올라가고,
# 만나는 지점이 오른쪽으로 밀린다.

# %%
try:
    import math

    import plotly.graph_objects as go

    # 로그 축에서는 shape/annotation 좌표를 log10 값으로 줘야 한다
    def lg(v):
        return math.log10(v)

    ns = [10 ** (i / 20) for i in range(20, 81)]   # 10 ~ 10,000 로그 등간격
    all_y = [cost_all(n) for n in ns]
    h16, be16 = breakeven_with_people(16)
    graph_y = [cost_graph(n) for n in ns]
    graph_h_y = [cost_graph(n) + h16 for n in ns]

    BLUE, ORANGE, GREEN = "#2a78d6", "#eb6834", "#2f9e6e"
    INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e8e7e3"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ns, y=all_y, mode="lines", name="전부 컨텍스트에 — O(N)",
        line=dict(color=BLUE, width=2.5)))
    fig.add_trace(go.Scatter(
        x=ns, y=graph_y, mode="lines", name="그래프 조회(토큰만) — O(1) 182원",
        line=dict(color=ORANGE, width=2.5)))
    fig.add_trace(go.Scatter(
        x=ns, y=graph_h_y, mode="lines", name="그래프 조회 + 사람 유지(연 16일)",
        line=dict(color=GREEN, width=2.5, dash="dash")))

    for x, label, color, anchor in (
            (HIT, f"토큰만<br>N*={HIT}", ORANGE, "left"),
            (be16, f"사람 유지 포함<br>N*≈{be16:,.0f}", GREEN, "right")):
        # 세로 기준선은 데이터 좌표 Scatter 로 그린다 (add_vline 은 로그 축에서 좌표계가 헷갈린다)
        fig.add_trace(go.Scatter(
            x=[x, x], y=[100, 200_000], mode="lines", showlegend=False,
            hoverinfo="skip", line=dict(color=color, width=2, dash="dot")))
        fig.add_annotation(x=lg(x), y=0.03, yref="paper", text=label,
                           showarrow=False, xanchor=anchor, yanchor="bottom",
                           font=dict(size=11, color=color))

    for n, txt, ax_, ay_ in ((50, "50개 → 911원/일", 6, -34),
                             (5_000, "5,000개 → 91,080원/일", -18, -34)):
        fig.add_annotation(x=lg(n), y=lg(cost_all(n)), text=txt, showarrow=True,
                           arrowhead=0, arrowcolor=MUTED, ax=ax_, ay=ay_,
                           xanchor="left" if ax_ > 0 else "right",
                           font=dict(size=11, color=MUTED))

    fig.update_layout(
        title=dict(text="사실 수 N에 따른 하루 비용 — 하나는 오르고 하나는 평평하다",
                   font=dict(size=16, color=INK)),
        width=900, height=470, paper_bgcolor="#fcfcfb", plot_bgcolor="#fcfcfb",
        font=dict(color=INK),
        legend=dict(orientation="h", yanchor="bottom", y=1.06, x=0),
        margin=dict(t=110, b=60, l=75, r=30),
    )
    fig.update_xaxes(type="log", title_text="사실 수 N (로그)", range=[1, 4],
                     dtick=1, gridcolor=GRID, zeroline=False)
    fig.update_yaxes(type="log", title_text="하루 비용 (원, 로그)",
                     range=[lg(100), lg(200_000)], dtick=1,
                     gridcolor=GRID, zeroline=False)

    import os
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
    fig.write_image(out, scale=2)  # kaleido 필요
    print(f"저장: {out}")
    _show(fig)
except ImportError as e:
    print(f"plotly/kaleido 미설치 — 시각화 생략: {e}")

# 출력:
# 저장: .../.fm/hints/cc4aa8ed-b7c2-4aa2-962f-905b7d1dddd9/expy.png


# %% [markdown]
# ## 정리
#
# $$C_\text{all}(N) = N \cdot u \;\; (O(N)) \qquad C_\text{graph}(N) = k \cdot u \;\; (O(1))$$
#
# - **전부 컨텍스트에**는 사실 수에 **비례**해서 오른다. 50개 911원 → 5,000개 91,080원 (100배 → 100배).
# - **그래프 조회**는 **안 오른다.** 몇 개가 쌓였든 걸어 오는 건 열 개쯤이라 182원 고정이다.
# - 토큰만 보면 분기점은 $N^{*} = k$ — 단가·턴 수·환율이 다 약분된다.
# - 사람 유지 비용 $H$를 더하면 $N^{*} = k + H/u$ 로 **오른쪽으로 밀린다.** 그게 «1,000개» 기준의 근거다.
# - 그래서 처음엔 평평한 목록으로 시작하고, 하루 비용이 눈에 띄면 그때 옮긴다. 옮기는 데는 이틀이면 된다.
