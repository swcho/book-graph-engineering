"""
5장 공통 데이터. 같은 사실 여섯 개를 두 가지 모델로 적는다. 의존성 없음.
"""

# ---- 프로퍼티 그래프 (LPG) ----
# 노드도 엣지도 속성 주머니를 하나씩 갖는다.
LPG_NODES = {
    "n1": {"labels": ["Company"], "props": {"name": "가온테크", "grade": "A"}},
    "n2": {"labels": ["Contract"], "props": {"id": "C-2025-118", "amount": 5_000_000}},
    "n3": {"labels": ["Person", "Employee"], "props": {"name": "김하늘", "title": "부장"}},
}
LPG_EDGES = [
    {"from": "n1", "type": "SIGNED", "to": "n2",
     "props": {"at": "2025-06-02", "channel": "직접", "confidence": 0.98}},
    {"from": "n1", "type": "MANAGED_BY", "to": "n3",
     "props": {"since": "2023-04-01"}},
]

# ---- RDF (같은 사실) ----
RDF_TRIPLES = [
    ("ex:Gaon", "rdf:type", "ex:Company"),
    ("ex:Gaon", "ex:name", '"가온테크"'),
    ("ex:Gaon", "ex:grade", '"A"'),
    ("ex:C2025118", "rdf:type", "ex:Contract"),
    ("ex:C2025118", "ex:id", '"C-2025-118"'),
    ("ex:C2025118", "ex:amount", '"5000000"^^xsd:integer'),
    ("ex:Kim", "rdf:type", "ex:Person"),
    ("ex:Kim", "rdf:type", "ex:Employee"),
    ("ex:Kim", "ex:name", '"김하늘"'),
    ("ex:Kim", "ex:title", '"부장"'),
    ("ex:Gaon", "ex:signed", "ex:C2025118"),
    ("ex:Gaon", "ex:managedBy", "ex:Kim"),
]

# 엣지에 붙은 속성을 RDF 로 적으려면 방법 세 가지 중 하나를 골라야 한다.
# (1) 구체화 — 관계를 노드로 승격
RDF_REIFIED = [
    ("ex:Gaon", "ex:hasSigning", "ex:Signing1"),
    ("ex:Signing1", "rdf:type", "ex:Signing"),
    ("ex:Signing1", "ex:contract", "ex:C2025118"),
    ("ex:Signing1", "ex:at", '"2025-06-02"^^xsd:date'),
    ("ex:Signing1", "ex:channel", '"직접"'),
    ("ex:Signing1", "ex:confidence", '"0.98"^^xsd:decimal'),
]
# (2) RDF-star — 트리플 자체를 주어로. 표기가 간결하다.
RDF_STAR = [
    "ex:Gaon ex:signed ex:C2025118 .",
    "<< ex:Gaon ex:signed ex:C2025118 >> ex:at        \"2025-06-02\"^^xsd:date .",
    "<< ex:Gaon ex:signed ex:C2025118 >> ex:channel   \"직접\" .",
    "<< ex:Gaon ex:signed ex:C2025118 >> ex:confidence \"0.98\"^^xsd:decimal .",
]
# (3) 이름 붙인 그래프 — 트리플 묶음에 이름을 주고 그 이름에 속성을 단다
RDF_NAMED_GRAPH = [
    "GRAPH ex:g1 { ex:Gaon ex:signed ex:C2025118 . }",
    "ex:g1 ex:at \"2025-06-02\"^^xsd:date .",
    "ex:g1 ex:channel \"직접\" .",
]
