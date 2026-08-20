# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# %% [markdown]
# # 리듀서와 교환법칙 — 순서가 답을 바꾸는가
#
# 상태 그래프에서 **같은 슈퍼스텝의 여러 노드가 같은 필드를 갱신**하면
# 실행기는 리듀서 `f(old, new)`로 갱신들을 차례차례 접어(fold) 넣는다.
#
# $$
# \text{final} \;=\; f\bigl(f(f(\text{init},\, u_{\sigma(1)}),\, u_{\sigma(2)}),\, u_{\sigma(3)}\bigr)
# $$
#
# 여기서 $\sigma$ 는 **실행기가 정하는 순열**이다. 개발자가 정할 수 없다.
# 따라서 리듀서는 반드시 **교환법칙**을 지켜야 한다.
#
# $$
# f(a,b) = f(b,a)
# $$
#
# 이 노트북은 순열을 **전부** 돌려서 결과가 갈리는지를 실제로 확인한다.

# %%
import functools
import itertools
import json
import os

import plotly.graph_objects as go
from plotly.subplots import make_subplots

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.getcwd()


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


def canon(x):
    """결과를 비교 가능한 문자열로 정규화."""
    if isinstance(x, (set, frozenset)):
        return json.dumps(sorted(map(str, x)), ensure_ascii=False)
    return json.dumps(x, sort_keys=True, ensure_ascii=False, default=str)


def all_orders(reducer, init, updates):
    """모든 실행 순서 순열에 대해 fold 결과를 모은다."""
    out = {}
    for perm in itertools.permutations(range(len(updates))):
        acc = functools.reduce(reducer, [updates[i] for i in perm], init)
        out[perm] = acc
    return out


def check(name, reducer, init, updates, show=3):
    res = all_orders(reducer, init, updates)
    groups = {}
    for perm, val in res.items():
        groups.setdefault(canon(val), []).append(perm)
    n = len(groups)
    verdict = "교환법칙 OK" if n == 1 else f"교환법칙 위반 ({n}가지)"
    print(f"[{name}] 순열 {len(res)}개 -> 서로 다른 결과 {n}개  ...  {verdict}")
    for i, (k, perms) in enumerate(groups.items()):
        if i >= show:
            print(f"      ... 외 {n - show}가지")
            break
        print(f"      {k}   <- 순열 {perms[0]} 등 {len(perms)}개")
    return n


print("준비 완료")

# 출력:
# 준비 완료

# %% [markdown]
# ## 1. 교환법칙을 **어기는** 리듀서
#
# 세 노드(재무 / 법무 / 영업)가 같은 슈퍼스텝에서 같은 필드를 갱신한다고 하자.
# 순열은 $3! = 6$ 가지다. 결과가 6가지로 갈리면 완전히 순서 의존이다.

# %%
# (1) 마지막 값 덮어쓰기 — 가장 흔한 기본 동작
def last_write_wins(old, new):
    return new


# (2) 문자열 이어 붙이기
def concat_str(old, new):
    return (old + " | " + new) if old else new


# (3) 리스트 이어 붙이기 (LangGraph 의 operator.add)
def list_concat(old, new):
    return list(old) + list(new)


# (4) 키 단위 병합 — "새 것이 이긴다" (19장 ex3 의 merge_dict)
def merge_dict(old, new):
    out = dict(old or {})
    out.update(new or {})
    return out


print("=== 교환법칙을 어기는 리듀서 ===\n")
bad = {}
bad["마지막 값 덮어쓰기"] = check(
    "마지막 값 덮어쓰기", last_write_wins, "", ["재무", "법무", "영업"]
)
print()
bad["문자열 이어 붙이기"] = check(
    "문자열 이어 붙이기", concat_str, "", ["재무", "법무", "영업"]
)
print()
bad["리스트 이어 붙이기"] = check(
    "리스트 이어 붙이기", list_concat, [], [["재무"], ["법무"], ["영업"]]
)
print()
bad["딕셔너리 new 우선 병합"] = check(
    "딕셔너리 new 우선 병합",
    merge_dict,
    {},
    [{"등급": "A"}, {"등급": "B"}, {"등급": "C", "지역": "수도권"}],
)

