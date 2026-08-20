# %% [markdown]
# # 사람이 20%를 직접 넣으면 드리프트를 막을 수 있는가?
#
# **답: 막지 못한다. 감속은 되지만 방향은 그대로다. 개별 사실이 아니라 비율에 개입해야 한다.**
#
# 28장 `ex4_drift.py` 의 전이행렬을 그대로 재현하고, 거기에
# "사람이 매 세대 20%를 원래 분포로 직접 주입"하는 변형을 붙여 두 궤적을 비교한다.
#
# ## 왜 마르코프 체인인가
#
# 에이전트는 **그래프에서 하나를 읽고, 그것에 이끌려 새 사실을 쓴다**.
# 읽을 확률이 현재 분포 $\pi_t$ 에 비례하고, 읽은 종류 $i$ 가 종류 $j$ 를 낳을 확률이
# $P_{ij}$ 이면, 새로 쓰이는 사실의 분포는 정확히
#
# $$\pi_{t+1} = \pi_t P$$
#
# 이다. 즉 자기가 쓴 것을 다시 읽는 루프는 **전이행렬 $P$ 위의 마르코프 체인**이고,
# 드리프트의 종착점은 $P$ 의 좌고유벡터(정상분포) $\pi^\ast$ 다.
#
# $$\pi^\ast P = \pi^\ast, \qquad \sum_k \pi^\ast_k = 1$$
#
# ## 사람이 20%를 넣으면 무엇이 달라지나
#
# 사람이 매 세대 비율 $h$ 만큼을 **원래 분포** $s$ 로 직접 주입하면 생성 분포는
#
# $$q_t = (1-h)\,\pi_t P + h\,s$$
#
# 가 된다. 이건 여전히 **아핀 축약사상**이라 고정점이 하나 있고, 그 고정점은
#
# $$\pi^\ast_h \left( I - (1-h)P \right) = h\,s
# \quad\Longleftrightarrow\quad
# \pi^\ast_h = h\,s\left( I - (1-h)P \right)^{-1}$$
#
# 이다. 핵심은 $h < 1$ 인 한 $\pi^\ast_h \neq s$ 라는 점이다.
# 주입은 고정점을 $s$ **쪽으로 당길 뿐** $s$ 에 **도달시키지 못한다**.
# 그리고 수렴 속도를 정하는 스펙트럼 반경이 $|\lambda_2|$ 에서 $(1-h)|\lambda_2|$ 로 줄어드니
# **느려지기만 한다** — 이게 "감속은 되는데 방향은 그대로"의 정확한 의미다.

# %%
# 필요 패키지: numpy, plotly, kaleido
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# ex4_drift.py 와 동일한 설정
KINDS = ["관계", "선호", "제약", "사건"]
START = {"관계": 40, "선호": 30, "제약": 20, "사건": 10}
EMIT = {
    "관계": {"관계": 0.62, "선호": 0.18, "제약": 0.05, "사건": 0.15},
    "선호": {"관계": 0.20, "선호": 0.55, "제약": 0.10, "사건": 0.15},
    "제약": {"관계": 0.25, "선호": 0.20, "제약": 0.35, "사건": 0.20},
    "사건": {"관계": 0.40, "선호": 0.20, "제약": 0.05, "사건": 0.35},
}
GEN = 100
PER_GEN = 20

P = np.array([[EMIT[i][j] for j in KINDS] for i in KINDS])
s = np.array([START[k] for k in KINDS], dtype=float)
s /= s.sum()

print("전이행렬 P (행=읽은 종류, 열=쓰는 종류)")
print(f"{'':>6}" + "".join(f"{k:>8}" for k in KINDS))
for i, k in enumerate(KINDS):
    print(f"{k:>6}" + "".join(f"{P[i, j]:>8.2f}" for j in range(4)))
print("\n행 합:", P.sum(axis=1))
print("시작 분포 s:", {k: f"{v:.0%}" for k, v in zip(KINDS, s)})

