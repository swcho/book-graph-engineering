# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
#   - plotly/kaleido 가 없어도 시뮬레이션·실측 셀은 그대로 돌아간다.
#   - 실제 DB(kuzu 등)는 쓰지 않는다. 순수 파이썬으로 «고정비용 vs 규모비용»만 재현한다.

# %% [markdown]
# # 인덱스 효과를 재려면 규모를 충분히 키워야 한다
#
# **질문** — 인덱스 효과를 재려면 무엇을 주의해야 하는가?
#
# **답** — 규모를 충분히 키워야 한다. 수천 개에서는 파싱 값이 지배해서 아무것도 안 보인다.
#
# ## 모형
#
# 쿼리 한 번의 시간은 두 덩어리로 쪼갤 수 있다.
#
# $$ T(N) \;=\; \underbrace{C_{\text{fix}}}_{\text{파싱 + 플래닝 + 왕복}} \;+\; \underbrace{W(N)}_{\text{실제 탐색}} $$
#
# 여기서 $C_{\text{fix}}$ 는 **N 과 무관한 상수**다. 쿼리 문자열을 토큰으로 쪼개고,
# 플랜을 세우고, 결과를 감싸서 돌려주는 값. 반면 $W(N)$ 만 데이터 규모를 탄다.
#
# | 접근 | $W(N)$ | 비고 |
# |---|---|---|
# | 전체 스캔 | $c_s \cdot N$ | 인덱스 없음. $O(N)$ |
# | 정렬 인덱스 | $c_t \cdot \log_2 N$ | B-tree 탐색. $O(\log N)$ |
# | 해시 인덱스 | $c_h$ | 기본 키 조회. $O(1)$ |
#
# 우리가 재고 싶은 «인덱스 배수»는 이렇게 정의된다.
#
# $$ R(N) \;=\; \frac{T_{\text{scan}}(N)}{T_{\text{index}}(N)}
#          \;=\; \frac{C_{\text{fix}} + c_s N}{C_{\text{fix}} + c_h} $$
#
# 핵심은 분모·분자에 **똑같은 $C_{\text{fix}}$ 가 들어 있다**는 것이다.
# $c_s N \ll C_{\text{fix}}$ 인 구간에서는
#
# $$ \lim_{N \to 0} R(N) \;\approx\; \frac{C_{\text{fix}}}{C_{\text{fix}}} \;=\; 1 $$
#
# 즉 **배수가 1 근처에 붙어 버린다**. 인덱스가 잘 듣고 있어도 측정값에는 안 나타난다.
# 33장 예제 2가 2,000~128,000개에서 배수 1.1을 보고 «어? 인덱스 효과가 없네» 하게 되는
# 이유가 정확히 이것이다.

# %%
import math
import time


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# 모형 상수 (단위: ms). 실제 임베디드 그래프 DB 를 재 본 대략의 크기다.
C_FIX = 0.35        # 파싱 + 플래닝 + 결과 래핑. N 과 무관한 고정비용
C_SCAN = 2.0e-6     # 노드 하나 훑는 값
C_HASH = 0.002      # 해시 인덱스 한 방 (사실상 상수)
C_TREE = 0.0015     # B-tree 한 레벨당 값


def t_scan(n):
    return C_FIX + C_SCAN * n


def t_hash(n):
    return C_FIX + C_HASH


def t_tree(n):
    return C_FIX + C_TREE * math.log2(max(n, 2))


print(f"고정비용 C_fix = {C_FIX} ms")
print(f"스캔이 고정비용과 같아지는 N = {C_FIX / C_SCAN:,.0f}")
# 출력: 고정비용 C_fix = 0.35 ms
# 출력: 스캔이 고정비용과 같아지는 N = 175,000

# %% [markdown]
# ## 1단계 — 모형으로 배수가 언제 «보이기» 시작하는지 본다
#
# N 을 1,000 부터 1억까지 로그 눈금으로 키우면서 $R(N)$ 을 찍어 본다.

# %%
SIZES = [10**3, 10**4, 10**5, 10**6, 10**7, 10**8]

