# %% [markdown]
# # CROSS_PRODUCT 가 3.4배여도 심각한 이유
#
# 33장 `ex1_read_plan.py` 는 같은 답을 내는 세 쿼리를 잰다.
#
# - **A. 두 끝을 따로 찾음** → 플랜에 `CROSS_PRODUCT` 가 있다. 사람 8,000명 × 팀 80개를 만들고 거른다.
# - **B. 팀에서 시작 / C. 사람에서 시작** → 관계를 따라간다.
#
# 측정값은 "A 가 B·C 의 3.4배". 3.4배는 아무도 안 고칠 숫자다. 그런데 이건 **배수 자체가 N에 비례해서 자라는** 종류의 차이다.
#
# $$T_A(N) \propto |P| \times |T| = N \cdot M, \qquad T_{B}(N) \propto |P| + E \;\text{(사실은 } \log|T| + \deg t \text{)}$$
#
# 그래서 배수는
#
# $$R(N) = \frac{T_A}{T_B} \sim \frac{N \cdot M}{N} = M \quad\text{— 상수가 아니라 } M \text{(팀 수)에 붙어 자란다.}$$
#
# 이 노트북은 순수 파이썬으로 두 플랜을 흉내 내서, 배수가 **왜 작은 규모에서 작아 보이는지**를 보여 준다.

# %%
import random
import time

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


N_TEAMS = 80
TARGET_TEAM = 7
TARGET_CITY = "마포"
CITIES = ["강남", "마포", "판교", "성수"]

print(f"팀 {N_TEAMS}개, 찾는 조건: 팀{TARGET_TEAM} 의 구성원 중 {TARGET_CITY} 거주자 수")
# 출력: 팀 80개, 찾는 조건: 팀7 의 구성원 중 마포 거주자 수


# %% [markdown]
# ## 1. 데이터를 만든다
#
# 사람 N명, 팀 M개, 소속 엣지 N개(사람마다 팀 하나). 두 가지 표현을 같이 만든다.
#
# - `people`, `teams` : 노드 목록 — 곱집합 플랜이 쓴다
# - `team_members` : 인접 리스트 — 관계 순회 플랜이 쓴다
# - `team_by_name` : 이름 → 팀 인덱스 (그래프 DB의 인덱스에 해당)

# %%
def build(n_people, n_teams=N_TEAMS, seed=42):
    rnd = random.Random(seed)
    people = [{"id": i, "name": f"P{i}", "city": CITIES[(i * 7) % 4]}
              for i in range(n_people)]
    teams = [{"id": t, "name": f"팀{t}"} for t in range(n_teams)]
    member_of = [rnd.randrange(n_teams) for _ in range(n_people)]

    team_members = [[] for _ in range(n_teams)]      # 인접 리스트 (관계)
    for i, t in enumerate(member_of):
        team_members[t].append(i)

    team_by_name = {t["name"]: t["id"] for t in teams}  # 인덱스
    return people, teams, member_of, team_members, team_by_name


p, t, mo, tm, tbn = build(8000)
print(f"사람 {len(p):,}명, 팀 {len(t)}개, 엣지 {len(mo):,}개")
print(f"팀{TARGET_TEAM} 구성원 수 = {len(tm[TARGET_TEAM]):,} (평균 차수 {len(mo) / len(t):.0f})")
# 출력: 사람 8,000명, 팀 80개, 엣지 8,000개
# 출력: 팀7 구성원 수 = 93 (평균 차수 100)


# %% [markdown]
# ## 2. 플랜 A — 곱집합 후 필터
#
# 쿼리 A 는 `(p:Person), (t:Team)` 처럼 **두 끝을 따로** 찾는다.
# 엔진이 둘을 잇는 방법을 못 찾으면 모든 쌍을 만들어 놓고 조건으로 거른다.
#
# $$\text{연산 수} = |P| \times |T| = N \cdot M$$

# %%
def plan_a_cross_product(people, teams, member_of):
    """CROSS_PRODUCT: 모든 (사람, 팀) 쌍을 만들고 나서 거른다."""
    ops = 0
    hit = 0
    for person in people:
        for team in teams:
            ops += 1                                     # 쌍 하나 생성 = 연산 1
            if team["name"] != f"팀{TARGET_TEAM}":
                continue
            if person["city"] != TARGET_CITY:
                continue
            if member_of[person["id"]] == team["id"]:
                hit += 1
    return hit, ops


