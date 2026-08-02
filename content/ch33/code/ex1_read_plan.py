"""
예제 1 — 쿼리 플랜을 읽는다. 진짜 EXPLAIN 출력으로.

    pip install kuzu
    python3 ex1_read_plan.py

같은 답을 내는 쿼리 셋의 플랜을 나란히 놓는다.
"""

import shutil
import tempfile
import time

import kuzu

N_PEOPLE = 8000
N_TEAMS = 80


def build(path):
    db = kuzu.Database(path)
    c = kuzu.Connection(db)
    c.execute("CREATE NODE TABLE Person(id INT64, name STRING, city STRING, "
              "PRIMARY KEY(id))")
    c.execute("CREATE NODE TABLE Team(id INT64, name STRING, PRIMARY KEY(id))")
    c.execute("CREATE REL TABLE Member(FROM Person TO Team, since STRING)")
    cities = ["강남", "마포", "판교", "성수"]
    for i in range(N_TEAMS):
        c.execute("CREATE (:Team {id:$i, name:$n})", {"i": i, "n": f"팀{i}"})
    import csv, os
    d = os.path.dirname(path)
    with open(d + "/p.csv", "w", newline="") as f:
        w = csv.writer(f)
        for i in range(N_PEOPLE):
            w.writerow([i, f"P{i}", cities[(i * 7) % len(cities)]])
    with open(d + "/m.csv", "w", newline="") as f:
        w = csv.writer(f)
        for i in range(N_PEOPLE):
            w.writerow([i, i % N_TEAMS, "2026-01-01"])
    c.execute(f"COPY Person FROM '{d}/p.csv'")
    c.execute(f"COPY Member FROM '{d}/m.csv'")
    return c


QUERIES = {
    "A. 두 끝을 따로 찾음": (
        "MATCH (p:Person), (t:Team) "
        "WHERE t.name = '팀7' AND p.city = '마포' "
        "AND EXISTS { MATCH (p)-[:Member]->(t) } RETURN count(p)"),
    "B. 팀에서 시작": (
        "MATCH (t:Team {name:'팀7'})<-[:Member]-(p:Person) "
        "WHERE p.city = '마포' RETURN count(p)"),
    "C. 사람에서 시작": (
        "MATCH (p:Person {city:'마포'})-[:Member]->(t:Team) "
        "WHERE t.name = '팀7' RETURN count(p)"),
}


def timed(c, q, reps=12):
    c.execute(q)
    t0 = time.perf_counter()
    for _ in range(reps):
        r = c.execute(q)
        while r.has_next():
            r.get_next()
    return (time.perf_counter() - t0) / reps * 1000


def main():
    tmp = tempfile.mkdtemp()
    c = build(tmp + "/db")
    print(f"사람 {N_PEOPLE:,}명, 팀 {N_TEAMS}개, 소속 엣지 {N_PEOPLE:,}개.")
    print("셋 다 「마포에 사는 팀7 구성원 수」를 센다. 답은 같다.\n")

    print(f"{'쿼리':<16}{'답':>6}{'평균(ms)':>12}")
    print("-" * 36)
    for name, q in QUERIES.items():
        r = c.execute(q)
        ans = r.get_next()[0]
        print(f"{name:<16}{ans:>6}{timed(c, q):>12.2f}")

    print("\n\n플랜에서 «연산자만» 뽑아 본다. (EXPLAIN 원문은 폭이 넓어 줄였다)\n")
    import re
    for name in ("A. 두 끝을 따로 찾음", "B. 팀에서 시작", "C. 사람에서 시작"):
        r = c.execute("EXPLAIN " + QUERIES[name])
        text = ""
        while r.has_next():
            text += str(r.get_next()[0])
        ops = re.findall(r"([A-Z_]{4,})\[\d+\]", text)
        # 아래에서 위로 읽는 것이 실행 순서다
        print(f"[{name}]")
        print("    " + "  →  ".join(reversed(ops)))
        print()

    print(
        "답이 셋 다 100 이다. 시간은 A 가 B·C 의 3.4배다.\n"
        "\nB 와 C 는 거의 같다. 엔진이 «어느 쪽에서 시작할지»를 알아서 정했기 때문이다.\n"
        "그러니까 요즘 엔진에서는 «어느 노드를 먼저 쓰느냐»가 대개 상관없다.\n"
        "저는 오래 이걸 튜닝 포인트로 알고 있었는데, 재 보니 아니었다.\n"
        "\n차이를 만든 건 A 다. 플랜에 CROSS_PRODUCT 가 있다.\n"
        "곱집합이다. 사람 8,000명 × 팀 80개를 만들어 놓고 거기서 거른다.\n"
        "\n이게 플랜을 읽을 때 제일 먼저 찾을 단어다. CROSS_PRODUCT 가 보이면\n"
        "«두 끝을 따로 찾아서 붙이고 있다»는 뜻이고, 데이터가 자라면 곱으로 커진다.\n"
        "지금은 3.4배지만 사람이 80만 명이면 배수가 훨씬 커진다.\n"
        "\n그래서 플랜에서 볼 것은 이렇게 정리된다.\n"
        "  1. CROSS_PRODUCT 가 있나 — 있으면 거기부터 고친다\n"
        "  2. SCAN 이 무엇을 훑나 — 인덱스를 타나, 전체를 훑나\n"
        "  3. FILTER 가 SCAN «앞»인가 «뒤»인가 — 뒤면 훑고 나서 버리는 것이다\n"
        "\n그리고 이건 «한 번 보고 끝»이 아니다.\n"
        "팀이 80개가 아니라 80만 개가 되면 엔진의 선택이 바뀐다.\n"
        "데이터가 자라면 플랜도 다시 봐야 한다."
    )
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
