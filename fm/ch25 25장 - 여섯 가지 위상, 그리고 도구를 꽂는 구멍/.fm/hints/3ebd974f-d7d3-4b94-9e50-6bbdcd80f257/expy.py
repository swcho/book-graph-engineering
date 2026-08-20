# %% [markdown]
# # 팬아웃의 천장은 폭이 아니라 합류다
#
# **질문** — 팬아웃 성능 개선에서 폭 키우기보다 효과가 큰 것은 무엇인가?
#
# **답** — 합류 코드를 가볍게 유지하는 것이다. 합류에서 전체 재정렬이나
# $O(n^2)$ 중복 제거를 하면 펴는 의미가 사라진다.
#
# 25.2절의 `ex2_fanout.py` 는 합류 값을 「갈래당 140ms」라는 **상수**로 넣었습니다.
# 그래서 합류가 $\Theta(n)$ 이고, 그것만으로도 이득이 1.57배에서 천장을 쳤습니다.
#
# 이 노트는 그 상수를 **실제 구현**으로 바꿔 봅니다. 합류를 세 가지로 짜고,
# 연산 수와 실측 시간을 직접 재서 팬아웃 이득이 어떻게 달라지는지 봅니다.
#
# | 합류 구현 | 하는 일 | 복잡도 |
# |---|---|---|
# | 해시 중복 제거 | `set` 에 키를 넣고 본 적 있나 확인 | $O(n)$ |
# | 쌍별 비교 | 새 항목마다 살아남은 항목 전부와 비교 | $O(n \cdot u) \approx O(n^2)$ |
# | 전체 재정렬 | 키로 정렬해 인접 중복 제거 후 점수로 재정렬 | $O(n \log n)$ |
#
# 팬아웃 총 시간의 모형은 이렇습니다. 폭 $W$, 갈래 하나 $T$, 갈래 수 $n$ 이면
#
# $$ \text{total}(n, W) = \underbrace{\left\lceil \frac{n}{W} \right\rceil \cdot T}_{\text{펴는 값} \;\propto\; n/W} \; + \; \underbrace{C(n)}_{\text{합류 값} \;\text{폭과 무관}} $$
#
# 오른쪽 항에 $W$ 가 **없습니다**. 폭을 키워도 합류 값은 한 톨도 줄지 않아요.
# 그래서 $C(n)$ 이 커지면 왼쪽을 아무리 눌러도 전체가 안 줄어듭니다.
# 이게 암달의 법칙(Amdahl's law)이 팬아웃에 나타나는 모습입니다.
#
# $$ \text{speedup}(n, W) = \frac{nT}{\lceil n/W \rceil T + C(n)} \;\xrightarrow[\;W \to \infty\;]{}\; \frac{nT}{T + C(n)} $$

# %%
# 필요 패키지: plotly, kaleido (정적 이미지 저장용)
import random
import time

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


TASK_MS = 900.0     # 갈래 하나 처리 시간 (ex2_fanout.py 와 같은 값)
COST_PER_OP = 0.25  # 합류 연산 한 번의 값(ms). 임베딩 유사도 비교 한 번쯤
DUP_RATE = 0.30     # 갈래 결과 중 다른 갈래와 겹치는 비율

print(f"갈래 하나 {TASK_MS:.0f}ms, 합류 연산 하나 {COST_PER_OP}ms, 중복률 {DUP_RATE:.0%}")
# 출력: 갈래 하나 900ms, 합류 연산 하나 0.25ms, 중복률 30%


# %% [markdown]
# ## 1. 갈래 결과 만들기
#
# 갈래 $n$ 개가 각각 항목 하나를 물어 옵니다. 그중 30%는 다른 갈래와 겹치는
# 중복이에요. 합류는 이 중복을 걷어내고 점수 순으로 정렬해서 내보내야 합니다.

# %%
def make_branches(n, seed=25):
    """갈래 n개의 결과. 30%는 앞에서 이미 나온 키의 중복."""
    rnd = random.Random(seed)
    keys, out = [], []
    for i in range(n):
        if keys and rnd.random() < DUP_RATE:
            k = rnd.choice(keys)          # 중복 항목
        else:
            k = f"doc-{i:05d}"
            keys.append(k)
        out.append([{"key": k, "score": rnd.random(), "text": k * 3}])
    return out


