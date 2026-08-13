# 그래프 데이터베이스가 조인보다 빠른 두 가지 이유는 무엇인가?

> **정답**: 절반은 인덱스 없는 인접성이고, 나머지 절반은 3장에서 본 「중간 결과가 곱해지지 않는다」는 점이다.

## 한 줄 핵심

두 이유는 **서로 다른 층에 있다.** 인덱스 없는 인접성은 **저장 계층**의 성질이다 — 「이웃 하나를 찾는 값이 얼마인가」. 중간 결과가 곱해지지 않는다는 것은 **실행 계층**의 성질이다 — 「홉을 겹칠 때 비용이 어떻게 늘어나는가」. 그래서 하나를 고쳐도 나머지는 그대로 남는다. 그리고 이 비대칭이 중요한 이유는, **2020년 전후로 관계형 진영이 두 번째 절반을 상당히 따라잡았지만 첫 번째 절반은 여전히 저장 구조의 차이로 남아 있기** 때문이다.

---

## 이유 ①: 인덱스 없는 인접성 — 홉 하나의 값

### 무엇이 다른가

| | 이웃을 찾는 방법 | 데이터가 늘면 |
|---|---|---|
| 관계형 | `friends(a)` 색인을 탄다. B-트리를 뿌리에서 잎까지 내려간다 | 트리가 **깊어진다** |
| 그래프 | 노드가 이웃 목록의 **주소를 직접 들고 있다**. 따라간다 | **그대로다** |

비용으로 쓰면 홉 하나가

$$T_{\text{색인}} = O(\log |E|) \quad\text{대}\quad T_{\text{직접}} = O(1)$$

이다. 로그는 작지만 **전체 크기에 의존한다**는 게 요점이다. $O(1)$은 의존하지 않는다.

### `ex5_index_free.py`가 실제로 잰 값

정렬 배열 + 이진 탐색으로 색인을 흉내 내고, `dict of list`로 직접 접근을 흉내 낸 결과다(평균 차수 12).

| 노드 수 | 색인 방식 | 직접 방식 | 배수 | 이론 색인 깊이 $\log_2 \lvert E \rvert$ |
|---:|---:|---:|---:|---:|
| 10,000 | 2.84 us | 0.20 us | **14.2x** | 16.9 |
| 100,000 | 4.94 us | 0.27 us | **18.3x** | 20.2 |

읽어야 할 지점은 배수가 아니라 **배수의 추세**다. 노드를 10배로 키웠을 때

- 색인 방식: 2.84 → 4.94 us (**1.7배 증가**). 트리 깊이가 16.9 → 20.2로 20% 깊어진 것에 캐시 미스가 얹혔다.
- 직접 방식: 0.20 → 0.27 us (**1.35배**). 이 증가분은 알고리즘이 아니라 파이썬 dict가 커져서 생긴 캐시 효과다.

10배가 아니라 100배, 10,000배로 키우면 이 격차가 계속 벌어진다. 색인은 로그로 자라고 직접 접근은 자라지 않기 때문이다.

### 정직하게 붙여야 할 단서 세 개

**(1) 시작 노드에는 여전히 색인이 필요하다.** 8장 「한 장 요약」이 못 박은 문장이다 — 「인덱스 없는 인접성은 **두 번째 홉부터** 이득입니다」. `MATCH (p:Person {name: "김영희"})`는 이름 색인 없이는 전체 훑기다. 즉 $k$홉 질의의 진짜 비용은

$$T = \underbrace{O(\log N)}_{\text{앵커 찾기, 한 번}} + \underbrace{k \cdot O(1)\text{급 홉}}_{\text{여기가 이득}}$$

이고, $k = 1$이면 앞 항이 전체를 지배한다. **1홉 질의에서는 그래프 DB가 관계형보다 빠를 이유가 거의 없다.**

