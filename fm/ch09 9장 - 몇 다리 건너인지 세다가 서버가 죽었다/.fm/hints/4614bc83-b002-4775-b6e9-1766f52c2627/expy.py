# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# 시각화 셀을 건너뛰면 표준 라이브러리만으로도 전부 실행된다.

# %% [markdown]
# # 다익스트라는 정확히 어떤 순서로 틀리는가
#
# `ex3_dijkstra_negative.py`의 그래프는 노드 4개, 엣지 4개짜리다.
#
# | 엣지 | 가중치 |
# |---|---|
# | A → C | $1$ |
# | A → B | $2$ |
# | B → C | $-5$ |
# | C → D | $1$ |
#
# 다익스트라가 기대는 전제는 이거다.
#
# $$\text{우선순위 큐에서 꺼낸 } u \text{의 } dist[u] \text{는 더 줄어들 수 없다}$$
#
# 이 전제는 **모든 가중치가 음이 아닐 때만** 참이다. 앞으로 갈 길의 비용이
# 항상 $\ge 0$ 이어야 "지금 제일 가까운 후보"가 곧 최종 답이 되기 때문이다.
# 여기서는 $B \to C$ 가 $-5$ 라서 전제가 깨진다.

# %%
import heapq
from collections import defaultdict

EDGES = [("A", "C", 1), ("A", "B", 2), ("B", "C", -5), ("C", "D", 1)]
NODES = ["A", "B", "C", "D"]

ADJ = defaultdict(list)
for a, b, w in EDGES:
    ADJ[a].append((b, w))

print("엣지:", EDGES)
print("인접:", dict(ADJ))
# 출력: 엣지: [('A', 'C', 1), ('A', 'B', 2), ('B', 'C', -5), ('C', 'D', 1)]
# 출력: 인접: {'A': [('C', 1), ('B', 2)], 'B': [('C', -5)], 'C': [('D', 1)]}


# %% [markdown]
# ## 1단계 — 다익스트라를 한 걸음씩 추적한다
#
# 원본과 똑같은 알고리즘인데, 팝/확정/완화(relax)가 일어날 때마다 로그를 남긴다.
# 핵심 줄은 원본의 `done.add(u)` — **한 번 확정하면 다시 안 본다**는 그 한 줄이다.

# %%
def dijkstra_trace(edges, start):
    adj = defaultdict(list)
    for a, b, w in edges:
        adj[a].append((b, w))

    dist = {start: 0}
    done = set()
    order = []          # 확정된 순서
    log = []            # (단계 설명, 그 시점의 거리표 스냅샷)
    pq = [(0, start)]
    step = 0

    def snap():
        return {n: dist.get(n, float("inf")) for n in NODES}

    log.append(("시작: dist[A]=0", snap()))
    while pq:
        d, u = heapq.heappop(pq)
        step += 1
        if u in done:
            log.append((f"[{step}] pop ({d}, {u}) → 이미 확정됨. 버린다(다시 안 펼침)", snap()))
            continue
        done.add(u)
        order.append(u)
        log.append((f"[{step}] pop ({d}, {u}) → {u} 확정 (확정 순서 {len(order)}번째)", snap()))
        for v, w in adj[u]:
            nd = d + w
            old = dist.get(v, float("inf"))
            if nd < old:
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
                log.append((f"      완화 {u}→{v}: {d}+{w}={nd} < {old} ⇒ dist[{v}]={nd}", snap()))
            else:
                log.append((f"      완화 {u}→{v}: {d}+{w}={nd} ≥ {old} ⇒ 무시", snap()))
    return dist, order, log


dist_d, order_d, log_d = dijkstra_trace(EDGES, "A")

def fmt(v):
    return "∞" if v == float("inf") else f"{v}"

print(f"{'단계':<62} {'A':>4} {'B':>4} {'C':>4} {'D':>4}")
print("-" * 84)
for desc, snapshot in log_d:
    row = " ".join(f"{fmt(snapshot[n]):>4}" for n in NODES)
    print(f"{desc:<62} {row}")
