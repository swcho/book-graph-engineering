"""
예제 2 — 진전을 무엇으로 잴 것인가. 이게 제일 어렵다.

    python3 ex2_stall_detection.py

의존성 없음.
"""

# 같은 루프를 세 가지 척도로 재 본다
ROUNDS = [
    # (위반 건수, 산출물 길이, 모델이 매긴 확신도)
    (9, 320, 0.55),
    (6, 480, 0.61),
    (4, 610, 0.68),
    (4, 890, 0.74),      # 위반은 그대로인데 길이와 확신도는 올랐다
    (4, 1240, 0.79),
    (3, 1610, 0.83),
]

METRICS = {
    "위반 건수 (낮을수록 좋다)": (lambda r: r[0], False),
    "산출물 길이 (길수록 좋다?)": (lambda r: r[1], True),
    "모델 확신도 (높을수록 좋다)": (lambda r: r[2], True),
}


def stalled_at(values, higher_better, limit=2):
    """limit 번 연속 나아지지 않으면 그 회차를 돌려준다."""
    for i in range(limit + 1, len(values) + 1):
        window = values[i - limit - 1:i]
        best_before = max(window[:-1]) if higher_better else min(window[:-1])
        worse = window[-1] <= best_before if higher_better else window[-1] >= best_before
        if worse:
            return i
    return None


def main():
    print(f"{'회차':>4} {'위반':>6} {'길이':>7} {'확신도':>8}")
    print("-" * 30)
    for i, r in enumerate(ROUNDS, 1):
        print(f"{i:>4} {r[0]:>6} {r[1]:>7} {r[2]:>8.2f}")

    print(f"\n{'척도':<26} {'멈추는 회차':>10} {'그때 위반':>9}")
    print("-" * 50)
    for name, (get, higher) in METRICS.items():
        vals = [get(r) for r in ROUNDS]
        at = stalled_at(vals, higher)
        v = ROUNDS[at - 1][0] if at else ROUNDS[-1][0]
        print(f"{name:<26} {str(at) if at else '안 멈춤':>10} {v:>9}")

    print(
        "\n같은 루프인데 척도에 따라 멈추는 시점이 다르다.\n"
        "\n«산출물 길이»는 영원히 안 멈춘다. 계속 길어지니까.\n"
        "그런데 길어지는 게 나아지는 건 아니다. 위반은 4에서 안 줄었다.\n"
        "\n«모델 확신도»도 계속 오른다. 15장에서 봤듯 자기 보고는 믿을 게 못 된다.\n"
        "\n«위반 건수»만 4회차에서 정체를 잡는다. 규칙으로 세는 값이라 안 흔들린다.\n"
        "\n진전 척도를 고르는 기준 하나. «모델이 스스로 올릴 수 있는 값이면 안 된다.»\n"
        "길이도 확신도도 모델이 마음대로 올릴 수 있다. 위반 건수는 못 올린다."
    )


if __name__ == "__main__":
    main()