# 출력:
# 전이행렬 P (행=읽은 종류, 열=쓰는 종류)
#             관계      선호      제약      사건
#     관계    0.62    0.18    0.05    0.15
#     선호    0.20    0.55    0.10    0.15
#     제약    0.25    0.20    0.35    0.20
#     사건    0.40    0.20    0.05    0.35
#
# 행 합: [1. 1. 1. 1.]
# 시작 분포 s: {'관계': '40%', '선호': '30%', '제약': '20%', '사건': '10%'}

# %% [markdown]
# ## 1. 정상분포 — 드리프트가 향하는 "방향"
#
# $\pi^\ast$ 는 $P^\top$ 의 고윳값 1 에 대응하는 고유벡터를 정규화해서 얻는다.
# 주입이 있는 경우의 고정점은 $\pi^\ast_h = h\,s (I-(1-h)P)^{-1}$ 로 바로 푼다.

# %%
def stationary(P):
    """P 의 좌고유벡터 (고윳값 1)."""
    w, v = np.linalg.eig(P.T)
    idx = np.argmin(np.abs(w - 1.0))
    pi = np.real(v[:, idx])
    return pi / pi.sum()


def fixed_point(P, s, h):
    """q = (1-h) pi P + h s 의 고정점. h=0 이면 정상분포."""
    if h == 0:
        return stationary(P)
    n = P.shape[0]
    return h * s @ np.linalg.inv(np.eye(n) - (1 - h) * P)


pi_star_0 = fixed_point(P, s, 0.0)
pi_star_20 = fixed_point(P, s, 0.2)

print(f"{'':>6}{'시작':>9}{'π* (주입 0%)':>15}{'π* (주입 20%)':>15}{'드리프트 부호':>15}")
print("-" * 62)
for i, k in enumerate(KINDS):
    d0 = pi_star_0[i] - s[i]
    d20 = pi_star_20[i] - s[i]
    sign = "↑ 증가" if d0 > 0 else "↓ 감소"
    print(f"{k:>6}{s[i]:>9.1%}{pi_star_0[i]:>14.1%}{pi_star_20[i]:>14.1%}{sign:>14}")

print("\n검증  π*P == π* :", np.allclose(pi_star_0 @ P, pi_star_0))
print("검증  0.8·π*P+0.2·s == π* :",
      np.allclose(0.8 * (pi_star_20 @ P) + 0.2 * s, pi_star_20))

# 두 고정점의 변화 방향이 같은가 (부호 일치 여부)
d0 = pi_star_0 - s
d20 = pi_star_20 - s
print("\n드리프트 벡터 부호가 전부 같은가:", np.all(np.sign(d0) == np.sign(d20)))
print("크기 비 (주입20% / 주입0%):",
      {k: round(float(v), 3) for k, v in zip(KINDS, d20 / d0)})
cos = d0 @ d20 / (np.linalg.norm(d0) * np.linalg.norm(d20))
print(f"두 드리프트 벡터의 코사인 유사도: {cos:.6f}   ← 1.0 이면 방향 완전 동일")

# 출력:
#              시작     π* (주입 0%)    π* (주입 20%)        드리프트 부호
# --------------------------------------------------------------
#     관계    40.0%         41.9%         41.0%          ↑ 증가
#     선호    30.0%         29.5%         29.6%          ↓ 감소
#     제약    20.0%          9.2%         12.1%          ↓ 감소
#     사건    10.0%         19.3%         17.2%          ↑ 증가
#
# 검증  π*P == π* : True
# 검증  0.8·π*P+0.2·s == π* : True
#
# 드리프트 벡터 부호가 전부 같은가: True
# 크기 비 (주입20% / 주입0%): {'관계': 0.528, '선호': 0.683, '제약': 0.736, '사건': 0.776}
# 두 드리프트 벡터의 코사인 유사도: 0.998837   ← 1.0 이면 방향 완전 동일

