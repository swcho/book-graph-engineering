"""
예제 4 — 표가 이긴 이유. 그래프를 편들기 전에 이걸 먼저 봐야 공정하다.

    python3 ex4_why_tables_won.py

의존성 없음. 세 가지를 눈으로 확인한다.
  (1) 선언적 질의 — 어떻게 찾을지는 안 적는다
  (2) 제약 — 잘못된 데이터가 아예 안 들어간다
  (3) 트랜잭션 — 절반만 반영되는 일이 없다
"""

import sqlite3


def setup():
    con = sqlite3.connect(":memory:", isolation_level=None)  # 트랜잭션을 직접 다룬다
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript("""
        CREATE TABLE company (
            id    INTEGER PRIMARY KEY,
            name  TEXT NOT NULL UNIQUE,
            grade TEXT NOT NULL CHECK (grade IN ('A','B','C'))
        );
        CREATE TABLE contract (
            id         TEXT PRIMARY KEY,
            company_id INTEGER NOT NULL REFERENCES company(id),
            amount     INTEGER NOT NULL CHECK (amount > 0)
        );
    """)
    con.executemany("INSERT INTO company VALUES (?,?,?)",
                    [(1, "가온테크", "A"), (2, "나루소프트", "B")])
    con.executemany("INSERT INTO contract VALUES (?,?,?)",
                    [("C-1", 1, 5_000_000), ("C-2", 2, 1_200_000)])
    con.commit()
    return con


def main():
    con = setup()

    print("(1) 선언적 질의 — 인덱스를 쓸지 어떤 순서로 읽을지는 내가 안 정한다")
    rows = con.execute("""
        SELECT c.name, SUM(k.amount) AS total
          FROM company c JOIN contract k ON k.company_id = c.id
         GROUP BY c.id HAVING total > 1000000
         ORDER BY total DESC
    """).fetchall()
    for name, total in rows:
        print(f"    {name}: {total:,}원")
    plan = con.execute("EXPLAIN QUERY PLAN SELECT * FROM contract WHERE company_id=1")
    print("    실행 계획:", "; ".join(str(r[-1]) for r in plan))

    print("\n(2) 제약 — 잘못된 데이터는 들어가지 않는다")
    for label, sql, args in [
        ("없는 회사에 계약 달기", "INSERT INTO contract VALUES (?,?,?)", ("C-9", 99, 100)),
        ("금액이 음수",          "INSERT INTO contract VALUES (?,?,?)", ("C-8", 1, -5)),
        ("등급이 규칙 밖",       "INSERT INTO company VALUES (?,?,?)",  (3, "다올물산", "Z")),
    ]:
        try:
            con.execute(sql, args)
            print(f"    {label}: 통과해 버렸다 (문제)")
        except sqlite3.IntegrityError as e:
            print(f"    {label}: 거부됨 — {e}")

    print("\n(3) 트랜잭션 — 절반만 반영되는 일이 없다")
    before = con.execute("SELECT COUNT(*) FROM contract").fetchone()[0]
    try:
        con.execute("BEGIN")
        con.execute("INSERT INTO contract VALUES ('C-3', 1, 300000)")
        con.execute("INSERT INTO contract VALUES ('C-4', 99, 400000)")  # 여기서 터진다
        con.execute("COMMIT")
    except sqlite3.IntegrityError as e:
        con.execute("ROLLBACK")
        print(f"    두 번째 INSERT 에서 거부: {e}")
    after = con.execute("SELECT COUNT(*) FROM contract").fetchone()[0]
    print(f"    시작 {before}행 → 끝 {after}행. 첫 INSERT 도 함께 사라졌다.")

    print(
        "\n이 셋이 40년 동안 관계형이 이긴 이유다. 그래프 진영이 이걸 갖추는 데 오래 걸렸다.\n"
        "지금 그래프 엔진을 고를 때도 여기부터 확인하는 게 맞다.\n"
        "제약이 있는가, 트랜잭션이 있는가, 질의가 선언적인가."
    )


if __name__ == "__main__":
    main()
