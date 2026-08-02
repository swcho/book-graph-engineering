"""
예제 5 — 다중 엣지와 자기 루프. 세는 방식이 흔들리는 자리.

    python3 ex5_multigraph.py

의존성 없음.
"""

from collections import Counter, defaultdict

# 같은 두 회사 사이에 계약이 세 번, 그리고 자회사가 자기 자신에게 대여한 건 하나.
EDGES = [
    ("가온테크", "나루소프트", "C-2023-011"),
    ("가온테크", "나루소프트", "C-2024-088"),
    ("가온테크", "나루소프트", "C-2025-118"),
    ("가온테크", "다올물산", "C-2025-200"),
    ("라온에너지", "라온에너지", "C-2025-301"),   # 자기 루프
]


def degree_simple(edges):
    """단순 그래프로 보면: 같은 쌍은 하나로 센다."""
    pairs = {(min(a, b), max(a, b)) for a, b, _ in edges if a != b}
    deg = Counter()
    for a, b in pairs:
        deg[a] += 1
        deg[b] += 1
    return deg


def degree_multi(edges):
    """다중 그래프로 보면: 엣지마다 센다. 자기 루프는 2로 센다(관례)."""
    deg = Counter()
    for a, b, _ in edges:
        if a == b:
            deg[a] += 2
        else:
            deg[a] += 1
            deg[b] += 1
    return deg


def main():
    print("엣지 목록")
    for e in EDGES:
        print("  ", e)

    ds, dm = degree_simple(EDGES), degree_multi(EDGES)
    print(f"\n{'노드':<12} {'단순 그래프 차수':>16} {'다중 그래프 차수':>16}")
    for n in sorted(set(ds) | set(dm)):
        print(f"{n:<12} {ds.get(n,0):>16} {dm.get(n,0):>16}")

    print(
        "\n가온테크의 차수가 2 냐 4 냐. 둘 다 맞다. 무엇을 세는지가 다를 뿐이다.\n"
        "  거래처 수를 알고 싶으면 단순 그래프.\n"
        "  거래 건수를 알고 싶으면 다중 그래프.\n"
        "\n사고는 이 둘을 섞을 때 난다. 중심성을 다중 그래프로 계산해 놓고\n"
        "«거래처가 많은 회사»라고 보고하면 틀린다. 계약을 여러 번 한 회사가 1등이 된다.\n"
        "\n자기 루프도 함정이다. 알고리즘마다 1로 세기도 하고 2로 세기도 한다.\n"
        "라이브러리를 바꾸면 숫자가 조용히 달라진다. 미리 걸러 두는 편이 낫다."
    )


if __name__ == "__main__":
    main()
