# 부품 종류를 추가할 때 두 안의 수정 범위

**질문**: 부품 종류를 추가할 때 두 안의 수정 범위는 어떻게 다른가?

**답**: A안은 노드 테이블·관계 테이블·질의 UNION 세 곳을 고쳐야 하고, B안은 행 하나만 넣으면 된다.

출처: 12장 예제 2 `code/ex2_deep_vs_flat.py` (깊은 분류 vs 얕은 분류)

---

## 1. 두 안이 무엇이었나

| | A안 — 깊은 분류 | B안 — 얕은 분류 |
|---|---|---|
| 발상 | 도메인 전문가의 분류 체계를 그대로 스키마로 옮긴다 | 역량 질문에서 거꾸로 뽑은 최소 어휘만 둔다 |
| 부품 표현 | `Bolt`, `Nut`, `Resistor`, `Capacitor` … 종류마다 **노드 테이블 하나** | `Part` 하나 + `category` **속성** |
| 관계 표현 | `UsesBolt`, `UsesNut`, `UsesResistor` … 종류마다 **관계 테이블 하나** | `Uses` 하나 |
| 노드 테이블 수 | 5 | 2 |
| 관계 테이블 수 | 4 | 1 |
| 「부품 전부」 질의 | UNION 4갈래 | 한 줄 |
| **부품 종류 추가 시 고칠 곳** | **3** | **0** |

예제가 마지막에 찍는 표의 `("부품 종류 추가 시 고칠 곳", 3, 0)` 이 한 줄이 이 카드의 핵심입니다.

---

## 2. A안에서 「와셔」를 추가한다면 — 실제로 고쳐야 하는 세 곳

### 고칠 곳 (1) 노드 테이블 — DDL 추가

```python
DEEP_SCHEMA = [
    "CREATE NODE TABLE Bolt(id STRING, name STRING, PRIMARY KEY(id))",
    "CREATE NODE TABLE Nut(id STRING, name STRING, PRIMARY KEY(id))",
    "CREATE NODE TABLE Resistor(id STRING, name STRING, PRIMARY KEY(id))",
    "CREATE NODE TABLE Capacitor(id STRING, name STRING, PRIMARY KEY(id))",
+   "CREATE NODE TABLE Washer(id STRING, name STRING, PRIMARY KEY(id))",   # ← (1)
    "CREATE NODE TABLE Product(id STRING, PRIMARY KEY(id))",
    ...
]
```

### 고칠 곳 (2) 관계 테이블 — DDL 추가

```python
    "CREATE REL TABLE UsesBolt(FROM Product TO Bolt)",
    "CREATE REL TABLE UsesNut(FROM Product TO Nut)",
    "CREATE REL TABLE UsesResistor(FROM Product TO Resistor)",
    "CREATE REL TABLE UsesCapacitor(FROM Product TO Capacitor)",
+   "CREATE REL TABLE UsesWasher(FROM Product TO Washer)",                 # ← (2)
```

`Uses`가 종류마다 쪼개져 있으니, 노드 테이블을 하나 만들 때마다 관계 테이블도 반드시 짝으로 하나 더 생깁니다. 종류 N개면 테이블이 2N개로 선형 증가합니다.

### 고칠 곳 (3) 질의 — UNION 한 갈래 추가

```cypher
MATCH (p:Product {id:'P1'})-[:UsesBolt]->(x:Bolt)           RETURN x.name AS 부품
UNION
MATCH (p:Product {id:'P1'})-[:UsesNut]->(x:Nut)             RETURN x.name AS 부품
UNION
MATCH (p:Product {id:'P1'})-[:UsesResistor]->(x:Resistor)   RETURN x.name AS 부품
UNION
MATCH (p:Product {id:'P1'})-[:UsesCapacitor]->(x:Capacitor) RETURN x.name AS 부품
UNION                                                       -- ← (3)
MATCH (p:Product {id:'P1'})-[:UsesWasher]->(x:Washer)       RETURN x.name AS 부품
```

