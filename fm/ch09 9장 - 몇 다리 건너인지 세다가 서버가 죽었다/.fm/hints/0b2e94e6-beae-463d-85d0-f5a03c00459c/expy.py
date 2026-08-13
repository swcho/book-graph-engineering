# %% [markdown]
# # 순차 실행 · 슈퍼스텝 실행 · 임계 경로
#
# `ex5_toposort.py`가 찍는 세 수치는 **같은 작업 그래프를 세 가지 스케줄로 돌렸을 때의 총 소요 시간**이다.
#
# | 수치 | 뜻 | 가정 |
# |---|---|---|
# | 순차 실행 $T_{seq}$ | 작업을 하나씩 줄 세워 돌린다 | 일꾼 1명 |
# | 슈퍼스텝 실행 $T_{ss}$ | 위상 정렬로 만든 층을 통째로 병렬 실행, 층 끝에서 배리어 | 일꾼 무한, 층 단위 동기화 |
# | 임계 경로 $T_{cp}$ | 의존이 풀리는 즉시 시작 (ASAP) | 일꾼 무한, 동기화 없음 |
#
# 관계는 항상 이렇다.
#
# $$T_{seq} \;\ge\; T_{ss} \;\ge\; T_{cp}$$
#
# 임계 경로는 **이론적 하한**이다. 슈퍼스텝은 그 하한에 못 미치는 게 아니라, 하한보다 **느릴 수 있다**.
# 아래에서 에셋의 TASKS 그래프로 세 수치를 직접 계산하고, 층 배리어에서 몇 분이 새는지 타임라인으로 본다.

# %%
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용. 없으면 그 셀만 건너뛰면 된다)
from collections import defaultdict, deque

# ex5_toposort.py 의 의존 그래프와 비용을 그대로 가져온다.
TASKS = {
    "외부 API 예열": [],
    "데이터 적재": [],
    "스키마 검증": ["데이터 적재"],
    "엔티티 병합": ["데이터 적재"],
    "관계 추출": ["스키마 검증", "엔티티 병합"],
    "품질 검사": ["관계 추출"],
    "색인 생성": ["관계 추출"],
    "배포": ["품질 검사", "색인 생성", "외부 API 예열"],
}

COST = {
    "외부 API 예열": 40,
    "데이터 적재": 20,
    "스키마 검증": 5,
    "엔티티 병합": 30,
    "관계 추출": 15,
    "품질 검사": 8,
    "색인 생성": 25,
    "배포": 3,
}

print(f"{'작업':<14} {'비용(분)':>8}  의존")
for t, deps in TASKS.items():
    print(f"{t:<14} {COST[t]:>8}  {', '.join(deps) or '-'}")
# 출력:
# 작업               비용(분)  의존
# 외부 API 예열           40  -
# 데이터 적재              20  -
# 스키마 검증              5  데이터 적재
# 엔티티 병합              30  데이터 적재
# 관계 추출               15  스키마 검증, 엔티티 병합
# 품질 검사               8  관계 추출
# 색인 생성               25  관계 추출
# 배포                    3  품질 검사, 색인 생성, 외부 API 예열


# %%
# 1단계 — 위상 정렬로 층(슈퍼스텝)을 만든다. Kahn 알고리즘.
def supersteps(tasks):
    indeg = {t: len(d) for t, d in tasks.items()}
    child = defaultdict(list)
    for t, deps in tasks.items():
        for d in deps:
            child[d].append(t)
    ready = deque(sorted(t for t, n in indeg.items() if n == 0))
    layers, done = [], 0
    while ready:
        layer = sorted(ready)
        ready.clear()
        layers.append(layer)
        done += len(layer)
        for t in layer:
            for c in child[t]:
                indeg[c] -= 1
                if indeg[c] == 0:
                    ready.append(c)
    if done != len(tasks):
        raise ValueError("사이클")
    return layers


