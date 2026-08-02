"""
예제 2 — 추론기와 검증기는 다른 물건이다.

    pip install pyshacl owlrl "rdflib>=7,<8"
    python3 ex2_infer_vs_validate.py

같은 «담당자는 반드시 하나 있다»를 두 방식으로 표현하고,
담당자가 없는 데이터를 넣었을 때 각각 무엇을 하는지 본다.
"""

from pyshacl import validate
from rdflib import Graph, Namespace, RDF

EX = Namespace("http://example.org/")

# OWL 방식 — «최소 하나» 를 클래스 제약으로 선언
OWL_SCHEMA = """
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex:   <http://example.org/> .
ex:Company a owl:Class ;
    rdfs:subClassOf [ a owl:Restriction ;
        owl:onProperty ex:managedBy ;
        owl:minCardinality 1 ] .
ex:managedBy a owl:ObjectProperty .
"""

# SHACL 방식 — 같은 뜻을 «형태» 로 선언
SHACL_SHAPE = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/> .
ex:CompanyShape a sh:NodeShape ;
    sh:targetClass ex:Company ;
    sh:property [ sh:path ex:managedBy ; sh:minCount 1 ;
                  sh:message "담당자가 없다" ] .
"""

DATA = """
@prefix ex: <http://example.org/> .
ex:Gaon a ex:Company ; ex:managedBy ex:Kim .
ex:Naru a ex:Company .
"""


def run_owl():
    try:
        import owlrl
    except ImportError:
        return None
    g = Graph().parse(data=OWL_SCHEMA + DATA, format="turtle")
    before = len(g)
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
    after = len(g)
    # 나루소프트에게 담당자가 «생겼는지» 확인
    has = list(g.objects(EX.Naru, EX.managedBy))
    return before, after, has


def run_shacl():
    data = Graph().parse(data=DATA, format="turtle")
    shapes = Graph().parse(data=SHACL_SHAPE, format="turtle")
    ok, _, text = validate(data, shacl_graph=shapes, inference="none")
    hits = [l.strip() for l in text.splitlines()
            if l.strip().startswith(("Focus Node", "Message"))]
    return ok, hits


def main():
    print("데이터: 가온테크는 담당자가 있고, 나루소프트는 없다.")
    print("규칙:   «회사는 담당자가 최소 하나 있어야 한다»\n")

    r = run_owl()
    print("=== OWL 추론기 ===")
    if r is None:
        print("  owlrl 이 설치되지 않았다. pip install owlrl")
    else:
        before, after, has = r
        print(f"  트리플 {before} → {after} (추론으로 {after-before}개 늘었다)")
        print(f"  나루소프트의 담당자: {has if has else '없음(빈 노드로 생기기도 한다)'}")
        print("  → 오류를 내지 않는다. «어딘가 있겠지»로 넘어간다.")

    ok, hits = run_shacl()
    print("\n=== SHACL 검증기 ===")
    print(f"  통과: {ok}")
    for h in hits:
        print(f"    {h[:70]}")
    print("  → 위반으로 잡아서 보고서에 적는다.")

    print(
        "\n같은 문장을 적었는데 하는 일이 다르다.\n"
        "  OWL 은 «세상에 무엇이 있는가»를 말한다. 없으면 있다고 결론 낸다.\n"
        "  SHACL 은 «우리 데이터가 어떤 모양이어야 하는가»를 말한다. 없으면 위반이다.\n"
        "\n제가 3주를 날린 이유가 이거다. 품질 검사를 OWL 로 짰다.\n"
        "추론기는 고장 나지 않았다. 제가 잘못된 도구를 골랐을 뿐이다."
    )


if __name__ == "__main__":
    main()
