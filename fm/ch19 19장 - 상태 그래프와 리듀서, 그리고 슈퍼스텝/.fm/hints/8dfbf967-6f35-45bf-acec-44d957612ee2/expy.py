# %% [markdown]
# # `ex3_custom_reducer.py`의 네 리듀서 — 순열 접기로 순서 의존을 잡아낸다
#
# 19장 예제 3은 리듀서 넷을 직접 정의한다.
#
# | 필드 | 리듀서 | 규칙 |
# |---|---|---|
# | `담당` | `keep_latest` | 타임스탬프가 더 최근인 쪽 |
# | `분류` | `keep_best` | 신뢰도(`conf`)가 높은 쪽 |
# | `속성` | `merge_dict` | 키 단위 병합, 겹치면 새 것 |
# | `태그` | `collect_unique` | 이어 붙이되 중복 제거, 순서 유지 |
#
# LangGraph 실행기는 같은 슈퍼스텝에서 온 갱신들을 **왼쪽 접기(fold)** 로 합친다.
#
# $$ \text{final} = f(\dots f(f(s_0, u_{\sigma(1)}), u_{\sigma(2)}) \dots, u_{\sigma(n)}) $$
#
# 여기서 $\sigma$ 는 실행기가 정하는 순열이고 **우리가 고를 수 없다**.
# 그러므로 리듀서가 안전하려면 모든 $\sigma$ 에 대해 결과가 같아야 한다.
# $f$ 가 결합법칙을 만족할 때, 이 조건은 곧 **교환법칙** $f(a,b)=f(b,a)$ 이다.
#
# 이 노트북은 갱신 셋(ERP·CRM·MDM)을 만들고 $3!=6$ 가지 순열 전부로 접어
# **서로 다른 결과가 몇 개 나오는지**를 리듀서마다 센다. 1이면 안전, 2 이상이면 순서 의존이다.
#
# 필요 패키지: `plotly`, `kaleido` (`pip install plotly kaleido`). LangGraph는 필요 없다 — 리듀서만 떼어내 검증한다.

# %%
import itertools
import json
from pathlib import Path

try:
    HERE = Path(__file__).resolve().parent
except NameError:
    HERE = Path.cwd()


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


def key(v):
    """결과를 비교 가능한 문자열로 정규화한다. dict는 키 정렬, list는 순서 유지."""
    return json.dumps(v, sort_keys=True, ensure_ascii=False)


print("준비 완료:", HERE.name)
# 출력: 준비 완료: 8dfbf967-6f35-45bf-acec-44d957612ee2

# %% [markdown]
# ## 1. 네 리듀서 — 원본 그대로
#
# `ex3_custom_reducer.py`에서 그대로 옮겨 왔다. 시그니처는 모두 `f(old, new) -> merged`.

# %%
def keep_latest(old, new):
    """타임스탬프가 더 최근인 쪽을 남긴다."""
    if not old:
        return new
    if not new:
        return old
    return new if new["at"] > old["at"] else old


def keep_best(old, new):
    """신뢰도가 높은 쪽. 같으면 먼저 온 쪽."""
    if not old:
        return new
    if not new:
        return old
    return new if new["conf"] > old["conf"] else old


def merge_dict(old, new):
    """키 단위 병합. 겹치면 새 것이 이긴다."""
    out = dict(old or {})
    out.update(new or {})
    return out


def collect_unique(old, new):
    """이어 붙이되 중복은 뺀다. 순서는 유지."""
    seen, out = set(), []
    for x in list(old or []) + list(new or []):
        k = x if isinstance(x, str) else str(x)
        if k not in seen:
            seen.add(k)
            out.append(x)
    return out


for f in (keep_latest, keep_best, merge_dict, collect_unique):
    print("{:<15} {}".format(f.__name__, f.__doc__))
# 출력: keep_latest     타임스탬프가 더 최근인 쪽을 남긴다.
# 출력: keep_best       신뢰도가 높은 쪽. 같으면 먼저 온 쪽.
# 출력: merge_dict      키 단위 병합. 겹치면 새 것이 이긴다.
# 출력: collect_unique  이어 붙이되 중복은 뺀다. 순서는 유지.

