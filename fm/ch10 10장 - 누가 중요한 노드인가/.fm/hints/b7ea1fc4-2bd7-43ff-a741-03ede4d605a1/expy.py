# %% [markdown]
# # 페이지랭크의 싱크 보정 — 새는 점수를 되돌려 놓기
#
# **질문.** 페이지랭크의 싱크 보정은 어떻게 구현하는가?
#
# **답.** 나가는 엣지가 없는 노드들의 점수 합(`leaked`)을 구해, 감쇠 계수를 곱한 뒤
# 전체 노드에 균등하게 다시 나눠 준다.
#
# 이 노트북은 10장 `ex2_pagerank.py` 의 조직도 데이터(`REPORTS`)로
# 보정 유/무의 **회차별 점수 합계**를 추적하고, 보정식이 왜 합계 $1.0$ 을 회복시키는지
# 수식과 수치로 함께 확인한다.
#
# 한 회차의 갱신식은 이렇다.
#
# $$
# r_{k+1}(v) \;=\; \frac{1-d}{n}
#   \;+\; d \sum_{u \to v} \frac{r_k(u)}{|\mathrm{out}(u)|}
#   \;+\; \underbrace{d \cdot \frac{L_k}{n}}_{\text{싱크 보정}},
# \qquad
# L_k = \sum_{u \in \mathrm{Sink}} r_k(u)
# $$
#
# 여기서 $d$ 는 감쇠 계수(관례적으로 $0.85$), $n$ 은 노드 수,
# $\mathrm{Sink}$ 는 나가는 엣지가 없는 노드 집합이다.

# %%
# 필요 패키지: plotly, kaleido (그래프/PNG 저장), networkx (라이브러리 비교 — 없으면 해당 셀만 건너뜀)
from collections import defaultdict


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


D = 0.85      # 감쇠 계수
TOL = 1e-12

# 10장 org.py 의 REPORTS — «누가 누구에게 결재를 올리는가»
REPORTS = [
    ("개발1", "김개발"), ("개발2", "김개발"), ("개발3", "김개발"),
    ("개발4", "김개발"), ("개발5", "김개발"), ("개발6", "김개발"),
    ("한영업", "정영업"), ("오영업", "정영업"), ("서영업", "정영업"),
    ("윤디자", "강디자"), ("임디자", "강디자"),
    ("김개발", "대표"), ("정영업", "대표"), ("강디자", "대표"),
    ("공장A", "서영업"), ("공장B", "공장A"), ("공장C", "공장A"),
    ("청소담당", "총무"), ("총무", "대표"),
]

NODES = sorted({x for a, b in REPORTS for x in (a, b)})
OUT = defaultdict(list)
for _a, _b in REPORTS:
    OUT[_a].append(_b)
SINKS = [v for v in NODES if not OUT[v]]

print(f"노드 수 n = {len(NODES)}")
print(f"싱크(나가는 엣지 없음) = {SINKS}")
# 출력: 노드 수 n = 20
# 출력: 싱크(나가는 엣지 없음) = ['대표']

# %% [markdown]
# 결재선을 따라 올라가면 결국 모두 `대표` 에서 멈춘다. `대표` 는 점수를 **받기만 하고
# 아무에게도 흘려보내지 않는다**. 이 노드가 들고 있는 점수 $L_k$ 가 매 회차마다
# 그래프 밖으로 새는 몫이다.

