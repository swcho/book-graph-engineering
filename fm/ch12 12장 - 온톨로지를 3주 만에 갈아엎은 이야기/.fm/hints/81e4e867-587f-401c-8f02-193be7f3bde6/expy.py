# %% [markdown]
# # `ex5_schema_drift.py`의 `audit()` — 스키마 드리프트를 집합 연산으로 재기
#
# 12장 예제 5의 `audit()`는 **문서(선언 스키마)** 와 **데이터(실제 레코드에 나타난 키)** 를
# 맞대어 세 가지를 계산한다.
#
# 1. **라벨별 레코드 건수** — 각 라벨(`Part`, `Product`, `Supplier`)에 몇 건이 있는가
# 2. **`+` 선언에 없는 키** — 데이터에는 있는데 문서에는 없는 키 (몇 건에 나타났는지도 함께)
# 3. **`-` 빠진 키** — 문서가 필수라고 선언했는데 일부 레코드에 없는 키 (몇 건에서 누락인지도 함께)
#
# 이 노트북은 외부 DB 없이 순수 파이썬으로 `audit()`를 재현하고,
# 주차별 스냅샷을 쌓아 드리프트가 **누적되는** 모습을 보여 준다.
#
# 필요 패키지: plotly (시각화), kaleido (PNG 저장). 감사 로직 자체는 표준 라이브러리만 쓴다.

# %%
from collections import Counter, defaultdict


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
# ## 1. 입력 — 선언 스키마와 실제 레코드
#
# 책의 예제와 같은 데이터다. `DECLARED`는 설계 문서, `ACTUAL_ROWS`는 운영 6개월 뒤 데이터.

# %%
DECLARED = {
    "Part": {"id", "name", "category"},
    "Product": {"id", "name", "released_on"},
    "Supplier": {"id", "name"},
}

ACTUAL_ROWS = [
    ("Part", {"id", "name", "category"}),
    ("Part", {"id", "name", "category", "legacy_code"}),
    ("Part", {"id", "name", "category", "legacy_code", "temp_flag"}),
    ("Part", {"id", "name"}),  # category 가 빠졌다
    ("Part", {"id", "name", "category", "note"}),
    ("Product", {"id", "name", "released_on"}),
    ("Product", {"id", "name", "released_on", "recall_reason"}),
    ("Product", {"id", "name"}),
    ("Supplier", {"id", "name", "contact"}),
    ("Supplier", {"id", "name", "contact", "tier"}),
]

for label, want in DECLARED.items():
    n = sum(1 for lb, _ in ACTUAL_ROWS if lb == label)
    print(f"{label:<9} 선언 {sorted(want)}  실제 {n}건")
# 출력: Part      선언 ['category', 'id', 'name']  실제 5건
# 출력: Product   선언 ['id', 'name', 'released_on']  실제 3건
# 출력: Supplier  선언 ['id', 'name']  실제 2건

# %% [markdown]
# ## 2. 수식 — `audit()`가 계산하는 집합 연산
#
# 라벨 $L$에 대해 레코드 집합을 $R_L = \{r_1, r_2, \dots, r_n\}$이라 하자.
# 각 $r_i$는 그 레코드가 **실제로 가진 키의 집합**이고, $n = |R_L|$이 **건수**다.
#
# 선언 스키마를 $D_L$이라 하면,
#
# $$
# U_L \;=\; \bigcup_{i=1}^{n} r_i
# \qquad\text{(관측 키 합집합 — 한 번이라도 나타난 키)}
# $$
#
# $$
# I_L \;=\; \bigcap_{i=1}^{n} r_i
# \qquad\text{(모든 레코드가 공통으로 가진 키)}
# $$
#
# 이제 감사 결과 두 축은 각각 **차집합** 하나다.
#
# $$
# \boxed{\;E_L \;=\; U_L \setminus D_L\;}
# \qquad\text{(\texttt{+} 선언에 없는 키)}
# $$
#
# $$
# \boxed{\;M_L \;=\; D_L \setminus I_L\;}
# \qquad\text{(\texttt{-} 빠진 키)}
# $$
#
# 각 키의 **출현 횟수**를 $c_L(k) = \left|\{\, i : k \in r_i \,\}\right|$라 두면,
# 보고서에 붙는 숫자는
#
# $$
# \text{extra}[k] = c_L(k) \quad (k \in E_L),
# \qquad
# \text{missing}[k] = n - c_L(k) \quad (k \in M_L)
# $$
#
# 코드의 `missing` 조건 `got.get(k, 0) < n` 은 곧 $c_L(k) < n \iff k \notin I_L$ 과 같다.
# 즉 **선언 필수 키 중 모든 레코드가 공유하지 못한 키**가 `-`다.
#
# 커버리지 비율 $\mathrm{cov}_L(k) = c_L(k) / n$ 로 보면
# $k \in I_L \iff \mathrm{cov}_L(k) = 1$, $k \in U_L \iff \mathrm{cov}_L(k) > 0$ 이다.

