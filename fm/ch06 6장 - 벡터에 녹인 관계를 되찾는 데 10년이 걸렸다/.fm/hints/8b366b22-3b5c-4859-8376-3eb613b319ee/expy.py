# %% [markdown]
# # `ex2_graphrag_lite.py` 의 커뮤니티 탐지 = 라벨 전파(label propagation)
#
# **질문** — `ex2_graphrag_lite.py` 의 커뮤니티 탐지 알고리즘은 무엇인가?
#
# **답** — 라벨 전파(label propagation)를 직접 구현했다. 이웃에서 가장 흔한 라벨을
# 가져오는 과정을 몇 바퀴 돌리면 노드가 뭉친다.
#
# 이 노트북은 6장 회고 코퍼스(문서-원인-영역 트리플)로 라벨 전파를 **처음부터** 구현해서
#
# 1. 라운드마다 라벨이 어떻게 줄어드는지,
# 2. 최종 커뮤니티가 무엇인지,
# 3. 왜 이 알고리즘이 **비결정적**인지 (그리고 그게 답을 어떻게 흔드는지),
# 4. 어떻게 완화하는지
#
# 를 순서대로 본다.

# %%
import random
from collections import Counter, defaultdict

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


SEED = 20260811
# 출력: (없음)

# %% [markdown]
# ## 1. 코퍼스 — 6장 `corpus.py` 의 트리플
#
# 장애 회고 12건에서 뽑은 `(문서, 관계, 개념)` 트리플. 관계는 `원인` 또는 `영역`.
# 여기서는 `expy.py` 만으로 돌아가도록 그대로 옮겨 적었다.

# %%
TRIPLES = [
    ("d01", "원인", "재시도"), ("d01", "원인", "멱등성 없음"), ("d01", "영역", "결제"),
    ("d02", "원인", "중복 요청"), ("d02", "원인", "멱등성 없음"), ("d02", "영역", "프로모션"),
    ("d03", "원인", "캐시 만료"), ("d03", "영역", "배송"),
    ("d04", "원인", "재시도"), ("d04", "원인", "상태 불일치"), ("d04", "영역", "회원"),
    ("d05", "원인", "부분 실패"), ("d05", "원인", "롤백 없음"), ("d05", "영역", "정산"),
    ("d06", "원인", "재처리"), ("d06", "원인", "멱등성 없음"), ("d06", "영역", "알림"),
    ("d07", "원인", "외부 장애"), ("d07", "영역", "스토리지"),
    ("d08", "원인", "소비자 중단"), ("d08", "원인", "오프셋 밀림"), ("d08", "영역", "포인트"),
    ("d09", "원인", "중복 요청"), ("d09", "원인", "멱등성 없음"), ("d09", "영역", "주문"),
    ("d10", "원인", "관측 부재"), ("d10", "영역", "검색"),
    ("d11", "원인", "재시도"), ("d11", "원인", "부분 실패"), ("d11", "영역", "결제"),
    ("d12", "원인", "배포"), ("d12", "원인", "상태 초기화"), ("d12", "영역", "인증"),
]
GLOBAL_QUESTION = "우리 장애 회고 전체에서 반복되는 원인은 무엇인가?"
GROUND_TRUTH = {"멱등성 없음", "재시도"}


def build_graph(triples):
    """트리플을 무향 인접 리스트로. 관계 종류(원인/영역)는 버린다."""
    adj = defaultdict(set)
    for s, _p, o in triples:
        adj[s].add(o)
        adj[o].add(s)
    return adj


ADJ = build_graph(TRIPLES)
DOCS = sorted(n for n in ADJ if n.startswith("d") and n[1:].isdigit())
CONCEPTS = sorted(n for n in ADJ if n not in set(DOCS))

print(f"노드 {len(ADJ)}개 (문서 {len(DOCS)}, 개념 {len(CONCEPTS)}), 간선 {sum(len(v) for v in ADJ.values()) // 2}개")
print("허브 상위 5:", Counter({n: len(v) for n, v in ADJ.items()}).most_common(5))
# 출력: 노드 37개 (문서 12, 개념 25), 간선 33개
# 출력: 허브 상위 5: [('멱등성 없음', 4), ('d01', 3), ('재시도', 3), ('d02', 3), ('d04', 3)]

