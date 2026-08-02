"""
예제 1 — 실패했을 때 무엇을 버리는가. 체인과 그래프의 차이는 여기서 갈린다.

    python3 ex1_chain_vs_graph.py

의존성 없음. 기대값으로 계산한다. 시뮬레이션은 시드에 흔들려서
«얼마나 아끼나»를 보기 어렵다.
"""

from steps import STEPS, cost

MAX_ATTEMPTS = 6


def expected_chain(fail_probs):
    """체인 — 어느 단계에서 실패하든 처음부터. 한 «회차»의 기대 비용을 구하고
    성공할 때까지 반복한다."""
    p_all_ok = 1.0
    for p in fail_probs:
        p_all_ok *= (1 - p)
    # 한 회차에 쓰는 기대 시간·토큰 (실패 지점까지만 쓴다)
    t = tok = 0.0
    reach = 1.0
    for (name, secs, tokens, _), p in zip(STEPS, fail_probs):
        t += reach * secs
        tok += reach * tokens
        reach *= (1 - p)
    n_rounds = 1 / p_all_ok if p_all_ok > 0 else float("inf")
    return t * n_rounds, tok * n_rounds


def expected_graph(fail_probs):
    """상태 그래프 — 실패한 단계만 다시. 단계별로 독립적으로 기대 횟수를 센다."""
    t = tok = 0.0
    for (name, secs, tokens, _), p in zip(STEPS, fail_probs):
        tries = 1 / (1 - p) if p < 1 else MAX_ATTEMPTS
        t += secs * tries
        tok += tokens * tries
    return t, tok


def main():
    base = [f for _, _, _, f in STEPS]
    one_shot_t = sum(s for _, s, _, _ in STEPS)
    one_shot_tok = sum(k for _, _, k, _ in STEPS)
    print(f"단계 {len(STEPS)}개. 한 번에 성공하면 "
          f"{one_shot_t}초 / {cost(one_shot_tok):,.0f}원\n")

    print(f"{'마지막 단계 실패율':>16} {'체인 초':>9} {'체인 원':>9} "
          f"{'그래프 초':>10} {'그래프 원':>10} {'시간 절약':>9} {'값 절약':>8}")
    print("-" * 78)
    for p_last in (0.05, 0.10, 0.20, 0.35, 0.50):
        probs = base[:-1] + [p_last]
        ct, ctok = expected_chain(probs)
        gt, gtok = expected_graph(probs)
        print(f"{p_last*100:>15.0f}% {ct:>9.0f} {cost(ctok):>8,.0f}원 "
              f"{gt:>10.0f} {cost(gtok):>9,.0f}원 "
              f"{(1-gt/ct)*100:>8.0f}% {(1-gtok/ctok)*100:>7.0f}%")

    print()
    print(f"{'단계 수':>8} {'체인 초':>9} {'그래프 초':>10} {'시간 절약':>9}")
    print("-" * 40)
    for n in (2, 4, 6, 8, 12):
        probs = [0.12] * n
        global STEPS_BACKUP
        saved = list(STEPS)
        STEPS.clear()
        STEPS.extend([(f"s{i}", 15, 5_000, 0.12) for i in range(n)])
        ct, _ = expected_chain(probs)
        gt, _ = expected_graph(probs)
        STEPS.clear(); STEPS.extend(saved)
        print(f"{n:>8} {ct:>9.0f} {gt:>10.0f} {(1-gt/ct)*100:>8.0f}%")

    print(
        "\n차이는 알고리즘이 아니라 «무엇을 버리는가»에서 나온다.\n"
        "체인은 3단계에서 실패하면 1·2단계 결과를 버린다. 이미 낸 값인데도.\n"
        "그래프는 3단계만 다시 한다. 앞의 결과가 체크포인트에 있으니까.\n"
        "\n두 표가 보여 주는 게 다르다.\n"
        "  위 — 뒤쪽 단계가 자주 실패할수록 격차가 벌어진다\n"
        "  아래 — 단계가 많을수록 격차가 벌어진다\n"
        "\n뒤집으면 이렇다. 단계가 두세 개고 실패가 드물면 체인으로 충분하다.\n"
        "그리고 대부분의 시스템이 거기서 시작한다. 시작은 그게 맞다."
    )


if __name__ == "__main__":
    main()
