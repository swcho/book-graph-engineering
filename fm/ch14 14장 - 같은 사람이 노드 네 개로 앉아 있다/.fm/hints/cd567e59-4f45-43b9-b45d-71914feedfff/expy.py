# %% [markdown]
# # `ex2_scoring.py`의 필드 가중치는 어떻게 배분되는가?
#
# 답부터 적어 둔다.
#
# | 필드 | 가중치 $w_i$ | 비교 방식 | 비중 |
# |---|---|---|---|
# | 사업자번호 | **0.45** | `exact` | 45% |
# | 이름 | **0.25** | `fuzzy` (2-gram 자카드) | 25% |
# | 주소 | **0.15** | `fuzzy` (2-gram 자카드) | 15% |
# | 대표자 | **0.10** | `exact` | 10% |
# | 전화 | **0.05** | `exact` | 5% |
#
# 합이 정확히 $1.00$이다. 그리고 이 배분에는 두 개의 설계 의도가 들어 있다.
#
# 1. **식별자에 몰아준다.** 사업자번호 하나가 나머지 네 필드(0.55)와 거의 맞먹는다.
#    법인을 유일하게 지목하는 값이니까.
# 2. **흔들리는 필드는 `fuzzy`, 딱 떨어지는 필드는 `exact`.**
#    이름·주소는 표기가 흔들리므로 유사도를 쓰고, 번호·사람 이름은 같으면 1 아니면 0이다.
#
# 여기서는 `ex2_scoring.py`의 `FIELDS`와 `score()`를 그대로 재현해서
# 어느 필드가 실제 점수의 몇 점을 만들어 냈는지 분해해 본다.

# %%
# 필요 패키지: plotly, kaleido, numpy (시각화/스윕 셀에서만 사용. 그 외는 표준 라이브러리만)
import re
from itertools import combinations


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# records.py 의 데이터 (id, 이름, 사업자번호, 주소, 대표자, 전화)
RECORDS = [
    ("r01", "가온테크",         "123-45-67890", "서울 강남구 테헤란로 1",   "김하늘", "02-1234-5678"),
    ("r02", "(주)가온테크",      "123-45-67890", "서울 강남구 테헤란로 1",   "김하늘", "02-1234-5678"),
    ("r03", "가온테크 주식회사",  "",             "서울 강남구 테헤란로 1길", "김하늘", "021234-5678"),
    ("r04", "GAON TECH",       "123-45-67890", "",                       "",       ""),
    ("r05", "가온테크놀로지",    "999-88-77777", "부산 해운대구 센텀로 9",   "박서준", "051-999-8877"),
    ("r06", "나루소프트",        "222-33-44444", "서울 마포구 월드컵로 2",   "이서연", "02-2222-3333"),
    ("r07", "나루소프트(주)",    "555-66-77777", "서울 마포구 월드컵로 2",   "이서연", "02-2222-3333"),
    ("r08", "다올물산 본사",     "333-44-55555", "인천 연수구 송도로 3",    "최민준", "032-333-4444"),
    ("r09", "다올물산 부산지점",  "333-44-55555", "부산 사하구 낙동로 8",    "정우진", "051-333-4444"),
    ("r10", "라온에너지",        "444-55-66666", "대전 유성구 대덕대로 4",   "한지우", "042-444-5555"),
    ("r11", "마루상사",         "666-77-88888", "광주 서구 상무로 6",      "오세훈", "062-666-7777"),
    ("r12", "머루상사",         "666-77-88888", "광주 서구 상무로 6",      "오세훈", "062-666-7777"),
]
TRUTH = {frozenset(["r01", "r02", "r03", "r04"]), frozenset(["r11", "r12"])}
BY_ID = {r[0]: r for r in RECORDS}

print(f"레코드 {len(RECORDS)}개, 정답 군집 {len(TRUTH)}개")
# 출력: 레코드 12개, 정답 군집 2개


