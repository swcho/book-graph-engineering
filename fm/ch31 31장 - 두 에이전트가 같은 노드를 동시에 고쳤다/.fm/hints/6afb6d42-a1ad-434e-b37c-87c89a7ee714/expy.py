# %% [markdown]
# # 낙관적 잠금에서 충돌은 어떻게 감지되는가
#
# **답: 에러가 아니라 `0행 갱신`으로 온다. `rowcount`를 봐야 한다.**
#
# 이 스크립트는 sqlite3(표준 라이브러리)만으로 다음을 순서대로 보여준다.
#
# 1. 잃어버린 갱신(lost update)이 **예외 없이** 일어나는 모습
# 2. `UPDATE ... WHERE id=? AND version=?` 가 충돌 시 **예외를 안 던지고** `rowcount == 0` 을 돌려주는 모습
# 3. `rowcount` 를 안 보면 충돌이 그대로 「성공」으로 로그에 찍히는 모습
# 4. `rowcount` 를 보고 재시도하는 루프
# 5. 진짜 스레드 경쟁에서의 동작
# 6. `rowcount` 를 쓸 때의 함정들
# 7. 충돌률에 따른 낙관적/비관적 비용 곡선 시각화
#
# 필요 패키지: plotly, kaleido (마지막 시각화 셀에서만 사용. 나머지는 표준 라이브러리만)

# %%
# 필요 패키지: plotly, kaleido  (설치: pip install plotly kaleido)
import random
import sqlite3
import threading
import time


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


DDL = "CREATE TABLE node (id TEXT PRIMARY KEY, props TEXT, version INTEGER);"


def fresh():
    """노드 한 개짜리 인메모리 그래프 저장소. version 칼럼이 핵심이다."""
    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.executescript(DDL)
    db.execute("INSERT INTO node VALUES ('t1', '팀장=박민수;인원=3', 1)")
    db.commit()
    return db


def parse(s):
    return dict(p.split("=") for p in s.split(";") if p)


def dump(d):
    return ";".join(f"{k}={v}" for k, v in sorted(d.items()))


db = fresh()
print(db.execute("SELECT id, props, version FROM node").fetchone())
# 출력: ('t1', '팀장=박민수;인원=3', 1)
# (INSERT 한 문자열이 그대로 나온다. dump() 정렬은 아래에서 쓴다)

# %% [markdown]
# ## 1. 잃어버린 갱신 — 에러가 안 난다
#
# 두 에이전트 A, B 가 **같은 옛 상태를 읽고** 각자 다른 필드를 고친 뒤 **통째로** 쓴다.
# 스레드 없이 순서만 인터리빙해도 결과는 똑같다.

# %%
db = fresh()

# A 가 읽는다
props_a = parse(db.execute("SELECT props FROM node WHERE id='t1'").fetchone()[0])
# B 도 (A 가 쓰기 전에) 읽는다  ← 여기가 창(window)이다
props_b = parse(db.execute("SELECT props FROM node WHERE id='t1'").fetchone()[0])

props_a["팀장"] = "이서연"   # A 의 판단 (모델 호출이라 치자, 느리다)
props_b["인원"] = "5"        # B 의 판단

# A 가 통째로 쓴다
cur_a = db.execute("UPDATE node SET props=? WHERE id='t1'", (dump(props_a),))
# B 가 통째로 쓴다
cur_b = db.execute("UPDATE node SET props=? WHERE id='t1'", (dump(props_b),))
db.commit()

print("A rowcount =", cur_a.rowcount, " B rowcount =", cur_b.rowcount)
print("최종 상태 :", db.execute("SELECT props FROM node WHERE id='t1'").fetchone()[0])
print("예외 발생 : 없음")
# 출력: A rowcount = 1  B rowcount = 1
# 출력: 최종 상태 : 인원=5;팀장=박민수
# 출력: 예외 발생 : 없음
#
# → 「팀장=이서연」이 사라졌다. 둘 다 rowcount 1 (성공)이고 예외도 없다.
#   로그에는 성공만 찍힌다. 이게 잃어버린 갱신의 성질이다.

