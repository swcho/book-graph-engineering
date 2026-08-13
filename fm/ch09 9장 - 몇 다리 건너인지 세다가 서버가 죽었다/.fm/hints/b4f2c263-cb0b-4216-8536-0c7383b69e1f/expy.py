# %% [markdown]
# # `bidi_path()`는 두 방향 탐색을 어떻게 번갈아 진행하는가
#
# 9장 `ex2_bidirectional.py`의 `bidi_path()`를 뜯어보고, 단방향 BFS와
# **방문 노드 수**를 직접 비교한다.
#
# 핵심 구조는 네 줄로 요약된다.
#
# ```python
# for _ in range(max_hop):                                     # (1) 라운드
#     for q, seen, other in ((fq, fwd, bwd), (bq, bwd, fwd)):  # (2) 방향 교대
#         for _ in range(len(q)):                              # (3) 딱 한 층만
#             ...
#             if v in other:                                   # (4) 만남 판정
#                 return _join(v, fwd, bwd), ...
# ```
#
# - (1) 라운드마다
# - (2) `(정방향 큐, 내 seen, 상대 seen)` → `(역방향 큐, 내 seen, 상대 seen)` 순으로 **교대**하고
# - (3) `len(q)`를 **미리 찍어** 그 개수만큼만 pop 하므로, 이번에 새로 넣은 노드는
#   다음 라운드로 밀린다. 즉 한 번에 정확히 **한 층(one level)** 만 확장한다.
# - (4) 새로 방문한 노드 `v`가 **반대쪽 `seen`** 에 이미 있으면 두 탐색이 만난 것이므로
#   `_join()`으로 앞쪽 절반과 뒤쪽 절반을 이어 붙인다.
#
# 필요 패키지: plotly, kaleido (마지막 시각화 저장용). 나머지는 표준 라이브러리만 사용.

# %%
import random
from collections import defaultdict, deque


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


