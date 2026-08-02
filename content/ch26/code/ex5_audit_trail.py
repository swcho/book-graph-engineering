"""
예제 5 — 막은 것도 로그로 남긴다. 그리고 그 로그가 정책을 고친다.

    python3 ex5_audit_trail.py

의존성 없음(표준 sqlite3). 차단 기록을 쌓고
「어느 규칙이 실제로 일하고 있나」를 센다.
"""

import sqlite3
from collections import Counter

DDL = """
CREATE TABLE gate_log (
  id       INTEGER PRIMARY KEY,
  agent    TEXT, tool TEXT, rule TEXT,
  verdict  TEXT,            -- 통과 / 차단
  reason   TEXT,
  overridden INTEGER        -- 사람이 나중에 뒤집었나
);
"""

EVENTS = [
    ("요약기", "read_docs",  "allow:read",     "통과", "",                 0),
    ("요약기", "http_post",  "deny:net-out",   "차단", "요약기에 없는 권한", 0),
    ("요약기", "http_post",  "deny:net-out",   "차단", "요약기에 없는 권한", 0),
    ("분석기", "db_read",    "allow:db-ro",    "통과", "",                 0),
    ("분석기", "run_shell",  "deny:exec",      "차단", "실행 권한 없음",     0),
    ("보고서", "send_mail",  "gate:approval",  "차단", "수신자가 외부 도메인", 1),
    ("보고서", "send_mail",  "gate:approval",  "차단", "수신자가 외부 도메인", 1),
    ("보고서", "send_mail",  "gate:approval",  "차단", "수신자가 외부 도메인", 1),
    ("보고서", "send_mail",  "gate:approval",  "차단", "수신자가 외부 도메인", 1),
    ("관리자", "run_shell",  "allow:exec-adm", "통과", "",                 0),
    ("요약기", "db_read",    "deny:db",        "차단", "요약기에 없는 권한", 0),
    ("분석기", "http_post",  "deny:net-out",   "차단", "분석기에 없는 권한", 0),
]


def main():
    db = sqlite3.connect(":memory:")
    db.executescript(DDL)
    db.executemany("INSERT INTO gate_log(agent,tool,rule,verdict,reason,"
                   "overridden) VALUES (?,?,?,?,?,?)", EVENTS)
    db.commit()

    print(f"{'규칙':<18}{'발동':>6}{'차단':>6}{'사람이 뒤집음':>14}{'뒤집힌 비율':>12}")
    print("-" * 58)
    rows = db.execute("""
        SELECT rule, COUNT(*), SUM(verdict='차단'), SUM(overridden)
        FROM gate_log GROUP BY rule ORDER BY COUNT(*) DESC""").fetchall()
    for rule, n, blocked, over in rows:
        rate = over / blocked if blocked else 0
        mark = "  ← 규칙이 틀렸다" if rate >= 0.8 else ""
        print(f"{rule:<18}{n:>6}{blocked:>6}{over:>14}{rate:>11.0%}{mark}")

    never = db.execute("""
        SELECT rule FROM gate_log GROUP BY rule HAVING SUM(verdict='차단')=0
        """).fetchall()
    print(f"\n한 번도 차단한 적 없는 규칙: {[r[0] for r in never]}")

    print(
        "\n이 표가 하는 일은 «정책을 고치는 것»이다.\n"
        "\ngate:approval 은 네 번 발동해서 네 번 다 사람이 뒤집었다.\n"
        "100% 뒤집힘은 «규칙이 틀렸다»는 뜻이다. 사람 시간만 쓰고 있다.\n"
        "외부 도메인 전부를 막을 게 아니라 «허용 도메인 목록»을 뒀어야 했다.\n"
        "\ndeny:net-out 은 세 번 막고 한 번도 안 뒤집혔다. 잘 일하는 규칙이다.\n"
        "\nallow: 로 시작하는 규칙들은 차단이 0이다. 당연하다, 허용 규칙이니까.\n"
        "그래도 로그를 남긴다. 왜냐하면 «누가 무엇을 했나»가 사고 조사의 절반이라서다.\n"
        "\n여기서 규칙 하나. 차단 로그에 반드시 넣을 것 셋이다.\n"
        "  - 어느 규칙이 막았나 (규칙 이름)\n"
        "  - 왜 막았나 (사람이 읽을 수 있는 이유)\n"
        "  - 나중에 사람이 뒤집었나 (이게 정책 품질 지표가 된다)\n"
        "\n세 번째가 대부분 빠진다. 그런데 그게 없으면\n"
        "«과하게 막고 있는 규칙»을 영원히 못 찾는다.\n"
        "그리고 과하게 막는 규칙은 결국 «다들 우회하는 규칙»이 된다."
    )


if __name__ == "__main__":
    main()