# %%
def audit(declared, rows):
    """ex5_schema_drift.py 의 audit() 를 그대로 재현 (의존성 없음)."""
    seen = defaultdict(Counter)  # seen[label][key] = c_L(k)
    counts = Counter()  # counts[label] = n
    for label, keys in rows:
        counts[label] += 1
        for k in keys:
            seen[label][k] += 1

    report = {}
    for label, want in declared.items():
        got = seen[label]
        n = counts[label]
        extra = {k: v for k, v in got.items() if k not in want}  # U_L \ D_L
        missing = {k: n - got.get(k, 0) for k in want if got.get(k, 0) < n}  # D_L \ I_L
        report[label] = {"건수": n, "선언에 없는 키": extra, "빠진 키": missing}
    return report


def print_report(rep):
    for label, r in rep.items():
        print(f"[{label}]  {r['건수']}건")
        for k, v in sorted(r["선언에 없는 키"].items(), key=lambda x: -x[1]):
            print(f"    + {k:<14} {v}건 — 문서에 없다")
        for k, v in sorted(r["빠진 키"].items(), key=lambda x: -x[1]):
            print(f"    - {k:<14} {v}건에서 누락")
        if not r["선언에 없는 키"] and not r["빠진 키"]:
            print("    문서와 일치")
        print()


print_report(audit(DECLARED, ACTUAL_ROWS))
# 출력: [Part]  5건
# 출력:     + legacy_code    2건 — 문서에 없다
# 출력:     + temp_flag      1건 — 문서에 없다
# 출력:     + note           1건 — 문서에 없다
# 출력:     - category       1건에서 누락
# 출력:
# 출력: [Product]  3건
# 출력:     + recall_reason  1건 — 문서에 없다
# 출력:     - released_on    1건에서 누락
# 출력:
# 출력: [Supplier]  2건
# 출력:     + contact        2건 — 문서에 없다
# 출력:     + tier           1건 — 문서에 없다
# 출력:

# %% [markdown]
# ## 3. 단계별 해부 — `Part` 라벨 하나만 손으로 따라가기
#
# $U_L$, $I_L$, $D_L$ 세 집합을 직접 만들어 두 차집합이 어떻게 나오는지 확인한다.

# %%
def dissect(label, declared, rows):
    recs = [keys for lb, keys in rows if lb == label]
    n = len(recs)
    D = declared[label]
    U = set().union(*recs) if recs else set()
    I = set.intersection(*recs) if recs else set()
    c = Counter(k for r in recs for k in r)
    print(f"라벨 {label}  n = {n}")
    print(f"  D  선언 스키마        = {sorted(D)}")
    print(f"  U  관측 키 합집합     = {sorted(U)}")
    print(f"  I  전건 공통 키       = {sorted(I)}")
    print(f"  E  = U \\ D  (+)      = {sorted(U - D)}")
    print(f"  M  = D \\ I  (-)      = {sorted(D - I)}")
    print(f"  커버리지 c(k)/n       = " + ", ".join(f"{k}:{c[k]}/{n}" for k in sorted(U)))
    return {"n": n, "D": D, "U": U, "I": I, "E": U - D, "M": D - I, "c": c}