# %% [markdown]
# ## 2. 낙관적 잠금 — WHERE 절에 version 을 넣는다
#
# $$\text{UPDATE node SET props}=?,\ \text{version}=\text{version}+1
# \quad \text{WHERE id}=?\ \wedge\ \text{version}=v_{\text{read}}$$
#
# 읽을 때의 버전 $v_{\text{read}}$ 를 WHERE 조건에 넣는다.
# 그 사이 누가 고쳤으면 저장된 버전이 $v_{\text{read}}+1$ 이 되어 **WHERE 가 아무 행도 못 찾는다**.
#
# SQL 문법은 완벽하고 트랜잭션도 정상이므로 **DB 는 에러를 낼 이유가 없다.**
# 그냥 「0행을 고쳤다」고 조용히 성공한다. 그 0이 충돌 신호다.

# %%
db = fresh()

# A 와 B 가 같은 시점을 읽는다 (props, version)
pa, va = db.execute("SELECT props, version FROM node WHERE id='t1'").fetchone()
pb, vb = db.execute("SELECT props, version FROM node WHERE id='t1'").fetchone()
print(f"A 가 읽은 version = {va},  B 가 읽은 version = {vb}")

da, dbp = parse(pa), parse(pb)
da["팀장"] = "이서연"
dbp["인원"] = "5"

# A 가 먼저 쓴다 — 버전이 그대로라 성공
cur_a = db.execute(
    "UPDATE node SET props=?, version=version+1 WHERE id='t1' AND version=?",
    (dump(da), va))
db.commit()
print(f"A: rowcount={cur_a.rowcount}  → {'성공' if cur_a.rowcount == 1 else '충돌'}")

# B 가 뒤이어 쓴다 — 버전이 이미 2라 WHERE version=1 이 안 맞는다
cur_b = db.execute(
    "UPDATE node SET props=?, version=version+1 WHERE id='t1' AND version=?",
    (dump(dbp), vb))
db.commit()
print(f"B: rowcount={cur_b.rowcount}  → {'성공' if cur_b.rowcount == 1 else '충돌'}")

print("예외 :", "없음")
print("최종 :", db.execute("SELECT props, version FROM node WHERE id='t1'").fetchone())
# 출력: A 가 읽은 version = 1,  B 가 읽은 version = 1
# 출력: A: rowcount=1  → 성공
# 출력: B: rowcount=0  → 충돌
# 출력: 예외 : 없음
# 출력: 최종 : ('인원=3;팀장=이서연', 2)
#
# → B 의 UPDATE 는 예외를 던지지 않았다. rowcount 가 0 일 뿐이다.
#   try/except 로는 절대 이 충돌을 못 잡는다.

# %% [markdown]
# ## 3. `rowcount` 를 안 보면 어떻게 되나
#
# 낙관적 잠금을 「걸어 놓기만」 하고 반환값을 안 보는 코드는
# 충돌을 **성공으로 로그에 남긴다.** 잃어버린 갱신과 증상이 똑같아진다.

# %%
def write_without_check(db, field, value, ver, props):
    """version 조건은 걸었는데 rowcount 를 안 본다. 흔한 버그."""
    d = parse(props)
    d[field] = value
    db.execute("UPDATE node SET props=?, version=version+1 "
               "WHERE id='t1' AND version=?", (dump(d), ver))
    db.commit()
    return "저장 완료"          # ← 거짓말


db = fresh()
pa, va = db.execute("SELECT props, version FROM node WHERE id='t1'").fetchone()
pb, vb = db.execute("SELECT props, version FROM node WHERE id='t1'").fetchone()

print("A:", write_without_check(db, "팀장", "이서연", va, pa))
print("B:", write_without_check(db, "인원", "5", vb, pb))
print("최종 :", db.execute("SELECT props, version FROM node WHERE id='t1'").fetchone())
# 출력: A: 저장 완료
# 출력: B: 저장 완료
# 출력: 최종 : ('인원=3;팀장=이서연', 2)
#
# → B 의 「인원=5」는 반영되지 않았는데 「저장 완료」라고 보고했다.
#   감지 장치는 있었지만 아무도 눈금을 안 읽었다.

