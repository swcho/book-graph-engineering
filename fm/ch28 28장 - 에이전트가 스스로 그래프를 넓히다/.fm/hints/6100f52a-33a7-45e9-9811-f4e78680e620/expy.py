# 필요 패키지: numpy, plotly, kaleido (정적 이미지 저장용)
#   pip install numpy plotly kaleido

# %% [markdown]
# # `ex4_drift.py` 100세대 시뮬레이션 — 결과와 그 원인
#
# **질문:** `ex4_drift.py`의 100세대 시뮬레이션 결과는 무엇인가?
#
# **답:** 제약이 20% → 9%로 반토막, 사건이 10% → 19%로 두 배,
# 관계는 40% → 42%로 거의 그대로.
#
# 이 노트북은
#
# 1. 책의 몬테카를로 루프(`random.Random(3)`)를 그대로 재현해 수치를 대조하고,
# 2. 같은 과정을 **평균 동역학**으로 풀어 세대별 궤적을 그리고,
# 3. 전이행렬 $P$의 **열 합**, **정상분포**(좌고유벡터), **수렴 속도**(제2고유값)로
#    "왜 제약만 반토막인가"를 설명한다.

# %%
import random

import numpy as np


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


KINDS = ["관계", "선호", "제약", "사건"]
START = {"관계": 40, "선호": 30, "제약": 20, "사건": 10}

# EMIT[읽은 종류][쓰는 종류] — 행 합이 1인 행-확률행렬 P
EMIT = {
    "관계": {"관계": 0.62, "선호": 0.18, "제약": 0.05, "사건": 0.15},
    "선호": {"관계": 0.20, "선호": 0.55, "제약": 0.10, "사건": 0.15},
    "제약": {"관계": 0.25, "선호": 0.20, "제약": 0.35, "사건": 0.20},
    "사건": {"관계": 0.40, "선호": 0.20, "제약": 0.05, "사건": 0.35},
}
GEN = 100
PER_GEN = 20

P = np.array([[EMIT[r][c] for c in KINDS] for r in KINDS])
pi0 = np.array([START[k] for k in KINDS], dtype=float)
pi0 = pi0 / pi0.sum()

print("P (행=읽은 종류, 열=쓴 종류)")
print(P)
print("행 합:", P.sum(axis=1))
print("시작 분포 pi0:", dict(zip(KINDS, pi0.round(3))))

# 출력:
# P (행=읽은 종류, 열=쓴 종류)
# [[0.62 0.18 0.05 0.15]
#  [0.2  0.55 0.1  0.15]
#  [0.25 0.2  0.35 0.2 ]
#  [0.4  0.2  0.05 0.35]]
# 행 합: [1. 1. 1. 1.]
# 시작 분포 pi0: {'관계': 0.4, '선호': 0.3, '제약': 0.2, '사건': 0.1}
# → 행 합이 모두 1. "읽으면 반드시 하나를 쓴다"는 제약이라 여기엔 정보가 없다.

# %% [markdown]
# ## 1. 책의 루프를 그대로 재현 (시드 3)
#
# 한 세대에 `PER_GEN = 20`개의 새 사실을 쓴다. 각 사실은
#
# - 현재 그래프 **개수에 비례**해 하나를 읽고 (seed),
# - 읽은 종류의 `EMIT` 행을 따라 새 종류를 쓴다.
#
# 중요한 것은 **기존 사실이 절대 사라지지 않는다**는 점이다. 분포는 지워져서가
# 아니라 새로 쌓이는 것에 **묽어져서** 움직인다.

# %%
def step(counts, rng, human_share=0.0):
    new = dict(counts)
    for _ in range(PER_GEN):
        if rng.random() < human_share:
            k = rng.choices(KINDS, [START[x] for x in KINDS])[0]
            new[k] += 1
            continue
        seed = rng.choices(KINDS, [counts[x] for x in KINDS])[0]
        emit = EMIT[seed]
        k = rng.choices(KINDS, [emit[x] for x in KINDS])[0]
        new[k] += 1
    return new


def run(human_share, seed=3):
    rng = random.Random(seed)
    c = dict(START)
    traj = []
    for _ in range(1, GEN + 1):
        c = step(c, rng, human_share)
        t = sum(c.values())
        traj.append([c[k] / t for k in KINDS])
    return np.array(traj)


mc = run(0.0)  # 사람 개입 0%
print(f"{'세대':>5}" + "".join(f"{k:>9}" for k in KINDS))
print("-" * 41)
print(f"{0:>5}" + "".join(f"{START[k] / 100:>8.0%}" for k in KINDS))
for g in (1, 10, 50, 100):
    print(f"{g:>5}" + "".join(f"{v:>8.0%}" for v in mc[g - 1]))

