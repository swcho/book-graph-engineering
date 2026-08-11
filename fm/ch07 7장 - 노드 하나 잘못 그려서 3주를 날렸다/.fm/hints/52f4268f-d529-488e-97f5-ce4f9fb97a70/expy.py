# 필요 패키지: plotly, kaleido  (표준 라이브러리: heapq, math, collections, itertools)
#   pip install plotly kaleido
# %% [markdown]
# # 가중치가 «거리»인가 «강도»인가 — `1.0 / w` 한 줄의 정체
#
# `ex3_weights.py`의 `dijkstra()`는 `as_distance=False`일 때 가중치를 `1.0 / w`로
# 역수 변환해 **거리로 번역**한다. 최단 경로 알고리즘은 예외 없이
# 「작을수록 가깝다」로 읽기 때문이다.
#
# 이 노트북에서 단계적으로 확인할 것:
#
# 1. 최단 경로 알고리즘이 실제로 «작은 값»만 좋아한다는 것
# 2. 같은 데이터가 해석에 따라 정반대 답을 낸다는 것
# 3. 역수 변환이 왜 통하는가 — 단조 감소 $f(w)=1/w$, $f'(w)=-1/w^2 < 0$
# 4. 역수 변환의 한계: $w=0$, 「강도 합 최대화」와 불일치, 확률이면 $-\log p$
# 5. $w_{\max}-w$ 방식이 홉 수에 편향되는 것

# %%
import heapq
import math
from collections import defaultdict


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


print("준비 완료")
# 출력: 준비 완료

# %% [markdown]
# ## 1. 책의 `dijkstra()`를 그대로 옮긴다
#
# 변환은 **그래프를 만드는 시점에 딱 한 줄**이다.
#
# ```python
# cost = w if as_distance else 1.0 / w
# ```
#
# 탐색 루프는 손대지 않는다. `heappop`은 언제나 누적값이 가장 작은 정점을 뽑고,
# `if nd < dist[v]`는 「더 작으면 갱신」이다. 즉 알고리즘의 세계관은 고정이다.

# %%
EDGES = [("A", "B", 8), ("B", "C", 8), ("A", "D", 3), ("D", "C", 3)]


def dijkstra(edges, start, goal, as_distance=True):
    adj = defaultdict(list)
    for a, b, w in edges:
        cost = w if as_distance else 1.0 / w  # ← 강도 해석은 여기서 거리로 번역된다
        adj[a].append((b, cost))
        adj[b].append((a, cost))
    dist = {start: 0.0}
    prev = {}
    pq = [(0.0, start)]
    while pq:
        d, u = heapq.heappop(pq)  # 누적값이 «가장 작은» 정점
        if u == goal:
            break
        if d > dist.get(u, float("inf")):
            continue
        for v, c in adj[u]:
            nd = d + c
            if nd < dist.get(v, float("inf")):  # 「더 작으면 좋다」
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    path, cur = [goal], goal
    while cur in prev:
        cur = prev[cur]
        path.append(cur)
    return list(reversed(path)), round(dist.get(goal, float("inf")), 3)


print("엣지:", EDGES)
# 출력: 엣지: [('A', 'B', 8), ('B', 'C', 8), ('A', 'D', 3), ('D', 'C', 3)]

# %% [markdown]
# ## 2. 같은 데이터, 정반대 답
#
# A에서 C로 가는 경로는 두 개뿐이다.
#
# $$C(A\to B\to C) = 8+8 = 16,\qquad C(A\to D\to C) = 3+3 = 6$$
#
# $$C_{1/w}(A\to B\to C) = \tfrac18+\tfrac18 = 0.25,\qquad
#   C_{1/w}(A\to D\to C) = \tfrac13+\tfrac13 \approx 0.667$$

# %%
p1, c1 = dijkstra(EDGES, "A", "C", as_distance=True)
p2, c2 = dijkstra(EDGES, "A", "C", as_distance=False)
print(f"숫자를 «거리»로 읽으면: {' → '.join(p1)}  (합 {c1})")
print(f"숫자를 «강도»로 읽으면: {' → '.join(p2)}  (합 {c2})")
print("\n같은 데이터인데 답이 반대다. 숫자에는 단위가 없다.")
# 출력: 숫자를 «거리»로 읽으면: A → D → C  (합 6.0)
# 출력: 숫자를 «강도»로 읽으면: A → B → C  (합 0.25)
# 출력:
# 출력: 같은 데이터인데 답이 반대다. 숫자에는 단위가 없다.