**(2) $O(1)$은 「공짜」가 아니라 「무작위 접근」이다.** 포인터 추적은 캐시 줄과 디스크 페이지를 예측 불가능하게 건드린다. 8장 `ex4_relabel.py`가 이 문제를 정면으로 다룬다 — 캐시 한 줄 64바이트에 4바이트 정수 16개가 들어오는데, 이웃 번호가 평균 수천 떨어져 있으면 **매번 새 줄을 가져온다.** 데이터가 메모리를 넘어서면 이 무작위 접근이 순차 스캔보다 훨씬 비싸진다.

**(3) 슈퍼 노드에서는 상수 인자가 무의미해진다.** 차수 100만인 노드의 이웃 목록을 $O(1)$에 「찾는」 것은 맞지만, 그 목록을 **읽는** 데 100만 번이 든다. `ex3_degree_skew.py`가 말하는 대로 2홉 비용은

$$C_{2\text{홉}} = \sum_{v} d(v)^2$$

이고, 평균 차수가 같아도 이 값은 자릿수로 다를 수 있다.

---

## 이유 ②: 중간 결과가 곱해지지 않는다 — 홉을 겹칠 때

### 무엇이 다른가

이유 ①이 홉 **하나**의 값이라면, 이것은 홉을 **겹쳤을 때** 값이 어떻게 늘어나는지의 문제다. 훨씬 크다.

$k$홉 친구를 찾는 SQL은 같은 표를 $k$번 조인한다.

```sql
SELECT COUNT(DISTINCT f4.b) FROM friends f1
  JOIN friends f2 ON f2.a = f1.b
  JOIN friends f3 ON f3.a = f2.b
  JOIN friends f4 ON f4.a = f3.b
WHERE f1.a = ?
```

이진 조인 엔진은 이걸 **왼쪽에서 오른쪽으로 하나씩** 붙인다. 각 단계에서 나오는 행 수는 대략

$$|T_k| \approx \bar{d}^{\,k}$$

즉 **곱셈으로 자란다.** 평균 차수 12면 4홉에서 $12^4 \approx 20{,}700$행이다. 그런데 실제 도달 노드는 훨씬 적다 — 200명짜리 그래프에서 4홉이면 이미 거의 전원이라 **200 미만**이다. 나머지는 전부 버려질 중복 경로다.

순회는 이 낭비를 안 한다. 홉마다 **집합으로 접어 버리기** 때문이다.

$$C_{\text{순회}} = \sum_{i=1}^{k} \sum_{u \in F_i} d(u), \qquad F_i = \text{(중복 제거된 } i\text{홉 프런티어)}$$

프런티어가 노드 집합으로 접히니 $|F_i| \le N$이 항상 성립한다. **곱해질 여지가 없다.**

### `ex2_sql_vs_graph.py`(3장)가 실제로 잰 값

사람 200명, 친구 관계 1,163개(양방향 2,326행). 색인은 공평하게 줬다.

| 홉 | SQL 조인 | 그래프 순회 | 배수 |
|---:|---:|---:|---:|
| 1 | 0.01 ms | 0.001 ms | 12x |
| 2 | 0.04 ms | 0.005 ms | 9x |
| 3 | 0.32 ms | 0.024 ms | 13x |
| 4 | **3.86 ms** | **0.041 ms** | **95x** |

SQL 쪽만 보면 3홉 → 4홉에서 **12배** 뛴다(0.32 → 3.86). 순회 쪽은 1.7배(0.024 → 0.041)다. 이 격차가 「곱해진다 대 안 곱해진다」의 전부다. **200명짜리 장난감 그래프에서** 이미 95배가 났다는 게 요점이다. 규모의 문제가 아니라 **점근 형태의 문제**다.

---

## 이 절반은 현대 RDBMS가 상당히 따라잡았다

여기가 정직하게 다뤄야 하는 부분이다. 「조인은 중간 결과가 곱해진다」는 **관계 모델의 성질이 아니고, 이진 조인 엔진의 성질이다.** 그리고 이진 조인은 관계형이 반드시 써야 하는 게 아니다.

### AGM 상한: 「곱해진다」가 왜 잘못인지의 정리

Atserias, Grohe, Marx(2008)가 조인 결과 크기의 **꼭 맞는(tight) 최악 상한**을 증명했다. 삼각형 질의

