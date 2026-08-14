# %% [markdown]
# # `ex2_scoring.py`의 이행성 묶기 = 유니온-파인드(disjoint set)
#
# 질문: **`ex2_scoring.py`는 이행성 묶기를 어떤 자료구조로 구현하는가?**
#
# 답: **유니온-파인드(disjoint set)**. `find`에 경로 압축을 적용하고 `union`으로 대표를 잇는다.
#
# 원본 코드는 딱 이만큼이다. 클래스도, 라이브러리도 없다.
#
# ```python
# parent = {k: k for k in BY_ID}          # 처음엔 모두가 자기 자신의 대표
#
# def find(x):
#     while parent[x] != x:
#         parent[x] = parent[parent[x]]   # ← 경로 압축(정확히는 경로 «절반» 압축)
#         x = parent[x]
#     return x
#
# def union(x, y):
#     parent[find(x)] = find(y)           # ← 대표를 대표에 잇는다
# ```
#
# 왜 유니온-파인드인가? 이행성이 곧 «동치 관계»이기 때문이다.
#
# $$a \sim b \;\wedge\; b \sim c \;\Longrightarrow\; a \sim c$$
#
# 동치 관계는 집합을 서로 겹치지 않는 조각(disjoint set)으로 쪼갠다.
# «같다»는 쌍을 계속 던져 주면 조각이 알아서 합쳐지는 자료구조 —
# 그게 유니온-파인드다.

# %%
# 필요 패키지: plotly, kaleido  (union-find 자체는 표준 라이브러리만 사용)
import os
from itertools import combinations
import re


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


HERE = os.path.dirname(os.path.abspath(__file__))
print("준비 완료")
# 출력: 준비 완료

# %% [markdown]
# ## 1. 경로 압축이 트리를 «납작하게» 만드는 걸 눈으로 보기
#
# 유니온-파인드의 `parent`는 배열(여기서는 dict) 하나로 표현된 **숲(forest)**이다.
# `parent[x] == x`이면 x가 그 조각의 대표(root)다.
#
# 최악의 경우 parent가 일자 사슬이 된다: `7 → 6 → 5 → … → 0`.
# 이때 `find(7)`은 7칸을 걸어가야 한다. 압축이 없으면 다음에도 또 7칸이다.

# %%
def find_plain(parent, x):
    """경로 압축 «없는» find. 걸어만 가고 아무것도 고치지 않는다."""
    steps = 0
    while parent[x] != x:
        x = parent[x]
        steps += 1
    return x, steps


def find_halving(parent, x):
    """ex2_scoring.py의 find. parent[x] = parent[parent[x]] — 경로 절반 압축."""
    steps = 0
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
        steps += 1
    return x, steps


def chain(n=8):
    """0 ← 1 ← 2 ← … ← n-1 형태의 최악 사슬."""
    p = {0: 0}
    p.update({i: i - 1 for i in range(1, n)})
    return p


def as_row(parent):
    return " ".join(f"{parent[k]}" for k in sorted(parent))


N = 8
print("노드      :", " ".join(str(k) for k in range(N)))
print("초기 parent:", as_row(chain(N)))
# 출력: 노드      : 0 1 2 3 4 5 6 7
# 출력: 초기 parent: 0 0 1 2 3 4 5 6

# %%
# --- 압축 없는 find: 몇 번 불러도 parent는 그대로, 비용도 그대로 ---
p_plain = chain(N)
print("[압축 없음]")
for t in range(1, 4):
    root, steps = find_plain(p_plain, 7)
    print(f"  find(7) #{t}: root={root}, 걸음={steps}, parent={as_row(p_plain)}")
# 출력: [압축 없음]
# 출력:   find(7) #1: root=0, 걸음=7, parent=0 0 1 2 3 4 5 6
# 출력:   find(7) #2: root=0, 걸음=7, parent=0 0 1 2 3 4 5 6
# 출력:   find(7) #3: root=0, 걸음=7, parent=0 0 1 2 3 4 5 6

