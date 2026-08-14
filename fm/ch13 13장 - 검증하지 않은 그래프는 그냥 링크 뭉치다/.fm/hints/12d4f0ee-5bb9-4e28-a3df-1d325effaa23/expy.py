# %% [markdown]
# # 품질을 한 숫자로 합치면 안 되는 이유
#
# 13.5절 `ex5_quality_metrics.py`를 재현하고, **왜 종합 점수가 거짓말을 하는지**를
# 수치로 분해해 본다.
#
# 핵심 문장:
#
# > 데이터가 늘면 **비율**은 좋아지고 **절대 개수**는 나빠진다. 둘 다 적어야 속지 않는다.
#
# 필요 패키지: `plotly`, `kaleido` (정적 이미지 저장용). 없으면 표 출력까지는 그대로 동작한다.

# %%
# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
from pathlib import Path


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


HERE = Path(__file__).parent if "__file__" in globals() else Path.cwd()
print("작업 폴더:", HERE.name)
# 출력: 작업 폴더: 12d4f0ee-5bb9-4e28-a3df-1d325effaa23


# %% [markdown]
# ## 1. 6주간의 원본 지표
#
# 그래프가 커지는 중이다. 1주 12,000 노드에서 6주 102,000 노드로 8.5배.
# 같이 기록한 지표는 다섯 가지다.
#
# | 지표 | 성격 |
# |---|---|
# | 차단 위반 수 | 절대 개수 |
# | 경고 수 | 절대 개수 |
# | 기록 수 | 절대 개수 |
# | 필수 속성 채움률 | 비율 |
# | 링크 유효율 | 비율 |

# %%
# (주차, 전체 노드, 차단, 경고, 기록, 필수속성 채움률, 링크 유효율)
WEEKS = [
    (1, 12_000, 40, 210, 980, 0.94, 0.99),
    (2, 18_000, 38, 260, 1420, 0.93, 0.99),
    (3, 26_000, 35, 340, 2100, 0.92, 0.98),
    (4, 41_000, 33, 520, 3350, 0.91, 0.98),
    (5, 63_000, 31, 810, 5200, 0.90, 0.97),
    (6, 102_000, 29, 1310, 8400, 0.89, 0.95),
]

for w, n, blk, warn, info, fill, link in WEEKS:
    print(f"{w}주  노드 {n:>7,}  차단 {blk:>3}  경고 {warn:>5,}  기록 {info:>5,}  채움 {fill:.2f}  링크 {link:.2f}")
# 출력:
# 1주  노드  12,000  차단  40  경고   210  기록   980  채움 0.94  링크 0.99
# 2주  노드  18,000  차단  38  경고   260  기록 1,420  채움 0.93  링크 0.99
# 3주  노드  26,000  차단  35  경고   340  기록 2,100  채움 0.92  링크 0.98
# 4주  노드  41,000  차단  33  경고   520  기록 3,350  채움 0.91  링크 0.98
# 5주  노드  63,000  차단  31  경고   810  기록 5,200  채움 0.90  링크 0.97
# 6주  노드 102,000  차단  29  경고 1,310  기록 8,400  채움 0.89  링크 0.95


# %% [markdown]
# ## 2. 흔히 쓰는 «종합 품질 점수»
#
# 위반에 심각도 가중치를 주고, 전체 노드 수의 절반으로 나눠 100점에서 뺀다.
#
# $$\text{bad} = 10 \cdot \text{차단} + 3 \cdot \text{경고} + 1 \cdot \text{기록}$$
#
# $$\text{score} = \max\left(0,\; 100 \times \left(1 - \frac{\text{bad}}{0.5\,N}\right)\right)$$
#
# 여기서 $N$은 전체 노드 수다. 분모에 $N$이 들어간다는 게 이 절의 전부다.
# **분자(위반 개수)보다 분모(데이터 크기)가 더 빨리 자라면 점수는 자동으로 올라간다.**

# %%
def composite(row):
    """흔히 쓰는 «품질 점수» — 위반율을 뒤집어 100점 만점으로."""
    _, n, blk, warn, info, fill, link = row
    bad = blk * 10 + warn * 3 + info
    return max(0.0, 100 * (1 - bad / (n * 0.5)))


