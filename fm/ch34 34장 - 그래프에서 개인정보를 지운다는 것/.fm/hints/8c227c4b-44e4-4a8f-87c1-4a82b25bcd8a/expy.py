# %% [markdown]
# # 재식별에 대응하는 세 가지 방법 — 일반화 / 억제 / 잡음
#
# 34.3절의 실험을 재현하고, 그 뒤에 붙는 **대응 셋**을 실제로 적용해 본다.
#
# 이름을 지워도 속성 조합이 남으면 사람이 특정된다. 대응은 셋이다.
#
# | 방법 | 하는 일 | 예 |
# |---|---|---|
# | 일반화(generalization) | 값의 해상도를 낮춘다 | `2019년 입사` → `2015~2020년` |
# | 억제(suppression) | 위험한 칸을 아예 뺀다 | 혼자인 사람의 `city`를 `*`로 |
# | 잡음(noise) | 값을 무작위로 흔든다 | `생월 7` → `생월 5~9` 중 하나 |
#
# 셋 다 **정확도를 내주고 익명성을 산다**. 이 노트북의 목표는 그 거래를
# 말이 아니라 숫자로 같은 표에 놓는 것이다.
#
# ## 재는 지표
#
# 익명성 쪽:
#
# $$\text{유일성 비율} = \frac{\bigl|\{g \in G : |g| = 1\}\bigr|}{N},
#   \qquad k = \min_{g \in G} |g|$$
#
# $G$는 준식별자(quasi-identifier) 조합이 같은 사람끼리 묶은 동등 클래스다.
# $k$가 1이면 혼자인 사람이 있다는 뜻이고, $k$-익명성은
# "어떤 조합으로도 최소 $k$명 이상으로 묶인다"는 성질이다.
#
# 유용성 쪽 — 세 가지 분석 작업을 정해 두고, 각각의 답이 얼마나 틀리는지 본다.
#
# $$\text{연도 TVD} = \tfrac{1}{2}\sum_{y}\bigl|\hat{p}(y) - p(y)\bigr|,
#   \quad
#   \text{도시 MAPE} = \frac{1}{|C|}\sum_{c}\frac{|\hat{n}_c - n_c|}{n_c},
#   \quad
#   \text{부서 MAE} = \frac{1}{|D|}\sum_{d}\bigl|\hat{\mu}_d - \mu_d\bigr|$$
#
# 세 지표를 고른 이유가 있다. **세 방법이 각각 다른 지표를 깨뜨린다.**
# 일반화는 연도 분포를, 억제는 도시별 인원 수를, 잡음은 부서별 평균을 깬다.
# 하나의 스칼라로 "유용성 손실"을 뭉개면 이 차이가 안 보인다.

# %%
# 필요 패키지: plotly, kaleido  (그 외는 표준 라이브러리만 사용)
#   pip install plotly kaleido
import math
import os
import random
import statistics
from collections import Counter, defaultdict

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


SEED = 34
rng = random.Random(SEED)

N = 5000
TEAMS = [f"팀{i}" for i in range(40)]
CITIES = ["강남", "마포", "판교", "성수", "여의도"]
ROLES = ["개발", "기획", "디자인", "영업", "운영"]
YEARS = list(range(2015, 2027))

# 준식별자 넷 — 34.3절에서 «절벽»이 생기는 그 조합
QI = ["team", "city", "role", "joined"]
MISSING = "*"


def make_people(n=N):
    return [{
        "team": rng.choice(TEAMS),
        "city": rng.choice(CITIES),
        "role": rng.choice(ROLES),
        "joined": rng.choice(YEARS),
        "birth_month": rng.randint(1, 12),
    } for _ in range(n)]


people = make_people()
print(f"가상 인구 {len(people):,}명, 준식별자 {QI}")
print("예시:", people[0])
# 출력: 가상 인구 5,000명, 준식별자 ['team', 'city', 'role', 'joined']
# 출력: 예시: {'team': '팀33', 'city': '판교', 'role': '운영', 'joined': 2015, 'birth_month': 4}

# %% [markdown]
# ## 1. 기준선 — 이름만 지운 상태
#
# 속성을 하나씩 붙여 가며 유일성 비율을 센다. 34.3절의 «절벽»을 먼저 확인한다.

# %%
def k_anon(rows, keys=QI):
    """(최소 그룹 k, 혼자인 사람 수, 동등 클래스 수)"""
    c = Counter(tuple(r[k] for k in keys) for r in rows)
    return min(c.values()), sum(1 for v in c.values() if v == 1), len(c)


