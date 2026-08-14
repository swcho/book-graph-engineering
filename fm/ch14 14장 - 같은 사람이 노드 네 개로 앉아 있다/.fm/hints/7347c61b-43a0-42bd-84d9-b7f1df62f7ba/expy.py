# %% [markdown]
# # `norm_name()` — 법인격 표기와 공백을 걷어 내기
#
# 14장 `ex1_blocking.py` / `ex2_scoring.py` 가 공유하는 두 줄짜리 정규화 함수다.
#
# ```python
# def norm_name(s):
#     """법인격 표기와 공백을 걷어 낸다."""
#     s = re.sub(r"\(주\)|주식회사|\(유\)|유한회사", "", s)
#     return re.sub(r"\s+", "", s)
# ```
#
# 하는 일은 딱 두 단계다.
#
# 1. **법인격 표기 제거** — `(주)`, `주식회사`, `(유)`, `유한회사` 를 빈 문자열로 치환
# 2. **모든 공백 제거** — `\s+` 를 빈 문자열로 치환 (공백을 하나로 줄이는 게 아니라 *없애* 버린다)
#
# 이 함수가 왜 필요한가? 블로킹 키 `key_name3()` 이 «이름 앞 3글자» 를 쓰기 때문이다.
# `(주)가온테크` 의 앞 3글자는 `(주)` 다. 정규화 없이는 `가온테크` 와 절대 같은 칸에 못 들어간다.
#
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용. 나머지 셀은 표준 라이브러리만)

# %%
import re
from collections import defaultdict
from itertools import combinations


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# 14장 원본 그대로
LEGAL_RE = r"\(주\)|주식회사|\(유\)|유한회사"


def norm_name(s):
    """법인격 표기와 공백을 걷어 낸다."""
    s = re.sub(LEGAL_RE, "", s)
    return re.sub(r"\s+", "", s)


print(norm_name("(주)가온테크"))
print(norm_name("가온테크 주식회사"))
print(norm_name("  가온 테크 (유) "))
# 출력: 가온테크
# 출력: 가온테크
# 출력: 가온테크

# %% [markdown]
# ## 단계별로 쪼개 보기
#
# 두 번의 `re.sub` 가 각각 무엇을 지우는지 중간 결과를 찍어 본다.
# 2단계(공백 제거)가 없으면 `가온테크 주식회사` → `가온테크 ` 로 뒤에 공백이 남고,
# 1단계(법인격 제거)가 없으면 `(주)가온테크` 의 괄호가 그대로 앞에 붙는다.

# %%
def norm_steps(s):
    """(원본, 법인격 제거 후, 공백까지 제거 후) 를 돌려준다."""
    step1 = re.sub(LEGAL_RE, "", s)
    step2 = re.sub(r"\s+", "", step1)
    return s, step1, step2


SAMPLES = [
    "가온테크",
    "(주)가온테크",
    "가온테크 주식회사",
    "가온 테크(유)",
    "유한회사 가온테크",
    "GAON TECH",
    "다올물산 부산지점",
]

print(f"{'원본':<20} {'① 법인격 제거':<20} {'② 공백 제거':<16}")
print("-" * 58)
for s in SAMPLES:
    a, b, c = norm_steps(s)
    print(f"{a!r:<20} {b!r:<20} {c!r:<16}")
# 출력: 원본                   ① 법인격 제거              ② 공백 제거
# 출력: ----------------------------------------------------------
# 출력: '가온테크'               '가온테크'               '가온테크'
# 출력: '(주)가온테크'            '가온테크'               '가온테크'
# 출력: '가온테크 주식회사'         '가온테크 '              '가온테크'
# 출력: '가온 테크(유)'           '가온 테크'              '가온테크'
# 출력: '유한회사 가온테크'         ' 가온테크'              '가온테크'
# 출력: 'GAON TECH'          'GAON TECH'          'GAONTECH'
# 출력: '다올물산 부산지점'         '다올물산 부산지점'         '다올물산부산지점'

# %% [markdown]
# 마지막 두 줄이 중요하다.
#
# - `GAON TECH` → `GAONTECH`: 공백은 지워지지만 **한글로 바뀌지 않는다**. 영문 표기는 못 잡는다.
# - `다올물산 부산지점` → `다올물산부산지점`: 공백을 지운 탓에 «본사/지점» 구분이 이름 문자열 안에 그대로 남는다.
#   정규화는 표기 차이만 지우고 의미 차이는 판단하지 않는다.

