"""
예제 4 — 이벤트를 어떻게 «접느냐»가 답을 정한다.

    python3 ex4_reducer_conflict.py

의존성 없음. 같은 이벤트 열에 리듀서 네 개를 적용한다.
19장의 리듀서가 여기서 «이력 접기»로 돌아온다.
"""

EVENTS = [
    ("2026-04-01T09:00", "hr-sync",    "선호", "채식",   "추가", 0.95),
    ("2026-04-03T14:20", "agent-4821", "선호", "육식",   "추가", 0.61),
    ("2026-04-03T14:21", "agent-4821", "선호", "채식",   "삭제", 0.61),
    ("2026-04-09T10:05", "user",       "선호", "채식",   "추가", 1.00),
    ("2026-04-22T16:40", "agent-5102", "선호", "비건",   "추가", 0.78),
]


def last_write_wins(evs):
    st = {}
    for at, who, k, v, op, conf in evs:
        if op == "추가":
            st[k] = (v, at, who)
        else:
            st.pop(k, None)
    return st


def highest_confidence(evs):
    best = {}
    for at, who, k, v, op, conf in evs:
        if op != "추가":
            continue
        if k not in best or conf > best[k][3]:
            best[k] = (v, at, who, conf)
    return {k: (v, at, who) for k, (v, at, who, _c) in best.items()}


def human_wins(evs):
    st = {}
    rank = {"user": 3, "hr-sync": 2}
    for at, who, k, v, op, conf in evs:
        r = rank.get(who, 1)
        if op == "삭제":
            if k in st and st[k][3] <= r:
                st.pop(k)
            continue
        if k not in st or r >= st[k][3]:
            st[k] = (v, at, who, r)
    return {k: (v, at, who) for k, (v, at, who, _r) in st.items()}


def accumulate(evs):
    """지우지 않고 전부 모아 둔다. 충돌은 «답이 여럿»으로 남긴다."""
    st = {}
    for at, who, k, v, op, conf in evs:
        st.setdefault(k, set())
        if op == "추가":
            st[k].add(v)
        else:
            st[k].discard(v)
    return {k: (" / ".join(sorted(v)), "-", "-") for k, v in st.items()}


def main():
    print("이벤트 5건. 사람과 에이전트가 번갈아 「선호」를 고쳤다.\n")
    for at, who, k, v, op, conf in EVENTS:
        print(f"  {at}  {who:<12}{k} = {v:<6}({op}, 확신 {conf:.2f})")

    print(f"\n{'리듀서':<20}{'결과':<22}{'누가 넣은 것':<14}{'언제'}")
    print("-" * 74)
    for name, fn in (("마지막이 이긴다", last_write_wins),
                     ("확신도가 이긴다", highest_confidence),
                     ("사람이 이긴다", human_wins),
                     ("전부 모은다", accumulate)):
        st = fn(EVENTS)
        for k, (v, at, who) in st.items():
            print(f"{name:<20}{k}={v:<20}{who:<14}{at}")

    print(
        "\n같은 이벤트 열인데 답이 넷이다. 리듀서가 답을 정한다.\n"
        "\n«마지막이 이긴다»는 제일 흔하고 제일 위험하다.\n"
        "에이전트가 마지막에 쓰면 사람이 명시한 것을 덮는다.\n"
        "여기서는 4월 9일에 사람이 「채식」이라고 했는데 22일에 에이전트가 「비건」으로 바꿨다.\n"
        "\n«확신도가 이긴다»는 사람 발화(1.00)를 존중한다. 그럴듯하다.\n"
        "그런데 확신도는 에이전트가 «스스로 매기는» 값이다.\n"
        "20장에서 본 「모델이 스스로 올릴 수 있는 값은 지표로 못 쓴다」가 여기도 적용된다.\n"
        "\n«사람이 이긴다»는 출처에 등급을 매긴다. 저는 이걸 기본으로 쓴다.\n"
        "확신도와 달리 등급은 «시스템이» 정하는 값이라 에이전트가 못 올린다.\n"
        "\n«전부 모은다»는 충돌을 숨기지 않는다. 대신 답이 여럿이라 조회하는 쪽이 곤란해진다.\n"
        "다만 «충돌이 있다»는 사실 자체가 중요한 도메인에서는 이게 맞다.\n"
        "\n요점은 이것이다. 이벤트를 쌓는 것만으로는 아무것도 안 정해진다.\n"
        "«어떻게 접을 것인가»가 실제 동작을 정하고, 그건 도메인 결정이다."
    )


if __name__ == "__main__":
    main()
