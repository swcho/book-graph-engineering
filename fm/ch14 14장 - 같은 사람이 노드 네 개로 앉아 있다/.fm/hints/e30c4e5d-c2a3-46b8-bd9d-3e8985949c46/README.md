# `MergeStore`가 병합 이력을 기록하는 이유

> **Q.** `MergeStore`가 병합 이력을 기록하는 이유는 무엇인가?
>
> **A.** 되돌리기 위해서다. merge와 unmerge를 사건으로 남기며, 6부 이벤트 소싱의 축소판이다.

---

## 1. 코드가 먼저 선언한다

`ex3_reversible_merge.py`의 docstring부터가 답을 미리 말해 준다.

```python
"""
예제 3 — 되돌릴 수 있는 병합. 노드를 지우지 않고 «가리키게» 한다.

의존성 없음. 6부 이벤트 소싱의 축소판이다.
"""
```

클래스 주석도 같은 이야기다.

```python
class MergeStore:
    """병합을 «사건»으로 기록한다. 원본 노드는 절대 지우지 않는다."""

    def __init__(self, nodes):
        self.nodes = dict(nodes)                 # id -> 속성
        self.canonical = {k: k for k in nodes}   # id -> 대표 id
        self.events = []                         # 되돌리기용 이력
```

필드가 딱 세 개인데 역할이 명확히 갈린다.

| 필드 | 성격 | 이벤트 소싱 대응 |
|---|---|---|
| `nodes` | 원본 속성. 병합해도 절대 지우지 않는다 | 불변 원장(原帳) |
| `events` | merge/unmerge 사건의 append-only 목록 | **이벤트 로그 = 진실의 원천** |
| `canonical` | id → 대표 id 포인터 | **이벤트를 접어 만든 파생 뷰(read model)** |

주석이 `self.events`를 그냥 "이력"이 아니라 **"되돌리기용 이력"**이라고 못 박은 게 핵심이다. 존재 이유가 감상이 아니라 기능이다.

## 2. 이벤트 레코드 구조

`merge`가 남기는 사건 레코드는 이렇게 생겼다.

```python
def merge(self, a, b, by, reason):
    ca, cb = self.resolve(a), self.resolve(b)
    if ca == cb:
        return False
    # 대표는 «정보가 더 많은» 쪽으로. 규칙을 못 박아 둔다.
    keep, drop = (ca, cb) if self._richness(ca) >= self._richness(cb) else (cb, ca)
    self.canonical[drop] = keep
    self.events.append({"op": "merge", "keep": keep, "drop": drop,
                        "by": by, "reason": reason})
    return True
```

필드 하나하나가 서로 다른 질문에 답한다.

| 필드 | 값 예시 | 답하는 질문 |
|---|---|---|
| `op` | `"merge"` / `"unmerge"` | 무슨 사건이 일어났나 (사건 종류) |
| `keep` | `"r01"` | 어느 쪽이 대표로 남았나 |
| `drop` | `"r04"` | 어느 쪽이 대표를 가리키게 됐나 — **되돌릴 대상** |
| `by` | `"auto"` / `"reviewer:kim"` | **누가** 합쳤나 (자동 규칙인가 사람인가) |
| `reason` | `"사업자번호 일치"` | **왜** 합쳤나 (판단 근거) |

`unmerge`는 여기에 한 필드를 더 얹는다.

```python
def unmerge(self, dropped):
    for i in range(len(self.events) - 1, -1, -1):
        e = self.events[i]
        if e["op"] == "merge" and e["drop"] == dropped:
            self.canonical[dropped] = dropped
            self.events.append({"op": "unmerge", "target": dropped,
                                "undoes": i})
            return True
    return False
```

- `target`: 되돌린 노드
- `undoes`: **몇 번째 사건을 취소했는지 가리키는 인덱스**

여기서 중요한 설계 판단이 두 개 있다.

1. **merge 이벤트를 지우지 않는다.** 되돌릴 때 로그에서 `[0] merge`를 삭제하는 게 아니라, `[2] unmerge ... undoes: 0`을 **뒤에 덧붙인다**. 로그는 append-only이고 과거는 고쳐지지 않는다. "합쳤다가 되돌렸다"는 사실 자체가 기록으로 남는다.
2. **상태 변경은 포인터 대입 한 번.** `self.canonical[dropped] = dropped`. 원본 속성(`nodes`)을 건드리지 않으므로 복구할 데이터가 애초에 사라진 적이 없다.

예제 실행 결과의 `4) 이력` 부분이 그대로 이 로그다.

```
[0] {'op': 'merge', 'keep': 'r01', 'drop': 'r04', 'by': 'auto', 'reason': '사업자번호 일치'}
[1] {'op': 'merge', 'keep': 'r06', 'drop': 'r07', 'by': 'auto', 'reason': '주소·대표자·전화 일치'}
[2] {'op': 'unmerge', 'target': 'r07', 'undoes': 1}
```

