"""
예제 2 — 「지운다」는 한 가지가 아니다. 네 수준을 비교한다.

    python3 ex2_delete_levels.py

의존성 없음. 각 수준이 무엇을 만족하고 무엇을 깨는지 표로 놓는다.
"""

LEVELS = [
    ("1. 숨기기(soft delete)",  "deleted=true 플래그"),
    ("2. 식별자 끊기",          "이름·연락처를 지우고 대체 키만 남긴다"),
    ("3. 가명화",              "식별자를 되돌릴 수 있는 토큰으로"),
    ("4. 완전 삭제",            "노드·엣지·본문·백업까지"),
]

# 각 수준이 만족하는가
CRITERIA = {
    "화면에서 안 보인다":       [True,  True,  True,  True],
    "이름으로 못 찾는다":       [False, True,  True,  True],
    "다른 데이터와 못 잇는다":   [False, False, False, True],
    "집계·통계가 유지된다":     [True,  True,  True,  False],
    "감사 이력이 유지된다":     [True,  True,  True,  False],
    "남의 이력이 안 깨진다":    [True,  True,  True,  False],
    "되돌릴 수 있다":          [True,  False, True,  False],
    "백업까지 지워진다":        [False, False, False, True],
}


def main():
    print("「지운다」의 네 수준.\n")
    for name, what in LEVELS:
        print(f"  {name:<24}{what}")

    print(f"\n{'기준':<24}" + "".join(f"{i + 1:>8}" for i in range(4)))
    print("-" * 58)
    for crit, vals in CRITERIA.items():
        print(f"{crit:<24}" + "".join(f"{'○' if v else '✗':>8}" for v in vals))

    scores = [sum(1 for vals in CRITERIA.values() if vals[i])
              for i in range(4)]
    print(f"\n{'만족한 기준 수':<24}" + "".join(f"{s:>8}" for s in scores))

    print(
        "\n어느 수준도 «전부»를 만족하지 않는다. 그게 이 표의 요점이다.\n"
        "\n4번(완전 삭제)이 제일 강해 보이는데 만족한 기준이 4개로 제일 적다.\n"
        "지우면 집계가 깨지고, 감사 이력이 사라지고, 남의 이력도 같이 깨진다.\n"
        "\n제일 많이 만족하는 건 3번(가명화)으로 6개다. 그런데 이것도 «다른 데이터와\n"
        "못 잇는다»와 «백업까지 지워진다»를 못 한다. 완벽한 칸이 없다.\n"
        "\n실무에서 제일 많이 쓰이는 건 2번(식별자 끊기)이다.\n"
        "  「김도현」을 「p-8f3a」로 바꾼다. 사람은 못 알아보는데 구조는 남는다.\n"
        "  「결제팀에 3명이 있었다」는 유지되고 「그중 하나가 김도현」은 사라진다.\n"
        "\n그런데 2번에는 함정이 있다. «다른 데이터와 못 잇는다» 칸이 ✗ 다.\n"
        "이름을 지워도 「2026년 3월 12일 14시 3분에 마포에서 결제」 같은 조합이\n"
        "남아 있으면 그것으로 사람을 특정할 수 있다. 재식별(re-identification)이다.\n"
        "\n그래서 이름만 지우는 것으로는 부족하다.\n"
        "  «몇 개를 조합하면 한 사람으로 좁혀지나»를 세야 한다.\n"
        "  이 값이 작으면 이름을 지워도 지워진 게 아니다.\n"
        "\n실무에서 저는 이렇게 나눈다.\n"
        "  기본은 2번. 식별자를 끊고 구조는 남긴다\n"
        "  법적 요구가 명시적이면 4번. 다만 «무엇이 깨지는지» 먼저 목록으로 만든다\n"
        "  실수 대비가 필요하면 3번. 되돌릴 수 있게 토큰을 따로 보관한다\n"
        "\n1번은 «지운 것»이 아니다. 그런데 많은 시스템이 1번만 하고 지웠다고 한다."
    )


if __name__ == "__main__":
    main()
