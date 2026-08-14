# 고아 계약 노드를 SHACL로 잡기 — `sh:inversePath` + `sh:minCount`

## 질문

고아 계약 노드를 SHACL로 어떻게 잡는가?

## 답

`sh:path [ sh:inversePath ex:signed ]`에 `sh:minCount 1`을 걸어, 자신을 체결한 회사가 하나도 없으면 Violation으로 잡는다.

```turtle
ex:ContractShape a sh:NodeShape ;
    sh:targetClass ex:Contract ;

    # 차단 — 계약인데 회사가 없으면 고아 노드다
    sh:property [
        sh:path [ sh:inversePath ex:signed ] ;
        sh:minCount 1 ;
        sh:severity sh:Violation ;
        sh:message "이 계약을 체결한 회사가 없다 (고아 노드)" ] .
```

---

## 1. 문제 상황: `data.ttl`의 `ex:C9`

13장 예제 데이터에는 계약 노드가 여러 개 있는데, 대부분은 이런 모양입니다.

```turtle
ex:Gaon a ex:Company ; rdfs:label "가온테크" ;
    ex:bizNumber "123-45-67890" ; ex:grade "A" ; ex:signed ex:C1 .
ex:C1 a ex:Contract ; ex:amount 5000000 .
```

`ex:Gaon --ex:signed--> ex:C1` 이라는 엣지가 있으니, `ex:C1`은 「누가 체결했는지」 추적이 됩니다.

그런데 딱 하나, 이런 노드가 섞여 있습니다.

```turtle
# 차단 — 아무도 체결하지 않은 계약. 고아 노드.
ex:C9 a ex:Contract ; ex:amount 990000 .
```

`ex:C9`는 **자기 자신만 보면 아무 문제가 없습니다.**

- 타입도 있고 (`a ex:Contract`)
- 금액도 있고 (`ex:amount 990000`) — 게다가 양수라 `sh:minInclusive 0`도 통과합니다.

문제는 「이 노드를 가리키는 화살표가 하나도 없다」는 점입니다. 그래프 전체를 놓고 봤을 때 `ex:C9`는 어디에도 매달려 있지 않은 **고아 노드(orphan node)** 입니다. 계약 99만 원이 장부에 떠 있는데 누가 맺은 계약인지 아무도 모르는 상태예요. 그래서 13장은 이걸 「경고」가 아니라 **차단(`sh:Violation`)** 으로 분류합니다.

---

## 2. 왜 정방향 경로로는 못 잡는가

여기가 이 카드의 핵심입니다.

SHACL의 `sh:property` 제약은 **포커스 노드(focus node)에서 출발하는 경로**를 평가합니다. `sh:path ex:amount`라고 쓰면, 검증기는 포커스 노드가 주어(subject)인 트리플 `?focus ex:amount ?value`를 찾아 값 집합을 만들고, 그 집합에 `sh:minCount`, `sh:datatype` 같은 제약을 적용합니다.

즉 정방향 경로는 **노드가 자기 손으로 들고 있는 속성**만 볼 수 있습니다.

그런데 「고아다」라는 사실은 노드 자신의 속성이 아닙니다.

- `ex:C9`에는 "나는 아무에게도 체결되지 않았다"를 뜻하는 트리플이 **존재하지 않습니다.**
- 애초에 「들어오는 엣지가 없다」는 건 **부재(absence)** 이고, RDF에서 부재는 트리플로 표현되지 않습니다. 없는 건 그냥 없어요.
- `ex:signed` 트리플의 주어는 회사(`ex:Gaon`)이고 목적어가 계약(`ex:C1`)입니다. 계약 쪽에는 그 관계가 아무것도 안 적혀 있습니다.

그래서 `ex:ContractShape` 안에서 `sh:path ex:signed ; sh:minCount 1`이라고 쓰면 완전히 엉뚱한 검사가 됩니다. 그건 「계약이 무언가를 체결했는가」를 묻는 것이고, `ex:C1`을 포함한 **모든 계약이 전부 위반**으로 잡힙니다. 방향이 반대이기 때문입니다.

반대로 `ex:CompanyShape`에 `sh:path ex:signed ; sh:minCount 1`을 거는 건 의미가 있지만(회사는 계약을 하나 이상 가져야 한다), 그건 「계약 없는 회사」를 잡는 규칙이지 「회사 없는 계약」을 잡는 규칙이 아닙니다. 회사 쪽을 아무리 검사해도, 어떤 회사도 가리키지 않는 `ex:C9`는 시야에 들어오지 않습니다. **아무도 언급하지 않은 노드는 아무 회사의 검사에도 걸리지 않으니까요.**

그러니 필요한 건 「이 노드로 **들어오는** `ex:signed` 엣지를 세는」 방법입니다.

---

## 3. SHACL Property Path와 `sh:inversePath`

SHACL의 `sh:path`는 단순 프로퍼티 IRI 하나만 받는 게 아니라, SPARQL 1.1 프로퍼티 경로에 대응하는 **경로 표현식**을 받습니다. 대표적인 것들:

| 경로 종류 | 표기 | 뜻 |
|---|---|---|
| Predicate path | `sh:path ex:signed` | 정방향 한 칸 |
| Inverse path | `sh:path [ sh:inversePath ex:signed ]` | **역방향** 한 칸 |
| Sequence path | `sh:path ( ex:a ex:b )` | 이어서 두 칸 |
| Alternative path | `sh:path [ sh:alternativePath ( ex:a ex:b ) ]` | 둘 중 아무거나 |
| Zero-or-more | `sh:path [ sh:zeroOrMorePath ex:parent ]` | 0회 이상 반복 |
| One-or-more | `sh:path [ sh:oneOrMorePath ex:parent ]` | 1회 이상 반복 |

