"""
예제 5 — 스키마 드리프트를 재는 법. 문서가 아니라 데이터에게 물어본다.

    python3 ex5_schema_drift.py

의존성 없음.
"""

from collections import Counter, defaultdict

# 설계 문서에 적힌 스키마
DECLARED = {
    "Part":    {"id", "name", "category"},
    "Product": {"id", "name", "released_on"},
    "Supplier":{"id", "name"},
}

# 실제 데이터에 나타난 키 (운영 6개월 뒤)
ACTUAL_ROWS = [
    ("Part", {"id", "name", "category"}),
    ("Part", {"id", "name", "category", "legacy_code"}),
    ("Part", {"id", "name", "category", "legacy_code", "temp_flag"}),
    ("Part", {"id", "name"}),                       # category 가 빠졌다
    ("Part", {"id", "name", "category", "note"}),
    ("Product", {"id", "name", "released_on"}),
    ("Product", {"id", "name", "released_on", "recall_reason"}),
    ("Product", {"id", "name"}),
    ("Supplier", {"id", "name", "contact"}),
    ("Supplier", {"id", "name", "contact", "tier"}),
]


def audit(declared, rows):
    seen = defaultdict(Counter)
    counts = Counter()
    for label, keys in rows:
        counts[label] += 1
        for k in keys:
            seen[label][k] += 1
    report = {}
    for label, want in declared.items():
        got = seen[label]
        n = counts[label]
        extra = {k: v for k, v in got.items() if k not in want}
        missing = {k: n - got.get(k, 0) for k in want if got.get(k, 0) < n}
        report[label] = {"건수": n, "선언에 없는 키": extra, "빠진 키": missing}
    return report


def main():
    rep = audit(DECLARED, ACTUAL_ROWS)
    for label, r in rep.items():
        print(f"[{label}]  {r['건수']}건")
        if r["선언에 없는 키"]:
            for k, v in sorted(r["선언에 없는 키"].items(), key=lambda x: -x[1]):
                print(f"    + {k:<14} {v}건 — 문서에 없다")
        if r["빠진 키"]:
            for k, v in sorted(r["빠진 키"].items(), key=lambda x: -x[1]):
                print(f"    - {k:<14} {v}건에서 누락")
        if not r["선언에 없는 키"] and not r["빠진 키"]:
            print("    문서와 일치")
        print()

    print(
        "이 감사를 배치로 매주 돌리면 드리프트가 «쌓이기 전에» 보인다.\n"
        "\n+ 표시가 붙은 키를 보고 셋 중 하나를 정한다.\n"
        "  1. 정식으로 스키마에 넣는다 (recall_reason 처럼 실제로 필요한 것)\n"
        "  2. 지운다 (temp_flag 처럼 임시로 넣고 잊은 것)\n"
        "  3. 별도 영역으로 옮긴다 (legacy_code 처럼 이전 시스템 잔재)\n"
        "\n- 표시는 더 급하다. 선언한 필수 키가 실제로는 없다는 뜻이다.\n"
        "질의가 조용히 빈 결과를 내고 있을 가능성이 높다.\n"
        "\n문서는 거짓말을 한다. 데이터는 안 한다. 문서 말고 데이터에게 물어보시라."
    )


if __name__ == "__main__":
    main()