print(f"{'조합':<40}{'k':>5}{'혼자':>7}{'유일성':>9}")
print("-" * 62)
for i in range(1, len(QI) + 2):
    keys = (QI + ["birth_month"])[:i]
    k, uniq, groups = k_anon(people, keys)
    print(f"{' + '.join(keys):<40}{k:>5}{uniq:>7}{uniq / len(people):>8.1%}")
# 출력: 조합                                          k     혼자      유일성
# 출력: --------------------------------------------------------------
# 출력: team                                      110      0    0.0%
# 출력: team + city                                14      0    0.0%
# 출력: team + city + role                          1     32    0.6%
# 출력: team + city + role + joined                 1   3348   67.0%
# 출력: team + city + role + joined + birth_month   1   4848   97.0%

# %% [markdown]
# 셋에서 넷으로 갈 때 0.6% → 67.0%. 두 배가 아니라 백 배다.
# 조합 가능한 칸의 수가 곱해지기 때문이다.
# $40 \times 5 \times 5 = 1000$개 칸에 5000명이면 칸당 평균 5명이지만,
# 여기에 연도 12개를 곱하면 12000개 칸에 5000명 — 칸이 사람보다 많아진다.
# 칸이 사람보다 많아지는 순간이 절벽이다.
#
# **이 상태가 「이름은 지웠습니다」다.** 3분의 2가 혼자다.
#
# ## 2. 세 가지 대응을 구현한다
#
# 각 함수는 원본을 건드리지 않고 사본을 돌려준다. 유용성 손실을 재려면
# 원본이 남아 있어야 하니까.

# %%
# --- (1) 일반화 — 입사연도를 구간으로 뭉갠다 -------------------------------
BUCKETS = [(2015, 2020), (2021, 2023), (2024, 2026)]


def bucket_of(year):
    for lo, hi in BUCKETS:
        if lo <= year <= hi:
            return f"{lo}~{hi}년"
    return "기타"


def generalize(rows):
    out = []
    for r in rows:
        q = dict(r)
        if not isinstance(r["joined"], str):
            q["joined"] = bucket_of(r["joined"])
        out.append(q)
    return out


# --- (2) 억제 — 혼자인 사람의 city 를 지운다 -------------------------------
def suppress(rows, cols=("city",), keys=QI):
    """준식별자 조합이 유일한 사람만 골라 지정한 칸을 뺀다."""
    c = Counter(tuple(r[k] for k in keys) for r in rows)
    out, hit = [], 0
    for r in rows:
        q = dict(r)
        if c[tuple(r[k] for k in keys)] == 1:
            for col in cols:
                q[col] = MISSING
            hit += 1
        out.append(q)
    return out, hit


# --- (3) 잡음 — 생월을 ±2 흔든다 (1~12 순환) -------------------------------
def add_noise(rows, col="birth_month", width=2, seed=SEED):
    r2 = random.Random(seed)
    out = []
    for r in rows:
        q = dict(r)
        q[col] = (r[col] + r2.randint(-width, width) - 1) % 12 + 1  # 12월+2 → 2월
        out.append(q)
    return out


g_rows = generalize(people)
s_rows, s_hit = suppress(people)
n_rows = add_noise(people)

print("일반화 후 joined 분포:",
      dict(sorted(Counter(r["joined"] for r in g_rows).items())))
print(f"억제로 city 를 뺀 사람: {s_hit}명 ({s_hit / len(people):.1%})")
print("잡음 전/후 생월 앞 8명:",
      [p["birth_month"] for p in people[:8]],
      [p["birth_month"] for p in n_rows[:8]])
# 출력: 일반화 후 joined 분포: {'2015~2020년': 2493, '2021~2023년': 1225, '2024~2026년': 1282}
# 출력: 억제로 city 를 뺀 사람: 3348명 (67.0%)
# 출력: 잡음 전/후 생월 앞 8명: [4, 7, 9, 10, 1, 1, 5, 4] [6, 7, 11, 8, 12, 11, 6, 4]