# %% [markdown]
# ## 2. 갱신 세 개 — 출처를 하나 더 늘린다
#
# 원본 예제는 ERP·CRM 둘이었다. 순서 의존은 둘보다 셋에서 훨씬 잘 드러나므로 MDM을 추가한다.
# 일부러 **동률(tie)** 을 심어 뒀다.
#
# - `담당`: CRM과 MDM의 `at`이 둘 다 `2026-01-15` → `keep_latest` 동률
# - `분류`: CRM과 MDM의 `conf`가 둘 다 `0.9` → `keep_best` 동률
# - `속성`: `등급` 키를 셋이 모두 쓴다 → `merge_dict` 충돌
# - `태그`: 셋이 원소를 겹쳐 쓴다 → `collect_unique` 순서 충돌

# %%
UPDATES = {
    "ERP": {
        "담당": {"who": "김하늘", "at": "2024-03-01"},
        "분류": {"cat": "제조", "conf": 0.7},
        "속성": {"사업자번호": "123-45-67890", "등급": "A"},
        "태그": ["제조", "중견"],
    },
    "CRM": {
        "담당": {"who": "박서준", "at": "2026-01-15"},
        "분류": {"cat": "유통", "conf": 0.9},
        "속성": {"등급": "B", "지역": "수도권"},
        "태그": ["중견", "수도권"],
    },
    "MDM": {
        "담당": {"who": "이도윤", "at": "2026-01-15"},
        "분류": {"cat": "물류", "conf": 0.9},
        "속성": {"등급": "C"},
        "태그": ["수도권", "제조"],
    },
}

FIELDS = [
    ("담당", keep_latest, {}),
    ("분류", keep_best, {}),
    ("속성", merge_dict, {}),
    ("태그", collect_unique, []),
]

SOURCES = list(UPDATES)
PERMS = list(itertools.permutations(SOURCES))
print("출처", SOURCES, "→ 순열", len(PERMS), "가지")
for p in PERMS:
    print("   ", " → ".join(p))
# 출력: 출처 ['ERP', 'CRM', 'MDM'] → 순열 6 가지
# 출력:     ERP → CRM → MDM
# 출력:     ERP → MDM → CRM
# 출력:     CRM → ERP → MDM
# 출력:     CRM → MDM → ERP
# 출력:     MDM → ERP → CRM
# 출력:     MDM → CRM → ERP

# %% [markdown]
# ## 3. 모든 순열로 접어서 결과가 갈리는지 본다
#
# 슈퍼스텝 하나를 흉내 내는 함수는 이게 전부다. 초기값에서 시작해 갱신을 차례로 접는다.

# %%
def scan(field, reducer, init, updates_by_src=None):
    """모든 순열로 접고 (순열, 결과) 목록과 서로 다른 결과 개수를 돌려준다."""
    rows = []
    for order in PERMS:
        acc = init
        for src in order:
            src_val = (updates_by_src or UPDATES)[src][field]
            acc = reducer(acc, src_val)
        rows.append((order, acc))
    distinct = {key(v) for _, v in rows}
    return rows, len(distinct)


base_result = {}
for field, reducer, init in FIELDS:
    rows, n = scan(field, reducer, init)
    base_result[field] = n
    flag = "안전" if n == 1 else "순서 의존!"
    print("=== {} / {}  → 서로 다른 결과 {}개  [{}]".format(field, reducer.__name__, n, flag))
    for order, val in rows:
        print("    {:<17} {}".format(" → ".join(order), key(val)))
    print()
# 출력: === 담당 / keep_latest  → 서로 다른 결과 2개  [순서 의존!]
# 출력:     ERP → CRM → MDM   {"at": "2026-01-15", "who": "박서준"}
# 출력:     ERP → MDM → CRM   {"at": "2026-01-15", "who": "이도윤"}
# 출력:     CRM → ERP → MDM   {"at": "2026-01-15", "who": "박서준"}
# 출력:     CRM → MDM → ERP   {"at": "2026-01-15", "who": "박서준"}
# 출력:     MDM → ERP → CRM   {"at": "2026-01-15", "who": "이도윤"}
# 출력:     MDM → CRM → ERP   {"at": "2026-01-15", "who": "이도윤"}
# 출력:
# 출력: === 분류 / keep_best  → 서로 다른 결과 2개  [순서 의존!]
# 출력:     ERP → CRM → MDM   {"cat": "유통", "conf": 0.9}
# 출력:     ERP → MDM → CRM   {"cat": "물류", "conf": 0.9}
# 출력:     ... (CRM이 먼저면 유통, MDM이 먼저면 물류 — conf 0.9 동률)
# 출력:
# 출력: === 속성 / merge_dict  → 서로 다른 결과 3개  [순서 의존!]
# 출력:     ERP → CRM → MDM   {"등급": "C", "사업자번호": "123-45-67890", "지역": "수도권"}
# 출력:     ERP → MDM → CRM   {"등급": "B", ...}
# 출력:     CRM → MDM → ERP   {"등급": "A", ...}
# 출력:     ... (마지막에 접힌 출처의 등급이 남는다: A / B / C)
# 출력:
# 출력: === 태그 / collect_unique  → 서로 다른 결과 3개  [순서 의존!]
# 출력:     ERP → CRM → MDM   ["제조", "중견", "수도권"]
# 출력:     CRM → ERP → MDM   ["중견", "수도권", "제조"]
# 출력:     MDM → ERP → CRM   ["수도권", "제조", "중견"]
# 출력:     ... (원소 집합은 같지만 리스트 «순서»가 갈린다)

