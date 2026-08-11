# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# %% [markdown]
# # 다익스트라의 `if d > dist.get(u, inf): continue`
#
# 7장 `ex3_weights.py`의 다익스트라에는 이런 두 줄이 있다.
#
# ```python
# d, u = heapq.heappop(pq)
# if d > dist.get(u, float("inf")):
#     continue
# ```
#
# 이 검사는 **이미 더 짧은 거리로 확정된 노드의 «낡은 항목»(stale entry)을 건너뛰기** 위한 것이다.
# 큐에 같은 노드를 여러 번 밀어 넣는 구현(=lazy insertion)에서만 필요한 검사다.
#
# ## 왜 중복이 생기나
#
# 교과서 다익스트라는 우선순위 큐에 노드를 하나씩만 두고,
# 더 짧은 거리를 찾으면 그 항목의 키를 낮춘다(**decrease-key**).
#
# $$\text{dist}[v] \leftarrow \text{dist}[u] + w(u,v) \quad\Rightarrow\quad \text{DecreaseKey}(Q, v, \text{dist}[v])$$
#
# 그런데 파이썬 `heapq`에는 decrease-key가 없다. 힙 안의 임의 원소를 찾으려면 $O(n)$이고,
# 위치를 따로 관리하는 인덱스드 힙을 직접 짜야 한다.
# 그래서 실무 구현은 대부분 **키를 낮추는 대신 새 항목을 하나 더 push**한다.
#
# $$\text{push}(Q, (\text{dist}[v],\, v)) \quad\text{— 기존 } (\text{old},\, v) \text{ 는 힙에 그대로 남는다}$$
#
# 남은 `(old, v)`가 **낡은 항목**이다. `old > dist[v]`이므로 힙에서 나중에 나오고,
# 나올 때는 이미 `v`가 더 짧은 거리로 확정된 뒤다. 그래서 그냥 버려야 한다.
# `d > dist.get(u, inf)` 가 정확히 "내가 들고 나온 거리가 지금 알려진 최단보다 크다 = 나는 낡았다"는 판정이다.

# %%
import heapq
import random
from collections import defaultdict


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


INF = float("inf")

# 낡은 항목이 반드시 생기는 최소 그래프.
#   A --10--> B      (B를 먼저 10으로 발견)
#   A --1--> C --2--> B   (나중에 B를 3으로 다시 발견)
EDGES = [("A", "B", 10), ("A", "C", 1), ("C", "B", 2), ("B", "D", 1)]
print("엣지:", EDGES)
# 출력: 엣지: [('A', 'B', 10), ('A', 'C', 1), ('C', 'B', 2), ('B', 'D', 1)]

# %% [markdown]
# ## 1. 낡은 항목이 힙에 남는 과정을 눈으로 보기
#
# 힙에서 꺼낼 때마다 `(꺼낸 거리 d, 노드 u, 현재 dist[u])`를 찍는다.
# `d > dist[u]`인 순간이 낡은 항목이다.

# %%
def dijkstra_traced(edges, start, guard=True, directed=True):
    """guard=False 로 두면 낡은 항목 검사를 생략한다. trace 로그를 함께 반환."""
    adj = defaultdict(list)
    for a, b, w in edges:
        adj[a].append((b, w))
        if not directed:
            adj[b].append((a, w))

    dist = {start: 0.0}
    pq = [(0.0, start)]
    trace = []          # (pop 순번, d, u, dist[u], 낡음 여부)
    pushes = 0          # 힙에 밀어 넣은 횟수
    pops = 0            # 힙에서 꺼낸 횟수
    expansions = 0      # 실제로 이웃을 훑은 횟수(= 노드 전개)
    scans = 0           # 훑은 엣지 수

    while pq:
        d, u = heapq.heappop(pq)
        pops += 1
        stale = d > dist.get(u, INF)
        trace.append((pops, d, u, dist.get(u, INF), stale))
        if guard and stale:
            continue
        expansions += 1
        for v, w in adj[u]:
            scans += 1
            nd = d + w
            if nd < dist.get(v, INF):
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
                pushes += 1

    stats = dict(pushes=pushes, pops=pops, expansions=expansions, scans=scans)
    return dist, trace, stats


dist_on, trace_on, stats_on = dijkstra_traced(EDGES, "A", guard=True)

print("pop 순서 (guard 있음)")
for i, d, u, cur, stale in trace_on:
    mark = "  <-- 낡은 항목, continue" if stale else ""
    print(f"  {i}: pop d={d:>4} u={u}  dist[{u}]={cur}{mark}")
