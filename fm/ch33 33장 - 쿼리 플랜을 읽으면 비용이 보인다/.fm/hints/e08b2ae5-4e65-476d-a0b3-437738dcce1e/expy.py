# %% [markdown]
# # 성능 작업 전에 구간별로 쪼개 봐야 하는 이유 — 암달의 법칙
#
# 33장 `ex5_where_time_goes.py` 의 실제 수치를 가지고
# 암달의 법칙 $S(s) = \dfrac{1}{(1-p) + p/s}$ 를 확인한다.
#
# - $p$ : 내가 **개선할 수 있는 구간**이 전체 시간에서 차지하는 비율
# - $s$ : 그 구간을 몇 배 빠르게 만들었나
# - $S(s)$ : 전체가 몇 배 빨라졌나
#
# 핵심은 극한이다.
#
# $$\lim_{s \to \infty} S(s) = \frac{1}{1-p}$$
#
# 즉 그 구간을 **0ms 로 만들어도** 전체는 $\dfrac{1}{1-p}$ 배까지밖에 못 간다.
#
# 필요 패키지: `pip install plotly kaleido`

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# 33장 ex5_where_time_goes.py 의 SEGMENTS 원본 수치
# (구간 이름, 한 요청에서의 시간 ms, 최대 절감 비율, 방법)
SEGMENTS = [
    ("입력 검증",        3,    0.0,  "이미 최소"),
    ("그래프 조회 x4",   9,    0.5,  "인덱스·플랜"),
    ("벡터 검색",       11,    0.4,  "차원 축소·근사"),
    ("컨텍스트 조립",    18,    0.7,  "24장 — 참조만 싣기"),
    ("모델 호출",     1_820,   0.3,  "짧은 프롬프트·작은 모델"),
    ("응답 후처리",      24,    0.6,  "스트리밍"),
    ("체크포인트 쓰기",   34,    0.8,  "상태 줄이기·슈퍼스텝 줄이기"),
]

TOTAL = sum(ms for _n, ms, _r, _h in SEGMENTS)
print(f"한 요청 총 시간 = {TOTAL:,} ms")
for name, ms, _r, _h in SEGMENTS:
    print(f"  {name:<16}{ms:>7,} ms   {ms / TOTAL:>7.2%}")
# 출력:
# 한 요청 총 시간 = 1,919 ms
#   입력 검증               3 ms     0.16%
#   그래프 조회 x4          9 ms     0.47%
#   벡터 검색              11 ms     0.57%
#   컨텍스트 조립          18 ms     0.94%
#   모델 호출           1,820 ms    94.84%
#   응답 후처리            24 ms     1.25%
#   체크포인트 쓰기        34 ms     1.77%

# %% [markdown]
# ## 1. 암달의 법칙 — 식과 극한
#
# 총 시간 $T$ 를 「개선 가능한 부분 $pT$」와 「그대로인 부분 $(1-p)T$」로 나눈다.
# 개선 가능한 부분을 $s$ 배 빠르게 하면
#
# $$T' = (1-p)T + \frac{pT}{s} \;\Longrightarrow\; S(s) = \frac{T}{T'} = \frac{1}{(1-p) + p/s}$$
#
# 절감률로 쓰면 더 직관적이다.
#
# $$1 - \frac{T'}{T} = p\left(1 - \frac{1}{s}\right)$$
#
# **절감률은 $p$ 에 정비례한다.** $p$ 가 작으면 $s$ 를 아무리 키워도 소용없다.

# %%
def speedup(p, s):
    """암달의 법칙: 비중 p 인 구간을 s 배 빠르게 했을 때 전체 속도 향상 배수."""
    return 1.0 / ((1.0 - p) + p / s)


def saving(p, s):
    """같은 조건에서의 전체 시간 절감률."""
    return p * (1.0 - 1.0 / s)


# 극한이 1/(1-p) 로 가는지 수치로 확인
for p in (0.5, 0.9, 0.9484, 0.0516):
    print(f"p={p:.4f}  S(2)={speedup(p, 2):6.3f}  S(10)={speedup(p, 10):6.3f}  "
          f"S(1e6)={speedup(p, 1e6):8.3f}   1/(1-p)={1 / (1 - p):8.3f}")
# 출력:
# p=0.5000  S(2)= 1.333  S(10)= 1.818  S(1e6)=   2.000   1/(1-p)=   2.000
# p=0.9000  S(2)= 1.818  S(10)= 5.263  S(1e6)=  10.000   1/(1-p)=  10.000
# p=0.9484  S(2)= 1.902  S(10)= 6.829  S(1e6)=  19.379   1/(1-p)=  19.380
# p=0.0516  S(2)= 1.026  S(10)= 1.049  S(1e6)=   1.054   1/(1-p)=   1.054
# (p 가 클수록 s 를 올린 보상이 오래간다. p=0.0516 은 s=2 에서 이미 천장 근처다)

