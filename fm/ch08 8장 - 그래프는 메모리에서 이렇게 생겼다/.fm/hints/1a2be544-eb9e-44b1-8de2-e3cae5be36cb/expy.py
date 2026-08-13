# %% [markdown]
# # dict of list는 왜 무거운가 — 원소마다 붙는 파이썬 객체
#
# **Q.** dict of list(인접 리스트)가 무거운 이유는 무엇인가?
# **A.** 파이썬 객체가 원소마다 붙기 때문이다. 편리하지만 원소당 오버헤드가 정수 배열보다 훨씬 크다.
#
# CSR은 이웃 하나를 **4바이트**에 담는다. dict of list는 이웃 하나를 담으려고
# 「리스트 칸에 든 포인터 8바이트」 + 「그 포인터가 가리키는 `int` 객체 28~32바이트」를 쓴다.
#
# $$\text{CSR: } 4E' \text{ bytes} \qquad\text{vs}\qquad \text{dict of list: } \underbrace{(8 + s_{\text{int}})}_{\approx 36\sim40} E' + \underbrace{(h_{\text{list}} + h_{\text{dict}})}_{\approx 110} n$$
#
# ($E'$ = 이웃 항목 총수, 무향이면 $2E$)
#
# 이 스크립트는 그 오버헤드를 **한 겹씩 벗겨서** 확인한다.
#
# 필요 패키지: plotly, kaleido (마지막 시각화 셀에서만 사용. 없으면 그 셀만 건너뛴다)

# %%
import random
import struct
import sys
import tracemalloc
from array import array
from collections import defaultdict


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


print("Python", sys.version.split()[0], "/ 포인터 크기", struct.calcsize("P"), "바이트")
print("빈 int  0     :", sys.getsizeof(0), "B   ← 헤더만")
print("int     1     :", sys.getsizeof(1), "B   ← 헤더 + 30비트 자릿수 1개(4B)")
print("int     2**30 :", sys.getsizeof(2**30), "B   ← 자릿수 2개")
print("빈 list []    :", sys.getsizeof([]), "B")
print("빈 dict {}    :", sys.getsizeof({}), "B")
print("빈 array('i') :", sys.getsizeof(array("i")), "B")
# 출력: Python 3.9.6 / 포인터 크기 8 바이트
# 출력: 빈 int  0     : 24 B   ← 헤더만
# 출력: int     1     : 28 B   ← 헤더 + 30비트 자릿수 1개(4B)
# 출력: int     2**30 : 32 B   ← 자릿수 2개
# 출력: 빈 list []    : 56 B
# 출력: 빈 dict {}    : 64 B
# 출력: 빈 array('i') : 64 B

# %% [markdown]
# ## 1단계 — 정수 하나의 값어치가 4바이트인데 실제 크기는 28바이트
#
# CPython의 `int`는 임의 정밀도 객체(`PyLongObject`)다. 구성은 이렇다.
#
# | 필드 | 크기 | 설명 |
# |---|---|---|
# | `ob_refcnt` | 8 B | 참조 카운트 |
# | `ob_type` | 8 B | 타입 포인터 |
# | `ob_size` | 8 B | 자릿수 개수(부호 포함) |
# | `ob_digit[]` | 4 B × k | 30비트씩 쪼갠 실제 값 |
#
# 헤더 24바이트 + 자릿수 4바이트 = **28바이트**. 게다가 pymalloc은 8바이트 정렬로
# 반올림하므로 실제 점유는 **32바이트**다. 노드 번호 하나를 담는 데 `array('i')`의 **8배**다.

# %%
digits = [(0, 0), (1, 1), (2**30, 2), (2**60, 3), (2**90, 4)]
print(f"{'값':>32} {'getsizeof':>10} {'8B 정렬 실제':>14} {'자릿수':>7}")
for v, k in digits:
    s = sys.getsizeof(v)
    print(f"{v:>32,} {s:>10} {(s + 7) // 8 * 8:>14} {k:>7}")