# %% [markdown]
# 그래프는 **문서 ↔ 개념** 이분(bipartite) 구조다. 문서끼리, 개념끼리 직접 이어진 간선은 없다.
# 그래서 문서 두 건이 같은 뭉치에 들어가려면 반드시 공유 개념(허브)을 거쳐야 한다.
# `멱등성 없음`(차수 4), `재시도`(차수 3)가 그 다리 역할을 한다 — 이게 뒤에서 커뮤니티를 만든다.

# %% [markdown]
# ## 2. 라벨 전파 — Raghavan, Albert, Kumara (2007)
#
# 원논문: *Near linear time algorithm to detect community structures in large-scale networks*,
# Phys. Rev. E **76**, 036106 ([arXiv:0709.2938](https://arxiv.org/abs/0709.2938)).
#
# 절차는 세 줄이다.
#
# 1. **초기화** — 모든 노드에 서로 다른 라벨을 준다. $\ell_v^{(0)} = v$
# 2. **갱신** — 노드를 (무작위) 순서로 훑으며 이웃의 최빈 라벨을 가져온다.
#
#    $$\ell_v \;\leftarrow\; \arg\max_{L}\; \bigl|\{\, u \in N(v) \;:\; \ell_u = L \,\}\bigr|$$
#
#    동률이면 그중 하나를 **무작위로** 고른다. 갱신은 **비동기(asynchronous)** — 방금 바꾼
#    라벨을 같은 라운드의 다음 노드가 곧바로 본다.
# 3. **정지** — 모든 노드가 이미 이웃 최빈 라벨 중 하나를 갖고 있으면 멈춘다.
#
#    $$\forall v:\quad \ell_v \in \arg\max_{L} \bigl|\{u \in N(v) : \ell_u = L\}\bigr|$$
#
# 라운드당 비용은 간선 수에 비례해 $O(m)$, 라운드 수가 거의 상수라서 **거의 선형**이다.
# 모듈도(modularity) 같은 **목적함수가 없다** — 그냥 지역 규칙의 반복일 뿐이다.
#
# `ex2_graphrag_lite.py` 의 구현은 여기서 두 군데를 바꿨다.
#
# | 원논문 | `ex2` 구현 |
# |---|---|
# | 노드 방문 순서 무작위 | `for n in sorted(adj)` — 이름 오름차순 고정 |
# | 동률 시 무작위 선택 | `Counter(...).most_common(1)` — 집합 순회 순서에 맡김 |
# | 정지 조건 = 라벨 안정 | `changed` 플래그 + `rounds=12` 상한 |
# | 모든 그룹 반환 | `len(v) > 1` 인 그룹만 (싱글톤 버림) |

# %%
def label_propagation_traced(adj, rounds=12, order=None, tie="min", rng=None):
    """ex2 와 같은 라벨 전파. 라운드별 스냅샷을 함께 돌려준다.

    tie="min"    : 동률이면 라벨 값이 가장 작은 것 (결정적)
    tie="random" : 동률이면 무작위 (원논문 방식)
    """
    nodes = sorted(adj)
    label = {n: i for i, n in enumerate(nodes)}
    history = [dict(label)]
    changes = []
    for _ in range(rounds):
        visit = list(nodes) if order is None else order(nodes, rng)
        changed = 0
        for n in visit:
            if not adj[n]:
                continue
            cnt = Counter(label[m] for m in sorted(adj[n]))
            top = max(cnt.values())
            cands = sorted(l for l, c in cnt.items() if c == top)
            best = min(cands) if tie == "min" else rng.choice(cands)
            if label[n] != best:
                label[n] = best
                changed += 1
        history.append(dict(label))
        changes.append(changed)
        if changed == 0:
            break
    return label, history, changes


