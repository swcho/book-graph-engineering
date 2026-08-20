# %% [markdown]
# # 세 판정 방법은 어디서 갈리는가
#
# `ex3_when_to_contract.py`는 「옛 스키마를 지워도 되나」를 세 가지 규칙으로 판정한다.
# 같은 데이터, 다른 규칙. 그리고 결론이 2:1로 갈린다.
#
# | 방법 | 규칙 | 결론 |
# |---|---|---|
# | 1 | 최근 30일 건수가 0인가 | 지워도 됨 |
# | 2 | 모든 주체가 30일 이상 조용한가 | 지워도 됨 |
# | 3 | 가장 긴 주기(92일)보다 오래 조용한가 | **아직** |
#
# 이 노트북은 **판정 함수 세 개를 나란히 구현**해서
# 「왜 앞의 둘은 항상 같은 답을 내는가」와
# 「세 번째만 다른 답을 내는 구간이 어디인가」를 직접 확인한다.
#
# (크론 표현식 파싱은 다른 카드의 주제다. 여기서는 주기를 상수로 준다.)

# %%
# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1. 입력 — 옛 이름을 읽은 기록
#
# `(일자, 읽은 주체, 건수)`. 기록은 90일째까지만 있고 오늘은 140일째다.
# 즉 **최근 50일은 기록 자체가 없다.**

# %%
READS = [
    (1,  "정산 배치",   420), (1,  "조직도 렌더", 1200),
    (7,  "정산 배치",   410), (7,  "조직도 렌더", 1180),
    (14, "정산 배치",   405), (14, "조직도 렌더",   30),
    (21, "정산 배치",   400), (21, "조직도 렌더",    0),
    (30, "정산 배치",   395),
    (45, "정산 배치",   390),
    (60, "정산 배치",     2),
    (75, "정산 배치",     0),
    (82, "월말 마감",    340),      # 월말에만 도는 배치
    (88, "분기 결산",    210),      # 분기에 한 번 도는 배치
    (90, "정산 배치",     0),
]
TODAY = 140
LONGEST_CYCLE = 92                  # 제일 드문 것 — 분기 결산

# 주체별 실제 주기 (참고용 — 방법 4에서 쓴다)
CYCLE = {"정산 배치": 1, "조직도 렌더": 1, "월말 마감": 31, "분기 결산": 92}


def by_reader(reads=READS):
    d = {}
    for day, who, n in reads:
        d.setdefault(who, []).append((day, n))
    return d


def last_use(hist):
    """건수가 0보다 큰 마지막 날. 0건 기록은 «돌았지만 안 읽었다»이므로 사용이 아니다."""
    used = [day for day, n in hist if n > 0]
    return max(used) if used else None


D = by_reader()
for who in sorted(D):
    print(f"{who:<12} last_use={last_use(D[who]):>3}  경과={TODAY - last_use(D[who]):>4}일"
          f"  주기={CYCLE[who]:>3}일")
# 출력: 분기 결산      last_use= 88  경과=  52일  주기= 92일
# 출력: 월말 마감      last_use= 82  경과=  58일  주기= 31일
# 출력: 정산 배치      last_use= 60  경과=  80일  주기=  1일
# 출력: 조직도 렌더    last_use= 14  경과= 126일  주기=  1일

# %% [markdown]
# 여기서 **분기 결산의 경과 52일**이 이 카드의 전부다.
#
# $$30 \le 52 < 92$$
#
# 30보다 크니 방법 1·2는 통과시키고, 92보다 작으니 방법 3은 막는다.

# %% [markdown]
# ## 2. 판정 함수 세 개를 그대로 옮긴다
#
# 원본 예제의 세 판정을 함수로 떼어내면 비교가 쉬워진다.
# 각 함수는 `(결론, 이유)`를 돌려준다.
#
# $$
# \begin{aligned}
# \text{방법 1:}\quad &\sum_{d > T-30} n = 0 \\
# \text{방법 2:}\quad &\min_{r}\,(T - \text{last\_use}(r)) \ge 30 \\
# \text{방법 3:}\quad &\min_{r}\,(T - \text{last\_use}(r)) > C_{\max}=92
# \end{aligned}
# $$

