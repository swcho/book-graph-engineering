# %% [markdown]
# # 이행이 잘 되고 있다는 신호 — 옛 이름 읽기 건수의 감쇠 곡선
#
# 32장의 결론 한 줄은 이것이다.
#
# > 조직도 렌더의 곡선을 보시라. **1,200 → 1,180 → 30 → 0** 으로 떨어졌다.
# > 그게 «새 코드로 옮겨 간» 흔적이다. 이런 곡선이 보이면 이행이 잘 되고 있는 것이다.
#
# 즉 **이행의 진척은 "새 코드가 배포됐다"가 아니라 "옛 이름 읽기 건수가 어떻게 떨어지느냐"로 관측한다.**
# 배포는 의도이고, 읽기 건수는 사실이다.
#
# 이 노트북에서 볼 것:
#
# 1. 건강한 감쇠 곡선(조직도 렌더)과 그 모양의 의미
# 2. 같은 "0"으로 끝나지만 신뢰할 수 없는 세 가지 **위험 신호 곡선**
# 3. **침묵 ≠ 안전** — 관측 창(30일)이 배치 주기(92일)보다 짧으면 0은 증거가 아니다
#
# 수식으로 쓰면 건강한 곡선은 대략 지수 감쇠에 가깝다.
#
# $$ r(t) \approx r_0 \cdot e^{-\lambda t}, \qquad \lambda > 0 $$
#
# 그리고 수축(옛 스키마 삭제)의 안전 조건은 시간이 아니라 **주기** 기준이다.
#
# $$ \text{safe} \iff \bigl(t_{\text{now}} - t_{\text{last read}}\bigr) > T_{\max\ \text{cycle}} $$

# %%
# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
import os

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
FONT = "Apple SD Gothic Neo, Noto Sans KR, sans-serif"
print("준비 완료:", HERE)
# 출력: 준비 완료: /Users/swcho/.../fc6c5b6f-04da-4bdb-b578-e9aa0035f4d0

# %% [markdown]
# ## 1. 원문의 관측 기록
#
# 예제 3(`ex3_when_to_contract.py`)의 `READS` 를 그대로 옮긴다.
# `(일자, 읽은 주체, 건수)` — 최근 90일간 **옛 이름(이끔)** 을 읽은 기록이다.

# %%
READS = [
    (1, "정산 배치", 420),
    (1, "조직도 렌더", 1200),
    (7, "정산 배치", 410),
    (7, "조직도 렌더", 1180),
    (14, "정산 배치", 405),
    (14, "조직도 렌더", 30),
    (21, "정산 배치", 400),
    (21, "조직도 렌더", 0),
    (30, "정산 배치", 395),
    (45, "정산 배치", 390),
    (60, "정산 배치", 2),
    (75, "정산 배치", 0),
    (82, "월말 마감", 340),  # 월말에만 도는 배치
    (88, "분기 결산", 210),  # 분기에 한 번 도는 배치
    (90, "정산 배치", 0),
]
TODAY = 140
LONGEST_CYCLE = 92  # 제일 드물게 도는 잡 — 분기 결산


def by_reader(reads):
    d = {}
    for day, who, n in reads:
        d.setdefault(who, []).append((day, n))
    for v in d.values():
        v.sort()
    return d


HIST = by_reader(READS)
for who, h in HIST.items():
    print(f"{who:<10} {[n for _d, n in h]}")
# 출력: 정산 배치     [420, 410, 405, 400, 395, 390, 2, 0, 0]
# 출력: 조직도 렌더    [1200, 1180, 30, 0]
# 출력: 월말 마감     [340]
# 출력: 분기 결산     [210]

# %% [markdown]
# ## 2. 건강한 곡선을 숫자로 확인한다
#
# "잘 되고 있다"를 눈대중이 아니라 두 개의 수로 잡아 둔다.
#
# - **감쇠율** $1 - r_t/r_{t-1}$ : 구간마다 몇 %가 사라졌나
# - **0 도달 후 재상승 여부** : 0 이 마지막인가, 아니면 잠깐 쉰 것인가
#
# 조직도 렌더는 1,180 → 30 구간에서 97% 가 사라진다. 새 코드로의 전환이 그 사이에 일어났다.
# 반면 정산 배치는 420 → 390 으로 **7% 밖에 안 줄었다.** 이 곡선은 "이행 중"이 아니라 "손 안 댐"이다.

