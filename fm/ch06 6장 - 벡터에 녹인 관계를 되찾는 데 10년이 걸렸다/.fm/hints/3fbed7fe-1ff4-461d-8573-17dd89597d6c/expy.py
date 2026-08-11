# %% [markdown]
# # `ex4_link_prediction.py` 의 링크 예측 점수, 처음부터 다시 계산하기
#
# 회사와 «원인» 이 양쪽에 놓인 **이분 그래프**(bipartite graph)에서,
# 아직 이어지지 않은 (회사, 원인) 쌍에 점수를 매긴다.
#
# $$
# \mathrm{score}(c, x) \;=\; \sum_{p \,\in\, N(x),\; p \neq c} \bigl|\, N(c) \cap N(p) \,\bigr|
# $$
#
# - $N(v)$ : 노드 $v$ 의 이웃 집합
# - $N(x)$ : 원인 $x$ 를 **이미 겪은 회사들** (peers)
# - $|N(c) \cap N(p)|$ : 회사 $c$ 와 회사 $p$ 가 **함께 가진 원인의 수** (공통 이웃 수)
#
# 즉 «$x$ 를 겪은 회사들 각각이 나와 얼마나 닮았나» 를 전부 더한 값이다.
# 닮은 회사가 많이 겪은 원인일수록 점수가 높아진다.

# %%
from collections import defaultdict
from itertools import combinations  # noqa: F401  (원본 코드에도 있지만 쓰이지 않는다)

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# ex4_link_prediction.py 의 EDGES 를 그대로 가져왔다.
EDGES = [
    ("가온테크", "재시도"), ("가온테크", "멱등성없음"),
    ("나루소프트", "재시도"), ("나루소프트", "멱등성없음"), ("나루소프트", "캐시"),
    ("다올물산", "재시도"),
    ("라온에너지", "멱등성없음"), ("라온에너지", "캐시"),
    ("마루상사", "캐시"),
]


def adjacency(edges):
    adj = defaultdict(set)
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    return adj


adj = adjacency(EDGES)
COMPANIES = sorted({a for a, _ in EDGES})
CAUSES = sorted({b for _, b in EDGES})

print("회사:", COMPANIES)
print("원인:", CAUSES)
for c in COMPANIES:
    print(f"  N({c}) = {sorted(adj[c])}")
for x in CAUSES:
    print(f"  N({x}) = {sorted(adj[x])}")

# 출력: 회사: ['가온테크', '나루소프트', '다올물산', '라온에너지', '마루상사']
# 출력: 원인: ['멱등성없음', '재시도', '캐시']
# 출력:   N(가온테크) = ['멱등성없음', '재시도']
# 출력:   N(나루소프트) = ['멱등성없음', '재시도', '캐시']
# 출력:   N(다올물산) = ['재시도']
# 출력:   N(라온에너지) = ['멱등성없음', '캐시']
# 출력:   N(마루상사) = ['캐시']
# 출력:   N(멱등성없음) = ['가온테크', '나루소프트', '라온에너지']
# 출력:   N(재시도) = ['가온테크', '나루소프트', '다올물산']
# 출력:   N(캐시) = ['나루소프트', '라온에너지', '마루상사']

# %% [markdown]
# ## 1단계 — 회사끼리의 «닮음» = 공통 이웃 수
#
# 이분 그래프라 회사와 회사는 직접 이어지지 않는다.
# 두 회사의 공통 이웃은 반드시 «원인» 이고, 그 개수가 곧 유사도가 된다.
#
# $$ \mathrm{sim}(c, p) = \bigl|\, N(c) \cap N(p) \,\bigr| $$

# %%
def common_neighbors(u, v):
    return len(adj[u] & adj[v])


print("회사 × 회사 공통 원인 수")
print("          " + "".join(f"{p[:4]:>8}" for p in COMPANIES))
SIM = {}
for c in COMPANIES:
    row = []
    for p in COMPANIES:
        SIM[(c, p)] = common_neighbors(c, p)
        row.append(SIM[(c, p)])
    print(f"{c[:5]:<6}" + "".join(f"{v:>8}" for v in row))

# 출력: 회사 × 회사 공통 원인 수
# 출력:               가온테크    나루소프    다올물산    라온에너    마루상사
# 출력: 가온테크         2       2       1       1       0
# 출력: 나루소프트        2       3       1       2       1
# 출력: 다올물산         1       1       1       0       0
# 출력: 라온에너지        1       2       0       2       1
# 출력: 마루상사         0       1       0       1       1

