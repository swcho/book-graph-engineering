# A안(깊은 분류)에서 "제품이 쓰는 부품 전부" 질의

**질문** — A안(깊은 분류)에서 "제품이 쓰는 부품 전부" 질의는 어떻게 되는가?

**답** — 부품 종류마다 MATCH 절을 쓰고 UNION으로 이어야 한다. 종류가 늘면 질의문도 늘어난다.

---

## 왜 이런 일이 생기나

A안은 도메인 전문가가 처음 제시한 방식입니다. 볼트는 볼트, 너트는 너트, 저항은 저항 — **다른 물건이니 다른 클래스**로 나눕니다. 분류학으로는 흠잡을 데가 없습니다.

문제는 그 결과 **"부품"이라는 개념이 스키마 어디에도 존재하지 않게 된다**는 점입니다. 그래프에 있는 건 `Bolt`, `Nut`, `Resistor`, `Capacitor`이고, 이들을 한꺼번에 가리키는 이름이 없습니다. 관계도 마찬가지로 `UsesBolt`, `UsesNut`, `UsesResistor`, `UsesCapacitor`로 쪼개져 있습니다.

그래서 "제품이 쓰는 부품 전부"라는, 사람에게는 한 문장인 질문이 **종류 개수만큼의 질의를 합집합으로 붙인 것**이 됩니다.

## 두 안의 스키마

### A안 — 깊은 분류

```cypher
CREATE NODE TABLE Bolt(id STRING, name STRING, PRIMARY KEY(id))
CREATE NODE TABLE Nut(id STRING, name STRING, PRIMARY KEY(id))
CREATE NODE TABLE Resistor(id STRING, name STRING, PRIMARY KEY(id))
CREATE NODE TABLE Capacitor(id STRING, name STRING, PRIMARY KEY(id))
CREATE NODE TABLE Product(id STRING, PRIMARY KEY(id))

CREATE REL TABLE UsesBolt(FROM Product TO Bolt)
CREATE REL TABLE UsesNut(FROM Product TO Nut)
CREATE REL TABLE UsesResistor(FROM Product TO Resistor)
CREATE REL TABLE UsesCapacitor(FROM Product TO Capacitor)
```

노드 테이블 5개, 관계 테이블 4개.

### B안 — 얕은 분류

```cypher
CREATE NODE TABLE Part(id STRING, name STRING, category STRING, PRIMARY KEY(id))
CREATE NODE TABLE Product(id STRING, PRIMARY KEY(id))

CREATE REL TABLE Uses(FROM Product TO Part)
```

노드 테이블 2개, 관계 테이블 1개. 볼트/너트/저항/커패시터의 구분은 **클래스가 아니라 `category` 속성 값**으로 내려갑니다.

## 같은 질문, 두 개의 질의문

### A안 — 종류마다 MATCH 한 줄, 사이사이 UNION

```cypher
MATCH (p:Product {id:'P1'})-[:UsesBolt]->(x:Bolt)           RETURN x.name AS 부품
UNION
MATCH (p:Product {id:'P1'})-[:UsesNut]->(x:Nut)             RETURN x.name AS 부품
UNION
MATCH (p:Product {id:'P1'})-[:UsesResistor]->(x:Resistor)   RETURN x.name AS 부품
UNION
MATCH (p:Product {id:'P1'})-[:UsesCapacitor]->(x:Capacitor) RETURN x.name AS 부품
```

7줄. 부품 종류 4개 × MATCH 1줄 + 그 사이 UNION 3줄입니다.

### B안 — 한 줄

```cypher
MATCH (p:Product {id:'P1'})-[:Uses]->(x:Part) RETURN x.name AS 부품
```

1줄. **두 질의의 결과는 완전히 같습니다.** 얻는 답은 동일한데 질의문의 길이와 유지 비용만 다릅니다.

## 종류가 하나 늘면 — 「와셔」를 추가한다

여기가 이 카드의 핵심입니다.

### A안에서 고쳐야 하는 곳 — 3군데

1. **노드 테이블 하나** 추가 — `CREATE NODE TABLE Washer(...)`
2. **관계 테이블 하나** 추가 — `CREATE REL TABLE UsesWasher(FROM Product TO Washer)`
3. **"부품 전부" 질의에 UNION 한 줄 + MATCH 한 줄** 추가

