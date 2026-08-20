# %% [markdown]
# # ex2_replay_cost.py — 스냅숏 주기 5만, 그리고 무엇을 비교하는가
#
# 30장 `ex2_replay_cost.py` 는 **의존성 없이** 딱 두 가지를 잰다.
#
# | 비교 대상 | 재생하는 구간 |
# |---|---|
# | (a) 처음부터 재생 | 이벤트 $0 \dots n-1$ 전부 |
# | (b) 스냅숏 이후만 재생 | 마지막 스냅숏 지점부터 $n-1$ 까지 |
#
# 그리고 그 스냅숏 주기가 장에서 고정한 값이다.
#
# ```python
# SNAPSHOT_EVERY = 50_000
# ```
#
# 즉 **5만 이벤트마다 스냅숏을 찍는다고 두고**, 위 (a) 와 (b) 의 실제 소요 시간을 잰다.
# 답을 한 줄로 줄이면 이렇다.
#
# > 5만 이벤트마다 스냅숏을 찍는다고 두고, 처음부터 재생과 스냅숏 이후만 재생을 비교한다.
#
# 이 노트북은 그 실험을 그대로 재현하고, 마지막에 재생량의 **상한** $\min(n, k)$ 를 그림으로 보인다.
#
# 필요 패키지: plotly, kaleido (그래프 저장용). 나머지는 표준 라이브러리만 쓴다.

# %%
# 공통 준비 — 장의 ex2 와 같은 구조. 표준 라이브러리만 쓴다.
import random
import time

import plotly.graph_objects as go


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


rng = random.Random(11)


def make_events(n):
    """(id, 주어, 관계, 목적어, 연산) 이벤트를 n 개 만든다. 72% 는 추가, 28% 는 삭제."""
    out = []
    for i in range(n):
        s = f"e{rng.randint(0, 400)}"
        o = f"t{rng.randint(0, 40)}"
        op = "추가" if rng.random() < 0.72 else "삭제"
        out.append((i, s, "속함", o, op))
    return out


def replay(events, start_state=None):
    """이벤트를 순서대로 «접어서» 상태를 만든다. start_state 가 곧 스냅숏이다."""
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


SNAPSHOT_EVERY = 50_000  # ← 장이 고정한 스냅숏 주기. 5만 이벤트마다 한 장.

print("스냅숏 주기 k =", f"{SNAPSHOT_EVERY:,}")
sample = make_events(5)
for e in sample:
    print(e)
print("5개만 접어 보면:", sorted(replay(sample)))

# 출력:
# 스냅숏 주기 k = 50,000
# (0, 'e231', '속함', 't35', '삭제')
# (1, 'e399', '속함', 't29', '추가')
# (2, 'e300', '속함', 't12', '추가')
# (3, 'e262', '속함', 't30', '추가')
# (4, 'e95', '속함', 't6', '추가')
# 5개만 접어 보면: [('e262', '속함', 't30'), ('e300', '속함', 't12'),
#                  ('e399', '속함', 't29'), ('e95', '속함', 't6')]
#   삭제(4번)는 없던 항목을 지우려 한 것이라 discard 로 조용히 넘어간다.

# %% [markdown]
# ## 1단계 — 장의 표를 그대로 재현한다
#
# `main()` 의 핵심은 이 네 줄이다.
#
# ```python
# last_snap = (n // SNAPSHOT_EVERY) * SNAPSHOT_EVERY   # 마지막 스냅숏 지점
# snap_state = replay(ev[:last_snap]) if last_snap else set()
# tail = ev[last_snap:]                                # 스냅숏 이후 꼬리
# tail_ms, st2 = timed(replay, tail, snap_state)
# ```
#
# 그리고 `assert st == st2` 로 **두 방법의 결과가 같은지** 확인한다.
# 이게 비교의 전제다. 값이 다르면 빠른 게 무슨 소용인가.
#
# 스냅숏 지점은 $\lfloor n/k \rfloor \cdot k$ 이므로, 재생할 꼬리 길이는
#
# $$\text{tail}(n) = n - \left\lfloor \frac{n}{k} \right\rfloor \cdot k = n \bmod k$$
#
# 단 $n < k$ 일 때는 스냅숏이 한 장도 없어서 꼬리가 곧 $n$ 이다.

# %%
rng = random.Random(11)  # 장과 같은 시드로 되돌린다

print(f"스냅숏을 {SNAPSHOT_EVERY:,} 이벤트마다 찍는다고 하자.\n")
print(f"{'이벤트 수':>12}{'처음부터(ms)':>14}{'스냅숏 이후(ms)':>16}"
      f"{'재생할 이벤트':>14}{'배수':>8}")
