# %% [markdown]
# # 벨만-포드는 음수 사이클을 어떻게 검사하는가
#
# **질문**: 벨만-포드는 음수 사이클을 어떻게 검사하는가?
#
# **답**: 노드 수 $-1$회 완화를 마친 뒤 **한 바퀴 더** 돌려, 여전히 거리가 줄어드는
# 엣지가 있으면 음수 사이클이 있다고 판정한다.
#
# 이 노트북은 세 가지를 눈으로 확인한다.
#
# 1. 라운드 $k$가 끝나면 「엣지 $k$개 이하로 가는 최단 거리」가 확정된다 → 그래서 $|V|-1$회면 충분하다
# 2. 음수 사이클이 **없으면** $|V|$번째 라운드에서 아무 것도 안 줄어든다
# 3. 음수 사이클이 **있으면** $|V|$번째 라운드에서 반드시 뭔가 줄어든다 (그리고 계속 줄어든다)
#
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용). 나머지 셀은 표준 라이브러리만 쓴다.

# %%
# 시각화 헬퍼. fig.show()를 직접 부르지 않고 이걸 통해 부른다.
def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


INF = float("inf")

# %% [markdown]
# ## 1. 라운드를 관찰할 수 있는 벨만-포드
#
# 표준 구현과 똑같지만, 라운드마다 거리표 스냅샷과 「이번 라운드에 갱신된 엣지 목록」을 남긴다.
#
# 완화(relax)는 단 한 줄이다.
#
# $$dist[v] \leftarrow \min\bigl(dist[v],\; dist[u] + w(u,v)\bigr)$$
#
# 마지막 검사 라운드는 값을 **고치지 않고** 「아직도 줄어드나?」만 묻는다.


# %%
def bellman_ford_trace(nodes, edges, start, extra_rounds=1):
    """|V|-1 라운드 완화 + extra_rounds 라운드의 '검사'.

    반환: (history, negative_cycle)
      history[i] = {"round": i, "dist": {...}, "updates": [(u,v,w,old,new), ...],
                    "check_only": bool}
    """
    dist = {n: INF for n in nodes}
    dist[start] = 0
    history = [{"round": 0, "dist": dict(dist), "updates": [], "check_only": False}]

    n_relax = len(nodes) - 1
    for r in range(1, n_relax + 1):
        updates = []
        for u, v, w in edges:
            if dist[u] == INF:  # 도달 못한 노드는 건너뛴다 (오버플로 방지)
                continue
            if dist[u] + w < dist[v]:
                updates.append((u, v, w, dist[v], dist[u] + w))
                dist[v] = dist[u] + w
        history.append(
            {"round": r, "dist": dict(dist), "updates": updates, "check_only": False}
        )

    # ── 여기부터가 음수 사이클 검사. 한 바퀴 더 돌린다.
    negative_cycle = False
    for r in range(n_relax + 1, n_relax + 1 + extra_rounds):
        updates = []
        for u, v, w in edges:
            if dist[u] == INF:
                continue
            if dist[u] + w < dist[v]:
                updates.append((u, v, w, dist[v], dist[u] + w))
                dist[v] = dist[u] + w  # 관찰용으로만 갱신 (계속 줄어드는 걸 보려고)
        if updates:
            negative_cycle = True
        history.append(
            {"round": r, "dist": dict(dist), "updates": updates, "check_only": True}
        )
    return history, negative_cycle


def fmt(x):
    return "∞" if x == INF else f"{x:g}"


def print_table(nodes, history, title):
    print(f"── {title}")
    head = f"{'라운드':>6} " + " ".join(f"{n:>6}" for n in nodes) + "   갱신"
    print(head)
    print("-" * len(head))
    for h in history:
        mark = "*" if h["check_only"] else " "
        row = f"{str(h['round']) + mark:>6} " + " ".join(
            f"{fmt(h['dist'][n]):>6}" for n in nodes
        )
        upd = ", ".join(f"{u}→{v}({old}→{new})" for u, v, _w, old, new in h["updates"])
        print(row + "   " + (upd if upd else "-"))
    print("  (* 표시가 |V|-1 라운드 이후의 '검사' 라운드)")


# %% [markdown]
# ## 2. 그래프 A — 음수 **가중치**는 있지만 음수 **사이클**은 없다
#
# 9장 `ex3_dijkstra_negative.py`에 나오는 그래프다.
#
# ```
# A→C (1), A→B (2), B→C (-5), C→D (1)
# ```
#
# `B→C`가 $-5$라 다익스트라는 여기서 조용히 틀린다. 하지만 사이클이 없으므로
# 벨만-포드는 정답을 내고, 검사 라운드에서 아무 것도 갱신되지 않는다.