print("dist =", dist_on)
print("stats =", stats_on)
# 출력: pop 순서 (guard 있음)
# 출력:   1: pop d= 0.0 u=A  dist[A]=0.0
# 출력:   2: pop d= 1.0 u=C  dist[C]=1.0
# 출력:   3: pop d= 3.0 u=B  dist[B]=3.0
# 출력:   4: pop d= 4.0 u=D  dist[D]=4.0
# 출력:   5: pop d=10.0 u=B  dist[B]=3.0  <-- 낡은 항목, continue
# 출력: dist = {'A': 0.0, 'B': 3.0, 'C': 1.0, 'D': 4.0}
# 출력: stats = {'pushes': 4, 'pops': 5, 'expansions': 4, 'scans': 4}

# %% [markdown]
# 5번째 pop이 바로 그 낡은 항목이다.
# `A→B` 직행 10으로 B를 처음 발견해 `(10, B)`를 push했는데,
# 그 뒤 `A→C→B`로 3이 나와 `(3, B)`를 다시 push했다.
# `(10, B)`는 힙에서 지우지 못했으니 그대로 남아 마지막에 나온다.
# 이때 `dist[B]`는 이미 3으로 확정되어 있으므로 $10 > 3$ → `continue`.
#
# 참고로 `pops(5) > pushes(4) + 1`이 아니라 `pops = pushes + 1`(시작 노드 push 포함)인데,
# **push 횟수가 노드 수(4)보다 많다**는 점이 중복 삽입의 흔적이다.

# %% [markdown]
# ## 2. guard를 빼면 어떻게 되나 — 틀리는가, 느려지는가
#
# 가중치가 모두 음이 아니면 **결과는 여전히 맞다**.
# 낡은 항목으로 전개해도 $d_{\text{stale}} > \text{dist}[u]$이므로
# $$d_{\text{stale}} + w(u,v) > \text{dist}[u] + w(u,v) \ge \text{dist}[v]$$
# 가 되어 `nd < dist[v]` 조건을 통과하지 못한다. 즉 덮어쓰기가 일어나지 않는다.
#
# 대신 **이웃을 한 번 더 훑는 헛일**을 한다. guard는 정확성 장치가 아니라
# "이미 끝난 노드를 다시 전개하지 않는다"는 **비용 장치**다.
# (책 코드가 `nd = d + c`로 pop해 온 `d`를 쓰기 때문에 이 안전성이 성립한다.
#  `nd = dist[u] + c`로 바꿔 쓰면 guard 없이도 값은 같지만 재전개가 연쇄되어 더 나빠진다.)

# %%
dist_off, trace_off, stats_off = dijkstra_traced(EDGES, "A", guard=False)
print("dist 동일?", dist_on == dist_off, dist_off)
print("guard 있음:", stats_on)
print("guard 없음:", stats_off)
# 출력: dist 동일? True {'A': 0.0, 'B': 3.0, 'C': 1.0, 'D': 4.0}
# 출력: guard 있음: {'pushes': 4, 'pops': 5, 'expansions': 4, 'scans': 4}
# 출력: guard 없음: {'pushes': 4, 'pops': 5, 'expansions': 5, 'scans': 5}

# %% [markdown]
# ## 3. 규모가 커지면 낭비도 커진다
#
# 무작위 그래프에서 guard 유무에 따른 **엣지 스캔 수**를 비교한다.
# 낡은 항목은 노드를 발견한 뒤 더 짧은 길을 찾을 때마다 하나씩 쌓이므로,
# 밀도가 높을수록(간선이 많을수록) 헛일도 늘어난다.

# %%
def random_graph(n, m, seed=0):
    rnd = random.Random(seed)
    nodes = [f"n{i}" for i in range(n)]
    edges = []
    for _ in range(m):
        a, b = rnd.sample(nodes, 2)
        edges.append((a, b, rnd.randint(1, 50)))
    return nodes, edges


rows = []
for n, m in [(50, 150), (50, 400), (200, 800), (200, 3000), (500, 5000)]:
    nodes, edges = random_graph(n, m, seed=7)
    d1, _, s_on = dijkstra_traced(edges, nodes[0], guard=True)
    d2, _, s_off = dijkstra_traced(edges, nodes[0], guard=False)
    assert d1 == d2, "결과는 같아야 한다"
    stale = s_on["pops"] - s_on["expansions"]
    rows.append(
        dict(
            label=f"n={n}, m={m}",
            pops=s_on["pops"],
            stale=stale,
            scans_on=s_on["scans"],
            scans_off=s_off["scans"],
            waste_pct=100.0 * (s_off["scans"] - s_on["scans"]) / max(s_on["scans"], 1),
        )
    )

