# %% [markdown]
# # 리듀서가 없는데 여러 노드가 같은 필드를 쓰면?
#
# **답**: 운이 나쁘면 갱신이 조용히 사라지고(lost update), 운이 좋으면 예외가 난다.
# LangGraph는 예외로 막아 준다.
#
# 이 노트북은 세 단계로 확인한다.
#
# 1. 순수 파이썬 슈퍼스텝 시뮬레이터로 **조용한 유실**을 재현한다.
# 2. 실제 LangGraph로 **`InvalidUpdateError`** 를 재현한다(설치돼 있을 때).
# 3. 리듀서를 붙였을 때 어떻게 합쳐지는지, 그리고 **교환법칙**이 왜 필요한지 본다.
#
# 필요 패키지: `plotly`, `kaleido` (시각화), 선택적으로 `langgraph`
# (없으면 순수 파이썬 시뮬레이터만 돌아간다)

# %%
# 필요 패키지: plotly, kaleido / (선택) langgraph>=0.6
import os
import operator
import warnings
from typing import Annotated, TypedDict

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


try:
    from langgraph.graph import END, START, StateGraph
    HAS_LANGGRAPH = True
except Exception:
    HAS_LANGGRAPH = False

print("langgraph 사용 가능:", HAS_LANGGRAPH)
# 출력: langgraph 사용 가능: True


# %% [markdown]
# ## 1. 슈퍼스텝을 손으로 흉내 내기
#
# 슈퍼스텝의 성질은 딱 두 가지다.
#
# - 같은 슈퍼스텝의 노드들은 **같은 상태 사본**을 읽는다 (서로가 쓴 걸 못 본다).
# - 노드는 상태 전체가 아니라 **바꾼 부분(update)** 만 돌려준다.
#
# 그래서 슈퍼스텝이 끝나는 순간, 같은 키에 대한 갱신이 여러 개 모인다.
# 이 여러 개를 **하나로 접는 함수**가 리듀서다.
#
# $$ \text{new\_state}[k] = \mathrm{reduce}\big(\text{old\_state}[k],\; u_1[k],\; u_2[k],\; \dots,\; u_n[k]\big) $$
#
# 리듀서가 없으면 접을 방법이 없다. 남는 선택지는 둘뿐이다.
# **마지막 하나만 남기거나(조용한 유실)**, **에러를 내거나**.

# %%
def superstep(state, updates, reducers=None, on_conflict="last-write-wins"):
    """슈퍼스텝 한 번을 흉내 낸다.

    state    : 슈퍼스텝 시작 시점의 상태 (모든 노드가 이 사본을 읽는다)
    updates  : [(노드이름, {키: 값}), ...]  같은 슈퍼스텝에서 나온 부분 갱신들
    reducers : {키: f(old, new)}            없으면 on_conflict 정책을 따른다
    """
    reducers = reducers or {}
    new = dict(state)
    seen = {}          # 이 슈퍼스텝에서 이미 쓴 키 -> 쓴 노드
    lost = []          # 조용히 사라진 갱신 기록

    for node, upd in updates:
        for k, v in upd.items():
            if k in reducers:
                new[k] = reducers[k](new[k], v)      # 여러 개를 접는다
            elif k not in seen:
                new[k] = v                            # 첫 번째 갱신
            else:
                # 같은 슈퍼스텝에서 같은 키를 두 번째로 쓰려 한다
                if on_conflict == "raise":
                    raise ValueError(
                        f"At key '{k}': Can receive only one value per step. "
                        f"('{seen[k]}' 와 '{node}' 가 동시에 씀)"
                    )
                lost.append((seen[k], k, new[k]))     # 앞사람 값이 버려진다
                new[k] = v                            # 마지막 사람이 이긴다
            seen.setdefault(k, node)
            seen[k] = node
    return new, lost


