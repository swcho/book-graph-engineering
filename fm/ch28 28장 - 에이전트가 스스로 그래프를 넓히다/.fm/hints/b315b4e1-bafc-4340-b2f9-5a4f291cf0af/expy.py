# %% [markdown]
# # ex3_provenance.py 재현 — 출처 하나를 철회하면 무엇이 무너지는가
#
# 28.3절 「어디서 온 사실인가」의 `ex3_provenance.py`를 kuzu 없이
# **순수 파이썬 자료구조**로 재현한다.
#
# 핵심 구조는 두 개다.
#
# - `SOURCES` / `FACTS` — 모든 엣지가 **출처(source)** 를 하나씩 달고 있다
# - `DERIVED_FROM` — 추론된 사실이 **어떤 사실에 기댔는지**를 적어 둔 근거 DAG
#
# 사실 집합을 $F$, 근거 함수를 $B: F \to 2^{F}$ 라 두면 추론 사실 $f$ 가 살아 있을 조건은
#
# $$\mathrm{alive}(f) \iff \mathrm{alive}(\mathrm{src}(f)) \;\wedge\; \bigwedge_{b \in B(f)} \mathrm{alive}(b)$$
#
# 즉 **논리곱(AND)** 이다. 근거 중 하나만 죽어도 $f$ 는 죽는다.
# 이것이 진리 유지 시스템(truth maintenance)의 justification 이고,
# 출처 철회는 이 조건을 따라 그래프를 거슬러 **연쇄 무효화**된다.
#
# 필요 패키지: plotly, kaleido (없으면 시각화 셀만 건너뛰면 된다. 계산 셀은 표준 라이브러리만 쓴다)

# %%
def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# 출처: id -> (이름, 날짜, 신뢰도)
SOURCES = {
    "src1": ("사용자 발화", "2026-05-01", 1.00),
    "src2": ("사내 위키 v3", "2026-04-20", 0.90),
    "src3": ("에이전트 추론", "2026-05-02", 0.55),
    "src4": ("외부 기사", "2026-03-11", 0.40),
}

# 사실: (주어, 관계, 목적어, 출처)
FACTS = [
    ("박민수", "이끔", "결제팀", "src1"),
    ("이서연", "속함", "결제팀", "src2"),
    ("이서연", "삶", "마포", "src1"),
    ("박민수", "삶", "마포", "src4"),      # 외부 기사에서 왔다
    ("이서연", "동료", "박민수", "src3"),  # 위 둘에서 «추론»된 것
    ("이서연", "이웃", "박민수", "src3"),  # 이것도 추론
]

# 추론된 사실이 어떤 사실에 기대고 있는지 (근거 DAG의 엣지)
DERIVED_FROM = {
    ("이서연", "동료", "박민수"): [("이서연", "속함", "결제팀"),
                                   ("박민수", "이끔", "결제팀")],
    ("이서연", "이웃", "박민수"): [("이서연", "삶", "마포"),
                                   ("박민수", "삶", "마포")],
}

SRC_OF = {(s, k, o): src for s, k, o, src in FACTS}
ALL_FACTS = [(s, k, o) for s, k, o, _ in FACTS]


def fmt(f):
    return f"{f[0]} -{f[1]}-> {f[2]}"


print(f"사실 {len(ALL_FACTS)}개, 출처 {len(SOURCES)}개, 추론 사실 {len(DERIVED_FROM)}개")
for f in ALL_FACTS:
    src = SRC_OF[f]
    tag = "추론" if f in DERIVED_FROM else "직접"
    print(f"  {fmt(f):<24} 출처 {SOURCES[src][0]:<12} 신뢰 {SOURCES[src][2]:.2f}  [{tag}]")

# 출력:
# 사실 6개, 출처 4개, 추론 사실 2개
#   박민수 -이끔-> 결제팀          출처 사용자 발화       신뢰 1.00  [직접]
#   이서연 -속함-> 결제팀          출처 사내 위키 v3      신뢰 0.90  [직접]
#   이서연 -삶-> 마포              출처 사용자 발화       신뢰 1.00  [직접]
#   박민수 -삶-> 마포              출처 외부 기사         신뢰 0.40  [직접]
#   이서연 -동료-> 박민수          출처 에이전트 추론     신뢰 0.55  [추론]
#   이서연 -이웃-> 박민수          출처 에이전트 추론     신뢰 0.55  [추론]

