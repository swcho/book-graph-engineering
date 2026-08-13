# %% [markdown]
# # 페이지랭크의 싱크 노드 — 점수는 어디로 새는가
#
# **질문**: 페이지랭크에서 싱크 노드는 어떤 문제를 일으키는가?
#
# **답**: 점수를 **받기만 하고 흘려보내지 않아** 매 회 점수가 새어 나간다.
# 순위는 잘 안 바뀌어 발견이 늦지만, **절대 임계**를 쓰고 있다면 그 임계가 조용히 의미를 잃는다.
#
# 이 스크립트는 10장 `ex2_pagerank.py` 의 `REPORTS` 그래프(누가 누구에게 결재를 올리는가)로
# 그 «샘»을 한 회씩 눈으로 따라간다.

# %%
# 필요 패키지: plotly, kaleido  (핵심 계산은 표준 라이브러리만 사용)
from collections import defaultdict


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# 10장 org.py 의 REPORTS — 유향 그래프. (부하) -> (상사)
REPORTS = [
    ("개발1", "김개발"), ("개발2", "김개발"), ("개발3", "김개발"),
    ("개발4", "김개발"), ("개발5", "김개발"), ("개발6", "김개발"),
    ("한영업", "정영업"), ("오영업", "정영업"), ("서영업", "정영업"),
    ("윤디자", "강디자"), ("임디자", "강디자"),
    ("김개발", "대표"), ("정영업", "대표"), ("강디자", "대표"),
    ("공장A", "서영업"), ("공장B", "공장A"), ("공장C", "공장A"),
    ("청소담당", "총무"), ("총무", "대표"),
]

NODES = sorted({x for a, b in REPORTS for x in (a, b)})
OUT = defaultdict(list)
for a, b in REPORTS:
    OUT[a].append(b)

SINKS = [v for v in NODES if not OUT[v]]
print("노드 수:", len(NODES))
print("싱크 노드(나가는 엣지가 0개):", SINKS)
# 출력: 노드 수: 20
# 출력: 싱크 노드(나가는 엣지가 0개): ['대표']
# → 결재선의 꼭대기. 대표는 아무에게도 결재를 올리지 않는다.

# %% [markdown]
# ## 1. 페이지랭크 한 회의 정의
#
# 감쇠 계수 $d = 0.85$ 일 때 표준 갱신식은
#
# $$ PR_{t+1}(v) \;=\; \frac{1-d}{N} \;+\; d \sum_{u \to v} \frac{PR_t(u)}{|\text{out}(u)|} $$
#
# 여기에는 조용한 가정이 하나 있다. **모든 노드가 자기 점수를 전부 내보낸다**는 가정이다.
# 그 가정이 참이면 전체 합이 보존된다.
#
# $$ \sum_v PR_{t+1}(v) = (1-d) + d\sum_u PR_t(u) = (1-d) + d\cdot 1 = 1 $$
#
# 그런데 $|\text{out}(u)| = 0$ 인 싱크 노드(dangling node)는 안쪽 합에 **아예 등장하지 않는다**.
# 그 노드가 들고 있던 점수 $PR_t(u)$ 는 다음 회로 넘어가지 못하고 사라진다.
#
# $$ \sum_v PR_{t+1}(v) \;=\; (1-d) \;+\; d\Big(S_t - \underbrace{\textstyle\sum_{u \in \text{sink}} PR_t(u)}_{\text{샌 양}}\Big) $$
#
# 랜덤 워커 비유로는, 막다른 웹페이지에 도착한 서퍼가 **그냥 증발해 버리는** 모형이다.

# %%
D = 0.85
TOL = 1e-12


def pagerank(edges, damping=D, fix_sinks=True, rounds=200, trace=False, stop_tol=TOL):
    """fix_sinks=False 면 싱크 보정을 끈다 — 즉 «샘»을 그대로 둔다.
    stop_tol=0 이면 조기 종료 없이 rounds 회를 다 돌아 회차별 기록을 남긴다."""
    nodes = sorted({x for a, b in edges for x in (a, b)})
    out = defaultdict(list)
    for a, b in edges:
        out[a].append(b)
    n = len(nodes)
    rank = {v: 1 / n for v in nodes}
    sinks = [v for v in nodes if not out[v]]
    history = [sum(rank.values())]

    for it in range(rounds):
        nxt = {v: (1 - damping) / n for v in nodes}
        leaked = sum(rank[v] for v in sinks) if fix_sinks else 0.0
        for v in nodes:
            if out[v]:
                share = damping * rank[v] / len(out[v])
                for w in out[v]:
                    nxt[w] += share
        if fix_sinks:                       # 샌 점수를 전 노드에 고루 되돌린다
            for v in nodes:
                nxt[v] += damping * leaked / n
        diff = sum(abs(nxt[v] - rank[v]) for v in nodes)
        rank = nxt
        history.append(sum(rank.values()))
        if diff < stop_tol:
            break
    return (rank, it + 1, history) if trace else (rank, it + 1, sum(rank.values()))


