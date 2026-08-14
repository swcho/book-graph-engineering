# %% [markdown]
# # `ex4_threshold_tuning.py`는 점수 분포를 어떻게 모의하는가
#
# 정답 한 줄:
#
# > 같은 쌍 400개는 $N(0.86,\ 0.11^2)$, 다른 쌍 9,600개는 $N(0.42,\ 0.15^2)$인
# > 정규분포로 만들고, 두 분포가 **겹치는 구간**을 남겨 둔다.
#
# 핵심은 세 가지다.
#
# 1. **두 개의 정규분포**로 «같은 쌍」과 «다른 쌍」의 점수를 따로 뽑는다.
# 2. 평균이 $0.86$ 대 $0.42$로 떨어져 있지만 표준편차가 $0.11,\ 0.15$라
#    꼬리가 서로 침범한다 — 즉 **한 임계로는 절대 깔끔하게 못 자른다**.
# 3. 개수 비가 $400 : 9{,}600 = 4\% : 96\%$ 다. 이 **클래스 불균형**이
#    정밀도를 깎는 주범이다.
#
# 아래에서 asset의 시뮬레이션을 시드까지 그대로 재현하고,
# 임계 스윕 표 → 이론값 대조 → ROC/PR → 기대비용 최소화까지 밟아 본다.

# %%
# 필요 패키지: numpy, scipy, plotly, kaleido
#   pip install numpy scipy plotly kaleido
import os
import random

import numpy as np
from scipy.stats import norm


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _HERE = os.getcwd()

print("준비 완료:", _HERE)
# 출력: 준비 완료: .../.fm/hints/846da6ba-8ab1-4868-9889-93251a0f6cdf


# %% [markdown]
# ## 1. asset의 시뮬레이션을 그대로 재현
#
# `ex4_threshold_tuning.py`의 해당 부분은 딱 네 줄이다.
#
# ```python
# random.seed(20260801)
# SAME = [min(1.0, max(0.0, random.gauss(0.86, 0.11))) for _ in range(400)]
# DIFF = [min(1.0, max(0.0, random.gauss(0.42, 0.15))) for _ in range(9_600)]
# ```
#
# - `random.gauss(mu, sigma)` — 평균 $\mu$, 표준편차 $\sigma$인 정규분포에서 한 개 뽑기.
# - `min(1.0, max(0.0, ...))` — 점수는 «닮은 정도」이므로 $[0,1]$ 밖으로 나가면 **자른다**(clip).
# - 시드를 박아 두었으니 몇 번 돌려도 같은 표가 나온다. 재현 가능한 실험의 최소 조건.

# %%
random.seed(20260801)

SAME = [min(1.0, max(0.0, random.gauss(0.86, 0.11))) for _ in range(400)]
DIFF = [min(1.0, max(0.0, random.gauss(0.42, 0.15))) for _ in range(9_600)]

same = np.array(SAME)
diff = np.array(DIFF)

print(f"같은 쌍 {len(SAME)}개  평균 {same.mean():.4f}  표준편차 {same.std(ddof=1):.4f}"
      f"  최소 {same.min():.4f}  최대 {same.max():.4f}")
print(f"다른 쌍 {len(DIFF):,}개  평균 {diff.mean():.4f}  표준편차 {diff.std(ddof=1):.4f}"
      f"  최소 {diff.min():.4f}  최대 {diff.max():.4f}")
print(f"양성 비율(=같은 쌍 비율) {len(SAME) / (len(SAME) + len(DIFF)):.2%}")
print(f"clip 으로 1.0 에 붙은 개수: {(same >= 1.0).sum()}개, "
      f"0.0 에 붙은 개수: {(diff <= 0.0).sum()}개")
# 출력: 같은 쌍 400개  평균 0.8495  표준편차 0.1022  최소 0.5722  최대 1.0000
# 출력: 다른 쌍 9,600개  평균 0.4208  표준편차 0.1513  최소 0.0000  최대 0.9760
# 출력: 양성 비율(=같은 쌍 비율) 4.00%
# 출력: clip 으로 1.0 에 붙은 개수: 34개, 0.0 에 붙은 개수: 21개
#
# 표본평균/표본표준편차가 지정값(0.86/0.11, 0.42/0.15) 근처에 붙는다.
# 다른 쌍은 0.4208/0.1513 로 거의 일치. 같은 쌍 평균이 0.8495 로 살짝 낮은 건
# **clip 때문**이다. 1.0 을 넘긴 34개가 전부 1.0 으로 눌리면서 평균을 끌어내린다.
# (표준오차는 각각 0.11/√400 ≈ 0.0055, 0.15/√9600 ≈ 0.0015)

