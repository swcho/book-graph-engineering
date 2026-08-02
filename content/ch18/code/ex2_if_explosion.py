"""
예제 2 — 조건 분기를 if 문으로 버티면 어디서 무너지나.

    python3 ex2_if_explosion.py

의존성 없음.
"""

from itertools import product

CONDITIONS = ["검색 결과 있음", "요약 길이 초과", "검토 통과",
              "사람 승인 필요", "재시도 남음"]


def paths(n):
    return 2 ** n


def readable_lines(n):
    """중첩 if 로 쓰면 대략 이 정도 줄이 된다 (경로마다 처리 두 줄)."""
    return paths(n) * 2 + n * 2


def graph_edges(n):
    """상태 그래프로 그리면 조건마다 «갈림길 노드 하나 + 나가는 엣지 둘»."""
    return n * 2


def main():
    print(f"{'조건 수':>7} {'경우의 수':>10} {'if 코드 줄':>12} "
          f"{'그래프 엣지':>12} {'사람이 다 볼 수 있나'}")
    print("-" * 62)
    for n in range(1, 9):
        p, l, e = paths(n), readable_lines(n), graph_edges(n)
        ok = "예" if p <= 8 else ("힘들다" if p <= 32 else "불가능")
        print(f"{n:>7} {p:>10,} {l:>12,} {e:>12} {ok:>18}")

    print("\n조건 5개일 때 실제 경우의 수를 세어 보면")
    n = 5
    for i, combo in enumerate(product([0, 1], repeat=n)):
        if i >= 4:
            print(f"    ... 나머지 {2**n - 4}가지")
            break
        desc = ", ".join(c for c, v in zip(CONDITIONS, combo) if v) or "(전부 아니오)"
        print(f"    {i+1:>2}. {desc}")

    print(
        "\n«경우의 수»와 «엣지 수»가 다른 속도로 는다.\n"
        "  경우의 수 — 조건마다 두 배 (지수)\n"
        "  엣지 수   — 조건마다 둘 (선형)\n"
        "\nif 문은 경우의 수를 «코드로 펼친다». 그래서 지수로 는다.\n"
        "상태 그래프는 갈림길을 «선언»한다. 조합은 실행 시점에 만들어진다.\n"
        "\n실무에서 무너지는 지점이 대개 조건 5개다.\n"
        "32가지 경우 중 몇 가지는 테스트를 안 해 보게 되고,\n"
        "안 해 본 경우가 운영에서 나온다.\n"
        "\n그런데 이게 «if 를 쓰지 마라»는 뜻은 아니다.\n"
        "조건 두세 개면 if 가 훨씬 읽기 쉽다. 그래프는 개념이 늘어나니까."
    )


if __name__ == "__main__":
    main()