# %%
def decay_table(who):
    h = HIST[who]
    rows = []
    prev = None
    for day, n in h:
        rate = None if prev in (None, 0) else 1 - n / prev
        rows.append((day, n, rate))
        prev = n
    return rows


for who in ("조직도 렌더", "정산 배치"):
    print(f"\n[{who}]")
    print(f"{'일자':>4}{'건수':>8}{'감쇠율':>10}")
    for day, n, rate in decay_table(who):
        r = "-" if rate is None else f"{rate:6.1%}"
        print(f"{day:>4}{n:>8}{r:>10}")
# 출력:
# 출력: [조직도 렌더]
# 출력:   일자      건수       감쇠율
# 출력:    1    1200         -
# 출력:    7    1180      1.7%
# 출력:   14      30     97.5%
# 출력:   21       0    100.0%
# 출력:
# 출력: [정산 배치]
# 출력:   일자      건수       감쇠율
# 출력:    1     420         -
# 출력:    7     410      2.4%
# 출력:   14     405      1.2%
# 출력:   21     400      1.2%
# 출력:   30     395      1.2%
# 출력:   45     390      1.3%
# 출력:   60       2     99.5%
# 출력:   75       0    100.0%
# 출력:   90       0         -

# %% [markdown]
# ## 3. 같은 0, 다른 의미 — 네 가지 곡선 모양
#
# 마지막 값이 0 인 곡선은 네 가지가 있는데, 그중 **하나만** 이행이 잘 된 신호다.
#
# | 모양 | 생김새 | 실제로 벌어진 일 |
# |---|---|---|
# | 건강한 감쇠 | 1200 → 1180 → 30 → 0 | 새 코드가 트래픽을 흡수했다 |
# | 절벽 (정체 후 급락) | 1200 → 1200 → 1200 → 0 | 이행이 아니라 **호출자가 죽었다** |
# | 반등 (0 찍고 튀어오름) | 1200 → 30 → 0 → 340 | 드물게 도는 배치가 깨어났다 |
# | 잔여 상주 | 1200 → 60 → 14 → 12 | 정체를 모르는 읽기가 남아 있다 |
#
# 핵심은 **0 자체가 신호가 아니라는 것.** 0 으로 가는 *경로*가 신호다.

# %%
DAYS = [1, 7, 14, 21, 30, 45, 60, 75, 90]

CURVES = {
    "건강한 감쇠": {
        "y": [1200, 1180, 30, 0, 0, 0, 0, 0, 0],
        "verdict": "이행 성공",
        "why": "새 코드가 트래픽을 흡수. 감쇠가 점진 → 급감 → 0 순서",
        "color": "#2E7D32",
    },
    "절벽 (정체 후 급락)": {
        "y": [1200, 1205, 1198, 1202, 1200, 0, 0, 0, 0],
        "verdict": "위험",
        "why": "줄어드는 과정이 없다. 옮겨 간 게 아니라 호출자가 멈춘 것",
        "color": "#C62828",
    },
    "반등 (0 후 재상승)": {
        "y": [1200, 30, 0, 0, 0, 0, 0, 340, 210],
        "verdict": "위험",
        "why": "월말·분기 배치가 깨어났다. 0 은 침묵이었을 뿐",
        "color": "#EF6C00",
    },
    "잔여 상주": {
        "y": [1200, 300, 60, 24, 14, 12, 12, 12, 12],
        "verdict": "위험",
        "why": "정체를 모르는 읽기가 남는다. 12건의 주인을 못 찾으면 수축 불가",
        "color": "#6A1B9A",
    },
}

