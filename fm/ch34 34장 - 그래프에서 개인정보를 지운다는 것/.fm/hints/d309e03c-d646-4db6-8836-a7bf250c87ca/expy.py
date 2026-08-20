# %% [markdown]
# # 재식별의 절벽 — 속성 넷이면 66%가 혼자가 된다
#
# 이름을 지웠다고 익명이 되지 않는다.
# 남은 속성(팀, 도시, 직군, 입사연도, 생월)을 **조합**하면 사람이 다시 특정된다.
#
# 이 스크립트는 34장 `ex3_reidentify.py`를 재현하고, 왜 **셋에서 넷으로 갈 때
# 절벽(cliff)이 생기는지**를 확률로 설명한다.
#
# 핵심 수식 하나만 미리 적어 둔다. 사람 $N$ 명, 속성 조합으로 만들어지는
# 칸(cell)의 수 $M$ 일 때, 임의의 한 사람이 **혼자인 칸**에 들어갈 확률은
#
# $$ p_{\text{unique}} = \left(1 - \frac{1}{M}\right)^{N-1} \approx e^{-(N-1)/M} $$
#
# 여기서 $M$ 은 속성을 하나 붙일 때마다 **곱해진다**. 지수의 인자 $N/M$ 이
# 곱셈으로 줄어드니, $p_{\text{unique}}$ 는 어느 지점에서 계단처럼 튀어오른다.

# %%
# 필요 패키지: plotly, kaleido, numpy  (pip install plotly kaleido numpy)
# 표/계산 부분은 표준 라이브러리만으로 동작한다.
import math
import os
import random
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() \
    else os.getcwd()


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


RNG = random.Random(4)   # seed 고정 — 책의 ex3 와 같은 값
N = 5000

TEAMS = [f"팀{i}" for i in range(40)]      # 40 가지
CITIES = ["강남", "마포", "판교", "성수", "여의도"]   # 5 가지
ROLES = ["개발", "기획", "디자인", "영업", "운영"]    # 5 가지
YEARS = list(range(2015, 2027))            # 12 가지
MONTHS = list(range(1, 13))                # 12 가지

CARD = {"team": 40, "city": 5, "role": 5, "joined": 12, "birth_month": 12}

print(f"사람 {N:,}명 / 속성 카디널리티 {CARD}")
# 출력: 사람 5,000명 / 속성 카디널리티 {'team': 40, 'city': 5, 'role': 5, 'joined': 12, 'birth_month': 12}

# %% [markdown]
# ## 1. 가상 인구를 만든다
#
# 이름·연락처는 이미 지운 상태다. 남은 것은 "준식별자(quasi-identifier)"뿐이다.
# 각 속성은 독립이고 균등분포라고 가정한다 (실제 인구는 편향이 있어서
# **더 쉽게** 재식별된다 — 이 가정은 낙관적인 쪽이다).

# %%
def make_population(n=N):
    return [{
        "team": RNG.choice(TEAMS),
        "city": RNG.choice(CITIES),
        "role": RNG.choice(ROLES),
        "joined": RNG.choice(YEARS),
        "birth_month": RNG.choice(MONTHS),
    } for _ in range(n)]


people = make_population()
print(people[0])
print(people[1])
# 출력: {'team': '팀15', 'city': '판교', 'role': '개발', 'joined': 2026, 'birth_month': 7}
# 출력: {'team': '팀30', 'city': '마포', 'role': '개발', 'joined': 2016, 'birth_month': 1}

# %% [markdown]
# ## 2. k-익명성과 유일성을 센다
#
# 같은 속성 조합을 가진 사람들을 한 묶음(equivalence class)으로 본다.
#
# - $k$ = 가장 작은 묶음의 크기. $k=1$ 이면 **혼자인 사람이 있다**는 뜻이다.
# - 유일성 비율 = (혼자인 사람 수) / $N$.
#
# "$k$-익명성을 만족한다"는 말은 *어떤 조합으로 봐도 최소 $k$ 명 이상으로
# 묶인다*는 성질이다.

