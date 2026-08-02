"""
예제 5 — 충돌을 감지한 «다음»에 무엇을 할 것인가.

    python3 ex5_merge_strategy.py

의존성 없음. 충돌 다섯 건에 병합 전략 넷을 적용한다.
감지는 기술이고 해결은 도메인이다.
"""

CONFLICTS = [
    # (필드, 원래 값, A 가 쓰려는 것, A 출처, B 가 쓰려는 것, B 출처, 종류)
    ("팀장",   "박민수", "이서연", "hr-sync",    "김도현", "agent-4821", "단일값"),
    ("인원",   "3",     "5",     "batch",      "4",     "agent-5102", "수치"),
    ("태그",   "결제",   "결제,정산", "user",     "결제,신규", "agent-4821", "집합"),
    ("설명",   "이전 설명", "새 설명 A", "user",   "새 설명 B", "user",      "자유문"),
    ("폐쇄일", "",      "2026-06-30", "admin", "",      "agent-5102", "단일값"),
]

RANK = {"user": 4, "admin": 4, "hr-sync": 3, "batch": 2}


def rank(src):
    return RANK.get(src, 1)


def last_wins(f, base, a, sa, b, sb, kind):
    return b, "나중 것"


def source_rank(f, base, a, sa, b, sb, kind):
    if rank(sa) > rank(sb):
        return a, f"{sa} 우선"
    if rank(sb) > rank(sa):
        return b, f"{sb} 우선"
    return None, "등급 같음 → 사람"


def type_aware(f, base, a, sa, b, sb, kind):
    if kind == "집합":
        merged = sorted(set(a.split(",")) | set(b.split(",")))
        return ",".join(merged), "합집합"
    if kind == "수치" and base.isdigit():
        # 양쪽의 «변화량»을 더한다
        d = (int(a) - int(base)) + (int(b) - int(base))
        return str(int(base) + d), "변화량 합산"
    return source_rank(f, base, a, sa, b, sb, kind)


def always_human(f, base, a, sa, b, sb, kind):
    return None, "사람 확인"


def main():
    print("충돌 5건. 원래 값과 양쪽이 쓰려는 값이 다르다.\n")
    print(f"{'필드':<8}{'종류':<8}{'원래':<10}{'A(출처)':<20}{'B(출처)'}")
    print("-" * 70)
    for f, base, a, sa, b, sb, kind in CONFLICTS:
        print(f"{f:<8}{kind:<8}{base or '-':<10}"
              f"{a + ' (' + sa + ')':<20}{b or '-'} ({sb})")

    print()
    for name, fn in (("마지막이 이긴다", last_wins),
                     ("출처 등급", source_rank),
                     ("종류를 보고", type_aware),
                     ("전부 사람에게", always_human)):
        auto = 0
        print(f"\n[{name}]")
        for f, base, a, sa, b, sb, kind in CONFLICTS:
            v, why = fn(f, base, a, sa, b, sb, kind)
            auto += v is not None
            print(f"    {f:<8}{(v if v is not None else '보류'):<14}{why}")
        print(f"    → 자동 해결 {auto}/{len(CONFLICTS)}, "
              f"사람에게 {len(CONFLICTS) - auto}건")

    print(
        "\n«마지막이 이긴다»는 5건을 전부 자동으로 처리한다. 그리고 전부 틀릴 수 있다.\n"
        "팀장을 에이전트가 정하고, 사용자가 쓴 설명을 다른 사용자가 덮는다.\n"
        "\n«출처 등급»은 4건을 처리하고 1건을 남긴다.\n"
        "남는 건 «설명»이다. 둘 다 user 라 등급이 같다. 이건 사람이 봐야 맞다.\n"
        "\n«종류를 보고»가 제일 낫다. 집합은 합치고 수치는 변화량을 더한다.\n"
        "  태그: 결제,정산 + 결제,신규 → 결제,신규,정산\n"
        "  인원: 3 → 5 (+2) 와 3 → 4 (+1) → 6\n"
        "\n«인원»의 결과를 보시라. 6이다. 양쪽 누구도 6을 쓰려고 하지 않았다.\n"
        "그런데 이게 맞을 수도 있다. «두 명 늘었고 한 명 늘었다»면 세 명 는 거니까.\n"
        "틀릴 수도 있다. 둘 다 «같은 사실»을 보고 다르게 센 것이면 6은 틀렸다.\n"
        "\n그래서 변화량 합산은 «독립적인 증분»일 때만 맞다.\n"
        "장바구니 담기, 재고 차감, 좋아요 수 같은 것들이다.\n"
        "«현재 값을 다시 센 결과»에는 쓰면 안 된다.\n"
        "\n결론은 이것이다. 충돌 «감지»는 기술 문제라 일반 해법이 있다.\n"
        "충돌 «해결»은 도메인 문제라 일반 해법이 없다.\n"
        "필드마다 「이건 어떻게 합칠까」를 정해 둬야 하고, 못 정하면 사람에게 보낸다."
    )


if __name__ == "__main__":
    main()