# %%
# --- ex2_scoring.py의 find: 지나가면서 parent를 고쳐 놓는다 ---
p_comp = chain(N)
print("[경로 압축(절반)]")
for t in range(1, 4):
    root, steps = find_halving(p_comp, 7)
    print(f"  find(7) #{t}: root={root}, 걸음={steps}, parent={as_row(p_comp)}")
# 출력: [경로 압축(절반)]
# 출력:   find(7) #1: root=0, 걸음=4, parent=0 0 1 1 3 3 5 5
# 출력:   find(7) #2: root=0, 걸음=2, parent=0 0 1 0 3 3 5 3
# 출력:   find(7) #3: root=0, 걸음=1, parent=0 0 1 0 3 3 5 0

# %% [markdown]
# 세 번 부르는 동안 사슬이 납작해졌다. 걸음 수가 7 → 4 → 2 → 1로 줄었다.
# parent 배열을 보면 7의 부모가 `6 → 5 → 3 → 0`으로 root에 가까워지고,
# 지나가는 길에 있던 2, 4, 6도 함께 끌어올려진다.
#
# 주의할 점: 원본의 `parent[x] = parent[parent[x]]`는 교과서적 «완전» 경로 압축
# (재귀로 경로의 모든 노드를 root에 직결)이 아니라 **경로 절반 압축(path halving)**이다.
# 한 번에 root까지 붙이지는 않지만 같은 상환 복잡도 등급을 얻고,
# 재귀 없이 while 한 줄로 끝나서 깊은 사슬에서도 스택이 터지지 않는다.

# %%
# 완전 압축과 비교해 보면 차이가 분명하다.
def find_full(parent, x):
    root, steps = x, 0
    while parent[root] != root:       # 1패스: root를 찾으며 걸음을 센다
        root = parent[root]
        steps += 1
    y = x
    while parent[y] != root:          # 2패스: 경로의 «모든» 노드를 root에 직결
        parent[y], y = root, parent[y]
    return root, steps


p_full = chain(N)
find_full(p_full, 7)
p_h = chain(N)
find_halving(p_h, 7)
print("완전 압축 1회 후 parent:", as_row(p_full))
print("절반 압축 1회 후 parent:", as_row(p_h))
# 출력: 완전 압축 1회 후 parent: 0 0 0 0 0 0 0 0
# 출력: 절반 압축 1회 후 parent: 0 0 1 1 3 3 5 5

# %% [markdown]
# ## 2. 실제 자동 병합 쌍을 순서대로 union하기
#
# `ex2_scoring.py`가 12개 레코드를 전부 비교해 점수 $\ge 0.85$로 «자동 병합» 판정한
# 쌍은 다음 4개다.
#
# | 쌍 | 점수 |
# |---|---|
# | r01–r02 | 1.000 |
# | r01–r03 | 0.973 |
# | r02–r03 | 0.973 |
# | r11–r12 | 0.875 |
#
# 아래 셀에서 원본 채점 로직을 그대로 돌려 이 쌍들을 직접 뽑는다.

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
BY_ID = {r[0]: r for r in RECORDS}
TRUTH = {frozenset(["r01", "r02", "r03", "r04"]), frozenset(["r11", "r12"])}


def norm_name(s):
    s = re.sub(r"\(주\)|주식회사|\(유\)|유한회사", "", s)
    return re.sub(r"\s+", "", s)


def norm_phone(s):
    return re.sub(r"\D", "", s or "")