# %% [markdown]
# ## 4. 제대로 된 형태 — rowcount 를 보고 재시도한다
#
# 재시도 횟수의 기댓값은 충돌 확률 $p$ 에 대해
#
# $$E[\text{시도}] = \sum_{k=1}^{\infty} k\,(1-p)p^{\,k-1} = \frac{1}{1-p}$$
#
# 이다. $p$ 가 1에 가까워지면 급격히 발산한다 (마지막 시각화 셀 참고).

# %%
def optimistic_update(db, field, value, lock, stats, delay=0.0, max_tries=5):
    """읽기 → 판단 → (버전 확인 + 쓰기). rowcount 로 충돌을 감지한다."""
    for attempt in range(max_tries):
        with lock:
            props, ver = db.execute(
                "SELECT props, version FROM node WHERE id='t1'").fetchone()
        d = parse(props)
        time.sleep(delay)                       # 판단 시간 (모델 호출 등)
        d[field] = value
        with lock:
            cur = db.execute(
                "UPDATE node SET props=?, version=version+1 "
                "WHERE id='t1' AND version=?", (dump(d), ver))
            db.commit()
            rc = cur.rowcount                   # ★ 여기가 감지 지점
        if rc == 1:
            stats["성공"] += 1
            stats["재시도"] += attempt
            return True
        stats["충돌"] += 1
        time.sleep(random.uniform(0.001, 0.005))   # 지수 백오프 + 흔들기
    stats["포기"] += 1
    return False


LOCK = threading.Lock()
db = fresh()
stats = {"성공": 0, "충돌": 0, "재시도": 0, "포기": 0}

optimistic_update(db, "팀장", "이서연", LOCK, stats)
optimistic_update(db, "인원", "5", LOCK, stats)
print("최종 :", db.execute("SELECT props, version FROM node WHERE id='t1'").fetchone())
print("통계 :", stats)
# 출력: 최종 : ('인원=5;팀장=이서연', 3)
# 출력: 통계 : {'성공': 2, '충돌': 0, '재시도': 0, '포기': 0}
#
# → 순차 실행이라 충돌이 안 났다. 둘 다 반영됐고 version 이 1→3 으로 올랐다.

# %% [markdown]
# ## 5. 진짜 스레드로 경쟁시키기
#
# 판단 시간(`delay`)을 겹치게 만들어 실제 충돌을 유발한다.
# 충돌은 여전히 예외가 아니라 `rowcount == 0` 으로만 나타난다.

# %%
random.seed(31)
db = fresh()
stats = {"성공": 0, "충돌": 0, "재시도": 0, "포기": 0}

jobs = [("팀장", "이서연", 0.20), ("인원", "5", 0.05)]
threads = [threading.Thread(target=optimistic_update,
                           args=(db, f, v, LOCK, stats, d))
           for f, v, d in jobs]
for t in threads:
    t.start()
    time.sleep(0.02)          # 읽는 시점을 겹치게 만든다
for t in threads:
    t.join()

final = db.execute("SELECT props, version FROM node WHERE id='t1'").fetchone()
print("최종 :", final)
print("통계 :", stats)
props = parse(final[0])
print("둘 다 반영 :", props.get("팀장") == "이서연" and props.get("인원") == "5")
# 출력: 최종 : ('인원=5;팀장=이서연', 3)
# 출력: 통계 : {'성공': 2, '충돌': 1, '재시도': 1, '포기': 0}
# 출력: 둘 다 반영 : True
#
# → 충돌 1건이 rowcount==0 으로 감지됐고, 재시도 1회로 둘 다 살았다.
#   (스레드 스케줄링에 따라 충돌 횟수는 실행마다 달라질 수 있다)

