"""
예제 2 — 엣지 방향을 어느 쪽으로 잡을 것인가.

    python3 ex2_direction.py

의존성 없음.
"""

from collections import defaultdict

# 같은 조직도를 두 방향으로 저장한다.
MANAGES = [("김부장", "박대리"), ("김부장", "이주임"), ("최이사", "김부장")]
REPORTS_TO = [(b, a) for a, b in MANAGES]


def out_index(edges):
    idx = defaultdict(list)
    for a, b in edges:
        idx[a].append(b)
    return idx


def ask_boss(name, edges, label):
    """«이 사람의 상사는?» 나가는 엣지로 답할 수 있으면 1번, 아니면 전체 훑기."""
    idx = out_index(edges)
    if label == "REPORTS_TO":
        return idx.get(name, []), 1
    scanned = 0
    found = []
    for a, b in edges:
        scanned += 1
        if b == name:
            found.append(a)
    return found, scanned


def ask_reports(name, edges, label):
    """«이 사람의 부하는?»"""
    idx = out_index(edges)
    if label == "MANAGES":
        return idx.get(name, []), 1
    scanned = 0
    found = []
    for a, b in edges:
        scanned += 1
        if b == name:
            found.append(a)
    return found, scanned


def main():
    for label, edges in (("MANAGES", MANAGES), ("REPORTS_TO", REPORTS_TO)):
        boss, s1 = ask_boss("박대리", edges, label)
        subs, s2 = ask_reports("김부장", edges, label)
        print(f"[{label}]")
        print(f"  박대리의 상사 → {boss}  (조회 비용 {s1})")
        print(f"  김부장의 부하 → {subs}  (조회 비용 {s2})")

    print(
        "\n같은 사실인데 «자주 묻는 쪽»을 나가는 방향으로 두면 비용이 다르다.\n"
        "엔진이 역방향 색인을 자동으로 만들어 주면 이 차이가 사라진다.\n"
        "Neo4j 는 양방향 탐색이 대칭이지만, 모든 엔진이 그런 건 아니다.\n"
        "\n방향을 정하는 기준 두 가지.\n"
        "  1. 자주 묻는 질문을 «나가는» 방향으로.\n"
        "  2. 카디널리티가 «1 쪽»에서 «N 쪽»으로. (부하는 여럿, 상사는 하나)\n"
        "둘이 충돌하면 1번을 따른다. 성능은 질의가 정한다."
    )


if __name__ == "__main__":
    main()
