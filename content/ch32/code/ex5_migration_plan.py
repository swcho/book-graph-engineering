"""
예제 5 — 마이그레이션 계획을 «검사 가능한 형태»로 적는다.

    python3 ex5_migration_plan.py

의존성 없음. 29장에서 아키텍처를 검사했듯이 마이그레이션도 검사한다.
「지금 몇 단계인가」와 「다음으로 넘어가도 되나」를 코드가 답한다.
"""

PHASES = [
    ("expand",      "새 스키마를 «더한다». 옛것 그대로"),
    ("dual-write",  "쓰기를 양쪽에 한다"),
    ("backfill",    "옛 데이터를 새 스키마로 복사"),
    ("dual-read",   "읽기를 둘 다 하고 비교"),
    ("cutover",     "읽기를 새것으로. 옛것은 검증용"),
    ("contract",    "옛 스키마 삭제"),
]

# 현재 관측값
STATE = {
    "새_스키마_존재": True,
    "양쪽_쓰기_비율": 1.00,
    "백필_진행률": 1.00,
    "불일치_건수": 3,
    "옛것_읽기_건수_최근": 0,
    "가장_긴_주기_일": 92,
    "옛것_마지막_읽기_경과일": 52,
    "롤백_가능": True,
}

GATES = {
    "expand":     [("새 스키마가 있나", lambda s: s["새_스키마_존재"])],
    "dual-write": [("양쪽 쓰기가 100%인가",
                    lambda s: s["양쪽_쓰기_비율"] >= 1.0)],
    "backfill":   [("백필이 끝났나", lambda s: s["백필_진행률"] >= 1.0)],
    "dual-read":  [("불일치가 0인가", lambda s: s["불일치_건수"] == 0)],
    "cutover":    [("옛것 읽기가 0인가",
                    lambda s: s["옛것_읽기_건수_최근"] == 0),
                   ("롤백이 가능한가", lambda s: s["롤백_가능"])],
    "contract":   [("가장 긴 주기보다 오래 조용한가",
                    lambda s: s["옛것_마지막_읽기_경과일"]
                              > s["가장_긴_주기_일"])],
}


def main():
    print("마이그레이션 여섯 단계. 각 단계를 «떠나려면» 통과해야 하는 조건.\n")
    print(f"{'단계':<14}{'하는 일':<32}{'다음으로 갈 조건':<26}{'통과'}")
    print("-" * 86)
    blocked_at = None
    for name, what in PHASES:
        checks = GATES[name]
        oks = [(label, fn(STATE)) for label, fn in checks]
        allok = all(v for _l, v in oks)
        label = " / ".join(l for l, _v in oks)
        mark = "○" if allok else "✗"
        print(f"{name:<14}{what:<32}{label:<26}{mark}")
        if not allok and blocked_at is None:
            blocked_at = name

    print(f"\n지금 막혀 있는 곳: {blocked_at}")
    for l, v in [(l, fn(STATE)) for l, fn in GATES[blocked_at]]:
        if not v:
            print(f"  → {l} : 아니오")

    print("\n관측값:")
    for k, v in STATE.items():
        print(f"  {k:<24}{v}")

    print(
        "\n계획을 문서로 적으면 「지금 어디쯤인가」를 사람이 판단하게 된다.\n"
        "그리고 사람은 「대충 된 것 같은데」로 다음 단계로 넘어간다.\n"
        "\n조건을 코드로 적으면 «넘어갈 수 없다». 불일치 3건이 남아 있으면 막힌다.\n"
        "\n여기 쓴 조건 여섯 개가 전부 앞 예제들에서 나온 것이다.\n"
        "  양쪽 쓰기 100%      — 예제 2의 3단계\n"
        "  불일치 0            — 예제 4의 «둘 다 읽고 비교»\n"
        "  가장 긴 주기        — 예제 3의 분기 결산\n"
        "\n한 가지 더. «롤백 가능»을 조건에 넣은 게 일부러다.\n"
        "cutover 는 되돌리기 제일 어려운 단계라, 그 앞에서 «되돌릴 수 있나»를 묻는다.\n"
        "옛 스키마가 아직 살아 있고 데이터가 최신이면 되돌릴 수 있다.\n"
        "\n이 파일을 CI 에 넣으면 마이그레이션이 «상태 기계»가 된다.\n"
        "그리고 상태 기계는 사람의 낙관을 안 탄다."
    )


if __name__ == "__main__":
    main()