def to_communities(label, min_size=2):
    groups = defaultdict(list)
    for n, l in label.items():
        groups[l].append(n)
    return sorted((sorted(v) for v in groups.values() if len(v) >= min_size),
                  key=lambda v: (-len(v), v))


label_d, hist_d, changes_d = label_propagation_traced(ADJ)
for r, (snap, ch) in enumerate(zip(hist_d[1:], changes_d), 1):
    print(f"라운드 {r}: 라벨 바뀐 노드 {ch:2d}개 → 남은 고유 라벨 {len(set(snap.values())):2d}개")
# 출력: 라운드 1: 라벨 바뀐 노드 28개 → 남은 고유 라벨  9개
# 출력: 라운드 2: 라벨 바뀐 노드  0개 → 남은 고유 라벨  9개

# %% [markdown]
# 37개 라벨이 **한 바퀴 만에 9개**로 떨어진다. 이게 라벨 전파가 빠른 이유다 —
# 비동기 갱신이라 라운드 안에서 라벨이 앞에서 뒤로 곧장 흘러간다.
# 두 번째 라운드에서 `changed == 0` 이 되어 조기 종료한다
# (`rounds=12` 는 진동을 막는 안전판일 뿐, 실제로는 2~5바퀴면 끝난다).

# %%
comms_d = to_communities(label_d)
print(f"최종 커뮤니티 {len(comms_d)}개 (크기 2 이상)\n")
for i, c in enumerate(comms_d, 1):
    docs = [n for n in c if n in set(DOCS)]
    concepts = [n for n in c if n not in set(DOCS)]
    print(f"  C{i} (n={len(c)}) 문서={docs}")
    print(f"          개념={concepts}")
# 출력: 최종 커뮤니티 9개 (크기 2 이상)
# 출력:
# 출력:   C1 (n=9) 문서=['d02', 'd06', 'd09']
# 출력:           개념=['멱등성 없음', '알림', '재처리', '주문', '중복 요청', '프로모션']
# 출력:   C2 (n=5) 문서=['d01', 'd11']
# 출력:           개념=['결제', '부분 실패', '재시도']
# 출력:   C3 (n=4) 문서=['d08']
# 출력:           개념=['소비자 중단', '오프셋 밀림', '포인트']
# 출력:   C4 (n=4) 문서=['d12']
# 출력:           개념=['배포', '상태 초기화', '인증']
# 출력:   C5 (n=3) 문서=['d03']
# 출력:           개념=['배송', '캐시 만료']
# 출력:   C6 (n=3) 문서=['d04']
# 출력:           개념=['상태 불일치', '회원']
# 출력:   C7 (n=3) 문서=['d05']
# 출력:           개념=['롤백 없음', '정산']
# 출력:   C8 (n=3) 문서=['d07']
# 출력:           개념=['스토리지', '외부 장애']
# 출력:   C9 (n=3) 문서=['d10']
# 출력:           개념=['검색', '관측 부재']

# %% [markdown]
# **C1 을 보라.** `멱등성 없음` 이라는 허브 하나가 `d02, d06, d09` 세 건을 한 뭉치로 끌어당겼다.
# `C2` 는 `재시도` 가 `d01, d11` 을 묶었다. 이게 이 예제가 노리는 그림이다 —
# 개별 문서를 따로 읽어서는 안 보이던 **반복 패턴**이, 색인 시점에 그래프를 뭉쳐 두면
# 커뮤니티 하나로 드러난다.
#
# 나머지 7개는 전부 «문서 1건 + 자기만 쓰는 개념» 짜리 파편이다. 문서 12건짜리 장난감
# 그래프에서 라벨 전파가 만들 수 있는 한계이고, 실제 GraphRAG 라면 여기서 계층을 한 겹
# 더 올려 다시 뭉친다 (뒤 6절).

# %% [markdown]
# ## 3. 요약을 접고, 질의 시점에 펴기
#
# `summarize()` 는 커뮤니티 안에서 **문서와 원인이 둘 다 같은 뭉치에 있는** 트리플만 센다.
# 즉 커뮤니티 분할이 곧 집계 단위다 — 분할이 흔들리면 답도 흔들린다는 뜻이다.

