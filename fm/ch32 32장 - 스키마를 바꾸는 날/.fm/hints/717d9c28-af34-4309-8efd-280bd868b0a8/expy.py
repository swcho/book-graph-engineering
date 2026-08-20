# %% [markdown]
# # 수축 기준은 「최근 30일」이 아니라 「가장 긴 배치 주기」다
#
# 32장 3절의 핵심입니다. 옛 스키마를 지워도 되는 시점을 판단할 때
# 흔히 쓰는 기준은 「최근 30일 동안 읽기가 0건인가」입니다.
# 그런데 이 기준은 **드물게 도는 잡**을 놓칩니다.
#
# - 분기 배치: 최대 간격 $92$일
# - 연말 정산: 최대 간격 $365$일
#
# 안전 조건은 시간 상수가 아니라 시스템에서 관측된 최대 주기입니다.
#
# $$\text{safe} \iff \min_{r \in R}\big(\text{today} - \text{lastUse}(r)\big) > T_{\max} + \text{margin}$$
#
# $$T_{\max} = \max_{c \in \text{crontab}} \; \max_i \big(t_{i+1}(c) - t_i(c)\big)$$
#
# 여기서 $T_{\max}$는 크론 표현식을 파싱해서 계산합니다.
# 이 노트북은 croniter 같은 외부 라이브러리 없이 표준 라이브러리만으로
# 다음 실행 시각들을 시뮬레이션해 $T_{\max}$를 뽑습니다.

# %%
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용. 앞의 셀들은 표준 라이브러리만 사용)
from datetime import date, timedelta


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


print("표준 라이브러리만으로 크론을 파싱한다. croniter 없음.")
# 출력: 표준 라이브러리만으로 크론을 파싱한다. croniter 없음.

# %% [markdown]
# ## 1단계 — 크론 필드 파서
#
# 크론 표현식은 `분 시 일 월 요일` 다섯 필드입니다.
# 우리가 알고 싶은 것은 **일 단위 최대 간격**이므로 `일 월 요일` 세 필드만 씁니다.
#
# 각 필드가 지원하는 문법: `*`, `5`, `1,4,7,10`, `1-5`, `*/3`, `1-11/2`

# %%
def parse_field(spec: str, lo: int, hi: int) -> set[int]:
    """크론 한 필드를 허용 값 집합으로 펼친다."""
    vals: set[int] = set()
    for part in spec.split(","):
        step = 1
        if "/" in part:
            part, s = part.split("/")
            step = int(s)
        if part == "*":
            a, b = lo, hi
        elif "-" in part:
            a, b = (int(x) for x in part.split("-"))
        else:
            a = b = int(part)
            if step != 1:          # "5/3" 은 5 부터 상한까지
                b = hi
        vals.update(range(a, b + 1, step))
    return vals


print(parse_field("*", 1, 12))
# 출력: {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}
print(parse_field("1,4,7,10", 1, 12))
# 출력: {1, 4, 7, 10}
print(sorted(parse_field("*/3", 1, 12)))
# 출력: [1, 4, 7, 10]
print(sorted(parse_field("1-5", 0, 6)))
# 출력: [1, 2, 3, 4, 5]

# %% [markdown]
# ## 2단계 — 그 날 도는가
#
# 주의할 점이 하나 있습니다. 표준 cron(Vixie cron)은 `일`과 `요일`이 **둘 다**
# 제한되어 있으면 **OR**로 판정합니다. 하나가 `*`면 나머지만 봅니다.
# 이 규칙을 틀리면 최대 간격이 실제보다 길게 나와서 수축 기준이 과하게 보수적이 됩니다.

