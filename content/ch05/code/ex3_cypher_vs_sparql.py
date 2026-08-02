"""
예제 3 — 같은 질문을 Cypher 와 SPARQL 로. §9.3 의 나란히 놓기.

    pip install kuzu "rdflib>=7,<8"
    python3 ex3_cypher_vs_sparql.py

확인 시점: Kuzu 0.11.3, rdflib 7.5.0.
Cypher 는 서버 없이 돌리려고 임베디드 엔진 Kuzu 를 쓴다.
Neo4j 5.x 와 문법이 갈리는 곳은 주석으로 표시했다.
"""

import shutil
import tempfile

import kuzu
from rdflib import Graph

CYPHER_SCHEMA = [
    "CREATE NODE TABLE Company(name STRING, grade STRING, PRIMARY KEY(name))",
    "CREATE NODE TABLE Contract(id STRING, startedOn DATE, endedOn DATE, PRIMARY KEY(id))",
    "CREATE REL TABLE Signed(FROM Company TO Contract, at DATE)",
    "CREATE REL TABLE Terminated(FROM Company TO Contract, at DATE)",
    # Neo4j 5.x 에는 이 스키마 선언이 없다. 라벨을 쓰면 그 자리에서 생긴다.
    # 스키마를 미리 못 박느냐가 두 엔진의 큰 차이다. 12장에서 다시 본다.
]

CYPHER_DATA = [
    "CREATE (:Company {name:'가온테크', grade:'A'})",
    "CREATE (:Company {name:'나루소프트', grade:'B'})",
    "CREATE (:Company {name:'라온에너지', grade:'C'})",
    "CREATE (:Contract {id:'M-2021-077', endedOn: date('2024-03-11')})",
    "CREATE (:Contract {id:'C-2025-118', startedOn: date('2025-06-02')})",
    "CREATE (:Contract {id:'C-2025-004', startedOn: date('2025-01-20')})",
    "CREATE (:Contract {id:'M-2020-031', endedOn: date('2024-08-05')})",
    "MATCH (a:Company {name:'가온테크'}), (b:Contract {id:'M-2021-077'}) "
    "CREATE (a)-[:Terminated {at: date('2024-03-11')}]->(b)",
    "MATCH (a:Company {name:'가온테크'}), (b:Contract {id:'C-2025-118'}) "
    "CREATE (a)-[:Signed {at: date('2025-06-02')}]->(b)",
    "MATCH (a:Company {name:'나루소프트'}), (b:Contract {id:'C-2025-004'}) "
    "CREATE (a)-[:Signed {at: date('2025-01-20')}]->(b)",
    "MATCH (a:Company {name:'라온에너지'}), (b:Contract {id:'M-2020-031'}) "
    "CREATE (a)-[:Terminated {at: date('2024-08-05')}]->(b)",
]

CYPHER_QUERY = """
MATCH (c:Company)-[t:Terminated]->(:Contract),
      (c)-[s:Signed]->(:Contract)
WHERE t.at < s.at
RETURN c.name AS 고객, t.at AS 해지, s.at AS 재계약
"""

TTL = """
@prefix ex:  <http://example.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
ex:Gaon a ex:Company ; ex:name "가온테크" ;
    ex:terminated ex:M2021077 ; ex:signed ex:C2025118 .
ex:Naru a ex:Company ; ex:name "나루소프트" ; ex:signed ex:C2025004 .
ex:Raon a ex:Company ; ex:name "라온에너지" ; ex:terminated ex:M2020031 .
ex:M2021077 ex:endedOn   "2024-03-11"^^xsd:date .
ex:C2025118 ex:startedOn "2025-06-02"^^xsd:date .
ex:C2025004 ex:startedOn "2025-01-20"^^xsd:date .
ex:M2020031 ex:endedOn   "2024-08-05"^^xsd:date .
"""

SPARQL_QUERY = """
PREFIX ex: <http://example.org/>
SELECT ?고객 ?해지 ?재계약 WHERE {
    ?c ex:name ?고객 ;
       ex:terminated ?old ;
       ex:signed     ?new .
    ?old ex:endedOn   ?해지 .
    ?new ex:startedOn ?재계약 .
    FILTER(?해지 < ?재계약)
}
"""


def run_cypher():
    tmp = tempfile.mkdtemp()
    try:
        conn = kuzu.Connection(kuzu.Database(f"{tmp}/db"))
        for stmt in CYPHER_SCHEMA + CYPHER_DATA:
            conn.execute(stmt)
        res = conn.execute(CYPHER_QUERY)
        rows = []
        while res.has_next():
            rows.append(res.get_next())
        return rows
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_sparql():
    g = Graph().parse(data=TTL, format="turtle")
    return [[str(x) for x in row] for row in g.query(SPARQL_QUERY)]


def main():
    print("질문: 해지했다가 그 뒤에 다시 계약한 고객은?\n")
    print("--- Cypher (Kuzu) ---")
    for r in run_cypher():
        print("  ", r)
    print("\n--- SPARQL (rdflib) ---")
    for r in run_sparql():
        print("  ", r)

    print(
        "\n답은 같다. 문장 모양이 다를 뿐이다.\n"
        "  Cypher 는 «그림»을 그린다.  (c)-[:Signed]->(:Contract)\n"
        "  SPARQL 은 «문장»을 나열한다. ?c ex:signed ?new .\n"
        "\n둘 다 익히면 좋지만, 팀에 하나만 고르라면 «데이터가 어디서 오는가»로 정하시라.\n"
        "밖에서 오는 데이터를 합치는 일이 많으면 RDF, 우리가 만드는 데이터면 LPG 가 편하다."
    )


if __name__ == "__main__":
    main()
