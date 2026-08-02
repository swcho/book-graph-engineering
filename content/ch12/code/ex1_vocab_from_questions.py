"""
예제 1 — 질의에서 어휘를 거꾸로 뽑는다.

    python3 ex1_vocab_from_questions.py

의존성 없음.
"""

from questions import EXPERT_TAXONOMY, QUESTIONS, VOCAB_FROM_QUESTIONS


def main():
    print("역량 질문 다섯 개")
    for i, q in enumerate(QUESTIONS, 1):
        print(f"  {i}. {q}")

    total = sum(len(v) for v in VOCAB_FROM_QUESTIONS.values())
    print(f"\n여기서 뽑은 어휘 — 전부 {total}개")
    for kind, words in VOCAB_FROM_QUESTIONS.items():
        print(f"  {kind:<6} {', '.join(words)}")

    print(f"\n도메인 전문가가 처음 제시한 분류 (일부): {len(EXPERT_TAXONOMY)}개")
    print(f"  {', '.join(EXPERT_TAXONOMY[:12])} ...")

    used = set()
    for words in VOCAB_FROM_QUESTIONS.values():
        used.update(words)
    unused = [t for t in EXPERT_TAXONOMY if t not in used]
    print(f"\n다섯 질문에 답하는 데 «쓰이지 않는» 분류: {len(unused)}개")
    print(f"  {', '.join(unused[:12])} ...")

    print(
        "\n«M6스테인리스육각볼트» 는 틀린 분류가 아니다. 정확한 분류다.\n"
        "다만 이 다섯 질문에 답하는 데는 필요가 없다.\n"
        "\n필요해지는 순간이 오면 그때 넣으면 된다.\n"
        "그때 넣는 비용보다, 안 쓰는 분류 190개를 유지하는 비용이 크다.\n"
        "\n온톨로지는 도메인의 진리가 아니라 «지금 우리 질의가 필요로 하는 최소 어휘»다."
    )


if __name__ == "__main__":
    main()
