# %% [markdown]
# # 자릿수가 흔들리는 지표 — 「그래프 전환점 1,000개」
#
# 35장 `ex4_selfcheck.py`는 이 책의 숫자를 「여러분이 다시 재야 하는 것」으로 바꾼 표다.
# 그 표에서 **그래프 전환점**(27장)만 주의 칸에 「인건비·단가에 달렸다」가 붙어 있고,
# 예제 마지막 출력이 이렇게 말한다.
#
# ```
# 체크포인터가 2배쯤 느리다 → 여러분도 배수는 비슷할 것
# 모델 호출이 95% 다      → 여러분도 90% 는 넘을 것
# 그래프 전환점이 1,000개  → 여러분은 300일 수도 3,000일 수도
# ```
#
# 이 스크립트는 왜 마지막 것만 **자릿수조차** 이식되지 않는지를 계산으로 보인다.
#
# 손익분기 모델은 이렇다. 엔티티 수 $N$에 대해 하루 비용을 맞춰 놓는다.
#
# $$
# \underbrace{N \cdot c_{no}}_{\text{비그래프: 전부 컨텍스트에}}
# \;=\;
# \underbrace{\frac{C_{fixed}}{H} + N \cdot c_{graph}}_{\text{그래프: 고정비 회수 + 유지비}}
# $$
#
# $$
# \Longrightarrow \quad N^{*} \;=\; \frac{C_{fixed} / H}{\,c_{no} - c_{graph}\,}
# $$
#
# - $c_{no}$ — 엔티티 하나를 컨텍스트에 넣는 하루 토큰 비용 → **토큰 단가에 정비례**
# - $c_{graph}$ — 엔티티 하나를 그래프에 유지하는 하루 비용(정규화 검토·저장) → **인건비에 정비례**
# - $C_{fixed}$ — 설계·정규화 파이프라인·운영 셋업의 **일회성 인건비**, $H$ — 회수 기간(일)
#
# 분자는 인건비이고 분모는 **서로 다른 가격에 매달린 두 값의 차이**다. 그래서 흔들린다.

# %%
# 필요 패키지: plotly, kaleido, numpy  (pip install plotly kaleido numpy)
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# 27장 ex4_memory_cost.py 의 기준값
TOK_PER_FACT = 22  # 사실 한 개를 프롬프트에 넣는 토큰 수
TURNS = 200  # 하루 대화 턴 수
KRW = 1_380  # 환율
PRICE_PER_M = 3.0  # 입력 토큰 $/1M (기준)

WAGE = 500_000  # 하루 인건비(원)
SETUP_DAYS = 5.5  # 설계 + 정규화 + 운영 셋업
HORIZON = 180  # 회수 기간(일)
MAINT_PER_FACT = 3.0  # 엔티티당 하루 유지비(원) — 정규화 검토 + 저장·색인

print(f"기준 토큰 단가  ${PRICE_PER_M}/1M")
print(f"기준 인건비     {WAGE:,}원/일 × {SETUP_DAYS}일, 회수 {HORIZON}일")
print(f"엔티티당 유지비 {MAINT_PER_FACT}원/일")
# 출력:
# 기준 토큰 단가  $3.0/1M
# 기준 인건비     500,000원/일 × 5.5일, 회수 180일
# 엔티티당 유지비 3.0원/일

# %% [markdown]
# ## 1. 기준값으로 전환점을 계산한다
#
# 엔티티 하나를 매일 컨텍스트에 넣는 비용은
# $c_{no} = (\text{토큰/사실}) \times (\text{하루 턴}) \times (\text{단가}) \times (\text{환율})$ 이다.
# 27장의 값과 맞는지 확인해 본다. 사실 5,000개면 하루 91,080원이 나와야 한다.


# %%
def c_no_per_fact(price_per_m=PRICE_PER_M):
    """엔티티 하나를 하루 동안 컨텍스트에 넣는 비용(원)."""
    return TOK_PER_FACT * TURNS * (price_per_m / 1_000_000) * KRW


def c_graph_per_fact(wage=WAGE, maint=MAINT_PER_FACT):
    """엔티티 하나를 그래프에 유지하는 하루 비용(원). 인건비에 비례."""
    return maint * (wage / WAGE)


def breakeven(price_per_m=PRICE_PER_M, wage=WAGE, setup_days=SETUP_DAYS, horizon=HORIZON):
    """N* = (C_fixed / H) / (c_no - c_graph). 전환점이 없으면 inf."""
    fixed_per_day = wage * setup_days / horizon
    denom = c_no_per_fact(price_per_m) - c_graph_per_fact(wage)
    if denom <= 0:
        return float("inf")
    return fixed_per_day / denom


