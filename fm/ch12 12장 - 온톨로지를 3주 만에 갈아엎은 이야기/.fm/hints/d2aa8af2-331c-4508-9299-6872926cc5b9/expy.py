# %% [markdown]
# # A안(깊은 분류) vs B안(얕은 분류) — 스키마와 질의문은 몇 배로 늘어나는가
#
# 12장 `ex2_deep_vs_flat.py`의 **A안(깊은 분류)** 은 이런 구조다.
#
# - `Bolt`, `Nut`, `Resistor`, `Capacitor` 를 **각각 별도의 노드 테이블**로 둔다.
# - `Product` 와의 관계도 `UsesBolt`, `UsesNut`, `UsesResistor`, `UsesCapacitor` 처럼
#   **부품 종류마다 별도의 관계 테이블**로 둔다.
#
# 반면 **B안(얕은 분류)** 은 `Part` 노드 테이블 하나에 `category` 속성을 두고,
# 관계는 `Uses` 하나만 둔다.
#
# 두 안은 「제품 P1 이 쓰는 부품 전부」라는 **같은 답**을 낸다.
# 다른 것은 답이 아니라 **비용**이다. 부품 종류 수 $N$ 에 대해 그 비용이
# 어떻게 늘어나는지를 순수 파이썬으로 스키마와 Cypher 문자열을 조립해 세어 본다.
#
# 필요 패키지: plotly, kaleido (그래프 저장용). 없어도 계산/출력 부분은 그대로 동작한다.
# kuzu 같은 DB 엔진은 쓰지 않는다 — 세는 것이 목적이므로 문자열만 만든다.

# %%
from __future__ import annotations


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# 12장 예제에 나오는 부품 종류(영문 라벨, 한글 이름, category)
PART_KINDS = [
    ("Bolt", "M6 볼트", "체결"),
    ("Nut", "M6 너트", "체결"),
    ("Resistor", "10k 저항", "전자"),
    ("Capacitor", "100uF 커패시터", "전자"),
    # 여기서부터는 「나중에 늘어나는 종류」다
    ("Washer", "M6 와셔", "체결"),
    ("Rivet", "3mm 리벳", "체결"),
    ("Diode", "1N4148 다이오드", "전자"),
    ("Transistor", "2N2222 트랜지스터", "전자"),
    ("Mosfet", "N채널 MOSFET", "전자"),
    ("Screw", "M3 나사", "체결"),
]

print(f"준비된 부품 종류 수: {len(PART_KINDS)}")
# 출력: 준비된 부품 종류 수: 10


# %% [markdown]
# ## 1. A안(깊은 분류)의 스키마를 생성한다
#
# 종류 하나가 늘 때마다 **노드 테이블 1개 + 관계 테이블 1개**가 늘어난다.
#
# $$\text{A안 노드 테이블} = N + 1 \quad (\text{Product 1개 포함})$$
# $$\text{A안 관계 테이블} = N$$

# %%
def deep_schema(kinds):
    """A안 — 종류마다 노드 테이블, 종류마다 관계 테이블."""
    nodes = [
        f"CREATE NODE TABLE {k}(id STRING, name STRING, PRIMARY KEY(id))"
        for k, _, _ in kinds
    ]
    nodes.append("CREATE NODE TABLE Product(id STRING, PRIMARY KEY(id))")
    rels = [f"CREATE REL TABLE Uses{k}(FROM Product TO {k})" for k, _, _ in kinds]
    return nodes, rels


nodes4, rels4 = deep_schema(PART_KINDS[:4])
print("[A안 · N=4] 노드 테이블")
for s in nodes4:
    print("  " + s)
print("[A안 · N=4] 관계 테이블")
for s in rels4:
    print("  " + s)
# 출력:
# [A안 · N=4] 노드 테이블
#   CREATE NODE TABLE Bolt(id STRING, name STRING, PRIMARY KEY(id))
#   CREATE NODE TABLE Nut(id STRING, name STRING, PRIMARY KEY(id))
#   CREATE NODE TABLE Resistor(id STRING, name STRING, PRIMARY KEY(id))
#   CREATE NODE TABLE Capacitor(id STRING, name STRING, PRIMARY KEY(id))
#   CREATE NODE TABLE Product(id STRING, PRIMARY KEY(id))
# [A안 · N=4] 관계 테이블
#   CREATE REL TABLE UsesBolt(FROM Product TO Bolt)
#   CREATE REL TABLE UsesNut(FROM Product TO Nut)
#   CREATE REL TABLE UsesResistor(FROM Product TO Resistor)
#   CREATE REL TABLE UsesCapacitor(FROM Product TO Capacitor)


