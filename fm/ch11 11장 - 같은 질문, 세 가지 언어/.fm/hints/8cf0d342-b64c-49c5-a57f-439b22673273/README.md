# `seed.py`는 어떤 데이터를 어떻게 공유하는가?

## 한 줄 답

회사·계약·체결·해지·모회사 관계를 **파이썬 리스트**로 두고, **같은 사실을 Turtle 문자열(`TTL`)로도** 적어 둔다. 그래서 Cypher(Kuzu)·SPARQL(rdflib)·SQL 세 엔진에 **같은 데이터**를 넣을 수 있다.

`seed.py` 첫 줄의 독스트링이 목적을 그대로 말한다.

> `"""11장 공통 데이터. 같은 사실을 Cypher(Kuzu) · SPARQL(rdflib) · SQL 세 곳에 넣는다."""`

---

## 1. `seed.py`가 내보내는 것 — 6개의 이름

| 이름 | 모양 | 담은 사실 |
|---|---|---|
| `COMPANIES` | `[(이름, 등급), ...]` | 회사 4곳 (가온테크 A, 나루소프트 B, 라온에너지 C, 다올물산 B) |
| `CONTRACTS` | `[(계약id, 시작일, 종료일), ...]` | 계약 5건. 해지 계약은 `startedOn`이 `None`, 진행 계약은 `endedOn`이 `None` |
| `SIGNED` | `[(회사, 계약id), ...]` | 체결 관계 3건 |
| `TERMINATED` | `[(회사, 계약id), ...]` | 해지 관계 2건 |
| `PARENT_OF` | `[(모회사, 자회사), ...]` | 모회사 관계 2건 (가온테크 → 가온소프트 → 가온연구소) |
| `TTL` | 여러 줄 문자열 | **위 사실을 전부 다시** RDF Turtle 문법으로 적은 것 |

앞의 다섯은 **관계형/속성 그래프 쪽 표현**(튜플 = 행)이고, `TTL`은 **RDF 쪽 표현**(트리플)이다. 같은 회사·계약이 두 군데에 각각 한 번씩 적혀 있다.

---

## 2. 세 엔진이 각각 어떻게 먹는가

```
                   seed.py
        ┌─────────────┴──────────────┐
   COMPANIES/CONTRACTS/            TTL
   SIGNED/TERMINATED            (Turtle 문자열)
        │                            │
   ┌────┴─────┐                      │
   │          │                      │
CREATE 문   INSERT 문           Graph().parse()
   │          │                      │
 Kuzu       sqlite3               rdflib
(Cypher)     (SQL)               (SPARQL)
```

- **Cypher / Kuzu** (`ex1_three_languages.py`의 `build_kuzu()`): 리스트를 for 루프로 돌면서 f-string으로 `CREATE (:Company {name:'가온테크', grade:'A'})` 같은 문장을 만들어 실행한다. 노드 테이블·렐 테이블 스키마를 먼저 `CREATE NODE TABLE` / `CREATE REL TABLE`로 선언하는 게 특징이다(스키마 있는 속성 그래프).
- **SQL / sqlite3** (`ex4_sql_pgq.py`의 `setup()`): 같은 리스트를 `con.executemany("INSERT INTO company VALUES (?,?)", COMPANIES)`처럼 **파라미터 바인딩으로 그대로** 밀어 넣는다. 튜플 모양이 곧 행 모양이므로 변환이 거의 없다.
- **SPARQL / rdflib** (`ex1`, `ex2`): 리스트를 쓰지 않고 `Graph().parse(data=TTL, format="turtle")` 한 줄로 끝낸다. RDF 그래프는 트리플의 집합이라 스키마 선언 단계가 없다.
- **Gremlin 식 순회** (`ex1`의 `gremlin_style()`): 엔진 없이 파이썬 dict/list로 `CONTRACTS`, `SIGNED`, `TERMINATED`를 직접 걸어 다닌다. 이것도 리스트 쪽 표현을 쓴다.

즉 **리스트를 쓰는 소비자가 셋(Kuzu, sqlite3, Gremlin 흉내), TTL을 쓰는 소비자가 하나(rdflib)** 다.

---

## 3. 왜 굳이 두 표현을 이중으로 관리하나

RDF와 속성 그래프는 **데이터 모델 자체가 다르기 때문**이다.

- 속성 그래프: 노드에 라벨과 속성 딕셔너리가 붙는다. `(:Company {name:'가온테크', grade:'A'})` — 회사가 하나의 객체.
- RDF: 세상이 **트리플(주어–술어–목적어)** 하나뿐이다. 속성도 트리플, 관계도 트리플. `ex:Gaon ex:name "가온테크"`와 `ex:Gaon ex:signed ex:C2025118`이 문법적으로 같은 급이다.

