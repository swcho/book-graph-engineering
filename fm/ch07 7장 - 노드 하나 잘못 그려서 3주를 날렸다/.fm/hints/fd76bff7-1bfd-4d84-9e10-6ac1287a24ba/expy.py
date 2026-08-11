# %% [markdown]
# # 단순 그래프 차수 vs 다중 그래프 차수
#
# 같은 엣지 목록을 두 가지로 세면 답이 달라진다.
#
# - **단순 그래프 차수**: 같은 쌍 $(u,v)$ 는 몇 번 나와도 **하나**로 센다 → 「거래처 수」
# - **다중 그래프 차수**: **엣지마다** 센다 → 「거래 건수」
# - **자기 루프**: 다중 그래프에서는 관례상 **2**로 센다 (엣지 양쪽 끝이 모두 그 노드에 붙으므로)
#
# 무향 그래프에서 차수는
#
# $$\deg(v) = \bigl|\{\,e \in E : v \in e\,\}\bigr| + \bigl|\{\,e \in E : e = (v,v)\,\}\bigr|$$
#
# 즉 자기 루프는 한 번 더 더해져서 2가 된다.
#
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용. 없으면 그 셀만 건너뛰면 된다)

# %%
# 시각화 헬퍼 — VSCode 셀/Jupyter 에서만 렌더링한다.
# 평범한 python3 실행에서는 plotly 기본 renderer 가 브라우저를 열기 때문.
def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1단계 — 데이터: 같은 쌍에 계약이 여러 번, 그리고 자기 루프 하나

# %%
from collections import Counter, defaultdict

EDGES = [
    ("가온테크", "나루소프트", "C-2023-011"),
    ("가온테크", "나루소프트", "C-2024-088"),
    ("가온테크", "나루소프트", "C-2025-118"),
    ("가온테크", "다올물산", "C-2025-200"),
    ("라온에너지", "라온에너지", "C-2025-301"),  # 자기 루프
]

for e in EDGES:
    print(e)
print("엣지 개수:", len(EDGES))
# 출력: ('가온테크', '나루소프트', 'C-2023-011')
# 출력: ('가온테크', '나루소프트', 'C-2024-088')
# 출력: ('가온테크', '나루소프트', 'C-2025-118')
# 출력: ('가온테크', '다올물산', 'C-2025-200')
# 출력: ('라온에너지', '라온에너지', 'C-2025-301')
# 출력: 엣지 개수: 5

# %% [markdown]
# ## 2단계 — 단순 그래프로 세기
#
# 같은 쌍을 집합(`set`)에 넣어 **중복을 없앤다**. 자기 루프는 아예 버린다
# (단순 그래프의 정의상 $(v,v)$ 엣지가 존재할 수 없다).

# %%
def degree_simple(edges):
    """단순 그래프: 같은 쌍은 하나로, 자기 루프는 제외."""
    pairs = {(min(a, b), max(a, b)) for a, b, _ in edges if a != b}
    deg = Counter()
    for a, b in pairs:
        deg[a] += 1
        deg[b] += 1
    return deg, pairs


deg_s, pairs = degree_simple(EDGES)
print("중복 제거된 쌍:", sorted(pairs))
print("차수:", dict(sorted(deg_s.items())))
# 출력: 중복 제거된 쌍: [('가온테크', '나루소프트'), ('가온테크', '다올물산')]
# 출력: 차수: {'가온테크': 2, '나루소프트': 1, '다올물산': 1}

# %% [markdown]
# 계약이 3번이든 30번이든 「나루소프트」는 1로만 센다. 자기 루프뿐인 「라온에너지」는
# 아예 표에서 사라진다(차수 0).

# %% [markdown]
# ## 3단계 — 다중 그래프로 세기
#
# 엣지를 하나씩 훑으면서 양 끝에 1을 더한다. 단, **자기 루프는 같은 노드에 2를 더한다**.

# %%
def degree_multi(edges, loop_weight=2):
    """다중 그래프: 엣지마다 센다. 자기 루프는 관례상 2."""
    deg = Counter()
    for a, b, _ in edges:
        if a == b:
            deg[a] += loop_weight
        else:
            deg[a] += 1
            deg[b] += 1
    return deg


