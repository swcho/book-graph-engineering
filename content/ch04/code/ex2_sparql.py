"""
예제 2 — 같은 데이터를 진짜 RDF 로. SPARQL 로 묻고, OWL 추론을 켜 본다.

    pip install "rdflib>=7,<8"
    python3 ex2_sparql.py

확인 시점: rdflib 7.5.0.
"""

from rdflib import Graph, Namespace, RDFS

EX = Namespace("http://example.org/")

Q_SIGNED = """
PREFIX ex:   <http://example.org/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?name ?start WHERE {
    ?c   a ex:Company ; rdfs:label ?name ; ex:signed ?k .
    ?k   ex:startedOn ?start .
}
ORDER BY ?start
"""

Q_CHURN = """
PREFIX ex:   <http://example.org/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?name WHERE {
    ?c ex:terminated ?old ; ex:signed ?new ; rdfs:label ?name .
    ?old ex:endedOn   ?end .
    ?new ex:startedOn ?start .
    FILTER(?start > ?end)
}
"""

Q_SUBSIDIARY = """
PREFIX ex: <http://example.org/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?p ?c WHERE { ?a ex:parentOf ?b . ?a rdfs:label ?p . ?b rdfs:label ?c . }
ORDER BY ?p ?c
"""

Q_PATH = """
PREFIX ex: <http://example.org/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?p ?c WHERE { ?a ex:parentOf+ ?b . ?a rdfs:label ?p . ?b rdfs:label ?c . }
ORDER BY ?p ?c
"""


def show(g, q, title):
    print(f"\n{title}")
    for row in g.query(q):
        print("  ", " · ".join(str(x) for x in row))


def main():
    g = Graph().parse("sample.ttl", format="turtle")
    print(f"트리플 {len(g)}개 적재")

    show(g, Q_SIGNED, "계약을 체결한 곳 (체결일 순)")
    show(g, Q_CHURN, "해지했다가 다시 체결한 곳 — 1장의 그 질문")
    show(g, Q_SUBSIDIARY, "적어 둔 모회사 관계만")
    show(g, Q_PATH, "경로 질의(+)로 이행 관계까지")

    print(
        "\n마지막 두 결과의 차이가 이 예제의 요점이다.\n"
        "ex:parentOf+ 의 «+» 하나가 «한 번 이상 따라가라»는 뜻이다.\n"
        "SQL 로 같은 걸 쓰면 재귀 CTE 20줄이 된다. 3장에서 본 그 차이다."
    )


if __name__ == "__main__":
    main()
