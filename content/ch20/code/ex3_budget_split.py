"""
예제 3 — 예산을 안 나누면 뒤쪽 단계가 굶는다.

    python3 ex3_budget_split.py

의존성 없음.
"""

TOTAL = 100.0

# (단계, 최소 필요 예산, 여유가 있으면 더 쓰는 양)
STAGES = [
    ("검색",  8,  40),
    ("요약",  6,  25),
    ("초안", 14,  60),
    ("검토", 10,  20),
]


def no_split(total):
    """먼저 오는 단계가 여유분을 다 쓴다."""
    left = total
    out = []
    for name, need, greedy in STAGES:
        want = need + greedy
        got = min(want, left)
        left -= got
        out.append((name, got, got >= need))
    return out


def even_split(total):
    share = total / len(STAGES)
    return [(n, share, share >= need) for n, need, _ in STAGES]


def reserve_first(total):
    """최소 필요분을 먼저 떼어 두고 나머지를 앞에서부터 쓴다."""
    reserved = sum(need for _, need, _ in STAGES)
    spare = total - reserved
    out = []
    for name, need, greedy in STAGES:
        extra = min(greedy, spare)
        spare -= extra
        out.append((name, need + extra, True))
    return out


def show(title, rows):
    print(f"\n{title}")
    print(f"    {'단계':<6} {'배정':>7} {'충분한가'}")
    starved = 0
    for name, got, ok in rows:
        starved += 0 if ok else 1
        print(f"    {name:<6} {got:>7.1f} {'예' if ok else '아니오 ←'}")
    if starved:
        print(f"    → {starved}개 단계가 최소 예산도 못 받았다")


def main():
    print(f"전체 예산 {TOTAL:.0f}. 단계별 최소 필요분 합계 "
          f"{sum(n for _, n, _ in STAGES)}.")

    show("나누지 않음 — 먼저 오는 쪽이 다 쓴다", no_split(TOTAL))
    show("균등 분배", even_split(TOTAL))
    show("최소분 먼저 떼어 두기", reserve_first(TOTAL))

    print(
        "\n«나누지 않음»에서 검토 단계가 0을 받는다.\n"
        "검색과 초안이 여유분을 다 써 버렸기 때문이다.\n"
        "\n그런데 검토는 «품질을 지키는» 단계다. 그게 굶으면 나쁜 결과가 그대로 나간다.\n"
        "제일 중요한 단계가 제일 마지막에 있어서 제일 먼저 굶는 구조다.\n"
        "\n«균등 분배»는 안전한데 낭비가 있다. 요약은 6이면 되는데 25를 받는다.\n"
        "\n«최소분 먼저»가 대개 답이다. 먼저 최소를 보장하고 남는 걸 앞에서부터 쓴다.\n"
        "다만 «최소가 얼마인지»를 알아야 한다. 그건 실측해야 하고,\n"
        "실측하려면 단계별 토큰을 따로 세고 있어야 한다.\n"
        "그 계측을 안 해 두면 이 전략을 못 쓴다."
    )


if __name__ == "__main__":
    main()
