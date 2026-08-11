# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# 실행: python3 expy.py   또는 VSCode에서 셀 단위 실행
#
# 투영 엣지 수의 상한 공식  n * k(k-1)/2  를 단계적으로 확인한다.

# %% [markdown]
# # 투영 엣지 수의 상한: $n \times \frac{k(k-1)}{2}$
#
# 이분 그래프 `(사용자)-[:구매]->(상품)` 를 상품 쪽으로 투영하면
# 「함께 산 상품끼리 잇기」 그래프가 나온다.
#
# 사용자 한 명이 상품 $k$개를 샀으면, 그 사용자가 만드는 짝은
#
# $$\binom{k}{2} = \frac{k(k-1)}{2}$$
#
# 사용자가 $n$명이면 전부 더해서
#
# $$n \times \frac{k(k-1)}{2}$$
#
# 이게 **상한**이다. 같은 짝이 여러 번 만들어져도 엣지는 하나로 합쳐지므로
# 실제 엣지 수는 이보다 적다.

# %%
from collections import defaultdict
from itertools import combinations
import os
import random


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
# ## 1단계 — 원본 이분 그래프
#
# 원문 `ex4_bipartite.py` 와 같은 데이터.

# %%
PURCHASES = [
    ("u1", "상품A"), ("u1", "상품B"),
    ("u2", "상품A"), ("u2", "상품B"), ("u2", "상품C"),
    ("u3", "상품C"),
]

users = sorted({u for u, _ in PURCHASES})
items = sorted({i for _, i in PURCHASES})
print(f"사용자 {len(users)}명: {users}")
print(f"상품   {len(items)}개: {items}")
print(f"엣지   {len(PURCHASES)}개")
# 출력: 사용자 3명: ['u1', 'u2', 'u3']
# 출력: 상품   3개: ['상품A', '상품B', '상품C']
# 출력: 엣지   6개

# %% [markdown]
# ## 2단계 — 투영해 보기
#
# 같은 사용자를 공유하는 상품끼리 잇는다. 가중치는 「함께 산 사람 수」.

# %%
def project(pairs, side=1):
    """side=1 이면 오른쪽(상품) 쪽으로 투영."""
    grouped = defaultdict(set)
    for a, b in pairs:
        key, val = (a, b) if side == 0 else (b, a)
        grouped[val].add(key)
    out = defaultdict(int)
    attempts = 0
    for _val, keys in grouped.items():
        for x, y in combinations(sorted(keys), 2):
            out[(x, y)] += 1
            attempts += 1
    return dict(out), attempts


proj, attempts = project(PURCHASES, side=1)
for (a, b), w in sorted(proj.items()):
    print(f"  {a} — {b}  (함께 산 사람 {w}명)")
print(f"\n짝 생성 시도 = {attempts}회,  실제 엣지 = {len(proj)}개")
# 출력:   상품A — 상품B  (함께 산 사람 2명)
# 출력:   상품A — 상품C  (함께 산 사람 1명)
# 출력:   상품B — 상품C  (함께 산 사람 1명)
# 출력:
# 출력: 짝 생성 시도 = 4회,  실제 엣지 = 3개

# %% [markdown]
# 시도는 4회인데 엣지는 3개다. `상품A—상품B` 짝이 `u1`, `u2` 에서 두 번
# 만들어졌지만 엣지 하나로 합쳐지고 가중치만 2가 되었다.
#
# **이것이 공식이 「상한」인 이유다.**

# %% [markdown]
# ## 3단계 — 공식과 실제 시도 횟수가 일치하는지 확인
#
# 사용자별 구매 수 $k_u$ 를 알면 시도 횟수는 정확히
#
# $$\sum_u \frac{k_u(k_u-1)}{2}$$

# %%
k_per_user = defaultdict(int)
for u, _ in PURCHASES:
    k_per_user[u] += 1