# %%
def verdict_recent30(d, today=TODAY):
    """방법 1 — 최근 30일 건수가 0인가. (전체 «합계»를 본다)"""
    total = sum(n for h in d.values() for day, n in h if day > today - 30)
    return total == 0, f"창(day > {today - 30}) 안의 총 건수 = {total}"


def verdict_all_quiet30(d, today=TODAY):
    """방법 2 — 모든 주체가 30일 이상 조용한가. (주체 «각각»을 본다)"""
    gaps = {w: today - last_use(h) for w, h in d.items() if last_use(h)}
    worst = min(gaps, key=lambda w: gaps[w])
    return gaps[worst] >= 30, f"제일 최근이 {worst} {gaps[worst]}일 전 (기준 30일)"


def verdict_longest_cycle(d, today=TODAY, cmax=LONGEST_CYCLE):
    """방법 3 — 가장 긴 주기보다 오래 조용한가."""
    gaps = {w: today - last_use(h) for w, h in d.items() if last_use(h)}
    worst = min(gaps, key=lambda w: gaps[w])
    return gaps[worst] > cmax, f"{worst}이 {gaps[worst]}일 전 (기준 {cmax}일)"


METHODS = [
    ("최근 30일 건수가 0인가", verdict_recent30),
    ("모든 주체가 30일 이상 조용", verdict_all_quiet30),
    (f"가장 긴 주기({LONGEST_CYCLE}일)보다 오래", verdict_longest_cycle),
]

print(f"오늘 = {TODAY}일째\n")
print(f"{'판정 방법':<30}{'결론':<12}이유")
print("-" * 78)
for name, fn in METHODS:
    ok, why = fn(D)
    print(f"{name:<30}{'지워도 됨' if ok else '아직':<12}{why}")
# 출력: 오늘 = 140일째
# 출력:
# 출력: 판정 방법                     결론          이유
# 출력: ------------------------------------------------------------------------------
# 출력: 최근 30일 건수가 0인가              지워도 됨       창(day > 110) 안의 총 건수 = 0
# 출력: 모든 주체가 30일 이상 조용          지워도 됨       제일 최근이 분기 결산 52일 전 (기준 30일)
# 출력: 가장 긴 주기(92일)보다 오래         아직          분기 결산이 52일 전 (기준 92일)

# %% [markdown]
# ## 3. 방법 1과 2는 왜 «항상» 같은가
#
# 우연이 아니다. 두 규칙은 집계 단위만 다르고 **임계값 30일이 같다.**
#
# > 「30일 창 안의 총 건수가 0」 $\iff$ 「창 안에 사용한 주체가 없다」
# > $\iff$ 「모든 주체의 마지막 사용이 창 밖」
#
# 오늘을 1일부터 260일까지 훑어서 두 판정이 한 번이라도 갈리는지 확인한다.

# %%
disagree_12 = [t for t in range(1, 261)
               if verdict_recent30(D, t)[0] != verdict_all_quiet30(D, t)[0]]
print("방법 1과 2가 갈리는 날:", disagree_12 or "없음")

disagree_13 = [t for t in range(1, 261)
               if verdict_recent30(D, t)[0] != verdict_longest_cycle(D, t)[0]]
print(f"방법 1과 3이 갈리는 구간: {min(disagree_13)}일 ~ {max(disagree_13)}일"
      f" ({len(disagree_13)}일간)")
# 출력: 방법 1과 2가 갈리는 날: 없음
# 출력: 방법 1과 3이 갈리는 구간: 118일 ~ 180일 (63일간)

# %% [markdown]
# 방법 1과 2는 260일을 통틀어 **한 번도 갈리지 않는다.** 같은 규칙이다.
#
# 반면 방법 1·2와 방법 3은 **118일 ~ 180일, 63일 동안** 정반대를 말한다.
# 예제의 `TODAY = 140`은 일부러 이 구간 가운데에 박아 둔 값이다.
#
# 임계값을 직접 계산해 보면 이유가 분명해진다.
# 마지막으로 실제 사용된 날은 88일(분기 결산)이므로
#
# $$T_{\text{방법 1,2}} = 88 + 30 = 118, \qquad T_{\text{방법 3}} = 88 + 92 + 1 = 181$$
#
# 세 방법의 진짜 차이는 판정 로직이 아니라 **창의 길이**다.