$$Q(a,b,c) = R(a,b) \bowtie S(b,c) \bowtie T(a,c), \qquad |R|,|S|,|T| \le N$$

의 출력은 최대 $O(N^{3/2})$개다. 그런데 **어떤 이진 조인 계획도** 최악의 경우 $\Omega(N^2)$ 시간이 걸린다. 두 관계를 먼저 붙이면 그 중간 결과가 $N^2$까지 커지고, 사영(projection)을 끼워 넣어도 못 피한다. 즉 이진 조인 엔진은 **답보다 다항식만큼 큰 중간 결과**를 만든다. 이게 「곱해진다」의 정확한 형태다.

### WCOJ: 그 간극을 메우는 알고리즘

**최악 최적 조인(worst-case optimal join, WCOJ)** 은 실행 시간이 AGM 상한과 일치하는 조인 알고리즘이다. 표 두 개씩 붙이는 대신 **변수(속성) 하나씩** 값을 정하고, 그 값을 만족하는 후보를 모든 관계에서 **동시에 교집합**한다. 삼각형이면 $O(N^{3/2})$에 끝난다.

| 알고리즘 | 나온 곳 |
|---|---|
| NPRR | Ngo, Porat, Ré, Rudra (2012) |
| Leapfrog Triejoin | Veldhuizen (LogicBlox, 2014) |
| Generic Join | Ngo, Ré, Rudra (2014) |

구조를 보면 알 수 있는데, **WCOJ의 「변수 하나씩 확장하고 교집합」은 그래프 순회와 사실상 같은 모양이다.** 관계형이 그래프 순회의 아이디어를 조인 알고리즘으로 형식화해 흡수한 셈이다.

### Yannakakis: 비순환 질의는 1981년에 이미 풀렸다

그리고 **$k$홉 체인 질의는 비순환(acyclic)** 이다. 3장의 그 95배 예제가 정확히 이 부류다.

Yannakakis(1981)와 Bernstein 등(1981)이 비순환 질의를 **입력과 출력의 합에 선형**으로 푸는 알고리즘을 냈다.

$$T_{\text{Yannakakis}} = O(\text{IN} + \text{OUT})$$

방법은 조인 전에 **세미조인(semi-join)을 두 번 통과시켜** 어느 출력 행에도 기여하지 못하는 입력 튜플을 미리 잘라내는 것이다. 남은 중간 튜플은 전부 최종 답에 기여한다 — **버려질 중간 결과가 정의상 0이다.** 이건 인스턴스 최적(instance-optimal)이라는 강한 보장이다.

**즉, 이론적으로 3장의 95배는 관계 모델의 한계가 아니었다.** SQLite가 1981년 알고리즘을 안 쓰는 이진 조인 엔진이라서 난 숫자다.

### 실제 시스템은 어디까지 왔나

- **LogicBlox**: leapfrog triejoin을 상용 엔진에 넣은 첫 사례.
- **EmptyHeaded**: WCOJ 기반 질의 엔진 연구 시스템.
- **Umbra**: 「Adopting Worst-Case Optimal Joins in Relational Database Systems」(Freitag 등, VLDB 2020) — 이름 그대로 WCOJ를 범용 RDBMS 옵티마이저에 통합했다.
- **DuckDB**: 술어 전달(predicate transfer) / 견고한 술어 전달(Robust Predicate Transfer) 계열 작업으로 비순환 질의에서 Yannakakis급 보장을 되살리는 방향.
- **SplitJoin**: 입력을 heavy/light로 쪼개 부분마다 다른 계획을 쓰는 프론트엔드. DuckDB와 Umbra 위에 얹어 중간 결과를 줄인다.
- **거꾸로 그래프 DB도 흡수했다**: Kuzu, GraphflowDB 같은 그래프 DBMS는 **이진 조인과 WCOJ를 섞는** 옵티마이저를 쓴다. 순회만으로는 순환 패턴(삼각형, 사각형)에서 최적이 아니라는 걸 알기 때문이다.