# %% [markdown]
# ## 1. 연쇄 철회 — 부동점(fixed point)까지 반복
#
# `ex3_provenance.py`의 `retract()`는 `while changed:` 루프로
# 「더 이상 죽는 게 없을 때까지」 반복한다. 즉 부동점 계산이다.
#
# 1. 그 출처를 단 엣지를 전부 `alive=false` (**직접** 사망)
# 2. 살아 있는 추론 사실 중 근거가 하나라도 죽은 것을 죽인다 (**연쇄** 사망)
# 3. 2에서 뭐라도 죽었으면 다시 2로 (추론이 추론에 기댈 수 있으므로)
#
# 원본은 kuzu 쿼리로 하지만 여기서는 `alive` 딕셔너리 하나로 같은 일을 한다.

# %%
def retract(src_to_kill, facts=ALL_FACTS, verbose=False):
    """출처 하나를 철회하고 (직접 사망, 연쇄 사망) 목록을 돌려준다."""
    alive = {f: True for f in facts}
    direct, cascaded = [], []

    # 1) 직접 사망 — 그 출처를 단 엣지
    for f in facts:
        if SRC_OF[f] == src_to_kill:
            alive[f] = False
            direct.append(f)

    # 2~3) 근거가 죽은 추론을 부동점까지 연쇄로 죽인다
    round_no = 0
    changed = True
    while changed:
        changed = False
        round_no += 1
        for derived, bases in DERIVED_FROM.items():
            if not alive.get(derived, False):
                continue
            for b in bases:
                if not alive.get(b, False):
                    alive[derived] = False
                    cascaded.append(derived)
                    changed = True
                    if verbose:
                        print(f"    라운드 {round_no}: {fmt(derived)} "
                              f"← 근거 {fmt(b)} 가 죽음")
                    break
    return direct, cascaded, alive


print("외부 기사(src4)가 오보로 밝혀져 철회한다.\n")
direct, cascaded, alive4 = retract("src4", verbose=True)
for f in direct:
    print(f"  죽임: {fmt(f):<24} (직접)")
for f in cascaded:
    print(f"  죽임: {fmt(f):<24} (연쇄)")

print("\n철회 뒤 살아 있는 사실:")
for f in ALL_FACTS:
    if alive4[f]:
        print(f"  {fmt(f):<24} 출처 {SOURCES[SRC_OF[f]][0]}")

print(f"\n엣지 1개를 지웠는데 {len(direct) + len(cascaded)}개가 사라졌다.")

# 출력:
# 외부 기사(src4)가 오보로 밝혀져 철회한다.
#
#     라운드 1: 이서연 -이웃-> 박민수 ← 근거 박민수 -삶-> 마포 가 죽음
#   죽임: 박민수 -삶-> 마포          (직접)
#   죽임: 이서연 -이웃-> 박민수      (연쇄)
#
# 철회 뒤 살아 있는 사실:
#   박민수 -이끔-> 결제팀          출처 사용자 발화
#   이서연 -속함-> 결제팀          출처 사내 위키 v3
#   이서연 -삶-> 마포              출처 사용자 발화
#   이서연 -동료-> 박민수          출처 에이전트 추론
#
# 엣지 1개를 지웠는데 2개가 사라졌다.

# %% [markdown]
# 답이 이것이다. **오보인 「박민수가 마포에 산다」를 철회하니 「이웃이다」도 같이 무너진다.**
#
# 「동료다」는 살아남는다. 그것은 src1·src2에 기대고 있어서 src4와 무관하기 때문이다.
# 근거를 적어 두지 않았다면 이 구분을 할 수 없다 — 오보를 지워도 「이웃이다」는
# 어디서 왔는지 아무도 모르는 사실로 그래프에 남는다.

# %% [markdown]
# ## 2. 출처별 파급 범위 비교
#
# 출처 $s$ 의 파급(blast radius)을
#
# $$\mathrm{blast}(s) = \bigl|\{f \in F : \neg\mathrm{alive}(f) \text{ after retracting } s\}\bigr|$$
#
# 로 정의하고 네 출처를 각각 철회해 본다. 파급이 큰 출처일수록
# **그래프의 신뢰도를 지배**한다 — 신뢰도 0.40짜리 외부 기사가
# 자기 엣지 하나보다 더 넓은 범위를 무너뜨린다면 그건 위험 신호다.

# %%
rows = []
for src in SOURCES:
    d, c, _ = retract(src)
    rows.append({
        "src": src,
        "name": SOURCES[src][0],
        "conf": SOURCES[src][2],
        "direct": len(d),
        "cascade": len(c),
        "total": len(d) + len(c),
        "amp": (len(d) + len(c)) / len(d) if d else 0.0,
        "killed": [fmt(x) for x in d + c],
    })

