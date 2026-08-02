"""
예제 1 — 전수 비교는 왜 안 되나, 그리고 블로킹이 무엇을 놓치나.

    python3 ex1_blocking.py

의존성 없음.
"""

import re
from collections import defaultdict
from itertools import combinations

from records import RECORDS


def norm_name(s):
    """법인격 표기와 공백을 걷어 낸다."""
    s = re.sub(r"\(주\)|주식회사|\(유\)|유한회사", "", s)
    return re.sub(r"\s+", "", s)


def key_bizno(r):
    return r[2] or None


def key_name3(r):
    n = norm_name(r[1])
    return n[:3] if len(n) >= 3 else n or None


def key_addr(r):
    a = r[3]
    return " ".join(a.split()[:2]) if a else None


def block(records, keyfn):
    b = defaultdict(list)
    for r in records:
        k = keyfn(r)
        if k:
            b[k].append(r[0])
    return {k: v for k, v in b.items() if len(v) > 1}


def pairs_from(blocks):
    out = set()
    for ids in blocks.values():
        for a, b in combinations(sorted(ids), 2):
            out.add((a, b))
    return out


def main():
    n = len(RECORDS)
    allpairs = n * (n - 1) // 2
    print(f"레코드 {n}개 → 전수 비교 쌍 {allpairs}개")
    print(f"10만 개라면 {100_000*99_999//2:,}쌍. 하루로 안 끝난다.\n")

    strategies = {
        "사업자번호": key_bizno,
        "이름 앞 3글자": key_name3,
        "주소 앞 2어절": key_addr,
    }
    unions = set()
    for label, fn in strategies.items():
        b = block(RECORDS, fn)
        p = pairs_from(b)
        unions |= p
        print(f"[{label}] 칸 {len(b)}개, 비교 쌍 {len(p)}개")
        for k, v in sorted(b.items()):
            print(f"    {k!r:<22} {v}")
        print()

    print(f"세 전략을 «합치면» 비교 쌍 {len(unions)}개 "
          f"(전수 {allpairs}개의 {len(unions)/allpairs*100:.0f}%)")

    # 정답 쌍이 후보에 들어왔는지 확인 — 이게 블로킹의 재현율이다
    from records import TRUTH
    truth_pairs = set()
    for group in TRUTH:
        for a, b in combinations(sorted(group), 2):
            truth_pairs.add((a, b))
    missed = truth_pairs - unions
    print(f"\n정답 쌍 {len(truth_pairs)}개 중 후보에 못 든 것: {len(missed)}개 {sorted(missed)}")

    print(
        "\n블로킹의 성패는 «재현율»이다. 후보에 못 들면 영영 못 만난다.\n"
        "그래서 전략을 하나만 쓰면 안 된다. 여러 개를 돌리고 합집합을 쓴다.\n"
        "\n사업자번호 하나만 썼다면 r03(번호 없음)을 놓쳤을 것이다.\n"
        "이름만 썼다면 r04(GAON TECH)를 놓쳤을 것이고.\n"
        "\n전략을 늘리면 후보가 늘어 느려진다. 그 균형이 설계다."
    )


if __name__ == "__main__":
    main()
