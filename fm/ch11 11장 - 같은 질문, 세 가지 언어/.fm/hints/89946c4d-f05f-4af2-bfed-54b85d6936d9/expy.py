# %% [markdown]
# # `ex4_sql_pgq.py`의 평범한 SQL — 조인 4번을 한 단계씩 벗겨 보기
#
# 11장 예제 4는 SQL/PGQ 표준 문법을 **보여 주기만** 하고,
# 실제 답은 「같은 뜻의 평범한 SQL」로 계산한다. 그 SQL이 이것이다.
#
# ```sql
# SELECT DISTINCT c.name AS 고객
#   FROM company c
#   JOIN terminated t ON t.company_name = c.name
#   JOIN contract  o ON o.id = t.contract_id
#   JOIN signed    s ON s.company_name = c.name
#   JOIN contract  n ON n.id = s.contract_id
#  WHERE o.ended_on < n.started_on
#  ORDER BY 고객
# ```
#
# 이 노트북은 같은 테이블을 sqlite3에 다시 만들고,
# **조인을 하나씩 붙이면서 행 수를 세어** 어디서 중복이 생기고
# `WHERE` / `DISTINCT`가 무엇을 걷어내는지 눈으로 확인한다.
#
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용. sqlite3는 표준 라이브러리)

# %%
import sqlite3

# 11장 code/seed.py 와 같은 데이터
COMPANIES = [("가온테크", "A"), ("나루소프트", "B"), ("라온에너지", "C"), ("다올물산", "B")]
CONTRACTS = [
    ("M-2021-077", None, "2024-03-11"),   # 해지된 옛 계약
    ("C-2025-118", "2025-06-02", None),   # 살아 있는 새 계약
    ("C-2025-004", "2025-01-20", None),
    ("M-2020-031", None, "2024-08-05"),
    ("C-2026-010", "2026-02-01", None),
]
SIGNED = [("가온테크", "C-2025-118"), ("나루소프트", "C-2025-004"),
          ("다올물산", "C-2026-010")]
TERMINATED = [("가온테크", "M-2021-077"), ("라온에너지", "M-2020-031")]


def setup(signed=SIGNED, terminated=TERMINATED, contracts=CONTRACTS):
    con = sqlite3.connect(":memory:")
    con.executescript("""
        CREATE TABLE company (name TEXT PRIMARY KEY, grade TEXT);
        CREATE TABLE contract (id TEXT PRIMARY KEY, started_on TEXT, ended_on TEXT);
        CREATE TABLE signed (company_name TEXT, contract_id TEXT);
        CREATE TABLE terminated (company_name TEXT, contract_id TEXT);
    """)
    con.executemany("INSERT INTO company VALUES (?,?)", COMPANIES)
    con.executemany("INSERT INTO contract VALUES (?,?,?)", contracts)
    con.executemany("INSERT INTO signed VALUES (?,?)", signed)
    con.executemany("INSERT INTO terminated VALUES (?,?)", terminated)
    con.commit()
    return con


con = setup()
for t in ("company", "contract", "signed", "terminated"):
    n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"{t:<12} {n}행")
# 출력:
# company      4행
# contract     5행
# signed       3행
# terminated   2행

# %% [markdown]
# ## 조인 4단계가 이어 붙이는 것
#
# 그래프로 보면 답하고 싶은 그림은 이렇다.
#
# ```
#            Terminated            Signed
#   Company ────────────▶ Contract(o)   Company ────────▶ Contract(n)
#      c                                   c(같은 노드)
#                    조건: o.ended_on < n.started_on
# ```
#
# 관계형 테이블에는 「간선」이 없으니, 간선 테이블과 노드 테이블을 번갈아 조인해서
# 이 그림을 손으로 다시 세운다. 네 번의 조인은 각각 이런 일을 한다.
#
# | # | 조인 | 붙이는 것 | 그래프에서 대응 |
# |---|---|---|---|
# | 1 | `JOIN terminated t ON t.company_name = c.name` | 회사 → 해지 간선 | `(c)-[:Terminated]->` |
# | 2 | `JOIN contract o ON o.id = t.contract_id` | 해지 간선 → 옛 계약 노드 | `->(o:Contract)` |
# | 3 | `JOIN signed s ON s.company_name = c.name` | **같은** 회사 → 서명 간선 | `(c)-[:Signed]->` |
# | 4 | `JOIN contract n ON n.id = s.contract_id` | 서명 간선 → 새 계약 노드 | `->(n:Contract)` |
#
# 간선 하나를 따라가는 데 조인이 **두 번**(간선 테이블 + 노드 테이블) 든다.
# Cypher의 화살표 하나 = SQL의 조인 두 개. 이게 3장에서 말한 조인 폭발의 씨앗이다.
#
# 3번 조인이 다시 `c.name`을 기준으로 붙는 게 핵심이다.
# 여기서 「해지한 회사」와 「서명한 회사」가 **같은 회사**라는 제약이 걸린다.
# Cypher라면 변수 `c`를 두 패턴에 그냥 두 번 쓰면 끝나는 일이다.

