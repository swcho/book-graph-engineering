# %% [markdown]
# # `EffectLog.begin()`의 세 분기
#
# 상대 API가 멱등 키를 지원하지 않을 때, 우리가 부수 효과를 직접 기록하는
# **부수 효과 로그(side-effect log)** 를 순수 Python + sqlite3로 구현한다.
#
# 핵심 규칙: 실행 **전**에 `started`를 적고, 끝나면 `done`으로 채운다.
# `begin(key)`의 반환값이 세 갈래를 가른다:
#
# | 반환값 | 의미 | 행동 |
# |---|---|---|
# | `None` | 기록 없음 (방금 `started` 기록) | 실제로 실행한다 |
# | `('done', result)` | 이전에 완료됨 | 저장된 결과를 재사용, 실행 건너뜀 |
# | `('started', None)` | 이전 시도가 시작에서 멈춤 | 「모름」 — 사람이 확인 |

# %%
import sqlite3


class EffectLog:
    """부수 효과를 기록한다. 실행 «전»에 적고, 끝나면 결과를 채운다."""

    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("""
            CREATE TABLE effects (
                key     TEXT PRIMARY KEY,
                status  TEXT NOT NULL,      -- started | done
                result  TEXT
            )""")
        self.db.commit()

    def begin(self, key):
        """이미 시작했거나 끝난 일이면 그 상태를 돌려준다. 처음이면 started 기록 후 None."""
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

    def dump(self):
        return self.db.execute("SELECT key, status, result FROM effects").fetchall()


class DumbAPI:
    """멱등을 지원 안 하는 외부 API — 부를 때마다 새 결제가 나간다."""

    def __init__(self):
        self.calls = 0

    def charge(self, amount):
        self.calls += 1
        return f"R-{self.calls:03d}"


# %% [markdown]
# ## 크래시를 흉내 내는 실행 함수
#
# 프로세스가 죽는 상황을 예외로 시뮬레이션한다.
# `crash_before_finish=True`면 API 호출은 성공했지만 `done`을 적기 **전에** 죽는다.

# %%
class Crash(Exception):
    """done 기록 전에 프로세스가 죽었음을 흉내 내는 예외."""


def attempt(log, api, key, amount, crash_before_finish=False):
    prior = log.begin(key)

    if prior is None:                       # 분기 1: 기록 없음 → 실행
        receipt = api.charge(amount)
        if crash_before_finish:
            raise Crash(f"결제 {receipt}는 나갔는데 done 기록 전에 죽음")
        log.finish(key, receipt)
        return receipt, "새 결제"

    status, result = prior
    if status == "done":                    # 분기 2: 완료 → 저장된 결과 재사용
        return result, "이미 완료 — 건너뜀"

    # 분기 3: started 잔존 → 모름
    return None, "이전 시도가 «시작»에서 멈춰 있다 — 사람이 확인해야 함"


# %% [markdown]
# ## 분기 1 → 분기 2: 정상 흐름
#
# 같은 키로 세 번 시도해도 실제 API 호출은 한 번뿐이다.
# 첫 시도는 `begin() → None`(실행), 이후는 `('done', result)`(건너뜀).

# %%
log, api = EffectLog(), DumbAPI()
for i in range(3):
    r, how = attempt(log, api, "order-8842", 50_000)
    print(f"시도 {i + 1}: {r} ({how})")
print(f"실제 API 호출 {api.calls}회, 로그: {log.dump()}")

# 출력:
# 시도 1: R-001 (새 결제)
# 시도 2: R-001 (이미 완료 — 건너뜀)
# 시도 3: R-001 (이미 완료 — 건너뜀)
# 실제 API 호출 1회, 로그: [('order-8842', 'done', 'R-001')]

# %% [markdown]
# ## 분기 3: `started`만 적고 죽은 경우
#
# 결제는 나갔는데 `done`을 못 적고 죽었다. 재시작 후 `begin()`은
# `('started', None)`을 돌려주고, 우리는 결제 여부를 **모른다**.
# 자동 재시도하면 중복 결제, 무조건 건너뛰면 미결제 위험 — 그래서 사람을 부른다.

# %%
log2, api2 = EffectLog(), DumbAPI()

try:
    attempt(log2, api2, "order-9001", 30_000, crash_before_finish=True)
except Crash as e:
    print(f"시도 1: 크래시! ({e})")

print(f"크래시 직후 로그: {log2.dump()}")

# 프로세스 재시작 후 같은 키로 재시도
r, how = attempt(log2, api2, "order-9001", 30_000)
print(f"시도 2: {r} ({how})")
print(f"실제 API 호출 {api2.calls}회 — 로그만 봐서는 1회인지 0회인지 알 수 없다")

# 출력:
# 시도 1: 크래시! (결제 R-001는 나갔는데 done 기록 전에 죽음)
# 크래시 직후 로그: [('order-9001', 'started', None)]
# 시도 2: None (이전 시도가 «시작»에서 멈춰 있다 — 사람이 확인해야 함)
# 실제 API 호출 1회 — 로그만 봐서는 1회인지 0회인지 알 수 없다

# %% [markdown]
# ## 반대 경우: API 호출 «전»에 죽었어도 로그는 똑같다
#
# `started`만 남은 로그는 「호출 후 죽음」과 「호출 전 죽음」을 구분하지 못한다.
# 그래서 이 상태를 「모름」으로 분류하는 것이 유일하게 정직한 답이다.

# %%
log3, api3 = EffectLog(), DumbAPI()

# begin()만 하고 API 호출 직전에 죽었다고 치자
log3.begin("order-9002")
print(f"호출 전 크래시 로그: {log3.dump()}")
print(f"실제 API 호출 {api3.calls}회 — 그런데 로그는 위(1회 호출)와 구분 불가")

r, how = attempt(log3, api3, "order-9002", 10_000)
print(f"재시도: {r} ({how})")

# 출력:
# 호출 전 크래시 로그: [('order-9002', 'started', None)]
# 실제 API 호출 0회 — 그런데 로그는 위(1회 호출)와 구분 불가
# 재시도: None (이전 시도가 «시작»에서 멈춰 있다 — 사람이 확인해야 함)

# %% [markdown]
# ## 정리
#
# `begin(key)`는 "실행해도 되는가?"를 답하는 게이트다:
#
# 1. **`None`** — 기록 없음. 방금 `started`를 적었으니 실행하라.
# 2. **`('done', result)`** — 완료됨. 저장된 결과를 쓰고 건너뛰어라.
# 3. **`('started', None)`** — 모름. 외부 호출과 우리 기록이 같은 트랜잭션이
#    아니라서 이 창은 없앨 수 없다. 자동 재시도 대신 사람이 마감한다.
#    (상대에게 조회 API가 있으면 재시작 때 물어봐서 사람 없이 마감할 수 있다.)
