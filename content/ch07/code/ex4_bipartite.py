"""
예제 4 — 이분 그래프와 투영. 편해 보이는데 엣지가 제곱으로 는다.

    python3 ex4_bipartite.py

의존성 없음.
"""

from collections import defaultdict
from itertools import combinations

PURCHASES = [
    ("u1", "상품A"), ("u1", "상품B"),
    ("u2", "상품A"), ("u2", "상품B"), ("u2", "상품C"),
    ("u3", "상품C"),
]


def project(pairs, side=1):
    """한쪽으로 투영. 같은 상대를 공유하면 잇는다."""
    grouped = defaultdict(set)
    for a, b in pairs:
        key, val = (a, b) if side == 0 else (b, a)
        grouped[val].add(key)
    out = defaultdict(int)
    for val, keys in grouped.items():
        for x, y in combinations(sorted(keys), 2):
            out[(x, y)] += 1
    return dict(out)


def simulate(n_users, items_per_user):
    """투영 엣지 수가 어떻게 느는지 계산으로 본다."""
    return n_users * items_per_user * (items_per_user - 1) // 2


def main():
    print("원본 이분 그래프")
    for p in PURCHASES:
        print("  ", p)
    print(f"  엣지 {len(PURCHASES)}개\n")

    proj = project(PURCHASES, side=1)
    print("상품 쪽으로 투영 (함께 산 상품끼리 잇기)")
    for (a, b), w in sorted(proj.items()):
        print(f"   {a} — {b}  (함께 산 사람 {w}명)")
    print(f"  엣지 {len(proj)}개")

    print("\n버려진 것: 누가 샀는지. 투영 그래프만 보면 u1, u2, u3 이 사라진다.")

    print("\n규모를 키우면 투영 엣지가 이렇게 는다")
    print(f"{'사용자':>8} {'1인당 구매':>10} {'투영 엣지(최대)':>16}")
    for n, k in ((1_000, 10), (1_000, 50), (100_000, 50), (100_000, 200)):
        print(f"{n:>8,} {k:>10} {simulate(n, k):>16,}")

    print(
        "\n1인당 200개를 산 사용자 10만 명이면 투영 엣지가 20억 개다.\n"
        "실제로는 중복이 합쳐지니 이보다 적지만, 상한이 이렇다는 게 중요하다.\n"
        "\n대안 두 가지.\n"
        "  1. 투영하지 말고 이분 그래프 그대로 2홉을 돈다. 필요할 때만 계산한다.\n"
        "  2. 투영하되 «함께 산 사람 N명 이상»으로 자른다. 대개 3명이면 충분하다.\n"
        "저는 2번을 쓰고, 자르는 값은 엣지 수가 노드 수의 20배를 넘지 않게 잡는다."
    )


if __name__ == "__main__":
    main()