rank_fix, it_fix, sum_fix = pagerank(REPORTS, fix_sinks=True)
rank_bad, it_bad, sum_bad = pagerank(REPORTS, fix_sinks=False)

# 회차별 기록은 조기 종료를 끄고 따로 뽑는다.
STEPS = 16
_, _, hist_fix = pagerank(REPORTS, fix_sinks=True, rounds=STEPS, trace=True, stop_tol=0.0)
_, _, hist_bad = pagerank(REPORTS, fix_sinks=False, rounds=STEPS, trace=True, stop_tol=0.0)

print(f"[보정 함]     반복 {it_fix:>3}회  최종 합계 {sum_fix:.6f}")
print(f"[보정 안 함]  반복 {it_bad:>3}회  최종 합계 {sum_bad:.6f}")
# 출력: [보정 함]     반복  68회  최종 합계 1.000000
# 출력: [보정 안 함]  반복   6회  최종 합계 0.374054

# %%
# 회차별로 합계가 어떻게 빠지는지 본다.
print(f"{'회차':>4} {'보정 함':>12} {'보정 안 함':>12} {'그 회에 샌 양':>14}")
print("-" * 46)
for i in range(0, 9):
    leak = "" if i == 0 else f"{hist_bad[i - 1] - hist_bad[i]:>14.6f}"
    print(f"{i:>4} {hist_fix[i]:>12.6f} {hist_bad[i]:>12.6f} {leak}")
# 출력:   회차         보정 함       보정 안 함       그 회에 샌 양
# 출력: ----------------------------------------------
# 출력:    0     1.000000     1.000000
# 출력:    1     1.000000     0.957500       0.042500
# 출력:    2     1.000000     0.813000       0.144500
# 출력:    3     1.000000     0.444525       0.368475
# 출력:    4     1.000000     0.418425       0.026100
# 출력:    5     1.000000     0.374054       0.044371
# 출력:    6     1.000000     0.374054       0.000000
# 출력:    7     1.000000     0.374054       0.000000
# 출력:    8     1.000000     0.374054       0.000000
#
# 이 그래프는 결재선이라 사이클이 없는 DAG 다. 그래서 «보정 안 함» 쪽은
# 6회 만에 딱 멈춘다 — 점수가 조직도 깊이만큼 위로 올라가 대표에게서 증발하고 끝.
# 3회차에 0.368 이 한꺼번에 빠지는 건 팀장들이 모은 점수가 대표에게 도착한 회차다.

# %% [markdown]
# ## 2. 손으로 검산할 수 있는 최소 예제
#
# 사슬 $A \to B \to C$ 에서 $C$ 만 싱크다. $N=3$, $d=0.85$.
#
# 보정을 끄면 수렴값은 손으로 바로 나온다. $A$ 는 들어오는 엣지가 없으므로
#
# $$ PR(A) = \tfrac{1-d}{3} = 0.05,\quad
#    PR(B) = 0.05 + 0.85 \cdot 0.05 = 0.0925,\quad
#    PR(C) = 0.05 + 0.85 \cdot 0.0925 = 0.1286 $$
#
# 합계는 $0.2711$. 1.0 이어야 할 확률분포가 27% 만 남았다.

# %%
CHAIN = [("A", "B"), ("B", "C")]
r_bad, _, s_bad = pagerank(CHAIN, fix_sinks=False)
r_fix, _, s_fix = pagerank(CHAIN, fix_sinks=True)
for v in ("A", "B", "C"):
    print(f"  {v}   보정 안 함 {r_bad[v]:.4f}   보정 함 {r_fix[v]:.4f}")
print(f"  합계 보정 안 함 {s_bad:.4f} / 보정 함 {s_fix:.4f}")
# 출력:   A   보정 안 함 0.0500   보정 함 0.1844
# 출력:   B   보정 안 함 0.0925   보정 함 0.3412
# 출력:   C   보정 안 함 0.1286   보정 함 0.4744
# 출력:   합계 보정 안 함 0.2711 / 보정 함 1.0000

