# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용. 그 외 셀은 표준 라이브러리만)
# %% [markdown]
# # 엣지 방향과 질의 비용
#
# 같은 조직도를 두 방향으로 저장하고, 두 질문의 비용을 실제로 세어 본다.
#
# - `MANAGES` : 관리자 → 부하
# - `REPORTS_TO` : 부하 → 관리자
#
# 정보량은 완전히 같다(한쪽을 뒤집으면 다른 쪽). 그런데 비용은 다르다.

# %%
from collections import defaultdict


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


MANAGES = [("김부장", "박대리"), ("김부장", "이주임"), ("최이사", "김부장")]
REPORTS_TO = [(b, a) for a, b in MANAGES]

print("MANAGES   ", MANAGES)
print("REPORTS_TO", REPORTS_TO)
print("두 목록의 엣지 수:", len(MANAGES), len(REPORTS_TO))
# 출력: MANAGES    [('김부장', '박대리'), ('김부장', '이주임'), ('최이사', '김부장')]
# 출력: REPORTS_TO [('박대리', '김부장'), ('이주임', '김부장'), ('김부장', '최이사')]
# 출력: 두 목록의 엣지 수: 3 3

# %% [markdown]
# ## 1단계 — 나가는 엣지 색인 (인접 리스트)
#
# 저장 엔진은 「출발 노드 → 도착 노드 목록」 형태의 색인을 만든다.
# **키는 출발 노드뿐이다.** 도착 노드는 값 안에 숨어 있다.

# %%
def out_index(edges):
    idx = defaultdict(list)
    for a, b in edges:
        idx[a].append(b)  # 출발 노드를 키로
    return dict(idx)


print("MANAGES 색인   :", out_index(MANAGES))
print("REPORTS_TO 색인:", out_index(REPORTS_TO))
# 출력: MANAGES 색인   : {'김부장': ['박대리', '이주임'], '최이사': ['김부장']}
# 출력: REPORTS_TO 색인: {'박대리': ['김부장'], '이주임': ['김부장'], '김부장': ['최이사']}

# %% [markdown]
# `MANAGES` 색인의 키는 `김부장`, `최이사`뿐이다.
# `박대리`는 키에 없다. 값 목록 안에만 있다. 여기서 비대칭이 생긴다.

# %% [markdown]
# ## 2단계 — 두 방식의 조회 비용을 센다
#
# - **나가는 색인 조회**: 키 하나를 찾는다. 비용 $1$ (해시 조회, $O(1)$)
# - **전체 훑기**: 엣지를 전부 순회하며 도착점을 비교한다. 비용 $E$ ($O(E)$)

# %%
def lookup_outgoing(idx, name):
    """나가는 색인으로 1회 조회."""
    return idx.get(name, []), 1


def scan_incoming(edges, name):
    """들어오는 엣지를 찾으려면 전체를 훑는다."""
    scanned = 0
    found = []
    for a, b in edges:
        scanned += 1
        if b == name:
            found.append(a)
    return found, scanned


def ask(edges, label, name, want):
    """want='부하' 또는 '상사'. 저장 방향과 일치하면 색인, 아니면 전체 훑기."""
    idx = out_index(edges)
    aligned = (label == "MANAGES" and want == "부하") or (label == "REPORTS_TO" and want == "상사")
    if aligned:
        return lookup_outgoing(idx, name) + ("나가는 색인",)
    return scan_incoming(edges, name) + ("전체 훑기",)


for label, edges in (("MANAGES", MANAGES), ("REPORTS_TO", REPORTS_TO)):
    subs, c_sub, how_sub = ask(edges, label, "김부장", "부하")
    boss, c_boss, how_boss = ask(edges, label, "박대리", "상사")
    print(f"[{label}]")
    print(f"  김부장의 부하 → {subs}  비용 {c_sub}  ({how_sub})")
    print(f"  박대리의 상사 → {boss}  비용 {c_boss}  ({how_boss})")
# 출력: [MANAGES]
# 출력:   김부장의 부하 → ['박대리', '이주임']  비용 1  (나가는 색인)
# 출력:   박대리의 상사 → ['김부장']  비용 3  (전체 훑기)
# 출력: [REPORTS_TO]
# 출력:   김부장의 부하 → ['박대리', '이주임']  비용 3  (전체 훑기)
# 출력:   박대리의 상사 → ['김부장']  비용 1  (나가는 색인)

# %% [markdown]
# 카드의 답이 그대로 나왔다.
#
# `MANAGES`로 저장하면
# - 「김부장의 부하는?」 → 나가는 엣지 색인으로 **1회 조회**
# - 「박대리의 상사는?」 → **전체 엣지를 훑기** (여기서는 3)
#
# 두 방향 중 어느 쪽도 「양쪽 다 싸게」 만들지 못한다. 비용이 뒤집힐 뿐이다.
#
# $$\text{나가는 방향} = O(1), \qquad \text{역방향} = O(E)$$

# %% [markdown]
# ## 3단계 — 규모를 키우면
#
# 엣지 3개짜리 장난감에서는 1 대 3이라 차이가 안 느껴진다.
# 조직도를 복제해 엣지를 늘려 보자. 나가는 색인은 그대로 1이고,
# 역방향만 $E$에 비례해 커진다.

# %%
def make_org(n_managers, span):
    """관리자 n명이 각각 span명을 관리하는 조직도."""
    return [(f"M{m}", f"E{m}_{i}") for m in range(n_managers) for i in range(span)]


