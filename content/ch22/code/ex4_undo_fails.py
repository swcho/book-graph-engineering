"""
예제 4 — 되갚기가 실패하면 어떻게 하나.

    python3 ex4_undo_fails.py

의존성 없음. 환불 API 가 죽어 있을 때 세 가지 대응을 비교한다.
"""

import random

CALLS = {"환불": 0}
REFUND_FAIL_UNTIL = 3      # 세 번째 호출까지는 실패한다


def refund():
    CALLS["환불"] += 1
    if CALLS["환불"] <= REFUND_FAIL_UNTIL:
        raise ConnectionError("환불 API 503")
    return "환불 완료"


def strategy_naive():
    """한 번 해 보고 안 되면 로그만 찍는다."""
    try:
        refund()
        return "복구됨", 1
    except ConnectionError:
        return "돈이 묶임 — 로그만 남음", 1


def strategy_retry(max_tries=3):
    """되갚기도 재시도한다. 다만 상한이 있다."""
    for i in range(1, max_tries + 1):
        try:
            refund()
            return "복구됨", i
        except ConnectionError:
            continue
    return "돈이 묶임 — 재시도 소진", max_tries


def strategy_dlq(max_tries=3):
    """상한까지 재시도하고, 안 되면 «되갚기 대기열»에 넣는다."""
    for i in range(1, max_tries + 1):
        try:
            refund()
            return "복구됨", i
        except ConnectionError:
            continue
    # 여기서 끝내지 않는다. 나중에 다시 꺼내 쓸 수 있게 적어 둔다.
    queued = {"작업": "환불", "주문": "A-1024", "금액": 50_000, "시도": max_tries}
    later = None
    for i in range(max_tries + 1, max_tries + 4):     # 대기열 소비자가 나중에 다시
        try:
            refund()
            later = i
            break
        except ConnectionError:
            continue
    if later:
        return f"대기열에서 {later}번째 시도에 복구됨", later
    return f"대기열에 남음 {queued}", max_tries


def main():
    print(f"환불 API 가 {REFUND_FAIL_UNTIL}번째 호출까지 503 을 돌려준다.\n")
    print(f"{'대응':<26}{'결과':<34}{'호출 수':>8}")
    print("-" * 70)
    for name, fn in (("한 번 해 보고 포기", strategy_naive),
                     ("상한까지 재시도", strategy_retry),
                     ("재시도 + 되갚기 대기열", strategy_dlq)):
        CALLS["환불"] = 0
        res, n = fn()
        print(f"{name:<26}{res:<34}{n:>8}")

    print(
        "\n두 번째가 헷갈리는 대목이다. 재시도를 3번 했는데도 실패로 끝난다.\n"
        "상한을 5로 올리면 되지 않나 싶지만, 그건 이번 장애 길이에만 맞춘 숫자다.\n"
        "다음 장애가 10분이면 또 실패한다.\n"
        "\n세 번째는 상한을 안 늘린다. 대신 «포기하지도 않는다».\n"
        "3번 실패하면 되갚기 작업을 대기열에 적어 두고 지금 흐름은 끝낸다.\n"
        "대기열 소비자가 나중에 다시 꺼내서 시도한다.\n"
        "\n요점은 이것이다. 되갚기는 «지금 성공해야 하는 일»이 아니라\n"
        "«언젠가 반드시 성공해야 하는 일»이다. 그 둘은 설계가 다르다.\n"
        "\n그리고 되갚기 대기열은 반드시 «누가 보는지»가 정해져 있어야 한다.\n"
        "쌓이기만 하고 아무도 안 보는 큐는 로그와 똑같다."
    )


if __name__ == "__main__":
    main()