# %% [markdown]
# ## 1. 정규화 함수와 유사도
#
# `fuzzy` 필드가 쓰는 유사도는 글자 2-gram 자카드다. 라이브러리 없이 쓸 만하다.
#
# $$\mathrm{sim}(a,b) = \frac{|G_2(a) \cap G_2(b)|}{|G_2(a) \cup G_2(b)|}$$
#
# 이름은 비교 전에 법인격 표기(`(주)`, `주식회사`, …)와 공백을 걷어 낸다.
# 그래서 「가온테크」와 「(주)가온테크」는 `fuzzy` 필드인데도 유사도 $1.0$이 나온다.
# 정규화가 `fuzzy` 가중치 0.25를 «제대로 쓰이게» 만드는 전처리다.

# %%
def norm_name(s):
    s = re.sub(r"\(주\)|주식회사|\(유\)|유한회사", "", s)
    return re.sub(r"\s+", "", s)


def norm_phone(s):
    return re.sub(r"\D", "", s or "")


def sim_str(a, b):
    """글자 2-gram 자카드."""
    def g(x):
        x = re.sub(r"\s+", "", x or "")
        return {x[i:i + 2] for i in range(len(x) - 1)} or {x}
    A, B = g(a), g(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


for a, b in [("가온테크", "(주)가온테크"), ("가온테크", "가온테크 주식회사"),
             ("가온테크", "GAON TECH"), ("가온테크", "가온테크놀로지"),
             ("마루상사", "머루상사")]:
    print(f"{a!r:<12} vs {b!r:<18} 원문 {sim_str(a, b):.3f}  "
          f"정규화 {sim_str(norm_name(a), norm_name(b)):.3f}")
# 출력: '가온테크'       vs '(주)가온테크'          원문 0.500  정규화 1.000
# 출력: '가온테크'       vs '가온테크 주식회사'        원문 0.429  정규화 1.000
# 출력: '가온테크'       vs 'GAON TECH'        원문 0.000  정규화 0.000
# 출력: '가온테크'       vs '가온테크놀로지'          원문 0.500  정규화 0.500
# 출력: '마루상사'       vs '머루상사'             원문 0.500  정규화 0.500


# %% [markdown]
# ## 2. `FIELDS` — 가중치 배분 그 자체
#
# 배분표가 곧 코드다. 튜플 하나에 (이름, 추출 함수, 가중치, 비교 방식)이 들어 있다.

# %%
FIELDS = [
    # (이름, 추출 함수, 가중치, 비교 방식)
    ("사업자번호", lambda r: r[2], 0.45, "exact"),
    ("이름",      lambda r: norm_name(r[1]), 0.25, "fuzzy"),
    ("주소",      lambda r: r[3], 0.15, "fuzzy"),
    ("대표자",    lambda r: r[4], 0.10, "exact"),
    ("전화",      lambda r: norm_phone(r[5]), 0.05, "exact"),
]

print(f"{'필드':<10} {'가중치':>6} {'비중':>7}  방식")
print("-" * 38)
_total_w = sum(w for _, _, w, _ in FIELDS)
for name, _, w, mode in FIELDS:
    print(f"{name:<10} {w:>6.2f} {w / _total_w * 100:>6.0f}%  {mode}")
print("-" * 38)
print(f"{'합':<10} {_total_w:>6.2f} {100:>6.0f}%")
print(f"\n사업자번호(0.45) vs 나머지 넷({_total_w - 0.45:.2f}) — 거의 맞먹는다")
print(f"exact 계열 합 {0.45 + 0.10 + 0.05:.2f} / fuzzy 계열 합 {0.25 + 0.15:.2f}")
# 출력: 필드            가중치      비중  방식
# 출력: --------------------------------------
# 출력: 사업자번호        0.45     45%  exact
# 출력: 이름           0.25     25%  fuzzy
# 출력: 주소           0.15     15%  fuzzy
# 출력: 대표자          0.10     10%  exact
# 출력: 전화           0.05      5%  exact
# 출력: --------------------------------------
# 출력: 합            1.00    100%
# 출력:
# 출력: 사업자번호(0.45) vs 나머지 넷(0.55) — 거의 맞먹는다
# 출력: exact 계열 합 0.60 / fuzzy 계열 합 0.40


# %% [markdown]
# ## 3. `score()` — 빈 값은 «모름»으로 빼고 나눈다
#
# 가중치 합이 1이라서 그냥 더하면 될 것 같지만, `score()`는 굳이 한 번 더 나눈다.
#
# $$s(a,b) = \frac{\sum_{i \in U} w_i \cdot \mathrm{sim}_i(a,b)}{\sum_{i \in U} w_i},
# \qquad U = \{\,i : a_i \neq \varnothing \ \wedge\ b_i \neq \varnothing\,\}$$
#
# 한쪽이라도 비어 있는 필드는 «모름»이라 분자에서도 분모에서도 빠진다.
# 이게 핵심이다. 빈 값을 «다르다(0점)»로 세면 정보가 없는 레코드가 부당하게
# 낮은 점수를 받는다. 그래서 분모 $\sum_{i \in U} w_i$가 쌍마다 달라진다.
#
# 부수 효과가 하나 더 있다. 분모로 나누므로 **가중치의 절대 크기는 무의미하고
# 비율만 의미가 있다.** $w \to c\,w$로 전부 스케일해도 점수는 그대로다.
# 「합을 1로 맞춘다」는 건 사람이 읽기 좋게 하는 관례일 뿐이다.

# %%
def score(a, b, fields=FIELDS):
    total = 0.0
    used = 0.0
    detail = []
    for name, get, w, mode in fields:
        x, y = get(a), get(b)
        if not x or not y:          # 한쪽이 비면 그 항목은 «모름»으로 빼둔다
            detail.append((name, None, w))
            continue
        s = 1.0 if (mode == "exact" and x == y) else (
            0.0 if mode == "exact" else sim_str(x, y))
        total += w * s
        used += w
        detail.append((name, s, w))
    return (total / used if used else 0.0), detail


HIGH, LOW = 0.85, 0.55

# 가중치를 3배로 키워도 점수는 동일하다 — 정규화가 스케일을 먹는다
SCALED = [(n, g, w * 3, m) for n, g, w, m in FIELDS]
for a, b in [("r01", "r02"), ("r01", "r04"), ("r06", "r07")]:
    s1, _ = score(BY_ID[a], BY_ID[b])
    s2, _ = score(BY_ID[a], BY_ID[b], SCALED)
    print(f"{a}-{b}  원본 {s1:.3f}  ×3 {s2:.3f}  같은가: {abs(s1 - s2) < 1e-12}")
# 출력: r01-r02  원본 1.000  ×3 1.000  같은가: True
# 출력: r01-r04  원본 0.643  ×3 0.643  같은가: True
# 출력: r06-r07  원본 0.550  ×3 0.550  같은가: True


# %% [markdown]
# ## 4. 쌍별 분해 — 어느 필드가 몇 점을 냈나
#
# 필드 $i$가 최종 점수에 기여한 몫은
#
# $$c_i = \frac{w_i \cdot \mathrm{sim}_i}{\sum_{j \in U} w_j}$$
#
# 이고 $\sum_i c_i = s$다. 아래 표에서 `기여` 열이 $c_i$다.

# %%
def breakdown(a, b):
    ra, rb = BY_ID[a], BY_ID[b]
    s, detail = score(ra, rb)
    used = sum(w for _, sim, w in detail if sim is not None)
    print(f"◆ {a}-{b}   최종 {s:.3f}   (분모 Σw = {used:.2f})")
    print(f"   {'필드':<10} {'w':>5} {'sim':>6} {'기여':>7}   비고")
    for name, sim, w in detail:
        if sim is None:
            print(f"   {name:<10} {w:>5.2f} {'—':>6} {'—':>7}   모름(제외)")
        else:
            print(f"   {name:<10} {w:>5.2f} {sim:>6.3f} {w * sim / used:>7.3f}")
    print()
    return s


for pair in [("r01", "r02"), ("r03", "r04"), ("r01", "r04"),
             ("r06", "r07"), ("r08", "r09"), ("r11", "r12")]:
    breakdown(*pair)
# 출력: ◆ r01-r02   최종 1.000   (분모 Σw = 1.00)
# 출력:    필드             w    sim      기여   비고
# 출력:    사업자번호       0.45  1.000   0.450
# 출력:    이름          0.25  1.000   0.250
# 출력:    주소          0.15  1.000   0.150
# 출력:    대표자         0.10  1.000   0.100
# 출력:    전화          0.05  1.000   0.050
# 출력:
# 출력: ◆ r03-r04   최종 0.000   (분모 Σw = 0.25)
# 출력:    필드             w    sim      기여   비고
# 출력:    사업자번호       0.45      —       —   모름(제외)
# 출력:    이름          0.25  0.000   0.000
# 출력:    주소          0.15      —       —   모름(제외)
# 출력:    대표자         0.10      —       —   모름(제외)
# 출력:    전화          0.05      —       —   모름(제외)
# 출력:
# 출력: ◆ r01-r04   최종 0.643   (분모 Σw = 0.70)
# 출력:    필드             w    sim      기여   비고
# 출력:    사업자번호       0.45  1.000   0.643
# 출력:    이름          0.25  0.000   0.000
# 출력:    주소          0.15      —       —   모름(제외)
# 출력:    대표자         0.10      —       —   모름(제외)
# 출력:    전화          0.05      —       —   모름(제외)
# 출력:
# 출력: ◆ r06-r07   최종 0.550   (분모 Σw = 1.00)
# 출력:    필드             w    sim      기여   비고
# 출력:    사업자번호       0.45  0.000   0.000
# 출력:    이름          0.25  1.000   0.250
# 출력:    주소          0.15  1.000   0.150
# 출력:    대표자         0.10  1.000   0.100
# 출력:    전화          0.05  1.000   0.050
# 출력:
# 출력: ◆ r08-r09   최종 0.533   (분모 Σw = 1.00)
# 출력:    필드             w    sim      기여   비고
# 출력:    사업자번호       0.45  1.000   0.450
# 출력:    이름          0.25  0.333   0.083
# 출력:    주소          0.15  0.000   0.000
# 출력:    대표자         0.10  0.000   0.000
# 출력:    전화          0.05  0.000   0.000
# 출력:
# 출력: ◆ r11-r12   최종 0.875   (분모 Σw = 1.00)
# 출력:    필드             w    sim      기여   비고
# 출력:    사업자번호       0.45  1.000   0.450
# 출력:    이름          0.25  0.500   0.125
# 출력:    주소          0.15  1.000   0.150
# 출력:    대표자         0.10  1.000   0.100
# 출력:    전화          0.05  1.000   0.050


# %% [markdown]
# 읽을 거리가 여기 다 있다.
#
# - **r01-r02** ($1.000$): 다섯 필드가 전부 만점. 「가온테크」/「(주)가온테크」는
#   정규화 덕에 `fuzzy` 필드도 1.0이 된다. 자동 병합.
# - **r01-r04** ($0.643$): 분모가 $0.70$으로 쪼그라들었다. 주소·대표자·전화가 비었으니까.
#   사업자번호 하나가 $0.45/0.70 = 0.643$을 만들고 이름은 「GAON TECH」라 0점.
#   그래서 애매 구간($0.55 \le s < 0.85$)에 떨어져 **사람에게 간다.**
#   가중치 0.45는 «식별자 하나만으로는 자동 병합에 못 닿는다»는 위치에 놓여 있다.
# - **r03-r04** ($0.000$): 겹치는 필드가 이름 하나뿐이라 분모가 $0.25$. 유사도 0이니 총점 0.
#   같은 회사인데도 이 쌍만 보면 아무 근거가 없다. 이행성이 필요한 이유다.
# - **r06-r07** ($0.550$): 사업자번호가 다르니 0.45가 통째로 죽고, 나머지 넷이 전부 만점.
#   $0.25+0.15+0.10+0.05 = 0.55$로 딱 `LOW` 경계다. 모회사-자회사, 저자가 잘못 병합했던 쌍.
#   **나머지 넷이 다 같아도 자동 병합에 못 닿는다** — 이게 0.45를 크게 준 보상이다.
# - **r08-r09** ($0.533$): 같은 법인의 본사/지점. 사업자번호가 0.45를 채우지만
#   주소·대표자·전화가 전부 달라 `LOW` 아래로 내려가 후보에서 빠진다.
# - **r11-r12** ($0.875$): 「마루상사」/「머루상사」 오타로 이름 기여가 $0.125$뿐인데도
#   나머지가 만점이라 `HIGH`를 넘겨 자동 병합된다.

# %%
# 전체 쌍 판정 — LOW 이상만 출력
def run(fields=FIELDS, high=HIGH, low=LOW, verbose=True):
    auto, review = [], []
    for a, b in combinations(sorted(BY_ID), 2):
        s, _ = score(BY_ID[a], BY_ID[b], fields)
        if s >= low:
            (auto if s >= high else review).append((a, b, s))
            if verbose:
                print(f"{a}-{b:<7} {s:>6.3f}  {'자동 병합' if s >= high else '사람 검토'}")
    return auto, review


auto, review = run()
print(f"\n자동 {len(auto)}쌍, 검토 {len(review)}쌍 "
      f"→ 12개 레코드(66쌍) 중 사람이 볼 것은 {len(review)}쌍뿐")
# 출력: r01-r02      1.000  자동 병합
# 출력: r01-r03      0.973  자동 병합
# 출력: r01-r04      0.643  사람 검토
# 출력: r02-r03      0.973  자동 병합
# 출력: r02-r04      0.643  사람 검토
# 출력: r06-r07      0.550  사람 검토
# 출력: r11-r12      0.875  자동 병합
# 출력:
# 출력: 자동 4쌍, 검토 3쌍 → 12개 레코드(66쌍) 중 사람이 볼 것은 3쌍뿐


# %% [markdown]
# ## 5. 민감도 — 사업자번호를 $0.45 \to 0.20$으로 낮추면
#
# 가중치는 취향이 아니다. 순위와 임계 통과 여부를 직접 바꾼다.
# 사업자번호의 비중만 줄이고 나머지는 그대로 두면 어떻게 되는지 본다.
# (정규화가 있으니 다른 값을 손보지 않아도 «상대 비중»만 내려간다.)

# %%
def variant(w_bizno):
    out = []
    for name, get, w, mode in FIELDS:
        out.append((name, get, w_bizno if name == "사업자번호" else w, mode))
    return out


PAIRS = [("r01", "r02"), ("r01", "r03"), ("r01", "r04"),
         ("r06", "r07"), ("r08", "r09"), ("r11", "r12")]
LOW_W = variant(0.20)


def verdict(s):
    return "자동 병합" if s >= HIGH else ("사람 검토" if s >= LOW else "무시")


print(f"{'쌍':<9} {'w=0.45':>8} {'판정':<9} {'w=0.20':>8} {'판정':<9} 변화")
print("-" * 62)
for a, b in PAIRS:
    s1, _ = score(BY_ID[a], BY_ID[b])
    s2, _ = score(BY_ID[a], BY_ID[b], LOW_W)
    v1, v2 = verdict(s1), verdict(s2)
    mark = "" if v1 == v2 else f"→ {v1} 에서 {v2} 로"
    print(f"{a}-{b:<5} {s1:>8.3f} {v1:<9} {s2:>8.3f} {v2:<9} {mark}")
# 출력: 쌍           w=0.45 판정          w=0.20 판정        변화
# 출력: --------------------------------------------------------------
# 출력: r01-r02      1.000 자동 병합        1.000 자동 병합
# 출력: r01-r03      0.973 자동 병합        0.973 자동 병합
# 출력: r01-r04      0.643 사람 검토        0.444 무시        → 사람 검토 에서 무시 로
# 출력: r06-r07      0.550 사람 검토        0.733 사람 검토
# 출력: r08-r09      0.533 무시           0.378 무시
# 출력: r11-r12      0.875 자동 병합        0.833 사람 검토      → 자동 병합 에서 사람 검토 로


# %%
# 순위가 어떻게 뒤집히는지 (상위 6쌍)
def ranking(fields):
    rows = []
    for a, b in combinations(sorted(BY_ID), 2):
        s, _ = score(BY_ID[a], BY_ID[b], fields)
        rows.append((f"{a}-{b}", s))
    rows.sort(key=lambda t: -t[1])
    return rows[:6]


r_base, r_low = ranking(FIELDS), ranking(LOW_W)
print(f"{'순위':<5} {'w=0.45':<20} {'w=0.20':<20}")
for i, (x, y) in enumerate(zip(r_base, r_low), 1):
    print(f"{i:<5} {x[0]} {x[1]:.3f}         {y[0]} {y[1]:.3f}")
# 출력: 순위    w=0.45               w=0.20
# 출력: 1     r01-r02 1.000         r01-r02 1.000
# 출력: 2     r01-r03 0.973         r01-r03 0.973
# 출력: 3     r02-r03 0.973         r02-r03 0.973
# 출력: 4     r11-r12 0.875         r11-r12 0.833
# 출력: 5     r01-r04 0.643         r06-r07 0.733
# 출력: 6     r02-r04 0.643         r01-r04 0.444


# %% [markdown]
# 세 가지가 동시에 벌어진다.
#
# - **r06-r07이 5위로 올라온다**: $0.550 \to 0.733$. 사업자번호가 다르다는
#   «가장 강한 반대 증거»의 힘이 빠지니, 주소·대표자·전화가 같은 모회사-자회사 쌍이
#   위로 올라온다. 더 낮추면 자동 병합에 닿는다. 저자가 실제로 저지른 그 사고다.
# - **r11-r12가 자동 병합에서 떨어진다**: $0.875 \to 0.833$. 같은 회사인데 오타 하나 때문에
#   사람 손으로 넘어간다. 놓치는 쪽 비용이다.
# - **r01-r04가 목록에서 빠진다**: $0.643 \to 0.444$로 `LOW` 아래. 사업자번호밖에 없는
#   레코드는 사업자번호의 비중이 곧 자기 점수다. 후보에서 탈락하면 영영 못 만난다.

# %%
# 사업자번호 가중치를 훑으면서 각 쌍의 점수 궤적을 본다
import numpy as np

W_GRID = np.round(np.arange(0.02, 0.81, 0.01), 2)
TRACK = [("r01", "r04"), ("r06", "r07"), ("r08", "r09"), ("r11", "r12"), ("r01", "r03")]
curves = {}
for a, b in TRACK:
    curves[f"{a}-{b}"] = [score(BY_ID[a], BY_ID[b], variant(w))[0] for w in W_GRID]

print(f"{'w':>5} {'r06-r07':>8} {'r11-r12':>8} {'r01-r04':>8} {'r08-r09':>8}  {'자동':>4} {'검토':>4}")
print("-" * 56)
for w in [0.02, 0.05, 0.09, 0.10, 0.20, 0.30, 0.45, 0.60, 0.80]:
    fv = variant(w)
    a_, r_ = run(fv, verbose=False)
    row = [score(BY_ID[x], BY_ID[y], fv)[0] for x, y in
           [("r06", "r07"), ("r11", "r12"), ("r01", "r04"), ("r08", "r09")]]
    print(f"{w:>5.2f} " + " ".join(f"{v:>8.3f}" for v in row) +
          f"  {len(a_):>4} {len(r_):>4}")

# r06-r07 이 HIGH 를 넘겨 «오병합»되기 시작하는 지점
bad = [w for w in W_GRID if score(BY_ID["r06"], BY_ID["r07"], variant(w))[0] >= HIGH]
print(f"\nr06-r07(다른 법인)이 자동 병합되는 구간: w <= {max(bad):.2f}")
# 출력:     w  r06-r07  r11-r12  r01-r04  r08-r09    자동   검토
# 출력: --------------------------------------------------------
# 출력:  0.02    0.965    0.781    0.074    0.181     4    1
# 출력:  0.05    0.917    0.792    0.167    0.222     4    1
# 출력:  0.09    0.859    0.805    0.265    0.271     4    1
# 출력:  0.10    0.846    0.808    0.286    0.282     3    2
# 출력:  0.20    0.733    0.833    0.444    0.378     3    2
# 출력:  0.30    0.647    0.853    0.545    0.451     4    1
# 출력:  0.45    0.550    0.875    0.643    0.533     4    3
# 출력:  0.60    0.478    0.891    0.706    0.594     4    3
# 출력:  0.80    0.407    0.907    0.762    0.654     4    3
# 출력:
# 출력: r06-r07(다른 법인)이 자동 병합되는 구간: w <= 0.09
#
# 표를 세로로 읽으면 r06-r07(다른 법인)은 w가 커질수록 «내려가고»,
# r11-r12·r01-r04(같은 회사)는 «올라간다». 두 방향이 동시에 좋아지는 구간이
# 0.45 근처다. w를 0.09 아래로 내리면 다른 법인이 자동 병합되고,
# w를 0.10~0.30 구간에 두면 r11-r12나 r01-r04가 임계 아래로 떨어진다.


# %% [markdown]
# ## 6. 시각화
#
# 왼쪽은 쌍별 기여도 누적 막대($c_i$의 합이 최종 점수). 오른쪽은 사업자번호
# 가중치를 훑었을 때의 점수 궤적과 두 임계선이다. 오른쪽 그림에서
# r06-r07(다른 법인)과 r11-r12(같은 회사)의 곡선이 서로 반대로 움직이는 게 보인다.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PAL = {"사업자번호": "#2563eb", "이름": "#059669", "주소": "#d97706",
       "대표자": "#7c3aed", "전화": "#dc2626"}

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=("필드별 기여도 c_i (합 = 최종 점수)",
                    "사업자번호 가중치 민감도"),
    horizontal_spacing=0.12,
)