# %% [markdown]
# ## 2. 겹치는 구간이 실제로 있는가
#
# 두 분포가 만나는 구간을 눈으로 확인한다.
# 「같은 쌍의 최솟값」과 「다른 쌍의 최댓값」 사이가 곧 **모호 구간**이다.

# %%
lo, hi = same.min(), diff.max()
print(f"같은 쌍 최솟값 {lo:.4f}  <  다른 쌍 최댓값 {hi:.4f}  → 구간 [{lo:.2f}, {hi:.2f}] 이 겹친다")

for t in (0.55, 0.65, 0.75, 0.85, 0.95):
    n_same = int((same >= t).sum())
    n_diff = int((diff >= t).sum())
    print(f"  임계 {t:.2f} 이상: 같은 쌍 {n_same:>3}개 / 다른 쌍 {n_diff:>4}개")
# 출력: 같은 쌍 최솟값 0.5722  <  다른 쌍 최댓값 0.9760  → 구간 [0.57, 0.98] 이 겹친다
# 출력:   임계 0.55 이상: 같은 쌍 400개 / 다른 쌍 1888개
# 출력:   임계 0.65 이상: 같은 쌍 390개 / 다른 쌍  638개
# 출력:   임계 0.75 이상: 같은 쌍 319개 / 다른 쌍  136개
# 출력:   임계 0.85 이상: 같은 쌍 211개 / 다른 쌍   24개
# 출력:   임계 0.95 이상: 같은 쌍  78개 / 다른 쌍    3개
#
# 임계 0.55 에서는 같은 쌍 400개를 다 잡지만 다른 쌍 1,888개가 같이 넘어온다 → 자동 병합하면 참사.
# 임계 0.95 로 올리면 다른 쌍은 3개뿐이지만 같은 쌍도 78개만 잡는다 → 322개를 놓친다.
# 겹침 구간이 [0.57, 0.98] 로 **점수 범위의 절반 가까이**다.
# «겹침이 있다」는 말은 곧 «한 임계로는 두 오류를 동시에 못 없앤다」는 말이다.

# %% [markdown]
# ## 3. 임계 스윕 — asset의 표를 복원
#
# asset은 임계를 **두 개** 둔다.
#
# - $s \ge \text{high}$ → 자동 병합
# - $s < \text{low}$ → 무시
# - $\text{low} \le s < \text{high}$ → 사람 검토
#
# 지표 정의는 이렇다. $S$는 같은 쌍(양성) 집합, $D$는 다른 쌍(음성) 집합.
#
# $$\text{TP} = |\{s \in S : s \ge \text{high}\}|,\quad
#   \text{FP} = |\{s \in D : s \ge \text{high}\}|$$
#
# $$\text{정밀도} = \frac{\text{TP}}{\text{TP}+\text{FP}},\qquad
#   \text{재현율} = \frac{\text{TP}}{|S|}$$
#
# 여기서 **FP = 오병합 수**, **FN = 놓침(= $s < \text{low}$ 인 양성)**,
# **사람 검토 = 두 임계 사이에 낀 전부**다.

# %%
def evaluate(high, low):
    tp = sum(1 for s in SAME if s >= high)
    fp = sum(1 for s in DIFF if s >= high)
    fn = sum(1 for s in SAME if s < low)
    review = sum(1 for s in SAME + DIFF if low <= s < high)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / len(SAME)
    return prec, rec, fp, fn, review


GRID = ((0.95, 0.80), (0.90, 0.70), (0.85, 0.55),
        (0.75, 0.55), (0.65, 0.50), (0.55, 0.50))

print(f"{'자동임계':>7} {'검토하한':>8} {'정밀도':>7} {'재현율':>7} "
      f"{'오병합':>7} {'놓침':>7} {'사람검토':>9}")
print("-" * 62)
rows = []
for high, low in GRID:
    p, r, fp, fn, rv = evaluate(high, low)
    rows.append((high, low, p, r, fp, fn, rv))
    print(f"{high:>7.2f} {low:>8.2f} {p:>7.3f} {r:>7.3f} {fp:>7,} {fn:>7,} {rv:>9,}")