_ = dissect("Part", DECLARED, ACTUAL_ROWS)
# 출력: 라벨 Part  n = 5
# 출력:   D  선언 스키마        = ['category', 'id', 'name']
# 출력:   U  관측 키 합집합     = ['category', 'id', 'legacy_code', 'name', 'note', 'temp_flag']
# 출력:   I  전건 공통 키       = ['id', 'name']
# 출력:   E  = U \ D  (+)      = ['legacy_code', 'note', 'temp_flag']
# 출력:   M  = D \ I  (-)      = ['category']
# 출력:   커버리지 c(k)/n       = category:4/5, id:5/5, legacy_code:2/5, name:5/5, note:1/5, temp_flag:1/5

# %% [markdown]
# 읽는 법.
#
# - `+ legacy_code` — 이전 시스템 잔재. 별도 영역으로 옮길 후보.
# - `+ temp_flag` — 임시로 넣고 잊은 것. 지울 후보.
# - `+ note` — 아직 판단 보류. 다음 주에 늘면 정식 편입 후보.
# - `- category` — **더 급하다.** 선언한 필수 키가 5건 중 1건에 없다.
#   `WHERE category = ...` 같은 질의가 그 1건을 **조용히** 빼먹고 있다는 뜻이다.

# %% [markdown]
# ## 4. 주차별 스냅샷 — 드리프트는 쌓인다
#
# 감사를 한 번 돌리면 사진 한 장이다. 매주 돌리면 **추세**가 보인다.
# 아래는 `Part` 라벨에 레코드가 주차별로 누적되는 합성 시나리오다.
# (각 주에 새 레코드가 들어오고, 이전 주 레코드는 그대로 남는다.)

# %%
WEEKLY_NEW = {
    "W1": [
        {"id", "name", "category"},
        {"id", "name", "category"},
    ],
    "W2": [
        {"id", "name", "category"},
        {"id", "name", "category", "legacy_code"},  # 이관 배치가 남긴 키
    ],
    "W3": [
        {"id", "name", "category", "legacy_code"},
        {"id", "name"},  # category 누락 시작
    ],
    "W4": [
        {"id", "name", "category", "legacy_code", "temp_flag"},  # 임시 플래그
        {"id", "name", "category"},
    ],
    "W5": [
        {"id", "name", "category", "note"},
        {"id", "name", "legacy_code"},  # category 또 누락
    ],
    "W6": [
        {"id", "name", "category", "note", "supplier_id"},  # 새 관계 키
        {"id", "name", "category", "note"},
    ],
}

WEEKS = list(WEEKLY_NEW)
snapshots = {}  # 주차 -> 그 시점까지 누적된 rows
_acc = []
for w in WEEKS:
    _acc = _acc + [("Part", keys) for keys in WEEKLY_NEW[w]]
    snapshots[w] = list(_acc)

history = {}
for w in WEEKS:
    rep = audit({"Part": DECLARED["Part"]}, snapshots[w])["Part"]
    history[w] = rep
    plus = ", ".join(f"{k}({v})" for k, v in sorted(rep["선언에 없는 키"].items()))
    minus = ", ".join(f"{k}({v})" for k, v in sorted(rep["빠진 키"].items()))
    print(f"{w}  n={rep['건수']:>2}  + [{plus or '-없음-'}]   - [{minus or '-없음-'}]")
# 출력: W1  n= 2  + [-없음-]   - [-없음-]
# 출력: W2  n= 4  + [legacy_code(1)]   - [-없음-]
# 출력: W3  n= 6  + [legacy_code(2)]   - [category(1)]
# 출력: W4  n= 8  + [legacy_code(3), temp_flag(1)]   - [category(1)]
# 출력: W5  n=10  + [legacy_code(4), note(1), temp_flag(1)]   - [category(2)]
# 출력: W6  n=12  + [legacy_code(4), note(3), supplier_id(1), temp_flag(1)]   - [category(2)]

