# 같은 "담당자는 최소 하나" 규칙을 OWL로 쓰면?

## 질문과 답

**질문** — 같은 "담당자는 최소 하나" 규칙을 OWL로 쓰면 어떤 결과가 나오는가?

**답** — `owl:minCardinality 1` 제약으로 선언하면 추론기가 오류를 내지 않고 "어딘가 있겠지"로 넘어가며, 빈 노드로 담당자를 만들어 내기도 한다.

---

## 한 줄로 먼저

OWL의 `owl:minCardinality 1`은 **"이걸 어겼는지 검사해라"가 아니라 "이 세상에는 담당자가 최소 하나 존재한다"는 사실 선언**이다. 그래서 담당자가 안 적혀 있는 데이터를 넣어도 추론기는 "위반"이 아니라 "아직 안 적었을 뿐, 어딘가 있다"고 읽는다. 13장 저자가 3주를 날린 지점이 정확히 여기다.

> 추론기는 고장 나지 않았다. 제가 잘못된 도구를 골랐을 뿐이다.
> — `ex2_infer_vs_validate.py` 마지막 줄

---

## 1. 예제 코드 (`code/ex2_infer_vs_validate.py`)

같은 문장 "회사는 담당자가 최소 하나 있어야 한다"를 두 언어로 적는다.

### OWL 방식 — «최소 하나»를 클래스 제약으로 **선언**

```turtle
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex:   <http://example.org/> .
ex:Company a owl:Class ;
    rdfs:subClassOf [ a owl:Restriction ;
        owl:onProperty ex:managedBy ;
        owl:minCardinality 1 ] .
ex:managedBy a owl:ObjectProperty .
```

### SHACL 방식 — 같은 뜻을 «형태»로 선언

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/> .
ex:CompanyShape a sh:NodeShape ;
    sh:targetClass ex:Company ;
    sh:property [ sh:path ex:managedBy ; sh:minCount 1 ;
                  sh:message "담당자가 없다" ] .
```

### 데이터 — 나루소프트에는 담당자가 없다

```turtle
@prefix ex: <http://example.org/> .
ex:Gaon a ex:Company ; ex:managedBy ex:Kim .
ex:Naru a ex:Company .
```

### 실행부

```python
def run_owl():
    g = Graph().parse(data=OWL_SCHEMA + DATA, format="turtle")
    before = len(g)
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
    after = len(g)
    # 나루소프트에게 담당자가 «생겼는지» 확인
    has = list(g.objects(EX.Naru, EX.managedBy))
    return before, after, has
```

```python
print(f"  트리플 {before} → {after} (추론으로 {after-before}개 늘었다)")
print(f"  나루소프트의 담당자: {has if has else '없음(빈 노드로 생기기도 한다)'}")
print("  → 오류를 내지 않는다. «어딘가 있겠지»로 넘어간다.")
```

### 실제 실행 결과 (pyshacl / owlrl / rdflib 7.x, 2026-08 확인)

```
OWL: 트리플 9 → 141 (추론으로 132개 늘었다)
     나루소프트의 담당자: 없음
     → 오류를 내지 않는다.

SHACL conforms: False
Constraint Violation in MinCountConstraintComponent
	Severity: sh:Violation
	Focus Node: ex:Naru
	Result Path: ex:managedBy
	Message: 담당자가 없다