c0 = c_no_per_fact()
print(f"c_no    = {c0:.3f} 원/사실/일")
print(f"c_graph = {c_graph_per_fact():.3f} 원/사실/일")
print(f"사실 5,000개 비그래프 하루 비용 = {5000 * c0:,.0f}원  (27장: 91,080원)")
print(f"사실   50개 비그래프 하루 비용 = {50 * c0:,.0f}원  (27장: 911원)")
print(f"\n기준 전환점 N* = {breakeven():,.0f}개  (책의 값: 1,000개)")
# 출력:
# c_no    = 18.216 원/사실/일
# c_graph = 3.000 원/사실/일
# 사실 5,000개 비그래프 하루 비용 = 91,080원  (27장: 91,080원)
# 사실   50개 비그래프 하루 비용 = 911원  (27장: 911원)
#
# 기준 전환점 N* = 1,004개  (책의 값: 1,000개)

# %% [markdown]
# 기준값에서 1,004개가 나온다. 27장의 「저는 1,000개를 기준으로 쓴다」와 맞다.
# 이제 **입력을 흔들어** 본다.
#
# ## 2. 인건비를 흔든다 — 분자가 그대로 따라간다
#
# $C_{fixed} = (\text{인건비}) \times (\text{셋업 일수})$ 이므로 $N^{*}$는 인건비에 거의 정비례한다.
# 엄밀히는 $c_{graph}$도 인건비에 비례해서 분모가 조금 줄기 때문에 정비례보다 살짝 더 빠르게 오른다.

# %%
wages = np.array([150_000, 200_000, 300_000, 500_000, 800_000, 1_200_000, 1_500_000])
n_by_wage = np.array([breakeven(wage=w) for w in wages])

print(f"{'하루 인건비':>12}{'N*':>10}{'기준 대비':>10}")
print("-" * 32)
for w, n in zip(wages, n_by_wage):
    print(f"{w:>12,}{n:>10,.0f}{n / n_by_wage[3]:>9.2f}배")
# 출력:
#       하루 인건비        N*     기준 대비
# --------------------------------
#      150,000       265     0.26배
#      200,000       359     0.36배
#      300,000       558     0.56배
#      500,000     1,004     1.00배
#      800,000     1,822     1.81배
#    1,200,000     3,328     3.32배
#    1,500,000     4,973     4.95배

# %% [markdown]
# 인건비만 흔들어도 **265 ~ 4,973**이다. 「300일 수도 3,000일 수도」라는 말이
# 과장이 아니라 인건비 폭 하나로 이미 채워진다.
#
# ## 3. 토큰 단가를 흔든다 — 분모가 차이값이라 증폭된다
#
# 분모는 $c_{no} - c_{graph}$다. 단가가 3분의 1이 되면 $c_{no}$만 3분의 1이 되고
# $c_{graph}$는 그대로 남으므로 분모는 3분의 1보다 훨씬 더 크게 줄어든다.
# 그래서 $N^{*}$는 단가 변화보다 크게 튄다.

# %%
prices = np.array([0.40, 0.494, 0.60, 1.0, 2.0, 3.0, 6.0, 15.0])
print(f"{'단가($/1M)':>12}{'c_no':>9}{'분모':>9}{'N*':>12}")
print("-" * 42)
for p in prices:
    d = c_no_per_fact(p) - c_graph_per_fact()
    n = breakeven(price_per_m=p)
    n_txt = "전환점 없음" if np.isinf(n) else f"{n:,.0f}"
    print(f"{p:>12.3f}{c_no_per_fact(p):>9.2f}{d:>9.2f}{n_txt:>12}")

# 분모가 0이 되는 임계 단가
p_crit = MAINT_PER_FACT * 1_000_000 / (TOK_PER_FACT * TURNS * KRW)
print(f"\n임계 단가 = ${p_crit:.3f}/1M 이하이면 c_no <= c_graph → N* 발산")
# 출력:
#    단가($/1M)     c_no       분모          N*
# ------------------------------------------
#        0.400     2.43    -0.57      전환점 없음
#        0.494     3.00    -0.00      전환점 없음
#        0.600     3.64     0.64      23,753
#        1.000     6.07     3.07       4,973
#        2.000    12.14     9.14       1,671
#        3.000    18.22    15.22       1,004
#        6.000    36.43    33.43         457
#       15.000    91.08    88.08         173
#
# 임계 단가 = $0.494/1M 이하이면 c_no <= c_graph → N* 발산

