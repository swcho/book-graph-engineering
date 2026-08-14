# 필요 패키지: plotly, kaleido  (sqlite3 는 표준 라이브러리)
#   pip install plotly kaleido
#
# 확인 시점: Python 3.13, sqlite3(내장), plotly 6.8.0
#
# 주제: SQL/PGQ 로 «표기»를 바꿔도 조인 폭발은 남는다.
#       폭발은 문법이 아니라 «중간 결과의 카디널리티 곱»에서 나온다는 것을 재어서 본다.

# %% [markdown]
# # SQL/PGQ 로 옮겨도 남는 문제: 조인 폭발
#
# 11장 예제 4(`ex4_sql_pgq.py`)의 마지막 문장이 이 카드의 답입니다.
#
# > 옮기지 않아도 된다는 게 공짜라는 뜻은 아니다.
# > 조인 폭발은 그대로 남는다(3장). 저장 위치가 아니라 «따라가는 값»이 문제였으니까.
#
# 이 노트북에서 확인할 것:
#
# 1. 평균 팬아웃 $f$ 를 조절할 수 있는 합성 그래프를 sqlite3 에 만든다.
# 2. $n$-홉 조인 사슬의 **접두 조인**($1..n$ 단계)마다 실제 행 수를 센다.
# 3. 해석식 $|R_n| \approx N \cdot f^{\,n}$ 과 맞춰 본다.
# 4. 조인 순서를 «작은 쪽»에서 시작하도록 바꾸면 **벽시계 시간**은 줄지만
#    $n$ 에 대한 **지수**는 그대로임을 확인한다.
#
# 핵심 구분:
#
# | 바뀌는 것 (SQL/PGQ 가 주는 것) | 바뀌지 않는 것 |
# |---|---|
# | 표기 — `MATCH (a)-[:E]->(b)` 패턴 | 중간 결과 크기 $N \cdot f^n$ |
# | 데이터 이동 불필요 (두 벌 운영 회피) | 카디널리티 곱, 지수의 밑 $f$ |
# | 사람이 읽는 의도 표현 | 실행 엔진이 실제로 만드는 행 수 |

# %%
import sqlite3
import random
import time
import os


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
print("작업 디렉터리:", os.path.basename(HERE))
# 출력: 작업 디렉터리: bd811513-3180-4352-b6ef-133adacfbadc


# %% [markdown]
# ## 1. 팬아웃 $f$ 를 조절하는 합성 그래프
#
# 노드 $N$ 개, 각 노드의 출차수(out-degree)를 $\{f-1, f, f+1\}$ 에서 균등하게 뽑습니다.
# 그러면 평균 팬아웃이 정확히 $f$ 이고, 도착 노드를 균등 무작위로 고르므로
# 길이 $n$ 인 **걷기(walk)** 의 기대 개수는
#
# $$\mathbb{E}\,|R_n| \;=\; N \cdot f^{\,n}$$
#
# 이 됩니다. 이것이 «따라가는 값»이 만드는 지수입니다.
# 테이블 한 장짜리 관계형 스키마(`edge(src, dst)`)라는 점을 눈여겨보세요.
# 저장 위치는 계속 관계형입니다.

# %%
def build(n_nodes: int, fanout: int, seed: int = 42) -> sqlite3.Connection:
    """평균 팬아웃이 fanout 인 방향 그래프를 sqlite3 메모리 DB에 만든다."""
    rnd = random.Random(seed)
    con = sqlite3.connect(":memory:")
    con.executescript("""
        CREATE TABLE node (id INTEGER PRIMARY KEY);
        CREATE TABLE edge (src INTEGER, dst INTEGER);
    """)
    con.executemany("INSERT INTO node VALUES (?)", [(i,) for i in range(n_nodes)])
    rows = []
    for src in range(n_nodes):
        deg = rnd.choice([fanout - 1, fanout, fanout + 1])
        for _ in range(deg):
            rows.append((src, rnd.randrange(n_nodes)))
    con.executemany("INSERT INTO edge VALUES (?,?)", rows)
    con.executescript("""
        CREATE INDEX ix_edge_src ON edge(src);
        CREATE INDEX ix_edge_dst ON edge(dst);
    """)
    con.commit()
    return con


con = build(n_nodes=2000, fanout=3)
n_edges = con.execute("SELECT COUNT(*) FROM edge").fetchone()[0]
print(f"노드 2000개, 엣지 {n_edges}개, 실측 평균 팬아웃 = {n_edges / 2000:.3f}")
# 출력: 노드 2000개, 엣지 6051개, 실측 평균 팬아웃 = 3.026


