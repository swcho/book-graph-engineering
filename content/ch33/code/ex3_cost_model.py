"""
예제 3 — 비용은 쿼리에서만 나지 않는다.

    python3 ex3_cost_model.py

의존성 없음. 그래프 시스템의 월 비용을 항목별로 쪼갠다.
대부분의 팀이 «쿼리 튜닝»을 하는데, 청구서의 큰 칸은 대개 다른 곳이다.
"""

KRW = 1_380

# 월 호출 수 · 1회 지연 · 1회 입력 토큰
WORKLOAD = {
    "그래프 조회":     dict(calls=360_000_000, ms=2.4,  tokens=0),
    "벡터 검색":       dict(calls=230_000_000, ms=8.0,  tokens=0),
    "모델 호출(판단)":  dict(calls=1_400_000,   ms=1800, tokens=6_200),
    "모델 호출(추출)":  dict(calls=180_000,     ms=2400, tokens=11_000),
    "체크포인트 쓰기":  dict(calls=540_000_000, ms=4.2,  tokens=0),
    "이벤트 로그 쓰기": dict(calls=540_000_000, ms=0.9,  tokens=0),
}

# 단가
CPU_KRW_PER_CORE_HOUR = 62
TOKEN_KRW_PER_1K = 3.0 / 1000 * KRW      # 입력 기준
STORAGE_KRW_PER_GB_MONTH = 33
HOURS = 24 * 30


def cpu_cores(calls, ms):
    """월 calls 회 × ms 밀리초를 처리하려면 평균 코어가 몇 개 필요한가."""
    return calls * ms / 1000.0 / (HOURS * 3600)


def main():
    print("월 비용을 항목별로 쪼갠다. 하루 종일 이 부하가 돈다고 가정.\n")
    print(f"{'항목':<18}{'월 호출':>15}{'1회 ms':>9}{'코어':>7}"
          f"{'월 인프라':>13}{'월 토큰':>15}{'합계':>15}")
    print("-" * 94)
    total = 0
    rows = []
    for name, w in WORKLOAD.items():
        cores = cpu_cores(w["calls"], w["ms"])
        infra = cores * CPU_KRW_PER_CORE_HOUR * HOURS
        tok = w["calls"] * w["tokens"] / 1000 * TOKEN_KRW_PER_1K
        s = infra + tok
        total += s
        rows.append((name, s))
        print(f"{name:<18}{w['calls']:>15,}{w['ms']:>9.1f}{cores:>7.1f}"
              f"{infra:>12,.0f}원{tok:>14,.0f}원{s:>14,.0f}원")

    print(f"\n{'합계':<18}{'':<31}{total:>55,.0f}원")

    print("\n항목별 비중:\n")
    for name, s in sorted(rows, key=lambda r: -r[1]):
        bar = "█" * int(s / total * 50)
        print(f"  {name:<18}{s / total:>6.1%}  {bar}")

    print(
        "\n그래프 조회가 월 3억 6천만 회로 제일 많이 도는데 비중은 아주 작다.\n"
        "모델 호출은 월 158만 회뿐인데(전체 호출의 0.1%도 안 된다) 비중이 압도적이다.\n"
        "\n그래서 «쿼리를 2ms 에서 1ms 로 줄이는» 튜닝은 청구서를 거의 안 바꾼다.\n"
        "1ms 를 줄여도 전체의 몇 %p 다.\n"
        "\n비용을 줄이려면 «모델 호출 횟수»나 «호출당 토큰»을 줄여야 한다.\n"
        "24장의 컨텍스트 얘기가 여기서 돈으로 돌아온다.\n"
        "\n그렇다고 쿼리 튜닝이 쓸모없다는 건 아니다. 다만 목적이 다르다.\n"
        "  쿼리 튜닝  → «지연»을 줄인다. 사용자가 기다리는 시간\n"
        "  토큰 줄이기 → «비용»을 줄인다. 청구서\n"
        "\n둘을 헷갈리면 엉뚱한 데 시간을 쓴다.\n"
        "느리다고 불평이 오면 쿼리를 보고, 청구서가 아프면 토큰을 본다.\n"
        "\n한 가지 예외가 있다. 체크포인트 쓰기가 월 5억 4천만 회로 도는데,\n"
        "이게 늘어나면 인프라 비중이 확 커진다. 21장에서 잰 그 값이다.\n"
        "그리고 이건 «쿼리»가 아니라 «구조»를 고쳐야 준다. 슈퍼스텝을 줄이는 것이다."
    )


if __name__ == "__main__":
    main()
