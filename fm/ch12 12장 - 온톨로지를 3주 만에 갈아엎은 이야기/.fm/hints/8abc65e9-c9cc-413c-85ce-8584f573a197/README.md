# '부품'을 schema.org/Product로 쓰면 안 되는 이유

## 질문과 답

**질문**: '부품'을 schema.org/Product로 쓰면 안 되는 이유는 무엇인가?

**답**: 우리에게 부품은 '다른 제품 안에 들어가는 것'이고 판매 단위가 아니다. 뜻이 달라 적합도가 0.4에 그친다.

---

## 1. 어디서 나온 이야기인가

12장 4절 「남의 어휘를 가져다 쓸까」, 예제 `code/ex4_reuse_or_build.py`의 판단표입니다.

| 우리 개념 | 공개 어휘 후보 | 적합도 | 결론 |
|---|---|---|---|
| 제품 | `schema.org/Product` | 0.9 | 그대로 가져다 쓴다 |
| 공급사 | `schema.org/Organization` | 0.8 | 그대로 가져다 쓴다 |
| **부품** | **`schema.org/Product`** | **0.4** | **우리 것으로 만들고 매핑만 걸어 둔다** |
| 납품 | `schema.org/seller` | 0.5 | 우리 것으로 만들고 매핑만 걸어 둔다 |
| 리콜 | 없음 | 0.0 | 만든다 |
| 대체가능 | 없음 | 0.0 | 만든다 |

임계값은 `THRESHOLD = 0.7`. 0.7 이상이면 재사용, 미만이면 "우리 것 + 매핑".

여기서 재미있는 건 **'제품'과 '부품'이 같은 후보(`schema.org/Product`)를 놓고 서로 다른 판정을 받았다**는 점입니다. 같은 URI인데 하나는 0.9, 하나는 0.4예요. 후보가 같다고 적합도가 같지 않다는 게 이 예제의 요점입니다.

---

## 2. schema.org/Product의 실제 정의

schema.org 문서의 정의는 이렇습니다.

> **Product**: "Any offered product or service. For example: a pair of shoes; a concert ticket; the rental of a car; a haircut; or an episode of a TV show streamed online."
> (제공되는(offered) 모든 제품 또는 서비스. 예: 신발 한 켤레, 콘서트 티켓, 자동차 렌탈, 이발, 스트리밍되는 TV 에피소드 한 편)

핵심 낱말은 **offered**입니다. schema.org의 Product는 태생이 "전자상거래·검색엔진 리치 결과용 어휘"이고, 그 세계관에서 Product란 **누군가에게 값을 매겨 제공되는 단위**입니다. 예시가 티켓·렌탈·이발까지 포함하는 게 그 증거예요. "물리적 물건"이 기준이 아니라 "거래 단위"가 기준입니다.

우리 정의는 다릅니다. `questions.py`의 역량 질문 다섯 개를 보면 부품이 이렇게 쓰입니다.

```text
"부품 X 를 쓴 제품 중 리콜된 것은?"
"공급사 A 가 납품한 부품이 들어간 제품은?"
"리콜 사유가 «과열»인 제품에 공통으로 들어간 부품은?"
"부품 X 의 대체 부품은 무엇이고, 언제부터 대체 가능한가?"
"제품 P 의 부품 목록을 3단계까지 펼치면?"
```

전부 **"들어간다 / 쓴다 / 펼친다"**입니다. 사고 파는 얘기가 한 줄도 없어요. 우리 부품은 **구성(composition)의 단위**이지 **거래(commerce)의 단위**가 아닙니다. 이 축이 어긋나 있는 게 적합도 0.4의 정체입니다.

---

## 3. 속성이 따라 들어온다 — "부품인데 왜 가격이 있지"

클래스를 빌려 쓰면 그 클래스에 딸린 속성이 통째로 따라옵니다. 여기서 혼란이 시작돼요. `schema.org/Product`의 주요 속성을 우리 부품에 얹어 보면:

