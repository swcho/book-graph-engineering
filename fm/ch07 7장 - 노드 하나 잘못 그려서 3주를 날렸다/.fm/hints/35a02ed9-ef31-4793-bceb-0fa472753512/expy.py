# %% [markdown]
# # 이분 그래프 투영의 두 가지 문제
#
# 질문: **이분 그래프를 투영하면 어떤 두 가지 문제가 생기는가?**
#
# 답: **정보가 사라지고(누가 샀는지) 엣지가 제곱으로 늘어난다.**
#
# 이 노트북은 그 두 문제를 순서대로 손으로 확인한다.
#
# 1. 이분 그래프와 투영을 직접 만든다
# 2. 문제 1 — 정보 손실: 서로 **다른** 원본이 **같은** 투영을 만드는 것을 확인한다 (되돌릴 수 없다)
# 3. 문제 2 — 엣지 폭발: 투영 엣지 수가 $\binom{k}{2}$ 로 늘어나는 것을 계산과 그림으로 본다
# 4. 대안 — 2홉 탐색, 임계값 절단
#
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용. 없어도 앞 셀들은 그대로 돌아간다)

# %%
from collections import defaultdict
from itertools import combinations


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# 이분 그래프: 노드가 두 종류(사용자, 상품)뿐이고 엣지는 «서로 다른 종류 사이»에만 있다.
PURCHASES = [
    ("u1", "상품A"),
    ("u1", "상품B"),
    ("u2", "상품A"),
    ("u2", "상품B"),
    ("u2", "상품C"),
    ("u3", "상품C"),
]

print("원본 이분 그래프 (사용자)-[:구매]->(상품)")
for u, i in PURCHASES:
    print(f"   {u} --구매--> {i}")
print(f"   노드 {len({u for u, _ in PURCHASES}) + len({i for _, i in PURCHASES})}개, 엣지 {len(PURCHASES)}개")
# 출력:
# 원본 이분 그래프 (사용자)-[:구매]->(상품)
#    u1 --구매--> 상품A
#    u1 --구매--> 상품B
#    u2 --구매--> 상품A
#    u2 --구매--> 상품B
#    u2 --구매--> 상품C
#    u3 --구매--> 상품C
#    노드 6개, 엣지 6개

# %% [markdown]
# ## 1. 투영(projection)이란
#
# 이분 그래프는 «상품끼리 얼마나 비슷한가» 같은 질문에 바로 답하지 못한다. 상품과 상품은 직접 이어져
# 있지 않기 때문이다. 그래서 한쪽 종류만 남기고 **상대를 공유하면 잇는다**. 이것이 투영이다.
#
# $$
# u \sim v \iff \exists\, w \in W \ \text{s.t.}\ (u,w) \in E \wedge (v,w) \in E
# $$
#
# 가중치는 보통 «공유한 상대의 수»로 둔다.

# %%
def project(pairs, side=1):
    """한쪽으로 투영. 같은 상대를 공유하면 잇는다. side=1 이면 오른쪽(상품) 투영."""
    grouped = defaultdict(set)
    for a, b in pairs:
        key, val = (a, b) if side == 0 else (b, a)
        grouped[val].add(key)
    out = defaultdict(int)
    for _val, keys in grouped.items():
        for x, y in combinations(sorted(keys), 2):
            out[(x, y)] += 1
    return dict(out)


proj_item = project(PURCHASES, side=1)  # 상품 쪽 투영
proj_user = project(PURCHASES, side=0)  # 사용자 쪽 투영

print("상품 쪽 투영 (함께 산 상품끼리 잇기)")
for (a, b), w in sorted(proj_item.items()):
    print(f"   {a} — {b}   (함께 산 사람 {w}명)")

print("\n사용자 쪽 투영 (같은 상품을 산 사람끼리 잇기)")
for (a, b), w in sorted(proj_user.items()):
    print(f"   {a} — {b}   (겹친 상품 {w}개)")
# 출력:
# 상품 쪽 투영 (함께 산 상품끼리 잇기)
#    상품A — 상품B   (함께 산 사람 2명)
#    상품A — 상품C   (함께 산 사람 1명)
#    상품B — 상품C   (함께 산 사람 1명)
#
# 사용자 쪽 투영 (같은 상품을 산 사람끼리 잇기)
#    u1 — u2   (겹친 상품 2개)
#    u2 — u3   (겹친 상품 1개)