# %% [markdown]
# 여기서 억제의 성질이 벌써 드러난다. 유일한 사람이 67.0%이므로
# **인구의 3분의 2에게서 도시 칸을 뺀다.** 「혼자인 사람만 건드린다」가
# 소수 손실처럼 들리지만, 유일성이 높은 데이터에서는 그 소수가 다수다.
#
# ## 3. 유용성을 재는 자
#
# 세 가지 분석 작업을 정한다.
#
# - **작업 A** — 연도별 입사 인원 분포. 일반화된 데이터에서는 원래 연도를
#   모르므로, 분석가는 구간 안에 균등 분배해 추정한다. 그 추정의 오차를 잰다.
# - **작업 B** — 도시별 인원 수. 억제된 행은 `city == '*'` 이므로
#   `WHERE city = '마포'` 같은 질의에 아예 안 걸린다. 그만큼 과소 집계된다.
# - **작업 C** — 부서별 평균 생월. 잡음이 여기를 흔든다.

# %%
def year_dist(rows):
    """연도 단위 추정 분포. 구간은 균등 분배, '*' 는 전체 연도에 균등 분배."""
    acc = defaultdict(float)
    for r in rows:
        v = r["joined"]
        if v == MISSING:
            span = YEARS
        elif isinstance(v, str):
            lo, hi = (int(x) for x in v.rstrip("년").split("~"))
            span = list(range(lo, hi + 1))
        else:
            span = [v]
        for y in span:
            acc[y] += 1.0 / len(span)
    total = sum(acc.values())
    return {k: v / total for k, v in acc.items()}


def tvd(p, q):
    return 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in set(p) | set(q))


def city_counts(rows):
    """'*' 는 어떤 도시에도 안 걸린다 — 질의가 보는 그대로."""
    c = Counter(r["city"] for r in rows)
    return {city: c.get(city, 0) for city in CITIES}


def mape(est, true):
    return sum(abs(est[k] - true[k]) / true[k] for k in true) / len(true)


def role_means(rows):
    acc = defaultdict(list)
    for r in rows:
        acc[r["role"]].append(r["birth_month"])
    return {k: statistics.fmean(v) for k, v in acc.items()}


def mae(a, b):
    keys = set(a) | set(b)
    return sum(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys) / len(keys)


BASE_YEAR = year_dist(people)
BASE_CITY = city_counts(people)
BASE_ROLE = role_means(people)
print("기준 연도분포(앞 4):",
      {k: round(v, 4) for k, v in sorted(BASE_YEAR.items())[:4]})
print("기준 도시별 인원:", BASE_CITY)
print("기준 부서 평균 생월:", {k: round(v, 3) for k, v in sorted(BASE_ROLE.items())})
# 출력: 기준 연도분포(앞 4): {2015: 0.083, 2016: 0.0806, 2017: 0.0798, 2018: 0.086}
# 출력: 기준 도시별 인원: {'강남': 1006, '마포': 1031, '판교': 989, '성수': 1001, '여의도': 973}
# 출력: 기준 부서 평균 생월: {'개발': 6.347, '기획': 6.678, '디자인': 6.415, '영업': 6.515, '운영': 6.394}

# %% [markdown]
# ## 4. 같은 표에 놓는다 — 익명성 이득 vs 유용성 손실
#
# 마지막 줄에 셋을 **조합**한 결과도 넣는다.
# 조합 순서는 일반화 → 잡음 → 억제다. 억제를 마지막에 둔 이유가 있다.
# 앞의 두 단계가 이미 유일성을 깎아 놓았으므로, 억제가 손댈 사람이 줄어든다.
# **순서 자체가 설계 변수다.**

# %%
def combined(rows):
    r = generalize(rows)
    r = add_noise(r)
    return suppress(r)


c_rows, c_hit = combined(people)

VARIANTS = [
    ("기준선(이름만 지움)", people, 0),
    ("(1) 일반화 — joined 3구간", g_rows, 0),
    ("(2) 억제 — 유일한 사람의 city", s_rows, s_hit),
    ("(3) 잡음 — birth_month ±2", n_rows, 0),
    ("(1)→(3)→(2) 조합", c_rows, c_hit),
]

report = []
for name, rows, hit in VARIANTS:
    k, uniq, groups = k_anon(rows)
    report.append({
        "name": name,
        "k": k, "uniq_rate": uniq / len(rows), "groups": groups,
        "year_tvd": tvd(year_dist(rows), BASE_YEAR),
        "city_mape": mape(city_counts(rows), BASE_CITY),
        "role_mae": mae(role_means(rows), BASE_ROLE),
        "touched": hit / len(rows),
    })