# %% [markdown]
# ## 3. 경로별 비용을 표로 펼쳐 본다
#
# 어떤 순서로 뒤집혔는지 눈으로 확인한다.

# %%
PATHS = [["A", "B", "C"], ["A", "D", "C"]]
W = {frozenset((a, b)): w for a, b, w in EDGES}


def path_edges(path):
    return [frozenset((path[i], path[i + 1])) for i in range(len(path) - 1)]


print(f"{'경로':<12} {'원래 w':<10} {'거리 합':>8} {'역수 합':>10}")
for p in PATHS:
    ws = [W[e] for e in path_edges(p)]
    d_sum = sum(ws)
    r_sum = sum(1.0 / w for w in ws)
    print(f"{'→'.join(p):<12} {str(ws):<10} {d_sum:>8} {r_sum:>10.3f}")
print("\n거리 합의 최솟값과 역수 합의 최솟값이 서로 다른 경로를 가리킨다.")
# 출력: 경로           원래 w         거리 합      역수 합
# 출력: A→B→C        [8, 8]           16      0.250
# 출력: A→D→C        [3, 3]            6      0.667
# 출력:
# 출력: 거리 합의 최솟값과 역수 합의 최솟값이 서로 다른 경로를 가리킨다.

# %% [markdown]
# ## 4. 역수 변환이 통하는 근거는 «단조 감소» 하나뿐
#
# $$f(w) = \frac{1}{w},\qquad f'(w) = -\frac{1}{w^{2}} < 0 \quad (w \ne 0)$$
#
# 따라서 $w>0$ 구간에서
#
# $$w_1 > w_2 \iff f(w_1) < f(w_2)$$
#
# 크기 순서가 정확히 뒤집힌다. 「강한 간선」이 「짧은 간선」이 된다.

# %%
for w1, w2 in [(8, 3), (3, 8), (10, 10), (1, 100)]:
    lhs = w1 > w2
    rhs = (1.0 / w1) < (1.0 / w2)
    print(f"w1={w1:>3}, w2={w2:>3} | (w1>w2)={lhs!s:<5} ((1/w1)<(1/w2))={rhs!s:<5} 일치={lhs == rhs}")
# 출력: w1=  8, w2=  3 | (w1>w2)=True  ((1/w1)<(1/w2))=True  일치=True
# 출력: w1=  3, w2=  8 | (w1>w2)=False ((1/w1)<(1/w2))=False 일치=True
# 출력: w1= 10, w2= 10 | (w1>w2)=False ((1/w1)<(1/w2))=False 일치=True
# 출력: w1=  1, w2=100 | (w1>w2)=False ((1/w1)<(1/w2))=False 일치=True

# %% [markdown]
# ## 5. 함정 1 — `w = 0`이면 터진다
#
# 강도 0(전혀 안 친함, 유사도 0)은 실무 데이터에 흔하다.

# %%
try:
    bad = [("A", "B", 0), ("B", "C", 5)]
    dijkstra(bad, "A", "C", as_distance=False)
except ZeroDivisionError as e:
    print("ZeroDivisionError:", e)

EPS = 1e-9
print(f"완화책: 1/(0 + eps) = {1.0 / (0 + EPS):.3e}  → 사실상 «무한히 먼» 간선으로 취급된다")
# 출력: ZeroDivisionError: float division by zero
# 출력: 완화책: 1/(0 + eps) = 1.000e+09  → 사실상 «무한히 먼» 간선으로 취급된다

# %% [markdown]
# ## 6. 함정 2 — 역수 합은 「강도 합 최대화」가 아니다
#
# 역수 합 $\sum 1/w_e$ 는 조화평균의 분모다. 조화평균은 **작은 값 하나가 전체를 끌어내린다**.
#
# $$\text{조화평균} \le \text{기하평균} \le \text{산술평균}$$
#
# 그래서 역수 합 최소화는 「약한 고리가 없는 경로」를 선호하고,
# 「강도 총합이 큰 경로」와는 다른 답을 낸다.

# %%
# X → Y 로 가는 두 경로: 직행(강도 9) vs 경유(강도 10, 10)
CAND = {
    "직행 X-Y (w=9)": [9],
    "경유 X-M-Y (w=10,10)": [10, 10],
}
print(f"{'경로':<24} {'강도 합':>8} {'역수 합':>10} {'강도 곱':>10}")
for name, ws in CAND.items():
    print(f"{name:<24} {sum(ws):>8} {sum(1.0 / w for w in ws):>10.4f} {math.prod(ws):>10}")

