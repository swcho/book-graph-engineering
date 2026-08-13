# 필요 패키지: plotly, kaleido  (계산 부분은 표준 라이브러리만으로 동작)
# 실행: python3 expy.py   /   또는 Jupyter에서 셀 단위 실행

# %% [markdown]
# # 중심성 분석에서 가장 값어치 있는 정보
#
# **질문** 중심성 분석에서 가장 값어치 있는 정보는 무엇인가?
#
# **답** 1등이 아니라 **지표 사이의 순위 차이**다. 차수는 낮은데 매개가 높은 노드가
# 아무도 모르는 급소다.
#
# 이 노트북은 10장의 «작은 회사» 그래프로 그 주장을 눈으로 확인한다.
#
# 1. 네 가지 중심성을 직접 구현한다
# 2. 지표마다 1등이 다르다는 것을 본다 — 그런데 그건 아직 시작일 뿐이다
# 3. **순위 차이(gap)** 를 계산해 «숨은 급소»를 뽑는다
# 4. 노드를 실제로 제거해서 그 급소가 진짜인지 검증한다

# %%
def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1. 데이터 — 작은 회사의 «누가 누구와 일하는가»
#
# 일부러 세 사람을 심어 두었다.
#
# - **김개발**: 아는 사람이 제일 많다 (차수 1등 후보)
# - **서영업**: 외주 공장으로 가는 *유일한* 통로다 (매개가 높을 후보)
# - **대표**: 팀장들과만 이어져 있다

# %%
EDGES = [
    # 개발팀 — 팀장이 전원과, 팀원끼리도 일부
    ("김개발", "개발1"), ("김개발", "개발2"), ("김개발", "개발3"),
    ("김개발", "개발4"), ("김개발", "개발5"), ("김개발", "개발6"),
    ("개발1", "개발2"), ("개발2", "개발3"), ("개발3", "개발4"),
    ("개발4", "개발5"), ("개발5", "개발6"),
    # 영업팀
    ("정영업", "한영업"), ("정영업", "오영업"), ("정영업", "서영업"),
    ("한영업", "오영업"), ("오영업", "서영업"),
    # 디자인팀
    ("강디자", "윤디자"), ("강디자", "임디자"), ("윤디자", "임디자"),
    # 팀장들과 대표
    ("대표", "김개발"), ("대표", "정영업"), ("대표", "강디자"),
    # 외주 공장 — 서영업 한 사람을 통해서만 회사와 이어진다
    ("서영업", "공장A"),
    ("공장A", "공장B"), ("공장A", "공장C"), ("공장B", "공장C"),
    # 청소담당 — 조연. 몇 사람만 안다
    ("청소담당", "개발1"), ("청소담당", "윤디자"),
]

from collections import defaultdict, deque


def adjacency(edges):
    adj = defaultdict(set)
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    return {k: sorted(v) for k, v in adj.items()}


ADJ = adjacency(EDGES)
print("노드", len(ADJ), "/ 엣지", len(EDGES))
# 출력: 노드 19 / 엣지 28

# %% [markdown]
# ## 2. 네 가지 지표 — 네 가지 «중요하다»
#
# 노드 수를 $n$, 이웃 집합을 $N(v)$, $s\to t$ 최단 경로 수를 $\sigma_{st}$,
# 그중 $v$ 를 지나는 것을 $\sigma_{st}(v)$ 라 하자.
#
# | 지표 | 수식 | 묻는 질문 |
# |---|---|---|
# | 차수 | $C_D(v)=\dfrac{|N(v)|}{n-1}$ | 아는 사람이 많은가 |
# | 근접 | $C_C(v)=\dfrac{n-1}{\sum_{u} d(v,u)}$ | 소문이 빨리 퍼지는가 |
# | 매개 | $C_B(v)=\dfrac{2}{(n-1)(n-2)}\displaystyle\sum_{s\neq v\neq t}\frac{\sigma_{st}(v)}{\sigma_{st}}$ | 없으면 갈라지는가 |
# | 고유벡터 | $\lambda x = A x$ (최대 고윳값의 고유벡터) | 힘 있는 이웃을 가졌는가 |
#
# 넷은 서로 다른 질문이다. 그러니 답이 서로 다른 건 버그가 아니라 **정보**다.

# %%
def degree_c(adj):
    n = len(adj) - 1
    return {v: len(nb) / n for v, nb in adj.items()}


