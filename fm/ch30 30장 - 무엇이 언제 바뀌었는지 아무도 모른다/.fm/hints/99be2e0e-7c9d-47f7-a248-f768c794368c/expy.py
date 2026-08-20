# 필요 패키지: plotly, kaleido (pip install plotly kaleido)
# 리듀서 자체는 표준 라이브러리만으로 돌아간다. plotly/kaleido 는 그래프 저장에만 쓴다.
# 아래 `# 출력:` 주석은 실제 실행 결과다(macOS / Python 3.13).
# 결정론적이라 재실행해도 숫자가 그대로 나온다.

# %% [markdown]
# # 30장 ex4 — 같은 이벤트, 네 개의 답
#
# 이벤트 소싱에서 «지금 상태»는 저장된 것이 아니라 **접어서(fold)** 만드는 것이다.
#
# $$ S = \mathrm{fold}(f,\; s_0,\; [e_1, e_2, \dots, e_n]) = f(\cdots f(f(s_0, e_1), e_2) \cdots, e_n) $$
#
# 여기서 이벤트 열 $[e_1 \dots e_n]$ 은 **원본**이고 바뀌지 않는다.
# 바뀔 수 있는 것은 접는 함수 $f$ — 즉 **리듀서**뿐이다.
# 그러니 이렇게 말할 수 있다.
#
# $$ \text{같은 } [e_i] \;+\; \text{다른 } f \;\Longrightarrow\; \text{다른 } S $$
#
# 30장 `ex4_reducer_conflict.py` 는 이걸 네 개의 $f$ 로 보인다.
#
# | 리듀서 | 규칙 | 우선하는 축 |
# |---|---|---|
# | 마지막이 이긴다 (LWW) | 시각이 가장 늦은 «추가»가 이긴다 | 시간 |
# | 확신도가 이긴다 | $\arg\max_i \mathrm{conf}(e_i)$ | 모델이 스스로 매긴 값 |
# | 사람이 이긴다 | $\arg\max_i \mathrm{rank}(\mathrm{actor}(e_i))$ | 시스템이 정한 출처 등급 |
# | 전부 모은다 | 지우지 않고 집합에 쌓는다 | 없음(충돌을 그대로 드러냄) |
#
# 이 노트북은 (1) 네 리듀서를 순수 함수로 정의해 같은 이벤트에 적용하고,
# (2) 도착 순서를 바꿔 넣어 **순서 의존성**을 재고,
# (3) 결과를 그래프로 비교한다.

# %%
import itertools
import os
from datetime import datetime

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


print("준비 완료")
# 출력: 준비 완료

# %% [markdown]
# ## 1. 이벤트 — 사람과 에이전트가 번갈아 「선호」를 고쳤다
#
# 장의 예제 그대로다. 튜플은 `(시각, 행위자, 키, 값, 연산, 확신도)`.
#
# - 4/1 `hr-sync` 가 「채식」을 넣는다 (확신 0.95)
# - 4/3 `agent-4821` 이 「육식」을 넣고 1분 뒤 「채식」을 지운다 (확신 0.61)
# - 4/9 **사람이 직접** 「채식」이라고 말한다 (확신 1.00)
# - 4/22 `agent-5102` 가 「비건」으로 바꾼다 (확신 0.78)
#
# 4월 9일에 사람이 명시한 「채식」과 4월 22일에 에이전트가 넣은 「비건」이 이 예제의 핵심 충돌이다.

# %%
EVENTS = [
    ("2026-04-01T09:00", "hr-sync",    "선호", "채식", "추가", 0.95),
    ("2026-04-03T14:20", "agent-4821", "선호", "육식", "추가", 0.61),
    ("2026-04-03T14:21", "agent-4821", "선호", "채식", "삭제", 0.61),
    ("2026-04-09T10:05", "user",       "선호", "채식", "추가", 1.00),
    ("2026-04-22T16:40", "agent-5102", "선호", "비건", "추가", 0.78),
]