LAYERS = supersteps(TASKS)
print(f"작업 {len(TASKS)}개 → 슈퍼스텝 {len(LAYERS)}개\n")
for i, layer in enumerate(LAYERS, 1):
    span = max(COST[t] for t in layer)
    detail = ", ".join(f"{t}({COST[t]})" for t in layer)
    print(f"  {i}차 span={span:>2}분 : {detail}")
# 출력:
# 작업 8개 → 슈퍼스텝 5개
#
#   1차 span=40분 : 데이터 적재(20), 외부 API 예열(40)
#   2차 span=30분 : 스키마 검증(5), 엔티티 병합(30)
#   3차 span=15분 : 관계 추출(15)
#   4차 span=25분 : 색인 생성(25), 품질 검사(8)
#   5차 span= 3분 : 배포(3)


# %%
# 2단계 — 세 수치를 계산한다.
def critical_path(tasks, cost):
    """의존이 풀리는 대로 시작할 때의 총 소요 시간과, 그 경로."""
    memo, prev = {}, {}

    def go(t):
        if t in memo:
            return memo[t]
        best, arg = 0, None
        for d in tasks[t]:
            v = go(d)
            if v > best:
                best, arg = v, d
        prev[t] = arg
        memo[t] = best + cost[t]
        return memo[t]

    end = max(tasks, key=go)
    path, cur = [], end
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    return memo[end], end, list(reversed(path))


T_seq = sum(COST.values())
T_ss = sum(max(COST[t] for t in layer) for layer in LAYERS)
T_cp, end_task, CP_PATH = critical_path(TASKS, COST)

print(f"순차 실행     T_seq = {T_seq}분")
print(f"슈퍼스텝 실행 T_ss  = {T_ss}분  ({T_seq / T_ss:.1f}배 단축)")
print(f"임계 경로     T_cp  = {T_cp}분  (끝나는 작업: {end_task})")
print(f"\n임계 경로: {' → '.join(f'{t}({COST[t]})' for t in CP_PATH)}")
print(f"검산: {' + '.join(str(COST[t]) for t in CP_PATH)} = {sum(COST[t] for t in CP_PATH)}")
print(f"\n부등식 확인: {T_seq} >= {T_ss} >= {T_cp} → {T_seq >= T_ss >= T_cp}")
print(f"슈퍼스텝이 하한보다 더 쓴 시간: {T_ss - T_cp}분")
# 출력:
# 순차 실행     T_seq = 146분
# 슈퍼스텝 실행 T_ss  = 113분  (1.3배 단축)
# 임계 경로     T_cp  = 93분  (끝나는 작업: 배포)
#
# 임계 경로: 데이터 적재(20) → 엔티티 병합(30) → 관계 추출(15) → 색인 생성(25) → 배포(3)
# 검산: 20 + 30 + 15 + 25 + 3 = 93
#
# 부등식 확인: 146 >= 113 >= 93 → True
# 슈퍼스텝이 하한보다 더 쓴 시간: 20분

