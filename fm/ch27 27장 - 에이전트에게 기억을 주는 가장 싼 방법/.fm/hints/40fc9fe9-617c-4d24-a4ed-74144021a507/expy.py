# 필요 패키지: kuzu, plotly, kaleido  (pip install kuzu plotly kaleido)
# 실행: python3 expy.py  /  또는 VSCode·Jupyter 에서 셀 단위 실행

# %% [markdown]
# # 시점 질의 — `e.vfrom <= t AND e.vto >= t`
#
# 에이전트의 기억은 **영원한 사실**이 아니다. 「박민수가 결제팀을 이끈다」는
# 2024년에는 참이고 2026년에는 거짓이다. 그래서 관계(엣지)마다 **유효 시간
# (valid time)** 구간 $[\mathit{vfrom},\ \mathit{vto}]$ 를 붙인다.
#
# 시점 $t$ 에서의 진실은 이 조건 하나로 뽑는다.
#
# $$\mathit{vfrom} \le t \ \wedge\ \mathit{vto} \ge t$$
#
# Cypher 로는 이렇게 쓴다.
#
# ```cypher
# MATCH (a:N)-[e:R]->(b:N)
# WHERE e.vfrom <= $t AND e.vto >= $t
# RETURN a.name, e.kind, b.name
# ```
#
# 핵심 두 가지.
#
# 1. **아직 끝나지 않은 사실의 `vto` 는 `NULL` 이 아니라 `9999-12-31`** 이다.
#    `NULL` 이면 `e.vto >= $t` 비교가 `NULL`(= 거짓 취급)이 되어 「지금도 참인
#    사실」이 전부 사라진다. 열린 구간을 **먼 미래의 상수**로 닫아 두면
#    분기 없이 부등식 하나로 끝난다. 이를 sentinel(파수꾼) 값이라 부른다.
# 2. **오래된 사실을 지우지 않는다.** 새 사실이 들어오면 옛 사실의 `vto` 를
#    채워 「닫을」 뿐이다. 지우면 「2025년 3월에 팀장이 누구였지」를 못 묻는다.

# %%
from datetime import date

# 문자열 날짜는 ISO-8601(YYYY-MM-DD)이라 사전순 비교 = 시간순 비교다.
# 그래서 STRING 칼럼에 그대로 부등식을 걸어도 맞는 답이 나온다.
FOREVER = "9999-12-31"

# (주어, 관계, 목적어, 유효 시작, 유효 끝(None = 지금도 참), 기록 시각)
FACTS = [
    ("박민수", "이끔", "결제팀", "2024-01-01", "2026-03-31", "2024-01-05"),
    ("이서연", "이끔", "결제팀", "2026-04-01", None, "2026-04-02"),
    ("나", "속함", "결제팀", "2023-06-01", None, "2023-06-01"),
    ("나", "선호", "채식", "2025-09-01", None, "2025-09-10"),
    ("나", "선호", "육식", "2023-01-01", "2025-08-31", "2023-01-15"),
]


def normalize(facts):
    """열린 구간(None)을 9999-12-31 로 닫아 둔다."""
    return [(s, k, o, vf, vt or FOREVER, rec) for s, k, o, vf, vt, rec in facts]


ROWS = normalize(FACTS)
for r in ROWS:
    print(r)
# 출력:
# ('박민수', '이끔', '결제팀', '2024-01-01', '2026-03-31', '2024-01-05')
# ('이서연', '이끔', '결제팀', '2026-04-01', '9999-12-31', '2026-04-02')
# ('나', '속함', '결제팀', '2023-06-01', '9999-12-31', '2023-06-01')
# ('나', '선호', '채식', '2025-09-01', '9999-12-31', '2025-09-10')
# ('나', '선호', '육식', '2023-01-01', '2025-08-31', '2023-01-15')

# %% [markdown]
# ## 1단계 — 시간을 안 보면 모순이 같이 산다
#
# 조건 없이 전부 꺼내면 「박민수도 팀장, 이서연도 팀장」, 「채식도 선호,
# 육식도 선호」가 동시에 나온다. 그래프가 틀린 게 아니라 **질의가 시간 칸을
# 안 봤을 뿐**이다.