# %% [markdown]
# ### 관찰 1 — `collect_unique`는 집합으로 보면 안전하다
#
# `태그`의 결과 셋은 리스트 순서만 다르고 원소는 같다.
# 즉 `collect_unique`는 **집합 준동형으로는 교환법칙을 만족**하지만
# **리스트(순서 포함)로는 만족하지 않는다.** 뒤 노드가 `태그[0]`을 읽는 순간 버그가 된다.

# %%
tag_rows, _ = scan("태그", collect_unique, [])
as_list = {key(v) for _, v in tag_rows}
as_set = {key(sorted(v)) for _, v in tag_rows}
print("리스트 기준 서로 다른 결과:", len(as_list))
print("집합 기준 서로 다른 결과:", len(as_set))
print("집합:", sorted(json.loads(next(iter(as_set)))))
# 출력: 리스트 기준 서로 다른 결과: 3
# 출력: 집합 기준 서로 다른 결과: 1
# 출력: 집합: ['수도권', '제조', '중견']

# %% [markdown]
# ## 4. 대수적 성질을 직접 판정한다
#
# 순열 접기가 "증상"이라면, 성질 판정은 "원인"이다. 표본 값들에 대해 세 가지를 확인한다.
#
# - 교환법칙 $f(a,b) = f(b,a)$ — 실행 순서 무관성의 필요조건
# - 결합법칙 $f(f(a,b),c) = f(a,f(b,c))$ — 부분 병합/재접기 안전성
# - 멱등성 $f(a,a) = a$ — 재시도·중복 전달 안전성

# %%
def check_props(field, reducer):
    vals = [UPDATES[s][field] for s in SOURCES]
    comm = all(key(reducer(a, b)) == key(reducer(b, a))
               for a, b in itertools.permutations(vals, 2))
    assoc = all(key(reducer(reducer(a, b), c)) == key(reducer(a, reducer(b, c)))
                for a, b, c in itertools.permutations(vals, 3))
    idem = all(key(reducer(a, a)) == key(a) for a in vals)
    return comm, assoc, idem


print("{:<6} {:<16} {:<8} {:<8} {}".format("필드", "리듀서", "교환", "결합", "멱등"))
print("-" * 52)
for field, reducer, _init in FIELDS:
    c, a, i = check_props(field, reducer)
    m = lambda ok: "O" if ok else "X"
    print("{:<6} {:<16} {:<8} {:<8} {}".format(field, reducer.__name__, m(c), m(a), m(i)))
# 출력: 필드   리듀서             교환       결합       멱등
# 출력: ----------------------------------------------------
# 출력: 담당   keep_latest      X        O        O
# 출력: 분류   keep_best        X        O        O
# 출력: 속성   merge_dict       X        O        O
# 출력: 태그   collect_unique   X        O        O

# %% [markdown]
# 넷 다 결합법칙과 멱등성은 만족하고 **교환법칙만 깨진다**. 원인은 각각 다르다.
#
# - `keep_latest` / `keep_best`: 비교 키가 **부분 순서**다. 동률이면 `>` 가 거짓이라 왼쪽(먼저 온 쪽)이 이긴다 → `f(a,b)=a`, `f(b,a)=b`.
# - `merge_dict`: 겹치는 키에서 오른쪽이 이기므로, 마지막 접기 대상이 승자다.
# - `collect_unique`: 원소 집합은 같지만 첫 등장 순서가 인자 순서를 그대로 물려받는다.
#
# ## 5. 고침 — 전순서(total order) 튜플 키
#
# 동률을 없애려면 비교 키를 **전순서**로 만들면 된다. 즉 서로 다른 두 값이 결코 같은 키를 갖지 않도록
# 판단 근거를 튜플로 쌓는다.
#
# $$ k(v) = (\text{at},\; \text{src\_rank},\; \text{id}) $$
#
# 이 키에 대해 `max`를 취하면 교환법칙·결합법칙·멱등성이 모두 성립한다.
# 핵심은 "리듀서를 고쳤다"가 아니라 **값 안에 순서를 정할 근거를 넣었다**는 것이다.