# %%
def flip_day(fn, hi=400):
    """이 판정이 «지워도 됨»으로 처음 뒤집히는 날."""
    for t in range(1, hi):
        if fn(D, t)[0]:
            return t
    return None


for name, fn in METHODS:
    print(f"{name:<30}→ {flip_day(fn)}일째부터 «지워도 됨»")
# 출력: 최근 30일 건수가 0인가              → 118일째부터 «지워도 됨»
# 출력: 모든 주체가 30일 이상 조용          → 118일째부터 «지워도 됨»
# 출력: 가장 긴 주기(92일)보다 오래         → 181일째부터 «지워도 됨»

# %% [markdown]
# ## 4. 앞의 둘이 틀리는 대가 — 분기 결산은 언제 깨어나나
#
# 분기 결산은 88일째에 돌았고 주기가 92일이다. 다음 실행은 180일째.
# 방법 1·2를 믿고 118일째에 지우면, **62일 뒤에 없어진 이름을 찾는다.**
# 예제의 오늘(140일)을 기준으로 하면 40일 뒤다.

# %%
next_run = last_use(D["분기 결산"]) + CYCLE["분기 결산"]
print(f"분기 결산 마지막 실행 = {last_use(D['분기 결산'])}일")
print(f"분기 결산 다음 실행   = {next_run}일")
print(f"오늘({TODAY}일) 기준 {next_run - TODAY}일 뒤에 깨어난다")
print(f"방법 1·2로 지우면 = {flip_day(verdict_recent30)}일 → "
      f"다음 실행까지 {next_run - flip_day(verdict_recent30)}일 남은 시점에 지운다 (사고)")
print(f"방법 3으로 지우면 = {flip_day(verdict_longest_cycle)}일 → "
      f"다음 실행({next_run}일)을 지나서 지운다 (안전)")
# 출력: 분기 결산 마지막 실행 = 88일
# 출력: 분기 결산 다음 실행   = 180일
# 출력: 오늘(140일) 기준 40일 뒤에 깨어난다
# 출력: 방법 1·2로 지우면 = 118일 → 다음 실행까지 62일 남은 시점에 지운다 (사고)
# 출력: 방법 3으로 지우면 = 181일 → 다음 실행(180일)을 지나서 지운다 (안전)

# %% [markdown]
# ## 5. 30일 창은 네 주체를 구분하지 못한다
#
# 30일 창으로 보면 네 줄이 전부 「조용」이다. 그래서 방법 1·2가 틀린다.
# 주체별 주기를 알면 「자기 주기보다 오래 조용한가」로 더 정확히 물을 수 있다.
# 결론은 방법 3과 같지만 **걸리는 이유가 정확해진다.**

# %%
def verdict_per_reader_cycle(d, today=TODAY):
    """방법 4(개선) — 주체마다 «자기» 주기와 비교한다."""
    blockers = [w for w, h in d.items()
                if last_use(h) and (today - last_use(h)) <= CYCLE[w]]
    return not blockers, f"막는 주체: {blockers or '없음'}"


print(f"{'주체':<12}{'경과':>6}{'주기':>6}{'30일창':>8}{'92일창':>8}{'자기주기':>10}")
print("-" * 52)
for who in sorted(D, key=lambda w: TODAY - last_use(D[w])):
    gap = TODAY - last_use(D[who])
    print(f"{who:<12}{gap:>6}{CYCLE[who]:>6}"
          f"{'조용' if gap >= 30 else '사용중':>8}"
          f"{'조용' if gap > 92 else '사용중':>8}"
          f"{'조용' if gap > CYCLE[who] else '사용중':>10}")

ok, why = verdict_per_reader_cycle(D)
print(f"\n방법 4 결론: {'지워도 됨' if ok else '아직'} — {why}")
# 출력: 주체            경과    주기   30일창   92일창      자기주기
# 출력: ----------------------------------------------------
# 출력: 분기 결산        52    92      조용     사용중       사용중
# 출력: 월말 마감        58    31      조용     사용중         조용
# 출력: 정산 배치        80     1      조용     사용중         조용
# 출력: 조직도 렌더     126     1      조용      조용         조용
# 출력:
# 출력: 방법 4 결론: 아직 — 막는 주체: ['분기 결산']