# 출력:
#    세대       관계       선호       제약       사건
# -----------------------------------------
#     0     40%     30%     20%     10%
#     1     38%     30%     18%     14%
#    10     41%     29%     14%     16%
#    50     41%     31%     10%     18%
#   100     42%     30%      9%     19%
#
# → 책 본문 그대로다.
#     제약 20% → 9%   (반토막)
#     사건 10% → 19%  (두 배)
#     관계 40% → 42%  (거의 그대로)
#   선호도 30% → 30%로 사실상 제자리. 움직인 것은 제약과 사건 둘뿐이다.

# %% [markdown]
# ## 2. 평균 동역학 — 난수를 걷어내면
#
# 세대 $t$의 비율을 $\pi_t$, 누적 사실 수를 $N_t$라 하면 새로 쓰이는 20개의
# 기대 분포는 $\pi_t P$ 이고, 누적 비율은
#
# $$\pi_{t+1} \;=\; \frac{N_t\,\pi_t \;+\; m\,\pi_t P}{N_t + m},\qquad m = 20,\; N_0 = 100$$
#
# 이다. 새로 **쓰이는 것**만 보면 순수한 마르코프 갱신
#
# $$\nu_{t+1} = \nu_t P$$
#
# 이지만, 그래프 전체 비율은 과거 누적에 눌려 훨씬 느리게 따라간다.

# %%
m, N = PER_GEN, 100.0
pi = pi0.copy()
det = []
for _ in range(GEN):
    pi = (N * pi + m * (pi @ P)) / (N + m)
    N += m
    det.append(pi.copy())
det = np.array(det)

print(f"{'세대':>5}" + "".join(f"{k:>9}" for k in KINDS) + "   (평균 동역학)")
for g in (1, 10, 50, 100):
    print(f"{g:>5}" + "".join(f"{v:>8.1%}" for v in det[g - 1]))
print("\n최종 누적 사실 수 N_100 =", int(N), " (시작 100개는 4.8%뿐)")

# 출력:
#    세대       관계       선호       제약       사건   (평균 동역학)
#     1    40.0%    29.9%    18.8%    11.3%
#    10    40.2%    29.8%    14.3%    15.7%
#    50    40.9%    29.6%    11.3%    18.2%
#   100    41.2%    29.6%    10.6%    18.7%
#
# 최종 누적 사실 수 N_100 = 2100  (시작 100개는 4.8%뿐)
# → 난수를 완전히 걷어내도 같은 그림이다. 제약은 20%→10.6%, 사건은 10%→18.7%.
#   시드 3 표본(9%/19%)과 1~2%p 안쪽. 이 드리프트는 운이 아니라 P의 구조다.

# %% [markdown]
# ## 3. 왜 제약만 반토막인가 — 열 합
#
# 행 합은 정의상 전부 1이다(읽으면 반드시 하나를 쓴다). 정보는 **열 합**에 있다.
#
# $$\text{in}(k) \;=\; \sum_{j} P_{jk}$$
#
# 는 "다른 종류들이 나를 낳아 주는 총량"이다. 대각원소(자기 재생산율)만 보면
# 제약 0.35 = 사건 0.35 로 같은데, 결과는 정반대로 갈렸다. 열 합을 보면 갈린다.

# %%
col = P.sum(axis=0)
print(f"{'종류':>4} {'자기재생산 P_kk':>14} {'열 합 in(k)':>12} {'열 합/4':>9} {'시작':>6}")
for i, k in enumerate(KINDS):
    print(f"{k:>4} {P[i, i]:>14.2f} {col[i]:>12.2f} {col[i] / 4:>9.1%} {pi0[i]:>6.0%}")
print("\n열 합 총계:", col.sum())

# 출력:
#   종류   자기재생산 P_kk    열 합 in(k)     열 합/4     시작
#   관계           0.62         1.47     36.8%    40%
#   선호           0.55         1.13     28.2%    30%
#   제약           0.35         0.55     13.8%    20%
#   사건           0.35         0.85     21.2%    10%
#
# 열 합 총계: 4.0
# → 제약의 열 합 0.55 는 꼴찌. 사건 0.85 의 65% 수준이다.
#   특히 «관계 → 제약» 0.05 vs «관계 → 사건» 0.15 = 3배 차이인데,
#   관계가 제일 흔하므로 이 3배가 매 세대 복리로 벌어진다.
#   살아남는 종류를 정하는 건 자기 재생산율이 아니라 «전체 분포와의 곱» pi·P 이다.