# %% [markdown]
# ## 2단계 — 아직 없는 (회사, 원인) 쌍마다 peer 기여를 합산
#
# 후보는 $x \notin N(c)$ 인 쌍뿐이다. 각 후보에 대해
# «$x$ 를 겪은 다른 회사» 들의 유사도를 전부 더한다.

# %%
rows = []
for c in COMPANIES:
    for x in CAUSES:
        if x in adj[c]:
            continue  # 이미 이어져 있다 = 예측 대상이 아니다
        peers = [p for p in COMPANIES if x in adj[p] and p != c]
        parts = [(p, SIM[(c, p)]) for p in peers]
        score = sum(v for _, v in parts)
        rows.append({"회사": c, "원인": x, "점수": score, "기여": parts})

rows.sort(key=lambda r: (-r["점수"], r["회사"], r["원인"]))

print(f"후보 쌍 {len(rows)}개 — 점수 순")
print(f"{'순위':<4}{'회사':<7}{'원인':<7}{'점수':<5} 기여 내역 (peer × 공통 원인 수)")
for i, r in enumerate(rows, 1):
    detail = " + ".join(f"{p}:{v}" for p, v in r["기여"])
    print(f"{i:<5}{r['회사']:<8}{r['원인']:<9}{r['점수']:<6}{detail}")

# 출력: 후보 쌍 6개 — 점수 순
# 출력: 순위  회사     원인     점수   기여 내역 (peer × 공통 원인 수)
# 출력: 1    가온테크    캐시       3     나루소프트:2 + 라온에너지:1 + 마루상사:0
# 출력: 2    라온에너지   재시도      3     가온테크:1 + 나루소프트:2 + 다올물산:0
# 출력: 3    다올물산    멱등성없음    2     가온테크:1 + 나루소프트:1 + 라온에너지:0
# 출력: 4    마루상사    멱등성없음    2     가온테크:0 + 나루소프트:1 + 라온에너지:1
# 출력: 5    다올물산    캐시       1     나루소프트:1 + 라온에너지:0 + 마루상사:0
# 출력: 6    마루상사    재시도      1     가온테크:0 + 나루소프트:1 + 다올물산:0
#
# 참고: 원본 ex4 는 `scored.sort(reverse=True)` 로 (점수, 회사, 원인) 튜플을
#      «내림차순» 정렬하므로 동점일 때 이름이 큰 쪽이 앞에 온다.
#      그래서 원본 출력의 1위는 «라온에너지 ↔ 재시도», 2위가 «가온테크 ↔ 캐시» 다.
#      점수 자체는 여기 계산과 완전히 같다.

# %% [markdown]
# ## 3단계 — 왜 이 점수가 나왔는지 되짚기
#
# 점수가 합이라서, 어느 peer 가 얼마를 냈는지 그대로 쪼갤 수 있다.
# 이게 «되짚을 수 있는 예측» 이다. 임베딩 코사인 유사도에는 없는 성질이다.

# %%
top = rows[0]
c, x = top["회사"], top["원인"]
print(f"1위: {c} ↔ {x} (점수 {top['점수']})")
for p, v in sorted(top["기여"], key=lambda t: -t[1]):
    shared = sorted(adj[c] & adj[p])
    print(f"  {c} 와 {p} 가 함께 가진 원인: {shared or '(없음)'}  → 기여 {v}")
best = max(top["기여"], key=lambda t: t[1])[0]
print(f"  → {best} 와 원인 {sorted(adj[c] & adj[best])} 를 공유한다.")
print(f"     그 {best} 가 {x} 를 겪었으니 {c} 도 겪을 수 있다는 추론이다.")

# 출력: 1위: 가온테크 ↔ 캐시 (점수 3)
# 출력:   가온테크 와 나루소프트 가 함께 가진 원인: ['멱등성없음', '재시도']  → 기여 2
# 출력:   가온테크 와 라온에너지 가 함께 가진 원인: ['멱등성없음']  → 기여 1
# 출력:   가온테크 와 마루상사 가 함께 가진 원인: (없음)  → 기여 0
# 출력:   → 나루소프트 와 원인 ['멱등성없음', '재시도'] 를 공유한다.
# 출력:      그 나루소프트 가 캐시 를 겪었으니 가온테크 도 겪을 수 있다는 추론이다.