# %%
def k_anon(pop, keys):
    """(k, 혼자인 사람 수, 실제로 채워진 칸 수) 를 돌려준다."""
    c = Counter(tuple(p[k] for k in keys) for p in pop)
    k = min(c.values())
    unique = sum(1 for v in c.values() if v == 1)
    return k, unique, len(c)


COMBOS = [
    ["team"],
    ["team", "city"],
    ["team", "city", "role"],
    ["team", "city", "role", "joined"],
    ["team", "city", "role", "joined", "birth_month"],
]

rows = []
for keys in COMBOS:
    k, uniq, filled = k_anon(people, keys)
    M = math.prod(CARD[x] for x in keys)          # 이론상 칸의 수
    theory = (1 - 1 / M) ** (N - 1)               # 이론상 유일성 확률
    rows.append({
        "keys": keys, "n_attr": len(keys), "M": M, "filled": filled,
        "k": k, "uniq": uniq, "ratio": uniq / N, "theory": theory,
        "load": N / M,
    })

hdr = (f"{'조합':<40}{'칸 M':>8}{'N/M':>8}{'k':>4}"
       f"{'혼자':>7}{'실측':>8}{'이론':>8}")
print(hdr)
print("-" * len(hdr))
for r in rows:
    print(f"{' + '.join(r['keys']):<40}{r['M']:>8}{r['load']:>8.2f}{r['k']:>4}"
          f"{r['uniq']:>7}{r['ratio']:>7.1%}{r['theory']:>8.1%}")
# 출력: 조합                                           칸 M     N/M   k     혼자      실측      이론
# 출력: -----------------------------------------------------------------------------------
# 출력: team                                          40  125.00 105      0   0.0%    0.0%
# 출력: team + city                                  200   25.00  11      0   0.0%    0.0%
# 출력: team + city + role                          1000    5.00   1     30   0.6%    0.7%
# 출력: team + city + role + joined                12000    0.42   1   3291  65.8%   65.9%
# 출력: team + city + role + joined + birth_month  144000    0.03   1   4816  96.3%   96.6%

# %% [markdown]
# ## 3. 절벽을 읽는다
#
# 실측과 이론이 소수점 단위로 맞는다. 그래서 절벽의 원인을 수식으로 말할 수 있다.
#
# | 속성 수 | $M$ | $N/M$ | 유일성 |
# |---:|---:|---:|---:|
# | 1 | 40 | 125 | 0% |
# | 2 | 200 | 25 | 0% |
# | 3 | 1,000 | 5 | 0.6% |
# | 4 | 12,000 | 0.42 | **65.8%** |
# | 5 | 144,000 | 0.035 | 96.3% |
#
# $e^{-N/M}$ 는 $N/M$ 이 1 근처를 지날 때 급하게 꺾인다.
#
# - $N/M = 5$ → $e^{-5} = 0.0067$ (거의 아무도 혼자가 아니다)
# - $N/M = 0.42$ → $e^{-0.42} = 0.66$ (**셋 중 둘이 혼자다**)
#
# 속성을 하나 붙였을 때 $M$ 이 12배가 되면서 $N/M$ 이 5 → 0.42 로 떨어졌고,
# 그 구간이 바로 $e^{-x}$ 의 무릎(knee)이다. **두 배가 아니라 백 배로 작동한다**는
# 책의 표현이 이걸 말한다 (0.6% → 65.8%, 약 110배).

# %%
for r in rows:
    print(f"{r['n_attr']}개: N/M = {r['load']:>7.3f}  "
          f"e^(-N/M) = {math.exp(-r['load']):.4f}")
# 출력: 1개: N/M = 125.000  e^(-N/M) = 0.0000
# 출력: 2개: N/M =  25.000  e^(-N/M) = 0.0000
# 출력: 3개: N/M =   5.000  e^(-N/M) = 0.0067
# 출력: 4개: N/M =   0.417  e^(-N/M) = 0.6592
# 출력: 5개: N/M =   0.035  e^(-N/M) = 0.9659

