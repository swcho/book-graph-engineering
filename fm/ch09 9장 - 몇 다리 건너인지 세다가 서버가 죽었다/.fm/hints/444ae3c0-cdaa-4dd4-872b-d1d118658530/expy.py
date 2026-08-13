# %% [markdown]
# # 평균 차수 12 그래프에서 한 홉은 몇 배인가
#
# 결론부터: **12배가 아니라 약 11배**다.
#
# 어떤 노드에 도착했다는 건 **엣지 하나를 타고 들어왔다**는 뜻이다.
# 그 노드의 차수가 $d$면, 앞으로 뻗을 수 있는 방향은 들어온 엣지를 뺀 $d-1$개다.
#
# $$b = d - 1 = 12 - 1 = 11$$
#
# 여기서 $b$를 **분기 계수(branching factor)** 라고 부른다.
# 홉 $k$에서 새로 만나는 노드 수는
#
# $$|L_k| \approx d \cdot b^{\,k-1} = 12 \cdot 11^{\,k-1}$$
#
# 5홉이면 $12 \cdot 11^4 \approx 175{,}000$. 시작점 대비 **약 1만 4천 배**($11^4$)다.

# %%
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용. 없으면 그 셀만 건너뛰면 된다)

AVG_DEG = 12
B = AVG_DEG - 1  # 분기 계수: 들어온 엣지 하나를 뺀 나머지

print(f"평균 차수 d = {AVG_DEG}, 분기 계수 b = d - 1 = {B}")
print()
print(f"{'홉':>3} {'이번 홉 새 노드(이론)':>22} {'누적':>14} {'직전 홉 대비':>12}")
theory = []
total = 1
prev = 1
for k in range(1, 8):
    new = AVG_DEG * B ** (k - 1)
    total += new
    theory.append((k, new, total))
    print(f"{k:>3} {new:>22,} {total:>14,} {new / prev:>11.1f}x")
    prev = new

print()
print(f"1홉 대비 5홉 배수 = 11^4 = {B**4:,}")
# 출력:
# 평균 차수 d = 12, 분기 계수 b = d - 1 = 11
#
#  홉      이번 홉 새 노드(이론)             누적    직전 홉 대비
#   1                     12             13        12.0x
#   2                    132            145        11.0x
#   3                  1,452          1,597        11.0x
#   4                 15,972         17,569        11.0x
#   5                175,692        193,261        11.0x
#   6              1,932,612      2,125,873        11.0x
#   7             21,258,732     23,384,605        11.0x
#
# 1홉 대비 5홉 배수 = 11^4 = 14,641

# %% [markdown]
# 첫 홉만 12배(시작 노드는 들어온 엣지가 없으니 12방향 전부),
# 그 다음부터는 계속 11배다. 이 11이 지수의 밑이라는 게 핵심이다.
#
# | 밑 | 5홉 | 6홉 |
# |---|---|---|
# | $10$ | 10,000 | 100,000 |
# | $11$ | 14,641 | 161,051 |
# | $12$ | 20,736 | 248,832 |
#
# 밑이 1 달라져도 몇 홉 지나면 배수가 크게 벌어진다.
# 그래서 "12배쯤 되겠지"와 "11배다"는 어림으로도 구분해서 말할 가치가 있다.

# %%
# 실측 — 책의 graph.make 와 같은 방식으로 무작위 그래프를 만들고 BFS 레벨을 센다.
import random
from collections import defaultdict