# 노드 셋이 같은 슈퍼스텝에서 logs 한 줄, count 1씩을 낸다
UPDATES = [
    ("재무", {"logs": ["재무 실행"], "count": 1}),
    ("법무", {"logs": ["법무 실행"], "count": 1}),
    ("영업", {"logs": ["영업 실행"], "count": 1}),
]
INIT = {"logs": [], "count": 0}

out, lost = superstep(INIT, UPDATES)          # 리듀서 없음 + 조용한 덮어쓰기
print("[리듀서 없음 / 조용한 덮어쓰기]")
print("   결과 :", out)
print("   유실 :", lost)
# 출력: [리듀서 없음 / 조용한 덮어쓰기]
# 출력:    결과 : {'logs': ['영업 실행'], 'count': 1}
# 출력:    유실 : [('재무', 'logs', ['재무 실행']), ('재무', 'count', 1), ('법무', 'logs', ['법무 실행']), ('법무', 'count', 1)]

# %% [markdown]
# 노드 셋이 다 성공했고, 예외도 없었고, 로그도 깨끗하다.
# 그런데 결과에는 **한 노드분만** 남았다. `count` 는 3이어야 하는데 1이다.
#
# 이게 「운이 나쁜 경우」다. 고전적인 **갱신 유실(lost update)** 이다.
# 더 나쁜 건 *누가* 살아남는지가 매번 다르다는 점이다.
# 실행기의 스케줄링 순서에 달렸고, 그 순서는 우리가 정하지 않는다.

# %%
# 같은 상황에서 "마지막 순서"만 바꿔 본다 — 답이 달라진다
for perm in ([0, 1, 2], [2, 0, 1], [1, 2, 0]):
    o, _ = superstep(INIT, [UPDATES[i] for i in perm])
    print([UPDATES[i][0] for i in perm], "->", o)
# 출력: ['재무', '법무', '영업'] -> {'logs': ['영업 실행'], 'count': 1}
# 출력: ['영업', '재무', '법무'] -> {'logs': ['법무 실행'], 'count': 1}
# 출력: ['법무', '영업', '재무'] -> {'logs': ['재무 실행'], 'count': 1}

# %%
# 같은 시뮬레이터, 정책만 "raise" 로 — 운이 좋은 경우
try:
    superstep(INIT, UPDATES, on_conflict="raise")
except ValueError as e:
    print("예외:", e)
# 출력: 예외: At key 'logs': Can receive only one value per step. ('재무' 와 '법무' 가 동시에 씀)

# %% [markdown]
# ## 2. 실제 LangGraph에서
#
# LangGraph는 **`raise` 쪽을 고른다**. 리듀서 없는 키에 한 슈퍼스텝에서 두 개 이상의
# 값이 들어오면 `InvalidUpdateError` 를 던진다.
#
# > `At key 'logs': Can receive only one value per step. Use an Annotated key to handle multiple values.`
#
# 조용히 지나가는 것보다 훨씬 낫다. 「막아 준다」는 게 이 뜻이다.

# %%
if HAS_LANGGRAPH:
    class NoReducer(TypedDict):        # A안: 리듀서 없음
        logs: list
        count: int

    class WithReducer(TypedDict):      # B안: 리듀서 있음
        logs: Annotated[list, operator.add]
        count: Annotated[int, operator.add]

    def build(state_type):
        def worker(name):
            def fn(s):
                return {"logs": [f"{name} 실행"], "count": 1}
            return fn

        b = StateGraph(state_type)
        for n in ("재무", "법무", "영업"):
            b.add_node(n, worker(n))
            b.add_edge(START, n)       # 셋을 «동시에» 시작 = 같은 슈퍼스텝
            b.add_edge(n, END)
        return b.compile()

    for label, t in (("리듀서 없음", NoReducer), ("리듀서 있음", WithReducer)):
        try:
            r = build(t).invoke({"logs": [], "count": 0})
            print(f"[{label}] logs={r['logs']} count={r['count']}")
        except Exception as e:
            print(f"[{label}] 예외 {type(e).__name__} — {str(e).splitlines()[0][:80]}")
