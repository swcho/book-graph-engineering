# %% [markdown]
# # 백필의 세 가지 원칙 (+ 한 번 더)
#
# 32장 요약의 한 줄:
#
# > 백필은 **쪼개서 돌리고**, **어디까지 했는지 남기고**, **멱등하게** 만드세요.
# > 그리고 **끝난 뒤 한 번 더** 돌립니다.
#
# 이 스크립트는 네 가지를 실제로 돌려 본다.
#
# | 절 | 보여 주는 것 |
# |---|---|
# | 1 | 통짜 백필이 왜 위험한가 (락 시간 · 실패 손실) |
# | 2 | 쪼개기(chunk) + 체크포인트 → 크래시 후 재개 |
# | 3 | 멱등 쓰기 vs 비멱등 쓰기 (같은 청크 두 번 처리) |
# | 4 | 백필 중 들어온 쓰기 → 마지막 한 번 더가 필요한 이유 |
#
# 실패 확률 $p$ 로 청크 하나가 죽는다고 하면, 청크 개수 $k$ 에 대해
# 「최소 한 번은 죽는다」 확률은
#
# $$P(\text{적어도 한 번 실패}) = 1 - (1-p)^k$$
#
# 이고, 체크포인트가 **없을 때** 기대 재작업량은 이미 처리한 전체가 날아가므로
# $O(N)$, **있을 때**는 청크 하나뿐이라 $O(N/k)$ 다. 이게 원칙 2의 전부다.

# %%
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용. 없으면 그 셀만 건너뛰면 된다)
import random
from dataclasses import dataclass, field


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


N_ROWS = 1000  # 옛 스키마에 들어 있는 행 수
CHUNK = 100  # 한 번에 처리할 크기
random.seed(32)

print(f"전체 {N_ROWS}행, 청크 크기 {CHUNK} → 청크 {N_ROWS // CHUNK}개")
# 출력: 전체 1000행, 청크 크기 100 → 청크 10개


# %% [markdown]
# ## 0. 장난감 저장소
#
# `old` 는 옛 스키마(`이끔`), `new` 는 새 스키마(`리드`).
# 백필은 `old` → `new` 로 값을 옮기는 일이다.
# `version` 은 「그 행이 마지막으로 언제 바뀌었나」를 나타내는 논리 시계로,
# 나중에 «백필 중에 바뀐 행»을 찾는 데 쓴다.

# %%
@dataclass
class Store:
    old: dict = field(default_factory=dict)  # key -> 값
    new: dict = field(default_factory=dict)  # key -> 값 (백필 대상)
    version: dict = field(default_factory=dict)  # key -> 논리 시계
    clock: int = 0
    writes: int = 0  # 새 스키마에 쓴 횟수 (비용 지표)

    def live_update(self, key, value):
        """서비스가 돌아가는 중 옛 스키마에 들어오는 쓰기."""
        self.clock += 1
        self.old[key] = value
        self.version[key] = self.clock

    def mismatch(self):
        """옛것과 새것이 어긋난 키 수 (예제 4의 «둘 다 읽고 비교»)."""
        return sum(1 for k, v in self.old.items() if self.new.get(k) != v)


def fresh_store(n=N_ROWS):
    s = Store()
    for i in range(n):
        s.live_update(f"k{i:04d}", f"v{i}")
    return s


s0 = fresh_store()
print("옛 스키마 행 수:", len(s0.old), "| 새 스키마 행 수:", len(s0.new))
print("불일치:", s0.mismatch())
# 출력: 옛 스키마 행 수: 1000 | 새 스키마 행 수: 0
# 출력: 불일치: 1000


# %% [markdown]
# ## 1. 원칙 1을 어긴 백필 — 통짜로 한 방에
#
# 트랜잭션 하나로 1000행을 다 만지면
# (1) 그 시간 내내 락을 쥐고, (2) 중간에 죽으면 **전부** 롤백된다.
# 몇 행까지 갔는지 기록이 없으니 재시도는 언제나 0부터다.

