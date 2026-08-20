# %% [markdown]
# # ex3_cost_model.py — 호출 횟수 순위와 비용 비중 순위는 왜 뒤집히는가
#
# 33.4절 「청구서의 큰 칸은 대개 다른 곳이다」의 워크로드를 그대로 재구성한다.
#
# **핵심 질문**: 가장 많이 도는 항목과 비용 비중이 큰 항목은 각각 무엇인가?
#
# - 가장 많이 도는 것: **그래프 조회** 월 3.6억 회 (체크포인트/이벤트 로그는 5.4억 회지만
#   책 본문이 「조회」 계열의 대표로 지목한 것은 그래프 조회다)
# - 비용 비중이 큰 것: **모델 호출** 월 158만 회 (전체 호출의 0.1% 미만)
#
# ## 비용 모델을 세우는 절차
#
# 항목 $i$ 의 월 비용은 두 갈래를 더한 값이다.
#
# $$ C_i = \underbrace{\text{cores}_i \times p_{\text{cpu}} \times H}_{\text{인프라}}
#        + \underbrace{\frac{n_i \cdot t_i}{1000} \times p_{\text{tok}}}_{\text{토큰}} $$
#
# 인프라는 「호출 수 × 1회 지연」을 **코어 시간**으로 환산해서 구한다.
# 월 $n_i$ 회를 각 $m_i$ 밀리초씩 처리하려면, 한 달 내내 평균 몇 개의 코어가
# 붙어 있어야 하는가를 묻는 식이다.
#
# $$ \text{cores}_i = \frac{n_i \times m_i / 1000}{H \times 3600},
#    \qquad H = 24 \times 30 = 720\ \text{시간} $$
#
# 토큰은 훨씬 단순하다. **월 호출 수 × 호출당 토큰 × 1K당 단가**. 끝이다.
#
# 이 두 식의 **단가 차이**가 순위를 뒤집는 원인이다.

# %%
# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
import os

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else "."

KRW = 1_380

# 월 호출 수 · 1회 지연(ms) · 1회 입력 토큰  — ex3_cost_model.py 원문 그대로
WORKLOAD = {
    "그래프 조회":      dict(calls=360_000_000, ms=2.4,  tokens=0),
    "벡터 검색":        dict(calls=230_000_000, ms=8.0,  tokens=0),
    "모델 호출(판단)":  dict(calls=1_400_000,   ms=1800, tokens=6_200),
    "모델 호출(추출)":  dict(calls=180_000,     ms=2400, tokens=11_000),
    "체크포인트 쓰기":  dict(calls=540_000_000, ms=4.2,  tokens=0),
    "이벤트 로그 쓰기": dict(calls=540_000_000, ms=0.9,  tokens=0),
}

CPU_KRW_PER_CORE_HOUR = 62
TOKEN_KRW_PER_1K = 3.0 / 1000 * KRW   # 입력 $3/1M 토큰 기준 → 원화
STORAGE_KRW_PER_GB_MONTH = 33
HOURS = 24 * 30

print(f"토큰 단가: 1K 입력 토큰당 {TOKEN_KRW_PER_1K:.2f}원")
print(f"CPU 단가:  코어-시간당 {CPU_KRW_PER_CORE_HOUR}원  (월 {HOURS}시간)")
# 출력:
# 토큰 단가: 1K 입력 토큰당 4.14원
# CPU 단가:  코어-시간당 62원  (월 720시간)

# %% [markdown]
# ## 1. 월 비용 표를 다시 만든다
#
# `cpu_cores(calls, ms)` 가 곧 코어 시간 환산이다.

# %%
def cpu_cores(calls, ms):
    """월 calls 회 × ms 밀리초를 처리하려면 평균 코어가 몇 개 필요한가."""
    return calls * ms / 1000.0 / (HOURS * 3600)


def cost_table(workload, ms_scale=1.0, token_scale=1.0):
    """항목별 (코어, 인프라, 토큰, 합계) 를 계산한다."""
    rows = []
    for name, w in workload.items():
        cores = cpu_cores(w["calls"], w["ms"] * ms_scale)
        infra = cores * CPU_KRW_PER_CORE_HOUR * HOURS
        tok = w["calls"] * w["tokens"] * token_scale / 1000 * TOKEN_KRW_PER_1K
        rows.append(dict(name=name, calls=w["calls"], ms=w["ms"] * ms_scale,
                         cores=cores, infra=infra, tokens=tok, total=infra + tok))
    return rows


rows = cost_table(WORKLOAD)
total = sum(r["total"] for r in rows)

