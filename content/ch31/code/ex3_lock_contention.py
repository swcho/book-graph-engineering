"""
예제 3 — 낙관적 잠금과 비관적 잠금, 어디서 뒤집히나.

    python3 ex3_lock_contention.py

의존성 없음. 충돌률을 바꿔 가며 두 방식의 처리량을 비교한다.
「낙관적이 좋다」는 조건부 참이다.
"""

HOLD_MS = 12.0        # 판단하는 시간 (읽고 나서 쓰기까지)
WRITE_MS = 1.5
LOCK_ACQUIRE_MS = 2.2   # 잠금을 «잡고 푸는» 값. 충돌이 없어도 매번 든다
N_OPS = 1000


def _expected_tries(p):
    """기대 시도 횟수 = 1/(1-p)"""
    return 1.0 / (1.0 - p) if p < 1 else 99


def optimistic_expected(p, max_tries=6):
    e = min(_expected_tries(p), max_tries)
    return N_OPS * e * (HOLD_MS + WRITE_MS), 0


def pessimistic(p_conflict):
    """잠그고 시작한다.
    - 잠금 자체를 잡고 푸는 값이 «매번» 든다
    - 충돌하면 앞사람이 끝날 때까지 기다린다. 대기열이 길수록 더 기다린다
    """
    total_ms = N_OPS * (HOLD_MS + WRITE_MS + LOCK_ACQUIRE_MS)
    if p_conflict < 1:
        # 대기 시간은 이용률이 오를수록 급격히 는다 (M/M/1 근사)
        queue = (p_conflict / (1 - p_conflict)) * (HOLD_MS + WRITE_MS)
    else:
        queue = 99 * (HOLD_MS + WRITE_MS)
    total_ms += N_OPS * p_conflict * queue
    return total_ms, 0


def main():
    print(f"판단 {HOLD_MS}ms, 쓰기 {WRITE_MS}ms, "
          f"잠금 획득 {LOCK_ACQUIRE_MS}ms, 연산 {N_OPS}회\n")
    print(f"{'충돌률':>8}{'낙관적(ms)':>14}{'기대 시도':>10}"
          f"{'비관적(ms)':>14}{'어느 쪽이 빠른가':>18}")
    print("-" * 68)
    for p in (0.01, 0.05, 0.15, 0.30, 0.50, 0.70):
        o, _ = optimistic_expected(p)
        pe, _ = pessimistic(p)
        e = min(_expected_tries(p), 6)
        win = "낙관적" if o < pe else "비관적"
        margin = abs(o - pe) / max(o, pe)
        mark = "" if margin > 0.05 else "  (비슷)"
        print(f"{p:>7.0%}{o:>14,.0f}{e:>10.2f}{pe:>14,.0f}{win:>18}{mark}")

    print(
        "\n15%와 30% 사이에서 뒤집힌다.\n"
        "낙관적은 충돌이 드물 때 이긴다. 막는 값을 안 내니까.\n"
        "충돌이 잦아지면 재시도가 쌓여서 뒤집힌다.\n"
        "\n뒤집히는 지점을 계산으로 구할 수 있다.\n"
        "  낙관적 = N × (1/(1-p)) × (판단+쓰기)\n"
        "  비관적 = N × (판단+쓰기+잠금획득) + N × p × 대기\n"
        "\n비관적은 충돌이 «없어도» 잠금 획득 값을 매번 낸다. 그게 왼쪽 구간의 손해다.\n"
        "낙관적은 충돌이 «잦아지면» 재시도 값이 곱해진다. 그게 오른쪽 구간의 손해다.\n"
        "\n판단 시간이 길수록 낙관적이 불리하다. 재시도할 때 판단을 다시 하니까.\n"
        "그래서 «에이전트가 모델을 부르는» 구간이 잠금 안에 있으면 최악이다.\n"
        "재시도 한 번에 모델 호출 한 번이 통째로 다시 든다.\n"
        "\n실무 요령 하나. 판단을 잠금 «밖»으로 빼면 둘 다 좋아진다.\n"
        "  1. 읽는다 (잠금 없이)\n"
        "  2. 모델을 부른다 (잠금 없이 — 여기가 제일 길다)\n"
        "  3. 짧게 잠그고 «버전 확인 + 쓰기»만 한다\n"
        "\n그러면 잠금을 붙드는 시간이 12ms 에서 1.5ms 로 준다.\n"
        "충돌률도 같이 떨어진다. 창이 좁아지니까."
    )


if __name__ == "__main__":
    main()