formula = sum(k * (k - 1) // 2 for k in k_per_user.values())
for u in users:
    k = k_per_user[u]
    print(f"  {u}: k={k} → C(k,2) = {k*(k-1)//2}")
print(f"\n공식 합계 = {formula},  실측 시도 = {attempts},  일치? {formula == attempts}")
print(f"실제 엣지 = {len(proj)}  (상한 {formula} 이하)")
# 출력:   u1: k=2 → C(k,2) = 1
# 출력:   u2: k=3 → C(k,2) = 3
# 출력:   u3: k=1 → C(k,2) = 0
# 출력:
# 출력: 공식 합계 = 4,  실측 시도 = 4,  일치? True
# 출력: 실제 엣지 = 3  (상한 4 이하)

# %% [markdown]
# ## 4단계 — 원문의 폭발 표 재현
#
# 모두가 똑같이 $k$개씩 산다고 가정한 균등 케이스.

# %%
def simulate(n_users, items_per_user):
    return n_users * items_per_user * (items_per_user - 1) // 2


print(f"{'사용자':>10} {'1인당 구매':>10} {'투영 엣지(최대)':>18}")
for n, k in ((1_000, 10), (1_000, 50), (100_000, 50), (100_000, 200)):
    print(f"{n:>10,} {k:>10} {simulate(n, k):>18,}")
# 출력:        사용자     1인당 구매      투영 엣지(최대)
# 출력:      1,000         10             45,000
# 출력:      1,000         50          1,225,000
# 출력:    100,000         50        122,500,000
# 출력:    100,000        200      1,990,000,000

# %% [markdown]
# ## 5단계 — 어느 축이 위험한가
#
# $n$에 대해서는 1차, $k$에 대해서는 2차다. 배율로 확인한다.

# %%
base = simulate(1_000, 10)
print(f"기준 n=1,000 k=10 → {base:,}\n")
print(f"n 만 10배 (10,000, 10) → {simulate(10_000, 10):,}"
      f"  배율 {simulate(10_000,10)/base:.1f}x")
print(f"k 만 10배 (1,000, 100) → {simulate(1_000, 100):,}"
      f"  배율 {simulate(1_000,100)/base:.1f}x")
# 출력: 기준 n=1,000 k=10 → 45,000
# 출력:
# 출력: n 만 10배 (10,000, 10) → 450,000  배율 10.0x
# 출력: k 만 10배 (1,000, 100) → 4,950,000  배율 110.0x

# %% [markdown]
# 같은 10배인데 $n$은 10배, $k$는 110배($\approx 10^2$)다.
# **1인당 구매 수가 진짜 위험한 축이다.**

# %% [markdown]
# ## 6단계 — 상품 종류 수에 의한 두 번째 상한
#
# 상품이 $m$종류뿐이면 가능한 짝 자체가 $\binom{m}{2}$ 개로 제한된다.
#
# $$|E| \le \min\!\left(n\cdot\frac{k(k-1)}{2},\ \frac{m(m-1)}{2}\right)$$

# %%
for n, k, m in ((100_000, 200, 1_000), (100_000, 200, 1_000_000)):
    a = simulate(n, k)
    b = m * (m - 1) // 2
    print(f"n={n:,} k={k} m={m:,}")
    print(f"   n·C(k,2) = {a:,}")
    print(f"   C(m,2)   = {b:,}")
    print(f"   → 실질 상한 {min(a,b):,}  (지배하는 쪽: "
          f"{'상품 종류 수' if b < a else '사용자·구매 수'})")
# 출력: n=100,000 k=200 m=1,000
# 출력:    n·C(k,2) = 1,990,000,000
# 출력:    C(m,2)   = 499,500
# 출력:    → 실질 상한 499,500  (지배하는 쪽: 상품 종류 수)
# 출력: n=100,000 k=200 m=1,000,000
# 출력:    n·C(k,2) = 1,990,000,000
# 출력:    C(m,2)   = 499,999,500,000
# 출력:    → 실질 상한 1,990,000,000  (지배하는 쪽: 사용자·구매 수)

# %% [markdown]
# 카탈로그가 작으면 $\binom{m}{2}$ 가 목을 죈다. 그래도
# $n\cdot\binom{k}{2}$ 가 중요한 이유는, **짝을 만들어 보는 계산 자체**는
# 중복 여부와 무관하게 그 횟수만큼 돌기 때문이다. 메모리 피크와 계산 시간은
# $n\cdot k^2$ 에 비례한다.

# %% [markdown]
# ## 7단계 — 평균으로 계산하면 과소평가된다 (옌센 부등식)
#
# $k^2$ 은 아래로 볼록하므로
#
# $$\frac{1}{n}\sum_u k_u^2 \ \ge\ \bar{k}^2$$
#
# 과소평가분은 분산으로 정확히 표현된다.
#
# $$\sum_u \frac{k_u(k_u-1)}{2} = \frac{n}{2}\left(\bar{k}^2 + V(k) - \bar{k}\right)$$
#
# 즉 평균만 쓰면 $\dfrac{n\,V(k)}{2}$ 만큼 덜 잡는다.

# %%
def exact_attempts(ks):
    return sum(k * (k - 1) // 2 for k in ks)


def avg_estimate(ks):
    n = len(ks)
    kbar = sum(ks) / n
    return n * kbar * (kbar - 1) / 2


def variance(ks):
    n = len(ks)
    kbar = sum(ks) / n
    return sum((k - kbar) ** 2 for k in ks) / n


cases = {
    "균등 (모두 50개)": [50] * 1000,
    "약한 편차 (30~70)": None,
    "헤비테일 (파레토)": None,
    "봇 1개 섞임": [10] * 999 + [50_000],
}

random.seed(7)
cases["약한 편차 (30~70)"] = [random.randint(30, 70) for _ in range(1000)]
cases["헤비테일 (파레토)"] = [
    max(1, int(3 * (random.paretovariate(1.4)))) for _ in range(1000)
]

for name, ks in cases.items():
    ex = exact_attempts(ks)
    es = avg_estimate(ks)
    v = variance(ks)
    gap = len(ks) * v / 2
    print(f"[{name}]")
    print(f"  평균 k = {sum(ks)/len(ks):.1f},  분산 V(k) = {v:,.1f}")
    print(f"  평균 기반 추정 = {es:15,.0f}")
    print(f"  정확한 시도    = {ex:15,}   ({ex/es:.2f}배)")
    print(f"  이론 격차 n·V/2 = {gap:14,.0f}  (실측 격차 {ex-es:,.0f})")
# 출력: [균등 (모두 50개)]
# 출력:   평균 k = 50.0,  분산 V(k) = 0.0
# 출력:   평균 기반 추정 =       1,225,000
# 출력:   정확한 시도    =       1,225,000   (1.00배)
# 출력:   이론 격차 n·V/2 =              0  (실측 격차 0)
# 출력: [약한 편차 (30~70)]
# 출력:   평균 k = 49.4,  분산 V(k) = 136.9
# 출력:   평균 기반 추정 =       1,194,698
# 출력:   정확한 시도    =       1,263,147   (1.06배)
# 출력:   이론 격차 n·V/2 =         68,449  (실측 격차 68,449)
# 출력: [헤비테일 (파레토)]
# 출력:   평균 k = 8.0,  분산 V(k) = 177.4
# 출력:   평균 기반 추정 =          28,225
# 출력:   정확한 시도    =         116,921   (4.14배)
# 출력:   이론 격차 n·V/2 =         88,696  (실측 격차 88,696)
# 출력: [봇 1개 섞임]
# 출력:   평균 k = 60.0,  분산 V(k) = 2,496,501.1
# 출력:   평균 기반 추정 =       1,769,405
# 출력:   정확한 시도    =   1,250,019,955   (706.46배)
# 출력:   이론 격차 n·V/2 =  1,248,250,550  (실측 격차 1,248,250,550)

# %% [markdown]
# 봇 계정 **하나**가 전체 시도 횟수를 700배로 만든다. 헤비테일에서도 15배다.
# 「평균 구매 수로 용량 산정했는데 운영에서 죽었다」의 정체가 이것이다.

# %% [markdown]
# ## 8단계 — 임계값 절단의 효과
#
# 「함께 산 사람 $N$명 이상」만 남기면 엣지가 얼마나 줄어드는지.

# %%
random.seed(11)
N_USERS, N_ITEMS, K = 2_000, 300, 20
# 인기 편향(멱법칙 비슷하게) 상품을 뽑는다
weights = [1.0 / (r + 1) ** 0.8 for r in range(N_ITEMS)]
item_names = [f"i{r:03d}" for r in range(N_ITEMS)]

pairs = []
for u in range(N_USERS):
    picked = set()
    while len(picked) < K:
        picked.add(random.choices(item_names, weights=weights, k=1)[0])
    for it in picked:
        pairs.append((f"u{u}", it))

proj_big, attempts_big = project(pairs, side=1)
upper = N_USERS * K * (K - 1) // 2
print(f"상한 n·C(k,2) = {upper:,}")
print(f"실측 시도      = {attempts_big:,}")
print(f"고유 엣지      = {len(proj_big):,}  (상한의 {len(proj_big)/upper*100:.1f}%)")
print(f"C(m,2) 상한    = {N_ITEMS*(N_ITEMS-1)//2:,}\n")

thresholds = [1, 2, 3, 5, 10, 20, 50]
kept = []
for t in thresholds:
    c = sum(1 for w in proj_big.values() if w >= t)
    kept.append(c)
    print(f"  가중치 >= {t:>3} → 엣지 {c:>7,}  (노드 {N_ITEMS}개의 {c/N_ITEMS:>6.1f}배)")
# 출력: 상한 n·C(k,2) = 380,000
# 출력: 실측 시도      = 380,000
# 출력: 고유 엣지      = 40,782  (상한의 10.7%)
# 출력: C(m,2) 상한    = 44,850
# 출력:
# 출력:   가중치 >=   1 → 엣지  40,782  (노드 300개의  135.9배)
# 출력:   가중치 >=   2 → 엣지  33,978  (노드 300개의  113.3배)
# 출력:   가중치 >=   3 → 엣지  27,134  (노드 300개의   90.4배)
# 출력:   가중치 >=   5 → 엣지  17,809  (노드 300개의   59.4배)
# 출력:   가중치 >=  10 → 엣지   8,695  (노드 300개의   29.0배)
# 출력:   가중치 >=  20 → 엣지   3,938  (노드 300개의   13.1배)
# 출력:   가중치 >=  50 → 엣지   1,106  (노드 300개의    3.7배)

# %% [markdown]
# 읽을 점 세 가지.
#
# - **상한 380,000 → 고유 엣지 40,782 (10.7%)**. 중복이 합쳐져 실제는 상한의
#   1/10 수준이다. 「상한이 이렇다」는 말의 뜻이 이것이다.
# - 여기서는 상품이 300개뿐이라 $\binom{m}{2}=44{,}850$ 이 두 번째 상한으로
#   작동한다. 고유 엣지가 이미 그 91%까지 차 있다 — 사실상 완전 그래프에 가깝다.
# - 원문의 「엣지 수가 **노드 수의 20배**를 넘지 않게」 기준을 맞추려면
#   임계값을 15~20 정도로 잡아야 한다. 임계값 20에서 13.1배로 들어온다.

# %% [markdown]
# ## 9단계 — 시각화
#
# 세 장으로 나눠 본다.
#
# 1. $k$에 대한 2차 성장 vs $n$에 대한 1차 성장
# 2. 상한과 실제 엣지 수의 벌어짐
# 3. 평균 기반 추정의 과소평가 (옌센)
# 4. 임계값 절단 효과

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "① 같은 배율로 늘렸을 때 (log-log, 기울기가 차수)",
        "② 상한 vs 실제 고유 엣지 (log y)",
        "③ 평균으로 계산하면 과소평가",
        "④ 가중치 임계값 절단 효과",
    ),
    vertical_spacing=0.16, horizontal_spacing=0.11,
)

