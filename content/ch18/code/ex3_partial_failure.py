"""
예제 3 — 병렬로 돌린 것 중 하나만 실패하면 어떻게 하나.

    python3 ex3_partial_failure.py

의존성 없음. 체인에는 이 질문에 답할 자리가 없다.
"""

TASKS = [
    ("재무 자료 조회", True,  "매출 84.2억"),
    ("법무 검토",      False, None),
    ("영업 이력 조회",  True,  "계약 12건"),
    ("리스크 평가",     True,  "중간"),
]


def strategy_all_or_nothing(tasks):
    if all(ok for _, ok, _ in tasks):
        return "완료", {n: v for n, _, v in tasks}
    return "실패", None


def strategy_best_effort(tasks):
    return "부분 완료", {n: v for n, ok, v in tasks if ok}


def strategy_degrade(tasks):
    out = {}
    missing = []
    for n, ok, v in tasks:
        if ok:
            out[n] = v
        else:
            out[n] = "확인 불가"
            missing.append(n)
    return f"완료 (미확인 {len(missing)}건)", out


def show(name, status, data):
    print(f"\n[{name}] → {status}")
    if data is None:
        print("    (결과 없음)")
        return
    for k, v in data.items():
        print(f"    {k:<14} {v}")


def main():
    print("작업 4개를 병렬로 돌렸는데 하나가 실패했다.")
    for n, ok, _ in TASKS:
        print(f"    {n:<14} {'성공' if ok else '실패'}")

    show("전부 아니면 없음", *strategy_all_or_nothing(TASKS))
    show("되는 것만", *strategy_best_effort(TASKS))
    show("빈칸을 표시하고 진행", *strategy_degrade(TASKS))

    print(
        "\n셋 다 맞는 답이다. 상황이 정한다.\n"
        "  전부 아니면 없음 — 결재 서류처럼 «불완전하면 안 되는» 산출물\n"
        "  되는 것만       — 대시보드처럼 «있는 만큼 보여 주면 되는» 것\n"
        "  빈칸 표시       — 보고서처럼 «무엇이 빠졌는지 보여야 하는» 것\n"
        "\n세 번째가 대개 제일 낫다. 그런데 제일 안 쓰인다.\n"
        "«확인 불가»를 화면에 그리는 일이 귀찮아서다.\n"
        "\n체인에는 이 선택을 표현할 자리가 없다. 실패하면 예외가 위로 던져지고 끝이다.\n"
        "상태 그래프에서는 «합류 노드»가 이 결정을 맡는다.\n"
        "부분 실패를 어떻게 다룰지가 노드 하나의 책임이 되는 것이다."
    )


if __name__ == "__main__":
    main()