hdr = (f"{'방법':<28}{'k':>3}{'유일성':>9}{'클래스':>7}"
       f"{'A:연도TVD':>11}{'B:도시MAPE':>12}{'C:부서MAE':>11}{'변형율':>8}")
print(hdr)
print("-" * 96)
for r in report:
    print(f"{r['name']:<28}{r['k']:>3}{r['uniq_rate']:>8.1%}{r['groups']:>7}"
          f"{r['year_tvd']:>11.4f}{r['city_mape']:>11.1%}{r['role_mae']:>11.3f}"
          f"{r['touched']:>8.1%}")
# 출력: 방법                            k      유일성    클래스    A:연도TVD    B:도시MAPE    C:부서MAE     변형율
# 출력: ------------------------------------------------------------------------------------------------
# 출력: 기준선(이름만 지움)                   1   67.0%   4114     0.0000       0.0%      0.000    0.0%
# 출력: (1) 일반화 — joined 3구간          1   18.2%   2360     0.0107       0.0%      0.000    0.0%
# 출력: (2) 억제 — 유일한 사람의 city         1   17.3%   2675     0.0000      67.0%      0.000   67.0%
# 출력: (3) 잡음 — birth_month ±2       1   67.0%   4114     0.0000       0.0%      0.132    0.0%
# 출력: (1)→(3)→(2) 조합                1    4.2%   1944     0.0107      18.2%      0.132   18.2%

# %% [markdown]
# ### 읽는 법
#
# 표가 세 방법의 **성격 차이**를 그대로 보여 준다. 각자 다른 칸을 깨뜨린다.
#
# - **일반화**: 유일성 67.0% → 18.2%. 준식별자에 직접 작용하므로 동등
#   클래스가 4114개에서 2360개로 합쳐진다. 대가는 연도 TVD 0.0107 — 연도
#   단위로 물으면 확률질량의 1.1%가 잘못된 연도로 배정된다. 구간 단위 집계만
#   한다면 손실은 0으로 보인다.
#   **손실이 안 보이는 게 아니라, 그 해상도를 이미 포기한 것이다.**
#   그리고 이 1.1%는 운이 좋아서 작다 — 다음 셀에서 확인한다.
# - **억제**: 유일성 17.3%로 일반화와 거의 같은 값을 사는데, 값이 비싸다.
#   인구의 67.0%에게서 도시 칸을 뺐고, 그 결과 도시별 인원 집계가
#   **평균 67% 과소 집계**된다. 남은 값 자체는 정확하다는 게 억제의 장점이지만,
#   결측이 무작위가 아니라 "특이한 사람"에 몰려 있어 조용한 편향을 만든다.
# - **잡음**: 유일성을 **전혀** 못 내렸다(67.0% 그대로). `birth_month`가
#   준식별자 넷에 안 들어 있으니 당연하다. 그런데 부서 평균 생월은 0.132달
#   어긋났다. **가장 나쁜 거래 — 유용성만 내주고 익명성은 못 샀다.**
#   잡음을 흔들려면 *실제로 식별에 쓰이는 칸*을 흔들어야 한다.
# - **조합**: 4.2%까지 내려간다. 그리고 순서 설계가 값을 한다.
#   억제 단독으로는 67%를 건드렸는데, 일반화를 먼저 하니 18.2%만 건드리고도
#   더 낮은 유일성에 도달했다. 같은 익명성을 더 싸게 산 것이다.
#
# 그리고 모든 줄의 $k$가 여전히 1이다. **평균이 좋아져도 최악은 안 좋아진다.**
# 유일성 4.2%는 여전히 209명이 혼자라는 뜻이다.

# %% [markdown]
# ### 곁가지 — 일반화의 손실은 데이터 분포에 달려 있다
#
# 위에서 연도 TVD가 0.0107밖에 안 나온 이유는 입사연도가 균등 분포이기
# 때문이다. 구간 안에 균등 분배해 복원하면 거의 맞는다.
# 실제 조직은 그렇지 않다 — 최근 몇 년에 몰려 있다. 기울어진 분포에서
# 같은 일반화를 하면 손실이 어떻게 되는지 본다.

# %%
def make_skewed(n=N, alpha=0.35, seed=SEED + 1):
    """최근 연도에 지수적으로 몰린 입사연도."""
    r = random.Random(seed)
    w = [math.exp(alpha * (y - YEARS[0])) for y in YEARS]
    out = []
    for _ in range(n):
        out.append({
            "team": r.choice(TEAMS), "city": r.choice(CITIES),
            "role": r.choice(ROLES),
            "joined": r.choices(YEARS, weights=w)[0],
            "birth_month": r.randint(1, 12),
        })
    return out