# %%
def pagerank(edges, damping=D, fix_sinks=True, rounds=200, self_loop_sinks=False):
    """보정 유/무를 켜고 끌 수 있는 페이지랭크. 회차별 합계 history 를 함께 돌려준다."""
    nodes = sorted({x for a, b in edges for x in (a, b)})
    out = defaultdict(list)
    for a, b in edges:
        out[a].append(b)
    if self_loop_sinks:                      # 대안 1: 싱크에 자기 자신으로 가는 엣지
        for v in nodes:
            if not out[v]:
                out[v].append(v)

    n = len(nodes)
    rank = {v: 1 / n for v in nodes}
    sinks = [v for v in nodes if not out[v]]
    history = [sum(rank.values())]           # 0회차(초기값) 합계 = 1.0

    for it in range(rounds):
        nxt = {v: (1 - damping) / n for v in nodes}
        leaked = sum(rank[v] for v in sinks) if fix_sinks else 0.0
        for v in nodes:
            if out[v]:
                share = damping * rank[v] / len(out[v])
                for w in out[v]:
                    nxt[w] += share
        if fix_sinks:
            for v in nodes:                  # 감쇠 계수를 곱해 전체에 «균등» 재분배
                nxt[v] += damping * leaked / n
        diff = sum(abs(nxt[v] - rank[v]) for v in nodes)
        rank = nxt
        history.append(sum(rank.values()))
        if diff < TOL:
            break
    return rank, it + 1, history


rank_fix, it_fix, hist_fix = pagerank(REPORTS, fix_sinks=True)
rank_raw, it_raw, hist_raw = pagerank(REPORTS, fix_sinks=False)

print(f"[보정 함]     반복 {it_fix:>2}회  합계 {sum(rank_fix.values()):.6f}")
print(f"[보정 안 함]  반복 {it_raw:>2}회  합계 {sum(rank_raw.values()):.6f}")
# 출력: [보정 함]     반복 68회  합계 1.000000
# 출력: [보정 안 함]  반복  6회  합계 0.374054

# %%
# 회차별 합계 추적 — 보정이 없으면 매 회 조금씩 새고, 있으면 1.0 을 유지한다
print(f"{'회차':>4} {'보정 함':>12} {'보정 안 함':>12} {'새는 몫 L_k':>12}")
print("-" * 44)
_r = {v: 1 / len(NODES) for v in NODES}
for k in range(0, 13):
    leak_k = sum(_r[v] for v in SINKS)
    fx = hist_fix[k] if k < len(hist_fix) else hist_fix[-1]
    rw = hist_raw[k] if k < len(hist_raw) else hist_raw[-1]
    print(f"{k:>4} {fx:>12.6f} {rw:>12.6f} {leak_k:>12.6f}")
    _nxt = {v: (1 - D) / len(NODES) for v in NODES}
    for v in NODES:
        if OUT[v]:
            s = D * _r[v] / len(OUT[v])
            for w in OUT[v]:
                _nxt[w] += s
    _r = _nxt
# 출력:   회차         보정 함       보정 안 함     새는 몫 L_k
# 출력: --------------------------------------------
# 출력:    0     1.000000     1.000000     0.050000
# 출력:    1     1.000000     0.957500     0.177500
# 출력:    2     1.000000     0.813000     0.466500
# 출력:    3     1.000000     0.444525     0.128731
# 출력:    4     1.000000     0.418425     0.154832
# 출력:    5     1.000000     0.374054     0.110461
# 출력:    6     1.000000     0.374054     0.110461
# 출력:    7     1.000000     0.374054     0.110461
# 출력:    8     1.000000     0.374054     0.110461
# 출력:    9     1.000000     0.374054     0.110461
# 출력:   10     1.000000     0.374054     0.110461
# 출력:   11     1.000000     0.374054     0.110461
# 출력:   12     1.000000     0.374054     0.110461
#
# 결재선이 «대표»까지 5단계라 6회차에서 이미 고정점에 닿는다. 보정을 안 하면
# 합계가 0으로 사라지는 게 아니라 «1보다 작은 다른 값(0.374)에 눌러앉는다».
# 0.0100 이상만 추천 같은 절대 임계를 쓰고 있었다면 그 임계의 의미가 이때 무너진다.