# %% [markdown]
# `30일창` 열은 전부 「조용」이라 정보가 없다. 그래서 방법 1·2가 틀린다.
# `92일창`은 진짜 문제 주체(분기 결산)를 잡지만, 이미 이행이 끝난
# 월말 마감·정산 배치까지 함께 「사용중」으로 만든다. 보수적이지만 안전하다.
# `자기주기`는 **분기 결산 하나만** 집어낸다.
#
# 즉 방법 3은 「가장 긴 주기 하나를 모두에게 적용」하는 보수적 근사다.
# 결론은 방법 4와 같고, 이 데이터에서는 그 보수성이 손해를 주지 않는다.

# %% [markdown]
# ## 6. 0건 기록은 이행이 잘 되고 있다는 신호
#
# 건수가 0인 줄은 「잡이 돌았지만 옛 이름을 안 읽었다」다.
# 하강 곡선이 보이면 새 코드로 옮겨 간 것이다.
# 반대로 데이터 점이 하나뿐이면 「이행 완료」가 아니라 「아직 한 번밖에 안 돌았다」다.

# %%
for who in ("조직도 렌더", "정산 배치", "월말 마감", "분기 결산"):
    curve = " → ".join(str(n) for _d, n in sorted(D[who]))
    note = "이행됨 (0으로 수렴)" if sorted(D[who])[-1][1] == 0 else "점이 하나 — 판단 불가"
    print(f"{who:<12}{curve:<34}{note}")
# 출력: 조직도 렌더     1200 → 1180 → 30 → 0             이행됨 (0으로 수렴)
# 출력: 정산 배치       420 → 410 → 405 → 400 → 395 → 390 → 2 → 0 → 0이행됨 (0으로 수렴)
# 출력: 월말 마감       340                               점이 하나 — 판단 불가
# 출력: 분기 결산       210                               점이 하나 — 판단 불가

# %% [markdown]
# ## 7. 시각화
#
# - 위: 읽기 기록 타임라인. 오늘(140일)과 두 임계선(30일 창, 92일 창)을 겹쳐 본다.
# - 아래: 오늘을 1~260일로 움직이며 세 판정의 결론이 뒤집히는 시점.
#   118~180일 구간이 「결론이 갈리는 띠」다.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

READERS = sorted(D, key=lambda w: -CYCLE[w])
COLORS = {"분기 결산": "#d62728", "월말 마감": "#ff7f0e",
          "정산 배치": "#1f77b4", "조직도 렌더": "#2ca02c"}

fig = make_subplots(
    rows=2, cols=1, row_heights=[0.52, 0.48], vertical_spacing=0.14,
    subplot_titles=("읽기 기록 타임라인 (원 크기 = 건수, 빈 원 = 0건)",
                    "오늘을 움직이며 본 세 판정의 결론"),
)

# --- 위 패널: 타임라인
for who in READERS:
    days = [d for d, _n in sorted(D[who])]
    ns = [n for _d, n in sorted(D[who])]
    fig.add_trace(go.Scatter(
        x=days, y=[who] * len(days), mode="markers+text",
        marker=dict(size=[10 + 26 * (n / 1200) ** 0.5 if n else 9 for n in ns],
                    color=[COLORS[who] if n else "rgba(0,0,0,0)" for n in ns],
                    line=dict(color=COLORS[who], width=2)),
        text=[str(n) for n in ns], textposition="top center",
        textfont=dict(size=9), name=f"{who} (주기 {CYCLE[who]}일)",
        hovertemplate=f"{who}<br>%{{x}}일 · %{{text}}건<extra></extra>",
    ), row=1, col=1)

fig.add_vline(x=TODAY, line=dict(color="black", width=2),
              annotation_text=f"오늘 {TODAY}일", annotation_position="top",
              row=1, col=1)
fig.add_vrect(x0=TODAY - 30, x1=TODAY, fillcolor="#1f77b4", opacity=0.10,
              line_width=0, annotation_text="30일 창 (방법 1·2)",
              annotation_position="bottom left", row=1, col=1)
