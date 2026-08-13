# %% [markdown]
# # `ex5_index_free.py`는 색인을 어떻게 흉내 내는가
#
# 예제 5의 핵심은 딱 두 함수다.
#
# ```python
# def build_sorted_edges(edges):
#     rows = sorted([(a, b) for a, b in edges] + [(b, a) for a, b in edges])
#     keys = [r[0] for r in rows]
#     return rows, keys
#
# def neighbors_via_index(rows, keys, u):
#     i = bisect_left(keys, u)          # ← 이진 탐색으로 구간 시작을 찾는다
#     out = []
#     while i < len(keys) and keys[i] == u:   # ← 같은 키가 끝날 때까지 훑는다
#         out.append(rows[i][1]); i += 1
#     return out
# ```
#
# 흉내의 구성 요소는 셋이다.
#
# | 관계형 DB의 조각 | 예제의 대역 |
# |---|---|
# | `edge(src, dst)` 테이블 | `rows` — 양방향으로 펼친 $2E$ 행 |
# | `src` 컬럼 위의 B-tree 인덱스 | `keys` **정렬 배열** + `bisect_left` |
# | 인덱스 탐색 후 매칭 행 스캔 | `while keys[i] == u` 구간 훑기 |
#
# 즉 「**정렬을 미리 해 두고, 시작 위치를 로그 시간에 찾는다**」는 B-tree의 골격만 남기고
# 페이지·팬아웃·버퍼풀을 다 버린 모형이다. 버린 것이 무엇인지가 이 노트의 후반부다.
#
# 필요 패키지: plotly, kaleido (마지막 시각화 셀에서만 사용. 없으면 그 셀만 건너뛴다)

