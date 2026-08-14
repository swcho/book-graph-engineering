# SKOS는 무엇을 위한 표준인가?

**답**: 개념 체계(concept scheme) 어휘를 표현하기 위한 W3C 표준이다.

---

## 한 줄 정리

SKOS(Simple Knowledge Organization System)는 **시소러스·분류표·주제어 목록·용어집처럼 이미 사람이 쓰고 있던 «개념 체계»를, 다시 설계하지 않고 그대로 웹에 올려 기계가 읽게 만드는 RDF 어휘**입니다. W3C 권고안(Recommendation, 2009-08-18)이고 네임스페이스는 `http://www.w3.org/2004/02/skos/core#`입니다.

명세 자신의 표현으로는 "지식 조직 체계(KOS)를 웹을 통해 공유하고 연결하기 위한 공통 데이터 모델"입니다.

---

## 왜 이런 표준이 따로 필요했나

도서관 주제어표, 산업 분류 코드, 회사 위키의 태그 체계 같은 것들은 이미 수십 년치가 쌓여 있습니다. 그런데 이것들은 **논리적 공리의 집합이 아닙니다**. "부품은 제품의 부분집합이다" 같은 정의가 아니라, 그냥 "이 낱말은 저 낱말보다 넓다" 정도의 사람끼리의 합의입니다.

이걸 OWL 온톨로지로 옮기려면 "이 상위/하위 관계가 subClassOf인가 part-of인가"를 항목마다 결정해야 합니다. 214개짜리 분류표를 그렇게 재설계하는 순간, 그건 이미 «이전»이 아니라 «재구축»입니다.

SKOS는 그 결정을 **하지 않아도 되게** 만든 표준입니다. 상위/하위를 `skos:broader`/`skos:narrower`라는 의도적으로 느슨한 관계로 두어서, 기존 체계를 원래 모양 그대로 RDF로 옮길 수 있게 합니다. 명세는 이걸 "저비용 이전(low-cost migration)"이라고 부릅니다.

---

## 핵심 어휘

### 클래스

| 어휘 | 뜻 |
|---|---|
| `skos:Concept` | 개념 하나. 지식 조직 체계의 기본 단위 |
| `skos:ConceptScheme` | 개념들의 묶음. 시소러스/분류표 한 벌에 대응 |
| `skos:Collection` | 개념들을 묶어 이름 붙인 그룹 (개념 자체는 아님) |
| `skos:OrderedCollection` | 순서가 있는 Collection. `skos:memberList`로 순서 표현 |

### 레이블 (사람이 읽는 이름)

| 어휘 | 뜻 |
|---|---|
| `skos:prefLabel` | 대표 이름. **언어 태그당 최대 하나** |
| `skos:altLabel` | 동의어·약어·이형 표기 |
| `skos:hiddenLabel` | 검색에는 걸리되 화면에는 안 보이는 이름 (오타 흡수용) |

셋은 서로 **disjoint**입니다. 같은 문자열을 prefLabel이면서 altLabel로 둘 수 없습니다.

이게 [5장 「문자열이 아니라 사물」](../../../ch05%205장%20-%20문자열이%20아니라%20사물/)과 맞물립니다. 개념의 정체성은 IRI가 갖고, 문자열은 전부 레이블로 밀려납니다. "M6 스테인리스 육각볼트", "M6 SUS 육각볼트", "M6 hex bolt (SUS)"는 개념 하나에 붙은 prefLabel/altLabel/altLabel입니다.

### 의미 관계

| 어휘 | 성질 |
|---|---|
| `skos:broader` / `skos:narrower` | 직접 상위/하위. **전이적이지 않음** (의도적) |
| `skos:broaderTransitive` / `skos:narrowerTransitive` | 간접까지 포함. 전이적 |
| `skos:related` | 계층이 아닌 연관. 대칭, 비전이적 |
| `skos:semanticRelation` | 위 관계들의 상위 프로퍼티 |

`skos:related`와 `skos:broaderTransitive`는 disjoint입니다. 조상이면서 동시에 «관련»일 수 없습니다.

**`broader`가 전이적이 아닌 이유**가 SKOS의 성격을 가장 잘 보여 줍니다. 실제 분류표에서 A→B→C 계층이 "A는 B의 종류 → B는 C의 종류"일 수도, "A는 B의 부분 → B는 C의 종류"일 수도 있습니다. 전자만 전이가 성립합니다. 어느 쪽인지 모르는 채로 옮겨야 하니, 전이를 **기본에서 뺐습니다**. 전이 추론이 안전하다고 판단한 곳에서만 `broaderTransitive`를 명시하면 됩니다.

### 문서화·식별

| 어휘 | 뜻 |
|---|---|
| `skos:definition` | 정의문 |
| `skos:scopeNote` | 이 개념을 어디까지 쓰는지 |
| `skos:example`, `skos:note`, `skos:editorialNote`, `skos:historyNote`, `skos:changeNote` | 각종 주석 (`skos:note`가 상위) |
| `skos:notation` | 체계 내 코드값 (예: `"303.4833"`) |
| `skos:inScheme` | 이 개념이 속한 체계 |
| `skos:hasTopConcept` / `skos:topConceptOf` | 체계의 최상위 개념 |