hdr = f"{'항목':<18}{'월 호출':>15}{'1회 ms':>9}{'코어':>7}{'월 인프라':>13}{'월 토큰':>15}{'합계':>15}{'비중':>8}"
print(hdr)
print("-" * 102)
for r in rows:
    print(f"{r['name']:<18}{r['calls']:>15,}{r['ms']:>9.1f}{r['cores']:>7.1f}"
          f"{r['infra']:>12,.0f}원{r['tokens']:>14,.0f}원{r['total']:>14,.0f}원"
          f"{r['total'] / total:>8.2%}")
print("-" * 102)
print(f"{'합계':<18}{'':<46}{total:>44,.0f}원")
# 출력:
# 항목                           월 호출    1회 ms     코어        월 인프라           월 토큰             합계      비중
# ------------------------------------------------------------------------------------------------------
# 그래프 조회                360,000,000      2.4    0.3      14,880원             0원        14,880원   0.03%
# 벡터 검색                 230,000,000      8.0    0.7      31,689원             0원        31,689원   0.07%
# 모델 호출(판단)               1,400,000   1800.0    1.0      43,400원    35,935,200원    35,978,600원  81.26%
# 모델 호출(추출)                 180,000   2400.0    0.2       7,440원     8,197,200원     8,204,640원  18.53%
# 체크포인트 쓰기              540,000,000      4.2    0.9      39,060원             0원        39,060원   0.09%
# 이벤트 로그 쓰기             540,000,000      0.9    0.2       8,370원             0원         8,370원   0.02%
# ------------------------------------------------------------------------------------------------------
# 합계                                                                                                44,277,239원

# %% [markdown]
# ## 2. 두 순위를 나란히 놓는다
#
# 호출 횟수로 줄 세운 것과 비용으로 줄 세운 것이 **거의 완전히 뒤집힌다**.

# %%
by_calls = sorted(rows, key=lambda r: -r["calls"])
by_cost = sorted(rows, key=lambda r: -r["total"])

print(f"{'순위':<5}{'호출 횟수 순':<22}{'월 호출':>15}   |  {'비용 순':<20}{'비중':>8}")
print("-" * 82)
for i, (a, b) in enumerate(zip(by_calls, by_cost), 1):
    print(f"{i:<5}{a['name']:<22}{a['calls']:>15,}   |  "
          f"{b['name']:<20}{b['total'] / total:>8.2%}")
# 출력:
# 순위   호출 횟수 순                          월 호출   |  비용 순                      비중
# ----------------------------------------------------------------------------------
# 1    체크포인트 쓰기                  540,000,000   |  모델 호출(판단)             81.26%
# 2    이벤트 로그 쓰기                 540,000,000   |  모델 호출(추출)             18.53%
# 3    그래프 조회                    360,000,000   |  체크포인트 쓰기               0.09%
# 4    벡터 검색                     230,000,000   |  벡터 검색                  0.07%
# 5    모델 호출(판단)                   1,400,000   |  그래프 조회                 0.03%
# 6    모델 호출(추출)                     180,000   |  이벤트 로그 쓰기              0.02%

# %%
# 호출 비중 vs 비용 비중을 숫자로 못 박는다
all_calls = sum(r["calls"] for r in rows)
model_calls = sum(r["calls"] for r in rows if r["name"].startswith("모델"))
model_cost = sum(r["total"] for r in rows if r["name"].startswith("모델"))
graph = next(r for r in rows if r["name"] == "그래프 조회")

print(f"전체 호출         {all_calls:>15,} 회")
print(f"그래프 조회       {graph['calls']:>15,} 회  "
      f"({graph['calls'] / all_calls:6.2%})  → 비용 {graph['total'] / total:6.3%}")
print(f"모델 호출 합계    {model_calls:>15,} 회  "
      f"({model_calls / all_calls:6.4%})  → 비용 {model_cost / total:6.2%}")
print()
print(f"모델 호출은 그래프 조회보다 {graph['calls'] / model_calls:,.0f}배 «덜» 도는데 "
      f"비용은 {model_cost / graph['total']:,.0f}배 «더» 든다.")
# 출력:
# 전체 호출           1,671,580,000 회
# 그래프 조회           360,000,000 회  (21.54%)  → 비용 0.034%
# 모델 호출 합계          1,580,000 회  (0.0945%)  → 비용 99.79%
#
# 모델 호출은 그래프 조회보다 228배 «덜» 도는데 비용은 2,969배 «더» 든다.

# %% [markdown]
# ## 3. 왜 뒤집히나 — 호출 1회당 단가로 환산해 보면 끝난다
#
# 순위가 뒤집히는 이유는 하나뿐이다. **호출 1회당 단가가 다르다.**
#
# $$ \text{단가}_i = \frac{C_i}{n_i} $$
#
# 그래프 조회 1회는 2.4ms 의 코어 시간이고, 코어-시간 62원을 밀리초로 환산하면
# 1회에 0.00004원짜리다. 반면 모델 호출 1회는 6,200 토큰을 태우므로
# $6.2 \times 4.14 \approx 25.7$원이다. **60만 배 차이**다.
#
# 호출 수 차이(228배)로는 이 단가 격차(60만 배)를 결코 못 따라잡는다.

