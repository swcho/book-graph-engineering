# %% [markdown]
# # 제일 느린 것과 제일 아픈 것은 다르다
#
# `ex4_hot_query.py` 의 워크로드를 그대로 옮겨서
# **1회 지연 순위**와 **총 시간 순위**를 나란히 계산한다.
#
# 핵심 지표는 하나뿐이다.
#
# $$ T_{\text{total}} = L \times N $$
#
# - $L$ : 1회 지연(latency, ms)
# - $N$ : 하루 호출 수(calls/day)
# - $T_{\text{total}}$ : 하루 총 점유 시간
#
# 시간으로 환산하면
#
# $$ T_{\text{hours}} = \frac{L_{\text{ms}} \times N}{1000 \times 3600} $$
#
# $L$ 만 보면 «제일 느린 것»이 1등이고, $L \times N$ 을 보면 «제일 아픈 것»이 1등이다.
# 이 둘이 뒤집히는 것이 이 절의 전부다.

# %%
import plotly.graph_objects as go


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# ex4_hot_query.py 의 QUERIES 를 그대로 옮긴 것
QUERIES = [
    # 이름                    1회 ms   하루 호출 수
    ("팀 구성원 조회",            2.1,   4_200_000),
    ("2홉 이웃 탐색",           18.0,     140_000),
    ("전체 조직도 렌더",        820.0,       1_400),
    ("사용자 권한 계산",          3.4,   2_800_000),
    ("월간 감사 리포트",      12_000.0,          30),
    ("이름으로 사람 찾기",        1.2,   6_100_000),
    ("커뮤니티 탐지",         31_000.0,           2),
]

rows = [(name, ms, n, ms * n / 1000 / 3600) for name, ms, n in QUERIES]
TOTAL = sum(r[3] for r in rows)
print(f"쿼리 {len(rows)}개, 하루 총 시간 {TOTAL:,.2f}h")
# 출력: 쿼리 7개, 하루 총 시간 8.26h

# %% [markdown]
# ## 1. 두 순위를 나란히 놓는다
#
# 왼쪽은 «1회 지연»으로 줄 세운 것 — 느린 쿼리 로그가 보여 주는 세계.
# 오른쪽은 «총 시간»으로 줄 세운 것 — 인프라 청구서가 보는 세계.

# %%
by_lat = sorted(rows, key=lambda r: -r[1])
by_tot = sorted(rows, key=lambda r: -r[3])

rank_lat = {r[0]: i + 1 for i, r in enumerate(by_lat)}
rank_tot = {r[0]: i + 1 for i, r in enumerate(by_tot)}

print(f"{'#':>2}  {'[1회 지연 순]':<22}{'ms':>10}   |   {'[총 시간 순]':<22}{'h':>7}{'비중':>7}")
print("-" * 88)
for i in range(len(rows)):
    a = by_lat[i]
    b = by_tot[i]
    print(f"{i + 1:>2}  {a[0]:<20}{a[1]:>12,.1f}   |   {b[0]:<20}"
          f"{b[3]:>9,.2f}{b[3] / TOTAL:>7.0%}")
# 출력:
#  #  [1회 지연 순]                   ms   |   [총 시간 순]                 h   비중
# ----------------------------------------------------------------------------------------
#  1  커뮤니티 탐지               31,000.0   |   사용자 권한 계산            2.64    32%
#  2  월간 감사 리포트            12,000.0   |   팀 구성원 조회              2.45    30%
#  3  전체 조직도 렌더               820.0   |   이름으로 사람 찾기          2.03    25%
#  4  2홉 이웃 탐색                   18.0   |   2홉 이웃 탐색               0.70     8%
#  5  사용자 권한 계산                 3.4   |   전체 조직도 렌더            0.32     4%
#  6  팀 구성원 조회                   2.1   |   월간 감사 리포트            0.10     1%
#  7  이름으로 사람 찾기               1.2   |   커뮤니티 탐지               0.02     0%

# %% [markdown]
# ## 2. 순위가 얼마나 뒤집혔나
#
# 지연 순위 $r_L$ 과 총 시간 순위 $r_T$ 의 차이를 본다.
# 완전히 뒤집혔다면 $r_T = n + 1 - r_L$ 이 된다.