# %% [markdown]
# 단가가 $15에서 $0.6까지 움직이는 동안 $N^{*}$는 **173에서 23,753까지 두 자릿수 넘게** 이동한다.
# 그리고 $0.494/1M 아래에서는 **전환점이 아예 사라진다.** 엔티티를 아무리 늘려도
# 「전부 컨텍스트에 넣기」가 「그래프를 유지하기」보다 싸므로 그래프가 이길 수 없다.
# 이게 손익분기형 지표의 진짜 위험이다. 값이 흔들리는 게 아니라 **질문 자체가 무의미해진다.**

# %%
# 인건비 스윕 곡선 + 300~3,000 밴드
fig_wage = go.Figure()
w_fine = np.linspace(100_000, 1_600_000, 200)
n_fine = np.array([breakeven(wage=w) for w in w_fine])
fig_wage.add_trace(go.Scatter(x=w_fine, y=n_fine, mode="lines", name="N*"))
fig_wage.add_hrect(y0=300, y1=3000, fillcolor="orange", opacity=0.15, line_width=0,
                   annotation_text="300 ~ 3,000")
fig_wage.add_hline(y=1000, line_dash="dot", annotation_text="책의 값 1,000")
fig_wage.update_layout(title="인건비를 흔들면 전환점이 300~3,000을 훑는다",
                       xaxis_title="하루 인건비(원)", yaxis_title="N* (엔티티 수)",
                       yaxis_type="log", template="plotly_white", height=420)
_show(fig_wage)

# 토큰 단가 스윕 곡선 (발산 구간 표시)
fig_price = go.Figure()
p_fine = np.linspace(p_crit * 1.02, 15.0, 400)
np_fine = np.array([breakeven(price_per_m=p) for p in p_fine])
fig_price.add_trace(go.Scatter(x=p_fine, y=np_fine, mode="lines", name="N*"))
fig_price.add_vline(x=p_crit, line_dash="dash",
                    annotation_text=f"임계 ${p_crit:.2f}/1M — 왼쪽은 전환점 없음")
fig_price.add_hrect(y0=300, y1=3000, fillcolor="orange", opacity=0.15, line_width=0)
fig_price.update_layout(title="토큰 단가가 내려가면 분모가 말라 전환점이 발산한다",
                        xaxis_title="입력 토큰 단가($/1M)", yaxis_title="N* (엔티티 수)",
                        yaxis_type="log", xaxis_type="log", template="plotly_white", height=420)
_show(fig_price)
print("스윕 곡선 2개 생성")
# 출력: 스윕 곡선 2개 생성

# %% [markdown]
# ## 4. 격자 — 인건비 × 토큰 단가
#
# 두 가격은 독립적으로 움직인다. 조직마다 (인건비, 단가) 좌표가 다르고
# 그 좌표에 따라 $\log_{10} N^{*}$가 2.5(=316)에서 3.5(=3,162)를 오간다.
# 격자 안에서 「1,000」은 **하나의 등고선**일 뿐이다.

# %%
w_grid = np.array([150_000, 250_000, 400_000, 600_000, 900_000, 1_400_000])
p_grid = np.array([0.6, 1.0, 2.0, 3.0, 6.0, 12.0])
Z = np.array([[breakeven(price_per_m=p, wage=w) for w in w_grid] for p in p_grid])

header = "단가 / 인건비"
print(f"{header:>13}" + "".join(f"{w // 1000:>9}k" for w in w_grid))
print("-" * 72)
for i, p in enumerate(p_grid):
    row = "".join("      inf" if np.isinf(v) else f"{v:>10,.0f}" for v in Z[i])
    print(f"{p:>11.1f}" + row)

finite = Z[np.isfinite(Z)]
print(f"\n격자 내 N* 범위: {finite.min():,.0f} ~ {finite.max():,.0f}  "
      f"({finite.max() / finite.min():.0f}배)")
in_band = ((finite >= 300) & (finite <= 3000)).sum()
print(f"300~3,000 밴드 안: {in_band}/{finite.size} 칸")
# 출력:
#      단가 / 인건비      150k      250k      400k      600k      900k     1400k
# ------------------------------------------------------------------------
#         0.6     1,671     3,564     9,831   424,383       inf       inf
#         1.0       886     1,671     3,328     7,416    40,923       inf
#         2.0       408       718     1,254     2,146     4,078    11,426
#         3.0       265       457       773     1,254     2,146     4,358
#         6.0       129       219       359       558       886     1,526
#        12.0        64       107       173       265       408       664
#
# 격자 내 N* 범위: 64 ~ 424,383  (6663배)
# 300~3,000 밴드 안: 17/33 칸

