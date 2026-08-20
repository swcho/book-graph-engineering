# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# 표 계산 부분은 표준 라이브러리만으로 동작한다. 시각화 셀만 plotly를 쓴다.

# %% [markdown]
# # 팬아웃 폭을 키우기 전에 — 합류를 프로파일하라
#
# **질문**: 팬아웃 폭을 키우기 전에 무엇을 확인해야 하는가?
#
# **답**: 합류(fan-in)를 프로파일해야 한다. 펴는 값보다 합치는 값이 천장을 만든다.
# 갈래끼리 비교하는 연산이 있으면 그건 제곱이다.
#
# ## 왜인가
#
# 팬아웃-팬인의 총 시간은 두 항의 합이다.
#
# $$T(n, w) = \underbrace{\left\lceil \frac{n}{w} \right\rceil \cdot t_{\text{wave}}(w)}_{\text{펴는 값 — 폭으로 나뉜다}} \;+\; \underbrace{M(n)}_{\text{합치는 값 — 폭과 무관}}$$
#
# 폭 $w$ 를 키우면 앞의 항만 줄어든다. 뒤의 항 $M(n)$ 은 **갈래 수** $n$ 의 함수라서
# 폭을 아무리 키워도 그대로 남는다. 그래서 이득에 천장이 생긴다.
#
# $$\lim_{w \to \infty} \frac{T_{\text{serial}}(n)}{T(n,w)} = \frac{n \cdot t}{M(n)}$$
#
# 이게 암달의 법칙(Amdahl's law)의 팬아웃 버전이다. $M(n)$ 이 직렬 잔여분이다.
#
# 그리고 합류 코드가 **갈래끼리 비교**를 하면 (전체 재정렬, 쌍별 중복 제거, 교차 검증)
#
# $$M(n) = c \cdot \binom{n}{2} = \Theta(n^2)$$
#
# 이 되어 천장이 $\dfrac{n \cdot t}{c\,n^2/2} = \dfrac{2t}{c\,n}$, 즉 **갈래를 늘릴수록 이득이 줄어든다.**
# 어느 지점부터는 병렬이 직렬보다 느려진다.

# %%
# 25장 ex2_fanout.py 와 같은 파라미터
TASK_MS = 900           # 갈래 하나 처리 시간
MERGE_PER_BRANCH = 140  # 합류할 때 갈래당 드는 시간 (선형 합류)
FAIL = 0.06             # 갈래 하나가 실패할 확률
RETRY_MS = TASK_MS      # 실패하면 한 번 더
SLOW_P = 0.10           # 갈래 하나가 「느린 놈」일 확률
SLOW_X = 3.5            # 느린 놈은 이만큼 더 걸린다


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


def serial_ms(n):
    return n * TASK_MS + n * FAIL * RETRY_MS


def wave_ms(width):
    """한 물결은 «제일 느린 갈래»가 끝나야 끝난다 — 꼬리 지연."""
    p_any_slow = 1 - (1 - SLOW_P) ** width
    base = TASK_MS * (1 + p_any_slow * (SLOW_X - 1))
    p_any_fail = 1 - (1 - FAIL) ** width
    return base + p_any_fail * RETRY_MS


print(f"직렬 8갈래 = {serial_ms(8):,.0f}ms")
print(f"물결 하나: 1폭 {wave_ms(1):,.0f}ms  4폭 {wave_ms(4):,.0f}ms  16폭 {wave_ms(16):,.0f}ms")
# 출력: 직렬 8갈래 = 7,632ms
# 출력: 물결 하나: 1폭 1,179ms  4폭 1,871ms  16폭 3,299ms

# %% [markdown]
# ## 1단계 — 합류가 천장을 만드는 것을 본다
#
# 폭 4로 고정하고 갈래 수만 늘린다. 「폭이 4니까 4배 빨라진다」가 왜 안 되는지 본다.