# 절벽의 위치: 유일성 50% 가 되는 M 은?  e^{-N/M} = 0.5  =>  M = N / ln 2
m_half = N / math.log(2)
print(f"\n유일성 50% 가 되는 칸의 수 M* = N / ln2 = {m_half:,.0f}")
print(f"  3개 조합의 M = 1,000  (M* 보다 작다 → 안전)")
print(f"  4개 조합의 M = 12,000 (M* 보다 크다 → 위험)")
# 출력:
# 출력: 유일성 50% 가 되는 칸의 수 M* = N / ln2 = 7,213
# 출력:   3개 조합의 M = 1,000  (M* 보다 작다 → 안전)
# 출력:   4개 조합의 M = 12,000 (M* 보다 크다 → 위험)

# %% [markdown]
# ## 4. 대응 — 일반화(generalization)로 절벽에서 물러난다
#
# 절벽의 원인은 $M$ 이 너무 커진 것이다. 그러면 $M$ 을 줄이면 된다.
# 입사연도를 "2019년" 대신 "2015~2019년" 같은 5년 구간으로 뭉개면
# 그 속성의 카디널리티가 12 → 3 으로 줄고, $M$ 도 12,000 → 3,000 이 된다.

# %%
def coarsen(pop, year_bucket=5, month_bucket=1):
    out = []
    for p in pop:
        q = dict(p)
        q["joined"] = (p["joined"] - 2015) // year_bucket
        q["birth_month"] = (p["birth_month"] - 1) // month_bucket
        out.append(q)
    return out


keys4 = ["team", "city", "role", "joined"]
print(f"{'처리':<28}{'joined 값 수':>12}{'M':>9}{'k':>4}{'유일성':>9}")
print("-" * 62)
for label, bucket in [("원본 (연 단위)", 1), ("3년 구간", 3), ("5년 구간", 5),
                      ("12년 통째 = 속성 제거", 12)]:
    pop2 = coarsen(people, year_bucket=bucket)
    card = len({p["joined"] for p in pop2})
    k, uniq, _ = k_anon(pop2, keys4)
    M = 40 * 5 * 5 * card
    print(f"{label:<28}{card:>12}{M:>9}{k:>4}{uniq / N:>8.1%}")
# 출력: 처리                            joined 값 수        M   k      유일성
# 출력: --------------------------------------------------------------
# 출력: 원본 (연 단위)                             12    12000   1   65.8%
# 출력: 3년 구간                                  4     4000   1   28.1%
# 출력: 5년 구간                                  3     3000   1   17.6%
# 출력: 12년 통째 = 속성 제거                         1     1000   1    0.6%

# %% [markdown]
# 일반화 한 번으로 65.8% → 17.6% 까지 내려간다. 하지만 $k$ 는 여전히 1 이다.
# **평균적으로 안전해졌다고 해서 모든 사람이 안전해진 것은 아니다.**
# $k=1$ 을 없애려면 남은 유일 개체를 억제(suppression)하거나 더 뭉개야 한다.
# 이것이 "정확도를 내주고 익명성을 산다"는 거래다.

# %%
# k >= 2 를 실제로 달성하려면 어디까지 가야 하나 — 억제(suppression) 비용을 센다
for label, bucket in [("원본", 1), ("3년", 3), ("5년", 5), ("제거", 12)]:
    pop2 = coarsen(people, year_bucket=bucket)
    c = Counter(tuple(p[k] for k in keys4) for p in pop2)
    drop = sum(v for v in c.values() if v < 2)   # k>=2 만들려고 버려야 하는 사람
    print(f"{label:<6} k>=2 달성을 위해 버릴 사람: {drop:>5}명 ({drop / N:>5.1%})")
