# 출처 추적 표준 — W3C PROV-O

**질문** 출처 추적 표준으로 무엇이 제시되는가?
**답** W3C PROV-O다. [표준]으로 분류된다.

---

## 1. 왜 14장에서 PROV-O가 나오는가

14장의 키워드 표는 마지막 줄에서 이렇게 못을 박습니다.

| 키워드 | 상태 | 출처 |
|---|---|---|
| 출처 추적 | **[표준]** | [PROV-O](https://www.w3.org/TR/prov-o/) |

같은 표의 다른 항목들과 상태 라벨을 비교하면 이 카드가 왜 「[표준]」이라는 꼬리표를 달고 있는지가 분명해집니다.

- 엔티티 해상도 / 블로킹 / 확률적 레코드 연결 → **[사실상 표준]** (논문과 관행은 있지만 공식 명세가 없다)
- 동일성 선언(`owl:sameAs`) / 느슨한 동일성(`skos:closeMatch`) / **출처 추적(PROV-O)** → **[표준]** (W3C 공식 권고안)
- 생존 규칙(survivorship rules) → **[실험]**

즉 14장에서 「점수를 매기는 방법」과 「어느 값을 남길지」는 각자 알아서 정해야 하는 영역인데, **「무엇을 언제 누가 왜 합쳤는지 기록하는 형식」만은 이미 표준이 있다**는 뜻입니다. 그 표준이 PROV-O입니다.

14장이 이 표준을 필요로 하는 이유는 두 곳에서 아주 구체적으로 드러납니다.

**(가) 병합 이력** — `ex3_reversible_merge.py`의 `MergeStore`는 병합을 「사건」으로 기록합니다.

```python
self.events.append({"op": "merge", "keep": keep, "drop": drop,
                    "by": by, "reason": reason})
```

`by="auto"`, `reason="사업자번호 일치"`. 이게 바로 출처 추적입니다. 다만 자체 포맷이죠.

**(나) 값 출처** — `ex5_survivorship.py`의 마지막 문장이 이 카드의 정확한 동기입니다.

> 그리고 고른 값마다 «어디서 왔는지»를 같이 저장한다.
> 그게 있어야 «이 대표자 이름 왜 이래요» 라는 문의에 답할 수 있다.

대표자가 「박서준」으로 정해진 이유(= CRM이 가장 최근이라서)를 저장해 두지 않으면, 6개월 뒤에 아무도 이유를 모릅니다. PROV-O는 이 「왜 이 값인가」를 적는 어휘를 제공합니다.

---

## 2. PROV-O 사실 확인 (W3C 권고안)

웹으로 확인한 내용입니다.

| 항목 | 값 |
|---|---|
| 정식 이름 | PROV-O: The PROV Ontology |
| 상태 | **W3C Recommendation** (권고안) |
| 발행일 | **2013년 4월 30일** |
| 명세 URL | <https://www.w3.org/TR/prov-o/> (고정판 `.../TR/2013/REC-prov-o-20130430/`) |
| 네임스페이스 | `http://www.w3.org/ns/prov#` (관례 접두어 `prov:`) |
| 표현 언어 | OWL2 |
| 발행 주체 | W3C Provenance Working Group |

PROV-O는 혼자 나온 게 아니라 PROV 계열의 한 조각입니다.

- **PROV-DM** — 개념 데이터 모델 (PROV-O가 OWL2로 인코딩하는 원본 모델)
- **PROV-O** — 그 모델의 OWL2 온톨로지 ← 14장이 가리키는 것
- **PROV-N** — 사람이 읽기 쉬운 압축 표기
- **PROV-XML** — XML 스키마 직렬화
- **PROV-CONSTRAINTS**, **PROV-AQ**, **PROV-PRIMER**, **PROV-OVERVIEW** 등

「PROV-O」라고 답해야 하는 이유는, 14장이 다루는 대상이 **그래프(RDF/OWL) 안에 이력을 노드와 엣지로 저장하는 일**이기 때문입니다. 같은 모델을 XML로 쓰고 싶으면 PROV-XML이고, 그래프에 넣고 싶으면 PROV-O입니다.

PROV-O는 어휘를 3층으로 나눠 놓았습니다. 이 계층 구조를 아는 게 실무에서 중요합니다.

1. **Starting Point Terms** — 최소 어휘. 대부분 이것만으로 충분합니다.
2. **Expanded Terms** — 하위 클래스·하위 속성으로 더 정밀하게 (`prov:wasRevisionOf`, `prov:hadPrimarySource`, `prov:specializationOf`, `prov:alternateOf` 등)
3. **Qualified Terms** — 관계 자체에 속성을 붙여야 할 때 (`prov:Derivation` + `prov:qualifiedDerivation` 같은 「한정 패턴(Qualification Pattern)」)

---

## 3. 핵심 3개 클래스

PROV-O의 뼈대는 클래스 세 개입니다. 명세의 정의를 그대로 옮기면:

| 클래스 | 명세 정의 | 한 줄 이해 | 14장에서는 |
|---|---|---|---|
| `prov:Entity` | 고정된 측면을 지닌 물리적·디지털·개념적 사물 | **것** (데이터) | 레코드 r01, r02, r04 / 대표 노드 / 병합 결과의 각 필드 값 |
| `prov:Activity` | 일정 기간에 걸쳐 발생하며 엔티티에 작용하는 무언가 | **일** (처리) | 블로킹, 점수 계산, 자동 병합, 사람 검토, unmerge, 생존 규칙 적용 |
| `prov:Agent` | 활동이 일어난 것에 대해 어떤 형태의 책임을 지는 무언가 | **책임자** | 병합 파이프라인(소프트웨어), 판정한 검토자(사람), ERP/CRM/명함스캔 시스템 |

세 클래스를 나눠 놓은 게 별것 없어 보이지만, 이 구분이 14장의 사고를 막습니다. `MergeStore.events`의 `{"by": "auto"}`는 문자열 하나입니다. 「auto」가 어느 버전의 어떤 규칙을 쓴 파이프라인인지, 임계가 0.85였는지 0.55였는지 알 수 없습니다. 14장이 「임계 0.55로 낮췄다가 모회사와 자회사를 합쳐 버렸고 되돌리는 데 사흘 걸렸다」고 고백한 그 사고에서, 정작 필요한 정보는 **어떤 실행(Activity)이 어떤 설정으로 그 병합을 만들었나**입니다. Agent를 노드로 만들어 두면 「이 에이전트가 만든 병합 전부」를 질의 하나로 뽑아 되돌릴 수 있습니다.

`prov:Agent`의 하위 클래스도 유용합니다.

- `prov:SoftwareAgent` — 병합 파이프라인
- `prov:Person` — 검토자
- `prov:Organization` — ERP를 운영하는 부서

---

## 4. 주요 속성 4개와 14장 문제의 대응

| 속성 | 방향 (정의역 → 치역) | 뜻 | 14장에서 답하는 질문 |
|---|---|---|---|
| `prov:wasGeneratedBy` | Entity → Activity | 이 값은 저 처리가 만들었다 | 이 대표 노드는 어느 병합 실행이 만들었나 |
| `prov:used` | Activity → Entity | 저 처리는 이 입력을 썼다 | 그 병합은 어느 레코드들을 입력으로 봤나 |
| `prov:wasDerivedFrom` | Entity → Entity | 이 값은 저 값에서 나왔다 | 이 「박서준」은 어느 레코드의 값에서 왔나 |
| `prov:wasAttributedTo` | Entity → Agent | 이 값의 책임은 저 주체에게 있다 | 누가/무엇이 이 값을 책임지나 |

관계도로 보면 이렇습니다.

```
        prov:wasAttributedTo
   ┌──────────────────────────────► prov:Agent
   │                                (병합 파이프라인 / 검토자 / ERP)
   │                                     ▲
prov:Entity ──prov:wasGeneratedBy──► prov:Activity
 (대표 노드)                          (병합 실행)  │ prov:wasAssociatedWith
   │                                     │
   │                            prov:used│
   │ prov:wasDerivedFrom                 ▼
   └────────────────────────────► prov:Entity
                                   (원본 레코드 r01, r04)
```

`wasDerivedFrom`은 사실 `wasGeneratedBy` + `used`를 지름길로 이은 것입니다. 「출력 ← 처리 ← 입력」 두 홉을 한 홉으로 줄인 셈이죠. 그래서 **어느 값이 어디서 왔는지만 알고 싶으면 `wasDerivedFrom` 하나**, **그 판단의 근거와 시각과 설정까지 알고 싶으면 Activity를 거치는 두 홉**을 씁니다. 14장의 사흘짜리 사고를 수습하려면 두 홉이 필요합니다.

### 4.1 병합 이력 — `MergeStore.events`를 PROV-O로 옮기면

14장 `ex3`의 첫 번째 병합, `s.merge("r01", "r04", by="auto", reason="사업자번호 일치")`는 이렇게 기록됩니다. (읽기 쉬운 Turtle)

```turtle
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix ex:   <https://example.org/kg/> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

# --- Agent: 누가 했나 ---
ex:merge-pipeline-v2.1 a prov:SoftwareAgent ;
    prov:actedOnBehalfOf ex:data-platform-team .

# --- Entity: 입력 레코드들 ---
ex:r01 a prov:Entity ; ex:name "가온테크"  ; ex:bizno "123-45-67890" .
ex:r04 a prov:Entity ; ex:name "GAON TECH" ; ex:bizno "123-45-67890" .

# --- Activity: 병합 실행 ---
ex:merge-20260801-0042 a prov:Activity ;
    prov:used            ex:r01, ex:r04 ;            # 무엇을 보고
    prov:wasAssociatedWith ex:merge-pipeline-v2.1 ;   # 누가 돌렸고
    prov:startedAtTime  "2026-08-01T00:42:11Z"^^xsd:dateTime ;
    prov:endedAtTime    "2026-08-01T00:42:11Z"^^xsd:dateTime ;
    ex:matchScore       1.000 ;                       # 점수는
    ex:highThreshold    0.85 ;                        # 임계는
    ex:lowThreshold     0.55 ;
    ex:reason           "사업자번호 일치" .            # reason 필드가 여기로

# --- Entity: 병합 결과인 대표 노드 ---
ex:canonical-gaon a prov:Entity ;
    prov:wasGeneratedBy  ex:merge-20260801-0042 ;      # 이 병합이 낳았다
    prov:wasDerivedFrom  ex:r01, ex:r04 ;              # 이것들에서 나왔다
    prov:wasAttributedTo ex:merge-pipeline-v2.1 .      # 자동 병합의 산물이다

# 원본은 지우지 않는다. 대표를 가리키게만 한다 (14장 3절)
ex:r04 prov:alternateOf ex:canonical-gaon ;
       owl:sameAs       ex:canonical-gaon .
```

`MergeStore`의 자체 이벤트 딕셔너리와 대응시키면 이렇습니다.

| `events` 항목 | PROV-O 대응 |
|---|---|
| `"op": "merge"` | `prov:Activity` 인스턴스 하나 (타입으로 구분) |
| `"keep"` | 결과 Entity + `prov:wasGeneratedBy` |
| `"drop"` | `prov:used`, `prov:wasDerivedFrom`의 대상 |
| `"by": "auto"` | `prov:wasAssociatedWith` / `prov:wasAttributedTo` → `prov:SoftwareAgent` |
| `"reason": "사업자번호 일치"` | Activity에 붙는 속성 (점수·임계·규칙 버전까지 확장) |
| (없음) | `prov:startedAtTime` / `prov:endedAtTime` — 자체 포맷에는 시각조차 없었다 |

**사람 판정도 같은 형식으로 들어갑니다.** `ex2`의 `HUMAN = {("r01","r04"): True, ("r06","r07"): False}` 판정은 Agent만 바꾼 똑같은 구조입니다.

```turtle
ex:reviewer-park a prov:Person .

ex:review-r06-r07 a prov:Activity ;
    prov:used              ex:r06, ex:r07 ;
    prov:wasAssociatedWith ex:reviewer-park ;
    ex:score               0.550 ;
    ex:decision            "다르다" ;
    ex:reason              "사업자번호 상이 — 모회사/자회사" .

ex:no-merge-r06-r07 a prov:Entity ;
    prov:wasGeneratedBy  ex:review-r06-r07 ;
    prov:wasAttributedTo ex:reviewer-park .
```

이게 되면 「자동이 정한 것」과 「사람이 정한 것」을 **한 질의로 구분**할 수 있습니다. 14장이 임계 두 개를 두고 애매 구간을 사람에게 보내는 이유가, 이력에서도 그대로 드러나야 값을 합니다. 재병합 파이프라인이 「사람이 다르다고 판정한 쌍은 다시 건드리지 않는다」를 지키려면 이 구분이 데이터로 있어야 하니까요.

**`unmerge`도 Activity입니다.** 14장의 사흘짜리 되돌리기는 PROV-O에서 「기록을 지우는 일」이 아니라 「기록을 하나 더 쌓는 일」입니다.

```turtle
ex:unmerge-20260804-0117 a prov:Activity ;
    prov:used              ex:canonical-naru ;
    prov:wasAssociatedWith ex:reviewer-park ;
    prov:wasInformedBy     ex:merge-20260801-0043 ;   # 저 병합 때문에 벌어진 일
    ex:reason              "오병합 — 사업자번호 상이" .
```

`prov:wasInformedBy`(Activity → Activity)가 「어떤 처리가 어떤 처리에 이어서 일어났나」를 잇습니다. 병합 → 오류 발견 → unmerge → 재병합의 사슬이 그래프에 남습니다. 14장 `ex3`의 `{"op": "unmerge", "undoes": i}`가 하던 일과 같은데, 인덱스 번호가 아니라 표준 속성으로 이어지죠.

### 4.2 값 출처 — `ex5` 생존 규칙을 PROV-O로

여기가 이 카드의 핵심 응용입니다. 14장 `ex5`는 필드마다 다른 규칙으로 값을 고릅니다.

| 필드 | 규칙 | 고른 값 | 근거 |
|---|---|---|---|
| name | 가장 신뢰도 높은 출처 | 가온테크 | r01(ERP, 2024-03-01) |
| ceo | 가장 최근 | 박서준 | r02(CRM, 2026-01-15) |
| tel | 가장 최근 중 비어 있지 않은 것 | 02-1234-5679 | r04(명함스캔, 2025-07-09) |
| addr | 가장 긴 값 | 서울 강남구 테헤란로 1길 22 | r02(CRM) |

「이 대표자 이름 왜 이래요」에 답하려면 **필드 값 하나하나가 Entity**여야 합니다. 노드 전체가 아니라 값 단위로 출처를 붙이는 것이죠.

```turtle
# 각 원본 시스템도 Agent다
ex:erp  a prov:SoftwareAgent, prov:Organization .
ex:crm  a prov:SoftwareAgent .
ex:card-scan a prov:SoftwareAgent .

# r02의 대표자 값 — 원본 값도 Entity로
ex:r02-ceo a prov:Entity ;
    ex:value             "박서준" ;
    prov:wasAttributedTo ex:crm ;
    prov:generatedAtTime "2026-01-15"^^xsd:date .

# 생존 규칙 적용이라는 Activity
ex:survivorship-ceo a prov:Activity ;
    prov:used              ex:r01-ceo, ex:r02-ceo ;   # 후보들
    prov:wasAssociatedWith ex:merge-pipeline-v2.1 ;
    ex:rule                "가장 최근" ;               # RULES["ceo"]
    ex:ruleVersion         "survivorship-rules@3" .

# 최종 대표자 값
ex:canonical-gaon-ceo a prov:Entity ;
    ex:value             "박서준" ;
    prov:wasGeneratedBy  ex:survivorship-ceo ;
    prov:wasDerivedFrom  ex:r02-ceo ;                 # ★ 이 값은 여기서 왔다
    prov:hadPrimarySource ex:crm ;                    # 1차 출처는 CRM
    prov:wasAttributedTo ex:merge-pipeline-v2.1 .
```

이제 「대표자가 왜 박서준이에요?」에 대한 답이 그래프 질의 하나입니다.

```sparql
SELECT ?src ?rule ?srcAgent ?when WHERE {
  ex:canonical-gaon-ceo prov:wasDerivedFrom ?src ;
                        prov:wasGeneratedBy  ?act .
  ?act  ex:rule ?rule .
  ?src  prov:wasAttributedTo ?srcAgent ;
        prov:generatedAtTime ?when .
}
# → src=r02-ceo, rule="가장 최근", srcAgent=CRM, when=2026-01-15
```

14장이 「ERP가 더 믿을 만한 출처라면 김하늘이 맞을 수도 있다」고 한 그 논쟁도, PROV-O 기록이 있으면 **논쟁이 아니라 확인**이 됩니다. 규칙과 후보와 선택이 다 남아 있으니 규칙만 바꿔 다시 돌리면 되고, 바꾼 뒤에도 이전 결정을 `prov:wasRevisionOf`로 이어 둘 수 있습니다.

```turtle
ex:canonical-gaon-ceo-v2 a prov:Entity ;
    ex:value            "김하늘" ;
    prov:wasRevisionOf  ex:canonical-gaon-ceo ;       # 개정 관계
    prov:wasDerivedFrom ex:r01-ceo ;
    ex:rule             "가장 신뢰도 높은 출처" .
```

### 4.3 「왜 값 하나마다 Entity인가」 — `prov:specializationOf`

값 단위 출처를 붙이려다 보면 「가온테크라는 회사」와 「2026-08-01 시점의 가온테크 레코드」가 뒤섞입니다. PROV-O는 이걸 위한 어휘가 따로 있습니다.

- `prov:specializationOf` — 「이 구체적 판(版)은 저 일반적 것의 특수화다」
- `prov:alternateOf` — 「이 둘은 같은 것을 가리키는 다른 표현이다」 (대칭)

14장이 「같은 사람이 노드 네 개로 앉아 있다」고 한 상황이 정확히 `prov:alternateOf`입니다. r01/r02/r03/r04는 하나의 실체를 가리키는 네 개의 표현입니다. 여기서 표준 어휘의 층위를 구분해 쓰는 게 중요합니다.

| 상황 | 쓸 어휘 | 14장 근거 |
|---|---|---|
| 완전히 같은 개체라고 단정 | `owl:sameAs` | 「동일성 선언」 [표준] |
| 같은 것의 다른 표현/판 | `prov:alternateOf`, `prov:specializationOf` | 되돌릴 수 있게 남긴다 |
| 비슷한데 단정 못 함 (애매 구간) | `skos:closeMatch` | 「느슨한 동일성」 [표준] |
| 그 판단의 이력·근거 | `prov:Activity` + 4개 속성 | 「출처 추적」 [표준] |

`owl:sameAs`는 위험합니다. 추론기가 두 노드의 모든 속성을 합쳐 버리기 때문에, 14장 3절이 강조한 「원본을 지우지 않는다」는 원칙이 논리 층위에서 깨질 수 있습니다. r06/r07처럼 나중에 「다르다」고 밝혀질 수 있는 쌍이라면 `skos:closeMatch` + PROV 이력으로 두고, 확정된 뒤에 `owl:sameAs`로 올리는 게 안전합니다. 어느 쪽이든 **판단 그 자체의 이력은 PROV-O로 남는다**는 점은 같습니다.

### 4.4 한정 패턴 (Qualified Terms)

`prov:wasDerivedFrom`은 단순 엣지라서 「어떻게 파생됐나」를 엣지에 붙일 수 없습니다. 그럴 때 관계를 노드로 승격시키는 게 한정 패턴입니다.

```turtle
ex:canonical-gaon-ceo prov:qualifiedDerivation [
    a prov:Derivation ;
    prov:entity   ex:r02-ceo ;
    prov:hadRole  ex:winning-candidate ;   # 이긴 후보
    prov:hadActivity ex:survivorship-ceo
] , [
    a prov:Derivation ;
    prov:entity   ex:r01-ceo ;
    prov:hadRole  ex:rejected-candidate ;  # 진 후보
    prov:hadActivity ex:survivorship-ceo
] .
```

「이긴 값」과 「진 값」을 구분해 둘 수 있습니다. RDF에서 엣지에 속성을 못 붙이는 한계를 표준이 정해 준 방식으로 우회하는 것이고, 프로퍼티 그래프의 엣지 속성에 해당합니다. 다만 트리플 수가 급격히 늘기 때문에 실무에서는 정말 필요한 필드에만 씁니다.

---

## 5. 표준을 쓰는 값과 비용

**값**

1. **어휘를 새로 발명하지 않는다.** `by`/`reason` 같은 자체 필드는 6개월 뒤 옆 팀이 못 읽습니다. `prov:wasAttributedTo`는 처음 보는 사람도 명세를 찾을 수 있습니다.
2. **시스템 간 교환이 된다.** PROV-O의 존재 이유가 「서로 다른 시스템, 서로 다른 맥락에서 생성된 출처 정보를 표현하고 교환하는 것」입니다. ERP·CRM·명함스캔이 각자 다른 포맷으로 이력을 남기면 합칠 수 없습니다.
3. **도구가 이미 있다.** 시각화, 검증(PROV-CONSTRAINTS), 워크플로 기록(RO-Crate 등)이 PROV를 전제로 만들어져 있습니다.
4. **감사·규제 대응.** 「이 값 왜 이래요」가 문의 수준이면 로그로 되지만, 감사 요구가 되면 표준 형식이 필요합니다.

**비용**

1. **트리플이 폭발합니다.** 값 하나에 Entity·Activity·Agent와 엣지 몇 개가 붙습니다. 14장이 「노드 수가 1.4배가 됐다」고 한 것은 되돌릴 수 있는 병합만의 비용이고, 값 단위 PROV까지 붙이면 데이터보다 이력이 커집니다.
2. **어디까지 남길지 정해야 합니다.** 모든 필드에 다 붙이지 말고, 분쟁이 생기는 필드(대표자, 주소처럼 사람이 문의하는 값)에만 값 단위로 붙이고 나머지는 노드 단위로 두는 절충이 흔합니다.
3. **Starting Point Terms만으로 시작하세요.** 처음부터 한정 패턴까지 쓰려 들면 아무도 안 씁니다.

---

## 6. 한 줄로 외울 것

> **14장의 출처 추적 표준은 W3C PROV-O(2013-04-30 권고안, `prov:` = `http://www.w3.org/ns/prov#`), [표준] 등급.**
> **Entity(것) / Activity(일) / Agent(책임자)** 세 클래스와,
> **`wasGeneratedBy`(이 값은 저 처리가 만들었다) / `used`(저 처리는 이 입력을 썼다) / `wasDerivedFrom`(이 값은 저 값에서 왔다) / `wasAttributedTo`(이 값의 책임은 저 주체에게 있다)** 네 속성으로,
> `MergeStore`의 `{by, reason}` 자체 포맷과 `ex5`의 「고른 값마다 어디서 왔는지」를 표준 어휘로 옮긴다.

---

## 참고 출처

- [PROV-O: The PROV Ontology (W3C Recommendation 2013-04-30)](https://www.w3.org/TR/prov-o/)
- [PROV-Overview](https://www.w3.org/TR/prov-overview/)
- [PROV Model Primer](https://www.w3.org/TR/prov-primer/)
- [PROV-O OWL 파일](https://www.w3.org/ns/prov-o.owl)
- [owl:sameAs — OWL2 Syntax](https://www.w3.org/TR/owl2-syntax/#Individual_Equality)
- [skos:closeMatch — SKOS Reference](https://www.w3.org/TR/skos-reference/#mapping)
