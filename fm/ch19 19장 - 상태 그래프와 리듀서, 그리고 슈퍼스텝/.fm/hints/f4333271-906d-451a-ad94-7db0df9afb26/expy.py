# %% [markdown]
# # 상태 크기의 진짜 비용은 저장비인가?
#
# **답: 아니다.** 저장비는 월 1,600원 수준이고, 진짜 값은 **직렬화 시간**이다.
# 슈퍼스텝마다 1.9MB를 쓰고 읽으면 그 지연이 그대로 사용자 대기 시간이 된다.
#
# 이 노트북은 19장 `ex4_state_size.py`의 필드 판정표와 비용 가정을 그대로 가져와서
# 두 축(원 / 밀리초)을 **실측**으로 나란히 놓는다.
#
# 필요 패키지: `plotly`, `kaleido` (PNG 저장용). 나머지는 표준 라이브러리.
#
# > 측정값은 CPU·파이썬 버전·JSON 구현에 따라 크게 달라진다.
# > 아래 `# 출력:` 주석은 이 노트북을 작성하며 실제로 돌린 한 환경(macOS / Python 3.9.6)의 값이다.
# > 절대값이 아니라 **자릿수와 기울기**를 보라.

# %%
import json
import math
import os
import pickle
import random
import string
import timeit

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()

# dataviz 기본 팔레트(라이트 모드) 슬롯 1·2
C_ALL = "#2a78d6"   # 전부 담기
C_LEAN = "#eb6834"  # 필요한 것만
INK = "#3d3d3a"
GRID = "#e5e4df"

random.seed(19)
print("준비 완료")

# 출력:
# 준비 완료

# %% [markdown]
# ## 1. 저자의 필드 판정표 재현
#
# `ex4_state_size.py`의 표 그대로다. 판정 기준은 단 하나 — **다음 노드가 읽는가**.

# %%
# (이름, 바이트, 왜, 상태에 둘까)
FIELDS = [
    ("질문",           220,    "다음 노드가 읽는다",     True),
    ("검색 결과 원문",  84_000, "요약만 있으면 된다",     False),
    ("검색 결과 주소",  180,    "필요하면 다시 읽는다",   True),
    ("검색 결과 요약",  1_800,  "다음 노드가 읽는다",     True),
    ("모델 원본 응답",  12_000, "로그에만 쓴다",         False),
    ("중간 계산 캐시",  31_000, "같은 노드 안에서만 쓴다", False),
    ("실행 로그",       6_400,  "사람이 나중에 본다",     False),
    ("재시도 횟수",     8,      "라우팅이 읽는다",       True),
    ("체크포인트 메타", 140,    "실행기가 쓴다",         True),
]

SUPERSTEPS = 14          # 저자 가정: 실행당 슈퍼스텝 14회
RUNS_PER_DAY = 1_200     # 저자 가정: 하루 실행 1,200회
BYTES_PER_GB = 1024 ** 3
STORAGE_WON_PER_GB_MONTH = 25

ALL_B = sum(sz for _, sz, _, _ in FIELDS)
LEAN_B = sum(sz for _, sz, _, need in FIELDS if need)

print(f"{'필드':<16}{'크기':>10}  상태에 둘까")
print("-" * 44)
for name, size, _why, need in FIELDS:
    print(f"{name:<16}{size:>9,}B  {'예' if need else '아니오'}")
print("-" * 44)
print(f"전부 담으면 {ALL_B:,}B, 필요한 것만 담으면 {LEAN_B:,}B ({ALL_B / LEAN_B:.1f}배)")
print(f"실행당 체크포인트 총량(슈퍼스텝 {SUPERSTEPS}회): "
      f"{ALL_B * SUPERSTEPS / 1e6:.2f}MB  vs  {LEAN_B * SUPERSTEPS / 1e3:.1f}KB")