# %%
# 조인을 하나씩 붙여 가며 중간 결과 행 수를 센다
STAGES = [
    ("1. company만",
     "SELECT c.name FROM company c"),
    ("2. + terminated",
     "SELECT c.name, t.contract_id FROM company c "
     "JOIN terminated t ON t.company_name = c.name"),
    ("3. + contract o",
     "SELECT c.name, o.id, o.ended_on FROM company c "
     "JOIN terminated t ON t.company_name = c.name "
     "JOIN contract o ON o.id = t.contract_id"),
    ("4. + signed",
     "SELECT c.name, o.id, s.contract_id FROM company c "
     "JOIN terminated t ON t.company_name = c.name "
     "JOIN contract o ON o.id = t.contract_id "
     "JOIN signed s ON s.company_name = c.name"),
    ("5. + contract n",
     "SELECT c.name, o.ended_on, n.started_on FROM company c "
     "JOIN terminated t ON t.company_name = c.name "
     "JOIN contract o ON o.id = t.contract_id "
     "JOIN signed s ON s.company_name = c.name "
     "JOIN contract n ON n.id = s.contract_id"),
    ("6. + WHERE o.ended_on < n.started_on",
     "SELECT c.name, o.ended_on, n.started_on FROM company c "
     "JOIN terminated t ON t.company_name = c.name "
     "JOIN contract o ON o.id = t.contract_id "
     "JOIN signed s ON s.company_name = c.name "
     "JOIN contract n ON n.id = s.contract_id "
     "WHERE o.ended_on < n.started_on"),
    ("7. + DISTINCT c.name",
     "SELECT DISTINCT c.name FROM company c "
     "JOIN terminated t ON t.company_name = c.name "
     "JOIN contract o ON o.id = t.contract_id "
     "JOIN signed s ON s.company_name = c.name "
     "JOIN contract n ON n.id = s.contract_id "
     "WHERE o.ended_on < n.started_on"),
]


def trace(con, label=""):
    counts = []
    print(f"--- {label} ---")
    for name, q in STAGES:
        rows = con.execute(q).fetchall()
        counts.append(len(rows))
        print(f"  {name:<38} {len(rows):>3}행")
    return counts


seed_counts = trace(con, "seed.py 원본 데이터")
# 출력:
# --- seed.py 원본 데이터 ---
#   1. company만                              4행
#   2. + terminated                          2행
#   3. + contract o                          2행
#   4. + signed                              1행
#   5. + contract n                          1행
#   6. + WHERE o.ended_on < n.started_on     1행
#   7. + DISTINCT c.name                     1행

# %% [markdown]
# ## 원본 데이터에서는 왜 아무것도 줄지 않았나
#
# `seed.py`는 회사마다 해지 계약이 0~1개, 서명 계약이 0~1개뿐이다.
# 그래서 곱집합이 커질 여지가 없다. 대신 다른 게 보인다.
#
# - 2단계에서 4행 → 2행: `terminated`에 없는 회사(나루소프트·다올물산)는 **탈락**한다.
#   `JOIN`은 inner join이므로 「해지 이력이 없는 회사」는 여기서 사라진다.
# - 4단계에서 2행 → 1행: 라온에너지는 해지만 하고 다시 서명하지 않아 여기서 탈락한다.
# - 남은 1행이 가온테크: `M-2021-077` 해지(2024-03-11) → `C-2025-118` 서명(2025-06-02).

