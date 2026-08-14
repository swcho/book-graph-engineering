# %% [markdown]
# # 전체 재색인 vs 증분 갱신 — 비용식은 어떻게 다른가?
#
# GraphRAG 계열 파이프라인의 하루 갱신 비용을 뜯어 보면 두 방식의 차이가
# 딱 한 항에서 갈린다.
#
# - **전체 재색인**:
#   $$C_{\text{full}} = N_{\text{new}} \cdot T_{\text{ext}} + N_{\text{comm}} \cdot T_{\text{sum}}$$
# - **증분 갱신** (영향 커뮤니티 비율 $r$):
#   $$C_{\text{inc}} = N_{\text{new}} \cdot T_{\text{ext}} + \lfloor r \cdot N_{\text{comm}} \rfloor \cdot T_{\text{sum}}$$
#
# 첫째 항(신규 문서 $N_{\text{new}}$건의 엔티티 추출)은 **두 식에서 완전히 같다**.
# 새 문서는 어차피 읽어야 하니까. 갈리는 건 둘째 항 — 커뮤니티 요약을
# **전부**($N_{\text{comm}}$개) 다시 쓰느냐, **영향받은 비율만**($r \cdot N_{\text{comm}}$개)
# 다시 쓰느냐다. 차액은
# $$C_{\text{full}} - C_{\text{inc}} \approx (1-r) \cdot N_{\text{comm}} \cdot T_{\text{sum}}$$
# 이므로 절감액은 오로지 $r$이 정한다.

# %%
# 필요 패키지: plotly, kaleido (표 계산 자체는 표준 라이브러리만 사용)
import os


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# 책의 비용 모델 상수 (2026년 8월 기준 대략치)
PRICE_PER_MTOK = 4_000        # 원 / 100만 토큰
TOK_PER_DOC_EXTRACT = 1_800   # 문서 하나 엔티티 추출
TOK_PER_SUMMARY = 2_400       # 커뮤니티 요약 하나

N_DOCS, N_COMM = 40_000, 620  # 코퍼스 규모: 문서 4만 건, 커뮤니티 620개
N_NEW = 200                   # 하루 신규 문서


def won(tok):
    return tok / 1_000_000 * PRICE_PER_MTOK


def daily_full(n_new, n_comm):
    """전체 재색인: 신규 추출 + 커뮤니티 «전부» 재요약"""
    return n_new * TOK_PER_DOC_EXTRACT + n_comm * TOK_PER_SUMMARY


def daily_incremental(n_new, n_comm, r):
    """증분 갱신: 신규 추출 + 영향받은 비율 r 만 재요약"""
    return n_new * TOK_PER_DOC_EXTRACT + int(n_comm * r) * TOK_PER_SUMMARY


extract_cost = won(N_NEW * TOK_PER_DOC_EXTRACT)
print(f"공통 항 — 신규 {N_NEW}건 추출: {N_NEW * TOK_PER_DOC_EXTRACT:,} 토큰 ≈ {extract_cost:,.0f}원/일")
print(f"전체 재색인 둘째 항 — 요약 {N_COMM}개 전부: {N_COMM * TOK_PER_SUMMARY:,} 토큰 ≈ {won(N_COMM * TOK_PER_SUMMARY):,.0f}원/일")
# 출력:
# 공통 항 — 신규 200건 추출: 360,000 토큰 ≈ 1,440원/일
# 전체 재색인 둘째 항 — 요약 620개 전부: 1,488,000 토큰 ≈ 5,952원/일

# %% [markdown]
# 추출 항은 하루 1,440원으로 고정이고, 전체 재색인은 여기에 요약 5,952원이
# 매일 통째로 얹힌다. 증분은 이 5,952원에 $r$ 을 곱한 만큼만 낸다.
#
# ## 시나리오: $r$ = 3% (기대) vs 34% (실측) vs 60% (비관)
#
# 저자의 기대는 5%였지만 실측은 34%. 커뮤니티 탐지가 전역 계산이라
# 새 문서가 기존 엔티티들을 잇는 다리 역할을 하면 경계가 여기저기 흔들린다.