# %% [markdown]
# W1은 「문서와 일치」다. 6주 뒤에는 미선언 키가 4종, 누락 건이 2건.
# **한 주도 요란하게 깨지지 않았다**는 점이 핵심이다.
# 드리프트는 사고가 아니라 침식이라, 배치 감사 없이는 눈에 띄지 않는다.

# %% [markdown]
# ## 5. 시각화 — 주차별 `+`/`-` 추이와 키 커버리지 히트맵
#
# 위: 주차별 미선언 키 **종수**와 누락 **건수**.
# 아래: 키별 커버리지 $\mathrm{cov}(k) = c(k)/n$ 히트맵.
# 선언 키가 1.00에서 떨어지면 `-`, 선언에 없는 키가 0을 넘으면 `+`다.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#898781", "#e1e0d9", "#fcfcfb"
BLUE_RAMP = [[0.0, "#fcfcfb"], [0.25, "#cde2fb"], [0.6, "#3987e5"], [1.0, "#0d366b"]]

extra_kinds = [len(history[w]["선언에 없는 키"]) for w in WEEKS]
missing_hits = [sum(history[w]["빠진 키"].values()) for w in WEEKS]

all_keys = sorted({k for w in WEEKS for k in audit({"Part": DECLARED["Part"]}, snapshots[w])["Part"]["선언에 없는 키"]})
key_order = sorted(DECLARED["Part"]) + all_keys
cov = []
for k in key_order:
    row = []
    for w in WEEKS:
        recs = [keys for _, keys in snapshots[w]]
        row.append(sum(1 for r in recs if k in r) / len(recs))
    cov.append(row)

fig = make_subplots(
    rows=2,
    cols=1,
    row_heights=[0.44, 0.56],
    vertical_spacing=0.14,
    subplot_titles=("주차별 드리프트 추이 (Part)", "키 커버리지 c(k)/n — 1.00 미만이면 누락"),
)
fig.add_trace(
    go.Scatter(
        x=WEEKS, y=extra_kinds, name="+ 선언에 없는 키 (종수)", mode="lines+markers",
        line=dict(color=BLUE, width=2), marker=dict(size=9, color=BLUE),
        hovertemplate="%{x}<br>미선언 키 %{y}종<extra></extra>",
    ),
    row=1, col=1,
)
fig.add_trace(
    go.Scatter(
        x=WEEKS, y=missing_hits, name="- 빠진 키 (누락 건수)", mode="lines+markers",
        line=dict(color=ORANGE, width=2), marker=dict(size=9, color=ORANGE),
        hovertemplate="%{x}<br>누락 %{y}건<extra></extra>",
    ),
    row=1, col=1,
)
fig.add_trace(
    go.Heatmap(
        z=cov, x=WEEKS, y=key_order, colorscale=BLUE_RAMP, zmin=0, zmax=1,
        xgap=2, ygap=2, colorbar=dict(title="cov", len=0.5, y=0.22, thickness=12),
        hovertemplate="%{y} · %{x}<br>커버리지 %{z:.2f}<extra></extra>",
        text=[[f"{v:.2f}" for v in row] for row in cov],
        texttemplate="%{text}", textfont=dict(size=10),
    ),
    row=2, col=1,
)
fig.add_annotation(
    x=WEEKS[-1], y=extra_kinds[-1], text=f"{extra_kinds[-1]}종", showarrow=False,
    xshift=22, font=dict(color=INK, size=11), row=1, col=1,
)
fig.add_annotation(
    x=WEEKS[-1], y=missing_hits[-1], text=f"{missing_hits[-1]}건", showarrow=False,
    xshift=22, font=dict(color=INK, size=11), row=1, col=1,
)
fig.update_layout(
    title=dict(text="스키마 드리프트 감사 — audit() 결과의 주차별 변화", font=dict(size=17, color=INK)),
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
    font=dict(color=INK, size=12),
    legend=dict(orientation="h", yanchor="top", y=-0.07, x=0),
    width=880, height=700, margin=dict(l=110, r=70, t=90, b=90),
)
fig.update_xaxes(showgrid=False, linecolor=GRID, tickfont=dict(color=MUTED))
fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False, tickfont=dict(color=MUTED), row=1, col=1)
fig.update_yaxes(showgrid=False, tickfont=dict(color=MUTED), row=2, col=1)