# %% [markdown]
# 여기서 답이 이미 나온다.
#
# * 주입 0%: 제약 20% → **9.2%**, 사건 10% → **19.3%**
# * 주입 20%: 제약 20% → **12.1%**, 사건 10% → **17.2%**
#
# 20%를 사람이 직접 넣어도 **제약은 여전히 내려가고 사건은 여전히 올라간다**.
# 드리프트 벡터의 부호가 전부 같고 코사인 유사도가 $0.9988$ — 사실상 **같은 방향**이다.
# 달라진 건 크기뿐이고, 제약 축에서는 $0.74$ 배로 줄었을 뿐이다.
# 개별 사실을 20% 넣는 개입은 **드리프트를 1/4쯤 깎는 감속기**이지 방향 전환기가 아니다.

# %% [markdown]
# ## 2. 100세대 시뮬레이션
#
# 실제 그래프는 세대마다 `PER_GEN=20` 개가 **누적**되므로, 세대 $t$ 의 총량을 $N_t$ 라 하면
#
# $$\pi_{t+1} = \frac{N_t \pi_t + 20\, q_t}{N_t + 20},
# \qquad q_t = (1-h)\,\pi_t P + h\,s$$
#
# 이다. 분모가 계속 커지므로 **관성**이 붙어 수렴이 느리다.
# 확률적 버전(`ex4_drift.py` 원본, seed=3)과 위 결정론적 기댓값 버전을 둘 다 돌린다.

# %%
import random


def step(counts, rng, human_share=0.0):
    """ex4_drift.py 원본 그대로."""
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


def run_stochastic(human_share, seed=3):
    rng = random.Random(seed)
    c = dict(START)
    traj = [np.array([START[k] for k in KINDS], dtype=float) / 100]
    for _ in range(GEN):
        c = step(c, rng, human_share)
        t = sum(c.values())
        traj.append(np.array([c[k] / t for k in KINDS]))
    return np.array(traj)


def run_deterministic(human_share):
    """같은 과정의 기댓값 궤적. 노이즈 없이 방향만 본다."""
    N = float(sum(START.values()))
    pi = np.array([START[k] for k in KINDS], dtype=float) / N
    traj = [pi.copy()]
    for _ in range(GEN):
        q = (1 - human_share) * (pi @ P) + human_share * s
        pi = (N * pi + PER_GEN * q) / (N + PER_GEN)
        N += PER_GEN
        traj.append(pi.copy())
    return np.array(traj)


sto_0, sto_20 = run_stochastic(0.0), run_stochastic(0.2)
det_0, det_20 = run_deterministic(0.0), run_deterministic(0.2)


def table(title, traj):
    print(f"\n[{title}]")
    print(f"{'세대':>5}" + "".join(f"{k:>9}" for k in KINDS))
    print("-" * 41)
    for g in (0, 1, 10, 50, 100):
        print(f"{g:>5}" + "".join(f"{traj[g][i]:>8.0%}" for i in range(4)))


table("확률 시뮬 · 사람 개입 0%", sto_0)
table("확률 시뮬 · 사람 개입 20%", sto_20)
table("기댓값 · 사람 개입 0%", det_0)
table("기댓값 · 사람 개입 20%", det_20)

# 출력:
# [확률 시뮬 · 사람 개입 0%]      ← ex4_drift.py 원본과 동일 (제약 9%, 사건 19%)
#    세대       관계       선호       제약       사건
# -----------------------------------------
#     0     40%     30%     20%     10%
#     1     38%     30%     18%     14%
#    10     41%     29%     14%     16%
#    50     41%     31%     10%     18%
#   100     42%     30%      9%     19%
#
# [확률 시뮬 · 사람 개입 20%]     ← 원본과 동일 (제약 12%)
#    세대       관계       선호       제약       사건
# -----------------------------------------
#     0     40%     30%     20%     10%
#     1     37%     32%     19%     12%
#    10     41%     32%     14%     13%
#    50     41%     29%     13%     18%
#   100     42%     29%     12%     17%
#
# [기댓값 · 사람 개입 0%]
#    세대       관계       선호       제약       사건
# -----------------------------------------
#     0     40%     30%     20%     10%
#     1     40%     30%     19%     11%
#    10     40%     30%     14%     16%
#    50     41%     30%     11%     18%
#   100     41%     30%     11%     19%
#
# [기댓값 · 사람 개입 20%]
#    세대       관계       선호       제약       사건
# -----------------------------------------
#     0     40%     30%     20%     10%
#     1     40%     30%     19%     11%
#    10     40%     30%     16%     14%
#    50     41%     30%     13%     16%
#   100     41%     30%     13%     17%

