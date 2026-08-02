"""
예제 2 — 같은 질문을 표와 그래프로. 홉이 늘어날 때 무슨 일이 생기나.

    python3 ex2_sql_vs_graph.py

의존성 없음 (sqlite3 는 표준 라이브러리).
질문: "0번 사람에서 k다리 건너 아는 사람은 몇 명인가?"
"""

import sqlite3
import time

from graphdata import N_PEOPLE, adjacency, make_edges

MAX_HOP = 4


def build_sqlite(edges):
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE friends (a INTEGER, b INTEGER)")
    rows = [(a, b) for a, b in edges] + [(b, a) for a, b in edges]
    con.executemany("INSERT INTO friends VALUES (?, ?)", rows)
    con.execute("CREATE INDEX idx_a ON friends(a)")   # 인덱스는 공평하게 준다
    con.commit()
    return con


def sql_khop(con, start, k):
    """조인을 k번 겹친다. 사람이 손으로 쓰는 그 쿼리."""
    joins = "".join(
        f" JOIN friends f{i} ON f{i}.a = f{i-1}.b" for i in range(2, k + 1)
    )
    sql = (f"SELECT COUNT(DISTINCT f{k}.b) FROM friends f1{joins} WHERE f1.a = ?")
    cur = con.execute(sql, (start,))
    return cur.fetchone()[0]


def graph_khop(adj, start, k):
    """이웃 목록을 k번 따라간다. 방문한 것만 읽는다."""
    frontier, seen = {start}, {start}
    for _ in range(k):
        nxt = set()
        for node in frontier:
            nxt.update(adj[node])
        frontier = nxt - seen
        seen |= nxt
    return len(frontier)


def timed(fn, *args, repeat=5):
    best = float("inf")
    out = None
    for _ in range(repeat):
        t0 = time.perf_counter()
        out = fn(*args)
        best = min(best, time.perf_counter() - t0)
    return out, best * 1000


def main():
    edges = make_edges()
    adj = adjacency(edges)
    con = build_sqlite(edges)

    print(f"사람 {N_PEOPLE}명, 친구 관계 {len(edges)}개 (양방향 {len(edges)*2}행)\n")
    print(f"{'홉':>3} {'SQL 조인(ms)':>14} {'그래프 순회(ms)':>16} {'배수':>8}")
    print("-" * 46)
    for k in range(1, MAX_HOP + 1):
        _, t_sql = timed(sql_khop, con, 0, k)
        _, t_g = timed(graph_khop, adj, 0, k)
        print(f"{k:>3} {t_sql:>14.2f} {t_g:>16.3f} {t_sql / max(t_g, 1e-9):>7.0f}x")

    print(
        "\n표가 느린 건 SQLite 탓이 아니다. 조인을 겹칠 때마다 중간 결과가 곱해지기 때문이다.\n"
        "그래프는 방문한 노드만 읽는다. 그래서 홉이 늘어도 «도달한 만큼»만 는다.\n"
        "\n다만 1홉에서는 표가 밀리지 않는다. 오히려 빠를 때도 있다.\n"
        "이 예제의 결론은 «표가 나쁘다»가 아니라 «깊이가 비용을 정한다»이다."
    )


if __name__ == "__main__":
    main()