print("\n확정 순서:", " → ".join(order_d))
# 출력:
# 단계                                                                A    B    C    D
# ------------------------------------------------------------------------------------
# 시작: dist[A]=0                                                     0    ∞    ∞    ∞
# [1] pop (0, A) → A 확정 (확정 순서 1번째)                             0    ∞    ∞    ∞
#       완화 A→C: 0+1=1 < inf ⇒ dist[C]=1                             0    ∞    1    ∞
#       완화 A→B: 0+2=2 < inf ⇒ dist[B]=2                             0    2    1    ∞
# [2] pop (1, C) → C 확정 (확정 순서 2번째)                             0    2    1    ∞
#       완화 C→D: 1+1=2 < inf ⇒ dist[D]=2                             0    2    1    2
# [3] pop (2, B) → B 확정 (확정 순서 3번째)                             0    2    1    2
#       완화 B→C: 2+-5=-3 < 1 ⇒ dist[C]=-3                            0    2   -3    2
# [4] pop (-3, C) → 이미 확정됨. 버린다(다시 안 펼침)                     0    2   -3    2
# [5] pop (2, D) → D 확정 (확정 순서 4번째)                             0    2   -3    2
#
# 확정 순서: A → C → B → D
# (※ 위 표는 실행 결과를 그대로 옮긴 것. 정렬 폭은 한글 폭 때문에 눈으로는 조금 어긋나 보인다)


# %% [markdown]
# ## 2단계 — 틀리는 순간을 문장으로
#
# 1. $A \to C = 1$, $A \to B = 2$ 라서 큐에서 **C가 B보다 먼저** 나온다.
# 2. C를 확정한 그 상태에서 $D = 1 + 1 = 2$ 로 계산한다.
# 3. 그 다음 B를 처리하며 $A \to B \to C = 2 + (-5) = -3$ 임을 알아낸다.
#    거리표에는 $dist[C] = -3$ 으로 **적는다**.
# 4. 그런데 C는 이미 확정(`done`)이라 큐에서 $(-3, C)$ 를 다시 꺼내도 버린다.
#    C의 이웃 D를 **다시 펼치지 않는다**.
# 5. 그래서 $D$ 는 $2$ 로 남는다. 정답은 $-3 + 1 = -2$.
#
# 고약한 점: **C는 맞고 D만 틀렸다.** 거리표에서 시작점 근처(A, B, C)만 보면
# 전부 정답이라 "잘 돌고 있네" 싶다. 틀린 건 확정 이후에 갱신된 노드의 **하류**다.
#
# 그리고 예외가 안 난다. 조용히 틀린 숫자를 돌려준다.

# %%
def bellman_ford(edges, start, nodes):
    dist = {n: float("inf") for n in nodes}
    dist[start] = 0
    for _ in range(len(nodes) - 1):
        for a, b, w in edges:
            if dist[a] + w < dist[b]:
                dist[b] = dist[a] + w
    for a, b, w in edges:                # 한 바퀴 더 → 음수 사이클 검사
        if dist[a] + w < dist[b]:
            return dist, True
    return dist, False


dist_bf, has_cycle = bellman_ford(EDGES, "A", NODES)

print(f"{'노드':<5} {'다익스트라':>12} {'벨만-포드':>12} {'같나':>6}")
for n in NODES:
    a, b = dist_d.get(n, float("inf")), dist_bf[n]
    print(f"{n:<5} {fmt(a):>12} {fmt(b):>12} {'예' if a == b else '아니오':>6}")
print(f"\n음수 사이클: {'있다' if has_cycle else '없다'}")
print(f"D 오차: 다익스트라 {dist_d['D']} vs 정답 {dist_bf['D']}  (차이 {dist_d['D'] - dist_bf['D']})")
# 출력:
# 노드      다익스트라        벨만-포드     같나
# A                0            0      예
# B                2            2      예
# C               -3           -3      예
# D                2           -2  아니오
#
# 음수 사이클: 없다
# D 오차: 다익스트라 2 vs 정답 -2  (차이 4)