# %%
def ask_no_time(rows):
    return sorted((s, k, o) for s, k, o, *_ in rows)


for s, k, o in ask_no_time(ROWS):
    print(f"  {s} -{k}-> {o}")
# 출력:
#   나 -선호-> 육식
#   나 -선호-> 채식
#   나 -속함-> 결제팀
#   박민수 -이끔-> 결제팀
#   이서연 -이끔-> 결제팀

# %% [markdown]
# ## 2단계 — 시점 $t$ 를 넣으면 「그때의 진실」이 나온다
#
# 필터는 부등식 두 개뿐이다. 분기도, `NULL` 검사도 없다.

# %%
def ask_at(rows, t):
    """시점 질의: vfrom <= t AND vto >= t"""
    return sorted((s, k, o) for s, k, o, vf, vt, _ in rows if vf <= t <= vt)


for t in ["2024-06-01", "2025-01-15", "2026-05-20"]:
    print(f"[{t} 시점에 물으면]")
    for s, k, o in ask_at(ROWS, t):
        print(f"  {s} -{k}-> {o}")
    print()
# 출력:
# [2024-06-01 시점에 물으면]
#   나 -선호-> 육식
#   나 -속함-> 결제팀
#   박민수 -이끔-> 결제팀
#
# [2025-01-15 시점에 물으면]
#   나 -선호-> 육식
#   나 -속함-> 결제팀
#   박민수 -이끔-> 결제팀
#
# [2026-05-20 시점에 물으면]
#   나 -선호-> 채식
#   나 -속함-> 결제팀
#   이서연 -이끔-> 결제팀
#

# %% [markdown]
# 같은 그래프인데 답이 다르다. **그게 맞는 것이다.**
#
# 사용자가 "팀장님께 보고서 보내 줘"라고 하면 `t = today` 로 물어야 하고,
# "2025년 3월에 팀장이 누구였지"라고 하면 `t = 2025-03-01` 로 물어야 한다.
# 요약문은 시간 칸을 갖고 다니지 않으므로 이 구분을 못 한다(24장).

# %%
today = date.today().isoformat()
print("오늘:", today)
for s, k, o in ask_at(ROWS, today):
    print(f"  {s} -{k}-> {o}")
# 출력:
# 오늘: 2026-08-18
#   나 -선호-> 채식
#   나 -속함-> 결제팀
#   이서연 -이끔-> 결제팀

# %% [markdown]
# ## 3단계 — `vto` 를 `NULL` 로 두면 왜 깨지는가
#
# SQL/Cypher 의 3값 논리에서 `NULL >= '2026-05-20'` 는 참도 거짓도 아닌
# `NULL` 이고, `WHERE` 절은 이를 **거짓처럼** 버린다. 그래서 "지금도 참인
# 사실"이 통째로 사라진다. 아래는 그 상황을 파이썬으로 흉내 낸 것이다.

# %%
def ask_at_nullish(facts, t):
    """vto 가 None 인 행을 3값 논리처럼 버리는(=버그) 버전."""
    out = []
    for s, k, o, vf, vt, _ in facts:
        if vt is None:          # NULL >= t  ->  NULL  ->  WHERE 가 버림
            continue
        if vf <= t <= vt:
            out.append((s, k, o))
    return sorted(out)


t = "2026-05-20"
print("sentinel 사용 :", ask_at(ROWS, t))
print("NULL 방치     :", ask_at_nullish(FACTS, t))
# 출력:
# sentinel 사용 : [('나', '선호', '채식'), ('나', '속함', '결제팀'), ('이서연', '이끔', '결제팀')]
# NULL 방치     : []

# %% [markdown]
# `NULL` 을 그대로 두면 `WHERE e.vto >= $t` 만으로는 답이 **비어 버린다**.
# 굳이 `NULL` 을 쓰려면 `(e.vto IS NULL OR e.vto >= $t)` 처럼 분기를 붙여야
# 하는데, 그러면 조건이 길어지고 인덱스도 잘 안 탄다. 그래서 `9999-12-31`
# 이라는 **먼 미래 상수**로 미리 닫아 두는 쪽이 싸다.

