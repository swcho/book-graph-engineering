# %% [markdown]
# # `ex2_fanout.py` — 갈래 2개일 때 병렬이 더 느린 이유
#
# 25장 예제 2의 시간 모델을 그대로 재현하고, **갈래 수 $n=2$** 에서
# 이득이 $0.89\times$(= 손해)로 나오는 이유를 **항별로 분해**한다.
#
# 모델은 세 덩어리다.
#
# $$
# T_{\text{직렬}}(n) = n\,T + n\,p_f\,R
# $$
#
# $$
# T_{\text{병렬}}(n, w) = \underbrace{\left\lceil \frac{n}{w} \right\rceil}_{\text{물결 수}} \cdot \underbrace{\Big[\, T\big(1 + P_{\text{slow}}(w)(x-1)\big) + P_{\text{fail}}(w)\,R \,\Big]}_{\text{물결 하나} = wave\_ms(w)} \;+\; \underbrace{n \cdot m}_{\text{합류}}
# $$
#
# 여기서 «하나라도» 확률이 폭에 따라 커지는 게 핵심이다.
#
# $$
# P_{\text{slow}}(w) = 1 - (1 - p_s)^{w}, \qquad P_{\text{fail}}(w) = 1 - (1 - p_f)^{w}
# $$
#
# | 기호 | 뜻 | 값 |
# |---|---|---|
# | $T$ | 갈래 하나 처리 시간 | 900 ms |
# | $m$ | 합류할 때 **갈래당** 드는 시간 | 140 ms |
# | $p_f$ | 갈래 하나가 실패할 확률 | 0.06 |
# | $R$ | 재시도 시간 | 900 ms |
# | $p_s$ | 갈래 하나가 «느린 놈»일 확률 | 0.10 |
# | $x$ | 느린 놈 배수 | 3.5 |
#
# 필요 패키지: plotly, kaleido (그림 저장용)

# %%
import math

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# ex2_fanout.py 의 상수 그대로
TASK_MS = 900           # 갈래 하나 처리 시간            T
MERGE_PER_BRANCH = 140  # 합류할 때 갈래당 드는 시간      m
FAIL = 0.06             # 갈래 하나가 실패할 확률          p_f
RETRY_MS = TASK_MS      # 실패하면 한 번 더               R
SLOW_P = 0.10           # 갈래 하나가 «느린 놈»일 확률     p_s
SLOW_X = 3.5            # 느린 놈은 이만큼 더 걸린다        x

print(f"T={TASK_MS}ms  m={MERGE_PER_BRANCH}ms  p_f={FAIL}  p_s={SLOW_P}  x={SLOW_X}")
# 출력: T=900ms  m=140ms  p_f=0.06  p_s=0.1  x=3.5


# %% [markdown]
# ## 1단계 — 원본 함수 재현
#
# `wave_ms(width)` 는 «한 물결은 제일 느린 갈래가 끝나야 끝난다»를 확률로 근사한다.
# 폭 안에 느린 놈이 **하나라도** 있으면 그 물결 전체가 느려진다.

# %%
def serial(n):
    ms = n * TASK_MS
    ms += n * FAIL * RETRY_MS
    return ms, 0


def wave_ms(width):
    """한 물결은 «제일 느린 갈래»가 끝나야 끝난다."""
    p_any_slow = 1 - (1 - SLOW_P) ** width
    base = TASK_MS * (1 + p_any_slow * (SLOW_X - 1))
    p_any_fail = 1 - (1 - FAIL) ** width
    return base + p_any_fail * RETRY_MS


