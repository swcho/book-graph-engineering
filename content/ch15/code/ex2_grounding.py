"""
예제 2 — 근거 검사. 지어낸 것을 걸러 내는 제일 싼 방법.

    python3 ex2_grounding.py

의존성 없음.
모델에게 «근거 문장»을 같이 내놓으라고 시키고, 그 문장이 원문에 정말 있는지 대조한다.
"""

import re

from docs import DOCS, GOLD
from extractor import extract

TEXT = dict(DOCS)


def normalize(s):
    return re.sub(r"\s+", "", s or "")


def has_evidence(doc_id, quote):
    """근거 문장이 원문에 실제로 있는가."""
    return normalize(quote) in normalize(TEXT.get(doc_id, ""))


def supports(quote, subj, obj):
    """근거 문장이 그 트리플을 실제로 뒷받침하는가.

    핵심은 «목적어»다. 주어는 문서 전체에 흔히 나오지만,
    목적어가 근거 문장에 없으면 그 값은 문장에서 나온 게 아니다.
    이 규칙 하나가 지어내기를 제일 많이 잡는다."""
    q = normalize(quote)
    def core(x):
        x = normalize(x)
        return re.sub(r"[0-9\-]", "", x)[:2] or x[:2]
    return core(obj) in q


HEDGE = ["알려져", "추정", "듯", "로 보인다", "가능성", "일 수 있"]


def is_hedged(doc_id, quote):
    """원문에서 그 문장 주변에 «단정하지 않는» 표현이 있는가."""
    text = TEXT.get(doc_id, "")
    i = text.find(quote[:8])
    window = text[max(0, i - 20): i + len(quote) + 40] if i >= 0 else text
    return any(h in window for h in HEDGE)


def main():
    kept, dropped = [], []
    for did, _ in DOCS:
        for s, p, o, quote in extract(did):
            t = (did, s, p, o)
            if not has_evidence(did, quote):
                dropped.append((t, "근거 문장이 원문에 없다"))
            elif not supports(quote, s, o):
                dropped.append((t, "문장이 트리플을 뒷받침하지 않는다"))
            elif is_hedged(did, quote):
                dropped.append((t, "원문이 단정하지 않는다"))
            else:
                kept.append(t)

    print(f"{'판정':<6} {'트리플'}")
    print("-" * 62)
    for t in kept:
        print(f"{'통과':<6} {t[1]:<12} {t[2]:<10} {t[3]}")
    for t, why in dropped:
        print(f"{'버림':<6} {t[1]:<12} {t[2]:<10} {t[3]:<14} ← {why}")

    got = set(kept)
    tp = got & GOLD
    prec = len(tp) / len(got) if got else 0
    rec = len(tp) / len(GOLD)
    print(f"\n근거 검사 뒤: 정밀도 {prec:.3f}  재현율 {rec:.3f}")
    print("(앞 예제: 정밀도 0.636  재현율 0.778)")

    print(
        "\n세 검사가 각각 다른 걸 잡는다.\n"
        "  근거 문장 존재    — 모델이 문장 자체를 지어낸 경우\n"
        "  목적어 포함       — 문장은 진짜인데 값을 지어낸 경우 («업종: IT 서비스»)\n"
        "  단정 여부         — 원문이 «알려져 있으나»라고 했는데 사실로 바꾼 경우\n"
        "\n두 번째가 제일 많이 잡는다. 그리고 제일 늦게 깨달았다.\n"
        "처음엔 «근거 문장이 원문에 있는가»만 봤는데, «업종»이 통과했다.\n"
        "근거로 낸 문장 «가온테크는»이 원문에 진짜 있었기 때문이다.\n"
        "문장은 진짜고 값만 지어낸 것이다. 이게 제일 흔한 실패다.\n"
        "\n이 검사가 싼 이유는 모델을 한 번 더 부르지 않아서다.\n"
        "문자열 대조라 밀리초 단위고, 결과가 매번 같다.\n"
        "\n대가도 봐야 한다. 재현율이 0.778 에서 0.667 로 떨어졌다.\n"
        "«가온테크 체결 C-2025-118» 이 억울하게 걸렸다. 근거 문장이\n"
        "«가온테크는 2025년 6월 2일» 이라 계약번호가 그 안에 없었기 때문이다.\n"
        "맞는 트리플인데 근거 문장을 짧게 잘라 낸 게 문제였다.\n"
        "\n고치는 방법은 «근거 문장을 문장 단위로 내놓게» 하는 것이다.\n"
        "조각 단위로 자르지 말고 마침표까지. 프롬프트 한 줄이면 되고,\n"
        "이 한 줄이 재현율을 되돌려 놓는다.\n"
        "\n한계도 분명하다. 목적어가 문장에 «있기만» 하면 통과한다.\n"
        "관계가 뒤집힌 경우(«A가 B를 인수»를 «B가 A를 인수»로)는 못 잡는다.\n"
        "그건 모델을 한 번 더 불러야 한다. 값이 두 배가 되고 정밀도가 오른다."
    )


if __name__ == "__main__":
    main()
