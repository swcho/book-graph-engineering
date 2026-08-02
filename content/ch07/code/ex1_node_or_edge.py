"""
예제 1 — 관계를 엣지로 둘까, 노드로 승격할까. 두 모델로 만들어 비교한다.

    python3 ex1_node_or_edge.py

의존성 없음.
"""

from collections import defaultdict

# --- 모델 A: 관계를 엣지로 ---
EDGE_MODEL = [
    ("가온테크", "SIGNED", "C-2025-118", {"at": "2025-06-02", "by": "김하늘"}),
    ("가온테크", "SIGNED", "C-2024-002", {"at": "2024-01-15", "by": "박서준"}),
    ("나루소프트", "SIGNED", "C-2025-004", {"at": "2025-01-20", "by": "김하늘"}),
]

# --- 모델 B: 관계를 노드로 승격 ---
NODE_MODEL_NODES = {
    "s1": {"label": "체결", "at": "2025-06-02"},
    "s2": {"label": "체결", "at": "2024-01-15"},
    "s3": {"label": "체결", "at": "2025-01-20"},
}
NODE_MODEL_EDGES = [
    ("가온테크", "HAS", "s1"), ("s1", "OF", "C-2025-118"), ("s1", "BY", "김하늘"),
    ("가온테크", "HAS", "s2"), ("s2", "OF", "C-2024-002"), ("s2", "BY", "박서준"),
    ("나루소프트", "HAS", "s3"), ("s3", "OF", "C-2025-004"), ("s3", "BY", "김하늘"),
]


def q_edge_model(who):
    """«김하늘이 담당한 체결 건» — 엣지 모델에서는 모든 엣지를 훑어야 한다."""
    scanned = 0
    out = []
    for s, t, o, props in EDGE_MODEL:
        scanned += 1
        if props.get("by") == who:
            out.append((s, o, props["at"]))
    return out, scanned


def q_node_model(who):
    """노드 모델에서는 김하늘에게 들어오는 BY 엣지만 보면 된다."""
    incoming = defaultdict(list)
    for s, t, o in NODE_MODEL_EDGES:
        incoming[o].append((s, t))
    scanned = 0
    out = []
    for s, t in incoming[who]:
        scanned += 1
        if t != "BY":
            continue
        company = next(a for a, tt, b in NODE_MODEL_EDGES if b == s and tt == "HAS")
        contract = next(b for a, tt, b in NODE_MODEL_EDGES if a == s and tt == "OF")
        out.append((company, contract, NODE_MODEL_NODES[s]["at"]))
    return out, scanned


def main():
    print("질문: 김하늘이 담당한 체결 건은?\n")
    a, sa = q_edge_model("김하늘")
    b, sb = q_node_model("김하늘")
    print(f"모델 A (엣지)  결과 {len(a)}건, 훑은 엣지 {sa}개")
    for r in a:
        print("   ", r)
    print(f"\n모델 B (노드 승격) 결과 {len(b)}건, 훑은 엣지 {sb}개")
    for r in b:
        print("   ", r)

    print(
        "\n엣지 3개짜리라 차이가 안 느껴진다. 엣지가 100만 개면 다르다.\n"
        "«by» 는 엣지 속성이라 색인을 걸 수 없는 엔진이 많다. 그러면 전체를 훑는다.\n"
        "노드로 승격하면 «김하늘» 노드에서 들어오는 엣지만 따라가면 된다.\n"
        "\n승격의 신호는 하나다. «그 속성으로 검색하기 시작했는가.»\n"
        "속성은 «읽는» 것이고 노드는 «찾는» 것이다. 찾기 시작하면 승격할 때다."
    )


if __name__ == "__main__":
    main()
