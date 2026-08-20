# %% [markdown]
# # 이 책의 숫자를 「자릿수와 방향」으로만 쓰는 이유
#
# 35장의 결론은 한 줄이다.
#
# > 이 책의 숫자는 자릿수와 방향으로만 쓰세요. 여러분 환경에서 다시 재는 데 하루면 됩니다.
#
# 이 스크립트는 그 문장을 **수치로** 확인한다. 확인할 것은 세 가지다.
#
# 1. 환경(하드웨어·모델 속도·단가)을 배수로 흔들면 **절대 초·절대 비용은 크게 달라진다**.
# 2. 같은 흔들기에서 **구간 비중의 순위(방향)와 자릿수는 대체로 살아남는다**.
# 3. 그런데 **살아남지 못하는 지표도 있다** — 27장 그래프 전환점 1,000개는 300~3,000으로 이동한다.
#
# 왜 이런 차이가 나는가. 절대값은 공통 배수에 **비례**하고, 비중은 공통 배수가 **약분**되기 때문이다.
#
# 어떤 구간 $i$의 시간을 $t_i$, 환경 배수를 $c$라 하면
#
# $$T(c) = c\sum_i t_i \quad\text{(절대값: } c \text{에 비례)}$$
#
# $$\text{share}_i(c) = \frac{c\,t_i}{c\sum_j t_j} = \frac{t_i}{\sum_j t_j} \quad\text{(비중: } c \text{와 무관)}$$
#
# 즉 **비율·배수·순위는 무차원량**이라서 환경을 옮겨도 살아남는다. 반면
#
# $$N^{*} = \frac{S}{u_{\text{doc}} - u_{\text{graph}}}$$
#
# 처럼 **차(差)가 분모에 들어가는 지표**는 분자·분모가 서로 다른 요인으로 흔들리면 약분이 안 되고,
# 작은 입력 변화가 자릿수를 밀어낸다. 이게 「주의 칸」에 적힌 것들이다.
#
# 필요 패키지: plotly, kaleido (없으면 표 출력까지는 그대로 동작)

# %%
# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
from __future__ import annotations

import os


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
print("작업 폴더:", os.path.basename(HERE))
# 출력: 작업 폴더: 7e79b485-d8bc-4f59-bfc5-91cdb8ed4402

# %% [markdown]
# ## 1. 저자 환경의 기준값 — 33장 지배 구간
#
# 책의 값은 「모델 호출이 응답 시간의 94.8%」다. 이걸 구간별 밀리초로 풀어 둔다.
# 이 숫자 자체는 **저자 환경의 것**이고, 우리가 볼 것은 이 숫자가 아니라 **비중과 순위**다.

# %%
BASE_MS = {
    "모델 호출": 4200.0,
    "그래프 조회": 120.0,
    "직렬화·파싱": 45.0,
    "네트워크·기타": 65.0,
}


def shares(stage_ms: dict[str, float]) -> dict[str, float]:
    total = sum(stage_ms.values())
    return {k: v / total for k, v in stage_ms.items()}


base_total = sum(BASE_MS.values())
base_share = shares(BASE_MS)
print(f"총 응답 시간 {base_total:,.0f} ms")
for k, v in sorted(base_share.items(), key=lambda x: -x[1]):
    print(f"  {k:<12} {BASE_MS[k]:>7,.0f} ms   {v:6.1%}")
# 출력: 총 응답 시간 4,430 ms
# 출력:   모델 호출          4,200 ms    94.8%
# 출력:   그래프 조회           120 ms     2.7%
# 출력:   네트워크·기타           65 ms     1.5%
# 출력:   직렬화·파싱            45 ms     1.0%

# %% [markdown]
# ## 2. 환경을 배수로 흔든다
#
# 구간마다 서로 다른 배수를 곱해 여섯 개 환경을 만든다.
# 마지막 하나는 ex1의 **반증 조건**이다 — 「같은 작업의 모델 지연이 10분의 1이 되면 60% 아래로 내려간다」.

