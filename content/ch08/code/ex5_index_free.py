"""
예제 5 — «인덱스 없는 인접성»이 무슨 뜻인가.

    python3 ex5_index_free.py

의존성 없음.
관계형: 이웃을 찾으려면 색인을 탄다. 색인은 로그 시간이고, 데이터가 늘면 깊어진다.
그래프:  이웃 목록의 주소를 노드가 직접 들고 있다. 데이터가 늘어도 그대로다.
"""

import math
import time
from bisect import bisect_left
from collections import defaultdict

from graphgen import make


def build_sorted_edges(edges):
    """색인을 흉내 낸다: 정렬된 배열 + 이진 탐색."""
    rows = sorted([(a, b) for a, b in edges] + [(b, a) for a, b in edges])
    keys = [r[0] for r in rows]
    return rows, keys


def neighbors_via_index(rows, keys, u):
    i = bisect_left(keys, u)
    out = []
    while i < len(keys) and keys[i] == u:
        out.append(rows[i][1]); i += 1
    return out


def neighbors_direct(adj, u):
    return adj[u]


def main():
    for n in (10_000, 100_000):
        edges = make(n=n, avg_deg=12)
        rows, keys = build_sorted_edges(edges)
        adj = defaultdict(list)
        for a, b in edges:
            adj[a].append(b); adj[b].append(a)

        probes = list(range(0, n, max(1, n // 2000)))

        t0 = time.perf_counter()
        for u in probes:
            neighbors_via_index(rows, keys, u)
        t_idx = (time.perf_counter() - t0) / len(probes) * 1e6

        t0 = time.perf_counter()
        for u in probes:
            neighbors_direct(adj, u)
        t_dir = (time.perf_counter() - t0) / len(probes) * 1e6

        print(f"노드 {n:>8,}  색인 방식 {t_idx:7.2f}us  직접 방식 {t_dir:7.2f}us  "
              f"이론 색인 깊이 {math.log2(len(rows)):.1f}")

    print(
        "\n색인 방식은 데이터가 늘면 탐색 깊이가 는다. 로그지만 늘긴 는다.\n"
        "직접 방식은 노드에서 이웃 목록으로 바로 간다. 전체 크기와 무관하다.\n"
        "\n이걸 «인덱스 없는 인접성(index-free adjacency)»이라고 부른다.\n"
        "그래프 데이터베이스가 조인보다 빠른 이유의 절반이 여기 있다.\n"
        "나머지 절반은 3장에서 본 «중간 결과가 안 곱해진다»이다.\n"
        "\n다만 «시작 노드를 찾는» 일에는 여전히 색인이 필요하다.\n"
        "이름으로 노드를 찾는 건 색인 없이는 전체 훑기다. 이 점을 자주 잊는다."
    )


if __name__ == "__main__":
    main()
