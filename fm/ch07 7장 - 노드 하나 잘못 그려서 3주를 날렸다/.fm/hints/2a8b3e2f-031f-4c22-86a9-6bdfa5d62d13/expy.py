# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# 표준 라이브러리만으로도 계산 셀은 모두 실행된다. 시각화 셀만 plotly가 필요하다.

# %% [markdown]
# # 같은 숫자, 정반대 답 — `ex3_weights.py`의 A→C
#
# 7.3절의 사고를 최소 재현한다. 엣지에 붙은 숫자는 하나인데, 그 숫자를 무엇으로
# 읽느냐에 따라 «가장 좋은 경로»가 뒤집힌다.
#
# ```python
# EDGES = [("A", "B", 8), ("B", "C", 8), ("A", "D", 3), ("D", "C", 3)]
# ```
#
# A에서 C로 가는 길은 두 개뿐이다.
#
# | 경로 | 엣지 값 | 합 |
# |---|---|---|
# | A–B–C | 8, 8 | 16 |
# | A–D–C | 3, 3 | 6 |
#
# - **거리 해석** (값이 클수록 멀다: 비용, 시간, 요금) → 합이 **작은** 쪽이 좋다 → **A–D–C (6)**
# - **강도 해석** (값이 클수록 가깝다: 친밀도, 유사도, 거래액) → 값이 **큰** 쪽이 좋다 → **A–B–C (8+8)**
#
# 두 해석이 서로 다른 경로를 고른다. 데이터는 한 글자도 바뀌지 않았다.

# %%
import heapq
from collections import defaultdict


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


EDGES = [("A", "B", 8), ("B", "C", 8), ("A", "D", 3), ("D", "C", 3)]

PATHS = [["A", "B", "C"], ["A", "D", "C"]]
W = {(a, b): w for a, b, w in EDGES} | {(b, a): w for a, b, w in EDGES}


def path_weights(path):
    return [W[(u, v)] for u, v in zip(path, path[1:])]


for p in PATHS:
    ws = path_weights(p)
    print(f"{'-'.join(p):8} 값 {ws}  합 {sum(ws)}")
# 출력: A-B-C    값 [8, 8]  합 16
# 출력: A-D-C    값 [3, 3]  합 6

# %% [markdown]
# ## 1단계 — 거리로 읽기: 합을 최소화
#
# 최단 경로 알고리즘(다익스트라)이 전제하는 해석이다. 엣지 값 $w$를 그대로 비용으로 본다.
#
# $$\text{cost}(P)=\sum_{(u,v)\in P} w_{uv},\qquad P^{*}=\arg\min_P \text{cost}(P)$$

# %%
best_dist = min(PATHS, key=lambda p: sum(path_weights(p)))
print("거리 해석 최적:", "-".join(best_dist), "합", sum(path_weights(best_dist)))
# 출력: 거리 해석 최적: A-D-C 합 6

# %% [markdown]
# ## 2단계 — 강도로 읽기: 값이 큰 쪽을 고른다
#
# 친밀도·유사도·거래액은 크면 클수록 «가깝다». 그래서 좋은 경로의 기준이 뒤집힌다.
#
# $$P^{*}=\arg\max_P \sum_{(u,v)\in P} w_{uv}$$
#
# 그런데 다익스트라에 이 목적을 그대로 넣을 수는 없다. 그래서 예제는 **역수 변환**으로
# 강도를 거리로 바꾼다.
#
# $$c_{uv}=\frac{1}{w_{uv}}\quad\Rightarrow\quad \min_P \sum \frac{1}{w_{uv}}$$
#
# - A–B–C: $1/8+1/8=0.25$
# - A–D–C: $1/3+1/3\approx0.667$
#
# 역수 쪽에서도 A–B–C가 이긴다. **거리 6짜리 경로를 버리고 16짜리 경로를 고른 것이다.**

# %%
best_strength = max(PATHS, key=lambda p: sum(path_weights(p)))
print("강도 해석(합 최대):", "-".join(best_strength), "합", sum(path_weights(best_strength)))
for p in PATHS:
    inv = sum(1.0 / w for w in path_weights(p))
    print(f"  {'-'.join(p)} 역수합 {inv:.3f}")
# 출력: 강도 해석(합 최대): A-B-C 합 16
# 출력:   A-B-C 역수합 0.250
# 출력:   A-D-C 역수합 0.667