# %% [markdown]
# ## 3. 플랜 B — 인덱스로 시작점 하나, 나머지는 관계로
#
# 쿼리 B 는 `(t:Team {name:'팀7'})<-[:Member]-(p:Person)` 이다.
# 시작점 하나만 인덱스로 찾고, 그다음은 이미 이어져 있는 엣지를 따라간다.
#
# $$\text{연산 수} = \underbrace{1}_{\text{인덱스 조회}} + \deg(t) \;\approx\; O(|P| + E)\ \text{규모에서 } O(E/M)$$

# %%
def plan_b_traversal(team_members, team_by_name, people):
    """인덱스로 팀 하나 찾고, 인접 리스트만 훑는다."""
    ops = 1                                              # 인덱스 조회 1회
    tid = team_by_name[f"팀{TARGET_TEAM}"]
    hit = 0
    for pid in team_members[tid]:                        # 엣지를 따라간다
        ops += 1
        if people[pid]["city"] == TARGET_CITY:
            hit += 1
    return hit, ops


a_hit, a_ops = plan_a_cross_product(p, t, mo)
b_hit, b_ops = plan_b_traversal(tm, tbn, p)
print(f"A: 답={a_hit}, 연산={a_ops:,}")
print(f"B: 답={b_hit}, 연산={b_ops:,}")
print(f"답이 같다: {a_hit == b_hit} / 연산 배수 {a_ops / b_ops:,.0f}x")
# 출력: A: 답=25, 연산=640,000
# 출력: B: 답=25, 연산=94
# 출력: 답이 같다: True / 연산 배수 6,809x


# %% [markdown]
# ## 4. N 을 키우며 연산 수와 실측 시간을 잰다
#
# 여기서 핵심은 **연산 수 배수는 이미 수천 배인데 실측 시간 배수는 훨씬 작다**는 점이다.
# 실측에는 파싱·계획·호출 같은 **고정 비용**이 붙기 때문이다. 33장 `ex2` 가 인덱스 실험에서
# 만난 것과 같은 함정이다.

# %%
SIZES = [500, 1000, 2000, 4000, 8000, 16000, 32000, 64000]

rows = []
for n in SIZES:
    people, teams, member_of, team_members, team_by_name = build(n)

    t0 = time.perf_counter()
    ha, oa = plan_a_cross_product(people, teams, member_of)
    ta = (time.perf_counter() - t0) * 1000

    reps = 200
    t0 = time.perf_counter()
    for _ in range(reps):
        hb, ob = plan_b_traversal(team_members, team_by_name, people)
    tb = (time.perf_counter() - t0) / reps * 1000

    assert ha == hb, (ha, hb)
    rows.append(dict(n=n, ops_a=oa, ops_b=ob, ms_a=ta, ms_b=tb))

print(f"{'사람 수':>9}{'A 연산':>12}{'B 연산':>9}{'A ms':>10}{'B ms':>9}"
      f"{'연산 배수':>12}{'시간 배수':>11}")
print("-" * 74)
for r in rows:
    print(f"{r['n']:>9,}{r['ops_a']:>12,}{r['ops_b']:>9,}"
          f"{r['ms_a']:>10.2f}{r['ms_b']:>9.3f}"
          f"{r['ops_a'] / r['ops_b']:>11,.0f}x{r['ms_a'] / r['ms_b']:>10,.0f}x")
# 출력:
#      사람 수        A 연산     B 연산      A ms     B ms       연산 배수      시간 배수
# --------------------------------------------------------------------------
#       500      40,000       10      5.52    0.001      4,000x     6,286x
#     1,000      80,000       13     10.48    0.001      6,154x     9,845x
#     2,000     160,000       23     21.38    0.002      6,957x    12,528x
#     4,000     320,000       55     44.43    0.004      5,818x    11,596x
#     8,000     640,000       94     86.50    0.007      6,809x    13,174x
#    16,000   1,280,000      178    185.09    0.014      7,191x    13,497x
#    32,000   2,560,000      363    348.75    0.026      7,052x    13,337x
#    64,000   5,120,000      773    712.65    0.061      6,624x    11,743x


