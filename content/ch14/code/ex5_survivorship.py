"""
예제 5 — 병합할 때 «어느 값을 남길 것인가». 규칙을 못 박아 두지 않으면 매번 다르다.

    python3 ex5_survivorship.py

의존성 없음.
"""

from datetime import date

RECORDS = [
    {"id": "r01", "src": "ERP",    "updated": date(2024, 3, 1),
     "name": "가온테크",     "ceo": "김하늘", "tel": "02-1234-5678", "addr": "서울 강남구 테헤란로 1"},
    {"id": "r02", "src": "CRM",    "updated": date(2026, 1, 15),
     "name": "(주)가온테크", "ceo": "박서준", "tel": "",             "addr": "서울 강남구 테헤란로 1길 22"},
    {"id": "r04", "src": "명함스캔", "updated": date(2025, 7, 9),
     "name": "GAON TECH",  "ceo": "",       "tel": "02-1234-5679", "addr": ""},
]

SOURCE_TRUST = {"ERP": 3, "CRM": 2, "명함스캔": 1}

RULES = {
    "name": "가장 신뢰도 높은 출처",
    "ceo":  "가장 최근",
    "tel":  "가장 최근 중 비어 있지 않은 것",
    "addr": "가장 긴 값",
}


def pick(field, rows):
    cand = [r for r in rows if r.get(field)]
    if not cand:
        return None, "값이 없다"
    rule = RULES[field]
    if rule == "가장 신뢰도 높은 출처":
        r = max(cand, key=lambda x: SOURCE_TRUST.get(x["src"], 0))
    elif rule == "가장 최근":
        r = max(cand, key=lambda x: x["updated"])
    elif rule == "가장 최근 중 비어 있지 않은 것":
        r = max(cand, key=lambda x: x["updated"])
    else:
        r = max(cand, key=lambda x: len(x[field]))
    return r[field], f"{rule} → {r['id']}({r['src']}, {r['updated']})"


def main():
    print("병합 대상")
    for r in RECORDS:
        print(f"  {r['id']} [{r['src']:<5} {r['updated']}] "
              f"{r['name']:<12} {r['ceo'] or '—':<5} {r['tel'] or '—':<14} {r['addr'] or '—'}")

    print("\n필드별로 «남길 값»을 규칙에 따라 고른다")
    print(f"{'필드':<6} {'선택된 값':<26} 근거")
    print("-" * 74)
    merged = {}
    for f in RULES:
        v, why = pick(f, RECORDS)
        merged[f] = v
        print(f"{f:<6} {str(v):<26} {why}")

    print(
        "\n대표자가 «박서준»으로 정해진 게 눈에 띈다. CRM 이 가장 최근이니까.\n"
        "그런데 ERP 가 더 믿을 만한 출처라면 «김하늘»이 맞을 수도 있다.\n"
        "\n어느 쪽이 정답인가. 도메인이 정한다.\n"
        "  대표자는 «바뀌는» 값이다 → 최근이 맞다\n"
        "  사업자번호는 «안 바뀌는» 값이다 → 신뢰도 높은 출처가 맞다\n"
        "\n중요한 건 규칙을 «필드마다» 정해서 코드에 박아 두는 것이다.\n"
        "규칙이 없으면 개발자가 그때그때 정하고, 6개월 뒤에 아무도 이유를 모른다.\n"
        "\n그리고 고른 값마다 «어디서 왔는지»를 같이 저장한다.\n"
        "그게 있어야 «이 대표자 이름 왜 이래요» 라는 문의에 답할 수 있다. 16장에서 다룬다."
    )


if __name__ == "__main__":
    main()
