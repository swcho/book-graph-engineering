# 필요 패키지: plotly, kaleido  (sqlite3 는 표준 라이브러리)
#   pip install plotly kaleido
#
# ex5_read_plan.py 의 두 질의(작은 쪽에서 시작 vs 큰 쪽에서 시작)를
# 의존성 없는 SQLite 로 재현한다. Kuzu 없이도 «시작점이 성능을 정한다»를
# 실행 계획 + 실측으로 확인하는 게 목표다.

# %% [markdown]
# # 시작점 하나가 성능을 정한다
#
# `ex5_read_plan.py`가 비교하는 두 질의는 **답이 같고 시작점이 다르다.**
#
# | | 시작 집합 | 필터 대상 | 첫 단계 후보 수 |
# |---|---|---|---|
# | 작은 쪽 | `City` (12개) | `City.name` = 주 키 | 1 |
# | 큰 쪽 | `Person` (2만 명) | `Person.city` = 색인 없는 열 | 20,000 |
#
# 비용 모형은 이렇다. 간선 수 $|E|$, 도시 수 $|C|$, 사람 수 $|P|$일 때
#
# $$\text{cost}_{\text{small}} \approx 1 + \frac{|E|}{|C|}, \qquad
#   \text{cost}_{\text{large}} \approx |P| + \frac{|E|}{|C|}$$
#
# 낭비 배수는 필터 선택도 $\sigma = 1/|C|$의 역수다.
#
# $$\frac{\text{cost}_{\text{large}}}{\text{cost}_{\text{small}}} \approx \frac{|P|}{|E|/|C|} = |C| = \frac{1}{\sigma}$$
#
# 아래에서 SQLite 로 이 식을 실측과 맞춰 본다.

# %%
import sqlite3
import time

N_CITY = 12


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


print("sqlite3", sqlite3.sqlite_version)
# 출력: sqlite3 3.51.0

# %% [markdown]
# ## 1. 데이터 만들기
#
# `ex5_read_plan.py`와 같은 모양이다.
#
# - `city` 12개 (`도시0` ~ `도시11`), `name`에 UNIQUE
# - `person` N명, `city_name`은 **색인 없는 비정규화 문자열** (`i % 12`로 배분)
# - `lives_in` 간선 N개, `city_id`에 색인 (그래프 DB의 인접 리스트 대역)
#
# 즉 도시 하나에 사는 사람은 약 $N/12$명.


# %%
def build(n_person, n_city=N_CITY, index_person_city=False):
    con = sqlite3.connect(":memory:")
    con.executescript(
        """
        CREATE TABLE city   (id INTEGER PRIMARY KEY, name TEXT UNIQUE);
        CREATE TABLE person (id INTEGER PRIMARY KEY, city_name TEXT);
        CREATE TABLE lives_in (person_id INTEGER, city_id INTEGER);
        """
    )
    con.executemany(
        "INSERT INTO city VALUES (?,?)", [(i, f"도시{i}") for i in range(n_city)]
    )
    con.executemany(
        "INSERT INTO person VALUES (?,?)",
        [(i, f"도시{i % n_city}") for i in range(n_person)],
    )
    con.executemany(
        "INSERT INTO lives_in VALUES (?,?)",
        [(i, i % n_city) for i in range(n_person)],
    )
    # 간선을 양방향으로 탈 수 있게 (그래프 DB 의 인접 리스트에 해당)
    con.executescript(
        """
        CREATE INDEX ix_edge_city   ON lives_in(city_id);
        CREATE INDEX ix_edge_person ON lives_in(person_id);
        """
    )
    if index_person_city:
        con.execute("CREATE INDEX ix_person_city ON person(city_name)")
    con.commit()
    return con


con = build(20_000)
print(con.execute("SELECT COUNT(*) FROM person").fetchone()[0], "명")
print(con.execute("SELECT COUNT(*) FROM city").fetchone()[0], "개 도시")
print(
    con.execute(
        "SELECT COUNT(*) FROM lives_in l JOIN city c ON c.id=l.city_id WHERE c.name='도시3'"
    ).fetchone()[0],
    "명이 도시3 거주",
)
# 출력: 20000 명
# 출력: 12 개 도시
# 출력: 1667 명이 도시3 거주

