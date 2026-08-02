"""
예제 4 — 시간이 붙은 그래프에 질의하기. Cypher 와 SPARQL 로.

    pip install kuzu "rdflib>=7,<8"
    python3 ex4_temporal_query.py

확인 시점 Kuzu 0.11.3, rdflib 7.5.0.
"""

import shutil
import tempfile

import kuzu
from rdflib import Graph

CY_SETUP = [
    "CREATE NODE TABLE Company(name STRING, PRIMARY KEY(name))",
    "CREATE NODE TABLE Person(name STRING, PRIMARY KEY(name))",
    # 유효 기간을 «엣지 속성»으로 둔다. 5장에서 본 LPG 의 장점이 여기서 나온다.
    "CREATE REL TABLE ManagedBy(FROM Company TO Person, "
    "valid_from DATE, valid_to DATE)",
    "CREATE (:Company {name:'가온테크'})",
    "CREATE (:Person {name:'김하늘'})",
    "CREATE (:Person {name:'박서준'})",
    "MATCH (c:Company{name:'가온테크'}), (p:Person{name:'김하늘'}) "
    "CREATE (c)-[:ManagedBy {valid_from: date('2026-03-01'), "
    "valid_to: date('2026-06-01')}]->(p)",
    "MATCH (c:Company{name:'가온테크'}), (p:Person{name:'박서준'}) "
    "CREATE (c)-[:ManagedBy {valid_from: date('2026-06-01'), "
    "valid_to: date('9999-12-31')}]->(p)",
]

CY_AT = """
MATCH (c:Company {{name:'가온테크'}})-[r:ManagedBy]->(p:Person)
WHERE r.valid_from <= date('{d}') AND date('{d}') < r.valid_to
RETURN p.name AS 담당
"""

TTL = """
@prefix ex:  <http://example.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
# RDF 는 엣지에 속성을 못 달아서 «사건 노드»로 승격한다 (5장 방법 1)
ex:Gaon a ex:Company ; ex:name "가온테크" ; ex:hasAssignment ex:a1, ex:a2 .
ex:a1 ex:person ex:Kim  ; ex:validFrom "2026-03-01"^^xsd:date ;
      ex:validTo "2026-06-01"^^xsd:date .
ex:a2 ex:person ex:Park ; ex:validFrom "2026-06-01"^^xsd:date ;
      ex:validTo "9999-12-31"^^xsd:date .
ex:Kim  ex:name "김하늘" .
ex:Park ex:name "박서준" .
"""

SP_AT = """
PREFIX ex:  <http://example.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?담당 WHERE {{
    ex:Gaon ex:hasAssignment ?a .
    ?a ex:person ?p ; ex:validFrom ?vf ; ex:validTo ?vt .
    ?p ex:name ?담당 .
    FILTER(?vf <= "{d}"^^xsd:date && "{d}"^^xsd:date < ?vt)
}}
"""


def main():
    tmp = tempfile.mkdtemp()
    try:
        conn = kuzu.Connection(kuzu.Database(f"{tmp}/db"))
        for s in CY_SETUP:
            conn.execute(s)
        g = Graph().parse(data=TTL, format="turtle")

        print(f"{'시점':<14} {'Cypher':<10} {'SPARQL'}")
        print("-" * 38)
        for d in ("2026-02-01", "2026-04-15", "2026-06-01", "2026-09-01"):
            r = conn.execute(CY_AT.format(d=d))
            cy = []
            while r.has_next():
                cy.append(r.get_next()[0])
            sp = [str(x[0]) for x in g.query(SP_AT.format(d=d))]
            print(f"{d:<14} {(cy or ['모름'])[0]:<10} {(sp or ['모름'])[0]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(
        "\n두 언어가 같은 답을 낸다. 쓰는 모양이 다를 뿐이다.\n"
        "\nLPG 는 엣지에 valid_from/valid_to 를 그냥 단다. 한 줄이다.\n"
        "RDF 는 엣지에 속성을 못 달아서 «배정»이라는 사건 노드를 만들었다.\n"
        "5장에서 본 구체화다. 노드가 늘고 질의가 한 줄 길어진다.\n"
        "\n그런데 RDF 쪽이 나은 점도 있다. 사건 노드에 «누가 언제 이 배정을 입력했나»를\n"
        "붙이기가 쉽다. LPG 에서 같은 걸 하려면 엣지 속성을 또 늘려야 하고,\n"
        "그 속성으로 검색하려는 순간 7장의 «노드로 승격» 문제가 다시 온다.\n"
        "\n시간을 다루기 시작하면 «관계가 사건이 된다». 이게 이 절의 진짜 결론이다."
    )


if __name__ == "__main__":
    main()