def make(n=50_000, avg_deg=12, seed=20260801):
    """9장 graph.py 와 같은 방식의 무방향 랜덤 그래프. 시드 고정."""
    rnd = random.Random(seed)
    adj = defaultdict(list)
    for a in range(n):
        for _ in range(avg_deg // 2):
            b = rnd.randrange(n)
            if a != b:
                adj[a].append(b)
                adj[b].append(a)
    return {k: sorted(set(v)) for k, v in adj.items()}


N = 50_000  # 책은 200_000. 여기서는 실행 시간을 위해 줄였다(경향은 같다).
adj = make(n=N)
print(f"노드 {len(adj):,}  평균 차수 {sum(len(v) for v in adj.values()) / len(adj):.1f}")
# 출력: 노드 50,000  평균 차수 12.0

# %% [markdown]
# ## 1. 단방향 BFS — 반지름 $d$ 짜리 공 하나
#
# 평균 차수 $k$ 인 그래프에서 $d$ 홉까지 훑으면 방문 노드는 대략
#
# $$ V_{\text{단방향}} \approx (k-1)^{d} $$
#
# 로 늘어난다. 지수가 그대로 $d$ 다.

# %%
def bfs_path(adj, s, t, max_hop=8):
    """책의 단방향 BFS. (경로, 방문 노드 수)를 돌려준다."""
    if s == t:
        return [s], 1
    seen = {s: None}
    q = deque([(s, 0)])
    while q:
        u, d = q.popleft()
        if d >= max_hop:
            continue
        for v in adj.get(u, ()):
            if v in seen:
                continue
            seen[v] = u
            if v == t:
                path = [v]
                while seen[path[-1]] is not None:
                    path.append(seen[path[-1]])
                return list(reversed(path)), len(seen)
            q.append((v, d + 1))
    return None, len(seen)


# %% [markdown]
# ## 2. 양방향 BFS — 반지름 $d/2$ 짜리 공 두 개
#
# $$ V_{\text{양방향}} \approx 2\,(k-1)^{d/2} = 2\sqrt{V_{\text{단방향}}} $$
#
# 공의 크기가 지수라서 반지름을 절반으로 줄이면 방문 수가 **제곱근**이 된다.
#
# 아래 구현은 책 코드 그대로다. 주석으로 교대 지점을 표시했다.

# %%
def bidi_path(adj, s, t, max_hop=8):
    if s == t:
        return [s], 1
    fwd, bwd = {s: None}, {t: None}      # 각 방향의 seen(= 부모 표). 시작점의 부모는 None
    fq, bq = deque([s]), deque([t])      # 각 방향의 큐
    for _ in range(max_hop):             # ── 라운드
        # ── 한 라운드 안에서 (정방향 → 역방향) 순으로 교대한다
        for q, seen, other in ((fq, fwd, bwd), (bq, bwd, fwd)):
            # len(q)를 미리 고정 → 이번에 새로 넣은 노드는 다음 라운드로 밀린다
            for _ in range(len(q)):      # ── 딱 한 층만 확장
                u = q.popleft()
                for v in adj.get(u, ()):
                    if v in seen:        # 내 쪽에서 이미 본 노드는 건너뛴다
                        continue
                    seen[v] = u          # 내 쪽 부모 기록
                    if v in other:       # ── 반대쪽 seen 에 있으면 «만났다»
                        return _join(v, fwd, bwd), len(fwd) + len(bwd)
                    q.append(v)          # 아니면 다음 층 후보로
    return None, len(fwd) + len(bwd)


def _join(meet, fwd, bwd):
    """만난 노드 meet 를 기준으로 s쪽 절반과 t쪽 절반을 이어 붙인다."""
    left = [meet]
    while fwd[left[-1]] is not None:     # meet → … → s (부모를 거슬러 올라감)
        left.append(fwd[left[-1]])
    right = []
    cur = bwd[meet]
    while cur is not None:               # meet 의 뒤쪽 부모 → … → t
        right.append(cur)
        cur = bwd[cur]
    return list(reversed(left)) + right  # s … meet … t


# %% [markdown]
# `_join()`이 방향과 무관하게 동작하는 이유: 만난 노드 `v`는 **어느 쪽에서 발견되든**
# 그 시점에 `fwd`와 `bwd` 양쪽에 모두 들어 있다. 방금 넣은 쪽이 `seen[v] = u`로 기록했고,
# 반대쪽은 이전 라운드에 이미 기록해 뒀기 때문이다. 그래서 `fwd` 부모를 따라가면 `s`,
# `bwd` 부모를 따라가면 `t`가 나온다.

# %% [markdown]
# ## 3. 한 층씩 교대하는 모습을 직접 찍어 보기
#
# 라운드마다 어느 쪽이 몇 개를 확장했고 각 `seen`이 얼마나 커졌는지 기록한다.
# `bidi_path()`와 로직은 같고 계측만 추가했다.

# %%
def bidi_trace(adj, s, t, max_hop=8):
    """라운드/방향별 확장 기록을 남기는 계측판."""
    log = []
    if s == t:
        return [s], log
    fwd, bwd = {s: None}, {t: None}
    fq, bq = deque([s]), deque([t])
    for rnd_i in range(1, max_hop + 1):
        for name, q, seen, other in (("정방향", fq, fwd, bwd), ("역방향", bq, bwd, fwd)):
            popped = len(q)              # 이번에 확장할 층의 크기(= 프런티어)
            before = len(seen)
            for _ in range(popped):
                u = q.popleft()
                for v in adj.get(u, ()):
                    if v in seen:
                        continue
                    seen[v] = u
                    if v in other:
                        log.append((rnd_i, name, popped, len(seen) - before,
                                    len(fwd), len(bwd), f"만남! v={v}"))
                        return _join(v, fwd, bwd), log
                    q.append(v)
            log.append((rnd_i, name, popped, len(seen) - before,
                        len(fwd), len(bwd), ""))
    return None, log


path, log = bidi_trace(adj, 0, 49_999)
print(f"{'라운드':>4} {'방향':>6} {'확장한 층 크기':>14} {'새 노드':>9} "
      f"{'|fwd|':>8} {'|bwd|':>8}  비고")
for r, name, popped, new, nf, nb, note in log:
    print(f"{r:>4} {name:>6} {popped:>14,} {new:>9,} {nf:>8,} {nb:>8,}  {note}")
print(f"\n경로: {path}  (길이 {len(path) - 1} 홉)")
# 출력:
#  라운드     방향    확장한 층 크기    새 노드    |fwd|    |bwd|  비고
#     1    정방향             1       15       16        1
#     1    역방향             1        9       16       10
#     2    정방향            15      177      193       10
#     2    역방향             9      100      193      110
#     3    정방향           177      478      671      110  만남! v=27561
#
# 경로: [0, 7953, 34623, 27561, 8855, 49999]  (길이 5 홉)

# %% [markdown]
# 읽는 법:
#
# - 라운드 1에서 정방향이 시작점 하나를 펼치고(층 크기 1), 이어서 역방향이 도착점 하나를 펼친다.
#   **한 라운드 = 양쪽 각각 한 층.**
# - `확장한 층 크기`가 그 방향의 프런티어다. 다음 라운드의 층 크기는 직전 라운드에
#   새로 넣은 노드 수와 같다 — `len(q)` 스냅숏이 층을 갈라 주기 때문이다.
# - 3라운드 정방향 도중, 새로 넣은 노드 27561이 `bwd`에 이미 있는 걸 보고 멈춘다.
#   이때 `|fwd| + |bwd| = 671 + 110 = 781`이 총 방문 노드 수다.
# - 정방향 층이 역방향 층보다 큰 건 0번 노드의 차수가 더 커서지, 알고리즘 편향이 아니다.
#
# 만약 `for _ in range(len(q))`가 아니라 `while q` 였다면 한쪽이 큐를 **끝까지** 비우므로
# 교대가 일어나지 않고 사실상 단방향 BFS가 된다. 아래에서 확인한다.

# %%
def bidi_broken(adj, s, t, max_hop=8):
    """일부러 망가뜨린 판: 층 스냅숏 없이 큐를 끝까지 비운다 → 교대가 사라진다."""
    if s == t:
        return [s], 1
    fwd, bwd = {s: None}, {t: None}
    fq, bq = deque([s]), deque([t])
    for _ in range(max_hop):
        for q, seen, other in ((fq, fwd, bwd), (bq, bwd, fwd)):
            while q:                     # ← len(q) 스냅숏이 없다
                u = q.popleft()
                for v in adj.get(u, ()):
                    if v in seen:
                        continue
                    seen[v] = u
                    if v in other:
                        return _join(v, fwd, bwd), len(fwd) + len(bwd)
                    q.append(v)
    return None, len(fwd) + len(bwd)


for s, t in [(0, 49_999), (7, 40_000)]:
    _, v_uni = bfs_path(adj, s, t)
    _, v_bi = bidi_path(adj, s, t)
    _, v_bad = bidi_broken(adj, s, t)
    print(f"{s} → {t}: 단방향 {v_uni:,} / 양방향 {v_bi:,} / 층 스냅숏 없앤 판 {v_bad:,}")
# 출력:
# 0 → 49999: 단방향 41,135 / 양방향 781 / 층 스냅숏 없앤 판 41,136
# 7 → 40000: 단방향 47,915 / 양방향 1,435 / 층 스냅숏 없앤 판 47,916

# %% [markdown]
# `while q` 판은 정방향이 혼자 그래프를 다 훑고 나서야 역방향에 차례가 오므로
# 방문 수가 단방향과 똑같아진다(+1은 `_join`용으로 들고 있는 `bwd = {t: None}` 하나).
# **교대의 단위가 «한 층»이라는 점이 절감의 전부**다.

# %% [markdown]
# ## 4. 방문 노드 수 비교

# %%
PAIRS = [(0, 49_999), (7, 40_000), (42, 24_999), (100, 33_333), (5, 12_345)]
rows = []
for s, t in PAIRS:
    p1, v1 = bfs_path(adj, s, t)
    p2, v2 = bidi_path(adj, s, t)
    rows.append((s, t, v1, v2, v1 / max(v2, 1), len(p1) - 1, len(p2) - 1))

print(f"{'쌍':<18} {'단방향 방문':>12} {'양방향 방문':>12} {'절감':>8} "
      f"{'단방향 길이':>11} {'양방향 길이':>11}")
print("-" * 78)
for s, t, v1, v2, ratio, l1, l2 in rows:
    print(f"{f'{s} → {t}':<18} {v1:>12,} {v2:>12,} {ratio:>7.1f}x {l1:>11} {l2:>11}")
# 출력:
# 쌍                    단방향 방문       양방향 방문       절감    단방향 길이   양방향 길이
# ------------------------------------------------------------------------------
# 0 → 49999                41,135          781    52.7x           5           5
# 7 → 40000                47,915        1,435    33.4x           5           5
# 42 → 24999                3,832          202    19.0x           4           4
# 100 → 33333              25,312          423    59.8x           5           5
# 5 → 12345                 1,907          266     7.2x           4           4

# %% [markdown]
# ## 5. 만나자마자 반환해도 최단이 보장되나
#
# `if v in other: return` 은 만남을 발견하는 **즉시** 돌아온다. 같은 층 뒤쪽에
# 더 짧게 만나지는 노드가 있을 수도 있는데 확인하지 않는 것처럼 보인다.
# 그런데 층을 맞춰 교대하면 보장이 따라온다.
#
# 라운드 $r$ 이 끝나면 `fwd`는 깊이 $0..r$, `bwd`도 깊이 $0..r$ 을 **완전히** 담고 있다.
# 실제 최단 거리를 $D$ 라 하자.
#
# - $D = 2m$: 라운드 $m$ 의 정방향 차례에는 만남이 없다(있었다면 $D \le 2m-1$).
#   이어지는 역방향 차례에서 발견되는 노드 $v$ 는 $d_b(v)=m$ 이고 $d_f(v) \ge D-m = m$,
#   그런데 $d_f(v) \le m$ 이므로 정확히 $m$. 따라서 찾은 길이 $= 2m = D$.
# - $D = 2m+1$: 라운드 $m$ 까지 만남이 없고, 라운드 $m+1$ 정방향에서
#   $d_f(v)=m+1$, $d_b(v) \ge D-(m+1) = m$ 이며 $d_b(v) \le m$ 이므로 정확히 $m$.
#   찾은 길이 $= 2m+1 = D$.
#
# 즉 **첫 만남이 곧 최단**이다. 200쌍으로 확인한다.

# %%
rnd = random.Random(0)
trials, longer = 0, 0
diff_hist = defaultdict(int)
for _ in range(200):
    s, t = rnd.randrange(N), rnd.randrange(N)
    p1, _ = bfs_path(adj, s, t)
    p2, _ = bidi_path(adj, s, t)
    if not p1 or not p2:
        continue
    trials += 1
    d = (len(p2) - 1) - (len(p1) - 1)
    diff_hist[d] += 1
    if d > 0:
        longer += 1
print(f"표본 {trials}쌍 중 양방향 경로가 더 긴 경우: {longer}쌍 ({longer / trials * 100:.0f}%)")
print("길이 차이 분포:", dict(sorted(diff_hist.items())))
# 출력:
# 표본 200쌍 중 양방향 경로가 더 긴 경우: 0쌍 (0%)
# 길이 차이 분포: {0: 200}

# %% [markdown]
# 단, 이 보장은 **층 단위 교대**와 **무방향(또는 대칭) 그래프**를 전제로 한다.
#
# - 층 스냅숏을 빼면(§3의 `bidi_broken`) 보장도 절감도 함께 사라진다.
# - 역방향이 `adj.get(u)`를 그대로 쓰므로 **방향 그래프에서는 틀린다**. 방향 그래프라면
#   역방향 큐는 «들어오는 엣지» 인접 리스트를 따로 써야 한다.
# - 가중치 그래프에서도 이 논증은 깨진다. 그때는 양방향 다익스트라의
#   별도 종료 조건(양쪽 확정 거리 합 ≥ 지금까지의 최선)이 필요하다.
#
# ### 덤: `max_hop` 의 의미가 두 함수에서 다르다
#
# 단방향의 `max_hop`은 **홉 상한**이지만, 양방향의 `max_hop`은 **라운드 수**다.
# 한 라운드에 양쪽이 한 층씩 가므로 실제 탐색 반경은 최대 $2 \times \text{max\_hop}$ 홉이다.
# 같은 값을 넘겨도 커버 범위가 두 배 차이 난다.

# %%
chain = defaultdict(list)                      # 0-1-2-…-39 사슬
for i in range(39):
    chain[i].append(i + 1)
    chain[i + 1].append(i)
chain = dict(chain)

for h in (5, 6, 11, 12):
    p_uni, _ = bfs_path(chain, 0, 12, max_hop=h)
    p_bi, _ = bidi_path(chain, 0, 12, max_hop=h)
    fmt = lambda p: "실패" if p is None else f"{len(p) - 1}홉"  # noqa: E731
    print(f"0→12 (실제 12홉)  max_hop={h:>2}: 단방향 {fmt(p_uni):>4}, 양방향 {fmt(p_bi):>4}")
# 출력:
# 0→12 (실제 12홉)  max_hop= 5: 단방향   실패, 양방향   실패
# 0→12 (실제 12홉)  max_hop= 6: 단방향   실패, 양방향  12홉
# 0→12 (실제 12홉)  max_hop=11: 단방향   실패, 양방향  12홉
# 0→12 (실제 12홉)  max_hop=12: 단방향  12홉, 양방향  12홉

# %% [markdown]
# 12홉짜리 목표를 단방향은 `max_hop=12`가 있어야 찾고, 양방향은 `max_hop=6`이면 찾는다
# ($D = 2m$ 이므로 라운드 $m = 6$ 에서 만난다).
#
# ## 6. 그래프가 클수록 이득이 커진다
#
# $V_{\text{단방향}} \approx (k-1)^d$, $V_{\text{양방향}} \approx 2(k-1)^{d/2}$ 이므로
# 절감 배수는 $\tfrac{1}{2}(k-1)^{d/2}$ — 그래프가 커져 $d$ 가 커질수록 벌어진다.
# 책이 20만 노드에서 75~88배를 본 이유다.

# %%
scale_rows = []
for n in (5_000, 20_000, 50_000, 100_000):
    g = make(n=n)
    tot_uni = tot_bi = 0
    for s, t in ((0, n - 1), (7, n // 2), (42, n // 3)):
        _, a = bfs_path(g, s, t)
        _, b = bidi_path(g, s, t)
        tot_uni += a
        tot_bi += b
    scale_rows.append((n, tot_uni / 3, tot_bi / 3, tot_uni / max(tot_bi, 1)))
    print(f"N={n:>7,}: 단방향 평균 {tot_uni / 3:>10,.0f}  "
          f"양방향 평균 {tot_bi / 3:>8,.0f}  절감 {tot_uni / tot_bi:>6.1f}x")
# 출력:
# N=  5,000: 단방향 평균      2,166  양방향 평균      158  절감   13.7x
# N= 20,000: 단방향 평균     10,300  양방향 평균      309  절감   33.4x
# N= 50,000: 단방향 평균     31,898  양방향 평균      659  절감   48.4x
# N=100,000: 단방향 평균     48,089  양방향 평균      687  절감   70.0x

# %% [markdown]
# ## 7. 시각화

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"   # 검증된 카테고리 팔레트 1·2·3
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e3e2dd"


def bfs_cum(adj, s, max_hop=6):
    """홉별 누적 방문 노드 수."""
    seen, frontier, out = {s}, [s], [1]
    for _ in range(max_hop):
        nxt = []
        for u in frontier:
            for v in adj.get(u, ()):
                if v not in seen:
                    seen.add(v)
                    nxt.append(v)
        out.append(len(seen))
        frontier = nxt
        if not frontier:
            break
    return out


uni_cum = bfs_cum(adj, 0, max_hop=5)
# 양방향: 라운드 r 이면 양쪽이 각각 r층 → 총 2r 홉을 커버하고, 방문은 두 공의 합
fwd_cum, bwd_cum = bfs_cum(adj, 0, 5), bfs_cum(adj, 49_999, 5)
bi_cum = [a + b for a, b in zip(fwd_cum, bwd_cum)]
hops_uni = list(range(len(uni_cum)))
hops_bi = [2 * i for i in range(len(bi_cum))]

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "같은 홉을 커버하는 데 드는 방문 노드 수",
        "쌍별 방문 노드 수 (N=50,000)",
        "라운드별로 확장한 층 크기 (정 → 역 교대)",
        "그래프가 커질수록 벌어지는 절감",
    ),
    vertical_spacing=0.17, horizontal_spacing=0.11,
)

# (1,1) 커버 홉 대비 누적 방문
fig.add_trace(go.Scatter(x=hops_uni, y=uni_cum, name="단방향 BFS", mode="lines+markers",
                         line=dict(color=C1, width=2), marker=dict(size=8, color=C1)),
              row=1, col=1)
fig.add_trace(go.Scatter(x=hops_bi, y=bi_cum, name="양방향 BFS", mode="lines+markers",
                         line=dict(color=C2, width=2), marker=dict(size=8, color=C2)),
              row=1, col=1)

# (1,2) 쌍별 방문 노드 수
labels = [f"{s}→{t}" for s, t, *_ in rows]
fig.add_trace(go.Bar(x=labels, y=[r[2] for r in rows], name="단방향 BFS",
                     marker=dict(color=C1, line=dict(color=SURFACE, width=2)),
                     text=[f"{r[2]:,}" for r in rows], textposition="outside",
                     textfont=dict(color=INK2, size=9), showlegend=False),
              row=1, col=2)
fig.add_trace(go.Bar(x=labels, y=[r[3] for r in rows], name="양방향 BFS",
                     marker=dict(color=C2, line=dict(color=SURFACE, width=2)),
                     text=[f"{r[3]:,}" for r in rows], textposition="outside",
                     textfont=dict(color=INK2, size=9), showlegend=False),
              row=1, col=2)

# (2,1) 라운드별 확장 층 크기
rounds = sorted({r for r, *_ in log})
fwd_sz = [next((p for rr, nm, p, *_ in log if rr == r and nm == "정방향"), 0) for r in rounds]
bwd_sz = [next((p for rr, nm, p, *_ in log if rr == r and nm == "역방향"), 0) for r in rounds]
fig.add_trace(go.Bar(x=[f"{r}라운드" for r in rounds], y=fwd_sz, name="정방향 층",
                     marker=dict(color=C1, line=dict(color=SURFACE, width=2)),
                     text=[f"{v:,}" for v in fwd_sz], textposition="outside",
                     textfont=dict(color=INK2, size=10), showlegend=False), row=2, col=1)
fig.add_trace(go.Bar(x=[f"{r}라운드" for r in rounds], y=bwd_sz, name="역방향 층",
                     marker=dict(color=C3, line=dict(color=SURFACE, width=2)),
                     text=[f"{v:,}" if v else "" for v in bwd_sz],
                     textposition="outside",
                     textfont=dict(color=INK2, size=10), showlegend=False), row=2, col=1)
fig.add_annotation(x=f"{rounds[0]}라운드", y=0.5, xshift=-27, row=2, col=1,
                   text="정방향", showarrow=False, font=dict(color=C1, size=11))
fig.add_annotation(x=f"{rounds[0]}라운드", y=0.5, xshift=27, row=2, col=1,
                   text="역방향", showarrow=False, font=dict(color=C3, size=11))
fig.add_annotation(x=f"{rounds[-1]}라운드", y=0.35, xshift=26, row=2, col=1,
                   text="역방향 차례가<br>오기 전에 만남", showarrow=False, align="left",
                   font=dict(color=INK2, size=10))

# (2,2) 그래프 크기별 방문 노드 수
ns = [f"{n // 1000}K" for n, *_ in scale_rows]
fig.add_trace(go.Bar(x=ns, y=[r[1] for r in scale_rows], name="단방향 BFS",
                     marker=dict(color=C1, line=dict(color=SURFACE, width=2)),
                     showlegend=False), row=2, col=2)
fig.add_trace(go.Bar(x=ns, y=[r[2] for r in scale_rows], name="양방향 BFS",
                     marker=dict(color=C2, line=dict(color=SURFACE, width=2)),
                     text=[f"{r[3]:.0f}배 절감" for r in scale_rows], textposition="outside",
                     textfont=dict(color=INK2, size=10), showlegend=False), row=2, col=2)

fig.update_yaxes(type="log", title_text="누적 방문 노드(로그)", row=1, col=1)
fig.update_xaxes(title_text="커버하는 홉 수", row=1, col=1)
fig.update_yaxes(type="log", title_text="방문 노드(로그)", row=1, col=2)
fig.update_yaxes(type="log", title_text="층 크기(로그)", row=2, col=1)
fig.update_yaxes(type="log", title_text="평균 방문 노드(로그)", row=2, col=2)
fig.update_xaxes(title_text="그래프 노드 수", row=2, col=2)
fig.update_layout(
    title=dict(text="bidi_path(): 한 라운드에 정·역 각각 한 층씩 — 방문 노드가 제곱근으로 준다",
               font=dict(size=17, color=INK)),
    barmode="group", bargap=0.3, bargroupgap=0.08,
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
    font=dict(color=INK2, size=12),
    legend=dict(orientation="h", y=1.10, x=0, font=dict(color=INK2)),
    width=1180, height=800, margin=dict(t=155, l=85, r=40, b=60),
)
fig.update_xaxes(showgrid=False, linecolor=GRID, ticks="outside", tickcolor=GRID)
fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)