# %% [markdown]
# ## 왜 보정식이 합계 $1.0$ 을 회복시키는가
#
# 한 회차의 **합계**만 따로 더해 보면 유도가 끝난다. $S_k = \sum_v r_k(v)$ 라 두자.
#
# **보정이 없을 때.** 각 노드 $u$ 는 자기 점수의 $d$ 배를 이웃에게 나눠 준다.
# 다만 싱크는 나눠 줄 상대가 없으므로 그 몫 $d\,r_k(u)$ 가 통째로 사라진다.
#
# $$
# S_{k+1} \;=\; \underbrace{n \cdot \frac{1-d}{n}}_{= \,1-d}
#   \;+\; d\,(S_k - L_k)
# $$
#
# 싱크가 있어 $L_k > 0$ 인 한 $S_{k+1} < 1-d+d\,S_k$ 이고, $S_0 = 1$ 에서 출발해도
# 매 회차 $1$ 아래로 밀려난다. 다만 **0으로 사라지지는 않는다** — 텔레포트 항이 매 회
# $1-d$ 를 새로 넣어 주므로, 합계는 $1$ 보다 작은 어떤 고정점(이 데이터에서는 $0.374$)에 눌러앉는다.
# ($L_k \equiv 0$ 인 그래프에서는 $S_{k+1}=1-d+d\,S_k$ 라서 $S_0=1$ 이면 $S_k \equiv 1$ 로 그대로 보존된다.)
#
# **보정을 넣으면.** 사라진 $d\,L_k$ 를 $n$ 등분해 $n$ 개 노드에 도로 얹으므로
# 정확히 $n \times \dfrac{d\,L_k}{n} = d\,L_k$ 가 되돌아온다.
#
# $$
# S_{k+1} \;=\; (1-d) \;+\; d\,(S_k - L_k) \;+\; d\,L_k \;=\; (1-d) + d\,S_k
# $$
#
# $S_0 = 1$ 이면 $S_1 = (1-d) + d = 1$ 이고, 귀납적으로 모든 회차에서 $S_k = 1$ 이다.
# 초기값이 1이 아니어도 $S_k \to 1$ 로 수렴한다 ($|d| < 1$ 인 축약 사상).
#
# 핵심은 **감쇠 계수 $d$ 를 곱한다**는 점이다. 싱크가 잃은 것은 원래 점수 $L_k$ 가 아니라
# 「$d$ 를 곱해 흘려보냈어야 할 몫」 $d\,L_k$ 뿐이다. 나머지 $(1-d)L_k$ 는 이미
# 텔레포트 항 $(1-d)/n$ 이 담당한다. 그래서 $d$ 를 빼먹고 $L_k/n$ 을 그냥 더하면
# 이번에는 합계가 $1$ 을 **넘어간다**.

# %%
# 위 유도를 수치로 확인 — S_{k+1} = (1-d) + d*(S_k - L_k) [+ d*L_k]
S, r = 1.0, {v: 1 / len(NODES) for v in NODES}
print(f"{'k':>3} {'예측 S_(k+1)':>14} {'실측 S_(k+1)':>14}")
for k in range(6):
    L = sum(r[v] for v in SINKS)
    pred = (1 - D) + D * (S - L)             # 보정 없는 경우의 예측
    nxt = {v: (1 - D) / len(NODES) for v in NODES}
    for v in NODES:
        if OUT[v]:
            s = D * r[v] / len(OUT[v])
            for w in OUT[v]:
                nxt[w] += s
    r, S = nxt, sum(nxt.values())
    print(f"{k:>3} {pred:>14.9f} {S:>14.9f}")

# d 를 빼먹고 L/n 을 그대로 더하면? — 합계가 1을 넘는다
r2 = {v: 1 / len(NODES) for v in NODES}
for _ in range(30):
    L = sum(r2[v] for v in SINKS)
    nxt = {v: (1 - D) / len(NODES) + L / len(NODES) for v in NODES}   # d 누락!
    for v in NODES:
        if OUT[v]:
            s = D * r2[v] / len(OUT[v])
            for w in OUT[v]:
                nxt[w] += s
    r2 = nxt
print(f"\nd 를 빼먹은 «보정»의 합계: {sum(r2.values()):.6f}  (1.0 이 아니다)")
# 출력:   k     예측 S_(k+1)     실측 S_(k+1)
# 출력:   0    0.957500000    0.957500000
# 출력:   1    0.813000000    0.813000000
# 출력:   2    0.444525000    0.444525000
# 출력:   3    0.418424688    0.418424688
# 출력:   4    0.374054156    0.374054156
# 출력:   5    0.374054156    0.374054156
# 출력:
# 출력: d 를 빼먹은 «보정»의 합계: 1.400589  (1.0 이 아니다)
#
# 예측과 실측이 소수점 9자리까지 같다 → 합계의 재귀식 유도가 맞다.