# %%
for r in con.execute(STAGES[4][1]):     # WHERE 직전 5단계
    print(r)
# 출력:
# ('가온테크', '2024-03-11', '2025-06-02')

print("\n최종 답:", [r[0] for r in con.execute(STAGES[6][1] + " ORDER BY c.name")])
# 출력:
# 최종 답: ['가온테크']

# %% [markdown]
# ## `WHERE o.ended_on < n.started_on`의 의미 — 순서가 질문이다
#
# 이 한 줄이 질문의 전부다. 질문은 「해지한 적 있고 서명한 적 있는 고객」이 아니라
# **「해지했다가 그 *뒤에* 다시 계약한 고객」**이다. 시간 순서가 붙는다.
#
# $$\text{o.ended\_on} \;<\; \text{n.started\_on}$$
#
# 부등호를 뒤집으면 완전히 다른 질문(계약 갱신 중 옛 계약 정리)이 되고,
# 조건을 빼면 「해지 이력과 계약 이력이 둘 다 있는 고객」이 된다.
# 조인은 *어떤 사실들을 이어 붙일지*만 정하고, 부등호가 *어떤 사실 조합이 답인지*를 정한다.
#
# 여기 함정이 하나 더 있다. `ended_on`이나 `started_on`이 `NULL`이면
# 비교 결과가 `NULL`(= 참이 아님)이 되어 그 행은 조용히 탈락한다.
# `seed.py`에서 살아 있는 계약은 `ended_on = NULL`, 해지된 계약은 `started_on = NULL`이라
# 마침 원하는 대로 동작하지만, 이건 데이터가 그렇게 생겼기 때문일 뿐이다.

# %%
# 부등호를 바꿔 보면 답이 달라진다
BASE = ("FROM company c "
        "JOIN terminated t ON t.company_name = c.name "
        "JOIN contract o ON o.id = t.contract_id "
        "JOIN signed s ON s.company_name = c.name "
        "JOIN contract n ON n.id = s.contract_id ")
for label, cond in [("o.ended_on < n.started_on  (해지 후 재계약)", "WHERE o.ended_on < n.started_on"),
                    ("o.ended_on > n.started_on  (재계약 후 해지)", "WHERE o.ended_on > n.started_on"),
                    ("조건 없음               (둘 다 있는 고객)", "")]:
    rows = [r[0] for r in con.execute(f"SELECT DISTINCT c.name {BASE}{cond} ORDER BY c.name")]
    print(f"  {label:<34} {rows}")
# 출력:
#   o.ended_on < n.started_on  (해지 후 재계약) ['가온테크']
#   o.ended_on > n.started_on  (재계약 후 해지) []
#   조건 없음               (둘 다 있는 고객)    ['가온테크']

# %% [markdown]
# ## 중복은 어디서 오는가 — 계약을 늘려 보기
#
# `DISTINCT`가 왜 필요한지는 데이터를 조금만 현실적으로 만들면 바로 드러난다.
# 가온테크에 해지 계약 하나, 서명 계약 하나를 더 준다.
#
# 그러면 조인 결과는 **경로의 조합**이 되어 곱으로 늘어난다.
#
# $$\text{행 수}(c) \;=\; |{\text{해지 계약}}(c)| \times |{\text{서명 계약}}(c)|$$
#
# 가온테크는 $2 \times 2 = 4$행. 네 행 모두 `c.name = '가온테크'`다.
# 우리가 묻는 건 **회사 이름**뿐이라, 서로 다른 4개의 경로가 같은 답 하나로 겹친다.
# 이 겹침을 없애는 게 `DISTINCT`다.
#
# Cypher/SQL-PGQ에서도 같은 일이 벌어진다. 패턴 매칭도 경로 단위로 결과를 내므로
# 원래 예제의 Cypher 역시 회사가 여러 계약을 가지면 같은 이름을 여러 번 돌려준다.
# `DISTINCT`는 SQL만의 세금이 아니라 **「경로를 물었는데 노드를 답으로 받고 싶다」**의 대가다.
#
# 나루소프트도 하나 추가한다. 2025-01-20에 서명하고 **그 뒤에** 2026-09-01에 해지했다.
# 조인은 통과하지만 부등호에서 탈락한다 — 순서가 반대이기 때문이다.