# %% [markdown]
# ## 2. 같은 뜻, 두 가지 시작점
#
# SQLite에서 `CROSS JOIN`은 **조인 순서 재정렬을 금지하는 힌트**다.
# 이걸로 최적화기의 판단을 덮어쓰고 두 시작점을 강제한다.
# (실무에서 힌트는 최후 수단이지만, 여기서는 대조 실험을 만드는 도구로 쓴다.)

# %%
Q_SMALL_FIRST = """
SELECT COUNT(*)
FROM city c
CROSS JOIN lives_in l ON l.city_id = c.id
CROSS JOIN person   p ON p.id      = l.person_id
WHERE c.name = ?
"""

Q_LARGE_FIRST = """
SELECT COUNT(*)
FROM person p
CROSS JOIN lives_in l ON l.person_id = p.id
CROSS JOIN city     c ON c.id        = l.city_id
WHERE p.city_name = ?
"""

print("작은 쪽:", con.execute(Q_SMALL_FIRST, ("도시3",)).fetchone()[0])
print("큰   쪽:", con.execute(Q_LARGE_FIRST, ("도시3",)).fetchone()[0])
# 출력: 작은 쪽: 1667
# 출력: 큰   쪽: 1667
# → 답은 똑같다. 다른 것은 «가는 길»뿐이다.

# %% [markdown]
# ## 3. 실행 계획을 읽는다 (`EXPLAIN QUERY PLAN`)
#
# 계획에서 볼 것 셋 (예제가 직접 말하는 체크리스트):
#
# 1. 어느 테이블부터 훑는가 («스캔»이 어디에 있나)
# 2. 색인을 타는가 아니면 전체를 훑는가
# 3. 중간 결과가 몇 행으로 추정되는가


# %%
def plan(con, q, param="도시3"):
    for _id, _parent, _aux, detail in con.execute("EXPLAIN QUERY PLAN " + q, (param,)):
        print("   ", detail)


print("[작은 쪽(City)에서 시작]")
plan(con, Q_SMALL_FIRST)
print("\n[큰 쪽(Person)에서 시작]")
plan(con, Q_LARGE_FIRST)
# 출력:
# [작은 쪽(City)에서 시작]
#     SEARCH c USING COVERING INDEX sqlite_autoindex_city_1 (name=?)
#     SEARCH l USING INDEX ix_edge_city (city_id=?)
#     SEARCH p USING INTEGER PRIMARY KEY (rowid=?)
#
# [큰 쪽(Person)에서 시작]
#     SCAN p
#     SEARCH l USING INDEX ix_edge_person (person_id=?)
#     SEARCH c USING INTEGER PRIMARY KEY (rowid=?)
#
# 읽는 법:
#   SEARCH = 색인 탐색(찍어서 간다),  SCAN = 전체 훑기.
#   작은 쪽은 첫 줄이 SEARCH ... (name=?) → 도시 «1개»를 콕 집는다.
#   큰 쪽은 첫 줄이 SCAN p → person 2만 행을 «전부» 읽고 나서 필터한다.
#   Kuzu 의 PRIMARY_KEY_SCAN_NODE_TABLE vs SCAN_NODE_TABLE+FILTER 와 같은 대비다.

# %% [markdown]
# ## 4. 얼마나 만지는가 — VM 명령 수로 재기
#
# SQLite의 `set_progress_handler(handler, n)`는 가상 머신 명령 `n`개마다
# 콜백을 부른다. 콜백 횟수 × n ≈ 실제로 수행한 작업량이다.
# "몇 행을 만졌나"의 대역으로 쓰기 좋다.


# %%
def vm_steps(con, q, param="도시3", every=100):
    calls = 0

    def h():
        nonlocal calls
        calls += 1
        return 0  # 0 = 계속 진행

    con.set_progress_handler(h, every)
    con.execute(q, (param,)).fetchone()
    con.set_progress_handler(None, 0)
    return calls * every


