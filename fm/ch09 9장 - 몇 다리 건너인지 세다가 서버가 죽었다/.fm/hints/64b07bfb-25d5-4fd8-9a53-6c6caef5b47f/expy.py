# %% [markdown]
# # `count_paths()` — 세는 건 다항, 나열은 지수
#
# 9장 `ex4_path_explosion.py` 의 `count_paths()` 를 뜯어본다.
#
# ```python
# def count_paths(adj, s, t):
#     memo = {}
#     def go(u):
#         if u == t:
#             return 1
#         if u in memo:
#             return memo[u]
#         memo[u] = sum(go(v) for v in adj[u])
#         return memo[u]
#     return go(s)
# ```
#
# 재귀식은 이것 하나다.
#
# $$ P(u) = \begin{cases} 1 & (u = t) \\ \sum_{v \in \text{adj}(u)} P(v) & (u \neq t) \end{cases} $$
#
# 핵심은 `memo` 다. 메모가 있으면 **각 노드의 $P(u)$ 를 딱 한 번만 계산**한다.
# 그래서 세는 비용은 $O(V+E)$ — 다항 시간이다.
# 반면 실제 경로를 **나열**하면 출력 자체가 $\binom{2n-2}{n-1}$ 개라 지수다.
#
# 아래 셀들을 순서대로 실행하며 확인한다.

# %%
import math
import sys
import time
from collections import defaultdict


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


def grid(w, h):
    """오른쪽·위로만 가는 격자 DAG. 순환이 없다는 게 이 장 전체의 전제다."""
    adj = defaultdict(list)
    for x in range(w):
        for y in range(h):
            if x + 1 < w:
                adj[(x, y)].append((x + 1, y))
            if y + 1 < h:
                adj[(x, y)].append((x, y + 1))
    return adj


g = grid(4, 4)
print("노드 수(출발 가능):", len(g))
print("엣지 수:", sum(len(v) for v in g.values()))
print("(0,0) 의 이웃:", g[(0, 0)])
print("(3,2) 의 이웃:", g[(3, 2)])
# 출력:
# 노드 수(출발 가능): 15
# 엣지 수: 24
# (0,0) 의 이웃: [(1, 0), (0, 1)]
# (3,2) 의 이웃: [(3, 3)]

# %% [markdown]
# ## 1. 메모이제이션이 하는 일 — 호출 계측
#
# `go()` 에 카운터를 달아 **진입 횟수**, **캐시 히트**, **실제 계산(미스)** 을 센다.
# 격자 $n \times n$ 의 노드 수는 $n^2$, 엣지 수는 $2n(n-1)$ 이다.
# 계산 횟수가 노드 수를, 총 진입 횟수가 엣지 수+1 을 넘지 않으면 다항 시간이다.

# %%
def count_paths_instrumented(adj, s, t):
    memo = {}
    stat = {"calls": 0, "hits": 0, "computed": 0}

    def go(u):
        stat["calls"] += 1
        if u == t:
            return 1
        if u in memo:
            stat["hits"] += 1
            return memo[u]
        stat["computed"] += 1
        memo[u] = sum(go(v) for v in adj[u])
        return memo[u]

    return go(s), stat


print(f"{'격자':>7} {'노드':>6} {'엣지':>7} {'go 진입':>9} {'계산':>7} {'캐시히트':>9} {'경로 수':>16}")
print("-" * 70)
for n in (3, 5, 8, 11, 15, 20):
    adj = grid(n, n)
    total, st = count_paths_instrumented(adj, (0, 0), (n - 1, n - 1))
    edges = sum(len(v) for v in adj.values())
    print(f"{f'{n}x{n}':>7} {n*n:>6} {edges:>7} {st['calls']:>9} "
          f"{st['computed']:>7} {st['hits']:>9} {total:>16,}")
# 출력:
#      격자     노드      엣지     go 진입      계산      캐시히트             경로 수
# ----------------------------------------------------------------------
#     3x3      9      12        13       8         3                6
#     5x5     25      40        41      24        15               70
#     8x8     64     112       113      63        48            3,432
#   11x11    121     220       221     120        99          184,756
#   15x15    225     420       421     224       195       40,116,600
#   20x20    400     760       761     399       360   35,345,263,800

# %% [markdown]
# 읽는 법:
#
# - **계산 횟수 = 노드 수 − 1** (목표 노드 $t$ 는 `u == t` 로 즉시 반환되어 memo를 안 쓴다)
# - **go 진입 = 엣지 수 + 1** (루트 호출 1회 + 각 엣지를 따라 정확히 1회)
#
# 즉 $O(V+E)$. 경로 수가 350억이 되어도 **작업량은 400노드/760엣지짜리 그대로**다.
# 답이 지수인데 계산은 선형이다 — 이게 「세기는 다항」의 정확한 의미다.