# %%
def summarize(community, triples):
    members = set(community)
    causes = Counter(o for s, p, o in triples
                     if p == "원인" and s in members and o in members)
    docs = sorted(m for m in members if m in set(DOCS))
    return {"문서": docs, "원인분포": causes}


def answer(communities, triples, k=2):
    total = Counter()
    for c in communities:
        total.update(summarize(c, triples)["원인분포"])
    return total, {c for c, _ in total.most_common(k)}


total_d, found_d = answer(comms_d, TRIPLES)
print("원인 순위:", total_d.most_common(5))
print(f"답: {sorted(found_d)} / 정답: {sorted(GROUND_TRUTH)} → {'맞음' if found_d == GROUND_TRUTH else '틀림'}")
# 출력: 원인 순위: [('멱등성 없음', 3), ('중복 요청', 2), ('재시도', 2), ('재처리', 1), ('부분 실패', 1)]
# 출력: 답: ['멱등성 없음', '중복 요청'] / 정답: ['멱등성 없음', '재시도'] → 틀림

# %% [markdown]
# **틀렸다.** 그리고 이건 버그가 아니라 이 카드가 보여 주려는 바로 그 지점이다.
#
# 위 구현은 `ex2` 와 알고리즘이 같고 **타이브레이크 규칙만 다르다**(`ex2` 는 집합 순회 순서,
# 여기서는 라벨 최솟값). 그것만으로 `d01` 이 `멱등성 없음` 쪽이 아니라 `재시도` 쪽으로 붙었고,
# `멱등성 없음` 카운트가 4에서 3으로 내려가 `재시도`(2) 와 `중복 요청`(2) 이 동률이 되었다.
# 동률에서 `Counter.most_common` 이 `중복 요청` 을 먼저 뽑아 답이 뒤집혔다.

# %% [markdown]
# ## 4. 비결정성 — 이 알고리즘의 진짜 함정
#
# 라벨 전파에는 **두 개의 자유도**가 있고, 둘 다 결과를 바꾼다.
#
# 1. **노드 방문 순서** — 비동기 갱신이라 누구를 먼저 보느냐가 라벨의 흐름 방향을 정한다.
# 2. **동률 타이브레이크** — 이분 그래프에서 차수 2짜리 노드는 거의 항상 1:1 동률이다.
#
# `ex2` 는 순서를 `sorted(adj)` 로 고정했으니 1번은 막았다. 하지만 2번은 열려 있다:
#
# ```python
# best = Counter(label[m] for m in adj[n]).most_common(1)[0][0]
# ```
#
# `adj[n]` 은 **`set`** 이고, 파이썬 문자열 해시는 프로세스마다 무작위화(`PYTHONHASHSEED`)된다.
# `Counter` 는 동률을 삽입 순서로 깨므로, **집합 순회 순서 = 해시 시드**가 타이브레이크를 정한다.
# 즉 `ex2_graphrag_lite.py` 는 같은 입력으로 **실행할 때마다 다른 커뮤니티**를 낸다.
#
# 아래에서 두 자유도를 명시적으로 흔들어 그 폭을 재 본다.

# %%
def shuffled(nodes, rng):
    v = list(nodes)
    rng.shuffle(v)
    return v


rng = random.Random(SEED)
trials = []
for _ in range(300):
    lab, _h, _c = label_propagation_traced(ADJ, order=shuffled, tie="random", rng=rng)
    cs = to_communities(lab)
    _tot, fnd = answer(cs, TRIPLES)
    trials.append((len(cs), max(len(c) for c in cs), tuple(sorted(fnd))))

n_comm = Counter(t[0] for t in trials)
print("커뮤니티 개수 분포:", dict(sorted(n_comm.items())))
print("최대 커뮤니티 크기 분포:", dict(sorted(Counter(t[1] for t in trials).items())))
# 출력: 커뮤니티 개수 분포: {7: 1, 8: 50, 9: 154, 10: 93, 11: 2}
# 출력: 최대 커뮤니티 크기 분포: {4: 2, 6: 87, 7: 27, 8: 56, 9: 53, 10: 25, 11: 22, 13: 12, 14: 15, 16: 1}