# 출력: 원본     k>=2 달성을 위해 버릴 사람:  3291명 (65.8%)
# 출력: 3년     k>=2 달성을 위해 버릴 사람:  1404명 (28.1%)
# 출력: 5년     k>=2 달성을 위해 버릴 사람:   879명 (17.6%)
# 출력: 제거     k>=2 달성을 위해 버릴 사람:    30명 ( 0.6%)

# %% [markdown]
# ## 5. 그림으로 보는 절벽

# %%
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=("속성 개수별 유일성 — 3개에서 4개로 갈 때의 절벽",
                    "e^(-N/M) 곡선 위의 위치"),
    horizontal_spacing=0.12,
)

xs = [r["n_attr"] for r in rows]
fig.add_trace(go.Bar(
    x=xs, y=[r["ratio"] * 100 for r in rows], name="실측(시뮬레이션)",
    marker_color="#4C6EF5",
    text=[f"{r['ratio']:.1%}" for r in rows], textposition="outside",
), row=1, col=1)
fig.add_trace(go.Scatter(
    x=xs, y=[r["theory"] * 100 for r in rows], name="이론 (1-1/M)^(N-1)",
    mode="lines+markers", line=dict(color="#E8590C", width=2, dash="dot"),
), row=1, col=1)

# 연속 곡선: M 을 연속으로 움직이며 유일성 확률을 그린다
mm = np.logspace(1.3, 5.4, 400)
fig.add_trace(go.Scatter(
    x=mm, y=np.exp(-N / mm) * 100, name="e^(-N/M)",
    mode="lines", line=dict(color="#495057", width=2),
), row=1, col=2)
fig.add_trace(go.Scatter(
    x=[r["M"] for r in rows], y=[r["ratio"] * 100 for r in rows],
    mode="markers+text", name="실제 조합",
    marker=dict(color="#4C6EF5", size=11),
    text=[f"{r['n_attr']}개" for r in rows], textposition="top left",
), row=1, col=2)
fig.add_vline(x=m_half, line=dict(color="#E8590C", dash="dash"),
              annotation_text="M* = N/ln2 (유일성 50%)",
              annotation_position="top left",
              annotation_font=dict(color="#E8590C"), row=1, col=2)

fig.update_xaxes(title_text="조합한 속성의 개수", dtick=1, row=1, col=1)
fig.update_xaxes(title_text="칸의 수 M (log)", type="log", row=1, col=2)
fig.update_yaxes(title_text="혼자인 사람의 비율 (%)", range=[0, 108],
                 row=1, col=1)
fig.update_yaxes(title_text="유일성 확률 (%)", range=[0, 108], row=1, col=2)
fig.update_layout(
    title="이름을 지워도 재식별된다 — 속성 넷이면 66%가 혼자 (N=5,000)",
    template="plotly_white", height=470, width=1100,
    legend=dict(orientation="h", y=-0.22),
)

_show(fig)
fig.write_image(os.path.join(HERE, "expy.png"), scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 6. 정리
#
# 1. $M$(속성 조합의 경우의 수)은 속성을 붙일 때마다 **곱해진다**.
#    선형이 아니라 지수적으로 커진다.
# 2. 유일성은 $e^{-N/M}$ 을 따르고, 이 함수는 $N \approx M$ 근처에서 급히 꺾인다.
#    그 무릎을 넘는 순간이 "절벽"이다. 이 예제에서는 3개 → 4개 구간이었다.
# 3. 그래서 익명화 심사는 **속성 하나씩** 보면 안 되고 **조합**으로 봐야 한다.
#    "팀만으로는 105명" 은 아무 보장이 아니다.
# 4. 그리고 그래프에서는 여기에 하나가 더 붙는다. 관계(엣지)의 모양 자체가
#    속성이다. 이웃의 종류·개수·2-hop 패턴은 각각 카디널리티가 큰 준식별자다.
#    $M$ 이 훨씬 빨리 커지니 절벽도 훨씬 빨리 온다.