# %%
print(f"{'영향 비율':>8} {'전체/일':>10} {'증분/일':>10} {'절감/일':>10} {'월 절감':>12}  비고")
print("-" * 66)
for r, note in ((0.03, "장밋빛 기대"), (0.34, "실측 (기대는 5%였다)"), (0.60, "비관 시나리오")):
    f = won(daily_full(N_NEW, N_COMM))
    i = won(daily_incremental(N_NEW, N_COMM, r))
    print(f"{r*100:>7.0f}% {f:>9,.0f}원 {i:>9,.0f}원 {f-i:>9,.0f}원 {(f-i)*30:>10,.0f}원  {note}")
# 출력:
#    영향 비율       전체/일       증분/일       절감/일         월 절감  비고
# ------------------------------------------------------------------
#       3%     7,392원     1,613원     5,779원    173,376원  장밋빛 기대
#      34%     7,392원     3,456원     3,936원    118,080원  실측 (기대는 5%였다)
#      60%     7,392원     5,011원     2,381원     71,424원  비관 시나리오

# %% [markdown]
# 전체 재색인 비용은 $r$ 과 무관하게 **평평한 선**이고, 증분 비용은 $r$ 에
# 비례해 올라가 $r=1$ 에서 전체 재색인과 만난다. 3%면 증분이 압도적으로 싸고
# (일 1,613원 vs 7,392원), 60%면 별 차이가 없어진다. **영향 커뮤니티 비율이
# 전부를 정하고, 그건 재 봐야 안다.**

# %%
import plotly.graph_objects as go

ratios = [x / 100 for x in range(0, 101, 2)]
full_line = [won(daily_full(N_NEW, N_COMM)) for _ in ratios]
inc_line = [won(daily_incremental(N_NEW, N_COMM, r)) for r in ratios]

C_FULL = "#2a78d6"   # blue
C_INC = "#eb6834"    # orange
C_INK = "#454545"

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=[r * 100 for r in ratios], y=full_line, mode="lines",
    name="전체 재색인", line=dict(color=C_FULL, width=2)))
fig.add_trace(go.Scatter(
    x=[r * 100 for r in ratios], y=inc_line, mode="lines",
    name="증분 갱신", line=dict(color=C_INC, width=2)))

for r, label in ((0.03, "3% 기대"), (0.34, "34% 실측"), (0.60, "60% 비관")):
    y = won(daily_incremental(N_NEW, N_COMM, r))
    fig.add_trace(go.Scatter(
        x=[r * 100], y=[y], mode="markers+text", showlegend=False,
        marker=dict(color=C_INC, size=10, line=dict(color="#ffffff", width=2)),
        text=[f"{label}<br>{y:,.0f}원"], textposition="bottom right",
        textfont=dict(size=11, color=C_INK)))

fig.add_annotation(x=50, y=full_line[0], text="전체 재색인 (r과 무관)", yshift=12,
                   showarrow=False, font=dict(size=11, color=C_FULL))
fig.update_layout(
    title="하루 갱신 비용 — 영향 커뮤니티 비율 r이 전부를 정한다",
    xaxis=dict(title="영향 커뮤니티 비율 r (%)", ticksuffix="%", gridcolor="#e8e8e8"),
    yaxis=dict(title="하루 비용 (원)", gridcolor="#e8e8e8", rangemode="tozero"),
    plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
    font=dict(color=C_INK),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    width=820, height=480, margin=dict(t=90))

_show(fig)
fig.write_image(os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png"), scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# | 항 | 전체 재색인 | 증분 갱신 |
# |---|---|---|
# | 신규 문서 추출 $N_{\text{new}} \cdot T_{\text{ext}}$ | 낸다 | **똑같이** 낸다 |
# | 커뮤니티 요약 | $N_{\text{comm}}$개 **전부** | $r \cdot N_{\text{comm}}$개 (영향분만) |
#
# 즉 두 비용식의 차이는 요약 항 하나뿐이고, 그 크기를 정하는 $r$은
# 설계로 정하는 값이 아니라 **측정해야 아는 값**이다 — 그리고 대개
# 생각보다 크다 (기대 5% → 실측 34%).
