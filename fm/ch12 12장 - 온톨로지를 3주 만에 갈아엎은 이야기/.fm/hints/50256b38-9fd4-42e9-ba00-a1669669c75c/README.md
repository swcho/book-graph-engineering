# 분류(클래스)를 나누는 올바른 근거

> **Q.** 분류(클래스)를 나누는 올바른 근거는 무엇인가?
>
> **A.** 「다른 물건인가」가 아니라 「다른 속성을 갖는가」다. 종류가 많거나 자주 늘면 클래스가 아니라 속성으로 둔다.

## 한 줄 정리

클래스를 새로 파는 근거는 **그 부류에만 있는 속성(과 그 속성으로 하는 질의)** 이다. 눈으로 봐서 다른 물건이라는 건 근거가 아니다.

## 왜 「다른 물건인가」가 함정인가

사람은 사물을 보면 자연스럽게 이름을 붙이고 나눈다. 도메인 전문가에게 물으면 특히 그렇다. 12장의 실제 사례에서 전문가가 처음 제시한 분류는 **214개 클래스**였다.

```
부품, 기계부품, 전자부품, 체결부품, 볼트, 너트, 와셔,
리벳, 육각볼트, 십자볼트, 스테인리스육각볼트, M6스테인리스육각볼트,
저항, 커패시터, 세라믹커패시터, 전해커패시터, 반도체, 다이오드,
트랜지스터, MOSFET, N채널MOSFET, ...
```
(`code/questions.py`의 `EXPERT_TAXONOMY`)

`M6스테인리스육각볼트`는 **틀린 분류가 아니다. 정확한 분류다.** 다만 우리가 답하려는 다섯 개의 역량 질문(competency question)에 답하는 데 필요가 없었다. 실제로 질문에서 거꾸로 뽑은 어휘는 클래스 4개(부품, 제품, 공급사, 리콜)뿐이었다.

즉, **「물건이 다르다」는 관찰은 언제나 참이라서 판단 기준이 되지 못한다.** 무한히 쪼갤 수 있기 때문이다. 끝나는 조건이 없는 기준은 기준이 아니다.

## 「다른 속성을 갖는가」가 근거인 이유

클래스를 쪼개서 얻는 것은 **그 클래스에만 붙는 속성과 제약**이다.

- 볼트에만 `나사산_규격`, `피치`, `강도등급`이 있고 **그 속성으로 질의한다** → `Bolt` 클래스를 따로 두는 게 맞다.
- 볼트와 너트와 저항이 전부 `id`, `name`, `category`만 갖는다 → 클래스를 나눌 이유가 없다. `Part` 하나에 `category` 속성으로 둔다.

속성이 같은데 클래스만 다르면, 그 분류는 **정보를 담지 않고 비용만 만든다.**

## 예제로 보는 비용 차이 (`code/ex2_deep_vs_flat.py`)

같은 데이터를 두 방식으로 넣고 「제품 P1이 쓰는 부품 전부」를 물어본다.

### A안 — 깊은 분류 (물건이 다르면 클래스)

```cypher
CREATE NODE TABLE Bolt(id STRING, name STRING, PRIMARY KEY(id))
CREATE NODE TABLE Nut(id STRING, name STRING, PRIMARY KEY(id))
CREATE NODE TABLE Resistor(id STRING, name STRING, PRIMARY KEY(id))
CREATE NODE TABLE Capacitor(id STRING, name STRING, PRIMARY KEY(id))
CREATE REL TABLE UsesBolt(FROM Product TO Bolt)
CREATE REL TABLE UsesNut(FROM Product TO Nut)
...
```

질의는 종류마다 한 줄씩 늘어난다.

```cypher
MATCH (p:Product {id:'P1'})-[:UsesBolt]->(x:Bolt)           RETURN x.name AS 부품
UNION
MATCH (p:Product {id:'P1'})-[:UsesNut]->(x:Nut)             RETURN x.name AS 부품
UNION
MATCH (p:Product {id:'P1'})-[:UsesResistor]->(x:Resistor)   RETURN x.name AS 부품
UNION
MATCH (p:Product {id:'P1'})-[:UsesCapacitor]->(x:Capacitor) RETURN x.name AS 부품
```

### B안 — 얕은 분류 (속성이 같으면 속성으로)

```cypher
CREATE NODE TABLE Part(id STRING, name STRING, category STRING, PRIMARY KEY(id))
CREATE NODE TABLE Product(id STRING, PRIMARY KEY(id))
CREATE REL TABLE Uses(FROM Product TO Part)
```

```cypher
MATCH (p:Product {id:'P1'})-[:Uses]->(x:Part) RETURN x.name AS 부품
```

### 결과 — 답은 같고 비용만 다르다

| 항목 | A안 (깊게) | B안 (얕게) |
|---|---:|---:|
| 노드 테이블 수 | 5 | 2 |
| 관계 테이블 수 | 4 | 1 |
| 질의문 줄 수 | 8 | 1 |
| **부품 종류 추가 시 고칠 곳** | **3** | **0** |

