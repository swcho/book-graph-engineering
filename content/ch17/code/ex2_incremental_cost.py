"""
예제 2 — GraphRAG 계열의 진짜 비용은 색인이 아니라 «갱신»이다.

    python3 ex2_incremental_cost.py

의존성 없음.
"""

PRICE_PER_MTOK = 4_000        # 원. 2026년 8월 기준 대략치
TOK_PER_DOC_EXTRACT = 1_800   # 문서 하나 엔티티 추출
TOK_PER_SUMMARY = 2_400       # 커뮤니티 요약 하나


def initial(n_docs, n_comm):
    return n_docs * TOK_PER_DOC_EXTRACT + n_comm * TOK_PER_SUMMARY


def daily(n_new, n_comm, affected_ratio, mode):
    """mode: full(전체 재색인) / incremental(바뀐 커뮤니티만)"""
    extract = n_new * TOK_PER_DOC_EXTRACT
    if mode == "full":
        return extract + n_comm * TOK_PER_SUMMARY
    return extract + int(n_comm * affected_ratio) * TOK_PER_SUMMARY


def won(tok):
    return tok / 1_000_000 * PRICE_PER_MTOK


def main():
    N_DOCS, N_COMM = 40_000, 620
    init = initial(N_DOCS, N_COMM)
    print(f"문서 {N_DOCS:,}건, 커뮤니티 {N_COMM}개")
    print(f"첫 색인: {init/1e6:.1f}M 토큰  ≈ {won(init):,.0f}원\n")

    print(f"{'하루 신규':>8} {'영향 커뮤니티':>12} "
          f"{'전체 재색인/일':>16} {'증분/일':>14} {'월 차액':>14}")
    print("-" * 70)
    for n_new, ratio in ((200, 0.03), (200, 0.15), (200, 0.60), (2000, 0.15)):
        f = daily(n_new, N_COMM, ratio, "full")
        i = daily(n_new, N_COMM, ratio, "incremental")
        print(f"{n_new:>8,} {ratio*100:>11.0f}% "
              f"{won(f):>15,.0f}원 {won(i):>13,.0f}원 "
              f"{won(f-i)*30:>13,.0f}원")

    print(
        "\n«영향 커뮤니티 비율»이 전부를 정한다.\n"
        "3% 면 증분이 압도적으로 싸고, 60% 면 전체 재색인과 별 차이가 없다.\n"
        "\n그럼 이 비율이 얼마인지 어떻게 아나. 재 봐야 안다.\n"
        "그리고 재 보면 대개 «생각보다 크다». 커뮤니티 탐지는 전역 계산이라\n"
        "노드 하나가 늘어도 경계가 여기저기 흔들리기 때문이다.\n"
        "\n제 경우 처음엔 5% 를 기대했는데 실측이 34% 였다.\n"
        "이유는 새 문서가 «기존 엔티티를 새로 이어 주는» 다리 역할을 해서였다.\n"
        "장애 회고 문서는 특히 그렇다. 여러 서비스를 한 문서에서 언급하니까.\n"
        "\n대처법 두 가지.\n"
        "  1. 커뮤니티를 «고정»한다. 한 번 정한 경계를 새 노드가 못 바꾸게.\n"
        "     싸지는데 시간이 지날수록 커뮤니티 품질이 나빠진다.\n"
        "  2. 요약을 계층으로 만든다. 하위 요약만 고치고 상위는 덜 자주 다시 쓴다.\n"
        "저는 1번을 쓰고 분기에 한 번 전체 재계산을 돌린다."
    )


if __name__ == "__main__":
    main()
