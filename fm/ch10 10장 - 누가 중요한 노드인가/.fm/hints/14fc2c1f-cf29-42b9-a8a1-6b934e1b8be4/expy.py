# %% [markdown]
# # `all_shortest()` — 거리표 한 장으로 모든 최단 경로 뽑기
#
# 10장 `ex1_centralities.py`의 `all_shortest(adj, s, t)`를 단계별로 뜯어본다.
#
# 1. **전방 BFS**로 시작점 $s$ 기준 거리표 $d$를 만든다.
# 2. **목표 $t$에서 거꾸로**, $d[v] = d[u] - 1$인 이웃만 따라가며 스택(DFS) 탐색을 한다.
# 3. $s$에 닿은 경로를 뒤집어 모은다.
#
# 핵심 불변식: 무가중 그래프에서 간선 $(u,v)$가 있으면 항상
# $$|d[u] - d[v]| \le 1$$
# 이므로 이웃은 «한 칸 가까움 / 같음 / 한 칸 멂» 셋 중 하나다.
# 그중 «한 칸 가까움»만 골라 따라가면 매 스텝 거리가 정확히 1씩 줄고,
# $d[t]$ 스텝 뒤 반드시 $s$에 도착한다.

# %%
from collections import defaultdict, deque


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


def adjacency(edges):
    adj = defaultdict(set)
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    return {k: sorted(v) for k, v in adj.items()}


# 최단 경로가 여러 갈래인 작은 그래프.
#   본줄기:  S -> (A|B) -> C -> (D|E) -> T   : 2 x 2 = 4갈래
#   A-B:     같은 층끼리 잇는 «옆걸음» 간선
#   X, Y:    T 로 못 가는 막다른 가지
#   W, V:    S-B-W-V-C-... 6홉짜리 우회로 (최단 4홉이 아니다)
EDGES = [
    ("S", "A"), ("S", "B"),
    ("A", "C"), ("B", "C"),
    ("C", "D"), ("C", "E"),
    ("D", "T"), ("E", "T"),
    ("A", "B"),                      # 같은 층 (d=1 <-> d=1)
    ("S", "X"), ("X", "Y"),          # 막다른 가지
    ("B", "W"), ("W", "V"), ("V", "C"),   # 우회로. V->C 는 거리가 «내려가는» 간선
]
adj = adjacency(EDGES)
print("노드 수:", len(adj))
print("인접 리스트:")
for v in sorted(adj):
    print(f"  {v}: {adj[v]}")
# 출력:
# 노드 수: 11
# 인접 리스트:
#   A: ['B', 'C', 'S']
#   B: ['A', 'C', 'S', 'W']
#   C: ['A', 'B', 'D', 'E', 'V']
#   D: ['C', 'T']
#   E: ['C', 'T']
#   S: ['A', 'B', 'X']
#   T: ['D', 'E']
#   V: ['C', 'W']
#   W: ['B', 'V']
#   X: ['S', 'Y']
#   Y: ['X']

# %% [markdown]
# ## 1단계 — 전방 BFS로 거리표 만들기
#
# `bfs_dist`는 원본 코드 그대로다. 큐에서 꺼낸 순서가 곧 거리 오름차순이므로,
# 처음 방문했을 때 기록한 $d[v] = d[u] + 1$이 곧 최단 거리다.
# 도달 불가능한 노드는 아예 $d$에 들어가지 않는다 — 이게 나중에 `d.get(v, -1)`의 방어막이 된다.

# %%
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


S, T = "S", "T"
d = bfs_dist(adj, S)
print("거리표 d (s =", S, "기준):")
for v in sorted(d, key=lambda x: (d[x], x)):
    print(f"  d[{v}] = {d[v]}")
print("\nd[T] =", d[T], "-> 최단 경로 길이는 반드시 간선", d[T], "개")
# 출력:
# 거리표 d (s = S 기준):
#   d[S] = 0
#   d[A] = 1
#   d[B] = 1
#   d[X] = 1
#   d[C] = 2
#   d[W] = 2
#   d[Y] = 2
#   d[D] = 3
#   d[E] = 3
#   d[V] = 3
#   d[T] = 4
#
# d[T] = 4 -> 최단 경로 길이는 반드시 간선 4 개