print(f"{'시각':<18}{'행위자':<14}{'키':<6}{'값':<8}{'연산':<6}{'확신도'}")
print("-" * 60)
for at, who, k, v, op, conf in EVENTS:
    print(f"{at:<18}{who:<14}{k:<6}{v:<8}{op:<6}{conf:.2f}")
# 출력:
# 시각                행위자           키     값       연산    확신도
# ------------------------------------------------------------
# 2026-04-01T09:00  hr-sync       선호    채식      추가    0.95
# 2026-04-03T14:20  agent-4821    선호    육식      추가    0.61
# 2026-04-03T14:21  agent-4821    선호    채식      삭제    0.61
# 2026-04-09T10:05  user          선호    채식      추가    1.00
# 2026-04-22T16:40  agent-5102    선호    비건      추가    0.78

# %% [markdown]
# ## 2. 리듀서 네 개 — 전부 순수 함수다
#
# 넷 다 «이벤트 리스트를 받아 상태 딕셔너리를 돌려주는» 순수 함수로 쓴다.
# 전역 상태를 건드리지 않으므로 같은 입력이면 항상 같은 출력이고,
# 그래서 **아무 때나 다시 접어도 같은 답**이 나온다 — 재생 가능성의 전제다.
#
# ### 2.1 마지막이 이긴다 $f_{LWW}$
#
# $$ f(s, e) = \begin{cases} s[k \mapsto v] & \text{op} = \text{추가} \\ s \setminus \{k\} & \text{op} = \text{삭제} \end{cases} $$
#
# 조건이 없다. 그냥 덮는다. 가장 흔하고 가장 위험하다.
#
# ### 2.2 확신도가 이긴다 $f_{conf}$
#
# $$ S[k] = e_j, \quad j = \arg\max_{i:\,\mathrm{op}_i=\text{추가}} \mathrm{conf}(e_i) $$
#
# 삭제는 아예 보지 않는다. 확신도가 «에이전트가 스스로 매기는» 값이라는 게 함정이다.
#
# ### 2.3 사람이 이긴다 $f_{rank}$
#
# $$ \mathrm{rank}(\text{user}) = 3 > \mathrm{rank}(\text{hr-sync}) = 2 > \mathrm{rank}(\text{agent-*}) = 1 $$
#
# 자기보다 등급이 낮은 이벤트는 덮지 못한다. 등급은 **시스템이** 부여하므로 에이전트가 올릴 수 없다.
#
# ### 2.4 전부 모은다 $f_{acc}$
#
# 상태가 값 하나가 아니라 **집합**이다. 충돌을 지우지 않고 「답이 여럿」으로 남긴다.

# %%
def last_write_wins(evs):
    """마지막 «추가»가 이긴다. 조건 없음."""
    st = {}
    for at, who, k, v, op, conf in evs:
        if op == "추가":
            st[k] = (v, at, who)
        else:
            st.pop(k, None)
    return st


def highest_confidence(evs):
    """확신도가 가장 높은 «추가»가 이긴다. 삭제는 무시한다."""
    best = {}
    for at, who, k, v, op, conf in evs:
        if op != "추가":
            continue
        if k not in best or conf > best[k][3]:
            best[k] = (v, at, who, conf)
    return {k: (v, at, who) for k, (v, at, who, _c) in best.items()}


RANK = {"user": 3, "hr-sync": 2}  # 나머지(에이전트)는 1


def human_wins(evs):
    """출처 등급이 높거나 같은 이벤트만 덮을 수 있다."""
    st = {}
    for at, who, k, v, op, conf in evs:
        r = RANK.get(who, 1)
        if op == "삭제":
            if k in st and st[k][3] <= r:
                st.pop(k)
            continue
        if k not in st or r >= st[k][3]:
            st[k] = (v, at, who, r)
    return {k: (v, at, who) for k, (v, at, who, _r) in st.items()}


