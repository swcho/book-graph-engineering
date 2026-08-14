# %% [markdown]
# # 블로킹(blocking)과 재현율
#
# **질문**: 블로킹은 무엇이며 성패를 정하는 지표는 무엇인가?
#
# **답**: 전수 비교 대신 후보 쌍을 좁히는 기법이다. 성패는 재현율인데, 후보에 못 들면 영영 만나지 못하기 때문이다.
#
# 이 스크립트는 14장 `ex1_blocking.py`의 데이터로 다음을 단계별로 확인한다.
#
# 1. 전수 비교 쌍이 $\binom{n}{2} \sim O(n^2)$ 로 폭발하는 것
# 2. 블로킹 키로 칸을 만들어 후보 쌍을 줄이는 것
# 3. 전략마다 **놓치는 쌍**이 다르고, 합집합이 재현율을 올리는 것
# 4. 감축률(속도)과 재현율(정확성)의 트레이드오프
#
# 필요 패키지: plotly, kaleido (없으면 표 출력까지는 그대로 동작)

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


# 14장 공통 데이터 (content/ch14/code/records.py)
# id, 이름, 사업자번호, 주소, 대표자, 전화
RECORDS = [
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

# 사람이 확인한 정답 군집
TRUTH = {
    frozenset(["r01", "r02", "r03", "r04"]),
    frozenset(["r11", "r12"]),
}

N = len(RECORDS)
print(f"레코드 {N}개")
# 출력: 레코드 12개

# %% [markdown]
# ## 1단계 — 전수 비교는 왜 안 되나
#
# $$\text{쌍의 수} = \binom{n}{2} = \frac{n(n-1)}{2}$$
#
# 제곱으로 자라므로 레코드가 10배가 되면 비교가 약 100배가 된다.

# %%
def all_pairs_count(n):
    return n * (n - 1) // 2


ALL_PAIRS = all_pairs_count(N)
print(f"레코드 {N}개 → 전수 비교 쌍 {ALL_PAIRS}개")
for n in (12, 1_000, 10_000, 100_000, 1_000_000):
    print(f"  n={n:>9,} → {all_pairs_count(n):>18,} 쌍")
# 출력: 레코드 12개 → 전수 비교 쌍 66개
# 출력:   n=       12 →                 66 쌍
# 출력:   n=    1,000 →            499,500 쌍
# 출력:   n=   10,000 →         49,995,000 쌍
# 출력:   n=  100,000 →      4,999,950,000 쌍
# 출력:   n=1,000,000 →    499,999,500,000 쌍

# %% [markdown]
# 10만 건에서 이미 50억 쌍이다. 쌍마다 문자열 유사도를 몇 개씩 계산하면 하루로 안 끝난다.
# **비교 대상 자체를 줄여야 한다.**
#
# ## 2단계 — 블로킹 키와 칸
#
# 레코드마다 값싼 키를 뽑아 같은 키끼리 한 칸에 모으고, **같은 칸 안에서만** 쌍을 만든다.
# 키 계산은 레코드당 $O(1)$ 이므로 칸 만들기는 $O(n)$ 이다.
#
# 이름 키는 정규화가 먼저다. 정규화 없이 앞 3글자를 자르면 `(주)가온테크`가 `(주)`가 되어
# 같은 회사가 다른 칸으로 갈라진다.

# %%
def norm_name(s):
    """법인격 표기와 공백을 걷어 낸다."""
    s = re.sub(r"\(주\)|주식회사|\(유\)|유한회사", "", s)
    return re.sub(r"\s+", "", s)


def key_bizno(r):
    return r[2] or None


def key_name3(r):
    n = norm_name(r[1])
    return n[:3] if len(n) >= 3 else n or None


def key_addr(r):
    a = r[3]
    return " ".join(a.split()[:2]) if a else None


for r in RECORDS[:5]:
    print(f"{r[0]} {r[1]:<12} bizno={key_bizno(r)!s:<14} name3={key_name3(r)!s:<10} addr={key_addr(r)}")
# 출력: r01 가온테크         bizno=123-45-67890   name3=가온테        addr=서울 강남구
# 출력: r02 (주)가온테크      bizno=123-45-67890   name3=가온테        addr=서울 강남구
# 출력: r03 가온테크 주식회사    bizno=None           name3=가온테        addr=서울 강남구
# 출력: r04 GAON TECH    bizno=123-45-67890   name3=GAO        addr=None
# 출력: r05 가온테크놀로지      bizno=999-88-77777   name3=가온테        addr=부산 해운대구

# %% [markdown]
# `r03`의 사업자번호 키가 `None`이다(빈 값). `r04`의 이름 키는 `GAO`, 주소 키는 `None`이다.
# 이 두 레코드가 뒤에서 각 전략의 실패 지점이 된다.

# %%
def block(records, keyfn):
    """키가 있는 것만 모으고, 2개 이상 모인 칸만 남긴다."""
    b = defaultdict(list)
    for r in records:
        k = keyfn(r)
        if k:  # 빈 값은 키가 아니다 — 묶으면 '값 없는 것들'끼리 폭발한다
            b[k].append(r[0])
    return {k: v for k, v in b.items() if len(v) > 1}


def pairs_from(blocks):
    out = set()
    for ids in blocks.values():
        for a, b in combinations(sorted(ids), 2):
            out.add((a, b))
    return out


STRATEGIES = {
    "사업자번호": key_bizno,
    "이름 앞 3글자": key_name3,
    "주소 앞 2어절": key_addr,
}

for label, fn in STRATEGIES.items():
    b = block(RECORDS, fn)
    print(f"[{label}] 칸 {len(b)}개, 비교 쌍 {len(pairs_from(b))}개")
    for k, v in sorted(b.items()):
        print(f"    {k!r:<22} {v}")
# 출력: [사업자번호] 칸 3개, 비교 쌍 5개
# 출력:     '123-45-67890'         ['r01', 'r02', 'r04']
# 출력:     '333-44-55555'         ['r08', 'r09']
# 출력:     '666-77-88888'         ['r11', 'r12']
# 출력: [이름 앞 3글자] 칸 3개, 비교 쌍 8개
# 출력:     '가온테'                  ['r01', 'r02', 'r03', 'r05']
# 출력:     '나루소'                  ['r06', 'r07']
# 출력:     '다올물'                  ['r08', 'r09']
# 출력: [주소 앞 2어절] 칸 3개, 비교 쌍 5개
# 출력:     '광주 서구'                ['r11', 'r12']
# 출력:     '서울 강남구'               ['r01', 'r02', 'r03']
# 출력:     '서울 마포구'               ['r06', 'r07']

# %% [markdown]
# ## 3단계 — 성패를 정하는 지표: 재현율
#
# 후보 쌍 집합 $C$, 정답 쌍 집합 $M$ 에 대해
#
# $$\text{재현율(Pair Completeness)} = \frac{|C \cap M|}{|M|}, \qquad
# \text{감축률(Reduction Ratio)} = 1 - \frac{|C|}{\binom{n}{2}}$$
#
# 두 실수의 회복 가능성이 **비대칭**이다.
#
# | 실수 | 결과 | 뒷단에서 고칠 수 있나 |
# |---|---|---|
# | 후보를 너무 많이 담음 | 느려진다 | 고칠 수 있다 (점수가 가짜 쌍을 걸러낸다) |
# | 정답 쌍을 빠뜨림 | 영영 못 만난다 | **못 고친다** (점수를 매길 기회조차 없다) |

# %%
TRUTH_PAIRS = set()
for group in TRUTH:
    for a, b in combinations(sorted(group), 2):
        TRUTH_PAIRS.add((a, b))

print(f"정답 쌍 {len(TRUTH_PAIRS)}개: {sorted(TRUTH_PAIRS)}")
# 출력: 정답 쌍 7개: [('r01', 'r02'), ('r01', 'r03'), ('r01', 'r04'), ('r02', 'r03'), ('r02', 'r04'), ('r03', 'r04'), ('r11', 'r12')]


def evaluate(cand):
    recall = len(cand & TRUTH_PAIRS) / len(TRUTH_PAIRS)
    reduction = 1 - len(cand) / ALL_PAIRS
    return recall, reduction, sorted(TRUTH_PAIRS - cand)


print(f"\n{'전략':<28} {'후보쌍':>6} {'재현율':>7} {'감축률':>7}  놓친 쌍")
print("-" * 78)
single = {}
for label, fn in STRATEGIES.items():
    cand = pairs_from(block(RECORDS, fn))
    single[label] = cand
    rec, red, missed = evaluate(cand)
    print(f"{label:<28} {len(cand):>6} {rec:>7.3f} {red:>7.3f}  {missed}")
# 출력: 전략                            후보쌍     재현율     감축률  놓친 쌍
# 출력: ------------------------------------------------------------------------------
# 출력: 사업자번호                             5   0.571   0.924  [('r01', 'r03'), ('r02', 'r03'), ('r03', 'r04')]
# 출력: 이름 앞 3글자                          8   0.429   0.879  [('r01', 'r04'), ('r02', 'r04'), ('r03', 'r04'), ('r11', 'r12')]
# 출력: 주소 앞 2어절                          5   0.571   0.924  [('r01', 'r04'), ('r02', 'r04'), ('r03', 'r04')]

# %% [markdown]
# 전략마다 **실패 모드가 다르다**.
#
# - 사업자번호만 쓰면 → `r03`(번호가 빈 값)이 어느 칸에도 못 들어가 `r03` 관련 쌍 3개를 놓친다.
# - 이름만 쓰면 → `r04`(GAON TECH)가 `GAO` 칸에 혼자 남고 `마루/머루`도 다른 칸이라 4개를 놓친다.
# - 주소만 쓰면 → `r04`(주소가 빔)가 어느 칸에도 못 들어가 3개를 놓친다.
#
# 세 전략 모두 `r04`나 `r03`에서 무너지는데, **무너지는 지점이 서로 다르다**.
#
# 그래서 **여러 전략을 돌리고 후보 쌍의 합집합**을 쓴다.
#
# $$C = C_{\text{bizno}} \cup C_{\text{name3}} \cup C_{\text{addr}}$$
#
# 합집합은 재현율에 대해 단조 증가한다. 전략을 추가하면 재현율은 절대 내려가지 않는다.

# %%
labels = list(STRATEGIES)
rows = []
acc = set()
for i, label in enumerate(labels, 1):
    acc = acc | single[label]
    rec, red, missed = evaluate(acc)
    rows.append((" + ".join(labels[:i]), len(acc), rec, red, missed))

print(f"{'누적 합집합':<44} {'후보쌍':>6} {'재현율':>7} {'감축률':>7}")
print("-" * 70)
for name, ncand, rec, red, _ in rows:
    print(f"{name:<44} {ncand:>6} {rec:>7.3f} {red:>7.3f}")
print(f"\n최종 후보 쌍 {len(acc)}개 = 전수 {ALL_PAIRS}개의 {len(acc)/ALL_PAIRS*100:.0f}%")
print(f"정답 쌍 {len(TRUTH_PAIRS)}개 중 후보에 못 든 것: {len(TRUTH_PAIRS - acc)}개 {sorted(TRUTH_PAIRS - acc)}")
# 출력: 누적 합집합                                       후보쌍     재현율     감축률
# 출력: ----------------------------------------------------------------------
# 출력: 사업자번호                                            5   0.571   0.924
# 출력: 사업자번호 + 이름 앞 3글자                                  11   0.857   0.833
# 출력: 사업자번호 + 이름 앞 3글자 + 주소 앞 2어절                      11   0.857   0.833
# 출력:
# 출력: 최종 후보 쌍 11개 = 전수 66개의 17%
# 출력: 정답 쌍 7개 중 후보에 못 든 것: 1개 [('r03', 'r04')]

# %% [markdown]
# 세 전략을 합쳐도 `('r03','r04')` 한 쌍은 못 담았다. `r03`은 번호가 없고 `r04`는 이름이 영문·주소가 비어
# **어떤 키로도 만나지 않는다.** 다만 실무에서는 뒷단 이행성(transitivity)이 이 쌍을 주워 온다:
# `r01–r03`(이름), `r01–r04`(번호)가 후보에 들었으니 같은 군집으로 묶인다. 아래에서 확인한다.

# %%
parent = {r[0]: r[0] for r in RECORDS}


def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


# 후보 쌍 중 '정답인' 것만 병합됐다고 가정 (점수·임계 단계가 완벽했을 때의 상한)
for a, b in sorted(acc & TRUTH_PAIRS):
    parent[find(a)] = find(b)

groups = defaultdict(list)
for r in RECORDS:
    groups[find(r[0])].append(r[0])
clusters = {frozenset(v) for v in groups.values() if len(v) > 1}
print("이행성으로 묶은 군집:", [sorted(c) for c in sorted(clusters, key=lambda x: sorted(x))])
print("정답과 일치:", "예" if clusters == TRUTH else "아니오")
# 출력: 이행성으로 묶은 군집: [['r01', 'r02', 'r03', 'r04'], ['r11', 'r12']]
# 출력: 정답과 일치: 예

# %% [markdown]
# 쌍 단위 재현율 0.857로도 군집은 정답과 일치했다. 하지만 이건 **후보에 든 쌍들이 사슬을 이어 준** 덕이다.
# 어떤 레코드가 어느 키에도 걸리지 않고 완전히 고립되면 이행성도 구제하지 못한다.
# 그래서 지표는 여전히 재현율이다.
#
# ## 4단계 — 트레이드오프 시각화
#
# 감축률(속도)과 재현율(정확성)을 한 평면에 놓고 본다. 왼쪽 아래에서 오른쪽 위로 갈수록 좋다.

# %%
def make_fig():
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "전수 비교는 O(n²)로 폭발한다",
            "블로킹: 후보 쌍 vs 재현율 (전략 누적)",
        ),
        specs=[[{}, {}]],
        horizontal_spacing=0.13,
    )

    # (1) O(n^2) 폭발
    ns = [10, 100, 1_000, 10_000, 100_000, 1_000_000]
    fig.add_trace(
        go.Scatter(
            x=ns,
            y=[all_pairs_count(n) for n in ns],
            mode="lines+markers",
            name="전수 비교 쌍 C(n,2)",
            line=dict(color="#d1495b", width=3),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=ns,
            y=ns,
            mode="lines",
            name="블로킹 키 계산 O(n)",
            line=dict(color="#2e86ab", width=2, dash="dash"),
        ),
        row=1,
        col=1,
    )
    fig.update_xaxes(type="log", title_text="레코드 수 n", row=1, col=1)
    fig.update_yaxes(type="log", title_text="연산 규모 (log)", row=1, col=1)

    # (2) 재현율 vs 후보 쌍
    names = ["①번호만"] + [f"{c}+{lb}" for c, lb in zip("②③", labels[1:])]
    xs = [r[1] for r in rows]
    ys = [r[2] for r in rows]
    # 좌표가 겹치는 점이 있어 라벨 위치를 점마다 다르게 준다
    tpos = ["bottom center", "top right", "bottom right"][: len(names)]
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="lines+markers+text",
            text=names,
            textposition=tpos,
            name="전략 합집합 누적",
            marker=dict(size=13, color="#2e86ab"),
            line=dict(color="#2e86ab", width=2),
        ),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=[ALL_PAIRS],
            y=[1.0],
            mode="markers+text",
            text=["전수 비교 (재현율 1.0, 감축률 0)"],
            textposition="bottom left",
            name="전수 비교",
            marker=dict(size=15, color="#d1495b", symbol="x"),
        ),
        row=1,
        col=2,
    )
    fig.add_hline(
        y=1.0,
        line=dict(color="#888", dash="dot"),
        annotation_text="재현율 상한 — 블로킹에서 잃으면 회복 불가",
        annotation_position="top left",
        row=1,
        col=2,
    )
    fig.update_xaxes(title_text=f"후보 쌍 수 (전수 {ALL_PAIRS})", range=[-2, ALL_PAIRS * 1.12], row=1, col=2)
    fig.update_yaxes(title_text="재현율 (Pair Completeness)", range=[0, 1.15], row=1, col=2)

    fig.update_layout(
        title="블로킹 — O(n²)을 사는 대신 재현율을 위험에 내놓는 거래",
        template="plotly_white",
        width=1150,
        height=470,
        legend=dict(orientation="h", y=-0.18),
    )
    return fig