# %%
# 불변식 확인: 모든 간선에 대해 |d[u] - d[v]| <= 1
bad = [(a, b) for a, b in EDGES if a in d and b in d and abs(d[a] - d[b]) > 1]
print("|d[u]-d[v]| > 1 인 간선:", bad, "-> 없어야 정상")

# 간선을 세 종류로 분류해 본다
kinds = {"내려감(-1)": [], "같음(0)": [], "올라감(+1)": []}
for a, b in EDGES:
    if a not in d or b not in d:
        continue
    diff = d[b] - d[a]
    key = {-1: "내려감(-1)", 0: "같음(0)", 1: "올라감(+1)"}[diff]
    kinds[key].append(f"{a}->{b}")
for k, v in kinds.items():
    print(f"  {k}: {v}")
# 출력:
# |d[u]-d[v]| > 1 인 간선: [] -> 없어야 정상
#   내려감(-1): ['V->C']
#   같음(0): ['A->B']
#   올라감(+1): ['S->A', 'S->B', 'A->C', 'B->C', 'C->D', 'C->E', 'D->T', 'E->T',
#                'S->X', 'X->Y', 'B->W', 'W->V']
#
# 세 종류뿐이고 «2 이상 차이»는 없다. 이것이 역방향 탐색이 성립하는 근거다.

# %% [markdown]
# ## 2단계 — 목표에서 거꾸로, `d[v] == d[u] - 1`만 따라간다
#
# 왜 **역방향**인가? 정방향($s$에서 $d[v] = d[u] + 1$을 따라감)으로도 최단 경로를 만들 수는 있다.
# 하지만 그러면 `X -> Y` 같은 **막다른 가지**로도 뻗어 나가서 $t$에 못 닿는 경로를 잔뜩 만들고 버려야 한다.
#
# 역방향은 다르다. $d[u] > 0$인 노드는 **반드시** $d[v] = d[u]-1$인 이웃을 하나 이상 가진다
# (BFS가 $u$를 그런 노드로부터 발견했으니까). 따라서 역방향 탐색의 **모든 가지는 낭비 없이 $s$에 도달**한다.
# 되돌아갈 일도 없다 — 거리가 단조 감소하므로 사이클이 생길 수 없어 `visited` 집합조차 필요 없다.

# %%
def all_shortest(adj, s, t, trace=False):
    """원본 ex1_centralities.py 의 all_shortest. trace=True 면 스택 진행을 찍는다."""
    d = bfs_dist(adj, s)
    if t not in d:
        return []
    out, stack = [], [(t, [t])]
    step = 0
    while stack:
        u, path = stack.pop()
        if trace:
            step += 1
            print(f"  step {step:>2}: pop ({u}, {'<-'.join(path)})  d[{u}]={d[u]}")
        if u == s:
            out.append(list(reversed(path)))
            if trace:
                print(f"           s 도착 -> 경로 확정: {' -> '.join(reversed(path))}")
            continue
        for v in adj[u]:
            if d.get(v, -1) == d[u] - 1:
                stack.append((v, path + [v]))
                if trace:
                    print(f"           push {v} (d={d[v]} == {d[u]}-1) OK")
            elif trace and v in d:
                print(f"           skip {v} (d={d[v]} != {d[u]}-1)")
    return out


