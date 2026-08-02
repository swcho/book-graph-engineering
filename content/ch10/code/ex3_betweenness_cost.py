"""
예제 3 — 매개 중심성은 왜 비싼가. 그리고 근사가 왜 충분한가.

    python3 ex3_betweenness_cost.py

의존성 없음.
"""

import random
import time
from collections import defaultdict, deque
from itertools import combinations


def make(n, avg_deg=6, seed=11, groups=None):
    """커뮤니티 + 다리 구조. 무작위 그래프에서는 매개 중심성이 거의 평평해서
    근사 품질을 논할 수가 없다. 실제 그래프처럼 구조를 넣어야 의미가 있다."""
    rnd = random.Random(seed)
    groups = groups or max(4, n // 60)
    size = n // groups
    adj = defaultdict(set)
    for g in range(groups):
        lo, hi = g * size, min((g + 1) * size, n)
        members = list(range(lo, hi))
        for a in members:                       # 그룹 안은 촘촘하게
            for _ in range(avg_deg // 2):
                b = rnd.choice(members)
                if a != b:
                    adj[a].add(b); adj[b].add(a)
    for g in range(groups - 1):                 # 그룹 사이는 다리 하나씩
        a = g * size
        b = (g + 1) * size
        if b < n:
            adj[a].add(b); adj[b].add(a)
    for v in range(n):
        adj.setdefault(v, set())
    return {k: sorted(v) for k, v in adj.items()}


def brandes(adj, sources=None):
    """브랜디스 알고리즘. sources 를 주면 그 노드에서만 시작한다(근사)."""
    cb = {v: 0.0 for v in adj}
    for s in (sources if sources is not None else adj):
        stack, pred = [], {v: [] for v in adj}
        sigma = {v: 0 for v in adj}; sigma[s] = 1
        dist = {v: -1 for v in adj}; dist[s] = 0
        q = deque([s])
        while q:
            v = q.popleft(); stack.append(v)
            for w in adj[v]:
                if dist[w] < 0:
                    dist[w] = dist[v] + 1; q.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]; pred[w].append(v)
        delta = {v: 0.0 for v in adj}
        while stack:
            w = stack.pop()
            for v in pred[w]:
                delta[v] += sigma[v] / sigma[w] * (1 + delta[w])
            if w != s:
                cb[w] += delta[w]
    return cb


def top_overlap(a, b, k=20):
    ta = {v for v, _ in sorted(a.items(), key=lambda x: -x[1])[:k]}
    tb = {v for v, _ in sorted(b.items(), key=lambda x: -x[1])[:k]}
    return len(ta & tb) / k


def main():
    print(f"{'노드':>8} {'전수 계산(s)':>14} {'표본 5%(s)':>12} {'상위 20 일치':>13}")
    print("-" * 52)
    for n in (300, 800, 1600):
        adj = make(n)
        t0 = time.perf_counter(); exact = brandes(adj); t_exact = time.perf_counter() - t0
        sample = random.Random(3).sample(sorted(adj), max(5, n // 20))
        t0 = time.perf_counter(); approx = brandes(adj, sample); t_approx = time.perf_counter() - t0
        print(f"{n:>8} {t_exact:>14.2f} {t_approx:>12.2f} "
              f"{top_overlap(exact, approx)*100:>12.0f}%")

    print(
        "\n전수 계산은 노드 수에 비례해 BFS 를 n 번 돈다. O(V·E) 다.\n"
        "노드가 두 배가 되면 시간이 네 배쯤 된다. 100만 노드에서는 며칠이 걸린다.\n"
        "\n표본 5% 만 써도 상위 20개는 대부분 같다.\n"
        "«정확한 값»이 필요한 경우는 드물다. 대개 «누가 위에 있나»만 필요하다.\n"
        "\n다만 근사는 하위권에서 많이 틀린다. 값 자체를 보고할 거면 전수를 써야 한다.\n"
        "그리고 표본을 무작위로 뽑을 때 시드를 고정하지 않으면 매번 순위가 흔들린다.\n"
        "\n한 가지 더. 이 예제의 그래프는 커뮤니티와 다리가 있는 «구조 있는» 그래프다.\n"
        "완전 무작위 그래프에서 같은 실험을 하면 일치율이 10~50%로 떨어진다.\n"
        "매개 중심성이 거의 평평해서 상위 20개라는 게 사실상 무작위이기 때문이다.\n"
        "근사가 잘 듣는 건 «진짜 급소가 있는» 그래프에서다. 그리고 대개 그렇다."
    )


if __name__ == "__main__":
    main()
