# %% [markdown]
# # `smell_cycle()` 은 사이클을 어떻게 검출하는가
#
# 13장 `ex3_graph_smells.py` 의 `smell_cycle()` 을 단계적으로 뜯어본다.
#
# 한 줄 요약: **DFS 를 돌면서 «지금 내가 밟고 서 있는 경로(`stack`)» 위의 노드를 다시
# 만나면 그게 사이클이다.** 그 노드가 경로 어디에 있었는지 찾아 거기서부터 잘라 낸다.
#
# 필요 패키지: `plotly`, `kaleido` (시각화 셀에서만 사용. 없으면 그 셀만 건너뛴다)

# %%
# 필요 패키지: plotly>=5, kaleido  (앞의 셀들은 표준 라이브러리만으로 동작한다)
import os
from collections import defaultdict


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()

# %% [markdown]
# ## 1. 작은 REPLACES 그래프
#
# 책의 예제에는 `n3 → n4 → n5 → n3` 이라는 «대체» 사이클이 심어져 있다.
# 여기에 **사이클이 아닌데 노드를 두 번 만나게 되는** 다이아몬드 모양(`a → b/c → d`)을
# 하나 더 붙인다. 이 다이아몬드가 뒤에서 «오탐» 을 가르는 시금석이 된다.

# %%
EDGES = [
    # 책 ex3_graph_smells.py 의 사이클 그대로
    ("n3", "REPLACES", "n4"),
    ("n4", "REPLACES", "n5"),
    ("n5", "REPLACES", "n3"),
    # 사이클 밖에서 사이클 안으로 들어오는 엣지
    ("n6", "REPLACES", "n3"),
    # 다이아몬드 — 사이클이 아니다. 하지만 d 는 두 경로로 «두 번» 도달한다.
    ("a", "REPLACES", "b"),
    ("a", "REPLACES", "c"),
    ("b", "REPLACES", "d"),
    ("c", "REPLACES", "d"),
    # 다른 관계는 무시되어야 한다 (사이클처럼 보이지만 rel 이 다르다)
    ("d", "SUPPLIED_BY", "a"),
]

print("엣지", len(EDGES), "개 / REPLACES 만", sum(1 for _, r, _ in EDGES if r == "REPLACES"), "개")
# 출력: 엣지 9 개 / REPLACES 만 8 개


def build_adj(edges, rel):
    """관계 이름이 rel 인 엣지만 골라 인접 리스트를 만든다."""
    adj = defaultdict(list)
    for a, r, b in edges:
        if r == rel:
            adj[a].append(b)
    return adj


ADJ = build_adj(EDGES, "REPLACES")
for u in ADJ:
    print(f"  {u} → {ADJ[u]}")
# 출력:
#   n3 → ['n4']
#   n4 → ['n5']
#   n5 → ['n3']
#   n6 → ['n3']
#   a → ['b', 'c']
#   b → ['d']
#   c → ['d']

# %% [markdown]
# ## 2. 원본 코드
#
# 책의 `smell_cycle()` 을 한 글자도 바꾸지 않고 옮겨 왔다.
#
# ```python
# def smell_cycle(edges, rel):
#     adj = defaultdict(list)
#     for a, r, b in edges:
#         if r == rel:
#             adj[a].append(b)
#     seen, stack, out = set(), set(), []
#
#     def go(u, path):
#         if u in stack:                                   # ← 사이클 검출 지점
#             out.append(path[path.index(u):] + [u]); return
#         if u in seen:                                    # ← 이미 끝난 가지, 다시 안 판다
#             return
#         seen.add(u); stack.add(u)
#         for v in adj[u]:
#             go(v, path + [u])
#         stack.discard(u)                                 # ← 되돌아 나올 때 스택에서 뺀다
#
#     for u in list(adj):
#         go(u, [])
#     return out
# ```
#
# 상태 변수는 셋이다.
#
# | 변수 | 뜻 | 색 |
# |---|---|---|
# | 어디에도 없음 | 아직 안 가 봄 | **white** (흰색) |
# | `stack` 에 있음 | 지금 내가 밟고 서 있는 경로 위 | **gray** (회색) |
# | `seen` 에 있고 `stack` 에 없음 | 다 파고 되돌아 나온 노드 | **black** (검정) |
#
# 집합 관계가 핵심이다. 언제나
#
# $$\text{stack} \subseteq \text{seen}$$
#
# 이므로 `stack` 검사를 **반드시 `seen` 검사보다 먼저** 해야 한다.