# %%
def fires_on(expr: str, d: date) -> bool:
    """크론 표현식이 날짜 d 에 한 번이라도 도는가 (시/분은 무시)."""
    parts = expr.split()
    if len(parts) != 5:
        raise ValueError(f"필드 5개가 아니다: {expr!r}")
    _minute, _hour, dom_s, mon_s, dow_s = parts

    if d.month not in parse_field(mon_s, 1, 12):
        return False

    dom_ok = d.day in parse_field(dom_s, 1, 31)
    # cron 요일: 일=0 … 토=6 (7도 일요일). python weekday(): 월=0 … 일=6
    dows = {x % 7 for x in parse_field(dow_s.replace("7", "0"), 0, 6)}
    dow_ok = ((d.weekday() + 1) % 7) in dows

    dom_star, dow_star = dom_s.strip() == "*", dow_s.strip() == "*"
    if dom_star and dow_star:
        return True
    if dom_star:
        return dow_ok
    if dow_star:
        return dom_ok
    return dom_ok or dow_ok          # 둘 다 제한 → OR


print(fires_on("0 3 * * *", date(2026, 8, 19)))      # 매일
# 출력: True
print(fires_on("0 3 1 1,4,7,10 *", date(2026, 8, 19)))   # 분기 1일
# 출력: False
print(fires_on("0 3 1 1,4,7,10 *", date(2026, 10, 1)))
# 출력: True

# %% [markdown]
# ## 3단계 — 최대 간격 계산
#
# 다음 실행 날짜들을 충분히 긴 구간(윤년을 포함하도록 9년)에서 시뮬레이션하고
# 인접 실행 사이의 차이 중 최댓값을 취합니다.
#
# $$T_{\max}(c) = \max_i \big(t_{i+1} - t_i\big), \quad t_i \in \text{fireDays}(c)$$

# %%
def max_gap_days(expr: str, start=date(2020, 1, 1), years: int = 9) -> int:
    """크론의 실행 간격 최댓값(일). 윤년/월말을 포함하도록 여러 해를 훑는다."""
    end = date(start.year + years, start.month, start.day)
    fires, d = [], start
    one = timedelta(days=1)
    while d < end:
        if fires_on(expr, d):
            fires.append(d)
        d += one
    if len(fires) < 2:
        raise ValueError(f"실행이 2회 미만이다: {expr!r}")
    return max((b - a).days for a, b in zip(fires, fires[1:]))


CRONS = [
    ("정산 배치",   "0 3 * * *",         "매일 03시"),
    ("조직도 렌더", "*/10 * * * *",      "10분마다"),
    ("주간 리포트", "0 4 * * 1",         "매주 월요일"),
    ("월말 마감",   "0 5 1 * *",         "매월 1일"),
    ("분기 결산",   "0 6 1 1,4,7,10 *",  "1·4·7·10월 1일"),
    ("반기 감사",   "0 6 1 1,7 *",       "1·7월 1일"),
    ("연말 정산",   "0 7 31 12 *",       "매년 12월 31일"),
]

print(f"{'잡':<12}{'크론':<22}{'설명':<18}{'최대 간격(일)':>14}")
print("-" * 68)
gaps = {}
for name, expr, desc in CRONS:
    g = max_gap_days(expr)
    gaps[name] = g
    print(f"{name:<12}{expr:<22}{desc:<18}{g:>14}")

T_MAX = max(gaps.values())
print(f"\nT_max = {T_MAX}일  (가장 드물게 도는 잡: "
      f"{max(gaps, key=lambda k: gaps[k])})")
# 출력:
# 잡           크론                    설명                      최대 간격(일)
# --------------------------------------------------------------------
# 정산 배치       0 3 * * *             매일 03시                         1
# 조직도 렌더      */10 * * * *          10분마다                          1
# 주간 리포트      0 4 * * 1             매주 월요일                         7
# 월말 마감       0 5 1 * *             매월 1일                         31
# 분기 결산       0 6 1 1,4,7,10 *      1·4·7·10월 1일                  92
# 반기 감사       0 6 1 1,7 *           1·7월 1일                      184
# 연말 정산       0 7 31 12 *           매년 12월 31일                   366
#
# T_max = 366일  (가장 드물게 도는 잡: 연말 정산)

