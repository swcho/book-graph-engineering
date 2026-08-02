"""
예제 1 — 유효 시간과 기록 시간이 왜 둘 다 필요한가.

    python3 ex1_two_axes.py

의존성 없음.
"""

from datetime import date

from bitemporal import BiTemporalStore, show

D = date


def main():
    st = BiTemporalStore()

    # 3월 1일부터 김하늘이 담당이었는데, 우리는 4월 10일에 알았다
    st.assert_fact("가온테크", "담당", "김하늘",
                   valid_from=D(2026, 3, 1), tx_at=D(2026, 4, 10))

    # 6월 1일부터 박서준으로 바뀌었고, 6월 3일에 알았다
    st.assert_fact("가온테크", "담당", "박서준",
                   valid_from=D(2026, 6, 1), tx_at=D(2026, 6, 3))

    show(st.history("가온테크", "담당"), "저장된 사실 전부")

    cases = [
        ("3월 15일에 담당이 누구였나 (지금 아는 대로)",   D(2026, 3, 15), None),
        ("3월 15일에 우리는 누구로 알고 있었나",          D(2026, 3, 15), D(2026, 3, 15)),
        ("7월 1일에 담당이 누구인가",                    D(2026, 7, 1), None),
        ("6월 2일에 우리는 7월 담당을 누구로 알았나",      D(2026, 7, 1), D(2026, 6, 2)),
    ]
    print("\n같은 저장소에 네 가지를 물어본다")
    for label, va, ta in cases:
        rows = st.query("가온테크", "담당", valid_at=va, tx_at=ta)
        ans = ", ".join(r["value"] for r in rows) or "모름"
        print(f"    {label:<40} → {ans}")

    print(
        "\n두 번째 줄이 이 예제의 요점이다.\n"
        "«3월 15일에 담당은 김하늘이었다»는 지금 아는 사실이고,\n"
        "«3월 15일에 우리는 몰랐다»도 동시에 참이다.\n"
        "\n감사에서 «그때 왜 그렇게 처리했나»를 물으면 두 번째가 필요하다.\n"
        "현재 값만 저장하면 이 질문에 답할 방법이 없다."
    )


if __name__ == "__main__":
    main()