deg_m = degree_multi(EDGES)
print("차수:", dict(sorted(deg_m.items())))
# 출력: 차수: {'가온테크': 4, '나루소프트': 3, '다올물산': 1, '라온에너지': 2}

# %% [markdown]
# ## 4단계 — 나란히 놓고 보기

# %%
nodes = sorted(set(deg_s) | set(deg_m))
print(f"{'노드':<10}{'단순':>8}{'다중':>8}")
for n in nodes:
    print(f"{n:<10}{deg_s.get(n, 0):>8}{deg_m.get(n, 0):>8}")
# 출력: 노드            단순      다중
# 출력: 가온테크           2       4
# 출력: 나루소프트          1       3
# 출력: 다올물산           1       1
# 출력: 라온에너지          0       2

# %% [markdown]
# 「가온테크의 차수는?」 → **2도 맞고 4도 맞다.** 무엇을 세는지가 다를 뿐이다.
#
# - 거래처 수를 알고 싶으면 → 단순 그래프 (2곳: 나루소프트, 다올물산)
# - 거래 건수를 알고 싶으면 → 다중 그래프 (4건)
#
# 사고는 섞을 때 난다. 중심성을 다중 그래프로 계산해 놓고 「거래처가 많은 회사」라고
# 보고하면 틀린다. 같은 곳과 계약을 여러 번 한 회사가 1등이 되어 버린다.

# %% [markdown]
# ## 5단계 — 왜 자기 루프가 2인가: 악수 정리(handshaking lemma)
#
# 무향 그래프에서 차수 합은 항상 엣지 수의 2배다.
#
# $$\sum_{v \in V} \deg(v) = 2\,|E|$$
#
# 자기 루프를 1로 세면 이 등식이 깨진다. 2로 세야 유지된다.

# %%
for w in (2, 1):
    total = sum(degree_multi(EDGES, loop_weight=w).values())
    print(f"자기 루프를 {w}로 셀 때  차수 합={total}, 2|E|={2 * len(EDGES)}, 일치={total == 2 * len(EDGES)}")
# 출력: 자기 루프를 2로 셀 때  차수 합=10, 2|E|=10, 일치=True
# 출력: 자기 루프를 1로 셀 때  차수 합=9, 2|E|=10, 일치=False

# %% [markdown]
# 그래서 「관례」는 그냥 관례가 아니다. 2로 세야 정리가 성립한다.
# 다만 라이브러리·알고리즘에 따라 1로 세거나 아예 무시하기도 한다.
# 라이브러리를 바꾸면 숫자가 **조용히** 달라지니, 자기 루프는 미리 걸러 두는 편이 낫다.

# %% [markdown]
# ## 6단계 — 방향이 있으면 in/out 으로 갈린다 (덤)
#
# 유향 다중 그래프에서는 $\deg(v) = \deg^{-}(v) + \deg^{+}(v)$ 이고,
# 자기 루프는 in 과 out 에 각각 1씩 들어가므로 합치면 자연히 2가 된다.

# %%
indeg, outdeg = Counter(), Counter()
for a, b, _ in EDGES:
    outdeg[a] += 1
    indeg[b] += 1

print(f"{'노드':<10}{'in':>6}{'out':>6}{'합':>6}")
for n in nodes:
    print(f"{n:<10}{indeg.get(n, 0):>6}{outdeg.get(n, 0):>6}{indeg.get(n, 0) + outdeg.get(n, 0):>6}")
# 출력: 노드         in   out     합
# 출력: 가온테크        0     4     4
# 출력: 나루소프트       3     0     3
# 출력: 다올물산        1     0     1
# 출력: 라온에너지       1     1     2

# %% [markdown]
# ## 7단계 — 시각화
#
# 왼쪽은 실제 그래프 모양(같은 쌍 사이의 3중 엣지, 자기 루프),
# 오른쪽은 두 방식의 차수 비교.

# %%
import math
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots

POS = {
    "가온테크": (0.0, 0.0),
    "나루소프트": (2.0, 0.9),
    "다올물산": (2.0, -0.9),
    "라온에너지": (-1.6, -0.7),
}

KO_FONT = "Apple SD Gothic Neo, AppleGothic, Noto Sans KR, sans-serif"
fig = make_subplots(
    rows=1,
    cols=2,
    column_widths=[0.52, 0.48],
    subplot_titles=("엣지 구조 (다중 엣지 3개 + 자기 루프)", "차수: 단순 vs 다중"),
)