# %% [markdown]
# ## 14장 데이터 12건에 그대로 적용
#
# `records.py` 의 `RECORDS` 다. 같은 회사가 네 가지 표기로 앉아 있다.

# %%
RECORDS = [
    # id, 이름, 사업자번호, 주소, 대표자, 전화
    ("r01", "가온테크",        "123-45-67890", "서울 강남구 테헤란로 1",  "김하늘", "02-1234-5678"),
    ("r02", "(주)가온테크",     "123-45-67890", "서울 강남구 테헤란로 1",  "김하늘", "02-1234-5678"),
    ("r03", "가온테크 주식회사", "",             "서울 강남구 테헤란로 1길", "김하늘", "021234-5678"),
    ("r04", "GAON TECH",      "123-45-67890", "",                      "",      ""),
    ("r05", "가온테크놀로지",   "999-88-77777", "부산 해운대구 센텀로 9",  "박서준", "051-999-8877"),
    ("r06", "나루소프트",       "222-33-44444", "서울 마포구 월드컵로 2",  "이서연", "02-2222-3333"),
    ("r07", "나루소프트(주)",   "555-66-77777", "서울 마포구 월드컵로 2",  "이서연", "02-2222-3333"),
    ("r08", "다올물산 본사",    "333-44-55555", "인천 연수구 송도로 3",   "최민준", "032-333-4444"),
    ("r09", "다올물산 부산지점", "333-44-55555", "부산 사하구 낙동로 8",   "정우진", "051-333-4444"),
    ("r10", "라온에너지",       "444-55-66666", "대전 유성구 대덕대로 4",  "한지우", "042-444-5555"),
    ("r11", "마루상사",        "666-77-88888", "광주 서구 상무로 6",     "오세훈", "062-666-7777"),
    ("r12", "머루상사",        "666-77-88888", "광주 서구 상무로 6",     "오세훈", "062-666-7777"),
]

# 사람이 확인한 정답 — r01~r04 는 같은 회사, r11/r12 도 같다
TRUTH = [{"r01", "r02", "r03", "r04"}, {"r11", "r12"}]


def key3_raw(name):
    """정규화 «없이» 앞 3글자."""
    return name[:3] if len(name) >= 3 else name or None


def key3_norm(name):
    """14장 key_name3() — 정규화 후 앞 3글자."""
    n = norm_name(name)
    return n[:3] if len(n) >= 3 else n or None


print(f"{'id':<5} {'원본 이름':<18} {'정규화':<16} {'raw[:3]':<10} {'norm[:3]'}")
print("-" * 62)
for r in RECORDS:
    print(f"{r[0]:<5} {r[1]:<18} {norm_name(r[1]):<16} {key3_raw(r[1])!r:<10} {key3_norm(r[1])!r}")
# 출력: id    원본 이름              정규화              raw[:3]    norm[:3]
# 출력: --------------------------------------------------------------
# 출력: r01   가온테크               가온테크             '가온테'      '가온테'
# 출력: r02   (주)가온테크            가온테크             '(주)'      '가온테'
# 출력: r03   가온테크 주식회사         가온테크             '가온테'      '가온테'
# 출력: r04   GAON TECH          GAONTECH         'GAO'      'GAO'
# 출력: r05   가온테크놀로지           가온테크놀로지          '가온테'      '가온테'
# 출력: r06   나루소프트              나루소프트            '나루소'      '나루소'
# 출력: r07   나루소프트(주)           나루소프트            '나루소'      '나루소'
# 출력: r08   다올물산 본사            다올물산본사           '다올물'      '다올물'
# 출력: r09   다올물산 부산지점         다올물산부산지점         '다올물'      '다올물'
# 출력: r10   라온에너지              라온에너지            '라온에'      '라온에'
# 출력: r11   마루상사               마루상사             '마루상'      '마루상'
# 출력: r12   머루상사               머루상사             '머루상'      '머루상'

# %% [markdown]
# ## 정규화 전/후로 블록이 어떻게 달라지나
#
# 블로킹은 «같은 키를 가진 것끼리만 비교» 하는 전략이다.
# 키가 어긋나면 그 쌍은 후보에 못 들어가고, 후보에 못 들면 영영 못 만난다(재현율 문제).
#
# 정규화가 바꾸는 건 딱 하나: `r02 (주)가온테크` 가 `'(주)'` 칸에서 `'가온테'` 칸으로 이사한다.

