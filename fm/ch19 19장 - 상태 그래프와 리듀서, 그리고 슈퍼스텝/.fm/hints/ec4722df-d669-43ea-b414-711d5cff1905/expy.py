# %% [markdown]
# # `ex1_lost_update.py`의 두 상태 타입은 어떻게 다른가?
#
# 답부터 적어 둡니다.
#
# - `NoReducer`는 `logs: list`, `count: int` — **리듀서가 없다**.
# - `WithReducer`는 `logs: Annotated[list, operator.add]`,
#   `count: Annotated[int, operator.add]` — **리듀서를 붙였다**.
#
# 이 노트북의 목적은 "붙였다/안 붙였다"를 외우는 게 아니라,
# `Annotated[T, reducer]`가 **파이썬 타입 시스템에서 실제로 무엇인지**를
# 런타임에 직접 열어 보는 것입니다. 그다음 두 타입을 같은 슈퍼스텝
# 병렬 갱신에 태워 결과가 어떻게 갈라지는지 출력합니다.
#
# 필요 패키지: `plotly`, `kaleido` (PNG 저장), `langgraph` (선택 — 없으면 순수
# 파이썬 슈퍼스텝 시뮬레이터로 재현)

# %%
import operator
import os
from typing import Annotated, TypedDict, get_args, get_origin, get_type_hints

import plotly.graph_objects as go


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
print("준비 완료")
# 출력: 준비 완료


# %% [markdown]
# ## 1단계 — 원본의 두 상태 타입
#
# `ex1_lost_update.py`에 실린 정의 그대로입니다. 딱 두 줄 차이입니다.

# %%
# --- A안: 리듀서 없음 ---
class NoReducer(TypedDict):
    logs: list
    count: int


# --- B안: 리듀서 있음 ---
class WithReducer(TypedDict):
    logs: Annotated[list, operator.add]
    count: Annotated[int, operator.add]


print("NoReducer.__annotations__   ", NoReducer.__annotations__)
print("WithReducer.__annotations__ ", WithReducer.__annotations__)
# 출력: NoReducer.__annotations__    {'logs': <class 'list'>, 'count': <class 'int'>}
# 출력: WithReducer.__annotations__  {'logs': typing.Annotated[list, <built-in function add>],
# 출력:                               'count': typing.Annotated[int, <built-in function add>]}


# %% [markdown]
# ## 2단계 — `Annotated`는 "타입 + 메타데이터 봉투"다
#
# `Annotated[T, m1, m2, ...]`는 타입 검사기 입장에서는 **그냥 `T`**입니다.
# 런타임에만 `m1, m2, ...`가 따라붙습니다. 즉
#
# $$\text{Annotated}[T, m] \;\xrightarrow{\;\text{타입검사기}\;}\; T,
# \qquad
# \text{Annotated}[T, m] \;\xrightarrow{\;\text{런타임}\;}\; (T,\; (m,))$$
#
# 그래서 `logs: Annotated[list, operator.add]`는 여전히 "logs는 list다"이면서,
# 동시에 "이 필드를 합칠 때는 `operator.add`를 써라"라는 **부가 정보**를 싣습니다.
#
# 중요한 함정: `get_type_hints()`는 기본적으로 이 봉투를 **벗겨 버립니다**.
# 메타데이터를 보려면 `include_extras=True`가 필요합니다.

# %%
stripped = get_type_hints(WithReducer)                       # 기본값: 봉투를 벗김
kept = get_type_hints(WithReducer, include_extras=True)      # 봉투를 유지

print("include_extras=False ->", stripped)
print("include_extras=True  ->", kept)
print("같은가?", stripped == kept)
# 출력: include_extras=False -> {'logs': <class 'list'>, 'count': <class 'int'>}
# 출력: include_extras=True  -> {'logs': typing.Annotated[list, <built-in function add>],
# 출력:                          'count': typing.Annotated[int, <built-in function add>]}
# 출력: 같은가? False