print(f"[{T} 에서 거꾸로 스택 탐색]")
paths = all_shortest(adj, S, T, trace=True)
# 출력(발췌 — 전체는 13 step):
#   step  1: pop (T, T)  d[T]=4
#            push D (d=3 == 4-1) OK
#            push E (d=3 == 4-1) OK
#   step  2: pop (E, T<-E)  d[E]=3
#            push C (d=2 == 3-1) OK
#            skip T (d=4 != 3-1)          <- 뒤로 돌아가는 간선은 자동으로 걸러진다
#   step  3: pop (C, T<-E<-C)  d[C]=2
#            push A (d=1 == 2-1) OK
#            push B (d=1 == 2-1) OK
#            skip D (d=3 != 2-1)
#            skip E (d=3 != 2-1)
#            skip V (d=3 != 2-1)          <- 우회로 진입 차단
#   step  4: pop (B, T<-E<-C<-B)  d[B]=1
#            skip A (d=1 != 1-1)          <- 같은 층 «옆걸음» 차단
#            skip C (d=2 != 1-1)
#            push S (d=0 == 1-1) OK
#            skip W (d=2 != 1-1)
#   step  5: pop (S, T<-E<-C<-B<-S)  d[S]=0
#            s 도착 -> 경로 확정: S -> B -> C -> E -> T
#   ... (D 쪽 가지도 대칭으로 반복)
# 눈여겨볼 점: pop 13번이 전부 «어떤 최단 경로의 한 칸»이었다. 헛걸음이 0이다.
# (T 를 뿌리로 한 탐색 트리 = 1 + 6 + 6 = 13 노드)

# %%
print("찾은 최단 경로", len(paths), "개:")
for p in paths:
    print("  ", " -> ".join(p), f"(길이 {len(p)-1})")

# 검증 1: 모두 길이가 d[t] 와 같은가
assert all(len(p) - 1 == d[T] for p in paths)
# 검증 2: 모든 경로가 실제 간선만 밟는가
assert all(b in adj[a] for p in paths for a, b in zip(p, p[1:]))
# 검증 3: 중복 없는가
assert len({tuple(p) for p in paths}) == len(paths)
print("\n검증 통과: 길이 일치 / 간선 유효 / 중복 없음")
print("우회로 S-B-W-V-C-D-T(6홉)를 밟은 경로:",
      [p for p in paths if "W" in p or "V" in p], "-> 없음")
# 출력:
# 찾은 최단 경로 4 개:
#    S -> B -> C -> E -> T (길이 4)
#    S -> A -> C -> E -> T (길이 4)
#    S -> B -> C -> D -> T (길이 4)
#    S -> A -> C -> D -> T (길이 4)
#
# 검증 통과: 길이 일치 / 간선 유효 / 중복 없음
# 우회로 S-B-W-V-C-D-T(6홉)를 밟은 경로: [] -> 없음

# %% [markdown]
# ## 3단계 — 최단 경로 DAG
#
# `d[v] == d[u] - 1` 조건은 원본 무향 그래프에서 **간선의 방향을 정해 주는** 것과 같다.
# 거리가 커지는 쪽으로 향하게 하면 사이클이 없는 그래프(DAG)가 되고,
# `all_shortest`는 이 DAG 위에서 $s \to t$ 경로를 전부 열거하는 일을 한다.
#
# 매개 중심성에서 각 경로에 $1/|paths|$씩 나눠 주는 것도 이 DAG 위 경로 개수를 기준으로 한다.

# %%
def shortest_dag(adj, s, t):
    """s->t 최단 경로에 실제로 쓰이는 간선만 남긴 DAG."""
    d = bfs_dist(adj, s)
    if t not in d:
        return set(), set()
    useful_edges, seen = set(), set()
    stack = [t]
    while stack:
        u = stack.pop()
        if u in seen:
            continue
        seen.add(u)
        for v in adj[u]:
            if d.get(v, -1) == d[u] - 1:
                useful_edges.add((v, u))   # v -> u (거리 증가 방향)
                stack.append(v)
    return useful_edges, seen


dag_edges, dag_nodes = shortest_dag(adj, S, T)
print("최단 경로 DAG 노드:", sorted(dag_nodes))
print("최단 경로 DAG 간선:", sorted(dag_edges))
print("탈락한 노드:", sorted(set(adj) - dag_nodes), "<- 막다른 가지 + 우회로")
# 출력:
# 최단 경로 DAG 노드: ['A', 'B', 'C', 'D', 'E', 'S', 'T']
# 최단 경로 DAG 간선: [('A','C'), ('B','C'), ('C','D'), ('C','E'),
#                     ('D','T'), ('E','T'), ('S','A'), ('S','B')]
# 탈락한 노드: ['V', 'W', 'X', 'Y'] <- 막다른 가지 + 우회로