그리고 이건 「부품 전부」 질의 **하나**에서 끝나지 않습니다. `-[:Uses*1..3]->` 같은 3단계 전개, 「공급사 A가 납품한 부품이 들어간 제품」, 「리콜 사유가 과열인 제품에 공통으로 들어간 부품」 — 역량 질문 다섯 개 중 부품을 훑는 질의는 **전부** UNION 갈래를 하나씩 더 답니다. 고칠 곳 「3」은 질의를 한 개로 셌을 때의 최소치이고, 실제로는 `2 + (부품을 훑는 질의 수)` 입니다.

### 그리고 데이터는 그 다음에

```cypher
CREATE (:Washer {id:'W1', name:'M6 와셔'});
MATCH (p:Product{id:'P1'}), (x:Washer{id:'W1'}) CREATE (p)-[:UsesWasher]->(x);
```

즉 A안에서는 **스키마 세 곳을 고친 뒤에야 비로소 데이터를 넣을 수 있습니다.**

---

## 3. B안에서 「와셔」를 추가한다면 — 행 하나

스키마는 손대지 않습니다.

```python
FLAT_SCHEMA = [
    "CREATE NODE TABLE Part(id STRING, name STRING, category STRING, PRIMARY KEY(id))",
    "CREATE NODE TABLE Product(id STRING, PRIMARY KEY(id))",
    "CREATE REL TABLE Uses(FROM Product TO Part)",
]   # ← 변경 없음
```

```cypher
-- 이 한 줄이 전부다
CREATE (:Part {id:'W1', name:'M6 와셔', category:'체결'});
MATCH (p:Product{id:'P1'}), (x:Part{id:'W1'}) CREATE (p)-[:Uses]->(x);
```

질의도 그대로입니다.

```cypher
MATCH (p:Product {id:'P1'})-[:Uses]->(x:Part) RETURN x.name AS 부품
-- 와셔가 저절로 결과에 들어온다
```

핵심은 **부품 종류가 스키마(DDL)가 아니라 데이터(`category` 값)로 표현된다**는 점입니다. 데이터를 늘리는 일은 스키마 변경이 아닙니다.

---

## 4. 왜 이게 「고칠 곳 3개」로 안 끝나고 배포·마이그레이션 비용이 되는가

이 카드가 실무에서 아픈 이유는 세 곳의 성격이 서로 다르기 때문입니다. B안의 `CREATE (:Part …)`는 **런타임 DML**이고, A안의 세 곳은 **DDL 2 + 애플리케이션 코드 1**입니다.

### (가) DDL은 배포 사건이다

`CREATE NODE TABLE` / `CREATE REL TABLE` 은 마이그레이션 스크립트로 관리되어야 합니다. 그래서 와셔 하나를 추가하려면 대체로 이런 절차가 붙습니다.

```
migrations/
  001_init.cypher
  002_add_washer.cypher     ← 새로 작성 + 리뷰 + 롤백 스크립트
```

```cypher
-- 002_add_washer.cypher
CREATE NODE TABLE Washer(id STRING, name STRING, PRIMARY KEY(id));
CREATE REL TABLE UsesWasher(FROM Product TO Washer);
```

- 마이그레이션 리뷰·승인 절차를 탄다.
- 스테이징에서 먼저 돌려야 한다.
- 롤백 경로(`DROP TABLE`)를 함께 준비해야 한다. 그런데 `DROP`은 되돌릴 수 없으므로, 이미 적재된 와셔 데이터가 있으면 롤백이 사실상 불가능해진다.
- 엔진에 따라 DDL이 카탈로그 락을 잡거나 짧은 다운타임을 요구할 수 있다.

B안에서 같은 일은 그냥 `INSERT` 한 건입니다. 마이그레이션 파일도, 리뷰도, 롤백 스크립트도, 다운타임도 없습니다. 롤백은 `DELETE`면 끝입니다.

### (나) 질의 수정은 애플리케이션 배포다

세 번째 지점인 UNION은 데이터베이스가 아니라 **코드**에 들어 있습니다. 즉 DDL 배포와 **애플리케이션 배포가 순서를 맞춰야** 합니다.

```
1. 마이그레이션 배포 (Washer, UsesWasher 생성)
2. 애플리케이션 배포 (UNION 갈래 추가된 질의)
3. 데이터 적재
```

순서가 틀어지면 이렇게 됩니다.

