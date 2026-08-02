"""
예제 3 — 상대가 멱등을 지원 안 하면, 우리가 «했다는 사실»을 먼저 적는다.

    python3 ex3_side_effect_log.py

의존성 없음 (sqlite3 는 표준 라이브러리).
"""

import sqlite3


class EffectLog:
    """부수 효과를 기록한다. 실행 «전»에 적고, 끝나면 결과를 채운다."""

    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("""
            CREATE TABLE effects (
                key     TEXT PRIMARY KEY,
                status  TEXT NOT NULL,      -- started | done | failed
                result  TEXT
            )""")
        self.db.commit()

    def begin(self, key):
        """이미 시작했거나 끝난 일이면 그 상태를 돌려준다."""
        row = self.db.execute(
            "SELECT status, result FROM effects WHERE key=?", (key,)).fetchone()
        if row:
            return row
        self.db.execute("INSERT INTO effects VALUES (?, 'started', NULL)", (key,))
        self.db.commit()
        return None

    def finish(self, key, result):
        self.db.execute("UPDATE effects SET status='done', result=? WHERE key=?",
                        (result, key))
        self.db.commit()


class DumbAPI:
    """멱등을 지원 안 하는 외부 API."""
    def __init__(self):
        self.calls = 0

    def charge(self, amount):
        self.calls += 1
        return f"R-{self.calls:03d}"


def attempt(log, api, key, amount, crash_before_finish=False):
    prior = log.begin(key)
    if prior:
        status, result = prior
        if status == "done":
            return result, "이미 완료 — 건너뜀"
        return None, "이전 시도가 «시작»에서 멈춰 있다 — 사람이 확인해야 함"
    receipt = api.charge(amount)
    if crash_before_finish:
        return receipt, "결제는 됐는데 기록 전에 죽음"
    log.finish(key, receipt)
    return receipt, "새 결제"


def main():
    print("[정상 흐름 — 세 번 시도]")
    log, api = EffectLog(), DumbAPI()
    for i in range(3):
        r, how = attempt(log, api, "order-8842", 50_000)
        print(f"    시도 {i+1}: {r} ({how})")
    print(f"    실제 API 호출 {api.calls}회\n")

    print("[결제 후 기록 전에 죽는 경우]")
    log2, api2 = EffectLog(), DumbAPI()
    r, how = attempt(log2, api2, "order-9001", 30_000, crash_before_finish=True)
    print(f"    시도 1: {r} ({how})")
    r, how = attempt(log2, api2, "order-9001", 30_000)
    print(f"    시도 2: {r} ({how})")
    print(f"    실제 API 호출 {api2.calls}회")

    print(
        "\n두 번째가 이 방법의 한계다.\n"
        "«시작»은 적었는데 «완료»를 못 적고 죽으면, 우리는 결제가 됐는지 모른다.\n"
        "\n그래서 자동으로 재시도하지 않고 «사람이 확인» 상태로 둔다.\n"
        "중복 결제보다 사람 한 번 부르는 게 싸니까.\n"
        "\n이 구간을 아예 없앨 수는 없다. 외부 호출과 우리 기록은 «같은 트랜잭션»이 아니라서다.\n"
        "줄일 수는 있다. 구간을 좁히는 것이다.\n"
        "  - 기록을 먼저, 호출을 나중에 (지금 방식)\n"
        "  - 호출 직후 즉시 기록 (그 사이가 창)\n"
        "  - 상대에게 «조회» API 가 있으면 재시작 때 물어본다 (제일 확실하다)\n"
        "\n세 번째가 되면 사람을 안 불러도 된다. 조회 API 가 있는지 먼저 확인하시라."
    )


if __name__ == "__main__":
    main()