# --- ① 배율 비교: log-log 에서 기울기 = 차수 ---
BASE_N, BASE_K = 1_000, 20
base_val = simulate(BASE_N, BASE_K)
cs = [1, 1.5, 2, 3, 5, 8, 10, 15, 20]
fig.add_trace(go.Scatter(
    x=cs, y=[simulate(BASE_N, int(BASE_K * c)) / base_val for c in cs],
    name="k 를 c배 → 약 c² 배 (기울기 2)", mode="lines+markers",
    line=dict(color="#2563eb", width=3), marker=dict(size=8),
    hovertemplate="c=%{x}배 → 상한 %{y:.1f}배<extra></extra>",
), row=1, col=1)
fig.add_trace(go.Scatter(
    x=cs, y=[simulate(int(BASE_N * c), BASE_K) / base_val for c in cs],
    name="n 을 c배 → 정확히 c배 (기울기 1)", mode="lines+markers",
    line=dict(color="#dc2626", width=3, dash="dash"), marker=dict(size=8),
    hovertemplate="c=%{x}배 → 상한 %{y:.1f}배<extra></extra>",
), row=1, col=1)
fig.update_xaxes(title_text="배율 c (기준 n=1,000 k=20)", type="log", row=1, col=1)
fig.update_yaxes(title_text="상한이 몇 배가 되는가", type="log", row=1, col=1)