# %% [markdown]
# `include_extras=False`로 읽으면 `WithReducer`가 `NoReducer`와 **완전히 똑같아 보입니다**.
# 리듀서 정보가 사라지기 때문입니다. LangGraph가 `include_extras=True`로 읽는 이유입니다.

# %%
print("벗긴 WithReducer == NoReducer 힌트?",
      get_type_hints(WithReducer) == get_type_hints(NoReducer))
# 출력: 벗긴 WithReducer == NoReducer 힌트? True


# %% [markdown]
# ## 3단계 — 메타데이터를 꺼내는 세 가지 통로
#
# | 방법 | 반환 |
# |---|---|
# | `tp.__metadata__` | 메타데이터 튜플만 `(operator.add,)` |
# | `tp.__origin__` | 벗긴 실제 타입 `list` |
# | `get_args(tp)` | `(list, operator.add)` — 타입이 0번, 나머지가 메타 |
# | `get_origin(tp)` | `typing.Annotated` 자체 — **벗긴 타입이 아니다** |
#
# `get_origin`은 "이게 Annotated냐?"를 묻는 데만 쓰고, 실제 타입은
# `get_args(tp)[0]` 또는 `tp.__origin__`으로 꺼내야 합니다.

# %%
tp = WithReducer.__annotations__["logs"]

print("타입             ", tp)
print("__metadata__     ", tp.__metadata__)
print("__origin__       ", tp.__origin__)
print("get_args(tp)     ", get_args(tp))
print("get_origin(tp)   ", get_origin(tp))
print("hasattr(list, '__metadata__') ->", hasattr(list, "__metadata__"))
# 출력: 타입              typing.Annotated[list, <built-in function add>]
# 출력: __metadata__      (<built-in function add>,)
# 출력: __origin__        <class 'list'>
# 출력: get_args(tp)      (<class 'list'>, <built-in function add>)
# 출력: get_origin(tp)    <class 'typing.Annotated'>
# 출력: hasattr(list, '__metadata__') -> False


# %% [markdown]
# ## 4단계 — `logs: list` 대 `Annotated[list, operator.add]`를 런타임에 구분해 내기
#
# 위 통로를 조합하면, 상태 타입 하나를 받아 **필드별 리듀서 유무**를 보고하는
# 함수를 직접 쓸 수 있습니다. LangGraph가 채널을 만들 때 하는 일의 축소판입니다.

# %%
def describe_state(state_type):
    """상태 TypedDict의 필드별 (실제타입, 리듀서) 를 뽑아낸다."""
    rows = []
    hints = get_type_hints(state_type, include_extras=True)
    for field, tp in hints.items():
        meta = getattr(tp, "__metadata__", ())      # Annotated 가 아니면 빈 튜플
        base = get_args(tp)[0] if meta else tp      # 봉투를 벗긴 실제 타입
        reducer = meta[0] if meta else None
        rows.append((field, base, reducer))
    return rows


def report(state_type):
    print(f"[{state_type.__name__}]")
    for field, base, reducer in describe_state(state_type):
        if reducer is None:
            print(f"    {field:<6} : {base.__name__:<5} 리듀서 없음  -> 채널 = LastValue(덮어쓰기)")
        else:
            print(f"    {field:<6} : {base.__name__:<5} 리듀서 {reducer.__name__:<4} -> 채널 = 누적(fold)")


report(NoReducer)
report(WithReducer)
# 출력: [NoReducer]
# 출력:     logs   : list  리듀서 없음  -> 채널 = LastValue(덮어쓰기)
# 출력:     count  : int   리듀서 없음  -> 채널 = LastValue(덮어쓰기)
# 출력: [WithReducer]
# 출력:     logs   : list  리듀서 add  -> 채널 = 누적(fold)
# 출력:     count  : int   리듀서 add  -> 채널 = 누적(fold)


