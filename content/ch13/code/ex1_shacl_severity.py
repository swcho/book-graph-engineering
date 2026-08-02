"""
예제 1 — SHACL 검증과 심각도 세 단계.

    pip install pyshacl "rdflib>=7,<8"
    python3 ex1_shacl_severity.py

확인 시점 pyshacl / rdflib 7.5.0.
"""

from collections import Counter

from pyshacl import validate
from rdflib import Graph, Namespace, URIRef

SH = Namespace("http://www.w3.org/ns/shacl#")
LEVEL = {"Violation": "차단", "Warning": "경고", "Info": "기록"}


def main():
    data = Graph().parse("data.ttl", format="turtle")
    shapes = Graph().parse("shapes.ttl", format="turtle")
    ok, report, _ = validate(data, shacl_graph=shapes, inference="none",
                             advanced=True)

    rows = []
    for r in report.subjects(URIRef(str(SH) + "resultSeverity"), None):
        sev = str(report.value(r, SH.resultSeverity)).rsplit("#", 1)[-1]
        node = str(report.value(r, SH.focusNode)).rsplit("/", 1)[-1]
        msg = str(report.value(r, SH.resultMessage) or "")
        rows.append((LEVEL.get(sev, sev), node, msg))

    order = {"차단": 0, "경고": 1, "기록": 2}
    rows.sort(key=lambda x: (order.get(x[0], 9), x[1]))

    print(f"전체 통과 여부: {ok}\n")
    print(f"{'심각도':<6} {'노드':<8} 내용")
    print("-" * 62)
    for sev, node, msg in rows:
        print(f"{sev:<6} {node:<8} {msg}")

    cnt = Counter(r[0] for r in rows)
    print(f"\n차단 {cnt['차단']}건 · 경고 {cnt['경고']}건 · 기록 {cnt['기록']}건")

    print(
        "\n«전체 통과 여부»가 False 인 게 함정이다.\n"
        "기록 등급 하나만 걸려도 False 가 나온다. 그래서 이 값만 보고\n"
        "적재를 막으면 «표시 이름이 없다» 때문에 파이프라인이 선다.\n"
        "\n실무에서는 심각도별로 나눠서 처리한다.\n"
        "  차단 → 적재 거부. 사람이 원천을 고쳐야 한다.\n"
        "  경고 → 적재는 하고 대시보드에 올린다. 질의가 틀릴 수 있으니까.\n"
        "  기록 → 주간 보고서에 숫자만. 추세가 나빠지면 그때 본다.\n"
        "\nSHACL 이 sh:severity 를 표준으로 제공하는 이유가 이거다."
    )


if __name__ == "__main__":
    main()