# %%
# (이름, {구간: 배수}, 단가 배수)
SCENARIOS = [
    ("저자 환경 (기준)", {}, 1.0),
    ("느린 그래프 DB (조회 5배)", {"그래프 조회": 5.0}, 1.0),
    ("저사양 온프렘 (전 구간 2.5배)", {k: 2.5 for k in BASE_MS}, 0.4),
    ("대형 모델 (호출 2배)", {"모델 호출": 2.0}, 3.0),
    ("빠른 모델 + 먼 리전", {"모델 호출": 0.5, "네트워크·기타": 3.0}, 1.0),
    ("모델 10배 빨라짐 (반증 조건)", {"모델 호출": 0.1}, 0.3),
]

UNIT_COST_PER_SEC = 0.0012  # 저자 환경의 초당 단가(가상 단위)

rows = []
for name, mult, price in SCENARIOS:
    stage = {k: v * mult.get(k, 1.0) for k, v in BASE_MS.items()}
    total = sum(stage.values())
    sh = shares(stage)
    top = max(sh, key=lambda k: sh[k])
    rows.append(
        dict(
            name=name,
            total_ms=total,
            model_share=sh["모델 호출"],
            top=top,
            rank=[k for k, _ in sorted(sh.items(), key=lambda x: -x[1])],
            cost=total / 1000 * UNIT_COST_PER_SEC * price,
        )
    )

print(f"{'환경':<30}{'총 ms':>9}{'절대 배수':>10}{'모델 비중':>10}{'비용 배수':>10}  1위 구간")
print("-" * 92)
for r in rows:
    print(
        f"{r['name']:<30}{r['total_ms']:>9,.0f}{r['total_ms'] / base_total:>9.2f}x"
        f"{r['model_share']:>10.1%}{r['cost'] / rows[0]['cost']:>9.2f}x  {r['top']}"
    )
# 출력: 환경                                 총 ms     절대 배수     모델 비중     비용 배수  1위 구간
# 출력: --------------------------------------------------------------------------------------------
# 출력: 저자 환경 (기준)                        4,430     1.00x     94.8%     1.00x  모델 호출
# 출력: 느린 그래프 DB (조회 5배)                 4,910     1.11x     85.5%     1.11x  모델 호출
# 출력: 저사양 온프렘 (전 구간 2.5배)              11,075     2.50x     94.8%     1.00x  모델 호출
# 출력: 대형 모델 (호출 2배)                     8,630     1.95x     97.3%     5.84x  모델 호출
# 출력: 빠른 모델 + 먼 리전                      2,460     0.56x     85.4%     0.56x  모델 호출
# 출력: 모델 10배 빨라짐 (반증 조건)                  650     0.15x     64.6%     0.04x  모델 호출

# %%
abs_mult = [r["total_ms"] / base_total for r in rows]
cost_mult = [r["cost"] / rows[0]["cost"] for r in rows]
sh_all = [r["model_share"] for r in rows]

print(f"절대 총시간 배수 범위 : {min(abs_mult):.2f}x ~ {max(abs_mult):.2f}x  (약 {max(abs_mult) / min(abs_mult):.0f}배 폭)")
print(f"절대 비용 배수 범위   : {min(cost_mult):.2f}x ~ {max(cost_mult):.2f}x  (약 {max(cost_mult) / min(cost_mult):.0f}배 폭)")
print(f"모델 비중 범위        : {min(sh_all):.1%} ~ {max(sh_all):.1%}")
print(f"1위 구간이 «모델 호출»인 환경: {sum(1 for r in rows if r['top'] == '모델 호출')}/{len(rows)}")
print(f"순위(방향)가 기준과 같은 환경 : {sum(1 for r in rows if r['rank'] == rows[0]['rank'])}/{len(rows)}")

no_falsifier = [r for r in rows if "반증" not in r["name"]]
print(f"\n반증 조건을 뺀 다섯 환경의 모델 비중: "
      f"{min(r['model_share'] for r in no_falsifier):.1%} ~ {max(r['model_share'] for r in no_falsifier):.1%}"
      f"  → 전부 «90% 안팎, 압도적 1위»라는 방향은 유지")