# %% [markdown]
# ## 왜 이 순서가 항상 성립하나
#
# 작업 $t$의 비용을 $c_t \ge 0$, 층 $L_i$의 span을 $s_i = \max_{t \in L_i} c_t$라 하자.
#
# **① $T_{seq} \ge T_{ss}$** — 각 층의 최댓값은 그 층의 합보다 클 수 없다.
#
# $$T_{ss} = \sum_i s_i = \sum_i \max_{t \in L_i} c_t \;\le\; \sum_i \sum_{t \in L_i} c_t = \sum_t c_t = T_{seq}$$
#
# 등호는 모든 층에 **비용이 0보다 큰 작업이 하나씩만** 있을 때, 즉 사실상 사슬(chain) 그래프일 때다.
#
# **② $T_{ss} \ge T_{cp}$** — Kahn 층 번호는 $\ell(t) = 1 + \max_{d \in \text{deps}(t)} \ell(d)$이므로,
# 엣지 $u \to t$가 있으면 $\ell(t) \ge \ell(u) + 1$이다.
# 따라서 어떤 경로 $P$도 **한 층에서 작업을 두 개 이상 지날 수 없다**. 층마다 최대 하나다.
#
# $$\sum_{t \in P} c_t \;\le\; \sum_{i \in \ell(P)} s_i \;\le\; \sum_i s_i = T_{ss}$$
#
# 모든 경로에 대해 성립하니 최댓값인 $T_{cp}$에도 성립한다. 즉 슈퍼스텝은 임계 경로 밑으로 절대 못 내려간다.
#
# **등호 $T_{ss} = T_{cp}$가 되는 조건**은 두 부등호가 동시에 붙을 때다.
#
# 1. 모든 층을 빠짐없이 지나면서
# 2. 각 층에서 **그 층의 최고 비용 작업**을 고르는
#
# 경로가 DAG 안에 실제로 존재해야 한다. 실무에서 쉽게 만족하는 경우는 두 가지다.
#
# - **층 안 비용이 균일할 때** ($c_t$가 전부 같으면 $s_i = c$, 그리고 층 정의상 길이 $k$짜리 사슬이 항상 존재하므로 $T_{ss} = T_{cp} = kc$)
# - **사슬 DAG** (층마다 작업 1개 → $T_{seq} = T_{ss} = T_{cp}$)
#
# 반대로 **한 층 안에 40분짜리와 20분짜리가 섞이면** 그 차이만큼 배리어에서 샌다.
# 이 예제의 20분 손실이 정확히 그것이다.

# %%
# 3단계 — 두 스케줄의 실제 타임라인을 만든다.
# (a) 슈퍼스텝: 층이 통째로 시작하고, 층의 제일 느린 작업이 끝날 때까지 다음 층은 못 간다.
ss_sched, clock = {}, 0
for layer in LAYERS:
    span = max(COST[t] for t in layer)
    for t in layer:
        ss_sched[t] = (clock, clock + COST[t], clock + span)  # 시작, 종료, 배리어 해제
    clock += span

# (b) ASAP(의존 단위): 선행 작업이 다 끝나면 바로 시작.
asap_sched = {}


def asap_finish(t):
    if t in asap_sched:
        return asap_sched[t][1]
    start = max((asap_finish(d) for d in TASKS[t]), default=0)
    asap_sched[t] = (start, start + COST[t])
    return start + COST[t]


for t in TASKS:
    asap_finish(t)

print(f"{'작업':<14} {'슈퍼스텝 시작~종료':>18} {'대기':>6} | {'ASAP 시작~종료':>16} {'앞당김':>7}")
for t in sorted(TASKS, key=lambda x: ss_sched[x][0]):
    s0, s1, bar = ss_sched[t]
    a0, a1 = asap_sched[t]
    print(f"{t:<14} {f'{s0}~{s1}':>18} {bar - s1:>6} | {f'{a0}~{a1}':>16} {s1 - a1:>7}")

print(f"\n슈퍼스텝 makespan = {max(v[2] for v in ss_sched.values())}분")
print(f"ASAP     makespan = {max(v[1] for v in asap_sched.values())}분 (= 임계 경로)")
# 출력:
# 작업                     슈퍼스텝 시작~종료     대기 |       ASAP 시작~종료     앞당김
# 외부 API 예열                    0~40      0 |             0~40       0
# 데이터 적재                       0~20     20 |             0~20       0
# 스키마 검증                      40~45     25 |            20~25      20
# 엔티티 병합                      40~70      0 |            20~50      20
# 관계 추출                       70~85      0 |            50~65      20
# 품질 검사                       85~93     17 |            65~73      20
# 색인 생성                      85~110      0 |            65~90      20
# 배포                        110~113      0 |            90~93      20
#
# 슈퍼스텝 makespan = 113분
# ASAP     makespan = 93분 (= 임계 경로)

