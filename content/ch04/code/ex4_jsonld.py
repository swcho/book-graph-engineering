"""
예제 4 — 시맨틱 웹이 실제로 이긴 자리. 웹페이지 안의 구조화 데이터.

    python3 ex4_jsonld.py

의존성 없음.
«웹 전체를 태깅하자»는 실패했지만, 검색 결과에 별점과 가격을 띄우고 싶은 욕구는
schema.org 태깅을 전 세계에 퍼뜨렸습니다. 명분이 아니라 이득이 표준을 퍼뜨립니다.
"""

import json
import re

HTML = """
<html><head><title>가온테크 유지보수 계약</title>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "가온테크",
  "url": "https://example.org/gaon",
  "employee": {"@type": "Person", "name": "김하늘", "jobTitle": "부장"},
  "aggregateRating": {"@type": "AggregateRating", "ratingValue": 4.3, "reviewCount": 27}
}
</script>
</head><body>...</body></html>
"""


def extract_jsonld(html):
    blocks = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.S | re.I)
    return [json.loads(b) for b in blocks]


def to_triples(obj, subject=None, prefix="_:b"):
    """JSON-LD 를 트리플로 편다. 중첩 객체는 빈 노드가 된다."""
    out, counter = [], [0]

    def walk(node, subj):
        for k, v in node.items():
            if k in ("@context",):
                continue
            if k == "@type":
                out.append((subj, "a", v))
                continue
            if isinstance(v, dict):
                counter[0] += 1
                child = f"{prefix}{counter[0]}"
                out.append((subj, k, child))
                walk(v, child)
            else:
                out.append((subj, k, v))

    root = subject or node_name(obj)
    walk(obj, root)
    return out


def node_name(obj):
    return obj.get("url") or obj.get("name") or "_:root"


if __name__ == "__main__":
    for doc in extract_jsonld(HTML):
        print(f"@type = {doc.get('@type')}, 주어 = {node_name(doc)}\n")
        for s, p, o in to_triples(doc):
            print(f"  {s:<28} {p:<18} {o}")

    print(
        "\n이 세 칸짜리 줄들이 RDF 다. 문법이 Turtle 이든 JSON-LD 든 상관없다.\n"
        "\n시맨틱 웹의 이상은 «모두가 뜻을 합의하자»였고, 그건 실패했다.\n"
        "실제로 퍼진 건 «검색 결과에 별점이 뜨면 클릭률이 오른다»였다.\n"
        "표준을 퍼뜨리는 건 명분이 아니라 이득이다. 이 문장은 여러분 사내 표준에도 적용된다."
    )