def timed(con, q, param="도시3", repeat=5):
    best = float("inf")
    for _ in range(repeat):
        t0 = time.perf_counter()
        con.execute(q, (param,)).fetchone()
        best = min(best, time.perf_counter() - t0)
    return best * 1000  # ms


s_steps, l_steps = vm_steps(con, Q_SMALL_FIRST), vm_steps(con, Q_LARGE_FIRST)
s_ms, l_ms = timed(con, Q_SMALL_FIRST), timed(con, Q_LARGE_FIRST)

print(f"작은 쪽(City)에서 시작   {s_ms:7.2f} ms   VM 명령 {s_steps:,}")
print(f"큰 쪽(Person)에서 시작   {l_ms:7.2f} ms   VM 명령 {l_steps:,}")
print(f"\n시간 배수 {l_ms / s_ms:.1f}x, 작업량 배수 {l_steps / s_steps:.1f}x")
print(f"이론 예측(선택도의 역수) = 도시 수 = {N_CITY}x")
# 출력: 작은 쪽(City)에서 시작      0.47 ms   VM 명령 11,700
# 출력: 큰 쪽(Person)에서 시작      1.32 ms   VM 명령 76,700
# 출력:
# 출력: 시간 배수 2.8x, 작업량 배수 6.6x
# 출력: 이론 예측(선택도의 역수) = 도시 수 = 12x
# → 작업량(VM 명령)은 6.6배, 시간은 2.8배 차이. 예측 12배보다 낮게 나온다.
#   이유: 두 계획의 «행당 단가»가 다르다. 큰 쪽의 2만 행은 순차 스캔이라 한 행이 싸고,
#   작은 쪽이 남기는 1,667행은 색인 탐색 + rowid 조회라 한 행이 비싸다.
#   $1/\sigma$ 는 «만지는 행 수»의 배수이지 «시간»의 배수는 아니다.
#   그래도 방향은 분명하다 — 시작점만 바꿔서 세 배가 붙는다.

# %% [markdown]
# ## 5. 규모를 키우면 격차가 벌어진다
#
# 두 비용 모두 $N$에 비례하지만 기울기가 다르다.
#
# $$\text{cost}_{\text{small}} \approx \frac{N}{|C|}, \qquad \text{cost}_{\text{large}} \approx N$$
#
# 비율은 $|C|$로 대략 일정하고, **절대 격차는 $N$에 비례해 벌어진다.**
# 그리고 도시 수가 늘면(선택도가 좋아지면) 비율 자체가 커진다.

# %%
SIZES = [2_500, 5_000, 10_000, 20_000, 40_000, 80_000]
rows = []
for n in SIZES:
    c = build(n)
    rows.append(
        {
            "n": n,
            "small_ms": timed(c, Q_SMALL_FIRST),
            "large_ms": timed(c, Q_LARGE_FIRST),
            "small_steps": vm_steps(c, Q_SMALL_FIRST),
            "large_steps": vm_steps(c, Q_LARGE_FIRST),
        }
    )
    c.close()

print(f"{'사람 수':>9} {'작은 쪽':>10} {'큰 쪽':>10} {'배수':>7} {'절대 격차':>10}")
for r in rows:
    print(
        f"{r['n']:>9,} {r['small_ms']:>9.2f}ms {r['large_ms']:>9.2f}ms "
        f"{r['large_ms'] / r['small_ms']:>6.1f}x {r['large_ms'] - r['small_ms']:>8.2f}ms"
    )
# 출력:      사람 수       작은 쪽        큰 쪽      배수      절대 격차
# 출력:     2,500      0.06ms      0.15ms    2.7x     0.10ms
# 출력:     5,000      0.11ms      0.31ms    2.8x     0.20ms
# 출력:    10,000      0.22ms      0.62ms    2.8x     0.40ms
# 출력:    20,000      0.44ms      1.25ms    2.8x     0.81ms
# 출력:    40,000      0.90ms      2.54ms    2.8x     1.64ms
# 출력:    80,000      1.85ms      5.07ms    2.7x     3.21ms
# → 배수는 2.8x 근처로 «일정»하고, 절대 격차는 0.10ms → 3.21ms 로 «비례해 벌어진다».
#   둘 다 O(N) 이지만 상수가 다르다. 그 상수를 좌우하는 것이 선택도다.

