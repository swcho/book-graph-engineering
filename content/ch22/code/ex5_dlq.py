"""
예제 5 — 데드레터 큐. 실패한 작업을 어디에 쌓고 어떻게 다시 꺼내나.

    python3 ex5_dlq.py

의존성 없음(표준 sqlite3 만 쓴다). 실패 원인을 나눠 담고 재처리한다.
"""

import sqlite3

DDL = """
CREATE TABLE dlq (
  id        INTEGER PRIMARY KEY,
  job       TEXT NOT NULL,
  reason    TEXT NOT NULL,     -- 왜 실패했나
  kind      TEXT NOT NULL,     -- 일시적 / 영구적 / 모름
  tries     INTEGER NOT NULL,
  payload   TEXT NOT NULL,
  status    TEXT NOT NULL      -- 대기 / 완료 / 포기
);
"""

JOBS = [
    ("환불",     "503 Service Unavailable", "일시적", 3, '{"order":"A-1024"}'),
    ("환불",     "잔액 부족",                "영구적", 1, '{"order":"A-1088"}'),
    ("알림 발송", "connection timeout",      "일시적", 3, '{"order":"A-1090"}'),
    ("재고 복구", "상품이 삭제됨",            "영구적", 1, '{"order":"A-1091"}'),
    ("환불",     "알 수 없는 500",           "모름",   3, '{"order":"A-1102"}'),
]


def retry(job, kind, attempt):
    """재처리 흉내. 일시적 실패는 2회차에 풀리고, 영구적은 영원히 안 풀린다."""
    if kind == "일시적":
        return attempt >= 2
    if kind == "영구적":
        return False
    return attempt >= 3       # 모름 — 늦게라도 풀릴 수 있다


def main():
    db = sqlite3.connect(":memory:")
    db.executescript(DDL)
    db.executemany(
        "INSERT INTO dlq(job, reason, kind, tries, payload, status) "
        "VALUES (?,?,?,?,?,'대기')", JOBS)
    db.commit()

    print("데드레터 큐에 5건이 쌓였다.\n")
    print(f"{'작업':<10}{'원인':<26}{'분류':<8}{'시도':>4}")
    print("-" * 50)
    for j, r, k, t, _p in JOBS:
        print(f"{j:<10}{r:<26}{k:<8}{t:>4}")

    print("\n일괄 재처리를 돌린다. 3회차까지.\n")
    print(f"{'주문':<10}{'분류':<8}{'결과':<24}{'총 시도':>8}")
    print("-" * 52)

    for rid, job, kind, tries, payload in db.execute(
            "SELECT id, job, kind, tries, payload FROM dlq WHERE status='대기'"):
        order = payload.split('"')[3]
        if kind == "영구적":          # 재시도해 봐야 소용없다. 호출을 아예 안 한다.
            db.execute("UPDATE dlq SET status='포기' WHERE id=?", (rid,))
            print(f"{order:<10}{kind:<8}{'재시도 없이 사람에게':<24}{tries:>8}")
            continue
        for a in range(1, 4):
            if retry(job, kind, a):
                db.execute("UPDATE dlq SET status='완료', tries=? WHERE id=?",
                           (tries + a, rid))
                print(f"{order:<10}{kind:<8}{'재처리 성공':<24}{tries + a:>8}")
                break
        else:
            db.execute("UPDATE dlq SET status='포기', tries=? WHERE id=?",
                       (tries + 3, rid))
            print(f"{order:<10}{kind:<8}{'사람이 봐야 함':<24}{tries + 3:>8}")
    db.commit()

    done = db.execute("SELECT COUNT(*) FROM dlq WHERE status='완료'").fetchone()[0]
    give = db.execute("SELECT COUNT(*) FROM dlq WHERE status='포기'").fetchone()[0]
    print(f"\n완료 {done}건, 사람 확인 {give}건")

    print(
        "\n여기서 값어치를 만드는 건 «분류» 칸이다.\n"
        "\n원인을 안 나누면 5건을 똑같이 3번씩 재시도한다. 15번 호출이다.\n"
        "잔액 부족은 백 번을 해도 안 풀리는데 세 번을 시도한다.\n"
        "\n분류를 붙이면 «영구적» 2건은 호출을 아예 안 한다. 9번으로 준다.\n"
        "그리고 사람이 볼 목록이 5건에서 2건으로 준다.\n"
        "\n분류를 어떻게 붙이냐고? HTTP 상태 코드로 대부분 갈린다.\n"
        "  429, 500, 502, 503, 504, 연결 오류 → 일시적\n"
        "  400, 402, 404, 409, 422        → 영구적\n"
        "  그 밖 / 응답 없음               → 모름\n"
        "\n«모름»을 없애려 하지 마시라. 모르는 건 모른다고 두고,\n"
        "재시도를 조금 더 준 다음 사람에게 넘기는 게 낫다."
    )


if __name__ == "__main__":
    main()