# %% [markdown]
# 여기까지가 핵심입니다. **두 타입의 차이는 "런타임에 읽을 수 있는 메타데이터"의
# 유무**이지, 정적 타입의 차이가 아닙니다. 그리고 그 메타데이터가 곧
# "이 필드를 여럿이 동시에 쓴다"는 선언이 됩니다.


# %% [markdown]
# ## 5단계 — 같은 슈퍼스텝에 태워 보기
#
# 슈퍼스텝 하나에서 노드 $n$개가 같은 필드에 값 $v_1, \dots, v_n$을 쓸 때,
# 리듀서 $\oplus$가 있으면 이전 값 $s$에 접어 넣습니다.
#
# $$s' = (\cdots((s \oplus v_1) \oplus v_2) \cdots) \oplus v_n$$
#
# 리듀서가 없으면 접을 규칙이 없습니다. $n \ge 2$면 LangGraph는 조용히
# 하나만 남기는 대신 **에러로 막습니다**.
#
# $$s' = \begin{cases} v_1 & (n = 1) \\ \textsf{InvalidUpdateError} & (n \ge 2) \end{cases}$$
#
# 먼저 순수 파이썬 시뮬레이터로 이 규칙을 그대로 구현합니다.

# %%
class InvalidUpdateError(Exception):
    pass


def run_superstep(state_type, initial, writes):
    """한 슈퍼스텝에서 여러 노드가 낸 부분 갱신(writes)을 채널 규칙대로 합친다."""
    reducers = {f: r for f, _, r in describe_state(state_type)}
    state = dict(initial)

    # 필드별로 이번 스텝의 쓰기를 모은다
    per_field = {}
    for w in writes:
        for f, v in w.items():
            per_field.setdefault(f, []).append(v)

    for f, values in per_field.items():
        red = reducers[f]
        if red is None:
            if len(values) > 1:
                raise InvalidUpdateError(
                    f"At key '{f}': Can receive only one value per step. "
                    f"Use an Annotated key to handle multiple values."
                )
            state[f] = values[0]
        else:
            acc = state[f]
            for v in values:
                acc = red(acc, v)      # s ⊕ v 를 왼쪽부터 접는다
            state[f] = acc
    return state


# 원본과 같은 시나리오: 재무·법무·영업 셋이 «동시에» 한 줄씩, 1씩
WRITES = [{"logs": [f"{n} 실행"], "count": 1} for n in ("재무", "법무", "영업")]
INITIAL = {"logs": [], "count": 0}

sim_results = {}
for label, t in (("리듀서 없음", NoReducer), ("리듀서 있음", WithReducer)):
    try:
        out = run_superstep(t, INITIAL, WRITES)
        sim_results[label] = out
        print(f"[{label}] logs={out['logs']}  count={out['count']}")
    except InvalidUpdateError as e:
        sim_results[label] = None
        print(f"[{label}] 예외 — {str(e)[:70]}")
# 출력: [리듀서 없음] 예외 — At key 'logs': Can receive only one value per step. Use an Annota
# 출력: [리듀서 있음] logs=['재무 실행', '법무 실행', '영업 실행']  count=3


# %% [markdown]
# ## 6단계 — 진짜 LangGraph로 확인
#
# `langgraph`가 있으면 원본 `ex1_lost_update.py`의 그래프를 그대로 세워
# 시뮬레이터 결과와 맞는지 확인합니다. 없으면 5단계 결과를 그대로 씁니다.

# %%
real_results = {}
try:
    from langgraph.graph import END, START, StateGraph

    def make(state_type):
        def worker(name):
            def fn(s):
                return {"logs": [f"{name} 실행"], "count": 1}
            return fn

        b = StateGraph(state_type)
        for n in ("재무", "법무", "영업"):
            b.add_node(n, worker(n))
            b.add_edge(START, n)       # 셋을 «동시에» 시작 — 같은 슈퍼스텝
            b.add_edge(n, END)
        return b.compile()

    for label, t in (("리듀서 없음", NoReducer), ("리듀서 있음", WithReducer)):
        try:
            out = make(t).invoke(dict(INITIAL))
            real_results[label] = out
            print(f"[{label}] logs={out['logs']}  count={out['count']}")
        except Exception as e:
            real_results[label] = None
            print(f"[{label}] 예외 — {str(e).splitlines()[0][:70]}")