# %%
NODES_A = ["A", "B", "C", "D"]
EDGES_A = [("A", "C", 1), ("A", "B", 2), ("B", "C", -5), ("C", "D", 1)]

hist_a, cyc_a = bellman_ford_trace(NODES_A, EDGES_A, "A")
print_table(NODES_A, hist_a, "그래프 A (음수 엣지 O, 음수 사이클 X)")
print(f"\n음수 사이클 판정: {'있다' if cyc_a else '없다'}")
print(f"최종 거리표: { {n: fmt(hist_a[-1]['dist'][n]) for n in NODES_A} }")

# 출력:
# ── 그래프 A (음수 엣지 O, 음수 사이클 X)
#    라운드      A      B      C      D   갱신
# ---------------------------------------
#     0       0      ∞      ∞      ∞   -
#     1       0      2     -3     -2   A→C(inf→1), A→B(inf→2), B→C(1→-3), C→D(inf→-2)
#     2       0      2     -3     -2   -
#     3       0      2     -3     -2   -
#     4*      0      2     -3     -2   -
#   (* 표시가 |V|-1 라운드 이후의 '검사' 라운드)
#
# 음수 사이클 판정: 없다
# 최종 거리표: {'A': '0', 'B': '2', 'C': '-3', 'D': '-2'}
#
# 참고: 이 엣지 순서에서는 라운드 1만에 수렴했다(C가 1로 갔다가 같은 라운드 안에서
# B→C로 -3까지 내려감). 라운드 2, 3은 확인만 하고 지나간다. 순서가 나쁘면
# 4절처럼 |V|-1 라운드를 꽉 채워야 한다.

# %% [markdown]
# 요점 두 가지.
#
# - 다익스트라는 `C`를 거리 1로 **확정**해 버려서 `D = 2`라는 틀린 값을 낸다.
#   벨만-포드는 확정 개념이 없고 모든 엣지를 계속 완화하므로 `C = -3`, `D = -2`를 얻는다.
# - 검사 라운드(`*`)의 갱신이 `-`다. 즉 모든 엣지가 삼각 부등식
#   $dist[v] \le dist[u] + w(u,v)$ 를 만족한다 → **음수 사이클 없음**.

# %% [markdown]
# ## 3. 그래프 B — 음수 사이클이 있다
#
# `B → C → D → B`를 도는 사이클의 합이 $2 + (-3) + (-2) = -3 < 0$ 이다.
#
# 이 사이클을 한 바퀴 돌 때마다 거리가 3씩 줄어든다. 최단 거리가 $-\infty$로 발산하므로
# **수렴할 값 자체가 없다.** 검사 라운드를 3번 붙여서 계속 줄어드는 모습을 본다.

# %%
NODES_B = ["A", "B", "C", "D"]
EDGES_B = [
    ("A", "B", 1),
    ("B", "C", 2),
    ("C", "D", -3),
    ("D", "B", -2),  # ← 이 엣지가 사이클을 닫는다
]

hist_b, cyc_b = bellman_ford_trace(NODES_B, EDGES_B, "A", extra_rounds=3)
print_table(NODES_B, hist_b, "그래프 B (음수 사이클 B→C→D→B, 합 = -3)")
print(f"\n음수 사이클 판정: {'있다' if cyc_b else '없다'}")

cycle_sum = 2 + (-3) + (-2)
print(f"사이클 가중치 합: {cycle_sum}")
print("검사 라운드마다 거리가 얼마나 더 줄었나:")
base = hist_b[len(NODES_B) - 1]["dist"]
for h in hist_b:
    if h["check_only"]:
        drop = {n: h["dist"][n] - base[n] for n in NODES_B}
        print(f"  라운드 {h['round']}: {drop}")

# 출력:
# ── 그래프 B (음수 사이클 B→C→D→B, 합 = -3)
#    라운드      A      B      C      D   갱신
# ---------------------------------------
#     0       0      ∞      ∞      ∞   -
#     1       0     -2      3      0   A→B(inf→1), B→C(inf→3), C→D(inf→0), D→B(1→-2)
#     2       0     -5      0     -3   B→C(3→0), C→D(0→-3), D→B(-2→-5)
#     3       0     -8     -3     -6   B→C(0→-3), C→D(-3→-6), D→B(-5→-8)
#     4*      0    -11     -6     -9   B→C(-3→-6), C→D(-6→-9), D→B(-8→-11)
#     5*      0    -14     -9    -12   B→C(-6→-9), C→D(-9→-12), D→B(-11→-14)
#     6*      0    -17    -12    -15   B→C(-9→-12), C→D(-12→-15), D→B(-14→-17)
#   (* 표시가 |V|-1 라운드 이후의 '검사' 라운드)
#
# 음수 사이클 판정: 있다
# 사이클 가중치 합: -3
# 검사 라운드마다 거리가 얼마나 더 줄었나:
#   라운드 4: {'A': 0, 'B': -3, 'C': -3, 'D': -3}
#   라운드 5: {'A': 0, 'B': -6, 'C': -6, 'D': -6}
#   라운드 6: {'A': 0, 'B': -9, 'C': -9, 'D': -9}