print(f"\narray('i') 한 칸: 4 B  → int 객체 한 개는 그보다 {32 / 4:.0f}배")
# 출력:                                값  getsizeof   8B 정렬 실제     자릿수
# 출력:                                0         24             24       0
# 출력:                                1         28             32       1
# 출력:                    1,073,741,824         32             32       2
# 출력:        1,152,921,504,606,846,976         36             40       3
# 출력: 1,237,940,039,285,380,274,899,124,224         40             40       4
# 출력:
# 출력: array('i') 한 칸: 4 B  → int 객체 한 개는 그보다 8배

# %% [markdown]
# ## 2단계 — small int 캐시가 만드는 착시
#
# CPython은 $-5 \le v \le 256$ 인 정수를 인터프리터 시작 시 미리 만들어 두고 공유한다
# (`NSMALLNEGINTS=5`, `NSMALLPOSINTS=257`). 그래서 **노드 번호가 작으면 `int` 객체 비용이 안 보인다.**
#
# 장난감 그래프(노드 10개)로 측정하면 「dict of list도 별로 안 무겁네?」라는 결론이 나오는데,
# 노드가 300개를 넘어가는 순간 원소마다 새 객체가 생긴다. **이 카드의 함정이 여기다.**

# %%
def fresh(v):
    """런타임에 int를 새로 만든다. 리터럴로 쓰면 컴파일러가 상수를 합쳐 버려서 실험이 거짓말을 한다."""
    return int(str(v))


_rnd = random.Random(0)
small = [_rnd.randrange(256) for _ in range(1000)]  # 노드 번호가 작은 장난감 그래프
large = [_rnd.randrange(1000, 2000) for _ in range(1000)]  # 현실적인 노드 번호

print("256 이하를 두 번 만들면 같은 객체?", fresh(255) is fresh(255), "← 캐시 공유")
print("257 이상을 두 번 만들면 같은 객체?", fresh(1255) is fresh(1255), "← 매번 새 객체")
print("리스트 1000칸을 채운 int 객체 개수 — 값이 0~255 :", len({id(x) for x in small}))
print("리스트 1000칸을 채운 int 객체 개수 — 값이 1000~ :", len({id(x) for x in large}))
# 출력: 256 이하를 두 번 만들면 같은 객체? True ← 캐시 공유
# 출력: 257 이상을 두 번 만들면 같은 객체? False ← 매번 새 객체
# 출력: 리스트 1000칸을 채운 int 객체 개수 — 값이 0~255 : 250
# 출력: 리스트 1000칸을 채운 int 객체 개수 — 값이 1000~ : 1000


# %%
def deep_size(obj, seen=None):
    """중첩 컨테이너까지 대략 더한다. 같은 객체는 한 번만 센다(8장 ex1_three_forms.py와 동일)."""
    seen = seen if seen is not None else set()
    if id(obj) in seen:
        return 0
    seen.add(id(obj))
    size = sys.getsizeof(obj)
    if isinstance(obj, dict):
        size += sum(deep_size(k, seen) + deep_size(v, seen) for k, v in obj.items())
    elif isinstance(obj, (list, tuple, set)):
        size += sum(deep_size(x, seen) for x in obj)
    return size


shallow = sys.getsizeof(large)
print(f"{'리스트(1000개)':<22} {'getsizeof':>10} {'deep_size':>10} {'차이':>10}")
for label, lst in (("작은 값(캐시됨)", small), ("큰 값(각자 객체)", large)):
    print(f"{label:<22} {sys.getsizeof(lst):>10,} {deep_size(lst):>10,} {deep_size(lst) - sys.getsizeof(lst):>10,}")

print("\ngetsizeof는 포인터 배열만 센다. int 객체 본체는 deep_size로만 보인다.")
print(f"array('i', 1000개)   : {sys.getsizeof(array('i', large)):>10,} B")
# 출력: 리스트(1000개)              getsizeof  deep_size         차이
# 출력: 작은 값(캐시됨)                   8,856     15,852      6,996
# 출력: 큰 값(각자 객체)                  8,856     36,856     28,000
# 출력:
# 출력: getsizeof는 포인터 배열만 센다. int 객체 본체는 deep_size로만 보인다.
# 출력: array('i', 1000개)   :      4,064 B

