# %% [markdown]
# # 이벤트에는 무엇을 넣어야 하는가
#
# 정답은 **「바뀐 것」(delta)** 이다. **「바뀐 뒤 전체 상태」(snapshot)** 를 넣으면
# 두 가지를 잃는다.
#
# 1. **무엇이 바뀌었는지 모른다** — 전체 상태만 보면 이번에 무엇을 건드렸는지
#    이벤트 자체에는 안 적혀 있다. 앞 상태와 비교(diff)해야만 알 수 있고,
#    앞 상태가 없으면(첫 이벤트, 보존 정책으로 잘린 로그) 영영 못 안다.
# 2. **동시 변경을 못 합친다** — 같은 기준 상태에서 갈라진 두 변경이 있을 때
#    delta 는 서로 다른 필드를 건드렸다면 합칠 수 있지만,
#    snapshot 은 통째로 덮으므로 나중 것이 앞 것을 지운다(lost update).
#
# 기호로 쓰면, 상태 $S$, 이벤트 $e$, 접기 함수(리듀서) $f$ 에 대해
#
# $$ S_n = f(S_{n-1},\, e_n) $$
#
# - delta 이벤트: $e_n = \Delta_n$ 이고 $f$ 는 **적용**이다. $S_n = S_{n-1} \oplus \Delta_n$
# - snapshot 이벤트: $e_n = S_n$ 이고 $f$ 는 **덮어쓰기**다. $S_n = e_n$ (앞 상태를 안 본다)
#
# 즉 snapshot 방식은 $f$ 가 $S_{n-1}$ 을 **버리는** 함수라서 정보가 사라진다.
#
# 필요 패키지: plotly, kaleido (없어도 앞부분 셀은 전부 실행된다)

# %%
import copy
import json

def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# 「이서연」이라는 사람 노드 하나. 이 노드가 시간에 따라 바뀐다.
BASE = {
    "name": "이서연",
    "team": "결제팀",
    "role": "팀원",
    "diet": "채식",
    "phone": "010-0000-0000",
}

print(json.dumps(BASE, ensure_ascii=False, indent=2))
# 출력:
# {
#   "name": "이서연",
#   "team": "결제팀",
#   "role": "팀원",
#   "diet": "채식",
#   "phone": "010-0000-0000"
# }

# %% [markdown]
# ## 1. 같은 변경을 두 가지 방식으로 기록한다
#
# 세 번의 변경(팀 이동, 승진, 식성 갱신)을 그대로 두 로그에 적는다.
# **둘은 「지금 상태」에 대해서는 완전히 같은 답을 낸다.** 차이는 그 다음에 드러난다.

# %%
CHANGES = [
    ("2026-04-01T09:00", "hr-sync",    {"team": "정산팀"}),
    ("2026-04-14T11:20", "admin:kim",  {"role": "이끔"}),
    ("2026-05-20T16:40", "agent-4821", {"diet": "비건"}),
]

def build_logs(base, changes):
    delta_log, snap_log = [], []
    cur = copy.deepcopy(base)
    for i, (at, actor, patch) in enumerate(changes, start=1):
        cur = {**cur, **patch}
        delta_log.append({"seq": i, "at": at, "actor": actor, "set": dict(patch)})
        snap_log.append({"seq": i, "at": at, "actor": actor, "state": copy.deepcopy(cur)})
    return delta_log, snap_log

DELTA_LOG, SNAP_LOG = build_logs(BASE, CHANGES)

def fold_delta(base, log):
    st = copy.deepcopy(base)
    for e in log:
        st.update(e["set"])          # S_n = S_{n-1} ⊕ Δ_n
    return st

def fold_snapshot(base, log):
    st = copy.deepcopy(base)
    for e in log:
        st = copy.deepcopy(e["state"])   # S_n = e_n  (앞 상태를 버린다)
    return st

print("delta  접기 :", fold_delta(BASE, DELTA_LOG))
print("snap   접기 :", fold_snapshot(BASE, SNAP_LOG))
print("같은가       :", fold_delta(BASE, DELTA_LOG) == fold_snapshot(BASE, SNAP_LOG))
# 출력:
# delta  접기 : {'name': '이서연', 'team': '정산팀', 'role': '이끔', 'diet': '비건', 'phone': '010-0000-0000'}
# snap   접기 : {'name': '이서연', 'team': '정산팀', 'role': '이끔', 'diet': '비건', 'phone': '010-0000-0000'}
# 같은가       : True

# %% [markdown]
# ## 2. 「무엇이 바뀌었나」를 물어본다
#
# 감사·사고 조사의 첫 질문이다. delta 로그는 이벤트 **한 건만 보면** 답이 나온다.
# snapshot 로그는 이벤트 한 건만으로는 못 답하고, **앞 이벤트와 diff** 를 떠야 한다.