_show(fig)

# %%
import os

here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."
out = os.path.join(here, "expy.png")
fig.write_image(out, scale=2)   # kaleido 필요
print("저장:", out)
# 출력: 저장: .../expy.png

# %% [markdown]
# ## 정리
#
# | 질문 | 답 |
# |---|---|
# | 어떻게 번갈아 가나 | 라운드마다 `((fq, fwd, bwd), (bq, bwd, fwd))` 튜플을 순회해 정방향 → 역방향 순으로 확장 |
# | 얼마나 확장하나 | `for _ in range(len(q))` — 큐 길이를 미리 찍어 **딱 한 층**만. 새로 넣은 노드는 다음 라운드 몫 |
# | 만난 걸 어떻게 아나 | 새로 방문한 `v`가 **반대쪽 `seen`(`other`)** 에 이미 있으면 만남 |
# | 만나면 뭘 하나 | `_join(v, fwd, bwd)` — `fwd` 부모를 거슬러 `s`까지, `bwd` 부모를 따라 `t`까지 이어 붙임 |
# | 첫 만남이 최단인가 | 층을 맞춰 교대하는 무방향 BFS라면 그렇다(§5 증명·실측). 층 스냅숏을 빼면 깨진다 |
# | 왜 빠른가 | 반지름 $d$ 공 하나 대신 $d/2$ 공 두 개. $(k-1)^d \to 2(k-1)^{d/2}$, 즉 제곱근 |
# | 못 쓰는 경우 | 도착지를 모를 때. «3다리 안의 사람 전부»는 양방향으로 못 푼다 |