# %% [markdown]
# ## 6. `rowcount` 함정 모음
#
# | 상황 | `cursor.rowcount` | 주의 |
# |---|---|---|
# | `SELECT` | `-1` | 조회에는 의미 없는 값 |
# | 조건이 안 맞는 `UPDATE` | `0` | **충돌 신호** |
# | 정상 `UPDATE` | `1` | 성공 |
# | 값이 같아도 WHERE 가 맞음 | `1` | sqlite 는 "matched" 가 아니라 "changed" 를 세지만, WHERE 가 맞으면 재기록되어 1 |
# | 없는 id 를 `UPDATE` | `0` | **충돌과 구별이 안 된다** ← 삭제된 노드인지 버전 충돌인지 따로 확인해야 함 |
# | `executemany` | 누적 합 | 배치에서는 개별 실패를 못 가린다 |
#
# 특히 마지막 두 줄이 중요하다. `rowcount == 0` 만으로는
# 「버전이 바뀌었다」와 「행이 아예 사라졌다」를 구별할 수 없다.

# %%
db = fresh()

cur = db.execute("SELECT * FROM node")
print("SELECT            rowcount =", cur.rowcount)

cur = db.execute("UPDATE node SET props=props WHERE id='t1' AND version=1")
print("조건 맞음          rowcount =", cur.rowcount)

cur = db.execute("UPDATE node SET props=props WHERE id='t1' AND version=999")
print("버전 불일치        rowcount =", cur.rowcount)

cur = db.execute("UPDATE node SET props=props WHERE id='없는노드' AND version=1")
print("행 자체가 없음      rowcount =", cur.rowcount)

cur = db.executemany(
    "UPDATE node SET props=props WHERE id=? AND version=?",
    [("t1", 1), ("t1", 999), ("없는노드", 1)])
print("executemany 3건    rowcount =", cur.rowcount)
db.commit()
# 출력: SELECT            rowcount = -1
# 출력: 조건 맞음          rowcount = 1
# 출력: 버전 불일치        rowcount = 0
# 출력: 행 자체가 없음      rowcount = 0
# 출력: executemany 3건    rowcount = 1
#
# → 0 이 두 가지 원인에서 나온다. 그래서 rowcount==0 을 만나면
#   보통 재조회해서 「행이 있나 / 버전이 몇인가」를 확인한 뒤
#   충돌 재시도인지 삭제 예외인지를 가른다.

# %%
def update_with_diagnosis(db, field, value, ver):
    """rowcount==0 의 원인을 갈라 본다."""
    props = db.execute("SELECT props FROM node WHERE id='t1'").fetchone()
    if props is None:
        return "행 없음(삭제됨)"
    d = parse(props[0])
    d[field] = value
    cur = db.execute("UPDATE node SET props=?, version=version+1 "
                     "WHERE id='t1' AND version=?", (dump(d), ver))
    db.commit()
    if cur.rowcount == 1:
        return "성공"
    row = db.execute("SELECT version FROM node WHERE id='t1'").fetchone()
    if row is None:
        return "삭제됨 → 재시도해도 소용없음"
    return f"버전 충돌 (기대 {ver}, 실제 {row[0]}) → 재시도"


db = fresh()
print(update_with_diagnosis(db, "팀장", "이서연", 1))
print(update_with_diagnosis(db, "인원", "5", 1))     # 이미 2로 올라갔다
db.execute("DELETE FROM node WHERE id='t1'")
db.commit()
print(update_with_diagnosis(db, "인원", "5", 2))
# 출력: 성공
# 출력: 버전 충돌 (기대 1, 실제 2) → 재시도
# 출력: 행 없음(삭제됨)

# %% [markdown]
# ## 7. 시각화 — 충돌률이 오르면 낙관적이 뒤집힌다
#
# 감지 자체는 `rowcount` 한 줄이지만, 감지 **이후 재시도 비용**이 방식의 우열을 가른다.
#
# $$\text{낙관적} = N \cdot \min\!\left(\frac{1}{1-p},\ K\right)\cdot(H + W)$$
# $$\text{비관적} = N \cdot (H + W + L) + N \cdot p \cdot \frac{p}{1-p}(H+W)$$
#
# $H$ = 판단 시간, $W$ = 쓰기 시간, $L$ = 잠금 획득 비용, $K$ = 최대 재시도.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