# %%
print(f"{'쿼리':<20}{'지연순위':>9}{'총시간순위':>11}{'이동':>8}")
print("-" * 50)
flips = 0
for name, ms, n, h in rows:
    d = rank_lat[name] - rank_tot[name]
    if abs(d) >= 3:
        flips += 1
    arrow = "↑" if d > 0 else ("↓" if d < 0 else "=")
    print(f"{name:<20}{rank_lat[name]:>9}{rank_tot[name]:>11}{arrow + str(abs(d)):>8}")

best_lat, worst_pain = by_lat[0], by_tot[0]
print(f"\n제일 «느린» 것 : {best_lat[0]} — {best_lat[1]:,.0f}ms × 하루 {best_lat[2]:,}회 "
      f"= {best_lat[3]:.5f}h ({best_lat[3] / TOTAL:.2%})")
print(f"제일 «아픈» 것 : {worst_pain[0]} — {worst_pain[1]:,.1f}ms × 하루 {worst_pain[2]:,}회 "
      f"= {worst_pain[3]:.2f}h ({worst_pain[3] / TOTAL:.1%})")
print(f"순위가 3계단 이상 움직인 쿼리: {flips}개 / {len(rows)}개")
# 출력:
# 쿼리                     지연순위     총시간순위      이동
# --------------------------------------------------
# 팀 구성원 조회                  6          2      ↑4
# 2홉 이웃 탐색                   4          4      =0
# 전체 조직도 렌더                3          5      ↓2
# 사용자 권한 계산                5          1      ↑4
# 월간 감사 리포트                2          6      ↓4
# 이름으로 사람 찾기               7          3      ↑4
# 커뮤니티 탐지                   1          7      ↓6
#
# 제일 «느린» 것 : 커뮤니티 탐지 — 31,000ms × 하루 2회 = 0.01722h (0.21%)
# 제일 «아픈» 것 : 사용자 권한 계산 — 3.4ms × 하루 2,800,000회 = 2.64h (32.0%)
# 순위가 3계단 이상 움직인 쿼리: 5개 / 7개

# %% [markdown]
# ## 3. 느린 쿼리 로그는 총 시간의 몇 %를 커버하나
#
# 임계값 $\theta$ 인 느린 쿼리 로그는 $L \ge \theta$ 인 쿼리만 찍는다.
# 그 로그가 커버하는 총 시간 비율은
#
# $$ C(\theta) = \frac{\sum_{i:\,L_i \ge \theta} L_i N_i}{\sum_i L_i N_i} $$
#
# 임계값을 낮출수록 커버리지는 오르지만, 100ms 근처에서는 거의 아무것도 못 잡는다.

# %%
def coverage(theta):
    hit = sum(h for _n, ms, _c, h in rows if ms >= theta)
    names = [n for n, ms, _c, _h in rows if ms >= theta]
    return hit, hit / TOTAL, names


print(f"{'임계값':>10}{'잡히는 쿼리':>8}{'커버 시간':>12}{'커버 비율':>10}   놓치는 1위")
print("-" * 74)
for theta in (10_000, 1_000, 100, 50, 10, 5, 3, 1):
    hit, ratio, names = coverage(theta)
    missed = [r for r in by_tot if r[1] < theta]
    top_missed = missed[0][0] if missed else "-"
    print(f"{theta:>10,}ms{len(names):>7}{hit:>11,.2f}h{ratio:>9.1%}   {top_missed}")

_, r100, n100 = coverage(100)
print(f"\n임계값 100ms → 찍히는 쿼리 {n100}")
print(f"  전체 총 시간의 {r100:.1%} 만 커버한다. 나머지 {1 - r100:.1%} 는 로그에 «한 줄도» 안 남는다.")
top3 = by_tot[:3]
print(f"  상위 셋({'·'.join(t[0] for t in top3)})은 {sum(t[3] for t in top3) / TOTAL:.0%} 를 먹지만")
print(f"  전부 {max(t[1] for t in top3):.1f}ms 이하라 100ms 로그에는 영원히 안 나온다.")
# 출력:
#        임계값 잡히는 쿼리       커버 시간     커버 비율   놓치는 1위
# --------------------------------------------------------------------------
#    10,000ms      2       0.12h     1.4%   사용자 권한 계산
#     1,000ms      2       0.12h     1.4%   사용자 권한 계산
#       100ms      3       0.44h     5.3%   사용자 권한 계산
#        50ms      3       0.44h     5.3%   사용자 권한 계산
#        10ms      4       1.14h    13.7%   사용자 권한 계산
#         5ms      4       1.14h    13.7%   사용자 권한 계산
#         3ms      5       3.78h    45.7%   팀 구성원 조회
#         1ms      7       8.26h   100.0%   -
#
# 임계값 100ms → 찍히는 쿼리 ['전체 조직도 렌더', '월간 감사 리포트', '커뮤니티 탐지']
#   전체 총 시간의 5.3% 만 커버한다. 나머지 94.7% 는 로그에 «한 줄도» 안 남는다.
#   상위 셋(사용자 권한 계산·팀 구성원 조회·이름으로 사람 찾기)은 86% 를 먹지만
#   전부 3.4ms 이하라 100ms 로그에는 영원히 안 나온다.