# %%
CONTRACTS2 = CONTRACTS + [
    ("M-2019-002", None, "2023-05-01"),   # 가온테크의 더 오래된 해지 계약
    ("C-2027-001", "2027-01-01", None),   # 가온테크의 추가 서명 계약
    ("M-2022-050", None, "2026-09-01"),   # 나루소프트가 «나중에» 해지한 계약
]
SIGNED2 = SIGNED + [("가온테크", "C-2027-001")]
TERMINATED2 = TERMINATED + [("가온테크", "M-2019-002"), ("나루소프트", "M-2022-050")]

con2 = setup(SIGNED2, TERMINATED2, CONTRACTS2)
big_counts = trace(con2, "계약을 늘린 데이터")
# 출력:
# --- 계약을 늘린 데이터 ---
#   1. company만                              4행
#   2. + terminated                          4행
#   3. + contract o                          4행
#   4. + signed                              5행
#   5. + contract n                          5행
#   6. + WHERE o.ended_on < n.started_on     4행
#   7. + DISTINCT c.name                     1행

# %%
# DISTINCT 없이 보면 중복이 그대로 드러난다
print("DISTINCT 없음:")
for r in con2.execute(f"SELECT c.name, o.id, o.ended_on, n.id, n.started_on {BASE}"
                      "WHERE o.ended_on < n.started_on ORDER BY c.name, o.id, n.id"):
    print("   ", r)
print("\nDISTINCT 있음:",
      [r[0] for r in con2.execute(f"SELECT DISTINCT c.name {BASE}"
                                 "WHERE o.ended_on < n.started_on ORDER BY c.name")])
# 출력:
# DISTINCT 없음:
#     ('가온테크', 'M-2019-002', '2023-05-01', 'C-2025-118', '2025-06-02')
#     ('가온테크', 'M-2019-002', '2023-05-01', 'C-2027-001', '2027-01-01')
#     ('가온테크', 'M-2021-077', '2024-03-11', 'C-2025-118', '2025-06-02')
#     ('가온테크', 'M-2021-077', '2024-03-11', 'C-2027-001', '2027-01-01')
#
# DISTINCT 있음: ['가온테크']

# %%
# 나루소프트는 조인은 통과하지만 부등호에서 탈락한다 (서명이 «먼저»였다)
for r in con2.execute(f"SELECT c.name, o.ended_on, n.started_on {BASE}"
                      "WHERE c.name = '나루소프트'"):
    print(r, "→ 해지가 서명보다 뒤. 조건 불통과")
# 출력:
# ('나루소프트', '2026-09-01', '2025-01-20') → 해지가 서명보다 뒤. 조건 불통과

# %% [markdown]
# ## 같은 질문, 세 가지 표기 — 줄 수와 가독성
#
# 아래 세 조각은 **완전히 같은 질문**에 답한다.
# 「해지했다가 그 뒤에 다시 계약한 고객은?」

# %%
CYPHER = """MATCH (c:Company)-[:Terminated]->(o:Contract),
      (c)-[:Signed]->(n:Contract)
WHERE o.endedOn < n.startedOn
RETURN c.name AS 고객
ORDER BY 고객"""

PGQ_MATCH = """SELECT * FROM GRAPH_TABLE (biz
  MATCH (c IS Company)-[IS Terminated]->(o IS Contract),
        (c)-[IS Signed]->(n IS Contract)
  WHERE o.ended_on < n.started_on
  COLUMNS (c.name AS 고객)
);"""

PLAIN_SQL = """SELECT DISTINCT c.name AS 고객
  FROM company c
  JOIN terminated t ON t.company_name = c.name
  JOIN contract  o ON o.id = t.contract_id
  JOIN signed    s ON s.company_name = c.name
  JOIN contract  n ON n.id = s.contract_id
 WHERE o.ended_on < n.started_on
 ORDER BY 고객"""

PGQ_DDL_LINES = 14   # CREATE PROPERTY GRAPH biz ... (일회성 선언)