`sh:inversePath`는 SPARQL의 `^ex:signed`와 같습니다. 포커스 노드가 **목적어(object)** 인 트리플을 찾아, 그 **주어들**을 값 집합으로 만듭니다.

```
정방향  sh:path ex:signed          →  { o | (focus, ex:signed, o) }
역방향  sh:path [ sh:inversePath ex:signed ]  →  { s | (s, ex:signed, focus) }
```

값 집합이 만들어지고 나면, 그 뒤의 제약(`sh:minCount`, `sh:class`, `sh:severity` …)은 정방향일 때와 **똑같이** 적용됩니다. 경로만 뒤집었을 뿐, 나머지 문법은 그대로예요. 이게 SHACL 설계의 깔끔한 지점입니다.

참고로 `sh:inversePath`의 값은 blank node 안에 쓰며, 값은 IRI 하나 또는 또 다른 경로 표현식입니다.

---

## 4. 규칙이 실제로 도는 과정

```turtle
ex:ContractShape a sh:NodeShape ;
    sh:targetClass ex:Contract ;
    sh:property [
        sh:path [ sh:inversePath ex:signed ] ;
        sh:minCount 1 ;
        sh:severity sh:Violation ;
        sh:message "이 계약을 체결한 회사가 없다 (고아 노드)" ] .
```

1. **타깃 선정** — `sh:targetClass ex:Contract`이므로 포커스 노드는 `ex:C1`, `ex:C2`, `ex:C3`, `ex:C4`, `ex:C5`, `ex:C9`.
2. **경로 평가** — 각 포커스 노드에 대해 `{ s | (s, ex:signed, focus) }`를 계산.
   - `ex:C1` → `{ ex:Gaon }`, 크기 1
   - `ex:C2` → `{ ex:Naru }`, 크기 1
   - …
   - `ex:C9` → `{ }`, **크기 0**
3. **`sh:minCount 1` 적용** — 값 집합 크기가 1 미만인 포커스 노드는 위반.
4. **결과** — `ex:C9` 하나만 걸리고, `sh:severity sh:Violation` + `sh:message`가 붙은 validation result가 리포트에 들어갑니다.

`ex1_shacl_severity.py`를 돌리면 이 결과가 `차단` 등급 줄로 출력됩니다 (`ex:C9` — "이 계약을 체결한 회사가 없다 (고아 노드)"). `ex:Naru`의 사업자번호 형식 오류와 함께 차단 2건이 나오는 구성이에요.

**핵심 뒤집기**: 「들어오는 엣지가 없다」는 표현할 수 없는 사실이지만, 「들어오는 엣지를 모은 집합의 크기가 0이다」는 표현할 수 있습니다. `sh:inversePath`가 부재를 **셀 수 있는 값 집합**으로 바꿔 주고, `sh:minCount`가 그 크기에 하한을 겁니다.

---

## 5. 함께 기억할 것들

**심각도 선택** — 13장의 차단 기준은 「되돌릴 수 없는가」 하나입니다. 소유자를 알 수 없는 계약이 그대로 적재되면 나중에 누구 것인지 복원할 수 없으니 `sh:Violation`입니다. 반면 `ex:amount -1`(마루상사의 `ex:C5`)은 집계를 틀리게 만들지만 원천에서 다시 읽어 고칠 수 있으니 `sh:Warning`이에요.

**전부 막으면 안 된다** — 이 장의 다른 축은 「전부 차단하면 데이터가 안 들어오고, 사람들이 검증을 우회한다」입니다. 고아 노드를 차단으로 둔 건 판단의 결과이지 기본값이 아닙니다. 도메인에 따라 「아직 회사가 붙지 않은 임시 계약」이 정상 상태라면 이 규칙은 `sh:Warning`이거나, 아예 상태 플래그로 타깃을 좁혀야 합니다.

**OWL로 쓰면 반대로 동작한다** — 같은 「반드시 하나 있어야 한다」를 OWL 카디널리티로 선언하면, 추론기는 위반이라고 적지 않고 **「그럼 어딘가에 있겠지」 하고 익명 개체를 만들어 냅니다**(open world assumption). 품질 검사에 추론기를 쓰면 안 되는 이유이고, `ex2_infer_vs_validate.py`가 보여 주는 대목입니다.

**SHACL 만능이 아니다** — 13.3절이 말하듯 슈퍼 노드, 사이클, 중복 의심, 다중 소속 같은 스멜은 형태 제약으로 못 잡습니다. 고아 노드는 「종류가 많아 일일이 못 쓴다」는 단서가 붙긴 하지만 형태 제약으로 잡히는 축에 속합니다. 다만 여기서 잡히는 건 **`ex:Contract` 타입에 대해 `ex:signed`의 부재**뿐입니다. 다른 클래스, 다른 관계의 고아를 잡으려면 그만큼의 shape을 또 써야 하고, 그래서 실무에서는 「엣지가 하나도 없는 노드」 같은 범용 스멜은 SHACL 대신 `ex3_graph_smells.py`처럼 세는 스크립트로 뽑아 사람이 보게 합니다.

---

## 원-라이너로 외우기

> 「들어오는 엣지가 없다」는 노드에 안 적혀 있다 → `sh:inversePath`로 화살표를 뒤집어 들어오는 걸 집합으로 만들고 → `sh:minCount 1`로 그 집합이 비었는지 센다.

## 참고

- [SHACL — Property Paths](https://www.w3.org/TR/shacl/#property-paths)
- [SHACL — sh:inversePath](https://www.w3.org/TR/shacl/#property-path-inverse)
- [SHACL — sh:minCount](https://www.w3.org/TR/shacl/#MinCountConstraintComponent)
- [SHACL — sh:severity](https://www.w3.org/TR/shacl/#severity)