# %% [markdown]
# ## 대안 비교 (1) — 싱크에 자기 자신으로 가는 엣지를 넣기
#
# "싱크가 문제라면 싱크를 없애 버리자"는 발상. `대표 → 대표` 자기 루프를 넣으면
# 나가는 엣지가 생기므로 합계는 **보존된다**. 구현도 한 줄이다.
#
# 하지만 이건 **다른 마르코프 연쇄**다. 자기 루프는 흘려보낸 점수를 전부 자기가 도로 받으므로,
# 싱크가 점수를 계속 쌓는다(흡수벽에 가깝다). 균등 재분배는 「막다른 길에 도달하면
# 아무 페이지로나 점프한다」는 원래 랜덤 서퍼 모형을 지키지만, 자기 루프는
# 「막다른 길에서 새로고침을 무한히 누른다」에 해당한다. 순위는 **왜곡된다**.

# %%
rank_loop, it_loop, hist_loop = pagerank(REPORTS, self_loop_sinks=True, fix_sinks=True)

def top(rank, k=5):
    return [(v, rank[v]) for v in sorted(rank, key=lambda x: -rank[x])[:k]]

print(f"{'노드':<8} {'보정(균등)':>12} {'자기 루프':>12} {'보정 없음':>12}")
print("-" * 48)
for v in sorted(rank_fix, key=lambda x: -rank_fix[x])[:6]:
    print(f"{v:<8} {rank_fix[v]:>12.4f} {rank_loop[v]:>12.4f} {rank_raw[v]:>12.4f}")
print(f"\n합계     {sum(rank_fix.values()):>12.4f} {sum(rank_loop.values()):>12.4f} "
      f"{sum(rank_raw.values()):>12.4f}")
print(f"대표 몫  {rank_fix['대표']:>12.4f} {rank_loop['대표']:>12.4f} {rank_raw['대표']:>12.4f}")
# 출력: 노드             보정(균등)        자기 루프        보정 없음
# 출력: ------------------------------------------------
# 출력: 대표             0.2953       0.7364       0.1105
# 출력: 김개발            0.1223       0.0458       0.0458
# 출력: 정영업            0.1103       0.0413       0.0413
# 출력: 서영업            0.0661       0.0247       0.0247
# 출력: 강디자            0.0541       0.0203       0.0203
# 출력: 공장A            0.0541       0.0203       0.0203
# 출력:
# 출력: 합계           1.0000       1.0000       0.3741
# 출력: 대표 몫        0.2953       0.7364       0.1105

# %% [markdown]
# 자기 루프를 넣으면 `대표` 혼자 전체 점수의 **73.6%** 를 가져간다(균등 재분배에서는 29.5%).
# 합계는 $1.0$ 이 맞지만 **「가장 중요한 노드」의 크기가 두 배 넘게 부풀었다**.
# 합계만 보고 "고쳤다"고 판단하면 안 된다는 뜻이다.
#
# 더 눈여겨볼 것은 **자기 루프 열과 보정 없음 열의 비싱크 값이 완전히 같다**는 점이다
# (`김개발` 0.0458 = 0.0458). 자기 루프는 싱크가 흘려보낸 점수를 **싱크 자신에게만** 돌려주므로
# 나머지 노드의 갱신식이 보정 없는 경우와 글자 그대로 동일하다. 즉 자기 루프는
# 「새는 점수를 되돌린」 게 아니라 「새는 점수를 싱크 안에 가둔」 것이다.
# 순위표만 보면 티가 안 난다 — 10장의 「순위는 안 바뀌어서 발견이 늦는다」가 이 얘기다.
#
# ## 대안 비교 (2) — 싱크에서 모든 노드로 가는 엣지를 실제로 그리기
#
# 원논문의 원래 처방은 **싱크에서 전체 노드로 향하는 가상의 엣지 $n$ 개**를 놓는 것이다.
# 그러면 싱크가 흘려보내는 $d\,r_k(u)$ 가 $n$ 등분되어 모두에게 $d\,r_k(u)/n$ 씩 간다.
# 이는 우리가 쓴 `damping * leaked / n` 과 **수학적으로 완전히 동일하다**.
# 즉 `leaked` 보정은 그 $O(n)$ 개 가상 엣지를 만들지 않고 **한 줄로 접은 최적화**다.