# %% [markdown]
# ## 2. 같은 질문, 두 가지 표기
#
# 「$n$ 홉 떨어진 쌍을 모두 찾아라」를 SQL/PGQ 표기와 평범한 SQL 로 각각 씁니다.
# 아래 PGQ 문장은 sqlite3 가 이해하지 못합니다(구현이 아직 안 퍼졌습니다).
# 중요한 건 **두 표기가 같은 조인 사슬로 내려온다**는 점입니다.

# %%
PGQ_TEXT = """
-- SQL/PGQ (ISO/IEC 9075-16:2023) — 테이블은 그대로 두고 그래프 «뷰»만 얹는다
CREATE PROPERTY GRAPH g
  VERTEX TABLES (node KEY (id) LABEL N PROPERTIES (id))
  EDGE TABLES (edge SOURCE KEY (src) REFERENCES node (id)
                    DESTINATION KEY (dst) REFERENCES node (id) LABEL E);

SELECT COUNT(*) FROM GRAPH_TABLE (g
  MATCH (a IS N)-[IS E]->{4}(b IS N)      -- 4홉
  COLUMNS (a.id, b.id)
);
"""


def chain_sql(n: int, count_only: bool = True) -> str:
    """n 홉 조인 사슬. PGQ 의 -[IS E]->{n} 이 실제로 내려오는 모양."""
    sel = "COUNT(*)" if count_only else f"e1.src AS a, e{n}.dst AS b"
    body = "FROM edge e1"
    for k in range(2, n + 1):
        body += f" JOIN edge e{k} ON e{k}.src = e{k - 1}.dst"
    return f"SELECT {sel} {body}"


print(PGQ_TEXT)
print("같은 뜻의 평범한 SQL (4홉):")
print(" ", chain_sql(4))
# 출력: (PGQ 문장 전문이 그대로 출력된 뒤)
#   같은 뜻의 평범한 SQL (4홉):
#     SELECT COUNT(*) FROM edge e1 JOIN edge e2 ON e2.src = e1.dst
#     JOIN edge e3 ON e3.src = e2.dst JOIN edge e4 ON e4.src = e3.dst
#   → PGQ 의 ->{4} 는 «네 번 조인»의 다른 표기일 뿐이다. 비용은 조인 쪽에 그대로 남는다.


# %% [markdown]
# ## 3. 접두 조인마다 실제 행 수를 센다
#
# $n = 1 \ldots 5$ 에 대해 실제 `COUNT(*)` 와 해석식 $N \cdot f^{\,n}$ 을 비교합니다.

# %%
def measure(con, max_n: int, n_nodes: int, fanout: float):
    out = []
    for n in range(1, max_n + 1):
        q = chain_sql(n)
        t0 = time.perf_counter()
        rows = con.execute(q).fetchone()[0]
        ms = (time.perf_counter() - t0) * 1000
        pred = n_nodes * fanout ** n
        out.append((n, rows, pred, ms))
    return out


rows_f3 = measure(con, 5, 2000, n_edges / 2000)
print(f"{'홉':>3} {'실측 행수':>12} {'예측 N·f^n':>14} {'비율':>7} {'시간(ms)':>10}")
for n, rows, pred, ms in rows_f3:
    print(f"{n:>3} {rows:>12,} {pred:>14,.0f} {rows / pred:>7.3f} {ms:>10.1f}")
# 출력:
#   홉        실측 행수       예측 N·f^n      비율     시간(ms)
#   1        6,051          6,051   1.000        0.0
#   2       18,332         18,307   1.001        1.0
#   3       55,587         55,389   1.004        4.7
#   4      168,385        167,579   1.005       16.0
#   5      510,081        507,009   1.006       51.9


# %% [markdown]
# 실측/예측 비율이 1.000 근처에 붙어 있습니다.
# **한 홉 늘 때마다 행 수가 $f$ 배**입니다. 이것이 조인 폭발이고,
# 이 곱셈은 `edge` 테이블이 관계형이라서 생긴 게 아니라
# 「한 노드에서 평균 $f$ 개를 따라간다」는 데이터의 성질에서 나옵니다.
# 그래서 문법을 PGQ 로 바꿔도 사라지지 않습니다.

# %%
# 팬아웃을 바꾸면 지수의 «밑»이 바뀐다. 문법과 무관하다.
sweep = {}
for f in (2, 3, 4):
    c2 = build(n_nodes=1000, fanout=f)
    e2 = c2.execute("SELECT COUNT(*) FROM edge").fetchone()[0]
    sweep[f] = measure(c2, 5, 1000, e2 / 1000)
    c2.close()

for f, res in sweep.items():
    print(f"f≈{f}: " + " → ".join(f"{r[1]:,}" for r in res))
