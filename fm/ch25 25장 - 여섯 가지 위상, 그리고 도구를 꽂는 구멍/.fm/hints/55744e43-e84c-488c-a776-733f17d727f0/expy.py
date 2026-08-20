# %% [markdown]
# # 라우팅 정확도가 100%여도 품질이 오르지 않은 이유
#
# **질문** 라우팅 정확도가 100%여도 품질이 오르지 않은 이유는 무엇인가?
#
# **답** 정밀한 길이 굳이 필요 없는 입력에도 0.88을 내어 빠른 길의 0.86보다 높다.
# 이 설정에서는 정밀한 길이 언제나 품질로 이긴다.
#
# 이 노트북은 `content/ch25/code/ex3_router.py` 의 품질·토큰 모델을 그대로 재현하고,
# 라우터 정확도 $a$ 를 $0 \to 1$ 로 훑으며
#
# - 품질 곡선 $Q(a)$ 와 토큰 곡선 $C(a)$
# - 「전부 정밀한 길」 기준선과의 격차 (= 천장)
# - 품질 1%p 를 내주고 아끼는 토큰, 즉 **교환비**
#
# 를 계산합니다. 핵심 구조는 **지배 전략(dominance)** 입니다.
# 정밀한 경로가 *모든* 입력 종류에서 품질 우위이면, 라우팅은 품질을 올리는 장치가 될 수 없습니다.

# %%
# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# 실행: python3 expy.py   /  VSCode 셀로도 그대로 돌아간다.

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


HERE = os.path.dirname(os.path.abspath(__file__))
print("준비 완료")
# 출력: 준비 완료

# %% [markdown]
# ## 1. ex3_router.py 의 모델을 그대로 옮긴다
#
# 길이 두 개뿐입니다. 각 길에는 숫자가 셋 붙습니다.
#
# | 길 | 비용 $c$ | 「맞을 때」 품질 $r$ | 「틀린 길로 왔을 때」 품질 $w$ |
# |---|---|---|---|
# | 빠른 길 | 1,200 | 0.86 | 0.42 |
# | 정밀한 길 | 7,400 | 0.93 | **0.88** |
#
# 굵게 표시한 **0.88** 이 이 카드의 답 전체입니다.
# 「정밀한 길로 굳이 안 보내도 되는 입력」을 정밀한 길로 보냈을 때의 품질이 0.88 이고,
# 이 값이 빠른 길이 *제대로* 맞았을 때의 0.86 보다 **높습니다**.

# %%
# 길 이름     비용   이 길이 «맞을 때» 품질   «틀린 길로 왔을 때» 품질
ROUTES = {
    "빠른 길":   (1_200, 0.86, 0.42),
    "정밀한 길": (7_400, 0.93, 0.88),
}
MIX = {"빠른 길": 0.72, "정밀한 길": 0.28}   # 실제 입력의 분포
N = 1_000

FAST, PREC = "빠른 길", "정밀한 길"


def other(k):
    return PREC if k == FAST else FAST


def all_precise():
    """모든 입력을 정밀한 길로. 라우터가 없다."""
    cost = N * ROUTES[PREC][0]
    q = sum(MIX[k] * (ROUTES[PREC][1] if k == PREC else ROUTES[PREC][2]) for k in MIX)
    return cost, q


def routed(acc):
    """정확도 acc 인 라우터를 태운다."""
    cost = q = 0.0
    for true_route, share in MIX.items():
        n = N * share
        for taken, p in ((true_route, acc), (other(true_route), 1 - acc)):
            c, right, wrong = ROUTES[taken]
            cost += n * p * c
            q += share * p * (right if taken == true_route else wrong)
    return cost, q