```cypher
-- 기존 4개 절 뒤에 이어 붙여야 한다
UNION
MATCH (p:Product {id:'P1'})-[:UsesWasher]->(x:Washer)       RETURN x.name AS 부품
```

그리고 3번은 **한 곳이 아닙니다.** "부품 전부"류 질의가 리포트에, 대시보드에, API 핸들러에, 배치 작업에 흩어져 있다면 **그 전부를 찾아 고쳐야** 합니다. 하나라도 빠뜨리면 그 질의는 에러를 내지 않고 **조용히 와셔만 빠진 결과**를 돌려줍니다. 이게 가장 나쁜 실패 방식입니다.

### B안에서 고쳐야 하는 곳 — 0군데

```cypher
CREATE (:Part {id:'W1', name:'M6 와셔', category:'체결'})
```

**행 하나를 넣으면 끝.** 스키마도 그대로, 질의문도 그대로입니다. 다음 날 새 부품 종류가 열 개 더 들어와도 마찬가지입니다.

## 숫자로 비교

| 항목 | A안 (깊게) | B안 (얕게) |
|---|---:|---:|
| 노드 테이블 수 | 5 | 2 |
| 관계 테이블 수 | 4 | 1 |
| 질의문 줄 수 | 7 | 1 |
| 부품 종류 추가 시 고칠 곳 | 3 | 0 |

앞의 세 줄은 "지금 좀 길다" 정도의 이야기입니다. **마지막 줄이 진짜 비용**입니다. 앞의 셋은 한 번 치르면 끝나는 값이지만, 마지막 줄은 **부품 종류가 늘 때마다 반복해서 치르는 값**이기 때문입니다.

부품 종류가 N개면 A안의 "부품 전부" 질의는 대략 `2N - 1`줄(MATCH N줄 + UNION N-1줄)로 자랍니다. 12장 도입부에 나오는 전문가의 214개 분류 체계를 그대로 A안으로 옮겼다면, 이 한 질문에 답하는 질의문이 수백 줄이 됩니다.

## 그럼 A안은 무조건 나쁜가

아닙니다. 판단 기준은 이겁니다.

> 분류를 나누는 기준은 **「다른 속성을 갖는가」**이지 **「다른 물건인가」**가 아니다.

- 볼트에만 있는 속성(나사산 규격, 강도 등급 같은 것)이 많고, **그 속성으로 질의한다면** A안이 맞습니다. 이때는 `Part` 하나에 몰아 두면 대부분 NULL인 컬럼이 잔뜩 생기고, 어떤 컬럼이 어떤 category에 유효한지가 스키마 밖의 암묵 규칙이 됩니다.
- 반대로 **종류만 다르고 속성 구성이 같다면**, 종류는 클래스가 아니라 속성 값입니다. 특히 **종류가 많거나 자주 늘어나는 축**이라면 더욱 그렇습니다. 클래스는 늘리는 데 스키마 변경이 필요하지만, 속성 값은 행 하나면 됩니다.

이 장의 전체 논지와도 이어집니다. 온톨로지는 도메인의 진리가 아니라 **지금 우리 질의가 필요로 하는 최소 어휘**입니다. 역량 질문 다섯 개 중 "제품 P의 부품 목록을 3단계까지 펼치면?"이 있다면, 그 질문에 **"부품"이라는 낱말이 등장한다**는 사실 자체가 스키마에 `Part`라는 이름이 있어야 한다는 신호입니다. A안에는 질문에 나오는 그 낱말이 스키마에 없어서, 질의문이 그 빈자리를 UNION으로 메우고 있는 셈입니다.

## 한 줄 정리

A안에서 "제품이 쓰는 부품 전부"는 **부품 종류마다 MATCH 절을 쓰고 UNION으로 이어 붙인 질의**가 되고, 종류가 늘 때마다 **노드 테이블 + 관계 테이블 + 흩어진 모든 UNION 질의문**을 함께 고쳐야 합니다. B안은 행 하나 추가로 끝납니다.

## 더 보기

- 예제 코드: `content/ch12/code/ex2_deep_vs_flat.py`
- 역량 질문(competency question): [Ontology Development 101](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf)
- 그래프 스키마 선언: [ISO/IEC 39075:2024 GQL](https://www.iso.org/standard/76120.html)
