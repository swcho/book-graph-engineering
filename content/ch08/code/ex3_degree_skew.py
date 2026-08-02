"""
예제 3 — 왜 어떤 그래프는 100만에서 멀쩡하고 어떤 건 10만에서 죽나.

    python3 ex3_degree_skew.py

의존성 없음.
"""

from collections import defaultdict

from graphgen import make


def degrees(edges):
    d = defaultdict(int)
    for a, b in edges:
        d[a] += 1; d[b] += 1
    return d


def two_hop_cost(edges):
    """2홉 탐색이 훑는 엣지 수의 합. 차수의 제곱합에 비례한다."""
    d = degrees(edges)
    return sum(v * v for v in d.values())


def main():
    print(f"{'그래프':<16} {'노드':>8} {'엣지':>10} {'평균차수':>9} "
          f"{'최대차수':>9} {'2홉 비용':>14}")
    print("-" * 72)
    for label, skew, n in (("고른 분포", False, 50_000), ("쏠린 분포", True, 50_000)):
        e = make(n=n, avg_deg=12, skew=skew)
        d = degrees(e)
        vals = sorted(d.values(), reverse=True)
        print(f"{label:<16} {n:>8,} {len(e):>10,} "
              f"{sum(vals)/len(vals):>9.1f} {vals[0]:>9,} {two_hop_cost(e):>14,}")

    print(
        "\n평균 차수는 거의 같은데 2홉 비용이 자릿수로 다르다.\n"
        "차수의 «제곱합»이 비용을 정하기 때문이다. 평균은 이 값을 못 잡아낸다.\n"
        "\n쏠린 그래프에서 상위 노드를 지나가는 질의 하나가 전체를 세운다.\n"
        "이런 노드를 슈퍼 노드(super node)라고 부른다.\n"
        "\n대처법 세 가지.\n"
        "  1. 슈퍼 노드를 질의에서 피한다 («기타», «미분류» 같은 것은 대개 지워도 된다)\n"
        "  2. 차수 상한을 두고 넘으면 쪼갠다 (샤딩된 이웃 목록)\n"
        "  3. 2홉 결과를 미리 계산해 둔다 (대신 갱신 비용을 낸다)\n"
        "저는 1번을 먼저 봅니다. 슈퍼 노드의 절반은 모델링 실수라서요."
    )


if __name__ == "__main__":
    main()
