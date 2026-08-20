# %% [markdown]
# # `ex1_lost_update.py` 의 시나리오
#
# **질문**: `ex1_lost_update.py`의 시나리오는 무엇인가?
#
# **답**: 에이전트 A가 팀장을 **이서연**으로(판단 0.20초), B가 인원을 **5**로(판단 0.05초)
# 동시에 고친다. **서로 다른 필드**인데도 하나가 사라진다.
#
# 노드 `t1` 의 초기 상태는 `팀장=박민수;인원=3` 이고, 두 에이전트는 각각
# 「**읽고 → 판단하고 → 통째로 쓴다**」를 한다. 판단하는 동안 남이 끼어들 수 있으므로
# 나중에 쓴 쪽이 앞 쪽의 변경을 통째로 덮어 버린다. 이것이 **잃어버린 갱신(lost update)** 이다.
#
# 핵심은 「같은 필드를 다퉈서」 사라지는 게 아니라는 점이다. `팀장` 과 `인원` 은
# 겹치지 않는 필드인데도, **쓰기 단위가 노드 전체**이기 때문에 서로를 덮는다.
#
# 필요 패키지: plotly, kaleido (시각화용). sqlite3 / threading 은 표준 라이브러리.

# %%
# 필요 패키지: plotly, kaleido  (없으면 시각화 셀만 건너뛴다)
import os
import sqlite3
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


DDL = """
CREATE TABLE node (
  id      TEXT PRIMARY KEY,
  props   TEXT,
  version INTEGER
);
"""


def fresh():
    """노드 t1 하나짜리 인메모리 DB. 초기 상태는 팀장=박민수;인원=3."""
    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.executescript(DDL)
    db.execute("INSERT INTO node VALUES ('t1', '팀장=박민수;인원=3', 1)")
    db.commit()
    return db


def parse(s):
    return dict(p.split("=") for p in s.split(";") if p)


def dump(d):
    return ";".join(f"{k}={v}" for k, v in sorted(d.items()))


print(dump(parse("팀장=박민수;인원=3")))
# 출력: 인원=3;팀장=박민수


# %% [markdown]
# ## 1. 「읽고 → 판단하고 → 통째로 쓰기」
#
# `naive_update` 는 에이전트 한 명의 동작이다. `LOCK` 은 SQLite 커넥션을 여러 스레드가
# 동시에 건드리지 않게 하는 **커넥션 보호용**일 뿐이다. 읽기와 쓰기 **사이**는 잠겨 있지
# 않다. 실무의 잠금도 대개 이렇다 — 판단(모델 호출)을 잠금 안에 넣을 수 없으니까.
#
# 시간축을 그리기 위해 각 구간(read / think / write)의 시각을 함께 기록한다.

# %%
LOCK = threading.Lock()


def naive_update(db, field, value, delay, log, spans, t0):
    """읽고 → 고치고 → 쓴다. 그 사이에 남이 끼어들 수 있다."""
    r0 = time.time()
    with LOCK:
        row = db.execute("SELECT props FROM node WHERE id='t1'").fetchone()
    r1 = time.time()
    props = parse(row[0])
    log.append(f"  [{field}] 읽음: {row[0]}")

    time.sleep(delay)                      # 판단하는 시간 (모델 호출이라고 생각하자)
    w0 = time.time()

    props[field] = value
    with LOCK:
        db.execute("UPDATE node SET props=? WHERE id='t1'", (dump(props),))
        db.commit()
    w1 = time.time()
    log.append(f"  [{field}] 씀:   {dump(props)}")

    spans.append((field, "read", r0 - t0, r1 - t0))
    spans.append((field, "think", r1 - t0, w0 - t0))
    spans.append((field, "write", w0 - t0, w1 - t0))


def run(plan, stagger=0.02):
    """plan = [(필드, 값, 판단시간), ...]  — 진짜 스레드로 경쟁시킨다."""
    db = fresh()
    log, spans = [], []
    t0 = time.time()
    ts = [threading.Thread(target=naive_update, args=(db, f, v, d, log, spans, t0))
          for f, v, d in plan]
    for t in ts:
        t.start()
        time.sleep(stagger)                # 읽는 시점을 겹치게 만든다
    for t in ts:
        t.join()
    final = db.execute("SELECT props FROM node WHERE id='t1'").fetchone()[0]
    return log, final, spans


# %% [markdown]
# ## 2. 시나리오 실행 — A(팀장, 0.20초) vs B(인원, 0.05초)

# %%
PLAN = [("팀장", "이서연", 0.20), ("인원", "5", 0.05)]