# %%
def smell_cycle(edges, rel):
    """책 ex3_graph_smells.py 원본."""
    adj = defaultdict(list)
    for a, r, b in edges:
        if r == rel:
            adj[a].append(b)
    seen, stack, out = set(), set(), []

    def go(u, path):
        if u in stack:
            out.append(path[path.index(u):] + [u]); return
        if u in seen:
            return
        seen.add(u); stack.add(u)
        for v in adj[u]:
            go(v, path + [u])
        stack.discard(u)

    for u in list(adj):
        go(u, [])
    return out


CYCLES = smell_cycle(EDGES, "REPLACES")
print(f"검출된 사이클 {len(CYCLES)}건")
for c in CYCLES:
    print("   ", " → ".join(c))
# 출력:
# 검출된 사이클 1건
#     n3 → n4 → n5 → n3

# %% [markdown]
# ## 3. DFS 추적 로그
#
# 같은 알고리즘에 로그만 붙였다. 각 줄은 «누구를 방문했고, 그때 white/gray/black 이
# 어떻게 나뉘어 있었는가» 를 보여 준다.
#
# 사이클은 **back edge** 를 만나는 순간 잡힌다. 즉 gray 노드로 향하는 엣지다.
# 반면 다이아몬드의 `b → d`, `c → d` 중 두 번째는 **cross edge** 이고, 그때 `d` 는
# 이미 black 이라 그냥 `return` 한다.

# %%
def smell_cycle_traced(edges, rel):
    adj = build_adj(edges, rel)
    seen, stack, out = set(), set(), []
    log = []

    def color(u):
        if u in stack:
            return "gray"
        if u in seen:
            return "black"
        return "white"

    def go(u, path, depth=0):
        pad = "  " * depth
        c = color(u)
        arrow = f"{path[-1]} → {u}" if path else f"(root) {u}"
        if u in stack:
            cyc = path[path.index(u):] + [u]
            log.append(f"{pad}{arrow:>14}  [{c:5}] back edge! 사이클 = {' → '.join(cyc)}")
            out.append(cyc)
            return
        if u in seen:
            log.append(f"{pad}{arrow:>14}  [{c:5}] 이미 끝난 가지 — 되돌아감(사이클 아님)")
            return
        seen.add(u); stack.add(u)
        log.append(f"{pad}{arrow:>14}  [white] 진입 · stack={sorted(stack)}")
        for v in adj[u]:
            go(v, path + [u], depth + 1)
        stack.discard(u)
        log.append(f"{pad}{'':>14}  [black] {u} 이탈 · stack={sorted(stack)}")

    for u in list(adj):
        go(u, [])
    return out, log


_, LOG = smell_cycle_traced(EDGES, "REPLACES")
print("\n".join(LOG))
# 출력:
#      (root) n3  [white] 진입 · stack=['n3']
#          n3 → n4  [white] 진입 · stack=['n3', 'n4']
#            n4 → n5  [white] 진입 · stack=['n3', 'n4', 'n5']
#              n5 → n3  [gray ] back edge! 사이클 = n3 → n4 → n5 → n3
#                     [black] n5 이탈 · stack=['n3', 'n4']
#                   [black] n4 이탈 · stack=['n3']
#                 [black] n3 이탈 · stack=[]
#      (root) n4  [black] 이미 끝난 가지 — 되돌아감(사이클 아님)
#      (root) n5  [black] 이미 끝난 가지 — 되돌아감(사이클 아님)
#      (root) n6  [white] 진입 · stack=['n6']
#          n6 → n3  [black] 이미 끝난 가지 — 되돌아감(사이클 아님)
#                 [black] n6 이탈 · stack=[]
#       (root) a  [white] 진입 · stack=['a']
#            a → b  [white] 진입 · stack=['a', 'b']
#              b → d  [white] 진입 · stack=['a', 'b', 'd']
#                     [black] d 이탈 · stack=['a', 'b']
#                   [black] b 이탈 · stack=['a']
#            a → c  [white] 진입 · stack=['a', 'c']
#              c → d  [black] 이미 끝난 가지 — 되돌아감(사이클 아님)
#                   [black] c 이탈 · stack=['a']
#                 [black] a 이탈 · stack=[]
#       (root) b  [black] 이미 끝난 가지 — 되돌아감(사이클 아님)
#       (root) c  [black] 이미 끝난 가지 — 되돌아감(사이클 아님)