# %% [markdown]
# ## 6. 선택도를 바꿔 보면 — 배수는 도시 수를 따라간다
#
# 사람 수를 2만으로 고정하고 도시 수만 늘린다.
# 도시가 많아질수록 `c.name = ?` 의 선택도 $\sigma = 1/|C|$가 좋아지고,
# 작은 쪽에서 시작할 때의 이득도 그만큼 커진다.

# %%
CITY_COUNTS = [4, 12, 50, 200, 1_000]
sel_rows = []
for nc in CITY_COUNTS:
    c = build(20_000, n_city=nc)
    s, l = timed(c, Q_SMALL_FIRST), timed(c, Q_LARGE_FIRST)
    sel_rows.append({"n_city": nc, "small_ms": s, "large_ms": l, "ratio": l / s})
    c.close()
    print(f"도시 {nc:>5}개  선택도 1/{nc:<5} 배수 {l / s:>7.1f}x  (예측 {nc}x)")
# 출력: 도시     4개  선택도 1/4     배수     1.8x  (예측 4x)
# 출력: 도시    12개  선택도 1/12    배수     2.8x  (예측 12x)
# 출력: 도시    50개  선택도 1/50    배수     6.4x  (예측 50x)
# 출력: 도시   200개  선택도 1/200   배수    19.3x  (예측 200x)
# 출력: 도시  1000개  선택도 1/1000  배수   101.6x  (예측 1000x)
# → 도시 4개일 때 2배도 안 되던 격차가, 도시 1,000개에서 100배가 된다.
#   log-log 기울기는 약 0.8 (배수 ~ |C|^0.8). 예측선보다 아래에 붙는 건
#   위에서 본 «행당 단가» 차이 때문이지만, «선택도가 좋아질수록 시작점 실수의
#   대가가 커진다»는 결론은 그대로다. 여기가 3장 «조인 폭발»과 만나는 지점이다.

# %% [markdown]
# ## 7. 그러면 나는 뭘 할 수 있나 — 색인 하나 더하기
#
# 큰 쪽에서 시작하는 게 나쁜 게 아니라, **색인 없이** 큰 쪽에서 시작하는 게 나쁘다.
# `person(city_name)`에 색인을 만들면 `SCAN p`가 `SEARCH p`로 바뀐다.

# %%
c_idx = build(20_000, index_person_city=True)
print("[색인 추가 후 — 큰 쪽에서 시작]")
plan(c_idx, Q_LARGE_FIRST)
before = rows[3]["large_ms"]
after = timed(c_idx, Q_LARGE_FIRST)
print(f"\n색인 전 {before:.2f} ms  →  색인 후 {after:.2f} ms  ({before / after:.1f}x 개선)")
print(f"작은 쪽에서 시작: {rows[3]['small_ms']:.2f} ms")
c_idx.close()
# 출력: [색인 추가 후 — 큰 쪽에서 시작]
#     SEARCH p USING COVERING INDEX ix_person_city (city_name=?)
#     SEARCH l USING INDEX ix_edge_person (person_id=?)
#     SEARCH c USING INTEGER PRIMARY KEY (rowid=?)
#
# 출력: 색인 전 1.25 ms  →  색인 후 0.59 ms  (2.1x 개선)
# 출력: 작은 쪽에서 시작: 0.44 ms
# → SCAN p 가 SEARCH p 로 바뀌었다. 전체 훑기가 색인 탐색이 됐고
#   작은 쪽에서 시작한 것과 거의 같은 수준까지 붙었다.
#   개입 순서: 질의 재작성 → 색인 → 힌트. 앞쪽이 이식성을 덜 해친다.

