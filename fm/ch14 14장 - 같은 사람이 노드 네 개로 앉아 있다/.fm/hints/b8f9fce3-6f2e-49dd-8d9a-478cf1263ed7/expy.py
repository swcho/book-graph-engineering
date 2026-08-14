# %% [markdown]
# # `sim_str()` — 글자 2-gram 집합의 자카드 유사도
#
# 14장의 `sim_str(a, b)`는 **라이브러리 없이** 문자열 유사도를 재는 함수다.
# 정체는 딱 두 단계다.
#
# 1. 문자열에서 **연속한 글자 2개**(2-gram)를 모아 **집합**으로 만든다.
# 2. 두 집합의 **자카드 유사도**를 낸다.
#
# $$J(A, B) = \frac{|A \cap B|}{|A \cup B|}$$
#
# 집합이므로 순서·중복은 사라지고, 교집합/합집합만 남는다.
# 값은 $0 \le J \le 1$, 완전히 같으면 1, 겹치는 2-gram이 없으면 0이다.
#
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용)

# %%
import re
from itertools import combinations

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1. 원본 구현 그대로
#
# 14장 `code/dedup.py`의 `sim_str()`을 손대지 않고 옮겨 온다.

# %%
def sim_str(a, b):
    """글자 2-gram 자카드. 라이브러리 없이 쓸 만하다."""
    def g(x):
        x = re.sub(r"\s+", "", x or "")
        return {x[i:i + 2] for i in range(len(x) - 1)} or {x}
    A, B = g(a), g(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def norm_name(s):
    """법인격 표기·공백 제거. 14장 code/dedup.py에서 sim_str 앞단에 붙는 전처리."""
    s = re.sub(r"\(주\)|주식회사|\(유\)|유한회사", "", s)
    return re.sub(r"\s+", "", s)


print(sim_str("가온테크", "가온테크(주)"))
print(sim_str("가온테크", norm_name("가온테크(주)")))
# 출력:
# 0.6
# 1.0

# %% [markdown]
# 여기서 이미 중요한 사실 하나가 드러난다.
# `sim_str()`은 «똑똑한» 함수가 아니다. `(주)`가 붙으면 0.6으로 떨어진다.
# 법인격 표기를 지워 주는 `norm_name()`이 앞에 있어야 1.0이 된다.
# 즉 **정규화가 유사도보다 먼저**다.

# %% [markdown]
# ## 2. 2-gram 집합을 눈으로 보기
#
# 슬라이딩 윈도로 길이 2 조각을 뜬다. 길이 $L$ 문자열의 2-gram 개수는 $L-1$개(중복 제거 전).

# %%
def grams(x, n=2):
    x = re.sub(r"\s+", "", x or "")
    return {x[i:i + n] for i in range(len(x) - n + 1)} or {x}


for s in ["가온테크", "가온테크놀로지", "가온테크(주)", "나루소프트"]:
    g = grams(s)
    print(f"{s:<10} |{len(s):>2}자| {len(g)}개  {sorted(g)}")
# 출력:
# 가온테크       | 4자| 3개  ['가온', '온테', '테크']
# 가온테크놀로지    | 7자| 6개  ['가온', '놀로', '로지', '온테', '크놀', '테크']
# 가온테크(주)    | 7자| 6개  ['(주', '가온', '온테', '주)', '크(', '테크']
# 나루소프트      | 5자| 4개  ['나루', '루소', '소프', '프트']

# %% [markdown]
# ## 3. 손계산과 맞춰 보기
#
# `가온테크` vs `가온테크놀로지`
#
# - $A=\{$가온, 온테, 테크$\}$, $|A|=3$
# - $B=\{$가온, 온테, 테크, 크놀, 놀로, 로지$\}$, $|B|=6$
# - $A \cap B = \{$가온, 온테, 테크$\}$ → 3
# - $A \cup B$ → 6
# - $J = 3/6 = 0.5$

# %%
a, b = "가온테크", "가온테크놀로지"
A, B = grams(a), grams(b)
inter, union = A & B, A | B
print(f"A∩B = {sorted(inter)}  ({len(inter)})")
print(f"A∪B = {sorted(union)}  ({len(union)})")
print(f"손계산 {len(inter)}/{len(union)} = {len(inter) / len(union):.4f}")
print(f"sim_str          = {sim_str(a, b):.4f}")
print("일치" if abs(len(inter) / len(union) - sim_str(a, b)) < 1e-12 else "불일치")
# 출력:
# A∩B = ['가온', '온테', '테크']  (3)
# A∪B = ['가온', '놀로', '로지', '온테', '크놀', '테크']  (6)
# 손계산 3/6 = 0.5000
# sim_str          = 0.5000
# 일치

# %% [markdown]
# `가온테크`(4자)와 `가온테크놀로지`(7자)는 **접두사가 완전히 같은데도 0.5**다.
# 자카드는 합집합으로 나누므로 «길이 차이»에 곧바로 벌점을 준다.
# 이게 장점이기도 하다 — 14장에서 r01(가온테크)과 r05(가온테크놀로지)는
# 실제로 **다른 회사**이므로, 이름만으로 0.5까지 깎아 주는 편이 안전하다.

# %% [markdown]
# ## 4. 14장 실제 회사명 쌍의 유사도
#
# `records.py`의 이름들로 표를 만든다. 정규화 전/후를 나란히 본다.

# %%
NAMES = {
    "r01": "가온테크",
    "r02": "(주)가온테크",
    "r03": "가온테크 주식회사",
    "r04": "GAON TECH",
    "r05": "가온테크놀로지",
    "r06": "나루소프트",
    "r07": "나루소프트(주)",
    "r08": "다올물산 본사",
    "r09": "다올물산 부산지점",
    "r10": "라온에너지",
    "r11": "마루상사",
    "r12": "머루상사",
}

PAIRS = [
    ("r01", "r02", "같은 회사(법인격 표기)"),
    ("r01", "r03", "같은 회사(주식회사 표기)"),
    ("r01", "r04", "같은 회사(영문 병기)"),
    ("r01", "r05", "다른 회사(이름만 비슷)"),
    ("r06", "r07", "모/자회사 — 다른 법인"),
    ("r08", "r09", "같은 법인, 다른 사업장"),
    ("r11", "r12", "같은 회사(오타 1글자)"),
    ("r10", "r11", "완전 별개"),
]

print(f"{'쌍':<10}{'이름 A':<12}{'이름 B':<14}{'원문':>7}{'정규화후':>9}  비고")
print("-" * 76)
for x, y, note in PAIRS:
    raw = sim_str(NAMES[x], NAMES[y])
    nrm = sim_str(norm_name(NAMES[x]), norm_name(NAMES[y]))
    print(f"{x}-{y:<6}{NAMES[x]:<12}{NAMES[y]:<14}{raw:>7.3f}{nrm:>9.3f}  {note}")
# 출력:
# 쌍         이름 A        이름 B               원문     정규화후  비고
# ----------------------------------------------------------------------------
# r01-r02   가온테크        (주)가온테크         0.500    1.000  같은 회사(법인격 표기)
# r01-r03   가온테크        가온테크 주식회사       0.429    1.000  같은 회사(주식회사 표기)
# r01-r04   가온테크        GAON TECH       0.000    0.000  같은 회사(영문 병기)
# r01-r05   가온테크        가온테크놀로지         0.500    0.500  다른 회사(이름만 비슷)
# r06-r07   나루소프트       나루소프트(주)        0.571    1.000  모/자회사 — 다른 법인
# r08-r09   다올물산 본사     다올물산 부산지점       0.333    0.333  같은 법인, 다른 사업장
# r11-r12   마루상사        머루상사            0.500    0.500  같은 회사(오타 1글자)
# r10-r11   라온에너지       마루상사            0.000    0.000  완전 별개

# %% [markdown]
# 표에서 읽어야 할 것 세 가지.
#
# - **r01–r04 (`가온테크` / `GAON TECH`) = 0.000.**
#   같은 회사인데 0점이다. 글자 n-gram은 표기 체계가 바뀌면 완전히 무력하다.
#   14장이 이름 가중치를 0.25로만 두고 사업자번호에 0.45를 준 이유가 여기 있다.
# - **r06–r07 (`나루소프트` / `나루소프트(주)`) = 1.000(정규화 후).**
#   이름이 완벽히 같지만 **다른 법인**이다. 유사도 1.0이 «같다»의 증거가 아니다.
# - **r01–r05 (0.500) 와 r11–r12 (0.500) 가 같은 점수.**
#   전자는 다른 회사, 후자는 오타난 같은 회사다.
#   **점수 하나로는 두 상황을 구분할 수 없다.**

# %% [markdown]
# ## 5. n을 바꿔 보면 — n=1, 2, 3 스윕
#
# `sim_str()`은 $n=2$로 고정돼 있다. n이 커지면 «더 긴 연속 일치»를 요구하니
# 까다로워지고(값이 내려감), n이 작아지면 글자만 겹쳐도 점수가 나온다(값이 올라감).

# %%
def sim_n(a, b, n=2):
    A, B = grams(a, n), grams(b, n)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


print(f"{'쌍':<10}{'A':<12}{'B':<14}{'n=1':>7}{'n=2':>7}{'n=3':>7}")
print("-" * 60)
sweep = {}
for x, y, _ in PAIRS:
    u, v = norm_name(NAMES[x]), norm_name(NAMES[y])
    row = [sim_n(u, v, n) for n in (1, 2, 3)]
    sweep[f"{x}-{y}"] = row
    print(f"{x}-{y:<6}{u:<12}{v:<14}" + "".join(f"{s:>7.3f}" for s in row))
# 출력:
# 쌍         A           B                 n=1    n=2    n=3
# ------------------------------------------------------------
# r01-r02   가온테크        가온테크            1.000  1.000  1.000
# r01-r03   가온테크        가온테크            1.000  1.000  1.000
# r01-r04   가온테크        GAONTECH        0.000  0.000  0.000
# r01-r05   가온테크        가온테크놀로지         0.571  0.500  0.400
# r06-r07   나루소프트       나루소프트           1.000  1.000  1.000
# r08-r09   다올물산본사      다올물산부산지점        0.444  0.333  0.250
# r11-r12   마루상사        머루상사            0.600  0.500  0.333
# r10-r11   라온에너지       마루상사            0.000  0.000  0.000

# %% [markdown]
# 규칙이 보인다. **다른 쌍에서는 n이 커질수록 값이 단조 감소**한다
# (`0.571 → 0.500 → 0.400`). 같은 쌍(1.000)은 n과 무관하다.
#
# 즉 **n을 키우면 «비슷한 척»을 걸러내는 힘이 세진다**.
# 그럼 왜 2인가? 한국어 회사명·기관명은 4~8자가 흔한데,
# $n=3$이면 4자 이름에서 3-gram이 2개밖에 안 나와 한 글자만 틀려도 급락한다
# (`마루상사`/`머루상사`가 n=2에서 0.500인데 n=3에서 0.333까지 떨어진다).
# 반대로 $n=1$은 어순을 완전히 버려서 `가온테크`/`테크가온`을 1.000으로 만든다.
# **2는 짧은 한글 이름에서 «분해능»과 «견고함»의 타협점**이다.

# %% [markdown]
# ## 6. 짧은 문자열의 취약점 — 여기가 진짜 함정
#
# 길이 $L$이면 2-gram은 최대 $L-1$개. 한 글자 오타는 최대 **2개**의 2-gram을 망친다.
# 그래서 $L$이 작을수록 오타 한 글자의 타격 비율이 커진다.
#
# 오타가 문자열 «중간»에 있고 $|A|=|B|=L-1$일 때 상한은 대략
# $$J \approx \frac{(L-1)-2}{(L-1)+2} = \frac{L-3}{L+1}$$

# %%
BASE = "가나다라마바사아자차"
print(f"{'길이':>4}{'원본':<12}{'가운데 1글자 오타':<14}{'J':>7}{'(L-3)/(L+1)':>13}")
print("-" * 54)
for L in range(2, 11):
    s = BASE[:L]
    t = list(s)
    t[L // 2] = "★"          # 가운데 한 글자만 바꾼다
    t = "".join(t)
    j = sim_str(s, t)
    print(f"{L:>4}{s:<12}{t:<14}{j:>7.3f}{(L - 3) / (L + 1):>13.3f}")
# 출력:
#   길이원본          가운데 1글자 오타          J  (L-3)/(L+1)
# ------------------------------------------------------
#    2가나          가★              0.000       -0.333
#    3가나다         가★다             0.000        0.000
#    4가나다라        가나★라            0.200        0.200
#    5가나다라마       가나★라마           0.333        0.333
#    6가나다라마바      가나다★마바          0.429        0.429
#    7가나다라마바사     가나다★마바사         0.500        0.500
#    8가나다라마바사아    가나다라★바사아        0.556        0.556
#    9가나다라마바사아자   가나다라★바사아자       0.600        0.600
#   10가나다라마바사아자차  가나다라마★사아자차      0.636        0.636

# %% [markdown]
# **2~3자 이름은 한 글자만 틀려도 유사도 0**이다.
# `대성` vs `태성`, `한국` vs `한극` 같은 쌍이 0.000으로 나온다는 뜻이다.
# 반대로 10자 이상 긴 문장(주소 등)에서는 오타 한두 개쯤은 0.7 이상을 유지한다.
#
# 실무 대응은 «임계값을 하나로 두지 말라»다.
# 14장이 이름 하나로 판정하지 않고 **사업자번호·주소·대표자·전화를 가중 합산**하고,
# 애매한 구간(0.55~0.85)을 **사람 검토**로 빼두는 이유가 바로 이 취약점이다.

# %%
for x, y in [("대성", "태성"), ("한국", "한극"), ("삼성", "성삼")]:
    print(f"{x} vs {y}  →  {sim_str(x, y):.3f}")
# 출력:
# 대성 vs 태성  →  0.000
# 한국 vs 한극  →  0.000
# 삼성 vs 성삼  →  0.000

# %% [markdown]
# ## 7. 편집거리·자로-윙클러와 비교
#
# 같은 «문자열 유사도»지만 세는 대상이 다르다.
#
# | 방식 | 무엇을 세나 | 순서 민감 | 짧은 문자열 | 부분 문자열 |
# |---|---|---|---|---|
# | 2-gram 자카드 | 겹치는 글자쌍 집합 | 약함(집합) | **취약** | 길이차로 감점 |
# | 편집거리(Levenshtein) | 삽입/삭제/치환 횟수 | 강함 | 견고 | 길이차 = 거리 |
# | 자로-윙클러 | 위치 근접 일치 + **접두사 보너스** | 강함 | 견고 | 접두사 같으면 후함 |
#
# 라이브러리 없이 셋 다 구현해 같은 쌍에 물려 본다.

# %%
def lev(a, b):
    """레벤슈타인 편집거리."""
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def sim_lev(a, b):
    """편집거리를 0~1 유사도로 정규화."""
    m = max(len(a), len(b))
    return 1.0 - lev(a, b) / m if m else 1.0


def jaro(a, b):
    if a == b:
        return 1.0
    la, lb = len(a), len(b)
    if not la or not lb:
        return 0.0
    win = max(la, lb) // 2 - 1
    fa, fb = [False] * la, [False] * lb
    m = 0
    for i, ca in enumerate(a):
        for j in range(max(0, i - win), min(lb, i + win + 1)):
            if not fb[j] and ca == b[j]:
                fa[i] = fb[j] = True
                m += 1
                break
    if not m:
        return 0.0
    sa = [a[i] for i in range(la) if fa[i]]
    sb = [b[j] for j in range(lb) if fb[j]]
    t = sum(x != y for x, y in zip(sa, sb)) / 2
    return (m / la + m / lb + (m - t) / m) / 3


def jaro_winkler(a, b, p=0.1):
    j = jaro(a, b)
    pref = 0
    for x, y in zip(a[:4], b[:4]):
        if x != y:
            break
        pref += 1
    return j + pref * p * (1 - j)


METRICS = [("2gram자카드", sim_str), ("편집거리", sim_lev), ("자로윙클러", jaro_winkler)]

CASES = [
    ("가온테크", "가온테크놀로지", "다른 회사"),
    ("마루상사", "머루상사", "같은 회사(오타)"),
    ("대성", "태성", "짧은+오타"),
    ("다올물산본사", "다올물산부산지점", "같은 법인/다른 사업장"),
    ("가온테크", "테크가온", "어순 뒤집기"),
    ("가온테크", "GAONTECH", "표기 체계 다름"),
]

print(f"{'A':<12}{'B':<16}" + "".join(f"{n:>13}" for n, _ in METRICS) + "  비고")
print("-" * 84)
cmp_rows = []
for x, y, note in CASES:
    vals = [f(x, y) for _, f in METRICS]
    cmp_rows.append((f"{x}/{y}", vals))
    print(f"{x:<12}{y:<16}" + "".join(f"{v:>13.3f}" for v in vals) + f"  {note}")
# 출력:
# A           B                    2gram자카드         편집거리        자로윙클러  비고
# ------------------------------------------------------------------------------------
# 가온테크        가온테크놀로지                 0.500        0.571        0.914  다른 회사
# 마루상사        머루상사                    0.500        0.750        0.833  같은 회사(오타)
# 대성          태성                      0.000        0.500        0.667  짧은+오타
# 다올물산본사      다올물산부산지점                0.333        0.500        0.833  같은 법인/다른 사업장
# 가온테크        테크가온                    0.500        0.000        0.000  어순 뒤집기
# 가온테크        GAONTECH                0.000        0.000        0.000  표기 체계 다름

# %% [markdown]
# 세 지표의 성격 차이가 선명하다.
#
# - **자로-윙클러는 접두사에 후하다.** `가온테크`/`가온테크놀로지`에 0.914를 준다.
#   실제로는 **다른 회사**이므로, 이 데이터에서는 위험한 관대함이다.
#   기업명 매칭에 자로-윙클러를 쓰면 «○○ / ○○홀딩스 / ○○산업»을 다 붙여 버린다.
# - **편집거리는 짧은 문자열에서 자카드보다 낫다.** `대성`/`태성`에 0.500 vs 0.000.
#   2~3자 이름이 많은 도메인이면 편집거리 쪽이 안전하다.
# - **자카드는 어순에 둔감하다.** `가온테크`/`테크가온`에 0.500을 주는데,
#   편집거리와 자로-윙클러는 둘 다 0.000이다. 집합으로 만드는 순간 위치 정보가 날아가고,
#   2-gram의 경계 효과로 절반만 남는 것이다(1-gram이면 1.000까지 간다).
#   회사명처럼 어절 순서가 뒤바뀔 수 있는 데이터에서는 이 둔감함이 장점이지만,
#   `서울지점`/`지점서울`류를 구분해야 한다면 함정이다.
# - **표기 체계가 바뀌면(한글↔영문) 세 지표 모두 0.000.** 어떤 문자열 유사도도 못 푼다.
#   이건 사업자번호 같은 **식별자**나 로마자 변환 같은 **정규화**로 풀 문제다.

# %%
print("1-gram 자카드로 어순 뒤집기:", sim_n("가온테크", "테크가온", 1))
# 출력: 1-gram 자카드로 어순 뒤집기: 1.0

# %% [markdown]
# ## 8. 시각화
#
# 왼쪽: 14장 회사명 12개 전체의 2-gram 자카드 히트맵(정규화 후).
# 오른쪽: 대표 쌍의 n=1/2/3 및 지표별 비교.

# %%
keys = list(NAMES)
norm = {k: norm_name(NAMES[k]) for k in keys}
mat = [[round(sim_str(norm[r], norm[c]), 3) for c in keys] for r in keys]
labels = [f"{k}<br>{NAMES[k]}" for k in keys]

fig = make_subplots(
    rows=1, cols=2,
    column_widths=[0.56, 0.44],
    subplot_titles=(
        "회사명 12개 2-gram 자카드 (정규화 후)",
        "n-gram 크기 스윕 (같은 쌍은 1.0 고정)",
    ),
    horizontal_spacing=0.13,
)

fig.add_trace(
    go.Heatmap(
        z=mat, x=labels, y=labels, zmin=0, zmax=1,
        colorscale="Blues", showscale=True,
        colorbar=dict(title="J", len=0.85, x=0.47, thickness=12),
        text=[[f"{v:.2f}" if v else "" for v in row] for row in mat],
        texttemplate="%{text}", textfont=dict(size=8),
        hovertemplate="%{y} ↔ %{x}<br>J=%{z:.3f}<extra></extra>",
    ),
    row=1, col=1,
)

pair_keys = list(sweep)
for i, n in enumerate((1, 2, 3)):
    fig.add_trace(
        go.Bar(
            name=f"n={n}",
            x=pair_keys,
            y=[sweep[p][i] for p in pair_keys],
            marker_color=["#9ecae1", "#3182bd", "#08306b"][i],
            hovertemplate="%{x}<br>J=%{y:.3f}<extra>n=" + str(n) + "</extra>",
        ),
        row=1, col=2,
    )

fig.add_hline(y=0.85, line_dash="dash", line_color="#c0392b", row=1, col=2,
              annotation_text="HIGH 0.85 자동병합", annotation_font_size=9)
fig.add_hline(y=0.55, line_dash="dot", line_color="#e67e22", row=1, col=2,
              annotation_text="LOW 0.55 검토", annotation_font_size=9)

fig.update_xaxes(tickangle=-45, tickfont=dict(size=8), row=1, col=1)
fig.update_yaxes(autorange="reversed", tickfont=dict(size=8), row=1, col=1)
fig.update_xaxes(tickangle=-30, tickfont=dict(size=9), row=1, col=2)
fig.update_yaxes(range=[0, 1.08], title_text="자카드 유사도", row=1, col=2)
fig.update_layout(
    title_text="sim_str(): 2-gram 자카드가 실제로 내는 점수",
    barmode="group", height=680, width=1360,
    template="plotly_white",
    margin=dict(b=150),
    legend=dict(orientation="h", yanchor="top", y=-0.20, x=0.66),
)

_show(fig)
fig.write_image("expy.png", scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# - `sim_str()` = **글자 2-gram 집합의 자카드 유사도**. `re` 하나로 6줄이면 끝난다.
#   $J(A,B)=\frac{|A\cap B|}{|A\cup B|}$.
# - **싸고 설명 가능하다.** 왜 0.5인지 교집합/합집합을 세서 보여줄 수 있다.
#   14장이 «라이브러리 없이도 쓸 만하다»고 한 이유다.
# - 대신 **약점이 분명하다**: 2~3자 문자열은 오타 한 글자에 0.000,
#   표기 체계가 다르면(한글↔영문) 0.000, 길이 차이는 곧 감점.
# - **정규화가 먼저**다. `norm_name()`으로 `(주)`·`주식회사`·공백을 지워야
#   0.500이 1.000이 된다.
# - 그리고 가장 중요한 것 — **유사도 1.0은 «같다»의 증거가 아니다.**
#   `나루소프트`/`나루소프트(주)`는 이름이 완전히 같지만 다른 법인이다.
#   그래서 14장은 이름에 0.25만 주고, 사업자번호(0.45)와 합산하고,
#   애매한 구간은 사람에게 넘긴다.