# %% [markdown]
# ## 2. 문제 하나 — 정보가 사라진다
#
# 상품 쪽 투영 결과에는 `u1`, `u2`, `u3` 이 **한 명도 남아 있지 않다**. 「상품A와 상품B는 2명이
# 함께 샀다」는 사실만 남고 「그게 **누구**였는지」는 없다.
#
# 그래서 투영 그래프만 들고는 이런 질문에 답할 수 없다.
#
# - 이 두 상품을 함께 산 사람이 우리 VIP인가 신규 가입자인가
# - 그 사람에게 다음에 무엇을 추천할까
# - 이 동시구매가 한 사람의 한 번 장바구니였나, 서로 모르는 여러 사람이었나
#
# 이건 «불편하다» 수준이 아니라 **되돌릴 수 없는(비가역) 손실**이다. 아래 셀이 그 증거다.

# %%
# 완전히 다른 두 원본이 «같은» 투영을 만든다.
ORIGIN_A = [("u1", "상품A"), ("u1", "상품B"), ("u2", "상품B"), ("u2", "상품C"), ("u3", "상품A"), ("u3", "상품C")]
ORIGIN_B = [("v1", "상품A"), ("v1", "상품B"), ("v1", "상품C")]

pa, pb = project(ORIGIN_A, side=1), project(ORIGIN_B, side=1)

print("원본 A: 세 사람이 각각 «두 개씩» 샀다  ->", sorted(pa.items()))
print("원본 B: 한 사람이 «세 개 다» 샀다      ->", sorted(pb.items()))
print("\n두 투영이 같은가?", pa == pb)
print("원본 사용자 수:", len({u for u, _ in ORIGIN_A}), "vs", len({u for u, _ in ORIGIN_B}))
# 출력:
# 원본 A: 세 사람이 각각 «두 개씩» 샀다  -> [(('상품A', '상품B'), 1), (('상품A', '상품C'), 1), (('상품B', '상품C'), 1)]
# 원본 B: 한 사람이 «세 개 다» 샀다      -> [(('상품A', '상품B'), 1), (('상품A', '상품C'), 1), (('상품B', '상품C'), 1)]
#
# 두 투영이 같은가? True
# 원본 사용자 수: 3 vs 1

# %% [markdown]
# 투영 그래프는 두 경우를 **구별하지 못한다**. 그런데 추천 품질은 정반대다.
#
# - 원본 B(한 사람이 세 개 다 샀다)는 「같이 쓰는 세트」라는 근거가 된다
# - 원본 A(세 사람이 서로 다른 쌍을 샀다)는 세트 근거가 전혀 아니다
#
# 즉 투영은 **다대일 사상**이다. 역상이 유일하지 않으니 복원이 불가능하다.
#
# $$
# \pi : \mathcal{B} \to \mathcal{G}, \qquad |\pi^{-1}(G)| > 1
# $$

# %% [markdown]
# ## 3. 문제 둘 — 엣지가 제곱으로 늘어난다
#
# 상품 $k$ 개를 산 사용자 한 명은 투영에서 **완전 그래프(클리크)** 하나를 만든다.
#
# $$
# \binom{k}{2} = \frac{k(k-1)}{2} = O(k^2)
# $$
#
# 사용자 $n$ 명이 각자 $k$ 개를 샀다면 투영 엣지의 상한은
#
# $$
# E_{\text{proj}} \le n \cdot \frac{k(k-1)}{2}
# $$
#
# 원본 이분 그래프의 엣지는 $nk$ 로 **선형**인데, 투영은 $k$ 에 **제곱**으로 붙는다.
# $k$ 가 10에서 200으로 20배가 되면 엣지는 400배 근처로 뛴다.

# %%
def simulate(n_users, items_per_user):
    """투영 엣지 수 상한."""
    return n_users * items_per_user * (items_per_user - 1) // 2


rows = [(1_000, 10), (1_000, 50), (100_000, 50), (100_000, 200)]
print(f"{'사용자':>9} {'1인당 구매':>10} {'원본 엣지':>12} {'투영 엣지(상한)':>18} {'배율':>8}")
for n, k in rows:
    src, prj = n * k, simulate(n, k)
    print(f"{n:>9,} {k:>10} {src:>12,} {prj:>18,} {prj / src:>7.1f}x")