# %%
def whole_hog_backfill(store, fail_at=None):
    """단일 트랜잭션 백필. fail_at 행에서 죽으면 통째로 롤백."""
    staged = {}
    for i, (k, v) in enumerate(sorted(store.old.items())):
        if fail_at is not None and i == fail_at:
            return {"상태": "실패", "커밋된_행": 0, "버린_작업": i, "락_구간": len(store.old)}
        staged[k] = v
    store.new.update(staged)
    store.writes += len(staged)
    return {"상태": "성공", "커밋된_행": len(staged), "버린_작업": 0, "락_구간": len(store.old)}


s = fresh_store()
r = whole_hog_backfill(s, fail_at=730)
print("통짜 백필 결과:", r)
print("남은 불일치:", s.mismatch())
# 출력: 통짜 백필 결과: {'상태': '실패', '커밋된_행': 0, '버린_작업': 730, '락_구간': 1000}
# 출력: 남은 불일치: 1000

# %% [markdown]
# 730행을 처리한 뒤 죽었는데 **커밋된 행은 0**이다.
# 진행률이 0으로 되돌아가고, 다시 돌려도 또 730행쯤에서 죽을 가능성이 남는다.
# 큰 테이블에서 이 패턴이 「몇 주째 백필 중」의 원인이 된다.


# %% [markdown]
# ## 2. 원칙 1 + 2 — 쪼개고, 어디까지 했는지 남긴다
#
# 체크포인트는 「다음에 처리할 커서」를 **백필 대상과 같은 저장소에**,
# 청크 커밋과 **같은 트랜잭션으로** 적어야 한다.
# 그래야 「썼는데 체크포인트는 못 남긴」 틈이 사라진다.

# %%
def chunked_backfill(store, checkpoint, chunk=CHUNK, crash_after=None, log=None):
    """
    checkpoint: {"cursor": 지금까지 처리한 키 개수} — 재시작할 때 그대로 넘긴다.
    crash_after: 이 개수만큼 청크를 처리한 뒤 예외 없이 즉시 중단(크래시 흉내).
    """
    keys = sorted(store.old)
    done = 0
    while checkpoint["cursor"] < len(keys):
        batch = keys[checkpoint["cursor"] : checkpoint["cursor"] + chunk]
        for k in batch:  # ── 청크 트랜잭션 시작
            store.new[k] = store.old[k]  # 멱등 쓰기 (덮어쓰기)
            store.writes += 1
        checkpoint["cursor"] += len(batch)  # 커서도 같은 트랜잭션에서
        done += 1  # ── 청크 트랜잭션 커밋
        if log is not None:
            log.append((checkpoint["cursor"], store.mismatch()))
        if crash_after is not None and done >= crash_after:
            return {"상태": "중단", "처리한_청크": done, "커서": checkpoint["cursor"]}
    return {"상태": "완료", "처리한_청크": done, "커서": checkpoint["cursor"]}


s = fresh_store()
ckpt = {"cursor": 0}
trace = []

run1 = chunked_backfill(s, ckpt, crash_after=7, log=trace)  # 7청크 처리하고 죽었다
print("1차 실행:", run1, "| 불일치:", s.mismatch())

run2 = chunked_backfill(s, ckpt, log=trace)  # 체크포인트에서 재개
print("2차 실행:", run2, "| 불일치:", s.mismatch())
print("버린 작업량(행):", 0, "| 총 쓰기:", s.writes)
# 출력: 1차 실행: {'상태': '중단', '처리한_청크': 7, '커서': 700} | 불일치: 300
# 출력: 2차 실행: {'상태': '완료', '처리한_청크': 3, '커서': 1000} | 불일치: 0
# 출력: 버린 작업량(행): 0 | 총 쓰기: 1000

