"""
예제 1 — 같은 질문을 세 언어로. 답은 같고 문장 모양이 다르다.

    pip install kuzu "rdflib>=7,<8"
    python3 ex1_three_languages.py

확인 시점: Kuzu 0.11.3, rdflib 7.5.0.
Gremlin 은 엔진이 필요해서, 여기서는 «걸음»을 파이썬으로 흉내 낸다.
문법이 아니라 «사고 방식»이 다르다는 걸 보여 주려는 것이다.
"""

import shutil
import tempfile
from collections import defaultdict

import kuzu
from rdflib import Graph

from seed import COMPANIES, CONTRACTS, SIGNED, TERMINATED, TTL

CYPHER = """
MATCH (c:Company)-[:Terminated]->(o:Contract),
      (c)-[:Signed]->(n:Contract)
WHERE o.endedOn < n.startedOn
RETURN c.name AS 고객
ORDER BY 고객
"""

SPARQL = """
PREFIX ex: <http://example.org/>
SELECT ?고객 WHERE {
    ?c ex:name ?고객 ; ex:terminated ?o ; ex:signed ?n .
    ?o ex:endedOn   ?end .
    ?n ex:startedOn ?start .
    FILTER(?end < ?start)
} ORDER BY ?고객
"""


def build_kuzu():
    tmp = tempfile.mkdtemp()
    conn = kuzu.Connection(kuzu.Database(f"{tmp}/db"))
    conn.execute("CREATE NODE TABLE Company(name STRING, grade STRING, PRIMARY KEY(name))")
    conn.execute("CREATE NODE TABLE Contract(id STRING, startedOn DATE, endedOn DATE, "
                 "PRIMARY KEY(id))")
    conn.execute("CREATE REL TABLE Signed(FROM Company TO Contract)")
    conn.execute("CREATE REL TABLE Terminated(FROM Company TO Contract)")
    for name, grade in COMPANIES:
        conn.execute(f"CREATE (:Company {{name:'{name}', grade:'{grade}'}})")
    for cid, s, e in CONTRACTS:
        sv = f"date('{s}')" if s else "NULL"
        ev = f"date('{e}')" if e else "NULL"
        conn.execute(f"CREATE (:Contract {{id:'{cid}', startedOn:{sv}, endedOn:{ev}}})")
    for rel, rows in (("Signed", SIGNED), ("Terminated", TERMINATED)):
        for a, b in rows:
            conn.execute(f"MATCH (x:Company {{name:'{a}'}}), (y:Contract {{id:'{b}'}}) "
                         f"CREATE (x)-[:{rel}]->(y)")
    return conn, tmp


def gremlin_style():
    """Gremlin 의 «걸음»을 파이썬으로. g.V().out('terminated')... 와 같은 사고."""
    ended = {a: next(e for c, s, e in CONTRACTS if c == b) for a, b in TERMINATED}
    started = defaultdict(list)
    for a, b in SIGNED:
        started[a].append(next(s for c, s, e in CONTRACTS if c == b))
    out = []
    for company, end in ended.items():                 # .hasLabel('Company').out('terminated')
        for start in started.get(company, []):         # .in().out('signed')
            if end < start:                            # .where(...)
                out.append(company)
    return sorted(set(out))


def main():
    conn, tmp = build_kuzu()
    try:
        res = conn.execute(CYPHER)
        cypher_rows = []
        while res.has_next():
            cypher_rows.append(res.get_next()[0])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    g = Graph().parse(data=TTL, format="turtle")
    sparql_rows = [str(r[0]) for r in g.query(SPARQL)]
    gremlin_rows = gremlin_style()

    print("질문: 해지했다가 그 뒤에 다시 계약한 고객은?\n")
    for name, rows in (("Cypher (Kuzu)", cypher_rows),
                       ("SPARQL (rdflib)", sparql_rows),
                       ("Gremlin 식 순회", gremlin_rows)):
        print(f"  {name:<18} {rows}")

    same = cypher_rows == sparql_rows == gremlin_rows
    print(f"\n셋이 같은가: {'예' if same else '아니오'}")
    print(
        "\n문장 모양이 다르다.\n"
        "  Cypher 는 «그림»이다.  (c)-[:Signed]->(n)  — 화이트보드에 그린 것과 같은 모양\n"
        "  SPARQL 은 «문장»이다.  ?c ex:signed ?n .    — 사실을 한 줄씩 늘어놓는다\n"
        "  Gremlin 은 «걸음»이다.  .out('signed')       — 어디로 갈지 순서대로 지시한다\n"
        "\n앞 둘은 선언형이다. 무엇을 원하는지만 적고 방법은 엔진이 정한다.\n"
        "Gremlin 은 명령형에 가깝다. 순회 순서를 내가 정한다.\n"
        "그래서 Gremlin 은 세밀한 제어가 되고, 대신 최적화기가 도와줄 여지가 적다."
    )


if __name__ == "__main__":
    main()