# 출력:
#       사용자     1인당 구매        원본 엣지          투영 엣지(상한)       배율
#     1,000         10       10,000             45,000     4.5x
#     1,000         50       50,000          1,225,000    24.5x
#   100,000         50    5,000,000        122,500,000    24.5x
#   100,000        200   20,000,000      1,990,000,000    99.5x

# %%
# 반대 방향도 똑같이 위험하다. «인기 상품» 하나가 사용자 쪽 투영에서 거대한 클리크를 만든다.
for buyers in (1_000, 10_000, 100_000):
    print(f"비닐봉지를 산 사람 {buyers:>7,}명 -> 사용자 투영 엣지 {buyers * (buyers - 1) // 2:>16,}개")
# 출력:
# 비닐봉지를 산 사람   1,000명 -> 사용자 투영 엣지          499,500개
# 비닐봉지를 산 사람  10,000명 -> 사용자 투영 엣지       49,995,000개
# 비닐봉지를 산 사람 100,000명 -> 사용자 투영 엣지    4,999,950,000개

# %% [markdown]
# 상품 하나가 엣지 50억 개를 만든다. 노드 10만 개짜리 그래프인데 엣지가 50억이다.
# 이게 「화이트보드에서는 예뻤어요」의 전형이다.

# %% [markdown]
# ## 4. 대안 — 2홉 탐색과 임계값 절단
#
# 1. **투영하지 말고 이분 그래프 그대로 2홉을 돈다.** 필요할 때만 계산하니 저장 비용이 0이고,
#    「누가 샀는지」도 경로에 그대로 남아 있다 (정보 손실 없음).
# 2. **투영하되 «함께 산 사람 $N$명 이상»으로 자른다.** 대개 3명이면 충분하다.
#    자르는 값은 엣지 수가 노드 수의 20배를 넘지 않게 잡는다.

# %%
def two_hop(pairs, start, min_shared=1):
    """투영을 저장하지 않고 필요할 때 2홉으로 계산한다. 중간에 «누가» 가 남는다."""
    right_of = defaultdict(set)
    left_of = defaultdict(set)
    for a, b in pairs:
        right_of[a].add(b)
        left_of[b].add(a)
    hits = defaultdict(set)  # 이웃 상품 -> 그 근거가 된 사용자 집합
    for user in left_of[start]:
        for item in right_of[user]:
            if item != start:
                hits[item].add(user)
    return {i: sorted(us) for i, us in hits.items() if len(us) >= min_shared}


print("«상품A와 함께 팔린 상품» 을 2홉으로 (근거 사용자까지)")
for item, users in sorted(two_hop(PURCHASES, "상품A").items()):
    print(f"   상품A ~ {item}   근거 사용자 {users}")

print("\n임계값 절단: 함께 산 사람 2명 이상만 남기면")
kept = {k: v for k, v in proj_item.items() if v >= 2}
print(f"   투영 엣지 {len(proj_item)}개 -> {len(kept)}개  {sorted(kept.items())}")
# 출력:
# «상품A와 함께 팔린 상품» 을 2홉으로 (근거 사용자까지)
#    상품A ~ 상품B   근거 사용자 ['u1', 'u2']
#    상품A ~ 상품C   근거 사용자 ['u2']
#
# 임계값 절단: 함께 산 사람 2명 이상만 남기면
#    투영 엣지 3개 -> 1개  [(('상품A', '상품B'), 2)]

# %% [markdown]
# 2홉 결과에는 `근거 사용자`가 붙어 있다. 투영이 버렸던 바로 그 정보다.