# %%
def changed_from_delta(log):
    return [(e["seq"], e["actor"], sorted(e["set"])) for e in log]

def changed_from_snapshot(log, base=None):
    out = []
    prev = base                      # base 를 모르면 None
    for e in log:
        if prev is None:
            out.append((e["seq"], e["actor"], "?? 앞 상태 없음"))
        else:
            diff = sorted(k for k in e["state"] if e["state"][k] != prev.get(k))
            out.append((e["seq"], e["actor"], diff))
        prev = e["state"]
    return out

print("[delta]    ", *changed_from_delta(DELTA_LOG), sep="\n  ")
print("\n[snapshot] 앞 상태(base)를 알 때", *changed_from_snapshot(SNAP_LOG, BASE), sep="\n  ")
print("\n[snapshot] 앞 상태가 없을 때(로그가 잘렸다)",
      *changed_from_snapshot(SNAP_LOG, None), sep="\n  ")
# 출력:
# [delta]
#   (1, 'hr-sync', ['team'])
#   (2, 'admin:kim', ['role'])
#   (3, 'agent-4821', ['diet'])
#
# [snapshot] 앞 상태(base)를 알 때
#   (1, 'hr-sync', ['team'])
#   (2, 'admin:kim', ['role'])
#   (3, 'agent-4821', ['diet'])
#
# [snapshot] 앞 상태가 없을 때(로그가 잘렸다)
#   (1, 'hr-sync', '?? 앞 상태 없음')
#   (2, 'admin:kim', ['role'])
#   (3, 'agent-4821', ['diet'])

# %% [markdown]
# 여기까지는 「앞 상태만 있으면 diff 로 되잖아」로 보인다. 하지만 diff 는
# **의도를 복원하지 못한다.** 두 가지가 바로 무너진다.
#
# - **되돌아온 값**: `비건 → 육식 → 비건` 을 거치면 처음과 끝의 diff 는 **빈 집합**이다.
#   그 사이에 에이전트가 건드렸다 되돌려 놓은 사실이 사라진다.
#   (28장의 「에이전트가 넣은 것 중 되돌려진 비율」 지표가 바로 이걸 센다.)
# - **덮어쓴 것과 안 건드린 것의 구별**: 같은 값으로 다시 쓴 것인지,
#   손도 안 댄 것인지 snapshot 은 구분 못 한다.

# %%
START = fold_delta(BASE, DELTA_LOG)          # diet=비건, team=정산팀
NOISY = [
    ("2026-06-01T09:00", "agent-4821", {"diet": "육식"}),
    ("2026-06-01T09:05", "user",       {"diet": "비건"}),   # 사람이 원래대로 되돌림
    ("2026-06-02T10:00", "hr-sync",    {"team": "정산팀"}),  # 같은 값으로 재기록
]
d2, s2 = build_logs(START, NOISY)

print("[delta]    각 이벤트가 스스로 무엇을 했는지 말한다")
for e in d2:
    print(f"  seq{e['seq']} {e['actor']:<12} set={e['set']}")

print("\n[snapshot] 처음과 끝만 diff 하면")
last = s2[-1]["state"]
print("  바뀐 필드:", sorted(k for k in last if last[k] != START[k]) or "없음")
print("  → 에이전트가 diet 를 건드렸다 사람이 되돌린 사실이 통째로 사라졌다")

print("\n[snapshot] seq3 에서 hr-sync 가 실제로 무엇을 썼나:",
      sorted(k for k in s2[2]["state"] if s2[2]["state"][k] != s2[1]["state"][k]) or "없음(= 안 건드린 것과 구별 불가)")
# 출력:
# [delta]    각 이벤트가 스스로 무엇을 했는지 말한다
#   seq1 agent-4821   set={'diet': '육식'}
#   seq2 user         set={'diet': '비건'}
#   seq3 hr-sync      set={'team': '정산팀'}
#
# [snapshot] 처음과 끝만 diff 하면
#   바뀐 필드: 없음
#   → 에이전트가 diet 를 건드렸다 사람이 되돌린 사실이 통째로 사라졌다
#
# [snapshot] seq3 에서 hr-sync 가 실제로 무엇을 썼나: 없음(= 안 건드린 것과 구별 불가)

# %% [markdown]
# ## 3. 동시 변경을 합쳐 본다
#
# 같은 기준 상태 $S_0$ 에서 두 행위자가 **동시에** 갈라져 나온다.
#
# - HR 싱크: `team` 을 바꾼다
# - 에이전트: `diet` 를 바꾼다
#
# 서로 **다른 필드**라 도메인적으로는 충돌이 아니다. 둘 다 살아야 한다.
#
# $$ \text{delta: } S = S_0 \oplus \Delta_A \oplus \Delta_B \qquad
#    \text{snapshot: } S = S_B \;(\text{또는} S_A) $$
#
# delta 는 $\oplus$ 가 필드 단위라 둘 다 반영된다. snapshot 은 통째로 덮으므로
# **어느 순서로 접든 한쪽이 통째로 사라진다.**