fig.add_vrect(x0=TODAY - LONGEST_CYCLE, x1=TODAY, fillcolor="#d62728",
              opacity=0.07, line_width=0,
              annotation_text=f"{LONGEST_CYCLE}일 창 (방법 3)",
              annotation_position="top left", row=1, col=1)
fig.add_annotation(x=88, y="분기 결산", ax=60, ay=-46, showarrow=True,
                   arrowhead=2, text="92일 창 «안». 여기서 갈린다",
                   font=dict(color="#d62728", size=11), row=1, col=1)

# --- 아래 패널: 판정 vs 오늘
TS = list(range(1, 261))
LEVEL = {0: 3, 1: 2, 2: 1}
for i, (name, fn) in enumerate(METHODS):
    ys = [LEVEL[i] + (0.30 if fn(D, t)[0] else -0.30) for t in TS]
    fig.add_trace(go.Scatter(
        x=TS, y=ys, mode="lines", line=dict(width=3, shape="hv",
                                            color=["#1f77b4", "#9467bd", "#d62728"][i]),
        name=f"방법 {i + 1}: {name}",
        hovertemplate=f"방법 {i + 1}<br>오늘 %{{x}}일<extra></extra>",
    ), row=2, col=1)

fig.add_vrect(x0=118, x1=180, fillcolor="#ffcc00", opacity=0.22, line_width=0,
              annotation_text="결론이 갈리는 63일<br>(방법 1·2 «지워도 됨» vs 방법 3 «아직»)",
              annotation_position="top left", row=2, col=1)
fig.add_vline(x=TODAY, line=dict(color="black", width=2),
              annotation_text=f"예제의 오늘 {TODAY}일 ", annotation_position="bottom left",
              row=2, col=1)
fig.add_vline(x=180, line=dict(color="#d62728", width=1.5, dash="dot"),
              annotation_text="분기 결산 다음 실행 180일",
              annotation_position="top right", row=2, col=1)

fig.update_xaxes(title_text="일자", range=[-8, 152], row=1, col=1)
fig.update_xaxes(title_text="「오늘」을 언제로 두는가 (일)", range=[0, 260], row=2, col=1)
fig.update_yaxes(title_text="", row=1, col=1)
fig.update_yaxes(tickvals=[3.3, 2.7, 2.3, 1.7, 1.3, 0.7],
                 ticktext=["지워도 됨", "아직", "지워도 됨", "아직", "지워도 됨", "아직"],
                 range=[0.4, 3.7], row=2, col=1)
fig.update_layout(
    height=880, width=1180, template="plotly_white",
    title="ex3_when_to_contract.py — 세 판정 방법이 갈리는 지점",
    legend=dict(orientation="h", yanchor="bottom", y=-0.13, x=0),
    margin=dict(l=110, r=40, t=90, b=130),
)

_show(fig)

# %%
import os

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(out, scale=2)
print("saved:", out)
# 출력: saved: .../expy.png

# %% [markdown]
# ## 정리
#
# 1. 방법 1(최근 30일 0건)과 방법 2(모든 주체 30일 조용)는 **집계 단위만 다르고 임계값이 같다.**
#    260일을 훑어도 한 번도 갈리지 않는다. 둘 다 「지워도 됨」.
# 2. 방법 3만 임계값을 **관측된 가장 긴 배치 주기(92일)**로 둔다. 「아직」.
# 3. 갈림점은 **분기 결산의 경과 52일** — $30 \le 52 < 92$.
# 4. 그 잡은 180일째에 깨어난다. 예제의 오늘(140일)로부터 40일 뒤.
#    앞의 둘을 믿고 지우면 그날 깨진다. **세 번째가 맞다.**
# 5. 그래서 수축 기준은 「시간(30일)」이 아니라 「가장 긴 주기」다.
#    주기는 크론 표현식을 파싱해서 구하고, 크론에 없는 것(사람이 손으로 도는 것)은
#    경고 로그와 알림으로 잡고, 지울 때는 되돌릴 수 있게(`이끔` → `_deprecated_이끔`) 지운다.