# 출력:
# === 교환법칙을 어기는 리듀서 ===
#
# [마지막 값 덮어쓰기] 순열 6개 -> 서로 다른 결과 3개  ...  교환법칙 위반 (3가지)
#       "영업"   <- 순열 (0, 1, 2) 등 2개
#       "법무"   <- 순열 (0, 2, 1) 등 2개
#       "재무"   <- 순열 (1, 2, 0) 등 2개
#
# [문자열 이어 붙이기] 순열 6개 -> 서로 다른 결과 6개  ...  교환법칙 위반 (6가지)
#       "재무 | 법무 | 영업"   <- 순열 (0, 1, 2) 등 1개
#       "재무 | 영업 | 법무"   <- 순열 (0, 2, 1) 등 1개
#       "법무 | 재무 | 영업"   <- 순열 (1, 0, 2) 등 1개
#       ... 외 3가지
#
# [리스트 이어 붙이기] 순열 6개 -> 서로 다른 결과 6개  ...  교환법칙 위반 (6가지)
#       ["재무", "법무", "영업"]   <- 순열 (0, 1, 2) 등 1개
#       ["재무", "영업", "법무"]   <- 순열 (0, 2, 1) 등 1개
#       ["법무", "재무", "영업"]   <- 순열 (1, 0, 2) 등 1개
#       ... 외 3가지
#
# [딕셔너리 new 우선 병합] 순열 6개 -> 서로 다른 결과 3개  ...  교환법칙 위반 (3가지)
#       {"등급": "C", "지역": "수도권"}   <- 순열 (0, 1, 2) 등 2개
#       {"등급": "B", "지역": "수도권"}   <- 순열 (0, 2, 1) 등 2개
#       {"등급": "A", "지역": "수도권"}   <- 순열 (1, 2, 0) 등 2개

# %% [markdown]
# 눈여겨볼 것.
#
# - **덮어쓰기**는 "마지막에 온 놈"이 이기므로 결과가 3가지(마지막 자리에 올 수 있는 값의 수).
# - **이어 붙이기**는 순열마다 결과가 달라 6가지 전부로 갈린다.
#   `list_concat`은 LangGraph 예제에서 가장 많이 쓰는 `operator.add`인데,
#   엄밀히는 교환법칙 위반이다. 다만 **원소 집합은 항상 같아서** 순서를 읽지 않기로
#   약속했다면 실용상 무해하다. 누군가 `state["logs"][0]`으로 분기하는 순간 버그가 된다.
# - **`merge_dict`**는 19장 본문에서 저자가 실제로 당한 함정이다.
#   "새 것이 이긴다"고 짰지만 무엇이 "새 것"인지는 실행기가 정한다.

# %% [markdown]
# ## 2. 교환법칙을 **지키는** 리듀서
#
# 승자 판단의 근거를 **인자 위치**가 아니라 **값 안**에 두면 순서 의존이 사라진다.

# %%
def add(old, new):
    return old + new


def take_max(old, new):
    return max(old, new)


def set_union(old, new):
    return set(old) | set(new)


def keep_latest(old, new):
    """타임스탬프가 더 최근인 쪽. (19장 ex3)"""
    if not old:
        return new
    if not new:
        return old
    return new if new["at"] > old["at"] else old


def sorted_unique(old, new):
    """이어 붙이되 중복 제거 + 정렬 -> 정규형이라 순서 의존이 사라진다."""
    return sorted(set(old) | set(new))


print("=== 교환법칙을 지키는 리듀서 ===\n")
good = {}
good["정수 덧셈"] = check("정수 덧셈", add, 0, [30, 45, 20])
print()
good["최댓값"] = check("최댓값", take_max, 0, [30, 45, 20])
print()
good["집합 합집합"] = check("집합 합집합", set_union, set(), [{"재무"}, {"법무"}, {"영업"}])
print()
good["정렬 + 중복 제거"] = check(
    "정렬 + 중복 제거", sorted_unique, [], [["재무"], ["법무"], ["영업", "재무"]]
)
print()
good["타임스탬프 기준 선택"] = check(
    "타임스탬프 기준 선택",
    keep_latest,
    {},
    [
        {"who": "김하늘", "at": "2024-03-01"},
        {"who": "박서준", "at": "2026-01-15"},
        {"who": "이도윤", "at": "2025-07-02"},
    ],
)