그래서 파이썬 튜플에서 RDF로 가려면 **URI를 만들어 붙이는 작업**이 추가로 필요하다. `"M-2021-077"` 같은 문자열 id는 그냥 못 쓰고 `ex:M2021077`처럼 하이픈을 뺀 URI로 바꿔야 한다(하이픈은 Turtle 접두 이름에서 쓸 수는 있지만 위치 제약이 있어 피한 것). 또 날짜는 `"2024-03-11"^^xsd:date`처럼 데이터타입을 명시해야 SPARQL의 `FILTER(?end < ?start)`가 문자열이 아니라 **날짜로 비교**한다.

이 변환 코드를 짜는 대신, 책은 **손으로 적은 Turtle 문자열을 그냥 하나 더 둔다**는 선택을 했다. 예제 파일이 짧아야 읽히기 때문이다. 변환기를 붙이면 예제의 주제(세 언어의 문장 모양 비교)가 아니라 변환기가 주인공이 되어 버린다.

---

## 4. 그 위험 — 두 표현이 어긋날 수 있다

이중 관리의 대가는 명확하다. **한쪽만 고치면 조용히 어긋난다.** `seed.py`에는 이미 그 흔적이 있다.

1. **TTL에만 있는 회사가 있다.** `ex:GaonSoft`(가온소프트), `ex:GaonLab`(가온연구소)은 `TTL`에 `a ex:Company`로 들어 있지만 `COMPANIES` 리스트에는 없다. 모회사 사슬을 보여 주려고 TTL 쪽에만 추가한 것이다. 그래서 "회사가 몇 개냐"를 세면 SQL은 4, SPARQL은 6이 나온다.
2. **`PARENT_OF`는 실제로 쓰이지 않는다.** `ex2_path_queries.py`는 `from seed import TTL`만 가져오고, Cypher 쪽 모회사 데이터는 파일 안에 `CY_DATA` 리스트로 **또 한 번** 하드코딩해 놓았다. 같은 사실이 `seed.PARENT_OF`, `seed.TTL`, `ex2.CY_DATA` **세 곳**에 적혀 있는 셈이다. 하나를 고쳐도 나머지 둘은 모른다.
3. **`grade`가 TTL에만 빠진 곳이 있다.** `ex:GaonSoft`, `ex:GaonLab`에는 `ex:grade`가 없다. 등급을 세는 질의를 SPARQL로 쓰면 NULL 처리를 따로 해야 한다.

실무로 옮기면 이게 바로 3장의 **「두 벌 운영」** 비용이다. 같은 사실을 두 저장소에 각각 적어 두면, 어긋나는 순간 **어느 쪽이 진짜인지 판정할 근거가 없다.** 그래서 실제 시스템에서는 보통 이렇게 한다.

- **단일 진실 원본(single source of truth)을 하나만 정한다.** 여기서는 파이썬 리스트를 원본으로 삼고,
- **나머지 표현은 코드로 생성한다.** `COMPANIES` → Turtle을 뽑는 `to_ttl()` 함수를 두면 어긋날 수가 없다.
- 생성이 어렵다면 최소한 **일치 검사(assert)를 테스트로 남긴다.** "TTL에서 파싱한 회사 집합 == `set(COMPANIES)`" 같은 것.

`ex1`의 마지막이 `same = cypher_rows == sparql_rows == gremlin_rows`로 셋을 비교하고 "셋이 같은가"를 찍는 건, 사실상 이 일치 검사를 **최소한의 형태로** 넣어 둔 것이다.

---

## 5. 왜 '같은 데이터'가 비교 실험의 전제 조건인가

11장의 주장은 "**답은 같고 문장 모양이 다르다**"다. 이 문장의 앞 절반이 성립하지 않으면 뒤 절반은 의미가 없다.

- 데이터가 다르면 결과가 달라진다. 결과가 다르면 **차이의 원인이 언어인지 데이터인지 구분할 수 없다.** 「SPARQL이 한 행 더 나왔다」가 SPARQL의 성질인지 TTL에 회사 두 개를 더 넣어서인지 알 길이 없다.
- 데이터를 고정하면 남는 변수가 **문법과 사고 방식 하나뿐**이 된다. 그래서 세 표현을 나란히 놓는 게 의미를 가진다.
  - Cypher는 **그림**: `(c)-[:Signed]->(n)` — 화이트보드에 그린 모양.
  - SPARQL은 **문장**: `?c ex:signed ?n .` — 사실을 한 줄씩 늘어놓음.
  - Gremlin은 **걸음**: `.out('signed')` — 어디로 갈지 순서대로 지시.