print("한 노드의 «서로 다른 필드»를 두 에이전트가 동시에 고친다.\n")
print("  에이전트 A: 팀장 = 이서연   (판단에 0.20초)")
print("  에이전트 B: 인원 = 5       (판단에 0.05초)\n")

log, final, spans = run(PLAN)
for line in log:
    print(line)
print(f"\n최종 상태: {final}")
# 출력:
# 한 노드의 «서로 다른 필드»를 두 에이전트가 동시에 고친다.
#
#   에이전트 A: 팀장 = 이서연   (판단에 0.20초)
#   에이전트 B: 인원 = 5       (판단에 0.05초)
#
#   [팀장] 읽음: 팀장=박민수;인원=3
#   [인원] 읽음: 팀장=박민수;인원=3      <- B도 «같은 옛 상태»를 읽었다
#   [인원] 씀:   인원=5;팀장=박민수      <- B가 먼저 쓴다 (0.05초)
#   [팀장] 씀:   인원=3;팀장=이서연      <- A가 나중에 덮는다 (0.20초)
#
# 최종 상태: 인원=3;팀장=이서연

# %%
props = parse(final)
print(f"팀장 = {props['팀장']}, 인원 = {props['인원']}")

lost = []
if props["팀장"] != "이서연":
    lost.append("팀장 변경")
if props["인원"] != "5":
    lost.append("인원 변경")
print(f"사라진 변경: {lost or '없음'}")
# 출력:
# 팀장 = 이서연, 인원 = 3
# 사라진 변경: ['인원 변경']

# %% [markdown]
# 두 에이전트가 **다른 필드**를 고쳤는데 하나가 사라졌다.
#
# 순서를 보면 답이 나온다. 둘 다 **같은 옛 상태**(`팀장=박민수;인원=3`)를 읽었다.
# 그다음 각자 자기 필드만 고쳐서 **통째로** 썼다. 나중에 쓴 쪽(A)이 앞 쪽(B)의 변경을
# 덮는다. B의 `인원=5` 는 A의 손에 들려 있던 옛 값 `인원=3` 으로 되돌아간다.
#
# **에러가 안 난다.** `UPDATE` 는 성공하고 로그에도 「성공」만 찍힌다. 그게 이 문제의
# 성질이다 — 조용히 틀린다.
#
# 30장에서 「전체 상태를 이벤트에 넣지 마라」고 한 이유가 이것이다.
# 전체를 쓰면 **겹치지 않는 변경도 서로를 덮는다**.

# %% [markdown]
# ## 3. 왜 사라지는가 — 시간축으로 보기
#
# 스레드 시작이 `stagger` 만큼 어긋나 있고 판단 시간이 서로 다르므로, 각 에이전트의
# 구간은 이렇게 배치된다. $t=0$ 을 A의 시작으로 두고 $s$ 를 stagger, $d_A, d_B$ 를 판단 시간이라 하면
#
# $$\text{A: read}\approx 0,\quad \text{A: write}\approx d_A \qquad
#   \text{B: read}\approx s,\quad \text{B: write}\approx s + d_B$$
#
# **손실 조건**은 「남의 쓰기보다 먼저 읽고, 남보다 나중에 쓴다」이다.
#
# $$s < d_A \;\land\; d_A > s + d_B \;\Rightarrow\; \text{B의 변경이 사라진다}$$
# $$s < d_A \;\land\; d_A < s + d_B \;\Rightarrow\; \text{A의 변경이 사라진다}$$
# $$d_A < s \;\Rightarrow\; \text{겹치지 않는다. 손실 없음}$$
#
# 이 시나리오는 $s=0.02,\ d_A=0.20,\ d_B=0.05$ 이므로 첫 번째 경우 — **B(인원)가 사라진다**.

# %%
for f, phase, a, b in sorted(spans, key=lambda x: x[2]):
    print(f"  {f:>3} {phase:<6} {a:6.3f}s → {b:6.3f}s  (길이 {b - a:.3f}s)")
# 출력:
#   팀장 read    0.000s →  0.000s  (길이 0.000s)
#   팀장 think   0.000s →  0.203s  (길이 0.203s)
#   인원 read    0.024s →  0.024s  (길이 0.000s)
#   인원 think   0.024s →  0.079s  (길이 0.055s)
#   인원 write   0.079s →  0.079s  (길이 0.000s)
#   팀장 write   0.203s →  0.203s  (길이 0.000s)
# (실행마다 ms 단위로 흔들리지만 «인원 변경이 사라진다»는 결과는 그대로다)

# %% [markdown]
# ## 4. 판단 시간을 바꿔가며 — 언제 누가 사라지나
#
# A의 판단 시간 $d_A$ 만 0초부터 0.15초까지 훑는다. $d_B=0.05,\ s=0.02$ 고정.
# 앞의 부등식대로 **경계는 $d_A = s = 0.02$ 와 $d_A = s + d_B = 0.07$** 두 곳에 있어야 한다.

