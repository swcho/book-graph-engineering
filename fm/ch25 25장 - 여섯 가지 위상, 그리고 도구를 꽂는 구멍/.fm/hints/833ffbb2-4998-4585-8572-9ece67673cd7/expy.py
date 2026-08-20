# %% [markdown]
# # 폭 4로 병렬화해도 4배가 안 되는 이유 — 합류가 만드는 암달 천장
#
# 25장 `ex2_fanout.py`의 비용 모델을 그대로 쓴다.
#
# $$
# \text{parallel}(n, W) \;=\; \underbrace{\left\lceil \tfrac{n}{W} \right\rceil \cdot \text{wave\_ms}(W)}_{\text{펴는 값 — } W\text{로 나눠진다}}
# \;+\; \underbrace{n \cdot \text{MERGE\_PER\_BRANCH}}_{\text{합류 값 — } W\text{가 없다}}
# $$
#
# 오른쪽 항에 $W$가 **아예 등장하지 않는다.** 이것이 암달의 법칙에서 말하는
# 직렬 부분이고, 이득에 천장을 만드는 유일한 범인이다.

# %%
# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
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


HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."

# %% [markdown]
# ## 1단계 — 책의 비용 모델을 그대로 옮긴다

# %%
TASK_MS = 900           # 갈래 하나 처리 시간
MERGE_PER_BRANCH = 140  # 합류할 때 갈래당 드는 시간 (정리·중복 제거)
FAIL = 0.06             # 갈래 하나가 실패할 확률
RETRY_MS = TASK_MS      # 실패하면 한 번 더
SLOW_P = 0.10           # 갈래 하나가 «느린 놈»일 확률
SLOW_X = 3.5            # 느린 놈은 이만큼 더 걸린다

BRANCH_MS = TASK_MS + FAIL * RETRY_MS   # 직렬에서 갈래 하나에 드는 기대 시간


def serial(n):
    """차례대로 처리. 합칠 일이 없으니 합류 값이 0이다."""
    return n * BRANCH_MS


def wave_ms(width):
    """한 물결은 «제일 느린 갈래»가 끝나야 끝난다 (꼬리 지연)."""
    p_any_slow = 1 - (1 - SLOW_P) ** width
    base = TASK_MS * (1 + p_any_slow * (SLOW_X - 1))
    p_any_fail = 1 - (1 - FAIL) ** width
    return base + p_any_fail * RETRY_MS


