# %% [markdown]
# # CSR = 오프셋 배열 + 이웃 배열
#
# CSR(압축 희소 행 형식, Compressed Sparse Row)은 **정수 배열 두 개**가 전부다.
#
# - `offset` — 길이 $n+1$. 노드 $u$의 이웃이 `nbr`의 어디서 시작하는지.
# - `nbr` — 길이 $2E$(무향). 모든 이웃을 노드 순서대로 이어 붙인 하나의 연속 배열.
#
# 읽는 규칙은 딱 하나다.
#
# $$\text{neighbors}(u) = \texttt{nbr}[\,\texttt{offset}[u] : \texttt{offset}[u+1]\,]$$
#
# 그래서 차수도 뺄셈 한 번이다.
#
# $$\deg(u) = \texttt{offset}[u+1] - \texttt{offset}[u]$$
#
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용. 없으면 그 셀만 건너뛴다)

# %%
import sys
from array import array
from collections import defaultdict, deque


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# 아주 작은 무향 그래프. 노드 0~4, 노드 4는 일부러 고립시킨다.
N = 5
EDGES = [(0, 1), (0, 2), (1, 3), (2, 3)]
print("노드 수 n =", N)
print("엣지     =", EDGES)
# 출력: 노드 수 n = 5
# 출력: 엣지     = [(0, 1), (0, 2), (1, 3), (2, 3)]

# %% [markdown]
# ## 1단계 — 차수 세기
#
# CSR 만들기는 세 번 훑으면 끝난다: **차수 세기 → 누적합 → 커서로 채우기**. 전체 $O(n + E)$.

# %%
deg = [0] * N
for a, b in EDGES:
    deg[a] += 1
    deg[b] += 1  # 무향이라 양쪽 다 센다

print("deg =", deg)
print("합계 =", sum(deg), "( = 2E =", 2 * len(EDGES), ")")
# 출력: deg = [2, 2, 2, 2, 0]
# 출력: 합계 = 8 ( = 2E = 8 )

# %% [markdown]
# ## 2단계 — 누적합(prefix sum)이 곧 오프셋 배열
#
# 여기서 길이가 왜 $n+1$인지가 드러난다. 칸 $n$개를 나누는 **벽은 $n+1$개**다.
# 마지막 칸 `offset[n]`은 전체 이웃 개수를 담는 보초(sentinel)이고,
# 덕분에 마지막 노드도 `offset[u+1]`로 끝을 읽을 수 있다.

# %%
offset = array("i", [0] * (N + 1))
for i in range(N):
    offset[i + 1] = offset[i] + deg[i]

print("offset      =", list(offset))
print("길이        =", len(offset), "( = n+1 =", N + 1, ")")
print("offset[0]   =", offset[0], "(항상 0)")
print("offset[n]   =", offset[N], "(전체 이웃 개수 = 2E)")
print("단조 증가?  =", all(offset[i] <= offset[i + 1] for i in range(N)))
# 출력: offset      = [0, 2, 4, 6, 8, 8]
# 출력: 길이        = 6 ( = n+1 = 6 )
# 출력: offset[0]   = 0 (항상 0)
# 출력: offset[n]   = 8 (전체 이웃 개수 = 2E)
# 출력: 단조 증가?  = True

# %% [markdown]
# 노드 4는 고립 노드라 `offset[4] == offset[5] == 8`이다.
# **값이 같으면 빈 구간**, 즉 차수 0이라는 뜻이다. 별도 표시가 필요 없다.

# %% [markdown]
# ## 3단계 — 커서를 들고 이웃 배열 채우기
#
# 2단계가 끝나면 각 노드가 쓸 자리가 이미 확정돼 있다. 그래서 배열을 늘리는 일(realloc)이 한 번도 없다.

# %%
cursor = list(offset[:N])  # 각 노드의 다음 쓰기 위치
nbr = array("i", [0] * offset[N])
for a, b in EDGES:
    nbr[cursor[a]] = b
    cursor[a] += 1
    nbr[cursor[b]] = a
    cursor[b] += 1

print("nbr    =", list(nbr))
print("길이   =", len(nbr), "( = 2E )")
print("cursor =", cursor, "(다 채우면 offset[1:]과 같아진다)")
print("검증   =", cursor == list(offset[1:]))
# 출력: nbr    = [1, 2, 0, 3, 0, 3, 1, 2]
# 출력: 길이   = 8 ( = 2E )
# 출력: cursor = [2, 4, 6, 8, 8] (다 채우면 offset[1:]과 같아진다)
# 출력: 검증   = True