def sim_str(a, b):
    def g(x):
        x = re.sub(r"\s+", "", x or "")
        return {x[i:i + 2] for i in range(len(x) - 1)} or {x}
    A, B = g(a), g(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


FIELDS = [
    ("사업자번호", lambda r: r[2], 0.45, "exact"),
    ("이름",      lambda r: norm_name(r[1]), 0.25, "fuzzy"),
    ("주소",      lambda r: r[3], 0.15, "fuzzy"),
    ("대표자",    lambda r: r[4], 0.10, "exact"),
    ("전화",      lambda r: norm_phone(r[5]), 0.05, "exact"),
]


def score(a, b):
    total = used = 0.0
    for _name, get, w, mode in FIELDS:
        x, y = get(a), get(b)
        if not x or not y:            # 한쪽이 비면 «모름»으로 빼둔다
            continue
        s = 1.0 if (mode == "exact" and x == y) else (
            0.0 if mode == "exact" else sim_str(x, y))
        total += w * s
        used += w
    return total / used if used else 0.0


HIGH, LOW = 0.85, 0.55
auto, review = [], []
for a, b in combinations(sorted(BY_ID), 2):
    s = score(BY_ID[a], BY_ID[b])
    if s >= LOW:
        (auto if s >= HIGH else review).append((a, b, round(s, 3)))

print("자동 병합 쌍:", [(a, b, s) for a, b, s in auto])
print("사람 검토 쌍:", [(a, b, s) for a, b, s in review])
# 출력: 자동 병합 쌍: [('r01', 'r02', 1.0), ('r01', 'r03', 0.973), ('r02', 'r03', 0.973), ('r11', 'r12', 0.875)]
# 출력: 사람 검토 쌍: [('r01', 'r04', 0.643), ('r02', 'r04', 0.643), ('r06', 'r07', 0.55)]

# %%
# 원본과 똑같은 유니온-파인드를 dict 하나로 만든다. 단계마다 상태를 찍는다.
IDS = sorted(BY_ID)


def new_dsu():
    return {k: k for k in IDS}


def make_ops(parent):
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        parent[find(x)] = find(y)      # 대표를 대표에 잇는다
    return find, union


def clusters_of(parent, find):
    groups = {}
    for k in IDS:
        groups.setdefault(find(k), []).append(k)
    return {frozenset(v) for v in groups.values() if len(v) > 1}


parent = new_dsu()
find, union = make_ops(parent)
print("초기 대표:", {k: find(k) for k in IDS[:4]}, "...(모두 자기 자신)")
for a, b, s in auto:
    union(a, b)
    reps = sorted({find(k) for k in IDS})
    print(f"union({a}, {b})  →  대표 개수 {len(reps)},  군집 {sorted(sorted(c) for c in clusters_of(parent, find))}")
# 출력: 초기 대표: {'r01': 'r01', 'r02': 'r02', 'r03': 'r03', 'r04': 'r04'} ...(모두 자기 자신)
# 출력: union(r01, r02)  →  대표 개수 11,  군집 [['r01', 'r02']]
# 출력: union(r01, r03)  →  대표 개수 10,  군집 [['r01', 'r02', 'r03']]
# 출력: union(r02, r03)  →  대표 개수 10,  군집 [['r01', 'r02', 'r03']]
# 출력: union(r11, r12)  →  대표 개수 9,  군집 [['r01', 'r02', 'r03'], ['r11', 'r12']]

# %% [markdown]
# 두 가지가 한눈에 보인다.
#
# 1. **이행성이 «공짜로» 나온다.** r01–r02와 r01–r03만 넣었는데 r02–r03도 같은 군집에 들어갔다.
# 2. **중복 union은 무해하다.** 세 번째 `union(r02, r03)`에서 대표 개수가 10 → 10으로 그대로다.
#    이미 같은 대표이므로 `parent[find(x)] = find(y)`가 자기 자신을 자기에게 잇고 끝난다.
#    점수 계산이 같은 사실을 몇 번 알려 주든 자료구조가 알아서 흡수한다.

# %%
# 최종 군집과 parent 배열을 확인한다.
final = clusters_of(parent, find)
print("최종 군집:", sorted(sorted(c) for c in final))
print("정답 군집:", sorted(sorted(c) for c in TRUTH))
print("일치?", final == TRUTH)
print("최종 parent:", {k: parent[k] for k in IDS})
# 출력: 최종 군집: [['r01', 'r02', 'r03'], ['r11', 'r12']]
# 출력: 정답 군집: [['r01', 'r02', 'r03', 'r04'], ['r11', 'r12']]
# 출력: 일치? False
# 출력: 최종 parent: {'r01': 'r03', 'r02': 'r03', 'r03': 'r03', 'r04': 'r04', 'r05': 'r05', 'r06': 'r06', 'r07': 'r07', 'r08': 'r08', 'r09': 'r09', 'r10': 'r10', 'r11': 'r12', 'r12': 'r12'}

# %% [markdown]
# parent 배열을 읽는 법: `r01 → r03`, `r02 → r03`, `r03 → r03`이므로 r03이 대표다.
# r04부터 r10은 각자 자기 자신을 가리키는 «혼자짜리» 조각이고, `r11 → r12`로 r12가 두 번째 대표다.
# 군집을 뽑는 코드가 `len(v) > 1` 조건을 붙이는 이유가 여기 있다 — 혼자인 조각은 군집이 아니다.
#
# 자동 병합만으로는 정답에 못 간다. r04(GAON TECH)가 0.643으로 애매 구간에 떨어졌기 때문이다.
# 사람 판정을 `union`으로 밀어 넣으면 채워진다 — **사람의 결정도 결국 같은 자료구조에 들어가는 간선**이다.

# %%
HUMAN = {("r01", "r04"): True, ("r02", "r04"): True, ("r06", "r07"): False}
for (a, b), same in HUMAN.items():
    if same:
        union(a, b)
after_human = clusters_of(parent, find)
print("사람 판정 반영 후:", sorted(sorted(c) for c in after_human))
print("정답과 일치?", after_human == TRUTH)
# 출력: 사람 판정 반영 후: [['r01', 'r02', 'r03', 'r04'], ['r11', 'r12']]
# 출력: 정답과 일치? True

# %% [markdown]
# ## 3. union 순서를 바꿔도 최종 군집은 같다
#
# `union`은 트리 «모양»은 순서에 따라 바꾸지만, 만들어지는 **분할(partition)은 순서에 무관**하다.
# 동치 관계의 폐쇄(transitive closure)는 유일하기 때문이다. 모든 순서를 다 돌려 확인한다.

# %%
from itertools import permutations

edges = [(a, b) for a, b, _ in auto] + [("r01", "r04"), ("r02", "r04")]
results, shapes = set(), set()
for order in permutations(edges):
    p = new_dsu()
    f, u = make_ops(p)
    for a, b in order:
        u(a, b)
    results.add(frozenset(clusters_of(p, f)))
    shapes.add(tuple(sorted(p.items())))

print(f"순서 {len(list(permutations(edges)))}가지 시도")
print(f"→ 서로 다른 최종 «군집»    : {len(results)}가지")
print(f"→ 서로 다른 최종 «parent 배열»: {len(shapes)}가지")
print("군집:", sorted(sorted(c) for c in next(iter(results))))
# 출력: 순서 720가지 시도
# 출력: → 서로 다른 최종 «군집»    : 1가지
# 출력: → 서로 다른 최종 «parent 배열»: 3가지
# 출력: 군집: [['r01', 'r02', 'r03', 'r04'], ['r11', 'r12']]

# %% [markdown]
# 720가지 순서 전부가 **같은 군집 1가지**로 수렴한다. 반면 `parent` 배열의 구체적 모양은 3가지다.
# 즉 «누가 대표인가»는 순서에 따라 달라지지만 «누가 누구와 같은가»는 달라지지 않는다.
#
# 실무 함의: 대표 ID를 외부에 노출해 저장하면 재실행 때 값이 바뀔 수 있다.
# 안정된 대표가 필요하면 `min(cluster)`처럼 결정적인 규칙으로 다시 뽑아 써야 한다.

# %%
print("대표가 순서마다 달라지는 예:")
for order in [edges, list(reversed(edges))]:
    p = new_dsu()
    f, u = make_ops(p)
    for a, b in order:
        u(a, b)
    print("  ", [a + "-" + b for a, b in order[:2]], "... → r01의 대표:", f("r01"))
# 출력: 대표가 순서마다 달라지는 예:
# 출력:    ['r01-r02', 'r01-r03'] ... → r01의 대표: r04
# 출력:    ['r02-r04', 'r01-r04'] ... → r01의 대표: r03

# %% [markdown]
# ## 4. 오염 시나리오 — 잘못된 간선 하나가 군집 두 개를 삼킨다
#
# 유니온-파인드는 «되돌리기»가 없다. 경로 압축이 이미 parent를 덮어썼기 때문에
# `union` 한 번을 취소하려면 처음부터 다시 돌려야 한다.
#
# 정답 상태는 군집 2개다: `{r01,r02,r03,r04}` (4명), `{r11,r12}` (2명).
# 여기에 잘못된 쌍 **r04–r12** 하나만 넣어 보자.

# %%
def build(extra=()):
    p = new_dsu()
    f, u = make_ops(p)
    for a, b in [(a, b) for a, b, _ in auto] + [("r01", "r04"), ("r02", "r04")]:
        u(a, b)
    for a, b in extra:
        u(a, b)
    return p, f


p_ok, f_ok = build()
p_bad, f_bad = build(extra=[("r04", "r12")])
c_ok = sorted(sorted(c) for c in clusters_of(p_ok, f_ok))
c_bad = sorted(sorted(c) for c in clusters_of(p_bad, f_bad))
print("정상 :", c_ok, f"→ 군집 {len(c_ok)}개, 최대 크기 {max(len(c) for c in c_ok)}")
print("오염 :", c_bad, f"→ 군집 {len(c_bad)}개, 최대 크기 {max(len(c) for c in c_bad)}")
print("잘못된 쌍 1개가 만든 «가짜 같음» 쌍 수:", 4 * 2)
# 출력: 정상 : [['r01', 'r02', 'r03', 'r04'], ['r11', 'r12']] → 군집 2개, 최대 크기 4
# 출력: 오염 : [['r01', 'r02', 'r03', 'r04', 'r11', 'r12']] → 군집 1개, 최대 크기 6
# 출력: 잘못된 쌍 1개가 만든 «가짜 같음» 쌍 수: 8

# %% [markdown]
# 간선 1개를 잘못 넣었는데 «같다»고 주장되는 쌍은 $4 \times 2 = 8$개 늘었다.
# 크기 $m$, $n$인 두 군집을 잘못 붙이면 오류가 $m \cdot n$개로 증폭된다 —
# 선형이 아니라 **곱**이다. 그래서 원문이 이렇게 경고한다.
#
# > 이행성도 공짜가 아니다. 잘못된 병합 하나가 군집 전체를 오염시킨다.
# > 그래서 군집 크기에 상한을 두거나, 커지면 사람에게 보내는 게 안전하다.
#
# 상한을 두는 방어를 붙여 보자.

# %%
MAX_CLUSTER = 4
p = new_dsu()
size = {k: 1 for k in IDS}
f, _ = make_ops(p)


def guarded_union(x, y):
    rx, ry = f(x), f(y)
    if rx == ry:
        return "이미 동일"
    if size[rx] + size[ry] > MAX_CLUSTER:
        return f"거부(크기 {size[rx]}+{size[ry]} > {MAX_CLUSTER}) → 사람에게"
    p[rx] = ry
    size[ry] += size[rx]
    return "병합"


for a, b in [(a, b) for a, b, _ in auto] + [("r01", "r04"), ("r02", "r04"), ("r04", "r12")]:
    print(f"  union({a}, {b}): {guarded_union(a, b)}")
print("최종 군집:", sorted(sorted(c) for c in clusters_of(p, f)))
# 출력:   union(r01, r02): 병합
# 출력:   union(r01, r03): 병합
# 출력:   union(r02, r03): 이미 동일
# 출력:   union(r11, r12): 병합
# 출력:   union(r01, r04): 병합
# 출력:   union(r02, r04): 이미 동일
# 출력:   union(r04, r12): 거부(크기 4+2 > 4) → 사람에게
# 출력: 최종 군집: [['r01', 'r02', 'r03', 'r04'], ['r11', 'r12']]

# %% [markdown]
# ## 5. 성능 — 경로 압축이 실제로 얼마나 아끼는가
#
# 최악 사슬 $n = 2000$에서 «깊은 노드부터» `find`를 두 바퀴 돌려 걸음 수를 센다.
# (깊은 쪽부터 부르는 게 압축이 없을 때의 진짜 최악 패턴이다.)

# %%
def bench(n, finder, rounds=2):
    p = chain(n)
    order = range(n - 1, -1, -1)      # 가장 깊은 노드부터
    total = 0
    per_round = []
    for _ in range(rounds):
        r_steps = sum(finder(p, x)[1] for x in order)
        per_round.append(r_steps)
        total += r_steps
    depth = max(find_plain(dict(p), x)[1] for x in range(n))
    return total, per_round, depth


N_BIG = 2000
t_plain, r_plain, d_plain = bench(N_BIG, find_plain)
t_half, r_half, d_half = bench(N_BIG, find_halving)
t_full, r_full, d_full = bench(N_BIG, find_full)
print(f"n={N_BIG}, 두 바퀴 find")
print(f"  압축 없음   : 총 {t_plain:>9,}걸음  라운드별 {r_plain}  최종 최대깊이 {d_plain}")
print(f"  절반 압축   : 총 {t_half:>9,}걸음  라운드별 {r_half}  최종 최대깊이 {d_half}")
print(f"  완전 압축   : 총 {t_full:>9,}걸음  라운드별 {r_full}  최종 최대깊이 {d_full}")
print(f"  절감(절반 압축 vs 없음): {(1 - t_half / t_plain) * 100:.2f}%")
# 출력: n=2000, 두 바퀴 find
# 출력:   압축 없음   : 총 3,998,000걸음  라운드별 [1999000, 1999000]  최종 최대깊이 1999
# 출력:   절반 압축   : 총     6,926걸음  라운드별 [4925, 2001]  최종 최대깊이 2
# 출력:   완전 압축   : 총     5,996걸음  라운드별 [3997, 1999]  최종 최대깊이 1
# 출력:   절감(절반 압축 vs 없음): 99.83%

# %% [markdown]
# 400만 걸음이 7천 걸음으로 줄었다. **99.83% 절감**이다. 깊이 1999짜리 사슬이 사실상 사라졌다.
#
# 두 압축 방식의 성격 차이도 숫자에 드러난다.
#
# - 완전 압축은 최종 최대 깊이가 **1** — 모든 노드가 root에 직결된다.
# - 절반 압축(원본)은 최대 깊이 **2**가 남는다. 그래서 둘째 바퀴가 1999가 아니라 2001걸음이다.
#   한 번에 root까지 못 붙이는 대신 재귀도, 2패스도 없다.
#
# 차이는 상수 배 수준이고 상환 복잡도 등급은 같다. 원본이 절반 압축을 고른 건 합리적인 선택이다.
#
# 복잡도 정리:
#
# | 조합 | `find` 상환 복잡도 |
# |---|---|
# | 아무것도 없음 | $O(n)$ |
# | 경로 압축만 (원본 `ex2_scoring.py`) | $O(\log n)$ |
# | 유니온 바이 랭크/사이즈만 | $O(\log n)$ |
# | **경로 압축 + 유니온 바이 랭크** | $O(\alpha(n))$ |
#
# $\alpha$는 아커만 함수의 역함수로, 우주에 있는 원자 수 정도의 $n$에서도 $\alpha(n) < 5$다.
# 즉 실질적으로 **상수 시간**이다.
#
# $$\text{연산 } m\text{번 총비용} = O(m \cdot \alpha(n))$$
#
# 원본 코드는 랭크 없이 경로 압축만 쓴다. 12개 레코드에서는 그 차이가 보이지 않고,
# `parent[find(x)] = find(y)`라는 한 줄의 단순함이 더 값지다. 필요해지면 다음처럼 랭크를 붙인다.

# %%
def dsu_ranked(keys):
    par = {k: k for k in keys}
    rank = {k: 0 for k in keys}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx == ry:
            return False
        if rank[rx] < rank[ry]:        # 낮은 트리를 높은 트리에 붙인다
            rx, ry = ry, rx
        par[ry] = rx
        if rank[rx] == rank[ry]:
            rank[rx] += 1
        return True
    return par, rank, find, union


par, rank, f2, u2 = dsu_ranked(range(N_BIG))
for i in range(1, N_BIG):              # 최악을 유도하려 일부러 사슬처럼 넣는다
    u2(i, i - 1)
print("랭크 사용 시 최대 깊이:", max(find_plain(dict(par), x)[1] for x in range(N_BIG)))
print("최대 랭크:", max(rank.values()))
# 출력: 랭크 사용 시 최대 깊이: 1
# 출력: 최대 랭크: 1

# %% [markdown]
# ## 6. 시각화
#
# 왼쪽: 사슬 $n=2000$에서 `find` 라운드별 총 걸음 수(로그 축).
# 오른쪽: 정상 상태와 오염 상태의 군집 크기 — 잘못된 간선 1개로 4+2가 6이 된다.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROUNDS = 4
curves = {}
for label, finder in [("압축 없음", find_plain), ("절반 압축 (원본)", find_halving), ("완전 압축", find_full)]:
    p = chain(N_BIG)
    curves[label] = [sum(finder(p, x)[1] for x in range(N_BIG - 1, -1, -1)) for _ in range(ROUNDS)]
print(curves)
# 출력: {'압축 없음': [1999000, 1999000, 1999000, 1999000], '절반 압축 (원본)': [4925, 2001, 1999, 1999], '완전 압축': [3997, 1999, 1999, 1999]}

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=("find 총 걸음 수 (사슬 n=2000, 로그 축)", "군집 크기: 정상 vs 오염된 간선 1개"),
)
COLORS = {"압축 없음": "#d1495b", "절반 압축 (원본)": "#2a9d8f", "완전 압축": "#457b9d"}
for label, ys in curves.items():
    fig.add_trace(
        go.Scatter(x=list(range(1, ROUNDS + 1)), y=ys, name=label, mode="lines+markers",
                   line=dict(color=COLORS[label], width=3), marker=dict(size=9)),
        row=1, col=1,
    )
