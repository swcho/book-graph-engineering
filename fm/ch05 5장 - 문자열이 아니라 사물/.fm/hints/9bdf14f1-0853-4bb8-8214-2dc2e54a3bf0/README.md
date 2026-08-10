# RDF 엣지 속성 (1) 구체화 — 관계를 노드로 승격시키는 대가

> **질문** RDF에서 엣지 속성을 다루는 방법 (1) 구체화(reification)는 무엇이며 대가는 무엇인가?
>
> **답** 관계를 노드로 승격시켜 속성을 그 노드에 단다. 원래 있던 `ex:signed` 엣지가 사라져 기존 질의가 전부 깨진다.

---

## 1. 문제가 어디서 생기나

RDF의 기본 단위는 `(주어, 술어, 목적어)` 트리플입니다. 트리플에는 "속성 주머니"를 달 자리가 없습니다.
그런데 실무에서 필요한 사실은 이렇게 생겼어요.

```
가온테크가 계약 C-2025-118에 서명했다.
    ├─ 언제:   2025-06-02
    ├─ 경로:   직접
    └─ 신뢰도: 0.98
```

프로퍼티 그래프(LPG)는 **한 줄**입니다. 엣지에 주머니가 달려 있으니까요.

```cypher
(가온테크)-[:SIGNED {at: date('2025-06-02'), channel: '직접', confidence: 0.98}]->(C-2025-118)
```

RDF는 이 자리에서 세 방법 중 하나를 골라야 합니다 (`code/model.py`, `code/ex2_edge_properties.py`).

| 방법 | 아이디어 | 원래 엣지 |
|---|---|---|
| (1) **구체화** | 관계를 노드로 승격 | **사라진다** |
| (2) RDF-star / 트리플 항 | 트리플 자체를 주어로 | 남는다 |
| (3) 이름 붙인 그래프 | 트리플 묶음에 이름 | 남는다 |

이 카드는 (1)번입니다.

---

## 2. 구체화 전 / 후를 나란히

### 전 (구체화 없음) — 5 트리플

```turtle
@prefix ex:  <http://example.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:Gaon      a ex:Company  ; ex:name "가온테크" ;
             ex:signed ex:C2025118 .          # ← 이 한 줄이 "엣지"다
ex:C2025118  a ex:Contract ; ex:id "C-2025-118" .
```

`ex:signed`는 **주어에서 목적어로 곧장 가는 1홉**입니다. 속성을 달 자리는 없습니다.

### 후 (책이 쓰는 중간 노드 방식) — 10 트리플

`code/model.py`의 `RDF_REIFIED`가 이 모양입니다.

```turtle
@prefix ex:  <http://example.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:Gaon      a ex:Company ; ex:name "가온테크" ;
             ex:hasSigning ex:Signing1 .      # ① 회사 → 서명사건
ex:Signing1  a  ex:Signing ;                  # ② 관계가 «사물»이 되었다
             ex:contract   ex:C2025118 ;      # ③ 서명사건 → 계약
             ex:at         "2025-06-02"^^xsd:date ;
             ex:channel    "직접" ;
             ex:confidence "0.98"^^xsd:decimal .
ex:C2025118  a ex:Contract ; ex:id "C-2025-118" .
```

바뀐 것 세 가지입니다.

1. **엣지 1개가 노드 1개 + 엣지 2개로 갈라졌다.** 경로 길이가 1홉 → 2홉이 되었습니다.
2. **술어 이름이 바뀌었다.** `ex:signed` → `ex:hasSigning` + `ex:contract`.
3. **`ex:signed` 트리플이 그래프에 더 이상 존재하지 않는다.** 이게 핵심입니다.

트리플 수는 관계 하나당 1줄 → 6줄(중간 노드 부분만 세면)로 늘어납니다. LPG의 1줄과 비교하면 6배예요.

---

## 3. "질의가 깨진다"가 구체적으로 무슨 뜻인가

말로만 하면 안 와닿으니 실제로 돌려 봤습니다 (`rdflib 7.6.0`, 위 두 그래프 그대로).

### (a) 직접 엣지를 밟는 SELECT — 1행 → **0행**

```sparql
PREFIX ex: <http://example.org/>
SELECT ?name ?cid WHERE {
  ?c ex:name ?name ;
     ex:signed ?k .          # ← 이 패턴이 매칭에 실패한다
  ?k ex:id ?cid .
}
```

| 그래프 | 결과 |
|---|---|
| 구체화 전 | `1행` — `["가온테크", "C-2025-118"]` |
| 구체화 후 | **`0행`** |