else:
    print("langgraph 미설치 — 1번 시뮬레이터 결과로 대체")
# 출력: [리듀서 없음] 예외 InvalidUpdateError — At key 'logs': Can receive only one value per step. Use an Annotate
# 출력: [리듀서 있음] logs=['법무 실행', '영업 실행', '재무 실행'] count=3

# %% [markdown]
# 두 가지를 같이 보자.
#
# - 리듀서 없음 → **예외**. 프로그램이 죽지만, 틀린 답을 들고 다니지는 않는다.
# - 리듀서 있음 → `count=3`, `logs` 세 줄. 전부 합쳐졌다.
#
# 그런데 `logs` 순서를 보라. `['법무', '영업', '재무']` 다.
# **등록 순서(재무→법무→영업)가 아니다.** 실행기가 정한 순서다.
# 여기서 다음 함정이 나온다.

# %% [markdown]
# ## 3. 리듀서는 교환법칙을 지켜야 한다
#
# 실행 순서를 우리가 정하지 못하므로, 리듀서는 순서와 무관하게 같은 답을 내야 한다.
#
# $$ f(a, b) = f(b, a) $$
#
# `operator.add` 는 정수에서는 교환법칙이 성립하고, 리스트에서는 성립하지 않는다
# (순서가 달라진다). 「합계」처럼 순서가 상관없는 값이면 안전하고,
# 「마지막 값이 이긴다」류의 리듀서는 순서에 통째로 끌려다닌다.
#
# 해법은 값 안에 **판단 근거(시각·출처·신뢰도)** 를 담고, 리듀서가 그걸 보고 정하는 것이다.

# %%
def keep_latest(old, new):
    """타임스탬프가 최근인 쪽 — 순서와 무관 (교환법칙 O)"""
    if not old:
        return new
    if not new:
        return old
    return new if new["at"] > old["at"] else old


def last_wins(old, new):
    """나중에 온 쪽 — 순서에 통째로 끌려간다 (교환법칙 X)"""
    return new


ERP = {"who": "김하늘", "at": "2024-03-01"}
CRM = {"who": "박서준", "at": "2026-01-15"}

for name, f in (("keep_latest", keep_latest), ("last_wins", last_wins)):
    ab = f(f({}, ERP), CRM)
    ba = f(f({}, CRM), ERP)
    print(f"{name:<12} f(ERP,CRM)={ab['who']}  f(CRM,ERP)={ba['who']}  "
          f"교환법칙 {'O' if ab == ba else 'X'}")
# 출력: keep_latest   f(ERP,CRM)=박서준  f(CRM,ERP)=박서준  교환법칙 O
# 출력: last_wins    f(ERP,CRM)=박서준  f(CRM,ERP)=김하늘  교환법칙 X

# %% [markdown]
# ## 4. 유실 규모 — 노드가 늘수록 얼마나 사라지나
#
# 같은 슈퍼스텝에서 $n$ 개 노드가 같은 필드를 쓸 때,
# 리듀서 없이 마지막 하나만 남기면 반영되는 갱신은 항상 1개다.
#
# $$ \text{유실률} = \frac{n - 1}{n} = 1 - \frac{1}{n} $$
#
# 노드가 5개면 80%가 사라진다. 그것도 **조용히**.

# %%
NS = list(range(1, 9))
applied_lost = [1 for _ in NS]                  # 리듀서 없음 + 조용한 덮어쓰기
applied_reduce = list(NS)                       # 리듀서 있음
loss_rate = [(n - 1) / n * 100 for n in NS]

for n, a, r, l in zip(NS, applied_lost, applied_reduce, loss_rate):
    print(f"노드 {n}개  덮어쓰기 반영 {a}개 / 리듀서 반영 {r}개 / 유실률 {l:5.1f}%")