# %% [markdown]
# ## 4. 반쪽으로 줄이면 얼마가 절약되나
#
# 지연을 절반으로 줄였을 때의 절감량은 총 시간에 비례한다.
#
# $$ \Delta T = \frac{L}{2} \times N = \frac{T_{\text{total}}}{2} $$
#
# 그래서 «31초를 15초로»는 무의미하고, «3.4ms 를 1.7ms 로»가 1.3시간을 돌려준다.

# %%
print(f"{'쿼리':<20}{'현재 h':>10}{'절반으로 줄이면':>16}{'전체 대비':>10}")
print("-" * 58)
for name, ms, n, h in by_tot:
    print(f"{name:<20}{h:>10,.3f}{h / 2:>14,.5f}h{h / 2 / TOTAL:>10.2%}")
# 출력:
# 쿼리                      현재 h  절반으로 줄이면    전체 대비
# ----------------------------------------------------------
# 사용자 권한 계산              2.644       1.32222h    16.00%
# 팀 구성원 조회                2.450       1.22500h    14.82%
# 이름으로 사람 찾기             2.033       1.01667h    12.30%
# 2홉 이웃 탐색                 0.700       0.35000h     4.24%
# 전체 조직도 렌더               0.319       0.15944h     1.93%
# 월간 감사 리포트               0.100       0.05000h     0.61%
# 커뮤니티 탐지                 0.017       0.00861h     0.10%

# %% [markdown]
# ## 5. 그림 — 지연 × 호출 수 평면과 등총시간 곡선
#
# 로그-로그 평면에서 «총 시간이 같은 점들»은 직선이 된다.
#
# $$ L \cdot N = C \;\Longrightarrow\; \log N = \log C - \log L $$
#
# 기울기 $-1$ 인 대각선들이 등총시간(iso-cost) 곡선이다.
# 오른쪽 위로 갈수록 아프고, 어느 대각선 위에 있느냐가 순위를 정한다.
# 세로 점선은 느린 쿼리 로그 임계값 100ms — 그 오른쪽만 로그에 찍힌다.

# %%
import math

from plotly.subplots import make_subplots

fig = make_subplots(
    rows=1, cols=2,
    column_widths=[0.58, 0.42],
    subplot_titles=("지연 × 호출 수 (등총시간 곡선 overlay)", "하루 총 시간"),
    horizontal_spacing=0.13,
)

# --- 왼쪽: 산점도 + 등총시간 대각선 (L*N = C, 로그-로그에서 기울기 -1 직선)
X_LO, X_HI = 10 ** -0.15, 10 ** 4.85       # x축 범위
for c_hours in (0.001, 0.01, 0.1, 1.0, 3.0):
    c_ms = c_hours * 3600 * 1000           # L * N = c_ms
    fig.add_trace(go.Scatter(
        x=[X_LO, X_HI], y=[c_ms / X_LO, c_ms / X_HI], mode="lines",
        line=dict(color="rgba(130,130,150,0.5)", width=1, dash="dot"),
        hoverinfo="skip", showlegend=False), row=1, col=1)
    # 라벨은 각 선의 «오른쪽 끝» 근처에. 로그 축 annotation 은 log10 좌표를 쓴다.
    lx = 4.55                              # log10(x) = 4.55
    fig.add_annotation(x=lx, y=math.log10(c_ms) - lx, xref="x", yref="y",
                       text=f"총 {c_hours:g}h", showarrow=False,
                       xanchor="left", yanchor="bottom",
                       font=dict(size=10, color="rgba(110,110,130,0.95)"))

