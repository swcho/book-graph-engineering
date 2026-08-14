# 사이클 스멜을 SHACL로 잡을 수 없는 이유

**질문** 사이클 스멜을 SHACL로 잡을 수 없는 이유는 무엇인가?

**답** SHACL에 「순환 없음」 제약이 없다. 예제에서는 REPLACES 관계의 순환을 DFS로 직접 찾는다.

---

## 1. 먼저, 어떤 상황인가

`ex3_graph_smells.py`가 만드는 데이터에는 이런 세 줄이 있습니다.

```python
("n3", "REPLACES", "n4"), ("n4", "REPLACES", "n5"),
("n5", "REPLACES", "n3"),                            # 사이클
```

`REPLACES`는 「이 부품이 저 부품을 대체한다」는 뜻입니다. n3이 n4를 대체하고, n4가 n5를 대체하고, n5가 다시 n3을 대체합니다. 원이 닫혔습니다.

여기서 핵심은 **어느 트리플 하나도 그 자체로는 잘못되지 않았다**는 점입니다.

- `n3 REPLACES n4` — 정상. 2024년에 설계팀이 넣었습니다.
- `n4 REPLACES n5` — 정상. 2025년에 구매팀이 넣었습니다.
- `n5 REPLACES n3` — 정상. 2026년에 다른 사람이 「n3이 단종돼서 옛날 n5로 롤백」이라고 넣었습니다.

세 개를 다 모아 놓고 봐야 문제가 보입니다. 이게 이 장에서 말하는 **그래프 스멜**의 정의입니다. 스키마로는 못 잡고 「세어 봐야」 보이는 것.

---

## 2. SHACL이 볼 수 있는 범위 — 초점 노드의 이웃

SHACL 검증은 이렇게 돌아갑니다.

1. `sh:target*`으로 **초점 노드(focus node)** 집합을 고른다.
2. 초점 노드마다 `sh:path`를 따라가 **값 노드(value nodes)** 집합을 만든다.
3. 그 값 노드 집합을 제약 컴포넌트로 검사한다.

즉 SHACL Core의 검사 단위는 **「초점 노드 하나 + 그 노드에서 경로로 닿는 값들」이라는 국소(local) 관점**입니다.

그런데 사이클은 국소 속성이 아닙니다. **전역(global) 속성**이에요. n3만 놓고 봐서는 알 수 없고, n3 → n4 → n5 → n3으로 되돌아왔다는 사실, 즉 **출발점과 도착점이 같다**는 비교가 필요합니다. 이 「출발점과 같은가」를 표현할 수단이 SHACL Core에는 없습니다.

> 같은 이유로 **슈퍼 노드**도 SHACL로 못 잡습니다. 「평균 차수의 5배」는 그래프 전체를 세어야 나오는 상대값이라서요. 사이클과 슈퍼 노드는 「SHACL의 시야가 국소적이다」라는 하나의 원인에서 갈라져 나온 두 증상입니다.

---

## 3. SHACL Core 제약 컴포넌트에 「순환 없음」이 없다

SHACL 명세(W3C Recommendation, 2017)의 Core 제약 컴포넌트는 딱 28개입니다.

| 분류 | 컴포넌트 |
|---|---|
| 값 타입 | `sh:class` `sh:datatype` `sh:nodeKind` |
| 개수 | `sh:minCount` `sh:maxCount` |
| 값 범위 | `sh:minExclusive` `sh:minInclusive` `sh:maxExclusive` `sh:maxInclusive` |
| 문자열 | `sh:minLength` `sh:maxLength` `sh:pattern` `sh:languageIn` `sh:uniqueLang` |
| 속성 쌍 | `sh:equals` `sh:disjoint` `sh:lessThan` `sh:lessThanOrEquals` |
| 논리 | `sh:not` `sh:and` `sh:or` `sh:xone` |
| 형태 기반 | `sh:node` `sh:property` `sh:qualifiedValueShape` |
| 기타 | `sh:closed` `sh:hasValue` `sh:in` |

**`sh:acyclic` 같은 건 없습니다.** 목록 끝입니다. 명세는 오히려 3.4.3절에서 「재귀적 형태(recursive shapes)를 이용한 검증은 정의되어 있지 않으며(not defined) 구현에 맡긴다」고 못 박습니다. 순환을 잡기는커녕, 형태 정의 자체가 순환하면 명세 밖으로 나갑니다.