# 출력:
# 필드                      크기  상태에 둘까
# --------------------------------------------
# 질문                    220B  예
# 검색 결과 원문           84,000B  아니오
# 검색 결과 주소              180B  예
# 검색 결과 요약            1,800B  예
# 모델 원본 응답           12,000B  아니오
# 중간 계산 캐시           31,000B  아니오
# 실행 로그               6,400B  아니오
# 재시도 횟수                  8B  예
# 체크포인트 메타              140B  예
# --------------------------------------------
# 전부 담으면 135,748B, 필요한 것만 담으면 2,348B (57.8배)
# 실행당 체크포인트 총량(슈퍼스텝 14회): 1.90MB  vs  32.9KB
#
# → 저자가 말한 "1.9MB"의 출처가 여기다. 135,748B × 14 = 1,900,472B.
#   빼야 할 세 필드(원문 84KB + 원본 응답 12KB + 캐시 31KB + 로그 6.4KB)가 전체의 98.3%다.

# %% [markdown]
# ## 2. 저장비 — 월 1,600원이 어디서 나오는가
#
# $$
# \text{월 저장비} = \frac{S \times n_{\text{superstep}} \times r_{\text{day}} \times 30}{1024^3} \times 25\,\text{원}
# $$
#
# - $S$ = 상태 하나의 바이트 수
# - $n_{\text{superstep}} = 14$, $r_{\text{day}} = 1{,}200$
# - 25원/GB·월 = 오브젝트 스토리지 대략 단가
#
# 이 식은 **한 달치를 전부 쌓아 둔다**는 가장 비싼 가정이다.
# 그런데도 결과가 커피 한 잔 값이 안 된다는 게 요점이다.

# %%
def storage_won_per_month(state_bytes, supersteps=SUPERSTEPS, runs_per_day=RUNS_PER_DAY):
    per_run = state_bytes * supersteps
    per_day = per_run * runs_per_day
    gb_month = per_day * 30 / BYTES_PER_GB
    return gb_month * STORAGE_WON_PER_GB_MONTH, per_run, per_day, gb_month


for label, b in (("전부", ALL_B), ("필요한 것만", LEAN_B)):
    won, per_run, per_day, gb_month = storage_won_per_month(b)
    print(f"{label:<12} 실행당 {per_run / 1e3:>8,.0f}KB  하루 {per_day / 1e9:>5.2f}GB  "
          f"월 {gb_month:>6.2f}GB  월 저장비 {won:>8,.0f}원")

WON_ALL, _, _, _ = storage_won_per_month(ALL_B)
WON_LEAN, _, _, _ = storage_won_per_month(LEAN_B)
print(f"\n차액: 월 {WON_ALL - WON_LEAN:,.0f}원. 57.8배를 줄여서 아낀 돈이 이것뿐이다.")

# 출력:
# 전부           실행당    1,900KB  하루  2.28GB  월  63.72GB  월 저장비    1,593원
# 필요한 것만       실행당       33KB  하루  0.04GB  월   1.10GB  월 저장비       28원
#
# 차액: 월 1,565원. 57.8배를 줄여서 아낀 돈이 이것뿐이다.
#
# → 저자의 "월 1,600원"은 1,593원의 반올림. 의사결정 회의를 한 번 여는 비용보다 싸다.
#    즉 이 항목은 "무의미하게 작다"가 결론이고, 여기서 논쟁을 멈추면 안 된다.

# %% [markdown]
# ## 3. 진짜 비용 — 가짜 상태를 만들어 직렬화 시간을 실측한다
#
# 판정표와 같은 구성으로 상태를 만든다. 반복 문자열은 JSON 인코더가 비현실적으로 빨리
# 처리하므로, 사람이 쓴 글에 가까운 **무작위 어휘 문장**으로 채운다.

# %%
_WORDS = ["".join(random.choices(string.ascii_lowercase, k=random.randint(3, 9)))
          for _ in range(400)]


def _text(nbytes):
    """대략 nbytes 크기의 자연어 비슷한 문자열."""
    out = []
    n = 0
    while n < nbytes:
        w = random.choice(_WORDS)
        out.append(w)
        n += len(w) + 1
    return " ".join(out)[:nbytes]