best_sum = max(CAND, key=lambda k: sum(CAND[k]))
best_rec = min(CAND, key=lambda k: sum(1.0 / w for w in CAND[k]))
print(f"\n강도 합 최대: {best_sum}")
print(f"역수 합 최소: {best_rec}")
print("→ 서로 다른 답. 역수 변환은 «간선 하나하나의 순서»만 보장한다." if best_sum != best_rec else "→ 같은 답")
# 출력: 경로                        강도 합      역수 합       강도 곱
# 출력: 직행 X-Y (w=9)                   9     0.1111          9
# 출력: 경유 X-M-Y (w=10,10)            20     0.2000        100
# 출력:
# 출력: 강도 합 최대: 경유 X-M-Y (w=10,10)
# 출력: 역수 합 최소: 직행 X-Y (w=9)
# 출력: → 서로 다른 답. 역수 변환은 «간선 하나하나의 순서»만 보장한다.

# %% [markdown]
# ## 7. 확률·유사도라면 `-log p`가 정석
#
# 경로의 강도를 **곱**으로 정의하고 싶다면(예: 각 링크가 통할 확률):
#
# $$\max_P \prod_{e\in P} p_e
#  = \max_P \sum_{e\in P} \log p_e
#  = \min_P \sum_{e\in P} \bigl(-\log p_e\bigr)$$
#
# 로그가 곱을 합으로 바꿔 주고, $0<p\le 1$ 이면 $-\log p \ge 0$ 이라
# 다익스트라의 «음수 간선 금지» 조건도 만족한다. `1/w`가 편법이라면
# 이건 **원래 문제와 수학적으로 동일한 변환**이다.

# %%
PROB_EDGES = [("A", "B", 0.9), ("B", "C", 0.9), ("A", "D", 0.5), ("D", "C", 0.99)]

# (1) 완전 탐색으로 «곱이 최대인 경로»를 구한다
PROB_PATHS = [["A", "B", "C"], ["A", "D", "C"]]
PW = {frozenset((a, b)): p for a, b, p in PROB_EDGES}
for p in PROB_PATHS:
    ps = [PW[e] for e in path_edges(p)]
    print(f"{'→'.join(p)}: 곱={math.prod(ps):.4f}  -log 합={sum(-math.log(x) for x in ps):.4f}")

# (2) 다익스트라에 -log 변환을 먹인다
NEGLOG = [(a, b, -math.log(p)) for a, b, p in PROB_EDGES]
p3, c3 = dijkstra(NEGLOG, "A", "C", as_distance=True)
print(f"\n-log 변환 + 최단경로: {' → '.join(p3)}  (비용 {c3}, 확률 {math.exp(-c3):.4f})")

# (3) 같은 데이터에 1/w 를 쓰면?
p4, c4 = dijkstra(PROB_EDGES, "A", "C", as_distance=False)
print(f"1/w 변환 + 최단경로 : {' → '.join(p4)}  (비용 {c4})")
print("\n여기서는 우연히 같은 답이지만, 근거가 다르다. -log 만이 곱 최대화와 등가다.")
# 출력: A→B→C: 곱=0.8100  -log 합=0.2107
# 출력: A→D→C: 곱=0.4950  -log 합=0.7032
# 출력:
# 출력: -log 변환 + 최단경로: A → B → C  (비용 0.211, 확률 0.8098)
# 출력:   (확률이 0.8100 이 아니라 0.8098 인 것은 비용을 소수 3자리로 round 했기 때문)
# 출력: 1/w 변환 + 최단경로 : A → B → C  (비용 2.222)
# 출력:
# 출력: 여기서는 우연히 같은 답이지만, 근거가 다르다. -log 만이 곱 최대화와 등가다.

# %% [markdown]
# ## 8. 함정 3 — `w_max - w` 는 «전역 최댓값»에 답이 매달린다
#
# 순서는 뒤집히지만 두 가지가 망가진다.
#
# 1. 모든 간선에 상수 $w_{\max}$ 를 더하는 셈이라 **간선이 적은 경로가 부당하게 유리**해진다.
# 2. 경로와 아무 상관없는 간선 하나가 들어와 $w_{\max}$ 를 올리면 **답이 바뀐다**.
#
# 아래에서는 목적지와 무관한 간선 `S-Z (w=1000)` 을 추가하기만 하는데 답이 뒤집힌다.
# $1/w$ 는 간선별 지역 변환이라 흔들리지 않는다.

