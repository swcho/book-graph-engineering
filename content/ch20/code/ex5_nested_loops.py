"""
예제 5 — 루프 안에 루프가 있으면 상한이 곱해진다.

    python3 ex5_nested_loops.py

의존성 없음.
"""

OUTER, INNER, TOOL = 5, 4, 3        # 각 층의 상한
COST_PER_CALL = 1.8                 # 원


def counts():
    """각 층이 «자기 상한»만 보면 총 호출이 몇 번이 되나."""
    return OUTER, OUTER * INNER, OUTER * INNER * TOOL


def with_global_budget(budget):
    """전역 예산이 있으면 실제로 몇 번까지 가나."""
    return int(budget / COST_PER_CALL)


def main():
    o, i, t = counts()
    print("층마다 상한을 따로 둔 경우")
    print(f"    바깥 루프  상한 {OUTER}  → 최대 {o}회")
    print(f"    안쪽 루프  상한 {INNER}  → 최대 {i}회")
    print(f"    도구 재시도 상한 {TOOL}  → 최대 {t}회")
    print(f"\n    총 모델 호출 최대 {t}회, 값 {t * COST_PER_CALL:,.0f}원")

    print("\n각 층 상한을 하나씩 올리면")
    print(f"    {'바깥':>4} {'안쪽':>4} {'도구':>4} {'총 호출':>8} {'값':>9}")
    for o2, i2, t2 in ((5, 4, 3), (6, 4, 3), (5, 5, 3), (5, 4, 4), (8, 6, 5)):
        n = o2 * i2 * t2
        print(f"    {o2:>4} {i2:>4} {t2:>4} {n:>8} {n*COST_PER_CALL:>8,.0f}원")

    print(
        "\n«8·6·5» 는 각 층에서 보면 다 합리적인 숫자다. 여덟 번, 여섯 번, 다섯 번.\n"
        f"그런데 곱하면 {8*6*5}회고 {8*6*5*COST_PER_CALL:,.0f}원이다.\n"
        "\n층마다 상한을 두는 건 필요하다. 다만 그것만으로는 부족하다.\n"
        "«전역 예산»을 하나 더 둬야 한다. 그리고 모든 층이 그걸 본다.\n"
    )

    for budget in (100, 300, 1000):
        n = with_global_budget(budget)
        print(f"    전역 예산 {budget:>5}원 → 최대 {n:>3}회 호출 "
              f"(층 상한 곱 {8*6*5}회보다 {'적다' if n < 240 else '많다'})")

    print(
        "\n전역 예산이 층 상한보다 먼저 걸리게 잡는 게 요령이다.\n"
        "그러면 층 상한은 «안전망»이 되고 전역 예산이 «실질 제어»가 된다.\n"
        "\n제가 겪은 사고가 이거였다. 층마다 상한이 다 있었는데 전역이 없었다.\n"
        "각 층 코드를 따로 리뷰하면 아무 문제가 없어 보인다. 곱하기를 아무도 안 했다."
    )


if __name__ == "__main__":
    main()