def accumulate(evs):
    """지우지 않고 전부 모아 둔다. 충돌은 «답이 여럿»으로 남긴다."""
    st = {}
    for at, who, k, v, op, conf in evs:
        st.setdefault(k, set())
        if op == "추가":
            st[k].add(v)
        else:
            st[k].discard(v)
    return {k: (" / ".join(sorted(v)), "-", "-") for k, v in st.items()}


REDUCERS = [
    ("마지막이 이긴다", last_write_wins),
    ("확신도가 이긴다", highest_confidence),
    ("사람이 이긴다", human_wins),
    ("전부 모은다", accumulate),
]

print("리듀서 4개 정의 완료:", [n for n, _ in REDUCERS])
# 출력: 리듀서 4개 정의 완료: ['마지막이 이긴다', '확신도가 이긴다', '사람이 이긴다', '전부 모은다']

# %% [markdown]
# ## 3. 같은 이벤트에 네 리듀서를 적용한다
#
# 이벤트는 한 글자도 바꾸지 않았다. 바꾼 것은 접는 방법뿐이다.

# %%
def fmt_width(s, w):
    """한글은 폭 2칸으로 세서 표를 맞춘다."""
    n = sum(2 if ord(ch) > 0x2FFF else 1 for ch in s)
    return s + " " * max(w - n, 0)


print(f"{fmt_width('리듀서', 20)}{fmt_width('결과', 24)}"
      f"{fmt_width('누가 넣은 것', 16)}언제")
print("-" * 78)
BASE = {}
for name, fn in REDUCERS:
    st = fn(EVENTS)
    BASE[name] = st
    for k, (v, at, who) in st.items():
        print(f"{fmt_width(name, 20)}{fmt_width(k + '=' + v, 24)}"
              f"{fmt_width(who, 16)}{at}")
# 출력:
# 리듀서              결과                    누가 넣은 것    언제
# ------------------------------------------------------------------------------
# 마지막이 이긴다     선호=비건               agent-5102      2026-04-22T16:40
# 확신도가 이긴다     선호=채식               user            2026-04-09T10:05
# 사람이 이긴다       선호=채식               user            2026-04-09T10:05
# 전부 모은다         선호=비건 / 육식 / 채식 -               -

# %% [markdown]
# ### 읽는 법
#
# - **마지막이 이긴다** → 「비건」. 4월 9일에 사람이 명시한 「채식」을 4월 22일 에이전트가 **덮었다**.
#   시각 말고는 아무것도 안 보기 때문이다. 이게 기본값으로 제일 흔하고, 그래서 제일 위험하다.
# - **확신도가 이긴다** → 「채식」. 사람 발화의 1.00 이 최고값이라 살아남았다. 그럴듯해 보이지만,
#   $\mathrm{conf}$ 는 **에이전트가 스스로 써넣는 값**이다. 에이전트가 0.99 를 적으면 그대로 이긴다.
#   (20장: 모델이 스스로 올릴 수 있는 값은 지표로 못 쓴다.)
# - **사람이 이긴다** → 「채식」. 답은 확신도와 같지만 **이유가 다르다.**
#   등급은 시스템이 부여하므로 에이전트가 위로 못 올린다. 장에서 기본으로 권하는 것이 이것이다.
# - **전부 모은다** → 「비건 / 육식 / 채식」. 충돌을 숨기지 않는다. 대신 조회하는 쪽이 곤란해진다.
#
# 확신도와 등급이 **우연히 같은 답을 냈다**는 점에 주의하자. 다음 셀에서 갈라진다.