### 매핑 (다른 체계와 잇기) — **12장에서 실제로 쓰이는 부분**

| 어휘 | 성질 |
|---|---|
| `skos:exactMatch` | 사실상 같음. 전이적, 대칭 |
| `skos:closeMatch` | 어떤 용도에서는 같다고 봐도 됨. 대칭, **비전이적** |
| `skos:broadMatch` / `skos:narrowMatch` | 체계를 넘는 상위/하위 |
| `skos:relatedMatch` | 체계를 넘는 연관 |
| `skos:mappingRelation` | 위 매핑들의 상위 프로퍼티 |

---

## SKOS vs OWL — 이게 핵심 대비

| | SKOS | OWL |
|---|---|---|
| 개념의 정체 | `skos:Concept`의 **인스턴스(개체)** | `owl:Class` |
| 계층 | `skos:broader` (느슨한 «더 넓다») | `rdfs:subClassOf` (모든 인스턴스가 포함됨) |
| 담는 것 | 개념에 대한 **사실(fact)** | **공리(axiom)** |
| 형식성 | 반형식적(semi-formal) | 형식적 |
| 추론 | 거의 안 함 | 추론기가 새 사실을 뽑아냄 |
| 목적 | 기존 체계를 «있는 그대로» 옮기기 | 도메인을 논리적으로 정의하기 |

명세의 문장을 그대로 옮기면: "시소러스나 분류 체계는 공리나 사실을 주장하지 않는다. 오히려 서로 구별되는 아이디어 또는 의미의 집합을 식별하고 기술할 뿐이다."

즉 SKOS에서 «자동차 → 탈것`skos:broader`»은 **"모든 자동차는 탈것이다"라는 주장이 아닙니다**. "우리 분류표에서 자동차 항목의 위에 탈것 항목이 놓여 있다"는 서술입니다. 이 차이가 추론기의 동작을 완전히 바꿉니다.

> 참고: SKOS 자체는 OWL로 정의된 온톨로지입니다. 다만 SKOS를 **쓰는** 데이터는 온톨로지가 아니라 개념 목록입니다. 한 리소스에 `skos:Concept`와 `owl:Class`를 동시에 붙이는 하이브리드도 가능하지만, 그러면 OWL Full로 떨어져 대부분의 추론기가 손을 놓습니다. 섞지 않는 편이 안전합니다.

---

## 12장에서 SKOS가 등장하는 자리

### 1) 키워드 표 (12장 「키워드와 1차 출처」)