def make_state(scale=1.0):
    """ex4의 필드 구성을 본뜬 가짜 상태. scale로 무거운 필드만 키우고 줄인다."""
    def sz(n):
        return max(1, int(n * scale))
    return {
        # --- 남겨야 할 작은 필드들 ---
        "질문": _text(220),
        "검색_결과_주소": [f"https://example.com/doc/{i}" for i in range(6)],
        "검색_결과_요약": _text(1_800),
        "재시도_횟수": 0,
        "체크포인트_메타": {"thread_id": "t-19", "step": 7, "ts": "2026-08-15T09:00:00Z"},
        # --- 빼야 할 무거운 필드들 ---
        "검색_결과_원문": [_text(sz(84_000) // 4) for _ in range(4)],
        "모델_원본_응답": _text(sz(12_000)),
        "중간_계산_캐시": {f"k{i}": _text(sz(31_000) // 40) for i in range(40)},
        "실행_로그": [_text(sz(6_400) // 32) for _ in range(32)],
    }


def json_bytes(state):
    return len(json.dumps(state, ensure_ascii=False).encode("utf-8"))


full = make_state(1.0)
lean = {k: v for k, v in make_state(1.0).items()
        if k in ("질문", "검색_결과_주소", "검색_결과_요약", "재시도_횟수", "체크포인트_메타")}

print(f"가짜 전체 상태  {json_bytes(full):>8,}B  (판정표 목표 {ALL_B:,}B)")
print(f"가짜 축소 상태  {json_bytes(lean):>8,}B  (판정표 목표 {LEAN_B:,}B)")

# 출력:
# 가짜 전체 상태   136,433B  (판정표 목표 135,748B)
# 가짜 축소 상태     2,375B  (판정표 목표 2,348B)
#
# → 판정표 수치를 ±2% 안에서 재현했다. 이제 이걸 직렬화한다.

# %% [markdown]
# ## 4. 라운드트립 시간 측정
#
# 체크포인트 한 번은 **쓰기(직렬화) + 읽기(역직렬화)** 한 왕복이다.
#
# $$
# t_{rt}(S) = t_{ser}(S) + t_{deser}(S)
# $$

# %%
def measure(state, repeat=7):
    """json / pickle 각각의 직렬화·역직렬화 시간(ms)을 잰다."""
    js = json.dumps(state, ensure_ascii=False)
    pk = pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)

    # 크기에 따라 반복 횟수를 조절해 측정 노이즈를 줄인다
    n = max(3, min(200, int(2_000_000 / max(1, len(js)))))

    def best(fn):
        return min(timeit.repeat(fn, repeat=repeat, number=n)) / n * 1000  # ms

    return {
        "bytes_json": len(js.encode("utf-8")),
        "json_ser": best(lambda: json.dumps(state, ensure_ascii=False)),
        "json_deser": best(lambda: json.loads(js)),
        "pickle_ser": best(lambda: pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)),
        "pickle_deser": best(lambda: pickle.loads(pk)),
    }


m_full = measure(full)
m_lean = measure(lean)

for label, m in (("전부 담기", m_full), ("필요한 것만", m_lean)):
    rt_j = m["json_ser"] + m["json_deser"]
    rt_p = m["pickle_ser"] + m["pickle_deser"]
    print(f"[{label}] {m['bytes_json']:,}B")
    print(f"    json   ser {m['json_ser']:7.3f}ms  deser {m['json_deser']:7.3f}ms  "
          f"왕복 {rt_j:7.3f}ms")
    print(f"    pickle ser {m['pickle_ser']:7.3f}ms  deser {m['pickle_deser']:7.3f}ms  "
          f"왕복 {rt_p:7.3f}ms")

# 출력:
# [전부 담기] 136,433B
#     json   ser   0.426ms  deser   0.158ms  왕복   0.584ms
#     pickle ser   0.009ms  deser   0.021ms  왕복   0.030ms
# [필요한 것만] 2,375B
#     json   ser   0.009ms  deser   0.005ms  왕복   0.014ms
#     pickle ser   0.001ms  deser   0.001ms  왕복   0.002ms
#
# → 순수 CPU 직렬화만으로도 왕복이 0.58ms vs 0.014ms, 약 42배 차이다.
#    크기 비(57.8배)와 거의 같다 — "크기가 곧 시간"이다.
#    pickle이 20배쯤 빠르지만 «전부 vs 축소» 비율은 그대로 남는다.
#    포맷을 갈아 끼워도 상수만 줄지, 크기 의존성은 안 사라진다.
#    그리고 이건 네트워크·DB 쓰기를 뺀 하한선이다. 18장의 체크포인트 실측 40~120ms에는
#    직렬화 외에 왕복 I/O가 포함돼 있다.

# %% [markdown]
# ## 5. 크기를 2KB에서 2MB까지 늘려 보면
#
# 직렬화는 대체로 바이트 수에 **선형**이다. 즉 상태를 57배 키우면 지연도 그만큼 붙는다.

# %%
TARGETS = [2_000, 8_000, 32_000, 135_748, 500_000, 1_000_000, 2_000_000]

sweep = []
for t in TARGETS:
    scale = max(0.0001, (t - 2_348) / (ALL_B - 2_348)) if t > 2_348 else 0.0001
    st = make_state(scale)
    m = measure(st, repeat=5)
    sweep.append(m)

print(f"{'크기':>10} {'json 왕복':>11} {'pickle 왕복':>13} {'ms/100KB':>10}")
print("-" * 48)
for m in sweep:
    rt_j = m["json_ser"] + m["json_deser"]
    rt_p = m["pickle_ser"] + m["pickle_deser"]
    print(f"{m['bytes_json']:>9,}B {rt_j:>10.3f}ms {rt_p:>12.3f}ms "
          f"{rt_j / (m['bytes_json'] / 100_000):>9.2f}")

# 출력:
#         크기     json 왕복     pickle 왕복   ms/100KB
# ------------------------------------------------
#     3,057B      0.025ms        0.009ms      0.83
#     8,637B      0.053ms        0.013ms      0.61
#    32,663B      0.156ms        0.018ms      0.48
#   136,438B      0.606ms        0.029ms      0.44
#   500,680B      2.325ms        0.070ms      0.46
# 1,000,631B      4.466ms        0.154ms      0.45
# 2,000,623B      8.315ms        0.316ms      0.42
#
# → 32KB 이상에서 ms/100KB가 0.42~0.48로 거의 상수다. 선형이다.
#    작은 상태에서 값이 커 보이는 건 호출 고정 오버헤드 때문이고,
#    바로 그래서 "작게 유지하면 고정비만 남는다"가 성립한다.
#    2KB → 2MB, 즉 1000배를 키우면 왕복이 0.025ms → 8.3ms로 330배 는다.
#    "상태 크기 = 지연"이라고 읽어도 된다. 저자의 8KB 기준선이 왜 의미 있는지가 여기서 보인다.

# %% [markdown]
# ## 6. 슈퍼스텝과 동시 사용자를 곱한다
#
# 체크포인트는 **슈퍼스텝마다** 왕복한다. 그래서 실행 한 번의 추가 지연은
#
# $$
# T_{\text{run}} = n_{\text{superstep}} \times \bigl(t_{ser} + t_{deser}\bigr)
# $$
#
# 이고, 동시 사용자 $u$가 같은 CPU/DB를 나눠 쓰면 체감 지연은
#
# $$
# T_{\text{felt}} \;\approx\; u \times n_{\text{superstep}} \times \bigl(t_{ser} + t_{deser}\bigr)
# $$
#
# 로 커진다(직렬화는 CPU 바운드라 코어가 모자라면 줄을 선다).
# 여기에 네트워크 왕복·DB 쓰기 지연을 더하면 18장에서 잰 **40~120ms**대가 된다.

# %%
N_SS = 8              # 문제에서 준 가정: 슈퍼스텝 8회
IO_OVERHEAD_MS = 40   # 18장 체크포인트 실측 하한(네트워크+DB 왕복)

rt_full = m_full["json_ser"] + m_full["json_deser"]
rt_lean = m_lean["json_ser"] + m_lean["json_deser"]

print(f"슈퍼스텝 {N_SS}회 기준 — 실행 한 번의 직렬화 지연")
print(f"    전부 담기    {rt_full * N_SS:8.2f}ms")
print(f"    필요한 것만  {rt_lean * N_SS:8.2f}ms")
print(f"    차이         {(rt_full - rt_lean) * N_SS:8.2f}ms\n")

print(f"동시 사용자별 누적 CPU 점유(직렬화만, +I/O {IO_OVERHEAD_MS}ms/슈퍼스텝 별도)")
print(f"{'동시 사용자':>10} {'전부(ms)':>12} {'축소(ms)':>12} {'절감(ms)':>12}")
print("-" * 50)
for u in (1, 10, 100, 1_000):
    a = rt_full * N_SS * u
    b = rt_lean * N_SS * u
    print(f"{u:>10,} {a:>11,.1f} {b:>11,.1f} {a - b:>11,.1f}")

DELAY_ALL = rt_full * N_SS
DELAY_LEAN = rt_lean * N_SS

# 출력:
# 슈퍼스텝 8회 기준 — 실행 한 번의 직렬화 지연
#     전부 담기        4.67ms
#     필요한 것만      0.11ms
#     차이             4.56ms
#
# 동시 사용자별 누적 CPU 점유(직렬화만, +I/O 40ms/슈퍼스텝 별도)
#     동시 사용자       전부(ms)       축소(ms)       절감(ms)
# --------------------------------------------------
#          1         4.7         0.1         4.6
#         10        46.7         1.1        45.6
#        100       467.2        11.2       456.0
#      1,000     4,672.1       112.5     4,559.6
#
# → 동시 사용자 100명이면 «상태를 문자열로 바꾸는 데»만 0.47초어치 CPU가 물린다.
#    슈퍼스텝을 저자 가정인 14회로 올리면 그대로 1.75배가 된다.
#    같은 절감을 돈으로 환산하면 월 1,565원이다. 어느 쪽이 의사결정을 바꾸는가.

# %% [markdown]
# ## 7. 두 축을 나란히 놓기
#
# 왼쪽: 상태 크기 대비 라운드트립 지연(선형).
# 가운데·오른쪽: 같은 결정("원문 84KB를 상태에서 뺀다")이 **원**과 **밀리초** 두 단위에서
# 각각 얼마나 움직이는가. 단위가 다르므로 축을 겹치지 않고 패널을 나눈다.

# %%
sizes_kb = [m["bytes_json"] / 1000 for m in sweep]
rt_json = [m["json_ser"] + m["json_deser"] for m in sweep]
rt_pickle = [m["pickle_ser"] + m["pickle_deser"] for m in sweep]

fig = make_subplots(
    rows=1, cols=3,
    column_widths=[0.46, 0.27, 0.27],
    horizontal_spacing=0.09,
    subplot_titles=(
        "상태 크기 → 라운드트립 지연 (실측)",
        "월 저장비 (원)",
        f"실행당 직렬화 지연 (ms, 슈퍼스텝 {N_SS}회)",
    ),
)

fig.add_trace(go.Scatter(
    x=sizes_kb, y=rt_json, name="json 왕복", mode="lines+markers",
    line=dict(color=C_ALL, width=2), marker=dict(size=8, color=C_ALL),
    hovertemplate="%{x:,.0f}KB<br>%{y:.2f}ms<extra>json</extra>",
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=sizes_kb, y=rt_pickle, name="pickle 왕복", mode="lines+markers",
    line=dict(color=C_LEAN, width=2), marker=dict(size=8, color=C_LEAN),
    hovertemplate="%{x:,.0f}KB<br>%{y:.2f}ms<extra>pickle</extra>",
), row=1, col=1)

# 기준점 직접 라벨 — 저자의 8KB 컷과 «전부 담기» 136KB.
# (로그 축에서 add_vline 은 좌표 해석이 어긋나므로 쓰지 않고 주석을 단다.
#  로그 축 주석의 x/y 는 log10 값으로 준다.)
for idx, txt, dy in ((1, "8KB 기준선", -46), (3, "전부 담기 136KB", -46)):
    fig.add_annotation(
        x=math.log10(sizes_kb[idx]), y=math.log10(rt_json[idx]),
        text=txt, showarrow=True, arrowhead=0, arrowwidth=1,
        arrowcolor="#a3a29a", ax=0, ay=dy,
        font=dict(size=11, color="#6b6a63"),
        row=1, col=1,
    )

labels = ["전부 담기", "필요한 것만"]
colors = [C_ALL, C_LEAN]

fig.add_trace(go.Bar(
    x=labels, y=[WON_ALL, WON_LEAN], marker_color=colors, showlegend=False,
    text=[f"{WON_ALL:,.0f}원", f"{WON_LEAN:,.0f}원"], textposition="outside",
    textfont=dict(color=INK, size=12),
    hovertemplate="%{x}<br>월 %{y:,.0f}원<extra></extra>",
), row=1, col=2)

fig.add_trace(go.Bar(
    x=labels, y=[DELAY_ALL, DELAY_LEAN], marker_color=colors, showlegend=False,
    text=[f"{DELAY_ALL:.1f}ms", f"{DELAY_LEAN:.2f}ms"], textposition="outside",
    textfont=dict(color=INK, size=12),
    hovertemplate="%{x}<br>실행당 %{y:.2f}ms<extra></extra>",
), row=1, col=3)

fig.update_xaxes(title_text="상태 크기 (KB)", type="log", row=1, col=1,
                 gridcolor=GRID, zeroline=False)
fig.update_yaxes(title_text="왕복 지연 (ms)", type="log", row=1, col=1,
                 gridcolor=GRID, zeroline=False)
for c in (2, 3):
    fig.update_xaxes(row=1, col=c, gridcolor=GRID, zeroline=False)
    fig.update_yaxes(row=1, col=c, gridcolor=GRID, zeroline=False, rangemode="tozero")
fig.update_yaxes(title_text="원 / 월", row=1, col=2)
fig.update_yaxes(title_text="ms / 실행", row=1, col=3)

fig.update_layout(
    title=dict(text="상태 크기의 비용: 저장비(원) vs 직렬화 지연(ms)",
               font=dict(size=17, color=INK)),
    template="plotly_white",
    font=dict(color=INK, size=12),
    legend=dict(orientation="h", y=-0.22, x=0),
    bargap=0.45,
    height=460, width=1180,
    margin=dict(t=90, b=90, l=70, r=30),
)

_show(fig)

png_path = os.path.join(HERE, "expy.png")
try:
    fig.write_image(png_path, scale=2)
    print(f"저장: {png_path}")
except Exception as e:  # kaleido 미설치 등
    print(f"PNG 저장 실패(무시 가능) — {type(e).__name__}: {e}")

# 출력:
# 저장: .../expy.png
#
# → 가운데 막대는 월 1,593원 vs 28원. 오른쪽 막대는 실행당 4.7ms vs 0.11ms.
#    같은 결정인데 사용자에게 보이는 건 오른쪽뿐이다.
#    (왼쪽 곡선은 로그–로그에서 기울기 1의 직선 = 완전한 선형)

# %% [markdown]
# ## 8. 숨은 비용까지 더한 총 계산
#
# 직렬화 CPU는 하한이다. 실제로는 슈퍼스텝마다 다음이 함께 붙는다.
#
# | 항목 | 왜 크기에 비례하나 |
# |---|---|
# | 네트워크 왕복 | 체크포인터가 원격 DB면 페이로드가 클수록 전송 시간이 는다 |
# | DB 쓰기 경합 | 큰 행/도큐먼트는 락 보유 시간과 WAL 양을 늘려 동시 실행끼리 서로를 기다리게 한다 |
# | 메모리 피크 | 직렬화 순간 원본 + 문자열 사본이 동시에 존재한다 (실질 2배) |
# | GC 압박 | 슈퍼스텝마다 수 MB 임시 객체가 생겼다 사라진다 → GC 일시정지가 잦아진다 |
#
# 이 중 어느 것도 "월 1,600원"에는 안 잡힌다.

# %%
NET_MS_PER_MB = 12.0   # 같은 리전 내 왕복, 대역폭 환산 가정치(환경마다 다름)
MEM_PEAK_FACTOR = 2.0  # 직렬화 순간 원본+사본

print(f"{'구분':<12}{'상태':>10}{'직렬화':>10}{'네트워크':>10}{'I/O 고정':>10}{'슈퍼스텝당':>12}{'실행 총계':>12}")
print("-" * 78)
rows = []
for label, state_b, rt in (("전부 담기", ALL_B, rt_full), ("필요한 것만", LEAN_B, rt_lean)):
    mb = state_b / 1e6
    net = mb * NET_MS_PER_MB * 2          # 쓰기 + 읽기
    per_ss = rt + net + IO_OVERHEAD_MS
    rows.append((label, per_ss * N_SS))
    print(f"{label:<12}{state_b / 1e3:>9,.1f}K{rt:>9.2f}ms{net:>9.2f}ms"
          f"{IO_OVERHEAD_MS:>9.1f}ms{per_ss:>11.2f}ms{per_ss * N_SS:>11.1f}ms")

print(f"\n실행당 차이: {rows[0][1] - rows[1][1]:,.1f}ms")
print(f"메모리 피크:  전부 {ALL_B * MEM_PEAK_FACTOR / 1e6:.2f}MB  "
      f"vs 축소 {LEAN_B * MEM_PEAK_FACTOR / 1e6:.3f}MB (슈퍼스텝마다 생성/소멸)")
print(f"\n같은 결정의 두 얼굴 →  월 {WON_ALL - WON_LEAN:,.0f}원 절감  /  "
      f"실행당 {rows[0][1] - rows[1][1]:,.1f}ms 절감")

# 출력:
# 구분                  상태       직렬화      네트워크    I/O 고정       슈퍼스텝당       실행 총계
# ------------------------------------------------------------------------------
# 전부 담기           135.7K     0.58ms     3.26ms     40.0ms      43.84ms      350.7ms
# 필요한 것만            2.3K     0.01ms     0.06ms     40.0ms      40.07ms      320.6ms
#
# 실행당 차이: 30.2ms
# 메모리 피크:  전부 0.27MB  vs 축소 0.005MB (슈퍼스텝마다 생성/소멸)
#
# 같은 결정의 두 얼굴 →  월 1,565원 절감  /  실행당 30.2ms 절감
#
# → I/O 고정비 40ms가 커서 «비율»은 8% 남짓으로 줄지만, 절감분은 사용자가 체감하는 30ms다.
#    슈퍼스텝을 14회로 올리면 53ms, 동시 사용자가 붙어 DB 쓰기가 밀리면 더 커진다.
#    네트워크가 지금 가정(같은 리전 12ms/MB)보다 느리면 여기가 지배 항이 된다.

# %% [markdown]
# ## 정리
#
# - 저자의 **월 1,600원**은 `135,748B × 14 슈퍼스텝 × 1,200 실행/일 × 30일 ÷ 1GB × 25원`이다.
#   가장 비싼 가정(한 달 전량 보관)으로 계산해도 이 금액이다. **의사결정을 바꿀 수 없는 크기**다.
# - 진짜 비용은 $T = n_{\text{superstep}} \times (t_{ser} + t_{deser})$ 다.
#   슈퍼스텝마다 왕복하므로 상태 크기가 곧 **슈퍼스텝 수만큼 곱해진 지연**이 된다.
# - 여기에 네트워크 왕복, DB 쓰기 경합, 메모리 피크, GC 압박이 따라붙는다. 전부 원 단위 장부에 안 잡힌다.
# - 그러므로 비용의 단위를 **"원"이 아니라 "밀리초 × 슈퍼스텝 수 × 동시 사용자"**로 잡아야 한다.
#   저자의 "상태 하나가 8KB를 넘으면 무엇을 뺄지 찾는다"는 기준선은 돈이 아니라 이 축에서 나온 숫자다.