### 3.1 「경로는 무한히 갈 수 있는데, 비교할 대상이 없다」

여기서 흔한 오해가 하나 나옵니다. **SHACL 경로에는 전이 폐포(transitive closure)가 있습니다.**

```turtle
sh:path [ sh:oneOrMorePath ex:replaces ]   # ex:replaces+ 와 같다
sh:path [ sh:zeroOrMorePath ex:replaces ]  # ex:replaces* 와 같다 (자기 자신 포함)
```

SHACL 경로 문법은 SPARQL 1.1 프로퍼티 경로의 부분집합입니다. `sh:inversePath`, `sh:alternativePath`, `sh:sequencePath`, `sh:zeroOrOnePath`, `sh:zeroOrMorePath`, `sh:oneOrMorePath`가 다 있습니다. 그래서 **「n3에서 REPLACES를 몇 번이든 타고 닿는 모든 노드」라는 값 집합은 만들 수 있습니다.**

문제는 그 다음입니다. 그 집합 안에 **n3 자신이 들어 있는지**를 물어볼 제약 컴포넌트가 없습니다.

- `sh:hasValue` — **상수 하나**만 받습니다. `sh:hasValue ex:n3`처럼 특정 노드는 쓸 수 있지만, 「초점 노드 자신」을 가리키는 변수가 Core에 없습니다. 노드 4만 개짜리 그래프에 형태 4만 개를 손으로 쓸 수는 없죠.
- `sh:disjoint` / `sh:equals` — 두 값 집합을 비교하니 될 것 같지만, 명세상 **이 파라미터의 값은 IRI(술어) 하나**입니다. 경로를 넣을 수 없습니다. 「`ex:replaces+`의 결과」와 「자기 자신」을 비교하는 식으로는 못 씁니다.
- `sh:node` / `sh:property` 로 중첩 — 중첩된 형태 안에서는 **초점 노드가 값 노드로 옮겨갑니다**. `$this`가 바뀌어 버려서, 원래 출발점을 기억할 방법이 사라집니다. 이게 「국소적」이라는 말의 기술적 실체입니다.

한마디로: **경로로 「어디까지 갈 수 있나」는 물을 수 있지만, 「거기서 원점으로 돌아왔나」는 물을 수 없습니다.**

### 3.2 길이 1짜리 자기 루프조차 못 잡는다

`n3 REPLACES n3` — 자기가 자기를 대체한다. 가장 단순한 사이클입니다. 이것도 SHACL Core로는 못 잡습니다. 위와 같은 이유예요. 「값 노드 중에 초점 노드가 있으면 안 된다」를 쓸 컴포넌트가 없습니다.

`sh:maxCount 1`을 걸어도 소용없습니다. 모든 노드의 REPLACES 출차수가 1이어도 사이클은 얼마든지 존재할 수 있습니다(예제의 n3→n4→n5→n3이 정확히 그 경우입니다).

### 3.3 고정 길이로 근사하면 그 길이까지만 잡는다

굳이 Core로 흉내 내려면 「길이 k짜리 순환 금지」를 k마다 하나씩 쓰는 방법뿐입니다. `sh:sequencePath`로 길이를 못 박고, 도착점을 상수와 비교하는 식이죠.

```turtle
# 길이 3 순환만, 그것도 특정 노드에 대해서만 검사하는 궁색한 형태
ex:N3Shape a sh:NodeShape ;
    sh:targetNode ex:n3 ;
    sh:property [
        sh:path ( ex:replaces ex:replaces ex:replaces ) ;   # sequencePath
        sh:not [ sh:hasValue ex:n3 ] ;                       # ← 상수라서 노드마다 형태가 필요
        sh:message "길이 3 순환" ] .
```

이 접근의 파산 지점이 뚜렷합니다.

1. **노드마다 형태를 하나씩 써야 합니다.** `sh:hasValue`가 상수만 받으니까요.
2. **길이마다 형태를 하나씩 써야 합니다.** 길이 3까지 막아 두면 길이 4짜리 순환은 그냥 통과합니다.
3. 순환의 최대 길이는 미리 알 수 없습니다. 데이터가 늘면 길어집니다.