def bezier(p0, p1, bulge, n=40):
    """두 점을 잇는 2차 베지어. bulge 로 휘는 정도를 준다."""
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1.0
    cx, cy = mx - dy / L * bulge, my + dx / L * bulge
    ts = [i / n for i in range(n + 1)]
    xs = [(1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * cx + t**2 * p1[0] for t in ts]
    ys = [(1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * cy + t**2 * p1[1] for t in ts]
    return xs, ys


# 같은 쌍이 몇 번 나오는지 세서, 겹치는 엣지를 서로 다른 곡률로 벌린다.
mult = defaultdict(int)
for a, b, _ in EDGES:
    mult[(a, b)] += 1

drawn = defaultdict(int)
for a, b, cid in EDGES:
    k = mult[(a, b)]
    i = drawn[(a, b)]
    drawn[(a, b)] += 1
    if a == b:  # 자기 루프는 작은 원으로
        x0, y0 = POS[a]
        r = 0.34
        xs = [x0 + r * math.cos(t / 30 * 2 * math.pi) for t in range(31)]
        ys = [y0 + r + r * math.sin(t / 30 * 2 * math.pi) for t in range(31)]
        color = "#d1495b"
    else:
        bulge = 0.0 if k == 1 else (i - (k - 1) / 2) * 0.45
        xs, ys = bezier(POS[a], POS[b], bulge)
        color = "#3d5a80"
    fig.add_trace(
        go.Scatter(
            x=xs, y=ys, mode="lines", line=dict(color=color, width=2.2),
            hoverinfo="text", text=f"{a} — {b} · {cid}", showlegend=False,
        ),
        row=1, col=1,
    )

fig.add_trace(
    go.Scatter(
        x=[POS[n][0] for n in POS],
        y=[POS[n][1] for n in POS],
        mode="markers+text",
        marker=dict(size=34, color="#f0f3f8", line=dict(color="#3d5a80", width=2)),
        text=list(POS),
        textposition="bottom center",
        textfont=dict(size=12),
        hovertext=[f"{n}<br>단순 {deg_s.get(n, 0)} / 다중 {deg_m.get(n, 0)}" for n in POS],
        hoverinfo="text",
        showlegend=False,
    ),
    row=1, col=1,
)

fig.add_trace(
    go.Bar(x=nodes, y=[deg_s.get(n, 0) for n in nodes], name="단순 그래프 차수",
           marker_color="#8fb8d8", text=[deg_s.get(n, 0) for n in nodes], textposition="outside"),
    row=1, col=2,
)
fig.add_trace(
    go.Bar(x=nodes, y=[deg_m.get(n, 0) for n in nodes], name="다중 그래프 차수",
           marker_color="#d1495b", text=[deg_m.get(n, 0) for n in nodes], textposition="outside"),
    row=1, col=2,
)

fig.update_xaxes(visible=False, row=1, col=1)
fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1, row=1, col=1)
fig.update_yaxes(title_text="차수", range=[0, 5], row=1, col=2)
fig.update_layout(
    title="같은 엣지 목록, 두 가지 차수 (자기 루프는 다중 그래프에서 2)",
    font=dict(family=KO_FONT, size=13),
    barmode="group",
    template="plotly_white",
    width=1000,
    height=460,
    legend=dict(orientation="h", y=-0.14, x=0.55),
)

_show(fig)

out = Path(__file__).parent / "expy.png" if "__file__" in dir() else Path("expy.png")
fig.write_image(str(out), scale=2)
print("saved:", out)
# 출력: saved: .../expy.png

# %% [markdown]
# ## 정리
#
# | | 같은 쌍 | 자기 루프 | 답하는 질문 |
# |---|---|---|---|
# | 단순 그래프 차수 | 하나로 센다 | 없는 것으로 본다 | 이웃(거래처)이 몇 곳인가 |
# | 다중 그래프 차수 | 엣지마다 센다 | 관례상 **2** | 관계(거래)가 몇 건인가 |
#
# 둘 다 맞는 답이다. 틀리는 건 **무엇을 세는지 정하지 않고 섞을 때**다.
