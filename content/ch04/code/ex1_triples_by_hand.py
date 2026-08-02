"""
예제 1 — 트리플 저장소를 30줄로. 의존성 없음.

    python3 ex1_triples_by_hand.py

RDF 가 어렵다는 인상은 대개 «도구»에서 옵니다. 모델 자체는 세 칸짜리 표예요.
"""

TRIPLES = [
    ("가온테크", "해지",   "계약:M-2021-077"),
    ("가온테크", "체결",   "계약:C-2025-118"),
    ("가온테크", "담당",   "김하늘"),
    ("가온테크", "모회사", "가온소프트"),
    ("가온소프트", "모회사", "가온연구소"),
    ("나루소프트", "체결", "계약:C-2025-004"),
]


def match(triples, s=None, p=None, o=None):
    """세 칸 중 아는 것만 채워서 묻는다. 이게 SPARQL 이 하는 일의 전부다."""
    return [t for t in triples
            if (s is None or t[0] == s)
            and (p is None or t[1] == p)
            and (o is None or t[2] == o)]


def closure(triples, prop):
    """이행성: A→B, B→C 면 A→C. OWL 이 대신 해 주는 계산을 직접 해 본다."""
    out = set(t for t in triples if t[1] == prop)
    changed = True
    while changed:
        changed = False
        for a, _, b in list(out):
            for c, _, d in list(out):
                if b == c and (a, prop, d) not in out and a != d:
                    out.add((a, prop, d))
                    changed = True
    return sorted(out)


if __name__ == "__main__":
    print("가온테크에 대해 아는 것")
    for t in match(TRIPLES, s="가온테크"):
        print("  ", " ".join(t))

    print("\n체결한 곳 전부")
    for t in match(TRIPLES, p="체결"):
        print("  ", t[0], "→", t[2])

    print("\n적어 두지 않은 사실 — 이행성으로 끌어낸 것")
    written = set(t for t in TRIPLES if t[1] == "모회사")
    for t in closure(TRIPLES, "모회사"):
        mark = "  " if t in written else "* "
        print(f"  {mark}{t[0]} 모회사 {t[2]}")
    print("\n  * 표시가 «아무도 적지 않았는데 참인» 문장이다.")
    print("  이걸 자동으로 해 주는 게 OWL 의 이행성 선언 한 줄이다.")
