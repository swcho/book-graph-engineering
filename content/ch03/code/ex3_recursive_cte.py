"""
예제 3 — 재귀 CTE. 관계형이 그래프 질의를 흉내 내는 표준 방법.

    python3 ex3_recursive_cte.py

의존성 없음. SQL:1999 부터 표준이다. 되긴 된다.
되는데, 어디가 불편한지를 보고 넘어가자.
"""

import sqlite3
import time

from graphdata import adjacency, make_edges
from ex2_sql_vs_graph import build_sqlite, graph_khop

CTE = """
WITH RECURSIVE reach(node, depth) AS (
    SELECT ?, 0
    UNION
    SELECT f.b, r.depth + 1
      FROM reach r JOIN friends f ON f.a = r.node
     WHERE r.depth < ?
)
SELECT COUNT(*) FROM reach WHERE depth = ?
"""


def main():
    edges = make_edges()
    adj = adjacency(edges)
    con = build_sqlite(edges)

    print("재귀 CTE 로 «정확히 k다리 건너» 세기\n")
    print(f"{'홉':>3} {'재귀 CTE':>12} {'순회':>10} {'CTE(ms)':>10} {'순회(ms)':>10}")
    print("-" * 50)
    for k in (1, 2, 3, 4):
        t0 = time.perf_counter()
        n_cte = con.execute(CTE, (0, k, k)).fetchone()[0]
        t_cte = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        n_g = graph_khop(adj, 0, k)
        t_g = (time.perf_counter() - t0) * 1000

        print(f"{k:>3} {n_cte:>12} {n_g:>10} {t_cte:>10.2f} {t_g:>10.3f}")

    print(
        "\n숫자가 다르다. 왜 그런지가 이 예제의 핵심이다.\n"
        "\nUNION 이 중복을 지우지만 «어느 깊이에서 처음 만났는지»는 남지 않는다.\n"
        "같은 사람이 2홉과 3홉 양쪽으로 도달되면 두 행이 다 살아남는다.\n"
        "정확한 «최단 거리 k» 를 원하면 깊이별 방문 집합을 직접 관리해야 하고,\n"
        "그 순간 SQL 로 쓰는 이점이 사라진다.\n"
        "\n재귀 CTE 가 나쁜 게 아니다. 표라는 자료구조에 «방문 표시»를 둘 자리가 없을 뿐이다."
    )


if __name__ == "__main__":
    main()
