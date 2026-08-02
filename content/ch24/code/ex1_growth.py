"""
예제 1 — 대화가 길어질 때 토큰이 «얼마나» 느는가.

    python3 ex1_growth.py

의존성 없음. 매 턴 전체 대화를 다시 보내는 구조에서
누적 토큰이 어떻게 자라는지 계산한다.
"""

TURN_IN = 220          # 한 턴에 사용자가 넣는 토큰
TURN_OUT = 380         # 한 턴에 모델이 내놓는 토큰
TOOL_OUT = 1_400       # 도구 결과가 붙는 턴의 추가 토큰
TOOL_EVERY = 3         # 세 턴에 한 번 도구를 부른다

PRICE_IN = 3.0 / 1_000_000    # 달러, 입력 100만 토큰당
PRICE_OUT = 15.0 / 1_000_000  # 달러, 출력 100만 토큰당
KRW = 1_380

WINDOW = 200_000       # 모델이 받아 주는 최대 입력 토큰


def simulate(turns):
    history = 0        # 지금까지 쌓인 대화 길이
    sent_in = 0        # 누적으로 «보낸» 입력 토큰
    sent_out = 0
    rows = []
    for t in range(1, turns + 1):
        history += TURN_IN
        if t % TOOL_EVERY == 0:
            history += TOOL_OUT
        # 매 턴 전체 대화를 다시 보낸다
        sent_in += history
        sent_out += TURN_OUT
        history += TURN_OUT
        if t in (1, 5, 10, 20, 40, 80, 120):
            cost = sent_in * PRICE_IN + sent_out * PRICE_OUT
            rows.append((t, history, sent_in, cost * KRW, history / WINDOW))
    return rows


def main():
    print("매 턴 전체 대화를 다시 보내는 구조. 도구 결과는 세 턴에 한 번 붙는다.\n")
    print(f"{'턴':>5}{'대화 길이':>12}{'누적 입력':>14}{'누적 비용':>12}{'창 사용률':>10}")
    print("-" * 56)
    for t, hist, sent, krw, use in simulate(120):
        print(f"{t:>5}{hist:>12,}{sent:>14,}{krw:>11,.0f}원{use:>9.0%}")

    print(
        "\n대화 길이는 «선형»으로 자란다. 턴마다 비슷한 양이 붙으니까.\n"
        "그런데 누적 입력은 «제곱»으로 자란다. 매 턴 전체를 다시 보내기 때문이다.\n"
        "\n턴이 두 배가 되면 비용은 네 배가 된다. 이게 감이 잘 안 오는 부분이다.\n"
        "20턴에서 괜찮던 비용이 80턴에서 괜찮지 않은 이유가 여기 있다.\n"
        "\n창 사용률도 보시라. 120턴이면 절반을 넘는다.\n"
        "«아직 창이 남았으니 괜찮다»가 아니다. 비용은 창이 차기 훨씬 전에 문제가 된다."
    )


if __name__ == "__main__":
    main()