def parallel(n, width, merge_per_branch=MERGE_PER_BRANCH):
    waves = -(-n // width)
    spread = waves * wave_ms(width)      # 폭으로 나눠지는 부분
    merge = n * merge_per_branch         # 폭과 무관한 부분
    return spread + merge, spread, merge


print(f"갈래 하나 기대 시간 BRANCH_MS = {BRANCH_MS:.0f}ms")
print(f"폭 4의 물결 하나  wave_ms(4) = {wave_ms(4):.2f}ms")
print(f"  → 갈래당 병렬 시간 {wave_ms(4) / 4:.2f}ms,  갈래당 합류 {MERGE_PER_BRANCH}ms")
# 출력: 갈래 하나 기대 시간 BRANCH_MS = 954ms
# 출력: 폭 4의 물결 하나  wave_ms(4) = 1871.10ms
# 출력:   → 갈래당 병렬 시간 467.78ms,  갈래당 합류 140ms

# %% [markdown]
# ## 2단계 — 갈래를 늘려도 이득이 안 오른다
#
# 폭을 4로 고정하고 갈래 수 $n$만 키운다. 1.57배에서 **정확히** 멈춘다.

# %%
print(f"{'갈래 수':>8}{'직렬(ms)':>12}{'병렬4폭(ms)':>14}{'펴는값':>11}{'합류값':>10}{'이득':>9}")
print("-" * 66)
for n in (2, 4, 8, 16, 32, 64, 256, 1024):
    s = serial(n)
    p, spread, merge = parallel(n, 4)
    print(f"{n:>8}{s:>12,.0f}{p:>14,.0f}{spread:>11,.0f}{merge:>10,.0f}{s / p:>8.4f}x")
# 출력:     갈래 수      직렬(ms)      병렬4폭(ms)        펴는값       합류값       이득
# 출력: ------------------------------------------------------------------
# 출력:        2       1,908         2,151      1,871       280  0.8870x
# 출력:        4       3,816         2,431      1,871       560  1.5697x
# 출력:        8       7,632         4,862      3,742     1,120  1.5697x
# 출력:       16      15,264         9,724      7,484     2,240  1.5697x
# 출력:       32      30,528        19,449     14,969     4,480  1.5697x
# 출력:       64      61,056        38,898     29,938     8,960  1.5697x
# 출력:      256     244,224       155,590    119,750    35,840  1.5697x
# 출력:     1024     976,896       622,362    479,002   143,360  1.5697x

# %% [markdown]
# ## 3단계 — $n$이 약분된다
#
# $n$이 $W$의 배수라 $\lceil n/W \rceil = n/W$ 이면
#
# $$
# \text{gain}(W) = \frac{\text{BRANCH\_MS} \cdot n}{\frac{n}{W}\,\text{wave\_ms}(W) + \text{MERGE} \cdot n}
# = \frac{\text{BRANCH\_MS}}{\frac{\text{wave\_ms}(W)}{W} + \text{MERGE}}
# $$
#
# 분자·분모의 $n$이 통째로 사라진다. 그래서 점근선이 아니라 **딱 붙는 값**이다.

# %%
def gain_closed(width, merge_per_branch=MERGE_PER_BRANCH):
    """n에 무관한 닫힌 형태의 이득 (n이 width의 배수일 때 정확)."""
    return BRANCH_MS / (wave_ms(width) / width + merge_per_branch)


print(f"닫힌 형태 gain(4) = {BRANCH_MS} / ({wave_ms(4) / 4:.2f} + {MERGE_PER_BRANCH}) "
      f"= {gain_closed(4):.4f}")
print(f"실측  serial(1024)/parallel(1024,4) = {serial(1024) / parallel(1024, 4)[0]:.4f}")
print(f"일치? {abs(gain_closed(4) - serial(1024) / parallel(1024, 4)[0]) < 1e-12}")
# 출력: 닫힌 형태 gain(4) = 954.0 / (467.78 + 140) = 1.5697
# 출력: 실측  serial(1024)/parallel(1024,4) = 1.5697
# 출력: 일치? True

# %% [markdown]
# ## 4단계 — 4배가 1.57배로 깎이는 과정을 두 단으로 쪼갠다
#
# * **합류를 뺀 이상적 선형**: $\text{gain} = W = 4.00$
# * **합류만 넣은 암달**: $\dfrac{954}{954/4 + 140} = 2.52$  ← 순수하게 직렬 부분의 몫
# * **꼬리 지연까지 넣은 실제**: $\dfrac{954}{1871.10/4 + 140} = 1.57$

# %%
W = 4
ideal = float(W)
amdahl_only = BRANCH_MS / (BRANCH_MS / W + MERGE_PER_BRANCH)   # 꼬리 없음
merge_only_tail = BRANCH_MS / (wave_ms(W) / W)                 # 합류 없음, 꼬리만
actual = gain_closed(W)

print(f"{'단계':<34}{'이득':>8}{'직전 대비':>11}")
print("-" * 53)
print(f"{'이상적 선형 (합류 0, 꼬리 없음)':<34}{ideal:>7.2f}x{'-':>11}")
print(f"{'+ 합류 140ms/갈래 (= 암달)':<34}{amdahl_only:>7.2f}x{amdahl_only / ideal - 1:>10.0%}")
print(f"{'+ 꼬리 지연 (wave_ms)':<34}{actual:>7.2f}x{actual / amdahl_only - 1:>10.0%}")
print(f"\n참고: 꼬리만 있고 합류가 없다면 {merge_only_tail:.2f}x")
# 출력: 단계                                      이득      직전 대비
# 출력: -----------------------------------------------------
# 출력: 이상적 선형 (합류 0, 꼬리 없음)                 4.00x          -
# 출력: + 합류 140ms/갈래 (= 암달)                 2.52x      -37%
# 출력: + 꼬리 지연 (wave_ms)                    1.57x      -38%
# 출력:
# 출력: 참고: 꼬리만 있고 합류가 없다면 2.04x

# %% [markdown]
# ## 5단계 — 암달의 법칙으로 환산
#
# 암달의 법칙: 전체 중 직렬 비율이 $s$면
#
# $$
# S(W) = \frac{1}{s + \dfrac{1-s}{W}}, \qquad \lim_{W\to\infty} S(W) = \frac{1}{s}
# $$
#
# 여기서 직렬 부분은 **합류**다. 갈래당 병렬 가능 954ms, 합류 140ms이므로
#
# $$
# s = \frac{140}{954+140} = 0.128 \;\Rightarrow\; S(\infty) = \frac{1}{0.128} = 7.81
# $$
#
# 예제는 직렬 기준선에 합류를 넣지 않으므로($\text{serial}=954n$)
# 예제 기준의 천장은 $954/140 = 6.81$배다.

# %%
s = MERGE_PER_BRANCH / (BRANCH_MS + MERGE_PER_BRANCH)
print(f"직렬 비율 s = {MERGE_PER_BRANCH}/{BRANCH_MS + MERGE_PER_BRANCH:.0f} = {s:.4f}")
print(f"암달 S(4)   = {1 / (s + (1 - s) / 4):.3f}   (= 꼬리 없는 2.52x × {1 + MERGE_PER_BRANCH / BRANCH_MS:.4f})")
print(f"암달 S(inf) = {1 / s:.3f}")
print(f"예제 기준 천장 gain(inf) = BRANCH_MS/MERGE = {BRANCH_MS / MERGE_PER_BRANCH:.3f}x")
print(f"실제로 폭 4096: {gain_closed(4096):.3f}x   (wave_ms 는 {wave_ms(4096):.0f}ms 로 포화)")
# 출력: 직렬 비율 s = 140/1094 = 0.1280
# 출력: 암달 S(4)   = 2.890   (= 꼬리 없는 2.52x × 1.1468)
# 출력: 암달 S(inf) = 7.814
# 출력: 예제 기준 천장 gain(inf) = BRANCH_MS/MERGE = 6.814x
# 출력: 실제로 폭 4096: 6.766x   (wave_ms 는 4050ms 로 포화)

# %% [markdown]
# ## 6단계 — 폭 1~16 이득 곡선
#
# 선형(이상) / 암달(합류만) / 실제(합류+꼬리) 셋을 나란히 놓는다.

# %%
WIDTHS = list(range(1, 17))
g_linear = [float(w) for w in WIDTHS]
g_amdahl = [BRANCH_MS / (BRANCH_MS / w + MERGE_PER_BRANCH) for w in WIDTHS]
g_actual = [gain_closed(w) for w in WIDTHS]

print(f"{'폭':>4}{'선형':>9}{'암달':>9}{'실제':>9}{'물결하나(ms)':>15}{'합류비중':>10}")
print("-" * 57)
for w, a, b, c in zip(WIDTHS, g_linear, g_amdahl, g_actual):
    share = MERGE_PER_BRANCH / (wave_ms(w) / w + MERGE_PER_BRANCH)
    if w in (1, 2, 4, 8, 16):
        print(f"{w:>4}{a:>8.2f}x{b:>8.2f}x{c:>8.2f}x{wave_ms(w):>15,.0f}{share:>10.1%}")
# 출력:   폭       선형       암달       실제       물결하나(ms)      합류비중
# 출력: ---------------------------------------------------------
# 출력:    1    1.00x   0.87x   0.72x          1,179      10.6%
# 출력:    2    2.00x   1.55x   1.11x          1,432      16.4%
# 출력:    4    4.00x   2.52x   1.57x          1,871      23.0%
# 출력:    8    8.00x   3.68x   2.09x          2,533      30.7%
# 출력:   16   16.00x   4.78x   2.76x          3,299      40.4%

# %% [markdown]
# 폭을 4에서 16으로 **4배** 키웠는데 이득은 1.57 → 2.76배, 겨우 **1.76배**만 늘었다.
# 그동안 합류 비중은 23% → 40%로 올라간다. 직렬 부분의 지분이 커지는 것이
# 곧 천장이 내려앉는 것이다.

# %% [markdown]
# ## 7단계 — 합류 값을 줄이는 편이 폭을 키우는 것보다 크게 듣는다

# %%
print("폭은 4로 고정, 합류 값만 바꾼다:")
for m in (0, 35, 70, 140, 280, 560):
    print(f"  MERGE={m:>4}ms/갈래 → 이득 {gain_closed(4, m):>5.2f}x   "
          f"천장(폭 inf) {BRANCH_MS / m if m else float('inf'):>7.2f}x")
print("\n합류는 그대로 두고 폭만 키운다:")
for w in (4, 8, 16, 32):
    print(f"  폭 {w:>3} → 이득 {gain_closed(w):>5.2f}x")
# 출력: 폭은 4로 고정, 합류 값만 바꾼다:
# 출력:   MERGE=   0ms/갈래 → 이득  2.04x   천장(폭 inf)     infx
# 출력:   MERGE=  35ms/갈래 → 이득  1.90x   천장(폭 inf)   27.26x
# 출력:   MERGE=  70ms/갈래 → 이득  1.77x   천장(폭 inf)   13.63x
# 출력:   MERGE= 140ms/갈래 → 이득  1.57x   천장(폭 inf)    6.81x
# 출력:   MERGE= 280ms/갈래 → 이득  1.28x   천장(폭 inf)    3.41x
# 출력:   MERGE= 560ms/갈래 → 이득  0.93x   천장(폭 inf)    1.70x
# 출력:
# 출력: 합류는 그대로 두고 폭만 키운다:
# 출력:   폭   4 → 이득  1.57x
# 출력:   폭   8 → 이득  2.09x
# 출력:   폭  16 → 이득  2.76x
# 출력:   폭  32 → 이득  3.67x

# %% [markdown]
# ## 8단계 — 최악의 경우: 합류가 $O(n^2)$이면 천장이 아니라 절벽이다
#
# 갈래끼리 비교하는 합류(전체 재정렬, 쌍쌍 중복 제거, 교차 검증)는
# `n·140`이 아니라 $c\,n^2$이다. 그러면 $n$이 약분되지 않고 이득이 1 아래로 내려간다.

# %%
C2 = 1.2  # 갈래 쌍당 합류 비용(ms)


def parallel_quadratic(n, width):
    return -(-n // width) * wave_ms(width) + C2 * n * n


print(f"{'갈래 수':>8}{'O(n) 합류 이득':>16}{'O(n^2) 합류 이득':>18}")
print("-" * 42)
for n in (4, 16, 64, 256, 1024):
    print(f"{n:>8}{serial(n) / parallel(n, 4)[0]:>15.2f}x"
          f"{serial(n) / parallel_quadratic(n, 4):>17.2f}x")
# 출력:     갈래 수      O(n) 합류 이득      O(n^2) 합류 이득
# 출력: ------------------------------------------
# 출력:        4           1.57x            2.02x
# 출력:       16           1.57x            1.96x
# 출력:       64           1.57x            1.75x
# 출력:      256           1.57x            1.23x
# 출력:     1024           1.57x            0.56x
#
# n 이 작을 때는 O(n^2) 합류가 오히려 싸 보인다(쌍이 적으니까). 그런데
# O(n) 합류는 n 과 무관하게 1.57x 를 유지하는 반면, O(n^2) 는 n 이 커지면
# 계속 내려가서 결국 1 아래, 즉 «직렬보다 느리다»로 간다. 천장이 아니라 절벽이다.

# %% [markdown]
# ## 9단계 — 그래프

# %%
COL_LINEAR = "#9aa4b2"
COL_AMDAHL = "#f0a63a"
COL_ACTUAL = "#3b7dd8"
COL_CEIL = "#d1495b"

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "폭 4 고정 · 갈래 수를 늘려도 1.57배에서 멈춘다",
        "폭별 이득 — 선형 vs 암달 vs 실제",
        "폭 4에서 4.00x → 1.57x 로 깎이는 과정",
        "합류 값이 천장을 정한다 (폭 4)",
    ),
)