# %%
# 4단계 — 20분은 정확히 어디서 새는가. 층별로 뜯어본다.
cp_set = set(CP_PATH)
print(f"{'층':>3} {'span':>5} {'임계 경로 작업':>16} {'비용':>5} {'손실':>5}")
lost_total = 0
for i, layer in enumerate(LAYERS, 1):
    span = max(COST[t] for t in layer)
    on_cp = [t for t in layer if t in cp_set]
    c = COST[on_cp[0]] if on_cp else 0
    lost_total += span - c
    print(f"{i:>3} {span:>5} {(on_cp[0] if on_cp else '-'):>16} {c:>5} {span - c:>5}")
print(f"\n총 손실 {lost_total}분 = T_ss({T_ss}) - T_cp({T_cp}) → {lost_total == T_ss - T_cp}")
print(
    "\n1차 층에서만 손실이 난다. '데이터 적재'는 20분에 끝나는데\n"
    "같은 층의 '외부 API 예열'이 40분이라 배리어가 40분에 열린다.\n"
    "그런데 '외부 API 예열'의 결과는 마지막 '배포'에서야 필요하다.\n"
    "의존이 아니라 층이 만든 대기다. 이게 슈퍼스텝이 임계 경로보다 느린 이유의 전부다."
)
# 출력:
#   층  span         임계 경로 작업    비용    손실
#   1    40           데이터 적재    20    20
#   2    30           엔티티 병합    30     0
#   3    15            관계 추출    15     0
#   4    25            색인 생성    25     0
#   5     3               배포     3     0
#
# 총 손실 20분 = T_ss(113) - T_cp(93) → True
#
# 1차 층에서만 손실이 난다. '데이터 적재'는 20분에 끝나는데
# 같은 층의 '외부 API 예열'이 40분이라 배리어가 40분에 열린다.
# 그런데 '외부 API 예열'의 결과는 마지막 '배포'에서야 필요하다.
# 의존이 아니라 층이 만든 대기다. 이게 슈퍼스텝이 임계 경로보다 느린 이유의 전부다.


# %%
# 5단계 — 간트 차트. 위가 슈퍼스텝(배리어 있음), 아래가 ASAP(의존 단위).
def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


import pathlib

import plotly.graph_objects as go
from plotly.subplots import make_subplots

C_CP = "#c0392b"  # 임계 경로 위의 작업
C_OFF = "#7f8c8d"  # 임계 경로 밖 작업
C_IDLE = "#f0d9d5"  # 배리어 대기(낭비)

order = sorted(TASKS, key=lambda t: (-ss_sched[t][0], t))  # y축 위에서 아래로 시간순

fig = make_subplots(
    rows=2,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.13,
    subplot_titles=(
        f"슈퍼스텝 실행 (층 배리어) — {T_ss}분",
        f"의존 단위 ASAP 실행 = 임계 경로 — {T_cp}분",
    ),
)

# 위: 슈퍼스텝. 실행 구간 + 배리어 대기 구간을 이어 붙인다.
fig.add_trace(
    go.Bar(
        y=order,
        x=[ss_sched[t][1] - ss_sched[t][0] for t in order],
        base=[ss_sched[t][0] for t in order],
        orientation="h",
        marker_color=[C_CP if t in cp_set else C_OFF for t in order],
        text=[f"{t} {COST[t]}분" for t in order],
        textposition="inside",
        insidetextanchor="start",
        name="실행",
        hovertemplate="%{y}: %{base}~%{x}<extra></extra>",
    ),
    row=1,
    col=1,
)
fig.add_trace(
    go.Bar(
        y=order,
        x=[ss_sched[t][2] - ss_sched[t][1] for t in order],
        base=[ss_sched[t][1] for t in order],
        orientation="h",
        marker_color=C_IDLE,
        marker_line=dict(color="#c0392b", width=1),
        name="배리어 대기 (낭비)",
        hovertemplate="대기 %{x}분<extra></extra>",
    ),
    row=1,
    col=1,
)

