# 프로퍼티 그래프(LPG)와 RDF의 근본적 차이

**답**: 세는 단위가 다르다. LPG는 속성을 주머니에 담고 RDF는 속성마다 트리플 한 줄로 편다.

---

## 한 줄로 기억할 것

같은 사실을 적어도 **LPG는 «노드 하나»로 세고, RDF는 «트리플 여러 줄»로 센다.**
표현력의 차이가 아니라 **세는 단위(granularity)의 차이**다. 그리고 이 차이가 실무에서 드러나는 지점은 딱 하나다.

> **속성 하나를 손가락으로 가리킬 수 있는가.**

---

## 1. 같은 사실, 두 벌로 적어 보기

5장 `code/model.py`는 같은 사실 여섯 개를 두 모델로 나란히 적어 둔다.

### LPG — 속성은 주머니(property bag) 안에

```python
LPG_NODES = {
    "n1": {"labels": ["Company"],  "props": {"name": "가온테크", "grade": "A"}},
    "n2": {"labels": ["Contract"], "props": {"id": "C-2025-118", "amount": 5_000_000}},
    "n3": {"labels": ["Person", "Employee"], "props": {"name": "김하늘", "title": "부장"}},
}
LPG_EDGES = [
    {"from": "n1", "type": "SIGNED", "to": "n2",
     "props": {"at": "2025-06-02", "channel": "직접", "confidence": 0.98}},
    {"from": "n1", "type": "MANAGED_BY", "to": "n3",
     "props": {"since": "2023-04-01"}},
]
```

노드도 엣지도 **자기 속성 주머니를 하나씩 들고 있다.** 세는 단위는 「노드 3개, 엣지 2개」.

### RDF — 속성마다 한 줄

```python
RDF_TRIPLES = [
    ("ex:Gaon",      "rdf:type", "ex:Company"),
    ("ex:Gaon",      "ex:name",  '"가온테크"'),
    ("ex:Gaon",      "ex:grade", '"A"'),
    ("ex:C2025118",  "rdf:type", "ex:Contract"),
    ("ex:C2025118",  "ex:id",    '"C-2025-118"'),
    ("ex:C2025118",  "ex:amount", '"5000000"^^xsd:integer'),
    ("ex:Kim",       "rdf:type", "ex:Person"),
    ("ex:Kim",       "rdf:type", "ex:Employee"),
    ("ex:Kim",       "ex:name",  '"김하늘"'),
    ("ex:Kim",       "ex:title", '"부장"'),
    ("ex:Gaon",      "ex:signed",    "ex:C2025118"),
    ("ex:Gaon",      "ex:managedBy", "ex:Kim"),
]
```

세는 단위는 「트리플 12개」. `ex1_two_models.py`가 출력하는 대비가 이것이다.

```text
LPG:  노드 3개, 엣지 2개
RDF:  트리플 12개   (엣지 속성은 아직 뺀 상태)
```

주목할 점 두 가지.

- **라벨이 여러 개인 노드**(`Person`, `Employee`)는 RDF에서 `rdf:type` 트리플 두 줄로 펴진다. 즉 LPG의 「라벨 목록」과 RDF의 「type 트리플들」은 같은 것을 다른 단위로 센 결과다.
- RDF에서는 노드와 속성값의 경계가 흐릿하다. 리터럴이든 다른 리소스든 **똑같이 술어(predicate) 한 줄**로 이어 붙인다. LPG는 「속성」과 「관계」를 문법 차원에서 갈라 놓는다.

---

## 2. 왜 이게 «근본적» 차이인가

새 속성 하나 추가하는 일은 양쪽 다 쉽다.

| 작업 | LPG | RDF |
|---|---|---|
| 새 속성 추가 | props에 키 하나 | 트리플 한 줄 |
| 속성값 읽기 | 주머니에서 꺼내기 | 술어로 조회 |
| **속성 하나에 출처·시각·신뢰도 달기** | **가리킬 손잡이가 없다** | **그 트리플을 가리키면 된다** |

`ex1_two_models.py`의 마지막 문단이 정확히 이 대비다.

> 속성 하나에 출처를 달 때: RDF는 그 트리플을 가리키면 된다.
> LPG는 속성이 주머니 안에 있어서 가리킬 손잡이가 없다. **이게 진짜 차이다.**

즉 RDF의 「펴 놓기」는 장황해 보이지만, 펴 놓은 덕분에 **모든 사실 하나하나가 주소를 갖는다.** 트리플 자체가 지목 가능한 대상이 된다. LPG의 「주머니에 담기」는 간결하지만, 주머니 안의 항목 하나에는 주소가 없다.