# 출력: 절대 총시간 배수 범위 : 0.15x ~ 2.50x  (약 17배 폭)
# 출력: 절대 비용 배수 범위   : 0.04x ~ 5.84x  (약 133배 폭)
# 출력: 모델 비중 범위        : 64.6% ~ 97.3%
# 출력: 1위 구간이 «모델 호출»인 환경: 6/6
# 출력: 순위(방향)가 기준과 같은 환경 : 5/6
# 출력:
# 출력: 반증 조건을 뺀 다섯 환경의 모델 비중: 85.4% ~ 97.3%  → 전부 «90% 안팎, 압도적 1위»라는 방향은 유지
#
# 읽는 법:
#   절대값(총 ms·비용)은 17배·133배로 흔들린다  → 책의 4,430ms·비용을 그대로 쓰면 안 된다
#   모델 비중과 1위 구간은 6/6에서 유지된다      → «모델 호출이 지배한다»는 방향은 그대로 쓸 수 있다
#   단 «모델 10배» 환경에서 90%는 깨진다        → 그래서 ex1은 이 주장의 확신을 35%로 적었다

# %% [markdown]
# ## 3. 환경이 달라도 비슷한 것 — 21장 체크포인터 배수
#
# 21장의 책의 값은 「메모리 대비 디스크 체크포인터 지연 **2.0~4.8배**」다.
# 주의 칸은 「상태 크기별로 재라」다. 상태 크기와 하드웨어를 함께 흔들어 보면,
# **절대 ms는 세 자릿수로 흔들리는데 배수는 좁은 구간에 머문다**.
#
# 디스크 지연에는 상태 크기에 비례하는 항 외에 크기와 무관한 **고정 오버헤드(fsync, 메타데이터)** 가 있다.
# 그래서 배수는 완전히 상수는 아니고, 작은 상태에서 커진다.
#
# $$\text{ratio}(n) = \frac{a_d n + f}{a_m n} = \frac{a_d}{a_m} + \frac{f}{a_m n}$$

# %%
A_MEM = 0.020   # ms per KB
A_DISK = 0.042  # ms per KB
FSYNC = 1.8     # ms 고정 오버헤드

print(f"{'상태 크기':>10}{'하드웨어':>16}{'메모리 ms':>12}{'디스크 ms':>12}{'배수':>8}")
print("-" * 60)
ratios = []
abs_disk = []
for hw_name, hw in [("빠른 NVMe", 0.6), ("기준", 1.0), ("느린 EBS", 4.0)]:
    for kb in (64, 1024, 16384):
        mem = A_MEM * kb
        disk = (A_DISK * kb + FSYNC) * hw
        ratios.append(disk / mem)
        abs_disk.append(disk)
        print(f"{kb:>8} KB{hw_name:>14}{mem:>12,.1f}{disk:>12,.1f}{disk / mem:>7.2f}x")

print(f"\n절대 디스크 지연 : {min(abs_disk):,.1f} ~ {max(abs_disk):,.1f} ms  "
      f"({max(abs_disk) / min(abs_disk):.0f}배 폭)")
print(f"배수(디스크/메모리): {min(ratios):.1f} ~ {max(ratios):.1f}x  "
      f"→ 책의 «2.0~4.8배»와 자릿수·방향이 같다")
