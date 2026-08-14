# 우리 어휘와 공개 어휘를 잇는 구체적 방법은 무엇인가?

**답:** RDF라면 `owl:sameAs`나 `skos:closeMatch`를 쓰고, LPG라면 속성으로 매핑 표를 둔다.

---

## 1. 왜 「잇는다」가 필요한가

12.4절 예제(`ex4_reuse_or_build.py`)는 우리가 필요한 개념마다 공개 어휘 후보와 적합도를 매긴다.

```python
NEEDED = {
    "제품":      {"공개어휘": "schema.org/Product",      "적합도": 0.9},
    "공급사":    {"공개어휘": "schema.org/Organization", "적합도": 0.8},
    "부품":      {"공개어휘": "schema.org/Product",      "적합도": 0.4},
    "리콜":      {"공개어휘": None,                       "적합도": 0.0},
    "대체가능":  {"공개어휘": None,                       "적합도": 0.0},
    "납품":      {"공개어휘": "schema.org/seller",        "적합도": 0.5},
}
THRESHOLD = 0.7
```

세 갈래로 갈린다.

| 적합도 | 판단 | 대응 |
|---|---|---|
| 0.7 이상 | 그대로 가져다 쓴다 | 우리 어휘를 따로 만들지 않는다 |
| 0.7 미만, 후보는 있음 | **우리 것으로 만들고 사상만 걸어 둔다** | ← 이 카드가 다루는 지점 |
| 후보 없음 | 만든다 | 이을 대상 자체가 없다 |

책이 짚는 실수는 두 가지다.

- **(가) 억지로 맞춰 쓴다** → 「부품인데 왜 가격이 있지」 같은 예외 조항이 쌓인다.
- **(나) 아예 무시하고 다 새로 만든다** → 밖과 데이터를 주고받을 때마다 변환기를 짠다.

중간이 답이다. 우리 클래스를 만들되, 공개 어휘와 「대략 같음」을 **데이터로** 남긴다. 그래야 나중에 외부 데이터와 붙일 때 매핑이 코드가 아니라 그래프 안에 있다.

> 중간이 답이다. 우리 것으로 만들되, 공개 어휘와 «대략 같음»을 걸어 둔다.
> RDF 라면 owl:sameAs 나 skos:closeMatch, LPG 라면 속성으로 매핑 표를 둔다.

---

## 2. RDF — `owl:sameAs`: 「완전히 같다」

`owl:sameAs`(OWL 2의 `SameIndividual`)는 **두 IRI가 같은 개체를 가리킨다**는 선언이다. OWL은 서로 다른 이름이 서로 다른 개체라고 가정하지 않는다(고유 이름 가정 없음, No Unique Name Assumption). 그래서 같음을 쓰려면 명시해야 한다.

```turtle
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix ex:   <https://example.com/ns#> .
@prefix wd:   <http://www.wikidata.org/entity/> .

# 우리 카탈로그의 «가온테크»와 위키데이터의 그 회사가 같은 법인이다
ex:supplier/gaon-tech  owl:sameAs  wd:Q12345678 .
```

W3C OWL 2 Primer의 설명이 핵심이다.

> `:James owl:sameAs :Jim.`
> 이는 추론기가 James에 대해 주어진 모든 정보가 Jim에게도 성립한다고 추론하게 한다.

### 남용이 위험한 이유

`owl:sameAs`는 **대칭·추이적**이며, 추론기가 두 개체의 모든 서술을 **양방향으로 전파**한다. 즉 한쪽에 붙은 속성이 반대쪽에도 그대로 붙는다.

- 우리가 붙인 `ex:내부등급 "B"`가 위키데이터 개체의 속성이 된다.
- 저쪽이 가진 잘못된 값이 우리 쪽으로 들어온다.
- 「대략 같음」 정도의 관계에 `sameAs`를 쓰면 **서로 모순되는 값이 한 개체에 몰린다.**

SKOS Primer가 드는 예가 정확히 이 사고다. `ex1:animal owl:sameAs ex2:animals`를 걸면 트리플이 합쳐져서 이렇게 된다.

```turtle
ex1:animal  rdf:type      skos:Concept ;
            skos:prefLabel "animal"@en ;      # ← 같은 언어에
            skos:prefLabel "animals"@en ;     # ← 대표 레이블이 둘
            skos:inScheme  ex1:referenceAnimalScheme ;
            skos:inScheme  ex2:eggSellerScheme .
```

한 개념이 같은 언어로 대표 레이블을 둘 가질 수는 없다. 개념 체계도 뒤섞였다. **`owl:sameAs`는 「거의 같다」에 쓰는 도구가 아니다.** 진짜로 동일한 개체(같은 법인, 같은 사람, 같은 제품 SKU)일 때만 쓴다.

