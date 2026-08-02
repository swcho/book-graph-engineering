"""
예제 3 — 다익스트라에 음수 가중치를 넣으면 조용히 틀린 답이 나온다.

    python3 ex3_dijkstra_negative.py

의존성 없음. 예외도 안 난다. 그게 무서운 점이다.
"""

import heapq
from collections import defaultdict

# 음수가 하나 있는 아주 작은 그래프
EDGES = [("A", "C", 1), ("A", "B", 2), ("B", "C", -5), ("C", "D", 1)]


def dijkstra(edges, start):
    adj = defaultdict(list)
    for a, b, w in edges:
        adj[a].append((b, w))
    dist = {start: 0}
    done = set()
    pq = [(0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if u in done:
            continue
        done.add(u)                      # 한 번 확정하면 다시 안 본다
        for v, w in adj[u]:
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist


def bellman_ford(edges, start, nodes):
    dist = {n: float("inf") for n in nodes}
    dist[start] = 0
    for _ in range(len(nodes) - 1):
        for a, b, w in edges:
            if dist[a] + w < dist[b]:
                dist[b] = dist[a] + w
    for a, b, w in edges:                # 한 바퀴 더 돌아 음수 사이클 검사
        if dist[a] + w < dist[b]:
            return dist, True
    return dist, False


def main():
    nodes = sorted({x for a, b, _ in EDGES for x in (a, b)})
    print("엣지:", EDGES, "\n")

    d1 = dijkstra(EDGES, "A")
    d2, has_cycle = bellman_ford(EDGES, "A", nodes)

    print(f"{'노드':<6} {'다익스트라':>12} {'벨만-포드':>12} {'같나':>6}")
    for n in nodes:
        a, b = d1.get(n, float("inf")), d2[n]
        print(f"{n:<6} {a:>12} {b:>12} {'예' if a == b else '아니오':>6}")

    print(f"\n음수 사이클: {'있다' if has_cycle else '없다'}")
    print(
        "\nC 는 맞고 D 는 틀렸다. 이 조합이 이 버그의 고약한 점이다.\n"
        "\n무슨 일이 있었나. A→C 가 1 이라 C 를 제일 먼저 꺼내 «확정»한다.\n"
        "그 상태에서 D 를 1+1=2 로 계산한다. 그 뒤에 B 를 처리하며\n"
        "A→B→C 가 -3 인 걸 알아내고 거리표에는 적는다. 그런데 C 는 이미 확정이라\n"
        "다시 펼치지 않는다. 그래서 D 는 2 로 남는다.\n"
        "\n거리표만 찍어 보면 C 가 맞으니 «잘 돌고 있네» 싶다.\n"
        "틀린 건 그 뒤쪽이다. 검증할 때 시작점 근처만 보면 놓친다.\n"
        "\n예외가 안 난다는 게 이 버그의 성질이다. 답이 그냥 조용히 틀린다.\n"
        "\n실무에서 음수 가중치가 생기는 자리:\n"
        "  - 할인이나 환급을 «음수 비용»으로 넣을 때\n"
        "  - 유사도를 «1 - 거리»로 바꿨는데 유사도가 1을 넘을 때\n"
        "  - 로그를 취했는데 값이 1보다 작을 때 (log 0.5 = -0.69)\n"
        "마지막이 제일 자주 봤다. 확률 곱을 최단 경로로 바꾸는 흔한 기법이다."
    )


if __name__ == "__main__":
    main()