print(f"{'주':>3} {'노드':>9} {'차단':>6} {'경고':>7} {'기록':>7} {'채움률':>7} {'링크':>7} {'종합점수':>9}")
print("-" * 66)
for r in WEEKS:
    w, n, blk, warn, info, fill, link = r
    print(f"{w:>3} {n:>9,} {blk:>6} {warn:>7,} {info:>7,} {fill:>7.2f} {link:>7.2f} {composite(r):>9.1f}")
# 출력:
#   주        노드     차단      경고      기록     채움률      링크      종합점수
# ------------------------------------------------------------------
#   1    12,000     40     210     980    0.94    0.99      66.5
#   2    18,000     38     260   1,420    0.93    0.99      71.3
#   3    26,000     35     340   2,100    0.92    0.98      73.3
#   4    41,000     33     520   3,350    0.91    0.98      74.4
#   5    63,000     31     810   5,200    0.90    0.97      74.8
#   6   102,000     29   1,310   8,400    0.89    0.95      75.3


# %% [markdown]
# ## 3. 분자와 분모를 갈라 보면
#
# 종합 점수가 66.5 → 75.3으로 «좋아졌다». 그런데 분자를 보자.

# %%
print(f"{'주':>3} {'bad(가중합)':>12} {'분모 0.5N':>10} {'bad/0.5N':>10} {'점수':>7}")
print("-" * 48)
base = None
for r in WEEKS:
    w, n, blk, warn, info, _, _ = r
    bad = blk * 10 + warn * 3 + info
    if base is None:
        base = (bad, n)
    print(f"{w:>3} {bad:>12,} {int(n * 0.5):>10,} {bad / (n * 0.5):>10.4f} {composite(r):>7.1f}")

bad6 = WEEKS[-1][2] * 10 + WEEKS[-1][3] * 3 + WEEKS[-1][4]
print(f"\n분자 bad: {base[0]:,} → {bad6:,}  ({bad6 / base[0]:.2f}배)")
print(f"분모 N  : {base[1]:,} → {WEEKS[-1][1]:,}  ({WEEKS[-1][1] / base[1]:.2f}배)")
print("분모가 더 빨리 자란다 → 비율은 좋아진다. 그런데 사람이 손으로 치워야 할 일감은 6배가 됐다.")
# 출력:
#   주    bad(가중합)     분모 0.5N   bad/0.5N      점수
# ------------------------------------------------
#   1        2,010      6,000     0.3350    66.5
#   2        2,580      9,000     0.2867    71.3
#   3        3,470     13,000     0.2669    73.3
#   4        5,240     20,500     0.2556    74.4
#   5        7,940     31,500     0.2521    74.8
#   6       12,620     51,000     0.2475    75.3
#
# 분자 bad: 2,010 → 12,620  (6.28배)
# 분모 N  : 12,000 → 102,000  (8.50배)
# 분모가 더 빨리 자란다 → 비율은 좋아진다. 그런데 사람이 손으로 치워야 할 일감은 6배가 됐다.


# %% [markdown]
# ## 4. 지표를 따로 보면 방향이 제각각이다
#
# 종합 점수 하나가 감춘 것을 지표별로 펴 본다.
# 1주를 100으로 놓은 상대 변화(%)로 그리면 방향이 확연히 갈린다.

# %%
names = ["차단", "경고", "기록", "채움률", "링크유효율", "종합점수"]
idx = [2, 3, 4, 5, 6]
series = {}
for k, name in zip(idx, names[:5]):
    series[name] = [r[k] for r in WEEKS]
series["종합점수"] = [composite(r) for r in WEEKS]

print(f"{'지표':<10} {'1주':>10} {'6주':>10} {'변화':>9}  판정")
print("-" * 52)
for name, vals in series.items():
    first, last = vals[0], vals[-1]
    delta = (last / first - 1) * 100
    # 차단/경고/기록은 낮을수록 좋고, 나머지는 높을수록 좋다
    lower_is_better = name in ("차단", "경고", "기록")
    good = (delta < 0) if lower_is_better else (delta > 0)
    print(f"{name:<10} {first:>10,.2f} {last:>10,.2f} {delta:>+8.1f}%  {'좋아짐' if good else '나빠짐'}")
# 출력:
# 지표                 1주         6주        변화  판정
# ----------------------------------------------------
# 차단              40.00      29.00    -27.5%  좋아짐
# 경고             210.00   1,310.00   +523.8%  나빠짐
# 기록             980.00   8,400.00   +757.1%  나빠짐
# 채움률             0.94       0.89     -5.3%  나빠짐
# 링크유효율           0.99       0.95     -4.0%  나빠짐
# 종합점수           66.50      75.25    +13.2%  좋아짐