# %%
# 강도: 짧고 약한 직행(S-T, 5) vs 길지만 아주 강한 경유(S-M-T, 100/100)
STR_EDGES = [("S", "T", 5), ("S", "M", 100), ("M", "T", 100)]


def solve_both(edges, tag):
    wm = max(w for *_, w in edges)
    sub = [(a, b, wm - w) for a, b, w in edges]
    ps, cs = dijkstra(sub, "S", "T", as_distance=True)
    pr, cr = dijkstra(edges, "S", "T", as_distance=False)
    print(f"[{tag}] w_max = {wm}")
    print(f"   (w_max - w) → {' → '.join(ps):<12} 비용 {cs}")
    print(f"   (1/w)       → {' → '.join(pr):<12} 비용 {cr}")
    return ps, pr


a_sub, a_rec = solve_both(STR_EDGES, "원본")
b_sub, b_rec = solve_both(STR_EDGES + [("S", "Z", 1000)], "무관한 S-Z(w=1000) 추가")
print(f"\nw_max-w 방식의 답: {'→'.join(a_sub)}  ⇒  {'→'.join(b_sub)}   변했나? {a_sub != b_sub}")
print(f"1/w      방식의 답: {'→'.join(a_rec)}  ⇒  {'→'.join(b_rec)}   변했나? {a_rec != b_rec}")
# 출력: [원본] w_max = 100
# 출력:    (w_max - w) → S → M → T    비용 0.0
# 출력:    (1/w)       → S → M → T    비용 0.02
# 출력: [무관한 S-Z(w=1000) 추가] w_max = 1000
# 출력:    (w_max - w) → S → T        비용 995.0
# 출력:    (1/w)       → S → M → T    비용 0.02
# 출력:
# 출력: w_max-w 방식의 답: S→M→T  ⇒  S→T   변했나? True
# 출력: 1/w      방식의 답: S→M→T  ⇒  S→M→T   변했나? False

# %% [markdown]
# ## 9. 예방법 — 이름에 뜻을 박아 넣는다
#
# ```
# weight (X)  →  cost_minutes, affinity_score (O)
# ```
#
# `weight`는 아무 뜻도 없다. `cost_minutes`는 「작을수록 좋다」가, `affinity_score`는
# 「클수록 좋다」가 이름에 들어 있다. 이름 하나로 막을 수 있는 사고다.

# %%
SCHEMA_CHECK = [
    ("weight", None),
    ("cost_minutes", "distance"),
    ("affinity_score", "strength"),
    ("similarity", "strength"),
    ("travel_time_sec", "distance"),
    ("fee_krw", "distance"),
]
DIST_HINTS = ("cost", "time", "minute", "sec", "fee", "price", "distance", "hop", "latency")
STR_HINTS = ("affinity", "score", "similarity", "sim", "trust", "amount", "strength", "weightsum")

for name, truth in SCHEMA_CHECK:
    low = name.lower()
    guess = "distance" if any(h in low for h in DIST_HINTS) else ("strength" if any(h in low for h in STR_HINTS) else None)
    mark = "OK " if guess == truth else "?? "
    print(f"{mark}{name:<18} 이름만으로 추론 → {guess}")
# 출력: OK weight             이름만으로 추론 → None
# 출력: OK cost_minutes       이름만으로 추론 → distance
# 출력: OK affinity_score     이름만으로 추론 → strength
# 출력: OK similarity         이름만으로 추론 → strength
# 출력: OK travel_time_sec    이름만으로 추론 → distance
# 출력: OK fee_krw            이름만으로 추론 → distance

# %% [markdown]
# ## 10. 시각화
#
# - 왼쪽/가운데: 같은 그래프를 두 해석으로 풀었을 때 선택되는 경로 (굵은 선)
# - 오른쪽: 변환 함수 $1/w$ 와 $-\log w$ 가 모두 단조 감소임을 확인

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

POS = {"A": (0.0, 0.0), "B": (1.0, 1.0), "C": (2.0, 0.0), "D": (1.0, -1.0)}