# %%
def block(records, keyfn):
    b = defaultdict(list)
    for r in records:
        k = keyfn(r[1])
        if k:
            b[k].append(r[0])
    return {k: v for k, v in sorted(b.items())}


def pairs_from(blocks):
    out = set()
    for ids in blocks.values():
        if len(ids) > 1:
            out |= {tuple(sorted(p)) for p in combinations(sorted(ids), 2)}
    return out


truth_pairs = set()
for g in TRUTH:
    truth_pairs |= {tuple(sorted(p)) for p in combinations(sorted(g), 2)}

B_raw, B_norm = block(RECORDS, key3_raw), block(RECORDS, key3_norm)
P_raw, P_norm = pairs_from(B_raw), pairs_from(B_norm)

for label, B, P in [("정규화 전", B_raw, P_raw), ("정규화 후", B_norm, P_norm)]:
    multi = {k: v for k, v in B.items() if len(v) > 1}
    hit = len(truth_pairs & P)
    print(f"[{label}] 칸 {len(B)}개 (2건 이상 {len(multi)}개), 비교 쌍 {len(P)}개, "
          f"정답 쌍 회수 {hit}/{len(truth_pairs)}")
    for k, v in B.items():
        mark = "  <-- 혼자 앉음" if len(v) == 1 else ""
        print(f"    {k!r:<10} {v}{mark}")
    print()
# 출력: [정규화 전] 칸 8개 (2건 이상 3개), 비교 쌍 5개, 정답 쌍 회수 1/7
# 출력:     '(주)'      ['r02']  <-- 혼자 앉음
# 출력:     'GAO'      ['r04']  <-- 혼자 앉음
# 출력:     '가온테'      ['r01', 'r03', 'r05']
# 출력:     '나루소'      ['r06', 'r07']
# 출력:     '다올물'      ['r08', 'r09']
# 출력:     '라온에'      ['r10']  <-- 혼자 앉음
# 출력:     '마루상'      ['r11']  <-- 혼자 앉음
# 출력:     '머루상'      ['r12']  <-- 혼자 앉음
# 출력:
# 출력: [정규화 후] 칸 7개 (2건 이상 3개), 비교 쌍 8개, 정답 쌍 회수 3/7
# 출력:     'GAO'      ['r04']  <-- 혼자 앉음
# 출력:     '가온테'      ['r01', 'r02', 'r03', 'r05']
# 출력:     '나루소'      ['r06', 'r07']
# 출력:     '다올물'      ['r08', 'r09']
# 출력:     '라온에'      ['r10']  <-- 혼자 앉음
# 출력:     '마루상'      ['r11']  <-- 혼자 앉음
# 출력:     '머루상'      ['r12']  <-- 혼자 앉음

# %% [markdown]
# 정규화 한 번으로 `'(주)'` 칸이 사라지고 `'가온테'` 칸이 3건 → 4건이 됐다.
# 회수한 정답 쌍은 1개 → 3개. 늘어난 쌍은 `(r01,r02)`, `(r02,r03)` —
# 즉 «`(주)` 때문에 다른 칸에 앉아 있던» r02 가 합류한 결과다.
#
# 대가도 있다. `(r02,r05)` 처럼 **다른 회사와의 거짓 후보도 함께 늘어난다**(5쌍 → 8쌍).
# 정규화는 재현율을 올리는 대신 비교량을 늘린다. 그 균형이 설계다.

# %%
print("정규화로 새로 후보에 든 쌍:", sorted(P_norm - P_raw))
print("정규화로 새로 회수한 정답 쌍:", sorted((truth_pairs & P_norm) - (truth_pairs & P_raw)))
print("정규화 후에도 못 든 정답 쌍:", sorted(truth_pairs - P_norm))
# 출력: 정규화로 새로 후보에 든 쌍: [('r01', 'r02'), ('r02', 'r03'), ('r02', 'r05')]
# 출력: 정규화로 새로 회수한 정답 쌍: [('r01', 'r02'), ('r02', 'r03')]
# 출력: 정규화 후에도 못 든 정답 쌍: [('r01', 'r04'), ('r02', 'r04'), ('r03', 'r04'), ('r11', 'r12')]

