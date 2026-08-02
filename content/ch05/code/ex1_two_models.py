"""
예제 1 — 같은 사실을 두 모델로 적으면 무엇이 달라지나.

    python3 ex1_two_models.py

의존성 없음.
"""

from model import LPG_EDGES, LPG_NODES, RDF_TRIPLES


def main():
    print("=== 프로퍼티 그래프 ===")
    for nid, n in LPG_NODES.items():
        print(f"  ({nid}:{':'.join(n['labels'])} {n['props']})")
    for e in LPG_EDGES:
        print(f"  ({e['from']})-[:{e['type']} {e['props']}]->({e['to']})")
    print(f"\n  노드 {len(LPG_NODES)}개, 엣지 {len(LPG_EDGES)}개")

    print("\n=== RDF (엣지 속성은 아직 뺐다) ===")
    for t in RDF_TRIPLES:
        print("  ", " ".join(t))
    print(f"\n  트리플 {len(RDF_TRIPLES)}개")

    print(
        "\n같은 사실인데 «단위»가 다르다.\n"
        "LPG 는 속성을 주머니에 담아 노드 하나로 세고, RDF 는 속성마다 한 줄이다.\n"
        "\n어느 쪽이 나은가. 세는 단위가 다를 뿐이지만, 실무에서는 차이가 난다.\n"
        "  - 새 속성을 추가할 때: RDF 는 줄 하나 추가. LPG 도 키 하나 추가. 둘 다 쉽다.\n"
        "  - 속성 하나에 출처를 달 때: RDF 는 그 트리플을 가리키면 된다.\n"
        "    LPG 는 속성이 주머니 안에 있어서 가리킬 손잡이가 없다. 이게 진짜 차이다."
    )


if __name__ == "__main__":
    main()