labels = [f"{a}-{b}" for a, b in PAIRS]
contrib = {name: [] for name, _, _, _ in FIELDS}
for a, b in PAIRS:
    _, detail = score(BY_ID[a], BY_ID[b])
    used = sum(w for _, sim, w in detail if sim is not None) or 1.0
    for name, sim, w in detail:
        contrib[name].append(0.0 if sim is None else w * sim / used)

for name, _, _, _ in FIELDS:
    fig.add_trace(go.Bar(x=labels, y=contrib[name], name=name,
                         marker_color=PAL[name], legendgroup="f",
                         hovertemplate="%{x} · " + name + " %{y:.3f}<extra></extra>"),
                  row=1, col=1)

for key, ys in curves.items():
    fig.add_trace(go.Scatter(x=W_GRID, y=ys, name=key, mode="lines",
                             legendgroup="p",
                             hovertemplate="w=%{x:.2f} → %{y:.3f}<extra>" + key + "</extra>"),
                  row=1, col=2)

for y, txt, dash in [(HIGH, "HIGH 0.85", "dash"), (LOW, "LOW 0.55", "dot")]:
    fig.add_hline(y=y, line_dash=dash, line_color="#64748b", row=1, col=1)
    fig.add_hline(y=y, line_dash=dash, line_color="#64748b",
                  annotation_text=txt, annotation_position="right", row=1, col=2)