# %%
Zlog = np.where(np.isfinite(Z), np.log10(np.clip(Z, 1, None)), np.nan)
fig_grid = go.Figure(
    go.Heatmap(
        z=Zlog,
        x=[f"{w // 1000}k" for w in w_grid],
        y=[f"${p:g}" for p in p_grid],
        colorscale="RdBu",
        colorbar=dict(title="log10 N*"),
        hovertemplate="인건비 %{x}/일, 단가 %{y}/1M → N*=10^%{z:.2f}<extra></extra>",
    )
)
fig_grid.update_layout(title="log10 N* — 흰 칸(NaN)은 전환점이 없는 구간",
                       xaxis_title="하루 인건비", yaxis_title="입력 토큰 단가($/1M)",
                       template="plotly_white", height=420)
_show(fig_grid)
print("히트맵 생성")
# 출력: 히트맵 생성

# %% [markdown]
# ## 5. 왜 다른 지표는 안 흔들리나 — 탄력도로 비교
#
# 탄력도 $\varepsilon = \dfrac{\partial \ln (\text{지표})}{\partial \ln (\text{입력})}$
# 가 「입력이 1% 흔들리면 지표가 몇 % 흔들리나」다.
#
# - **그래프 전환점**: 인건비에 대해 $\varepsilon \approx 1$, 토큰 단가에 대해
#   $\varepsilon = -\dfrac{c_{no}}{c_{no}-c_{graph}}$. 분모가 작아지면 무한히 커진다.
# - **체크포인터 배수** $t_{disk}/t_{mem}$: 하드웨어가 전반적으로 $k$배 빨라지면
#   분자·분모가 **함께** 변해 $k$가 약분된다. $\varepsilon = 0$.
# - **모델 호출 비중** $s = \dfrac{t_{model}}{t_{model}+t_{rest}}$:
#   $\varepsilon = 1 - s$. $s = 0.948$이면 0.05. 게다가 값이 $[0,1]$에 갇혀 있다.

# %%
def eps_breakeven_price(price_per_m=PRICE_PER_M):
    cn = c_no_per_fact(price_per_m)
    return -cn / (cn - c_graph_per_fact())


def eps_share(s):
    return 1 - s


rows = [
    ("그래프 전환점 (인건비)", 1.02, "분자가 인건비 그 자체"),
    ("그래프 전환점 (토큰 단가)", abs(eps_breakeven_price()), "분모가 두 값의 차이"),
    ("그래프 전환점 (단가 $0.6)", abs(eps_breakeven_price(0.6)), "분모가 0에 접근 → 폭주"),
    ("체크포인터 배수", 0.0, "공통 인자 약분"),
    ("모델 호출 비중 94.8%", eps_share(0.948), "값이 [0,1]에 갇힘"),
]
print(f"{'지표':<28}{'|탄력도|':>9}  이유")
print("-" * 70)
for name, e, why in rows:
    print(f"{name:<28}{e:>9.2f}  {why}")

# 10분의 1 충격을 넣어 본다
print("\n[모델 지연이 10분의 1이 되면] 비중 94.8% →", end=" ")
t_model, t_rest = 0.948, 0.052
print(f"{(t_model / 10) / (t_model / 10 + t_rest):.1%}  (35장 반증 조건: 60% 아래)")
print("[토큰 단가가 10분의 1이 되면] N* 1,004 →", end=" ")
n10 = breakeven(price_per_m=PRICE_PER_M / 10)
print("전환점 없음" if np.isinf(n10) else f"{n10:,.0f}")
# 출력:
# 지표                              |탄력도|  이유
# ----------------------------------------------------------------------
# 그래프 전환점 (인건비)                    1.02  분자가 인건비 그 자체
# 그래프 전환점 (토큰 단가)                  1.20  분모가 두 값의 차이
# 그래프 전환점 (단가 $0.6)                5.66  분모가 0에 접근 → 폭주
# 체크포인터 배수                         0.00  공통 인자 약분
# 모델 호출 비중 94.8%                   0.05  값이 [0,1]에 갇힘
#
# [모델 지연이 10분의 1이 되면] 비중 94.8% → 64.6%  (35장 반증 조건: 60% 아래)
# [토큰 단가가 10분의 1이 되면] N* 1,004 → 전환점 없음