print(f"{'N':>12}{'스캔 ms':>12}{'해시 ms':>12}{'배수':>10}   {'보이나?':>8}")
print("-" * 60)
model_rows = []
for n in SIZES:
    ts, th = t_scan(n), t_hash(n)
    r = ts / th
    verdict = "안 보임" if r < 1.5 else ("어렴풋" if r < 5 else "명확")
    model_rows.append((n, ts, th, r))
    print(f"{n:>12,}{ts:>12.3f}{th:>12.3f}{r:>9.1f}x   {verdict:>8}")
# 출력:            N     스캔 ms     해시 ms      배수      보이나?
# 출력: ------------------------------------------------------------
# 출력:        1,000       0.352       0.352      1.0x      안 보임
# 출력:       10,000       0.370       0.352      1.1x      안 보임
# 출력:      100,000       0.550       0.352      1.6x       어렴풋
# 출력:    1,000,000       2.350       0.352      6.7x         명확
# 출력:   10,000,000      20.350       0.352     57.8x         명확
# 출력:  100,000,000     200.350       0.352    569.2x         명확

# %% [markdown]
# 1,000개에서 배수는 **1.0배**다. 인덱스가 있으나 없으나 똑같아 보인다.
# 그런데 같은 모형, 같은 상수로 1억 개까지 키우면 **569배**가 된다.
# 인덱스의 성질이 변한 게 아니라, **고정비용에 가려져 있던 것이 드러난 것**뿐이다.
#
# 배수가 $R$ 배로 «보이려면» 필요한 N 은 식을 뒤집어서 구할 수 있다.
#
# $$ N \;\ge\; \frac{(R-1)\,(C_{\text{fix}} + c_h)}{c_s} $$

# %%
def n_for_ratio(r):
    return (r - 1) * (C_FIX + C_HASH) / C_SCAN


for r in (1.1, 2, 5, 10, 100):
    print(f"배수 {r:>5}x 를 보려면 최소 N ≈ {n_for_ratio(r):>15,.0f}")
# 출력: 배수   1.1x 를 보려면 최소 N ≈          17,600
# 출력: 배수     2x 를 보려면 최소 N ≈         176,000
# 출력: 배수     5x 를 보려면 최소 N ≈         704,000
# 출력: 배수    10x 를 보려면 최소 N ≈       1,584,000
# 출력: 배수   100x 를 보려면 최소 N ≈      17,424,000

# %% [markdown]
# 「인덱스가 10배 빠르다」를 눈으로 확인하려면 **150만 건 이상**이 필요하다.
# 수천 건짜리 장난감 데이터로 재고 결론을 내리면 안 되는 이유다.
#
# ## 2단계 — 실측. 리스트 선형 탐색 vs dict 해시 조회
#
# 모형이 아니라 진짜로 재 본다. DB 대신 파이썬 자료구조를 쓴다.
#
# - **스캔** = `list.index(target)` → $O(N)$
# - **인덱스** = `dict[target]` → $O(1)$
#
# 그리고 «파싱·플래닝»을 흉내 내기 위해, 두 경우 **모두**에 같은
# 쿼리 문자열 파싱 작업을 붙인다. 실제 DB 가 매 호출마다 하는 그 일이다.

# %%
QUERY = "MATCH (p:Person) WHERE p.name = $n RETURN p.id, p.city ORDER BY p.id"
PLAN_REPS = 12   # 실제 DB 의 파싱+플래닝 비용에 자릿수를 맞추기 위한 반복


def parse_and_plan(q=QUERY):
    """쿼리 파싱 + 플래닝 흉내. N 과 완전히 무관한 고정비용."""
    plan = None
    for _ in range(PLAN_REPS):
        toks = q.replace("(", " ( ").replace(")", " ) ").replace(",", " , ").split()
        ops, args = [], []
        for t in toks:
            (ops if t.isupper() else args).append(t)
        plan = (tuple(ops), tuple(args))
    return plan


def bench(fn, reps):
    t0 = time.perf_counter()
    for _ in range(reps):
        fn()
    return (time.perf_counter() - t0) / reps * 1000   # ms


# 고정비용만 따로 잰다
FIX_MS = bench(parse_and_plan, 2000)
print(f"측정된 고정비용(파싱+플래닝) = {FIX_MS * 1000:.1f} us")
# 출력: 측정된 고정비용(파싱+플래닝) = 22.3 us
#       (기기·파이썬 버전마다 절대값은 달라진다. 중요한 건 «N 과 무관한 상수»라는 점이다)