# (1,1) n별 이득
NS = [2, 4, 8, 12, 16, 24, 32, 48, 64, 128, 256, 512, 1024]
fig.add_trace(go.Scatter(
    x=NS, y=[serial(n) / parallel(n, 4)[0] for n in NS],
    mode="lines+markers", name="실제 이득 (폭 4)",
    line=dict(color=COL_ACTUAL, width=2.5), marker=dict(size=7),
), row=1, col=1)
fig.add_hline(y=gain_closed(4), line=dict(color=COL_CEIL, dash="dash", width=2),
              annotation_text=f"천장 {gain_closed(4):.2f}x = 954/(1871.1/4+140)",
              annotation_position="top right", row=1, col=1)
fig.add_hline(y=4.0, line=dict(color=COL_LINEAR, dash="dot", width=1.5),
              annotation_text="기대했던 4.00x", annotation_position="bottom right",
              row=1, col=1)
fig.update_xaxes(type="log", title_text="갈래 수 n (log)", row=1, col=1)
fig.update_yaxes(title_text="이득 (배)", range=[0, 4.5], row=1, col=1)

# (1,2) 폭별 이득
fig.add_trace(go.Scatter(x=WIDTHS, y=g_linear, mode="lines", name="선형 (이상)",
                         line=dict(color=COL_LINEAR, dash="dot", width=2)), row=1, col=2)