「경로 제약은 결국 유한 길이 경로의 표현이고, `zeroOrMorePath`로 길이를 무한히 늘려도 **자기 자신 도달 금지**는 Core 제약 컴포넌트로 정의되어 있지 않다」— 이 문장이 이 질문의 정확한 답입니다.

---

## 4. `sh:sparql`로 흉내 내기 — 되긴 되는데

SHACL 명세는 두 부분입니다. **Part 1: SHACL Core**, **Part 2: SHACL-SPARQL**. Part 2의 `sh:sparql`(SPARQL 기반 제약)을 쓰면 탈출구가 생깁니다.

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/> .

ex:NoReplaceCycleShape a sh:NodeShape ;
    sh:targetClass ex:Part ;
    sh:sparql [
        a sh:SPARQLConstraint ;
        sh:severity sh:Warning ;
        sh:message "REPLACES 관계가 자기 자신으로 되돌아온다" ;
        sh:prefixes ex: ;
        sh:select """
            SELECT $this
            WHERE {
                $this ex:replaces+ $this .
            }
        """ ] .
```

`$this`가 SPARQL 안에서는 초점 노드로 바인딩되므로, Core에서 없던 「출발점 = 도착점」 비교가 여기서는 됩니다. pyshacl도 `sh:sparql`을 지원합니다.

### 그런데 한계가 넷 있습니다

**(1) 이건 이제 SHACL이 아니라 SPARQL입니다.**
형태 언어의 장점(선언적, 도구가 해석 가능, 형태를 다시 데이터로 질의 가능)이 사라집니다. SPARQL 문자열 리터럴 안으로 로직이 숨어서, 형태 그래프를 분석하는 도구는 이 제약이 뭘 하는지 알 수 없습니다. RDF가 아닌 저장소(프로퍼티 그래프 위의 SHACL 구현, SHACL → JSON Schema 변환기 등)로는 아예 이식되지 않습니다. Core만 지원하는 검증기에서는 조용히 무시됩니다.

**(2) 위반 보고가 사람에게 쓸모없습니다.**
`ex:replaces+`는 중간 경로를 바인딩하지 않습니다. 그래서 결과는 「n3은 순환에 속한다」, 「n4는 순환에 속한다」, 「n5는 순환에 속한다」— **순환 하나당 위반 3건**이고, 정작 필요한 `n3 → n4 → n5 → n3`이라는 **경로 자체는 안 나옵니다.** 고치려는 사람은 어느 링크를 끊어야 할지 알 수 없습니다. 예제의 DFS는 경로를 그대로 출력합니다.

**(3) 성능이 초점 노드 수만큼 곱해집니다.**
`sh:sparql`은 초점 노드마다 한 번씩 실행됩니다. 부품 노드가 10만 개면 전이 폐포 질의를 10만 번 돕니다. 반면 DFS는 그래프 전체를 **한 번** 훑어 O(V+E)로 끝납니다. 여기에 `+` 경로의 최적화 품질이 저장소마다 천차만별이라는 문제가 얹힙니다.

**(4) 대개는 SHACL을 전체 그래프에 돌리지 않습니다.**
실무 파이프라인은 **적재되는 배치**를 검증합니다. n3→n4는 2024년 배치, n5→n3은 2026년 배치에 들어 있으면, 어느 배치도 단독으로는 순환을 포함하지 않습니다. 순환은 **누적된 전체 그래프**에만 존재합니다. 게이트 방식 검증은 원리적으로 이걸 못 봅니다. 그래서 스멜 검사는 게이트가 아니라 **주기적 전수 스캔**으로 돌립니다.

> SHACL-AF(Advanced Features)의 `sh:expression`, SHACL 함수, 노드 표현식도 후보로 거론됩니다. 하지만 (가) SHACL-AF는 Recommendation이 아니라 **Working Group Note**라 구현 지원이 들쭉날쭉하고, (나) 커스텀 함수의 몸통은 결국 SPARQL이나 네이티브 코드라서 위 (1)~(3)이 그대로 따라옵니다. `ex1_shacl_severity.py`가 `validate(..., advanced=True)`로 켜는 게 이 SHACL-AF입니다.

---

## 5. 그래서 DFS로 직접 찾는다

`ex3_graph_smells.py`의 `smell_cycle`이 하는 일입니다.

```python
def smell_cycle(edges, rel):
    adj = defaultdict(list)
    for a, r, b in edges:
        if r == rel:                      # REPLACES 간선만 뽑아 인접 리스트를 만든다
            adj[a].append(b)
    seen, stack, out = set(), set(), []

    def go(u, path):
        if u in stack:                    # 지금 내려온 경로 위에 다시 나타났다 = 역방향 간선
            out.append(path[path.index(u):] + [u]); return
        if u in seen:                     # 이미 다 훑은 노드 = 다시 안 본다
            return
        seen.add(u); stack.add(u)
        for v in adj[u]:
            go(v, path + [u])
        stack.discard(u)                  # 이 노드에서 내려가는 탐색이 끝났다

    for u in list(adj):
        go(u, [])
    return out