# %% [markdown]
# 사이클 위의 노드들이 라운드마다 정확히 **사이클 가중치 합(-3)** 만큼 더 줄어든다.
# 사이클 밖의 `A`는 그대로다. 이게 「$|V|-1$ 라운드로 끝났어야 하는데 아직도 줄어든다」의 정체다.
#
# ### 왜 이 검사가 정확한 판정인가 (증명 요약)
#
# **(→) 음수 사이클이 없으면 검사 라운드에서 갱신이 없다.**
# $|V|-1$ 라운드 뒤 `dist`는 진짜 최단 거리이고, 최단 거리는 모든 엣지에 대해
# 삼각 부등식 $dist[v] \le dist[u] + w(u,v)$ 를 만족한다. 따라서 완화 조건이 성립하지 않는다.
#
# **(←) 음수 사이클이 있으면 검사 라운드에서 반드시 갱신이 있다.**
# 사이클 $v_0 \to v_1 \to \dots \to v_k = v_0$ 위의 모든 엣지가 갱신되지 않았다고 가정하면
# 모든 $i$에 대해 $dist[v_i] \le dist[v_{i-1}] + w(v_{i-1}, v_i)$ 이다.
# 한 바퀴 전부 더하면 $dist$ 항이 상쇄되어
#
# $$0 \le \sum_{i=1}^{k} w(v_{i-1}, v_i)$$
#
# 가 남는데, 이는 사이클 합이 음수라는 가정에 모순이다.

# %% [markdown]
# ## 4. 왜 하필 $|V| - 1$회인가 — 최단 경로의 엣지 수 상한
#
# 음수 사이클이 없으면 최단 경로 중에는 **단순 경로**(같은 노드를 두 번 안 지남)가 반드시 있다.
# 사이클을 잘라내도 가중치 합이 $\ge 0$ 이므로 거리가 늘지 않기 때문이다.
# 단순 경로는 노드를 최대 $|V|$개 지나므로 엣지는 최대 $|V|-1$개다.
#
# 한편 벨만-포드의 불변식은 「라운드 $k$가 끝나면 $k$홉 이하 최단 거리가 확정된다」이다.
# 두 사실을 합치면 $|V|-1$ 라운드로 충분하다.
#
# 최악의 순서를 만들어 「라운드 하나에 홉 하나」밖에 못 나가는 경우를 직접 확인한다.
# 사슬 $0 \to 1 \to \dots \to n-1$ 의 엣지를 **역순**으로 훑으면 그렇게 된다.

# %%
def chain_edges(n, reverse_order=True):
    e = [(i, i + 1, 1) for i in range(n - 1)]
    return list(reversed(e)) if reverse_order else e


CHAIN_N = 7
CHAIN_NODES = list(range(CHAIN_N))
hist_c, cyc_c = bellman_ford_trace(CHAIN_NODES, chain_edges(CHAIN_N), 0)

print(f"사슬 {CHAIN_N}노드, 엣지를 역순으로 훑을 때 (최악의 순서)")
head = f"{'라운드':>6} " + " ".join(f"{n:>4}" for n in CHAIN_NODES) + "   확정된 홉"
print(head)
print("-" * len(head))
for h in hist_c:
    reached = sum(1 for n in CHAIN_NODES if h["dist"][n] != INF) - 1
    mark = "*" if h["check_only"] else " "
    print(
        f"{str(h['round']) + mark:>6} "
        + " ".join(f"{fmt(h['dist'][n]):>4}" for n in CHAIN_NODES)
        + f"   {reached}홉까지"
    )
print(f"\n음수 사이클 판정: {'있다' if cyc_c else '없다'}")
print(f"최단 경로의 최대 홉 수 = {CHAIN_N - 1} = |V| - 1  → 딱 그만큼의 라운드가 필요했다")