# %%
ans = Counter(t[2] for t in trials)
correct = sum(n for a, n in ans.items() if set(a) == GROUND_TRUTH)
print(f"정답({sorted(GROUND_TRUTH)}) 적중률: {correct}/300 = {correct / 300:.1%}\n")
for a, n in ans.most_common(6):
    mark = "  ← 정답" if set(a) == GROUND_TRUTH else ""
    print(f"  {n:3d}회 ({n / 300:5.1%})  {list(a)}{mark}")
# 출력: 정답(['멱등성 없음', '재시도']) 적중률: 101/300 = 33.7%
# 출력:
# 출력:   125회 (41.7%)  ['멱등성 없음', '중복 요청']
# 출력:   101회 (33.7%)  ['멱등성 없음', '재시도']  ← 정답
# 출력:    44회 (14.7%)  ['재시도', '중복 요청']
# 출력:    30회 (10.0%)  ['부분 실패', '재시도']

# %% [markdown]
# 여기가 이 카드의 핵심 교훈이다. **커뮤니티 개수가 7~11 사이에서 출렁이고
# (최대 커뮤니티 크기는 4~16), 그에 따라 최종 답도 네 가지로 갈린다.**
# 정답이 나오는 건 300회 중 101회, **33.7%** 뿐이다.
#
# 그러니 책 본문의 "맞았나: 예" 는 알고리즘의 보증이 아니라 **그 실행에서의 운**이다.
# 실제로 `ex2_graphrag_lite.py` 를 여러 번 돌려 보면 답이 달라진다 — 이 예제 자체가
# `adj[n]` 의 `set` 순회 순서에 걸려 있기 때문이다:
#
# ```bash
# for i in 1 2 3 4 5; do python3 ex2_graphrag_lite.py | grep '^답:'; done
# # 답: ['멱등성 없음', '재시도']
# # 답: ['재시도', '중복 요청']
# # 답: ['재시도', '중복 요청']
# # 답: ['재시도', '캐시 만료']
# # 답: ['부분 실패', '재시도']
# ```
#
# 그래도 예제의 논지는 무너지지 않는다. 논지는 "라벨 전파가 정확하다" 가 아니라
# **"세는 시점을 색인 시점으로 옮기면 전역 질문에 답할 창구가 생긴다"** 이기 때문이다.
# 라벨 전파는 그 창구를 20줄로 만들어 보여 주는 자리 표시자(placeholder)이고,
# 이 흔들림이야말로 실제 GraphRAG 가 굳이 Leiden 을 쓰는 이유이기도 하다.

# %% [markdown]
# ## 5. 완화 — 세 가지 방법
#
# | 방법 | 하는 일 | 대가 |
# |---|---|---|
# | **결정적 타이브레이크** | 동률이면 라벨 최솟값. `sorted(adj[n])` 로 순회 | 재현되지만 이름 순 편향이 생김 |
# | **시드 고정 + 여러 번** | `random.Random(seed)`, 순서를 재현 가능하게 섞기 | 여전히 시드에 따라 다른 답 |
# | **합의 클러스터링(consensus)** | $R$ 회 돌려 "같은 뭉치에 든 비율" 행렬을 만들고 임계값으로 자름 | 비용 $R$ 배 |
#
# 합의 클러스터링만 실제로 돌려 본다 (Lancichinetti & Fortunato 2012 의 아이디어를 축약).

