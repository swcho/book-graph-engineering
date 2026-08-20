# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# 표준 라이브러리만으로 해시 고리 자체는 재현된다: hashlib, json, sqlite3, unicodedata

# %% [markdown]
# # `ex5_audit_trail.py`의 해시 고리는 어떻게 구성되는가
#
# **답**: 각 항목의 해시를 `seq`·시각·행위자·`op`·`payload`·**앞 해시**로 계산하고,
# 다음 항목이 그 해시를 `prev`로 저장한다.
#
# 즉 $i$번째 항목의 해시는
#
# $$h_i = H\bigl(\text{seq}_i \,\|\, \text{at}_i \,\|\, \text{actor}_i \,\|\, \text{op}_i \,\|\, \text{payload}_i \,\|\, h_{i-1}\bigr)$$
#
# 이고, 첫 항목은 $h_0 = \texttt{"-"}$ 라는 고정 씨앗을 쓴다.
# $H$는 SHA-256이며 앞 16자리(hex)만 잘라 쓴다 → $64$비트.
#
# 여기서 $\|$는 「그냥 이어 붙이기」가 아니라 **정규화된 직렬화**다.
# `ex5`는 여섯 필드를 **JSON 배열 하나**로 묶어 `sort_keys=True`, `ensure_ascii=False`로 덤프한다.
# 왜 그게 중요한지는 아래에서 직접 깨 본다.

# %%
# 장의 ex5 를 그대로 재현한다 (의존성 없음: sqlite3 + hashlib).
import hashlib
import json
import sqlite3

DDL = """
CREATE TABLE log (
  seq   INTEGER PRIMARY KEY,
  at    TEXT, actor TEXT, op TEXT, payload TEXT,
  prev  TEXT,        -- 앞 항목의 해시
  hash  TEXT         -- 이 항목의 해시
);
"""

EVENTS = [
    ("2026-04-01T09:00", "hr-sync",    "추가", {"s": "박민수", "k": "이끔", "o": "결제팀"}),
    ("2026-04-01T09:00", "hr-sync",    "삭제", {"s": "박민수", "k": "이끔", "o": "결제팀"}),
    ("2026-04-01T09:01", "hr-sync",    "추가", {"s": "이서연", "k": "이끔", "o": "결제팀"}),
    ("2026-04-14T11:20", "agent-4821", "추가", {"s": "이서연", "k": "이끔", "o": "정산팀"}),
    ("2026-04-15T08:40", "admin:kim",  "삭제", {"s": "이서연", "k": "이끔", "o": "정산팀"}),
]

SEED = "-"   # h_0. 고리의 시작점