bs = make_branches(12)
uniq = len({it["key"] for b in bs for it in b})
print(f"갈래 12개 → 항목 12개, 그중 서로 다른 키 {uniq}개")
print("앞 4개:", [b[0]["key"] for b in bs[:4]])
# 출력: 갈래 12개 → 항목 12개, 그중 서로 다른 키 10개
# 출력: 앞 4개: ['doc-00000', 'doc-00001', 'doc-00001', 'doc-00001']


# %% [markdown]
# ## 2. 합류 세 가지
#
# 세 구현 모두 **결과는 같습니다**. 중복 없는 항목을 점수 내림차순으로 돌려줘요.
# 다른 것은 그 결과에 도달하는 연산 수뿐입니다.
#
# 연산 수는 추정하지 않고 실제로 셉니다. 정렬은 `__lt__` 를 세는 래퍼로
# 파이썬 Timsort가 실제로 한 비교 횟수를 잡습니다.

# %%
class _CountingKey:
    """정렬이 실제로 한 비교 횟수를 세는 키 래퍼."""
    __slots__ = ("v", "c")

    def __init__(self, v, c):
        self.v, self.c = v, c

    def __lt__(self, other):
        self.c[0] += 1
        return self.v < other.v


def merge_hash(branches):
    """O(n) — 해시 집합으로 본 적 있나만 확인한다."""
    seen, out, ops = set(), [], 0
    for b in branches:
        for it in b:
            ops += 1                       # 해시 조회 1회
            if it["key"] not in seen:
                seen.add(it["key"])
                out.append(it)
    c = [0]
    out.sort(key=lambda it: _CountingKey(-it["score"], c))
    return out, ops + c[0]


def merge_pairwise(branches):
    """O(n·u) — 새 항목마다 살아남은 항목 전부와 견줘 본다."""
    items = [it for b in branches for it in b]
    out, ops = [], 0
    for it in items:
        dup = False
        for kept in out:
            ops += 1                       # 쌍별 비교 1회
            if kept["key"] == it["key"]:
                dup = True
                break
        if not dup:
            out.append(it)
    c = [0]
    out.sort(key=lambda it: _CountingKey(-it["score"], c))
    return out, ops + c[0]


def merge_fullsort(branches):
    """O(n log n) — 키로 전체 정렬해 인접 중복을 걷고, 점수로 다시 전체 정렬."""
    items = [it for b in branches for it in b]
    c = [0]
    items.sort(key=lambda it: _CountingKey(it["key"], c))   # 정렬 1
    out, prev = [], None
    for it in items:
        c[0] += 1                          # 인접 비교 1회
        if it["key"] != prev:
            out.append(it)
            prev = it["key"]
    out.sort(key=lambda it: _CountingKey(-it["score"], c))  # 정렬 2
    return out, c[0]


MERGES = [("해시 O(n)", merge_hash),
          ("쌍별 O(n²)", merge_pairwise),
          ("전체 재정렬 O(n log n)", merge_fullsort)]

bs = make_branches(200)
for name, fn in MERGES:
    res, ops = fn(bs)
    print(f"{name:<24} 결과 {len(res):>3}개  연산 {ops:>6,}회  "
          f"1등 점수 {res[0]['score']:.4f}")
# 출력: 해시 O(n)                  결과 147개  연산  1,056회  1등 점수 0.9991
# 출력: 쌍별 O(n²)                 결과 147개  연산 13,650회  1등 점수 0.9991
# 출력: 전체 재정렬 O(n log n)        결과 147개  연산  2,054회  1등 점수 0.9991


# %% [markdown]
# 세 줄 다 **147개, 1등 점수 0.9991**. 결과가 완전히 같습니다.
# 연산 수만 1,056 / 13,650 / 2,054 으로 갈립니다. 쌍별이 해시의 12.9배예요.
# 그리고 이 배수는 $n$ 이 커지면 같이 커집니다.

# %% [markdown]
# ## 3. 연산 수와 실측 시간을 재 본다
#
# $n$ 을 두 배씩 키우며 연산 수와 실제 벽시계 시간을 같이 잡습니다.
# 복잡도 주장이 맞으면 두 배마다 연산 수가 해시는 ×2, 쌍별은 ×4로 늘어야 합니다.

