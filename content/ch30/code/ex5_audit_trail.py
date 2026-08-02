"""
예제 5 — 이벤트 로그가 감사 로그가 되려면 무엇이 더 필요한가.

    python3 ex5_audit_trail.py

의존성 없음(표준 sqlite3, hashlib). 이벤트에 «고리»를 걸어
중간을 지우거나 고치면 표가 나게 만든다.
"""

import hashlib
import json
import sqlite3

DDL = """
CREATE TABLE log (
  seq   INTEGER PRIMARY KEY,
  at    TEXT, actor TEXT, op TEXT, payload TEXT,
  prev  TEXT,        -- 앞 항목의 해시
  hash  TEXT         -- 이 항목의 해시
);
"""

EVENTS = [
    ("2026-04-01T09:00", "hr-sync",    "추가", {"s": "박민수", "k": "이끔", "o": "결제팀"}),
    ("2026-04-01T09:00", "hr-sync",    "삭제", {"s": "박민수", "k": "이끔", "o": "결제팀"}),
    ("2026-04-01T09:01", "hr-sync",    "추가", {"s": "이서연", "k": "이끔", "o": "결제팀"}),
    ("2026-04-14T11:20", "agent-4821", "추가", {"s": "이서연", "k": "이끔", "o": "정산팀"}),
    ("2026-04-15T08:40", "admin:kim",  "삭제", {"s": "이서연", "k": "이끔", "o": "정산팀"}),
]


def digest(seq, at, actor, op, payload, prev):
    body = json.dumps([seq, at, actor, op, payload, prev],
                      ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(body.encode()).hexdigest()[:16]


def append(db, at, actor, op, payload):
    row = db.execute("SELECT seq, hash FROM log ORDER BY seq DESC "
                     "LIMIT 1").fetchone()
    seq = (row[0] + 1) if row else 1
    prev = row[1] if row else "-"
    h = digest(seq, at, actor, op, payload, prev)
    db.execute("INSERT INTO log VALUES (?,?,?,?,?,?,?)",
               (seq, at, actor, op, json.dumps(payload, ensure_ascii=False),
                prev, h))
    return seq


def verify(db):
    bad = []
    prev = "-"
    for seq, at, actor, op, payload, p, h in db.execute(
            "SELECT * FROM log ORDER BY seq"):
        want = digest(seq, at, actor, op, json.loads(payload), prev)
        if p != prev:
            bad.append((seq, "앞 고리가 안 맞음"))
        elif h != want:
            bad.append((seq, "내용이 바뀜"))
        prev = h
    return bad


def main():
    db = sqlite3.connect(":memory:")
    db.executescript(DDL)
    for at, actor, op, payload in EVENTS:
        append(db, at, actor, op, payload)
    db.commit()

    print("이벤트 5건을 고리로 이어 적었다.\n")
    print(f"{'seq':>4}  {'시각':<20}{'행위자':<13}{'op':<6}{'앞 고리':<18}{'해시'}")
    print("-" * 82)
    for seq, at, actor, op, payload, p, h in db.execute(
            "SELECT * FROM log ORDER BY seq"):
        print(f"{seq:>4}  {at:<20}{actor:<13}{op:<6}{p:<18}{h}")

    print(f"\n검증: {verify(db) or '이상 없음'}")

    print("\n\n이제 4번 항목을 몰래 고친다. 「이서연」을 「김도현」으로.")
    db.execute("UPDATE log SET payload=? WHERE seq=4",
               (json.dumps({"s": "김도현", "k": "이끔", "o": "정산팀"},
                           ensure_ascii=False),))
    db.commit()
    print(f"검증: {verify(db)}")

    print("\n\n이번엔 3번 항목을 통째로 지운다.")
    db.execute("UPDATE log SET payload=? WHERE seq=4",
               (json.dumps({"s": "이서연", "k": "이끔", "o": "정산팀"},
                           ensure_ascii=False),))
    db.execute("DELETE FROM log WHERE seq=3")
    db.commit()
    print(f"검증: {verify(db)}")

    print(
        "\n고리가 있으면 «고친 곳»과 «지운 곳»이 둘 다 잡힌다.\n"
        "고치면 그 항목의 해시가 안 맞고, 지우면 다음 항목의 앞 고리가 안 맞는다.\n"
        "\n이게 왜 필요한가. 이벤트 로그를 «감사 로그»로 쓰려면\n"
        "「나중에 안 고쳤다」를 증명할 수 있어야 하기 때문이다.\n"
        "\n그냥 테이블에 쌓아 두면 DB 접근 권한이 있는 사람이 고칠 수 있다.\n"
        "그리고 그런 권한을 가진 사람은 대개 여럿이다.\n"
        "\n다만 분명히 해 두자. 고리는 «막지» 않는다. «표가 나게» 할 뿐이다.\n"
        "전부 다시 계산하면 일관된 위조본을 만들 수 있다.\n"
        "그걸 막으려면 해시를 밖에 내보내야 한다. 다른 시스템에 적어 두거나,\n"
        "매일 한 번 어딘가에 공개하거나.\n"
        "\n대부분의 사내 시스템에서는 «표가 나는 것»만으로 충분하다.\n"
        "내부자가 작정하고 위조하는 것까지 막으려면 값이 확 뛴다.\n"
        "어디까지 막을지는 무엇을 지키는지에 달렸다."
    )


if __name__ == "__main__":
    main()
