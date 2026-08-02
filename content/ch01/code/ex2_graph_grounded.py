"""
예제 2 — 같은 질문을 그래프 근거로 답하기.

    python3 ex2_graph_grounded.py

의존성 없음. 그래프 데이터베이스도, 라이브러리도 쓰지 않는다.
그래프는 제품 이름이 아니라 자료구조라는 걸 먼저 보여 주려는 것이다.
Neo4j로 옮긴 같은 질의는 11장에서 다시 만난다.
"""

from collections import defaultdict

from notes import TRIPLES, QUESTION, GROUND_TRUTH


def build_graph(triples):
    """(주어) -[술어 {속성}]-> (목적어) 를 인접 리스트로."""
    out = defaultdict(list)
    for s, p, o, props in triples:
        out[s].append((p, o, props))
    return out


def terminated_then_resigned(out, year="2024"):
    """해지 엣지 하나와, 그보다 뒤에 놓인 체결 엣지 하나를 동시에 가진 노드를 찾는다."""
    answers = []
    for node, edges in out.items():
        ends = [e for e in edges if e[0] == "해지" and e[2]["연월"].startswith(year)]
        if not ends:
            continue
        for _, ended_contract, end_props in ends:
            later = [
                e for e in edges
                if e[0] == "체결" and e[2]["연월"] > end_props["연월"]
            ]
            for _, new_contract, new_props in later:
                answers.append({
                    "고객": node,
                    "해지": (ended_contract, end_props["연월"]),
                    "재계약": (new_contract, new_props["연월"]),
                })
    return answers


def main():
    out = build_graph(TRIPLES)
    rows = terminated_then_resigned(out)

    print(f"질문: {QUESTION}\n")
    print("경로를 따라간 결과")
    for r in rows:
        print(f"  {r['고객']}")
        print(f"    해지  {r['해지'][0]}  ({r['해지'][1]})")
        print(f"    재계약 {r['재계약'][0]}  ({r['재계약'][1]})")

    found = {r["고객"] for r in rows}
    print(f"\n답: {sorted(found)}")
    print(f"정답: {sorted(GROUND_TRUTH)}")
    print(f"맞았나: {'예' if found == GROUND_TRUTH else '아니오'}")

    # 여기가 핵심이다. 답과 함께 '왜 그렇게 답했는지'가 딸려 나온다.
    print(
        "\n라온에너지가 빠진 이유: 해지 엣지는 있는데 그 뒤로 이어지는 체결 엣지가 없다.\n"
        "다올물산이 빠진 이유: 술어가 '해지'가 아니라 '해지의사'다. 철회 속성이 True다.\n"
        "이 두 문장은 짐작이 아니라 그래프를 읽은 결과다. 틀렸다면 데이터가 틀린 것이고,\n"
        "어느 엣지가 틀렸는지 손가락으로 가리킬 수 있다."
    )


if __name__ == "__main__":
    main()
