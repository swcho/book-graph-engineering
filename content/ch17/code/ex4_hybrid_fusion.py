"""
예제 4 — 라우팅 대신 «둘 다 돌리고 합치기». 언제 이게 나은가.

    python3 ex4_hybrid_fusion.py

의존성 없음. 순위 융합(reciprocal rank fusion)을 20줄로 구현한다.
"""

from collections import defaultdict

# 같은 질문에 두 엔진이 낸 결과 (순위 순)
VECTOR_RANK = ["d11", "d01", "d09", "d05", "d02"]
GRAPH_RANK = ["d12", "d02", "d06", "d09", "d03"]

GOLD = {"d01", "d02", "d06", "d09"}    # 사람이 확인한 정답 문서
K = 60                                  # RRF 상수. 60이 관례다.


def rrf(*rankings, k=K):
    score = defaultdict(float)
    for r in rankings:
        for pos, item in enumerate(r, 1):
            score[item] += 1 / (k + pos)
    return sorted(score, key=lambda x: -score[x])


def prec_at(ranked, n):
    top = ranked[:n]
    return len(set(top) & GOLD) / n


def main():
    fused = rrf(VECTOR_RANK, GRAPH_RANK)
    print(f"{'':<12} {'순위'}")
    print(f"{'벡터':<12} {VECTOR_RANK}")
    print(f"{'그래프':<12} {GRAPH_RANK}")
    print(f"{'융합':<12} {fused}")

    print(f"\n{'방식':<12} {'P@1':>6} {'P@2':>6} {'P@3':>6} {'P@4':>6}")
    print("-" * 42)
    for name, r in (("벡터", VECTOR_RANK), ("그래프", GRAPH_RANK), ("융합", fused)):
        print(f"{name:<12}" + "".join(f"{prec_at(r, n):>6.2f}" for n in (1, 2, 3, 4)))

    print(
        "\n두 엔진 모두 1위가 오답인데, 융합하면 1위가 정답이 된다.\n"
        "각자 «두 번째로 확신하는 것»이 겹쳤기 때문이다.\n"
        "\n다만 융합이 항상 이기지는 않는다. 한쪽만 아는 정답은 순위가 내려간다.\n"
        "융합은 «둘 다 상위에 올린 것»을 밀어 올리는 방식이라 그렇다.\n"
        "\n그럼 언제 융합을 쓰나. 제 기준은 둘이다.\n"
        "  1. 라우터의 정확도가 낮을 때 — 잘못 보내는 것보다 둘 다 돌리는 게 낫다\n"
        "  2. 질문이 여러 유형에 걸칠 때 — «김하늘 담당 장애의 원인과 그 문서» 같은\n"
        "\n대가는 값이다. 매번 두 번 검색한다. 그리고 지연도 는다.\n"
        "\n제가 실제로 쓰는 구조는 이렇다.\n"
        "  라우터가 확신하면(임계 위) 한쪽만, 애매하면 둘 다.\n"
        "  이러면 애매한 20% 만 두 배 비용을 낸다."
    )


if __name__ == "__main__":
    main()