# 출력:
# f≈2: 2,030 → 4,156 → 8,535 → 17,536 → 36,032
# f≈3: 3,013 → 9,172 → 27,827 → 84,410 → 256,345
# f≈4: 4,013 → 16,156 → 64,846 → 260,014 → 1,042,220
# (홉이 하나 늘 때마다 각각 약 2배 / 3배 / 4배. 지수의 밑이 곧 팬아웃이다.)


# %% [markdown]
# ## 4. 실행 계획: 엔진이 무엇을 만들고 있는가
#
# `EXPLAIN QUERY PLAN` 을 보면 사슬이 **중첩 루프 4단**으로 내려옵니다.
# 옵티마이저는 내가 쓴 순서(e1→e2→e3→e4)를 무시하고 자기 순서(e2부터)를 골랐고,
# 색인도 잘 탑니다. 즉 **한 단계의 비용은 최적화됐습니다**.
# 그런데 루프 단 수는 홉 수만큼 그대로 남습니다. 곱셈 구조가 여기 있습니다.

# %%
for row in con.execute("EXPLAIN QUERY PLAN " + chain_sql(4)):
    print("  ", row[-1])
# 출력:
#    SCAN e2
#    SEARCH e3 USING INDEX ix_edge_src (src=?)
#    SEARCH e1 USING COVERING INDEX ix_edge_dst (dst=?)
#    SEARCH e4 USING COVERING INDEX ix_edge_src (src=?)


# %% [markdown]
# ## 5. 「작은 쪽에서 시작」은 상수를 줄인다. 지수는 못 줄인다
#
# 「시드 노드 5개에 $n$ 홉 안에 도달하는 걷기의 수」를 두 순서로 셉니다.
#
# * **정방향(큰 쪽 먼저)**: `e1` 전체 스캔 → 앞으로 전진 → 마지막에 `dst IN 시드` 로 걸러낸다.
#   중간 결과 $\approx N \cdot f^{n}$.
# * **역방향(작은 쪽 먼저)**: 시드에 꽂히는 엣지부터 시작해 거꾸로 올라간다.
#   중간 결과 $\approx |S| \cdot f^{\,n}$.
#
# 결과 행 수는 **같습니다**. 상수가 $N$ 에서 $|S|$ 로 줄지만 $f^{\,n}$ 은 그대로입니다.

# %%
con.executescript("CREATE TABLE seed (id INTEGER PRIMARY KEY);")
con.executemany("INSERT INTO seed VALUES (?)", [(i,) for i in (7, 101, 555, 900, 1234)])
con.commit()


def forward_sql(n):  # 큰 쪽부터. CROSS JOIN 으로 순서를 고정한다.
    body = "FROM edge e1"
    for k in range(2, n + 1):
        body += f" CROSS JOIN edge e{k} ON e{k}.src = e{k - 1}.dst"
    return f"SELECT COUNT(*) {body} WHERE e{n}.dst IN (SELECT id FROM seed)"


def backward_sql(n):  # 작은 쪽(시드)부터 거꾸로.
    body = f"FROM seed s CROSS JOIN edge e{n} ON e{n}.dst = s.id"
    for k in range(n - 1, 0, -1):
        body += f" CROSS JOIN edge e{k} ON e{k}.dst = e{k + 1}.src"
    return f"SELECT COUNT(*) {body}"


def timed(q, repeat=3):
    best, rows = float("inf"), None
    for _ in range(repeat):
        t0 = time.perf_counter()
        rows = con.execute(q).fetchone()[0]
        best = min(best, time.perf_counter() - t0)
    return rows, best * 1000


order_cmp = []
print(f"{'홉':>3} {'결과행':>8} {'정방향 ms':>11} {'역방향 ms':>11} {'배속':>7}")
for n in range(1, 6):
    rf, mf = timed(forward_sql(n))
    rb, mb = timed(backward_sql(n))
    assert rf == rb, (n, rf, rb)
    order_cmp.append((n, rf, mf, mb))
    print(f"{n:>3} {rf:>8,} {mf:>11.1f} {mb:>11.1f} {mf / mb:>7.1f}x")
# 출력:
#   홉      결과행      정방향 ms      역방향 ms      배속
#   1       15         0.0         0.0     1.1x   ← 1홉은 측정 하한. 배속은 의미 없음
#   2       57         2.6         0.0   321.1x
#   3      178        10.8         0.0   391.7x
#   4      528        36.5         0.1   371.4x
#   5    1,591       118.4         0.3   395.5x


# %% [markdown]
# 300배 이상 빨라졌습니다. 그런데 **결과 행 수와 홉당 증가율은 똑같습니다**.
# 역방향 시간도 홉이 하나 늘 때마다 대략 $f$ 배씩 늡니다.
# 즉 순서 최적화(그리고 SQL/PGQ 같은 표기 개선)는
#
# $$T(n) \;\sim\; C \cdot f^{\,n}$$
#
# 에서 **$C$ 를 건드릴 뿐 $f^{\,n}$ 을 건드리지 못합니다.**
# 지수를 건드리는 유일한 방법은 데이터/질문을 바꾸는 것입니다.
# 홉 상한을 걸거나(9장), 팬아웃이 큰 슈퍼노드를 제외하거나, 결과 개수를 제한하는 것.

