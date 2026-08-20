# %% [markdown]
# # 여섯 위상: 품질 1등과 그 대가
#
# 질문: **여섯 위상 중 품질이 가장 높은 것과 그 대가는 무엇인가?**
#
# 답: **순환(생성-검증)이 0.89로 가장 높지만 토큰이 가장 많이 든다.
# '토큰당 품질'로 보면 오히려 아래쪽이다.**
#
# 이 노트북은 `ex1_topologies.py` 의 비용 모델을 그대로 재현해서,
# 「품질 순위」와 「토큰당 품질 순위」가 어떻게 뒤집히는지 계산하고 그린다.
#
# 핵심 지표 정의:
#
# $$\text{효율} = \frac{q}{\text{tok}} \times 10^4$$
#
# 품질 $q$ 는 위로 갈수록 좋고, 토큰 $\text{tok}$ 은 아래로 갈수록 좋다.
# 두 지표를 하나로 묶으면 순위가 바뀐다 — 그게 이 장의 요점이다.
#
# 필요 패키지: plotly, kaleido (정적 PNG 저장용)

# %%
def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1. 비용 모델 상수
#
# 「문서 8편을 읽고 보고서 한 장을 쓴다」는 **똑같은 작업**을
# 여섯 가지 연결 방식으로 돌린다. 작업이 같으니 읽어야 하는 양도 같다.
# 달라지는 것은 *언제 무엇을 몇 번 하는가* 뿐이다.

# %%
DOCS = 8
READ_MS, READ_TOK = 900, 2_400        # 문서 한 편 읽기
WRITE_MS, WRITE_TOK = 1_800, 3_200    # 보고서 한 장 쓰기
CHECK_MS, CHECK_TOK = 700, 1_100      # 검토 한 번
ROUTE_MS, ROUTE_TOK = 300, 400        # 라우팅 판단 한 번
PAR = 4                               # 동시에 돌릴 수 있는 수

print(f"문서 {DOCS}편, 동시 폭 {PAR}, 물결 수 {-(-DOCS // PAR)}")
# 출력: 문서 8편, 동시 폭 4, 물결 수 2


# %% [markdown]
# ## 2. 여섯 위상
#
# | 위상 | 다른 이름 | 무엇이 붙는가 |
# |---|---|---|
# | 경로 | 파이프라인 | 아무것도. 한 줄로 죽 이어진다 |
# | 이분·합류 | 팬아웃-팬인 | 동시성. 토큰은 그대로 |
# | 성형 | 감독자-작업자 | 물결마다 라우팅 판단 |
# | 순환 | 생성-검증, 평가자-최적화 | 쓰기+검토를 3회 반복 |
# | 동적 엣지 | 라우터 | 앞단에 판단 1회 |
# | 트리 | 계층적 위임 | 중간 관리자의 부분 보고서 |

# %%
def 경로():
    """파이프라인. 한 줄로 죽 이어진다."""
    ms = DOCS * READ_MS + WRITE_MS
    tok = DOCS * READ_TOK + WRITE_TOK
    return ms, tok, 0.71, "단순. 느리다."