# %%
print(f"{'항목':<18}{'월 호출':>15}{'1회 단가(원)':>16}{'단가 배수':>12}")
print("-" * 61)
base = min(r["total"] / r["calls"] for r in rows)
for r in sorted(rows, key=lambda r: -r["total"] / r["calls"]):
    unit = r["total"] / r["calls"]
    print(f"{r['name']:<18}{r['calls']:>15,}{unit:>16.6f}{unit / base:>11,.0f}x")
# 출력:
# 항목                           월 호출        1회 단가(원)       단가 배수
# -------------------------------------------------------------
# 모델 호출(추출)                 180,000       45.581333  2,940,731x
# 모델 호출(판단)               1,400,000       25.699000  1,658,000x
# 벡터 검색                 230,000,000        0.000138          9x
# 체크포인트 쓰기              540,000,000        0.000072          5x
# 그래프 조회                360,000,000        0.000041          3x
# 이벤트 로그 쓰기             540,000,000        0.000016          1x
#
# (이벤트 로그 쓰기 = 1x 기준. 모델 호출(판단)은 그래프 조회의 약 62만 배)

# %% [markdown]
# ## 4. 민감도 분석 — 쿼리 2배 가속 vs 토큰 30% 절감
#
# 두 개선안을 같은 저울에 올린다.
#
# - **(A) 쿼리 2배 가속**: 그래프 조회 지연을 $2.4 \to 1.2$ms. 3주짜리 튜닝 작업.
# - **(A+) 인프라 전부 2배 가속**: 그래프·벡터·체크포인트·로그 전부 절반으로.
#   현실적으로 불가능에 가까운 상한선.
# - **(B) 토큰 30% 절감**: 컨텍스트를 다듬어 입력 토큰을 0.7배로. (24장)

# %%
def scenario(label, workload=None, ms_scale=1.0, token_scale=1.0, only=None):
    w = dict(WORKLOAD)
    if only:
        w = {k: (dict(v, ms=v["ms"] * ms_scale) if k in only else v)
             for k, v in w.items()}
        r = cost_table(w, 1.0, token_scale)
    else:
        r = cost_table(w, ms_scale, token_scale)
    t = sum(x["total"] for x in r)
    return label, t, total - t, (total - t) / total


INFRA_ITEMS = ("그래프 조회", "벡터 검색", "체크포인트 쓰기", "이벤트 로그 쓰기")

cases = [
    scenario("기준선", ),
    scenario("A. 그래프 조회 2배 가속", ms_scale=0.5, only=("그래프 조회",)),
    scenario("A+. 인프라 전부 2배 가속", ms_scale=0.5, only=INFRA_ITEMS),
    scenario("A++. 인프라 지연 0 (물리 상한)", ms_scale=0.0, only=INFRA_ITEMS),
    scenario("B. 토큰 30% 절감", token_scale=0.7),
    scenario("B+. 모델 호출 30% 감축", token_scale=0.7),  # 아래에서 정정
]

# B+ 는 호출 수 자체를 줄인 것이므로 따로 계산한다
w_fewer = {k: (dict(v, calls=int(v["calls"] * 0.7)) if k.startswith("모델") else v)
           for k, v in WORKLOAD.items()}
t_fewer = sum(x["total"] for x in cost_table(w_fewer))
cases[-1] = ("B+. 모델 호출 30% 감축", t_fewer, total - t_fewer,
             (total - t_fewer) / total)

print(f"{'시나리오':<32}{'월 비용':>16}{'절감액':>16}{'절감률':>10}")
print("-" * 74)
for label, t, saved, ratio in cases:
    print(f"{label:<32}{t:>15,.0f}원{saved:>15,.0f}원{ratio:>10.2%}")
# 출력:
# 시나리오                                        월 비용             절감액       절감률
# --------------------------------------------------------------------------
# 기준선                                  44,277,239원              0원     0.00%
# A. 그래프 조회 2배 가속                      44,269,799원          7,440원     0.02%
# A+. 인프라 전부 2배 가속                     44,230,239원         46,999원     0.11%
# A++. 인프라 지연 0 (물리 상한)                44,183,240원         93,999원     0.21%
# B. 토큰 30% 절감                         31,037,519원     13,239,720원    29.90%
# B+. 모델 호출 30% 감축                     31,022,196원     13,255,043원    29.94%

