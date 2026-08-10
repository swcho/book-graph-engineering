# RDF-star 방식은 무엇이며 어떤 장단점이 있는가?

> **카드 답**
> `<< ex:Gaon ex:signed ex:C2025118 >>`처럼 트리플 자체를 주어로 쓴다. 원래 엣지가 남아 기존 질의가 깨지지 않지만, 아직 후보 권고안 단계다.

확인 시점: **2026년 8월 10일**. 이 문서의 표준 현황은 이 날짜 기준으로 W3C `/TR/` 원문을 직접 확인한 것이다.

---

## 1. 문제의 출발점 — RDF에는 「엣지에 속성을 다는 자리」가 없다

프로퍼티 그래프(LPG)에서는 엣지가 속성 주머니를 하나씩 갖는다. 5장 `model.py`의 LPG 쪽은 한 줄이다.

```python
{"from": "n1", "type": "SIGNED", "to": "n2",
 "props": {"at": "2025-06-02", "channel": "직접", "confidence": 0.98}}
```

RDF의 트리플은 `(주어, 술어, 목적어)` 세 칸뿐이다. `ex:Gaon ex:signed ex:C2025118 .` 에 「언제, 어떤 경로로, 얼마나 확실하게」를 붙일 네 번째 칸이 없다. 그래서 RDF는 우회로 세 개를 준비해 두었고, 5장 `ex2_edge_properties.py`가 그 셋을 나란히 놓는다.

| 방법 | 줄 수 | 핵심 대가 |
|---|---|---|
| (1) 구체화 — 관계를 노드로 승격 | 6줄 | **원래 `ex:signed` 엣지가 사라진다. 기존 질의가 전부 깨진다.** |
| (2) RDF-star — 트리플 자체를 주어로 | 4줄 | 원래 엣지가 남아 질의가 안 깨진다. **대신 표준이 아직 확정 전이다.** |
| (3) 이름 붙인 그래프 | 3줄 | 트리플 *묶음* 단위라, 엣지 하나만 가리키려면 묶음도 하나짜리로 만들어야 한다. |

이 카드는 (2)를 (1)과 대비해서 이해하는 카드다.

---

## 2. 세 방법을 코드로 나란히

### (1) 구체화 — 관계를 노드로 승격

```turtle
ex:Gaon      ex:hasSigning ex:Signing1 .
ex:Signing1  rdf:type      ex:Signing .
ex:Signing1  ex:contract   ex:C2025118 .
ex:Signing1  ex:at         "2025-06-02"^^xsd:date .
ex:Signing1  ex:channel    "직접" .
ex:Signing1  ex:confidence "0.98"^^xsd:decimal .
```

`ex:signed`라는 술어가 **어디에도 없다.** 관계가 `ex:Signing1`이라는 노드로 승격되면서, 원래 한 칸이었던 엣지가 `ex:hasSigning` + `ex:contract` 두 홉으로 쪼개졌다.

> 참고로 이 패턴은 RDF 1.1의 「표준 구체화 어휘」(`rdf:Statement` / `rdf:subject` / `rdf:predicate` / `rdf:object`, 트리플 4개 추가)와는 다른, 이른바 **n항 관계·사건 노드(event node)** 패턴이다. 실무에서 「구체화」라고 말할 때 셋 중 어느 쪽인지(표준 구체화 어휘 / 사건 노드 / 싱글톤 프로퍼티) 먼저 확인하는 게 좋다. 5장 예제는 사건 노드 쪽이다.

### (2) RDF-star

```turtle
ex:Gaon ex:signed ex:C2025118 .
<< ex:Gaon ex:signed ex:C2025118 >> ex:at         "2025-06-02"^^xsd:date .
<< ex:Gaon ex:signed ex:C2025118 >> ex:channel    "직접" .
<< ex:Gaon ex:signed ex:C2025118 >> ex:confidence "0.98"^^xsd:decimal .
```

첫 줄이 그대로 남아 있다는 게 이 방법의 전부다. 나머지 세 줄은 그 첫 줄을 「가리켜서」 메타데이터를 붙인다.

### (3) 이름 붙인 그래프

```trig
GRAPH ex:g1 { ex:Gaon ex:signed ex:C2025118 . }
ex:g1 ex:at      "2025-06-02"^^xsd:date .
ex:g1 ex:channel "직접" .
```

