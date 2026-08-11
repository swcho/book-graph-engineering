# %% [markdown]
# # `ex4_bipartite.py`의 `project()` — 이분 그래프 투영
#
# **질문:** `project()` 함수는 무엇을 계산하는가?
#
# **답:** 한쪽으로 투영해 **같은 상대를 공유하는 노드끼리 잇고**, **공유한 상대 수를 엣지 가중치로** 센다.
#
# 이분 그래프(bipartite graph)는 노드가 두 종류로 나뉘고 엣지가 **항상 서로 다른 종류 사이에만**
# 놓이는 그래프다. 여기서는 `사용자`와 `상품`, 엣지는 «구매».
#
# $$V = U \sqcup I, \qquad E \subseteq U \times I$$
#
# 사용자끼리도, 상품끼리도 직접 이어진 엣지가 없다. 그런데 우리가 정작 묻고 싶은 건
# 「이 상품과 **같이** 팔리는 상품은?」처럼 **한 종류 안에서의** 관계다.
# 그래서 한쪽 종류만 남기고 접는다. 이게 **투영(projection)**.
#
# $$w(x, y) = \bigl|\; N(x) \cap N(y) \;\bigr|$$
#
# $N(x)$는 $x$의 이웃 집합(= 상대편 종류의 노드들). 두 노드의 이웃 집합이 겹치면 잇고,
# **겹친 개수**가 가중치다. 겹치는 게 없으면 엣지 자체가 없다.

# %%
# 필요 패키지: plotly, kaleido  (PNG 저장용. 개념 계산 부분은 표준 라이브러리만 사용)
from collections import defaultdict
from itertools import combinations


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# 원본 이분 그래프: (사용자, 상품) 구매 기록
PURCHASES = [
    ("u1", "상품A"), ("u1", "상품B"),
    ("u2", "상품A"), ("u2", "상품B"), ("u2", "상품C"),
    ("u3", "상품C"),
]

print("원본 이분 그래프 (사용자 3, 상품 3, 엣지 %d)" % len(PURCHASES))
for p in PURCHASES:
    print("  ", p)
# 출력:
# 원본 이분 그래프 (사용자 3, 상품 3, 엣지 6)
#    ('u1', '상품A')
#    ('u1', '상품B')
#    ('u2', '상품A')
#    ('u2', '상품B')
#    ('u2', '상품C')
#    ('u3', '상품C')

# %% [markdown]
# ## 1단계 — `project()` 원문과 두 줄의 뜻
#
# ```python
# def project(pairs, side=1):
#     """한쪽으로 투영. 같은 상대를 공유하면 잇는다."""
#     grouped = defaultdict(set)
#     for a, b in pairs:
#         key, val = (a, b) if side == 0 else (b, a)
#         grouped[val].add(key)
#     out = defaultdict(int)
#     for val, keys in grouped.items():
#         for x, y in combinations(sorted(keys), 2):
#             out[(x, y)] += 1
#     return dict(out)
# ```
#
# 읽는 순서가 헷갈리기 쉬운 곳은 `key, val` 뒤집기 한 줄이다.
#
# | `side` | 살아남는 쪽(`key`) | 접히는 쪽(`val`, 그룹 기준) | 결과 엣지 |
# |---|---|---|---|
# | `1` | `b` = 상품 | `a` = 사용자 | 상품 — 상품 |
# | `0` | `a` = 사용자 | `b` = 상품 | 사용자 — 사용자 |
#
# 즉 `side`는 **투영 후에 남길 튜플 위치**다. `grouped`는 「접히는 쪽 노드 → 그 노드의 이웃 집합」,
# 즉 $N(\cdot)$ 그 자체다. 그리고 `combinations(..., 2)`가 그 이웃 집합 안의 **모든 쌍**을 잇는다.
#
# 한 그룹은 크기 $k$의 **클리크(clique)** 하나를 만든다 — 여기서 엣지 폭발이 시작된다.
#
# $$\binom{k}{2} = \frac{k(k-1)}{2}$$

# %%
def project(pairs, side=1):
    """한쪽으로 투영. 같은 상대를 공유하면 잇는다."""
    grouped = defaultdict(set)
    for a, b in pairs:
        key, val = (a, b) if side == 0 else (b, a)
        grouped[val].add(key)
    out = defaultdict(int)
    for val, keys in grouped.items():
        for x, y in combinations(sorted(keys), 2):
            out[(x, y)] += 1
    return dict(out)