# %%
SRC_RANK = {"MDM": 3, "ERP": 2, "CRM": 1}  # 동률일 때 신뢰하는 출처 우선순위

# 각 갱신에 출처를 각인한다 — 리듀서가 볼 수 있어야 한다
STAMPED = {}
for src, upd in UPDATES.items():
    STAMPED[src] = {
        "담당": dict(upd["담당"], src=src),
        "분류": dict(upd["분류"], src=src),
        "속성": {k: {"v": v, "at": upd["담당"]["at"], "src": src} for k, v in upd["속성"].items()},
        "태그": list(upd["태그"]),
    }


def keep_latest_fixed(old, new):
    """(at, 출처순위, who) 전순서 키의 최대값. 동률 없음."""
    if not old:
        return new
    if not new:
        return old
    k = lambda d: (d["at"], SRC_RANK[d["src"]], d["who"])
    return new if k(new) > k(old) else old


def keep_best_fixed(old, new):
    """(conf, 출처순위, cat) 전순서 키의 최대값."""
    if not old:
        return new
    if not new:
        return old
    k = lambda d: (d["conf"], SRC_RANK[d["src"]], d["cat"])
    return new if k(new) > k(old) else old


def merge_dict_fixed(old, new):
    """키마다 «새 것이 이긴다»가 아니라 «(at, 출처순위)가 큰 쪽이 이긴다»."""
    out = dict(old or {})
    for k, cand in (new or {}).items():
        cur = out.get(k)
        if cur is None or (cand["at"], SRC_RANK[cand["src"]]) > (cur["at"], SRC_RANK[cur["src"]]):
            out[k] = cand
    return out


def collect_unique_fixed(old, new):
    """중복 제거 후 정규 순서(사전순)로 고정한다. 순서가 값의 일부가 되지 않게."""
    return sorted(set(list(old or []) + list(new or [])))


FIELDS_FIXED = [
    ("담당", keep_latest_fixed, {}),
    ("분류", keep_best_fixed, {}),
    ("속성", merge_dict_fixed, {}),
    ("태그", collect_unique_fixed, []),
]

fixed_result = {}
print("{:<6} {:<22} {:<10} {}".format("필드", "리듀서", "결과 개수", "최종값(대표)"))
print("-" * 88)
for field, reducer, init in FIELDS_FIXED:
    rows, n = scan(field, reducer, init, STAMPED)
    fixed_result[field] = n
    val = rows[0][1]
    if field == "속성":  # 래핑을 벗겨 사람이 읽게
        val = {k: "{} (from {})".format(d["v"], d["src"]) for k, d in val.items()}
    print("{:<6} {:<22} {:<10} {}".format(field, reducer.__name__, n, key(val)))
# 출력: 필드   리듀서                    결과 개수      최종값(대표)
# 출력: 담당   keep_latest_fixed      1          {"at": "2026-01-15", "src": "MDM", "who": "이도윤"}
# 출력: 분류   keep_best_fixed        1          {"cat": "물류", "conf": 0.9, "src": "MDM"}
# 출력: 속성   merge_dict_fixed       1          {"등급": "C (from MDM)", "사업자번호": "123-45-67890 (from ERP)", "지역": "수도권 (from CRM)"}
# 출력: 태그   collect_unique_fixed   1          ["수도권", "제조", "중견"]