# %% [markdown]
# ## 8. 시각화
#
# - 왼쪽: 사람 수 대비 실행 시간 (양쪽 다 $O(N)$, 기울기가 다르다)
# - 오른쪽: 도시 수(=선택도의 역수) 대비 낭비 배수

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "사람 수 대비 실행 시간 (도시 12개 고정)",
            "선택도 대비 낭비 배수 (사람 2만 고정)",
        ),
    )
    ns = [r["n"] for r in rows]
    fig.add_trace(
        go.Scatter(
            x=ns,
            y=[r["large_ms"] for r in rows],
            name="큰 쪽(Person)에서 시작",
            mode="lines+markers",
            line=dict(color="#d62728", width=3),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=ns,
            y=[r["small_ms"] for r in rows],
            name="작은 쪽(City)에서 시작",
            mode="lines+markers",
            line=dict(color="#1f77b4", width=3),
        ),
        row=1,
        col=1,
    )
    ncs = [r["n_city"] for r in sel_rows]
    fig.add_trace(
        go.Scatter(
            x=ncs,
            y=[r["ratio"] for r in sel_rows],
            name="실측 배수",
            mode="lines+markers",
            line=dict(color="#d62728", width=3),
            showlegend=False,
        ),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=ncs,
            y=ncs,
            name="이론 예측 = 1/선택도",
            mode="lines",
            line=dict(color="#7f7f7f", width=2, dash="dash"),
        ),
        row=1,
        col=2,
    )
    fig.update_xaxes(title_text="사람 수", type="log", row=1, col=1)
    fig.update_yaxes(title_text="실행 시간 (ms)", type="log", row=1, col=1)
    fig.update_xaxes(title_text="도시 수 |C|", type="log", row=1, col=2)
    fig.update_yaxes(title_text="큰 쪽 / 작은 쪽 (배)", type="log", row=1, col=2)
    fig.update_layout(
        title_text="시작점 선택이 성능을 정한다 — SQLite 재현",
        template="plotly_white",
        width=1100,
        height=460,
        legend=dict(orientation="h", y=-0.22),
    )
    _show(fig)

    import pathlib

    out = pathlib.Path(__file__).with_name("expy.png") if "__file__" in dir() else pathlib.Path("expy.png")
    fig.write_image(str(out), scale=2)  # kaleido 필요
    print("saved:", out)
except ImportError as e:
    print("시각화 생략 (필요 패키지 없음):", e)
# 출력: saved: .../expy.png

# %% [markdown]
# ## 정리
#
# | 관점 | 작은 쪽(City)에서 시작 | 큰 쪽(Person)에서 시작 |
# |---|---|---|
# | 계획 첫 연산자 | `SEARCH c ... (name=?)` / Kuzu `PRIMARY_KEY_SCAN_NODE_TABLE` | `SCAN p` / Kuzu `SCAN_NODE_TABLE`+`FILTER` |
# | 첫 단계 카디널리티 | 1 | 20,000 |
# | 총 접촉 행수 | $1 + N/|C|$ | $N + N/|C|$ |
# | 2만 명 실측 (SQLite) | 0.44 ms | 1.25 ms |
# | 2만 명 실측 (Kuzu 0.11.3) | 0.39 ms | 0.84 ms |
#
# - 접촉 행수의 낭비 배수는 $1/\sigma = |C|$. 시간 배수는 «행당 단가» 차이 때문에
#   그보다 작게 나오지만, **선택도가 좋아질수록 시작점 실수의 대가가 커진다**는
#   관계는 6절에서 확인했다 (도시 4개 1.8배 → 1,000개 101배).
# - 선언형 언어에서는 시작점을 **최적화기**가 고른다. 사용자의 개입은
#   **① 질의 재작성(색인 타는 열로 필터, 필터 밀어넣기, 통계 갱신) → ② 색인 → ③ 힌트** 순.
#   뒤로 갈수록 강제력은 세지고 이식성은 나빠진다.
# - `EXPLAIN`은 계획만 보여 준다. 실측 행수·시간은 `PROFILE`(Kuzu) / `EXPLAIN ANALYZE`(PG).
# - 11장은 "계획을 읽을 줄 알아야 한다"까지. 고치는 법은 33장.