가장 짧고 RDF 1.1로 이미 표준이다. 문제는 단위다. `ex:g1`은 트리플 묶음이므로, 엣지 하나에만 신뢰도를 달려면 트리플 하나만 든 그래프를 계약마다 하나씩 만들어야 한다. 그래프 수가 엣지 수만큼 늘어나고, 그래프 이름이 사실상 엣지 ID가 된다. 게다가 기본 그래프에서 `?c ex:signed ?new`로 찾던 질의는 **트리플이 명명 그래프로 옮겨간 순간 안 잡힌다**(엔진이 union default graph로 동작하지 않는 한). 즉 (3)도 (1)만큼은 아니지만 질의를 건드린다.

---

## 3. 「기존 질의가 깨지지 않는다」가 구체적으로 무슨 뜻인가

5장 `ex3_cypher_vs_sparql.py`에 실제로 돌아가는 SPARQL 질의가 있다. 이 질의가 리트머스지다.

```sparql
PREFIX ex: <http://example.org/>
SELECT ?고객 ?해지 ?재계약 WHERE {
    ?c ex:name ?고객 ;
       ex:terminated ?old ;
       ex:signed     ?new .      # ← 이 한 줄이 관건
    ?old ex:endedOn   ?해지 .
    ?new ex:startedOn ?재계약 .
    FILTER(?해지 < ?재계약)
}
```

**(1) 구체화로 갈아타면** 그래프에 `ex:signed`가 없으므로 `?c ex:signed ?new` 가 0건이 되고, 질의 전체가 빈 결과를 낸다. 고쳐 쓰려면 이렇게 된다.

```sparql
    ?c ex:hasSigning/ex:contract ?new .   # 프로퍼티 경로로 두 홉을 건너야 한다
```

한 줄짜리 수정처럼 보이지만, 실무에서 이 한 줄은 **`ex:signed`를 쓰는 모든 질의, 모든 SHACL 도형, 모든 대시보드, 모든 추론 규칙, 팀 위키의 모든 예제**를 뜻한다. 게다가 `ex:signed`를 참조하는 외부 데이터셋이나 온톨로지(다른 팀이 `owl:ObjectProperty ex:signed`에 맞춰 만든 것)까지 끌려온다. 5장의 「RDF로 시작했다가 4개월 만에 갈아탔다」는 도입부가 이 종류의 비용을 말한다.

**(2) RDF-star로 가면** `ex:Gaon ex:signed ex:C2025118 .` 이 여전히 **주장된 트리플(asserted triple)** 로 그래프 안에 남는다. 그래서 위 질의는 **한 글자도 고치지 않고 그대로 같은 답을 낸다.** 새로 붙인 메타데이터는 그 위에 얹힌 별도 레이어이고, 그것을 안 보는 질의는 그것의 존재를 모른다. 이게 「기존 질의가 깨지지 않는다」의 정확한 뜻이다.

즉 세 방법의 진짜 차이는 표기 길이(6줄 / 4줄 / 3줄)가 아니라 **기존 술어를 보존하느냐**다.

> **중요한 단서**: 보존은 자동이 아니다. `<< s p o >> ...` 만 쓰면 `s p o` 는 **주장되지 않는다.** RDF 1.2 Turtle이 명시한다 — *"this graph does not assert that employee38 has a jobTitle of 'Assistant Designer'; it says that employee22 has made that claim"*. 5장 예제가 첫 줄에 평범한 트리플을 따로 적어 둔 것은 실수가 아니라 필수다. 이렇게 주장된 트리플과 그것을 가리키는 메타데이터가 함께 있는 모양을 RDF 1.2는 **트리플 주석(triple annotation)** 이라 부른다. 반대로 「알리스의 성이 Liddell인지 확신이 없다」처럼 **주장하지 않고 언급만** 하는 것도 가능하며, 그게 트리플 항의 원래 설계 의도다.

---

## 4. 2026년 8월 기준 표준 현황 — 카드의 「후보 권고안」은 정확한가

카드가 말하는 대로 아직 권고안(REC)이 아니다. 다만 문서마다 성숙도가 갈라져 있고, **하필 문법을 정의하는 문서들이 더 뒤에 있다.**