# %%
def probe(da, db_delay=0.05, stagger=0.02):
    _, fin, _ = run([("팀장", "이서연", da), ("인원", "5", db_delay)], stagger=stagger)
    p = parse(fin)
    if p["팀장"] == "이서연" and p["인원"] == "5":
        return "손실 없음"
    if p["팀장"] != "이서연":
        return "A(팀장) 사라짐"
    return "B(인원) 사라짐"


DAS = [0.00, 0.01, 0.015, 0.03, 0.05, 0.065, 0.08, 0.10, 0.15]
sweep = [(da, probe(da)) for da in DAS]
for da, verdict in sweep:
    print(f"  A의 판단 {da:5.3f}s → {verdict}")
# 출력:
#   A의 판단 0.000s → 손실 없음
#   A의 판단 0.010s → 손실 없음
#   A의 판단 0.015s → 손실 없음
#   A의 판단 0.030s → A(팀장) 사라짐
#   A의 판단 0.050s → A(팀장) 사라짐
#   A의 판단 0.065s → A(팀장) 사라짐
#   A의 판단 0.080s → B(인원) 사라짐
#   A의 판단 0.100s → B(인원) 사라짐
#   A의 판단 0.150s → B(인원) 사라짐

# %% [markdown]
# 예측한 두 경계($0.02$, $0.07$)에서 정확히 결과가 갈린다.
#
# 그리고 **판단이 짧을 때만 안전하다**. 에이전트 시스템에서 판단은 모델 호출이라
# 수백 ms ~ 수 초다. 즉 이 시나리오는 예외가 아니라 **기본값**이다.

# %% [markdown]
# ## 5. 시각화 — 간트 타임라인 + 판단 시간 스윕

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    COLOR = {"read": "#4C78A8", "think": "#F58518", "write": "#E45756"}
    LABEL = {"팀장": "A · 팀장=이서연", "인원": "B · 인원=5"}
    MINW = 0.004  # 0초짜리 구간도 보이게 최소 폭을 준다

    fig = make_subplots(
        rows=2, cols=1, vertical_spacing=0.22,
        subplot_titles=("① 실제 실행 타임라인 (read / think / write)",
                        "② A의 판단 시간을 바꾸면 누가 사라지나"),
    )

    seen = set()
    for phase in ("read", "think", "write"):
        xs, ys, bases, texts = [], [], [], []
        for f, ph, a, b in spans:
            if ph != phase:
                continue
            xs.append(max(b - a, MINW))
            ys.append(LABEL[f])
            bases.append(a)
            texts.append(f"{LABEL[f]} · {ph}<br>{a:.3f}s → {b:.3f}s")
        fig.add_trace(go.Bar(
            x=xs, y=ys, base=bases, orientation="h", name=phase,
            marker_color=COLOR[phase], hovertext=texts, hoverinfo="text",
            legendgroup=phase, showlegend=phase not in seen,
        ), row=1, col=1)
        seen.add(phase)

    # B의 쓰기 시점과 A의 쓰기 시점 표시
    b_write = max(b for f, ph, a, b in spans if f == "인원" and ph == "write")
    a_write = max(b for f, ph, a, b in spans if f == "팀장" and ph == "write")
    fig.add_vline(x=b_write, line_dash="dot", line_color="#888", row=1, col=1)
    fig.add_vline(x=a_write, line_dash="dot", line_color="#888", row=1, col=1)
    fig.add_annotation(x=a_write, y=1.35, text="A가 옛 값으로 덮어씀 → 인원=5 소멸",
                       showarrow=False, xanchor="right", font=dict(size=11, color="#E45756"),
                       row=1, col=1)

    # ② 영역: [0, s) 안전 / [s, s+d_B) A 손실 / [s+d_B, ∞) B 손실
    ZONES = ((0.000, 0.020, "#54A24B", "안전"),
             (0.020, 0.070, "#B279A2", "A 손실"),
             (0.070, 0.160, "#D1495B", "B 손실"))
    for x0, x1, c, lab in ZONES:
        fig.add_vrect(x0=x0, x1=x1, fillcolor=c, opacity=0.10,
                      line_width=0, row=2, col=1)
        fig.add_annotation(x=(x0 + x1) / 2, y=1.75, text=lab, showarrow=False,
                           font=dict(size=12, color=c), row=2, col=1)

    VC = {"손실 없음": "#54A24B", "A(팀장) 사라짐": "#B279A2", "B(인원) 사라짐": "#D1495B"}
    seen2 = set()
    for da, verdict in sweep:
        fig.add_trace(go.Scatter(
            x=[da], y=[1], mode="markers", name=verdict,
            marker=dict(color=VC[verdict], size=15, symbol="circle",
                        line=dict(color="white", width=1.5)),
            hovertext=f"판단 {da:.3f}s → {verdict}", hoverinfo="text",
            legendgroup=verdict, showlegend=verdict not in seen2,
        ), row=2, col=1)
        seen2.add(verdict)
    for x, lab in ((0.020, "d_A = s = 0.02"), (0.070, "d_A = s + d_B = 0.07")):
        fig.add_vline(x=x, line_dash="dash", line_color="#333", row=2, col=1)
        fig.add_annotation(x=x, y=0.25, text=lab, showarrow=False, xanchor="left",
                           xshift=4, font=dict(size=11, color="#333"), row=2, col=1)

    fig.update_xaxes(title_text="경과 시간 (초)", row=1, col=1)
    fig.update_xaxes(title_text="A(팀장)의 판단 시간 d_A (초)  ·  d_B = 0.05, s = 0.02 고정",
                     range=[-0.004, 0.162], row=2, col=1)
    fig.update_yaxes(autorange="reversed", row=1, col=1)
    fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=False,
                     range=[0, 2.1], row=2, col=1)
    fig.update_layout(
        title="잃어버린 갱신 — 서로 다른 필드인데 하나가 사라진다",
        barmode="overlay", height=660, width=1000,
        template="plotly_white", bargap=0.45,
        legend=dict(tracegroupgap=6),
    )
    _show(fig)
    fig.write_image(os.path.join(HERE, "expy.png"), scale=2)
    print("expy.png 저장 완료")