| 속성 | schema.org 정의 | 부품에 붙었을 때 |
|---|---|---|
| `offers` | "An offer to provide this item — for example, an offer to sell a product, rent the DVD of a movie, perform a service…" | **M6 볼트의 판매 오퍼가 뭐지?** 우리는 볼트를 팔지 않는다. 사 오기만 한다. 값이 늘 비어 있는데 스키마상으로는 채워도 되는 칸이 된다 |
| `price` / `priceCurrency` (`offers` → `Offer`) | 오퍼에 붙는 가격과 통화 | **"부품인데 왜 가격이 있지"** — 예제 4가 직접 지목한 그 혼란. 조달 단가인가, 판매가인가, 개당인가 로트당인가. 아무도 정의한 적 없는데 칸만 열려 있다 |
| `sku` | "The Stock Keeping Unit (SKU), i.e. a **merchant-specific** identifier for a product or service" | 상인(merchant) 기준 재고 관리 코드다. 우리 부품 ID는 사내 BOM 식별자이지 판매 재고 코드가 아니다. 뜻이 다른 두 식별자가 같은 칸에 섞여 들어간다 |
| `gtin` / `gtin13` | 국제 거래 단품 식별 번호 | 애초에 유통되지 않는 사내 가공 부품에는 존재하지 않는다. 그런데 "빈 칸이니 뭐라도 넣자"는 압력이 생긴다 |
| `brand` | 제품에 붙은 브랜드 | 공급사와 브랜드가 헷갈린다. 우리는 이미 `공급사`(Organization)와 `납품` 관계로 이걸 표현하기로 했다. 표현 경로가 둘이 되면 질의가 둘 다 봐야 한다 |
| `review` / `aggregateRating` | 소비자 리뷰와 집계 평점 | 볼트에 별점 4.3이 붙는다. 무의미할 뿐 아니라, 리콜 판단을 평점으로 하려는 사람이 언젠가 나온다 |
| `isSimilarTo` | "A pointer to another, **functionally similar** product" | 가장 위험한 유혹. 우리의 `대체가능하다`와 비슷해 보이지만 **"언제부터 대체 가능한가"(유효시작일)를 담을 자리가 없다**. 역량 질문 4번이 그걸 묻는데 답을 못 한다 |
| `isAccessoryOrSparePartFor` | "A pointer to another product for which this product is an **accessory or spare part**" | 이름만 보면 딱 맞는 것 같지만, 여기서 spare part도 **따로 팔리는 수리용 부품**이다. 조립 시점에 안에 들어가는 구성 부품과 다르다. 그리고 이 속성 역시 양쪽이 Product인 걸 전제한다 |
| `isConsumableFor` / `isRelatedTo` | 소모품 관계 / 관련 상품 | "관련"의 뜻이 우리 도메인에 정의된 적이 없다. 나중에 아무거나 담기는 쓰레기통 속성이 된다 |

정리하면 혼란은 세 갈래로 옵니다.

1. **채울 수 없는 칸**(offers, gtin) — 늘 비어 있는데 스키마는 허용한다. 신입이 "왜 비어 있죠?"라고 묻는다.
2. **잘못 채워지는 칸**(sku, brand, price) — 뜻이 다른 값이 그럴듯하게 들어가고, 아무도 틀렸다고 말해 주지 않는다.
3. **거의 맞아서 더 위험한 칸**(isSimilarTo, isAccessoryOrSparePartFor) — 우리 개념의 80%만 담고 나머지 20%(유효시작일)를 조용히 잘라 먹는다.

예제 4의 표현으로는 이게 **"억지로 맞춰 쓴다 → 나중에 «부품인데 왜 가격이 있지» 같은 혼란이 생긴다"**, 즉 실수 (가)입니다. 억지로 맞춰 쓰면 **예외 조항이 쌓입니다.** "Product인데 부품일 때는 offers를 무시하세요", "sku는 부품일 때만 사내 코드입니다" 같은 문서가 늘어나고, 그 문서는 12장 5절이 말하듯 곧 거짓말을 하기 시작합니다.

### 반대쪽 실수도 있다

> (나) 아예 무시하고 다 새로 만든다 → 밖과 데이터를 주고받을 때 매번 변환한다

공개 어휘를 통째로 버리면 외부 카탈로그를 받아올 때마다 손으로 짠 변환 코드를 태워야 합니다. 그러니 답은 양극단이 아니라 중간입니다.

---

## 4. 그럼 어떻게 하나 — 우리 어휘 + 매핑

예제 4의 결론:

> 중간이 답이다. 우리 것으로 만들되, 공개 어휘와 «대략 같음»을 걸어 둔다.
> RDF 라면 owl:sameAs 나 skos:closeMatch, LPG 라면 속성으로 매핑 표를 둔다.

### RDF에서

```turtle
@prefix ex:   <http://example.org/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sdo:  <https://schema.org/> .

# 제품 — 적합도 0.9. 그냥 가져다 쓴다
ex:Product rdfs:subClassOf sdo:Product .

# 부품 — 적합도 0.4. 우리 클래스로 세우고 «대략 같음»만 건다
ex:Part a rdfs:Class ;
    rdfs:label "부품"@ko ;
    rdfs:comment "다른 제품 안에 들어가는 구성 단위. 판매 단위가 아니다."@ko ;
    skos:closeMatch sdo:Product .
```