print("-" * 68)

for n in (10_000, 63_000, 217_000, 1_034_000):
    ev = make_events(n)
    full_ms, st = timed(replay, ev)

    last_snap = (n // SNAPSHOT_EVERY) * SNAPSHOT_EVERY
    snap_state = replay(ev[:last_snap]) if last_snap else set()
    tail = ev[last_snap:]
    tail_ms, st2 = timed(replay, tail, snap_state)

    assert st == st2, "두 방법의 결과가 다르면 비교 자체가 무의미하다"
    ratio = full_ms / tail_ms if tail_ms else 0
    print(f"{n:>12,}{full_ms:>14.1f}{tail_ms:>16.1f}"
          f"{len(tail):>14,}{ratio:>7.1f}x")

# 출력: (측정값이라 실행마다 조금씩 달라진다)
#        이벤트 수      처음부터(ms)      스냅숏 이후(ms)       재생할 이벤트      배수
# --------------------------------------------------------------------
#       10,000           1.7             1.3        10,000    1.3x
#       63,000          14.4             3.5        13,000    4.1x
#      217,000          54.8             5.6        17,000    9.8x
#    1,034,000         271.2            10.5        34,000   25.7x
#
# 읽는 법:
#  - 첫 줄(1만 개)은 배수가 1 근처다. 10,000 < 50,000 이라 스냅숏이 아직 한 장도
#    안 찍혔고, 결국 처음부터 재생하는 것과 똑같다. 장의 실행 가이드도 «첫 줄에서
#    배수가 1 근처거나 그보다 작게 나오는 것도 정상»이라고 못박아 둔다.
#  - 이벤트가 늘수록 «처음부터» 열은 비례해서 커지는데, «스냅숏 이후» 열은
#    거의 안 커진다. 꼬리 길이가 n mod 50,000 이라 5만을 넘지 못하기 때문이다.

# %% [markdown]
# ## 2단계 — 왜 안 커지나: 재생량의 상한 $\min(n, k)$
#
# 스냅숏 주기가 $k$ 일 때 재생해야 할 이벤트 수는
#
# $$\text{tail}(n) = \begin{cases} n & (n < k) \\ n \bmod k & (n \ge k)\end{cases}
# \qquad\Longrightarrow\qquad \text{tail}(n) \;\le\; \min(n,\, k)$$
#
# 즉 **재생량은 데이터 양 $n$ 에 대해 위로 막혀 있다.** 장의 문장 그대로다.
#
# > 이벤트가 백만 개든 천만 개든 재생할 것은 최대 5만 개다.
# > 그러니 재생 시간이 «데이터 양»이 아니라 «스냅숏 주기»로 정해진다.
#
# 반대로 처음부터 재생은 $\Theta(n)$ 이라 막아 주는 것이 없다.
# 숫자로 확인해 보자.

# %%
K = SNAPSHOT_EVERY
print(f"{'n':>12}{'tail(n)':>10}{'min(n,k)':>10}{'상한 지킴':>10}")
print("-" * 42)
for n in (10_000, 49_999, 50_000, 63_000, 217_000, 1_034_000, 10_000_000):
    tail = n - (n // K) * K
    ok = "예" if tail <= min(n, K) else "아니오"
    print(f"{n:>12,}{tail:>10,}{min(n, K):>10,}{ok:>10}")

# 출력:
#            n   tail(n)  min(n,k)     상한 지킴
# ------------------------------------------
#       10,000    10,000    10,000        예
#       49,999    49,999    49,999        예
#       50,000         0    50,000        예
#       63,000    13,000    50,000        예
#      217,000    17,000    50,000        예
#    1,034,000    34,000    50,000        예
#   10,000,000         0    50,000        예
#
# n 이 천만이어도 재생량은 5만을 절대 넘지 못한다. 이것이 «상한»이다.
# (n 이 k 의 배수일 때 tail 이 0 인 것은 스냅숏이 방금 찍혔다는 뜻이다.
#  최악의 경우는 n mod k = k-1, 즉 49,999 개다.)

# %% [markdown]
# ## 3단계 — 두 곡선을 실제로 재어 그린다
#
# 이벤트 수를 늘려 가며 (a) 처음부터 재생, (b) 스냅숏 이후만 재생의 시간을 직접 잰다.
# 큰 리스트를 한 번만 만들어 두고 `islice` 로 구간만 훑으면 리스트 복사 비용이 안 섞인다.
# 그리고 측정 잡음을 줄이려고 3번 재서 «가장 빠른 값»을 쓴다.
#
# 기대하는 그림:
#
# - (a) 는 $n$ 에 비례해 **직선으로 오른다**.
# - (b) 는 $n \bmod k$ 를 따라 **톱니 모양으로 오르내리며, 결코 $k$ 개분을 넘지 않는다**.

# %%
from itertools import islice

rng = random.Random(11)
N_MAX = 1_012_000
BIG = make_events(N_MAX)          # 한 번만 만든다


def best_of(reps, lo, hi, start_state=None):
    """[lo, hi) 구간을 reps 번 재생해 가장 빠른 시간(ms)과 결과를 돌려준다."""
    best, res = float("inf"), None
    for _ in range(reps):
        ms, res = timed(replay, islice(BIG, lo, hi), start_state)
        best = min(best, ms)
    return best, res


# 주기 5만의 약수로 샘플링하면 n mod k 가 몇 값에 고정돼 톱니가 안 보인다.
# 일부러 5만과 어긋나는 간격으로 재서 톱니 전체를 훑는다.
STEP = 46_000
NS = list(range(STEP, N_MAX + 1, STEP))
REPS_FULL, REPS_TAIL = 2, 5   # 꼬리는 짧으니 여러 번 재서 잡음을 깎는다

full_times, tail_times, tail_lens = [], [], []
for n in NS:
    full_ms, st = best_of(REPS_FULL, 0, n)

    last_snap = (n // SNAPSHOT_EVERY) * SNAPSHOT_EVERY
    snap_state = replay(islice(BIG, 0, last_snap)) if last_snap else set()
    tail_ms, st2 = best_of(REPS_TAIL, last_snap, n, snap_state)
    assert st == st2

    full_times.append(full_ms)
    tail_times.append(tail_ms)
    tail_lens.append(n - last_snap)

# 최악의 꼬리(= k-1 개)를 실제 스냅숏 상태 위에서 재서 «상한선»의 높이를 구한다.
# 950,000 = 19 x 50,000 이므로 여기가 스냅숏 지점이고, 그 뒤 49,999개가 최악의 꼬리다.
WORST_SNAP = 950_000
worst_state = replay(islice(BIG, 0, WORST_SNAP))
bound_ms, _ = best_of(REPS_TAIL, WORST_SNAP,
                      WORST_SNAP + SNAPSHOT_EVERY - 1, worst_state)

print(f"측정 지점 {len(NS)}개 (n = {NS[0]:,} ~ {NS[-1]:,})")
print(f"처음부터   : 최소 {min(full_times):7.1f} ms  최대 {max(full_times):7.1f} ms")
print(f"스냅숏 이후: 최소 {min(tail_times):7.1f} ms  최대 {max(tail_times):7.1f} ms")
print(f"재생 이벤트 수 최대 {max(tail_lens):,} (상한 {SNAPSHOT_EVERY:,})")
print(f"최악 꼬리 {SNAPSHOT_EVERY - 1:,}개 재생 = {bound_ms:.1f} ms  ← 이게 (b) 의 천장")

# 출력: (측정값이라 실행 환경/실행마다 달라진다)
# 측정 지점 22개 (n = 46,000 ~ 1,012,000)
# 처음부터   : 최소     7.0 ms  최대   252.8 ms
# 스냅숏 이후: 최소     4.5 ms  최대    20.2 ms
# 재생 이벤트 수 최대 48,000 (상한 50,000)
# 최악 꼬리 49,999개 재생 = 24.6 ms  ← 이게 (b) 의 천장
#
# «처음부터» 는 n 에 따라 36배까지 벌어지는데,
# «스냅숏 이후» 는 24.6ms 라는 천장 아래를 계속 맴돈다.

# %%
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=NS, y=full_times, mode="lines+markers", name="(a) 처음부터 재생 — Θ(n)",
    line=dict(color="#d62728", width=2), marker=dict(size=6)))
fig.add_trace(go.Scatter(
    x=NS, y=tail_times, mode="lines+markers",
    name="(b) 스냅숏 이후만 재생 — n mod k",
    line=dict(color="#1f77b4", width=2), marker=dict(size=6)))
for x in range(SNAPSHOT_EVERY, N_MAX, SNAPSHOT_EVERY):
    fig.add_vline(x=x, line=dict(color="rgba(130,130,130,0.22)", width=1, dash="dot"))
fig.add_hline(
    y=bound_ms, line=dict(color="#2ca02c", width=2, dash="dash"),
    annotation_text=f"상한: k−1 = {SNAPSHOT_EVERY - 1:,}개 재생 ≈ {bound_ms:.1f} ms",
    annotation_position="top right",
    annotation_font=dict(size=12, color="#2ca02c"))
fig.add_annotation(
    xref="paper", yref="paper", x=0.02, y=0.70,
    text=("세로 점선 = 스냅숏 지점 (k = 50,000)<br>"
          "(b) 의 재생량 tail(n) = n mod k ≤ min(n, k)<br>"
          "→ 데이터가 아무리 쌓여도 초록 선 위로 못 올라간다"),
    showarrow=False, align="left", font=dict(size=12),
    bgcolor="rgba(255,255,255,0.85)", bordercolor="rgba(0,0,0,0.25)",
    borderwidth=1, borderpad=6)
fig.update_layout(
    title="ex2_replay_cost.py — 처음부터 재생 vs 스냅숏 이후만 재생 (k = 5만)",
    xaxis_title="이벤트 수 n",
    yaxis_title="재생 시간 (ms)",
    legend=dict(x=0.02, y=0.98, bgcolor="rgba(255,255,255,0.8)"),
    width=980, height=560, template="plotly_white")
_show(fig)

import os
_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png") \
    if "__file__" in dir() else "expy.png"
fig.write_image(_png, scale=2)
print("저장:", os.path.basename(_png))

# 출력:
# 저장: expy.png
#  - 빨간 선은 n 에 비례해 곧게 우상향한다 (약 7 ms → 253 ms).
#  - 파란 선은 n mod k 를 따라 오르내리지만, 초록 점선(최악 꼬리 = 24.6 ms)
#    아래에 계속 갇혀 있다. 데이터가 백만이 되어도 천장이 안 올라간다.

# %% [markdown]
# ## 4단계 — 그래서 주기 $k$ 를 얼마로 잡나
#
# 장은 상한을 보인 다음 곧바로 교환 관계를 적는다.
#
# ```
# 짧게 잡으면 — 재생은 빠른데 스냅숏 저장 공간이 늘어난다
# 길게 잡으면 — 공간은 아끼는데 복구가 느려진다
# ```
#
# 그리고 정하는 법은 **복구 목표 시간에서 거꾸로 계산**하는 것이다.
# 「장애 났을 때 3초 안에 복구」가 목표라면, 3초에 재생할 수 있는 이벤트 수를 재고
# 그만큼을 주기로 잡는다. 위에서 측정한 처리량으로 계산해 보자.

# %%
throughput = NS[-1] / (full_times[-1] / 1000.0)   # 초당 재생 가능한 이벤트 수
worst_sec = bound_ms / 1000.0                     # 3단계에서 실제로 잰 최악 복구 시간
print(f"측정 처리량: 약 {throughput:,.0f} 이벤트/초")
print(f"k = {SNAPSHOT_EVERY:,} 일 때 실측 최악 복구: {worst_sec:.3f} 초")
print()
print(f"{'복구 목표(초)':>14}{'권장 주기 k':>16}{'목표 대비 여유':>16}")
print("-" * 46)
for target in (0.5, 1, 3, 10):
    k_rec = int(throughput * target)
    print(f"{target:>14}{k_rec:>16,}{target / worst_sec:>15.0f}배")

# 출력: (처리량은 실행 환경에 따라 달라진다)
# 측정 처리량: 약 4,002,487 이벤트/초
# k = 50,000 일 때 실측 최악 복구: 0.025 초
#
#     복구 목표(초)        권장 주기 k       목표 대비 여유
# ----------------------------------------------
#           0.5         2,001,243             20배
#             1         4,002,487             41배
#             3        12,007,461            122배
#            10        40,024,870            407배
#
# 이 장난감 리듀서는 초당 수백만 건을 접으므로 k = 5만은 대단히 보수적이다.
# 실제 시스템의 리듀서는 훨씬 무겁다(그래프 쓰기, 검증, 직렬화). 중요한 건 숫자가
# 아니라 «목표 시간 → 처리량 측정 → 주기 역산» 이라는 방향이다.

# %% [markdown]
# ## 정리
#
# - `ex2_replay_cost.py` 의 스냅숏 주기는 `SNAPSHOT_EVERY = 50_000`, 즉 **5만 이벤트마다 한 장**이다.
# - 비교 대상은 **(a) 처음부터 재생** 과 **(b) 스냅숏 이후만 재생** 두 가지이고,
#   `assert st == st2` 로 두 결과가 같음을 확인한 뒤 시간만 비교한다.
# - (a) 는 $\Theta(n)$, (b) 는 $\text{tail}(n) = n \bmod k \le \min(n, k)$ 라 **상한이 있다**.
# - 그래서 재생 시간은 데이터 양이 아니라 스냅숏 주기가 정한다. 주기는 복구 목표 시간에서 역산한다.
# - 이건 새 발명이 아니라 데이터베이스의 **쓰기 전 로그(WAL) + 체크포인트** 구조 그대로다.