# %%
# 반례 — 에이전트가 확신도를 스스로 올려 적으면?
# A안: 에이전트가 1.00 을 적는다. 사람의 1.00 과 «동점»이고 `conf > best` 는 강부등호라
#      먼저 온 사람이 지킨다. 아슬아슬하게 버틴다.
# B안: 사람 발화가 파서를 거쳐 0.90 으로 기록되고 에이전트가 0.99 를 적는다.
#      현실에서 훨씬 흔한 모양이다.
VARIANTS = {
    "A. 에이전트 conf 1.00 (사람도 1.00)": EVENTS[:-1] + [
        ("2026-04-22T16:40", "agent-5102", "선호", "비건", "추가", 1.00),
    ],
    "B. 사람 발화 0.90, 에이전트 0.99": [
        e if e[1] != "user" else (e[0], e[1], e[2], e[3], e[4], 0.90)
        for e in EVENTS[:-1]
    ] + [("2026-04-22T16:40", "agent-5102", "선호", "비건", "추가", 0.99)],
}

for label, evs in VARIANTS.items():
    print(label)
    for name, fn in REDUCERS:
        v, at, who = fn(evs)["선호"]
        print(f"  {fmt_width(name, 20)}선호={fmt_width(v, 22)}{who}")
    print()
# 출력:
# A. 에이전트 conf 1.00 (사람도 1.00)
#   마지막이 이긴다     선호=비건                  agent-5102
#   확신도가 이긴다     선호=채식                  user
#   사람이 이긴다       선호=채식                  user
#   전부 모은다         선호=비건 / 육식 / 채식    -
#
# B. 사람 발화 0.90, 에이전트 0.99
#   마지막이 이긴다     선호=비건                  agent-5102
#   확신도가 이긴다     선호=비건                  agent-5102
#   사람이 이긴다       선호=채식                  user
#   전부 모은다         선호=비건 / 육식 / 채식    -
#
# B 에서 확신도 리듀서가 무너졌다. 에이전트가 «자기 손으로» 쓴 숫자 하나로 사람을 덮었다.
# 등급 리듀서는 A·B 둘 다 「채식」을 지킨다. 등급은 에이전트가 못 올리는 값이기 때문이다.

# %% [markdown]
# ## 4. 순서 의존성 — 도착 순서가 뒤바뀌면?
#
# 실제 시스템에서 이벤트는 «시각 순»으로 도착하지 않는다. 큐가 밀리거나, 재처리하거나,
# 서로 다른 소스가 늦게 붙는다. 그래서 이렇게 묻는다.
#
# $$ \text{어떤 순열 } \sigma \text{ 에 대해서도 } \mathrm{fold}(f, s_0, [e_{\sigma(1)} \dots e_{\sigma(n)}]) \text{ 가 같은가?} $$
#
# 이 성질을 **순서 무관(order-independent)** 또는 가환이라 한다.
# 이벤트 5개면 순열은 $5! = 120$ 개다. 전부 돌려서 서로 다른 결과가 몇 가지 나오는지 센다.

# %%
def result_str(st):
    return "; ".join(f"{k}={v}" for k, (v, _at, _who) in sorted(st.items()))


perms = list(itertools.permutations(EVENTS))
print(f"순열 {len(perms)}가지를 전부 접는다.\n")

ORDER_STATS = {}
print(f"{fmt_width('리듀서', 20)}{fmt_width('서로 다른 결과', 18)}"
      f"{fmt_width('순서 무관?', 14)}나온 답들")
print("-" * 96)
for name, fn in REDUCERS:
    outs = {}
    for p in perms:
        r = result_str(fn(list(p)))
        outs[r] = outs.get(r, 0) + 1
    ORDER_STATS[name] = outs
    tag = "예" if len(outs) == 1 else "아니오"
    listed = ", ".join(f"{r}({c})" for r, c in sorted(outs.items()))
    print(f"{fmt_width(name, 20)}{fmt_width(str(len(outs)) + '가지', 18)}"
          f"{fmt_width(tag, 14)}{listed}")