# %% [markdown]
# ## 3. "감속" 을 숫자로 — 제약이 10% 경보선을 언제 뚫나

# %%
ALARM = 0.10  # 제약 비율 경보선
ci = KINDS.index("제약")


def cross(traj, level=ALARM):
    below = np.where(traj[:, ci] < level)[0]
    return int(below[0]) if len(below) else None


print("제약 비율이 10% 아래로 내려가는 시점 (기댓값 궤적, 세대)")
for h, traj in ((0.0, det_0), (0.2, det_20), (0.5, run_deterministic(0.5))):
    g = cross(traj)
    print(f"  사람 개입 {h:>4.0%}  →  {'도달 안 함 (100세대 내)' if g is None else f'{g}세대'}"
          f"   |  100세대 제약 {traj[-1][ci]:.1%}  |  고정점 {fixed_point(P, s, h)[ci]:.1%}")

print("\n제약 감소분 중 사람 개입이 되돌린 비율")
for h in (0.1, 0.2, 0.3, 0.5, 0.8):
    lost0 = s[ci] - fixed_point(P, s, 0.0)[ci]
    lost_h = s[ci] - fixed_point(P, s, h)[ci]
    print(f"  개입 {h:>4.0%}  →  제약 고정점 {fixed_point(P, s, h)[ci]:>6.1%}"
          f"   (손실 {lost_h / lost0:>5.1%} 만큼 남음, 방향 동일)")

# 출력:
# 제약 비율이 10% 아래로 내려가는 시점 (기댓값 궤적, 세대)
#   사람 개입   0%  →  도달 안 함 (100세대 내)   |  100세대 제약 10.6%  |  고정점 9.2%
#   사람 개입  20%  →  도달 안 함 (100세대 내)   |  100세대 제약 12.9%  |  고정점 12.1%
#   사람 개입  50%  →  도달 안 함 (100세대 내)   |  100세대 제약 15.9%  |  고정점 15.6%
#   (확률 시뮬에서는 주입 0% 가 50세대에 10%를 찍고 100세대에 9%로 내려간다)
#
# 제약 감소분 중 사람 개입이 되돌린 비율
#   개입  10%  →  제약 고정점  10.7%   (손실 86.3% 만큼 남음, 방향 동일)
#   개입  20%  →  제약 고정점  12.1%   (손실 73.6% 만큼 남음, 방향 동일)
#   개입  30%  →  제약 고정점  13.3%   (손실 61.9% 만큼 남음, 방향 동일)
#   개입  50%  →  제약 고정점  15.6%   (손실 41.1% 만큼 남음, 방향 동일)
#   개입  80%  →  제약 고정점  18.4%   (손실 14.8% 만큼 남음, 방향 동일)

# %% [markdown]
# 개입을 **80%까지** 올려도 제약은 20%로 돌아오지 않고 18.4%에서 멈춘다.
# "사람이 5분의 4를 직접 쓴다"는 건 자동 확장을 포기한다는 뜻인데도 방향은 그대로다.
# **개별 사실을 더 많이 넣는 것으로는 이 문제를 풀 수 없다.**

# %% [markdown]
# ## 4. 진짜 해법 — 비율에 개입한다
#
# 개별 사실(레벨)이 아니라 **전이행렬 자체(비율)** 에 손을 대면 어떻게 되나.
# 28장이 제시한 대응은 두 가지다.
#
# * 관계가 전체의 55%를 넘으면 **관계 쓰기를 멈춘다** → 행렬의 관계 열을 잘라 재정규화
# * 제약이 10% 아래로 내려가면 **경보를 울린다** → 제약 열에 하한을 강제
#
# 아래는 "제약이 하한 $c$ 아래면 그 세대의 쓰기에서 제약 비율을 $c$ 로 강제하고
# 나머지를 비례 축소" 하는 비율 개입이다. 개입량은 20%보다 훨씬 작다.