**왜 `skos:closeMatch`이고 `owl:sameAs`나 `skos:exactMatch`가 아닌가.** SKOS 명세가 이 둘을 구분해 둔 이유가 정확히 여기에 있습니다.

| 매핑 술어 | 의미 | 이행성(transitive) | 부품 사례 |
|---|---|---|---|
| `skos:exactMatch` | "폭넓은 정보 검색 응용에서 서로 바꿔 써도 된다" | **있다** | 위험. 이행 추론이 체인으로 번진다 |
| `skos:closeMatch` | "일부 정보 검색 응용에서 쓸 만큼 충분히 비슷하다" | **없다**(의도적으로 배제) | **적절** |
| `owl:sameAs` | 두 URI가 **같은 개체**라고 단언 | 있다 | 절대 금물 |

`skos:closeMatch`는 대칭이지만 **이행적이지 않도록 일부러 선언되어 있습니다**. 명세는 그 이유를 여러 체계의 매핑을 이어 붙일 때 생기는 "compound errors"(누적 오류)를 막기 위해서라고 밝힙니다. 즉 `ex:Part closeMatch sdo:Product`와 `sdo:Product closeMatch 남의어휘:Article`이 있어도 `ex:Part`가 `남의어휘:Article`이 되지 않아요. 적합도 0.4짜리 느슨한 연결에 정확히 필요한 성질입니다.

반면 `owl:sameAs`를 쓰면 추론기가 **`sdo:Product`의 모든 속성을 우리 부품 인스턴스에 그대로 상속시킵니다.** 3절에서 본 offers, price, sku가 전부 합법적인 서술이 되고, 우리는 아무것도 막지 못한 채 다시 실수 (가)로 돌아갑니다. 예제 4 본문이 `owl:sameAs`를 언급하긴 하지만, 적합도 0.4에 실제로 어울리는 건 `skos:closeMatch` 쪽입니다. 굳이 방향까지 표현하고 싶다면 `skos:broadMatch`(우리 부품보다 schema.org Product가 더 넓다)가 후보이고, 이것도 이행적인 `skos:broader`의 하위 속성이라 신중해야 합니다.

### LPG(Kuzu/Neo4j)에서

LPG에는 이런 매핑 술어가 없으니 **속성이나 별도 매핑 표**로 둡니다.

```cypher
CREATE NODE TABLE Part(
  id STRING, name STRING, category STRING,
  PRIMARY KEY(id)
);
CREATE NODE TABLE VocabMap(
  local_term STRING, external_iri STRING, relation STRING, fit DOUBLE,
  PRIMARY KEY(local_term)
);
```

```text
local_term  external_iri                  relation    fit
부품        https://schema.org/Product    closeMatch  0.4
제품        https://schema.org/Product    subClassOf  0.9
공급사      https://schema.org/Organization subClassOf 0.8
납품        https://schema.org/seller     closeMatch  0.5
```

매핑을 데이터로 두면 12장 5절의 드리프트 감사(`ex5_schema_drift.py`)처럼 **배치로 검사할 수 있습니다.** 문서에만 적어 두면 6개월 뒤에 거짓말이 됩니다.

---

## 5. 관계는 재사용할 수 있나 — isPartOf / hasPart

"클래스는 못 빌려도 관계는 빌릴 수 있지 않나" 하는 생각이 자연스럽게 듭니다. `schema.org/isPartOf`와 그 역인 `hasPart`가 후보예요. 결론부터 말하면 **여기서도 안 맞습니다.**

- `isPartOf`의 정의: "indicates an item or CreativeWork that this item, or CreativeWork (in some sense), is part of."
- 사용되는 타입(domain): **CreativeWork** 계열. `Product`는 들어 있지 않습니다.
- 값의 타입(range): CreativeWork 또는 URL.

즉 `isPartOf`/`hasPart`는 schema.org 안에서 **저작물의 부분-전체 관계**(챕터가 책의 일부, 에피소드가 시즌의 일부)로 자리 잡은 속성입니다. 물리적 제품의 BOM 전개를 위해 만들어진 게 아니에요. 여기에 볼트를 끼워 넣으면 클래스에서 저지른 실수를 관계에서 반복하는 셈입니다.

그래서 12장의 선택은 **우리 관계를 그대로 쓰는 것**입니다. `questions.py`에서 뽑은 관계 어휘는 네 개뿐이었습니다.

```text
관계: 사용한다, 납품한다, 리콜되었다, 대체가능하다
```