# 출력:    자동임계     검토하한     정밀도     재현율     오병합      놓침      사람검토
# 출력: --------------------------------------------------------------
# 출력:    0.95     0.80   0.963   0.195       3     136       243
# 출력:    0.90     0.70   0.911   0.357      14      35       514
# 출력:    0.85     0.55   0.898   0.527      24       0     2,053
# 출력:    0.75     0.55   0.701   0.797     136       0     1,833
# 출력:    0.65     0.50   0.379   0.975     638       0     2,262
# 출력:    0.55     0.50   0.175   1.000   1,888       0     1,002
#
# 읽는 법 — 위에서 아래로 내려갈수록 «과감해진다».
#  - 0.95/0.80 → 정밀도 0.963, 오병합 3개. 대신 재현율 0.195 에 놓침 136개.
#    자동으로 처리한 게 78건뿐이니 «거의 다 사람에게 넘긴」 셈.
#  - 0.85/0.55 → 정밀도 0.898, 재현율 0.527. 놓침 0(모든 양성이 0.57 이상이라). 검토 2,053건.
#  - 0.75/0.55 → 재현율 0.797 로 뛰지만 오병합 136개. 정밀도 0.701 — 자동 병합 3건 중 1건이 오답.
#  - 0.55/0.50 → 재현율 1.000 이지만 정밀도 0.175. 자동 병합한 2,288건 중 1,888건이 «틀린 병합».
# 세 열(정밀도·오병합·사람검토)이 서로 반대로 움직인다. 공짜 점심이 없다는 게 표의 전부다.

# %% [markdown]
# ## 4. 이론값과 대조 — 정규분포 누적분포로 오류율 계산
#
# 시뮬레이션 숫자는 «표본」이다. 참값은 정규분포의 누적분포함수 $\Phi$로 바로 나온다.
# 표준화를 쓰면,
#
# $$P(S \ge t) = P\!\left(Z \ge \frac{t-\mu}{\sigma}\right) = 1 - \Phi\!\left(\frac{t-\mu}{\sigma}\right)$$
#
# 그래서 기대 개수는
#
# $$E[\text{TP}] = 400\left(1-\Phi\!\left(\tfrac{t-0.86}{0.11}\right)\right),\qquad
#   E[\text{FP}] = 9{,}600\left(1-\Phi\!\left(\tfrac{t-0.42}{0.15}\right)\right)$$
#
# clip 은 상관없다. $1.0$ 으로 잘린 값도 $t \le 1$ 이면 여전히 $t$ 이상이므로
# **위쪽 꼬리 확률은 clip 전과 같다**. (아래쪽도 마찬가지)

# %%
MU_S, SD_S, N_S = 0.86, 0.11, 400
MU_D, SD_D, N_D = 0.42, 0.15, 9_600

print(f"{'임계':>5} {'TP실측':>7} {'TP이론':>8} {'FP실측':>7} {'FP이론':>8} "
      f"{'정밀도실측':>10} {'정밀도이론':>10}")
print("-" * 64)
for t in (0.55, 0.65, 0.75, 0.85, 0.90, 0.95):
    tp_obs = int((same >= t).sum())
    fp_obs = int((diff >= t).sum())
    tp_th = N_S * norm.sf(t, MU_S, SD_S)       # sf = 1 - cdf (생존함수)
    fp_th = N_D * norm.sf(t, MU_D, SD_D)
    p_obs = tp_obs / (tp_obs + fp_obs) if tp_obs + fp_obs else 0.0
    p_th = tp_th / (tp_th + fp_th)
    print(f"{t:>5.2f} {tp_obs:>7} {tp_th:>8.1f} {fp_obs:>7} {fp_th:>8.1f} "
          f"{p_obs:>10.3f} {p_th:>10.3f}")