# %% [markdown]
# 책의 숫자가 그대로 나옵니다.
#
# - 분기 배치 `0 6 1 1,4,7,10 *` → **92일**
#   (10월 1일 → 1월 1일이 $31+30+31=92$일로 가장 길다. 1월→4월은 90~91일뿐이다)
# - 연말 정산 `0 7 31 12 *` → **365일**, 단 윤년을 끼면 **366일**
#
# 시뮬레이션이 366을 주는 건 버그가 아닙니다. 2023-12-31 → 2024-12-31 이
# 366일이라서 그렇습니다. 수축 기준은 **최악의 간격**을 써야 하니
# 365가 아니라 366이 맞습니다. 「$365$일 조용했으니 지워도 되겠지」로 지우면
# 윤년에는 하루 차이로 터집니다.
#
# 「최근 30일」기준은 이 표에서 매일/10분/주간만 통과시킵니다.
# 월말 마감(31일)조차 30일 창을 넘습니다.

# %% [markdown]
# ## 4단계 — 두 기준을 나란히 놓는다
#
# 예제 3(`ex3_when_to_contract.py`)의 상황을 그대로 씁니다.
# 오늘은 140일째이고, 옛 이름(`이끔`)을 마지막으로 읽은 기록은 이렇습니다.

# %%
TODAY = 140
LAST_USE = {           # 옛 이름을 마지막으로 읽은 날 (경과일은 TODAY - 값)
    "정산 배치":   90,   # 이미 새 이름으로 옮겨 감
    "조직도 렌더": 14,
    "월말 마감":   82,
    "분기 결산":   88,   # ← 92일마다 도는 잡. 52일 전에 돌았다
}
MARGIN = 30            # 여유. 한 주기를 다 기다린 뒤 추가로 두는 관측 창

print(f"{'주체':<12}{'마지막 사용':>10}{'경과일':>8}{'주기(일)':>10}{'한 주기 지났나':>16}")
print("-" * 60)
for who, day in sorted(LAST_USE.items(), key=lambda kv: -kv[1]):
    elapsed = TODAY - day
    cyc = gaps[who]
    print(f"{who:<12}{day:>10}{elapsed:>8}{cyc:>10}"
          f"{('예' if elapsed > cyc else '아니오'):>16}")

min_quiet = min(TODAY - d for d in LAST_USE.values())
quiet30 = min_quiet >= 30
safe_tmax = min_quiet > T_MAX
safe_margin = min_quiet > T_MAX + MARGIN

print(f"\n제일 최근 읽기: {min_quiet}일 전")
print(f"{'기준':<34}{'임계(일)':>10}{'판정':>12}")
print("-" * 56)
print(f"{'최근 30일 조용':<34}{30:>10}{('지워도 됨' if quiet30 else '아직'):>12}")
print(f"{'가장 긴 주기(T_max)':<34}{T_MAX:>10}"
      f"{('지워도 됨' if safe_tmax else '아직'):>12}")
print(f"{'T_max + 여유':<34}{T_MAX + MARGIN:>10}"
      f"{('지워도 됨' if safe_margin else '아직'):>12}")
# 출력:
# 주체              마지막 사용     경과일     주기(일)        한 주기 지났나
# ------------------------------------------------------------
# 정산 배치               90      50         1               예
# 분기 결산               88      52        92             아니오
# 월말 마감               82      58        31               예
# 조직도 렌더              14     126         1               예
#
# 제일 최근 읽기: 50일 전
# 기준                                     임계(일)          판정
# --------------------------------------------------------
# 최근 30일 조용                                 30       지워도 됨
# 가장 긴 주기(T_max)                           366          아직
# T_max + 여유                               396          아직

# %% [markdown]
# 「최근 30일」기준은 **지워도 됨**이라고 답합니다. 그리고 그 답은 틀렸습니다.
#
# 분기 결산은 52일 전에 돌았고 주기가 92일입니다.
# 아직 **한 주기가 지나지 않았습니다.** 40일 뒤에 깨어나서 없어진 이름을 찾습니다.

