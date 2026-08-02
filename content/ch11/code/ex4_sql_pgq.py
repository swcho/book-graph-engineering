"""
예제 4 — SQL/PGQ. 관계형 테이블 위에 «그래프 뷰»를 얹는 표준.

    python3 ex4_sql_pgq.py

의존성 없음 (sqlite3 는 표준 라이브러리).
SQL/PGQ(ISO/IEC 9075-16:2023)를 실제로 구현한 엔진이 아직 널리 퍼지지 않아서,
여기서는 «표준 문법»을 보여 주고 같은 뜻의 평범한 SQL 을 돌려서 답을 맞춰 본다.
"""

import sqlite3
import textwrap

from seed import COMPANIES, CONTRACTS, SIGNED, TERMINATED

PGQ = textwrap.dedent("""
    -- SQL/PGQ 표준 문법 (ISO/IEC 9075-16:2023)
    CREATE PROPERTY GRAPH biz
      VERTEX TABLES (
        company KEY (name) LABEL Company PROPERTIES (name, grade),
        contract KEY (id)  LABEL Contract PROPERTIES (id, started_on, ended_on)
      )
      EDGE TABLES (
        signed     SOURCE KEY (company_name) REFERENCES company (name)
                   DESTINATION KEY (contract_id) REFERENCES contract (id)
                   LABEL Signed,
        terminated SOURCE KEY (company_name) REFERENCES company (name)
                   DESTINATION KEY (contract_id) REFERENCES contract (id)
                   LABEL Terminated
      );

    SELECT * FROM GRAPH_TABLE (biz
      MATCH (c IS Company)-[IS Terminated]->(o IS Contract),
            (c)-[IS Signed]->(n IS Contract)
      WHERE o.ended_on < n.started_on
      COLUMNS (c.name AS 고객)
    );
""").strip()

PLAIN_SQL = """
SELECT DISTINCT c.name AS 고객
  FROM company c
  JOIN terminated t ON t.company_name = c.name
  JOIN contract  o ON o.id = t.contract_id
  JOIN signed    s ON s.company_name = c.name
  JOIN contract  n ON n.id = s.contract_id
 WHERE o.ended_on < n.started_on
 ORDER BY 고객
"""


def setup():
    con = sqlite3.connect(":memory:")
    con.executescript("""
        CREATE TABLE company (name TEXT PRIMARY KEY, grade TEXT);
        CREATE TABLE contract (id TEXT PRIMARY KEY, started_on TEXT, ended_on TEXT);
        CREATE TABLE signed (company_name TEXT, contract_id TEXT);
        CREATE TABLE terminated (company_name TEXT, contract_id TEXT);
    """)
    con.executemany("INSERT INTO company VALUES (?,?)", COMPANIES)
    con.executemany("INSERT INTO contract VALUES (?,?,?)", CONTRACTS)
    con.executemany("INSERT INTO signed VALUES (?,?)", SIGNED)
    con.executemany("INSERT INTO terminated VALUES (?,?)", TERMINATED)
    con.commit()
    return con


def main():
    print("SQL/PGQ 표준 문법 — 테이블은 그대로 두고 그래프 «뷰»만 선언한다\n")
    print(textwrap.indent(PGQ, "    "))

    con = setup()
    rows = [r[0] for r in con.execute(PLAIN_SQL)]
    print(f"\n같은 뜻의 평범한 SQL 실행 결과: {rows}")

    print(
        "\nSQL/PGQ 의 값어치는 «데이터를 옮기지 않아도 된다»는 데 있다.\n"
        "테이블은 그대로 두고 그래프로 보는 시각만 얹는다.\n"
        "3장에서 본 «두 벌 운영»의 비용을 안 내도 된다는 뜻이다.\n"
        "\n다만 2026년 8월 기준으로, 이 문법을 프로덕션에서 쓰는 팀을 저는 못 봤다.\n"
        "구현이 덜 퍼졌다. 그래서 이 예제는 «돌아가는 코드»가 아니라\n"
        "«앞으로 이렇게 될 가능성»을 보여 주는 것이다. 확인 시점을 꼭 같이 읽어 달라.\n"
        "\n그리고 옮기지 않아도 된다는 게 공짜라는 뜻은 아니다.\n"
        "조인 폭발은 그대로 남는다(3장). 저장 위치가 아니라 «따라가는 값»이 문제였으니까."
    )


if __name__ == "__main__":
    main()