PC, PQ = all_precise()
print(f"전부 정밀한 길 : 토큰 {PC:>10,.0f}   품질 {PQ:.4f}")
c100, q100 = routed(1.00)
print(f"라우팅 100%    : 토큰 {c100:>10,.0f}   품질 {q100:.4f}")
print(f"→ 정확도가 «완벽»한데도 품질이 {PQ - q100:+.4f} ({(q100 - PQ) * 100:+.2f}%p) 움직였다.")
# 출력: 전부 정밀한 길 : 토큰  7,400,000   품질 0.8940
# 출력: 라우팅 100%    : 토큰  2,936,000   품질 0.8796
# 출력: → 정확도가 «완벽»한데도 품질이 +0.0144 (-1.44%p) 움직였다.

# %% [markdown]
# ## 2. 지배(dominance) — 진짜 원인은 표 한 칸이다
#
# 라우팅이 품질을 올릴 수 있는 조건은 하나입니다.
# **어떤 입력 종류에서는 빠른 길이 정밀한 길보다 품질이 좋아야** 합니다.
# 그래야 「그 입력만 빠른 길로 골라 보내면 품질이 오른다」가 성립합니다.
#
# 입력 종류 $t$, 선택한 길 $k$ 에 대한 품질 행렬을 $Q[t][k]$ 로 적으면
#
# $$
# Q[t][k] = \begin{cases} r_k & (k = t) \\ w_k & (k \neq t) \end{cases}
# $$
#
# 이 행렬을 열끼리 비교해서, 정밀한 길 열이 모든 행에서 크거나 같으면
# 정밀한 길은 **약지배 전략(weakly dominant strategy)** 입니다.

# %%
print("품질 행렬  Q[입력 종류][선택한 길]\n")
print(f"{'입력 종류':<12}{'빠른 길':>10}{'정밀한 길':>12}   승자")
print("-" * 52)
dominated = True
for t in MIX:
    row = {}
    for k in ROUTES:
        c, right, wrong = ROUTES[k]
        row[k] = right if k == t else wrong
    win = PREC if row[PREC] >= row[FAST] else FAST
    if row[PREC] < row[FAST]:
        dominated = False
    print(f"{t:<12}{row[FAST]:>10.2f}{row[PREC]:>12.2f}   {win}")
print()
print(f"정밀한 길이 모든 행에서 우위인가? → {dominated}")
print("→ 지배 전략이므로, 라우팅으로 «품질을» 개선할 여지가 애초에 0 이다.")
# 출력: 품질 행렬  Q[입력 종류][선택한 길]
# 출력:
# 출력: 입력 종류             빠른 길       정밀한 길   승자
# 출력: ----------------------------------------------------
# 출력: 빠른 길              0.86        0.88   정밀한 길
# 출력: 정밀한 길             0.42        0.93   정밀한 길
# 출력:
# 출력: 정밀한 길이 모든 행에서 우위인가? → True
# 출력: → 지배 전략이므로, 라우팅으로 «품질을» 개선할 여지가 애초에 0 이다.

# %% [markdown]
# ## 3. 닫힌 형태로 풀어 본다
#
# 정확도 $a$ 인 라우터의 평균 품질은 입력 종류별로 갈라서 쓰면
#
# $$
# Q(a) = \underbrace{0.72\,[\,a\cdot 0.86 + (1-a)\cdot 0.88\,]}_{\text{빠른 길이 정답인 72\%}}
#      + \underbrace{0.28\,[\,a\cdot 0.93 + (1-a)\cdot 0.42\,]}_{\text{정밀한 길이 정답인 28\%}}
# $$
#
# 정리하면
#
# $$
# Q(a) = 0.7512 + 0.1284\,a, \qquad
# C(a) = 5{,}664{,}000 - 2{,}728{,}000\,a
# $$
#
# 둘 다 $a$ 에 대해 **일차 함수**입니다. 여기서 두 가지를 읽습니다.
#
# 1. $Q'(a) = +0.1284 > 0$ 이므로 정확도를 올리면 품질은 **오릅니다**. 라우터를 잘 만드는 건 헛일이 아닙니다.
# 2. 그런데 $Q(1) = 0.8796 < 0.894 = Q_{\text{전부 정밀}}$ 입니다.
#    정확도를 100%까지 밀어붙여도 **천장이 기준선보다 낮습니다**.
#
# 첫째 항의 계수가 음수($-0.0144a$)라는 게 문제입니다.
# 「빠른 길이 정답인 72%」 구간에서는 라우터가 *맞출수록* 품질이 떨어집니다.