# %% [markdown]
# 2차 실행이 처리한 청크는 **3개**다. 700행은 다시 안 만졌다.
# 통짜 백필이 730행을 버렸던 자리에서, 체크포인트는 0행을 버린다.


# %% [markdown]
# ## 3. 원칙 3 — 멱등하게
#
# 재시도는 **반드시** 일어난다. 타임아웃, 재배포, 사람의 중복 실행.
# 그러면 같은 청크가 두 번 처리되는데, 쓰기가 멱등하지 않으면 그때 데이터가 상한다.
#
# - 멱등: `new[k] = old[k]` (덮어쓰기 / `MERGE` / upsert) → 몇 번 해도 같은 상태
# - 비멱등: `new[k].append(old[k])` 나 `count += 1` → 횟수만큼 결과가 달라진다

# %%
def idempotent_apply(target, k, v):
    target[k] = v  # upsert


def non_idempotent_apply(target, k, v):
    target.setdefault(k, []).append(v)  # 관계를 CREATE 로 만드는 경우와 같다


keys = ["k0001", "k0002"]
src = {"k0001": "v1", "k0002": "v2"}

idem, non_idem = {}, {}
for attempt in (1, 2, 3):  # 같은 청크를 세 번 처리
    for k in keys:
        idempotent_apply(idem, k, src[k])
        non_idempotent_apply(non_idem, k, src[k])
    print(f"{attempt}회 처리 후 → 멱등: {idem} | 비멱등: {non_idem}")
# 출력: 1회 처리 후 → 멱등: {'k0001': 'v1', 'k0002': 'v2'} | 비멱등: {'k0001': ['v1'], 'k0002': ['v2']}
# 출력: 2회 처리 후 → 멱등: {'k0001': 'v1', 'k0002': 'v2'} | 비멱등: {'k0001': ['v1', 'v1'], 'k0002': ['v2', 'v2']}
# 출력: 3회 처리 후 → 멱등: {'k0001': 'v1', 'k0002': 'v2'} | 비멱등: {'k0001': ['v1', 'v1', 'v1'], 'k0002': ['v2', 'v2', 'v2']}

# %% [markdown]
# 비멱등 백필을 세 번 재시도하면 관계가 3배로 늘어난다.
# 그래프에서 이게 특히 잘 나는데, `CREATE (a)-[:리드]->(b)` 는 부를 때마다 엣지를 하나 더 만든다.
# 32장 예제 2의 `copy` 단계를 두 번 돌리면 엣지가 두 배가 되는 게 정확히 이 문제다.
# 멱등하게 쓰려면 「없으면 만들고 있으면 그대로」(`MERGE`) 여야 한다.
#
# 멱등성의 부수 효과가 하나 더 있다. **체크포인트가 조금 뒤처져도 괜찮아진다.**
# 커서를 남기기 직전에 죽어서 마지막 청크를 두 번 처리해도 결과가 같으니,
# 「적어도 한 번(at-least-once)」 보장만으로 「정확히 한 번」의 결과를 얻는다.

# %%
# 체크포인트가 한 청크 뒤처진 채 재개해도(청크 중복 처리) 상태는 같다
s = fresh_store()
ckpt = {"cursor": 0}
chunked_backfill(s, ckpt, crash_after=7)
ckpt["cursor"] -= CHUNK  # 커서 커밋 실패 흉내 → 7번째 청크를 다시 처리
chunked_backfill(s, ckpt)
print("중복 처리 후 불일치:", s.mismatch(), "| 새 스키마 행 수:", len(s.new), "| 쓰기:", s.writes)
# 출력: 중복 처리 후 불일치: 0 | 새 스키마 행 수: 1000 | 쓰기: 1100

# %% [markdown]
# 쓰기 횟수만 100번 늘고(중복 청크 값) 결과는 동일하다.
# 「값은 중복 쓰기, 얻는 것은 안심」이 멱등성의 거래다.