rows = []
for n_managers, span in ((1, 2), (100, 5), (10_000, 5), (200_000, 5)):
    edges = make_org(n_managers, span)
    _, c_sub = lookup_outgoing(out_index(edges), "M0")
    _, c_boss = scan_incoming(edges, "E0_0")
    rows.append((len(edges), c_sub, c_boss))

print(f"{'엣지 수 E':>12} {'부하 질의(색인)':>16} {'상사 질의(훑기)':>16}")
for e, cs, cb in rows:
    print(f"{e:>12,} {cs:>16} {cb:>16,}")
# 출력:      엣지 수 E    부하 질의(색인)    상사 질의(훑기)
# 출력:            2                1                2
# 출력:          500                1              500
# 출력:       50,000                1           50,000
# 출력:    1,000,000                1        1,000,000

# %% [markdown]
# 엣지 100만 개에서 역방향 질의는 100만 번 훑는다. **결과가 1건이어도** 그렇다.
# 나가는 방향 질의는 계속 1이다.

# %% [markdown]
# ## 4단계 — 엔진이 역방향 색인을 만들어 주면 차이가 사라진다
#
# 비용 차이는 역방향 색인이 없을 때만 성립한다.
# Neo4j처럼 노드마다 나가는/들어오는 엣지를 함께 들고 있으면 양방향이 대칭이다.
# 대신 쓰기 비용과 저장 공간이 두 배로 든다.

# %%
def both_index(edges):
    out, inc = defaultdict(list), defaultdict(list)
    for a, b in edges:
        out[a].append(b)
        inc[b].append(a)
    return dict(out), dict(inc)


out_idx, in_idx = both_index(MANAGES)
print("나가는 색인:", out_idx)
print("들어오는 색인:", in_idx)
print("김부장의 부하 → ", out_idx.get("김부장", []), " 비용 1")
print("박대리의 상사 → ", in_idx.get("박대리", []), " 비용 1")
print("저장 항목 수: 단방향", len(MANAGES), "→ 양방향", len(MANAGES) * 2)
# 출력: 나가는 색인: {'김부장': ['박대리', '이주임'], '최이사': ['김부장']}
# 출력: 들어오는 색인: {'박대리': ['김부장'], '이주임': ['김부장'], '김부장': ['최이사']}
# 출력: 김부장의 부하 →  ['박대리', '이주임']  비용 1
# 출력: 박대리의 상사 →  ['김부장']  비용 1
# 출력: 저장 항목 수: 단방향 3 → 양방향 6

# %% [markdown]
# ## 시각화
#
# 왼쪽: `MANAGES` 저장 시 두 질문의 비용 (로그 축).
# 오른쪽: 엣지 수가 늘 때 색인 조회는 평평하고 전체 훑기는 선형으로 오른다.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(
    rows=1,
    cols=2,
    subplot_titles=("MANAGES 저장 시 질의 비용 (E=3)", "엣지 수 대비 조회 비용"),
    horizontal_spacing=0.14,
)

# 왼쪽: 두 질문 비교
q_labels = ["김부장의 부하는?<br>(나가는 색인)", "박대리의 상사는?<br>(전체 훑기)"]
q_costs = [1, len(MANAGES)]
fig.add_trace(
    go.Bar(
        x=q_labels,
        y=q_costs,
        text=[f"{c}회" for c in q_costs],
        textposition="outside",
        marker_color=["#2E86AB", "#D1495B"],
        showlegend=False,
    ),
    row=1,
    col=1,
)

# 오른쪽: 규모 확장
e_vals = [e for e, _, _ in rows]
fig.add_trace(
    go.Scatter(
        x=e_vals,
        y=[cs for _, cs, _ in rows],
        mode="lines+markers",
        name="나가는 색인 O(1)",
        line=dict(color="#2E86AB", width=3),
    ),
    row=1,
    col=2,
)
fig.add_trace(
    go.Scatter(
        x=e_vals,
        y=[cb for _, _, cb in rows],
        mode="lines+markers",
        name="전체 훑기 O(E)",
        line=dict(color="#D1495B", width=3),
    ),
    row=1,
    col=2,
)

fig.update_yaxes(title_text="훑은 엣지 수", range=[0, 4], dtick=1, row=1, col=1)
fig.update_xaxes(title_text="엣지 수 E", type="log", row=1, col=2)
fig.update_yaxes(title_text="훑은 엣지 수", type="log", row=1, col=2)
fig.update_layout(
    title_text="엣지 방향이 질의 비용을 가른다 — 자주 묻는 쪽을 나가는 방향으로",
    template="plotly_white",
    width=1000,
    height=460,
    legend=dict(orientation="h", y=-0.22, x=0.62),
)

_show(fig)

import os

_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_png, scale=2)
print("저장:", _png)
# 출력: 저장: .../expy.png

# %% [markdown]
# ## 결론
#
# | 저장 방향 | 김부장의 부하는? | 박대리의 상사는? |
# |---|---|---|
# | `MANAGES` | **1** (나가는 색인) | $E$ (전체 훑기) |
# | `REPORTS_TO` | $E$ (전체 훑기) | **1** (나가는 색인) |
#
# 방향을 정하는 기준 두 가지.
#
# 1. 자주 묻는 질문을 **나가는** 방향으로.
# 2. 카디널리티가 **1 쪽**에서 **N 쪽**으로. (부하는 여럿, 상사는 하나)
#
# 둘이 충돌하면 1번을 따른다. **성능은 질의가 정한다.**