# %%
def q_closed(a):
    return 0.7512 + 0.1284 * a


def c_closed(a):
    return 5_664_000 - 2_728_000 * a


print(f"{'a':>6}{'Q(a) 시뮬':>12}{'Q(a) 닫힌형':>14}{'C(a) 시뮬':>14}{'C(a) 닫힌형':>15}")
print("-" * 62)
for a in (0.0, 0.5, 0.7, 1.0):
    c, q = routed(a)
    print(f"{a:>6.2f}{q:>12.4f}{q_closed(a):>14.4f}{c:>14,.0f}{c_closed(a):>15,.0f}")

# 항별 분해: 72% 구간과 28% 구간이 서로 반대 방향으로 움직인다
print("\n항별 분해 (정확도가 오를 때 각 구간의 기여)")
print(f"{'a':>6}{'72% 구간':>12}{'28% 구간':>12}{'합':>10}")
print("-" * 40)
for a in (0.0, 0.5, 1.0):
    t1 = 0.72 * (a * 0.86 + (1 - a) * 0.88)
    t2 = 0.28 * (a * 0.93 + (1 - a) * 0.42)
    print(f"{a:>6.2f}{t1:>12.4f}{t2:>12.4f}{t1 + t2:>10.4f}")
print("→ 72% 구간은 0.6336 → 0.6192 로 «내려간다». 맞출수록 손해다.")
# 출력:      a     Q(a) 시뮬      Q(a) 닫힌형       C(a) 시뮬       C(a) 닫힌형
# 출력: --------------------------------------------------------------
# 출력:   0.00      0.7512        0.7512     5,664,000      5,664,000
# 출력:   0.50      0.8154        0.8154     4,300,000      4,300,000
# 출력:   0.70      0.8411        0.8411     3,754,400      3,754,400
# 출력:   1.00      0.8796        0.8796     2,936,000      2,936,000
# 출력:
# 출력: 항별 분해 (정확도가 오를 때 각 구간의 기여)
# 출력:      a      72% 구간      28% 구간         합
# 출력: ----------------------------------------
# 출력:   0.00      0.6336      0.1176    0.7512
# 출력:   0.50      0.6264      0.1890    0.8154
# 출력:   1.00      0.6192      0.2604    0.8796
# 출력: → 72% 구간은 0.6336 → 0.6192 로 «내려간다». 맞출수록 손해다.

# %% [markdown]
# ## 4. 교환비 — 품질 1%p 에 토큰 몇 개인가
#
# 라우팅은 품질을 올리는 장치가 아니라 **교환**입니다. 그러면 환율을 재야 합니다.
#
# $$
# \text{교환비}(a) = \frac{C_{\text{전부 정밀}} - C(a)}{100 \cdot (Q_{\text{전부 정밀}} - Q(a))}
# \quad [\text{품질 } 1\%p \text{ 당 아끼는 토큰}]
# $$
#
# 이 값이 클수록 남는 장사입니다.

# %%
print(f"{'정확도':>8}{'총 토큰':>12}{'품질':>9}{'절감':>8}{'품질 손실':>11}{'1%p당 절감 토큰':>18}")
print("-" * 68)
for acc in (1.00, 0.95, 0.90, 0.80, 0.70, 0.50):
    c, q = routed(acc)
    dq = (PQ - q) * 100          # %p
    dc = PC - c
    rate = dc / dq if dq > 1e-12 else float("inf")
    print(f"{acc:>7.0%}{c:>12,.0f}{q:>9.3f}{1 - c / PC:>8.0%}"
          f"{dq:>10.2f}p{rate:>18,.0f}")
