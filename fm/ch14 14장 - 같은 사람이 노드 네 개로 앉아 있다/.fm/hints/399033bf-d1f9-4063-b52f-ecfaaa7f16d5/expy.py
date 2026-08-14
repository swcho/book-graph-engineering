# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
#   - 표/계산 셀은 표준 라이브러리만으로 동작한다.
#   - 마지막 시각화 셀만 plotly/kaleido를 쓴다.

# %% [markdown]
# # 레코드 10만 개를 전수 비교하면 쌍이 몇 개인가?
#
# 답: **약 50억 쌍**. 정확히는
#
# $$\binom{100000}{2}=\frac{100000\times 99999}{2}=4{,}999{,}950{,}000$$
#
# 엔티티 해상도(entity resolution)의 첫 관문이 여기다.
# "일단 다 비교해 보자"가 안 되는 이유는 알고리즘이 느려서가 아니라,
# 비교해야 할 **쌍의 개수 자체가 레코드 수의 제곱으로 늘기 때문**이다.
#
# $$\binom{n}{2}=\frac{n(n-1)}{2}\sim\frac{n^2}{2}\quad(n\to\infty)$$
#
# 레코드가 10배 늘면 쌍은 100배 늘어난다. 이 셀부터 그 감각을 숫자로 잡아 본다.

# %%
from itertools import combinations
from math import comb


def n_pairs(n: int) -> int:
    """n개에서 순서 없이 2개를 뽑는 방법의 수 = 전수 비교 쌍 수."""
    return n * (n - 1) // 2


n = 100_000
print(f"n = {n:,}")
print(f"n(n-1)/2      = {n_pairs(n):,}")
print(f"math.comb(n,2)= {comb(n, 2):,}")
print(f"근사 n^2/2    = {n * n // 2:,}")
print(f"→ 약 {n_pairs(n) / 1e8:.0f}억 쌍")

# 출력: n = 100,000
# 출력: n(n-1)/2      = 4,999,950,000
# 출력: math.comb(n,2)= 4,999,950,000
# 출력: 근사 n^2/2    = 5,000,000,000
# 출력: → 약 50억 쌍

# %%
# 정의 확인 — 작은 n에서 itertools로 실제 쌍을 세어 공식과 맞춰 본다.
for small in (2, 3, 4, 12, 100):
    actual = sum(1 for _ in combinations(range(small), 2))
    assert actual == n_pairs(small), small
    print(f"n={small:>4}  실제 쌍 {actual:>6,}  공식 {n_pairs(small):>6,}")

# 출력: n=   2  실제 쌍      1  공식      1
# 출력: n=   3  실제 쌍      3  공식      3
# 출력: n=   4  실제 쌍      6  공식      6
# 출력: n=  12  실제 쌍     66  공식     66
# 출력: n= 100  실제 쌍  4,950  공식  4,950

# %% [markdown]
# ## 1. n이 커질 때 쌍은 어떻게 늘어나는가
#
# 이차 증가의 핵심은 "배율"이다. $n$이 $k$배가 되면 쌍은 대략 $k^2$배가 된다.
#
# $$\frac{\binom{kn}{2}}{\binom{n}{2}}\approx k^2$$
#
# 14장 예제의 레코드 12개는 쌍이 66개다. 눈으로 훑을 수 있다.
# 10만 개는 50억 쌍이다. 같은 방법이 아니다.

# %%
SIZES = [12, 100, 1_000, 10_000, 100_000, 1_000_000, 10_000_000]

print(f"{'n':>12} {'쌍 수':>20} {'앞 줄 대비 배율':>14}")
print("-" * 50)
prev = None
for m in SIZES:
    p = n_pairs(m)
    ratio = f"{p / prev:>13.1f}x" if prev else f"{'—':>14}"
    print(f"{m:>12,} {p:>20,} {ratio}")
    prev = p

# 출력:            n                  쌍 수      앞 줄 대비 배율
# 출력: --------------------------------------------------
# 출력:           12                   66              —
# 출력:          100                4,950          75.0x
# 출력:        1,000              499,500         100.9x
# 출력:       10,000           49,995,000         100.1x
# 출력:      100,000        4,999,950,000         100.0x
# 출력:    1,000,000      499,999,500,000         100.0x
# 출력:   10,000,000   49,999,995,000,000         100.0x