# 출력:      상태 크기            하드웨어      메모리 ms      디스크 ms      배수
# 출력: ------------------------------------------------------------
# 출력:       64 KB       빠른 NVMe         1.3         2.7   2.10x
# 출력:     1024 KB       빠른 NVMe        20.5        26.9   1.31x
# 출력:    16384 KB       빠른 NVMe       327.7       414.0   1.26x
# 출력:       64 KB            기준         1.3         4.5   3.51x
# 출력:     1024 KB            기준        20.5        44.8   2.19x
# 출력:    16384 KB            기준       327.7       689.9   2.11x
# 출력:       64 KB        느린 EBS         1.3        18.0  14.03x
# 출력:     1024 KB        느린 EBS        20.5       179.2   8.75x
# 출력:    16384 KB        느린 EBS       327.7     2,759.7   8.42x
# 출력:
# 출력: 절대 디스크 지연 : 2.7 ~ 2,759.7 ms  (1025배 폭)
# 출력: 배수(디스크/메모리): 1.3 ~ 14.0x  → 책의 «2.0~4.8배»와 자릿수·방향이 같다
#
# 주의: «느린 EBS»까지 넣으면 배수도 14배까지 간다. 자릿수가 완전히 안전한 건 아니고
#       «디스크가 메모리보다 한 자릿수 안쪽으로 느리다»는 방향이 살아남는 것이다.

# %% [markdown]
# ## 4. 살아남지 못하는 것 — 27장 그래프 전환점
#
# 책의 값은 「사실 **1,000개**부터 그래프가 싸다」이고, 주의 칸은 「인건비·단가에 달렸다」다.
# 그리고 35장 본문은 이걸 명시적으로 예외로 지목한다.
#
# > 그래프 전환점이 1,000개 → 여러분은 300일 수도 3,000일 수도
#
# 왜 이것만 흔들리는가. 전환점은 **차가 분모에 들어가는 값**이다.
#
# $$N^{*} = \frac{S \cdot w \cdot s}{u_{\text{doc}} w - u_{\text{graph}} p}$$
#
# - $w$: 인건비 배수 (분자와 분모에 함께 들어감)
# - $s$: 스키마 설정 난이도 배수 (분자에만)
# - $p$: 인프라 단가 배수 (분모에만, **뺄셈 쪽**)
#
# 2절의 비중과 달리 여기서는 **공통 배수가 약분되지 않는다**. $w$가 분자·분모에 다 들어가지만
# 분모의 $-u_{\text{graph}} p$ 항이 $w$와 무관하게 남기 때문에, $w$를 3배로 올리면
# 전환점이 오히려 **내려간다**. 그리고 분모가 0에 가까워지면 $N^{*}$가 폭발하고,
# 음수가 되면 **그래프가 아무리 커도 안 싸지는 구간**이 생긴다.

# %%
S0, U_DOC, U_GRAPH = 1000.0, 1.2, 0.2  # 저자 환경에서 N* = 1,000이 되도록 잡은 값


def breakeven(w=1.0, s=1.0, p=1.0):
    denom = U_DOC * w - U_GRAPH * p
    if denom <= 0:
        return float("inf")  # 그래프가 절대 싸지지 않는다
    return S0 * w * s / denom


CASES = [
    ("저자 환경 (기준)", dict()),
    ("인건비 3배 (w=3)", dict(w=3.0)),
    ("인건비 1/3 (w=0.33)", dict(w=0.33)),
    ("스키마 단순 + 단가 싸다 (s=0.4, p=0.5)", dict(s=0.4, p=0.5)),
    ("스키마 복잡 + 단가 비싸다 (s=2.5, p=2)", dict(s=2.5, p=2.0)),
    ("싼 인건비 + 비싼 그래프 (w=0.2, p=1.1)", dict(w=0.2, p=1.1)),
    ("더 비싼 그래프 (w=0.2, p=1.3)", dict(w=0.2, p=1.3)),
]

print(f"{'조건':<42}{'전환점 N*':>14}{'기준 대비':>10}")
print("-" * 68)
finite = []
for label, kw in CASES:
    n = breakeven(**kw)
    if n == float("inf"):
        print(f"{label:<42}{'∞ (안 싸짐)':>14}{'—':>10}")
    else:
        finite.append(n)
        print(f"{label:<42}{n:>14,.0f}{n / 1000:>9.2f}x")

print(f"\n유한한 값의 범위: {min(finite):,.0f} ~ {max(finite):,.0f}개 "
      f"({max(finite) / min(finite):.1f}배 폭)")