# %% [markdown]
# ## 3단계 — "다시 펼치기"를 허용하면 고쳐진다
#
# `done` 집합을 지우면(= 확정을 포기하면) 사실상 SPFA/벨만-포드가 된다.
# 답은 맞지만 최악의 경우 지수적으로 같은 노드를 다시 펼친다. 이게 다익스트라가
# "확정"을 두는 이유이자, 음수 가중치에서 그 최적화가 무너지는 이유다.

# %%
def dijkstra_no_done(edges, start):
    """done 집합을 없앤 버전 = 재확장 허용. 정답은 맞지만 성능 보장이 사라진다."""
    adj = defaultdict(list)
    for a, b, w in edges:
        adj[a].append((b, w))
    dist = {start: 0}
    pq = [(0, start)]
    pops = 0
    while pq:
        d, u = heapq.heappop(pq)
        pops += 1
        if d > dist.get(u, float("inf")):
            continue
        for v, w in adj[u]:
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist, pops


dist_fix, pops = dijkstra_no_done(EDGES, "A")
print("재확장 허용:", {n: fmt(dist_fix.get(n, float("inf"))) for n in NODES}, f"(pop {pops}회)")
print("벨만-포드  :", {n: fmt(dist_bf[n]) for n in NODES})
print("일치:", all(dist_fix.get(n) == dist_bf[n] for n in NODES))
# 출력: 재확장 허용: {'A': '0', 'B': '2', 'C': '-3', 'D': '-2'} (pop 6회)
# 출력: 벨만-포드  : {'A': '0', 'B': '2', 'C': '-3', 'D': '-2'}
# 출력: 일치: True


# %% [markdown]
# ## 4단계 — 그림으로
#
# 왼쪽: 그래프와 가중치(음수 엣지는 붉은색). 노드 라벨에 다익스트라 값과 정답을 같이 적었다.
# 오른쪽: 확정이 일어난 시점마다의 거리표 히트맵. $C$ 행이 확정 **뒤에** $1 \to -3$ 으로
# 바뀌는데도 $D$ 행은 $2$ 에 굳어 있는 게 보인다.

# %%
def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