# %% [markdown]
# ## 2. "하루로 끝나지 않는다"를 시간으로 환산
#
# 쌍 하나를 비교하는 비용을 $t$라 하면 총 시간은
#
# $$T(n)=\binom{n}{2}\cdot t$$
#
# 필드 5개를 정규화하고 2-gram 자카드를 계산하는 파이썬 함수 한 번은
# 현실적으로 마이크로초 단위가 아니라 **수십~수백 마이크로초** 걸린다.
# 여기서는 낙관적인 10µs와 현실적인 100µs를 둘 다 본다.

# %%
def humanize(seconds: float) -> str:
    """초를 사람이 읽는 단위로."""
    for unit, size in (("초", 60), ("분", 60), ("시간", 24), ("일", 365)):
        if seconds < size:
            return f"{seconds:.1f}{unit}"
        seconds /= size
    return f"{seconds:.1f}년"


PER_PAIR = [("10µs", 10e-6), ("100µs", 100e-6), ("1µs (C 수준)", 1e-6)]

print(f"{'n':>10} " + " ".join(f"{label:>16}" for label, _ in PER_PAIR))
print("-" * 62)
for m in [1_000, 10_000, 100_000, 1_000_000]:
    row = [f"{humanize(n_pairs(m) * t):>16}" for _, t in PER_PAIR]
    print(f"{m:>10,} " + " ".join(row))

print()
secs = n_pairs(100_000) * 100e-6
print(f"n=100,000, 쌍당 100µs → {humanize(secs)} (초로는 {secs:,.0f}초)")
print("쌍당 10µs로 줄여도 하루를 넘지 않을 뿐, 반나절이 통째로 날아간다.")

# 출력:          n             10µs            100µs       1µs (C 수준)
# 출력: --------------------------------------------------------------
# 출력:      1,000             5.0초            50.0초             0.5초
# 출력:     10,000             8.3분            1.4시간            50.0초
# 출력:    100,000           13.9시간             5.8일            1.4시간
# 출력:  1,000,000            57.9일             1.6년             5.8일
# 출력:
# 출력: n=100,000, 쌍당 100µs → 5.8일 (초로는 499,995초)
# 출력: 쌍당 10µs로 줄여도 하루를 넘지 않을 뿐, 반나절이 통째로 날아간다.

# %% [markdown]
# ## 3. 코어를 늘리면 되지 않나
#
# 안 된다. 병렬화는 상수 배 이득이고, 문제는 **차수**다.
# 코어 32개를 완벽하게 쓴다 해도 $n$이 10배 되면 다시 원점이다.

# %%
CORES = 32
t = 100e-6
for m in (100_000, 1_000_000):
    one = n_pairs(m) * t
    print(f"n={m:>9,}  1코어 {humanize(one):>8}  {CORES}코어 {humanize(one / CORES):>8}")

print("\n32배 빨라져도 n을 10배 키우면 100배 느려진다. 상수로는 이차를 못 이긴다.")

# 출력: n=  100,000  1코어     5.8일  32코어    4.3시간
# 출력: n=1,000,000  1코어     1.6년  32코어    18.1일
# 출력:
# 출력: 32배 빨라져도 n을 10배 키우면 100배 느려진다. 상수로는 이차를 못 이긴다.

# %% [markdown]
# ## 4. 블로킹 — 차수를 깎는다
#
# 블로킹(blocking)은 "같을 가능성이 있는 것끼리만 같은 칸에 넣고, 칸 안에서만 비교"한다.
#
# 레코드 $n$개를 크기 $s$인 칸 $n/s$개로 나누면 비교 쌍은
#
# $$\frac{n}{s}\cdot\binom{s}{2}=\frac{n(s-1)}{2}\;=\;O(n)$$
#
# **칸 크기가 상수로 유지되면 선형**이 된다. 이게 블로킹의 전부다.
#
# 반대로 칸 **개수** $b$를 고정하면
#
# $$b\cdot\binom{n/b}{2}\approx\frac{n^2}{2b}\;=\;O(n^2)$$
#
# 여전히 이차다. 상수 배만 깎은 것이다.
# 즉 "블로킹했다"가 아니라 **"칸이 커지지 않는 키를 골랐다"**가 핵심이다.