print(f"{'분포':<12}{'2015년 비중':>12}{'2026년 비중':>12}"
      f"{'유일성':>9}{'일반화 후':>10}{'연도TVD':>10}")
print("-" * 66)
for label, pop in [("균등", people), ("최근 편중", make_skewed())]:
    base = year_dist(pop)
    _, u0, _ = k_anon(pop)
    _, u1, _ = k_anon(generalize(pop))
    print(f"{label:<12}{base[2015]:>11.1%}{base[2026]:>12.1%}"
          f"{u0 / len(pop):>8.1%}{u1 / len(pop):>10.1%}"
          f"{tvd(year_dist(generalize(pop)), base):>10.4f}")
# 출력: 분포              2015년 비중    2026년 비중      유일성     일반화 후     연도TVD
# 출력: ------------------------------------------------------------------
# 출력: 균등                 8.3%        8.2%   67.0%     18.2%    0.0107
# 출력: 최근 편중              0.6%       30.1%   45.0%     15.4%    0.1355

# %% [markdown]
# TVD가 0.0107에서 0.1355로 **13배** 커졌다. 익명성 이득은 비슷한 크기인데
# (67.0→18.2 vs 45.0→15.4, 둘 다 4분의 1 수준으로 감소) 정확도 손실만 13배다.
#
# 그래서 "일반화는 값이 싸다"는 일반론은 없다. **구간을 어디서 끊느냐와
# 데이터가 그 구간 안에서 어떻게 퍼져 있느냐가 값을 정한다.**
# 균등하게 퍼진 칸을 뭉개면 싸고, 한쪽에 몰린 칸을 뭉개면 비싸다.
# 익명화 파라미터는 실제 데이터에 대고 측정해서 정하는 것이지
# 표준값을 베끼는 게 아니다.

# %% [markdown]
# ## 5. $k \ge 2$를 진짜로 만들려면 — 억제의 강도를 올린다
#
# 억제하는 칸의 수를 1개(`city`)에서 2개, 3개로 늘리면서
# 유일성과 $k$가 어떻게 변하는지 본다.

# %%
print(f"{'억제한 칸':<26}{'k':>3}{'혼자':>7}{'유일성':>9}{'지워진 셀':>11}")
print("-" * 58)
SUP_CURVE = []
for cols in ([], ["city"], ["city", "role"], ["city", "role", "joined"]):
    rows, hit = suppress(people, cols=cols) if cols else (people, 0)
    k, uniq, _ = k_anon(rows)
    cells = hit * len(cols)
    SUP_CURVE.append((len(cols), cells, uniq / len(rows)))
    print(f"{(' + '.join(cols) or '(없음)'):<26}{k:>3}{uniq:>7}"
          f"{uniq / len(rows):>8.2%}{cells:>11,}")
# 출력: 억제한 칸                       k     혼자      유일성      지워진 셀
# 출력: ----------------------------------------------------------
# 출력: (없음)                        1   3348  66.96%          0
# 출력: city                        1    865  17.30%      3,348
# 출력: city + role                 1      1   0.02%      6,696
# 출력: city + role + joined        2      0   0.00%     10,044

# %% [markdown]
# 네 줄을 읽어 보자.
#
# - `city` 한 칸만 빼면 유일성이 17.30%로 내려가는데 $k$는 여전히 1이다.
#   유일했던 사람들이 `('팀7', '*', '개발', 2019)` 같은 모양으로 모이면서
#   서로 짝을 찾아 주지만, 짝이 없는 865명은 여전히 혼자다.
#   **억제는 "유일한 사람을 없앤다"가 아니라 "유일한 사람들을 서로 섞는다"다.**
# - 두 칸을 빼면 혼자인 사람이 단 1명으로 줄어든다. 그런데도 $k$는 아직 1이다.
#   $k$는 최악값이라 한 명만 남아도 1이다. **유일성 0.02%와 $k=1$이 같이
#   나오는 이 줄이, 평균 지표만 보면 안 되는 이유다.**
# - 세 칸을 빼야 $k = 2$가 된다. 그 대가로 10,044개 셀이 사라졌고,
#   억제된 사람의 준식별자는 `team` 하나만 남았다. 정보가 거의 없는 행이다.
#
# **완전한 익명성의 값은 완전한 무정보다.** 34.2절의 "「지운다」의 네 수준"
# 표에서 완전 삭제가 만족하는 기준이 가장 *적었던* 것과 정확히 같은 모양이다.
# 어느 수준도 전부를 만족하지 않는다.