# %% [markdown]
# 같은 「정수 1000개」인데 15,852 B / 36,856 B / 4,064 B로 갈린다.
#
# - 값이 0~255면 서로 다른 객체가 **250개**만 생긴다(중복 값은 캐시를 공유). 항목당 약 16 B.
# - 값이 1000 이상이면 객체가 **1000개** 생긴다. 항목당 8 B(포인터) + 28 B(객체) = 36 B.
# - `array('i')`는 객체가 **0개**다. 항목당 4 B.
#
# **`array`는 값을 담고, `list`는 값을 가리키는 포인터 + 객체를 담는다.** 이 한 문장이 오버헤드의 정체다.

# %% [markdown]
# ## 3단계 — list는 포인터 배열 + 여유분(over-allocation)
#
# `list`는 헤더 40바이트 + GC 헤더 16바이트 = **56바이트**로 시작하고,
# 칸마다 **8바이트 포인터**를 쓴다. 게다가 `append`할 때마다 realloc하지 않으려고
# 필요보다 넉넉히 잡는다. CPython 3.9의 성장 공식은 이렇다.
#
# $$\texttt{new\_allocated} = (\texttt{newsize} + (\texttt{newsize} \gg 3) + 6) \;\&\; \lnot 3$$
#
# 즉 약 **12.5% 여유분**이 붙는다. 인접 리스트를 `append`로 쌓으면 이 여유분도 같이 산다.

# %%
prev, rows = None, []
lst = []
for i in range(120):
    lst.append(i)
    allocated = (sys.getsizeof(lst) - 56) // 8
    if allocated != prev:
        rows.append((len(lst), allocated, sys.getsizeof(lst)))
        prev = allocated

print(f"{'len':>5} {'allocated':>10} {'getsizeof':>10} {'낭비칸':>7}")
for n_, a_, s_ in rows:
    print(f"{n_:>5} {a_:>10} {s_:>10} {a_ - n_:>7}")

waste = sum(a_ - n_ for n_, a_, _ in rows) / len(rows)
print(f"\n성장 직후 평균 낭비 칸 {waste:.1f}개. 차수 12짜리 리스트는 16칸을 잡는다(4칸 = 32 B 낭비).")
# 출력:   len  allocated  getsizeof    낭비칸
# 출력:     1          4         88       3
# 출력:     5          8        120       3
# 출력:     9         16        184       7
# 출력:    17         24        248       7
# 출력:    25         32        312       7
# 출력:    33         40        376       7
# 출력:    41         52        472      11
# 출력:    53         64        568      11
# 출력:    65         76        664      11
# 출력:    77         92        792      15
# 출력:    93        108        920      15
# 출력:   109        128       1080      19
# 출력:
# 출력: 성장 직후 평균 낭비 칸 9.7개. 차수 12짜리 리스트는 16칸을 잡는다(4칸 = 32 B 낭비).

# %% [markdown]
# ## 4단계 — dict는 노드마다 해시 테이블 슬롯을 산다
#
# `dict`는 load factor를 $2/3$ 아래로 유지하려고 항목 수의 1.5배 이상 되는
# **2의 거듭제곱** 크기 테이블을 잡는다. 항목 하나당 `(hash, key*, value*)` 24바이트 +
# 인덱스 배열 몫이 들어간다. 그래서 노드를 넣을 때마다 계단식으로 뛴다.

# %%
prev, drows = None, []
d = {}
for i in range(300, 600):
    d[i] = None
    s = sys.getsizeof(d)
    if s != prev:
        drows.append((len(d), s))
        prev = s

print(f"{'항목 수':>7} {'dict bytes':>11} {'항목당':>8}")
for n_, s_ in drows:
    print(f"{n_:>7} {s_:>11,} {s_ / n_:>7.1f}")
print("\n리사이즈 직후가 가장 헐렁하다. 항목당 유효 비용은 대략 36~90 B 사이를 오간다.")
# 출력:    항목 수  dict bytes      항목당
# 출력:       1         232   232.0
# 출력:       6         360    60.0
# 출력:      11         640    58.2
# 출력:      22       1,176    53.5
# 출력:      43       2,272    52.8
# 출력:      86       4,696    54.6
# 출력:     171       9,312    54.5
# 출력:
# 출력: 리사이즈 직후가 가장 헐렁하다. 항목당 유효 비용은 대략 36~90 B 사이를 오간다.