# %% [markdown]
# ## 3. 순위는 왜 «잘 안 바뀌는가»
#
# 「잘 안 바뀐다」보다 강한 말을 할 수 있다. 이 보정 방식에서는 **순위가 아예 안 바뀐다.**
# 두 반복식의 고정점을 나란히 써 보면 이유가 보인다. $M$ 을 전이 행렬, $e$ 를 1 벡터라 하면
#
# $$ r_{\text{샘}} = \tfrac{1-d}{N} e + d M\, r_{\text{샘}}, \qquad
#    r_{\text{보정}} = \Big(\tfrac{1-d}{N} + \tfrac{d L}{N}\Big) e + d M\, r_{\text{보정}} $$
#
# ($L$ 은 싱크가 들고 있는 질량. 고정점에서는 그냥 **상수**다.)
# 둘 다 $r = \alpha (I - dM)^{-1} e$ 꼴이고 $\alpha$ 만 다르다. 즉
#
# $$ r_{\text{샘}} = \Big(\textstyle\sum_v r_{\text{샘}}(v)\Big)\; r_{\text{보정}} $$
#
# **모든 노드가 똑같은 배율로 줄어든다.** 그래서 정렬 결과가 완전히 일치한다.
# 발견이 늦는 이유가 바로 이것 — 대시보드의 «Top 10» 은 티끌만큼도 안 이상해 보인다.

# %%
order_fix = sorted(NODES, key=lambda v: -rank_fix[v])
order_bad = sorted(NODES, key=lambda v: -rank_bad[v])

print(f"{'순위':>4} {'보정 함':<10}{'점수':>8}   {'보정 안 함':<10}{'점수':>8}   {'비율':>7}")
print("-" * 58)
for i in range(8):
    a, b = order_fix[i], order_bad[i]
    print(f"{i+1:>4} {a:<10}{rank_fix[a]:>8.4f}   {b:<10}{rank_bad[b]:>8.4f}   "
          f"{rank_bad[b] / rank_fix[a]:>7.3f}")

same = sum(1 for i in range(len(NODES)) if order_fix[i] == order_bad[i])
print(f"\n순위가 그대로인 자리: {same}/{len(NODES)}")
# 출력:   순위 보정 함            점수   보정 안 함          점수        비율
# 출력: ----------------------------------------------------------
# 출력:    1 대표          0.2953   대표          0.1105     0.374
# 출력:    2 김개발         0.1223   김개발         0.0458     0.374
# 출력:    3 정영업         0.1103   정영업         0.0413     0.374
# 출력:    4 서영업         0.0661   서영업         0.0247     0.374
# 출력:    5 강디자         0.0541   강디자         0.0203     0.374
# 출력:    6 공장A         0.0541   공장A         0.0203     0.374
# 출력:    7 총무          0.0371   총무          0.0139     0.374
# 출력:    8 개발1         0.0201   개발1         0.0075     0.374
# 출력:
# 출력: 순위가 그대로인 자리: 20/20
#
# 비율 열이 전부 0.374 — 예측대로 «똑같은 배율»이다.

# %%
# 위 주장을 수치로 확인: 새어 나간 벡터를 합계로 나누면 보정판과 정확히 같은가?
gap = max(abs(rank_bad[v] / sum_bad - rank_fix[v]) for v in NODES)
print(f"max |rank_bad/합계 - rank_fix| = {gap:.3e}")
# 출력: max |rank_bad/합계 - rank_fix| = 1.498e-13
# → 부동소수점 오차 수준. 정확히 비례한다.

# %% [markdown]
# ## 4. 그런데 절대 임계는 조용히 무너진다
#
# 「점수 0.05 이상이면 핵심 인물로 보고한다」 같은 **절댓값 규칙**을 박아 두었다면,
# 전체 질량이 절반으로 줄어든 순간 그 규칙은 다른 뜻이 된다.
# 코드는 안 바뀌었고, 예외도 안 나고, 순위표도 그대로다. 규칙만 의미를 잃었다.

# %%
for thr in (0.10, 0.05, 0.02):
    a = [v for v in NODES if rank_fix[v] >= thr]
    b = [v for v in NODES if rank_bad[v] >= thr]
    print(f"임계 {thr:.2f}  보정 함 {len(a):>2}명 {a}")
    print(f"           보정 안 함 {len(b):>2}명 {b}")
# 출력: 임계 0.10  보정 함  3명 ['김개발', '대표', '정영업']
# 출력:            보정 안 함  1명 ['대표']
# 출력: 임계 0.05  보정 함  6명 ['강디자', '공장A', '김개발', '대표', '서영업', '정영업']
# 출력:            보정 안 함  1명 ['대표']
# 출력: 임계 0.02  보정 함 20명 ['강디자', '개발1', ... , '총무', '한영업']   (전원)
# 출력:            보정 안 함  6명 ['강디자', '공장A', '김개발', '대표', '서영업', '정영업']
#
# 「0.05 이상을 핵심 인물로 본다」는 규칙이 6명 → 1명이 된다.
# 순위표는 완벽히 동일한데 보고 대상만 조용히 사라진다.