print(f"{'출처':<14}{'신뢰':>6}{'직접':>6}{'연쇄':>6}{'합계':>6}{'증폭':>7}  무효화된 사실")
print("-" * 92)
for r in sorted(rows, key=lambda x: -x["total"]):
    print(f"{r['name']:<14}{r['conf']:>6.2f}{r['direct']:>6}{r['cascade']:>6}"
          f"{r['total']:>6}{r['amp']:>7.1f}x  {', '.join(r['killed'])}")

# 출력:
# 출처              신뢰  직접  연쇄  합계     증폭  무효화된 사실
# --------------------------------------------------------------------------------------------
# 사용자 발화        1.00     2     2     4    2.0x  박민수 -이끔-> 결제팀, 이서연 -삶-> 마포, 이서연 -동료-> 박민수, 이서연 -이웃-> 박민수
# 사내 위키 v3       0.90     1     1     2    2.0x  이서연 -속함-> 결제팀, 이서연 -동료-> 박민수
# 에이전트 추론      0.55     2     0     2    1.0x  이서연 -동료-> 박민수, 이서연 -이웃-> 박민수
# 외부 기사          0.40     1     1     2    2.0x  박민수 -삶-> 마포, 이서연 -이웃-> 박민수

# %% [markdown]
# 읽는 법이 세 가지다.
#
# - **사용자 발화(src1)** 는 직접 2 + 연쇄 2 = 4개, 전체 6개 중 3분의 2를 무너뜨린다.
#   신뢰도 1.00인 출처가 그래프의 등뼈다. 이것이 흔들리면 그래프가 흔들린다.
# - **에이전트 추론(src3)** 은 증폭이 1.0배다. 잎(leaf)이라 아무도 그것에 기대지 않는다.
#   지금은 그렇다 — 추론 위에 또 추론을 쌓기 시작하면 이 숫자가 올라간다.
# - **외부 기사(src4)** 는 신뢰도 0.40인데 증폭이 2.0배다.
#   *제일 약한 출처가 자기 몫보다 넓게 퍼져 있다.* 28장이 경고하는 상황이다.
#
# 추론 결과의 신뢰도는 근거 중 가장 약한 것을 넘을 수 없다:
#
# $$\mathrm{conf}(f) \le \min_{b \in B(f)} \mathrm{conf}(b)$$

# %%
print(f"{'추론 사실':<22}{'선언된 신뢰':>12}{'근거 최소':>10}  근거")
print("-" * 78)
for d, bases in DERIVED_FROM.items():
    declared = SOURCES[SRC_OF[d]][2]
    weakest = min(SOURCES[SRC_OF[b]][2] for b in bases)
    flag = "  ← 과대평가" if declared > weakest else ""
    print(f"{fmt(d):<22}{declared:>12.2f}{weakest:>10.2f}  "
          f"{' + '.join(fmt(b) for b in bases)}{flag}")

# 출력:
# 추론 사실                   선언된 신뢰    근거 최소  근거
# ------------------------------------------------------------------------------
# 이서연 -동료-> 박민수              0.55      0.90  이서연 -속함-> 결제팀 + 박민수 -이끔-> 결제팀
# 이서연 -이웃-> 박민수              0.55      0.40  이서연 -삶-> 마포 + 박민수 -삶-> 마포  ← 과대평가

# %% [markdown]
# 「이웃이다」는 0.55로 적혀 있는데 근거 중 제일 약한 것이 0.40이다.
# 선언된 신뢰가 근거보다 높다 — **철회되기 전에 이미 과대평가돼 있었다.**
# 출처를 달아 두면 철회를 기다리지 않고 이 불일치를 미리 잡을 수 있다.

# %% [markdown]
# ## 3. 시각화 — 근거 DAG와 출처별 파급 범위

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

SRC_COLOR = {"src1": "#2E86C1", "src2": "#28B463", "src3": "#8E44AD", "src4": "#CB4335"}

# 근거 DAG 좌표: 아래 = 직접 사실(출처에서 옴), 위 = 추론 사실
POS = {
    ("박민수", "이끔", "결제팀"): (0.0, 0.0),
    ("이서연", "속함", "결제팀"): (1.0, 0.0),
    ("이서연", "삶", "마포"): (2.0, 0.0),
    ("박민수", "삶", "마포"): (3.0, 0.0),
    ("이서연", "동료", "박민수"): (0.5, 1.0),
    ("이서연", "이웃", "박민수"): (2.5, 1.0),
}

fig = make_subplots(
    rows=1, cols=2,
    column_widths=[0.58, 0.42],
    subplot_titles=("근거 DAG (붉은 점선 = src4 철회로 죽는 경로)",
                    "출처별 파급 범위 (직접 + 연쇄)"),
    specs=[[{"type": "scatter"}, {"type": "bar"}]],
)