덧붙여, `owl:sameAs`는 **개체(individual)** 사이의 술어다. 클래스끼리라면 `owl:equivalentClass`, 속성끼리라면 `owl:equivalentProperty`가 맞는 짝이다. 예제 4의 `부품 ~ schema.org/Product`는 클래스 층위 얘기이므로 애초에 `sameAs`의 자리가 아니다.

---

## 3. RDF — SKOS 매핑 술어: 「어느 정도 같다」를 눈금으로

SKOS는 서로 다른 개념 체계(concept scheme)를 **합치지 않고 잇기 위해** 매핑 술어를 따로 둔다. 전부 `skos:mappingRelation`의 하위 속성이고, 그 위는 `skos:semanticRelation`이다.

| 술어 | 뜻 | 논리 성질 | 상위 속성 |
|---|---|---|---|
| `skos:exactMatch` | 폭넓은 범위의 검색 응용에서 **바꿔 써도 된다**는 높은 확신 | 대칭 + **추이적** | `skos:closeMatch` |
| `skos:closeMatch` | **일부** 응용에서 바꿔 쓸 만큼 충분히 비슷함 | 대칭, **추이 아님** | `skos:mappingRelation` |
| `skos:broadMatch` | 상대 개념이 **더 넓다** | `skos:broader`의 하위 | `skos:mappingRelation` |
| `skos:narrowMatch` | 상대 개념이 **더 좁다** (`broadMatch`의 역) | `skos:narrower`의 하위 | `skos:mappingRelation` |
| `skos:relatedMatch` | 상하 관계는 아니고 **연관됨** | 대칭 | `skos:mappingRelation` |

세부 규칙 두 가지를 기억해 두면 사고를 막는다.

1. **`closeMatch`는 일부러 추이적이 아니다.** A≈B, B≈C 라고 A≈C가 되면 체계를 서너 개 건너뛰는 순간 의미가 무너지기 때문이다. 「대략 같음」은 전파시키지 않는 게 설계 의도다.
2. **`exactMatch`는 `broadMatch`/`narrowMatch`/`relatedMatch`와 서로소(disjoint)다.** 같은 두 개념에 `exactMatch`와 `broadMatch`를 동시에 걸면 모순이다.

```turtle
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix ex:   <https://example.com/ns#> .
@prefix sdo:  <https://schema.org/> .

ex:부품    a skos:Concept ; skos:prefLabel "부품"@ko ; skos:inScheme ex:catalog .
ex:제품    a skos:Concept ; skos:prefLabel "제품"@ko ; skos:inScheme ex:catalog .
ex:리콜    a skos:Concept ; skos:prefLabel "리콜"@ko ; skos:inScheme ex:catalog .

# 적합도 0.9 — 사실상 같다
ex:제품    skos:exactMatch    sdo:Product .

# 적합도 0.4 — 비슷하지만 우리 «부품»은 판매 단위가 아니다.
# (a) 「일부 응용에서는 바꿔 써도 된다」 정도로만 잇는다
ex:부품    skos:closeMatch    sdo:Product .

# (b) 관계를 더 정확히 말할 수 있다면 — 우리 «부품»은 sdo:Product 보다 좁다
ex:부품    skos:broadMatch    sdo:Product .

# ✗ 이렇게 쓰면 틀린다
# ex:부품  skos:narrowMatch   sdo:Product .   # 「Product 가 더 좁다」가 되어 방향이 반대
# ex:부품  skos:exactMatch    sdo:Product .   # broadMatch 와 서로소(S46) — 모순이고, 뜻도 과하다

# 상하도 등가도 아닌 그냥 관련 — 납품 ~ seller
ex:납품    skos:relatedMatch  sdo:seller .

# 공개 어휘에 대응이 없다 — 이을 곳이 없으니 걸지 않는다
# ex:리콜 은 매핑 없음
```

> `broadMatch`의 방향 읽는 법: `A skos:broadMatch B`는 **B가 A보다 넓다**는 뜻이다(`skos:broader`의 하위 속성이므로). 헷갈리면 「주어가 좁고 목적어가 넓다」로 외운다.

### 그래서 무엇을 고르나

| 상황 | 고를 것 |
|---|---|
| 같은 실체(법인·사람·SKU)를 두 IRI가 가리킴 | `owl:sameAs` |
| 클래스 정의가 논리적으로 동일 | `owl:equivalentClass` |
| 개념 체계가 다르고 뜻이 사실상 같음 | `skos:exactMatch` |
| 뜻이 겹치지만 딱 맞지는 않음 (예제 4의 「부품」) | `skos:closeMatch` |
| 우리 개념이 상대보다 좁다 / 넓다 | `skos:broadMatch` / `skos:narrowMatch` |
| 인접하지만 등가도 상하도 아님 | `skos:relatedMatch` |

카드의 답이 `owl:sameAs`**나** `skos:closeMatch`라고 두 개를 나열한 이유가 여기 있다. **확신의 세기가 다르면 술어도 달라야 한다.** 적합도 0.4짜리에 `sameAs`를 거는 건 숫자를 매겨 놓고 무시하는 짓이다.

---

