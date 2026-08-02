"""
예제 1 — 네 가지 중심성. 1등이 서로 다르다.

    python3 ex1_centralities.py

의존성 없음. 다 직접 구현한다. 20~40줄이면 된다.
"""

from collections import defaultdict, deque
from itertools import combinations

from org import EDGES


def adjacency(edges):
    adj = defaultdict(set)
    for a, b in edges:
        adj[a].add(b); adj[b].add(a)
    return {k: sorted(v) for k, v in adj.items()}


def degree_c(adj):
    n = len(adj) - 1
    return {v: len(nb) / n for v, nb in adj.items()}


def bfs_dist(adj, s):
    d = {s: 0}
    q = deque([s])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in d:
                d[v] = d[u] + 1
                q.append(v)
    return d


def closeness_c(adj):
    out = {}
    for v in adj:
        d = bfs_dist(adj, v)
        total = sum(d.values())
        out[v] = (len(d) - 1) / total if total else 0
    return out


def betweenness_c(adj):
    """모든 쌍의 최단 경로를 세고, 각 노드가 몇 번 «지나가는 길목»이었는지 센다."""
    score = {v: 0.0 for v in adj}
    for s, t in combinations(sorted(adj), 2):
        paths = all_shortest(adj, s, t)
        if not paths:
            continue
        for p in paths:
            for mid in p[1:-1]:
                score[mid] += 1 / len(paths)
    n = len(adj)
    norm = (n - 1) * (n - 2) / 2
    return {v: s / norm for v, s in score.items()}


def all_shortest(adj, s, t):
    d = bfs_dist(adj, s)
    if t not in d:
        return []
    out, stack = [], [(t, [t])]
    while stack:
        u, path = stack.pop()
        if u == s:
            out.append(list(reversed(path)))
            continue
        for v in adj[u]:
            if d.get(v, -1) == d[u] - 1:
                stack.append((v, path + [v]))
    return out


def eigen_c(adj, rounds=100):
    """고유벡터 중심성 — «중요한 이웃»을 가진 노드가 중요하다."""
    x = {v: 1.0 for v in adj}
    for _ in range(rounds):
        nx = {v: sum(x[u] for u in adj[v]) for v in adj}
        norm = max(nx.values()) or 1
        nx = {v: y / norm for v, y in nx.items()}
        if all(abs(nx[v] - x[v]) < 1e-9 for v in adj):
            break
        x = nx
    return x


def main():
    adj = adjacency(EDGES)
    metrics = {
        "차수": degree_c(adj),
        "근접": closeness_c(adj),
        "매개": betweenness_c(adj),
        "고유벡터": eigen_c(adj),
    }
    print(f"{'노드':<10}" + "".join(f"{k:>10}" for k in metrics))
    print("-" * 52)
    for v in sorted(adj, key=lambda x: -metrics["차수"][x]):
        print(f"{v:<10}" + "".join(f"{metrics[k][v]:>10.3f}" for k in metrics))

    print(f"\n{'지표':<10} {'1등':<10} {'2등':<10}")
    for k, m in metrics.items():
        rank = sorted(m, key=lambda v: -m[v])
        print(f"{k:<10} {rank[0]:<10} {rank[1]:<10}")

    # 차수는 낮은데 매개가 높은 사람 — 아무도 안 알아보는 급소
    hidden = sorted(adj, key=lambda v: -(metrics["매개"][v] - metrics["차수"][v]))[0]
    print(f"\n차수 대비 매개가 제일 높은 사람: {hidden}"
          f"  (차수 {metrics['차수'][hidden]:.3f} / 매개 {metrics['매개'][hidden]:.3f})")

    print(
        "\n1등이 지표마다 다르다는 게 이 예제의 전부다.\n"
        "그리고 진짜 급소는 1등이 아니라 «차수는 낮은데 매개가 높은» 사람이다.\n"
        "서영업은 아는 사람이 적다. 그런데 외주 공장으로 가는 유일한 통로다.\n"
        "조직도에도 안 보이고 차수 순위에도 안 뜬다. 휴가를 가면 공장이 멈춘다.\n"
        "\n«중요한 사람을 찾아 주세요»라는 요구를 받으면 되물어야 한다.\n"
        "  - 아는 사람이 많은 사람인가 (차수)\n"
        "  - 없으면 조직이 갈라지는 사람인가 (매개)\n"
        "  - 소문이 제일 빨리 퍼지는 사람인가 (근접)\n"
        "  - 힘 있는 사람과 이어진 사람인가 (고유벡터)\n"
        "네 개가 다 다른 질문이고, 다른 사람을 가리킨다."
    )


if __name__ == "__main__":
    main()
