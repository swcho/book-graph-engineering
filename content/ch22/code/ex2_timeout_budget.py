"""
예제 2 — 층마다 타임아웃을 걸었는데 바깥이 먼저 끊긴다.

    python3 ex2_timeout_budget.py

의존성 없음. 「각 층 타임아웃」과 「남은 예산을 나눠 쓰기」를 비교한다.
"""

#        이름     실제 걸리는 시간   이 단계가 쓸모 있으려면 최소한 필요한 시간
STEPS = [("검색", 4.0, 1.0), ("요약", 3.0, 1.0), ("초안", 9.0, 3.0), ("검토", 2.0, 2.0)]
OUTER_TIMEOUT = 15.0     # 사용자에게 약속한 응답 시간
PER_STEP_TIMEOUT = 10.0  # 각 단계에 건 타임아웃


def run_naive():
    """각 층이 자기 타임아웃만 본다."""
    spent, log = 0.0, []
    for name, need, _min in STEPS:
        took = min(need, PER_STEP_TIMEOUT)
        spent += took
        cut = took < need
        log.append((name, need, PER_STEP_TIMEOUT, took, "단계 타임아웃" if cut else "완료"))
        if spent >= OUTER_TIMEOUT:
            log.append(("(바깥)", 0, OUTER_TIMEOUT, spent, "전체 타임아웃 — 여기서 끊긴다"))
            break
    return spent, log


def run_budget():
    """남은 예산을 보고 각 층의 타임아웃을 그때그때 정한다."""
    remaining, log = OUTER_TIMEOUT, []
    for i, (name, need, _min) in enumerate(STEPS):
        # 뒤에 남은 단계들의 «최소 필요분»을 먼저 떼어 놓는다
        reserved = sum(m for _, _, m in STEPS[i + 1:])
        allow = max(0.0, remaining - reserved)
        took = min(need, allow)
        remaining -= took
        cut = took < need
        log.append((name, need, round(allow, 1), took,
                    "잘림 — 부분 결과 반환" if cut else "완료"))
    return OUTER_TIMEOUT - remaining, log


def show(title, spent, log):
    print(f"\n[{title}]")
    print(f"  {'단계':<8}{'필요':>6}{'허용':>8}{'실제':>8}  결과")
    for name, need, allow, took, res in log:
        need_s = f"{need:.1f}" if need else "-"
        print(f"  {name:<8}{need_s:>6}{allow:>8}{took:>8.1f}  {res}")
    print(f"  총 {spent:.1f}초 / 약속 {OUTER_TIMEOUT:.1f}초")


def main():
    print(f"단계 넷을 순서대로 돈다. 사용자에게 약속한 응답 시간은 {OUTER_TIMEOUT:.0f}초.")
    print("단계마다 «최소 필요분»을 미리 선언해 둔다: 검색 1, 요약 1, 초안 3, 검토 2초.")
    print(f"각 단계에 건 타임아웃은 {PER_STEP_TIMEOUT:.0f}초. 합치면 40초다.")

    show("층마다 따로 건 타임아웃", *run_naive())
    show("남은 예산을 나눠 쓰기", *run_budget())

    print(
        "\n위쪽은 검토 단계에 도달하지 못한다. 초안이 9초를 다 쓰고 나면 남은 게 없다.\n"
        "각 단계는 자기 타임아웃(10초)을 지켰다. 아무 단계도 잘못하지 않았는데 전체가 실패한다.\n"
        "\n아래쪽은 초안을 중간에 자른다. 대신 검토가 필요한 2초를 온전히 받는다.\n"
        "「완성 안 된 초안을 검토한 결과」와 「초안만 있고 검토 못 한 결과」 중\n"
        "어느 쪽이 나은지는 도메인이 정한다. 다만 «고를 수 있게» 되는 게 중요하다.\n"
        "\n규칙 하나. 각 층의 타임아웃 합이 바깥 타임아웃보다 크면\n"
        "그 설정은 «거짓말»이다. 아무도 지킬 수 없는 약속이다."
    )


if __name__ == "__main__":
    main()