# %% [markdown]
# ## 2. 메모를 빼면 무슨 일이 일어나나
#
# `memo` 한 줄을 지우면 같은 재귀식이 **경로 개수만큼** 호출된다.
# 사실 메모 없는 `go(s)` 의 호출 횟수는 「$s$ 에서 출발하는 모든 부분경로의 수」와 같다.

# %%
def count_paths_naive(adj, s, t):
    stat = {"calls": 0}

    def go(u):
        stat["calls"] += 1
        if u == t:
            return 1
        return sum(go(v) for v in adj[u])

    return go(s), stat["calls"]


print(f"{'격자':>7} {'경로 수':>12} {'memo 호출':>10} {'naive 호출':>12} {'배수':>10}")
print("-" * 56)
for n in (3, 4, 5, 6, 7, 8):
    adj = grid(n, n)
    s, t = (0, 0), (n - 1, n - 1)
    total, st = count_paths_instrumented(adj, s, t)
    _, naive_calls = count_paths_naive(adj, s, t)
    print(f"{f'{n}x{n}':>7} {total:>12,} {st['calls']:>10} {naive_calls:>12,} "
          f"{naive_calls/st['calls']:>9.1f}x")
# 출력:
#      격자         경로 수    memo 호출     naive 호출         배수
# --------------------------------------------------------
#     3x3            6         13           19       1.5x
#     4x4           20         25           69       2.8x
#     5x5           70         41          251       6.1x
#     6x6          252         61          923      15.1x
#     7x7          924         85        3,431      40.4x
#     8x8        3,432        113       12,869     113.9x

# %% [markdown]
# `memo` 호출은 $O(V+E)$ 로 **2차식**처럼 늘고, naive 호출은 **지수**로 는다.
# 한 줄 차이가 복잡도 계급을 바꾼다.

# %% [markdown]
# ## 3. 세기 vs 나열 — 시간 측정
#
# 이제 진짜 비교. 같은 격자에서
#
# - `count_paths` : 경로 **수**만 반환
# - `enumerate_paths` : 경로를 **전부 생성**
#
# 나열은 출력 크기 자체가 $\binom{2n-2}{n-1}$ 이므로, 아무리 잘 짜도
# $\Omega(\text{출력 크기})$ 밑으로 못 내려간다. **알고리즘 문제가 아니라 출력 문제다.**
# 폭발을 막으려고 나열은 $n \le 11$ 로 제한한다.

# %%
def count_paths(adj, s, t):
    memo = {}

    def go(u):
        if u == t:
            return 1
        if u in memo:
            return memo[u]
        memo[u] = sum(go(v) for v in adj[u])
        return memo[u]

    return go(s)


def enumerate_paths(adj, s, t):
    """모든 경로를 실제로 만들어 낸다. DAG라 방문 표시조차 필요 없다."""
    path = [s]

    def go(u):
        if u == t:
            yield tuple(path)
            return
        for v in adj[u]:
            path.append(v)
            yield from go(v)
            path.pop()

    yield from go(s)


ENUM_LIMIT = 11
rows = []
print(f"{'격자':>7} {'최단 길이':>10} {'경로 수':>18} {'세기(ms)':>11} {'나열(ms)':>12}")
print("-" * 64)
for n in (3, 5, 8, 11, 15, 20, 25):
    adj = grid(n, n)
    s, t = (0, 0), (n - 1, n - 1)

    t0 = time.perf_counter()
    total = count_paths(adj, s, t)
    t_count = (time.perf_counter() - t0) * 1000

    if n <= ENUM_LIMIT:
        t0 = time.perf_counter()
        listed = sum(1 for _ in enumerate_paths(adj, s, t))
        t_enum = (time.perf_counter() - t0) * 1000
        assert listed == total, (listed, total)
        enum_txt = f"{t_enum:>12.2f}"
    else:
        t_enum, enum_txt = None, f"{'(생략)':>11}"

    rows.append((n, 2 * (n - 1), total, t_count, t_enum))
    print(f"{f'{n}x{n}':>7} {2*(n-1):>10} {total:>18,} {t_count:>11.2f} {enum_txt}")
# 출력:
#      격자      최단 길이               경로 수      세기(ms)       나열(ms)
# ----------------------------------------------------------------
#     3x3          4                  6        0.01         0.01
#     5x5          8                 70        0.02         0.07
#     8x8         14              3,432        0.04         3.64
#   11x11         20            184,756        0.08       268.25
#   15x15         28         40,116,600        0.14        (생략)
#   20x20         38     35,345,263,800        0.25        (생략)
#   25x25         48 32,247,603,683,100        0.39        (생략)
# (시간 수치는 머신에 따라 다르다. 경향만 보면 된다.)