# %% [markdown]
# 같은 「10분의 1」 충격에 대해 모델 호출 비중은 94.8% → 64.6%로 **자릿수를 유지**하고,
# 그래프 전환점은 **전환점 자체가 사라진다.** 35장이 앞의 두 개는 자릿수째로 이식된다고 하고
# 마지막 것만 주의 칸을 붙인 이유가 이 한 줄에 다 있다.

# %%
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=("① 인건비 → N* (300~3,000 밴드)",
                    "② 토큰 단가 → N* (임계 아래는 전환점 없음)",
                    "③ log10 N* 격자 (인건비 × 단가)",
                    "④ 입력 1% 변화에 대한 |탄력도|"),
    specs=[[{"type": "xy"}, {"type": "xy"}], [{"type": "heatmap"}, {"type": "xy"}]],
    vertical_spacing=0.16, horizontal_spacing=0.12,
)

fig.add_trace(go.Scatter(x=w_fine, y=n_fine, mode="lines",
                         line=dict(color="#2b6cb0", width=3), showlegend=False), row=1, col=1)
fig.add_hrect(y0=300, y1=3000, fillcolor="orange", opacity=0.15, line_width=0, row=1, col=1)
fig.add_hline(y=1000, line_dash="dot", line_color="#c05621", row=1, col=1)

fig.add_trace(go.Scatter(x=p_fine, y=np_fine, mode="lines",
                         line=dict(color="#b83280", width=3), showlegend=False), row=1, col=2)
fig.add_hrect(y0=300, y1=3000, fillcolor="orange", opacity=0.15, line_width=0, row=1, col=2)
fig.add_vline(x=p_crit, line_dash="dash", line_color="#c53030", row=1, col=2)

fig.add_trace(go.Heatmap(z=Zlog, x=[f"{w // 1000}k" for w in w_grid],
                         y=[f"${p:g}" for p in p_grid], colorscale="RdBu",
                         colorbar=dict(title="log10 N*", len=0.42, y=0.2)), row=2, col=1)

fig.add_trace(go.Bar(x=[r[0] for r in rows], y=[r[1] for r in rows],
                     marker_color=["#2b6cb0", "#b83280", "#c53030", "#2f855a", "#2f855a"],
                     text=[f"{r[1]:.2f}" for r in rows], textposition="outside",
                     showlegend=False), row=2, col=2)

fig.update_yaxes(type="log", title_text="N*", row=1, col=1)
fig.update_xaxes(title_text="하루 인건비(원)", row=1, col=1)
fig.update_yaxes(type="log", title_text="N*", row=1, col=2)
fig.update_xaxes(type="log", title_text="단가($/1M)", row=1, col=2)
fig.update_xaxes(title_text="하루 인건비", row=2, col=1)
fig.update_yaxes(title_text="단가($/1M)", row=2, col=1)
fig.update_yaxes(title_text="|탄력도|", row=2, col=2)
fig.update_xaxes(tickangle=-20, row=2, col=2)
fig.update_layout(height=860, width=1180, template="plotly_white",
                  title_text="그래프 전환점 1,000개 — 자릿수가 흔들리는 지표의 해부")

_show(fig)
fig.write_image("expy.png", scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# | 지표 | 형태 | 자릿수 이식 |
# |---|---|---|
# | 체크포인터 2배 (21장) | 비율 $t_{disk}/t_{mem}$ | 된다 — 공통 인자 약분 |
# | 모델 호출 90% (33장) | 경계 있는 비율, $\varepsilon = 1-s$ | 된다 — $[0,1]$에 갇힘 |
# | **그래프 전환점 1,000개 (27장)** | **차이의 역수** $\dfrac{C_{fixed}/H}{c_{no}-c_{graph}}$ | **안 된다 — 300일 수도 3,000일 수도** |
#
# 그래서 이 지표에서 가져갈 것은 **1,000이라는 수가 아니라 식**이다.
# 자기 인건비, 자기 토큰 단가, 자기 회수 기간, 자기 엔티티당 유지비를 꽂아서 다시 계산한다.
# 계산 자체는 청구서 한 장이면 되고, 35장 말대로 「다시 재는 데 하루면」 된다.
#
# 그리고 흔들리지 않는 결론이 하나 남는다. **처음부터 그래프로 가지 말 것.**
# 평평한 목록으로 시작하고 하루 비용이 눈에 띌 때 옮긴다. 옮기는 데 이틀이다.
# 흔들리는 것은 「언제」이고, 「어떤 순서로」는 흔들리지 않는다.