## 3. 이력이 없으면 무엇을 못 하나

"기록하는 이유"를 이해하는 가장 빠른 길은 **없을 때 못 하는 일**을 세어 보는 것이다. 네 가지가 한꺼번에 무너진다.

### (1) 되돌리기 — 이게 1차 목적

`drop`이 기록돼 있지 않으면 `unmerge("r07")`이 성립하지 않는다. 어느 노드가 어느 대표를 가리키게 됐는지 모르니 "원래대로"라는 상태가 정의되지 않는다. 예제의 주석이 이 지점을 정면으로 짚는다.

```
핵심은 «원본을 안 지운다»는 것이다.
r07 의 속성이 그대로 남아 있으니 되돌리기가 대입 한 번이다.

노드를 실제로 지우고 속성을 합쳐 버리면 이게 안 된다.
어느 값이 어디서 왔는지 모르니까 원래대로 쪼갤 수 없다.
```

되돌리기 비용은 자동화 정책 자체를 바꾼다. `ex4_threshold_tuning.py` 마지막 문단이 그 계산이다.

```
사람 한 건 검토: 약 40초, 인건비로 환산해 400원
오병합 하나 수습: 평균 2시간 (원인 파악 + 되돌리기 + 영향 받은 질의 확인)
→ 오병합 하나가 검토 180건과 맞먹는다
...
다만 이건 «되돌리기가 비싼» 경우다. 되돌리기가 싸면 계산이 달라진다.
앞 예제처럼 unmerge 가 대입 한 번이면 오병합 값이 2시간에서 5분이 된다.
```

즉 **이력은 임계값을 낮출 수 있게 해 주는 자산**이다. 한 장 요약의 "되돌릴 수 있으면 훨씬 공격적으로 자동화할 수 있고요"가 이 뜻이다.

### (2) 감사 — 누가 왜 합쳤나

`by`와 `reason`이 담당하는 몫이다. `r06`/`r07`(나루소프트 / 나루소프트(주))은 `by="auto", reason="주소·대표자·전화 일치"`로 합쳐졌다. 사고가 터진 뒤 물어야 하는 질문은 "합쳐졌다"가 아니라 **"왜 합쳐졌나"**다.

- `by="auto"`니까 사람 판정 실수가 아니라 **규칙 자체가 잘못됐다** → 규칙을 고쳐야 한다.
- `reason="주소·대표자·전화 일치"`니까 **사업자번호를 거부권 규칙으로 안 걸어 뒀다**는 진단이 바로 나온다.

이 두 필드가 없으면 "언젠가 누군가 합쳤다"만 남는다. 그러면 같은 사고를 또 낸다. 실제로 이 장의 서두가 그 사흘의 기록이고, 14.2절 결론이 "점수 위에 «절대 안 되는» 거부권 규칙을 두세요"다. 그 결론에 도달하려면 `reason`을 읽을 수 있어야 한다.

`by`는 책임 소재도 나눈다. `auto`로 들어온 병합은 규칙 튜닝 대상, 사람이 넣은 병합은 판정 기준 교육/합의 대상이다. 규제·컴플라이언스 관점에서도 마스터 데이터가 언제 누구 손으로 바뀌었는지에 답할 수 있어야 한다.

### (3) 재현 — 같은 규칙을 다시 돌릴 수 있나

`canonical` 딕셔너리만 스냅숏으로 들고 있으면 **결과**는 있지만 **과정**이 없다. 이력이 있으면 다음이 가능해진다.

- 규칙을 v1 → v2로 고친 뒤, 로그의 `by="auto"` 사건만 골라 **재실행**해서 v1과 v2의 결과 차이를 뽑아낸다(회귀 테스트).
- 사람이 판정한 사건(`by="reviewer:*"`)은 **정답 데이터**로 따로 보존해 재실행 대상에서 빼거나, 새 규칙의 평가셋으로 재활용한다. `ex2_scoring.py`의 `HUMAN = {("r01","r04"): True, ("r06","r07"): False}`가 바로 그런 사람 판정 기록이고, 이력에 남아야 다음 라운드에 재사용할 수 있다.
- 특정 시점 상태를 복원할 수 있다. 로그 앞부분 N개만 접으면 "지난주 화요일의 `canonical`"이 나온다. 그래프 질의 결과가 어제와 오늘 다른 이유를 설명하려면 이게 필요하다.

이력 없이 규칙만 다시 돌리면 "지금 상태"가 새 규칙 결과인지 옛 규칙 잔여물인지 구분이 안 된다. **상태를 재구성할 수 없으면 실험을 할 수 없다.**

### (4) 디버깅 — 이 군집은 왜 이렇게 생겼나