`ex2_deep_vs_flat.py`의 B안이 이걸 그대로 구현합니다.

```cypher
CREATE NODE TABLE Part(id STRING, name STRING, category STRING, PRIMARY KEY(id));
CREATE NODE TABLE Product(id STRING, PRIMARY KEY(id));
CREATE REL TABLE Uses(FROM Product TO Part);
```

`Uses` 하나면 "제품 P1이 쓰는 부품 전부"가 한 줄로 끝납니다. `Product`와 `Part`를 **다른 클래스로 나눈 것 자체가** 이 관계를 깔끔하게 만들어 줍니다. 만약 둘 다 `schema.org/Product`로 뭉뚱그렸다면 `Uses`의 출발과 도착이 같은 타입이 되고, "이 Product는 완제품인가 부품인가"를 구분하는 플래그 속성이 하나 더 필요해집니다. 그 플래그가 바로 예외 조항의 씨앗이에요.

정리하면 재사용 여부는 이렇게 갈립니다.

| 대상 | 재사용? | 이유 |
|---|---|---|
| `schema.org/Product` ← 제품 | O (subClassOf) | 적합도 0.9. 판매 단위라는 뜻이 우리와 맞는다 |
| `schema.org/Organization` ← 공급사 | O (subClassOf) | 적합도 0.8 |
| `schema.org/Product` ← 부품 | X (closeMatch만) | 적합도 0.4. 구성 단위 vs 거래 단위 |
| `schema.org/isPartOf`·`hasPart` | X | domain이 CreativeWork. 제품 BOM용이 아니다 |
| `schema.org/isSimilarTo` ← 대체가능 | X | 유효시작일을 담을 자리가 없다 |
| `schema.org/seller` ← 납품 | X (매핑만) | 적합도 0.5 |

---

## 6. 한 줄 판단 기준

> 판단 기준 한 줄: 적합도 0.7 을 넘으면 가져다 쓰고, 아니면 만들고 이어 둔다.
> 0.7 은 제 감이다. 중요한 건 «숫자를 정해 두고 매번 같은 기준으로 판단하는 것»이다.

0.7이라는 숫자 자체가 근거가 있는 건 아닙니다. 요점은 **매번 같은 기준으로 판단한다**는 것이고, 그 판단을 개인의 취향이 아니라 팀이 합의한 숫자에 맡긴다는 것입니다. 부품이 0.4라는 것도 정밀한 측정이 아니라, "핵심 속성 열 개 중 네 개쯤만 우리 뜻에 맞는다"는 감각의 기록이에요. 기록해 두었기 때문에 반년 뒤에 "왜 부품은 Product를 안 썼죠?"라는 질문에 답할 수 있습니다.

---

## 7. 시험에 나올 만한 포인트

- **핵심 이유 한 문장**: schema.org/Product는 "offered", 즉 **제공/판매되는 단위**를 뜻하는데, 우리 부품은 **다른 제품 안에 들어가는 구성 단위**여서 뜻이 다르다.
- **적합도 숫자**: 부품 = **0.4**, 임계값 = **0.7**. 같은 후보를 놓고 제품은 0.9로 재사용, 부품은 0.4로 탈락.
- **구체적 혼란의 예**: "부품인데 왜 가격이 있지" — `offers` → `Offer` → `price`가 딸려 온다. `sku`(merchant-specific), `gtin`, `review`/`aggregateRating`도 마찬가지.
- **두 가지 실수**: (가) 억지로 맞춰 쓴다 → 예외 조항이 쌓인다 / (나) 다 새로 만든다 → 외부 교환 때마다 변환한다.
- **답**: 우리 어휘로 만들고 `skos:closeMatch`(비이행적)로 이어 둔다. `owl:sameAs`나 `skos:exactMatch`는 속성을 통째로 상속시켜 (가)로 되돌아간다.
- **관계 재사용**: `isPartOf`/`hasPart`는 domain이 CreativeWork이라 제품 BOM에 부적합. 우리 `Uses` 관계를 쓴다.

---

## 참고 문헌

- schema.org — [Product](https://schema.org/Product), [offers](https://schema.org/offers), [sku](https://schema.org/sku), [isSimilarTo](https://schema.org/isSimilarTo), [isAccessoryOrSparePartFor](https://schema.org/isAccessoryOrSparePartFor), [isPartOf](https://schema.org/isPartOf)
- W3C — [SKOS Simple Knowledge Organization System Reference](https://www.w3.org/TR/skos-reference/) (§10 Mapping Properties)
- 12장 예제 — `code/ex4_reuse_or_build.py`, `code/ex2_deep_vs_flat.py`, `code/questions.py`