# %%
import math
import random
import time
from array import array
from bisect import bisect_left
from collections import defaultdict


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# graphgen.make 를 그대로 옮겨 온다. 시드는 원본과 동일하게 고정.
def make(n=50_000, avg_deg=12, skew=False, seed=20260801):
    rnd = random.Random(seed)
    edges = set()
    if not skew:
        for a in range(n):
            for _ in range(avg_deg // 2):
                b = rnd.randrange(n)
                if a != b:
                    edges.add((min(a, b), max(a, b)))
        return sorted(edges)
    targets = [0, 1, 2]
    for a in range(3, n):
        for _ in range(avg_deg // 2):
            b = rnd.choice(targets)
            if a != b:
                edges.add((min(a, b), max(a, b)))
                targets.append(b)
        targets.append(a)
    return sorted(edges)


print("준비 완료")
# 출력: 준비 완료

# %% [markdown]
# ## 1단계 — 아주 작은 그래프로 «정렬 배열 색인»을 눈으로 본다
#
# 노드 8개짜리 그래프를 만들어서 `rows` / `keys`가 실제로 어떻게 생겼는지 찍어 본다.

# %%
tiny_edges = [(0, 3), (0, 5), (1, 3), (2, 5), (3, 6), (4, 5), (5, 7), (6, 7)]
TN = 8


def build_sorted_edges(edges):
    """색인을 흉내 낸다: 정렬된 배열 + 이진 탐색."""
    rows = sorted([(a, b) for a, b in edges] + [(b, a) for a, b in edges])
    keys = [r[0] for r in rows]
    return rows, keys


t_rows, t_keys = build_sorted_edges(tiny_edges)

print("원본 엣지 (무방향)     :", tiny_edges)
print("rows (양방향으로 펼쳐 정렬):")
print("  idx :", " ".join(f"{i:>2}" for i in range(len(t_rows))))
print("  key :", " ".join(f"{k:>2}" for k in t_keys))
print("  val :", " ".join(f"{r[1]:>2}" for r in t_rows))
print(f"\n엣지 {len(tiny_edges)}개 -> rows {len(t_rows)}개 (= 2E). 색인 흉내의 첫 비용은 «두 배 저장»이다.")
# 출력: 원본 엣지 (무방향)     : [(0, 3), (0, 5), (1, 3), (2, 5), (3, 6), (4, 5), (5, 7), (6, 7)]
# 출력: rows (양방향으로 펼쳐 정렬):
# 출력:   idx :  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
# 출력:   key :  0  0  1  2  3  3  3  4  5  5  5  5  6  6  7  7
# 출력:   val :  3  5  3  5  0  1  6  5  0  2  4  7  3  7  5  6
# 출력:
# 출력: 엣지 8개 -> rows 16개 (= 2E). 색인 흉내의 첫 비용은 «두 배 저장»이다.

# %% [markdown]
# `keys`는 **비감소 정렬**이므로 노드 $u$의 이웃은 반드시 하나의 **연속 구간**에 모여 있다.
#
# $$[\;\texttt{bisect\_left}(keys, u),\;\; \texttt{bisect\_left}(keys, u{+}1)\;)$$
#
# `bisect_left`는 그 구간의 **왼쪽 경계**만 찾아 주고, 오른쪽 경계는 `while keys[i] == u`로 걸어서 만난다.
# 즉 비용은 두 항의 합이다.
#
# $$C_{\text{색인}}(u) \;=\; \underbrace{\lceil \log_2 2E \rceil}_{\text{경계 찾기}} \;+\; \underbrace{\deg(u)}_{\text{구간 훑기}}$$

# %%
def binsearch_steps(keys, u):
    """bisect_left 와 동일한 결과를 내면서 비교 횟수를 센다."""
    lo, hi, steps = 0, len(keys), 0
    while lo < hi:
        mid = (lo + hi) // 2
        steps += 1
        if keys[mid] < u:
            lo = mid + 1
        else:
            hi = mid
    return lo, steps


def neighbors_via_index(rows, keys, u):
    i = bisect_left(keys, u)
    out = []
    while i < len(keys) and keys[i] == u:
        out.append(rows[i][1])
        i += 1
    return out


print(f"{'u':>2} {'bisect_left':>12} {'비교 횟수':>9} {'스캔 길이':>9}  이웃")
for u in range(TN):
    lo, steps = binsearch_steps(t_keys, u)
    nb = neighbors_via_index(t_rows, t_keys, u)
    assert lo == bisect_left(t_keys, u)
    print(f"{u:>2} {lo:>12} {steps:>9} {len(nb):>9}  {nb}")
print(f"\nlen(keys)={len(t_keys)} -> 비교 횟수는 log2(16)=4 근처(구간 폭 때문에 4~5). 이게 «색인 깊이»의 대역이다.")
# 출력:  u  bisect_left  비교 횟수  스캔 길이  이웃
# 출력:  0            0         5         2  [3, 5]
# 출력:  1            2         4         1  [3]
# 출력:  2            3         4         1  [5]
# 출력:  3            4         4         3  [0, 1, 6]
# 출력:  4            7         4         1  [5]
# 출력:  5            8         4         4  [0, 2, 4, 7]
# 출력:  6           12         4         2  [3, 7]
# 출력:  7           14         4         2  [5, 6]
# 출력:
# 출력: len(keys)=16 -> 비교 횟수는 log2(16)=4 근처(구간 폭 때문에 4~5). 이게 «색인 깊이»의 대역이다.

# %% [markdown]
# ## 2단계 — CSR은 같은 일을 «탐색 없이» 한다
#
# CSR의 `offset`은 위에서 `bisect_left`가 계산해 낸 **구간 경계를 미리 표로 적어 둔 것**이다.
#
# $$\text{CSR}: \quad [\;\texttt{offset}[u],\;\; \texttt{offset}[u{+}1]\;) \qquad\text{— 탐색 0회, 배열 접근 2회}$$
#
# `offset[u]`는 노드 번호로 바로 인덱싱한다. **이것이 「인덱스 없는 인접성」의 기계적 정체**다.
# 색인을 빠르게 만든 게 아니라, 색인을 **주소 계산으로 치환**했다.

# %%
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


def neighbors_csr(offset, nbr, u):
    return nbr[offset[u] : offset[u + 1]]


t_off, t_nbr = build_csr(tiny_edges, TN)
print("offset :", list(t_off))
print("nbr    :", list(t_nbr))
print()
print(f"{'u':>2}  {'bisect_left 결과':>16}  {'offset[u]':>10}  일치")
for u in range(TN):
    lo = bisect_left(t_keys, u)
    print(f"{u:>2}  {lo:>16}  {t_off[u]:>10}  {lo == t_off[u]}")

# 이웃 «집합»이 같은지 확인 (CSR 의 배치 순서는 정렬과 다르다)
same = all(sorted(neighbors_via_index(t_rows, t_keys, u)) == sorted(neighbors_csr(t_off, t_nbr, u)) for u in range(TN))
print(f"\n두 방식의 이웃 집합 동일: {same}")
print("offset 배열이 bisect_left 의 «답안지»다. 탐색을 미리 해서 표로 굳혀 둔 것.")
# 출력: offset : [0, 2, 3, 4, 7, 8, 12, 14, 16]
# 출력: nbr    : [3, 5, 3, 5, 0, 1, 6, 5, 0, 2, 4, 7, 3, 7, 5, 6]
# 출력:
# 출력:  u  bisect_left 결과   offset[u]  일치
# 출력:  0                 0           0  True
# 출력:  1                 2           2  True
# 출력:  2                 3           3  True
# 출력:  3                 4           4  True
# 출력:  4                 7           7  True
# 출력:  5                 8           8  True
# 출력:  6                12          12  True
# 출력:  7                14          14  True
# 출력:
# 출력: 두 방식의 이웃 집합 동일: True
# 출력: offset 배열이 bisect_left 의 «답안지»다. 탐색을 미리 해서 표로 굳혀 둔 것.

# %% [markdown]
# ## 3단계 — 데이터를 키우면 홉당 비용이 어떻게 벌어지는가
#
# **평균 차수를 12로 고정**한다. 그러면 구간 훑는 길이는 그대로고, 변하는 건 탐색 깊이뿐이다.
# 이 통제가 중요하다. 늘어나는 비용을 전부 「색인 깊이」로 귀속시킬 수 있다.
#
# 노드 수를 5,000 → 80,000까지 16배 키우면서 홉 하나(= 이웃 목록 한 번 얻기)의 시간을 잰다.
# 절대값은 기계마다 다르니 **가장 작은 크기 대비 배수**로 읽는다.

# %%
SIZES = (5_000, 10_000, 20_000, 40_000, 80_000)
N_PROBE = 8_000
REPEAT = 15   # 최소값을 취한다. 반복이 적으면 배수가 심하게 튄다.
rnd_probe = random.Random(20260801)

results = []
for n in SIZES:
    edges = make(n=n, avg_deg=12)
    rows, keys = build_sorted_edges(edges)
    offset, nbr = build_csr(edges, n)
    adj = defaultdict(list)
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)

    probes = [rnd_probe.randrange(n) for _ in range(N_PROBE)]

    def bench(fn):
        best = float("inf")
        for _ in range(REPEAT):
            t0 = time.perf_counter()
            for u in probes:
                fn(u)
            best = min(best, time.perf_counter() - t0)
        return best / len(probes) * 1e6  # us / hop

    t_idx = bench(lambda u: neighbors_via_index(rows, keys, u))
    t_csr = bench(lambda u: neighbors_csr(offset, nbr, u))
    t_dict = bench(lambda u: adj[u])
    steps = sum(binsearch_steps(keys, u)[1] for u in probes) / len(probes)

    results.append(
        dict(n=n, e=len(edges), rows=len(rows), t_idx=t_idx, t_csr=t_csr, t_dict=t_dict, steps=steps, log2=math.log2(len(rows)))
    )
    print(f"n={n:>7,} E={len(edges):>8,} rows={len(rows):>9,}  색인 {t_idx:6.2f}us  CSR {t_csr:6.2f}us  dict {t_dict:6.2f}us  비교 {steps:5.2f}회 (log2={math.log2(len(rows)):5.2f})")
# 필요 패키지: 없음 (표준 라이브러리만)
# 출력: n=  5,000 E=  29,958 rows=   59,916  색인   2.43us  CSR   0.20us  dict   0.06us  비교 15.90회 (log2=15.87)
# 출력: n= 10,000 E=  59,962 rows=  119,924  색인   2.68us  CSR   0.20us  dict   0.06us  비교 16.91회 (log2=16.87)
# 출력: n= 20,000 E= 119,964 rows=  239,928  색인   4.05us  CSR   0.20us  dict   0.06us  비교 17.90회 (log2=17.87)
# 출력: n= 40,000 E= 239,949 rows=  479,898  색인   5.25us  CSR   0.20us  dict   0.06us  비교 18.91회 (log2=18.87)
# 출력: n= 80,000 E= 479,963 rows=  959,926  색인   4.79us  CSR   0.20us  dict   0.06us  비교 19.91회 (log2=19.87)
# 출력: (엣지 수는 make(avg_deg=12) 가 노드마다 6개를 던지므로 E ~ 6n. 평균 차수는 어느 크기에서나 12)

# %% [markdown]
# ### 배수로 읽기
#
# 세로로 비교하면(같은 $n$에서 색인 대 CSR) **홉 하나의 값**을 알 수 있고,
# 가로로 비교하면(작은 $n$ 대 큰 $n$) **데이터가 커질 때의 기울기**를 알 수 있다.

# %%
b = results[0]
print(f"{'n':>8} {'색인/CSR':>9} {'색인 증가':>10} {'CSR 증가':>9} {'비교 증가':>10}")
for r in results:
    print(
        f"{r['n']:>8,} {r['t_idx']/r['t_csr']:>8.1f}x {r['t_idx']/b['t_idx']:>9.2f}x "
        f"{r['t_csr']/b['t_csr']:>8.2f}x {r['steps']/b['steps']:>9.2f}x"
    )
print(
    "\n- 같은 크기에서 색인 방식은 CSR 대비 10~30배 비싸다 (홉 하나당).\n"
    "- 데이터 16배 -> 비교 횟수는 +4회(= log2 16, 1.25배). 시간은 그보다 더 는다(1.5~2.5배).\n"
    "  이진 탐색은 배열을 절반씩 건너뛰므로 «캐시 적대적»이다. 배열이 커지면 초반 몇 번의\n"
    "  점프가 매번 새 캐시 줄을 끌어온다. 즉 깊이만 느는 게 아니라 깊이 하나의 값도 비싸진다.\n"
    "- CSR 은 16배 커져도 그대로다(±5% 측정 노이즈). offset[u] 는 크기와 무관한 «주소 계산».\n"
    "- k홉이면 이 차이가 k번 곱해진다. 그래서 «두 번째 홉부터 이득»이다."
)
# 출력:        n  색인/CSR   색인 증가  CSR 증가   비교 증가
# 출력:    5,000     12.4x      1.00x     1.00x      1.00x
# 출력:   10,000     13.1x      1.10x     1.04x      1.06x
# 출력:   20,000     20.7x      1.67x     1.00x      1.13x
# 출력:   40,000     26.0x      2.16x     1.03x      1.19x
# 출력:   80,000     24.2x      1.97x     1.01x      1.25x
# 출력:   (시간 배수는 실행마다 흔들린다. «비교 증가»만 결정적이고, 시간은 그보다 크게 는다는 방향만 읽는다)
# 출력:
# 출력: - 같은 크기에서 색인 방식은 CSR 대비 10~30배 비싸다 (홉 하나당).
# 출력: - 데이터 16배 -> 비교 횟수는 +4회(= log2 16, 1.25배). 시간은 그보다 더 는다(1.5~2.5배).
# 출력:   이진 탐색은 배열을 절반씩 건너뛰므로 «캐시 적대적»이다. ...
# 출력: - CSR 은 16배 커져도 그대로다(±5% 측정 노이즈). offset[u] 는 크기와 무관한 «주소 계산».
# 출력: - k홉이면 이 차이가 k번 곱해진다. 그래서 «두 번째 홉부터 이득»이다.

# %% [markdown]
# ## 4단계 — 흉내가 «과장»하는 부분: 팬아웃
#
# 여기가 예제의 정직한 한계다. 정렬 배열의 이진 탐색은 **팬아웃 2**의 트리다.
# 실제 B-tree는 한 페이지에 수백 개의 키를 담아 팬아웃이 수백이다.
#
# $$\underbrace{d_2 = \log_2 (2E)}_{\text{예제}} \qquad\text{vs.}\qquad \underbrace{d_f = \log_f (2E) = \frac{\log_2 2E}{\log_2 f}}_{\text{실제 B-tree}}$$
#
# 8KB 페이지에 (4바이트 키 + 8바이트 포인터)를 채우면 팬아웃 $f \approx 8192/12 \approx 680$,
# 절반만 찬 상태를 가정해도 $f \approx 340$이다. $\log_2 340 \approx 8.4$이므로
# **예제는 실제 색인의 깊이를 8배 이상 과장한다.**

# %%
FANOUTS = (2, 128, 340, 680)
print(f"{'rows(2E)':>12} " + " ".join(f"{'f='+str(f):>8}" for f in FANOUTS))
for r in results:
    depths = [math.log(r["rows"], f) for f in FANOUTS]
    print(f"{r['rows']:>12,} " + " ".join(f"{d:>8.2f}" for d in depths))

print("\n10억 행 테이블까지 밀어 보면:")
for rows in (1_000_000, 100_000_000, 1_000_000_000):
    print(f"  {rows:>15,} 행 -> log2={math.log2(rows):5.1f}   f=340 -> {math.log(rows, 340):4.2f}   f=680 -> {math.log(rows, 680):4.2f}")
print(
    "\n실무 B-tree 의 깊이는 3~4 레벨에서 멈춘다. 그리고 상위 1~2 레벨은 버퍼 풀에 상주해서\n"
    "실제 디스크 접근은 흔히 1~2회다. 예제의 log2 곡선은 «깊어진다»는 방향만 맞고, «얼마나»는 틀리다."
)
# 출력:     rows(2E)      f=2    f=128    f=340    f=680
# 출력:       59,916    15.87     2.27     1.89     1.69
# 출력:      119,924    16.87     2.41     2.01     1.79
# 출력:      239,928    17.87     2.55     2.13     1.90
# 출력:      479,898    18.87     2.70     2.24     2.01
# 출력:      959,926    19.87     2.84     2.36     2.11
# 출력:
# 출력: 10억 행 테이블까지 밀어 보면:
# 출력:        1,000,000 행 -> log2= 19.9   f=340 -> 2.37   f=680 -> 2.12
# 출력:      100,000,000 행 -> log2= 26.6   f=340 -> 3.16   f=680 -> 2.82
# 출력:    1,000,000,000 행 -> log2= 29.9   f=340 -> 3.56   f=680 -> 3.18
# 출력:
# 출력: 실무 B-tree 의 깊이는 3~4 레벨에서 멈춘다. 그리고 상위 1~2 레벨은 버퍼 풀에 상주해서
# 출력: 실제 디스크 접근은 흔히 1~2회다. 예제의 log2 곡선은 «깊어진다»는 방향만 맞고, «얼마나»는 틀리다.

# %% [markdown]
# ## 5단계 — 흉내가 «생략»하는 부분: 시작 노드 찾기
#
# 예제에서 프로브는 정수 노드 번호다. 그래서 CSR은 `offset[u]`로 바로 간다.
# 하지만 현실의 질의는 「이름이 `user_12345`인 사람의 친구」다. **이름 → 내부 번호** 변환에는
# 그래프 DB도 색인이 필요하다. 색인 없이는 전체 훑기다.

# %%
n = 20_000
edges = make(n=n, avg_deg=12)
offset, nbr = build_csr(edges, n)
names = [f"user_{i:05d}" for i in range(n)]
name_sorted = sorted(names)          # 색인 있는 경우 (정렬 배열 + 이진 탐색)
name_to_id = {nm: i for i, nm in enumerate(names)}   # 해시 색인

targets = [names[rnd_probe.randrange(n)] for _ in range(500)]


def lookup_scan(nm):                 # 색인 없음: 전체 훑기
    for i, x in enumerate(names):
        if x == nm:
            return i
    return -1


def lookup_bisect(nm):               # B-tree 흉내
    i = bisect_left(name_sorted, nm)
    return i if i < len(name_sorted) and name_sorted[i] == nm else -1


def lookup_hash(nm):
    return name_to_id.get(nm, -1)


took = {}
for label, fn in (("전체 훑기", lookup_scan), ("정렬+이진탐색", lookup_bisect), ("해시 색인", lookup_hash)):
    t0 = time.perf_counter()
    for nm in targets:
        fn(nm)
    took[label] = (time.perf_counter() - t0) / len(targets) * 1e6
    print(f"  시작 노드 찾기 {label:<14} {took[label]:8.2f} us")

t0 = time.perf_counter()
for nm in targets:
    neighbors_csr(offset, nbr, name_to_id[nm])
dt_hop = (time.perf_counter() - t0) / len(targets) * 1e6
print(f"\n  (참고) 시작 노드를 안 뒤의 1홉                 {dt_hop:8.2f} us")
print(f"  -> 전체 훑기는 이진 탐색의 약 {took['전체 훑기']/took['정렬+이진탐색']:,.0f}배. 첫 홉의 색인은 «있으면 좋은 것»이 아니라 필수다.")
print("\n첫 진입은 색인이 필요하다. 인덱스 없는 인접성이 공짜로 만드는 건 «그 다음 홉»뿐이다.")
# 출력:   시작 노드 찾기 전체 훑기            341.56 us
# 출력:   시작 노드 찾기 정렬+이진탐색           0.55 us
# 출력:   시작 노드 찾기 해시 색인               0.37 us
# 출력:
# 출력:   (참고) 시작 노드를 안 뒤의 1홉                     0.36 us
# 출력:   -> 전체 훑기는 이진 탐색의 약 622배. 첫 홉의 색인은 «있으면 좋은 것»이 아니라 필수다.
# 출력:
# 출력: 첫 진입은 색인이 필요하다. 인덱스 없는 인접성이 공짜로 만드는 건 «그 다음 홉»뿐이다.

# %% [markdown]
# ## 6단계 — 시각화
#
# 왼쪽: 홉당 시간(가장 작은 크기 대비 배수). 오른쪽: 탐색 깊이 — 예제의 $\log_2$ 와
# 실제 B-tree의 $\log_f$, 그리고 CSR의 상수 0.

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    ns = [r["n"] for r in results]
    base_idx, base_csr = results[0]["t_idx"], results[0]["t_csr"]

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "홉당 시간 — 가장 작은 크기 대비 배수",
            "탐색 깊이 — 팬아웃이 곡선을 눌러 버린다",
        ),
    )

    fig.add_trace(
        go.Scatter(x=ns, y=[r["t_idx"] / base_idx for r in results], name="정렬 배열 + bisect_left",
                   mode="lines+markers", line=dict(color="#C0392B", width=3)),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=ns, y=[r["t_csr"] / base_csr for r in results], name="CSR offset[u] 직접 접근",
                   mode="lines+markers", line=dict(color="#1F77B4", width=3)),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=ns, y=[r["steps"] / results[0]["steps"] for r in results],
                   name="이진 탐색 비교 횟수 (결정적)", mode="lines+markers",
                   line=dict(color="#7F5A2E", width=2, dash="dash")),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=ns, y=[1.0] * len(ns), name="기준선 1.0x", mode="lines",
                   line=dict(color="#888", width=1, dash="dot"), showlegend=False),
        row=1, col=1,
    )

    for f, color, dash in ((2, "#C0392B", "solid"), (340, "#E67E22", "dash"), (680, "#F1C40F", "dash")):
        fig.add_trace(
            go.Scatter(x=ns, y=[math.log(r["rows"], f) for r in results],
                       name=f"log_{f}(2E)" + (" — 예제" if f == 2 else " — 실제 B-tree"),
                       mode="lines+markers", line=dict(color=color, width=3, dash=dash)),
            row=1, col=2,
        )
    fig.add_trace(
        go.Scatter(x=ns, y=[0] * len(ns), name="CSR = 탐색 0회", mode="lines+markers",
                   line=dict(color="#1F77B4", width=3)),
        row=1, col=2,
    )

    fig.update_xaxes(title_text="노드 수 (log 축)", type="log", row=1, col=1)
    fig.update_xaxes(title_text="노드 수 (log 축)", type="log", row=1, col=2)
    fig.update_yaxes(title_text="상대 시간 (배)", row=1, col=1)
    fig.update_yaxes(title_text="탐색 깊이 (레벨)", row=1, col=2)
    fig.update_layout(
        title="색인 흉내(정렬+이진탐색) vs 인덱스 없는 인접성(CSR offset)",
        template="plotly_white",
        width=1100,
        height=480,
        legend=dict(orientation="h", y=-0.22),
        margin=dict(t=90, b=110),
    )

    _show(fig)

    import pathlib

    out = pathlib.Path(__file__).parent / "expy.png" if "__file__" in dir() else pathlib.Path("expy.png")
    fig.write_image(str(out), scale=2)
    print(f"저장: {out}")