fig.add_trace(go.Scatter(x=WIDTHS, y=g_amdahl, mode="lines+markers", name="암달 (합류만)",
                         line=dict(color=COL_AMDAHL, width=2.5), marker=dict(size=6)),
              row=1, col=2)
fig.add_trace(go.Scatter(x=WIDTHS, y=g_actual, mode="lines+markers", name="실제 (합류+꼬리)",
                         line=dict(color=COL_ACTUAL, width=2.5), marker=dict(size=6)),
              row=1, col=2)
fig.add_hline(y=BRANCH_MS / MERGE_PER_BRANCH,
              line=dict(color=COL_CEIL, dash="dash", width=2),
              annotation_text=f"암달 한계 954/140 = {BRANCH_MS / MERGE_PER_BRANCH:.2f}x",
              annotation_position="top left", row=1, col=2)
fig.update_xaxes(title_text="동시 폭 W", dtick=2, row=1, col=2)
fig.update_yaxes(title_text="이득 (배)", range=[0, 17], row=1, col=2)

# (2,1) 폭포: 4.00 → 2.52 → 1.57
fig.add_trace(go.Bar(
    x=["이상적 선형", "+ 합류(암달)", "+ 꼬리 지연"],
    y=[ideal, amdahl_only, actual],
    marker_color=[COL_LINEAR, COL_AMDAHL, COL_ACTUAL],
    text=[f"{v:.2f}x" for v in (ideal, amdahl_only, actual)],
    textposition="outside", showlegend=False,
), row=2, col=1)
fig.update_yaxes(title_text="이득 (배)", range=[0, 4.8], row=2, col=1)