# 출력:
# 순열 120가지를 전부 접는다.
#
# 리듀서              서로 다른 결과    순서 무관?    나온 답들
# ------------------------------------------------------------------------------------------------
# 마지막이 이긴다     4가지             아니오        (24), 선호=비건(24), 선호=육식(24), 선호=채식(48)
# 확신도가 이긴다     1가지             예            선호=채식(120)
# 사람이 이긴다       1가지             예            선호=채식(120)
# 전부 모은다         2가지             아니오        선호=비건 / 육식(40), 선호=비건 / 육식 / 채식(80)

# %% [markdown]
# ### 읽는 법
#
# - **마지막이 이긴다**가 최악이다. 순열마다 답이 4가지로 갈린다.
#   심지어 «빈 결과»(24/120)까지 나온다 — 삭제가 맨 뒤로 밀린 경우다.
#   *도착 순서가 곧 진실*이 되어 버리는데, 도착 순서는 큐 지연 같은 우연이 정한다.
# - **확신도가 이긴다**는 순서 무관이다. $\max$ 는 가환이니 당연하다(동점은 강부등호 `>` 라 먼저 온 쪽 유지).
#   다만 앞 셀에서 봤듯 **순서에 안전한 것과 위조에 안전한 것은 다른 얘기**다.
# - **사람이 이긴다**도 이 이벤트 집합에서는 순서 무관이다. 이유가 있다.
#   최고 등급(`user`, 3)의 이벤트가 «추가»이고, 그보다 등급이 높거나 같은 이벤트가 하나도 없어서
#   언제 도착하든 마지막에 남는 값이 「채식」으로 고정된다.
#   일반적으로 무관하지는 않다 — `r >= st[k][3]` 이라 **같은 등급끼리는 나중 것이 이기므로**,
#   `user` 이벤트가 둘이면 순서가 답을 가른다.
# - **전부 모은다**는 `추가`/`삭제` 상쇄 순서에 따라 갈린다.
#   「채식」 추가가 둘(4/1, 4/9), 삭제가 하나(4/3)라 **삭제가 두 추가보다 뒤에 오는 1/3 = 40가지**에서
#   「채식」이 사라진다. 합집합만 쓰면 완전 무관해지지만 그러면 삭제를 못 쓴다 —
#   이게 31장의 동시 변경/CRDT 로 이어지는 실마리다.
#
# 정리하면, **순서 무관성과 안전성은 별개의 축**이다.
#
# | 리듀서 | 순서 무관 (이 데이터) | 일반적으로 순서 무관 | 에이전트가 이길 수 있나 |
# |---|---|---|---|
# | 마지막이 이긴다 | ✗ (4가지) | ✗ | 예 (마지막에 쓰기만 하면) |
# | 확신도가 이긴다 | ✓ | ✓ (동점 제외) | 예 (확신도를 올려 적으면) |
# | 사람이 이긴다 | ✓ | ✗ (동급 동점 시) | 아니오 |
# | 전부 모은다 | ✗ (2가지) | ✗ (삭제가 있으면) | — (충돌로 남김) |

# %% [markdown]
# ## 5. 그래프 — 네 리듀서가 고른 이벤트
#
# 위: 이벤트 타임라인. 마커 크기는 확신도, 색은 출처 등급, 세모는 삭제.
# 가운데: 각 리듀서가 최종적으로 채택한 값이 **어느 이벤트에서 왔는지**.
# 아래: 순열 120개에서 나온 서로 다른 결과 수(낮을수록 순서에 둔감).

# %%
def ts(at):
    return datetime.fromisoformat(at)


COLOR = {"user": "#d62728", "hr-sync": "#1f77b4"}


def color_of(who):
    return COLOR.get(who, "#7f7f7f")


fig = make_subplots(
    rows=3, cols=1,
    row_heights=[0.36, 0.34, 0.30],
    vertical_spacing=0.11,
    subplot_titles=(
        "① 이벤트 5건 — 크기=확신도 · 빨강=사람 파랑=시스템 회색=에이전트 · ●추가 ▼삭제",
        "② 각 리듀서가 채택한 값과 그 출처 이벤트",
        "③ 순열 120가지에서 나온 서로 다른 결과 수 (낮을수록 순서에 둔감)",
    ),
)