def grouped_of(pairs, side=1):
    """중간 산물 grouped 만 따로 꺼내 본다 (= 이웃 집합 N(·))."""
    g = defaultdict(set)
    for a, b in pairs:
        key, val = (a, b) if side == 0 else (b, a)
        g[val].add(key)
    return {k: sorted(v) for k, v in g.items()}


print("side=1 의 grouped  (사용자 → 그 사람이 산 상품 집합)")
for k, v in grouped_of(PURCHASES, side=1).items():
    print(f"   {k}: {v}   → 쌍 {len(v) * (len(v) - 1) // 2}개 생성")
# 출력:
# side=1 의 grouped  (사용자 → 그 사람이 산 상품 집합)
#    u1: ['상품A', '상품B']   → 쌍 1개 생성
#    u2: ['상품A', '상품B', '상품C']   → 쌍 3개 생성
#    u3: ['상품C']   → 쌍 0개 생성

# %% [markdown]
# ## 2단계 — 상품 쪽 투영 (`side=1`)
#
# `u1`이 만든 쌍 1개와 `u2`가 만든 쌍 3개를 **합산**한다. 같은 쌍이 여러 그룹에서
# 반복되면 `out[(x, y)] += 1`이 누적된다 — 이 누적값이 곧 **공유한 상대 수**다.
#
# $$w(\text{상품A}, \text{상품B}) = |\{u_1, u_2\} \cap \{u_1, u_2\}| = 2$$

# %%
proj_item = project(PURCHASES, side=1)
print("상품 쪽 투영 (함께 산 상품끼리 잇기)")
for (a, b), w in sorted(proj_item.items()):
    print(f"   {a} — {b}  (함께 산 사람 {w}명)")
print(f"   엣지 {len(proj_item)}개  (원본은 {len(PURCHASES)}개)")
# 출력:
# 상품 쪽 투영 (함께 산 상품끼리 잇기)
#    상품A — 상품B  (함께 산 사람 2명)
#    상품A — 상품C  (함께 산 사람 1명)
#    상품B — 상품C  (함께 산 사람 1명)
#    엣지 3개  (원본은 6개)

# %%
# 정의식과 직접 대조: w(x,y) = |N(x) ∩ N(y)|
buyers = defaultdict(set)
for u, i in PURCHASES:
    buyers[i].add(u)

print("정의식으로 다시 계산")
for x, y in combinations(sorted(buyers), 2):
    shared = buyers[x] & buyers[y]
    print(f"   {x} ∩ {y} = {sorted(shared) or '없음'}  → w={len(shared)}"
          f"   (project 결과: {proj_item.get((x, y), 0)})")
# 출력:
# 정의식으로 다시 계산
#    상품A ∩ 상품B = ['u1', 'u2']  → w=2   (project 결과: 2)
#    상품A ∩ 상품C = ['u2']  → w=1   (project 결과: 1)
#    상품B ∩ 상품C = ['u2']  → w=1   (project 결과: 1)

# %% [markdown]
# ## 3단계 — 반대쪽 투영 (`side=0`)
#
# 같은 함수, 인자 하나만 바꾸면 **사용자 유사도 그래프**가 나온다.
# 「같은 상품을 산 사용자끼리 잇고, 겹친 상품 수를 가중치로」.
# 추천 시스템의 item-item / user-user 협업 필터링이 정확히 이 두 투영이다.

# %%
proj_user = project(PURCHASES, side=0)
print("사용자 쪽 투영 (같은 상품을 산 사람끼리 잇기)")
for (a, b), w in sorted(proj_user.items()):
    print(f"   {a} — {b}  (함께 산 상품 {w}개)")
print(f"   엣지 {len(proj_user)}개")
print("   u1 — u3 은 없다: 겹치는 상품이 0개라 엣지 자체가 안 생긴다.")
# 출력:
# 사용자 쪽 투영 (같은 상품을 산 사람끼리 잇기)
#    u1 — u2  (함께 산 상품 2개)
#    u2 — u3  (함께 산 상품 1개)
#    엣지 2개
#    u1 — u3 은 없다: 겹치는 상품이 0개라 엣지 자체가 안 생긴다.