def bfs_dist(adj, s):
    d = {s: 0}
    q = deque([s])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in d:
                d[v] = d[u] + 1
                q.append(v)
    return d


def closeness_c(adj):
    out = {}
    for v in adj:
        d = bfs_dist(adj, v)
        total = sum(d.values())
        out[v] = (len(d) - 1) / total if total else 0.0
    return out


def betweenness_c(adj):
    """브랜디스 알고리즘. 무향이라 쌍을 두 번 세므로 (n-1)(n-2) 로 나눈다."""
    cb = {v: 0.0 for v in adj}
    for s in adj:
        stack, pred = [], {v: [] for v in adj}
        sigma = {v: 0 for v in adj}; sigma[s] = 1
        dist = {v: -1 for v in adj}; dist[s] = 0
        q = deque([s])
        while q:
            v = q.popleft(); stack.append(v)
            for w in adj[v]:
                if dist[w] < 0:
                    dist[w] = dist[v] + 1; q.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]; pred[w].append(v)
        delta = {v: 0.0 for v in adj}
        while stack:
            w = stack.pop()
            for v in pred[w]:
                delta[v] += sigma[v] / sigma[w] * (1 + delta[w])
            if w != s:
                cb[w] += delta[w]
    n = len(adj)
    return {v: s / ((n - 1) * (n - 2)) for v, s in cb.items()}


def eigen_c(adj, rounds=200):
    x = {v: 1.0 for v in adj}
    for _ in range(rounds):
        nx = {v: sum(x[u] for u in adj[v]) for v in adj}
        norm = max(nx.values()) or 1.0
        nx = {v: y / norm for v, y in nx.items()}
        if all(abs(nx[v] - x[v]) < 1e-12 for v in adj):
            break
        x = nx
    return x


METRICS = {
    "차수": degree_c(ADJ),
    "근접": closeness_c(ADJ),
    "매개": betweenness_c(ADJ),
    "고유벡터": eigen_c(ADJ),
}
NAMES = list(METRICS)

print(f"{'노드':<8}" + "".join(f"{k:>10}" for k in NAMES))
print("-" * 48)
for v in sorted(ADJ, key=lambda x: -METRICS["차수"][x]):
    print(f"{v:<8}" + "".join(f"{METRICS[k][v]:>10.3f}" for k in NAMES))
# 출력:
# 노드              차수        근접        매개      고유벡터
# ------------------------------------------------
# 김개발          0.389     0.429     0.504     1.000
# 정영업          0.222     0.409     0.484     0.165
# 개발1          0.167     0.340     0.093     0.481
# 개발2          0.167     0.327     0.009     0.576
# 개발3          0.167     0.316     0.003     0.602
# 개발4          0.167     0.316     0.003     0.599
# 개발5          0.167     0.316     0.003     0.562
# 오영업          0.167     0.321     0.013     0.086
# 서영업          0.167     0.333     0.294     0.077
# 강디자          0.167     0.360     0.182     0.149
# 윤디자          0.167     0.295     0.052     0.106
# 대표           0.167     0.462     0.597     0.364
# 공장A          0.167     0.269     0.209     0.027
# 개발6          0.111     0.310     0.000     0.432
# 한영업          0.111     0.300     0.000     0.069
# 임디자          0.111     0.281     0.000     0.071
# 공장B          0.111     0.217     0.000     0.010
# 공장C          0.111     0.217     0.000     0.010
# 청소담당         0.111     0.281     0.044     0.162

# %% [markdown]
# ## 3. 1등은 지표마다 다르다 — 하지만 그건 아직 «값어치 있는 정보»가 아니다
#
# 1등만 보면 «김개발 또는 대표가 제일 중요합니다» 같은 보고서가 나온다.
# 조직도를 보면 이미 아는 사실이다. 그래프를 돌린 값어치가 없다.

# %%
for k in NAMES:
    rank = sorted(METRICS[k], key=lambda v: -METRICS[k][v])
    print(f"{k:<8} 1등 {rank[0]:<8} 2등 {rank[1]:<8} 3등 {rank[2]:<8}")
# 출력:
# 차수       1등 김개발      2등 정영업      3등 개발1
# 근접       1등 대표       2등 김개발      3등 정영업
# 매개       1등 대표       2등 김개발      3등 정영업
# 고유벡터     1등 김개발      2등 개발3      3등 개발4

