# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# %% [markdown]
# # 폭발 반경(blast radius)을 BFS로 재기
#
# `ex4_blast_radius.py`의 핵심 질문은 이것이다.
#
# > 에이전트 하나가 **장악**되면, 피해는 어디까지 번지나?
#
# 모델은 3계층 방향 그래프다.
#
# $$ \text{에이전트} \xrightarrow{\text{쓸 수 있는 도구}} \text{도구} \xrightarrow{\text{닿는}} \text{자원} $$
#
# 장악된 에이전트 $s$ 에서 시작해,
# - 그 에이전트의 도구가 닿는 **자원을 모으고**,
# - 도구에 `spawn`이 있으면 **다른 에이전트로 갈아타며** 큐에 넣는다(BFS 확장).
#
# 반경(=피해 점수)은 닿은 자원 집합 $R$ 의 가치 합이다.
# $$ \text{score}(s) = \sum_{r \in R(s)} \text{VALUE}[r] $$

# %%
from collections import deque

import plotly.graph_objects as go


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1. 그래프 정의
#
# 에이전트 → 도구, 도구 → 자원, 그리고 자원의 가치를 적는다.
# `spawn`은 닿는 자원이 없지만(`[]`) 대신 다른 에이전트로 갈아타게 해 준다.


# %%
def build_agents():
    # 매 실험마다 새 dict를 돌려줘 원본 훼손을 막는다
    return {
        "요약기": ["read_docs"],
        "분석기": ["read_docs", "db_read"],
        "보고서": ["db_read", "send_mail"],
        "관리자": ["read_docs", "db_read", "send_mail", "run_shell", "spawn"],
    }


TOOLS = {
    "read_docs": ["문서저장소"],
    "db_read": ["고객DB"],
    "send_mail": ["외부"],
    "run_shell": ["서버파일", "외부"],
    "spawn": [],  # 다른 에이전트를 만들 수 있다
}

SPAWNABLE = ["요약기", "분석기", "보고서", "관리자"]
VALUE = {"문서저장소": 1, "고객DB": 5, "외부": 4, "서버파일": 5}

print("에이전트:", list(build_agents()))
print("자원 가치:", VALUE)
# 출력: 에이전트: ['요약기', '분석기', '보고서', '관리자']
# 출력: 자원 가치: {'문서저장소': 1, '고객DB': 5, '외부': 4, '서버파일': 5}


# %% [markdown]
# ## 2. BFS로 반경 계산
#
# `seen_agents`가 방문 집합(무한 루프 방지)이자, 몇 에이전트로 번졌는지의 척도다.
# `resources`에 도구가 닿는 자원을 합쳐 간다.


# %%
def radius(agents, start, allow_spawn=True):
    """장악된 에이전트에서 시작해 닿는 (에이전트 집합, 자원 집합)."""
    seen_agents, resources = set(), set()
    q = deque([start])
    while q:
        a = q.popleft()
        if a in seen_agents:
            continue
        seen_agents.add(a)
        for t in agents[a]:
            resources |= set(TOOLS[t])  # ① 자원을 모은다
            if t == "spawn" and allow_spawn:  # ② spawn이면 다른 에이전트로 확장
                q.extend(SPAWNABLE)
    return seen_agents, resources


def score(resources):
    return sum(VALUE[r] for r in resources)


def report(agents, allow_spawn=True):
    rows = []
    for a in agents:
        ags, res = radius(agents, a, allow_spawn)
        rows.append((a, len(ags), sorted(res), score(res)))
    return rows


spawn_on = report(build_agents(), allow_spawn=True)
for a, nag, res, sc in spawn_on:
    print(f"{a:<6} 닿는에이전트 {nag}  자원 {res}  점수 {sc}")
# 출력: 요약기   닿는에이전트 1  자원 ['문서저장소']  점수 1
# 출력: 분석기   닿는에이전트 1  자원 ['고객DB', '문서저장소']  점수 6
# 출력: 보고서   닿는에이전트 1  자원 ['고객DB', '외부']  점수 9
# 출력: 관리자   닿는에이전트 4  자원 ['고객DB', '문서저장소', '서버파일', '외부']  점수 15

# %% [markdown]
# ## 3. spawn 제거 전후 비교
#
# 관리자만 spawn을 가졌으므로 자원 점수 표는 거의 그대로다.
# 그러나 **관리자가 닿는 에이전트가 4 → 1**로 줄어든다.
# spawn 제거는 자원 반경이 아니라 **"전파(lateral movement)"를 끊는다.**

# %%
spawn_off = report(build_agents(), allow_spawn=False)
print(f"{'에이전트':<6}{'닿는에이전트(on→off)':<20}{'점수(동일)':<10}")
for (a, nag_on, _, sc), (_, nag_off, _, _) in zip(spawn_on, spawn_off):
    mark = "  ← 전파 끊김" if nag_on != nag_off else ""
    print(f"{a:<6}{nag_on} → {nag_off:<16}{sc:<10}{mark}")