- 2번을 먼저 하면 → `UsesWasher` 테이블이 없어 질의가 **에러**로 죽는다.
- 3번을 2번보다 먼저 하면 → 와셔 데이터는 들어와 있는데 **질의가 조용히 빠뜨린다**. 에러가 아니라 「결과가 덜 나온다」로 나타나서 아무도 모른다. 12장 예제 5의 「질의가 조용히 빈 결과를 내고 있을 가능성이 높다」와 정확히 같은 실패 양상이다.

무중단 배포라면 구버전과 신버전 인스턴스가 잠시 공존하므로, 이 창(window) 동안 구버전 인스턴스는 와셔를 못 보는 답을 계속 내놓습니다.

### (다) 질의를 고쳐야 할 곳을 사람이 기억해야 한다

A안에서 진짜 무서운 건 (1)(2)를 빼먹는 경우가 아니라 — 그건 에러로 즉시 드러납니다 — **(3)을 어딘가 한 군데 빼먹는 경우**입니다. 그 질의는 계속 정상 동작하는 것처럼 보이면서 와셔만 빠진 답을 냅니다. 종류가 늘수록 「UNION을 달아야 할 질의 목록」은 문서에만 존재하게 되고, 12장의 표현대로 **문서는 거짓말을 합니다.**

B안에는 애초에 그런 목록이 없습니다. 새 종류가 기존 질의에 **자동으로** 포함되기 때문입니다.

### (라) 그래서 비용이 어떻게 자라나

| | A안 | B안 |
|---|---|---|
| 종류 N개일 때 테이블 수 | 2N + 1 | 3 (고정) |
| 종류 하나 추가 | DDL 2 + 코드 N곳 + 배포 2회 | 행 1개 |
| 배포 필요 | 예 (DB + 앱, 순서 의존) | 아니오 |
| 롤백 | DROP TABLE, 데이터 있으면 사실상 불가 | DELETE |
| 빼먹었을 때 증상 | 조용히 결과 누락 | 해당 없음 |
| 새 종류 추가 주체 | 개발자 | 운영자/데이터 담당 |

마지막 줄이 조직적으로 제일 큽니다. A안에서 부품 종류 추가는 **개발 티켓**이지만, B안에서는 **데이터 입력**입니다. 214개 분류를 그대로 스키마로 옮겼다면 428개 테이블과, 종류가 하나 늘 때마다 도는 릴리스 사이클을 갖게 됩니다.

---

## 5. 그렇다고 A안이 무조건 나쁜 건 아니다

12장이 이 예제 끝에 붙인 단서를 같이 외워 두세요.

> 「볼트에만 있는 속성」(나사산 규격 같은 것)이 많고 그걸로 질의한다면 A안이 맞다.
> 분류를 나누는 기준은 **「다른 속성을 갖는가」**이지 **「다른 물건인가」**가 아니다.

B안으로 갔을 때 치르는 대가도 분명합니다.

- `Part`에 볼트 전용 컬럼(`thread_spec`)을 넣으면 저항 행에서는 항상 NULL이 된다. 종류별 전용 속성이 많아질수록 NULL 밭이 된다.
- 타입 시스템이 「제품은 볼트에만 연결된다」 같은 제약을 걸어 주지 못한다. 그 검사는 SHACL이나 별도 검증 배치로 밀려난다(12장 예제 3의 「적재 시점 vs 검증 시점」).
- `category` 값에 오타가 들어가도 엔진이 막지 않는다. Kuzu에는 CHECK 제약이 없어서 값의 범위를 스키마로 못 막는다는 점을 예제 3이 그대로 보여 준다.

판단 기준: **종류가 많거나 자주 늘면 속성으로, 종류별 고유 속성이 많고 그걸로 질의하면 클래스로.**

---

## 6. 한 줄 요약

A안에서 부품 종류 추가는 **노드 테이블 DDL + 관계 테이블 DDL + 질의 UNION** 세 곳을 고치는 스키마 변경이라 마이그레이션과 앱 배포를 순서 맞춰 태워야 하고, 빠뜨리면 조용히 결과가 누락된다. B안에서는 종류가 데이터(`category` 값)이므로 **행 하나 INSERT**로 끝나고 배포도 롤백도 필요 없다.