def make(n=200_000, avg_deg=12, seed=20260801):
    """각 노드가 avg_deg/2 개의 무작위 무방향 엣지를 뿌린다 → 평균 차수 ≈ avg_deg."""
    rnd = random.Random(seed)
    adj = defaultdict(list)
    for a in range(n):
        for _ in range(avg_deg // 2):
            b = rnd.randrange(n)
            if a != b:
                adj[a].append(b)
                adj[b].append(a)
    return {k: sorted(set(v)) for k, v in adj.items()}


def bfs_levels(adj, start, max_hop):
    seen = {start}
    frontier = [start]
    out = []
    for _hop in range(1, max_hop + 1):
        nxt = []
        for u in frontier:
            for v in adj.get(u, ()):
                if v not in seen:
                    seen.add(v)
                    nxt.append(v)
        out.append((_hop, len(nxt), len(seen)))
        frontier = nxt
        if not frontier:
            break
    return out


N = 200_000
adj = make(n=N)
deg = sum(len(v) for v in adj.values()) / len(adj)
print(f"노드 {len(adj):,}  평균 차수 {deg:.1f}\n")

print(f"{'홉':>3} {'새 노드':>12} {'누적':>12} {'배수':>8} {'전체 대비':>10}")
measured = []
prev = 1
for hop, new, total in bfs_levels(adj, 0, 8):
    measured.append((hop, new, total))
    print(f"{hop:>3} {new:>12,} {total:>12,} {new / max(prev, 1):>7.1f}x {total / len(adj) * 100:>9.1f}%")
    prev = new
# 출력:
# 노드 200,000  평균 차수 12.0
#
#  홉          새 노드           누적       배수      전체 대비
#   1           12           13    12.0x       0.0%
#   2          138          151    11.5x       0.1%
#   3        1,600        1,751    11.6x       0.9%
#   4       17,653       19,404    11.0x       9.7%
#   5      117,011      136,415     6.6x      68.2%
#   6       63,582      199,997     0.5x     100.0%
#   7            3      200,000     0.0x     100.0%
#   8            0      200,000     0.0x     100.0%

# %% [markdown]
# 실측에서 읽을 것 두 가지.
#
# **1. 4홉까지는 이론값(11~12배)과 거의 같다.** 무작위 그래프에서 초반 프런티어는
#    아직 그래프 전체에 비해 작아서 중복 도달이 거의 없다.
#
# **2. 5홉부터 배수가 무너진다.** 배수가 갑자기 6.6배, 0.5배로 떨어지는 건
#    "덜 퍼져서"가 아니라 **더 퍼질 곳이 없어서**다. 5홉에 이미 그래프의 68%,
#    6홉에 100%를 먹었다. 지수 성장은 그래프 크기 $N$에서 잘린다.
#
# $$|L_k| \approx \min\left(12 \cdot 11^{\,k-1},\; N - \text{누적}\right)$$
#
# 「여섯 다리 건너면 다 안다」는 말이 바로 이 표다.
# 이야기로는 재밌지만, 질의로 쓰면 **"전체를 훑어라"와 같은 뜻**이 된다.
#
# 그래서 홉 상한 없는 순회는 사실상 전체 스캔이다.
# 서버가 죽은 건 알고리즘이 나빠서가 아니라 **상한이 없어서**다.

# %%
# 시각화 — 이론 곡선 vs 실측, 그리고 누적 커버리지
def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


import plotly.graph_objects as go
from plotly.subplots import make_subplots

hops_t = [k for k, _, _ in theory]
new_t = [n for _, n, _ in theory]
hops_m = [k for k, _, _ in measured]
new_m = [n for _, n, _ in measured]
cov_m = [t / N * 100 for _, _, t in measured]

fig = make_subplots(
    rows=1,
    cols=2,
    subplot_titles=("홉당 새 노드 수 (로그 스케일)", "누적 커버리지 (%)"),
)

fig.add_trace(
    go.Scatter(x=hops_t, y=new_t, mode="lines+markers", name="이론 12·11^(k-1)", line=dict(dash="dash")),
    row=1,
    col=1,
)
fig.add_trace(go.Scatter(x=hops_m, y=new_m, mode="lines+markers", name="실측 (N=200,000)"), row=1, col=1)
fig.add_hline(y=N, line_dash="dot", annotation_text="N = 200,000 (천장)", row=1, col=1)

fig.add_trace(
    go.Bar(x=hops_m, y=cov_m, name="누적 %", marker_color="#c44", showlegend=False),
    row=1,
    col=2,
)

fig.update_yaxes(type="log", title_text="새 노드 수", row=1, col=1)
fig.update_yaxes(range=[0, 105], title_text="전체 대비 %", row=1, col=2)
fig.update_xaxes(title_text="홉", row=1, col=1)
fig.update_xaxes(title_text="홉", row=1, col=2)
fig.update_layout(
    title="평균 차수 12 그래프: 한 홉마다 11배, 그리고 5홉에서 끝난다",
    height=460,
    width=1000,
)

_show(fig)

import pathlib

out = pathlib.Path(__file__).parent / "expy.png" if "__file__" in dir() else pathlib.Path("expy.png")
fig.write_image(str(out))
print(f"저장: {out}")
# 출력: 저장: .../expy.png

# %% [markdown]
# ## 정리
#
# - 평균 차수 $d$ 그래프에서 한 홉의 배수는 $d$가 아니라 **$d-1$**. 들어온 엣지 하나는 되돌아가는 방향이라 뺀다.
# - $d = 12$면 **약 11배**. 5홉이면 $11^4 \approx 14{,}641$배.
# - 이 지수 성장은 $N$에서 잘린다. 그래서 "5홉이면 전체의 68%, 6홉이면 전부"가 된다.
# - 실무 결론: `MATCH (a)-[*]-(b)` 처럼 **홉 상한 없는 가변 길이 패턴은 전체 스캔**이다.
#   상한을 박고, 도착지를 아는 경우엔 양방향 탐색으로 반지름을 절반으로 줄여라 (방문 수가 제곱근이 된다).
