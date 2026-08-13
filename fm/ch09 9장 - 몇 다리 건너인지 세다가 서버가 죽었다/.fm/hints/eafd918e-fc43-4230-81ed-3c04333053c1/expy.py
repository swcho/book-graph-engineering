# %% [markdown]
# # `bfs_levels()` — 홉별 통계는 어떻게 계산되나
#
# **질문**: `bfs_levels()`는 홉별 통계를 어떻게 계산하는가?
#
# **답**: frontier를 유지하며 홉마다 아직 보지 않은 이웃만 모아 다음 frontier로 삼고,
# 이번 홉의 새 노드 수와 누적 방문 수를 기록한다.
#
# 핵심 아이디어 세 가지:
#
# 1. **frontier(경계)** — "직전 홉에서 처음 발견된 노드들"만 담는 리스트. 큐가 아니라 층(layer) 단위 리스트다.
# 2. **seen(방문 집합)** — 이미 발견한 노드 전부. `v not in seen` 검사가 중복 방문과 되돌아감을 동시에 막는다.
# 3. **out(통계)** — 홉마다 `(hop, len(nxt), len(seen))` 튜플 하나. 각각 홉 번호, 이번 홉의 새 노드 수, 누적 방문 수.
#
# 평균 차수가 $\bar{d}$ 이면 한 홉마다 대략 $\bar{d}-1$ 배씩 늘어난다.
# 홉 $h$ 까지의 누적 방문 수는 대략
#
# $$ |S_h| \approx 1 + \bar{d}\sum_{i=0}^{h-1}(\bar{d}-1)^i $$
#
# 로 지수 증가한다. 그래서 상한 없는 순회는 사실상 전체 스캔이 된다.

# %%
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용. 없으면 해당 셀만 건너뛴다)
import random
from collections import defaultdict


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1단계 — 원본 구현 그대로 보기
#
# 책 `ex1_bfs_explosion.py`의 함수다. 주석으로 각 줄이 무슨 일을 하는지 붙였다.

# %%
def bfs_levels(adj, start, max_hop):
    seen = {start}          # 지금까지 발견한 노드 전부 (시작 노드 포함)
    frontier = [start]      # "이번에 펼칠" 층. 처음엔 시작 노드 하나
    out = []                # 홉별 통계 (hop, 이번 홉 새 노드 수, 누적)
    for hop in range(1, max_hop + 1):
        nxt = []                             # 다음 층을 여기에 모은다
        for u in frontier:                   # 현재 층의 노드만 펼친다
            for v in adj.get(u, ()):         # 그 이웃들을 훑고
                if v not in seen:            # 처음 보는 노드만
                    seen.add(v)              # 즉시 seen 에 넣어 중복 차단
                    nxt.append(v)            # 다음 층 후보로 추가
        out.append((hop, len(nxt), len(seen)))  # 이번 홉 새 노드 수 + 누적
        frontier = nxt                       # 다음 층으로 교체 (핵심)
        if not frontier:                     # 더 뻗을 곳이 없으면 조기 종료
            break
    return out


print(bfs_levels.__name__, "정의 완료")
# 출력: bfs_levels 정의 완료


# %% [markdown]
# ## 2단계 — 손으로 따라갈 수 있는 작은 그래프
#
# 아래 그래프에서 노드 `0`에서 출발해 홉별로 무엇이 발견되는지 본다.
#
# ```
# 0 ─ 1 ─ 3 ─ 5
# │   │       │
# 2 ─ 4 ─────-6 ─ 7
# ```

# %%
SMALL = {
    0: [1, 2],
    1: [0, 3, 4],
    2: [0, 4],
    3: [1, 5],
    4: [1, 2, 6],
    5: [3, 6],
    6: [4, 5, 7],
    7: [6],
}

for hop, new, total in bfs_levels(SMALL, 0, 10):
    print(f"홉 {hop}: 새 노드 {new}개, 누적 {total}개")
# 출력: 홉 1: 새 노드 2개, 누적 3개
# 출력: 홉 2: 새 노드 2개, 누적 5개
# 출력: 홉 3: 새 노드 2개, 누적 7개
# 출력: 홉 4: 새 노드 1개, 누적 8개
# 출력: 홉 5: 새 노드 0개, 누적 8개
# (홉 5에서 frontier 가 비어 break — max_hop 10 을 다 돌지 않는다)


