"""
예제 2 — 병렬로 펴면 언제 이득이고 언제 손해인가.

    python3 ex2_fanout.py

의존성 없음. 합류(fan-in) 값과 실패율을 넣으면
«펴는 게 이득인 구간»이 생각보다 좁다는 게 보인다.
"""

TASK_MS = 900          # 갈래 하나 처리 시간
MERGE_PER_BRANCH = 140 # 합류할 때 갈래당 드는 시간 (정리·중복 제거)
FAIL = 0.06            # 갈래 하나가 실패할 확률
RETRY_MS = TASK_MS     # 실패하면 한 번 더
SLOW_P = 0.10          # 갈래 하나가 «느린 놈»일 확률
SLOW_X = 3.5           # 느린 놈은 이만큼 더 걸린다


def serial(n):
    ms = n * TASK_MS
    ms += n * FAIL * RETRY_MS
    return ms, 0


def wave_ms(width):
    """한 물결은 «제일 느린 갈래»가 끝나야 끝난다."""
    p_any_slow = 1 - (1 - SLOW_P) ** width
    base = TASK_MS * (1 + p_any_slow * (SLOW_X - 1))
    p_any_fail = 1 - (1 - FAIL) ** width
    return base + p_any_fail * RETRY_MS


def parallel(n, width):
    waves = -(-n // width)
    ms = waves * wave_ms(width)
    merge = n * MERGE_PER_BRANCH
    return ms + merge, merge


def main():
    print(f"갈래 하나 {TASK_MS}ms, 합류 정리 갈래당 {MERGE_PER_BRANCH}ms, "
          f"갈래 실패율 {FAIL:.0%}\n")
    print(f"{'갈래 수':>7}{'직렬(ms)':>12}{'병렬 4폭(ms)':>16}"
          f"{'그중 합류':>12}{'이득':>10}")
    print("-" * 60)
    for n in (2, 4, 8, 16, 32, 64):
        s, _ = serial(n)
        p, merge = parallel(n, 4)
        gain = s / p
        mark = "" if gain > 1.15 else "  ← 별 이득 없음"
        print(f"{n:>7}{s:>12,.0f}{p:>16,.0f}{merge:>12,.0f}{gain:>9.2f}x{mark}")

    print("\n같은 갈래 16개를 폭만 바꿔 가며:\n")
    print(f"{'동시 폭':>7}{'물결 수':>9}{'물결 하나(ms)':>16}{'총 시간(ms)':>14}")
    print("-" * 48)
    for w in (1, 2, 4, 8, 16):
        p, _ = parallel(16, w)
        print(f"{w:>7}{-(-16 // w):>9}{wave_ms(w):>16,.0f}{p:>14,.0f}")

    print(
        "\n첫 표. 갈래 2개짜리는 병렬이 «더 느리다». 0.89배다.\n"
        "펴는 값보다 합류와 꼬리 지연이 더 들기 때문이다.\n"
        "그리고 갈래를 늘려도 이득이 1.57배에서 천장을 친다. 폭이 4인데 4배가 아니다.\n"
        "펴는 값은 나누기(÷폭)인데 합류 값은 갈래 수에 비례해서 안 줄어든다.\n"
        "갈래를 아무리 늘려도 배수가 더 안 오르는 이유가 이것이다.\n"
        "\n둘째 표가 제가 틀렸던 곳이다.\n"
        "«폭을 키우면 하나라도 실패할 확률이 올라서 손해»라고 생각했다. 아니었다.\n"
        "물결 수가 줄어드는 효과가 훨씬 커서, 폭을 키우면 총 시간은 계속 준다.\n"
        "\n대신 «물결 하나» 칸을 보시라. 폭이 커질수록 물결 하나가 길어진다.\n"
        "제일 느린 갈래가 끝나야 물결이 끝나기 때문이다(꼬리 지연).\n"
        "16폭이면 물결 하나가 3,299ms 다. 1폭일 때(1,179ms)의 2.8배다.\n"
        "\n그래서 폭을 키우는 값은 «총 시간»이 아니라 «변동성»으로 치른다.\n"
        "평균은 좋아지는데 최악이 나빠진다. 사용자가 느끼는 건 대개 최악 쪽이다.\n"
        "\n그리고 합류 코드를 «가볍게» 유지하는 게 폭을 키우는 것보다 크게 듣는다.\n"
        "첫 표에서 천장을 만든 게 합류였다. 폭이 아니라.\n"
        "합류에서 전체를 다시 정렬하거나 중복 제거를 O(n²)로 하고 있으면\n"
        "펴는 의미가 사라진다. 실제로 제가 그랬다."
    )


if __name__ == "__main__":
    main()
