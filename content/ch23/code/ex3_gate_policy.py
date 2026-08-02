"""
예제 3 — 승인 문턱을 어디에 둘 것인가. 숫자로 정해 본다.

    python3 ex3_gate_policy.py

의존성 없음. 하루치 요청 분포를 놓고 문턱별로
「사람이 볼 건수」와 「그냥 나가는 위험 금액」을 계산한다.
"""

import random

REVIEW_MINUTES = 3        # 한 건 검토에 걸리는 시간
REVIEWERS = 2             # 검토 담당자 수
WORK_MINUTES = 8 * 60     # 하루 근무 시간
ERROR_RATE = 0.04         # 자동 처리 중 잘못된 비율 (실측 가정)


def day(seed=7, n=1200):
    """하루치 환불 요청. 금액은 소액이 많고 고액이 드물다."""
    rng = random.Random(seed)
    return [int(rng.lognormvariate(10.4, 1.15)) for _ in range(n)]


def evaluate(amounts, threshold):
    reviewed = [a for a in amounts if a >= threshold]
    auto = [a for a in amounts if a < threshold]
    load = len(reviewed) * REVIEW_MINUTES
    capacity = REVIEWERS * WORK_MINUTES
    risk = sum(auto) * ERROR_RATE
    return len(reviewed), load, capacity, risk


def main():
    amounts = day()
    print(f"하루 환불 요청 {len(amounts)}건, 합계 {sum(amounts):,}원")
    print(f"검토 한 건 {REVIEW_MINUTES}분, 담당자 {REVIEWERS}명, "
          f"하루 처리 가능 {REVIEWERS * WORK_MINUTES // REVIEW_MINUTES}건\n")

    print(f"{'문턱':>10}{'사람이 볼 건수':>14}{'검토 시간(분)':>14}"
          f"{'용량 대비':>10}{'자동 처리 위험액':>16}")
    print("-" * 66)
    for t in (0, 50_000, 100_000, 300_000, 1_000_000, 10**9):
        n, load, cap, risk = evaluate(amounts, t)
        label = "전부 사람" if t == 0 else ("전부 자동" if t == 10**9 else f"{t:,}원")
        print(f"{label:>10}{n:>14}{load:>14}{load / cap:>9.0%}{risk:>16,.0f}원")

    print(
        "\n«전부 사람»은 검토 시간이 용량의 3배가 넘는다. 실제로는 이렇게 된다.\n"
        "밀린 건이 쌓이고, 담당자가 대충 보기 시작하고, 결국 «전부 자동»과 같아진다.\n"
        "이게 제일 나쁜 결말이다. 사람을 갈아 넣고 효과는 0인 상태.\n"
        "\n«전부 자동»은 위험액이 그대로 노출된다.\n"
        "\n중간 어딘가가 답인데, 고르는 기준은 «용량»이다.\n"
        "검토 시간이 용량의 70%를 넘지 않는 문턱 중 제일 낮은 것을 고른다.\n"
        "30%는 휴가·회의·급한 건을 위해 비워 둔다.\n"
        "\n문턱을 «금액»으로만 잡는 게 최선은 아니다.\n"
        "신규 고객, 반복 환불, 이상 패턴 같은 신호를 섞으면 같은 용량으로 더 잡는다.\n"
        "다만 시작은 금액이 좋다. 계산이 되고, 설명이 되고, 감사도 통과한다."
    )


if __name__ == "__main__":
    main()