# %%
def consensus(adj, runs=200, thr=0.6, seed=SEED):
    r = random.Random(seed)
    nodes = sorted(adj)
    co = Counter()
    for _ in range(runs):
        lab, _h, _c = label_propagation_traced(adj, order=shuffled, tie="random", rng=r)
        by = defaultdict(list)
        for n, l in lab.items():
            by[l].append(n)
        for grp in by.values():
            g = sorted(grp)
            for i in range(len(g)):
                for j in range(i + 1, len(g)):
                    co[(g[i], g[j])] += 1
    # 동반출현 비율 >= thr 인 쌍만 남기고 union-find
    parent = {n: n for n in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for (a, b), c in co.items():
        if c / runs >= thr:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
    lab2 = {n: find(n) for n in nodes}
    return to_communities(lab2), co


comms_c, co = consensus(ADJ)
print(f"합의 커뮤니티 {len(comms_c)}개 (200회, 임계값 0.6)")
for i, c in enumerate(comms_c, 1):
    print(f"  C{i}: {c}")
# 출력: 합의 커뮤니티 10개 (200회, 임계값 0.6)
# 출력:   C1: ['d02', 'd09', '멱등성 없음', '주문', '중복 요청', '프로모션']
# 출력:   C2: ['d01', 'd11', '결제', '재시도']
# 출력:   C3: ['d08', '소비자 중단', '오프셋 밀림', '포인트']
# 출력:   C4: ['d12', '배포', '상태 초기화', '인증']
# 출력:   C5: ['d03', '배송', '캐시 만료']
# 출력:   C6: ['d04', '상태 불일치', '회원']
# 출력:   C7: ['d05', '롤백 없음', '정산']
# 출력:   C8: ['d06', '알림', '재처리']
# 출력:   C9: ['d07', '스토리지', '외부 장애']
# 출력:   C10: ['d10', '검색', '관측 부재']

# %%
# 가장 안정적인 쌍 / 가장 불안정한 쌍
pairs = sorted(co.items(), key=lambda kv: -kv[1])
print("항상 같이 묶이는 쌍 (상위 5):")
for (a, b), c in pairs[:5]:
    print(f"  {c / 200:5.1%}  {a} — {b}")
print("\n애매한 쌍 (0.4~0.6, 상위 5):")
for (a, b), c in [p for p in pairs if 0.4 <= p[1] / 200 <= 0.6][:5]:
    print(f"  {c / 200:5.1%}  {a} — {b}")
# 출력: 항상 같이 묶이는 쌍 (상위 5):
# 출력:  100.0%  d04 — 상태 불일치
# 출력:  100.0%  d04 — 회원
# 출력:  100.0%  상태 불일치 — 회원
# 출력:  100.0%  d02 — 프로모션
# 출력:  100.0%  d09 — 주문
# 출력:
# 출력: 애매한 쌍 (0.4~0.6, 상위 5):
# 출력:   55.0%  d05 — 부분 실패
# 출력:   55.0%  롤백 없음 — 부분 실패
# 출력:   55.0%  부분 실패 — 정산
# 출력:   53.0%  d11 — 부분 실패
# 출력:   52.0%  결제 — 부분 실패

# %% [markdown]
# 합의가 준 것은 **안정된 10개 분할**과, 그보다 값진 **불확실성의 지도**다.
#
# - `d04 — 상태 불일치 — 회원` 처럼 잎(차수 1)이 자기 문서에 붙는 쌍은 **100%** 로 굳는다.
# - `부분 실패` 는 `d05`(정산)와 `d11`(결제) **양쪽에 걸친 다리**라서 50~55% 에서 진동한다.
#   어느 쪽으로 갈지 알고리즘이 확신하지 못한다는 뜻이고, 앞 절에서 답이 흔들린 원인 중 하나다.
#
# 200회 합의는 결과를 안정시키는 대신 **비용을 200배** 쓴다. 그럴 바에는 애초에
# **모듈도를 최적화하고 연결성을 보장하는 알고리즘**을 쓰는 게 맞다 — 그게 다음 절이다.

# %% [markdown]
# ## 6. 왜 Louvain/Leiden 이 아니라 라벨 전파였나
#
# | | 라벨 전파 (2007) | Louvain (2008) | Leiden (2019) |
# |---|---|---|---|
# | 목적함수 | **없음** (지역 규칙) | 모듈도 $Q$ 탐욕 최적화 | 모듈도/CPM + refinement |
# | 계층 구조 | 없음 (평평한 1단) | 있음 (aggregate 반복) | 있음 |
# | 보증 | 없음 | 커뮤니티가 **끊길 수** 있음 | 연결성 보장, 수렴 시 국소 최적 |
# | 구현 난이도 | **~20줄, 의존성 0** | 수백 줄 | 라이브러리 필수 |
# | 결정성 | 순서/타이 의존 | 순서 의존 | 순서 의존 (시드 고정 필요) |
#
# 모듈도는
#
# $$Q = \frac{1}{2m}\sum_{i,j}\Bigl[A_{ij} - \frac{k_i k_j}{2m}\Bigr]\delta(c_i, c_j)$$
#
# 인데, 라벨 전파는 이 $Q$ 를 **쳐다보지도 않는다**. 그래서 빠르고, 그래서 보증이 없다.
#
# **책이 라벨 전파를 고른 이유는 하나다: 6장 예제의 원칙이 "의존성 없음"이기 때문.**
# `python-louvain`/`igraph`/`graspologic` 를 `pip install` 하게 만드는 순간
# 독자가 보려던 것(= 언제 접느냐)이 설치 안내에 묻힌다.
#
# **실제 Microsoft GraphRAG 는 Leiden 을 쓴다.** 그것도 평평한 Leiden 이 아니라
# **계층적 Leiden**(`graspologic` 의 `hierarchical_leiden`)이다. 큰 커뮤니티를 크기 상한
# (기본 `max_cluster_size=10`) 아래로 쪼개질 때까지 재귀적으로 나눠서, 레벨 0/1/2… 의
# 커뮤니티 트리를 만든다. 그 트리의 **레벨마다 요약(community report)을 LLM 이 작성**하고,
# 전역 질의는 이 레벨을 골라 map-reduce 로 훑는다.
#
# `ex2` 에 없는 것을 정리하면:
#
# - 계층 (다중 해상도 요약 → 질문 규모에 맞춰 레벨 선택)
# - 모듈도/CPM 기반 품질 보증과 해상도 파라미터
# - 커뮤니티 연결성 보장 (Leiden 의 refinement 단계)
# - 가중 간선 (GraphRAG 는 엔티티 쌍의 동시 등장 횟수를 가중치로 씀)
# - LLM 요약 (`ex2` 는 `Counter` 규칙 기반)

# %% [markdown]
# ## 7. 시각화
#
# 왼쪽 위: 라운드별 남은 고유 라벨 수 — 결정적 실행 vs 무작위 순서 20회.
# 오른쪽 위: 300회 시행의 커뮤니티 개수 분포 (비결정성의 폭).
# 아래: 이분 그래프 레이아웃 — 결정적 실행의 커뮤니티로 색칠.

# %%
PALETTE = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2",
           "#B279A2", "#EECA3B", "#FF9DA6", "#9D755D", "#BAB0AC"]

