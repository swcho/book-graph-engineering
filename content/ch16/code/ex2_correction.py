"""
예제 2 — 만료와 정정은 다르다. 섞으면 과거 재현이 깨진다.

    python3 ex2_correction.py

의존성 없음.
"""

from datetime import date

from bitemporal import BiTemporalStore, show

D = date


def scenario_expire():
    """만료 — 그때는 맞았고 지금은 아니다."""
    st = BiTemporalStore()
    st.assert_fact("가온테크", "등급", "A", valid_from=D(2026, 1, 1), tx_at=D(2026, 1, 1))
    st.assert_fact("가온테크", "등급", "B", valid_from=D(2026, 5, 1), tx_at=D(2026, 5, 1))
    return st


def scenario_correct():
    """정정 — 그때도 틀렸다. 처음부터 B 였는데 A 로 잘못 적었다."""
    st = BiTemporalStore()
    st.assert_fact("가온테크", "등급", "A", valid_from=D(2026, 1, 1), tx_at=D(2026, 1, 1))
    st.correct("가온테크", "등급", "B", valid_from=D(2026, 1, 1), tx_at=D(2026, 5, 1))
    return st


def main():
    for name, st in (("만료 — 5월에 등급이 바뀌었다", scenario_expire()),
                     ("정정 — 처음부터 B였는데 잘못 적었다", scenario_correct())):
        print(f"\n{'='*66}\n{name}")
        show(st.history("가온테크", "등급"), "저장된 사실")

        print("\n    질의")
        for label, va, ta in (
            ("3월 1일 등급 (지금 아는 대로)",        D(2026, 3, 1), None),
            ("3월 1일 등급 (4월 시점 지식으로)",      D(2026, 3, 1), D(2026, 4, 1)),
            ("6월 1일 등급 (지금 아는 대로)",        D(2026, 6, 1), None),
        ):
            rows = st.query("가온테크", "등급", valid_at=va, tx_at=ta)
            ans = ", ".join(r["value"] for r in rows) or "모름"
            print(f"      {label:<34} → {ans}")

    print(
        "\n" + "=" * 66 +
        "\n첫 줄을 비교해 보라. 「3월 1일 등급, 지금 아는 대로」\n"
        "  만료 시나리오 → A   (그때는 진짜 A 였다)\n"
        "  정정 시나리오 → B   (그때도 B 였는데 우리가 잘못 적었다)\n"
        "\n두 번째 줄은 둘 다 A 다. 4월 시점에는 둘 다 A 로 알고 있었으니까.\n"
        "\n이 구분이 왜 중요하냐면, 만료를 정정으로 처리하면\n"
        "과거 보고서가 «소급해서» 바뀐다. 감사에서 이게 문제가 된다.\n"
        "반대로 정정을 만료로 처리하면 틀린 값이 과거에 영원히 남는다.\n"
        "\n실무에서는 사람이 이 둘을 자주 헷갈린다.\n"
        "그래서 입력 화면에서 «값이 바뀐 건가요, 잘못 적은 건가요»를 묻는 게 낫다.\n"
        "질문 하나를 더 하는 게 나중에 며칠을 아낀다."
    )


if __name__ == "__main__":
    main()
