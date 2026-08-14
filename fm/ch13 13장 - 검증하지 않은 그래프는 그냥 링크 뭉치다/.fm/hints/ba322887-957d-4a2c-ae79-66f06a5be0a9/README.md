# 슈퍼 노드를 SHACL로 잡기 어려운 이유

## 질문

슈퍼 노드를 SHACL로 잡기 어려운 이유는 무엇인가?

## 답

**'평균의 5배'는 데이터 전체를 봐야 나오는 상대값이기 때문이다. SHACL은 노드 단위 형태 제약이다.**

---

## 1. 판정식을 그대로 써 보면 문제가 보인다

13장 `ex3_graph_smells.py`의 슈퍼 노드 판정은 이렇게 생겼습니다.

```python
def smell_supernode(nodes, edges, factor=5):
    d = degrees(edges)
    avg = sum(d.values()) / len(d)          # ← 그래프 전체 집계
    return [(v, n) for v, n in d.most_common() if n > avg * factor]
```

판정식을 수식으로 옮기면:

```
deg(v) > 5 × avg(deg over ALL nodes in G)
```

좌변 `deg(v)`는 노드 하나만 보면 나옵니다. 문제는 **우변**입니다. `avg`를 알려면 그래프에 있는 모든 노드의 차수를 세야 합니다. 즉 노드 `v`의 합격/불합격이 **`v`와 아무 관계도 없는 저 멀리 있는 노드들의 상태에 달려 있습니다.**

여기서 두 가지 성질이 따라옵니다.

| 성질 | 의미 |
|---|---|
| **비국소(non-local)** | `v` 근처만 봐서는 판정이 안 나온다. 그래프 전체를 훑어야 한다. |
| **비단조(non-monotonic)** | 데이터를 **추가**했을 뿐인데 이미 통과했던 노드가 위반이 되거나, 이미 위반이던 노드가 통과가 된다. 차수 낮은 노드를 잔뜩 넣으면 `avg`가 내려가 없던 슈퍼 노드가 생기고, 차수 높은 노드를 넣으면 `avg`가 올라가 있던 슈퍼 노드가 사라진다. |

## 2. SHACL의 검증 모델 — focus node 단위, 로컬