# %% [markdown]
# ## 4단계 — 투영은 **비가역**이다 (버려지는 정보)
#
# `상품A — 상품B (2)`만 보면 **누가** 샀는지 알 수 없다. 접힌 쪽 노드가 사라졌기 때문이다.
# 서로 다른 원본 이분 그래프가 **같은 투영**을 낼 수 있다는 걸 직접 확인해 보자.

# %%
ALT = [
    ("v1", "상품A"), ("v1", "상품B"),
    ("v2", "상품A"), ("v2", "상품B"), ("v2", "상품C"),
    ("v3", "상품C"),
]  # 사용자 이름만 다른 그래프

MERGED = [
    ("w1", "상품A"), ("w1", "상품B"), ("w1", "상품C"),
    ("w2", "상품A"), ("w2", "상품B"),
]  # 구조 자체가 다른 그래프 (엣지 5개)

print("PURCHASES 투영:", dict(sorted(project(PURCHASES, 1).items())))
print("ALT       투영:", dict(sorted(project(ALT, 1).items())))
print("MERGED    투영:", dict(sorted(project(MERGED, 1).items())))
print("→ 셋 다 같은 투영. 원본을 되돌릴 수 없다.")
# 출력:
# PURCHASES 투영: {('상품A', '상품B'): 2, ('상품A', '상품C'): 1, ('상품B', '상품C'): 1}
# ALT       투영: {('상품A', '상품B'): 2, ('상품A', '상품C'): 1, ('상품B', '상품C'): 1}
# MERGED    투영: {('상품A', '상품B'): 2, ('상품A', '상품C'): 1, ('상품B', '상품C'): 1}
# → 셋 다 같은 투영. 원본을 되돌릴 수 없다.

# %% [markdown]
# ## 5단계 — 엣지 제곱 폭발
#
# `simulate()`가 계산하는 건 투영 엣지 수의 **상한**이다.
# 사용자 $n$명이 각각 $k$개를 샀다면 각자 클리크 하나씩:
#
# $$E_{\text{proj}} \le n \cdot \binom{k}{2} = \frac{n\,k(k-1)}{2} \;=\; O(nk^2)$$
#
# 사용자 수에는 **선형**, 1인당 구매 수에는 **제곱**이다. $k$가 무섭다.
# (별도의 천장도 있다: 상품이 $m$개면 $E_{\text{proj}} \le \binom{m}{2}$. 중복 쌍은 가중치로 합쳐지므로
# 실제 값은 두 상한 중 작은 쪽보다 작다.)

# %%
def simulate(n_users, items_per_user):
    """투영 엣지 수가 어떻게 느는지 계산으로 본다."""
    return n_users * items_per_user * (items_per_user - 1) // 2


print(f"{'사용자':>9} {'1인당 구매':>11} {'투영 엣지(최대)':>18}")
CASES = ((1_000, 10), (1_000, 50), (100_000, 50), (100_000, 200))
for n, k in CASES:
    print(f"{n:>9,} {k:>11} {simulate(n, k):>18,}")
print("\n사용자만 100배 늘면 엣지도 100배. 1인당 구매를 4배 늘리면 엣지는 약 16배.")
# 출력:
#       사용자      1인당 구매          투영 엣지(최대)
#     1,000          10             45,000
#     1,000          50          1,225,000
#   100,000          50        122,500,000
#   100,000         200      1,990,000,000
#
# 사용자만 100배 늘면 엣지도 100배. 1인당 구매를 4배 늘리면 엣지는 약 16배.

# %%
# 실제 투영은 중복이 합쳐진다. 작은 합성 데이터로 «상한 vs 실제»를 비교해 본다.
import random

random.seed(7)
N_USERS, N_ITEMS, K = 300, 40, 8
synth = [(f"u{u}", f"i{i}")
         for u in range(N_USERS)
         for i in random.sample(range(N_ITEMS), K)]

