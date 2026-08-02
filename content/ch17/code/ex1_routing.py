"""
예제 1 — 질문 유형별로 라우팅한다. 그리고 라우터가 틀렸을 때를 본다.

    python3 ex1_routing.py

의존성 없음.
"""

import math
import re
from collections import Counter, defaultdict

from corpus17 import DOCS, QUESTIONS, TRIPLES

TEXT = dict(DOCS)

AGG_WORDS = ["전체", "몇 건", "가장", "자주", "평균", "총", "별로", "추세", "반복"]
MULTI_WORDS = ["공통", "누구", "관련", "함께", "같은"]


def route(q):
    if any(w in q for w in AGG_WORDS):
        return "전역집계"
    if any(w in q for w in MULTI_WORDS):
        return "다중홉"
    return "사실조회"


# ---------- 벡터 검색 (1장과 같은 방식) ----------
def grams(t, n=2):
    s = re.sub(r"[^0-9A-Za-z가-힣]", "", t)
    return [s[i:i + n] for i in range(len(s) - n + 1)]


def vector_answer(q, k=1):
    tfs = [Counter(grams(t)) for _, t in DOCS]
    df = Counter()
    for tf in tfs:
        df.update(tf)
    n = len(DOCS)
    idf = {g: math.log((n + 1) / (df[g] + 1)) + 1 for g in df}

    def vec(c):
        v = {g: x * idf.get(g, 0) for g, x in c.items()}
        nm = math.sqrt(sum(y * y for y in v.values())) or 1
        return {g: y / nm for g, y in v.items()}

    qv = vec(Counter(grams(q)))
    scored = sorted(((sum(qv[g] * vec(tf).get(g, 0) for g in qv), i)
                     for i, tf in enumerate(tfs)), reverse=True)[:k]
    hit_docs = [DOCS[i][0] for _, i in scored]
    return {o for d, p, o in TRIPLES if d in hit_docs and p == "원인"}


# ---------- 그래프 순회 ----------
def graph_answer(q):
    by_doc = defaultdict(lambda: defaultdict(set))
    for d, p, o in TRIPLES:
        by_doc[d][p].add(o)
    for person in {o for _, p, o in TRIPLES if p == "담당"}:
        if person in q:
            docs = [d for d in by_doc if person in by_doc[d]["담당"]]
            causes = [c for d in docs for c in by_doc[d]["원인"]]
            cnt = Counter(causes)
            top = max(cnt.values())
            return {c for c, n in cnt.items() if n == top}
    for cause in {o for _, p, o in TRIPLES if p == "원인"}:
        if cause in q:
            docs = [d for d in by_doc if cause in by_doc[d]["원인"]]
            return {p for d in docs for p in by_doc[d]["담당"]}
    return set()


# ---------- 전역 집계 ----------
def global_answer(q):
    if "담당자별" in q or "담당자" in q and "건수" in q:
        return {p for _, pr, p in TRIPLES if pr == "담당"}
    causes = Counter(o for _, p, o in TRIPLES if p == "원인")
    top = causes.most_common(1)[0][1]
    return {c for c, n in causes.items() if n == top}


ENGINES = {"사실조회": vector_answer, "다중홉": graph_answer,
           "전역집계": global_answer}


def main():
    print(f"{'질문':<28} {'실제 유형':<8} {'라우터':<8} {'정답?':<6} 답")
    print("-" * 86)
    right = 0
    for q, kind, gold in QUESTIONS:
        r = route(q)
        got = ENGINES[r](q)
        ok = got == gold
        right += ok
        print(f"{q:<28} {kind:<8} {r:<8} {'예' if ok else '아니오':<6} "
              f"{sorted(got) or '—'}")

    print(f"\n{right}/{len(QUESTIONS)} 정답")

    print("\n라우터를 일부러 틀리게 해 보면")
    q, kind, gold = QUESTIONS[4]
    for wrong in ("사실조회", "다중홉"):
        got = ENGINES[wrong](q)
        print(f"    «{q}» 를 {wrong} 로 보내면 → {sorted(got) or '—'} "
              f"(정답 {sorted(gold)})")

    print(
        "\n라우터가 틀리면 «틀린 엔진이 그럴듯한 답»을 낸다. 이게 무섭다.\n"
        "빈 답이면 사용자가 알아채는데, 그럴듯한 답이면 그냥 믿는다.\n"
        "\n그래서 라우터를 애매할 때 어느 쪽으로 기울일지가 설계다.\n"
        "저는 벡터 쪽으로 기울인다. 벡터가 틀리면 «근거 문서»가 같이 나와서\n"
        "사용자가 «어 이거 아닌데»를 알아챌 여지가 있기 때문이다.\n"
        "그래프 집계는 숫자만 나와서 검증할 방법이 없다."
    )


if __name__ == "__main__":
    main()