# %% [markdown]
# ## 2. B안(얕은 분류)의 스키마를 생성한다
#
# $N$ 이 아무리 커져도 그대로다. 종류는 테이블이 아니라 `category` **속성값**이 된다.
#
# $$\text{B안 노드 테이블} = 2,\qquad \text{B안 관계 테이블} = 1$$

# %%
def flat_schema(kinds):
    """B안 — Part 하나 + category 속성, Uses 하나. kinds 를 받지만 결과는 상수다."""
    nodes = [
        "CREATE NODE TABLE Part(id STRING, name STRING, category STRING, PRIMARY KEY(id))",
        "CREATE NODE TABLE Product(id STRING, PRIMARY KEY(id))",
    ]
    rels = ["CREATE REL TABLE Uses(FROM Product TO Part)"]
    return nodes, rels


fn, fr = flat_schema(PART_KINDS[:4])
for s in fn + fr:
    print("  " + s)
print(f"N=4 일 때 {len(fn + fr)}개, N=10 일 때 {len(sum(flat_schema(PART_KINDS), []))}개")
# 출력:
#   CREATE NODE TABLE Part(id STRING, name STRING, category STRING, PRIMARY KEY(id))
#   CREATE NODE TABLE Product(id STRING, PRIMARY KEY(id))
#   CREATE REL TABLE Uses(FROM Product TO Part)
# N=4 일 때 3개, N=10 일 때 3개


# %% [markdown]
# ## 3. 같은 질문을 두 안으로 각각 물어본다
#
# 질문: **「제품 P1 이 쓰는 부품 전부」**
#
# A안은 관계 테이블이 종류마다 다르므로 `MATCH` 를 종류 수만큼 쓰고 `UNION` 으로 잇는다.
#
# $$L_A(N) = N + (N-1) = 2N - 1 \ \text{줄}$$
#
# B안은 라벨이 하나뿐이라 $N$ 과 무관하게 한 줄이다.
#
# $$L_B(N) = 1 \ \text{줄}$$

# %%
def deep_query(kinds, product="P1"):
    """A안 — 종류마다 MATCH 한 줄, 사이를 UNION 으로 잇는다."""
    parts = [
        f"MATCH (p:Product {{id:'{product}'}})-[:Uses{k}]->(x:{k}) RETURN x.name AS 부품"
        for k, _, _ in kinds
    ]
    return "\nUNION\n".join(parts)


def flat_query(kinds=None, product="P1"):
    """B안 — 종류가 몇 개든 한 줄."""
    return f"MATCH (p:Product {{id:'{product}'}})-[:Uses]->(x:Part) RETURN x.name AS 부품"


def line_count(q):
    return q.strip().count("\n") + 1


print("── A안 질의문 (N=4) ──")
print(deep_query(PART_KINDS[:4]))
print("\n── B안 질의문 (N=4) ──")
print(flat_query())
print(f"\n줄 수: A안 {line_count(deep_query(PART_KINDS[:4]))} / B안 {line_count(flat_query())}")
# 출력:
# ── A안 질의문 (N=4) ──
# MATCH (p:Product {id:'P1'})-[:UsesBolt]->(x:Bolt) RETURN x.name AS 부품
# UNION
# MATCH (p:Product {id:'P1'})-[:UsesNut]->(x:Nut) RETURN x.name AS 부품
# UNION
# MATCH (p:Product {id:'P1'})-[:UsesResistor]->(x:Resistor) RETURN x.name AS 부품
# UNION
# MATCH (p:Product {id:'P1'})-[:UsesCapacitor]->(x:Capacitor) RETURN x.name AS 부품
#
# ── B안 질의문 (N=4) ──
# MATCH (p:Product {id:'P1'})-[:Uses]->(x:Part) RETURN x.name AS 부품
#
# 줄 수: A안 7 / B안 1