| 키워드 | 상태 | 출처 |
|---|---|---|
| 개념 체계 어휘 | [표준] | [SKOS](https://www.w3.org/TR/skos-reference/) |

`[표준]`은 공식 명세라는 뜻입니다. SHACL, OWL 2 Profiles, RDF Schema, GQL과 같은 줄에 놓여 있고, schema.org만 `[사실상 표준]`으로 구분되어 있습니다.

### 2) `ex4_reuse_or_build.py` — 12.4절 「남의 어휘를 가져다 쓸까」

SKOS가 실제 판단에 쓰이는 곳은 여깁니다. 예제는 필요한 개념마다 공개 어휘와의 **적합도**를 매기고 0.7을 임계값으로 갈라칩니다.

```python
NEEDED = {
    "제품":      {"공개어휘": "schema.org/Product",      "적합도": 0.9},
    "공급사":    {"공개어휘": "schema.org/Organization", "적합도": 0.8},
    "부품":      {"공개어휘": "schema.org/Product",      "적합도": 0.4},
    "리콜":      {"공개어휘": None,                       "적합도": 0.0},
    "대체가능":  {"공개어휘": None,                       "적합도": 0.0},
}
```

결과는 셋으로 갈립니다.

- **0.7 이상** → 그대로 가져다 쓴다 (제품, 공급사)
- **0.7 미만인데 비슷은 함** → 우리 것으로 만들고 «대략 같음»만 걸어 둔다 (부품)
- **공개 어휘에 아예 없음** → 만든다 (리콜, 대체가능)

문제는 **부품(0.4)**입니다. schema.org에도 `Product`가 있지만 뜻이 다릅니다. 예제의 설명을 그대로 옮기면:

> 우리에게 부품은 «다른 제품 안에 들어가는 것»이고, 판매 단위가 아니다.
>
> 여기서 두 가지 실수가 가능하다.
>   (가) 억지로 맞춰 쓴다 → 나중에 «부품인데 왜 가격이 있지» 같은 혼란이 생긴다
>   (나) 아예 무시하고 다 새로 만든다 → 밖과 데이터를 주고받을 때 매번 변환한다
>
> 중간이 답이다. 우리 것으로 만들되, 공개 어휘와 «대략 같음»을 걸어 둔다.
> **RDF 라면 `owl:sameAs` 나 `skos:closeMatch`**, LPG 라면 속성으로 매핑 표를 둔다.

여기서 `owl:sameAs`와 `skos:closeMatch`가 나란히 놓인 게 중요합니다. 둘은 강도가 전혀 다릅니다.

| | `owl:sameAs` | `skos:closeMatch` |
|---|---|---|
| 뜻 | 두 IRI가 **같은 것** | 어떤 용도에서는 바꿔 써도 됨 |
| 추론 | 모든 속성이 양방향으로 **복사됨** | 아무것도 복사 안 됨 |
| 전이 | 전이적 | 비전이적 |
| 위험 | schema.org의 `price`가 우리 «부품»에 들러붙음 | 없음 |

**0.4짜리 적합도에 `owl:sameAs`를 걸면 정확히 예제가 경고한 「부품인데 왜 가격이 있지」가 일어납니다.** 추론기가 schema.org `Product`의 모든 서술을 우리 부품에 밀어 넣기 때문입니다. `skos:closeMatch`는 "닿아 있다"는 기록만 남기고 추론을 일으키지 않습니다. 적합도가 낮을수록 `closeMatch` 쪽입니다.

강도 순서로 정리하면:

```
owl:sameAs        (동일 개체. 가장 강함, 위험도 최고)
  ↓
skos:exactMatch   (개념으로서 사실상 같음. 전이적)
  ↓
skos:closeMatch   (어떤 용도에서는 같음. 비전이적)   ← 부품 = 0.4 는 여기
  ↓
skos:broadMatch / narrowMatch / relatedMatch  (방향/연관만)
```

12장의 표현으로 "우리 것으로 만들고 **사상(mapping)만 걸어 두라**"는 게 정확히 이 줄의 아래쪽을 쓰라는 말입니다.

---

## 언제 SKOS를 쓰고 언제 OWL을 쓰나

**SKOS 쪽**
- 이미 사람이 관리하던 분류표·태그 체계를 옮길 때
- 상위/하위가 subClassOf인지 part-of인지 항목마다 다르거나 불확실할 때
- 다국어 레이블·동의어·약어가 많을 때
- 다른 조직의 어휘와 느슨하게 이어 두고 싶을 때 (`closeMatch`)
- 추론은 필요 없고 **탐색과 검색**이 목적일 때

**OWL 쪽**
- 도메인 제약을 형식적으로 못 박고 추론기로 새 사실을 뽑아야 할 때
- 클래스 정의로 자동 분류(classification)를 돌릴 때

12장의 논조로 보면 SKOS는 「위에서 아래로 6개월 온톨로지를 짓는」 실패를 피하는 도구 쪽에 가깝습니다. 남의 체계를 완벽히 이해해서 논리로 재구축하지 않고, **일단 있는 그대로 옮기고 필요해지면 그때 굳히는** 방식이기 때문입니다.

다만 그 느슨함이 곧 「검증이 없다」는 뜻이기도 합니다. 그래서 12장은 SHACL을 함께 얹고, [13장 「검증하지 않은 그래프는 그냥 링크 뭉치다」](../../../ch13%2013장%20-%20검증하지%20않은%20그래프는%20그냥%20링크%20뭉치다/)로 넘어갑니다.

---

## 시험 대비 한 줄

- **SKOS = 개념 체계(concept scheme) 어휘를 표현하기 위한 W3C 표준.** 시소러스·분류표·태그 체계를 RDF로 옮기는 데이터 모델.
- 핵심 클래스는 `skos:Concept` / `skos:ConceptScheme` / `skos:Collection`.
- 레이블은 `prefLabel`(언어당 1개) / `altLabel` / `hiddenLabel`.
- 계층은 `broader` / `narrower`(**비전이적**), 연관은 `related`.
- 체계 간 연결은 `exactMatch` / `closeMatch` / `broadMatch` / `narrowMatch` / `relatedMatch`.
- OWL과의 차이: SKOS는 개념을 **인스턴스**로 두고 **사실**을 기록하는 반형식적 모델, OWL은 개념을 **클래스**로 두고 **공리**를 기록하는 형식적 모델.
- 12장 용법: 공개 어휘와 적합도가 애매할 때(부품 0.4) `owl:sameAs` 대신 `skos:closeMatch`로 이어 둔다.

## 참고 문헌

- [SKOS Simple Knowledge Organization System Reference (W3C Recommendation)](https://www.w3.org/TR/skos-reference/)
- [SKOS Primer](https://www.w3.org/TR/skos-primer/)
- [Using OWL and SKOS (W3C SWD Working Group)](https://www.w3.org/2006/07/SWD/SKOS/skos-and-owl/master.html)
- [What's SKOS, What's not, Why and What Should be Done (NKOS/ASIST 2015)](https://nkos.dublincore.org/ASIST2015/ASISTBusch-SKOS.pdf)
