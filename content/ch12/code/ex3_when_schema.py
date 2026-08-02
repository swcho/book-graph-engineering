"""
예제 3 — 스키마를 언제 못 박을 것인가. 엔진에 따라 선택지가 다르다.

    pip install kuzu "rdflib>=7,<8" pyshacl
    python3 ex3_when_schema.py

확인 시점 Kuzu 0.11.3, rdflib 7.5.0.
같은 «잘못된 데이터»를 세 가지 방식에 넣어 보고, 언제 걸리는지 본다.
"""

import shutil
import tempfile

import kuzu
from pyshacl import validate
from rdflib import Graph

BAD_ROWS = [
    ("등급이 규칙 밖", "가온테크", "Z"),
    ("이름이 비었다", "", "A"),
]

SHAPES = """
@prefix sh:  <http://www.w3.org/ns/shacl#> .
@prefix ex:  <http://example.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:CompanyShape a sh:NodeShape ;
    sh:targetClass ex:Company ;
    sh:property [ sh:path ex:name ; sh:minCount 1 ; sh:minLength 1 ;
                  sh:datatype xsd:string ] ;
    sh:property [ sh:path ex:grade ; sh:in ("A" "B" "C") ] .
"""

DATA_TTL = """
@prefix ex: <http://example.org/> .
ex:Gaon a ex:Company ; ex:name "가온테크" ; ex:grade "Z" .
ex:Naru a ex:Company ; ex:name ""        ; ex:grade "A" .
ex:Daol a ex:Company ; ex:name "다올물산" ; ex:grade "B" .
"""


def try_kuzu_typed():
    """적재 시점에 막는다 — 스키마가 강제되는 엔진."""
    tmp = tempfile.mkdtemp()
    out = []
    try:
        conn = kuzu.Connection(kuzu.Database(f"{tmp}/db"))
        conn.execute("CREATE NODE TABLE Company(name STRING, grade STRING, "
                     "PRIMARY KEY(name))")
        for label, name, grade in BAD_ROWS:
            try:
                conn.execute(f"CREATE (:Company {{name:'{name}', grade:'{grade}'}})")
                out.append((label, "통과 (막지 못함)"))
            except Exception as e:
                out.append((label, f"거부 — {str(e).splitlines()[0][:40]}"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def try_shacl():
    """적재는 되고, 검증 단계에서 보고서로 잡는다."""
    data = Graph().parse(data=DATA_TTL, format="turtle")
    shapes = Graph().parse(data=SHAPES, format="turtle")
    ok, _, text = validate(data, shacl_graph=shapes, inference="none")
    violations = text.count("Constraint Violation")
    return ok, violations, text


def main():
    print("=== 방식 1: 스키마 강제 (적재 시점에 막는다) ===")
    for label, result in try_kuzu_typed():
        print(f"  {label:<16} {result}")
    print("  → 타입은 막지만 «값의 범위»(등급이 A/B/C 중 하나)는 못 막는다.")
    print("    이 엔진에는 CHECK 제약이 없다. 엔진마다 다르다.")

    print("\n=== 방식 2: SHACL 검증 (적재는 되고, 나중에 보고서) ===")
    ok, n, text = try_shacl()
    print(f"  통과 여부: {ok},  위반 {n}건")
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(("Constraint Violation", "Focus Node", "Value Node",
                            "Message")):
            print(f"    {line[:88]}")

    print(
        "\n=== 방식 3: 스키마 없음 ===\n"
        "  아무것도 안 걸린다. 6개월 뒤에 발견한다.\n"
        "\n세 방식의 진짜 차이는 «언제 아느냐»다.\n"
        "  적재 시점  — 즉시. 대신 적재가 실패하니 파이프라인이 멈춘다.\n"
        "  검증 시점  — 배치가 돌 때. 데이터는 들어가 있고 보고서로 안다.\n"
        "  없음       — 사용자가 알려 준다.\n"
        "\n제 기준: 되돌릴 수 없는 것은 적재 시점에, 나머지는 검증 시점에.\n"
        "적재를 너무 엄격하게 잡으면 데이터가 아예 안 들어와서 그것대로 문제가 된다."
    )


if __name__ == "__main__":
    main()