정리하면, **두 진영이 서로의 절반을 가져가는 중이다.** 관계형은 WCOJ/Yannakakis로 이유 ②를 메웠고, 그래프는 WCOJ로 순환 패턴 질의를 메웠다. 남은 진짜 구조적 차이는 이유 ①의 저장 배치다 — 그리고 그것도 클러스터형 색인, 커버링 색인, 정렬된 컬럼 저장으로 부분적으로 좁혀진다.

### 남는 구별

| | 이유 ① 인덱스 없는 인접성 | 이유 ② 중간 결과 |
|---|---|---|
| 층 | 저장 배치 | 실행 알고리즘 |
| 관계형이 따라잡았나 | **부분적** (클러스터형/커버링 색인, 컬럼 저장) | **상당히** (WCOJ, Yannakakis, 술어 전달) |
| 아직 남은 차이 | 앵커 이후의 홉당 상수 인자 | 옵티마이저가 그 계획을 **골라 줄지**가 실무 변수 |

두 번째 행의 마지막 항이 실무에서 가장 자주 문제가 된다. WCOJ를 **구현한** 엔진이라도 옵티마이저가 통계를 잘못 읽으면 이진 조인 계획을 고른다. 그래프 DB는 「순회」가 기본값이라 그 실수를 할 여지가 적다. 이건 알고리즘의 우위가 아니라 **기본값의 우위**다.

---

## 반례: 조인이 더 빠른 질의들

「그래프가 빠르다」는 조건부 명제다. 조건이 깨지는 경우다.

### (1) 프런티어가 넓을 때 — 순차 스캔이 포인터 추적을 이긴다

인덱스 없는 인접성은 **선택적일 때** 이긴다. 데이터의 큰 비율을 건드리면 뒤집힌다. 노드 200,000개 / 엣지 1,199,954개 CSR에서, 같은 답을 내는 두 방식을 재 봤다.

| 프런티어 | 포인터 추적(순회식) | 순차 스캔(집합/조인식) | 승자 |
|---|---:|---:|---|
| 전체 (100%) | 207.2 ms | **25.6 ms** | **스캔 8.1x** |
| 0.1% | **0.15 ms** | 25.5 ms | **순회 166x** |

같은 그래프, 같은 자료 구조, 같은 정답이다. **바뀐 건 선택도 하나다.** 프런티어가 전체면 순회는 무작위 접근 200,000번을 하고, 스캔은 캐시 프리페처가 완벽히 예측하는 순차 읽기 한 번을 한다. 8배 차이가 나는데, 이 8배가 바로 관계형 엔진이 해시 조인과 벡터화 실행에 걸고 있는 판돈이다.

실무 번역: **"모든 사용자의 모든 주문을 집계하라"** 는 그래프 순회로 풀 질의가 아니다.

### (2) 전역 집계

`GROUP BY` / `SUM` / 정렬처럼 **모든 행을 한 번씩 읽고 접는** 작업은 관계형의 홈그라운드다. 컬럼 저장 + 벡터화 실행 + SIMD가 전부 여기에 맞춰 설계돼 있다. 벤치마크 문헌도 같은 결론이다 — 관계형은 그룹화·정렬·집계 조합에서, 그래프는 다중 조인·패턴 매칭·경로 탐색에서 각각 우세하다.

### (3) 1홉 질의

위에서 본 대로 $k=1$이면 비용이 앵커 조회에 지배된다. 3장 예제조차 「1홉에서는 표가 밀리지 않는다. 오히려 빠를 때도 있다」고 적어 뒀다. 색인 하나 탄 뒤 이웃 목록을 읽는 일에서 두 시스템은 하는 일이 같다.

### (4) 술어가 아주 선택적일 때

중간 결과 폭발은 **필터가 약할 때** 생긴다. `WHERE f1.created_at > ? AND f4.city = ?` 처럼 각 단계가 강하게 걸러지면 옵티마이저가 그 술어를 밀어 넣어(predicate pushdown) 중간 결과를 처음부터 작게 유지한다. 이 경우 곱셈이 애초에 일어나지 않는다.

### (5) 슈퍼 노드를 지나는 질의