# %%
def pairs_fixed_block_size(n: int, s: int) -> int:
    """칸 크기 s 고정: 칸 수 = n/s. O(n)."""
    blocks = max(1, n // s)
    per = n // blocks
    return blocks * n_pairs(per)


def pairs_fixed_block_count(n: int, b: int) -> int:
    """칸 개수 b 고정: 칸 크기 = n/b. 여전히 O(n^2)."""
    per = max(1, n // b)
    return b * n_pairs(per)


print(f"{'n':>10} {'전수':>18} {'칸크기 100 고정':>18} {'칸수 1000 고정':>18}")
print("-" * 68)
for m in [10_000, 100_000, 1_000_000]:
    print(f"{m:>10,} {n_pairs(m):>18,} "
          f"{pairs_fixed_block_size(m, 100):>18,} "
          f"{pairs_fixed_block_count(m, 1000):>18,}")

print()
full = n_pairs(100_000)
blocked = pairs_fixed_block_size(100_000, 100)
print(f"n=100,000: 전수 {full:,} → 칸크기 100 블로킹 {blocked:,}")
print(f"  줄어든 비율 {blocked / full * 100:.4f}%  ({full // blocked:,}배 감소)")
print(f"  쌍당 100µs 기준 {humanize(full * 100e-6)} → {humanize(blocked * 100e-6)}")

# 출력:          n                 전수         칸크기 100 고정         칸수 1000 고정
# 출력: --------------------------------------------------------------------
# 출력:     10,000         49,995,000            495,000             45,000
# 출력:    100,000      4,999,950,000          4,950,000          4,950,000
# 출력:  1,000,000    499,999,500,000         49,500,000        499,500,000
# 출력:
# 출력: n=100,000: 전수 4,999,950,000 → 칸크기 100 블로킹 4,950,000
# 출력:   줄어든 비율 0.0990%  (1,010배 감소)
# 출력:   쌍당 100µs 기준 5.8일 → 8.2분
#
# 읽는 법: 칸수 고정 열을 세로로 읽으면 45,000 → 4,950,000 → 499,500,000.
#   n이 10배마다 100배씩 뛴다. n=100,000에서 두 블로킹이 우연히 만나지만
#   그 뒤로는 칸수 고정 쪽이 10배씩 벌어진다. 이게 O(n)과 O(n^2)의 차이다.

# %% [markdown]
# ## 5. 이론이 아니라 14장 실제 데이터로
#
# 14장 `records.py`의 레코드 12개(= 66쌍)에 블로킹 전략 세 개를 돌려 본다.
# 전략 하나로는 놓치는 쌍이 생기므로 **합집합**을 쓴다는 게 장의 결론이다.
#
# 확인할 것이 두 가지다.
# 1. 합집합을 써도 전수 비교보다 훨씬 적다 (비용)
# 2. 그래도 놓치는 쌍이 남는다 (재현율)
#
# 후보를 줄이는 대가는 항상 재현율이다. 후보에 못 들면 점수를 매길 기회조차 없다.

# %%
import re
from collections import defaultdict

RECORDS = [
    # id, 이름, 사업자번호, 주소, 대표자, 전화
    ("r01", "가온테크", "123-45-67890", "서울 강남구 테헤란로 1", "김하늘", "02-1234-5678"),
    ("r02", "(주)가온테크", "123-45-67890", "서울 강남구 테헤란로 1", "김하늘", "02-1234-5678"),
    ("r03", "가온테크 주식회사", "", "서울 강남구 테헤란로 1길", "김하늘", "021234-5678"),
    ("r04", "GAON TECH", "123-45-67890", "", "", ""),
    ("r05", "가온테크놀로지", "999-88-77777", "부산 해운대구 센텀로 9", "박서준", "051-999-8877"),
    ("r06", "나루소프트", "222-33-44444", "서울 마포구 월드컵로 2", "이서연", "02-2222-3333"),
    ("r07", "나루소프트(주)", "555-66-77777", "서울 마포구 월드컵로 2", "이서연", "02-2222-3333"),
    ("r08", "다올물산 본사", "333-44-55555", "인천 연수구 송도로 3", "최민준", "032-333-4444"),
    ("r09", "다올물산 부산지점", "333-44-55555", "부산 사하구 낙동로 8", "정우진", "051-333-4444"),
    ("r10", "라온에너지", "444-55-66666", "대전 유성구 대덕대로 4", "한지우", "042-444-5555"),
    ("r11", "마루상사", "666-77-88888", "광주 서구 상무로 6", "오세훈", "062-666-7777"),
    ("r12", "머루상사", "666-77-88888", "광주 서구 상무로 6", "오세훈", "062-666-7777"),
]


def norm_name(s):
    s = re.sub(r"\(주\)|주식회사|\(유\)|유한회사", "", s)
    return re.sub(r"\s+", "", s)


STRATEGIES = {
    "사업자번호": lambda r: r[2] or None,
    "이름 앞 3글자": lambda r: (norm_name(r[1])[:3] or None),
    "주소 앞 2어절": lambda r: (" ".join(r[3].split()[:2]) if r[3] else None),
}


def blocked_pairs(records, keyfn):
    b = defaultdict(list)
    for r in records:
        k = keyfn(r)
        if k:
            b[k].append(r[0])
    out = set()
    for ids in b.values():
        if len(ids) > 1:
            out |= set(combinations(sorted(ids), 2))
    return out, {k: v for k, v in b.items() if len(v) > 1}


total = n_pairs(len(RECORDS))
print(f"레코드 {len(RECORDS)}개 → 전수 비교 쌍 {total}개\n")

union = set()
for label, fn in STRATEGIES.items():
    pairs, blocks = blocked_pairs(RECORDS, fn)
    union |= pairs
    print(f"[{label}] 칸 {len(blocks)}개, 비교 쌍 {len(pairs)}개 "
          f"(전수의 {len(pairs) / total * 100:.0f}%)")

print(f"\n합집합 비교 쌍 {len(union)}개 (전수 {total}개의 {len(union) / total * 100:.0f}%)")

# 정답 쌍이 후보에 들어왔는지 — 이게 재현율이다
TRUTH = [frozenset(["r01", "r02", "r03", "r04"]), frozenset(["r11", "r12"])]
truth_pairs = set()
for g in TRUTH:
    truth_pairs |= set(combinations(sorted(g), 2))
missed = truth_pairs - union
print(f"정답 쌍 {len(truth_pairs)}개 중 후보에 못 든 것 {len(missed)}개 → 재현율 "
      f"{(len(truth_pairs) - len(missed)) / len(truth_pairs) * 100:.0f}%")
print(f"못 든 쌍: {sorted(missed)}")
print("  r03은 사업자번호가 비어 있고, r04는 주소가 비어 있고 이름이 영문이다.")
print("  세 전략을 다 합쳐도 이 쌍은 같은 칸에 들어갈 길이 없다.")

# 출력: 레코드 12개 → 전수 비교 쌍 66개
# 출력:
# 출력: [사업자번호] 칸 3개, 비교 쌍 5개 (전수의 8%)
# 출력: [이름 앞 3글자] 칸 3개, 비교 쌍 8개 (전수의 12%)
# 출력: [주소 앞 2어절] 칸 3개, 비교 쌍 5개 (전수의 8%)
# 출력:
# 출력: 합집합 비교 쌍 11개 (전수 66개의 17%)
# 출력: 정답 쌍 7개 중 후보에 못 든 것 1개 → 재현율 86%
# 출력: 못 든 쌍: [('r03', 'r04')]
# 출력:   r03은 사업자번호가 비어 있고, r04는 주소가 비어 있고 이름이 영문이다.
# 출력:   세 전략을 다 합쳐도 이 쌍은 같은 칸에 들어갈 길이 없다.
#
# 참고: r03–r04를 직접 못 잡아도 r01을 매개로 이행성(r01–r03, r01–r04)으로
#       같은 군집에 들어간다. 이 부분은 14.2절(점수·임계·이행성)의 몫이다.

# %% [markdown]
# ## 6. 그림으로
#
# 왼쪽: 쌍 수의 증가(로그-로그). 전수와 "칸 수 고정"은 기울기 2(이차),
# "칸 크기 고정"은 기울기 1(선형)이다. 로그-로그에서 기울기가 곧 차수다.
# 두 블로킹 곡선이 $n=10^5$에서 한 번 교차하지만, 중요한 건 만나는 점이 아니라
# 기울기다. 그 뒤로는 주황이 파랑에서 한 자릿수씩 멀어진다.
#
# 오른쪽: 쌍당 100µs 가정에서의 소요 시간. 1시간/1일/1년 선을 그어 두면
# "하루로 끝나지 않는다"가 정확히 어디서 시작되는지 보인다.

# %%
def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


import plotly.graph_objects as go
from plotly.subplots import make_subplots

NS = [10 ** k for k in range(2, 8)]  # 100 ~ 10,000,000
full_pairs = [n_pairs(m) for m in NS]
# 칸보다 레코드가 적으면(n < 칸 수, n < 칸 크기) 쌍이 0이라 로그축에 못 그린다 → None
bs_pairs = [pairs_fixed_block_size(m, 100) or None for m in NS]
bc_pairs = [pairs_fixed_block_count(m, 1000) or None for m in NS]

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=("비교 쌍 수 (로그-로그)", "소요 시간 — 쌍당 100µs"),
    horizontal_spacing=0.12,
)

SERIES = [
    ("전수 비교 C(n,2)", full_pairs, "#d62728"),
    ("블로킹: 칸 수 1000 고정 (여전히 O(n²))", bc_pairs, "#ff7f0e"),
    ("블로킹: 칸 크기 100 고정 (O(n))", bs_pairs, "#1f77b4"),
]
for name, ys, color in SERIES:
    fig.add_trace(
        go.Scatter(x=NS, y=ys, name=name, mode="lines+markers",
                   line=dict(color=color, width=2)),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=NS, y=[(v * 100e-6 if v else None) for v in ys], name=name,
                   mode="lines+markers",
                   line=dict(color=color, width=2), showlegend=False),
        row=1, col=2,
    )