# %% [markdown]
# ## 5. 보정하는 방법 세 가지
#
# 1. **되돌리기(가장 흔함)** — 싱크가 들고 있던 질량을 모든 노드에 $1/N$ 로 재분배한다.
#    위 코드의 `fix_sinks=True` 가 이것. 수학적으로는 싱크 노드에서 전체로 가는
#    가상 엣지를 그어 준 것과 같다.
# 2. **자기 루프** — 싱크에 $v \to v$ 를 달아 질량을 붙잡아 둔다. 싱크 점수가 부풀려진다.
# 3. **끝에 정규화** — 새는 대로 두고 마지막에 합계로 나눈다. 3절에서 확인했듯
#    균등 되돌리기와 **결과가 정확히 같다**. 다만 반복 도중의 합계로는 수렴 판정을
#    못 하고, 개인화 벡터가 균등하지 않으면 1번과 갈라진다.
#
# 실무 확인법은 단순하다. **점수 합계를 찍어 보고 1.0 인지 본다.**
# NetworkX 등 주요 구현은 대부분 되돌리기를 하지만, 직접 짠 코드나
# 일부 그래프 DB 내장 함수는 안 하는 경우가 있다.

# %%
# 임계 감시용 자가진단 한 줄
def assert_no_leak(rank, tol=1e-6):
    s = sum(rank.values())
    return f"합계 {s:.6f} — {'정상' if abs(s - 1.0) < tol else '샘 발생! 절대 임계 재검토 필요'}"


print("보정 함   :", assert_no_leak(rank_fix))
print("보정 안 함:", assert_no_leak(rank_bad))
# 출력: 보정 함   : 합계 1.000000 — 정상
# 출력: 보정 안 함: 합계 0.374054 — 샘 발생! 절대 임계 재검토 필요

# %% [markdown]
# ## 6. 시각화
#
# 왼쪽: 회차별 전체 점수 합계. 보정을 끄면 1.0 에서 미끄러져 내려가 다른 값에 눌러앉는다.
# 오른쪽: 상위 노드의 점수. 막대 높이만 낮아지고 **순서는 그대로**라 눈치채기 어렵다.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

top = order_fix[:8]
steps = min(len(hist_fix), len(hist_bad))

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=("회차별 점수 합계 (질량 보존)", "상위 8명 점수 — 순서는 그대로"),
)
fig.add_trace(go.Scatter(x=list(range(steps)), y=hist_fix[:steps], name="싱크 보정 함",
                         mode="lines+markers", line=dict(color="#2E86C1", width=3)), row=1, col=1)
fig.add_trace(go.Scatter(x=list(range(steps)), y=hist_bad[:steps], name="싱크 보정 안 함",
                         mode="lines+markers", line=dict(color="#C0392B", width=3)), row=1, col=1)
fig.add_hline(y=1.0, line=dict(color="gray", dash="dot"), row=1, col=1)

fig.add_trace(go.Bar(x=top, y=[rank_fix[v] for v in top], name="보정 함",
                     marker_color="#2E86C1", showlegend=False), row=1, col=2)
fig.add_trace(go.Bar(x=top, y=[rank_bad[v] for v in top], name="보정 안 함",
                     marker_color="#C0392B", showlegend=False), row=1, col=2)
# 절대 임계선 — 오른쪽 서브플롯 축을 명시적으로 참조해야 확실히 그려진다.
fig.add_shape(type="line", xref="x2", yref="y2", x0=-0.5, x1=len(top) - 0.5,
              y0=0.05, y1=0.05, line=dict(color="#E67E22", dash="dash", width=2))
fig.add_annotation(xref="x2", yref="y2", x=len(top) - 0.6, y=0.078,
                   text="절대 임계 0.05  ← 파랑 6명 / 빨강 1명", showarrow=False,
                   xanchor="right", font=dict(color="#B9770E", size=13))

fig.update_xaxes(title_text="반복 회차", row=1, col=1)
fig.update_yaxes(title_text="점수 합계", range=[0, 1.12], row=1, col=1)
fig.update_yaxes(title_text="페이지랭크 점수", row=1, col=2)
fig.update_layout(title=dict(text="싱크 노드가 삼키는 점수 — 합계는 새고, 순위는 안 바뀐다",
                             x=0.02, y=0.96, font=dict(size=19)),
                  height=480, width=1150, barmode="group",
                  margin=dict(t=95, b=60),
                  legend=dict(x=0.13, y=0.60, bgcolor="rgba(255,255,255,0.85)",
                              bordercolor="#BBBBBB", borderwidth=1))

_show(fig)
fig.write_image("expy.png", scale=2)
print("saved expy.png")
# 출력: saved expy.png