print("\n→ 100%에서는 1%p 당 310만 토큰을 아낀다. 아주 좋은 환율이다.")
print("→ 50%로 내려가면 1%p 당 39만 토큰. 환율이 8배 나빠진다. 이건 대개 손해다.")
# 출력:      정확도        총 토큰       품질      절감      품질 손실        1%p당 절감 토큰
# 출력: --------------------------------------------------------------------
# 출력:    100%   2,936,000    0.880     60%      1.44p         3,100,000
# 출력:     95%   3,072,400    0.873     58%      2.08p         2,078,578
# 출력:     90%   3,208,800    0.867     57%      2.72p         1,538,620
# 출력:     80%   3,481,600    0.854     53%      4.01p           977,645
# 출력:     70%   3,754,400    0.841     49%      5.29p           688,889
# 출력:     50%   4,300,000    0.815     42%      7.86p           394,402
# 출력:
# 출력: → 100%에서는 1%p 당 310만 토큰을 아낀다. 아주 좋은 환율이다.
# 출력: → 50%로 내려가면 1%p 당 39만 토큰. 환율이 8배 나빠진다. 이건 대개 손해다.

# %% [markdown]
# ## 5. 그럼 언제 라우팅이 품질을 «올리는» 장치가 되나
#
# 답의 문장을 뒤집어 봅니다. 정밀한 길의 「틀린 길로 왔을 때」 품질을 $w_p$ 라는 변수로 두면
#
# $$
# Q_{\text{전부 정밀}}(w_p) = 0.72\,w_p + 0.28 \cdot 0.93, \qquad
# Q_{\text{라우팅}}(a{=}1) = 0.72 \cdot 0.86 + 0.28 \cdot 0.93
# $$
#
# 라우팅 쪽은 $w_p$ 와 무관합니다(100% 정확하면 틀린 길로 가는 입력이 없으니까).
# 두 식을 비교하면 조건이 아주 깔끔하게 남습니다.
#
# $$
# Q_{\text{라우팅}}(1) > Q_{\text{전부 정밀}} \iff w_p < 0.86 = r_{\text{fast}}
# $$
#
# 즉 임계값은 정확히 **빠른 길의 정답 품질 0.86** 입니다.
# ex3 은 $w_p = 0.88 > 0.86$ 으로 잡았기 때문에 지배가 성립하고, 품질이 안 올랐습니다.

# %%
print(f"{'w_p':>7}{'전부 정밀':>12}{'라우팅 100%':>14}{'라우팅 우위':>14}")
print("-" * 48)
for wp in (0.40, 0.60, 0.80, 0.84, 0.86, 0.88, 0.95):
    q_ap = 0.72 * wp + 0.28 * 0.93
    q_rt = 0.72 * 0.86 + 0.28 * 0.93
    print(f"{wp:>7.2f}{q_ap:>12.4f}{q_rt:>14.4f}{'예' if q_rt > q_ap else '아니오':>14}")
print("\n→ 임계값 w_p = 0.86 (= 빠른 길의 정답 품질). 여기서 부호가 뒤집힌다.")
print("→ ex3 의 w_p = 0.88 은 임계값보다 크다. 그래서 100%에서도 품질이 못 오른다.")
# 출력:     w_p       전부 정밀      라우팅 100%        라우팅 우위
# 출력: ------------------------------------------------
# 출력:    0.40      0.5484        0.8796             예
# 출력:    0.60      0.6924        0.8796             예
# 출력:    0.80      0.8364        0.8796             예
# 출력:    0.84      0.8652        0.8796             예
# 출력:    0.86      0.8796        0.8796         아니오
# 출력:    0.88      0.8940        0.8796         아니오
# 출력:    0.95      0.9444        0.8796         아니오