차수가 극단적으로 쏠린 그래프에서 순회는 $\sum_v d(v)^2$의 지배를 받는다. `ex3_degree_skew.py`가 보여 준 그대로, 평균 차수가 같아도 2홉 비용이 자릿수로 다르다. 이럴 때는 오히려 **집합 기반 조인이 정직하게 병렬화되고 예측 가능하다.** 8장의 처방(슈퍼 노드를 질의에서 피하기, 차수 상한 두고 쪼개기, 2홉 미리 계산)도 결국 순회를 포기하고 다른 걸 하라는 말이다.

### (6) 순환 패턴 — 여기선 WCOJ가 순회를 이긴다

삼각형이나 사각형 같은 순환 패턴을 소박한 확장-교집합 순회로 세면 최악 최적이 아니다. 그래서 Kuzu와 GraphflowDB가 **자기 엔진 안에 WCOJ를 넣었다.** 순회가 항상 최선이 아니라는 걸 그래프 진영이 인정한 결과다.

---

## 시험에 나올 한 줄

- 절반 ①: **인덱스 없는 인접성** — 홉 하나가 $O(\log |E|)$ 대신 $O(1)$급. 단, **두 번째 홉부터**이고 앵커에는 색인이 필요하다.
- 절반 ②: **중간 결과가 곱해지지 않는다**(3장) — 이진 조인은 $\bar{d}^{\,k}$로 자라고, 순회는 프런티어가 노드 집합으로 접혀 $\lvert F_i \rvert \le N$으로 제한된다. 3장 실측 4홉 **95배**.
- 정직한 각주: 절반 ②는 **관계 모델의 한계가 아니라 이진 조인 엔진의 한계**다. AGM 상한 · WCOJ(NPRR, leapfrog triejoin, Generic Join) · Yannakakis $O(\text{IN}+\text{OUT})$가 이론적으로 해결했고, Umbra·DuckDB·LogicBlox가 실제로 구현 중이다.
- 반례: 넓은 프런티어(실측 **스캔이 8.1배 승**), 전역 집계, 1홉, 강한 술어, 슈퍼 노드, 순환 패턴.

---

## 출처

- [Neo4j — Graph database concepts (index-free adjacency)](https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/)
- [Neo4j — Graph database vs. relational database](https://neo4j.com/blog/graph-database/graph-database-vs-relational-database/)
- [Ngo, Ré, Rudra — Worst-case Optimal Join Algorithms (ACM)](https://dl.acm.org/doi/pdf/10.1145/3180143)
- [CS294-248 강의 노트 — Worst-Case Optimal Joins (Hung Ngo)](https://berkeley-cs294-248.github.io/lectures/hung-ngo-wcoj.pdf)
- [Lecture 6: Size Bounds for Joins — The AGM Bound (UW-Madison)](https://pages.cs.wisc.edu/~paris/cs784-s17/lectures/lecture6.pdf)
- [A Gentle(-ish) Introduction to Worst-Case Optimal Joins](https://justinjaffray.com/a-gentle-ish-introduction-to-worst-case-optimal-joins/)
- [Database Theory in Action: Yannakakis' Algorithm](https://arxiv.org/html/2601.00098)
- [Adopting Worst-Case Optimal Joins in Relational Database Systems (Umbra)](https://www.researchgate.net/publication/344970075_Adopting_worst-case_optimal_joins_in_relational_database_systems)
- [Optimizing Subgraph Queries by Combining Binary and Worst-Case Optimal Joins](https://www.researchgate.net/publication/335905887_Optimizing_subgraph_queries_by_combining_binary_and_worst-case_optimal_joins)
- [One Join Order Does Not Fit All: Reducing Intermediate Results with Per-Split Query Plans (SplitJoin, DuckDB·Umbra)](https://arxiv.org/html/2510.25684v1)
- [A+ Indexes: Tunable and Space-Efficient Adjacency Lists in Graph DBMSs](https://arxiv.org/pdf/2004.00130)
- [Performance of Graph and Relational Databases in Complex Queries (MDPI)](https://www.mdpi.com/2076-3417/12/13/6490)
- [General-Purpose Join Algorithms for Listing Triangles in Large Graphs](https://arxiv.org/pdf/1501.06689)