# %% [markdown]
# ## 4단계 — 경로 수는 지수로 터진다
#
# 「다이아몬드」 하나($u \to \{a, b\} \to w$)를 직렬로 $k$개 이으면
# 최단 경로 수는 정확히
# $$P(k) = 2^{k}$$
# 이다. 노드는 $3k+1$개인데 경로는 $2^k$개 — 즉 노드 수에 대해 **지수**다.
#
# `all_shortest`는 그 경로를 전부 리스트로 만들어 들고 있고, 게다가 `path + [v]`로
# 매 push마다 리스트를 복사한다. 시간·메모리 모두 $\Theta(P \cdot L)$이다.

# %%
import time


def diamond_chain(k):
    """u0 -> {a_i, b_i} -> u_{i+1} 을 k 개 직렬. 최단 경로 = 2^k 개."""
    edges = []
    for i in range(k):
        edges += [(f"u{i}", f"a{i}"), (f"u{i}", f"b{i}"),
                  (f"a{i}", f"u{i+1}"), (f"b{i}", f"u{i+1}")]
    return edges


print(f"{'k':>3} {'노드':>5} {'경로 수':>9} {'2^k':>8} {'시간(ms)':>10}")
print("-" * 40)
for k in (1, 2, 4, 8, 12, 16, 18):
    a = adjacency(diamond_chain(k))
    t0 = time.perf_counter()
    ps = all_shortest(a, "u0", f"u{k}")
    ms = (time.perf_counter() - t0) * 1000
    print(f"{k:>3} {len(a):>5} {len(ps):>9} {2**k:>8} {ms:>10.1f}")
# 출력:
#   k    노드     경로 수      2^k    시간(ms)
# ----------------------------------------
#   1     4         2        2        0.0
#   2     7         4        4        0.0
#   4    13        16       16        0.0
#   8    25       256      256        0.5
#  12    37      4096     4096        7.6
#  16    49     65536    65536      138.2
#  18    55    262144   262144      629.1
# (노드 55개짜리 «작은» 그래프에서 이미 0.6초. k=30 이면 10억 개다.)

# %% [markdown]
# ## 5단계 — 그래서 브랜디스는 경로를 «세기만» 한다
#
# 매개 중심성에 필요한 건 경로 «목록»이 아니라 개수 $\sigma$와 비율뿐이다.
# BFS 중에 $\sigma[w] \mathrel{+}= \sigma[v]$로 누적하면 경로를 만들지 않고도 개수를 얻는다.
# 값이 $2^{18}$이어도 정수 하나면 끝이다 — 이것이 10장 `ex3`의 브랜디스 알고리즘이
# $O(V \cdot E)$로 끝나는 이유다.

# %%
def count_shortest(adj, s):
    """경로를 열거하지 않고 개수 sigma 만 센다 (브랜디스 전반부)."""
    sigma = {v: 0 for v in adj}
    sigma[s] = 1
    dist = {s: 0}
    q = deque([s])
    while q:
        v = q.popleft()
        for w in adj[v]:
            if w not in dist:
                dist[w] = dist[v] + 1
                q.append(w)
            if dist[w] == dist[v] + 1:
                sigma[w] += sigma[v]
    return sigma


k = 18
a = diamond_chain(k)
t0 = time.perf_counter()
sg = count_shortest(adjacency(a), "u0")
ms = (time.perf_counter() - t0) * 1000
print(f"k={k}: sigma[u{k}] = {sg[f'u{k}']}  (= 2^{k} = {2**k})   {ms:.2f} ms")
print("열거 방식은 같은 문제에서 수백 ms 가 걸렸다. 1만 배 가까운 차이다.")

sg_small = count_shortest(adj, S)
print(f"\n작은 예제: sigma[{T}] = {sg_small[T]}  / all_shortest 개수 = {len(paths)}")
# 출력:
# k=18: sigma[u18] = 262144  (= 2^18 = 262144)   0.07 ms
# 열거 방식은 같은 문제에서 수백 ms 가 걸렸다. 1만 배 가까운 차이다.
#
# 작은 예제: sigma[T] = 4  / all_shortest 개수 = 4