# 아래: ASAP
fig.add_trace(
    go.Bar(
        y=order,
        x=[asap_sched[t][1] - asap_sched[t][0] for t in order],
        base=[asap_sched[t][0] for t in order],
        orientation="h",
        marker_color=[C_CP if t in cp_set else C_OFF for t in order],
        text=[f"{t} {COST[t]}분" for t in order],
        textposition="inside",
        insidetextanchor="start",
        showlegend=False,
        hovertemplate="%{y}: %{base}~%{x}<extra></extra>",
    ),
    row=2,
    col=1,
)

# 층 배리어 위치를 세로선으로
bar_x, acc = [], 0
for layer in LAYERS:
    acc += max(COST[t] for t in layer)
    bar_x.append(acc)
for x in bar_x:
    fig.add_vline(x=x, line_dash="dot", line_color="#c0392b", line_width=1, row=1, col=1)
fig.add_vline(x=T_cp, line_dash="dash", line_color="#27ae60", line_width=2, row=2, col=1)
fig.add_vline(
    x=T_cp,
    line_dash="dash",
    line_color="#27ae60",
    line_width=2,
    annotation_text=f"하한 {T_cp}분",
    annotation_position="top left",
    annotation_font_color="#27ae60",
    row=1,
    col=1,
)

fig.update_layout(
    title=f"순차 {T_seq}분 &gt; 슈퍼스텝 {T_ss}분 &gt; 임계 경로 {T_cp}분 — 차이 {T_ss - T_cp}분은 층 배리어 대기",
    barmode="stack",
    height=640,
    width=1050,
    bargap=0.25,
    margin=dict(t=110),
    legend=dict(orientation="h", y=1.08, x=0.0),
    font=dict(family="Apple SD Gothic Neo, Malgun Gothic, NanumGothic, sans-serif", size=12),
)
fig.update_xaxes(title_text="경과 시간(분)", range=[0, T_ss + 6], row=2, col=1)
fig.update_xaxes(range=[0, T_ss + 6], row=1, col=1)

_show(fig)

out = pathlib.Path(__file__).parent / "expy.png" if "__file__" in dir() else pathlib.Path("expy.png")
fig.write_image(str(out))
print(f"저장: {out}")
# 출력: 저장: .../expy.png

# %% [markdown]
# 위 차트에서 읽을 것.
#
# - 빨간 막대가 임계 경로 위의 작업이다. 아래 패널에서 이 막대들이 **틈 없이 이어져** 93분을 만든다.
# - 위 패널의 연한 구간이 **배리어 대기**다. `데이터 적재`가 20분에 끝나고도 40분까지 놀고,
#   그 20분이 뒤의 모든 작업을 통째로 밀어 20분 손해로 남는다.
# - `외부 API 예열`(40분)은 층 1에 묶여 있지만 실제로는 `배포`(90분 시점) 전까지만 끝나면 된다.
#   **의존 관계가 요구하지 않는 동기화**를 층이 강제한 것이다.

# %%
# 6단계 — 등호 조건 검증. 언제 T_ss 가 T_cp 와 같아지나.
def three_numbers(tasks, cost):
    layers = supersteps(tasks)
    seq = sum(cost.values())
    ss = sum(max(cost[t] for t in layer) for layer in layers)
    cp, _, _ = critical_path(tasks, cost)
    return seq, ss, cp


# (a) 층 안 비용이 균일하면 T_ss == T_cp
uniform = {t: 10 for t in TASKS}
print("균일 비용(전부 10분):", three_numbers(TASKS, uniform), "→ T_ss == T_cp:",
      three_numbers(TASKS, uniform)[1] == three_numbers(TASKS, uniform)[2])

# (b) 사슬 DAG 면 셋이 전부 같다
chain = {"a": [], "b": ["a"], "c": ["b"], "d": ["c"]}
chain_cost = {"a": 7, "b": 2, "c": 9, "d": 4}
print("사슬 DAG:", three_numbers(chain, chain_cost))