# %%
def parallel(n, width, merge_fn):
    waves = -(-n // width)
    spread = waves * wave_ms(width)
    merge = merge_fn(n)
    return spread + merge, spread, merge


def merge_linear(n):
    """갈래당 고정 비용. 정리·포맷·이어붙이기."""
    return n * MERGE_PER_BRANCH


print(f"{'갈래':>5}{'직렬':>10}{'병렬4폭':>10}{'펴는값':>9}{'합류':>9}"
      f"{'합류비중':>10}{'이득':>8}")
print("-" * 62)
for n in (2, 4, 8, 16, 32, 64, 128):
    s = serial_ms(n)
    p, spread, merge = parallel(n, 4, merge_linear)
    print(f"{n:>5}{s:>10,.0f}{p:>10,.0f}{spread:>9,.0f}{merge:>9,.0f}"
          f"{merge / p:>9.0%}{s / p:>7.2f}x")

print("\n폭 4인데 이득은 4배가 아니라 1.57배에서 천장을 친다.")
print(f"이론 천장 = n*t / M(n) = {TASK_MS * (1 + FAIL)}/{MERGE_PER_BRANCH} "
      f"= {TASK_MS * (1 + FAIL) / MERGE_PER_BRANCH:.2f}x (폭이 무한이어도 이것뿐)")
# 출력:    갈래        직렬      병렬4폭      펴는값       합류      합류비중      이득
# 출력: --------------------------------------------------------------
# 출력:     2     1,908     2,151    1,871      280      13%   0.89x
# 출력:     4     3,816     2,431    1,871      560      23%   1.57x
# 출력:     8     7,632     4,862    3,742    1,120      23%   1.57x
# 출력:    16    15,264     9,724    7,484    2,240      23%   1.57x
# 출력:    32    30,528    19,449   14,969    4,480      23%   1.57x
# 출력:    64    61,056    38,898   29,938    8,960      23%   1.57x
# 출력:   128   122,112    77,795   59,875   17,920      23%   1.57x
# 출력:
# 출력: 폭 4인데 이득은 4배가 아니라 1.57배에서 천장을 친다.
# 출력: 이론 천장 = n*t / M(n) = 954.0/140 = 6.81x (폭이 무한이어도 이것뿐)

# %% [markdown]
# 갈래 2개짜리는 병렬이 **더 느리다**(0.89배). 펴는 값보다 합류와 꼬리 지연이 더 든다.
#
# 그리고 갈래 수를 128까지 늘려도 이득이 1.57배에 고정된다. 합류가 총 시간의 23%를
# 계속 차지하기 때문이다. 이 23%가 「폭을 키워도 절대 줄지 않는 부분」이다.

# %% [markdown]
# ## 2단계 — 폭을 키워 보고, 무엇이 줄고 무엇이 안 줄는지 본다
#
# 갈래 16개를 고정하고 폭만 1 → 16으로 키운다.

# %%
print(f"{'폭':>4}{'물결수':>8}{'물결하나':>10}{'펴는값':>9}{'합류':>8}"
      f"{'총시간':>9}{'최악물결':>10}")
print("-" * 58)
for w in (1, 2, 4, 8, 16):
    p, spread, merge = parallel(16, w, merge_linear)
    worst = TASK_MS * SLOW_X + RETRY_MS  # 느리고 실패까지 한 갈래
    print(f"{w:>4}{-(-16 // w):>8}{wave_ms(w):>10,.0f}{spread:>9,.0f}"
          f"{merge:>8,.0f}{p:>9,.0f}{worst:>10,.0f}")

print("\n총 시간은 폭을 키우면 계속 준다. 합류(2,240ms)는 한 칸도 안 준다.")
print("대신 «물결 하나»가 길어진다 — 평균은 좋아지고 최악이 나빠진다.")
# 출력:    폭     물결수      물결하나      펴는값      합류      총시간      최악물결
# 출력: ----------------------------------------------------------
# 출력:    1      16     1,179   18,864   2,240   21,104     4,050
# 출력:    2       8     1,432   11,458   2,240   13,698     4,050
# 출력:    4       4     1,871    7,484   2,240    9,724     4,050
# 출력:    8       2     2,533    5,066   2,240    7,306     4,050
# 출력:   16       1     3,299    3,299   2,240    5,539     4,050
# 출력:
# 출력: 총 시간은 폭을 키우면 계속 준다. 합류(2,240ms)는 한 칸도 안 준다.
# 출력: 대신 «물결 하나»가 길어진다 — 평균은 좋아지고 최악이 나빠진다.

# %% [markdown]
# 16폭에서 총 5,539ms 중 2,240ms(40%)가 합류다. 펴는 값을 3,299ms까지 짜냈는데
# 합류가 그보다 더 큰 덩어리로 남았다. **여기서 폭을 더 키워도 의미가 없다.**
# 다음에 손댈 곳은 폭이 아니라 합류 코드다.

# %% [markdown]
# ## 3단계 — 합류에 「갈래끼리 비교」가 있으면 그건 제곱이다
#
# 합류에서 이런 걸 하고 있으면 $\Theta(n^2)$ 이다.
#
# - 갈래 결과끼리 쌍별 중복 제거 (`for a in results: for b in results:`)
# - 갈래 간 모순 검증 / 교차 확인
# - 전체를 다시 정렬 후 인접 비교 (정렬 자체는 $n\log n$ 이지만 비교 함수가 무거우면 상수가 크다)
# - 갈래마다 임베딩 유사도 행렬 계산
#
# 선형 합류와 제곱 합류를 나란히 놓는다.

# %%
PAIR_MS = 4.0  # 갈래 쌍 하나를 비교하는 데 드는 시간


def merge_quadratic(n):
    """갈래끼리 쌍별 비교. n(n-1)/2 쌍."""
    return n * MERGE_PER_BRANCH + PAIR_MS * n * (n - 1) / 2


print(f"{'갈래':>5}{'직렬':>10}{'선형합류':>11}{'이득':>8}"
      f"{'제곱합류':>11}{'이득':>8}{'그중비교':>10}")
print("-" * 64)
for n in (4, 8, 16, 32, 64, 128, 256):
    s = serial_ms(n)
    pl, _, _ = parallel(n, 8, merge_linear)
    pq, _, mq = parallel(n, 8, merge_quadratic)
    pair = PAIR_MS * n * (n - 1) / 2
    flag = "  ← 병렬이 손해" if s / pq < 1.0 else ""
    print(f"{n:>5}{s:>10,.0f}{pl:>11,.0f}{s / pl:>7.2f}x"
          f"{pq:>11,.0f}{s / pq:>7.2f}x{pair / pq:>9.0%}{flag}")
# 출력:    갈래        직렬       선형합류      이득       제곱합류      이득      그중비교
# 출력: ----------------------------------------------------------------
# 출력:     4     3,816      3,093   1.23x      3,117   1.22x       1%
# 출력:     8     7,632      3,653   2.09x      3,765   2.03x       3%
# 출력:    16    15,264      7,306   2.09x      7,786   1.96x       6%
# 출력:    32    30,528     14,611   2.09x     16,595   1.84x      12%
# 출력:    64    61,056     29,223   2.09x     37,287   1.64x      22%
# 출력:   128   122,112     58,445   2.09x     90,957   1.34x      36%
# 출력:   256   244,224    116,891   2.09x    247,451   0.99x      53%  ← 병렬이 손해
# %% [markdown]
# 256갈래에서 제곱 합류는 **직렬보다 느리다**(0.99배). 총 시간의 53%가 쌍별 비교다.
#
# 무서운 점은 이게 **작은 n에서는 안 보인다**는 것이다. 4갈래에서 비교 비용은 1%다.
# 「잘 되네, 폭을 늘리자」 하고 갈래를 늘리는 순간 제곱이 깨어난다.
# 그래서 폭을 키우기 **전에** 프로파일해야 한다.

# %% [markdown]
# ## 4단계 — 프로파일 체크리스트를 코드로
#
# 실제로 재는 방법. 합류 함수만 따로 떼어 n을 두 배씩 올리며 시간을 재고,
# 기울기(더블링 비율)를 본다.
#
# - 비율 $\approx 1$ → $O(1)$, 폭을 키워도 된다
# - 비율 $\approx 2$ → $O(n)$, 선형. 상수를 줄일 수 있는지 본다
# - 비율 $\approx 4$ → $O(n^2)$, **폭을 키우기 전에 여기를 고쳐야 한다**

# %%
import time


def merge_impl_linear(results):
    """갈래별로 한 번만 훑는다."""
    seen, out = set(), []
    for r in results:
        k = r["key"]
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def merge_impl_pairwise(results):
    """갈래끼리 쌍별로 비교한다. 흔한 «중복 제거» 코드다."""
    out = []
    for r in results:
        if not any(r["key"] == o["key"] for o in out):
            out.append(r)
    return out


def profile(fn, sizes=(500, 1000, 2000, 4000, 8000)):
    rows, prev = [], None
    for n in sizes:
        data = [{"key": i % (n // 2), "v": i} for i in range(n)]
        t0 = time.perf_counter()
        fn(data)
        dt = (time.perf_counter() - t0) * 1000
        ratio = dt / prev if prev else float("nan")
        rows.append((n, dt, ratio))
        prev = dt
    return rows


for label, fn in (("선형 (set)", merge_impl_linear),
                  ("쌍별 (any 루프)", merge_impl_pairwise)):
    print(f"\n[{label}]")
    print(f"{'n':>7}{'시간(ms)':>11}{'더블링비':>10}  판정")
    for n, dt, ratio in profile(fn):
        verdict = ("-" if ratio != ratio else
                   "O(1)~O(n)" if ratio < 2.6 else
                   "O(n log n)" if ratio < 3.2 else "O(n^2) ← 문제")
        r = "  -  " if ratio != ratio else f"{ratio:>5.2f}"
        print(f"{n:>7}{dt:>11.3f}{r:>10}  {verdict}")
# 출력:
# 출력: [선형 (set)]
# 출력:       n     시간(ms)      더블링비  판정
# 출력:     500      0.033       -    -
# 출력:    1000      0.064      1.90  O(1)~O(n)
# 출력:    2000      0.126      1.98  O(1)~O(n)
# 출력:    4000      0.258      2.04  O(1)~O(n)
# 출력:    8000      0.512      1.99  O(1)~O(n)
# 출력:
# 출력: [쌍별 (any 루프)]
# 출력:       n     시간(ms)      더블링비  판정
# 출력:     500      2.955       -    -
# 출력:    1000     11.830      4.00  O(n^2) ← 문제
# 출력:    2000     46.337      3.92  O(n^2) ← 문제
# 출력:    4000    183.407      3.96  O(n^2) ← 문제
# 출력:    8000    730.637      3.98  O(n^2) ← 문제
# (절대 시간은 머신에 따라 다르다. 볼 것은 더블링비 — 2에 붙으면 선형, 4에 붙으면 제곱)

# %% [markdown]
# 더블링비 약 4.0. 명확한 $O(n^2)$ 이다. n=8000에서 731ms — 갈래를 늘릴수록
# 펴서 아낀 시간을 합류에서 다 토해낸다.
#
# 두 구현은 **같은 일**을 한다(키 기준 중복 제거). 다른 건 자료구조뿐이다.
# 폭을 4에서 16으로 키우는 것보다 이 한 줄을 고치는 게 크게 듣는다.

# %% [markdown]
# ## 시각화
#
# 왼쪽: 폭을 키울 때 펴는 값은 줄고 합류는 상수로 남는다(천장).
# 오른쪽: 갈래 수를 늘릴 때 선형 합류와 제곱 합류의 이득 곡선.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=("폭을 키우면 «펴는 값»만 준다 (갈래 16개)",
                    "합류가 제곱이면 이득이 무너진다 (폭 8)"),
)

# 왼쪽: 폭 vs 시간 구성
widths = [1, 2, 4, 8, 16]
spreads, merges = [], []
for w in widths:
    _, sp, mg = parallel(16, w, merge_linear)
    spreads.append(sp)
    merges.append(mg)

fig.add_trace(go.Bar(x=[str(w) for w in widths], y=spreads, name="펴는 값 (÷폭)",
                     marker_color="#4C78A8", legendgroup="l"), row=1, col=1)
fig.add_trace(go.Bar(x=[str(w) for w in widths], y=merges, name="합류 값 (폭과 무관)",
                     marker_color="#E45756", legendgroup="l"), row=1, col=1)

# 오른쪽: 갈래 수 vs 이득
ns = [2, 4, 8, 16, 32, 64, 128, 256, 512]
g_lin = [serial_ms(n) / parallel(n, 8, merge_linear)[0] for n in ns]
g_quad = [serial_ms(n) / parallel(n, 8, merge_quadratic)[0] for n in ns]

fig.add_trace(go.Scatter(x=ns, y=g_lin, mode="lines+markers",
                         name="선형 합류 O(n)", line=dict(color="#4C78A8", width=3)),
              row=1, col=2)
fig.add_trace(go.Scatter(x=ns, y=g_quad, mode="lines+markers",
                         name="제곱 합류 O(n²)", line=dict(color="#E45756", width=3)),
              row=1, col=2)
fig.add_hline(y=1.0, line_dash="dot", line_color="gray",
              annotation_text="1.0 = 직렬과 같음", row=1, col=2)

fig.update_xaxes(title_text="동시 폭 w", row=1, col=1)
fig.update_xaxes(title_text="갈래 수 n (log)", type="log", row=1, col=2)
fig.update_yaxes(title_text="시간 (ms)", row=1, col=1)
fig.update_yaxes(title_text="직렬 대비 이득 (배)", row=1, col=2)
fig.update_layout(barmode="stack", height=460, width=1080,
                  title_text="펴는 값보다 합치는 값이 천장을 만든다",
                  template="plotly_white")

import os
_out = os.path.join(os.path.dirname(os.path.abspath(__file__))
                    if "__file__" in dir() else ".", "expy.png")
fig.write_image(_out, scale=2)
print(f"저장: {_out}")
_show(fig)
# 출력: 저장: .../expy.png

# %% [markdown]
# ## 정리
#
# | 확인할 것 | 재는 방법 | 나쁜 신호 |
# |---|---|---|
# | 합류가 총 시간의 몇 %인가 | 펴는 구간과 합류 구간을 따로 타이밍 | 20% 넘으면 폭 늘리는 이득이 이미 깎여 있다 |
# | 합류의 복잡도가 무엇인가 | 갈래 수를 2배씩 올리며 더블링비 | 비율이 4에 붙으면 $O(n^2)$ |
# | 갈래끼리 비교하는 코드가 있는가 | 합류 함수에서 이중 루프·쌍별 검증 찾기 | 있으면 무조건 제곱 |
# | 꼬리 지연이 얼마인가 | 갈래별 소요시간의 p99 / 중앙값 | 폭이 커질수록 물결 하나가 길어진다 |
#
# 순서:
# 1. **합류를 먼저 프로파일한다.** 합류가 총 시간의 지배적 비중이면 폭은 건드리지 않는다.
# 2. 갈래끼리 비교하는 연산이 있으면 해시/인덱스로 선형화한다.
# 3. 그 다음에 폭을 키운다. 이때 총 시간은 줄지만 최악(꼬리)이 나빠지는 것을 감수한다.
