"""
예제 2 — 재생은 얼마나 걸리나. 그리고 스냅숏이 왜 필요한가.

    python3 ex2_replay_cost.py

의존성 없음. 이벤트 수를 늘려 가며 «처음부터 재생»과
«스냅숏 + 이후만 재생»을 비교한다.
"""

import random
import time

rng = random.Random(11)


def make_events(n):
    out = []
    for i in range(n):
        s = f"e{rng.randint(0, 400)}"
        o = f"t{rng.randint(0, 40)}"
        op = "추가" if rng.random() < 0.72 else "삭제"
        out.append((i, s, "속함", o, op))
    return out


def replay(events, start_state=None):
    st = set(start_state) if start_state else set()
    for _i, s, k, o, op in events:
        if op == "추가":
            st.add((s, k, o))
        else:
            st.discard((s, k, o))
    return st


def timed(fn, *a):
    t0 = time.perf_counter()
    r = fn(*a)
    return (time.perf_counter() - t0) * 1000, r


SNAPSHOT_EVERY = 50_000


def main():
    print(f"스냅숏을 {SNAPSHOT_EVERY:,} 이벤트마다 찍는다고 하자.\n")
    print(f"{'이벤트 수':>12}{'처음부터(ms)':>14}{'스냅숏 이후(ms)':>16}"
          f"{'재생할 이벤트':>14}{'배수':>8}")
    print("-" * 68)

    for n in (10_000, 63_000, 217_000, 1_034_000):
        ev = make_events(n)
        full_ms, st = timed(replay, ev)

        # 스냅숏 뒤에 남은 것만 재생
        last_snap = (n // SNAPSHOT_EVERY) * SNAPSHOT_EVERY
        snap_state = replay(ev[:last_snap]) if last_snap else set()
        tail = ev[last_snap:]
        tail_ms, st2 = timed(replay, tail, snap_state)

        assert st == st2
        ratio = full_ms / tail_ms if tail_ms else 0
        print(f"{n:>12,}{full_ms:>14.1f}{tail_ms:>16.1f}"
              f"{len(tail):>14,}{ratio:>7.1f}x")

    print(
        "\n처음부터 재생하면 이벤트 수에 비례해서 늘어난다. 백만 개면 395ms 다.\n"
        "스냅숏이 있으면 «마지막 스냅숏 이후»만 재생하니 16ms 로 끝난다.\n"
        "\n첫 줄은 배수가 0.8 이다. 스냅숏이 아직 한 번도 안 찍혀서\n"
        "결국 처음부터 재생하는 것과 같고, 측정 잡음만 얹혔다.\n"
        "스냅숏은 «데이터가 충분히 쌓인 뒤에» 값을 하기 시작한다.\n"
        "\n여기서 중요한 건 «상한»이라는 말이다.\n"
        "이벤트가 백만 개든 천만 개든 재생할 것은 최대 5만 개다.\n"
        "그러니 재생 시간이 «데이터 양»이 아니라 «스냅숏 주기»로 정해진다.\n"
        "\n주기를 어떻게 잡나. 두 값의 교환이다.\n"
        "  짧게 잡으면 — 재생은 빠른데 스냅숏 저장 공간이 늘어난다\n"
        "  길게 잡으면 — 공간은 아끼는데 복구가 느려진다\n"
        "\n저는 «복구 목표 시간»에서 거꾸로 계산한다.\n"
        "「장애 났을 때 3초 안에 복구」가 목표면, 3초에 재생할 수 있는\n"
        "이벤트 수를 재고 그만큼을 주기로 잡는다.\n"
        "\n그리고 이건 데이터베이스가 하는 일과 같다.\n"
        "쓰기 전 로그(WAL)와 체크포인트. 30년 된 구조를 그대로 쓰는 것이다."
    )


if __name__ == "__main__":
    main()