try:
    fig = make_fig()
    _show(fig)
    import os

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
    fig.write_image(out, scale=2)
    print("saved:", out)
except ImportError as e:
    print("시각화 생략 (패키지 없음):", e)
# 출력: saved: .../expy.png

# %% [markdown]
# 왼쪽 그림: 빨간 선(전수 비교)과 파란 점선(블로킹 키 계산)의 간격이 곧 블로킹이 버는 값이다.
# 로그 축에서도 벌어지는 게 보인다.
#
# 오른쪽 그림: 전략을 더할수록 오른쪽(느려짐)과 위쪽(재현율 상승)으로 움직인다.
# 세 번째 전략(주소)은 후보 쌍도 재현율도 그대로다 — 앞 두 전략이 이미 담은 쌍만 다시 담았다.
# 즉 전략을 늘리는 것 자체가 목적이 아니고, **다른 실패 모드를 덮는** 전략을 골라야 한다.
# 전수 비교(X 표시)는 재현율 1.0을 보장하지만 후보 쌍이 66개 전부다.
# 설계는 이 곡선에서 **재현율을 먼저 확보하고** 남는 예산으로 감축률을 사는 순서로 한다.
#
# ## 정리
#
# - **블로킹** = 값싼 키로 칸을 만들어 **같은 칸 안에서만** 비교하는 기법. $O(n^2)$ → 실용적 규모.
# - **성패는 재현율**. 감축률이 낮으면 느릴 뿐이고 정밀도는 뒷단이 회복해 주지만,
#   후보에서 빠진 쌍은 점수를 매길 기회조차 없어 **영영 못 만난다**.
# - 그래서 **전략을 서너 개 돌리고 합집합**을 쓴다. 빈 값은 키로 쓰지 않고, 거대한 칸은 쪼갠다.
# - 그리고 정답 표본으로 **재현율을 계속 측정**한다. 측정 없는 블로킹은 조용히 데이터를 버린다.