# %% [markdown]
# ## 잡아 주는 케이스 / 여전히 놓치는 케이스
#
# | 변형 유형 | 예시 | `norm_name()` 이 잡나 |
# |---|---|---|
# | 법인격 접두 | `(주)가온테크` vs `가온테크` | O — 1단계에서 제거 |
# | 법인격 접미 + 공백 | `가온테크 주식회사` | O — 1·2단계 둘 다 필요 |
# | 띄어쓰기 변형 | `가온 테크` vs `가온테크` | O — 2단계에서 제거 |
# | 영문 표기 | `GAON TECH` vs `가온테크` | X — 문자 자체가 다르다 |
# | 오타 | `머루상사` vs `마루상사` | X — 한 글자가 다르다 |
# | 지점 구분 | `다올물산 부산지점` vs `다올물산 본사` | X — 오히려 붙여서 한 덩어리로 만든다 |
# | 다른 회사인데 앞 3글자 동일 | `가온테크놀로지` | X — 거짓 후보를 더 만든다 |
#
# `(주)` 계열 표기만 지우므로 `Inc.`, `Corp.`, `Ltd.`, `㈜`(단일 문자) 는 남는다.
# 확장하려면 정규식에 패턴을 더 넣어야 한다.

# %%
for a, b in [("(주)가온테크", "가온테크"), ("가온테크 주식회사", "가온테크"),
             ("가온 테크", "가온테크"), ("GAON TECH", "가온테크"),
             ("머루상사", "마루상사"), ("㈜가온테크", "가온테크"),
             ("Gaon Tech Inc.", "가온테크")]:
    same = norm_name(a) == norm_name(b)
    print(f"{a!r:<18} vs {b!r:<10} → {norm_name(a)!r:<12} == {norm_name(b)!r:<10} : "
          f"{'같은 키 O' if same else '다른 키 X'}")
# 출력: '(주)가온테크'          vs '가온테크'     → '가온테크'       == '가온테크'     : 같은 키 O
# 출력: '가온테크 주식회사'        vs '가온테크'     → '가온테크'       == '가온테크'     : 같은 키 O
# 출력: '가온 테크'            vs '가온테크'     → '가온테크'       == '가온테크'     : 같은 키 O
# 출력: 'GAON TECH'        vs '가온테크'     → 'GAONTECH'   == '가온테크'     : 다른 키 X
# 출력: '머루상사'             vs '마루상사'     → '머루상사'       == '마루상사'     : 다른 키 X
# 출력: '㈜가온테크'            vs '가온테크'     → '㈜가온테크'      == '가온테크'     : 다른 키 X
# 출력: 'Gaon Tech Inc.'   vs '가온테크'     → 'GaonTechInc.' == '가온테크'     : 다른 키 X

# %% [markdown]
# ## 유사도 관점 — `sim_str()` 도 함께 보기
#
# `ex2_scoring.py` 의 «이름» 필드는 `norm_name()` 을 거친 뒤 글자 2-gram 자카드로 비교한다.
#
# $$\mathrm{sim}(a,b) = \frac{|G_2(a) \cap G_2(b)|}{|G_2(a) \cup G_2(b)|}$$
#
# 여기서 $G_2(x)$ 는 $x$ 의 인접 두 글자 집합이다.
# 정규화는 이 유사도도 밀어 올린다 — `(주)` 가 만들던 잡음 2-gram(`(주`, `주)`, `)가`)이 사라지니까.

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


CASES = [
    ("(주)가온테크", "가온테크"),
    ("가온테크 주식회사", "가온테크"),
    ("나루소프트(주)", "나루소프트"),
    ("가온테크놀로지", "가온테크"),
    ("머루상사", "마루상사"),
    ("GAON TECH", "가온테크"),
]
print(f"{'A':<18} {'B':<12} {'정규화 전':>9} {'정규화 후':>9}   차이")
print("-" * 58)
for a, b in CASES:
    before, after = sim_str(a, b), sim_str(norm_name(a), norm_name(b))
    print(f"{a!r:<18} {b!r:<12} {before:>9.3f} {after:>9.3f}   {after - before:+.3f}")