이 성질은 메타데이터가 필요할 때 갈라진다.

- 「이 회사의 등급이 A라는 사실은 누가, 언제, 어디서 말했나」 → RDF는 그 등급 트리플을 지목해서 붙인다.
- LPG에서 같은 걸 하려면 속성을 노드로 승격시켜야 한다. 즉 `grade`를 주머니에서 꺼내 별도 노드로 만드는 모델 변경이 필요하다.

---

## 3. 방향을 바꾸면 RDF가 불편해진다 — 엣지 속성

같은 논리가 정확히 반대로도 작동한다. **관계 자체에 속성을 달 때**는 LPG가 압도적으로 편하다. LPG는 엣지도 주머니를 갖기 때문이다.

```text
LPG (1줄)
  (가온테크)-[:SIGNED {at:'2025-06-02', channel:'직접', confidence:0.98}]->(계약)
```

RDF에는 「엣지에 속성」이라는 문법 자리가 없다. 그래서 세 방법 중 하나를 골라야 한다 (`ex2_edge_properties.py`).

### (1) 구체화(reification) — 관계를 노드로 승격, 6줄

```text
ex:Gaon      ex:hasSigning ex:Signing1
ex:Signing1  rdf:type      ex:Signing
ex:Signing1  ex:contract   ex:C2025118
ex:Signing1  ex:at         "2025-06-02"^^xsd:date
ex:Signing1  ex:channel    "직접"
ex:Signing1  ex:confidence "0.98"^^xsd:decimal
```

대가: **원래 있던 `ex:signed` 엣지가 사라진다.** 그 엣지를 밟던 기존 질의가 전부 깨진다.

### (2) RDF-star — 트리플 자체를 주어로, 4줄

```text
ex:Gaon ex:signed ex:C2025118 .
<< ex:Gaon ex:signed ex:C2025118 >> ex:at         "2025-06-02"^^xsd:date .
<< ex:Gaon ex:signed ex:C2025118 >> ex:channel    "직접" .
<< ex:Gaon ex:signed ex:C2025118 >> ex:confidence "0.98"^^xsd:decimal .
```

장점: **원래 엣지가 남아 있어 기존 질의가 안 깨진다.** 대가: 아직 자리를 잡는 중인 명세다(RDF 1.2 triple terms). 도구 지원이 고르지 않다.

### (3) 이름 붙인 그래프(named graph) — 3줄

```text
GRAPH ex:g1 { ex:Gaon ex:signed ex:C2025118 . }
ex:g1 ex:at      "2025-06-02"^^xsd:date .
ex:g1 ex:channel "직접" .
```

대가: **트리플 묶음 단위**라서, 엣지 하나만 가리키려면 묶음도 하나짜리로 만들어야 한다. 그래프 수가 폭발한다.

### 실무 기준선

- 엣지 속성이 **드물게** 필요하면 RDF로 충분하다. 세 방법 중 하나 고르면 된다.
- 엣지 속성이 **기본**이면 LPG가 편하다. 관계마다 시각·출처·신뢰도를 다는 경우다.
- 저자 기준: **관계의 30% 이상에 속성이 붙으면 LPG, 그 밑이면 RDF.**

---

## 4. 질의 언어에도 같은 차이가 비친다

`ex3_cypher_vs_sparql.py`는 「해지했다가 그 뒤에 다시 계약한 고객은?」이라는 **같은 질문**을 두 언어로 던지고 **같은 답**을 받는다.

```cypher
MATCH (c:Company)-[t:Terminated]->(:Contract),
      (c)-[s:Signed]->(:Contract)
WHERE t.at < s.at
RETURN c.name AS 고객, t.at AS 해지, s.at AS 재계약
```

```sparql
SELECT ?고객 ?해지 ?재계약 WHERE {
    ?c ex:name ?고객 ; ex:terminated ?old ; ex:signed ?new .
    ?old ex:endedOn   ?해지 .
    ?new ex:startedOn ?재계약 .
    FILTER(?해지 < ?재계약)
}
```

- Cypher는 **그림**을 그린다: `(c)-[:Signed]->(:Contract)`
- SPARQL은 **문장**을 나열한다: `?c ex:signed ?new .`

여기서도 단위 차이가 보인다. Cypher에서는 엣지 속성 `t.at`을 엣지 변수에 점 찍어 바로 읽는다. SPARQL에서는 `?old ex:endedOn ?해지 .`처럼 **한 줄을 더 써서** 노드 쪽 속성을 끌어와야 한다. 위 예제에서 시각 정보가 엣지가 아니라 계약 노드에 붙어 있는 것도 그 때문이다.