real = len(project(synth, side=1))
upper_clique = simulate(N_USERS, K)
upper_items = N_ITEMS * (N_ITEMS - 1) // 2
print(f"원본 이분 엣지        : {len(synth):,}")
print(f"상한 n·C(k,2)         : {upper_clique:,}")
print(f"상한 C(m,2) (상품 천장): {upper_items:,}")
print(f"실제 투영 엣지        : {real:,}")
# 출력:
# 원본 이분 엣지        : 2,400
# 상한 n·C(k,2)         : 8,400
# 상한 C(m,2) (상품 천장): 780
# 실제 투영 엣지        : 780

# %% [markdown]
# ## 6단계 — 대안: 2홉 탐색과 가중치 컷
#
# 1. **투영하지 않고** 이분 그래프에서 2홉을 돈다. 필요한 노드에 대해서만, 질의 시점에 계산.
#    저장 폭발이 없고 정보 손실도 없다. 대신 매번 계산 비용.
# 2. **투영하되 자른다.** $w \ge \tau$인 엣지만 남긴다. 책의 저자는 «엣지 수 $\le$ 노드 수 $\times$ 20»이
#    되도록 $\tau$를 잡는다고 한다.

# %%
def two_hop(pairs, node, side=1):
    """투영을 만들지 않고, 그 노드 하나에 대해서만 즉석 계산."""
    g = defaultdict(set)
    for a, b in pairs:
        key, val = (a, b) if side == 0 else (b, a)
        g[val].add(key)
    hits = defaultdict(int)
    for val, keys in g.items():
        if node in keys:                    # 1홉: node → val
            for other in keys:              # 2홉: val → other
                if other != node:
                    hits[other] += 1
    return dict(hits)


print("상품A 의 2홉 이웃:", two_hop(PURCHASES, "상품A"))
print("투영 결과와 일치  :", {"상품B": proj_item[("상품A", "상품B")],
                              "상품C": proj_item[("상품A", "상품C")]})
# 출력:
# 상품A 의 2홉 이웃: {'상품B': 2, '상품C': 1}
# 투영 결과와 일치  : {'상품B': 2, '상품C': 1}

# %%
proj_synth = project(synth, side=1)
print(f"{'컷 τ':>5} {'남는 엣지':>10} {'노드당 엣지':>12}")
for tau in (1, 8, 11, 14, 18):
    kept = {e: w for e, w in proj_synth.items() if w >= tau}
    nodes = len({n for e in kept for n in e}) or 1
    print(f"{tau:>5} {len(kept):>10,} {len(kept) / nodes:>12.1f}")
print("\n컷을 조금만 올려도 엣지가 급격히 준다. w 분포가 대개 한쪽으로 몰려 있기 때문이다.")
# 출력:
#   컷 τ      남는 엣지       노드당 엣지
#     1        780         19.5
#     8        673         16.8
#    11        406         10.2
#    14        135          3.5
#    18         14          0.8
#
# 컷을 조금만 올려도 엣지가 급격히 준다. w 분포가 대개 한쪽으로 몰려 있기 때문이다.

# %% [markdown]
# ## 시각화
#
# 왼쪽: 원본 이분 그래프. 가운데: 상품 쪽 투영(`side=1`). 오른쪽: 사용자 쪽 투영(`side=0`).
# 아래: 1인당 구매 수 $k$에 따른 투영 엣지 상한 (로그 스케일).

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

USERS = ["u1", "u2", "u3"]
ITEMS = ["상품A", "상품B", "상품C"]
POS_BI = {**{u: (0.0, 2 - i) for i, u in enumerate(USERS)},
          **{it: (1.0, 2 - i) for i, it in enumerate(ITEMS)}}
POS_ITEM = {"상품A": (0.0, 1.0), "상품B": (1.0, 1.0), "상품C": (0.5, 0.0)}
POS_USER = {"u1": (0.0, 0.0), "u2": (0.5, 1.0), "u3": (1.0, 0.0)}

fig = make_subplots(
    rows=2, cols=3,
    specs=[[{}, {}, {}], [{"colspan": 3}, None, None]],
    row_heights=[0.58, 0.42], vertical_spacing=0.16,
    subplot_titles=("원본 이분 그래프 (엣지 6)",
                    "side=1 상품 투영 (엣지 3)",
                    "side=0 사용자 투영 (엣지 2)",
                    "투영 엣지 상한 = n·k(k−1)/2"),
)

C_USER, C_ITEM, C_EDGE = "#3b6ea5", "#c9622f", "#9aa5b1"


