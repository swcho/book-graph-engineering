"""
예제 4 — 이행 중에 «둘 다» 읽는 코드를 어떻게 쓰나.

    python3 ex4_dual_read.py

의존성 없음. 옛것과 새것이 공존하는 구간의 읽기 전략 넷을 비교한다.
그중 하나만 「데이터가 어긋났을 때」를 알려 준다.
"""

# 이행 중 상태: 일부는 옛 이름만, 일부는 둘 다, 일부는 새 이름만
ROWS = [
    ("t1", "박민수", None,     "옛것만"),
    ("t2", "이서연", "이서연",  "둘 다 · 같음"),
    ("t3", "김도현", "정하윤",  "둘 다 · 다름"),      # 어긋났다
    ("t4", None,     "최유진",  "새것만"),
    ("t5", None,     None,     "둘 다 없음"),
]


def old_only(old, new):
    return old, None


def new_only(old, new):
    return new, None


def new_then_old(old, new):
    return (new if new is not None else old), None


def compare_both(old, new):
    """둘 다 읽고 «다르면» 신고한다."""
    if old is not None and new is not None and old != new:
        return new, "불일치"
    if old is None and new is None:
        return None, "둘 다 없음"
    return (new if new is not None else old), None


def main():
    print("이행 중 데이터 상태:\n")
    print(f"{'키':<5}{'옛 이름':<10}{'새 이름':<10}상황")
    print("-" * 44)
    for k, o, n, note in ROWS:
        print(f"{k:<5}{(o or '-'):<10}{(n or '-'):<10}{note}")

    print(f"\n{'전략':<18}" + "".join(f"{r[0]:>8}" for r in ROWS)
          + f"{'문제 감지':>12}")
    print("-" * 76)
    for name, fn in (("옛것만 읽기", old_only),
                     ("새것만 읽기", new_only),
                     ("새것 없으면 옛것", new_then_old),
                     ("둘 다 읽고 비교", compare_both)):
        cells, alerts = [], 0
        for k, o, n, _note in ROWS:
            v, flag = fn(o, n)
            alerts += flag is not None
            cells.append(f"{(v or '-'):>8}")
        print(f"{name:<18}" + "".join(cells) + f"{alerts:>12}건")

    print(
        "\nt3 을 보시라. 옛 이름은 김도현이고 새 이름은 정하윤이다. 어긋났다.\n"
        "\n왜 어긋나나. 이행 중에 «양쪽으로 쓰는» 코드에 버그가 있었거나,\n"
        "옛 코드가 아직 살아 있어서 옛 이름만 고쳤거나,\n"
        "배치가 옛것을 새것으로 복사하는 도중에 누가 옛것을 고쳤거나.\n"
        "\n앞의 세 전략은 t3 에서 «그냥 하나를 고른다». 조용히.\n"
        "고른 게 맞을 수도 틀릴 수도 있는데 아무도 모른다.\n"
        "\n네 번째만 «불일치»를 신고한다. 그리고 그게 이행의 진짜 안전장치다.\n"
        "\n이행 중에는 데이터가 어긋난다. 안 어긋나는 이행은 없다.\n"
        "중요한 건 어긋나는 것을 «막는» 게 아니라 «아는» 것이다.\n"
        "\n실무에서는 이렇게 쓴다.\n"
        "  이행 구간 동안 «둘 다 읽고 비교»로 돌린다\n"
        "  불일치를 지표로 세고, 0 이 될 때까지 수축하지 않는다\n"
        "  불일치가 나오면 그 키만 따로 고친다\n"
        "\n값은 읽기가 두 배가 되는 것이다. 이행 구간에만 내는 값이라 괜찮다.\n"
        "그리고 이 값을 안 내면, 수축한 뒤에 «조용히 틀린 데이터»가 남는다."
    )


if __name__ == "__main__":
    main()