# %% [markdown]
# ## 3단계 — frontier 가 어떻게 바뀌는지 눈으로 보기
#
# 원본과 동일한 로직에 "이번 층에 누가 들어갔는지"를 추적하는 버전.
# `seen` 에 **발견 즉시** 넣는 것이 중요하다. 같은 층 안에서 두 노드가
# 같은 이웃을 가리켜도 새 노드는 한 번만 세어진다.

# %%
def bfs_levels_verbose(adj, start, max_hop):
    seen = {start}
    frontier = [start]
    rows = []
    for hop in range(1, max_hop + 1):
        nxt = []
        for u in frontier:
            for v in adj.get(u, ()):
                if v not in seen:
                    seen.add(v)
                    nxt.append(v)
        rows.append((hop, list(frontier), list(nxt), len(nxt), len(seen)))
        frontier = nxt
        if not frontier:
            break
    return rows


for hop, cur, nxt, new, total in bfs_levels_verbose(SMALL, 0, 10):
    print(f"홉 {hop}: frontier={cur} → 다음 frontier={nxt} (새 {new}, 누적 {total})")
# 출력: 홉 1: frontier=[0] → 다음 frontier=[1, 2] (새 2, 누적 3)
# 출력: 홉 2: frontier=[1, 2] → 다음 frontier=[3, 4] (새 2, 누적 5)
# 출력: 홉 3: frontier=[3, 4] → 다음 frontier=[5, 6] (새 2, 누적 7)
# 출력: 홉 4: frontier=[5, 6] → 다음 frontier=[7] (새 1, 누적 8)
# 출력: 홉 5: frontier=[7] → 다음 frontier=[] (새 0, 누적 8)


# %% [markdown]
# ## 4단계 — `seen` 검사를 빼면 어떻게 되나
#
# `if v not in seen` 이 없으면 홉마다 왔던 길을 되돌아가고, "새 노드 수"가
# 새 노드가 아니라 **엣지 수**를 세게 된다. 무한히 커진다.

# %%
def bfs_levels_broken(adj, start, max_hop):
    """일부러 seen 검사를 뺀 잘못된 버전."""
    frontier = [start]
    out = []
    total = 1
    for hop in range(1, max_hop + 1):
        nxt = [v for u in frontier for v in adj.get(u, ())]
        total += len(nxt)
        out.append((hop, len(nxt), total))
        frontier = nxt
    return out


print("올바른 버전 (누적은 8에서 멈춤):")
for hop, new, total in bfs_levels(SMALL, 0, 6):
    print(f"  홉 {hop}: 새 {new:>4}, 누적 {total:>5}")
print("seen 없는 버전 (끝없이 증가):")
for hop, new, total in bfs_levels_broken(SMALL, 0, 6):
    print(f"  홉 {hop}: 새 {new:>4}, 누적 {total:>5}")
# 출력: 올바른 버전 (누적은 8에서 멈춤):
# 출력:   홉 1: 새    2, 누적     3
# 출력:   홉 2: 새    2, 누적     5
# 출력:   홉 3: 새    2, 누적     7
# 출력:   홉 4: 새    1, 누적     8
# 출력:   홉 5: 새    0, 누적     8
# 출력: seen 없는 버전 (끝없이 증가):
# 출력:   홉 1: 새    2, 누적     3
# 출력:   홉 2: 새    5, 누적     8
# 출력:   홉 3: 새   12, 누적    20
# 출력:   홉 4: 새   31, 누적    51
# 출력:   홉 5: 새   72, 누적   123
# 출력:   홉 6: 새  185, 누적   308


# %% [markdown]
# ## 5단계 — 실제 규모에서의 폭발
#
# 책의 `graph.make()` 와 같은 방식으로 랜덤 그래프를 만든다.
# 원본은 노드 20만 개(메모리 약 1GB)를 쓰지만, 여기서는 5만 개로 줄인다.
# 배수(이번 홉 새 노드 / 직전 홉 새 노드)가 대략 평균 차수 - 1 근처에서
# 시작해, 그래프를 다 덮는 순간 급격히 꺾이는 게 관전 포인트다.