print()
print("{:<6} {:<22} {:<6} {:<6} {:<8} {}".format("필드", "리듀서(수정)", "교환", "결합", "멱등", "멱등(정규형)"))
print("-" * 68)
for field, reducer, _init in FIELDS_FIXED:
    vals = [STAMPED[s][field] for s in SOURCES]
    comm = all(key(reducer(a, b)) == key(reducer(b, a)) for a, b in itertools.permutations(vals, 2))
    assoc = all(key(reducer(reducer(a, b), c)) == key(reducer(a, reducer(b, c)))
                for a, b, c in itertools.permutations(vals, 3))
    idem = all(key(reducer(a, a)) == key(a) for a in vals)
    # 정규형(한 번 접은 값)에 대한 멱등성: f(n, n) == n
    idem_n = all(key(reducer(reducer(a, a), reducer(a, a))) == key(reducer(a, a)) for a in vals)
    m = lambda ok: "O" if ok else "X"
    print("{:<6} {:<22} {:<6} {:<6} {:<8} {}".format(
        field, reducer.__name__, m(comm), m(assoc), m(idem), m(idem_n)))
# 출력: 필드   리듀서(수정)            교환    결합    멱등     멱등(정규형)
# 출력: --------------------------------------------------------------------
# 출력: 담당   keep_latest_fixed      O     O     O        O
# 출력: 분류   keep_best_fixed        O     O     O        O
# 출력: 속성   merge_dict_fixed       O     O     O        O
# 출력: 태그   collect_unique_fixed   O     O     X        O
#
# 주: collect_unique_fixed 는 f(a,a) 가 «정렬된» 리스트를 돌려주므로
#     입력이 이미 정규형(정렬·중복 없음)이 아니면 f(a,a) != a 다.
#     한 번 접은 뒤로는 f(n,n) == n 이므로 «정규형 위에서 멱등»하다.
#     재시도·중복 전달에는 안전하다는 뜻이다.

# %% [markdown]
# ## 6. 시각화 — 리듀서별 "서로 다른 결과 개수"
#
# $y=1$ 이면 어떤 실행 순서에도 같은 답이 나온다는 뜻이다. 그 선 위로 올라간 막대가 곧 버그 후보다.

# %%
import plotly.graph_objects as go

names = [f for f, _, _ in FIELDS]
labels = ["{}<br>{}".format(f, r.__name__) for f, r, _ in FIELDS]
before = [base_result[f] for f in names]
after = [fixed_result[f] for f in names]

fig = go.Figure()
fig.add_bar(x=labels, y=before, name="원본 (ex3 그대로)",
            marker_color="#d1495b", text=before, textposition="outside")
fig.add_bar(x=labels, y=after, name="전순서 튜플 키로 수정",
            marker_color="#2a9d8f", text=after, textposition="outside")
fig.add_hline(y=1, line_dash="dash", line_color="#6c757d",
              annotation_text="1 = 순서 무관(안전)", annotation_position="top right")
fig.update_layout(
    title="6가지 실행 순열로 접었을 때 «서로 다른 결과» 개수",
    xaxis_title="필드 / 리듀서",
    yaxis_title="서로 다른 결과 개수",
    yaxis=dict(range=[0, 3.6], dtick=1),
    barmode="group",
    template="plotly_white",
    width=920, height=520,
    legend=dict(orientation="h", y=1.08, x=0),
)

out_png = HERE / "expy.png"
fig.write_image(str(out_png))
print("저장:", out_png.name, "| 원본", before, "→ 수정", after)
_show(fig)
# 출력: 저장: expy.png | 원본 [2, 2, 3, 3] → 수정 [1, 1, 1, 1]

# %% [markdown]
# ## 정리
#
# | 리듀서 | 시그니처 | 하는 일 | 순서 의존 원인 | 처방 |
# |---|---|---|---|---|
# | `keep_latest` | `(dict, dict) -> dict` | `at` 큰 쪽 | `at` 동률 → 왼쪽 승 | `(at, src_rank, id)` 전순서 키 |
# | `keep_best` | `(dict, dict) -> dict` | `conf` 큰 쪽 | `conf` 동률 → 왼쪽 승 | `(conf, src_rank, cat)` 전순서 키 |
# | `merge_dict` | `(dict, dict) -> dict` | 키 단위 병합 | 겹친 키에서 나중이 승 | 값마다 `(at, src)`를 달고 키별 최대값 |
# | `collect_unique` | `(list, list) -> list` | 중복 제거 이어 붙이기 | 첫 등장 순서가 인자 순서 | 정규 순서로 정렬(또는 순서에 의미 부여 금지) |
#
# 19장 본문의 표현을 그대로 빌리면, **"순서에 기대는 리듀서는 내가 예상한 답을 안 낸다."**
# 실행기 버전이 올라가면 순서가 또 바뀔 수 있으니, 값 안에 시각·출처·신뢰도를 담고
# 리듀서가 그것만 보고 결정하게 해야 한다.
