"""
예제 2 — 점수 매기기와 임계. 그리고 «이행성»이 놓친 쌍을 주워 온다.

    python3 ex2_scoring.py

의존성 없음.
"""

import re
from itertools import combinations

from records import RECORDS, TRUTH

BY_ID = {r[0]: r for r in RECORDS}


def norm_name(s):
    s = re.sub(r"\(주\)|주식회사|\(유\)|유한회사", "", s)
    return re.sub(r"\s+", "", s)


def norm_phone(s):
    return re.sub(r"\D", "", s or "")


def sim_str(a, b):
    """글자 2-gram 자카드. 라이브러리 없이 쓸 만하다."""
    def g(x):
        x = re.sub(r"\s+", "", x or "")
        return {x[i:i+2] for i in range(len(x)-1)} or {x}
    A, B = g(a), g(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


FIELDS = [
    # (이름, 추출 함수, 가중치, 비교 방식)
    ("사업자번호", lambda r: r[2], 0.45, "exact"),
    ("이름",      lambda r: norm_name(r[1]), 0.25, "fuzzy"),
    ("주소",      lambda r: r[3], 0.15, "fuzzy"),
    ("대표자",    lambda r: r[4], 0.10, "exact"),
    ("전화",      lambda r: norm_phone(r[5]), 0.05, "exact"),
]


def score(a, b):
    total = 0.0
    used = 0.0
    detail = []
    for name, get, w, mode in FIELDS:
        x, y = get(a), get(b)
        if not x or not y:          # 한쪽이 비면 그 항목은 «모름»으로 빼둔다
            detail.append((name, None, w))
            continue
        s = 1.0 if (mode == "exact" and x == y) else (
            0.0 if mode == "exact" else sim_str(x, y))
        total += w * s
        used += w
        detail.append((name, s, w))
    return (total / used if used else 0.0), detail


HIGH, LOW = 0.85, 0.55


def main():
    print(f"{'쌍':<12} {'점수':>6}  판정")
    print("-" * 46)
    auto, review = [], []
    for a, b in combinations(sorted(BY_ID), 2):
        s, _ = score(BY_ID[a], BY_ID[b])
        if s >= LOW:
            verdict = "자동 병합" if s >= HIGH else "사람 검토"
            (auto if s >= HIGH else review).append((a, b))
            print(f"{a}–{b:<7} {s:>6.3f}  {verdict}")

    # 이행성으로 묶기
    parent = {k: k for k in BY_ID}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(x, y):
        parent[find(x)] = find(y)
    for a, b in auto:
        union(a, b)
    groups = {}
    for k in BY_ID:
        groups.setdefault(find(k), []).append(k)
    clusters = {frozenset(v) for v in groups.values() if len(v) > 1}

    print(f"\n자동 병합 {len(auto)}쌍 → 이행성으로 묶으면 군집 {len(clusters)}개")
    for c in sorted(clusters, key=lambda x: sorted(x)):
        print(f"    {sorted(c)}")

    print(f"\n정답 군집")
    for c in sorted(TRUTH, key=lambda x: sorted(x)):
        print(f"    {sorted(c)}")

    print(f"\n자동 병합만으로 정답과 일치: {'예' if clusters == TRUTH else '아니오'}")
    print(f"사람 검토로 넘어간 쌍 {len(review)}개: {review}")

    # 사람이 판정한 결과를 반영한다 — r04 는 같음, r06/r07 은 다름
    HUMAN = {("r01", "r04"): True, ("r02", "r04"): True, ("r06", "r07"): False}
    for (a, b), same in HUMAN.items():
        if same:
            union(a, b)
    groups2 = {}
    for k in BY_ID:
        groups2.setdefault(find(k), []).append(k)
    clusters2 = {frozenset(v) for v in groups2.values() if len(v) > 1}

    print(f"\n사람 판정을 반영한 뒤 군집 {len(clusters2)}개")
    for c in sorted(clusters2, key=lambda x: sorted(x)):
        print(f"    {sorted(c)}")
    print(f"정답과 일치: {'예' if clusters2 == TRUTH else '아니오'}")

    print(
        "\n자동 병합만으로는 정답에 못 갔다. r04(GAON TECH)가 걸렸다.\n"
        "사업자번호는 같은데 이름이 영문이고 주소·대표자·전화가 비어 있어서\n"
        "점수가 0.643 으로 애매 구간에 떨어졌다.\n"
        "\n이게 정상이다. 이 정보만으로는 «같다»고 단정할 수 없으니까.\n"
        "자동화가 할 일은 «다 맞히는 것»이 아니라 «애매한 것을 골라내는 것»이다.\n"
        "여기서는 12개 레코드 중 3쌍만 사람에게 갔다. 그게 성과다.\n"
        "\n반대 방향도 보라. r06–r07(나루소프트/나루소프트(주))은 0.550 으로\n"
        "애매 구간 바닥에 걸렸고, 사람이 «다르다»고 판정했다. 사업자번호가 다르니까.\n"
        "자동 병합 임계를 0.55 로 낮췄다면 모회사와 자회사를 합쳐 버렸을 것이다.\n"
        "제가 실제로 그렇게 했고, 되돌리는 데 사흘 걸렸다.\n"
        "\n이행성도 공짜가 아니다. 잘못된 병합 하나가 군집 전체를 오염시킨다.\n"
        "그래서 군집 크기에 상한을 두거나, 커지면 사람에게 보내는 게 안전하다."
    )


if __name__ == "__main__":
    main()