# %% [markdown]
# ## 5. 같은 사건을 비율로도, 개수로도 적어 보기
#
# 「경고」 하나만 두 방식으로 적어 본다. 완전히 반대 이야기가 나온다.
#
# - 비율: $\dfrac{\text{경고}}{N}$ — 1,000노드당 몇 건인가
# - 개수: 경고 그 자체 — 사람이 실제로 처리해야 할 건수

# %%
print(f"{'주':>3} {'경고 개수':>9} {'천노드당 경고':>13}")
print("-" * 30)
for w, n, blk, warn, info, fill, link in WEEKS:
    print(f"{w:>3} {warn:>9,} {warn / n * 1000:>13.2f}")
print("\n비율은 17.50 → 12.84 로 «개선».  개수는 210 → 1,310 으로 6.2배 «악화».")
print("둘 다 사실이다. 하나만 적으면 반드시 속는다.")
# 출력:
#   주     경고 개수      천노드당 경고
# ------------------------------
#   1       210         17.50
#   2       260         14.44
#   3       340         13.08
#   4       520         12.68
#   5       810         12.86
#   6     1,310         12.84
#
# 비율은 17.50 → 12.84 로 «개선».  개수는 210 → 1,310 으로 6.2배 «악화».
# 둘 다 사실이다. 하나만 적으면 반드시 속는다.


# %% [markdown]
# ## 6. 심슨의 역설과 같은 구조
#
# 이건 통계에서 말하는 **심슨의 역설**(Simpson's paradox)과 같은 함정이다.
# 부분집합별 비율은 모두 나빠졌는데, 크기가 다른 집단을 합치면 전체 비율이 좋아 보일 수 있다.
#
# 아래는 「원래 있던 더러운 도메인은 그대로인데, 크고 비교적 깨끗한 도메인이 급성장」한 상황이다.
# 두 도메인의 오류율은 **둘 다 나빠졌는데** 전체 오류율은 **좋아 보인다**.
# 그리고 실제로 고쳐야 할 건수는 3.5배가 됐다.

# %%
# (도메인, 노드 수, 오류 수)
BEFORE = [("깨끗한 도메인", 1_000, 10), ("더러운 도메인", 1_000, 300)]  # 1.0% / 30.0%
AFTER = [("깨끗한 도메인", 50_000, 750), ("더러운 도메인", 1_000, 320)]  # 1.5% / 32.0%


def rate(rows):
    n = sum(x[1] for x in rows)
    e = sum(x[2] for x in rows)
    return e / n


for label, rows in (("전", BEFORE), ("후", AFTER)):
    parts = "  ".join(f"{d}: {e / n:.2%}" for d, n, e in rows)
    print(f"{label}  {parts}   전체 오류율: {rate(rows):.2%}")

err_before = sum(x[2] for x in BEFORE)
err_after = sum(x[2] for x in AFTER)
print("\n부분집합 오류율: 1.00%→1.50%, 30.00%→32.00%.  둘 다 나빠졌다.")
print("전체 오류율:    15.50% → 2.10%.  «좋아졌다»고 보고된다.")
print(f"고쳐야 할 건수: {err_before} → {err_after}  ({err_after / err_before:.1f}배).")
print("한 숫자로 합치는 순간 이 셋 중 마지막 둘이 사라진다.")
# 출력:
# 전  깨끗한 도메인: 1.00%  더러운 도메인: 30.00%   전체 오류율: 15.50%
# 후  깨끗한 도메인: 1.50%  더러운 도메인: 32.00%   전체 오류율: 2.10%
#
# 부분집합 오류율: 1.00%→1.50%, 30.00%→32.00%.  둘 다 나빠졌다.
# 전체 오류율:    15.50% → 2.10%.  «좋아졌다»고 보고된다.
# 고쳐야 할 건수: 310 → 1070  (3.5배).
# 한 숫자로 합치는 순간 이 셋 중 마지막 둘이 사라진다.


