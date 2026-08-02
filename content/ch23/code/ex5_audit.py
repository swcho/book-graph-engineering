"""
예제 5 — 누가 언제 무엇을 승인했나. 그리고 그때 무엇을 보고 있었나.

    python3 ex5_audit.py

의존성 없음(표준 sqlite3). 승인 기록을 남기고 되짚어 본다.
"""

import sqlite3

DDL = """
CREATE TABLE approval (
  id           INTEGER PRIMARY KEY,
  thread_id    TEXT NOT NULL,
  node         TEXT NOT NULL,
  asked_at     TEXT NOT NULL,
  answered_at  TEXT,
  actor        TEXT,
  decision     TEXT,
  shown        TEXT NOT NULL,   -- 사람에게 «실제로 보여 준» 내용
  state_hash   TEXT NOT NULL    -- 그 순간의 상태 지문
);
"""

ROWS = [
    ("환불-A1024", "사람확인", "2026-03-14T09:02Z", "2026-03-14T09:05Z",
     "kim", "승인", "금액 300,000 / 미개봉 / 첫 환불", "a91c"),
    ("환불-A1031", "사람확인", "2026-03-14T09:11Z", "2026-03-14T14:48Z",
     "lee", "거절", "금액 890,000 / 개봉 / 3회차 환불", "77de"),
    ("환불-A1050", "사람확인", "2026-03-14T10:20Z", None,
     None, None, "금액 4,200,000 / 확인 불가", "b30f"),
]


def main():
    db = sqlite3.connect(":memory:")
    db.executescript(DDL)
    db.executemany(
        "INSERT INTO approval(thread_id,node,asked_at,answered_at,actor,"
        "decision,shown,state_hash) VALUES (?,?,?,?,?,?,?,?)", ROWS)
    db.commit()

    print("승인 기록\n")
    print(f"{'스레드':<14}{'담당':<6}{'결정':<6}{'응답까지':>10}  보여 준 내용")
    print("-" * 78)
    for t, a, d, q, ans, shown in db.execute(
            "SELECT thread_id, actor, decision, asked_at, answered_at, shown "
            "FROM approval"):
        if ans:
            qh = int(q[11:13]) * 60 + int(q[14:16])
            ah = int(ans[11:13]) * 60 + int(ans[14:16])
            took = f"{ah - qh}분"
        else:
            took = "미응답"
        print(f"{t:<14}{(a or '-'):<6}{(d or '-'):<6}{took:>10}  {shown}")

    print(
        "\n«보여 준 내용» 칸이 이 표의 값어치다.\n"
        "\n결정만 남기면 나중에 «왜 승인했느냐»에 답할 수 없다.\n"
        "화면에 무엇이 떠 있었는지가 없으면, 담당자가 잘못 판단한 건지\n"
        "시스템이 잘못된 정보를 보여 준 건지 구분이 안 된다.\n"
        "\n실제로 저희는 이걸로 한 번 갈렸다. 승인은 났는데 사고가 났고,\n"
        "화면에 «3회차 환불»이 안 떠 있었다는 게 기록으로 남아 있었다.\n"
        "담당자 잘못이 아니라 화면 잘못이었다.\n"
        "\nstate_hash 는 그 순간의 상태 지문이다.\n"
        "재개할 때 지문이 다르면 «승인한 그 내용»과 «지금 실행할 내용»이 다른 것이다.\n"
        "그러면 다시 물어야 한다. 사흘 전 승인으로 오늘 4,200,000원을 내보내면 안 된다."
    )


if __name__ == "__main__":
    main()