# %% [markdown]
# 최단 경로 **길이**는 $2(n-1)$ 로 선형, 경로 **수**는 $\binom{2n-2}{n-1}$ 로 지수.
# 세는 시간은 노드 수를 따라 완만히 늘고, 나열 시간은 경로 수를 따라 폭발한다.
#
# 25x25 격자의 경로 수는 32조 개가 넘는데 **세는 데는 1ms 도 안 걸린다.**
# 같은 걸 나열하려 하면 — 한 경로를 1ns 에 뽑아도 9시간 가까이 걸린다.
# 위 측정에서 11x11 나열이 이미 250ms 대인데, 여기서 한 변을 넷만 더 늘리면 손을 뗄 수밖에 없다.

# %%
# 닫힌 꼴 검증: n x n 격자의 코너-투-코너 경로 수 = C(2n-2, n-1)
print(f"{'n':>4} {'count_paths':>22} {'C(2n-2, n-1)':>22} {'일치':>5}")
for n in (3, 5, 8, 11, 15, 20, 30):
    adj = grid(n, n)
    got = count_paths(adj, (0, 0), (n - 1, n - 1))
    want = math.comb(2 * n - 2, n - 1)
    print(f"{n:>4} {got:>22,} {want:>22,} {'예' if got == want else '아니오':>5}")
# 출력:
#    n            count_paths           C(2n-2, n-1)    일치
#    3                      6                      6     예
#    5                     70                     70     예
#    8                  3,432                  3,432     예
#   11                184,756                184,756     예
#   15             40,116,600             40,116,600     예
#   20         35,345,263,800         35,345,263,800     예
#   30 30,067,266,499,541,040 30,067,266,499,541,040     예

# %% [markdown]
# ## 4. 순환이 있으면 왜 안 되나
#
# `count_paths()` 가 성립하는 전제는 **DAG** 다. 엣지 하나만 되돌려도 세 가지가 동시에 깨진다.
#
# 1. **답이 무한하다.** 사이클을 한 바퀴 더 돌면 다른 경로이므로 경로 수가 $\infty$.
# 2. **재귀가 안 끝난다.** `memo[u]` 는 `sum(...)` 이 *끝난 뒤에* 채워지므로,
#    사이클 위에서는 `u` 가 memo에 들어가기 전에 다시 `go(u)` 로 진입한다 → `RecursionError`.
# 3. **「단순 경로」로 바꾸면 다항성이 사라진다.** 방문 집합이 상태에 들어가므로
#    memo 키가 $(u, \text{visited})$ 가 되고 상태 공간이 $O(V \cdot 2^V)$ 로 폭발한다.

# %%
cyc = grid(3, 3)
cyc[(2, 2)] = [(0, 0)]  # 목표 노드에서 출발점으로 되돌아가는 엣지 하나 추가

old = sys.getrecursionlimit()
sys.setrecursionlimit(300)
try:
    print(count_paths(cyc, (0, 0), (1, 1)))  # t 를 (1,1) 로 두면 (2,2)→(0,0) 사이클이 살아 있다
except RecursionError as e:
    print("RecursionError:", e)
finally:
    sys.setrecursionlimit(old)
# 출력:
# RecursionError: maximum recursion depth exceeded in comparison

# %% [markdown]
# 여기서 흔한 오해 하나. 「그럼 방문 중 표시(회색 마킹)를 해서 사이클을 끊으면 되지 않나?」
# 끊으면 크래시는 막지만, 그건 **더 이상 같은 문제가 아니다**.
# 사이클을 끊는 순간 답은 「경로 수」가 아니라 「어떤 임의의 DFS 트리 위의 경로 수」가 된다.
#
# 제대로 하려면 **단순 경로(simple path)** 를 세야 하는데, 이건 일반 그래프에서
# **#P-complete** (Valiant, 1979) — 다항 시간 알고리즘이 알려져 있지 않다.
# 아래는 그 폭발을 눈으로 본다: 양방향 격자에서 코너-투-코너 단순 경로 수.

# %%
def undirected_grid(n):
    adj = defaultdict(list)
    for x in range(n):
        for y in range(n):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = x + dx, y + dy
                if 0 <= a < n and 0 <= b < n:
                    adj[(x, y)].append((a, b))
    return adj


def count_simple_paths(adj, s, t):
    """방문 집합을 들고 다녀야 한다 = memo 를 못 쓴다 = 지수."""
    stat = {"calls": 0}
    visited = {s}

    def go(u):
        stat["calls"] += 1
        if u == t:
            return 1
        total = 0
        for v in adj[u]:
            if v in visited:
                continue
            visited.add(v)
            total += go(v)
            visited.remove(v)
        return total

    return go(s), stat["calls"]


