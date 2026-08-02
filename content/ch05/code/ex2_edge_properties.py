"""
예제 2 — 엣지에 속성을 달아야 할 때. RDF 가 불편해지는 지점.

    python3 ex2_edge_properties.py

의존성 없음.
"""

from model import LPG_EDGES, RDF_NAMED_GRAPH, RDF_REIFIED, RDF_STAR


def main():
    e = LPG_EDGES[0]
    print("프로퍼티 그래프 — 엣지에 그냥 붙인다 (1줄)")
    print(f"  (가온테크)-[:{e['type']} {e['props']}]->(계약)")

    print(f"\nRDF 방법 (1) 구체화 — 관계를 노드로 승격 ({len(RDF_REIFIED)}줄)")
    for t in RDF_REIFIED:
        print("  ", " ".join(t))
    print("  → 원래 있던 ex:signed 엣지가 사라진다. 기존 질의가 전부 깨진다.")

    print(f"\nRDF 방법 (2) RDF-star — 트리플을 주어로 ({len(RDF_STAR)}줄)")
    for line in RDF_STAR:
        print("  ", line)
    print("  → 원래 엣지가 남아 있다. 기존 질의가 안 깨진다. 대신 아직 후보 권고안이다.")

    print(f"\nRDF 방법 (3) 이름 붙인 그래프 ({len(RDF_NAMED_GRAPH)}줄)")
    for line in RDF_NAMED_GRAPH:
        print("  ", line)
    print("  → 트리플 묶음 단위라, 엣지 하나만 가리키려면 묶음도 하나짜리로 만들어야 한다.")

    print(
        "\n정리하면 이렇다.\n"
        "  엣지 속성이 «드물게» 필요하면 RDF 로 충분하다. 세 방법 중 하나를 고르면 된다.\n"
        "  엣지 속성이 «기본»이면 LPG 가 편하다. 관계마다 시각·출처·신뢰도를 다는 경우다.\n"
        "\n제 기준: 관계의 30% 이상에 속성이 붙으면 LPG. 그 밑이면 RDF."
    )


if __name__ == "__main__":
    main()