# %% [markdown]
# ## 두 배열로 그래프를 읽어 보기
#
# 이웃 조회는 슬라이스 한 번, 차수는 뺄셈 한 번.

# %%
for u in range(N):
    lo, hi = offset[u], offset[u + 1]
    print(f"노드 {u}: nbr[{lo}:{hi}] = {str(list(nbr[lo:hi])):<10} deg = {hi - lo}")
# 출력: 노드 0: nbr[0:2] = [1, 2]     deg = 2
# 출력: 노드 1: nbr[2:4] = [0, 3]     deg = 2
# 출력: 노드 2: nbr[4:6] = [0, 3]     deg = 2
# 출력: 노드 3: nbr[6:8] = [1, 2]     deg = 2
# 출력: 노드 4: nbr[8:8] = []         deg = 0

# %% [markdown]
# ## 왜 n+1인가 — 없으면 어떻게 되는지 직접 확인
#
# 길이 $n$짜리 「시작 배열」만 있으면 마지막 노드의 끝을 모른다.
# 조건 분기를 넣어 특수 처리하거나, 끝 배열을 하나 더 들고 다녀야 한다.

# %%
start_only = list(offset[:N])  # 길이 n 짜리 시작 배열만 가진 척
print("start_only =", start_only)

try:
    u = N - 1  # 마지막 노드
    print(list(nbr[start_only[u] : start_only[u + 1]]))
except IndexError as e:
    print(f"마지막 노드({N - 1})의 끝을 읽으려다 실패: IndexError: {e}")
print("→ 보초 칸 offset[n]이 있으면 분기 없이 모든 노드를 같은 코드로 읽는다.")
# 출력: start_only = [0, 2, 4, 6, 8]
# 출력: 마지막 노드(4)의 끝을 읽으려다 실패: IndexError: list index out of range
# 출력: → 보초 칸 offset[n]이 있으면 분기 없이 모든 노드를 같은 코드로 읽는다.

# %% [markdown]
# ## 순회 — 연속 구간을 그대로 읽는다
#
# BFS 안쪽 루프가 `range(offset[u], offset[u+1])`이다.
# 포인터를 따라 점프하는 대신 **한 방향으로 쭉** 읽는다. 이게 8.2절의 「왜 연속이면 빠른가」다.

# %%
def bfs_csr(offset, nbr, start, n):
    seen = bytearray(n)
    seen[start] = 1
    q = deque([start])
    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for i in range(offset[u], offset[u + 1]):  # 연속 구간
            v = nbr[i]
            if not seen[v]:
                seen[v] = 1
                q.append(v)
    return order


print("BFS(0) 방문 순서 =", bfs_csr(offset, nbr, 0, N))
print("노드 4는 고립이라 안 나온다.")
# 출력: BFS(0) 방문 순서 = [0, 1, 2, 3]
# 출력: 노드 4는 고립이라 안 나온다.

# %% [markdown]
# ## 인접 리스트와 같은 정보, 다른 그릇
#
# CSR과 인접 리스트는 **논리적으로 동일**하다. $O(n+E)$에 상호 변환된다.

# %%
adj = defaultdict(list)
for a, b in EDGES:
    adj[a].append(b)
    adj[b].append(a)

same = all(sorted(adj[u]) == sorted(nbr[offset[u] : offset[u + 1]]) for u in range(N))
print("adj  =", {u: adj[u] for u in range(N)})
print("두 표현이 같은 그래프인가?", same)
# 출력: adj  = {0: [1, 2], 1: [0, 3], 2: [0, 3], 3: [1, 2], 4: []}
# 출력: 두 표현이 같은 그래프인가? True

# %% [markdown]
# ## 규모를 키우면 — 메모리 차이
#
# CSR의 크기는 정확히 계산된다(32비트 정수 기준).
#
# $$\text{bytes} = 4(n+1) + 4 \cdot 2E$$
#
# 반면 dict of list는 원소마다 파이썬 객체 헤더가 붙는다.

# %%
import random


