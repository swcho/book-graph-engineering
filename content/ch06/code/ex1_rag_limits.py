"""
예제 1 — 조각 검색만으로 «전역» 질문에 답해 보기.

    python3 ex1_rag_limits.py

의존성 없음. 1장의 벡터 검색과 같은 방식(글자 2-gram TF-IDF)을 쓴다.
"""

import math
import re
from collections import Counter

from corpus import DOCS, GLOBAL_QUESTION, GROUND_TRUTH

TOP_K = 4


def grams(t, n=2):
    s = re.sub(r"[^0-9A-Za-z가-힣]", "", t)
    return [s[i:i + n] for i in range(len(s) - n + 1)]


def search(query, docs, k):
    tfs = [Counter(grams(d[1])) for d in docs]
    df = Counter()
    for tf in tfs:
        df.update(tf.keys())
    n = len(docs)
    idf = {g: math.log((n + 1) / (df[g] + 1)) + 1 for g in df}

    def vec(c):
        v = {g: x * idf.get(g, 0) for g, x in c.items()}
        nm = math.sqrt(sum(y * y for y in v.values())) or 1
        return {g: y / nm for g, y in v.items()}

    qv = vec(Counter(grams(query)))
    scored = []
    for i, tf in enumerate(tfs):
        dv = vec(tf)
        keys = qv.keys() & dv.keys()
        scored.append((sum(qv[g] * dv[g] for g in keys), i))
    scored.sort(reverse=True)
    return scored[:k]


def main():
    print(f"질문: {GLOBAL_QUESTION}\n")
    hits = search(GLOBAL_QUESTION, DOCS, TOP_K)
    print(f"상위 {TOP_K}개 조각")
    for s, i in hits:
        print(f"  [{s:.3f}] {DOCS[i][0]} {DOCS[i][1]}")

    print(
        f"\n이 {TOP_K}개만 보고 «반복되는 원인»을 셀 수 있나?\n"
        f"전체 {len(DOCS)}건 중 {TOP_K}건만 봤다. 나머지 {len(DOCS)-TOP_K}건에 무엇이 있는지 모른다.\n"
        f"정답은 {sorted(GROUND_TRUTH)} 인데, 이건 전체를 세어야 나오는 답이다.\n"
        "\nk 를 12로 올려 전부 넣으면? 이 예제에서는 된다. 문서가 12건이니까.\n"
        "문서가 12만 건이면 못 넣는다. 그게 이 한계의 실체다.\n"
        "«조각을 더 넣기»로는 못 넘는 벽이고, 그래서 색인 시점에 미리 접어 둬야 한다."
    )


if __name__ == "__main__":
    main()