fig.add_vline(x=0.45, line_dash="dash", line_color="#334155",
              annotation_text="현재 0.45", annotation_position="bottom right",
              row=1, col=2)

fig.update_layout(barmode="stack", template="plotly_white", height=470, width=1180,
                  title="ex2_scoring.py 가중치 배분 — 0.45 / 0.25 / 0.15 / 0.10 / 0.05 (합 1.00)",
                  legend=dict(orientation="h", y=-0.20, traceorder="normal"))
fig.update_yaxes(title_text="점수", range=[0, 1.05], row=1, col=1)
fig.update_yaxes(title_text="점수", range=[0, 1.05], row=1, col=2)
fig.update_xaxes(title_text="레코드 쌍", row=1, col=1)
fig.update_xaxes(title_text="사업자번호 가중치 w", row=1, col=2)

import os
_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_png, scale=2)
print(f"saved: {os.path.basename(_png)}")
_show(fig)
# 출력: saved: expy.png


# %% [markdown]
# ## 정리
#
# - `FIELDS` 가중치는 **사업자번호 0.45(exact), 이름 0.25(fuzzy), 주소 0.15(fuzzy),
#   대표자 0.10(exact), 전화 0.05(exact)**. 합은 1.00.
# - 식별자에 절반 가까이 몰아주고, 표기가 흔들리는 필드만 `fuzzy`로 둔다.
# - `score()`는 빈 필드를 «모름»으로 빼고 $\sum_{i \in U} w_i$로 나눈다.
#   그래서 분모가 쌍마다 다르고, 가중치의 절대 크기가 아니라 비율만 의미가 있다.
# - 0.45라는 값은 두 방향으로 동시에 맞춰져 있다.
#   식별자 하나만으로는 자동 병합에 못 닿고($0.45/0.70 = 0.643$),
#   식별자가 다르면 나머지 넷이 다 같아도 못 닿는다($0.55$).
# - 이 값을 0.20으로 낮추면 r06-r07(다른 법인)이 순위를 타고 올라오고
#   r11-r12(같은 회사)는 자동 병합에서 떨어진다. 가중치 하나가 정확도와
#   사람 검토량을 동시에 흔든다.