# %% [markdown]
# ## 2. 여러 $p$ 값에 대한 $S(s)$ 곡선
#
# 각 곡선은 자기만의 수평 점근선 $1/(1-p)$ 에 갇힌다.
# $p=0.05$ 곡선은 $s=4$ 쯤에서 이미 평평해진다 — 더 노력할 이유가 없다.

# %%
P_MODEL = 1820 / TOTAL           # 모델 호출의 비중
P_REST = (TOTAL - 1820) / TOTAL  # 모델 호출을 뺀 나머지 전부의 비중
print(f"p(모델 호출)  = {P_MODEL:.6f}  → 천장 {1 / (1 - P_MODEL):.2f}배")
print(f"p(나머지 전부) = {P_REST:.6f}  → 천장 {1 / (1 - P_REST):.4f}배")
# 출력:
# p(모델 호출)  = 0.948411  → 천장 19.38배
# p(나머지 전부) = 0.051589  → 천장 1.0544배

S_GRID = [1 + i * 0.25 for i in range(0, 129)]  # s = 1 .. 33
P_CURVES = [0.05, 0.25, 0.50, 0.75, 0.90, 0.95]
PALETTE = ["#6E7B8B", "#4C9AA8", "#3E7CB1", "#B5793B", "#A2543A", "#8A3F52"]


def amdahl_fig():
    fig = go.Figure()
    for color, p in zip(PALETTE, P_CURVES):
        fig.add_trace(go.Scatter(
            x=S_GRID, y=[speedup(p, s) for s in S_GRID],
            mode="lines", name=f"p = {p:.2f}",
            line=dict(color=color, width=2.5),
            hovertemplate="s=%{x:.1f}<br>S=%{y:.2f}<extra></extra>"))
        fig.add_hline(y=1 / (1 - p), line=dict(color=color, width=1, dash="dot"),
                      opacity=0.5)
    # ex5 의 두 시나리오를 점으로 얹는다
    fig.add_trace(go.Scatter(
        x=[2.757], y=[speedup(P_REST, 2.757)], mode="markers+text",
        name="ex5: 나머지 전부 최적화",
        marker=dict(color="#111111", size=11, symbol="diamond"),
        text=["나머지 전부 → 1.034배"], textposition="top center",
        textfont=dict(size=11)))
    fig.add_trace(go.Scatter(
        x=[1 / (1 - 0.3)], y=[speedup(P_MODEL, 1 / (1 - 0.3))],
        mode="markers+text", name="ex5: 모델 호출만 30% 절감",
        marker=dict(color="#8A3F52", size=11, symbol="diamond"),
        text=["모델 호출만 → 1.398배"], textposition="bottom right",
        textfont=dict(size=11)))
    fig.update_xaxes(title_text="s (개선 구간을 몇 배 빠르게 했나)")
    fig.update_yaxes(title_text="S(s) (전체 속도 향상 배수)", type="log",
                     tickmode="array", tickvals=[1, 1.5, 2, 3, 5, 10, 20],
                     ticktext=["1x", "1.5x", "2x", "3x", "5x", "10x", "20x"])
    fig.update_layout(
        title="암달의 법칙 — 점선은 각 p 의 천장 1/(1-p)",
        template="simple_white", height=520,
        legend=dict(orientation="h", y=-0.18))
    return fig


fig1 = amdahl_fig()
_show(fig1)

# %% [markdown]
# ## 3. ex5 의 7구간 시간 분해
#
# 모델 호출 하나가 **94.8%** 다. 나머지 여섯 구간을 다 합쳐도 99ms, 5.2% 뿐이다.

# %%
names = [n for n, _m, _r, _h in SEGMENTS]
times = [m for _n, m, _r, _h in SEGMENTS]
ratios = [m / TOTAL for m in times]
colors = ["#8A3F52" if n == "모델 호출" else "#6E7B8B" for n in names]

# 비중이 큰 순으로 정렬 (막대는 아래에서 위로 그려지므로 역순)
order = sorted(range(len(names)), key=lambda i: times[i])


