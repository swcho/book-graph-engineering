"""
예제 5 — 실행 계획 읽기. 질의문이 아니라 계획이 성능을 정한다.

    python3 ex5_read_plan.py

확인 시점 Kuzu 0.11.3.
"""

import shutil
import tempfile
import time

import kuzu

N_PERSON = 20_000
N_CITY = 12


def build():
    tmp = tempfile.mkdtemp()
    conn = kuzu.Connection(kuzu.Database(f"{tmp}/db"))
    conn.execute("CREATE NODE TABLE City(name STRING, PRIMARY KEY(name))")
    conn.execute("CREATE NODE TABLE Person(id INT64, city STRING, PRIMARY KEY(id))")
    conn.execute("CREATE REL TABLE LivesIn(FROM Person TO City)")
    for i in range(N_CITY):
        conn.execute(f"CREATE (:City {{name:'도시{i}'}})")
    conn.execute(
        "UNWIND range(0, %d) AS i CREATE (:Person {id: i, city: '도시' + CAST(i %% %d AS STRING)})"
        % (N_PERSON - 1, N_CITY))
    conn.execute(
        "MATCH (p:Person), (c:City) WHERE p.city = c.name CREATE (p)-[:LivesIn]->(c)")
    return conn, tmp


def timed(conn, q, repeat=3):
    best = float("inf"); n = 0
    for _ in range(repeat):
        t0 = time.perf_counter()
        r = conn.execute(q)
        n = 0
        while r.has_next():
            r.get_next(); n += 1
        best = min(best, time.perf_counter() - t0)
    return n, best * 1000


def main():
    conn, tmp = build()
    try:
        q_city_first = ("MATCH (c:City)<-[:LivesIn]-(p:Person) "
                        "WHERE c.name = '도시3' RETURN COUNT(p)")
        q_person_first = ("MATCH (p:Person)-[:LivesIn]->(c:City) "
                          "WHERE p.city = '도시3' RETURN COUNT(p)")

        print(f"사람 {N_PERSON:,}명, 도시 {N_CITY}개\n")
        for label, q in (("작은 쪽(City)에서 시작", q_city_first),
                         ("큰 쪽(Person)에서 시작", q_person_first)):
            n, ms = timed(conn, q)
            print(f"  {label:<22} 결과 {n}행  {ms:7.2f} ms")

        print("\n실행 계획 (작은 쪽에서 시작):")
        r = conn.execute("EXPLAIN " + q_city_first)
        while r.has_next():
            for line in str(r.get_next()[0]).splitlines()[:14]:
                print("   ", line)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(
        "\n계획에서 볼 것은 셋이다.\n"
        "  1. 어느 테이블부터 훑는가 («스캔» 이 어디에 있나)\n"
        "  2. 색인을 타는가 아니면 전체를 훑는가\n"
        "  3. 중간 결과가 몇 행으로 추정되는가\n"
        "\n선언형 언어의 대가가 여기 있다. 무엇을 원하는지만 적으면 편한데,\n"
        "느릴 때 «왜 느린지»를 알려면 계획을 읽어야 한다.\n"
        "33장에서 계획을 고치는 법을 다룬다. 여기서는 «읽을 줄 알아야 한다»까지만."
    )


if __name__ == "__main__":
    main()