def add_graph(fig, col, chosen, title_cost_fn):
    chosen_e = set(path_edges(chosen))
    for a, b, w in EDGES:
        key = frozenset((a, b))
        picked = key in chosen_e
        x0, y0 = POS[a]
        x1, y1 = POS[b]
        fig.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line=dict(width=8 if picked else 2, color="#d1495b" if picked else "#b0b7c3"),
                hoverinfo="text",
                text=f"{a}-{b}: w={w}, cost={title_cost_fn(w):.3f}",
                showlegend=False,
            ),
            row=1,
            col=col,
        )
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        fig.add_annotation(
            x=mx, y=my, text=f"w={w}<br>c={title_cost_fn(w):.3f}",
            showarrow=False, font=dict(size=10, color="#333"),
            bgcolor="rgba(255,255,255,0.75)", row=1, col=col,
        )
    fig.add_trace(
        go.Scatter(
            x=[POS[n][0] for n in POS],
            y=[POS[n][1] for n in POS],
            mode="markers+text",
            text=list(POS),
            textposition="middle center",
            textfont=dict(size=13, color="white"),
            marker=dict(size=34, color="#30475e"),
            showlegend=False,
            hoverinfo="text",
        ),
        row=1,
        col=col,
    )


fig = make_subplots(
    rows=1,
    cols=3,
    subplot_titles=(
        f"거리 해석 (cost=w)<br>선택: {'→'.join(p1)} (합 {c1})",
        f"강도 해석 (cost=1/w)<br>선택: {'→'.join(p2)} (합 {c2})",
        "변환 함수는 모두 단조 감소",
    ),
    column_widths=[0.31, 0.31, 0.38],
)

add_graph(fig, 1, p1, lambda w: float(w))
add_graph(fig, 2, p2, lambda w: 1.0 / w)

ws = [0.2 + 0.05 * i for i in range(200)]  # 0.2 .. 10.15
fig.add_trace(
    go.Scatter(x=ws, y=[1.0 / w for w in ws], mode="lines", name="1/w", line=dict(width=3, color="#d1495b")),
    row=1,
    col=3,
)
fig.add_trace(
    go.Scatter(
        x=ws,
        y=[-math.log(w) for w in ws],
        mode="lines",
        name="-log w",
        line=dict(width=3, color="#2a9d8f", dash="dash"),
    ),
    row=1,
    col=3,
)
fig.add_trace(
    go.Scatter(
        x=[3, 8],
        y=[1 / 3, 1 / 8],
        mode="markers+text",
        text=["w=3 → 0.333", "w=8 → 0.125"],
        textposition="top right",
        marker=dict(size=11, color="#d1495b", symbol="diamond"),
        showlegend=False,
    ),
    row=1,
    col=3,
)

for c in (1, 2):
    fig.update_xaxes(visible=False, row=1, col=c)
    fig.update_yaxes(visible=False, row=1, col=c, scaleanchor=f"x{c}" if c > 1 else "x")
fig.update_xaxes(title_text="가중치 w (강도)", row=1, col=3)
fig.update_yaxes(title_text="변환된 비용", range=[-3, 5.5], row=1, col=3)

fig.update_layout(
    title_text="같은 숫자, 반대 답 — 강도는 반드시 거리로 번역해서 넣는다",
    height=480,
    width=1180,
    plot_bgcolor="white",
    legend=dict(orientation="h", y=-0.12, x=0.72),
)

_show(fig)

import os

_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_out, scale=2)
print("saved:", _out)
# 출력: saved: .../52f4268f-d529-488e-97f5-ce4f9fb97a70/expy.png

# %% [markdown]
# ## 정리
#
# | 상황 | 변환 | 비고 |
# |---|---|---|
# | 숫자가 이미 거리/비용 | 없음 | `as_distance=True` |
# | 강도, 순서만 뒤집으면 됨 | $1/w$ | $w=0$ 주의, 조화평균 성질 |
# | 확률·유사도, 경로 강도 = 곱 | $-\log w$ | 곱 최대화와 정확히 등가 |
# | 「가장 약한 고리」가 기준 | 최대용량(bottleneck) 경로 | 합이 아니라 min-max |
#
# 기억할 한 줄: **최단 경로 알고리즘은 항상 «작을수록 가깝다»로 읽는다.**
# 그리고 애초에 사고를 막는 가장 싼 방법은 이름이다 — `weight` 대신 `cost_minutes`, `affinity_score`.