# %% [markdown]
# ## 4. 정상분포 — 루프가 결국 도달하는 곳
#
# 새로 쓰이는 사실의 분포는 $\nu_{t+1} = \nu_t P$ 를 따르므로, $P$의 고유값 1에
# 대응하는 **좌고유벡터**가 종착지다.
#
# $$\pi^{*} P = \pi^{*},\qquad \sum_k \pi^{*}_k = 1$$
#
# (열 합 / 4 는 $P$가 이중확률행렬일 때만 정상분포와 같다. 여기서는 어긋나므로
# 방향의 감은 주지만 정확한 답은 아니다.)

# %%
w, v = np.linalg.eig(P.T)          # 좌고유벡터 = P^T 의 우고유벡터
idx = np.argsort(-w.real)
stat = np.real(v[:, idx[0]])
stat = stat / stat.sum()

print("정상분포 pi* :", {k: f"{x:.1%}" for k, x in zip(KINDS, stat)})
print("검산 pi*P    :", np.allclose(stat @ P, stat))
print("열 합/4 근사 :", {k: f"{x:.1%}" for k, x in zip(KINDS, col / 4)})
print("시작 분포    :", {k: f"{x:.0%}" for k, x in zip(KINDS, pi0)})
print("MC 100세대   :", {k: f"{x:.0%}" for k, x in zip(KINDS, mc[-1])})

# 출력:
# 정상분포 pi* : {'관계': '41.9%', '선호': '29.5%', '제약': '9.2%', '사건': '19.3%'}
# 검산 pi*P    : True
# 열 합/4 근사 : {'관계': '36.8%', '선호': '28.2%', '제약': '13.8%', '사건': '21.2%'}
# 시작 분포    : {'관계': '40%', '선호': '30%', '제약': '20%', '사건': '10%'}
# MC 100세대   : {'관계': '42%', '선호': '30%', '제약': '9%', '사건': '19%'}
#
# → 100세대 결과 = 정상분포다. 소수점까지 겹친다.
#     제약 9.2% ↔ 9%,  관계 41.9% ↔ 42%,  사건 19.3% ↔ 19%,  선호 29.5% ↔ 30%
#   답안의 세 숫자는 우연한 표본이 아니라 P가 처음부터 정해 둔 종착지다.
#   그래서 시드를 바꿔도 몇 %p만 흔들리고 방향은 안 바뀐다.
#   (열 합/4 근사는 방향의 감만 준다. P가 이중확률행렬이 아니라 값이 어긋난다.)

# %% [markdown]
# ## 5. 수렴 속도 — 제2고유값과 누적의 관성
#
# 새로 쓰이는 분포 $\nu_t$의 오차는 제2고유값 $\lambda_2$의 크기로 기하 감쇠한다.
#
# $$\|\nu_t - \pi^{*}\| \sim |\lambda_2|^{t},\qquad
#   t_{1/2} = \frac{\ln 2}{-\ln|\lambda_2|}$$
#
# 그런데 그래프 **전체** 비율은 과거가 지워지지 않아 훨씬 느리다.
# $N_t = N_0 + mt$ 이므로 아직 안 기운 과거의 지분이 $\mathcal{O}(1/t)$ 로만 얇아진다.
# 기하 감쇠가 아니라 **다항 감쇠** — "며칠이면 끝날 드리프트"가 아니라
# 몇 달에 걸쳐 조용히 진행되는 드리프트인 이유다.

# %%
lam = np.sort_complex(w)[::-1]
lam2 = max(abs(x) for x in w if abs(x - 1) > 1e-9)
print("고유값:", np.round(np.real_if_close(lam, tol=1e6), 4))
print(f"|lambda_2| = {lam2:.4f},  반감기 t_half = {np.log(2) / -np.log(lam2):.2f} 세대")

nu = pi0.copy()
print("\n세대   신규쓰기 오차   누적비율 오차   (L1 거리, pi* 기준)")
for t in range(1, GEN + 1):
    nu = nu @ P
    if t in (1, 2, 5, 10, 20, 50, 100):
        e_new = np.abs(nu - stat).sum()
        e_cum = np.abs(det[t - 1] - stat).sum()
        print(f"{t:>4} {e_new:>14.5f} {e_cum:>15.5f}")