# %% [markdown]
# ## 5단계 — 실제 그래프로 세 그릇 비교
#
# 8장 `graphgen.py`와 같은 방식으로 무작위 그래프를 만들고,
# **dict of list**, **dict of array('i')**, **CSR(배열 2개)** 를 나란히 잰다.


# %%
def make(n, avg_deg=12, seed=20260801):
    rnd = random.Random(seed)
    edges = set()
    for a in range(n):
        for _ in range(avg_deg // 2):
            b = rnd.randrange(n)
            if a != b:
                edges.add((min(a, b), max(a, b)))
    return sorted(edges)


def build_adjlist(edges):
    adj = defaultdict(list)
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    return dict(adj)


def build_csr(edges, n):
    deg = [0] * n
    for a, b in edges:
        deg[a] += 1
        deg[b] += 1
    offset = array("i", [0] * (n + 1))
    for i in range(n):
        offset[i + 1] = offset[i] + deg[i]
    cur = list(offset[:n])
    nbr = array("i", [0] * offset[n])
    for a, b in edges:
        nbr[cur[a]] = b
        cur[a] += 1
        nbr[cur[b]] = a
        cur[b] += 1
    return offset, nbr


SIZES = (2_000, 10_000, 50_000)
table = []
print(f"{'노드':>7} {'엣지':>8} {'dict of list':>14} {'dict of array':>14} {'CSR':>11} {'배수(list/CSR)':>15}")
for n in SIZES:
    edges = make(n)
    adj = build_adjlist(edges)
    b_list = deep_size(adj)
    b_arr = deep_size({u: array("i", vs) for u, vs in adj.items()})
    off, nbr = build_csr(edges, n)
    b_csr = sys.getsizeof(off) + sys.getsizeof(nbr)
    table.append((n, len(edges), b_list, b_arr, b_csr))
    print(f"{n:>7,} {len(edges):>8,} {b_list:>14,} {b_arr:>14,} {b_csr:>11,} {b_list / b_csr:>14.1f}x")
# 출력:      노드       엣지   dict of list  dict of array         CSR    배수(list/CSR)
# 출력:   2,000   11,956        786,592        353,460     103,780            7.6x
# 출력:  10,000   59,962      4,038,736      1,694,692     519,828            7.8x
# 출력:  50,000  299,958     21,508,836      9,621,196   2,599,796            8.3x

# %% [markdown]
# `dict of array('i')`만 봐도 절반 이하로 줄어든다. 그 차이가 순수하게
# **「원소마다 붙은 `int` 객체 + 포인터」** 비용이다. 나머지 차이는 노드마다 붙은
# 컨테이너 헤더와 dict 슬롯이다.
#
# ## 6단계 — 원소당 오버헤드 분해
#
# 가장 큰 그래프에서 **이웃 항목 하나당 몇 바이트**를 쓰는지 나눠 본다.
# 무향이라 이웃 항목 총수는 $E' = 2E$다.

# %%
n, e, b_list, b_arr, b_csr = table[-1]
eprime = 2 * e

edges = make(n)
adj = build_adjlist(edges)

n_nodes = len(adj)
h_dict = sys.getsizeof(adj)
h_lists = sum(sys.getsizeof(v) for v in adj.values())  # 포인터 배열 + 여유분 + 헤더
b_ints = b_list - h_dict - h_lists  # 남은 것 = int 객체 본체
slots_alloc = sum((sys.getsizeof(v) - 56) // 8 for v in adj.values())

print(f"이웃 항목 총수 E' = 2E = {eprime:,}, 노드 {n_nodes:,}\n")
print(f"{'구성 요소':<34} {'바이트':>13} {'항목당':>8}")
print(f"{'dict 해시 테이블(노드 키)':<34} {h_dict:>13,} {h_dict / eprime:>7.2f}")
print(f"{'list 헤더 56 B × 노드':<34} {56 * n_nodes:>13,} {56 * n_nodes / eprime:>7.2f}")
print(f"{'list 포인터 칸 8 B × allocated':<34} {8 * slots_alloc:>13,} {8 * slots_alloc / eprime:>7.2f}")
print(f"{'int 객체 본체':<34} {b_ints:>13,} {b_ints / eprime:>7.2f}")
print("-" * 57)
print(f"{'dict of list 합계':<34} {b_list:>13,} {b_list / eprime:>7.2f}")
print(f"{'CSR (nbr 4 B + offset 몫)':<34} {b_csr:>13,} {b_csr / eprime:>7.2f}")
print(f"\n여유분(over-allocation)으로 산 빈 칸: {slots_alloc - eprime:,}개 = {8 * (slots_alloc - eprime):,} B")
print(f"항목당 오버헤드 배수: {(b_list / eprime) / (b_csr / eprime):.1f}x")
# 출력: 이웃 항목 총수 E' = 2E = 599,916, 노드 50,000
# 출력:
# 출력: 구성 요소                                        바이트      항목당
# 출력: dict 해시 테이블(노드 키)                      2,621,536    4.37
# 출력: list 헤더 56 B × 노드                      2,800,000    4.67
# 출력: list 포인터 칸 8 B × allocated             6,333,504   10.56
# 출력: int 객체 본체                              9,753,796   16.26
# 출력: ---------------------------------------------------------
# 출력: dict of list 합계                       21,508,836   35.85
# 출력: CSR (nbr 4 B + offset 몫)               2,599,796    4.33
# 출력:
# 출력: 여유분(over-allocation)으로 산 빈 칸: 191,772개 = 1,534,176 B
# 출력: 항목당 오버헤드 배수: 8.3x

# %% [markdown]
# `int 객체 본체`가 항목당 32 B가 아니라 16.3 B로 나오는 이유: `deep_size`는 같은 객체를
# 한 번만 세는데, 무향 엣지 하나가 만든 `int` 객체가 양쪽 인접 리스트에 **공유**되기 때문이다.
# 파일에서 한 줄씩 파싱해 넣는 현실에서는 공유가 안 일어나므로 이 값이 32 B에 가까워진다.
#
# ## 7단계 — tracemalloc으로 「실제로 붙잡고 있는 양」 측정
#
# `deep_size`는 근사다. 그래프를 **스트림으로 적재**하는 상황을 흉내 내서
# 각 구조가 끝까지 붙잡고 있는 실제 힙 사용량을 잰다. 포인트는 이것이다.
#
# - CSR: `int` 객체는 **잠깐 쓰고 버린다.** 값이 배열에 복사되므로 GC가 회수한다.
# - dict of list: `int` 객체를 **끝까지 붙잡는다.** 리스트가 그 객체를 참조하니 못 버린다.


# %%
def fresh_edges(edges):
    """파일에서 파싱해 넣는 상황. 원소마다 새 int 객체가 생긴다(256 이하는 캐시 공유)."""
    for a, b in edges:
        yield int(str(a)), int(str(b))


def build_csr_stream(factory, n):
    """엣지를 두 번 흘려보내며 CSR을 만든다. 중간 int 객체는 남지 않는다."""
    deg = [0] * n
    for a, b in factory():
        deg[a] += 1
        deg[b] += 1
    off = array("i", [0] * (n + 1))
    for i in range(n):
        off[i + 1] = off[i] + deg[i]
    cur = list(off[:n])
    nb = array("i", [0] * off[n])
    for a, b in factory():
        nb[cur[a]] = b
        cur[a] += 1
        nb[cur[b]] = a
        cur[b] += 1
    return off, nb


NT = 10_000
src = make(NT)

tracemalloc.start()
m0 = tracemalloc.get_traced_memory()[0]
adj_t = build_adjlist(fresh_edges(src))
m1 = tracemalloc.get_traced_memory()[0]
del adj_t
m2 = tracemalloc.get_traced_memory()[0]
csr_t = build_csr_stream(lambda: fresh_edges(src), NT)
m3 = tracemalloc.get_traced_memory()[0]
tracemalloc.stop()

real_adj, real_csr = m1 - m0, m3 - m2
print(f"{'구조':<16} {'tracemalloc 실측':>18} {'deep_size 추정':>16}")
print(f"{'dict of list':<16} {real_adj:>18,} {table[1][2]:>16,}")
print(f"{'CSR':<16} {real_csr:>18,} {table[1][4]:>16,}")
print(f"\n실측 배수 {real_adj / real_csr:.1f}x  (deep_size 추정 {table[1][2] / table[1][4]:.1f}x)")
print("실측이 더 나쁘다. deep_size가 공유 int를 한 번만 세고 pymalloc 반올림을 빼먹기 때문이다.")
del csr_t
# 출력: 구조                 tracemalloc 실측     deep_size 추정
# 출력: dict of list              5,395,370        4,038,736
# 출력: CSR                         520,752          519,828
# 출력:
# 출력: 실측 배수 10.4x  (deep_size 추정 7.8x)
# 출력: 실측이 더 나쁘다. deep_size가 공유 int를 한 번만 세고 pymalloc 반올림을 빼먹기 때문이다.

# %% [markdown]
# **10.4배.** `deep_size`가 말한 7.8배는 낙관적인 하한이었다.
# 그리고 이 10~11배가 8장 도입부의 「4.1GB vs 380MB」와 정확히 같은 배수다.
#
# ## 8단계 — 100만 노드로 외삽
#
# 항목당 비용이 정해지면 나머지는 곱셈이다. 8장 도입부의 「4.1GB vs 380MB」가 여기서 나온다.

# %%
per_item_list = b_list / eprime
per_item_csr = b_csr / eprime
print(f"{'노드':>12} {'이웃 항목':>13} {'dict of list':>14} {'CSR':>11}")
for m in (1_000_000, 10_000_000):
    items = m * 12  # 평균 차수 12 → 이웃 항목 12m
    gb_list = items * per_item_list / 1024**3
    gb_csr = items * per_item_csr / 1024**3
    print(f"{m:>12,} {items:>13,} {gb_list:>11.2f} GB {gb_csr:>8.2f} GB")
print(f"\n항목당 {per_item_list:.1f} B vs {per_item_csr:.1f} B. 32GB 장비에서 살아남는지 여부가 여기서 갈린다.")
print("1,000만 노드 줄이 곧 8장 도입부의 「4.1GB vs 380MB」다.")
# 출력:           노드         이웃 항목   dict of list         CSR
# 출력:    1,000,000    12,000,000        0.40 GB     0.05 GB
# 출력:   10,000,000   120,000,000        4.01 GB     0.48 GB
# 출력:
# 출력: 항목당 35.9 B vs 4.3 B. 32GB 장비에서 살아남는지 여부가 여기서 갈린다.
# 출력: 1,000만 노드 줄이 곧 8장 도입부의 「4.1GB vs 380MB」다.

# %% [markdown]
# ## 시각화

# %%
try:
    import math

    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    BLUE, ORANGE, RED = "#4C78A8", "#F58518", "#C0392B"
    # dict of list 오버헤드는 「한 덩어리의 부분들」이라 단색 계열 농담으로 쌓는다.
    RAMP = ["#8C2D2D", "#C0392B", "#E07A6A", "#F3B5AB"]

    fig = make_subplots(
        rows=1,
        cols=2,
        column_widths=[0.42, 0.58],
        horizontal_spacing=0.13,
        subplot_titles=(
            "이웃 항목 1개당 바이트 — 오버헤드 분해",
            "같은 그래프, 그릇만 다름 (바이트, 로그 스케일)",
        ),
    )

    # --- 왼쪽: 항목당 오버헤드 누적 막대 ---
    # barmode는 figure 전체에 하나뿐이라 "group"으로 두고, 여기서는 base= 로 직접 쌓는다.
    parts = [
        ("int 객체 본체", b_ints / eprime, RAMP[0]),
        ("list 포인터 칸 (8 B + 여유분)", 8 * slots_alloc / eprime, RAMP[1]),
        ("list 헤더 56 B/노드", 56 * n_nodes / eprime, RAMP[2]),
        ("dict 해시 테이블", h_dict / eprime, RAMP[3]),
    ]
    acc = 0.0
    for label, val, color in parts:
        fig.add_trace(
            go.Bar(
                x=["dict of list"],
                y=[val],
                base=[acc],
                offsetgroup="L",
                width=0.55,
                name=label,
                marker_color=color,
                marker_line=dict(color="white", width=1),
                text=[f"{val:.1f}"],
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(color="white", size=13),
                legendgroup="parts",
                legendgrouptitle_text="dict of list 항목당 오버헤드 구성",
            ),
            row=1,
            col=1,
        )
        acc += val

    fig.add_trace(
        go.Bar(
            x=["CSR (배열 2개)"],
            y=[per_item_csr],
            base=[0],
            offsetgroup="L",
            width=0.55,
            name="CSR — 정수 4 B, 객체 0개",
            marker_color=BLUE,
            text=[f"<b>{per_item_csr:.1f}</b>"],
            textposition="outside",
            textfont=dict(size=13),
            legendgroup="parts",
        ),
        row=1,
        col=1,
    )
    fig.add_annotation(
        x="dict of list",
        y=per_item_list,
        text=f"<b>{per_item_list:.1f} B/항목</b> = CSR의 {per_item_list / per_item_csr:.1f}배",
        showarrow=True,
        arrowhead=2,
        arrowwidth=1.2,
        arrowcolor="#555",
        ax=0,
        ay=-34,
        font=dict(size=13, color="#333"),
        row=1,
        col=1,
    )

    # --- 오른쪽: 규모별 총 메모리 (그룹 막대) ---
    labels = [f"{n_:,}노드" for n_, *_ in table]
    allv = []
    for name, idx, color in (
        ("dict of list", 2, RED),
        ("dict of array('i')", 3, ORANGE),
        ("CSR (배열 2개)", 4, BLUE),
    ):
        vals = [row[idx] for row in table]
        allv += vals
        fig.add_trace(
            go.Bar(
                x=labels,
                y=vals,
                offsetgroup=name,
                name=name,
                marker_color=color,
                text=[f"{v / 1e6:.2f} MB<br>{v / row[4]:.1f}x" for v, row in zip(vals, table)],
                textposition="outside",
                textfont=dict(size=10),
                legendgroup="scale",
                legendgrouptitle_text="구조별 총 메모리",
            ),
            row=1,
            col=2,
        )

    fig.update_yaxes(title_text="bytes / 이웃 항목 1개", range=[0, per_item_list * 1.28], row=1, col=1)
    fig.update_yaxes(
        type="log",
        title_text="bytes",
        range=[math.log10(min(allv) * 0.55), math.log10(max(allv) * 4.0)],
        row=1,
        col=2,
    )
    fig.update_layout(
        title="dict of list가 무거운 이유 — 파이썬 객체가 원소마다 붙는다",
        barmode="group",
        template="plotly_white",
        width=1180,
        height=660,
        legend=dict(orientation="h", y=-0.14, x=0.5, xanchor="center", font=dict(size=11)),
        margin=dict(l=80, r=40, t=100, b=190),
    )

    _show(fig)
    fig.write_image("expy.png", scale=2)
    print("expy.png 저장 완료")
except ImportError as exc:
    print("plotly/kaleido 없음 — 시각화 셀 건너뜀:", exc)
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# | 그릇 | 이웃 1개당 | 정체 |
# |---|---|---|
# | `array('i')` / CSR | **4 B** | 값을 직접 담는다. 객체 헤더 0 |
# | `dict of array('i')` | **약 16 B** | 값은 배열에 있지만 노드마다 컨테이너가 붙는다 |
# | `dict of list` | **약 36 B** | 포인터 8 B + `int` 객체 28~32 B + 컨테이너 몫 |
#
# - **핵심 한 문장:** `array`는 **값**을 담고 `list`는 값을 가리키는 **포인터 + 객체**를 담는다.
# - 오버헤드는 네 겹이다. ① `int` 객체 본체(16~32 B) ② 리스트 포인터 칸(8 B) ③ 리스트 over-allocation 여유분(약 12.5%) ④ 노드마다 붙는 list 헤더 56 B와 dict 슬롯.
# - **측정 함정:** 노드 번호가 256 이하면 small int 캐시 때문에 오버헤드가 안 보인다. 장난감 그래프로 재면 결론이 뒤집힌다.
# - `deep_size`가 말한 8배는 **낙관적 하한**이다. 스트림 적재를 흉내 낸 `tracemalloc` 실측은 **10.4배**였다.
# - 그래도 인접 리스트는 **쌓기(append)와 수정에 강하다.** 실무 패턴은 「인접 리스트로 적재하고, 분석 직전에 CSR로 굽는다」.