# (2,2) 합류 값 스윕
MS = list(range(0, 401, 10))
fig.add_trace(go.Scatter(
    x=MS, y=[gain_closed(4, m) for m in MS], mode="lines", name="이득 (폭 4)",
    line=dict(color=COL_ACTUAL, width=2.5), showlegend=False,
), row=2, col=2)
fig.add_vline(x=MERGE_PER_BRANCH, line=dict(color=COL_CEIL, dash="dash", width=2),
              annotation_text="예제값 140ms → 1.57x", annotation_position="top right",
              row=2, col=2)
fig.add_hline(y=1.0, line=dict(color="#888", dash="dot", width=1),
              annotation_text="1.0x = 병렬화 무의미", annotation_position="bottom left",
              row=2, col=2)
fig.update_xaxes(title_text="갈래당 합류 비용 (ms)", row=2, col=2)
fig.update_yaxes(title_text="이득 (배)", row=2, col=2)

fig.update_layout(
    title=dict(text="폭 4인데 4배가 아닌 이유 — 합류는 폭으로 나눠지지 않는다", x=0.02),
    height=820, width=1180, template="plotly_white",
    legend=dict(orientation="h", y=-0.06, x=0.02),
    margin=dict(t=90, b=90),
)

_show(fig)

PNG = os.path.join(HERE, "expy.png")
fig.write_image(PNG, scale=2)  # kaleido 필요
print(f"저장: {PNG}")
# 출력: 저장: .../expy.png

# %% [markdown]
# ## 정리
#
# * 병렬화가 나누는 것은 **펴는 값뿐**이다. 합류 값은 `n × 갈래당 비용`으로 그대로 남는다.
# * $n$이 약분되므로 갈래를 늘려도 이득은 **정확히 1.57배**에 머문다. 점근이 아니라 상수다.
# * 4.00x → 2.52x 는 순수하게 **암달**(합류 = 직렬 부분)의 몫이고,
#   2.52x → 1.57x 는 **꼬리 지연**(물결은 최악 갈래를 기다린다)의 몫이다.
# * 폭을 4배 키워도 이득은 1.76배만 오른다. 반면 합류 값을 반으로 줄이면
#   폭을 그대로 두고도 1.57 → 1.77배가 된다. **합류를 먼저 프로파일하라.**
# * 합류에 갈래 간 비교($O(n^2)$)가 있으면 천장이 아니라 절벽이다. $n$이 커질수록
#   이득이 1 아래로 떨어진다.