# --- ② 상한 vs 실제 ---
k_grid = [5, 10, 20, 30, 40]
uppers, actuals = [], []
random.seed(3)
M_ITEMS, N_U = 200, 500
inames = [f"x{r}" for r in range(M_ITEMS)]
wts = [1.0 / (r + 1) ** 0.7 for r in range(M_ITEMS)]
for k in k_grid:
    ps = []
    for u in range(N_U):
        picked = set()
        while len(picked) < k:
            picked.add(random.choices(inames, weights=wts, k=1)[0])
        ps += [(f"u{u}", it) for it in picked]
    pr, _ = project(ps, side=1)
    uppers.append(N_U * k * (k - 1) // 2)
    actuals.append(len(pr))

fig.add_trace(go.Bar(
    x=[str(k) for k in k_grid], y=uppers, name="상한 n·C(k,2)",
    marker_color="#93c5fd",
), row=1, col=2)
fig.add_trace(go.Bar(
    x=[str(k) for k in k_grid], y=actuals, name="실제 고유 엣지",
    marker_color="#1d4ed8",
), row=1, col=2)
fig.add_trace(go.Scatter(
    x=[str(k) for k in k_grid], y=[M_ITEMS * (M_ITEMS - 1) // 2] * len(k_grid),
    name="C(m,2) 포화선", mode="lines",
    line=dict(color="#ea580c", width=2, dash="dot"),
), row=1, col=2)
fig.update_xaxes(title_text="1인당 구매 k (사용자 500명, 상품 200종)", row=1, col=2)
fig.update_yaxes(title_text="엣지 수 (log)", type="log", row=1, col=2)

# --- ③ 옌센: 평균 추정 vs 정확 ---
labels = list(cases.keys())
est = [avg_estimate(cases[c]) for c in labels]
ex_ = [exact_attempts(cases[c]) for c in labels]
fig.add_trace(go.Bar(
    x=labels, y=est, name="평균 k 기반 추정", marker_color="#fca5a5",
), row=2, col=1)
fig.add_trace(go.Bar(
    x=labels, y=ex_, name="정확한 Σ C(k_u,2)", marker_color="#b91c1c",
), row=2, col=1)
fig.update_yaxes(title_text="짝 생성 시도 (log)", type="log", row=2, col=1)

# --- ④ 임계값 절단 ---
fig.add_trace(go.Scatter(
    x=thresholds, y=kept, mode="lines+markers", name="남는 엣지",
    line=dict(color="#059669", width=3), marker=dict(size=9),
), row=2, col=2)
fig.add_trace(go.Scatter(
    x=thresholds, y=[N_ITEMS * 20] * len(thresholds),
    mode="lines", name="노드 수 × 20 (원문 기준)",
    line=dict(color="#7c3aed", width=2, dash="dash"),
), row=2, col=2)
fig.update_xaxes(title_text="가중치 임계값 (함께 산 사람 수 ≥)", type="log", row=2, col=2)
fig.update_yaxes(title_text="남는 엣지 수", type="log", row=2, col=2)

fig.update_layout(
    title_text="투영 엣지 상한 n·k(k−1)/2 — 네 가지 관점",
    height=880, width=1300, barmode="group",
    template="plotly_white",
    legend=dict(orientation="h", yanchor="bottom", y=-0.13, x=0),
    font=dict(size=12),
)

_show(fig)
png_path = os.path.join(HERE, "expy.png")
fig.write_image(png_path, scale=2)
print(f"저장: {png_path}")
# 출력: 저장: .../expy.png

# %% [markdown]
# ## 정리
#
# | 항목 | 값 |
# |---|---|
# | 상한 공식 | $n \times \dfrac{k(k-1)}{2}$ |
# | 유도 | 사용자 1명의 짝 $\binom{k}{2}$ 을 $n$명 합산 |
# | $n$ 의존성 | 1차 (선형) |
# | $k$ 의존성 | **2차** — $k$가 10배면 약 100배 |
# | 왜 상한인가 | 중복 짝은 엣지 하나로 합쳐지고 가중치만 오름 |
# | 두 번째 상한 | 상품 $m$종일 때 $\binom{m}{2}$ |
# | 계산 비용 | 중복 여부와 무관하게 $\Theta(n k^2)$ 번 짝을 만들어 봄 |
# | 평균 사용 시 오차 | 정확히 $\dfrac{n\,V(k)}{2}$ 만큼 과소평가 (옌센) |
# | 대안 | 2홉 온디맨드 / 임계값 절단 / 허브·봇 제외 |