names = [r[0] for r in rows]
lat = [r[1] for r in rows]
cnt = [r[2] for r in rows]
hrs = [r[3] for r in rows]
# 라벨이 겹치지 않도록 점마다 위치를 흩는다
POS = {
    "팀 구성원 조회": "middle right",
    "2홉 이웃 탐색": "top center",
    "전체 조직도 렌더": "top center",
    "사용자 권한 계산": "bottom right",
    "월간 감사 리포트": "top center",
    "이름으로 사람 찾기": "top right",
    "커뮤니티 탐지": "top center",
}

fig.add_trace(go.Scatter(
    x=lat, y=cnt, mode="markers+text", text=names,
    textposition=[POS[n] for n in names],
    textfont=dict(size=11, color="#333"),
    marker=dict(size=[12 + 34 * (h / TOTAL) ** 0.5 for h in hrs],
                color=hrs, colorscale="Sunsetdark", cmin=0, cmax=max(hrs),
                line=dict(color="white", width=1.2)),
    customdata=[[h, h / TOTAL] for h in hrs],
    hovertemplate="<b>%{text}</b><br>1회 %{x:,.1f}ms<br>하루 %{y:,}회"
                  "<br>총 %{customdata[0]:.3f}h (%{customdata[1]:.1%})<extra></extra>",
    showlegend=False), row=1, col=1)

fig.add_vline(x=100, line=dict(color="crimson", width=1.5, dash="dash"),
              row=1, col=1)
# 로그 축이므로 log10 좌표: x=10^1.95≈89ms, y=10^0.35≈2.2회
fig.add_annotation(x=1.95, y=0.35, xref="x", yref="y",
                   text="느린 쿼리 로그 임계값 100ms<br>← 왼쪽은 로그에 «한 줄도» 안 남는다"
                        "<br>(그런데 총 시간의 94.7% 가 여기 있다)",
                   showarrow=False, xanchor="right", align="right",
                   font=dict(size=11, color="crimson"))

# --- 오른쪽: 총 시간 막대
bar_names = [r[0] for r in by_tot][::-1]
bar_h = [r[3] for r in by_tot][::-1]
bar_ms = [r[1] for r in by_tot][::-1]
fig.add_trace(go.Bar(
    x=bar_h, y=bar_names, orientation="h",
    marker=dict(color=["crimson" if m >= 100 else "#4C72B0" for m in bar_ms]),
    text=[f"{h:.2f}h ({h / TOTAL:.0%})" for h in bar_h],
    textposition="outside", textfont=dict(size=10),
    hovertemplate="<b>%{y}</b><br>총 %{x:.3f}h<extra></extra>",
    showlegend=False), row=1, col=2)

fig.update_xaxes(type="log", title_text="1회 지연 (ms, log)", row=1, col=1,
                 range=[-0.15, 4.85])
fig.update_yaxes(type="log", title_text="하루 호출 수 (log)", row=1, col=1,
                 range=[-0.35, 7.6])
fig.update_xaxes(title_text="하루 총 시간 (h)", row=1, col=2, range=[0, 3.5])
fig.update_layout(
    title=dict(text="제일 느린 것(오른쪽 끝) ≠ 제일 아픈 것(위쪽) — "
                    "빨강 = 100ms 로그에 찍히는 쿼리",
               font=dict(size=15)),
    template="plotly_white", width=1180, height=560,
    margin=dict(l=70, r=40, t=95, b=60),
)

fig.write_image("expy.png", scale=2)
_show(fig)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# | 관점 | 1등 | 무엇을 찾나 | 놓치는 것 |
# |---|---|---|---|
# | p99 / 느린 쿼리 로그 | 커뮤니티 탐지 (31초) | 사용자가 «기다린다»고 느끼는 것 | 총 시간의 94.7% |
# | 총 시간 $L \times N$ | 사용자 권한 계산 (2.64h, 32%) | 인프라를 «먹는» 것 | 드물지만 치명적인 지연 |
#
# - 임계값 100ms 로그는 세 쿼리만 찍고, 전체 총 시간의 **5.3%** 만 커버한다.
# - 상위 셋(권한 계산·팀 구성원·이름 찾기)이 전체의 **86%**(개별 반올림 합으로는 87%)를 먹는데
#   전부 1~3.4ms 짜리라 로그에 한 줄도 안 남는다.
# - 둘 다 봐야 하지만, **고치는 순서는 대개 총 시간이 먼저**다.