# %% [markdown]
# ## 5단계 — 52일 조용한 필드를 지우면 언제 깨지나
#
# 타임라인으로 봅니다. 위/아래 두 패널입니다.
#
# 1. 잡별 최대 간격 (막대) — 30일 선과 비교
# 2. **옛 이름을 읽는 시점** 타임라인 — 140일째에 지웠을 때 180일째에 터지는 지점
#
# 두 번째 패널의 점은 「그 잡이 옛 이름을 읽은/읽을 시점」입니다.
# 자주 도는 잡은 이미 새 이름으로 옮겨 가서 어느 날짜부터 점이 끊기고,
# 분기 결산만 아직 옛 이름을 읽는 상태입니다.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

DELETE_30 = TODAY                              # 「최근 30일」기준으로 지운 날
QUARTER = "분기 결산"
PERIOD_Q = gaps[QUARTER]                       # 92
CONTRACT_OK = LAST_USE[QUARTER] + PERIOD_Q + MARGIN   # 안전한 수축 시점


def schedule(last_day: int, period: int, horizon: int) -> list[int]:
    """마지막 실행일에서 주기를 앞뒤로 되짚어 실행 시점 목록을 만든다."""
    days, d = [], last_day
    while d >= -period:                        # 과거로 (화면 밖 한 칸까지)
        days.append(d)
        d -= period
    d = last_day + period
    while d <= horizon:                        # 미래로
        days.append(d)
        d += period
    return sorted(days)


fig = make_subplots(
    rows=2, cols=1, row_heights=[0.42, 0.58], vertical_spacing=0.19,
    subplot_titles=("① 크론별 최대 실행 간격(일) — 「최근 30일」 창과 비교",
                    "② 옛 이름을 읽는 시점 — 140일째 수축이 180일째에 터진다"),
)

# --- ① 최대 간격 막대 ---
names = [n for n, _e, _d in CRONS]
vals = [gaps[n] for n in names]
fig.add_trace(go.Bar(
    x=names, y=vals,
    marker_color=["#94a3b8" if v <= 30 else "#dc2626" for v in vals],
    text=[f"{v}일" for v in vals], textposition="outside", cliponaxis=False,
    hovertemplate="%{x}: 최대 간격 %{y}일<extra></extra>",
), row=1, col=1)
fig.add_hline(y=30, line=dict(color="#2563eb", dash="dash", width=2),
              row=1, col=1)
fig.add_annotation(x=2.6, y=120, xref="x", yref="y", xanchor="left",
                   text="◀ 「최근 30일」 기준선<br>월말 마감(31일)조차 넘어선다",
                   showarrow=False, align="left",
                   font=dict(size=12, color="#2563eb"))

# --- ② 옛 이름 읽기 타임라인 ---
# 자주 도는 잡: 옛 이름 읽기가 어느 날 끊겼다(이행 완료) → 선분으로
MIGRATED = [("조직도 렌더", 14, "#94a3b8"), ("정산 배치", 90, "#0ea5e9")]
LANES = ["조직도 렌더 (10분마다)", "정산 배치 (매일)", "분기 결산 (92일 주기)"]

for i, (who, stop, color) in enumerate(MIGRATED):
    y = i + 1
    fig.add_trace(go.Scatter(
        x=[0, stop], y=[y, y], mode="lines",
        line=dict(color=color, width=9),
        hovertemplate=f"{who} · 0~{stop}일: 옛 이름 읽음<extra></extra>",
        showlegend=False,
    ), row=2, col=1)
    fig.add_annotation(x=stop + 4, y=y, xref="x2", yref="y2",
                       text=f"{stop}일 이후 옛 이름 안 읽음 (이행 완료)",
                       showarrow=False, xanchor="left", font=dict(size=11,
                                                                 color=color))