이행성(transitive closure)이 걸리면 병합은 쌍 단위가 아니라 군집 단위로 번진다. `ex2_scoring.py` 결론이 경고하는 대목이다.

```
이행성도 공짜가 아니다. 잘못된 병합 하나가 군집 전체를 오염시킨다.
그래서 군집 크기에 상한을 두거나, 커지면 사람에게 보내는 게 안전하다.
```

노드 20개짜리 군집이 생겼을 때, 이력이 있으면 그 군집을 만든 merge 사건들을 순서대로 늘어놓고 **어느 한 사건이 오염의 시작점인지** 이분 탐색할 수 있다. `keep`/`drop`이 간선(edge)이라 군집 형성 과정이 그래프로 복원된다. 이력이 없으면 `canonical` 포인터 20개만 보이고, 어느 판정이 다리를 놓았는지 알 수 없다. 그러면 **전부 풀고 처음부터**밖에 남지 않는다.

정리하면 이렇다.

| 잃는 것 | 없어지는 필드 | 구체적 증상 |
|---|---|---|
| 되돌리기 | `drop`, `op` | unmerge 자체가 불가능. 복구는 전체 재적재 |
| 감사 | `by`, `reason` | "왜 합쳤나"에 답 못 함 → 같은 사고 반복 |
| 재현 | 사건 순서 전체 | 규칙 v1/v2 비교, 과거 시점 복원 불가 |
| 디버깅 | `keep`–`drop` 간선 | 오염 군집의 시작점 특정 불가 |

## 4. 이벤트 소싱의 축소판인 이유

`MergeStore`가 "6부 이벤트 소싱의 축소판"이라고 자칭하는 근거를 개념 대 코드로 맞춰 보면 정확히 겹친다.

### 이벤트 소싱의 핵심 개념 세 가지

1. **현재 상태 = 이벤트를 접은 결과.** Martin Fowler의 정의대로, 이벤트 소싱은 애플리케이션의 상태를 도메인 이벤트 로그를 처리해서 **전부 유도해 낼 수 있을 때** 성립한다. 결정적 특징은 *"언제든 애플리케이션 상태를 날려 버리고 로그에서 확신을 갖고 재구축할 수 있다"*는 것이다.
2. **이벤트는 append-only이고 불변이다.** 이벤트는 append-only 저장소에 기록되고, 그 이벤트 저장소가 **시스템 오브 레코드(system of record)** — 즉 진실의 원천이다. 과거 이벤트를 수정하거나 삭제하지 않는다. 취소는 "삭제"가 아니라 **보상 이벤트를 덧붙이는 것**으로 표현한다.
3. **상태는 파생 뷰다.** 현재 상태는 직접 저장되는 1급 데이터가 아니라, 이벤트 스트림을 재생(replay, 이른바 rehydration)해서 얻는 **읽기용 투영(projection)**이다. 버리고 다시 만들 수 있고, 필요하면 여러 형태로 여러 개 만들 수도 있다.

### 코드와의 1:1 대응

| 이벤트 소싱 개념 | `MergeStore` |
|---|---|
| 이벤트 로그 (진실의 원천) | `self.events` |
| 이벤트 append (불변) | `self.events.append({...})` — 기존 원소를 고치지 않는다 |
| 보상 이벤트 (compensating event) | `{"op": "unmerge", "target": ..., "undoes": i}` |
| 파생 읽기 모델 (projection) | **`self.canonical`** |
| 상태 재구성 (replay / rehydration) | `events`를 처음부터 접으면 `canonical`이 나온다 |
| 질의 (query side) | `resolve()`, `clusters()`, `view()` |

**`canonical`이 그 「접힌 결과」다.** 이 대응이 이 카드의 핵심이다. `canonical`은 원본 데이터가 아니라 `events`를 순서대로 적용해 만든 파생 뷰다. 실제로 이렇게 재구성된다.

```python
def rebuild(node_ids, events):
    """events 를 접어서 canonical 을 복원한다. 이게 replay 다."""
    canonical = {k: k for k in node_ids}
    for e in events:
        if e["op"] == "merge":
            canonical[e["drop"]] = e["keep"]
        elif e["op"] == "unmerge":
            canonical[e["target"]] = e["target"]
    return canonical
```

`canonical`을 통째로 날려도 `nodes`와 `events`만 있으면 완전히 되살아난다. Fowler의 "상태를 날려 버리고 로그에서 재구축한다"가 그대로 성립한다는 뜻이고, 그래서 이 클래스가 축소판이라 불릴 자격이 있다.

`view()`가 하는 일도 투영이다.

```python
def view(self, nid):
    """대표 노드의 속성 + 병합된 것들의 속성을 채워 넣는다."""
```