# %%
def run_quota(floor=0.15, cap_rel=0.55):
    """비율 개입: 제약에 하한, 관계에 상한을 두고 생성 분포 자체를 교정."""
    N = float(sum(START.values()))
    pi = np.array([START[k] for k in KINDS], dtype=float) / N
    traj = [pi.copy()]
    ri = KINDS.index("관계")
    intervened = 0.0
    for _ in range(GEN):
        q = pi @ P
        base = q.copy()
        if pi[ci] < floor:          # 제약 하한
            q[ci] = floor
        if pi[ri] > cap_rel:        # 관계 상한
            q[ri] = 0.0
        rest = [i for i in range(4) if i not in {ci, ri} or q[i] == base[i]]
        room = 1.0 - sum(q[i] for i in range(4) if i not in rest)
        tot = sum(base[i] for i in rest)
        for i in rest:
            q[i] = base[i] * room / tot if tot else 0.0
        intervened += np.abs(q - base).sum() / 2
        pi = (N * pi + PER_GEN * q) / (N + PER_GEN)
        N += PER_GEN
        traj.append(pi.copy())
    return np.array(traj), intervened / GEN


quota, avg_touch = run_quota()
table("비율 개입 (제약 하한 15%)", quota)
print(f"\n평균 개입량(세대당 재배치된 확률질량): {avg_touch:.1%}"
      f"   ← 사람이 직접 쓴 20% 개입보다 작다")
print(f"100세대 제약 비율:  주입20% {det_20[-1][ci]:.1%}   비율개입 {quota[-1][ci]:.1%}")

# 출력:
# [비율 개입 (제약 하한 15%)]
#    세대       관계       선호       제약       사건
# -----------------------------------------
#     0     40%     30%     20%     10%
#     1     40%     30%     19%     11%
#    10     40%     30%     15%     16%
#    50     39%     28%     15%     18%
#   100     39%     28%     15%     18%
#
# 평균 개입량(세대당 재배치된 확률질량): 3.8%   ← 사람이 직접 쓴 20% 개입보다 작다
# 100세대 제약 비율:  주입20% 12.9%   비율개입 15.0%

# %% [markdown]
# 세대당 평균 **3.8%** 의 확률질량만 재배치했는데, 20%를 사람이 직접 쓴 것보다
# 제약 비율을 더 잘 지켰다. 그리고 이건 우연이 아니라 구조적이다.
# 개별 사실 주입은 $\pi$ 에 상수를 더할 뿐이고, 비율 개입은 $P$ 를 바꿔
# **정상분포 자체를 옮긴다**.

# %%
# --- 시각화 -------------------------------------------------------------
COLORS = {"주입 없음": "#D1495B", "20% 주입": "#0F7B8A", "고정점": "#9AA0A6"}

fig = make_subplots(
    rows=2, cols=2, subplot_titles=[f"{k}" for k in KINDS],
    shared_xaxes=True, vertical_spacing=0.13, horizontal_spacing=0.09,
)
gens = np.arange(GEN + 1)

for idx, k in enumerate(KINDS):
    r, c_ = idx // 2 + 1, idx % 2 + 1
    first = idx == 0
    fig.add_trace(go.Scatter(
        x=gens, y=det_0[:, idx], mode="lines", name="주입 없음",
        line=dict(color=COLORS["주입 없음"], width=2.5),
        legendgroup="a", showlegend=first,
        hovertemplate="세대 %{x} · %{y:.1%}<extra>주입 없음</extra>"), row=r, col=c_)
    fig.add_trace(go.Scatter(
        x=gens, y=det_20[:, idx], mode="lines", name="사람 20% 주입",
        line=dict(color=COLORS["20% 주입"], width=2.5, dash="dash"),
        legendgroup="b", showlegend=first,
        hovertemplate="세대 %{x} · %{y:.1%}<extra>20% 주입</extra>"), row=r, col=c_)
    # 확률 시뮬 궤적은 옅게
    fig.add_trace(go.Scatter(
        x=gens, y=sto_0[:, idx], mode="lines", name="확률 시뮬(주입 없음)",
        line=dict(color=COLORS["주입 없음"], width=1), opacity=0.35,
        legendgroup="c", showlegend=first, hoverinfo="skip"), row=r, col=c_)
    # 정상분포 / 고정점 수평선
    for y, dash in ((pi_star_0[idx], "dot"), (pi_star_20[idx], "dot")):
        fig.add_hline(y=y, line=dict(color=COLORS["고정점"], width=1, dash=dash),
                      row=r, col=c_)
    fig.add_annotation(
        x=GEN, y=pi_star_0[idx], text=f"π* {pi_star_0[idx]:.0%}", row=r, col=c_,
        xanchor="right", yanchor="bottom", showarrow=False,
        font=dict(size=10, color=COLORS["고정점"]))
    fig.update_yaxes(tickformat=".0%", row=r, col=c_,
                     gridcolor="rgba(128,128,128,0.18)", zeroline=False)
    fig.update_xaxes(row=r, col=c_, gridcolor="rgba(128,128,128,0.12)",
                     zeroline=False)

