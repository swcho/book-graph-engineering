# %% [markdown]
# # RRF(Reciprocal Rank Fusion) 점수 계산식
#
# 여러 검색 엔진이 낸 랭킹을 **점수 없이 순위만으로** 합치는 방법.
#
# $$\text{RRF}(d) = \sum_{r \in \text{랭킹들}} \frac{1}{k + \text{pos}_r(d)}$$
#
# - $\text{pos}_r(d)$: 랭킹 $r$에서 문서 $d$의 순위 (1위, 2위, …)
# - $k$: 상위권 점수 차를 완만하게 만드는 상수. **관례적으로 60**을 쓴다.
#
# 아래에서 (1) 손 계산, (2) 책의 예제(융합이 이기는 경우), (3) $k$의 효과,
# (4) 융합이 지는 경우를 차례로 확인한다.

# %%
from collections import defaultdict


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


def rrf_scores(*rankings, k=60):
    """각 랭킹의 순위 pos에 대해 1/(k+pos)를 누적한다."""
    score = defaultdict(float)
    for r in rankings:
        for pos, item in enumerate(r, 1):  # 순위는 1부터
            score[item] += 1 / (k + pos)
    return dict(score)


def rrf(*rankings, k=60):
    s = rrf_scores(*rankings, k=k)
    return sorted(s, key=lambda x: -s[x])


# %% [markdown]
# ## 1. 손 계산: 세 문서, 두 랭킹
#
# | 순위 | 벡터 | 그래프 |
# |---|---|---|
# | 1 | A | B |
# | 2 | C | C |
# | 3 | B | A |
#
# $k=60$이면
# $\text{A}=\frac{1}{61}+\frac{1}{63}$, $\text{B}=\frac{1}{63}+\frac{1}{61}$,
# $\text{C}=\frac{1}{62}+\frac{1}{62}$.
# **양쪽 모두 2위**인 C가 "1위+3위"인 A, B와 사실상 동점이 된다.

# %%
scores = rrf_scores(["A", "C", "B"], ["B", "C", "A"], k=60)
for d, s in sorted(scores.items(), key=lambda x: -x[1]):
    print(f"{d}: {s:.6f}")
# 출력:
# A: 0.032266
# B: 0.032266
# C: 0.032258

# %% [markdown]
# ## 2. 책의 예제: 두 엔진 모두 1위가 오답인데, 융합하면 1위가 정답
#
# 각 엔진이 "두 번째로 확신하는 것"(d02, d09)이 서로 겹치기 때문이다.

# %%
VECTOR_RANK = ["d11", "d01", "d09", "d05", "d02"]
GRAPH_RANK = ["d12", "d02", "d06", "d09", "d03"]
GOLD = {"d01", "d02", "d06", "d09"}  # 사람이 확인한 정답 문서


def prec_at(ranked, n):
    return len(set(ranked[:n]) & GOLD) / n


fused = rrf(VECTOR_RANK, GRAPH_RANK, k=60)
print("벡터  :", VECTOR_RANK)
print("그래프:", GRAPH_RANK)
print("융합  :", fused)
print()
print(f"{'방식':<8} {'P@1':>5} {'P@2':>5} {'P@3':>5} {'P@4':>5}")
for name, r in (("벡터", VECTOR_RANK), ("그래프", GRAPH_RANK), ("융합", fused)):
    print(f"{name:<8}" + "".join(f"{prec_at(r, n):>6.2f}" for n in (1, 2, 3, 4)))
# 출력:
# 벡터  : ['d11', 'd01', 'd09', 'd05', 'd02']
# 그래프: ['d12', 'd02', 'd06', 'd09', 'd03']
# 융합  : ['d02', 'd09', 'd11', 'd12', 'd01', 'd06', 'd05', 'd03']
#
# 방식      P@1   P@2   P@3   P@4
# 벡터      0.00  0.50  0.67  0.50
# 그래프    0.00  0.50  0.67  0.75
# 융합      1.00  1.00  0.67  0.50

# %% [markdown]
# ## 3. $k$의 효과: 곡선 $\frac{1}{k+\text{pos}}$의 기울기
#
# - $k$가 작으면 1위 점수가 압도적 → 한 엔진의 "확신"이 결과를 지배.
# - $k$가 크면 순위 간 차이가 완만 → 여러 엔진의 "합의"가 이긴다.
#
# 예: 1위/2위 점수 비율은 $k=0$일 때 $2.0$, $k=60$일 때 $\frac{62}{61}\approx1.016$.

# %%
for k in (0, 5, 60, 300):
    r = (1 / (k + 1)) / (1 / (k + 2))
    print(f"k={k:>3}: 1위/2위 점수 비율 = {r:.3f}")
# 출력:
# k=  0: 1위/2위 점수 비율 = 2.000
# k=  5: 1위/2위 점수 비율 = 1.167
# k= 60: 1위/2위 점수 비율 = 1.016
# k=300: 1위/2위 점수 비율 = 1.003

