"""
예제 5 — 기억을 계층으로 나눈다. 어디에 두느냐로 조회 값이 달라진다.

    python3 ex5_memory_tiers.py

의존성 없음. 계층별 조회 지연과 «맞힐 확률»을 놓고
질문 100개를 처리할 때 총 비용을 계산한다.
"""

TIERS = [
    # 이름            지연(ms)  건당 토큰   이 계층에서 답이 나올 확률
    ("작업 기억",         0.0,      0,      0.55),   # 지금 컨텍스트 안
    ("최근 요약",         1.5,    350,      0.20),   # 이번 세션 요약
    ("에피소드 기억",     18.0,    900,      0.15),   # 지난 세션 기록
    ("지식 그래프",       42.0,    600,      0.08),   # 27장에서 다룬다
    ("없음(모름)",       0.0,      0,      0.02),
]

N_Q = 100
PRICE_IN = 3.0 / 1_000_000
KRW = 1_380


def cascade():
    """위 계층부터 차례로 찾아 내려간다."""
    ms = tok = 0.0
    remaining = 1.0
    rows = []
    for name, lat, t, p in TIERS:
        reached = remaining          # 이 계층까지 «내려온» 질문 비율
        hit = p                      # 이 계층에서 «해결되는» 질문 비율
        ms += reached * N_Q * lat
        tok += reached * N_Q * t
        rows.append((name, reached * N_Q, hit * N_Q, ms, tok))
        remaining -= p
    return rows, ms, tok


def all_at_once():
    """계층을 안 나누고 전부 한 번에 컨텍스트에 넣는다."""
    lat = sum(t[1] for t in TIERS)
    tok = sum(t[2] for t in TIERS)
    return N_Q * lat, N_Q * tok


def main():
    rows, ms, tok = cascade()
    print(f"질문 {N_Q}개. 위 계층부터 차례로 찾아 내려간다.\n")
    print(f"{'계층':<16}{'여기까지 내려온 질문':>20}{'여기서 해결':>12}"
          f"{'누적 지연(ms)':>14}")
    print("-" * 66)
    for name, reached, hit, cms, _ in rows:
        print(f"{name:<16}{reached:>20.0f}{hit:>12.0f}{cms:>14,.0f}")

    ams, atok = all_at_once()
    print(f"\n{'방식':<22}{'총 지연(ms)':>14}{'총 토큰':>12}{'토큰 비용':>12}")
    print("-" * 62)
    print(f"{'계층별로 내려가기':<22}{ms:>14,.0f}{tok:>12,.0f}"
          f"{tok * PRICE_IN * KRW:>11,.0f}원")
    print(f"{'전부 한 번에 넣기':<22}{ams:>14,.0f}{atok:>12,.0f}"
          f"{atok * PRICE_IN * KRW:>11,.0f}원")

    print(
        "\n«전부 한 번에»가 왜 나쁜지가 이 표에 있다.\n"
        "질문의 55%는 지금 컨텍스트 안에서 답이 나온다. 그런데도 매번 다 끌어온다.\n"
        "\n계층으로 나누면 위에서 끝나는 질문은 아래를 안 건드린다.\n"
        "«비싼 조회를 안 하는 것»이 «빠른 조회를 만드는 것»보다 크게 듣는다.\n"
        "\n조심할 지점 하나. 이 계산은 «위 계층이 맞을 때»를 전제한다.\n"
        "작업 기억에 오래된 값이 남아 있으면 잘못된 답으로 55%를 처리한다.\n"
        "그러면 아래 계층은 영영 안 불린다. 틀린 채로 빠르다.\n"
        "\n그래서 계층 설계에서 제일 중요한 건 속도가 아니라 «갱신»이다.\n"
        "위 계층이 낡지 않게 유지하는 비용을 안 세면 이 표는 거짓말이 된다."
    )


if __name__ == "__main__":
    main()