print(f"{'격자':>7} {'DAG 경로(메모)':>16} {'단순 경로(무방향)':>20} {'호출 수':>14}")
print("-" * 62)
for n in (2, 3, 4, 5, 6):
    dag_cnt = count_paths(grid(n, n), (0, 0), (n - 1, n - 1))
    simple_cnt, calls = count_simple_paths(undirected_grid(n), (0, 0), (n - 1, n - 1))
    print(f"{f'{n}x{n}':>7} {dag_cnt:>16,} {simple_cnt:>20,} {calls:>14,}")
# 출력:
#      격자       DAG 경로(메모)           단순 경로(무방향)           호출 수
# --------------------------------------------------------------
#     2x2                2                    2              5
#     3x3                6                   12             51
#     4x4               20                  184          1,271
#     5x5               70                8,512         90,111
#     6x6              252            1,262,816     18,470,411
# (이 셀만 10초 안팎 걸린다. 7x7 은 단순 경로가 5억 7천만 개라 여기서 끊었다.)

# %% [markdown]
# DAG 쪽은 노드 수에 비례한 작업으로 끝나는데, 단순 경로 쪽은
# 호출 수가 답과 같은 속도로 는다. **메모를 못 쓰니까 곧 나열과 같은 비용이 된다.**
#
# ### 정리
#
# | | DAG 위 경로 세기 | DAG 위 경로 나열 | 일반 그래프 단순 경로 세기 |
# |---|---|---|---|
# | 비용 | $O(V+E)$ | $\Omega(\text{경로 수})$ | #P-complete |
# | 왜 | 노드당 1회 계산 | 출력 자체가 지수 | 상태에 방문 집합이 붙음 |
# | 실무 대응 | 그냥 하면 된다 | 상한·조건을 되물어라 | 하지 마라 |

# %% [markdown]
# ## 5. 시각화

# %%
try:
    import plotly.graph_objects as go_plot
    from plotly.subplots import make_subplots

    INK = "#0b0b0b"
    MUTED = "#898781"
    GRID = "#e1e0d9"
    SURFACE = "#fcfcfb"
    C_COUNT = "#2a78d6"   # 세기
    C_ENUM = "#eb6834"    # 나열

    ns = [r[0] for r in rows]
    paths = [r[2] for r in rows]
    t_counts = [r[3] for r in rows]
    enum_ns = [r[0] for r in rows if r[4] is not None]
    enum_ts = [r[4] for r in rows if r[4] is not None]

    fig = make_subplots(
        rows=1, cols=2, horizontal_spacing=0.13,
        subplot_titles=("경로 수는 조합으로 는다", "세는 비용 vs 나열 비용"),
    )

    fig.add_trace(
        go_plot.Scatter(
            x=ns, y=paths, mode="lines+markers+text", name="서로 다른 경로 수",
            line=dict(color=C_COUNT, width=2), marker=dict(size=8, color=C_COUNT),
            text=["", "", "", "", "", "353억", "32조"], textposition="top left",
            textfont=dict(color=MUTED, size=11), showlegend=False,
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go_plot.Scatter(
            x=ns, y=t_counts, mode="lines+markers", name="세기 (메모이제이션)",
            line=dict(color=C_COUNT, width=2), marker=dict(size=8, color=C_COUNT),
        ),
        row=1, col=2,
    )
    fig.add_trace(
        go_plot.Scatter(
            x=enum_ns, y=enum_ts, mode="lines+markers", name="나열 (전부 생성)",
            line=dict(color=C_ENUM, width=2), marker=dict(size=8, color=C_ENUM),
        ),
        row=1, col=2,
    )

    fig.update_xaxes(title_text="격자 한 변 n", gridcolor=GRID, zeroline=False,
                     linecolor="#c3c2b7", tickfont=dict(color=MUTED))
    fig.update_yaxes(type="log", gridcolor=GRID, zeroline=False,
                     linecolor="#c3c2b7", tickfont=dict(color=MUTED))
    fig.update_yaxes(title_text="경로 수 (로그)", row=1, col=1)
    fig.update_yaxes(title_text="소요 시간 ms (로그)", row=1, col=2)
    fig.update_layout(
        title=dict(text="n×n 격자: 세는 건 다항, 나열은 지수",
                   font=dict(color=INK, size=17)),
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        font=dict(color=INK, size=12),
        legend=dict(orientation="h", y=-0.2, x=0.55, font=dict(color=MUTED)),
        width=980, height=440, margin=dict(t=80, b=90, l=70, r=30),
    )

    _show(fig)
    fig.write_image("expy.png", scale=2)
    print("expy.png 저장 완료")
except ImportError as e:
    print("plotly/kaleido 없음, 시각화 생략:", e)
# 출력:
# expy.png 저장 완료