print("→ 백 단위에서 만 단위까지 넘나든다. 자릿수 자체가 흔들리는 지표다.")
print("→ 게다가 어떤 조건에서는 전환점이 «없다». 이건 «방향»조차 뒤집히는 경우다.")
# 출력: 조건                                            전환점 N*     기준 대비
# 출력: --------------------------------------------------------------------
# 출력: 저자 환경 (기준)                                     1,000     1.00x
# 출력: 인건비 3배 (w=3)                                       882     0.88x
# 출력: 인건비 1/3 (w=0.33)                                  1,684     1.68x
# 출력: 스키마 단순 + 단가 싸다 (s=0.4, p=0.5)                     364     0.36x
# 출력: 스키마 복잡 + 단가 비싸다 (s=2.5, p=2)                    3,125     3.13x
# 출력: 싼 인건비 + 비싼 그래프 (w=0.2, p=1.1)                   10,000    10.00x
# 출력: 더 비싼 그래프 (w=0.2, p=1.3)                       ∞ (안 싸짐)         —
# 출력:
# 출력: 유한한 값의 범위: 364 ~ 10,000개 (27.5배 폭)
# 출력: → 백 단위에서 만 단위까지 넘나든다. 자릿수 자체가 흔들리는 지표다.
# 출력: → 게다가 어떤 조건에서는 전환점이 «없다». 이건 «방향»조차 뒤집히는 경우다.

# %%
# 위 표의 값을 딕셔너리로 다시 확인한다 (정렬 없이 raw 숫자).
for label, kw in CASES:
    n = breakeven(**kw)
    print(label, "->", "inf" if n == float("inf") else f"{n:,.1f}")
# 출력: 저자 환경 (기준) -> 1,000.0
# 출력: 인건비 3배 (w=3) -> 882.4
# 출력: 인건비 1/3 (w=0.33) -> 1,683.7
# 출력: 스키마 단순 + 단가 싸다 (s=0.4, p=0.5) -> 363.6
# 출력: 스키마 복잡 + 단가 비싸다 (s=2.5, p=2) -> 3,125.0
# 출력: 싼 인건비 + 비싼 그래프 (w=0.2, p=1.1) -> 10,000.0
# 출력: 더 비싼 그래프 (w=0.2, p=1.3) -> inf
#
# 눈여겨볼 것 셋:
#  1. 인건비를 3배로 올리면 전환점이 «내려간다»(1,000 → 882). 직관과 방향이 반대다.
#     분자도 3배가 되지만 분모의 -0.2p 항이 상대적으로 작아져 비율이 뒤집힌다.
#  2. 인건비를 1/3로 낮추면 전환점이 «올라간다»(1,000 → 1,684).
#     «인건비가 싸면 그래프 도입 문턱이 낮아진다»는 직관이 통하지 않는다.
#  3. w=0.2, p=1.1 에서는 분모 1.2*0.2 - 0.2*1.1 = 0.02 로 0에 붙으면서
#     N*이 10,000까지 폭발하고, p=1.3 이면 분모가 음수가 되어 «절대 안 싸진다».
# 이것이 자릿수 예측이 실패하는 지표의 모양이다. 27장의 주의 칸이 그래서 붙어 있다.