def digest(seq, at, actor, op, payload, prev):
    """해시 입력 = [seq, at, actor, op, payload, prev] 여섯 필드를 정규 직렬화한 것."""
    body = json.dumps([seq, at, actor, op, payload, prev],
                      ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(body.encode()).hexdigest()[:16]


def append(db, at, actor, op, payload):
    row = db.execute("SELECT seq, hash FROM log ORDER BY seq DESC LIMIT 1").fetchone()
    seq = (row[0] + 1) if row else 1
    prev = row[1] if row else SEED          # 앞 항목의 해시를 prev 로 «저장»한다
    h = digest(seq, at, actor, op, payload, prev)
    db.execute("INSERT INTO log VALUES (?,?,?,?,?,?,?)",
               (seq, at, actor, op, json.dumps(payload, ensure_ascii=False), prev, h))
    return seq


def verify(db):
    bad = []
    prev = SEED
    for seq, at, actor, op, payload, p, h in db.execute("SELECT * FROM log ORDER BY seq"):
        want = digest(seq, at, actor, op, json.loads(payload), prev)
        if p != prev:
            bad.append((seq, "앞 고리가 안 맞음"))
        elif h != want:
            bad.append((seq, "내용이 바뀜"))
        prev = h                            # 다음 항목 검증의 기대 prev
    return bad


def dump(db, title):
    print(title)
    print(f"{'seq':>4}  {'시각':<20}{'행위자':<13}{'op':<6}{'앞 고리(prev)':<20}{'해시(hash)'}")
    print("-" * 86)
    for seq, at, actor, op, payload, p, h in db.execute("SELECT * FROM log ORDER BY seq"):
        print(f"{seq:>4}  {at:<20}{actor:<13}{op:<6}{p:<20}{h}")


db = sqlite3.connect(":memory:")
db.executescript(DDL)
for at, actor, op, payload in EVENTS:
    append(db, at, actor, op, payload)
db.commit()

dump(db, "이벤트 5건을 고리로 이어 적었다.\n")
print(f"\n검증: {verify(db) or '이상 없음'}")

# 출력:
# 이벤트 5건을 고리로 이어 적었다.
#
#  seq  시각                  행위자          op    앞 고리(prev)          해시(hash)
# --------------------------------------------------------------------------------------
#    1  2026-04-01T09:00    hr-sync      추가    -                   25b3a28f6c74f499
#    2  2026-04-01T09:00    hr-sync      삭제    25b3a28f6c74f499    c26f3343819833bd
#    3  2026-04-01T09:01    hr-sync      추가    c26f3343819833bd    7624be68113654d2
#    4  2026-04-14T11:20    agent-4821   추가    7624be68113654d2    f8412c5ab022557d
#    5  2026-04-15T08:40    admin:kim    삭제    f8412c5ab022557d    c8a4143730b9f6ed
#
# 검증: 이상 없음
#  → n번의 hash 가 n+1번의 prev 로 그대로 들어가 있다. 이게 «고리»다.

# %% [markdown]
# ## 고리가 성립하는 두 개의 축
#
# | 축 | 무엇을 묶나 | 깨지면 잡히는 것 |
# |---|---|---|
# | **세로(내용)** | 해시 입력에 `seq·at·actor·op·payload`가 들어간다 | 그 항목의 어느 필드든 고치면 `hash`가 안 맞는다 |
# | **가로(순서)** | 해시 입력에 $h_{i-1}$이 들어가고, 그 값이 `prev` 칼럼에도 저장된다 | 항목을 지우거나 순서를 바꾸면 다음 항목의 `prev`가 안 맞는다 |
#
# 한 항목을 고치려면 세로가 깨지고, 그걸 맞추려고 해시를 다시 계산하면
# 그 뒤 전부의 가로가 연쇄로 깨진다. 그래서 「국소적 수정」이 불가능하다.

# %%
# 시나리오 A — 4번 항목의 payload 만 몰래 고친다. 「이서연」 → 「김도현」.
db.execute("UPDATE log SET payload=? WHERE seq=4",
           (json.dumps({"s": "김도현", "k": "이끔", "o": "정산팀"}, ensure_ascii=False),))
db.commit()
bad_modify = verify(db)
print(f"4번 payload 수정 후 검증: {bad_modify}")

# 왜 4번에서만 걸리나 — verify 가 «저장된» hash 를 다음 prev 로 쓰기 때문.
row4 = db.execute("SELECT * FROM log WHERE seq=4").fetchone()
print(f"  저장된 hash : {row4[6]}")
print(f"  재계산 hash : {digest(4, row4[1], row4[2], row4[3], json.loads(row4[4]), row4[5])}")

# 출력:
# 4번 payload 수정 후 검증: [(4, '내용이 바뀜')]
#   저장된 hash : f8412c5ab022557d
#   재계산 hash : bac8471bbfbc2f7d
#  → 세로 축이 깨졌다. payload 한 글자만 달라도 재계산 해시가 완전히 달라진다.

# %%
# 시나리오 B — 되돌린 뒤, 3번 항목을 통째로 지운다.
db.execute("UPDATE log SET payload=? WHERE seq=4",
           (json.dumps({"s": "이서연", "k": "이끔", "o": "정산팀"}, ensure_ascii=False),))
db.execute("DELETE FROM log WHERE seq=3")
db.commit()
bad_delete = verify(db)
print(f"3번 항목 삭제 후 검증: {bad_delete}")

row4 = db.execute("SELECT * FROM log WHERE seq=4").fetchone()
row2 = db.execute("SELECT * FROM log WHERE seq=2").fetchone()
print(f"  4번이 들고 있는 prev : {row4[5]}   (지워진 3번의 해시)")
print(f"  검증기가 기대한 prev : {row2[6]}   (남아 있는 2번의 해시)")
dump(db, "\n남은 표:\n")

# 출력:
# 3번 항목 삭제 후 검증: [(4, '앞 고리가 안 맞음')]
#   4번이 들고 있는 prev : 7624be68113654d2   (지워진 3번의 해시)
#   검증기가 기대한 prev : c26f3343819833bd   (남아 있는 2번의 해시)
#
# 남은 표:
#
#  seq  시각                  행위자          op    앞 고리(prev)          해시(hash)
# --------------------------------------------------------------------------------------
#    1  2026-04-01T09:00    hr-sync      추가    -                   25b3a28f6c74f499
#    2  2026-04-01T09:00    hr-sync      삭제    25b3a28f6c74f499    c26f3343819833bd
#    4  2026-04-14T11:20    agent-4821   추가    7624be68113654d2    f8412c5ab022557d
#    5  2026-04-15T08:40    admin:kim    삭제    f8412c5ab022557d    c8a4143730b9f6ed
#  → 지워진 항목의 해시가 «다음 항목 안에» 화석처럼 남아 있어서 구멍이 드러난다.
#    삭제는 흔적을 지우는 게 아니라 구멍을 «만든다».

# %% [markdown]
# ### 잡히는 지점이 딱 한 곳인 이유 (그리고 그 대가)
#
# `ex5`의 `verify`는 다음 라운드의 기대값으로 **재계산한 해시가 아니라 저장된 `h`**를 쓴다
# (`prev = h`). 그래서 위반이 한 줄에서 멈추고 뒤로 번지지 않는다 —
# 「어디가 처음 깨졌나」를 바로 짚어 주므로 사고 조사에 좋다.
#
# 대신 이 검증기는 「$i$번이 깨졌으면 $i$번 이후는 전부 신뢰할 수 없다」는 판단을
# 스스로 내려 주지 않는다. 그 판단은 읽는 사람 몫이다.
# 반대로 `prev = want`로 chaining 하면 위반이 뒤로 전부 번져서
# 「신뢰 경계」는 명확해지지만 최초 지점을 찾기 어려워진다. 취향이 아니라 용도의 문제다.

# %% [markdown]
# ## 왜 «정규화된 직렬화»인가
#
# 해시는 **바이트**를 먹는다. 사람 눈에 같은 값이라도 바이트가 다르면 해시가 다르다.
# 감사 로그에서 이건 치명적이다 — 정직한 검증기가 「위조됐다」고 오탐하거나,
# 반대로 공격자가 **의미가 다른 두 기록을 같은 해시**로 만들 수 있다.
#
# `ex5`가 고른 방어는 두 겹이다.
#
# 1. 여섯 필드를 **JSON 배열**로 감싼다 → 필드 경계가 구조로 박힌다.
# 2. `sort_keys=True` → `payload` 딕셔너리의 키 순서가 바뀌어도 같은 바이트.
#
# 아래에서 각각이 없으면 어떻게 되는지 실제로 만들어 본다.

# %%
# (1) 필드 경계 — 그냥 이어 붙이면 «다른 기록»이 «같은 해시»가 된다.
def naive(seq, at, actor, op, payload, prev):
    return hashlib.sha256(
        f"{seq}{at}{actor}{op}{payload}{prev}".encode()).hexdigest()[:16]

A = (1, "2026-04-01T09:00", "admin", ":kim", {}, "-")   # actor="admin", op=":kim"
B = (1, "2026-04-01T09:00", "admin:kim", "", {}, "-")   # actor="admin:kim", op=""
print("[경계 없는 이어붙이기]")
print(f"  A actor='admin'     op=':kim' -> {naive(*A)}")
print(f"  B actor='admin:kim' op=''     -> {naive(*B)}")
print(f"  같은 해시인가? {naive(*A) == naive(*B)}   ← 행위자 세탁이 공짜로 된다")
print("[ex5 방식: JSON 배열]")
print(f"  A -> {digest(*A)}")
print(f"  B -> {digest(*B)}")
print(f"  같은 해시인가? {digest(*A) == digest(*B)}")

# 출력:
# [경계 없는 이어붙이기]
#   A actor='admin'     op=':kim' -> b4d9996072774891
#   B actor='admin:kim' op=''     -> b4d9996072774891
#   같은 해시인가? True   ← 행위자 세탁이 공짜로 된다
# [ex5 방식: JSON 배열]
#   A -> 3c583e90d35bafec
#   B -> 2525a706cf320ce4
#   같은 해시인가? False

# %%
# (2) 키 순서 — sort_keys 가 없으면 «같은 기록»이 «다른 해시»가 된다(오탐).
p1 = {"s": "이서연", "k": "이끔", "o": "정산팀"}
p2 = {"o": "정산팀", "k": "이끔", "s": "이서연"}   # 의미상 완전히 동일


def unsorted_digest(seq, at, actor, op, payload, prev):
    body = json.dumps([seq, at, actor, op, payload, prev], ensure_ascii=False)
    return hashlib.sha256(body.encode()).hexdigest()[:16]


args1 = (4, "2026-04-14T11:20", "agent-4821", "추가", p1, "f4b81f37c0d3a5d6")
args2 = (4, "2026-04-14T11:20", "agent-4821", "추가", p2, "f4b81f37c0d3a5d6")
print(f"sort_keys 없음: {unsorted_digest(*args1)} vs {unsorted_digest(*args2)} "
      f"-> 같은가? {unsorted_digest(*args1) == unsorted_digest(*args2)}")
print(f"sort_keys 있음: {digest(*args1)} vs {digest(*args2)} "
      f"-> 같은가? {digest(*args1) == digest(*args2)}")

# 출력:
# sort_keys 없음: c4ebd38491e4cd9d vs 86e7c92f50c13b6b -> 같은가? False
# sort_keys 있음: 7fa669dd071a9ec6 vs 7fa669dd071a9ec6 -> 같은가? True
#  → JSON 은 객체 키 순서를 «의미 없음»으로 규정한다. 직렬화가 그 규정을 반영해야
#    ORM/드라이버가 키 순서를 바꿔도 검증이 통과한다.

# %%
# (3) ex5 의 정규화가 «커버하지 못하는» 구멍들 — 실제 운영에서 물리는 곳.
import unicodedata

nfc = "이서연"                                  # 완성형 (NFC)
nfd = unicodedata.normalize("NFD", nfc)         # 자모 분해 (NFD)
print(f"보이는 값 동일: {nfc!r} == {nfd!r} ? {nfc == nfd}   "
      f"(코드포인트 {len(nfc)} vs {len(nfd)})")
d_nfc = digest(4, "2026-04-14T11:20", "a", "추가", {"s": nfc}, "-")
d_nfd = digest(4, "2026-04-14T11:20", "a", "추가", {"s": nfd}, "-")
print(f"  해시: {d_nfc} vs {d_nfd} -> 같은가? {d_nfc == d_nfd}")
print("  ← macOS 파일 경로/일부 IME 는 NFD 로 준다. 유니코드 정규화(NFC)를 «해시 전에» 해야 한다.\n")

print(f"ensure_ascii 차이 : {digest(1, 'x', 'a', '추가', {'s': '가'}, '-')} vs "
      f"{hashlib.sha256(json.dumps([1, 'x', 'a', '추가', {'s': '가'}, '-'], sort_keys=True).encode()).hexdigest()[:16]}")
print("  ← ensure_ascii 옵션 하나만 달라도 전혀 다른 해시. 구현끼리 «합의»가 필요하다.\n")

print(f"float 표현      : {digest(1, 'x', 'a', '추가', {'c': 0.1 + 0.2}, '-')} vs "
      f"{digest(1, 'x', 'a', '추가', {'c': 0.3}, '-')}")
print("  ← 0.1+0.2 != 0.3. 확신도 같은 float 를 payload 에 넣으면 언어/런타임마다 갈린다.\n")

print(f"해시 길이       : 16 hex = 64비트. 생일 문제로 충돌 기대 ~2^32 ≈ {2**32:,} 항목")
print("  ← 교재용 축약이다. 실제 감사 로그는 자르지 말고 64 hex(256비트) 전체를 쓴다.")

# 출력:
# 보이는 값 동일: '이서연' == '이서연' ? False   (코드포인트 3 vs 7)
#   해시: 146344735f7262be vs a484a09bfebc7c43 -> 같은가? False
#   ← macOS 파일 경로/일부 IME 는 NFD 로 준다. 유니코드 정규화(NFC)를 «해시 전에» 해야 한다.
#
# ensure_ascii 차이 : a85c170d4751df3a vs 9e6a716b95e74702
#   ← ensure_ascii 옵션 하나만 달라도 전혀 다른 해시. 구현끼리 «합의»가 필요하다.
#
# float 표현      : f94e6755c2291682 vs 83ce3b04f611b243
#   ← 0.1+0.2 != 0.3. 확신도 같은 float 를 payload 에 넣으면 언어/런타임마다 갈린다.
#
# 해시 길이       : 16 hex = 64비트. 생일 문제로 충돌 기대 ~2^32 ≈ 4,294,967,296 항목
#   ← 교재용 축약이다. 실제 감사 로그는 자르지 말고 64 hex(256비트) 전체를 쓴다.

# %% [markdown]
# ## RFC 6962(Certificate Transparency) 계열과 무엇이 다른가
#
# 장의 키워드 표는 「해시 고리 — [표준] — RFC 6962」로 적고 있지만,
# RFC 6962가 정의하는 것은 **선형 해시 고리가 아니라 머클 해시 트리(Merkle Hash Tree)**다.
# 둘 다 「추가 전용 로그의 위변조를 드러낸다」는 목적은 같고, 성질이 다르다.
#
# | | `ex5`의 선형 해시 고리 | RFC 6962 머클 트리 |
# |---|---|---|
# | 구조 | $h_i = H(\text{record}_i \| h_{i-1})$ | 리프를 두 개씩 묶어 올리는 이진 트리, 루트 = MTH |
# | 포함 증명 | 없음. **전체를 다시 훑어야** 확인된다 → $O(n)$ | audit path $O(\log n)$ 노드만 받으면 증명 |
# | 일관성 증명 | 없음. 「예전 로그가 지금 로그의 접두사다」를 짧게 못 보인다 | consistency proof $O(\log n)$ |
# | 도메인 분리 | 없음 | 리프 앞에 `0x00`, 내부 노드 앞에 `0x01` 바이트를 붙여 리프/노드 혼동 공격 차단 |
# | 서명 | 없음 | STH(Signed Tree Head)를 로그 운영자 키로 서명 |
# | 외부 고정 | 없음 (장 본문: 「해시를 밖에 내보내야 한다」) | 여러 감시자(monitor·auditor)가 STH를 교차 검증 |
# | 해시 폭 | SHA-256을 64비트로 절단 | SHA-256 전체 |
#
# **핵심 차이 한 줄**: 선형 고리는 「내가 로그 전체를 갖고 있을 때 훼손을 알아챌 수 있다」는 성질이고,
# 머클 트리는 「로그 전체를 갖고 있지 않은 제3자에게도 짧은 증명으로 납득시킬 수 있다」는 성질이다.
#
# 그리고 장 본문이 못 박은 대로, 둘 중 어느 쪽도 위변조를 **막지** 않는다. **표가 나게** 할 뿐이다.
# 고리는 전부 다시 계산하면 일관된 위조본이 되므로, 진짜 방어는 해시를 바깥에 고정(anchoring)하는 것이다.

# %%
# 고리를 전부 다시 계산하면 «일관된 위조본»이 된다 — 왜 외부 고정이 필요한가.
def rechain(db):
    rows = list(db.execute("SELECT seq, at, actor, op, payload FROM log ORDER BY seq"))
    prev = SEED
    for seq, at, actor, op, payload in rows:
        h = digest(seq, at, actor, op, json.loads(payload), prev)
        db.execute("UPDATE log SET prev=?, hash=? WHERE seq=?", (prev, h, seq))
        prev = h
    return prev   # 마지막 해시 = 로그 전체의 «지문»


forged = sqlite3.connect(":memory:")
forged.executescript(DDL)
for at, actor, op, payload in EVENTS:
    append(forged, at, actor, op, payload)
tip_before = forged.execute("SELECT hash FROM log ORDER BY seq DESC LIMIT 1").fetchone()[0]

forged.execute("UPDATE log SET actor='hr-sync' WHERE seq=4")   # 에이전트 흔적 지우기
tip_after = rechain(forged)
forged.commit()
print(f"위조 후 재계산 검증: {verify(forged) or '이상 없음'}   ← 내부 검증은 통과한다!")
print(f"  어제 외부에 적어 둔 tip : {tip_before}")
print(f"  오늘 로그의 tip         : {tip_after}")
print(f"  일치? {tip_before == tip_after}   ← 밖에 적어 둔 값 하나가 위조를 잡는다")

# 출력:
# 위조 후 재계산 검증: 이상 없음   ← 내부 검증은 통과한다!
#   어제 외부에 적어 둔 tip : c8a4143730b9f6ed
#   오늘 로그의 tip         : 6e021559225c6c51
#   일치? False   ← 밖에 적어 둔 값 하나가 위조를 잡는다

# %% [markdown]
# ## 시각화
#
# 세 가지 상태를 같은 좌표계에 그린다.
#
# 1. **정상** — $h_i$가 다음 칸의 `prev`로 그대로 흘러간다.
# 2. **4번 payload 수정** — 세로 축(내용)이 깨져 그 칸에서 `hash != want`.
# 3. **3번 삭제** — 가로 축(순서)이 끊겨 4번의 `prev`가 허공을 가리킨다.

# %%
import plotly.graph_objects as go


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


OK, BAD, GHOST = "#2c7fb8", "#d7301f", "#bdbdbd"

# (제목, 표시할 seq 목록, {seq: 사유})
SCENES = [
    ("① 정상: 고리가 이어진다", [1, 2, 3, 4, 5], {}),
    ("② seq=4 payload 수정 → 내용이 바뀜", [1, 2, 3, 4, 5], {4: "hash ≠ 재계산"}),
    ("③ seq=3 삭제 → 앞 고리가 안 맞음", [1, 2, 4, 5], {4: "prev 가 허공"}),
]

fig = go.Figure()
for r, (title, seqs, bads) in enumerate(SCENES):
    y = -r * 1.05
    # x 좌표는 «원래 seq 자리»로 고정한다 → 지워진 항목이 «구멍»으로 보인다
    xs = {s: s - 1 for s in seqs}
    fig.add_annotation(x=-0.85, y=y + 0.40, text=f"<b>{title}</b>", xref="x", yref="y",
                       showarrow=False, xanchor="left", font=dict(size=13))
    if r == 2:   # 지워진 3번 자리를 유령 상자로
        fig.add_shape(type="rect", x0=2 - 0.34, x1=2 + 0.34, y0=y - 0.2, y1=y + 0.2,
                      line=dict(color=GHOST, width=2, dash="dot"), fillcolor="rgba(0,0,0,0)")
        fig.add_annotation(x=2, y=y, text="<i>seq 3</i><br><sub>삭제됨</sub>",
                           showarrow=False, font=dict(size=10, color=GHOST))
    for i, s in enumerate(seqs):
        bad = s in bads
        x = xs[s]
        fig.add_shape(type="rect", x0=x - 0.34, x1=x + 0.34, y0=y - 0.2, y1=y + 0.2,
                      line=dict(color=BAD if bad else OK, width=3 if bad else 2),
                      fillcolor="rgba(215,48,31,0.12)" if bad else "rgba(44,127,184,0.10)")
        fig.add_annotation(x=x, y=y, text=f"seq {s}<br><sub>h<sub>{s}</sub></sub>",
                           showarrow=False, font=dict(size=11))
        if bad:
            fig.add_annotation(x=x, y=y - 0.31, text=bads[s], showarrow=False,
                               font=dict(size=10, color=BAD))
        if i == 0:
            continue
        gap = s - seqs[i - 1] != 1          # 고리 자체가 끊긴 곳(=삭제)
        x0 = xs[seqs[i - 1]] + 0.34
        ay = y + 0.32 if gap else y         # 구멍 위로 우회시켜 겹침을 피한다
        fig.add_annotation(x=x - 0.34, y=ay, ax=x0, ay=ay,
                           xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=3, arrowsize=1.1, arrowwidth=2,
                           arrowcolor=BAD if gap else OK, text="")
        fig.add_annotation(x=(x0 + x - 0.34) / 2, y=ay + 0.15,
                           text="prev 불일치" if gap else "prev", showarrow=False,
                           font=dict(size=9, color=BAD if gap else OK))

fig.add_annotation(x=-0.85, y=-2.82, xanchor="left", showarrow=False, align="left",
                   font=dict(size=11, color="#444"),
                   text="② 는 <b>세로</b>(내용) 축이 깨진 것 — 상자는 제자리인데 hash 가 안 맞는다.<br>"
                        "③ 은 <b>가로</b>(순서) 축이 깨진 것 — seq 4 의 prev 가 사라진 seq 3 의 해시를 가리킨다.")

fig.update_layout(
    title="해시 고리: h<sub>i</sub> = H(seq · at · actor · op · payload · h<sub>i-1</sub>)"
          " — 고친 곳과 지운 곳이 어디서 잡히나",
    xaxis=dict(visible=False, range=[-1.0, 4.7]),
    yaxis=dict(visible=False, range=[-3.05, 0.7]),
    showlegend=False, width=1000, height=540,
    plot_bgcolor="white", paper_bgcolor="white", margin=dict(l=20, r=20, t=70, b=20),
)

_show(fig)

import os
_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_png, scale=2)
print(f"저장: {_png}")

# 출력:
# 저장: .../a5f2997c-b92c-4101-b288-1d83237ec079/expy.png

# %% [markdown]
# ## 정리
#
# - **구성**: $h_i = H(\text{seq}_i \| \text{at}_i \| \text{actor}_i \| \text{op}_i \| \text{payload}_i \| h_{i-1})$,
#   그리고 그 $h_i$를 다음 행이 `prev` 칼럼에 **저장**한다. 첫 행의 $h_0$는 `"-"`.
# - **$\|$는 정규 직렬화**: JSON 배열 + `sort_keys=True` + `ensure_ascii=False`.
#   경계가 없으면 서로 다른 기록이 같은 해시가 되고, 키 순서를 안 맞추면 정상 기록이 오탐된다.
# - **잡히는 방식**: 고치면 그 항목의 `hash`가 안 맞고(세로), 지우면 다음 항목의 `prev`가 안 맞는다(가로).
# - **한계**: 막지 못하고 표만 낸다. 전부 재계산한 위조본은 내부 검증을 통과하므로,
#   tip 해시를 외부에 고정해야 한다. RFC 6962는 그 위에 머클 트리 + 서명 + 감시자를 얹어
#   제3자에게 $O(\log n)$ 증명까지 제공한다.