# %%
REAL_SIZES = [1_000, 4_000, 16_000, 64_000, 256_000, 1_000_000, 4_000_000]

print(f"{'N':>11}{'스캔 ms':>11}{'인덱스 ms':>11}{'배수':>9}"
      f"{'고정비 비중(스캔)':>18}")
print("-" * 62)
real_rows = []
for n in REAL_SIZES:
    names = [f"P{i}" for i in range(n)]
    index = {name: i for i, name in enumerate(names)}
    target = f"P{n // 2}"                     # 평균적인 위치
    reps = max(3, min(400, 2_000_000 // n))

    def q_scan(_names=names, _t=target):
        parse_and_plan()
        return _names.index(_t)

    def q_index(_index=index, _t=target):
        parse_and_plan()
        return _index[_t]

    ms_scan = bench(q_scan, reps)
    ms_idx = bench(q_index, reps)
    real_rows.append((n, ms_scan, ms_idx, ms_scan / ms_idx))
    print(f"{n:>11,}{ms_scan:>11.4f}{ms_idx:>11.4f}"
          f"{ms_scan / ms_idx:>8.1f}x{FIX_MS / ms_scan:>17.0%}")
    del names, index
# 출력:           N    스캔 ms  인덱스 ms     배수  고정비 비중(스캔)
# 출력: --------------------------------------------------------------
# 출력:       1,000     0.0261     0.0216      1.2x              86%
# 출력:       4,000     0.0387     0.0222      1.7x              58%
# 출력:      16,000     0.0935     0.0217      4.3x              24%
# 출력:      64,000     0.2884     0.0212     13.6x               8%
# 출력:     256,000     1.0380     0.0220     47.3x               2%
# 출력:   1,000,000     4.5610     0.0277    164.4x               0%
# 출력:   4,000,000    16.3126     0.0265    615.9x               0%

# %% [markdown]
# 표를 위에서 아래로 읽는 것이 이 카드의 전부다.
#
# - **1,000개**: 배수 1.2배. 고정비용이 스캔 시간의 **86%**를 차지한다.
#   여기서 「인덱스 별 효과 없네」라고 결론 내면 **틀린다**.
# - **16,000개**: 4.3배. 이제야 어렴풋이 보인다.
# - **100만개**: 164배. 고정비용 비중이 0%로 떨어지고, 진짜 차이가 그대로 드러난다.
#
# 인덱스가 갑자기 좋아진 게 아니다. **눈금이 바뀐 것**이다.
#
# > 33장의 예제 2 가 `SIZES = [2000, 8000, 32000, 128000]` 에서
# > 배수 1.1 을 보고 멈춘 것이 바로 표의 첫 두 줄 구간이다.
#
# ## 3단계 — 그림으로
#
# 왼쪽: 시간의 절대값(log-log). 오른쪽: 배수.
# 배수 곡선이 «1 에 붙어 있는 평평한 구간»이 바로 측정하면 안 되는 규모다.

# %%
def make_fig():
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    ns = [10**(3 + 0.1 * k) for k in range(51)]        # 1e3 ~ 1e8
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("① 한 번의 시간 (모형, log-log)",
                        "② 인덱스 배수 R(N) — 모형 vs 실측"),
    )

    # ① 시간
    fig.add_trace(go.Scatter(x=ns, y=[C_FIX] * len(ns), name="고정비용 C_fix",
                             line=dict(color="#888", dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=ns, y=[C_SCAN * n for n in ns], name="스캔 작업분 O(N)",
                             line=dict(color="#d62728", dash="dash")), row=1, col=1)
    fig.add_trace(go.Scatter(x=ns, y=[t_scan(n) for n in ns], name="스캔 총합",
                             line=dict(color="#d62728", width=3)), row=1, col=1)
    fig.add_trace(go.Scatter(x=ns, y=[t_tree(n) for n in ns], name="정렬 인덱스 총합 O(log N)",
                             line=dict(color="#2ca02c", width=2, dash="longdash")),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=ns, y=[t_hash(n) for n in ns], name="해시 인덱스 총합 O(1)",
                             line=dict(color="#1f77b4", width=3)), row=1, col=1)

    # ② 배수
    fig.add_trace(go.Scatter(x=ns, y=[t_scan(n) / t_hash(n) for n in ns],
                             name="모형 배수", line=dict(color="#1f77b4", width=3)),
                  row=1, col=2)
    fig.add_trace(go.Scatter(x=[r[0] for r in real_rows], y=[r[3] for r in real_rows],
                             name="실측 배수 (list vs dict)", mode="markers+lines",
                             marker=dict(size=9, symbol="diamond", color="#ff7f0e"),
                             line=dict(color="#ff7f0e", dash="dot")), row=1, col=2)
    fig.add_hline(y=1, line=dict(color="#888", dash="dot"), row=1, col=2)

    # 「아무것도 안 보이는 구간」 표시
    n_edge = n_for_ratio(1.5)
    for col in (1, 2):
        fig.add_vrect(x0=10**3, x1=n_edge, fillcolor="#d62728", opacity=0.07,
                      line_width=0, row=1, col=col)
    fig.add_annotation(x=math.log10(4.0e3), y=math.log10(90),
                       text="이 구간에서 재면<br>아무것도 안 보인다<br>(배수 ≈ 1)",
                       showarrow=False, align="center",
                       font=dict(size=12, color="#d62728"), row=1, col=2)

    fig.update_xaxes(type="log", title_text="노드 수 N", row=1, col=1)
    fig.update_xaxes(type="log", title_text="노드 수 N", row=1, col=2)
    fig.update_yaxes(type="log", title_text="시간 (ms)", row=1, col=1)
    fig.update_yaxes(type="log", title_text="배수 (스캔 / 인덱스)", row=1, col=2)
    fig.update_layout(
        title="인덱스 효과는 규모를 키워야 드러난다 — 고정비용이 작은 N 을 덮는다",
        height=520, width=1180, template="plotly_white",
        legend=dict(orientation="h", y=-0.18),
    )
    return fig


try:
    _fig = make_fig()
    _show(_fig)
    import os
    _fig.write_image(os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png"),
                     scale=2)
    print("expy.png 저장 완료")
except ImportError as e:
    print(f"시각화 건너뜀 (패키지 없음): {e}")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 4단계 — 반대 방향의 함정
#
# 「작은 데이터에서 재면 인덱스 효과를 못 본다」의 **뒷면**도 33장이 짚는다.
#
# > 반대로, 수천 개짜리 데이터에 인덱스를 붙이며 튜닝하는 것도 헛일이다.
#
# 수천 건에서는 인덱스를 붙여 봐야 실제로 줄어드는 게 없다. 줄일 수 있는 최대치가
# 전체의 몇 %뿐이기 때문이다. 암달의 법칙과 같은 모양이다.

# %%
print(f"{'N':>11}{'인덱스로 줄일 수 있는 최대':>26}")
print("-" * 38)
for n, ts, th, _r in model_rows:
    print(f"{n:>11,}{(ts - th) / ts:>25.1%}")
# 출력:           N   인덱스로 줄일 수 있는 최대
# 출력: --------------------------------------
# 출력:       1,000                     0.0%
# 출력:      10,000                     4.9%
# 출력:     100,000                    36.0%
# 출력:   1,000,000                    85.0%
# 출력:  10,000,000                    98.3%
# 출력: 100,000,000                    99.8%

# %% [markdown]
# ## 정리
#
# 1. 쿼리 시간 = **고정비용(파싱·플래닝)** + **규모비용(탐색)**. 인덱스는 뒤쪽만 건드린다.
# 2. 작은 N 에서는 고정비용이 분모·분자를 동시에 채워서 배수를 **1 로 눌러 버린다**.
# 3. 그래서 인덱스 효과를 재려면 $c_s N \gg C_{\text{fix}}$ 가 되도록 **규모를 키워야** 한다.
#    실무 감각으로는 최소 수십만~백만 단위.
# 4. 거꾸로, 수천 건짜리 데이터에 인덱스를 붙이며 튜닝하는 것도 헛일이다. 줄일 게 없다.
# 5. 실측할 때는 «고정비용이 전체의 몇 %인가»를 같이 찍어 보면 실수를 피할 수 있다.