print(f"{'곡선':<20}{'마지막값':>8}{'최소값':>7}{'0이후재상승':>12}  판정")
print("-" * 78)
for name, c in CURVES.items():
    y = c["y"]
    zero_i = next((i for i, v in enumerate(y) if v == 0), None)
    rebound = zero_i is not None and any(v > 0 for v in y[zero_i:])
    print(f"{name:<20}{y[-1]:>8}{min(y):>7}{str(rebound):>12}  {c['verdict']}")
# 출력: 곡선                    마지막값     최소값     0이후재상승  판정
# 출력: ------------------------------------------------------------------------------
# 출력: 건강한 감쇠                    0      0       False  이행 성공
# 출력: 절벽 (정체 후 급락)              0      0       False  위험
# 출력: 반등 (0 후 재상승)             210      0        True  위험
# 출력: 잔여 상주                     12     12       False  위험

# %% [markdown]
# 주의: **절벽 곡선은 위 표의 산술 지표로는 건강한 곡선과 구별되지 않는다.**
# 둘 다 마지막이 0 이고 재상승도 없다. 구별하려면 *0 에 닿기 직전까지의 감쇠*를 봐야 한다.
# 건강한 곡선은 0 에 닿기 전에 이미 97.5% 가 줄어 있고, 절벽은 직전까지 0% 다.
#
# 그래서 판정은 세 가지 조건의 논리곱으로 쓴다.
#
# $$ \text{healthy} \iff \text{reaches } 0 \;\wedge\; \neg\text{rebound} \;\wedge\; \text{predrop decay} > 0.5 $$

# %%
def diagnose(y):
    """0 도달 / 재상승 / 0 직전까지의 감쇠 — 셋을 함께 본다."""
    zero_i = next((i for i, v in enumerate(y) if v == 0), None)
    reaches_zero = zero_i is not None
    rebound = reaches_zero and any(v > 0 for v in y[zero_i:])
    if reaches_zero and zero_i > 0:
        predrop = 1 - y[zero_i - 1] / y[0]
    else:
        predrop = None  # 0 에 아예 닿지 않으면 정의할 수 없다
    return reaches_zero, rebound, predrop


print(f"{'곡선':<20}{'0도달':>6}{'재상승':>7}{'0직전감쇠':>10}  판정")
print("-" * 72)
for name, c in CURVES.items():
    z, reb, pre = diagnose(c["y"])
    if not z:
        verdict = "잔여 상주 — 0 에 못 닿음"
    elif reb:
        verdict = "반등 — 침묵이었을 뿐"
    elif pre is not None and pre <= 0.5:
        verdict = "절벽 — 이행 아님"
    else:
        verdict = "건강한 감쇠"
    ps = "-" if pre is None else f"{pre:.1%}"
    print(f"{name:<20}{str(z):>6}{str(reb):>7}{ps:>10}  {verdict}")
# 출력: 곡선                    0도달    재상승    0직전감쇠  판정
# 출력: ------------------------------------------------------------------------
# 출력: 건강한 감쇠                True  False     97.5%  건강한 감쇠
# 출력: 절벽 (정체 후 급락)          True  False      0.0%  절벽 — 이행 아님
# 출력: 반등 (0 후 재상승)          True   True     97.5%  반등 — 침묵이었을 뿐
# 출력: 잔여 상주                False  False         -  잔여 상주 — 0 에 못 닿음

# %% [markdown]
# ## 4. 침묵은 안전이 아니다 — 관측 창 대비 배치 주기
#
# 예제 3의 세 가지 판정을 그대로 돌려 본다. 앞의 둘은 «지워도 됨»이라 하고 세 번째만 «아직»이라 한다.
# **그리고 세 번째가 맞다.**
#
# $$ \text{관측 창}(30) < T_{\max\ \text{cycle}}(92) \Rightarrow \text{0 은 증거가 아니다} $$

# %%
def last_use(h):
    used = [d for d, n in h if n > 0]
    return max(used) if used else None


