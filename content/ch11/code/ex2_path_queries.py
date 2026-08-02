"""
예제 2 — 가변 길이 경로. 세 언어의 표기가 제일 크게 갈리는 자리.

    python3 ex2_path_queries.py

확인 시점: Kuzu 0.11.3, rdflib 7.5.0.
"""

import shutil
import tempfile

import kuzu
from rdflib import Graph

from seed import TTL

CY_SCHEMA = [
    "CREATE NODE TABLE Co(name STRING, PRIMARY KEY(name))",
    "CREATE REL TABLE ParentOf(FROM Co TO Co)",
]
CY_DATA = [
    "CREATE (:Co {name:'가온테크'})", "CREATE (:Co {name:'가온소프트'})",
    "CREATE (:Co {name:'가온연구소'})",
    "MATCH (a:Co {name:'가온테크'}), (b:Co {name:'가온소프트'}) CREATE (a)-[:ParentOf]->(b)",
    "MATCH (a:Co {name:'가온소프트'}), (b:Co {name:'가온연구소'}) CREATE (a)-[:ParentOf]->(b)",
]

QUERIES = {
    "직접 자회사만": (
        "MATCH (a:Co)-[:ParentOf]->(b:Co) RETURN a.name, b.name ORDER BY a.name, b.name",
        """PREFIX ex: <http://example.org/>
           SELECT ?p ?c WHERE { ?a ex:parentOf ?b . ?a ex:name ?p . ?b ex:name ?c }
           ORDER BY ?p ?c"""),
    "1~3단계 아래 전부": (
        "MATCH (a:Co)-[:ParentOf*1..3]->(b:Co) RETURN a.name, b.name ORDER BY a.name, b.name",
        """PREFIX ex: <http://example.org/>
           SELECT ?p ?c WHERE { ?a ex:parentOf+ ?b . ?a ex:name ?p . ?b ex:name ?c }
           ORDER BY ?p ?c"""),
}


def run_cypher(conn, q):
    r = conn.execute(q)
    out = []
    while r.has_next():
        out.append(tuple(r.get_next()))
    return out


def main():
    tmp = tempfile.mkdtemp()
    try:
        conn = kuzu.Connection(kuzu.Database(f"{tmp}/db"))
        for s in CY_SCHEMA + CY_DATA:
            conn.execute(s)
        g = Graph().parse(data=TTL, format="turtle")

        for title, (cy, sp) in QUERIES.items():
            print(f"\n== {title} ==")
            c = run_cypher(conn, cy)
            s = [tuple(str(x) for x in row) for row in g.query(sp)]
            print(f"  Cypher {len(c)}행: {c}")
            print(f"  SPARQL {len(s)}행: {s}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(
        "\n표기를 나란히 놓으면 이렇다.\n"
        "  Cypher : -[:ParentOf*1..3]->     상한을 «반드시» 쓸 수 있다\n"
        "  SPARQL : ex:parentOf+            상한 표기가 없다\n"
        "  SQL    : WITH RECURSIVE ... 20줄  (3장 참조)\n"
        "\nSPARQL 의 경로 표현에는 «최대 몇 홉»을 적는 표준 문법이 없다.\n"
        "그래서 9장에서 본 «상한을 걸어라»를 SPARQL 에서는 다른 방식으로 해야 한다.\n"
        "질의 타임아웃, 결과 개수 제한, 아니면 깊이를 명시적으로 펼쳐 쓰기.\n"
        "\n표준이 있다고 모든 게 표준으로 되는 건 아니다. 이런 구멍이 실무를 정한다."
    )


if __name__ == "__main__":
    main()
