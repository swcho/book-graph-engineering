# Kuzu의 스키마 강제 — 막는 것과 못 막는 것

**질문**: Kuzu의 스키마 강제로 막을 수 있는 것과 막을 수 없는 것은 각각 무엇인가?

**답**: 타입은 막지만 값의 범위(등급이 A/B/C 중 하나)는 막지 못한다. 이 엔진에는 CHECK 제약이 없으며 엔진마다 다르다.

---

## 1. 이 질문이 나온 자리

12장 「스키마를 언제 못 박을 것인가」 절의 예제 `ex3_when_schema.py`가 출처입니다.
같은 «잘못된 데이터» 두 줄을 세 가지 방식에 넣어 보고, **언제 걸리는지**를 비교하는 예제죠.

```python
BAD_ROWS = [
    ("등급이 규칙 밖", "가온테크", "Z"),   # grade 가 A/B/C 가 아니다
    ("이름이 비었다", "", "A"),            # name 이 빈 문자열이다
]
```

방식 1이 Kuzu(확인 시점 0.11.3)입니다. 스키마는 이렇게 잡혀 있습니다.

```python
conn.execute("CREATE NODE TABLE Company(name STRING, grade STRING, "
             "PRIMARY KEY(name))")
```

그리고 예제가 출력하는 결론이 그대로 답입니다.

```
→ 타입은 막지만 «값의 범위»(등급이 A/B/C 중 하나)는 못 막는다.
  이 엔진에는 CHECK 제약이 없다. 엔진마다 다르다.
```

`grade:'Z'`도 `name:''`도 **둘 다 STRING이므로 그냥 들어갑니다.** 스키마가 있다고 해서
"검증이 되고 있다"고 생각하면 안 된다는 것이 이 절의 핵심입니다.

## 2. Kuzu의 스키마가 «보장하는» 것

Kuzu는 스키마 강제(schema-enforced) 속성 그래프 엔진입니다. 문서가 label 대신 **table**이라는
단어를 쓰는 이유도, 내부적으로 관계형 시스템에 가깝기 때문입니다. 그래서 다음은 적재 시점에
확실히 막힙니다.

| 보장 항목 | 무엇을 막는가 | 예제에서의 근거 |
|---|---|---|
| **테이블 존재** | 선언되지 않은 노드/관계 테이블에 쓰기 | `CREATE NODE TABLE`을 먼저 해야 `CREATE (:Company ...)`가 된다 |
| **속성(컬럼) 집합** | 선언에 없는 속성을 임의로 붙이기 | ex5의 스키마 드리프트(`legacy_code`, `temp_flag`)가 LPG 무스키마에서나 생기는 일 |
| **타입** | STRING 자리에 구조가 안 맞는 값 | `name STRING, grade STRING` |
| **PRIMARY KEY** | 널(NULL)과 중복 | 노드 테이블에는 PK가 **필수**. `PRIMARY KEY(name)` |
| **관계 양 끝단 타입** | 엉뚱한 노드끼리 잇기 | `CREATE REL TABLE Uses(FROM Product TO Part)` — Part가 아닌 것에 `Uses`를 걸 수 없다 |
| **관계 다중도(multiplicity)** | 1:1/1:N 위반 | `ONE_ONE`, `ONE_MANY`, `MANY_ONE`, `MANY_MANY` 지정 시 엔진이 강제 |
| **기본값(DEFAULT)** | (막는 건 아니지만) 값 누락 시 채움. 미지정이면 NULL |  |

ex2의 A안/B안 스키마가 이 보장의 예입니다.

```
CREATE REL TABLE UsesBolt(FROM Product TO Bolt)     # A안: 끝단이 Bolt로 못 박힘
CREATE REL TABLE Uses(FROM Product TO Part)         # B안: 끝단이 Part로 못 박힘
```

**B안에서 `category:'전자'`를 `category:'전자부품'`으로 오타 내는 것은 아무도 안 막아 줍니다.**
분류를 클래스에서 속성으로 내리면(12.2절) 얻는 유연성의 대가가 정확히 이것입니다.
A안이라면 「없는 테이블」이라 적재가 실패했을 오류가, B안에서는 조용히 통과합니다.

## 3. Kuzu가 «못 막는» 것

한 줄로: **값의 의미에 관한 규칙 전부**.