```

핵심은 **왼쪽에 "위반" 한 줄이 없다**는 것이다. 트리플은 132개나 늘었는데 그중 "나루소프트에 문제가 있다"는 정보는 단 하나도 없다. 품질 검사를 이걸로 짜면, 파이프라인은 영원히 초록불이다.

---

## 2. 왜 "제약"이 아니라 "선언"이 되는가 — 열린 세계 가정(OWA)

### OWA: 적혀 있지 않은 것은 «거짓»이 아니라 «모른다»

OWL은 **열린 세계 가정(Open World Assumption)** 위에서 동작한다.

| | 닫힌 세계(CWA) | 열린 세계(OWA) |
|---|---|---|
| 그래프에 `ex:Naru ex:managedBy ?x`가 없다 | "담당자가 **없다**" (거짓) | "담당자가 있는지 **모른다**" |
| 쓰는 곳 | SQL, SHACL, 프로그래밍 언어 | OWL, 서술 논리 |

그래서 OWL 추론기가 보는 상황은 이렇다.

1. 공리: 모든 `ex:Company`는 `ex:managedBy`를 최소 1개 가진다.
2. 사실: `ex:Naru a ex:Company`.
3. 결론: **따라서 `ex:Naru`에게는 담당자가 있다.** 누구인지는 모르지만 존재한다.

3번이 "결론"이라는 게 전부다. 추론기 입장에서 데이터는 아무것도 어기지 않았다. 오히려 새 사실 하나를 알려줬다. 모순(inconsistency)이 아니므로 오류도 아니다.

### 논리적으로 무엇을 적은 것인가

`owl:minCardinality 1`은 서술 논리로 `≥1 managedBy.⊤`, 즉 `owl:someValuesFrom owl:Thing`과 같다. 이건 **존재 한정(existential)** 이다. "존재한다"는 주장이지 "존재하는지 확인해라"가 아니다.

검사로 동작하려면 «없음»이 «거짓»이어야 하는데, OWA에서는 «없음»이 «미지»다. 미지에서는 모순이 안 나오고, 모순이 없으면 추론기는 할 말이 없다.

### OWL로 모순을 내려면 무엇이 필요한가

참고로, OWL에서 오류(비일관성)를 내는 건 반대쪽이다. **`owl:maxCardinality`** 같은 상한이 걸렸을 때다.

```turtle
# 담당자는 «최대 1명»
[ a owl:Restriction ; owl:onProperty ex:managedBy ; owl:maxCardinality 1 ]
```

여기에 `ex:Naru ex:managedBy ex:Kim, ex:Lee`가 들어오면 — **여기서도 바로 오류가 나지 않는다.** 이번엔 두 번째 가정이 발목을 잡는다.

---

## 3. 이름 유일성 가정 없음(non-UNA) — 상한 제약마저 무디게 만드는 것

**UNA(Unique Name Assumption)** 는 "서로 다른 식별자는 서로 다른 것을 가리킨다"는 가정이다. 관계형 DB는 이걸 당연히 깔고 간다. OWL은 **깔지 않는다(non-UNA)**.

그래서 `ex:Kim`과 `ex:Lee`가 나온 위 상황에서 추론기는 이렇게 결론 낸다.

> 담당자는 최대 1명인데 둘이 적혀 있다. 그렇다면 **`ex:Kim owl:sameAs ex:Lee`** 겠구나.

오류가 아니라 **동일성 추론**이 나온다. 데이터를 고치라는 신호 대신, 서로 다른 두 사람을 하나로 합쳐 버리는 새 트리플이 생긴다. 이게 실무에서 훨씬 무섭다. 조용히 그래프가 오염되기 때문이다.

명시적으로 `ex:Kim owl:differentFrom ex:Lee`나 `owl:AllDifferent`를 적어 뒀을 때에야 비로소 비일관성이 뜬다. 즉 OWL에서 "위반"을 보려면 **모순을 만들 재료를 사람이 미리 다 넣어 둬야** 한다. 검증기라면 안 해도 될 일이다.

정리하면,

- **OWA** 때문에 `minCardinality`(하한)는 검사가 되지 않는다 → 없으면 «있다고 결론».
- **non-UNA** 때문에 `maxCardinality`(상한)도 검사가 되지 않는다 → 넘치면 «같은 것이라고 결론».

양쪽 다 "위반 보고" 대신 "새 결론"이 나온다. OWL은 **추론 언어**이지 검증 언어가 아니라는 말이 이 뜻이다.

---

## 4. 빈 노드(익명 개체)를 상정하는 메커니즘

답에 나오는 "빈 노드로 담당자를 만들어 내기도 한다"가 무슨 뜻인지 정확히 짚어 둔다. 도구에 따라 결과가 다르기 때문이다.

### (a) 타블로 기반 DL 추론기 (HermiT, Pellet, JFact 등)

`≥1 managedBy.⊤`를 만족시키려고 **익명 개체(anonymous individual)를 내부에서 만들어 낸다.** 이게 타블로 알고리즘의 존재 규칙(∃-rule)이다.

1. `Naru : Company`
2. `Company ⊑ ≥1 managedBy.⊤`이므로 `Naru : ≥1 managedBy.⊤`
3. 이를 만족시키려고 새 익명 노드 `_:x`를 만들고 `managedBy(Naru, _:x)`를 놓는다
4. 모순 없음 → **일관됨(consistent)** 이라고 보고하고 끝

여기서 만들어진 `_:x`는 "모델이 존재한다"는 증명을 위한 임시 목격자(witness)다. 보통 결과 그래프로 물질화되지 않고 사라진다. 그래도 결론은 같다 — **에러가 안 난다.** 잘못된 데이터가 "완벽하게 일관된 데이터"로 통과한다.

### (b) 스콜렘화하는 물질화 엔진 (존재 규칙/TGD를 지원하는 시스템)

RDFox의 존재 규칙, `owl:someValuesFrom` 물질화 옵션을 켠 일부 엔진, chase 알고리즘 계열은 그 목격자를 **실제 블랭크 노드 트리플로 그래프에 써 넣는다.**

```turtle
ex:Naru ex:managedBy _:b0 .   # 추론기가 만들어 낸 «담당자»
```

이게 답에서 말하는 "빈 노드로 담당자를 만들어 내기도 한다"의 문자 그대로의 경우다. 결과가 최악인데,

- 담당자 없는 회사를 찾는 질의 `?c ex:managedBy ?p`가 **나루소프트까지 잡아 온다**
- 화면에 `_:b0` 또는 빈칸이 뜬다
- 담당자 수를 세면 숫자가 부풀려진다
- 원천에는 없는 데이터인데 그래프에는 있다 — 어디서 왔는지 추적하기도 어렵다

### (c) owlrl (예제가 쓰는 것, OWL 2 RL)

OWL 2 RL 프로파일은 **규칙 기반**이고, 존재 한정을 결론 쪽(superclass position)에서 지원하지 않는다. 새 개체를 만들어 내는 규칙이 아예 없다. 그래서 실제 실행 결과가

```
트리플 9 → 141 (추론으로 132개 늘었다)
나루소프트의 담당자: 없음
```

으로 나온다. 늘어난 132개는 `rdfs:subClassOf` 반사성, 클래스/프로퍼티 타입 공리 등 OWL RL의 공리적 폐포지 "담당자"가 아니다. 예제 코드가

```python
print(f"  나루소프트의 담당자: {has if has else '없음(빈 노드로 생기기도 한다)'}")
```

처럼 두 경우를 한 줄에 담아 둔 이유다. **핵심은 (a)(b)(c) 어느 쪽이든 "담당자가 없다"는 보고가 나오지 않는다는 것**이다. 있다고 결론 내거나, 만들어 내거나, 조용히 아무 말도 안 하거나 — 셋 다 품질 검사로는 실패다.

---

## 5. 같은 규칙, SHACL 쪽 — `sh:minCount 1`

SHACL은 정반대 가정 위에 서 있다.

- **닫힌 세계에 가깝게 동작한다.** 데이터 그래프에 없으면 없는 것이다.
- **UNA를 사실상 채택한다.** 서로 다른 IRI는 서로 다른 노드다.
- 추론이 아니라 **대상 선택 → 제약 평가 → 보고서 생성**이 전부다. 새 트리플을 데이터 그래프에 만들지 않는다.

### 동작 순서

1. `sh:targetClass ex:Company` → 대상(focus node) 수집: `ex:Gaon`, `ex:Naru`
2. 각 focus node에 대해 `sh:path ex:managedBy`로 값 집합(value nodes)을 뽑는다
   - `ex:Gaon` → `{ex:Kim}`, 크기 1
   - `ex:Naru` → `{}`, 크기 0
3. `sh:minCount 1` 평가 → `ex:Naru`가 0 < 1 이므로 **위반**
4. 검증 보고서(Validation Report)에 결과 노드를 적는다

### 실제 보고서

```
Conforms: False
Results (1):
Constraint Violation in MinCountConstraintComponent
        (http://www.w3.org/ns/shacl#MinCountConstraintComponent):
	Severity: sh:Violation
	Source Shape: [ sh:message "담당자가 없다" ; sh:minCount 1 ; sh:path ex:managedBy ]
	Focus Node: ex:Naru
	Result Path: ex:managedBy
	Message: 담당자가 없다
```

보고서에서 실무적으로 중요한 필드는 이렇다.

| 필드 | 값 | 왜 중요한가 |
|---|---|---|
| `sh:conforms` | `false` | 파이프라인의 분기 조건 |
| `sh:focusNode` | `ex:Naru` | **어느 노드가 문제인지** — 사람에게 넘길 주소 |
| `sh:resultPath` | `ex:managedBy` | 어느 속성인지 |
| `sh:resultMessage` | `"담당자가 없다"` | `sh:message`로 사람이 직접 쓴 문장 |
| `sh:sourceConstraintComponent` | `sh:MinCountConstraintComponent` | 어떤 종류의 위반인지 (집계·분류용) |
| `sh:resultSeverity` | `sh:Violation` | 기본값. `sh:severity`로 `sh:Warning`/`sh:Info`로 낮출 수 있다 |

예제 코드가 보고서 텍스트에서 `Focus Node`와 `Message` 줄만 뽑아 오는 것도 이 두 개가 사람이 실제로 쓰는 정보이기 때문이다.

```python
ok, _, text = validate(data, shacl_graph=shapes, inference="none")
hits = [l.strip() for l in text.splitlines()
        if l.strip().startswith(("Focus Node", "Message"))]
```

`inference="none"`이 붙어 있는 것도 의도적이다. pyshacl은 검증 전에 RDFS/OWL 추론을 돌리는 옵션이 있는데, 그걸 켜면 이 예제가 대조하려는 두 세계가 섞여 버린다.

---

## 6. 나란히 놓고 보기

| | OWL `owl:minCardinality 1` | SHACL `sh:minCount 1` |
|---|---|---|
| 무엇을 말하는가 | "세상에 무엇이 있는가" | "우리 데이터가 어떤 모양이어야 하는가" |
| 세계 가정 | 열린 세계(OWA) | 닫힌 세계에 가까움 |
| 이름 가정 | non-UNA (다른 IRI가 같을 수 있다) | UNA (다른 IRI는 다르다) |
| 값이 없을 때 | **"있는데 안 적혔겠지"** — 통과 | **위반** |
| 값이 넘칠 때(상한) | `owl:sameAs`를 추론 | `sh:maxCount` 위반 |
| 출력 | 늘어난 트리플(추론 폐포) | 검증 보고서 (`conforms`, focus node, message) |
| 그래프를 바꾸는가 | 바꾼다 (물질화 시 빈 노드까지) | 바꾸지 않는다 |
| 실패 신호 | 없음 (모순일 때만 inconsistent) | `conforms = False` |
| 심각도 조절 | 없음 | `sh:severity` (Violation/Warning/Info) |
| 적합한 용도 | 분류, 계층 추론, 지식 확장 | **데이터 품질 게이트** |

---

## 7. 실무에서 이게 왜 3주짜리 사고가 되는가

품질 검사를 OWL로 짜면 이런 순서로 흘러간다.

1. 온톨로지에 `minCardinality`, `someValuesFrom`, `functionalProperty`를 열심히 적는다. 규칙은 다 표현됐다.
2. 추론기를 돌린다. **에러가 하나도 안 난다.** 데이터가 깨끗한 줄 안다.
3. 실제로는 담당자 없는 회사가 수천 개다. 추론기는 "어딘가 있겠지"로 다 통과시켰다.
4. 물질화까지 켰다면 그래프에는 `_:b0` 담당자와 잘못 병합된 `owl:sameAs`가 쌓인다.
5. 몇 주 뒤 대시보드가 이상하다는 제보로 발견된다. 이미 그래프는 오염돼 있다.

13장이 요약에서 못 박는 한 줄이 이거다.

> 추론기와 검증기는 다른 물건입니다. OWL은 없으면 있다고 결론 내고, SHACL은 없으면 위반이라고 적습니다. 품질 검사에 추론기를 쓰면 3주를 날립니다.

**규칙**: "이 데이터가 규칙을 지켰는가?"를 묻고 싶으면 SHACL이다. "이 데이터로부터 무엇을 더 알 수 있는가?"를 묻고 싶을 때만 OWL이다. 문장이 똑같아 보여도 도구가 하는 일이 다르다.

---

## 관련 카드로 이어지는 지점

- `ex1_shacl_severity.py` — SHACL은 여기서 한 발 더 나간다. `sh:severity`로 차단/경고/기록을 나눌 수 있다. OWL에는 대응물이 없다.
- `ex1`의 함정 — `conforms=False`는 **기록(Info) 등급 하나만 걸려도** False다. 이 불리언만 보고 적재를 막으면 "표시 이름이 없다" 때문에 파이프라인이 선다. 반드시 심각도별로 갈라서 처리해야 한다.
- `ex3_graph_smells.py` — SHACL로도 못 잡는 것들(슈퍼 노드, 사이클, 중복 의심)은 또 다른 층이 필요하다.

## 1차 출처

- [Shapes Constraint Language (SHACL)](https://www.w3.org/TR/shacl/) — `sh:minCount`는 [MinCountConstraintComponent](https://www.w3.org/TR/shacl/#MinCountConstraintComponent), 보고서 구조는 [Validation Report](https://www.w3.org/TR/shacl/#validation-report)
- [sh:severity](https://www.w3.org/TR/shacl/#severity)
- [OWL 2 Web Ontology Language Primer](https://www.w3.org/TR/owl2-primer/) — 열린 세계 가정과 UNA 없음에 대한 설명
- [OWL 2 Profiles](https://www.w3.org/TR/owl2-profiles/) — OWL 2 RL이 존재 한정을 결론 위치에서 지원하지 않는 이유
