# %% [markdown]
# # 날짜를 문자열로 비교하면 어떤 방식으로 틀리는가
#
# **답: 예외가 나지 않고 조용히 반대로 정렬된다. 그래서 발견이 늦다.**
#
# 문자열 비교는 사전순(lexicographic)이다. 왼쪽부터 문자 코드를 한 자리씩 비교하기
# 때문에, 모든 값이 `YYYY-MM-DD`처럼 **자릿수가 완전히 같을 때만** 우연히 시간순과
# 일치한다. 자릿수가 하나라도 어긋나는 순간(`2024-3-11`, `2024/03/11`, `2024-08` 등)
# 비교 결과가 뒤집히는데, 이때 아무런 예외도 발생하지 않는다.
#
# 이 스크립트는 16장 예제 3(`ex3_string_dates.py`)의 내용을 단계별로 재현한다.

# %%
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용. 나머지 셀은 표준 라이브러리만 사용)
from datetime import date


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1단계 — 틀리는 원리: 사전순은 문자 코드 순이다
#
# `"2024-3-11"`과 `"2024-12-01"`을 비교해 보자. 다섯 번째 글자에서
# `'3'`(코드 51)과 `'1'`(코드 49)이 맞붙는데, `'3' > '1'`이므로 문자열 비교는
# **3월이 12월보다 크다(늦다)**고 답한다.
#
# $$\text{"2024-3-11"} > \text{"2024-12-01"} \quad (\text{문자열}) \qquad
# \text{3월 11일} < \text{12월 1일} \quad (\text{실제})$$

# %%
a, b = "2024-3-11", "2024-12-01"

print(f"문자열 비교:  {a!r} > {b!r}  →  {a > b}")
print(f"실제 날짜:    date(2024,3,11) > date(2024,12,1)  →  {date(2024, 3, 11) > date(2024, 12, 1)}")

# 어느 자리에서 승부가 났나
for i, (ca, cb) in enumerate(zip(a, b)):
    if ca != cb:
        print(f"결정 지점: {i}번째 글자 {ca!r}(코드 {ord(ca)}) vs {cb!r}(코드 {ord(cb)}) → {ca!r} 승")
        break

# 출력: 문자열 비교:  '2024-3-11' > '2024-12-01'  →  True
# 출력: 실제 날짜:    date(2024,3,11) > date(2024,12,1)  →  False
# 출력: 결정 지점: 5번째 글자 '3'(코드 51) vs '1'(코드 49) → '3' 승

# %% [markdown]
# ## 2단계 — 「조용히」가 핵심: 예외 없이 정렬이 뒤집힌다
#
# 타입 오류라면 그 자리에서 터져서 바로 고쳤을 것이다. 문자열 날짜는
# `sorted()`가 **정상적으로 완료**되고, 결과만 반대다. 로그에도, 모니터링에도
# 아무것도 남지 않는다 — 그래서 발견이 늦다.

# %%
dates_str = ["2024-12-01", "2024-3-11", "2024/05/20", "2024-08-15", "2025-01-05"]


def parse(s):
    """실무에서 흔히 쓰는 관대한 파서. 이 관대함이 사고를 만든다."""
    s = s.replace("/", "-").split("T")[0]
    parts = [int(x) for x in s.split("-")]
    while len(parts) < 3:
        parts.append(1)
    return date(*parts)


by_string = sorted(dates_str)                    # 예외 없음. 그냥 성공한다.
by_date = sorted(dates_str, key=parse)           # 시간순 정답

print("문자열 정렬:", by_string)
print("시간순 정렬:", by_date)
print("일치 여부  :", by_string == by_date)

# 출력: 문자열 정렬: ['2024-08-15', '2024-12-01', '2024-3-11', '2024/05/20', '2025-01-05']
# 출력: 시간순 정렬: ['2024-3-11', '2024/05/20', '2024-08-15', '2024-12-01', '2025-01-05']
# 출력: 일치 여부  : False
#
# 3월(2024-3-11)이 12월 뒤로, 5월(2024/05/20)이 그보다 더 뒤로 밀렸다.
# 비표준 표기 2건이 끼어들자 정렬 전체가 뒤집혔는데, 예외는 한 번도 나지 않았다.