# %% [markdown]
# ## 4단계 — 새 사실이 들어오면 옛 사실의 `vto` 를 닫는다
#
# 「이끔」이나 「선호(주식 취향)」처럼 **동시에 하나만 참일 수 있는 관계**를
# 단일 값(single-valued) 관계 목록으로 코드에 적어 둔다. 새 사실이 들어오면
# 지우는 게 아니라 옛 사실의 `vto` 를 새 사실 시작 하루 전으로 채운다.
#
# Cypher 로는 이렇다.
#
# ```cypher
# MATCH (a:N)-[e:R {kind:'이끔'}]->(b:N {name:'결제팀'})
# WHERE e.vto = '9999-12-31'
# SET e.vto = $day_before
# ```

# %%
from datetime import timedelta

SINGLE_VALUED = {"이끔", "선호"}   # 동시에 하나만 참일 수 있는 관계


def prev_day(iso):
    d = date.fromisoformat(iso) - timedelta(days=1)
    return d.isoformat()


def insert_fact(rows, s, k, o, vfrom, recorded):
    """새 사실 삽입 + 충돌하는 열린 사실 닫기. 옛 행은 지우지 않는다."""
    closed = []
    if k in SINGLE_VALUED:
        for i, (rs, rk, ro, rvf, rvt, rrec) in enumerate(rows):
            # 같은 주체·같은 관계로 열려 있는 사실만 닫는다
            same_slot = (rk == k) and (rs == s or ro == o)
            if same_slot and rvt == FOREVER and rvf < vfrom:
                rows[i] = (rs, rk, ro, rvf, prev_day(vfrom), rrec)
                closed.append((rs, rk, ro, rows[i][4]))
    rows.append((s, k, o, vfrom, FOREVER, recorded))
    return closed


rows2 = list(ROWS)
closed = insert_fact(rows2, "정하늘", "이끔", "결제팀", "2026-07-01", "2026-07-02")
print("닫힌 사실:", closed)
print("2026-06-15 :", ask_at(rows2, "2026-06-15"))
print("2026-07-15 :", ask_at(rows2, "2026-07-15"))
# 출력:
# 닫힌 사실: [('이서연', '이끔', '결제팀', '2026-06-30')]
# 2026-06-15 : [('나', '선호', '채식'), ('나', '속함', '결제팀'), ('이서연', '이끔', '결제팀')]
# 2026-07-15 : [('나', '선호', '채식'), ('나', '속함', '결제팀'), ('정하늘', '이끔', '결제팀')]

# %% [markdown]
# 이서연의 행은 **삭제되지 않았다**. `vto` 만 `2026-06-30` 으로 닫혔다.
# 그래서 과거 시점 질의는 여전히 이서연을 돌려준다. 이것이 "지우지 말고
# 끝나는 시각을 적어라"의 실체다.

# %% [markdown]
# ## 5단계 — 실제 Cypher 로 확인 (kuzu)
#
# 위 파이썬 필터가 그래프 DB 에서 문자 그대로 같은 모양이라는 것을 본다.

# %%
import shutil
import tempfile

try:
    import kuzu

    tmp = tempfile.mkdtemp()
    db = kuzu.Database(tmp + "/db")
    c = kuzu.Connection(db)
    c.execute("CREATE NODE TABLE N(name STRING, PRIMARY KEY(name))")
    c.execute("CREATE REL TABLE R(FROM N TO N, kind STRING, "
              "vfrom STRING, vto STRING, recorded STRING)")
    names = set()
    for s, _k, o, *_ in ROWS:
        names |= {s, o}
    for n in sorted(names):
        c.execute("CREATE (:N {name:$n})", {"n": n})
    for s, k, o, vf, vt, rec in ROWS:
        c.execute(
            "MATCH (a:N {name:$s}),(b:N {name:$o}) "
            "CREATE (a)-[:R {kind:$k, vfrom:$vf, vto:$vt, recorded:$r}]->(b)",
            {"s": s, "o": o, "k": k, "vf": vf, "vt": vt, "r": rec})

    CYPHER = ("MATCH (a:N)-[e:R]->(b:N) WHERE e.vfrom <= $t AND e.vto >= $t "
              "RETURN a.name, e.kind, b.name ORDER BY a.name")
    for t in ["2025-01-15", "2026-05-20"]:
        r = c.execute(CYPHER, {"t": t})
        print(f"[{t}]")
        while r.has_next():
            a, k, b = r.get_next()
            print(f"  {a} -{k}-> {b}")
    shutil.rmtree(tmp, ignore_errors=True)