# %% [markdown]
# ## 6. 차분 프라이버시 — 잡음을 원칙화하면
#
# 위의 "잡음"은 임의적이다. ±2는 어디서 나온 숫자인가? ±3이면 얼마나 더
# 안전한가? 답할 근거가 없다. 차분 프라이버시(differential privacy)는 이
# 질문에 정의를 준다. 한 사람만 다른 인접 데이터셋 $D, D'$과 모든 결과
# 집합 $S$에 대해
#
# $$\Pr[\mathcal{M}(D) \in S] \le e^{\varepsilon}\,\Pr[\mathcal{M}(D') \in S]$$
#
# 를 만족하면 $\mathcal{M}$은 $\varepsilon$-차분 프라이버시를 만족한다.
# "내가 데이터에 있든 없든 결과 분포가 $e^{\varepsilon}$배 안에서 같다"는 뜻이다.
# 개수 세기 질의의 민감도는 $\Delta = 1$이므로
# $\mathrm{Lap}(\Delta/\varepsilon)$ 잡음을 더하면 되고, 그 표준편차는
# $\sqrt{2}\,\Delta/\varepsilon$이다.
#
# **잡음 크기가 데이터 크기와 무관하다**는 게 핵심이다. 그래서 큰 집계는
# 거의 안 다치고, 작은 집계 — 한두 명이 걸리는 위험한 질의 — 만 무의미해진다.

# %%
def laplace_sample(scale, r):
    u = r.random() - 0.5
    return -scale * (1 if u >= 0 else -1) * math.log(1 - 2 * abs(u))


def dp_error(rows, keys, eps, seed=SEED, trials=200):
    """개수 질의에 Laplace(1/eps). trials 회 반복해 평균 절대오차와 상대오차."""
    r = random.Random(seed)
    true = Counter(tuple(x[k] for k in keys) for x in rows)
    scale = 1.0 / eps
    errs = []
    for _ in range(trials):
        errs.append(statistics.fmean(
            abs(laplace_sample(scale, r)) for _ in true))
    err = statistics.fmean(errs)
    return err, err / statistics.fmean(true.values())


print("질의 A: 부서별 인원 (5개 칸, 참값 평균 1000명)")
print(f"{'ε':>7}{'잡음 SD':>10}{'집계 MAE':>10}{'상대오차':>10}  해석")
print("-" * 62)
EPS_ROWS = []
for eps in [0.01, 0.1, 0.5, 1.0, 5.0]:
    err, rel = dp_error(people, ["role"], eps)
    note = ("사실상 무의미" if rel > 0.2 else
            "집계 신뢰 가능" if rel < 0.02 else "주의해서 사용")
    EPS_ROWS.append((eps, math.sqrt(2) / eps, rel))
    print(f"{eps:>7}{math.sqrt(2) / eps:>10.1f}{err:>10.1f}{rel:>9.1%}  {note}")

print("\n질의 B: 준식별자 넷 조합별 인원 (4114개 칸, 참값 평균 1.2명)")
print(f"{'ε':>7}{'잡음 SD':>10}{'집계 MAE':>10}{'상대오차':>10}  해석")
print("-" * 62)
for eps in [0.1, 1.0, 5.0]:
    err, rel = dp_error(people, QI, eps)
    note = ("사실상 무의미" if rel > 0.2 else
            "집계 신뢰 가능" if rel < 0.02 else "주의해서 사용")
    print(f"{eps:>7}{math.sqrt(2) / eps:>10.1f}{err:>10.1f}{rel:>9.1%}  {note}")
# 출력: 질의 A: 부서별 인원 (5개 칸, 참값 평균 1000명)
# 출력:       ε     잡음 SD    집계 MAE      상대오차  해석
# 출력: --------------------------------------------------------------
# 출력:    0.01     141.4      97.5     9.7%  주의해서 사용
# 출력:     0.1      14.1       9.7     1.0%  집계 신뢰 가능
# 출력:     0.5       2.8       1.9     0.2%  집계 신뢰 가능
# 출력:     1.0       1.4       1.0     0.1%  집계 신뢰 가능
# 출력:     5.0       0.3       0.2     0.0%  집계 신뢰 가능
# 출력:
# 출력: 질의 B: 준식별자 넷 조합별 인원 (4114개 칸, 참값 평균 1.2명)
# 출력:       ε     잡음 SD    집계 MAE      상대오차  해석
# 출력: --------------------------------------------------------------
# 출력:     0.1      14.1      10.0   823.9%  사실상 무의미
# 출력:     1.0       1.4       1.0    82.4%  사실상 무의미
# 출력:     5.0       0.3       0.2    16.5%  주의해서 사용