def segments_fig():
    fig = go.Figure(go.Bar(
        x=[times[i] for i in order], y=[names[i] for i in order],
        orientation="h",
        marker=dict(color=[colors[i] for i in order]),
        text=[f"{times[i]:,}ms  ({ratios[i]:.2%})" for i in order],
        textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: %{x:,}ms<extra></extra>"))
    fig.update_xaxes(title_text="한 요청에서의 시간 (ms, 로그 축)", type="log",
                     range=[0.3, 3.9], tickmode="array",
                     tickvals=[3, 10, 30, 100, 300, 1000, 3000],
                     ticktext=["3", "10", "30", "100", "300", "1,000", "3,000"])
    fig.update_layout(
        title=f"ex5 — 한 요청 {TOTAL:,}ms 의 구간별 분해",
        template="simple_white", height=420, showlegend=False)
    return fig


fig2 = segments_fig()
_show(fig2)

# %% [markdown]
# ## 4. 시나리오 계산 — "모델 호출 외 전부 0으로" 는 몇 % 인가
#
# 세 가지를 비교한다.
#
# - **A** 모델 호출 외 여섯 구간을 **전부 0ms** 로 (물리적으로 불가능한 최선, $s \to \infty$)
# - **B** 여섯 구간을 표의 「최대 절감 비율」만큼 실제로 줄이면 (ex5 가 계산하는 값)
# - **C** 모델 호출 **하나만** 30% 줄이면

# %%
non_model = TOTAL - 1820                       # 99 ms
save_b = sum(m * r for n, m, r, _h in SEGMENTS if n != "모델 호출")  # 63.1 ms

sc = {}
# A: 나머지를 전부 0으로 → s = ∞
sc["A 나머지 전부 0ms"] = (P_REST, float("inf"), non_model)
# B: 나머지를 최대 절감 비율만큼 → s = 99 / (99 - 63.1)
sc["B 나머지 최대 절감"] = (P_REST, non_model / (non_model - save_b), save_b)
# C: 모델 호출만 30%
sc["C 모델 호출만 30%"] = (P_MODEL, 1 / (1 - 0.3), 1820 * 0.3)

print(f"{'시나리오':<20}{'p':>9}{'s':>9}{'절감 ms':>10}{'S':>8}{'절감률':>9}")
print("-" * 65)
rows = []
for label, (p, s, ms_saved) in sc.items():
    S = speedup(p, s) if s != float("inf") else 1 / (1 - p)
    red = saving(p, s) if s != float("inf") else p
    rows.append((label, S, red))
    s_txt = "inf" if s == float("inf") else f"{s:.3f}"
    print(f"{label:<20}{p:>9.4f}{s_txt:>9}{ms_saved:>10,.1f}{S:>8.4f}{red:>9.2%}")
# 출력:
# 시나리오                        p        s   절감 ms       S      절감률
# -----------------------------------------------------------------
# A 나머지 전부 0ms           0.0516      inf      99.0  1.0544    5.16%
# B 나머지 최대 절감            0.0516    2.758      63.1  1.0340    3.29%
# C 모델 호출만 30%           0.9484    1.429     546.0  1.3977   28.45%

# %%
# ex5 의 문장을 그대로 재현해 본다
print(f"모델 호출 비중       : {1820 / TOTAL:.1%}")
print(f"나머지 전부 최대 절감 : {save_b:,.1f}ms  = 총 {TOTAL:,}ms 의 {save_b / TOTAL:.1%}")
print(f"→ {TOTAL:,}ms 가 {TOTAL - save_b:,.1f}ms 로 줄어든다")
print()
print(f"모델 호출만 30% 절감  : {1820 * 0.3:,.1f}ms = 총 {TOTAL:,}ms 의 {1820 * 0.3 / TOTAL:.1%}")
print(f"→ 한 구간 손댄 쪽이 여섯 구간 다 손댄 쪽의 {(1820 * 0.3) / save_b:.1f}배")
print()
print(f"나머지를 손대는 작업의 천장 : {1 / (1 - P_REST):.4f}배 (= {P_REST:.2%} 절감)")
print(f"모델 호출을 손대는 작업의 천장: {1 / (1 - P_MODEL):.2f}배 (= {P_MODEL:.2%} 절감)")
# 출력:
# 모델 호출 비중       : 94.8%
# 나머지 전부 최대 절감 : 63.1ms  = 총 1,919ms 의 3.3%
# → 1,919ms 가 1,855.9ms 로 줄어든다
#
# 모델 호출만 30% 절감  : 546.0ms = 총 1,919ms 의 28.5%
# → 한 구간 손댄 쪽이 여섯 구간 다 손댄 쪽의 8.7배
#
# 나머지를 손대는 작업의 천장 : 1.0544배 (= 5.16% 절감)
# 모델 호출을 손대는 작업의 천장: 19.38배 (= 94.84% 절감)

# %% [markdown]
# ## 5. 33장 서두의 "3주 동안 쿼리 튜닝, 9ms → 4ms"
#
# 그래프 조회 구간은 9ms, 비중 $p = 9/1919 = 0.47\%$ 다.
# 4ms 로 줄였으니 $s = 9/4 = 2.25$.

# %%
p_q = 9 / TOTAL
s_q = 9 / 4
print(f"p = 9/{TOTAL} = {p_q:.5f} ({p_q:.2%}),  s = {s_q}")
print(f"전체 속도 향상 S = {speedup(p_q, s_q):.5f}배")
print(f"전체 절감률      = {saving(p_q, s_q):.3%}")
print(f"→ {TOTAL:,}ms 가 {TOTAL / speedup(p_q, s_q):,.1f}ms 로. 3주의 성과가 5ms 다.")
print(f"이 구간의 천장(9ms 를 0ms 로 만들어도) = {p_q:.2%} 절감")
# 출력:
# p = 9/1919 = 0.00469 (0.47%),  s = 2.25
# 전체 속도 향상 S = 1.00261배
# 전체 절감률      = 0.261%
# → 1,919ms 가 1,914.0ms 로. 3주의 성과가 5ms 다.
# 이 구간의 천장(9ms 를 0ms 로 만들어도) = 0.47% 절감

# %% [markdown]
# ## 6. 정리 그림 저장
#
# 세 장을 한 판에 모아 `expy.png` 로 저장한다.

# %%
import os

fig = make_subplots(
    rows=2, cols=2,
    specs=[[{"colspan": 2}, None], [{}, {}]],
    row_heights=[0.52, 0.48],
    vertical_spacing=0.14, horizontal_spacing=0.12,
    subplot_titles=(
        "① 암달의 법칙 S(s) — 점선은 천장 1/(1-p)",
        f"② ex5 구간 분해 (총 {TOTAL:,}ms)",
        "③ 시나리오별 전체 절감률",
    ))

for color, p in zip(PALETTE, P_CURVES):
    fig.add_trace(go.Scatter(
        x=S_GRID, y=[speedup(p, s) for s in S_GRID], mode="lines",
        name=f"p = {p:.2f}", line=dict(color=color, width=2.2)), row=1, col=1)
    fig.add_hline(y=1 / (1 - p), line=dict(color=color, width=1, dash="dot"),
                  opacity=0.45, row=1, col=1)

fig.add_trace(go.Bar(
    x=[times[i] for i in order], y=[names[i] for i in order], orientation="h",
    marker=dict(color=[colors[i] for i in order]),
    text=[f"{ratios[i]:.1%}" for i in order], textposition="outside",
    cliponaxis=False, showlegend=False), row=2, col=1)

fig.add_trace(go.Bar(
    x=[r[0] for r in rows], y=[r[2] for r in rows],
    marker=dict(color=["#6E7B8B", "#6E7B8B", "#8A3F52"]),
    text=[f"{r[2]:.1%}" for r in rows], textposition="outside",
    cliponaxis=False, showlegend=False), row=2, col=2)

fig.update_yaxes(title_text="S(s)", type="log", tickmode="array",
                 tickvals=[1, 1.5, 2, 3, 5, 10, 20],
                 ticktext=["1x", "1.5x", "2x", "3x", "5x", "10x", "20x"],
                 row=1, col=1)
fig.update_xaxes(title_text="s", row=1, col=1)
fig.update_xaxes(title_text="ms (로그)", type="log", range=[0.3, 3.9],
                 tickmode="array", tickvals=[3, 10, 30, 100, 300, 1000, 3000],
                 ticktext=["3", "10", "30", "100", "300", "1,000", "3,000"],
                 row=2, col=1)
fig.update_yaxes(title_text="전체 절감률", tickformat=".0%", range=[0, 0.34],
                 row=2, col=2)
fig.update_layout(
    title_text="성능 작업 전에 구간별로 쪼개 봐야 하는 이유 — p 가 천장을 정한다",
    template="simple_white", height=860, width=1180,
    legend=dict(orientation="h", y=1.02, x=0.55, yanchor="bottom"))

_show(fig)

_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_png, scale=2)   # 필요 패키지: kaleido
print(f"저장: {_png}")
# 출력:
# 저장: .../e08b2ae5-4e65-476d-a0b3-437738dcce1e/expy.png

# %% [markdown]
# ## 결론
#
# $$S(s) = \frac{1}{(1-p) + p/s}, \qquad \lim_{s\to\infty} S(s) = \frac{1}{1-p}$$
#
# - $s$ 는 **노력**해서 얻는 값이고, $p$ 는 **측정**하면 바로 나오는 값이다.
# - 그런데 결과를 지배하는 것은 $p$ 다. $p$ 가 5%면 천장이 1.05배다.
# - 그래서 **재는 것이 먼저다.** 쪼개 보지 않으면 자기 작업의 천장을 모른 채 3주를 쓴다.
# - 에이전트 시스템에서 $p$ 가 큰 구간은 거의 항상 모델 호출이다.