# %% [markdown]
# ## 6. 시각화
#
# 네 칸으로 봅니다.
#
# 1. **품질 곡선** — $Q(a)$ 는 오르지만 천장($a=1$)이 기준선 아래에서 멈춘다
# 2. **토큰 곡선** — 정확도가 오를수록 단조 감소. 여기가 라우터가 진짜로 버는 곳이다
# 3. **교환비** — 품질 1%p 당 아끼는 토큰. 정확도가 낮아지면 환율이 급격히 나빠진다
# 4. **$w_p$ 스윕** — 정밀한 길의 「오지랖 품질」이 0.86 아래로 내려가야 라우팅이 품질로 이긴다

# %%
STEPS = 101
accs = [i / (STEPS - 1) for i in range(STEPS)]
qs = [routed(a)[1] for a in accs]
cs = [routed(a)[0] for a in accs]
rates = []
for a in accs:
    c, q = routed(a)
    dq = (PQ - q) * 100
    rates.append(None if dq < 1e-9 else (PC - c) / dq)

wps = [0.40 + 0.006 * i for i in range(101)]
q_ap_wp = [0.72 * w + 0.28 * 0.93 for w in wps]
q_rt_wp = [0.72 * 0.86 + 0.28 * 0.93] * len(wps)

C_Q, C_BASE, C_TOK, C_RATE, C_MARK = "#2f6fbf", "#c8503c", "#3f9d6a", "#8a5cd0", "#9aa0a6"

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "① 품질 Q(a) — 오르지만 천장이 기준선 아래",
        "② 토큰 C(a) — 라우터가 진짜로 버는 곳",
        "③ 교환비 — 품질 1%p당 아끼는 토큰",
        "④ w_p 스윕 — 부호가 뒤집히는 임계값 0.86",
    ),
    vertical_spacing=0.16, horizontal_spacing=0.11,
)

# ① 품질
fig.add_trace(go.Scatter(x=accs, y=qs, mode="lines", name="라우팅 Q(a)",
                         line=dict(color=C_Q, width=3)), row=1, col=1)
fig.add_trace(go.Scatter(x=accs, y=[PQ] * len(accs), mode="lines",
                         name="전부 정밀한 길 0.894",
                         line=dict(color=C_BASE, width=2, dash="dash")), row=1, col=1)
fig.add_trace(go.Scatter(x=[1.0], y=[q100], mode="markers+text",
                         text=["0.880 (천장) "], textposition="bottom left",
                         marker=dict(color=C_Q, size=11, symbol="circle"),
                         showlegend=False), row=1, col=1)
fig.add_trace(go.Scatter(x=[1.0, 1.0], y=[q100, PQ], mode="lines",
                         line=dict(color=C_MARK, width=2, dash="dot"),
                         showlegend=False), row=1, col=1)
fig.add_annotation(x=1.0, y=(q100 + PQ) / 2, text="격차 1.44%p", showarrow=True,
                   arrowhead=2, ax=-70, ay=-24, font=dict(size=11, color=C_BASE),
                   row=1, col=1)

# ② 토큰
fig.add_trace(go.Scatter(x=accs, y=cs, mode="lines", name="라우팅 C(a)",
                         line=dict(color=C_TOK, width=3), showlegend=True), row=1, col=2)
fig.add_trace(go.Scatter(x=accs, y=[PC] * len(accs), mode="lines",
                         name="전부 정밀 7.4M",
                         line=dict(color=C_BASE, width=2, dash="dash")), row=1, col=2)
fig.add_annotation(x=1.0, y=c100, text="60% 절감", showarrow=True, arrowhead=2,
                   ax=-46, ay=-26, font=dict(size=11, color=C_TOK), row=1, col=2)

# ③ 교환비
fig.add_trace(go.Scatter(x=accs, y=rates, mode="lines", name="교환비",
                         line=dict(color=C_RATE, width=3)), row=2, col=1)