q_days = schedule(LAST_USE[QUARTER], PERIOD_Q, horizon=300)
ok = [d for d in q_days if d <= DELETE_30]
ng = [d for d in q_days if d > DELETE_30]
fig.add_trace(go.Scatter(
    x=ok, y=[3] * len(ok), mode="markers",
    marker=dict(color="#dc2626", size=14, symbol="circle"),
    hovertemplate="분기 결산 · %{x}일째 · 옛 이름 읽음(정상)<extra></extra>",
    showlegend=False,
), row=2, col=1)
fig.add_trace(go.Scatter(
    x=ng, y=[3] * len(ng), mode="markers",
    marker=dict(color="#dc2626", size=20, symbol="x-thin",
                line=dict(width=4, color="#dc2626")),
    hovertemplate="분기 결산 · %{x}일째 · 옛 이름 없음 → 실패<extra></extra>",
    showlegend=False,
), row=2, col=1)

# 조용 구간 음영: 분기 결산 마지막 실행 → 오늘
fig.add_vrect(x0=LAST_USE[QUARTER], x1=TODAY, row=2, col=1,
              fillcolor="#fde68a", opacity=0.45, line_width=0)
fig.add_annotation(x=(LAST_USE[QUARTER] + TODAY) / 2, y=3.62,
                   xref="x2", yref="y2",
                   text="52일 조용 (한 주기 92일에 못 미친다)",
                   showarrow=False, font=dict(size=12, color="#a16207"))

first_break = min(ng)
for x, color, dash, width, text, ypos, xanch in (
    (DELETE_30, "#2563eb", "dash", 2,
     f"{DELETE_30}일 · 「30일 조용」 → 삭제", 0.95, "right"),
    (first_break, "#dc2626", "solid", 3,
     f"{first_break}일 · 분기 결산 실패", 0.60, "right"),
    (CONTRACT_OK, "#16a34a", "dot", 2,
     f"{CONTRACT_OK}일 · T_max+여유 기준 수축 가능", 0.95, "left"),
):
    fig.add_vline(x=x, row=2, col=1,
                  line=dict(color=color, dash=dash, width=width))
    fig.add_annotation(x=x, y=ypos, xref="x2", yref="y2", text=text,
                       showarrow=False, yanchor="middle", xanchor=xanch,
                       font=dict(size=12, color=color),
                       bgcolor="rgba(255,255,255,0.88)")

# 140 → 180 사이의 "조용한 40일"
fig.add_annotation(x=(DELETE_30 + first_break) / 2, y=2.35,
                   xref="x2", yref="y2",
                   text=f"삭제하고 {first_break - DELETE_30}일 동안<br>"
                        "아무 일도 안 일어난다<br>→ 안전해 보인다",
                   showarrow=False, font=dict(size=11, color="#dc2626"))

fig.update_yaxes(title_text="최대 간격(일)", row=1, col=1,
                 range=[0, max(vals) * 1.3])
fig.update_yaxes(row=2, col=1, tickmode="array", tickvals=[1, 2, 3],
                 ticktext=LANES, range=[0.1, 4.0], showgrid=False)
fig.update_xaxes(title_text="일자(day)", row=2, col=1, range=[-12, 300],
                 dtick=50)
fig.update_layout(
    height=800, width=1180, template="plotly_white", showlegend=False,
    title="수축 기준: 「최근 30일」 vs 「가장 긴 배치 주기」",
    margin=dict(l=150, r=40, t=100, b=70),
)

_show(fig)

print(f"140일째 수축 → 첫 실패는 {first_break}일째 (분기 결산)")
print(f"수축과 실패 사이의 침묵: {first_break - DELETE_30}일")
print(f"안전한 수축 시점: {CONTRACT_OK}일째 (마지막 사용 88 + 주기 92 + 여유 {MARGIN})")
# 출력: 140일째 수축 → 첫 실패는 180일째 (분기 결산)
# 출력: 수축과 실패 사이의 침묵: 40일
# 출력: 안전한 수축 시점: 210일째 (마지막 사용 88 + 주기 92 + 여유 30)

# %%
fig.write_image("expy.png", scale=2)
print("expy.png 저장")
# 출력: expy.png 저장