# %% [markdown]
# ## 3단계 — 책의 코드를 그대로 돌려 본다
#
# `ex3_weights.py`의 `dijkstra(..., as_distance=)` 플래그 하나가 두 세계를 가른다.
# `as_distance=False`이면 비용을 $1/w$로 바꿔 넣는다.

# %%
def dijkstra(edges, start, goal, as_distance=True):
    adj = defaultdict(list)
    for a, b, w in edges:
        cost = w if as_distance else 1.0 / w
        adj[a].append((b, cost))
        adj[b].append((a, cost))
    dist = {start: 0.0}
    prev = {}
    pq = [(0.0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if u == goal:
            break
        if d > dist.get(u, float("inf")):
            continue
        for v, c in adj[u]:
            nd = d + c
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    path, cur = [goal], goal
    while cur in prev:
        cur = prev[cur]
        path.append(cur)
    return list(reversed(path)), round(dist.get(goal, float("inf")), 3)


p1, c1 = dijkstra(EDGES, "A", "C", as_distance=True)
p2, c2 = dijkstra(EDGES, "A", "C", as_distance=False)
print(f"«거리»로 읽으면: {' → '.join(p1)}  (합 {c1})")
print(f"«강도»로 읽으면: {' → '.join(p2)}  (합 {c2})")
print("정반대 경로:", p1 != p2)
# 출력: «거리»로 읽으면: A → D → C  (합 6.0)
# 출력: «강도»로 읽으면: A → B → C  (합 0.25)
# 출력: 정반대 경로: True

# %% [markdown]
# ## 4단계 — 사고 재현: 친밀도를 그대로 최단경로에 넣으면
#
# 저자가 겪은 사고는 «강도 데이터를 거리라고 믿은» 경우다. 친밀도 8은 «아주 친함»인데
# 알고리즘은 «비용 8, 멀다»로 읽는다. 그래서 **가장 안 친한 경로를 가장 가까운 사이라고 답한다.**

# %%
AFFINITY = {"A-B-C": 16, "A-D-C": 6}  # 값이 클수록 친하다
buggy = min(AFFINITY, key=AFFINITY.get)      # 다익스트라가 고르는 것
correct = max(AFFINITY, key=AFFINITY.get)    # 실제로 원했던 것
print(f"알고리즘의 답(버그): {buggy}  친밀도 {AFFINITY[buggy]}")
print(f"의도했던 답        : {correct}  친밀도 {AFFINITY[correct]}")
# 출력: 알고리즘의 답(버그): A-D-C  친밀도 6
# 출력: 의도했던 답        : A-B-C  친밀도 16

# %% [markdown]
# ## 5단계 — 역수 변환도 «강도 합 최대»와 같은 답은 아니다
#
# 여기서는 두 방식이 같은 A–B–C를 골랐지만, 우연이다. 역수합 최소와 강도합 최대는
# 다른 목적함수다. 값이 갈리는 반례를 만들어 본다.

# %%
COUNTER = [("A", "B", 10), ("B", "C", 10), ("A", "D", 1), ("D", "C", 100)]
W2 = {(a, b): w for a, b, w in COUNTER} | {(b, a): w for a, b, w in COUNTER}
for p in PATHS:
    ws = [W2[(u, v)] for u, v in zip(p, p[1:])]
    print(f"{'-'.join(p)}  강도합 {sum(ws):>3}  역수합 {sum(1/w for w in ws):.3f}")
print("강도합 최대 →", "A-D-C", "/ 역수합 최소 →", "-".join(dijkstra(COUNTER, "A", "C", as_distance=False)[0]))
# 출력: A-B-C  강도합  20  역수합 0.200
# 출력: A-D-C  강도합 101  역수합 1.010
# 출력: 강도합 최대 → A-D-C / 역수합 최소 → A-B-C
#
# 즉 «강도를 거리로 바꾸는 변환»조차 하나가 아니다. 역수($1/w$), 뺄셈($w_{max}-w$),
# 확률의 곱을 합으로 바꾸는 $-\log w$, 최소 엣지를 최대화하는 병목(widest path)이 모두
# 다른 답을 낼 수 있다. 그래서 «무슨 뜻의 숫자인가»를 먼저 못 박아야 한다.

# %% [markdown]
# ## 6단계 — 예방책: 이름에 뜻을 박아 넣기
#
# `weight`라는 이름은 방향(클수록 좋은지 나쁜지)과 단위를 둘 다 숨긴다.
# 이름만 바꿔도 이 사고는 코드 리뷰에서 걸린다.

# %%
NAMING = [
    ("weight", "X", "클수록 좋은지 나쁜지 모른다. 단위도 없다"),
    ("cost_minutes", "O", "거리 해석. 합 최소화. 단위는 분"),
    ("affinity_score", "O", "강도 해석. 최단경로에 그대로 넣으면 안 된다"),
    ("distance_km", "O", "거리 해석. 단위는 km"),
    ("similarity", "O", "강도 해석. 0~1"),
]
for name, ok, why in NAMING:
    print(f"  {ok}  {name:16} {why}")
# 출력:   X  weight           클수록 좋은지 나쁜지 모른다. 단위도 없다
# 출력:   O  cost_minutes     거리 해석. 합 최소화. 단위는 분
# 출력:   O  affinity_score   강도 해석. 최단경로에 그대로 넣으면 안 된다
# 출력:   O  distance_km      거리 해석. 단위는 km
# 출력:   O  similarity       강도 해석. 0~1

# %% [markdown]
# ## 시각화 — 같은 그래프, 다른 정답
#
# 왼쪽은 거리 해석, 오른쪽은 강도 해석. 굵고 진한 선이 각 해석이 고른 경로다.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

POS = {"A": (0.0, 0.0), "B": (1.0, 1.0), "C": (2.0, 0.0), "D": (1.0, -1.0)}
PICKED = {"거리 해석 → A-D-C (합 6)": ["A", "D", "C"], "강도 해석 → A-B-C (8+8)": ["A", "B", "C"]}

fig = make_subplots(rows=1, cols=2, subplot_titles=list(PICKED.keys()))

for col, (title, picked) in enumerate(PICKED.items(), start=1):
    picked_pairs = {frozenset(e) for e in zip(picked, picked[1:])}
    for a, b, w in EDGES:
        on = frozenset((a, b)) in picked_pairs
        x0, y0 = POS[a]
        x1, y1 = POS[b]
        fig.add_trace(
            go.Scatter(
                x=[x0, x1], y=[y0, y1], mode="lines",
                line=dict(width=8 if on else 2, color="#c0392b" if on else "#b0b7bd"),
                hovertext=f"{a}-{b} = {w}", hoverinfo="text", showlegend=False,
            ),
            row=1, col=col,
        )
        # 라벨은 굵은 선에 가리지 않도록 그래프 중심(1, 0)의 반대쪽으로 살짝 밀어 둔다.
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        ox, oy = mx - 1.0, my - 0.0
        norm = (ox**2 + oy**2) ** 0.5 or 1.0
        fig.add_trace(
            go.Scatter(
                x=[mx + 0.22 * ox / norm], y=[my + 0.22 * oy / norm], mode="text",
                text=[str(w)], textfont=dict(size=16, color="#c0392b" if on else "#6b7280"),
                showlegend=False, hoverinfo="skip",
            ),
            row=1, col=col,
        )
    fig.add_trace(
        go.Scatter(
            x=[POS[n][0] for n in POS], y=[POS[n][1] for n in POS],
            mode="markers+text", text=list(POS), textposition="bottom center",
            marker=dict(size=34, color="#2c3e50"), textfont=dict(size=14),
            showlegend=False, hoverinfo="skip",
        ),
        row=1, col=col,
    )

fig.update_xaxes(visible=False, range=[-0.45, 2.45])
fig.update_yaxes(visible=False, range=[-1.55, 1.4])
fig.update_layout(
    title="같은 EDGES, 정반대의 A→C 최적 경로",
    width=960, height=430, plot_bgcolor="white", paper_bgcolor="white",
    margin=dict(l=20, r=20, t=90, b=20),
)
_show(fig)

import pathlib

_out = pathlib.Path(__file__).with_name("expy.png") if "__file__" in dir() else pathlib.Path("expy.png")
fig.write_image(str(_out), scale=2)
print("saved:", _out)
# 출력: saved: .../expy.png

# %% [markdown]
# ## 한 줄 정리
#
# `EDGES`의 숫자 8과 3은 아무 뜻이 없다. 뜻은 **읽는 쪽이 정한다.**
# 거리로 읽으면 합이 작은 **A-D-C(3+3)**, 강도로 읽으면 값이 큰 **A-B-C(8+8)**.
# 같은 데이터에서 정반대 답이 나오고, 그 갈림길은 `weight`라는 이름이 숨긴다.
