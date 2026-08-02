"""
예제 3 — ISO GQL 표준 문법과 엔진 방언이 어긋나는 자리를 실제로 세어 본다.

    python3 ex3_gql_dialects.py

확인 시점 2026년 8월, Kuzu 0.11.3.
GQL(ISO/IEC 39075:2024) 문법을 그대로 넣어 보고 되는지 안 되는지 표시한다.
«표준이 있어도 방언이 남는다»를 말이 아니라 결과로 확인하는 게 목적이다.
"""

import shutil
import tempfile

import kuzu

SETUP = [
    "CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY(name))",
    "CREATE REL TABLE Knows(FROM Person TO Person, since INT64)",
    "CREATE (:Person {name:'가온', age:41})",
    "CREATE (:Person {name:'나루', age:35})",
    "CREATE (:Person {name:'다올', age:29})",
    "MATCH (a:Person {name:'가온'}), (b:Person {name:'나루'}) "
    "CREATE (a)-[:Knows {since:2019}]->(b)",
    "MATCH (a:Person {name:'나루'}), (b:Person {name:'다올'}) "
    "CREATE (a)-[:Knows {since:2022}]->(b)",
]

# (설명, 문법 계열, 질의문)
CASES = [
    ("기본 패턴 매칭", "GQL/Cypher 공통",
     "MATCH (p:Person) RETURN p.name ORDER BY p.name"),
    ("WHERE 절", "GQL/Cypher 공통",
     "MATCH (p:Person) WHERE p.age > 30 RETURN p.name ORDER BY p.name"),
    ("가변 길이 경로", "Cypher 방언",
     "MATCH (a:Person)-[:Knows*1..2]->(b:Person) RETURN a.name, b.name"),
    ("GQL 표준: LET 절", "GQL 표준",
     "MATCH (p:Person) LET nm = p.name RETURN nm"),
    ("GQL 표준: NEXT 절", "GQL 표준",
     "MATCH (p:Person) RETURN p.name AS n NEXT RETURN n"),
    ("GQL 표준: FILTER 절", "GQL 표준",
     "MATCH (p:Person) FILTER p.age > 30 RETURN p.name"),
    ("Cypher 방언: WITH 절", "Cypher 방언",
     "MATCH (p:Person) WITH p WHERE p.age > 30 RETURN p.name"),
]


def main():
    tmp = tempfile.mkdtemp()
    try:
        conn = kuzu.Connection(kuzu.Database(f"{tmp}/db"))
        for s in SETUP:
            conn.execute(s)

        print(f"{'항목':<22} {'계열':<16} {'결과'}")
        print("-" * 64)
        ok = fail = 0
        for label, family, q in CASES:
            try:
                r = conn.execute(q)
                n = 0
                while r.has_next():
                    r.get_next(); n += 1
                print(f"{label:<22} {family:<16} 성공 ({n}행)")
                ok += 1
            except Exception as e:
                msg = str(e).split("\n")[0][:38]
                print(f"{label:<22} {family:<16} 실패 — {msg}")
                fail += 1
        print(f"\n성공 {ok} / 실패 {fail}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(
        "\nGQL 은 2024년에 국제 표준이 됐다. 그런데 이 엔진은 GQL 전용 절을 아직 안 받는다.\n"
        "«표준이 나왔다»와 «표준대로 돌아간다» 사이에 몇 년이 있다.\n"
        "\nSQL 도 같은 길을 걸었다. SQL-92 가 나오고도 방언이 10년 넘게 남았다.\n"
        "지금 어느 엔진을 쓰든, 3년 뒤에 GQL 로 옮길 준비를 해 두는 게 낫다.\n"
        "구체적으로는 이렇다.\n"
        "  - 질의문을 코드에 흩뿌리지 말고 한곳에 모은다\n"
        "  - 엔진 고유 함수는 별도 파일로 격리한다\n"
        "  - 「이 질의가 어떤 질문에 답하는가」를 주석으로 남긴다 (다시 쓸 때 필요하다)"
    )


if __name__ == "__main__":
    main()