# %% [markdown]
# ## 4. 「와셔를 하나 추가한다」 — 고칠 곳이 몇 군데인가
#
# A안은 세 군데(노드 테이블 DDL, 관계 테이블 DDL, 질의문의 UNION 한 줄)를 고쳐야 한다.
# B안은 **행 하나를 넣으면 끝**이다. 스키마도 질의문도 그대로다.

# %%
def diff_report(before, after):
    dn_b, dr_b = deep_schema(before)
    dn_a, dr_a = deep_schema(after)
    ddl_delta = len(set(dn_a + dr_a) - set(dn_b + dr_b))
    q_delta = line_count(deep_query(after)) - line_count(deep_query(before))
    return ddl_delta, q_delta


ddl_delta, q_delta = diff_report(PART_KINDS[:4], PART_KINDS[:5])
print(f"A안: DDL {ddl_delta}개 추가, 질의문 {q_delta}줄 증가  → 고칠 곳 {ddl_delta + 1}군데")
print("  추가되는 DDL:")
for s in sorted(
    set(sum(deep_schema(PART_KINDS[:5]), [])) - set(sum(deep_schema(PART_KINDS[:4]), []))
):
    print("    " + s)
print("B안: DDL 0개 추가, 질의문 0줄 증가  → 고칠 곳 0군데")
print("  추가되는 데이터 한 줄:")
k, name, cat = PART_KINDS[4]
print(f"    CREATE (:Part {{id:'W1', name:'{name}', category:'{cat}'}})")
# 출력:
# A안: DDL 2개 추가, 질의문 2줄 증가  → 고칠 곳 3군데
#   추가되는 DDL:
#     CREATE NODE TABLE Washer(id STRING, name STRING, PRIMARY KEY(id))
#     CREATE REL TABLE UsesWasher(FROM Product TO Washer)
# B안: DDL 0개 추가, 질의문 0줄 증가  → 고칠 곳 0군데
#   추가되는 데이터 한 줄:
#     CREATE (:Part {id:'W1', name:'M6 와셔', category:'체결'})


# %% [markdown]
# ## 5. $N$ 을 1부터 10까지 늘려 가며 표로 본다
#
# | 지표 | A안 | B안 |
# |---|---|---|
# | 노드 테이블 | $N+1$ | $2$ |
# | 관계 테이블 | $N$ | $1$ |
# | 스키마 DDL 합계 | $2N+1$ | $3$ |
# | 질의문 줄 수 | $2N-1$ | $1$ |

# %%
Ns = list(range(1, len(PART_KINDS) + 1))
rows = []
for n in Ns:
    ks = PART_KINDS[:n]
    dn, dr = deep_schema(ks)
    fnn, frr = flat_schema(ks)
    rows.append(
        {
            "N": n,
            "A_ddl": len(dn) + len(dr),
            "B_ddl": len(fnn) + len(frr),
            "A_q": line_count(deep_query(ks)),
            "B_q": line_count(flat_query()),
        }
    )

print(f"{'N':>3} {'A안 DDL':>8} {'B안 DDL':>8} {'A안 질의줄':>10} {'B안 질의줄':>10}")
print("-" * 44)
for r in rows:
    print(f"{r['N']:>3} {r['A_ddl']:>8} {r['B_ddl']:>8} {r['A_q']:>10} {r['B_q']:>10}")

# 공식과 실제 생성 결과가 맞는지 검증
assert all(r["A_ddl"] == 2 * r["N"] + 1 for r in rows)
assert all(r["A_q"] == 2 * r["N"] - 1 for r in rows)
assert all(r["B_ddl"] == 3 and r["B_q"] == 1 for r in rows)
print("\n공식 검증 통과: A안 DDL=2N+1, A안 질의줄=2N-1, B안=상수")
# 출력:
#   N   A안 DDL   B안 DDL    A안 질의줄     B안 질의줄
# --------------------------------------------
#   1        3        3          1          1
#   2        5        3          3          1
#   3        7        3          5          1
#   4        9        3          7          1
#   5       11        3          9          1
#   6       13        3         11          1
#   7       15        3         13          1
#   8       17        3         15          1
#   9       19        3         17          1
#  10       21        3         19          1
#
# 공식 검증 통과: A안 DDL=2N+1, A안 질의줄=2N-1, B안=상수