## 4. LPG — 속성으로 매핑 표를 둔다

Neo4j·Kuzu 같은 LPG에는 추론기도, `owl:sameAs` 같은 내장 등가 술어도 없다. 그래서 매핑을 **데이터로 직접 적는다.** 두 가지 방식이 있다.

### 방식 A — 노드 속성에 얹기 (간단, 매핑이 1:1일 때)

```cypher
// Neo4j: 우리 라벨에 공개 어휘 IRI 와 매핑 강도를 속성으로 붙인다
MATCH (c:Concept {name: '부품'})
SET c.externalVocab  = 'https://schema.org/Product',
    c.matchType      = 'closeMatch',   // exact | close | broad | narrow | related
    c.matchScore     = 0.4,
    c.matchNote      = '우리 부품은 판매 단위가 아님';
```

읽을 때는 그냥 속성 조회다.

```cypher
MATCH (c:Concept)
WHERE c.externalVocab IS NOT NULL AND c.matchScore >= 0.7
RETURN c.name, c.externalVocab, c.matchType
ORDER BY c.matchScore DESC;
```

한계가 분명하다. 한 개념을 schema.org와 위키데이터 **양쪽**에 매핑하려면 속성이 배열이 되고, 그 순간 `matchType`·`matchScore`와 짝을 맞추기가 지저분해진다.

### 방식 B — 별도 매핑 노드/관계 (1:N, 출처·시점을 남길 때)

```cypher
// 외부 어휘 항목 자체를 노드로 만들고, 매핑을 관계로 둔다
MERGE (ext:ExternalTerm {iri: 'https://schema.org/Product'})
  ON CREATE SET ext.vocabulary = 'schema.org', ext.label = 'Product'
WITH ext
MATCH (c:Concept {name: '부품'})
MERGE (c)-[m:MAPS_TO]->(ext)
  SET m.matchType = 'closeMatch',
      m.score     = 0.4,
      m.decidedBy = 'ontology-review-2026-08',
      m.decidedAt = date();
```

관계에 속성을 달 수 있는 게 LPG의 강점이라 **「누가 언제 0.4로 판단했는가」까지 그래프 안에 남는다.** RDF에서 같은 걸 하려면 reification이나 RDF-star가 필요하다.

질의도 자연스럽다.

```cypher
// 외부로 내보낼 때 쓸 수 있는 매핑만 (exact 이상)
MATCH (c:Concept)-[m:MAPS_TO]->(ext:ExternalTerm)
WHERE m.matchType = 'exactMatch'
RETURN c.name AS 우리어휘, ext.iri AS 공개어휘;

// 매핑이 아예 없는 개념 — 우리가 새로 만든 것들
MATCH (c:Concept)
WHERE NOT (c)-[:MAPS_TO]->(:ExternalTerm)
RETURN c.name;   // 리콜, 대체가능
```

Kuzu처럼 스키마를 선언하는 LPG라면 매핑 표가 아예 테이블이 된다.

```cypher
CREATE NODE TABLE ExternalTerm(iri STRING, vocabulary STRING, label STRING, PRIMARY KEY(iri));
CREATE REL TABLE MapsTo(FROM Concept TO ExternalTerm, matchType STRING, score DOUBLE);
```

### 핵심 차이

RDF에서는 매핑 술어가 **추론기에게 주는 지시**다(`sameAs`면 실제로 트리플이 합쳐진다). LPG에서는 매핑이 **그냥 기록**이고, 그걸 해석해 무슨 일을 할지는 우리 애플리케이션 코드가 정한다. 그래서 LPG 쪽이 사고는 덜 나지만, 「이 매핑을 어떻게 쓸 것인가」를 아무도 대신 정해 주지 않는다.

---

## 5. 한 줄 정리

적합도 0.7을 기준으로 **가져다 쓸지 만들지**를 먼저 정하고, 만들기로 했으면 **끊지 말고 잇는다.** RDF는 확신의 세기에 맞춰 술어를 고르되 「거의 같음」에 `owl:sameAs`를 쓰지 말고 `skos:closeMatch`(또는 `broadMatch`)를 쓴다. LPG는 추론기가 없으므로 매핑을 노드 속성이나 `MAPS_TO` 관계로 **표처럼 적어 둔다.**

---

## 참고

- [OWL 2 Web Ontology Language Primer (W3C)](https://www.w3.org/TR/owl2-primer/) — `owl:sameAs`, 고유 이름 가정 없음
- [SKOS Simple Knowledge Organization System Reference (W3C)](https://www.w3.org/TR/skos-reference/) — 매핑 술어의 대칭·추이·서로소 조건(S39~S46)
- [SKOS Primer (W3C)](https://www.w3.org/TR/skos-primer/) — `owl:sameAs`를 쓰면 안 되는 이유와 레이블 충돌 예
- [schema.org 어휘 목록](https://schema.org/docs/schemas.html)
- 12장 예제 `code/ex4_reuse_or_build.py`
