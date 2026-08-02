"""
예제 4 — 커뮤니티 탐지 두 가지. 라벨 전파와 모듈러리티.

    python3 ex4_communities.py

의존성 없음.
"""

import random
from collections import Counter, defaultdict

from org import EDGES


def adjacency(edges):
    adj = defaultdict(set)
    for a, b in edges:
        adj[a].add(b); adj[b].add(a)
    return {k: sorted(v) for k, v in adj.items()}


def label_propagation(adj, seed=0, rounds=50):
    rnd = random.Random(seed)
    label = {v: i for i, v in enumerate(sorted(adj))}
    order = sorted(adj)
    for _ in range(rounds):
        rnd.shuffle(order)
        changed = False
        for v in order:
            if not adj[v]:
                continue
            cnt = Counter(label[u] for u in adj[v])
            best = max(cnt.items(), key=lambda x: (x[1], -x[0]))[0]
            if label[v] != best:
                label[v] = best; changed = True
        if not changed:
            break
    groups = defaultdict(list)
    for v, l in label.items():
        groups[l].append(v)
    return sorted((sorted(g) for g in groups.values()), key=len, reverse=True)


def modularity(adj, communities):
    m = sum(len(v) for v in adj.values()) / 2
    q = 0.0
    for c in communities:
        s = set(c)
        lc = sum(1 for v in c for u in adj[v] if u in s) / 2
        dc = sum(len(adj[v]) for v in c)
        q += lc / m - (dc / (2 * m)) ** 2
    return q


def greedy_modularity(adj):
    """작은 그래프용 탐욕 병합. 큰 그래프에는 루뱅 계열을 쓴다."""
    comms = [[v] for v in sorted(adj)]
    best_q = modularity(adj, comms)
    improved = True
    while improved and len(comms) > 1:
        improved = False
        best_pair, best_new = None, best_q
        for i in range(len(comms)):
            for j in range(i + 1, len(comms)):
                merged = comms[:i] + comms[i + 1:j] + comms[j + 1:] + [comms[i] + comms[j]]
                q = modularity(adj, merged)
                if q > best_new + 1e-12:
                    best_new, best_pair = q, (i, j)
        if best_pair:
            i, j = best_pair
            comms = comms[:i] + comms[i + 1:j] + comms[j + 1:] + [comms[i] + comms[j]]
            best_q = best_new
            improved = True
    return sorted((sorted(c) for c in comms), key=len, reverse=True), best_q


def show(title, comms, q=None):
    print(f"\n{title}" + (f"  (모듈러리티 {q:.3f})" if q is not None else ""))
    for i, c in enumerate(comms, 1):
        print(f"  {i}. ({len(c)}명) {', '.join(c)}")


def main():
    adj = adjacency(EDGES)

    print("라벨 전파 — 시드를 바꿔 세 번 돌린다")
    for seed in (0, 1, 2):
        comms = label_propagation(adj, seed=seed)
        print(f"  seed={seed}: 커뮤니티 {len(comms)}개, "
              f"크기 {[len(c) for c in comms]}, 모듈러리티 {modularity(adj, comms):.3f}")

    show("라벨 전파 (seed=0)", label_propagation(adj, 0))
    comms, q = greedy_modularity(adj)
    show("모듈러리티 최적화", comms, q)

    print(
        "\n라벨 전파는 빠른데 «시드에 따라 결과가 달라진다».\n"
        "같은 데이터로 어제와 오늘 다른 커뮤니티가 나오면 보고서를 못 쓴다.\n"
        "그래서 운영에 쓸 거면 시드를 고정하고, 고정했다는 사실을 문서에 적어야 한다.\n"
        "\n모듈러리티 최적화는 안정적인 대신 느리다.\n"
        "여기서는 탐욕 병합이라 노드 20개짜리에서만 쓸 만하다.\n"
        "실무에서는 루뱅(Louvain)이나 라이덴(Leiden) 계열을 쓴다."
    )


if __name__ == "__main__":
    main()