# %% [markdown]
# $N=1$ 일 때는 두 안이 똑같이 3개다. **종류가 하나뿐이면 깊은 분류라는 개념 자체가 없다.**
# 갈라지는 것은 종류가 늘어나기 시작하면서이고, 그 뒤로는 A안만 선형으로 자란다.

# %% [markdown]
# ## 6. 그래프로 본다

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("스키마 DDL 문 개수", "「부품 전부」 질의문 줄 수"),
    )
    style_a = dict(mode="lines+markers", line=dict(color="#d1495b", width=3))
    style_b = dict(mode="lines+markers", line=dict(color="#2a9d8f", width=3))

    fig.add_trace(
        go.Scatter(x=Ns, y=[r["A_ddl"] for r in rows], name="A안 (깊은 분류)", **style_a),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=Ns, y=[r["B_ddl"] for r in rows], name="B안 (얕은 분류)", **style_b),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=Ns, y=[r["A_q"] for r in rows], name="A안 (깊은 분류)", showlegend=False, **style_a
        ),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=Ns, y=[r["B_q"] for r in rows], name="B안 (얕은 분류)", showlegend=False, **style_b
        ),
        row=1,
        col=2,
    )
    fig.update_xaxes(title_text="부품 종류 수 N", row=1, col=1)
    fig.update_xaxes(title_text="부품 종류 수 N", row=1, col=2)
    fig.update_yaxes(title_text="개수", row=1, col=1)
    fig.update_yaxes(title_text="줄 수", row=1, col=2)
    fig.update_layout(
        title="A안(깊은 분류)만 N 에 비례해 자란다 — 2N+1 과 2N-1",
        template="plotly_white",
        width=1000,
        height=460,
    )
    _show(fig)

    import os

    png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
    fig.write_image(png, scale=2)
    print(f"저장: {png}")
except ImportError as e:
    print(f"plotly/kaleido 없음 — 그래프 생략 ({e})")
# 출력: 저장: .../expy.png


# %% [markdown]
# ## 7. 그럼 A안은 무조건 나쁜가 — 아니다
#
# 12장의 결론은 「얕게 하라」가 아니라 **분류를 나누는 기준**에 관한 것이다.
#
# > 분류를 나누는 기준은 「다른 속성을 갖는가」이지 「다른 물건인가」가 아니다.
#
# 볼트에만 있는 속성(나사산 규격, 강도 등급)이 많고 **그 속성으로 질의한다면**
# A안이 맞다. 아래처럼 종류별 고유 속성이 있으면 B안은 `Part` 테이블에
# 대부분 NULL 인 열이 쌓이거나 스키마 없는 `props` 자루가 된다.

# %%
UNIQUE_PROPS = {
    "Bolt": ["thread_spec", "grade", "head_type"],
    "Nut": ["thread_spec", "grade"],
    "Resistor": ["ohm", "tolerance", "power_w"],
    "Capacitor": ["farad", "voltage", "dielectric"],
}
공유속성 = set.intersection(*(set(v) for v in UNIQUE_PROPS.values()))
전체속성 = set().union(*(set(v) for v in UNIQUE_PROPS.values()))
print(f"전체 속성 {len(전체속성)}개 중 모든 종류가 공유하는 속성: {len(공유속성)}개 {sorted(공유속성)}")
희소도 = 1 - sum(len(v) for v in UNIQUE_PROPS.values()) / (
    len(UNIQUE_PROPS) * len(전체속성)
)
print(f"B안 한 테이블에 다 넣을 때 NULL 비율: {희소도:.0%}")
print(
    "\nNULL 비율이 높고 그 속성으로 질의한다 → A안(쪼갠다)\n"
    "속성이 거의 같고 종류가 자주 는다      → B안(속성으로 둔다)"
)
# 출력:
# 전체 속성 9개 중 모든 종류가 공유하는 속성: 0개 []
# B안 한 테이블에 다 넣을 때 NULL 비율: 69%
#
# NULL 비율이 높고 그 속성으로 질의한다 → A안(쪼갠다)
# 속성이 거의 같고 종류가 자주 는다      → B안(속성으로 둔다)
