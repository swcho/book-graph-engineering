"""
예제 1 — 벡터 검색만으로 답해 보기.

    python3 ex1_vector_only.py

의존성 없음. 임베딩 모델 대신 글자 2-gram TF-IDF 코사인 유사도를 쓴다.
모델을 큰 걸로 바꿔도 이 예제가 보여 주는 한계는 그대로다.
관계를 저장하지 않았기 때문에 생기는 한계라서 그렇다.
"""

import math
import re
from collections import Counter

from notes import NOTES, QUESTION, GROUND_TRUTH

TOP_K = 3


def grams(text, n=2):
    """한국어는 띄어쓰기가 들쭉날쭉하다. 글자 n-gram이 형태소 분석기 없이도 잘 먹힌다."""
    s = re.sub(r"[^0-9A-Za-z가-힣]", "", text)
    return [s[i:i + n] for i in range(len(s) - n + 1)]


def build_index(docs):
    tfs = [Counter(grams(d)) for d in docs]
    df = Counter()
    for tf in tfs:
        df.update(tf.keys())
    n = len(docs)
    idf = {g: math.log((n + 1) / (df[g] + 1)) + 1.0 for g in df}
    vecs = []
    for tf in tfs:
        v = {g: c * idf.get(g, 0.0) for g, c in tf.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs.append({g: x / norm for g, x in v.items()})
    return vecs, idf


def search(query, vecs, idf, k=TOP_K):
    q = Counter(grams(query))
    qv = {g: c * idf.get(g, 0.0) for g, c in q.items()}
    norm = math.sqrt(sum(x * x for x in qv.values())) or 1.0
    qv = {g: x / norm for g, x in qv.items()}
    scored = []
    for i, v in enumerate(vecs):
        keys = qv.keys() & v.keys()
        scored.append((sum(qv[g] * v[g] for g in keys), i))
    scored.sort(reverse=True)
    return scored[:k]


def main():
    vecs, idf = build_index(NOTES)
    hits = search(QUESTION, vecs, idf)

    print(f"질문: {QUESTION}\n")
    print(f"상위 {TOP_K}개 문서")
    for score, i in hits:
        print(f"  [{score:.3f}] {NOTES[i]}")

    # 검색된 문서만 보고 회사 이름을 뽑아 보자. 이게 벡터 검색이 줄 수 있는 최선이다.
    names = {"가온테크", "나루소프트", "다올물산", "라온에너지"}
    guessed = {n for _, i in hits for n in names if n in NOTES[i]}

    print(f"\n검색 결과에서 뽑은 후보: {sorted(guessed) or '없음'}")
    print(f"정답:                    {sorted(GROUND_TRUTH)}")
    print(f"맞았나: {'예' if guessed == GROUND_TRUTH else '아니오'}")
    print(
        "\n왜 틀렸나: '해지'가 들어간 문장과 '체결'이 들어간 문장은 서로 다른 벡터다.\n"
        "두 문장이 같은 회사를 가리킨다는 사실이 어디에도 적혀 있지 않다.\n"
        "top-k를 8로 올려 문서를 전부 넣어도, 두 사실을 잇는 일은 모델의 짐작에 맡겨진다."
    )


if __name__ == "__main__":
    main()