# %% [markdown]
# ## 6단계 — 수축 게이트를 코드로
#
# 예제 5(`ex5_migration_plan.py`)의 `contract` 게이트가 하는 일을 그대로 옮기면
# 이렇게 됩니다. 크론 목록에서 $T_{\max}$를 뽑고, 관측된 최소 침묵 기간과 비교합니다.

# %%
def contract_gate(crontab: dict[str, str], last_use_elapsed: dict[str, int],
                  margin: int = 30) -> tuple[bool, str]:
    """옛 스키마를 지워도 되는가. (통과여부, 이유)"""
    t_max = max(max_gap_days(e) for e in crontab.values())
    threshold = t_max + margin
    worst_who = min(last_use_elapsed, key=lambda k: last_use_elapsed[k])
    worst = last_use_elapsed[worst_who]
    if worst > threshold:
        return True, f"최소 침묵 {worst}일 > T_max({t_max}) + 여유({margin})"
    return False, (f"{worst_who}가 {worst}일 전에 읽었다. "
                   f"{threshold - worst}일 더 기다려야 한다 "
                   f"(T_max={t_max}, 임계={threshold})")


CRONTAB = {n: e for n, e, _d in CRONS}
ELAPSED = {w: TODAY - d for w, d in LAST_USE.items()}

for day in (140, 210, 400, 500):
    el = {w: day - d for w, d in LAST_USE.items()}
    ok, why = contract_gate(CRONTAB, el)
    print(f"{day:>4}일째 → {'통과' if ok else '막힘':<4} {why}")
# 출력:
#  140일째 → 막힘   정산 배치가 50일 전에 읽었다. 346일 더 기다려야 한다 (T_max=366, 임계=396)
#  210일째 → 막힘   정산 배치가 120일 전에 읽었다. 276일 더 기다려야 한다 (T_max=366, 임계=396)
#  400일째 → 막힘   정산 배치가 310일 전에 읽었다. 86일 더 기다려야 한다 (T_max=366, 임계=396)
#  500일째 → 통과   최소 침묵 410일 > T_max(366) + 여유(30)

# %% [markdown]
# T_max가 366(연말 정산)이라서 500일째가 되어야 통과합니다.
# 크론에 연 1회 잡이 하나만 있어도 수축은 **1년 넘게** 기다려야 한다는 뜻입니다.
# 그게 불편해서 「최근 30일」로 줄이면, 그 잡이 깨어나는 날 조용히 터집니다.
#
# 실무에서 이 대기가 정말 못 견딜 때 쓰는 방법은 기준을 줄이는 게 아니라
# **범위를 줄이는** 것입니다. 문제되는 잡(연말 정산)만 골라 먼저 새 스키마로
# 옮기고, 그 잡을 크론 목록에서 제외한 뒤 $T_{\max}$를 다시 계산합니다.
# 그러면 T_max가 184(반기 감사)로 내려갑니다.
#
# ## 정리
#
# | 항목 | 내용 |
# |---|---|
# | 틀린 기준 | 「최근 30일 읽기 0건」 — 월말 마감(31일)조차 못 통과 |
# | 맞는 기준 | 가장 긴 배치 주기 $T_{\max}$ + 여유 |
# | 분기 배치 | `0 6 1 1,4,7,10 *` → 92일 (10월 1일 → 1월 1일) |
# | 연말 정산 | `0 7 31 12 *` → 365일 (윤년을 끼면 366일) |
# | 구하는 법 | 크론 표현식 파싱 → 실행 날짜 시뮬레이션 → 인접 간격 최댓값 |
# | 크론에 없는 것 | 사람이 손으로 도는 것은 못 잡는다 → 옛 이름 읽으면 경고 로그 + 알림 |
# | 지우는 법 | 바로 DROP 말고 `_deprecated_이끔` 으로 개명 후 한 주기 더 기다린다 |
# | 추가 규칙 | 드물게 도는 잡일수록 실패 알림을 세게 건다 |