# %%
print("역방향(작은 쪽) 시간의 홉당 증가 배수:")
for i in range(1, len(order_cmp)):
    prev, cur = order_cmp[i - 1][3], order_cmp[i][3]
    print(f"  {order_cmp[i - 1][0]}홉 → {order_cmp[i][0]}홉 : x{cur / prev:.2f}")
# 출력:
# 역방향(작은 쪽) 시간의 홉당 증가 배수:
#   1홉 → 2홉 : x4.08
#   2홉 → 3홉 : x3.38
#   3홉 → 4홉 : x3.56
#   4홉 → 5홉 : x3.04
# (f≈3 이므로 홉당 약 3배. 작은 쪽에서 시작해도 지수는 살아 있다.)


# %% [markdown]
# ## 6. 시각화
#
# 로그 축에서 직선이면 지수 증가입니다. 세 팬아웃 모두 직선이고, 기울기가 $\log f$ 입니다.

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("중간 결과 행 수 (측정 vs 예측 N·f^n)",
                        "조인 순서: 시간은 바뀌고 지수는 그대로"),
    )
    colors = {2: "#4C78A8", 3: "#F58518", 4: "#54A24B"}
    for f, res in sweep.items():
        hops = [r[0] for r in res]
        fig.add_trace(go.Scatter(x=hops, y=[r[1] for r in res], mode="lines+markers",
                                 name=f"측정 f≈{f}", line=dict(color=colors[f], width=2)),
                      row=1, col=1)
        fig.add_trace(go.Scatter(x=hops, y=[r[2] for r in res], mode="lines",
                                 name=f"예측 f≈{f}", showlegend=False,
                                 line=dict(color=colors[f], width=1, dash="dot")),
                      row=1, col=1)

    # n=1 은 측정 하한(0.0ms) 이라 로그 축에서 왜곡을 준다. n>=2 만 그린다.
    cmp2 = [r for r in order_cmp if r[0] >= 2]
    hops = [r[0] for r in cmp2]
    fig.add_trace(go.Scatter(x=hops, y=[r[2] for r in cmp2], mode="lines+markers",
                             name="정방향(큰 쪽 먼저) ms", line=dict(color="#E45756", width=2)),
                  row=1, col=2)
    fig.add_trace(go.Scatter(x=hops, y=[r[3] for r in cmp2], mode="lines+markers",
                             name="역방향(작은 쪽 먼저) ms", line=dict(color="#72B7B2", width=2)),
                  row=1, col=2)

    fig.update_xaxes(title_text="홉 수 n", dtick=1, row=1, col=1)
    fig.update_xaxes(title_text="홉 수 n (n=1 은 측정 하한이라 제외)", dtick=1, row=1, col=2)
    fig.update_yaxes(title_text="행 수 (log)", type="log", row=1, col=1)
    fig.update_yaxes(title_text="벽시계 시간 ms (log)", type="log", row=1, col=2)
    fig.update_layout(
        title="조인 폭발은 표기가 아니라 카디널리티 곱의 문제다",
        template="plotly_white", width=1100, height=460,
        legend=dict(orientation="h", y=-0.22),
    )
    _show(fig)
    fig.write_image(os.path.join(HERE, "expy.png"), scale=2)
    print("expy.png 저장 완료")
except Exception as exc:  # noqa: BLE001
    print("시각화 건너뜀:", type(exc).__name__, exc)
# 출력: expy.png 저장 완료


# %% [markdown]
# ## 정리
#
# | 질문 | 답 |
# |---|---|
# | SQL/PGQ 가 바꾸는 것 | **표기**. `GRAPH_TABLE(... MATCH ...)` 로 의도를 그림처럼 쓴다. 데이터를 그래프 DB로 옮기지 않아도 된다 |
# | SQL/PGQ 가 바꾸지 않는 것 | **중간 결과 크기**. $|R_n| \approx N \cdot f^{\,n}$ 는 그대로다 |
# | 왜 남는가 | 문제는 «저장 위치»가 아니라 «따라가는 값». 홉마다 팬아웃 $f$ 가 곱해지는 건 데이터의 성질이다 |
# | 순서 최적화의 한계 | 상수 $C$ 만 줄인다. 위 실험에서 300배 빨라졌지만 홉당 증가율은 여전히 $\approx f$ |
# | 실제 대책 | 홉 상한, 슈퍼노드 제외, 결과 개수 제한, 사전 계산 — 즉 «질문»을 바꾸는 것 |
