"""
예제 5 — 해상도 한계. 모듈러리티는 작은 커뮤니티를 못 본다.

    python3 ex5_resolution.py

의존성 없음.
«고리 모양으로 이어진 작은 뭉치들»을 만들어 놓고 찾아보게 한다.
정답은 뭉치 하나하나인데, 모듈러리티는 이웃한 뭉치들을 붙여 버린다.
"""

from collections import defaultdict


def ring_of_cliques(k, size):
    """크기 size 인 완전 그래프 k 개를 고리 모양으로 잇는다. 정답 커뮤니티 = k 개."""
    edges = []
    for c in range(k):
        base = c * size
        for i in range(size):
            for j in range(i + 1, size):
                edges.append((base + i, base + j))
        edges.append((base, ((c + 1) % k) * size))     # 다음 뭉치와 다리 하나
    return edges


def adjacency(edges):
    adj = defaultdict(set)
    for a, b in edges:
        adj[a].add(b); adj[b].add(a)
    return {k: sorted(v) for k, v in adj.items()}


def modularity(adj, comms, gamma=1.0):
    """gamma 가 해상도 매개변수. 크면 잘게, 작으면 크게 나눈다."""
    m = sum(len(v) for v in adj.values()) / 2
    q = 0.0
    for c in comms:
        s = set(c)
        lc = sum(1 for v in c for u in adj[v] if u in s) / 2
        dc = sum(len(adj[v]) for v in c)
        q += lc / m - gamma * (dc / (2 * m)) ** 2
    return q


def truth(k, size):
    return [list(range(c * size, (c + 1) * size)) for c in range(k)]


def merged_pairs(k, size):
    """이웃한 두 뭉치를 하나로 붙인 답."""
    out = []
    for c in range(0, k - 1, 2):
        out.append(list(range(c * size, (c + 2) * size)))
    if k % 2:
        out.append(list(range((k - 1) * size, k * size)))
    return out


def main():
    size = 4
    print(f"뭉치 크기 {size}, 고리 모양으로 이음\n")
    print(f"{'뭉치 수':>8} {'정답 Q':>10} {'둘씩 붙인 Q':>12} {'어느 쪽이 이기나':>18}")
    print("-" * 54)
    for k in (4, 8, 16, 24, 32):
        edges = ring_of_cliques(k, size)
        adj = adjacency(edges)
        q_true = modularity(adj, truth(k, size))
        q_merged = modularity(adj, merged_pairs(k, size))
        winner = "정답" if q_true > q_merged else "붙인 쪽 (틀림)"
        print(f"{k:>8} {q_true:>10.4f} {q_merged:>12.4f} {winner:>18}")

    print(
        "\n뭉치가 많아지면 «둘씩 붙인» 답의 모듈러리티가 정답을 이긴다.\n"
        "모듈러리티를 최대화하는 알고리즘은 그래서 작은 뭉치를 붙여 버린다.\n"
        "이걸 해상도 한계(resolution limit)라고 부른다. 버그가 아니라 지표의 성질이다.\n"
        "\n대처법 두 가지.\n"
        "  1. 해상도 매개변수 gamma 를 올린다. 잘게 나뉜다. 값은 실험으로 정한다.\n"
        "  2. 커뮤니티를 찾은 뒤 각 커뮤니티 안에서 다시 돌린다(계층적).\n"
        "\n둘 다 «정답이 몇 개인지 모른다»는 문제를 근본적으로 풀지는 못한다.\n"
        "그래서 커뮤니티 개수는 알고리즘이 정하게 두지 말고 «쓰임새»로 정하는 게 낫다.\n"
        "요약문을 만들 거면 요약 하나가 다룰 만한 크기로, 라우팅에 쓸 거면 라우팅 단위로."
    )


if __name__ == "__main__":
    main()