# %% [markdown]
# 두 표가 같은 잡음을 서로 다르게 받아들인다. $\varepsilon = 1$에서
# 부서별 집계는 0.1% 틀리고, 준식별자 조합별 집계는 82% 틀린다.
# **같은 $\varepsilon$인데 결과가 다른 게 아니라, 위험이 다른 질의니까 그렇다.**
# 5000명을 5칸으로 나눈 질의는 개인을 노출하지 않고, 4114칸으로 나눈 질의는
# 곧 개인이다. 차분 프라이버시는 후자만 정확히 쓸모없게 만든다.
#
# 세 방법과의 관계는 이렇다.
#
# | | 임의적 잡음(3번) | 차분 프라이버시 |
# |---|---|---|
# | 잡음 크기 | ±2 — 근거 없음 | $\Delta/\varepsilon$ — 질의 민감도에서 유도 |
# | 보장 | 없음 (사후에 유일성 세 봐야 안다) | 수학적, 사전 보장 |
# | 반복 질의 | 여러 번 물으면 평균으로 잡음이 걷힌다 | 예산 $\sum \varepsilon_i$ 로 누적 관리 |
# | 어디를 흔들지 | 사람이 고른다 (틀리면 위 3번 줄) | 질의 구조가 정한다 |
# | 대상 | 저장된 값 | 질의 결과 (또는 값: local DP) |
#
# **차분 프라이버시는 3번 잡음의 원칙화된 버전이다.** 같은 도구를 쓰지만
# "얼마나 흔들어야 안전한가"와 "여러 번 물으면 어떻게 되나"에 답이 있다.
# 34장 키워드 표에서 차등 정보보호가 [사실상 표준]으로 올라와 있는 이유다.
#
# ## 7. 시각화

# %%
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "① 익명성 이득 — 유일성 비율 (낮을수록 안전)",
        "② 유용성 손실 — A 연도TVD · B 도시MAPE · C 부서MAE",
        "③ 억제 강도를 올릴 때 — 지운 셀 vs 유일성",
        "④ 차분 프라이버시 — 같은 ε, 다른 질의",
    ),
    vertical_spacing=0.18, horizontal_spacing=0.11,
)

SHORT = ["기준선", "(1)일반화", "(2)억제", "(3)잡음", "조합"]
COLORS = ["#8892a4", "#3f7fd0", "#d08a3f", "#c0504d", "#4d9b6a"]

# ① 유일성
fig.add_trace(go.Bar(
    x=SHORT, y=[r["uniq_rate"] * 100 for r in report],
    marker_color=COLORS, showlegend=False,
    text=[f"{r['uniq_rate']:.1%}" for r in report], textposition="outside",
), row=1, col=1)

# ② 세 유용성 지표. 단위가 달라 각자의 최대값을 100으로 정규화하고
#    막대 위에 실제 값을 적는다. 범례 대신 A/B/C 표기를 부제에 둔다.
def _norm(vals):
    m = max(vals) or 1.0
    return [v / m * 100 for v in vals]


for tag, key, color, fmt in [
    ("A", "year_tvd", "#3f7fd0", "{:.3f}"),
    ("B", "city_mape", "#d08a3f", "{:.0%}"),
    ("C", "role_mae", "#c0504d", "{:.3f}"),
]:
    vals = [r[key] for r in report]
    fig.add_trace(go.Bar(
        x=SHORT, y=_norm(vals), marker_color=color, showlegend=False,
        text=[f"{tag}={fmt.format(v)}" if v > 0 else "" for v in vals],
        textposition="outside", textfont_size=10, textangle=0, cliponaxis=False,
    ), row=1, col=2)

# ③ 억제 강도
fig.add_trace(go.Scatter(
    x=[c for _, c, _ in SUP_CURVE], y=[u * 100 for _, _, u in SUP_CURVE],
    mode="lines+markers+text",
    text=[f"{n}칸 억제" for n, _, _ in SUP_CURVE], textposition="top right",
    textfont_size=10,
    line=dict(color="#d08a3f", width=2), marker=dict(size=10),
    showlegend=False,
), row=2, col=1)