# %%
S0 = copy.deepcopy(BASE)

A = {"at": "2026-07-01T10:00", "actor": "hr-sync",    "set": {"team": "정산팀"}}
B = {"at": "2026-07-01T10:00", "actor": "agent-4821", "set": {"diet": "비건"}}

# 각자 자기 쪽에서 만든 「바뀐 뒤 전체 상태」
A_snap = {**S0, **A["set"]}
B_snap = {**S0, **B["set"]}

def merge_delta(base, evs):
    st = copy.deepcopy(base)
    for e in evs:
        st.update(e["set"])
    return st

def merge_snapshot(base, snaps):
    st = copy.deepcopy(base)
    for s in snaps:
        st = copy.deepcopy(s)
    return st

want = {**S0, "team": "정산팀", "diet": "비건"}

for label, got in (
    ("delta  A→B", merge_delta(S0, [A, B])),
    ("delta  B→A", merge_delta(S0, [B, A])),
    ("snap   A→B", merge_snapshot(S0, [A_snap, B_snap])),
    ("snap   B→A", merge_snapshot(S0, [B_snap, A_snap])),
):
    lost = sorted(k for k in want if got[k] != want[k])
    print(f"{label}: team={got['team']:<5} diet={got['diet']:<5} "
          f"{'OK 둘 다 반영' if not lost else '유실: ' + ','.join(lost)}")
# 출력:
# delta  A→B: team=정산팀   diet=비건    OK 둘 다 반영
# delta  B→A: team=정산팀   diet=비건    OK 둘 다 반영
# snap   A→B: team=결제팀   diet=비건    유실: team
# snap   B→A: team=정산팀   diet=채식    유실: diet

# %% [markdown]
# delta 는 **순서를 바꿔도 결과가 같다**(서로 다른 필드라 교환 가능).
# snapshot 은 순서가 답을 바꾸고, 어느 쪽이든 한 필드를 잃는다.
# 게다가 **잃었다는 사실조차 로그에 안 남는다** — snapshot 은 늘 "정상적인 전체 상태"처럼 보인다.
#
# 그리고 delta 는 **같은 필드**를 동시에 건드렸을 때만 진짜 충돌이라고 말할 수 있다.
# snapshot 은 모든 동시 쓰기를 전부 충돌로 만든다.

# %%
def conflict_fields(base, evs):
    """delta 라면 「실제로 겹치는 필드」만 충돌이다."""
    touched = {}
    for e in evs:
        for k, v in e["set"].items():
            touched.setdefault(k, []).append((e["actor"], v))
    return {k: v for k, v in touched.items() if len(v) > 1 and len({x[1] for x in v}) > 1}

C = {"at": "2026-07-01T10:00", "actor": "user", "set": {"diet": "채식"}}

print("A(team) vs B(diet)  충돌 필드:", conflict_fields(S0, [A, B]) or "없음 → 자동 병합 가능")
print("B(diet) vs C(diet)  충돌 필드:", conflict_fields(S0, [B, C]))
print("\nsnapshot 이라면 두 경우 모두 「전체 상태가 다르다」로만 보이고,")
print("어느 것이 진짜 충돌인지 시스템이 구별할 수 없다:",
      B_snap != {**S0, **C['set']})
# 출력:
# A(team) vs B(diet)  충돌 필드: 없음 → 자동 병합 가능
# B(diet) vs C(diet)  충돌 필드: {'diet': [('agent-4821', '비건'), ('user', '채식')]}
#
# snapshot 이라면 두 경우 모두 「전체 상태가 다르다」로만 보이고,
# 어느 것이 진짜 충돌인지 시스템이 구별할 수 없다: True

# %% [markdown]
# ## 4. 값: 로그 크기
#
# delta 이벤트의 크기는 **바꾼 필드 수**에 비례한다. snapshot 이벤트의 크기는
# **상태 전체 크기**에 비례한다. 노드가 $m$ 개 필드를 갖고 이벤트가 $n$ 건이면
#
# $$ \text{delta} \sim O(n \cdot k),\quad \text{snapshot} \sim O(n \cdot m),\quad k \ll m $$
#
# 필드가 많은 노드일수록 격차가 벌어진다. (전체 상태를 통째로 남기는 것 자체가
# 나쁜 건 아니다. 다만 그건 **스냅숏**이고, 이벤트를 대체하는 게 아니라
# 재생을 짧게 하려고 **주기적으로** 곁들이는 것이다.)