# %% [markdown]
# ## 4. 「끝난 뒤 한 번 더」 — 움직이는 표적
#
# 백필은 **살아 있는 시스템** 위에서 돈다. 커서가 지나간 뒤에 그 행이 또 바뀔 수 있다.
# 그러면 백필은 「100% 완료」라고 보고하는데 새 스키마에는 헌 값이 남는다.
#
# 커서 위치를 $c$, 백필 도는 동안 들어온 쓰기 개수를 $m$ 이라 하면,
# 이미 지나간 구간에 떨어지는 쓰기의 기대 개수는
#
# $$E[\text{놓친 행}] \approx \sum_{j} \Pr[\text{key}_j < c_j]$$
#
# 즉 백필이 진행될수록 「놓칠 확률」이 커진다. 그래서 끝나고 한 번 더 돈다.

# %%
def backfill_with_live_traffic(store, chunk=CHUNK, writes_per_chunk=12, log=None):
    """청크를 하나 처리할 때마다 라이브 쓰기가 몇 건 섞여 들어온다."""
    keys = sorted(store.old)
    cursor = 0
    missed_hint = []
    while cursor < len(keys):
        for k in keys[cursor : cursor + chunk]:
            store.new[k] = store.old[k]
            store.writes += 1
        cursor += chunk
        for _ in range(writes_per_chunk):  # ← 그 사이 서비스는 계속 돌고 있다
            k = random.choice(keys)
            store.live_update(k, f"수정-{store.clock}")
            if keys.index(k) < cursor:  # 커서가 이미 지나간 행이면 새것이 헌 값이 된다
                missed_hint.append(k)
        if log is not None:
            log.append((cursor, store.mismatch()))
    return {"커서": cursor, "라이브_쓰기": writes_per_chunk * (len(keys) // chunk), "놓친_행": len(set(missed_hint))}


s = fresh_store()
live_trace = []
r = backfill_with_live_traffic(s, log=live_trace)
print("백필 1회전:", r)
print("진행률 100%인데 남은 불일치:", s.mismatch())
# 출력: 백필 1회전: {'커서': 1000, '라이브_쓰기': 120, '놓친_행': 72}
# 출력: 진행률 100%인데 남은 불일치: 72

# %%
# 「한 번 더」 — 두 번째 패스. 라이브 트래픽이 잦아든 뒤(또는 dual-write 가 켜진 뒤) 돌린다.
before = s.mismatch()
sweep_writes = 0
for k, v in sorted(s.old.items()):
    if s.new.get(k) != v:  # 어긋난 행만 (전체를 다시 돌아도 멱등하므로 안전)
        s.new[k] = v
        sweep_writes += 1
print(f"최종 스윕: 고친 행 {sweep_writes} | 불일치 {before} → {s.mismatch()}")
# 출력: 최종 스윕: 고친 행 72 | 불일치 72 → 0

# %% [markdown]
# 여기서 중요한 순서가 있다. **한 번 더 돌리는 것만으로는 0을 보장하지 못한다.**
# 스윕이 도는 동안에도 쓰기가 들어오면 또 새 불일치가 생긴다.
# 그래서 32장 예제 5의 게이트 순서가 이렇게 생겼다.
#
# 1. `dual-write` — 새로 들어오는 쓰기는 **양쪽에** 쓴다 (→ 「지나간 뒤 바뀜」의 원천을 막는다)
# 2. `backfill` — 옛 데이터를 쪼개서 · 체크포인트로 · 멱등하게 옮긴다
# 3. 최종 스윕 — 그래도 남은 잔여를 한 번 더 훑는다
# 4. `dual-read` — 불일치를 **세고**, **0이 될 때까지 수축하지 않는다**
#
# dual-write 없이 백필만 돌리면 스윕이 끝없이 꼬리를 문다.

# %%
# dual-write 가 켜진 상태를 흉내: 라이브 쓰기가 양쪽에 들어간다
def live_update_dual(store, key, value):
    store.clock += 1
    store.old[key] = value
    store.new[key] = value  # 양쪽 쓰기
    store.version[key] = store.clock


s = fresh_store()
keys = sorted(s.old)
cursor = 0
while cursor < len(keys):
    for k in keys[cursor : cursor + CHUNK]:
        s.new[k] = s.old[k]
        s.writes += 1
    cursor += CHUNK
    for _ in range(12):
        live_update_dual(s, random.choice(keys), f"수정-{s.clock}")
print("dual-write + 백필 1회전 후 불일치:", s.mismatch())
# 출력: dual-write + 백필 1회전 후 불일치: 0


# %% [markdown]
# ## 5. 시각화
#
# 세 곡선을 겹쳐 본다.
#
# - **체크포인트 있음**: 크래시 지점에서 진행률이 유지된다
# - **체크포인트 없음**: 크래시하면 0으로 되돌아간다
# - **라이브 트래픽**: 커서가 100%에 닿아도 불일치가 0이 안 된다 → 「한 번 더」

# %%
try:
    import plotly.graph_objects as go

    n_chunks = N_ROWS // CHUNK
    crash = 7

    with_ckpt = [min(i, n_chunks) * 100 / n_chunks for i in range(n_chunks + 1)]
    no_ckpt = [i * 100 / n_chunks for i in range(crash + 1)] + [0.0] + [
        i * 100 / n_chunks for i in range(1, n_chunks - crash + 1)
    ]
    no_ckpt = no_ckpt[: n_chunks + 1] + [None] * max(0, n_chunks + 1 - len(no_ckpt[: n_chunks + 1]))
    live_mismatch = [100.0] + [m * 100 / N_ROWS for _c, m in live_trace]

    x = list(range(n_chunks + 1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=with_ckpt, name="진행률 · 체크포인트 있음", mode="lines+markers"))
    fig.add_trace(go.Scatter(x=x, y=no_ckpt, name="진행률 · 체크포인트 없음(크래시=0으로)", mode="lines+markers", line=dict(dash="dash")))
    fig.add_trace(go.Scatter(x=x, y=live_mismatch, name="남은 불일치(%) · 라이브 트래픽", mode="lines+markers", yaxis="y"))
    fig.add_vline(x=crash, line_dash="dot", annotation_text="크래시")
    fig.add_hline(y=0, line_width=1)
    fig.update_layout(
        title="쪼개기 · 체크포인트 · 그리고 끝나도 0이 아닌 불일치",
        xaxis_title="처리한 청크 수",
        yaxis_title="퍼센트",
        legend=dict(orientation="h", y=-0.25),
        template="plotly_white",
        height=480,
    )
    _show(fig)
    fig.write_image("expy.png", scale=2)
    print("expy.png 저장")
except Exception as e:  # noqa: BLE001
    print("시각화 건너뜀:", type(e).__name__, e)
# 출력: expy.png 저장


# %% [markdown]
# ## 정리
#
# | 원칙 | 없으면 | 있으면 |
# |---|---|---|
# | 쪼갠다 | 락을 오래 쥐고, 실패하면 전부 롤백 | 청크 단위 커밋. 언제든 멈출 수 있다 |
# | 어디까지 했는지 남긴다 | 재시도가 항상 0부터 ($O(N)$ 재작업) | 죽은 자리에서 재개 ($O(N/k)$ 재작업) |
# | 멱등하게 만든다 | 재시도가 엣지·행을 중복 생성 | 몇 번 돌려도 같은 상태 |
# | 한 번 더 돌린다 | 「100% 완료」인데 헌 값이 남는다 | 백필 중에 바뀐 행을 회수 |
#
# 그리고 마지막 판정은 백필 자신이 하지 않는다.
# 32장 예제 4의 «둘 다 읽고 비교»가 세는 **불일치 건수가 0**이 되어야
# 예제 5의 `dual-read` 게이트를 지나 수축으로 갈 수 있다.
