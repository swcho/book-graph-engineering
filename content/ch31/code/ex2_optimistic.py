"""
예제 2 — 낙관적 잠금. 쓰기 직전에 «안 바뀌었나»만 확인한다.

    python3 ex2_optimistic.py

의존성 없음. 같은 경쟁을 세 방식으로 처리하고 결과를 비교한다.
"""

import random
import sqlite3
import threading
import time

DDL = """
CREATE TABLE node (id TEXT PRIMARY KEY, props TEXT, version INTEGER);
"""


def fresh():
    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.executescript(DDL)
    db.execute("INSERT INTO node VALUES ('t1', '팀장=박민수;인원=3', 1)")
    db.commit()
    return db


def parse(s):
    return dict(p.split("=") for p in s.split(";") if p)


def dump(d):
    return ";".join(f"{k}={v}" for k, v in sorted(d.items()))


LOCK = threading.Lock()
STATS = {"충돌": 0, "재시도": 0}


def naive(db, field, value, delay):
    with LOCK:
        props, _v = db.execute(
            "SELECT props, version FROM node WHERE id='t1'").fetchone()
    d = parse(props)
    time.sleep(delay)
    d[field] = value
    with LOCK:
        db.execute("UPDATE node SET props=? WHERE id='t1'", (dump(d),))
        db.commit()


def optimistic(db, field, value, delay, max_tries=5):
    for attempt in range(max_tries):
        with LOCK:
            props, ver = db.execute(
                "SELECT props, version FROM node WHERE id='t1'").fetchone()
        d = parse(props)
        time.sleep(delay)
        d[field] = value
        with LOCK:
            # 버전이 그대로일 때만 쓴다
            cur = db.execute(
                "UPDATE node SET props=?, version=version+1 "
                "WHERE id='t1' AND version=?", (dump(d), ver))
            db.commit()
            if cur.rowcount == 1:
                if attempt:
                    STATS["재시도"] += 1
                return True
            STATS["충돌"] += 1
        time.sleep(random.uniform(0.005, 0.03))   # 흔들기 (22장)
    return False


def field_level(db, field, value, delay):
    """통째로 안 쓰고 «그 필드만» 고친다. 읽고-고치고-쓰기 창이 없다."""
    time.sleep(delay)
    with LOCK:
        props, _v = db.execute(
            "SELECT props, version FROM node WHERE id='t1'").fetchone()
        d = parse(props)
        d[field] = value
        db.execute("UPDATE node SET props=?, version=version+1 "
                   "WHERE id='t1'", (dump(d),))
        db.commit()


def run(fn, label):
    STATS.update({"충돌": 0, "재시도": 0})
    db = fresh()
    ts = [threading.Thread(target=fn, args=(db, f, v, d))
          for f, v, d in (("팀장", "이서연", 0.20), ("인원", "5", 0.05))]
    for t in ts:
        t.start()
        time.sleep(0.02)
    for t in ts:
        t.join()
    props = parse(db.execute(
        "SELECT props FROM node WHERE id='t1'").fetchone()[0])
    ok = props.get("팀장") == "이서연" and props.get("인원") == "5"
    return label, dump(props), ok, dict(STATS)


def main():
    print("같은 경쟁(다른 필드를 동시에 수정)을 세 방식으로 처리한다.\n")
    print(f"{'방식':<20}{'최종 상태':<26}{'둘 다 반영':<12}{'충돌/재시도'}")
    print("-" * 74)
    for fn, label in ((naive, "그냥 쓰기"),
                      (optimistic, "낙관적 잠금"),
                      (field_level, "필드 단위 수정")):
        label, final, ok, st = run(fn, label)
        print(f"{label:<20}{final:<26}{'○' if ok else '✗ 하나 사라짐':<12}"
              f"{st['충돌']}/{st['재시도']}")

    print(
        "\n낙관적 잠금은 «버전»을 하나 두고, 쓸 때 그 버전이 그대로인지 본다.\n"
        "  UPDATE node SET props=?, version=version+1\n"
        "   WHERE id=? AND version=?          ← 이 조건이 전부다\n"
        "\n버전이 바뀌었으면 UPDATE 가 «0행»을 고친다. 그게 충돌 신호다.\n"
        "그러면 다시 읽고 다시 시도한다.\n"
        "\n이름이 «낙관적»인 이유는 «대개 충돌 안 난다»고 보고 미리 안 막기 때문이다.\n"
        "충돌이 잦으면 재시도가 늘어서 오히려 손해가 된다. 그때는 잠금이 낫다.\n"
        "\n필드 단위 수정은 아예 창을 없앤다. 읽기와 쓰기 사이에 «판단»을 안 둔다.\n"
        "가능하면 이게 제일 낫다. 다만 «읽은 값을 보고 판단해야» 하는 경우엔 못 쓴다.\n"
        "  「인원이 5 미만이면 한 명 추가」 같은 조건이 있으면 읽어야 하니까.\n"
        "\n그래서 실무에서는 이렇게 나눈다.\n"
        "  단순 설정 → 필드 단위\n"
        "  읽고 판단해야 함 → 낙관적 잠금\n"
        "  충돌이 잦고 비용이 큼 → 비관적 잠금(다음 예제)"
    )


if __name__ == "__main__":
    main()