# %% [markdown]
# ## 5. 그림으로 — 흔들리는 것과 안 흔들리는 것

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    names = [r["name"] for r in rows]
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "절대값은 안 살아남는다 (총 응답시간 배수)",
            "방향은 살아남는다 (모델 호출 비중)",
            "배수는 대체로 살아남는다 (체크포인터)",
            "예외: 자릿수가 흔들린다 (그래프 전환점)",
        ),
        vertical_spacing=0.18,
        horizontal_spacing=0.12,
    )

    # (1,1) 절대 총시간 배수 + 비용 배수
    fig.add_trace(go.Bar(x=names, y=abs_mult, name="총 응답시간 배수",
                         marker_color="#6b7280"), row=1, col=1)
    fig.add_trace(go.Bar(x=names, y=cost_mult, name="비용 배수",
                         marker_color="#c084fc"), row=1, col=1)

    # (1,2) 모델 비중
    colors = ["#2563eb"] * len(rows)
    colors[-1] = "#dc2626"  # 반증 조건
    fig.add_trace(go.Bar(x=names, y=[s * 100 for s in sh_all], name="모델 비중 %",
                         marker_color=colors, showlegend=False), row=1, col=2)
    fig.add_hline(y=90, line_dash="dash", line_color="#dc2626", row=1, col=2,
                  annotation_text="책의 주장 90%", annotation_position="bottom right")

    # (2,1) 체크포인터: 절대 지연(로그) vs 배수
    kbs = [64, 256, 1024, 4096, 16384]
    for hw_name, hw, dash in [("빠른 NVMe", 0.6, "dot"), ("기준", 1.0, "solid"), ("느린 EBS", 4.0, "dash")]:
        fig.add_trace(
            go.Scatter(
                x=kbs,
                y=[(A_DISK * k + FSYNC) * hw / (A_MEM * k) for k in kbs],
                mode="lines+markers",
                name=f"배수 · {hw_name}",
                line=dict(dash=dash),
            ),
            row=2, col=1,
        )
    fig.add_hrect(y0=2.0, y1=4.8, fillcolor="#22c55e", opacity=0.12,
                  line_width=0, row=2, col=1,
                  annotation_text="책의 값 2.0~4.8배", annotation_position="top left")

    # (2,2) 전환점
    be_labels = ["기준", "w=3", "w=0.33", "s=0.4\np=0.5", "s=2.5\np=2", "w=0.2\np=1.1"]
    be_vals = [breakeven(), breakeven(w=3.0), breakeven(w=0.33),
               breakeven(s=0.4, p=0.5), breakeven(s=2.5, p=2.0),
               breakeven(w=0.2, p=1.1)]
    fig.add_trace(go.Bar(x=be_labels, y=be_vals, marker_color="#f59e0b",
                         showlegend=False), row=2, col=2)
    fig.add_hline(y=1000, line_dash="dash", line_color="#111827", row=2, col=2,
                  annotation_text="책의 값 1,000개", annotation_position="top right")

    fig.update_yaxes(title_text="기준 대비 배수", row=1, col=1)
    fig.update_yaxes(title_text="비중 (%)", range=[0, 100], row=1, col=2)
    fig.update_yaxes(title_text="디스크/메모리 배수", row=2, col=1)
    fig.update_xaxes(title_text="상태 크기 (KB, 로그)", type="log", row=2, col=1)
    fig.update_yaxes(title_text="전환점 N* (사실 개수)", type="log", row=2, col=2)
    fig.update_xaxes(tickangle=-25, row=1, col=1)
    fig.update_xaxes(tickangle=-25, row=1, col=2)
    fig.update_layout(
        title_text="이 책의 숫자: 자릿수와 방향만 가져가라 (35장)",
        height=820, width=1180, barmode="group",
        legend=dict(orientation="h", y=-0.08),
        template="plotly_white",
    )

    _show(fig)
    fig.write_image(os.path.join(HERE, "expy.png"), scale=2)
    print("expy.png 저장 완료")
except Exception as e:  # noqa: BLE001
    print("시각화 건너뜀:", type(e).__name__, e)
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 6. 그래서 무엇을 재야 하는가 — ex4_selfcheck.py의 11개
#
# 「하루면 된다」는 이 목록이 **11개뿐**이기 때문이다. 200개가 아니다.
# 각 항목의 「책의 값」은 참고선이고, 「주의」 칸이 **자릿수를 신뢰할 수 있는지**를 알려준다.