print(f"{'읽는 주체':<12}{'마지막 사용':>10}{'경과일':>7}{'최근 30일':>10}")
print("-" * 42)
for who, h in sorted(HIST.items()):
    lu = last_use(h)
    recent = sum(n for d, n in h if d > TODAY - 30)
    print(f"{who:<12}{lu if lu else '없음':>10}{TODAY - lu if lu else 999:>7}{recent:>10}")

quiet30 = all(sum(n for d, n in h if d > TODAY - 30) == 0 for h in HIST.values())
all_quiet30 = all((TODAY - last_use(h)) >= 30 for h in HIST.values() if last_use(h))
safe_cycle = all((TODAY - last_use(h)) > LONGEST_CYCLE for h in HIST.values() if last_use(h))

print()
for label, v in (
    ("최근 30일 건수가 0인가", quiet30),
    ("모든 주체가 30일 이상 조용", all_quiet30),
    (f"가장 긴 주기({LONGEST_CYCLE}일)보다 오래", safe_cycle),
):
    print(f"{label:<30}{'지워도 됨' if v else '아직'}")
# 출력: 읽는 주체           마지막 사용    경과일     최근 30일
# 출력: ------------------------------------------
# 출력: 분기 결산                 88     52         0
# 출력: 월말 마감                 82     58         0
# 출력: 정산 배치                 60     80         0
# 출력: 조직도 렌더                14    126         0
# 출력:
# 출력: 최근 30일 건수가 0인가                지워도 됨
# 출력: 모든 주체가 30일 이상 조용             지워도 됨
# 출력: 가장 긴 주기(92일)보다 오래           아직

# %% [markdown]
# 분기 결산은 52일째 조용하다. 30일 창으로 보면 완전한 0 이다.
# 그런데 이건 **92일마다 도는 잡**이다. 40일 뒤에 깨어나서 없어진 이름을 찾는다.
# 연말 정산이면 365일이므로 «1년 조용»해도 지우면 안 된다.

# %% [markdown]
# ## 5. 시각화
#
# 왼쪽 위가 정답 곡선이고, 나머지 셋은 마지막 값만 보면 속기 쉬운 곡선들이다.
# 각 패널에 **30일 관측 창**(회색 음영)과 **92일 배치 주기**(점선)를 겹쳐 그려서,
# 관측 창 안의 0 이 왜 증거가 못 되는지 보이게 한다.

# %%
titles = list(CURVES)
fig = make_subplots(
    rows=2,
    cols=2,
    subplot_titles=[f"{t} — {CURVES[t]['verdict']}" for t in titles],
    vertical_spacing=0.16,
    horizontal_spacing=0.09,
)

for i, name in enumerate(titles):
    r, cc = i // 2 + 1, i % 2 + 1
    c = CURVES[name]
    fig.add_trace(
        go.Scatter(
            x=DAYS,
            y=c["y"],
            mode="lines+markers+text",
            line=dict(color=c["color"], width=3),
            marker=dict(size=8),
            text=[str(v) if v in (c["y"][0], max(c["y"]), c["y"][-1]) or v == 0 else "" for v in c["y"]],
            textposition="top center",
            textfont=dict(size=9, color=c["color"]),
            name=name,
            hovertemplate="%{x}일: %{y}건<extra></extra>",
            showlegend=False,
        ),
        row=r,
        col=cc,
    )
    # 30일 관측 창 — "최근 30일이 0" 이라고 말하는 구간
    fig.add_vrect(
        x0=60, x1=90, fillcolor="#9E9E9E", opacity=0.15, line_width=0,
        row=r, col=cc,
    )
    # 가장 긴 배치 주기(92일) 경계
    fig.add_vline(
        x=92, line=dict(color="#455A64", width=1.5, dash="dot"),
        row=r, col=cc,
    )
    fig.add_annotation(
        x=0.02,
        y=0.97,
        xref="x domain" if i == 0 else f"x{i + 1} domain",
        yref="y domain" if i == 0 else f"y{i + 1} domain",
        text=c["why"], showarrow=False, align="left",
        font=dict(size=9, color="#37474F"), xanchor="left", yanchor="top",
        row=r, col=cc,
    )