# %% [markdown]
# ## 3단계 — 실무 사고 재현: 유효 기간 자르기가 무너진다
#
# 책의 사례: 외부 시스템에서 들어온 날짜 일부가 `2024-3-11` 형식이었고,
# 그 레코드들(전체의 4%)만 계약 만료 계산이 틀렸다. 월별 집계는 멀쩡해서
# 오차 범위처럼 보였고, 고객이 「우리 계약 왜 만료됐냐」고 전화한 뒤에야 발견됐다.

# %%
# 외부 피드에서 들어온 기준일(비표준 표기)과 만료일을 비교한다
record_date = "2026-9-15"     # 실제로는 9월 15일
expires_at = "2026-10-31"    # 만료일은 10월 31일 — 아직 유효해야 한다

expired_by_string = record_date > expires_at
expired_by_date = parse(record_date) > parse(expires_at)

print(f"문자열 비교: {record_date!r} > {expires_at!r} → {expired_by_string}  → 만료 처리(오답)")
print(f"날짜 비교  : {parse(record_date)} > {parse(expires_at)} → {expired_by_date}  → 유효(정답)")

# 출력: 문자열 비교: '2026-9-15' > '2026-10-31' → True  → 만료 처리(오답)
# 출력: 날짜 비교  : 2026-09-15 > 2026-10-31 → False  → 유효(정답)
#
# '9' > '1' 하나 때문에 살아 있는 계약이 만료로 처리된다. 역시 예외는 없다.

# %% [markdown]
# ## 4단계 — 언제 배신하나: 6가지 표기 케이스 (책 예제 3)
#
# 자릿수가 완전히 같은 첫 케이스만 우연히 맞고, 나머지 다섯은 전부 틀린다.

# %%
CASES = [
    ("자릿수가 맞을 때", "2024-03-11", "2025-06-02"),
    ("월에 0이 빠졌을 때", "2024-3-11", "2024-12-01"),
    ("연-월만 있을 때", "2024-08", "2024-8"),
    ("슬래시 표기가 섞였을 때", "2024/03/11", "2024-06-02"),
    ("연도만 있을 때", "2024", "2024-01-01"),
    ("시각이 붙었을 때", "2024-03-11", "2024-03-11T09:00"),
]


def cmp3(x, y):
    return "A<B" if x < y else ("A=B" if x == y else "A>B")


mismatch = 0
print(f"{'상황':<16} {'A':<12} {'B':<18} {'문자열':>6} {'날짜':>5} 같나")
for label, sa, sb in CASES:
    s_cmp, d_cmp = cmp3(sa, sb), cmp3(parse(sa), parse(sb))
    same = s_cmp == d_cmp
    mismatch += not same
    print(f"{label:<16} {sa:<12} {sb:<18} {s_cmp:>6} {d_cmp:>5} {'예' if same else '아니오 ←'}")
print(f"\n6건 중 {mismatch}건에서 문자열 비교가 틀린 답을 낸다.")

# 출력: 상황               A            B                     문자열    날짜 같나
# 출력: 자릿수가 맞을 때        2024-03-11   2025-06-02            A<B   A<B 예
# 출력: 월에 0이 빠졌을 때      2024-3-11    2024-12-01            A>B   A<B 아니오 ←
# 출력: 연-월만 있을 때        2024-08      2024-8                A<B   A=B 아니오 ←
# 출력: 슬래시 표기가 섞였을 때   2024/03/11   2024-06-02            A>B   A<B 아니오 ←
# 출력: 연도만 있을 때         2024         2024-01-01            A<B   A=B 아니오 ←
# 출력: 시각이 붙었을 때        2024-03-11   2024-03-11T09:00      A<B   A=B 아니오 ←
# 출력:
# 출력: 6건 중 5건에서 문자열 비교가 틀린 답을 낸다.