for label, code in (("Cypher", CYPHER), ("SQL/PGQ (질의부)", PGQ_MATCH), ("평범한 SQL", PLAIN_SQL)):
    lines = code.strip().splitlines()
    joins = sum(1 for ln in lines if "JOIN" in ln.upper())
    arrows = code.count("->")
    print(f"  {label:<18} {len(lines)}줄   JOIN {joins}개   화살표 {arrows}개")
print(f"\n  SQL/PGQ 는 위 질의부와 별도로 CREATE PROPERTY GRAPH DDL {PGQ_DDL_LINES}줄이 «한 번» 필요하다.")
print("  그 대신 질의문마다 반복되던 JOIN 4줄이 화살표 2개로 사라진다.")
# 출력:
#   Cypher             5줄   JOIN 0개   화살표 2개
#   SQL/PGQ (질의부)      6줄   JOIN 0개   화살표 2개
#   평범한 SQL            8줄   JOIN 4개   화살표 0개
#
#   SQL/PGQ 는 위 질의부와 별도로 CREATE PROPERTY GRAPH DDL 14줄이 «한 번» 필요하다.
#   그 대신 질의문마다 반복되던 JOIN 4줄이 화살표 2개로 사라진다.

# %% [markdown]
# ### 읽어 낼 것
#
# - **줄 수 차이는 작다.** 5 / 6 / 8줄. 「SQL은 스무 줄」이 되는 건 가변 길이 경로(`ex2`)이고,
#   고정 길이 2홉짜리 질문에서는 SQL도 그럭저럭 버틴다.
# - **차이는 무엇을 적는가에 있다.** Cypher/PGQ에는 `->`가 두 개 있고 조인이 0개다.
#   평범한 SQL에는 화살표가 없고 조인이 4개다. 후자를 읽는 사람은
#   `t.company_name = c.name`을 보고 「아 이게 간선이구나」를 머리로 복원해야 한다.
# - **`o`와 `n`이 같은 `contract` 테이블을 두 번 별칭으로 가리키는 것**도 SQL 쪽 부담이다.
#   그림에서는 노드가 두 개인 게 자명한데, SQL에서는 별칭을 잘못 쓰면 조용히 틀린다.
# - **`DISTINCT`는 SQL 쪽에만 붙어 있다.** 다만 이건 표기의 문제가 아니라
#   위에서 본 대로 경로 중복 때문이고, Cypher에서도 데이터가 늘면 같은 문제를 만난다.
# - **조인 폭발은 표기를 바꿔도 남는다.** SQL/PGQ는 「테이블을 옮기지 않아도 된다」를 주지
#   「따라가는 값이 비싸다」는 문제를 없애 주지는 않는다(11장 마지막 문단).

# %%
# 필요 패키지: plotly, kaleido
import plotly.graph_objects as go


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


short = ["company", "+terminated", "+contract o", "+signed", "+contract n",
         "+WHERE", "+DISTINCT"]

fig = go.Figure()
fig.add_bar(x=short, y=seed_counts, name="seed.py 원본",
            marker_color="#7f8fa6", text=seed_counts, textposition="outside")
fig.add_bar(x=short, y=big_counts, name="계약을 늘린 데이터",
            marker_color="#e1701a", text=big_counts, textposition="outside")
fig.update_layout(
    title="조인 4단계 → WHERE → DISTINCT 단계별 행 수",
    xaxis_title="질의 단계 (왼쪽부터 누적)",
    yaxis_title="행 수",
    barmode="group",
    template="plotly_white",
    width=980, height=460,
    legend=dict(orientation="h", y=1.12, x=0),
)
fig.update_yaxes(range=[0, max(big_counts + seed_counts) + 1.5])
_show(fig)

import os
_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_out, scale=2)
print("saved:", _out)
# 출력:
# saved: .../expy.png

# %% [markdown]
# ## 한 줄 정리
#
# 평범한 SQL은 그래프를 **직접 말할 수 없어서**, 간선 테이블과 노드 테이블을
# `company → terminated → contract(o) → signed → contract(n)` 순으로 네 번 조인해
# 「같은 회사의 해지 계약 하나와 서명 계약 하나」 조합을 전부 만들어 놓고,
# `WHERE o.ended_on < n.started_on`으로 **해지가 먼저인 조합만** 남기고,
# 계약 조합마다 생기는 경로 중복을 `DISTINCT`로 눌러 회사 이름 하나로 접는다.