- **열거값 / 값의 범위** — `grade`가 A·B·C 중 하나인가. `quantity > 0`인가. `discount BETWEEN 0 AND 1`인가.
- **문자열의 내용 규칙** — 빈 문자열 금지, 최소 길이, 정규식(사업자등록번호 형식 등).
- **PK 아닌 속성의 필수(NOT NULL)·유일성(UNIQUE)** — Kuzu에서 이 보장은 사실상 **PRIMARY KEY 하나에만** 붙습니다.
  ex3에서 `name`이 PK라서 빈 문자열이라도 «값이 있으니» 통과합니다. 만약 PK가 아니었다면 NULL도 들어갔겠죠.
- **속성 사이의 관계(레코드 내 제약)** — `released_on <= recalled_on` 같은 것.
- **카디널리티 형태 제약** — 「제품은 부품을 1개 이상 가져야 한다」. 다중도는 «최대 몇 개»에 가깝지
  「최소 1개는 있어야 한다」를 SHACL의 `sh:minCount`처럼 일반적으로 표현하지는 못합니다.
- **속성 조합의 존재 규칙** — 「리콜된 제품에는 `recall_reason`이 반드시 있어야 한다」(ex5의 `-` 표시가 잡아내는 그것).

관계형 DB라면 이 대부분이 `CHECK`, `NOT NULL`, `UNIQUE`, `FOREIGN KEY`, `ENUM` 도메인 타입으로
해결됩니다. **Kuzu의 DDL에는 CHECK에 해당하는 문법이 (확인한 문서 범위에서는) 없습니다.**

> 확실성 표기: Kuzu의 `CREATE NODE TABLE` / `CREATE REL TABLE` 문서에서 확인되는 것은
> 타입, `PRIMARY KEY`(노드 테이블 필수), `DEFAULT`, `SERIAL`, 관계 끝단 타입과 다중도입니다.
> CHECK 제약은 문서에 나타나지 않으며, 본문 예제(0.11.3)의 실행 결과도 값 범위 위반이 통과하는
> 것을 보여 줍니다. 버전이 올라가면 달라질 수 있으니, **현재 쓰는 버전에서 직접 넣어 보고 확인**하는 것이
> 안전합니다. 예제가 하는 일이 정확히 그 «직접 넣어 보기»입니다.

## 4. 그래서 왜 SHACL / 애플리케이션 레벨 검증이 따라오는가

엔진이 «값의 의미»를 안 봐 주면, 그 일은 사라지지 않고 **다른 층으로 이동합니다.** 갈 곳은 셋뿐입니다.

1. **적재 파이프라인(애플리케이션 코드)** — INSERT 전에 파이썬으로 검사.
2. **검증 계층(SHACL 같은 형태 제약 언어)** — 적재는 되고, 배치가 돌 때 보고서로 안다.
3. **아무 데도 안 감** — 6개월 뒤 사용자가 알려 준다.

3번이 12장이 가장 위험하다고 말하는 상태입니다. 특히 **문서만 있고 검사가 없는 경우**가 최악인데,
「우리는 등급을 A/B/C로 씁니다」라고 위키에 적혀 있으면 **지켜지고 있다고 착각**하기 때문입니다.

ex3의 방식 2가 SHACL입니다. Kuzu가 못 막은 규칙이 SHACL에서는 선언으로 표현됩니다.

```turtle
ex:CompanyShape a sh:NodeShape ;
    sh:targetClass ex:Company ;
    sh:property [ sh:path ex:name ; sh:minCount 1 ; sh:minLength 1 ;
                  sh:datatype xsd:string ] ;     # 빈 문자열을 막는다
    sh:property [ sh:path ex:grade ; sh:in ("A" "B" "C") ] .   # 값의 범위를 막는다
```

`sh:in`이 정확히 CHECK 제약의 자리를 메우고, `sh:minLength 1`이 빈 이름을 잡습니다.
`sh:minCount`, `sh:maxCount`, `sh:pattern`, `sh:lessThan` 등으로 3절에서 «못 막는다»고 나열한 것들을
거의 그대로 덮을 수 있습니다.

핵심은 SHACL이 Kuzu의 «상위 호환»이라는 게 아니라, **작동 시점이 다르다**는 것입니다.

| 방식 | 언제 아는가 | 대가 |
|---|---|---|
| 스키마 강제 (Kuzu 타입·PK·끝단) | 적재 시점, 즉시 | 적재가 실패하니 파이프라인이 멈춘다 |
| SHACL / 배치 검증 | 검증 배치가 돌 때 | 나쁜 데이터가 이미 그래프 안에 들어가 있다 |
| 없음 | 사용자가 알려 준다 | — |

저자의 기준은 「**되돌릴 수 없는 것은 적재 시점에, 나머지는 검증 시점에**」입니다.
적재를 너무 엄격하게 잡으면 데이터가 아예 안 들어와서 그것대로 문제가 됩니다.