# ④ 차분 프라이버시. 범례 없이 선 끝에 이름을 붙인다.
for label, keys, color in [("부서별 (5칸)", ["role"], "#4d9b6a"),
                           ("준식별자 넷 (4114칸)", QI, "#c0504d")]:
    ys = [dp_error(people, keys, eps)[1] * 100 for eps, _, _ in EPS_ROWS]
    labels = [""] * len(ys)
    labels[0] = label
    fig.add_trace(go.Scatter(
        x=[e for e, _, _ in EPS_ROWS], y=ys, mode="lines+markers+text",
        text=labels, textposition="top right", textfont_size=10,
        line=dict(color=color, width=2), marker=dict(size=9),
        showlegend=False,
    ), row=2, col=2)

fig.update_yaxes(title_text="유일성 (%)", range=[0, 80], row=1, col=1)
fig.update_yaxes(title_text="각 지표 최대치 = 100", range=[0, 130], row=1, col=2)
fig.update_yaxes(title_text="유일성 (%)", range=[-8, 80], row=2, col=1)
fig.update_xaxes(title_text="지워진 셀 수", range=[-900, 11800], row=2, col=1)
fig.update_yaxes(title_text="상대오차 (%, 로그)", type="log",
                 range=[-2.1, 4.6], row=2, col=2)
fig.update_xaxes(title_text="ε (로그)", type="log", row=2, col=2,
                 tickvals=[0.01, 0.1, 0.5, 1.0, 5.0],
                 ticktext=["0.01", "0.1", "0.5", "1", "5"])

fig.update_layout(
    height=800, width=1150, barmode="group",
    title=dict(text="재식별 대응 셋 — 정확도를 내주고 익명성을 산다",
               x=0.03, y=0.975, font=dict(size=17)),
    template="plotly_white",
    font=dict(family="AppleGothic, Apple SD Gothic Neo, Malgun Gothic, sans-serif",
              size=12),
    margin=dict(t=100, b=60),
)

_show(fig)

try:
    _here = os.path.dirname(os.path.abspath(__file__))
except NameError:      # 노트북 커널에서는 __file__ 이 없다
    _here = os.getcwd()
fig.write_image(os.path.join(_here, "expy.png"), scale=2)
print("saved:", os.path.join(_here, "expy.png"))
# 출력: saved: <hint dir>/expy.png

# %% [markdown]
# ## 정리
#
# 1. **일반화**는 값의 해상도를 낮춘다. 준식별자에 직접 작용하므로 유일성이
#    크게 떨어진다(67.0% → 18.2%). 잃는 것은 세밀한 값이고, 그 손실은
#    "구간 단위로만 분석하겠다"고 물러설 때 지표에서 사라진 것처럼 보인다.
# 2. **억제**는 위험한 칸을 뺀다. 남은 값은 정확하지만 결측이 무작위가
#    아니라 편향을 만들고, 그 칸을 쓰는 집계는 크게 과소 계상된다(도시 −67%).
#    그리고 "혼자인 사람만"이 인구의 3분의 2일 수 있다.
# 3. **잡음**은 값을 흔든다. 준식별자가 아닌 칸을 흔들면 유용성만 내주고
#    익명성은 못 산다(표의 3번 줄). 어디를 흔들지가 전부다.
# 4. 셋은 **조합해야 하고 순서가 있다.** 일반화를 먼저 하면 억제가 손댈
#    사람이 67% → 18%로 줄면서 유일성은 오히려 4.2%까지 내려간다.
# 5. 그래도 $k$는 1이다. **평균적 익명성과 최악의 익명성은 다른 것이고**,
#    $k \ge 2$를 실제로 보장하려면 준식별자를 거의 다 지워야 한다.
# 6. **차분 프라이버시**는 3번 잡음의 원칙화다. 잡음 크기를 질의 민감도에서
#    유도하고, 반복 질의를 예산으로 관리한다.
# 7. 그리고 34장의 마지막 경고 — 그래프에서는 이 셋으로도 부족하다.
#    **관계 자체가 식별자**다. 속성을 전부 지워도 이웃의 «모양»이 유일하면
#    특정된다. 위 실험은 속성 표에 대한 것이고, 엣지 조합의 유일성에는
#    아직 정착한 해법이 없다.