# 출력:
# === 교환법칙을 지키는 리듀서 ===
#
# [정수 덧셈] 순열 6개 -> 서로 다른 결과 1개  ...  교환법칙 OK
#       95   <- 순열 (0, 1, 2) 등 6개
#
# [최댓값] 순열 6개 -> 서로 다른 결과 1개  ...  교환법칙 OK
#       45   <- 순열 (0, 1, 2) 등 6개
#
# [집합 합집합] 순열 6개 -> 서로 다른 결과 1개  ...  교환법칙 OK
#       ["법무", "영업", "재무"]   <- 순열 (0, 1, 2) 등 6개
#
# [정렬 + 중복 제거] 순열 6개 -> 서로 다른 결과 1개  ...  교환법칙 OK
#       ["법무", "영업", "재무"]   <- 순열 (0, 1, 2) 등 6개
#
# [타임스탬프 기준 선택] 순열 6개 -> 서로 다른 결과 1개  ...  교환법칙 OK
#       {"at": "2026-01-15", "who": "박서준"}   <- 순열 (0, 1, 2) 등 6개

# %% [markdown]
# ## 3. 함정 — 동률(tie)에서 교환법칙이 되살아나 깨진다
#
# `keep_latest`는 `at`이 서로 다를 때만 안전하다.
# 마지막 줄이 `return new if new["at"] > old["at"] else old` 이므로
# **`at`이 같으면 `old`(= 먼저 온 쪽)가 이긴다.** 즉 동률 구간은 순서 의존이다.
#
# 고치는 법은 비교 키를 **전순서(total order)**로 확장하는 것이다.
#
# $$
# \text{key}(x) = (x.\text{at},\; x.\text{source})
# $$

# %%
TIED = [
    {"who": "김하늘", "at": "2026-01-15", "source": "ERP"},
    {"who": "박서준", "at": "2026-01-15", "source": "CRM"},  # at 동률!
    {"who": "이도윤", "at": "2024-03-01", "source": "MDM"},
]


def keep_latest_fixed(old, new):
    """동률이면 source 로 결정 -> 전순서라 순서와 무관."""
    if not old:
        return new
    if not new:
        return old
    key = lambda x: (x["at"], x["source"])  # noqa: E731
    return new if key(new) > key(old) else old


print("=== 동률이 있을 때 ===\n")
tie = {}
tie["keep_latest (tie-break 없음)"] = check("keep_latest (tie-break 없음)", keep_latest, {}, TIED)
print()
tie["keep_latest_fixed (전순서)"] = check("keep_latest_fixed (전순서)", keep_latest_fixed, {}, TIED)

# 출력:
# === 동률이 있을 때 ===
#
# [keep_latest (tie-break 없음)] 순열 6개 -> 서로 다른 결과 2개  ...  교환법칙 위반 (2가지)
#       {"at": "2026-01-15", "source": "ERP", "who": "김하늘"}   <- 순열 (0, 1, 2) 등 3개
#       {"at": "2026-01-15", "source": "CRM", "who": "박서준"}   <- 순열 (1, 0, 2) 등 3개
#
# [keep_latest_fixed (전순서)] 순열 6개 -> 서로 다른 결과 1개  ...  교환법칙 OK
#       {"at": "2026-01-15", "source": "ERP", "who": "김하늘"}   <- 순열 (0, 1, 2) 등 6개

# %% [markdown]
# 타임스탬프만으로는 부족하다. **같은 초에 찍힌 값 두 개**는 실무에서 아주 흔하고,
# 그때만 답이 갈리기 때문에 재현이 특히 어렵다.
#
# 분산 시스템에서 이 패턴의 정식 이름이 **LWW-Register**이고,
# `(timestamp, replica_id)` 튜플로 비교하는 것이 표준 처방이다.

# %% [markdown]
# ## 4. 결합법칙과 멱등성 — 교환법칙만으로는 부족한 지점
#
# | 성질 | 수식 | 막아 주는 것 |
# |---|---|---|
# | 교환법칙 | $f(a,b)=f(b,a)$ | **도착 순서**가 답을 바꾸는 것 |
# | 결합법칙 | $f(f(a,b),c)=f(a,f(b,c))$ | **묶는 방식**(부분 집계·트리 병합)이 답을 바꾸는 것 |
# | 멱등성 | $f(a,a)=a$ | **중복 반영**(재시도·at-least-once)이 값을 부풀리는 것 |
#
# 셋을 다 만족하면 그 병합은 **결합 반격자의 최소 상한**이 되고,
# 그 필드는 사실상 **CRDT**(정확히는 CvRDT)가 된다.

