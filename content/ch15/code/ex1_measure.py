"""
예제 1 — 정밀도와 재현율을 먼저 잰다. 재지 않으면 개선했는지 모른다.

    python3 ex1_measure.py

의존성 없음.
"""

from docs import DOCS, GOLD
from extractor import extract


def main():
    got = set()
    for did, _ in DOCS:
        for s, p, o, _ in extract(did):
            got.add((did, s, p, o))

    tp = got & GOLD
    fp = got - GOLD
    fn = GOLD - got
    prec = len(tp) / len(got) if got else 0
    rec = len(tp) / len(GOLD) if GOLD else 0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0

    print(f"뽑은 트리플 {len(got)}개, 정답 {len(GOLD)}개\n")
    print(f"맞음  {len(tp):>2}개")
    print(f"틀림  {len(fp):>2}개")
    print(f"놓침  {len(fn):>2}개")
    print(f"\n정밀도 {prec:.3f}  재현율 {rec:.3f}  F1 {f1:.3f}\n")

    print("틀린 것 — 왜 틀렸는지 종류를 나눠 보면")
    reasons = {
        ("d01", "C-2025-118", "계약체결일자", "2025-06-02"): "어휘 밖 술어 (뜻은 맞다)",
        ("d01", "가온테크", "업종", "IT 서비스"): "지어냄 (원문에 없다)",
        ("d04", "가온테크", "협업", "나루소프트"): "어휘 밖 + 근거가 약하다",
        ("d05", "마루상사", "모회사", "다올물산"): "추측을 사실로 (공시된 바 없다)",
    }
    for t in sorted(fp):
        print(f"    {t[1]:<12} {t[2]:<8} {t[3]:<14} — {reasons.get(t, '?')}")

    print("\n놓친 것")
    for t in sorted(fn):
        print(f"    {t[1]:<12} {t[2]:<8} {t[3]}")

    print(
        "\n정밀도 0.64는 «열에 서넛이 거짓»이라는 뜻이다.\n"
        "이 상태로 적재하면 질의가 거짓을 답한다. 그리고 사용자는 한 번 겪으면 안 쓴다.\n"
        "\n그런데 틀린 넷이 다 같은 종류가 아니다.\n"
        "  «계약체결일자»는 뜻이 맞다. 어휘에 매핑하면 정답이 된다.\n"
        "  «업종»과 «모회사»는 진짜 거짓이다. 버려야 한다.\n"
        "\n종류를 안 나누고 «정밀도 0.6»만 보면 무엇을 고칠지 모른다.\n"
        "오류를 분류하는 게 개선의 첫 단계다."
    )


if __name__ == "__main__":
    main()