def make(n, avg_deg=12, seed=20260801):
    rnd = random.Random(seed)
    edges = set()
    for a in range(n):
        for _ in range(avg_deg // 2):
            b = rnd.randrange(n)
            if a != b:
                edges.add((min(a, b), max(a, b)))
    return sorted(edges)


def build_csr(edges, n):
    d = [0] * n
    for a, b in edges:
        d[a] += 1
        d[b] += 1
    off = array("i", [0] * (n + 1))
    for i in range(n):
        off[i + 1] = off[i] + d[i]
    cur = list(off[:n])
    nb = array("i", [0] * off[n])
    for a, b in edges:
        nb[cur[a]] = b
        cur[a] += 1
        nb[cur[b]] = a
        cur[b] += 1
    return off, nb


def deep_size(obj, seen=None):
    seen = seen if seen is not None else set()
    if id(obj) in seen:
        return 0
    seen.add(id(obj))
    size = sys.getsizeof(obj)
    if isinstance(obj, dict):
        size += sum(deep_size(k, seen) + deep_size(v, seen) for k, v in obj.items())
    elif isinstance(obj, (list, tuple, set)):
        size += sum(deep_size(x, seen) for x in obj)
    return size


sizes = []
print(f"{'노드':>8} {'엣지':>9} {'CSR(B)':>12} {'dict of list(B)':>16} {'배수':>7}")
for n in (2_000, 10_000, 50_000):
    e = make(n)
    off, nb = build_csr(e, n)
    csr_bytes = sys.getsizeof(off) + sys.getsizeof(nb)
    a = defaultdict(list)
    for x, y in e:
        a[x].append(y)
        a[y].append(x)
    adj_bytes = deep_size(dict(a))
    sizes.append((n, len(e), csr_bytes, adj_bytes))
    print(f"{n:>8,} {len(e):>9,} {csr_bytes:>12,} {adj_bytes:>16,} {adj_bytes / csr_bytes:>6.1f}x")

n_, e_, c_, _ = sizes[-1]
print(f"\n공식 검증: 4*(n+1) + 4*2E = {4 * (n_ + 1) + 4 * 2 * e_:,} B  (실측 {c_:,} B, array 헤더 포함)")
# 출력:       노드        엣지       CSR(B)  dict of list(B)      배수
# 출력:    2,000    11,956      103,780          786,592    7.6x
# 출력:   10,000    59,962      519,828        4,038,736    7.8x
# 출력:   50,000   299,958    2,599,796       21,508,836    8.3x
# 출력:
# 출력: 공식 검증: 4*(n+1) + 4*2E = 2,599,668 B  (실측 2,599,796 B, array 헤더 포함)

# %% [markdown]
# 두 배열이라서 **객체 헤더가 0**이다. 7~8배 차이가 전부 그 오버헤드다.
# 그리고 노드를 100만으로 키우면 이 배수가 곧 「4.1GB vs 380MB」가 된다.
#
# ## 시각화 — 오프셋 배열이 이웃 배열을 어떻게 자르는가

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    PALETTE = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#B279A2"]

    fig = make_subplots(
        rows=2,
        cols=1,
        row_heights=[0.62, 0.38],
        vertical_spacing=0.16,
        subplot_titles=(
            "offset(길이 n+1)이 nbr(길이 2E)을 노드별 구간으로 자른다",
            "같은 그래프, 그릇만 다름 — 메모리(바이트, 로그 스케일)",
        ),
    )

    # --- 위: CSR 레이아웃 다이어그램 ---
    # nbr 배열 셀 (소유 노드 색으로)
    owner = []
    for u in range(N):
        owner += [u] * (offset[u + 1] - offset[u])

    for i, v in enumerate(nbr):
        fig.add_shape(
            type="rect",
            x0=i,
            x1=i + 1,
            y0=0,
            y1=1,
            line=dict(color="white", width=2),
            fillcolor=PALETTE[owner[i] % len(PALETTE)],
            row=1,
            col=1,
        )
        fig.add_annotation(
            x=i + 0.5, y=0.5, text=f"<b>{v}</b>", showarrow=False,
            font=dict(color="white", size=15), row=1, col=1,
        )
        fig.add_annotation(
            x=i + 0.5, y=-0.16, text=str(i), showarrow=False,
            font=dict(color="#888", size=10), row=1, col=1,
        )

    # offset 값과 경계선
    for u, o in enumerate(offset):
        fig.add_shape(
            type="line", x0=o, x1=o, y0=-0.05, y1=2.25,
            line=dict(color="#333", width=1.5, dash="dot"), row=1, col=1,
        )

        if u < N:
            fig.add_annotation(
                x=o, y=2.35, text=f"offset[{u}]={o}", showarrow=False, xanchor="left",
                font=dict(color="#333", size=10), row=1, col=1,
            )
        else:  # 보초 칸은 위쪽에 따로 (offset[n-1]과 같은 x 에 올 수 있다)
            fig.add_annotation(
                x=o, y=2.8, text=f"<b>offset[n]={o}</b> ← 보초(sentinel), 전체 길이 2E",
                showarrow=False, xanchor="right",
                font=dict(color="#B279A2", size=11), row=1, col=1,
            )

    # 노드별 구간 브래킷
    for u in range(N):
        lo, hi = offset[u], offset[u + 1]
        if hi == lo:
            fig.add_annotation(
                x=lo, y=1.85, text=f"노드 {u}: offset[{u}]==offset[{u + 1}] → 빈 구간(deg=0)",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.2,
                arrowcolor=PALETTE[u % len(PALETTE)], ax=-30, ay=-22,
                xanchor="right", font=dict(color=PALETTE[u % len(PALETTE)], size=11),
                row=1, col=1,
            )
            continue
        fig.add_shape(
            type="rect", x0=lo + 0.04, x1=hi - 0.04, y0=1.2, y1=1.5,
            line=dict(color=PALETTE[u % len(PALETTE)], width=2),
            fillcolor=PALETTE[u % len(PALETTE)], opacity=0.18, row=1, col=1,
        )
        fig.add_annotation(
            x=(lo + hi) / 2, y=1.35, text=f"노드 {u} · deg={hi - lo}", showarrow=False,
            font=dict(color=PALETTE[u % len(PALETTE)], size=11), row=1, col=1,
        )

    fig.add_annotation(
        x=0, y=1.0, text="nbr →", showarrow=False, xanchor="right",
        font=dict(color="#333", size=12), row=1, col=1,
    )

    # --- 아래: 메모리 비교 ---
    labels = [f"{n:,}노드" for n, _, _, _ in sizes]
    fig.add_trace(
        go.Bar(
            x=labels, y=[c for _, _, c, _ in sizes], name="CSR (배열 2개)",
            marker_color=PALETTE[0],
            text=[f"{c / 1e6:.2f} MB" for _, _, c, _ in sizes], textposition="outside",
        ),
        row=2, col=1,
    )
    fig.add_trace(
        go.Bar(
            x=labels, y=[a for _, _, _, a in sizes], name="dict of list",
            marker_color=PALETTE[1],
            text=[f"{a / 1e6:.2f} MB ({a / c:.1f}x)" for _, _, c, a in sizes],
            textposition="outside",
        ),
        row=2, col=1,
    )

    fig.update_xaxes(visible=False, range=[-2.2, len(nbr) + 0.6], row=1, col=1)
    fig.update_yaxes(visible=False, range=[-0.45, 3.1], row=1, col=1)
    fig.update_yaxes(type="log", title_text="bytes", row=2, col=1)
    fig.update_layout(
        title="CSR = offset(어디서부터) + nbr(무엇이)",
        template="plotly_white",
        width=1000,
        height=760,
        showlegend=True,
        legend=dict(orientation="h", y=-0.06, x=0.5, xanchor="center"),
        margin=dict(l=70, r=40, t=90, b=90),
    )

    _show(fig)
    fig.write_image("expy.png", scale=2)
    print("expy.png 저장 완료")
except ImportError as exc:
    print("plotly/kaleido 없음 — 시각화 셀 건너뜀:", exc)
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# | 배열 | 길이 | 담는 것 | SciPy 이름 |
# |---|---|---|---|
# | 오프셋 배열 `offset` | $n+1$ | 노드별 이웃 **시작 위치** (+ 보초 하나) | `indptr` |
# | 이웃 배열 `nbr` | $2E$ (무향) | 모든 이웃을 **연속으로** 나열 | `indices` |
#
# - `offset[u+1] - offset[u]` = 차수. `offset[n]` = 전체 이웃 수.
# - 길이가 $n+1$인 이유: **한 노드의 끝은 다음 노드의 시작**이고, 마지막 노드에는 다음이 없으니 보초가 필요하다.
# - 가중치·속성은 `nbr`과 같은 길이의 **병렬 배열**로 붙는다(SciPy의 `data`). 위치 정보는 여전히 두 개.
# - 대가는 불변성이다. 엣지를 끼우려면 뒤를 다 밀어야 한다 → 「인접 리스트로 쌓고 CSR로 굽는다」.