# %%
def is_commutative(f, vals):
    return all(canon(f(a, b)) == canon(f(b, a)) for a in vals for b in vals)


def is_associative(f, vals):
    return all(
        canon(f(f(a, b), c)) == canon(f(a, f(b, c)))
        for a in vals
        for b in vals
        for c in vals
    )


def is_idempotent(f, vals):
    return all(canon(f(a, a)) == canon(a) for a in vals)


def avg(old, new):
    """평균 — 교환법칙은 만족하지만 결합법칙이 깨진다."""
    return (old + new) / 2


NUMS = [1, 2, 3, 7]
FLOATS = [1.0, 2.0, 3.0, 7.0]  # avg 는 float 를 내므로 타입을 맞춰 비교한다
SETS = [frozenset({"a"}), frozenset({"b"}), frozenset({"a", "c"})]
LISTS = [["a"], ["b"], ["c"]]

CASES = [
    ("정수 덧셈 (add)", add, NUMS),
    ("최댓값 (max)", take_max, NUMS),
    ("집합 합집합 (union)", lambda a, b: frozenset(a) | frozenset(b), SETS),
    ("리스트 concat", list_concat, LISTS),
    ("마지막 값 덮어쓰기", last_write_wins, NUMS),
    ("평균 (avg)", avg, FLOATS),
]

print(f"{'리듀서':<22}{'교환':^8}{'결합':^8}{'멱등':^8}  판정")
print("-" * 62)
props = {}
for name, f, vals in CASES:
    c, a, i = is_commutative(f, vals), is_associative(f, vals), is_idempotent(f, vals)
    props[name] = (c, a, i)
    if c and a and i:
        verdict = "CRDT 가능 (반격자)"
    elif c and a:
        verdict = "가환 모노이드 — 중복 전달 주의"
    elif c:
        verdict = "순서는 안전, 묶는 방식은 위험"
    else:
        verdict = "리듀서로 쓰면 안 된다"
    mk = lambda b: "  O   " if b else "  X   "  # noqa: E731
    print(f"{name:<22}{mk(c):^8}{mk(a):^8}{mk(i):^8}  {verdict}")

# 출력: (터미널에서는 한글 폭 때문에 열이 조금 어긋나 보인다)
# 리듀서                   교환   결합   멱등   판정
# --------------------------------------------------------------
# 정수 덧셈 (add)            O     O     X    가환 모노이드 — 중복 전달 주의
# 최댓값 (max)              O     O     O    CRDT 가능 (반격자)
# 집합 합집합 (union)        O     O     O    CRDT 가능 (반격자)
# 리스트 concat             X     O     X    리듀서로 쓰면 안 된다
# 마지막 값 덮어쓰기          X     O     O    리듀서로 쓰면 안 된다
# 평균 (avg)                O     X     O    순서는 안전, 묶는 방식은 위험

# %% [markdown]
# 읽는 법.
#
# - **`add`**: 교환·결합은 되지만 **멱등이 아니다**. 노드가 타임아웃으로 재시도되어
#   같은 갱신이 두 번 도착하면 카운터가 부풀려진다.
# - **`max` / `union`**: 셋 다 만족. 중복 전달에도 안전하다. 이게 CRDT의 G-Set·G-Counter다.
# - **`list concat`**: 결합은 되지만 교환이 아니다. 순서를 읽지 않는다는 전제에서만 쓴다.
# - **`last_write_wins`**: 교환이 아니다. 값 안에 타임스탬프를 넣어야 고쳐진다.
# - **`avg`**: 교환은 되는데 **결합이 깨진다**. 그래서 평균을 리듀서로 쓰면 안 되고,
#   `(합, 개수)` 쌍을 리듀서로 쓰고 **마지막에 나눠야** 한다.

# %% [markdown]
# ## 5. 중복 전달 시뮬레이션 — 멱등성이 없으면 어떻게 되나
#
# 노드 하나가 재시도되어 같은 갱신이 두 번 도착한다고 하자.