# %%
NS = [32, 64, 128, 256, 512, 1024, 2048]
ops_tbl, wall_tbl = {}, {}

for name, fn in MERGES:
    ops_tbl[name], wall_tbl[name] = [], []
    for n in NS:
        bs = make_branches(n)
        t0 = time.perf_counter()
        reps = 5
        for _ in range(reps):
            res, ops = fn(bs)
        dt = (time.perf_counter() - t0) / reps * 1000
        ops_tbl[name].append(ops)
        wall_tbl[name].append(dt)

print(f"{'n':>6}" + "".join(f"{nm.split()[0]+' 연산':>14}" for nm, _ in MERGES)
      + "".join(f"{nm.split()[0]+' ms':>12}" for nm, _ in MERGES))
print("-" * 84)
for i, n in enumerate(NS):
    print(f"{n:>6}"
          + "".join(f"{ops_tbl[nm][i]:>14,}" for nm, _ in MERGES)
          + "".join(f"{wall_tbl[nm][i]:>12.3f}" for nm, _ in MERGES))
# 출력:      n         해시 연산         쌍별 연산         전체 연산       해시 ms       쌍별 ms       전체 ms
# 출력: ------------------------------------------------------------------------------------
# 출력:     32           116           436           195       0.021       0.048       0.048
# 출력:     64           257         1,523           484       0.041       0.110       0.089
# 출력:    128           587         5,541         1,160       0.088       0.400       0.190
# 출력:    256         1,383        21,241         2,734       0.201       1.323       0.436
# 출력:    512         3,139        81,972         6,165       0.457       4.947       0.957
# 출력:   1024         6,848       315,007        13,684       1.014      18.946       2.194
# 출력:   2048        15,176     1,259,969        30,009       2.235      71.359       5.300

# %% [markdown]
# ## 4. 성장 지수를 뽑아 본다
#
# 두 배씩 키웠으니 인접한 두 점의 비율에 $\log_2$ 를 씌우면 지수가 나옵니다.
#
# $$ \alpha = \log_2 \frac{C(2n)}{C(n)} $$
#
# $\alpha \approx 1$ 이면 선형, $\alpha \approx 2$ 면 제곱입니다.

# %%
import math

print(f"{'구현':<24}{'구간별 성장 지수 α':<34}{'평균':>8}")
print("-" * 68)
for name, _ in MERGES:
    v = ops_tbl[name]
    alphas = [math.log2(v[i + 1] / v[i]) for i in range(len(v) - 1)]
    print(f"{name:<24}{' '.join(f'{a:.2f}' for a in alphas):<34}"
          f"{sum(alphas) / len(alphas):>8.2f}")
# 출력: 구현                      구간별 성장 지수 α                             평균
# 출력: --------------------------------------------------------------------
# 출력: 해시 O(n)                 1.15 1.19 1.24 1.18 1.13 1.15         1.17
# 출력: 쌍별 O(n²)                1.80 1.86 1.94 1.95 1.94 2.00         1.92
# 출력: 전체 재정렬 O(n log n)       1.31 1.26 1.24 1.17 1.15 1.13         1.21

# %% [markdown]
# 실측 평균이 **1.17 / 1.92 / 1.21**. 짜 놓은 복잡도 그대로 나왔습니다.
#
# 해시와 전체 재정렬이 딱 1.00 이 아닌 것은 둘 다 마지막에 점수 정렬
# ($O(n \log n)$)을 하기 때문입니다. 그 $\log n$ 항이 α를 1.2쯤으로 밀어 올려요.
# 실전에서 이 정도는 상수와 구별이 안 갑니다.
#
# 쌍별만 **1.92**, 사실상 2입니다. $n$ 이 두 배면 합류 값이 네 배예요.
# 여기서 「갈래끼리 비교하는 연산이 있으면 그건 제곱이다」라는 한 장 요약이
# 왜 무서운 말인지 보입니다. 갈래를 8개에서 64개로 늘리는 흔한 결정이
# 합류 값을 64배로 만듭니다.

# %% [markdown]
# ## 5. 이 합류 값이 팬아웃 이득을 얼마나 먹는가
#
# 이제 연산 수를 시간으로 바꿔 총 시간을 계산합니다.
# 직렬은 받는 즉시 누적하니 별도 합류 단계가 없다고 봅니다($nT$).

