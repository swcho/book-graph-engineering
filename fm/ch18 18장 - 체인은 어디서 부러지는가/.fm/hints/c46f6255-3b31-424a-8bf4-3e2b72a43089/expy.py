# %% [markdown]
# # 조건이 늘 때: `if` 경우의 수 vs 그래프 엣지
#
# 조건이 $n$개일 때
#
# - `if` 문 경로(경우의 수): $2^n$ — 조건마다 **두 배** (지수)
# - 그래프 엣지: $2n$ — 조건마다 **둘** (선형: 갈림길 노드 하나 + 나가는 엣지 둘)
#
# `if`는 조합을 **코드로 펼치고**, 그래프는 갈림길을 **선언**만 한다.
# 조합은 실행 시점에 만들어진다. 그래서 증가 속도가 다르다.

# %%
# 필요 패키지: plotly, kaleido (표 부분은 표준 라이브러리만으로 동작)

def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


def if_paths(n):
    """중첩 if 로 펼치면 경로가 조건마다 두 배 — 지수."""
    return 2 ** n


def graph_edges(n):
    """조건마다 갈림길 노드 하나 + 나가는 엣지 둘 — 선형."""
    return 2 * n


# %% [markdown]
# ## 1. 숫자로 비교 — 다섯 개 근처에서 사람이 다 못 본다
#
# 사람이 실제로 테스트해 보는 경로는 여덟 가지쯤이 한계다.
# 조건 5개면 $2^5 = 32$가지 — 이미 손으로 다 못 본다.

# %%
print(f"{'조건 수':>6} {'if 경우의 수 2^n':>16} {'그래프 엣지 2n':>14} {'배율(지수/선형)':>14} {'사람이 다 보나'}")
print("-" * 68)
for n in range(1, 9):
    p, e = if_paths(n), graph_edges(n)
    ok = "예" if p <= 8 else ("힘들다" if p <= 32 else "불가능")
    print(f"{n:>7} {p:>15,} {e:>15} {p / e:>13.1f}x {ok:>10}")

# 출력:
#    조건 수    if 경우의 수 2^n      그래프 엣지 2n      배율(지수/선형) 사람이 다 보나
# --------------------------------------------------------------------
#       1               2               2           1.0x          예
#       2               4               4           1.0x          예
#       3               8               6           1.3x          예
#       4              16               8           2.0x        힘들다
#       5              32              10           3.2x        힘들다
#       6              64              12           5.3x        불가능
#       7             128              14           9.1x        불가능
#       8             256              16          16.0x        불가능

# %% [markdown]
# ## 2. 조건 5개의 경우의 수를 실제로 펼쳐 보기
#
# `if` 문을 쓴다는 건 아래 32가지를 전부 코드(그리고 테스트)로 감당한다는 뜻이다.

# %%
from itertools import product

CONDITIONS = ["검색 결과 있음", "요약 길이 초과", "검토 통과", "사람 승인 필요", "재시도 남음"]
n = len(CONDITIONS)
combos = list(product([0, 1], repeat=n))
print(f"조건 {n}개 → 경우의 수 {len(combos)}가지 (그래프라면 엣지 {graph_edges(n)}개로 끝)")
for i, combo in enumerate(combos[:4], 1):
    desc = ", ".join(c for c, v in zip(CONDITIONS, combo) if v) or "(전부 아니오)"
    print(f"  {i:>2}. {desc}")
print(f"  ... 나머지 {len(combos) - 4}가지")

# 출력:
# 조건 5개 → 경우의 수 32가지 (그래프라면 엣지 10개로 끝)
#    1. (전부 아니오)
#    2. 재시도 남음
#    3. 사람 승인 필요
#    4. 사람 승인 필요, 재시도 남음
#   ... 나머지 28가지

# %% [markdown]
# ## 3. 시각화 — 지수 vs 선형
#
# 왼쪽은 선형 축: $2^n$이 폭발하는 모양이 그대로 보인다.
# 오른쪽은 로그 축: 지수($2^n$)는 직선이 되고, 선형($2n$)은 아래에서 완만하게 휜다.
# 회색 점선은 「사람이 테스트해 보는 한계 ≈ 8가지」.

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    ns = list(range(1, 9))
    paths = [if_paths(k) for k in ns]
    edges = [graph_edges(k) for k in ns]

    BLUE, ORANGE = "#2a78d6", "#eb6834"   # 검증된 범주형 팔레트 슬롯 1, 2
    INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e8e7e3"

    fig = make_subplots(
        rows=1, cols=2, horizontal_spacing=0.10,
        subplot_titles=("선형 축 — 폭발이 보인다", "로그 축 — 지수는 직선이 된다"),
    )
    for col, logy in ((1, False), (2, True)):
        fig.add_trace(go.Scatter(
            x=ns, y=paths, mode="lines+markers", name="if 경우의 수 2ⁿ (지수)",
            line=dict(color=BLUE, width=2), marker=dict(size=8),
            showlegend=(col == 1)), row=1, col=col)
        fig.add_trace(go.Scatter(
            x=ns, y=edges, mode="lines+markers", name="그래프 엣지 2n (선형)",
            line=dict(color=ORANGE, width=2), marker=dict(size=8, symbol="square"),
            showlegend=(col == 1)), row=1, col=col)
        fig.add_hline(y=8, line=dict(color=MUTED, width=1, dash="dot"), row=1, col=col)
        if logy:
            fig.update_yaxes(type="log", row=1, col=col)

    fig.add_annotation(x=7.9, y=10, text="사람이 테스트하는 한계 ≈ 8",
                       showarrow=False, xanchor="right", yanchor="bottom",
                       font=dict(size=11, color=MUTED), row=1, col=1)
    fig.add_vline(x=5, line=dict(color=MUTED, width=1, dash="dash"), row=1, col=1)
    fig.add_annotation(x=5, y=200, text="조건 5개: 32가지", showarrow=False,
                       xanchor="left", font=dict(size=11, color=MUTED), row=1, col=1)

    fig.update_layout(
        title=dict(text="조건 n개 — if 경로는 2ⁿ, 그래프 엣지는 2n", font=dict(size=16, color=INK)),
        width=900, height=430, paper_bgcolor="#fcfcfb", plot_bgcolor="#fcfcfb",
        font=dict(color=INK),
        legend=dict(orientation="h", yanchor="bottom", y=1.10, x=0),
        margin=dict(t=110, b=50, l=60, r=30),
    )
    fig.update_xaxes(title_text="조건 수 n", dtick=1, gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(title_text="개수", row=1, col=1)

    import os
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
    fig.write_image(out, scale=2)  # kaleido 필요
    print(f"저장: {out}")
    _show(fig)
except ImportError as e:
    print(f"plotly/kaleido 미설치 — 시각화 생략: {e}")

# 출력:
# 저장: .../.fm/hints/c46f6255-3b31-424a-8bf4-3e2b72a43089/expy.png

# %% [markdown]
# ## 정리
#
# $$\text{if 경로 수} = 2^n \;(\text{지수}) \qquad \text{그래프 엣지 수} = 2n \;(\text{선형})$$
#
# - `if`는 경우의 수를 코드로 **펼치고**, 그래프는 갈림길을 **선언**한다.
# - 조건 5개($2^5 = 32$) 근처에서 사람이 전 경로를 다 못 본다 — 안 해 본 경로가 운영에서 터진다.
# - 단, 조건 두세 개면 `if`가 더 읽기 쉽다. 문제는 그 뒤의 **증가 속도**다.