# (a) 라벨 수 감소 곡선
rng2 = random.Random(SEED + 1)
random_curves = []
for _ in range(20):
    _l, h, _c = label_propagation_traced(ADJ, order=shuffled, tie="random", rng=rng2)
    random_curves.append([len(set(s.values())) for s in h])
det_curve = [len(set(s.values())) for s in hist_d]

fig = make_subplots(
    rows=2, cols=2,
    row_heights=[0.34, 0.66],
    specs=[[{}, {}], [{"colspan": 2}, None]],
    subplot_titles=("(a) 라운드별 남은 고유 라벨 수",
                    "(b) 300회 시행의 커뮤니티 개수",
                    "(c) 문서↔개념 이분 그래프 — 결정적 실행의 커뮤니티"),
    vertical_spacing=0.13,
)

for i, cur in enumerate(random_curves):
    fig.add_trace(go.Scatter(x=list(range(len(cur))), y=cur, mode="lines",
                             line=dict(color="rgba(120,130,150,0.35)", width=1),
                             showlegend=(i == 0), name="무작위 순서 20회"),
                  row=1, col=1)
fig.add_trace(go.Scatter(x=list(range(len(det_curve))), y=det_curve, mode="lines+markers",
                         line=dict(color="#E45756", width=3), marker=dict(size=8),
                         name="ex2 (고정 순서)"), row=1, col=1)
