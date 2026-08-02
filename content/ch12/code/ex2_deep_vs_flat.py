"""
예제 2 — 깊은 분류와 얕은 분류. 질의문 길이와 유지 비용을 재 본다.

    pip install kuzu
    python3 ex2_deep_vs_flat.py

확인 시점 Kuzu 0.11.3.
"""

import shutil
import tempfile

import kuzu

# --- A안: 깊은 분류 (전문가 방식) ---
DEEP_SCHEMA = [
    "CREATE NODE TABLE Bolt(id STRING, name STRING, PRIMARY KEY(id))",
    "CREATE NODE TABLE Nut(id STRING, name STRING, PRIMARY KEY(id))",
    "CREATE NODE TABLE Resistor(id STRING, name STRING, PRIMARY KEY(id))",
    "CREATE NODE TABLE Capacitor(id STRING, name STRING, PRIMARY KEY(id))",
    "CREATE NODE TABLE Product(id STRING, PRIMARY KEY(id))",
    "CREATE REL TABLE UsesBolt(FROM Product TO Bolt)",
    "CREATE REL TABLE UsesNut(FROM Product TO Nut)",
    "CREATE REL TABLE UsesResistor(FROM Product TO Resistor)",
    "CREATE REL TABLE UsesCapacitor(FROM Product TO Capacitor)",
]
DEEP_DATA = [
    "CREATE (:Bolt {id:'B1', name:'M6 볼트'})",
    "CREATE (:Nut {id:'N1', name:'M6 너트'})",
    "CREATE (:Resistor {id:'R1', name:'10k 저항'})",
    "CREATE (:Capacitor {id:'C1', name:'100uF 커패시터'})",
    "CREATE (:Product {id:'P1'})", "CREATE (:Product {id:'P2'})",
    "MATCH (p:Product{id:'P1'}),(x:Bolt{id:'B1'}) CREATE (p)-[:UsesBolt]->(x)",
    "MATCH (p:Product{id:'P1'}),(x:Resistor{id:'R1'}) CREATE (p)-[:UsesResistor]->(x)",
    "MATCH (p:Product{id:'P2'}),(x:Nut{id:'N1'}) CREATE (p)-[:UsesNut]->(x)",
    "MATCH (p:Product{id:'P2'}),(x:Capacitor{id:'C1'}) CREATE (p)-[:UsesCapacitor]->(x)",
]
# «제품 P1 이 쓰는 부품 전부» — 종류마다 한 줄씩 써야 한다
DEEP_QUERY = """
MATCH (p:Product {id:'P1'})-[:UsesBolt]->(x:Bolt)      RETURN x.name AS 부품
UNION
MATCH (p:Product {id:'P1'})-[:UsesNut]->(x:Nut)        RETURN x.name AS 부품
UNION
MATCH (p:Product {id:'P1'})-[:UsesResistor]->(x:Resistor) RETURN x.name AS 부품
UNION
MATCH (p:Product {id:'P1'})-[:UsesCapacitor]->(x:Capacitor) RETURN x.name AS 부품
"""

# --- B안: 얕은 분류 (질의에서 뽑은 방식) ---
FLAT_SCHEMA = [
    "CREATE NODE TABLE Part(id STRING, name STRING, category STRING, PRIMARY KEY(id))",
    "CREATE NODE TABLE Product(id STRING, PRIMARY KEY(id))",
    "CREATE REL TABLE Uses(FROM Product TO Part)",
]
FLAT_DATA = [
    "CREATE (:Part {id:'B1', name:'M6 볼트', category:'체결'})",
    "CREATE (:Part {id:'N1', name:'M6 너트', category:'체결'})",
    "CREATE (:Part {id:'R1', name:'10k 저항', category:'전자'})",
    "CREATE (:Part {id:'C1', name:'100uF 커패시터', category:'전자'})",
    "CREATE (:Product {id:'P1'})", "CREATE (:Product {id:'P2'})",
    "MATCH (p:Product{id:'P1'}),(x:Part{id:'B1'}) CREATE (p)-[:Uses]->(x)",
    "MATCH (p:Product{id:'P1'}),(x:Part{id:'R1'}) CREATE (p)-[:Uses]->(x)",
    "MATCH (p:Product{id:'P2'}),(x:Part{id:'N1'}) CREATE (p)-[:Uses]->(x)",
    "MATCH (p:Product{id:'P2'}),(x:Part{id:'C1'}) CREATE (p)-[:Uses]->(x)",
]
FLAT_QUERY = "MATCH (p:Product {id:'P1'})-[:Uses]->(x:Part) RETURN x.name AS 부품"


def run(schema, data, query):
    tmp = tempfile.mkdtemp()
    try:
        conn = kuzu.Connection(kuzu.Database(f"{tmp}/db"))
        for s in schema + data:
            conn.execute(s)
        r = conn.execute(query)
        out = []
        while r.has_next():
            out.append(r.get_next()[0])
        return sorted(out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    deep = run(DEEP_SCHEMA, DEEP_DATA, DEEP_QUERY)
    flat = run(FLAT_SCHEMA, FLAT_DATA, FLAT_QUERY)

    print("질문: 제품 P1 이 쓰는 부품 전부\n")
    print(f"  A안 (깊은 분류) {deep}")
    print(f"  B안 (얕은 분류) {flat}")
    print(f"  같은가: {'예' if deep == flat else '아니오'}\n")

    print(f"{'항목':<24} {'A안 (깊게)':>12} {'B안 (얕게)':>12}")
    print("-" * 52)
    rows = [
        ("노드 테이블 수", 5, 2),
        ("관계 테이블 수", 4, 1),
        ("질의문 줄 수", DEEP_QUERY.strip().count("\n") + 1,
                        FLAT_QUERY.strip().count("\n") + 1),
        ("부품 종류 추가 시 고칠 곳", 3, 0),
    ]
    for label, a, b in rows:
        print(f"{label:<24} {a:>12} {b:>12}")

    print(
        "\n마지막 줄이 핵심이다.\n"
        "A안에서 «와셔»를 추가하려면 노드 테이블 하나, 관계 테이블 하나,\n"
        "그리고 «부품 전부» 질의에 UNION 한 줄을 더 넣어야 한다.\n"
        "B안에서는 행 하나를 넣으면 끝난다.\n"
        "\n그럼 A안이 무조건 나쁜가. 아니다.\n"
        "«볼트에만 있는 속성»(나사산 규격 같은 것)이 많고 그걸로 질의한다면 A안이 맞다.\n"
        "분류를 나누는 기준은 «다른 속성을 갖는가»이지 «다른 물건인가»가 아니다."
    )


if __name__ == "__main__":
    main()