**왜 빈 결과인가.** SPARQL의 기본 그래프 패턴 매칭은 트리플 단위 완전 일치입니다. `?c ex:signed ?k`는 술어 IRI가 정확히 `ex:signed`인 트리플을 찾는데, 구체화 후 그래프에는 그런 트리플이 **한 개도 없습니다**. 첫 패턴이 빈 해(solution)를 내면 join 결과 전체가 빈 집합이 됩니다. 문법 오류도, 예외도, 경고도 없습니다. **그냥 조용히 0행**입니다. 이게 가장 위험한 지점이에요 — 대시보드는 "0건"을 정상 값처럼 그립니다.

### (b) ASK — `true` → **`false`**

```sparql
PREFIX ex: <http://example.org/>
ASK { ex:Gaon ex:signed ex:C2025118 }
```

| 그래프 | 결과 |
|---|---|
| 구체화 전 | `true` |
| 구체화 후 | **`false`** |

사실은 그대로 데이터에 있는데, "가온테크가 이 계약에 서명했나?"에 그래프가 **아니라고 대답합니다**. 참/거짓이 뒤집히는 것이지 누락이 아닙니다.

### (c) 집계 — `1` → **`0`**

```sparql
SELECT (COUNT(*) AS ?n) WHERE { ?c ex:signed ?k }
```

| 그래프 | 결과 |
|---|---|
| 구체화 전 | `1` |
| 구체화 후 | **`0`** |

"이번 달 신규 계약 건수" 같은 지표가 0으로 떨어집니다.

### (d) 술어를 변수로 둬도 안 구해진다 — **0행**

"술어 이름만 바뀐 거니까 와일드카드로 받으면 되지 않나?" 싶지만 안 됩니다.

```sparql
SELECT ?name ?cid WHERE { ?c ex:name ?name ; ?p ?k . ?k ex:id ?cid . }
```

| 그래프 | 결과 |
|---|---|
| 구체화 후 | **`0행`** |

**왜인가.** 문제는 술어 «이름»이 아니라 **홉 수**입니다. `?c ?p ?k`로 도달하는 `?k`는 `ex:Signing1`인데, `ex:Signing1`에는 `ex:id`가 없습니다. 계약은 한 홉 더 가야 나옵니다. 구체화는 이름만 바꾸는 리네이밍이 아니라 **그래프의 위상(topology)을 바꾸는 변경**이라서, 술어를 변수화해도 구제되지 않습니다.

같은 이유로 프로퍼티 경로도 전부 다시 써야 합니다. `ex:signed+`, `ex:signed/ex:amount` 같은 경로, `ex:signed`에 걸어 둔 SHACL 제약, OWL 도메인/레인지 공리, `CONSTRUCT` 템플릿, 인덱스·머티리얼라이즈드 뷰까지 함께 깨집니다.

### (e) 5장 예제 질의도 깨진다

`code/ex3_cypher_vs_sparql.py`의 SPARQL은 `ex:signed`와 `ex:terminated`를 그대로 밟습니다.

```sparql
?c ex:name ?고객 ; ex:terminated ?old ; ex:signed ?new .
```

`ex:signed`를 구체화하는 순간 이 질의도 0행이 됩니다. 이렇게 다시 쓰면 다시 1행이 됩니다.

```sparql
?c ex:name ?고객 ; ex:terminated ?old ; ex:hasSigning ?s .
?s ex:contract ?new ; ex:at ?재계약시각 .
```

### 정상 동작하는 새 질의 (참고)

```sparql
PREFIX ex: <http://example.org/>
SELECT ?name ?cid ?at WHERE {
  ?c ex:name ?name ; ex:hasSigning ?s .
  ?s ex:contract ?k ; ex:at ?at .          # ← 속성은 여기서 얻는다
  ?k ex:id ?cid .
}
```
→ `1행` — `["가온테크", "C-2025-118", "2025-06-02"]`

**얻은 것**: `ex:at`, `ex:channel`, `ex:confidence`를 손가락으로 가리킬 수 있게 되었습니다.
**잃은 것**: `ex:signed`를 알고 있던 모든 질의·제약·뷰.

---

## 4. RDF 1.1 표준 `rdf:Statement` 구체화와 이 책의 중간 노드 방식

"reification"이라는 이름은 원래 RDF 표준 어휘를 가리킵니다. 둘은 **다른 것이지만 같은 병을 앓습니다**.

### RDF 1.1 표준 방식