# %%
def merge_ms(name, n):
    return ops_tbl[name][NS.index(n)] * COST_PER_OP


def speedup(name, n, W):
    serial = n * TASK_MS
    par = -(-n // W) * TASK_MS + merge_ms(name, n)
    return serial / par


W = 8
print(f"폭 W={W} 고정. 합류 구현만 바꾼다.\n")
print(f"{'n':>6}{'직렬(ms)':>12}{'펴는 값(ms)':>13}"
      + "".join(f"{nm.split()[0]+' 합류ms':>15}" for nm, _ in MERGES)
      + "".join(f"{nm.split()[0]+' 이득':>13}" for nm, _ in MERGES))
print("-" * 122)
for n in NS:
    row = f"{n:>6}{n * TASK_MS:>12,.0f}{-(-n // W) * TASK_MS:>13,.0f}"
    row += "".join(f"{merge_ms(nm, n):>15,.0f}" for nm, _ in MERGES)
    row += "".join(f"{speedup(nm, n, W):>12.2f}x" for nm, _ in MERGES)
    print(row)
# 출력:      n      직렬(ms)     펴는 값(ms)        해시 합류ms        쌍별 합류ms        전체 합류ms        해시 이득        쌍별 이득        전체 이득
# 출력: --------------------------------------------------------------------------------------------------------------------------
# 출력:     32      28,800        3,600             29            109             49        7.94x        7.76x        7.89x
# 출력:     64      57,600        7,200             64            381            121        7.93x        7.60x        7.87x
# 출력:    128     115,200       14,400            147          1,385            290        7.92x        7.30x        7.84x
# 출력:    256     230,400       28,800            346          5,310            684        7.91x        6.75x        7.81x
# 출력:    512     460,800       57,600            785         20,493          1,541        7.89x        5.90x        7.79x
# 출력:   1024     921,600      115,200          1,712         78,752          3,421        7.88x        4.75x        7.77x
# 출력:   2048   1,843,200      230,400          3,794        314,992          7,502        7.87x        3.38x        7.75x

# %% [markdown]
# 해시는 $n$ 이 64배가 되도록 **7.87배**를 지킵니다. 폭이 8이니 거의 이론값이에요.
#
# 쌍별은 7.76배에서 **3.38배**로 내려갑니다. 같은 폭, 같은 갈래인데요.
# $n{=}2048$ 에서 합류 값 315초가 펴는 값 230초를 **넘어섰습니다**.
# 이 지점부터는 합류가 총 시간을 지배해서, 갈래를 더 늘릴수록 이득이 계속 죽습니다.
#
# 전체 재정렬은 7.75배. $O(n \log n)$ 은 실전에서 거의 공짜입니다.
# 문제는 「정렬」이 아니라 「쌍별 비교」예요.

# %% [markdown]
# ## 6. 카드의 핵심 — 폭을 키우는 것과 합류를 고치는 것
#
# 이제 두 개선을 나란히 놓습니다. $n{=}2048$ 에서
#
# - **폭 키우기**: 쌍별 합류를 그대로 두고 $W$ 를 8 → 128 로 (16배 투자)
# - **합류 고치기**: $W{=}8$ 그대로 두고 쌍별 → 해시로 (코드 몇 줄)

# %%
n = 2048
WIDTHS = [1, 2, 4, 8, 16, 32, 64, 128]

print(f"n={n}. 표의 값은 직렬 대비 속도 이득.\n")
print(f"{'폭 W':>6}" + "".join(f"{nm:>24}" for nm, _ in MERGES))
print("-" * 78)
grid = {nm: [] for nm, _ in MERGES}
for w in WIDTHS:
    row = f"{w:>6}"
    for nm, _ in MERGES:
        s = speedup(nm, n, w)
        grid[nm].append(s)
        row += f"{s:>23.2f}x"
    print(row)
# 출력: n=2048. 표의 값은 직렬 대비 속도 이득.
# 출력:
# 출력:   폭 W                 해시 O(n)                쌍별 O(n²)       전체 재정렬 O(n log n)
# 출력: ------------------------------------------------------------------------------
# 출력:      1                   1.00x                   0.85x                   1.00x
# 출력:      2                   1.99x                   1.49x                   1.98x
# 출력:      4                   3.97x                   2.38x                   3.94x
# 출력:      8                   7.87x                   3.38x                   7.75x
# 출력:     16                  15.49x                   4.28x                  15.02x
# 출력:     32                  30.02x                   4.95x                  28.31x
# 출력:     64                  56.55x                   5.36x                  50.77x
# 출력:    128                 101.31x                   5.60x                  84.16x

# %%
a = speedup("쌍별 O(n²)", n, 8)
b = speedup("쌍별 O(n²)", n, 128)
c = speedup("해시 O(n)", n, 8)
ceiling = n * TASK_MS / (TASK_MS + merge_ms("쌍별 O(n²)", n))

print(f"기준        쌍별 합류 + 폭 8      → {a:.2f}x")
print(f"폭 16배 투자 쌍별 합류 + 폭 128    → {b:.2f}x   ({b / a:.2f}배 개선)")
print(f"합류만 교체  해시 합류 + 폭 8       → {c:.2f}x   ({c / a:.2f}배 개선)")
print(f"\n쌍별 합류를 둔 채 폭을 무한히 키워도 천장은 {ceiling:.2f}x 다.")
print(f"해시 합류 + 폭 8 이 그 천장({ceiling:.2f}x)을 이미 넘는다: {c:.2f}x")
# 출력: 기준        쌍별 합류 + 폭 8      → 3.38x
# 출력: 폭 16배 투자 쌍별 합류 + 폭 128    → 5.60x   (1.66배 개선)
# 출력: 합류만 교체  해시 합류 + 폭 8       → 7.87x   (2.33배 개선)
# 출력:
# 출력: 쌍별 합류를 둔 채 폭을 무한히 키워도 천장은 5.83x 다.
# 출력: 해시 합류 + 폭 8 이 그 천장(5.83x)을 이미 넘는다: 7.87x

# %% [markdown]
# 이게 카드의 답입니다.
#
# 폭을 8에서 128로, 즉 **동시 실행 슬롯을 16배** 늘리면 1.66배 좋아집니다.
# 합류를 쌍별에서 해시로 바꾸면, 폭은 8 그대로인데 **2.33배** 좋아집니다.
# 값을 안 치른 쪽이 더 크게 들었어요.
#
# 그리고 더 중요한 건 **천장**입니다. 쌍별 합류를 둔 채로는 폭을 무한히
# 키워도 5.83배를 못 넘습니다($W \to \infty$ 극한). 반면 해시 합류는 폭 8만으로
# 7.87배로 그 천장을 이미 넘어섭니다. 폭으로는 살 수 없는 구간이 있는 거예요.
#
# 표 첫 줄도 눈에 담아 두세요. 폭 1(사실상 직렬)에서 쌍별 합류는 **0.85배**입니다.
# 합류 단계를 따로 두는 것만으로 직렬보다 느려졌어요.
# `ex2_fanout.py` 첫 표의 「갈래 2개짜리는 병렬이 더 느리다, 0.89배다」와 같은 현상입니다.

# %% [markdown]
# ## 7. 그림으로

# %%
C = {"해시 O(n)": "#2563eb", "쌍별 O(n²)": "#dc2626",
     "전체 재정렬 O(n log n)": "#059669"}

fig = make_subplots(
    rows=1, cols=3,
    subplot_titles=("① 합류 연산 수 (실측, log-log)",
                    f"② 폭 W=8 고정, n 이 커질 때 이득",
                    f"③ n={n} 고정, 폭을 키울 때 이득"),
    horizontal_spacing=0.08,
)

for nm, _ in MERGES:
    fig.add_trace(go.Scatter(x=NS, y=ops_tbl[nm], name=nm, legendgroup=nm,
                             mode="lines+markers",
                             line=dict(color=C[nm], width=2.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=NS, y=[speedup(nm, k, 8) for k in NS], name=nm,
                             legendgroup=nm, showlegend=False,
                             mode="lines+markers",
                             line=dict(color=C[nm], width=2.5)), row=1, col=2)
    fig.add_trace(go.Scatter(x=WIDTHS, y=grid[nm], name=nm, legendgroup=nm,
                             showlegend=False, mode="lines+markers",
                             line=dict(color=C[nm], width=2.5)), row=1, col=3)

LOGX = dict(type="log", tickmode="array", showgrid=True)

# ②의 이론 천장(폭 8)과 ③의 쌍별 천장
fig.add_hline(y=8, line=dict(color="#64748b", dash="dot"), row=1, col=2,
              annotation_text="폭 8 의 이론 천장 8x",
              annotation_position="top left",
              annotation_font=dict(size=11, color="#475569"))
fig.add_hline(y=ceiling, line=dict(color="#dc2626", dash="dot"), row=1, col=3)
# log 축에서는 주석 좌표도 log10 값이다.
fig.add_annotation(xref="x3", yref="y3", x=math.log10(48), y=math.log10(ceiling),
                   ax=-6, ay=62, showarrow=True, arrowhead=2, arrowsize=0.8,
                   arrowcolor="#dc2626", xanchor="center",
                   text=f"쌍별 합류의 천장 {ceiling:.1f}x (W→∞)",
                   font=dict(size=11, color="#dc2626"))

fig.update_xaxes(title_text="갈래 수 n", tickvals=NS, ticktext=[str(v) for v in NS],
                 **LOGX, row=1, col=1)
fig.update_yaxes(type="log", title_text="합류 연산 수",
                 tickvals=[100, 1_000, 10_000, 100_000, 1_000_000],
                 ticktext=["100", "1천", "1만", "10만", "100만"], row=1, col=1)
fig.update_xaxes(title_text="갈래 수 n", tickvals=NS, ticktext=[str(v) for v in NS],
                 **LOGX, row=1, col=2)
fig.update_yaxes(title_text="직렬 대비 이득 (x)", range=[0, 9.2],
                 dtick=2, row=1, col=2)
fig.update_xaxes(title_text="동시 폭 W", tickvals=WIDTHS,
                 ticktext=[str(v) for v in WIDTHS], **LOGX, row=1, col=3)
fig.update_yaxes(type="log", title_text="직렬 대비 이득 (x)",
                 range=[math.log10(0.6), math.log10(220)],
                 tickvals=[1, 3, 10, 30, 100], ticktext=["1", "3", "10", "30", "100"],
                 row=1, col=3)

fig.update_layout(
    title=dict(text="팬아웃의 천장은 폭이 아니라 합류가 만든다", x=0.03),
    template="plotly_white", height=470, width=1320,
    legend=dict(orientation="h", y=-0.20, x=0.5, xanchor="center"),
    margin=dict(t=95, b=95, l=70, r=30),
)

_show(fig)
fig.write_image("expy.png", scale=2)
print("expy.png 저장")
# 출력: expy.png 저장

# %% [markdown]
# ## 정리
#
# - ① 합류 연산 수는 구현에 따라 기울기가 다릅니다. 실측 성장 지수가
#   **1.17 / 1.92 / 1.21**. 쌍별만 제곱이에요.
# - ② 폭을 8로 고정하면 해시 합류는 $n$ 과 무관하게 7.87배를 지키는데,
#   쌍별은 7.76배 → 3.38배로 흘러내립니다. 「펴는 의미가 사라진다」가 이 선입니다.
# - ③ 폭을 키우는 개선은 쌍별 합류에서 **5.83배 천장**에 막힙니다.
#   해시 합류는 폭 8만으로 그 천장을 넘습니다.
#
# 그래서 순서가 이렇습니다.
#
# 1. **폭을 키우기 전에 합류를 프로파일한다.** 총 시간에서 합류가 몇 %인지 잰다.
# 2. **갈래끼리 비교하는 연산이 있나 본다.** 있으면 그건 제곱이다.
#    중복 제거, 유사도 클러스터링, 「서로 모순되나」 검사가 다 여기 걸린다.
# 3. **키를 뽑을 수 있으면 해시로 바꾼다.** 정확한 중복이면 `set` 하나로 끝난다.
#    의미 중복이면 임베딩 → 버킷(LSH) 으로 후보를 줄여 제곱을 벗긴다.
# 4. **전체 재정렬은 그다음이다.** $O(n \log n)$ 은 대개 문제가 아니다.
#    문제가 되는 것은 「합류에서 전부 다시 읽는」 형태다.
#
# 25.2절 마지막 줄이 이걸 한 문장으로 말합니다.
# 「합류 코드를 가볍게 유지하는 게 폭을 키우는 것보다 크게 듣는다.
# 첫 표에서 천장을 만든 게 합류였다. 폭이 아니라.」