# 출력: A                  B                정규화 전     정규화 후   차이
# 출력: ----------------------------------------------------------
# 출력: '(주)가온테크'          '가온테크'           0.500     1.000   +0.500
# 출력: '가온테크 주식회사'        '가온테크'           0.429     1.000   +0.571
# 출력: '나루소프트(주)'         '나루소프트'          0.571     1.000   +0.429
# 출력: '가온테크놀로지'          '가온테크'           0.500     0.500   +0.000
# 출력: '머루상사'             '마루상사'           0.500     0.500   +0.000
# 출력: 'GAON TECH'        '가온테크'           0.000     0.000   +0.000

# %% [markdown]
# 위 3줄은 1.000 — 완전 일치가 됐다. 아래 3줄은 그대로다.
# **정규화가 올려 주는 건 «표기 변형» 뿐**이라는 사실이 숫자로 드러난다.
#
# 그리고 `가온테크놀로지` 가 0.500 에 머무는 건 좋은 신호다.
# 정규화는 다른 회사를 억지로 붙이지 않는다 — 임계값이 그 판정을 맡는다.

# %% [markdown]
# ## 시각화
#
# 왼쪽: 정규화 전/후 «이름 앞 3글자» 칸 구성. `(주)` 칸이 사라지고 `가온테` 칸이 4건으로 커진다.
# 오른쪽: 유사도 상승폭. 표기 변형만 위로 뛰고 영문·오타는 바닥에 남는다.

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    keys = sorted(set(B_raw) | set(B_norm))
    raw_cnt = [len(B_raw.get(k, [])) for k in keys]
    norm_cnt = [len(B_norm.get(k, [])) for k in keys]

    fig = make_subplots(
        rows=1, cols=2, horizontal_spacing=0.16,
        subplot_titles=("① 블록(이름 앞 3글자) 크기", "② 이름 2-gram 자카드 유사도"),
    )
    fig.add_trace(go.Bar(x=keys, y=raw_cnt, name="정규화 전",
                         marker_color="#c9ccd1",
                         text=[c or "" for c in raw_cnt], textposition="outside"),
                  row=1, col=1)
    fig.add_trace(go.Bar(x=keys, y=norm_cnt, name="정규화 후",
                         marker_color="#2b6cb0",
                         text=[c or "" for c in norm_cnt], textposition="outside"),
                  row=1, col=1)

    labels = [f"{a}<br>vs {b}" for a, b in CASES]
    before = [sim_str(a, b) for a, b in CASES]
    after = [sim_str(norm_name(a), norm_name(b)) for a, b in CASES]
    fig.add_trace(go.Bar(x=labels, y=before, name="정규화 전",
                         marker_color="#c9ccd1", showlegend=False),
                  row=1, col=2)
    fig.add_trace(go.Bar(x=labels, y=after, name="정규화 후",
                         marker_color="#2b6cb0", showlegend=False),
                  row=1, col=2)

    fig.update_yaxes(title_text="레코드 수", row=1, col=1, range=[0, 5])
    fig.update_yaxes(title_text="자카드 유사도", row=1, col=2, range=[0, 1.15])
    fig.update_xaxes(tickangle=-30, row=1, col=2)
    fig.update_layout(
        title_text="norm_name(): 법인격 표기 + 공백 제거가 블로킹과 유사도에 미치는 효과",
        barmode="group", template="plotly_white", height=520, width=1200,
        legend=dict(orientation="h", yanchor="top", y=0.99,
                    xanchor="left", x=0.01, bgcolor="rgba(255,255,255,0.6)"),
    )
    _show(fig)
    fig.write_image("expy.png", scale=2)
    print("expy.png 저장 완료")
except ImportError as e:
    print("시각화 건너뜀 (plotly/kaleido 필요):", e)
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# - `norm_name()` = `(주)|주식회사|(유)|유한회사` 제거 → `\s+` 전부 제거. 두 줄이다.
# - 목적은 «표기가 다른 같은 이름» 을 같은 블로킹 키/같은 유사도 축에 올려놓는 것.
# - `(주)가온테크` 는 정규화 없이는 `'(주)'` 칸에 혼자 앉아 있고, 정규화하면 `'가온테'` 칸에 합류한다.
# - 잡는 것: 법인격 표기, 띄어쓰기. 못 잡는 것: 영문 표기, 오타, `㈜`/`Inc.` 같은 미등록 패턴, 지점 구분.
# - 그래서 14장은 이름 하나만 믿지 않는다. 사업자번호·주소 블로킹을 함께 돌리고 **합집합**을 후보로 쓴다.