# 출력:
# 고유값: [1.     0.385  0.2817 0.2033]
# |lambda_2| = 0.3850,  반감기 t_half = 0.73 세대
#
# 세대   신규쓰기 오차   누적비율 오차   (L1 거리, pi* 기준)
#    1        0.06946         0.19946
#    2        0.02214         0.17976
#    5        0.00103         0.14118
#   10        0.00001         0.10715
#   20        0.00000         0.07564
#   50        0.00000         0.04417
#  100        0.00000         0.02843
#
# → 신규 쓰기 분포는 5세대면 정상분포에 붙는다 (|lambda_2|=0.385, 반감기 0.73세대).
#   반면 누적 비율 오차는 아주 느리다. 20세대 0.076 → 100세대 0.028,
#   세대를 5배 더 돌려도 오차는 2.7배밖에 안 준다 (기하 감쇠가 아니라 다항 감쇠).
#   즉 «지금 쓰이는 것»은 5세대 만에 이미 기울어 끝났는데,
#   «전체 비율»이 그 사실을 드러내는 데 100세대가 걸린다.
#   드리프트를 눈으로 못 잡는 이유이자, 비율 지표를 매일 재라는 처방이 나오는 지점이다.

# %% [markdown]
# ## 6. 세대별 비율 궤적

# %%
import plotly.graph_objects as go

COLOR = {"관계": "#3b6fd4", "선호": "#8a63c8", "제약": "#d64545", "사건": "#2f9e6f"}
gens = np.arange(0, GEN + 1)

fig = go.Figure()
for i, k in enumerate(KINDS):
    fig.add_trace(go.Scatter(
        x=gens, y=np.concatenate([[pi0[i]], mc[:, i]]),
        name=f"{k} (시뮬)", mode="lines",
        line=dict(color=COLOR[k], width=2.2),
    ))
    fig.add_trace(go.Scatter(
        x=gens, y=np.concatenate([[pi0[i]], det[:, i]]),
        name=f"{k} (평균)", mode="lines",
        line=dict(color=COLOR[k], width=1.1, dash="dot"),
        showlegend=False,
    ))
    fig.add_hline(y=stat[i], line=dict(color=COLOR[k], width=0.8, dash="dash"),
                  opacity=0.45)
    fig.add_annotation(x=GEN, y=stat[i], xshift=42,
                       text=f"π*={stat[i]:.1%}", showarrow=False,
                       font=dict(size=10, color=COLOR[k]))

fig.add_annotation(x=30, y=0.155, text="제약 20% → 9%  (반토막)",
                   showarrow=False, font=dict(size=12, color="#d64545"))
fig.add_annotation(x=30, y=0.225, text="사건 10% → 19%  (두 배)",
                   showarrow=False, font=dict(size=12, color="#2f9e6f"))
fig.update_layout(
    title="ex4_drift.py — 100세대 종류 비율 궤적 (실선=시뮬 시드3, 점선=평균 동역학, 파선=정상분포)",
    xaxis_title="세대", yaxis_title="전체 사실 중 비율",
    yaxis=dict(tickformat=".0%", range=[0, 0.5]),
    xaxis=dict(range=[0, 112]),
    width=980, height=560, template="plotly_white",
    legend=dict(orientation="h", y=-0.16),
    margin=dict(l=60, r=90, t=70, b=90),
)
_show(fig)

import os
_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_png, scale=2)
print("저장:", _png)

# 출력:
# 저장: .../6100f52a-33a7-45e9-9811-f4e78680e620/expy.png

# %% [markdown]
# ## 정리
#
# | 종류 | 시작 | 100세대 | 정상분포 $\pi^*$ | 자기재생산 $P_{kk}$ | 열 합 |
# |---|---|---|---|---|---|
# | 관계 | 40% | 42% | 41.9% | 0.62 | 1.47 |
# | 선호 | 30% | 30% | 29.5% | 0.55 | 1.13 |
# | 제약 | 20% | **9%** | 9.2% | 0.35 | **0.55** |
# | 사건 | 10% | **19%** | 19.3% | 0.35 | 0.85 |
#
# - 100세대 결과 = $P$의 정상분포. 시드를 바꿔도 몇 %p만 움직이고 방향은 안 바뀐다.
# - 제약과 사건은 자기 재생산율이 0.35로 같은데 정반대로 갔다. 갈라 놓은 것은
#   **열 합**(남이 나를 낳아 주는 양: 0.55 대 0.85)과 거기에 곱해지는 **현재 분포**다.
#   가장 흔한 관계가 사건은 15%, 제약은 5%로 낳으니 그 3배가 복리로 벌어진다.
# - 신규 쓰기는 5세대면 기울지만 ($|\lambda_2| = 0.385$) 누적 비율은 $\mathcal{O}(1/t)$로
#   따라온다. 그래서 100세대나 걸리고, 그래서 눈에 안 띈다.
# - 처방은 개별 사실 검수가 아니라 **비율 상한/하한**: 관계 55% 초과 시 쓰기 중단,
#   제약 10% 미만 시 경보.