# %%
EXPANDED = list(REPORTS) + [(s, v) for s in SINKS for v in NODES]   # 싱크 → 전 노드
rank_exp, _, _ = pagerank(EXPANDED, fix_sinks=False)                # 이제 싱크가 없다

maxdiff = max(abs(rank_exp[v] - rank_fix[v]) for v in NODES)
print(f"«싱크→전 노드 엣지» 결과와 «leaked 보정» 결과의 최대 차이: {maxdiff:.3e}")
print(f"엣지 수: {len(REPORTS)} → {len(EXPANDED)}  (n={len(NODES)} 개가 추가됨)")
# 출력: «싱크→전 노드 엣지» 결과와 «leaked 보정» 결과의 최대 차이: 5.551e-17
# 출력: 엣지 수: 19 → 39  (n=20 개가 추가됨)

# %% [markdown]
# ## 대안 비교 (3) — `networkx.pagerank` 의 dangling 처리
#
# `nx.pagerank` 는 이 보정을 **기본으로 켜 놓는다**. 핵심 루프는 사실상 이렇다.
#
# ```python
# danglesum = alpha * sum(xlast[n] for n in dangling_nodes)   # = d * leaked
# for n in x:
#     for _, nbr, wt in W.edges(n, data=weight):
#         x[nbr] += alpha * xlast[n] * wt
#     x[n] += danglesum * dangling_weights.get(n, 0) + (1.0 - alpha) * p.get(n, 0)
# ```
#
# - `dangling_nodes` = 가중 출차수가 $0$ 인 노드 = 우리의 `sinks`
# - `danglesum = alpha * sum(...)` = 우리의 `damping * leaked`
# - `dangling_weights` 는 기본값이 개인화 벡터 `p`, 그 `p` 의 기본값이 균등 $1/n$
#   → 결국 `danglesum / n`, 우리 식과 **한 글자도 다르지 않다**
#
# 다른 점은 **분배 비율을 바꿀 수 있다**는 것뿐이다. `dangling=` 인자에 딕셔너리를 주면
# 「막다른 길에 빠졌을 때 어디로 점프하는가」를 균등이 아닌 임의 분포로 지정할 수 있다.
# (`personalization=` 을 주면 `dangling` 기본값도 그 분포를 따라간다.)

# %%
try:
    import networkx as nx

    G = nx.DiGraph()
    G.add_nodes_from(NODES)
    G.add_edges_from(REPORTS)
    nx_rank = nx.pagerank(G, alpha=D, tol=1e-14, max_iter=500)

    diff = max(abs(nx_rank[v] - rank_fix[v]) for v in NODES)
    print(f"networkx 결과 합계: {sum(nx_rank.values()):.6f}")
    print(f"직접 구현(leaked 보정)과의 최대 차이: {diff:.3e}")

    # dangling 분배를 «대표에게만» 몰아주면 자기 루프와 같아진다
    dang = {v: (1.0 if v == "대표" else 0.0) for v in NODES}
    nx_loop = nx.pagerank(G, alpha=D, dangling=dang, tol=1e-14, max_iter=500)
    print(f"dangling=대표 100% 일 때 대표 점수: {nx_loop['대표']:.4f} "
          f"(자기 루프 구현: {rank_loop['대표']:.4f})")
except ImportError:
    print("networkx 없음 — 이 셀은 건너뜀 (pip install networkx)")