for a in (0.5, 0.8, 1.0):
    c, q = routed(a)
    dq = (PQ - q) * 100
    fig.add_trace(go.Scatter(x=[a], y=[(PC - c) / dq], mode="markers+text",
                             text=[f"{a:.0%}"], textposition="top center",
                             marker=dict(color=C_RATE, size=9), showlegend=False),
                  row=2, col=1)

# ④ w_p 스윕
fig.add_trace(go.Scatter(x=wps, y=q_ap_wp, mode="lines", name="전부 정밀(w_p 의존)",
                         line=dict(color=C_BASE, width=3)), row=2, col=2)
fig.add_trace(go.Scatter(x=wps, y=q_rt_wp, mode="lines", name="라우팅 100%(w_p 무관)",
                         line=dict(color=C_Q, width=3, dash="dash")), row=2, col=2)
fig.add_trace(go.Scatter(x=[0.86], y=[0.8796], mode="markers",
                         marker=dict(color="#000000", size=11, symbol="x"),
                         showlegend=False), row=2, col=2)
fig.add_annotation(x=0.86, y=0.8796, text="임계 w_p=0.86", showarrow=True, arrowhead=2,
                   ax=-58, ay=34, font=dict(size=11), row=2, col=2)
fig.add_annotation(x=0.90, y=0.72, text="ex3 은 여기(0.88)<br>→ 정밀한 길이 지배",
                   showarrow=False, font=dict(size=10, color=C_BASE), row=2, col=2)

fig.update_xaxes(title_text="라우터 정확도 a", row=1, col=1)
fig.update_xaxes(title_text="라우터 정확도 a", row=1, col=2)
fig.update_xaxes(title_text="라우터 정확도 a", row=2, col=1)
fig.update_xaxes(title_text="정밀한 길의 «오지랖» 품질 w_p", row=2, col=2)
fig.update_yaxes(title_text="평균 품질", row=1, col=1)
fig.update_yaxes(title_text="총 토큰", row=1, col=2)
fig.update_yaxes(title_text="토큰 / 품질 1%p", type="log", row=2, col=1)
fig.update_yaxes(title_text="평균 품질", row=2, col=2)

fig.update_layout(
    title=dict(text="라우터는 품질을 올리는 장치가 아니라 교환이다 (ex3_router.py 모델)", x=0.02),
    height=780, width=1180, template="plotly_white",
    legend=dict(orientation="h", yanchor="bottom", y=-0.11, x=0.0),
    margin=dict(t=90, b=90, l=70, r=40),
)

_show(fig)
png = os.path.join(HERE, "expy.png")
fig.write_image(png, scale=2)
print(f"저장: {png}")
# 출력: 저장: .../55744e43-e84c-488c-a776-733f17d727f0/expy.png

# %% [markdown]
# ## 7. 정리
#
# - 라우팅 정확도 100%에서 품질이 0.894 → 0.880 으로 **내려간** 건 라우터의 결함이 아니라
#   **모델 가정의 결과**입니다. 정밀한 길이 안 필요한 입력에도 0.88(> 0.86)을 내니까요.
# - $Q(a) = 0.7512 + 0.1284a$ 는 증가 함수입니다. 정확도를 올리는 노력은 헛되지 않습니다.
#   다만 $Q(1) = 0.8796$ 이 **기준선보다 낮은 천장**이라는 게 요점입니다.
# - 지배 구조가 있으면 라우팅으로 얻을 수 있는 건 품질이 아니라 **토큰**뿐입니다.
#   100%에서 품질 1.44%p 를 내주고 60%를 아끼고, 50%에서는 7.86%p 를 내주고 42%만 아낍니다.
#   교환비가 8배 나빠집니다.
# - 그래서 라우터를 넣기 전에 만들 것은 라우터가 아니라 **채점 데이터셋**입니다.
#   정확도 $a$ 를 모르면 위 표의 어느 줄에 서 있는지 알 수 없고,
#   그러면 「라우터 넣었더니 좋아졌다」는 느낌만 남습니다.