for r in rows:
    print(
        f"{r['label']:>14} | pop {r['pops']:>5} | 낡은항목 {r['stale']:>4} "
        f"| 스캔 guard {r['scans_on']:>5} / no-guard {r['scans_off']:>5} "
        f"| 추가비용 +{r['waste_pct']:.1f}%"
    )
# 출력:      n=50, m=150 | pop    60 | 낡은항목   11 | 스캔 guard   147 / no-guard   176 | 추가비용 +19.7%
# 출력:      n=50, m=400 | pop    90 | 낡은항목   40 | 스캔 guard   400 / no-guard   704 | 추가비용 +76.0%
# 출력:     n=200, m=800 | pop   260 | 낡은항목   66 | 스캔 guard   776 / no-guard  1048 | 추가비용 +35.1%
# 출력:    n=200, m=3000 | pop   429 | 낡은항목  229 | 스캔 guard  3000 / no-guard  6398 | 추가비용 +113.3%
# 출력:    n=500, m=5000 | pop   947 | 낡은항목  447 | 스캔 guard  5000 / no-guard  9482 | 추가비용 +89.6%

# %% [markdown]
# `guard`가 있으면 스캔 수가 (도달 가능한) 엣지 수에 수렴한다 — 각 노드를 딱 한 번만 전개하므로.
# 없으면 낡은 항목만큼 노드를 재전개해 스캔이 최대 두 배 넘게 늘어난다.
#
# ## 4. 대안 — `visited` 집합
#
# 같은 목적을 집합으로도 달성할 수 있다. `dist` 비교 대신 "확정 표시"를 남기는 방식이다.
#
# ```python
# if u in done:
#     continue
# done.add(u)
# ```
#
# 음이 아닌 가중치에서 두 방식은 완전히 동등하다(전개 횟수도 같다).
# `d > dist[u]`는 별도 자료구조가 필요 없고, `done` 집합은 부동소수 비교를 피할 수 있다.
# 하지만 다음 절에서 보듯 **음수 간선이 섞이면 두 방식이 갈린다**.

# %%
def dijkstra_visited(edges, start, directed=True):
    adj = defaultdict(list)
    for a, b, w in edges:
        adj[a].append((b, w))
        if not directed:
            adj[b].append((a, w))
    dist = {start: 0.0}
    done = set()
    pq = [(0.0, start)]
    scans = 0
    while pq:
        d, u = heapq.heappop(pq)
        if u in done:          # d > dist[u] 검사와 같은 역할
            continue
        done.add(u)
        for v, w in adj[u]:
            scans += 1
            nd = d + w
            if nd < dist.get(v, INF):
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist, scans


nodes, edges = random_graph(200, 3000, seed=7)
dA, _, sA = dijkstra_traced(edges, nodes[0], guard=True)
dB, sB = dijkstra_visited(edges, nodes[0])
print("두 방식 결과 동일?", dA == dB, "| 스캔", sA["scans"], sB)
# 출력: 두 방식 결과 동일? True | 스캔 3000 3000

# %% [markdown]
# ## 5. 음수 간선 — `d > dist[u]`와 `visited`가 갈리는 지점
#
# 음수 간선이 있으면 "먼저 pop된 노드는 확정"이라는 다익스트라의 전제가 깨진다.
# 이때 두 guard의 성격 차이가 드러난다.
#
# * `if d > dist[u]: continue` — **거리 기준** 판정이다. 나중에 `dist[u]`가 더 낮아지면
#   그 시점에 `(새 거리, u)`가 새로 push되고, 그 항목은 `d == dist[u]`이므로 낡지 않았다.
#   그래서 노드가 **다시 전개된다**. 결과적으로 SPFA(Bellman–Ford 큐 버전)처럼 동작해
#   음수 간선이 있어도 (음수 사이클이 없으면) 답을 스스로 고친다. 대신 최악에는 지수 시간.
# * `if u in done: continue` — **방문 기준** 판정이다. 한 번 전개한 노드는 두 번 다시 안 본다.
#   `dist[u]`가 뒤늦게 낮아져도 전파되지 않아 **하류 노드가 틀린 값에 갇힌다**.
#
# 아래 그래프: `A→B=2, A→C=1, C→D=1, D→B=-5, B→E=1`.
# `B`의 진짜 최단은 $1+1-5=-3$, `E`는 $-2$다.
# 하지만 `B`는 힙에서 먼저 $2$로 pop되어 `E=3`을 만들고,
# 그 뒤에야 `D`가 `B`를 $-3$으로 낮춘다.