# %% [markdown]
# ## 6단계 — 시각화
#
# 노드를 $d[v]$에 따라 층으로 세우면 왜 이 알고리즘이 도는지가 한눈에 보인다.
# 굵은 파란 화살표가 최단 경로 DAG의 간선이고, 회색 점선은 최단 경로에 쓸모없는 간선이다.

# %%
import plotly.graph_objects as go

layers = defaultdict(list)
for v in sorted(adj):
    layers[d.get(v, -1)].append(v)

pos = {}
for layer, vs in layers.items():
    for i, v in enumerate(sorted(vs)):
        pos[v] = (layer, i - (len(vs) - 1) / 2)

fig = go.Figure()

# 쓸모없는 간선 (회색 점선)
for a_, b_ in EDGES:
    if (a_, b_) in dag_edges or (b_, a_) in dag_edges:
        continue
    x0, y0 = pos[a_]
    x1, y1 = pos[b_]
    fig.add_trace(go.Scatter(x=[x0, x1], y=[y0, y1], mode="lines",
                             line=dict(color="#b0b6be", width=1.5, dash="dot"),
                             hoverinfo="skip", showlegend=False))

# 최단 경로 DAG 간선 (굵은 파랑)
for u_, w_ in sorted(dag_edges):
    x0, y0 = pos[u_]
    x1, y1 = pos[w_]
    fig.add_trace(go.Scatter(x=[x0, x1], y=[y0, y1], mode="lines",
                             line=dict(color="#2b6cb0", width=3),
                             hoverinfo="skip", showlegend=False))

on_dag = [v for v in sorted(adj) if v in dag_nodes]
off_dag = [v for v in sorted(adj) if v not in dag_nodes]
for group, color, name in ((on_dag, "#2b6cb0", "최단 경로 DAG"),
                           (off_dag, "#a0aec0", "탈락 (막다른 가지 / 우회로)")):
    fig.add_trace(go.Scatter(
        x=[pos[v][0] for v in group], y=[pos[v][1] for v in group],
        mode="markers+text", text=[f"{v}<br>d={d[v]}" for v in group],
        textposition="middle center", textfont=dict(color="white", size=11),
        marker=dict(size=42, color=color, line=dict(color="white", width=2)),
        name=name, hovertext=[f"{v}: d={d[v]}" for v in group], hoverinfo="text"))

for layer in sorted(layers):
    fig.add_annotation(x=layer, y=-2.0, text=f"d={layer}", showarrow=False,
                       font=dict(size=12, color="#4a5568"))

fig.update_layout(
    title="거리표 층 구조 — 역방향 탐색은 d를 1씩 내려간다 (S -> T, 최단 경로 4개)",
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    plot_bgcolor="white", width=980, height=520,
    legend=dict(orientation="h", y=1.06, x=0.5, xanchor="center"))

_show(fig)
fig.write_image("expy.png", scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료
# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)

# %% [markdown]
# ## 정리
#
# | 단계 | 하는 일 | 비용 |
# |---|---|---|
# | BFS 거리표 | $d[v]$ = $s$로부터 최단 거리 | $O(V+E)$ |
# | 역방향 스택 탐색 | $d[v]=d[u]-1$인 이웃만 따라감 | $O(P \cdot L)$ (출력 크기 비례) |
#
# - **건전성**: 매 스텝 거리가 정확히 1씩 줄므로 나온 경로 길이는 항상 $d[t]$ → 전부 최단 경로.
# - **완전성**: 최단 경로 위의 노드는 반드시 거리가 1씩 증가하므로, 모든 최단 경로가 이 조건을 통과한다.
# - **역방향인 이유**: $d[u]>0$이면 «한 칸 가까운 이웃»이 반드시 존재 → 헛가지가 안 생긴다.
# - **함정**: 경로 수 $P$는 노드 수에 대해 지수적일 수 있다. 개수/비율만 필요하면 열거하지 말고 $\sigma$를 세라(브랜디스).