# 출력:    임계    TP실측     TP이론    FP실측     FP이론      정밀도실측      정밀도이론
# 출력: ----------------------------------------------------------------
# 출력:  0.55     400    399.0    1888   1853.4      0.175      0.177
# 출력:  0.65     390    388.7     638    600.9      0.379      0.393
# 출력:  0.75     319    336.5     136    133.5      0.701      0.716
# 출력:  0.85     211    214.5      24     19.9      0.898      0.915
# 출력:  0.90     143    143.2      14      6.6      0.911      0.956
# 출력:  0.95      78     82.7       3      2.0      0.963      0.977
#
# 이론과 실측이 잘 맞는다. 시뮬레이션은 «정규분포 가정을 표본으로 실현한 것」에 불과함이 확인된다.
# 어긋나는 곳은 전부 **꼬리**다. t=0.90 의 FP 기대값이 6.6 인데 실측 14 —
# 개수가 한 자릿수면 포아송 요동(표준편차 ≈ √6.6 ≈ 2.6)이 상대적으로 크다.
# 교훈 두 개:
#  1) 「오병합 0건 관측」은 「오병합 확률 0」이 아니다. 표본이 작아서 안 보였을 수 있다.
#  2) 그래서 임계는 관측 표뿐 아니라 **이론 꼬리 확률**로도 검산해야 한다.

# %% [markdown]
# ## 5. 클래스 불균형이 정밀도를 깎는 방식
#
# 각 쌍 하나만 보면 임계 $0.85$ 에서 다른 쌍이 넘어올 확률은
#
# $$1-\Phi\!\left(\frac{0.85-0.42}{0.15}\right) = 1-\Phi(2.87) \approx 0.0021$$
#
# 0.2%다. 아주 좋아 보인다. 그런데 다른 쌍이 **9,600개**다.
# $9{,}600 \times 0.00207 \approx 20$개가 넘어온다. 양성은 400개뿐이고
# 그중 임계를 넘는 건 약 214개니, 오병합 20개는 무시할 수 없다.
#
# 정밀도를 베이즈 형태로 쓰면 원인이 드러난다. 양성 비율(사전확률)을 $\pi$라 하면
#
# $$\text{정밀도} = \frac{\pi \cdot \text{TPR}}{\pi \cdot \text{TPR} + (1-\pi)\cdot \text{FPR}}$$
#
# $\pi$가 작아질수록 분모의 두 번째 항이 커진다. **분류기 성능은 그대로인데 정밀도만 떨어진다.**

# %%
def precision_at(t, pi):
    """양성 비율 pi 일 때의 이론 정밀도."""
    tpr = norm.sf(t, MU_S, SD_S)
    fpr = norm.sf(t, MU_D, SD_D)
    return pi * tpr / (pi * tpr + (1 - pi) * fpr)


print(f"{'임계':>5} {'TPR':>7} {'FPR':>8} | " + " ".join(f"{f'π={p:.0%}':>9}" for p in (0.5, 0.2, 0.04, 0.01)))
print("-" * 64)
for t in (0.65, 0.75, 0.85, 0.95):
    tpr, fpr = norm.sf(t, MU_S, SD_S), norm.sf(t, MU_D, SD_D)
    cells = " ".join(f"{precision_at(t, p):>9.3f}" for p in (0.5, 0.2, 0.04, 0.01))
    print(f"{t:>5.2f} {tpr:>7.3f} {fpr:>8.5f} | {cells}")
# 출력:    임계     TPR      FPR |     π=50%     π=20%      π=4%      π=1%
# 출력: ----------------------------------------------------------------
# 출력:  0.65   0.972  0.06260 |     0.939     0.795     0.393     0.136
# 출력:  0.75   0.841  0.01390 |     0.984     0.938     0.716     0.379
# 출력:  0.85   0.536  0.00207 |     0.996     0.985     0.915     0.723
# 출력:  0.95   0.207  0.00021 |     0.999     0.996     0.977     0.910
#
# 같은 임계 0.65 에서 정밀도가 0.939(균형) → 0.393(4%) → 0.136(1%) 로 무너진다.
# 분류기는 하나도 안 변했다. TPR 0.972, FPR 0.0626 는 세 열에서 동일하다.
# 바뀐 건 «후보 중 진짜의 비율」뿐이다.
# 임계 0.85 의 FPR 은 0.00207 — 0.2%다. 그런데 9,600 × 0.00207 ≈ 20개가 넘어온다.
# 실무 함의: 블로킹으로 후보 쌍 수를 줄이면(π 를 키우면) 같은 점수 모델로도 정밀도가 오른다.
# 14장이 블로킹(ex1)과 임계(ex4)를 같은 장에 둔 이유다.