# 출력:
# 사슬 7노드, 엣지를 역순으로 훑을 때 (최악의 순서)
#    라운드    0    1    2    3    4    5    6   확정된 홉
# -------------------------------------------------
#     0     0    ∞    ∞    ∞    ∞    ∞    ∞   0홉까지
#     1     0    1    ∞    ∞    ∞    ∞    ∞   1홉까지
#     2     0    1    2    ∞    ∞    ∞    ∞   2홉까지
#     3     0    1    2    3    ∞    ∞    ∞   3홉까지
#     4     0    1    2    3    4    ∞    ∞   4홉까지
#     5     0    1    2    3    4    5    ∞   5홉까지
#     6     0    1    2    3    4    5    6   6홉까지
#     7*    0    1    2    3    4    5    6   6홉까지
#
# 음수 사이클 판정: 없다
# 최단 경로의 최대 홉 수 = 6 = |V| - 1  → 딱 그만큼의 라운드가 필요했다

# %% [markdown]
# 라운드가 하나 늘 때마다 확정되는 홉이 정확히 하나씩 는다.
# $|V|-1$을 한 번이라도 덜 돌면 마지막 노드가 $\infty$로 남는다.
# 그래서 $|V|-1$은 「넉넉히」가 아니라 **딱 맞는 상한**이다.

# %% [markdown]
# ## 5. 시각화 — 라운드별 거리 변화
#
# 왼쪽(그래프 A)은 $|V|-1$ 라운드에서 평평해지고 검사 라운드에서 움직이지 않는다.
# 오른쪽(그래프 B)은 검사 라운드 이후로도 계속 아래로 떨어진다. 이 「안 멈춤」이 판정 근거다.

# %%
# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
import os

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 비교를 위해 그래프 A에도 검사 라운드를 3번 붙인다
hist_a3, _ = bellman_ford_trace(NODES_A, EDGES_A, "A", extra_rounds=3)

PALETTE = ["#4C78A8", "#F58518", "#54A24B", "#E45756"]
CUT = len(NODES_A) - 1  # |V| - 1

fig = make_subplots(
    rows=1,
    cols=2,
    subplot_titles=(
        "그래프 A: 음수 사이클 없음 → 검사 라운드에서 정지",
        "그래프 B: 음수 사이클 있음 → 계속 감소",
    ),
    shared_xaxes=False,
)

for col, (hist, nodes, tag) in enumerate(
    [(hist_a3, NODES_A, "A"), (hist_b, NODES_B, "B")], start=1
):
    rounds = [h["round"] for h in hist]
    for i, n in enumerate(nodes):
        ys = [None if h["dist"][n] == INF else h["dist"][n] for h in hist]
        fig.add_trace(
            go.Scatter(
                x=rounds,
                y=ys,
                mode="lines+markers",
                name=f"{tag}:{n}",
                line=dict(color=PALETTE[i % len(PALETTE)], width=2),
                marker=dict(size=7),
                legendgroup=tag,
                showlegend=True,
            ),
            row=1,
            col=col,
        )
    # |V|-1 라운드 경계선
    fig.add_vline(
        x=CUT + 0.5,
        line=dict(color="#888", dash="dash", width=1.5),
        annotation_text="|V|-1 완료 → 여기부터 검사",
        annotation_position="top left",
        annotation_font_size=10,
        row=1,
        col=col,
    )
    fig.update_xaxes(title_text="완화 라운드", dtick=1, row=1, col=col)
    fig.update_yaxes(title_text="dist (∞는 생략)", row=1, col=col)

fig.update_layout(
    title="벨만-포드: |V|-1 라운드 뒤 한 바퀴 더 → 줄어들면 음수 사이클",
    template="plotly_white",
    height=460,
    width=1100,
    legend=dict(orientation="h", y=-0.18),
    margin=dict(t=90, b=80),
)

_show(fig)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(OUT, scale=2)
print(f"저장: {OUT}")

# 출력:
# 저장: .../9cf55aa4-2421-425d-b5f5-358c949ace83/expy.png

# %% [markdown]
# ## 6. 실무에서 밟는 지뢰
#
# | 실수 | 결과 |
# |---|---|
# | 검사 라운드를 빼먹음 | 음수 사이클이 있어도 못 잡고, 거리표는 그럴듯해 보인다 |
# | `dist[u]`가 $\infty$인 엣지를 그냥 계산 | C/Java에서 `INT_MAX + w`가 오버플로로 음수가 되어 **가짜 사이클** 판정 |
# | 시작점에서 도달 불가능한 음수 사이클 | 이 검사로는 안 잡힌다. 가상 소스에서 모든 노드로 가중치 0 엣지를 걸어야 전역 검사가 된다 |
# | 무향 그래프에 음수 엣지 하나 | 그 자체가 음수 사이클($u \to v \to u$)이다 |
#
# ### 마지막 한 줄
#
# $|V|-1$은 단순 경로의 엣지 수 상한이라 그 이상 돌 이유가 없다.
# 그래서 「그 뒤에도 줄어든다」는 사실이 곧 「최단 거리가 존재하지 않는다 = 음수 사이클이 있다」의 증거다.