# %%
# k에 따라 융합 순위 자체가 바뀔 수 있다.
# X는 벡터에서만 1위, Y는 양쪽에서 2위/3위.
V = ["X", "Y", "a", "b"]
G = ["c", "d", "Y", "e"]
for k in (0, 60):
    s = rrf_scores(V, G, k=k)
    order = sorted(s, key=lambda x: -s[x])
    print(f"k={k:>2}: 1위={order[0]}  (X={s['X']:.4f}, Y={s['Y']:.4f})")
# 출력:
# k= 0: 1위=X  (X=1.0000, Y=0.8333)
# k=60: 1위=Y  (X=0.0164, Y=0.0320)
# k=0에서는 벡터의 "확신"(X 1위)이 이기고,
# k=60에서는 양쪽의 "합의"(Y가 두 랭킹 모두 상위)가 이긴다.

# %% [markdown]
# ## 4. 융합이 항상 이기지는 않는다
#
# 한쪽 엔진만 아는 정답은 항이 하나뿐이라 순위가 내려간다.
# RRF는 «둘 다 상위에 올린 것»을 밀어 올리는 방식이기 때문이다.

# %%
V = ["정답", "n1", "n2"]        # 벡터만 정답을 1위로 안다
G = ["n1", "n2", "n3"]          # 그래프는 정답을 아예 못 찾음
f = rrf(V, G, k=60)
print("벡터:", V, "→ 융합:", f)
print("정답의 위치: 벡터 1위 → 융합", f.index("정답") + 1, "위")
# 출력:
# 벡터: ['정답', 'n1', 'n2'] → 융합: ['n1', 'n2', '정답', 'n3']
# 정답의 위치: 벡터 1위 → 융합 3 위

# %% [markdown]
# ## 5. 시각화
#
# 왼쪽: 순위별 기여 점수 $\frac{1}{k+\text{pos}}$ 를 1위 기준으로 정규화한 곡선.
# $k$가 클수록 곡선이 평평해져 상위권 특혜가 사라진다.
#
# 오른쪽: 책 예제의 문서별 RRF 점수 분해(벡터 기여 + 그래프 기여, $k=60$).
# 양쪽에서 모두 점수를 받은 d02, d09가 1·2위로 올라선다.

# %%
# 필요 패키지: plotly, kaleido
import os

import plotly.graph_objects as go
from plotly.subplots import make_subplots

C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"  # 벡터, 그래프, 강조
SURFACE, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"

fig = make_subplots(
    cols=2, rows=1, horizontal_spacing=0.12,
    subplot_titles=("순위별 기여 점수 (1위=1로 정규화)", "책 예제의 RRF 점수 분해 (k=60)"),
)

# 왼쪽: 1/(k+pos) 정규화 곡선
positions = list(range(1, 21))
for k, color in ((0, C1), (10, C2), (60, C3)):
    ys = [(1 / (k + p)) / (1 / (k + 1)) for p in positions]
    fig.add_trace(
        go.Scatter(x=positions, y=ys, mode="lines", name=f"k={k}",
                   line=dict(color=color, width=2), legendgroup="k"),
        row=1, col=1,
    )

# 오른쪽: 문서별 기여 누적 막대
k = 60
docs = rrf(VECTOR_RANK, GRAPH_RANK, k=k)
vec_part = [1 / (k + VECTOR_RANK.index(d) + 1) if d in VECTOR_RANK else 0 for d in docs]
gra_part = [1 / (k + GRAPH_RANK.index(d) + 1) if d in GRAPH_RANK else 0 for d in docs]
fig.add_trace(
    go.Bar(x=docs, y=vec_part, name="벡터 기여", marker_color=C1,
           marker_line=dict(color=SURFACE, width=2)),
    row=1, col=2,
)
fig.add_trace(
    go.Bar(x=docs, y=gra_part, name="그래프 기여", marker_color=C2,
           marker_line=dict(color=SURFACE, width=2)),
    row=1, col=2,
)
# 정답 문서 표시
for i, d in enumerate(docs):
    if d in GOLD:
        fig.add_annotation(x=i, y=vec_part[i] + gra_part[i], text="정답",
                           showarrow=False, yshift=12, font=dict(color=INK2, size=11),
                           row=1, col=2)

fig.update_layout(
    barmode="stack",
    title=dict(text="RRF: score(d) = Σ 1/(k + pos)", font=dict(color=INK, size=17)),
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
    font=dict(color=INK2, size=12),
    width=980, height=430,
    legend=dict(orientation="h", y=-0.18),
    margin=dict(t=90),
)
fig.update_xaxes(title_text="순위 pos", row=1, col=1, gridcolor="#e8e8e5", zeroline=False)
fig.update_yaxes(title_text="상대 점수", row=1, col=1, gridcolor="#e8e8e5", zeroline=False)
fig.update_xaxes(title_text="융합 순위 순 문서", row=1, col=2, showgrid=False)
fig.update_yaxes(title_text="RRF 점수", row=1, col=2, gridcolor="#e8e8e5", zeroline=False)

_show(fig)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(out, scale=2)
print("saved:", out)
# 출력: saved: .../.fm/hints/9c302055-8d93-4547-880e-62d6a0c9a4d0/expy.png