```

교과서적인 **역방향 간선(back edge) 검출**입니다. 집합이 둘인 게 핵심이에요.

- `seen` — 한 번이라도 탐색을 마친 노드. 재방문을 막아 O(V+E)를 보장합니다.
- `stack` — **지금 재귀 호출 스택에 올라 있는 노드**. 즉 현재 경로 위의 노드들.

`u in stack`이 참이라는 건 「지금 내려오던 길에서 이미 지나온 노드로 되돌아왔다」는 뜻이고, 이게 정확히 사이클입니다. `path[path.index(u):] + [u]`로 경로에서 그 지점부터 잘라내면 `n3 → n4 → n5 → n3`이라는 **순환 고리 자체**가 나옵니다. 출력은 이렇습니다.

```
[사이클] «대체» 관계에 순환 — 1건
    n3 → n4 → n5 → n3
```

`sh:sparql`이 못 주던 바로 그 정보입니다.

### DFS를 골랐을 때의 이득

| | `sh:sparql` | DFS |
|---|---|---|
| 복잡도 | 초점 노드마다 전이 폐포 | 전체 한 번, O(V+E) |
| 결과 | 「이 노드는 순환에 속함」 × N | 순환 경로 그 자체 |
| 의존성 | 검증기 + SPARQL 엔진 | 없음(예제는 순수 파이썬) |
| 관계 종류 확장 | 형태를 새로 씀 | `rel` 인자만 바꿈 |

### 알아 둘 잔가지

- 재귀 구현이라 체인이 아주 길면 파이썬 재귀 한도(기본 1000)에 걸립니다. 실무 규모에서는 명시적 스택으로 바꾸는 게 안전합니다.
- 한 순환이 진입 순서에 따라 두 번 이상 보고되거나, 표현이 회전된 형태(`n4 → n5 → n3 → n4`)로 나올 수 있습니다. 정규화(가장 작은 노드에서 시작하도록 회전)해서 중복을 접는 후처리를 붙이면 좋습니다.
- **자동으로 고치면 안 됩니다.** 이 장이 반복해서 강조하는 지점이에요. 어느 링크를 끊을지는 도메인 판단입니다. 스멜 검사기의 일은 **목록을 뽑아 사람 앞에 놓는 것**까지입니다.

---

## 6. REPLACES 순환이 실무에서 만드는 문제

「그래서 순환이 왜 나쁜데?」에 답할 수 있어야 합니다.

**(1) 최신 버전을 결정할 수 없다.**
`REPLACES` 체인의 존재 이유가 「이 부품의 현행 대체품은 무엇인가」에 답하기 위해서입니다. 정상이라면 체인을 끝까지 따라가서 **아무도 대체하지 않는 노드**가 답입니다. 순환이 있으면 그런 끝이 없습니다. n3, n4, n5 셋 다 「누군가에게 대체당한」 상태라 **답이 존재하지 않습니다.** 질의는 빈 결과를 내거나, 우연히 먼저 만난 노드를 반환합니다. 후자가 더 나쁩니다 — 조용히 틀리니까요.

**(2) 무한 루프.**
SPARQL의 `+`나 Cypher의 가변 길이 경로는 대개 중복 제거 덕에 종료됩니다. 그런데 애플리케이션 코드의 `while current.replaced_by: current = current.replaced_by` 같은 루프는 안 끝납니다. ETL 잡, 리포트 배치, 프런트엔드 재귀 렌더링에서 터집니다. 예제의 DFS도 `stack` 검사를 빼면 무한 재귀에 빠집니다.

**(3) 위상 정렬이 깨진다.**
대체 관계는 암묵적으로 **DAG(비순환 유향 그래프)**를 가정합니다. BOM 전개, 단종 처리 순서, 마이그레이션 순서, 재고 소진 계획 — 전부 위상 정렬에 기댑니다. 순환이 하나 들어가면 위상 정렬이 **정의 자체가 안 되고**, 그 위에 얹힌 계획 로직이 통째로 무너집니다.

**(4) 캐시와 증분 갱신이 스스로를 무효화한다.**
n3의 최신 버전이 바뀌면 n5를 다시 계산하고, n5가 바뀌면 n4를, n4가 바뀌면 다시 n3을 — 무효화가 원을 돌며 멈추지 않습니다.

**(5) 비즈니스 의미가 모순이다.**
「A가 B를 대체한다」는 시간 순서를 담은 주장입니다. A가 B보다 나중입니다. 순환은 「n3이 n5보다 나중이면서 동시에 앞」이라고 말하는 셈입니다. 데이터가 자기 자신과 모순됩니다.

---

## 7. 이 장의 결론 — 두 겹 검증

예제 3이 마지막에 출력하는 표가 이 질문의 맥락 전체입니다. 다섯 스멜이 SHACL로 안 잡히는 이유가 **각각 다릅니다.**

| 스멜 | SHACL로 못 잡는 이유 |
|---|---|
| 슈퍼 노드 | 「평균의 5배」는 그래프 전체를 봐야 나오는 **상대값** |
| 고아 노드 | 잡히긴 하는데(`sh:inversePath` + `sh:minCount 1`) 종류가 많아 일일이 못 씀 |
| **사이클** | **SHACL에 「순환 없음」 제약이 없다** |
| 중복 의심 | 「비슷하다」는 판정이라 **참/거짓이 아니다** |
| 다중 소속 | **위반이 아닐 수도 있다.** 도메인이 정한다 |

그래서 검증은 두 층입니다.

- **1층 SHACL** — 참/거짓이 분명한 형태 제약. 게이트에 걸고 `sh:severity`로 차단/경고/기록을 나눈다.
- **2층 스멜** — 세어 보고 「이상하면 사람이 본다」. 주기적으로 전수 스캔하고, **자동으로 고치지 않는다.**

사이클은 명백히 2층입니다. 1층에 억지로 밀어 넣으려다(`sh:sparql`) 이식성과 성능과 보고 품질을 다 잃는 것보다, 2층에서 20줄짜리 DFS로 경로까지 찍어 사람에게 넘기는 게 낫습니다.

---

## 한 문장으로

> SHACL Core의 제약 컴포넌트 28개 중에 「순환 없음」이 없다. 경로 문법에 `sh:zeroOrMorePath`가 있어서 **어디까지 닿는지**는 물을 수 있지만, **초점 노드 자신에게 되돌아왔는지**를 검사할 컴포넌트가 없기 때문이다(`sh:hasValue`는 상수만, `sh:disjoint`는 술어 IRI만 받고, 중첩 형태는 `$this`를 옮겨 버린다). `sh:sparql`로 `$this ex:replaces+ $this`를 쓰면 흉내는 나지만 이식성·성능·보고 품질을 잃는다. 그래서 예제는 REPLACES 간선만 뽑아 DFS 역방향 간선 검출로 `n3 → n4 → n5 → n3`이라는 **경로 자체**를 O(V+E)에 뽑아 사람에게 넘긴다.

## 참고

- [Shapes Constraint Language (SHACL)](https://www.w3.org/TR/shacl/) — Core 제약 컴포넌트 전체 목록(4장), SHACL 경로(2.3.1절), 재귀 미정의(3.4.3절), SPARQL 기반 제약(Part 2)
- [sh:severity](https://www.w3.org/TR/shacl/#severity)
- [SHACL Advanced Features](https://www.w3.org/TR/shacl-af/) — W3C Working Group Note
- 이 책 2장 「안티패턴 카탈로그 = 그래프 스멜」, 14장 「중복 의심」의 본편