| 문서 | 2026-08-10 기준 상태 | 날짜 |
|---|---|---|
| [RDF 1.2 Concepts](https://www.w3.org/TR/rdf12-concepts/) | **Candidate Recommendation Snapshot** | 2026-04-07 |
| [RDF 1.2 Semantics](https://www.w3.org/TR/rdf12-semantics/) | **Candidate Recommendation Snapshot** | 2026-04-07 |
| [RDF 1.2 Turtle](https://www.w3.org/TR/rdf12-turtle/) | **Working Draft** | 2026-07-30 |
| [RDF 1.2 Primer](https://www.w3.org/TR/rdf12-primer/) | Group Note Draft | 2026-04-16 |
| [SPARQL 1.2 Query Language](https://www.w3.org/TR/sparql12-query/) | **Working Draft** | 2026-06-25 |

읽는 법:

- **추상 모델과 의미론은 CR까지 갔다.** Concepts 문서는 "This Candidate Recommendation is not expected to advance to Recommendation any earlier than 05 May 2026"라고 적어 두었고, CR을 나가려면 워킹 그룹 규칙상 **테스트 스위트의 각 테스트를 통과하는 독립 구현이 최소 둘** 있어야 한다. 그 문턱을 아직 넘지 못한 상태다.
- **정작 우리가 코드에 타이핑하는 것(Turtle 문법, SPARQL 문법)은 CR이 아니라 Working Draft다.** 그리고 Turtle은 2026년 4월판에서 7월 30일판으로 다시 갱신되었다. 즉 카드의 「후보 권고안 단계」는 관대하게 표현한 쪽이고, **문법 층은 그보다 한 단계 더 이르다.**
- RDF 1.2 / SPARQL 1.2는 RDF 1.1 / SPARQL 1.1과 **호환**을 유지한다는 게 워킹 그룹 방침이다. 기존 RDF 1.1 데이터·질의가 깨지는 일은 없다. 위험은 「RDF 1.1 → 1.2」가 아니라 **「RDF-star 초안 → RDF 1.2」** 구간에 있다.

---

## 5. 카드의 `<< >>` 표기가 지금은 뜻이 달라졌다 — 가장 실무적인 함정

RDF-star라는 이름은 원래 W3C **RDF-star Community Group** 리포트(2021-12-17판)에서 왔다. 그 초안과 지금의 RDF 1.2는 **설계가 상당히 다르다.** 여기가 이 카드에서 가장 값나가는 부분이다.

### 5.1 초안 → RDF 1.2 변경 요약

| 항목 | RDF-star CG 초안 (2021) | RDF 1.2 (2026) |
|---|---|---|
| 트리플을 항으로 쓰는 표기 | `<< s p o >>` (인용 트리플, quoted triple) | `<<( s p o )>>` (**트리플 항**, triple term) |
| `<< s p o >>` 의 뜻 | 트리플 항 그 자체 | **구체화 트리플의 문법 설탕** — 리이파이어(reifier)를 뜻한다 |
| 메타데이터 붙이는 뼈대 | 인용 트리플에 직접 술어를 건다 | `리이파이어 rdf:reifies <<( s p o )>>` 를 거치고, 술어는 **리이파이어**에 건다 |
| 트리플 항을 쓸 수 있는 자리 | 주어·목적어 양쪽 | **`rdf:reifies` 의 목적어 자리로 사실상 제한** (Turtle 문법의 `subject` 생성 규칙에 `tripleTerm`이 없다) |
| 참조 투명성 | **참조 불투명(opaque)** — 같은 것을 가리키는 다른 IRI로 쓴 두 인용 트리플은 서로 다른 항 | **투명(transparent)** — *"RDF terms that appear in a triple term have the same denotation as when they appear in an asserted triple"* |
| 같은 `<< s p o >>` 를 여러 줄에 반복 | 같은 항이므로 메타데이터가 한곳에 모인다 | **줄마다 새 빈 노드 리이파이어가 생긴다** |

RDF 1.2가 `rdf:reifies` 와 리이파이어를 도입한 이유는, 「트리플을 인용한다」보다 **「그 명제와 관련된 무언가에 이름을 준다」** 가 더 넓은 요구를 담기 때문이다. 리이파이어는 그 명제가 참이라는 *주장*일 수도, *신념*일 수도, 그 명제가 성립하는 *상황*이나 그것을 성립시킨 *사건*일 수도 있다. Concepts 문서는 *"It is expected that the reifiers (rather than the triple terms) will be used in further statements"* 라고 못 박는다.

### 5.2 그래서 5장 예제는 지금 어떻게 읽히나

```turtle
ex:Gaon ex:signed ex:C2025118 .
<< ex:Gaon ex:signed ex:C2025118 >> ex:at         "2025-06-02"^^xsd:date .
<< ex:Gaon ex:signed ex:C2025118 >> ex:channel    "직접" .
<< ex:Gaon ex:signed ex:C2025118 >> ex:confidence "0.98"^^xsd:decimal .
```

RDF 1.2 Turtle에서 이 문서는 **문법 오류가 아니다.** `triples ::= ... | (reifiedTriple predicateObjectList?)` 이므로 그대로 파싱된다. 그런데 스펙에 이런 문장이 있다.

> *"If no reifiers are present, or a reifier is not immediately followed by an iri or BlankNode, a fresh RDF blank node is allocated."*

`~` 로 리이파이어를 명시하지 않았으므로 **줄마다 새 빈 노드가 하나씩** 만들어진다. 완전히 펼치면 이렇게 된다.

```turtle
ex:Gaon ex:signed ex:C2025118 .

_:b0 rdf:reifies <<( ex:Gaon ex:signed ex:C2025118 )>> .
_:b0 ex:at "2025-06-02"^^xsd:date .

_:b1 rdf:reifies <<( ex:Gaon ex:signed ex:C2025118 )>> .   # ← 다른 빈 노드!
_:b1 ex:channel "직접" .

_:b2 rdf:reifies <<( ex:Gaon ex:signed ex:C2025118 )>> .   # ← 또 다른 빈 노드!
_:b2 ex:confidence "0.98"^^xsd:decimal .
```

**세 속성이 세 개의 서로 다른 「서명 사건」에 흩어졌다.** RDF-star 초안에서는 `<< ... >>` 가 동일한 인용 트리플 항이었으므로 세 속성이 한곳에 모였다. 구체적 실패 시나리오는 이렇다.

```sparql
# "시각과 경로가 동시에 기록된 서명"을 찾는 질의 → 0건
SELECT ?시각 ?경로 WHERE {
  ?r rdf:reifies <<( ex:Gaon ex:signed ex:C2025118 )>> .
  ?r ex:at ?시각 .
  ?r ex:channel ?경로 .    # 어떤 ?r 도 at 과 channel 을 같이 갖지 않는다
}
```

파서는 통과, 적재도 통과, 질의만 조용히 0건. **에러 없이 뜻이 바뀌는** 종류의 비호환이라 가장 잡기 어렵다. 같은 함정을 스펙 자체가 예시로 든다 — 한 줄에 `;` 로 이어 쓴 것과 두 줄로 나눠 쓴 것이 이제 **같지 않다**(전자는 리이파이어 하나, 후자는 둘).

### 5.3 RDF 1.2로 제대로 옮기면

**방법 A — 리이파이어에 이름을 준다** (`~` 사용):

```turtle
VERSION "1.2"
PREFIX ex:  <http://example.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

ex:Gaon ex:signed ex:C2025118 .
<< ex:Gaon ex:signed ex:C2025118 ~ ex:sign1 >>
    ex:at         "2025-06-02"^^xsd:date ;
    ex:channel    "직접" ;
    ex:confidence "0.98"^^xsd:decimal .
```

**방법 B — 주석 문법 `{| ... |}`** (한 방에 「주장 + 구체화」, LPG의 한 줄에 가장 가깝다):

```turtle
VERSION "1.2"
PREFIX ex:  <http://example.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

ex:Gaon ex:signed ex:C2025118 ~ ex:sign1 {|
    ex:at         "2025-06-02"^^xsd:date ;
    ex:channel    "직접" ;
    ex:confidence "0.98"^^xsd:decimal
|} .
```

둘 다 이 다섯 트리플로 펼쳐진다(방법 A는 첫 줄을 직접 적었고, B는 주석 문법이 자동으로 주장해 준다).

```turtle
ex:Gaon  ex:signed  ex:C2025118 .
ex:sign1 rdf:reifies <<( ex:Gaon ex:signed ex:C2025118 )>> .
ex:sign1 ex:at         "2025-06-02"^^xsd:date .
ex:sign1 ex:channel    "직접" .
ex:sign1 ex:confidence "0.98"^^xsd:decimal .
```

`ex:sign1` 이라는 이름이 붙었으니 나중에 「이 서명을 누가 검증했는지」를 또 얹을 수 있다. 그리고 **`ex:signed` 는 여전히 거기 있다.** 이게 (1) 구체화와의 결정적 차이다 — 구체화도 `ex:Signing1` 이라는 이름을 만들지만, 그 대가로 `ex:signed` 를 지웠다. RDF-star/1.2는 **이름을 만들면서 원래 술어도 남긴다.**

> 사족: `{| ... |}` 블록을 리이파이어 없이 쓰면 다시 새 빈 노드가 배정된다. 두 블록을 나란히 쓰면 리이파이어가 둘 생긴다(스펙 Example 31-32). 「같은 엣지에 대한 메타데이터인가, 서로 다른 출처의 서로 다른 주장인가」를 의식적으로 골라 `~` 를 쓰거나 안 쓰는 습관이 필요하다.

---

## 6. SPARQL 1.2로 질의하기

**주석 문법 (Turtle과 대칭):**

```sparql
VERSION "1.2"
PREFIX ex: <http://example.org/>
SELECT ?고객 ?계약 ?시각 ?신뢰도 WHERE {
    ?c ex:name ?고객 .
    ?c ex:signed ?계약 ~ ?r {| ex:at ?시각 ; ex:confidence ?신뢰도 |}
}
```

**펼친 형태 (`rdf:reifies` 를 직접 쓴다):**

```sparql
VERSION "1.2"
PREFIX ex:  <http://example.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?고객 ?시각 WHERE {
    ?c ex:name ?고객 ; ex:signed ?계약 .
    ?r rdf:reifies <<( ?c ex:signed ?계약 )>> .
    ?r ex:at ?시각 .
}
```

알아둘 것들:

- `VERSION "1.2"` **버전 선언 지시자**가 새로 생겼다. 1.2 기능을 쓰려면 질의/문서에 명시하거나 미디어 타입의 `version` 파라미터로 알린다.
- 트리플 항을 다루는 함수군이 생겼다: `TRIPLE(s, p, o)`, `SUBJECT`, `PREDICATE`, `OBJECT`, `isTRIPLE`. `<<( ... )>>` 는 `TRIPLE()` 의 축약형이고 **인자에 변수나 직접 쓴 RDF 항만** 올 수 있다(임의 식은 `TRIPLE()` 함수형으로).
- `BIND( <<( ?s ?p ?o )>> AS ?tt )` 로 트리플 항을 변수에 담을 수 있다.

---

## 7. 후보 권고안 단계가 실무에서 뜻하는 위험

카드의 「아직 후보 권고안 단계다」를 한 줄로만 외우면 「곧 나오겠네」로 오해한다. 실제 위험은 셋이다.

### 위험 1 — 엔진마다 「어느 시점의 초안」을 구현했는지가 다르다

같은 `<<` 두 글자가 엔진마다 다른 뜻이다.

| 엔진 | 2026-08 기준 상황 |
|---|---|
| **Oxigraph** | RDF-star 초안을 **버리고** RDF 1.2로 갈아탔다. 이관 논의 이슈(#1286)에서 「RDF-star와 RDF 1.2를 동시에 투명하게 구현하는 것은 불가능하다」고 결론 내렸다. NQuads로 덤프해서 다시 적재하는 흔한 이관 방식은 **트리플 항 등장마다 새 빈 노드를 만들어 버려서 잘 동작하지 않는다**는 점까지 명시되어 있다. 별도로 「RDF 1.2 메타 질의가 매우 느리다」(#1687, 2026-04)와 주석 문법 결과 누락 버그(#1493)가 있었다. |
| **Apache Jena** | RDF-star 초안 문법을 오래 지원해 왔고, RDF 1.2 대응은 진행 중이다(#2805 "Support RDF 1.2" 열림). 2026년에도 관련 버그가 계속 잡히고 있다 — `CONSTRUCT` 에서 `rdf:reifies` 트리플이 누락되는 문제(#4129), 트리플 항의 잘못된 주어를 걸러내지 못하는 문법 검사 구멍(#4141, **2026-08-10 갱신**). |
| **Eclipse RDF4J** | RDF 1.2 대응이 활발하지만 **아직 조각이 빠져 있다.** NativeStore의 트리플 항 지원이 미완(#5938, 2026-07), RDF 1.2 Basic / RDF 1.1 직렬화 분리(#5949), 문서 갱신(#5954) 모두 열린 상태다. |
| **Ontotext GraphDB** | RDF-star / SPARQL-star를 문서화해 지원하며 인용 트리플을 영속화한다. 다만 문서 서술이 **`<< >>` = 임베디드 트리플**이라는 초안 모델에 기반해 있다. |
| **AllegroGraph** 등 상용 | 각자 RDF-star 지원을 광고하지만, 어느 초안 기준인지는 제품 문서를 확인해야 한다. |
| **Neo4j / Kuzu 등 LPG 엔진** | 애초에 무관하다. 엣지 속성이 모델의 기본이라 이 논쟁 자체가 없다. |

실무 결론: **「RDF-star 지원」이라는 체크박스를 믿지 말고, `<<( )>>` 를 파싱하는지 · `rdf:reifies` 를 이해하는지 · `~` 와 `{| |}` 를 지원하는지 · 같은 `<< >>` 를 반복했을 때 리이파이어를 몇 개 만드는지 네 가지를 직접 찔러 봐야 한다.** 5장 마지막 조언(「질의 다섯 개를 두 언어로 써 보는 반나절」)을 여기에 그대로 적용하면 된다.

### 위험 2 — 저장된 데이터가 문법 변경에 인질로 잡힌다

질의는 고칠 수 있지만 적재된 데이터는 다르다. Oxigraph 사례가 정확히 그 문제였다. 트리플 항이 이제 주어 자리에 못 오게 되면서, 기존 데이터를 그냥 들고 있는 「멍청한 이관」이 불가능해졌고, 결국 **트리플 항의 해시를 빈 노드 식별자로 만들어 `rdf:reifies` 트리플을 새로 끼워 넣는 자동 이관**을 논의해야 했다. 데이터가 수억 트리플이라면 이건 반나절짜리 작업이 아니다.

### 위험 3 — 의미론이 바뀌면 추론 결과가 바뀐다

참조 불투명 → 투명 전환은 문법이 아니라 **의미론** 변경이다. 초안에서는 `ex:Gaon` 과 `ex:가온테크` 가 `owl:sameAs` 여도 두 인용 트리플은 서로 다른 항이었다. RDF 1.2에서는 트리플 항 안의 항도 바깥과 같은 것을 가리킨다. 동일성 추론이나 스마트 매칭이 걸린 그래프에서는 **같은 데이터·같은 질의인데 답이 달라질 수 있다.** 문자열 치환으로는 못 잡는 종류의 차이다.

---

## 8. 그래서 실무에서 어떻게 고를 것인가

5장의 기준선은 단순하다.

> **관계의 30% 이상에 속성이 붙으면 LPG. 그 밑이면 RDF.**

RDF를 골랐다면, 그 안에서의 선택을 이렇게 정리할 수 있다.

| 상황 | 권장 | 이유 |
|---|---|---|
| 관계 자체가 1급 개체다 (서명 사건에 참여자·승인자·첨부문서가 붙는다) | **(1) 구체화(사건 노드)** | 어차피 노드가 필요하다. RDF 1.1이라 어디서나 돌아간다. 대신 술어 이름 변경 비용을 처음부터 치르고 시작하라. |
| 출처·시각·신뢰도 같은 **얇은 메타데이터**를 기존 술어를 살린 채로 얹고 싶다 | **(2) RDF-star / RDF 1.2** | 기존 질의가 안 깨진다. 단, 아래 조건부. |
| 데이터 **묶음** 단위 출처·버전·적재 배치를 관리한다 | **(3) 이름 붙인 그래프** | 이미 표준이고 모든 엔진이 지원한다. 엣지 단위로 쓰지만 마라. |
| 관계마다 속성이 기본으로 붙는다 | **LPG로 간다** | RDF의 세 우회로 어느 것도 편하지 않다. |

(2)를 고를 때의 방어 수칙:

1. **`~` 로 리이파이어에 항상 IRI 이름을 준다.** 빈 노드에 맡기지 마라. 위 5.2의 조용한 0건 사고가 이 한 줄로 사라진다.
2. **같은 엣지에 속성 여러 개는 `{| ... |}` 한 블록으로 묶는다.** 줄을 나누는 순간 뜻이 달라진다.
3. **저장은 `rdf:reifies` 펼친 형태로 생각한다.** `<< >>` 는 어디까지나 문법 설탕이고, 엔진 간 이식성은 펼친 형태에 있다.
4. **엔진 버전을 문서에 못 박고 회귀 테스트를 둔다.** 5장이 「확인 시점 2026년 8월, Kuzu 0.11.3, rdflib 7.5.0」을 적어 둔 것과 같은 습관이다.
5. **RDF 1.1로 되돌릴 탈출구를 남긴다.** 최악의 경우 리이파이어 기반 표현은 평범한 트리플로 그대로 내려앉으므로(그게 RDF 1.2 설계의 장점이다) `<< >>` 문법에 코드가 의존하지 않게만 해 두면 된다.

---

## 9. 한 줄로 다시

**RDF-star(현행 RDF 1.2)는 「엣지를 지우지 않고 엣지에 이름을 붙이는」 방법이다.** 그래서 기존 술어를 쓰던 질의·온톨로지·대시보드가 그대로 산다 — 구체화가 치르는 가장 큰 비용을 안 치른다. 대가는 표준의 미성숙이다. 추상 모델은 후보 권고안(2026-04-07)까지 갔지만 **Turtle과 SPARQL 문법은 아직 초안(Working Draft, 2026-07/06)** 이고, 무엇보다 이름의 출처인 RDF-star 초안과 현행 RDF 1.2는 `<< >>` 의 뜻 자체가 다르다. 「RDF-star 지원」이라는 말을 들으면 **어느 초안 기준인지 되물어야 한다.**

---

## 출처

- [RDF 1.2 Concepts and Abstract Data Model](https://www.w3.org/TR/rdf12-concepts/) — W3C Candidate Recommendation Snapshot, 2026-04-07 (§1.5 Triple Terms and Reification, §3.6 Triple Terms, §H Changes)
- [RDF 1.2 Semantics](https://www.w3.org/TR/rdf12-semantics/) — W3C Candidate Recommendation Snapshot, 2026-04-07
- [RDF 1.2 Turtle](https://www.w3.org/TR/rdf12-turtle/) — W3C Working Draft, 2026-07-30 (§2.11 Reified Triples, §2.11.1 Annotation Syntax, §6 Grammar)
- [RDF 1.2 Primer](https://www.w3.org/TR/rdf12-primer/) — W3C Group Note Draft, 2026-04-16
- [SPARQL 1.2 Query Language](https://www.w3.org/TR/sparql12-query/) — W3C Working Draft, 2026-06-25 (§4.3 Version Announcement, §17.4.6 Functions on Triple Terms, §19.7 Grammar)
- [RDF Datasets (RDF 1.1)](https://www.w3.org/TR/rdf11-datasets/) — 이름 붙인 그래프
- [RDF-star and SPARQL-star, CG Final Community Group Report (2021-12-17)](https://w3c.github.io/rdf-star/cg-spec/2021-12-17.html) — 「RDF-star」라는 이름의 출처, 인용 트리플·참조 불투명
- [oxigraph/oxigraph#1286 — Migration from RDF-star to RDF 1.2](https://github.com/oxigraph/oxigraph/issues/1286) — 초안 대비 변경점과 이관 불가능성 정리
- [oxigraph/oxigraph#1687 — rdf 1.2 meta queries very slow](https://github.com/oxigraph/oxigraph/issues/1687)
- [apache/jena#2805 — Support RDF 1.2](https://github.com/apache/jena/issues/2805), [#4129](https://github.com/apache/jena/issues/4129), [#4141](https://github.com/apache/jena/issues/4141)
- [eclipse-rdf4j/rdf4j#5938 — RDF 1.2 triple terms in NativeStore](https://github.com/eclipse-rdf4j/rdf4j/issues/5938), [#5406 RDF 1.2 PR Tracking](https://github.com/eclipse-rdf4j/rdf4j/issues/5406)
- [Apache Jena — Support of RDF-star](https://jena.apache.org/documentation/rdf-star/)
- [GraphDB 11.3 — RDF-star and SPARQL-star](https://graphdb.ontotext.com/documentation/11.3/rdf-sparql-star.html)
- [AllegroGraph — RDF-Star Support](https://franz.com/agraph/support/documentation/rdf-star.html)
- 5장 예제: `code/model.py` (`RDF_REIFIED` / `RDF_STAR` / `RDF_NAMED_GRAPH`), `code/ex2_edge_properties.py`, `code/ex3_cypher_vs_sparql.py`