fig.update_xaxes(title_text="라운드", dtick=1, row=1, col=1)
fig.update_yaxes(title_text="고유 라벨 수", row=1, col=1)

# (b) 커뮤니티 개수 히스토그램
ks = sorted(n_comm)
fig.add_trace(go.Bar(x=ks, y=[n_comm[k] for k in ks], marker_color="#4C78A8",
                     text=[n_comm[k] for k in ks], textposition="outside",
                     showlegend=False), row=1, col=2)
fig.add_vline(x=len(comms_d), line_dash="dash", line_color="#E45756", row=1, col=2)
fig.update_xaxes(title_text="커뮤니티 개수", dtick=1, row=1, col=2)
fig.update_yaxes(title_text="시행 수", row=1, col=2)

# (c) 이분 그래프
comm_of = {}
for i, c in enumerate(comms_d):
    for n in c:
        comm_of[n] = i
pos = {}
doc_row = {n: i * (len(CONCEPTS) - 1) / max(len(DOCS) - 1, 1) for i, n in enumerate(DOCS)}
for n in DOCS:
    pos[n] = (0.0, -doc_row[n])
# 개념은 «이어진 문서들의 평균 높이»(barycenter) 순으로 놓아 선 교차를 줄인다
bary = sorted(CONCEPTS, key=lambda n: (sum(doc_row[m] for m in ADJ[n] if m in doc_row)
                                       / max(sum(1 for m in ADJ[n] if m in doc_row), 1), n))
for i, n in enumerate(bary):
    pos[n] = (1.0, -float(i))
CONCEPTS = bary

ex, ey = [], []
for s, _p, o in TRIPLES:
    ex += [pos[s][0], pos[o][0], None]
    ey += [pos[s][1], pos[o][1], None]
fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines",
                         line=dict(color="rgba(140,150,165,0.45)", width=1),
                         hoverinfo="skip", showlegend=False), row=2, col=1)

for side, names, anchor in (("문서", DOCS, "right"), ("개념", CONCEPTS, "left")):
    fig.add_trace(go.Scatter(
        x=[pos[n][0] for n in names], y=[pos[n][1] for n in names],
        mode="markers+text", text=names, textposition=f"middle {anchor}",
        textfont=dict(size=10),
        marker=dict(size=[13 if len(ADJ[n]) > 2 else 9 for n in names],
                    color=[PALETTE[comm_of[n] % len(PALETTE)] if n in comm_of else "#CCCCCC"
                           for n in names],
                    line=dict(color="white", width=1)),
        hovertext=[f"{n} · 차수 {len(ADJ[n])} · C{comm_of.get(n, -1) + 1}" for n in names],
        hoverinfo="text", showlegend=False), row=2, col=1)

fig.update_xaxes(visible=False, range=[-0.45, 1.55], row=2, col=1)
fig.update_yaxes(visible=False, row=2, col=1)

fig.update_layout(
    title="라벨 전파 — ex2_graphrag_lite.py 의 커뮤니티 탐지",
    height=1000, width=1150, template="plotly_white",
    legend=dict(orientation="h", y=1.06, x=0.0),
    margin=dict(l=60, r=30, t=110, b=50),
)
_show(fig)

fig.write_image("expy.png", scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 한 줄 정리
#
# `ex2_graphrag_lite.py` 의 커뮤니티 탐지는 **라벨 전파** — 이웃의 최빈 라벨을 가져오는
# 규칙을 몇 바퀴 돌리는 것뿐이다. 의존성 없이 20줄로 되니까 골랐고, 그 대가로
# **목적함수도 계층도 결정성도 없다.** 실제 GraphRAG 는 같은 자리에 **계층적 Leiden** 을 놓는다.