- `ex1`의 질문 "해지했다가 그 뒤에 다시 계약한 고객은?"에 대해 **가온테크**만 답이 되는 것도 데이터가 그렇게 설계됐기 때문이다. 가온테크는 `M-2021-077`을 2024-03-11에 해지하고 `C-2025-118`을 2025-06-02에 체결했다. 라온에너지는 해지만 했고(체결 없음), 나루소프트·다올물산은 체결만 했다. 즉 **경계 사례를 일부러 섞어** 질의가 진짜로 조건을 거르는지 보이게 한 것이다.

정리하면 `seed.py`는 단순한 편의 모듈이 아니라 **실험의 통제 변수를 고정하는 장치**다. 그래서 이 파일이 흔들리면 11장 전체의 결론이 흔들린다.

---

## 6. Turtle 문법 빠르게 훑기

`TTL` 문자열을 읽을 때 필요한 요소만.

```turtle
@prefix ex:  <http://example.org/> .                     ← ① 접두사 선언
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:Gaon  a ex:Company ; ex:name "가온테크" ; ex:grade "A" ;
   ex:terminated ex:M2021077 ; ex:signed ex:C2025118 ;
   ex:parentOf ex:GaonSoft .                             ← ④ 마침표로 주어 끝

ex:M2021077 ex:endedOn "2024-03-11"^^xsd:date .          ← ⑤ 데이터타입
```

1. **접두사(`@prefix`)**: 긴 URI를 짧게 쓰는 별명. `ex:Gaon`은 실제로 `http://example.org/Gaon`이다. 질의문 쪽에서도 `PREFIX ex: <http://example.org/>`로 **같은 접두사를 다시 선언**해야 한다(데이터의 `@prefix`가 질의로 따라오지 않는다). 이게 `ex1`, `ex2`의 SPARQL 문자열 첫 줄에 `PREFIX`가 늘 붙어 있는 이유.
2. **주어–술어–목적어(트리플)**: `ex:Gaon ex:name "가온테크"` = "가온이라는 것의 이름은 가온테크다". 이 세 칸이 RDF의 유일한 문장 형식이다.
3. **세미콜론(`;`)**: **주어를 이어 쓴다.** 술어와 목적어만 새로 적으면 된다. `ex:Gaon a ex:Company ; ex:name "가온테크"`는 트리플 두 개(`ex:Gaon a ex:Company`, `ex:Gaon ex:name "가온테크"`)와 같다. 세미콜론이 없으면 매 줄 `ex:Gaon`을 반복해야 한다.
   - (참고: 쉼표 `,`는 **주어와 술어를 둘 다** 이어 쓴다. `seed.py`에는 안 쓰였다.)
4. **마침표(`.`)**: 한 주어에 대한 서술이 끝났다는 표시. 문장의 종결이다. 빠뜨리면 파싱 에러가 난다.
5. **`a`**: `rdf:type`의 약어. `ex:Gaon a ex:Company`는 "가온은 Company다" — 라벨/클래스 지정에 해당한다.
6. **`"값"^^xsd:date`**: 리터럴에 **데이터타입을 붙인다.** 이게 있어야 `FILTER(?end < ?start)`가 날짜 비교로 동작한다. 붙이지 않으면 문자열 비교가 되는데, ISO 8601 날짜는 문자열 정렬과 날짜 정렬이 우연히 일치해서 **버그가 숨는다.** 형식이 다른 날짜가 섞이는 순간 조용히 틀린 답이 나온다.

---

## 7. 외워 둘 포인트

- `seed.py`가 담은 것: **회사·계약·체결·해지·모회사** 다섯 종류의 사실.
- 표현이 **둘**: 파이썬 리스트(Kuzu·sqlite3·Gremlin 흉내용) + Turtle 문자열 `TTL`(rdflib용).
- 목적: **같은 데이터**를 세 엔진에 넣어, 결과가 아니라 **문장 모양**만 비교되게 만드는 것.
- 대가: 두 표현이 **어긋날 수 있다**(실제로 가온소프트·가온연구소가 TTL에만 있다). 실무라면 하나를 원본으로 두고 나머지를 생성하거나 일치 검사를 붙인다.

---

## 참고

- [SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/) — `PREFIX`, `FILTER`
- [RDF 1.1 Turtle](https://www.w3.org/TR/turtle/) — 접두사, 세미콜론/쉼표 축약, `a`, `^^` 데이터타입
- [Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)
- [ISO/IEC 9075-16:2023 (SQL/PGQ)](https://www.iso.org/standard/79473.html)
