# `ex3_when_schema.py`의 SHACL 형태는 어떤 제약을 선언하는가?

## 한 줄 답

`ex:name`에 **minCount 1, minLength 1, datatype xsd:string**을, `ex:grade`에 **`sh:in ("A" "B" "C")`** 를 선언한다.

---

## 1. 문제의 코드 (asset 원문 그대로)

`ex3_when_schema.py`의 `SHAPES` 상수입니다.

```turtle
@prefix sh:  <http://www.w3.org/ns/shacl#> .
@prefix ex:  <http://example.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:CompanyShape a sh:NodeShape ;
    sh:targetClass ex:Company ;
    sh:property [ sh:path ex:name ; sh:minCount 1 ; sh:minLength 1 ;
                  sh:datatype xsd:string ] ;
    sh:property [ sh:path ex:grade ; sh:in ("A" "B" "C") ] .
```

그리고 이 형태로 검사할 데이터입니다.

```turtle
@prefix ex: <http://example.org/> .
ex:Gaon a ex:Company ; ex:name "가온테크" ; ex:grade "Z" .
ex:Naru a ex:Company ; ex:name ""        ; ex:grade "A" .
ex:Daol a ex:Company ; ex:name "다올물산" ; ex:grade "B" .
```

이 장(12.3 "스키마를 언제 못 박을 것인가")의 논지는 **"같은 잘못된 데이터를 세 방식에 넣고 언제 걸리는지 본다"** 입니다.
방식 1은 Kuzu의 적재 시점 타입 강제, 방식 2가 바로 이 SHACL, 방식 3은 스키마 없음입니다.
SHACL은 **적재는 다 되고 나중에 보고서로 잡는** 쪽이라는 게 핵심 대비입니다.

---

## 2. 한 줄씩 해설

### `@prefix sh: <http://www.w3.org/ns/shacl#> .`

