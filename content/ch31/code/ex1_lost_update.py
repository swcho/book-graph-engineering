"""
예제 1 — 잃어버린 갱신. 둘이 동시에 고치면 하나가 사라진다.

    python3 ex1_lost_update.py

의존성 없음(표준 sqlite3, threading). 진짜 스레드로 경쟁시킨다.
"""

import sqlite3
import threading
import time

DDL = """
CREATE TABLE node (
  id      TEXT PRIMARY KEY,
  props   TEXT,
  version INTEGER
);
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


def naive_update(db, field, value, delay, log):
    """읽고 → 고치고 → 쓴다. 그 사이에 남이 끼어들 수 있다."""
    with LOCK:
        row = db.execute("SELECT props FROM node WHERE id='t1'").fetchone()
    props = parse(row[0])
    log.append(f"  [{field}] 읽음: {row[0]}")
    time.sleep(delay)                      # 판단하는 시간
    props[field] = value
    with LOCK:
        db.execute("UPDATE node SET props=? WHERE id='t1'", (dump(props),))
        db.commit()
    log.append(f"  [{field}] 씀:   {dump(props)}")


def run(delays):
    db = fresh()
    log = []
    ts = [threading.Thread(target=naive_update,
                           args=(db, f, v, d, log))
          for f, v, d in delays]
    for t in ts:
        t.start()
        time.sleep(0.02)                   # 읽는 시점을 겹치게 만든다
    for t in ts:
        t.join()
    final = db.execute("SELECT props FROM node WHERE id='t1'").fetchone()[0]
    return log, final


def main():
    print("한 노드의 «서로 다른 필드»를 두 에이전트가 동시에 고친다.\n")
    print("  에이전트 A: 팀장 = 이서연   (판단에 0.20초)")
    print("  에이전트 B: 인원 = 5       (판단에 0.05초)\n")

    log, final = run([("팀장", "이서연", 0.20), ("인원", "5", 0.05)])
    for l in log:
        print(l)

    print(f"\n최종 상태: {final}")
    props = parse(final)
    print(f"\n팀장 = {props['팀장']}, 인원 = {props['인원']}")

    lost = []
    if props["팀장"] != "이서연":
        lost.append("팀장 변경")
    if props["인원"] != "5":
        lost.append("인원 변경")
    print(f"사라진 변경: {lost or '없음'}")

    print(
        "\n두 에이전트가 «다른 필드»를 고쳤는데 하나가 사라졌다.\n"
        "\n순서를 보시라. 둘 다 «같은 옛 상태»를 읽었다.\n"
        "그다음 각자 자기 필드를 고쳐서 «통째로» 썼다.\n"
        "나중에 쓴 쪽이 앞 쪽의 변경을 덮는다.\n"
        "\n이걸 잃어버린 갱신(lost update)이라고 부른다.\n"
        "에러가 안 난다. 로그에도 «성공»만 찍힌다. 그게 이 문제의 성질이다.\n"
        "\n30장에서 «전체 상태를 이벤트에 넣지 마라»고 한 이유가 이것이다.\n"
        "전체를 쓰면 겹치지 않는 변경도 서로를 덮는다.\n"
        "\n대응은 셋이다.\n"
        "  1. 잠금 — 한 번에 하나만 고치게 한다. 느리고 데드락이 난다\n"
        "  2. 낙관적 잠금 — 쓰기 직전에 «안 바뀌었나» 확인한다\n"
        "  3. 필드 단위 변경 — 통째로 안 쓰고 바뀐 것만 쓴다\n"
        "\n2번과 3번을 같이 쓰는 게 실무의 답이다. 다음 예제들에서 본다."
    )


if __name__ == "__main__":
    main()
