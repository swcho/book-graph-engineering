"""
예제 4 — 임베딩 없이도 되는 링크 예측, 그리고 임베딩이 필요해지는 지점.

    python3 ex4_link_prediction.py

의존성 없음.
"""

from collections import defaultdict
from itertools import combinations

EDGES = [
    ("가온테크", "재시도"), ("가온테크", "멱등성없음"),
    ("나루소프트", "재시도"), ("나루소프트", "멱등성없음"), ("나루소프트", "캐시"),
    ("다올물산", "재시도"),
    ("라온에너지", "멱등성없음"), ("라온에너지", "캐시"),
    ("마루상사", "캐시"),
]


def adjacency(edges):
    adj = defaultdict(set)
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    return adj


def common_neighbors(adj, u, v):
    return len(adj[u] & adj[v])


def adamic_adar(adj, u, v):
    """이웃이 적은 공통 이웃일수록 더 값지다. 1홉만 봐도 이 정도는 된다."""
    import math
    return round(sum(1 / math.log(len(adj[w])) for w in adj[u] & adj[v]
                     if len(adj[w]) > 1), 3)


def main():
    adj = adjacency(EDGES)
    companies = sorted({a for a, _ in EDGES})

    print("아직 이어지지 않은 (회사, 원인) 쌍 중 이어질 법한 것")
    causes = sorted({b for _, b in EDGES})
    cand = [(c, x) for c in companies for x in causes if x not in adj[c]]
    scored = []
    for c, x in cand:
        # 회사 c 와 «x 를 가진 다른 회사들» 의 공통 이웃 수로 점수를 낸다
        peers = [p for p in companies if x in adj[p] and p != c]
        score = sum(common_neighbors(adj, c, p) for p in peers)
        scored.append((score, c, x))
    scored.sort(reverse=True)
    for s, c, x in scored[:5]:
        print(f"  점수 {s}: {c} ↔ {x}")

    print("\n왜 이 점수가 나왔는지 되짚을 수 있다")
    s, c, x = scored[0]
    peers = [p for p in companies if x in adj[p] and p != c]
    ranked = sorted(peers, key=lambda p: -len(adj[c] & adj[p]))
    for p in ranked:
        shared = sorted(adj[c] & adj[p])
        print(f"  {c} 와 {p} 가 함께 가진 원인: {shared or '(없음)'}")
    best = ranked[0]
    print(f"  → {best} 와 원인 {sorted(adj[c] & adj[best])} 를 공유한다.")
    print(f"     그 {best} 가 {x} 를 겪었으니 {c} 도 겪을 수 있다는 추론이다.")

    print(
        "\n여기까지는 임베딩이 필요 없다. 이웃만 세면 된다.\n"
        "임베딩이 필요해지는 건 «공통 이웃이 0인데 비슷한» 경우다.\n"
        "예: 두 회사가 겹치는 원인이 하나도 없는데, 각자의 이웃들이 서로 비슷할 때.\n"
        "그때는 2홉·3홉 구조를 좌표로 눌러 담아야 비교가 된다.\n"
        "\n대신 그 순간 위의 «되짚기» 출력이 사라진다. 이게 이 장의 거래다."
    )


if __name__ == "__main__":
    main()