원본 `nodes`를 지우지 않고, 조회 시점에 대표 노드 기준으로 속성을 합성한 **읽기 모델**을 만들어 준다. 쓰기(merge/unmerge, 로그에 append)와 읽기(`view`, `clusters`)가 다른 모델을 쓰는 이 분리가 **CQRS**의 형태다. CQRS는 "정보를 갱신할 때 쓰는 모델과 읽을 때 쓰는 모델이 서로 다를 수 있다"는 발상이며, 흔히 이벤트 소싱과 짝지어 쓰인다. Fowler는 동시에 *대부분의 시스템은 CRUD로 머무는 게 낫고, CQRS는 복잡도가 정당화되는 바운디드 컨텍스트에만 적용하라*고 경고하는데, 엔티티 해상도는 그 예외에 해당하는 전형적 영역이다. 오병합의 되돌리기 가능성이 도메인 요구사항 자체이기 때문이다.

### 대가도 정직하게 적혀 있다

```
대가는 저장 공간과 조회 비용이다. 조회할 때마다 resolve 를 거쳐야 한다.
제 경우 노드 수가 1.4배가 됐고, 조회에 인덱스 조회 한 번이 더 붙었다.
사흘짜리 사고를 다시 안 겪는 값으로는 쌌다.
```

이벤트 소싱의 대가와 정확히 같은 종류다. 상태를 직접 갖지 않고 파생시키는 대신, 저장 공간과 읽기 경로의 간접 비용을 낸다.

## 5. 실무 주의점 (6부로 가기 전 예고편)

이 축소판을 진짜 시스템으로 키우면 이벤트 소싱의 알려진 세 난관을 그대로 만난다.

- **이벤트 스키마 진화.** 이벤트는 불변인데 스키마는 변한다. 이게 이벤트 소싱의 가장 어려운 장기 문제로 꼽힌다. 예를 들어 나중에 `reason`을 자유 문자열에서 `{rule_id, score}` 구조로 바꾸고 싶어지면, 이미 쌓인 옛 이벤트는 옛 형식 그대로 남아 있다. 해법은 이벤트에 `version`을 넣고 읽을 때 새 형식으로 올려 주는 **업캐스팅(upcasting)** 인데, 지루하고 계속 누적되는 일이다. 그래서 처음부터 `op`/`by`/`reason` 같은 필드 이름을 신중하게 고르고, 추가는 쉽고 제거는 어렵다고 가정하는 게 낫다.
- **로그 크기.** 저장 공간이 영구히 증가한다. merge/unmerge는 사용자 이벤트보다 훨씬 드물어 부담이 작지만, 대규모 배치 재적재 때마다 수백만 사건을 append하는 파이프라인이면 압축·아카이빙 전략이 필요해진다.
- **스냅숏.** 사건이 수백만 건이면 매번 전체를 접어 `canonical`을 만드는 게 느려진다. 표준 해법은 특정 시점의 상태를 주기적으로 저장하고 그 이후 사건만 재생하는 것이다. 1,000만 번째 사건까지 왔다면 999만 번째 스냅숏에서 시작해 1만 건만 접는다. 다만 **스냅숏은 캐시일 뿐 진실의 원천이 아니다.** `canonical`을 저장해 두더라도 `events`가 여전히 원장이고, 스냅숏은 언제든 버리고 다시 만들 수 있어야 한다. 이 구분이 흐려지는 순간 되돌리기·감사·재현이 다시 무너진다.

## 6. 한 줄로

`MergeStore`의 `events`는 로그 파일이 아니라 **원장**이다. `canonical`은 그 원장을 접은 결과일 뿐이다. 이력을 남기는 이유는 되돌리기 위해서고, 되돌릴 수 있어야 더 과감하게 자동화할 수 있다.

---

## 참고 출처

- [Focusing on Events — Martin Fowler](https://martinfowler.com/eaaDev/EventNarrative.html)
- [Event Sourcing Pattern — Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)
- [bliki: CQRS — Martin Fowler](https://martinfowler.com/bliki/CQRS.html)
- [Command and Query Responsibility Segregation (CQRS) Pattern — Microsoft Learn](https://learn.microsoft.com/en-us/previous-versions/msp-n-p/dn568103(v=pandp.10))
- [Event Sourcing Production Anti-Patterns: Schema Evolution, Snapshotting, and Event Store Scaling](https://www.youngju.dev/blog/architecture/2026-03-07-architecture-event-sourcing-cqrs-production-patterns.en)
- [Event Sourcing in Practice: Append-Only Event Store with Projections and Snapshots](https://letsbuildsolutions.com/blog/system-design/event-sourcing-in-practice-building-an-append-only-event-store-with-projections-and-snapshots/)
- [Event Sourcing: Trade-Offs and Architectural Considerations — n8n Blog](https://blog.n8n.io/event-sourcing/)
- [PROV-O: The PROV Ontology — W3C](https://www.w3.org/TR/prov-o/) (출처 추적, 14장 키워드 표)