# %% [markdown]
# ## 4단계 — 이건 협업 필터링과 같은 식이다
#
# 위 식은 **user-based CF** 의 모양 그대로다.
# 사용자 = 회사, 아이템 = 원인, 유사도 = 공통 아이템 수라고 읽으면 된다.
#
# $$
# \hat{r}(u, i) \;=\; \sum_{v \,\in\, U(i)} \mathrm{sim}(u, v)
# $$
#
# 그리고 합의 순서를 바꾸면 **item-based CF** 로 그대로 넘어간다.
#
# $$
# \mathrm{score}(c,x)
# = \sum_{p \in N(x)} \sum_{y \in N(c)} \mathbb{1}[\,p \in N(y)\,]
# = \sum_{y \,\in\, N(c)} \bigl|\, N(x) \cap N(y) \,\bigr|
# = \sum_{y \in N(c)} \mathrm{cooc}(x, y)
# $$
#
# $\mathrm{cooc}(x,y)$ 는 «원인 $x$ 와 $y$ 를 동시에 겪은 회사 수», 곧 아이템–아이템 공기 행렬이다.
# user-based 로 재도 item-based 로 재도 **같은 수**가 나온다.
# 두 식 모두 결국 이분 그래프에서 $c \to y \to p \to x$ 로 가는 **길이 3짜리 경로 수**를 세는 것이고,
# 행렬로는 $(B B^{\top} B)_{c,x}$ 다 ($B$ 는 회사×원인 이분 인접 행렬).

# %%
def cooc(x, y):
    return len(adj[x] & adj[y])


print("원인 × 원인 공기 행렬 cooc(x, y)")
print("            " + "".join(f"{y:>10}" for y in CAUSES))
for x in CAUSES:
    print(f"{x:<10}" + "".join(f"{cooc(x, y):>10}" for y in CAUSES))

print("\nuser-based 합 vs item-based 합 vs 3홉 경로 수")
print(f"{'회사':<7}{'원인':<9}{'user':<7}{'item':<7}{'paths':<7}일치")


def paths3(c, x):
    """c -> y -> p -> x 경로를 하나씩 다 센다. (B Bᵀ B)[c, x] 와 같다."""
    n = 0
    for y in adj[c]:            # 내가 겪은 원인
        for p in adj[y]:        # 그 원인을 겪은 다른 회사
            if x in adj[p]:     # 그 회사가 x 도 겪었나
                n += 1
    return n


for r in rows:
    c, x = r["회사"], r["원인"]
    u = r["점수"]
    i = sum(cooc(x, y) for y in adj[c])
    p3 = paths3(c, x)
    print(f"{c:<8}{x:<11}{u:<8}{i:<8}{p3:<8}{'예' if u == i == p3 else '아니오'}")

# 출력: 원인 × 원인 공기 행렬 cooc(x, y)
# 출력:                 멱등성없음       재시도        캐시
# 출력: 멱등성없음              3         2         2
# 출력: 재시도                 2         3         1
# 출력: 캐시                  2         1         3
# 출력:
# 출력: user-based 합 vs item-based 합 vs 3홉 경로 수
# 출력: 회사     원인       user   item   paths  일치
# 출력: 가온테크    캐시         3       3       3       예
# 출력: 라온에너지   재시도        3       3       3       예
# 출력: 다올물산    멱등성없음      2       2       2       예
# 출력: 마루상사    멱등성없음      2       2       2       예
# 출력: 다올물산    캐시         1       1       1       예
# 출력: 마루상사    재시도        1       1       1       예

# %% [markdown]
# ## 5단계 — 시각화
#
# 왼쪽: 이분 그래프. 회색 실선이 기존 간선, 빨간 점선이 상위 2개 예측 링크.
# 오른쪽 위: 후보 점수를 peer 기여로 쪼갠 누적 막대 (되짚기가 그림으로 보인다).
# 오른쪽 아래: 원인–원인 공기 행렬 (item-based CF 쪽 시선).

# %%
fig = make_subplots(
    rows=2, cols=2,
    column_widths=[0.5, 0.5], row_heights=[0.55, 0.45],
    specs=[[{"rowspan": 2}, {}], [None, {}]],
    subplot_titles=(
        "이분 그래프 — 회색: 기존, 빨강 점선: 예측 상위 2",
        "후보 점수 = peer 기여의 합 (되짚기 가능)",
        "원인 × 원인 공기 행렬 cooc(x, y) — item-based CF",
    ),
)