except ImportError:
    print("langgraph 없음 — 5단계 시뮬레이터 결과를 사용합니다.")
    real_results = sim_results
# 출력: [리듀서 없음] 예외 — At key 'logs': Can receive only one value per step. Use an Annota
# 출력: [리듀서 있음] logs=['법무 실행', '영업 실행', '재무 실행']  count=3
# 참고: langgraph 0.6.11 확인. logs 안의 «순서»는 노드 실행 순서에 따라 달라질 수
#       있습니다. 리듀서가 보장하는 건 «세 개가 다 남는다»이지 순서가 아닙니다.

# %%
print("시뮬레이터와 LangGraph 결과가 일치하는가?",
      {k: (v is None) for k, v in sim_results.items()}
      == {k: (v is None) for k, v in real_results.items()})
# 출력: 시뮬레이터와 LangGraph 결과가 일치하는가? True


# %% [markdown]
# ## 7단계 — 결과 시각화
#
# `logs` 길이와 `count`를 나란히 놓습니다. 리듀서가 없는 쪽은 값이 나오지
# 않았으므로 0으로 찍고, 막대 위에 "에러로 중단"이라고 적습니다.

# %%
keys = ["리듀서 없음", "리듀서 있음"]

logs_len = [len(real_results[k]["logs"]) if real_results[k] else 0 for k in keys]
counts = [real_results[k]["count"] if real_results[k] else 0 for k in keys]
notes = ["에러로 중단" if real_results[k] is None else "" for k in keys]

x = ["리듀서 없음 (NoReducer)", "리듀서 있음 (WithReducer)"]

fig = go.Figure()
fig.add_bar(name="logs 길이", x=x, y=logs_len, marker_color="#4C78A8",
            text=[str(v) for v in logs_len], textposition="outside")
fig.add_bar(name="count 값", x=x, y=counts, marker_color="#F58518",
            text=[str(v) for v in counts], textposition="outside")

for i, note in enumerate(notes):
    if note:
        fig.add_annotation(x=x[i], y=0.35, text=note, showarrow=False,
                           font=dict(color="#D62728", size=13))

fig.update_layout(
    title="같은 슈퍼스텝에서 노드 3개가 동시에 쓴 결과",
    barmode="group",
    yaxis_title="값",
    yaxis_range=[0, 4],
    template="plotly_white",
    width=760, height=440,
)

_show(fig)

png_path = os.path.join(HERE, "expy.png")
try:
    fig.write_image(png_path)
    print("저장:", png_path)
except Exception as e:
    print("PNG 저장 실패 (kaleido 필요):", e)
# 출력: 저장: .../expy.png


# %% [markdown]
# ## 정리
#
# | | `NoReducer` | `WithReducer` |
# |---|---|---|
# | `logs` 선언 | `list` | `Annotated[list, operator.add]` |
# | `count` 선언 | `int` | `Annotated[int, operator.add]` |
# | `__metadata__` | 없음 (`hasattr` False) | `(operator.add,)` |
# | 채널 동작 | LastValue — 한 스텝에 한 번만 | fold — 이전 값에 접어 넣음 |
# | 3개 동시 쓰기 | `InvalidUpdateError` | `logs` 3줄, `count` 3 |
#
# 원본이 강조하는 건 "리듀서를 붙였다"가 아니라
# **"이 필드를 여럿이 쓴다는 걸 타입에 적었다"**입니다.
# 그리고 그 "적었다"의 실체가 바로 4단계에서 꺼내 본
# `Annotated.__metadata__` — 코드를 읽지 않고 타입만 읽어도
# 동시 쓰기 여부를 알 수 있게 해 주는 런타임 메타데이터입니다.