fig.update_layout(
    title=dict(
        text="사람 20% 주입은 <b>감속기</b>일 뿐 방향 전환기가 아니다"
             "<br><sup>점선 = 정상분포 π* / 고정점. "
             "제약은 두 경우 모두 내려가고 사건은 두 경우 모두 올라간다</sup>",
        x=0.02, xanchor="left"),
    template="plotly_white", height=620, width=980,
    font=dict(size=13),
    legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=1),
    margin=dict(t=130, l=60, r=30, b=50),
    hovermode="x unified",
)
fig.update_xaxes(title_text="세대", row=2, col=1)
fig.update_xaxes(title_text="세대", row=2, col=2)

_show(fig)

import os
_png = os.path.join(os.path.dirname(os.path.abspath(__file__))
                    if "__file__" in dir() else ".", "expy.png")
fig.write_image(_png, scale=2)
print("저장:", _png)

# 출력:
# 저장: .../2cd0aadb-028f-4838-ab52-9989241065b6/expy.png

# %% [markdown]
# ## 정리
#
# | | 제약 (시작 20%) | 사건 (시작 10%) | 방향 |
# |---|---|---|---|
# | 주입 없음 $\pi^\ast_0$ | **9.2%** | **19.3%** | 제약↓ 사건↑ |
# | 사람 20% 주입 $\pi^\ast_{0.2}$ | **12.1%** | **17.2%** | 제약↓ 사건↑ (**동일**) |
# | 사람 80% 주입 | 18.4% | — | 제약↓ (**동일**) |
# | 비율 개입 (제약 하한 15%) | **15.0%**, 개입량 3.8% | — | **막힘** |
#
# 1. 드리프트의 방향은 **전이행렬 $P$ 의 구조**가 정한다. 시작 분포도, 주입되는 사실의
#    내용도 아니다. 방향은 $P$ 의 좌고유벡터라는 **하나의 벡터**로 결정돼 있다.
# 2. 개별 사실을 $h$ 만큼 주입하는 건 $\pi$ 를 $s$ 쪽으로 $h$ 만큼 끌어당기는 것이라
#    고정점을 **선분 위에서 조금 움직일 뿐** 부호를 뒤집지 못한다.
#    코사인 유사도 $0.9988$ — 방향은 문자 그대로 그대로다.
# 3. 그리고 수렴만 $(1-h)$ 배로 느려진다. **감속**의 정체가 이것이다.
#    "가끔 사람이 확인한다"는 결국 "망가지는 데 더 오래 걸린다"일 뿐이다.
# 4. 방향을 바꾸려면 $P$ 를 건드려야 한다. 즉 **종류별 비율 상한/하한**이다.
#    3.8%의 개입으로 20% 주입보다 나은 결과가 나온 이유다.
# 5. 실무 함의: 매일 종류별 비율을 재는 쿼리 한 줄을 돌리고,
#    관계 > 55% 이면 쓰기를 멈추고 제약 < 10% 이면 경보를 울린다.
#    **이 지표가 없으면 "묽어지는" 것을 영영 못 본다.**