# 출력: 에이전트  닿는에이전트(on→off)    점수(동일)
# 출력: 요약기   1 → 1               1
# 출력: 분석기   1 → 1               6
# 출력: 보고서   1 → 1               9
# 출력: 관리자   4 → 1               15          ← 전파 끊김

# %% [markdown]
# ## 4. 시각화 — 관리자 장악 시 BFS 반경 (spawn on vs off)
#
# 3계층 그래프를 좌(spawn on)·우(spawn off) 두 패널에 그린다.
# 장악 시작점(관리자)에서 BFS로 **닿은 노드는 빨강**, 못 닿은 노드는 회색이다.
# spawn을 빼면 오른쪽에서 다른 에이전트들이 회색으로 떨어져 나간다.


# %%
def reached_nodes(agents, start, allow_spawn):
    seen_agents, resources = radius(agents, start, allow_spawn)
    tools = set()
    for a in seen_agents:
        tools |= set(agents[a])
    return seen_agents, tools, resources


# 3계층 좌표 (x=계층, y=순서)
AGENT_POS = {"요약기": 3, "분석기": 2, "보고서": 1, "관리자": 0}
TOOL_LIST = ["read_docs", "db_read", "send_mail", "run_shell", "spawn"]
RES_LIST = ["문서저장소", "고객DB", "외부", "서버파일"]
TOOL_POS = {t: i for i, t in enumerate(TOOL_LIST)}
RES_POS = {r: i for i, r in enumerate(RES_LIST)}


def panel_traces(agents, start, allow_spawn, xshift):
    seen_a, seen_t, seen_r = reached_nodes(agents, start, allow_spawn)
    edge_x, edge_y = [], []
    # 에이전트→도구
    for a, tools in agents.items():
        for t in tools:
            edge_x += [xshift + 0, xshift + 1, None]
            edge_y += [AGENT_POS[a] * 1.25, TOOL_POS[t], None]
    # 도구→자원
    for t, ress in TOOLS.items():
        for r in ress:
            edge_x += [xshift + 1, xshift + 2, None]
            edge_y += [TOOL_POS[t], RES_POS[r], None]
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(color="rgba(150,150,150,0.35)", width=1),
        hoverinfo="none", showlegend=False,
    )

    def node_trace(names, pos_map, xcol, seen, ycol_scale=1.0):
        xs, ys, texts, colors = [], [], [], []
        for n in names:
            xs.append(xshift + xcol)
            ys.append(pos_map[n] * ycol_scale)
            texts.append(n)
            colors.append("#d62728" if n in seen else "#b0b0b0")
        return go.Scatter(
            x=xs, y=ys, mode="markers+text", text=texts,
            textposition="middle right", textfont=dict(size=11),
            marker=dict(size=16, color=colors, line=dict(color="white", width=1)),
            hoverinfo="text", showlegend=False,
        )

    a_trace = node_trace(list(AGENT_POS), AGENT_POS, 0, seen_a, ycol_scale=1.25)
    t_trace = node_trace(TOOL_LIST, TOOL_POS, 1, seen_t)
    r_trace = node_trace(RES_LIST, RES_POS, 2, seen_r)
    return [edge_trace, a_trace, t_trace, r_trace]


agents_full = build_agents()
fig = go.Figure()
for tr in panel_traces(agents_full, "관리자", True, xshift=0):
    fig.add_trace(tr)
for tr in panel_traces(build_agents(), "관리자", False, xshift=4):
    fig.add_trace(tr)

# 패널 제목
fig.add_annotation(x=1, y=5.2, text="<b>spawn 있음</b> — 관리자 장악 → 4 에이전트로 전파",
                   showarrow=False, font=dict(size=13))
fig.add_annotation(x=5, y=5.2, text="<b>spawn 없음</b> — 전파 끊김 (관리자만)",
                   showarrow=False, font=dict(size=13))
fig.add_annotation(x=2, y=-1.2, text="빨강 = BFS로 닿음 · 회색 = 못 닿음",
                   showarrow=False, font=dict(size=11, color="#666"))

fig.update_layout(
    title="폭발 반경: 관리자 장악 시 BFS로 닿는 범위 (spawn 제거 전후)",
    xaxis=dict(visible=False, range=[-0.5, 7.5]),
    yaxis=dict(visible=False, range=[-1.6, 5.6]),
    width=1100, height=560, plot_bgcolor="white",
    margin=dict(l=20, r=20, t=60, b=20),
)

_show(fig)
fig.write_image("expy.png", scale=2)
print("saved expy.png")
# 출력: saved expy.png