# (c) 원래 비용에서 '외부 API 예열'만 20분으로 낮추면? (층 1의 편차가 사라진다)
flat1 = dict(COST, **{"외부 API 예열": 20})
print("외부 API 예열을 20분으로:", three_numbers(TASKS, flat1))
# 출력:
# 균일 비용(전부 10분): (80, 50, 50) → T_ss == T_cp: True
# 사슬 DAG: (22, 22, 22)
# 외부 API 예열을 20분으로: (126, 93, 93)

# %%
# 7단계 — 무작위 DAG 2,000개로 부등식이 정말 항상 성립하는지 확인.
import random

rnd = random.Random(20260801)
violations = 0
equal_ss_cp = 0
gaps = []
for _ in range(2000):
    n = rnd.randint(4, 12)
    nodes = [f"n{i}" for i in range(n)]
    g = {nodes[0]: []}
    for i in range(1, n):
        k = rnd.randint(0, min(i, 3))
        g[nodes[i]] = rnd.sample(nodes[:i], k)  # 위상 순서가 보장되니 사이클 없음
    c = {t: rnd.randint(1, 50) for t in nodes}
    seq, ss, cp = three_numbers(g, c)
    if not (seq >= ss >= cp):
        violations += 1
    if ss == cp:
        equal_ss_cp += 1
    gaps.append(ss - cp)

print(f"부등식 위반 사례: {violations}건 / 2,000건")
print(f"T_ss == T_cp 인 경우: {equal_ss_cp}건 ({equal_ss_cp / 20:.1f}%)")
print(f"T_ss - T_cp 평균 {sum(gaps) / len(gaps):.1f}분, 최대 {max(gaps)}분")
# 출력:
# 부등식 위반 사례: 0건 / 2,000건
# T_ss == T_cp 인 경우: 606건 (30.3%)
# T_ss - T_cp 평균 15.7분, 최대 99분

# %% [markdown]
# ## 정리
#
# - **$T_{seq} \ge T_{ss} \ge T_{cp}$는 항상 참이다.** 비용이 음수가 아니고 일꾼이 무한하다는 가정 아래
#   순수하게 정의에서 따라 나온다 (무작위 DAG 2,000개에서 위반 0건).
# - **임계 경로는 이론적 하한**이다. 어떤 스케줄러도 이 값 밑으로 내려갈 수 없다.
#   경로 위의 작업들은 서로 의존하므로 병렬화 자체가 불가능하기 때문이다.
# - **슈퍼스텝은 하한을 못 맞출 수 있다.** 원인은 층 배리어 하나뿐이다.
#   같은 층에 비용 편차가 있으면 $\sum_i (s_i - c_{\text{경로}(i)})$만큼 샌다. 이 예제에서 20분.
# - **등호 조건**: 각 층의 최고 비용 작업들이 하나의 경로로 이어질 때. 실무에서 흔한 충분조건은
#   *층 안 비용 균일* 또는 *사슬 DAG*다. 무작위 DAG에서도 30%쯤은 우연히 등호가 된다.
# - **현실 보정**: 일꾼이 유한하면 임계 경로도 달성 불가능하다. 이때의 하한은
#   $\max(T_{cp},\; T_{seq}/p)$ 쪽으로 올라간다 ($p$ = 일꾼 수). 그래도 $T_{cp}$가 하한이라는 사실은 변하지 않는다.
# - **엔지니어링 판단**: 층 단위는 구현이 쉽다(배리어 하나, 상태 관리 단순). 의존 단위는 빠르지만
#   작업별 완료 이벤트와 준비 큐를 직접 굴려야 한다. 층 안 비용 편차가 작으면 슈퍼스텝으로 충분하고,
#   `외부 API 예열` 같은 **긴 독립 작업**이 섞이는 순간 의존 단위 스케줄러가 값을 한다.