# ① 타임라인
for op, symbol in (("추가", "circle"), ("삭제", "triangle-down")):
    sel = [e for e in EVENTS if e[4] == op]
    if not sel:
        continue
    fig.add_trace(go.Scatter(
        x=[ts(e[0]) for e in sel],
        y=[e[3] for e in sel],
        mode="markers+text",
        marker=dict(size=[10 + 26 * e[5] for e in sel],
                    color=[color_of(e[1]) for e in sel],
                    symbol=symbol, line=dict(width=1, color="white")),
        text=[f"{e[1]} {e[5]:.2f}" for e in sel],
        textposition="bottom center", textfont=dict(size=10),
        name=op, showlegend=False,
        hovertemplate="%{x|%m-%d %H:%M}<br>%{y}<extra></extra>",
    ), row=1, col=1)

# ② 리듀서가 채택한 값 — 그 값이 마지막으로 «추가»된 이벤트 시각에 찍는다
last_add = {}
for at, who, k, v, op, conf in EVENTS:
    if op == "추가":
        last_add[v] = (at, who)

names = [n for n, _ in REDUCERS]
for name in names:
    v_str = BASE[name]["선호"][0]
    values = [x.strip() for x in v_str.split("/")]
    fig.add_trace(go.Scatter(
        x=[ts(last_add[v][0]) for v in values],
        y=[name] * len(values),
        mode="markers+text",
        marker=dict(size=20, symbol="star",
                    color=[color_of(last_add[v][1]) for v in values],
                    line=dict(width=1, color="white")),
        text=values, textposition="middle right", textfont=dict(size=11),
        showlegend=False,
        hovertemplate=name + ": %{text}<extra></extra>",
    ), row=2, col=1)

# ③ 순서 의존성
counts = [len(ORDER_STATS[n]) for n in names]
fig.add_trace(go.Bar(
    x=names, y=counts,
    marker_color=["#d62728" if c > 1 else "#2ca02c" for c in counts],
    text=[f"{c}가지" for c in counts], textposition="outside",
    showlegend=False,
    hovertemplate="%{x}: %{y}가지<extra></extra>",
), row=3, col=1)

fig.update_xaxes(title_text="시각", row=1, col=1)
fig.update_xaxes(title_text="채택된 값의 출처 이벤트 시각", row=2, col=1)
fig.update_yaxes(title_text="값", categoryorder="array",
                 categoryarray=["채식", "육식", "비건"],
                 range=[-0.7, 2.5], row=1, col=1)
fig.update_yaxes(title_text="", categoryorder="array",
                 categoryarray=[n for n, _ in REDUCERS],
                 range=[-0.6, 3.6], row=2, col=1)
fig.update_yaxes(title_text="서로 다른 결과 수", range=[0, 5], dtick=1, row=3, col=1)
fig.update_layout(
    title="같은 이벤트 5건, 리듀서 4개 — 답이 넷으로 갈린다",
    height=980, width=1120, template="plotly_white",
    margin=dict(t=90, b=60, l=100, r=60),
    showlegend=False,
)

_show(fig)
_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png") \
    if "__file__" in dir() else "expy.png"
fig.write_image(_png, scale=2)
print("저장:", os.path.basename(_png))
# 출력: 저장: expy.png

# %% [markdown]
# ## 6. 한 줄 정리
#
# > 이벤트를 쌓는 것만으로는 아무것도 안 정해진다. **어떻게 접을 것인가**가 실제 동작을 정하고,
# > 그건 기술 결정이 아니라 **도메인 결정**이다.
#
# 「마지막이 이긴다」를 기본값으로 두면 에이전트가 사람을 덮는다.
# 마지막에 쓰는 쪽은 대개 사람이 아니라 24시간 도는 에이전트이기 때문이다.