# %%
UPD = [{"node": "재무", "cost": 30}, {"node": "법무", "cost": 45}]
DUP = UPD + [UPD[0]]  # 재무가 재시도로 한 번 더 도착


def add_cost(old, new):
    return old + new["cost"]


def add_cost_dedup(old, new):
    """갱신 ID 로 중복을 걸러 멱등성을 인위적으로 만든다 (OR-Set 아이디어)."""
    seen, total = old
    if new["node"] in seen:
        return old
    return (seen | {new["node"]}, total + new["cost"])


print("정상 전달:", functools.reduce(add_cost, UPD, 0))
print("중복 전달:", functools.reduce(add_cost, DUP, 0), " <- 30 이 두 번 더해졌다")
print("중복 제거:", functools.reduce(add_cost_dedup, DUP, (frozenset(), 0))[1])

# 출력:
# 정상 전달: 75
# 중복 전달: 105  <- 30 이 두 번 더해졌다
# 중복 제거: 75

# %% [markdown]
# ## 6. 시각화 — 순열별 결과가 몇 갈래로 갈리는가
#
# 왼쪽: 리듀서별 **서로 다른 결과의 개수**. 1이면 교환법칙 만족.
# 오른쪽: **순열 × 리듀서** 히트맵. 같은 색이면 같은 결과다.
# 한 행이 단색이면 그 리듀서는 순서에 무관하다.

# %%
PERM_CASES = [
    ("마지막 값 덮어쓰기", last_write_wins, "", ["재무", "법무", "영업"]),
    ("문자열 이어 붙이기", concat_str, "", ["재무", "법무", "영업"]),
    ("리스트 concat", list_concat, [], [["재무"], ["법무"], ["영업"]]),
    ("dict new 우선 병합", merge_dict, {}, [{"g": "A"}, {"g": "B"}, {"g": "C"}]),
    ("keep_latest (동률)", keep_latest, {}, TIED),
    ("keep_latest + tie-break", keep_latest_fixed, {}, TIED),
    ("정수 덧셈", add, 0, [30, 45, 20]),
    ("최댓값", take_max, 0, [30, 45, 20]),
    ("집합 합집합", set_union, set(), [{"재무"}, {"법무"}, {"영업"}]),
    ("정렬 + 중복 제거", sorted_unique, [], [["재무"], ["법무"], ["영업"]]),
]

names, counts, matrix = [], [], []
perm_labels = ["".join(str(i) for i in p) for p in itertools.permutations(range(3))]

for name, f, init, upd in PERM_CASES:
    res = all_orders(f, init, upd)
    order, gid = {}, []
    for p in itertools.permutations(range(3)):
        k = canon(res[p])
        order.setdefault(k, len(order))
        gid.append(order[k])
    names.append(name)
    counts.append(len(order))
    matrix.append(gid)

BAD, OK, GRID, TEXT, MUTED = "#C1443B", "#2F7D62", "#E3E1DC", "#2B2A28", "#6E6A65"
bar_colors = [OK if c == 1 else BAD for c in counts]

fig = make_subplots(
    rows=1,
    cols=2,
    column_widths=[0.44, 0.56],
    horizontal_spacing=0.16,
    subplot_titles=("서로 다른 결과의 개수 (1이면 교환법칙 OK)", "순열별 결과 그룹 (행이 단색이면 순서 무관)"),
)

fig.add_trace(
    go.Bar(
        x=counts,
        y=names,
        orientation="h",
        marker_color=bar_colors,
        text=[str(c) for c in counts],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{y}<br>서로 다른 결과 %{x}가지<extra></extra>",
        showlegend=False,
    ),
    row=1,
    col=1,
)

fig.add_trace(
    go.Heatmap(
        z=matrix,
        x=perm_labels,
        y=names,
        # 결과 그룹 ID 는 명목형이라 좋고/나쁨 없는 중립 색조를 쓴다
        colorscale=[
            [0.0, "#F2EFE9"], [0.2, "#D8D2C6"], [0.4, "#B3B7BF"],
            [0.6, "#8891A3"], [0.8, "#5D6880"], [1.0, "#3A425A"],
        ],
        zmin=0,
        zmax=5,
        showscale=False,
        xgap=2,
        ygap=2,
        hovertemplate="%{y}<br>순열 %{x} -> 결과그룹 %{z}<extra></extra>",
    ),
    row=1,
    col=2,
)