# --- (1) 이분 그래프 ---
cy = {c: (len(COMPANIES) - 1 - i) for i, c in enumerate(COMPANIES)}
xy = {x: (len(CAUSES) - 1 - i) * 2 + 0.5 for i, x in enumerate(CAUSES)}
for a, b in EDGES:
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[cy[a], xy[b]], mode="lines",
        line=dict(color="rgba(120,120,120,0.55)", width=2),
        hoverinfo="skip", showlegend=False), row=1, col=1)
for r in rows[:2]:
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[cy[r["회사"]], xy[r["원인"]]], mode="lines",
        line=dict(color="#d62728", width=3, dash="dash"),
        hovertext=f"{r['회사']} ↔ {r['원인']} : {r['점수']}",
        hoverinfo="text", showlegend=False), row=1, col=1)
fig.add_trace(go.Scatter(
    x=[0] * len(COMPANIES), y=[cy[c] for c in COMPANIES], mode="markers+text",
    marker=dict(size=26, color="#1f77b4"), text=COMPANIES,
    textposition="middle left", showlegend=False), row=1, col=1)
fig.add_trace(go.Scatter(
    x=[1] * len(CAUSES), y=[xy[x] for x in CAUSES], mode="markers+text",
    marker=dict(size=26, color="#ff7f0e"), text=CAUSES,
    textposition="middle right", showlegend=False), row=1, col=1)

# --- (2) 누적 막대: peer 기여 ---
labels = [f"{r['회사']}<br>↔{r['원인']}" for r in rows]
palette = {"가온테크": "#1f77b4", "나루소프트": "#2ca02c", "다올물산": "#9467bd",
           "라온에너지": "#ff7f0e", "마루상사": "#8c564b"}
for peer in COMPANIES:
    vals = [dict(r["기여"]).get(peer, 0) for r in rows]
    if not any(vals):
        continue
    fig.add_trace(go.Bar(
        x=labels, y=vals, name=peer, marker_color=palette[peer],
        text=[v or "" for v in vals], textposition="inside",
        legendgroup=peer), row=1, col=2)

# --- (3) 공기 행렬 히트맵 ---
fig.add_trace(go.Heatmap(
    z=[[cooc(x, y) for y in CAUSES] for x in CAUSES],
    x=CAUSES, y=CAUSES, colorscale="Blues", showscale=False,
    text=[[cooc(x, y) for y in CAUSES] for x in CAUSES],
    texttemplate="%{text}", hoverinfo="skip"), row=2, col=2)

fig.update_xaxes(visible=False, range=[-0.45, 1.45], row=1, col=1)
fig.update_yaxes(visible=False, row=1, col=1)
fig.update_yaxes(title_text="점수", row=1, col=2)
fig.update_layout(
    barmode="stack", height=740, width=1180,
    title_text="ex4_link_prediction.py — 공통 이웃 합 점수를 처음부터 계산하기",
    legend_title_text="기여한 peer", template="plotly_white",
    font=dict(family="Apple SD Gothic Neo, NanumGothic, sans-serif", size=13),
    margin=dict(l=70, r=30, t=90, b=60),
)

_show(fig)

import os  # noqa: E402

_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_out, scale=2)
print("saved:", _out)

# 출력: saved: .../.fm/hints/3fbed7fe-1ff4-461d-8573-17dd89597d6c/expy.png

# %% [markdown]
# ## 정리
#
# - 점수 정의: $\mathrm{score}(c,x) = \sum_{p \in N(x),\, p \neq c} |N(c) \cap N(p)|$
# - 후보는 «아직 이어지지 않은 (회사, 원인) 쌍» 뿐이다.
# - 합이라서 peer 별로 쪼개 «누구와 무엇을 공유해서 이 점수가 나왔는지» 를 그대로 말할 수 있다.
# - 같은 값을 item-based CF 식 $\sum_{y \in N(c)} \mathrm{cooc}(x,y)$ 로도 얻는다. 3홉 경로 세기와 동치다.
# - 한계: 공통 이웃이 0이면 점수도 0이다. 겹치는 원인이 하나도 없는 두 회사는 아무리 «구조적으로 닮아도»
#   이 방식으로는 잡히지 않는다. 거기서부터 임베딩(2·3홉을 좌표로 누르기)이 필요해지고,
#   그 순간 위의 «되짚기» 가 사라진다.