def 이분합류():
    """팬아웃-팬인. 문서를 나눠 읽고 합친다."""
    waves = -(-DOCS // PAR)
    ms = waves * READ_MS + WRITE_MS
    tok = DOCS * READ_TOK + WRITE_TOK
    return ms, tok, 0.71, "빠르다. 토큰은 같다."


def 성형():
    """감독자-작업자. 감독자가 매번 다음 일을 정한다."""
    waves = -(-DOCS // PAR)
    ms = waves * (ROUTE_MS + READ_MS) + ROUTE_MS + WRITE_MS
    tok = (waves + 1) * ROUTE_TOK + DOCS * READ_TOK + WRITE_TOK
    return ms, tok, 0.78, "판단이 붙는다. 감독자가 병목."


def 순환():
    """생성-검증. 검토가 통과할 때까지 돈다(여기서는 3회)."""
    rounds = 3
    waves = -(-DOCS // PAR)
    ms = waves * READ_MS + rounds * (WRITE_MS + CHECK_MS)
    tok = DOCS * READ_TOK + rounds * (WRITE_TOK + CHECK_TOK)
    return ms, tok, 0.89, "품질이 오른다. 값이 비싸다."


def 동적엣지():
    """라우터. 문서 종류를 보고 다른 처리기로 보낸다."""
    waves = -(-DOCS // PAR)
    ms = ROUTE_MS + waves * READ_MS + WRITE_MS
    tok = ROUTE_TOK + DOCS * READ_TOK + WRITE_TOK
    return ms, tok, 0.81, "쉬운 건 싸게, 어려운 건 비싸게."


def 트리():
    """계층적 위임. 중간 관리자가 부분 보고서를 만든다."""
    groups = 2
    per = DOCS // groups
    ms = (ROUTE_MS + (-(-per // PAR)) * READ_MS + WRITE_MS) + WRITE_MS
    tok = groups * (ROUTE_TOK + per * READ_TOK + WRITE_TOK) + WRITE_TOK
    return ms, tok, 0.84, "부분 요약이 남는다. 중간 손실도."


TOPOLOGIES = (
    ("경로", 경로),
    ("이분·합류", 이분합류),
    ("성형", 성형),
    ("순환", 순환),
    ("동적 엣지", 동적엣지),
    ("트리", 트리),
)

# %% [markdown]
# ## 3. 표로 나란히 놓기
#
# 마지막 칸이 이 카드의 핵심이다. 효율은
# $q/\text{tok}\times 10^4$ 로, "토큰 1만 개를 써서 사는 품질"이다.

# %%
rows = []
for name, fn in TOPOLOGIES:
    ms, tok, q, note = fn()
    rows.append({
        "위상": name, "지연": ms, "토큰": tok, "품질": q,
        "효율": q / tok * 10_000, "성격": note,
    })

hdr = f"{'위상':<11}{'지연(ms)':>10}{'토큰':>9}{'품질':>7}{'토큰당 품질':>13}"
print(hdr)
print("-" * 52)
for r in rows:
    print(f"{r['위상']:<11}{r['지연']:>10,}{r['토큰']:>9,}"
          f"{r['품질']:>7.2f}{r['효율']:>13.3f}")
# 출력: 위상          지연(ms)     토큰   품질   토큰당 품질
# 출력: ----------------------------------------------------
# 출력: 경로             9,000   22,400   0.71        0.317
# 출력: 이분·합류         3,600   22,400   0.71        0.317
# 출력: 성형             4,500   23,600   0.78        0.331
# 출력: 순환             9,300   32,100   0.89        0.277
# 출력: 동적 엣지         3,900   22,800   0.81        0.355
# 출력: 트리             4,800   29,600   0.84        0.284
# 출력: (한글 폭 때문에 열이 눈으로는 조금 밀려 보인다. 값은 위와 같다.)


# %% [markdown]
# ## 4. 1등이 서로 다르다
#
# 「좋은 위상」은 없다. 제일 빠른 것, 제일 싼 것, 품질 1등이 전부 다르다.

# %%
fast = min(rows, key=lambda r: r["지연"])
cheap = min(rows, key=lambda r: r["토큰"])
best = max(rows, key=lambda r: r["품질"])
eff = max(rows, key=lambda r: r["효율"])

print(f"제일 빠른 것   {fast['위상']}   ({fast['지연']:,}ms)")
print(f"제일 싼 것     {cheap['위상']}   ({cheap['토큰']:,} 토큰)")
print(f"품질 1등       {best['위상']}   (q={best['품질']:.2f})")
print(f"효율 1등       {eff['위상']}   ({eff['효율']:.3f})")
# 출력: 제일 빠른 것   이분·합류   (3,600ms)
# 출력: 제일 싼 것     경로   (22,400 토큰)
# 출력: 품질 1등       순환   (q=0.89)
# 출력: 효율 1등       동적 엣지   (0.355)


# %% [markdown]
# ## 5. 순위 뒤집힘
#
# 품질 내림차순 순위와 효율 내림차순 순위를 나란히 놓는다.
# 순환이 **1위 → 6위(꼴찌)** 로 떨어진다. 5칸 낙차다.

# %%
by_q = sorted(rows, key=lambda r: -r["품질"])
by_e = sorted(rows, key=lambda r: -r["효율"])
rank_q = {r["위상"]: i + 1 for i, r in enumerate(by_q)}
rank_e = {r["위상"]: i + 1 for i, r in enumerate(by_e)}

print(f"{'위상':<11}{'품질순위':>9}{'효율순위':>9}{'낙차':>7}")
print("-" * 36)
for r in by_q:
    n = r["위상"]
    print(f"{n:<11}{rank_q[n]:>9}{rank_e[n]:>9}{rank_e[n] - rank_q[n]:>+7}")
# 출력: 위상          품질순위    효율순위    낙차
# 출력: ------------------------------------
# 출력: 순환                1        6     +5
# 출력: 트리                2        5     +3
# 출력: 동적 엣지            3        1     -2
# 출력: 성형                4        2     -2
# 출력: 경로                5        3     -2
# 출력: 이분·합류            6        4     -2


# %% [markdown]
# ## 6. 순환은 품질을 «돈으로 산» 것이다
#
# 기준선(이분·합류)과 비교해서, 품질 1%p 를 올리는 데 든 토큰을 센다.
#
# $$\text{추가 토큰당 품질} = \frac{\Delta q}{\Delta \text{tok}}$$

# %%
base = next(r for r in rows if r["위상"] == "이분·합류")
print(f"기준선: {base['위상']}  q={base['품질']:.2f}, tok={base['토큰']:,}\n")
print(f"{'위상':<11}{'Δ품질':>8}{'Δ토큰':>9}{'품질 1%p 값(토큰)':>19}")
print("-" * 47)
for r in rows:
    dq = r["품질"] - base["품질"]
    dt = r["토큰"] - base["토큰"]
    if dq <= 0:
        print(f"{r['위상']:<11}{dq:>+8.2f}{dt:>+9,}{'-':>19}")
    else:
        print(f"{r['위상']:<11}{dq:>+8.2f}{dt:>+9,}{dt / (dq * 100):>19,.0f}")
# 출력: 기준선: 이분·합류  q=0.71, tok=22,400
# 출력:
# 출력: 위상            Δ품질     Δ토큰    품질 1%p 값(토큰)
# 출력: -----------------------------------------------
# 출력: 경로            +0.00       +0                  -
# 출력: 이분·합류        +0.00       +0                  -
# 출력: 성형            +0.07   +1,200                171
# 출력: 순환            +0.18   +9,700                539
# 출력: 동적 엣지        +0.10     +400                 40
# 출력: 트리            +0.13   +7,200                554
# 출력: → 순환은 품질 1%p 를 사는 데 539 토큰을 쓴다. 동적 엣지(40)의 13배다.


# %% [markdown]
# ## 7. 병렬은 시간을 사는 것이지 돈을 아끼는 게 아니다
#
# 경로와 이분·합류는 **토큰이 완전히 같다** (22,400). 지연만 9,000 → 3,600 이다.
# 나눠 읽는다고 읽는 양이 줄지는 않으니까.

# %%
p = next(r for r in rows if r["위상"] == "경로")
f = next(r for r in rows if r["위상"] == "이분·합류")
print(f"토큰 차이 {f['토큰'] - p['토큰']:,}  (같다)")
print(f"지연 차이 {f['지연'] - p['지연']:,}ms  "
      f"({p['지연'] / f['지연']:.2f}배 빠름)")
# 출력: 토큰 차이 0  (같다)
# 출력: 지연 차이 -5,400ms  (2.50배 빠름)


# %% [markdown]
# ## 8. 시각화
#
# 왼쪽: 품질 막대(순환 1등). 가운데: 토큰 막대(순환 꼴찌).
# 오른쪽: 효율 막대(순환 꼴찌). 아래: 토큰-품질 산점도에
# 등효율선을 얹어서, 순환이 「선 아래」에 있다는 것을 보인다.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

names = [r["위상"] for r in rows]
HI, LO, MID = "#d62728", "#7f7f7f", "#1f77b4"


def bars(vals, hi_is_good):
    tgt = max(vals) if hi_is_good else min(vals)
    return [HI if v == tgt else LO for v in vals]


fig = make_subplots(
    rows=2, cols=3,
    specs=[[{}, {}, {}], [{"colspan": 3}, None, None]],
    row_heights=[0.42, 0.58], vertical_spacing=0.16,
    subplot_titles=("품질 (높을수록 좋다)", "토큰 (낮을수록 좋다)",
                    "토큰당 품질 ×10⁴", "토큰 대비 품질 — 등효율선 위/아래"),
)

qs = [r["품질"] for r in rows]
ts = [r["토큰"] for r in rows]
es = [r["효율"] for r in rows]

fig.add_bar(x=names, y=qs, marker_color=bars(qs, True),
            text=[f"{v:.2f}" for v in qs], textposition="outside",
            showlegend=False, row=1, col=1)
fig.add_bar(x=names, y=ts, marker_color=bars(ts, True),  # 최대=최악을 빨강
            text=[f"{v:,}" for v in ts], textposition="outside",
            showlegend=False, row=1, col=2)
fig.add_bar(x=names, y=es, marker_color=[HI if v == min(es) else LO for v in es],
            text=[f"{v:.3f}" for v in es], textposition="outside",
            showlegend=False, row=1, col=3)

# 등효율선: q = k * tok
for k, dash in ((max(es), "dash"), (min(es), "dot")):
    xs = [20_000, 34_000]
    fig.add_scatter(x=xs, y=[k * x / 10_000 for x in xs], mode="lines",
                    line=dict(color="#bbbbbb", dash=dash, width=1),
                    name=f"등효율 {k:.3f}", row=2, col=1)

fig.add_scatter(
    x=ts, y=qs, mode="markers+text", text=names,
    # 경로와 이분·합류는 좌표가 완전히 같다(토큰 22,400 / 품질 0.71).
    # 라벨이 겹치니 한쪽만 아래로 내린다. «점이 겹친다»가 곧 결론이다.
    textposition=["bottom center" if n == "경로" else "top center"
                  for n in names],
    marker=dict(size=[20 if n == "순환" else 12 for n in names],
                color=[HI if n == "순환" else MID for n in names],
                line=dict(width=1, color="white")),
    name="위상", row=2, col=1,
)

fig.update_yaxes(title_text="품질", range=[0, 1.05], row=1, col=1)
fig.update_yaxes(title_text="토큰", range=[0, 37_000], row=1, col=2)
fig.update_yaxes(title_text="효율", range=[0, 0.42], row=1, col=3)
fig.update_xaxes(title_text="총 토큰", row=2, col=1)
fig.update_yaxes(title_text="품질", range=[0.6, 0.98], row=2, col=1)
fig.update_layout(
    title_text="여섯 위상 — 품질 1등(순환)은 효율 꼴찌다",
    height=760, width=1080, template="plotly_white",
    legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"),
)

_show(fig)

import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(OUT, scale=2)
print(f"저장: {OUT}")
# 출력: 저장: .../35a721fa-4905-45b4-922a-a0adb36edcaa/expy.png


# %% [markdown]
# ## 9. 정리 — 고르는 순서
#
# 순환은 품질 0.89 로 1등이지만 토큰 32,100 으로 꼴찌고,
# 토큰당 품질 0.277 로도 꼴찌다. **품질을 돈으로 산 것이지
# 공짜로 얻은 게 아니다.**
#
# 그래서 위상은 「좋은 것」을 고르는 게 아니라 제약에서 거꾸로 고른다.
#
# 1. 품질 하한이 있나 → 있으면 순환을 넣는다 (토큰을 내준다)
# 2. 지연 상한이 있나 → 있으면 이분·합류로 편다 (토큰은 그대로)
# 3. 입력 종류가 갈리나 → 갈리면 동적 엣지 (품질 조금 내주고 토큰 크게 아낀다)
# 4. 다 아니면 경로. 제일 단순한 게 제일 오래 산다.

# %%
print("품질 1등:", best["위상"], f"(q={best['품질']:.2f})")
print("그 대가 :", f"토큰 {best['토큰']:,} — 6위(최다), "
      f"토큰당 품질 {best['효율']:.3f} — {rank_e[best['위상']]}위(최하)")
# 출력: 품질 1등: 순환 (q=0.89)
# 출력: 그 대가 : 토큰 32,100 — 6위(최다), 토큰당 품질 0.277 — 6위(최하)