# %% [markdown]
# ## 6. ROC 와 PR 곡선
#
# - **ROC**: $x=\text{FPR}$, $y=\text{TPR}$. 클래스 비율과 무관 → 불균형을 «숨긴다».
# - **PR**: $x=\text{재현율}$, $y=\text{정밀도}$. 불균형을 그대로 보여 준다.
#
# 불균형 문제에서 ROC-AUC만 보고 «성능 좋다」고 하면 낚인다. 아래 숫자가 그 증거다.

# %%
ts = np.linspace(0.0, 1.0001, 1001)
tpr_curve = np.array([(same >= t).mean() for t in ts])
fpr_curve = np.array([(diff >= t).mean() for t in ts])
tp_curve = tpr_curve * N_S
fp_curve = fpr_curve * N_D
with np.errstate(invalid="ignore", divide="ignore"):
    prec_curve = np.where(tp_curve + fp_curve > 0, tp_curve / (tp_curve + fp_curve), 1.0)

# AUC (FPR 증가 방향으로 정렬해 사다리꼴 적분)
order = np.argsort(fpr_curve)
roc_auc = np.trapezoid(tpr_curve[order], fpr_curve[order])
order_r = np.argsort(tpr_curve)
pr_auc = np.trapezoid(prec_curve[order_r], tpr_curve[order_r])

print(f"ROC-AUC = {roc_auc:.4f}   (1.0 이 완벽, 0.5 가 동전던지기)")
print(f"PR-AUC  = {pr_auc:.4f}   (양성 비율 0.04 가 무작위 기준선)")
print(f"두 정규분포의 이론 AUC = {norm.cdf((MU_S - MU_D) / np.hypot(SD_S, SD_D)):.4f}")
# 출력: ROC-AUC = 0.9903   (1.0 이 완벽, 0.5 가 동전던지기)
# 출력: PR-AUC  = 0.8300   (양성 비율 0.04 가 무작위 기준선)
# 출력: 두 정규분포의 이론 AUC = 0.9910
#
# ROC-AUC 0.990 — «거의 완벽한 모델»처럼 보인다. 실제로는 위 표에서 봤듯이
# 임계 0.65 에서 정밀도가 0.379 로 무너진다. ROC 는 그 사실을 전혀 안 보여 준다.
# PR-AUC 0.830 이 그보다 정직한 요약이다(무작위 기준선은 0.04).
# 이론 AUC 는 Φ((μ_S-μ_D)/√(σ_S²+σ_D²)) = Φ(0.44/0.1860) = Φ(2.366) = 0.9910 으로 바로 나온다.
# 시뮬레이션 0.9903 과 소수점 셋째 자리까지 맞는다 — 모의가 의도대로 됐다는 뜻.

# %% [markdown]
# ## 7. 기대비용 최소화 — «임계를 어디에 둘 것인가»
#
# asset이 준 숫자를 그대로 쓴다.
#
# - 사람 한 건 검토: 400원
# - 오병합 하나 수습: 2시간 ≈ 검토 180건 ≈ 72,000원
# - 놓침 하나: 여기서는 검토 5건(2,000원)으로 가정 — 나중에 발견되면 다시 붙이면 되니 싸다
#
# 총비용은
#
# $$C(\text{high}) = c_{\text{fp}}\cdot \text{FP}(\text{high}) + c_{\text{rv}}\cdot \text{Review}(\text{high}) + c_{\text{fn}}\cdot \text{FN}(\text{low})$$
#
# 이 함수를 임계에 대해 최소화하면 «어디」가 답으로 나온다.
# 되돌리기가 싸지면($c_{\text{fp}}$ 가 5분 ≈ 3,000원) 최적 임계가 어떻게 내려가는지도 본다.
# `low` 는 $0.70$ 으로 고정한다 — FN 은 `low` 만으로 정해지므로 `high` 최적화에는 상수다.

# %%
C_REVIEW, C_FN = 400, 2_000
LOW = 0.70
highs = np.round(np.arange(0.71, 0.996, 0.005), 3)

FN_FIXED = int((same < LOW).sum())   # low 로만 결정된다. high 와 무관.
print(f"놓침(FN) = {FN_FIXED}개 — low={LOW} 가 정하며 high 를 어디에 두든 변하지 않는다\n")