# %% [markdown]
# ## 5. 그림으로 한 번에
#
# 왼쪽: 원본 이분 그래프(사용자가 보인다). 가운데: 상품 쪽 투영(사용자가 사라졌다).
# 오른쪽: 1인당 구매 수 $k$ 에 따른 엣지 수 — 원본은 선형, 투영은 제곱.

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    users = sorted({u for u, _ in PURCHASES})
    items = sorted({i for _, i in PURCHASES})
    pos_u = {u: (0.0, -idx) for idx, u in enumerate(users)}
    pos_i = {i: (1.0, -idx - 0.5) for idx, i in enumerate(items)}

    fig = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=(
            "원본 이분 그래프 (엣지 6)",
            "상품 쪽 투영 — 사용자 소멸 (엣지 3)",
            "엣지 수: 선형 vs 제곱 (사용자 1,000명)",
        ),
        specs=[[{"type": "scatter"}, {"type": "scatter"}, {"type": "scatter"}]],
    )

    # (1) 이분 그래프
    ex, ey = [], []
    for u, i in PURCHASES:
        ex += [pos_u[u][0], pos_i[i][0], None]
        ey += [pos_u[u][1], pos_i[i][1], None]
    fig.add_trace(
        go.Scatter(
            x=ex, y=ey, mode="lines", line=dict(color="#9aa5b1", width=1.5), hoverinfo="skip", showlegend=False
        ),
        1,
        1,
    )
    fig.add_trace(
        go.Scatter(
            x=[pos_u[u][0] for u in users],
            y=[pos_u[u][1] for u in users],
            mode="markers+text",
            text=users,
            textposition="middle left",
            marker=dict(size=22, color="#2f6fed"),
            name="사용자",
        ),
        1,
        1,
    )
    fig.add_trace(
        go.Scatter(
            x=[pos_i[i][0] for i in items],
            y=[pos_i[i][1] for i in items],
            mode="markers+text",
            text=items,
            textposition="middle right",
            marker=dict(size=22, color="#e8863c"),
            name="상품",
        ),
        1,
        1,
    )

    # (2) 투영 그래프 (삼각형 배치)
    tri = {"상품A": (0.0, 0.0), "상품B": (1.0, 0.0), "상품C": (0.5, 0.9)}
    for (a, b), w in proj_item.items():
        fig.add_trace(
            go.Scatter(
                x=[tri[a][0], tri[b][0]],
                y=[tri[a][1], tri[b][1]],
                mode="lines",
                line=dict(color="#9aa5b1", width=1 + 2.5 * w),
                hovertext=f"{a}—{b} 함께 산 사람 {w}명",
                showlegend=False,
            ),
            1,
            2,
        )
    fig.add_trace(
        go.Scatter(
            x=[p[0] for p in tri.values()],
            y=[p[1] for p in tri.values()],
            mode="markers+text",
            text=list(tri),
            textposition="top center",
            marker=dict(size=24, color="#e8863c"),
            showlegend=False,
        ),
        1,
        2,
    )
    fig.add_annotation(
        x=0.5, y=-0.35, xref="x2", yref="y2", text="u1 u2 u3 → 없음", showarrow=False, font=dict(color="#c23b22")
    )

    # (3) 증가 곡선
    ks = list(range(2, 201))
    n = 1_000
    fig.add_trace(
        go.Scatter(x=ks, y=[n * k for k in ks], mode="lines", name="원본 nk (선형)", line=dict(color="#2f6fed")), 1, 3
    )
    fig.add_trace(
        go.Scatter(
            x=ks,
            y=[simulate(n, k) for k in ks],
            mode="lines",
            name="투영 nk(k-1)/2 (제곱)",
            line=dict(color="#c23b22"),
        ),
        1,
        3,
    )

    fig.update_xaxes(visible=False, range=[-0.35, 1.6], row=1, col=1)
    fig.update_yaxes(visible=False, row=1, col=1)
    fig.update_xaxes(visible=False, range=[-0.35, 1.35], row=1, col=2)
    fig.update_yaxes(visible=False, range=[-0.55, 1.25], row=1, col=2)
    fig.update_xaxes(title_text="1인당 구매 수 k", row=1, col=3)
    fig.update_yaxes(title_text="엣지 수 (log)", type="log", row=1, col=3)
    fig.update_layout(
        title="이분 그래프 투영의 두 문제 — 정보 손실 · 엣지 제곱 증가",
        template="plotly_white",
        height=460,
        width=1300,
        legend=dict(orientation="h", y=-0.15),
    )

    import os

    _here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
    _show(fig)
    fig.write_image(os.path.join(_here, "expy.png"), scale=2)
    print("expy.png 저장 완료")
except ImportError as e:
    print("시각화 생략 (필요 패키지: plotly, kaleido):", e)
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# | 문제 | 무슨 일이 벌어지나 | 대응 |
# |---|---|---|
# | 정보 손실 | 투영 후 반대편 노드가 사라진다 (누가 샀는지). 다대일 사상이라 복원 불가 | 이분 그래프를 원본으로 남기고, 필요할 때 2홉으로 계산 |
# | 엣지 폭발 | 한 노드의 이웃 $k$ 개가 $\binom{k}{2}$ 엣지로 부푼다. 허브 하나가 수십억 엣지 | 임계값 절단(함께 산 사람 3명 이상), 엣지 수를 노드 수의 20배 이내로 |