SHACL(<https://www.w3.org/TR/shacl/>)의 검증은 다음 순서로 돕니다.

1. **target 선택**: `sh:targetClass`, `sh:targetNode`, `sh:targetSubjectsOf`, `sh:targetObjectsOf`로 **focus node** 집합을 고른다.
2. **value node 추출**: 각 focus node에서 `sh:path`를 따라 값들을 뽑는다.
3. **제약 평가**: 그 값들에 `sh:minCount` / `sh:maxCount` / `sh:datatype` / `sh:pattern` / `sh:in` / `sh:minInclusive` 등을 건다.
4. **결과 취합**: focus node × shape × 제약 조합마다 `sh:ValidationResult`를 만든다.

즉 SHACL의 판정 단위는 **"focus node 하나 + 그 노드에서 path로 닿는 값들"** 입니다. 13장 `shapes.ttl`을 보면 이 구조가 그대로 드러납니다.

```turtle
ex:CompanyShape a sh:NodeShape ;
    sh:targetClass ex:Company ;
    sh:property [
        sh:path ex:bizNumber ;
        sh:minCount 1 ; sh:maxCount 1 ;
        sh:pattern "^[0-9]{3}-[0-9]{2}-[0-9]{5}$" ;
        sh:severity sh:Violation ;
        sh:message "사업자번호가 없거나 형식이 틀렸다" ] .
```

이 shape가 회사 A를 검사할 때, 회사 B가 그래프에 몇 개 있든 결과가 바뀌지 않습니다. **이 독립성이 SHACL의 설계 의도이자 장점**입니다. 덕분에

- focus node별 **병렬 검증**이 가능하고,
- 적재 시 **변경분만 증분 검증**해도 되며(안 건드린 노드는 결과가 그대로니까),
- 위반 리포트가 "어느 노드의 어느 path가 왜 틀렸는지"로 **국소적으로 지목**됩니다.

`avg(deg)` 같은 전역 집계를 제약에 끌어들이는 순간 이 세 가지가 전부 깨집니다. 병렬화 못 하고, 증분 검증 못 하고, "이 노드가 왜 위반이죠?"에 "다른 노드들이 다 작아서요"라고 답해야 합니다.

**핵심 대비:**

| | SHACL 형태 제약 | 슈퍼 노드 판정 |
|---|---|---|
| 판정 범위 | focus node + path 이웃 (로컬) | 그래프 전체 (전역 집계) |
| 임계값 | shape에 박힌 **상수** | 데이터에서 계산되는 **상대값** |
| 데이터 추가 시 | 기존 판정 불변(단조) | 기존 판정이 뒤집힘(비단조) |
| 결과 | 참/거짓이 분명한 위반 | "이상하다"는 의심 신호 |
| 조치 | 차단하거나 고친다 | 목록 뽑아 사람이 본다 |

## 3. `sh:maxCount`로 절대 임계를 거는 건 다른 이야기다

"그럼 `sh:maxCount 100` 걸면 되는 거 아닌가?" — 흔한 반론인데, 이건 **다른 문제를 푸는 것**입니다.

**(1) 상대값 → 상수로 바꿔치기한 것이다.**
`maxCount 100`은 "평균의 5배"가 아니라 "100개 초과 금지"입니다. 데이터가 10배로 커져 평균 차수가 200이 돼도 임계는 여전히 100입니다. 그러면 정상 노드가 전부 위반으로 쏟아집니다. 반대로 초기 데이터가 작을 땐 진짜 허브가 100을 못 넘어 안 잡힙니다. **임계값을 사람이 손으로 재조정해 줘야 하는데, 그 재조정의 근거가 바로 "지금 평균이 얼마냐"** 입니다. 결국 원래 문제로 돌아옵니다.

**(2) `maxCount`가 세는 것과 degree가 세는 것이 다르다.**
`sh:maxCount`는 **하나의 `sh:path`에서 나오는 value node 개수**를 셉니다. 그런데 슈퍼 노드의 degree는

- **모든 predicate에 걸친 합**이고,
- **in-degree + out-degree 양방향**입니다.

`ex3`의 `degrees()`가 `d[a] += 1; d[b] += 1`로 양쪽 다 세는 게 그것입니다. SHACL로 이걸 흉내 내려면 predicate마다 `sh:path`를 하나씩 쓰고 역방향은 `sh:inversePath`를 또 쓰고, 그 개수들을 **합산**해야 하는데 — **SHACL Core에는 여러 path의 카운트를 합산하는 연산자가 없습니다.** `sh:alternativePath`로 predicate를 나열해 볼 수는 있지만, predicate 목록을 shape에 하드코딩해야 하고 스키마가 늘어날 때마다 shape를 고쳐야 합니다.

**(3) 심각도의 의미가 다르다.**
`sh:maxCount` 위반은 `sh:Violation`으로 올려 적재를 차단하는 게 자연스럽습니다. 하지만 슈퍼 노드는 **위반이 아닙니다.** 「미분류」 카테고리에 30개가 몰린 건 실제로 그럴 수도 있고(대형 공급사, 공통 부품), 데이터 정리가 안 된 것일 수도 있습니다. 이걸 차단으로 걸면 13.2절이 경고하는 그 함정 — **"전부 막으면 데이터가 안 들어오고, 사람들이 검증을 우회한다"** — 에 그대로 빠집니다.

## 4. `sh:sparql`로 억지로 흉내 낼 때의 비용과 한계

SHACL-SPARQL(SHACL Advanced Features, <https://www.w3.org/TR/shacl-af/>)의 `sh:sparql` 제약을 쓰면 **원리적으로는** 전역 집계를 넣을 수 있습니다. 대충 이런 모양입니다.

```turtle
ex:SuperNodeShape a sh:NodeShape ;
    sh:targetClass ex:Category ;
    sh:severity sh:Info ;
    sh:sparql [
        sh:message "차수가 평균의 5배를 넘는다 (슈퍼 노드 의심)" ;
        sh:prefixes ex: ;
        sh:select """
            SELECT $this WHERE {
              { SELECT $this (COUNT(*) AS ?deg) WHERE {
                  { ?x ?p $this } UNION { $this ?p ?y }
                } GROUP BY $this }
              { SELECT (AVG(?d) AS ?avg) WHERE {
                  { SELECT ?n (COUNT(*) AS ?d) WHERE {
                      { ?a ?p1 ?n } UNION { ?n ?p2 ?b }
                    } GROUP BY ?n }
                } }
              FILTER(?deg > 5 * ?avg)
            }
        """ ] .
```

돌아가긴 하지만, 실무에서 이걸 검증 파이프라인에 얹으면 다음을 감수해야 합니다.

**(a) 비용이 focus node 수만큼 곱해진다.**
SHACL-SPARQL의 `sh:select`는 **focus node마다 `$this`를 바인딩해 한 번씩 실행**됩니다. 위 쿼리 안에는 그래프 전체를 훑어 `AVG`를 구하는 서브쿼리가 들어 있으니, focus node가 N개면 대략 **O(N × |E|)** 입니다. 모든 노드가 대상이면 O(V × E). 100만 노드 그래프에서는 그냥 안 끝납니다. 엔진이 상수 서브쿼리를 캐싱해 주기를 기대할 수는 있지만, **명세가 보장하는 동작이 아닙니다.** 반면 `ex3`처럼 절차적으로 한 번 세면 O(E)로 끝납니다.

**(b) pre-binding 규칙이 발목을 잡는다.**
SHACL 명세는 `$this` 주입(pre-binding)에 제약을 겁니다 — 주입되는 변수는 쿼리에서 재바인딩되면 안 되고(`BIND`/`VALUES`/`GROUP BY` 대상 금지 등), **서브쿼리 안쪽으로는 `SELECT` 절에 그 변수가 투영돼 있을 때만 전달**됩니다. 그래서 위처럼 `$this`를 서브쿼리 안에서 `GROUP BY` 하는 형태는 엔진 구현에 따라 거부되거나 다르게 동작합니다. 회피하려고 쿼리를 비틀수록 읽을 수 없는 물건이 됩니다.

**(c) 이식성이 없다.**
`sh:sparql`은 **SHACL Core가 아니라 SHACL-SPARQL/Advanced Features**입니다. Core만 구현한 검증기에서는 이 shape가 조용히 무시되거나 오류가 납니다. pyshacl은 지원하지만, 그래프 DB에 내장된 검증기나 다른 스택으로 옮기는 순간 깨질 수 있습니다. Core shape는 어디서든 도는데 이것만 안 돕니다.

**(d) 증분 검증이 불가능해진다.**
적재 파이프라인에서 SHACL을 쓰는 이유의 절반은 "이번에 들어온 변경분만 빠르게 검사"입니다. 전역 `AVG`가 들어가면 **한 건만 추가돼도 모든 노드의 판정이 이론상 바뀔 수 있어** 전체를 다시 검증해야 합니다.

**(e) '전체'의 경계가 애매하다.**
SHACL은 하나의 data graph를 검증합니다. 그런데 운영에서는 named graph로 나뉘고 샤딩돼 있는 게 보통입니다. **평균을 어느 범위에서 낼 것인가**(전체? 이 named graph만? 이 라벨의 노드만?)는 SHACL이 답해 주지 않는, 도메인이 정해야 하는 질문입니다.

**(f) 결과의 의미가 안 맞는다.**
나오는 것은 `sh:ValidationResult`, 즉 **"위반"** 입니다. `sh:severity sh:Info`로 낮춰도 리포트 성격은 "규칙을 어겼다"입니다. 슈퍼 노드는 어긴 게 아니라 **"세어 보니 튄다, 사람이 확인해라"** 입니다. 도구의 출력 의미와 실제 필요한 의미가 어긋나 있습니다.

## 5. 그래서 13장의 결론 — 두 겹으로 간다

```
1층  SHACL   — 참/거짓이 분명한 형태 제약. 자동 판정, 자동 차단 가능.
              (사업자번호 형식, 필수 속성, 값 범위, 데이터타입…)

2층  그래프 스멜 — 세어 봐야 보이는 것. 목록만 뽑아 사람이 본다.
              (슈퍼 노드, 사이클, 중복 의심, 다중 소속…)
```

**2층은 자동으로 고치지 않습니다. 목록을 뽑아 주는 게 일입니다.**

`ex3`이 정리한 다섯 스멜은 SHACL로 못 잡는 **이유가 각각 다릅니다.** 슈퍼 노드만 유별난 게 아니라는 걸 같이 기억해 두면 답이 흔들리지 않습니다.

| 스멜 | SHACL로 어려운 이유 | 어려움의 종류 |
|---|---|---|
| **슈퍼 노드** | 「평균의 5배」는 데이터 전체를 봐야 나오는 **상대값** | 전역 집계 |
| 고아 노드 | 형태 제약(`sh:minCount`, `sh:inversePath`)으로 잡히긴 하나 노드 종류마다 써야 해서 실무상 못 씀 | 표현력은 있으나 규모 문제 |
| 사이클 | SHACL에 「순환 없음」 제약 자체가 없음 | 표현력 부재 |
| 중복 의심 | 「비슷하다」는 판정이라 참/거짓이 아님 | 판정이 이진이 아님 |
| 다중 소속 | 위반이 아닐 수도 있음. 도메인이 정함 | 위반 여부 자체가 미정 |

## 한 줄 정리

> SHACL은 **"이 노드 하나가 정해진 모양인가"** 를 묻는 도구다. 슈퍼 노드는 **"이 노드가 나머지 전체에 비해 튀는가"** 를 묻는다. 질문의 범위가 다르다. `sh:maxCount`로 상수 임계를 걸면 질문이 바뀌어 버리고, `sh:sparql`로 전역 집계를 밀어 넣으면 비용·이식성·증분성이 무너진다. 그래서 세는 일은 검증기 밖 2층 스멜 리포트로 빼고, 결과는 차단이 아니라 사람이 볼 목록으로 낸다.

## 출처

- [Shapes Constraint Language (SHACL)](https://www.w3.org/TR/shacl/) — 검증 모델, focus node, `sh:maxCount`, pre-binding
- [sh:severity](https://www.w3.org/TR/shacl/#severity) — 심각도 세 단계
- [SHACL Advanced Features](https://www.w3.org/TR/shacl-af/) — `sh:sparql` 기반 제약
- 13장 `code/ex3_graph_smells.py`, `code/shapes.ttl`