# %% [markdown]
# ## 5단계 — 시각화: 정렬이 「조용히 뒤집히는」 모습
#
# 2단계의 다섯 레코드를 범프 차트로 그린다. 왼쪽이 문자열 정렬 순위,
# 오른쪽이 실제 시간순 순위다. 비표준 표기 2건(빨강)이 잘못된 자리에
# 끼어들면서 표준 표기 레코드들까지 줄줄이 밀려난다 — 선이 교차하는
# 만큼이 「조용한 오답」이다.

# %%
import os

import plotly.graph_objects as go

# 색: dataviz 참조 팔레트 (light) — 상태색 critical은 비표준 표기 전용
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#898781", "#e1e0d9", "#fcfcfb"
CRITICAL, NEUTRAL = "#d03b3b", "#898781"

n = len(dates_str)
rank_str = {v: i + 1 for i, v in enumerate(by_string)}   # 1 = 가장 이르다고 판단
rank_real = {v: i + 1 for i, v in enumerate(by_date)}
bad = {"2024-3-11", "2024/05/20"}                        # 비표준 표기

fig = go.Figure()
for v in dates_str:
    is_bad = v in bad
    color = CRITICAL if is_bad else NEUTRAL
    fig.add_trace(go.Scatter(
        x=["문자열 정렬", "실제 시간순"], y=[rank_str[v], rank_real[v]],
        mode="lines+markers",
        line=dict(color=color, width=2.5 if is_bad else 2),
        marker=dict(size=9, color=color),
        hovertemplate=f"{v}<br>문자열 순위 %{{y}}<extra></extra>",
        showlegend=False,
    ))
    fig.add_annotation(x=-0.06, y=rank_str[v], xref="x", yref="y",
                       text=f"<b>{v}</b>" if is_bad else v,
                       font=dict(color=CRITICAL if is_bad else INK, size=13),
                       showarrow=False, xanchor="right")
    fig.add_annotation(x=1.06, y=rank_real[v], xref="x", yref="y",
                       text=f"{rank_real[v]}위", font=dict(color=MUTED, size=12),
                       showarrow=False, xanchor="left")

fig.update_layout(
    title=dict(text="문자열 정렬은 예외 없이, 조용히 순서를 뒤집는다<br>"
                    "<sup>빨강 = 비표준 표기(월 0 누락, 슬래시). 선의 교차 = 조용한 오답</sup>",
               font=dict(color=INK, size=17)),
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
    font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", color=INK),
    xaxis=dict(tickfont=dict(size=14, color=INK), showgrid=False, zeroline=False),
    yaxis=dict(autorange="reversed", tickmode="array",
               tickvals=list(range(1, n + 1)),
               ticktext=[f"{i}위" for i in range(1, n + 1)],
               tickfont=dict(color=MUTED), gridcolor=GRID, zeroline=False,
               title=dict(text="이른 날짜 순위 (1위 = 가장 이르다)",
                          font=dict(color=MUTED, size=12))),
    margin=dict(l=140, r=70, t=90, b=40), width=760, height=420,
)
_show(fig)

_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."
fig.write_image(os.path.join(_here, "expy.png"), scale=2)
print("expy.png 저장 완료")

# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# - **틀리는 방식**: 타입 에러도, 파싱 예외도 없다. `sorted()`와 `>`가 정상 완료되고
#   결과만 반대다. 월별 집계는 멀쩡해 보여서(사례에서는 오류가 4%뿐) 발견이 늦다.
# - **예방법 두 가지** (16장 16.3절):
#   1. **적재 시점에 날짜 타입으로 파싱한다.** 문자열로 두지 않는다.
#   2. **파싱 실패는 차단 등급 위반으로 올린다** (13장). 조용히 원본 문자열로
#      남겨 두면 1번이 무력해진다.