fig.update_layout(
    title=dict(
        text="리듀서는 교환법칙을 지켜야 한다 — 3개 갱신의 모든 실행 순서(3! = 6)를 돌린 결과",
        x=0.5,
        xanchor="center",
        font=dict(size=17, color=TEXT),
    ),
    template="plotly_white",
    font=dict(family="Apple SD Gothic Neo, AppleGothic, Noto Sans KR, sans-serif", color=TEXT, size=12),
    plot_bgcolor="white",
    paper_bgcolor="white",
    height=520,
    width=1180,
    margin=dict(l=170, r=40, t=90, b=70),
    bargap=0.35,
)
fig.update_xaxes(
    title_text="서로 다른 결과 개수", range=[0, 6.8], dtick=1,
    gridcolor=GRID, zeroline=False, row=1, col=1,
)
fig.update_xaxes(title_text="실행 순서 순열", row=1, col=2, tickfont=dict(color=MUTED))
fig.update_yaxes(autorange="reversed", row=1, col=1)
fig.update_yaxes(autorange="reversed", showticklabels=False, row=1, col=2)

PNG = os.path.join(HERE, "expy.png")
fig.write_image(PNG, scale=2)
print("저장:", PNG)
_show(fig)

# 출력:
# 저장: .../e2902828-0327-4027-964a-d46387ef8e53/expy.png

# %% [markdown]
# ## 7. 실무 체크리스트
#
# 1. **판단 근거를 값 안에 넣어라.** 승자를 `new`/`old` 같은 **인자 위치**로 고르면 이미 틀렸다.
#    시각·출처·신뢰도·버전을 값에 실어라.
# 2. **동률을 없애라.** 비교 키를 `(timestamp, source_id)` 같은 **전순서 튜플**로 확장.
# 3. **결과를 정규형으로.** 리스트면 `sorted`, 중복은 집합으로 걷어 낸 뒤 정렬.
# 4. **재시도를 가정하라.** 멱등하지 않으면 갱신에 고유 ID를 달아 중복을 거른다.
# 5. **테스트로 강제하라.** `itertools.permutations`로 모든 순서를 돌려
#    결과가 하나로 모이는지 단위 테스트를 만든다 (아래 `assert_commutative`).
# 6. **못 지키겠으면 병렬로 두지 마라.** 본질적으로 순서 의존인 병합은
#    리듀서로 풀지 말고 **슈퍼스텝 경계 노드를 하나 넣어 직렬화**한다.

# %%
def assert_commutative(reducer, init, updates):
    results = {canon(functools.reduce(reducer, perm, init))
               for perm in itertools.permutations(updates)}
    assert len(results) == 1, f"교환법칙 위반: {len(results)}가지 결과"
    return next(iter(results))


print("keep_latest_fixed:", assert_commutative(keep_latest_fixed, {}, TIED))
try:
    assert_commutative(merge_dict, {}, [{"g": "A"}, {"g": "B"}, {"g": "C"}])
except AssertionError as e:
    print("merge_dict:", e)

print(
    "\n결론 — 리듀서는 «실행기가 정하는 순서»를 받아들여야 하는 함수다.\n"
    "교환법칙은 순서가 결과를 바꾸지 못하게 하는 최소 조건이고,\n"
    "결합법칙은 «묶는 방식», 멱등성은 «중복 반영»까지 막아 준다.\n"
    "셋을 다 갖추면 그 필드는 CRDT 가 되고, 그때부터 분산 환경에서도 안전하다."
)

# 출력:
# keep_latest_fixed: {"at": "2026-01-15", "source": "ERP", "who": "김하늘"}
# merge_dict: 교환법칙 위반: 3가지 결과
#
# 결론 — 리듀서는 «실행기가 정하는 순서»를 받아들여야 하는 함수다.
# 교환법칙은 순서가 결과를 바꾸지 못하게 하는 최소 조건이고,
# 결합법칙은 «묶는 방식», 멱등성은 «중복 반영»까지 막아 준다.
# 셋을 다 갖추면 그 필드는 CRDT 가 되고, 그때부터 분산 환경에서도 안전하다.