import os

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    POS = {"A": (0, 0), "B": (1, 1), "C": (1, -1), "D": (2, -1)}

    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.46, 0.54],
        subplot_titles=("그래프 (붉은 엣지 = 음수)", "확정 시점별 거리표"),
        specs=[[{"type": "scatter"}, {"type": "heatmap"}]],
    )

    # --- 왼쪽: 그래프 ---
    for a, b, w in EDGES:
        x0, y0 = POS[a]
        x1, y1 = POS[b]
        neg = w < 0
        fig.add_trace(
            go.Scatter(
                x=[x0, x1], y=[y0, y1], mode="lines",
                line=dict(color="#d62728" if neg else "#8c8c8c", width=4 if neg else 2),
                hoverinfo="skip", showlegend=False,
            ), row=1, col=1,
        )
        fig.add_annotation(
            x=(x0 + x1) / 2, y=(y0 + y1) / 2, text=f"<b>{w}</b>",
            showarrow=False, font=dict(size=14, color="#d62728" if neg else "#333"),
            bgcolor="rgba(255,255,255,0.85)", row=1, col=1,
        )

    wrong = [dist_d.get(n) != dist_bf[n] for n in NODES]
    fig.add_trace(
        go.Scatter(
            x=[POS[n][0] for n in NODES], y=[POS[n][1] for n in NODES],
            mode="markers+text", text=NODES, textposition="middle center",
            textfont=dict(size=17, color="#111"),
            marker=dict(size=44, color=["#ffb3b3" if w_ else "#bcd9ff" for w_ in wrong],
                        line=dict(color="#333", width=2)),
            hoverinfo="skip", showlegend=False,
        ), row=1, col=1,
    )
    # 노드별 거리 라벨은 엣지와 겹치지 않게 방향을 따로 준다
    OFF = {"A": (-0.52, 0), "B": (0, 0.34), "C": (0, -0.34), "D": (0, -0.34)}
    for n in NODES:
        bad = dist_d.get(n) != dist_bf[n]
        fig.add_annotation(
            x=POS[n][0] + OFF[n][0], y=POS[n][1] + OFF[n][1],
            text=f"D={fmt(dist_d.get(n, float('inf')))} / 정답={fmt(dist_bf[n])}",
            showarrow=False, font=dict(size=12, color="#c00000" if bad else "#333"),
            row=1, col=1,
        )

    # --- 오른쪽: 확정 시점 스냅샷 히트맵 ---
    cols, snaps = [], []
    for desc, snapshot in log_d:
        if "확정" in desc and "이미" not in desc:
            u = desc.split("pop (")[1].split(", ")[1].split(")")[0]
            cols.append(f"{len(cols) + 1}. {u} 확정")
            snaps.append(snapshot)
    cols.append("최종")
    snaps.append({n: dist_d.get(n, float("inf")) for n in NODES})
    cols.append("정답(BF)")
    snaps.append(dist_bf)

    # inf 는 None 으로 두어 회색 배경 그대로 두고, 숫자만 색으로 구분한다
    z = [[None if s[n] == float("inf") else s[n] for s in snaps] for n in NODES]
    txt = [[fmt(s[n]) for s in snaps] for n in NODES]
    fig.add_trace(
        go.Heatmap(
            z=z, x=cols, y=NODES, text=txt, texttemplate="%{text}",
            textfont=dict(size=16), colorscale="RdBu_r", zmid=0, zmin=-4, zmax=4,
            showscale=False, xgap=3, ygap=3, hoverinfo="skip",
        ), row=1, col=2,
    )
    # 틀린 칸(다익스트라 최종 D) 을 붉은 테두리로 강조
    ci, ri = len(cols) - 2, NODES.index("D")
    fig.add_shape(type="rect", x0=ci - 0.5, x1=ci + 0.5, y0=ri - 0.5, y1=ri + 0.5,
                  line=dict(color="#c00000", width=4), row=1, col=2)
    fig.add_annotation(xref="x2", yref="paper", x=cols[ci], y=-0.155,
                       text="↑ 최종 D=2 — 여기가 틀림 (정답 -2)", showarrow=False,
                       font=dict(size=12, color="#c00000"))

    fig.update_xaxes(visible=False, range=[-1.25, 2.6], row=1, col=1)
    fig.update_yaxes(visible=False, range=[-1.75, 1.6], row=1, col=1)
    fig.update_xaxes(tickfont=dict(size=12), row=1, col=2)
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=14), row=1, col=2)
    fig.update_layout(
        title="다익스트라가 틀리는 순서: A → C 확정 → D=2 고정 → 뒤늦게 C=-3 (그러나 D는 그대로)",
        width=1180, height=520, plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=110, b=95, l=40, r=40),
    )

    _show(fig)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
    fig.write_image(out, scale=2)
    print("저장:", out)
except ImportError as e:
    print("plotly/kaleido 미설치 — 시각화 생략:", e)
# 출력: 저장: .../4614bc83-b002-4775-b6e9-1766f52c2627/expy.png


# %% [markdown]
# ## 정리
#
# - 틀리는 **순서**: `A 확정 → C 확정(dist=1) → D=1+1=2 → B 확정 → dist[C]=-3 기록 →
#   (-3, C) 팝은 done이라 버림 → D는 2로 남음`
# - 즉 **잘못된 확정 하나가, 그 노드의 하류 전체를 오염시킨다.**
# - C 자체는 거리표가 나중에 갱신돼서 정답이다. 그래서 시작점 근처만 검증하면 못 잡는다.
# - 실무에서 음수가 새어 들어오는 자리: 할인/환급을 음수 비용으로 모델링, `1 - 유사도`가
#   음수가 되는 경우, 그리고 확률 곱을 최단 경로로 바꾸려고 $-\log p$ 대신 $\log p$ 를
#   쓴 경우($\log 0.5 = -0.69$). 마지막이 제일 흔하다.
# - 음수가 있을 수 있으면 벨만-포드(또는 SPFA/존슨)를 쓴다. 확률이면 $-\log p \ge 0$ 이
#   되도록 부호를 뒤집어 다익스트라를 그대로 살리는 방법도 있다.
