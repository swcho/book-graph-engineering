"""
예제 3 — 가중치가 «거리»인가 «강도»인가. 뒤집으면 답이 반대로 나온다.

    python3 ex3_weights.py

의존성 없음. 다익스트라를 직접 짠다(9장에서 다시 다룬다).
"""

import heapq
from collections import defaultdict

# 같은 숫자를 두 가지 뜻으로 읽어 본다.
#  강도 해석: 값이 클수록 가깝다 (친밀도, 유사도, 거래액)
#  거리 해석: 값이 클수록 멀다 (비용, 시간, 요금)
EDGES = [("A", "B", 8), ("B", "C", 8), ("A", "D", 3), ("D", "C", 3)]


def dijkstra(edges, start, goal, as_distance=True):
    adj = defaultdict(list)
    for a, b, w in edges:
        cost = w if as_distance else 1.0 / w
        adj[a].append((b, cost))
        adj[b].append((a, cost))
    dist = {start: 0.0}
    prev = {}
    pq = [(0.0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if u == goal:
            break
        if d > dist.get(u, float("inf")):
            continue
        for v, c in adj[u]:
            nd = d + c
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    path, cur = [goal], goal
    while cur in prev:
        cur = prev[cur]
        path.append(cur)
    return list(reversed(path)), round(dist.get(goal, float("inf")), 3)


def main():
    print("엣지:", EDGES)
    print("\nA 에서 C 로 가는 «가장 좋은» 경로는?\n")

    p1, c1 = dijkstra(EDGES, "A", "C", as_distance=True)
    print(f"  숫자를 «거리»로 읽으면: {' → '.join(p1)}  (합 {c1})")
    p2, c2 = dijkstra(EDGES, "A", "C", as_distance=False)
    print(f"  숫자를 «강도»로 읽으면: {' → '.join(p2)}  (합 {c2})")

    print(
        "\n같은 데이터, 반대 답이다.\n"
        "\n제가 실제로 겪은 사고가 이거였다. 친밀도(클수록 가깝다)를 저장해 놓고\n"
        "최단 경로 알고리즘에 그대로 넣었다. 알고리즘은 «작을수록 가깝다»로 읽는다.\n"
        "그래서 제일 안 친한 경로를 «가장 가까운 사이»라고 답했다. 2주 만에 알았다.\n"
        "\n예방법 하나. 속성 이름에 뜻을 박아 넣는다.\n"
        "  weight (X)  →  cost_minutes, affinity_score (O)\n"
        "이름 하나로 막을 수 있는 사고를 이름을 아껴서 만든다."
    )


if __name__ == "__main__":
    main()