참고로 Cypher 예제는 서버 없이 돌리려고 임베디드 엔진 **Kuzu 0.11.3**을 쓴다. Kuzu는 `CREATE NODE TABLE` / `CREATE REL TABLE`로 **스키마를 미리 못 박는데**, Neo4j 5.x는 라벨을 쓰면 그 자리에서 생긴다. 스키마 선언 여부는 두 엔진의 또 다른 큰 차이다.

---

## 5. 그래서 무엇을 고를 것인가

표현력으로 고르는 게 아니다. **상황**으로 고른다.

| 신호 | 유리한 쪽 |
|---|---|
| 밖에서 오는 데이터를 합치는 일이 많다 (여러 출처, 공용 어휘, URI 정렬) | **RDF** |
| 우리가 만드는 데이터가 대부분이다 | **LPG** |
| 사실 하나하나에 출처·근거·신뢰도가 필요하다 | **RDF** (트리플이 주소를 가짐) |
| 관계 30% 이상에 속성이 붙는다 | **LPG** |
| 추론·온톨로지·스키마 공유가 목표다 | **RDF** |
| 경로 탐색·이웃 순회 성능이 중요하다 | **LPG** |

그리고 5장이 가장 강조하는 실전 조언.

> **고르기 전에 질의 다섯 개를 두 언어로 써 보는 반나절이 4개월을 아낍니다.**

저자 본인이 RDF로 시작했다가 4개월 만에 프로퍼티 그래프로 갈아탄 경험에서 나온 말이다.

---

## 6. 이 카드가 5장의 다른 축과 만나는 곳

5장에는 축이 두 개 있다. 이 카드는 「두 모델, 다른 세는 단위」 축이고, 다른 축은 2012년 「문자열이 아니라 사물」 선언이다. 두 축은 **술어(predicate)** 에서 만난다.

`ex4_things_not_strings.py`는 같은 이름 「타지마할」을 가진 서로 다른 사물 셋(건물/음악가/식당)이 **각자 다른 술어**를 갖는 걸 보여 준다. 「타지마할 입장료」라고 물으면, `입장료`라는 술어를 가진 사물이 건물뿐이라 답이 정해진다.

> 2012년 선언의 핵심은 «더 많이 저장하자»가 아니라 **«사물마다 다른 술어를 갖게 하자»** 였다. 술어 목록이 곧 그 사물의 정체다.

그러니 LPG의 「속성 키 목록」과 RDF의 「술어 목록」은 같은 것을 부르는 두 이름이다. 세는 단위만 다르다. 이 생각은 4부에서 도구 라우팅으로 돌아온다. 에이전트가 어떤 도구를 부를지 고르는 일도 결국 「어떤 술어를 가졌나」를 보는 일이다.

---

## 자주 하는 착각

| 착각 | 실제 |
|---|---|
| RDF가 LPG보다 표현력이 떨어진다 | 표현력 차이가 아니라 단위 차이다. 서로 변환 가능하다. 다만 비용이 다르다. |
| LPG는 엣지 속성을, RDF는 엣지 속성을 못 쓴다 | RDF도 세 방법으로 쓴다. 다만 문법 자리가 없어서 우회해야 한다. |
| 트리플 수가 많으면 비효율이다 | 펴 놓은 덕에 모든 사실이 주소를 갖는다. 그게 값이다. |
| RDF-star면 문제가 끝난다 | 기존 엣지를 보존하는 건 맞지만, 명세가 아직 자리를 잡는 중이고 엔진 지원이 고르지 않다. |

---

## 1차 출처

| 키워드 | 상태 | 링크 |
|---|---|---|
| 지식 그래프 선언 | 사실상 표준 | [things, not strings](https://blog.google/products/search/introducing-knowledge-graph-things-not/) |
| 그래프 질의 언어 GQL | 표준 | [ISO/IEC 39075:2024](https://www.iso.org/standard/76120.html) |
| Cypher 질의 언어 | 사실상 표준 | [Cypher Manual](https://neo4j.com/docs/cypher-manual/current/) |
| RDF-star 트리플 항 | 표준 | [RDF 1.2 triple terms](https://www.w3.org/TR/rdf12-concepts/) |
| 이름 붙인 그래프 | 표준 | [RDF Datasets](https://www.w3.org/TR/rdf11-datasets/) |
| 임베디드 그래프 엔진 | 사실상 표준 | [Kuzu](https://github.com/kuzudb/kuzu) |

관련 예제: `code/model.py`, `code/ex1_two_models.py`, `code/ex2_edge_properties.py`, `code/ex3_cypher_vs_sparql.py`, `code/ex4_things_not_strings.py`