# %%
def make(n=50_000, avg_deg=12, seed=20260801):
    rnd = random.Random(seed)
    adj = defaultdict(list)
    for a in range(n):
        for _ in range(avg_deg // 2):
            b = rnd.randrange(n)
            if a != b:
                adj[a].append(b)
                adj[b].append(a)
    return {k: sorted(set(v)) for k, v in adj.items()}


ADJ = make()
n_nodes = len(ADJ)
avg_deg = sum(len(v) for v in ADJ.values()) / n_nodes
print(f"노드 {n_nodes:,}  평균 차수 {avg_deg:.1f}")
# 출력: 노드 50,000  평균 차수 12.0

levels = bfs_levels(ADJ, 0, 8)
print(f"{'홉':>3} {'이번 홉 새 노드':>16} {'누적':>10} {'배수':>8} {'전체 대비':>10}")
prev = 1
for hop, new, total in levels:
    print(f"{hop:>3} {new:>16,} {total:>10,} {new / max(prev, 1):>7.1f}x "
          f"{total / n_nodes * 100:>9.1f}%")
    prev = new
# 출력:   홉        이번 홉 새 노드         누적       배수      전체 대비
# 출력:   1               15         16    15.0x       0.0%
# 출력:   2              177        193    11.8x       0.4%
# 출력:   3            2,015      2,208    11.4x       4.4%
# 출력:   4           17,914     20,122     8.9x      40.2%
# 출력:   5           29,633     49,755     1.7x      99.5%
# 출력:   6              245     50,000     0.0x     100.0%
# 출력:   7                0     50,000     0.0x     100.0%
# (홉 7에서 새 노드가 0 → frontier 가 비어 break. max_hop=8 을 다 쓰지 않는다)


# %% [markdown]
# ## 6단계 — 시각화
#
# 왼쪽: 홉별 "이번 홉 새 노드 수"(로그 축). 초반 몇 홉은 직선 = 지수 증가.
# 오른쪽: 누적 방문 비율. S자를 그리며 5~6홉에서 100%에 닿는다.
#
# 이 두 곡선이 `bfs_levels()` 가 반환하는 `(hop, len(nxt), len(seen))` 튜플의
# 두 번째·세 번째 값이다.

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    hops = [h for h, _, _ in levels]
    news = [nw for _, nw, _ in levels]
    pcts = [t / n_nodes * 100 for _, _, t in levels]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("홉별 새 노드 수 (len(nxt), 로그 축)",
                        "누적 방문 비율 (len(seen) / N)"),
    )
    fig.add_trace(
        go.Bar(x=hops, y=news, name="이번 홉 새 노드",
               marker_color="#4C78A8",
               text=[f"{v:,}" for v in news], textposition="outside"),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=hops, y=pcts, name="누적 %", mode="lines+markers",
                   line=dict(color="#E45756", width=3)),
        row=1, col=2,
    )
    fig.update_yaxes(type="log", title_text="새 노드 수 (log)", row=1, col=1)
    fig.update_yaxes(title_text="전체 대비 %", range=[0, 105], row=1, col=2)
    fig.update_xaxes(title_text="홉", dtick=1, row=1, col=1)
    fig.update_xaxes(title_text="홉", dtick=1, row=1, col=2)
    fig.update_layout(
        title=f"bfs_levels(): 노드 {n_nodes:,}, 평균 차수 {avg_deg:.1f}",
        height=460, width=1000, showlegend=False, template="plotly_white",
    )
    _show(fig)

    import os
    out_png = os.path.join(os.path.dirname(os.path.abspath(__file__))
                           if "__file__" in dir() else ".", "expy.png")
    fig.write_image(out_png, scale=2)
    print("저장:", out_png)
except ImportError as e:
    print("plotly/kaleido 없음 — 시각화 건너뜀:", e)
# 출력: 저장: .../expy.png


# %% [markdown]
# ## 정리
#
# | 변수 | 역할 | 통계에서의 의미 |
# |---|---|---|
# | `frontier` | 직전 홉에서 **처음** 발견된 노드 목록 | 다음 홉에 펼칠 대상 |
# | `nxt` | 이번 홉에 처음 발견된 노드 목록 | `len(nxt)` = 이번 홉 새 노드 수 |
# | `seen` | 발견한 노드 전체 집합 | `len(seen)` = 누적 방문 수 |
#
# - 큐 하나로 도는 일반 BFS와 달리, **층 단위 리스트 두 개**(`frontier` → `nxt`)를
#   교대로 쓰기 때문에 거리(홉)를 따로 저장하지 않고도 홉별 집계가 나온다.
# - `seen.add(v)` 를 **큐에 넣는 순간** 하는 것이 중복 카운트를 막는 열쇠다.
# - `if not frontier: break` 는 도달 가능한 성분을 다 덮었을 때의 조기 종료다.
# - 시간 복잡도는 도달 범위 안의 $O(V + E)$. `max_hop` 은 이 범위를 잘라 주는
#   유일한 안전장치이고, 상한이 없으면 사실상 전체 스캔이다.