def parallel(n, width):
    waves = -(-n // width)
    ms = waves * wave_ms(width)
    merge = n * MERGE_PER_BRANCH
    return ms + merge, merge


s2, _ = serial(2)
p2, merge2 = parallel(2, 4)
print(f"n=2  직렬 {s2:,.1f}ms   병렬(폭4) {p2:,.1f}ms   그중 합류 {merge2:,.0f}ms")
print(f"이득 = {s2:.1f} / {p2:.1f} = {s2 / p2:.2f}x  →  {'손해' if s2 / p2 < 1 else '이득'}")
# 출력: n=2  직렬 1,908.0ms   병렬(폭4) 2,151.1ms   그중 합류 280ms
# 출력: 이득 = 1908.0 / 2151.1 = 0.89x  →  손해


# %% [markdown]
# ## 2단계 — 항별 분해: 아끼는 값 vs 치르는 값
#
# 갈래가 2개뿐이면 물결은 1개다. 즉 **직렬 900+900 → 병렬 900 하나**로 접혀서
# $T$ 하나(900ms)를 아낀다. 이게 «펴서 아끼는 값»의 전부다.
#
# 그 900ms 를 아끼려고 치르는 값은 셋이다.
#
# 1. **꼬리 지연** — `wave_ms(4)` 의 base 가 900 이 아니라 1,673.8. 느린 놈 할증 +773.8ms
# 2. **재시도 기댓값 증가** — 직렬은 갈래마다 독립으로 $p_f R$ 을 더하는데(2×54=108),
#    병렬은 «폭 안에 하나라도 실패»라 $P_{\text{fail}}(4) R = 197.3$
# 3. **합류** — 갈래 수에 **비례**한다. $n\,m = 2 \times 140 = 280$ms. 펴도 안 줄어든다

# %%
p_any_slow = 1 - (1 - SLOW_P) ** 4
base4 = TASK_MS * (1 + p_any_slow * (SLOW_X - 1))
p_any_fail = 1 - (1 - FAIL) ** 4

tail = base4 - TASK_MS                      # 꼬리 지연 할증
retry_par = p_any_fail * RETRY_MS           # 병렬 재시도 기댓값
retry_ser = 2 * FAIL * RETRY_MS             # 직렬 재시도 기댓값
merge = 2 * MERGE_PER_BRANCH                # 합류

saved = TASK_MS                             # 물결로 접혀서 아끼는 값 (900*2 -> 900*1)
paid = tail + (retry_par - retry_ser) + merge

print(f"P_slow(4) = 1-0.9^4  = {p_any_slow:.4f}   →  base = {base4:,.1f}ms (꼬리 할증 +{tail:,.1f})")
print(f"P_fail(4) = 1-0.94^4 = {p_any_fail:.4f}   →  재시도 {retry_par:,.1f}ms (직렬은 {retry_ser:,.1f})")
print()
print(f"  아끼는 값  : 물결로 접힘        +{saved:>8,.1f}ms")
print(f"  치르는 값 1: 꼬리 지연          -{tail:>8,.1f}ms")
print(f"  치르는 값 2: 재시도 증가        -{retry_par - retry_ser:>8,.1f}ms")
print(f"  치르는 값 3: 합류 (n*m)         -{merge:>8,.1f}ms")
print(f"  {'-' * 42}")
print(f"  합계                            {saved - paid:>+9,.1f}ms   (양수면 이득)")
print(f"\n검산: 직렬 {s2:,.1f} - 병렬 {p2:,.1f} = {s2 - p2:+,.1f}ms")
# 출력: P_slow(4) = 1-0.9^4  = 0.3439   →  base = 1,673.8ms (꼬리 할증 +773.8)
# 출력: P_fail(4) = 1-0.94^4 = 0.2193   →  재시도 197.3ms (직렬은 108.0)
# 출력:
# 출력:   아끼는 값  : 물결로 접힘        +   900.0ms
# 출력:   치르는 값 1: 꼬리 지연          -   773.8ms
# 출력:   치르는 값 2: 재시도 증가        -    89.3ms
# 출력:   치르는 값 3: 합류 (n*m)         -   280.0ms
# 출력:   ------------------------------------------
# 출력:   합계                              -243.1ms   (양수면 이득)
# 출력:
# 출력: 검산: 직렬 1,908.0 - 병렬 2,151.1 = -243.1ms


# %% [markdown]
# ## 3단계 — 갈래 수를 늘리면? (원본 첫 표)
#
# $n=2$ 는 손해지만 $n$ 이 커지면 이득이 생긴다. 다만 **천장이 있다**.
#
# 물결 수는 $\lceil n/4 \rceil$ 로 «나누기»인데, 합류는 $n\,m$ 으로 «비례»다.
# $n \to \infty$ 에서 이득의 상한은
#
# $$
# \lim_{n\to\infty}\frac{n(T + p_f R)}{\frac{n}{w}\,wave\_ms(w) + n m}
# = \frac{T + p_f R}{\frac{wave\_ms(w)}{w} + m}
# $$

# %%
ns = [2, 4, 8, 16, 32, 64]
rows = []
print(f"{'갈래 수':>7}{'직렬(ms)':>12}{'병렬 4폭(ms)':>14}{'그중 합류':>11}{'이득':>9}")
print("-" * 55)
for n in ns:
    sv, _ = serial(n)
    pv, mg = parallel(n, 4)
    rows.append((n, sv, pv, mg, sv / pv))
    mark = "" if sv / pv > 1.15 else "  ← 별 이득 없음"
    print(f"{n:>7}{sv:>12,.0f}{pv:>14,.0f}{mg:>11,.0f}{sv / pv:>8.2f}x{mark}")

ceiling = (TASK_MS + FAIL * RETRY_MS) / (wave_ms(4) / 4 + MERGE_PER_BRANCH)
print(f"\nn→무한 이득 상한 = {ceiling:.2f}x  (폭이 4인데 4배가 아니다)")
# 출력:     갈래 수    직렬(ms)  병렬 4폭(ms)   그중 합류      이득
# 출력: -------------------------------------------------------
# 출력:       2       1,908         2,151        280    0.89x  ← 별 이득 없음
# 출력:       4       3,816         2,431        560    1.57x
# 출력:       8       7,632         4,862      1,120    1.57x
# 출력:      16      15,264         9,724      2,240    1.57x
# 출력:      32      30,528        19,449      4,480    1.57x
# 출력:      64      61,056        38,898      8,960    1.57x
# 출력:
# 출력: n→무한 이득 상한 = 1.57x  (폭이 4인데 4배가 아니다)


# %% [markdown]
# ## 4단계 — 합류를 없애면 $n=2$ 도 이득이 되나?
#
# 세 항 중 무엇을 지우면 $n=2$ 가 이득으로 돌아서는지 확인한다.
# 답: 합류를 지우면 겨우 $1.02\times$ (본전). **더 크게 듣는 건 꼬리 지연**($1.39\times$)이다.
#
# 그리고 하나 더. 원본 코드는 $n=2$ 인데도 `wave_ms(4)` 를 부른다.
# 갈래가 2개면 폭도 실질 2인데 **폭 4의 꼬리 위험**을 물린 셈이다.
# 폭을 실제 갈래 수로 맞추면(`min(n, w)`) 결과가 어떻게 달라지는지도 같이 본다.

# %%
def parallel_variant(n, width, use_merge=True, use_tail=True, clamp=False):
    w = min(n, width) if clamp else width
    waves = -(-n // width)
    p_any_slow = 1 - (1 - SLOW_P) ** w
    base = TASK_MS * (1 + (p_any_slow * (SLOW_X - 1) if use_tail else 0.0))
    p_any_fail = 1 - (1 - FAIL) ** w
    ms = waves * (base + p_any_fail * RETRY_MS)
    return ms + (n * MERGE_PER_BRANCH if use_merge else 0)


cases = [
    ("원본 그대로", dict()),
    ("합류 0 (m=0)", dict(use_merge=False)),
    ("꼬리 지연 없음", dict(use_tail=False)),
    ("합류 0 + 꼬리 없음", dict(use_merge=False, use_tail=False)),
    ("폭을 min(n,w)=2 로 clamp", dict(clamp=True)),
]
print(f"{'변형':<26}{'병렬(ms)':>11}{'이득':>9}")
print("-" * 46)
for label, kw in cases:
    pv = parallel_variant(2, 4, **kw)
    print(f"{label:<26}{pv:>11,.0f}{s2 / pv:>8.2f}x")
# 출력: 변형                           병렬(ms)     이득
# 출력: ----------------------------------------------
# 출력: 원본 그대로                        2,151    0.89x
# 출력: 합류 0 (m=0)                     1,871    1.02x
# 출력: 꼬리 지연 없음                      1,377    1.39x
# 출력: 합류 0 + 꼬리 없음                  1,097    1.74x
# 출력: 폭을 min(n,w)=2 로 clamp           1,712    1.11x


# %% [markdown]
# ## 5단계 — 물결 하나는 길어지고 총 시간은 줄어든다 (원본 둘째 표)
#
# 저자가 틀렸다고 고백한 부분. «폭을 키우면 실패 확률이 올라 손해»가 아니다.
# 물결 수가 줄어드는 효과가 훨씬 크다. 대신 **물결 하나가 길어진다** = 꼬리 지연 = 변동성.

# %%
widths = [1, 2, 4, 8, 16]
print(f"{'동시 폭':>7}{'물결 수':>9}{'물결 하나(ms)':>15}{'총 시간(ms)':>14}")
print("-" * 46)
sweep = []
for w in widths:
    pv, _ = parallel(16, w)
    sweep.append((w, math.ceil(16 / w), wave_ms(w), pv))
    print(f"{w:>7}{-(-16 // w):>9}{wave_ms(w):>15,.0f}{pv:>14,.0f}")
print(f"\n물결 하나: 1폭 {wave_ms(1):,.0f}ms → 16폭 {wave_ms(16):,.0f}ms  ({wave_ms(16) / wave_ms(1):.1f}배)")
# 출력:     동시 폭     물결 수    물결 하나(ms)     총 시간(ms)
# 출력: ----------------------------------------------
# 출력:       1        16          1,179         21,104
# 출력:       2         8          1,432         13,698
# 출력:       4         4          1,871         9,724
# 출력:       8         2          2,533         7,306
# 출력:      16         1          3,299         5,539
# 출력:
# 출력: 물결 하나: 1폭 1,179ms → 16폭 3,299ms  (2.8배)


# %% [markdown]
# ## 6단계 — 그림
#
# - 왼쪽: $n=2$ 에서 직렬 vs 병렬을 **항별로 쌓은 막대**. 병렬 쪽 초과분이 눈에 보인다.
# - 오른쪽: 갈래 수별 이득 곡선. $n=2$ 만 1.0 아래고, 나머지는 1.57x 천장에 붙는다.

# %%
fig = make_subplots(
    rows=1,
    cols=2,
    subplot_titles=("n=2 항별 분해 (ms)", "갈래 수별 이득 (폭 4)"),
    column_widths=[0.45, 0.55],
)

# --- 왼쪽: 스택 막대
cats = ["직렬", "병렬(폭 4)"]
stack = [
    ("기본 작업 T", [2 * TASK_MS, TASK_MS], "#4C78A8"),
    ("재시도", [retry_ser, retry_par], "#F58518"),
    ("꼬리 지연", [0, tail], "#E45756"),
    ("합류 n·m", [0, merge], "#72B7B2"),
]
for name, vals, color in stack:
    fig.add_bar(x=cats, y=vals, name=name, marker_color=color, row=1, col=1)
fig.update_layout(barmode="stack")

fig.add_annotation(
    x="병렬(폭 4)", y=p2 + 130,
    text=f"+{p2 - s2:,.0f}ms 손해<br>{s2 / p2:.2f}x",
    showarrow=False, font=dict(size=12, color="#E45756"), row=1, col=1,
)

# --- 오른쪽: 이득 곡선
gs = [(n, serial(n)[0] / parallel(n, 4)[0]) for n in range(1, 33)]
fig.add_scatter(
    x=[g[0] for g in gs], y=[g[1] for g in gs],
    mode="lines+markers", name="이득 s/p",
    line=dict(color="#54A24B", width=2), row=1, col=2,
)
fig.add_hline(y=1.0, line=dict(color="#888", dash="dash"), row=1, col=2)
fig.add_hline(y=ceiling, line=dict(color="#B279A2", dash="dot"), row=1, col=2)
fig.add_annotation(x=26, y=ceiling + 0.09, text=f"천장 {ceiling:.2f}x", showarrow=False,
                   font=dict(size=11, color="#B279A2"), row=1, col=2)
fig.add_annotation(x=2, y=gs[1][1] - 0.16, text="n=2 → 0.89x (손해)", showarrow=True,
                   arrowhead=2, ax=55, ay=32, font=dict(size=11, color="#E45756"), row=1, col=2)

fig.update_yaxes(title_text="시간 (ms)", row=1, col=1)
fig.update_xaxes(title_text="갈래 수 n", row=1, col=2)
fig.update_yaxes(title_text="직렬 / 병렬", range=[0.5, 1.9], row=1, col=2)
fig.update_layout(
    title_text="ex2_fanout: 펴서 아끼는 값 < 합류 + 꼬리 지연 (n=2)",
    height=460, width=1050, template="plotly_white",
    legend=dict(orientation="h", y=-0.16),
)

_show(fig)
fig.write_image("expy.png", scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료


# %% [markdown]
# ## 정리
#
# 갈래 2개에서 병렬이 지는 이유는 **덧셈과 나눗셈의 싸움**이다.
#
# - 펴서 아끼는 값은 $T\big(n - \lceil n/w \rceil\big)$ — $n$ 이 작으면 거의 없다. $n=2,w=4$ 면 딱 900ms 하나
# - 치르는 값 중 **합류 $n\,m$ 은 갈래 수에 비례**해서 펴도 안 줄고,
#   **꼬리 지연은 폭에 따라 커진다** ($1-(1-p_s)^w$)
# - $n=2$: 아끼는 900 < 치르는 773.8 + 89.3 + 280 = 1,143.1 → 243.1ms 손해 → $0.89\times$
#
# 실무 함의는 «폭을 키우자»가 아니다. **합류 코드를 가볍게 유지하는 것**이
# 폭을 키우는 것보다 크게 듣는다. 천장 $1.57\times$ 를 만든 게 폭이 아니라 합류였다.
# 그리고 갈래가 몇 개 안 되면 그냥 직렬로 두는 게 빠르다.