def draw_graph(edges, pos, col, colors, weighted):
    for e in edges:
        a, b = e[0], e[1]
        x0, y0 = pos[a]
        x1, y1 = pos[b]
        w = e[2] if weighted else 1
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1], mode="lines",
            line=dict(color=C_EDGE, width=1.2 + 2.2 * (w - 1)),
            hoverinfo="skip", showlegend=False), row=1, col=col)
        if weighted:
            fig.add_trace(go.Scatter(
                x=[(x0 + x1) / 2], y=[(y0 + y1) / 2], mode="text",
                text=[f"<b>{w}</b>"], textfont=dict(size=12, color="#444"),
                hoverinfo="skip", showlegend=False), row=1, col=col)
    xs = [pos[n][0] for n in pos]
    ys = [pos[n][1] for n in pos]
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers+text", text=list(pos),
        textposition="bottom center", textfont=dict(size=11),
        marker=dict(size=22, color=[colors[n] for n in pos],
                    line=dict(color="white", width=1.5)),
        hovertemplate="%{text}<extra></extra>", showlegend=False), row=1, col=col)


bi_colors = {**{u: C_USER for u in USERS}, **{i: C_ITEM for i in ITEMS}}
draw_graph(PURCHASES, POS_BI, 1, bi_colors, weighted=False)
draw_graph([(a, b, w) for (a, b), w in sorted(proj_item.items())],
           POS_ITEM, 2, {i: C_ITEM for i in ITEMS}, weighted=True)
draw_graph([(a, b, w) for (a, b), w in sorted(proj_user.items())],
           POS_USER, 3, {u: C_USER for u in USERS}, weighted=True)

ks = list(range(2, 201))
for n, color in ((1_000, "#3b6ea5"), (100_000, "#c9622f")):
    fig.add_trace(go.Scatter(
        x=ks, y=[simulate(n, k) for k in ks], mode="lines",
        name=f"사용자 {n:,}명", line=dict(color=color, width=2.4),
        hovertemplate="k=%{x}, 엣지≈%{y:,}<extra></extra>"), row=2, col=1)
fig.add_trace(go.Scatter(
    x=[k for _, k in CASES], y=[simulate(n, k) for n, k in CASES],
    mode="markers", name="책의 표", marker=dict(size=9, color="#2e7d5b", symbol="diamond"),
    hovertemplate="k=%{x}, 엣지=%{y:,}<extra></extra>"), row=2, col=1)

for c in (1, 2, 3):
    fig.update_xaxes(visible=False, row=1, col=c)
    fig.update_yaxes(visible=False, row=1, col=c, scaleanchor=f"x{c if c > 1 else ''}")
fig.update_xaxes(title_text="1인당 구매 수 k", row=2, col=1)
fig.update_yaxes(title_text="투영 엣지 상한 (log)", type="log", row=2, col=1)
fig.update_layout(
    title="이분 그래프 투영: project() 가 무엇을 계산하고, 왜 폭발하는가",
    template="plotly_white", width=1080, height=760,
    font=dict(family="Apple SD Gothic Neo, AppleGothic, Noto Sans KR, sans-serif", size=12),
    legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"),
    margin=dict(l=60, r=30, t=70, b=90),
)

_show(fig)

# %%
import os

_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_png, scale=2)
print("saved:", _png)
# 출력:
# saved: .../848b1c38-7b9c-4f4e-97c2-8e0c644d2382/expy.png

# %% [markdown]
# ## 정리
#
# - `project(pairs, side)`는 이분 그래프를 **`side`가 가리키는 쪽만 남기고** 접는다.
# - `grouped`는 접히는 쪽 노드의 **이웃 집합** $N(\cdot)$, `combinations(..., 2)`가 그 안에서
#   **모든 쌍**을 만들고, `out[(x,y)] += 1`이 **공유한 상대 수**를 누적한다.
# - 결과 엣지의 뜻: 「$x$와 $y$를 **함께** 가진 상대가 $w$개 있다」.
# - 대가: 접힌 쪽 정보가 **완전히 사라지고**(비가역), 엣지가 $O(nk^2)$로 **제곱 폭발**한다.
# - 대응: 2홉 즉석 계산, 또는 $w \ge \tau$ 컷.