_show(fig)

import os

_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
_png = os.path.join(_here, "expy.png")
try:
    fig.write_image(_png, scale=2)
    print(f"저장: {_png}")
except Exception as e:  # kaleido 미설치 등
    print(f"PNG 저장 실패 (kaleido 필요): {e}")
# 출력: 저장: .../expy.png

# %% [markdown]
# ## 6. 실제 그래프 DB에서 「관측 키」 뽑기
#
# 위 노트북은 `ACTUAL_ROWS`를 손으로 적었지만, 운영에서는 그래프 DB에 직접 물어본다.
# 아래는 라벨별 $c_L(k)$와 $n$을 뽑는 질의 뼈대다(실행하지 않고 문자열로만 둔다).

# %%
NEO4J_APOC = """
// Neo4j — 노드마다 실제 키 목록을 펼쳐 라벨별로 센다
MATCH (n:Part)
WITH count(n) AS n_total, collect(keys(n)) AS all_keys
UNWIND all_keys AS ks
UNWIND ks AS k
RETURN k AS key, count(*) AS c, n_total, toFloat(count(*)) / n_total AS coverage
ORDER BY coverage ASC, key
"""

NEO4J_SCHEMA = """
// 선언 스키마 쪽 (D_L) — 제약/인덱스로 선언된 것
SHOW CONSTRAINTS YIELD labelsOrTypes, properties
RETURN labelsOrTypes, properties
"""

KUZU = """
-- Kuzu 는 스키마가 고정이라 «미선언 키»가 애초에 들어오지 못한다.
-- 대신 «선언했지만 비어 있는 필수 키»(= M_L)를 NULL 비율로 잰다.
CALL TABLE_INFO('Part') RETURN *;          -- D_L: 선언된 컬럼 목록

MATCH (p:Part)
RETURN count(*)                                   AS n,
       count(p.category)                          AS c_category,
       1.0 * count(p.category) / count(*)         AS cov_category;
-- Kuzu 에서 드리프트는 «키가 늘어나는» 형태가 아니라
-- «적재 스크립트가 자꾸 실패한다 / 컬럼이 NULL 로 찬다» 형태로 나타난다.
"""

SPARQL = """
# SPARQL — 술어(predicate)가 곧 키다
SELECT ?p (COUNT(DISTINCT ?s) AS ?c)
WHERE {
  ?s a ex:Part .
  ?s ?p ?o .
}
GROUP BY ?p
ORDER BY ?c

# n (분모)
SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a ex:Part }

# SHACL 을 쓰면 M_L 은 sh:minCount 위반 보고서로 바로 나온다:
#   ex:PartShape a sh:NodeShape ; sh:targetClass ex:Part ;
#     sh:property [ sh:path ex:category ; sh:minCount 1 ] .
# E_L(미선언 키)은 sh:closed true 로 잡는다.
"""

for name, q in [("Neo4j/APOC", NEO4J_APOC), ("Neo4j 제약", NEO4J_SCHEMA), ("Kuzu", KUZU), ("SPARQL", SPARQL)]:
    print(f"--- {name} ---")
    print(q.strip())
    print()
# 출력: 각 질의 문자열이 그대로 출력된다 (README 의 「그래프 DB 질의」 절 참고)

# %% [markdown]
# ## 정리
#
# - `audit()`가 계산하는 것: **라벨별 건수 $n$**, **`+` $E_L = U_L \setminus D_L$**, **`-` $M_L = D_L \setminus I_L$**.
# - `+`는 셋 중 하나로 처리한다 — 정식 편입 / 삭제 / 별도 영역 이관.
# - `-`는 더 급하다. 질의가 조용히 빈 결과를 내고 있다는 신호다.
# - 30줄짜리 배치를 매주 돌리면, 6주 뒤에 놀랄 일이 없다.
#   **문서는 거짓말을 하고 데이터는 안 한다.**