# 출력: 노드 1개  덮어쓰기 반영 1개 / 리듀서 반영 1개 / 유실률   0.0%
# 출력: 노드 2개  덮어쓰기 반영 1개 / 리듀서 반영 2개 / 유실률  50.0%
# 출력: 노드 3개  덮어쓰기 반영 1개 / 리듀서 반영 3개 / 유실률  66.7%
# 출력: 노드 4개  덮어쓰기 반영 1개 / 리듀서 반영 4개 / 유실률  75.0%
# 출력: 노드 5개  덮어쓰기 반영 1개 / 리듀서 반영 5개 / 유실률  80.0%
# 출력: 노드 6개  덮어쓰기 반영 1개 / 리듀서 반영 6개 / 유실률  83.3%
# 출력: 노드 7개  덮어쓰기 반영 1개 / 리듀서 반영 7개 / 유실률  85.7%
# 출력: 노드 8개  덮어쓰기 반영 1개 / 리듀서 반영 8개 / 유실률  87.5%

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

FONT = "Apple SD Gothic Neo, AppleGothic, Noto Sans KR, sans-serif"

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=("반영된 갱신 수", "조용한 유실률 (리듀서 없음)"),
)

fig.add_trace(go.Bar(name="리듀서 있음 (합쳐짐)", x=NS, y=applied_reduce,
                     marker_color="#2E86DE",
                     hovertemplate="노드 %{x}개 → 반영 %{y}개<extra></extra>"),
              row=1, col=1)
fig.add_trace(go.Bar(name="리듀서 없음 (마지막만 남음)", x=NS, y=applied_lost,
                     marker_color="#C8CDD4",
                     hovertemplate="노드 %{x}개 → 반영 %{y}개<extra></extra>"),
              row=1, col=1)
fig.add_trace(go.Scatter(name="유실률 1-1/n", x=NS, y=loss_rate,
                         mode="lines+markers", line=dict(color="#E74C3C", width=3),
                         hovertemplate="노드 %{x}개 → %{y:.1f}% 유실<extra></extra>"),
              row=1, col=2)

fig.add_annotation(x=2.8, y=1.15, text="리듀서가 없으면 여기까지만 반영된다<br>(LangGraph는 예외로 막아 준다)",
                   showarrow=True, arrowhead=2, ax=10, ay=-70,
                   font=dict(size=11, color="#E74C3C"), row=1, col=1)

fig.update_xaxes(title_text="같은 필드를 쓰는 노드 수 n", dtick=1, row=1, col=1)
fig.update_xaxes(title_text="같은 필드를 쓰는 노드 수 n", dtick=1, row=1, col=2)
fig.update_yaxes(title_text="갱신 수", row=1, col=1)
fig.update_yaxes(title_text="유실률 (%)", range=[0, 100], row=1, col=2)
fig.update_layout(
    title="리듀서 없이 같은 필드를 동시에 쓰면 — 조용한 유실 vs 예외",
    template="plotly_white", font=dict(family=FONT, size=12),
    barmode="group", height=460, width=1000,
    legend=dict(orientation="h", y=-0.22, x=0.02),
)

_show(fig)
fig.write_image(os.path.join(HERE, "expy.png"), scale=2)
print("saved:", os.path.join(HERE, "expy.png"))
# 출력: saved: .../expy.png

# %% [markdown]
# ## 정리
#
# | 상황 | 결과 | 판정 |
# |---|---|---|
# | 리듀서 없음 + 마지막 값만 남기는 실행기 | 갱신이 조용히 사라짐 (lost update) | 운이 나쁨 |
# | 리듀서 없음 + LangGraph | `InvalidUpdateError` 예외 | 운이 좋음 |
# | `Annotated[list, operator.add]` | 전부 합쳐짐 | 정답 |
#
# 핵심은 「리듀서를 붙였다」가 아니라 **「이 필드를 여럿이 쓴다는 걸 타입에 적었다」** 는 것이다.
# 타입만 읽어도 동시 쓰기 여부를 알 수 있다. 코드를 안 읽어도.