def cost_parts(h, c_fp):
    fp = int((diff >= h).sum())
    rv = int(((same >= LOW) & (same < h)).sum() + ((diff >= LOW) & (diff < h)).sum())
    return c_fp * fp, C_REVIEW * rv, C_FN * FN_FIXED, fp, rv


def cost_curve(c_fp):
    return np.array([sum(cost_parts(h, c_fp)[:3]) for h in highs], dtype=float)


for label, c_fp in (("되돌리기 비쌈 (2시간 = 72,000원)", 72_000),
                    ("되돌리기 쌈 (5분 = 3,000원)", 3_000)):
    print(label)
    print(f"  {'임계':>5} {'오병합':>6} {'검토':>6} {'오병합비용':>12} {'검토비용':>10} {'총비용':>12}")
    for h in (0.75, 0.80, 0.85, 0.90, 0.95, 0.99):
        c1, c2, c3, fp, rv = cost_parts(h, c_fp)
        print(f"  {h:>5.2f} {fp:>6,} {rv:>6,} {c1:>12,} {c2:>10,} {c1 + c2 + c3:>12,}")
    curve = cost_curve(c_fp)
    i = int(curve.argmin())
    h = float(highs[i])
    p, r, fp, fn, rv = evaluate(h, LOW)
    print(f"  → 최적 자동임계 {h:.3f}, 총비용 {curve[i]:,.0f}원 "
          f"(정밀도 {p:.3f} 재현율 {r:.3f} 오병합 {fp} 검토 {rv:,})\n")
# 출력: 놓침(FN) = 35개 — low=0.7 가 정하며 high 를 어디에 두든 변하지 않는다
# 출력:
# 출력: 되돌리기 비쌈 (2시간 = 72,000원)
# 출력:      임계    오병합     검토        오병합비용       검토비용          총비용
# 출력:    0.75    136    216    9,792,000     86,400    9,948,400
# 출력:    0.80     60    347    4,320,000    138,800    4,528,800
# 출력:    0.85     24    436    1,728,000    174,400    1,972,400
# 출력:    0.90     14    514    1,008,000    205,600    1,283,600
# 출력:    0.95      3    590      216,000    236,000      522,000
# 출력:    0.99      0    633            0    253,200      323,200
# 출력:   → 최적 자동임계 0.980, 총비용 318,800원 (정밀도 1.000 재현율 0.122 오병합 0 검토 622)
# 출력:
# 출력: 되돌리기 쌈 (5분 = 3,000원)
# 출력:      임계    오병합     검토        오병합비용       검토비용          총비용
# 출력:    0.75    136    216      408,000     86,400      564,400
# 출력:    0.80     60    347      180,000    138,800      388,800
# 출력:    0.85     24    436       72,000    174,400      316,400
# 출력:    0.90     14    514       42,000    205,600      317,600
# 출력:    0.95      3    590        9,000    236,000      315,000
# 출력:    0.99      0    633            0    253,200      323,200
# 출력:   → 최적 자동임계 0.860, 총비용 310,000원 (정밀도 0.910 재현율 0.502 오병합 20 검토 450)
#
# 되돌리기 비용이 24배(72,000 vs 3,000) 차이 나면 최적 임계가 0.980 → 0.860 으로 내려간다.
# 비싼 쪽: 0.75 의 총비용 995만 원 vs 0.99 의 32만 원 — 30배 차이. 오병합 항이 압도한다.
#         → «무조건 임계를 올린다»가 정답. 재현율 0.122 를 감수한다.
# 싼 쪽:   0.85~0.99 총비용이 31만 원대로 거의 평평하다.
#         → 임계를 내려도 손해가 없다. 재현율이 0.122 → 0.502 로 4배가 되는데 비용은 그대로.
# 「임계를 높게 잡는다」는 asset의 결론은 «되돌리기가 비싼 경우」의 답일 뿐이고,
# unmerge 가 대입 한 번(ex3)이면 계산이 뒤집힌다.
# 즉 임계는 «모델 성능»이 아니라 **비용 구조**가 정한다.

# %% [markdown]
# ## 8. 그림 — 겹침 / ROC / PR / 비용

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=("① 점수 분포와 겹치는 구간",
                    "② ROC (불균형을 숨긴다)",
                    "③ PR (불균형이 드러난다)",
                    "④ 기대비용 vs 자동임계"),
)