# 출력: networkx 결과 합계: 1.000000
# 출력: 직접 구현(leaked 보정)과의 최대 차이: 1.881e-13
# 출력: dangling=대표 100% 일 때 대표 점수: 0.7364 (자기 루프 구현: 0.7364)
# (networkx 3.2.1 에서 확인)

# %% [markdown]
# `dangling` 을 「싱크 자신에게 100%」로 주면 자기 루프 구현과 소수점 넷째 자리까지 같다.
# 즉 자기 루프는 **dangling 분배를 싱크에 몰아준 특수 경우**로 볼 수 있다.
# 균등 재분배(기본값)와 자기 루프는 같은 틀 안의 서로 다른 선택지지, 「맞고 틀림」이 아니다.
# 다만 페이지랭크의 원래 의미(랜덤 서퍼)에 맞는 기본값은 균등 쪽이다.
#
# ## 시각화 — 회차별 점수 합계

# %%
try:
    import plotly.graph_objects as go

    ks = list(range(0, 21))

    def pad(h):
        return [h[k] if k < len(h) else h[-1] for k in ks]

    # 보정 함/자기 루프는 둘 다 정확히 1.0 위에 겹친다 → 선 굵기·점선으로 분리해 둘 다 보이게
    series = [
        ("싱크 보정 (균등 재분배)", pad(hist_fix), "#2a78d6", "solid", 4, 22),
        ("자기 루프 대안", pad(hist_loop), "#eb6834", "dot", 2, -2),
        ("보정 없음 (새는 점수)", pad(hist_raw), "#1baf7a", "solid", 2, 0),
    ]

    fig = go.Figure()
    for name, ys, color, dash, width, yshift in series:
        fig.add_trace(go.Scatter(
            x=ks, y=ys, name=name, mode="lines",
            line=dict(color=color, width=width, dash=dash),
            hovertemplate="%{y:.4f}<extra>" + name + "</extra>",
        ))
        fig.add_annotation(                     # 직접 라벨 (색만으로 구분하지 않도록)
            x=ks[-1], y=ys[-1], text=f"  {name.split(' (')[0]} {ys[-1]:.3f}",
            showarrow=False, xanchor="left", yshift=yshift,
            font=dict(size=11, color="#52514e"),
        )

    fig.update_layout(
        title="페이지랭크 회차별 점수 합계 — 싱크 보정 유/무",
        xaxis_title="반복 회차 k", yaxis_title="점수 합계 S_k",
        template="plotly_white", width=980, height=460,
        margin=dict(l=70, r=250, t=70, b=60),
        paper_bgcolor="#fcfcfb", plot_bgcolor="#fcfcfb",
        font=dict(color="#0b0b0b"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.24, x=0),
        hovermode="x unified",
    )
    fig.update_yaxes(range=[0, 1.12], gridcolor="#e6e5e0", zeroline=False)
    fig.update_xaxes(gridcolor="#e6e5e0", zeroline=False, dtick=2)

    _show(fig)
    import os
    fig.write_image(os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png"),
                    scale=2)
    print("expy.png 저장 완료")
except ImportError as e:
    print(f"plotly/kaleido 없음 — 시각화 건너뜀 ({e})")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# | 방식 | 합계 | 구현 비용 | 의미 |
# |---|---|---|---|
# | 보정 없음 | $<1$, 계속 감소 | — | 절대 임계가 조용히 망가진다 |
# | **`leaked` 균등 재분배** | $1.0$ | $O(n)$ 한 줄 | 랜덤 서퍼 모형 그대로. 표준 |
# | 싱크 → 전 노드 엣지 | $1.0$ | 엣지 $+O(n\cdot|\mathrm{Sink}|)$ | 위와 수학적으로 동일, 비쌈 |
# | 싱크에 자기 루프 | $1.0$ | 한 줄 | **다른 모형**. 싱크가 점수를 쌓음 |
# | `nx.pagerank` 기본값 | $1.0$ | 무료 | `leaked` 균등 재분배와 동일 |
#
# 라이브러리를 쓸 때 확인할 것은 두 가지다.
# **(1)** dangling 보정을 하는가, **(2)** 한다면 어느 분포로 되돌리는가.