# %%
NEG = [("A", "B", 2), ("A", "C", 1), ("C", "D", 1), ("D", "B", -5), ("B", "E", 1)]
d_dist, _, _ = dijkstra_traced(NEG, "A", guard=True)     # d > dist[u] 방식
d_none, _, _ = dijkstra_traced(NEG, "A", guard=False)    # guard 없음
d_seen, _ = dijkstra_visited(NEG, "A")                   # visited 집합 방식
print("정답            : B=-3, E=-2")
print("d > dist[u]     :", d_dist)
print("guard 없음      :", d_none)
print("visited 집합    :", d_seen, " <-- E 가 갱신되지 않았다" if d_seen.get("E") != -2 else "")
# 출력: 정답            : B=-3, E=-2
# 출력: d > dist[u]     : {'A': 0.0, 'B': -3.0, 'C': 1.0, 'D': 2.0, 'E': -2.0}
# 출력: guard 없음      : {'A': 0.0, 'B': -3.0, 'C': 1.0, 'D': 2.0, 'E': -2.0}
# 출력: visited 집합    : {'A': 0.0, 'B': -3.0, 'C': 1.0, 'D': 2.0, 'E': 3.0}  <-- E 가 갱신되지 않았다

# %% [markdown]
# 정리하면 `if d > dist.get(u, inf): continue`는
#
# 1. **낡은 항목을 버리는 정리 장치** — 중복 push를 허용한 대가를 pop 시점에 청산한다.
# 2. **각 노드를 한 번만 전개하게 만드는 비용 장치** — 음이 아닌 가중치에서 $O((V+E)\log V)$를 지킨다.
# 3. **거리 기준이라 자기 교정 여지가 남는 안전한 형태** — `visited` 집합보다 덜 공격적이다.
#
# 그리고 7장의 교훈과 같은 결이다 — **가중치의 «뜻»(거리인가 강도인가, 부호가 무엇인가)이
# 알고리즘의 전제를 정한다.** 친밀도를 그대로 넣으면 guard가 아무리 정확해도 답은 틀린다.

# %% [markdown]
# ## 6. 시각화
#
# 왼쪽: 최소 그래프의 pop 타임라인(낡은 항목을 붉게 표시).
# 오른쪽: 규모별 엣지 스캔 수 — guard 유무 비교.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(
    rows=1,
    cols=2,
    subplot_titles=("힙 pop 타임라인 (낡은 항목 = 붉은 X)", "엣지 스캔 수: guard 유무"),
    column_widths=[0.42, 0.58],
)

xs = [t[0] for t in trace_on]
ys = [t[1] for t in trace_on]
labels = [f"{t[2]} (dist={t[3]})" for t in trace_on]
fresh = [i for i, t in enumerate(trace_on) if not t[4]]
stale_i = [i for i, t in enumerate(trace_on) if t[4]]

fig.add_trace(
    go.Scatter(
        x=[xs[i] for i in fresh],
        y=[ys[i] for i in fresh],
        mode="markers+text",
        text=[labels[i] for i in fresh],
        textposition="top center",
        marker=dict(size=14, color="#2b6cb0", symbol="circle"),
        name="유효한 항목",
    ),
    row=1,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=[xs[i] for i in stale_i],
        y=[ys[i] for i in stale_i],
        mode="markers+text",
        text=[labels[i] for i in stale_i],
        textposition="top center",
        marker=dict(size=18, color="#c53030", symbol="x"),
        name="낡은 항목 (continue)",
    ),
    row=1,
    col=1,
)
fig.update_xaxes(title_text="pop 순번", row=1, col=1, dtick=1, range=[0.3, 6.0])
fig.update_yaxes(title_text="꺼낸 거리 d", row=1, col=1, range=[-1.5, 13])

fig.add_trace(
    go.Bar(
        x=[r["label"] for r in rows],
        y=[r["scans_on"] for r in rows],
        name="guard 있음",
        marker_color="#2b6cb0",
    ),
    row=1,
    col=2,
)
fig.add_trace(
    go.Bar(
        x=[r["label"] for r in rows],
        y=[r["scans_off"] for r in rows],
        name="guard 없음",
        marker_color="#c53030",
        text=[f"+{r['waste_pct']:.0f}%" for r in rows],
        textposition="outside",
    ),
    row=1,
    col=2,
)
fig.update_yaxes(title_text="훑은 엣지 수", row=1, col=2)
fig.update_layout(
    title_text="낡은 항목 건너뛰기(if d > dist[u]: continue)의 역할",
    barmode="group",
    template="plotly_white",
    height=520,
    width=1200,
)

_show(fig)

import os

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(out, scale=2)
print("saved:", out)
# 출력: saved: .../expy.png