bins = dict(start=0.0, end=1.0, size=0.02)
fig.add_trace(go.Histogram(x=diff, xbins=bins, name="다른 쌍 9,600",
                           marker_color="#8899bb", opacity=0.75), row=1, col=1)
fig.add_trace(go.Histogram(x=same, xbins=bins, name="같은 쌍 400",
                           marker_color="#d9534f", opacity=0.75), row=1, col=1)
fig.add_vrect(x0=float(same.min()), x1=float(diff.max()), row=1, col=1,
              fillcolor="#f0ad4e", opacity=0.18, line_width=0,
              annotation_text="겹침 구간", annotation_position="top left")
fig.update_yaxes(type="log", title_text="개수(로그)", row=1, col=1)
fig.update_xaxes(title_text="점수", row=1, col=1)

fig.add_trace(go.Scatter(x=fpr_curve[order], y=tpr_curve[order], mode="lines",
                         name=f"ROC (AUC={roc_auc:.3f})",
                         line=dict(color="#0275d8")), row=1, col=2)
fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", showlegend=False,
                         line=dict(color="#bbbbbb", dash="dot")), row=1, col=2)
fig.update_xaxes(title_text="FPR", row=1, col=2)
fig.update_yaxes(title_text="TPR", row=1, col=2)

fig.add_trace(go.Scatter(x=tpr_curve, y=prec_curve, mode="lines",
                         name=f"PR (AUC={pr_auc:.3f})",
                         line=dict(color="#5cb85c")), row=2, col=1)
fig.add_hline(y=N_S / (N_S + N_D), row=2, col=1, line=dict(color="#bbbbbb", dash="dot"),
              annotation_text="무작위 기준선 0.04", annotation_position="bottom right")
fig.update_xaxes(title_text="재현율", row=2, col=1)
fig.update_yaxes(title_text="정밀도", range=[0, 1.05], row=2, col=1)

for label, c_fp, color in (("되돌리기 비쌈", 72_000, "#d9534f"),
                           ("되돌리기 쌈", 3_000, "#5bc0de")):
    curve = cost_curve(c_fp)
    fig.add_trace(go.Scatter(x=highs, y=curve, mode="lines", name=label,
                             line=dict(color=color)), row=2, col=2)
    i = int(curve.argmin())
    fig.add_trace(go.Scatter(x=[highs[i]], y=[curve[i]], mode="markers",
                             showlegend=False,
                             marker=dict(color=color, size=11, symbol="star")), row=2, col=2)
fig.update_xaxes(title_text="자동 병합 임계", row=2, col=2)
fig.update_yaxes(type="log", title_text="총비용(원, 로그)", row=2, col=2)

fig.update_layout(barmode="overlay", height=760, width=1080,
                  title_text="ex4_threshold_tuning.py — 두 정규분포 모의와 임계의 대가",
                  template="plotly_white")

_show(fig)
fig.write_image(os.path.join(_HERE, "expy.png"), scale=2)
print("저장:", os.path.join(_HERE, "expy.png"))
# 출력: 저장: .../.fm/hints/846da6ba-8ab1-4868-9889-93251a0f6cdf/expy.png

# %% [markdown]
# ## 정리
#
# | 질문 | 답 |
# |---|---|
# | 같은 쌍 | 400개, $N(0.86,\ 0.11^2)$, $[0,1]$ 로 clip |
# | 다른 쌍 | 9,600개, $N(0.42,\ 0.15^2)$, $[0,1]$ 로 clip |
# | 왜 정규분포 두 개? | 실제 점수 분포의 모양 — 높은 쪽/낮은 쪽에 몰리되 **겹친다** |
# | 왜 겹치게? | 겹침이 없으면 임계 하나로 끝난다. 겹치니까 «두 임계 + 사람」이 필요해진다 |
# | 왜 4 : 96? | 클래스 불균형. FPR 0.2%도 9,600을 곱하면 오병합 20건이 된다 |
# | 임계는 어떻게 정하나? | 모델 성능이 아니라 «오병합 수습 비용 : 검토 비용» 비율로 정한다 |
#
# 한 문장으로: **겹치는 두 정규분포 + 4% 양성 비율**로 «한 임계로는 못 자르는」 현실을
# 재현해, 임계 이동이 정밀도·재현율·사람 부담을 어떻게 맞바꾸는지 보게 만든 모의다.