fig.add_trace(
    go.Bar(x=["r01..r04", "r11,r12"], y=[4, 2], name="정상 (군집 2개)",
           marker_color="#2a9d8f", text=[4, 2], textposition="outside"),
    row=1, col=2,
)
fig.add_trace(
    go.Bar(x=["r01..r04", "r11,r12"], y=[6, 0], name="오염 (군집 1개)",
           marker_color="#d1495b", text=[6, ""], textposition="outside"),
    row=1, col=2,
)
fig.update_yaxes(type="log", title_text="걸음 수(누적, 로그)", row=1, col=1)
fig.update_xaxes(title_text="find 라운드", dtick=1, row=1, col=1)
fig.update_yaxes(title_text="군집 크기(레코드 수)", range=[0, 7.5], row=1, col=2)
fig.update_layout(
    title="경로 압축의 효과와 이행성 오염 — ex2_scoring.py의 유니온-파인드",
    template="plotly_white", width=1100, height=470, barmode="group",
    legend=dict(orientation="h", y=-0.18),
)
_show(fig)

out = os.path.join(HERE, "expy.png")
fig.write_image(out, scale=2)
print("저장 완료:", os.path.basename(out), "존재?", os.path.exists(out))
# 출력: 저장 완료: expy.png 존재? True

# %% [markdown]
# ## 정리
#
# - `ex2_scoring.py`의 이행성 묶기는 **유니온-파인드(disjoint set)**다. dict 하나 + 함수 두 개.
# - `find`는 `parent[x] = parent[parent[x]]`로 **경로 압축**(정확히는 경로 절반 압축)을 걸어 트리를 납작하게 만든다.
# - `union(x, y)`는 `parent[find(x)] = find(y)` — **대표를 대표에 잇는다**. 원소가 아니라 root를 연결하는 게 핵심.
# - 최종 군집은 union 순서에 무관하지만, **대표 ID는 순서에 따라 바뀐다**. 대표를 저장하려면 결정적 규칙을 따로 둘 것.
# - 이행성은 이득도 «공짜»고 손해도 «공짜»다. 잘못된 간선 1개가 $m \cdot n$개의 가짜 쌍을 만든다 → 군집 크기 상한이 필요하다.
# - 랭크까지 붙이면 $O(\alpha(n))$ ≈ 상수. 다만 12개 레코드에서는 원본의 한 줄짜리 단순함이 옳은 선택이다.
