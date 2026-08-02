"""
예제 4 — «최단 경로 하나»와 «모든 경로»는 완전히 다른 문제다.

    python3 ex4_path_explosion.py

의존성 없음.
"""

from collections import defaultdict, deque

# 격자 모양 그래프. 경로 개수가 조합으로 는다.
def grid(w, h):
    adj = defaultdict(list)
    for x in range(w):
        for y in range(h):
            if x + 1 < w:
                adj[(x, y)].append((x + 1, y))
            if y + 1 < h:
                adj[(x, y)].append((x, y + 1))
    return adj


def count_paths(adj, s, t):
    memo = {}
    def go(u):
        if u == t:
            return 1
        if u in memo:
            return memo[u]
        memo[u] = sum(go(v) for v in adj[u])
        return memo[u]
    return go(s)


def shortest_len(adj, s, t):
    q, seen = deque([(s, 0)]), {s}
    while q:
        u, d = q.popleft()
        if u == t:
            return d
        for v in adj[u]:
            if v not in seen:
                seen.add(v); q.append((v, d + 1))
    return -1


def main():
    print(f"{'격자':>8} {'최단 경로 길이':>14} {'서로 다른 경로 수':>20}")
    print("-" * 46)
    for n in (3, 5, 8, 11, 15, 20):
        adj = grid(n, n)
        s, t = (0, 0), (n - 1, n - 1)
        print(f"{f'{n}x{n}':>8} {shortest_len(adj, s, t):>14} "
              f"{count_paths(adj, s, t):>20,}")

    print(
        "\n최단 경로 길이는 선형으로 늘고, 경로 개수는 조합으로 는다.\n"
        "20x20 격자에서 경로가 350억 개가 넘는다. 세는 건 되는데 나열은 못 한다.\n"
        "\n그래서 «모든 경로를 보여 줘»라는 요구가 오면 되물어야 한다.\n"
        "  - 정말 전부인가, 아니면 «가장 짧은 것 몇 개»인가\n"
        "  - 길이 상한이 있나\n"
        "  - 중간에 반드시 지나야 할 노드가 있나\n"
        "\n제가 겪은 장애 중 하나가 이거였다. «영향 범위를 다 보여 줘»를\n"
        "모든 경로 열거로 구현했고, 어느 날 노드 하나가 슈퍼 노드가 됐다."
    )


if __name__ == "__main__":
    main()
