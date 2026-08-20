# %% [markdown]
# # SQLite 체크포인터는 메모리 대비 얼마나 느린가
#
# 책(21장, `ex4_checkpointer_cost.py`)의 실측 결론:
#
# > SQLite 체크포인터는 메모리 체크포인터의 **2.0~2.8배** 느리고,
# > 상태가 **32KB를 넘으면 4.8배**까지 벌어진다.
#
# 이 스크립트는 LangGraph 없이 순수 Python(`dict` vs `sqlite3`)으로
# 같은 구조의 벤치마크를 재현한다. 핵심 모델:
#
# $$T_{\text{run}} = N \times \big(t_{\text{node}} + t_{\text{serialize}}(s) + t_{\text{ckpt}}(s)\big)$$
#
# - $N$: 슈퍼스텝 수 (체크포인트는 **슈퍼스텝 경계마다** 찍힌다)
# - $t_{\text{node}}$: 노드 실행 + 그래프 기계장치 비용 (체크포인터와 무관한 공통 비용)
# - $t_{\text{ckpt}}(s)$: 체크포인트 쓰기 — 메모리는 dict 대입, SQLite는 `INSERT + COMMIT`
#
# SQLite 쪽은 $t_{\text{ckpt}}(s) \approx c_{\text{txn}} + s/B$ 로 근사된다.
# $c_{\text{txn}}$(트랜잭션 고정비, 커밋마다 붙는 디스크 동기화)이 있어서
# **작은 상태에서는 배율이 평평**하고, 상태 $s$가 커지면
# $s/B$(쓰기 대역폭 항)가 지배해 **배율이 꺾여 올라간다**.

# %%
# 필요 패키지: plotly, kaleido (벤치마크 자체는 표준 라이브러리만 사용)
import os
import pickle
import sqlite3
import tempfile
import time


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1. 두 종류의 체크포인터
#
# LangGraph의 `InMemorySaver`와 `SqliteSaver`를 최소 형태로 흉내 낸다.
# 둘 다 상태를 **직렬화(pickle)** 하는 것은 같다. 차이는 저장 위치뿐이다.
#
# - 메모리: dict 대입 — 프로세스가 죽으면 **같이 사라진다** (체크포인터가 아니라 캐시)
# - SQLite: 슈퍼스텝마다 `INSERT + COMMIT` — 커밋마다 fsync 계열 디스크 동기화가 붙는다.
#   이 고정비가 내구성(durability)의 값이다.

# %%
class MemoryCheckpointer:
    """dict 저장 — LangGraph InMemorySaver 역할."""

    def __init__(self):
        self.store = {}

    def put(self, thread, step, blob):
        self.store[(thread, step)] = blob


class SqliteCheckpointer:
    """파일 SQLite 저장 — LangGraph SqliteSaver 역할. 슈퍼스텝마다 커밋."""

    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            "CREATE TABLE ckpt (thread TEXT, step INT, blob BLOB,"
            " PRIMARY KEY (thread, step))")
        self.conn.commit()

    def put(self, thread, step, blob):
        self.conn.execute("INSERT OR REPLACE INTO ckpt VALUES (?, ?, ?)",
                          (thread, step, blob))
        self.conn.commit()   # 체크포인트마다 트랜잭션 — 내구성의 값

    def close(self):
        self.conn.close()


# %% [markdown]
# ## 2. 슈퍼스텝 시뮬레이션
#
# 책의 예제처럼 **노드 12개짜리 선형 그래프**를 끝까지 돌린다.
# 노드 하나 = (노드 실행 흉내 0.3ms busy-wait) + (상태 갱신) + (직렬화) + (체크포인트 쓰기).
#
# 노드 실행 비용을 넣는 이유: 책의 배율(2.0~2.8x)은 *그래프 실행 전체* 대비 배율이다.
# 그래프 기계장치·노드 실행이라는 공통 비용이 분모에 들어 있어서 배율이 완만하게 나온다.
# 이 공통 비용을 빼고 체크포인트 쓰기만 비교하면 배율은 수천 배로 튄다(아래 3-b에서 확인).
#
# 상태 크기는 1KB/8KB/32KB/64KB에 더해, 꺾임이 확실히 보이도록
# 책의 최대치인 256KB도 잰다.

# %%
N_STEPS = 12                                          # 책 예제와 동일한 슈퍼스텝 수
SIZES = (1_000, 8_000, 32_000, 64_000, 256_000)       # 상태 크기
NODE_WORK_S = 0.0003                                  # 노드 실행 흉내 0.3ms
REPEAT = 9                                            # 반복 중 최솟값 채택 (노이즈 제거)