```turtle
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

ex:S1  a rdf:Statement ;
       rdf:subject   ex:Gaon ;
       rdf:predicate ex:signed ;      # ← 술어가 «목적어 자리의 데이터»로 내려왔다
       rdf:object    ex:C2025118 ;
       ex:at         "2025-06-02"^^xsd:date ;
       ex:channel    "직접" .
```

`rdf:Statement`, `rdf:subject`, `rdf:predicate`, `rdf:object`는 RDF Schema에 정의된 정식 어휘입니다. 문장을 «말하는» 대신 «묘사»합니다.

여기서 결정적인 사실 하나. **RDF 1.1 명세는 이 구체화 어휘에 형식 의미론을 주지 않습니다.** 즉 위 네 줄이 그래프에 있다고 해서 `ex:Gaon ex:signed ex:C2025118`이 **함의(entail)되지 않습니다**. 추론기를 아무리 돌려도 원래 엣지가 되살아나지 않아요. 실제로 확인해 보면:

| 질의 | `rdf:Statement` 그래프 |
|---|---|
| `SELECT ... ?c ex:signed ?k ...` | **0행** |
| `ASK { ex:Gaon ex:signed ex:C2025118 }` | **false** |

책의 중간 노드 방식과 **정확히 같은 증상**입니다. 표준 어휘를 쓰는 것이 구원이 아니라는 뜻이죠.

### 두 방식 비교

