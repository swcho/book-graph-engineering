"""
예제 2 — 인덱스가 있고 없고. 그리고 «언제 안 듣나».

    pip install kuzu
    python3 ex2_index_effect.py

기본 키로 찾는 것과 속성으로 찾는 것을 나란히 잰다.
"""

import csv
import os
import shutil
import tempfile
import time

import kuzu

SIZES = [2000, 8000, 32000, 128000]


def build(path, n):
    db = kuzu.Database(path)
    c = kuzu.Connection(db)
    c.execute("CREATE NODE TABLE Person(id INT64, name STRING, city STRING, "
              "PRIMARY KEY(id))")
    d = os.path.dirname(path)
    cities = ["강남", "마포", "판교", "성수"]
    with open(f"{d}/p{n}.csv", "w", newline="") as f:
        w = csv.writer(f)
        for i in range(n):
            w.writerow([i, f"P{i}", cities[(i * 7) % 4]])
    c.execute(f"COPY Person FROM '{d}/p{n}.csv'")
    return c


def timed(c, q, params, reps=40):
    c.execute(q, params)
    t0 = time.perf_counter()
    for _ in range(reps):
        r = c.execute(q, params)
        while r.has_next():
            r.get_next()
    return (time.perf_counter() - t0) / reps * 1000


def main():
    tmp = tempfile.mkdtemp()
    print("같은 표에서 세 가지로 한 사람을 찾는다.\n")
    print(f"{'노드 수':>10}{'기본 키로':>12}{'속성으로':>12}"
          f"{'속성 + LIKE':>14}{'배수(속성/키)':>14}")
    print("-" * 64)
    for n in SIZES:
        c = build(f"{tmp}/db{n}", n)
        target = n // 2
        pk = timed(c, "MATCH (p:Person {id:$i}) RETURN p.name", {"i": target})
        at = timed(c, "MATCH (p:Person) WHERE p.name = $n RETURN p.id",
                   {"n": f"P{target}"})
        lk = timed(c, "MATCH (p:Person) WHERE p.name STARTS WITH $n "
                      "RETURN count(p)", {"n": f"P{target}"})
        print(f"{n:>10,}{pk:>12.3f}{at:>12.3f}{lk:>14.3f}{at / pk:>14.1f}x")

    print(
        "\n제가 기대한 건 «기본 키는 평평하고 속성은 비례해서 는다»였다. 아니었다.\n"
        "배수가 1.1 언저리에서 거의 안 변한다. 둘 다 비슷하게 늘어난다.\n"
        "\n이 규모에서는 «쿼리를 파싱하고 계획을 세우는» 값이 지배하기 때문이다.\n"
        "실제 찾기는 둘 다 1ms 도 안 걸리는데, 그 앞뒤에 붙는 고정 값이 훨씬 크다.\n"
        "\n그래서 배운 게 하나 있다. \u00ab인덱스 효과를 재려면 규모를 충분히 키워야 한다.\u00bb\n"
        "수천 개에서 재고 «인덱스가 별 효과 없네»라고 결론 내면 틀린다.\n"
        "그리고 반대로, 수천 개짜리 데이터에 인덱스를 붙이며 튜닝하는 것도 헛일이다.\n"
        "\n여기서 흔한 오해가 하나 더 있다. «인덱스를 걸면 다 빨라진다»가 아니다.\n"
        "인덱스는 «찾는 방식»에 맞아야 듣는다.\n"
        "\n  같음 비교(=)        → 해시 인덱스가 듣는다\n"
        "  범위 비교(<, >)      → 정렬 인덱스가 듣는다. 해시는 안 듣는다\n"
        "  앞부분 일치(STARTS)  → 정렬 인덱스가 듣는다\n"
        "  가운데 일치(CONTAINS) → 어느 것도 안 듣는다. 전문 검색이 필요하다\n"
        "\n그리고 그래프에서는 하나 더 있다.\n"
        "«관계를 따라가는 것»에는 인덱스가 필요 없다. 이미 이어져 있으니까.\n"
        "\n그래서 그래프 튜닝의 첫 질문은 «인덱스를 걸까»가 아니라\n"
        "«시작점을 인덱스로 찾고 나머지는 관계로 갈 수 있나»다.\n"
        "시작점 하나만 인덱스로 찾으면 그다음은 공짜다."
    )
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