# %% [markdown]
# ## 7. 시각화 — 한 장에 겹쳐 놓으면 거짓말이 보인다
#
# 왼쪽 위: 종합 점수 혼자 우상향.
# 오른쪽 위: 절대 개수는 폭증.
# 왼쪽 아래: 비율 지표는 완만히 하락.
# 오른쪽 아래: 경고를 «개수»와 «천 노드당»으로 나란히.

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    weeks = [r[0] for r in WEEKS]
    nodes = [r[1] for r in WEEKS]
    blocks = [r[2] for r in WEEKS]
    warns = [r[3] for r in WEEKS]
    infos = [r[4] for r in WEEKS]
    fills = [r[5] for r in WEEKS]
    links = [r[6] for r in WEEKS]
    scores = [composite(r) for r in WEEKS]
    warn_per_k = [w / n * 1000 for w, n in zip(warns, nodes)]

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "종합 점수 — 혼자 보면 «좋아지는 중»",
            "절대 개수 — 경고·기록이 폭증",
            "비율 지표 — 조용히 하락",
            "경고: 개수 vs 천 노드당 비율",
        ),
        specs=[[{}, {}], [{}, {"secondary_y": True}]],
    )

    fig.add_trace(
        go.Scatter(x=weeks, y=scores, mode="lines+markers", name="종합 점수", line=dict(color="#2E86DE", width=3)),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=weeks, y=blocks, mode="lines+markers", name="차단", line=dict(color="#10AC84")), row=1, col=2
    )
    fig.add_trace(
        go.Scatter(x=weeks, y=warns, mode="lines+markers", name="경고", line=dict(color="#EE5A24")), row=1, col=2
    )
    fig.add_trace(
        go.Scatter(x=weeks, y=infos, mode="lines+markers", name="기록", line=dict(color="#8395A7")), row=1, col=2
    )
    fig.add_trace(
        go.Scatter(x=weeks, y=fills, mode="lines+markers", name="채움률", line=dict(color="#9B59B6")), row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=weeks, y=links, mode="lines+markers", name="링크 유효율", line=dict(color="#F79F1F")), row=2, col=1
    )
    fig.add_trace(go.Bar(x=weeks, y=warns, name="경고 개수", marker_color="#EE5A24"), row=2, col=2)
    fig.add_trace(
        go.Scatter(
            x=weeks, y=warn_per_k, mode="lines+markers", name="천 노드당 경고", line=dict(color="#2E86DE", width=3)
        ),
        row=2,
        col=2,
        secondary_y=True,
    )

    fig.update_yaxes(title_text="점수", row=1, col=1)
    fig.update_yaxes(title_text="건수(로그)", type="log", row=1, col=2)
    fig.update_yaxes(title_text="비율", range=[0.85, 1.0], row=2, col=1)
    fig.update_yaxes(title_text="개수", row=2, col=2, secondary_y=False)
    fig.update_yaxes(title_text="천 노드당", row=2, col=2, secondary_y=True)
    fig.update_xaxes(title_text="주차")
    fig.update_layout(
        title_text="품질을 한 숫자로 합치면 안 되는 이유 — 비율은 좋아지고 개수는 나빠진다",
        height=760,
        width=1150,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.12),
    )

    _show(fig)

    out = HERE / "expy.png"
    fig.write_image(str(out), scale=2)
    print("저장:", out.name)
except ImportError as e:
    print("plotly/kaleido 없음 — 시각화를 건너뛴다:", e)
# 출력: 저장: expy.png


# %% [markdown]
# ## 8. 정리
#
# 1. **종합 점수의 분모는 데이터 크기다.** 데이터가 위반보다 빨리 자라면 점수는 저절로 오른다.
#    지표가 아니라 성장률을 재는 셈이 된다.
# 2. **합치면 방향이 다른 지표가 상쇄된다.** 차단 위반은 정말 줄었는데(40 → 29),
#    경고 폭증(210 → 1,310)과 링크 유효율 하락(0.99 → 0.95)이 한 숫자 안에서 서로를 지운다.
# 3. **비율만 적으면 일감의 크기를 못 본다.** 천 노드당 경고는 17.5 → 12.8로 좋아졌지만,
#    사람이 손으로 치워야 할 경고는 210건에서 1,310건이 됐다. 팀 인원은 그대로다.
# 4. **개수만 적으면 성장을 벌준다.** 데이터가 8.5배 늘었는데 경고가 6.3배만 늘었다면
#    단위 데이터당 품질은 실제로 나아진 것이다. 개수만 보면 이 개선이 안 보인다.
#
# 그래서 규칙 두 가지:
#
# > 1. 지표를 하나로 합치지 않는다. 넷이면 넷을 다 보여 준다.
# > 2. 절대 개수와 비율을 **둘 다** 적는다. 하나만 적으면 반드시 속는다.