한 가지 덧붙이면, SHACL은 RDF 위에서 도는 표준이므로 Kuzu 같은 LPG 엔진에 그대로 얹히지 않습니다.
ex3이 Kuzu 부분과 rdflib+pyshacl 부분을 **분리해서** 보여 주는 이유가 이것입니다.
LPG에서 같은 일을 하려면 (가) 그래프를 RDF로 내보내 SHACL을 돌리거나, (나) 검증 질의를 Cypher로
직접 짜서 배치로 돌리거나(ex5의 드리프트 감사가 그 30줄짜리 축소판), (다) 적재 코드에서 검사해야 합니다.

## 5. 다른 엔진과의 차이 — 「엔진마다 다르다」의 실제 내용

답의 마지막 문장 「엔진마다 다르다」가 시험에 나오는 부분입니다. 확인된 범위에서 정리하면.

| 엔진 / 계층 | 타입 | 필수(존재) | 유일성 | 값의 범위 (CHECK/enum) |
|---|---|---|---|---|
| **Kuzu** | 예 (테이블 컬럼 타입) | PK만 | PK만 | **아니오** |
| **Neo4j Community** | 아니오(에디션 제한) | 아니오 | 예 (property uniqueness) | 아니오 |
| **Neo4j Enterprise** | 예 (property type constraint) | 예 (existence constraint) | 예 + node/rel key | **아니오** |
| **RDF + SHACL** | 예 (`sh:datatype`) | 예 (`sh:minCount`) | 형태로 표현 가능 | **예** (`sh:in`, `sh:pattern`, 범위 비교) |
| **관계형 DB (PostgreSQL 등)** | 예 | `NOT NULL` | `UNIQUE` | **예** (`CHECK`, `ENUM`, 도메인 타입) |

읽는 법 세 가지.

- **Neo4j는 스키마 옵셔널**입니다. Kuzu처럼 테이블을 먼저 선언해야 쓸 수 있는 구조가 아니고,
  아무 라벨·아무 속성이나 쓸 수 있는 상태가 기본이며 **제약을 «추가»해서 조입니다.** 방향이 반대죠.
  게다가 네 종류 중 세 종류(존재, 키, 속성 타입)가 **Enterprise 전용**이라, 커뮤니티 에디션에서는
  유일성 제약 하나로 버텨야 합니다.
- 그럼에도 **Neo4j에도 CHECK는 없습니다.** 즉 「값의 범위를 엔진이 못 막는다」는 Kuzu만의 흠이
  아니라 현재 주류 그래프 엔진 전반의 상태에 가깝습니다. 그래서 SHACL이나 애플리케이션 검증이
  선택이 아니라 사실상 기본 구성이 됩니다.
- **표준 쪽 흐름**: 12장의 키워드 표에 있는 `ISO/IEC 39075:2024 GQL`이 그래프 스키마 선언을
  표준화하려는 시도입니다. 다만 각 엔진이 어디까지 구현했는지는 제품·버전마다 다르니,
  **「우리 엔진, 우리 버전에서 실제로 넣어 보고 막히는지 확인」**하는 습관이 정답입니다.
  이 장의 예제가 문서 대신 실행 결과를 보여 주는 이유이자, 12.5절 「문서 말고 데이터에게 물어보라」와
  같은 태도입니다.

## 6. 한 문장으로

**Kuzu는 «형태»(테이블·속성·타입·PK·관계 끝단·다중도)를 적재 시점에 강제하지만 «값의 의미»(범위, 열거,
필수, 패턴)는 검사하지 않으며, CHECK 제약이 없으므로 그 일은 SHACL이나 애플리케이션·배치 검증으로
반드시 옮겨 놓아야 한다. 그리고 어디까지 막히는지는 엔진과 버전마다 다르므로 직접 넣어 보고 확인한다.**

## 함께 보면 좋은 것

- 12.3절 예제 `code/ex3_when_schema.py` — 이 카드의 직접 출처
- 12.5절 예제 `code/ex5_schema_drift.py` — 엔진이 안 막아 준 결과가 6개월 뒤 어떤 모습인지
- 13장 「검증하지 않은 그래프는 그냥 링크 뭉치다」 — 검증을 추론기로 하려다 3주를 날린 이야기
- [SHACL — Shapes Constraint Language](https://www.w3.org/TR/shacl/) (W3C 표준)
- [Kuzu — Create table](https://docs.kuzudb.com/cypher/data-definition/create-table/)
- [Neo4j Cypher Manual — Constraints](https://neo4j.com/docs/cypher-manual/current/constraints/)
- [ISO/IEC 39075:2024 GQL](https://www.iso.org/standard/76120.html)