# --- 왼쪽: 근거 DAG ---
dead4 = {f for f in ALL_FACTS if not alive4[f]}
for derived, bases in DERIVED_FROM.items():
    for b in bases:
        x0, y0 = POS[b]
        x1, y1 = POS[derived]
        broken = b in dead4
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1], mode="lines",
            line=dict(color="#CB4335" if broken else "#AAB7B8",
                      width=3 if broken else 1.6,
                      dash="dot" if broken else "solid"),
            hoverinfo="skip", showlegend=False), row=1, col=1)

for src in SOURCES:
    mine = [f for f in ALL_FACTS if SRC_OF[f] == src]
    fig.add_trace(go.Scatter(
        x=[POS[f][0] for f in mine], y=[POS[f][1] for f in mine],
        mode="markers+text",
        text=[fmt(f) for f in mine], textposition="bottom center",
        textfont=dict(size=9),
        marker=dict(size=[26 if f in dead4 else 20 for f in mine],
                    color=SRC_COLOR[src],
                    line=dict(color="#1B2631", width=2),
                    symbol=["x" if f in dead4 else "circle" for f in mine]),
        name=f"{SOURCES[src][0]} ({SOURCES[src][2]:.2f})",
        hovertext=[f"{fmt(f)}<br>출처 {SOURCES[src][0]} ({SOURCES[src][2]:.2f})"
                   f"<br>{'src4 철회 후 사망' if f in dead4 else '생존'}" for f in mine],
        hoverinfo="text", legendgroup=src), row=1, col=1)

fig.add_annotation(x=-0.55, y=0.0, text="직접 사실", showarrow=False,
                   font=dict(size=10, color="#566573"), row=1, col=1)
fig.add_annotation(x=-0.55, y=1.0, text="추론 사실", showarrow=False,
                   font=dict(size=10, color="#566573"), row=1, col=1)

# --- 오른쪽: 파급 범위 막대 ---
order = sorted(rows, key=lambda r: r["total"])
labels = [f"{r['name']}<br>({r['conf']:.2f})" for r in order]
fig.add_trace(go.Bar(
    y=labels, x=[r["direct"] for r in order], orientation="h",
    name="직접 무효화", marker_color="#5D6D7E",
    text=[r["direct"] for r in order], textposition="inside"), row=1, col=2)
fig.add_trace(go.Bar(
    y=labels, x=[r["cascade"] for r in order], orientation="h",
    name="연쇄 무효화", marker_color="#CB4335",
    text=[r["cascade"] for r in order], textposition="inside"), row=1, col=2)

fig.update_layout(
    barmode="stack",
    title="ex3_provenance — 출처 하나를 철회하면 무엇이 연쇄로 죽는가",
    height=560, width=1280, template="plotly_white",
    legend=dict(orientation="h", y=-0.12))
fig.update_xaxes(visible=False, range=[-0.9, 3.6], row=1, col=1)
fig.update_yaxes(visible=False, range=[-0.45, 1.35], row=1, col=1)
fig.update_xaxes(title_text="무효화된 사실 수 (전체 6개 중)", dtick=1, row=1, col=2)

_show(fig)

import os
_png = os.path.join(os.path.dirname(os.path.abspath(__file__))
                    if "__file__" in dir() else ".", "expy.png")
try:
    fig.write_image(_png, scale=2)
    print(f"저장: {_png}")
except Exception as e:  # kaleido 미설치 등
    print(f"이미지 저장 실패(kaleido 필요): {e}")

# 출력: 저장: .../expy.png

# %% [markdown]
# ## 정리
#
# | 물음 | 답 |
# |---|---|
# | 철회하면 무엇이 죽나 | 그 출처를 단 엣지가 **직접** 죽고, 거기 기대던 추론이 **연쇄**로 죽는다 |
# | 어떻게 아나 | `DERIVED_FROM`에 「무엇에 기댔는지」를 **추론하는 그 순간에** 적어 뒀기 때문 |
# | 언제 멈추나 | 더 죽는 게 없을 때까지(부동점). 추론이 추론에 기댈 수 있으므로 한 바퀴로는 부족 |
# | 안 적어 두면 | 오보인 줄 알아도 「이웃이다」가 남는다. 출처 불명 사실이 쌓이면 그래프 전체를 못 믿게 된다 |
#
# 그리고 예제가 스스로 다는 단서 — 이 예제는 근거를 **손으로** 적어 뒀지만,
# 실무에서는 추론할 때 그때그때 기록해야 한다. **나중에는 복원 못 한다.**