# %%
def jbytes(o):
    return len(json.dumps(o, ensure_ascii=False).encode())

WIDTHS = [5, 10, 20, 40, 80]
N_EVENTS = 200
rows = []
for m in WIDTHS:
    state = {f"f{i}": f"값{i:03d}" for i in range(m)}
    d = sum(jbytes({"seq": i, "at": "2026-07-01T10:00", "actor": "hr-sync",
                    "set": {"f0": f"v{i}"}}) for i in range(N_EVENTS))
    s = sum(jbytes({"seq": i, "at": "2026-07-01T10:00", "actor": "hr-sync",
                    "state": {**state, "f0": f"v{i}"}}) for i in range(N_EVENTS))
    rows.append((m, d, s, s / d))

print(f"{'필드수':>6}{'delta(B)':>12}{'snapshot(B)':>14}{'배수':>8}")
for m, d, s, r in rows:
    print(f"{m:>6}{d:>12,}{s:>14,}{r:>7.1f}x")
# 출력:
#    필드수    delta(B)   snapshot(B)      배수
#      5      15,980        29,180     1.8x
#     10      15,980        45,180     2.8x
#     20      15,980        79,180     5.0x
#     40      15,980       147,180     9.2x
#     80      15,980       283,180    17.7x

# %% [markdown]
# ## 5. 시각화
#
# 왼쪽: 로그 크기 증가. 오른쪽: 동시 변경 병합 결과(살아남은 필드 수).

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("로그 크기 (200건 기록 시)", "동시 변경 A(team)+B(diet) 병합 결과"),
    )

    fig.add_trace(go.Scatter(x=[r[0] for r in rows], y=[r[1] for r in rows],
                             mode="lines+markers", name="delta (바뀐 것)",
                             line=dict(color="#2E86DE", width=3)), row=1, col=1)
    fig.add_trace(go.Scatter(x=[r[0] for r in rows], y=[r[2] for r in rows],
                             mode="lines+markers", name="snapshot (전체 상태)",
                             line=dict(color="#EE5A24", width=3)), row=1, col=1)

    labels = ["delta A→B", "delta B→A", "snap A→B", "snap B→A"]
    kept = []
    for got in (merge_delta(S0, [A, B]), merge_delta(S0, [B, A]),
                merge_snapshot(S0, [A_snap, B_snap]), merge_snapshot(S0, [B_snap, A_snap])):
        kept.append(sum(1 for k in ("team", "diet") if got[k] == want[k]))
    fig.add_trace(go.Bar(x=labels, y=kept, name="반영된 변경 수",
                         marker_color=["#2E86DE", "#2E86DE", "#EE5A24", "#EE5A24"],
                         text=[f"{v}/2" for v in kept], textposition="outside",
                         showlegend=False), row=1, col=2)

    fig.update_xaxes(title_text="노드의 필드 수 m", row=1, col=1)
    fig.update_yaxes(title_text="누적 바이트", row=1, col=1)
    fig.update_yaxes(title_text="살아남은 변경 (최대 2)", range=[0, 2.6], row=1, col=2)
    fig.update_layout(title_text="이벤트에 「바뀐 것」을 넣을 때 vs 「전체 상태」를 넣을 때",
                      width=1000, height=460, template="plotly_white")

    _show(fig)
    fig.write_image("expy.png", scale=2)
    print("expy.png 저장 완료")
except ImportError as e:
    print("plotly/kaleido 없음 — 시각화 생략:", e)
# 출력:
# expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# | | delta (「바뀐 것」) | snapshot (「바뀐 뒤 전체 상태」) |
# |---|---|---|
# | 무엇이 바뀌었나 | 이벤트 한 건이 스스로 말한다 | 앞 상태와 diff 해야 하고, 되돌린 변경은 소실 |
# | 누가 무엇을 건드렸나 | 그대로 나온다 | 같은 값 재기록 = 안 건드림, 구별 불가 |
# | 동시 변경 병합 | 다른 필드면 자동 병합, 순서 무관 | 통째로 덮음 → 한쪽 유실, 순서가 답을 바꿈 |
# | 진짜 충돌 판별 | 겹치는 필드만 충돌 | 모든 동시 쓰기가 충돌처럼 보임 |
# | 로그 크기 | $O(n \cdot k)$ | $O(n \cdot m)$ |
#
# 전체 상태를 저장하는 일 자체를 금지하는 게 아니다. 그건 **스냅숏**의 역할이고,
# 재생 시간을 상한으로 묶기 위해 **주기적으로** 찍는 것이다.
# **이벤트**는 어디까지나 「바뀐 것」이어야 한다.