def run_graph(ckpt, thread, payload):
    """슈퍼스텝 N_STEPS개를 실행. 경계마다 체크포인트를 찍는다."""
    state = {"n": 0, "blob": payload}
    for step in range(N_STEPS):
        t0 = time.perf_counter()
        while time.perf_counter() - t0 < NODE_WORK_S:
            pass                             # 노드 실행 흉내 (busy-wait)
        state = {"n": state["n"] + 1, "blob": payload}
        ckpt.put(thread, step, pickle.dumps(state))  # 직렬화는 양쪽 공통


def bench(make_ckpt, payload):
    best = float("inf")
    for i in range(REPEAT):
        ckpt = make_ckpt()
        t0 = time.perf_counter()
        run_graph(ckpt, f"t{i}", payload)
        best = min(best, time.perf_counter() - t0)
        if hasattr(ckpt, "close"):
            ckpt.close()
    return best * 1000   # ms


# %% [markdown]
# ## 3. 실측
#
# 상태 크기별로
# **(a)** 그래프 전체 실행 시간의 배율,
# **(b)** 체크포인트 쓰기 1회의 순수 비용을 잰다.

# %%
# (a) 그래프 전체 실행 시간 — 책 ex4 와 같은 비교
tmpdir = tempfile.mkdtemp()
_counter = [0]


def new_sqlite():
    _counter[0] += 1
    return SqliteCheckpointer(os.path.join(tmpdir, f"c{_counter[0]}.sqlite"))


results = []   # (size, mem_ms, sqlite_ms, ratio)
print(f"노드 {N_STEPS}개짜리 그래프를 끝까지 돌린 시간 (ms)\n")
print(f"{'상태 크기':>8} {'메모리':>9} {'SQLite':>9} {'배율':>7}")
print("-" * 40)
for size in SIZES:
    payload = "x" * size
    mem = bench(MemoryCheckpointer, payload)
    dsk = bench(new_sqlite, payload)
    results.append((size, mem, dsk, dsk / mem))
    print(f"{size:>7,}B {mem:>9.2f} {dsk:>9.2f} {dsk/mem:>6.1f}x")

# 출력 (macOS/APFS 실측 — fsync 노이즈 때문에 절대값은 실행마다 조금씩 다르다):
# 노드 12개짜리 그래프를 끝까지 돌린 시간 (ms)
#
#     상태 크기       메모리    SQLite      배율
# ----------------------------------------
#   1,000B      3.61     10.18    2.8x
#   8,000B      3.62     11.78    3.3x
#  32,000B      3.62     10.47    2.9x
#  64,000B      3.63     11.16    3.1x
# 256,000B      3.66     14.77    4.0x

# %%
# (b) 체크포인트 쓰기 "1회"의 순수 비용 — 공통 비용(노드 실행)을 뺀 알맹이
def bench_put(make_ckpt, payload, n=40, rounds=5):
    blob = pickle.dumps({"n": 1, "blob": payload})
    best = float("inf")
    for _ in range(rounds):
        ckpt = make_ckpt()
        t0 = time.perf_counter()
        for step in range(n):
            ckpt.put("t", step, blob)
        best = min(best, (time.perf_counter() - t0) / n * 1000)
        if hasattr(ckpt, "close"):
            ckpt.close()
    return best


print(f"쓰기 1회 비용 (ms)\n")
print(f"{'상태 크기':>8} {'dict 대입':>10} {'INSERT+COMMIT':>14}")
print("-" * 38)
for size in SIZES:
    payload = "x" * size
    m = bench_put(MemoryCheckpointer, payload)
    d = bench_put(new_sqlite, payload)
    print(f"{size:>7,}B {m:>9.4f} {d:>13.3f}")

# 출력 (동일 환경 실측):
# 쓰기 1회 비용 (ms)
#
#     상태 크기   dict 대입  INSERT+COMMIT
# --------------------------------------
#   1,000B    0.0001         0.699
#   8,000B    0.0002         0.751
#  32,000B    0.0002         0.639
#  64,000B    0.0001         0.726
# 256,000B    0.0002         1.281