# %% [markdown]
# ## 5. 왜 실측 배수는 「3.4배」로 보였나 — 고정 비용 모델
#
# 실제 DB 에서 한 번 재는 시간은
#
# $$T_{\text{측정}}(N) = \underbrace{C}_{\text{파싱·계획·왕복 (상수)}} + \underbrace{k \cdot W(N)}_{\text{진짜 일}}$$
#
# 이고, 배수는
#
# $$R(N) = \frac{C + k\,N M}{C + k\,N} \xrightarrow[\;C \gg kNM\;]{} 1, \qquad \xrightarrow[\;C \ll kNM\;]{} M$$
#
# 즉 **작은 N 에서는 배수가 1 쪽으로 눌려 보이고**, N 이 커지면 $M$(팀 수)까지 올라간다.
# 3.4배는 "작은 차이"가 아니라 **아직 눌려 있는 상태의 큰 차이**다.

# %%
# 33장 ex1 상황(사람 8,000 / 팀 80)에서 3.4배가 나오도록 고정 비용 C 를 역산한다.
N0, M0, R0 = 8000, 80, 3.4
K = 1.0                                   # 일 단위당 시간 (임의 단위)
# C + K*N0*M0 = R0 * (C + K*N0)  ->  C = K*N0*(M0 - R0) / (R0 - 1)
C = K * N0 * (M0 - R0) / (R0 - 1)


def modeled_ratio(n, m=M0):
    return (C + K * n * m) / (C + K * n)


print(f"역산한 고정 비용 C = {C:,.0f} 일 단위 (= 사람 {C / K:,.0f}명 훑는 값)")
print(f"검산: N=8,000 에서 배수 {modeled_ratio(8000):.2f}x\n")
print(f"{'사람 수':>12}{'예상 배수':>12}")
print("-" * 24)
for n in [8_000, 80_000, 800_000, 8_000_000, 80_000_000]:
    print(f"{n:>12,}{modeled_ratio(n):>11.1f}x")
# 출력: 역산한 고정 비용 C = 255,333 일 단위 (= 사람 255,333명 훑는 값)
# 출력: 검산: N=8,000 에서 배수 3.40x
# 출력:
#         사람 수       예상 배수
# ------------------------
#        8,000        3.4x
#       80,000       19.8x
#      800,000       60.9x
#    8,000,000       77.6x
#   80,000,000       79.7x


# %% [markdown]
# 사람이 8,000명일 때 3.4배였던 것이, **80만 명이면 60배**가 된다.
# 상한은 팀 수 $M=80$ 이다. 팀도 같이 자라면 상한 자체가 올라간다.
#
# 절대 시간으로 보면 더 분명하다. A 는 $N$ 에 선형이지만 기울기가 $M$ 배다.

# %%
for n in [8_000, 800_000, 80_000_000]:
    # 실측 기울기(1인당 ms)를 마지막 측정에서 뽑는다
    slope_a = rows[-1]["ms_a"] / rows[-1]["n"]
    slope_b = rows[-1]["ms_b"] / rows[-1]["n"]
    print(f"사람 {n:>12,}명 → A {slope_a * n:>12,.1f}ms   B {slope_b * n:>10,.3f}ms")
# 출력: 사람        8,000명 → A         89.1ms   B      0.008ms
# 출력: 사람      800,000명 → A      8,908.2ms   B      0.763ms
# 출력: 사람   80,000,000명 → A    890,816.2ms   B     76.253ms


# %% [markdown]
# ## 6. 그림으로
#
# 왼쪽: 연산 수의 점근 차이($O(NM)$ vs $O(N/M)$ 규모의 순회).
# 가운데: 실측 시간.
# 오른쪽: 배수 곡선 — 실측 배수와, 고정 비용을 넣은 모델이 어떻게 $M=80$ 으로 수렴하는지.

# %%
BLUE = "#3B82F6"
RED = "#EF4444"
GRAY = "#94A3B8"

ns = [r["n"] for r in rows]

fig = make_subplots(
    rows=1, cols=3,
    subplot_titles=("연산 수 (점근)", "실측 시간 (ms)", "배수 곡선 — 3.4배는 어디쯤인가"),
    horizontal_spacing=0.08,
)