except ImportError as exc:
    print(f"시각화 건너뜀 (필요 패키지: plotly, kaleido) — {exc}")
# 필요 패키지: plotly, kaleido
# 출력: 저장: .../expy.png

# %% [markdown]
# ## 정리 — 흉내가 잡는 것과 놓치는 것
#
# | 관계형 B-tree 조인의 요소 | 예제가 흉내 내는가 | 비고 |
# |---|---|---|
# | 키 정렬 순서 위의 로그 시간 탐색 | **O** | `sorted` + `bisect_left`의 핵심 |
# | 매칭 행이 연속 구간에 모임 | **O** | `while keys[i] == u` |
# | 데이터가 커지면 깊이가 는다는 방향 | **O** | $\log_2 2E$가 $n$에 따라 오른다 |
# | 양방향 조회를 위한 중복 저장 | **O** | `rows`가 $2E$ 행 |
# | **팬아웃 수백** | **X** | 예제 팬아웃 2 → 깊이를 8배 이상 과장 |
# | **디스크/SSD 페이지 단위 I/O** | **X** | 전부 인메모리 리스트. 페이지 미스 비용이 없다 |
# | **상위 레벨의 버퍼 풀 상주** | **X** | 실제로는 루트·중간 레벨이 캐시돼 디스크 접근 1~2회 |
# | 커버링 인덱스 / 힙 페치 구분 | **X** | `rows[i][1]`이 곧 값. 랜덤 힙 접근이 없다 |
# | 조인 플래너 (해시/머지/중첩 루프 선택) | **X** | 방법이 하나로 고정 |
# | 잠금·MVCC·WAL | **X** | 읽기 전용 정적 배열 |
#
# **읽는 법**: 예제의 배수를 「관계형 DB가 그래프 DB보다 12배 느리다」로 읽으면 안 된다.
# 예제가 증명하는 것은 **비용의 «모양»**이다.
#
# $$C_{\text{색인}}(k\text{홉}) = \sum_{i=1}^{k}\big(d(\text{크기}) + \deg\big) \quad\text{vs}\quad C_{\text{CSR}}(k\text{홉}) = \sum_{i=1}^{k}\big(\underbrace{0}_{\text{탐색}} + \deg\big)$$
#
# 크기에 의존하는 항 $d(\text{크기})$가 홉마다 붙는지 아닌지 — 그게 인덱스 없는 인접성의 전부다.
# 실제 $d$는 예제보다 훨씬 작지만(3~4, 캐시되면 유효 1~2), **0은 아니다.**