SHACL 어휘의 네임스페이스입니다. W3C 권고( [SHACL](https://www.w3.org/TR/shacl/) )가 정의하는 모든 용어(`sh:NodeShape`, `sh:path`, `sh:minCount` ...)가 이 네임스페이스 아래에 있습니다.
`ex:`는 예제용 우리 어휘, `xsd:`는 XML Schema 데이터타입 네임스페이스입니다.

### `ex:CompanyShape a sh:NodeShape ;`

`ex:CompanyShape`라는 이름의 **노드 형태(node shape)** 를 하나 선언합니다.

- **노드 형태**: 검사 대상 노드 *그 자체* 에 대한 제약을 담는 그릇. "이 노드는 어떠해야 하는가."
- **속성 형태(property shape)**: 어떤 노드에서 특정 경로(`sh:path`)를 따라 나온 값들에 대한 제약. "이 노드의 `ex:name` 값들은 어떠해야 하는가."

노드 형태는 `sh:property`로 속성 형태들을 매달아서 조합합니다. 여기 `ex:CompanyShape`는 속성 형태 두 개를 갖습니다.

> 참고: `a sh:NodeShape`를 명시적으로 쓰지 않아도, `sh:targetClass`나 `sh:property`가 붙어 있으면 SHACL 처리기가 형태로 인식합니다. 다만 사람이 읽기 좋으라고 명시하는 게 관례입니다.

### `sh:targetClass ex:Company ;`

**대상 선언(target)** 입니다. "이 형태를 데이터 그래프의 *어느* 노드들에 적용할 것인가"를 정합니다.

`sh:targetClass ex:Company`는 **`rdf:type`이 `ex:Company`인 모든 노드**를 초점 노드(focus node)로 삼는다는 뜻입니다.
위 데이터에서는 `ex:Gaon`, `ex:Naru`, `ex:Daol` 세 개가 초점 노드가 됩니다.

대상 선언의 다른 종류들:

| 선언 | 의미 |
|---|---|
| `sh:targetClass` | 해당 클래스의 인스턴스 전부 |
| `sh:targetNode` | 딱 지정한 노드만 |
| `sh:targetSubjectsOf` | 어떤 술어의 주어로 등장한 노드들 |
| `sh:targetObjectsOf` | 어떤 술어의 목적어로 등장한 노드들 |

> 주의: `sh:targetClass`는 원칙적으로 `rdfs:subClassOf*`를 따라 하위 클래스 인스턴스까지 포함합니다. 그런데 예제는 `validate(..., inference="none")`으로 추론을 끄고 돌립니다. 그래서 **명시적으로 `a ex:Company`라고 적힌 노드만** 잡힙니다. 12장이 계속 말하는 "언제 아느냐"와 같은 결의 이야기로, 추론을 켜면 잡히는 범위가 달라진다는 걸 기억해 두세요.

### `sh:property [ sh:path ex:name ; sh:minCount 1 ; sh:minLength 1 ; sh:datatype xsd:string ] ;`

대괄호 `[ ... ]`는 Turtle의 **빈 노드(blank node)** 문법입니다. 이름 없는 속성 형태를 그 자리에서 만들어 붙인 것이죠.
따로 이름을 줘서 재사용하고 싶으면 `ex:NameShape a sh:PropertyShape ; ...`처럼 떼어내도 결과는 같습니다.

이 속성 형태 안의 제약 네 조각:

| 항목 | 역할 |
|---|---|
| `sh:path ex:name` | **경로**. 초점 노드에서 `ex:name` 술어를 따라 나온 값들이 이 형태의 검사 대상(값 노드, value node)이 된다. 속성 형태에는 `sh:path`가 **필수**다. |
| `sh:minCount 1` | 그 값이 **최소 1개는 있어야 한다**. 즉 `ex:name`이 아예 없으면 위반. 필수 속성을 만드는 방법. |
| `sh:minLength 1` | 각 값의 **문자열 길이가 1 이상**이어야 한다. 즉 빈 문자열 `""` 금지. |
| `sh:datatype xsd:string` | 각 값이 **`xsd:string` 리터럴**이어야 한다. 숫자, 날짜, IRI, 빈 노드면 위반. |

이 셋의 역할 분담이 중요합니다.

- `sh:minCount`는 **개수**(있냐 없냐)를 봅니다.
- `sh:minLength`는 **길이**(비었냐)를 봅니다.
- `sh:datatype`는 **타입**(무슨 종류의 값이냐)을 봅니다.

셋 다 있어야 "이름은 반드시 있고, 비어 있지 않은, 문자열"이라는 뜻이 완성됩니다. 하나라도 빼면 구멍이 납니다.
특히 `minCount`만 걸면 `ex:name ""`이 통과해 버립니다 — 값이 "있긴" 하니까요. 예제 데이터의 `ex:Naru`가 정확히 그 함정입니다.

> 세부: Turtle에서 따옴표만 친 리터럴 `"가온테크"`는 데이터타입이 생략된 것이고, RDF 1.1에서는 이것이 곧 `xsd:string`입니다. 그래서 `sh:datatype xsd:string`을 통과합니다. 만약 `"가온테크"@ko`처럼 언어 태그를 달면 데이터타입이 `rdf:langString`이 되어 **위반**합니다. 다국어 이름을 다룰 거라면 `sh:datatype` 대신 `sh:nodeKind sh:Literal`이나 `sh:languageIn`을 쓰는 게 맞습니다.
>
> 세부 2: `sh:minLength`는 리터럴이면 그 어휘 표현(lexical form)의 길이, IRI면 IRI 문자열의 길이를 봅니다. 빈 노드에는 적용할 수 없어 항상 위반입니다.

### `sh:property [ sh:path ex:grade ; sh:in ("A" "B" "C") ] .`

두 번째 속성 형태입니다.

- `sh:path ex:grade` — `ex:grade`로 따라 나온 값들을 본다.
- `sh:in ("A" "B" "C")` — 그 값이 **이 목록 안에 있어야 한다**. 관계형 DB의 `CHECK grade IN ('A','B','C')` 또는 열거형(enum)에 해당합니다.

`("A" "B" "C")` 는 Turtle의 **컬렉션(collection) 축약 문법**입니다. 실제로는 `rdf:first`/`rdf:rest`로 이어진 RDF 리스트로 펼쳐집니다.

```turtle
# ("A" "B" "C") 를 펼치면
_:b1 rdf:first "A" ; rdf:rest _:b2 .
_:b2 rdf:first "B" ; rdf:rest _:b3 .
_:b3 rdf:first "C" ; rdf:rest rdf:nil .
```

여기서 놓치기 쉬운 점 하나. **`ex:grade`에는 `sh:minCount`가 없습니다.** 즉 등급은 **선택 속성**입니다.
"없어도 되지만, 있다면 A/B/C 중 하나여야 한다"가 정확한 의미입니다. 필수로 만들고 싶었다면 `sh:minCount 1`을 같이 적어야 합니다.
`sh:maxCount 1`도 없으니 `ex:grade "A", "B"`처럼 두 개를 달아도 개수 자체는 통과합니다(둘 다 목록 안에 있으므로).

### `sh:severity` — 이 예제에는 안 적혀 있지만 반드시 작동하는 것

각 제약에는 **심각도(severity)** 가 붙습니다. 명시하지 않으면 **기본값이 `sh:Violation`** 입니다.
예제 형태에는 `sh:severity`가 한 줄도 없으므로, 위반은 전부 `sh:Violation`으로 보고됩니다. 그래서 텍스트 보고서에 `Constraint Violation`이라는 문자열이 찍히고, 예제 코드가 그걸 세는 겁니다.

```python
violations = text.count("Constraint Violation")
```

세 단계가 있습니다.

| 값 | 뜻 | 쓰임새 |
|---|---|---|
| `sh:Violation` | 위반 (기본값) | 진짜 막아야 하는 것 |
| `sh:Warning` | 경고 | 고쳐야 하지만 파이프라인을 세울 정도는 아닌 것 |
| `sh:Info` | 정보 | 참고용 관찰 |

```turtle
sh:property [ sh:path ex:grade ; sh:in ("A" "B" "C") ;
              sh:severity sh:Warning ;
              sh:message "등급은 A/B/C 중 하나여야 합니다" ] .
```

중요한 점: **심각도를 낮춰도 `conforms`는 여전히 `true`가 되지 않는다** — 가 아니라, 반대입니다.
SHACL 명세상 `sh:conforms`는 **`sh:Violation` 결과가 하나도 없을 때 `true`** 입니다. `Warning`/`Info`만 있으면 결과 목록에는 나오지만 `conforms`는 `true`가 됩니다.
이게 실무에서 유용한 이유: "적재는 통과시키되 보고서에는 남긴다"를 심각도 한 줄로 조절할 수 있습니다. 12장이 말한 "되돌릴 수 없는 것은 적재 시점에, 나머지는 검증 시점에"를 SHACL 안에서 한 단계 더 세분화하는 손잡이입니다.

`sh:message`도 같이 기억해 두세요. 안 적으면 처리기가 만들어 낸 기계적인 문장이 나오고, 적으면 그 문장이 보고서에 그대로 들어갑니다. 운영자가 읽을 보고서라면 반드시 적는 편이 낫습니다.

---

## 3. 이 형태로 예제 데이터를 검사하면 무엇이 걸리는가

초점 노드는 `ex:Gaon`, `ex:Naru`, `ex:Daol` 셋입니다.

| 노드 | `ex:name` | `ex:grade` | 판정 |
|---|---|---|---|
| `ex:Gaon` | `"가온테크"` — OK | `"Z"` — **`sh:in` 위반** | 위반 1건 |
| `ex:Naru` | `""` — **`sh:minLength` 위반** (minCount·datatype은 통과) | `"A"` — OK | 위반 1건 |
| `ex:Daol` | `"다올물산"` — OK | `"B"` — OK | 통과 |

따라서 `conforms = False`, **위반 총 2건**입니다. 예제의 `BAD_ROWS`가 말하는 "등급이 규칙 밖", "이름이 비었다" 두 줄과 정확히 대응합니다.

여기가 이 장의 핵심 대비입니다. 방식 1(Kuzu)에서는 `grade STRING`이라 `"Z"`도 멀쩡한 문자열이라 **통과해 버립니다**. 예제 출력이 이렇게 말하죠.

> 타입은 막지만 «값의 범위»(등급이 A/B/C 중 하나)는 못 막는다. 이 엔진에는 CHECK 제약이 없다.

`sh:in`은 바로 그 빠진 CHECK 제약을 SHACL 쪽에서 메워 주는 도구입니다. 대신 값은 이미 그래프에 들어가 있고, 우리는 나중에 보고서로 압니다.

---

## 4. 위반 시 나오는 validation report

### 4-1. RDF 그래프 형태 (명세가 정의하는 원본)

SHACL 검증의 결과는 **그 자체가 RDF 그래프**입니다. 이걸 다시 질의하거나 저장할 수 있다는 게 SHACL의 큰 장점입니다.

```turtle
@prefix sh:  <http://www.w3.org/ns/shacl#> .
@prefix ex:  <http://example.org/> .

[] a sh:ValidationReport ;
   sh:conforms false ;
   sh:result [
       a sh:ValidationResult ;
       sh:resultSeverity sh:Violation ;
       sh:sourceConstraintComponent sh:InConstraintComponent ;
       sh:sourceShape _:gradeShape ;
       sh:focusNode  ex:Gaon ;
       sh:resultPath ex:grade ;
       sh:value      "Z" ;
       sh:resultMessage "Value is not in list of allowed values ..."
   ] ,
   [
       a sh:ValidationResult ;
       sh:resultSeverity sh:Violation ;
       sh:sourceConstraintComponent sh:MinLengthConstraintComponent ;
       sh:sourceShape _:nameShape ;
       sh:focusNode  ex:Naru ;
       sh:resultPath ex:name ;
       sh:value      "" ;
       sh:resultMessage "String length not >= Literal(\"1\", ...)"
   ] .
```

읽는 법:

| 술어 | 읽는 법 |
|---|---|
| `sh:conforms` | 전체 통과 여부. `sh:Violation`이 하나도 없어야 `true` |
| `sh:focusNode` | **어느 노드**가 문제인가 → `ex:Gaon` |
| `sh:resultPath` | **어느 속성**이 문제인가 → `ex:grade` |
| `sh:value` | **어떤 값**이 문제인가 → `"Z"` |
| `sh:sourceConstraintComponent` | **어떤 제약**에 걸렸나 → `sh:InConstraintComponent` |
| `sh:sourceShape` | 그 제약이 적힌 형태(여기선 빈 노드) |
| `sh:resultSeverity` | 심각도 |
| `sh:resultMessage` | 사람이 읽을 메시지 |

제약별 컴포넌트 이름은 규칙적입니다.

| 제약 | 컴포넌트 |
|---|---|
| `sh:minCount` | `sh:MinCountConstraintComponent` |
| `sh:minLength` | `sh:MinLengthConstraintComponent` |
| `sh:datatype` | `sh:DatatypeConstraintComponent` |
| `sh:in` | `sh:InConstraintComponent` |

이게 그래프이므로 SPARQL로 바로 집계할 수 있습니다.

```sparql
PREFIX sh: <http://www.w3.org/ns/shacl#>
SELECT ?component (COUNT(*) AS ?n) WHERE {
  ?r a sh:ValidationResult ;
     sh:sourceConstraintComponent ?component .
} GROUP BY ?component ORDER BY DESC(?n)
```

"어떤 제약이 제일 많이 깨지는가"를 바로 뽑을 수 있죠. 12.5절의 드리프트 감사와 자연스럽게 이어집니다.

### 4-2. 사람이 읽는 텍스트 형태 (pyshacl이 만들어 주는 것)

`validate()`가 세 번째로 돌려주는 문자열은 대략 이렇게 생겼습니다.

```
Validation Report
Conforms: False
Results (2):
Constraint Violation in InConstraintComponent (http://www.w3.org/ns/shacl#InConstraintComponent):
	Severity: sh:Violation
	Source Shape: [ sh:in ( Literal("A") Literal("B") Literal("C") ) ; sh:path ex:grade ]
	Focus Node: ex:Gaon
	Value Node: Literal("Z")
	Result Path: ex:grade
	Message: Value is not in list of allowed values
Constraint Violation in MinLengthConstraintComponent (http://www.w3.org/ns/shacl#MinLengthConstraintComponent):
	Severity: sh:Violation
	Source Shape: [ sh:datatype xsd:string ; sh:minCount Literal("1", datatype=xsd:integer) ; ... ]
	Focus Node: ex:Naru
	Value Node: Literal("")
	Result Path: ex:name
	Message: String length not >= Literal("1", datatype=xsd:integer)
```

예제 코드가 이 텍스트를 그대로 파싱합니다.

```python
for line in text.splitlines():
    line = line.strip()
    if line.startswith(("Constraint Violation", "Focus Node", "Value Node", "Message")):
        print(f"    {line[:88]}")
```

즉 **어느 제약(Constraint Violation) / 어느 노드(Focus Node) / 어떤 값(Value Node) / 왜(Message)** 네 줄만 골라 찍는 겁니다. 위반 보고서를 읽을 때 실무에서도 딱 이 네 가지만 보면 됩니다.

> 텍스트 보고서의 정확한 문구·줄 순서는 pyshacl 버전에 따라 조금씩 달라질 수 있습니다. 스크립트에서 개수를 세거나 파싱해야 한다면 문자열보다 **결과 그래프(`results_graph`)를 SPARQL로 질의**하는 쪽이 안전합니다.

---

## 5. pyshacl 사용법

### 5-1. 설치

```bash
pip install "rdflib>=7,<8" pyshacl
```

예제는 `kuzu`도 같이 씁니다(방식 1 비교용).

### 5-2. 파이썬 API — 예제가 쓰는 방식

```python
from pyshacl import validate
from rdflib import Graph

data   = Graph().parse(data=DATA_TTL, format="turtle")
shapes = Graph().parse(data=SHAPES,   format="turtle")

ok, results_graph, text = validate(data, shacl_graph=shapes, inference="none")
```

반환값은 **`(conforms, results_graph, results_text)`** 3-튜플입니다.

| 위치 | 이름 | 내용 |
|---|---|---|
| 0 | `conforms` | `bool`. `sh:Violation`이 없으면 `True` |
| 1 | `results_graph` | `rdflib.Graph`. 위 4-1의 RDF 보고서 |
| 2 | `results_text` | `str`. 위 4-2의 사람용 텍스트 |

자주 쓰는 인자:

| 인자 | 뜻 |
|---|---|
| `shacl_graph` | 형태 그래프. 생략하면 데이터 그래프 안에서 형태를 찾는다 |
| `ont_graph` | 온톨로지 그래프. 추론에 쓸 클래스·속성 정의를 따로 넣을 때 |
| `inference` | `"none"` / `"rdfs"` / `"owlrl"` / `"both"`. 검증 전에 돌릴 추론 |
| `advanced` | `True`면 SPARQL 기반 제약, `sh:rule` 등 고급 기능 활성 |
| `abort_on_first` | 첫 위반에서 중단 |
| `allow_infos` / `allow_warnings` | `Info`/`Warning`을 통과로 취급 |
| `debug` | 검증 과정 로그 출력 |

`inference="none"`은 의도적인 선택입니다. 추론을 켜면 `rdfs:subClassOf`를 타고 대상이 늘어나고, 무엇이 왜 걸렸는지 설명하기가 어려워집니다. 13장에서 "검증을 추론기로 하려다 3주를 날린" 이야기가 나오는 것도 같은 맥락입니다. **검증과 추론은 다른 일**입니다.

### 5-3. CLI

```bash
# 사람이 읽는 보고서
pyshacl -s shapes.ttl -f human data.ttl

# RDF 보고서를 Turtle로
pyshacl -s shapes.ttl -f turtle -o report.ttl data.ttl

# 추론 켜기 / 고급 기능 켜기
pyshacl -s shapes.ttl -i rdfs -a data.ttl
```

**종료 코드가 0이면 통과, 1이면 위반**입니다. 그래서 CI에 그대로 붙일 수 있습니다.

```yaml
- run: pyshacl -s shapes/company.ttl -f human data/companies.ttl
```

---

## 6. 이 형태를 실무로 옮길 때 고칠 곳

예제는 최소 형태라 일부러 생략한 게 많습니다. 실제로 쓴다면 이렇게 보강합니다.

```turtle
ex:CompanyShape a sh:NodeShape ;
    sh:targetClass ex:Company ;
    sh:property [
        sh:path      ex:name ;
        sh:name      "회사명" ;
        sh:minCount  1 ;
        sh:maxCount  1 ;          # 이름은 하나만
        sh:minLength 1 ;
        sh:datatype  xsd:string ;
        sh:message   "회사명은 비어 있지 않은 문자열 하나여야 합니다."
    ] ;
    sh:property [
        sh:path     ex:grade ;
        sh:minCount 1 ;           # 등급도 필수로
        sh:maxCount 1 ;
        sh:in       ("A" "B" "C") ;
        sh:severity sh:Warning ;  # 막지는 않고 보고서에만
        sh:message  "등급은 A, B, C 중 하나여야 합니다."
    ] ;
    sh:closed true ;              # 선언 안 한 속성은 금지
    sh:ignoredProperties ( rdf:type ) .
```

추가된 것들:

- `sh:maxCount` — 값이 여러 개 붙는 걸 막습니다. `minCount`만 있으면 중복이 통과합니다.
- `sh:name` / `sh:message` — 보고서를 사람 말로 만듭니다.
- `sh:severity sh:Warning` — 등급 오류는 적재를 멈추지 않고 보고서에만 남깁니다.
- `sh:closed true` — **선언하지 않은 속성이 붙으면 위반**. 오타 속성(`ex:nmae`)을 잡는 가장 값싼 방법입니다. `rdf:type`은 항상 붙으므로 `sh:ignoredProperties`로 빼 줍니다.

자주 쓰는 다른 제약도 같이 외워 두면 좋습니다.

| 제약 | 의미 |
|---|---|
| `sh:pattern` | 정규식 (예: 사업자등록번호 형식) |
| `sh:nodeKind` | `sh:IRI` / `sh:Literal` / `sh:BlankNode` 등 노드 종류 |
| `sh:class` | 값 노드가 특정 클래스의 인스턴스여야 함 (관계의 타입 검사) |
| `sh:minInclusive` / `sh:maxInclusive` | 수치 범위 |
| `sh:node` | 값 노드가 또 다른 노드 형태를 만족해야 함 (중첩) |
| `sh:or` / `sh:and` / `sh:not` / `sh:xone` | 논리 조합 |
| `sh:languageIn` / `sh:uniqueLang` | 다국어 리터럴 |

---

## 7. 시험 대비 요약

- `ex:CompanyShape`는 `sh:NodeShape`이고, `sh:targetClass ex:Company`로 **`ex:Company` 인스턴스 전부**를 검사한다.
- `ex:name`: **`sh:minCount 1`**(반드시 있어야), **`sh:minLength 1`**(비어 있으면 안 되고), **`sh:datatype xsd:string`**(문자열이어야).
- `ex:grade`: **`sh:in ("A" "B" "C")`** — 있다면 A/B/C 중 하나. `minCount`가 없으니 **선택 속성**.
- `sh:severity`는 안 적혀 있고, 기본값은 **`sh:Violation`**. 그래서 텍스트 보고서에 `Constraint Violation`이 찍히고 예제가 그걸 센다.
- 예제 데이터에서는 `ex:Gaon`(grade `"Z"` → `sh:in` 위반)과 `ex:Naru`(name `""` → `sh:minLength` 위반) **2건**이 잡히고 `conforms=False`.
- 보고서는 RDF 그래프이며 `sh:focusNode` / `sh:resultPath` / `sh:value` / `sh:sourceConstraintComponent`가 핵심 네 축.
- `validate()`는 `(conforms, results_graph, results_text)`를 돌려주고, 예제는 `inference="none"`으로 추론을 끄고 검증만 한다.
- 장의 논지: Kuzu는 **적재 시점**에 타입만 막고 값 범위는 못 막는다. SHACL은 **검증 시점**에 값 범위까지 잡되 데이터는 이미 들어가 있다. 진짜 차이는 「언제 아느냐」다.

## 더 읽을거리

- [SHACL — W3C Recommendation](https://www.w3.org/TR/shacl/) (12장 키워드 표의 1차 출처)
- [pyshacl](https://github.com/RDFLib/pySHACL)
- [RDF Schema 1.1](https://www.w3.org/TR/rdf11-schema/)