fig.add_trace(go.Scatter(x=ns, y=[r["ops_a"] for r in rows], name="A: CROSS_PRODUCT O(N·M)",
                         mode="lines+markers", line=dict(color=RED, width=3)), row=1, col=1)
fig.add_trace(go.Scatter(x=ns, y=[r["ops_b"] for r in rows], name="B: 관계 순회 O(1+deg)",
                         mode="lines+markers", line=dict(color=BLUE, width=3)), row=1, col=1)

fig.add_trace(go.Scatter(x=ns, y=[r["ms_a"] for r in rows], name="A 실측",
                         mode="lines+markers", line=dict(color=RED, width=3, dash="dot"),
                         showlegend=False), row=1, col=2)
fig.add_trace(go.Scatter(x=ns, y=[r["ms_b"] for r in rows], name="B 실측",
                         mode="lines+markers", line=dict(color=BLUE, width=3, dash="dot"),
                         showlegend=False), row=1, col=2)

model_ns = [8000 * (2 ** i) for i in range(15)]
fig.add_trace(go.Scatter(x=model_ns, y=[modeled_ratio(n) for n in model_ns],
                         name="모델: (C+kNM)/(C+kN)", mode="lines",
                         line=dict(color="#8B5CF6", width=3)), row=1, col=3)
# 주의: 로그 축에서 add_hline(y=80) 은 10^80 에 그려진다. 수평선은 트레이스로 그린다.
fig.add_trace(go.Scatter(x=[model_ns[0], model_ns[-1]], y=[N_TEAMS, N_TEAMS],
                         mode="lines", line=dict(color=GRAY, dash="dash", width=2),
                         name=f"상한 M={N_TEAMS} (팀 수)"), row=1, col=3)
fig.add_trace(go.Scatter(x=[8000], y=[3.4], mode="markers+text",
                         marker=dict(color=RED, size=14, symbol="circle"),
                         text=["33장 측정: 3.4x"], textposition="top right",
                         name="33장 측정점"), row=1, col=3)
fig.add_trace(go.Scatter(x=[800_000], y=[modeled_ratio(800_000)], mode="markers+text",
                         marker=dict(color="#F59E0B", size=14),
                         text=[f"80만 명: {modeled_ratio(800_000):.0f}x"],
                         textposition="middle right", showlegend=False), row=1, col=3)

fig.update_xaxes(type="log", title_text="사람 수 N", row=1, col=1)
fig.update_xaxes(type="log", title_text="사람 수 N", row=1, col=2)
fig.update_xaxes(type="log", title_text="사람 수 N", row=1, col=3)
fig.update_yaxes(type="log", title_text="연산 수", row=1, col=1)
fig.update_yaxes(type="log", title_text="ms", row=1, col=2)
fig.update_yaxes(type="log", title_text="A / B 배수", row=1, col=3)

fig.update_layout(
    title="CROSS_PRODUCT: 지금 3.4배인 것이 나중에 60배가 되는 이유",
    template="plotly_white", height=460, width=1280,
    legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="left", x=0),
    margin=dict(t=90, b=110),
)

_show(fig)
fig.write_image("expy.png", scale=2)   # 필요 패키지: plotly, kaleido
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료


# %% [markdown]
# ## 정리
#
# 1. `CROSS_PRODUCT` 는 **비용이 곱**이다. $O(|P| \times |T|)$ 대 $O(|P| + E)$ 는 상수배 차이가 아니다.
# 2. 작은 벤치마크에서 배수가 작아 보이는 건 고정 비용 $C$ 가 지배하기 때문이다.
#    `3.4배` 라는 숫자 자체가 "규모가 작다"는 신호다.
# 3. 그래서 플랜을 읽을 때 **숫자(ms)가 아니라 연산자(`CROSS_PRODUCT`)**를 먼저 본다.
#    ms 는 오늘의 데이터 크기에 묶인 값이고, 연산자는 내일의 기울기를 알려 준다.
# 4. 고치는 법: 두 끝을 따로 찾지 말고, **시작점 하나를 인덱스로 찾고 나머지는 관계로 간다.**