# %% [markdown]
# ## 4. 읽는 법
#
# **(a) 그래프 전체 기준 배율** — 책과 같은 모양이 나온다.
# 64KB까지는 배율이 완만하고(실측 2.8~3.3x, 책 2.0~2.8x),
# 그 뒤에 꺾여 올라간다(실측 256KB에서 4.0x, 책 4.8x).
#
# **(b) 쓰기 1회의 순수 비용** — 왜 그런지가 여기서 보인다.
# `INSERT+COMMIT`은 1KB에서 0.70ms, 256KB에서 1.28ms — 데이터가 **256배** 늘었는데
# 비용은 **2배도 안** 늘었다. 작은 구간에서는 트랜잭션 고정비 $c_{\text{txn}}$
# (커밋마다 붙는 디스크 동기화)이 지배하기 때문이다.
# 참고로 dict 대입은 0.0002ms — 커밋 1회가 dict 대입 수천 번 값이다.
#
# 그래서 대처가 구간마다 다르다:
#
# | 구간 | 지배 항 | 효과 있는 대처 |
# |---|---|---|
# | 32KB 미만 | 트랜잭션 고정비 $c_{\text{txn}}$ | 상태를 줄여도 소용없다. **슈퍼스텝 수**를 줄여라 |
# | 32KB 이상 | 쓰기 대역폭 $s/B$ | **상태 크기**를 줄이는 게 바로 듣는다 (19장) |
#
# 그리고 이 오버헤드를 이유로 메모리 체크포인터를 쓰면 안 된다.
# 프로세스가 죽으면 다 사라지니까 — 그건 체크포인터가 아니라 **캐시**다.
# 지연이 문제면 줄일 곳은 상태 크기지, 체크포인터 종류가 아니다.

# %%
# 시각화 — 왼쪽: 절대 시간(그래프 전체, ms), 오른쪽: 메모리 대비 배율
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    BLUE, ORANGE = "#2a78d6", "#eb6834"     # 시리즈 색 (메모리 / SQLite)
    INK, MUTED, GRID = "#0b0b0b", "#898781", "#e1e0d9"
    SURFACE = "#fcfcfb"

    labels = [f"{s//1000}KB" for s, *_ in results]
    mem_ms = [r[1] for r in results]
    dsk_ms = [r[2] for r in results]
    ratios = [r[3] for r in results]

    fig = make_subplots(
        rows=1, cols=2, horizontal_spacing=0.14,
        subplot_titles=("그래프 전체 실행 시간 (ms)", "메모리 대비 배율"))

    fig.add_bar(x=labels, y=mem_ms, name="메모리(dict)",
                marker_color=BLUE, row=1, col=1,
                text=[f"{v:.1f}" for v in mem_ms], textposition="outside")
    fig.add_bar(x=labels, y=dsk_ms, name="SQLite 파일",
                marker_color=ORANGE, row=1, col=1,
                text=[f"{v:.1f}" for v in dsk_ms], textposition="outside")

    fig.add_scatter(x=labels, y=ratios, mode="lines+markers+text",
                    name="배율 (SQLite/메모리)", line=dict(color=ORANGE, width=2),
                    marker=dict(size=9),
                    text=[f"{v:.1f}x" for v in ratios], textposition="top center",
                    textfont=dict(color=INK), showlegend=False, row=1, col=2)
    fig.add_hline(y=1.0, line=dict(color=MUTED, width=1, dash="dot"),
                  row=1, col=2,
                  annotation_text="1.0x = 메모리", annotation_font_color=MUTED)

    fig.update_layout(
        title=dict(text=f"SQLite 체크포인터의 값 — 슈퍼스텝 {N_STEPS}개, 상태 크기별",
                   font=dict(color=INK, size=17)),
        barmode="group", bargap=0.3,
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        font=dict(family="system-ui, -apple-system, sans-serif", color=INK),
        legend=dict(orientation="h", y=-0.22, x=0),
        width=960, height=470, margin=dict(t=90, b=90, l=60, r=30))
    fig.update_xaxes(title_text="상태 크기", color=MUTED, linecolor="#c3c2b7",
                     showgrid=False)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor="#c3c2b7", color=MUTED)
    fig.update_yaxes(title_text="ms", row=1, col=1,
                     range=[0, max(dsk_ms) * 1.25])
    fig.update_yaxes(row=1, col=2, range=[0, max(ratios) * 1.3])

    _show(fig)
    out_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
    fig.write_image(out_png, scale=2)        # kaleido 필요
    print(f"저장: {out_png}")
except ImportError as e:
    print(f"시각화 생략 (패키지 없음: {e})")

# 출력: 저장: .../expy.png

# %% [markdown]
# ## 5. 정리
#
# - **질문**: SQLite 체크포인터는 메모리 대비 얼마나 느린가?
# - **답**: 책의 실측으로 **2.0~2.8배**, 상태가 **32KB를 넘으면 4.8배**까지.
#   이 재현 벤치마크(dict vs sqlite3)에서도 같은 모양(2.8x → 4.0x)이 나왔다.
# - 배율이 작은 상태에서 평평한 이유: 커밋(트랜잭션)의 **고정비**가 지배해서.
#   큰 상태에서 꺾이는 이유: **쓰기 대역폭** 항이 상태 크기에 비례해 커져서.
# - 재 보기 전에는 어느 구간에 있는지 모른다 — "상태를 줄이면 항상 빨라진다"는 틀린 직관.