# %%
MEASURE = [
    ("21장", "체크포인터 배수", "2.0~4.8배", "상태 크기별로 재라", "배수"),
    ("22장", "재시도 봉우리", "흔들기로 200→83", "실패율부터 재라", "방향"),
    ("23장", "승인 문턱", "70% 이하", "용량은 조직마다 다르다", "환경 의존"),
    ("24장", "사실 보존율", "요약 72% / 오프로딩 100%", "사후 계측으로 재라", "방향"),
    ("25장", "팬아웃 이득 천장", "1.57배", "합류 값에 달렸다", "환경 의존"),
    ("27장", "그래프 전환점", "1,000개", "인건비·단가에 달렸다", "자릿수 흔들림"),
    ("28장", "드리프트", "제약 20%→9%", "종류 분류부터 하라", "방향"),
    ("31장", "잠금 갈림길", "15~30%", "판단 시간에 달렸다", "환경 의존"),
    ("32장", "가장 긴 주기", "730일", "크론을 파싱해서 계산하라", "직접 계산"),
    ("33장", "지배 구간", "94.8%", "이게 제일 먼저 잴 것", "방향"),
    ("34장", "구조적 k", "1", "속성 k 와 따로 재라", "직접 계산"),
]

print(f"{'장':<5}{'지표':<16}{'책의 값':<26}{'가져갈 수 있는 것'}")
print("-" * 76)
for ch, name, val, _note, kind in MEASURE:
    print(f"{ch:<5}{name:<16}{val:<26}{kind}")

from collections import Counter  # noqa: E402

c = Counter(k for *_, k in MEASURE)
print(f"\n총 {len(MEASURE)}개 — 전부 재는 데 대략 하루")
print("가져갈 수 있는 것의 종류:", dict(c))
print(f"«자릿수 흔들림»으로 표시된 것: {c['자릿수 흔들림']}개 (27장 전환점)")
print("\n하나만 고르라면 33장 지배 구간. 재는 데 30분, 안 재면 3주를 쓴다.")
# 출력: 장    지표              책의 값                      가져갈 수 있는 것
# 출력: ----------------------------------------------------------------------------
# 출력: 21장  체크포인터 배수        2.0~4.8배                  배수
# 출력: 22장  재시도 봉우리         흔들기로 200→83               방향
# 출력: 23장  승인 문턱           70% 이하                    환경 의존
# 출력: 24장  사실 보존율          요약 72% / 오프로딩 100%        방향
# 출력: 25장  팬아웃 이득 천장       1.57배                     환경 의존
# 출력: 27장  그래프 전환점         1,000개                    자릿수 흔들림
# 출력: 28장  드리프트            제약 20%→9%                 방향
# 출력: 31장  잠금 갈림길          15~30%                    환경 의존
# 출력: 32장  가장 긴 주기         730일                      직접 계산
# 출력: 33장  지배 구간           94.8%                     방향
# 출력: 34장  구조적 k           1                         직접 계산
# 출력:
# 출력: 총 11개 — 전부 재는 데 대략 하루
# 출력: 가져갈 수 있는 것의 종류: {'배수': 1, '방향': 4, '환경 의존': 3, '자릿수 흔들림': 1, '직접 계산': 2}
# 출력: «자릿수 흔들림»으로 표시된 것: 1개 (27장 전환점)
# 출력:
# 출력: 하나만 고르라면 33장 지배 구간. 재는 데 30분, 안 재면 3주를 쓴다.

# %% [markdown]
# ## 정리
#
# | 지표의 모양 | 환경을 옮기면 | 책에서 쓰는 법 |
# |---|---|---|
# | 비중 $t_i / \sum t_j$ | 공통 배수가 약분됨 | 자릿수·방향 그대로 가져간다 |
# | 배수 $a/b$ | 대체로 유지, 고정 오버헤드만큼 흔들림 | 「몇 배쯤」까지만 가져간다 |
# | 차가 분모인 값 $S/(u_1-u_2)$ | 자릿수가 튀고, 부호가 뒤집히기도 함 | 반드시 다시 잰다 |
#
# 그래서 35장의 문장은 두 부분이다.
#
# - **자릿수와 방향으로만 쓴다** — 절대값은 저자 환경의 것이라 이식되지 않는다.
# - **하루면 다시 잴 수 있다** — 재야 할 것이 11개로 정리돼 있으니 못 잴 이유가 없다.
#
# 그리고 재 보고 다르게 나오면, 그쪽이 맞다.
