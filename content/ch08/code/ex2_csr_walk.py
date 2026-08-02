"""
예제 2 — CSR 로 BFS 를 돌려 본다. 그리고 dict 판과 시간을 비교한다.

    python3 ex2_csr_walk.py

의존성 없음.
"""

import time
from array import array
from collections import defaultdict, deque

from graphgen import make

N = 50_000


def build_csr(edges, n):
    deg = [0] * n
    for a, b in edges:
        deg[a] += 1; deg[b] += 1
    offset = array("i", [0] * (n + 1))
    for i in range(n):
        offset[i + 1] = offset[i] + deg[i]
    cur = list(offset[:n])
    nbr = array("i", [0] * offset[n])
    for a, b in edges:
        nbr[cur[a]] = b; cur[a] += 1
        nbr[cur[b]] = a; cur[b] += 1
    return offset, nbr


def bfs_csr(offset, nbr, start, n):
    seen = bytearray(n)
    seen[start] = 1
    q = deque([start])
    visited = 0
    while q:
        u = q.popleft()
        visited += 1
        for i in range(offset[u], offset[u + 1]):     # 연속 구간 그대로 읽기
            v = nbr[i]
            if not seen[v]:
                seen[v] = 1
                q.append(v)
    return visited


def bfs_dict(adj, start):
    seen = {start}
    q = deque([start])
    visited = 0
    while q:
        u = q.popleft()
        visited += 1
        for v in adj.get(u, ()):                       # 객체를 따라 점프
            if v not in seen:
                seen.add(v)
                q.append(v)
    return visited


def main():
    edges = make(n=N, avg_deg=12)
    adj = defaultdict(list)
    for a, b in edges:
        adj[a].append(b); adj[b].append(a)
    offset, nbr = build_csr(edges, N)

    print(f"노드 {N:,} 엣지 {len(edges):,}\n")
    for name, fn in (("CSR", lambda: bfs_csr(offset, nbr, 0, N)),
                     ("dict of list", lambda: bfs_dict(adj, 0))):
        best, got = float("inf"), 0
        for _ in range(3):
            t0 = time.perf_counter()
            got = fn()
            best = min(best, time.perf_counter() - t0)
        print(f"  {name:<14} 방문 {got:,}개  {best*1000:8.1f} ms")

    print(
        "\n파이썬에서는 차이가 크지 않다. 인터프리터 오버헤드가 지배하기 때문이다.\n"
        "같은 코드를 C 나 Rust 로 옮기면 CSR 쪽이 보통 3~10배 빨라진다.\n"
        "\n그래도 파이썬에서 CSR 을 쓸 이유가 있다. 메모리다.\n"
        "앞 예제에서 8배 차이였다. 메모리에 안 들어가면 속도 논쟁은 의미가 없다."
    )


if __name__ == "__main__":
    main()