마지막 줄이 핵심이다. A안에서 「와셔」를 추가하려면 ① 노드 테이블 하나, ② 관계 테이블 하나, ③ 「부품 전부」 질의에 `UNION` 한 줄을 더 넣어야 한다. **스키마 변경 + 코드 변경 + 배포**가 따라온다. B안에서는 `category:'체결'`인 행 하나를 넣으면 끝난다.

## 그래서 A안이 무조건 나쁜가

아니다. **볼트에만 있는 속성(나사산 규격 같은 것)이 많고 그것으로 질의한다면 A안이 맞다.** 그때는 클래스를 나눠야 그 속성에 타입과 제약을 걸 수 있고, 질의도 `MATCH (b:Bolt) WHERE b.pitch = 1.0` 처럼 자연스러워진다.

판단은 결국 두 질문이다.

1. **이 부류에만 있는 속성이 있는가?** 없으면 속성(라벨/카테고리)으로 둔다.
2. **그 속성으로 실제로 질의하는가?** 안 하면 아직 클래스로 승격시킬 때가 아니다.

## 두 번째 규칙 — 「자주 늘어나는가」

카드 뒷면의 후반부(“종류가 많거나 자주 늘면 클래스가 아니라 속성으로 둔다”)는 **변경 빈도**에 대한 규칙이다.

- **클래스는 스키마다.** 늘리려면 DDL을 치고 질의를 고치고 배포해야 한다. → 변경 비용이 크다.
- **속성 값은 데이터다.** 늘리려면 행 하나 넣으면 된다. → 변경 비용이 거의 없다.

따라서 **자주 바뀌는 것은 데이터 쪽에, 안정적인 것은 스키마 쪽에** 둔다. 부품 종류처럼 분기마다 새 항목이 생기는 축은 스키마에 박으면 안 된다. 반대로 「제품 / 부품 / 공급사 / 리콜」처럼 도메인이 존재하는 한 안 바뀌는 축은 클래스로 두는 게 맞다.

경험칙으로:
- 종류가 손에 꼽히고 몇 년째 그대로다 → 클래스 후보
- 종류가 수십~수백이고 계속 늘어난다 → 속성 값 (`category`, `type` 같은 필드)

## 실무에서 쓰는 체크리스트

새 클래스를 만들자는 제안이 왔을 때 순서대로 물어본다.

1. 이 클래스에만 있는 **속성**이 무엇인가? 없으면 → 속성으로.
2. 그 속성으로 **거는 질의**가 실제로 있는가? 없으면 → 속성으로.
3. 이 클래스에만 걸리는 **제약(필수/범위)** 이 있는가? 있으면 클래스 근거가 강해진다.
4. 이 축의 종류가 **1년에 몇 개나 늘 것 같은가?** 자주 늘면 → 속성으로.
5. 이 클래스만 갖는 **관계**가 있는가? (부품→볼트만 `HasThread` 같은 것) 있으면 클래스 근거가 된다.

RDF 진영에서도 같은 판단이 있다. 「클래스로 만들 것인가, `skos:Concept` 값으로 둘 것인가」의 문제다. 자주 늘어나는 분류 축은 OWL 클래스 계층 대신 SKOS 개념 체계에 두고 속성으로 가리키는 게 일반적인 해법이다.

## 흔한 오해

- **「클래스가 많아야 정교한 온톨로지」** → 아니다. 안 쓰는 분류 190개를 유지하는 비용이, 필요해질 때 하나 넣는 비용보다 훨씬 크다. 온톨로지는 도메인의 진리가 아니라 **지금 우리 질의가 필요로 하는 최소 어휘**다.
- **「나중에 필요할지 모르니 미리 쪼개자」** → 미리 쪼갠 클래스는 질의문과 파이프라인에 전부 흔적을 남긴다. 필요해지는 순간이 오면 그때 넣는다.
- **「속성으로 두면 타입 안정성을 잃는다」** → 잃는 것은 맞다. 그래서 값 범위 검사가 필요하면 SHACL(`sh:in ("체결" "전자" ...)`) 같은 검증 계층으로 보완한다(12.3절, `ex3_when_schema.py`).

## 함께 보면 좋은 것

- `code/ex1_vocab_from_questions.py` — 214개 분류 중 다섯 질문에 쓰이는 것만 남기는 과정
- `code/ex2_deep_vs_flat.py` — 이 카드의 직접 근거가 되는 예제
- [SHACL](https://www.w3.org/TR/shacl/) — 클래스를 안 쪼개고 값 범위를 제약하는 방법
- [SKOS](https://www.w3.org/TR/skos-reference/) — 자주 늘어나는 분류 축을 개념 체계로 두는 표준
- [Ontology Development 101](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf) — 역량 질문과 「클래스 vs 속성」 판단의 고전적 출처