# n=100,000 지점 강조 — 이 카드의 답
fig.add_trace(
    go.Scatter(x=[100_000], y=[n_pairs(100_000)], mode="markers+text",
               marker=dict(color="#d62728", size=14, symbol="star"),
               text=["약 50억 쌍"], textposition="top left",
               showlegend=False),
    row=1, col=1,
)

from math import log10

for secs, label in ((3600, "1시간"), (86400, "1일"), (86400 * 365, "1년")):
    fig.add_hline(y=secs, line=dict(color="gray", width=1, dash="dot"), row=1, col=2)
    fig.add_annotation(
        x=log10(120), y=log10(secs), xref="x2", yref="y2",
        text=label, showarrow=False, yshift=8,
        font=dict(color="gray", size=12), xanchor="left",
    )

fig.update_xaxes(type="log", title_text="레코드 수 n", row=1, col=1)
fig.update_xaxes(type="log", title_text="레코드 수 n", row=1, col=2)
fig.update_yaxes(type="log", title_text="비교 쌍 수", row=1, col=1)
fig.update_yaxes(type="log", title_text="소요 시간 (초)", row=1, col=2)
fig.update_layout(
    title="레코드 10만 개 전수 비교 = 약 50억 쌍. 블로킹이 깎는 것은 상수가 아니라 차수다.",
    template="plotly_white", width=1100, height=520,
    legend=dict(orientation="h", yanchor="bottom", y=-0.28, x=0),
)

_show(fig)

import os
_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_png, scale=2)
print(f"저장: {_png}")

# 출력: 저장: .../expy.png

# %% [markdown]
# ## 정리
#
# - $\binom{100000}{2}=\dfrac{100000\times 99999}{2}=4{,}999{,}950{,}000$ — **약 50억 쌍**.
# - 쌍당 100µs면 5.8일, 10µs여도 13.9시간. **하루로 끝나지 않는다.**
# - 코어를 32개 써도 상수 배 이득뿐이다. $n$이 10배면 쌍은 100배다.
# - 블로킹은 **칸 크기가 상수로 유지될 때만** $O(n)$이 된다.
#   칸 개수만 고정하면 $n^2/(2b)$로 여전히 이차다.
# - 후보를 줄이면 재현율을 잃는다. 그래서 전략을 여러 개 돌리고 **합집합**을 쓴다.
#   14장 데이터에서 합집합은 전수의 17%(11쌍)로 재현율 86%였다.
#   전략을 늘리면 재현율이 오르고 후보가 늘어 느려진다. 그 균형이 설계다.