# %% [markdown]
# ## 4. 값어치는 «순위 차이»에 있다
#
# 노드 $v$ 의 차수 순위를 $r_D(v)$, 매개 순위를 $r_B(v)$ 라 할 때
#
# $$\mathrm{gap}(v) \;=\; r_D(v) - r_B(v)$$
#
# 가 크게 양수인 노드 — **차수 순위는 뒤쪽인데 매개 순위는 앞쪽인 노드** — 가
# 조직도에도, 인기 순위에도 안 뜨는 급소 후보다. (순위는 1이 제일 높음)

# %%
def ranks(score):
    """1이 가장 높음. 동점은 평균 순위."""
    order = sorted(score, key=lambda v: -score[v])
    out, i = {}, 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and score[order[j + 1]] == score[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return out


R = {k: ranks(METRICS[k]) for k in NAMES}
gap = {v: R["차수"][v] - R["매개"][v] for v in ADJ}

print(f"{'노드':<8}{'차수순위':>8}{'매개순위':>8}{'gap':>8}{'매개값':>9}")
print("-" * 41)
for v in sorted(ADJ, key=lambda v: -gap[v])[:6]:
    print(f"{v:<8}{R['차수'][v]:>8.1f}{R['매개'][v]:>8.1f}{gap[v]:>8.1f}{METRICS['매개'][v]:>9.3f}")
# 출력:
# 노드          차수순위    매개순위     gap      매개값
# -----------------------------------------
# 청소담당         16.5     9.0     7.5    0.044
# 대표            8.0     1.0     7.0    0.597
# 서영업           8.0     4.0     4.0    0.294
# 공장A           8.0     5.0     3.0    0.209
# 강디자           8.0     6.0     2.0    0.182
# 개발1           8.0     7.0     1.0    0.093

# %% [markdown]
# ### 순위 차이만으로는 부족하다 — 절대 수준도 같이 본다
#
# `청소담당`은 gap이 제일 크지만 매개 자체가 0.044로 바닥이다. 순위가 워낙 뒤라서
# 조금만 올라와도 gap이 커지는 것뿐이다. 순위 차이는 «후보를 좁히는 필터»이고,
# 최종 판단은 **매개 절댓값이 상위권인가**를 같이 봐야 한다.
#
# 실무 규칙: **매개 상위 $k$ 안에 들면서 차수 상위 $k$ 에는 없는 노드**를 뽑는다.

# %%
TOPK = 5
top_b = sorted(ADJ, key=lambda v: -METRICS["매개"][v])[:TOPK]
top_d = sorted(ADJ, key=lambda v: -METRICS["차수"][v])[:TOPK]
hidden = [v for v in top_b if v not in set(top_d)]
print(f"매개 상위 {TOPK}: {top_b}")
print(f"차수 상위 {TOPK}: {top_d}")
print(f"→ 매개 상위인데 차수 상위는 아닌 사람: {hidden}")
# 출력:
# 매개 상위 5: ['대표', '김개발', '정영업', '서영업', '공장A']
# 차수 상위 5: ['김개발', '정영업', '개발1', '개발2', '개발3']
# → 매개 상위인데 차수 상위는 아닌 사람: ['대표', '서영업', '공장A']

# %% [markdown]
# ## 5. 검증 — 진짜로 빼 보면 안다
#
# 급소의 정의는 «없으면 갈라지는가»였다. 그러면 실제로 노드를 지우고
# 그래프가 몇 조각으로 쪼개지는지, 무엇이 떨어져 나가는지 세면 된다.

# %%
def components(adj):
    seen, comps = set(), []
    for s in adj:
        if s in seen:
            continue
        d = bfs_dist(adj, s)
        comps.append(sorted(d))
        seen |= set(d)
    return sorted(comps, key=len, reverse=True)


def remove(adj, v):
    return {u: [w for w in nb if w != v] for u, nb in adj.items() if u != v}


print(f"{'제거':<8}{'차수순위':>8}{'매개순위':>8}{'조각':>6}  떨어져 나간 노드")
print("-" * 62)
for v in ["(없음)", "김개발", "개발1", "청소담당", "서영업", "대표"]:
    sub = ADJ if v == "(없음)" else remove(ADJ, v)
    comps = components(sub)
    lost = [] if len(comps) == 1 else sorted(x for c in comps[1:] for x in c)
    rk = "  -   -" if v == "(없음)" else f"{R['차수'][v]:>8.1f}{R['매개'][v]:>8.1f}"
    print(f"{v:<8}{rk}{len(comps):>6}  {', '.join(lost) if lost else '-'}")
# 출력:
# 제거          차수순위    매개순위    조각  떨어져 나간 노드
# --------------------------------------------------------------
# (없음)     -   -     1  -
# 김개발          1.0     2.0     1  -
# 개발1           8.0     7.0     1  -
# 청소담당        16.5     9.0     1  -
# 서영업           8.0     4.0     2  공장A, 공장B, 공장C
# 대표            8.0     1.0     2  공장A, 공장B, 공장C, 서영업, 오영업, 정영업, 한영업

# %% [markdown]
# 결과가 말하는 것:
#
# - **김개발**을 빼도 회사는 안 갈라진다. 차수 1등·고유벡터 1등인데도 그렇다.
#   개발팀은 자기들끼리도 이어져 있고, 대표를 통한 우회로가 있다.
#   *차수 1등은 «대체 가능한 인기인»일 수 있다.*
# - **서영업**은 차수 공동 8위(0.167)로 지극히 평범하다. 그런데 빼면 공장 A·B·C가
#   통째로 떨어져 나간다. 조직도에도 안 뜨고 차수 순위에도 안 뜬다.
#   휴가를 가면 공장이 멈춘다. **이 사람이 «아무도 모르는 급소»다.**
# - **대표**도 차수 공동 8위인데 매개 1등이고, 빼면 7명이 떨어져 나간다.
#   다만 대표는 조직도만 봐도 아는 사람이다 — 그래프가 «새로» 알려준 건 서영업 쪽이다.
#
# 즉 순위 차이는 두 방향으로 값어치가 있다.
# 차수↑/매개↓ 는 «빼도 되는 사람», 차수↓/매개↑ 는 «빼면 안 되는 사람»이다.

# %%
print(f"서영업 — 차수 {METRICS['차수']['서영업']:.3f}(순위 {R['차수']['서영업']:.1f}), "
      f"매개 {METRICS['매개']['서영업']:.3f}(순위 {R['매개']['서영업']:.1f})")
print(f"김개발 — 차수 {METRICS['차수']['김개발']:.3f}(순위 {R['차수']['김개발']:.1f}), "
      f"매개 {METRICS['매개']['김개발']:.3f}(순위 {R['매개']['김개발']:.1f})")
print("\n«중요한 사람을 찾아 주세요»에는 되물어야 한다:")
for q in ["아는 사람이 많은 사람인가 (차수)",
          "없으면 조직이 갈라지는 사람인가 (매개)",
          "소문이 제일 빨리 퍼지는 사람인가 (근접)",
          "힘 있는 사람과 이어진 사람인가 (고유벡터)"]:
    print("  -", q)
# 출력:
# 서영업 — 차수 0.167(순위 8.0), 매개 0.294(순위 4.0)
# 김개발 — 차수 0.389(순위 1.0), 매개 0.504(순위 2.0)
#
# «중요한 사람을 찾아 주세요»에는 되물어야 한다:
#   - 아는 사람이 많은 사람인가 (차수)
#   - 없으면 조직이 갈라지는 사람인가 (매개)
#   - 소문이 제일 빨리 퍼지는 사람인가 (근접)
#   - 힘 있는 사람과 이어진 사람인가 (고유벡터)

# %% [markdown]
# ## 6. 시각화
#
# - **왼쪽(범프 차트)**: 네 지표에서 각 사람의 순위가 어떻게 움직이는가.
#   선이 가파를수록 «지표에 따라 평가가 갈리는 사람»이다. 서영업은 차수 8위에서
#   매개 4위로 올라가고, 개발3은 고유벡터 2위인데 매개는 바닥이다.
# - **오른쪽(산점도)**: 차수(x) 대 매개(y). 오른쪽 아래는 «인기만 많은 사람»,
#   **왼쪽 위**가 찾던 영역 — 차수는 낮은데 매개가 높은 급소다.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

CAT = {"서영업": "#2a78d6", "김개발": "#eb6834", "대표": "#1baf7a", "개발3": "#eda100"}
MUTED, INK, GRID, SURF = "#c3c2b7", "#0b0b0b", "#e1e0d9", "#fcfcfb"
HL = list(CAT)

fig = make_subplots(
    rows=1, cols=2, horizontal_spacing=0.13,
    subplot_titles=("지표별 순위 이동 (위쪽이 1등)", "차수 대 매개 — 왼쪽 위가 숨은 급소"),
)

# --- 왼쪽: 범프 차트 -------------------------------------------------
for v in sorted(ADJ):
    if v in HL:
        continue
    fig.add_trace(go.Scatter(
        x=NAMES, y=[R[k][v] for k in NAMES], mode="lines",
        line=dict(color=MUTED, width=1), hoverinfo="skip", showlegend=False), 1, 1)
for v in HL:
    fig.add_trace(go.Scatter(
        x=NAMES, y=[R[k][v] for k in NAMES], mode="lines+markers+text",
        text=[""] * (len(NAMES) - 1) + [v], textposition="middle right",
        textfont=dict(color=INK, size=11), cliponaxis=False,
        line=dict(color=CAT[v], width=2),
        marker=dict(size=9, color=CAT[v], line=dict(width=2, color=SURF)),
        name=v, legendgroup=v,
        hovertemplate=f"{v} · %{{x}} 순위 %{{y}}<extra></extra>"), 1, 1)

# --- 오른쪽: 차수 대 매개 산점도 --------------------------------------
rest = [v for v in sorted(ADJ) if v not in HL]
fig.add_trace(go.Scatter(
    x=[METRICS["차수"][v] for v in rest], y=[METRICS["매개"][v] for v in rest],
    mode="markers", marker=dict(size=9, color=MUTED, line=dict(width=2, color=SURF)),
    text=rest, hovertemplate="%{text}<br>차수 %{x:.3f} · 매개 %{y:.3f}<extra></extra>",
    showlegend=False), 1, 2)
for v in HL:
    fig.add_trace(go.Scatter(
        x=[METRICS["차수"][v]], y=[METRICS["매개"][v]], mode="markers+text",
        marker=dict(size=13, color=CAT[v], line=dict(width=2, color=SURF)),
        text=[v], textposition="top center", textfont=dict(color=INK, size=11),
        name=v, legendgroup=v, showlegend=False,
        hovertemplate=f"{v}<br>차수 %{{x:.3f}} · 매개 %{{y:.3f}}<extra></extra>"), 1, 2)

fig.update_yaxes(autorange="reversed", title_text="순위", gridcolor=GRID,
                 dtick=2, row=1, col=1)
fig.update_xaxes(gridcolor=GRID, range=[-0.3, 3.75], row=1, col=1)
fig.update_xaxes(title_text="차수 중심성", gridcolor=GRID, row=1, col=2)
fig.update_yaxes(title_text="매개 중심성", gridcolor=GRID, row=1, col=2)
fig.update_layout(
    title="1등이 아니라 지표 사이의 순위 차이가 급소를 가리킨다",
    template="simple_white", plot_bgcolor=SURF, paper_bgcolor=SURF,
    font=dict(color=INK, size=12), width=1000, height=520,
    legend=dict(orientation="h", y=-0.16, x=0.5, xanchor="center", title_text=""),
    margin=dict(l=70, r=30, t=90, b=90),
)

_show(fig)
fig.write_image("expy.png", scale=2)
print("saved expy.png")
# 출력: saved expy.png

# %% [markdown]
# ## 정리
#
# | 보는 방식 | 나오는 답 | 값어치 |
# |---|---|---|
# | 지표 하나의 1등 | 김개발 / 대표 | 조직도로도 아는 사실 |
# | 네 지표의 1등 비교 | 지표마다 다르다 | 「어떤 중요함이냐」를 되묻게 됨 |
# | **지표 사이 순위 차이** | **서영업** | **아무도 모르던 급소** |
#
# - 차수↓ / 매개↑ = 다리 역할. 조직의 단일 장애점(SPOF). 백업 인력을 붙여야 한다.
# - 차수↑ / 매개↓ = 인기 있지만 대체 가능. 빠져도 우회로가 있다.
# - 순위 차이는 **후보를 좁히는 필터**다. 매개 절댓값과 «실제로 빼 보는 검증»을
#   함께 써야 «순위가 뒤라서 gap만 큰» 노드(청소담당)에 속지 않는다.