# %% [markdown]
# 로그에서 읽어야 할 두 줄이 있다.
#
# * `n5 → n3` — `n3` 이 **gray**(= `stack` 안). 진짜 사이클. **back edge.**
# * `c → d` — `d` 는 **black**(= `seen` 이지만 `stack` 밖). 사이클 아님. **cross edge.**
#
# 두 줄 다 «이미 만나 본 노드» 다. 구분하는 건 오직 `stack` 뿐이다.
#
# ## 4. 사이클 경로를 잘라 내는 방법
#
# `path` 는 **`u` 까지 오는 데 거친 조상들의 리스트**다 (`u` 자신은 아직 안 들어 있다).
# `u` 가 `stack` 위에 있다는 건 `path` 안 어딘가에 `u` 가 이미 있다는 뜻이므로,
#
# $$i = \text{path.index}(u), \qquad \text{cycle} = \text{path}[i:] + [u]$$
#
# 로 **`u` 가 처음 나온 자리부터 끝까지** 를 잘라 낸다. 앞쪽의 «사이클로 들어오는 꼬리»
# 는 버려진다.

# %%
demo_path = ["n0", "n9", "n3", "n4", "n5"]   # n5 에서 n3 을 다시 만난 순간의 path
u = "n3"
i = demo_path.index(u)
print("path       :", demo_path)
print("index(n3)  :", i)
print("버려지는 꼬리:", demo_path[:i])
print("사이클      :", demo_path[i:] + [u])
# 출력:
# path       : ['n0', 'n9', 'n3', 'n4', 'n5']
# index(n3)  : 2
# 버려지는 꼬리: ['n0', 'n9']
# 사이클      : ['n3', 'n4', 'n5', 'n3']

# %% [markdown]
# ## 5. 틀리는 두 가지 방법
#
# ### (A) `seen` 만 쓰고 `stack` 을 안 쓴다 → **오탐**
#
# 무향 그래프 감각으로 «이미 방문한 노드를 또 만나면 사이클» 이라고 쓰면,
# 다이아몬드처럼 여러 경로로 같은 노드에 닿는 DAG 도 사이클로 신고한다.
# 게다가 `u` 가 `path` 에 없어서 `path.index(u)` 가 `ValueError` 로 터지기도 한다.
#
# ### (B) `seen` 을 먼저 검사한다 → **미탐**
#
# $\text{stack} \subseteq \text{seen}$ 이므로 `if u in seen: return` 이 앞에 오면
# `if u in stack:` 줄에는 **영원히 도달하지 못한다**. 사이클을 하나도 못 잡는다.
# 이건 조용히 0건을 뱉으므로 제일 위험하다.

# %%
def smell_cycle_visited_only(edges, rel):
    """(A) 잘못된 버전 — '이미 방문'을 '현재 스택 위'로 착각한다."""
    adj = build_adj(edges, rel)
    seen, out = set(), []

    def go(u, path):
        if u in seen:
            if u in path:
                out.append(path[path.index(u):] + [u])
            else:
                out.append(["<ValueError!>"] + path + [u])   # 원본이라면 여기서 예외
            return
        seen.add(u)
        for v in adj[u]:
            go(v, path + [u])

    for u in list(adj):
        go(u, [])
    return out


def smell_cycle_wrong_order(edges, rel):
    """(B) 잘못된 버전 — seen 검사를 stack 검사보다 먼저 한다."""
    adj = build_adj(edges, rel)
    seen, stack, out = set(), set(), []

    def go(u, path):
        if u in seen:                                   # stack ⊆ seen 이라 여기서 다 걸린다
            return
        if u in stack:                                  # 도달 불가능한 죽은 코드
            out.append(path[path.index(u):] + [u]); return
        seen.add(u); stack.add(u)
        for v in adj[u]:
            go(v, path + [u])
        stack.discard(u)

    for u in list(adj):
        go(u, [])
    return out


for name, fn in [
    ("올바름  (stack 먼저)", smell_cycle),
    ("(A) visited 만 사용 ", smell_cycle_visited_only),
    ("(B) seen 검사가 먼저", smell_cycle_wrong_order),
]:
    res = fn(EDGES, "REPLACES")
    print(f"{name} : {len(res)}건")
    for c in res:
        print("      ", " → ".join(c))