except ImportError:
    print("kuzu 없음 — pip install kuzu")
# 출력:
# [2025-01-15]
#   나 -선호-> 육식
#   나 -속함-> 결제팀
#   박민수 -이끔-> 결제팀
# [2026-05-20]
#   나 -선호-> 채식
#   나 -속함-> 결제팀
#   이서연 -이끔-> 결제팀

# %% [markdown]
# ## 6단계 — 유효 구간 간트 차트
#
# 가로축이 시간, 막대 하나가 사실 하나의 $[\mathit{vfrom},\ \mathit{vto}]$ 다.
# 세로 점선이 시점 $t$ 이고, **점선이 가로지르는 막대들이 곧 질의 결과**다.
# `9999-12-31` 은 그림에서 잘라 화살표(∞)로 표시했다.

# %%
def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


import plotly.graph_objects as go

CLIP = "2027-06-30"     # 9999-12-31 을 그림에서 자를 지점
PROBES = ["2025-01-15", "2026-05-20"]

labels, starts, ends, opens = [], [], [], []
for s, k, o, vf, vt, _ in ROWS:
    labels.append(f"{s} -{k}-> {o}")
    starts.append(vf)
    ends.append(CLIP if vt == FOREVER else vt)
    opens.append(vt == FOREVER)

fig = go.Figure()
for i, (lab, vf, vt, is_open) in enumerate(zip(labels, starts, ends, opens)):
    fig.add_trace(go.Scatter(
        x=[vf, vt], y=[lab, lab], mode="lines",
        line=dict(width=18, color="#8aa9d6" if is_open else "#c9a0a0"),
        hovertemplate=f"{lab}<br>{vf} ~ {'현재(9999-12-31)' if is_open else vt}<extra></extra>",
        showlegend=False))
    if is_open:
        fig.add_annotation(x=vt, y=lab, text="∞", showarrow=False,
                           xshift=14, font=dict(size=16, color="#4a6f9e"))

for p in PROBES:
    fig.add_vline(x=p, line=dict(color="#d1495b", width=2, dash="dash"))
    fig.add_annotation(x=p, y=1.04, yref="paper", text=f"t = {p}",
                       showarrow=False, font=dict(size=12, color="#d1495b"))

fig.update_layout(
    title="유효 시간 구간과 시점 질의 (vfrom ≤ t ≤ vto)",
    xaxis=dict(title="유효 시간", type="date",
               range=["2022-10-01", "2027-09-30"]),
    yaxis=dict(autorange="reversed"),
    template="plotly_white", height=380,
    margin=dict(l=170, r=60, t=80, b=50))

_show(fig)

import os
_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_png, width=1000, height=380, scale=2)
print("saved:", _png)
# 출력:
# saved: /.../.fm/hints/40fc9fe9-617c-4d24-a4ed-74144021a507/expy.png

# %% [markdown]
# ## 정리
#
# | 항목 | 값 |
# |---|---|
# | 시점 질의 조건 | `e.vfrom <= t AND e.vto >= t` |
# | 열린 사실의 `vto` | `9999-12-31` (sentinel, `NULL` 아님) |
# | 사실이 끝날 때 | 삭제가 아니라 `vto` 를 채워 **닫는다** |
# | 닫는 시점 | 새 사실 `vfrom` 의 하루 전 (구간이 안 겹치게) |
# | 닫을 대상 | 단일 값 관계 목록(`이끔`, `선호` …)에 있는 열린 사실 |
#
# 이 조건 하나가 「지금 팀장은 누구인가」와 「2025년 3월 팀장은 누구였는가」를
# **같은 그래프에서** 답하게 만든다. 그리고 모순된 사실을 컨텍스트에 함께
# 밀어 넣는 사고를 막는다 — 모순된 기억을 받은 모델은 「최근 것」이 아니라
# 「자주 나온 것」을 고르기 때문이다.