HOLD_MS, WRITE_MS, LOCK_MS, N_OPS, MAX_TRIES = 12.0, 1.5, 2.2, 1000, 6


def expected_tries(p):
    return 1.0 / (1.0 - p) if p < 1 else float("inf")


def optimistic_cost(p):
    return N_OPS * min(expected_tries(p), MAX_TRIES) * (HOLD_MS + WRITE_MS)


def pessimistic_cost(p):
    total = N_OPS * (HOLD_MS + WRITE_MS + LOCK_MS)
    queue = (p / (1 - p)) * (HOLD_MS + WRITE_MS) if p < 1 else 0.0
    return total + N_OPS * p * queue


ps = [i / 100 for i in range(1, 80)]
opt = [optimistic_cost(p) for p in ps]
pes = [pessimistic_cost(p) for p in ps]
tries = [min(expected_tries(p), MAX_TRIES) for p in ps]

# 교차점 찾기
cross = next((p for p, o, q in zip(ps, opt, pes) if o > q), None)
print("뒤집히는 충돌률 :", f"{cross:.0%}" if cross else "없음")
# 출력: 뒤집히는 충돌률 : 17%

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=("충돌률에 따른 총 비용", "기대 시도 횟수 1/(1-p)"))

fig.add_trace(go.Scatter(x=ps, y=opt, name="낙관적 (rowcount 재시도)",
                         line=dict(color="#2563eb", width=3)), row=1, col=1)
fig.add_trace(go.Scatter(x=ps, y=pes, name="비관적 (선점 잠금)",
                         line=dict(color="#dc2626", width=3)), row=1, col=1)
if cross:
    fig.add_vline(x=cross, line=dict(color="#666", dash="dash"), row=1, col=1)
    fig.add_annotation(x=cross, y=max(opt) * 0.9, text=f"뒤집힘 {cross:.0%}",
                       showarrow=False, xshift=45, row=1, col=1)

fig.add_trace(go.Scatter(x=ps, y=tries, name="E[시도] = 1/(1-p)",
                         line=dict(color="#059669", width=3),
                         showlegend=False), row=1, col=2)
fig.add_hline(y=MAX_TRIES, line=dict(color="#999", dash="dot"), row=1, col=2)

fig.update_xaxes(title_text="충돌률 p", tickformat=".0%", row=1, col=1)
fig.update_xaxes(title_text="충돌률 p", tickformat=".0%", row=1, col=2)
fig.update_yaxes(title_text="총 소요 (ms)", row=1, col=1)
fig.update_yaxes(title_text="시도 횟수", row=1, col=2)
fig.update_layout(
    title="충돌은 rowcount==0 으로 감지된다 — 감지 이후의 비용 곡선",
    template="plotly_white", height=430, width=1000,
    legend=dict(orientation="h", y=-0.2))

_show(fig)
fig.write_image("expy.png", scale=2)
print("saved expy.png")
# 출력: saved expy.png

# %% [markdown]
# ## 정리
#
# - 낙관적 잠금의 충돌은 **예외(exception)로 오지 않는다.** SQL 은 정상이고 트랜잭션도 정상이다.
# - `UPDATE ... WHERE id=? AND version=?` 이 조건에 맞는 행을 못 찾으면
#   **0행을 갱신하고 조용히 성공**한다. 그 0이 유일한 충돌 신호다.
# - 따라서 반드시 `cursor.rowcount`(또는 드라이버별 등가물 — JDBC `executeUpdate()` 반환값,
#   ORM 의 `UPDATE ... RETURNING`, `db.query(...).rowsAffected`)를 확인해야 한다.
# - `rowcount` 를 안 보면 감지 장치를 달아 놓고 안 읽는 셈이라, 잃어버린 갱신과 증상이 같아진다.
# - `rowcount == 0` 은 「버전 충돌」과 「행 삭제됨」 둘 다에서 나온다. 재조회로 갈라야 한다.
# - 감지는 기술 문제라 일반 해법(`rowcount`)이 있지만, 감지 이후의 **해결**은 도메인 문제다.