except ImportError as e:
    print(f"시각화 건너뜀 (plotly/kaleido 없음): {e}")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 6. 정리
#
# | 항목 | 내용 |
# |---|---|
# | 초기 상태 | `팀장=박민수;인원=3` (노드 `t1`) |
# | 에이전트 A | `팀장 → 이서연`, 판단 **0.20초** |
# | 에이전트 B | `인원 → 5`, 판단 **0.05초** |
# | 겹치는 필드 | **없음** |
# | 결과 | `인원=3;팀장=이서연` — B의 변경이 **조용히** 사라짐 |
# | 에러 | 없음. 로그에도 「성공」만 |
#
# 원인은 경쟁 자체가 아니라 **쓰기 단위가 노드 전체**라는 데 있다.
# 대응은 셋이고, 실무의 답은 2 + 3 을 같이 쓰는 것이다.
#
# 1. **잠금** — 한 번에 하나만 고치게 한다. 느리고 데드락이 난다
# 2. **낙관적 잠금** — 쓰기 직전에 「안 바뀌었나」 확인한다 (충돌은 에러가 아니라 `rowcount == 0` 으로 온다)
# 3. **필드 단위 변경** — 통째로 안 쓰고 바뀐 것만 쓴다
#
# 아래는 3번(필드 단위 쓰기)만 적용해도 이 시나리오가 사라진다는 확인이다.

# %%
def field_update(db, field, value, delay, log):
    """통째로 쓰지 않고, 쓰기 시점에 «그 필드만» 갱신한다."""
    with LOCK:
        row = db.execute("SELECT props FROM node WHERE id='t1'").fetchone()
    log.append(f"  [{field}] 읽음: {row[0]}")
    time.sleep(delay)
    with LOCK:  # 쓰기 직전에 최신 상태를 다시 읽고 내 필드만 얹는다
        cur = parse(db.execute("SELECT props FROM node WHERE id='t1'").fetchone()[0])
        cur[field] = value
        db.execute("UPDATE node SET props=? WHERE id='t1'", (dump(cur),))
        db.commit()
    log.append(f"  [{field}] 씀:   {dump(cur)}")


db = fresh()
log2 = []
ts = []
for f, v, d in PLAN:
    t = threading.Thread(target=field_update, args=(db, f, v, d, log2))
    t.start()
    ts.append(t)
    time.sleep(0.02)
for t in ts:
    t.join()
fixed = db.execute("SELECT props FROM node WHERE id='t1'").fetchone()[0]
for line in log2:
    print(line)
print(f"\n최종 상태: {fixed}")
print("손실:", "없음" if parse(fixed) == {"팀장": "이서연", "인원": "5"} else "있음")
# 출력:
#   [팀장] 읽음: 팀장=박민수;인원=3
#   [인원] 읽음: 팀장=박민수;인원=3
#   [인원] 씀:   인원=5;팀장=박민수
#   [팀장] 씀:   인원=5;팀장=이서연
#
# 최종 상태: 인원=5;팀장=이서연
# 손실: 없음
