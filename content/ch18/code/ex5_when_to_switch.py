"""
예제 5 — 언제 갈아탈까. 체인을 유지하는 값과 그래프로 가는 값을 견줘 본다.

    python3 ex5_when_to_switch.py

의존성 없음.
"""

# 체인에 조건을 하나씩 더할 때 드는 «이해 비용»과 «버그 비용»
def chain_complexity(n_conditions):
    paths = 2 ** n_conditions
    untested = max(0, paths - 8)          # 사람이 실제로 테스트하는 건 여덟 가지쯤
    return paths, untested


def graph_complexity(n_conditions):
    # 노드 수는 선형으로 늘고, 개념 학습 비용이 처음에 한 번 붙는다
    return n_conditions * 2 + 3, 0


LEARN_COST_DAYS = 2.0          # 상태 그래프 개념·도구를 익히는 데 드는 시간
BUG_COST_DAYS = 0.5            # 안 테스트된 경로 하나가 언젠가 만드는 비용의 기댓값
BUG_RATE = 0.08                # 안 테스트된 경로가 실제로 터질 확률


def main():
    print(f"{'조건 수':>7} {'체인 경로':>10} {'미검증':>8} "
          f"{'체인 예상 손실(일)':>18} {'그래프 총비용(일)':>18} {'유리한 쪽'}")
    print("-" * 78)
    for n in range(1, 9):
        paths, untested = chain_complexity(n)
        nodes, _ = graph_complexity(n)
        chain_loss = untested * BUG_RATE * BUG_COST_DAYS
        graph_cost = LEARN_COST_DAYS + nodes * 0.05
        better = "체인" if chain_loss < graph_cost else "그래프"
        print(f"{n:>7} {paths:>10,} {untested:>8,} "
              f"{chain_loss:>18.1f} {graph_cost:>18.1f} {better:>10}")

    print(
        "\n갈아타는 지점이 조건 6~7개 사이에 나온다.\n"
        "그 전에는 체인이 싸다. 개념이 적고 코드가 짧으니까.\n"
        "\n이 계산의 전제 셋을 밝혀 둔다. 여러분 값으로 바꿔서 다시 계산해 보시라.\n"
        "  - 상태 그래프 학습 비용 2일 — 팀이 이미 안다면 0\n"
        "  - 미검증 경로가 터질 확률 8% — 도메인마다 다르다\n"
        "  - 버그 하나에 0.5일 — 되돌리기 어려운 작업이면 훨씬 크다\n"
        "\n특히 세 번째가 크면 갈아타는 지점이 확 앞으로 온다.\n"
        "결제나 삭제처럼 되돌리기 힘든 일을 다루면 조건 두세 개에서도 그래프가 낫다.\n"
        "\n반대로 «틀려도 사람이 다시 누르면 그만»인 일이면 조건 여덟 개까지 체인으로 버틸 만하다."
    )


if __name__ == "__main__":
    main()
