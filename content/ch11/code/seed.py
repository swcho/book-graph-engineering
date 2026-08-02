"""11장 공통 데이터. 같은 사실을 Cypher(Kuzu) · SPARQL(rdflib) · SQL 세 곳에 넣는다."""

COMPANIES = [("가온테크", "A"), ("나루소프트", "B"), ("라온에너지", "C"), ("다올물산", "B")]
CONTRACTS = [
    ("M-2021-077", None, "2024-03-11"),
    ("C-2025-118", "2025-06-02", None),
    ("C-2025-004", "2025-01-20", None),
    ("M-2020-031", None, "2024-08-05"),
    ("C-2026-010", "2026-02-01", None),
]
SIGNED = [("가온테크", "C-2025-118"), ("나루소프트", "C-2025-004"),
          ("다올물산", "C-2026-010")]
TERMINATED = [("가온테크", "M-2021-077"), ("라온에너지", "M-2020-031")]
PARENT_OF = [("가온테크", "가온소프트"), ("가온소프트", "가온연구소")]

TTL = """
@prefix ex:  <http://example.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
ex:Gaon  a ex:Company ; ex:name "가온테크" ; ex:grade "A" ;
   ex:terminated ex:M2021077 ; ex:signed ex:C2025118 ;
   ex:parentOf ex:GaonSoft .
ex:GaonSoft a ex:Company ; ex:name "가온소프트" ; ex:parentOf ex:GaonLab .
ex:GaonLab  a ex:Company ; ex:name "가온연구소" .
ex:Naru a ex:Company ; ex:name "나루소프트" ; ex:grade "B" ; ex:signed ex:C2025004 .
ex:Raon a ex:Company ; ex:name "라온에너지" ; ex:grade "C" ; ex:terminated ex:M2020031 .
ex:Daol a ex:Company ; ex:name "다올물산" ; ex:grade "B" ; ex:signed ex:C2026010 .
ex:M2021077 ex:endedOn   "2024-03-11"^^xsd:date .
ex:M2020031 ex:endedOn   "2024-08-05"^^xsd:date .
ex:C2025118 ex:startedOn "2025-06-02"^^xsd:date .
ex:C2025004 ex:startedOn "2025-01-20"^^xsd:date .
ex:C2026010 ex:startedOn "2026-02-01"^^xsd:date .
"""