# 출력:
# 올바름  (stack 먼저) : 1건
#        n3 → n4 → n5 → n3
# (A) visited 만 사용  : 7건
#        n3 → n4 → n5 → n3
#        <ValueError!> → n4
#        <ValueError!> → n5
#        <ValueError!> → n6 → n3
#        <ValueError!> → a → c → d
#        <ValueError!> → b
#        <ValueError!> → c
# (B) seen 검사가 먼저 : 0건
#
# 진짜 사이클 1건 + 가짜 6건. <ValueError!> 로 표시된 것은 u 가 path 에 없어서
# 원본 코드였다면 path.index(u) 가 예외를 던졌을 자리다.

# %% [markdown]
# 결과가 정확히 세 갈래로 갈린다.
#
# | 버전 | 결과 | 문제 |
# |---|---|---|
# | 원본 | 1건 (`n3→n4→n5→n3`) | 정답 |
# | (A) `visited` 만 | 7건 | 다이아몬드·재진입까지 사이클로 신고 (**오탐**), 실제론 `ValueError` |
# | (B) 순서 뒤바꿈 | 0건 | 진짜 사이클도 못 잡음 (**미탐**) |
#
# ### 사이클이 없는 그래프에서도 확인

# %%
DAG_ONLY = [(a, "REPLACES", b) for a, b in [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")]]
print("올바른 버전 :", smell_cycle(DAG_ONLY, "REPLACES"))
print("(A) 버전    :", smell_cycle_visited_only(DAG_ONLY, "REPLACES"))
# 출력:
# 올바른 버전 : []
# (A) 버전    : [['<ValueError!>', 'a', 'c', 'd'], ['<ValueError!>', 'b'], ['<ValueError!>', 'c']]

# %% [markdown]
# 사이클이 하나도 없는 순수 DAG 인데 (A) 는 «사이클 3건» 이라고 보고한다.
# 13장 문맥으로 옮기면 — 사람이 검토할 스멜 목록에 가짜 항목이 섞여 들어간다.
# 스멜 검사는 자동으로 고치지 않고 «사람에게 목록을 준다» 는 게 일이기 때문에,
# 오탐은 사람의 신뢰를 깎아 먹고 결국 목록 자체를 안 보게 만든다.
#
# ## 6. 복잡도와 한계
#
# 각 노드와 엣지를 한 번씩 본다.
#
# $$O(V + E)$$
#
# 다만 `path + [u]` 로 리스트를 매번 복사하므로 깊이가 $d$ 일 때 경로 복사 비용이
# $O(d)$ 씩 더 붙는다. 작은 스멜 검사용으론 문제없지만 백만 노드에는 쓰지 못한다.
#
# 한계도 분명하다.
#
# * **모든 사이클을 열거하지 않는다.** back edge 하나당 하나만 기록한다.
#   전부 열거하려면 Johnson 알고리즘 같은 게 필요하다. 스멜 검사 목적으론 «있다/없다»
#   와 대표 경로 하나면 충분하다.
# * **재귀 깊이**가 파이썬 기본 한계(1000)에 걸릴 수 있다. 긴 체인이면 반복문 DFS 로.
# * `rel` 하나만 본다. 여러 관계가 섞여 도는 사이클은 못 잡는다 (위 예제의
#   `d --SUPPLIED_BY--> a` 가 무시되는 것이 그 예다).

# %%
# 재귀 대신 명시적 스택으로 같은 일을 하는 버전 (깊은 그래프용)
def smell_cycle_iterative(edges, rel):
    adj = build_adj(edges, rel)
    seen, on_stack, out = set(), set(), []
    for root in list(adj):
        if root in seen:
            continue
        # (노드, 자식 이터레이터) 를 직접 쌓는다. path 는 스택 자체가 들고 있다.
        path = []
        work = [(root, iter(adj[root]))]
        seen.add(root); on_stack.add(root); path.append(root)
        while work:
            u, it = work[-1]
            nxt = next(it, None)
            if nxt is None:
                work.pop(); on_stack.discard(u); path.pop()
                continue
            if nxt in on_stack:
                out.append(path[path.index(nxt):] + [nxt])
            elif nxt not in seen:
                seen.add(nxt); on_stack.add(nxt); path.append(nxt)
                work.append((nxt, iter(adj[nxt])))
    return out


print("재귀   :", smell_cycle(EDGES, "REPLACES"))
print("반복문 :", smell_cycle_iterative(EDGES, "REPLACES"))
# 출력:
# 재귀   : [['n3', 'n4', 'n5', 'n3']]
# 반복문 : [['n3', 'n4', 'n5', 'n3']]

# %% [markdown]
# ## 7. 시각화 — 사이클 엣지를 강조한 노드-링크 다이어그램
#
# 빨간 화살표가 `smell_cycle()` 이 잡아낸 사이클이다. 회색 화살표는 같은 REPLACES
# 관계지만 사이클에 속하지 않는다. 오른쪽 다이아몬드가 «두 번 도달하지만 사이클이
# 아닌» 부분이다.

# %%
POS = {
    "n3": (2.6, 1.0), "n4": (3.4, 0.2), "n5": (1.8, 0.2), "n6": (2.6, 1.9),
    "a": (5.2, 1.6), "b": (4.6, 0.8), "c": (5.8, 0.8), "d": (5.2, 0.0),
}
CYCLE_EDGES = set()
for c in CYCLES:
    for x, y in zip(c, c[1:]):
        CYCLE_EDGES.add((x, y))
print("사이클 엣지:", sorted(CYCLE_EDGES))
# 출력: 사이클 엣지: [('n3', 'n4'), ('n4', 'n5'), ('n5', 'n3')]

try:
    import plotly.graph_objects as go_

    CYC_COLOR, NORM_COLOR = "#d1495b", "#9aa5b1"
    fig = go_.Figure()
    annos = []
    for a, r, b in EDGES:
        if r != "REPLACES":
            continue
        is_cyc = (a, b) in CYCLE_EDGES
        x0, y0 = POS[a]; x1, y1 = POS[b]
        annos.append(dict(
            x=x1, y=y1, ax=x0, ay=y0, xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=3, arrowsize=1.4,
            arrowwidth=3 if is_cyc else 1.6,
            arrowcolor=CYC_COLOR if is_cyc else NORM_COLOR,
            standoff=16, startstandoff=16,
        ))

    in_cycle = {v for c in CYCLES for v in c}
    xs = [POS[v][0] for v in POS]
    ys = [POS[v][1] for v in POS]
    fig.add_trace(go_.Scatter(
        x=xs, y=ys, mode="markers+text",
        text=list(POS), textposition="middle center",
        textfont=dict(size=13, color="white"),
        marker=dict(
            size=42,
            color=[CYC_COLOR if v in in_cycle else "#4a6fa5" for v in POS],
            line=dict(width=0),
        ),
        hovertext=[f"{v} — {'사이클 위' if v in in_cycle else '사이클 아님'}" for v in POS],
        hoverinfo="text", showlegend=False,
    ))
    # 범례용 더미 트레이스
    for nm, col in [("사이클 (back edge)", CYC_COLOR), ("일반 REPLACES", NORM_COLOR)]:
        fig.add_trace(go_.Scatter(x=[None], y=[None], mode="lines",
                                  line=dict(color=col, width=3), name=nm))

    fig.update_layout(
        title="REPLACES 그래프 — smell_cycle() 이 잡아낸 사이클",
        annotations=annos, template="plotly_white",
        xaxis=dict(visible=False, range=[1.2, 6.4]),
        yaxis=dict(visible=False, range=[-0.5, 2.4], scaleanchor="x"),
        width=860, height=520,
        legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center"),
        margin=dict(l=20, r=20, t=60, b=40),
    )
    _show(fig)
    fig.write_image(os.path.join(HERE, "expy.png"), scale=2)
    print("expy.png 저장 완료")
except ImportError:
    print("plotly / kaleido 가 없어 시각화를 건너뛴다. pip install plotly kaleido")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# 1. `smell_cycle()` 은 DFS 를 돌면서 **`stack`(= 지금 밟고 있는 경로)** 을 따로 관리한다.
# 2. `stack` 위의 노드를 다시 만나면 그것이 **back edge**, 곧 사이클이다.
# 3. `path[path.index(u):] + [u]` 로 사이클 부분만 잘라 기록한다.
# 4. `seen`(black 포함) 과 `stack`(gray) 을 혼동하면
#    — `seen` 만 쓰면 **오탐**(DAG 를 사이클이라 신고),
#    — `seen` 을 먼저 검사하면 **미탐**(사이클을 하나도 못 잡음).
# 5. SHACL 에는 «순환 없음» 제약이 없다. 그래서 이건 2층(스멜)에서 «세어 보는» 검사고,
#    자동으로 고치지 않고 사람이 볼 목록만 뽑는다.