fig.add_annotation(
    x=75, y=1, xref="x", yref="y domain",
    text="30일 관측 창", showarrow=False,
    font=dict(size=9, color="#616161"), yanchor="bottom",
)
fig.add_annotation(
    x=92, y=0.55, xref="x", yref="y domain",
    text="92일<br>가장 긴<br>배치 주기", showarrow=False,
    font=dict(size=9, color="#455A64"), xanchor="left", xshift=4,
)

fig.update_xaxes(title_text="경과일", tickvals=DAYS, range=[-4, 108], gridcolor="#ECEFF1")
fig.update_yaxes(title_text="옛 이름 읽기 건수", range=[-90, 1400], gridcolor="#ECEFF1")
fig.update_layout(
    title=dict(
        text="옛 이름 읽기 건수 곡선 — 0 이 아니라 <b>0 으로 가는 경로</b>가 신호다"
        "<br><sup>점선 = 가장 긴 배치 주기 92일. 관측 창(회색)이 주기보다 짧으면 침묵은 안전이 아니다</sup>",
        x=0.5,
        xanchor="center",
    ),
    font=dict(family=FONT, size=11),
    plot_bgcolor="white",
    paper_bgcolor="white",
    height=760,
    width=1150,
    margin=dict(t=110, b=60, l=70, r=40),
)

_show(fig)
fig.write_image(os.path.join(HERE, "expy.png"), scale=2)
print("saved:", os.path.join(HERE, "expy.png"))
# 출력: saved: /Users/swcho/.../fc6c5b6f-04da-4bdb-b578-e9aa0035f4d0/expy.png

# %% [markdown]
# ## 6. 정리 — 관측을 게이트로 바꾼다
#
# 예제 5(`ex5_migration_plan.py`)는 이 관측값들을 **통과 조건**으로 코드에 박아 둔다.
# 곡선을 눈으로 보는 데서 끝내면 사람이 "대충 된 것 같은데"로 넘어가기 때문이다.

# %%
STATE = {
    "불일치_건수": 3,
    "옛것_읽기_건수_최근": 0,
    "가장_긴_주기_일": 92,
    "옛것_마지막_읽기_경과일": 52,
    "롤백_가능": True,
}

GATES = [
    ("dual-read", "불일치가 0인가", lambda s: s["불일치_건수"] == 0),
    ("cutover", "옛것 읽기가 0인가", lambda s: s["옛것_읽기_건수_최근"] == 0),
    ("cutover", "롤백이 가능한가", lambda s: s["롤백_가능"]),
    ("contract", "가장 긴 주기보다 오래 조용한가",
     lambda s: s["옛것_마지막_읽기_경과일"] > s["가장_긴_주기_일"]),
]

blocked = None
for phase, label, fn in GATES:
    ok = fn(STATE)
    print(f"{phase:<11}{label:<24}{'○' if ok else '✗'}")
    if not ok and blocked is None:
        blocked = (phase, label)
print(f"\n막힌 곳: {blocked[0]} — {blocked[1]}")
# 출력: dual-read  불일치가 0인가                 ✗
# 출력: cutover    옛것 읽기가 0인가               ○
# 출력: cutover    롤백이 가능한가                 ○
# 출력: contract   가장 긴 주기보다 오래 조용한가        ✗
# 출력:
# 출력: 막힌 곳: dual-read — 불일치가 0인가

# %% [markdown]
# 정리하면 **이행이 잘 되고 있다는 신호는 세 가지가 동시에 성립할 때다.**
#
# 1. 옛 이름 읽기 건수가 **점진적으로** 떨어져 0 에 닿는다 (1,200 → 1,180 → 30 → 0)
# 2. 0 에 닿은 뒤 **가장 긴 배치 주기보다 오래** 0 을 유지한다 (92일, 연말 정산이면 365일)
# 3. 그 사이 «둘 다 읽고 비교»의 **불일치 건수도 0** 이다
#
# 하나라도 빠지면 0 은 이행의 증거가 아니라 관측 실패의 증거다.
