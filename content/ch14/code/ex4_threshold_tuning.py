"""
예제 4 — 임계 하나를 옮기면 무엇이 달라지나. 정밀도·재현율·사람 부담.

    python3 ex4_threshold_tuning.py

의존성 없음.
"""

import random

random.seed(20260801)

# 점수 분포를 흉내 낸다. 실제 데이터에서 뽑은 모양에 가깝다.
# 같은 것들은 높은 쪽에, 다른 것들은 낮은 쪽에 몰리되 «겹치는 구간»이 있다.
SAME = [min(1.0, max(0.0, random.gauss(0.86, 0.11))) for _ in range(400)]
DIFF = [min(1.0, max(0.0, random.gauss(0.42, 0.15))) for _ in range(9_600)]


def evaluate(high, low):
    tp = sum(1 for s in SAME if s >= high)
    fp = sum(1 for s in DIFF if s >= high)
    fn = sum(1 for s in SAME if s < low)
    review = sum(1 for s in SAME + DIFF if low <= s < high)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / len(SAME)
    return prec, rec, fp, fn, review


def main():
    print(f"같은 쌍 {len(SAME)}개, 다른 쌍 {len(DIFF):,}개\n")
    print(f"{'자동임계':>7} {'검토하한':>8} {'정밀도':>7} {'재현율':>7} "
          f"{'오병합':>7} {'놓침':>7} {'사람검토':>9}")
    print("-" * 62)
    for high, low in ((0.95, 0.80), (0.90, 0.70), (0.85, 0.55),
                      (0.75, 0.55), (0.65, 0.50), (0.55, 0.50)):
        p, r, fp, fn, rv = evaluate(high, low)
        print(f"{high:>7.2f} {low:>8.2f} {p:>7.3f} {r:>7.3f} "
              f"{fp:>7,} {fn:>7,} {rv:>9,}")

    print(
        "\n임계를 낮출수록 자동으로 더 많이 병합하고, 오병합이 는다.\n"
        "임계를 올릴수록 안전한데 사람이 볼 게 는다.\n"
        "\n어디를 고를까. «오병합 하나의 값»과 «사람 한 건 검토 비용»을 비교하면 된다.\n"
        "\n제 경우를 숫자로 적으면 이랬다.\n"
        "  사람 한 건 검토: 약 40초, 인건비로 환산해 400원\n"
        "  오병합 하나 수습: 평균 2시간 (원인 파악 + 되돌리기 + 영향 받은 질의 확인)\n"
        "  → 오병합 하나가 검토 180건과 맞먹는다\n"
        "\n그래서 저는 임계를 높게 잡습니다. 사람이 많이 보더라도요.\n"
        "다만 이건 «되돌리기가 비싼» 경우다. 되돌리기가 싸면 계산이 달라진다.\n"
        "앞 예제처럼 unmerge 가 대입 한 번이면 오병합 값이 2시간에서 5분이 된다."
    )


if __name__ == "__main__":
    main()