| | RDF 1.1 `rdf:Statement` | 책의 중간 노드 (`ex:Signing1`) |
|---|---|---|
| 어휘 | 표준 (`rdf:*`) | 도메인 자체 정의 (`ex:Signing`, `ex:contract`) |
| 문패턴 이름 | reification | n-ary relation / event node ([W3C n-ary relations 노트](https://www.w3.org/TR/swbp-n-aryRelations/) 패턴 1) |
| 트리플 오버헤드 | 속성 3개 → 뼈대 4 + 속성 3 = **7줄** (원본까지 남기면 8줄) | 속성 3개 → **6줄** |
| 형식 의미론 | 없음 (원래 트리플 함의 안 함) | 없음 (애초에 다른 트리플) |
| 원래 엣지 | 사라진다 | 사라진다 |
| 술어의 자리 | `rdf:predicate`의 **목적어**(데이터로 강등) | 노드의 `rdf:type`(`ex:Signing`) |
| 도메인 모델링 | 관계가 "진술"로만 남음 | 관계가 «서명 사건»이라는 1급 개체가 됨 |
| 질의 가독성 | 낮음 (뼈대 3줄을 매번 씀) | 상대적으로 나음 |
| 추론·SHACL 친화 | 나쁨 (술어가 데이터라 OWL 공리 안 걸림) | 좋음 (`ex:Signing` 클래스에 제약·계층 부여 가능) |

**언제 어느 쪽인가.**
- 목적이 **"이 문장에 대해 말하기"** (출처, 신뢰도, 누가 주장했나, 언제 관측했나)라면 `rdf:Statement` 계열이 의도에 맞습니다. 다만 실무에서는 (2) RDF-star / (3) 이름 붙인 그래프가 거의 항상 더 낫습니다.
- 목적이 **"관계 자체가 실은 사건이었다"** (서명, 고용, 결혼, 거래 — 시작·종료·장소·당사자를 갖는 것)라면 중간 노드가 정답입니다. 이 경우 `ex:signed`가 사라지는 것은 «손실»이 아니라 **모델링 오류를 고친 것**입니다. 애초에 서명은 엣지가 아니라 사건이었으니까요.

이 구분이 실무의 핵심입니다. 관계의 30% 이상에 속성이 붙는다면 그건 «엣지에 속성이 필요하다»는 신호일 수도 있고, «그 관계들이 실은 사건이다»는 신호일 수도 있습니다. 전자면 LPG, 후자면 중간 노드 방식이 RDF에서도 자연스럽습니다.

### RDF 1.2와의 관계

RDF 1.2(2026-04-07 기준 Candidate Recommendation)는 **트리플 항(triple term)** 을 도입합니다. `rdf:reifies`의 목적어로 트리플 항을 두는 «구체화 트리플»이 정식 메커니즘이고, Turtle 등 구체 문법은 이를 위한 축약 표기를 제공합니다. 책의 `RDF_STAR` 예시가 쓰는 `<< ... >>` 표기가 그 계열입니다.

```turtle
ex:Gaon ex:signed ex:C2025118 .                                          # ← 원래 엣지가 남는다
<< ex:Gaon ex:signed ex:C2025118 >> ex:at "2025-06-02"^^xsd:date .
```

핵심 차이: **원래 엣지가 그대로 주장(assert)된 상태로 남습니다.** 그래서 `?c ex:signed ?k`도, `ASK { ex:Gaon ex:signed ex:C2025118 }`도 계속 동작합니다. 구체화의 핵심 대가를 없앤 것이 RDF-star / RDF 1.2의 존재 이유예요.
RDF 1.1 `rdf:Statement` 어휘는 RDF 1.2 concepts에서 폐기 선언되지도, 다뤄지지도 않았습니다 (명세의 규범 범위 밖). 즉 여전히 쓸 수는 있지만, 새로 짜는 모델에서 «문장에 대해 말하기»가 목적이라면 트리플 항 쪽을 보는 게 맞습니다.

---

## 5. 완화책: 원래 엣지를 남겨 두기 (중복 저장)

가장 흔한 현장 처방입니다.

```turtle
# 구체화한 사실
ex:Gaon      ex:hasSigning ex:Signing1 .
ex:Signing1  a ex:Signing ; ex:contract ex:C2025118 ;
             ex:at "2025-06-02"^^xsd:date ; ex:channel "직접" ;
             ex:confidence "0.98"^^xsd:decimal .

# + 원래 엣지를 «그대로 한 번 더» 적는다
ex:Gaon      ex:signed ex:C2025118 .
```

실제로 돌려 보면 양쪽이 다 삽니다.

| 질의 | 전 | 구체화만 | 구체화 + 원본 유지 |
|---|---|---|---|
| `?c ex:signed ?k` | 1행 | 0행 | **1행** ✅ |
| `?s ex:contract ?k ; ex:at ?at` | 0행 | 1행 | **1행** ✅ |
| `ASK { ex:Gaon ex:signed ex:C2025118 }` | true | false | **true** ✅ |
| 트리플 수 | 5 | 10 | **11** |

기존 질의가 안 깨지고 새 속성도 얻습니다. 대신 대가가 붙습니다.

### 대가 (1) 두 개의 진실 — 갱신·삭제 이상

같은 사실이 두 곳에 있으니 **원자적으로 같이 고쳐야** 합니다.
- 계약이 취소되어 `ex:signed`를 지웠는데 `ex:Signing1`이 남으면, 구체화 쪽 질의는 여전히 서명이 있다고 답합니다.
- 반대 순서로 지우면 `ex:signed`가 남아 유령 엣지가 됩니다.
- 계약 대상이 `ex:C2025118` → `ex:C2025119`로 정정되면 **두 곳**을 고쳐야 합니다.

RDF 스토어는 이런 쌍(pair) 불변식을 강제해 주지 않습니다. 트랜잭션 경계, SHACL 제약, 또는 "쓰기는 반드시 이 함수로만"이라는 규율로 애플리케이션이 떠안아야 합니다. 그리고 파이프라인이 여럿 붙는 순간 반드시 어긋납니다(drift).

### 대가 (2) 조용한 중복 행

두 경로를 `UNION`이나 프로퍼티 경로로 함께 받으면 **같은 답이 두 번** 나옵니다.

```sparql
PREFIX ex: <http://example.org/>
SELECT ?name ?cid WHERE {
  ?c ex:name ?name ;
     (ex:signed|ex:hasSigning/ex:contract) ?k .   # 스키마 이행기에 흔히 쓰는 방어적 패턴
  ?k ex:id ?cid .
}
```

| 그래프 | 결과 |
|---|---|
| 전 | 1행 |
| 구체화만 | 1행 |
| **구체화 + 원본 유지** | **2행** — `["가온테크","C-2025-118"]` × 2 |

`COUNT(*)`도 1 → **2**로 부풀어 오릅니다. 지표가 두 배가 되는 종류의 버그고, 0행보다 발견이 늦습니다. `DISTINCT`나 `COUNT(DISTINCT ...)`를 습관적으로 붙여야 하는데, 그건 그것대로 성능 비용입니다.

### 대가 (3) 저장·인덱스 팽창

관계 하나가 1트리플 → 7트리플이 됩니다(원본 1 + 구체화 6). 관계 1억 개 규모면 트리플이 7배로 늘고, SPO/POS/OSP 인덱스가 다 같이 커집니다. 조인 홉도 1홉 → 2홉이라 질의 지연이 함께 올라갑니다.

### 대가 (4) 추론과 CONSTRUCT의 이중 계산

OWL 추론이나 규칙이 두 표현 모두를 훑으면, 파생 트리플이 두 갈래로 만들어집니다. `CONSTRUCT`로 뷰를 뽑을 때도 중복 제거를 명시하지 않으면 그대로 새어 나갑니다.

### 대가 (5) "어느 쪽이 정본인가"의 모호함

새로 합류한 사람은 `ex:signed`를 보고 그것만 씁니다. 그러면 `ex:confidence 0.98` 같은 정보를 그냥 못 봅니다. 반대로 구체화 쪽만 쓰는 사람은 원본 엣지에 대한 업데이트를 놓칩니다. 문서 없이는 필연적으로 갈라집니다.

### 그래서 실무 판단

원래 엣지를 남기고 싶다는 욕구는 정당합니다. 다만 **수동 중복은 그 욕구를 만족시키는 가장 나쁜 방법**입니다. 같은 결과를 더 싸게 얻는 길이 있습니다.

| 처방 | 원래 엣지 | 진실의 개수 | 비고 |
|---|---|---|---|
| 구체화만 | 없음 | 1 | 기존 질의 전부 재작성 |
| 구체화 + 수동 중복 | 있음 | **2** | 갱신 이상 + 중복 행 + 7배 저장 |
| **(2) RDF-star / 트리플 항** | 있음 | 1 | 표기 간결, 명세가 CR 단계 · 스토어 지원 확인 필요 |
| **(3) 이름 붙인 그래프** | 있음 | 1 | 묶음 단위. 엣지 하나만 가리키려면 1개짜리 묶음을 만들어야 해서 그래프가 폭증 |
| **LPG로 간다** | 있음 | 1 | 관계의 30% 이상에 속성이 붙으면 이쪽 |

중복을 굳이 유지해야 한다면 최소한 이렇게 하세요.
1. **한쪽을 파생으로 선언한다.** 구체화 쪽을 정본으로 두고, `ex:signed`는 `CONSTRUCT`/규칙으로 **생성되는 것**으로 정의합니다. 손으로 두 번 쓰지 않습니다.
2. **파생분을 별도의 이름 붙인 그래프에 넣는다.** `GRAPH ex:derived { ex:Gaon ex:signed ex:C2025118 }`. 정본과 파생이 물리적으로 갈라지니 중복 행과 재생성이 통제됩니다.
3. **SHACL로 쌍 불변식을 검사한다.** `ex:Signing`이 있으면 대응 `ex:signed`도 있어야 한다(그리고 그 역도)를 CI에서 돌립니다.
4. **이행 기간을 못 박는다.** 방어적 `(ex:signed|ex:hasSigning/ex:contract)` 패턴은 «영구 설계»가 아니라 «마이그레이션 기간용»으로만 씁니다.

---

## 6. 한 줄 정리

구체화는 **관계를 노드로 승격시켜 속성을 달 자리를 만드는 것**이고, 대가는 **원래 엣지가 그래프에서 사라져 그 엣지를 밟던 SELECT는 0행, ASK는 false, COUNT는 0이 되는 것** — 그것도 오류 없이 조용히 그렇게 되는 것입니다. RDF 1.1 표준 `rdf:Statement` 방식도 형식 의미론이 없어 같은 증상을 보입니다. 원래 엣지를 남겨 중복 저장하면 기존 질의는 살지만 진실이 두 개가 되어 갱신 이상, 중복 행, 7배 저장을 사게 됩니다. 이 대가를 없애려고 나온 것이 (2) RDF-star / RDF 1.2 트리플 항이고, 애초에 이 문제가 없는 쪽이 LPG입니다.

---

## 참고

- `code/model.py` — `RDF_TRIPLES`, `RDF_REIFIED`, `RDF_STAR`, `RDF_NAMED_GRAPH`
- `code/ex2_edge_properties.py` — 세 방법과 각각의 대가를 출력
- `code/ex3_cypher_vs_sparql.py` — `ex:signed`를 직접 밟는 SPARQL (구체화하면 깨지는 그 질의)
- [W3C — Defining N-ary Relations on the Semantic Web](https://www.w3.org/TR/swbp-n-aryRelations/) (중간 노드 방식의 원조 패턴)
- [W3C — RDF 1.2 Concepts and Abstract Syntax](https://www.w3.org/TR/rdf12-concepts/) (트리플 항, `rdf:reifies`)
- [W3C — RDF 1.1 Datasets](https://www.w3.org/TR/rdf11-datasets/) (이름 붙인 그래프)

*본문의 행 수·트리플 수·`true`/`false` 값은 rdflib 7.6.0으로 위 Turtle과 SPARQL을 실제 실행해 확인한 값입니다.*