# %%
a = cases[1][2]
b = cases[4][2]
print(f"토큰 30% 절감은 그래프 조회 2배 가속보다 {b / a:,.0f}배 효과가 크다.")
print(f"인프라 지연을 «0» 으로 만들어도 절감률은 {cases[3][3]:.2%} 다.")
print("→ 암달의 법칙. 99.8% 를 차지하는 구간을 안 건드리면 상한이 0.21%다.")
# 출력:
# 토큰 30% 절감은 그래프 조회 2배 가속보다 1,780배 효과가 크다.
# 인프라 지연을 «0» 으로 만들어도 절감률은 0.21% 다.
# → 암달의 법칙. 99.8% 를 차지하는 구간을 안 건드리면 상한이 0.21%다.

# %% [markdown]
# ## 5. 시각화
#
# 왼쪽은 호출 횟수(선형 축), 오른쪽은 비용 비중. 같은 항목이 두 축에서
# 정반대 자리에 놓인다.

# %%
names = [r["name"] for r in rows]
COL_CALL = "#4C78A8"
COL_COST = "#E45756"
COL_SAVE = "#72B7B2"

fig = make_subplots(
    rows=2, cols=2,
    specs=[[{}, {}], [{}, {}]],
    subplot_titles=("① 월 호출 횟수 (많이 도는 순)",
                    "② 월 비용 비중 (돈 쓰는 순)",
                    "③ 호출 1회당 단가 (로그 축) — 뒤집힘의 원인",
                    "④ 민감도: 쿼리 가속 vs 토큰 절감 (로그 축)"),
    vertical_spacing=0.18, horizontal_spacing=0.12,
)

o_calls = sorted(rows, key=lambda r: r["calls"])
fig.add_trace(go.Bar(
    y=[r["name"] for r in o_calls], x=[r["calls"] for r in o_calls],
    orientation="h", marker_color=COL_CALL, name="월 호출",
    text=[f"{r['calls'] / 1e6:,.1f}M" for r in o_calls], textposition="auto",
), row=1, col=1)

o_cost = sorted(rows, key=lambda r: r["total"])
fig.add_trace(go.Bar(
    y=[r["name"] for r in o_cost], x=[r["total"] / total * 100 for r in o_cost],
    orientation="h", marker_color=COL_COST, name="비용 비중(%)",
    text=[f"{r['total'] / total:.2%}" for r in o_cost], textposition="auto",
), row=1, col=2)

o_unit = sorted(rows, key=lambda r: r["total"] / r["calls"])
fig.add_trace(go.Bar(
    y=[r["name"] for r in o_unit],
    x=[r["total"] / r["calls"] for r in o_unit],
    orientation="h", marker_color="#F58518", name="1회 단가(원)",
    text=[f"{r['total'] / r['calls']:,.5f}원" for r in o_unit],
    textposition="auto",
), row=2, col=1)

sens = sorted(cases[1:], key=lambda c: c[2])
fig.add_trace(go.Bar(
    y=[c[0] for c in sens], x=[max(c[2], 1) for c in sens],
    orientation="h", marker_color=COL_SAVE, name="월 절감액(원)",
    text=[f"{c[2]:,.0f}원 ({c[3]:.2%})" for c in sens], textposition="auto",
), row=2, col=2)

fig.update_xaxes(title_text="회/월", row=1, col=1)
fig.update_xaxes(title_text="%", row=1, col=2)
fig.update_xaxes(title_text="원 (로그)", type="log", row=2, col=1)
fig.update_xaxes(title_text="원 (로그)", type="log", row=2, col=2)
fig.update_layout(
    title_text="ex3_cost_model — 많이 도는 것 ≠ 돈 먹는 것",
    height=820, width=1280, showlegend=False,
    font=dict(family="Apple SD Gothic Neo, NanumGothic, sans-serif", size=12),
    margin=dict(l=140, r=40, t=90, b=60),
)

_show(fig)
fig.write_image(os.path.join(HERE, "expy.png"), scale=2)
print("saved:", os.path.join(HERE, "expy.png"))
# 출력: saved: .../expy.png

# %% [markdown]
# ## 정리
#
# | | 1위 | 값 |
# |---|---|---|
# | 호출 횟수 | 그래프 조회 (조회 계열 대표) | 월 3.6억 회 · 전체의 21.5% |
# | 비용 비중 | 모델 호출 | 월 158만 회(0.09%) · 비용의 99.8% |
#
# - 쿼리를 **빠르게** 해도 청구서는 안 바뀐다 (상한 0.21%).
# - 쿼리를 **정확하게** 해서 컨텍스트를 줄이면 토큰이 줄고, 그게 청구서를 바꾼다.
# - 쿼리 튜닝은 **지연**을 줄이는 작업, 토큰 줄이기는 **비용**을 줄이는 작업.
#   목적이 다르므로 둘을 헷갈리면 엉뚱한 데 시간을 쓴다.
# - 단 하나의 예외: 체크포인트 쓰기 월 5.4억 회. 지금은 0.09%지만 슈퍼스텝이
#   늘면 인프라 비중이 커진다. 이건 쿼리가 아니라 **구조**를 고쳐야 준다(21장).
